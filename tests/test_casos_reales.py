"""Los casos reales que mandó Juan (25/10/2026): Corte Certo exportado por vidrio y lotes de Optima.
Sin nombres de clientes: solo números de presupuesto o de pedido, códigos de vidrio y medidas."""

from pathlib import Path

import pytest

from optimizador.configuracion import Catalogo
from optimizador.historico import comparar, exportados, optima

RAIZ = Path(__file__).resolve().parents[1]
CORTE_CERTO = RAIZ / "datos" / "casos" / "corte_certo"
OPTIMA = RAIZ / "datos" / "casos" / "optima"

pytestmark = pytest.mark.skipif(not CORTE_CERTO.exists(), reason="faltan los casos reales")


@pytest.fixture(scope="module")
def preparados():
    cat = Catalogo(usar_locales=False)
    casos = exportados.leer(CORTE_CERTO)
    return cat, casos, *exportados.preparar(casos, cat)


def test_lectura_y_cobertura(preparados):
    _, casos, trabajos, cob = preparados
    assert len(casos) == 1341 and sum(len(c.piezas) > 0 for c in casos) == 1341
    descartados = len(cob["sin_hojas"]) + len(cob["con_bandas"]) + len(cob["area_no"]) + len(cob["no_cierran"])
    principales = [t for t in trabajos if not t["extra"]["alternativa"]]
    alternativas = [t for t in trabajos if t["extra"]["alternativa"]]
    assert cob["control_ok"] == len(principales) and cob["control_ok"] + descartados == 1341
    assert cob["control_ok"] > 1000
    # La alternativa (hoja entera) solo existe cuando el caso también cierra así.
    assert len(alternativas) == cob["con_alternativa"]
    assert all(t["extra"]["variante"] == "hoja entera" for t in alternativas)


def test_piezas_ya_traen_el_mas3_y_no_se_suma_otra_vez(preparados):
    _, casos, trabajos, _ = preparados
    caso = next(c for c in casos if any(p["pulido_recto"] for p in c.piezas))
    con = exportados._piezas(caso, True)
    assert all("clase" not in p for p in con)  # el programa no suma nada: ya viene sumado
    assert any(p["ancho"] == q["ancho_original"] + 3 for p, q in zip(con, caso.piezas) if q["pulido_recto"])


def test_control_usa_banda_20_como_corte_certo(preparados):
    cat, casos, _, _ = preparados
    # 5+5: con la banda de Lucas (50) no cierra; con 20 (como estaba cargado Corte Certo) sí.
    caso = next(c for c in casos if c.numero == "4872" and c.material == "LX5+5IN")
    assert exportados.control(caso, cat)["plancha"] == "3600x2500"


def test_cuantas_entran_por_plancha():
    # 900 × 478: en la hoja entera (3600) entran 4 × 5 = 20; con banda 20 (3580), como mucho 17.
    assert exportados.max_por_plancha(900, 478, 3600, 2500) == 20
    assert exportados.max_por_plancha(900, 478, 3580, 2500) == 17
    assert exportados.max_por_plancha(30, 40, 3580, 2500) is None  # piezas chicas: no se cuenta
    piezas = [{"cantidad": 7800, "ancho": 478, "largo": 900}]
    assert exportados.minimo_planchas(piezas, 3580, 2500) == 459  # por área serían 391


def test_control_descarta_la_banda_si_las_piezas_no_entran(preparados):
    cat, casos, _, _ = preparados
    # 7800 piezas de 900 × 478 en 412 hojas: con banda 20 hacen falta 459 → era la hoja entera.
    caso = next(c for c in casos if c.numero == "7781" and c.material == "FL4IN")
    r = exportados.control(caso, cat)
    assert (r["plancha"], r["variante"], r["alternativa"]) == ("3600x2500", "hoja entera", None)


def test_algunos_casos_de_punta_a_punta(preparados, tmp_path):
    cat, _, trabajos, _ = preparados
    elegidos = [t for t in trabajos if t["n_piezas"] <= 30][:4]
    filas = comparar.correr(elegidos, tmp_path / "r.jsonl",
                            comparar.Opciones(esfuerzo="rapido", muestra=None, hipotesis=("H0",)), cat,
                            mostrar=lambda *a: None)
    assert len(filas) == 4 and all(f["verificado"] and f["completo"] for f in filas)


@pytest.mark.skipif(not OPTIMA.exists(), reason="faltan los lotes de Optima")
def test_optima_un_lote():
    cat = Catalogo(usar_locales=False)
    lotes = optima.leer(OPTIMA)
    assert [l.lote for l in lotes] == ["164601", "165903", "172802", "172905", "173703"]
    lote = next(l for l in lotes if l.lote == "172802")
    assert sum(p["cantidad"] for p in lote.piezas) == 29
    r = optima.calcular(lote, cat, "lucas", "rapido")
    assert r["verificado"] and r["completo"] and r["destaque"] == 30 and r["banda"] == 30
