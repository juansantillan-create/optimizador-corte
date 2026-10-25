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
| 2026-10-25 | Los archivos subidos sueltos a la raíz se ubicaron según el mapa de `CLAUDE.md` con `git mv` (`download` → `.gitattributes`, `download (1)` → `.gitignore`, `LEEME (2)/(4)` → `datos/` y `contexto/`). | Llegaron "planos"; `git mv` conserva la historia. Detalle en `docs/INVENTARIO.md` |
| 2026-10-25 | Colores de los montajes: regla propia, **un color por tipo de pieza**, con la paleta clásica de Windows en el orden de Corte Certo (bordó, verde, oliva, …); amarillo = sobrante. | Medido en la captura 2: no es "verde = girada, oliva = retazo" ni "un color por medida". No sabemos la regla de Corte Certo; esta se lee bien. Pregunta 5 |
| 2026-10-25 | Textura: veta horizontal = el largo de la pieza va en el eje X (lado largo de la plancha); vertical = en el eje Y. Con veta la pieza no gira. | Lo que dice el brief §6.1; Metrix no da la orientación. Pregunta 18 |
| 2026-10-25 | `requirements.txt` con versiones fijas y dos tramos: Python ≥ 3.12 usa las mismas versiones que la nube (numpy 2.5.4, scipy 1.18.1); 3.10/3.11 usan numpy 2.2.6 y scipy 1.15.3. | Se verificó que todas tienen paquetes para Windows (`pip download --platform win_amd64`). Mismas versiones = mismos resultados. Pregunta 20 |
| 2026-10-25 | El cálculo se corta por **cantidad de trabajo** (iteraciones, llamadas al generador, nodos de la programación entera), no por reloj; el reloj queda solo como límite de seguridad, con aviso si se usa. | Regla 5 de `CLAUDE.md`: el mismo caso tiene que dar lo mismo en la nube y en la PC de Juan, que es más lenta |
| 2026-10-25 | Se reemplazó por `<OBRA>` el nombre de una obra en `contexto/fabrica/DATA_DICTIONARY.md` (lo encontró el revisor). Sigue en el commit 1aac472 de la historia: no se reescribe (regla 6). | Si hace falta borrarlo también de la historia, lo tiene que decidir Juan (es irreversible) |
