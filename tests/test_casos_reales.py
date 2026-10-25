"""Los casos reales que mandó Juan (25/10/2026): Corte Certo exportado por vidrio y lotes de Optima.
Sin nombres de clientes: solo números de presupuesto o de pedido, códigos de vidrio y medidas."""

from pathlib import Path

import pytest

from optimizador.configuracion import Catalogo
from optimizador.historico import comparar, exportados, optima, principal

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
    descartados = sum(len(cob[k]) for k in ("sin_hojas", "con_bandas", "area_no", "varias_medidas",
                                             "no_cierran", "duplicados", "sin_piezas"))
    principales = [t for t in trabajos if not t["extra"]["alternativa"]]
    alternativas = [t for t in trabajos if t["extra"]["alternativa"]]
    assert cob["control_ok"] == len(principales) and cob["control_ok"] + descartados == 1341
    assert cob["control_ok"] > 1000 and sum(cob["variantes"].values()) == cob["control_ok"]
    # Cada caso una sola vez, y su variante (si tiene) es la otra de banda 20 ↔ hoja entera.
    assert len({(t["numero"], t["material"]) for t in principales}) == len(principales)
    assert len(alternativas) == cob["con_alternativa"] + cob["forzadas"]
    assert sum(bool(a["extra"].get("forzada")) for a in alternativas) == cob["forzadas"]
    por_caso = {(t["numero"], t["material"]): t for t in principales}
    for a in alternativas:
        t = por_caso[(a["numero"], a["material"])]
        assert t["extra"]["tiene_alternativa"] == (not a["extra"]["forzada"]) and t["piezas"] == a["piezas"]
        assert {t["extra"]["variante"], a["extra"]["variante"]} == {"banda 20", "hoja entera"}


def test_piezas_ya_traen_el_mas3_y_no_se_suma_otra_vez(preparados):
    _, casos, trabajos, _ = preparados
    caso = next(c for c in casos if any(p["pulido_recto"] for p in c.piezas))
    con = exportados._piezas(caso, True)
    assert all("clase" not in p for p in con)  # el programa no suma nada: ya viene sumado
    assert any(p["ancho"] == q["ancho_original"] + 3 for p, q in zip(con, caso.piezas) if q["pulido_recto"])


def _caso(casos, numero, material):
    return next(c for c in casos if c.numero == numero and c.material == material)


def test_control_prefiere_lo_que_cierra_redondeando(preparados):
    cat, casos, _, _ = preparados
    # 5+5, 79 %: con la hoja entera da 79,20 (redondeando, 79); con 3580, 79,65 (solo truncando).
    r = exportados.control(_caso(casos, "4872", "LX5+5IN"), cat)
    assert (r["plancha"], r["variante"], r["redondea"]) == ("3600x2500", "hoja entera", True)
    assert (r["alternativa"]["variante"], r["alternativa"]["redondea"]) == ("banda 20", False)
    # 4+4 NL, 81 %: con 3580 da 81,28 y con la hoja entera 80,83; las dos redondean y gana la más
    # cercana (la hoja entera). Banda 20 queda como variante.
    r = exportados.control(_caso(casos, "6348", "LX4+4NL"), cat)
    assert (r["variante"], r["redondea"], r["alternativa"]["variante"]) == ("hoja entera", True, "banda 20")


def test_evidencia_de_la_banda(preparados):
    cat, casos, _, _ = preparados
    filas = exportados.evidencia_banda(casos, cat)
    antes = [f for f in filas if f["periodo"] < "2026-07"]
    assert antes and sum(f["casos"] for f in antes) > 200
    # Hasta junio de 2026: con 3600 redondeando cierra casi todo; con la banda de Lucas de 50, casi nada.
    for f in antes:
        assert f["3600 (hoja entera)"]["redondea_%"] >= 90 and f["3550 (banda 50)"]["redondea_%"] <= 10
    assert (sum(f["contra_3600_redondeando"] for f in antes) < sum(f["contra_3580_truncando"] for f in antes))


def test_medida_anotada_que_ya_es_util_va_tal_cual(preparados):
    cat, casos, _, _ = preparados
    # "27x3190x2540": 3190 no es una hoja entera conocida (la de 3210 menos 20): no se le resta más.
    r = exportados.control(_caso(casos, "10657", "CK6K2"), cat)
    assert (r["variante"], r["alternativa"]) == (exportados.ANOTADA_UTIL, None)
    assert r["planchas"] == [{"ancho": 3190, "largo": 2540, "corte_banda": 0}]


def test_casos_iguales_se_cuentan_una_vez(preparados):
    _, _, trabajos, cob = preparados
    # 6348 LX4+4NL y 6358 FL6NL: las mismas piezas, hojas y %.
    assert {"numero": "6358", "material": "FL6NL", "igual_a": "6348 LX4+4NL"} in cob["duplicados"]
    assert not any(t["numero"] == "6358" and t["material"] == "FL6NL" for t in trabajos)


def test_cuantas_entran_por_plancha():
    # 900 × 478: en la hoja entera (3600) entran 4 × 5 = 20; con banda 20 (3580), como mucho 17.
    assert exportados.max_por_plancha(900, 478, 3600, 2500) == 20
    assert exportados.max_por_plancha(900, 478, 3580, 2500) == 17
    assert exportados.max_por_plancha(30, 40, 3580, 2500) is None  # piezas chicas: no se cuenta
    piezas = [{"cantidad": 7800, "ancho": 478, "largo": 900}]
    assert exportados.minimo_planchas(piezas, 3580, 2500) == 459  # por área serían 375


def test_control_descarta_la_banda_si_las_piezas_no_entran(preparados):
    cat, casos, _, _ = preparados
    # 7800 piezas de 900 × 478 en 412 hojas: con banda 20 hacen falta 459 → era la hoja entera.
    r = exportados.control(_caso(casos, "7781", "FL4IN"), cat)
    assert (r["plancha"], r["variante"]) == ("3600x2500", "hoja entera")
    # Con banda 20 cierra solo con otra medida, deducida (3660 × 2440): no hay variante, y como es
    # menos confiable que la de hojas.csv, se sabe que era la hoja entera. Igual se calcula con banda
    # 20 en la misma medida ("forzada"), para ver cuánto daría cotizar siempre así.
    assert r["alternativa"] is None and r["unica"]
    assert (r["forzada"]["plancha"], r["forzada"]["variante"]) == ("3600x2500", "banda 20")


def test_vistas_eligen_la_variante_pedida():
    def fila(numero, variante, planchas, alternativa=False, tiene=False):
        return {"numero": numero, "material": "X", "hipotesis": "H0", "cc_hojas": 10, "cc_aprov": 80.0,
                "planchas": planchas, "minimo": 5, "verificado": True, "completo": True, "avisos": [],
                "n_piezas": 10, "grupo": "X", "calibracion": False, "aprovechamiento": 80.0, "plancha": "3600x2500",
                "extra": {"variante": variante, "alternativa": alternativa, "tiene_alternativa": tiene,
                          "unica": not tiene}}
    todas = [fila("1", "hoja entera", 10, tiene=True), fila("1", "banda 20", 11, alternativa=True),
             fila("2", "banda 20", 9, tiene=True), fila("2", "hoja entera", 9, alternativa=True),
             fila("3", "banda 20", 12)]
    # El 3 con la hoja entera "forzada": las piezas no entran (deja piezas sin calcular).
    todas.append({**fila("3", "hoja entera", 0, alternativa=True), "completo": False})
    filas, vistas = principal.vistas_exportados(todas)
    assert [f["numero"] for f in filas] == ["1", "2", "3"]
    assert vistas["probable"]["casos"] == vistas["banda"]["casos"] == vistas["entera"]["casos"] == 3
    assert vistas["banda"]["peores_%"] == 66.7  # el 1 con banda 20 da 11 y el 3 da 12
    assert vistas["entera"]["no_entran"] == 1 and vistas["entera"]["peores_%"] == 33.3  # el 3 no se puede
    assert vistas["seguros"]["casos"] == 1  # solo el 3 no tiene otra variante que cierre


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
    assert set(r["hojas"]) <= {"3600x2500"}  # solo las medidas que usó Optima
    # Como se cotizaría: "Como Corte Certo hoy" con la plancha por defecto (sin destaque).
    c = optima.calcular(lote, cat, "corte_certo", "rapido", medidas_de_optima=False)
    assert c["destaque"] == 0 and c["banda"] == 20 and c["verificado"]
