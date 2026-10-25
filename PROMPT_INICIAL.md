# Prompts para Claude Code en la web

## Cómo se usa (Juan)

1. Entrá a [claude.ai/code](https://claude.ai/code) y elegí el repo **`optimizador-corte`**
   (rama `main`).
2. Modo: **Aceptar ediciones**, para que trabaje solo y suba su rama sin pedir permiso. Modelo:
   el más capaz que tengas.
3. Pegá el **prompt 1** tal cual y mandalo. Podés cerrar la pestaña: sigue trabajando.
4. Cuando termine, revisá su mensaje final y el PR. Si está bien, en GitHub apretá **Merge** en
   el PR, así la próxima sesión arranca de ahí.
5. Para seguir, otra sesión con el **prompt 2**. Cuando tengas el zip de casos viejos, el
   **prompt 3**.

Las capturas de Corte Certo, la planilla de medidas y los documentos de la fábrica ya están en el
repo: no hace falta adjuntarlos. Si adjuntás algo nuevo, el prompt le dice qué hacer con eso.

---

## Prompt 1 — arranque

```text
Sos el desarrollador del optimizador de corte de vidrio de Cristalux. Vas a trabajar solo y por
mucho tiempo en esta sesión en la nube: no voy a estar mirando, así que no te frenes a preguntar.

Objetivo: un programa local (Python, Windows, PC con poca RAM) que reemplace a Corte Certo v3.9K
para cotizar. Dado un listado de piezas de vidrio, calcula cuántas planchas hacen falta, los
montajes y el aprovechamiento, con la misma configuración, los mismos números y las mismas
pantallas que Corte Certo. Se valida contra cientos de presupuestos viejos donde quedó anotado
lo que dio Corte Certo.

Antes de escribir código, leé en este orden:
1. CLAUDE.md (las reglas que no se negocian).
2. docs/ESTADO.md (si una sesión anterior ya avanzó, seguí desde ahí).
3. docs/BRIEF_OPTIMIZADOR.md (la especificación: alcance, motor, salidas, interfaz, validación,
   fases y metas).
4. docs/CORTE_CERTO.md y las 4 capturas de docs/img/ (mirá las imágenes).
5. config/LEEME.md y config/hojas.csv (planchas, corte banda y separación entre piezas).
6. contexto/LEEME.md (qué documentos de la fábrica leer enteros y cuáles solo consultar).
7. docs/CONTRATO_DATOS.md y lo que haya en datos/casos/ (puede estar vacío).
8. docs/PREGUNTAS_ABIERTAS.md (si hay respuestas mías, aplicalas primero).

Si en este mensaje vienen archivos adjuntos, guardalos donde corresponde según el §3 del brief
antes de empezar. Lo que tenga nombres de clientes va a datos/privado/ y nunca a git.

Después hacé las fases F0 a F5 del brief, en orden. Al cerrar cada una: tests en verde, commit,
docs/ESTADO.md al día y una revisión del subagente "revisor". Si datos/casos/ está vacío, hacé
todo con casos sintéticos y dejá la validación histórica (F4) lista para correr cuando lleguen
los datos.

Cuando algo del negocio no esté claro, elegí lo más razonable, anotalo en docs/DECISIONES.md y
dejá la pregunta en docs/PREGUNTAS_ABIERTAS.md con la opción que usaste. Nunca inventes datos en
silencio y no hagas nada irreversible.

Al terminar, o si la sesión se está por cortar:
- docs/ESTADO.md al día;
- un PR con todo;
- un último mensaje con qué anda, cómo lo pruebo en mi PC paso a paso, los números de la
  validación, qué falta y qué tengo que contestar yo.

Arrancá por la fase F0.
```

---

## Prompt 2 — seguir (sesiones siguientes)

```text
Seguí con el optimizador de corte. Leé CLAUDE.md y docs/ESTADO.md. Aplicá primero las respuestas
nuevas que haya en docs/PREGUNTAS_ABIERTAS.md y después continuá con la próxima fase pendiente
de docs/BRIEF_OPTIMIZADOR.md, con las reglas de siempre: trabajás solo sin preguntar; al cerrar
cada fase, commit y docs/ESTADO.md al día; revisión del subagente "revisor" y PR al final, con
un mensaje de cierre para mí.
```

---

## Prompt 3 — llegaron los casos históricos

```text
Llegaron los casos históricos del optimizador de corte. Están en datos/casos/, o adjuntos en
este mensaje: en ese caso, verificá que no tengan nombres de clientes y guardalos ahí. Leé
CLAUDE.md, docs/ESTADO.md y docs/CONTRATO_DATOS.md y hacé la fase F4 del brief:
1. Encontrá y documentá los formatos de la leyenda (docs/FORMATO_LEYENDAS.md), con su cobertura.
2. Reconstruí las piezas por material y controlalas contra los m² de la leyenda.
3. Calibrá las hipótesis H0 a H2 sobre el 70 % de los casos e informá sobre el 30 % restante en
   docs/VALIDACION.md, con la página de revisión.
Empezá con una muestra de 50 casos y dejá escrita la cobertura antes de correr todo. Al
terminar: ESTADO.md, revisor, PR y un mensaje para mí con los números en palabras simples.
```
