# Instalación en la PC de la oficina (Windows)

Para alguien que no programa. Se hace **una sola vez** (más o menos 15 minutos). No hace falta ser
administrador de la PC.

## Lo que hace falta

- Windows 10 u 11.
- **Internet solo la primera vez** (para bajar Python y las librerías). Después anda sin internet.
  Si la PC no tiene internet, ver "Sin internet" al final.
- Unos 600 MB libres de disco.

## Paso 1: instalar Python (una sola vez)

1. Entrá a **https://www.python.org/downloads/windows/**.
2. Bajá **Python 3.12** o **3.13**, "Windows installer (64-bit)". (Con 3.12 o más nuevo los
   resultados son los mismos que en la nube; con 3.10 o 3.11 también anda, pero algún caso puede
   dar distinto.)
3. Abrí el instalador. En la **primera pantalla**:
   - **destildá** "Use admin privileges when installing py.exe" (así no pide administrador);
   - **tildá** "Add python.exe to PATH";
   - apretá **"Install Now"** (se instala solo para tu usuario).
4. Al final, "Close".

Para comprobar: menú Inicio → escribí `cmd` → Enter → en la ventana negra escribí `py --version`
(o `python --version`) → Enter. Tiene que decir "Python 3.12…" o "3.13…".

## Paso 2: copiar el programa

1. En GitHub, en el repo **optimizador-corte**, botón verde **Code** → **Download ZIP**.
2. Descomprimilo en una carpeta fija, por ejemplo `C:\Optimizador`. (Puede tener espacios en el
   nombre; mejor que no esté en el Escritorio ni en Descargas, para no borrarla sin querer.)
3. Adentro tiene que estar el archivo **`Abrir_Optimizador.bat`**.

## Paso 3: abrirlo

1. Doble clic en **`Abrir_Optimizador.bat`**.
2. **La primera vez** dice "Primera vez: preparando el programa…" y tarda unos minutos (baja e
   instala las librerías en la carpeta `.venv`, adentro de la carpeta del programa).
3. Cuando termina, se abre solo el navegador en **http://127.0.0.1:8520** con el optimizador.
   (Si el 8520 está ocupado usa el siguiente libre, 8521, etc.; la ventana negra dice cuál.)
4. **La ventana negra tiene que quedar abierta** mientras se usa. Cerrarla apaga el programa.

Las veces siguientes es solo el doble clic (tarda unos segundos).

Tip: clic derecho en `Abrir_Optimizador.bat` → "Enviar a" → "Escritorio (crear acceso directo)".

## Probar que anda bien en esta PC (opcional)

En la carpeta del programa: clic en la barra de direcciones del Explorador, escribí `cmd` y Enter.
En la ventana negra:

```text
.venv\Scripts\python.exe -m optimizador banco --esfuerzo rapido
```

Corre los 85 casos de prueba y al final muestra un resumen con los tiempos de esta PC. Si algún caso
"EMPEORÓ" respecto de la nube, avisar. Para la prueba completa (más lenta), sin `--esfuerzo rapido`.

## Actualizar el programa

Cuando haya una versión nueva:

1. Bajá el ZIP nuevo y descomprimilo **en otra carpeta**.
2. Copiá de la carpeta vieja a la nueva, si existen:
   - `config\local\` (los cambios de materiales que hicieron en esta PC);
   - `proyectos\` (los proyectos guardados).
3. Usá el `Abrir_Optimizador.bat` de la carpeta nueva (la primera vez vuelve a instalar las
   librerías si cambiaron).

## Si algo falla

| Qué pasa | Qué hacer |
|---|---|
| "No se encontró Python" | Volver al paso 1 (asegurarse de tildar "Add python.exe to PATH"). Cerrar y abrir de nuevo. |
| "Falló la instalación" la primera vez | Revisar que haya internet y volver a hacer doble clic. Si no hay internet, ver abajo. |
| El navegador no se abre | Abrirlo a mano y entrar a la dirección que muestra la ventana negra (`http://127.0.0.1:8520/`). |
| La página dice "No se pudo conectar con el programa" | La ventana negra se cerró: doble clic otra vez en `Abrir_Optimizador.bat`. |
| Algo raro con las librerías | Borrar la carpeta `.venv` (adentro de la carpeta del programa) y hacer doble clic: se reinstala. |

## Sin internet

En una PC **con** internet y el mismo Python (por ejemplo 3.12), en una ventana negra:

```text
py -3.12 -m pip download -r requirements.txt --only-binary=:all: --platform win_amd64 --python-version 3.12 -d paquetes
```

Eso crea una carpeta `paquetes` (unos 60 MB). Copiala adentro de la carpeta del programa en la PC
sin internet: `Abrir_Optimizador.bat` la usa sola (instala desde ahí, sin conectarse). El instalador
de Python también se puede llevar en un pendrive.

## Qué guarda y dónde

Todo queda adentro de la carpeta del programa:

| Carpeta | Qué |
|---|---|
| `.venv\` | Python y las librerías del optimizador (no es el `_work\venv` de Metrix) |
| `config\local\` | Cambios de materiales hechos en esta PC |
| `proyectos\` | Proyectos guardados con "Guardar" |
| `salida\` | Resultados de la validación histórica |

No se conecta a Metrix, ni a SQL Server, ni a internet mientras corre.
