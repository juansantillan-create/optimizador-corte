"""Casos borde del brief §6.6, más las fórmulas del informe."""

from optimizador.api import optimizar

FECHA = "2026-10-25 00:00:00"


def calcular(piezas, preset="corte_certo", materiales=None, esfuerzo="rapido"):
    ent = {"proyecto": {"codigo": "T", "descripcion": "test"}, "preset": preset, "piezas": piezas,
           "materiales": materiales or {}, "opciones": {"esfuerzo": esfuerzo}, "fecha": FECHA}
    res = optimizar(ent)
    assert res["verificado"], res["validacion"]
    return res


def material(res, codigo):
    return next(m for m in res["materiales"] if m["codigo"] == codigo)


def test_pieza_que_no_entra():
    res = calcular([{"item": "7", "material": "FL10IN", "cantidad": 1, "ancho": 3700, "largo": 2600},
                    {"item": "8", "material": "FL10IN", "cantidad": 2, "ancho": 1000, "largo": 1000}])
    m = material(res, "FL10IN")
    assert any("ítem 7" in e and "no entra en ninguna plancha de FL10IN" in e and "3700 × 2600" in e
               for e in m["errores"])
    assert m["piezas"] == 2 and m["planchas"] == 1


def test_entra_solo_girada_sin_rotacion():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 1, "ancho": 2000, "largo": 3000}],
                   materiales={"FL5IN": {"rotacion": False}})
    m = material(res, "FL5IN")
    assert any("entraría girada" in e for e in m["errores"])
    assert m["planchas"] == 0


def test_cantidad_y_medidas_invalidas():
    res = calcular([
        {"item": "1", "material": "FL5IN", "cantidad": 0, "ancho": 500, "largo": 500},
        {"item": "2", "material": "FL5IN", "cantidad": 2, "ancho": 0, "largo": 500},
        {"item": "3", "material": "FL5IN", "cantidad": 2, "ancho": -5, "largo": 500},
        {"item": "4", "material": "", "cantidad": 2, "ancho": 500, "largo": 500},
        {"item": "5", "material": "FL5IN", "cantidad": "dos", "ancho": 500, "largo": 500},
        {"item": "6", "material": "FL5IN", "cantidad": 2, "ancho": 500, "largo": 500},
    ])
    errores = " | ".join(res["errores"])
    for item in ("ítem 1", "ítem 2", "ítem 3", "ítem 4", "ítem 5"):
        assert item in errores
    assert material(res, "FL5IN")["piezas"] == 2


def test_material_desconocido_con_espesor():
    res = calcular([{"item": "1", "material": "FL8BR", "cantidad": 2, "ancho": 1000, "largo": 1000}])
    m = material(res, "FL8BR")
    assert any("SUPUESTA" in a for a in m["avisos"])
    assert m["planchas_usadas"][0]["supuesta"] is True
    assert m["planchas_usadas"][0]["ancho"] == 3580  # como Corte Certo: banda 20 en todos los vidrios
    m = material(calcular([{"item": "1", "material": "FL8BR", "cantidad": 2, "ancho": 1000, "largo": 1000}],
                          preset="lucas"), "FL8BR")
    assert m["planchas_usadas"][0]["ancho"] == 3570  # regla de Lucas: banda de 8 mm (30)


def test_material_sin_planchas_no_frena_a_los_demas():
    res = calcular([{"item": "1", "material": "XYZ", "cantidad": 2, "ancho": 1000, "largo": 1000},
                    {"item": "2", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 1000}])
    assert any("no tiene planchas" in e for e in material(res, "XYZ")["errores"])
    assert material(res, "FL5IN")["planchas"] == 1


def test_pieza_igual_a_la_plancha_util():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 3580, "largo": 2500}])
    m = material(res, "FL5IN")
    assert m["planchas"] == 3 and m["layouts"] == 1 and m["aprovechamiento"] == 100.0


def test_muchas_piezas_iguales():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 300, "ancho": 500, "largo": 500}],
                   esfuerzo="normal")
    m = material(res, "FL5IN")
    # 7 × 5 = 35 por plancha (3500 × 2500 de 3580 × 2500): 300 / 35 -> 9 planchas
    assert m["planchas"] == 9
    assert m["minimo_teorico_planchas"] <= 9


def test_separacion_que_llena_justo():
    # 3 piezas de 1180 con 20 de separación: 3·1180 + 2·20 = 3580 (justo). Alto: 2500.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 1180, "largo": 2500}],
                   materiales={"FL5IN": {"separacion_piezas_mm": 20}})
    m = material(res, "FL5IN")
    assert m["configuracion"]["separacion_piezas_mm"] == 20
    assert m["planchas"] == 1


def test_separacion_que_no_entra():
    # Con 1181 ya no entran 3 en una plancha.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 1181, "largo": 2500}],
                   materiales={"FL5IN": {"separacion_piezas_mm": 20}})
    assert material(res, "FL5IN")["planchas"] == 2


def test_preset_de_lucas_usa_destaque_y_no_separacion():
    # Juan, 25/10/2026 (pregunta 2): la distancia de la regla es el destaque mínimo, no una separación.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 1180, "largo": 2500}],
                   preset="lucas")
    conf = material(res, "FL5IN")["configuracion"]
    assert conf["separacion_piezas_mm"] == 0 and conf["destaque_min_mm"] == 20


def test_piezas_mas_chicas_que_el_destaque():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 4, "ancho": 15, "largo": 800},
                    {"item": "2", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 1000}],
                   materiales={"FL5IN": {"destaque_min_mm": 20}})
    m = material(res, "FL5IN")
    assert any("menos que el destaque" in a for a in m["avisos"])
    assert m["piezas"] == 6


def test_varias_medidas_de_plancha():
    # FL4IN tiene 3600×2500, 3600×2200 y 3300×2440. Por defecto se cotiza solo con la de 3600 × 2500
    # (Juan, 25/10/2026). Con las otras habilitadas, una pieza de 3500 × 2100 entra en las dos
    # primeras y tiene que elegir la de menos m² (3580 × 2200).
    pieza = [{"item": "1", "material": "FL4IN", "cantidad": 2, "ancho": 3500, "largo": 2100}]
    m = material(calcular(pieza), "FL4IN")
    assert {(p["ancho"], p["largo"]) for p in m["planchas_usadas"]} == {(3580, 2500)}
    todas = {"FL4IN": {"planchas_habilitadas": {"3600x2200": True, "3300x2440": True}}}
    m = material(calcular(pieza, materiales=todas), "FL4IN")
    assert m["planchas"] == 2
    assert {(p["ancho"], p["largo"]) for p in m["planchas_usadas"]} == {(3580, 2200)}


def test_deshabilitar_una_medida():
    res = calcular([{"item": "1", "material": "FL4IN", "cantidad": 2, "ancho": 3500, "largo": 2100}],
                   materiales={"FL4IN": {"planchas_habilitadas": {"3600x2200": False}}})
    m = material(res, "FL4IN")
    assert {(p["ancho"], p["largo"]) for p in m["planchas_usadas"]} == {(3580, 2500)}


def test_pulido_recto_suma_3_mm():
    # 3 piezas de 1190 × 2497 con pulido recto: cortan 1193 × 2500 -> 3·1193 = 3579 <= 3580.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 3, "ancho": 1190, "largo": 2497,
                     "clase": "FLOAT PR TEMP"}])
    m = material(res, "FL5IN")
    assert m["planchas"] == 1
    assert m["tipos"][0]["ancho_corte"] == 1193 and m["tipos"][0]["largo_corte"] == 2500
    # 3578 + 3 = 3581 > 3580: con pulido recto ya no entra (ni girada); sin pulido, sí.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 1, "ancho": 3578, "largo": 1000,
                     "clase": "FLOAT PR TEMP"}])
    assert any("3581 × 1003" in e for e in material(res, "FL5IN")["errores"])
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 1, "ancho": 3578, "largo": 1000,
                     "clase": "FLOAT TEMP"}])
    assert material(res, "FL5IN")["planchas"] == 1


def test_textura_no_gira():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 2000, "largo": 1000}],
                   materiales={"FL5IN": {"textura": "vertical"}})
    m = material(res, "FL5IN")
    for mont in m["montajes"]:
        for p in mont["piezas"]:
            assert (p["ancho"], p["largo"]) == (2000, 1000)


def test_formulas_del_informe_como_corte_certo():
    # 2 piezas de 3580 × 2500 y 1 de 1000 × 1000: 2 + 1 = 3 planchas de 3580 × 2500.
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 3580, "largo": 2500},
                    {"item": "2", "material": "FL5IN", "cantidad": 1, "ancho": 1000, "largo": 1000}])
    m = material(res, "FL5IN")
    assert m["m2_piezas"] == 18.9
    assert m["m2_planchas"] == 26.85
    assert m["aprovechamiento"] == round(18.9 / 26.85 * 100, 2) == 70.39
    assert m["perdida"] == 29.61
    assert m["perimetro_m"] == round((2 * 2 * (3580 + 2500) + 2 * 2000) / 1000, 2)
    assert m["planchas_usadas"] == [{"cantidad": 3, "ancho": 3580, "largo": 2500, "tipo": "Plancha",
                                     "hoja_ancho": 3600, "hoja_largo": 2500, "supuesta": False}]


def test_cuentas_del_caso_413():
    # Las cuentas de la captura 1: 82 planchas de 3580 × 2500 y 564,583068 m² de piezas.
    m2_planchas = 82 * 3580 * 2500 / 1e6
    assert m2_planchas == 733.9
    assert round(564.583068 / m2_planchas * 100, 2) == 76.93
    assert round(100 - 76.93, 2) == 23.07


def test_reproducible():
    piezas = [{"item": str(i), "material": "FL5IN", "cantidad": 1 + i % 4, "ancho": 300 + 97 * i,
               "largo": 400 + 53 * i} for i in range(1, 15)]
    a = calcular(piezas, esfuerzo="normal")
    b = calcular(piezas, esfuerzo="normal")
    for m in (a, b):
        for mat in m["materiales"]:
            mat.pop("calculo", None)
    assert a == b


def test_nunca_mas_piezas_que_las_pedidas():
    # Regresión (revisor F2): con 1000 × 700 entran 11 mezclando orientaciones y la caché del
    # generador reusaba ese montaje para una cota menor.
    for cantidad in (9, 10, 11, 13, 20, 21, 22):
        for esfuerzo in ("rapido", "normal"):
            res = calcular([{"item": "1", "material": "FL5IN", "cantidad": cantidad, "ancho": 1000, "largo": 700}],
                           esfuerzo=esfuerzo)
            assert material(res, "FL5IN")["piezas"] == cantidad


def test_generador_respeta_cotas_con_cache():
    import random

    from optimizador.motor import arbol
    from optimizador.motor.generador import Generador, TipoGen

    r = random.Random(3)
    for _ in range(30):
        tipos = [TipoGen(((a, b), (b, a))) for a, b in
                 [(r.randint(200, 1500), r.randint(200, 1500)) for _ in range(r.randint(1, 4))]]
        g = Generador(3580, 2500, tipos, 0)
        valores = [float(r.randint(1, 5)) for _ in tipos]
        for _ in range(6):  # varias llamadas seguidas: la caché se reusa
            cotas = [r.randint(0, 25) for _ in tipos]
            for nodo in g.generar(valores, cotas):
                usadas = arbol.contar(nodo)
                assert all(usadas.get(i, 0) <= c for i, c in enumerate(cotas)), (cotas, usadas)


def test_maximo_tamano_cortado_avisa():
    piezas = [{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 1500, "largo": 2500}]
    res = calcular(piezas, materiales={"FL5IN": {"corte_max_libre": False, "corte_max_mm": 2000}})
    assert any("máximo tamaño cortado" in a for a in material(res, "FL5IN")["avisos"])
    res = calcular(piezas)
    assert not any("máximo tamaño cortado" in a for a in material(res, "FL5IN")["avisos"])


# ------------------------------------------------ lo que encontró la revisión de F1
def test_configuracion_imposible_no_se_calcula():
    piezas = [{"item": "1", "material": "FL4IN", "cantidad": 3, "ancho": 1200, "largo": 2500}]
    for ajuste in ({"separacion_piezas_mm": -10}, {"margen_derecha_mm": -40}, {"textura": "diagonal"},
                   {"destaque_min_mm": "x"}, {"planchas": [{"ancho": 3600, "largo": 2500, "corte_banda": -5}]}):
        res = calcular(piezas, materiales={"FL4IN": ajuste})
        m = material(res, "FL4IN")
        assert m["planchas"] == 0 and any("no se calcula este material" in e for e in m["errores"]), ajuste


def test_textura_como_la_escribe_corte_certo():
    piezas = [{"item": "1", "material": "FL4IN", "cantidad": 2, "ancho": 1700, "largo": 2400}]
    sin = material(calcular(piezas, materiales={"FL4IN": {"textura": "Sem"}}), "FL4IN")
    assert sin["configuracion"]["textura"] == "sin" and sin["planchas"] == 1
    hor = material(calcular(piezas, materiales={"FL4IN": {"textura": "Horizontal"}}), "FL4IN")
    assert hor["configuracion"]["textura"] == "horizontal"


def test_ajustes_en_minuscula_y_de_materiales_que_no_estan():
    piezas = [{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 1000}]
    res = calcular(piezas, materiales={"fl5in": {"separacion_piezas_mm": 7}, "FL8IN": {"rotacion": False}})
    assert material(res, "FL5IN")["configuracion"]["separacion_piezas_mm"] == 7
    assert any("FL8IN" in a and "ninguna pieza" in a for a in res["avisos"])


def test_punto_de_miles_en_la_entrada():
    res = calcular([{"item": "1", "material": "FL4IN", "cantidad": 2, "ancho": "1.200", "largo": "800"}])
    m = material(res, "FL4IN")
    assert m["tipos"][0]["ancho"] == 1200 and m["m2_piezas"] == 1.92


def test_validador_compara_con_la_configuracion_de_la_entrada():
    from optimizador.configuracion import Catalogo
    from optimizador.validador import validar
    ent = {"preset": "corte_certo", "fecha": FECHA, "opciones": {"esfuerzo": "rapido"},
           "piezas": [{"item": "1", "material": "FL4IN", "cantidad": 3, "ancho": 1200, "largo": 2500}],
           "materiales": {"FL4IN": {"separacion_piezas_mm": 10}}}
    res = optimizar(ent)
    assert res["verificado"]
    cat = Catalogo()
    m = material(res, "FL4IN")
    m["configuracion"]["separacion_piezas_mm"] = 0  # el resultado "dice" que usó otra separación
    assert any("separacion_piezas_mm" in e for e in validar(ent, res, cat))
    m["configuracion"]["separacion_piezas_mm"] = -10
    assert any("no es una medida válida" in e for e in validar(ent, res))


def test_caso_grande_que_ponia_piezas_de_mas():
    # Revisión de F1: este presupuesto típico daba 303 piezas de 300 (el validador lo atajaba).
    from optimizador.banco import caso_realista
    ent = caso_realista(4020, 30, 300, 300, 2400)
    ent["opciones"] = {"esfuerzo": "normal"}
    res = optimizar(ent)
    assert res["verificado"], res["validacion"][:3]
    assert res["completo"] and res["materiales"][0]["piezas"] == 300


def test_resultado_incompleto_se_marca():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 1, "ancho": 5000, "largo": 500},
                    {"item": "2", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 500}])
    assert res["completo"] is False and material(res, "FL5IN")["planchas"] == 1
    assert calcular([{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 500}])["completo"]


def test_cancelar_antes_del_primer_montaje():
    piezas = [{"item": str(i), "material": "FL4IN", "cantidad": 1, "ancho": 300 + 7 * i, "largo": 400 + 5 * i}
              for i in range(80)]
    ent = {"piezas": piezas, "opciones": {"esfuerzo": "normal"}, "fecha": FECHA}
    res = optimizar(ent, cancelar=lambda: True)
    m = material(res, "FL4IN")
    assert res["verificado"] and not res["completo"] and m["planchas"] == 0
    assert any("cancelado" in e for e in m["errores"])


def test_veta_no_marca_piezas_giradas():
    res = calcular([{"item": "1", "material": "FL4IN", "cantidad": 2, "ancho": 800, "largo": 1500}],
                   materiales={"FL4IN": {"textura": "horizontal"}})
    assert not any(p["girada"] for mo in material(res, "FL4IN")["montajes"] for p in mo["piezas"])


# ------------------------------------------------ lo que encontró la revisión de F5
def test_plancha_inservible_es_aviso_si_hay_otras():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 500}],
                   materiales={"FL5IN": {"planchas": [{"ancho": 3600, "largo": 2500, "corte_banda": 20},
                                                      {"ancho": 300, "largo": 200, "corte_banda": 400}]}})
    m = material(res, "FL5IN")
    assert res["completo"] and m["planchas"] == 1 and any("sin medida útil" in a for a in m["avisos"])


def test_pulido_recto_no_y_planchas_con_punto_de_miles():
    res = calcular([{"item": "1", "material": "FL5IN", "cantidad": 1, "ancho": 1000, "largo": 500,
                     "pulido_recto": "no"}],
                   materiales={"FL5IN": {"planchas": [{"ancho": "3.600", "largo": "2.500", "corte_banda": 20}]}})
    m = material(res, "FL5IN")
    assert m["m2_piezas"] == 0.5 and m["configuracion"]["planchas"][0]["ancho"] == 3600


def test_muchisimas_medidas_en_maximo_no_hace_columnas():
    from optimizador.motor import calculo
    piezas = [{"item": str(i), "material": "FL5IN", "cantidad": 1, "ancho": 200 + i, "largo": 300 + (7 * i) % 500}
              for i in range(calculo.MAX_TIPOS_COLUMNAS + 1)]
    res = optimizar({"piezas": piezas, "opciones": {"esfuerzo": "maximo"}, "fecha": FECHA})
    m = material(res, "FL5IN")
    assert res["verificado"] and res["completo"]
    assert any("solo la heurística" in a for a in m["avisos"])


def test_hipotesis_de_la_validacion_con_la_misma_plancha():
    # H0, H1 y H2 cambian solo la separación: la plancha útil es la misma (la de Corte Certo).
    from optimizador.configuracion import Catalogo

    cat = Catalogo(usar_locales=False)
    utiles = {h: [(p.ancho - p.corte_banda, p.largo) for p in cat.material("LX5+5IN", h, usar_locales=False).planchas]
              for h in ("H0", "H1", "H2")}
    assert utiles["H0"] == utiles["H1"] == utiles["H2"]
