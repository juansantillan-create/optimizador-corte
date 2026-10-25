# Formatos de la leyenda de Corte Certo en los presupuestos

La "leyenda" es lo que anotó la oficina en Metrix con el resultado de Corte Certo. Sirve para la
validación histórica (fase F4). Este archivo junta los formatos encontrados, con ejemplos
**anonimizados**, y cómo los lee el programa (`optimizador/historico/leyendas.py`).

## Dónde está

En la ventana **"Situación de Presupuesto → Observaciones"** de Metrix (Juan, 25/10/2026). No está
en `TV_DESCRIP`. La columna de `PRESUP` se confirma al exportar (probablemente `NOTAS_CAUSA`;
pregunta 8). El zip trae todas las columnas de texto y el lector busca en todas.

## Formato A: una línea por material (ejemplo real de Juan, 25/10)

```text
LISTA 1
4+4 NLIGHT: 88 HOJAS - 91% ******* L.DIST -10%
3+3 LOWE: 105 HOJAS - 72% ******* L.DIST -10%
4+4 LOWE_ 22 HOJAS - 64%******* L.DIST -10%
```

| Parte | Ejemplo | Qué es |
|---|---|---|
| material abreviado | `4+4 NLIGHT` | composición + color o tipo, a mano. **No** es el código de Metrix |
| separador | `:` o `_` | a veces es `_` en lugar de `:` (tipeo) |
| hojas | `88 HOJAS` | planchas que dio Corte Certo para ese material |
| aprovechamiento | `91%` | el % de Corte Certo, redondeado a entero |
| cotización | `******* L.DIST -10%` | después de los asteriscos: lista y descuento con que se cotizó. No se usa para optimizar |
| encabezado | `LISTA 1` | línea suelta con la lista de precios. Se guarda como dato, no es un material |

**Cómo se lee** (tolerante, sin adivinar):
- Por línea: `<material> [:_-]? <n> HOJA(S) [-–] <p> %`, sin importar mayúsculas, espacios de más
  ni el espacio que falta antes de los asteriscos. También "PLANCHA(S)" o "CHAPA(S)" en lugar de
  "HOJAS", y coma decimal en el %.
- El material abreviado se relaciona con un código de Metrix usando **las piezas del mismo
  presupuesto**: misma composición (`4+4`, `3+3`, `10`) y palabras clave (`NLIGHT` ↔ `NL` /
  "NEUTRO LIGHT", `LOWE` ↔ `LOW` / "LOW-E", `INC` ↔ `IN`, `GRIS` ↔ `GR`…). Si quedan dos
  candidatos o ninguno, el caso va a "no se pudo relacionar" con el motivo.
- Lo que no matchea ninguna regla se cuenta como "no leído" y se guardan ejemplos.

**Control**: los m² de piezas reconstruidos ÷ (hojas × plancha útil) tienen que dar el % de la
leyenda (±0,5 por el redondeo a entero). Si no, el caso se informa aparte.

## Cobertura

Se completa cuando lleguen los casos (`datos/casos/`): `python -m optimizador historico` deja en
`salida/historico/cobertura.json` cuántas leyendas se leyeron, cuántas no y por qué, con ejemplos
de las que no se entendieron (y la página de revisión las lista). Con eso se agregan acá los
formatos nuevos que aparezcan, con 3 ejemplos de cada uno.

Con el caso de juguete (inventado) se leen todas las líneas del formato A, incluidas las variantes
con "_" y sin espacio antes de los asteriscos.
