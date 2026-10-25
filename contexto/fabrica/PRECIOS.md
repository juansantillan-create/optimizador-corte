# Precios — todo en un solo lugar

**Empezado el 2026-10-17** con Juan ("conglomerar todo el tema de precios en
un solo lado bien ordenadito"). Es la entrada para cualquier tema de precios:
qué hay, dónde está y qué falta. Sin nombres de clientes a propósito (regla de
`CLAUDE.md`); `salida/precios/`, `LISTAS PRECIOS A CRUZAR/` y
`FLETES POR CLIENTES.xlsx` no van a git.

## Mapa

| Tema | Estado | Código | Salida |
|---|---|---|---|
| Precios de Metrix por proceso (DIST / CORTE / TEMPLADO / DVH), copia diaria con historial | **hecho** 2026-10-17 | `negocio/precios.py copia` | hoja `precios_metrix`, `datos/precios_metrix.csv`, `historial/` |
| Herrajes | **hecho** | ídem | hoja `herrajes`, `datos/herrajes.csv` |
| FASON templado (lista contra artículos `<código>F`) | **hecho**; los precios mal y los FASON que faltan los corrige Juan en Metrix | `negocio/precios.py fason` | hoja `fason`, `control/control_fason.xlsx` |
| Listas DVH 1/2/3 y listas propias → descuento por artículo y proceso | **hecho** 2026-10-17 | `negocio/listas_dvh.py` | hoja `descuentos_dvh`, `datos/descuentos_dvh.csv` |
| Qué lista usa cada cliente | **hecho** (Lista 3 por descarte a revisar) | ídem | hoja `clientes_lista`, `control/revision_listas_clientes.xlsx` |
| Listas de distribución por cliente | **cerrado** 2026-10-07 (en espera: 2 códigos de mainque y 5 altas) | `negocio/listas_distribucion.py` (`docs/LISTAS_DISTRIBUCION.md`) | hoja `descuentos_distribucion` |
| Fletes por cliente | **hecho**; faltan 8 códigos de cliente | `negocio/precios.py fletes` | hoja `fletes`, `datos/fletes.csv` |

## Cómo correrlo

```
_work\venv\Scripts\python.exe -m negocio.precios consolidar   (todo junto: lo normal)
_work\venv\Scripts\python.exe -m negocio.precios copia
_work\venv\Scripts\python.exe -m negocio.precios fason [--ruta "<otra lista de fason>"]
_work\venv\Scripts\python.exe -m negocio.precios fletes
_work\venv\Scripts\python.exe -m negocio.listas_dvh
```

Solo `SELECT` contra Metrix. El servicio de negocio saca la **copia** sola
(`negocio/servicio.py::_quizas_copia_precios`) la primera vez que termina un
ciclo de datos en el día: si ya existe `historial/precios_metrix_<hoy>.csv`, no
hace nada. Para que el servicio tome este cambio hay que reiniciarlo
(`Reiniciar_Metrix.bat`). **consolidar** se corre a mano cuando cambia una
lista: toma el último `Lista FASON TEMPLADO*.xlsx` y los últimos
`Lista DVH - LISTA n - *.xlsx` de `LISTAS PRECIOS A CRUZAR/`, más
`CLIENTES CON LISTA.xlsx` y `FLETES POR CLIENTES.xlsx`. Si cambió la lista de
distribución, correr antes `python -m negocio.listas_distribucion`.

## `salida/precios/`

| Qué | Para qué |
|---|---|
| `precios.xlsx` | **El consolidado**: una hoja por tema, con `LEEME` |
| `datos/*.csv` | Los mismos datos planos, para un programa (`;`, UTF-8, coma decimal). **Sin datos de ventas a propósito**: Juan, 2026-10-17, "dejemos los datos planos nomás, lo de ventas lo sacamos por otro lado" |
| `control/` | Para revisar, no para el programa: `control_fason.xlsx`, `revision_listas_clientes.xlsx` (qué lista se ve en los presupuestos de cada cliente), `precios_metrix.xlsx` (sin precio real + cambios contra la copia anterior) |
| `historial/` | Una copia de `PRECIOS` por día (formato largo) |
| `config/` | Correcciones a mano, nombran clientes: `clientes_lista_manual.csv` (`cliente_metrix;lista;nota`: pisa la lista de la planilla o suma un cliente nuevo), `listas_propias_clientes.csv` (bloque de lista propia → cliente, ej. un bloque = cliente 549, que no cruza por nombre), `fletes_clientes.csv` (nombre de la planilla de fletes → cliente) |

## Hallazgos (verificados contra la base, 2026-10-17)

### Precios de Metrix
- `PRECIOS` tiene una fila por artículo + categoría (1.119 filas):
  DISTRIBUCION 534 artículos, CORTE 200, TEMPLADO 198, DVH 187. **CORTE y DVH
  valen lo mismo** en todos los vidrios.
- **`ARTICULO.PRECIODOLAR = 1` (164 artículos) = precio en dólares.** Los
  vidrios de capa (Cool Lite, Eclipse, Solar-E, Low-E, Stopsol, Super Tints) y
  62 de los 126 herrajes valen entre 2 y 230 porque son U$S, no porque sean de
  relleno. `negocio/listas_distribucion.py` los trata como "sin precio" (corte
  en 100): ojo si se reusa esa regla.
- Los precios de relleno (1,00 / 1,03 / 1,05 / 1,24 / 1,31) son los menores de
  2 en artículos en pesos.
- Herrajes: solo tienen precio DISTRIBUCION. Fletes: no tienen precio en
  `PRECIOS` (familia `DESPACHO`).
- La tabla **`LISTA`** de Metrix (357 filas con precio, corte, DVH y templado)
  está **desactualizada**: 190 de 356 artículos difieren de `PRECIOS`. No se usa.

### FASON
- El precio está en el artículo `<código>F` ("... FASON"), en categoría
  TEMPLADO. El artículo base tiene en TEMPLADO el precio del vidrio templado
  completo (FL10IN ~77.900 contra FL10INF 17.318).
- **Los FASON con precio mal tienen el precio de una lista anterior**: casi
  todos están 20,6% abajo (= lista ÷ 1,26) o 24,4% abajo (dos aumentos
  atrás).
- Reglas de la lista (`_regla()`), con las respuestas de Juan del 2026-10-17:
  - `N mm inc` → `FLNIN`; `N mm color` → `FLN` + `BR/GR/VE`.
  - **Neutro Light no es color**: 5 y 6 mm van al precio "especial 6", 8 mm al
    "especial 8".
  - "Especial 6" = `Eclipse 6 mm - Solar-E - Low-e 6mm. Cool Lite St y knt
    6mm` (familias ECLIPSE ADVANT, SOLAR-E, LOW-E, COOL LITE ST y KNT de 6
    mm). "Especial 8" = `KNT 155 164 140 8MM`.
  - **Super Tints**: mismo precio en cualquier espesor (a verificar más
    adelante).
  - Los FASON que la lista no cotiza **no se hacen más**: Juan los marca
    obsoletos en Metrix. **Ya no se templa nada de 4 mm**.
  - "12 mm color" no tiene artículo en Metrix: se crea cuando se venda.
- Datos raros en `ARTICULO`: CT4AZF figura con espesor 6 (es de 4 mm), varios
  FASON tienen espesor 0, y el base del Optigreen (SU6MMOG) está en FLOAT
  COLOR mientras su FASON está en SUPER TINTS. Se marcan en `nota`.

### Listas DVH 1/2/3
- **Lista 2 = Lista 1 × 1,05** y **Lista 3 = Lista 2 × 1,05**, en todos los
  precios. La Lista 1 es la base: es la única que trae "% dcto metrix" y la
  hoja de listas propias.
- Ese "% dcto metrix" da **exacto** contra: **CRUDO → precio CORTE**,
  **TEMPLADO → precio TEMPLADO**, **cámaras → precio DISTRIBUCION de
  `CAMnnP`** (polisulfuro). La silicona estructural (`CAMnnE`) va con 7% y el
  offset es `CAM12EOFF`. Por eso el mismo descuento sale en la Lista 2 como
  8,95% y en la Lista 1 como 13,28% (laminado 5+5 templado): es el × 1,05.
- **En un DVH el descuento no va en el `DVH00n`, sino en cada componente**
  (vidrio 1, cámara, vidrio 2): en "Aplicar Descuentos" aparecen esos
  artículos y el % queda en `DETPRES.DESCU1/2/3` (Juan, 2026-10-08 y
  2026-10-17). Por eso la tabla es por artículo + proceso.
- Quedan **fuera** (Juan, 2026-10-17): los vidrios especiales (Low-E, Cool
  Lite: precio por optimización / USD), láminas, pegado estructural y
  opacificado (en USD, o no son componente de un DVH), y todo lo que tiene
  precio 0 (no se hace).
- Sin precio CORTE en Metrix: LX4+4BO, LX5+5BC, LX5+5BO.
- En las listas propias hay 4 renglones que no coinciden con el "% dcto"
  de la planilla. El 5+5 incoloro de dos clientes difiere unos 0,2 a 1,3
  puntos (la planilla se calculó con un precio anterior), y la cámara 20 de
  uno dice 32,24% cuando el precio da 24,72%. Vale el calculado, que es el
  que lleva al precio de la lista.

### Qué lista usa cada cliente (`CLIENTES CON LISTA.xlsx`, 171 razones sociales, todas cruzan con Metrix)
Decisiones de Juan (2026-10-17):
- **Lista 1**: no se le asigna a nadie. La usa el comercial a criterio, cuando
  el presupuesto es grande o hay un acuerdo especial.
- **Sin lista** (73): **Lista 3 por descarte**, marcados `POR DESCARTE
  (revisar)`.
- **Templado ingeniería** (14): no es una lista. Es el **precio de Metrix
  sin descuento** (templados que no van en un DVH, ej. puertas); la marca
  solo separa a esos clientes del resto.
- **Lista propia** (17): **13 tienen su propia hoja en la lista de
  distribución** (de ahí "propia"). Tres tienen además su propia lista DVH en
  la segunda hoja de la Lista 1; los demás no tienen lista DVH propia.
- **Lista especial** (1): no la tenemos.

Revisión contra los presupuestos desde el 08-09-26
(`control/revision_listas_clientes.xlsx`):
- De los clientes de Lista 2 con presupuestos, 8 siguen la Lista 2, 8 la
  Lista 1 y 9 mezclan. Cuadra con que la Lista 1 se da a criterio.
- Los de templado ingeniería van casi todos sin descuento.
- Dos de los tres clientes con lista DVH propia usan exactamente su hoja. El
  tercero tiene sobre todo otros descuentos.

### Fletes (`FLETES POR CLIENTES.xlsx`, vigencia 08-07-26)
- Importe = km × 2 (ida y vuelta) × precio por km. El precio por km es 1.500
  con camión **propio** y 2.000 con **semi**.
- Algunos importes están a mano (Mendoza, un destino lejano) y hay 2 destinos
  sin cliente: se respetan tal cual, con nota.
- 8 nombres abreviados no cruzan con un cliente de Metrix: se completan en
  `config/fletes_clientes.csv`.

## Lo que falta para cerrar

La checklist imprimible (con nombres, fuera de git) es
`salida/precios/control/CHECKLIST_CIERRE_PRECIOS.html`: 27 puntos más un anexo con los
73 clientes en Lista 3 por descarte. La completan a mano en la oficina y Juan pasa la
transcripción en texto libre; la sesión que la reciba carga cada respuesta en
`salida/precios/config/` (o en el lugar que corresponda) y corre `consolidar`.
Resumen:
- Fletes: 8 códigos de cliente, confirmar 2 deducidos, 4 importes a mano, 2 destinos sin
  cliente, vigencia y precio por km, qué pasa con los clientes que no están en la planilla.
- FASON (Juan, en Metrix): 26 precios a corregir, 12 artículos a crear, 7 a marcar
  obsoletos, verificar Super Tints.
- Listas DVH: qué usan los 14 "Lista propia" sin lista DVH, conseguir la Lista especial,
  vigencia de la tercera lista propia, 4 diferencias de la hoja de propias, 3 laminados sin
  precio CORTE, 8 clientes de Lista 2 que reciben Lista 1 (¿acuerdo fijo?), revisar los 73
  por descarte.
- Distribución: lo que estaba en espera (2 códigos de mainque, 5 altas).
- Metrix: esmerilado genérico LX?+?ES sin precio.
- Sistema: reiniciar el servicio, commit.

Las respuestas sobre la lista de cada cliente van en `config/clientes_lista_manual.csv`
(`cliente_metrix;lista;nota`): pisan a la planilla y sirven también para sumar un cliente
nuevo que todavía no está en `CLIENTES CON LISTA.xlsx` (origen "a mano").

### Idea pendiente (para el mapa del orquestador)
Cómo se suman a mano los clientes y fletes nuevos, y de dónde salen. Anotado también en
`docs/VISION_ORQUESTADOR.md` (preguntas abiertas).

## Historia

| Fecha | Qué |
|---|---|
| 2026-10-17 | `negocio/precios.py` (copia diaria con historial, control FASON, fletes, consolidado) y `negocio/listas_dvh.py` (listas DVH 1/2/3 y propias, clientes). Respuestas de Juan: la lista de distribución 08-09-26 sigue vigente; Lista 1 a criterio; sin lista → Lista 3 por descarte; templado ingeniería = Metrix sin descuento; reglas del FASON (Neutro Light especial, Super Tints cualquier espesor, lo que no está en la lista no se hace, nada de 4 mm templado). |
