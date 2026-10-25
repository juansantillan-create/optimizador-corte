# Optimizador de corte de Cristalux: informe

Para la oficina comercial, producción y quien siga desarrollándolo. Octubre de 2026.

## 1. Qué es

Un programa propio que, dado un listado de piezas de vidrio (material, cantidad, ancho, largo),
calcula **cuántas hojas hacen falta, cómo se acomodan las piezas (los montajes) y el
aprovechamiento**. Usa la misma configuración y las mismas pantallas que Corte Certo, corre en una PC
de la oficina sin internet, y todo resultado pasa por un **validador independiente** que revisa que
las piezas entren, no se pisen, se puedan cortar de lado a lado (guillotina) y que las cuentas den.

Hoy sirve para **cotizar**. La idea es que, más adelante, también arme el corte de producción (lo
que hoy hace Optima).

## 2. Cómo le fue

**Contra Corte Certo** (1089 presupuestos viejos que se pudieron comparar, de 1341):

| | Mismas hojas | Menos hojas | Más hojas |
|---|---|---|---|
| Todos los casos | **80,0 %** | 16,5 % | 3,5 % |
| Con esfuerzo "Máximo" en los que daban más | 80,9 % | 16,6 % | 2,5 % |
| Presupuestos de hasta 20 piezas | 97,5 % | 0,4 % | 2,2 % |
| Presupuestos de más de 100 piezas | 57,6 % | 37,5 % | 4,9 % |

En **96,5 % de los casos da igual o menos vidrio que Corte Certo**. En los presupuestos grandes es
donde más ahorra (uno de cada tres da menos hojas).

**Contra Optima** (5 lotes cortados en planta, con la configuración de producción: corte banda y
destaque mínimo de la regla de Lucas, también al final de la hoja y entre piezas separadas):

| Lote | Vidrio | Optima (m² de hoja) | Programa, esfuerzo normal | Programa, esfuerzo máximo |
|---|---|---|---|---|
| 164601 | CA4PA | 12,00 | 12,00 (igual) | 12,00 (igual) |
| 165903 | FL5IN | 73,44 | 74,52 (+1,5 %) | 73,44 (igual) |
| 172802 | FL8IN | 36,00 | 36,00 (igual) | 36,00 (igual) |
| 172905 | FL6IN | 97,23 | 99,00 (+1,8 %; Optima usó 2 retazos) | 99,00 |
| 173703 | FL10IN | 94,64 | 94,64 (igual) | 91,39 (−3,4 %) |
| **Total** | | **313,32** | **316,16 (+0,9 %)** | **311,83 (−0,5 %)** |

Con esfuerzo máximo empata o mejora a Optima en 4 de 5 lotes; en el otro, Optima usó dos retazos
que el programa no tiene (no sabe qué hay en stock). Son solo 5 lotes: confirma que la
configuración de Optima está bien entendida, no es una estadística.

Detalle completo, con los peores casos y cómo se hizo: `docs/VALIDACION.md`.

## 3. Cómo se usa

1. Doble clic en `Abrir_Optimizador.bat` (la primera vez instala lo necesario; `docs/INSTALACION.md`).
   Se abre el navegador en `http://127.0.0.1:8520`.
2. **Proyecto**: pegar las piezas desde Excel o importar la planilla de la Interfaz (un DVH son 2
   vidrios; un escalonado usa ANCHO2/LARGO2 para el segundo).
3. Elegir la configuración:
   - **"Como Corte Certo hoy"** (para cotizar): plancha de 3580 × 2500 (hoja de 3600 menos 20 de
     banda), sin separación ni destaque, +3 mm en las piezas con pulido recto.
   - **"Reglas de corte (Lucas, como Optima)"** (para ver cómo saldría en planta): banda y destaque de
     la regla de Lucas (20/30/50 según el espesor).
4. **Calcular**. "Normal" tarda segundos; "Máximo" busca más (en presupuestos muy grandes, minutos).
5. Resultado: el informe y los montajes como Corte Certo, para imprimir o exportar a Excel/CSV.

Detalle: `docs/USO.md`.

### Cómo entra en la cotización de hoy

La planilla de cotización (ejemplo: la de Eclipse) toma de Corte Certo, por vidrio, **cuántas hojas y
de qué medida**, y con eso calcula:

- **m² de hoja** = hojas × ancho × alto;
- **neto** = m² de piezas, que se cobra al precio del vidrio;
- **desperdicio** = m² de hoja − m² de piezas, que también se cobra.

El optimizador devuelve exactamente eso por material (`planchas_usadas`, `m2_hoja_entera`,
`m2_piezas`, `aprovechamiento`), así que puede reemplazar el paso de "cargar en Corte Certo y copiar
el resultado".

## 4. Cómo seguir: que optimice solo, en segundo plano

Hoy el comercial carga las piezas, calcula y copia. La idea es que **nadie cargue nada**: cuando un
presupuesto cambia, el cálculo se hace solo y la cotización ya tiene las hojas y el desperdicio.

### Cómo se comunica con el orquestador

El optimizador **no se conecta a nada de la fábrica** (ni Metrix, ni SQL Server, ni Gmail): recibe
un JSON y devuelve un JSON. El orquestador es el que lee el presupuesto y escribe el resultado. Hay
tres formas de llamarlo, con la misma entrada y la misma salida (`docs/API.md`):

| Forma | Cuándo conviene |
|---|---|
| `from optimizador.api import optimizar` → `optimizar(entrada)` | El orquestador es Python y corre en la misma PC |
| `python -m optimizador calcular entrada.json -o resultado.json` | Desde cualquier lenguaje o script; el código de salida dice si salió bien (0), si el validador lo rechazó (1) o si faltan piezas (2) |
| HTTP local: `POST /api/calcular`, `GET /api/calculo/{id}` y `GET /api/calculo/{id}/resultado.json` | Si el optimizador queda abierto como servicio (puerto 8520) |

Flujo propuesto:

```text
Metrix (presupuesto)  →  orquestador  →  entrada.json  →  optimizador  →  resultado.json
                                                                              │
cotización (planilla o app) ←  orquestador  ←  hojas, m², desperdicio, avisos ┘
```

1. El orquestador detecta un presupuesto nuevo o modificado y arma la entrada: proyecto
   (número de presupuesto), piezas (material, cantidad, ancho, largo, clase), preset
   `"corte_certo"` y esfuerzo `"normal"`.
2. Llama al optimizador. Si `verificado` es falso o `completo` es falso, **no se usa el resultado**:
   se avisa al comercial (los avisos y errores vienen en el JSON, en castellano).
3. Guarda el resultado junto al presupuesto y completa la cotización: por material, hojas × medida,
   m² de hoja, neto y desperdicio.
4. Si el presupuesto no cambió, no se recalcula: la misma entrada da siempre el mismo resultado
   (semillas fijas), así que se puede guardar y reusar.

Cosas a tener en cuenta:
- **Un cálculo a la vez por PC** (es lo que aguanta una PC modesta). Para varios presupuestos, una
  cola: se calculan uno detrás de otro con "normal" y, si sobra tiempo (de noche), se repasan los
  grandes con "máximo".
- Los avisos importan: plancha supuesta (vidrio que no está en la planilla), pieza que no entra,
  etc. El orquestador los tiene que mostrar, no esconder.
- Las medidas de hoja salen de `config/hojas.csv` (de `Medidas_hojas.xlsx`) y `config/hojas_extra.csv`
  (stock y casos viejos). Si cambia la planilla, se vuelve a importar.

### Hacia reemplazar Optima

Para cotizar ya está. Para cortar en planta faltan, en este orden:

1. **Stock**: que sepa cuántas hojas hay de cada medida (los listados de stock que mandaste) y no
   use más de las que hay.
2. **Retazos**: usar los sobrantes guardados y decir qué sobrante conviene guardar.
3. **Juntar pedidos**: optimizar varios presupuestos del mismo vidrio juntos (como un lote de
   Optima), que es donde más se ahorra.
4. **Salida para planta**: montajes con etiquetas y el formato que leen las mesas de corte.
5. **Aprobación del jefe de planta**: el programa propone ("con este cambio se ahorran 2 hojas
   juntando estos pedidos") y el jefe de planta decide si lo imputa o no. Nada cambia en producción
   sin esa aprobación.

Con eso, los datos de cotización, stock y producción "hablan entre sí": una cotización ya sabe qué
hay en stock, y una optimización de planta se puede rehacer en el momento si entra un pedido
urgente o se rompe una hoja.

## 5. Lo que falta o hay que mirar

- En presupuestos grandes, a veces da más hojas que Corte Certo (3,5 % de los casos; 2,5 % con
  "Máximo"). Se puede seguir mejorando el motor.
- "Máximo" con muchas medidas distintas puede tardar minutos.
- Con la plancha achicada (3580), una pieza que mide lo mismo que la hoja (3600 en 3600, 3200 en
  Cool Lite) no se puede cotizar: el programa lo avisa.
- Falta probarlo en la PC de la oficina (tiempos con `python -m optimizador banco`).
- Pregunta abierta: la 16 (si las mesas limitan las etapas de corte).
