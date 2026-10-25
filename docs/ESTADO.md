# Estado del proyecto

Cada sesión, al cerrar una etapa, actualiza este archivo para que la siguiente pueda retomar sin
leer toda la conversación. Lo más nuevo, arriba.

## 25/10/2026: fase F5 (entrega) y correcciones de las revisiones de F1, F3 y F4

**Dónde quedó todo, en una línea**: el optimizador anda de punta a punta (pegar o importar piezas →
calcular → informe y montajes como Corte Certo → imprimir/exportar), todo resultado pasa el
validador, y la validación contra los casos viejos está lista pero **no se corrió porque los datos
no llegaron**.

**Hecho en esta etapa**
- `docs/INSTALACION.md` (paso a paso para la PC de la oficina, también sin internet), `docs/USO.md`
  (cómo cotizar) y el `README.md`.
- Correcciones de la revisión de **F4** (validación histórica): el control usa siempre el +3 mm;
  tolerancia ±0,5; el lector no pierde materiales; la página para git no lleva texto escrito a mano;
  retomar recalcula si cambiaron las piezas; avisos de la reconstrucción al lado de cada caso.
- Correcciones de la revisión de **F1** (motor y validador): un valor imposible en un material
  (sierra o margen negativo, textura desconocida) ya no da piezas encimadas con "Validador OK": el
  material no se calcula y se avisa; el validador arma de nuevo la configuración desde la entrada;
  campo `completo` (falta alguna pieza → aviso en rojo y código de salida 2); "1.200" = 1200;
  aviso si la programación entera se corta por reloj; redondeo "como siempre".
- Correcciones de la revisión de **F3** (interfaz e importadores): encabezados con otros nombres,
  con unidades o con un título arriba; aviso si no hay columna de cantidad; la planilla de la
  Interfaz pegada o en `.xlsx` (DVH = 2 vidrios); Calcular pregunta si hay avisos; un cálculo a la
  vez; Cancelar corta también al principio; los cambios de sierra/destaque/pulido se guardan por
  preset; la ficha de Propiedades físicas se parece más a la captura 4; el `.bat` controla la
  versión de Python, rehace un `.venv` roto y abre igual sin internet; un segundo doble clic usa
  el programa que ya está abierto; el servidor solo atiende a esta PC.
- **Rendimiento con muchas medidas distintas**: 200 piezas todas distintas pasaron de 78 s a 11 s;
  2000 todas distintas, de más de 700 MB a 310 MB (tarda 68 s en la nube: se pasa de la meta de
  60 s; ver `VALIDACION.md` §2.4).
- `herramientas/prueba_estres.py`: casos al azar, también de tamaño real, contra el validador.
- Banco sintético corrido de nuevo: los mismos resultados que antes en los 85 casos.

**Qué falta**
1. **Correr la validación histórica** cuando lleguen los datos (`docs/CONTRATO_DATOS.md`): ahí se
   sabe si da lo mismo que Corte Certo y cuál de las hipótesis H0–H2 usaba la oficina.
2. **Probar en la PC de la oficina**: el `.bat`, los tiempos (`python -m optimizador banco`) y una
   planilla `.xls` real de la Interfaz (la posición de la cantidad es supuesta, pregunta 13).
3. **Motor**: el "corte perfecto" (piezas todas distintas que llenan justo k planchas) da el óptimo
   en el 50 % de los casos hasta 100 piezas; la meta del brief es 95 %. En presupuestos reales
   (piezas repetidas) queda en la cota de la relajación en 11 de 13 casos. Y el peor caso de 2000
   piezas todas distintas tarda más de 60 s.
4. Las preguntas abiertas de `docs/PREGUNTAS_ABIERTAS.md` (las importantes: 1, 3, 13, 24).
5. No se hizo: exportar al formato de Corte Certo (no se conoce), precios en "Propiedades
   comerciales" (no hay captura), y que el máximo tamaño cortado lo respete el motor (hoy solo
   avisa).

**Cómo seguir**: con los datos, el prompt 3 de `PROMPT_INICIAL.md`. Para mejorar el motor, empezar
por `docs/VALIDACION.md` §2.2 (qué se probó y no sirvió).

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

**Revisión del subagente revisor (F3)**: 4 problemas graves (un encabezado de cantidad que no se
reconocía tomaba 1 pieza sin avisar; la planilla de la Interfaz en `.xlsx` o pegada contaba un solo
vidrio del DVH; Cancelar no cortaba mientras se armaba el primer montaje y con muchas medidas
distintas tardaba minutos y pasaba los 700 MB; una sierra negativa daba piezas encimadas con
"Validador OK"), 8 medios y varios menores. Se corrigieron en la etapa F5 (ver arriba y
`DECISIONES.md`); quedaron sin hacer: que la ficha de Propiedades físicas sea idéntica a la
captura 4 (se acercó la grilla y se agregaron dibujitos simples) y que los errores de `xlrd` salgan
en castellano en todos los casos.

## 25/10/2026: fase F2 cerrada (informe, montajes SVG, impresión, JSON)

**Hecho**
- `optimizador/informe.py`: "Informe de cálculo" con el formato de la captura 1 (proyectos
  calculados, lista de materiales, planchas usadas, perímetro, punto decimal o coma) y un recuadro
  aparte con lo agregado (validador, preset, mínimo teórico, m² de hoja entera, peso, avisos).
- "Visualizar e imprimir montajes" como la captura 2: Datos generales en recuadros negros con
  números en color, miniaturas apiladas con ×N, 6 por fila; detalle de cada montaje con medidas,
  ítems, sobrantes y cortes numerados (rojo = de lado a lado, azul = adentro de una tira).
- Impresión A4 apaisada por CSS: informe solo, montajes varios por hoja, o uno por hoja (se
  verificó a PDF: un detalle normal entra en una hoja; uno con muchísimas piezas y cortes puede
  ocupar más, porque la lista de cortes es larga).
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
esfuerzo normal sin pasarse de 10 s). El máximo tamaño cortado ("Limitado") se controla con
aviso; el motor no lo evita al armar los montajes.

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
