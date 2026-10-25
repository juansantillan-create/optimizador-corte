# Plan: NP "a pedido" — cómo le llegan los presupuestos al bot de mainque

**Estado: diseño acordado con Juan el 2026-10-06. Generador HECHO
(`negocio/servir_np.py`, 2026-10-06); falta el lado del bot.**
Este documento es el contrato entre dos piezas que se desarrollan en chats
distintos:

- **El bot** (`bots/bot_mainque.py`, lo sigue el chat del bot): la ventana que
  usan los compañeros en el escritorio remoto para cargar la NP.
- **El generador** (lado PC de Juan, en `negocio/`): arma la planilla de la NP
  a partir del presupuesto de Metrix, en el momento en que alguien la pide.

Si alguno de los dos chats necesita cambiar algo del contrato (nombres de
archivo, campos del JSON, estados), **se cambia primero acá** y se sube
`"version"`.

> Sin nombres de clientes a propósito (regla de `CLAUDE.md`).

---

## La idea en una línea

Un compañero escribe el **Nº de presupuesto** en la ventana del bot; la PC de
Juan arma la planilla **en ese momento** (desde Metrix en vivo) y la deja en el
Público; el bot la muestra, la carga en mainque y anota el resultado. **Nadie
abre mainque a mano y no se guarda nada "por las dudas" cada X minutos.**

## Decisiones de Juan (2026-10-06)

| # | Tema | Decisión |
|---|---|---|
| 1 | Dónde corre el generador | **En la PC de Juan**, dentro del servicio de negocio que ya corre ahí (es la única que tiene los 3 ingredientes del cruce, ver abajo). |
| 2 | Quién aprieta F10 | **ENSAYO como ahora** hasta que haya confianza: el bot completa todo y el compañero guarda. COMPLETO sigue existiendo. |
| 3 | Cómo pide el presupuesto el compañero | **Una cajita en la ventana del bot** (Nº de presupuesto + Buscar). Se descartó un Excel compartido: se bloquea si dos lo tienen abierto y no se ve nada hasta que se guarda. |
| 4 | Permisos de la carpeta | Carpeta común del equipo en el Público, sin restricciones especiales. |
| — | Empresa real vs TEST | Todavía TEST: faltan mapear cosas del bot. Este plan es solo **cómo servirle los datos**. |

**Por qué "a pedido" y no generar todo cada X minutos**: armar la planilla de
un presupuesto tarda ~0,05 s y son unas pocas consultas `SELECT`. Generándola
en el momento siempre sale con la última versión del presupuesto (si alguien
lo cambió, se ve), no se carga Metrix ni el Público con copias que nadie va a
usar, y no hay planillas viejas dando vueltas.

---

## Diagrama general

```
 ESCRITORIO REMOTO (sesión de cada compañero)          PC DE JUAN (192.168.130.158)
 ┌──────────────────────────────────────┐              ┌──────────────────────────────────────────┐
 │  bot_mainque.exe                      │              │  servicio de negocio (ya corre siempre)  │
 │  ┌────────────────────────────────┐  │              │   └─ tarea "servir NP" cada 5 s          │
 │  │ Nº de presupuesto [11580][Buscar]│ │              │        └─ proceso hijo: generador        │
 │  │ ✔ Cliente 1234 · 6 productos     │ │              │             │                            │
 │  │   Total NP sin IVA $ ...         │ │              │             ├─► SQL Server Metrix        │
 │  │ (•)ENSAYO ( )COMPLETO  [Cargar]  │ │              │             │   (solo lectura, en vivo)  │
 │  └────────────────────────────────┘  │              │             ├─► datos mainque\ (catálogos)│
 │            │              ▲           │              │             └─► equivalencias_manuales.csv│
 │            │              │           │              └─────────────────┬──────────▲─────────────┘
 │            ▼              │           │                                │          │
 │         mainque (TEST)    │           │                                │          │
 └────────────┬──────────────┼───────────┘                                │          │
              │ 1 pedido     │ 3 respuesta + planilla                     │          │
              │ 5 resultado  │                                            │          │
              ▼              │                                            ▼          │
 ┌──────────────────────────────────────────────────────────────────────────────────────────────┐
 │  \\192.168.130.210\Publico\Herrajes\ej metrix\juan\np_bot\                                   │
 │    pedidos\      ← el bot deja el pedido            (lo lee y archiva el generador)          │
 │    listas\       ← el generador deja respuesta + planilla   (las lee el bot)                 │
 │    resultados\   ← el bot deja qué pasó al cargar   (lo lee el generador)                    │
 │    procesados\   ← archivo de lo ya atendido (se limpia solo a los 7 días)                   │
 │    registro.csv  ← historial de NP cargadas (SOLO lo escribe el generador)                   │
 └──────────────────────────────────────────────────────────────────────────────────────────────┘
```

El Público es el único punto que ven las dos máquinas (los `.exe` del bot ya
viven ahí), así que no hace falta abrir puertos ni red nueva.

### Los 3 ingredientes del generador (por qué tiene que ser la PC de Juan)

| Ingrediente | Dónde está | Qué aporta |
|---|---|---|
| El presupuesto | SQL Server de Metrix, leído en vivo (usuario de solo lectura) | cliente, renglones, cantidades, precios, bonificación |
| Catálogos de mainque | `C:\Users\geronimo.zanon\datos mainque\` (`ACTUALIZADOS\`, `VIEJOS\`) | qué códigos existen en mainque |
| Decisiones de Juan | `salida\cruce_mainque\equivalencias_manuales.csv` | cruces confirmados a mano (clientes, DVH, flete...) |

El cruce en sí ya existe y no se toca: `negocio/cruce_mainque.py`
(`armar_lineas_np`, `generar_planilla_bot`, `limpiar_caches`), ver
`docs/MAPA_CRUCE_MAINQUE.md`.

---

## Secuencia, paso a paso

```
 Compañero            Bot (su sesión)                 Público np_bot\             Generador (PC Juan)
    │                      │                               │                            │
    │ escribe 11580,       │                               │                            │
    │ aprieta Buscar ─────►│ 1. escribe pedidos\<id>.json ►│                            │
    │                      │    (con .tmp y renombrar)     │                            │
    │                      │                               │◄── 2. cada 5 s mira ───────│
    │                      │                               │    pedidos\ ; si hay algo: │
    │                      │                               │    arma la planilla desde  │
    │                      │                               │    Metrix EN ESE MOMENTO,  │
    │                      │                               │    consulta registro.csv   │
    │                      │                               │◄── 3. escribe ─────────────│
    │                      │                               │    listas\<id>.xlsx (si    │
    │                      │                               │    corresponde) y DESPUÉS  │
    │                      │                               │    listas\<id>.json        │
    │                      │◄── espera listas\<id>.json ───│                            │
    │                      │    (mira cada 1 s, máx 60 s)  │                            │
    │◄── muestra resumen ──│                               │                            │
    │    o el motivo       │                               │                            │
    │ elige ENSAYO,        │                               │                            │
    │ aprieta Cargar ─────►│ 4. carga la NP en mainque     │                            │
    │                      │    (igual que hoy, con todas  │                            │
    │                      │    sus verificaciones)        │                            │
    │ guarda (F10) y       │                               │                            │
    │ tipea el Nº de NP ──►│ 5. escribe resultados\<id>.json►                           │
    │                      │                               │◄── 6. lo pasa a ───────────│
    │                      │                               │    registro.csv y archiva  │
```

Tiempo típico desde "Buscar" hasta ver el resumen: **~5 a 15 segundos**
(hasta 5 s de espera del generador + arrancar el proceso hijo + 0,05 s del
cruce).

## Qué ve el compañero según la respuesta

```
                          ┌─────────────────────┐
         Buscar 11580 ───►│ espera respuesta    │── 60 s sin respuesta ──► "El generador no responde
                          │ (máx 60 s)          │                            (¿PC de Juan apagada?).
                          └──────────┬──────────┘                            Probá más tarde."
                                     │
      ┌──────────────────┬───────────┴─────────┬─────────────────────┐
      ▼                  ▼                     ▼                     ▼
   LISTA            NO_SE_PUEDE            YA_CARGADO               ERROR
   resumen:         lista de motivos       "Ya tiene NP 2698        mensaje técnico
   cliente,         ("DVH sin código       (cargada el 06/10        (se manda a Juan)
   productos,        en mainque: ...")     por X)."
   total, avisos    → va a un humano,      + si la huella cambió:
   → [Cargar]         no hay planilla      "OJO: el presupuesto
                                            cambió después"
                                           → no se carga. Botón
                                            "Cargar igual" solo
                                            con confirmación
                                            (pedido con "forzar")
```

---

## Contrato de archivos (versión 1)

**Carpeta base**: `\\192.168.130.210\Publico\Herrajes\ej metrix\juan\np_bot\`
(configurable en los dos lados; en el generador, variable de entorno
`METRIX_DIR_NP_BOT`).

**Reglas que valen para los dos lados**
1. **Escritura atómica**: siempre escribir `<nombre>.tmp` y renombrarlo al
   final. Nadie lee archivos `.tmp`.
2. **Un solo dueño por archivo**: el bot solo escribe en `pedidos\` y
   `resultados\`; el generador solo en `listas\`, `procesados\` y
   `registro.csv`. (Varios bots escribiendo el mismo CSV a la vez se pisan;
   por eso cada bot deja su propio archivo y el generador consolida.)
3. **El `.json` de respuesta se escribe último**: si `listas\<id>.json`
   existe, la planilla `listas\<id>.xlsx` ya está completa.
4. Textos en UTF-8. Fechas ISO (`2026-10-06T10:15:30`). Montos con punto
   decimal, sin separador de miles.

### `id` del pedido
`<presupuesto>_<AAAAMMDD_HHMMSS>_<usuario>` — por ejemplo
`11580_20261006_101530_jperez`. Lo arma el bot. `usuario` = variable de entorno
`USERNAME` de la sesión.

### 1) `pedidos\<id>.json` — lo escribe el bot

```json
{
  "version": 1,
  "id": "11580_20261006_101530_jperez",
  "presupuesto": 11580,
  "pedido_por": "jperez",
  "equipo": "<COMPUTERNAME>",
  "fecha": "2026-10-06T10:15:30",
  "forzar": false
}
```
- `presupuesto` es **siempre `PRESUP.NUMERO`** (número de presupuesto), no
  número de pedido: los dos rangos se pisan en Metrix. La cajita dice
  "Nº de presupuesto".
- `forzar: true` solo si el compañero confirmó "Cargar igual" ante un
  `YA_CARGADO`.
- `acepta_falta_cliente` (**opcional**, agregado 2026-10-08, bot v1.3): si es
  `true` y lo **único** que falta es el cliente, el generador arma la planilla
  igual (con `Cliente mainque` vacío) y responde `FALTA_CLIENTE`: el usuario
  escribe el código en el bot, sin un segundo pedido. Desde la v1.3 el cliente
  es además **editable en todos los presupuestos** (para "facturámelo a tal"),
  porque los productos y precios no dependen del cliente.
- `cliente_mainque` (**opcional**, agregado 2026-10-08, bot v1.2): código de
  cliente de mainque que el compañero escribió **a mano** porque el cliente no
  tiene cruce. El generador lo usa para ESA NP (no lo guarda en
  `equivalencias_manuales.csv`) y suma un aviso "elegido a mano en el bot".
  Pedidos sin este campo funcionan igual que antes.

### 2) `listas\<id>.json` (+ `listas\<id>.xlsx`) — lo escribe el generador

```json
{
  "version": 1,
  "id": "11580_20261006_101530_jperez",
  "presupuesto": 11580,
  "estado": "LISTA",
  "planilla": "11580_20261006_101530_jperez.xlsx",
  "resumen": {
    "cliente_mainque": 1234,
    "obra": "texto de PRESUP.OBRA",
    "productos": 6,
    "total_np_sin_iva": 1234567.89,
    "bonificacion_general": 0.0,
    "aceptado": true
  },
  "avisos": ["Bonificación general 5% aplicada al precio de cada producto"],
  "motivos": [],
  "huella": "a1b2c3d4e5f6",
  "np_anterior": null,
  "generado": "2026-10-06T10:15:34"
}
```

| `estado` | Cuándo | Qué trae |
|---|---|---|
| `LISTA` | el cruce salió completo | `planilla` + `resumen` + `avisos` |
| `FALTA_CLIENTE` | (solo si el pedido trae `acepta_falta_cliente`, bot v1.3+) lo único sin cruce es el cliente | `planilla` (con `Cliente mainque` vacío) + `resumen` + `avisos` + `cliente_metrix` + `motivos`. El bot pide el código de mainque al usuario. |
| `NO_SE_PUEDE` | algún cliente o producto sin cruce seguro (el `ValueError` del cruce) | `motivos`: un texto por cada cosa que falta, ya legible para un humano. Sin planilla. Desde 2026-10-08 también `falta_cliente` (true si lo **único** que falta es el cliente: el bot ofrece escribir el código a mano y repide con `cliente_mainque`) y `cliente_metrix`. |
| `YA_CARGADO` | `registro.csv` ya tiene una NP **guardada** de ese presupuesto y el pedido no trae `forzar` | `np_anterior: {"nro_np", "fecha", "cargada_por", "huella_cambio": true/false}`. Sin planilla. |
| `ERROR` | falla técnica (Metrix no responde, etc.) | `motivos` con el detalle |

- La **planilla `.xlsx`** es exactamente la de hoy (`generar_planilla_bot`:
  hoja `pedido` que lee `leer_pedido()`, más la hoja `control`). El bot no
  necesita cambiar cómo la lee.
- **Productos por m² (pedido del chat del bot, 2026-10-06, bot v0.3)**: la hoja
  `pedido` suma 4 columnas **opcionales** a la derecha de la Descripción, con
  este encabezado en la fila de `Producto`:

  | E `Unidad` | F `Medida 2` | G `Medida 3` | H `Hojas` |
  |---|---|---|---|
  | `UN` o `M2` (vacío = `UN`) | cm (fasón 5034: `1`) | cm (fasón 5034: `1`) | hojas esperadas (solo para verificar; vacío en fasón) |

  - En una línea `M2` la **Cantidad son los m² totales** (como hoy) y el bot abre
    "Parámetros técnicos del producto" con Medida 2 / Medida 3. Sin medidas, el
    bot **rechaza la planilla** (no adivina un 1×1).
  - Distribución (clase `DIST` / `LAMILUX`): Medida 2 / Medida 3 = ancho / alto
    de la **hoja** en cm (mm ÷ 10: 3600 → 360). mainque calcula solo las hojas
    en Equival. y el bot las compara con `Hojas`.
  - Una línea M2 lleva **una sola medida de hoja**. Si un presupuesto tiene
    hojas del mismo código en **tamaños distintos**, el generador arma **una
    línea por tamaño** con el **mismo código de producto repetido** (desde
    2026-10-09, caso 11740). El bot carga cada línea por separado.
  - Planillas sin estas columnas se siguen leyendo igual (todo `UN`).
- `huella`: resumen corto (hash) de cliente + códigos + cantidades + precios.
  Sirve para detectar si el presupuesto cambió después de cargado.
- `aceptado: false` si `PRESUP.ESTADO_PRES` no es `ACEPTADO`: la planilla sale
  igual, con un aviso. El bot debería mostrarlo bien visible.

### 3) `resultados\<id>.json` — lo escribe el bot, al terminar

```json
{
  "version": 1,
  "id": "11580_20261006_101530_jperez",
  "presupuesto": 11580,
  "huella": "a1b2c3d4e5f6",
  "modo": "ENSAYO",
  "resultado": "GUARDADA",
  "nro_np": 2698,
  "usuario": "jperez",
  "fecha": "2026-10-06T10:18:02",
  "detalle": ""
}
```
- `resultado`: `GUARDADA` (hay NP), `NO_GUARDADA` (el compañero decidió no
  guardar) o `ABORTADA` (frenó el bot: freno de emergencia, verificación que
  no cerró...; el motivo en `detalle`).
- **En ENSAYO el bot no ve el F10**: al final pregunta *"¿La guardaste? Nº de
  NP: [____]  /  No la guardé"*. Si no se escribe este archivo, el registro no
  se entera y no puede frenar una carga doble.
- `huella`: la misma que vino en la respuesta (así el registro sabe qué
  versión del presupuesto se cargó).
- `empresa` (opcional, bot v1.5 en adelante): `TEST` o `REAL`, la empresa de
  mainque donde quedó la NP.

**Empresa TEST (corregido el 2026-10-15).** La empresa TEST de mainque **no es
de prueba**: ahí se cargan las NP **reales** de los clientes con medio IVA o
sin IVA (opciones 2 y 3 del bot). En Metrix su O.Compra lleva una "T"
(`2709T`). Hasta el bot v1.4, toda NP guardada en TEST se informaba como
`NO_GUARDADA` "de prueba" y no entraba al registro. Así pasó con 2707, 2708 y
2709, que eran reales: se agregaron a mano al registro el 15/10. Desde la v1.5
llegan `GUARDADA` + `empresa`. Lo que es una prueba lo decide el **generador**
por el cliente de Metrix: una `GUARDADA` de un presupuesto del cliente de
prueba (`config.CLIENTE_PRUEBA_METRIX`, 2691) se anota `PRUEBA`.

### 4) `registro.csv` — solo lo escribe el generador

Separado por `;`, una fila por resultado:
`fecha;presupuesto;nro_np;resultado;modo;usuario;huella;id;empresa`
(la columna `empresa` se agregó el 2026-10-15; las filas anteriores la tienen
vacía).

Es la memoria de "qué presupuesto ya tiene NP". Un presupuesto cuenta como
cargado solo con `resultado = GUARDADA` (`PRUEBA` no cuenta). En el
`YA_CARGADO`, `np_anterior` trae además `empresa`. Para la O.Compra del pedido
de Metrix, `servir_np.ocompra_de_np`: `30361` (REAL) o `2709T` (TEST).

**Códigos nuevos desde las cajitas (`cruces_nuevos`).** Si el código que se
escribe no está en el export de mainque, el generador devuelve
`codigo_desconocido` y el bot ofrece el tilde "es un código nuevo". Hasta la
v1.4 eso valía solo para DVH (que se dan de alta como UN). Desde el 2026-10-15
vale para **cualquier producto** (caso FL8BR TEMP → 9295, creado en el
momento): el cruce viaja con `"nuevo": true` y, si no es DVH, con
`"unidad": "UN"` o `"M2"`, que elige el usuario (entre los vidrios hay de las
dos unidades).

---

## Qué tiene que hacer cada chat

### Chat del bot (`bots/bot_mainque.py`)
- [ ] Cajita "Nº de presupuesto" + botón Buscar (queda el botón actual de
      elegir un Excel, para pruebas).
- [ ] Escribir `pedidos\<id>.json` (con `.tmp` y renombrar).
- [ ] Esperar `listas\<id>.json` (cada 1 s, máximo 60 s) y mostrar el resumen,
      los avisos o los motivos según `estado`.
- [ ] Con `LISTA`: cargar `listas\<id>.xlsx` como hoy (sin cambios en la
      carga ni en las verificaciones).
- [ ] Con `YA_CARGADO`: mostrar la NP anterior y el aviso de huella; "Cargar
      igual" solo con confirmación → nuevo pedido con `forzar: true`.
- [ ] Al terminar: preguntar el Nº de NP en ENSAYO (en COMPLETO ya lo lee) y
      escribir `resultados\<id>.json`.
- [ ] Si el generador no responde en 60 s: mensaje claro, no reintentar solo.

### Generador (chat de `negocio/`, PC de Juan)
**Hecho el 2026-10-06.**
- [x] `negocio/servir_np.py`: atiende todo lo que haya en `pedidos\`
      (`limpiar_caches()` → `armar_lineas_np` / `generar_planilla_bot` →
      `listas\`), consolida `resultados\` en `registro.csv`, archiva en
      `procesados\` y borra lo de más de 7 días.
- [x] Sumado a `negocio/servicio.py` como una tarea cada 5 s que, **solo si
      hay archivos nuevos**, corre el generador en un **proceso hijo con
      tiempo límite** (120 s; mismo esquema que el ciclo analítico desde el
      2026-10-05: si pyodbc se cae, no se lleva el servicio puesto). Si el
      Público no responde, avisa una vez en el log y reintenta solo.
- [x] Nunca escribe en SQL Server (solo `SELECT`, como todo el repo).
- [x] Logger de `pipeline.bitacora` (`logs/negocio_servir_np.log`).
- [x] Probado con las planillas de muestra: **29/29 idénticas** a las de
      `salida/cruce_mainque/planillas_bot/`; 32 pedidos en 8,4 s (incluye
      leer los catálogos de mainque); presupuesto con cliente sin cruce →
      `NO_SE_PUEDE`; inexistente o JSON roto → `ERROR`; `.tmp` ignorados;
      `GUARDADA` → `registro.csv` → `YA_CARGADO` (huella igual) → con
      `forzar` vuelve a `LISTA`.

Comandos útiles (desde la carpeta del proyecto):
```
_work\venv\Scripts\python.exe -m negocio.servir_np estado   (qué hay en cada carpeta y en el registro)
_work\venv\Scripts\python.exe -m negocio.servir_np          (atender lo pendiente a mano, sin el servicio)
```
Para probar sin tocar el Público: variable de entorno `METRIX_DIR_NP_BOT`
apuntando a otra carpeta. Las carpetas `pedidos\`, `listas\`, etc. las crea
el generador solo la primera vez que mira.

**Columnas M2 del bot v0.3 (Unidad / Medida 2 / Medida 3 / Hojas): hechas el
2026-10-06** en `negocio/cruce_mainque.py` (`_medidas_m2`), así que salen en
toda planilla (servida o hecha a mano):
- Columna `Unidad` siempre (`UN` o `M2`, la unidad del código en mainque).
- Fasón 5034 → `1` y `1`, `Hojas` vacío.
- Hoja entera (clase `DIST` / `LAMILUX`) → tamaño de la hoja en cm, **lado
  mayor primero** (3600×2500 mm → `360`, `250`); `Hojas` = m² ÷ área de la
  hoja (siempre entero en los datos; si no da entero → `NO_SE_PUEDE`).
- **Hojas de distinto tamaño en el mismo código** (la duda de arriba): no
  apareció en ninguna de las 90 líneas de distribución de los últimos 200
  presupuestos aceptados. Si aparece → `NO_SE_PUEDE` con el motivo (no se
  parte en líneas hasta que Juan lo decida).
  **Resuelto el 2026-10-09 (pedido de Juan, caso 11740: LX3+3 LAMILUX en
  2200×3600, 2500×3600 y 2500×4000 → código 145):** si el código es **todo
  distribución**, se parte en **una línea por tamaño de hoja**, cada una con
  sus m², su importe (precio = importe ÷ m²) y sus `Hojas`. Ej.: 145 ×
  142,56 m² (360×220, 18 hojas) + 145 × 153 m² (360×250, 17) + 145 × 150 m²
  (400×250, 15). 2500×3600 y 3600×2500 cuentan como la misma hoja. Si el
  código mezcla hojas enteras y cortes, sigue `NO_SE_PUEDE`.
- **Corte o templado con código en m²** (ej. corte de un vidrio que solo tiene
  código de hoja: 178, 193, 23; templado 2214): piezas de tamaños distintos y
  el contrato no define qué medida va → `NO_SE_PUEDE` ("falta definir Medida 2
  / Medida 3"). Son 7 de los últimos 200 aceptados.
  **Resuelto el 2026-10-07 (regla de Juan):** todo lo que no sea distribución
  (hojas enteras o medias, 3600×2500 o 1800×2500) lleva **1 y 1, sin `Hojas`**,
  igual que el fasón. El campo Especific. ("hoja origen") lo sigue resolviendo
  el bot (si viene vacío escribe 1). Las 7 planillas pasan `leer_pedido()` y
  quedan **198 de 200** listos (los 2 que faltan son del cliente 2666, que se
  factura a otra razón social). Si un mismo código mezcla hojas enteras y
  cortes en un presupuesto → `NO_SE_PUEDE` (no apareció nunca).
- Verificado: las 192 planillas listas de los últimos 200 aceptados pasan el
  `leer_pedido()` real del bot v0.3 (rama `worktree-bot-v03-m2`) con las
  mismas medidas; las muestras aprobadas siguen idénticas en
  producto/cantidad/precio (27/29; las otras 2 son los casos de corte/templado
  en m²).

Detalles que el bot puede aprovechar:
- `ERROR` incluye "No existe el presupuesto N" cuando el número no está en
  Metrix (típico: tipearon un Nº de pedido).
- Más de 20 productos → `NO_SE_PUEDE` con el motivo (el bot carga hasta 20).
- Si el `id` trae caracteres raros (barras, espacios), el generador usa el
  nombre del archivo del pedido como `id`: armar el `id` como dice el
  contrato evita sorpresas.

---

## Carga sobre Metrix, el Público y la PC de Juan

- **Metrix**: solo se consulta cuando hay un pedido, unas pocas consultas
  livianas por presupuesto. 50 NP por día no se notan (el ciclo de negocio ya
  trae la tabla de piezas entera cada 5 min).
- **Público**: archivos de pocos KB, se archivan al atenderse y se borran a
  los 7 días.
- **PC de Juan**: mirar una carpeta casi vacía cada 5 s es despreciable; el
  proceso hijo solo arranca cuando hay pedidos.
- **Si la PC de Juan está apagada**: los pedidos quedan esperando en
  `pedidos\` (no se pierden) y el bot avisa a los 60 s. Si algún día molesta,
  el generador se puede mudar a una máquina siempre prendida sin cambiar el
  contrato (necesita los 3 ingredientes).

## Fuera de alcance de la v1 (ideas para después)

- **Bandeja de "aceptados sin NP"**: el servicio de negocio ya trae `PRESUP`
  cada 5 min a la base local; se podría mostrar la lista en la ventana del bot
  para elegir en vez de tipear, sin consultar Metrix de más.
- Página web con vista previa (sobre la API que ya existe).
- Bot desatendido en una sesión dedicada, tomando los mismos pedidos (el
  contrato no cambia: solo cambia quién deja el pedido y quién aprieta F10).
- Pedido por mail (orquestador).
- Pedir por **Nº de pedido** de Metrix (`presupuesto_de_pedido()` ya existe,
  pero solo ~22% de los pedidos tienen presupuesto vinculado).
