# optimizador-corte

Optimizador de corte de vidrio de **Cristalux**, para **cotizar**: dado un listado de piezas,
calcula cuántas planchas hacen falta, cómo se acomodan (montajes) y el aprovechamiento, con la
misma configuración y las mismas pantallas que Corte Certo v3.9K. Corre local en una PC de la
oficina (Windows). No manda nada a las mesas de corte: eso sigue siendo Optima.

**Estado**: en construcción. Repo armado el 21/10/2026 con la especificación; el código lo
desarrollan sesiones de Claude Code en la web. Ver `docs/ESTADO.md`.

## Por dónde empezar

| Si sos… | Leé |
|---|---|
| Juan, arrancando una sesión en la nube | `PROMPT_INICIAL.md` (qué pegar y cómo) |
| Una sesión de Claude | `CLAUDE.md` → `docs/ESTADO.md` → `docs/BRIEF_OPTIMIZADOR.md` |
| Alguien que quiere entender qué hace | `docs/BRIEF_OPTIMIZADOR.md` §0–§5 y `docs/CORTE_CERTO.md` |
| Quien va a armar el zip de casos viejos | `docs/CONTRATO_DATOS.md` |

## Reglas

- **Nada de nombres de clientes** en este repo. Datos con nombres: `datos/privado/`, que no va a
  git.
- **No se conecta a Metrix** ni a ningún sistema de la fábrica: trabaja con archivos.

## Cómo se usa

Se completa cuando esté la interfaz. La idea es un doble clic en `Abrir_Optimizador.bat`, que
abre el navegador en `http://127.0.0.1:8520`.
