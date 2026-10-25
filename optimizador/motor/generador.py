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
                 max_alternancia: int = 2, presupuesto_alternancia: int = 120):
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
        self._limite_alternancia = 0
        self.llamadas = 0  # cantidad de trabajo hecho (para medir esfuerzo, no por reloj)
        self._cache: dict = {}
        self._valores_cache: tuple | None = None
        self._entran: dict = {}
        # Las dos listas de orientaciones (normal y transpuesta), calculadas una sola vez: el
        # caché las distingue por cuál de las dos es.
        self._normal = tuple(t.orientaciones for t in tipos)
        self._transpuesta = tuple(tuple((b, a) for a, b in t.orientaciones) for t in tipos)

    # ------------------------------------------------------------------ API
    def generar(self, valores: list[float], cotas: list[int],
                direcciones: tuple[str, ...] = ("x", "y")) -> list[Nodo]:
        """Devuelve los montajes encontrados (uno por orientación del primer corte que dio algo),
        el mejor primero."""
        clave = tuple(valores)
        if clave != self._valores_cache:
            self._cache = {}
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
        maximos = []
        for c, ors in zip(cotas, orients):
            entra = max(((A // a) * (B // b) for a, b in ors if a <= A and b <= B), default=0)
            maximos.append(min(c, entra))
        clave = ("plancha", orients is self._transpuesta, A, B, prof, tuple(maximos))
        guardado = self._cache.get(clave)
        if guardado is None:
            prueba = list(cotas)
            nodo = self._plancha_calcular(A, B, orients, valores, prueba, prof)
            consumo = {i: c - q for i, (c, q) in enumerate(zip(cotas, prueba)) if c != q}
            guardado = (nodo, consumo)
            self._cache[clave] = guardado
        nodo, consumo = guardado
        for i, n in consumo.items():
            cotas[i] -= n
        return nodo

    def _plancha_calcular(self, A: int, B: int, orients, valores, cotas: list[int], prof: int) -> Nodo | None:
        inicial = list(cotas)
        puestas = self._solo_tiras(A, B, orients, valores, cotas, None if prof == 0 else 12)
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
        anchos = sorted({a for t, ors in enumerate(orients) if cotas[t] > 0 and valores[t] > 0
                         for a, b in ors if a <= A and b <= B})
        if not anchos:
            return None
        if max_anchos is not None and len(anchos) > max_anchos:
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
        clave_entran = (orients is self._transpuesta, l, B)
        entran = self._entran.get(clave_entran)
        if entran is None:
            entran = []
            for t, ors in enumerate(orients):
                maximo = max(((l // a) * (B // b) for a, b in ors if a <= l and b <= B), default=0)
                if maximo > 0:
                    entran.append((t, maximo))
            self._entran[clave_entran] = entran
        clave = (clave_entran, tuple(min(cotas[t], m) for t, m in entran))
        if clave in self._cache:
            return self._cache[clave]
        resultado = self._tira_calcular(l, B, orients, valores, cotas)
        self._cache[clave] = resultado
        return resultado

    def _tira_calcular(self, l: int, B: int, orients, valores, cotas: list[int]) -> _Tira | None:
        self.llamadas += 1
        d = self.destaque
        # Cada renglón: (piezas [(tipo, a, b)], alto). Pueden ser k piezas iguales una al lado de
        # la otra, o piezas distintas de la misma altura (mochila a lo ancho).
        renglones: list[tuple[tuple[tuple[int, int, int], ...], int]] = []
        cosas: list[Cosa] = []
        por_alto: dict[int, list[tuple[int, int]]] = {}
        for t, ors in enumerate(orients):
            if cotas[t] <= 0 or valores[t] <= 0:
                continue
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
            for transponer in (False, True):
                prueba = list(cotas)
                if transponer:
                    sub = self._plancha(nodo.alto, nodo.ancho, self._otra(orients), valores, prueba,
                                        self.max_alternancia)
                    sub = sub.transpuesto() if sub is not None else None
                else:
                    sub = self._plancha(nodo.ancho, nodo.alto, orients, valores, prueba,
                                        self.max_alternancia)
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

