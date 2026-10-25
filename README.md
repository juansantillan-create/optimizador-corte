Optimizador de corte de vidrio propio de Cristalux, para cotizar: fases F0 a F5 del brief (docs/BRIEF_OPTIMIZADOR.md). Corre local en la PC de la oficina (Windows, sin internet), con doble clic en Abrir_Optimizador.bat.

Qué trae
Motor (optimizador/motor/): montajes de guillotina por etapas, heurística secuencial, generación de columnas + programación entera (HiGHS, de scipy), cantidades exactas y el sobrante junto en la última plancha. El trabajo se corta por cantidad, no por reloj: el mismo caso da lo mismo en cualquier PC.
Validador independiente (optimizador/validador.py): revisa cada resultado antes de mostrarlo (geometría, guillotina, destaque, orientación, cantidades exactas, números del informe y que la configuración sea la de la entrada).
Informe y montajes como Corte Certo (capturas 1 y 2), impresión A4, exportar Excel/CSV/JSON (optimizador/informe.py, dibujo.py, exportar.py).
Interfaz local (optimizador/servidor.py + optimizador/web/): materiales con la ficha de la captura 4, proyecto (pegar desde Excel, importar CSV/XLSX/.xls de la Interfaz), "Cálculo en proceso" como la captura 3, resultados y comparar.
Validación histórica lista para correr (optimizador/historico/): lee la leyenda de Corte Certo de las observaciones, reconstruye las piezas, controla la entrada, calibra H0–H2 con el 70 % y reporta sobre el 30 %. No se corrió: los datos todavía no llegaron.
Documentos: docs/INSTALACION.md, docs/USO.md, docs/API.md, docs/VALIDACION.md, docs/ESTADO.md, docs/DECISIONES.md, docs/PREGUNTAS_ABIERTAS.md.
Números (detalle en docs/VALIDACION.md)
Todo resultado pasa el validador: 85 de 85 en el banco sintético y 500 de 500 en la prueba de estrés (158 de tamaño real).
"Corte perfecto" (piezas todas distintas que llenan justo k planchas), hasta 100 piezas: óptimo en 30 de 60 (50 %); con esfuerzo "Máximo", 36 de 60. La meta del brief es 95 %: no se cumple.
Presupuestos realistas: en 11 de 13 el resultado está en la cota de la relajación lineal.
Tiempos en la nube: típico (300 piezas, 30 medidas) 1,2 s la primera solución y 5–8 s el final; grande (2000 piezas, 60 medidas) 23 s; el peor caso (2000 piezas todas distintas) 69 s, por encima de la meta de 60 s. Memoria: 110 MB (310 MB el peor caso).
Revisiones
Todas las fases (F0 a F5) las revisó el subagente revisor. Lo grave que encontró está corregido y con tests:

el motor ponía piezas de más en casos grandes;
un valor negativo en la configuración daba piezas encimadas con "Validador OK";
Cancelar no cortaba; con "Máximo" y 2000 medidas distintas pasaba los 1000 MB;
importaciones que perdían la cantidad o un vidrio del DVH;
el control de la validación histórica sacaba el +3 mm cuando le convenía;
privacidad de la página de revisión publicable.
Lo que no se hizo está en docs/ESTADO.md.

Cómo probarlo
pytest -q (todo en verde con Python 3.13 y 3.10).
En Windows: seguir docs/INSTALACION.md (doble clic en Abrir_Optimizador.bat).
Benchmark en la PC: .venv\Scripts\python.exe -m optimizador banco.
Qué tiene que contestar Juan
docs/PREGUNTAS_ABIERTAS.md (las más importantes: 1, 3, 13 y 24).

🤖 Generated with Claude Code

https://claude.ai/code/session_01HJ8A24TCMxCxYoHiNxfUbU


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
.venv\Scripts\python.exe herramientas\prueba_estres.py   # 500 casos al azar contra el validador
```
