# Entendimiento (fase F0, 25/10/2026)

Qué entendí después de leer todo el repo, qué me hizo dudar y cómo lo voy a encarar.

## Qué es, en pocas palabras

Un programa que corre en una PC de la oficina y, para **cotizar**, hace lo mismo que hoy hace
Corte Certo v3.9K: le das la lista de vidrios de un presupuesto (material, cantidad, ancho,
largo) y te dice cuántas planchas hacen falta, cómo se acomodan las piezas (los montajes) y el
aprovechamiento. Tiene que dar **los mismos números con las mismas fórmulas** y mostrarse **como
Corte Certo**, para que la oficina no se pierda. Además, tiene que poder llamarlo el orquestador
como una función de Python o un JSON (para el "portón de producción", donde se controla el
consumo de hojas). No manda nada a las mesas de corte: eso sigue siendo Optima.

## Lo que saqué de las capturas

- **Informe (captura 1)**: las cuentas cierran exactas. 82 planchas × 3,58 × 2,5 = 733,9 m² (se
  cuenta la plancha **útil**, sin el corte banda) y 564,583068 ÷ 733,9 = 76,93 %.
- **Montajes (captura 2)**: medí los dibujos en píxeles (≈ 22,7 mm por píxel en los dos ejes).
  - Las piezas del 413 son grandes y variadas: ~1000 × 2385, ~1130 × 2385, ~1880 × 1000,
    ~1590 × 790, ~1400 × 1000… Hay muchas medidas distintas, no 3.
  - **El primer corte es vertical** (tiras del alto de la plancha, de izquierda a derecha);
    adentro de cada tira se corta horizontal y a veces hay un tercer corte (montajes 3 y 13).
    Es guillotina de 3 etapas.
  - El sobrante queda **arriba y a la derecha**: las piezas se acomodan desde abajo a la
    izquierda, como nuestro origen de coordenadas.
  - **Los colores** son exactamente los de la paleta clásica de Windows: bordó = `(128,0,0)`,
    verde = `(0,128,0)`, oliva = `(128,128,0)` y amarillo = `(255,255,0)`. Son el 2.º, 3.º y 4.º
    color de esa paleta, en orden. No es "oliva = retazo" ni "verde = girada" (en el montaje 8
    hay una oliva y dos verdes de la misma medida y orientación), ni "un color por medida" (el
    bordó aparece en al menos 3 medidas). Lo que cierra con todo es "un color por renglón del
    proyecto, rotando entre 3", pero es una suposición. Para nuestro dibujo uso una regla propia
    que se lee mejor: un color por tipo de pieza con la misma paleta (pregunta 5).
- **Propiedades físicas (captura 4)**: todo en 0 (sierra, destaque, constante, márgenes). En
  Corte Certo la única regla es la plancha ya achicada a 3580 × 2500.

## Las dos configuraciones

- **"Como Corte Certo hoy"** (por defecto): plancha útil = plancha − corte banda; sin separación.
- **"Reglas de corte (Lucas)"**: además, 20/30/50 mm entre piezas.
- Todo editable por material. La validación histórica (F4) dice cuál reproduce a Corte Certo
  (hipótesis H0 a H3).

## Lo que me hizo dudar (y qué hago mientras tanto)

| Duda | Qué hago por defecto | Dónde |
|---|---|---|
| Qué significan los colores | Regla propia: un color por tipo de pieza, con la paleta de Corte Certo | Pregunta 5 |
| Con textura, qué lado de la pieza va con la veta (Metrix no dice la orientación) | Veta horizontal: el **largo** de la pieza va a lo largo de la plancha (eje X); vertical: a lo ancho (eje Y) | Pregunta 18 (nueva) |
| Varias medidas de plancha en un material | Todas habilitadas, se mezclan y gana la de menos m² | Pregunta 3 |
| "Destaque mínimo" exacto | Ningún sobrante que haya que separar con un corte puede medir menos que el destaque (salvo 0) | Pregunta 2 |
| Cuántas etapas de corte | No se configura un límite: el generador arma montajes de 3 o 4 etapas (como la captura) y el validador acepta cualquier guillotina | Pregunta 16 |
| Corte Certo usa la plancha "acostada" y el primer corte vertical | Igual: primero se prueban tiras verticales y después horizontales, y se queda con lo mejor | — |
| Reproducibilidad entre la nube y la PC | Límites por cantidad de trabajo (iteraciones, nodos), no por reloj; versiones fijas de numpy/scipy. Igual puede haber diferencias mínimas entre Linux y Windows: se controla con el banco de pruebas | Decisiones |
| Python de la PC de Juan | Funciona con 3.10 o más nuevo; se recomienda 3.12 o 3.13 (mismas versiones que en la nube), instalado "solo para mí" | `requirements.txt`, pregunta 20 |
| Instalación sin internet | La primera instalación baja los paquetes de internet; para la PC sin internet se puede llevar una carpeta con los paquetes ya bajados (F5) | `INSTALACION.md` |

## Cómo lo voy a encarar (el motor)

1. **Agrupar** las piezas iguales (material, medida, rotación) en tipos con cantidad.
2. **Generador de montajes** de guillotina por etapas (estilo Gilmore–Gomory):
   - tiras con el ancho de alguna pieza; adentro, "renglones" de piezas (mochila 1D), y las
     tiras se combinan a lo largo de la plancha (otra mochila 1D);
   - las dos orientaciones del primer corte;
   - con separación (se agranda cada pieza y la plancha en la separación) y destaque (un
     sobrante es 0 o al menos el destaque);
   - las mochilas en numpy, con cotas por cantidad pedida.
3. **Heurística rápida** (siempre disponible, < 2 s): "secuencial": arma el mejor montaje para
   lo que falta, lo repite todas las veces que se pueda, y sigue. Da pocos montajes con muchas
   repeticiones, como Corte Certo. Es el piso si lo demás falla.
4. **Generación de columnas + programación entera** (HiGHS, que viene con scipy):
   - la relajación lineal da un "precio" por tipo de pieza; con esos precios el generador busca
     montajes mejores;
   - después, programación entera en dos pasos: (a) menos m² de plancha; (b) con esos m²,
     menos montajes distintos;
   - las piezas de más se sacan (quedan como sobrante) para que las cantidades den exactas;
   - el sobrante se junta en la última plancha (se reacomodan las planchas menos llenas).
5. **Cota inferior** ("mínimo teórico"): ⌈área de piezas ÷ área útil⌉ y las piezas que no
   pueden compartir plancha.
6. **Validador independiente**: código aparte, simple, que no usa nada del motor. Revisa
   adentro de la plancha, sin solaparse, separación, destaque, guillotina (descomposición
   recursiva), rotación, textura, cantidades exactas y que los m² y el aprovechamiento
   recalculados coincidan. Corre en cada cálculo y en todos los tests.

## Plan por fases

| Fase | Qué voy a entregar |
|---|---|
| F0 | Este archivo, `INVENTARIO.md`, preguntas al día, repo ordenado, esqueleto del paquete `optimizador/` |
| F1 | Motor + validador + banco sintético ("corte perfecto" y realistas) + CLI; tiempos medidos; `VALIDACION.md` |
| F2 | Informe de cálculo y montajes en SVG (como las capturas 1 y 2), impresión A4, JSON y `API.md` |
| F3 | Interfaz en el navegador (FastAPI + HTML/JS sin compilar), `Abrir_Optimizador.bat`, importadores (pegar de Excel, CSV/XLSX, Interfaz de Metrix), presets |
| F4 | Lector de leyendas, reconstrucción de piezas, calibración H0–H3 (70/30), página de revisión. Sin datos: de punta a punta con un caso de juguete claramente inventado |
| F5 | `INSTALACION.md`, `USO.md`, `ESTADO.md` final, PR |

## Riesgos

- **Sin casos históricos** todavía: el motor se valida con casos sintéticos de óptimo conocido;
  la comparación con Corte Certo queda lista para cuando lleguen.
- **Velocidad en Python**: las mochilas van en numpy y con caché; se mide en la nube y se deja
  un comando de benchmark para la PC de Juan.
- **Cotizar con más o menos planchas que Corte Certo** cambia el precio: por eso el informe
  dice siempre con qué preset y valores se calculó, y el mínimo teórico.
