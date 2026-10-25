# Cómo cotizar con el optimizador

Lo mismo que hoy se hace con Corte Certo, en el navegador. Para instalarlo: `docs/INSTALACION.md`.

## En 1 minuto

1. Doble clic en **`Abrir_Optimizador.bat`** (se abre el navegador).
2. Arriba, en **Configuración**, dejá **"Como Corte Certo hoy"** (es lo que se usa en la oficina:
   la plancha con el corte banda, sin separación entre piezas y +3 mm en las piezas con pulido
   recto).
3. Pestaña **Proyecto**: poné el **código** (el número de presupuesto) y una descripción.
4. En Excel, seleccioná las celdas de las piezas (**material, cantidad, ancho, largo**; si querés,
   descripción y clase), copiá con **Ctrl+C**, volvé al optimizador y apretá **Ctrl+V**. Se abre
   una **vista previa**: revisá que las columnas estén bien y apretá **"Agregar al proyecto"**.
5. Apretá **Calcular ▶**. Primero muestra lo que conviene mirar (materiales que no están en la
   planilla, piezas que no entran…) y, si hay algo, pregunta si calcular igual. Después aparece
   "Cálculo en proceso".
6. Al terminar se abre **Resultados**: el **Informe de cálculo** (como el de Corte Certo) y, abajo,
   los **montajes** de cada material. Las planchas, los m² y el aprovechamiento están ahí.
7. **Imprimir informe** o **Imprimir montajes** (en la impresora o "Guardar como PDF").

## Las pestañas

### Proyecto

- La grilla se edita como una planilla: Enter baja a la fila de abajo (y agrega una si es la
  última). ✕ borra el renglón.
- **Material**: el código de Metrix (FL5IN, LX4+4IN…).
- **Medidas en milímetros**. Cuál es el ancho y cuál el largo da igual si la pieza se puede girar.
- **Gira**: "material" = lo que diga el material (normalmente sí); "no" para una pieza que no se
  puede girar.
- **Clase**: si tiene "PR" (por ejemplo "FLOAT PR TEMP"), se le suman **3 mm al ancho y al largo**
  (pulido recto, como se hacía en Corte Certo).
- **Importar archivo…**: CSV, Excel (`.xlsx`) o la planilla `.xls` de la Interfaz de Metrix (un
  DVH se convierte en sus 2 vidrios; los herrajes se ignoran; la planilla de la Interfaz también se
  reconoce si se pega o se guarda como `.xlsx`). Siempre muestra la vista previa. Los encabezados
  pueden tener otros nombres ("Cant. pzas", "Alto (mm)"…) o un título arriba; si no encuentra la
  columna de la cantidad, lo avisa y toma 1 por renglón.
- **Guardar** / **Abrir…**: los proyectos quedan en la carpeta `proyectos` del programa. Si dos
  códigos van al mismo archivo ("11580/A" y "11580 A"), pregunta antes de reemplazar.
- **Revisar**: muestra los avisos sin calcular.

### Materiales

- La lista de los materiales de la planilla de medidas (`Medidas_hojas.xlsx`).
- **Propiedades físicas**: los mismos campos que en Corte Certo (ancho de la sierra, destaque,
  rotación, textura, retazo, constante, márgenes…). El número rojo entre paréntesis es el valor de
  la configuración elegida arriba.
- **Planchas**: las medidas de plancha del material. Destildá una para no usarla.
- **Ok (guardar en esta PC)**: los cambios quedan guardados en esta PC (`config\local`) y se marcan
  con ✎ en la lista. El ancho de la sierra, el destaque y el pulido recto valen **solo para la
  configuración elegida arriba** (cada una los pone a su manera); lo demás vale para todas.
  **"Volver a los valores de la configuración"** los borra. No se aceptan valores negativos.

### Calcular

Como la pantalla de Corte Certo: material en curso, tiempo de cálculo, estimado y restante, la torta
con el % y la cantidad de montajes armados. **Cancelar** se queda con lo mejor encontrado hasta ese
momento (termina el paso que está haciendo, puede tardar unos segundos). Mientras calcula no se
puede empezar otro cálculo.

### Resultados

- **Informe de cálculo**: proyectos calculados, lista de materiales (piezas, m², layouts,
  planchas, m², aprovechamiento) y planchas usadas. Abajo, en un recuadro aparte, lo que agrega el
  optimizador: si pasó el **validador**, el mínimo teórico, los m² de hoja entera, el peso y los
  avisos.
- **Montajes**: "Datos generales" (cantidad de montajes, total de chapas, aprovechamiento,
  pérdida) y los dibujos. Un montaje que se corta en varias planchas se ve **apilado** con "×N".
  Clic en un dibujo → el detalle con las medidas, los sobrantes y los cortes en orden.
- **Consumo a Excel / CSV**: material, medida de plancha, cantidad de planchas, m² y montajes.

### Comparar

Para comparar con lo que dio Corte Certo: escribí sus planchas (y si querés layouts y
aprovechamiento) al lado de cada material; la diferencia sale en verde (a favor) o rojo (en contra).

## Arriba a la derecha

| Opción | Qué hace |
|---|---|
| Configuración | **Como Corte Certo hoy** (por defecto) o **Reglas de corte (Lucas)**: además separa las piezas 20/30/50 mm según el espesor. El informe dice siempre cuál se usó |
| Esfuerzo | **Normal** (lo recomendado: segundos). **Rápido**: solo la primera solución (para ver rápido). **Máximo**: busca más (puede tardar minutos) |
| Decimales | Punto (como Corte Certo) o coma |

## Qué quiere decir cada aviso

| Aviso | Qué pasa |
|---|---|
| "no está en config/hojas.csv: se usa una plancha SUPUESTA" | El material no está en la planilla de medidas: se calculó con 3600 × 2500 y la banda de su espesor. **Revisar** antes de cotizar (pregunta 14) |
| "no entra en ninguna plancha" | La pieza es más grande que la plancha útil: no se calcula. Revisar la medida |
| "entraría girada, pero el material no permite girarla" | El material tiene veta o está marcado sin rotación |
| "separación supuesta" | Con "Reglas de corte", el material no está en la regla de Lucas: se usa la de su espesor (pregunta 15) |
| "medida muy chica" | Menos de 50 mm: ¿está en milímetros? |
| "RESULTADO INCOMPLETO" (en rojo) | Alguna pieza no se calculó (no entra, material sin planchas, un valor del material imposible): las planchas no la incluyen. Ver los errores |
| "Validador: FALLÓ" (en rojo) | El resultado tiene un error: **no usarlo** y avisar |

## Números: cómo se calculan (iguales a Corte Certo)

- m² de piezas = Σ ancho × largo × cantidad ÷ 1.000.000 (6 decimales), con el +3 mm del pulido
  recto.
- m² de planchas = planchas × medida **útil** (por ejemplo 3580 × 2500 = 8,95 m²).
- Aprovechamiento = m² de piezas ÷ m² de planchas × 100 (2 decimales). Pérdida = 100 − eso.
- Perímetro = Σ 2 × (ancho + largo) × cantidad ÷ 1000.
- Mínimo teórico (agregado): con menos planchas que eso no se puede.
