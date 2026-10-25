// Optimizador de corte — Cristalux. Página local (sin internet, sin compilar).
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));
const estado = {
  proyecto: { codigo: "", descripcion: "", piezas: [] },
  calculo: null,      // id del último cálculo
  resultado: null,    // resumen del último cálculo terminado
  materiales: [],
  material: null,     // ficha abierta
  importado: null,    // vista previa de lo pegado o importado
  sondeo: null,
};

// ----------------------------------------------------------------- utilidades
function mensaje(texto, error = false) {
  const m = $("#mensaje");
  m.textContent = texto;
  m.className = "mensaje" + (error ? " error" : "");
  m.hidden = false;
  clearTimeout(mensaje.t);
  mensaje.t = setTimeout(() => (m.hidden = true), error ? 7000 : 3500);
}
async function api(url, opciones = {}) {
  const o = { headers: { "Content-Type": "application/json" }, ...opciones };
  if (o.body && typeof o.body !== "string") o.body = JSON.stringify(o.body);
  const r = await fetch(url, o);
  if (!r.ok) {
    let detalle = r.statusText;
    try { detalle = (await r.json()).detail || detalle; } catch (e) { /* sin detalle */ }
    const error = new Error(detalle);
    error.status = r.status;
    throw error;
  }
  return r.json();
}
function esc(t) {
  return String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function hms(seg) {
  if (seg == null || !isFinite(seg)) return "--:--:--";
  seg = Math.max(0, Math.round(seg));
  const h = String(Math.floor(seg / 3600)).padStart(2, "0");
  const m = String(Math.floor((seg % 3600) / 60)).padStart(2, "0");
  const s = String(seg % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}
function coma() { return $("#decimal").value === "1"; }
function num(x, d) { const t = Number(x).toFixed(d); return coma() ? t.replace(".", ",") : t; }
function guardarBorrador() {
  try { localStorage.setItem("optimizador.borrador", JSON.stringify(estado.proyecto)); } catch (e) { /* sin almacenamiento */ }
}
function leerBorrador() {
  try {
    const t = localStorage.getItem("optimizador.borrador");
    if (t) estado.proyecto = JSON.parse(t);
  } catch (e) { /* sin almacenamiento */ }
}

// ------------------------------------------------------------------- pestañas
function irA(nombre) {
  $$("#pestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.pestana === nombre));
  $$(".pestana").forEach((s) => s.classList.toggle("activa", s.id === nombre));
  if (nombre === "materiales" && !estado.materiales.length) cargarMateriales();
  if (nombre === "comparar") dibujarComparar();
}
$$("#pestanas button").forEach((b) => b.addEventListener("click", () => irA(b.dataset.pestana)));

// =================================================================== PROYECTO
const COLUMNAS = ["item", "material", "cantidad", "ancho", "largo", "rota", "clase", "descripcion"];

function dibujarGrilla() {
  $("#p-codigo").value = estado.proyecto.codigo || "";
  $("#p-descripcion").value = estado.proyecto.descripcion || "";
  const cuerpo = $("#grilla tbody");
  cuerpo.innerHTML = "";
  estado.proyecto.piezas.forEach((p, i) => cuerpo.appendChild(filaGrilla(p, i)));
  totales();
}
function filaGrilla(p, i) {
  const tr = document.createElement("tr");
  const rota = p.rota === true ? "si" : p.rota === false ? "no" : "";
  tr.innerHTML = `<td class="n">${i + 1}</td>
    <td><input data-c="item" value="${esc(p.item)}" size="4"></td>
    <td><input data-c="material" value="${esc(p.material)}" size="10" list="lista-materiales"></td>
    <td><input data-c="cantidad" class="num" value="${esc(p.cantidad)}" size="5"></td>
    <td><input data-c="ancho" class="num" value="${esc(p.ancho)}" size="6"></td>
    <td><input data-c="largo" class="num" value="${esc(p.largo)}" size="6"></td>
    <td><select data-c="rota"><option value="">material</option><option value="si">sí</option><option value="no">no</option></select></td>
    <td><input data-c="clase" value="${esc(p.clase || "")}" size="12"></td>
    <td><input data-c="descripcion" value="${esc(p.descripcion || "")}"></td>
    <td class="quitar"><button title="Borrar renglón">✕</button></td>`;
  $("select", tr).value = rota;
  $$("input,select", tr).forEach((el) => {
    el.addEventListener("change", () => {
      const c = el.dataset.c;
      let v = el.value.trim();
      if (c === "material") v = v.toUpperCase();
      if (c === "rota") v = v === "si" ? true : v === "no" ? false : null;
      estado.proyecto.piezas[i][c] = v;
      if (c === "material") el.value = v;
      guardarBorrador();
      totales();
    });
    el.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" && el.tagName === "INPUT") {
        ev.preventDefault();
        const abajo = cuerpoFila(i + 1);
        if (abajo) $(`[data-c="${el.dataset.c}"]`, abajo).focus();
        else { agregarRenglon(); $(`[data-c="${el.dataset.c}"]`, cuerpoFila(i + 1)).focus(); }
      }
    });
  });
  $(".quitar button", tr).addEventListener("click", () => {
    estado.proyecto.piezas.splice(i, 1);
    guardarBorrador();
    dibujarGrilla();
  });
  return tr;
}
function cuerpoFila(i) { return $$("#grilla tbody tr")[i]; }
function renglonVacio(p) { return !p.material && !p.ancho && !p.largo; }
function hayPiezas() { return estado.proyecto.piezas.some((p) => !renglonVacio(p)); }
function agregarRenglon() {
  const piezas = estado.proyecto.piezas;
  const anterior = piezas[piezas.length - 1];
  piezas.push({ item: String(piezas.length + 1), material: anterior ? anterior.material : "", cantidad: 1, ancho: "", largo: "", rota: null, clase: "", descripcion: "" });
  guardarBorrador();
  dibujarGrilla();
}
function totales() {
  let piezas = 0, m2 = 0;
  for (const p of estado.proyecto.piezas) {
    const c = Number(String(p.cantidad).replace(",", ".")) || 0;
    piezas += c;
    m2 += c * (Number(p.ancho) || 0) * (Number(p.largo) || 0) / 1e6;
  }
  $("#totales").textContent = `${estado.proyecto.piezas.length} renglones · ${piezas} piezas · ${num(m2, 3)} m² (sin pulido)`;
}
$("#p-codigo").addEventListener("change", (e) => { estado.proyecto.codigo = e.target.value.trim(); guardarBorrador(); });
$("#p-descripcion").addEventListener("change", (e) => { estado.proyecto.descripcion = e.target.value.trim(); guardarBorrador(); });
$("#b-renglon").addEventListener("click", agregarRenglon);
$("#b-nuevo").addEventListener("click", () => {
  if (estado.proyecto.piezas.length && !confirm("¿Empezar un proyecto nuevo? Lo que no guardaste se pierde.")) return;
  estado.proyecto = { codigo: "", descripcion: "", piezas: [] };
  guardarBorrador();
  dibujarGrilla();
  $("#revision").hidden = true;
});
$("#b-guardar").addEventListener("click", async () => {
  if (!estado.proyecto.codigo) { mensaje("Poné un código de proyecto para guardarlo", true); $("#p-codigo").focus(); return; }
  try {
    let r;
    try { r = await api("/api/proyectos", { method: "POST", body: entradaCalculo() }); }
    catch (e) {
      if (e.status !== 409 || !confirm(`${e.message}. ¿Reemplazarlo?`)) throw e;
      r = await api("/api/proyectos?sobrescribir=1", { method: "POST", body: entradaCalculo() });
    }
    mensaje(`Guardado en proyectos/${r.archivo}`);
  } catch (e) { mensaje(e.message, true); }
});
$("#b-abrir").addEventListener("click", async () => {
  const lista = await api("/api/proyectos");
  const cuerpo = $("#va-lista tbody");
  cuerpo.innerHTML = "";
  $("#va-vacio").hidden = lista.length > 0;
  for (const p of lista) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${esc(p.codigo)}</td><td>${esc(p.descripcion)}</td><td>${p.renglones}</td><td>${esc(p.modificado)}</td>`;
    tr.addEventListener("click", async () => {
      if (hayPiezas() && !confirm(`¿Abrir ${p.codigo}? Reemplaza el proyecto que está cargado (lo que no guardaste se pierde).`)) return;
      const d = await api("/api/proyectos/" + encodeURIComponent(p.archivo));
      estado.proyecto = { codigo: d.proyecto?.codigo || "", descripcion: d.proyecto?.descripcion || "", piezas: d.piezas || [] };
      if (d.preset) $("#preset").value = d.preset;
      if (d.opciones?.esfuerzo) $("#esfuerzo").value = d.opciones.esfuerzo;
      guardarBorrador();
      dibujarGrilla();
      cerrarVentanas();
      mensaje(`Abierto ${p.codigo}`);
    });
    cuerpo.appendChild(tr);
  }
  abrirVentana("#v-abrir");
});

// ------------------------------------------------- pegar e importar (vista previa)
function abrirVentana(id) {
  $("#velo").hidden = false;
  $$(".ventana").forEach((v) => (v.hidden = "#" + v.id !== id));
}
function cerrarVentanas() { $("#velo").hidden = true; }
$$(".ventana .cerrar").forEach((b) => b.addEventListener("click", cerrarVentanas));
$("#velo").addEventListener("click", (e) => { if (e.target.id === "velo") cerrarVentanas(); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") cerrarVentanas(); });

function abrirPegar(texto = "") {
  $("#vi-titulo").textContent = "Pegar desde Excel";
  $("#vi-texto").hidden = false;
  $("#vi-previa").hidden = false;
  $("#vi-texto").value = texto;
  $("#vi-resultado").innerHTML = "";
  $("#vi-agregar").disabled = $("#vi-reemplazar").disabled = true;
  abrirVentana("#v-importar");
  if (texto) vistaPrevia(); else $("#vi-texto").focus();
}
$("#b-pegar").addEventListener("click", () => abrirPegar());
$("#vi-previa").addEventListener("click", vistaPrevia);
async function vistaPrevia() {
  try {
    mostrarImportacion(await api("/api/importar/texto", { method: "POST", body: { texto: $("#vi-texto").value } }));
  } catch (e) { mensaje(e.message, true); }
}
function mostrarImportacion(imp) {
  estado.importado = imp;
  const columnas = Object.entries(imp.columnas).map(([c, d]) => `<b>${esc(c)}</b>: ${esc(d)}`).join(" · ");
  const filas = imp.piezas.slice(0, 200).map((p) => `<tr><td>${esc(p.item)}</td><td>${esc(p.material)}</td><td>${p.cantidad}</td><td>${p.ancho}</td><td>${p.largo}</td><td>${esc(p.clase || "")}</td><td>${esc(p.descripcion || "")}</td></tr>`).join("");
  const avisos = imp.avisos.length ? `<div class="revision"><b>Avisos</b><ul>${imp.avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></div>` : "";
  $("#vi-resultado").innerHTML = `<p class="ayuda">Columnas detectadas: ${columnas || "ninguna"}</p>${avisos}
    <p><b>${imp.piezas.length}</b> renglones para importar${imp.piezas.length > 200 ? " (se muestran los primeros 200)" : ""}.</p>
    <table class="lista"><thead><tr><th>Ítem</th><th>Material</th><th>Cant.</th><th>Ancho</th><th>Largo</th><th>Clase</th><th>Descripción</th></tr></thead><tbody>${filas}</tbody></table>`;
  $("#vi-agregar").disabled = $("#vi-reemplazar").disabled = imp.piezas.length === 0;
}
function aceptarImportacion(reemplazar) {
  const imp = estado.importado || { piezas: [], columnas: {} };
  let piezas = imp.piezas;
  // Los renglones vacíos (como el que hay al empezar) no se dejan.
  estado.proyecto.piezas = reemplazar ? [] : estado.proyecto.piezas.filter((p) => !renglonVacio(p));
  if (!reemplazar && !("item" in imp.columnas)) {
    // Sin columna de ítem, el importador numera desde 1: se sigue la numeración del proyecto.
    const ultimo = Math.max(0, ...estado.proyecto.piezas.map((p) => parseInt(p.item, 10)).filter((n) => !isNaN(n)));
    piezas = piezas.map((p, i) => ({ ...p, item: String(ultimo + i + 1) }));
  }
  estado.proyecto.piezas.push(...piezas.map((p) => ({ rota: null, clase: "", descripcion: "", ...p })));
  guardarBorrador();
  dibujarGrilla();
  cerrarVentanas();
  mensaje(`${piezas.length} renglones agregados`);
}
$("#vi-agregar").addEventListener("click", () => aceptarImportacion(false));
$("#vi-reemplazar").addEventListener("click", () => aceptarImportacion(true));
$("#b-importar").addEventListener("click", () => $("#archivo").click());
$("#archivo").addEventListener("change", async (e) => {
  const archivo = e.target.files[0];
  if (!archivo) return;
  const datos = await new Promise((ok, mal) => {
    const lector = new FileReader();
    lector.onload = () => ok(String(lector.result).split(",")[1] || "");
    lector.onerror = mal;
    lector.readAsDataURL(archivo);
  });
  e.target.value = "";
  try {
    const imp = await api("/api/importar/archivo", { method: "POST", body: { nombre: archivo.name, datos } });
    $("#vi-titulo").textContent = `Importar ${archivo.name}`;
    $("#vi-texto").hidden = true;
    $("#vi-previa").hidden = true;
    abrirVentana("#v-importar");
    mostrarImportacion(imp);
  } catch (err) { mensaje(err.message, true); }
});
// Ctrl+V en la pestaña Proyecto (fuera de un campo) abre la vista previa con lo pegado.
document.addEventListener("paste", (e) => {
  if (!$("#proyecto").classList.contains("activa") || !$("#velo").hidden) return;
  const destino = e.target;
  const texto = e.clipboardData.getData("text");
  const esTabla = texto.includes("\t") || texto.trim().includes("\n");
  if (destino.tagName === "INPUT" && !esTabla) return;
  e.preventDefault();
  abrirPegar(texto);
});

// ------------------------------------------------------- revisar y calcular
function entradaCalculo() {
  return {
    proyecto: { codigo: estado.proyecto.codigo || "SIN-CODIGO", descripcion: estado.proyecto.descripcion || "" },
    preset: $("#preset").value,
    piezas: estado.proyecto.piezas.map((p) => {
      const d = { item: p.item, material: p.material, cantidad: p.cantidad, ancho: p.ancho, largo: p.largo };
      if (p.rota === true || p.rota === false) d.rota = p.rota;
      if (p.clase) d.clase = p.clase;
      if (p.descripcion) d.descripcion = p.descripcion;
      if (p.origen) d.origen = p.origen;
      return d;
    }),
    opciones: { esfuerzo: $("#esfuerzo").value },
  };
}
async function revisar() {
  const r = await api("/api/revisar", { method: "POST", body: entradaCalculo() });
  const caja = $("#revision");
  caja.hidden = false;
  if (!r.errores.length && !r.avisos.length) {
    caja.className = "revision bien";
    caja.innerHTML = `Todo en orden: ${r.piezas} piezas de ${r.materiales.length} material(es).`;
  } else {
    caja.className = "revision" + (r.errores.length ? " mal" : "");
    caja.innerHTML = `<b>Antes de calcular, mirá esto:</b><ul>` +
      r.errores.map((e) => `<li class="error">${esc(e)}</li>`).join("") +
      r.avisos.map((a) => `<li>${esc(a)}</li>`).join("") + "</ul>";
  }
  return r;
}
$("#b-revisar").addEventListener("click", () => revisar().catch((e) => mensaje(e.message, true)));
$("#b-calcular").addEventListener("click", calcular);
async function calcular() {
  if (!estado.proyecto.piezas.length) { mensaje("No hay piezas cargadas", true); return; }
  try {
    const r = await revisar();
    if (r.errores.length && !confirm("Hay renglones con errores que no se van a calcular (ver la lista). ¿Calcular igual el resto?")) return;
    if (!r.errores.length && r.avisos.length && !confirm(`Hay ${r.avisos.length} aviso(s) para mirar antes de calcular (ver la lista). ¿Calcular igual?`)) return;
    const c = await api("/api/calcular", { method: "POST", body: entradaCalculo() });
    estado.calculo = c.id;
    $("#proceso").hidden = false;
    $("#c-ayuda").hidden = true;
    $("#b-cancelar").disabled = false;
    $("#b-cancelar").textContent = "Cancelar (quedarse con lo mejor hasta ahora)";
    $("#b-calcular").disabled = true;
    irA("calcular");
    sondear();
  } catch (e) { mensaje(e.message, true); }
}
function dibujarTorta(avance) {
  const svg = $("#torta");
  const cx = 110, cy = 65, rx = 105, ry = 60;
  const ang = Math.min(avance, 0.999) * 2 * Math.PI;
  const x = cx + rx * Math.sin(ang), y = cy - ry * Math.cos(ang);
  const grande = ang > Math.PI ? 1 : 0;
  svg.innerHTML = `<ellipse cx="${cx + 3}" cy="${cy + 4}" rx="${rx}" ry="${ry}" fill="#000"/>
    <ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#008080"/>
    ${avance > 0 ? `<path d="M${cx},${cy} L${cx},${cy - ry} A${rx},${ry} 0 ${grande} 1 ${x},${y} Z" fill="#00ff00"/>` : ""}
    <text x="${cx}" y="${cy + 8}" text-anchor="middle" font-size="22" fill="#fff" font-family="Arial">${Math.round(avance * 100)}%</text>`;
}
async function sondear() {
  clearTimeout(estado.sondeo);
  if (!estado.calculo) return;
  let c;
  try { c = await api("/api/calculo/" + estado.calculo); } catch (e) { mensaje(e.message, true); $("#b-calcular").disabled = false; return; }
  const p = c.progreso || {};
  $("#c-material").textContent = p.material || "—";
  $("#c-tiempo").textContent = hms(c.segundos);
  $("#c-estimado").textContent = hms(c.estimado);
  $("#c-restante").textContent = c.estimado ? hms(c.estimado - c.segundos) : "--:--:--";
  $("#c-montaje").textContent = String(p.montajes || 0).padStart(3, "0");
  const fases = { secuencial: "armando montajes (heurística)", columnas: "buscando mejores montajes", entera: "eligiendo la mejor combinación", buceo: "probando combinaciones exactas", juntar: "juntando el sobrante" };
  $("#c-fase").textContent = (p.materiales > 1 ? `Material ${p.numero_material} de ${p.materiales} · ` : "") + (fases[p.fase] || "");
  dibujarTorta(c.avance || 0);
  if (c.estado === "calculando") { estado.sondeo = setTimeout(sondear, 500); return; }
  $("#b-cancelar").disabled = true;
  $("#b-calcular").disabled = false;
  if (c.estado === "error") { mensaje("El cálculo falló: " + c.error, true); return; }
  estado.resultado = c;
  mostrarResultados();
  irA("resultados");
  mensaje(c.estado === "cancelado" ? "Cálculo cancelado: se muestra lo mejor encontrado" : "Cálculo terminado");
}
$("#b-cancelar").addEventListener("click", async () => {
  if (!estado.calculo) return;
  $("#b-cancelar").disabled = true;
  $("#b-cancelar").textContent = "Cancelando… (termina el paso que está haciendo)";
  try { await api(`/api/calculo/${estado.calculo}/cancelar`, { method: "POST" }); } catch (e) { mensaje(e.message, true); }
});

// =================================================================== RESULTADOS
function urlInforme(modo) { return `/api/calculo/${estado.calculo}/informe.html?modo=${modo}&coma=${$("#decimal").value}`; }
function mostrarResultados() {
  const r = estado.resultado;
  $("#r-vacio").hidden = !!r;
  $("#r-marco").hidden = !r;
  $("#r-botones").hidden = !r;
  if (!r) return;
  const aviso = $("#r-aviso");
  if (r.verificado === false) {
    aviso.hidden = false;
    aviso.className = "revision mal";
    aviso.innerHTML = "<b>El validador encontró un problema en este resultado: no lo uses para cotizar.</b> El detalle está en el informe.";
  } else if (r.completo === false) {
    aviso.hidden = false;
    aviso.className = "revision mal";
    aviso.innerHTML = "<b>Resultado incompleto: hay piezas que no se calcularon.</b> Las planchas no las incluyen; los errores están en el informe.";
  } else { aviso.hidden = true; }
  $("#r-marco").src = urlInforme("detalle");
}
function imprimir(modo) {
  const w = window.open(urlInforme(modo), "_blank");
  if (!w) { mensaje("El navegador bloqueó la ventana: permití ventanas emergentes para imprimir", true); return; }
  w.addEventListener("load", () => setTimeout(() => w.print(), 300));
}
$("#r-imp-informe").addEventListener("click", () => imprimir("informe"));
$("#r-imp-miniaturas").addEventListener("click", () => imprimir("miniaturas"));
$("#r-imp-detalle").addEventListener("click", () => imprimir("detalle"));
$("#r-xlsx").addEventListener("click", () => (location.href = `/api/calculo/${estado.calculo}/consumo.xlsx`));
$("#r-csv").addEventListener("click", () => (location.href = `/api/calculo/${estado.calculo}/consumo.csv?coma=1`));
$("#r-json").addEventListener("click", () => window.open(`/api/calculo/${estado.calculo}/resultado.json`, "_blank"));
$("#decimal").addEventListener("change", () => { if (estado.resultado) mostrarResultados(); totales(); });

// =================================================================== COMPARAR
function dibujarComparar() {
  const r = estado.resultado;
  $("#cmp-vacio").hidden = !!r;
  const cuerpo = $("#cmp-tabla tbody");
  cuerpo.innerHTML = "";
  if (!r) return;
  for (const m of r.resumen) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${esc(m.codigo)} <span class="ayuda">${esc(m.descripcion)}</span></td>
      <td><input data-c="planchas" type="number" min="0"></td><td><input data-c="layouts" type="number" min="0"></td>
      <td><input data-c="aprov" type="number" min="0" max="100" step="0.01"></td>
      <td>${m.planchas}</td><td>${m.layouts}</td><td>${num(m.aprovechamiento, 2)}</td><td class="minimo">…</td><td class="dif"></td>`;
    const actualizar = () => {
      const cc = Number($('[data-c="planchas"]', tr).value);
      const td = $(".dif", tr);
      if (!$('[data-c="planchas"]', tr).value) { td.textContent = ""; return; }
      const d = m.planchas - cc;
      td.textContent = d === 0 ? "igual" : (d > 0 ? `+${d} (peor)` : `${d} (mejor)`);
      td.className = "dif " + (d > 0 ? "peor" : d < 0 ? "mejor" : "");
    };
    $$("input", tr).forEach((i) => i.addEventListener("input", actualizar));
    cuerpo.appendChild(tr);
  }
  // El mínimo teórico sale del resultado completo.
  api(`/api/calculo/${estado.calculo}/resultado.json`).then((res) => {
    $$("#cmp-tabla tbody tr").forEach((tr, i) => { $(".minimo", tr).textContent = res.materiales[i]?.minimo_teorico_planchas ?? "-"; });
  }).catch(() => {});
}

// =================================================================== MATERIALES
async function cargarMateriales() {
  estado.materiales = await api("/api/materiales");
  const datalist = document.getElementById("lista-materiales") || document.body.appendChild(Object.assign(document.createElement("datalist"), { id: "lista-materiales" }));
  datalist.innerHTML = estado.materiales.map((m) => `<option value="${esc(m.codigo)}">${esc(m.descripcion)}</option>`).join("");
  dibujarListaMateriales();
}
function dibujarListaMateriales() {
  const filtro = $("#m-filtro").value.trim().toUpperCase();
  const cuerpo = $("#m-lista tbody");
  cuerpo.innerHTML = "";
  for (const m of estado.materiales) {
    if (filtro && !m.codigo.includes(filtro) && !m.descripcion.toUpperCase().includes(filtro)) continue;
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${esc(m.codigo)}${m.ajustado ? " ✎" : ""}</td><td>${esc(m.descripcion)}</td><td>${esc(m.color)}</td>`;
    if (estado.material && estado.material.codigo === m.codigo) tr.classList.add("elegido");
    tr.addEventListener("click", () => abrirMaterial(m.codigo));
    cuerpo.appendChild(tr);
  }
}
$("#m-filtro").addEventListener("input", dibujarListaMateriales);
$("#preset").addEventListener("change", () => { if (estado.material) abrirMaterial(estado.material.codigo); });

async function abrirMaterial(codigo, sub = "fisicas") {
  try { estado.material = await api(`/api/materiales/${encodeURIComponent(codigo)}?preset=${$("#preset").value}`); }
  catch (e) { mensaje(e.message, true); return; }
  dibujarListaMateriales();
  dibujarFicha(sub);
}
function campo(nombre, etiqueta, unidad = "mm", extra = "") {
  const m = estado.material;
  return `<label>${etiqueta ? etiqueta + " " : ""}<input type="number" min="0" data-f="${nombre}" value="${esc(m[nombre])}" ${extra}> ${unidad}
    <span class="defecto">(${esc(m.base[nombre])})</span></label>`;
}
// Dibujitos como los de la captura 4 de Corte Certo (verde agua = piezas, amarillo = sobrante).
const ICONOS = {
  sierra: '<rect x="2" y="4" width="22" height="12" fill="#0bb"/><rect x="28" y="4" width="22" height="12" fill="#0bb"/><rect x="2" y="20" width="48" height="10" fill="#0bb"/><path d="M24 34 L28 34 M24 31 L24 37 M28 31 L28 37" stroke="#000"/>',
  destaque: '<rect x="2" y="4" width="38" height="28" fill="#0bb" stroke="#000"/><rect x="40" y="4" width="8" height="28" fill="#ff0" stroke="#000"/><path d="M40 1 L48 1" stroke="#000"/>',
  rotacion: '<rect x="2" y="6" width="10" height="24" fill="#0bb" stroke="#000"/><path d="M13 18 L20 18 M17 15 L20 18 L17 21" stroke="#000" fill="none"/><rect x="22" y="6" width="26" height="24" fill="#ff0" stroke="#000"/><rect x="22" y="6" width="10" height="24" fill="#0bb" stroke="#000"/>',
  retazo: '<rect x="2" y="4" width="34" height="28" fill="#0bb" stroke="#000"/><rect x="36" y="4" width="12" height="28" fill="#ff0" stroke="#000"/>',
  constante: '<rect x="2" y="12" width="10" height="10" fill="#0bb" stroke="#000"/><rect x="18" y="8" width="14" height="14" fill="#0bb" stroke="#000"/><rect x="34" y="4" width="16" height="18" fill="#ff0" stroke="#000"/>',
  espesor: '<path d="M4 24 L36 14 L50 18 L18 28 Z" fill="#0aa" stroke="#000"/><path d="M4 24 L4 27 L18 31 L18 28" fill="#077" stroke="#000"/>',
  peso: '<rect x="8" y="6" width="36" height="6" fill="#0aa" stroke="#000"/><rect x="10" y="14" width="32" height="18" fill="#ddd" stroke="#000"/><circle cx="26" cy="23" r="6" fill="#fff" stroke="#000"/>',
  maximo: '<rect x="4" y="6" width="40" height="6" fill="#0aa" stroke="#000"/><rect x="4" y="14" width="40" height="6" fill="#0aa" stroke="#000"/><rect x="4" y="22" width="40" height="6" fill="#0aa" stroke="#000"/>',
};
function icono(nombre) { return `<svg class="icono" viewBox="0 0 52 38" width="52" height="38" aria-hidden="true">${ICONOS[nombre]}</svg>`; }
function radio(nombre, opciones) {
  const m = estado.material;
  return opciones.map(([valor, etiqueta, recomendado]) =>
    `<label>${recomendado ? '<span class="recomendado">*</span> ' : ""}<input type="radio" name="${nombre}" data-f="${nombre}" value="${valor}" ${String(m[nombre]) === String(valor) ? "checked" : ""}> ${etiqueta}</label>`).join("");
}
function dibujarFicha(sub) {
  const m = estado.material;
  const com = (m.locales && m.locales.comercial) || {};
  const ajustado = Object.keys(m.locales || {}).length > 0;
  const avisos = m.avisos.length ? `<div class="revision">${m.avisos.map(esc).join("<br>")}</div>` : "";
  const planchas = m.planchas.map((p, i) => `<tr><td><input type="checkbox" data-plancha="${p.ancho}x${p.largo}" ${p.habilitada ? "checked" : ""}></td>
      <td>${p.ancho} × ${p.largo}</td><td>${p.corte_banda}</td><td>${p.ancho - p.corte_banda - m.margen_izquierda_mm - m.margen_derecha_mm} × ${p.largo - m.margen_arriba_mm - m.margen_abajo_mm}</td>
      <td>${p.supuesta ? "<b>SUPUESTA</b> " : ""}${esc(p.origen)}</td></tr>`).join("");
  $("#m-ficha").innerHTML = `
    <div class="subpestanas">
      <button data-sub="descripcion">Descripción</button><button data-sub="fisicas">Propiedades físicas</button>
      <button data-sub="comerciales">Propiedades comerciales</button><button data-sub="planchas">Planchas</button>
    </div>
    <div class="franja">Los valores aquí definidos valen para el material ${esc(m.codigo)}. La sierra, el destaque y el pulido recto, solo con «${esc($("#preset").selectedOptions[0].text)}»; lo demás, con todos los presets.</div>
    ${avisos}
    <div data-panel="descripcion" class="descripcion-campos">
      <span>Código</span><b>${esc(m.codigo)}</b>
      <span>Descripción</span><input data-f="descripcion" value="${esc(m.descripcion)}">
      <span>Color</span><input data-f="color" value="${esc(m.color)}">
      <span>Está en hojas.csv</span><span>${m.en_hojas_csv ? "Sí" : "<b>No</b> (planchas supuestas)"}</span>
    </div>
    <div data-panel="fisicas" class="grupos fisicas">
      <fieldset class="g-sierra"><legend>Ancho de la sierra</legend>${icono("sierra")}${campo("separacion_piezas_mm", "")}<span class="ayuda">separación entre piezas</span></fieldset>
      <fieldset class="g-destaque"><legend>Ancho mínimo de destaque</legend>${icono("destaque")}${campo("destaque_min_mm", "")}</fieldset>
      <fieldset class="g-rotacion"><legend>Rotación permitida</legend>${icono("rotacion")}${radio("rotacion", [["true", "SI", true], ["false", "NO"]])}</fieldset>
      <fieldset class="g-textura"><legend>Textura</legend>${radio("textura", [["horizontal", "Horizontal"], ["vertical", "Vertical"], ["sin", "Sem (sin textura)"]])}</fieldset>
      <fieldset class="g-retazo"><legend>Genera retazo</legend>${icono("retazo")}
        <div class="retazo">${radio("genera_retazo", [["true", "SI"], ["false", "NO"]])}
        <div>${campo("retazo_ancho_min_mm", "Ancho mínimo para retazo:")}${campo("retazo_largo_min_mm", "Largo mínimo para retazo:")}
        <label><input type="checkbox" data-f="usar_area_min" ${m.usar_area_min ? "checked" : ""}> Utilice el área mínima</label>
        ${campo("retazo_area_min_m2", "", "m2", 'step="0.01"')}</div></div></fieldset>
      <fieldset class="g-constante"><legend>Agrega una constante en las dimensiones de los pedazos de este material</legend>
        ${icono("constante")}${campo("constante_ancho_mm", "Ancho")}${campo("constante_largo_mm", "Largo")}
        <span class="ayuda">(Agrega en la anchura y en la altura tecleada en el orden)</span></fieldset>
      <fieldset class="g-espesor"><legend>Espesor</legend>${icono("espesor")}${campo("espesor_mm", "", "mm", 'step="0.1"')}</fieldset>
      <fieldset class="g-peso"><legend>Pese específico</legend>${icono("peso")}${campo("peso_kg_m2", "", "Kg / m2", 'step="0.1"')}</fieldset>
      <fieldset class="g-margen"><legend>Margen de seguridad para la plancha</legend>
        <div class="margenes">
          <span></span>${campo("margen_arriba_mm", "", "")}<span></span>
          ${campo("margen_izquierda_mm", "", "")}<div class="plancha-mini"></div>${campo("margen_derecha_mm", "", "")}
          <span></span>${campo("margen_abajo_mm", "", "")}<span></span>
        </div><span class="ayuda">( 0 ... 500 mm )</span></fieldset>
      <fieldset class="g-maximo"><legend>Máximo tamaño cortado (usado en guillotinas)</legend>${icono("maximo")}${radio("corte_max_libre", [["true", "Libre", true], ["false", "Limitado"]])}
        ${campo("corte_max_mm", "", "mm")}<span class="ayuda">( 10 ... 10000 mm ) — se controla con aviso</span></fieldset>
      <fieldset class="g-pulido"><legend>Cristalux: pulido recto</legend>${campo("sobremedida_pulido_mm", "+")}<span class="ayuda">se suma al ancho y al largo de las piezas con clase PR</span></fieldset>
    </div>
    <div data-panel="comerciales">
      <p class="provisorio">Provisorio: no hay captura de esta pestaña de Corte Certo (pregunta 7). Los precios se guardan pero todavía no se usan en el cálculo.</p>
      <div class="descripcion-campos">
        <span>Precio m² de plancha</span><input type="number" step="0.01" data-com="precio_m2_plancha" value="${esc(com.precio_m2_plancha ?? "")}">
        <span>Precio m² de retazo</span><input type="number" step="0.01" data-com="precio_m2_retazo" value="${esc(com.precio_m2_retazo ?? "")}">
      </div>
    </div>
    <div data-panel="planchas" style="padding:10px">
      <table class="lista"><thead><tr><th>Usar</th><th>Hoja</th><th>Corte banda</th><th>Plancha útil</th><th>De dónde sale</th></tr></thead><tbody>${planchas}</tbody></table>
      <p class="ayuda">Las medidas salen de <code>config/hojas.csv</code> (planilla Medidas_hojas.xlsx). Destildá una medida para no usarla en este material.</p>
    </div>
    <div class="pie-ficha">
      <span class="ayuda observacion">💡 Observación: las opciones que normalmente ofrecen los resultados más buenos son marcados en <span class="recomendado">rojo</span>, con el símbolo <span class="recomendado">*</span>. El número rojo entre paréntesis es el valor de la configuración.</span>
      <span class="estado-ajuste">${ajustado ? "✎ Este material tiene cambios guardados en esta PC." : ""}</span>
      <button id="m-restaurar" ${ajustado ? "" : "disabled"}>Volver a los valores de la configuración</button>
      <button class="principal" id="m-guardar">Ok (guardar en esta PC)</button>
    </div>`;
  const mostrar = (s) => {
    $$("#m-ficha .subpestanas button").forEach((b) => b.classList.toggle("activa", b.dataset.sub === s));
    $$("#m-ficha [data-panel]").forEach((p) => (p.hidden = p.dataset.panel !== s));
  };
  $$("#m-ficha .subpestanas button").forEach((b) => b.addEventListener("click", () => mostrar(b.dataset.sub)));
  mostrar(sub);
  $("#m-guardar").addEventListener("click", guardarMaterial);
  $("#m-restaurar").addEventListener("click", async () => {
    await api(`/api/materiales/${encodeURIComponent(m.codigo)}/locales`, { method: "DELETE" });
    estado.materiales = await api("/api/materiales");
    abrirMaterial(m.codigo);
    mensaje("Valores de la configuración restaurados");
  });
}
async function guardarMaterial() {
  const m = estado.material;
  const cambios = {};
  const valor = (el) => {
    if (el.type === "checkbox") return el.checked;
    if (el.type === "radio") return el.value === "true" ? true : el.value === "false" ? false : el.value;
    if (el.type === "number") return el.value === "" ? null : Number(el.value);
    return el.value;
  };
  for (const el of $$("#m-ficha [data-f]")) {
    if (el.type === "radio" && !el.checked) continue;
    const f = el.dataset.f;
    const v = valor(el);
    if (v === null) continue;
    if (String(v) !== String(m.base[f] ?? m[f])) cambios[f] = v;
  }
  const habilitadas = {};
  let algunaApagada = false;
  for (const el of $$("#m-ficha [data-plancha]")) {
    habilitadas[el.dataset.plancha] = el.checked;
    if (!el.checked) algunaApagada = true;
  }
  if (algunaApagada) cambios.planchas_habilitadas = habilitadas;
  const com = {};
  for (const el of $$("#m-ficha [data-com]")) if (el.value !== "") com[el.dataset.com] = Number(el.value);
  if (Object.keys(com).length) cambios.comercial = com;
  try {
    // Reemplaza lo guardado para este material (los cambios de la sierra, el destaque y el pulido
    // de otros presets se conservan).
    await api(`/api/materiales/${encodeURIComponent(m.codigo)}?preset=${$("#preset").value}`, { method: "PUT", body: cambios });
    estado.materiales = await api("/api/materiales");
    abrirMaterial(m.codigo);
    mensaje(Object.keys(cambios).length ? `Guardado (${Object.keys(cambios).length} cambio(s) en esta PC)` : "Sin cambios: se usan los valores de la configuración");
  } catch (e) { mensaje(e.message, true); }
}

// ======================================================================= inicio
(async function inicio() {
  try {
    const e = await api("/api/estado");
    $("#version").textContent = "v" + e.version;
  } catch (err) { mensaje("No se pudo conectar con el programa: ¿está abierta la ventana negra?", true); }
  leerBorrador();
  if (!estado.proyecto.piezas.length) agregarRenglon(); else dibujarGrilla();
  cargarMateriales().catch(() => {});
  dibujarTorta(0);
  $("#proceso").hidden = true;
  mostrarResultados();
})();
