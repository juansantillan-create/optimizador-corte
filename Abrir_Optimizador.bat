@echo off
rem Optimizador de corte - Cristalux. Doble clic para abrirlo.
rem La primera vez prepara el programa (crea la carpeta .venv e instala lo necesario).
rem Cerrar esta ventana apaga el programa.
chcp 65001 >nul
title Optimizador de corte - Cristalux
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
rem Un .venv roto (sin pip o sin Python que ande) se vuelve a crear.
if exist "%PY%" (
  "%PY%" -m pip --version >nul 2>nul
  if errorlevel 1 (
    echo La carpeta .venv esta rota: se vuelve a crear.
    rmdir /s /q .venv
  )
)
if exist "%PY%" goto :revisar

echo.
echo Primera vez: preparando el programa. Puede tardar unos minutos...
set "BASE="
where py >nul 2>nul
if %errorlevel%==0 (
  set "BASE=py -3"
) else (
  where python >nul 2>nul
  if not errorlevel 1 set "BASE=python"
)
if not defined BASE goto :sinpython
rem Hace falta Python 3.10 o mas nuevo.
%BASE% -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 (
  echo.
  echo El Python de esta PC es muy viejo: hace falta 3.10 o mas nuevo ^(mejor 3.12 o 3.13^).
  echo Instalalo desde python.org y volve a hacer doble clic. Ver docs\INSTALACION.md
  pause
  exit /b 1
)
%BASE% -m venv .venv
if not exist "%PY%" goto :sinpython

:revisar
rem Si cambio requirements.txt (o es la primera vez), se instalan las dependencias.
fc /b requirements.txt .venv\requirements_instalados.txt >nul 2>nul
if %errorlevel%==0 goto :abrir
echo Instalando lo necesario...
if exist "paquetes\" (
  "%PY%" -m pip install --disable-pip-version-check --no-index --find-links paquetes -r requirements.txt
) else (
  "%PY%" -m pip install --disable-pip-version-check -r requirements.txt
)
if errorlevel 1 goto :fallo
copy /y requirements.txt .venv\requirements_instalados.txt >nul
goto :abrir

:fallo
echo.
if exist "paquetes\" (
  echo Fallo la instalacion desde la carpeta "paquetes": puede ser de otra version de Python.
  echo Hay que bajarla de nuevo con el mismo Python de esta PC ^(ver docs\INSTALACION.md^).
) else (
  echo Fallo la instalacion. Si la PC no tiene internet, copia la carpeta "paquetes"
  echo ^(ver docs\INSTALACION.md^) y volve a intentar.
)
if exist ".venv\requirements_instalados.txt" (
  echo.
  echo Se abre igual con las librerias que ya estaban instaladas.
  pause
  goto :abrir
)
pause
exit /b 1

:sinpython
echo.
echo No se encontro Python. Instalalo desde python.org ^(version 3.12 o 3.13,
echo opcion "Install for me only"^) y volve a hacer doble clic. Ver docs\INSTALACION.md
pause
exit /b 1

:abrir
echo.
"%PY%" -m optimizador servidor
echo.
echo El programa se cerro.
pause
