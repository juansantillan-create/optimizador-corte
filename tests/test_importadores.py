"""Importar piezas: pegado de Excel, CSV, XLSX y planilla de la Interfaz."""

import io

import openpyxl

from optimizador import importadores as imp


def test_pegado_con_encabezado_y_formatos_de_numero():
    texto = "Material\tCant.\tAncho\tAlto\tObs\nfl5in\t4\t1.200\t2400\tpaño fijo\nFL5IN\t2\t1000\t600,0\t\nLX3+3IN\tx\t500\t500\n"
    r = imp.desde_texto(texto)
    assert [p["material"] for p in r.piezas] == ["FL5IN", "FL5IN"]
    assert r.piezas[0] == {"item": "1", "material": "FL5IN", "cantidad": 4, "ancho": 1200, "largo": 2400,
                           "descripcion": "paño fijo"}
    assert r.piezas[1]["largo"] == 600
    assert any("fila 4" in a for a in r.avisos)  # la cantidad "x" no se inventa
    assert r.columnas["largo"].startswith("columna 4")


def test_pegado_sin_encabezado_por_posicion():
    r = imp.desde_texto("FL5IN\t3\t500\t700\nFL4IN\t1\t300\t300\tchico")
    assert len(r.piezas) == 2 and r.piezas[1]["descripcion"] == "chico"
    assert any("por posición" in a for a in r.avisos)


def test_pegado_con_espacios():
    r = imp.desde_texto("FL5IN 4 1200 2400 paño fijo grande")
    assert r.piezas[0]["descripcion"] == "paño fijo grande" and r.piezas[0]["ancho"] == 1200


def test_numero_mm():
    assert imp.numero_mm("1.200") == 1200
    assert imp.numero_mm("1.234,5") == 1234.5
    assert imp.numero_mm("600,0") == 600
    assert imp.numero_mm("") is None and imp.numero_mm("abc") is None


def test_csv_con_punto_y_coma_y_latin1():
    datos = "Código;Cantidad;Ancho;Largo;Descripción\nFL5IN;2;800;600;baño\n".encode("cp1252")
    r = imp.desde_csv(datos)
    assert r.piezas == [{"item": "1", "material": "FL5IN", "cantidad": 2, "ancho": 800, "largo": 600,
                         "descripcion": "baño"}]


def _xlsx(filas):
    libro = openpyxl.Workbook()
    hoja = libro.active
    for f in filas:
        hoja.append(f)
    datos = io.BytesIO()
    libro.save(datos)
    return datos.getvalue()


def test_xlsx():
    r = imp.desde_xlsx(_xlsx([["Material", "Cantidad", "Ancho", "Largo", "Clase"],
                              ["FL6IN", 3, 1000, 2000, "FLOAT PR TEMP"]]))
    assert r.piezas[0]["clase"] == "FLOAT PR TEMP" and r.piezas[0]["cantidad"] == 3


def test_interfaz_dvh_y_herrajes_por_posicion():
    # Columnas de Juan (pregunta 13): A TIPO, B VIDRIO1, C CAMARA, D VIDRIO2, E ANCHO, F LARGO,
    # G ANCHO2, H LARGO2, I CANTIDAD, J TIPOLOGIA, K OBS, L NTAS, M CLASE, N/O CLASE CARA1/2.
    fila_dvh = ["DVH", "FL4IN", "CAM12", "FL5IN", 1000, 1200, "", "", 2, "", "", "", "DVH PR", "", ""]
    fila_esc = ["DVH", "FL4IN", "CAM12", "FL5IN", 1000, 1200, 960, 1160, 1, "", "", "", "", "", ""]
    fila_vs = ["TEMPLUX", "FL10IN", "", "", 800, 900, "", "", 3, "", "", "", "FLOAT PR TEMP", "", ""]
    herraje = ["DIST", "HERR01", "", "", 0, 1, "", "", 4, "", "", "", "", "", ""]
    r = imp.desde_interfaz(_xlsx([fila_dvh, fila_esc, fila_vs, herraje]), "planilla.xlsx")
    assert [(p["material"], p["cantidad"], p["ancho"], p["largo"]) for p in r.piezas] == [
        ("FL4IN", 2, 1000, 1200), ("FL5IN", 2, 1000, 1200),  # el DVH son 2 vidrios
        ("FL4IN", 1, 1000, 1200), ("FL5IN", 1, 960, 1160),  # escalonado: el vidrio 2 con ANCHO2/LARGO2
        ("FL10IN", 3, 800, 900)]
    assert any("herrajes" in a for a in r.avisos) and any("escalonado" in a for a in r.avisos)


def test_interfaz_con_encabezados():
    r = imp.desde_interfaz(_xlsx([["TIPO", "VIDRIO1", "CAMARA", "VIDRIO2", "ANCHO", "LARGO", "CANT"],
                                  ["VS", "FL5IN", "", "", 500, 600, 3]]), "x.xlsx")
    assert r.piezas[0]["cantidad"] == 3 and not any("SUPUESTA" in v for v in r.columnas.values())


# ------------------------------------------------ lo que encontró la revisión de F3
def test_encabezados_con_otros_nombres_unidades_y_titulo():
    for texto in ("Material\tCantidad de piezas\tAncho\tLargo\nFL4IN\t5\t1200\t800",
                  "Material\tCant. pzas\tAncho (mm)\tAlto (mm)\nFL4IN\t5\t1200\t800",
                  "Presupuesto 123\n\nMaterial\tQty\tAncho\tLargo\nFL4IN\t5\t1200\t800",
                  "Cantidad\tMaterial\tAncho\tLargo\n5\tFL4IN\t1200\t800"):
        r = imp.desde_texto(texto)
        assert [(p["material"], p["cantidad"], p["ancho"], p["largo"]) for p in r.piezas] == \
            [("FL4IN", 5, 1200, 800)], texto


def test_sin_columna_de_cantidad_avisa():
    r = imp.desde_texto("Material\tAncho\tLargo\tDescripción\nFL4IN\t1000\t500\tpuerta")
    assert r.piezas[0]["cantidad"] == 1 and any("cantidad" in a for a in r.avisos)


def test_planilla_de_la_interfaz_pegada_o_en_xlsx():
    texto = ("TIPO\tVIDRIO1\tCAMARA\tVIDRIO2\tANCHO\tLARGO\tCANTIDAD\n"
             "DVH\tFL4IN\tCAM12\tFL5IN\t900\t1400\t2\nDIST\tHERR\t\t\t500\t1\t4")
    r = imp.desde_texto(texto)
    assert [(p["material"], p["cantidad"]) for p in r.piezas] == [("FL4IN", 2), ("FL5IN", 2)]
    assert any("herrajes" in a for a in r.avisos)


def test_csv_con_coma_decimal_sin_comillas_y_unicode():
    r = imp.desde_csv(b"material,cantidad,ancho,largo\nFL4IN,2,1200,5,800\nFL4IN,2,1200,800")
    assert len(r.piezas) == 1 and any("más columnas" in a for a in r.avisos)
    r = imp.desde_csv("material;cantidad;ancho;largo\nFL4IN;2;1200;800".encode("utf-16"))
    assert r.piezas[0]["ancho"] == 1200


def test_nan_e_infinito_no_son_numeros():
    assert imp.numero_mm("nan") is None and imp.numero_mm("inf") is None
    assert imp.numero_mm(float("nan")) is None


def test_dos_columnas_para_lo_mismo():
    r = imp.desde_texto("Material\tCant. m2\tCant. piezas\tAncho\tLargo\nFL4IN\t1,92\t2\t1200\t800")
    assert r.piezas[0]["cantidad"] == 2
    r = imp.desde_texto("Material\tCantidad\tAncho\tAlto\tLargo\nFL4IN\t2\t1200\t800\t900")
    assert r.piezas[0]["largo"] == 900 and any("más de una columna" in a for a in r.avisos)
