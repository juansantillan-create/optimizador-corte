"""Comparar contra lo que dio Corte Certo y calibrar las hipótesis (brief §10.3 y §10.4).

Por cada presupuesto con leyenda:
1. Se leen las líneas de la leyenda (`leyendas.py`) y se reconstruyen las piezas (`reconstruir.py`).
2. Cada material abreviado de la leyenda ("4+4 NLIGHT") se relaciona con un código de Metrix de las
   piezas del mismo presupuesto (`relacionar`). Si hay dudas, o si dos líneas van al mismo código,
   el caso va aparte con el motivo.
3. **Control de la entrada**: m² de piezas (con el +3 mm del pulido recto, como Corte Certo hoy) ÷
   (hojas de la leyenda × plancha útil) tiene que dar el % de la leyenda, redondeado como lo
   escribió la oficina (±0,5 si es entero, más 0,01 por el redondeo de Corte Certo). Se prueba
   cada medida de plancha del material en la que entren las piezas. Si no cierra, el caso se
   informa aparte (y se dice si cerraría sin el +3).
4. Se calcula con las hipótesis H0, H1 y H2, **con la misma medida de plancha** que dio el control.
5. **Calibración**: con el 70 % de los casos (elegidos por número de presupuesto, siempre los
   mismos) se elige por grupo de material la hipótesis que más veces da las mismas planchas que
   Corte Certo; los números finales se informan sobre el 30 % restante. Los resultados que no
   pasaron el validador o que dejaron piezas sin calcular no entran en las cuentas: se cuentan
   aparte.

Los resultados se guardan renglón por renglón en un JSONL a medida que salen: si la corrida se corta,
se retoma desde donde quedó (si cambiaron las piezas o la leyenda de un caso, se recalcula).
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

from ..api import optimizar, tiene_pulido_recto
from ..configuracion import PULIDO_RECTO_MM, Catalogo, composicion_de_codigo
from . import leyendas as ley
from .datos import Casos
from .reconstruir import reconstruir

HIPOTESIS = ("H0", "H1", "H2")
# Corte Certo da el % con 2 decimales y la oficina lo escribe redondeado (pregunta 24: ¿o lo trunca?).
MARGEN_CORTE_CERTO = 0.01


def cierra(calculado: float, leyenda: float, decimales: int = 0) -> bool:
    """¿Nuestro % puede ser el que escribió la oficina? Juan, 25/10 (pregunta 24): se redondeaba,
    pero según el comercial 90,57 % pudo quedar como 91 o como 90. Así que vale lo que da al
    redondear (±0,5) y lo que da al truncar (hasta 1 por encima), más 0,01 por el redondeo de
    Corte Certo."""
    paso = 10 ** -decimales
    return leyenda - paso / 2 - MARGEN_CORTE_CERTO <= calculado < leyenda + paso + MARGEN_CORTE_CERTO


def redondea(calculado: float, leyenda: float, decimales: int = 0) -> bool:
    """¿Da el % de la leyenda redondeando (lo normal, pregunta 24)? Más estricto que `cierra`."""
    paso = 10 ** -decimales
    return abs(calculado - leyenda) <= paso / 2 + MARGEN_CORTE_CERTO


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
# Palabras que no dicen nada del color o el tipo.
NEUTRAS = {"MM", "FL", "FLOAT", "LX", "LAM", "LAMINADO", "LAMILUX", "X", "TEMP", "TEMPLADO", "DVH", "PR",
           "PULIDO", "VIDRIO", "CRISTAL", "Y"}


def _composicion_texto(texto: str) -> str | None:
    t = texto.upper()
    m = re.search(r"(\d+)\s*\+\s*(\d+)", t)
    if m:
        return f"{int(m.group(1))}+{int(m.group(2))}"
    m = re.search(r"(\d+)", t)
    return str(int(m.group(1))) if m else None


def _coincide(palabra: str, codigo: str, catalogo: Catalogo) -> bool:
    desc = catalogo.materiales[codigo].descripcion.upper() if codigo in catalogo.materiales else ""
    sufijo = re.sub(r"^[A-Z]*\d+(\+\d+)?", "", codigo)
    formas = ALIAS.get(palabra, [palabra])
    return any(f == sufijo or sufijo.startswith(f) for f in formas if len(f) <= 3) or \
        any(f in desc for f in formas if len(f) > 2)


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
    palabras = [p for p in re.findall(r"[A-Z]+", abreviado.upper()) if p not in NEUTRAS]
    colores = [p for p in palabras if p in ALIAS]
    mismos = [c for c in candidatos if comp is None or comp_de(c) == comp]
    if not mismos:
        if len(candidatos) == 1 and not colores:
            return None, f"composición distinta ({comp} contra {comp_de(candidatos[0])})"
        return None, f"ningún material del presupuesto es {comp}"
    if len(mismos) == 1:
        c = mismos[0]
        if colores and not any(_coincide(p, c, catalogo) for p in colores):
            return None, f"{c} tiene esa composición, pero no es {' '.join(colores)}"
        return c, "único con esa composición" + (f" y {' '.join(colores)}" if colores else "")
    puntajes = sorted(((sum(_coincide(p, c, catalogo) for p in palabras), c) for c in mismos), reverse=True)
    if puntajes[0][0] > 0 and puntajes[0][0] > puntajes[1][0]:
        return puntajes[0][1], f"por las palabras ({', '.join(palabras)})"
    return None, f"ambiguo entre {', '.join(c for _, c in puntajes)}"


def _mm2(piezas: list[dict], con_pulido: bool) -> float:
    total = 0.0
    for p in piezas:
        extra = PULIDO_RECTO_MM if con_pulido and tiene_pulido_recto(p.get("clase", "")) else 0
        total += (p["ancho"] + extra) * (p["largo"] + extra) * p["cantidad"]
    return total


def _entran(piezas: list[dict], w: int, h: int, girar: bool) -> bool:
    for p in piezas:
        extra = PULIDO_RECTO_MM if tiene_pulido_recto(p.get("clase", "")) else 0
        a, l = p["ancho"] + extra, p["largo"] + extra
        if not ((a <= w and l <= h) or (girar and l <= w and a <= h)):
            return False
    return True


def control_entrada(piezas: list[dict], material: str, hojas: int, aprov: float, catalogo: Catalogo,
                    decimales: int = 0) -> dict:
    """¿Cierran los m² de las piezas (con el +3 del pulido recto) con las hojas y el % de la
    leyenda? Devuelve {"plancha": "AxB" o None, "detalle", "ambigua": [otras que también cierran],
    "cierra_sin_mas3": bool, "supuesta": bool, "no_entran": bool}."""
    mat = catalogo.material(material, "H0", usar_locales=False)
    girar = mat.rotacion and mat.textura == "sin"
    con, sin = _mm2(piezas, True), _mm2(piezas, False)
    pruebas = []
    for pl in mat.planchas:
        w, h = mat.util(pl)
        if not _entran(piezas, w, h, girar):
            continue
        calc = con / (hojas * w * h) * 100
        calc_sin = sin / (hojas * w * h) * 100
        pruebas.append((abs(calc - aprov), pl.clave(), calc, calc_sin, pl.supuesta))
    pruebas.sort()
    salida = {"plancha": None, "ambigua": [], "cierra_sin_mas3": False, "no_entran": not pruebas,
              "supuesta": any(pl.supuesta for pl in mat.planchas),
              "detalle": ", ".join(f"{c}: {calc:.2f} %" + (f" (sin +3: {cs:.2f} %)" if abs(cs - calc) > 1e-9 else "")
                                   for _, c, calc, cs, _ in pruebas[:4]) or
                        ("las piezas no entran en ninguna plancha" if mat.planchas else "el material no tiene planchas")}
    cierran = [x for x in pruebas if cierra(x[2], aprov, decimales)]
    if cierran:
        salida["plancha"] = cierran[0][1]
        salida["supuesta"] = cierran[0][4]
        salida["ambigua"] = [x[1] for x in cierran[1:]]
        salida["con_pulido"] = True
    elif con != sin:
        # Pregunta 25: "está bueno que en la validación pruebes los dos": si cierra sin el +3, se
        # compara igual, sin el +3 y marcado aparte.
        sin_mas3 = sorted((abs(cs - aprov), c, sup) for _, c, _, cs, sup in pruebas if cierra(cs, aprov, decimales))
        if sin_mas3:
            salida["cierra_sin_mas3"] = True
            salida["plancha"] = sin_mas3[0][1]
            salida["supuesta"] = sin_mas3[0][2]
            salida["ambigua"] = [x[1] for x in sin_mas3[1:]]
            salida["con_pulido"] = False
    return salida


def es_calibracion(numero: str) -> bool:
    """70 % para calibrar, 30 % para informar. Siempre el mismo reparto (por el número)."""
    return int(hashlib.sha1(str(numero).encode()).hexdigest(), 16) % 10 < 7


@dataclass
class Opciones:
    esfuerzo: str = "normal"
    muestra: int | None = 50  # None = todos
    hipotesis: tuple[str, ...] = HIPOTESIS
    procesos: int = 1  # casos que se calculan a la vez (en la nube, varios; en la PC, 1)
    repaso_maximo: bool = False  # casos exportados: repetir con esfuerzo máximo los que dan más hojas


def _firma(t: dict) -> str:
    """Huella de lo que entra al cálculo: si cambia, el caso se recalcula al retomar."""
    datos = json.dumps([t["piezas"], t["plancha"], t["cc_hojas"], t["cc_aprov"], PULIDO_RECTO_MM,
                        t.get("con_pulido", True), t.get("planchas")],
                       sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(datos.encode()).hexdigest()[:16]


def preparar(casos: Casos, catalogo: Catalogo) -> tuple[list[dict], dict]:
    """Lee leyendas y reconstruye: devuelve los "trabajos" (caso + material) y la cobertura."""
    codigos = set(catalogo.materiales)
    trabajos = []
    cobertura = {"presupuestos": len(casos.presupuestos), "con_texto": 0, "con_pinta": 0,
                 "leidos": 0, "lineas": 0, "relacionadas": 0, "control_ok": 0,
                 "no_leidas": [], "lineas_no_leidas": [], "ignoradas": 0, "sin_relacionar": [],
                 "repetidas": [], "no_cierran": [], "sin_piezas": [], "con_avisos": 0,
                 "plancha_supuesta": 0, "plancha_ambigua": 0}
    for numero in sorted(casos.presupuestos, key=lambda n: (len(n), n)):
        fila = casos.presupuestos[numero]
        if any((v or "").strip() for k, v in fila.items() if k not in ("numero", "fecha", "estado_pres", "tipopresup")):
            cobertura["con_texto"] += 1
        leyenda = ley.buscar(fila)
        if not leyenda.tiene_pinta:
            continue
        cobertura["con_pinta"] += 1
        cobertura["ignoradas"] += len(leyenda.ignoradas)
        if not leyenda.lineas:
            cobertura["no_leidas"].append({"numero": numero, "lineas": leyenda.no_leidas[:3]})
            continue
        cobertura["leidos"] += 1
        if leyenda.no_leidas:
            # Se leyó algo, pero no todo: puede faltar un material.
            cobertura["lineas_no_leidas"].append({"numero": numero, "lineas": leyenda.no_leidas[:3]})
        rec = reconstruir(casos, numero, codigos)
        if not rec.piezas:
            cobertura["sin_piezas"].append({"numero": numero, "excluidos": rec.excluidos[:5],
                                            "avisos": rec.avisos[:5]})
            continue
        candidatos = rec.materiales()
        relacion = []
        for linea in leyenda.lineas:
            cobertura["lineas"] += 1
            codigo, motivo = relacionar(linea.material, candidatos, catalogo)
            if codigo is None:
                cobertura["sin_relacionar"].append({"numero": numero, "material": linea.material,
                                                    "motivo": motivo, "candidatos": candidatos})
                continue
            relacion.append((linea, codigo, motivo))
        por_codigo: dict[str, int] = {}
        for _, codigo, _ in relacion:
            por_codigo[codigo] = por_codigo.get(codigo, 0) + 1
        for linea, codigo, motivo in relacion:
            if por_codigo[codigo] > 1:
                # Dos líneas de la leyenda van al mismo código: no se sabe cuál es cuál.
                cobertura["repetidas"].append({"numero": numero, "material": codigo,
                                               "lineas": [l.material for l, c, _ in relacion if c == codigo]})
                continue
            cobertura["relacionadas"] += 1
            piezas = [p for p in rec.piezas if p["material"] == codigo]
            avisos = list(rec.avisos_material.get(codigo, []))
            no_cierra = {"numero": numero, "material": codigo,
                         "leyenda": f"{linea.hojas} hojas {linea.aprovechamiento:g}%", "avisos": avisos[:3]}
            if linea.aprovechamiento > 100 or linea.hojas <= 0:
                cobertura["no_cierran"].append({**no_cierra, "motivo": "imposible",
                                                "probado": "imposible (más de 100 % o 0 hojas)"})
                continue
            control = control_entrada(piezas, codigo, linea.hojas, linea.aprovechamiento, catalogo,
                                      linea.decimales)
            if control["plancha"] is None:
                motivo_nc = ("no_entran" if control["no_entran"] else
                             "reconstruccion" if avisos else "no_cierra")
                cobertura["no_cierran"].append({**no_cierra, "motivo": motivo_nc, "probado": control["detalle"]})
                continue
            cobertura["control_ok"] += 1
            if control["cierra_sin_mas3"]:
                avisos.append("la leyenda cierra solo SIN el +3 mm del pulido recto: se calcula sin el +3")
                cobertura["sin_mas3"] = cobertura.get("sin_mas3", 0) + 1
            if control["supuesta"]:
                avisos.append(f"{codigo} no está en hojas.csv: se usó una plancha supuesta ({control['plancha']})")
                cobertura["plancha_supuesta"] += 1
            if control["ambigua"]:
                avisos.append(f"también cierra con {', '.join(control['ambigua'])}; se usó {control['plancha']}, "
                              f"la más cercana (pregunta 3)")
                cobertura["plancha_ambigua"] += 1
            if avisos:
                cobertura["con_avisos"] += 1
            t = {"numero": numero, "material": codigo, "abreviado": linea.material,
                 "relacion": motivo, "cc_hojas": linea.hojas,
                 "cc_aprov": linea.aprovechamiento, "plancha": control["plancha"],
                 "con_pulido": control.get("con_pulido", True),
                 "plancha_supuesta": control["supuesta"], "avisos": avisos, "piezas": piezas,
                 "n_piezas": sum(p["cantidad"] for p in piezas),
                 "grupo": _grupo(codigo, catalogo),
                 "calibracion": es_calibracion(numero)}
            t["firma"] = _firma(t)
            trabajos.append(t)
    return trabajos, cobertura


def _grupo(codigo: str, catalogo: Catalogo) -> str:
    comp = catalogo.composicion.get(codigo) or composicion_de_codigo(codigo)[0] or "?"
    regla = catalogo.reglas.get(comp)
    return regla["grupo"] if regla else comp


def _leer_hechos(salida: Path, mostrar) -> dict[tuple, dict]:
    hechos: dict[tuple, dict] = {}
    if not salida.exists():
        return hechos
    for n, linea in enumerate(salida.read_text(encoding="utf-8").splitlines(), start=1):
        if not linea.strip():
            continue
        try:
            r = json.loads(linea)
        except json.JSONDecodeError:
            # La corrida anterior se cortó a mitad de una línea: ese caso se vuelve a calcular.
            mostrar(f"aviso: la línea {n} de {salida.name} está cortada; ese caso se recalcula")
            continue
        hechos[(r["numero"], r["material"], r["hipotesis"], r["esfuerzo"], r.get("firma"))] = r
    return hechos


def entrada_de(t: dict, hip: str, esfuerzo: str, catalogo: Catalogo) -> dict:
    """La entrada de `optimizar()` para un caso: sus piezas y solo la plancha que dio el control
    (o las medidas de hoja que anotó la oficina, en `planchas`)."""
    ajustes = {"planchas": t["planchas"]} if t.get("planchas") else {"planchas_habilitadas": _solo(t, catalogo)}
    if t.get("con_pulido") is False:
        ajustes["sobremedida_pulido_mm"] = 0
    return {"proyecto": {"codigo": t["numero"], "descripcion": f"histórico {t['numero']}"},
            "preset": hip, "piezas": t["piezas"], "fecha": "histórico",
            "materiales": {t["material"]: ajustes}, "opciones": {"esfuerzo": esfuerzo}}


CAMPOS_FILA = ("numero", "material", "abreviado", "relacion", "cc_hojas", "cc_aprov", "plancha",
               "plancha_supuesta", "avisos", "n_piezas", "grupo", "calibracion", "firma")


def calcular_caso(t: dict, hip: str, esfuerzo: str, catalogo: Catalogo) -> tuple[dict, list]:
    """Corre un caso con una hipótesis. Devuelve (fila de resultados, montajes para dibujar)."""
    t0 = time.perf_counter()
    res = optimizar(entrada_de(t, hip, esfuerzo, catalogo), catalogo=catalogo)
    m = res["materiales"][0]
    fila = {k: t.get(k) for k in CAMPOS_FILA}
    fila.update({k: t[k] for k in ("con_pulido", "extra") if k in t})
    fila.update({"hipotesis": hip, "esfuerzo": esfuerzo,
                 "planchas": m["planchas"], "aprovechamiento": m["aprovechamiento"],
                 "m2_planchas": m.get("m2_planchas"),
                 "montajes": m["layouts"], "minimo": m.get("minimo_teorico_planchas"),
                 "verificado": res["verificado"], "completo": not m["errores"],
                 "errores": m["errores"][:3],
                 "segundos": round(time.perf_counter() - t0, 2)})
    montajes = [{k: mo[k] for k in ("numero", "repeticiones", "plancha", "piezas")} for mo in m["montajes"]]
    return fila, montajes


_CATALOGO_PROCESO: Catalogo | None = None


def _trabajar(tarea):
    """Para los procesos de `multiprocessing` (cada uno arma su catálogo una vez)."""
    global _CATALOGO_PROCESO
    if _CATALOGO_PROCESO is None:
        _CATALOGO_PROCESO = Catalogo(usar_locales=False)
    t, hip, esfuerzo = tarea
    return calcular_caso(t, hip, esfuerzo, _CATALOGO_PROCESO)


def correr(trabajos: list[dict], salida: Path, opciones: Opciones, catalogo: Catalogo,
           mostrar=print) -> list[dict]:
    """Corre las hipótesis. Lo ya calculado (en `salida`, JSONL) no se repite. Con
    `opciones.procesos` > 1 calcula varios casos a la vez (el resultado es el mismo: cada caso no
    depende de los otros, y se guardan en el mismo orden)."""
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechos = _leer_hechos(salida, mostrar)
    elegidos = trabajos if opciones.muestra is None else _muestra(trabajos, opciones.muestra)
    pendientes = []
    por_clave: dict[tuple, dict] = {}
    for t in elegidos:
        for hip in opciones.hipotesis:
            clave = (t["numero"], t["material"], hip, opciones.esfuerzo, t["firma"])
            if clave in hechos and hechos[clave].get("verificado"):
                # La cuenta es la misma (misma firma); los datos de contexto, los de ahora. (Lo que
                # no pasó el validador se vuelve a calcular: puede haber sido un error ya arreglado.)
                por_clave[clave] = {**hechos[clave], "extra": t.get("extra") or {}}
            else:
                pendientes.append((t, hip, opciones.esfuerzo))
    if hechos and pendientes:
        mostrar(f"Ya calculados: {len(por_clave)}; faltan {len(pendientes)}")
    texto_previo = salida.read_text(encoding="utf-8") if salida.exists() else ""
    carpeta = salida.parent / "montajes"
    carpeta.mkdir(exist_ok=True)
    with salida.open("a", encoding="utf-8") as archivo:
        if texto_previo and not texto_previo.endswith("\n"):
            archivo.write("\n")  # que lo nuevo no quede pegado a una línea cortada
        if opciones.procesos > 1 and len(pendientes) > 1:
            import multiprocessing
            contexto = multiprocessing.get_context("spawn")  # igual en Windows y en Linux
            with contexto.Pool(opciones.procesos) as pool:
                resultados = pool.imap(_trabajar, pendientes, chunksize=1)
                _guardar_resultados(resultados, pendientes, archivo, carpeta, por_clave, mostrar)
        else:
            resultados = (calcular_caso(t, hip, esf, catalogo) for t, hip, esf in pendientes)
            _guardar_resultados(resultados, pendientes, archivo, carpeta, por_clave, mostrar)
    filas = []
    for t in elegidos:
        for hip in opciones.hipotesis:
            fila = por_clave.get((t["numero"], t["material"], hip, opciones.esfuerzo, t["firma"]))
            if fila is not None:
                filas.append(fila)
    return filas


def _guardar_resultados(resultados, pendientes, archivo, carpeta, por_clave, mostrar) -> None:
    for n, ((t, hip, esfuerzo), (fila, montajes)) in enumerate(zip(pendientes, resultados), start=1):
        sufijo = "_alternativa" if (t.get("extra") or {}).get("alternativa") else ""
        (carpeta / nombre_montajes(t["numero"], t["material"] + sufijo, hip, esfuerzo)).write_text(
            json.dumps(montajes, ensure_ascii=False), encoding="utf-8")
        archivo.write(json.dumps(fila, ensure_ascii=False) + "\n")
        archivo.flush()
        por_clave[(t["numero"], t["material"], hip, esfuerzo, t["firma"])] = fila
        mostrar(f"[{n}/{len(pendientes)}] {t['numero']} {t['material']} {hip}: Corte Certo {t['cc_hojas']} "
                f"hojas; nuestro {fila['planchas']} ({fila['segundos']:g} s)")


def nombre_montajes(numero: str, material: str, hip: str, esfuerzo: str) -> str:
    return re.sub(r"[^A-Za-z0-9_+.-]", "_", f"{numero}_{material}_{hip}_{esfuerzo}") + ".json"


def _solo(t: dict, catalogo: Catalogo) -> dict:
    mat = catalogo.material(t["material"], "H0", usar_locales=False)
    return {p.clave(): p.clave() == t["plancha"] for p in mat.planchas}


def _muestra(trabajos: list[dict], n: int) -> list[dict]:
    """Una muestra fija (por número de presupuesto y material), con casos de calibración y de
    prueba intercalados (7 de calibración por cada 3 de prueba, como el reparto)."""
    # Se eligen casos (presupuesto + material), no trabajos: si un caso tiene una variante (la hoja
    # entera en los casos exportados), va entera con él y no cuenta como otro caso.
    primeros: dict[tuple[str, str], dict] = {}
    for t in trabajos:
        primeros.setdefault((t["numero"], t["material"]), t)
    orden = sorted(primeros.values(), key=lambda t: hashlib.sha1(f"{t['numero']}|{t['material']}".encode()).hexdigest())
    calib = [t for t in orden if t["calibracion"]]
    prueba = [t for t in orden if not t["calibracion"]]
    elegidos = []
    while len(elegidos) < n and (calib or prueba):
        for lista, cuantos in ((calib, 7), (prueba, 3)):
            for _ in range(cuantos):
                if lista and len(elegidos) < n:
                    elegidos.append(lista.pop(0))
    claves = [(t["numero"], t["material"]) for t in elegidos]
    por_clave: dict[tuple[str, str], list[dict]] = {}
    for t in trabajos:
        por_clave.setdefault((t["numero"], t["material"]), []).append(t)
    return [t for clave in claves for t in por_clave[clave]]


def cuenta(f: dict) -> bool:
    """¿Entra este resultado en las cuentas? Solo si pasó el validador y calculó todas las piezas."""
    return bool(f["verificado"]) and f.get("completo", not f.get("errores"))


# ----------------------------------------------------------------------- calibrar
def calibrar(filas: list[dict]) -> dict:
    """Elige por grupo de material la hipótesis que más reproduce a Corte Certo (con el 70 %)."""
    por_grupo: dict[str, dict[str, list[dict]]] = {}
    for f in filas:
        if f["calibracion"] and cuenta(f):
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


def informe_prueba(filas: list[dict], eleccion: dict, solo_prueba: bool = True) -> dict:
    """Números sobre el 30 % de prueba (o sobre todos, con `solo_prueba=False`, cuando la hipótesis
    no se calibró), con la hipótesis elegida para cada grupo (H0 si el grupo no tuvo casos de
    calibración)."""
    todas = [f for f in filas if (not solo_prueba or not f["calibracion"])
             and f["hipotesis"] == eleccion.get(f["grupo"], {}).get("hipotesis", "H0")]
    prueba = [f for f in todas if cuenta(f)]
    def resumen(fs, todas_fs):
        base = {"no_validados": sum(1 for f in todas_fs if not f["verificado"]),
                "incompletos": sum(1 for f in todas_fs if f["verificado"] and not cuenta(f))}
        if not fs:
            return {"casos": 0, **base}
        difs = [f["planchas"] - f["cc_hojas"] for f in fs]
        return {"casos": len(fs),
                "iguales_%": round(sum(d == 0 for d in difs) / len(fs) * 100, 1),
                "mejores_%": round(sum(d < 0 for d in difs) / len(fs) * 100, 1),
                "peores_%": round(sum(d > 0 for d in difs) / len(fs) * 100, 1),
                "diferencia_media": round(sum(difs) / len(fs), 2),
                "peor_diferencia": max(difs),
                "corte_certo_en_el_minimo": sum(1 for f in fs if f["minimo"] is not None and f["cc_hojas"] == f["minimo"]),
                # Menos hojas que el mínimo teórico es imposible: la leyenda o las piezas no son las de ese cálculo.
                "corte_certo_debajo_del_minimo": sum(1 for f in fs if f["minimo"] is not None and f["cc_hojas"] < f["minimo"]),
                "con_avisos": sum(1 for f in fs if f.get("avisos")),
                **base}
    por_material: dict[str, list] = {}
    por_tamano: dict[str, list] = {}
    def tamano(f):
        return "hasta 20 piezas" if f["n_piezas"] <= 20 else "21 a 100 piezas" if f["n_piezas"] <= 100 else "más de 100 piezas"
    for f in prueba:
        por_material.setdefault(f["material"], []).append(f)
        por_tamano.setdefault(tamano(f), []).append(f)
    peores = sorted(prueba, key=lambda f: (-(f["planchas"] - f["cc_hojas"]), f["numero"]))[:10]
    return {"total": resumen(prueba, todas),
            "por_material": {k: resumen(v, [f for f in todas if f["material"] == k]) for k, v in sorted(por_material.items())},
            "por_tamano": {k: resumen(v, [f for f in todas if tamano(f) == k]) for k, v in por_tamano.items()},
            "peores": [{k: f[k] for k in ("numero", "material", "n_piezas", "cc_hojas", "cc_aprov",
                                          "planchas", "aprovechamiento", "minimo", "plancha", "hipotesis")}
                       for f in peores if f["planchas"] > f["cc_hojas"]]}


MOTIVOS_NO_CIERRAN = {
    "no_cierra": "los m² no dan el % de la leyenda (el presupuesto cambió o era otra plancha)",
    "sin_mas3": "cierran solo SIN el +3 mm del pulido recto",
    "reconstruccion": "no cierran y la reconstrucción de las piezas tiene avisos",
    "no_entran": "las piezas no entran en ninguna plancha del material",
    "imposible": "la leyenda dice más de 100 % o 0 hojas",
}


def markdown(cobertura: dict, eleccion: dict, prueba: dict, opciones: Opciones, origen: str,
             inventado: bool = False) -> str:
    """El texto para `docs/VALIDACION.md` (sección 1), en palabras simples."""
    c = cobertura
    no_cierran: dict[str, int] = {}
    for x in c["no_cierran"]:
        no_cierran[x.get("motivo", "no_cierra")] = no_cierran.get(x.get("motivo", "no_cierra"), 0) + 1
    lineas = []
    if inventado:
        lineas += ["> **DATOS INVENTADOS** (caso de juguete): estos números solo prueban que el programa "
                   "anda; no dicen nada de Corte Certo.", ""]
    lineas += [f"Datos: `{origen}`. Esfuerzo: {opciones.esfuerzo}. "
               + ("Todos los casos." if opciones.muestra is None else f"Muestra de {opciones.muestra} casos."), "",
               "**Cobertura de la leyenda**", "",
               "| | Cantidad |", "|---|---|",
               f"| Presupuestos en el zip | {c['presupuestos']} |",
               f"| Con algo escrito | {c['con_texto']} |",
               f"| Con pinta de leyenda | {c['con_pinta']} |",
               f"| Leyenda leída | {c['leidos']} |",
               f"| … de esas, con alguna línea que no se entendió | {len(c.get('lineas_no_leidas', []))} |",
               f"| No se pudo leer la leyenda | {len(c['no_leidas'])} |",
               f"| Líneas que no son materiales (TOTAL, etc.) | {c.get('ignoradas', 0)} |",
               f"| Leyenda leída pero sin piezas de vidrio reconstruidas | {len(c.get('sin_piezas', []))} |",
               f"| Líneas de material leídas | {c['lineas']} |",
               f"| Material relacionado con un código de Metrix | {c['relacionadas']} |",
               f"| No se pudo relacionar el material | {len(c['sin_relacionar'])} |",
               f"| Dos líneas de la leyenda van al mismo código (no se comparan) | {len(c.get('repetidas', []))} |",
               f"| Pasaron el control de la entrada (m² ↔ % de la leyenda) | {c['control_ok']} |"]
    for motivo, texto in MOTIVOS_NO_CIERRAN.items():
        if no_cierran.get(motivo):
            lineas.append(f"| No cierran: {texto} | {no_cierran[motivo]} |")
    lineas += [f"| Comparados con avisos de la reconstrucción o de la plancha | {c.get('con_avisos', 0)} |",
               f"| … con plancha supuesta (el material no está en hojas.csv) | {c.get('plancha_supuesta', 0)} |",
               f"| … con más de una medida de plancha que cierra | {c.get('plancha_ambigua', 0)} |", "",
               ]
    lineas += resultados_md(eleccion, prueba)
    return "\n".join(lineas)


def resultados_md(eleccion: dict, prueba: dict, titulo: str = "Resultado sobre el 30 % de prueba",
                  con_eleccion: bool = True) -> list[str]:
    """Las tablas de resultados (iguales, mejores, peores; por material y tamaño; los peores)."""
    t = prueba["total"]
    lineas = []
    if con_eleccion:
        lineas += ["**Hipótesis elegida por grupo de material (con el 70 %)**", "",
                   "| Grupo | Hipótesis | Casos | Iguales a Corte Certo |", "|---|---|---|---|"]
        for g, e in sorted(eleccion.items()):
            lineas.append(f"| {g} | {e['hipotesis']} | {e['casos']} | {e['iguales']} % |")
        lineas.append("")
    lineas += [f"**{titulo}**", ""]
    if t["casos"]:
        lineas += [f"- Casos: {t['casos']}",
                   f"- Iguales a Corte Certo: {t['iguales_%']} %; con menos planchas: {t['mejores_%']} %; "
                   f"con más planchas: {t['peores_%']} %",
                   f"- Diferencia media: {t['diferencia_media']:+} planchas por caso (negativo = a favor); "
                   f"la peor: {t['peor_diferencia']:+}",
                   f"- Casos donde Corte Certo ya estaba en el mínimo teórico: {t['corte_certo_en_el_minimo']}",
                   f"- Casos donde la leyenda dice menos hojas que el mínimo teórico (imposible; hay que "
                   f"mirarlos): {t['corte_certo_debajo_del_minimo']}",
                   f"- Casos comparados con avisos: {t['con_avisos']}",
                   f"- Resultados que no pasaron el validador (fuera de las cuentas): {t['no_validados']}",
                   f"- Resultados con piezas sin calcular (fuera de las cuentas): {t['incompletos']}", "",
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
    return lineas
