# API: la función `optimizar()`, la línea de comandos y el JSON

Para el orquestador (o cualquier script). La interfaz en el navegador usa exactamente lo mismo.

## Cómo se llama

**Desde Python** (sin estado global; se puede importar desde otro proyecto):

```python
from optimizador.api import optimizar

resultado = optimizar(entrada)            # entrada y resultado: dicts (el JSON de abajo)
if not resultado["verificado"]:
    print(resultado["validacion"])        # el validador encontró un problema: no usar
elif not resultado["completo"]:
    print("faltan piezas")                # hay piezas que no se calcularon: ver los errores
```

Opcionales: `optimizar(entrada, progreso=f, cancelar=g)`. `progreso(**datos)` se llama mientras
calcula (`material`, `fase`, `planchas`, `montajes`, `iteracion`…); `cancelar()` devuelve `True`
para cortar y quedarse con la mejor solución encontrada hasta ese momento.

**Desde la consola**:

```text
python -m optimizador calcular proyecto.json -o resultado.json --html informe.html
python -m optimizador calcular proyecto.json --preset lucas --esfuerzo rapido
python -m optimizador materiales FL5IN        # ver las planchas configuradas de un material
python -m optimizador banco                   # banco de pruebas (sirve de benchmark)
python -m optimizador historico --todo --procesos 3 --docs   # contra los casos de Corte Certo
python -m optimizador optima --docs          # contra los lotes cortados con Optima
python -m optimizador servidor                # la interfaz en el navegador
```

Opciones de `calcular`: `-o resultado.json`, `--html informe.html` (informe + montajes para
imprimir), `--coma` (coma decimal en el HTML), `--preset`, `--esfuerzo`, `--silencioso`.

Para exportar el consumo a planilla desde Python: `optimizador.exportar.a_csv(resultado)` (coma
decimal, `;`) o `a_xlsx(resultado, "consumo.xlsx")`.

Código de salida: 0 = resultado verificado y completo, 1 = el validador encontró un problema,
2 = no se pudo leer la entrada o el resultado está **incompleto** (alguna pieza no se calculó).

## Entrada

```json
{
  "proyecto": {"codigo": "11580", "descripcion": "Presupuesto 11580"},
  "preset": "corte_certo",
  "piezas": [
    {"item": "1", "material": "FL5IN", "cantidad": 4, "ancho": 1200, "largo": 2400,
     "descripcion": "paño fijo", "origen": {"presupuesto": 11580, "renglon": 3}},
    {"item": "2", "material": "FL5IN", "cantidad": 2, "ancho": 1000, "largo": 600,
     "clase": "FLOAT PR TEMP"}
  ],
  "materiales": {"FL5IN": {"separacion_piezas_mm": 0}},
  "opciones": {"esfuerzo": "normal"},
  "fecha": "2026-10-25 10:00:00"
}
```

| Campo | Qué es |
|---|---|
| `proyecto` | código y descripción (van al informe) |
| `preset` | `corte_certo` ("Como Corte Certo hoy", por defecto), `lucas` ("Reglas de corte"), o las hipótesis `H0`, `H1`, `H2` de la validación |
| `piezas[]` | un renglón por medida. `material` = código de Metrix; `cantidad`, `ancho`, `largo` en mm enteros (como texto también vale "1.200" = 1200) |
| `piezas[].rota` | `true`/`false`; si no viene, lo que diga el material |
| `piezas[].clase` o `pulido_recto` | si la clase tiene "PR" (o `pulido_recto: true`) se suman 3 mm al ancho y al largo (confirmado por Juan) |
| `piezas[].sobremedida_mm` | sobremedida extra opcional (se suma a las dos medidas) |
| `materiales` | ajustes por material encima del preset (el código, sin importar mayúsculas): cualquier campo de "Propiedades físicas" (ver abajo), `planchas` (lista que reemplaza a la de `hojas.csv`) o `planchas_habilitadas` (`{"3600x2200": false}`). Un valor que no se puede usar (negativo, no numérico, textura desconocida) deja ese material sin calcular, con el error |
| `opciones.esfuerzo` | `rapido` (solo la heurística: menos de 2 s en un presupuesto típico; con cientos de medidas distintas, 10 a 70 s), `normal`, `maximo` |
| `fecha` | opcional; si no viene, la hora actual (es lo único que cambia entre dos corridas iguales) |

Campos de material que se pueden ajustar: `separacion_piezas_mm` (ancho de la sierra),
`destaque_min_mm`, `genera_retazo`, `retazo_ancho_min_mm`, `retazo_largo_min_mm`, `usar_area_min`,
`retazo_area_min_m2`, `rotacion`, `textura` (`sin`/`horizontal`/`vertical`; también "Sem" = sin), `constante_ancho_mm`,
`constante_largo_mm`, `margen_arriba_mm`, `margen_abajo_mm`, `margen_izquierda_mm`,
`margen_derecha_mm`, `corte_max_libre`, `corte_max_mm`, `sobremedida_pulido_mm`, `espesor_mm`,
`peso_kg_m2`, `descripcion`, `color`.

## Salida

Lo principal (los mismos números que el informe de Corte Certo):

| Campo | Qué es |
|---|---|
| `verificado` | `true` si pasó el **validador independiente**; si es `false`, `validacion` dice por qué y el resultado no se debe usar |
| `completo` | `true` si se calcularon **todas** las piezas. Si es `false` (una pieza no entra, un material sin planchas o con una configuración imposible), las planchas no las incluyen: ver `errores` |
| `materiales[].calculado` | `false` si ese material no se calculó (no tiene montajes) |
| `materiales[]` | uno por material, en el orden en que aparecen |
| `materiales[].piezas`, `m2_piezas` | cantidad de piezas y m² (6 decimales, con el +3 del pulido recto). No cuentan los renglones con error (que no se calcularon) |
| `m2_piezas_presupuesto` | m² con las medidas del presupuesto (sin el +3) |
| `layouts`, `planchas`, `m2_planchas` | montajes distintos, planchas y m² de plancha **útil** |
| `aprovechamiento`, `perdida` | m² de piezas ÷ m² de planchas × 100, 2 decimales; pérdida = 100 − aprovechamiento |
| `planchas_usadas[]` | cantidad, ancho y largo útiles, tipo ("Plancha"), medida de la hoja entera y si es **supuesta** |
| `perimetro_m` | Σ 2 × (ancho + largo) × cantidad ÷ 1000 |
| `calculo_especial_perimetro_m` | siempre 0 (no sabemos qué es; pregunta 6) |
| `minimo_teorico_planchas` | agregado propio: cota inferior (no se puede hacer con menos) |
| `m2_hoja_entera`, `peso_planchas_kg`, `peso_piezas_kg` | agregados propios |
| `configuracion` | todos los valores con que se calculó ese material (preset + ajustes) |
| `tipos[]` | las piezas agrupadas por medida: ítems (si dos renglones tienen la misma medida se juntan y el ítem sale como "1+3"), medida del presupuesto (`ancho_presupuesto`, `largo_presupuesto`), medida con el +3 (`ancho`, `largo`), medida de corte, cantidad, color del dibujo |
| `avisos[]`, `errores[]` | lo que hay que mirar (material supuesto, pieza que no entra, etc.); también hay `avisos` y `errores` generales |
| `calculo` | segundos, trabajo hecho y valor de la relajación lineal (diagnóstico, no es un mínimo) |

Cada montaje (`materiales[].montajes[]`):

| Campo | Qué es |
|---|---|
| `numero`, `repeticiones` | número de montaje y en cuántas planchas se corta igual |
| `plancha` | medida útil (`ancho` = X = lado largo, `largo` = Y), hoja entera y corte banda |
| `piezas[]` | `x`, `y` (abajo a la izquierda, mm), `ancho` (en X) y `largo` (en Y) **como quedan en la plancha**, `tipo`, `item`, `girada` |
| `sobrantes[]` | rectángulos que sobran: `x`, `y`, `ancho`, `largo`, `tipo` (`retazo` o `desperdicio`) |
| `cortes[]` | en orden: `nivel` (1 = de lado a lado de la plancha), `vertical`, `posicion`, `desde`, `hasta` |
| `etapas`, `m2_piezas`, `aprovechamiento` | etapas de corte del montaje y sus números |

"Girada" quiere decir que la pieza va con su **ancho** a lo largo del eje Y (sin girar, el ancho va
en X, a lo largo del lado largo de la plancha).

## Ejemplo de salida (recortado)

La salida real de la entrada de arriba (con `configuracion`, `calculo`, los cortes y los montajes recortados con "..."):

```json
{
 "version": "0.0.1",
 "fecha": "2026-10-25 10:00:00",
 "proyecto": {
  "codigo": "11580",
  "descripcion": "Presupuesto 11580"
 },
 "preset": "corte_certo",
 "preset_nombre": "Como Corte Certo hoy",
 "esfuerzo": "normal",
 "piezas": 6,
 "materiales": [
  {
   "codigo": "FL5IN",
   "descripcion": "FL 5 MM INC",
   "configuracion": {
    "color": "",
    "separacion_piezas_mm": 0,
    "destaque_min_mm": 0,
    "rotacion": true,
    "textura": "sin",
    "sobremedida_pulido_mm": 3,
    "...": "...",
    "planchas": [
     {
      "ancho": 3600,
      "largo": 2500,
      "corte_banda": 20,
      "habilitada": true,
      "supuesta": false,
      "origen": "MONOLITICO fila 37"
     }
    ]
   },
   "piezas": 6,
   "m2_piezas": 12.729618,
   "m2_piezas_presupuesto": 12.72,
   "perimetro_m": 35.22,
   "calculo_especial_perimetro_m": 0.0,
   "tipos": [
    {
     "tipo": 1,
     "items": [
      {
       "item": "1",
       "cantidad": 4
      }
     ],
     "ancho_presupuesto": 1200,
     "largo_presupuesto": 2400,
     "ancho": 1200,
     "largo": 2400,
     "ancho_corte": 1200,
     "largo_corte": 2400,
     "cantidad": 4,
     "rota": true,
     "color": "#800000"
    },
    {
     "tipo": 2,
     "items": [
      {
       "item": "2",
       "cantidad": 2
      }
     ],
     "ancho_presupuesto": 1000,
     "largo_presupuesto": 600,
     "ancho": 1003,
     "largo": 603,
     "ancho_corte": 1003,
     "largo_corte": 603,
     "cantidad": 2,
     "rota": true,
     "color": "#008000"
    }
   ],
   "avisos": [],
   "errores": [],
   "calculado": true,
   "layouts": 2,
   "planchas": 2,
   "m2_planchas": 17.9,
   "aprovechamiento": 71.12,
   "perdida": 28.88,
   "planchas_usadas": [
    {
     "cantidad": 2,
     "ancho": 3580,
     "largo": 2500,
     "tipo": "Plancha",
     "hoja_ancho": 3600,
     "hoja_largo": 2500,
     "supuesta": false
    }
   ],
   "montajes": [
    {
     "repeticiones": 1,
     "plancha": {
      "ancho": 3580,
      "largo": 2500,
      "hoja_ancho": 3600,
      "hoja_largo": 2500,
      "corte_banda": 20,
      "supuesta": false
     },
     "piezas": [
      {
       "tipo": 1,
       "item": "1",
       "x": 0,
       "y": 0,
       "ancho": 1200,
       "largo": 2400,
       "girada": false
      },
      {
       "tipo": 1,
       "item": "1",
       "x": 1200,
       "y": 0,
       "ancho": 1200,
       "largo": 2400,
       "girada": false
      },
      {
       "tipo": 2,
       "item": "2",
       "x": 2400,
       "y": 0,
       "ancho": 603,
       "largo": 1003,
       "girada": true
      },
      {
       "tipo": 2,
       "item": "2",
       "x": 2400,
       "y": 1003,
       "ancho": 603,
       "largo": 1003,
       "girada": true
      }
     ],
     "sobrantes": [
      {
       "x": 0,
       "y": 2400,
       "ancho": 1200,
       "largo": 100,
       "tipo": "desperdicio"
      },
      {
       "x": 1200,
       "y": 2400,
       "ancho": 1200,
       "largo": 100,
       "tipo": "desperdicio"
      },
      {
       "x": 2400,
       "y": 2006,
       "ancho": 603,
       "largo": 494,
       "tipo": "desperdicio"
      },
      {
       "x": 3003,
       "y": 0,
       "ancho": 577,
       "largo": 2500,
       "tipo": "desperdicio"
      }
     ],
     "cortes": [
      {
       "nivel": 1,
       "vertical": true,
       "posicion": 1200,
       "desde": 0,
       "hasta": 2500
      },
      {
       "nivel": 1,
       "vertical": true,
       "posicion": 2400,
       "desde": 0,
       "hasta": 2500
      },
      "..."
     ],
     "etapas": 2,
     "m2_piezas": 6.969618,
     "aprovechamiento": 77.87,
     "numero": 1
    }
   ],
   "minimo_teorico_planchas": 2,
   "m2_hoja_entera": 18.0,
   "peso_piezas_kg": 159.1,
   "peso_planchas_kg": 225.0,
   "calculo": {
    "segundos": "…",
    "trabajo": "…",
    "origen": "secuencial (1.5)",
    "relajacion_lineal_m2": null
   }
  }
 ],
 "avisos": [],
 "errores": [],
 "completo": true,
 "verificado": true,
 "validacion": []
}
```

## Garantías

- **Reproducible**: la misma entrada con la misma configuración da el mismo resultado (salvo
  `fecha` y los segundos de `calculo`). El trabajo se corta por cantidad, no por reloj; si alguna
  vez se llega al límite de seguridad por tiempo, sale un aviso.
- **Nunca inventa en silencio**: material que no está en `hojas.csv` → plancha supuesta con aviso;
  pieza que no entra o con datos inválidos → error por pieza, y los demás se calculan igual.
- **Todo resultado pasa por el validador** (`optimizador/validador.py`), que no comparte código
  con el motor y arma de nuevo la configuración de cada material desde la entrada.
