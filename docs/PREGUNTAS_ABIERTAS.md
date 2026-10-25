# Preguntas abiertas (para Juan)

Contestá en texto libre debajo de cada una ("sí", "no, va con 20", "preguntale a Lucas"…). La
próxima sesión lee las respuestas, las aplica, anota la decisión en `DECISIONES.md` y la mueve a
"Respondidas". Mientras tanto, el programa usa la opción **por defecto**.

## Abiertas

**1. ¿Corte Certo se usaba con separación entre piezas?**
- **Por qué importa**: cambia cuántas planchas da.
- **Hoy creemos**: no. Solo se carga la plancha achicada (3580 × 2500): la captura de
  Propiedades físicas tiene todo en 0.
- **Por defecto**: preset "Como Corte Certo hoy", sin separación. La validación con los casos
  viejos lo va a confirmar.
- Respuesta:

**2. En la mesa, "20 mm de distancia mínima entre piezas", ¿quiere decir…**
- (a) que todas las piezas quedan separadas 20 mm, o
- (b) que pueden compartir el corte, pero si entre dos piezas queda una tira de sobrante, esa
  tira tiene que medir al menos 20 mm?
- **Por defecto**: (a), en el preset "Reglas de corte (Lucas)".
- Respuesta:

**3. Cuando un material tiene varias medidas de plancha, ¿con cuál se cotiza?**
- Ejemplos: FL4IN 3600 × 2500 / 3600 × 2200 / 3300 × 2440; FL10IN 3700 × 2500 / 3700 × 2200 /
  3050 × 2050.
- ¿Se elige una? ¿Se pueden mezclar? ¿Depende del stock?
- **Por defecto**: todas habilitadas y el programa elige la combinación de menos m². Se puede
  deshabilitar una medida por material.
- Respuesta:

**4. (Sigue de la 4 respondida) Pulido: ¿el pulido de aristas (MF) suma algo? ¿Y el +3 mm del
pulido recto se cargaba en las medidas de las piezas en Corte Certo?**
- Lo segundo importa para los números: si se cargaba en las medidas, Corte Certo cuenta los m² de
  piezas (y el aprovechamiento) con las medidas +3.
- **Por defecto**: el MF no suma; el +3 del pulido recto **sí** cuenta en los m² de piezas del
  informe (como si se hubiera cargado así en Corte Certo). El informe muestra además los m² con
  las medidas del presupuesto (sin el +3).
- Respuesta:

**5. En los montajes de Corte Certo, ¿qué quieren decir los colores bordó, verde y oliva?**
- El amarillo es sobrante.
- Lo que se ve midiendo la captura (25/10): son los colores 2, 3 y 4 de la paleta clásica de
  Windows, en orden. Pero ninguna regla simple cierra:
  - en el montaje 8 hay una pieza oliva y dos verdes **de la misma medida y orientación** (no es
    "oliva = retazo" ni "verde = girada");
  - en los montajes 1, 9 y 11 hay piezas bordó y verdes del mismo tamaño, y el bordó aparece en al
    menos 3 medidas distintas (no es "un color por medida": habría más de 3 colores).
  - Lo que sí cierra con todo: **un color por renglón del proyecto, rotando entre esos 3**. Es una
    suposición.
- **Por defecto** (cambió el 25/10): regla propia, para que se lea bien: un color por tipo de
  pieza, recorriendo la misma paleta (bordó, verde, oliva, azul marino, violeta, verde azulado…);
  todo el sobrante en amarillo. No pretende copiar la regla de Corte Certo.
- Respuesta:

**6. "Cálculo especial de perímetro": ¿se usa? ¿para qué?**
- **Por defecto**: se muestra en 0,00, como en la captura.
- Respuesta:

**7. ¿Podés mandar capturas de las pestañas "Descripción" y "Propiedades comerciales" de un
material en Corte Certo?**
- **Por defecto**: campos provisorios (código, descripción, color, espesor; precio por m²).
- Respuesta:

**8. (Sigue de la 8 respondida) La leyenda en "Situación de Presupuesto → Observaciones":
¿en qué columna de `PRESUP` queda guardada?**
- Juan cree que es `NOTAS_CAUSA` (en el diccionario figura como "motivo del rechazo", así que hay
  que confirmarlo mirando un presupuesto que tenga la leyenda).
- ¿Siempre con el formato "MATERIAL: NN HOJAS - NN%"? ¿Hay leyendas viejas con otro formato?
- **Por defecto**: el zip trae todas las columnas de texto de `PRESUP` (`NOTAS_CAUSA`,
  `TV_DESCRIP` y cualquier otra de observaciones) y el lector busca la leyenda en todas
  (`docs/CONTRATO_DATOS.md`, versión 2).
- Respuesta:

**9. Para cotizar, ¿el aprovechamiento va sobre la plancha útil o sobre la hoja entera?**
- Plancha útil: 3580, como Corte Certo. Hoja entera: 3600.
- **Por defecto**: como Corte Certo. La hoja entera se informa aparte.
- Respuesta:

**10. ¿Hay vidrios que no se pueden girar?**
- Por el dibujo o la veta: catedral, martelé, stipolite, esmerilado…
- **Por defecto**: todos se pueden girar, como en la captura.
- Respuesta:

**11. ¿Se cotiza alguna vez con retazos de stock?**
- En Corte Certo existe "Planchas / offcuts usados".
- **Por defecto**: no, solo planchas enteras.
- Respuesta:

**12. ¿Corte Certo guarda los proyectos? ¿Dónde?**
- El de la captura es el 413.
- Si se pueden copiar, son casos perfectos para validar (ver `CONTRATO_DATOS.md`, fuente B).
- Respuesta:

**13. ¿Podés pasar una planilla de la Interfaz de ejemplo, sin nombres de clientes?**
- Sirve para confirmar qué hay en cada columna, de la A a la P (CANTIDAD, CLASE, etc.).
- Respuesta:

**14. Materiales que no están en `Medidas_hojas.xlsx` (por ejemplo FL8BR u otros colores): ¿qué
plancha llevan?**
- **Por defecto**: 3600 × 2500, con la banda de su espesor, marcada como "supuesta" en el
  informe.
- Respuesta:

**15. La separación de los materiales que no menciona la regla de Lucas, ¿es igual a la del
float o del laminado del mismo espesor?**
- Son 45 materiales: float 3 mm, 5+3, 6+6, catedral, Cool Lite, Eclipse, espejos, etc.
- **Por defecto**: sí (columna `separacion_fuente` de `config/hojas.csv`).
- Respuesta:

**16. ¿Las mesas u Optima limitan las etapas de corte (X, Y, Z)?**
- Para cotizar no cambia tanto, pero sirve para que el montaje sea cortable de verdad.
- **Por defecto**: no se configura un límite. El generador arma montajes de 3 o 4 etapas (como
  los de la captura de Corte Certo) y el validador acepta cualquier guillotina.
- Respuesta:

**17. Corte Certo usa códigos de material propios (5 = "5 mm Incoloro", 2004 = ?). ¿Hay una
tabla que los relacione con los códigos de Metrix?**
- Sirve si las leyendas viejas nombran el material con el código de Corte Certo.
- Respuesta:

**18. Con textura (veta), ¿qué lado de la pieza va con la veta?**
- En Metrix, LARGO y ANCHO de una pieza no dicen la orientación. Con rotación permitida da igual;
  con veta, no.
- **Por defecto**: veta "Horizontal" = el **largo** de la pieza va a lo largo de la plancha (el
  lado de 3580); "Vertical" = el largo va a lo ancho (el lado de 2500). La pieza no se gira.
- Ojo: sin veta y sin rotación, la pieza va como se cargó, con su **ancho** a lo largo de la
  plancha (la convención de `CLAUDE.md`). Con veta horizontal queda al revés (el largo en X).
- Respuesta:

**19. Cuando se mezclan planchas de distinta medida en un material, ¿alcanza con que el
programa elija la combinación de menos m²?**
- Ejemplo: 3 planchas de 3600 × 2500 o 2 de 3600 × 2500 + 1 de 3600 × 2200.
- **Por defecto**: sí, gana la de menos m² de plancha útil; si empatan, la de menos montajes.
- Respuesta:

**20. ¿Qué Python tiene (o puede tener) la PC de la oficina?**
- El programa anda con Python 3.10 o más nuevo, pero los resultados son idénticos a los de la
  nube solo con 3.12 o más nuevo (mismas versiones de las librerías de cálculo).
- **Por defecto**: la instalación recomienda Python 3.12 o 3.13 de python.org, instalado "solo
  para mí" (no pide permisos de administrador).
- Respuesta:

**21. Nombres de compañeros en los documentos de la fábrica: ¿los dejamos?**
- No son clientes, pero el revisor encontró en `contexto/fabrica/` el usuario de Windows de un
  compañero (en rutas como `C:\Users\…`) y nombres de pila de empleados, y en las propiedades de
  `config/fuentes/Medidas_hojas.xlsx` figura quién lo creó.
- **Por defecto**: se dejan como están (la regla de `CLAUDE.md` es sobre clientes).
- Respuesta:

**22. ¿Faltó subir algún archivo?**
- Llegaron `download`, `download (1)` y `download (3)` (falta un `(2)`), y `LEEME.md`, `LEEME (2)`
  y `LEEME (4)` (faltan `(1)` y `(3)`). Por el contenido no parece faltar nada, pero conviene
  confirmarlo.
- **Por defecto**: se sigue con lo que hay.
- Respuesta:

## Respondidas

**4. Pulido recto "+3 mm": ¿en las dos medidas (ancho y largo)? ¿Se cargaba así en Corte Certo?**
- Respuesta de Juan (25/10): **confirmado**, las piezas con pulido recto se optimizaron con +3 mm
  en el ancho **y** en el largo.
- Qué se hizo: el +3 pasó a ser parte de "Como Corte Certo hoy" (y de "Reglas de corte"); la
  hipótesis H3 de la validación dejó de ser hipótesis (`DECISIONES.md`, 25/10). Lo que falta
  (pulido MF y si cuenta en los m²) sigue en la pregunta 4 de arriba.

**8. ¿Dónde se anotó lo que dio Corte Certo en los presupuestos viejos?**
- Respuesta de Juan (25/10): **no** está en `TV_DESCRIP`. Está en la ventana "Situación de
  Presupuesto → Observaciones" de Metrix (columna de `PRESUP` a confirmar; probablemente
  `NOTAS_CAUSA`). Formato real, una línea por material:
  ```
  LISTA 1
  4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10%
  3+3 LOWE: 105 HOJAS - 72% ******* L.DIST -10%
  4+4 LOWE_ 22 HOJAS - 64%******* L.DIST -10%
  ```
  = material abreviado (hay que relacionarlo con el código de Metrix por las piezas del
  presupuesto), hojas, aprovechamiento en %, y cómo se cotizó (lista y descuento).
- Qué se hizo: `CONTRATO_DATOS.md` pasó a la versión 2; el formato quedó en
  `docs/FORMATO_LEYENDAS.md`. Lo que falta confirmar (la columna) sigue en la pregunta 8 de arriba.
