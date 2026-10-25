# Runbook — "it broke, what do I do"

Written for someone who is not comfortable in a terminal. Every step here
either involves double-clicking a file, opening a web browser, or using
Windows' built-in PowerShell in a very mechanical, copy-paste way. This is
Windows — there is no Linux/bash anywhere in this project.

If you get stuck at any step, stop and ask for help rather than guessing —
this project talks to a live production system (Metrix / SQL Server), and
`../CLAUDE.md` explains why caution matters more than speed here.

## 1. Is the system up? (do this first, always)

Open a web browser and go to:

```
http://localhost:8080/salud
```

- If you see something like `{"estado":"ok","tablas":92,"ultima_carga":"...Z"}`
  — the `.tps`/OData pipeline is alive. Check the `ultima_carga` (last load)
  timestamp: if it's more than an hour old, see **Problem 2** below.
- If the page doesn't load at all ("can't reach this site") — go to
  **Problem 1** below.

To check the two dashboards:

```
http://localhost:8501   (Tablero Programación — piece-level board)
http://localhost:8502   (Panorama gerencial — management dashboard)
```

If either doesn't load, see **Problem 3**.

### Checking from another computer on the office network

Same idea, but use this PC's network address instead of `localhost`:

```
http://192.168.130.158:8080/salud
```

**Note**: that address can change if the router reassigns it. If it stops
working for coworkers specifically (but works fine on this PC via
`localhost`), that's the most likely reason — see `salida/acceso_red_local.md`
for how to find the current address and update it.

## 2. Where everything lives

| I want to know... | Look here |
|---|---|
| Is the pipeline healthy right now? | `http://localhost:8080/salud` (see above) |
| Did the last `.tps` refresh match row counts? | `salida/reporte_validacion.md` |
| Did the last business-data refresh match row counts? | `salida/reporte_validacion_negocio.md` |
| Is the pipeline running fast enough, or falling behind? | `salida/reporte_rendimiento_pipeline.md` (self-updating, based on real timing, not guesses) |
| What did the service actually do/log recently? | `logs/servicio.log` (`.tps` side), `logs/negocio_servicio.log` (business side) |
| Detailed step-by-step log of one script | `logs/<nombre_del_script>.log` — every script writes its own file, named after itself (e.g. `logs/refrescar.log`, `logs/negocio_ciclo_analitico.log`) |

## 3. Prender / Apagar / Reiniciar (start / stop / restart)

Three double-click shortcuts in the project's root folder:

| File | What it does |
|---|---|
| `Iniciar_Metrix.bat` | Starts the services if they're stopped |
| `Detener_Metrix.bat` | Stops all three services |
| `Reiniciar_Metrix.bat` | Stops then starts everything — **the fix for most "seems stuck" problems** |

These control the three Windows Scheduled Tasks that keep everything running:
`Metrix_ServicioOData` (the `.tps` pipeline + API), `Metrix_NegocioServicio`
(SQL Server business data), and `Metrix_TableroVivo` (the port-8501
dashboard). All three are also set to start automatically every time someone
logs into this Windows account — you shouldn't need to start them by hand on
a normal day.

**The management dashboard (port 8502) is not in this list yet** — see
Problem 3 below for how to start it manually, and `../CLAUDE.md` for why it
isn't automatic yet.

## 4. Common problems and fixes

### Problem 1 — `http://localhost:8080/salud` won't load at all

1. Double-click `Iniciar_Metrix.bat`, wait about 10 seconds, try the page
   again.
2. Still nothing? Double-click `Reiniciar_Metrix.bat`, wait about 10 seconds,
   try again.
3. Still nothing? Open PowerShell (Start menu → type "PowerShell" → Enter)
   and run:
   ```
   schtasks /query /tn "Metrix_ServicioOData"
   ```
   Look at the "Estado"/"Status" line. If it says something other than
   "Running", something is preventing the task from starting — check
   `logs/servicio.log` (most recent lines) for an error, or ask for help with
   that log's content.

### Problem 2 — the health check works, but `ultima_carga` (last load) is old

This means the process is alive but the refresh cycle stopped actually
completing. **Known issue as of this writing**: the `.tps` pipeline stopped
refreshing on 2026-07-07 despite the service restarting fine many times
since — see `../CLAUDE.md`'s "Other gotchas" section. This affects Metrix's
internal report-metadata tables only, not the real business data.

To check if this is still happening: look at the last lines of
`logs/refrescar.log` — if the last entry is old (days/weeks), the scheduled
refresh job isn't firing even though the process shows as running. A
`Reiniciar_Metrix.bat` is worth trying, but if the underlying scheduler bug
hasn't been fixed yet, it may recur. This needs a code-level look at
`pipeline/servicio.py`'s `BackgroundScheduler` setup — flag it for a session
with more time, it's on the Step 3 refactor list.

For the **business-data side**, check `salida/reporte_validacion_negocio.md`'s
"Fecha" line the same way — if that's stale, the fix is the same
(`Reiniciar_Metrix.bat`, then check `logs/negocio_servicio.log`).

### Problem 3 — a dashboard (8501 or 8502) won't load

**Port 8501** (Tablero Programación) is controlled by the same
`Reiniciar_Metrix.bat` as everything else — try that first.

**Port 8502** (Panorama gerencial) is **not** wired into the automatic
startup yet, so it needs to be started by hand after every PC reboot:
1. Open PowerShell.
2. Run these two commands (they navigate to the project folder and then
   start the dashboard):
   ```
   cd "C:\Users\geronimo.zanon\copia dir metrix"
   _work\venv\Scripts\streamlit.exe run negocio\tablero_gerencial_app.py --server.port 8502
   ```
3. Leave that PowerShell window open (closing it stops the dashboard) and
   open `http://localhost:8502` in a browser.

To make port 8502 start automatically like the others, someone with
Windows administrator rights needs to add a Scheduled Task for it, the same
way the other three were set up (see `Metrix_TableroVivo` in Task Scheduler
as a template) plus a matching Windows Firewall rule if coworkers need to
reach it too (see `salida/acceso_red_local.md` for the firewall-rule pattern
used for the other ports).

### Problem 4 — Power BI says "the URL doesn't point to an OData service" / won't connect

1. Confirm the API itself is healthy (`http://localhost:8080/salud`, see
   step 1) — if that page doesn't load, fix that first (Problem 1).
2. If `/salud` works but Power BI still refuses to connect, try the URL by
   hand in a browser first: `http://localhost:8080/$metadata` should show
   an XML document, not an error. If it errors, note the exact message —
   this endpoint has a history of picky OData-compliance issues (see the
   comments in `pipeline/api.py`), worth flagging to whoever maintains the
   code.
3. Re-open Power BI, `Obtener datos → OData feed → http://localhost:8080/`,
   or just double-click `Conectar_PowerBI.pbids` in the project root, which
   has this pre-filled.
4. Full step-by-step Power BI guide (which view to use for which report):
   `salida/guia_power_bi.md`.

### Problem 5 — a `.tps` file "failed to copy" in the validation report

Usually means the Clarion Metrix application had that file open/locked at
the exact moment the pipeline tried to copy it. This is expected
occasionally and self-heals on the next cycle (every 15 minutes) — no action
needed unless it persists across many consecutive cycles, in which case
check `logs/copiar_tps.log` for the exact file and error.

### Problem 6 — a table's row count doesn't match between source and DuckDB

Check `salida/reporte_validacion.md` (`.tps` side) or
`salida/reporte_validacion_negocio.md` (business side). A **small** mismatch
on the business side is expected and not a bug — Metrix is in live use during
business hours, so someone may load an order in the few seconds between the
extraction and the recount (the report itself explains this). A **large**
or **persistent** mismatch is worth investigating — check the matching log
file (`logs/negocio_ciclo_analitico.log` or `logs/refrescar.log`) for errors
around that time.

### Problem 7 — "database is corrupt" error in a log

Happened at least once (see `../CLAUDE.md`'s gotchas). Because both
pipelines build a new file before ever touching the "live" one (see
`ARCHITECTURE.md`'s "atomic swap" explanation), a corrupt build gets thrown
away automatically and the *next* cycle should just work — no manual fix
needed for a one-off occurrence. If it happens repeatedly, that's a sign of
disk trouble on this PC, worth a hardware check.

### Problem 8 — `TEMPRPT.TPS` still shows as "encrypted, no key" in the validation report

Expected — this file's password was never found. It's a temporary reporting
table, not core business data, so the rest of the system works fine without
it. If someone ever finds the password (ask whoever originally built Metrix,
or its original installer), open `salida/claves_tps.txt` with Notepad and add
a line:
```
TEMPRPT.TPS=the_real_password_here
```
Save the file — the next automatic refresh (within 15 minutes, or run
`Reiniciar_Metrix.bat` to force it sooner) will pick it up on its own. No
code change, no restart of anything else needed.

## 5. Changing how often things refresh

- `.tps` pipeline interval: edit `INTERVALO_MIN` in `pipeline/config.py`
  (default 15 minutes), then `Reiniciar_Metrix.bat`.
- Business-data (analytical) interval: edit `INTERVALO_NEGOCIO_MIN` in
  `negocio/config.py` (default 5 minutes — lowered from 15 on 2026-07-22
  after trimming which columns get pulled; see the comment above that setting
  before changing it, going lower may make cycles overlap and slow down —
  check `salida/reporte_rendimiento_pipeline.md` after any change), then
  `Reiniciar_Metrix.bat`.
- The 1-minute "live lane" (`INTERVALO_VIVO_SEG`) is currently **disabled**
  (see `negocio/servicio.py`) — changing this setting alone won't reactivate
  it, see `ARCHITECTURE.md` for why it was turned off.

## 6. If you need to verify the SQL Server connection is really read-only

Run this from PowerShell (needs the SQL credentials already set up, see
`../CLAUDE.md`'s "Secrets" table):

```
cd "C:\Users\geronimo.zanon\copia dir metrix"
_work\venv\Scripts\python.exe -m negocio.probar_conexion
```

This prints the connected identity and its SQL Server roles — it should show
**only** `db_datareader`, nothing else. It doesn't change anything; it's a
read-only diagnostic, safe to run any time.

## 7. Dobladora de varillas (BASB-2500) — app `SistemaDVH.exe` (added 2026-09-30)

Replaces the old `SistemaDVH.exe` (no source; its logic was reconstructed
from its bytecode — see `app_dobladora/nucleo.py` header). Runs on the DVH
line's PC (Windows 10), not on this one.

- **Daily data file**: `\192.168.130.210\Publico\Produccion\DVH\BASB 2500\_datos_metrix\dobladora_datos.json`,
  written by the business service once a day (first cycle after 06:00 —
  `negocio/exportar_datos_dobladora.py`, hooked in `negocio/servicio.py`).
  DVH orders from the last 60 days with DVH still unassembled + open DVH
  repositions (broken in sector DVH) + KNT article codes. If the share is
  unreachable the cycle is unaffected and it retries next cycle.
  **Regenerate by hand**: `_work\venv\Scripts\python.exe -m negocio.exportar_datos_dobladora`.
- **App**: shows "Datos de Metrix: dd/mm HH:MM" in green (today's file) or
  amber (older). If the file is missing, the operators just use
  "Seleccionar Detalle.CSV" as always — both inputs go through the same logic.
- **Rebuild the .exe** after changing `app_dobladora/`: double-click
  `app_dobladora\construir_exe.bat` → `app_dobladora\dist\SistemaDVH.exe`
  (it runs a self-test at the end; it must print `ok | ...`).
- Sent repositions are remembered in `...\_datos_metrix\reposiciones_enviadas.json`.
- Byte values per type are editable in the app (saved per PC in
  `%APPDATA%\SistemaDVH\config.json`); default PDV 7 / KNT 6 / resto 6.5.
