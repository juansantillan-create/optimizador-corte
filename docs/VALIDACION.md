# Validación

Qué tan confiable es el optimizador, en palabras simples. Se actualiza cada vez que cambia el motor
(regla 7 de `CLAUDE.md`). Lo más nuevo, arriba.

## 1. Contra Corte Certo (casos históricos)

**En pocas palabras** (corrida del 25/10/2026, esfuerzo normal, con las medidas de hoja del stock
y de los casos ya cargadas en `config/hojas_extra.csv`; de los 1341 casos se pudieron comparar 1089):

- **80,0 % da las mismas hojas que Corte Certo**, 16,5 % da menos y 3,5 % da más. Con esfuerzo
  máximo en los que dan más: 80,9 % iguales y 2,5 % con más.
- Hasta 20 piezas, 97,5 % iguales. Con más de 100 piezas, 57,6 % iguales y 37,5 % con menos hojas.
- Corte Certo parece haber pasado de la hoja entera (3600) a la plancha achicada (3580) en agosto
  de 2026 (tabla por período, abajo). El programa cotiza con 3580 (Juan, pregunta 28): calculados
  así todos los casos viejos, 11,5 % da más hojas que lo que cotizó Corte Certo entonces (en 21 las
  piezas ni entran: miden lo mismo que la hoja o casi).
- Todos los resultados pasaron el validador.

<!-- HISTORICO: lo escribe `python -m optimizador historico --docs` -->
Datos: `datos/casos/corte_certo` (exportados de Metrix el 25/10/2026). Esfuerzo: normal. Todos los casos. Configuración: H0 (solo el corte banda, sin separación ni destaque: así se usaba Corte Certo), con la misma medida de plancha que dio el control.

**Qué casos se pudieron comparar**

| | Casos |
|---|---|
| Casos exportados (presupuesto + vidrio) | 1341 |
| Sin cantidad de hojas (solo bandas o solo el %) | 17 |
| Corte Certo usó además bandas o recortes (no se puede repetir igual) | 124 |
| El área de la hoja que se deduce no cierra (leyenda o vidrio mal anotado) | 34 |
| Varias medidas de hoja anotadas (el programa no limita cuántas usa de cada una) | 3 |
| Sin piezas | 0 |
| No cierran: los m² no dan el % de la leyenda (el presupuesto cambió o era otra plancha) | 38 |
| Iguales a otro caso (mismas piezas, plancha y resultado de Corte Certo; a veces el mismo pedido en otro vidrio, a veces otro presupuesto): se cuentan una vez | 36 |
| **Pasaron el control y se compararon** | **1089** |
| … calculados con la hoja entera / con banda 20 / con la medida útil anotada | 754 / 305 / 30 |
| … donde también cierra la otra (banda 20 ↔ hoja entera): se calcularon las dos | 932 |
| … donde la otra no cierra: se calculó igual, solo para "cotizando siempre con…" | 127 |
| … donde el % cierra solo truncando, no redondeando | 25 |
| … que cierran solo SIN el +3 mm del pulido (se calcularon sin el +3) | 3 |
| … con las medidas de hoja anotadas en la leyenda | 46 |
| … con plancha supuesta (el material no está en hojas.csv) | 21 |
| … con una medida de hoja que hojas.csv no tiene para ese material (ver abajo) | 10 |
| … con más de una medida de plancha que cierra (se usó la más cercana) | 210 |

**Medidas de hoja que Corte Certo usó y no están en `hojas.csv`** (habría que sumarlas a `Medidas_hojas.xlsx`; pregunta 29)

| Material | Medida (casos) |
|---|---|
| CK8K1 | 3600x2540 (4) |
| LX4+4IN76 | 3600x2500 (2) |
| OP5IN | 3600x2400 (1) |
| CK6K1 | 3600x2400 (1) |
| OA10IN | 3600x2400 (1) |
| LO6IN | 3600x2400 (1) |

**¿Corte Certo cortaba sobre 3600 o sobre 3580?** (pregunta 28). Casos con % entero y hoja de 3600 × 2500 en hojas.csv que cierran con alguna de las dos. Para cada ancho: cuántos dan el % **redondeando** y, entre paréntesis, la diferencia media leyenda − calculado. Hay dos lecturas que dan casi lo mismo en promedio: "3600 y la oficina redondeaba" y "3580 y la oficina truncaba". Lo que las separa son las dos últimas columnas: cuántos casos contradicen cada una (con 3600, una diferencia de más de 0,5; con 3580, una leyenda más alta que lo calculado).

| Período | Casos | 3600 (hoja entera) | 3580 (banda 20) | 3570 (banda 30) | 3550 (banda 50) | Contradicen 3600 redondeando | Contradicen 3580 truncando |
|---|---|---|---|---|---|---|---|
| 2025 T3 | 39 | 95 % (-0.04) | 46 % (-0.48) | 36 % (-0.70) | 5 % (-1.15) | 2 | 5 |
| 2025 T4 | 60 | 92 % (-0.02) | 57 % (-0.47) | 28 % (-0.70) | 3 % (-1.15) | 5 | 8 |
| 2026 T1 | 82 | 98 % (-0.02) | 56 % (-0.47) | 27 % (-0.70) | 1 % (-1.16) | 2 | 2 |
| 2026 T2 | 124 | 94 % (-0.03) | 56 % (-0.45) | 33 % (-0.67) | 6 % (-1.10) | 7 | 15 |
| 2026-07 | 34 | 100 % (-0.01) | 65 % (-0.45) | 35 % (-0.67) | 0 % (-1.11) | 0 | 2 |
| 2026-08 | 14 | 86 % (+0.20) | 79 % (-0.25) | 50 % (-0.47) | 14 % (-0.93) | 2 | 2 |
| 2026-09 | 20 | 90 % (-0.05) | 45 % (-0.49) | 25 % (-0.72) | 5 % (-1.17) | 2 | 2 |
| 2026-10 | 20 | 65 % (+0.20) | 70 % (-0.24) | 65 % (-0.46) | 20 % (-0.90) | 7 | 7 |
| **Total** | 393 |  |  |  |  | 27 | 43 |

**Según qué plancha**: la cuenta principal usa, en cada caso, la plancha con la que mejor cierra el % de Corte Certo (redondeando primero, y la más cercana). Las filas "cotizando siempre con…" calculan todos los casos con esa plancha, cierre o no con el %: dicen cuánto se parecería el programa a Corte Certo si cotizara siempre así. Si las piezas no entran, cuenta como más hojas (no se puede cotizar). La diferencia media y la peor son de los que sí se calcularon.

| Plancha | Casos | Iguales | Menos planchas | Más planchas | Dif. media | Peor |
|---|---|---|---|---|---|---|
| La plancha con la que mejor cierra el % de cada caso: **la cuenta principal** | 1089 | 80.0 % | 16.5 % | 3.5 % | -0.27 | +9 |
| Cotizando siempre con banda 20 (3580) | 1089 | 75.5 % | 13.0 % | 11.5 % (con 21 donde las piezas no entran) | +0.13 | +47 |
| Cotizando siempre con la hoja entera (3600) | 1089 | 79.8 % | 18.1 % | 2.1 % | -0.32 | +9 |
| Solo los casos donde la otra no cierra con ninguna medida igual de confiable | 95 | 81.1 % | 17.9 % | 1.1 % | -0.47 | +1 |

**Con esfuerzo máximo** en los 38 casos donde el normal da más hojas que Corte Certo (más 88 variantes de plancha): mejoran 11 casos (y 15 variantes); el más lento tardó 324.31 s. Así quedan:

| Plancha | Casos | Iguales | Menos planchas | Más planchas | Dif. media | Peor |
|---|---|---|---|---|---|---|
| La plancha con la que mejor cierra el % de cada caso: **la cuenta principal** | 1089 | 80.9 % | 16.6 % | 2.5 % | -0.28 | +9 |
| Cotizando siempre con banda 20 (3580) | 1089 | 76.9 % | 13.1 % | 10.0 % (con 21 donde las piezas no entran) | +0.11 | +47 |
| Cotizando siempre con la hoja entera (3600) | 1089 | 80.5 % | 18.2 % | 1.3 % | -0.33 | +9 |
| Solo los casos donde la otra no cierra con ninguna medida igual de confiable | 95 | 81.1 % | 17.9 % | 1.1 % | -0.47 | +1 |

**Según de dónde salió la medida de hoja** (cuenta principal)

| Medida de hoja | Casos | Iguales | Menos planchas | Más planchas | Dif. media |
|---|---|---|---|---|---|
| la medida de hoja del material en hojas.csv | 1033 | 80.0 % | 16.5 % | 3.6 % | -0.27 |
| las medidas de hoja anotadas en la leyenda | 46 | 76.1 % | 21.7 % | 2.2 % | -0.26 |
| una medida deducida (hojas.csv no la tiene para ese material) | 10 | 100.0 % | 0.0 % | 0.0 % | +0.0 |

**Resultado de la cuenta principal (todos los casos comparados)**

- Casos: 1089
- Iguales a Corte Certo: 80.0 %; con menos planchas: 16.5 %; con más planchas: 3.5 %
- Diferencia media: -0.27 planchas por caso (negativo = a favor); la peor: +9
- Casos donde Corte Certo ya estaba en el mínimo teórico: 277
- Casos donde la leyenda dice menos hojas que el mínimo teórico (imposible; hay que mirarlos): 0
- Casos comparados con avisos: 852
- Resultados que no pasaron el validador (fuera de las cuentas): 0
- Resultados con piezas sin calcular (fuera de las cuentas): 0

| Material | Casos | Iguales | Mejores | Peores | Dif. media |
|---|---|---|---|---|---|
| CK6K1 | 168 | 76.2 % | 21.4 % | 2.4 % | -0.43 |
| CK6K2 | 46 | 82.6 % | 15.2 % | 2.2 % | -0.52 |
| CK6K3 | 21 | 76.2 % | 23.8 % | 0.0 % | -1.24 |
| CK6KB | 2 | 50.0 % | 50.0 % | 0.0 % | -0.5 |
| CK6KG | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CK8K1 | 30 | 96.7 % | 3.3 % | 0.0 % | -0.03 |
| CK8K2 | 17 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CK8K3 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CS6S1 | 1 | 0.0 % | 100.0 % | 0.0 % | -4.0 |
| CS6S2 | 4 | 50.0 % | 50.0 % | 0.0 % | -2.75 |
| CS8S1 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CS8S2 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CT6AZ | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CT6G1 | 15 | 66.7 % | 33.3 % | 0.0 % | -0.33 |
| CT6G2 | 11 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6AR | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6BL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6CL | 2 | 50.0 % | 50.0 % | 0.0 % | -1.0 |
| EC6EV | 14 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6GY | 68 | 76.5 % | 22.1 % | 1.5 % | -0.24 |
| FL4GR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL4IN | 5 | 80.0 % | 20.0 % | 0.0 % | -0.2 |
| FL5BR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL5IN | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL6BR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL6GR | 7 | 71.4 % | 28.6 % | 0.0 % | -0.71 |
| FL6IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL6NL | 10 | 40.0 % | 60.0 % | 0.0 % | -0.9 |
| FL8GR | 2 | 50.0 % | 50.0 % | 0.0 % | -0.5 |
| FL8IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL8NL | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| GRAPH6 | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LA5+5VC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LO6IN | 17 | 70.6 % | 23.5 % | 5.9 % | -0.53 |
| LX3+3BC | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3BO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3ES | 19 | 89.5 % | 10.5 % | 0.0 % | -0.11 |
| LX3+3ESL | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3GC | 7 | 71.4 % | 14.3 % | 14.3 % | +0.0 |
| LX3+3GCESM | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3GO | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3IN | 41 | 73.2 % | 19.5 % | 7.3 % | -0.32 |
| LX3+3IN76 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3LOWE | 93 | 68.8 % | 24.7 % | 6.5 % | -0.26 |
| LX3+3OPBR | 2 | 0.0 % | 100.0 % | 0.0 % | -1.0 |
| LX4+4ES | 10 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX4+4ESL | 3 | 66.7 % | 33.3 % | 0.0 % | -0.33 |
| LX4+4GC | 27 | 85.2 % | 14.8 % | 0.0 % | -0.15 |
| LX4+4GO | 7 | 71.4 % | 0.0 % | 28.6 % | +0.43 |
| LX4+4IN | 75 | 81.3 % | 14.7 % | 4.0 % | -0.21 |
| LX4+4IN76 | 3 | 66.7 % | 33.3 % | 0.0 % | -2.0 |
| LX4+4LOWE | 57 | 86.0 % | 10.5 % | 3.5 % | -0.11 |
| LX4+4NL | 25 | 80.0 % | 12.0 % | 8.0 % | +0.0 |
| LX4+4NL114 | 1 | 0.0 % | 100.0 % | 0.0 % | -1.0 |
| LX4+4ST120 | 24 | 75.0 % | 25.0 % | 0.0 % | -0.67 |
| LX4+4ST150 | 23 | 87.0 % | 8.7 % | 4.3 % | -0.04 |
| LX4+4STB12 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX4+4VC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX4+4VO | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+3AC | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5AV | 4 | 75.0 % | 0.0 % | 25.0 % | +0.25 |
| LX5+5BC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5ES | 5 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5ESL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5GC | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5GO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5IN | 59 | 88.1 % | 8.5 % | 3.4 % | -0.07 |
| LX5+5IN76 | 6 | 50.0 % | 50.0 % | 0.0 % | -1.0 |
| LX5+5NL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6GC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6GO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6IN | 24 | 75.0 % | 16.7 % | 8.3 % | -0.04 |
| LX6+6IN76 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6K114 | 1 | 0.0 % | 100.0 % | 0.0 % | -1.0 |
| LX6+6NL114 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OA10IN | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OA4IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OA8IN | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OL3+3IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OP4IN | 11 | 90.9 % | 0.0 % | 9.1 % | +0.09 |
| OP5IN | 7 | 71.4 % | 14.3 % | 14.3 % | +0.0 |
| OP6GR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OP6IN | 3 | 33.3 % | 66.7 % | 0.0 % | -1.0 |
| SO6BL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| SO6OC | 14 | 71.4 % | 14.3 % | 14.3 % | +0.0 |
| SO6OG | 7 | 71.4 % | 28.6 % | 0.0 % | -0.57 |
| SU6AR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| SU6SU | 26 | 88.5 % | 3.8 % | 7.7 % | +0.04 |

| Tamaño | Casos | Iguales | Mejores | Peores | Dif. media |
|---|---|---|---|---|---|
| hasta 20 piezas | 277 | 97.5 % | 0.4 % | 2.2 % | +0.02 |
| 21 a 100 piezas | 423 | 89.1 % | 7.8 % | 3.1 % | -0.05 |
| más de 100 piezas | 389 | 57.6 % | 37.5 % | 4.9 % | -0.71 |

**Los peores (más planchas que Corte Certo)**

| Presupuesto | Material | Piezas | Corte Certo | Nuestro | Mínimo teórico | Plancha |
|---|---|---|---|---|---|---|
| 8504 | LX4+4IN | 283 | 178 (71 %) | 187 (67.64 %) | 131 | 3660x2440 |
| 11404 | LX3+3LOWE | 124 | 36 (83 %) | 41 (72.85 %) | 30 | 3210x2400 |
| 5701 | LX3+3LOWE | 166 | 60 (87 %) | 65 (80.61 %) | 53 | 3300x2440 |
| 9126 | LX6+6IN | 386 | 78 (85 %) | 82 (81.04 %) | 67 | 3600x2500 |
| 6673 | CK6K1 | 249 | 55 (84 %) | 58 (79.8 %) | 47 | 3210x2540 |
| 7369 | CK6K1 | 1242 | 418 (78 %) | 421 (77.92 %) | 329 | 3210x2540 |
| 10120 | LX3+3LOWE | 40 | 11 (84 %) | 13 (71.14 %) | 10 | 3600x2200 |
| 11864 | LX4+4NL | 449 | 124 (62 %) | 126 (60.97 %) | 96 | 3660x2440 |
| 7319 | LX4+4GO | 52 | 8 (96 %) | 10 (77.11 %) | 8 | 3600x2500 |
| 7786 | LX3+3IN | 391 | 70 (91 %) | 72 (88.68 %) | 64 | 3600x2500 |
<!-- /HISTORICO -->

**Cómo se hizo** (detalle en `optimizador/historico/exportados.py`). Para repetirlo:

```text
python -m optimizador historico --todo --procesos 3 --repaso-maximo --docs
```

1. Los casos llegaron ya leídos, uno por presupuesto y vidrio (`datos/casos/corte_certo/`): las
   piezas (con el +3 mm del pulido recto ya sumado) y lo que dice la leyenda de Corte Certo (hojas,
   %, bandas).
2. **Control de la entrada**: los m² de las piezas tienen que cerrar con las hojas y el % de la
   leyenda, redondeado o truncado (pregunta 24). Se prueban la plancha con banda de 20 mm
   (3580 × 2500) y la hoja entera (3600 × 2500), con las medidas de hoja del vidrio en `hojas.csv`
   o las anotadas en la leyenda (si la anotada no es una hoja entera conocida, como 3190 o 3280, ya
   es la plancha útil y va tal cual); si ninguna cierra, otras medidas conocidas (primero las de la
   misma familia de vidrio), y eso se avisa (pregunta 29). Primero con el +3 y, si no cierra, sin
   (pregunta 25).
3. **¿Entran las piezas?** Una plancha se descarta si con ella no se puede llegar a las hojas de
   Corte Certo: por área, por piezas que no entran dos juntas, y por cuántas piezas de una misma
   medida entran como mucho en una plancha (ej. 900 × 478: 17 en la de 3580 y 20 en la de 3600).
4. **Cuál plancha gana**, si cierran varias: la que tiene el +3; la de `hojas.csv` (o la anotada)
   antes que una deducida; la que da el % **redondeando** antes que la que solo da truncando; la más
   cercana (si quedan iguales, banda 20). Esa es la cuenta principal.
5. Con la misma medida se calcula también la otra variante (banda 20 ↔ hoja entera), cierre o no:
   con eso se arman las filas "cotizando siempre con…". Si las piezas no entran, ese caso cuenta
   como "más hojas". "Solo los casos donde la otra no cierra" son los que no cierran con la otra
   variante con ninguna medida igual de confiable.
6. Se calcula como estaba Corte Certo: sin separación ni destaque (H0). No hay calibración ni
   muestra de prueba (hay una sola configuración), así que los números son sobre **todos** los casos
   comparados. Los casos iguales a otro se cuentan una vez.
7. Todo resultado pasa por el validador; los que no pasan o dejan piezas sin calcular se cuentan
   aparte.
8. Con `--repaso-maximo`, los cálculos donde el esfuerzo normal da más hojas que Corte Certo se
   repiten con el máximo, y se muestra cómo quedan las cuentas.

Lo calculado se guarda a medida que sale (`salida/historico/`, no va a git): si se corta, se vuelve
a correr el mismo comando y sigue donde quedó. Con `--procesos 3` los 2132 cálculos tardan unos
15 minutos en la nube, y el repaso con máximo, otros 10.

El método viejo (el zip del contrato v2, con las leyendas por leer y las piezas por reconstruir
desde Metrix) sigue en `optimizador/historico/comparar.py` y se prueba con el caso de juguete
(`tests/historico_juguete/`, 19 presupuestos **inventados**: esos números no dicen nada del
optimizador).

## 1.b Contra Optima (cortes reales en planta)

**En pocas palabras**: con la configuración de producción (banda y destaque de la regla de Lucas) y
las mismas medidas de hoja que usó Optima:

- con **esfuerzo normal**, el programa usa los mismos m² de hoja en 3 de los 5 lotes, 1,5 % más en el
  FL5IN y 1,8 % más en el FL6IN, donde Optima usó dos retazos en vez de una hoja (al cotizar no se
  usan retazos, pregunta 11). En total, **0,9 % más vidrio que Optima**;
- con **esfuerzo máximo**, el FL5IN da igual que Optima y el FL10IN, 3,4 % menos (pero usa 9 hojas de
  3700 × 2500 donde Optima usó 8 y dos de 3050 × 2050: puede que fuera lo que había en stock, y el
  programa no lo sabe). En total, 0,5 % menos;
- "Como cotización" muestra lo que daría el presupuesto con la plancha por defecto (respuesta 3): en
  el FL5IN, 9 hojas de 3600 × 2500 (81 m²) donde Optima usó 2 de 3600 × 2500 y 7 de 3600 × 2200
  (73,4 m²).

Son solo 5 lotes: sirve para ver que la configuración de Optima está bien entendida, no como
estadística. Para repetirlo: `python -m optimizador optima --docs`.

<!-- OPTIMA: lo escribe `python -m optimizador optima --docs` -->
Datos: `datos/casos/optima` (5 lotes cortados en planta con Optima). Mismas piezas y mismas medidas de hoja que usó Optima; corte banda y destaque mínimo de la regla de Lucas (preset "Reglas de corte (Lucas, como Optima)"). El programa no sabe qué había en stock: puede usar todas las hojas que quiera de cada medida (Optima usó las que había y, en un lote, retazos). Por eso se comparan los **m² de hoja**. "Como cotización": "Como Corte Certo hoy" con la plancha por defecto del vidrio.

| Lote | Vidrio | Piezas | Optima: hojas | Optima: m² | Nuestro (normal): hojas | m² | diferencia | Nuestro (máximo): hojas | m² | diferencia | Como cotización |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 164601 | CA4PA | 33 | 3×2500×1600 | 12.00 | 3×2500×1600 | 12.00 | +0.00 m² (+0.0 %) | 3×2500×1600 | 12.00 | +0.00 m² (+0.0 %) | 3×2500×1600: 12.00 m² |
| 165903 | FL5IN | 75 | 2×3600×2500; 7×3600×2200 | 73.44 | 3×3600×2500; 6×3600×2200 | 74.52 | +1.08 m² (+1.5 %) | 2×3600×2500; 7×3600×2200 | 73.44 | +0.00 m² (+0.0 %) | 9×3600×2500: 81.00 m² |
| 172802 | FL8IN | 29 | 4×3600×2500 | 36.00 | 4×3600×2500 | 36.00 | +0.00 m² (+0.0 %) | 4×3600×2500 | 36.00 | +0.00 m² (+0.0 %) | 4×3600×2500: 36.00 m² |
| 172905 | FL6IN | 38 | 10×3600×2500 + retazos 2×3580×1010 | 97.23 | 11×3600×2500 | 99.00 | +1.77 m² (+1.8 %) | 11×3600×2500 | 99.00 | +1.77 m² (+1.8 %) | 11×3600×2500: 99.00 m² |
| 173703 | FL10IN | 54 | 8×3700×2500; 1×3700×2200; 2×3050×2050 | 94.64 | 8×3700×2500; 1×3700×2200; 2×3050×2050 | 94.64 | +0.00 m² (+0.0 %) | 9×3700×2500; 1×3700×2200 | 91.39 | -3.25 m² (-3.4 %) | 10×3700×2500: 92.50 m² |

Total: Optima 313.32 m² de hoja; nuestro 316.16 m² con esfuerzo normal (+0.9 %); 311.83 m² con esfuerzo máximo (-0.5 %). Negativo = el programa usa menos vidrio.
<!-- /OPTIMA -->

## 2. Banco sintético (25/10/2026, motor con las correcciones de las revisiones de F1 a F4)

(El 25/10, después de las respuestas de Juan, los 36 casos con separación dejaron de usar el preset
de Lucas, que ahora es destaque, y piden la separación explícita: dan exactamente lo mismo. Los 85
casos se volvieron a correr y coinciden con `tests/banco/esperado.json`.)

Máquina: nube, Linux, Python 3.13, Intel Xeon 2,8 GHz, 4 núcleos (el cálculo usa uno solo). La PC
de la oficina va a ser más lenta: para medirla, `python -m optimizador banco` (ver §4).

85 casos fijos en `tests/banco/` (semillas fijas). Para correrlos:
`python -m optimizador banco` (tarda unos 5 minutos).

### 2.1 Todo resultado pasa el validador

| Prueba | Casos | Pasaron el validador |
|---|---|---|
| Banco sintético | 85 | **85 (100 %)** |
| Prueba de estrés (`herramientas/prueba_estres.py`, semilla 1): 3 de cada 4 chicos con separación, destaque, veta, constantes, márgenes y varias planchas; 1 de cada 4 de tamaño real (plancha 3600 × 2500, 20 a 400 piezas, 3 a 60 medidas) | 500 (342 chicos y 158 de tamaño real) | **500 (100 %)** |
| Tests con instancias al azar (`hypothesis`, en cada `pytest`) | 60 por corrida | 100 % |

La revisión de F1 encontró que la versión anterior ponía **piezas de más** en algunos casos grandes
(300 piezas de 30 medidas, o 2000 piezas): el validador lo atajaba, pero el caso no se podía
calcular. Las 500 instancias al azar de esa versión eran todas chicas y no lo mostraban. Está
corregido (con tests) y la prueba de estrés de ahora incluye casos de tamaño real.

El validador (`optimizador/validador.py`) no usa nada del motor: revisa de nuevo que cada pieza
esté adentro de la plancha útil, que no se solapen, la separación, que la plancha se pueda cortar
por guillotina sin dejar tiras más angostas que el destaque, la orientación (rotación y veta),
que las cantidades den exactas, y recalcula los m², las planchas, el aprovechamiento, la pérdida y
el perímetro.

### 2.2 "Corte perfecto": se sabe cuál es el óptimo

Se parten k planchas en piezas con cortes al azar; las piezas llenan exacto las k planchas, así que
el óptimo es k. Dos familias:

- **3 etapas** (como corta una mesa y como se ven los montajes de Corte Certo): tiras verticales,
  renglones y piezas. 3 a 12 piezas por plancha.
- **Guillotina libre** (cualquier profundidad de cortes, 6 a 15 piezas por plancha): mucho más
  difícil.

Casi todas las piezas son **distintas entre sí** (cantidad 1): es el peor caso posible, un
rompecabezas exacto. En un presupuesto real hay muchas piezas repetidas.

| Familia (hasta 100 piezas) | Casos | Encontró el óptimo | Planchas de más (en total) | Tiempo máximo |
|---|---|---|---|---|
| 3 etapas | 36 | **20 (56 %)** | 16 (siempre 1 en los que falló) | 9,6 s |
| Guillotina libre | 24 | **10 (42 %)** | 14 (siempre 1) | 8,1 s |

Además hay 12 casos de guillotina libre con 101 a 121 piezas: ninguno en el óptimo (1 plancha de
más en todos).

- **La meta del brief (≥ 95 % de óptimos hasta 100 piezas) no se cumple todavía.** Los casos de 1 a
  3 planchas salen casi todos bien; desde 4 o 5 planchas suele sobrar una.
- Por qué: para llenar k planchas al 100 % con piezas todas distintas hay que encontrar **la**
  combinación exacta. Se vio (caso CP3-1006) que dejando trabajar más al motor la encuentra (la
  relajación lineal llega a 6,0 y la entera da 6), pero tarda el doble de lo que se le permite en el
  esfuerzo normal. Con el esfuerzo máximo, ver §2.5.
- Lo que se probó y no sirvió (anotado para no repetirlo): un segundo paso de programación entera
  para reducir montajes (lento, sin mejora); buscar primero con un generador barato (la relajación
  convergía más lento); un "buceo" (diving) que fija montajes de a uno (no mejoró estos casos; quedó
  solo en el esfuerzo máximo).

### 2.3 Realistas (templados, DVH y casos como el 413)

Medidas de 300 a 2500 mm con muchas repetidas, y 3 casos "tipo 413" inventados (252 piezas grandes,
unas 3 por plancha). No se sabe el óptimo: se compara con el **mínimo teórico** (por área: es un
piso que muchas veces no se puede alcanzar) y, como diagnóstico, con la **relajación lineal** de
los montajes que generó el motor (si el resultado es igual a esa cota redondeada para arriba, con
esos montajes no se puede hacer mejor).

| Caso | Piezas | Planchas | Mínimo teórico | Relajación lineal | Montajes | Segundos |
|---|---|---|---|---|---|---|
| RE-2000 | 20 | 2 | 2 | — | 2 | 0,06 |
| RE-2001 | 50 | 6 | 6 | — | 6 | 0,2 |
| RE-2002 | 80 | 6 | 6 | — | 6 | 0,4 |
| RE-2003 | 120 | 21 | 19 | 19,90 | 15 | 1,8 |
| RE-2004 | 300 | 46 | 43 | 44,23 | 25 | 5,3 |
| RE-2005 | 300 | 13 | 12 | 12,00 | 13 | 7,9 |
| RE-2006 | 40 | 9 | 8 | 8,50 | 7 | 0,2 |
| RE-2007 | 200 | 25 | 24 | 24,07 | 20 | 3,9 |
| RE-2008 | 60 | 3 | 3 | — | 3 | 0,3 |
| RE-2009 | 250 | 50 | 47 | 49,46 | 31 | 2,6 |
| T413-3000 | 252 | 73 | 64 | 72,94 | 20 | 0,3 |
| T413-3001 | 252 | 73 | 61 | 72,06 | 18 | 0,3 |
| T413-3002 | 252 | 73 | 59 | 72,02 | 20 | 0,4 |

("—" = la heurística ya llegó al mínimo teórico y no hizo falta seguir.)

- En 4 casos se llegó al mínimo teórico (óptimo seguro).
- En 7 más el resultado es igual a la relajación redondeada para arriba.
- En RE-2003 y RE-2004 queda 1 plancha por encima de esa cota.
- En los "tipo 413" el mínimo teórico por área (59–64) es muy optimista: con piezas tan grandes
  entran 3 por plancha y la relajación dice 72–73.

### 2.4 Tiempos y memoria (nube)

| Caso | Primera solución (esfuerzo "rápido") | Final (esfuerzo "normal") | Meta |
|---|---|---|---|
| Típico: 300 piezas, 30 medidas de 300 a 2400 mm | 1,2 s | 5,4 s | < 2 s / ≤ 10 s ✔ |
| Típico: 300 piezas, 30 medidas de 300 a 1200 mm | 1,7 s | 8,1 s | < 2 s / ≤ 10 s ✔ (justo) |
| Como el 413: 252 piezas grandes | 0,1 s | 0,3 s | ✔ |
| Grande: 2000 piezas, 60 medidas | 4,4 s | 23 s | ≤ 60 s ✔ |
| Fuera del típico: 200 piezas **todas distintas** | 12 s | 11 s | (no es "típico": > 30 medidas) |
| Peor caso: 2000 piezas **todas distintas** | 68 s | 69 s | ≤ 60 s ✘ (se pasa) |
| Ídem con esfuerzo "Máximo" (3 medidas de plancha) | | 69 s | antes de la revisión de F5: 23 minutos y 1053 MB |
| Entre el típico y el peor: 40 casos de 45 a 160 medidas distintas (revisor de F5) | | 9 de los 40 pasan los 10 s (el más lento, 21 s) | — |
| Memoria máxima | | 110 MB (grande); 310 MB (2000 todas distintas, en cualquier esfuerzo) | < 500 MB ✔ |

Las medidas del banco y de esta tabla son con otras pruebas corriendo a la vez en la misma
máquina (puede sumar algo de tiempo). Con muchas medidas distintas el motor prueba menos
combinaciones (ver `DECISIONES.md`): antes de esta corrección, 200 piezas distintas tardaban 78 s
y 2000 distintas pasaban los 700 MB. Con más de 500 medidas distintas se usa solo la heurística
(con aviso), también en "Máximo".

El trabajo se corta por **cantidad** (tiras calculadas por el generador), no por reloj: en una PC
más lenta tarda más, pero da **el mismo resultado**. El reloj solo corta a los 60 s (normal) como
seguridad, y si eso pasa sale un aviso.

### 2.5 Esfuerzo máximo

Más trabajo (hasta 13 veces el normal), sigue buscando mientras la relajación diga que se puede
bajar una plancha, y bucea. Solo los casos de "corte perfecto" (corrida del 25/10 con el motor
actual; con otras pruebas corriendo a la vez en la misma máquina):

| Familia (hasta 100 piezas) | Normal | Máximo | Tiempo medio con máximo | Máximo |
|---|---|---|---|---|
| 3 etapas | 20 de 36 | **23 de 36 (64 %)** | 6,2 s | 29 s |
| Guillotina libre | 10 de 24 | **13 de 24 (54 %)** | 8,1 s | 28 s |

Los 12 casos de 101 a 121 piezas siguen con 1 plancha de más (hasta 129 s cada uno).

Mejora, pero tampoco llega al 95 %. Para un presupuesto difícil se puede elegir "Máximo" en la
interfaz.

## 3. Metas del brief (§14): dónde estamos

| Meta | Estado |
|---|---|
| 100 % de los resultados pasa el validador | ✔ (85 de 85 del banco, 500 de 500 de la prueba de estrés y los 2132 cálculos contra Corte Certo; 2 se rechazaban por un error de redondeo del validador, ya corregido) |
| Óptimo en ≥ 95 % del "corte perfecto" hasta 100 piezas | ✘ 50 % (56 % en 3 etapas, 42 % en guillotina libre) |
| Tiempos de §6.5 | ✔ en la nube para el típico y el grande; ✘ el peor caso (2000 piezas todas distintas) tarda 68 s. En la PC de la oficina va a tardar más: medirlo con §4 |
| Reproducir a Corte Certo en ≥ 90 % de los casos históricos | ✘ 80,0 % iguales (80,9 % con esfuerzo máximo en los peores); en los casos de hasta 20 piezas, 97,5 %. Juan, 25/10: no hace falta llegar al 90 % si ya da igual o mejor que Corte Certo |
| Igual o menos planchas que Corte Certo en ≥ 95 % | ✔ 96,5 % con la plancha con la que cierra cada caso (97,5 % con máximo en los peores); ✘ 88,5 % si se cotizan todos los casos viejos con 3580 |
| Números con la fórmula de Corte Certo al 0,01 % | ✔ el validador los recalcula en cada resultado; además, un test con las cuentas del 413 (733,9 m² y 76,93 %), que prueba la fórmula (no pasa por el motor) |

## 4. Para medir en la PC de la oficina

```text
.venv\Scripts\python.exe -m optimizador banco --esfuerzo rapido
.venv\Scripts\python.exe -m optimizador banco
```

Al final muestra un resumen y la máquina. Si algún caso da **más** planchas que lo guardado en
`tests/banco/esperado.json`, lo avisa ("EMPEORÓ").
