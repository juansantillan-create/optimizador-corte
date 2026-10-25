"""Árbol de guillotina: cómo guarda el motor un montaje.

Cada nodo es un rectángulo:
- `pieza`: una pieza (tipo y orientación);
- `sobrante`: un pedazo que no se usa;
- `x`: los hijos van uno al lado del otro a lo ancho (se separan con cortes verticales);
- `y`: los hijos van uno arriba del otro (se separan con cortes horizontales).

Los hijos de un nodo `x` tienen todos el alto del nodo y sus anchos suman exacto el ancho del
nodo (lo mismo, al revés, en `y`). Así el sobrante siempre está explícito.

**Medidas "agrandadas"**: adentro del motor cada pieza y la plancha se agrandan en la separación
entre piezas s (el "ancho de la sierra"). n piezas en fila cumplen n·a + (n−1)·s <= A, que es lo
mismo que n·(a+s) <= A+s. Al pasar a coordenadas reales se le resta s a cada rectángulo (la
posición no cambia). Con s = 0 las dos cosas coinciden.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Nodo:
    tipo: str  # "pieza" | "sobrante" | "x" | "y"
    ancho: int  # agrandado, a lo largo de X
    alto: int  # agrandado, a lo largo de Y
    hijos: list["Nodo"] = field(default_factory=list)
    pieza: int = -1  # índice del tipo de pieza (solo en "pieza")

    def transpuesto(self) -> "Nodo":
        """El mismo árbol con X e Y intercambiados."""
        tipo = {"x": "y", "y": "x"}.get(self.tipo, self.tipo)
        return Nodo(tipo, self.alto, self.ancho, [h.transpuesto() for h in self.hijos], self.pieza)


def pieza(indice: int, ancho: int, alto: int) -> Nodo:
    return Nodo("pieza", ancho, alto, pieza=indice)


def sobrante(ancho: int, alto: int) -> Nodo:
    return Nodo("sobrante", ancho, alto)


def fila_x(hijos: list[Nodo], ancho: int, alto: int) -> Nodo:
    """Pone los hijos uno al lado del otro en un rectángulo ancho × alto. Si un hijo es más bajo,
    se completa con sobrante arriba; lo que sobra a la derecha queda como sobrante."""
    return _apilar(hijos, ancho, alto, "x")


def columna_y(hijos: list[Nodo], ancho: int, alto: int) -> Nodo:
    """Pone los hijos uno arriba del otro en un rectángulo ancho × alto."""
    return _apilar(hijos, ancho, alto, "y")


def _apilar(hijos: list[Nodo], ancho: int, alto: int, eje: str) -> Nodo:
    completos: list[Nodo] = []
    usado = 0
    for h in hijos:
        if eje == "x":
            if h.alto < alto:
                h = Nodo("y", h.ancho, alto, [h, sobrante(h.ancho, alto - h.alto)])
            usado += h.ancho
        else:
            if h.ancho < ancho:
                h = Nodo("x", ancho, h.alto, [h, sobrante(ancho - h.ancho, h.alto)])
            usado += h.alto
        completos.append(h)
    total = ancho if eje == "x" else alto
    if usado > total:
        raise ValueError(f"los hijos no entran: {usado} > {total}")
    if usado < total:
        completos.append(sobrante(total - usado, alto) if eje == "x" else sobrante(ancho, total - usado))
    if len(completos) == 1:
        return completos[0]
    return normalizar(Nodo(eje, ancho, alto, completos))


def normalizar(nodo: Nodo) -> Nodo:
    """Junta niveles iguales seguidos (un `x` adentro de un `x`) y sobrantes vecinos."""
    if nodo.tipo not in ("x", "y"):
        return nodo
    hijos: list[Nodo] = []
    for h in nodo.hijos:
        h = normalizar(h)
        if h.tipo == nodo.tipo:
            hijos.extend(h.hijos)
        else:
            hijos.append(h)
    juntos: list[Nodo] = []
    for h in hijos:
        if juntos and h.tipo == "sobrante" and juntos[-1].tipo == "sobrante":
            previo = juntos.pop()
            if nodo.tipo == "x":
                h = sobrante(previo.ancho + h.ancho, h.alto)
            else:
                h = sobrante(h.ancho, previo.alto + h.alto)
        juntos.append(h)
    if len(juntos) == 1:
        return juntos[0]
    if all(h.tipo == "sobrante" for h in juntos):
        return sobrante(nodo.ancho, nodo.alto)
    return Nodo(nodo.tipo, nodo.ancho, nodo.alto, juntos)


def contar(nodo: Nodo, cantidades: dict[int, int] | None = None) -> dict[int, int]:
    """Cuántas piezas de cada tipo tiene el árbol."""
    if cantidades is None:
        cantidades = {}
    if nodo.tipo == "pieza":
        cantidades[nodo.pieza] = cantidades.get(nodo.pieza, 0) + 1
    for h in nodo.hijos:
        contar(h, cantidades)
    return cantidades


def hojas(nodo: Nodo, x: int = 0, y: int = 0):
    """Recorre el árbol y devuelve (nodo, x, y) de cada pieza y sobrante, en medidas agrandadas."""
    if nodo.tipo in ("pieza", "sobrante"):
        yield nodo, x, y
        return
    for h in nodo.hijos:
        yield from hojas(h, x, y)
        if nodo.tipo == "x":
            x += h.ancho
        else:
            y += h.alto


@dataclass(frozen=True)
class Corte:
    """Un corte de guillotina en coordenadas reales (mm, origen abajo a la izquierda).

    `nivel` 1 = corte de lado a lado de la plancha, 2 = adentro de una tira, etc.
    `vertical` = la línea de corte es vertical (separa cosas a lo ancho).
    `posicion` = la X (o la Y) donde empieza el corte; `desde`/`hasta` = el largo de la línea.
    """

    nivel: int
    vertical: bool
    posicion: int
    desde: int
    hasta: int


def cortes(nodo: Nodo, separacion: int, x: int = 0, y: int = 0, nivel: int = 1) -> list[Corte]:
    """Los cortes del árbol, ordenados: primero los de nivel 1 (de lado a lado de la plancha)."""
    lista: list[Corte] = []
    _cortes(nodo, separacion, x, y, nivel, lista)
    lista.sort(key=lambda c: (c.nivel, c.desde if c.vertical else c.posicion,
                              c.posicion if c.vertical else c.desde))
    return lista


def _cortes(nodo: Nodo, s: int, x: int, y: int, nivel: int, lista: list[Corte]) -> None:
    if nodo.tipo not in ("x", "y"):
        return
    pos_x, pos_y = x, y
    for i, h in enumerate(nodo.hijos):
        if i > 0:
            # El corte va donde termina (en medidas reales) el hijo anterior.
            if nodo.tipo == "x":
                lista.append(Corte(nivel, True, pos_x - s, y, y + nodo.alto - s))
            else:
                lista.append(Corte(nivel, False, pos_y - s, x, x + nodo.ancho - s))
        _cortes(h, s, pos_x, pos_y, nivel + 1, lista)
        if nodo.tipo == "x":
            pos_x += h.ancho
        else:
            pos_y += h.alto


def profundidad(nodo: Nodo) -> int:
    """Cantidad de niveles de corte (etapas) del árbol."""
    if nodo.tipo not in ("x", "y"):
        return 0
    return 1 + max(profundidad(h) for h in nodo.hijos)
