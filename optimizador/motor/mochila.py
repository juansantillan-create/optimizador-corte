"""Mochila 1D acotada ("knapsack"): elegir cosas de cierto largo y valor para llenar un largo
disponible, sin pasarse de la cantidad que hay de cada una.

Es la pieza básica del generador de montajes: una tira de la plancha se llena con piezas
apiladas (mochila a lo alto) y la plancha se llena con tiras (mochila a lo ancho).

Detalles:
- Programación dinámica sobre milímetros enteros, con numpy (una operación por "paquete").
- Cotas por cantidad: cada cosa se parte en paquetes de 1, 2, 4, … unidades (partición binaria),
  así cada paquete se toma o no se toma (mochila 0/1) y nunca se pasa de la cota.
- `dp[c]` = mejor valor usando **exactamente** c mm. Al final se elige el mejor c tal que el
  sobrante (capacidad − c) sea 0 o al menos el destaque mínimo.
- Empates: gana lo primero que se encontró (comparación estricta), así el resultado no depende
  de nada más que del orden de la entrada (reproducible).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

MENOS_INF = -1e300


@dataclass(frozen=True)
class Cosa:
    """Algo que se puede poner en la mochila: ocupa `largo` mm, vale `valor`, hay `cota`."""

    largo: int
    valor: float
    cota: int


def paquetes(cota: int) -> list[int]:
    """Partición binaria de una cota: 13 -> [1, 2, 4, 6]. Suman la cota y con subconjuntos de
    ellos se arma cualquier cantidad entre 0 y la cota."""
    resultado = []
    k = 1
    resto = cota
    while resto > 0:
        tomar = min(k, resto)
        resultado.append(tomar)
        resto -= tomar
        k *= 2
    return resultado


_PAQUETES = [paquetes(n) for n in range(512)]


def sobrante_valido(sobrante: int, destaque: int) -> bool:
    """Un sobrante que hay que separar con un corte tiene que medir 0 o al menos el destaque."""
    return sobrante == 0 or sobrante >= destaque


def resolver(capacidad: int, cosas: list[Cosa], destaque: int = 0) -> tuple[float, list[int]]:
    """Mochila acotada. Devuelve (mejor valor, cantidad elegida de cada cosa).

    Si no entra nada, devuelve (0.0, [0, 0, ...]).
    """
    cantidades = [0] * len(cosas)
    if capacidad <= 0 or not cosas:
        return 0.0, cantidades
    dp = np.full(capacidad + 1, MENOS_INF)
    dp[0] = 0.0
    tomados: list[tuple[int, int, int, np.ndarray]] = []  # (cosa, unidades, largo, máscara)
    for i, cosa in enumerate(cosas):
        if cosa.cota <= 0 or cosa.largo <= 0 or cosa.largo > capacidad or cosa.valor <= 0:
            continue
        maximo = min(cosa.cota, capacidad // cosa.largo)
        for unidades in _PAQUETES[maximo] if maximo < len(_PAQUETES) else paquetes(maximo):
            largo = unidades * cosa.largo
            candidato = dp[: capacidad + 1 - largo] + unidades * cosa.valor
            destino = dp[largo:]
            mascara = candidato > destino
            np.copyto(destino, candidato, where=mascara)
            tomados.append((i, unidades, largo, mascara))
    mejor_c = _mejor_capacidad(dp, capacidad, destaque)
    if mejor_c is None or dp[mejor_c] <= 0:
        return 0.0, cantidades
    c = mejor_c
    for i, unidades, largo, mascara in reversed(tomados):
        if c >= largo and mascara[c - largo]:
            cantidades[i] += unidades
            c -= largo
    return float(dp[mejor_c]), cantidades


def _mejor_capacidad(dp: np.ndarray, capacidad: int, destaque: int) -> int | None:
    """El c de mayor valor con sobrante válido; si empatan, el más chico (más compacto)."""
    c_validos = np.arange(capacidad + 1)
    sobrante = capacidad - c_validos
    ok = (sobrante == 0) | (sobrante >= destaque)
    valores = np.where(ok, dp, MENOS_INF)
    c = int(np.argmax(valores))  # argmax devuelve el primero: el c más chico entre empates
    if valores[c] <= MENOS_INF / 2:
        return None
    return c


def mejores_por_capacidad(capacidad: int, cosas: list[Cosa], destaque: int = 0) -> np.ndarray:
    """Para cada capacidad l entre 0 y `capacidad`, el mejor valor que entra en l mm respetando
    el destaque en el sobrante (sin reconstruir qué se eligió). Sirve para evaluar de una vez
    todos los anchos de tira posibles."""
    dp = np.full(capacidad + 1, MENOS_INF)
    dp[0] = 0.0
    for cosa in cosas:
        if cosa.cota <= 0 or cosa.largo <= 0 or cosa.largo > capacidad or cosa.valor <= 0:
            continue
        maximo = min(cosa.cota, capacidad // cosa.largo)
        for unidades in _PAQUETES[maximo] if maximo < len(_PAQUETES) else paquetes(maximo):
            largo = unidades * cosa.largo
            candidato = dp[: capacidad + 1 - largo] + unidades * cosa.valor
            np.maximum(dp[largo:], candidato, out=dp[largo:])
    return _con_sobrante(dp, destaque)


def _con_sobrante(dp: np.ndarray, destaque: int) -> np.ndarray:
    """mejor[l] = máx(dp[l], máx de dp[c] con c <= l - destaque); con destaque 0, el máximo
    acumulado."""
    acumulado = np.maximum.accumulate(dp)
    if destaque <= 0:
        mejor = acumulado
    else:
        mejor = dp.copy()
        if destaque < len(dp):
            mejor[destaque:] = np.maximum(dp[destaque:], acumulado[: len(dp) - destaque])
    return np.where(mejor > MENOS_INF / 2, mejor, 0.0)
