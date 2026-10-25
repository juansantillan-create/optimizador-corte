"""Genera `tests/historico_juguete/`: un zip "de juguete" con el formato de `docs/CONTRATO_DATOS.md`
(versión 2) para probar la validación histórica de punta a punta mientras no lleguen los datos
reales.

**TODO ES INVENTADO**: números de presupuesto 900001 en adelante, piezas y leyendas armadas a
mano. No sale de Metrix y no tiene nombres de nadie.

    python herramientas/generar_caso_juguete.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "tests" / "historico_juguete"
UTIL = {"FL4IN": 3580 * 2500, "FL5IN": 3580 * 2500, "LX4+4NL": 3570 * 2500, "LX3+3LOW": 3280 * 2440,
        "LX3+3IN": 3580 * 2500, "LX3+3BC": 3580 * 2500, "FL10IN": 3650 * 2500}
ABREV = {"FL4IN": "4 INC", "FL5IN": "5 INC", "LX4+4NL": "4+4 NLIGHT", "LX3+3LOW": "3+3 LOWE",
         "LX3+3IN": "3+3", "FL10IN": "10 INC"}


def m2(piezas, material):
    total = 0
    for mat, cant, ancho, largo, clase in piezas:
        if mat == material:
            extra = 3 if " PR" in f" {clase} " else 0
            total += cant * (ancho + extra) * (largo + extra)
    return total


def linea(material, hojas, piezas, separador=":"):
    aprov = round(m2(piezas, material) / (hojas * UTIL[material]) * 100)
    return f"{ABREV[material]}{separador} {hojas} HOJAS - {aprov}% ******* L.DIST -10%"


def main():
    r = random.Random(7)
    presupuestos, renglones, piezas_csv = [], [], []
    casos = []
    # 900001: float 5 mm, piezas grandes, cotizado con 3 hojas.
    casos.append((900001, [("FL5IN", 4, 1150, 2400, "FLOAT TEMP"), ("FL5IN", 3, 1000, 2380, "FLOAT PR TEMP")],
                  [("FL5IN", 3)], "", []))
    # 900002: un DVH (FL4IN + FL5IN) más un herraje y un flete que no se optimizan.
    casos.append((900002, [("DVH", 6, 900, 1400, "DVH")], [("FL4IN", 1), ("FL5IN", 1)], "",
                  [("HERR01", "HERRAJES", 4), ("FLETE", "FLETES", 1)]))
    # 900003: dos laminados, con el separador "_" que aparece en las leyendas reales.
    casos.append((900003, [("LX4+4NL", 10, 1200, 1500, "LAM"), ("LX3+3LOW", 4, 800, 1000, "LAM")],
                  [("LX4+4NL", 3), ("LX3+3LOW", 1)], "_", []))
    # 900004: texto que no es una leyenda que se pueda leer.
    casos.append((900004, [("FL5IN", 2, 500, 500, "")], [], "quedan 2 hojas aprox", []))
    # 900005: la leyenda no cierra con las piezas (el presupuesto cambió después).
    casos.append((900005, [("FL5IN", 2, 500, 600, "")], [("FL5IN", 10)], "", []))
    # 900006: sin leyenda.
    casos.append((900006, [("FL5IN", 2, 700, 800, "")], [], "dolar 1450", []))
    # 900007: material ambiguo ("3+3" con dos laminados 3+3 distintos).
    casos.append((900007, [("LX3+3IN", 4, 1000, 1000, ""), ("LX3+3BC", 2, 600, 600, "")], [("LX3+3IN", 1)],
                  "ambiguo", []))
    # 900008 a 900019: más float para que haya casos de calibración y de prueba.
    for k in range(12):
        numero = 900008 + k
        material = r.choice(["FL5IN", "FL4IN", "FL10IN"])
        pz = [(material, r.randint(2, 10), r.randrange(400, 1800, 10), r.randrange(500, 2300, 10),
               r.choice(["", "FLOAT PR TEMP"])) for _ in range(r.randint(2, 5))]
        area = m2(pz, material)
        hojas = max(1, -(-area // UTIL[material]) + r.choice([0, 0, 0, 1, 1, -0]))
        casos.append((numero, pz, [(material, int(hojas))], "", []))

    for numero, pz, leyenda, extra, otros in casos:
        if extra == "quedan 2 hojas aprox":
            obs = extra
        elif extra == "ambiguo":
            obs = "LISTA 1\n3+3: 1 HOJAS - 52% ******* L.DIST -10%"
        elif extra == "dolar 1450":
            obs = ""
        elif numero == 900005:
            obs = "LISTA 1\n5 INC: 10 HOJAS - 90% ******* L.DIST -10%"  # no cierra a propósito
        else:
            obs = "LISTA 1\n" + "\n".join(linea(m, h, pz if m != "FL4IN" or numero != 900002 else
                                                [("FL4IN", 6, 900, 1400, "")],
                                                extra or ":") for m, h in leyenda)
            if numero == 900002:
                obs = "LISTA 2\n" + linea("FL4IN", 1, [("FL4IN", 6, 900, 1400, "")]) + "\n" + \
                      linea("FL5IN", 1, [("FL5IN", 6, 900, 1400, "")])
        presupuestos.append({"numero": numero, "fecha": "2026-01-01", "estado_pres": "ACEPTADO",
                             "tipopresup": "", "observaciones": obs,
                             "tv_descrip": "dolar 1450 (inventado)" if extra == "dolar 1450" else ""})
        orden = 0
        for mat, cant, ancho, largo, clase in pz:
            orden += 1
            if mat == "DVH":
                renglones.append({"numero": numero, "orden": orden, "v_codart": "DVH4-12-5", "familia": "XDVH",
                                  "art1": "FL4IN", "art2": "CAM12", "art3": "FL5IN", "claseart1": "",
                                  "claseart3": "", "clase": clase, "largo": largo, "ancho": ancho,
                                  "v_canti": cant, "v_cantialt": 0, "detalle": "DVH inventado"})
                continue
            renglones.append({"numero": numero, "orden": orden, "v_codart": mat, "familia": "FLOAT",
                              "art1": "", "art2": "", "art3": "", "claseart1": "", "claseart3": "",
                              "clase": clase, "largo": largo, "ancho": ancho,
                              "v_canti": round(cant * ancho * largo / 1e6, 3), "v_cantialt": cant,
                              "detalle": "inventado"})
            piezas_csv.append({"numero": numero, "v_codart": mat, "clase": clase, "largo": largo,
                               "ancho": ancho, "v_canti": round(cant * ancho * largo / 1e6, 3),
                               "v_cantialt": cant, "detalle": ""})
        for codigo, familia, cant in otros:
            orden += 1
            renglones.append({"numero": numero, "orden": orden, "v_codart": codigo, "familia": familia,
                              "art1": "", "art2": "", "art3": "", "claseart1": "", "claseart3": "",
                              "clase": "", "largo": 0, "ancho": 0, "v_canti": cant, "v_cantialt": 0,
                              "detalle": "inventado"})
    articulos = [{"codigo": c, "descripcion": d, "familia": f, "espesor": e, "factor": 1, "clase": "", "compuesto": ""}
                 for c, d, f, e in [("DVH4-12-5", "DVH 4/12/5 (inventado)", "XDVH", 0), ("CAM12", "CAMARA 12", "CAMARAS", 0),
                                    ("HERR01", "HERRAJE INVENTADO", "HERRAJES", 0), ("FLETE", "FLETE", "FLETES", 0)]]
    familias = [{"familia": f, "medidas": "", "perimetro": ""} for f in ("XDVH", "CAMARAS", "HERRAJES", "FLETES", "FLOAT")]
    DESTINO.mkdir(parents=True, exist_ok=True)
    for nombre, filas in (("presupuestos.csv", presupuestos), ("renglones.csv", renglones),
                          ("piezas.csv", piezas_csv), ("articulos.csv", articulos), ("familias.csv", familias)):
        with (DESTINO / nombre).open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";")
            w.writeheader()
            w.writerows(filas)
    (DESTINO / "LEEME.txt").write_text(
        "CASO DE JUGUETE, TODO INVENTADO (no sale de Metrix).\n"
        "Lo genera herramientas/generar_caso_juguete.py para probar la validación histórica.\n"
        "Contrato: docs/CONTRATO_DATOS.md versión 2. La leyenda está en la columna 'observaciones'.\n",
        encoding="utf-8")
    print(f"{len(presupuestos)} presupuestos inventados en {DESTINO}")


if __name__ == "__main__":
    main()
