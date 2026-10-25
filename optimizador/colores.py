"""Los colores de los montajes, en un solo lugar para cambiarlos fácil.

Corte Certo usa los colores clásicos de Windows: bordó (128,0,0), verde (0,128,0), oliva
(128,128,0) para las piezas y amarillo (255,255,0) para el sobrante, y en la captura aparecen solo
esos 3 colores de pieza aunque hay muchas medidas. No sabemos su regla exacta (pregunta 5); acá:
cada tipo de pieza toma uno de esos 3 colores, rotando (tipo 1 bordó, 2 verde, 3 oliva, 4 bordó…).
Así se ve como Corte Certo; para saber qué pieza es cada una está el detalle (medida e ítem).
"""

PALETA_PIEZAS = [
    "#800000",  # bordó
    "#008000",  # verde
    "#808000",  # oliva
]
SOBRANTE = "#FFFF00"  # amarillo
CONTORNO = "#000000"


def color_pieza(tipo: int) -> str:
    """Color del tipo de pieza número `tipo` (empieza en 1)."""
    return PALETA_PIEZAS[(tipo - 1) % len(PALETA_PIEZAS)]
