"""Los colores de los montajes, en un solo lugar para cambiarlos fácil.

Corte Certo usa los colores clásicos de Windows: bordó (128,0,0), verde (0,128,0), oliva
(128,128,0) para las piezas y amarillo (255,255,0) para el sobrante. No sabemos qué regla usa para
elegir el color de cada pieza (pregunta 5); acá se usa una propia: un color por tipo de pieza,
recorriendo la misma paleta en el mismo orden.
"""

PALETA_PIEZAS = [
    "#800000",  # bordó
    "#008000",  # verde
    "#808000",  # oliva
    "#000080",  # azul marino
    "#800080",  # violeta
    "#008080",  # verde azulado
    "#808080",  # gris
    "#FF0000",  # rojo
    "#0000FF",  # azul
    "#FF00FF",  # fucsia
    "#00A0A0",  # celeste oscuro
    "#A05000",  # marrón
]
SOBRANTE = "#FFFF00"  # amarillo
CONTORNO = "#000000"


def color_pieza(tipo: int) -> str:
    """Color del tipo de pieza número `tipo` (empieza en 1)."""
    return PALETA_PIEZAS[(tipo - 1) % len(PALETA_PIEZAS)]
