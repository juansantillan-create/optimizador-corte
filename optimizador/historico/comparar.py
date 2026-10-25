"""Comparar contra lo que dio Corte Certo y calibrar las hipótesis (brief §10.3 y §10.4).

Por cada presupuesto con leyenda:
1. Se leen las líneas de la leyenda (`leyendas.py`) y se reconstruyen las piezas (`reconstruir.py`).
2. Cada material abreviado de la leyenda ("4+4 NLIGHT") se relaciona con un código de Metrix de las
   piezas del mismo presupuesto (`relacionar`). Si hay dudas, el caso va aparte con el motivo.
3. **Control de la entrada**: m² de piezas ÷ (hojas de la leyenda × plancha útil) tiene que dar el
   % de la leyenda (±0,6, porque la leyenda lo redondea). Se prueba cada medida de plancha del
   material, con y sin el +3 mm del pulido recto. Si no cierra, el caso se informa aparte.
4. Se calcula con las hipótesis H0, H1 y H2, **con la misma medida de plancha** que dio el control.
5. **Calibración**: con el 70 % de los casos (elegidos por número de presupuesto, siempre los
   mismos) se elige por grupo de material la hipótesis que más veces da las mismas planchas que
   Corte Certo; los números finales se informan sobre el 30 % restante.

Los resultados se guardan renglón por renglón en un JSONL a medida que salen: si la corrida se corta,
se retoma desde donde quedó.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from ..api import optimizar, tiene_pulido_recto
from ..configuracion import Catalogo, composicion_de_codigo
from . import leyendas as ley
from .datos import Casos
from .reconstruir import reconstruir

HIPOTESIS = ("H0", "H1", "H2")
TOLERANCIA_APROV = 0.6

# Palabras de las leyendas -> cómo aparecen en los códigos y descripciones de Metrix.
ALIAS = {
    "NLIGHT": ["NL", "NEUTRO LIGHT", "NEU LIGHT", "NEUTRAL"], "NL": ["NL", "NEUTRO LIGHT"],
    "LOWE": ["LOW", "LOW-E", "LOWE"], "LOW": ["LOW", "LOW-E"],
    "INC": ["IN", "INC", "INCOLORO"], "INCOLORO": ["IN", "INC"], "IN": ["IN", "INC"],
    "GRIS": ["GR", "GRIS"], "GC": ["GC", "GRIS CLARO"], "GO": ["GO", "GRIS OSCURO"],
    "CLARO": ["CLARO", "C"], "OSCURO": ["OSCURO", "O"],
    "BRONCE": ["BR", "BC", "BRONCE"], "BR": ["BR", "BRONCE"],
    "ESM": ["ES", "ESM", "ESMERILADO"], "ESMERILADO": ["ES", "ESMERILADO"],
    "VERDE": ["V", "VC", "VERDE"], "OPACID": ["OA", "OPACID"], "ESPEJO": ["OP", "OPTIMIRROR"],
    "ACUSTICO": ["AC", "ACUSTICO"], "EXTRA": ["EB", "EXTRA BLANCO"],
}


def _composicion_texto(texto: str) -> str | None:
    t = texto.upper()
    m = re.search(r"(\d+)\s*\+\s*(\d+)", t)
    if m:
        return f"{int(m.group(1))}+{int(m.group(2))}"
    m = re.search(r"(\d+)", t)
    return str(int(m.group(1))) if m else None


def relacionar(abreviado: str, candidatos: list[str], catalogo: Catalogo) -> tuple[str | None, str]:
    """Material de la leyenda -> código de Metrix entre los del presupuesto. Devuelve (código o
    None, motivo)."""
    if not candidatos:
        return None, "el presupuesto no tiene piezas de vidrio"
    if not abreviado:
        if len(candidatos) == 1:
            return candidatos[0], "la leyenda no dice el material y hay uno solo"
        return None, "la leyenda no dice el material y hay varios"
    comp = _composicion_texto(abreviado)
    def comp_de(codigo):
        return catalogo.composicion.get(codigo) or composicion_de_codigo(codigo)[0]
    mismos = [c for c in candidatos if comp is None or comp_de(c) == comp]
    if not mismos:
        if len(candidatos) == 1:
            return candidatos[0], f"composición distinta ({comp} contra {comp_de(candidatos[0])}), pero hay un solo material"
        return None, f"ningún material del presupuesto es {comp}"
    if len(mismos) == 1:
        return mismos[0], "único con esa composición"
    palabras = [p for p in re.findall(r"[A-Z]+", abreviado.upper()) if p not in ("MM", "FL", "LX", "LAM", "X")]
    puntajes = []
    for c in mismos:
        desc = catalogo.materiales[c].descripcion.upper() if c in catalogo.materiales else ""
        sufijo = re.sub(r"^[A-Z]*\d+(\+\d+)?", "", c)
        puntos = 0
        for p in palabras:
            formas = ALIAS.get(p, [p])
            if any(f == sufijo or sufijo.startswith(f) for f in formas if len(f) <= 3) or \
                    any(f in desc for f in formas if len(f) > 2):
                puntos += 1
        puntajes.append((puntos, c))
    puntajes.sort(reverse=True)
    if puntajes[0][0] > 0 and (len(puntajes) == 1 or puntajes[0][0] > puntajes[1][0]):
        return puntajes[0][1], f"por las palabras ({', '.join(palabras)})"
    return None, f"ambiguo entre {', '.join(c for _, c in puntajes)}"


def control_entrada(piezas: list[dict], material: str, hojas: int, aprov: float, catalogo: Catalogo):
    """¿Cierran los m² de las piezas con las hojas y el % de la leyenda? Devuelve (plancha "AxB" o
    None, con_pulido bool o None, detalle)."""
    mat = catalogo.material(material, "H0", usar_locales=False)
    mm2_con = sum((p["ancho"] + (3 if tiene_pulido_recto(p.get("clase", "")) else 0)) *
                  (p["largo"] + (3 if tiene_pulido_recto(p.get("clase", "")) else 0)) * p["cantidad"]
                  for p in piezas)
    mm2_sin = sum(p["ancho"] * p["largo"] * p["cantidad"] for p in piezas)
    pruebas = []
    for pl in mat.planchas:
        w, h = mat.util(pl)
        for con, mm2 in ((True, mm2_con), (False, mm2_sin)):
            calc = mm2 / (hojas * w * h) * 100 if hojas else 0
            pruebas.append((abs(calc - aprov), pl.clave(), con, calc))
    pruebas.sort(key=lambda x: (x[0], not x[2]))
    mejor = pruebas[0] if pruebas else None
    detalle = ", ".join(f"{c}{'+3' if con else ''}: {calc:.2f} %" for _, c, con, calc in pruebas[:4])
    if mejor and mejor[0] <= TOLERANCIA_APROV:
        return mejor[1], mejor[2], detalle
    return None, None, detalle


def es_calibracion(numero: str) -> bool:
    """70 % para calibrar, 30 % para informar. Siempre el mismo reparto (por el número)."""
    return int(hashlib.sha1(str(numero).encode()).hexdigest(), 16) % 10 < 7


@dataclass
class Opciones:
    esfuerzo: str = "normal"
    muestra: int | None = 50  # None = todos
    hipotesis: tuple[str, ...] = HIPOTESIS


def preparar(casos: Casos, catalogo: Catalogo) -> tuple[list[dict], dict]:
    """Lee leyendas y reconstruye: devuelve los "trabajos" (caso + material) y la cobertura."""
    codigos = set(catalogo.materiales)
    trabajos = []
    cobertura = {"presupuestos": len(casos.presupuestos), "con_texto": 0, "con_pinta": 0,
                 "leidos": 0, "lineas": 0, "relacionadas": 0, "control_ok": 0,
                 "no_leidas": [], "sin_relacionar": [], "no_cierran": [], "sin_piezas": []}
    for numero in sorted(casos.presupuestos, key=lambda n: (len(n), n)):
        fila = casos.presupuestos[numero]
        if any((v or "").strip() for k, v in fila.items() if k not in ("numero", "fecha", "estado_pres", "tipopresup")):
            cobertura["con_texto"] += 1
        leyenda = ley.buscar(fila)
        if not leyenda.tiene_pinta:
            continue
        cobertura["con_pinta"] += 1
        if not leyenda.lineas:
            cobertura["no_leidas"].append({"numero": numero, "lineas": leyenda.no_leidas[:3]})
            continue
        cobertura["leidos"] += 1
        rec = reconstruir(casos, numero, codigos)
        if not rec.piezas:
            cobertura["sin_piezas"].append({"numero": numero, "excluidos": rec.excluidos[:5]})
            continue
        candidatos = rec.materiales()
        for linea in leyenda.lineas:
            cobertura["lineas"] += 1
            codigo, motivo = relacionar(linea.material, candidatos, catalogo)
            if codigo is None:
                cobertura["sin_relacionar"].append({"numero": numero, "material": linea.material,
                                                    "motivo": motivo, "candidatos": candidatos})
                continue
            cobertura["relacionadas"] += 1
            piezas = [p for p in rec.piezas if p["material"] == codigo]
            if linea.aprovechamiento > 100 or linea.hojas <= 0:
                cobertura["no_cierran"].append({"numero": numero, "material": codigo,
                                                "leyenda": f"{linea.hojas} hojas {linea.aprovechamiento:g}%",
                                                "probado": "imposible (más de 100 % o 0 hojas)"})
                continue
            plancha, con_pulido, detalle = control_entrada(piezas, codigo, linea.hojas,
                                                           linea.aprovechamiento, catalogo)
            if plancha is None:
                cobertura["no_cierran"].append({"numero": numero, "material": codigo,
                                                "leyenda": f"{linea.hojas} hojas {linea.aprovechamiento:g}%",
                                                "probado": detalle})
                continue
            cobertura["control_ok"] += 1
            trabajos.append({"numero": numero, "material": codigo, "abreviado": linea.material,
                             "relacion": motivo, "cc_hojas": linea.hojas,
                             "cc_aprov": linea.aprovechamiento, "plancha": plancha,
                             "con_pulido": con_pulido, "piezas": piezas,
                             "n_piezas": sum(p["cantidad"] for p in piezas),
                             "grupo": _grupo(codigo, catalogo),
                             "calibracion": es_calibracion(numero)})
    return trabajos, cobertura


def _grupo(codigo: str, catalogo: Catalogo) -> str:
    comp = catalogo.composicion.get(codigo) or composicion_de_codigo(codigo)[0] or "?"
    regla = catalogo.reglas.get(comp)
    return regla["grupo"] if regla else comp


def correr(trabajos: list[dict], salida: Path, opciones: Opciones, catalogo: Catalogo,
           mostrar=print) -> list[dict]:
    """Corre las hipótesis. Lo ya calculado (en `salida`, JSONL) no se repite."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechos: dict[tuple, dict] = {}
    if salida.exists():
        for linea in salida.read_text(encoding="utf-8").splitlines():
            if linea.strip():
                r = json.loads(linea)
                hechos[(r["numero"], r["material"], r["hipotesis"], r["esfuerzo"])] = r
    elegidos = trabajos if opciones.muestra is None else _muestra(trabajos, opciones.muestra)
    filas = []
    with salida.open("a", encoding="utf-8") as archivo:
        for n, t in enumerate(elegidos, start=1):
            for hip in opciones.hipotesis:
                clave = (t["numero"], t["material"], hip, opciones.esfuerzo)
                if clave in hechos:
                    filas.append(hechos[clave])
                    continue
                entrada = {"proyecto": {"codigo": t["numero"], "descripcion": f"histórico {t['numero']}"},
                           "preset": hip, "piezas": t["piezas"], "fecha": "histórico",
                           "materiales": {t["material"]: {"planchas_habilitadas": _solo(t, catalogo)}},
                           "opciones": {"esfuerzo": opciones.esfuerzo}}
                if t["con_pulido"] is False:
                    # La leyenda cierra sin el +3: se respeta lo que se cargó en su momento.
                    entrada["materiales"][t["material"]]["sobremedida_pulido_mm"] = 0
                t0 = time.perf_counter()
                res = optimizar(entrada, catalogo=catalogo)
                m = res["materiales"][0]
                fila = {k: t[k] for k in ("numero", "material", "abreviado", "relacion", "cc_hojas",
                                          "cc_aprov", "plancha", "con_pulido", "n_piezas", "grupo",
                                          "calibracion")}
                fila.update({"hipotesis": hip, "esfuerzo": opciones.esfuerzo,
                             "planchas": m["planchas"], "aprovechamiento": m["aprovechamiento"],
                             "montajes": m["layouts"], "minimo": m.get("minimo_teorico_planchas"),
                             "verificado": res["verificado"], "errores": m["errores"][:3],
                             "segundos": round(time.perf_counter() - t0, 2)})
                # Los montajes, aparte (para dibujarlos en la página de revisión).
                carpeta = salida.parent / "montajes"
                carpeta.mkdir(exist_ok=True)
                (carpeta / nombre_montajes(t["numero"], t["material"], hip, opciones.esfuerzo)).write_text(
                    json.dumps([{k: mo[k] for k in ("numero", "repeticiones", "plancha", "piezas")}
                                for mo in m["montajes"]], ensure_ascii=False), encoding="utf-8")
                archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
                archivo.flush()
                filas.append(fila)
            mostrar(f"[{n}/{len(elegidos)}] {t['numero']} {t['material']}: Corte Certo {t['cc_hojas']} hojas; "
                    + ", ".join(f"{f['hipotesis']}={f['planchas']}" for f in filas[-len(opciones.hipotesis):]))
    return filas


def nombre_montajes(numero: str, material: str, hip: str, esfuerzo: str) -> str:
    return re.sub(r"[^A-Za-z0-9_+.-]", "_", f"{numero}_{material}_{hip}_{esfuerzo}") + ".json"


def _solo(t: dict, catalogo: Catalogo) -> dict:
    mat = catalogo.material(t["material"], "H0", usar_locales=False)
    return {p.clave(): p.clave() == t["plancha"] for p in mat.planchas}


def _muestra(trabajos: list[dict], n: int) -> list[dict]:
    """Una muestra fija (por número de presupuesto), mitad calibración y mitad prueba si se puede."""
    orden = sorted(trabajos, key=lambda t: hashlib.sha1(f"{t['numero']}|{t['material']}".encode()).hexdigest())
    return orden[:n]


# ----------------------------------------------------------------------- calibrar
def calibrar(filas: list[dict]) -> dict:
    """Elige por grupo de material la hipótesis que más reproduce a Corte Certo (con el 70 %)."""
    por_grupo: dict[str, dict[str, list[dict]]] = {}
    for f in filas:
        if f["calibracion"] and f["verificado"]:
            por_grupo.setdefault(f["grupo"], {}).setdefault(f["hipotesis"], []).append(f)
    eleccion = {}
    for grupo, hips in por_grupo.items():
        puntajes = []
        for hip, fs in hips.items():
            iguales = sum(f["planchas"] == f["cc_hojas"] for f in fs) / len(fs)
            dif = sum(abs(f["planchas"] - f["cc_hojas"]) for f in fs) / len(fs)
            puntajes.append((-iguales, dif, HIPOTESIS.index(hip) if hip in HIPOTESIS else 9, hip, len(fs)))
        puntajes.sort()
        _, dif, _, hip, n = puntajes[0]
        eleccion[grupo] = {"hipotesis": hip, "casos": n, "iguales": round(-puntajes[0][0] * 100, 1),
                           "diferencia_media_abs": round(dif, 2),
                           "todas": {p[3]: {"iguales_%": round(-p[0] * 100, 1), "dif_abs": round(p[1], 2)}
                                     for p in puntajes}}
    return eleccion


def informe_prueba(filas: list[dict], eleccion: dict) -> dict:
    """Números sobre el 30 % de prueba, con la hipótesis elegida para cada grupo (H0 si el grupo
    no tuvo casos de calibración)."""
    prueba = [f for f in filas if not f["calibracion"]
              and f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0")]
    def resumen(fs):
        if not fs:
            return {"casos": 0}
        difs = [f["planchas"] - f["cc_hojas"] for f in fs]
        return {"casos": len(fs),
                "iguales_%": round(sum(d == 0 for d in difs) / len(fs) * 100, 1),
                "mejores_%": round(sum(d < 0 for d in difs) / len(fs) * 100, 1),
                "peores_%": round(sum(d > 0 for d in difs) / len(fs) * 100, 1),
                "diferencia_media": round(sum(difs) / len(fs), 2),
                "peor_diferencia": max(difs),
                "corte_certo_en_el_minimo": sum(1 for f in fs if f["minimo"] is not None and f["cc_hojas"] <= f["minimo"]),
                "no_validados": sum(1 for f in fs if not f["verificado"])}
    por_material: dict[str, list] = {}
    por_tamano: dict[str, list] = {}
    for f in prueba:
        por_material.setdefault(f["material"], []).append(f)
        tam = "hasta 20 piezas" if f["n_piezas"] <= 20 else "21 a 100 piezas" if f["n_piezas"] <= 100 else "más de 100 piezas"
        por_tamano.setdefault(tam, []).append(f)
    peores = sorted(prueba, key=lambda f: (-(f["planchas"] - f["cc_hojas"]), f["numero"]))[:10]
    return {"total": resumen(prueba),
            "por_material": {k: resumen(v) for k, v in sorted(por_material.items())},
            "por_tamano": {k: resumen(v) for k, v in por_tamano.items()},
            "peores": [{k: f[k] for k in ("numero", "material", "n_piezas", "cc_hojas", "cc_aprov",
                                          "planchas", "aprovechamiento", "minimo", "plancha", "hipotesis")}
                       for f in peores if f["planchas"] > f["cc_hojas"]]}


def markdown(cobertura: dict, eleccion: dict, prueba: dict, opciones: Opciones, origen: str) -> str:
    """El texto para `docs/VALIDACION.md` (sección 1), en palabras simples."""
    c = cobertura
    t = prueba["total"]
    lineas = [f"Datos: `{origen}`. Esfuerzo: {opciones.esfuerzo}. "
              + ("Todos los casos." if opciones.muestra is None else f"Muestra de {opciones.muestra} casos."), "",
              "**Cobertura de la leyenda**", "",
              "| | Cantidad |", "|---|---|",
              f"| Presupuestos en el zip | {c['presupuestos']} |",
              f"| Con algo escrito | {c['con_texto']} |",
              f"| Con pinta de leyenda | {c['con_pinta']} |",
              f"| Leyenda leída | {c['leidos']} |",
              f"| Líneas de material leídas | {c['lineas']} |",
              f"| Material relacionado con un código de Metrix | {c['relacionadas']} |",
              f"| Pasaron el control de la entrada (m² ↔ % de la leyenda) | {c['control_ok']} |",
              f"| No se pudo leer la leyenda | {len(c['no_leidas'])} |",
              f"| No se pudo relacionar el material | {len(c['sin_relacionar'])} |",
              f"| No cierran (el presupuesto cambió o era otra plancha) | {len(c['no_cierran'])} |", "",
              "**Hipótesis elegida por grupo de material (con el 70 %)**", "",
              "| Grupo | Hipótesis | Casos | Iguales a Corte Certo |", "|---|---|---|---|"]
    for g, e in sorted(eleccion.items()):
        lineas.append(f"| {g} | {e['hipotesis']} | {e['casos']} | {e['iguales']} % |")
    lineas += ["", "**Resultado sobre el 30 % de prueba**", ""]
    if t["casos"]:
        lineas += [f"- Casos: {t['casos']}",
                   f"- Iguales a Corte Certo: {t['iguales_%']} %; con menos planchas: {t['mejores_%']} %; "
                   f"con más planchas: {t['peores_%']} %",
                   f"- Diferencia media: {t['diferencia_media']:+} planchas por caso (negativo = a favor); "
                   f"la peor: {t['peor_diferencia']:+}",
                   f"- Casos donde Corte Certo ya estaba en el mínimo teórico: {t['corte_certo_en_el_minimo']}",
                   f"- Resultados que no pasaron el validador: {t['no_validados']}", "",
                   "| Material | Casos | Iguales | Mejores | Peores | Dif. media |", "|---|---|---|---|---|---|"]
        for mat, r in prueba["por_material"].items():
            lineas.append(f"| {mat} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | {r['peores_%']} % | {r['diferencia_media']:+} |")
        lineas += ["", "| Tamaño | Casos | Iguales | Mejores | Peores | Dif. media |", "|---|---|---|---|---|---|"]
        for tam, r in prueba["por_tamano"].items():
            lineas.append(f"| {tam} | {r['casos']} | {r['iguales_%']} % | {r['mejores_%']} % | {r['peores_%']} % | {r['diferencia_media']:+} |")
        if prueba["peores"]:
            lineas += ["", "**Los peores (más planchas que Corte Certo)**", "",
                       "| Presupuesto | Material | Piezas | Corte Certo | Nuestro | Mínimo teórico | Plancha |",
                       "|---|---|---|---|---|---|---|"]
            for p in prueba["peores"]:
                lineas.append(f"| {p['numero']} | {p['material']} | {p['n_piezas']} | {p['cc_hojas']} ({p['cc_aprov']:g} %) | "
                              f"{p['planchas']} ({p['aprovechamiento']:g} %) | {p['minimo']} | {p['plancha']} |")
    else:
        lineas.append("No hay casos de prueba todavía.")
    return "\n".join(lineas)
