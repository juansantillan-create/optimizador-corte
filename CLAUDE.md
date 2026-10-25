# CLAUDE.md — optimizador-corte

Instrucciones permanentes para cualquier sesión de Claude que trabaje en este repo (en la
nube o en la PC de Juan). La especificación completa está en `docs/BRIEF_OPTIMIZADOR.md`;
dónde quedó el trabajo, en `docs/ESTADO.md`. **Leé los dos antes de tocar código.**

## Qué es

Un optimizador de corte de vidrio propio de Cristalux, **para cotizar**. Dado un listado de
piezas (material, cantidad, ancho, largo), calcula:
- cuántas planchas hacen falta;
- cómo se acomodan las piezas (los montajes);
- el aprovechamiento.

Tiene que usar la misma configuración, dar los mismos números y mostrar las mismas pantallas
que **Corte Certo v3.9K**, que es lo que se usa hoy en la oficina. No reemplaza a Optima
(producción y mesas de corte): no manda nada a las mesas ni imprime etiquetas. Se desarrolla en
la nube con Claude y **corre local** en una PC de la oficina.

## Para quién se escribe

Para Juan (oficina comercial; técnico, no programador de tiempo completo) y sus compañeros.
- Todo en **castellano rioplatense**: documentos, pantallas, mensajes de error y commits. Las
  funciones y variables van en castellano sin tildes (`calcular_montajes`, `plancha_util`),
  como en los otros proyectos de Juan.
- Explicaciones simples, sin jerga. Si hace falta un término técnico, explicalo la primera vez
  que aparece.
- Lo que tiene que decidir Juan va a `docs/PREGUNTAS_ABIERTAS.md`. Cada entrada lleva la
  pregunta, por qué importa y la opción por defecto que ya se está usando. Juan contesta en
  texto libre ("sí", "no, va con 20", "preguntale a Lucas"): interpretalo y aplicalo.

## Reglas que no se negocian

1. **Sin nombres de clientes en git**: ni en el código, ni en docs, tests, fixtures o commits.
   Los casos se identifican por número de presupuesto. Los datos con nombres van en
   `datos/privado/`, que git ignora.
2. **No se conecta a nada de la fábrica**: ni Metrix, ni SQL Server, ni mainque, ni Gmail. Trabaja
   con archivos. Los casos viejos llegan exportados (ver `docs/CONTRATO_DATOS.md`).
3. **Nunca se inventa en silencio.** Si un dato falta o no se entiende, se ve un aviso en el
   resultado y en el informe; nunca queda un supuesto escondido. Todo resultado pasa por el
   **validador geométrico independiente** antes de mostrarse (ver el brief, §6.4).
4. **Corre en una PC modesta con Windows**:
   - Poca RAM: el programa tiene que andar con menos de 500 MB.
   - Python 3.10 o más nuevo, con un **venv propio**. Nunca el `_work\venv` del proyecto de
     Metrix.
   - Dependencias mínimas que se instalen en Windows sin compilar nada (numpy y scipy sí).
   - Sin internet mientras corre.
   - Puertos ya ocupados en esa PC: 8080, 8090, 8501 y 8502. La interfaz usa el **8520** (o el
     siguiente libre).
5. **Resultados reproducibles**: la misma entrada con la misma configuración da siempre el
   mismo resultado (semillas fijas; nada que dependa del orden de un diccionario ni de la hora).
6. **Nada irreversible**:
   - Nada de `git push --force` ni reescribir la historia.
   - No se borra nada de `datos/`.
   - Las corridas grandes guardan resultados parciales sobre la marcha.
7. **Antes de cada commit**:
   - `pytest -q` tiene que pasar.
   - Si cambió el motor: correr el banco de pruebas y actualizar `docs/VALIDACION.md`.
   - Commits chicos, en castellano, que digan qué y por qué.
8. **Al cerrar cada etapa**:
   - Actualizar `docs/ESTADO.md` (qué se hizo, qué falta, cómo seguir), para que otra sesión
     pueda retomar sin leer toda la conversación.
   - Anotar las decisiones en `docs/DECISIONES.md` (fecha, qué y por qué).

## Medidas: es fácil confundirse

- Todo en **milímetros enteros**. m² = mm² ÷ 1.000.000.
- La plancha se dibuja **acostada**, con el lado largo horizontal, igual que en Corte Certo:
  - **Ancho = eje X = lado largo** (3580);
  - **Largo = eje Y = lado corto** (2500).
  En `Medidas_hojas.xlsx` es igual: "Ancho" es el lado largo (3600), y el corte banda se le
  resta a ese lado.
- En Metrix, `LARGO`/`ANCHO` de una pieza **no** dicen la orientación. Con rotación permitida da
  igual. Con textura (veta), ver `docs/PREGUNTAS_ABIERTAS.md`.
- Origen de coordenadas: abajo a la izquierda, X hacia la derecha e Y hacia arriba (como el SCAD
  de la water jet). Al dibujar en pantalla se invierte Y.

## Vocabulario

| Palabra | Qué es |
|---|---|
| plancha / chapa / hoja | El vidrio entero como viene del proveedor (ej. 3600 × 2500) |
| plancha útil | La plancha menos el corte banda y los márgenes (ej. 3580 × 2500) |
| corte banda | Lo que se le saca al lado largo de la hoja por el canto (20, 30 o 50 mm según el espesor) |
| separación entre piezas | Lo que queda entre pieza y pieza ("ancho de la sierra" en Corte Certo) |
| destaque mínimo | La tira más angosta que se puede separar al cortar (campo de Corte Certo) |
| montaje / layout | Un esquema de corte de una plancha; puede repetirse en varias planchas |
| aprovechamiento | m² de piezas ÷ m² de planchas útiles usadas, en % (la fórmula de Corte Certo) |
| pérdida | 100 % − aprovechamiento |
| retazo / offcut | Sobrante rectangular que sirve para otra cosa |
| guillotina | Cada corte atraviesa el pedazo de lado a lado (así se corta el vidrio) |

## Mapa del repo

| Dónde | Qué |
|---|---|
| `PROMPT_INICIAL.md` | Los prompts para arrancar y seguir las sesiones en la nube |
| `docs/BRIEF_OPTIMIZADOR.md` | **La especificación**: alcance, motor, salidas, interfaz, validación, fases, metas |
| `docs/CORTE_CERTO.md` + `docs/img/` | Las pantallas de Corte Certo que hay que replicar (4 capturas reales) |
| `docs/CONTRATO_DATOS.md` | Qué trae el zip de casos históricos y cómo se arma en la PC de Juan |
| `docs/ESTADO.md` · `DECISIONES.md` · `PREGUNTAS_ABIERTAS.md` | Dónde quedó todo, qué se decidió, qué falta que conteste Juan |
| `config/` | Medidas de planchas (`hojas.csv`, sale de `fuentes/Medidas_hojas.xlsx`) y reglas de corte |
| `contexto/` | Documentos de la fábrica (Metrix, glosario, orquestador). Mapa en `contexto/LEEME.md` |
| `datos/` | Casos históricos para validar (`datos/casos/` va a git sin nombres; `datos/privado/` no) |
| `herramientas/` | Scripts sueltos (ej. `importar_medidas_hojas.py`) |
| `optimizador/` | El programa (paquete de Python): motor, validador, informe, interfaz |
| `tests/` | Los tests (`pytest -q`) y el banco sintético (`tests/banco/`) |
| `requirements.txt` · `requirements-dev.txt` · `pyproject.toml` | Dependencias con versiones fijas y datos del paquete |
| `.claude/agents/revisor.md` | Subagente revisor independiente: usarlo al cerrar cada fase |

## Para probar en la PC de Juan

Doble clic en `Abrir_Optimizador.bat` (la primera vez instala lo necesario; ver
`docs/INSTALACION.md`). Se abre el navegador en `http://127.0.0.1:8520`. Cerrar la ventana negra
apaga el programa.
