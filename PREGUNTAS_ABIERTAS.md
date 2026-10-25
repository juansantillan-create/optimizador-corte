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

**4. Pulido recto "+3 mm": ¿en las dos medidas (ancho y largo)?**
- ¿Se cargaba así en Corte Certo?
- ¿El pulido de aristas (MF) suma algo?
- **Por defecto**: no se suma en "Como Corte Certo hoy"; en "Reglas de corte", +3 en ancho y en
  largo para las clases con PR.
- Respuesta:

**5. En los montajes de Corte Certo, ¿qué quieren decir los colores bordó, verde y oliva?**
- El amarillo es sobrante.
- **Por defecto**: bordó = pieza, verde = pieza girada, oliva = retazo aprovechable.
- Respuesta:

**6. "Cálculo especial de perímetro": ¿se usa? ¿para qué?**
- **Por defecto**: se muestra en 0,00, como en la captura.
- Respuesta:

**7. ¿Podés mandar capturas de las pestañas "Descripción" y "Propiedades comerciales" de un
material en Corte Certo?**
- **Por defecto**: campos provisorios (código, descripción, color, espesor; precio por m²).
- Respuesta:

**8. ¿Dónde se anotó lo que dio Corte Certo en los presupuestos viejos?**
- ¿Siempre en el mismo campo? ¿Con un formato fijo?
- Pasá 3 o 4 ejemplos, aunque sea a mano.
- **Por defecto**: buscar en `PRESUP.TV_DESCRIP`.
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
- **Por defecto**: sin límite (guillotina libre).
- Respuesta:

**17. Corte Certo usa códigos de material propios (5 = "5 mm Incoloro", 2004 = ?). ¿Hay una
tabla que los relacione con los códigos de Metrix?**
- Sirve si las leyendas viejas nombran el material con el código de Corte Certo.
- Respuesta:

## Respondidas

(todavía ninguna)
