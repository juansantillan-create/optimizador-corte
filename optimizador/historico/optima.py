"""Comparar contra cortes reales hechos con Optima (`datos/casos/optima/`, 25/10/2026).

Cada lote es una corrida de Optima: varios pedidos del mismo vidrio, cortados en planta. Se sabe
qué hojas se usaron (cantidad × medida) y los m² de piezas (ver el `LEEME.txt` de la carpeta).

Cómo se compara (Juan, 25/10/2026: "los de Optima sí llevan la configuración de la distancia mínima
para destaque y entre hojas"; los de Corte Certo no):
- mismas piezas (ya con el +3 mm del pulido recto) y las **mismas medidas de hoja** que usó Optima;
- configuración de producción: corte banda y **destaque mínimo** de la regla de Lucas (preset
  `lucas`). "Entre hojas" se interpretó como el corte banda de la hoja (pregunta 31);
- el programa no sabe cuántas hojas de cada medida había en stock: puede usar todas las que quiera
  de cada medida. Optima usó las que había (y en un lote, retazos). Por eso se comparan los **m² de
  hoja**, con esfuerzo normal (el de la oficina) y con el máximo.

Además se calcula como se cotizaría ("Como Corte Certo hoy", sin destaque, con la plancha por
defecto del vidrio), para ver cuánto cambia.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..api import optimizar
from ..configuracion import Catalogo, composicion_de_codigo


@dataclass
class Lote:
    lote: str
    material: str
    descripcion: str
    hojas: list[tuple[int, int, int]]  # (cantidad, ancho, largo), ancho = lado largo
    retazos: list[tuple[int, int, int]]
    m2_hojas: float
    m2_piezas: float
    aprovechamiento_bruto: float
    desperdicio_real: float
    piezas: list[dict] = field(default_factory=list)


def _medidas(texto: str) -> list[tuple[int, int, int]]:
    salida = []
    for parte in (texto or "").split(";"):
        m = re.fullmatch(r"\s*(\d+)\s*x\s*(\d+)\s*x\s*(\d+)\s*", parte, re.IGNORECASE)
        if m:
            n, a, b = (int(g) for g in m.groups())
            salida.append((n, max(a, b), min(a, b)))
    return salida


def _float(texto: str) -> float:
    try:
        return float((texto or "0").replace(",", "."))
    except ValueError:
        return 0.0


def leer(carpeta: Path) -> list[Lote]:
    carpeta = Path(carpeta)
    lotes: dict[str, Lote] = {}
    with (carpeta / "lotes_optima.csv").open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            lotes[r["lote"]] = Lote(
                lote=r["lote"], material=r["v_codart"].strip().upper(), descripcion=r.get("descripcion", ""),
                hojas=_medidas(r.get("hojas", "")), retazos=_medidas(r.get("retazos", "")),
                m2_hojas=_float(r.get("m2_hojas")), m2_piezas=_float(r.get("m2_piezas")),
                aprovechamiento_bruto=_float(r.get("aprovechamiento_bruto_pct")),
                desperdicio_real=_float(r.get("desperdicio_real_optima_pct")))
    with (carpeta / "piezas.csv").open(encoding="utf-8-sig", newline="") as f:
        for n, p in enumerate(csv.DictReader(f, delimiter=";"), start=1):
            lote = lotes.get(p["lote"])
            if lote is None:
                continue
            # Medida a optimizar: ya trae el +3 del pulido recto. Sin "clase": no se suma nada más.
            lote.piezas.append({"item": f"{p['pedido']}-{n}", "material": lote.material,
                                "cantidad": int(float(p["cantidad"])), "ancho": int(float(p["ancho"])),
                                "largo": int(float(p["largo"])), "descripcion": f"pedido {p['pedido']}"})
    return sorted(lotes.values(), key=lambda x: x.lote)


def _banda(lote: Lote, catalogo: Catalogo, preset: str) -> int:
    """La banda del material con ese preset (la de la regla de Lucas, o 20 como Corte Certo)."""
    mat = catalogo.material(lote.material, preset, usar_locales=False)
    if mat.planchas:
        return mat.planchas[0].corte_banda
    comp = composicion_de_codigo(lote.material)[0]
    regla = catalogo.reglas.get(comp) if comp else None
    return int(regla["corte_banda_mm"]) if regla else 20


def calcular(lote: Lote, catalogo: Catalogo, preset: str = "lucas", esfuerzo: str = "normal",
             medidas_de_optima: bool = True) -> dict:
    """Las piezas del lote con las medidas de hoja que usó Optima (o, con `medidas_de_optima`
    falso, con la plancha por defecto del vidrio, como se cotizaría)."""
    banda = _banda(lote, catalogo, preset)
    medidas = sorted({(a, l) for _, a, l in lote.hojas})
    materiales = ({lote.material: {"planchas": [{"ancho": a, "largo": l, "corte_banda": banda} for a, l in medidas]}}
                  if medidas_de_optima else {})
    entrada = {"proyecto": {"codigo": f"lote {lote.lote}", "descripcion": "comparación con Optima"},
               "preset": preset, "piezas": lote.piezas, "fecha": "histórico", "materiales": materiales,
               "opciones": {"esfuerzo": esfuerzo}}
    res = optimizar(entrada, catalogo=catalogo)
    m = res["materiales"][0]
    hojas_usadas = {}
    for u in m["planchas_usadas"]:
        clave = f"{u['hoja_ancho']}x{u['hoja_largo']}" if "hoja_ancho" in u else f"{u['ancho']}x{u['largo']}"
        hojas_usadas[clave] = hojas_usadas.get(clave, 0) + u["cantidad"]
    m2_hojas = sum(n * int(c.split("x")[0]) * int(c.split("x")[1]) for c, n in hojas_usadas.items()) / 1e6
    return {"preset": preset, "esfuerzo": esfuerzo, "planchas": m["planchas"], "hojas": hojas_usadas,
            "m2_hojas": round(m2_hojas, 3), "m2_piezas": m["m2_piezas"],
            "aprovechamiento_bruto": round(m["m2_piezas"] / m2_hojas * 100, 1) if m2_hojas else 0.0,
            "aprovechamiento_util": m["aprovechamiento"], "montajes": m["layouts"],
            "minimo": m.get("minimo_teorico_planchas"), "verificado": res["verificado"],
            "completo": res["completo"], "errores": m["errores"][:3], "avisos": m["avisos"][:3],
            "destaque": m["configuracion"]["destaque_min_mm"], "banda": banda}


ESFUERZOS = ("normal", "maximo")
NOMBRE_ESFUERZO = {"rapido": "rápido", "normal": "normal", "maximo": "máximo"}


def comparar_todo(carpeta: Path, catalogo: Catalogo, esfuerzos=ESFUERZOS, mostrar=print) -> list[dict]:
    filas = []
    for lote in leer(carpeta):
        nuestro = {e: calcular(lote, catalogo, "lucas", e) for e in esfuerzos}
        cotizado = calcular(lote, catalogo, "corte_certo", esfuerzos[0], medidas_de_optima=False)
        fila = {"lote": lote.lote, "material": lote.material, "piezas": sum(p["cantidad"] for p in lote.piezas),
                "optima": {"hojas": "; ".join(f"{n}×{a}×{l}" for n, a, l in lote.hojas),
                           "retazos": "; ".join(f"{n}×{a}×{l}" for n, a, l in lote.retazos),
                           "planchas": sum(n for n, _, _ in lote.hojas) + sum(n for n, _, _ in lote.retazos),
                           "m2_hojas": lote.m2_hojas, "m2_piezas": lote.m2_piezas,
                           "aprovechamiento_bruto": lote.aprovechamiento_bruto,
                           "desperdicio_real": lote.desperdicio_real},
                "nuestro": nuestro, "como_cotizacion": cotizado}
        filas.append(fila)
        mostrar(f"lote {lote.lote} {lote.material}: Optima {fila['optima']['m2_hojas']} m² de hoja; nuestro "
                + ", ".join(f"{e} {r['m2_hojas']} m² ({r['planchas']} hojas)" for e, r in nuestro.items())
                + f"; como cotización {cotizado['m2_hojas']} m²")
    return filas


def _hojas(r: dict) -> str:
    return "; ".join(f"{v}×{k.replace('x', '×')}" for k, v in sorted(r["hojas"].items(), reverse=True))


def _dif(n: float, o: float) -> str:
    return f"{n - o:+.2f} m² ({(n - o) / o * 100:+.1f} %)" if o else "—"


def markdown(filas: list[dict], carpeta: str) -> str:
    esfuerzos = list(filas[0]["nuestro"]) if filas else list(ESFUERZOS)
    lineas = [f"Datos: `{carpeta}` (5 lotes cortados en planta con Optima). Mismas piezas y mismas medidas de "
              "hoja que usó Optima; corte banda y destaque mínimo de la regla de Lucas (preset \"Reglas de corte "
              "(Lucas, como Optima)\"). El programa no sabe qué había en stock: puede usar todas las hojas que "
              "quiera de cada medida (Optima usó las que había y, en un lote, retazos). Por eso se comparan los "
              "**m² de hoja**. \"Como cotización\": \"Como Corte Certo hoy\" con la plancha por defecto del vidrio.", "",
              "| Lote | Vidrio | Piezas | Optima: hojas | Optima: m² | " +
              " | ".join(f"Nuestro ({NOMBRE_ESFUERZO[e]}): hojas | m² | diferencia" for e in esfuerzos) + " | Como cotización |",
              "|---|---|---|---|---|" + "---|---|---|" * len(esfuerzos) + "---|"]
    tot_o = 0.0
    tot = {e: 0.0 for e in esfuerzos}
    for f in filas:
        o, c = f["optima"], f["como_cotizacion"]
        tot_o += o["m2_hojas"]
        celdas = []
        for e in esfuerzos:
            n = f["nuestro"][e]
            tot[e] += n["m2_hojas"]
            celdas.append(f"{_hojas(n)} | {n['m2_hojas']:.2f} | {_dif(n['m2_hojas'], o['m2_hojas'])}")
        hojas_o = o["hojas"] + (f" + retazos {o['retazos']}" if o["retazos"] else "")
        lineas.append(f"| {f['lote']} | {f['material']} | {f['piezas']} | {hojas_o} | {o['m2_hojas']:.2f} | "
                      + " | ".join(celdas) + f" | {_hojas(c)}: {c['m2_hojas']:.2f} m² |")
    if tot_o:
        lineas += ["", f"Total: Optima {tot_o:.2f} m² de hoja; nuestro "
                   + "; ".join(f"{tot[e]:.2f} m² con esfuerzo {NOMBRE_ESFUERZO[e]} "
                               f"({(tot[e] - tot_o) / tot_o * 100:+.1f} %)"
                               for e in esfuerzos)
                   + ". Negativo = el programa usa menos vidrio."]
    no_ok = sorted({f["lote"] for f in filas for n in f["nuestro"].values() if not (n["verificado"] and n["completo"])})
    if no_ok:
        lineas.append(f"Lotes con problemas (no validados o incompletos): {', '.join(no_ok)}")
    return "\n".join(lineas)


def ejecutar(carpeta: Path, salida: Path, docs: bool = False, mostrar=print) -> list[dict]:
    from .principal import actualizar_validacion, ruta_para_docs

    catalogo = Catalogo(usar_locales=False)
    filas = comparar_todo(carpeta, catalogo, mostrar=mostrar)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    texto = markdown(filas, ruta_para_docs(carpeta))
    (salida / "resumen.md").write_text(texto + "\n", encoding="utf-8")
    if docs:
        actualizar_validacion(texto, marca="OPTIMA")
        mostrar("docs/VALIDACION.md actualizado (comparación con Optima)")
    mostrar(texto)
    return filas
