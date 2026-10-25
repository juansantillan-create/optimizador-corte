"""Exportar el consumo por material a CSV o XLSX (brief §7.4).

Una fila por material y medida de plancha: material, descripción, medida de la hoja, plancha útil,
planchas, m² de plancha útil, m² de hoja entera, montajes y aprovechamiento del material.
CSV con `;` y UTF-8 con BOM (Excel en Windows lo abre bien), punto o coma decimal.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

COLUMNAS = ["proyecto", "material", "descripcion", "hoja_ancho", "hoja_largo", "util_ancho",
            "util_largo", "supuesta", "planchas", "m2_planchas_util", "m2_hoja_entera", "montajes",
            "piezas", "m2_piezas", "aprovechamiento_material", "preset"]
# Encabezados para la planilla. Las últimas columnas son DEL MATERIAL (se repiten en cada medida de
# plancha): no hay que sumarlas.
TITULOS = {"proyecto": "Proyecto", "material": "Material", "descripcion": "Descripción",
           "hoja_ancho": "Hoja ancho (mm)", "hoja_largo": "Hoja largo (mm)", "util_ancho": "Útil ancho (mm)",
           "util_largo": "Útil largo (mm)", "supuesta": "Plancha supuesta", "planchas": "Planchas",
           "m2_planchas_util": "m² planchas (útil)", "m2_hoja_entera": "m² hoja entera",
           "montajes": "Montajes con esta plancha", "piezas": "Piezas del material (no sumar)",
           "m2_piezas": "m² piezas del material (no sumar)",
           "aprovechamiento_material": "Aprov. del material % (no sumar)", "preset": "Configuración"}


def filas_consumo(res: dict) -> list[dict]:
    filas = []
    for mat in res["materiales"]:
        if not mat["planchas_usadas"]:
            filas.append({"proyecto": res["proyecto"]["codigo"], "material": mat["codigo"],
                          "descripcion": mat["descripcion"], "planchas": 0, "montajes": 0,
                          "piezas": mat["piezas"], "m2_piezas": mat["m2_piezas"],
                          "preset": res.get("preset_nombre", "")})
            continue
        for u in mat["planchas_usadas"]:
            montajes = sum(1 for m in mat["montajes"]
                           if (m["plancha"]["ancho"], m["plancha"]["largo"]) == (u["ancho"], u["largo"]))
            filas.append({
                "proyecto": res["proyecto"]["codigo"],
                "material": mat["codigo"],
                "descripcion": mat["descripcion"],
                "hoja_ancho": u["hoja_ancho"],
                "hoja_largo": u["hoja_largo"],
                "util_ancho": u["ancho"],
                "util_largo": u["largo"],
                "supuesta": "SI" if u.get("supuesta") else "NO",
                "planchas": u["cantidad"],
                "m2_planchas_util": round(u["cantidad"] * u["ancho"] * u["largo"] / 1e6, 6),
                "m2_hoja_entera": round(u["cantidad"] * u["hoja_ancho"] * u["hoja_largo"] / 1e6, 6),
                "montajes": montajes,
                "piezas": mat["piezas"],
                "m2_piezas": mat["m2_piezas"],
                "aprovechamiento_material": mat["aprovechamiento"],
                "preset": res.get("preset_nombre", ""),
            })
    return filas


def a_csv(res: dict, coma: bool = True) -> str:
    """Con coma decimal por defecto (Excel con configuración argentina)."""
    salida = io.StringIO()
    w = csv.DictWriter(salida, fieldnames=COLUMNAS, delimiter=";", extrasaction="ignore")
    w.writerow(TITULOS)
    for fila in filas_consumo(res):
        if coma:
            fila = {k: (str(v).replace(".", ",") if isinstance(v, float) else v) for k, v in fila.items()}
        w.writerow(fila)
    return "\ufeff" + salida.getvalue()


def a_xlsx(res: dict, ruta: Path | None = None) -> bytes:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    libro = Workbook()
    hoja = libro.active
    hoja.title = "Consumo"
    hoja.append([TITULOS[c] for c in COLUMNAS])
    for celda in hoja[1]:
        celda.font = Font(bold=True)
    for fila in filas_consumo(res):
        hoja.append([fila.get(c) for c in COLUMNAS])
    for col, ancho in zip("ABCDEFGHIJKLMNOP", (12, 12, 30, 10, 10, 10, 10, 9, 9, 16, 15, 9, 8, 14, 22, 24)):
        hoja.column_dimensions[col].width = ancho
    datos = io.BytesIO()
    libro.save(datos)
    if ruta is not None:
        Path(ruta).write_bytes(datos.getvalue())
    return datos.getvalue()
