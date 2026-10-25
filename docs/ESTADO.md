# Estado del proyecto

Cada sesión, al cerrar una etapa, actualiza este archivo para que la siguiente pueda retomar sin
leer toda la conversación. Lo más nuevo, arriba.

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
