# Contrato de datos: los casos históricos para validar

**Versión 1 — 21/10/2026.** Qué trae el zip de casos históricos, cómo se arma en la PC de Juan y
qué hace con él la sesión en la nube. Si alguno de los dos lados necesita cambiar algo, se cambia
primero acá y se sube la versión.

## Para qué

En Metrix hay muchísimos presupuestos en los que quedó anotado lo que dio Corte Certo (la
"leyenda": planchas, aprovechamiento…), junto con las piezas que se cotizaron. Son la mejor
prueba de que el optimizador da lo mismo o mejor. La nube no ve la base de Metrix, ni debe: los
datos viajan **en un zip, sin nombres de clientes**.

## Dónde va

- En el repo, en **`datos/casos/`**, con un commit, si pesa menos de 50 MB (GitHub avisa a los
  50 MB y rechaza archivos de más de 100 MB). Si pesa más, partirlo por año o usar Parquet.
- O adjunto en el mensaje a la sesión. En ese caso, la sesión lo guarda en `datos/casos/` y lo
  commitea, solo si pasó el control de privacidad.
- **Nunca** a git: lo que tenga nombres. Eso va a `datos/privado/`.

## Qué trae el zip: `casos_historicos_AAAA-MM-DD.zip`

Archivos CSV con separador `;`, UTF-8, punto decimal, fechas `AAAA-MM-DD` y medidas en mm
enteros. Opcional: un `casos.duckdb` con las mismas tablas (para consultar con SQL).

| Archivo | De dónde sale | Columnas |
|---|---|---|
| `LEEME.txt` | quien exporta | fecha y hora de la exportación, versión de este contrato, filtros usados, cantidades por archivo, en qué columna estaba la leyenda |
| `presupuestos.csv` | `PRESUP` | `numero`, `fecha` (de `TV_FEFAC`, fecha Clarion = días desde el 28/12/1800), `estado_pres`, `tipopresup`, `notas` (el texto donde está la leyenda, **limpio**, ver abajo) |
| `renglones.csv` | `DETPRES` + `ARTICULO` | `numero`, `orden` (posición del renglón, si existe), `v_codart`, `familia`, `art1`, `art2`, `art3`, `claseart1`, `claseart3`, `clase`, `largo`, `ancho`, `v_canti`, `v_cantialt`, `detalle` (limpio) |
| `piezas.csv` | `DETPRES2` | `numero`, `v_codart`, `clase`, `largo`, `ancho`, `v_canti` (m²), `v_cantialt` (piezas), `detalle` (limpio, si la columna existe) |
| `articulos.csv` | `ARTICULO` | `codigo`, `descripcion`, `familia`, `espesor`, `factor`, `clase`, `compuesto` (solo los artículos que aparecen en los renglones y piezas) |
| `familias.csv` | `FAMILIAS` | `familia`, `medidas`, `perimetro` |
| `control_privacidad.txt` | quien exporta | cuántos reemplazos hizo la limpieza, por tipo (sin mostrar los nombres) |
| `ESQUEMA.md` (opcional) | Juan | la descripción de la base que quiera sumar |

**Qué presupuestos entran**: todos los que tengan algo escrito en las notas, aunque no parezca una
leyenda. Así la nube ve todos los formatos y mide la cobertura. Cuantos más, mejor; sin límite de
fecha. La sesión filtra después.

**Recordatorios de `contexto/fabrica/DATA_DICTIONARY.md`**:
- En `DETPRES`, `V_CANTI` son **unidades** en DVH, herrajes, fletes y perforaciones, y **m²** en
  las líneas de vidrio con piezas en `DETPRES2`.
- En `DETPRES2`, `V_CANTI` ya son m² y `V_CANTIALT` son las piezas.
- En DVH, `ART1`/`ART3` son los dos vidrios y `ART2` la cámara.
- `PRESUP.NUMERO` y `PEDIDO1.TV_FACTU` comparten rango: acá siempre es **número de presupuesto**.

## Limpieza (privacidad): obligatoria antes de que salga de la PC

1. **No exportar**: código ni nombre de cliente, `OBRA`, `USUARIO`, CUIT, mails, teléfonos.
2. **En los textos** (`notas`, `detalle`):
   - reemplazar cualquier aparición de **cualquier** razón social o nombre de fantasía de la
     tabla `CLIENTES` por `<CLIENTE>`. No alcanza con el cliente del presupuesto: a veces se
     nombra a otro. Comparar sin tildes ni mayúsculas, solo nombres de 4 letras o más;
   - reemplazar el texto de la obra del presupuesto por `<OBRA>`;
   - mails → `<MAIL>`, CUIT → `<CUIT>`, teléfonos → `<TEL>`.
3. **Control final**:
   - volver a buscar todos los nombres de clientes en el resultado: tiene que dar 0;
   - anotar los conteos en `control_privacidad.txt`;
   - si algo no se pudo limpiar, ese presupuesto no se exporta (y se cuenta).

## Cómo se arma en la PC de Juan

Solo lectura, como todo en el proyecto de Metrix:
- con la conexión de solo lectura del proyecto (`negocio.conexion`, que bloquea cualquier cosa
  que no sea `SELECT`);
- o leyendo la copia local (Parquet o DuckDB), con `read_only=True` y
  `SET memory_limit='500MB'`.

Si es pesado, fuera del horario de planta. Consulta orientativa (la sesión local la adapta a los
nombres reales de las columnas):

```sql
-- notas de los presupuestos (después se limpian en Python)
SELECT NUMERO, TV_FEFAC, ESTADO_PRES, TIPOPRESUP, CODCLI, OBRA, TV_DESCRIP
FROM PRESUP;            -- filtrar en Python los que tienen texto en TV_DESCRIP

-- renglones de esos presupuestos
SELECT d.NUMERO, d.V_CODART, a.FAMILIA, d.ART1, d.ART2, d.ART3, d.CLASEART1, d.CLASEART3,
       d.CLASE, d.LARGO, d.ANCHO, d.V_CANTI, d.V_CANTIALT, d.DETALLE
FROM DETPRES d LEFT JOIN ARTICULO a ON a.CODIGO = d.V_CODART;

-- piezas
SELECT NUMERO, V_CODART, CLASE, LARGO, ANCHO, V_CANTI, V_CANTIALT
FROM DETPRES2;
```

**Primero hay que confirmar dónde está la leyenda.** Lo más probable es `PRESUP.TV_DESCRIP`, que
según el diccionario es donde se anotan cosas como las hojas a consumir. Pero puede estar en otra
columna de texto o en otra tabla. Mirar 20 presupuestos que Juan sepa que tienen la leyenda y
buscar el texto.

### Prompt para pedírselo a una sesión de Claude en la PC de Juan

Abrir Claude en la carpeta del proyecto de Metrix (`copia dir metrix`) y pegar, **junto con este
archivo entero**:

```text
Necesito armar el zip de casos históricos para el optimizador de corte (repo optimizador-corte).
Seguí al pie de la letra el contrato que te pego abajo (CONTRATO_DATOS.md, versión 1).
Reglas: solo SELECT contra Metrix con la conexión de solo lectura del proyecto, o leyendo la
copia local con read_only=True y memory_limit 500MB; nada de escribir en la base; nada de
nombres de clientes en el resultado (hacé la limpieza y el control del contrato).
Antes de exportar todo, mostrame: en qué columna está la leyenda, cuántos presupuestos tienen
algo escrito y 10 leyendas de ejemplo ya limpias. Si te digo que está bien, exportá todo, dejá
el zip en la carpeta que te indique y decime cuántos casos salieron y cuánto pesa.
```

O pedírselo a Claude en la conversación donde se armó este repo, con la PC prendida y la app de
escritorio abierta: desde ahí puede correrlo en la PC de Juan.

## Fuente B (mejor, si existe): los proyectos guardados en Corte Certo

El proyecto de la captura es el **413**: probablemente Corte Certo guarda los proyectos (piezas
y, quizás, el resultado). Si se pueden exportar, son casos **perfectos**: la entrada exacta que
vio Corte Certo, con su configuración y su resultado, sin depender de lo que alguien anotó.
Pregunta abierta para Juan: dónde guarda los datos Corte Certo, y si se pueden exportar a
CSV/TXT o copiar sus archivos. Si llegan, van como `datos/casos/corte_certo_proyectos/` con su
propio `LEEME.txt`.

## Qué hace la sesión en la nube cuando llegan

Es la fase F4 del brief:
1. Leer `LEEME.txt` y verificar que los archivos coincidan con este contrato. Si no coinciden,
   anotar las diferencias y adaptarse.
2. Encontrar los formatos de la leyenda → `docs/FORMATO_LEYENDAS.md`, con su cobertura.
3. Reconstruir las piezas por material y controlarlas contra los m² de la leyenda.
4. Calibrar (H0–H3) sobre el 70 % e informar sobre el 30 % → `docs/VALIDACION.md` + página de
   revisión.
