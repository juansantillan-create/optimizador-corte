# Planos para la water jet: plano del cliente → planilla + .wpd

Estado al 2026-10-16: **prueba de concepto cerrada y validada por Juan** con 2 planos
reales (uno CAD, uno foto). El `.wpd` del plano foto (112 agujeros + 3 entrantes) **se pasó
a producción y se perforó correctamente** (Juan, 2026-10-16). Es la pieza "Generador de planos" de
`docs/VISION_ORQUESTADOR.md` y de la etapa "Planos generados" de
`docs/EXPEDIENTE_PEDIDO.md`.

> Este doc va a git: no nombra clientes ni pedidos. Los planos reales, los
> resultados y los nombres están en la carpeta de trabajo (fuera de git).

## Dónde está

**El código y el prompt están en este repo, en `waterjet/`** (desde 2026-10-16; antes
vivían solo en la carpeta de trabajo):

| Archivo | Qué es |
|---|---|
| `prompts/waterjet_planos.txt` | El prompt para Haiku: lee el plano y devuelve un JSON. Desde el 18/10 vive con los demás prompts (antes `waterjet/prompt_haiku_planos_waterjet.txt`) y se cambia solo desde la sesión de prompts: ver `prompts/README.md`. |
| `waterjet/armar_waterjet.py` | El código: JSON → planilla de la Interfaz Excel + un `.wpd` por pieza. |
| `waterjet/comparar.py` | Compara lo que leyó un modelo contra una referencia, agujero por agujero y entrante por entrante (posición real en mm). Es la herramienta para medir cada cambio del prompt. |
| `waterjet/dibujar_wpd.py` | Dibuja un `.wpd` en PNG (pieza, agujeros, recorridos con sus arcos) para revisarlo sin abrir el SCAD. |
| `waterjet/referencias/` | `.wpd` de ejemplo hechos a mano por Juan en el SCAD, de los que sale cada formato (hoy: `REFERENCIA DE ENTRANTE.wpd`). Sin datos de clientes. |

**Los datos reales quedan fuera de git**, en la carpeta de trabajo
`C:\Users\geronimo.zanon\wpds planos water jet\`: la plantilla `Libro1.xlsx` y una
subcarpeta por plano probado (el plano original, el JSON interpretado, `advertencias.txt`,
los `.wpd` y `pruebas\` con los JSON de cada corrida de Haiku/Opus y la referencia).

Corre con el venv del proyecto (`_work\venv\Scripts\python.exe`, necesita `openpyxl`;
`dibujar_wpd.py` usa `Pillow`). No toca Metrix ni la base: solo lee archivos y escribe
archivos nuevos.

## Tandas: las OC que pasa Juan (desde 2026-10-19)

Mientras el prompt de planos no reconoce herrajes, Juan trabaja así con una sesión de Claude:
le pasa una lista de OC, Claude busca el cierre de Nicolás de cada una en el Gmail de Juan
(solo lectura), **lee los planos él mismo** (no Haiku), arma los `.wpd` y una página para
que Juan controle lado a lado. Dos tandas (46 `.wpd`) validadas por Juan el 19 y 20/10.

| Archivo (`waterjet/`) | Qué hace |
|---|---|
| `tanda.py` | Dónde está la tanda: variable `WJ_TANDA`; sin ella, la carpeta `pedidos AAAA-MM-DD` más nueva. |
| `bajar_oc.py <OC> <OC>...` | Baja de Gmail el hilo del cierre de Nicolás de cada OC, con adjuntos, a `originales\<OC>\`. |
| `bajar_hilo.py <carpeta> <threadId>` | Baja un hilo cualquiera (plano en un mail de Juan, o un pedido repetido de meses antes). |
| `medir_pdf.py` | Lista líneas, curvas y textos de un PDF de CAD, para medir cotas exactas por código. |
| `armar_tanda.py` | Lee el `datos_oc.py` de la tanda → un `.wpd` por ítem (`OC - item N.wpd`) y `revision_datos.json`. |
| `pagina_revision.py` | `revision.html`: plano del cliente al lado del `.wpd` dibujado **con cotas** (`cotas.py`), avisos, votos bien / mal / duda. |
| `cotas.py` | Dibujo con cotas: cada cota sale del borde desde el que mide la fórmula del `.wpd`; herrajes acotados al centro. |
| `calado.py` / `verificar_calado.py` | Calado interior grande partido en celdas (ver abajo) y simulación de que no quede nada pegado. |

**Carpeta de cada tanda** (fuera de git, tiene datos de clientes):
`C:\Users\geronimo.zanon\wpds planos water jet\pedidos AAAA-MM-DD\` con `originales\`,
`planos_png\`, **`datos_oc.py`** (la lectura de los planos que escribe Claude: piezas,
agujeros, herrajes con su `.whd`, avisos y OC sin plano), `wpd\` y `revision.html`.

```
set WJ_TANDA=C:\Users\geronimo.zanon\wpds planos water jet\pedidos AAAA-MM-DD
_work\venv\Scripts\python.exe waterjet\bajar_oc.py <OC> <OC> <OC>...
   (Claude lee los planos y escribe datos_oc.py)
_work\venv\Scripts\python.exe waterjet\armar_tanda.py
_work\venv\Scripts\python.exe waterjet\pagina_revision.py
```

**Reglas que ya están (todas de Juan):**
- Herrajes como `HardwareReference` a un `.whd` de la galería. Se elige comparando la geometría
  del `.whd` con el plano y **cómo los usó Juan en sus `.wpd` viejos** (`My Pieces`).
- **Bisagras P63: siempre `VARIOS\P63 64x41 mm - VALLS (MODIFICADO)`**, aunque haya una P63 con
  el nombre del cliente ("funciona mejor"; la galería tiene mucho repetido).
- **P63 arriba en la mesa**: se traban y hay que sacarlas a mano. Si todas caen en el borde de
  abajo, la pieza se espeja de arriba a abajo (`P63_ARRIBA = True` en el `datos_oc.py` de la
  tanda; la del 19/10 no lo tiene para no cambiar `.wpd` ya validados).
- F4 en croquis: el triangulito apunta al borde por el que entra la muesca.
- **Espejo, opacid y control solar van espejados en la mesa** (Juan, 2026-10-21): se mecanizan con
  el coating para arriba y el plano se ve desde afuera (salvo que diga otra cosa). Se detecta por el
  texto del vidrio (`CON_COATING` en `armar_tanda.py`); una pieza lo apaga con `"coating": False`. Si
  además las P63 quedan abajo, NO se espeja por P63 (cambiaría la cara): queda aviso.
- Arquitos de entrada / salida de entrantes y recortes: hacia el lado del vidrio que queda. Recortes
  largos van en varios cortes (pedazos de ~160), como los calados.
- **Sobremedida** (Juan, 2026-10-21): todo vidrio que va a la water jet mide mínimo **350 × 650**; si
  no llega se le suma hasta 350 (o 650) y **nunca menos de 50 mm** (325 → +50; 298 → +52). Va del lado
  que no tiene herrajes ni entrantes en el borde (arriba / derecha si se puede); las cotas y fórmulas
  siguen midiendo desde el vidrio real y una línea guía del SCAD marca el corte (como el
  `30344 - item 2.wpd` de Juan, que sale igual). En el dibujo es una franja rayada "SOBREMEDIDA 52 ·
  se corta", también en la hoja del operario. El cruce con la nota de pedido acepta la medida con
  sobremedida (Metrix la carga así: 350 × 898 "SOBREMEDIDA (298)"). Automático en `armar_tanda.py`
  (`aplicar_sobremedida`); una pieza lo apaga con `"sobremedida": False`.
- **Detalle de herrajes**: cada OC tiene un desplegable con un dibujo de cada herraje distinto que usa,
  ampliado, con el borde del vidrio y sus cotas (profundidad y boca por cada borde que toca,
  agujeros con Ø, distancia al borde y entre ellos, radios distintos), como el detalle en círculo de
  los planos de los clientes (`cotas.svg_herraje`). No va en el plano de la pieza; en la hoja del
  operario se agrega tildando "Incluir detalle de herrajes".
- Vidrios espejo uno del otro (puerta de dos hojas): un solo `.wpd`, se da vuelta el vidrio;
  si tiene cara (satinado) va aviso.
- **Calado interior grande**: celdas de hasta ~160 (Juan eligió 170 para ahorrar tiempo) con
  rincones redondeados, en serpentina; cada corte arranca adentro de la celda que ya cayó y
  sobre el borde final la celda posterior sigue recta (si no queda una "uña"). Copiado de
  `REFERENCIA DE ENTRANTE-RECORTE GRANDE.wpd` de Juan. Falta confirmar en la máquina que
  respeta el orden de los Jobs.
- `ref_juan` en una pieza la compara contra un `.wpd` de Juan de otra OC (pedido repetido).

### Supervisión y hoja del operario (desde 2026-10-20)

`waterjet/supervision.py` arma, en la carpeta de red `\\192.168.130.210\Publico\22 - Mecanizados\`
(otro equipo, no la PC de Juan):
- `supervision.html`: los ítems que Juan ya marcó OK, OC por OC (cliente, obra y NP leídos de
  Metrix con un SELECT), plano del cliente al lado del plano cargado, para que jefe de planta y
  jefe de calidad los vean. **Sin firmas** (Juan, 2026-10-21: llevar esa cuenta no le corresponde
  a la oficina). Se probó firmar con archivos en la carpeta de red y no anda: Chrome no deja
  elegir carpetas de red (`showDirectoryPicker` → "The user aborted a request").
- **Lote**: la tanda es cuándo se cargaron los planos, no cuándo se mecanizan. Arriba se
  escriben (o tildan) las OC del lote que se mecaniza, de cualquier tanda, y se ve y se imprime
  solo eso; el lote queda en la dirección (`#lote=30363,30402`).
- `operario.html`: hojas para imprimir del lote. Por defecto **varias piezas por hoja**: dos
  filas por A4 apaisada, paradas como el plano, con cotas más grandes (`texto` de `cotas.py`,
  ~8 a 12 pt impresas). Sin recuadro ni firmas por pieza (Juan): el título de la hoja dice la
  OC (cliente, obra, vidrio) y cada plano solo "Ítem N × cant". O "1 por hoja", grande y
  **como queda en la mesa**. Con las dos primeras tandas: 45 ítems en 7 hojas.
- `planos\<tanda>\`: copia de los planos del cliente que usa la página.

Juan corrige antes de subir y carga él los `.wpd` en la máquina: la página no versiona ni
reparte archivos. La config (tandas subidas y, por tanda, qué ítems están aprobados) está fuera
de git en `wpds planos water jet\supervision.json`.

**Circuito de cada tanda (acordado el 21/10):** Juan pasa las OC → Claude baja los mails, **lee la
nota de pedido de cada OC en Metrix** (para numerar los ítems como Metrix y saber qué líneas son
mecanizadas), lee los planos y arma los `.wpd` + `revision.html` → `armar_tanda.py` **cruza cada
plano con su línea de la nota de pedido** (`nota_pedido.py`) → Juan marca bien / mal / duda y pega
"Copiar mis respuestas" en la sesión → Claude guarda ese texto en la tanda (`respuestas_juan.txt`) y
sube solo los OK; los MAL se corrigen, Juan los vuelve a revisar y se suben en la vuelta siguiente.

**Cruce con la nota de pedido** (`nota_pedido.py`, desde 2026-10-21; desde el mismo día con las **piezas vivas de `CAJAS`** primero, porque `PEDIDO3` es la nota de INGRESO y no ve los cambios: la 30390 sigue 1800 × 838 en `PEDIDO3` y sus piezas son 1780 / 1745; `CAJAS.MEC`: `*` no lleva, `X` hecho, vacío pendiente). De Metrix (solo lectura)
`PEDIDO1.OCOMPRA → TV_FACTU` y las líneas de `PEDIDO3` (cantidad `V_CANTIALT`, `LARGO × ANCHO`,
`CLASE` con "MEC", `NOTAS` "Item 8 - ESP 5 - C/FORMA", `ARTICULO.DESCRIPCION`), las mismas que
imprime la nota de pedido (verificado con la 12097). Cada ítem se compara por número de ítem,
medida (en cualquier sentido), cantidad y que la línea sea mecanizada; si no coincide, sugiere el
ítem de la NP que tiene esa medida. También lista las líneas mecanizadas sin plano. Las dos
páginas muestran ✓ / ⚠ por ítem y la nota de pedido de cada OC con sus líneas marcadas. Primer
caso real: el espejo de la 30306 se había armado como ítem 1 y es el ítem 8. Con las tres primeras
tandas marcó además 30333 (plano 1888 / NP 1880), 30390 (medida final que no se corrigió en
Metrix) y 30335 ítems 1-2 (ya no están en la NP).

Las páginas tienen **zoom con la ruedita** sobre el plano del cliente y el dibujo (arrastrar para
mover, doble clic vuelve), y se busca por OC o por número de NP (`pagina_comun.py`).

```
_work\venv\Scripts\python.exe waterjet\supervision.py --agregar --respuestas <tanda>\respuestas_juan.txt
_work\venv\Scripts\python.exe waterjet\supervision.py --agregar   (sube la tanda entera)
_work\venv\Scripts\python.exe waterjet\supervision.py             (regenera)
```

### Lista de planos pendientes (desde 2026-10-21)

`Planos_Pendientes.bat` (raíz) corre `waterjet/pendientes.py` y después `supervision.py`, y abre
`wpds planos water jet\planos_pendientes.html`. Pensado para correr a la mañana.
- Lee de Metrix (solo lectura) los pedidos cargados en los últimos `dias` (30) con alguna pieza
  mecanizada: con piezas en `CAJAS` manda el flag `MEC` (así no entran los "C/FORMA" que no van a
  la water jet); sin piezas todavía, la nota de ingreso (`PEDIDO3`, igual que `nota_pedido.py`).
- Por ítem dice dónde está su plano: en supervisión, en una tanda, en el SCAD, ya mecanizado
  (`MEC = X`) o **falta**. El SCAD es la carpeta de red de la water
  `\\192.168.130.234\waterjet\mecanizado\My Pieces\` (`2022\`, donde guarda Juan, "30344 - item 2.wpd",
  y `AlePlanos\`, "30377,2.wpd"); tiene más de 8600 `.wpd` desde 2022, así que se miran solo los
  tocados en los últimos 180 días. Si la PC de la water está apagada, esa parte se saltea.
- Busca el mail de cierre de cada OC en Gmail (solo lectura) y marca **"el mail no trae plano"**
  (o "solo imágenes") cuando la OC tiene mecanizado y el mail no adjunta plano: esas hay que
  pedírselas al cliente o al vendedor. Pausa entre consultas y reintento si Gmail limita.
- Se tilda a mano (queda en el navegador), filtro "Solo los que faltan", "Copiar OC que faltan"
  (para pasarlas como tanda).
- **Nunca borra**: acumula en `wpds planos water jet\planos_pendientes.json`; lo que tiene más de
  30 días no se muestra en la lista pero queda en "Archivo". Config en `pendientes_config.json`.
- `supervision.html` suma un desplegable "Pedidos en producción con mecanizado": cuáles ya tienen
  los planos cargados, cuáles se hicieron por fuera (SCAD / ya mecanizados) y a cuáles les faltan,
  ordenado por número de NP de Metrix, la más nueva arriba (Juan: es lo que más se usa).

## Cómo funciona (explicado para Juan)

La idea es **dividir el trabajo en dos**, para que cada parte haga lo que mejor hace:

```
 plano del cliente           Haiku (con el prompt)              armar_waterjet.py
 (PDF de CAD, foto,   ──►    "LEE" el plano y anota      ──►    "ESCRIBE" los archivos
  planilla escaneada)        lo que ve, en un JSON              con reglas fijas
                             (medidas, agujeros, dudas)         ├─ planilla para la Interfaz
                                                                ├─ un .wpd por pieza
                                                                └─ advertencias.txt
```

1. **Haiku lee, no decide.** El prompt le pide que anote, por cada vidrio: tipología,
   cantidad, ancho y alto, si tiene forma, y cada agujero con su Ø y sus dos cotas
   (horizontal: desde la izquierda o la derecha; vertical: desde arriba o abajo),
   **tal cual las acota el plano**. Si los agujeros forman un bloque regular, anota una
   **grilla** (primer agujero, paso, filas y columnas) en vez de cada uno; y cada **corte
   entrante** con su borde, posición, largo y profundidad. Si algo no está escrito (ej. el Ø), lo deja vacío
   y lo avisa; no inventa. No elige códigos ni clases de Metrix.
2. **El script aplica las reglas.** Con ese JSON, `armar_waterjet.py`:
   - arma el **código del vidrio** (`FL` + espesor + color, ej. `FL10IN`) y lo controla
     contra la lista de códigos float que existen;
   - pone **TIPO** (`TEMPLUX` si es templado), **CLASE** (`FLOAT PR MEC TEMP` si lleva
     perforaciones, `FLOAT PR TEMP` si no) y **OBS** (`C/PERF` con perforaciones,
     `P RECTO` sin). Casos que no conoce (crudo, otro canto) → los deja vacíos con aviso;
   - expande cada grilla en sus agujeros (la cuenta la hace el código, no el modelo);
   - arma cada entrante como recorrido del chorro (`Routing`), con la entrada y los
     rincones redondeados como los hace la fábrica;
   - escribe cada agujero en el `.wpd` en el idioma del SCAD: desde la izquierda → `201`,
     desde la derecha → `DX-106`, desde abajo → `106`, desde arriba → `DY-183`. Así el
     `.wpd` queda atado al mismo borde que usó el plano;
   - si el vidrio está **parado** en el plano, lo **acuesta hacia la derecha** para la mesa
     (ver abajo);
   - junta todas las dudas (de Haiku y propias) en `advertencias.txt`.
3. **Juan revisa** las advertencias y abre los `.wpd` en el SCAD antes de cortar. Los
   entrantes ya van en el `.wpd`; las otras formas (escalones, recortes de esquina) por
   ahora las agrega él a mano.

Por qué así: las reglas de Metrix y las cuentas en un programa no se equivocan ni
cambian de un día al otro; un modelo sí. Al modelo le queda solo lo que el programa
no puede hacer: mirar un dibujo y entenderlo.

### Uso

Desde PowerShell, en la carpeta del proyecto (`copia dir metrix`):

```
_work\venv\Scripts\python.exe waterjet\armar_waterjet.py <json> <plantilla> <carpeta salida> [opciones]
```

1. Pasarle a Haiku (Console/playground o API) el prompt + el plano; guardar la respuesta
   como `.json` en la carpeta del pedido.
2. Correr el script. Plantilla: `"C:\Users\geronimo.zanon\wpds planos water jet\Libro1.xlsx"`,
   o `-` para generar solo los `.wpd`.
3. Opciones: `--diametro 10` (Ø para los agujeros sin Ø en el plano; deja aviso),
   `--espesor 10` (DimZ, ej. laminado 5+5), `--nombre obra` (nombre de los `.wpd`
   si el plano no trae cliente; si no, usa el cliente o el Nº de pedido).
4. Leer `advertencias.txt` y abrir los `.wpd` en el SCAD (o mirar el dibujo:
   `_work\venv\Scripts\python.exe waterjet\dibujar_wpd.py <archivo.wpd> <salida.png>`).

Para **probar un cambio del prompt**: armar a mano la referencia JSON del plano (la lectura
correcta), correr el prompt con Haiku sin contexto **dos veces o más**, y medir:

```
_work\venv\Scripts\python.exe waterjet\comparar.py <referencia.json> <haiku_1.json> <haiku_2.json>
```

Y volver a pasar los planos anteriores, para no romper lo que ya andaba.

## El formato `.wpd` (Wps_S_Cad)

XML, UTF-8 sin BOM, fin de línea CRLF, sin salto final. Sacado del `.wpd` que Juan hizo a
mano para la pieza 1 de la prueba 1; el script lo reproduce idéntico (salvo fecha/usuario).

```xml
<DataObject xsi:type="Piece" Name="<nombre>" DimX="<ancho>" DimY="<alto>" DimZ="<espesor>">
  <Jobs>
    <Job xsi:type="Boring" XFormula="DX-106" YFormula="DY-183" D="38" Finish="false" />
    ...
  </Jobs>
  <Hardwares />
</DataObject>
```

- Origen **abajo a la izquierda**, X hacia la derecha, Y hacia arriba, cotas al centro del agujero.
- `DX`/`DY` = ancho/alto de la pieza (fórmulas del SCAD).
- `Boring` = agujero redondo pasante, `D` = Ø. `Finish="false"` copiado del ejemplo (sin
  saber todavía qué cambia en `true`).
- Todavía **no sabemos** cómo guarda el SCAD un recorte de esquina/escalón ni otros
  mecanizados (avellanado, calado) ni qué es `<Hardwares />`. Con un `.wpd` de ejemplo
  hecho a mano de cada uno se agrega (así se hizo con los entrantes, abajo).

### Cortes entrantes (Job `Routing`, desde 2026-10-16)

Sacado de `REFERENCIA DE ENTRANTE.wpd`, que Juan hizo en el SCAD: un entrante de 150 × 45
en el borde de abajo de una pieza de 500 × 500. El script la reproduce idéntica.

```xml
<Job xsi:type="Routing" JetCorrection="C" IsClosed="false" Finish="N">
  <Name />
  <Vertices X="145" Y="-5"  Bulge="0.41421356237309509" />   <!-- arranca 5 afuera del vidrio -->
  <Vertices X="150" Y="0"   Bulge="0" />                     <!-- entra en el borde -->
  <Vertices X="150" Y="35"  Bulge="-0.41421356237309509" />  <!-- rincón radio 10 -->
  <Vertices X="160" Y="45"  Bulge="0" />
  <Vertices X="290" Y="45"  Bulge="-0.41421356237309509" />  <!-- rincón radio 10 -->
  <Vertices X="300" Y="35"  Bulge="0" />
  <Vertices X="300" Y="0"   Bulge="0.41421356237309509" />   <!-- sale con arco radio 5 -->
  <Vertices X="305" Y="-5"  Bulge="0" />
</Job>
```

- Es una **cadena de puntos** (el recorrido del chorro). `Bulge` dice cómo se llega al
  punto SIGUIENTE: `0` = recta; `0.414…` = tan(90°/4) = arco de 90°; `+` antihorario,
  `−` horario (la misma convención que DXF). Coordenadas absolutas en mm (sin `DX`/`DY`).
- Práctica de la fábrica (Juan): el chorro **entra desde afuera** con un arquito (radio 5,
  arranca 5 mm afuera y 5 mm antes) tangente al corte, y los **rincones de adentro** van
  redondeados (radio 10). Es el **convenio actual para templado** (Juan, 2026-10-16; se
  puede cambiar si se acuerda otro). El script usa esos valores para todo entrante; si el
  entrante es más chico que el radio, lo achica y avisa.
- El script arma cada entrante como si estuviera en el borde de abajo (igual que la
  referencia) y lo **gira** al borde que toque; girar no cambia el sentido de los arcos.
- Van **después** de los agujeros en `<Jobs>`, pero da igual: **la máquina decide** qué
  perforar o cortar primero (Juan, 2026-10-16).
- El sentido del recorrido tampoco importa: en el plano foto unos arrancan por la izquierda
  y otros por la derecha, y se perforó bien.
- `JetCorrection="C"`, `IsClosed="false"`, `Finish="N"` copiados de la referencia sin
  saber todavía qué significan las otras opciones.
- Para revisar a ojo sin abrir el SCAD: `waterjet\dibujar_wpd.py <archivo.wpd> <salida.png>`
  dibuja la pieza, los agujeros y los recorridos con sus arcos.

### Vidrio acostado (decisión de Juan, 2026-10-15)

En la mesa el vidrio va **acostado** (lado largo horizontal). Si el plano lo dibuja parado
(alto > ancho), el `.wpd` lo gira **90° hacia la derecha** (horario): el borde de arriba
del plano queda a la **derecha**, que es donde la máquina arranca a perforar. Los
agujeros que en el plano estaban a 70 de arriba quedan a 70 del borde derecho.

**Es una rotación, no un espejo.** Intercambiar X e Y de cada agujero "a secas" da la
pieza espejada, que en un laminado con cara (ej. cover glass) deja los agujeros mal. El
script cambia de qué borde se mide cada cota (arriba→derecha, derecha→abajo,
abajo→izquierda, izquierda→arriba) y el número queda igual. Verificado: deshaciendo
el giro, los 112 agujeros de la prueba 2 vuelven exactos a su lugar en el plano; el
espejo no.

La planilla de la Interfaz queda con ancho y alto como en el plano.

## Pruebas hechas

Método: yo (Claude) armo una **referencia** del plano por mi cuenta, después un agente
**sin contexto** sigue el prompt sobre el plano (solo leer el plano y escribir el JSON, sin
código), y se compara agujero por agujero (posición absoluta en mm). Juan controla los
`.wpd` en el SCAD contra el plano.

| | Prueba 1 (2026-10-14) | Prueba 2 (2026-10-15) |
|---|---|---|
| Plano | PDF de CAD (vectorial) | Foto (jpeg) de una planilla de toma de medidas |
| Vidrio | 8 templados 10 mm incoloro, bordes pulidos | 1 laminado 5+5 (cover glass + PVB + float), con cortes entrantes |
| Agujeros | 32 (4 por pieza, Ø38), cotas distintas a izq/der y arriba/abajo | 112 en grilla (8 filas × 14, paso 40), sin Ø escrito |
| Dificultad | 1 pieza con escalón: un agujero acotado desde el escalón | casi nada acotado uno por uno: hay que reconstruir la grilla con el paso |
| **Haiku** | **8/8 piezas, 32/32 agujeros** | **112/112 agujeros** |
| **Opus** | — | **112/112 agujeros** (mejores avisos) |
| Validación de Juan | Los 8 `.wpd` contra el SCAD: "más que joyas" | Ø real = 10 (el plano no lo decía) |

Lo que aprendimos:
- **Haiku alcanza** para leer planos de este tipo, también fotos. No inventó el Ø que
  faltaba; lo dejó vacío y avisó.
- **Opus avisa mejor** (ej. el paso entre dos filas que no está escrito, agujeros tachados
  que son marca de cota). Para planos dudosos puede valer la pena usarlo o pedirle a Haiku
  esos avisos.
- **El ejemplo del prompt no puede tener números del plano de prueba**: en la primera
  corrida pasó y "ayudó" a Haiku con la pieza difícil. Se corrigió y se volvió a probar.
- En **planos de CAD** el PDF trae la geometría exacta: se puede medir por código
  (`pdfplumber`) para controlar las cotas (en la prueba 1 coincidieron todas). Ojo:
  una cota escrita puede no coincidir 1 a 1 con el dibujo (prueba 1: 172 escrito, ~171
  dibujado); manda la escrita, con aviso.
- Detalles de cabecera: Haiku a veces deja "CLIENTE:" en el nombre (el script lo limpia,
  los `:` no van en nombres de archivo); hay planos sin campo cliente (`--nombre`).

### Prueba 2b: entrantes y grillas (2026-10-16)

Mismo plano foto de la prueba 2, con el prompt ampliado (entrantes + grillas).

| Corrida | Agujeros | Entrantes (3) | Qué pasó |
|---|---|---|---|
| v2 (solo entrantes, agujeros uno por uno) | **3**/112 | ✅ 3/3 | Listó solo los 3 agujeros acotados y avisó "lista INCOMPLETA" → por eso se agregaron las grillas |
| v3 A (con grillas) | ✅ 112/112 | ✅ 3/3 | Perfecta |
| v3 B (con grillas) | 56/112 | ✅ 3/3 | Dejó sin origen horizontal la grilla de abajo (no está acotada en el plano); el script la descartó con aviso. → regla nueva: un bloque **alineado** con otro acotado usa su cota |
| v4 (con regla de alineación) | ✅ 112/112 | ✅ 3/3 | Perfecta, explicó la alineación en advertencias |

Control de que no se rompió lo anterior: el plano CAD de la prueba 1 con el prompt v4 →
8/8 piezas, 32/32 agujeros, sin grillas ni entrantes falsos (el recorte de esquina de la
pieza 7 quedó, bien, como forma y no como entrante).

Lecciones: (1) pedirle a Haiku que liste muchos agujeros iguales uno por uno no es
confiable; describir el patrón y que el código lo expanda, sí. (2) Correr la **misma
prueba más de una vez**: dos corridas iguales dieron resultados distintos. (3) Otra vez
se colaron números del plano de prueba en el ejemplo del prompt; se corrigió antes de
probar. Revisar siempre eso.

## Pendiente

- **Formas**: los entrantes ya están (Juan los revisa en el SCAD). Faltan los recortes
  de esquina/escalones → falta un `.wpd` de ejemplo hecho en el SCAD. Hoy: rectángulo
  envolvente + aviso, Juan lo acomoda a mano.
- **Herrajes en el programa automático** (en las tandas ya se cargan; ver arriba): la idea
  es que Haiku solo nombre lo que dice el plano y un **catálogo** en Python decida el `.whd`,
  su origen y su orientación, armado con los `.wpd` viejos de Juan. Antes (2026-10-16):
  en el SCAD los herrajes se cargan como **hardware** (`<Hardwares />`) y
  ya traen sus propios radios y mecanizado: solo hay que **posicionar el herraje** (Juan,
  2026-10-16). Idea charlada para reconocerlos (todavía sin hacer): Haiku agrupa y describe
  la "huella" de cada herraje (cuántos agujeros, Ø, separación, destaje, posición) y el
  código la cruza con (1) lo escrito en el plano, (2) los herrajes y cantidades del
  **presupuesto** de ese plano y (3) un catálogo de huellas de los ~10 herrajes más usados
  (Metrix tiene 124 artículos en la familia HERRAJES, con códigos estándar D1, D2, D16,
  P1, P5, P63, M300...). Falta: un `.wpd` con un herraje insertado en el SCAD (para ver qué
  va en `<Hardwares>`), el catálogo/plantillas del proveedor, y 5-10 planos viejos con
  herrajes y su Nº de presupuesto. También: cómo se cargan los herrajes en la planilla/Metrix.
- **Más tipos de planos**: a mano, otros CAD, varios vidrios por foto. Armar un set de
  prueba con planos reales y sus `.wpd` correctos para medir cada cambio del prompt.
- **Laminados en la planilla**: las reglas de código/clase hoy cubren solo float templado
  con canto pulido; lo demás sale vacío con aviso.
- Conectarlo al orquestador: que el JSON salga del "pedido interpretado" del expediente.
