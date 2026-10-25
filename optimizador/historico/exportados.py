"""Casos de Corte Certo ya exportados por vidrio (`datos/casos/corte_certo/`, 25/10/2026).

A diferencia del zip del contrato (`datos.py`), acá la leyenda ya está leída y las piezas ya están
reconstruidas por vidrio (ver el `LEEME.txt` de la carpeta):

- `resultados_corte_certo.csv`: un renglón por caso (presupuesto + vidrio) con las hojas y el % que
  dio Corte Certo, y si se anotó, la medida de las hojas (`detalle_hojas`) o bandas.
- `piezas.csv`: las piezas de cada caso. `largo`/`ancho` **ya traen el +3 mm** del pulido recto;
  `largo_original`/`ancho_original`, sin.

Qué se hace con cada caso:
1. Se dejan aparte los que no se pueden comparar (sin hojas, con bandas, con el control de área
   del exportador en NO, con varias medidas de hoja anotadas) y se cuentan.
2. **Control de la entrada** (`control`): m² de piezas ÷ (hojas × plancha útil) tiene que dar el %
   de Corte Certo (redondeado o truncado, `comparar.cierra`). Se prueban las medidas de plancha del
   material (o las anotadas en `detalle_hojas`), con banda 20 y con la hoja entera, con el +3 y, si
   no cierra, sin el +3 (pregunta 25). Gana la que da el % redondeando (pregunta 24).
3. Se calcula con H0 (solo el corte banda: Corte Certo se usaba sin separación ni destaque, Juan
   25/10) y esa misma plancha; si con la misma medida cierra también la otra variante (banda 20 ↔
   hoja entera), se calcula también (pregunta 28).
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..configuracion import BANDA_CORTE_CERTO_MM, Catalogo
from . import comparar

ARCHIVO_RESULTADOS = "resultados_corte_certo.csv"


@dataclass
class CasoExportado:
    numero: str
    fecha: str
    material: str
    descripcion: str
    etiqueta: str
    hojas: int | None
    detalle_hojas: list[tuple[int, int, int]]  # (cantidad, ancho, largo) con ancho = lado largo
    bandas: str
    aprovechamiento: float | None
    decimales: int
    m2_piezas: float
    area_ok: str
    criterio: str
    piezas: list[dict] = field(default_factory=list)


def es_carpeta_exportada(carpeta: Path) -> bool:
    return (Path(carpeta) / ARCHIVO_RESULTADOS).exists()


def _numero(texto: str) -> float | None:
    texto = (texto or "").strip().replace(",", ".")
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _decimales(texto: str) -> int:
    x = _numero(texto)
    if x is None or x == int(x):
        return 0
    return len(texto.strip().replace(",", ".").split(".")[1].rstrip("0"))


def _detalle(texto: str) -> list[tuple[int, int, int]]:
    salida = []
    for parte in (texto or "").split(";"):
        m = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*x\s*(\d+)\s*", parte, re.IGNORECASE)
        if m:
            n, a, b = (int(g) for g in m.groups())
            salida.append((n, max(a, b), min(a, b)))
    return salida


def leer(carpeta: Path) -> list[CasoExportado]:
    carpeta = Path(carpeta)
    with (carpeta / ARCHIVO_RESULTADOS).open(encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    casos: dict[tuple[str, str], CasoExportado] = {}
    for r in filas:
        hojas = _numero(r.get("hojas", ""))
        caso = CasoExportado(
            numero=r["numero"].strip(), fecha=r.get("fecha", ""), material=r["v_codart"].strip().upper(),
            descripcion=r.get("descripcion", ""), etiqueta=r.get("etiqueta_leyenda", ""),
            hojas=int(hojas) if hojas is not None else None, detalle_hojas=_detalle(r.get("detalle_hojas", "")),
            bandas=(r.get("bandas") or "").strip(), aprovechamiento=_numero(r.get("aprovechamiento_pct", "")),
            decimales=_decimales(r.get("aprovechamiento_pct", "")), m2_piezas=_numero(r.get("m2_piezas", "")) or 0,
            area_ok=(r.get("area_ok") or "").strip().upper(), criterio=r.get("criterio_emparejamiento", ""))
        casos[(caso.numero, caso.material)] = caso
    with (carpeta / "piezas.csv").open(encoding="utf-8-sig", newline="") as f:
        for p in csv.DictReader(f, delimiter=";"):
            caso = casos.get((p["numero"].strip(), p["v_codart"].strip().upper()))
            if caso is None:
                continue
            caso.piezas.append({
                "cantidad": int(float(p["cantidad"])),
                "ancho": int(float(p["ancho"])), "largo": int(float(p["largo"])),
                "ancho_original": int(float(p.get("ancho_original") or p["ancho"])),
                "largo_original": int(float(p.get("largo_original") or p["largo"])),
                "pulido_recto": (p.get("pulido_recto") or "0").strip() == "1",
                "origen": p.get("origen", ""),
            })
    return sorted(casos.values(), key=lambda c: (len(c.numero), c.numero, c.material))


def _piezas(caso: CasoExportado, con_pulido: bool) -> list[dict]:
    """Las piezas para `optimizar()`: con la medida tal cual (ya con el +3) o la original. Sin
    "clase": el +3 ya está (o no va), así que el programa no suma nada."""
    salida = []
    for n, p in enumerate(caso.piezas, start=1):
        a, l = (p["ancho"], p["largo"]) if con_pulido else (p["ancho_original"], p["largo_original"])
        salida.append({"item": str(n), "material": caso.material, "cantidad": p["cantidad"],
                       "ancho": a, "largo": l, "descripcion": p["origen"]})
    return salida


def _mm2(piezas: list[dict]) -> int:
    return sum(p["ancho"] * p["largo"] * p["cantidad"] for p in piezas)


def _entran(piezas: list[dict], w: int, h: int) -> bool:
    return all((p["ancho"] <= w and p["largo"] <= h) or (p["largo"] <= w and p["ancho"] <= h) for p in piezas)


def _familia(codigo: str) -> str:
    """'EC6CL' -> 'EC', 'LX3+3LOWE' -> 'LX': las letras antes del espesor."""
    m = re.match(r"[A-Z]+", codigo.upper())
    return m.group(0) if m else codigo.upper()


def medidas_conocidas(catalogo: Catalogo, codigo: str = "") -> list[tuple[int, int, int]]:
    """Medidas de hoja de hojas.csv para probar con qué hoja calculó Corte Certo un material que no
    la tiene cargada: (prioridad, ancho, largo). Primero las de los materiales de la misma familia
    (EC…, LX…, CK…), de la más usada a la menos; después las demás, y 3210 × 2550 (la del LOW-E)."""
    familia = _familia(codigo)
    cuenta_familia: dict[tuple[int, int], int] = {}
    cuenta: dict[tuple[int, int], int] = {}
    for mat in catalogo.materiales.values():
        for p in mat.planchas:
            cuenta[(p.ancho, p.largo)] = cuenta.get((p.ancho, p.largo), 0) + 1
            if _familia(mat.codigo) == familia:
                cuenta_familia[(p.ancho, p.largo)] = cuenta_familia.get((p.ancho, p.largo), 0) + 1
    salida = [(1, a, l) for a, l in sorted(cuenta_familia, key=lambda m: (-cuenta_familia[m], m))]
    salida += [(2, a, l) for a, l in sorted(cuenta, key=lambda m: (-cuenta[m], m)) if (a, l) not in cuenta_familia]
    if (3210, 2550) not in cuenta:
        salida.append((2, 3210, 2550))
    return salida


MAX_MEDIDAS_NORMALES = 60  # más que esto por lado y la cuenta de `max_por_plancha` no vale la pena


def _normales(largo: int, a: int, b: int) -> list[int]:
    """Las posiciones de corte que se arman sumando a y b (las únicas que hacen falta probar)."""
    hechas = {0}
    for d in (a, b):
        for x in sorted(hechas):
            y = x + d
            while y < largo:
                hechas.add(y)
                y += d
    return sorted(x for x in hechas if 0 < x < largo)


def max_por_plancha(a: int, b: int, w: int, h: int) -> int | None:
    """Cuántas piezas a × b (se pueden girar) entran como mucho en una plancha w × h con cortes de
    guillotina. None si la cuenta sería muy larga (piezas muy chicas: ahí no hace falta)."""
    xs, ys = _normales(w, a, b), _normales(h, a, b)
    if len(xs) > MAX_MEDIDAS_NORMALES or len(ys) > MAX_MEDIDAS_NORMALES:
        return None
    memo: dict[tuple[int, int], int] = {}

    def g(x: int, y: int) -> int:
        if (x, y) in memo:
            return memo[(x, y)]
        mejor = max([(x // p) * (y // q) for p, q in ((a, b), (b, a)) if p <= x and q <= y], default=0)
        for c in xs:
            if c > x // 2:
                break
            mejor = max(mejor, g(c, y) + g(x - c, y))
        for c in ys:
            if c > y // 2:
                break
            mejor = max(mejor, g(x, c) + g(x, y - c))
        memo[(x, y)] = mejor
        return mejor

    return g(w, h)


def minimo_planchas(piezas: list[dict], w: int, h: int) -> int:
    """Cota rápida de cuántas planchas w × h hacen falta: por área; porque dos piezas de más de la
    mitad de la plancha en los dos sentidos no entran juntas; y porque de cada medida entran como
    mucho tantas por plancha (`max_por_plancha`). Si da más que las hojas de Corte Certo, Corte
    Certo no pudo haber usado esa plancha."""
    area = 0
    grandes = 0
    por_medida = 0
    for p in piezas:
        orientaciones = [o for o in ((p["ancho"], p["largo"]), (p["largo"], p["ancho"])) if o[0] <= w and o[1] <= h]
        if not orientaciones:
            return 10 ** 9
        area += p["ancho"] * p["largo"] * p["cantidad"]
        if all(a * 2 > w and l * 2 > h for a, l in orientaciones):
            grandes += p["cantidad"]
    juntas: dict[tuple[int, int], int] = {}
    for p in piezas:
        clave = (max(p["ancho"], p["largo"]), min(p["ancho"], p["largo"]))
        juntas[clave] = juntas.get(clave, 0) + p["cantidad"]
    cota = max(-(-area // (w * h)), grandes)
    for (a, b), n in sorted(juntas.items()):
        if n <= cota:
            continue  # aunque entre una sola por plancha, no sube la cota
        tope = max_por_plancha(a, b, w, h)
        if tope:
            por_medida = max(por_medida, -(-n // tope))
    return max(cota, por_medida)


VARIANTES = (("banda 20", BANDA_CORTE_CERTO_MM), ("hoja entera", 0))
ANOTADA_UTIL = "medida anotada (ya útil)"


def medidas_de_hoja(catalogo: Catalogo) -> set[tuple[int, int]]:
    """Las medidas de hoja entera que se conocen (hojas.csv y `medidas_conocidas`)."""
    salida = {(p.ancho, p.largo) for mat in catalogo.materiales.values() for p in mat.planchas}
    return salida | {(a, l) for _, a, l in medidas_conocidas(catalogo)}


def _posible(piezas: list[dict], medidas: list[tuple[int, int, int]], hojas: int) -> bool:
    """¿Pueden entrar las piezas en esas hojas (cantidad, ancho útil, largo)?"""
    if any(w <= 0 or h <= 0 for _, w, h in medidas):
        return False
    if len(medidas) == 1:
        return minimo_planchas(piezas, medidas[0][1], medidas[0][2]) <= hojas
    return all(_entran(piezas, w, h) for _, w, h in medidas)


def control(caso: CasoExportado, catalogo: Catalogo) -> dict:
    """¿Con qué plancha calculó Corte Certo? Se prueban:
    - las medidas anotadas en la leyenda (`detalle_hojas`) si las hay; si no, las del material en
      hojas.csv y, si ninguna cierra, otras medidas conocidas (se avisa: falta en hojas.csv);
    - con la banda de 20 mm y con la hoja entera (pregunta 28). Una medida anotada que no es de
      hoja entera (3190, 3280…) ya es la plancha útil: va tal cual;
    - primero con el +3 del pulido recto y, si no cierra, sin (pregunta 25).
    Una plancha en la que las piezas no pueden entrar en las hojas de Corte Certo (por la cota de
    `minimo_planchas`, con las piezas con o sin el +3) se descarta.
    Entre las que cierran gana, en este orden: con el +3; la de hojas.csv (o la anotada) antes que
    una deducida; la que da el % **redondeando** (lo normal según Juan, pregunta 24) antes que la que
    solo da truncando; la más cercana (y si quedan iguales, banda 20).
    Devuelve {"plancha", "planchas" (la lista para `optimizar`; None = la del material en
    hojas.csv), "variante", "con_pulido", "redondea", "supuesta", "medida_nueva", "ambigua",
    "alternativa" (la otra variante con la misma medida, si también cierra), "forzada" (la otra
    variante con la misma medida cuando no cierra), "unica" (la otra variante no cierra con ninguna
    medida igual de confiable), "detalle"};
    "plancha" None si no cierra."""
    mat = catalogo.material(caso.material, "H0", usar_locales=False)
    piezas = {True: _piezas(caso, True), False: _piezas(caso, False)}
    mm2 = {k: _mm2(v) for k, v in piezas.items()}
    hay_pulido = mm2[True] != mm2[False]
    opciones = []
    if caso.detalle_hojas:
        utiles = all((a, l) not in medidas_de_hoja(catalogo) for _, a, l in caso.detalle_hojas)
        for orden_v, (variante, banda) in enumerate(((ANOTADA_UTIL, 0),) if utiles else VARIANTES):
            opciones.append({"prioridad": 0, "orden_v": orden_v, "variante": variante,
                             "clave": "+".join(f"{n}x{a}x{l}" for n, a, l in caso.detalle_hojas),
                             "medidas": [(n, a - banda, l) for n, a, l in caso.detalle_hojas],
                             "planchas": [{"ancho": a, "largo": l, "corte_banda": banda}
                                          for _, a, l in caso.detalle_hojas], "supuesta": False})
    else:
        for orden_v, (variante, banda) in enumerate(VARIANTES):
            propias = set()
            for pl in mat.planchas:
                propias.add((pl.ancho, pl.largo))
                opciones.append({"prioridad": 0, "orden_v": orden_v, "variante": variante, "clave": pl.clave(),
                                 "medidas": [(caso.hojas, pl.ancho - banda, pl.largo)],
                                 "planchas": None if banda == BANDA_CORTE_CERTO_MM and not pl.supuesta else
                                 [{"ancho": pl.ancho, "largo": pl.largo, "corte_banda": banda}],
                                 "supuesta": pl.supuesta})
            for prioridad, a, l in medidas_conocidas(catalogo, caso.material):
                if (a, l) not in propias:
                    opciones.append({"prioridad": prioridad, "orden_v": orden_v, "variante": variante,
                                     "clave": f"{a}x{l}", "medidas": [(caso.hojas, a - banda, l)],
                                     "planchas": [{"ancho": a, "largo": l, "corte_banda": banda}],
                                     "supuesta": False})
    salida = {"plancha": None, "planchas": None, "variante": None, "con_pulido": True, "redondea": False,
              "supuesta": False, "medida_nueva": False, "ambigua": [], "alternativa": None, "unica": False,
              "forzada": None, "detalle": "", "no_entran": True}
    pruebas = []
    for o in opciones:
        util = sum(n * w * h for n, w, h in o["medidas"])
        for con_pulido in ((True, False) if hay_pulido else (True,)):
            if util <= 0 or not _posible(piezas[con_pulido], o["medidas"], caso.hojas):
                continue
            if con_pulido:
                salida["no_entran"] = False
            calc = mm2[con_pulido] / util * 100
            red = comparar.redondea(calc, caso.aprovechamiento, caso.decimales)
            pruebas.append({**o, "con_pulido": con_pulido, "calc": calc, "redondea": red,
                            "orden": (not con_pulido, o["prioridad"], not red,
                                      round(abs(calc - caso.aprovechamiento), 6), o["orden_v"], o["clave"])})
    pruebas.sort(key=lambda x: x["orden"])
    salida["detalle"] = ", ".join(f"{x['clave']} ({x['variante']}){'' if x['con_pulido'] else ' sin +3'}: {x['calc']:.2f} %"
                                  for x in pruebas[:4])
    cierran = [x for x in pruebas if comparar.cierra(x["calc"], caso.aprovechamiento, caso.decimales)]
    if not cierran:
        return salida
    x = cierran[0]
    salida.update({"plancha": x["clave"], "planchas": x["planchas"], "variante": x["variante"],
                   "supuesta": x["supuesta"], "con_pulido": x["con_pulido"], "redondea": x["redondea"],
                   "medida_nueva": x["prioridad"] > 0,
                   "ambigua": sorted({y["clave"] for y in cierran if y["clave"] != x["clave"]
                                      and (y["con_pulido"], y["prioridad"], y["variante"])
                                      == (x["con_pulido"], x["prioridad"], x["variante"])})})
    # La otra variante (banda 20 ↔ hoja entera) con la misma medida de hoja, si también cierra: no se
    # sabe cuál de las dos tenía Corte Certo y se calculan las dos, con las mismas piezas. Se sabe
    # cuál usó ("unica") solo si la otra no cierra con ninguna medida igual de confiable.
    otras = [y for y in cierran if y["variante"] != x["variante"] and y["variante"] != ANOTADA_UTIL
             and y["con_pulido"] == x["con_pulido"] and y["prioridad"] <= x["prioridad"]]
    salida["unica"] = not otras and x["variante"] != ANOTADA_UTIL
    misma = next((y for y in otras if y["clave"] == x["clave"]), None)
    if misma is not None and x["variante"] != ANOTADA_UTIL:
        salida["alternativa"] = {"plancha": misma["clave"], "planchas": misma["planchas"],
                                 "variante": misma["variante"], "redondea": misma["redondea"]}
    elif x["variante"] != ANOTADA_UTIL:
        # La otra variante con la misma medida aunque no cierre (o las piezas no entren): no es lo que
        # usó Corte Certo, pero dice cuánto daría cotizar siempre así (filas "siempre…").
        forzada = next((o for o in opciones if o["clave"] == x["clave"] and o["variante"] != x["variante"]), None)
        if forzada is not None:
            salida["forzada"] = {"plancha": forzada["clave"], "planchas": forzada["planchas"],
                                 "variante": forzada["variante"], "redondea": False}
    return salida


def _clave_problema(piezas: list[dict], plancha: str, variante: str, hojas: int, aprov: float) -> tuple:
    """Lo que define el problema de corte: dos casos con lo mismo son el mismo cálculo."""
    return (tuple(sorted((p["cantidad"], p["ancho"], p["largo"]) for p in piezas)), plancha, variante, hojas, aprov)


def preparar(casos: list[CasoExportado], catalogo: Catalogo) -> tuple[list[dict], dict]:
    """Los casos que se pueden comparar ("trabajos" para `comparar.correr`) y la cobertura."""
    cob = {"casos": len(casos), "sin_hojas": [], "con_bandas": [], "area_no": [], "sin_piezas": [],
           "varias_medidas": [], "no_cierran": [], "duplicados": [], "control_ok": 0, "sin_mas3": 0,
           "plancha_supuesta": 0, "plancha_ambigua": 0, "con_detalle": 0, "con_avisos": 0, "medida_nueva": {},
           "variantes": {}, "solo_truncando": 0, "con_alternativa": 0, "forzadas": 0}
    trabajos = []
    vistos: dict[tuple, dict] = {}
    for caso in casos:
        ref = {"numero": caso.numero, "material": caso.material}
        if not caso.piezas:
            cob["sin_piezas"].append(ref)
            continue
        if not caso.hojas or caso.aprovechamiento is None:
            cob["sin_hojas"].append(ref)  # solo bandas o solo el %: no hay cantidad de hojas para comparar
            continue
        if caso.bandas:
            cob["con_bandas"].append(ref)  # Corte Certo usó además recortes: no se puede repetir igual
            continue
        if caso.area_ok == "NO":
            cob["area_no"].append(ref)  # el exportador ya vio que la leyenda o el vidrio no cierran
            continue
        if len(caso.detalle_hojas) > 1:
            # Varias medidas de hoja: el programa no puede limitar cuántas usa de cada una, así que
            # contar hojas no sería justo.
            cob["varias_medidas"].append(ref)
            continue
        if caso.aprovechamiento > 100:
            cob["no_cierran"].append({**ref, "motivo": "imposible", "leyenda": f"{caso.hojas} hojas {caso.aprovechamiento:g}%",
                                      "probado": "más de 100 %", "avisos": []})
            continue
        c = control(caso, catalogo)
        if c["plancha"] is None:
            cob["no_cierran"].append({**ref, "motivo": "no_entran" if c["no_entran"] else "no_cierra",
                                      "leyenda": f"{caso.hojas} hojas {caso.aprovechamiento:g}%",
                                      "probado": c["detalle"], "avisos": []})
            continue
        piezas = _piezas(caso, c["con_pulido"])
        clave = _clave_problema(piezas, c["plancha"], c["variante"], caso.hojas, caso.aprovechamiento)
        if clave in vistos:
            # Las mismas piezas, la misma plancha y lo mismo de Corte Certo que otro caso (el mismo
            # pedido cotizado en otro vidrio): se compara una sola vez.
            cob["duplicados"].append({**ref, "igual_a": f"{vistos[clave]['numero']} {vistos[clave]['material']}"})
            continue
        vistos[clave] = ref
        cob["control_ok"] += 1
        cob["variantes"][c["variante"]] = cob["variantes"].get(c["variante"], 0) + 1
        avisos = []
        if c["variante"] == "hoja entera":
            avisos.append("se usó la hoja entera (sin corte banda): es con la que cierra el % de Corte Certo")
        elif c["variante"] == ANOTADA_UTIL:
            avisos.append("la medida anotada en la leyenda ya es la plancha útil: se usó tal cual")
        if not c["redondea"]:
            avisos.append("el % de Corte Certo cierra solo truncando, no redondeando")
            cob["solo_truncando"] += 1
        if not c["con_pulido"]:
            avisos.append("la leyenda cierra solo SIN el +3 mm del pulido recto: se calcula sin el +3")
            cob["sin_mas3"] += 1
        if c["supuesta"]:
            avisos.append(f"{caso.material} no está en hojas.csv: se usó una plancha supuesta")
            cob["plancha_supuesta"] += 1
        if c["medida_nueva"]:
            avisos.append(f"cierra con {c['plancha']}, que no está en hojas.csv para {caso.material}")
            cob["medida_nueva"].setdefault(caso.material, {}).setdefault(c["plancha"], 0)
            cob["medida_nueva"][caso.material][c["plancha"]] += 1
        if c["ambigua"]:
            avisos.append(f"también cierra con {', '.join(c['ambigua'])}; se usó {c['plancha']}, la más cercana")
            cob["plancha_ambigua"] += 1
        origen_plancha = "leyenda" if caso.detalle_hojas else ("deducida" if c["medida_nueva"] else "hojas.csv")
        if caso.detalle_hojas:
            cob["con_detalle"] += 1
        if avisos:
            cob["con_avisos"] += 1
        if c["alternativa"]:
            cob["con_alternativa"] += 1
        t = {"numero": caso.numero, "material": caso.material, "abreviado": caso.etiqueta,
             "relacion": caso.criterio, "cc_hojas": caso.hojas, "cc_aprov": caso.aprovechamiento,
             "plancha": c["plancha"], "planchas": c["planchas"], "con_pulido": c["con_pulido"],
             "plancha_supuesta": c["supuesta"], "avisos": avisos, "piezas": piezas,
             "n_piezas": sum(p["cantidad"] for p in piezas), "grupo": comparar._grupo(caso.material, catalogo),
             "calibracion": comparar.es_calibracion(caso.numero),
             "extra": {"fecha": caso.fecha, "tipos": len(piezas), "plancha_origen": origen_plancha,
                       "variante": c["variante"], "redondea": c["redondea"], "alternativa": False,
                       "tiene_alternativa": bool(c["alternativa"]), "unica": c["unica"]}}
        t["firma"] = comparar._firma(t)
        trabajos.append(t)
        a = c["alternativa"] or c["forzada"]
        if a:
            # La otra variante (banda 20 ↔ hoja entera), con las mismas piezas: si también cierra, es
            # otra lectura posible de Corte Certo; si no, solo dice cuánto daría cotizar siempre así.
            forzada = c["alternativa"] is None
            if forzada:
                cob["forzadas"] += 1
            aviso = (f"variante: {a['variante']} con {a['plancha']} "
                     + ("(no cierra con el % de Corte Certo: solo para ver cómo cotizaría)" if forzada else "(también cierra)"))
            alt = {**t, "plancha": a["plancha"], "planchas": a["planchas"], "avisos": [aviso],
                   "extra": {**t["extra"], "variante": a["variante"], "redondea": a["redondea"], "alternativa": True,
                             "forzada": forzada}}
            alt["firma"] = comparar._firma(alt)
            trabajos.append(alt)
    return trabajos, cob


VISTAS = {"probable": "La plancha con la que mejor cierra el % de cada caso: **la cuenta principal**",
          "banda": "Cotizando siempre con banda 20 (3580)",
          "entera": "Cotizando siempre con la hoja entera (3600)",
          "seguros": "Solo los casos donde la otra no cierra con ninguna medida igual de confiable"}

MARGEN_EVIDENCIA = comparar.MARGEN_CORTE_CERTO
ANCHOS_EVIDENCIA = (("3600 (hoja entera)", 3600), ("3580 (banda 20)", 3580), ("3570 (banda 30)", 3570),
                    ("3550 (banda 50)", 3550))


def _periodo(fecha: str) -> str:
    """Trimestres hasta junio de 2026; después, meses (ahí cambia, pregunta 28)."""
    anio, mes = fecha[:4], int(fecha[5:7] or 1)
    if fecha[:7] < "2026-07":
        return f"{anio} T{(mes - 1) // 3 + 1}"
    return fecha[:7]


def evidencia_banda(casos: list[CasoExportado], catalogo: Catalogo) -> list[dict]:
    """¿Corte Certo cortaba sobre 3600 o sobre 3580? Por período, en los casos más limpios (% entero,
    vidrio con hoja de 3600 × 2500 en hojas.csv, sin medidas anotadas ni bandas, y que cierran con
    3600 o 3580): cuántos dan el % **redondeando** con cada ancho y la diferencia media
    (leyenda − calculado). Si la oficina redondeaba, el ancho bueno da diferencia media cerca de 0."""
    por: dict[str, list[dict[str, float]]] = {}
    for c in casos:
        if not c.hojas or c.bandas or c.area_ok == "NO" or c.detalle_hojas or c.decimales or c.aprovechamiento is None:
            continue
        mat = catalogo.material(c.material, "H0", usar_locales=False)
        if not any((p.ancho, p.largo) == (3600, 2500) for p in mat.planchas):
            continue
        mm2 = _mm2(_piezas(c, True))
        dif = {nombre: c.aprovechamiento - mm2 / (c.hojas * w * 2500) * 100 for nombre, w in ANCHOS_EVIDENCIA}
        if min(abs(dif[ANCHOS_EVIDENCIA[0][0]]), abs(dif[ANCHOS_EVIDENCIA[1][0]])) > 1.0:
            continue  # no cierra con ninguna de las dos: es otro problema (otra plancha, otro pedido)
        por.setdefault(_periodo(c.fecha), []).append(dif)
    salida = []
    for periodo in sorted(por):
        fs = por[periodo]
        fila = {"periodo": periodo, "casos": len(fs)}
        for nombre, _ in ANCHOS_EVIDENCIA:
            fila[nombre] = {"redondea_%": round(sum(comparar.redondea(-f[nombre], 0) for f in fs) / len(fs) * 100),
                            "dif_media": round(sum(f[nombre] for f in fs) / len(fs), 2)}
        # Las dos lecturas posibles dan casi la misma diferencia media; lo que las separa es qué casos
        # las contradicen: "3600 redondeando" no admite diferencias de más de 0,5 para ningún lado;
        # "3580 truncando" no admite que la leyenda sea más que lo calculado (ni 1 o más por debajo).
        a, b = ANCHOS_EVIDENCIA[0][0], ANCHOS_EVIDENCIA[1][0]
        fila["contra_3600_redondeando"] = sum(not comparar.redondea(-f[a], 0) for f in fs)
        fila["contra_3580_truncando"] = sum(f[b] > MARGEN_EVIDENCIA or f[b] <= -1 - MARGEN_EVIDENCIA for f in fs)
        salida.append(fila)
    return salida


def _fila_vista(nombre: str, r: dict) -> str:
    no_entran = f" (con {r['no_entran']} donde las piezas no entran)" if r.get("no_entran") else ""
    return (f"| {nombre} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | {r['peores_%']} %{no_entran} | "
            f"{r['diferencia_media']:+} | {r['peor_diferencia']:+} |")


def markdown(cob: dict, prueba: dict, opciones: comparar.Opciones, origen: str, por_origen: dict | None = None,
             vistas: dict | None = None, evidencia: list[dict] | None = None, repaso: dict | None = None) -> str:
    lineas = [f"Datos: `{origen}` (exportados de Metrix el 25/10/2026). Esfuerzo: {opciones.esfuerzo}. "
              + ("Todos los casos." if opciones.muestra is None else f"Muestra de {opciones.muestra} casos.")
              + " Configuración: H0 (solo el corte banda, sin separación ni destaque: así se usaba Corte "
              "Certo), con la misma medida de plancha que dio el control.", "",
              "**Qué casos se pudieron comparar**", "", "| | Casos |", "|---|---|",
              f"| Casos exportados (presupuesto + vidrio) | {cob['casos']} |",
              f"| Sin cantidad de hojas (solo bandas o solo el %) | {len(cob['sin_hojas'])} |",
              f"| Corte Certo usó además bandas o recortes (no se puede repetir igual) | {len(cob['con_bandas'])} |",
              f"| El área de la hoja que se deduce no cierra (leyenda o vidrio mal anotado) | {len(cob['area_no'])} |",
              f"| Varias medidas de hoja anotadas (el programa no limita cuántas usa de cada una) | "
              f"{len(cob['varias_medidas'])} |",
              f"| Sin piezas | {len(cob['sin_piezas'])} |"]
    motivos: dict[str, int] = {}
    for x in cob["no_cierran"]:
        motivos[x["motivo"]] = motivos.get(x["motivo"], 0) + 1
    for motivo, n in sorted(motivos.items()):
        lineas.append(f"| No cierran: {comparar.MOTIVOS_NO_CIERRAN.get(motivo, motivo)} | {n} |")
    variantes = cob.get("variantes", {})
    lineas += [f"| Iguales a otro caso (mismas piezas, plancha y resultado de Corte Certo; a veces el mismo pedido "
               f"en otro vidrio, a veces otro presupuesto): se cuentan una vez | "
               f"{len(cob['duplicados'])} |",
               f"| **Pasaron el control y se compararon** | **{cob['control_ok']}** |",
               f"| … calculados con la hoja entera / con banda 20 / con la medida útil anotada | "
               f"{variantes.get('hoja entera', 0)} / {variantes.get('banda 20', 0)} / {variantes.get(ANOTADA_UTIL, 0)} |",
               f"| … donde también cierra la otra (banda 20 ↔ hoja entera): se calcularon las dos | {cob['con_alternativa']} |",
               f"| … donde la otra no cierra: se calculó igual, solo para \"cotizando siempre con…\" | {cob['forzadas']} |",
               f"| … donde el % cierra solo truncando, no redondeando | {cob['solo_truncando']} |",
               f"| … que cierran solo SIN el +3 mm del pulido (se calcularon sin el +3) | {cob['sin_mas3']} |",
               f"| … con las medidas de hoja anotadas en la leyenda | {cob['con_detalle']} |",
               f"| … con plancha supuesta (el material no está en hojas.csv) | {cob['plancha_supuesta']} |",
               f"| … con una medida de hoja que hojas.csv no tiene para ese material (ver abajo) | "
               f"{sum(sum(v.values()) for v in cob['medida_nueva'].values())} |",
               f"| … con más de una medida de plancha que cierra (se usó la más cercana) | {cob['plancha_ambigua']} |", ""]
    if cob["medida_nueva"]:
        lineas += ["**Medidas de hoja que Corte Certo usó y no están en `hojas.csv`** (habría que sumarlas a "
                   "`Medidas_hojas.xlsx`; pregunta 29)", "", "| Material | Medida (casos) |", "|---|---|"]
        for mat, medidas in sorted(cob["medida_nueva"].items(), key=lambda x: -sum(x[1].values())):
            lineas.append(f"| {mat} | " + ", ".join(f"{m} ({n})" for m, n in sorted(medidas.items(), key=lambda x: -x[1])) + " |")
        lineas.append("")
    if evidencia:
        nombres = [n for n, _ in ANCHOS_EVIDENCIA]
        lineas += ["**¿Corte Certo cortaba sobre 3600 o sobre 3580?** (pregunta 28). Casos con % entero y hoja de "
                   "3600 × 2500 en hojas.csv que cierran con alguna de las dos. Para cada ancho: cuántos dan el % "
                   "**redondeando** y, entre paréntesis, la diferencia media leyenda − calculado. Hay dos lecturas "
                   "que dan casi lo mismo en promedio: \"3600 y la oficina redondeaba\" y \"3580 y la oficina "
                   "truncaba\". Lo que las separa son las dos últimas columnas: cuántos casos contradicen cada una "
                   "(con 3600, una diferencia de más de 0,5; con 3580, una leyenda más alta que lo calculado).", "",
                   "| Período | Casos | " + " | ".join(nombres) + " | Contradicen 3600 redondeando | "
                   "Contradicen 3580 truncando |",
                   "|---|---|" + "---|" * len(nombres) + "---|---|"]
        for f in evidencia:
            celdas = " | ".join(f"{f[n]['redondea_%']} % ({f[n]['dif_media']:+.2f})" for n in nombres)
            lineas.append(f"| {f['periodo']} | {f['casos']} | {celdas} | {f['contra_3600_redondeando']} | "
                          f"{f['contra_3580_truncando']} |")
        tot = {k: sum(f[k] for f in evidencia) for k in ("casos", "contra_3600_redondeando", "contra_3580_truncando")}
        lineas += [f"| **Total** | {tot['casos']} | " + " | ".join("" for _ in nombres) + f" | "
                   f"{tot['contra_3600_redondeando']} | {tot['contra_3580_truncando']} |", ""]
    if vistas:
        lineas += ["**Según qué plancha**: la cuenta principal usa, en cada caso, la plancha con la que mejor cierra "
                   "el % de Corte Certo (redondeando primero, y la más cercana). Las filas \"cotizando siempre "
                   "con…\" calculan todos los casos con esa plancha, cierre o no con el %: dicen cuánto se "
                   "parecería el programa a Corte Certo si cotizara siempre así. Si las piezas no entran, cuenta "
                   "como más hojas (no se puede cotizar). La diferencia media y la peor son de los que sí se "
                   "calcularon.", "",
                   "| Plancha | Casos | Iguales | Menos planchas | Más planchas | Dif. media | Peor |",
                   "|---|---|---|---|---|---|---|"]
        lineas += [_fila_vista(nombre, vistas[clave]) for clave, nombre in VISTAS.items()
                   if (vistas.get(clave) or {}).get("casos")]
        lineas.append("")
    if repaso and repaso.get("casos"):
        lineas += [f"**Con esfuerzo máximo** en los {repaso['casos']} casos donde el normal da más hojas que Corte "
                   f"Certo (más {repaso['alternativas']} variantes de plancha): mejoran {repaso['mejoran']} casos "
                   f"(y {repaso['mejoran_alternativas']} variantes); el más lento tardó {repaso['segundos_max']:g} s. "
                   "Así quedan:", "",
                   "| Plancha | Casos | Iguales | Menos planchas | Más planchas | Dif. media | Peor |",
                   "|---|---|---|---|---|---|---|"]
        lineas += [_fila_vista(nombre, repaso["vistas"][clave]) for clave, nombre in VISTAS.items()
                   if (repaso["vistas"].get(clave) or {}).get("casos")]
        lineas.append("")
    if por_origen:
        nombres = {"hojas.csv": "la medida de hoja del material en hojas.csv",
                   "leyenda": "las medidas de hoja anotadas en la leyenda",
                   "deducida": "una medida deducida (hojas.csv no la tiene para ese material)"}
        lineas += ["**Según de dónde salió la medida de hoja** (cuenta principal)", "",
                   "| Medida de hoja | Casos | Iguales | Menos planchas | Más planchas | Dif. media |",
                   "|---|---|---|---|---|---|"]
        for clave, r in por_origen.items():
            if r.get("casos"):
                lineas.append(f"| {nombres[clave]} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | "
                              f"{r['peores_%']} % | {r['diferencia_media']:+} |")
        lineas.append("")
    lineas += comparar.resultados_md({}, prueba, titulo="Resultado de la cuenta principal (todos los casos comparados)",
                                     con_eleccion=False)
    return "\n".join(lineas)
