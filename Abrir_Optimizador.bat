@echo off
rem Optimizador de corte - Cristalux. Doble clic para abrirlo.
rem La primera vez prepara el programa (crea la carpeta .venv e instala lo necesario).
rem Cerrar esta ventana apaga el programa.
chcp 65001 >nul
title Optimizador de corte - Cristalux
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if exist "%PY%" goto :revisar

echo.
echo Primera vez: preparando el programa. Puede tardar unos minutos...
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m venv .venv
) else (
  python -m venv .venv
)
if not exist "%PY%" (
  echo.
  echo No se encontro Python. Instalalo desde python.org ^(version 3.12 o 3.13,
  echo opcion "Install for me only"^) y volve a hacer doble clic. Ver docs\INSTALACION.md
  pause
  exit /b 1
)

:revisar
rem Si cambio requirements.txt (o es la primera vez), se instalan las dependencias.
fc /b requirements.txt .venv\requirements_instalados.txt >nul 2>nul
if %errorlevel%==0 goto :abrir
echo Instalando lo necesario...
if exist "paquetes\" (
  "%PY%" -m pip install --no-index --find-links paquetes -r requirements.txt
) else (
  "%PY%" -m pip install --disable-pip-version-check -r requirements.txt
)
if errorlevel 1 (
  echo.
  echo Fallo la instalacion. Si la PC no tiene internet, copia la carpeta "paquetes"
  echo ^(ver docs\INSTALACION.md^) y volve a intentar.
  pause
  exit /b 1
)
copy /y requirements.txt .venv\requirements_instalados.txt >nul

:abrir
echo.
"%PY%" -m optimizador servidor
echo.
echo El programa se cerro.
pause
