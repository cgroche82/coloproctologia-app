"""
Servidor de desarrollo.

Levanta la aplicación con recarga automática y una base de datos aparte
(dev_coloproctologia.db, en la raíz del proyecto e ignorada por git), para no
tocar nunca la base real de la carpeta compilada.

    python dev_server.py
"""

import os

# Debe fijarse ANTES de importar la aplicación: database.py lee DB_PATH al cargarse
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("DB_PATH", os.path.join(BASE_DIR, "dev_coloproctologia.db"))

if __name__ == "__main__":
    import uvicorn

    print(f"Base de datos de desarrollo: {os.environ['DB_PATH']}")
    uvicorn.run("main:app", host="127.0.0.1", port=8010, reload=True)
