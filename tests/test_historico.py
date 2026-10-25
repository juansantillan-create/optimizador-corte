"""Validación histórica (F4) de punta a punta con el caso de juguete (todo inventado)."""

import json
from pathlib import Path

import pytest

from optimizador.configuracion import Catalogo
from optimizador.historico import comparar, datos, leyendas, principal, reconstruir

JUGUETE = Path(__file__).parent / "historico_juguete"


def test_leyenda_formato_real():
    ley = leyendas.leer("LISTA 1\n4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10%\n"
                        "3+3 LOWE: 105 HOJAS - 72% ******* L.DIST -10%\n"
                        "4+4 LOWE_ 22 HOJAS - 64%******* L.DIST -10%\n"
                        "FL 10 INC 3 hojas 85,5 %\ndolar 1450\nquedan 3 hojas aprox")
    assert ley.lista == "LISTA 1"
    assert [(l.material, l.hojas, l.aprovechamiento) for l in ley.lineas] == [
        ("4+4 NLIGHT", 88, 91.0), ("3+3 LOWE", 105, 72.0), ("4+4 LOWE", 22, 64.0), ("FL 10 INC", 3, 85.5)]
    assert ley.lineas[0].cotizacion == "L.DIST -10%"
    assert ley.no_leidas == ["quedan 3 hojas aprox"]


def test_leyenda_saltos_escapados_y_columnas():
    ley = leyendas.buscar({"numero": "1", "tv_descrip": "dolar 1450",
                           "observaciones": "5 INC: 3 HOJAS - 76%\\n4 INC: 1 HOJAS - 50%"})
    assert ley.columna == "observaciones" and len(ley.lineas) == 2


def test_relacionar():
    cat = Catalogo(usar_locales=False)
    assert comparar.relacionar("4+4 NLIGHT", ["LX4+4NL", "LX3+3LOW"], cat)[0] == "LX4+4NL"
    assert comparar.relacionar("3+3 LOWE", ["LX4+4NL", "LX3+3LOW"], cat)[0] == "LX3+3LOW"
    assert comparar.relacionar("4+4 LOWE", ["LX4+4LOWE", "LX4+4NL"], cat)[0] == "LX4+4LOWE"
    codigo, motivo = comparar.relacionar("3+3", ["LX3+3IN", "LX3+3BC"], cat)
    assert codigo is None and "ambiguo" in motivo
    assert comparar.relacionar("5 INC", ["FL5IN"], cat)[0] == "FL5IN"


def test_reconstruir_dvh_herrajes_y_sin_duplicar():
    casos = datos.leer(JUGUETE)
    assert not casos.diferencias
    cat = Catalogo(usar_locales=False)
    rec = reconstruir.reconstruir(casos, "900002", set(cat.materiales))
    assert sorted(p["material"] for p in rec.piezas) == ["FL4IN", "FL5IN"]  # DVH = 2 vidrios
    assert all(p["cantidad"] == 6 for p in rec.piezas)
    assert {e["codigo"] for e in rec.excluidos} == {"HERR01", "FLETE"}
    # Un artículo en varios renglones: las piezas de DETPRES2 se cuentan una sola vez.
    for numero in casos.presupuestos:
        rec = reconstruir.reconstruir(casos, numero, set(cat.materiales))
        for codigo in rec.materiales():
            d2 = sum(int(p["v_cantialt"]) for p in casos.piezas.get(numero, []) if p["v_codart"] == codigo)
            if d2:
                assert sum(p["cantidad"] for p in rec.piezas if p["material"] == codigo) == d2


def test_reparto_70_30_fijo():
    n = [str(900000 + i) for i in range(1000)]
    calib = sum(comparar.es_calibracion(x) for x in n)
    assert 650 < calib < 750
    assert [comparar.es_calibracion(x) for x in n[:20]] == [comparar.es_calibracion(x) for x in n[:20]]


@pytest.fixture(scope="module")
def corrida(tmp_path_factory):
    salida = tmp_path_factory.mktemp("historico")
    res = principal.ejecutar(JUGUETE, salida, comparar.Opciones(esfuerzo="rapido", muestra=None),
                             mostrar=lambda *a: None)
    return salida, res


def test_de_punta_a_punta(corrida):
    salida, res = corrida
    c = res["cobertura"]
    assert c["presupuestos"] == 19 and c["leidos"] == 17
    assert len(c["no_leidas"]) == 1 and c["no_leidas"][0]["numero"] == "900004"
    assert len(c["sin_relacionar"]) == 1 and c["sin_relacionar"][0]["numero"] == "900007"
    assert len(c["no_cierran"]) == 1 and c["no_cierran"][0]["numero"] == "900005"
    assert res["prueba"]["total"]["casos"] > 0
    assert all(g["hipotesis"] in ("H0", "H1", "H2") for g in res["eleccion"].values())
    pagina = (salida / "revision.html").read_text(encoding="utf-8")
    assert "Copiar mis respuestas" in pagina and "<svg" in pagina and "http" not in pagina.replace("http://www.w3.org/2000/svg", "")
    assert (salida / "resumen.md").read_text(encoding="utf-8").startswith("Datos:")


def test_retoma_sin_recalcular(corrida):
    salida, _ = corrida
    jsonl = salida / "resultados_rapido.jsonl"
    antes = jsonl.read_text(encoding="utf-8").count("\n")
    principal.ejecutar(JUGUETE, salida, comparar.Opciones(esfuerzo="rapido", muestra=None), mostrar=lambda *a: None)
    assert jsonl.read_text(encoding="utf-8").count("\n") == antes


def test_actualizar_validacion(tmp_path):
    ruta = tmp_path / "VALIDACION.md"
    ruta.write_text("# V\n\n## 1. Contra Corte Certo (casos históricos)\n\nviejo\n\n## 2. Otro\n", encoding="utf-8")
    principal.actualizar_validacion("NUEVO 1", ruta)
    principal.actualizar_validacion("NUEVO 2", ruta)
    texto = ruta.read_text(encoding="utf-8")
    assert "NUEVO 2" in texto and "NUEVO 1" not in texto and "## 2. Otro" in texto
