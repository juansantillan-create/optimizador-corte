# Configuración: planchas y reglas de corte

| Archivo | Qué es | ¿Se edita a mano? |
|---|---|---|
| `fuentes/Medidas_hojas.xlsx` | Planilla original de Juan (hojas MONOLITICO y LAMINADO) | Sí, es la fuente. Después hay que regenerar el CSV |
| `fuentes/reglas_corte_2026-10-21.txt` | Texto original de las reglas de Lucas | No: es el registro de lo que se dijo |
| `reglas_corte.csv` | Las reglas por grupo de espesor: corte banda y separación entre piezas | Sí, si cambia una regla |
| `hojas.csv` | **Lo que usa el programa**: una fila por material y medida de plancha | No: se genera |

Para regenerar `hojas.csv` después de tocar el Excel o las reglas:

```
python herramientas/importar_medidas_hojas.py
```

El comando avisa lo que no entiende o lo que no coincide (no adivina).

## Columnas de `hojas.csv`

Separador `;`, UTF-8 con BOM (para que Excel muestre bien las tildes). Medidas en mm.

| Columna | Qué es |
|---|---|
| `codigo`, `descripcion` | Código y descripción de Metrix (FL5IN, "FL 5 MM INC") |
| `hoja_excel`, `fila_excel` | De dónde salió (para revisar contra el Excel) |
| `composicion`, `espesor_mm`, `laminado` | "5" o "4+4"; espesor total de vidrio (4+4 → 8); SI/NO |
| `hoja_ancho_mm`, `hoja_largo_mm` | Plancha entera: **ancho = lado largo** (3600), largo = lado corto (2500) |
| `corte_banda_mm` | Lo que se le saca al lado largo (del Excel) |
| `util_ancho_mm`, `util_largo_mm` | Plancha útil = ancho − banda, y el largo igual (3580 × 2500) |
| `separacion_piezas_mm` | Separación entre piezas según `reglas_corte.csv` (se usa en el preset "Reglas de corte") |
| `separacion_fuente` | `regla de Lucas 21/10/2026` (confirmado, float/Lamilux) o `supuesto …` (ver pregunta 15) |
| `grupo_regla` | Grupo de `reglas_corte.csv` que se aplicó |
| `peso_kg_m2` | 2,5 kg/m² por mm de espesor (calculado, para el "peso específico" de Corte Certo) |
| `avisos` | Lo raro de esa fila (por ejemplo, en LAMINADO el Excel tiene invertidas Descripción y Código) |

**Al 21/10/2026**:
- 101 medidas de plancha y 87 materiales.
- 10 materiales con más de una medida: CK6K1, CT6G2, FL10IN, FL3IN, FL4IN, LX3+3BC, LX3+3GC,
  LX3+3IN, LX4+4IN y OA8IN.
- 45 materiales con separación **supuesta**.
- Ninguna banda del Excel contradice la regla de Lucas.
