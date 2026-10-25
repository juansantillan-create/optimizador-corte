# Validación

Qué tan confiable es el optimizador, en palabras simples. Se actualiza cada vez que cambia el motor
(regla 7 de `CLAUDE.md`). Lo más nuevo, arriba.

## 1. Contra Corte Certo (casos históricos)

**Todavía no hay números reales**: los casos viejos no llegaron (`datos/casos/` está vacío). Todo
está listo para correr cuando lleguen:

```text
python -m optimizador historico                  # primero una muestra de 50 casos
python -m optimizador historico --todo --docs    # todos; escribe los números acá abajo
```

Qué hace (detalle en `optimizador/historico/comparar.py`):
1. Lee el zip o la carpeta del contrato (`docs/CONTRATO_DATOS.md`, versión 2) y avisa si algo no
   coincide con el contrato.
2. Busca la leyenda en "Situación de Presupuesto → Observaciones" (y en las otras columnas de texto)
   y la lee (`docs/FORMATO_LEYENDAS.md`). Cuenta cuántas lee y cuántas no, con ejemplos.
3. Reconstruye las piezas de cada presupuesto por material (DVH = 2 vidrios; herrajes, fletes,
   perforaciones, cámaras y láminas afuera; cada pieza de `DETPRES2` se cuenta una sola vez). Lo
   dudoso (DETPRES2 que no cierra con DETPRES, cantidad sacada de los m², DVH escalonado…) queda
   como aviso al lado del caso.
4. Relaciona el material abreviado de la leyenda ("4+4 NLIGHT") con el código de Metrix de las
   piezas del presupuesto (por composición y palabras, también el color). Si hay dudas, o si dos
   líneas van al mismo código, el caso va aparte.
5. **Control de la entrada**: los m² de las piezas, **con el +3 mm del pulido recto**, tienen que
   cerrar con las hojas y el % de la leyenda (±0,5 por el redondeo a entero, más 0,01 por el de
   Corte Certo; pregunta 24). Se prueban las medidas de plancha del material en las que entran las
   piezas; si cierra con más de una, se usa la más cercana y se avisa. Lo que no cierra se informa
   aparte con el motivo (el presupuesto cambió, otra plancha, cerraría solo sin el +3, la
   reconstrucción tiene avisos).
6. Calcula cada caso con H0, H1 y H2 **con la misma medida de plancha**, elige por grupo de
   material la que más se parece a Corte Certo usando el **70 %** de los casos (siempre los
   mismos, por número de presupuesto) e informa los números sobre el **30 %** restante. Los
   resultados que no pasan el validador o que dejan piezas sin calcular se cuentan aparte.
7. Arma la página de revisión (`salida/historico/revision.html`): caso por caso, nuestros montajes
   al lado de los números de Corte Certo, filtros (peores, mejores…), marcas bien/mal/duda y un
   botón "Copiar mis respuestas" para pegar en la sesión.

Lo calculado se guarda a medida que sale (`salida/historico/`, no va a git): si se corta, se
vuelve a correr el mismo comando y sigue donde quedó. Con esfuerzo normal tarda unos segundos por
caso y por hipótesis; para miles de casos conviene `--esfuerzo rapido` primero.

**Prueba con el caso de juguete** (`tests/historico_juguete/`, 19 presupuestos **inventados** que
genera `herramientas/generar_caso_juguete.py`): corre de punta a punta; lee 17 leyendas, no puede
leer 1 (a propósito), no puede relacionar 1 (material ambiguo, a propósito), 1 no cierra (a
propósito) y compara el resto con las 3 hipótesis. **Esos números no dicen nada del optimizador**:
las "hojas de Corte Certo" del juguete son inventadas (algunas, imposibles).

## 2. Banco sintético (25/10/2026, motor con las correcciones de las revisiones de F1 a F4)

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
| 3 etapas | 36 | **20 (56 %)** | 16 (siempre 1 en los que falló) | 9,5 s |
| Guillotina libre | 24 | **10 (42 %)** | 14 (siempre 1) | 8,3 s |

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
| RE-2000 | 20 | 2 | 2 | — | 2 | 0,04 |
| RE-2001 | 50 | 6 | 6 | — | 6 | 0,2 |
| RE-2002 | 80 | 6 | 6 | — | 6 | 0,5 |
| RE-2003 | 120 | 21 | 19 | 19,90 | 15 | 1,8 |
| RE-2004 | 300 | 46 | 43 | 44,28 | 25 | 5,4 |
| RE-2005 | 300 | 13 | 12 | 12,02 | 13 | 7,4 |
| RE-2006 | 40 | 9 | 8 | 8,50 | 7 | 0,1 |
| RE-2007 | 200 | 25 | 24 | 24,06 | 20 | 3,7 |
| RE-2008 | 60 | 3 | 3 | — | 3 | 0,2 |
| RE-2009 | 250 | 50 | 47 | 49,46 | 31 | 2,4 |
| T413-3000 | 252 | 73 | 64 | 72,94 | 20 | 0,3 |
| T413-3001 | 252 | 73 | 61 | 72,06 | 18 | 0,4 |
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
| Memoria máxima | | 110 MB (grande); 310 MB (2000 todas distintas) | < 500 MB ✔ |

Las medidas del banco y de esta tabla son con otras pruebas corriendo a la vez en la misma
máquina (puede sumar algo de tiempo). Con muchas medidas distintas el motor prueba menos
combinaciones (ver `DECISIONES.md`): antes de esta corrección, 200 piezas distintas tardaban 78 s
y 2000 distintas pasaban los 700 MB.

El trabajo se corta por **cantidad** (tiras calculadas por el generador), no por reloj: en una PC
más lenta tarda más, pero da **el mismo resultado**. El reloj solo corta a los 60 s (normal) como
seguridad, y si eso pasa sale un aviso.

### 2.5 Esfuerzo máximo

Más trabajo (hasta 13 veces el normal), sigue buscando mientras la relajación diga que se puede
bajar una plancha, y bucea. Solo los casos de "corte perfecto" (corrida del 25/10, versión anterior
a la corrección de la caché del 25/10 — ver la próxima corrida):

| Familia (hasta 100 piezas) | Normal | Máximo | Tiempo medio con máximo | Máximo |
|---|---|---|---|---|
| 3 etapas | 20 de 36 | **23 de 36 (64 %)** | 6,6 s | 40 s |
| Guillotina libre | 10 de 24 | **13 de 24 (54 %)** | 39 s | 153 s |

Mejora, pero tampoco llega al 95 %. Para un presupuesto difícil se puede elegir "Máximo" en la
interfaz.

## 3. Metas del brief (§14): dónde estamos

| Meta | Estado |
|---|---|
| 100 % de los resultados pasa el validador | ✔ (85 de 85 del banco y 500 de 500 de la prueba de estrés) |
| Óptimo en ≥ 95 % del "corte perfecto" hasta 100 piezas | ✘ 50 % (56 % en 3 etapas, 42 % en guillotina libre) |
| Tiempos de §6.5 | ✔ en la nube para el típico y el grande; ✘ el peor caso (2000 piezas todas distintas) tarda 68 s. En la PC de la oficina va a tardar más: medirlo con §4 |
| Reproducir a Corte Certo en ≥ 90 % de los casos históricos | pendiente: faltan los datos |
| Igual o menos planchas que Corte Certo en ≥ 95 % | pendiente: faltan los datos |
| Números con la fórmula de Corte Certo al 0,01 % | ✔ el validador los recalcula en cada resultado; además, un test con las cuentas del 413 (733,9 m² y 76,93 %), que prueba la fórmula (no pasa por el motor) |

## 4. Para medir en la PC de la oficina

```text
.venv\Scripts\python.exe -m optimizador banco --esfuerzo rapido
.venv\Scripts\python.exe -m optimizador banco
```

Al final muestra un resumen y la máquina. Si algún caso da **más** planchas que lo guardado en
`tests/banco/esperado.json`, lo avisa ("EMPEORÓ").
