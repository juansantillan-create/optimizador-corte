"""Casos de Corte Certo ya exportados por vidrio (`datos/casos/corte_certo/`, 25/10/2026).

A diferencia del zip del contrato (`datos.py`), acá la leyenda ya está leída y las piezas ya están
reconstruidas por vidrio (ver el `LEEME.txt` de la carpeta):

- `resultados_corte_certo.csv`: un renglón por caso (presupuesto + vidrio) con las hojas y el % que
  dio Corte Certo, y si se anotó, la medida de las hojas (`detalle_hojas`) o bandas.
- `piezas.csv`: las piezas de cada caso. `largo`/`ancho` **ya traen el +3 mm** del pulido recto;
  `largo_original`/`ancho_original`, sin.

Qué se hace con cada caso:
1. Se dejan aparte los que no se pueden comparar (sin hojas, con bandas, con el control de área
   del exportador en NO) y se cuentan.
2. **Control de la entrada**: m² de piezas ÷ (hojas × plancha útil) tiene que dar el % de Corte
   Certo (redondeado o truncado, `comparar.cierra`). Se prueban las medidas de plancha del
   material (o las anotadas en `detalle_hojas`), con el +3 y, si no cierra, sin el +3
   (pregunta 25). Así se sabe con qué hoja se calculó.
3. Se calcula con H0 (solo el corte banda: Corte Certo se usaba sin separación ni destaque, Juan
   25/10) y esa misma plancha.
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


def control(caso: CasoExportado, catalogo: Catalogo) -> dict:
    """¿Con qué plancha cierra el % de Corte Certo? Se prueban:
    - las medidas anotadas en la leyenda (`detalle_hojas`) si las hay; si no, las del material en
      hojas.csv y, si ninguna cierra, otras medidas conocidas (se avisa: falta en hojas.csv);
    - con la banda de Corte Certo (20 mm) y con la hoja entera: los casos muestran las dos cosas
      (pregunta 28), y el % casi nunca alcanza para distinguirlas;
    - primero con el +3 del pulido recto y, si no cierra, sin (pregunta 25).
    Una plancha en la que las piezas no pueden entrar en las hojas de Corte Certo (por la cota de
    `minimo_planchas`) se descarta.
    Devuelve {"plancha", "planchas" (la lista para `optimizar`; None = la del material en
    hojas.csv), "variante", "con_pulido", "supuesta", "medida_nueva", "ambigua", "alternativa"
    (la hoja entera, si también es posible), "detalle"}; "plancha" None si no cierra."""
    mat = catalogo.material(caso.material, "H0", usar_locales=False)
    con, sin = _piezas(caso, True), _piezas(caso, False)
    mm2 = {True: _mm2(con), False: _mm2(sin)}
    hay_pulido = mm2[True] != mm2[False]
    opciones = []
    for orden_v, (variante, banda) in enumerate(VARIANTES):
        if caso.detalle_hojas:
            planchas = [{"ancho": a, "largo": l, "corte_banda": banda} for _, a, l in caso.detalle_hojas]
            opciones.append({"prioridad": 0, "orden_v": orden_v, "variante": variante,
                             "clave": "+".join(f"{n}x{a}x{l}" for n, a, l in caso.detalle_hojas),
                             "util": sum(n * (a - banda) * l for n, a, l in caso.detalle_hojas), "planchas": planchas,
                             "supuesta": False,
                             "posible": all(_entran(con, a - banda, l) for _, a, l in caso.detalle_hojas)
                             and (len(caso.detalle_hojas) > 1 or minimo_planchas(
                                 con, caso.detalle_hojas[0][1] - banda, caso.detalle_hojas[0][2]) <= caso.hojas)})
            continue
        propias = set()
        for pl in mat.planchas:
            propias.add((pl.ancho, pl.largo))
            w, h = pl.ancho - banda, pl.largo
            opciones.append({"prioridad": 0, "orden_v": orden_v, "variante": variante, "clave": pl.clave(),
                             "util": caso.hojas * w * h,
                             "planchas": None if banda == BANDA_CORTE_CERTO_MM and not pl.supuesta else
                             [{"ancho": pl.ancho, "largo": pl.largo, "corte_banda": banda}],
                             "supuesta": pl.supuesta, "posible": minimo_planchas(con, w, h) <= caso.hojas})
        for prioridad, a, l in medidas_conocidas(catalogo, caso.material):
            if (a, l) not in propias:
                opciones.append({"prioridad": prioridad, "orden_v": orden_v, "variante": variante, "clave": f"{a}x{l}",
                                 "util": caso.hojas * (a - banda) * l,
                                 "planchas": [{"ancho": a, "largo": l, "corte_banda": banda}], "supuesta": False,
                                 "posible": minimo_planchas(con, a - banda, l) <= caso.hojas})
    salida = {"plancha": None, "planchas": None, "variante": None, "con_pulido": True, "supuesta": False,
              "medida_nueva": False, "ambigua": [], "alternativa": None, "detalle": "",
              "no_entran": not any(o["posible"] for o in opciones)}
    pruebas = []
    for o in opciones:
        if not o["posible"] or o["util"] <= 0:
            continue
        for con_pulido in ((True, False) if hay_pulido else (True,)):
            calc = mm2[con_pulido] / o["util"] * 100
            pruebas.append({**o, "con_pulido": con_pulido, "calc": calc,
                            "orden": (not con_pulido, o["prioridad"], o["orden_v"], abs(calc - caso.aprovechamiento), o["clave"])})
    pruebas.sort(key=lambda x: x["orden"])
    salida["detalle"] = ", ".join(f"{x['clave']} ({x['variante']}){'' if x['con_pulido'] else ' sin +3'}: {x['calc']:.2f} %"
                                  for x in pruebas[:4])
    cierran = [x for x in pruebas if comparar.cierra(x["calc"], caso.aprovechamiento, caso.decimales)]
    if cierran:
        x = cierran[0]
        salida.update({"plancha": x["clave"], "planchas": x["planchas"], "variante": x["variante"],
                       "supuesta": x["supuesta"], "con_pulido": x["con_pulido"], "medida_nueva": x["prioridad"] > 0,
                       "ambigua": sorted({y["clave"] for y in cierran[1:] if y["orden"][:3] == x["orden"][:3]
                                          and y["clave"] != x["clave"]})})
        if x["variante"] == VARIANTES[0][0]:
            otra = next((y for y in cierran if y["variante"] == VARIANTES[1][0] and y["clave"] == x["clave"]
                         and y["con_pulido"] == x["con_pulido"]), None)
            if otra is not None:
                salida["alternativa"] = {"plancha": otra["clave"], "planchas": otra["planchas"],
                                         "variante": otra["variante"]}
    return salida


def preparar(casos: list[CasoExportado], catalogo: Catalogo) -> tuple[list[dict], dict]:
    """Los casos que se pueden comparar ("trabajos" para `comparar.correr`) y la cobertura."""
    cob = {"casos": len(casos), "sin_hojas": [], "con_bandas": [], "area_no": [], "sin_piezas": [],
           "no_cierran": [], "control_ok": 0, "sin_mas3": 0, "plancha_supuesta": 0, "plancha_ambigua": 0,
           "con_detalle": 0, "con_avisos": 0, "medida_nueva": {}, "hoja_entera": 0, "con_alternativa": 0}
    trabajos = []
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
        cob["control_ok"] += 1
        avisos = [] if c["variante"] == VARIANTES[0][0] else ["con banda 20 no cierra o no entra: se usó la hoja entera"]
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
        if c["variante"] != VARIANTES[0][0]:
            cob["hoja_entera"] += 1
        if c["alternativa"]:
            cob["con_alternativa"] += 1
        piezas = _piezas(caso, c["con_pulido"])
        t = {"numero": caso.numero, "material": caso.material, "abreviado": caso.etiqueta,
             "relacion": caso.criterio, "cc_hojas": caso.hojas, "cc_aprov": caso.aprovechamiento,
             "plancha": c["plancha"], "planchas": c["planchas"], "con_pulido": c["con_pulido"],
             "plancha_supuesta": c["supuesta"], "avisos": avisos, "piezas": piezas,
             "n_piezas": sum(p["cantidad"] for p in piezas), "grupo": comparar._grupo(caso.material, catalogo),
             "calibracion": comparar.es_calibracion(caso.numero),
             "extra": {"fecha": caso.fecha, "tipos": len(piezas), "plancha_origen": origen_plancha,
                       "variante": c["variante"], "alternativa": False, "tiene_alternativa": bool(c["alternativa"])}}
        t["firma"] = comparar._firma(t)
        trabajos.append(t)
        if c["alternativa"]:
            # La misma comparación con la hoja entera (si Corte Certo no tenía banda en ese vidrio).
            alt = {**t, "plancha": c["alternativa"]["plancha"], "planchas": c["alternativa"]["planchas"],
                   "extra": {**t["extra"], "variante": c["alternativa"]["variante"], "alternativa": True}}
            alt["firma"] = comparar._firma(alt)
            trabajos.append(alt)
    return trabajos, cob


VISTAS = {"banda": "Banda 20 donde cierran las dos (la cuenta principal)",
          "entera": "Hoja entera donde cierran las dos",
          "seguros": "Solo los casos donde cierra una sola de las dos (se sabe cuál usó Corte Certo)"}


def markdown(cob: dict, prueba: dict, opciones: comparar.Opciones, origen: str, por_origen: dict | None = None,
             vistas: dict | None = None) -> str:
    lineas = [f"Datos: `{origen}` (exportados de Metrix el 25/10/2026). Esfuerzo: {opciones.esfuerzo}. "
              + ("Todos los casos." if opciones.muestra is None else f"Muestra de {opciones.muestra} casos.")
              + " Configuración: H0 (solo el corte banda, sin separación ni destaque: así se usaba Corte "
              "Certo), con la misma medida de plancha que dio el control.", "",
              "**Qué casos se pudieron comparar**", "", "| | Casos |", "|---|---|",
              f"| Casos exportados (presupuesto + vidrio) | {cob['casos']} |",
              f"| Sin cantidad de hojas (solo bandas o solo el %) | {len(cob['sin_hojas'])} |",
              f"| Corte Certo usó además bandas o recortes (no se puede repetir igual) | {len(cob['con_bandas'])} |",
              f"| El área de la hoja que se deduce no cierra (leyenda o vidrio mal anotado) | {len(cob['area_no'])} |",
              f"| Sin piezas | {len(cob['sin_piezas'])} |"]
    motivos: dict[str, int] = {}
    for x in cob["no_cierran"]:
        motivos[x["motivo"]] = motivos.get(x["motivo"], 0) + 1
    for motivo, n in sorted(motivos.items()):
        lineas.append(f"| No cierran: {comparar.MOTIVOS_NO_CIERRAN.get(motivo, motivo)} | {n} |")
    lineas += [f"| **Pasaron el control y se compararon** | **{cob['control_ok']}** |",
               f"| … de esos, cierran solo SIN el +3 mm del pulido (se calcularon sin el +3) | {cob['sin_mas3']} |",
               f"| … con las medidas de hoja anotadas en la leyenda | {cob['con_detalle']} |",
               f"| … con plancha supuesta (el material no está en hojas.csv) | {cob['plancha_supuesta']} |",
               f"| … con una medida de hoja que hojas.csv no tiene para ese material (ver abajo) | "
               f"{sum(sum(v.values()) for v in cob['medida_nueva'].values())} |",
               f"| … con más de una medida de plancha que cierra (se usó la más cercana) | {cob['plancha_ambigua']} |",
               f"| … donde con banda 20 no cierra o las piezas no entran, y se usó la hoja entera | {cob['hoja_entera']} |",
               f"| … donde cierran las dos (banda 20 y hoja entera): ver la línea de abajo | {cob['con_alternativa']} |", ""]
    if cob["medida_nueva"]:
        lineas += ["**Medidas de hoja que Corte Certo usó y no están en `hojas.csv`** (habría que sumarlas a "
                   "`Medidas_hojas.xlsx`; pregunta 29)", "", "| Material | Medida (casos) |", "|---|---|"]
        for mat, medidas in sorted(cob["medida_nueva"].items(), key=lambda x: -sum(x[1].values())):
            lineas.append(f"| {mat} | " + ", ".join(f"{m} ({n})" for m, n in sorted(medidas.items(), key=lambda x: -x[1])) + " |")
        lineas.append("")
    if por_origen:
        nombres = {"hojas.csv": "la medida de hoja del material en hojas.csv",
                   "leyenda": "las medidas de hoja anotadas en la leyenda",
                   "deducida": "una medida deducida (hojas.csv no la tiene para ese material)"}
        lineas += ["**Según de dónde salió la medida de hoja**", "",
                   "| Medida de hoja | Casos | Iguales | Menos planchas | Más planchas | Dif. media |",
                   "|---|---|---|---|---|---|"]
        for clave, r in por_origen.items():
            if r.get("casos"):
                lineas.append(f"| {nombres[clave]} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | "
                              f"{r['peores_%']} % | {r['diferencia_media']:+} |")
        lineas.append("")
    if vistas:
        lineas += ["**Banda 20 u hoja entera** (pregunta 28): en la mayoría de los casos el % de Corte Certo cierra "
                   "con las dos, así que se calcularon las dos y se muestran los dos extremos. La tercera fila son "
                   "los casos donde se sabe cuál usó (cierra una sola, o las piezas no entran en la otra).", "",
                   "| Supuesto sobre Corte Certo | Casos | Iguales | Menos planchas | Más planchas | Dif. media | "
                   "Peor |", "|---|---|---|---|---|---|---|"]
        for clave, nombre in VISTAS.items():
            r = vistas.get(clave) or {}
            if r.get("casos"):
                lineas.append(f"| {nombre} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | "
                              f"{r['peores_%']} % | {r['diferencia_media']:+} | {r['peor_diferencia']:+} |")
        lineas.append("")
    lineas += comparar.resultados_md({}, prueba, titulo="Resultado con banda 20 (todos los casos comparados)",
                                     con_eleccion=False)
    return "\n".join(lineas)
