"""El validador tiene que aceptar un resultado bueno y rechazar cada tipo de error."""

import copy

import pytest

from optimizador.api import optimizar
from optimizador.validador import _es_guillotina, validar


def _entrada():
    return {
        "proyecto": {"codigo": "T1", "descripcion": "test"},
        "piezas": [
            {"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 1150, "largo": 2400},
            {"item": "2", "material": "FL5IN", "cantidad": 4, "ancho": 800, "largo": 600},
        ],
        "opciones": {"esfuerzo": "rapido"},
        "fecha": "2026-10-25 00:00:00",
    }


@pytest.fixture(scope="module")
def bueno():
    ent = _entrada()
    res = optimizar(ent)
    assert res["verificado"], res["validacion"]
    return ent, res


def test_resultado_bueno_pasa(bueno):
    ent, res = bueno
    assert validar(ent, res) == []


def _primera_pieza(res):
    return res["materiales"][0]["montajes"][0]["piezas"][0]


def test_pieza_afuera(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    _primera_pieza(r)["x"] = 3000
    errores = validar(ent, r)
    assert any("se sale" in e for e in errores)


def test_solape(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    piezas = r["materiales"][0]["montajes"][0]["piezas"]
    piezas[1]["x"], piezas[1]["y"] = piezas[0]["x"] + 10, piezas[0]["y"] + 10
    assert any("solapan" in e for e in validar(ent, r))


def test_pieza_de_mas(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    r["materiales"][0]["montajes"][0]["repeticiones"] += 1
    errores = validar(ent, r)
    assert any("se colocaron" in e for e in errores)
    assert any("planchas informado" in e for e in errores)


def test_medida_cambiada(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    pz = _primera_pieza(r)
    pz["ancho"] -= 1
    assert any("no coinciden con las pedidas" in e for e in validar(ent, r))


def test_numeros_del_informe(bueno):
    ent, res = bueno
    for campo, delta in (("m2_piezas", 0.001), ("aprovechamiento", 0.01), ("perdida", 0.01),
                         ("m2_planchas", 0.01), ("perimetro_m", 0.01)):
        r = copy.deepcopy(res)
        r["materiales"][0][campo] += delta
        assert validar(ent, r), campo


def test_girada_sin_rotacion(bueno):
    ent, res = bueno
    ent2 = copy.deepcopy(ent)
    for p in ent2["piezas"]:
        p["rota"] = False
    r = copy.deepcopy(res)
    girada = any(p["girada"] for m in r["materiales"][0]["montajes"] for p in m["piezas"])
    if girada:
        assert validar(ent2, r)


def test_separacion_no_respetada(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    r["materiales"][0]["configuracion"]["separacion_piezas_mm"] = 20
    # Las piezas que se tocan ya no cumplen la separación (o la plancha deja de ser cortable).
    assert validar(ent, r)


def test_plancha_que_no_existe(bueno):
    ent, res = bueno
    r = copy.deepcopy(res)
    r["materiales"][0]["montajes"][0]["plancha"]["ancho"] = 3600
    assert any("no corresponde" in e for e in validar(ent, r))


def test_molinete_no_es_guillotina():
    # El "molinete": 4 piezas alrededor de una central; no se puede cortar de lado a lado.
    rects = [(0, 0, 200, 100), (200, 0, 100, 200), (100, 200, 200, 100), (0, 100, 100, 200),
             (100, 100, 100, 100)]
    ok, motivo = _es_guillotina(rects, 300, 300, 0)
    assert not ok and "guillotina" in motivo


def test_guillotina_y_destaque():
    rects = [(0, 0, 100, 100), (100, 0, 95, 100)]
    assert _es_guillotina(rects, 200, 100, 0)[0]
    # Sobra una tira de 5 mm a la derecha: con destaque 10 no se puede separar.
    ok, motivo = _es_guillotina(rects, 200, 100, 10)
    assert not ok and "destaque" in motivo
    assert _es_guillotina(rects, 195, 100, 10)[0]
