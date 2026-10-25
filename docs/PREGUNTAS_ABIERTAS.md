# Preguntas abiertas (para Juan)

Contestá en texto libre debajo de cada una ("sí", "no, va con 20", "preguntale a Lucas"…). La
próxima sesión lee las respuestas, las aplica, anota la decisión en `DECISIONES.md` y la mueve a
"Respondidas". Mientras tanto, el programa usa la opción **por defecto**.

## Abiertas

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
| 28 | ¿Cotizamos con la hoja entera o con 3580? | Se sigue cotizando con banda 20 | Sin cambios ("Como Corte Certo hoy" con 3580) |
| 29 | Medidas de hoja que faltan en `Medidas_hojas.xlsx` | Cargalas: si están anotadas es porque se usan (y mandó el stock) | `config/hojas_extra.csv`: 69 medidas del stock y de los casos |
| 30 | Plancha por defecto si no hay 3600 × 2500 | La de 3700 × 2500 era solo para 10 mm; si no, las medidas del vidrio | La de 3700 × 2500 se prefiere solo en 10 mm |
| 31 | "Distancia mínima entre hojas" en Optima | Es el mismo destaque: lo que sobra al final de la hoja o entre dos piezas separadas no puede ser menor (ej. 10 mm: 4 × 875 en 3550 entran; 4 × 880 no) | Sin cambios: es como ya funcionaba el destaque (probado con ese ejemplo) |

Respondidas antes: la 4 original (+3 mm en ancho y largo) y la 8 original (la leyenda está en
"Situación de Presupuesto → Observaciones"), el 25/10.
