# Estado del proyecto

Cada sesión, al cerrar una etapa, actualiza este archivo para que la siguiente pueda retomar sin
leer toda la conversación. Lo más nuevo, arriba.

## 25/10/2026: fase F4 lista para correr (validación histórica; sin datos todavía)

**Hecho**
- `optimizador/historico/`: lector del zip/carpeta del contrato (v2), lector de leyendas (formato
  real de Juan), reconstrucción de piezas (DVH = 2 vidrios, sin herrajes/fletes/cámaras, sin contar
  dos veces), relación material abreviado → código de Metrix, control de la entrada por
  aprovechamiento, corrida de H0–H2 con la misma plancha, calibración 70/30 por grupo de material,
  resumen para `docs/VALIDACION.md` y página de revisión con marcas y "Copiar mis respuestas".
- `python -m optimizador historico [--todo] [--docs] [--publicar]`; guarda resultados parciales y
  retoma si se corta.
- Caso de juguete **inventado** en `tests/historico_juguete/` (lo genera
  `herramientas/generar_caso_juguete.py`) y tests de punta a punta.
- Se encontró y arregló un error de reconstrucción: con un vidrio en varios renglones, las piezas
  de `DETPRES2` se contaban dos veces.

**Cuando lleguen los datos**: ponerlos en `datos/casos/` (o adjuntarlos) y usar el prompt 3 de
`PROMPT_INICIAL.md`. Primero `python -m optimizador historico` (muestra de 50) y mirar la
cobertura; después `--todo --docs`.

## 25/10/2026: fase F3 cerrada (interfaz local, .bat, importadores, presets)

**Hecho**
- `Abrir_Optimizador.bat`: doble clic → crea `.venv` la primera vez (con `py -3` o `python`),
  instala `requirements.txt` (o desde una carpeta `paquetes\` sin internet), levanta el servidor y
  abre el navegador. Reinstala solo si cambió `requirements.txt`. Cerrar la ventana lo apaga.
- `optimizador/servidor.py` (FastAPI) en 127.0.0.1:**8520** o el siguiente libre (saltea 8080,
  8090, 8501, 8502). Nada de internet: la página (`optimizador/web/`) es HTML/JS/CSS sin compilar.
- Pantallas: **Materiales** (lista + Descripción / Propiedades físicas como la captura 4 /
  Propiedades comerciales provisoria / Planchas, con el valor de la configuración en rojo entre
  paréntesis; los cambios se guardan en `config/local/materiales.json`, que no va a git),
  **Proyecto** (grilla editable, pegar desde Excel con vista previa, importar CSV/XLSX/.xls de la
  Interfaz, guardar/abrir en `proyectos/`, revisar antes de calcular), **Calcular** (como la
  captura 3, con cancelar), **Resultados** (informe + montajes, imprimir en 3 modos, exportar Excel,
  CSV y JSON) y **Comparar** (cargar a mano lo que dio Corte Certo).
- Presets en la barra de arriba: "Como Corte Certo hoy" / "Reglas de corte (Lucas)"; esfuerzo
  rápido/normal/máximo; punto o coma decimal.
- Importadores (`optimizador/importadores.py`): columnas por encabezado (con sinónimos) o por
  posición; números con punto de miles o coma decimal; DVH = 2 vidrios; herrajes ignorados con
  aviso. La posición de la CANTIDAD en la planilla de la Interfaz es **supuesta** (pregunta 13).
- Se probó de punta a punta con un navegador (Playwright): pegar, revisar, calcular, ver
  resultados, comparar y guardar un material, sin errores de JavaScript.
- Tests nuevos: importadores y servidor (levantado de verdad en un puerto libre).

**No se pudo probar**: el `.bat` en Windows (la nube es Linux) ni la lectura de un `.xls` real de
la Interfaz (no hay planilla de ejemplo).

## 25/10/2026: fase F2 cerrada (informe, montajes SVG, impresión, JSON)

**Hecho**
- `optimizador/informe.py`: "Informe de cálculo" con el formato de la captura 1 (proyectos
  calculados, lista de materiales, planchas usadas, perímetro, punto decimal o coma) y un recuadro
  aparte con lo agregado (validador, preset, mínimo teórico, m² de hoja entera, peso, avisos).
- "Visualizar e imprimir montajes" como la captura 2: Datos generales en recuadros negros con
  números en color, miniaturas apiladas con ×N, 6 por fila; detalle de cada montaje con medidas,
  ítems, sobrantes y cortes numerados (rojo = de lado a lado, azul = adentro de una tira).
- Impresión A4 apaisada por CSS: informe solo, montajes varios por hoja, o uno por hoja (se
  verificó a PDF: cada detalle entra en una hoja).
- `docs/API.md`: entrada, salida y ejemplo completo; CLI `--html`.
- `optimizador/exportar.py`: consumo por material a CSV (`;`, UTF-8 con BOM) y XLSX.

**No se hizo**: exportar el proyecto en el formato que importa Corte Certo (era opcional y no
conocemos ese formato).

## 25/10/2026: fase F1 cerrada (motor + validador + banco sintético + CLI)

**Hecho**
- Motor (`optimizador/motor/`): generador de montajes de guillotina (tiras, renglones iguales o
  mixtos, alternancia de la dirección de corte, relleno de sobrantes), heurística secuencial,
  generación de columnas + programación entera con HiGHS (scipy), cantidades exactas, sobrante
  junto en la última plancha, mínimo teórico. Trabajo limitado por cantidad (reproducible).
- Validador independiente (`optimizador/validador.py`), usado en cada cálculo y en los tests.
- `optimizar()` (`optimizador/api.py`), presets "Como Corte Certo hoy" (con +3 mm en pulido recto,
  confirmado por Juan) y "Reglas de corte (Lucas)", hipótesis H0–H2, ajustes por material.
- CLI: `python -m optimizador calcular|materiales|banco|servidor`.
- Banco sintético en `tests/banco/` (85 casos fijos) y resultados en `docs/VALIDACION.md`.
- Tests: 49 (mochila contra fuerza bruta, validador con resultados rotos, casos borde del brief,
  instancias al azar, banco). Además 500 instancias al azar: 0 fallas.

**Números** (detalle en `docs/VALIDACION.md`): 100 % validado; tiempos y memoria dentro de las
metas; óptimo en 50 % del "corte perfecto" hasta 100 piezas (**meta 95 %: no se cumple**; son
rompecabezas de piezas todas distintas; los casos realistas quedan en la cota de la relajación en
11 de 13).

**Pendiente del motor**: mejorar el "corte perfecto" (generador más fuerte o más trabajo en el
esfuerzo normal sin pasarse de 10 s); máximo tamaño cortado (`corte_max_mm`) todavía no se
controla (se guarda la opción).

## 25/10/2026: fase F0 cerrada (inventario y entendimiento)

**Hecho**
- Repo ordenado según el mapa de `CLAUDE.md` (los archivos habían llegado sueltos en la raíz).
- `docs/INVENTARIO.md`: qué es cada archivo y para qué sirve.
- `docs/ENTENDIMIENTO.md`: qué se entendió, dudas y plan del motor.
- Análisis de la captura de montajes en píxeles: primer corte vertical, 3 etapas, sobrante arriba
  y a la derecha, colores de la paleta de Windows (por tipo de pieza; pregunta 5 actualizada).
- Preguntas nuevas: 18 (textura), 19 (mezclar medidas de plancha), 20 (Python de la PC).
- Esqueleto del paquete `optimizador/`, `requirements.txt` (versiones fijas con paquetes para
  Windows) y un test mínimo. `pytest -q` en verde.
- Se verificó que `herramientas/importar_medidas_hojas.py` regenera `config/hojas.csv` idéntico.

**Revisión del subagente revisor (F0)**: 1 problema grave (el nombre de una obra en
`contexto/fabrica/DATA_DICTIONARY.md`: reemplazado por `<OBRA>`; sigue en la historia de git), 4
medios (inventario incompleto, la regla de colores tampoco cerraba con la captura, el brief con la
hipótesis vieja, `hypothesis` sin paquete para Python 3.10) y 9 menores. Corregidos todos menos
los que tiene que decidir Juan (preguntas 21 y 22) y los avisos para F3/F5 (instalación sin
internet, Python "solo para mí", no usar fuentes de internet en la interfaz).

**Todavía no hay motor.** **Datos históricos**: no llegaron (`datos/casos/` vacío).

**Siguiente paso**: fase F1 (motor + validador + banco sintético + CLI).

## 21/10/2026: repo creado (sesión de armado, Claude + Juan)

**Hecho**
- Especificación completa: `docs/BRIEF_OPTIMIZADOR.md`.
- Pantallas de Corte Certo con las 4 capturas: `docs/CORTE_CERTO.md`.
- Contrato de los datos históricos: `docs/CONTRATO_DATOS.md`.
- Medidas de planchas convertidas: `config/hojas.csv` (101 medidas, 87 materiales), desde
  `config/fuentes/Medidas_hojas.xlsx` con `herramientas/importar_medidas_hojas.py`.
- Reglas de corte de Lucas: `config/reglas_corte.csv`.
- Documentos de la fábrica copiados en `contexto/fabrica/`, sin nombres de clientes; mapa en
  `contexto/LEEME.md`.
- Preguntas abiertas para Juan: `docs/PREGUNTAS_ABIERTAS.md` (17).

**Todavía no hay código del optimizador.**

**Datos históricos**: todavía no llegaron. `datos/casos/` está vacío.

**Siguiente paso**: fase F0 del brief (inventario y entendimiento). El prompt para arrancar está
en `PROMPT_INICIAL.md`.
