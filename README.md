# optimizador-corte

Optimizador de corte de vidrio de **Cristalux**, para **cotizar**: dado un listado de piezas,
calcula cuántas planchas hacen falta, cómo se acomodan (montajes) y el aprovechamiento, con la
misma configuración, las mismas fórmulas y pantallas como las de Corte Certo v3.9K. Corre local en
una PC de la oficina (Windows), sin internet. No manda nada a las mesas de corte: eso sigue siendo
Optima.

## Cómo se usa

Doble clic en **`Abrir_Optimizador.bat`**: se abre el navegador en `http://127.0.0.1:8520`.
Pegás las piezas desde Excel, apretás **Calcular** y ves el informe y los montajes para imprimir.

- Instalación paso a paso: [`docs/INSTALACION.md`](docs/INSTALACION.md)
- Cómo cotizar: [`docs/USO.md`](docs/USO.md)
- Qué tan confiable es (números): [`docs/VALIDACION.md`](docs/VALIDACION.md)
- Para el orquestador (función de Python, CLI y JSON): [`docs/API.md`](docs/API.md)

## Por dónde empezar

| Si sos… | Leé |
|---|---|
| Juan, arrancando una sesión en la nube | `PROMPT_INICIAL.md` (qué pegar y cómo) |
| Una sesión de Claude | `CLAUDE.md` → `docs/ESTADO.md` → `docs/BRIEF_OPTIMIZADOR.md` |
| Alguien que quiere entender qué hace | `docs/BRIEF_OPTIMIZADOR.md` §0–§5 y `docs/CORTE_CERTO.md` |
| Quien va a armar el zip de casos viejos | `docs/CONTRATO_DATOS.md` |
| Quien tiene que contestar dudas | `docs/PREGUNTAS_ABIERTAS.md` |

## Reglas

- **Nada de nombres de clientes** en este repo. Datos con nombres: `datos/privado/`, que no va a
  git.
- **No se conecta a Metrix** ni a ningún sistema de la fábrica: trabaja con archivos.
- Todo resultado pasa por un **validador independiente** antes de mostrarse.

## Para desarrollar

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m optimizador banco      # banco de pruebas sintético
```
