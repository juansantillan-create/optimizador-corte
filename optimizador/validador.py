"""Validador geométrico independiente (brief §6.4).

Revisa un resultado **sin usar nada del motor**: lee la entrada original y el resultado (los
dos son dicts, el JSON de `docs/API.md`) y controla todo de nuevo, con código simple:

- cada plancha útil coincide con su hoja menos corte banda y márgenes;
- toda pieza está adentro de la plancha útil y no se solapa con otra;
- la separación entre piezas se respeta (no se cobra contra los bordes);
- la plancha se puede cortar por guillotina (descomposición recursiva) y ningún sobrante que
  haya que separar mide menos que el destaque mínimo;
- cada pieza está en una orientación permitida (rotación y veta);
- las cantidades son exactas: ni una pieza de más ni de menos por medida;
- los m², las planchas, el aprovechamiento, la pérdida y el perímetro recalculados coinciden con
  los informados.

Devuelve la lista de errores (vacía = todo bien). Si hay errores, el resultado no se muestra como
bueno.
"""

from __future__ import annotations

import re
from collections import defaultdict

TOLERANCIA_M2 = 5e-7  # el informe redondea los m² a 6 decimales
LIMITE_PASOS_GUILLOTINA = 200_000


CAMPOS_MM = ("separacion_piezas_mm", "destaque_min_mm", "constante_ancho_mm", "constante_largo_mm",
             "margen_arriba_mm", "margen_abajo_mm", "margen_izquierda_mm", "margen_derecha_mm",
             "sobremedida_pulido_mm")
# Lo que se compara contra la configuración armada de nuevo desde la entrada.
CAMPOS_COMPARAR = CAMPOS_MM + ("rotacion", "textura")


def validar(entrada: dict, resultado: dict, catalogo=None) -> list[str]:
    """Con `catalogo`, además arma de nuevo la configuración de cada material desde la entrada
    (preset y ajustes) y controla que el resultado diga haber usado esa misma."""
    errores: list[str] = []
    esperado = _piezas_esperadas(entrada, resultado)
    for mat in resultado.get("materiales", []):
        codigo = mat.get("codigo", "?")
        try:
            if mat.get("calculado") is False:
                # No se calculó (configuración imposible, sin planchas): no puede tener montajes.
                if mat.get("montajes") or mat.get("planchas"):
                    errores.append(f"{codigo}: dice que no se calculó pero tiene montajes")
                continue
            errores += _controlar_configuracion(codigo, mat.get("configuracion", {}))
            if catalogo is not None and mat.get("montajes"):
                errores += _comparar_configuracion(codigo, mat.get("configuracion", {}), entrada,
                                                   resultado, catalogo)
            errores += _validar_material(mat, esperado.get(codigo, []))
        except Exception as exc:  # un resultado roto tiene que aparecer como error, no romper
            errores.append(f"{codigo}: no se pudo validar ({type(exc).__name__}: {exc})")
    codigos = {m.get("codigo") for m in resultado.get("materiales", [])}
    for codigo, items in esperado.items():
        if codigo not in codigos and any(it["cantidad"] > 0 for it in items):
            errores.append(f"{codigo}: hay piezas en la entrada pero el material no está en el resultado")
    return errores


# --------------------------------------------------------------- la configuración
def _controlar_configuracion(codigo: str, cfg: dict) -> list[str]:
    """Valores que no tienen sentido: medidas negativas, plancha útil más grande que la hoja o sin
    medida, textura desconocida."""
    errores = []
    for campo in CAMPOS_MM:
        v = cfg.get(campo, 0)
        if not isinstance(v, (int, float)) or v != v or v < 0:
            errores.append(f"{codigo}: {campo} = {v!r} no es una medida válida")
    if cfg.get("textura", "sin") not in ("sin", "horizontal", "vertical"):
        errores.append(f"{codigo}: textura {cfg.get('textura')!r} desconocida")
    for p in cfg.get("planchas", []):
        if not p.get("habilitada", True):
            continue
        w = p["ancho"] - p.get("corte_banda", 0) - cfg.get("margen_izquierda_mm", 0) - cfg.get("margen_derecha_mm", 0)
        h = p["largo"] - cfg.get("margen_arriba_mm", 0) - cfg.get("margen_abajo_mm", 0)
        # Una plancha que queda sin medida útil no se puede usar (si un montaje la usa, falla el
        # control de que las piezas estén adentro); una útil más grande que la hoja es imposible.
        if p.get("corte_banda", 0) < 0 or w > p["ancho"] or h > p["largo"]:
            errores.append(f"{codigo}: la plancha {p['ancho']} × {p['largo']} da una útil de {w} × {h}, "
                           "más grande que la hoja")
    return errores


def _comparar_configuracion(codigo: str, cfg: dict, entrada: dict, resultado: dict, catalogo) -> list[str]:
    """Arma la configuración desde la entrada (sin usar la del resultado) y la compara."""
    preset = entrada.get("preset") or "corte_certo"
    ajustes: dict = {}
    for k, v in (entrada.get("materiales") or {}).items():
        if str(k).strip().upper() == codigo:
            ajustes.update(v or {})
    try:
        mat = catalogo.material(codigo, preset, ajustes)
    except ValueError as exc:
        return [f"{codigo}: la configuración de la entrada no se puede usar ({exc}) y sin embargo hay montajes"]
    errores = []
    for campo in CAMPOS_COMPARAR:
        if getattr(mat, campo) != cfg.get(campo):
            errores.append(f"{codigo}: el resultado dice {campo} = {cfg.get(campo)!r} y la entrada pide "
                           f"{getattr(mat, campo)!r}")
    planchas = [(p.ancho, p.largo, p.corte_banda, p.habilitada) for p in mat.planchas]
    del_resultado = [(p["ancho"], p["largo"], p.get("corte_banda", 0), p.get("habilitada", True))
                     for p in cfg.get("planchas", [])]
    if planchas != del_resultado:
        errores.append(f"{codigo}: las planchas del resultado no son las de la configuración")
    return errores


# ------------------------------------------------------------------- lo que se pidió
def _num(v):
    t = str(v).strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):  # "1.200" = 1200 (punto de miles)
        t = t.replace(".", "")
    elif "," in t and "." in t:  # "1.200,5"
        t = t.replace(".", "").replace(",", ".")
    try:
        x = float(t.replace(",", "."))
    except (TypeError, ValueError):
        return None
    if x != x or x in (float("inf"), float("-inf")):
        return None
    return int(round(x))


def _pulido(d: dict) -> bool:
    if d.get("pulido_recto") is not None:
        valor = d["pulido_recto"]
        if isinstance(valor, str):
            return valor.strip().lower() in ("si", "sí", "s", "true", "1", "x", "verdadero")
        return bool(valor)
    return re.search(r"(^|[^A-Z0-9])PR([^A-Z0-9]|$)", str(d.get("clase") or "").upper()) is not None


def _piezas_esperadas(entrada: dict, resultado: dict) -> dict[str, list[dict]]:
    """Por material: cada renglón válido de la entrada con sus medidas de corte y de m² y las
    orientaciones permitidas, según la configuración que dice el resultado."""
    configs = {m.get("codigo"): m.get("configuracion", {}) for m in resultado.get("materiales", [])}
    salida: dict[str, list[dict]] = defaultdict(list)
    for d in entrada.get("piezas") or []:
        codigo = str(d.get("material") or "").strip().upper()
        cant, ancho, largo = _num(d.get("cantidad")), _num(d.get("ancho")), _num(d.get("largo"))
        if not codigo or cant is None or ancho is None or largo is None:
            continue
        if cant <= 0 or ancho <= 0 or largo <= 0:
            continue
        cfg = configs.get(codigo)
        if cfg is None:
            salida[codigo].append({"cantidad": cant, "orientaciones": set(), "m2": 0})
            continue
        extra = (_num(d.get("sobremedida_mm")) or 0) + (cfg.get("sobremedida_pulido_mm", 0) if _pulido(d) else 0)
        am, lm = ancho + extra, largo + extra
        ac, lc = am + cfg.get("constante_ancho_mm", 0), lm + cfg.get("constante_largo_mm", 0)
        rota = d.get("rota")
        if isinstance(rota, str):
            rota = rota.strip().lower() in ("si", "sí", "s", "true", "1", "x")
        if rota is None:
            rota = cfg.get("rotacion", True)
        textura = cfg.get("textura", "sin")
        if textura == "horizontal":
            orients = {(lc, ac)}
        elif textura == "vertical":
            orients = {(ac, lc)}
        elif rota:
            orients = {(ac, lc), (lc, ac)}
        else:
            orients = {(ac, lc)}
        # ¿Entra en alguna plancha útil habilitada? Si no, se espera que no esté en el resultado.
        utiles = []
        for p in cfg.get("planchas", []):
            if not p.get("habilitada", True):
                continue
            w = p["ancho"] - p.get("corte_banda", 0) - cfg.get("margen_izquierda_mm", 0) - cfg.get("margen_derecha_mm", 0)
            h = p["largo"] - cfg.get("margen_arriba_mm", 0) - cfg.get("margen_abajo_mm", 0)
            utiles.append((w, h))
        s = int(cfg.get("separacion_piezas_mm", 0))
        dmin = int(cfg.get("destaque_min_mm", 0))
        if not any(_cortable_sola(a, b, w, h, s, dmin) for a, b in orients for w, h in utiles):
            continue
        salida[codigo].append({"cantidad": cant, "orientaciones": orients, "m2": am * lm,
                               "perimetro": 2 * (am + lm)})
    return salida


def _cortable_sola(a: int, b: int, w: int, h: int, s: int, dmin: int) -> bool:
    """La pieza a × b sola en la plancha w × h: entra, y lo que sobra a la derecha y arriba mide
    0 o al menos el destaque (en alguno de los dos órdenes de corte)."""
    if a > w or b > h:
        return False
    if dmin <= 0:
        return True
    derecha, arriba = w - a, h - b
    for sobra in (derecha, arriba):
        if 0 < sobra < dmin:
            return False
    if derecha > 0 and arriba > 0 and a + s < dmin and b + s < dmin:
        return False
    return True


# --------------------------------------------------------------------- un material
def _validar_material(mat: dict, esperados: list[dict]) -> list[str]:
    codigo = mat.get("codigo", "?")
    cfg = mat.get("configuracion", {})
    s = int(cfg.get("separacion_piezas_mm", 0))
    d = int(cfg.get("destaque_min_mm", 0))
    errores: list[str] = []
    montajes = mat.get("montajes", [])
    utiles_validas = set()
    for p in cfg.get("planchas", []):
        if p.get("habilitada", True):
            w = p["ancho"] - p.get("corte_banda", 0) - cfg.get("margen_izquierda_mm", 0) - cfg.get("margen_derecha_mm", 0)
            h = p["largo"] - cfg.get("margen_arriba_mm", 0) - cfg.get("margen_abajo_mm", 0)
            utiles_validas.add((w, h, p["ancho"], p["largo"]))
    colocadas: dict[tuple[int, int], int] = defaultdict(int)
    m2_planchas_mm2 = 0
    planchas = 0
    for m in montajes:
        n = m.get("numero", "?")
        donde = f"{codigo} montaje {n}"
        reps = int(m.get("repeticiones", 0))
        if reps <= 0:
            errores.append(f"{donde}: repeticiones {reps}")
            continue
        pl = m["plancha"]
        W, H = int(pl["ancho"]), int(pl["largo"])
        if (W, H, pl.get("hoja_ancho"), pl.get("hoja_largo")) not in utiles_validas:
            errores.append(f"{donde}: la plancha útil {W} × {H} no corresponde a ninguna plancha "
                           "habilitada del material (hoja − banda − márgenes)")
        planchas += reps
        m2_planchas_mm2 += reps * W * H
        rects = []
        for i, pz in enumerate(m.get("piezas", [])):
            x, y, a, b = int(pz["x"]), int(pz["y"]), int(pz["ancho"]), int(pz["largo"])
            if a <= 0 or b <= 0:
                errores.append(f"{donde}: pieza {i + 1} con medida {a} × {b}")
                continue
            if x < 0 or y < 0 or x + a > W or y + b > H:
                errores.append(f"{donde}: la pieza {a} × {b} en ({x}, {y}) se sale de la plancha "
                               f"útil {W} × {H}")
            rects.append((x, y, a, b))
            colocadas[(a, b)] += reps
        # Solapes y separación (rectángulos agrandados en s a la derecha y arriba).
        for i in range(len(rects)):
            xi, yi, ai, bi = rects[i]
            for j in range(i + 1, len(rects)):
                xj, yj, aj, bj = rects[j]
                if xi < xj + aj + s and xj < xi + ai + s and yi < yj + bj + s and yj < yi + bi + s:
                    errores.append(f"{donde}: las piezas en ({xi}, {yi}) y ({xj}, {yj}) se solapan "
                                   f"o quedan a menos de {s} mm")
        # Guillotina y destaque.
        inflados = [(x, y, a + s, b + s) for x, y, a, b in rects]
        ok, motivo = _es_guillotina(inflados, W + s, H + s, d)
        if not ok:
            errores.append(f"{donde}: {motivo}")
    # Cantidades exactas por medida (con las orientaciones permitidas de cada renglón).
    errores += _cantidades(codigo, colocadas, esperados)
    # Números del informe.
    m2_piezas = sum(e["m2"] * e["cantidad"] for e in esperados) / 1e6
    n_piezas = sum(e["cantidad"] for e in esperados)
    perimetro = sum(e.get("perimetro", 0) * e["cantidad"] for e in esperados) / 1000
    m2_planchas = m2_planchas_mm2 / 1e6
    _comparar(errores, codigo, "piezas", mat.get("piezas"), n_piezas, 0)
    _comparar(errores, codigo, "m² de piezas", mat.get("m2_piezas"), m2_piezas, TOLERANCIA_M2)
    _comparar(errores, codigo, "planchas", mat.get("planchas"), planchas, 0)
    _comparar(errores, codigo, "layouts", mat.get("layouts"), len(montajes), 0)
    _comparar(errores, codigo, "m² de planchas", mat.get("m2_planchas"), m2_planchas, TOLERANCIA_M2)
    _comparar(errores, codigo, "perímetro", mat.get("perimetro_m"), round(perimetro, 2), 0.0051)
    if m2_planchas > 0:
        aprov = round(m2_piezas / m2_planchas * 100, 2)
        _comparar(errores, codigo, "aprovechamiento", mat.get("aprovechamiento"), aprov, 0.0051)
        _comparar(errores, codigo, "pérdida", mat.get("perdida"), round(100 - aprov, 2), 0.0051)
    return errores


def _comparar(errores: list[str], codigo: str, que: str, informado, calculado, tol: float) -> None:
    if informado is None or abs(float(informado) - float(calculado)) > tol:
        errores.append(f"{codigo}: {que} informado {informado}, recalculado {calculado}")


def _cantidades(codigo: str, colocadas: dict[tuple[int, int], int], esperados: list[dict]) -> list[str]:
    """¿Se pueden repartir las piezas colocadas entre los renglones pedidos, respetando la
    orientación permitida de cada uno, sin que sobre ni falte ninguna? (flujo máximo)."""
    total_colocadas = sum(colocadas.values())
    total_pedidas = sum(e["cantidad"] for e in esperados)
    errores = []
    if total_colocadas != total_pedidas:
        errores.append(f"{codigo}: se colocaron {total_colocadas} piezas y se pidieron {total_pedidas}")
    medidas = sorted(colocadas)
    # Grafo: fuente -> medida colocada -> renglón -> sumidero.
    nodos = 2 + len(medidas) + len(esperados)
    cap = defaultdict(int)
    ady = defaultdict(set)

    def arista(u, v, c):
        cap[(u, v)] += c
        ady[u].add(v)
        ady[v].add(u)

    F, S = 0, nodos - 1
    for i, med in enumerate(medidas):
        arista(F, 1 + i, colocadas[med])
        for j, e in enumerate(esperados):
            if med in e["orientaciones"]:
                arista(1 + i, 1 + len(medidas) + j, colocadas[med])
    for j, e in enumerate(esperados):
        arista(1 + len(medidas) + j, S, e["cantidad"])
    flujo = 0
    while True:
        previo = {F: None}
        cola = [F]
        while cola and S not in previo:
            u = cola.pop(0)
            for v in sorted(ady[u]):
                if v not in previo and cap[(u, v)] > 0:
                    previo[v] = u
                    cola.append(v)
        if S not in previo:
            break
        camino = []
        v = S
        while previo[v] is not None:
            camino.append((previo[v], v))
            v = previo[v]
        f = min(cap[a] for a in camino)
        for u, v in camino:
            cap[(u, v)] -= f
            cap[(v, u)] += f
        flujo += f
    if flujo != total_colocadas or flujo != total_pedidas:
        sin_lugar = [f"{a}×{b}" for a, b in medidas]
        errores.append(f"{codigo}: las piezas colocadas no coinciden con las pedidas (medida u "
                       f"orientación). Colocadas: {', '.join(sin_lugar) or 'ninguna'}")
    return errores


# ------------------------------------------------------------------------ guillotina
def _es_guillotina(rects: list[tuple[int, int, int, int]], W: int, H: int, d: int) -> tuple[bool, str]:
    """¿Se puede cortar la plancha W × H con cortes de lado a lado, sacando todas las piezas, sin
    que ningún sobrante separado mida menos que el destaque `d` (0 = no se controla)?"""
    pasos = [0]
    memo: dict[tuple[int, int, int, int], bool] = {}

    def adentro(x0, y0, w, h):
        return [r for r in rects if r[0] >= x0 and r[1] >= y0 and r[0] + r[2] <= x0 + w and r[1] + r[3] <= y0 + h]

    def cortar(x0, y0, w, h) -> bool:
        clave = (x0, y0, w, h)
        if clave in memo:
            return memo[clave]
        pasos[0] += 1
        if pasos[0] > LIMITE_PASOS_GUILLOTINA:
            raise _Demasiado()
        piezas = adentro(x0, y0, w, h)
        if not piezas:
            ok = d <= 0 or w >= d and h >= d
            memo[clave] = ok
            return ok
        if len(piezas) == 1 and piezas[0] == (x0, y0, w, h):
            memo[clave] = True
            return True
        candidatos = []
        xs = sorted({r[0] for r in piezas} | {r[0] + r[2] for r in piezas})
        for cx in xs:
            if x0 < cx < x0 + w and not any(r[0] < cx < r[0] + r[2] for r in piezas):
                candidatos.append(("v", cx))
        ys = sorted({r[1] for r in piezas} | {r[1] + r[3] for r in piezas})
        for cy in ys:
            if y0 < cy < y0 + h and not any(r[1] < cy < r[1] + r[3] for r in piezas):
                candidatos.append(("h", cy))
        ok = False
        for eje, c in candidatos:
            if eje == "v":
                partes = ((x0, y0, c - x0, h), (c, y0, x0 + w - c, h))
            else:
                partes = ((x0, y0, w, c - y0), (x0, c, w, y0 + h - c))
            if all(cortar(*p) for p in partes):
                ok = True
                break
            if d <= 0:
                # Sin destaque, si un corte válido no alcanza, ninguno alcanza.
                break
        memo[clave] = ok
        return ok

    try:
        ok = cortar(0, 0, W, H)
    except _Demasiado:
        return False, "no se pudo verificar la guillotina (demasiadas combinaciones)"
    except RecursionError:
        return False, "no se pudo verificar la guillotina (demasiado profundo)"
    if ok:
        return True, ""
    if d > 0:
        return False, (f"no se puede cortar por guillotina sin dejar un sobrante de menos de {d} mm "
                       "(destaque mínimo)")
    return False, "no se puede cortar por guillotina (hay piezas trabadas)"


class _Demasiado(Exception):
    pass
