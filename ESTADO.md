# Estado del proyecto

Cada sesión, al cerrar una etapa, actualiza este archivo para que la siguiente pueda retomar sin
leer toda la conversación. Lo más nuevo, arriba.

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
