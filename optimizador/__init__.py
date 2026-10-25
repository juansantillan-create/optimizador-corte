"""Optimizador de corte de vidrio de Cristalux, para cotizar.

Dado un listado de piezas (material, cantidad, ancho, largo), calcula cuántas planchas hacen
falta, cómo se acomodan (montajes) y el aprovechamiento, con las mismas fórmulas que Corte Certo
v3.9K. Todo en milímetros enteros; la plancha va acostada (ancho = eje X = lado largo).

Mapa del paquete:
- `modelo`: las piezas, los materiales, las planchas y los montajes.
- `configuracion`: lee `config/hojas.csv` y arma los presets.
- `motor/`: el cálculo (generador de montajes, heurística, programación entera).
- `validador`: revisa cada resultado sin usar nada del motor.
- `informe`, `dibujo`: el informe de cálculo y los montajes en SVG.
- `api`: la función `optimizar()` y el JSON para el orquestador.
"""

__version__ = "0.0.1"
