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
    resumen = (salida / "resumen.md").read_text(encoding="utf-8")
    assert resumen.startswith("> **DATOS INVENTADOS**") and "Datos:" in resumen


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


# ------------------------------------------------- casos armados para lo que encontró la revisión de F4
def _casos(presupuestos, renglones=(), piezas=(), articulos=()):
    c = datos.Casos(origen="prueba")
    for p in presupuestos:
        c.presupuestos[p["numero"]] = p
    for r in renglones:
        c.renglones.setdefault(r["numero"], []).append(r)
    for p in piezas:
        c.piezas.setdefault(p["numero"], []).append(p)
    for a in articulos:
        c.articulos[a["codigo"].upper()] = a
    return c


def _renglon(numero, codigo, largo, ancho, canti, cantialt, clase="", familia="FLOAT", **extra):
    return {"numero": numero, "v_codart": codigo, "familia": familia, "art1": "", "art2": "", "art3": "",
            "claseart1": "", "claseart3": "", "clase": clase, "largo": str(largo), "ancho": str(ancho),
            "v_canti": str(canti), "v_cantialt": str(cantialt), "detalle": "", **extra}


def _pieza(numero, codigo, largo, ancho, cantialt, clase=""):
    return {"numero": numero, "v_codart": codigo, "clase": clase, "largo": str(largo), "ancho": str(ancho),
            "v_canti": str(round(cantialt * largo * ancho / 1e6, 3)), "v_cantialt": str(cantialt)}


def test_leyenda_dos_materiales_en_una_linea_y_lineas_raras():
    for texto in ("4+4 NLIGHT: 88 HOJAS - 91% / 3+3 LOWE: 105 HOJAS - 72%",
                  "4+4 NLIGHT: 88 HOJAS - 91% ******* 3+3 LOWE: 105 HOJAS - 72%",
                  "4+4 NLIGHT: 88 HOJAS - 91% 3+3 LOWE: 105 HOJAS - 72%",
                  "LISTA 1 / 4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10% / 3+3 LOWE: 105 HOJAS - 72%"):
        ley = leyendas.leer(texto)
        assert [l.material for l in ley.lineas] == ["4+4 NLIGHT", "3+3 LOWE"], texto
    ley = leyendas.leer("5 INC: 2 HOJAS - 56%\n4 INC 2 HOJAS 45 por ciento hojas")
    assert len(ley.lineas) == 1 and len(ley.no_leidas) == 1  # lo que no se entiende se cuenta
    ley = leyendas.leer("TOTAL: 2 HOJAS - 56%\n5 INC: 2 HOJAS - 56%")
    assert [l.material for l in ley.lineas] == ["5 INC"] and ley.ignoradas
    assert not leyendas.leer("5 INC: 3 HOJAS - 32% DESPERDICIO").lineas
    assert not leyendas.leer("5 INC 1.5 HOJAS - 40%").lineas
    ley = leyendas.leer("LISTA 1 5 INC: 2 HOJAS - 56%")
    assert ley.lista == "LISTA 1" and ley.lineas[0].material == "5 INC"
    assert leyendas.leer("4+4 NL/LOWE: 10 HOJAS - 80%").lineas[0].material == "4+4 NL/LOWE"


def test_relacionar_mira_el_color_aunque_la_composicion_sea_unica():
    cat = Catalogo(usar_locales=False)
    assert comparar.relacionar("4 GRIS", ["FL4IN", "FL5GR"], cat)[0] is None
    assert comparar.relacionar("6 OPACID", ["OA8IN", "FL6IN"], cat)[0] is None
    assert comparar.relacionar("5 INC TEMP", ["FL5IN"], cat)[0] == "FL5IN"
    assert comparar.relacionar("10", ["FL10IN"], cat)[0] == "FL10IN"


def test_control_con_mas3_y_tolerancia_redondeo_o_truncado():
    cat = Catalogo(usar_locales=False)
    # FL10IN, 1 hoja de 3680 × 2500 útil (banda 20, como Corte Certo): 48,57 % se pudo escribir 49
    # (redondeado) o 48 (truncado),
    # según el comercial (Juan, pregunta 24); 47 o 50, no.
    lado = int((0.4857 * 3680 * 2500) ** 0.5)
    piezas = [{"material": "FL10IN", "cantidad": 1, "ancho": lado, "largo": lado, "clase": ""}]
    for leyenda, cierra in ((47, False), (48, True), (49, True), (50, False)):
        assert (comparar.control_entrada(piezas, "FL10IN", 1, leyenda, cat)["plancha"] == "3700x2500") is cierra
    # Con pulido recto: si la leyenda solo cierra sin el +3, se compara igual, sin el +3 (pregunta 25).
    pr = [{"material": "FL5IN", "cantidad": 100, "ancho": 197, "largo": 297, "clase": "FLOAT PR TEMP"}]
    sin = 100 * 197 * 297 / (3580 * 2500) * 100
    con = 100 * 200 * 300 / (3580 * 2500) * 100
    assert round(con) - round(sin) >= 2
    r = comparar.control_entrada(pr, "FL5IN", 1, round(sin), cat)
    assert r["plancha"] == "3600x2500" and r["cierra_sin_mas3"] and r["con_pulido"] is False
    r = comparar.control_entrada(pr, "FL5IN", 1, round(con), cat)
    assert r["plancha"] == "3600x2500" and r["con_pulido"] is True


def test_control_plancha_ambigua_supuesta_y_piezas_que_no_entran():
    cat = Catalogo(usar_locales=False)
    # FL4IN 2,4 m² en 1 hoja: 3300×2440 da 29,99 % y 3600×2200 da 30,47 %; las dos cierran con 30 %.
    piezas = [{"material": "FL4IN", "cantidad": 1, "ancho": 1600, "largo": 1500, "clase": ""}]
    r = comparar.control_entrada(piezas, "FL4IN", 1, 30, cat)
    assert r["plancha"] and r["ambigua"]
    r = comparar.control_entrada([{"material": "FL6XX", "cantidad": 1, "ancho": 3000, "largo": 2000,
                                   "clase": ""}], "FL6XX", 1, round(6e6 / (3580 * 2500) * 100), cat)
    assert r["plancha"] and r["supuesta"]
    r = comparar.control_entrada([{"material": "FL5IN", "cantidad": 1, "ancho": 4000, "largo": 2600,
                                   "clase": ""}], "FL5IN", 2, 58, cat)
    assert r["plancha"] is None and r["no_entran"]


def test_reconstruir_avisa_lo_dudoso_y_no_cuenta_dos_veces():
    cat = set(Catalogo(usar_locales=False).materiales)
    # Un vidrio en dos renglones, uno con piezas en DETPRES2 y otro sin: aviso.
    c = _casos([{"numero": "1"}],
               [_renglon("1", "FL5IN", 1000, 500, 1.5, 3), _renglon("1", "FL5IN", 800, 600, 0.96, 2)],
               [_pieza("1", "FL5IN", 1000, 500, 3)])
    rec = reconstruir.reconstruir(c, "1", cat)
    assert rec.avisos_material.get("FL5IN")
    # El mismo DVH en dos renglones, uno sin DETPRES2: aviso por las unidades.
    dvh = dict(familia="XDVH", art1="FL4IN", art3="FL5IN")
    c = _casos([{"numero": "2"}],
               [{**_renglon("2", "DVH4-12-5", 900, 600, 4, 0), **dvh},
                {**_renglon("2", "DVH4-12-5", 700, 500, 5, 0), **dvh}],
               [_pieza("2", "DVH4-12-5", 900, 600, 4)])
    rec = reconstruir.reconstruir(c, "2", cat)
    assert rec.avisos_material.get("FL4IN") and rec.avisos_material.get("FL5IN")
    # V_CANTIALT = 0: la cantidad sale de los m², con aviso.
    c = _casos([{"numero": "3"}], [_renglon("3", "FL5IN", 500, 500, 4, 0)])
    rec = reconstruir.reconstruir(c, "3", cat)
    assert rec.piezas[0]["cantidad"] == 16 and rec.avisos_material.get("FL5IN")
    # Piezas de DETPRES2 con el código de un vidrio del DVH: no se suman otra vez.
    c = _casos([{"numero": "4"}], [{**_renglon("4", "DVH4-12-5", 900, 600, 2, 0), **dvh}],
               [_pieza("4", "FL4IN", 900, 600, 2)])
    rec = reconstruir.reconstruir(c, "4", cat)
    assert sum(p["cantidad"] for p in rec.piezas if p["material"] == "FL4IN") == 2
    assert rec.avisos_material.get("FL4IN")


def test_reconstruir_filtros_de_lo_que_no_es_vidrio_y_clase_del_dvh():
    cat = set(Catalogo(usar_locales=False).materiales)
    arts = [{"codigo": "DVHX", "descripcion": "DVH", "familia": "XDVH", "espesor": "21"},
            {"codigo": "PVB038", "descripcion": "PVB 0,38", "familia": "MP LAMINAS", "espesor": "0.38"},
            {"codigo": "CAM9", "descripcion": "CÁMARA 9", "familia": "CÁMARAS", "espesor": "9"},
            {"codigo": "ENV", "descripcion": "ENVÍO A OBRA", "familia": "VARIOS", "espesor": "1"}]
    c = _casos([{"numero": "5"}],
               [_renglon("5", "DVHX", 900, 600, 2, 0, familia="XDVH"),  # sin ART1/ART3
                _renglon("5", "PVB038", 900, 600, 1, 1, familia="MP LAMINAS"),
                _renglon("5", "CAM9", 900, 600, 1, 1, familia="CÁMARAS"),
                _renglon("5", "ENV", 0, 0, 1, 0, familia="VARIOS")], articulos=arts)
    rec = reconstruir.reconstruir(c, "5", cat)
    assert not rec.piezas and {e["codigo"] for e in rec.excluidos} == {"DVHX", "PVB038", "CAM9", "ENV"}
    # DVH con piezas en DETPRES2 de clase "DVH": el pulido recto sale de CLASEART1/3.
    c = _casos([{"numero": "6"}],
               [{**_renglon("6", "DVH4-12-5", 900, 600, 2, 0, familia="XDVH", clase="DVH ESCALONADO"),
                 "art1": "FL4IN", "art3": "FL5IN", "claseart1": "FLOAT PR TEMP", "claseart3": ""}],
               [_pieza("6", "DVH4-12-5", 900, 600, 2, clase="DVH")])
    rec = reconstruir.reconstruir(c, "6", cat)
    clases = {p["material"]: p["clase"] for p in rec.piezas}
    assert clases == {"FL4IN": "FLOAT PR TEMP", "FL5IN": "DVH"}
    assert any("escalonado" in a for a in rec.avisos)
    # Una pieza de DETPRES2 sin clase no hereda el pulido de otro renglón del mismo vidrio.
    c = _casos([{"numero": "7"}],
               [_renglon("7", "FL5IN", 1000, 500, 1.5, 3, clase="FLOAT PR TEMP"), _renglon("7", "FL5IN", 800, 600, 0.96, 2)],
               [_pieza("7", "FL5IN", 1000, 500, 3, clase="FLOAT PR TEMP"), _pieza("7", "FL5IN", 800, 600, 2)])
    rec = reconstruir.reconstruir(c, "7", cat)
    assert [p["clase"] for p in rec.piezas] == ["FLOAT PR TEMP", ""]


def test_dos_lineas_al_mismo_codigo_no_se_comparan():
    cat = Catalogo(usar_locales=False)
    c = _casos([{"numero": "8", "observaciones": "4 GRIS: 1 HOJAS - 27%\n4 INC: 1 HOJAS - 27%"}],
               [_renglon("8", "FL4IN", 2000, 1200, 2.4, 1)], [_pieza("8", "FL4IN", 2000, 1200, 1)])
    trabajos, cob = comparar.preparar(c, cat)
    assert [t["abreviado"] for t in trabajos] == ["4 INC"] and cob["sin_relacionar"][0]["material"] == "4 GRIS"
    c = _casos([{"numero": "9", "observaciones": "4 INC: 1 HOJAS - 27%\n4 INCOLORO: 1 HOJAS - 27%"}],
               [_renglon("9", "FL4IN", 2000, 1200, 2.4, 1)], [_pieza("9", "FL4IN", 2000, 1200, 1)])
    trabajos, cob = comparar.preparar(c, cat)
    assert not trabajos and cob["repetidas"]


def test_retomar_recalcula_si_cambian_las_piezas_y_tolera_una_linea_cortada(tmp_path):
    cat = Catalogo(usar_locales=False)
    c = _casos([{"numero": "10", "observaciones": "5 INC: 1 HOJAS - 54%"}],
               [_renglon("10", "FL5IN", 2200, 2200, 4.84, 1)], [_pieza("10", "FL5IN", 2200, 2200, 1)])
    trabajos, _ = comparar.preparar(c, cat)
    assert len(trabajos) == 1
    salida = tmp_path / "r.jsonl"
    opciones = comparar.Opciones(esfuerzo="rapido", muestra=None, hipotesis=("H0",))
    comparar.correr(trabajos, salida, opciones, cat, mostrar=lambda *a: None)
    salida.write_text(salida.read_text(encoding="utf-8") + '{"numero": "10", "mat', encoding="utf-8")
    filas = comparar.correr(trabajos, salida, opciones, cat, mostrar=lambda *a: None)
    assert len(filas) == 1 and salida.read_text(encoding="utf-8").count("\n") == 2
    otro = [{**trabajos[0], "piezas": [{**trabajos[0]["piezas"][0], "ancho": 2100}]}]
    otro[0]["firma"] = comparar._firma(otro[0])
    comparar.correr(otro, salida, opciones, cat, mostrar=lambda *a: None)
    assert salida.read_text(encoding="utf-8").count('"numero": "10"') == 3  # recalculado


def test_publicar_y_docs_no_aceptan_datos_inventados_ni_nombres(tmp_path, monkeypatch):
    casos = datos.leer(JUGUETE)
    assert principal.es_inventado(casos)
    c = _casos([{"numero": "11", "observaciones": "OBRA FULANITO DETAL 5 INC: 2 HOJAS - 56%"}])
    assert "FULANITO" in principal.palabras_sospechosas("<p>Presupuesto 11 FULANITO</p>", c)
    assert not principal.palabras_sospechosas("<p>Presupuesto 11 FL5IN plancha</p>", c)
    escritos = []
    monkeypatch.setattr(principal, "actualizar_validacion", lambda *a, **k: escritos.append(a))
    principal.ejecutar(JUGUETE, tmp_path, comparar.Opciones(esfuerzo="rapido", muestra=3), docs=True,
                       publicar=True, mostrar=lambda *a: None)
    assert not escritos


def test_pagina_publicable_sin_textos_escritos_a_mano(corrida):
    salida, res = corrida
    filas = [json.loads(l) for l in (salida / "resultados_rapido.jsonl").read_text(encoding="utf-8").splitlines()]
    from optimizador.historico import revision
    pagina = revision.html(filas, res["eleccion"], res["prueba"], res["cobertura"], {}, publicable=True)
    assert "leyenda: «" not in pagina and "quedan 2 hojas" not in pagina


def test_varios_zips_se_juntan(tmp_path):
    import zipfile
    for anio in ("2024", "2025"):
        with zipfile.ZipFile(tmp_path / f"casos_historicos_{anio}.zip", "w") as z:
            for ruta in JUGUETE.iterdir():
                texto = ruta.read_text(encoding="utf-8")
                if ruta.name in ("presupuestos.csv", "renglones.csv", "piezas.csv") and anio == "2024":
                    texto = texto.replace("9000", "8000")
                z.writestr(ruta.name, texto)
    casos = datos.leer(tmp_path)
    assert len(casos.presupuestos) == 38 and any("se juntaron 2 zips" in d for d in casos.diferencias)
