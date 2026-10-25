@echo off
rem Baja las librerias del optimizador a la carpeta "paquetes", para instalar en una PC SIN
rem internet. Correrlo en una PC CON internet y con el mismo Python que la PC de destino.
rem Despues copiar la carpeta "paquetes" adentro de la carpeta del programa en la otra PC.
chcp 65001 >nul
cd /d "%~dp0\.."
where py >nul 2>nul
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")
for /f "tokens=2 delims= " %%v in ('%PY% --version') do set "VER=%%v"
for /f "tokens=1,2 delims=." %%a in ("%VER%") do set "PYV=%%a.%%b"
echo Bajando paquetes para Python %PYV% (Windows 64 bits) en la carpeta "paquetes"...
%PY% -m pip download -r requirements.txt --only-binary=:all: --platform win_amd64 --python-version %PYV% -d paquetes
if errorlevel 1 (
  echo Fallo la descarga. Revisar la conexion a internet.
) else (
  echo Listo. Copia la carpeta "paquetes" a la PC sin internet, adentro de la carpeta del programa.
)
pause
