# Cruce Metrix ↔ mainque (para la Nota de Pedido del bot)

Documento creado el 2026-10-03. Código: `negocio/cruce_mainque.py`.
Pedido de Juan: que un bot pueda convertir un presupuesto/pedido de Metrix en
una **Nota de Pedido (NP)** de mainque (sistema de facturación, Oracle Forms).
El bot que tipea la NP es `bots/bot_mainque.py` (en master); este módulo le
arma la planilla.

> **Proyecto cerrado el 2026-10-06.** Para usarlo desde otro chat (bot de
> mainque, servicio que publica las planillas) empezar por
> **`docs/MAPA_CRUCE_MAINQUE.md`**: qué hay, dónde, cómo se usa y qué quedó
> abierto. Este documento es el detalle técnico y la historia de cada decisión.

> **Este documento no tiene nombres de clientes a propósito.** Las tablas con
> nombres están en `salida/cruce_mainque/` (fuera de git).

## Regla de oro

**Nunca se inventa un cruce en silencio.** Cada equivalencia lleva *método* y
*confianza*. Para armar una NP solo se usan las confianzas **MANUAL**,
**ALTA**, **REGLA** y **EQUIVALENTE** (`CONFIANZAS_USABLES`; REGLA y
EQUIVALENTE desde el 2026-10-05, confirmadas por Juan); todo lo demás va a una lista de pendientes
y, si una NP tiene un solo pendiente, **no se genera la planilla** (la NP
saldría por un importe distinto al del presupuesto).

| Confianza | Qué significa | ¿La usa el bot? |
|---|---|---|
| `MANUAL` | Lo cargó Juan en `equivalencias_manuales.csv`, o es una regla fija de Juan (herrajes → 8694, perforaciones → 5056, flete → 61, FASON → 5034) | Sí |
| `ALTA` | Clientes: mismo CUIT (un solo cliente con ese CUIT en cada sistema), o mismo código + nombre idéntico (Juan, 2026-10-05). Artículos: **un solo** código de mainque con exactamente la misma composición | Sí |
| `REGLA` | Varios códigos de mainque con la misma composición (o equivalentes); se eligió uno con la regla de desempate (ver abajo). **Confirmada por Juan el 2026-10-05** | Sí |
| `EQUIVALENTE` | Artículos: un solo código que difiere solo en lo que Juan dijo que no importa (2026-10-05): "TEMP" no escrito en mainque, espesor no informado en mainque, cámara negra vs aluminio, intercapa que mainque no informa | Sí |
| `MEDIA` | Clientes: CUIT con nombre muy distinto, o CUIT en dos clientes de Metrix. Artículos: un único candidato *aproximado* (intercapa solo en mainque, vidrio de capa suelto con/sin TEMP) | No |
| `BAJA` | Clientes: solo por nombre. Artículos: varios candidatos aproximados | No |
| `SIN CANDIDATOS` / `SIN CRUCE` | No hay nada en mainque | No |
| `SIN COMPOSICION` | No se pudo interpretar el artículo de Metrix (código sin descripción en `ARTICULO`, laminados compuestos `XLAM`, artículos sin familia) | No |
| `FUERA DE ALCANCE` | DVH con un vidrio FASON (el FASON suelto ya no: va al 5034 desde el 2026-10-05) | No |

## Cómo se usa

```
_work\venv\Scripts\python.exe -m negocio.cruce_mainque                    (todas las tablas)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque lineas 11590       (líneas de la NP)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque lineas 11590 --simular-aprox   (como quedaría aceptando los aproximados)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque planilla 11580     (planilla del bot)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque planilla-pedido 10950  (desde el pedido, vía PEDIDO1.PRESUP_REL)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque cobertura 200      (¿cuántos presupuestos quedan listos?)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque revision 200       (REVISAR_NP.xlsx para Juan)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque aplicar-revision   (carga los NO de Juan)
```

**Revisión sin entrar a Metrix** (pedido de Juan, 2026-10-05):
`revision` genera `salida/cruce_mainque/REVISAR_NP.xlsx` (si Juan ya completó
algo en una versión anterior, **se conserva**). Hojas:
- `LEEME`: instrucciones.
- `productos`: cada cruce Metrix → mainque una sola vez, en palabras, con
  semáforo (amarillo REVISAR, celeste REGLA TUYA, verde SEGURO, rojo FALTA
  CODIGO) y en qué presupuestos con pedido aparece (para chequearlo por OC).
- `con_pedido`: los presupuestos con pedido en Metrix (`PEDIDO1.PRESUP_REL`,
  no anulados; muchos los carga SILVINA aunque entren por la interfaz): cliente,
  pedido, OC (`PEDIDO1.OCOMPRA`), quién lo ingresó, subtotal como en "Detalle
  de Presupuesto 2" (= `TV_TSIVA`), bonificación, total de la NP y cuántos
  amarillos valida. Juan pone **BIEN / MAL** comparando con la NP real de mainque.
- `subtotal_por_articulo`: la "tabla dinámica" que Juan arma sobre el Detalle
  de Presupuesto 2, ya hecha: por presupuesto con pedido y por artículo,
  cantidad, m² y subtotal, un renglón TOTAL (gris) por presupuesto (= su
  subtotal), el cliente de mainque y, al lado del subtotal, el código y la
  descripción del artículo de mainque (para buscar la NP por cliente y OC). Los DVH se agrupan por
  composición (en el informe cada ítem DVH es DVH001, DVH002...); si un mismo
  artículo va a dos códigos (ej. FL4IN en hoja → 28 y cortado → 3333) salen los dos.
- `clientes` y `clientes_sin_cruce` (clientes con pedidos del último año sin
  código de mainque; Juan completa el código).
- `presupuestos`, `lineas` y `detalle_ppto_2` (líneas como el informe 222 de
  Metrix, misma lógica que `salida/vista_informe_presupuestos_2.sql`; ojo:
  algunos herrajes están en DETPRES **y** DETPRES2 y el informe los suma dos
  veces —11488, 11527—; esas filas salen marcadas "REPETIDO" y la NP los cuenta
  una vez).

`aplicar-revision` agrega a `equivalencias_manuales.csv` (nunca borra; la
fila nueva gana): los NO con código correcto (productos y clientes), los
códigos de `clientes_sin_cruce`, y **cada producto amarillo que aparece en un
presupuesto BIEN** (y en ninguno MAL) queda confirmado como MANUAL con su
código actual. Los amarillos de un presupuesto MAL se listan para revisar.

Desde Python: `cliente_mainque(cliente_metrix)`, `armar_lineas_np(numero_presupuesto)`,
`generar_planilla_bot(numero_presupuesto)`.

Lee el SQL Server **solo con SELECT** (vía `negocio.conexion.consultar`, que
bloquea cualquier otra cosa) y los Excel de mainque de
`C:\Users\geronimo.zanon\datos mainque\ACTUALIZADOS\` (exportados y
**recategorizados por Juan y su equipo**, 2026-10-05; `VIEJOS\` se lee solo
para la columna informativa `en_catalogo_VIEJO` de las tablas, nunca para una
NP). Escribe solo en
`salida/cruce_mainque/`:

| Archivo | Qué tiene |
|---|---|
| `cruce_clientes.xlsx` | resumen, equivalencias, pendientes (ordenados por actividad), conflictos |
| `clientes_equivalencias.csv` | los pares (para uso de máquina) |
| `cruce_articulos.xlsx` | resumen, templados, cortado a medida, distribución, vidrios pendientes, DVH, DVH sin código, DVH a confirmar, cómo se interpretó cada DVH del catálogo de mainque |
| `vidrios_equivalencias.csv`, `dvh_equivalencias.csv` | idem en CSV |
| `cobertura.csv` | resultado del comando `cobertura` |
| `planillas_bot/np_presupuesto_<n>.xlsx` | planillas para el bot (`planillas_bot/para_revisar_aprox/`: con algún cruce aproximado, **no** para el bot) |
| `equivalencias_manuales.csv` | **decisiones de Juan** (el módulo lo crea vacío y nunca lo pisa) |

### `equivalencias_manuales.csv` (separado por `;`)

```
tipo;clave_metrix;codigo_mainque;nota
cliente;9999;8888;(ejemplo inventado) confirmado por Juan 2026-10-xx
articulo;FL8IN TEMP;5099;regla A MEDIDA confirmada
articulo;DVH CK6K1 TEMP / CAM12P / LX3+3IN;4777;
articulo;PI12-30;5056;perforaciones como línea aparte
```

`clave_metrix` es la columna del mismo nombre en las tablas (para artículos
también vale la clave canónica de la columna `composicion`; en DVH vale en
cualquier orden de vidrios y con cámara negra o común). Tiene prioridad
sobre cualquier cruce automático.

**Códigos de mainque dados de alta después del export** de los Excel (ej. 9213
y 9273, DVH, 2026-10-05): una fila `codigo_nuevo;<unidad UN/M2>;<código>;<descripción>`
los suma al catálogo, y después se usan con una fila `articulo` normal:

```
codigo_nuevo;UN;9213;DVH COOL LITE KNT 140 6 MM TEMP / 9 / 5 MM INC
articulo;DVH 6 KNT140 TEMP / 9 / 5 FLOAT INC;9213;
```

## 1. Clientes

**Fuentes**: `CLIENTES` de Metrix (`C_CODCLI`, `C_RAZSOC`, `C_CUIT`) y
`CLIENTES TODOS.xlsx` de mainque (CODIGO, DENOMINACION, CUIT con guiones).

**Orden de cruce** (el primero que aplica):
1. **CUIT** normalizado (solo dígitos, 11) que aparece con **un solo código**
   en mainque → `ALTA` ("CUIT + mismo codigo" o "CUIT"). Baja a `MEDIA` si el
   nombre es muy distinto (similitud < 0,50). Se valida además el dígito
   verificador de AFIP (solo como observación).
2. Sin cruce por CUIT, **mismo código en ambos sistemas y nombre parecido**
   (≥ 0,85) → `MEDIA`. Si los dos tienen CUIT válido y distinto → conflicto.
3. **Solo nombre** (≥ 0,90 y 0,05 por encima del segundo) → `BAJA`, va a
   pendientes como *sugerencia*. Nunca se usa solo.

Nombres normalizados: sin acentos, sin puntuación, sin formas societarias
(S.A., S.R.L., SAS...), comparando también con las palabras ordenadas.

**Resultado (2026-10-03)**: 1.246 clientes Metrix, 1.264 mainque.
999 `ALTA` (todos por CUIT), 172 `MEDIA` (168 mismo código + nombre idéntico
sin CUIT en Metrix, y 4 cuyo CUIT está en dos clientes de Metrix), 24 `BAJA`,
75 pendientes (33 con presupuestos en los últimos 12 meses), 12 conflictos.

**2026-10-05 (Juan)**: los 168 "mismo código + nombre idéntico" (similitud
1,0) pasan a `ALTA` → 1.167 ALTA. Y dos clientes muy activos sin CUIT quedan
resueltos a mano en `equivalencias_manuales.csv` (uno con el código propuesto,
otro con el código de mainque de otra razón social que indicó Juan).

**¿Los números de cliente coinciden?** **En parte, y hay un patrón claro**:
de los 1.003 cruces por CUIT, **797 tienen el mismo código** en los dos
sistemas, y los 797 tienen `C_FECHALTA` = **2022-06-06** en Metrix: son los
clientes que se cargaron en Metrix copiando el padrón de mainque cuando se
arrancó. El mayor código Metrix que coincide es el 2413. **Los clientes dados
de alta después de esa carga tienen numeración independiente** en cada
sistema (y algunos clientes viejos también difieren). Conclusión: **no usar
nunca el código de Metrix como código de mainque**; siempre pasar por el cruce.

**Conflictos** (hoja `conflictos`): un CUIT con varios códigos en mainque (4),
un CUIT de Metrix que en mainque tiene varios códigos (4, también quedan en
pendientes), un CUIT repetido entre clientes de Metrix (4).

## 2. Artículos — vidrios sueltos (templados, cortados a medida, distribución)

**Catálogo** (desde 2026-10-05): `datos mainque\ACTUALIZADOS\GRUPO * MODIF.xlsx`,
recategorizado por Juan y su equipo. Grupos: 16 TEMPLADOS, 15 LAMINADO
TEMPLADO, 13 LAMINADO CORTADO A MEDIDA, 14 FLOAT, 4 LAMINADO DISTRIBUCION,
3 ESPEJOS, 11 DVH, 10 HERRAJES. No están los grupos viejos CRISTAL,
ESPECIALES, CATEDRAL, POLICARBONATO ni FLETES: según Juan (2026-10-05) fue un
error de carga, así que **si ACTUALIZADOS no tiene equivalencia se usa el
export VIEJO** (ver "Respaldo en el catálogo VIEJO"). Los export repiten la
cabecera cada ~40 filas (salto de página): se saltean.
(Historia: en el export viejo, "GRUPO TEMPLADOS.xlsx" era en realidad
ARQUITECTURA Y DECORACION y los templados estaban en CRISTAL/ESPECIALES.)

**Tipo de venta** (de `DETPRES2.CLASE`), define el producto Metrix y en qué
grupo de mainque se busca primero (`GRUPOS_PREFERIDOS`):

| Clase Metrix | Venta | Producto Metrix | Grupos mainque | Filtro |
|---|---|---|---|---|
| contiene `TEMP` | TEMPLADO | `FL8IN TEMP` | TEMPLADOS, LAMINADO TEMPLADO | — |
| `DIST`, `LAMILUX` | DISTRIBUCION (hoja entera) | `LX3+3IN DIST` | LAMINADO DISTRIBUCION, ESPEJOS | no "A MEDIDA", no templados |
| el resto (`LAM PMF`, `LAM CORTADO`, `FLOAT PR`...) | CORTE | `LX4+4IN76` | LAMINADO CORTADO A MEDIDA, FLOAT, ESPEJOS | solo "A MEDIDA", no templados |

Verificado el 2026-10-05: las piezas `DIST` son hojas enteras (8,6 m² promedio)
y las `LAMILUX` también (305 de 308 renglones de 12 meses = 9 m², hoja
3600×2500) → se tratan como distribución (**confirmado por Juan**). La parte
PR/PMF/MEC de la clase **no** cambia el código: el precio de la pieza ya
incluye esos procesos.

**Cómo se compara**: un mismo parser (`parsear_vidrio`) lee la descripción de
`ARTICULO` de Metrix y la de mainque y las lleva a una composición canónica:
espesor (`8`, `6+6`), base (`FLOAT`, `OPACID`, `LOWE`, `KNT140`, `ST120`,
`EC_GREY`, `SOLARE_ONCLEAR`, `NEUTROLIGHT`, `ESPEJO`, `ESMERILADO`...),
color, temple (`TEMP` / `TERM` / crudo) e intercapa (`PVB076`, `PVB152`,
`SGP089`, `IPL089`, `EVA`...). Si en el texto queda cualquier palabra que no
sea de float/laminado/color, el vidrio queda **NO RECONOCIDO**.
- **OPTIMIRROR** (familia OPTIMIRROR de Metrix, "OPTIMIRROR PLUS 4 MM INC")
  = **ESPEJO** de mainque, para corte y para distribución (confirmado por Juan).
- **Esmerilado**: lechoso (`LX3+3ESL`), traslúcido (`LX3+3EST`) y a secas
  (`LX3+3ES`) son todos `ESMERILADO` (Juan: "no hace falta diferenciar, por
  ahora").
- Colores: además de gris/bronce/verde/azul, "COLOR" (830 "ESPEJO COLOR 6 MM")
  y "AMBAR" (302 "MARTELE AMBAR") son colores, no incoloro.

Niveles (`comparar_vidrios`):
- `EXACTA`: misma composición en todo. **TERM cuenta como TEMP** (Juan: no
  hacen TERM), así decide la regla (ej. SU6AR TEMP → 4698 "SUPER TINTS ARTIC
  BLUE 6 MM TERM" A MEDIDA y no 1537 M2).
- `EQUIV` (marcado `=` en las tablas) — **aceptado por Juan el 2026-10-05**:
  Metrix TEMP y mainque sin "TEMP" escrito *dentro de un DVH o en los grupos
  TEMPLADOS / LAMINADO TEMPLADO*; espesor no informado en mainque (KNT 6 mm y
  KNT 8 mm / 12 / 3+3 van al código "KNT / 12 / 3+3"); **intercapa que
  mainque no informa** (LX10+10 SGP TEMP → 5435 "10+10 INCOLORO TEMPLADO").
  **Al revés no**: crudo en Metrix contra TEMP en mainque es otro producto
  (salvo vidrios de capa —Cool Lite, Eclipse, Solar-E—, que en Metrix a veces
  no dicen TEMP dentro de un DVH).
- `APROX` (marcado `~`): intercapa solo en mainque (Metrix sin intercapa), o
  un vidrio de capa suelto con/sin TEMP. → `MEDIA` / `BAJA`, **no** van al bot.

Se descartan como candidatos: "NO USAR", mamparas/tapas/cajas/medidas fijas
("800 X 1400"), referencias a una obra puntual ("T230096", "624J"), FASON
(el 5034 "FAZON TEMPLADO" se asigna fijo, ver abajo), "ESMALTADO" (porcelanato).

**Elección** (`elegir_candidato`): se usa el mejor nivel que tenga candidatos
(EXACTA, si no EQUIV, si no APROX). Si hay uno solo → ALTA / EQUIVALENTE /
MEDIA. Si hay varios pero **uno solo en el grupo preferido** para esa venta →
igual (el grupo lo curó Juan). Si no, **regla de desempate** (confirmada por
Juan el 2026-10-05) → REGLA (o BAJA si son aproximados):
0. primero los del grupo preferido para la venta;
1. ESPECIFICACION "A MEDIDA" primero;
2. después unidad **UN** antes que **M2**;
3. después los que no están en el archivo del grupo DVH;
4. desempate final: código más alto (alta más reciente).

Siempre al final: especificación **DESCARTE** (sobrantes, ej. 4313 FLOAT 5 MM).

Para **distribución** (catálogo ACTUALIZADO) 1-4 se reemplazan por: **M2**
primero y después el **código más bajo** (Juan, 2026-10-05: 4+4 INC → 146 y
no 673 "INC. K"; 3+3 G. CLARO → 173; 3+3 INC → 145 y no 424/425 de MEDIDA2
200/160; 6+6 → 196).

**Respaldo en el catálogo VIEJO** (`articulo_mainque`, Juan 2026-10-05):
- Si ACTUALIZADOS no da un cruce usable (ALTA/REGLA/EQUIVALENTE), se busca
  en `VIEJOS\`, con la regla original (sin grupos preferidos, código más alto
  entre iguales). Las tablas lo marcan en la columna `catalogo` = `VIEJO`.
- Si ACTUALIZADOS solo tiene el código **sin intercapa** y el VIEJO tiene uno
  con la **misma intercapa**, gana el viejo (regla 5 de Juan; caso aprobado:
  11375, LX6+6 SGP 0,89 TEMP → **2214** "LAM. 6+6 INC TEMPLADO SENTRYGLASS" M2).
- Un código que **también está en ACTUALIZADOS** se juzga con el grupo en el
  que lo pusieron (ej. 8613 "LAM 4+4 PVB 0.76" es de LAM DISTRIBUCION: no se
  usa para un corte). Del resto, una hoja entera nunca va a un "A MEDIDA".
- Hoja entera con el VIEJO: regla original pero, entre iguales, el código
  **más bajo** (Juan: float 4 mm → **28**, no 415). El martelé ámbar en hoja
  queda fijado a mano en 302 (aprobado en la planilla 11415; su duplicado es 222).
- Así salen, por ejemplo: float en hoja FL3IN → 23, FL4IN → 28, FL5IN → 107,
  FL6IN → 116, FL8IN → 5956 (UN STANDARD), FL10IN → 5734; Pacífico 212,
  Stipolite 213, Martelé 211 (ámbar 302); templado 4 mm → 8453.

**Corte de un producto que solo tiene código de distribución** (Juan,
2026-10-05): si para un corte no hay código "A MEDIDA" (ni en ACTUALIZADOS),
la pieza cortada va con el código de **distribución** (M2, el más bajo). Ej.
LX3+3VC cortado → 178 M2, LX5+5EST cortado → 193 M2. **A futuro** (cuando
haya tiempo) se podrían dar de alta en mainque los "A MEDIDA" que faltan:
laminados de color, Neutro Light, acústico, espejo 6 mm, espejo laminado...
(lista: hoja `cortado_a_medida` de `cruce_articulos.xlsx`, detalle que empieza
con "[corte con codigo de distribucion").

**FASON** (Juan, 2026-10-05; hasta ese día quedaba fuera de alcance): toda
pieza con clase `FAS*` (FAS TEMP, FAS PR, FAS MEC TEMP, FAS) o con "FASON" en
la descripción del artículo (FL8INF "FL 8 MM INC FASON") va al código
**5034 "FAZON TEMPLADO"**, **siempre en M2**, y todas juntas en **una sola
línea**: cantidad = suma de m², precio = suma de subtotales / suma de m². Ej.
11267: FASON de 10, 5, 6 y 8 mm → 5034 × 42,192 m² a 14.902,97. Un DVH con un
vidrio FASON sigue pendiente (no hubo ninguno en los 200 presupuestos).

**Herrajes** (Juan, 2026-10-05): las familias de Metrix `HERRAJES` y
`OBSOLETO` (herrajes viejos que se siguen vendiendo: frenos, zócalos,
tiradores, cerraduras) van **todas juntas en una sola línea** con el código
**8694 "HERRAJES"**: cantidad = **suma de unidades** (4 bisagras + 1 manijón =
5), precio = suma de esas líneas (con la bonificación general aplicada) /
cantidad.

**Correcciones de Juan del 2026-10-06** (cruzó ~400 renglones de
`subtotal_por_articulo` contra las NP reales de mainque):
- **Flete** (familia `DESPACHO`) → código **61** (también vale 551 "FLETE DE
  MERCADERIA"; se toma el más bajo). El 61 no estaba en los export: está como
  `codigo_nuevo` en `equivalencias_manuales.csv`.
- **Perforaciones** (familia `PERF`: PI12-30, PIM10, PIM30, ENTRANTE) →
  código **5056** "PERFORACIONES / ENTRANTES", todas en una línea, cantidad =
  suma de unidades. (A la madrugada del 6/10 se probó sumarlas al subtotal del
  vidrio; Juan lo corrigió al revisar la NP esa mañana: llevan su código.)
- **Hoja entera con el catálogo VIEJO**: M2 y el código **más bajo** (FL8IN →
  126, FL10IN → 130, armado 6 → 219), no los UN STANDARD (5956, 5734).
- DVH 3+3 / 15 / 3+3 → 940; Optimirror 5 mm cortado → 249 (manuales).
- Una decisión manual de DVH vale también con la clave de Metrix invertida.
- 34 cruces amarillos confirmados como MANUAL; quedan 5 de 154.
- **Vidrio crudo cortado** (FLOAT CORTADO / LAM CORTADO): va con el código
  **"A MEDIDA"** (es corte); solo la clase DIST / LAMILUX va con código de hoja.
  Las NP 11263, 11478 y 11237, cargadas en mainque con código de hoja, fueron un
  error humano (Juan, 2026-10-06).

**Resultado (2026-10-05, presupuestos de los últimos 12 meses)**, % del
importe presupuestado que el bot ya puede usar (ALTA/REGLA/EQUIVALENTE):

| Venta | Combinaciones | Usable | Sin candidatos |
|---|---|---|---|
| Templado | 103 | 89,1% | 10,5% |
| Cortado a medida | 83 | 89,4% | 10,6% |
| Distribución (incl. LAMILUX) | 50 | 99,2% | 0,8% |

(FASON va aparte, al 5034.) Lo que queda **sin
candidatos en corte a medida** son productos que en mainque **solo tienen
código de distribución** (M2) y no "A MEDIDA": laminados de color (bronce,
gris oscuro, verde), Neutro Light, acústico 5+3, esmerilado 5+5, espejo 6 mm,
espejo laminado 3+3 → pregunta 1.

## 3. DVH — el "descifrador"

**Metrix**: cada ítem DVH es una fila de `DETPRES` (familia `XDVH`) con
`ART1`/`CLASEART1` (vidrio 1), `ART2` (cámara), `ART3`/`CLASEART3` (vidrio 2);
`V_CANTI` = piezas, `V_PRETO` = total. No tiene filas en `DETPRES2`.
La composición sale de la descripción de `ARTICULO` de cada vidrio + "TEMP"
si la clase lo dice; la cámara del número del código (`CAM09P` → 9).

**mainque**: el texto libre ("D.V.H. LAM. 3+3INC./9/FLOAT 4MM. INC.",
"DVH COOL LITE KNT 140 6 MM TEMP / 12 / 3+3 MM INC") se corta por `/` en
vidrio / cámara / vidrio y cada vidrio pasa por el mismo parser. De los 913
artículos del archivo DVH se interpretan 867; el resto son insumos (butilo,
perfiles), triples, laminados compuestos ("EC.ADV.GREY 6MMTERM+4MM INC TERM")
o descripciones sin "/" entre cámara y vidrio. Ver la hoja
`catalogo_dvh_mainque` para revisar cómo se leyó cada uno.

**Supuestos (a confirmar)**:
- El orden de los vidrios no importa (A/12/B = B/12/A).
- La cámara se compara solo por mm: mainque no distingue P/E. **Negra vs
  aluminio no importa** (Juan, 2026-10-05: en mainque casi nunca se
  especifica): si difiere queda `EQUIV`; si existen las dos variantes, gana
  la que coincide (`EXACTA`).
- Componentes del DVH: TEMP/TERM/sin "TEMP" escrito en mainque y espesor no
  informado (KNT / 12 / 3+3) → `EQUIV` (Juan, 2026-10-05). Varios DVH de
  Metrix pueden ir al mismo código de mainque.
- Lamilux (`LX`) y laminado comprado (`LA`) son el mismo producto para
  mainque ("LAM 3+3 INC").
- "BLINDEX SOLAR GRIS" = ST120, "AZUL" = STB120, "NEUTRO" = ST150,
  "NEUTRO LIGHT" = Neutro Light; "BLINDEX ENERGY" = Low-E.

**Resultado (2026-10-05, 914 composiciones de los últimos 12 meses)**, en %
del importe presupuestado: usable (ALTA 422 / REGLA 115 / EQUIVALENTE 95
composiciones) **82,2** · MEDIA 1,5 · BAJA 0,9 · **sin código en mainque
15,5** (236 composiciones; el 2026-10-03 eran ALTA 54,1 y 274 sin código;
lista completa en la hoja `dvh_sin_codigo`, ordenada por importe). Ejemplos de
las más grandes sin código: FL10GR TEMP / 20 / FL10IN TEMP, CK6K3 (KNT 164)
/ 15 / LX4+4, FL8BR TEMP / 12 negra / LX4+4 Low-E, SU6SU / 12 / LX4+4 Low-E.

## 4. Líneas de la NP

**De dónde sale el precio final** (verificado contra la base el 2026-10-03):

- `PRESUP.TV_TSIVA` = **Σ `DETPRES.V_PRETO`** en el 100% de los presupuestos
  desde el 10500 (1.048 de 1.048). Es el neto **sin IVA** y **antes** de la
  bonificación general.
- Cuando el artículo tiene piezas en `DETPRES2` (vidrio de las familias con
  `FAMILIAS.MEDIDAS='SI'`), `DETPRES.V_PRETO` = **Σ `DETPRES2.V_PRETO`**
  (979 de 979), y `DETPRES2.V_PRETO` = `VIDRIO_PREUNI` × `V_CANTI` (m²).
- **El descuento de "Aplicar Descuentos" ya está adentro del precio de cada
  pieza**: `DETPRES2.VIDRIO_PREUNI` = precio de lista (`PRECIOS`, categoría
  TEMPLADO) × (1 − `DETPRES.DESCUENTO`/100), comprobado en 41 líneas
  recientes con descuentos de −20% a +87,5% (ej. FL10IN con 4,70 → 0,953 de
  la lista; LX5+5IN76 con 8,95 → 0,9105). Por eso se usa `V_PRETO` tal cual.
- Los flags `PRESUP.APLICACLASES` / `APLICADESCUENTOS` **no** sirven para
  saber si el precio es el final (el 11580 tiene `APLICACLASES` vacío y su
  precio ya es el de clase con descuento).
- `PRESUP.TV_TOTAL` = `TV_TSIVA` − `TV_TOTBON` + IVA (`TV_IMIVA18`+`TV_IMIVA9`)
  + otros impuestos.

**Cómo se arma cada línea**:
1. Cada pieza (`DETPRES2`) o ítem DVH / línea sin piezas (`DETPRES`) se
   convierte en un producto Metrix → código mainque (cruce de arriba).
2. Se **agrupa por código de mainque** (varios ítems DVH con la misma
   composición, o piezas de distintas medidas del mismo vidrio, van a una
   sola línea).
3. **Cantidad** = piezas si la unidad del código es **UN**
   (`DETPRES2.V_CANTIALT`, o `DETPRES.V_CANTI` en DVH/herrajes/flete) o m²
   si es **M2** (`DETPRES2.V_CANTI`; en DVH, largo × ancho × piezas). Otra
   unidad (ML, KG...) → pendiente.
4. **Bonificación general** (`PRESUP.TV_BONIF` %, importe en `TV_TOTBON`;
   ~2% de los presupuestos) — regla de Juan, 2026-10-05: el subtotal de
   **cada** producto se multiplica por (1 − `TV_BONIF`/100) antes de dividir.
   Ej. 11560: FL10IN 1.414.508,41 × 0,95 / 13 UN = **103.367,92** → NP
   1.343.782,99 sin IVA, 1.625.977,41 con IVA 21% (= `PRESUP.TV_TOTAL`).
   Si `TV_BONIF` y `TV_TOTBON` no cierran entre sí, queda pendiente.
5. **Precio unitario** = subtotal (ya bonificado) / cantidad, redondeado a 2
   decimales (la diferencia de redondeo queda en `diferencia_redondeo`, son
   centavos: precio × cantidad puede no dar exacto el subtotal).
6. Control: Σ líneas + Σ pendientes debe dar `TV_TSIVA` (si no, aviso). La
   hoja "control" de cada planilla muestra el total esperado de la NP sin IVA
   (`TV_TSIVA − TV_TOTBON`) contra cantidad × precio.

Ejemplo verificado a mano: presupuesto 11590 → 3 grupos de piezas FL10IN
FLOAT PR MEC TEMP (16 + 11 + 4) → una línea de **31 UN** del código propuesto
3553, subtotal = suma exacta de las piezas.

**Planilla del bot**: mismo formato que `leer_pedido()`: filas
"Cliente mainque" / "Presupuesto" / "Obra", una vacía, encabezado
"Producto | Cantidad | Precio unitario | Descripción (solo referencia)".
Verificado leyendo las 27 planillas de muestra con el `leer_pedido()` real del
bot v0.2 (rama `worktree-bot-mainque-v02`, hasta 20 productos).

**Cobertura** (últimos 200 presupuestos ACEPTADOS, comando `cobertura`):

| Fecha | Listos para el bot | Qué cambió |
|---|---|---|
| 2026-10-03 | 30 | solo ALTA/MANUAL, catálogo viejo |
| 2026-10-05 | **108** | catálogo ACTUALIZADOS, regla y equivalencias confirmadas por Juan, LAMILUX = distribución, OPTIMIRROR = espejo |
| 2026-10-05 (tarde) | **184** | respuestas de Juan: catálogo VIEJO de respaldo, intercapa, herrajes/perforaciones/flete → 8694, 168 clientes a ALTA + 2 manuales, bot de hasta 20 productos |

| 2026-10-05 (FASON) | 193 | FASON → 5034 en M2, una línea |
| 2026-10-05 (final) | **199** | corte con código de distribución, clientes 2610/2685, DVH 9213 y 9273 (altas posteriores al export), float 4 mm → 28, 8694 con suma de unidades |

El único que no queda listo es el **11242** (cliente Metrix 2666): **a
propósito**, se facturó a otra razón social y no tiene contraparte en mainque
(Juan, 2026-10-05).

### Validación contra NP reales — PENDIENTE

Falta comparar 2 o 3 NP reales de mainque contra su presupuesto de Metrix
(Juan las va a pasar), y Juan está revisando las planillas de muestra de
`salida/cruce_mainque/planillas_bot/indice_planillas.xlsx`. Las 19 de la
mañana (`planillas_bot_anteriores_2026-10-05_0919/`) las **aprobó Juan**; las
27 actuales (esas 19, que salen idénticas —columna `vs_aprobada_0919`— + 8
nuevas) están pendientes de su revisión. Ya confirmado por
Juan (2026-10-05, caso 11560): precio **sin IVA** y bonificación general
prorrateada en el precio. Falta: código de cada producto, UN vs m², flete.

## Preguntas abiertas

Todas las preguntas de los días 3 a 6 de octubre quedaron respondidas por Juan
(ver las secciones de arriba). Lo que quedó abierto al cerrar el proyecto
(ninguna cosa bloquea) está en **`docs/MAPA_CRUCE_MAINQUE.md`**, sección "Lo
que quedó abierto".
