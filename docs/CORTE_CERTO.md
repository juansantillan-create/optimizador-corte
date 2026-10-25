# Corte Certo v3.9K: las pantallas que hay que replicar

Corte Certo es un programa brasileño de optimización de corte. La oficina lo usa en castellano;
algunas palabras quedaron a medio traducir ("Sem", "Pese específico"). Las 4 capturas son
reales, del 20/10/2026, y están en `docs/img/`. **Miralas** antes de diseñar las pantallas: los
nombres, el orden y los colores tienen que ser reconocibles para la gente de la oficina.

Lo que no se ve en las capturas está marcado ❓ y tiene su pregunta en
`docs/PREGUNTAS_ABIERTAS.md`.

---

## 1. Informe de cálculo — `img/corte_certo_1_informe_calculo.png`

Ventana "Visualizar e imprimir montajes". Arriba a la izquierda dice "Corte Certo v.3.9K"; arriba
a la derecha, **Informe de cálculo** (azul, subrayado) con la fecha y la hora (`20/10/26
23:20:19`).

**Proyectos calculados** (puede haber más de uno calculado junto):

| Código | Descripción | Piezas | Código del material |
|---|---|---|---|
| 413 | PRJ 413 | 252 | 5 |

**Lista de Materiales:**

| Código | Descripción | Piezas | (m2) | Layouts | Planchas | (m2) | Aprov. |
|---|---|---|---|---|---|---|---|
| 5 | 5 mm Incoloro | 252 | 564.583068 | 13 | 82 | 733.9 | 76.93% |

Debajo de cada material, **Planchas / offcuts usados:**

| Cantidad | Ancho | Largo | Tipo |
|---|---|---|---|
| 82 | 3580.0 | 2500.0 | Plancha |

Al pie:
- `Perímetro - Piezas: 1630.22 m`
- `Cálculo especial de perímetro: 0.00 m` ❓ (no sabemos qué calcula)

Abajo, una barra negra **"Elija el material para visualizar:"** con una lista
(Código | Descripción | Color) para pasar a los montajes de ese material. La columna Color
está vacía en la captura.

**Las cuentas cierran:**
- 82 × 3,58 × 2,5 = **733,9 m²**: las planchas se cuentan con la medida **útil** (3580, ya sin
  el corte banda).
- 564,583068 ÷ 733,9 = **76,93 %**.
- Los m² de piezas tienen 6 decimales porque son mm² ÷ 10⁶ exactos.
- En promedio, cada pieza mide 2,24 m² y entran ~3 por plancha (252 ÷ 82 = 3,07): son piezas
  grandes.

Detalles de formato:
- Punto decimal.
- Medidas de plancha con un decimal (`3580.0`).
- El material se identifica con un código propio de Corte Certo (`5`). Nosotros usamos el código
  de Metrix (`FL5IN`).

## 2. Visualizar e imprimir montajes — `img/corte_certo_2_montajes.png`

Encabezado: `Proyecto : 413 PRJ 413   252   Material : (5) 5 mm Incoloro`.

**Datos generales** (recuadros negros, números en color):

| Etiqueta | Valor | Color del número |
|---|---|---|
| Cdad. de montajes: | 13 | celeste |
| Total de chapas: | 82 | celeste |
| Aprovechamiento: | 76.93 % | verde |
| Pérdida: | 23.07 % | rojo |

Al lado, una lamparita: *"Posicione el cursor en un esquema para detalles, y pulsa el botón para
obtener más información, revisar, imprimir, etc."*

**Miniaturas**:
- 13 montajes en una grilla de 6 por fila.
- Cada uno es una plancha acostada (lado largo horizontal) con contorno negro.
- Los que se repiten en varias planchas se dibujan **apilados**, como una pila de chapas: varios
  contornos corridos hacia abajo y a la derecha. Más contornos = más repeticiones. En la captura,
  los montajes 5, 6, 10 y 12 son pilas grandes, y el 3 y el 4, chicas.
- Casi todos tienen 3 piezas por plancha, en tiras verticales del alto de la plancha o un poco
  menos, con el sobrante en una tira a la derecha y/o arriba.
- **Colores**:
  - piezas en **bordó**, **verde** y **oliva**;
  - sobrante en **amarillo**;
  - ❓ no sabemos qué distingue bordó, verde y oliva. En un mismo montaje hay piezas que se ven
    del mismo tamaño y tienen distinto color, así que no es "un color por medida". Medido el
    25/10: tampoco es "verde = girada, oliva = retazo" (montaje 8: una oliva y dos verdes de la
    misma medida y orientación). Lo que cierra es "un color por renglón del proyecto, rotando
    entre 3", sin confirmar. Son los colores 2, 3 y 4 de la paleta de Windows: `(128,0,0)`,
    `(0,128,0)`, `(128,128,0)`; el amarillo es `(255,255,0)`. Ver pregunta 5.

**Lo que agregamos nosotros**:
- "×N" visible en cada pila;
- clic en una miniatura → detalle con medidas, cortes numerados y lista de piezas;
- imprimir.

## 3. Cálculo en proceso — `img/corte_certo_3_calculo_en_proceso.png`

Fondo gris, título *"Cálculo en proceso. Por favor espere..."*.

| Etiqueta | Valor | Estilo |
|---|---|---|
| Material : | 2004 | amarillo sobre negro |
| Tiempo de cálculo : | 00:00:08 | verde sobre negro |
| Tiempo estimado : | 00:00:10 | verde sobre negro |
| Tiempo restante estimado : | 00:00:02 | celeste sobre negro |

A la derecha, una **torta** verde con una porción verde azulada y el número en el medio
(`80%`). Abajo, `Montaje 004`: va contando los montajes que arma.

Para nosotros:
- misma información: material en curso, tiempos, % y montaje N;
- botón **Cancelar**, que devuelve la mejor solución encontrada hasta ese momento.

## 4. Material → Propiedades físicas — `img/corte_certo_4_propiedades_fisicas.png`

Pestañas: **Descripción** | **Propiedades físicas** (la de la captura) | **Propiedades
comerciales**. ❓ No hay captura de Descripción ni de Comerciales: proponé campos razonables
(código, descripción, color, espesor; precio por m² de plancha y de retazo) marcados como
provisorios.

Barra negra arriba: "Los valores aquí definieron…" (cortado; dice algo como "los valores
definidos acá valen para este material").

| Campo de Corte Certo | En la captura | Qué es | Nombre sugerido |
|---|---|---|---|
| Ancho de la sierra (mm) | 0 | Lo que se pierde en cada corte (separación entre piezas) | `separacion_piezas_mm` |
| Ancho mínimo de destaque (mm) | 0 | Tira más angosta que se puede separar | `destaque_min_mm` |
| Genera retazo: SI / NO | SI | Si los sobrantes grandes cuentan como retazo | `genera_retazo` |
| · Ancho mínimo para retazo (mm) | 0 | | `retazo_ancho_min_mm` |
| · Largo mínimo para retazo (mm) | 0 | | `retazo_largo_min_mm` |
| · [ ] Utilice el área mínima (m2) | sin tildar, 0 | | `retazo_area_min_m2` |
| Rotación permitida: SI / NO | SI (con *) | Si la pieza se puede girar 90° | `rotacion` |
| Textura: Horizontal / Vertical / Sem | Sem (= sin) | Dirección de la veta; con veta no se gira | `textura` |
| Agrega una constante en las dimensiones de los pedazos: Ancho / Largo (mm) | 0 / 0 | Se suma a cada pieza ("en la anchura y en la altura tecleada") | `constante_ancho_mm`, `constante_largo_mm` |
| Espesor (mm) | 0 | | `espesor_mm` |
| Pese específico (Kg/m2) | 0 | Para el peso | `peso_kg_m2` |
| Margen de seguridad para la plancha (4 valores, −500 … 500 mm) | 0, 0, 0, 0 | Lo que no se usa en cada borde | `margen_arriba_mm`… |
| Máximo tamaño cortado (usado en guillotinas): Libre / Limitado (10 … 10000 mm) | Libre, 10000 (con *) | Largo máximo de un corte | `corte_max_mm` |

Notas:
- Al pie dice: *"Observación: las opciones que normalmente ofrecen los resultados más buenos son
  marcados en rojo, con el símbolo \*"*. Están marcados con \* "Rotación: SI" y "Máximo tamaño
  cortado: Libre".
- Debajo de varios campos hay un "(0)" rojo chiquito. ❓ Parece el valor por defecto o el valor
  general; no cambia nada para nosotros.
- **Todo en 0** confirma lo que cree Juan: en Corte Certo la única regla de corte es la plancha ya
  achicada (3580 × 2500). No hay separación entre piezas ni márgenes.

Agregados de Cristalux (no están en Corte Certo):
- **corte banda**: se resta del lado largo de la plancha (de `Medidas_hojas.xlsx`);
- **preset** ("Como Corte Certo hoy" / "Reglas de corte (Lucas)").

Ver `docs/BRIEF_OPTIMIZADOR.md` §5.
