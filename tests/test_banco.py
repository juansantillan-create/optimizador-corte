"""Algunos casos del banco sintético: no pueden empeorar respecto de lo guardado como esperado
(tests/banco/esperado.json). El banco entero se corre con `python -m optimizador banco`."""

import json
from pathlib import Path

import pytest

from optimizador.api import optimizar
from optimizador.configuracion import Catalogo

CARPETA = Path(__file__).parent / "banco"
RAPIDOS = ["CP3-1001", "CP3-1002", "CP3-1003", "CP3-1010", "CPL-1037", "RE-2000", "RE-2001",
           "RE-2008", "T413-3001"]


@pytest.fixture(scope="module")
def esperado():
    return {c["caso"]: c for c in json.loads((CARPETA / "esperado.json").read_text(encoding="utf-8"))["casos"]}


@pytest.mark.parametrize("caso", RAPIDOS)
def test_no_empeora(caso, esperado):
    datos = json.loads((CARPETA / f"{caso}.json").read_text(encoding="utf-8"))
    datos["opciones"] = {"esfuerzo": "normal"}
    res = optimizar(datos, catalogo=Catalogo(usar_locales=False))
    assert res["verificado"], res["validacion"]
    m = res["materiales"][0]
    assert m["planchas"] <= esperado[caso]["planchas"]
    if datos["banco"].get("optimo"):
        assert m["planchas"] >= datos["banco"]["optimo"]
