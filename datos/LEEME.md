# Datos para validar

| Carpeta | Qué va | ¿Va a git? |
|---|---|---|
| `casos/` | El zip (o la carpeta) de casos históricos, **sin nombres de clientes**, según `docs/CONTRATO_DATOS.md` | Sí |
| `privado/` | Cualquier cosa que tenga nombres de clientes (para trabajar local en la PC de Juan) | **No** (está en `.gitignore`) |

Lo que hay en `casos/` (llegó el 25/10/2026, sin nombres de clientes; cada carpeta tiene su
`LEEME.txt`):

| Carpeta | Qué es |
|---|---|
| `casos/corte_certo/` | 1341 casos de presupuestos de Metrix (2024-05 a 2026-10): las piezas y lo que dio Corte Certo (hojas y %). Sin separación ni destaque, como se cotiza |
| `casos/optima/` | 5 lotes cortados de verdad con Optima: las piezas, las hojas que se usaron y el desperdicio. Optima sí usa el destaque mínimo de la regla de Lucas |

Cómo se usan: `python -m optimizador historico` (ver `docs/VALIDACION.md` §1).
