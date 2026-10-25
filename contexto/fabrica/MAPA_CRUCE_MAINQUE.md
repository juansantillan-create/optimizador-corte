# Mapa del cruce Metrix ↔ mainque (Notas de Pedido) — proyecto cerrado

**Cerrado el 2026-10-06** con Juan. Este archivo es el punto de entrada para
cualquier chat que use lo que se construyó: **qué hay, dónde está, cómo se usa
y qué quedó abierto**. El detalle técnico y la historia de cada decisión están
en `docs/CRUCE_MAINQUE.md`.

> Sin nombres de clientes a propósito (regla de `CLAUDE.md`). Los nombres
> están en los Excel de `salida/cruce_mainque/`, que no van a git.

---

## En una línea

`negocio/cruce_mainque.py` toma un **presupuesto de Metrix** (SQL Server, solo
lectura) y arma la **planilla Excel** que el bot `bots/bot_mainque.py` carga
como **Nota de Pedido (NP) en mainque**: cliente de mainque, código de mainque
de cada producto, cantidad y precio unitario sin IVA (con la bonificación
general ya aplicada). Si algo no tiene cruce seguro, **no genera la planilla**
(el caso va a un humano).

## Estado final

- **199 de los últimos 200 presupuestos aceptados** salen listos para el bot.
  El que falta (11242, cliente Metrix 2666) queda afuera **a propósito**: se
  factura a otra razón social.
  **Actualización 2026-10-06 (bot v0.3, productos por m²)**: las planillas
  llevan ahora Unidad / Medida 2 / Medida 3 / Hojas para las líneas M2 (ver
  `docs/PLAN_NP_A_PEDIDO.md`). Las líneas de **corte o templado con código en
  m²** quedaban pendientes `SIN MEDIDAS` (192 de 200 listos).
  **Resuelto 2026-10-07**: llevan 1 y 1 como el fasón (solo la distribución
  lleva el tamaño de la hoja) → **198 de 200** listos; los 2 restantes son del
  cliente 2666 (otra razón social, afuera a propósito).
- **Validado contra la realidad**: Juan cruzó ~290 renglones de 136
  presupuestos contra las NP reales de mainque (2026-10-06). Todo lo que estaba
  mal se corrigió en las reglas. Las únicas diferencias que quedaron (vidrio
  crudo cortado cargado como hoja en 11263, 11478 y 11237) fueron **errores de
  carga en mainque**: el cruce está bien (Juan, 2026-10-06).
- **28 planillas de muestra** pasan el lector real del bot (`leer_pedido()` del
  bot v0.2, hasta 20 productos). 19 de ellas las aprobó Juan una por una.

---

## 🤖 Para el chat que sigue el BOT de mainque

**Qué recibe el bot**: un `.xlsx` por presupuesto, hoja **`pedido`** (la única
que tiene que leer), con este formato exacto (el de `leer_pedido()`):

| Fila | A | B | C | D |
|---|---|---|---|---|
| 1 | `Cliente mainque` | código de cliente de mainque | | |
| 2 | `Presupuesto` | número de presupuesto de Metrix | | |
| 3 | `Obra` | texto (`PRESUP.OBRA`) | | |
| 4 | *(vacía)* | | | |
| 5 | `Producto` | `Cantidad` | `Precio unitario` | `Descripción (solo referencia)` |
| 6… | código de mainque | cantidad | precio | descripción de mainque + origen en Metrix (**no se tipea**) |

- **Precio unitario**: **sin IVA**, con la **bonificación general del
  presupuesto ya descontada** (no hay que aplicarla de nuevo). Redondeado a 2
  decimales; el subtotal puede diferir en centavos.
- **Cantidad**: piezas si el código de mainque es **UN**, m² si es **M2**
  (hasta 3 decimales).
- **Un código aparece una sola vez**: los productos de Metrix que van al mismo
  código de mainque ya vienen sumados (ej. todos los herrajes en una línea
  8694, todo el FASON en una línea 5034, todas las perforaciones en una 5056).
- **Hasta 20 productos** (`MAX_LINEAS_BOT`, igual que `MAX_LINEAS` del bot).
  Si un presupuesto tuviera más, la planilla igual se genera y la hoja
  `control` lo avisa; el bot la rechaza. (En los últimos 200: ninguno.)
- Hoja **`control`** (informativa, para humanos): total de Metrix sin IVA,
  bonificación, total esperado de la NP (`TV_TSIVA − TV_TOTBON`), suma de las
  líneas, de dónde sale cada línea y su confianza, y los **AVISO** (ej.
  "Bonificación general 5% aplicada al precio de cada producto"). Útil para que
  el bot verifique el total que lee en pantalla antes de F10.
- **Observación de la NP**: el bot ya arma `P<presupuesto> - <obra>` con las
  filas 2 y 3.
- **Si un presupuesto tiene algo sin cruce, no hay planilla** (ver más abajo
  qué devuelve). El bot nunca recibe una NP incompleta.
- **Empresa TEST de mainque**: tiene los mismos códigos que la real (confirmado
  por Juan el 2026-10-06), incluidos los dados de alta después del export de
  los Excel (61 flete, 9213 y 9273 DVH). **Ojo (2026-10-15): no es de prueba.**
  Ahí van las NP reales de los clientes con medio IVA o sin IVA, con "T" en la
  O.Compra de Metrix. Ver `docs/PLAN_NP_A_PEDIDO.md`, sección del resultado.
- Muestras para probar: `salida/cruce_mainque/planillas_bot/`
  (`indice_planillas.xlsx` dice qué prueba cada una: FASON, herrajes, 8
  productos, catálogo viejo, LAMILUX, intercapa, espejos, DVH equivalente...).

Generar una planilla a mano (desde la carpeta del proyecto):

```
_work\venv\Scripts\python.exe -m negocio.cruce_mainque planilla 11580
_work\venv\Scripts\python.exe -m negocio.cruce_mainque planilla-pedido 10950   (desde el número de pedido)
_work\venv\Scripts\python.exe -m negocio.cruce_mainque lineas 11580            (solo mostrar, sin escribir)
```

---

## 🖥️ Para el chat que sirve los presupuestos desde el servidor a la carpeta pública

> **Diseño acordado el 2026-10-06: `docs/PLAN_NP_A_PEDIDO.md`.** La planilla
> se genera **a pedido** (el compañero tipea el Nº de presupuesto en la ventana
> del bot, la PC de Juan la arma en ese momento y la deja en
> `...\juan\np_bot\listas\`), no se publica todo cada X minutos. Ahí está el
> contrato de archivos entre el bot y el generador.

**La función a usar** (no hace falta reimplementar nada del cruce):

```python
from negocio import cruce_mainque as cm

cm.limpiar_caches()          # OBLIGATORIO antes de cada tanda si el proceso queda corriendo
try:
    ruta, np_ = cm.generar_planilla_bot(numero_presupuesto, ruta=r"\\...\Publico\...\np_presupuesto_11580.xlsx")
except ValueError as ex:     # hay pendientes: NO se escribió nada
    texto = str(ex)          # "Presupuesto 11242: hay pendientes, no se genera la planilla:\n  - cliente 2666: SIN CRUCE -- ..."
```

- `armar_lineas_np(numero)` devuelve lo mismo sin escribir archivo (dict con
  `lineas`, `pendientes`, `avisos`, `cliente_mainque`, `total_metrix_sin_iva`,
  `bonificacion_general`, `productos`...). Útil para decidir antes de escribir.
- `presupuesto_de_pedido(pedido)` → número de presupuesto vinculado a un pedido
  (`PEDIDO1.PRESUP_REL`; levanta `ValueError` si no tiene). Solo ~22% de los
  pedidos tienen presupuesto vinculado; muchos los carga SILVINA aunque entren
  por la interfaz.
- **Qué presupuestos procesar**: `PRESUP.ESTADO_PRES = 'ACEPTADO'` (si no está
  aceptado, la planilla sale igual pero con un AVISO). Ojo: `PRESUP.NUMERO` y
  `PEDIDO1.TV_FACTU` comparten rango numérico y pueden chocar; no usar el
  número solo como identificador sin saber de qué tabla viene.
- **Velocidad**: ~0,05 s por presupuesto (200 en ~12 s), todo con `SELECT`.

**Requisitos para que corra** (en el server o donde sea):

| Qué | Dónde | Nota |
|---|---|---|
| Python y librerías | `_work\venv\Scripts\python.exe` del repo | correr desde la raíz del repo |
| Credenciales SQL Server (solo lectura) | `_work/credenciales_metrix_lectura.txt` | lo lee `negocio/config.py`; nunca copiarlas a otro lado |
| Excel exportados de mainque | `C:\Users\geronimo.zanon\datos mainque\` (`ACTUALIZADOS\` y `VIEJOS\`) | **se puede cambiar con la variable de entorno `METRIX_DATOS_MAINQUE`** |
| Decisiones de Juan | `salida/cruce_mainque/equivalencias_manuales.csv` | relativo a la carpeta del repo; si se corre en otra máquina, copiarlo (sin él se pierden las 54 decisiones de Juan) |

**Recomendaciones** (no implementadas, son del lado del servicio):
- Escribir cada planilla con nombre temporal y **renombrarla al final**, para
  que el bot nunca agarre un archivo a medio escribir (es el mismo patrón de
  "atomic swap" del repo: `pipeline.bitacora.reemplazar_archivo_con_reintentos`).
- Llevar **registro de qué presupuesto ya se publicó / ya cargó el bot**, para
  no generar ni cargar dos veces la misma NP (también figura como pendiente en
  `bots/ESTADO_Y_PENDIENTES.md`).
- Dejar los que dan `ValueError` en un listado para un humano (con el texto del
  error, que ya dice qué falta y por qué).
- Seguir las convenciones del repo: logger de `pipeline.bitacora`, lock de
  instancia única si es un servicio, y **nunca escribir en SQL Server**.

---

## 📁 Dónde está cada cosa

| Qué | Dónde | En git |
|---|---|---|
| Código del cruce | `negocio/cruce_mainque.py` | sí (master) |
| Documentación técnica + historia de decisiones | `docs/CRUCE_MAINQUE.md` | sí |
| Este mapa | `docs/MAPA_CRUCE_MAINQUE.md` | sí |
| Bot de mainque (NP) | `bots/bot_mainque.py` (v0.2.1), `bots/README.md`, `bots/ESTADO_Y_PENDIENTES.md` | sí |
| Excel exportados de mainque (clientes y artículos) | `C:\Users\geronimo.zanon\datos mainque\` (`CLIENTES TODOS.xlsx`, `ACTUALIZADOS\GRUPO * MODIF.xlsx`, `VIEJOS\GRUPO *.xlsx`) | no |
| **Decisiones de Juan** (clientes, artículos, códigos nuevos) | `salida/cruce_mainque/equivalencias_manuales.csv` (+ backup `equivalencias_manuales_backup_2026-10-06.csv`) | **no** (tiene datos de clientes) — no borrar |
| Tablas de cruce (clientes, artículos, DVH sin código...) | `salida/cruce_mainque/cruce_clientes.xlsx`, `cruce_articulos.xlsx`, `*_equivalencias.csv` | no |
| Planilla de revisión para humanos | `salida/cruce_mainque/REVISAR_NP.xlsx` (comando `revision`) | no |
| Cruce de Juan contra mainque (6/10) | `salida/cruce_mainque/REVISAR_NP_cruzada_por_Juan_2026-10-06.xlsx` y `REVISAR_NP_revisada_por_Juan_2026-10-06_0847.xlsx`; original en `\\192.168.130.210\Publico\Herrajes\ej metrix\REVISAR_NP.xlsx` | no |
| Planillas de muestra para el bot | `salida/cruce_mainque/planillas_bot/` (+ las aprobadas el 5/10 en `planillas_bot_anteriores_2026-10-05_0919/`) | no |
| Informe 222 "Detalle de Presupuesto 2" en SQL | `salida/vista_informe_presupuestos_2.sql` (y reimplementado en `_detalle_presupuesto_2()`) | sí |

## ⚙️ Cómo funciona (en 6 pasos)

1. **Cliente**: `cliente_mainque(codigo_metrix)` → por **CUIT** (los códigos de
   Metrix y mainque solo coinciden para los clientes cargados el 2022-06-06; los
   demás son independientes), o mismo código + nombre idéntico, o decisión
   manual de Juan.
2. **Cada renglón del presupuesto** (`DETPRES` + piezas de `DETPRES2`) se
   convierte en un "producto Metrix": vidrio suelto + tipo de venta (según la
   clase: TEMPLADO / CORTE / DISTRIBUCIÓN), DVH (vidrio / cámara / vidrio),
   FASON, herraje, perforación o flete.
3. **Producto Metrix → código de mainque**: un parser lleva la descripción de
   Metrix y la de mainque a la misma composición (espesor, vidrio base, color,
   temple, intercapa) y busca en el catálogo de mainque; si hay varios, decide
   la regla (abajo). Las decisiones manuales de Juan ganan siempre.
4. **Agrupar por código de mainque** (cantidad en UN o M2 según el código).
5. **Precio** = subtotal de Metrix (`V_PRETO`, ya con descuentos de línea) ×
   (1 − bonificación general) ÷ cantidad. La suma cierra con `TV_TSIVA − TV_TOTBON`.
6. **Planilla**: solo si no hay ningún pendiente.

## 📏 Reglas de negocio (todas confirmadas por Juan, 3 al 6 de octubre de 2026)

| Tema | Regla |
|---|---|
| Catálogo | `ACTUALIZADOS` (grupos curados por Juan y su equipo); si ahí no hay equivalencia, `VIEJOS`. Códigos dados de alta después del export: fila `codigo_nuevo` en el CSV de decisiones. |
| Tipo de venta (clase de la pieza) | contiene `TEMP` → templado (grupos TEMPLADOS / LAMINADO TEMPLADO); `DIST` o `LAMILUX` → **hoja entera** (LAMINADO DISTRIBUCIÓN, en M2); el resto → corte ("A MEDIDA": LAM CORTADO A MEDIDA, FLOAT, ESPEJOS). **Vidrio crudo cortado** (`FLOAT CORTADO`, `LAM CORTADO`) **es corte → "A MEDIDA"**, aunque las piezas sean grandes: lo único que va con código de hoja es la clase DIST / LAMILUX (Juan, 2026-10-06; las NP 11263, 11478 y 11237 cargadas con código de hoja fueron un error humano). |
| Varios códigos iguales | grupo que corresponde a la venta → "A MEDIDA" → UN → fuera del grupo DVH → **código más alto**. En **hoja entera**: M2 y **código más bajo** (146 y no 673 "K"; 126 y 130 para float 8 y 10). Especificación DESCARTE, último. |
| Equivalencias aceptadas | mainque no dice "TEMP" (dentro de un DVH o grupo de templados); TERM = TEMP; espesor no informado (KNT 6 y 8 → mismo código); cámara negra o aluminio; intercapa que mainque no informa (10+10 SGP → 10+10). **Pero si existe el código con la misma intercapa, gana ese**, aunque sea del catálogo viejo (6+6 SGP → 2214). Crudo en Metrix contra TEMP en mainque: **no** (otro producto). |
| Equivalencias de nombres | LAMILUX = laminado de distribución; OPTIMIRROR = espejo; esmerilado / lechoso / traslúcido = esmerilado |
| Corte sin código "A MEDIDA" | va con el código de hoja en M2 (ej. LX3+3 verde claro cortado → 178) |
| FASON (clase `FAS*` o "FASON" en el artículo) | **5034** "FAZON TEMPLADO", siempre en M2, todo en una línea |
| Herrajes (familias HERRAJES, OBSOLETO) | **8694** "HERRAJES", una línea, cantidad = suma de unidades |
| Perforaciones (familia PERF: PI12-30, PIM10, PIM30, ENTRANTE) | **5056** "PERFORACIONES / ENTRANTES", una línea, cantidad = suma de unidades |
| Flete (familia DESPACHO) | **61** (también vale 551; se toma el más bajo) |
| Bonificación general | prorrateada en el precio de cada producto |
| DVH | el orden de los vidrios no importa; una decisión manual vale en los dos órdenes |
| Clientes | mismo CUIT → seguro; mismo código y nombre idéntico → seguro; el resto, a mano |

**Confianzas que usa el bot** (`CONFIANZAS_USABLES`): `MANUAL` (decisión de
Juan o regla fija), `ALTA` (un solo código posible), `REGLA` (varios iguales,
elegido por la regla), `EQUIVALENTE` (difiere solo en lo aceptado arriba).
`MEDIA` / `BAJA` / `SIN CANDIDATOS` / `SIN COMPOSICION` / `FUERA DE ALCANCE`
→ pendiente, no hay planilla.

## 🔧 Mantenimiento (si algún día cambia algo)

| Situación | Qué hacer |
|---|---|
| **Falta el código de un producto o cliente (lo más fácil, desde 2026-10-13)** | En el bot de mainque (v1.4+): buscar el presupuesto; si sale "no se puede cargar", abajo aparece una cajita por cada producto/cliente sin código → escribir el código de mainque → **Guardar y buscar de nuevo**. Cliente sin cruce en una NP que sí se puede cargar: dejar tildado **"recordarlo para la próxima"** (se guarda al terminar la carga). Detalle abajo, en *Cruces desde el bot*. |
| Un código está mal / falta una equivalencia | Agregar una fila en `equivalencias_manuales.csv`: `articulo;<clave_metrix>;<codigo>;<nota>` (la clave sale de las tablas o de la hoja `control`). Gana sobre todo lo automático. |
| Un cliente nuevo no cruza | `cliente;<codigo_metrix>;<codigo_mainque>;<nota>` |
| Se dio de alta un código nuevo en mainque | `codigo_nuevo;<UN o M2>;<codigo>;<descripción>`, o volver a exportar el grupo de mainque a `datos mainque\ACTUALIZADOS\` |
| Revisar todo sin entrar a Metrix | `... -m negocio.cruce_mainque revision 200` → `REVISAR_NP.xlsx` (hoja LEEME); después `aplicar-revision` carga los NO/SI. Lo marcado se conserva al regenerar. |
| ¿Cuántos quedan listos? | `... -m negocio.cruce_mainque cobertura 200` |
| Regenerar todas las tablas | `... -m negocio.cruce_mainque` |

### Cruces desde el bot (bot v1.4, pedido de Juan 2026-10-13)

"Una manera fácil de sumar cruces de clientes y de ítems que no involucre
encontrar las planillas". Agrega dos campos **opcionales** al contrato de
`docs/PLAN_NP_A_PEDIDO.md` (versión 1 sigue valiendo: bots viejos no los mandan
y no pasa nada). Código: `negocio/servir_np.py` (`faltantes_cruzables`,
`guardar_cruces`) y `bots/bot_mainque.py` (`mostrar_cajas_cruce`, `guardar_cruces`).

- **Respuesta** (`listas\<id>.json`) de `NO_SE_PUEDE` y `FALTA_CLIENTE`:
  `faltantes` = lo que se arregla escribiendo un código de mainque,
  `[{tipo: "cliente"|"articulo", clave_metrix, motivo, candidatos, propuesto}]`.
  `motivo` es el mismo texto de `motivos` (el bot no lo repite);
  `propuesto` es el código que el cruce sugiere sin confirmar (MEDIA/BAJA), y
  precarga la cajita. No son "cruzables": medidas, unidad, importes,
  bonificación general, el cliente de prueba de Metrix, ni un código que no
  está en el catálogo.
- **Pedido** (`pedidos\<id>.json`): `cruces_nuevos` =
  `[{tipo, clave_metrix, codigo_mainque, nuevo?}]`. El generador los valida
  **todos o ninguno**: la clave tiene que figurar como faltante en ESE
  presupuesto; un artículo tiene que estar en el catálogo de mainque (si es
  un DVH que no está, se rechaza y el bot muestra el tilde "es un DVH nuevo";
  con `nuevo: true` se agrega además `codigo_nuevo;UN;...` — casi todos los
  DVH de mainque son UN); un cliente se acepta aunque no esté en el export de
  clientes (los clientes sin cruce suelen ser altas nuevas). Si sale bien,
  agrega las filas a `equivalencias_manuales.csv` (nota `bot <usuario>
  <fecha> (ppto N): <descripción>`), vuelve a armar la NP en el mismo viaje y
  avisa "Guardado para siempre: …" (`cruces_guardados`). Si algo está mal:
  `NO_SE_PUEDE` con el error primero en `motivos` y las cajitas con lo escrito
  (`escrito`, `codigo_desconocido`).
- **Resultado** (`resultados\<id>.json`): `cruces_nuevos` con el cliente, si en
  un `FALTA_CLIENTE` quedó tildado "recordarlo para la próxima". Se guarda al
  consolidar el resultado, salvo que la carga haya sido `ABORTADA`.
- Antes del primer cambio de cada día queda una copia
  `equivalencias_manuales_respaldo_<fecha>.csv` al lado. Una fila mal cargada
  se borra con el Bloc de notas, como siempre.

## ❓ Lo que quedó abierto (conocido, no bloquea)

1. **5 clientes con pedidos del último año sin código de mainque**: 2540 y 2457
   (a confirmar), 2490, 2647 y 1 (los resuelve Mauro). Hoja
   `clientes_sin_cruce` de `REVISAR_NP.xlsx`.
2. **DVH sin código en mainque**: 232 composiciones en 12 meses (hoja
   `dvh_sin_codigo` de `cruce_articulos.xlsx`). Como 61, 9213 y 9273 no
   estaban en el export, conviene **volver a exportar los grupos DVH y FLETES**
   de mainque: puede que muchos ya existan.
3. **Laminados compuestos `XLAM`** (LAM001…LAM046, uno por presupuesto) y 4
   artículos sin familia (BLIND4HBRI, BLINDFRMAT, BLINDFRNEG, POMODORINO): sin
   código, van a un humano.
4. **5 cruces sin validar contra una NP real** (ningún presupuesto con pedido los
   usa todavía): 3 DVH con varios códigos iguales (4715, 4913, 3493) y 2
   laminados 10+10 con intercapa al código genérico (5435, 5713).
5. DVH con descripción idéntica y varios códigos en mainque: en las NP reales
   se usaron indistintamente el más alto y el más bajo; Juan los considera
   válidos a los dos. El cruce toma el más alto, salvo los confirmados a mano.

## 🗓️ Historia

| Fecha | Qué |
|---|---|
| 2026-10-03 | Primera versión (rama `cruce-mainque`): clientes por CUIT, templados, DVH, líneas de la NP. 30 de 200 listos. |
| 2026-10-05 | Catálogo `ACTUALIZADOS`, respuestas de Juan (regla, equivalencias, FASON, herrajes, LAMILUX...). Merge a master (`2d0cd93`). 199 de 200. Planilla de revisión. |
| 2026-10-06 | Juan cruzó 136 presupuestos contra las NP reales: flete 61, perforaciones 5056, hoja entera M2 y más bajo, 34 cruces confirmados; crudo cortado → "A MEDIDA" confirmado. Proyecto cerrado. |
