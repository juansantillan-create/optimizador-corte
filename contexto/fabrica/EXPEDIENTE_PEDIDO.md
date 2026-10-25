# El expediente del pedido — la columna del orquestador

*Borrador del 14/10/2026 (paso 1 de la propuesta del 13/10), actualizado el 15/10 con las
respuestas de Juan. Lo marcado ❓ espera respuesta. Visión general: `docs/VISION_ORQUESTADOR.md`.*

## Para qué sirve

Hoy cada pieza tiene su propio registro: la cola del bot de Metrix
(`prueba_gemela\cola`), el `np_bot\registro.csv` de mainque, los logs. Nadie sabe
"en qué anda el pedido de tal cliente" sin mirar tres lugares.

El **expediente** es **una ficha por pedido**, desde que llega el mail hasta que se
entrega. El orquestador no es otra cosa que un servicio que mira cada expediente y se
pregunta *"¿qué le falta?"*, encarga ese paso (a un módulo de Python o a un bot) y anota
el resultado. **Las herramientas no se reescriben ni se juntan en un programa**: cada
una sigue haciendo lo suyo, y el expediente es lo que las ata.

## Reglas de diseño

1. **Una sola verdad.** Lo que diga el expediente es el estado del pedido. Los bots y
   los módulos no se hablan entre ellos: hablan con el expediente.
2. **Solo el orquestador escribe el expediente.** Los bots siguen con sus carpetas de
   cola (el contrato que ya funciona) y el orquestador lee lo que dejan.
3. **Cada paso se verifica por la base de Metrix** (solo lectura, como siempre) antes de
   avanzar. Lo que no se puede verificar va a la bandeja.
4. **Cada paso se puede retomar.** Si algo se corta a mitad, antes de repetir un paso el
   orquestador mira en la base si ya se hizo (por la **matrícula** en la obra). Así no
   se duplica nada.
5. **Nada entra a producción sin una persona.** Una mala cotización se arregla; un mal
   envío a producción, no (Juan, 13/10). El bot puede llegar hasta el **pedido
   PENDIENTE sin imputar**; **imputar lo hace el comercial**, después de controlar.
6. **Ante cualquier duda, a la bandeja**, con el motivo escrito en castellano.
7. **Todo queda anotado con fecha y hora.** De ahí salen solos los números para
   gerencia (ver "Lo que sale gratis").

## Dos formas de entrar, un solo circuito

**Todo pedido pasa por presupuesto → mainque → producción** (Juan, 15/10: eso no cambia).
Lo que cambia es **quién dispara** el paso a mainque:

- **Cotización**: el cliente pide precio. Interpretación → presupuesto → se le envía →
  **el cliente confirma** (lo marca el comercial o, más adelante, el bot leyendo el mail)
  → **eso dispara** mainque → pedido → planos (si hay).
- **Pedido directo**: clientes con cuenta que mandan el pedido ya confirmado ("es un
  pedido nuevo"), por lo general chico. Es el mismo circuito, pero **el disparo es
  inmediato**: interpretación → presupuesto → mainque → pedido → plano para la water jet.
  Es el candidato ideal para la etapa 1.

El clasificador tiene que distinguir estos dos casos. La "tecla" por cliente dice a qué
clientes se les acepta un pedido directo sin confirmación.

## Qué guarda un expediente

| Dato | Qué es | Ejemplo |
|---|---|---|
| **Matrícula** | El número del expediente. Es la misma que va adelante de la obra en Metrix | `AAX` |
| Canal y origen | Por dónde llegó y cómo encontrarlo (hilo del mail, mensajes) | mail, hilo de templados@ |
| Cliente | Código en Metrix y en mainque, y con cuánta seguridad se reconoció | 2691 / 425, "seguro" |
| Comercial a cargo | Por la cartera del cliente; si es compartido, el que lo "toma" | Juan |
| Adjuntos | Planos, planillas, fotos, guardados en una carpeta del expediente | `plano_2.pdf` |
| Planos generados | Plano para la water jet (desde el JSON interpretado) y esquema de corte de hojas | (más adelante) |
| Tipo de entrada | Cotización o pedido directo | pedido directo |
| Pedido interpretado | Lo que entendió el interpretador: piezas, procesos, perforaciones | (JSON) |
| Advertencias | Lo que hizo dudar al interpretador o al verificador | "agujero sin Ø" |
| Presupuesto | Nº en Metrix, versión (si el cliente pide cambios) y su PDF | 11775 v1 |
| NP y pedido | Nº de NP en mainque y de pedido en Metrix, con su PDF | 2706 / 12137 |
| Estado actual | Ver abajo | PEDIDO_CARGADO |
| Historial | Cada cambio de estado: cuándo, quién (bot o persona) y el resultado | — |
| Costo | Lo que gastó en la API de Haiku (para controlar los 10 USD) | — |

## Los estados

```
 RECIBIDO ──► CLASIFICADO ──► INTERPRETADO ──► PRESUPUESTO_CARGADO ──► VERIFICADO
                  │                                                        │
                  └─ no es pedido: DESCARTADO                              ▼
                     (consulta, factura, spam)                    LISTO_PARA_ENVIAR
                                                                  (A INFORMAR + PDF +
                                                                   borrador de respuesta)
                                                                           │
                                                          el comercial lo manda al cliente
                                                                           ▼
                                                                    ENVIADO_AL_CLIENTE
                                                                     │       │       │
                                                     pide cambios ◄──┘       │       └──► RECHAZADO
                                                     (vuelve a INTERPRETADO,  │
                                                      presupuesto v2)         ▼
                                                                         ACEPTADO
                                                                           │
                                                                           ▼
                                                     NP_CARGADA (mainque) ──► PEDIDO_CARGADO
                                                                              (PENDIENTE, sin imputar)
                                                                                    │
                                                                 🔒 el comercial controla e IMPUTA
                                                                                    ▼
                                                     EN_PRODUCCION ──► LISTO ──► ENTREGADO ──► CERRADO

 Desde CUALQUIER estado:  ──► EN_REVISION (bandeja, con motivo) ──► vuelve al estado que corresponda
                          ──► CANCELADO (por una persona)
```

| Estado | Lo mueve | Cómo se verifica | Pieza que ya existe |
|---|---|---|---|
| RECIBIDO | lector de mail | el mail quedó guardado con sus adjuntos | ⬜ lector |
| CLASIFICADO | Haiku | — (si duda: a revisión) | ⬜ |
| INTERPRETADO | Haiku + código (CAD medido) | advertencias vacías; si no, a revisión | 🟡 interpretador / cotizador |
| PRESUPUESTO_CARGADO | bot (Interfaz + Metrix) | presupuesto encontrado por matrícula | ✅ `bot_presupuesto_metrix` |
| VERIFICADO | cerebro | lo cargado = lo interpretado, renglón por renglón | ✅ comparador de `presupuesto_gemelo` |
| LISTO_PARA_ENVIAR | bot + cerebro | Situación A INFORMAR, PDF existe, borrador creado | ✅ cierre v0.6 / ⬜ borrador |
| ENVIADO_AL_CLIENTE | **comercial** (manda el borrador) | el mail salió en el hilo | ⬜ |
| ACEPTADO | ❓ ver abajo | Situación ACEPTADO en Metrix | ✅ (paso del bot) |
| NP_CARGADA | bot de mainque | Nº de NP anotado | ✅ `bot_mainque` + `servir_np` |
| PEDIDO_CARGADO | bot de Metrix | pedido con O.Compra = NP, por SQL | ✅ v0.6.4 (12137, 13/10) |
| EN_PRODUCCION | **comercial** (imputa) | pedido imputado, por SQL | — (lo hace una persona) |
| LISTO / ENTREGADO | la base de Metrix | piezas por puesto (CAJAS), como el tablero | ✅ datos ya extraídos |

**El portón de producción (regla 5).** En la etapa 1 el bot **nunca imputa**. Eso
cambia el trabajo del comercial: carga menos y controla más. Para que el control sea
rápido, la bandeja muestra lado a lado (Juan, 15/10: lo que se controla cuando se controla):
  - el **pedido interpretado** contra **lo cargado para producción**, con las diferencias
    marcadas;
  - el **plano que mandó el cliente** contra el **plano generado** para la water jet;
  - en los casos con precio: el **desglose del descuento** y el **consumo de hojas** (de
    dónde salió, con el optimizador).

Hoy casi no se controla antes de imputar porque lleva tiempo. Si la bandeja lo hace
rápido, el control mejora en lugar de empeorar.

**La "tecla" por cliente, redefinida.** Como imputar siempre es humano, la tecla ya no
decide "pasar a producción solo". Decide **si después de ACEPTADO el bot sigue solo**
hasta PEDIDO_CARGADO (NP y pedido), o si lo hace el comercial a mano como hoy.

## La bandeja

Es una página en la red de la oficina, como los tableros, y cada comercial ve lo suyo:

- **Para revisar**: expedientes EN_REVISION con su motivo. "Lo resuelvo yo" o "corregí y
  seguí".
- **Para mandar**: borradores listos (también aparecen en su Gmail).
- **Para imputar**: pedidos cargados, con la comparación pedido ↔ cargado.
- **Mis pedidos**: en qué estado está cada uno. Es el primer paso de "el cliente ve sus
  pedidos" (etapa 4).

## Dónde vive

- **Un archivo de base de datos SQLite** en el servidor. Es un solo archivo, fácil de
  copiar como backup, y aguanta muchos lectores con un solo escritor (el orquestador).
  No va en la DuckDB de los tableros: esa se reemplaza entera cada 5 minutos (el "swap"),
  y ahí no puede vivir algo que se va escribiendo de a poco.
- Una **carpeta por expediente** (`expedientes\AAX\`) con los adjuntos, los PDF y el
  JSON interpretado.
- El servidor IASCRISTAL es **el mismo que tiene el SQL Server de Metrix**: tiene
  28-32 GB de RAM (Juan, 15/10), así que alcanza de sobra. Igual, lo que corra ahí tiene
  que ser liviano para no frenar Metrix: Haiku corre afuera (en la API) y el resto es
  poco trabajo.

## Lo que sale gratis: números para gerencia

Como cada cambio de estado queda anotado con hora y con quién lo hizo, sin trabajo extra
salen:

- pedidos por día, cuántos pasaron solos y cuántos fueron a la bandeja (y por qué);
- **tiempo desde que llega el mail hasta el presupuesto enviado**, antes y después;
- minutos de carga ahorrados (comparando con una medición manual de base, ver abajo);
- errores **frenados** por las verificaciones, que muestran que el sistema es seguro;
- gasto de la API por pedido.

Esto es el material para "presentarlo y mostrar sus beneficios". **Propuesta:** durante
una semana, cronometrar a mano 10 o 15 pedidos reales por paso (una planilla simple), así
tenemos el "antes".

## Si algo se cae (nadie sabe reiniciar un servicio)

- **El orquestador avisa solo por mail** cuando algo falla o un paso tarda demasiado.
- **Se reinicia solo**, como ya hace `negocio/servicio.py` con cada ciclo.
- **Una página de estado** con un semáforo por pieza y un botón "reiniciar".
- **Si está apagado no pasa nada grave**: los pedidos se siguen cargando a mano como hoy.
  El orquestador ayuda, pero no es imprescindible para que la oficina funcione.

## Primer corte a construir: modo sombra

**Estado al 16/10/2026: funcionando** (`negocio/sombra.py`, `negocio/interpretador.py`,
`negocio/sombra_pagina.py`).

- **Cómo se mira**: doble clic en `Abrir_Sombra.bat` (raíz del proyecto). Levanta un
  servidor local (solo en esta PC, se cierra al cerrar su ventana) y abre la página: el
  resumen arriba y cada expediente con lo que cargó la persona al lado de lo que
  entendió la sombra, pieza por pieza, más las advertencias, el texto del mail y los
  adjuntos. No toca Metrix ni Gmail. (El archivo suelto `salida\sombra\sombra.html`
  sigue existiendo, solo para mirar.)
- **Veredicto** (desde el 19/10): en cada expediente con diferencias, Juan marca quién
  tenía razón (la sombra = error de carga del comercial; lo cargado; los dos), y en los
  que no tienen pareja, si faltaba cargarlo. Los números de arriba lo tienen en cuenta:
  "pedidos bien entendidos" suma los que la sombra tenía razón, y aparecen los "errores
  de carga encontrados". Se guarda en la base de expedientes (columnas `veredicto*`).
- **Solo**: `negocio/servicio.py` la corre al terminar el ciclo de datos, como mucho
  cada 15 min y con al menos 500 MB de RAM libre. Lee Gmail (la etiqueta
  `templados` de Juan, **solo lectura**), interpreta hasta 10 pedidos nuevos con
  Haiku 5.5, busca las parejas y rearma la página. Para que empiece hay que
  reiniciar los servicios una vez (`Reiniciar_Metrix.bat`).
- **Pareja** (el presupuesto real): la respuesta de Nicolás en el hilo
  (`2709T / P11865`, Juan va en copia desde ~01/10); si no, la base de Metrix por
  medidas; si un mail no tiene pareja propia pero todas sus piezas están en un
  presupuesto, "parte del presupuesto N" (pasó una vez: 10 mails en el 11608).
- **Clasificador del mail** (desde el 19/10, hecho desde la sesión de prompts; **paso 1 =
  modo observación**): antes del manual del cotizador corre `interpretador.clasificar`
  con `prompts/clasificador_mail.txt` (v6: 99/99 intenciones en el banco de casos, 8/8
  con la API real). Guarda en el expediente (columna `clasificacion`, que se agrega sola,
  y `clasificado_haiku.json` en la carpeta) la intención (pedido, aprobación, no
  aprobado, cotización, consulta, seguimiento, reclamo, administrativo, envío a
  producción, otro), las familias (= a qué prompt va después), referencias, adjuntos,
  mecanizado y un resumen; la página lo muestra en "Qué es el mail" y en la fila. **No
  cambia nada de lo que sigue**: el manual corre igual con todos los mails y, si el
  clasificador falla, queda un evento y la sombra sigue. Para clasificar expedientes
  viejos: `python -m negocio.sombra clasificar [N | #ID ...]`. Paso 2 (pendiente, con
  Juan): que el manual corra solo en pedidos, cotizaciones y aprobaciones, y después cada
  familia vaya a su prompt (`prompts/PENDIENTES.md`).
- **"Abrir carpeta"** (arreglado el 19/10): con el servidor local el enlace a la carpeta
  daba "No existe"; ahora abre la carpeta del expediente en el Explorador de Windows.
- **Costo**: unos 0,003 USD por pedido (manual) + ~0,0014 por mail (clasificador); tope
  de 0,80 USD en `negocio/interpretador.py` (`TOPE_USD`), compartido.
- **Si Google pide el permiso de nuevo** (la página deja de sumar mails y el log
  `logs/negocio_sombra.log` lo dice): correr a mano
  `_work\venv\Scripts\python.exe -m negocio.sombra gmail` y aceptar en el navegador.
- **Primer resultado (16/10)**: pedidos 19 de 20 iguales a lo cargado (38/39
  piezas), cotizaciones 3 de 6; 0,11 USD en total.

El plan original de este corte era:

1. La base de expedientes (tabla + historial).
2. El lector de Gmail: crea expedientes RECIBIDO → CLASIFICADO → INTERPRETADO con los
   pedidos **reales**, **sin tocar Metrix ni contestar nada**.
3. Una página que los lista: qué entendió, qué dudas tuvo, cuánto costó.

Con dos o tres semanas así tenemos volumen real, tasa de acierto y casos raros, y
mostramos algo concreto sin riesgo. Recién después se conectan los bots (que ya andan).

## Preguntas abiertas

- ✅ **ACEPTADO / disparo** (15/10): lo dispara el comercial, o el bot leyendo la
  confirmación en el mail; en los pedidos directos es inmediato.
- ✅ **Gmail** (15/10): templados@ y comercial@ son grupos de Google que Juan administra;
  se puede sumar la casilla del bot como miembro. ❓ Falta definir desde qué casilla se
  leen y dónde quedan los borradores.
- ❓ En los últimos 60 días, 355 de 736 pedidos (48 %) no tienen presupuesto vinculado
  (213 cargados por personas y 142 por INTERFAZ), aunque "todo pasa por presupuesto".
  ¿Se carga el pedido sin poner el Nº de presupuesto?
- ❓ Si 3 letras de matrícula alcanzan: son 17.576 expedientes, más de un año a 40 por
  día; después se pasa a 4 letras.
