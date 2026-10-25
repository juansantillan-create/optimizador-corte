"""Controles mínimos del repo (fase F0)."""

import csv
from pathlib import Path

import optimizador

RAIZ = Path(__file__).resolve().parents[1]


def test_version():
    assert optimizador.__version__


def test_hojas_csv_tiene_las_101_medidas():
    with (RAIZ / "config" / "hojas.csv").open(encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    assert len(filas) == 101
    assert len({f["codigo"] for f in filas}) == 87
    for f in filas:
        assert int(f["util_ancho_mm"]) == int(f["hoja_ancho_mm"]) - int(f["corte_banda_mm"])
        assert int(f["hoja_ancho_mm"]) >= int(f["hoja_largo_mm"])
