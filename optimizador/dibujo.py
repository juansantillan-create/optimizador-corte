"""Dibujos de los montajes en SVG (nítidos al imprimir y livianos).

- `miniatura`: como en "Visualizar e imprimir montajes" de Corte Certo (captura 2): la plancha
  acostada con contorno negro, las piezas en color, el sobrante en amarillo y, si el montaje se
  repite, **apilada** como una pila de chapas (contornos corridos hacia abajo y a la derecha), con
  "×N" a la vista.
- `detalle`: grande, con la medida y el ítem de cada pieza, las medidas de los sobrantes y los
  cortes numerados en orden (primero los de lado a lado de la plancha).

Coordenadas: el resultado tiene el origen abajo a la izquierda (Y hacia arriba); en el SVG se
invierte Y. Los colores están en `colores.py`.
"""

from __future__ import annotations

from html import escape

from . import colores


def _f(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def miniatura(montaje: dict, ancho_px: float = 158, max_pila: int = 12, numero: bool = True,
              ancho_referencia: int | None = None) -> str:
    """`ancho_referencia`: el ancho de la plancha más grande del material, para que las miniaturas
    de planchas distintas se vean en la misma escala (y se note cuál es más chica)."""
    pl = montaje["plancha"]
    W, H = pl["ancho"], pl["largo"]
    k = ancho_px / (ancho_referencia or W)
    ancho_px = W * k
    alto_px = H * k
    reps = montaje.get("repeticiones", 1)
    capas = min(max(reps - 1, 0), max_pila)
    paso = 2.5
    margen = 1
    total_w = ancho_px + capas * paso + 2 * margen
    total_h = alto_px + capas * paso + 2 * margen + (14 if numero else 0)
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" class="miniatura" '
              f'width="{_f(total_w)}" height="{_f(total_h)}" viewBox="0 0 {_f(total_w)} {_f(total_h)}">']
    y0 = margen + (14 if numero else 0)
    if numero:
        partes.append(f'<text x="{margen}" y="11" font-size="11" font-family="Arial, sans-serif">'
                      f'Montaje {montaje.get("numero", "")}</text>')
        if reps > 1:
            partes.append(f'<text x="{_f(total_w - margen)}" y="11" font-size="11" font-weight="bold" '
                          f'text-anchor="end" font-family="Arial, sans-serif">×{reps}</text>')
    # La pila: contornos corridos hacia abajo y a la derecha, del fondo hacia adelante.
    for i in range(capas, 0, -1):
        partes.append(f'<rect x="{_f(margen + i * paso)}" y="{_f(y0 + i * paso)}" width="{_f(ancho_px)}" '
                      f'height="{_f(alto_px)}" fill="#ffffff" stroke="#000" stroke-width="0.6"/>')
    partes.append(_plancha(montaje, margen, y0, k, trazo=0.5))
    partes.append("</svg>")
    return "".join(partes)


def _plancha(montaje: dict, x0: float, y0: float, k: float, trazo: float) -> str:
    pl = montaje["plancha"]
    W, H = pl["ancho"], pl["largo"]
    partes = [f'<rect x="{_f(x0)}" y="{_f(y0)}" width="{_f(W * k)}" height="{_f(H * k)}" '
              f'fill="{colores.SOBRANTE}" stroke="{colores.CONTORNO}" stroke-width="{trazo * 2}"/>']
    for p in montaje["piezas"]:
        x = x0 + p["x"] * k
        y = y0 + (H - p["y"] - p["largo"]) * k
        partes.append(f'<rect x="{_f(x)}" y="{_f(y)}" width="{_f(p["ancho"] * k)}" '
                      f'height="{_f(p["largo"] * k)}" fill="{colores.color_pieza(p["tipo"])}" '
                      f'stroke="{colores.CONTORNO}" stroke-width="{trazo}"/>')
    return "".join(partes)


def detalle(montaje: dict, ancho_px: float = 1000, cortes: bool = True) -> str:
    """El montaje grande: medidas, ítems, sobrantes y cortes numerados."""
    pl = montaje["plancha"]
    W, H = pl["ancho"], pl["largo"]
    margen_izq, margen_sup = 46, 30
    k = ancho_px / W
    total_w = ancho_px + margen_izq + 10
    total_h = H * k + margen_sup + 40
    x0, y0 = margen_izq, margen_sup
    fuente = "Arial, sans-serif"
    partes = [f'<svg xmlns="http://www.w3.org/2000/svg" class="detalle" width="{_f(total_w)}" '
              f'height="{_f(total_h)}" viewBox="0 0 {_f(total_w)} {_f(total_h)}" font-family="{fuente}">']
    partes.append(_plancha(montaje, x0, y0, k, trazo=0.8))
    # Cotas de la plancha útil.
    partes.append(f'<text x="{_f(x0 + W * k / 2)}" y="{_f(y0 - 10)}" font-size="13" text-anchor="middle">'
                  f'{W} mm</text>')
    partes.append(f'<text x="{_f(x0 - 10)}" y="{_f(y0 + H * k / 2)}" font-size="13" text-anchor="middle" '
                  f'transform="rotate(-90 {_f(x0 - 10)} {_f(y0 + H * k / 2)})">{H} mm</text>')
    # Rótulos de piezas y sobrantes.
    for p in montaje["piezas"]:
        partes.append(_rotulo(x0 + p["x"] * k, y0 + (H - p["y"] - p["largo"]) * k, p["ancho"] * k,
                              p["largo"] * k, f'{p["ancho"]} × {p["largo"]}', f'ítem {p["item"]}' +
                              (" ↻" if p.get("girada") else ""), "#ffffff"))
    for s in montaje.get("sobrantes", []):
        if s["ancho"] * k < 30 or s["largo"] * k < 14:
            continue
        partes.append(_rotulo(x0 + s["x"] * k, y0 + (H - s["y"] - s["largo"]) * k, s["ancho"] * k,
                              s["largo"] * k, f'{s["ancho"]} × {s["largo"]}',
                              "retazo" if s.get("tipo") == "retazo" else "", "#000000"))
    if cortes:
        rotulos = []
        ocupados: list[tuple[float, float]] = []
        for n, c in enumerate(montaje.get("cortes", []), start=1):
            if c["vertical"]:
                x1 = x2 = x0 + c["posicion"] * k
                ya, yb = y0 + (H - c["desde"]) * k, y0 + (H - c["hasta"]) * k
                lugares = [(x1, min(ya, yb) + f * abs(yb - ya)) for f in (0.08, 0.5, 0.3, 0.7, 0.92)]
            else:
                ya = yb = y0 + (H - c["posicion"]) * k
                x1, x2 = x0 + c["desde"] * k, x0 + c["hasta"] * k
                lugares = [(min(x1, x2) + f * abs(x2 - x1), ya) for f in (0.92, 0.5, 0.7, 0.3, 0.08)]
            # El número va donde no se pise con otro.
            cx, cy = next(((x, y) for x, y in lugares if all(abs(x - ox) > 20 or abs(y - oy) > 20
                                                             for ox, oy in ocupados)), lugares[0])
            ocupados.append((cx, cy))
            color = "#d00000" if c["nivel"] == 1 else "#0050d0"
            ancho_linea = 2 if c["nivel"] == 1 else 1.4
            # Primero un borde blanco, así la línea se ve sobre cualquier color.
            partes.append(f'<line x1="{_f(x1)}" y1="{_f(ya)}" x2="{_f(x2)}" y2="{_f(yb)}" stroke="#ffffff" '
                          f'stroke-width="{ancho_linea + 2.4}"/>')
            partes.append(f'<line class="corte" x1="{_f(x1)}" y1="{_f(ya)}" x2="{_f(x2)}" y2="{_f(yb)}" '
                          f'stroke="{color}" stroke-width="{ancho_linea}" stroke-dasharray="7 3"/>')
            rotulos.append(f'<circle cx="{_f(cx)}" cy="{_f(cy)}" r="9" fill="#ffffff" stroke="{color}" stroke-width="1.5"/>'
                           f'<text x="{_f(cx)}" y="{_f(cy + 4)}" font-size="11" font-weight="bold" '
                           f'text-anchor="middle" fill="{color}">{n}</text>')
        partes += rotulos
    partes.append(f'<text x="{x0}" y="{_f(y0 + H * k + 20)}" font-size="12">'
                  f'Plancha útil {W} × {H} (hoja {pl["hoja_ancho"]} × {pl["hoja_largo"]}). '
                  f'Cortes: rojo = de lado a lado de la plancha, azul = adentro de una tira. '
                  f'↻ = pieza girada.</text>')
    partes.append("</svg>")
    return "".join(partes)


def _rotulo(x: float, y: float, w: float, h: float, linea1: str, linea2: str, color: str) -> str:
    tam = max(6.0, min(14.0, h / 3.2, w / (0.62 * max(len(linea1), 1))))
    cx, cy = x + w / 2, y + h / 2
    if h < tam * 1.2 or w < tam * 2:
        return ""
    texto = (f'<text x="{_f(cx)}" y="{_f(cy - (tam * 0.15 if linea2 else -tam * 0.35))}" '
             f'font-size="{_f(tam)}" text-anchor="middle" fill="{color}">{escape(linea1)}</text>')
    if linea2 and h > tam * 2.6:
        texto += (f'<text x="{_f(cx)}" y="{_f(cy + tam * 1.05)}" font-size="{_f(tam * 0.8)}" '
                  f'text-anchor="middle" fill="{color}">{escape(linea2)}</text>')
    return texto
