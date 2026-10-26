# Prueba en la PC de la oficina (25/10/2026, noche)

Primera vez que el optimizador se instala y se corre en una PC de la oficina (hasta ahora todo se
había medido en la nube). Lo hizo una sesión de Claude Code en la PC de Juan, siguiendo
`docs/INSTALACION.md` con un `.venv` propio dentro de la carpeta del repo.

**En una línea**: anda todo, da **exactamente los mismos resultados que la nube** en los 85 casos
del banco y esta PC es **un 10 % más rápida** que la nube. Lo único que falló es una falsa alarma
del banco con `--esfuerzo rapido` (ver §4).

## 1. La PC

| | |
|---|---|
| Procesador | Intel Pentium Gold G6405 @ 4,1 GHz (2 núcleos, 4 hilos) |
| RAM | 3,9 GB en total; **entre 400 y 900 MB libres** durante la prueba |
| Sistema | Windows 11 Pro |
| Python | **3.14.6** (el único instalado; no está el lanzador `py`, se usa `python`) |
| Carpeta | `C:\Users\geronimo.zanon\optimizador-corte-git` (clon de `main`, commit `7454999`) |

Durante la prueba los servicios de Metrix estaban apagados (domingo a la noche) y había varias
sesiones de Claude Code abiertas, que eran lo que más memoria ocupaba. En un día de semana el ciclo
de Metrix corre cada 15 minutos en esta misma PC: los tiempos pueden subir algo y la RAM libre
bajar.

Ojo: ya existía una carpeta `C:\Users\geronimo.zanon\optimizador-corte` con la especificación del
21/10 (sin `.git`, sin código). No se tocó; el clon quedó al lado, con `-git` al final.

## 2. Instalación

| Paso | Resultado | Tiempo |
|---|---|---|
| `python -m venv .venv` | OK | 7,6 s |
| `.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` | OK: todo vino como paquete listo para Windows y Python 3.14 (numpy 2.5.4, scipy 1.18.1, pydantic-core 2.50.1, etc.), **no compiló nada** | 52 s |

`requirements-dev.txt` es `requirements.txt` + pytest e hypothesis. Se copió `requirements.txt` a
`.venv\requirements_instalados.txt`, como hace el `.bat`, para que `Abrir_Optimizador.bat` no
reinstale la primera vez.

`docs/INSTALACION.md` recomienda Python 3.12 o 3.13; con **3.14 también anda** y los resultados son
idénticos a la nube (que usa 3.13).

## 3. Tests: `pytest -q`

| Corrida | Resultado | Tiempo | Pico de RAM |
|---|---|---|---|
| 1ª | **123 pasaron**, 0 fallaron | 60,5 s | (no se midió bien) |
| 2ª (`-rA --durations=8`) | **123 pasaron**, 0 fallaron | 45,0 s | 155 MB |

Los más lentos: preparar `test_casos_reales` (16 s, lee los 1341 casos exportados),
`test_muchisimas_medidas_en_maximo_no_hace_columnas` (10 s) y
`test_caso_grande_que_ponia_piezas_de_mas` (6 s). La 1ª corrida tarda más porque Python todavía
no tenía nada compilado (`__pycache__`).

## 4. Banco sintético: `python -m optimizador banco`

### 4.1 Esfuerzo normal (el del comando tal cual)

- **85 de 85 pasaron el validador**, **ninguno "EMPEORÓ"**, código de salida 0.
- **Resultados idénticos a la nube** caso por caso: mismas planchas, mismos montajes y mismo
  aprovechamiento en los 85 (comparado contra `tests/banco/esperado.json`).
- Corte perfecto hasta 100 piezas: 30 de 60 en el óptimo (20 de 36 en 3 etapas), igual que la nube.
- Tiempo total **269,5 s** (nube: 297,5 s). Caso más lento **8,55 s** (nube: 9,57 s).
- Caso por caso (los que tardan más de medio segundo, 53 casos), esta PC tarda en promedio
  **0,90 veces** lo de la nube (entre 0,78 y 1,13).
- Pico de RAM: **105 MB**. RAM libre mínima de la PC durante la corrida: 649 MB.

| Familia | Casos | Esta PC: total / más lento | Nube: total / más lento |
|---|---|---|---|
| Corte perfecto, 3 etapas (CP3) | 36 | 91,3 s / 8,32 s | 98,8 s / 9,57 s |
| Corte perfecto, guillotina libre (CPL) | 36 | 156,7 s / 8,55 s | 174,9 s / 9,52 s |
| Realistas (RE) | 10 | 20,7 s / 7,11 s | 22,7 s / 7,92 s |
| Tipo 413 (T413) | 3 | 0,9 s / 0,36 s | 1,0 s / 0,38 s |

Los realistas, que son lo más parecido a un presupuesto:

| Caso | Piezas | Planchas | Esta PC | Nube | Esfuerzo rápido (planchas) |
|---|---|---|---|---|---|
| RE-2000 | 20 | 2 | 0,04 s | 0,06 s | 0,02 s (2) |
| RE-2001 | 50 | 6 | 0,19 s | 0,23 s | 0,14 s (6) |
| RE-2002 | 80 | 6 | 0,38 s | 0,40 s | 0,23 s (6) |
| RE-2003 | 120 | 21 | 1,71 s | 1,84 s | 0,37 s (21) |
| RE-2004 | 300 | 46 | 5,26 s | 5,33 s | 0,94 s (46) |
| RE-2005 | 300 | 13 | 7,11 s | 7,92 s | 1,49 s (13) |
| RE-2006 | 40 | 9 | 0,13 s | 0,20 s | 0,05 s (9) |
| RE-2007 | 200 | 25 | 3,34 s | 3,89 s | 0,70 s (25) |
| RE-2008 | 60 | 3 | 0,20 s | 0,26 s | 0,14 s (3) |
| RE-2009 | 250 | 50 | 2,30 s | 2,57 s | 0,73 s (**51**) |
| T413-3000 | 252 | 73 | 0,27 s | 0,30 s | 0,13 s (73) |
| T413-3001 | 252 | 73 | 0,31 s | 0,32 s | 0,14 s (73) |
| T413-3002 | 252 | 73 | 0,36 s | 0,38 s | 0,16 s (73) |

Con esto, las metas de tiempo del brief para el caso típico (≤ 10 s con esfuerzo normal) se cumplen
también en esta PC, con margen.

### 4.2 Esfuerzo rápido (`--esfuerzo rapido`, el que sugiere `INSTALACION.md`)

- 85 de 85 pasaron el validador. Total **60,3 s**, el más lento 3,97 s, pico de RAM 55 MB.
- Corte perfecto hasta 100 piezas: 18 de 60 en el óptimo (con normal, 30).
- **Dice "EMPEORÓ" en 13 casos y termina con código de salida 1** (12 de corte perfecto y RE-2009,
  todos con 1 plancha de más).

**Esto no es un problema de la PC: es una falsa alarma.** `comparar_con_esperado`
(`optimizador/banco.py`, línea 272) compara siempre contra `tests/banco/esperado.json`, que se
guardó con esfuerzo **normal**, sin mirar con qué esfuerzo se corrió. Con menos esfuerzo es esperable
que algunos casos den una plancha más. Pero `INSTALACION.md` ("Probar que anda bien en esta PC")
dice que con `--esfuerzo rapido`, "si algún caso EMPEORÓ respecto de la nube, avisar": quien lo
siga al pie de la letra va a ver 13 avisos y va a pensar que algo anda mal.

Arreglos posibles (no se hizo ninguno; elegir uno):
1. Que el banco compare solo cuando el esfuerzo coincide con el de `esperado.json` (y si no, que lo
   diga en vez de avisar "EMPEORÓ").
2. Guardar un `esperado_rapido.json` y comparar contra ese.
3. Como mínimo, cambiar `INSTALACION.md` para que la prueba recomendada sea el banco normal (tarda
   unos 4 minutos y medio en esta PC).

## 5. La interfaz (servidor)

No se usó `Abrir_Optimizador.bat`, porque abre el navegador y en esta PC conviene no gastar esa RAM
de más. Se probó lo mismo que hace el `.bat` por dentro:

- `python -m optimizador servidor --no-abrir` levantó en **127.0.0.1:8520** (estaba libre; los
  servicios de Metrix en 8080/8501/8502 estaban apagados).
- `/` (la página) responde bien; `/api/estado` y `/api/materiales` también.
- Cálculo de `ejemplos/proyecto_ejemplo.json` por `/api/calcular`: terminó "listo" en
  aproximadamente 1 s, **completo, validado** y sin avisos (FL5IN 81,79 %, LX4+4IN 67,25 %).
- Se bajaron bien el informe HTML (83 KB), el consumo en CSV y en XLSX.
- El servidor ocupaba **107 MB** después del cálculo. Se apagó y el puerto quedó libre.

## 6. Qué no se probó

- **El doble clic en `Abrir_Optimizador.bat`** (la instalación se hizo a mano con los mismos
  comandos). Con `.venv` ya creado y `requirements_instalados.txt` copiado, el `.bat` debería
  arrancar directo. Probarlo de día con el navegador.
- **Con el ciclo de Metrix corriendo**: los tiempos y la RAM son de un domingo con los servicios
  apagados.
- Los casos grandes de `VALIDACION.md` §2.4 (2000 piezas, ~310 MB): no se corrieron, para no
  apretar la RAM de esta PC.
- Esfuerzo máximo, la validación histórica (`python -m optimizador historico --todo`) y
  `herramientas/prueba_estres.py`.
- Una planilla `.xls` real de la Interfaz (sigue pendiente, como dice `ESTADO.md`).

## 7. Para repetir esta prueba

En una ventana negra, en la carpeta del repo:

```text
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m optimizador banco --salida salida\banco_pc.json
```

El JSON de `--salida` trae el tiempo de cada caso. Para compararlo con la nube, usá el de
`tests/banco/esperado.json`. **No uses `--guardar`**: pisa los resultados esperados.
