# Listas de precios de distribución → descuento en Metrix

**Iniciado el 2026-10-06** con Juan, como primer paso ("preparar el terreno")
para una **app de distribución**. Este archivo explica qué hace
`negocio/listas_distribucion.py`, dónde deja todo, cómo se mantiene y qué
quedó abierto.

> Sin nombres de clientes a propósito (regla de `CLAUDE.md`). Los nombres
> están en los Excel/CSV de `salida/listas_distribucion/`, que no van a git.

---

## En una línea

Para cada cliente con lista de distribución: cada vidrio de su lista → su
**artículo de Metrix** y su **código de mainque** (hoja entera), el **precio
que paga** (por m² + IVA) y el **descuento a cargar en Metrix** sobre el
precio `DISTRIBUCION` de Metrix para llegar a ese precio.

Formato pedido por Juan: *cliente / código Metrix / código mainque / vidrio /
precio del cliente / descuento a aplicar en Metrix*.

## Cómo correrlo

```
_work\venv\Scripts\python.exe -m negocio.listas_distribucion
_work\venv\Scripts\python.exe -m negocio.listas_distribucion --ruta "<otro Excel de listas>"
```

Solo hace `SELECT` contra Metrix. Deja:

| Archivo | Qué es |
|---|---|
| `salida/listas_distribucion/cruce_listas_distribucion.xlsx` | Todo, con hoja `LEEME` |
| `salida/listas_distribucion/descuentos_distribucion.csv` | Lo mínimo para la app (`;`, UTF-8): una fila por cliente + artículo + variante con descuento calculado |
| `salida/listas_distribucion/DUDAS_LISTAS_DISTRIBUCION.xlsx` | **Lo que falta definir, para Juan**: una fila por duda, pocas columnas, respuesta en amarillo (hoja `COMO RESPONDER`) |

Cuando Juan completa la planilla de dudas:

```
_work\venv\Scripts\python.exe -m negocio.listas_distribucion aplicar-dudas
```

Pasa las respuestas a `config/*.csv` (con backup `config_backup_<fecha>` antes
de tocar nada), regenera todo y lista lo que no entendió. Al regenerar, las
respuestas ya escritas que todavía no se aplicaron se conservan.

Juan contesta en **texto libre** y está bien ("CODIGO METRIX: 2528", "NO
VENDEMOS MAS!", "CAMBIADO DENTRO DE METRIX!", "LISTA DE <otra lista>", "es otra
razón social de <cliente>", "NO COMPRA MAS", "SIN CLIENTE METRIX"):
`_interpretar()` lo traduce y `_buscar_lista()` encuentra la lista por
palabras parecidas. La planilla tiene dos pestañas: **DUDAS** y **PENDIENTES DE
ALTA** (clientes con lista que todavía no existen en Metrix/mainque: cuando se
den de alta, Juan escribe el código ahí y aplica; es la "guía" que pidió).

Hojas del Excel: `LEEME`, `resumen` (una fila por cliente: rango de
descuentos, m² comprados), `cruce` (todo, coloreado por estado), `app`,
`clientes`, `pendientes` (vidrios sin artículo), `fuera_de_lista` (lo que
compran como DIST y no está en su lista), `clientes_dist_sin_lista`,
`notas_hojas` (fletes, condiciones y dudas de cada hoja).

## Fuentes

| Qué | Dónde |
|---|---|
| Listas de los clientes | `LISTAS PRECIOS A CRUZAR/Lista de precios SEPTIEMBRE 08-09-26.xlsx` (una hoja por cliente o grupo; fuera de git) |
| Precio directo de Metrix | `PRECIOS` con `CATEGORI = 'DISTRIBUCION'` (sin clases ni procesos) |
| Artículos | `ARTICULO` |
| Qué compra cada cliente | `PEDIDO2.GRUPO = 'DIST'`, últimos 12 meses, pedidos no anulados |
| Cliente y artículo de mainque | `negocio/cruce_mainque.py` (`cliente_mainque`, `articulo_mainque` con clase `DIST`) |
| Configuración (nombra clientes) | `salida/listas_distribucion/config/*.csv` (fuera de git, ver abajo) |

**No se usaron** (todavía): las 3 listas DVH (`Lista DVH - LISTA 1/2/3`) y
`CLIENTES CON LISTA.xlsx` (razón social → Lista 1/2/3/Propia). Son de DVH, o
sea con proceso; ya traen una columna "% dcto metrix". Quedan para un paso
siguiente.

## Cómo funciona

1. **Leer las hojas** con un formato declarado a mano por hoja
   (`config/hojas.csv`): columna de la etiqueta del vidrio y columnas de precio
   con su **variante**. Las filas sin precio ("Float Inc.", "Laminado Color",
   "Especiales", "Templados"…) abren una **sección**. Fletes, cuentas y notas
   quedan fuera a propósito.
2. **Vidrio de la lista → artículo(s) de Metrix** (`articulos_metrix`), con
   reglas legibles. Si la lista agrupa productos que en Metrix son artículos
   distintos, sale **una fila por artículo**:
   - "3+3 mm Claro" → gris claro **y** bronce claro (`LX3+3GC`, `LX3+3BC`).
   - "Austral/Stipolite/Sycamore" → `CA4AU`, `CA4ST`, `CA4SY`.
   - "Lechoso/Traslúcido" → `LX?+?ESL` y `LX?+?EST`.
   - "Lamilux 4+4 ST Gris/Neu/Ver" → `ST120`, `ST150`, `ST467`.
   - Laminado incoloro de distribución = **Lamilux** (`LX…`), no `LA…`.
   - Lo que no se reconoce va a `pendientes`: **nunca se adivina**.
3. **Código de mainque de hoja entera**: misma regla que la NP (grupo LAM
   DISTRIBUCIÓN o catálogo viejo, M2, **el código más bajo**; Juan,
   2026-10-06).
4. **Descuento** = `(1 − precio_cliente / precio_dist_metrix) × 100`,
   redondeado a 2 decimales. `precio_metrix_con_descuento` es el control de lo
   que daría Metrix con ese descuento.
5. **Control con lo cargado de verdad** (`descuento_ultimo_ppto_pct`,
   `coincide_con_ppto`): el `DETPRES.DESCUENTO` del último presupuesto
   vinculado (`PEDIDO1.PRESUP_REL`) a un pedido donde ese artículo va como
   `GRUPO = 'DIST'`. Coincide si alguna variante de la lista da ese descuento
   (±0,5 puntos).

**Cómo se cargan los pedidos de distribución** (Juan, 2026-10-07): las clases
existen (float: hoja entera `DIST`, cortada `FLOAT CORTADO`; laminado: hoja
entera `LAMILUX`, cortada `LAM CORTADO`), pero **en la práctica no se usan**:
el mismo artículo tendría dos procesos y dos precios por m². Los pedidos se
cargan por la interfaz al presupuesto de Metrix **sin clase**, y después se
aplica un descuento/recargo ("aplicar descuentos") hasta llegar al precio del
cliente. Por eso el descuento contra `PRECIOS.DISTRIBUCION` es el correcto,
también para las hojas cortadas. Verificado: en un cliente, float 5 y 6 mm,
Lamilux 3+3 y 5+5 y espejo 3 mm dan exactamente el descuento de su
presupuesto; en las listas propias coinciden 124 de ~140 combinaciones
cliente + artículo, y las que no son presupuestos de la lista anterior.

> Ojo: los presupuestos de vidrio **cortado** también van sin clase, pero con
> el descuento de las listas DVH, calculado contra el precio `CORTE` (float 4
> mm 23,94%, 3+3 21,88%…). Por eso el control solo mira presupuestos
> vinculados a pedidos DIST.

### Estados

| Estado | Significa |
|---|---|
| `OK` | descuento entre 0% y 60% |
| `OK (USD)` | lista en dólares en la hoja y en Metrix |
| `RECARGO` | el cliente paga **más** que la lista DIST de Metrix (descuento negativo) |
| `REVISAR` | descuento > 60% o moneda distinta |
| `NO SE COMERCIALIZA` | artículo legacy o marcado "no se vende" (no va a la app) |
| `EXCLUIDO` | templados y laminados Blindex de VASA: no entran (Juan, 2026-10-07) |
| `SIN PRECIO DIST` | el artículo no tiene precio DIST real en Metrix (vacío o "de relleno" 1,00 / 1,04 / 1,24…) |
| `SIN ARTICULO METRIX` | el vidrio no tiene artículo (templados, Blindex, acanalado) |

### Variantes (hojas con cortes)

Juan pidió especificar el descuento de las hojas con uno o dos cortes. Lo que
las hojas dicen explícitamente sale como **variante**, con su propio
descuento contra el mismo precio DIST:

- **media hoja 1800×2500 (1 corte)** contra hoja entera 3600×2500 (una hoja);
- **hoja cortada en 3 bandas** (2 cortes; una sub-lista);
- **hoja con cortes (+10%)** y **(+15%)**: derivadas de la nota de la hoja
  (`config/recargos_cortes.csv`);
- además: directo VASA / retiro Cristalux, paquete / hoja, Blindex, medidas de hoja.

## Configuración (fuera de git)

`salida/listas_distribucion/config/` (separador `;`, se edita con Excel; el
módulo nunca la pisa). Si se borra, el módulo avisa qué archivo falta.
**Hacer backup antes de tocarla**: es el relevamiento hecho a mano.

| Archivo | Columnas | Para qué |
|---|---|---|
| `hojas.csv` | `hoja;lista;col_etiqueta;precios;fila_desde;fila_hasta;seccion_inicial;col_variante` | formato de cada hoja. `precios` = `B=hoja entera \| C=media hoja…`. `lista` ≠ `hoja` = sub-lista con cliente propio |
| `hojas_ignoradas.csv` | `hoja;motivo` | plantillas y listas viejas |
| `clientes.csv` | `lista;nombre_en_lista;cliente_metrix;observacion` | cliente(s) de Metrix de cada lista (vacío = no encontrado) |
| `recargos_cortes.csv` | `lista;factor;variante;nota` | recargo por cortes de una nota de la hoja |
| `notas_hojas.csv` | `hoja;nota` | fletes, condiciones, dudas |
| `articulos_no_comercializados.csv` | `articulo;nota` | no se venden más (los 6 legacy, 2026-10-07) |
| `precios_manuales.csv` | `articulo;precio_dist;nota` | precio DIST para artículos que en Metrix no lo tienen (lo ideal es cargarlo también en Metrix) |
| `articulos_manuales.csv` | `vidrio_en_lista;articulos;nota` | vidrio que las reglas no traducen → códigos, o `NO SE VENDE` |
| `descuentos_manuales.csv` | `lista;cliente_metrix;articulo;descuento_pct;nota` | descuento que vale aunque la hoja diga otro (`descuento_pct` vacío = vale el de la hoja) |

`clientes.csv` tiene además una columna opcional `cliente_mainque` (código de
mainque dado a mano) y tres listas especiales: `Lista Dist` (la general, 0%),
`Segun presupuestos` (el cliente no tiene hoja: su lista son los descuentos de
sus últimos pedidos DIST) e `Inactivos` (no compra más: sin filas). Un cliente
con otra razón social usa la lista del cliente principal (fila aparte en esa
lista, con su propio código). Las marcas `[Juan: ...]` en `observacion` las deja
`aplicar-dudas` para no volver a preguntar.

| Situación | Qué hacer |
|---|---|
| Llega la lista del mes que viene con el mismo formato | correr con `--ruta`; revisar `pendientes` y `notas_hojas` (hoja nueva = "sin configurar") |
| Se movieron filas o columnas en una hoja | corregir esa hoja en `hojas.csv` |
| Se confirmó un cliente | completar `cliente_metrix` en `clientes.csv` (el de mainque sale solo por CUIT; si no, cargarlo en `salida/cruce_mainque/equivalencias_manuales.csv`) |

## Hallazgos (verificados contra la base, 2026-10-06)

- **La hoja "Lista Dist" del Excel ES la lista DISTRIBUCIÓN de Metrix**: ~75
  artículos coinciden al centavo (0%). Sirve de control: donde no coincide, se
  avisa en todas las filas de ese artículo (6 artículos: Stopsol 4 y 6 mm,
  Pacific 6 mm, Pyroshield 6 mm, Coverglass Blanco Puro 5 mm y Extra Blanco 3+3).
- **Metrix no tiene descuentos por cliente en uso**: `DESCFAM` tiene 4 filas
  de prueba, `CLIENTES.C_BONIFICA` = 0 en todos. El descuento va renglón por
  renglón (`DETPRES.DESCUENTO`).
- **Los pedidos de distribución no tienen precio en Metrix**
  (`PEDIDO2.PRECIO = 0` en los ~485 pedidos `GRUPO = 'DIST'` de 12 meses): el
  precio de distribución hoy está solo en mainque. Por eso no hay "descuento
  actual" de Metrix contra el cual validar; de los pedidos solo se toma qué y
  cuánto compra cada cliente.
- **Muchos artículos tienen precio de relleno en `PRECIOS`** (1,00 / 1,04 /
  1,19 / 1,24 / 1,31): se tratan como "sin precio".
- **Esmerilado**: en los pedidos se carga `LX3+3ES` / `LX4+4ES` (precio de
  relleno), pero las listas lo cotizan como lechoso/traslúcido (`ESL`/`EST`,
  con precio). Lo marca la hoja `fuera_de_lista`.

## Estado (corrida del 2026-10-07, con las respuestas de Juan)

- 35 listas con precios (más 3 hojas de clientes sin precios cargados).
- 2.483 filas: 2.077 OK, 2 OK (USD), 212 RECARGO, 33 sin precio DIST, 1 sin
  artículo, 125 no se comercializa, 33 excluidas.
- 13 clientes que compran DIST sin hoja propia quedaron en la `Lista Dist`
  general (respuesta 7), pero 5 de ellos se cargan con descuentos grandes: van
  como duda.
- **34 dudas** en `DUDAS_LISTAS_DISTRIBUCION.xlsx`: 8 clientes sin código, 2 a
  confirmar, 1 sin código de mainque, 3 hojas sin precios, 5 "¿qué lista
  usa?", 2 descuentos de pedidos recientes distintos a la hoja, 12 artículos
  sin precio DIST y 1 vidrio sin artículo.

## Respuestas de Juan (2026-10-07)

1. **Clases**: ver "Cómo se cargan los pedidos de distribución" arriba (sin
   clase + descuento/recargo). El descuento contra DIST queda como está, también
   para las hojas con cortes.
2. **Recargos**: están bien.
3. **Los 6 artículos donde la Lista Dist no coincidía** (Stopsol 4 y 6, Pacific
   6, Pyroshield 6, Coverglass Blanco Puro 5 y Extra Blanco 3+3): legacy, no se
   comercializan más → `articulos_no_comercializados.csv`.
4. **Esmerilado**: hoy hay dos, lechoso (`ESL`) y traslúcido (`EST`); las
   planillas no lo distinguían. "Lechoso/Traslúcido" o "esm" → los dos códigos,
   al mismo precio. El genérico `LX?+?ES` de los pedidos viejos no tiene precio.
5. y 6. **Precios y clientes faltantes**: pidió una planilla simple para
   completar → `DUDAS_LISTAS_DISTRIBUCION.xlsx`.
7. **Clientes sin hoja**: usan la lista de distribución (general).
8. Notas ambiguas: está bien no aplicarlas por ahora.
9. **Blindex y templados**: NO entran.
10. **Listas DVH 1/2/3**: son el paso siguiente.

## Historia

| Fecha | Qué |
|---|---|
| 2026-10-06 | Primera versión: 35 listas, mapeo de vidrios validado con la Lista Dist (0%), clientes relevados a mano, configuración fuera de git. |
| 2026-10-07 (noche) | Juan: las 2 dudas (mainque de 2690 y 2658) y los 5 pendientes de alta quedan en espera **a propósito**: no se dan de alta en mainque hasta que se les facture. El mainque forzado 3346 es correcto (se le presupuesta a un cliente y se le factura a otro, como 2442 → 2573). Rama pasada a master. |
| 2026-10-07 (tarde) | Juan completó la planilla: 23 respuestas aplicadas (clientes encontrados, 2 razones sociales que usan la lista de otro cliente, una hoja que era un cliente ya cargado, 2 inactivos, 5 sin alta, precios cargados directamente en Metrix, Neutro Light float no se vende). Lector de texto libre y pestaña PENDIENTES DE ALTA. Quedan 2 dudas (códigos de mainque) y 5 pendientes de alta. |
| 2026-10-07 | Respuestas de Juan; control contra el descuento real de los presupuestos de pedidos DIST; planilla de dudas + `aplicar-dudas`; lista "Segun presupuestos"; descuentos, precios y artículos manuales. |
