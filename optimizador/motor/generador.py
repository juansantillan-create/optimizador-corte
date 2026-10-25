"""Generador de montajes de guillotina por etapas (estilo Gilmore–Gomory).

Dado un valor por tipo de pieza y cuántas quedan de cada una (la cota), arma un montaje de una
plancha que junte la mayor cantidad de valor posible. Lo usan:
- la heurística secuencial (valor = área de la pieza);
- la generación de columnas (valor = "precio" de cada pieza que da la relajación lineal).

Cómo arma el montaje (primer corte vertical; la otra orientación se hace transponiendo):
1. **Tiras**: la plancha se corta de lado a lado en tiras verticales. El ancho de cada tira es
   el ancho de alguna pieza.
2. **Adentro de la tira**: se apilan "renglones" a lo alto. Un renglón es una pieza sola o k
   piezas iguales una al lado de la otra. Se elige con una mochila a lo alto (`mochila.py`).
3. **Las tiras en la plancha**: otra mochila, a lo ancho, elige qué tiras poner.
4. Como las cotas son por tipo de pieza, se arma tira por tira descontando lo que ya se usó.
5. **Relleno**: cada sobrante grande se vuelve a llenar con lo que quede (eso agrega etapas y
   permite renglones con piezas distintas).

Todo en medidas agrandadas (ver `arbol.py`). El destaque mínimo se respeta en cada sobrante:
cada pedazo que sobra mide 0 o al menos el destaque en los dos sentidos.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import arbol
from .arbol import Nodo
from .mochila import Cosa, resolver


@dataclass(frozen=True)
class TipoGen:
    """Un tipo de pieza para el generador: las orientaciones permitidas, agrandadas, (dx, dy)."""

    orientaciones: tuple[tuple[int, int], ...]


def sobrante_ok(ancho: int, alto: int, destaque: int) -> bool:
    """Un pedazo que sobra tiene que medir 0 o al menos el destaque en los dos sentidos."""
    if ancho <= 0 or alto <= 0 or destaque <= 0:
        return True
    return ancho >= destaque and alto >= destaque


def sobrantes_ok(nodo: Nodo, destaque: int) -> bool:
    if destaque <= 0:
        return True
    return all(sobrante_ok(h.ancho, h.alto, destaque)
               for h, _, _ in arbol.hojas(nodo) if h.tipo == "sobrante")


TIPOS_VECTORIAL = 64
# Tope del caché (en "casilleros" guardados: un par tipo-cantidad cuenta uno). Al llegar, se vacía
# entero: así la memoria queda acotada (< 500 MB en el peor caso) y el resultado sigue siendo el
# mismo en cualquier PC (no depende del reloj ni de la memoria libre).
TOPE_CACHE = 1_500_000


@dataclass
class _Tira:
    valor: float
    ancho: int
    nodo: Nodo
    usadas: dict[int, int]


class Generador:
    """Arma montajes para una medida de plancha (agrandada) y un juego de tipos de pieza."""

    def __init__(self, ancho: int, alto: int, tipos: list[TipoGen], destaque: int = 0,
                 relleno: bool = True, max_por_renglon: int = 4, max_relleno: int = 3,
                 max_alternancia: int = 2, presupuesto_alternancia: int = 120,
                 max_anchos: int | None = None, max_tipos_tira: int | None = None,
                 max_anchos_adentro: int = 12):
        self.ancho = ancho
        self.alto = alto
        self.tipos = tipos
        self.destaque = destaque
        self.relleno = relleno
        self.max_por_renglon = max_por_renglon
        self.max_relleno = max_relleno
        self.max_alternancia = max_alternancia
        # Trabajo máximo (tiras calculadas) que se gasta en la alternancia por cada montaje: es
        # una cantidad, no un tiempo, así el resultado es el mismo en cualquier PC.
        self.presupuesto_alternancia = presupuesto_alternancia
        # Con muchas medidas distintas, cuántos anchos de tira se prueban en la plancha entera (los
        # de las piezas de más valor). None = todos.
        self.max_anchos = max_anchos
        self.max_anchos_adentro = max_anchos_adentro  # ídem adentro de un corte (alternancia, relleno)
        # Con muchas medidas distintas, cuántos tipos de pieza se consideran adentro de una tira (los
        # de más valor que entran). Acota el tiempo y la memoria. None = todos.
        self.max_tipos_tira = max_tipos_tira
        self._limite_alternancia = 0
        self.llamadas = 0  # cantidad de trabajo hecho (para medir esfuerzo, no por reloj)
        self._cache: dict = {}
        self._tamano_cache = 0
        self._valores_cache: tuple | None = None
        self._orden_valor: list[int] | None = None
        # Las dos listas de orientaciones (normal y transpuesta), calculadas una sola vez: el
        # caché las distingue por cuál de las dos es.
        self._normal = tuple(t.orientaciones for t in tipos)
        self._transpuesta = tuple(tuple((b, a) for a, b in t.orientaciones) for t in tipos)
        # Con muchos tipos, los filtros "qué entra en este rectángulo" se hacen con numpy (da lo
        # mismo que el código simple, más rápido). Cada tipo: primera y última orientación.
        self._vectorial = len(tipos) > TIPOS_VECTORIAL
        self._arreglos: dict[bool, tuple] = {}
        self._activos_valor = None  # valores > 0 (numpy)
        self._orden_np = None

    # ------------------------------------------------------------------ API
    def generar(self, valores: list[float], cotas: list[int],
                direcciones: tuple[str, ...] = ("x", "y")) -> list[Nodo]:
        """Devuelve los montajes encontrados (uno por orientación del primer corte que dio algo),
        el mejor primero."""
        clave = tuple(valores)
        if clave != self._valores_cache:
            self._cache = {}
            self._tamano_cache = 0
            self._orden_valor = None  # los tipos de más valor a menos (se arma al usarlo)
            self._orden_np = None
            self._activos_valor = np.asarray(valores, dtype=float) > 0 if self._vectorial else None
            self._valores_cache = clave
        resultados: list[tuple[float, int, Nodo]] = []
        for orden, direccion in enumerate(direcciones):
            self._limite_alternancia = self.llamadas + self.presupuesto_alternancia
            nodo = self._generar_en(direccion, self.ancho, self.alto, valores, list(cotas),
                                    profundidad=0)
            if nodo is not None:
                valor = self._valor(nodo, valores)
                resultados.append((valor, orden, nodo))
        resultados.sort(key=lambda r: (-r[0], r[1]))
        return [r[2] for r in resultados]

    def mejor(self, valores: list[float], cotas: list[int]) -> Nodo | None:
        candidatos = self.generar(valores, cotas)
        return candidatos[0] if candidatos else None

    # ------------------------------------------------------------- interno
    @staticmethod
    def _valor(nodo: Nodo, valores: list[float]) -> float:
        return sum(valores[t] * n for t, n in arbol.contar(nodo).items())

    def _orientaciones(self, transpuesto: bool) -> tuple[tuple[tuple[int, int], ...], ...]:
        return self._transpuesta if transpuesto else self._normal

    def _otra(self, orients):
        return self._normal if orients is self._transpuesta else self._transpuesta

    def _generar_en(self, direccion: str, ancho: int, alto: int, valores: list[float],
                    cotas: list[int], profundidad: int) -> Nodo | None:
        """Primer corte vertical ("x": tiras verticales) u horizontal ("y"). Para "y" se
        transpone el problema, se resuelve igual y se vuelve a transponer."""
        transpuesto = direccion == "y"
        orients = self._orientaciones(transpuesto)
        A, B = (alto, ancho) if transpuesto else (ancho, alto)
        nodo = self._plancha(A, B, orients, valores, cotas)
        if nodo is None:
            return None
        if self.relleno and profundidad == 0:
            nodo = self._rellenar(nodo, orients, valores, cotas)
        if not sobrantes_ok(nodo, self.destaque):
            return None
        return nodo.transpuesto() if transpuesto else nodo

    def _plancha(self, A: int, B: int, orients, valores, cotas: list[int], prof: int = 0) -> Nodo | None:
        """Llena un rectángulo A × B. Modifica `cotas` (descuenta lo usado).

        Prueba tiras verticales solas y, además, "unas tiras verticales y el resto con cortes
        horizontales" (el resto se llena con este mismo método, transpuesto). Así salen montajes
        con más etapas, como cuando una pieza larga cruza por debajo de dos columnas.
        """
        # Cota segura de cuántas entran de cada tipo (por área): mezclando orientaciones pueden
        # entrar más que en una grilla de una sola orientación, así que esa no sirve para el caché.
        if self._vectorial:
            a1, b1, a2, b2 = self._arreglo(orients)
            m1 = np.where((a1 <= A) & (b1 <= B), (A * B) // (a1 * b1), 0)
            m2 = np.where((a2 <= A) & (b2 <= B), (A * B) // (a2 * b2), 0)
            maximo = np.minimum(np.asarray(cotas, dtype=np.int64), np.maximum(m1, m2))
            indices = np.nonzero(maximo > 0)[0]
            estado = tuple(zip(indices.tolist(), maximo[indices].tolist()))
        else:
            maximos = []
            for c, ors in zip(cotas, orients):
                entra = max(((A * B) // (a * b) for a, b in ors if a <= A and b <= B), default=0)
                maximos.append(min(c, entra))
            estado = tuple((i, m) for i, m in enumerate(maximos) if m > 0)
        clave = ("plancha", orients is self._transpuesta, A, B, prof)
        guardado = self._reusar(clave, estado, cotas)
        if guardado is None:
            prueba = list(cotas)
            nodo = self._plancha_calcular(A, B, orients, valores, prueba, prof)
            consumo = {i: c - q for i, (c, q) in enumerate(zip(cotas, prueba)) if c != q}
            guardado = (nodo, consumo)
            self._guardar(clave, estado, guardado)
        nodo, consumo = guardado
        for i, n in consumo.items():
            cotas[i] -= n
        return nodo

    def _reusar(self, clave, estado: tuple, cotas: list[int]):
        """Lo guardado para `clave` que sirva con estas cotas, o None.

        Con los mismos valores, lo que se armó con más piezas disponibles sigue sirviendo con
        menos, mientras alcancen las piezas que usa: con menos piezas no se puede armar nada
        mejor que eso con este mismo método. Así la heurística secuencial, que va gastando
        piezas, no recalcula todo en cada plancha."""
        for guardado_estado, guardado in self._cache.get(clave, ()):
            if guardado_estado == estado:
                return guardado
            antes = dict(guardado_estado)
            if all(m <= antes.get(i, 0) for i, m in estado):
                nodo, consumo = guardado
                if nodo is None or all(cotas[i] >= n for i, n in consumo.items()):
                    return guardado
        return None

    def _guardar(self, clave, estado: tuple, guardado) -> None:
        self._contar_cache(len(estado) + 8)
        lista = self._cache.setdefault(clave, [])
        lista.insert(0, (estado, guardado))
        del lista[3:]

    def _contar_cache(self, tamano: int) -> None:
        self._tamano_cache += tamano
        if self._tamano_cache > TOPE_CACHE:
            self._cache.clear()
            self._tamano_cache = tamano

    def _plancha_calcular(self, A: int, B: int, orients, valores, cotas: list[int], prof: int) -> Nodo | None:
        inicial = list(cotas)
        puestas = self._solo_tiras(A, B, orients, valores, cotas,
                                   self.max_anchos if prof == 0 else self.max_anchos_adentro)
        mejor_nodo = arbol.fila_x(puestas, A, B) if puestas else None
        mejor_valor = self._valor(mejor_nodo, valores) if mejor_nodo is not None else 0.0
        mejor_cotas = list(cotas)
        if prof < self.max_alternancia and self.llamadas < self._limite_alternancia:
            prefijo: list[Nodo] = []
            restantes = list(inicial)
            usado = 0
            valor_prefijo = 0.0
            max_prefijo = (4, 2, 1)[min(prof, 2)]
            for j in range(min(len(puestas or []), max_prefijo) + 1):
                resto = A - usado
                if self.llamadas >= self._limite_alternancia:
                    break
                if (j > 0 or prof > 0) and resto > 0:
                    prueba = list(restantes)
                    sub = self._plancha(B, resto, self._otra(orients), valores, prueba, prof + 1)
                    if sub is not None:
                        sub = sub.transpuesto()
                        valor = valor_prefijo + self._valor(sub, valores)
                        if valor > mejor_valor + 1e-9:
                            candidato = arbol.fila_x(prefijo + [sub], A, B)
                            if sobrantes_ok(candidato, self.destaque):
                                mejor_nodo, mejor_valor, mejor_cotas = candidato, valor, prueba
                if j < len(puestas or []):
                    tira = puestas[j]
                    prefijo.append(tira)
                    usado += tira.ancho
                    for i, n in arbol.contar(tira).items():
                        restantes[i] -= n
                    valor_prefijo += self._valor(tira, valores)
        cotas[:] = mejor_cotas
        return mejor_nodo

    def _solo_tiras(self, A: int, B: int, orients, valores, cotas: list[int],
                    max_anchos: int | None = None) -> list[Nodo] | None:
        """Tiras verticales de lado a lado. Modifica `cotas`. Devuelve las tiras puestas.
        Con `max_anchos`, solo se prueban los anchos de las piezas de más valor."""
        d = self.destaque
        if self._vectorial:
            anchos = self._anchos_vectorial(A, B, orients, valores, cotas, max_anchos)
            if not anchos:
                return None
        else:
            anchos = sorted({a for t, ors in enumerate(orients) if cotas[t] > 0 and valores[t] > 0
                             for a, b in ors if a <= A and b <= B})
            if not anchos:
                return None
        if not self._vectorial and max_anchos is not None and len(anchos) > max_anchos:
            valor_ancho: dict[int, float] = {}
            for t, ors in enumerate(orients):
                if cotas[t] > 0 and valores[t] > 0:
                    for a, b in ors:
                        if a <= A and b <= B:
                            valor_ancho[a] = max(valor_ancho.get(a, 0.0), valores[t])
            anchos = sorted(sorted(valor_ancho, key=lambda a: (-valor_ancho[a], a))[:max_anchos])
        # 1) Cada ancho de tira, con todas las cotas: valor y composición.
        tiras: dict[int, _Tira] = {}
        for l in anchos:
            tira = self._tira(l, B, orients, valores, cotas)
            if tira is not None:
                tiras[l] = tira
        if not tiras:
            return None
        # 2) Mochila a lo ancho para elegir qué tiras poner.
        lista = sorted(tiras.values(), key=lambda t: t.ancho)
        cosas = []
        for t in lista:
            cota = min((cotas[i] // n for i, n in t.usadas.items() if n > 0), default=0)
            cosas.append(Cosa(t.ancho, t.valor, max(cota, 0)))
        _, cantidades = resolver(A, cosas, d)
        elegidas: list[int] = []
        for t, n in zip(lista, cantidades):
            elegidas.extend([t.ancho] * n)
        # Las más "densas" (valor por mm) primero; así, si se acaban piezas, las pierden las peores.
        elegidas.sort(key=lambda l: (-tiras[l].valor / l, -l))
        # 3) Armar tira por tira descontando lo usado. Si la tira elegida todavía entra con lo
        #    que queda, sigue siendo la mejor de ese ancho y se usa tal cual.
        puestas: list[Nodo] = []
        libre = A
        for l in elegidas:
            if l > libre:
                continue
            tira = tiras[l]
            if any(cotas[i] < n for i, n in tira.usadas.items()):
                tira = self._tira(l, B, orients, valores, cotas)
                if tira is None:
                    continue
            puestas.append(tira.nodo)
            libre -= l
            for i, n in tira.usadas.items():
                cotas[i] -= n
        # 4) Si queda ancho, seguir con la mejor tira que entre (goloso). Lo que dio cada ancho
        #    con todas las cotas es una cota superior: se prueban de la más prometedora a la
        #    menos y se corta cuando ya no puede ganar.
        prometedoras = sorted(tiras.values(), key=lambda t: (-t.valor / t.ancho, t.ancho))
        while libre > 0:
            mejor: _Tira | None = None
            for cand in prometedoras:
                l = cand.ancho
                if mejor is not None and cand.valor / l <= mejor.valor / mejor.ancho + 1e-12:
                    break
                if l > libre or not sobrante_ok(libre - l, B, d):
                    continue
                tira = cand
                if any(cotas[i] < n for i, n in tira.usadas.items()):
                    tira = self._tira(l, B, orients, valores, cotas)
                    if tira is None:
                        continue
                if mejor is None or tira.valor / l > mejor.valor / mejor.ancho + 1e-12:
                    mejor = tira
            if mejor is None:
                break
            puestas.append(mejor.nodo)
            libre -= mejor.ancho
            for i, n in mejor.usadas.items():
                cotas[i] -= n
        if not puestas:
            return None
        if libre > 0 and not sobrante_ok(libre, B, d):
            # El sobrante final quedó más angosto que el destaque: se saca la última tira.
            ultima = puestas.pop()
            libre += ultima.ancho
            for i, n in arbol.contar(ultima).items():
                cotas[i] += n
            if not puestas or not sobrante_ok(libre, B, d):
                return None
        return puestas

    def _tira(self, l: int, B: int, orients, valores, cotas: list[int]) -> _Tira | None:
        """La mejor tira vertical de ancho l y alto B: renglones apilados."""
        # Caché: el resultado depende de las cotas solo hasta lo máximo que entra en la tira.
        candidatos = self._candidatos(l, B, orients, valores, cotas)
        estado = tuple((t, min(cotas[t], m)) for t, m in candidatos)
        clave = ("tira", orients is self._transpuesta, l, B)
        guardado = self._reusar_tira(clave, estado, cotas)
        if guardado is not None:
            return guardado[0]
        resultado = self._tira_calcular(l, B, orients, valores, cotas, [t for t, _ in candidatos])
        self._guardar(clave, estado, (resultado, resultado.usadas if resultado is not None else {}))
        return resultado

    def _candidatos(self, l: int, B: int, orients, valores, cotas: list[int]) -> list[tuple[int, int]]:
        """Los tipos que quedan y entran en una tira l × B, de más valor a menos, con cuántos
        entran como mucho (cota segura por área, igual que en `_plancha`). Con `max_tipos_tira`,
        solo los primeros."""
        if self._orden_valor is None:
            self._orden_valor = sorted(range(len(valores)), key=lambda t: (-valores[t], t))
        salida = []
        if self._vectorial:
            if self._orden_np is None:
                self._orden_np = np.asarray(self._orden_valor, dtype=np.int64)
            a1, b1, a2, b2 = self._arreglo(orients)
            entra = (((a1 <= l) & (b1 <= B)) | ((a2 <= l) & (b2 <= B))) & self._activos_valor & \
                (np.asarray(cotas, dtype=np.int64) > 0)
            elegidos = self._orden_np[entra[self._orden_np]]
            if self.max_tipos_tira is not None:
                elegidos = elegidos[:self.max_tipos_tira]
            for t in elegidos.tolist():
                salida.append((t, max((l * B) // (a * b) for a, b in orients[t] if a <= l and b <= B)))
            return salida
        for t in self._orden_valor:
            if cotas[t] <= 0 or valores[t] <= 0:
                continue
            maximo = max(((l * B) // (a * b) for a, b in orients[t] if a <= l and b <= B), default=0)
            if maximo > 0:
                salida.append((t, maximo))
                if self.max_tipos_tira is not None and len(salida) >= self.max_tipos_tira:
                    break
        return salida

    def _arreglo(self, orients) -> tuple:
        """Las medidas de cada tipo en numpy: (ancho y alto de la primera orientación, de la última)."""
        clave = orients is self._transpuesta
        arreglo = self._arreglos.get(clave)
        if arreglo is None:
            arreglo = tuple(np.asarray([f(ors) for ors in orients], dtype=np.int64)
                            for f in (lambda o: o[0][0], lambda o: o[0][1], lambda o: o[-1][0], lambda o: o[-1][1]))
            self._arreglos[clave] = arreglo
        return arreglo

    def _anchos_vectorial(self, A: int, B: int, orients, valores, cotas: list[int],
                          max_anchos: int | None) -> list[int]:
        """Lo mismo que el código simple de `_solo_tiras`: los anchos de tira posibles y, con
        `max_anchos`, los de las piezas de más valor (a igual valor, el más angosto)."""
        a1, b1, a2, b2 = self._arreglo(orients)
        activos = self._activos_valor & (np.asarray(cotas, dtype=np.int64) > 0)
        f1 = activos & (a1 <= A) & (b1 <= B)
        f2 = activos & (a2 <= A) & (b2 <= B)
        anchos = np.concatenate([a1[f1], a2[f2]])
        if anchos.size == 0:
            return []
        distintos = np.unique(anchos)
        if max_anchos is None or distintos.size <= max_anchos:
            return distintos.tolist()
        v = np.asarray(valores, dtype=float)
        vals = np.concatenate([v[f1], v[f2]])
        orden = np.lexsort((anchos, -vals))
        vistos: set[int] = set()
        primeros: list[int] = []
        for w in anchos[orden].tolist():
            if w not in vistos:
                vistos.add(w)
                primeros.append(w)
                if len(primeros) >= max_anchos:
                    break
        return sorted(primeros)

    def _reusar_tira(self, clave, estado: tuple, cotas: list[int]):
        """Como `_reusar`, para una tira: sirve lo guardado con los mismos tipos candidatos y, de
        cada uno, la misma cantidad o más (si alcanzan las piezas que usa)."""
        tipos = [t for t, _ in estado]
        for guardado_estado, guardado in self._cache.get(clave, ()):
            if guardado_estado == estado:
                return guardado
            if len(guardado_estado) == len(estado) and [t for t, _ in guardado_estado] == tipos and \
                    all(c <= g for (_, c), (_, g) in zip(estado, guardado_estado)):
                nodo, consumo = guardado
                if nodo is None or all(cotas[i] >= n for i, n in consumo.items()):
                    return guardado
        return None

    def _tira_calcular(self, l: int, B: int, orients, valores, cotas: list[int],
                       candidatos: list[int]) -> _Tira | None:
        self.llamadas += 1
        d = self.destaque
        # Cada renglón: (piezas [(tipo, a, b)], alto). Pueden ser k piezas iguales una al lado de
        # la otra, o piezas distintas de la misma altura (mochila a lo ancho).
        renglones: list[tuple[tuple[tuple[int, int, int], ...], int]] = []
        cosas: list[Cosa] = []
        por_alto: dict[int, list[tuple[int, int]]] = {}
        for t in sorted(candidatos):
            ors = orients[t]
            for a, b in ors:
                if a > l or b > B:
                    continue
                por_alto.setdefault(b, []).append((t, a))
                kmax = min(cotas[t], l // a)
                ks = sorted({k for k in range(1, min(kmax, self.max_por_renglon) + 1)}
                            | {kmax, min(cotas[t], kmax)})
                for k in ks:
                    if k <= 0 or not sobrante_ok(l - k * a, b, d):
                        continue
                    renglones.append((((t, a, b),) * k, b))
                    cosas.append(Cosa(b, k * valores[t], min(cotas[t] // k, B // b)))
        # Renglones mixtos: piezas distintas con la misma altura, llenando el ancho de la tira.
        for b, lista in sorted(por_alto.items()):
            if len({t for t, _ in lista}) < 2:
                continue
            # El renglón depende solo del ancho, del alto y de las cotas (no del alto de la tira):
            # se guarda para reusarlo en tiras de otro alto.
            clave = ("mixto", l, b, tuple((t, a, min(cotas[t], l // a)) for t, a in lista))
            guardado = self._cache.get(clave)
            if guardado is None:
                valor, cant = resolver(l, [Cosa(a, valores[t], min(cotas[t], l // a)) for t, a in lista], d)
                guardado = (valor, tuple(pz for (t, a), n in zip(lista, cant) for pz in [(t, a, b)] * n))
                self._contar_cache(len(lista) + 8)
                self._cache[clave] = guardado
            valor, piezas = guardado
            if valor <= 0 or len({pz[0] for pz in piezas}) < 2:
                continue
            if not sobrante_ok(l - sum(a for _, a, _ in piezas), b, d):
                continue
            uso: dict[int, int] = {}
            for tt, _, _ in piezas:
                uso[tt] = uso.get(tt, 0) + 1
            cota = min([B // b] + [cotas[tt] // n for tt, n in uso.items()])
            if cota > 0:
                renglones.append((piezas, b))
                cosas.append(Cosa(b, valor, cota))
        if not cosas:
            return None
        _, cantidades = resolver(B, cosas, d)
        # Arreglar si dos renglones con el mismo tipo se pasaron de la cota entre los dos.
        usadas: dict[int, int] = {}
        elegidos: list[tuple[tuple[tuple[int, int, int], ...], int]] = []
        densidad = [sum(valores[pz[0]] for pz in r[0]) / r[1] for r in renglones]
        for i in sorted(range(len(renglones)), key=lambda i: (-densidad[i], i)):
            piezas, b = renglones[i]
            uso: dict[int, int] = {}
            for tt, _, _ in piezas:
                uso[tt] = uso.get(tt, 0) + 1
            for _ in range(cantidades[i]):
                if all(usadas.get(tt, 0) + n <= cotas[tt] for tt, n in uso.items()):
                    for tt, n in uso.items():
                        usadas[tt] = usadas.get(tt, 0) + n
                    elegidos.append(renglones[i])
        if not elegidos:
            return None
        alto_usado = sum(b for _, b in elegidos)
        if not sobrante_ok(l, B - alto_usado, d):
            return None
        # Los renglones más altos abajo (el sobrante queda arriba, como Corte Certo).
        elegidos.sort(key=lambda r: (-r[1], r[0]))
        hijos = [arbol.fila_x([arbol.pieza(tt, a, bb) for tt, a, bb in piezas], l, b)
                 for piezas, b in elegidos]
        nodo = arbol.columna_y(hijos, l, B)
        valor = sum(valores[pz[0]] for piezas, _ in elegidos for pz in piezas)
        return _Tira(valor, l, nodo, usadas)

    def _rellenar(self, nodo: Nodo, orients, valores, cotas: list[int], nivel: int = 0) -> Nodo:
        """Vuelve a llenar los sobrantes con las piezas que quedan (modifica `cotas`). Lo que se
        pone en un sobrante se vuelve a rellenar, hasta `max_relleno` niveles."""
        if not any(c > 0 for c in cotas):
            return nodo
        if nodo.tipo == "sobrante":
            hay = any(cotas[t] > 0 and valores[t] > 0 and a <= nodo.ancho and b <= nodo.alto
                      for t, ors in enumerate(orients) for a, b in ors)
            if not hay:
                return nodo
            mejor: Nodo | None = None
            mejor_valor = 0.0
            # Al rellenar no se alterna más (ya se está adentro de un corte) y se prueban pocos
            # anchos de tira: profundidad al menos 1.
            prof = max(self.max_alternancia, 1)
            for transponer in (False, True):
                prueba = list(cotas)
                if transponer:
                    sub = self._plancha(nodo.alto, nodo.ancho, self._otra(orients), valores, prueba, prof)
                    sub = sub.transpuesto() if sub is not None else None
                else:
                    sub = self._plancha(nodo.ancho, nodo.alto, orients, valores, prueba, prof)
                if sub is None or not sobrantes_ok(sub, self.destaque):
                    continue
                v = self._valor(sub, valores)
                if v > mejor_valor + 1e-12:
                    mejor, mejor_valor = sub, v
            if mejor is None:
                return nodo
            for t, n in arbol.contar(mejor).items():
                cotas[t] -= n
            if nivel + 1 < self.max_relleno:
                mejor = self._rellenar(mejor, orients, valores, cotas, nivel + 1)
            return mejor
        if nodo.tipo == "pieza":
            return nodo
        hijos = [self._rellenar(h, orients, valores, cotas, nivel) for h in nodo.hijos]
        return arbol.normalizar(Nodo(nodo.tipo, nodo.ancho, nodo.alto, hijos))

