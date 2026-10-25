# Visión: el orquestador y la central de Cristalux

Armado con Juan el 09/10/2026, después de que los bots de presupuesto (Interfaz +
Metrix) y de NP (mainque) funcionaran de punta a punta. **Actualizado el 15/10** con la
charla del 13 al 15/10: dos entradas al circuito, el portón de producción, Gmail, el
optimizador y los planos. **Actualizado el 16/10**: el modo sombra ya funciona (Gmail →
Haiku → comparación con lo cargado, con sus primeros números), los planos de la water jet
pasaron a producción y el bot de mainque v1.5 trata la empresa TEST como real. **No es un
plan con fechas:** es el mapa hacia dónde vamos y el orden en que lo vamos a construir. Se
actualiza a medida que decidimos cosas.

El detalle de la columna (la ficha de cada pedido, sus estados y quién mueve cada uno)
está en **`docs/EXPEDIENTE_PEDIDO.md`**.

## La idea en una frase

**Metrix y mainque siguen siendo el motor.** Alrededor construimos una **central** para
la oficina (y más adelante para los clientes) y un **orquestador** que lleva cada pedido
de punta a punta, haciendo solo lo que hoy se hace a mano, y que deja a las personas
**revisando en lugar de cargando**.

## Tres capas

Todo lo que construimos entra en una de estas tres capas. **Las herramientas no se
juntan en un solo programa:** cada una hace lo suyo, y el expediente es lo que las ata.

| Capa | Qué es | Cómo está |
|---|---|---|
| **Caras** | Cómo lo usan las personas: el Gmail de cada comercial (borradores), la bandeja/consola, más adelante el portal de clientes | Por hacer (hay tableros y Power BI) |
| **Columna** | El **expediente** de cada pedido + el orquestador que pregunta "¿qué le falta?" y lo encarga | Diseñado (`docs/EXPEDIENTE_PEDIDO.md`), sin construir |
| **Piezas** | *Cerebro* (Python en el servidor: interpretar, cruzar, verificar, optimizar, dibujar) y *manos* (bots que escriben en Metrix y mainque por pantalla) | Muchas ya andan (tabla abajo) |

## El mapa

```
            CLIENTES                         OFICINA                        FÁBRICA
   (más adelante) sus presupuestos,   bandeja/consola: revisar,       pantallas por puesto
   pedidos y fechas de producción     aprobar, estado de cada         (ya hay tablero)
   y despacho                         pedido, lo que hizo el bot
            │                                  │
            └──────────────┬───────────────────┘
                     CENTRAL  ◄── respuestas y avisos al cliente (mail, firma del bot)
                           │
     ┌─────────────────────┼──────────────────────────┐
  ENTRADA              ORQUESTADOR                  DATOS
  mail (80 %): el bot   EXPEDIENTE por pedido       copia de la base de Metrix
  es miembro de los     (un mensaje = un pedido)    cada 5 min (presupuestos,
  grupos templados@ y   CEREBRO: decide, calcula    pedidos, 472.000 piezas
  comercial@            y verifica (servidor        con su estado)
  WhatsApp Web (19 %):  IASCRISTAL, 28-32 GB)
  se reenvía a la       MANOS: bots en la sesión
  casilla del bot       de escritorio remoto
  papel (1 %): foto     dedicada
  → INTERPRETADOR          │  los bots escriben como un usuario, por pantalla;
    (Haiku + código)       │  la base de Metrix se lee y NUNCA se escribe
                    METRIX (producción) · MAINQUE (facturación)
```

## El recorrido de un pedido

**Todo pedido pasa por presupuesto → mainque → producción** (Juan, 15/10). Hay dos
formas de entrar, y lo único que cambia es **qué dispara** el paso a mainque:

```
 mail nuevo (un mensaje = un expediente; los hilos se usan para cotizaciones y charlas)
   │
   ▼
 CLASIFICADO ── no es pedido (consulta, factura…) ──► se descarta / a una persona
   │
   ├── COTIZACIÓN (el cliente pide precio)        ├── PEDIDO DIRECTO (cliente con cuenta,
   │                                              │   "es un pedido nuevo", por lo general chico)
   ▼                                              ▼
 INTERPRETADO ─── ¿dudas? ──► BANDEJA DE REVISIÓN (una persona decide y lo devuelve)
   │
   ▼
 PRESUPUESTO CARGADO (Interfaz + Metrix; la obra lleva la MATRÍCULA) → VERIFICADO por la base
   │
   ├── cotización: A INFORMAR + PDF + borrador de respuesta → el comercial lo manda
   │       │
   │       └── el cliente CONFIRMA (lo marca el comercial, o el bot leyendo el mail) ──┐
   │                                                                                   │
   └── pedido directo: el disparo es INMEDIATO ────────────────────────────────────────┤
                                                                                       ▼
                                           ACEPTADO → NP en mainque → PEDIDO en Metrix
                                           (con el Nº de presupuesto: los renglones salen
                                            tal cual) → PLANOS (water jet, si hay)
                                                       │
                                                       ▼
                                    🔒 PORTÓN DE PRODUCCIÓN (siempre una persona)
                                    el comercial controla en la consola y APRUEBA
                                                       │
                                                       ▼
                         imputar + mail al cliente con copia a producción
                         (hoy: lo hace el comercial; más adelante: el bot, al aprobar)
                                                       │
                                                       ▼
                         SEGUIMIENTO (piezas por puesto) → listo / despachado → AVISO
```

**El portón de producción.** Una mala cotización se arregla; un mal envío a producción,
no. Por eso el bot llega como mucho hasta el **pedido PENDIENTE sin imputar** (probado
el 13/10: pedido 12137) y **una persona aprueba**. Hoy el paso a producción "de verdad"
es el **mail de respuesta al cliente con copia a producción**; imputar en Metrix se hace
a veces y sin control, porque lo hace la misma persona que cargó. Con el orquestador, la
consola le muestra al comercial lado a lado:
- el **pedido interpretado** contra **lo cargado**, con las diferencias marcadas;
- el **plano del cliente** contra el **plano generado**;
- con precios: el **desglose del descuento** y el **consumo de hojas**.

Cuando el comercial aprueba, primero lo hace él como hoy (imputa y manda el mail). Más
adelante, el botón "Aprobar" hace que el bot impute y mande el mail.

**La "tecla" por cliente.** Administración define qué clientes tienen cuenta corriente.
La tecla dice a qué clientes se les acepta un **pedido directo** (el disparo inmediato,
sin esperar confirmación). El portón de producción sigue siendo humano para todos.

**Fuera del horario.** Hoy se carga de 8 a 17. El orquestador puede trabajar de noche y
los fines de semana: un pedido directo del sábado queda cargado y PENDIENTE, y el lunes a
primera hora solo falta aprobar. Y algo que el jefe ya pidió: poder ofrecerle un
presupuesto a alguien un sábado a la noche, mandándole el pedido al bot y recibiendo el
PDF de vuelta.

## Las piezas y cómo están hoy

| Pieza | Estado al 16/10 | Dónde |
|---|---|---|
| **Expediente + orquestador** | 🟡 El **expediente ya existe** en el modo sombra (ficha por mail, estados, historial, costo, pareja). Falta el orquestador que mueve a los bots | `negocio/sombra.py`, `docs/EXPEDIENTE_PEDIDO.md` |
| **Lector de mail** (Gmail) | ✅ Lee el Gmail de Juan, **solo lectura**, la etiqueta `templados` (filtro del grupo), cada 15 min después del ciclo de datos (arranca al reiniciar los servicios). Para la etapa 1 hará falta una casilla propia del bot que pueda escribir borradores | `negocio/sombra.py` |
| **Interpretador** (Haiku + código) | ✅ Haiku 5.5 con el prompt del cotizador de Juan tal cual, más tipo de entrada (pedido, cotización, fasón, no es pedido) y perforaciones. Lee PDF, fotos y planillas. En el modo sombra: **pedidos 19 de 20 iguales a lo cargado (38/39 piezas)**, cotizaciones 3 de 6. Unos 0,003 USD por pedido, tope 0,80 USD | `negocio/interpretador.py` |
| **Bot de presupuesto** (Interfaz + Metrix) | ✅ v0.6.4: lotes de punta a punta, 14/14 gemelos iguales; cierre (Situación, PDF) | `bots/bot_presupuesto_metrix.py` |
| **Verificación por la base** | ✅ Dos formas: presupuesto contra presupuesto (prueba gemela) y pedido interpretado contra lo cargado, pieza por pieza (modo sombra, `comparar_piezas`). Falta usarlo como "verificador" del orquestador | `negocio/presupuesto_gemelo.py`, `negocio/sombra.py` |
| **Bot de NP** (mainque) | ✅ En uso por los compañeros (v1.5, 15/10): las NP de la empresa TEST se registran como reales; códigos nuevos de cualquier producto desde las cajitas, con unidad UN/M2 | `bots/bot_mainque.py` |
| **Generador de NP** | ✅ Hoy en la PC de Juan → pasa al servidor (permiso confirmado el 09/10). El registro guarda la empresa y arma la O.Compra ("30361" o "2709T") | `negocio/servir_np.py` |
| **Bot de paso a producción** (pedido con O.Compra = NP) | ✅ Probado el 13/10 (11775 → NP 2706 → pedido 12137), sin imputar | `bots/bot_presupuesto_metrix.py` |
| **Descuentos por cliente** (listas) | 🟡 Casi cerrado: es de donde sale cada % | `docs/LISTAS_DISTRIBUCION.md` |
| **Generador de planos** (water jet) | ✅ Prueba de concepto cerrada el 15/10: Haiku lee el plano (CAD o foto) → JSON → planilla + `.wpd` del SCAD; validado por Juan; agujeros, grillas y entrantes; primera pieza perforada en producción el 16/10. Faltan escalones/recortes de esquina y herrajes | `docs/WATERJET_PLANOS.md` |
| **Optimizador de corte** (reemplazo de Corte Certo) | Por hacer. Solo acomodar rectángulos en hojas con 2 parámetros por tipo de hoja (distancia al borde y entre piezas) → hojas, aprovechamiento y esquema. Falta el archivo de medidas de hojas (lo pasa Juan) | — |
| **Bandeja / consola** | 🟡 Primera versión **de solo lectura**: la página del modo sombra (`Abrir_Sombra.bat`), con cada pedido pieza por pieza contra lo cargado. Falta revisar, corregir y aprobar | `negocio/sombra_pagina.py` |
| **Portal de clientes** | Después de afianzar la oficina | — |

## Etapas

**Etapa 0 — Modo sombra. ✅ En marcha desde el 16/10.** El lector lee los pedidos reales
de templados@ y el interpretador los entiende **sin tocar Metrix ni contestar nada**. Una
página muestra qué entendió, qué dudas tuvo y cuánto costó. Nos da volumen real, tasa de
acierto y casos raros, y es la mejor demostración para gerencia. En paralelo: cronometrar a
mano 10 a 15 pedidos actuales (el "antes").

Primer resultado (16/10, mails del 01 al 16/10, 35 expedientes, 0,11 USD):

| | Comparados | Iguales | Piezas bien |
|---|---|---|---|
| Pedidos | 20 | 19 | 38 de 39 |
| Cotizaciones | 6 | 3 | 14 de 17 |

Lo que enseñó: la pareja sale casi siempre de la respuesta de Nicolás con
"NP / P(presupuesto)" (Juan va en copia desde ~01/10) y, si no, buscando las medidas en la
base; una vez se juntaron 10 mails de un cliente en un solo presupuesto (no es lo normal) y
también se encontraron; el cliente casi nunca está cargado como email en Metrix (2 de 35),
así que se identifica por la pareja; los fasones y los productos fuera de catálogo (vidrio
pintado) Haiku los marca para una persona, y está bien. Detalle y uso:
`docs/EXPEDIENTE_PEDIDO.md`, sección "Primer corte a construir: modo sombra".

**Etapa 1 — Pedidos directos de templados de clientes con cuenta, de punta a punta.**
Son chicos, frecuentes, ya vienen confirmados y muchos traen plano para la water jet. Juan
y el comercial de laminados son los primeros usuarios. Falta:
1. **Expediente + orquestador mínimo**: cola, estados, verificación, la tecla por cliente.
2. **Interpretador de templados**: ✅ armado y midiéndose en el modo sombra (19 de 20
   pedidos iguales). Falta juntar más semanas de datos y mirar los casos que fallan.
3. **Descuentos por cliente** firmes. Incluye "con forma": el subtotal del artículo
   +25 % se logra con un recargo, sin tildar la clase.
4. **Generador de planos** para la water jet: ✅ prueba de concepto validada y primera
   pieza perforada en producción (16/10, `docs/WATERJET_PLANOS.md`). Falta conectarlo al
   expediente (el plano del mail → `.wpd` automático).
5. **Consola**: revisar, la comparación lado a lado y el botón Aprobar.
6. **Infraestructura**: sesión de escritorio remoto dedicada al bot (las tres
   aplicaciones en una pantalla, nunca minimizadas), el generador en el servidor, y que
   todo se reinicie solo y avise por mail cuando falla.

**Etapa 2 — Cotizaciones y todos los vidrios** (DVH, laminados, distribución), el
borrador de respuesta en el Gmail del comercial, el **optimizador de corte**, leer la
confirmación del cliente en el mail, y más pasos de mainque.

**Etapa 3 — La central de la oficina completa**: estado de cada pedido, lo que hizo el
bot, avisos y recordatorios a los clientes ("¿viste el presupuesto?"), el bot imputando
al aprobar.

**Etapa 4 — Portal de clientes**: ver sus presupuestos, sus pedidos y las fechas de
producción y despacho; después cargar pedidos con un formulario.

## Decisiones tomadas

- Metrix y mainque no se tocan por dentro: se **leen** por la base (solo lectura) y se
  **escriben** por pantalla, como un usuario.
- **Todo pedido pasa por presupuesto → mainque → producción.** El bot carga el pedido
  **con** el Nº de presupuesto (los renglones salen tal cual). Así se corrige hacia
  adelante una desprolijidad de hoy: casi la mitad de los pedidos de los últimos 60 días
  se cargó sin el Nº de presupuesto (por Metrix a mano o por la Interfaz, que en los
  pedidos tampoco deja poner el nombre de la obra).
- **Un mensaje = un expediente.** Los clientes con cuenta mandan cada pedido en un mail
  nuevo; los hilos son para cotizaciones y charlas técnicas.
- **El portón de producción es humano.** El bot puede preparar todo; una persona aprueba.
- El bot tiene **su propia firma** (Juan: da imagen de avance, no de frialdad).
- El programador de Metrix solo hace cambios muy simples: no contamos con una vía
  oficial de carga. Si una sesión de bot no alcanza, se suman **otras manos en un
  segundo escritorio remoto**.
- Sesión de escritorio remoto **dedicada** al bot.
- La **matrícula** en la obra está bien aunque el cliente la vea, y es el número del
  expediente.
- Pruebas en Metrix: cliente de prueba **2691** y usuario **BOT**. En mainque, **la
  empresa TEST no es de prueba** (Juan, 15/10): ahí van las NP reales de los clientes
  con medio IVA o sin IVA, con "T" en la O.Compra de Metrix ("2709T"). Toda NP de
  prueba que se guarde ahí se borra a mano después (Juan ya lo hizo con 2698, 2699
  y 2706). Lo que define una prueba es el cliente de Metrix 2691, no la empresa.
- **Gmail**: el bot se suma como miembro de los grupos templados@ y comercial@ (los
  administra Juan). WhatsApp Web: al principio, puente casero reenviando a la casilla
  del bot.
- **Servidor IASCRISTAL**: 28-32 GB de RAM, alcanza. Lo que corre ahí tiene que ser
  liviano para no frenar Metrix (Haiku corre afuera, en la API).
- Primero se afianza la **oficina**; el portal de clientes viene después.
- Lo mantenemos **nosotros** (Juan + Claude, con documentación): simple, que se
  recupere solo y que avise cuando algo falla. Hoy nadie más sabe reiniciar un servicio.
- **Presupuesto**: unos 10 USD de API para arrancar. Cada expediente anota su costo.
  Medido el 16/10: unos 0,003 USD por pedido con Haiku 5.5 (35 expedientes por 0,11 USD).
- **Modo sombra con el Gmail de Juan** (16/10): solo lectura, la etiqueta `templados`;
  alcanza para medir. La casilla propia del bot (para escribir borradores) es de la etapa 1.
- **Clases que dan lo mismo para cotizar** (Juan, 16/10): en un SGP, LAM PR TEMP y FLOAT PR
  TEMP marcan el templado y pisan el precio de distribución igual. Para **producción** el
  SGP va distinto: como un "sanguchito" FL8IN (FLOAT PR TEMP) / 89SGP / FL8IN, igual que un
  DVH pero laminado. Tenerlo en cuenta al automatizar el paso a producción.
- **Un mail = un presupuesto** es lo normal; juntar varios mails en un presupuesto pasó una
  vez para no hacer 15 presupuestos, 15 NP y 15 pedidos. La sombra lo soporta igual.
- **Fasón queda afuera** del interpretador (decisión del 14/09): Haiku lo marca como
  "fasón" y se cuenta aparte, no como error.
- El seguimiento de presupuestos y pedidos hoy se hace con el Power BI: el orquestador
  no lo reemplaza.
- La contraseña de `sa` en `ORIGENES.TPS` no se va a rotar (Metrix depende de eso):
  riesgo conocido y aceptado.

## Riesgos conocidos

| Riesgo | Cómo lo encaramos |
|---|---|
| El bot (por pantalla) es el cuello de botella | Primero exprimir una sesión; si no alcanza, segunda sesión de manos |
| Una versión nueva de Metrix cambia pantallas | El kit de mapeo para volver a medir; los bots se frenan ante lo desconocido |
| Un error del bot con plata de un cliente real | Verificación por la base después de cada paso + el portón humano + la bandeja |
| Un mal envío a producción | Portón humano con comparación lado a lado; el bot nunca imputa solo |
| La sesión del bot se minimiza o se desconecta | Sesión dedicada; los bots restauran la ventana y frenan si no pueden |
| Solo Juan lo sabe mantener | Que se reinicie solo, avise por mail y tenga una página de estado; si se apaga, la oficina sigue a mano |
| La PC de Juan tiene 3,9 GB de RAM | Todo lo pesado corre después del ciclo de datos y solo con RAM libre (la sombra se saltea si hay menos de 500 MB); Juan suma 4 GB el 19/10. A futuro, llevar el generador y el orquestador al servidor |
| El portal expone datos fuera de la oficina | Va al final, con usuarios y cada cliente viendo solo lo suyo |

## Preguntas abiertas

- **Nombre** para la herramienta (para presentarla y para la firma del bot).
- ¿Producción arranca con el **mail en copia** o con el **pedido imputado** en Metrix?
  Define qué tiene que pasar sí o sí al aprobar.
- Regla de cuenta corriente (la define administración): ¿qué se controla antes de
  aceptar un pedido directo?
- ~~Formato que lee la water jet.~~ Resuelto el 14/10: `.wpd` (XML del SCAD Wps_S_Cad), ver `docs/WATERJET_PLANOS.md`.
- Archivo con las medidas de las hojas y los 2 parámetros por tipo de hoja (para el
  optimizador).
- Cómo cronometrar el "antes" (planilla simple, Juan pide ayuda).
- Casilla propia del bot en Google Workspace para la etapa 1 (¿hace falta una licencia?) y
  dónde quedan los borradores de respuesta.
- **Alta a mano de clientes y fletes nuevos** (Juan, 2026-10-17; para ubicar en el mapa): hoy la lista de
  cada cliente sale de `CLIENTES CON LISTA.xlsx` y los fletes de `FLETES POR CLIENTES.xlsx`, ambos copiados
  a mano. ¿De dónde salen los clientes nuevos y quién los suma (alta en Metrix → lista asignada → flete)?
  ¿Con qué herramienta (planilla compartida, formulario, la central)? Hoy `negocio/precios.py` los lee y
  las correcciones van en `salida/precios/config/` (ver `docs/PRECIOS.md`).
