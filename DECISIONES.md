# Decisiones

Una línea por decisión: fecha, qué se decidió y por qué. Lo más nuevo, abajo.

| Fecha | Decisión | Por qué / quién |
|---|---|---|
| 2026-10-14 | El optimizador propio es **solo para cotizar**: calcula y acomoda vidrios en planchas, con pocas configuraciones. Sin etiquetas ni envío a mesas (eso sigue siendo Optima). | Juan |
| 2026-10-14 | Se desarrolla en la nube con Claude y **corre local** en la PC de la oficina. | Juan |
| 2026-10-21 | **Repo separado** del proyecto de Metrix (`optimizador-corte`, privado en GitHub). | No mezclarlo con credenciales, `.tps` ni datos de clientes; que la nube vea solo lo necesario |
| 2026-10-21 | Tiene que verse y configurarse **como Corte Certo**: mismos campos, nombres y números. | Juan: "tal cual las imágenes, configuraciones del optimizador que ya usamos" |
| 2026-10-21 | Dos presets: **"Como Corte Certo hoy"** (por defecto: solo corte banda) y **"Reglas de corte (Lucas)"** (banda + separación 20/30/50). Todo editable por material. | Juan: "con esa configuración o cambiándola"; la captura tiene sierra y destaque en 0 |
| 2026-10-21 | Planchas: de `Medidas_hojas.xlsx` → `config/hojas.csv`. El corte banda se resta al lado largo. | Planilla de Juan; así está cargado Corte Certo (3580 × 2500) |
| 2026-10-21 | Medidas en mm enteros; plancha acostada; Ancho = X = lado largo. | Convención de Corte Certo y de la planilla |
| 2026-10-21 | El aprovechamiento se calcula como Corte Certo (m² de piezas ÷ m² de plancha útil); la hoja entera se informa aparte. | Para poder comparar con lo que dio Corte Certo |
| 2026-10-21 | Se valida contra los casos históricos de Metrix (zip sin nombres, `docs/CONTRATO_DATOS.md`). La configuración final sale de esa calibración. | Juan: "tenemos acceso total a casos anteriores…" |
