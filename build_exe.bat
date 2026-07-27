@echo off
REM ============================================================
REM  Compilar Registro Quirurgico Coloproctologia (HUMS)
REM  Genera dist\RegistroColoproctologia\
REM ============================================================

cd /d "%~dp0"

REM Usar el entorno virtual del proyecto si existe
if exist "venv\Scripts\python.exe" (
    set PY=venv\Scripts\python.exe
    echo Usando el entorno virtual del proyecto.
) else (
    set PY=python
    echo No hay venv; usando el Python del sistema.
)

echo.
echo === Instalando dependencias ===
%PY% -m pip install --quiet --upgrade pip
%PY% -m pip install --quiet -r requirements.txt
if errorlevel 1 goto error
%PY% -m pip install --quiet -r requirements-build.txt
if errorlevel 1 goto error

echo.
echo === Limpiando compilacion anterior ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo === Compilando (puede tardar 1-3 minutos) ===
%PY% -m PyInstaller coloproctologia.spec --noconfirm
if errorlevel 1 goto error

echo.
echo ============================================================
echo  LISTO
echo.
echo  Carpeta generada:  dist\RegistroColoproctologia\
echo  Ejecutable:        RegistroColoproctologia.exe
echo.
echo  Copia la carpeta COMPLETA al buzon compartido.
echo  La base de datos se creara dentro al primer arranque.
echo ============================================================
echo.
pause
exit /b 0

:error
echo.
echo *** ERROR durante la compilacion ***
echo.
pause
exit /b 1
