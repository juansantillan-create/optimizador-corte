"""Informe de cálculo y "Visualizar e imprimir montajes" en HTML, como Corte Certo.

Una sola página HTML, sin nada de internet (CSS y SVG adentro), que sirve para la pantalla y
para imprimir en A4 apaisada con "Imprimir" o "Guardar como PDF" del navegador:

- **Informe de cálculo** (captura 1): proyectos calculados, lista de materiales, planchas usadas,
  perímetro. Abajo, en un recuadro aparte, lo que agregamos nosotros (no está en Corte Certo).
- **Visualizar e imprimir montajes** (captura 2): Datos generales en recuadros negros con números
  en color y las miniaturas (apiladas si se repiten, con ×N).
- **Detalle** de cada montaje: dibujo grande, piezas, sobrantes y cortes en orden.

`modo_impresion`: "informe" (solo el informe), "miniaturas" (informe + montajes, varios por
hoja) o "detalle" (además, un montaje por hoja, grande).
"""

from __future__ import annotations

from html import escape

from . import __version__, colores, dibujo


def numero(x: float, decimales: int, coma: bool = False, sacar_ceros: bool = False) -> str:
    texto = f"{x:.{decimales}f}"
    if sacar_ceros and "." in texto:
        texto = texto.rstrip("0").rstrip(".")
    return texto.replace(".", ",") if coma else texto


def fecha_corte_certo(fecha: str) -> str:
    """'2026-10-25 23:20:19' -> '25/10/26   23:20:19' (como el informe de Corte Certo)."""
    try:
        dia, hora = fecha.split(" ")
        a, m, d = dia.split("-")
        return f"{d}/{m}/{a[2:]}&nbsp;&nbsp;&nbsp;{hora}"
    except ValueError:
        return escape(fecha)


CSS = """
:root { --azul: #00008b; --gris: #808080; }
* { box-sizing: border-box; }
body { margin: 0; background: #f0f0f0; color: #000; font-family: Arial, Helvetica, sans-serif; font-size: 13px; }
.hoja { background: #fff; margin: 10px auto; padding: 12px 18px; max-width: 1180px; }
.cabecera { display: flex; justify-content: space-between; align-items: flex-start; }
.programa { color: var(--gris); font-size: 10px; }
.titulo-informe { text-align: right; }
.titulo-informe h1 { margin: 0; font-size: 17px; color: var(--azul); text-decoration: underline; }
.subtitulo { color: var(--azul); text-decoration: underline; font-size: 12px; margin: 14px 0 2px; }
table.cc { border-collapse: collapse; width: 100%; }
table.cc th { text-align: left; font-weight: bold; padding: 1px 6px 1px 0; }
table.cc td { padding: 1px 6px 1px 0; }
table.cc .sub th, table.cc .sub td.etq { color: var(--gris); font-weight: bold; }
.agregados { border: 1px solid #b0b0b0; background: #fafafa; padding: 6px 10px; margin-top: 14px; font-size: 12px; }
.agregados h3 { margin: 0 0 4px; font-size: 12px; }
.aviso { color: #8a4b00; } .error { color: #b00000; font-weight: bold; }
.ok { color: #006400; font-weight: bold; }
.barra-negra { background: #000; color: #fff; text-align: center; padding: 4px; font-size: 14px; margin-top: 14px; }
table.elegir { border-collapse: collapse; width: 450px; max-width: 100%; }
table.elegir th { color: var(--azul); font-weight: normal; text-align: left; border-bottom: 1px solid #999; border-right: 1px solid #999; padding: 2px 6px; }
table.elegir td { padding: 2px 6px; border-right: 1px solid #ccc; }
table.elegir a { color: #000; text-decoration: none; }
.encabezado-montajes { color: var(--gris); font-size: 13px; border-bottom: 2px solid #999; padding-bottom: 3px; }
.datos-generales { display: flex; align-items: center; gap: 14px; margin: 6px 0 10px; }
.dg-tabla { border-collapse: collapse; }
.dg-tabla td.etq { background: #f0f0f0; border: 1px solid #c0c0c0; text-align: right; padding: 1px 6px; font-size: 11px; }
.dg-tabla td.val { background: #000; text-align: center; min-width: 52px; padding: 1px 6px; font-size: 12px; }
.celeste { color: #00bfff; } .verde { color: #00ff00; } .rojo { color: #ff2020; }
.lamparita { font-size: 11px; max-width: 260px; }
.grilla { display: flex; flex-wrap: wrap; gap: 14px 20px; align-items: flex-end; }
.grilla a { color: #000; text-decoration: none; }
.detalle-montaje { margin-top: 16px; border-top: 1px solid #ccc; padding-top: 8px; }
.detalle-montaje h3 { margin: 0 0 6px; font-size: 14px; }
.detalle-montaje svg.detalle { max-width: 100%; height: auto; }
table.lista { border-collapse: collapse; font-size: 11px; margin: 4px 12px 4px 0; }
table.lista th, table.lista td { border: 1px solid #c8c8c8; padding: 1px 5px; text-align: right; }
table.lista th { background: #eee; }
.listas { display: flex; flex-wrap: wrap; align-items: flex-start; }
.color { display: inline-block; width: 12px; height: 12px; border: 1px solid #000; vertical-align: middle;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.alarma { background: #b00000; color: #fff; font-weight: bold; padding: 8px 12px; margin: 0 0 10px; font-size: 15px;
  -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.error-material td { color: #b00000; font-size: 12px; }
.medida-plancha { font-size: 10px; color: #444; text-align: center; }
@page { size: A4 landscape; margin: 9mm; }
@media print {
  * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  body { background: #fff; }
  .grilla { gap: 3mm 3mm; }
  .grilla svg.miniatura { width: 41mm; height: auto; }
  .hoja { margin: 0; padding: 0; max-width: none; }
  .no-imprimir { display: none !important; }
  .salto { break-before: page; }
  .detalle-montaje { break-inside: avoid; }
  .detalle-montaje h3 { font-size: 11pt; margin-bottom: 2mm; }
  .detalle-montaje svg.detalle { width: auto; height: 118mm; max-width: 100%; display: block; }
  .detalle-montaje table.lista { font-size: 7.5pt; }
  .detalle-montaje .listas { gap: 0 4mm; }
  .grilla svg.miniatura { break-inside: avoid; }
  .barra-negra, .dg-tabla td.val { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  svg { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
}
"""


def html_resultado(res: dict, modo_impresion: str = "detalle", coma: bool = False,
                   titulo: str | None = None) -> str:
    partes = ["<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>",
              f"<title>{escape(titulo or 'Informe de cálculo ' + res['proyecto']['codigo'])}</title>",
              f"<style>{CSS}</style></head><body>"]
    partes.append(seccion_informe(res, coma))
    if modo_impresion in ("miniaturas", "detalle"):
        for i, mat in enumerate(res["materiales"]):
            if mat["montajes"]:
                partes.append(seccion_montajes(res, mat, coma, con_detalle=modo_impresion == "detalle"))
    partes.append("</body></html>")
    return "".join(partes)


def seccion_informe(res: dict, coma: bool = False) -> str:
    n = lambda x, d, s=False: numero(x, d, coma, s)  # noqa: E731
    proy = res["proyecto"]
    p = ["<div class='hoja'>", _alarma(res),
         "<div class='cabecera'>",
         f"<div class='programa'>Optimizador de corte Cristalux v.{escape(__version__)}</div>",
         f"<div class='titulo-informe'><h1>Informe de cálculo</h1>{fecha_corte_certo(res.get('fecha', ''))}</div>",
         "</div>",
         "<div class='subtitulo'>Proyectos calculados</div>",
         "<table class='cc'><tr><th style='width:7%'>Código</th><th style='width:25%'>Descripción</th>"
         "<th style='width:14%'>Piezas</th><th>Código del material</th></tr>"]
    for mat in res["materiales"]:
        p.append(f"<tr><td>{escape(proy['codigo'])}</td><td>{escape(proy['descripcion'])}</td>"
                 f"<td>{mat['piezas']}</td><td>{escape(mat['codigo'])}</td></tr>")
    p.append("</table>")
    p.append("<div class='subtitulo'>Lista de Materiales:</div><table class='cc'>"
             "<tr><th style='width:7%'>Código</th><th style='width:25%'>Descripción</th>"
             "<th style='width:14%'>Piezas</th><th>(m2)</th><th>Layouts</th><th>Planchas</th>"
             "<th>(m2)</th><th>Aprov.</th></tr>")
    for mat in res["materiales"]:
        p.append(f"<tr><td>{escape(mat['codigo'])}</td><td>{escape(mat['descripcion'])}</td>"
                 f"<td>{mat['piezas']}</td><td>{n(mat['m2_piezas'], 6)}</td><td>{mat['layouts']}</td>"
                 f"<td>{mat['planchas']}</td><td>{n(mat['m2_planchas'], 6, True)}</td>"
                 f"<td>{n(mat['aprovechamiento'], 2)}%</td></tr>")
        p.append("<tr class='sub'><td class='etq' colspan='2'>Planchas / offcuts usados:</td>"
                 "<th>Cantidad</th><th>Ancho</th><th>Largo</th><th>Tipo</th><td></td><td></td></tr>")
        for u in mat["planchas_usadas"]:
            tipo = u["tipo"] + (" (supuesta)" if u.get("supuesta") else "")
            p.append(f"<tr><td colspan='2'></td><td>{u['cantidad']}</td><td>{n(u['ancho'], 1)}</td>"
                     f"<td>{n(u['largo'], 1)}</td><td>{escape(tipo)}</td><td></td><td></td></tr>")
        if mat["errores"]:
            p.append(f"<tr class='error-material'><td colspan='8'>⚠ {len(mat['errores'])} renglón(es) de "
                     f"este material no se calcularon (ver avisos)</td></tr>")
        p.append(f"<tr><td colspan='8'>Perímetro - Piezas: {n(mat['perimetro_m'], 2)} m<br>"
                 f"Cálculo especial de perímetro: {n(mat.get('calculo_especial_perimetro_m', 0.0), 2)} m</td></tr>")
    p.append("</table>")
    p.append(_agregados(res, coma))
    p.append("<div class='barra-negra'>Elija el material para visualizar:</div>"
             "<table class='elegir'><tr><th style='width:20%'>Código</th><th>Descripción</th>"
             "<th style='width:12%'>Color</th></tr>")
    for i, mat in enumerate(res["materiales"]):
        enlace = f"#material-{i}" if mat["montajes"] else ""
        p.append(f"<tr><td><a href='{enlace}'>{escape(mat['codigo'])}</a></td>"
                 f"<td><a href='{enlace}'>{escape(mat['descripcion'])}</a></td>"
                 f"<td>{escape(mat['configuracion'].get('color', '') if isinstance(mat.get('configuracion'), dict) else '')}</td></tr>")
    p.append("</table></div>")
    return "".join(p)


def _alarma(res: dict) -> str:
    if res.get("verificado") is False:
        return ("<div class='alarma'>⚠ EL VALIDADOR ENCONTRÓ UN PROBLEMA EN ESTE RESULTADO: NO USARLO PARA "
                "COTIZAR. El detalle está en el recuadro de abajo.</div>")
    return ""


def _agregados(res: dict, coma: bool) -> str:
    n = lambda x, d, s=False: numero(x, d, coma, s)  # noqa: E731
    p = ["<div class='agregados'><h3>Agregados del optimizador (no están en Corte Certo)</h3>"]
    verificado = res.get("verificado")
    if verificado is True:
        p.append("<div class='ok'>Validador independiente: OK (geometría, guillotina, cantidades y "
                 "números revisados)</div>")
    elif verificado is False:
        p.append("<div class='error'>Validador independiente: FALLÓ — este resultado no se puede usar:</div><ul>")
        p += [f"<li class='error'>{escape(e)}</li>" for e in res.get("validacion", [])]
        p.append("</ul>")
    p.append(f"<div>Configuración: <b>{escape(res.get('preset_nombre', ''))}</b> "
             f"(esfuerzo {escape(res.get('esfuerzo', ''))})</div>")
    p.append("<table class='lista'><tr><th>Material</th><th>m² piezas (medida del presupuesto, sin +3)</th>"
             "<th>Mínimo teórico</th><th>m² hoja entera</th>"
             "<th>Peso planchas (kg)</th><th>Sierra</th><th>Destaque</th><th>+ pulido recto</th>"
             "<th>Rotación</th><th>Textura</th><th>Planchas (hoja − banda)</th></tr>")
    for mat in res["materiales"]:
        c = mat["configuracion"]
        planchas = ", ".join(f"{pl['ancho']}×{pl['largo']} − {pl['corte_banda']}"
                             + ("" if pl.get("habilitada", True) else " (deshabilitada)")
                             + (" SUPUESTA" if pl.get("supuesta") else "") for pl in c["planchas"])
        p.append(f"<tr><td>{escape(mat['codigo'])}</td><td>{n(mat.get('m2_piezas_presupuesto', 0), 6)}</td>"
                 f"<td>{mat.get('minimo_teorico_planchas', '-')}</td>"
                 f"<td>{n(mat.get('m2_hoja_entera', 0), 6, True)}</td>"
                 f"<td>{n(mat.get('peso_planchas_kg', 0), 1)}</td>"
                 f"<td>{c['separacion_piezas_mm']} mm</td><td>{c['destaque_min_mm']} mm</td>"
                 f"<td>{c['sobremedida_pulido_mm']} mm</td><td>{'Sí' if c['rotacion'] else 'No'}</td>"
                 f"<td>{escape(c['textura'])}</td><td style='text-align:left'>{escape(planchas)}</td></tr>")
    p.append("</table>")
    mensajes = [(e, "error") for e in res.get("errores", [])] + [(a, "aviso") for a in res.get("avisos", [])]
    for mat in res["materiales"]:
        mensajes += [(f"{mat['codigo']}: {e}" if not e.startswith(mat["codigo"]) else e, "error")
                     for e in mat["errores"]]
        mensajes += [(a, "aviso") for a in mat["avisos"]]
    if mensajes:
        p.append("<div><b>Avisos:</b><ul>")
        p += [f"<li class='{cl}'>{escape(m)}</li>" for m, cl in mensajes]
        p.append("</ul></div>")
    p.append("</div>")
    return "".join(p)


def seccion_montajes(res: dict, mat: dict, coma: bool = False, con_detalle: bool = True) -> str:
    n = lambda x, d: numero(x, d, coma)  # noqa: E731
    i = res["materiales"].index(mat)
    proy = res["proyecto"]
    p = [f"<div class='hoja salto' id='material-{i}'>", _alarma(res),
         f"<div class='encabezado-montajes'>Proyecto : {escape(proy['codigo'])} {escape(proy['descripcion'])}"
         f"&nbsp;&nbsp;&nbsp; {mat['piezas']} &nbsp;&nbsp;&nbsp; Material : ({escape(mat['codigo'])}) "
         f"{escape(mat['descripcion'])}</div>",
         "<div class='datos-generales'><div>Datos generales:</div><table class='dg-tabla'>",
         f"<tr><td class='etq'>Cdad. de montajes:</td><td class='val celeste'>{mat['layouts']}</td></tr>",
         f"<tr><td class='etq'>Total de chapas:</td><td class='val celeste'>{mat['planchas']}</td></tr>",
         f"<tr><td class='etq'>Aprovechamiento:</td><td class='val verde'>{n(mat['aprovechamiento'], 2)} %</td></tr>",
         f"<tr><td class='etq'>Pérdida:</td><td class='val rojo'>{n(mat['perdida'], 2)} %</td></tr>",
         "</table><div class='lamparita'>💡 Hacé clic en un montaje para ver el detalle: medidas, "
         "cortes en orden y lista de piezas. ×N = cantidad de planchas que se cortan así.</div></div>",
         "<div class='grilla'>"]
    referencia = max(m["plancha"]["ancho"] for m in mat["montajes"])
    varias = len({(m["plancha"]["ancho"], m["plancha"]["largo"]) for m in mat["montajes"]}) > 1
    for m in mat["montajes"]:
        titulo = (f"Montaje {m['numero']}: {m['repeticiones']} plancha(s) de {m['plancha']['ancho']} × "
                  f"{m['plancha']['largo']}, aprovechamiento {n(m['aprovechamiento'], 2)} %")
        medida = (f"<div class='medida-plancha'>{m['plancha']['ancho']} × {m['plancha']['largo']}</div>"
                  if varias else "")
        dib = dibujo.miniatura(m, ancho_referencia=referencia)
        if con_detalle:
            p.append(f"<a href='#m-{i}-{m['numero']}' title='{titulo}'>{dib}{medida}</a>")
        else:
            p.append(f"<div title='{titulo}'>{dib}{medida}</div>")
    p.append("</div>")
    p.append(_leyenda_tipos(mat))
    p.append("</div>")
    if con_detalle:
        for m in mat["montajes"]:
            p.append(detalle_montaje(res, mat, m, coma))
    return "".join(p)


def _leyenda_tipos(mat: dict) -> str:
    p = ["<div class='listas'><table class='lista'><tr><th>Color</th><th>Tipo</th><th>Ítems</th>"
         "<th>Medida del presupuesto</th><th>Medida de corte</th><th>Cantidad</th></tr>"]
    for t in mat["tipos"]:
        items = ", ".join(f"{it['item']} ({it['cantidad']})" for it in t["items"])
        p.append(f"<tr><td><span class='color' style='background:{t['color']}'></span></td>"
                 f"<td>{t['tipo']}</td><td style='text-align:left'>{escape(items)}</td>"
                 f"<td>{t.get('ancho_presupuesto', t['ancho'])} × {t.get('largo_presupuesto', t['largo'])}</td>"
                 f"<td>{t['ancho_corte']} × {t['largo_corte']}</td>"
                 f"<td>{t['cantidad']}</td></tr>")
    p.append("</table></div>")
    return "".join(p)


def detalle_montaje(res: dict, mat: dict, m: dict, coma: bool = False) -> str:
    n = lambda x, d: numero(x, d, coma)  # noqa: E731
    i = res["materiales"].index(mat)
    pl = m["plancha"]
    p = [f"<div class='hoja salto detalle-montaje' id='m-{i}-{m['numero']}'>", _alarma(res),
         f"<h3>{escape(mat['codigo'])} — Montaje {m['numero']} — se corta en {m['repeticiones']} "
         f"plancha(s) de {pl['ancho']} × {pl['largo']} — aprovechamiento {n(m['aprovechamiento'], 2)} %</h3>",
         dibujo.detalle(m)]
    # Piezas del montaje agrupadas.
    cuenta: dict[tuple, int] = {}
    for pz in m["piezas"]:
        clave = (pz["tipo"], pz["item"], pz["ancho"], pz["largo"], pz["girada"])
        cuenta[clave] = cuenta.get(clave, 0) + 1
    p.append("<div class='listas'><table class='lista'><tr><th>Color</th><th>Ítem</th><th>Medida en la plancha</th>"
             "<th>Girada</th><th>Por plancha</th><th>Total</th></tr>")
    for (tipo, item, a, b, girada), c in sorted(cuenta.items()):
        p.append(f"<tr><td><span class='color' style='background:{colores.color_pieza(tipo)}'></span></td>"
                 f"<td>{escape(item)}</td><td>{a} × {b}</td><td>{'sí' if girada else ''}</td>"
                 f"<td>{c}</td><td>{c * m['repeticiones']}</td></tr>")
    p.append("</table>")
    if m["sobrantes"]:
        p.append("<table class='lista'><tr><th>Sobrante</th><th>Medida</th><th>X</th><th>Y</th><th>Tipo</th></tr>")
        for k, s in enumerate(sorted(m["sobrantes"], key=lambda s: -s["ancho"] * s["largo"]), start=1):
            p.append(f"<tr><td>{k}</td><td>{s['ancho']} × {s['largo']}</td><td>{s['x']}</td><td>{s['y']}</td>"
                     f"<td>{escape(s['tipo'])}</td></tr>")
        p.append("</table>")
    if m["cortes"]:
        p.append("<table class='lista'><tr><th>Corte</th><th>Nivel</th><th>Línea</th><th>En</th><th>Desde</th>"
                 "<th>Hasta</th></tr>")
        for k, c in enumerate(m["cortes"], start=1):
            linea = "vertical (X)" if c["vertical"] else "horizontal (Y)"
            p.append(f"<tr><td>{k}</td><td>{c['nivel']}</td><td>{linea}</td><td>{c['posicion']}</td>"
                     f"<td>{c['desde']}</td><td>{c['hasta']}</td></tr>")
        p.append("</table>")
    p.append("</div></div>")
    return "".join(p)
