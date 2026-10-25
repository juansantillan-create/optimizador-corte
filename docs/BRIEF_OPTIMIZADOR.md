# Brief: optimizador de corte de vidrio (reemplazo de Corte Certo para cotizar)

Escrito el 21/10/2026 con Juan, a partir de sus capturas de Corte Certo, la planilla de medidas
de hojas, las reglas de corte que pasó con Lucas y la documentación de la fábrica. Es la
especificación de este repo: si algo de acá choca con la realidad (los datos, una captura, una
respuesta de Juan), gana la realidad. Anotá el cambio en `docs/DECISIONES.md` y corregí este
archivo.

---

## 0. En una frase

Un programa local (Windows, Python) que, dado un listado de piezas de vidrio, calcula cuántas
planchas hacen falta, cómo se acomodan (montajes) y el aprovechamiento, **con la misma
configuración, los mismos números y las mismas pantallas que Corte Certo v3.9K**. Se valida
contra cientos de casos viejos en los que quedó anotado lo que dio Corte Certo.

## 1. Por qué

- Hoy la oficina usa **Corte Certo v3.9K** solo para tener un panorama de cómo "da" la
  optimización y **cotizar** en base a eso. La optimización real y el envío a las mesas de corte
  los hace **Optima** en producción (una mesa automática para float y otra para laminado, por
  guillotina). Esto no cambia.
- Juan quiere un optimizador propio **solo para cotizar**: calcular y acomodar los vidrios en
  planchas, con pocas configuraciones (distancia al canto y entre piezas), sin etiquetas ni envío
  a mesas.
- Además tiene que poder **automatizarse**. En la fábrica se está armando un orquestador que
  lleva cada pedido del mail a producción (`contexto/fabrica/VISION_ORQUESTADOR.md`). Ahí el
  optimizador figura como "por hacer": *"solo acomodar rectángulos en hojas con 2 parámetros por
  tipo de hoja (distancia al borde y entre piezas) → hojas, aprovechamiento y esquema"*. En el
  "portón de producción", el comercial controla el **consumo de hojas** y de dónde salió
  (`contexto/fabrica/EXPEDIENTE_PEDIDO.md`). O sea, además de la pantalla hace falta una función
  y un JSON.
- Se desarrolla en la nube con Claude y después **corre todo local** en la PC de la oficina.

## 2. Alcance

**Entra**
- Motor de optimización 2D por **guillotina**:
  - varios materiales;
  - varias medidas de plancha por material;
  - rotación y textura;
  - la configuración por material de Corte Certo, más las reglas de Cristalux (corte banda y
    separación).
- **Informe de cálculo** y **Visualizar e imprimir montajes** como los de Corte Certo, impresos
  en A4.
- **Interfaz local** en el navegador: materiales, proyecto (piezas), calcular (con progreso),
  resultados e imprimir.
- **Importar piezas**: pegar desde Excel, CSV/XLSX y la planilla de la Interfaz de Metrix.
- **Banco de validación**: contra casos históricos (lo que dio Corte Certo) y contra casos
  sintéticos con óptimo conocido.
- **CLI + función de Python + JSON**, para el orquestador.

**No entra (por ahora)**
- Enviar a mesas de corte, etiquetas, códigos de barra.
- Stock real de planchas y retazos.
- Formas no rectangulares (se usa el rectángulo que las envuelve, con aviso).
- Conectarse a Metrix, mainque o Gmail.
- Portal web o acceso desde otras PC (más adelante).

## 3. Qué hay en este repo (los ~25 archivos)

| Dónde | Qué es | Para qué te sirve |
|---|---|---|
| `docs/img/corte_certo_*.png` (4) | Capturas reales de Corte Certo | **Lo que hay que replicar**. Miralas (se pueden leer como imagen). Descripción en `docs/CORTE_CERTO.md` |
| `config/fuentes/Medidas_hojas.xlsx` | Planilla de Juan: medidas de cada plancha por código de Metrix + corte banda | **Fuente de las planchas**. Ya convertida a `config/hojas.csv` |
| `config/fuentes/reglas_corte_2026-10-21.txt` | Reglas de corte de Lucas (texto original) | **Fuente de la separación entre piezas**. Ya pasada a `config/reglas_corte.csv` |
| `contexto/fabrica/*.md` + `mapa_orquestador.html` (15) | Documentación de la fábrica: Metrix, glosario, orquestador, precios, water jet… | Contexto. **Cuáles leer enteros y cuáles solo consultar: `contexto/LEEME.md`** |
| `datos/casos/` | Casos históricos exportados de Metrix (puede estar vacío al principio) | **Validación**. Formato: `docs/CONTRATO_DATOS.md` |

Si aparece un archivo que no está en esta tabla (por ejemplo, Juan adjuntó algo en el mensaje):
1. Abrilo y clasificalo.
2. Guardalo donde corresponde según esta tabla.
3. Anotalo en `docs/INVENTARIO.md`.

Si tiene nombres de clientes, va a `datos/privado/`, que no va a git.

## 4. Corte Certo: qué hay que replicar

Detalle completo, campo por campo, en **`docs/CORTE_CERTO.md`**. En resumen:

1. **Material → Propiedades físicas**:
   - ancho de la sierra y ancho mínimo de destaque;
   - retazos: sí/no, ancho y largo mínimos, área mínima;
   - rotación permitida y textura;
   - constante que se suma a las piezas;
   - espesor y peso específico;
   - 4 márgenes de seguridad de la plancha;
   - máximo tamaño cortado (guillotinas).

   Más las pestañas "Descripción" y "Propiedades comerciales", de las que todavía no hay captura.
2. **Proyecto**: código, descripción y lista de piezas (material, cantidad, ancho, largo).
3. **Cálculo en proceso**: material que se está calculando, tiempo de cálculo, estimado y
   restante, torta con el %, "Montaje NNN".
4. **Informe de cálculo**: proyectos calculados, lista de materiales (piezas, m² de piezas,
   layouts, planchas, m² de planchas, aprovechamiento), planchas usadas (cantidad, ancho, largo,
   tipo) y perímetro de piezas.
5. **Visualizar e imprimir montajes**:
   - recuadro "Datos generales": cantidad de montajes, total de chapas, aprovechamiento y pérdida;
   - una miniatura por montaje, **apilada** cuando se repite en varias planchas;
   - piezas en color y sobrante en amarillo;
   - detalle e impresión.

**Caso de referencia (captura 1 y 2):**
- Proyecto 413: 252 piezas de "5 mm Incoloro" = 564,583068 m².
- Resultado: **13 montajes y 82 planchas** de 3580 × 2500 = 733,9 m²; aprovechamiento
  **76,93 %**, pérdida 23,07 %; perímetro de piezas 1630,22 m.
- Las cuentas cierran: 82 × 3,58 × 2,5 = 733,9 y 564,583068 ÷ 733,9 = 76,93 %. No hay lista de
  piezas, así que sirve para el **formato** y las **fórmulas**, no para comparar el acomodo.

## 5. Configuración de corte de Cristalux

### 5.1 Planchas (`config/hojas.csv`, sale de `Medidas_hojas.xlsx`)

- 101 medidas de plancha para 87 códigos de Metrix: 66 monolíticos y 35 laminados.
- 10 materiales tienen más de una medida. Por ejemplo, FL4IN tiene 3600 × 2500, 3600 × 2200 y
  3300 × 2440, y FL10IN tiene 3700 × 2500, 3700 × 2200 y 3050 × 2050.
- **Corte banda**: se resta del **lado largo**. Una plancha de 3600 × 2500 queda útil en
  3580 × 2500 (20 mm), 3570 (30 mm) o 3550 (50 mm), según el espesor. Así está cargado Corte
  Certo: la plancha figura como 3580 × 2500.
- Para regenerar el CSV: `python herramientas/importar_medidas_hojas.py`. El Excel tiene
  invertidas Descripción y Código en la hoja LAMINADO; el script lo detecta.
- Material que no está en `hojas.csv`:
  - aviso claro;
  - opción de usar una plancha por defecto según el espesor (3600 × 2500 con la banda de la
    regla), marcada como **supuesta** en el informe.

### 5.2 Separación entre piezas (`config/reglas_corte.csv`, regla de Lucas del 21/10/2026)

| Grupo | Corte banda | Separación entre piezas | Estado |
|---|---|---|---|
| Float 4/5/6 mm | 20 | 20 | confirmado |
| Float 8 mm | 30 | 30 | confirmado |
| Float 10 mm | 50 | 50 | confirmado |
| Laminado 3+3 | 20 | 20 | confirmado |
| Laminado 4+4 | 30 | **20** | confirmado (no es error) |
| Laminado 5+5 | 50 | 50 | confirmado |
| Float 3 mm, 5+3, 6+6 y los vidrios que no son float/Lamilux | según el espesor | según el espesor | **supuesto** (está en `hojas.csv`, columna `separacion_fuente`) |

### 5.3 Dos configuraciones de fábrica ("presets") + todo editable

Juan cree que en Corte Certo **solo se usa la distancia al canto**: la plancha cargada ya
achicada a 3580, **sin** separación entre piezas. La captura de Propiedades físicas lo confirma:
sierra 0, destaque 0, constante 0, márgenes 0. La separación de 20/30/50 sería la regla de
producción. Juan pidió que el programa pueda trabajar **"con esa configuración o cambiándola"**.
Por eso:

- **Preset "Como Corte Certo hoy"** (por defecto): corte banda del Excel, separación 0,
  destaque 0, rotación sí, textura sin.
- **Preset "Reglas de corte (Lucas)"**: corte banda + separación de `reglas_corte.csv`.
- **Cada material se puede editar** campo por campo, como en Corte Certo. Los cambios locales no
  se pierden al actualizar el programa.
- El informe dice siempre con qué preset y qué valores se calculó.

### 5.4 Hipótesis que decide la validación histórica

No sabemos con qué configuración exacta se calcularon los casos viejos. El banco de validación
(§10) tiene que probar estas hipótesis y decir **cuál reproduce mejor lo que dio Corte Certo**,
por grupo de material:

| | Hipótesis |
|---|---|
| H0 | Solo corte banda (lo que muestra la captura) |
| H1 | Corte banda + separación como "ancho de la sierra" (todas las piezas separadas) |
| H2 | Corte banda + separación como "destaque mínimo" (las piezas pueden compartir corte, pero un sobrante entre dos piezas tiene que medir 0 o al menos X) |
| H3 | Las anteriores + **3 mm** en las piezas con pulido recto |

Sobre H3: según Juan, *"las medidas de la planilla son las de corte, salvo pulido recto, que
suma 3 mm"*. Falta confirmar si es en las dos medidas y si se cargaba así en Corte Certo.

## 6. El motor

### 6.1 Modelo

- **Pieza**: ítem, material, ancho, largo, cantidad, rota (sí/no; por defecto lo que diga el
  material), descripción, origen (presupuesto/renglón, opcional) y "sobremedida" opcional.
- **Material**: los campos de Propiedades físicas de Corte Certo + corte banda + lista de
  planchas (medidas, habilitada sí/no, prioridad).
- **Plancha útil** = plancha − corte banda (lado largo) − márgenes de seguridad.
- **Cortes de guillotina**: cada corte va de lado a lado del pedazo que se está cortando, que es
  como se corta el vidrio. Etapas (corte X, después Y, después Z…): configurable. Por defecto,
  sin límite, salvo que la validación muestre que Corte Certo se comporta como 2 o 3 etapas.
- **Separación como sierra**: equivale a agrandar cada pieza y la plancha útil en la
  separación s. Con n piezas en fila hay que cumplir n·a + (n−1)·s ≤ A, que es lo mismo que
  n·(a+s) ≤ A+s. Así no se la cobra contra los bordes.
- **Destaque mínimo d**: ningún sobrante entre 0 y d (sin incluir el 0) que haya que separar
  con un corte. 0 = no se controla.
- **Constante**: se suma a las medidas de cada pieza del material antes de acomodar.
- **Textura** horizontal/vertical: la pieza no rota y su largo va en la dirección de la veta.
- **Máximo tamaño cortado** (si está "Limitado"): ningún corte más largo que ese valor. Es poco
  común; implementalo al final o como verificación con aviso.

### 6.2 Qué se optimiza (en este orden)

1. Menos **m² de plancha** (con una sola medida, es lo mismo que menos planchas). Si hay varias
   medidas habilitadas, se pueden mezclar, salvo que la configuración diga otra cosa.
2. Menos **montajes distintos**: a la oficina y a la mesa les conviene repetir. Corte Certo lo
   muestra apilado.
3. **Sobrante aprovechable** lo más grande y rectangular posible, juntado en la última plancha.
4. **Tiempo**:
   - una primera solución en pocos segundos;
   - después mejora hasta el tope, mostrando progreso (como "Cálculo en proceso");
   - el tope se mide por **cantidad de trabajo** (iteraciones), no solo por reloj, para que el
     mismo caso dé lo mismo en la nube y en la PC de Juan. El reloj es solo un límite de
     seguridad.

### 6.3 Cómo encararlo (sugerencia con razones; si encontrás algo mejor, usalo y explicalo)

- **Agrupar** las piezas iguales en tipos con su cantidad. Los presupuestos suelen tener muchas
  repetidas.
- **Generar montajes** con programación dinámica de guillotina por etapas, al estilo
  Gilmore–Gomory:
  - tiras con el alto de alguna pieza;
  - adentro de cada tira, pilas y piezas (mochila 1D);
  - las tiras se apilan en la plancha (otra mochila 1D);
  - probar las dos orientaciones de la plancha.

  Es barato y produce montajes "de vidriero". La guillotina sin límite de etapas por puntos de
  grilla es más cara en Python: dejala para el final, si hace falta.
- **Elegir cuántas veces se usa cada montaje** con programación lineal entera: cubrir la
  cantidad de cada pieza con la menor cantidad de m² de plancha. Hacelo con generación de
  columnas: la relajación lineal da precios para cada tipo de pieza, que se usan como valores
  para generar montajes mejores. `scipy.optimize.linprog`/`milp` (HiGHS) ya viene con scipy y
  da los precios duales. Esto produce naturalmente "13 montajes × repeticiones = 82 planchas",
  como Corte Certo.
- **Exactitud**:
  - la solución entera tiene que dar **exactamente** las cantidades pedidas;
  - las piezas de más de un montaje se sacan (quedan como sobrante), aunque eso agregue un
    montaje distinto;
  - el resto que quede se acomoda con una heurística (búsqueda en haz o *greedy* de guillotina).
- **Heurística rápida de respaldo**, siempre disponible: da algo en menos de 2 s y es el piso si
  el resto falla o se corta.
- **Cota inferior**:
  - ⌈Σ área de piezas ÷ área útil⌉, más las piezas grandes que no pueden compartir plancha;
  - se informa como "mínimo teórico";
  - la cota de la relajación lineal vale solo para la familia de montajes generada: usala como
    diagnóstico interno, no la muestres como mínimo.

### 6.4 Validador geométrico independiente (obligatorio)

Un módulo aparte, de código simple, que **no comparte lógica con el motor** y revisa cada
resultado antes de devolverlo:
- toda pieza adentro de la plancha útil;
- sin solaparse;
- separación respetada;
- destaque respetado;
- la plancha se puede cortar por guillotina (descomposición recursiva);
- rotación solo si se permite;
- textura respetada;
- **cantidades exactas**: ni una pieza de más ni de menos;
- los m² y el aprovechamiento recalculados por su cuenta coinciden con los informados.

Se usa en todos los tests (incluidos tests con instancias al azar) y en cada cálculo de la
interfaz. Si falla, el resultado no se muestra como bueno: se muestra el error.

### 6.5 Rendimiento (PC de Juan: Windows, poca RAM, CPU común)

| Caso | Meta |
|---|---|
| Presupuesto típico: ≤ 300 piezas y ≤ 30 medidas distintas por material | primera solución en < 2 s; final en ≤ 10 s |
| Grande: ≤ 2.000 piezas | ≤ 60 s, con progreso |
| Memoria | < 500 MB en el peor caso |

Medí en la nube y anotá la máquina, porque la PC de Juan es más lenta. Dejá un comando de
*benchmark* para que Juan lo corra en su PC.

### 6.6 Casos borde que tienen que estar cubiertos (con test)

- Pieza que no entra en ninguna plancha del material: error claro por pieza ("no entra en
  ninguna plancha de FL10IN: 3700 × 2600").
- Pieza que entra solo girada en un material sin rotación.
- Cantidad 0, medidas 0 o negativas, material vacío o desconocido.
- Material sin planchas en la configuración: aviso, y se calculan los demás materiales.
- Pieza del mismo tamaño que la plancha útil.
- Muchísimas piezas iguales (ej. 300 de 500 × 500).
- Piezas más chicas que el destaque.
- Separación > 0 con piezas que llenan justo la plancha.
- Varias medidas de plancha en el mismo material.

## 7. Salidas

### 7.1 Informe de cálculo (igual a Corte Certo)

Fecha y hora, y después:
- **Proyectos calculados**: código, descripción, piezas, código del material.
- **Lista de materiales**: código, descripción, piezas, m² de piezas, layouts, planchas, m² de
  planchas, aprovechamiento.
- **Planchas / offcuts usados**: cantidad, ancho, largo, tipo (Plancha / Offcut).
- **Perímetro de piezas** (m).
- **Cálculo especial de perímetro** (m): no sabemos qué es; dejalo en 0,00 con la pregunta
  abierta.

Fórmulas (las de Corte Certo, verificadas con el caso 413):
- m² de piezas = Σ ancho × largo × cantidad ÷ 10⁶, con **6 decimales** (564,583068). Son las
  medidas del proyecto, antes de sumar constantes.
- m² de planchas = planchas × área **útil** (733,9).
- Aprovechamiento = m² piezas ÷ m² planchas × 100, con 2 decimales. Pérdida = 100 − eso.
- Perímetro = Σ 2 × (ancho + largo) × cantidad ÷ 1000, con 2 decimales.

Agregados propios (marcados como tales, para no confundir con Corte Certo):
- **mínimo teórico** de planchas;
- **m² de hoja entera** (3600 × 2500, lo que se compra);
- **peso** (kg);
- **preset** y valores usados;
- **avisos**.

### 7.2 Montajes

- **Dibujos en SVG**: nítidos al imprimir y livianos.
- **Miniaturas** en grilla. Un montaje que se repite se dibuja **apilado**, con contornos
  corridos como pila de chapas, y con "×N" visible (en Corte Certo hay que pasar el mouse).
- **Colores**:
  - en las capturas, las piezas son bordó, verde y oliva, y el sobrante amarillo;
  - no sabemos qué distingue bordó, verde y oliva (pregunta 5). La hipótesis "verde = girada,
    oliva = retazo" no cierra con la captura (25/10). Regla propia por defecto: un color por tipo
    de pieza con la misma paleta, sobrante en amarillo;
  - los colores van en **un solo lugar** del código, para cambiarlos fácil.
- **Detalle de un montaje**:
  - medidas de cada pieza y número de ítem adentro del rectángulo;
  - sobrantes con sus medidas;
  - cortes numerados en orden (primero los de lado a lado de la plancha);
  - repeticiones y lista de piezas.
- **Impresión** A4 apaisada, por CSS de impresión del navegador ("Imprimir" o "Guardar como
  PDF"):
  - el informe;
  - todos los montajes (varios por hoja);
  - o uno por hoja, grande.

### 7.3 JSON para el orquestador (y la CLI)

Entrada (ejemplo):
```json
{
  "proyecto": {"codigo": "413", "descripcion": "PRJ 413"},
  "preset": "corte_certo",
  "piezas": [
    {"item": "1", "material": "FL5IN", "cantidad": 4, "ancho": 1200, "largo": 2400,
     "rota": true, "descripcion": "", "origen": {"presupuesto": 11580, "renglon": 3}}
  ],
  "materiales": {"FL5IN": {"separacion_piezas_mm": 0}},
  "opciones": {"esfuerzo": "normal"}
}
```

Salida:
- `informe` con los mismos campos que el de la pantalla, por material;
- `montajes`: cada uno con material, número, repeticiones, plancha, piezas (x, y, ancho, largo,
  ítem, girada), sobrantes (tipo retazo/desperdicio) y secuencia de cortes;
- `avisos`;
- `verificado: true/false` (el validador);
- versión del programa y configuración usada.

Documentarlo en `docs/API.md` con un ejemplo completo. La función de Python
(`optimizador.optimizar(...)`) recibe y devuelve lo mismo, sin estado global, para que el
orquestador la pueda importar.

### 7.4 Exportar

- CSV/XLSX con el consumo por material: material, medida de plancha, planchas, m², montajes y
  aprovechamiento.
- Opcional, si sale fácil: el proyecto en el formato que importa Corte Certo, para compararlos
  lado a lado durante la transición.

## 8. Interfaz local

- **Arranque**: doble clic en `Abrir_Optimizador.bat`, como los `.bat` que ya usa Juan:
  - crea el venv si no existe e instala dependencias;
  - levanta el servidor en `127.0.0.1:8520`;
  - abre el navegador.
  
  Cerrar esa ventana apaga el programa. Nada de servicios de Windows ni de permisos de
  administrador.
- **Tecnología sugerida**: FastAPI + HTML/JS sin compilar (sin npm) + SVG.
  - Da control total del aspecto, para que se parezca a Corte Certo, y CSS de impresión.
  - Es liviano en RAM.
  - FastAPI ya se usa en la fábrica.
  
  Si elegís otra cosa, justificalo.
- **Pantallas**, con los mismos nombres y el mismo orden de datos que Corte Certo, para que la
  oficina se sienta en casa:
  1. **Materiales**:
     - lista (código, descripción, color);
     - pestañas Descripción / **Propiedades físicas** (idéntica a la captura 4) / Propiedades
       comerciales (provisoria);
     - planchas del material;
     - botón de preset.
  2. **Proyecto**:
     - código, descripción y grilla de piezas;
     - pegar desde Excel e importar (§9);
     - guardar y abrir (archivos JSON en `proyectos/`, que no va a git).
  3. **Calcular**: pantalla "Cálculo en proceso" (captura 3), con cancelar.
  4. **Resultados**:
     - Informe de cálculo (captura 1);
     - "Elija el material para visualizar";
     - **Visualizar e imprimir montajes** (captura 2), con el recuadro negro de Datos generales
       y sus números en color.
  5. **Comparar** (nuevo): un caso histórico o un resultado de Corte Certo cargado a mano, al
     lado de nuestro resultado.
- **Aspecto**: limpio y actual, pero reconocible:
  - mismas etiquetas;
  - recuadros negros con números en color en Datos generales y en el progreso;
  - amarillo para el desperdicio;
  - miniaturas apiladas.
  
  Números con punto decimal como Corte Certo (para comparar), con opción de coma.

## 9. Entradas e importadores

- **Pegar desde Excel** (texto separado por tabulaciones): detectar columnas por encabezado
  (material, cantidad, ancho, largo, descripción) o por posición, con vista previa antes de
  aceptar.
- **CSV / XLSX** genérico, con las mismas columnas.
- **Planilla de la Interfaz de Metrix** (`.xls` Excel 97, solo Hoja1).
  - Columnas fijas de la A a la P: TIPO, VIDRIO1, CAMARA, VIDRIO2, ANCHO, LARGO, …, CLASE, CLASE
    CARA1, CLASE CARA2, OC. La posición exacta de cada una hay que confirmarla con una planilla
    real sin nombres (pregunta abierta).
  - Un **DVH** son 2 vidrios: una pieza de VIDRIO1 y otra de VIDRIO2.
  - Los **herrajes** se cargan con TIPO = DIST, LARGO = 1 y el código del herraje en VIDRIO1: se
    ignoran, con aviso.
  - Clase con "PR": sobremedida de pulido según la configuración (H3).
- **Casos históricos** (`datos/casos/`), para el banco y para la pantalla Comparar.
- Siempre: los materiales que no están en la configuración y las medidas raras se muestran como
  aviso **antes** de calcular.

## 10. Validación contra la historia (el corazón)

Detalle de los datos en `docs/CONTRATO_DATOS.md`. Resumen: casos de Metrix con las piezas de
cada presupuesto y, en las notas, la "leyenda" con lo que dio Corte Certo. Lo más probable es que
esté en `PRESUP.TV_DESCRIP` (ver `contexto/fabrica/DATA_DICTIONARY.md`), pero hay que
verificarlo. **Son muchos casos**: es la mejor herramienta que tenemos para que el programa sea
confiable.

**Si `datos/casos/` está vacío**:
- armá todo el banco igual, con un caso de juguete **claramente inventado**;
- dejalo listo para correr cuando lleguen los datos;
- no te frenes.

### 10.1 Leer la leyenda (sin adivinar)

1. Buscar los textos con pinta de optimización: "hoja", "plancha", "chapa", "aprov", "%",
   "3600", "x 2500", "layouts", "montajes".
2. Agruparlos por formato y escribir un lector tolerante por formato.
3. **Medir la cobertura**: cuántos se leen, cuántos no y por qué.
4. Guardar ejemplos de lo que no se entiende.

Puede haber varios materiales por presupuesto, planchas de distintas medidas, texto mezclado con
otras cosas (cotización del dólar, condiciones) o leyendas desactualizadas (el presupuesto
cambió después). Escribí `docs/FORMATO_LEYENDAS.md` con ejemplos reales anonimizados de cada
formato. Si un formato es ambiguo, a `PREGUNTAS_ABIERTAS.md` con 3 ejemplos.

### 10.2 Reconstruir lo que se optimizó

- **Piezas**: de `DETPRES2` (vidrio con medidas; `V_CANTIALT` = piezas). Los **DVH** salen de
  `DETPRES` (`ART1` y `ART3` = los dos vidrios, `V_CANTI` = unidades). En los escalonados, el
  segundo vidrio puede medir distinto (casi nunca).
- **No se optimizan**: herrajes, fletes, perforaciones, consumibles ni cámaras.
- **Material** = código de Metrix → `config/hojas.csv`.
- **Control de que la entrada está bien**: si la leyenda trae los m² de piezas (Corte Certo los
  da con 6 decimales), compararlos con los reconstruidos:
  - si coinciden exacto, la entrada está bien;
  - si no, dicen si se cargó con sobremedida (+3 mm) o si el presupuesto cambió después.
  
  Los casos que no cierran se informan aparte, no se mezclan con los buenos.

### 10.3 Comparar y calibrar

- Por caso y material: planchas nuestras contra planchas de Corte Certo, aprovechamiento,
  montajes y mínimo teórico.
- **Calibración**:
  - correr H0–H3 sobre una parte de los casos (70 %);
  - elegir por grupo de material la que mejor reproduce a Corte Certo;
  - **informar sobre el 30 % restante**, para no hacerse trampa.
- **Resumen para Juan** en `docs/VALIDACION.md`, en palabras simples:
  - % de casos iguales, mejores (menos planchas) y peores;
  - diferencia media;
  - todo eso por material y por tamaño de proyecto;
  - en cuántos casos Corte Certo ya estaba en el mínimo teórico;
  - los 10 peores con explicación.
- **Página de revisión** (HTML), como las de la water jet y el modo sombra:
  - caso por caso, nuestros montajes dibujados al lado de los números de Corte Certo;
  - filtros: peores, mejores, no se pudo leer;
  - Juan marca bien / mal / duda;
  - un botón copia sus respuestas como texto para pegar en la sesión.
  
  Si pesa menos de 5 MB y no tiene nombres, va a `docs/validacion/`; si no, se genera local.

### 10.4 Presupuesto de máquina

- Primero una muestra (50 casos); después todo.
- Límite de trabajo por caso.
- Corridas largas en segundo plano y por tandas, guardando resultados parciales, para retomar
  si se corta.
- La validación completa no debería pasar de ~1 hora de máquina. Si hay miles de casos, muestreá
  y decí cómo.

## 11. Banco sintético (siempre, haya o no datos)

- **"Corte perfecto"**:
  - partir k planchas en piezas con cortes de guillotina al azar (con y sin separación);
  - el óptimo es k planchas sin desperdicio;
  - el motor tiene que encontrar k (o decir a cuánto quedó).
- **Al azar realistas**: medidas de templados y DVH típicos (de 300 a 2500 mm, muchas repetidas)
  y casos como el 413 (piezas grandes, ~3 por plancha). Se comparan contra el mínimo teórico.
- Se guarda como archivos fijos (semilla fija) en `tests/banco/`, con sus resultados esperados,
  para detectar si un cambio empeora algo.

## 12. Fases y entregables

Al cerrar cada fase: tests en verde, commit, `docs/ESTADO.md` al día y una revisión del
subagente `revisor`.

| Fase | Qué | Terminado cuando |
|---|---|---|
| **F0** | Inventario y entendimiento | Escritos `docs/INVENTARIO.md` (cada archivo: qué es y para qué sirve) y `docs/ENTENDIMIENTO.md` (1–2 páginas: qué entendiste, qué te hizo dudar, plan); `PREGUNTAS_ABIERTAS.md` al día. Sin código todavía, salvo el esqueleto del paquete |
| **F1** | Motor + validador + banco sintético + CLI (`python -m optimizador calcular proyecto.json`) | Tests con instancias al azar en verde; banco sintético con resultados en `docs/VALIDACION.md`; tiempos medidos |
| **F2** | Informe de cálculo, montajes SVG, impresión, JSON (`docs/API.md`) | El informe de un caso de prueba se ve igual que la captura 1, y las miniaturas como la captura 2 |
| **F3** | Interfaz local + `Abrir_Optimizador.bat` + importadores + presets | Se puede cargar un proyecto pegando desde Excel, calcular, ver e imprimir sin tocar la consola |
| **F4** | Validación histórica: lector de leyendas, reconstrucción, calibración, página de revisión | `docs/VALIDACION.md` con los números del 30 % de prueba. Si no hay datos: el banco corre de punta a punta con el caso de juguete |
| **F5** | Entrega | `docs/INSTALACION.md` (paso a paso en Windows, para alguien que no programa), `docs/USO.md` (cómo cotizar con el programa), `ESTADO.md` final, PR |

## 13. Cómo trabajar

- **Sesión desatendida**: Juan no está mirando. No te frenes a preguntar:
  - elegí lo razonable;
  - escribilo en `docs/DECISIONES.md`;
  - anotá la pregunta en `docs/PREGUNTAS_ABIERTAS.md` con la opción por defecto que usaste;
  - seguí.
- **Gastá en calidad, no en vueltas**:
  - tests, casos borde y validación, sí;
  - reescribir lo que anda o correr la validación entera por cada cambio chico, no;
  - si algo no avanza después de 3 intentos distintos, anotalo y pasá a lo siguiente.
- **Subagentes**:
  - para trabajo independiente en paralelo (por ejemplo, la interfaz mientras se afina el motor);
  - al cerrar cada fase, el subagente **`revisor`** revisa sin haber visto cómo se hizo.
- **Dependencias**: anotadas en `requirements.txt` con versiones fijas que tengan paquetes para
  Windows.
  - Sugeridas: numpy, scipy, fastapi, uvicorn, openpyxl, xlrd (para el `.xls` de la Interfaz).
  - Para desarrollo: pytest e hypothesis.
- **Git**:
  - commits chicos;
  - la sesión en la nube trabaja en su rama;
  - al final de cada fase importante, PR con un resumen para Juan;
  - nunca force push.

## 14. Metas

- **Motor**:
  - el 100 % de los resultados pasa el validador;
  - en el banco "corte perfecto" encuentra el óptimo en ≥ 95 % de las instancias de hasta 100
    piezas;
  - cumple los tiempos de §6.5.
- **Contra Corte Certo (histórico)**: son metas iniciales; ajustalas con los datos y explicá por
  qué.
  1. **Reproducir**: con la configuración calibrada, el mismo número de planchas en ≥ 90 % de
     los casos leíbles del grupo de prueba.
  2. **Igualar o mejorar**: igual o menos planchas en ≥ 95 % de los casos; nunca más de 1
     plancha de diferencia en contra.
  3. **Números**: aprovechamiento, m² y perímetro calculados con la fórmula de Corte Certo, al
     0,01 %.
- **Uso**: Juan puede cotizar un presupuesto típico de punta a punta en la interfaz en menos de
  2 minutos, sin consola.
