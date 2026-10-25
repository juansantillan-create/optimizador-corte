# Datos para validar

| Carpeta | Qué va | ¿Va a git? |
|---|---|---|
| `casos/` | El zip (o la carpeta) de casos históricos, **sin nombres de clientes**, según `docs/CONTRATO_DATOS.md` | Sí |
| `privado/` | Cualquier cosa que tenga nombres de clientes (para trabajar local en la PC de Juan) | **No** (está en `.gitignore`) |

Si `casos/` está vacío, la sesión en la nube arma todo igual con datos sintéticos. La validación
histórica (fase F4) queda lista para correr cuando lleguen los datos.
