"""Página de revisión de la validación histórica (brief §10.3), como las de la water jet:

- caso por caso, nuestros montajes dibujados al lado de los números de Corte Certo;
- filtros: peores, mejores, iguales, no se pudo leer, no cierran;
- Juan marca bien / mal / duda (queda guardado en su navegador);
- un botón copia sus respuestas como texto para pegar en la sesión.

Una sola página HTML, sin internet. La versión "para git" (`publicable=True`) no incluye los
textos crudos de las observaciones (por si la limpieza de nombres falló en alguno).
"""

from __future__ import annotations

import json
from html import escape

from .. import dibujo


def html(filas: list[dict], eleccion: dict, prueba: dict, cobertura: dict, montajes: dict,
         publicable: bool = False) -> str:
    """`filas`: resultados (uno por caso, material e hipótesis). `montajes`: (numero, material) ->
    lista de montajes del resultado elegido (para dibujar)."""
    elegidas = [f for f in filas if f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0")]
    elegidas.sort(key=lambda f: (-(f["planchas"] - f["cc_hojas"]), f["numero"], f["material"]))
    t = prueba.get("total", {})
    partes = [_CABEZA,
              "<h1>Validación contra Corte Certo</h1>",
              f"<p class='resumen'>Casos comparados: <b>{len(elegidas)}</b> "
              f"(prueba: {sum(1 for f in elegidas if not f['calibracion'])}). "]
    if t.get("casos"):
        partes.append(f"Sobre el 30 % de prueba: iguales <b>{t['iguales_%']} %</b>, con menos planchas "
                      f"<b>{t['mejores_%']} %</b>, con más planchas <b>{t['peores_%']} %</b>; diferencia media "
                      f"<b>{t['diferencia_media']:+}</b>.")
    partes.append("</p><div class='filtros'>Mostrar: "
                  "<button data-f='todos' class='activo'>Todos</button>"
                  "<button data-f='peor'>Peores</button><button data-f='mejor'>Mejores</button>"
                  "<button data-f='igual'>Iguales</button><button data-f='prueba'>Solo el 30 % de prueba</button>"
                  "<button data-f='sinmarcar'>Sin marcar</button>"
                  " &nbsp; <button id='copiar' class='principal'>Copiar mis respuestas</button>"
                  "<span id='copiado'></span></div>")
    for f in elegidas:
        dif = f["planchas"] - f["cc_hojas"]
        clase = "peor" if dif > 0 else "mejor" if dif < 0 else "igual"
        clave = f"{f['numero']}|{f['material']}"
        minis = "".join(dibujo.miniatura(m, ancho_px=96, max_pila=8) for m in montajes.get(clave, [])[:14])
        partes.append(
            f"<div class='caso {clase} {'prueba' if not f['calibracion'] else 'calibra'}' data-clave='{escape(clave)}'>"
            f"<div class='cab'><b>Presupuesto {escape(f['numero'])}</b> · {escape(f['material'])} "
            f"<span class='gris'>(leyenda: «{escape(f['abreviado'])}», {escape(f['relacion'])})</span>"
            f"<span class='dif {clase}'>{'igual' if dif == 0 else f'{dif:+d} plancha(s)'}</span></div>"
            f"<table class='num'><tr><th></th><th>Planchas</th><th>Aprov.</th><th>Montajes</th></tr>"
            f"<tr><td>Corte Certo</td><td>{f['cc_hojas']}</td><td>{f['cc_aprov']:g} %</td><td>—</td></tr>"
            f"<tr><td>Nuestro ({escape(f['hipotesis'])})</td><td>{f['planchas']}</td><td>{f['aprovechamiento']:g} %</td>"
            f"<td>{f['montajes']}</td></tr>"
            f"<tr><td>Mínimo teórico</td><td>{f['minimo']}</td><td></td><td></td></tr></table>"
            f"<div class='gris'>{f['n_piezas']} piezas · plancha {escape(f['plancha'])}"
            f"{'' if f['con_pulido'] else ' · la leyenda cierra SIN el +3 mm de pulido'}"
            f"{'' if f['verificado'] else ' · <b class=peor>NO pasó el validador</b>'}"
            f"{' · calibración' if f['calibracion'] else ' · prueba'}</div>"
            f"<div class='minis'>{minis}</div>"
            f"<div class='marca'>"
            + "".join(f"<label><input type='radio' name='{escape(clave)}' value='{v}'> {v}</label>" for v in ("bien", "mal", "duda"))
            + f" <input class='coment' placeholder='comentario'></div></div>")
    partes.append("<h2>Lo que no se pudo comparar</h2>")
    partes.append(_lista("No cierran (m² de piezas contra hojas y % de la leyenda)", cobertura.get("no_cierran", []),
                         lambda x: f"{x['numero']} {x['material']}: leyenda {x['leyenda']}; probado {x['probado']}"))
    partes.append(_lista("No se pudo relacionar el material", cobertura.get("sin_relacionar", []),
                         lambda x: f"{x['numero']} «{x['material']}»: {x['motivo']} (hay: {', '.join(x['candidatos'])})"))
    partes.append(_lista("Leyenda sin piezas de vidrio reconstruidas", cobertura.get("sin_piezas", []),
                         lambda x: f"{x['numero']}"))
    if not publicable:
        partes.append(_lista("No se pudo leer la leyenda (texto tal cual, para mirar el formato)",
                             cobertura.get("no_leidas", []),
                             lambda x: f"{x['numero']}: " + " / ".join(x["lineas"])))
    else:
        partes.append(f"<p class='gris'>No se pudo leer la leyenda en {len(cobertura.get('no_leidas', []))} "
                      "presupuestos (los textos están en la versión local de esta página).</p>")
    partes.append(_PIE)
    return "".join(partes)


def _lista(titulo: str, elementos: list, texto) -> str:
    if not elementos:
        return f"<h3>{escape(titulo)}: ninguno</h3>"
    filas = "".join(f"<li>{escape(texto(e))}</li>" for e in elementos[:300])
    extra = f"<li>… y {len(elementos) - 300} más</li>" if len(elementos) > 300 else ""
    return f"<h3>{escape(titulo)}: {len(elementos)}</h3><ul class='chica'>{filas}{extra}</ul>"


_CABEZA = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Revisión contra Corte Certo</title>
<style>
body{font:14px Arial,sans-serif;margin:0;padding:12px 16px;background:#f0f0f0;color:#111}
h1{font-size:20px;margin:4px 0} .resumen{margin:4px 0 8px}
.filtros{position:sticky;top:0;background:#f0f0f0;padding:6px 0;z-index:2;border-bottom:1px solid #ccc}
button{font:inherit;padding:3px 10px;border:1px solid #888;background:#fafafa;border-radius:3px;cursor:pointer}
button.activo{background:#cfe0ff} button.principal{background:#0a5c2a;color:#fff;border-color:#064}
.caso{background:#fff;border:1px solid #ccc;margin:8px 0;padding:8px 10px}
.caso.peor{border-left:6px solid #c00}.caso.mejor{border-left:6px solid #0a0}.caso.igual{border-left:6px solid #999}
.cab{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}.dif{margin-left:auto;font-weight:bold}
.dif.peor,b.peor{color:#c00}.dif.mejor{color:#080}.gris{color:#666;font-size:12px}
table.num{border-collapse:collapse;margin:4px 0;font-size:13px}table.num td,table.num th{border:1px solid #ddd;padding:1px 8px;text-align:right}
table.num td:first-child{text-align:left}
.minis{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0}.marca{margin-top:4px}.marca label{margin-right:10px}
.coment{width:50%;min-width:200px}.chica{font-size:12px}
@media(max-width:600px){.coment{width:100%}}
</style></head><body>"""

_PIE = """<script>
(function(){
  var clave='optimizador.revision';
  var guardado={};
  try{guardado=JSON.parse(localStorage.getItem(clave)||'{}');}catch(e){}
  function guardar(){try{localStorage.setItem(clave,JSON.stringify(guardado));}catch(e){}}
  document.querySelectorAll('.caso').forEach(function(c){
    var k=c.dataset.clave, g=guardado[k]||{};
    c.querySelectorAll('input[type=radio]').forEach(function(r){
      if(g.marca===r.value) r.checked=true;
      r.addEventListener('change',function(){guardado[k]=Object.assign(guardado[k]||{},{marca:r.value});guardar();});
    });
    var t=c.querySelector('.coment'); t.value=g.comentario||'';
    t.addEventListener('input',function(){guardado[k]=Object.assign(guardado[k]||{},{comentario:t.value});guardar();});
  });
  document.querySelectorAll('.filtros [data-f]').forEach(function(b){
    b.addEventListener('click',function(){
      document.querySelectorAll('.filtros [data-f]').forEach(function(x){x.classList.toggle('activo',x===b);});
      var f=b.dataset.f;
      document.querySelectorAll('.caso').forEach(function(c){
        var g=guardado[c.dataset.clave]||{};
        var ver=f==='todos'||c.classList.contains(f)||(f==='sinmarcar'&&!g.marca);
        c.style.display=ver?'':'none';
      });
    });
  });
  document.getElementById('copiar').addEventListener('click',function(){
    var lineas=[];
    Object.keys(guardado).sort().forEach(function(k){
      var g=guardado[k]; if(!g.marca&&!g.comentario) return;
      lineas.push(k.replace('|',' ')+': '+(g.marca||'sin marca')+(g.comentario?' — '+g.comentario:''));
    });
    var texto='Revisión contra Corte Certo ('+lineas.length+' casos)\\n'+lineas.join('\\n');
    var listo=function(){document.getElementById('copiado').textContent=' copiado ('+lineas.length+')';};
    if(navigator.clipboard){navigator.clipboard.writeText(texto).then(listo,function(){prompt('Copiá esto:',texto);});}
    else{prompt('Copiá esto:',texto);}
  });
})();
</script></body></html>"""
