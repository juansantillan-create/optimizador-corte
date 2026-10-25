# Data Dictionary — every table and field this project uses

This is the most important reference file in this repo — the tribal knowledge
about what Metrix's data actually means, written down so it doesn't live only
in one person's head. It was built by cross-checking field names against
Metrix's own report SQL (243 built-in reports) and against real screens in
Metrix, over several investigation sessions — not guessed from column names
alone. Where something is still uncertain, it says so explicitly; don't
upgrade a "not confirmed" to a fact without checking with the user.

Read `../CLAUDE.md` and `ARCHITECTURE.md` first for context. See
`GLOSSARY.md` for domain-term translations (templado, DVH, etc.).

**A note on confidence**: phrases like "confirmed with real data on
2026-07-10" or "not confirmed" are carried over verbatim from the original
investigation notes (mostly in `salida/*.md`) — keep that distinction when
you extend this file. Don't state something as fact just because it's
plausible; add a new "not confirmed" note instead.

---

## Part 1 — The `.tps` files (Metrix's internal report-engine metadata)

These 9 files, decoded by `pipeline/`, are **not business data** — they
describe how Metrix's own 243 built-in reports are put together. Useful for
understanding Metrix internals, not for building business reports directly
(use Part 2 for that).

| File → table | Contents |
|---|---|
| `COLUMNAS.TPS` → `columnas` | Column definitions used across Metrix's reports |
| `CONSULTA.TPS` → `consulta` | Query definitions behind Metrix's reports |
| `INFORMES.TPS` → `informes` | Catalog of Metrix's 243 built-in reports |
| `INFXUSU.TPS` → `infxusu` | Per-user report access/config |
| `ORIGENES.TPS` → `origenes` | Data-source connection definitions Metrix's reports use. **Contains the SQL Server `sa` password in plain text — see the critical issue in `../CLAUDE.md`. Do not expose or quote this table's contents.** |
| `SCRIPTS.TPS` → `scripts` | The actual SQL text behind each report — this is how the business schema below was originally mapped (by reading the real SQL of dozens of Metrix's own reports) |
| `VARIABLE.TPS` → `variable` | Report parameter/variable definitions |
| `INFGCIAL.TPS` → `infgcial` | Small, low-row-count support table |
| `TEMPRPT.TPS` → *(not loaded)* | Password-protected, password unknown; a temporary reporting table, not core business data. See `../CLAUDE.md` for how to unlock it if the password is ever found. |

---

## Part 2 — The real business data (SQL Server, database `METRIX`)

Read via the `negocio_*`-prefixed tables in `salida/datos.duckdb`. Source:
server `IASCRISTAL`, database `METRIX`, read-only user `metrix_lectura`.

### `CLIENTES` — Clients

The customer master list.

| Field | Meaning |
|---|---|
| `C_CODCLI` (PK) | Client code |
| `C_RAZSOC` / `RAZSOC` | Legal/business name |

Other columns exist (vendor, region, classification, contact) but weren't
extracted in detail — not needed by current reports. 1,213 rows.
Orphan rate against `PEDIDO1`/`PRESUP`: <0.2% — the join is reliable.

### `PRESUP` — Budgets / quotes (header)

A price quote given to a client, before it becomes a real order.

| Field | Meaning |
|---|---|
| `NUMERO` (PK) | Quote number. **Not a SQL Server `IDENTITY` column** — the real numbering mechanism was investigated and not conclusively confirmed (a table called `NUMEROS` was ruled out as the source; most likely `MAX(NUMERO)+1` done by the Clarion app itself). **Important**: this number shares its numeric range (0–10000) with `PEDIDO1.TV_FACTU` and the two can collide — the same number can exist in both tables for different clients. Never use the number alone, without knowing which table it came from, as an identifier. |
| `TV_FEFAC` | Quote creation date (Clarion-style integer — see "Dates" below) |
| `CLIENTE`, `CODCLI` | Client (FK to `CLIENTES.C_CODCLI`) |
| `OBRA` | Project/site name |
| `TV_TOTAL`, `TV_TSIVA` (total incl. VAT), `TV_TOTBON` (discount) | Apparent net total = `TV_TSIVA - TV_TOTBON` |
| `TV_BONIF` | Discount shown to the client on the final quote (different from the internal per-line `DETPRES.DESCUENTO`, see below) |
| `ESTADO_PRES` | **The status field actually used day to day.** Real values: `A INFORMAR` (5,703 — "on hold," not yet communicated to client), `ACEPTADO` (3,488), `RECHAZADO` (259), `REPETIDO` (204), blank (113), `INFORMADO` (4), `PENDIENTE` (1). |
| `ESTADO` | A *different* status field, **confirmed not used in practice** ("we never post budgets with that field" — the user's words). Real values: `PENDIENTE` (6,631), `A INFORMA` (3,115), blank (18), `IMPUTADO` (8). **Use `ESTADO_PRES` for anything, ignore `ESTADO`.** |
| `RECHAZ_CAUSA`, `NOTAS_CAUSA` | Rejection reason |
| `TIPOPRESUP` | Quote type |
| `TV_DESCRIP` | Free-text notes — likely where staff jot down day-of-quote context (e.g. that day's USD exchange rate, sheets to be consumed). **Don't try to parse this automatically; it's unstructured.** |
| `USUARIO` | User who entered the quote |

9,835 rows. Example validated end-to-end: quote 5647 (<cliente>),
project "FAS TEMP", `ACEPTADO`, total $151,138.23.

### `DETPRES` — Quote detail, one row per material line

What you see opening "Detalle" on a quote in Metrix — one row per
material/process combination.

| Field | Meaning |
|---|---|
| `NUMERO` (FK → `PRESUP.NUMERO`) | Orphan rate: 0.00% |
| `V_CODART`, `ART1`, `ART2`, `ART3` | Up to 3 articles/processes per line. Confirmed: `ART1`/`DESCU1` = first glass pane, `ART2`/`DESCU2` = the air gap/spacer (e.g. `CAM09P`, `CAM12P`), `ART3`/`DESCU3` = second pane (same as `ART1` for a symmetric DVH unit) |
| `LARGO`, `ANCHO` | Dimensions in millimeters. `LARGO*ANCHO*0.000001` = m² |
| `V_CANTI` | Quantity — **depends on the line** (corrected 2026-10-03, `docs/CRUCE_MAINQUE.md`): for DVH items (`XDVH`), hardware, freight and perforations it is the piece/unit count; for glass lines that have pieces in `DETPRES2` it is the **total m²** and the piece count is in `V_CANTIALT` (e.g. 2 pieces of FL8IN → `V_CANTI`=3.422, `V_CANTIALT`=2) |
| `V_PREUNI` / `V_PRETO` | Unit price / line total. `V_PRETO` is the **final** line price (after "Aplicar Clases" and "Aplicar Descuentos"); `PRESUP.TV_TSIVA` = Σ `V_PRETO` in 100% of quotes ≥ 10500, and when the article has `DETPRES2` pieces `V_PRETO` = Σ `DETPRES2.V_PRETO` (verified 2026-10-03) |
| `DETALLE` | Free-text description |
| `DESCUENTO` | Line-level adjustment. **For plain tempered glass (non-DVH), this is almost always `-2`, and it is NOT a real business discount** — it's a correction for a historical pricing quirk (Metrix's base tempered-glass price loads about 2% too low; the `-2`, being negative, works out as a +2% surcharge that compensates). |
| `EST_PRETO`, `POL_PRETO`, `MEC_PRETO`, `PDV_PRETO`, etc. | Price broken down per sub-process — useful for "which process contributes most to the final price" analysis |

79 columns, 81,095 rows. Real business filter confirmed against Metrix's own
"Informe Presupuestos 2" report (translated faithfully into
`salida/vista_informe_presupuestos_2.sql`): excludes articles whose
`FAMILIAS.MEDIDAS='SI'` or `FAMILIAS.PERIMETRO='SI'`; for `DVH*`/`EVA*`
articles the description is trimmed before the first `:` and M2/ML are
computed (`LARGO*ANCHO*V_CANTI`).

### `DETPRES2` — Quote detail, one row per individual piece

**Correction to an earlier assumption**: this is not exclusive to DVH/EVA
products — it's used whenever a material within the quote has individual
pieces of different sizes (confirmed with a plain single-pane example, 16
pieces of different sizes). `DETPRES` is the per-material aggregate;
`DETPRES2` is the piece-by-piece breakdown when it applies.

| Field | Meaning |
|---|---|
| `NUMERO` (FK → `PRESUP.NUMERO`) | |
| `V_CODART` | |
| `V_CANTI` | **Unlike `DETPRES`, here `V_CANTI` already IS m²** (not multiplied by dimensions) |
| `V_CANTIALT` | The real piece/unit count (confirmed with a real case: 295×1075mm × 2 units = exactly that row's `V_CANTI`, already in m²) |
| `VIDRIO_PRETO` | Glass-only amount for that line |
| `VIDRIO_PREUNI` | Price per m² **already discounted**: list price (`PRECIOS`, category TEMPLADO for tempered) × (1 − `DETPRES.DESCUENTO`/100) — checked on 41 recent lines, 2026-10-03 |
| `V_PREUNI` / `V_PRETO` / `DETALLE` | Unit price / total / description |

### `PEDIDO1` — Orders (header)

A production order, typically (~22% of the time) born from an accepted quote.

| Field | Meaning |
|---|---|
| `TV_FACTU` (PK) | Order number. Shares its numeric range with `PRESUP.NUMERO` (see collision note above). |
| `TV_FEFAC` | Order creation date |
| `TV_FEVENC` | Delivery commitment date to the client |
| `TV_COCLI` (FK → `CLIENTES.C_CODCLI`) | Orphan rate: 0.06% |
| `CLASE` | Order class/type |
| `PROCESO` | Current stage, already computed by Metrix, in plain text — good for a dashboard. Real values (2026-07): `ENTREGADO` (3,912), `TERMINADO` (2,836), `PRODUCCION` (1,243), `OPTIMIZADO` (993), `ESPERA` (968), `CORTE MONOLITICO` (313), `CORTE LAMINADO` (245), `MECANIZADO` (39), `PULIDO RECTO` (32), `DVH` (28), `PULIDO MF` (13), `PAREJAS` (10), `TEMPLADO` (5) |
| `PR_FEC`, `CT_FEC`, `BD_FEC`, `MEC_FEC`, `TP_FEC`, `LM_FEC`, `HJ_FEC`, `DV_FEC`, `FC_FEC` (invoiced), `FIN_FEC` (production finished), `LT_FEC` (**dispatched/delivered** — the most important date for lead time) | Milestone dates per stage, at order level (likely MIN/MAX across the order's pieces — exact aggregation formula not confirmed) |
| `<PROC>_FEC_PLAN` (e.g. `CT_FEC_PLAN`, `TP_FEC_PLAN`) | *Planned* dates per stage. Real but very sparse: 0% (`HER_FEC_PLAN`, `LT_FEC_PLAN`) to 5.2% (`TP_FEC_PLAN`) coverage of 10,685 orders — too sparse for a reliable KPI today |
| `TOTM2` | Total m² of the order |
| `ESTADO` | Real values: `IMPUTADA` (10,022), `ANULADO` (493), `PENDIENTE` (122), blank (5). **This is a different field/vocabulary from `PRESUP.ESTADO` — don't confuse the two tables' status fields.** |
| `PRESUP_REL` (FK → `PRESUP.NUMERO`) | **Resolved**: of 10,642 orders, 2,312 (~22%) have `PRESUP_REL <> 0`; of those, 99.96% find their quote. **The remaining 78% (8,330 orders) have `PRESUP_REL = 0`** — no formally linked quote. Open business question, partly explained (older orders, or orders entered via the `INTERFAZ` Excel-import tool — 65% of unlinked orders come from that user), not fully resolved. |
| `NOMUSU`, `USUARIO` | User who entered the order — `INTERFAZ` (the automated Excel importer, a separate tool, not part of this project) is the most frequent value |
| `NOMUSUPROD` | The cleanest "responsible operator" field — but at whole-order level, not per piece/stage. 12–13 real production staff names. |
| `NOMUSUCARGA`, `OPTIMIZADO_USU`, `CORTADO_USU`, `TALLER_USU`, `TEMPFPROCESO_USU` | "User per stage" fields that exist but are **100% empty** — legacy, never adopted |
| `TERMINADO_USU` | Partially populated but mixes person names with process names — not reliable without cleanup |
| `ENTREGADO_USU` | Partially populated but contains Clarion-style date integers, not names — looks mis-loaded |
| `ANULA_FEC` / `ANULA_USU` / `MOTIVO` | Clean cancellation fields, 501 cancelled orders. Real reasons: "MAL CARGADO" (79), "CAMBIOS DEL CLIENTE" (30), "CANCELADO POR EL CLIENTE" (19) |
| `URGENTE`, `CRITICIDAD`, `BLOQUEADO` | Manual priority flags — good candidates to highlight on a dashboard |
| `LOTE` | Production batch grouping |
| `OPTIMIZACION` | Reference to a cutting-optimization plan |
| `OCOMPRA` | Client's purchase order — free text. Confirmed exact against the "Tablero Programación 2026" spreadsheet for the order tested. Cleaner source than `CAJAS.NUMOC` (which usually but not always matches). |
| `ENTRECALLES` | An old Metrix field (originally: spacing between cut panels) that the team **repurposed to write the project/site name** — confirmed with real data (395/500 recent orders have it filled with text like "RECLAMO 931", "COUNTRY GOLF"). Fragile: it only works because staff keep using this convention informally, not because it's a designed field. |

126 columns, 10,685 rows. **No dollar-amount column of its own** — for the
78% of orders with no linked quote, there is no way to know the order's $
value from `PEDIDO1` alone (only m²).

**Known data-quality gap**: 41,667 pieces in `CAJAS` belong to orders whose
`PEDIDO1.PROCESO` already says `TERMINADO`, and 9,215 more to `ENTREGADO`,
but the pieces' own process flags were never fully marked — see the "backlog
zombie" finding in Part 4 below.

### `PEDIDO2` — Order lines, non-DVH family (fixed/catalog measurements)

| Field | Meaning |
|---|---|
| `V_FACTUR` (FK → `PEDIDO1.TV_FACTU`) | Confirmed exact join (Metrix report 179) |
| `V_CODART`, `LARGO`, `ANCHO`, `V_CANTI` | Article and dimensions |
| `GRUPO` | **The field the team already uses to classify the order** (DVH / DIST / LAM / TEMPLUX / PDV / VIDRIO SOLO / FASON / etc.) — confirmed against 10 manually-validated real orders, exact match on all. Primary source for order classification; falls back to reading `CAJAS`'s process flags only when `GRUPO` is blank (mainly in-house Lamilux production, which doesn't go through the sales/classification circuit). A single order can have multiple `PEDIDO2` lines with different `GRUPO` values — resolved by priority (DVH/PDV first), not alphabetically. |
| `ART1`, `ART2`, `ART3` | For DVH/PDV orders: the two real glass materials (`ART1`/`ART3`) and the air-gap spacer (`ART2`, family `CAMARAS`). For `GRUPO=LAM`: `ART2` (family `MP LAMINAS`) gives the real interlayer material (PVB/PVB1.52/SGP/IPL/EVA) — `CAJAS.NOMCLASE` just says "LAM" with no detail. |

### `PEDIDO3` — Order lines, DVH family (piece-level, mirrors `DETPRES2`)

| Field | Meaning |
|---|---|
| `V_FACTUR` (FK → `PEDIDO1.TV_FACTU`) | Confirmed exact join (Metrix report 129) |
| `V_CODART`, `LARGO`, `ANCHO`, `V_CANTI`, `V_CANTIALT` | Article, dimensions, quantity (m²), real piece count |
| `CLASE` | Piece class (e.g. `"PDV DVH"`) — the real field used to detect PDV pieces (see Glossary) |
| `CIRCULAR`, `L_LADOS`, `A_LADOS`, `REQ_PUL`, `ART_PUL`, `PRECIO_PUL`, `L_LADOS_PUL`, `A_LADOS_PUL`, `DONE_PUL`, `FECHA_PUL` | Per-side polishing parameters |

**Orders in `ESPERA` (not yet cut) have no rows in `CAJAS`** (confirmed: 100%
of recent `ESPERA` orders have zero `CAJAS` pieces) — `PEDIDO2`/`PEDIDO3`
carry the same level of detail (class, notes, dimensions, quantity) for
these, and are used as a fallback data source before pieces exist.

### `CAJAS` — Individual glass pieces (the most important table)

The piece-tracking table — one row per physical piece of glass moving
through the factory. ~472,000–492,000 rows (grows continuously).

| Field | Meaning |
|---|---|
| `NUMERO` (PK) | **Confirmed by the user**: a single, factory-wide, ever-increasing piece ID — not reset per order. If the last piece loaded was 400,000 and a new 10-piece order comes in, those pieces are 400,001–400,010. This is the real unique identifier for a physical piece anywhere in the plant. |
| `NUMERO_REL` / `NUMERO_REL_AUX` | Linked/related piece (e.g. a DVH pairing) |
| `PEDIDO` (FK → `PEDIDO1.TV_FACTU`) | Orphan rate: 0.01%. About 7,700 pieces have `PEDIDO=0` (no real order attached — likely raw stock or orphaned pieces; excluded from dashboards) |
| `NUMOC` | Client PO, free text — prefer `PEDIDO1.OCOMPRA` as the cleaner source (doesn't always match) |
| `V_CODART` (FK → `ARTICULO.CODIGO`) | Orphan rate: 0.11% |
| `LARGO`, `ANCHO` | Dimensions in mm |
| `ENTRECALLES` | Cutting margin/spacing between panels on the glass sheet — a cutting-technical value, exact formula/usage not fully documented |
| `NOTAS` | Piece type/item/observation free text |
| `NOMCLASE` | Piece class name (e.g. `"PDV DVH"`, `"LAM PR PDV"`, `"DVH SELL EST"` — the last one links DVH + structural sealing explicitly). **This is the real field used to detect the PDV class — not a process flag.** |
| `DESTINO` | Piece status; value seen: `'ANULADA'` (cancelled) |
| `OPTIMIZACION` | Cutting-optimization plan the piece belongs to (`-1`/`0`/positive values seen) |
| `FACTOR` (on `ARTICULO`, used with `CAJAS`) | Surface multiplier used in Metrix's real m²/ml formula: `m2 = LARGO*ANCHO*0.000001*FACTOR` (or `*1` if `FACTOR=0`); `ml = ((LARGO*2)+(ANCHO*2))*0.001*FACTOR` |
| `V_CANTI` | Quantity, used in DVH context |
| `INGRESO` / `EGRESO` | System entry date / real dispatch date. `EGRESO` coverage: 24.6% historically |
| `NUMPAQUETE`, `NUMPAQUETELUX` | Stock package number / Lamilux package number |
| `LAMILUX`, `MARCA` | Flags used to filter pieces in the Lamilux circuit (`LAMILUX=1 AND MARCA=1`) |
| `LUX_MOTIVOROTURA` / `LUX_SECTORROTURA` / `LUX_ROTURA` | Breakage tracking — only 581 pieces (0.12%), almost entirely scoped to the Lamilux/Autoclave circuit. Real reasons: "ROTO DENTRO DEL HORNO" (377), "DEFECTO DE LAMINACIÓN" (36) |
| `NOMUSU` | **Careful — despite the name, this is NOT an operator.** It's the client's business name. A future reader could easily misuse this as "who worked the piece." |

167 columns total — each process contributes 7 columns (see the process-flag
table below).

### `ARTICULO` — Product/glass catalog

| Field | Meaning |
|---|---|
| `CODIGO` (PK) | |
| `DESCRIPCION` | |
| `FAMILIA` (FK → `FAMILIAS.FAMILIA`) | Orphan rate: 0.00%. Values seen: `'XDVH'`, `'XEVA'`, `'MP LAMINAS'` (raw-material interlayer sheets) |
| `ART_PUL`, `L_LADOS_PUL`, `A_LADOS_PUL` | Polishing-length calculation parameters |
| `COSTO` | **Exists but does NOT represent a usable cost.** Only 240 of 3,849 articles (6%) have `COSTO > 0`, and all 240 share the exact same value, `1.0000` — a loading placeholder, not a real cost. (Correction, 2026-07-08, to an earlier assumption that this enabled margin analysis — it does not, until the user explains the pattern further.) |
| `ESPESOR` | Thickness — relevant to why tempering is a bottleneck (the furnace batches by thickness) |

3,849 rows.

### `FAMILIAS` — Product families (catalog)

| Field | Meaning |
|---|---|
| `FAMILIA` (PK) | |
| `TEMP`, `CORTE`, `POL`, `MEC`, etc. ("recipe"-looking flags) | **These are NOT a strict per-piece recipe** — important nuance. Real cross-check: `FAMILIAS.TEMP=1` pieces split across `CAJAS.TP='*'` (not applicable, 333,765), `CAJAS.TP='X'` (done, 92,591), and `CAJAS.TP=''` (pending, 19,502). Conclusion: `FAMILIAS.TEMP=1` means the family *can* require tempering, not that a given piece does. **For real per-piece routing, use `CAJAS`'s own process flags directly** (or `CLASES`, below). |
| `MEDIDAS`, `PERIMETRO` | 'SI'/blank flags, used as a real filter in Metrix's original quote-detail report (excludes these families from `DETPRES` line totals) |

### `CLASES` — The real process "recipe" (confirmed)

Discovered separately from `FAMILIAS`, and is the table that actually drives
process routing.

| Field | Meaning |
|---|---|
| `CLASE` | Class name (e.g. `'DVH'`, `'DVH SELL EST'`, `'DIST'`, `'FLOAT PR MEC TEMP'`, `'FLOAT PR TEMP'`, `'FASON1'`...`'FASON12'`, `'PDV1'`...`'PDV4'` — 80+ classes) |
| One `tinyint` (0/1) column per process | `CT`, `BD`, `TP`, `LM`, `DV`, `MF`, `HJ`, `MEC`, `SER`, `HER`, `PEG` |

Confirmed with real data: `'FLOAT PR MEC TEMP'` has `CT=1, BD=1, TP=1, MEC=1`;
`'FLOAT PR TEMP'` has `CT=1, BD=1, TP=1, MEC=0` — matches the class name
exactly.

### `LISTA` — Price list, per article, split by process (confirmed)

| Field | Meaning |
|---|---|
| `FAMILIA`, `CODIGO`, `DESCRIPCION` | |
| `PRECIO` (raw/base), `PRECIOCORTE`, `PRECIODVH`, `PRECIOTEMP` | Four different prices per article |
| `COMPONENTES` | Free text, seen empty in the sample |

357 rows ("older backup" version). Example (`FL10IN`, quote 9947):
`PRECIO=$34,111.20`, `PRECIOCORTE=$38,984.02`, `PRECIODVH=$38,984.02`,
`PRECIOTEMP=$66,639.77` (1.95× the base price).

### `PRECIOS` — Price list, primary source for backlog valuation

| Field | Meaning |
|---|---|
| `S_CODART`, `CATEGORI` (`DISTRIBUCION`/`CORTE`/`DVH`/`TEMPLADO`), `S_PRECIO`, `S_FEPRECIO` (Clarion date), `FAMILIA`, `DENOMINACION` | |

910 rows, the "newer / better coverage" price table. Example (`FL10IN`, "FLOAT
INCOLORO 10mm"): `DISTRIBUCION=35,815.02`, `CORTE=40,933.22`, `DVH=40,933.22`,
`TEMPLADO=69,971.76`. Coverage: `DISTRIBUCION` 48%, others 75–92% — but only
of 357–910 articles out of 3,849 total in `ARTICULO`. **Any valuation built
on this is a floor, not the real total** — most low-rotation/discontinued
codes have no price in either table. Exact relationship between `LISTA` and
`PRECIOS` (historical-by-date? different channel?) not confirmed.

### `NUMEROS` — Manual numbering counter (investigated, inconclusive)

`FACTURA` (decimal), `TIPO` (10 real values: `A`,`B`,`D`,`H`,`T`,`U`,`V`,`W`,`X`,`Y`,
each with one row — `A`/`B` likely Argentine invoice types). **None suggest
"quote"** — the earlier hypothesis that this governs `PRESUP.NUMERO` is
considered unconfirmed and probably wrong.

### Other tables (present, lower detail)

| Table | Purpose |
|---|---|
| `DETPRESCONS` | Consumables on a quote (silicone, gaskets, profiles — sold by m²/linear-meter/weight, not glass). 11,853 rows, actively used. |
| `DETPRESINS` | Installation service on a quote. 2,094 rows, actively used. `V_CANTI` vs `V_CANTI_REAL` = budgeted vs. actual. |
| `DETPRES3` / `DETPRES4` | **No real usage** — 0 rows each. Safe to ignore. |
| `PARAME` | General parameters table. `MARCA` flag used as a filter in several reports — exact meaning **not confirmed, low confidence**. Don't invent its meaning. |
| `SALVALE` | Likely "vales de salida" (dispatch/delivery notes) — structure not fully extracted, out of the current focus (pieces/orders/quotes). |
| `AJSTOCK1`/`2`/`3` | Manual stock adjustments — header (type/status/date), non-dimensioned detail (consumables, counted by quantity), dimensioned detail (sheets/glass, adds `LARGO`/`ANCHO`). If `AJSTOCK1.TIPO <> 'ENTRADA'`, the quantity subtracts instead of adding. |
| `RENTRADA` / `DETENT` / `DETENT2` | Supplier goods-receipt notes — header, non-dimensioned detail, dimensioned detail. |
| `FECHAS` | System parameter: `ALTADESDE` = the date Metrix started tracking package-level stock (~2025-07-08); `SUCURSAL` = branch filter column. |
| `SUCURSAL` | Warehouse/bay catalog (`NUMERO`, `NOMBRE`) — resolves a stock package's location from its latest goods-receipt note. |
| `DETPRESINS_AUX`, `DETPRAUX` | Found while listing the database's 144 total tables, not investigated further. |

---

## Part 3 — `CAJAS` process-flag columns

Each process contributes **7 columns**: `<P>` (flag), `<P>_FEC` (date),
`<P>_HORA` (time, coded in blocks of 10 — decode as
`TIME '00:00:00' + to_milliseconds((hora-1)*10)`), `<P>_ERR` (rework/error
counter), `<P>_FEC_ERR`, `<P>_HORA_ERR`, `<P>_OBS_ERR` (free-text error note).

**Flag values**: `'*'` = process **not applicable** to this piece (excluded
from routing); `'X'` = process **done**; `''` (blank) = process **pending**.

19 possible process columns exist; 14 have real, meaningful volume.

| Flag | Process (Spanish) | Process (English) | Confidence / usage | Pieces with an error |
|---|---|---|---|---|
| `CT` | Corte monolítico | Monolithic cutting | High (99.7% satisfy `CT_FEC<=TP_FEC`) | 285 |
| `SER` | Corte laminado | Laminated cutting | High (alternative to `CT` depending on glass type) | 120 |
| `BD` | Pulido recto / bordes | Straight-edge polishing | High (99.0% satisfy `BD_FEC<=TP_FEC`) | 576 |
| `MF` | Pulido matado de filo | Chamfered-edge polishing | Medium | 1,337 (2nd highest absolute) |
| `MEC` | Mecanizado (perforado/entalles) | Machining/drilling/notching | High (99.5% satisfy `CT_FEC<=MEC_FEC`, 98.8% `MEC_FEC<=TP_FEC`) | 300 (worst relative rate: 3.11%) |
| `TP` | Templado | Tempering | High — the most critical process (thermal shock) | 875 (highest among high-volume processes) |
| `HJ` | Parejas (emparejado para DVH) | Pairing/matching for IGU | Medium | 746 |
| `DV` | DVH (armado) | IGU assembly | High (100% satisfy `TP_FEC<=DV_FEC` and `DV_FEC<=LT_FEC`) | 1,508 (**highest of all processes**) |
| `HER` | Sellado estructural | Structural sealing | Low usage (1,429 pieces marked done). Confirmed via Metrix's own report #198 ("Proceso de Sellado Estructural"), which literally uses `CAJAS.HER='X'`. **Not "PDV"** — see Glossary. | 12 |
| `PEG` | Pegado a bastidor | Frame gluing/mounting | Low-medium usage (12,859 pieces) | 93 |
| `LM` | Laminado EVA | EVA laminating | Medium (3,906 pieces) | 198 |
| `LUX` | Lamilux | Sale of an uncut, autoclaved glass sheet to another glass processor (confirmed by the user) | High (name confirmed). No meaningfully-used own date field — `AUT_FEC` is the real milestone | N/A |
| `AUT` | Autoclave | Autoclave (pressure lamination) | High (17,219 pieces, name confirmed) | — |
| `LT` | Despacho / entrega | Dispatch / delivery | High (100% satisfy being the last step) | 803 |
| `MD` | *(name not confirmed)* | — | **No real usage** (0% of pieces) — likely legacy | 0 |
| `OT` | *(name not confirmed)* | — | **No real usage** (~0%) — likely legacy | — |
| `FINAL` | *(name not confirmed)* | — | **No real usage** (~0%) — likely legacy | — |
| `CAR` | Cargada (en camión/despacho) | Loaded for shipping | Minimal usage — seen in the Lamilux/Autoclave circuit: `AUT='X' AND CAR='X'` = "autoclaved, loaded" | — |
| `RES` | Reservada | Reserved | Minimal usage — `AUT='X' AND RES='X'` = "autoclaved, reserved" | — |

**Confirmed subtleties**:
- Process order was validated empirically against real data — every
  consecutive pair's `fecha_anterior <= fecha_siguiente` check passed
  98.8–100% of the time.
- The 14 real processes group into 9 stages for lifecycle analysis: 1) Corte
  (`ct`/`ser`), 2) Pulido (`bd`/`mf`), 3) Mecanizado (`mec`), 4) Templado
  (`tp`), 5) Parejas (`hj`), 6) DVH (`dv`), 7) Sellado (`her`/`peg`), 8)
  Laminado/Autoclave (`lm`/`lux`/`aut`), 9) Despacho (`lt`).
- For **tempered** glass, straight-edge polishing is already included in the
  tempering price — `PR_PRETO=0` on tempered pieces even when the class name
  says "FLOAT PR MEC TEMP" (confirmed on a real case). For laminated or raw
  float glass, it's billed separately.
- `CAJAS.DESTINO='ANULADA'` marks a cancelled/rejected piece (22,471 pieces,
  4.7%) but has no date of its own — you can't know *when* it happened.
- There's no universal "breakage" flag — the most reliable signal is
  `<PROC>_ERR>0` at any stage the piece passed through (4,986 pieces, 1.05%
  of the total, have at least one error).

---

## Part 4 — Views catalog

These hand-written SQL views (`salida/*.sql`) sit on top of the raw tables
and are what Power BI and the dashboards actually query — prefer these over
querying raw tables directly when building a new report.

### Base (`salida/vistas_informes_negocio.sql`)

| View | Purpose | Source tables |
|---|---|---|
| macro `fecha_clarion(dias)` | Converts a Clarion-style integer (days since 1800-12-28) to a real `DATE`; `0` → `NULL` | — |
| `vista_detalle_presupuesto` | Quote line items (free-measure + DVH/EVA unified), own `id` for OData | `PRESUP`, `DETPRES`, `DETPRES2` |
| `vista_presupuesto_a_pedido` | Quote→order link, only the ~22% with `PRESUP_REL<>0` | `PRESUP`, `PEDIDO1` |
| `vista_historial_cliente` | Every order for a client, with key dates and m² | `CLIENTES`, `PEDIDO1` |
| `vista_totales_cliente` | Client ranking by accumulated orders/m² | derived from `vista_historial_cliente` |
| `vista_cola_piezas` | Piece production queue (analytical/15-min version) | `CAJAS`, `PEDIDO1` |

### Per-process (`salida/vistas_procesos_metrix.sql`) — translated from Metrix reports 189–199

Each process has a detail view (one row per completed piece) and a `_totales`
view (aggregated by article/destination). m²/ml formula:
`m2=LARGO*ANCHO*0.000001*FACTOR`, `ml=((LARGO*2)+(ANCHO*2))*0.001*FACTOR`.

| View pair | Metrix report | Filter |
|---|---|---|
| `vista_proceso_corte_monolitico[_totales]` | 189 | `CT='X'` |
| `vista_proceso_corte_laminado[_totales]` | 190 | `SER='X' AND LAMILUX<>1` |
| `vista_proceso_pulido_recto[_totales]` | 191 | `BD='X'` |
| `vista_proceso_pulido_matado_filo[_totales]` | 192 | `MF='X'` |
| `vista_proceso_mecanizado[_totales]` | 193 | `MEC='X'` |
| `vista_proceso_templado[_totales]` | 194 | `TP='X'` |
| `vista_proceso_parejas[_totales]` | 195 | `HJ='X'` |
| `vista_proceso_dvh[_totales]` | 196 | `DV='X'` |
| `vista_proceso_laminado_eva[_totales]` | 197 | `LM='X'` |
| `vista_proceso_sellado_estructural[_totales]` | 198 | `HER='X'` |
| `vista_proceso_pegado_bastidor[_totales]` | 199 | `PEG='X'` |

### Stock (`salida/vistas_stock_lamilux_autoclave.sql`) — Metrix reports 224–229, 234–235

| View | Metrix report | Purpose |
|---|---|---|
| `vista_stock_paquetes` | 224 | Non-dimensioned stock, recomputed from `FECHAS.ALTADESDE` forward |
| `vista_stock_paquetes_laminas` | 226 | Same, for dimensioned sheets/glass |
| `vista_stock_paquetes_insumos` | 227 | Same as above, plus `ubicacion` (warehouse bay) |
| `vista_stock_lamilux_material` | 225 | Lamilux pieces by autoclave-circuit status |
| `vista_stock_lamilux_paquete` | 228 | Autoclaved pieces grouped by Lamilux package |
| `vista_stock_lamilux_pieza` | 229 | Same breakdown, piece-level |
| `vista_proceso_lamilux[_totales]` | 234 | Completed Lamilux pieces |
| `vista_proceso_autoclave[_totales]` | 235 | Completed Autoclave pieces |

### Metrics (`salida/vistas_metricas.sql`)

| View | Purpose |
|---|---|
| `vista_wip_por_proceso` | WIP and volume (done/pending/N-A) per process |
| `vista_calidad_por_proceso` | Error % per process |
| `vista_cumplimiento_entregas` | On-time/late delivery status per order (fixed 2026-07-08 to add a "no commitment date" bucket so it doesn't distort the late %) |
| `vista_backlog` | Active, undelivered orders |

### Quote-to-order reconciliation (`salida/vistas_conciliacion_presupuestos.sql`, added 2026-08-12)

Built for the commercial area: finds production orders whose quote should be
marked `ACEPTADO` in Metrix but isn't (see open question #8 above — the ~78%
of orders with no formally linked quote). Read-only, like everything else —
these are review lists for a human to correct by hand in Metrix, not an
auto-fixer.

| View | Purpose |
|---|---|
| `vista_conciliacion_directa` | Orders with `PRESUP_REL` already set whose linked quote's `ESTADO_PRES <> 'ACEPTADO'`. Unambiguous, high confidence (154 rows as of 2026-08-12). |
| `vista_conciliacion_candidatos` | For orders with no `PRESUP_REL` (the ~78%): candidate quotes for the same client, scored 0–100 (obra/site-name similarity via `jaro_winkler_similarity` on `PEDIDO1.ENTRECALLES` vs `PRESUP.OBRA` 40pts, m² similarity 30pts, piece-count similarity 15pts, date proximity 15pts), top 3 per order, min score 40. **~77% of unlinked orders come from the `INTERFAZ` bulk-import user** (`pedido_usuario` column) — for those, no linked quote is often structural (never went through Metrix's quote flow), not an oversight; deprioritize those when reviewing. Score ≥70 is reasonably trustworthy; below that, check the individual similarity columns before trusting it — small orders (1–2 pieces) can coincidentally score well on size alone. |

### Lifecycle model / "gold" layer (`salida/vistas_gold_ciclo_vida.sql`)

| View | Purpose |
|---|---|
| `gold_dim_proceso` | The 14 real stages, grouped into 9 |
| `gold_fact_eventos_pieza[_crudo]` | One row per (piece, applicable stage) — approximate timeline (a stage's "entry" = previous stage's exit, or `INGRESO`) |
| `gold_fact_pieza_estado` | Current state per piece: PENDIENTE / EN PROCESO / TERMINADA / DESPACHADA / ANULADA, plus days in current stage |
| `gold_dim_cliente`, `gold_dim_presupuesto`, `gold_dim_pedido`, `gold_dim_operario` | Cleaned dimension tables |

**Important limitation to keep in mind**: there is no historical event table
in Metrix — only a single timestamp per flag on `CAJAS`. This "gold" layer is
an approximation built on top of that, not a true event log.

### Executive KPIs (`salida/vistas_kpi_ejecutivos.sql`) — current, authoritative version

All scoped to a rolling 90 days (by explicit user request, 2026-07-08), except
`kpi_backlog_zombie_piezas` which deliberately looks further back.

| View | Purpose |
|---|---|
| `kpi_wip_genuino` | Real WIP (pieces actively moving, ≤90 days) per stage |
| `kpi_backlog_zombie_piezas` | Pieces with no movement in >90 days / >1 year — a data-quality finding, not a routine KPI |
| `kpi_pedidos_en_riesgo` | Active orders due in -14 to +7 days, flags whether dispatch already scheduled |
| `kpi_backlog_critico` | Active orders >60 days late |
| `kpi_puntualidad_metrix` | On-time % using `PEDIDO1.LT_FEC` (secondary number now) |
| `kpi_puntualidad_real` | On-time % using the logistics spreadsheet's dispatch date — **the real, headline number**, since `LT_FEC` only covers 34% of orders actually dispatched |
| `kpi_retrabajo_por_etapa` | Error % per stage, last 90 days |
| `kpi_conversion_presupuesto` | % of quotes (last 90 days) that became an order |
| `kpi_ranking_clientes` | Client ranking by m², last 90 days |
| `kpi_carga_logistica_futura` | Upcoming scheduled dispatches from the logistics spreadsheet |

This set additionally depends on `logistica_despachos` — **not one of the SQL
Server tables**, but an external source: the hand-maintained
`Programacion Logistica 2026.xlsx` spreadsheet, loaded by
`negocio/cargar_logistica.py`. It exists because Metrix's own `LT_FEC` field
only covers 34% of orders the logistics team confirms as actually dispatched.

### Valuation (`salida/vistas_valorizacion.sql`)

| View/macro | Purpose |
|---|---|
| macro `categoria_precio(tipo)` | Maps an order's `TIPO` to a `PRECIOS` price category |
| `precio_vigente` | Most recent price per article+category |
| `kpi_valor_backlog` | Estimated $ value of the active backlog — a **floor**, not the real total (only covers articles with a price found) |

### Quote detail (`salida/vista_informe_presupuestos_2.sql`)

`vista_informe_presupuestos_2` — a faithful translation of Metrix's own
"Informe Presupuestos 2" report (id 222). Metrix keeps adding columns to
this report; the view follows it (diff old vs new `SCRIPTS.TPS`/`COLUMNAS.TPS`):
`ingreso` (`PRESUP.USUARIO`, added 2026-08-13), `clase` (line class,
`DETPRES.CLASE`/`DETPRES2.CLASE`) and `tipo` (`PRESUP.TIPOPRESUP`, e.g.
"PRESUPUESTO NORMAL"/"OPCION A OTRO PRESUPUESTO"; NULL on old quotes) —
both added 2026-10-15 from the `TPS3/` copy.

### Spacer-bending machine / BYTE (`salida/vista_byte_piezas_dvh.sql`, added 2026-09-29)

Feeds the CSV for the spacer-bar bending machine (*dobladora de varillas*),
generated by `negocio/exportar_dobladora.py <pedido>` (replaces an older
program whose code isn't available; format reproduced 1:1 against a real CSV
it produced, see the SQL file header). BYTE = the CSV's "Sealant Depth": how
much the spacer is shrunk vs. the glass size, later filled with silicone.

| View | Purpose |
|---|---|
| `vista_byte_piezas_dvh` | One row per DVH piece (`CAJAS`, family `XDVH`, same source as Metrix report 216 "Piezas (DVH / EVA / LAM)"): composition split from `DESTINO` (`vidrio1`/`camara`/`vidrio2`), `camara_mm`, `byte` + `motivo_byte`, `escalonado`. |
| `vista_dobladora_items` | One row per item (= one CSV row): piece count, total spacer length (glass perimeter × count, in m), byte. |

BYTE rule (confirmed with the user 2026-09-28, first match wins):
**7.0** if `NOMCLASE` starts with `PDV` (even with KNT) → **6.0** if glass 1 or
2 is a KNT article (`ARTICULO.DESCRIPCION LIKE '%KNT%'` — *not* the `CK`
code prefix: `CK6K6`/`CK8K4` are Cool Lite KS) → **6.5** otherwise, including
class `DVH SELL EST` (used only so the glass can be "declared" in both the DVH
and PDV areas; not structural glazing). `PEDIDO2.GRUPO='PDV'` is not a usable
signal (7 orders ever, last one 2026-03).

### Repositions / breakage follow-up (`salida/vistas_reposiciones.sql`, added 2026-09-29)

Source: SQL Server `DEVENG1` (one row per reposition) + `DEVENG2` (glass to
replace), extracted since 2026-09-29 — found via Metrix reports 212/218/220.
`DEVENG1.NOTAS` = `'PIEZA <n>: <free text>'` where `<n>` is the broken piece
in `CAJAS`; the reposition **reuses that same `CAJAS` piece** (its process
flags are reset and it goes through production again). `CORTADO` = re-cut
date, `TERMINADO` = tempering date, `FINALIZADA=1` = closed (no close date is
stored). `REVISADA='-'` = discarded (excluded, like Metrix does). `ESTADO`,
`PEDIDOREP`, `PEDIDO1.REPOSICION` are unused.

| View | Purpose |
|---|---|
| `vista_reposiciones` | All repositions, one row each: piece, item, motive/sector, `tipo_dvh` (`DVH armado` / `Hoja de DVH` / `No DVH`), the item's DVH count vs. assembled, current `etapa`, `dias_abierta`. Validated 2026-09-29 against Metrix report 218's own SQL: identical row count and m² for last month (143) and last year (2,241). |
| `vista_reposiciones_dvh` | DVH-related only. **Most are a single sheet of a DVH, not the assembled DVH** (~1,300 vs ~190 in the last year) — matched to the item via `PEDIDO`+`NOTAS`+`LARGO`+`ANCHO`. Metrix's summary reports 146/174/176 exclude `XDVH` and miss these entirely. |
| `vista_reposiciones_dvh_mensual` | Monthly count/m²/open/avg days-to-recut per type, sector and motive (for Power BI). |

---

## Part 5 — Data-quality findings (read before building a new report on this data)

1. **"Backlog zombie" — the largest data-quality finding of this project.**
   Counting "in process" pieces with no recency filter gives 123,421 pieces
   averaging 700–1,100 days in their current stage (impossible for genuine
   work). Cause: 41,667 pieces belong to orders already marked `TERMINADO`
   and 9,215 more to `ENTREGADO` at header level, but their individual flags
   were never finished; the remaining 72,339 are "active" orders with no
   recent movement. In total, 109,007 pieces (176,603 m²) with no movement
   in >90 days, of which 79,262 (124,899 m²) haven't moved in over a year.
   **Any WIP/bottleneck/at-risk metric that doesn't filter by recency will be
   badly distorted.** `kpi_wip_genuino` is the fix (≤90-day movement, ≤90-day
   order).
2. **Fixed bug**: `vista_cumplimiento_entregas` used to compare
   `lt_fec > tv_fevenc` without excluding `tv_fevenc=0` — since 0 sorts
   before any real date, every order with no commitment date fell into "late"
   with an absurd `dias_atraso` (~82,000). Before the fix: 989 "late" vs. 98
   "on time" (9%). After filtering to orders with a real date: 98 on time /
   336 late = **22.6% on time**, average delay 10.3 days (max 57). Still low,
   but now the real number, not an artifact.
3. **Corrupt commitment dates (minor)**: 58 of 9,065 orders (0.6%) have a
   commitment date before the order date (impossible) — explicitly filtered
   out (`fecha_compromiso >= fecha_pedido`) in `kpi_pedidos_en_riesgo` and
   `kpi_backlog_critico`.
4. **No operator or machine tracking exists at piece/stage level.** An
   exhaustive table search (`%maquina%`/`%equipo%`/`%operario%`/etc.) found
   nothing. `CAJAS.NOMUSU` is **not** an operator despite the name (it's the
   client). The only clean field is `PEDIDO1.NOMUSUPROD`, but at whole-order
   level only.
5. **Breakage/rejection signal is fragmented, no single source.**
   `<PROC>_ERR`+`<PROC>_OBS_ERR` is the best source (4,986 pieces, 1.05%).
   `CAJAS.DESTINO='ANULADA'` (22,471 pieces, 4.7%) has no date. Lamilux-
   specific breakage fields cover only 581 pieces. `PEDIDO1.ANULA_FEC`/`MOTIVO`
   is clean but order-level (501 cases).
6. **`ARTICULO.COSTO` does not support margin analysis** — see Part 2. Any
   margin/profitability metric should be treated as not currently supportable.
7. **`<PROC>_FEC_PLAN` (planned dates) too sparse for a KPI** — 0–5.2%
   coverage of orders.
8. **Quote→order link covers only ~22% of orders** — see `PEDIDO1.PRESUP_REL`
   above. Open business question, not fully resolved.
9. **`PEDIDO1` has no $ amount of its own** — order-value ranking only works
   for the ~22% with a linked quote; the rest only have m².
10. **`FAMILIAS` is not a process recipe** — use `CLASES` (confirmed) or
    `CAJAS`'s own flags for real routing.
11. **`CALCULA_GRILLAQV` stored procedure could never be inspected** — the
    `db_datareader` role doesn't include `VIEW DEFINITION`. Not blocking (a
    separate state machine was built and validated against real data
    instead), but its server-side logic remains unknown.
12. **`$ value of the backlog is a floor, not the real total`** — `PRECIOS`/
    `LISTA` only cover 357–910 of 3,849 articles.
13. **The team's own spreadsheet ("Tablero Programación 2026.xlsx") "Estado"
    column does not mirror any Metrix field** — it's manual staff judgment,
    sometimes ahead of Metrix, sometimes contradicting it. Don't automate it
    without more context. Its cell colors are also hand-painted, not
    conditional formatting — no inferable meaning from the file structure.
14. **`% PDV` in the team's spreadsheet was mislabeled** (fixed 2026-07-10):
    it actually measures structural sealing (`HER`), not PDV. PDV is a piece
    *class* (`NOMCLASE`/`PEDIDO3.CLASE`), not a process flag. Renamed to
    `% SELLADO` in `negocio/tablero_comun.py`, with real PDV detection added
    by class instead.

### Open business questions (not technical — need a human answer)

- Why ~78% of orders have no formally linked quote.
- The exact reason `PRESUP.ESTADO` (unused) exists alongside `ESTADO_PRES`
  (used) — it's clear which to use, just not *why* the unused one exists.
- The real mechanism behind `PRESUP.NUMERO` assignment.
- Whether `ARTICULO.COSTO` will ever be populated with real costs (margin
  analysis is blocked on this).
- Whether a bulk cleanup of the "backlog zombie" (109,007 pieces / ~2,443
  orders >60 days late) is worth doing — a business call, not a technical one.
- Whether operator/machine-level productivity could ever be tracked manually,
  since Metrix has no such data today.
- Why individual piece flags don't get updated when an order is closed at
  header level — unclear if this is a skipped operational step or an
  undetected bulk-close mechanism.
- The exact relationship between `LISTA` and `PRECIOS` (historical-by-date,
  or a different sales channel?).

### A commercial note worth handling carefully

The largest client represents about 4× the volume of the next-largest
client (388 orders / 50,720 m² vs. 12,949 m² for #2) — real client
concentration, useful for risk conversations but sensitive to share widely.
Dispatch (not production) is where the most pieces are queued (7,793) —
suggests a logistics bottleneck more than a production one.
