# Preguntas abiertas (para Juan)

Contestá en texto libre debajo de cada una ("sí", "no, va con 20", "preguntale a Lucas"…). La
próxima sesión lee las respuestas, las aplica, anota la decisión en `DECISIONES.md` y la mueve a
"Respondidas". Mientras tanto, el programa usa la opción **por defecto**.

## Abiertas

**28. ¿Corte Certo tenía cargada la plancha con banda de 20 mm (3580 × 2500) o la hoja entera (3600 × 2500)?**
- Con la banda de Lucas (30 o 50) el % de Corte Certo casi nunca cierra: eso está claro. Pero entre
  banda 20 y hoja entera los casos viejos muestran **las dos cosas**:
  - en 990 de 1122 casos el % cierra con las dos (20 mm en 3600 es apenas 0,5 %);
  - en 68 solo puede ser banda 20;
  - en 64 solo puede ser la hoja entera. Por ejemplo, el presupuesto 7781: 7800 piezas de
    900 × 478 en 412 hojas. En la de 3580 entran como mucho 17 por hoja (harían falta 459); en la
    de 3600 entran 20 (4 × 900 = 3600 justo). O el 10921: piezas de 2170 y 1430 de ancho, que
    suman 3600 justo, al 100 %.
  - Pasa en todas las épocas y en casi todos los vidrios; desde septiembre de 2026 se ven más
    casos de banda 20.
- ¿Puede ser que cada PC (o cada comercial) tuviera Corte Certo cargado distinto, o que se haya
  cambiado en algún momento?
- **Por qué importa**: con la hoja entera entran 20 mm más por hoja. Casi nunca cambia la cantidad
  de hojas, pero cuando las piezas suman justo 3600 sí (en el 7781, 47 hojas de diferencia).
- **Cómo da el programa en cada caso** (`docs/VALIDACION.md` §1): si Corte Certo usaba banda 20,
  78,6 % de los casos iguales y 8,0 % con más planchas; si usaba la hoja entera, 80,2 % iguales y
  2,1 % con más.
- **Por defecto**: "Como Corte Certo hoy" usa banda 20 en todos los vidrios (lo prudente: nunca
  cotiza menos vidrio del que se puede cortar). Si me decís que se cotiza con la hoja entera, se
  cambia en una línea (`BANDA_CORTE_CERTO_MM` en `optimizador/configuracion.py`).
- Respuesta:

**29. Medidas de hoja que Corte Certo usó y no están en `Medidas_hojas.xlsx`**
- En muchos casos viejos el % de Corte Certo solo cierra con una medida de hoja que la planilla
  no tiene para ese vidrio. La lista (material → medida que cierra, y en cuántos casos) está en
  `docs/VALIDACION.md` §1, tabla "Medidas de hoja que Corte Certo usó y no están en hojas.csv".
  Las más repetidas: LX3+3LOWE con 3300 × 2440 (95 casos); LX4+4GC con 3600 × 2500 (26); CK8K1
  (25), CT6G1 (13) y CK8K2 (12) con 3210 × 2540; LX4+4ST120 con 3600 × 2140 (14) o 3210 × 2400 (7).
- **Por qué importa**: para cotizar esos vidrios el programa usa la plancha de la planilla (o una
  supuesta de 3600 × 2500), que puede no ser la real.
- **Por defecto**: no se cambió la planilla. Si me confirmás las medidas (o actualizás
  `Medidas_hojas.xlsx`), se cargan con `herramientas/importar_medidas_hojas.py`.
- Respuesta:

**30. Plancha por defecto cuando no hay 3600 × 2500**
- Contestaste (pregunta 3): "si está la opción de 3600 × 2500, usar siempre esa; si no, en el caso
  de 6 mm la de 3700 × 2500". En la planilla, la de 3700 × 2500 la tiene el **FL 10 mm**, no los
  de 6 mm.
- **Por defecto**: si el material tiene 3600 × 2500, solo esa; si no, 3700 × 2500; si no tiene
  ninguna de las dos (Cool Lite 3210 × 2540, Eclipse 3300 × 2440…), todas las suyas y el programa
  elige la combinación de menos m².
- Respuesta:

**16. ¿Las mesas u Optima limitan las etapas de corte (X, Y, Z)?**
- Para cotizar no cambia tanto, pero sirve para que el montaje sea cortable de verdad.
- **Por defecto**: no se configura un límite. El generador arma montajes de 3 o 4 etapas (como
  los de la captura de Corte Certo) y el validador acepta cualquier guillotina.
- Respuesta (25/10): "no lo sé". Queda abierta por si alguien de producción lo sabe.

## Respondidas (25/10/2026)

| # | Pregunta | Respuesta de Juan | Qué se hizo |
|---|---|---|---|
| 1 | ¿Corte Certo se usaba con separación entre piezas? | No | Confirmado el preset "Como Corte Certo hoy" sin separación |
| 2 | "20 mm de distancia mínima entre piezas": ¿separación o tira mínima? | Es la (b): pueden compartir el corte, pero una tira de sobrante entre piezas mide al menos 20 | El preset de Lucas usa la distancia como **destaque mínimo** ("Reglas de corte (Lucas, como Optima)") |
| 3 | ¿Con qué medida de plancha se cotiza? | La de 3600 × 2500 si está; si no, la de 3700 × 2500 | Plancha por defecto así; las demás quedan deshabilitadas (ver la 30) |
| 4 | ¿El pulido de aristas suma? ¿El +3 del PR se cargaba en Corte Certo? | El de aristas no suma; el PR sí, y se sumaba a mano antes de importar | Sin cambios: era lo que se hacía |
| 5 | ¿Qué quieren decir los colores de los montajes? | Solo para distinguir las piezas; el amarillo siempre es sobrante | Sin cambios |
| 6 | "Cálculo especial de perímetro" | No se usa | Queda en 0,00 |
| 7 | Capturas de "Descripción" y "Propiedades comerciales" | Con lo que hay alcanza | Sin cambios |
| 8 | ¿En qué columna de `PRESUP` está la leyenda? | Ya está en los casos que mandé | Era `PRESUP.NOTAS_SITUACION`; los casos llegaron ya leídos (`datos/casos/corte_certo/`) |
| 9 | ¿El aprovechamiento va sobre la plancha útil o la hoja entera? | Sobre la hoja usada: si se usa la de 3580, esa | Sin cambios: sobre la plancha útil, como Corte Certo |
| 10 | ¿Hay vidrios que no se pueden girar? | Todos se pueden girar | Sin cambios |
| 11 | ¿Se cotiza con retazos de stock? | No | Sin cambios |
| 12 | ¿Corte Certo guarda los proyectos? | No | — |
| 13 | Columnas de la planilla de la Interfaz | TIPO / VIDRIO1 / CAMARA / VIDRIO2 / ANCHO / LARGO / ANCHO2 / LARGO2 / CANTIDAD / TIPOLOGIA / OBS / NTAS / CLASE / CLASE CARA1 / CLASE CARA2 | El importador usa la CANTIDAD de la columna I y ANCHO2/LARGO2 para el vidrio 2 de un DVH escalonado |
| 14 | Materiales que no están en `Medidas_hojas.xlsx` | Está bien la plancha supuesta de 3600 × 2500 | Sin cambios |
| 15 | Separación de los materiales que no menciona la regla de Lucas | Por defecto | Sin cambios |
| 17 | ¿Códigos de material de Corte Certo? | Códigos nuestros nomás | Sin cambios |
| 18 | ¿Qué lado va con la veta? | No te preocupes: para cotizar no va al caso | Sin cambios |
| 19 | Mezclar medidas de plancha: ¿gana la de menos m²? | Sí | Sin cambios |
| 20 | ¿Qué Python tiene la PC? | Se puede instalar cualquiera de los dos (3.12 o 3.13) | Sin cambios |
| 21 | Nombres de compañeros en los documentos de la fábrica | Está bien así | Sin cambios |
| 22 | ¿Faltó algún archivo? | Seguí con lo que hay | — |
| 23 | Perímetro: ¿por material o total? | Por material | Sin cambios |
| 24 | El % de la leyenda, ¿redondeado o truncado? | Redondeado, pero según el comercial 90,57 pudo quedar 91 o 90 | El control acepta las dos cosas |
| 25 | Casos que cierran solo sin el +3 | Probá los dos | Se comparan igual, sin el +3, y se cuentan aparte |
| 26 | Sierra y destaque juntos | La sierra no se usa en vidrio; el destaque mínimo sí, pero en Optima, no al cotizar | Corte Certo: sin sierra ni destaque. Optima: destaque de la regla |
| 27 | Márgenes negativos en Corte Certo | Ni idea, no le des bola | Siguen sin aceptarse |

Respondidas antes: la 4 original (+3 mm en ancho y largo) y la 8 original (la leyenda está en
"Situación de Presupuesto → Observaciones"), el 25/10.
