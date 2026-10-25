"""Validación contra los presupuestos viejos (fase F4 del brief, §10).

- `datos`: lee el zip (o la carpeta) de casos según `docs/CONTRATO_DATOS.md`.
- `leyendas`: encuentra y lee la "leyenda" con lo que dio Corte Certo.
- `reconstruir`: arma las piezas de cada presupuesto por material (DVH = 2 vidrios; nada de
  herrajes, fletes, perforaciones ni cámaras).
- `comparar`: relaciona cada material de la leyenda con su código de Metrix, controla la entrada,
  corre las hipótesis H0–H2, calibra con el 70 % de los casos e informa sobre el 30 % restante.
- `revision`: la página HTML para que Juan revise caso por caso.

Se corre con `python -m optimizador historico` (ver `docs/VALIDACION.md`).
"""
