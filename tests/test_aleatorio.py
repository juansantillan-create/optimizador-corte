"""Instancias al azar: todo resultado tiene que pasar el validador independiente."""

from hypothesis import HealthCheck, given, settings, strategies as st

from optimizador.api import optimizar

pieza = st.fixed_dictionaries({
    "cantidad": st.integers(1, 6),
    "ancho": st.integers(30, 700),
    "largo": st.integers(30, 600),
    "rota": st.sampled_from([None, None, True, False]),
    "clase": st.sampled_from(["", "FLOAT PR TEMP", "FLOAT TEMP"]),
})

plancha = st.fixed_dictionaries({
    "ancho": st.integers(700, 1200),
    "largo": st.integers(500, 700),
    "corte_banda": st.sampled_from([0, 20, 30]),
})

config = st.fixed_dictionaries({
    "separacion_piezas_mm": st.sampled_from([0, 0, 5, 20]),
    "destaque_min_mm": st.sampled_from([0, 0, 10, 25]),
    "rotacion": st.booleans(),
    "textura": st.sampled_from(["sin", "sin", "sin", "horizontal", "vertical"]),
    "constante_ancho_mm": st.sampled_from([0, 0, 2]),
    "margen_arriba_mm": st.sampled_from([0, 0, 10]),
    "margen_izquierda_mm": st.sampled_from([0, 0, 15]),
})


@settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(piezas=st.lists(pieza, min_size=1, max_size=8),
       planchas=st.lists(plancha, min_size=1, max_size=2),
       cfg=config,
       esfuerzo=st.sampled_from(["rapido", "normal"]))
def test_al_azar_siempre_valido(piezas, planchas, cfg, esfuerzo):
    for i, p in enumerate(piezas, start=1):
        p["item"] = str(i)
        p["material"] = "FL5IN"
    ajustes = dict(cfg)
    ajustes["planchas"] = planchas
    ent = {"proyecto": {"codigo": "AZ", "descripcion": "al azar"}, "piezas": piezas,
           "materiales": {"FL5IN": ajustes}, "opciones": {"esfuerzo": esfuerzo},
           "fecha": "2026-10-25 00:00:00"}
    res = optimizar(ent)
    assert res["verificado"], res["validacion"]
    m = res["materiales"][0]
    # Todo lo que no dio error se colocó.
    if m["planchas"]:
        assert m["planchas"] >= m["minimo_teorico_planchas"] or len(planchas) > 1
