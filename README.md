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

## Qué trae y cómo anda

- **Motor** (`optimizador/motor/`): montajes de guillotina por etapas, heurística secuencial,
  generación de columnas + programación entera (HiGHS, de scipy), cantidades exactas y el sobrante
  junto en la última plancha. El trabajo se corta por cantidad, no por reloj: el mismo caso da lo
  mismo en cualquier PC.
- **Validador independiente** (`optimizador/validador.py`): revisa cada resultado antes de
  mostrarlo (geometría, guillotina, destaque, orientación, cantidades exactas, números del informe
  y que la configuración sea la de la entrada).
- **Informe y montajes como Corte Certo**, impresión A4, exportar Excel/CSV/JSON.
- **Interfaz local** (`optimizador/servidor.py` + `optimizador/web/`): materiales, proyecto (pegar
  desde Excel, importar CSV/XLSX/.xls de la Interfaz), "Cálculo en proceso", resultados y comparar.
- **Validación** (`optimizador/historico/`): contra 1341 casos viejos de Corte Certo y 5 lotes
  cortados con Optima.

**Números** (detalle en [`docs/VALIDACION.md`](docs/VALIDACION.md)):

- Contra Corte Certo (1081 casos comparables): **80,3 % da las mismas planchas**, 16,7 % menos y
  3,1 % más. Hasta 20 piezas: 98,5 % iguales. Corte Certo parece haber pasado de la hoja entera
  (3600) a la plancha achicada (3580) en agosto de 2026: calculados con 3580, el 11 % de los casos
  viejos da más hojas (pregunta 28).
- Contra Optima (5 lotes, con la banda y el destaque de la regla de Lucas): con esfuerzo normal, 3
  lotes con los mismos m² de hoja y en total 0,9 % más vidrio (Optima usó retazos en un lote); con
  esfuerzo máximo, 0,5 % menos.
- Todo resultado pasa el validador: los 85 casos del banco sintético, 500 de la prueba de estrés y
  los 2132 cálculos contra Corte Certo.
- "Corte perfecto" (piezas todas distintas que llenan justo k planchas), hasta 100 piezas: óptimo
  en 30 de 60 (36 con esfuerzo "Máximo"). La meta del brief es 95 %: no se cumple.
- Tiempos en la nube: típico (300 piezas, 30 medidas) 1,2 s la primera solución y 5–8 s el final;
  el peor caso (2000 piezas todas distintas) 69 s. Memoria: 110 MB (310 MB el peor caso).

Dónde quedó cada cosa y qué falta: [`docs/ESTADO.md`](docs/ESTADO.md). Lo que tiene que contestar
Juan: [`docs/PREGUNTAS_ABIERTAS.md`](docs/PREGUNTAS_ABIERTAS.md).

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
.venv\Scripts\python.exe herramientas\prueba_estres.py   # 500 casos al azar contra el validador
```
