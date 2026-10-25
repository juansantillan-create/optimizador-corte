"""Cálculo de un material: cuántas planchas, qué montajes y cuántas veces cada uno.

Pasos (brief §6.2 y §6.3):
1. **Tipos de pieza**: se juntan las piezas iguales (misma medida de corte y misma regla de giro).
2. **Heurística secuencial** (rápida, siempre disponible): arma el mejor montaje para lo que
   falta, lo repite todas las veces que se pueda y sigue con el resto. Se prueba con algunas
   variantes del "valor" de cada pieza y se queda con la mejor.
3. **Generación de columnas**: la relajación lineal (HiGHS, de scipy) da un precio por tipo de
   pieza; con esos precios el generador busca montajes mejores, hasta que no aparecen más.
4. **Programación entera** sobre los montajes encontrados: la menor cantidad de m² de plancha.
   Entre soluciones con los mismos m² gana la de menos montajes distintos.
5. **Cantidades exactas**: las piezas de más se sacan (quedan como sobrante), empezando por las
   planchas menos llenas.
6. **Juntar el sobrante**: se reacomodan las planchas menos llenas para que el sobrante quede
   junto en la última, sin agregar planchas ni montajes.

El trabajo se limita por cantidad (iteraciones, nodos), no por reloj, para que el mismo caso dé
lo mismo en cualquier PC. El reloj es solo un límite de seguridad (con aviso si se usa).
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np

from . import arbol
from .arbol import Nodo
from .generador import Generador, TipoGen


# ----------------------------------------------------------------------------- datos
@dataclass
class Tipo:
    """Un tipo de pieza: todas las piezas iguales de un material."""

    indice: int
    ancho: int  # medida del proyecto (sin constantes): para m² y perímetro
    largo: int
    ancho_corte: int  # con constante y sobremedida: lo que se acomoda
    largo_corte: int
    cantidad: int
    rota: bool
    orientaciones: tuple[tuple[int, int], ...]  # reales (dx, dy) permitidas
    items: list[tuple[str, int]] = field(default_factory=list)  # (ítem, cantidad)
    mm2_presupuesto: int = 0  # con las medidas del presupuesto (sin +3 ni constantes)
    medida_presupuesto: tuple[int, int] = (0, 0)  # ancho × largo del primer renglón, como se cargó

    @property
    def etiqueta(self) -> str:
        return "+".join(i for i, _ in self.items)


@dataclass
class Stock:
    """Una medida de plancha habilitada del material."""

    indice: int  # posición en material.planchas
    ancho: int  # útil, real
    largo: int
    costo: float  # m² de plancha útil


@dataclass
class Uso:
    """Un montaje y cuántas planchas se cortan así."""

    stock: int  # índice en la lista de stocks
    nodo: Nodo  # en medidas agrandadas
    repeticiones: int
    cuenta: tuple[int, ...]  # piezas de cada tipo en UNA plancha


@dataclass
class Solucion:
    usos: list[Uso]
    origen: str = ""

    def costo(self, stocks: list[Stock]) -> float:
        return sum(u.repeticiones * stocks[u.stock].costo for u in self.usos)

    def planchas(self) -> int:
        return sum(u.repeticiones for u in self.usos)

    def clave(self, stocks: list[Stock]) -> tuple:
        """Para comparar soluciones: menos m², después menos montajes, después más sobrante
        junto (el sobrante más grande, en negativo)."""
        return (round(self.costo(stocks), 6), len(self.usos), -self.sobrante_mayor())

    def sobrante_mayor(self) -> int:
        mayor = 0
        for u in self.usos:
            for h, _, _ in arbol.hojas(u.nodo):
                if h.tipo == "sobrante":
                    mayor = max(mayor, h.ancho * h.alto)
        return mayor


@dataclass
class Limites:
    """Cuánto trabajo se hace según el esfuerzo pedido."""

    variantes_secuencial: tuple[float, ...]
    iteraciones_columnas: int
    trabajo: int  # tiras calculadas por el generador (heurística + columnas)
    nodos_entera: int
    segundos_seguridad: float
    buceo: bool = False


# Variantes de la heurística: el valor de cada pieza es su área elevada a este número. Con más
# de 1 se priorizan las piezas grandes (que son las difíciles de ubicar): en los casos de prueba
# 1,5 dio en promedio lo mejor y 1,0 (área pura) lo peor.
# El trabajo se mide en tiras calculadas por el generador (no en segundos), así el mismo caso da
# lo mismo en cualquier PC. Las variantes después de la primera solo corren si queda trabajo.
ESFUERZOS = {
    "rapido": Limites((1.5,), 0, 0, 0, 30),
    "normal": Limites((1.5, 1.2, 2.0), 80, 9000, 1000, 60),
    "maximo": Limites((1.5, 1.2, 2.0, 1.0, 1.35, 1.75), 300, 120000, 20000, 300, buceo=True),
}


@dataclass
class ResultadoMaterial:
    tipos: list[Tipo]
    stocks: list[Stock]
    separacion: int
    solucion: Solucion | None
    cota_planchas: int  # mínimo teórico (planchas de la medida más grande)
    cota_m2: float
    cota_lp_m2: float | None  # diagnóstico interno (no es un mínimo)
    avisos: list[str]
    errores: list[str]
    trabajo: dict
    segundos: float


# ------------------------------------------------------------------------ problema
class Problema:
    def __init__(self, tipos: list[Tipo], stocks: list[Stock], separacion: int, destaque: int):
        self.tipos = tipos
        self.stocks = stocks
        self.s = separacion
        self.d = destaque
        self.demanda = [t.cantidad for t in tipos]
        self.n = len(tipos)
        tipos_gen = [TipoGen(tuple((a + separacion, b + separacion) for a, b in t.orientaciones))
                     for t in tipos]
        self.generadores = [Generador(st.ancho + separacion, st.largo + separacion, tipos_gen, destaque)
                            for st in stocks]
        # Generador barato (sin alternancia de cortes y un solo nivel de relleno): lo usa la
        # heurística secuencial, que lo llama muchas veces.
        self.generadores_rapidos = [Generador(st.ancho + separacion, st.largo + separacion, tipos_gen,
                                              destaque, max_relleno=1, max_alternancia=0)
                                    for st in stocks]
        # Área agrandada de cada tipo: es el "valor" natural de una pieza.
        self.area = [float((t.ancho_corte + separacion) * (t.largo_corte + separacion)) for t in tipos]
        self.area_real = [float(t.ancho_corte * t.largo_corte) for t in tipos]

    def trabajo(self) -> int:
        return sum(g.llamadas for g in self.generadores + self.generadores_rapidos)

    def cuenta(self, nodo: Nodo) -> tuple[int, ...]:
        c = arbol.contar(nodo)
        return tuple(c.get(i, 0) for i in range(self.n))

    def aprovechamiento(self, stock: int, cuenta) -> float:
        return sum(self.area_real[i] * n for i, n in enumerate(cuenta)) / (
            self.stocks[stock].ancho * self.stocks[stock].largo)


# ---------------------------------------------------------------- heurística rápida
def secuencial(p: Problema, potencia: float = 1.0, restante: list[int] | None = None,
               cancelar=None, completo: bool = False, progreso=None) -> Solucion | None:
    """Arma un montaje para lo que falta, lo repite lo más posible, y sigue. Con `completo` usa
    el generador completo (más lento, encuentra montajes de más etapas)."""
    generadores = p.generadores if completo else p.generadores_rapidos
    rem = list(p.demanda if restante is None else restante)
    usos: list[Uso] = []
    while any(r > 0 for r in rem):
        if cancelar is not None and cancelar():
            return None
        # Valores fijos durante toda la corrida (lo agotado lo filtran las cotas): así el
        # generador reaprovecha su caché de un paso al otro.
        valores = [a ** potencia for a in p.area]
        mejor = None
        for k, g in enumerate(generadores):
            for nodo in g.generar(valores, rem):
                cuenta = p.cuenta(nodo)
                if not any(cuenta):
                    continue
                aprov = p.aprovechamiento(k, cuenta)
                clave = (aprov, -k)
                if mejor is None or clave > mejor[0]:
                    mejor = (clave, k, nodo, cuenta)
        if mejor is None:
            # Quedan piezas que no se pudieron ubicar (no debería pasar: se filtran antes).
            # Se devuelve lo armado; `calcular` lo informa como error.
            break
        _, k, nodo, cuenta = mejor
        exceso = [max(0, n - r) for n, r in zip(cuenta, rem)]
        if any(exceso):
            # No debería pasar (el generador respeta las cotas), pero si pasa, las piezas de más
            # se sacan acá: las cantidades tienen que dar exactas.
            nodo = sacar_piezas(nodo, exceso)
            cuenta = p.cuenta(nodo)
            if not any(cuenta):
                break
        reps = min(rem[i] // n for i, n in enumerate(cuenta) if n > 0)
        reps = max(reps, 1)
        usos.append(Uso(k, nodo, reps, cuenta))
        for i, n in enumerate(cuenta):
            rem[i] = max(0, rem[i] - reps * n)
        if progreso is not None:
            progreso(sum(p.demanda) - sum(rem), len(usos))
    if not usos:
        return None
    return Solucion(usos, f"secuencial ({potencia:g})")


# ------------------------------------------------------- generación de columnas + entera
@dataclass
class Columna:
    stock: int
    nodo: Nodo
    cuenta: tuple[int, ...]


def _resolver_lp(p: Problema, columnas: list[Columna]):
    from scipy.optimize import linprog

    A = np.array([[c.cuenta[i] for c in columnas] for i in range(p.n)], dtype=float)
    costos = np.array([p.stocks[c.stock].costo for c in columnas])
    res = linprog(costos, A_ub=-A, b_ub=-np.array(p.demanda, dtype=float),
                  bounds=[(0, None)] * len(columnas), method="highs")
    if res.status != 0:
        return None, None
    duales = -np.asarray(res.ineqlin.marginals)
    return float(res.fun), duales


def generar_columnas(p: Problema, columnas: list[Columna], iteraciones: int, progreso=None,
                     cancelar=None, reloj_limite: float | None = None,
                     planchas_conocidas: int | None = None,
                     trabajo_max: int | None = None) -> tuple[float | None, int]:
    """Agrega montajes a `columnas` mientras mejoren la relajación lineal. Devuelve (valor de la
    relajación, iteraciones hechas).

    Corte temprano (cota de Farley): con una sola medida de plancha, si la relajación ya muestra
    que no se puede bajar de `planchas_conocidas`, no tiene sentido seguir buscando montajes.
    """
    vistos = {(c.stock, c.cuenta) for c in columnas}
    valor = None
    hechas = 0
    historia: list[float] = []
    for it in range(iteraciones):
        if cancelar is not None and cancelar():
            break
        if reloj_limite is not None and time.perf_counter() > reloj_limite:
            break
        if trabajo_max is not None and p.trabajo() >= trabajo_max:
            break
        valor, duales = _resolver_lp(p, columnas)
        if duales is None:
            break
        hechas = it + 1
        if progreso:
            progreso(fase="columnas", iteracion=it + 1, de=iteraciones)
        # Valor = precio dual + un poquito de área, para que el espacio libre igual se llene.
        valores = [max(float(d), 0.0) + 1e-6 * a for d, a in zip(duales, p.area)]
        nuevas = 0
        mejor_razon = 0.0  # máx (valor dual del montaje ÷ costo de la plancha)
        # (Se probó buscar primero con el generador barato: la relajación convergía más lento y
        # se perdían los montajes perfectos. Se usa siempre el completo.)
        for generadores in (p.generadores,):
            for k, g in enumerate(generadores):
                for nodo in g.generar(valores, p.demanda):
                    cuenta = p.cuenta(nodo)
                    if not any(cuenta):
                        continue
                    valor_dual = sum(float(duales[i]) * n for i, n in enumerate(cuenta))
                    mejor_razon = max(mejor_razon, valor_dual / p.stocks[k].costo)
                    if (k, cuenta) in vistos:
                        continue
                    if p.stocks[k].costo - valor_dual < -1e-9 * p.stocks[k].costo:
                        columnas.append(Columna(k, nodo, cuenta))
                        vistos.add((k, cuenta))
                        nuevas += 1
            if nuevas > 0:
                break  # el barato alcanzó: no hace falta el completo en esta vuelta
        if nuevas == 0:
            break
        if planchas_conocidas is not None and len(p.stocks) == 1 and mejor_razon > 0:
            farley = valor / max(mejor_razon, 1.0) / p.stocks[0].costo
            if math.ceil(farley - 1e-6) >= planchas_conocidas:
                break
            # "Cola": la relajación casi no baja (menos de 0,05 % en 5 vueltas) y todavía no
            # llega a una plancha menos que la mejor solución conocida. (Con una regla más
            # apurada se cortaba antes de encontrar los montajes perfectos: ver VALIDACION.md.)
            historia.append(valor)
            if (len(historia) >= 6 and historia[-6] - historia[-1] < 0.0005 * historia[-1]
                    and math.ceil(valor / p.stocks[0].costo - 1e-6) >= planchas_conocidas):
                break
    if valor is not None and hechas == iteraciones:
        valor, _ = _resolver_lp(p, columnas)
    return valor, hechas


def resolver_entera(p: Problema, columnas: list[Columna], nodos: int, segundos: float,
                    costo_conocido: float | None = None):
    """Programación entera: cuántas veces se usa cada montaje para cubrir todas las piezas con la
    menor cantidad de m² de plancha. Devuelve (Solucion o None, aviso o None).

    (Se probó un segundo paso que, con esos m², minimizara la cantidad de montajes distintos con
    variables binarias: tardaba segundos y no mejoraba nada en los casos de prueba. La cantidad
    de montajes se cuida eligiendo entre soluciones de igual m² la de menos montajes.)"""
    from scipy.optimize import Bounds, LinearConstraint, milp

    m = len(columnas)
    A = np.array([[c.cuenta[i] for c in columnas] for i in range(p.n)], dtype=float)
    d = np.array(p.demanda, dtype=float)
    # Costo en unidades enteras (el área útil dividida por el máximo común divisor de las áreas):
    # así HiGHS sabe que el objetivo es entero y corta apenas prueba que no se puede mejorar.
    areas = [st.ancho * st.largo for st in p.stocks]
    unidad = math.gcd(*areas) if len(areas) > 1 else areas[0]
    costos = np.array([p.stocks[c.stock].ancho * p.stocks[c.stock].largo // unidad for c in columnas],
                      dtype=float)
    # Ninguna columna hace falta más veces que las que cubren toda la demanda de alguno de sus tipos.
    tope = np.array([max(math.ceil(p.demanda[i] / c.cuenta[i]) for i in range(p.n) if c.cuenta[i] > 0)
                     for c in columnas], dtype=float)
    opciones = {"node_limit": nodos, "time_limit": segundos, "presolve": True}
    aviso = None
    restricciones = [LinearConstraint(A, lb=d, ub=np.inf)]
    if costo_conocido is not None:
        # Solo interesa algo estrictamente mejor que lo que ya se tiene: si la relajación muestra
        # que no existe, HiGHS termina enseguida.
        tope_costo = round(costo_conocido * 1e6 / unidad) - 1
        restricciones.append(LinearConstraint(costos[None, :], lb=-np.inf, ub=tope_costo + 1e-6))
    res = milp(costos, constraints=restricciones,
               integrality=np.ones(m), bounds=Bounds(np.zeros(m), tope), options=opciones)
    if res.x is None:
        if costo_conocido is not None and res.status in (0, 2):
            return None, None  # no hay nada mejor con estos montajes
        return None, None if costo_conocido is not None else \
            "la programación entera no encontró solución en el límite de trabajo"
    if res.status == 1 and "time" in str(res.message).lower():
        aviso = "la programación entera se cortó por tiempo (el resultado puede variar entre PCs)"
    x = np.round(res.x).astype(int)
    usos = [Uso(columnas[j].stock, columnas[j].nodo, int(x[j]), columnas[j].cuenta)
            for j in range(m) if x[j] > 0]
    return Solucion(usos, "columnas + entera"), aviso


# -------------------------------------------------------------- cantidades exactas
def quitar_sobrantes(p: Problema, sol: Solucion) -> Solucion:
    """Saca las piezas de más (si la programación entera cubrió de más) para que las cantidades
    den exactas. Empieza por las planchas menos llenas y trata de tocar la menor cantidad de
    montajes."""
    total = [0] * p.n
    for u in sol.usos:
        for i, n in enumerate(u.cuenta):
            total[i] += u.repeticiones * n
    exceso = [t - d for t, d in zip(total, p.demanda)]
    if all(e <= 0 for e in exceso):
        return sol
    usos = [Uso(u.stock, u.nodo, u.repeticiones, u.cuenta) for u in sol.usos]
    while any(e > 0 for e in exceso):
        # El montaje que más exceso absorbe en una plancha; si empatan, el menos lleno.
        mejor = None
        for j, u in enumerate(usos):
            absorbe = sum(min(e, n) for e, n in zip(exceso, u.cuenta) if e > 0)
            if absorbe <= 0:
                continue
            clave = (absorbe, -p.aprovechamiento(u.stock, u.cuenta), -j)
            if mejor is None or clave > mejor[0]:
                mejor = (clave, j)
        j = mejor[1]
        u = usos[j]
        quitar = [min(e, n) if e > 0 else 0 for e, n in zip(exceso, u.cuenta)]
        # Cuántas planchas de este montaje pueden recibir el mismo recorte.
        veces = min([u.repeticiones] + [exceso[i] // q for i, q in enumerate(quitar) if q > 0])
        veces = max(veces, 1)
        nodo = sacar_piezas(u.nodo, quitar)
        cuenta = tuple(n - q for n, q in zip(u.cuenta, quitar))
        u.repeticiones -= veces
        nuevo = [Uso(u.stock, nodo, veces, cuenta)] if any(cuenta) else []
        usos = [x for x in usos if x.repeticiones > 0] + nuevo
        for i, q in enumerate(quitar):
            exceso[i] -= q * veces
    return Solucion(_juntar_iguales(usos), sol.origen)


def sacar_piezas(nodo: Nodo, quitar: list[int]) -> Nodo:
    """Cambia por sobrante las piezas indicadas, empezando por las últimas (arriba a la
    derecha), así el lugar libre queda junto al sobrante que ya había."""
    pendientes = list(quitar)

    def recorrer(n: Nodo) -> Nodo:
        if n.tipo == "pieza":
            if pendientes[n.pieza] > 0:
                pendientes[n.pieza] -= 1
                return arbol.sobrante(n.ancho, n.alto)
            return n
        if n.tipo == "sobrante":
            return n
        hijos = [recorrer(h) for h in reversed(n.hijos)][::-1]
        return arbol.normalizar(Nodo(n.tipo, n.ancho, n.alto, hijos))

    return recorrer(nodo)


def firma(nodo: Nodo) -> tuple:
    return (nodo.tipo, nodo.ancho, nodo.alto, nodo.pieza, tuple(firma(h) for h in nodo.hijos))


def _juntar_iguales(usos: list[Uso]) -> list[Uso]:
    """Dos usos con el mismo montaje (mismo árbol y misma plancha) son uno solo."""
    juntos: dict[tuple, Uso] = {}
    for u in usos:
        clave = (u.stock, firma(u.nodo))
        if clave in juntos:
            juntos[clave].repeticiones += u.repeticiones
        else:
            juntos[clave] = Uso(u.stock, u.nodo, u.repeticiones, u.cuenta)
    return list(juntos.values())


# ---------------------------------------------------------------- juntar el sobrante
def _lp_resto(p: Problema, columnas: list[Columna], demanda: list[int]):
    """Relajación lineal para cubrir `demanda` con `columnas`. Devuelve (x, duales) o (None, None)."""
    from scipy.optimize import linprog

    A = np.array([[c.cuenta[i] for c in columnas] for i in range(p.n)], dtype=float)
    costos = np.array([p.stocks[c.stock].costo for c in columnas])
    res = linprog(costos, A_ub=-A, b_ub=-np.array(demanda, dtype=float),
                  bounds=[(0, None)] * len(columnas), method="highs")
    if res.status != 0:
        return None, None
    return np.asarray(res.x), -np.asarray(res.ineqlin.marginals)


def bucear(p: Problema, columnas: list[Columna], trabajo_max: int, iteraciones_por_paso: int = 6,
           cancelar=None) -> Solucion | None:
    """Buceo ("diving"): se fija el montaje que la relajación lineal más usa, se descuentan sus
    piezas y se vuelve a resolver lo que falta (generando montajes nuevos para ese resto).

    Sirve sobre todo cuando las piezas son casi todas distintas: ahí la programación entera tiene
    que encontrar una combinación exacta entre muchos montajes y el buceo la arma de a uno.
    """
    resto = list(p.demanda)
    usos: list[Uso] = []
    pool = list(columnas)
    vistos = {(c.stock, c.cuenta) for c in pool}
    while any(r > 0 for r in resto):
        if p.trabajo() >= trabajo_max or (cancelar and cancelar()):
            break
        validas = [c for c in pool if any(c.cuenta) and all(a <= r for a, r in zip(c.cuenta, resto))]
        # Que cada tipo que falta tenga al menos un montaje posible.
        for i in range(p.n):
            if resto[i] > 0 and not any(c.cuenta[i] > 0 for c in validas):
                valores = [p.area[j] if j == i else 0.0 for j in range(p.n)]
                for k, g in enumerate(p.generadores):
                    for nodo in g.generar(valores, resto):
                        cuenta = p.cuenta(nodo)
                        if any(cuenta) and (k, cuenta) not in vistos:
                            col = Columna(k, nodo, cuenta)
                            pool.append(col)
                            validas.append(col)
                            vistos.add((k, cuenta))
        x = None
        for _ in range(iteraciones_por_paso):
            x, duales = _lp_resto(p, validas, resto)
            if x is None or p.trabajo() >= trabajo_max:
                break
            valores = [max(float(d), 0.0) + 1e-6 * a for d, a in zip(duales, p.area)]
            nuevas = 0
            for k, g in enumerate(p.generadores):
                for nodo in g.generar(valores, resto):
                    cuenta = p.cuenta(nodo)
                    if not any(cuenta) or (k, cuenta) in vistos:
                        continue
                    if p.stocks[k].costo - sum(float(duales[i]) * n for i, n in enumerate(cuenta)) < \
                            -1e-9 * p.stocks[k].costo:
                        col = Columna(k, nodo, cuenta)
                        pool.append(col)
                        validas.append(col)
                        vistos.add((k, cuenta))
                        nuevas += 1
            if nuevas == 0:
                break
        x, _ = _lp_resto(p, validas, resto)
        if x is None:
            break
        # El más usado por la relajación; si empatan, el más lleno.
        j = max(range(len(validas)),
                key=lambda j: (round(x[j], 6), p.aprovechamiento(validas[j].stock, validas[j].cuenta), -j))
        col = validas[j]
        veces = max(1, int(x[j] + 1e-6))
        veces = min([veces] + [resto[i] // n for i, n in enumerate(col.cuenta) if n > 0])
        usos.append(Uso(col.stock, col.nodo, veces, col.cuenta))
        for i, n in enumerate(col.cuenta):
            resto[i] -= veces * n
    if any(r > 0 for r in resto):
        final = secuencial(p, 1.5, restante=resto, completo=True)
        if final is None:
            return None
        usos += final.usos
    columnas[:] = pool
    return Solucion(_juntar_iguales(usos), "buceo")


def juntar_sobrante(p: Problema, sol: Solucion, max_planchas: int = 4) -> Solucion:
    """Reacomoda las planchas menos llenas para que el sobrante quede junto en la última (o
    para ahorrar una plancha), sin agregar montajes ni m²."""
    mejor = sol
    instancias = sorted(((p.aprovechamiento(u.stock, u.cuenta), j) for j, u in enumerate(sol.usos)))
    # Se toman las últimas planchas (una por montaje poco lleno) hasta max_planchas.
    tomadas: list[int] = []
    for _, j in instancias:
        if len(tomadas) >= max_planchas:
            break
        tomadas.append(j)
    for cantidad in range(2, len(tomadas) + 1):
        grupo = tomadas[:cantidad]
        # Una plancha de cada montaje del grupo.
        resto = [0] * p.n
        for j in grupo:
            for i, n in enumerate(sol.usos[j].cuenta):
                resto[i] += n
        nueva = secuencial(p, 1.5, restante=resto, completo=True)
        if nueva is None:
            continue
        usos = []
        for j, u in enumerate(sol.usos):
            reps = u.repeticiones - (1 if j in grupo else 0)
            if reps > 0:
                usos.append(Uso(u.stock, u.nodo, reps, u.cuenta))
        candidata = Solucion(_juntar_iguales(usos + nueva.usos), sol.origen)
        if candidata.clave(p.stocks) < mejor.clave(p.stocks):
            mejor = candidata
    return mejor


# ----------------------------------------------------------------------- cota inferior
def cota_inferior(p: Problema) -> tuple[int, float]:
    """Mínimo teórico: (planchas de la medida más grande, m² de plancha útil).

    - Por área: ⌈Σ área de piezas (agrandada en la separación) ÷ área útil (agrandada)⌉.
    - Por piezas grandes: dos piezas que miden más de la mitad de la plancha en los dos sentidos
      (en cualquier orientación permitida) no pueden ir en la misma plancha.
    """
    s = p.s
    k_max = max(range(len(p.stocks)), key=lambda k: p.stocks[k].costo)
    st = p.stocks[k_max]
    W, H = st.ancho + s, st.largo + s
    area_total = sum(p.area[i] * p.demanda[i] for i in range(p.n))
    por_area = math.ceil(area_total / (W * H) - 1e-9)
    grandes = 0
    for t in p.tipos:
        if all(a + s > W / 2 and b + s > H / 2 for a, b in t.orientaciones):
            grandes += t.cantidad
    planchas = max(por_area, grandes)
    m2 = sum(p.area_real[i] * p.demanda[i] for i in range(p.n)) / 1e6
    return planchas, m2


# ------------------------------------------------------------------------- todo junto
def calcular(tipos: list[Tipo], stocks: list[Stock], separacion: int, destaque: int,
             esfuerzo: str = "normal", progreso=None, cancelar=None) -> ResultadoMaterial:
    inicio = time.perf_counter()
    lim = ESFUERZOS.get(esfuerzo, ESFUERZOS["normal"])
    reloj_limite = inicio + lim.segundos_seguridad
    avisos: list[str] = []
    errores: list[str] = []
    p = Problema(tipos, stocks, separacion, destaque)
    cota_planchas, cota_m2 = cota_inferior(p)
    tiempos: dict[str, float] = {}

    def avisar(**kw):
        """Progreso para la pantalla "Cálculo en proceso": fase, avance estimado (0 a 1) y
        cantidad de montajes armados hasta ahora."""
        if not progreso:
            return
        fase = kw.get("fase")
        trabajo = min(1.0, p.trabajo() / lim.trabajo) if lim.trabajo else 0.0
        solo_heuristica = lim.iteraciones_columnas == 0
        if fase == "secuencial":
            hecho = (kw.get("variante", 1) - 1 + kw.get("parte", 1.0)) / max(kw.get("de", 1), 1)
            avance = (0.95 if solo_heuristica else 0.3) * hecho
        elif fase == "columnas":
            avance = 0.3 + 0.55 * trabajo
        elif fase == "entera":
            avance = 0.87
        elif fase == "buceo":
            avance = 0.9
        else:
            avance = 0.97
        kw.setdefault("montajes", len(columnas))
        progreso(avance=round(min(avance, 0.99), 3), **kw)

    # 1) Heurística secuencial con algunas variantes.
    mejor: Solucion | None = None
    columnas: list[Columna] = []
    for n_var, potencia in enumerate(lim.variantes_secuencial):
        if cancelar is not None and cancelar() and mejor is not None:
            break
        if n_var > 0 and p.trabajo() > 0.3 * lim.trabajo:
            break
        t0 = time.perf_counter()
        completo = n_var == 0 and sum(p.demanda) <= 400
        total_piezas = sum(p.demanda)

        def paso(colocadas, montajes, _n=n_var):
            avisar(fase="secuencial", variante=_n + 1, de=len(lim.variantes_secuencial),
                   parte=colocadas / total_piezas, montajes=montajes)

        sol = secuencial(p, potencia, cancelar=cancelar if mejor is not None else None,
                         completo=completo, progreso=paso)
        tiempos['secuencial'] = tiempos.get('secuencial', 0) + time.perf_counter() - t0
        if sol is None:
            continue
        for u in sol.usos:
            columnas.append(Columna(u.stock, u.nodo, u.cuenta))
        if mejor is None or sol.clave(stocks) < mejor.clave(stocks):
            mejor = sol
        avisar(fase="secuencial", variante=n_var + 1, de=len(lim.variantes_secuencial),
               planchas=mejor.planchas(), montajes=len(mejor.usos))
    if mejor is None:
        errores.append("no se pudo armar ningún montaje")
        return ResultadoMaterial(tipos, stocks, separacion, None, cota_planchas, cota_m2, None,
                                 avisos, errores, {"generador": p.trabajo()},
                                 time.perf_counter() - inicio)

    # 2) Generación de columnas + programación entera (si vale la pena).
    cota_lp = None
    iteraciones = 0
    ya_optimo = (len(stocks) == 1 and mejor.planchas() <= cota_planchas)
    if lim.iteraciones_columnas > 0 and not ya_optimo and not (cancelar and cancelar()):
        # Columnas "homogéneas": la mayor cantidad posible de cada tipo solo.
        for i in range(p.n):
            valores = [1.0 if j == i else 0.0 for j in range(p.n)]
            for k, g in enumerate(p.generadores):
                for nodo in g.generar(valores, p.demanda):
                    cuenta = p.cuenta(nodo)
                    if any(cuenta):
                        columnas.append(Columna(k, nodo, cuenta))
        columnas = _sin_repetir(columnas)
        t0 = time.perf_counter()
        cota_lp, iteraciones = generar_columnas(p, columnas, lim.iteraciones_columnas, avisar,
                                                cancelar, reloj_limite, mejor.planchas(), lim.trabajo)
        if not (cancelar and cancelar()):
            avisar(fase="entera")
            restante = max(1.0, reloj_limite - time.perf_counter())
            tiempos['columnas'] = time.perf_counter() - t0
            t0 = time.perf_counter()
            sol, aviso = resolver_entera(p, columnas, lim.nodos_entera, min(restante, 20.0),
                                         mejor.costo(stocks))
            tiempos['entera'] = time.perf_counter() - t0
            if aviso:
                avisos.append(aviso)
            if sol is not None:
                sol = quitar_sobrantes(p, sol)
                if sol.clave(stocks) < mejor.clave(stocks):
                    mejor = sol
            # Buceo, si todavía no se llegó al mínimo teórico. (El valor de la relajación no
            # sirve para decidir: si la generación de columnas no terminó, es una cota por arriba.)
            falta = len(stocks) > 1 or mejor.planchas() > cota_planchas
            if lim.buceo and falta and not (cancelar and cancelar()):
                t0 = time.perf_counter()
                avisar(fase="buceo")
                sol = bucear(p, columnas, p.trabajo() + lim.trabajo, cancelar=cancelar)
                tiempos['buceo'] = time.perf_counter() - t0
                if sol is not None and sol.clave(stocks) < mejor.clave(stocks):
                    mejor = sol
    if time.perf_counter() > reloj_limite:
        avisos.append("el cálculo llegó al límite de tiempo de seguridad: el resultado puede variar "
                      "entre PCs")
    # Control: ¿quedó alguna pieza sin ubicar? (no debería pasar)
    puestas = [0] * p.n
    for u in mejor.usos:
        for i, n in enumerate(u.cuenta):
            puestas[i] += u.repeticiones * n
    for t, (pu, de) in zip(tipos, zip(puestas, p.demanda)):
        if pu < de:
            errores.append(f"ítems {t.etiqueta}: {de - pu} pieza(s) de {t.ancho_corte} × "
                           f"{t.largo_corte} no se pudieron ubicar")
    # 3) Juntar el sobrante en la última plancha.
    if not (cancelar and cancelar()):
        t0 = time.perf_counter()
        mejor = juntar_sobrante(p, mejor)
        tiempos['juntar'] = time.perf_counter() - t0
    if cancelar and cancelar():
        avisos.append("cálculo cancelado: se muestra la mejor solución encontrada hasta ese momento")
    trabajo = {"generador": p.trabajo(), "columnas": len(columnas), "iteraciones_columnas": iteraciones,
               "segundos_por_fase": {k: round(v, 3) for k, v in tiempos.items()}}
    return ResultadoMaterial(tipos, stocks, separacion, mejor, cota_planchas, cota_m2,
                             cota_lp, avisos, errores,
                             trabajo, time.perf_counter() - inicio)


def _sin_repetir(columnas: list[Columna]) -> list[Columna]:
    vistos = set()
    unicas = []
    for c in columnas:
        clave = (c.stock, c.cuenta)
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(c)
    return unicas
