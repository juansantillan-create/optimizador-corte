# Validación

Qué tan confiable es el optimizador, en palabras simples. Se actualiza cada vez que cambia el motor
(regla 7 de `CLAUDE.md`). Lo más nuevo, arriba.

## 1. Contra Corte Certo (casos históricos)

**Todavía no hay números**: los casos viejos no llegaron (`datos/casos/` está vacío). Todo está
listo para correr cuando lleguen (fase F4, ver `docs/CONTRATO_DATOS.md`).

## 2. Banco sintético (25/10/2026, versión 0.1 del motor)

Máquina: nube, Linux, Python 3.13, Intel Xeon 2,8 GHz, 4 núcleos (el cálculo usa uno solo). La PC
de la oficina va a ser más lenta: para medirla, `python -m optimizador banco` (ver §4).

85 casos fijos en `tests/banco/` (semillas fijas). Para correrlos:
`python -m optimizador banco` (tarda unos 5 minutos).

### 2.1 Todo resultado pasa el validador

| Prueba | Casos | Pasaron el validador |
|---|---|---|
| Banco sintético | 85 | **85 (100 %)** |
| Instancias al azar (con separación, destaque, veta, constantes, márgenes, varias planchas) | 500 | **500 (100 %)** |
| Tests con instancias al azar (`hypothesis`, en cada `pytest`) | 60 por corrida | 100 % |

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
| 3 etapas | 36 | **20 (56 %)** | 16 (siempre 1 en los que falló) | 9 s |
| Guillotina libre | 24 | **10 (42 %)** | 14 | 15 s |

Además hay 12 casos de guillotina libre con 100 a 121 piezas: ninguno en el óptimo (1 o 2 planchas
de más).

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
| RE-2000 | 20 | 2 | 2 | — | 2 | 0,04 |
| RE-2001 | 50 | 6 | 6 | — | 6 | 0,2 |
| RE-2002 | 80 | 6 | 6 | — | 6 | 0,4 |
| RE-2003 | 120 | 21 | 19 | 19,90 | 15 | 2,3 |
| RE-2004 | 300 | 46 | 43 | 44,28 | 25 | 5,5 |
| RE-2005 | 300 | 13 | 12 | 12,02 | 13 | 7,4 |
| RE-2006 | 40 | 9 | 8 | 8,50 | 7 | 0,2 |
| RE-2007 | 200 | 25 | 24 | 24,06 | 20 | 4,0 |
| RE-2008 | 60 | 3 | 3 | — | 3 | 0,2 |
| RE-2009 | 250 | 50 | 47 | 49,46 | 31 | 3,1 |
| T413-3000 | 252 | 73 | 64 | 72,94 | 20 | 0,6 |
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
| Típico: 300 piezas, 30 medidas de 300 a 2400 mm | 1,1 s | 4–5 s | < 2 s / ≤ 10 s ✔ |
| Típico: 300 piezas, 30 medidas de 300 a 1200 mm | 1,8 s | 7–12 s | < 2 s / ≤ 10 s (justo) |
| Como el 413: 252 piezas grandes | 0,1 s | 0,3 s | ✔ |
| Grande: 2000 piezas, 60 medidas | 6,9 s | 21 s | ≤ 60 s ✔ |
| Memoria máxima (caso grande) | | 109 MB | < 500 MB ✔ |

El trabajo se corta por **cantidad** (tiras calculadas por el generador), no por reloj: en una PC
más lenta tarda más, pero da **el mismo resultado**. El reloj solo corta a los 60 s (normal) como
seguridad, y si eso pasa sale un aviso.

### 2.5 Esfuerzo máximo

Se corre aparte (tarda mucho más). Resultados: ver la próxima actualización de este archivo.

## 3. Metas del brief (§14): dónde estamos

| Meta | Estado |
|---|---|
| 100 % de los resultados pasa el validador | ✔ (585 de 585 casos) |
| Óptimo en ≥ 95 % del "corte perfecto" hasta 100 piezas | ✘ 50 % (56 % en 3 etapas, 42 % en guillotina libre) |
| Tiempos de §6.5 | ✔ en la nube (el típico de piezas medianas queda justo en 10 s) |
| Reproducir a Corte Certo en ≥ 90 % de los casos históricos | pendiente: faltan los datos |
| Igual o menos planchas que Corte Certo en ≥ 95 % | pendiente: faltan los datos |
| Números con la fórmula de Corte Certo al 0,01 % | ✔ (test con las cuentas del 413: 733,9 m² y 76,93 %) |

## 4. Para medir en la PC de la oficina

```text
.venv\Scripts\python.exe -m optimizador banco --esfuerzo rapido
.venv\Scripts\python.exe -m optimizador banco
```

Al final muestra un resumen y la máquina. Si algún caso da **más** planchas que lo guardado en
`tests/banco/esperado.json`, lo avisa ("EMPEORÓ").
