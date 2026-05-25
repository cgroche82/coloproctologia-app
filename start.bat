@echo off
echo ============================================
echo   Registro Quirurgico Coloproctologia
echo ============================================
echo.

REM Check if venv exists, create if not
if not exist "venv\" (
    echo Creando entorno virtual...
    python -m venv venv
    echo.
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt --quiet

echo.
echo Iniciando servidor en http://localhost:8000
echo Pulsa Ctrl+C para detener
echo.
set DB_PATH=./data/coloproctologia.db
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause
