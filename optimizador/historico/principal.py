"""`python -m optimizador historico`: la validación histórica de punta a punta.

    python -m optimizador historico                       # muestra de 50 casos (para empezar)
    python -m optimizador historico --todo                # todos los casos (corre en tandas)
    python -m optimizador historico --datos otra/carpeta  # por defecto, datos/casos
    python -m optimizador historico --todo --docs         # además, actualiza docs/VALIDACION.md
    python -m optimizador historico --todo --publicar     # además, copia la página a docs/validacion/

Lo calculado se guarda en `salida/historico/` (no va a git) a medida que sale: si se corta, se
vuelve a correr el mismo comando y sigue desde donde quedó.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from ..configuracion import RAIZ, Catalogo
from . import comparar, datos, exportados, revision

MARCA_INICIO = "<!-- HISTORICO: lo escribe `python -m optimizador historico --docs` -->"
MARCA_FIN = "<!-- /HISTORICO -->"


def ejecutar(carpeta_datos: Path, salida: Path, opciones: comparar.Opciones, docs: bool = False,
             publicar: bool = False, mostrar=print) -> dict:
    carpeta_datos = Path(carpeta_datos)
    if (carpeta_datos / "corte_certo").is_dir():
        carpeta_datos = carpeta_datos / "corte_certo"  # datos/casos/corte_certo (exportados por vidrio)
    if exportados.es_carpeta_exportada(carpeta_datos):
        return ejecutar_exportados(carpeta_datos, salida, opciones, docs, publicar, mostrar)
    catalogo = Catalogo(usar_locales=False)
    casos = datos.leer(carpeta_datos)
    for d in casos.diferencias:
        mostrar(f"aviso (contrato): {d}")
    if not casos.presupuestos:
        mostrar(f"No hay casos en {carpeta_datos}. Ver docs/CONTRATO_DATOS.md.")
        return {}
    inventado = es_inventado(casos)
    if inventado:
        mostrar("aviso: estos datos dicen ser INVENTADOS (caso de juguete); los números no valen como validación")
    trabajos, cobertura = comparar.preparar(casos, catalogo)
    c = cobertura
    mostrar(f"Presupuestos: {c['presupuestos']} · con pinta de leyenda: {c['con_pinta']} · leídos: {c['leidos']} · "
            f"líneas: {c['lineas']} · relacionadas: {c['relacionadas']} · pasan el control: {c['control_ok']}")
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "cobertura.json").write_text(json.dumps(cobertura, ensure_ascii=False, indent=1), encoding="utf-8")
    filas = comparar.correr(trabajos, salida / f"resultados_{opciones.esfuerzo}.jsonl", opciones, catalogo, mostrar)
    eleccion = comparar.calibrar(filas)
    prueba = comparar.informe_prueba(filas, eleccion)
    texto = comparar.markdown(cobertura, eleccion, prueba, opciones, str(carpeta_datos), inventado)
    (salida / "resumen.md").write_text(texto + "\n", encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps({"eleccion": eleccion, "prueba": prueba},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    montajes = {}
    for f in filas:
        if f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0"):
            ruta = salida / "montajes" / comparar.nombre_montajes(f["numero"], f["material"], f["hipotesis"], f["esfuerzo"])
            if ruta.exists():
                montajes[f"{f['numero']}|{f['material']}"] = json.loads(ruta.read_text(encoding="utf-8"))
    corrida = f"{Path(casos.origen).name}|{opciones.esfuerzo}"
    pagina = revision.html(filas, eleccion, prueba, cobertura, montajes, corrida=corrida)
    (salida / "revision.html").write_text(pagina, encoding="utf-8")
    mostrar(f"Página de revisión: {salida / 'revision.html'}")
    if publicar and inventado:
        mostrar("No se copia la página a docs/validacion/: los datos son inventados")
    elif publicar:
        publica = revision.html(filas, eleccion, prueba, cobertura, montajes, publicable=True, corrida=corrida)
        sospechosas = palabras_sospechosas(publica, casos)
        if sospechosas:
            mostrar(f"No se copia la página a docs/validacion/: tiene {len(sospechosas)} palabras que salen de los "
                    f"textos libres del zip y podrían ser nombres (queda solo en salida/historico/)")
        elif len(publica.encode()) >= 5_000_000:
            mostrar("La página pesa más de 5 MB: queda solo en salida/historico/ (no va a git)")
        else:
            destino = RAIZ / "docs" / "validacion" / "revision.html"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(publica, encoding="utf-8")
            mostrar(f"Copiada a {destino} (sin los textos de las observaciones)")
    if docs and inventado:
        mostrar("No se actualiza docs/VALIDACION.md: los datos son inventados")
    elif docs:
        actualizar_validacion(texto)
        mostrar("docs/VALIDACION.md actualizado (sección 1)")
    mostrar(texto)
    return {"cobertura": cobertura, "eleccion": eleccion, "prueba": prueba}


def ruta_para_docs(carpeta: Path) -> str:
    """La carpeta como se escribe en los documentos: relativa al repo si está adentro (sin la ruta
    de la PC donde se corrió)."""
    try:
        return Path(carpeta).resolve().relative_to(RAIZ).as_posix()
    except ValueError:
        return Path(carpeta).name


def ejecutar_exportados(carpeta: Path, salida: Path, opciones: comparar.Opciones, docs: bool = False,
                        publicar: bool = False, mostrar=print) -> dict:
    """Los casos exportados por vidrio (`exportados.py`): una sola hipótesis, H0 (Corte Certo se
    usaba sin separación ni destaque), así que no hay calibración y los números son sobre todos
    los casos comparados."""
    catalogo = Catalogo(usar_locales=False)
    casos = exportados.leer(carpeta)
    trabajos, cob = exportados.preparar(casos, catalogo)
    mostrar(f"Casos: {cob['casos']} · se pueden comparar: {cob['control_ok']} · sin hojas: {len(cob['sin_hojas'])} · "
            f"con bandas: {len(cob['con_bandas'])} · área no cierra: {len(cob['area_no'])} · "
            f"no cierran: {len(cob['no_cierran'])}")
    opciones = comparar.Opciones(esfuerzo=opciones.esfuerzo, muestra=opciones.muestra, hipotesis=("H0",),
                                 procesos=opciones.procesos, repaso_maximo=opciones.repaso_maximo)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "cobertura.json").write_text(json.dumps(cob, ensure_ascii=False, indent=1), encoding="utf-8")
    todas = comparar.correr(trabajos, salida / f"resultados_{opciones.esfuerzo}.jsonl", opciones, catalogo, mostrar)
    filas, vistas = vistas_exportados(todas)
    prueba = comparar.informe_prueba(filas, {}, solo_prueba=False)
    por_origen = {o: comparar.informe_prueba([f for f in filas if (f.get("extra") or {}).get("plancha_origen") == o],
                                             {}, solo_prueba=False)["total"]
                  for o in ("hojas.csv", "leyenda", "deducida")}
    repaso = None
    if opciones.repaso_maximo and opciones.esfuerzo != "maximo":
        repaso = repaso_maximo(trabajos, todas, salida, opciones, catalogo, mostrar)
    evidencia = exportados.evidencia_banda(casos, catalogo)
    texto = exportados.markdown(cob, prueba, opciones, ruta_para_docs(carpeta), por_origen, vistas, evidencia, repaso)
    (salida / "resumen.md").write_text(texto + "\n", encoding="utf-8")
    (salida / "resumen.json").write_text(json.dumps({"prueba": prueba, "vistas": vistas, "por_origen": por_origen,
                                                     "evidencia_banda": evidencia, "repaso_maximo": repaso},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    montajes = {}
    for f in filas:
        ruta = salida / "montajes" / comparar.nombre_montajes(f["numero"], f["material"], f["hipotesis"], f["esfuerzo"])
        if ruta.exists():
            montajes[f"{f['numero']}|{f['material']}"] = json.loads(ruta.read_text(encoding="utf-8"))
    corrida = f"{carpeta.name}|{opciones.esfuerzo}"
    (salida / "revision.html").write_text(revision.html(filas, {}, prueba, cob, montajes, corrida=corrida),
                                          encoding="utf-8")
    mostrar(f"Página de revisión: {salida / 'revision.html'}")
    if publicar:
        publica = revision.html(filas, {}, prueba, cob, montajes, publicable=True, corrida=corrida)
        if len(publica.encode()) >= 5_000_000:
            mostrar("La página pesa más de 5 MB: queda solo en salida/historico/ (no va a git)")
        else:
            destino = RAIZ / "docs" / "validacion" / "revision.html"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(publica, encoding="utf-8")
            mostrar(f"Copiada a {destino}")
    if docs:
        actualizar_validacion(texto)
        mostrar("docs/VALIDACION.md actualizado (sección 1)")
    mostrar(texto)
    return {"cobertura": cob, "prueba": prueba, "vistas": vistas, "por_origen": por_origen,
            "evidencia_banda": evidencia, "repaso_maximo": repaso}


def _total_siempre(fs: list[dict]) -> dict:
    """Totales de una fila "cotizando siempre con…": un caso donde las piezas no entran en esa
    plancha (el cálculo deja piezas afuera) no se puede cotizar así, y cuenta como "más hojas"."""
    total = comparar.informe_prueba(fs, {}, solo_prueba=False)["total"]
    no_entran = sum(1 for f in fs if f["verificado"] and not comparar.cuenta(f))
    if not no_entran:
        return {**total, "no_entran": 0}
    validos = [f for f in fs if comparar.cuenta(f)]
    difs = [f["planchas"] - f["cc_hojas"] for f in validos]
    n = len(validos) + no_entran
    return {**total, "casos": n, "no_entran": no_entran,
            "iguales_%": round(sum(d == 0 for d in difs) / n * 100, 1),
            "mejores_%": round(sum(d < 0 for d in difs) / n * 100, 1),
            "peores_%": round((sum(d > 0 for d in difs) + no_entran) / n * 100, 1)}


def vistas_exportados(todas: list[dict]) -> tuple[list[dict], dict]:
    """Las filas de la cuenta principal (un resultado por caso: la plancha con la que mejor cierra
    el %) y los totales de cada vista de `exportados.VISTAS`. Las variantes (la otra de banda 20 ↔
    hoja entera, cierre o no) solo entran en las filas "siempre con…"."""
    filas = [f for f in todas if not (f.get("extra") or {}).get("alternativa")]
    otras = {(f["numero"], f["material"]): f for f in todas if (f.get("extra") or {}).get("alternativa")}

    def con(variante: str) -> list[dict]:
        salida = []
        for f in filas:
            alt = otras.get((f["numero"], f["material"]))
            usar_alt = alt is not None and f["extra"].get("variante") != variante and alt["extra"].get("variante") == variante
            salida.append(alt if usar_alt else f)
        return salida

    vistas = {"probable": comparar.informe_prueba(filas, {}, solo_prueba=False)["total"],
              "banda": _total_siempre(con("banda 20")), "entera": _total_siempre(con("hoja entera")),
              "seguros": comparar.informe_prueba([f for f in filas if f["extra"].get("unica")], {},
                                                 solo_prueba=False)["total"]}
    return filas, vistas


def repaso_maximo(trabajos: list[dict], todas: list[dict], salida: Path, opciones: comparar.Opciones,
                  catalogo: Catalogo, mostrar=print) -> dict:
    """Repite con esfuerzo máximo los cálculos (casos y variantes) donde el esfuerzo de la corrida
    dio más hojas que Corte Certo, y arma las vistas con esos resultados en lugar de los otros."""
    por_firma = {(f["numero"], f["material"], f["firma"]): f for f in todas}
    peores = [t for t in trabajos if (f := por_firma.get((t["numero"], t["material"], t["firma"])))
              and comparar.cuenta(f) and f["planchas"] > t["cc_hojas"]]
    mostrar(f"Repaso con esfuerzo máximo: {len(peores)} cálculos donde el {opciones.esfuerzo} da más hojas")
    opciones_max = comparar.Opciones(esfuerzo="maximo", muestra=None, hipotesis=opciones.hipotesis,
                                     procesos=opciones.procesos)
    maximos = {(f["numero"], f["material"], f["firma"]): f
               for f in comparar.correr(peores, salida / "resultados_maximo.jsonl", opciones_max, catalogo, mostrar)}
    mezcla = []
    for f in todas:
        m = maximos.get((f["numero"], f["material"], f["firma"]))
        mezcla.append({**m, "extra": f["extra"]} if m is not None and comparar.cuenta(m) else f)
    _, vistas = vistas_exportados(mezcla)
    def es_alt(f):
        return bool((f.get("extra") or {}).get("alternativa"))
    mejoran = [f for f in mezcla if (k := (f["numero"], f["material"], f["firma"])) in maximos
               and comparar.cuenta(maximos[k]) and maximos[k]["planchas"] < por_firma[k]["planchas"]]
    return {"casos": sum(not t["extra"]["alternativa"] for t in peores),
            "alternativas": sum(bool(t["extra"]["alternativa"]) for t in peores),
            "mejoran": sum(not es_alt(f) for f in mejoran), "mejoran_alternativas": sum(es_alt(f) for f in mejoran),
            "segundos_max": max((f["segundos"] for f in maximos.values()), default=0), "vistas": vistas}


def es_inventado(casos: datos.Casos) -> bool:
    """El caso de juguete (y cualquier dato de prueba) lo dice en su LEEME."""
    return bool(re.search(r"TODO INVENTADO|CASO DE JUGUETE", casos.leeme.upper()))


def _palabras(texto: str) -> set[str]:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().upper()
    return {p for p in re.findall(r"[A-Z]{4,}", t)}


def palabras_sospechosas(pagina: str, casos: datos.Casos) -> set[str]:
    """Control de nombres antes de publicar (brief §10.3): palabras de la página que también están en
    los textos libres del zip (observaciones, detalles) y que no son nuestras (no aparecen en el
    código del programa ni en las descripciones de los artículos). Tiene que dar vacío."""
    libres: set[str] = set()
    for fila in casos.presupuestos.values():
        for k, v in fila.items():
            if k not in ("numero", "fecha") and isinstance(v, str):
                libres |= _palabras(v)
    for lista in casos.renglones.values():
        for r in lista:
            libres |= _palabras(r.get("detalle") or "")
    for lista in casos.piezas.values():
        for p in lista:
            libres |= _palabras(p.get("detalle") or "")
    nuestras: set[str] = set()
    for fuente in (Path(__file__).parent.parent).rglob("*.py"):
        nuestras |= _palabras(fuente.read_text(encoding="utf-8"))
    for art in casos.articulos.values():
        nuestras |= _palabras(f"{art.get('codigo', '')} {art.get('descripcion', '')} {art.get('familia', '')}")
    for mat in Catalogo(usar_locales=False).materiales.values():
        nuestras |= _palabras(f"{mat.codigo} {mat.descripcion}")
    texto = re.sub(r"<[^>]+>", " ", pagina)
    return (_palabras(texto) & libres) - nuestras


def actualizar_validacion(texto: str, ruta: Path | None = None, marca: str = "HISTORICO") -> None:
    """Reemplaza en `docs/VALIDACION.md` el bloque entre las marcas (`HISTORICO`: la sección 1,
    contra Corte Certo; `OPTIMA`: la 1.b, contra Optima)."""
    ruta = ruta or RAIZ / "docs" / "VALIDACION.md"
    contenido = ruta.read_text(encoding="utf-8")
    if marca == "HISTORICO":
        inicio, fin = MARCA_INICIO, MARCA_FIN
        titulo = "## 1. Contra Corte Certo (casos históricos)\n"
        nuevo_titulo = None
    else:
        inicio = f"<!-- {marca}: lo escribe `python -m optimizador optima --docs` -->"
        fin = f"<!-- /{marca} -->"
        titulo = "## 2. Banco sintético"
        nuevo_titulo = "## 1.b Contra Optima (cortes reales en planta)\n\n"
    bloque = f"{inicio}\n{texto}\n{fin}"
    if inicio in contenido and fin in contenido:
        antes = contenido.split(inicio)[0]
        despues = contenido.split(fin, 1)[1]
        contenido = antes + bloque + despues
    elif nuevo_titulo is None:
        contenido = contenido.replace(titulo, titulo + "\n" + bloque + "\n", 1)
    else:
        contenido = contenido.replace(titulo, nuevo_titulo + bloque + "\n\n" + titulo, 1)
    ruta.write_text(contenido, encoding="utf-8")
