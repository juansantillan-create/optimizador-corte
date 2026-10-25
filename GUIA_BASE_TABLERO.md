# Guía de la base del tablero (`base_tablero.duckdb`)

Para quien quiera armar su propia versión del **Tablero de programación** o
analizar la producción de la planta con datos reales de Metrix. Está pensada
para leerla y también para **pegarla entera en una IA** (Gemini, ChatGPT,
Claude) como contexto antes de pedirle consultas o código: no tiene ningún dato
real de clientes, solo la estructura y las reglas.

Escrita el 2026-10-16. La genera y la copia junto a la base
`negocio/exportar_base_tablero.py`; el original vive en `docs/GUIA_BASE_TABLERO.md`.

---

## 0. En 30 segundos

- Es un archivo **DuckDB** (una base de datos en un solo archivo, se consulta con SQL).
- Es una **foto** de Metrix: no se actualiza sola. La fecha de la foto está en la tabla `_info`.
- No se conecta a nada: ni al servidor de Metrix ni a internet. Se puede romper lo que se quiera, la original no se toca.
- Viene en la carpeta `salida\base_tablero\` del proyecto, junto con:
  - `GUIA_BASE_TABLERO.md`: este archivo.
  - `mapa_tablero.html`: página visual que muestra, con pedidos reales, cómo los datos se transforman en cada columna del tablero. **Conviene abrirla primero.**
- Las tablas más importantes:
  - **`tablero`**: el resultado final, una fila por pedido. Es lo mismo que muestra la pantalla `http://localhost:8501`.
  - **`cajas`**: una fila por **pieza física**, con qué procesos lleva, cuáles ya están hechos y **cuándo** (día y hora).
  - **`piezas_pasos`**: la misma información de `cajas`, pero una fila por pieza y proceso, con fecha y hora ya convertidas. Es la más cómoda para analizar.
  - **`pedido1`**: los pedidos (cabecera). **`pedido2` / `pedido3`**: las líneas de cada pedido.
  - **`reposiciones`**: vidrios rotos que se refabrican.

---

## 1. Reglas de convivencia (importante: la PC es compartida)

Esta PC también corre los servicios de datos de Metrix: la API para Power BI,
el tablero del puerto 8501 y la copia cada 5 minutos. Tiene **3,9 GB de RAM** y
anda justa. El 2026-10-16 se quedó sin memoria un rato por correr dos cosas
pesadas a la vez.

1. **Trabajar sobre esta base, nunca sobre `salida\datos.duckdb`** (la usan los
   servicios) **ni contra el SQL Server de Metrix**.
2. **Mejor trabajar sobre una copia propia.** Copiá `base_tablero.duckdb` a tu
   carpeta y abrí esa. Si alguien tiene abierta la de `salida\base_tablero\`,
   no se puede regenerar.
3. **Abrir en modo solo lectura** cuando no haga falta escribir:
   `duckdb.connect(ruta, read_only=True)`.
4. **Ponerle un tope de memoria a DuckDB** al conectar:
   `SET memory_limit = '500MB'; SET threads = 2;`. Si la consulta necesita más,
   DuckDB usa el disco: tarda un poco más, pero no ahoga la PC.
5. **Python: no instalar paquetes en `_work\venv`**, que es el entorno de los
   servicios. Hay que crear uno propio:
   `python -m venv C:\ruta\mi_entorno`, después
   `C:\ruta\mi_entorno\Scripts\pip install duckdb pandas streamlit`.
6. **Streamlit: usar otro puerto.** El 8501, el 8502 y el 8080 ya están tomados.
   Por ejemplo: `streamlit run mi_tablero.py --server.port 8510`.
7. **Cerrar lo que no se usa** (Streamlit, Jupyter, pestañas pesadas), sobre todo en horario de planta.
8. **Para tener datos nuevos**: doble clic en `Generar_Base_Tablero.bat`, en la
   carpeta del proyecto. Tarda unos 10 segundos y, si en ese momento está corriendo
   la copia de datos, espera solo a que termine.

---

## 2. Cómo abrirla

**Python**:

```python
import duckdb
con = duckdb.connect(r"C:\ruta\a\base_tablero.duckdb", read_only=True)
con.execute("SET memory_limit = '500MB'; SET threads = 2")
df = con.execute("SELECT * FROM tablero LIMIT 20").fetchdf()   # un DataFrame de pandas
print(df)
con.close()
```

**Un Streamlit mínimo** (para arrancar un tablero propio):

```python
import duckdb, streamlit as st
st.set_page_config(page_title="Mi tablero", layout="wide")

@st.cache_data(ttl=600)
def cargar():
    con = duckdb.connect(r"C:\ruta\a\base_tablero.duckdb", read_only=True)
    try:
        return con.execute("""
            SELECT * FROM tablero
            WHERE INGRESO >= current_date - INTERVAL 30 DAY
            ORDER BY INGRESO DESC""").fetchdf()
    finally:
        con.close()   # cerrar siempre: si queda abierta no se puede regenerar

st.dataframe(cargar(), use_container_width=True, hide_index=True)
```

**DBeaver** u otro visor: se puede abrir con el driver de DuckDB. Hay que
cerrar la conexión al terminar. La base se genera con DuckDB 1.5.4: conviene
usar esa versión o una más nueva.

---

## 3. Mapa de tablas

```
clientes ──(c_codcli = pedido1.tv_cocli)── pedido1 ──(tv_factu)──┬── pedido2  (v_factur)   líneas del pedido
                                              │                   ├── pedido3  (v_factur)   detalle antes de cortar
                                              │                   └── cajas    (pedido)     piezas físicas
deveng1 ──(pedido = pedido1.tv_factu)─────────┘                        │
   │  └──(notas 'PIEZA n' → cajas.numero)──────────────────────────────┘
   └──(numero)── deveng2                    pedido2 / pedido3 / cajas ──(v_codart = articulo.codigo)── articulo
                                            cajas ──(nomclase = clases.clase)── clases
```

Tablas ya armadas (derivadas):

| Tabla | Sale de | Qué es |
|---|---|---|
| `tablero` | pedido1 + pedido2 + pedido3 + cajas + articulo + clientes | El tablero de programación, una fila por pedido |
| `piezas_pasos` (vista) | cajas | Una fila por pieza y proceso aplicable, con fecha/hora reales |
| `reposiciones` | deveng1 + deveng2 + cajas + pedido2 | Una fila por reposición, con etapa y días abierta (validada contra el informe 218 de Metrix) |
| `_info` | — | Cuándo se generó, de qué foto, cuántas filas tiene cada tabla |

Tamaños aproximados (octubre 2026): `cajas` 525 mil piezas, `pedido1` 12 mil
pedidos, `pedido2` 59 mil líneas, `pedido3` 44 mil, `articulo` 4 mil,
`clientes` 1.250 y `reposiciones` 7.700.

---

## 4. Convenciones que hay que saber sí o sí

### Fechas y horas (formato Clarion)

Metrix es un sistema Clarion y guarda las fechas como números:

- **Fecha** (`*_fec`, `tv_fefac`, `fecha`...): **días desde el 28/12/1800**.
  `0` = sin fecha. En SQL: `DATE '1800-12-28' + CAST(x AS INTEGER)`.
- **Hora** (`*_hora`): **centésimas de segundo desde la medianoche, más 1**.
  `0` = sin hora. Ejemplo: `3600001` = 10:00:00.

La base trae dos funciones (macros) para no hacer la cuenta a mano:

```sql
SELECT fecha_clarion(tv_fefac) FROM pedido1;                -- DATE
SELECT fecha_hora_clarion(tp_fec, tp_hora) FROM cajas;      -- TIMESTAMP
```

En `piezas_pasos`, `tablero` y `reposiciones` las fechas ya vienen convertidas.

### Marcas de proceso de las piezas (`cajas`)

Cada proceso es una columna de texto con 3 valores posibles:

| Valor | Significa |
|---|---|
| `'X'` | **hecho** (y tiene fecha y hora en `<proceso>_fec` / `<proceso>_hora`) |
| `''` (vacío) | **pendiente** (la pieza pasa por ese proceso pero todavía no se declaró) |
| `'*'` | **no aplica** (la pieza no pasa por ese proceso) |

### Los procesos

| Columna | Proceso | Etapa (orden) | En el tablero |
|---|---|---|---|
| `ct` | Corte monolítico | 1 Corte | `% COM` |
| `ser` | Corte laminado | 1 Corte | `% COL` |
| `bd` | Pulido recto | 2 Pulido | `% PUR` |
| `mf` | Pulido matado de filo (aristas) | 2 Pulido | `% PUF` |
| `mec` | Mecanizado (perforado / entalles) | 3 | `% MEC` |
| `tp` | Templado | 4 | `% TEM` |
| `hj` | Parejas (emparejado de hojas para DVH) | 5 | `% PAR` |
| `dv` | Armado DVH | 6 | `% DVH` |
| `lm` | Laminado EVA | 7 | `% LAM` |
| `her` | Sellado estructural | 8 | `% SELLADO` |
| `peg` | Pegado a bastidor | 9 | `% PEG` (lo que la planilla llamaba "% PDV") |
| `lux` | Lamilux (laminado propio en hoja entera) | 10 | — |
| `aut` | Autoclave | 10 | — |

El orden se validó con datos reales: en el 99 % de las piezas la fecha de cada
paso es igual o posterior a la del anterior.

### Otras reglas básicas

- **`cajas.pedido = 0`**: unas 7.700 piezas sin pedido (stock o piezas sueltas). **Siempre excluirlas.**
- **`cajas.destino = 'ANULADA'`**: pieza anulada (~23 mil, sin fecha de anulación). Excluirlas al contar producción pendiente. En el resto de las piezas `destino` es un texto descriptivo (el vidrio, o la composición del DVH al que va).
- **Artículos de familia `X…`** (`XDVH`, `XLAM`...): **no son vidrio**. Son el registro de la **unidad armada** (el DVH o el laminado completo). En `cajas`, la pieza `XDVH` lleva la marca `dv` (armado) y las hojas de vidrio son otras piezas, que llevan `ct`, `bd`, `hj`, etc. Para contar m² de vidrio hay que excluir las `X…`; para contar unidades, contar justamente esas.
- **m² de una pieza** = `largo * ancho / 1e6 * factor` (`factor` sale de `articulo`; si vale 0, usar 1). `largo` y `ancho` están en mm.
- **Números de pedido**: `pedido1.tv_factu`, `pedido2.v_factur`, `pedido3.v_factur` y `cajas.pedido` son el mismo número. En la tabla `tablero` la columna se llama `"N° Metrix"`.
- **Columnas con símbolos en `tablero`** (`"N° Metrix"`, `"m²"`, `"% TEM"`): en SQL van **entre comillas dobles**.
- **Los % del tablero** están guardados como fracción de 0 a 1 (`0.5` = 50 %). Vacío (`NULL`) = ninguna pieza del pedido pasa por ese proceso.

---

## 5. Tablas, columna por columna

### `cajas`: una fila por pieza física (la más importante)

| Columna | Significado |
|---|---|
| `numero` | ID único de la pieza en toda la fábrica (correlativo, no se reinicia por pedido) |
| `pedido` | N° de pedido (→ `pedido1.tv_factu`). 0 = sin pedido |
| `v_codart` | Artículo (→ `articulo.codigo`) |
| `largo`, `ancho` | Medidas en mm |
| `largo3`, `ancho3` | Medida de la segunda hoja en DVH escalonados (casi siempre 0) |
| `nomclase` | Clase de la pieza (ej. `FLOAT PR MEC TEMP`, `DVH`, `PDV DVH`, `LAM PMF`). Define la receta de procesos (→ `clases`). **PDV se detecta por acá**, no por una marca de proceso |
| `notas` | Texto libre del ítem (ej. "C/PERF", "SOBREMED") |
| `destino` | `ANULADA` = pieza anulada; si no, texto descriptivo |
| `numoc` | Orden de compra (texto). Mejor usar `pedido1.ocompra` |
| `optimizacion` | Lote de optimización de corte al que pertenece (-1/0 = sin lote) |
| `numpaquete`, `numpaquetelux` | Paquete de stock / paquete Lamilux |
| `ingreso` | Fecha (Clarion) de alta de la pieza en el sistema |
| `v_canti` | Cantidad (uso en DVH) |
| `lamilux`, `marca`, `car`, `res` | Marcas del circuito Lamilux/Autoclave (`car` = cargada, `res` = reservada) |
| `<proceso>`, `<proceso>_fec`, `<proceso>_hora` | Marca, fecha y hora de cada proceso (ver sección 4) |

### `piezas_pasos` (vista): una fila por pieza y proceso aplicable

Ya excluye `pedido = 0` y los procesos con `'*'`.

| Columna | Significado |
|---|---|
| `pieza`, `pedido`, `v_codart`, `nomclase` | Como en `cajas` |
| `proceso` | Columna de origen (`ct`, `tp`, `dv`...) |
| `nombre_proceso` | Nombre legible ("Templado") |
| `orden_etapa`, `etapa` | Orden y nombre de la etapa (ver tabla de procesos) |
| `estado` | `hecho` / `pendiente` |
| `fecha` | DATE en que se declaró (NULL si está pendiente) |
| `fecha_hora` | TIMESTAMP en que se declaró (NULL si pendiente o sin hora) |

### `pedido1`: cabecera del pedido (una fila por pedido)

| Columna | Significado |
|---|---|
| `tv_factu` | **N° de pedido** |
| `tv_cocli` | Código de cliente (→ `clientes.c_codcli`) |
| `tv_fefac` | Fecha de carga del pedido (Clarion). Es el "INGRESO" del tablero |
| `tv_fevenc` | Fecha de entrega comprometida al cliente (Clarion) |
| `proceso` | Etapa actual según Metrix (`ESPERA`, `OPTIMIZADO`, `PRODUCCION`, `TERMINADO`, `ENTREGADO`...) |
| `estado` | `IMPUTADA`, `ANULADO`, `PENDIENTE` (vocabulario distinto al de presupuestos) |
| `clase`, `clasepedido` | Clase / tipo del pedido |
| `ocompra` | Orden de compra del cliente (texto libre). Es la "OC" del tablero |
| `entrecalles` | Campo viejo que el equipo **reutiliza para anotar la obra**. Es la "OBRA" de DESCRIPCION |
| `presup_rel` | Presupuesto de origen (solo ~22 % de los pedidos lo tiene; 0 = sin presupuesto) |
| `totm2`, `totml` | Totales de m² y metros lineales según Metrix |
| `urgente`, `criticidad`, `bloqueado` | Marcas de prioridad cargadas a mano |
| `lote` | Agrupación de producción |
| `nomusu` | Usuario que cargó el pedido (`INTERFAZ` = importador de Excel) |
| `nomusuprod` | Responsable de producción, a nivel pedido |
| `zonaentrega` | Zona de entrega (sin validar) |
| `motivo`, `anula_fec`, `anula_usu` | Anulación: motivo, fecha y usuario |
| `pr_fec`, `ct_fec`, `bd_fec`, `tp_fec`, `dv_fec`, `fin_fec`, `lt_fec`, `fc_fec`... (+ `_hora`) | Hitos por etapa a nivel pedido (Clarion). `lt_fec` = despachado, `fin_fec` = producción terminada, `fc_fec` = facturado. La regla exacta (primera o última pieza) no está confirmada. **Para tiempos reales, usar las piezas.** |

### `pedido2`: líneas del pedido (lo que se vendió)

| Columna | Significado |
|---|---|
| `v_factur` | N° de pedido |
| `v_codart` | Artículo. Si es de familia `X…` (XDVH, XLAM), la línea es una **unidad armada** |
| `grupo` | **Clasificación que carga el equipo**: DVH, PDV, LAM, TEMPLUX, VIDRIO SOLO, FASON, DIST, LAMILUX... Es la fuente del TIPO del tablero. Hay variantes con espacios o en minúscula: normalizar con `upper(trim(grupo))` |
| `v_canti` | En líneas de unidad armada: **cantidad de unidades**. En el resto: **m²** |
| `v_cantialt` | Cantidad de piezas (cuando está cargada) |
| `largo`, `ancho` | Medida (en unidades armadas, la medida de la unidad) |
| `art1`, `art2`, `art3` | Componentes: en DVH, `art1`/`art3` son los dos vidrios y `art2` la cámara; en LAM, `art2` es la lámina (PVB, SGP, EVA...) |
| `clase` | Clase (ej. `PDV DVH`) |
| `notas`, `notasprod` | Notas del ítem / notas de producción |

### `pedido3`: detalle por medida (sobre todo antes de cortar)

Mientras un pedido está en ESPERA todavía no tiene piezas en `cajas`; este es el
detalle disponible.

| Columna | Significado |
|---|---|
| `v_factur`, `v_codart`, `largo`, `ancho`, `clase`, `notas` | Como arriba |
| `v_canti` | m² de la línea |
| `v_cantialt` | Cantidad real de piezas de esa medida |
| `circular`, `diametro` | Piezas circulares |
| `req_pul`, `req_perf`, `cant_perf` | Requiere pulido / perforación, cantidad de perforaciones |

### `articulo`: catálogo

`codigo`, `descripcion`, `familia` (ej. `FLOAT INCOLORO`, `LAMILUX`, `XDVH`,
`MP LAMINAS` = materia prima), `factor` (multiplicador de m²), `espesor`,
`clase`, `compuesto`.

### `clientes`

`c_codcli`, `c_razsoc` (razón social), `c_fantasia`, `c_locali`, `c_provincia`.
El código **423** es una cuenta interna de producción propia de Lamilux
("OT LAMILUX"): no es un cliente real.

### `clases`: receta de procesos por clase

Una fila por clase (`clase`, 85 clases) y una columna 0/1 por proceso (`ct`,
`bd`, `tp`, `lm`, `dv`, `mf`, `hj`, `mec`, `ser`, `her`, `peg`). Ejemplo: `FLOAT PR MEC TEMP`
→ corte, pulido recto, mecanizado y templado. Es "lo que debería llevar"; lo
que realmente lleva cada pieza está en sus marcas de `cajas`.

### `deveng1`, `deveng2`, `reposiciones`: vidrios rotos que se refabrican

- **`deveng1`**: una fila por reposición. `numero`, `fecha` (Clarion), `pedido`,
  `codcli`, `notas` (`'PIEZA n: texto'`, donde `n` es la pieza de `cajas`),
  `sector`/`motivo` (y `sectorrotura`/`motivorotura`), `cortado` (fecha del
  recorte), `terminado` (fecha del templado), `finalizada` (1 = cerrada),
  `revisada` (`'-'` = descartada, se excluye) y `usuario`.
- **`deveng2`**: el vidrio a reponer (`numero` → `deveng1.numero`, `codigo`, `largo`, `ancho`, `cantidad`).
- **`reposiciones`** (ya armada, conviene usar esta): una fila por reposición,
  con `fecha`, `pedido`, `cliente`, `pieza`, artículo, medidas, `m2`, `motivo`,
  `sector`, `tipo_dvh` (`DVH armado` / `Hoja de DVH` / `No DVH`),
  `fecha_corte`, `fecha_templado`, `finalizada`, **`etapa`** (Finalizada,
  Pendiente de corte, Cortada pendiente de templado, Lista sin cerrar en
  Metrix...), `dias_abierta` y `dias_hasta_corte`.

**Ojo:** Metrix **no crea una pieza nueva** para la reposición: reusa la misma
pieza de `cajas` y le reinicia las marcas. Por eso **las fechas de `cajas` son
solo de la última vuelta**. Para medir retrabajo hay que usar `reposiciones`.
Algunas reposiciones se cargan como pedido nuevo (notas tipo "REPO_01") y no
aparecen acá.

### `tablero`: el resultado

Columnas: `INGRESO`, `SEMANA`, `tablero`, `TIPO`, `Proceso Final`,
`"N° Metrix"`, `OC`, `DESCRIPCION`, `"m²"`, `OBSERVACION`, `cant`,
`"% COM"` … `"% PEG"`, `"m² vidrio"`. Cómo sale cada una: sección 6.

---

## 6. Cómo se calcula el tablero (reglas exactas)

El código que lo calcula está en `negocio/tablero_comun.py::armar_dataframe`. Cada
regla de ahí se validó contra la planilla "Tablero Programación 2026" y contra
pantallas de Metrix. Para cada pedido se juntan cuatro fuentes:

1. **Cabecera**: `pedido1` + `clientes`.
2. **A, piezas (`cajas` + `articulo`)**: si el pedido ya se cortó.
3. **B, `pedido3`**: si todavía no se cortó.
4. **C, `pedido2`**: siempre (GRUPO, unidades armadas, materiales).

Prioridad para cantidades, m² y materiales: **A > B > C** (la primera que tenga datos).

| Columna | Regla |
|---|---|
| `INGRESO` | `fecha_clarion(pedido1.tv_fefac)` |
| `SEMANA`, `tablero` | Vacías a propósito: las decide el equipo, no salen de Metrix |
| `TIPO` | `pedido2.grupo`. Si el pedido tiene líneas con distintos GRUPO, gana el primero en este orden: DVH > PDV > LAM > TEMPLUX > VIDRIO SOLO > FASON > LAMILUX > DIST. Sin GRUPO, pero con piezas: se deduce de las marcas (`dv` aplica → DVH; `lm` → LAM; `lux`/`aut` → LAMILUX; `tp` → TEMPLUX; corte/pulido → VIDRIO SOLO). Sin nada → DIST. **Si TIPO es DVH y alguna pieza es de clase PDV, pasa a PDV** |
| `Proceso Final` | DVH → DVH · PDV → PDV · TEMPLUX → TEMPLADO · DIST → DIST · LAMILUX → AUTOCLAVE · LAM → material de la lámina (`pedido2.art2` → `articulo`, familia `MP LAMINAS`: PVB / PVB1.52 / SGP / IPL / EVA) · VIDRIO SOLO → según la clase más común de las piezas: PMF → PULIDO ARISTAS, PR → PULIDO RECTO, si no CORTE · FASON → FASON TEMPLADO / LAMINADO / PULIDO según la clase |
| `"N° Metrix"` | `pedido1.tv_factu` |
| `OC` | `pedido1.ocompra` |
| `DESCRIPCION` | `clientes.c_razsoc` + `' - '` + `pedido1.entrecalles` (si hay obra) + `' -C/PERF'`, `' -C/FORMA'`, `' -SOBREMED'` si **alguna** pieza tiene ese texto en `notas`. Cliente 423 → "OT LAMILUX" |
| `"m²"` | **m² de la unidad armada** (como la planilla): si el pedido tiene líneas de `pedido2` con artículo de familia `X…` → Σ de esas líneas `largo × ancho × v_canti / 1e6`, más Σ `v_canti` del resto de las líneas. Si no tiene unidades armadas, es igual a "m² vidrio". Coincide con la planilla en el 97,4 % de los pedidos |
| `"m² vidrio"` | Vidrio consumido. A: Σ `largo × ancho × factor / 1e6` de las piezas, sin familias `X…`. B: Σ `pedido3.v_canti`. C: Σ `pedido2.v_canti` (DVH sin piezas: Σ `largo × ancho × v_canti × 2 / 1e6`). En un DVH es el doble del m² de la unidad |
| `OBSERVACION` | Descripciones distintas de `articulo` de las piezas (sin familias `X…` ni `MP …`, sin el prefijo "LAMILUX "). DVH sin piezas: los vidrios de `pedido2.art1`/`art3` |
| `cant` | DVH/PDV: piezas con `dv` aplicable (= unidades armadas). LAM: unidades de las líneas XLAM de pedido2. LAMILUX: piezas con `aut` aplicable. Resto: todas las piezas del pedido (sin cortar: Σ `pedido3.v_cantialt`; en DIST, cantidad de filas de `pedido3`; sin pedido3: Σ `pedido2.v_cantialt`) |
| `"% XXX"` | Piezas del pedido con la marca en `'X'` ÷ piezas donde la marca no es `'*'`. Si todas son `'*'` → NULL |

El cálculo de los % en SQL puro, para usarlo de base:

```sql
SELECT pedido,
       COUNT(*) FILTER (WHERE tp = 'X') * 1.0 / NULLIF(COUNT(*) FILTER (WHERE tp <> '*'), 0) AS pct_tem,
       COUNT(*) FILTER (WHERE ct = 'X') * 1.0 / NULLIF(COUNT(*) FILTER (WHERE ct <> '*'), 0) AS pct_com
FROM cajas
WHERE pedido <> 0
GROUP BY pedido;
```

---

## 7. Recetas SQL (probadas sobre la base el 2026-10-16)

**Pedidos del último mes que todavía no terminaron corte, templado o DVH:**

```sql
SELECT "N° Metrix", INGRESO, TIPO, DESCRIPCION, "m²", "% COM", "% TEM", "% DVH"
FROM tablero
WHERE INGRESO >= current_date - INTERVAL 30 DAY
  AND ("% COM" < 1 OR "% TEM" < 1 OR "% DVH" < 1)
ORDER BY INGRESO;
```

**Producción por día y proceso (piezas y m² de vidrio), última semana:**

```sql
SELECT pp.fecha, pp.nombre_proceso,
       COUNT(*) AS piezas,
       ROUND(SUM(c.largo * c.ancho / 1e6 * CASE WHEN a.factor <> 0 THEN a.factor ELSE 1 END), 1) AS m2
FROM piezas_pasos pp
JOIN cajas c ON c.numero = pp.pieza
LEFT JOIN articulo a ON a.codigo = c.v_codart
WHERE pp.estado = 'hecho'
  AND pp.fecha >= current_date - INTERVAL 7 DAY
  AND a.familia NOT LIKE 'X%'          -- solo vidrio, sin registros de unidad armada
GROUP BY ALL
ORDER BY pp.fecha DESC, piezas DESC;
```

**Templado por hora del día (último mes):** muestra los turnos y el corte del almuerzo.

```sql
SELECT hour(fecha_hora) AS hora, COUNT(*) AS piezas
FROM piezas_pasos
WHERE proceso = 'tp' AND estado = 'hecho' AND fecha >= current_date - INTERVAL 30 DAY
GROUP BY 1 ORDER BY 1;
```

**Horas desde el corte hasta el templado (mediana por semana):**

```sql
WITH t AS (
  SELECT pieza,
         MAX(fecha_hora) FILTER (WHERE proceso IN ('ct', 'ser')) AS corte,
         MAX(fecha_hora) FILTER (WHERE proceso = 'tp') AS templado
  FROM piezas_pasos
  WHERE estado = 'hecho'
  GROUP BY pieza
)
SELECT date_trunc('week', templado) AS semana,
       COUNT(*) AS piezas,
       ROUND(median(date_diff('minute', corte, templado)) / 60.0, 1) AS horas_mediana
FROM t
WHERE corte IS NOT NULL AND templado >= current_date - INTERVAL 60 DAY AND templado >= corte
GROUP BY 1 ORDER BY 1;
```

**Cola actual por proceso** (piezas pendientes de pedidos de los últimos 90
días, sin anuladas; ver la trampa "pedidos zombis" en la sección 8):

```sql
SELECT pp.nombre_proceso, COUNT(*) AS piezas_pendientes, COUNT(DISTINCT pp.pedido) AS pedidos
FROM piezas_pasos pp
JOIN pedido1 p ON p.tv_factu = pp.pedido
JOIN cajas c ON c.numero = pp.pieza
WHERE pp.estado = 'pendiente'
  AND fecha_clarion(p.tv_fefac) >= current_date - INTERVAL 90 DAY
  AND coalesce(c.destino, '') <> 'ANULADA'
GROUP BY pp.nombre_proceso, pp.orden_etapa
ORDER BY pp.orden_etapa;
```

**Reposiciones abiertas por sector y motivo:**

```sql
SELECT sector, motivo, COUNT(*) AS abiertas, ROUND(AVG(dias_abierta)) AS dias_promedio
FROM reposiciones
WHERE etapa <> 'Finalizada'
GROUP BY ALL ORDER BY abiertas DESC;
```

**Recorrido de una pieza, paso a paso:**

```sql
SELECT nombre_proceso, estado, fecha_hora
FROM piezas_pasos WHERE pieza = 500000 ORDER BY orden_etapa, fecha_hora;
```

---

## 8. Trampas conocidas (ya hicieron equivocar a alguien)

1. **Pedidos "zombis"**: muchas piezas viejas (más de 100 mil) quedaron con
   marcas pendientes aunque el pedido ya se entregó, porque al cerrar el pedido
   no se actualizan las piezas. **Cualquier medida de trabajo en curso o de
   cuello de botella tiene que filtrar por fechas recientes** (por ejemplo,
   pedidos de los últimos 90 días o piezas con movimiento reciente). Si no, da
   colas absurdas.
2. **m² de unidad ≠ m² de vidrio**: un DVH de 1 m² consume 2 m² de vidrio.
3. **"% PDV" de la planilla vieja = pegado a bastidor (`peg`)**. PDV (piel de
   vidrio) es una *clase* de pieza (`nomclase` contiene "PDV"), no un proceso.
   El sellado estructural es `her`.
4. **Piezas de familia `X…`**: son la unidad armada, no vidrio. Ver sección 4.
5. **Reposiciones reusan la pieza**: las fechas de `cajas` son de la última vuelta.
6. **`pedido1.nomusu` no es el operario** (es quien cargó el pedido). **No hay
   registro de operario ni de máquina por pieza** en Metrix.
7. **Hitos de `pedido1` (`ct_fec`, `tp_fec`...)**: no está confirmado si
   corresponden a la primera o a la última pieza. Para tiempos, usar
   `piezas_pasos`.
8. **Algunas fechas son absurdas** (hay alguna en 1958): son errores de carga
   puntuales. Filtrar por rango razonable.
9. **Empates**: si un pedido tiene la misma cantidad de piezas de dos clases,
   el "Proceso Final" de VIDRIO SOLO/FASON puede salir de cualquiera de las
   dos. El orden de los materiales en OBSERVACION tampoco es fijo.
10. **Es una foto**: mirar `SELECT * FROM _info` para saber de cuándo son los datos.

---

## 9. Lo que no está (o no está confirmado)

- **Errores/retrabajo por proceso** (`<proceso>_err`, `_obs_err`): existen en
  Metrix, pero no se copian (de las 167 columnas de las piezas viajan 59). Se
  pueden agregar si hacen falta.
- **Fechas planificadas** (`*_fec_plan`): casi vacías en Metrix (0–5 % de los pedidos), no vienen.
- **Optimización de corte (% OPT)**: no está automatizada. `cajas.optimizacion` (lote) podría ser la base.
- **SEMANA / fecha objetivo / Estado / colores** de la planilla del equipo: son
  decisiones a mano, no hay de dónde sacarlas en Metrix.
- **Precios y costos**: no vienen (y `articulo.costo` en Metrix no es un costo real).
- **Capacidad por sector**: no está en Metrix. Está a mano en la hoja "Hoja 42"
  de la planilla "Tablero Programación 2026": por ejemplo, corte monolítico
  50–55 hojas/día y templado 250–400 m²/día.

---

## 10. Contexto sugerido para la IA

Pegar esto (junto con la guía) al empezar una conversación con Gemini u otra IA:

> Estoy trabajando con una base DuckDB (`base_tablero.duckdb`) que es una copia
> de solo lectura de Metrix, el ERP de una fábrica de vidrio procesado
> (corte, pulido, mecanizado, templado, DVH, laminado). Te paso la guía con
> todas las tablas, columnas y reglas. Respetá especialmente: fechas en
> formato Clarion (usar `fecha_clarion()` / `fecha_hora_clarion()` o la vista
> `piezas_pasos`), marcas de proceso `'X'` = hecho, `''` = pendiente, `'*'` =
> no aplica; excluir `pedido = 0`; los artículos de familia `X…` son unidades
> armadas, no vidrio; filtrar por fechas recientes para cualquier medida de
> trabajo en curso; las columnas de `tablero` con símbolos van entre comillas
> dobles. La PC tiene poca RAM: en Python conectá con `read_only=True` y
> `SET memory_limit='500MB'`. Escribime SQL de DuckDB y código Python
> (pandas / Streamlit) listo para correr.
