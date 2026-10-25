# Documentos de la fábrica: qué es cada uno y cuánto importa para el optimizador

Vienen del proyecto de Metrix de Juan (foto al 21/10/2026; ese proyecto sigue cambiando). Están
en `contexto/fabrica/`.

Algunos mencionan cosas que no están en este repo:
- el `../CLAUDE.md` de ese proyecto: lo que importa de ahí está resumido en nuestro `CLAUDE.md`
  (solo lectura, sin nombres de clientes, cuidado con producción, Windows);
- rutas de la PC de Juan y direcciones de la red interna: no sirven desde la nube.

Se sacaron 4 menciones a clientes antes de subirlos: 2 en DATA_DICTIONARY, 1 en PRECIOS y 1 en
EXPEDIENTE_PEDIDO.

| Archivo | Qué es | Importa para el optimizador | Cómo leerlo |
|---|---|---|---|
| `GLOSSARY.md` | Vocabulario del vidrio y de Metrix (templado, DVH, laminado, pulido, fasón, Lamilux, m² y ml según Metrix) | **Alta** | Entero, en la fase F0 |
| `DATA_DICTIONARY.md` | Las tablas y campos de Metrix: qué significa cada uno y sus trampas | **Alta** para reconstruir los casos históricos (F4) | Parte 2: `PRESUP`, `DETPRES`, `DETPRES2`, `ARTICULO`, `FAMILIAS`, `CLASES`. El resto, de consulta |
| `GUIA_BASE_TABLERO.md` | Cómo consultar la copia DuckDB de Metrix: fechas Clarion, marcas de proceso, artículos `X…` (unidades armadas, no vidrio) | **Alta** si los datos llegan en DuckDB | §4 (convenciones) y §8 (trampas) |
| `VISION_ORQUESTADOR.md` | El plan general: un orquestador que lleva cada pedido de punta a punta. El optimizador figura "por hacer" | Media: explica para quién es la API y por qué | "Las piezas y cómo están hoy" y "Etapas" |
| `EXPEDIENTE_PEDIDO.md` | La ficha de cada pedido y el "portón de producción", donde el comercial controla el consumo de hojas | Media: la salida JSON tiene que servir para eso | "Los estados" y "El portón de producción" |
| `mapa_orquestador.html` | Lámina visual del orquestador (16/10) | Baja | Opcional. Sirve como ejemplo del estilo de las páginas que ya usa Juan |
| `ARCHITECTURE.md` | Cómo fluyen los datos de Metrix: pipelines, DuckDB, "atomic swap", puertos | Media: convenciones de la casa | Puertos y "atomic swap" |
| `RUNBOOK.md` | Qué hacer cuando algo se rompe; cómo es la PC (Windows, `.bat`, gente que no usa consola) | Media: así tienen que ser el arranque y la instalación | Secciones 1, 3 y 4 |
| `PANORAMA_2026-10-07.md` | Estado del proyecto grande al 07/10 (bots de presupuesto y de notas de pedido) | Baja | Opcional |
| `PRECIOS.md` | Precios de Metrix por proceso (distribución, corte, templado, DVH), fasón y listas | Baja ahora; sirve si después se valoriza la optimización | Consulta |
| `LISTAS_DISTRIBUCION.md` | Listas de distribución por cliente y variantes de hoja (media hoja 1800 × 2500, hoja con cortes +10 % / +15 %) | Baja: muestra cómo se venden hojas y medias hojas | Consulta |
| `CRUCE_MAINQUE.md` · `MAPA_CRUCE_MAINQUE.md` · `PLAN_NP_A_PEDIDO.md` | Cruce de presupuestos de Metrix con la facturación (mainque) y el bot de notas de pedido | Baja: contexto de clases (DIST/LAMILUX = hoja entera; el resto, corte "a medida") | Consulta |
| `WATERJET_PLANOS.md` | Planos para la water jet (`.wpd`) | Baja en el tema, **alta en el método**: referencia + comparador + página de revisión lado a lado con votos de Juan; "el modelo lee, el código decide". Tiene además la medida mínima de las piezas que van a la water jet (350 × 650, "sobremedida") | "Cómo funciona" y "Supervisión y hoja del operario" |

**Lo que el optimizador NO tiene que copiar de estos proyectos**:
- la conexión a SQL Server;
- los bots que escriben en Metrix y mainque;
- los servicios de Windows.

El optimizador es un programa aparte, que trabaja con archivos.
