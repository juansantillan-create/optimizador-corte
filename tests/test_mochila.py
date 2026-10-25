"""La mochila acotada contra fuerza bruta."""

import itertools

from hypothesis import given, settings, strategies as st

from optimizador.motor.mochila import Cosa, mejores_por_capacidad, paquetes, resolver


def test_paquetes_suman_la_cota():
    for n in range(0, 100):
        p = paquetes(n)
        assert sum(p) == n
        # con subconjuntos se arma cualquier cantidad entre 0 y n
        sumas = {sum(c) for r in range(len(p) + 1) for c in itertools.combinations(p, r)}
        assert sumas == set(range(n + 1))


def _fuerza_bruta(capacidad, cosas, destaque):
    mejor = 0.0
    rangos = [range(min(c.cota, capacidad // c.largo) + 1) for c in cosas]
    for cant in itertools.product(*rangos):
        usado = sum(n * c.largo for n, c in zip(cant, cosas))
        if usado > capacidad:
            continue
        sobra = capacidad - usado
        if destaque > 0 and 0 < sobra < destaque:
            continue
        mejor = max(mejor, sum(n * c.valor for n, c in zip(cant, cosas)))
    return mejor


@settings(max_examples=150, deadline=None)
@given(
    capacidad=st.integers(1, 60),
    cosas=st.lists(st.tuples(st.integers(1, 25), st.integers(1, 20), st.integers(0, 4)),
                   min_size=1, max_size=4),
    destaque=st.integers(0, 8),
)
def test_resolver_igual_a_fuerza_bruta(capacidad, cosas, destaque):
    cs = [Cosa(l, float(v), c) for l, v, c in cosas]
    valor, cant = resolver(capacidad, cs, destaque)
    esperado = _fuerza_bruta(capacidad, cs, destaque)
    assert abs(valor - esperado) < 1e-9
    # la cantidad devuelta es factible y da ese valor
    usado = sum(n * c.largo for n, c in zip(cant, cs))
    assert usado <= capacidad
    assert all(0 <= n <= c.cota for n, c in zip(cant, cs))
    if valor > 0:
        assert abs(sum(n * c.valor for n, c in zip(cant, cs)) - valor) < 1e-9
        sobra = capacidad - usado
        assert sobra == 0 or sobra >= destaque


@settings(max_examples=60, deadline=None)
@given(
    capacidad=st.integers(1, 50),
    cosas=st.lists(st.tuples(st.integers(1, 20), st.integers(1, 20), st.integers(0, 3)),
                   min_size=1, max_size=3),
    destaque=st.integers(0, 6),
)
def test_mejores_por_capacidad(capacidad, cosas, destaque):
    cs = [Cosa(l, float(v), c) for l, v, c in cosas]
    tabla = mejores_por_capacidad(capacidad, cs, destaque)
    for l in range(capacidad + 1):
        assert abs(tabla[l] - _fuerza_bruta(l, cs, destaque)) < 1e-9


def test_nada_entra():
    assert resolver(10, [Cosa(20, 5.0, 3)]) == (0.0, [0])
    assert resolver(0, [Cosa(1, 5.0, 3)]) == (0.0, [0])
