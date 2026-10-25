# Validación

Qué tan confiable es el optimizador, en palabras simples. Se actualiza cada vez que cambia el motor
(regla 7 de `CLAUDE.md`). Lo más nuevo, arriba.

## 1. Contra Corte Certo (casos históricos)

**En pocas palabras** (corrida del 25/10/2026, esfuerzo normal, 1122 casos que se pudieron
comparar de los 1341 que llegaron):

- **78,6 % da las mismas hojas que Corte Certo**, 13,4 % da menos y 8,0 % da más, con la plancha de
  3580 × 2500 (banda 20, como cotiza el programa).
- Si Corte Certo usaba la hoja entera de 3600 (pregunta 28): 80,2 % iguales, 17,6 % menos y 2,1 %
  más. En los 132 casos donde se sabe cuál usó: 78,0 % iguales, 21,2 % menos y 0,8 % más (1 caso,
  por 1 hoja).
- Cuanto más chico el presupuesto, más se parece: hasta 20 piezas, 97,5 % iguales; con más de 100
  piezas, 59 % iguales y 29,5 % con menos hojas.
- Con **esfuerzo máximo** en los 113 casos donde el normal daba más hojas, 27 mejoran: quedan
  79,9 % iguales y 6,6 % con más (banda 20), o 81,0 % y 1,2 % (hoja entera). El más lento tardó
  5 minutos (1364 piezas de 258 medidas).
- Los que siguen dando más son sobre todo casos con una medida de hoja deducida (que no está en
  `hojas.csv` para ese vidrio: puede no ser la real, pregunta 29) y algunos chicos muy apretados
  (ej. 7319: 52 piezas al 96 % en 8 hojas; el programa da 10).
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
| Sin piezas | 0 |
| No cierran: los m² no dan el % de la leyenda (el presupuesto cambió o era otra plancha) | 43 |
| No cierran: las piezas no entran en ninguna plancha del material | 1 |
| **Pasaron el control y se compararon** | **1122** |
| … de esos, cierran solo SIN el +3 mm del pulido (se calcularon sin el +3) | 3 |
| … con las medidas de hoja anotadas en la leyenda | 48 |
| … con plancha supuesta (el material no está en hojas.csv) | 43 |
| … con una medida de hoja que hojas.csv no tiene para ese material (ver abajo) | 244 |
| … con más de una medida de plancha que cierra (se usó la más cercana) | 36 |
| … donde con banda 20 no cierra o las piezas no entran, y se usó la hoja entera | 64 |
| … donde cierran las dos (banda 20 y hoja entera): ver la línea de abajo | 990 |

**Medidas de hoja que Corte Certo usó y no están en `hojas.csv`** (habría que sumarlas a `Medidas_hojas.xlsx`; pregunta 29)

| Material | Medida (casos) |
|---|---|
| LX3+3LOWE | 3300x2440 (95), 3600x2140 (2), 3600x2200 (1), 3660x2440 (1) |
| LX4+4GC | 3600x2500 (26), 3600x2540 (1) |
| CK8K1 | 3210x2540 (25) |
| LX4+4ST120 | 3600x2140 (14), 3210x2400 (7), 3300x2440 (1) |
| CT6G1 | 3210x2540 (13) |
| CK8K2 | 3210x2540 (12) |
| CS6S2 | 3210x2550 (5) |
| EC6CL | 3300x2440 (3) |
| LX4+4LOWE | 3600x2140 (1), 3600x2200 (1), 3210x2500 (1) |
| GRAPH6 | 2500x1600 (3) |
| CK6K2 | 3300x2440 (2), 3210x2500 (1) |
| CK6K1 | 3210x2500 (1), 3600x2140 (1), 3660x2440 (1) |
| LX5+5IN | 3660x2440 (1), 3700x2500 (1) |
| OL3+3IN | 3600x2500 (2) |
| FL6GR | 3310x2130 (1), 3210x2200 (1) |
| LX4+4IN | 3210x2400 (1), 3660x2440 (1) |
| LX4+4NL | 3210x2550 (1), 3660x2440 (1) |
| CK6KB | 3210x2540 (2) |
| FL4GR | 3600x2500 (1) |
| FL8GR | 3600x2500 (1) |
| SO6OC | 3600x2500 (1) |
| CS8S2 | 3210x2550 (1) |
| CK8K3 | 3210x2540 (1) |
| LX4+4IN76 | 3210x2400 (1) |
| LX4+4ST150 | 3210x2500 (1) |
| LX6+6K114 | 3210x2550 (1) |
| CK6K3 | 3300x2440 (1) |
| CS8S1 | 3210x2540 (1) |
| SO6BL | 3300x2440 (1) |
| OP4IN | 3210x2550 (1) |
| SO6OG | 3600x2500 (1) |
| LX5+5AV | 3660x2440 (1) |

**Según de dónde salió la medida de hoja**

| Medida de hoja | Casos | Iguales | Menos planchas | Más planchas | Dif. media |
|---|---|---|---|---|---|
| la medida de hoja del material en hojas.csv | 830 | 80.5 % | 11.7 % | 7.8 % | -0.07 |
| las medidas de hoja anotadas en la leyenda | 48 | 72.9 % | 16.7 % | 10.4 % | -0.12 |
| una medida deducida (hojas.csv no la tiene para ese material) | 244 | 73.4 % | 18.4 % | 8.2 % | -0.13 |

**Banda 20 u hoja entera** (pregunta 28): en la mayoría de los casos el % de Corte Certo cierra con las dos, así que se calcularon las dos y se muestran los dos extremos. La tercera fila son los casos donde se sabe cuál usó (cierra una sola, o las piezas no entran en la otra).

| Supuesto sobre Corte Certo | Casos | Iguales | Menos planchas | Más planchas | Dif. media | Peor |
|---|---|---|---|---|---|---|
| Banda 20 donde cierran las dos (la cuenta principal) | 1122 | 78.6 % | 13.4 % | 8.0 % | -0.08 | +15 |
| Hoja entera donde cierran las dos | 1122 | 80.2 % | 17.6 % | 2.1 % | -0.29 | +11 |
| Solo los casos donde cierra una sola de las dos (se sabe cuál usó Corte Certo) | 132 | 78.0 % | 21.2 % | 0.8 % | -0.47 | +1 |

**Resultado con banda 20 (todos los casos comparados)**

- Casos: 1122
- Iguales a Corte Certo: 78.6 %; con menos planchas: 13.4 %; con más planchas: 8.0 %
- Diferencia media: -0.08 planchas por caso (negativo = a favor); la peor: +15
- Casos donde Corte Certo ya estaba en el mínimo teórico: 282
- Casos donde la leyenda dice menos hojas que el mínimo teórico (imposible; hay que mirarlos): 0
- Casos comparados con avisos: 331
- Resultados que no pasaron el validador (fuera de las cuentas): 0
- Resultados con piezas sin calcular (fuera de las cuentas): 0

| Material | Casos | Iguales | Mejores | Peores | Dif. media |
|---|---|---|---|---|---|
| CK6K1 | 169 | 75.7 % | 16.0 % | 8.3 % | -0.17 |
| CK6K2 | 46 | 78.3 % | 8.7 % | 13.0 % | -0.26 |
| CK6K3 | 21 | 81.0 % | 14.3 % | 4.8 % | -0.24 |
| CK6KB | 2 | 50.0 % | 50.0 % | 0.0 % | -0.5 |
| CK6KG | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CK8K1 | 30 | 96.7 % | 3.3 % | 0.0 % | -0.03 |
| CK8K2 | 17 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CK8K3 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CS6S1 | 1 | 0.0 % | 100.0 % | 0.0 % | -4.0 |
| CS6S2 | 5 | 60.0 % | 40.0 % | 0.0 % | -2.2 |
| CS8S1 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CS8S2 | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CT6AZ | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| CT6G1 | 15 | 73.3 % | 26.7 % | 0.0 % | -0.27 |
| CT6G2 | 11 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6AR | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6BL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6CL | 3 | 66.7 % | 33.3 % | 0.0 % | -0.67 |
| EC6EV | 14 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| EC6GY | 70 | 74.3 % | 21.4 % | 4.3 % | -0.16 |
| FL4GR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL4IN | 5 | 80.0 % | 20.0 % | 0.0 % | -0.2 |
| FL5BR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL5IN | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL6BR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL6GR | 7 | 42.9 % | 14.3 % | 42.9 % | +1.71 |
| FL6IN | 2 | 50.0 % | 0.0 % | 50.0 % | +0.5 |
| FL6NL | 11 | 45.5 % | 45.5 % | 9.1 % | +0.64 |
| FL8GR | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL8IN | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| FL8NL | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| GRAPH6 | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LA5+5VC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LO6IN | 16 | 50.0 % | 25.0 % | 25.0 % | -0.31 |
| LX3+3BC | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3BO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3ES | 19 | 94.7 % | 5.3 % | 0.0 % | -0.05 |
| LX3+3ESL | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3GC | 7 | 71.4 % | 14.3 % | 14.3 % | +0.0 |
| LX3+3GCESM | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3GO | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3IN | 42 | 64.3 % | 16.7 % | 19.0 % | +0.02 |
| LX3+3IN76 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX3+3LOWE | 103 | 69.9 % | 21.4 % | 8.7 % | -0.11 |
| LX3+3OPBR | 2 | 50.0 % | 50.0 % | 0.0 % | -0.5 |
| LX4+4ES | 10 | 80.0 % | 0.0 % | 20.0 % | +0.2 |
| LX4+4ESL | 3 | 66.7 % | 33.3 % | 0.0 % | -0.33 |
| LX4+4GC | 27 | 74.1 % | 14.8 % | 11.1 % | -0.04 |
| LX4+4GO | 7 | 85.7 % | 0.0 % | 14.3 % | +0.29 |
| LX4+4IN | 77 | 76.6 % | 11.7 % | 11.7 % | -0.09 |
| LX4+4IN76 | 3 | 33.3 % | 33.3 % | 33.3 % | -1.67 |
| LX4+4LOWE | 59 | 89.8 % | 5.1 % | 5.1 % | +0.0 |
| LX4+4NL | 25 | 84.0 % | 8.0 % | 8.0 % | +0.52 |
| LX4+4NL114 | 1 | 0.0 % | 100.0 % | 0.0 % | -1.0 |
| LX4+4ST120 | 24 | 66.7 % | 25.0 % | 8.3 % | -0.58 |
| LX4+4ST150 | 23 | 87.0 % | 4.3 % | 8.7 % | +0.09 |
| LX4+4STB12 | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX4+4VC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX4+4VO | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+3AC | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5AV | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5BC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5ES | 5 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5ESL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5GC | 3 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5GO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX5+5IN | 62 | 88.7 % | 8.1 % | 3.2 % | -0.06 |
| LX5+5IN76 | 6 | 50.0 % | 50.0 % | 0.0 % | -1.0 |
| LX5+5NL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6GC | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6GO | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6IN | 24 | 70.8 % | 4.2 % | 25.0 % | +0.42 |
| LX6+6IN76 | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| LX6+6K114 | 1 | 0.0 % | 100.0 % | 0.0 % | -1.0 |
| LX6+6NL114 | 2 | 50.0 % | 50.0 % | 0.0 % | -0.5 |
| OA4IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OA8IN | 4 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OL3+3IN | 2 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OP4IN | 11 | 90.9 % | 0.0 % | 9.1 % | +0.09 |
| OP5IN | 6 | 66.7 % | 16.7 % | 16.7 % | +0.0 |
| OP6GR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| OP6IN | 4 | 25.0 % | 50.0 % | 25.0 % | -0.25 |
| SO6BL | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| SO6OC | 16 | 68.8 % | 18.8 % | 12.5 % | +0.0 |
| SO6OG | 7 | 71.4 % | 28.6 % | 0.0 % | -0.71 |
| SU6AR | 1 | 100.0 % | 0.0 % | 0.0 % | +0.0 |
| SU6SU | 30 | 93.3 % | 3.3 % | 3.3 % | +0.0 |

| Tamaño | Casos | Iguales | Mejores | Peores | Dif. media |
|---|---|---|---|---|---|
| hasta 20 piezas | 279 | 97.5 % | 0.4 % | 2.2 % | +0.02 |
| 21 a 100 piezas | 433 | 85.0 % | 6.5 % | 8.5 % | +0.05 |
| más de 100 piezas | 410 | 59.0 % | 29.5 % | 11.5 % | -0.3 |

**Los peores (más planchas que Corte Certo)**

| Presupuesto | Material | Piezas | Corte Certo | Nuestro | Mínimo teórico | Plancha |
|---|---|---|---|---|---|---|
| 6348 | LX4+4NL | 551 | 204 (81 %) | 219 (75.72 %) | 166 | 3600x2500 |
| 6358 | FL6NL | 551 | 204 (81 %) | 219 (75.72 %) | 166 | 3600x2500 |
| 6094 | FL6GR | 342 | 155 (79 %) | 167 (73.86 %) | 124 | 3310x2130 |
| 10510 | CK6K3 | 194 | 51 (89 %) | 62 (73.42 %) | 46 | 3300x2440 |
| 7490 | CK6K1 | 218 | 84 (88 %) | 92 (81.19 %) | 75 | 3210x2540 |
| 7152 | LX3+3IN | 436 | 115 (98 %) | 121 (93.6 %) | 114 | 3600x2500 |
| 4931 | LX4+4IN | 66 | 28 (87 %) | 33 (74.51 %) | 25 | 3600x2500 |
| 5701 | LX3+3LOWE | 166 | 60 (87 %) | 65 (81.1 %) | 53 | 3300x2440 |
| 9524 | EC6GY | 173 | 68 (91 %) | 73 (85.67 %) | 63 | 3300x2440 |
| 9524 | LX3+3LOWE | 173 | 68 (91 %) | 73 (85.67 %) | 63 | 3300x2440 |
<!-- /HISTORICO -->

**Cómo se hizo** (detalle en `optimizador/historico/exportados.py`). Para repetirlo:

```text
python -m optimizador historico --todo --procesos 3 --docs
```

1. Los casos llegaron ya leídos, uno por presupuesto y vidrio (`datos/casos/corte_certo/`): las
   piezas (con el +3 mm del pulido recto ya sumado) y lo que dice la leyenda de Corte Certo (hojas,
   %, bandas).
2. **Control de la entrada**: los m² de las piezas tienen que cerrar con las hojas y el % de la
   leyenda. El % pudo quedar redondeado o truncado (pregunta 24). Se prueban la plancha con la
   banda de 20 mm (3580 × 2500) y la hoja entera (3600 × 2500), con las medidas de hoja del vidrio
   en `hojas.csv` o las anotadas en la leyenda; si ninguna cierra, otras medidas conocidas (primero
   las de la misma familia de vidrio), y eso se avisa (pregunta 29). Se prueba primero con el +3 y,
   si no cierra, sin (pregunta 25).
3. **¿Entran las piezas?** Una plancha se descarta si con ella no se puede llegar a las hojas de
   Corte Certo: por área, por piezas que no entran dos juntas, y por cuántas piezas de una misma
   medida entran como mucho en una plancha (ej. 900 × 478: 17 en la de 3580 y 20 en la de 3600).
   Así se vio que muchos de los "peores" casos de la primera corrida eran casos donde Corte Certo
   usó la hoja entera.
4. Se calcula cada caso como estaba Corte Certo: sin separación ni destaque (H0), con la plancha
   que dio el control. Si cierran las dos (banda 20 y hoja entera), se calculan las dos.
5. No hay calibración ni muestra de prueba: hay una sola configuración (Juan, 25/10: Corte Certo
   no se usaba con separación), así que los números son sobre **todos** los casos comparados.
6. Todo resultado pasa por el validador; los que no pasan o dejan piezas sin calcular se cuentan
   aparte.

Lo calculado se guarda a medida que sale (`salida/historico/`, no va a git): si se corta, se vuelve
a correr el mismo comando y sigue donde quedó. Con `--procesos 3` los 2112 cálculos tardan unos
15 minutos en la nube.

El método viejo (el zip del contrato v2, con las leyendas por leer y las piezas por reconstruir
desde Metrix) sigue en `optimizador/historico/comparar.py` y se prueba con el caso de juguete
(`tests/historico_juguete/`, 19 presupuestos **inventados**: esos números no dicen nada del
optimizador).

## 1.b Contra Optima (cortes reales en planta)

**En pocas palabras**: con la configuración de producción (banda y destaque de la regla de Lucas) y
las mismas medidas de hoja, el programa usa **los mismos m² de hoja que Optima en 3 de los 5 lotes**,
3,4 % menos en uno (FL10IN) y 1,8 % más en otro (FL6IN, donde Optima usó dos retazos de stock en vez
de una hoja; al cotizar no se usan retazos, pregunta 11). En total, 0,5 % menos vidrio. Son solo 5
lotes: sirve para ver que la configuración de Optima está bien entendida, no como estadística.
Para repetirlo: `python -m optimizador optima --docs`.

<!-- OPTIMA: lo escribe `python -m optimizador optima --docs` -->
Datos: `datos/casos/optima` (5 lotes cortados en planta con Optima). Esfuerzo: maximo. Mismas piezas y mismas medidas de hoja que usó Optima; corte banda y destaque mínimo de la regla de Lucas (preset "Reglas de corte (Lucas, como Optima)"). Optima usó las hojas que había (y en un lote, retazos); el programa puede usar todas las que quiera de cada medida, así que se comparan los **m² de hoja**.

| Lote | Vidrio | Piezas | Optima: hojas | Optima: m² de hoja | Nuestro: hojas | Nuestro: m² de hoja | Diferencia | Aprov. bruto Optima → nuestro | Como cotización (m²) |
|---|---|---|---|---|---|---|---|---|---|
| 164601 | CA4PA | 33 | 3×2500×1600 | 12.00 | 3×2500×1600 | 12.00 | +0.00 m² (+0.0 %) | 77 % → 77 % | 12.00 |
| 165903 | FL5IN | 75 | 2×3600×2500; 7×3600×2200 | 73.44 | 2×3600×2500; 7×3600×2200 | 73.44 | +0.00 m² (+0.0 %) | 93.3 % → 93.3 % | 72.36 |
| 172802 | FL8IN | 29 | 4×3600×2500 | 36.00 | 4×3600×2500 | 36.00 | +0.00 m² (+0.0 %) | 86.5 % → 86.5 % | 36.00 |
| 172905 | FL6IN | 38 | 10×3600×2500 + retazos 2×3580×1010 | 97.23 | 11×3600×2500 | 99.00 | +1.77 m² (+1.8 %) | 88.7 % → 87.1 % | 99.00 |
| 173703 | FL10IN | 54 | 8×3700×2500; 1×3700×2200; 2×3050×2050 | 94.64 | 9×3700×2500; 1×3700×2200 | 91.39 | -3.25 m² (-3.4 %) | 83.4 % → 86.4 % | 87.28 |

Total: Optima 313.32 m² de hoja; nuestro 311.83 m² (-0.5 %). Negativo = el programa usa menos vidrio.
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
| 100 % de los resultados pasa el validador | ✔ (85 de 85 del banco, 500 de 500 de la prueba de estrés y los 2112 cálculos contra Corte Certo; 2 de esos se rechazaban por un error de redondeo del validador, ya corregido) |
| Óptimo en ≥ 95 % del "corte perfecto" hasta 100 piezas | ✘ 50 % (56 % en 3 etapas, 42 % en guillotina libre) |
| Tiempos de §6.5 | ✔ en la nube para el típico y el grande; ✘ el peor caso (2000 piezas todas distintas) tarda 68 s. En la PC de la oficina va a tardar más: medirlo con §4 |
| Reproducir a Corte Certo en ≥ 90 % de los casos históricos | ✘ 78,6 % iguales (80,2 % si Corte Certo usaba la hoja entera); en los casos de hasta 20 piezas, 97,5 % |
| Igual o menos planchas que Corte Certo en ≥ 95 % | ✘ 92,0 % con banda 20; ✔ 97,9 % si Corte Certo usaba la hoja entera, y 99,2 % en los 132 casos donde se sabe cuál usó |
| Números con la fórmula de Corte Certo al 0,01 % | ✔ el validador los recalcula en cada resultado; además, un test con las cuentas del 413 (733,9 m² y 76,93 %), que prueba la fórmula (no pasa por el motor) |

## 4. Para medir en la PC de la oficina

```text
.venv\Scripts\python.exe -m optimizador banco --esfuerzo rapido
.venv\Scripts\python.exe -m optimizador banco
```

Al final muestra un resumen y la máquina. Si algún caso da **más** planchas que lo guardado en
`tests/banco/esperado.json`, lo avisa ("EMPEORÓ").
