"""El servidor local de punta a punta (sin navegador): se levanta de verdad en un puerto libre."""

import base64
import json
import shutil
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from optimizador.configuracion import CARPETA_CONFIG

uvicorn = pytest.importorskip("uvicorn")


@pytest.fixture(scope="module")
def servidor(tmp_path_factory):
    from optimizador.servidor import crear_app, puerto_libre

    config = tmp_path_factory.mktemp("config")
    for nombre in ("hojas.csv", "reglas_corte.csv"):
        shutil.copy(CARPETA_CONFIG / nombre, config / nombre)
    proyectos = tmp_path_factory.mktemp("proyectos")
    puerto = puerto_libre(18520, 18600)
    srv = uvicorn.Server(uvicorn.Config(crear_app(config, proyectos), host="127.0.0.1", port=puerto,
                                        log_level="error"))
    hilo = threading.Thread(target=srv.run, daemon=True)
    hilo.start()
    for _ in range(100):
        if srv.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{puerto}", config, proyectos
    srv.should_exit = True
    hilo.join(timeout=5)


def pedir(base, ruta, cuerpo=None, metodo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(base + ruta, data=datos, method=metodo or ("POST" if datos else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        contenido = r.read()
        return json.loads(contenido) if r.headers.get_content_type() == "application/json" else contenido


ENTRADA = {"proyecto": {"codigo": "S1", "descripcion": "servidor"},
           "piezas": [{"item": "1", "material": "FL5IN", "cantidad": 5, "ancho": 1000, "largo": 2000},
                      {"item": "2", "material": "FL8BR", "cantidad": 1, "ancho": 500, "largo": 500}],
           "opciones": {"esfuerzo": "rapido"}}


def test_pagina_y_estado(servidor):
    base, _, _ = servidor
    html = pedir(base, "/").decode()
    assert "Optimizador de corte" in html and "http" not in html.replace("http-equiv", "")
    assert "corte_certo" in pedir(base, "/api/estado")["presets"]


def test_revisar_avisa_material_supuesto(servidor):
    base, _, _ = servidor
    r = pedir(base, "/api/revisar", ENTRADA)
    assert any("FL8BR" in a and "SUPUESTA" in a for a in r["avisos"]) and r["piezas"] == 6


def test_calcular_informe_y_exportar(servidor):
    base, _, _ = servidor
    c = pedir(base, "/api/calcular", ENTRADA)
    for _ in range(200):
        c = pedir(base, f"/api/calculo/{c['id']}")
        if c["estado"] != "calculando":
            break
        time.sleep(0.1)
    assert c["estado"] == "listo" and c["verificado"] is True
    html = pedir(base, f"/api/calculo/{c['id']}/informe.html?modo=detalle").decode()
    assert "Informe de cálculo" in html and "Cdad. de montajes:" in html
    assert pedir(base, f"/api/calculo/{c['id']}/consumo.csv").decode("utf-8-sig").startswith("Proyecto;")
    assert pedir(base, f"/api/calculo/{c['id']}/consumo.xlsx")[:2] == b"PK"
    assert pedir(base, f"/api/calculo/{c['id']}/resultado.json")["verificado"] is True


def test_ajustes_de_material_en_la_pc(servidor):
    base, config, _ = servidor
    m = pedir(base, "/api/materiales/FL4IN")
    assert m["separacion_piezas_mm"] == 0 and len(m["planchas"]) == 3
    pedir(base, "/api/materiales/FL4IN", {"separacion_piezas_mm": 7,
                                          "planchas_habilitadas": {"3300x2440": False}}, "PUT")
    m = pedir(base, "/api/materiales/FL4IN")
    assert m["separacion_piezas_mm"] == 7 and m["base"]["separacion_piezas_mm"] == 0
    assert [p["habilitada"] for p in m["planchas"]] == [True, True, False]
    guardado = json.loads((config / "local" / "materiales.json").read_text())["FL4IN"]
    # La sierra depende del preset: se guarda solo para "Como Corte Certo hoy".
    assert guardado["por_preset"]["corte_certo"]["separacion_piezas_mm"] == 7
    assert pedir(base, "/api/materiales/FL4IN?preset=lucas")["separacion_piezas_mm"] == 20
    assert [p["habilitada"] for p in pedir(base, "/api/materiales/FL4IN?preset=lucas")["planchas"]] == [True, True, False]
    # Un valor imposible no se guarda.
    with pytest.raises(urllib.error.HTTPError) as error:
        pedir(base, "/api/materiales/FL4IN", {"separacion_piezas_mm": -10}, "PUT")
    assert error.value.code == 400
    pedir(base, "/api/materiales/FL4IN/locales", metodo="DELETE")
    assert pedir(base, "/api/materiales/FL4IN")["separacion_piezas_mm"] == 0


def test_solo_atiende_a_esta_pc(servidor):
    base, _, _ = servidor
    req = urllib.request.Request(base + "/api/estado", headers={"Host": "malicioso.example.com"})
    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(req, timeout=10)
    assert error.value.code == 403


def test_proyectos_con_el_mismo_nombre_de_archivo(servidor):
    base, _, proyectos = servidor
    largo = {**ENTRADA, "proyecto": {"codigo": "P" * 70, "descripcion": ""}}
    r = pedir(base, "/api/proyectos", largo)
    assert pedir(base, "/api/proyectos/" + r["archivo"])["proyecto"]["codigo"] == "P" * 70
    pedir(base, "/api/proyectos", {**ENTRADA, "proyecto": {"codigo": "11580/A"}})
    with pytest.raises(urllib.error.HTTPError) as error:
        pedir(base, "/api/proyectos", {**ENTRADA, "proyecto": {"codigo": "11580 A"}})
    assert error.value.code == 409
    pedir(base, "/api/proyectos?sobrescribir=1", {**ENTRADA, "proyecto": {"codigo": "11580 A"}})


def test_guardar_y_abrir_proyecto(servidor):
    base, _, proyectos = servidor
    r = pedir(base, "/api/proyectos", ENTRADA)
    assert (proyectos / r["archivo"]).exists()
    lista = pedir(base, "/api/proyectos")
    assert lista[0]["codigo"] == "S1"
    assert pedir(base, "/api/proyectos/" + r["archivo"])["piezas"][0]["ancho"] == 1000


def test_importar_archivo(servidor):
    base, _, _ = servidor
    datos = base64.b64encode("material;cantidad;ancho;largo\nFL5IN;2;300;400\n".encode()).decode()
    r = pedir(base, "/api/importar/archivo", {"nombre": "piezas.csv", "datos": datos})
    assert r["piezas"][0]["ancho"] == 300


def test_calculo_en_curso_y_uno_a_la_vez(servidor):
    base, _, _ = servidor
    piezas = [{"item": str(i), "material": "FL4IN", "cantidad": 1, "ancho": 200 + 3 * i, "largo": 300 + 5 * i}
              for i in range(150)]
    c = pedir(base, "/api/calcular", {"piezas": piezas, "opciones": {"esfuerzo": "normal"}})
    try:
        assert pedir(base, "/api/calculo_en_curso")["id"] == c["id"]  # p. ej., después de recargar
        with pytest.raises(urllib.error.HTTPError) as error:
            pedir(base, "/api/calcular", ENTRADA)
        assert error.value.code == 409
    finally:
        pedir(base, f"/api/calculo/{c['id']}/cancelar", {})
    for _ in range(200):
        if pedir(base, f"/api/calculo/{c['id']}")["estado"] != "calculando":
            break
        time.sleep(0.2)
    with pytest.raises(urllib.error.HTTPError) as error:
        pedir(base, "/api/calculo_en_curso")
    assert error.value.code == 404
