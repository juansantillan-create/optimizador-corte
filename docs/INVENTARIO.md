# Inventario del repo

Qué es cada archivo y para qué sirve. Si aparece un archivo nuevo (por ejemplo, adjunto en un
mensaje), se clasifica, se guarda donde corresponde y se anota acá (brief §3).

**25/10/2026 (fase F0)**: los archivos llegaron todos sueltos en la raíz (subidos "planos" a
GitHub, algunos con nombres como `LEEME (2).md` o `download`). Se ubicaron según el mapa de
`CLAUDE.md` con `git mv`, así la historia de cada uno se conserva. Ninguno tiene nombres de
clientes (se buscaron razones sociales, CUIT, mails y teléfonos), salvo el nombre de una obra en
`contexto/fabrica/DATA_DICTIONARY.md` que encontró el revisor y se reemplazó por `<OBRA>` (sigue en
la historia de git; ver `DECISIONES.md`).

## Raíz

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `CLAUDE.md` | Reglas permanentes para las sesiones de Claude | Lo primero que se lee. Reglas que no se negocian |
| `README.md` | Presentación del repo | Por dónde empezar según quién sos |
| `PROMPT_INICIAL.md` | Los 3 prompts para arrancar sesiones en la nube | Lo usa Juan |
| `.gitignore` | Lo que no va a git (`datos/privado/`, `proyectos/`, `config/local/`, venv…) | Privacidad y limpieza. Llegó como `download (1)` |
| `.gitattributes` | Fin de línea CRLF para los `.bat`; binarios | Que los `.bat` anden en Windows. Llegó como `download` |
| `requirements.txt` | Dependencias con versiones fijas (todas con paquetes para Windows) | Instalar el programa |
| `requirements-dev.txt` | Lo de arriba más pytest e hypothesis | Correr los tests |
| `pyproject.toml` | Datos del paquete y configuración de pytest | Que el orquestador pueda instalar e importar `optimizador` |

## `optimizador/` (el programa) y `tests/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `optimizador/__init__.py`, `__main__.py` | El paquete y la línea de comandos (`python -m optimizador`) | `calcular`, `materiales`, `banco`, `servidor` |
| `optimizador/modelo.py` | Pieza, Material, Plancha, Proyecto | Las convenciones de medidas |
| `optimizador/configuracion.py` | Lee `hojas.csv` y las reglas; presets y ajustes locales | Con qué valores se calcula |
| `optimizador/motor/mochila.py` | Mochila 1D acotada (numpy) | Pieza básica del generador |
| `optimizador/motor/arbol.py` | Árbol de guillotina, cortes, medidas reales | Cómo se guarda un montaje |
| `optimizador/motor/generador.py` | Generador de montajes de guillotina | El corazón del motor |
| `optimizador/motor/calculo.py` | Heurística, generación de columnas, entera, cantidades exactas | Calcula un material |
| `optimizador/api.py` | `optimizar()`: entrada → resultado (JSON) | Para la interfaz y el orquestador |
| `optimizador/validador.py` | Validador independiente | Revisa cada resultado |
| `optimizador/banco.py` | Genera y corre el banco sintético | Benchmark y control de que nada empeore |
| `optimizador/colores.py`, `dibujo.py`, `informe.py`, `exportar.py` | Colores, SVG de montajes, informe HTML, CSV/XLSX | Fase F2 |
| `optimizador/importadores.py`, `servidor.py`, `web/` | Importar piezas, servidor local y la página | Fase F3 |
| `optimizador/historico/` | Validación contra los casos viejos: datos, leyendas, reconstrucción, comparar/calibrar, página de revisión | Fase F4 (`python -m optimizador historico`) |
| `tests/historico_juguete/` | Caso de juguete **inventado** con el formato del contrato | Probar F4 sin datos reales |
| `ejemplos/proyecto_ejemplo.json` | Un proyecto inventado para probar la CLI | `python -m optimizador calcular ejemplos/proyecto_ejemplo.json` |
| `tests/` | Tests (`pytest -q`); `tests/banco/` = 85 casos fijos + `esperado.json` | Controlar que todo ande |

## `docs/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `BRIEF_OPTIMIZADOR.md` | La especificación completa | Alcance, motor, salidas, interfaz, validación, fases y metas |
| `CORTE_CERTO.md` | Las pantallas de Corte Certo, campo por campo | Lo que hay que replicar |
| `img/corte_certo_1_informe_calculo.png` | Captura: Informe de cálculo (proyecto 413) | Formato y fórmulas del informe |
| `img/corte_certo_2_montajes.png` | Captura: Visualizar e imprimir montajes | Miniaturas, pilas, colores, Datos generales |
| `img/corte_certo_3_calculo_en_proceso.png` | Captura: Cálculo en proceso | Pantalla de progreso |
| `img/corte_certo_4_propiedades_fisicas.png` | Captura: Material → Propiedades físicas | Campos de configuración por material |
| `CONTRATO_DATOS.md` | Qué trae el zip de casos históricos (versión 2: la leyenda está en "Situación de Presupuesto → Observaciones") | Fase F4 |
| `FORMATO_LEYENDAS.md` | Los formatos de la leyenda de Corte Certo y cómo se leen | Fase F4 |
| `ESTADO.md` | Dónde quedó el trabajo | Para retomar sin leer la conversación |
| `DECISIONES.md` | Qué se decidió, cuándo y por qué | Registro |
| `PREGUNTAS_ABIERTAS.md` | Lo que tiene que contestar Juan, con la opción por defecto | Juan contesta abajo de cada una |
| `INVENTARIO.md` | Este archivo | |
| `ENTENDIMIENTO.md` | Qué entendió la sesión de F0, dudas y plan | Fase F0 |
| `VALIDACION.md` | Qué tan confiable es: banco sintético, tiempos, metas (y la validación histórica cuando lleguen los datos) | Para Juan |
| `API.md` | La función `optimizar()`, la CLI y el JSON | Para el orquestador |

## `config/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `LEEME.md` | Explica los archivos de configuración | Llegó como `LEEME.md` en la raíz |
| `hojas.csv` | **Lo que usa el programa**: 101 medidas de plancha de 87 materiales, con corte banda, plancha útil y separación | Fuente de las planchas. Se genera, no se edita |
| `reglas_corte.csv` | Corte banda y separación por grupo de espesor (regla de Lucas) | Preset "Reglas de corte (Lucas)" |
| `fuentes/Medidas_hojas.xlsx` | Planilla original de Juan (MONOLITICO y LAMINADO) | Fuente de `hojas.csv`. **Se verificó el 25/10: regenerar el CSV con el script da un archivo idéntico** |
| `fuentes/reglas_corte_2026-10-21.txt` | Texto original de la regla de Lucas | Registro de lo que se dijo |

## `contexto/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `LEEME.md` | Mapa de los documentos de la fábrica: cuáles leer enteros y cuáles consultar | Llegó como `LEEME (4).md` |
| `fabrica/GLOSSARY.md` | Vocabulario del vidrio y de Metrix | Leído entero en F0 |
| `fabrica/DATA_DICTIONARY.md` | Tablas y campos de Metrix, con sus trampas | F4: reconstruir los casos (`PRESUP`, `DETPRES`, `DETPRES2`) |
| `fabrica/GUIA_BASE_TABLERO.md` | Cómo consultar la copia DuckDB de Metrix | F4, si los datos llegan en DuckDB (fechas Clarion, artículos `X…`) |
| `fabrica/VISION_ORQUESTADOR.md` | El plan del orquestador; el optimizador figura "por hacer" | Para quién es la API (F2) |
| `fabrica/EXPEDIENTE_PEDIDO.md` | La ficha del pedido y el "portón de producción" | La salida JSON tiene que servir para controlar el consumo de hojas |
| `fabrica/mapa_orquestador.html` | Lámina visual del orquestador | Ejemplo del estilo de páginas de Juan |
| `fabrica/ARCHITECTURE.md` | Cómo fluyen los datos de Metrix; puertos ocupados | Convenciones (puertos, "atomic swap") |
| `fabrica/RUNBOOK.md` | Qué hacer cuando algo se rompe; cómo es la PC | Cómo tienen que ser el arranque y la instalación (`.bat`, nada de consola) |
| `fabrica/PANORAMA_2026-10-07.md` | Estado del proyecto grande al 07/10 | Contexto, opcional |
| `fabrica/PRECIOS.md` | Precios de Metrix por proceso | Consulta (si después se valoriza) |
| `fabrica/LISTAS_DISTRIBUCION.md` | Listas por cliente, hoja entera y media hoja | Consulta |
| `fabrica/CRUCE_MAINQUE.md`, `MAPA_CRUCE_MAINQUE.md`, `PLAN_NP_A_PEDIDO.md` | Cruce de presupuestos con la facturación y bot de NP | Consulta: clases DIST/LAMILUX = hoja entera |
| `fabrica/WATERJET_PLANOS.md` | Planos para la water jet | El **método** (referencia + comparador + página de revisión con votos de Juan) se copia en F4 |

## `datos/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `LEEME.md` | Qué va en `casos/` y en `privado/` | Llegó como `LEEME (2).md` |
| `casos/.gitkeep` | Archivo vacío para que la carpeta exista en git | Llegó como `download (3)` (vacío) |
| `casos/` | **Vacía al 25/10/2026**: los casos históricos todavía no llegaron | F4 |
| `privado/` | No existe en git (está en `.gitignore`) | Lo que tenga nombres de clientes, solo en la PC de Juan |

## `herramientas/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `importar_medidas_hojas.py` | Convierte `Medidas_hojas.xlsx` en `hojas.csv` | Regenerar la configuración de planchas |
| `generar_caso_juguete.py` | Genera el caso de juguete de `tests/historico_juguete/` | Tests de F4 |

## `.claude/agents/`

| Archivo | Qué es | Para qué sirve |
|---|---|---|
| `revisor.md` | Subagente revisor independiente | Revisa al cerrar cada fase. Llegó como `revisor.md` en la raíz |

## Lo que no llegó

- Llegaron `LEEME.md`, `LEEME (2).md` y `LEEME (4).md` (no `(1)` ni `(3)`), y `download`,
  `download (1)` y `download (3)` (no `(2)`). Por el contenido de los que llegaron no parece faltar
  nada (cubren `config/`, `datos/` y `contexto/`), pero quedó la pregunta 22.
- No llegaron casos históricos ni una planilla de la Interfaz de Metrix (pregunta 13).

## Lo que se agrega en las fases siguientes

Se anota a medida que aparece (código en `optimizador/`, tests en `tests/`, documentos nuevos en
`docs/`). Ver `docs/ESTADO.md`.
