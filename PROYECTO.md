# Registro Quirúrgico Coloproctología - HUMS

## Descripción
App web para registro quirúrgico de la Unidad de Cirugía Coloproctología del 
Hospital Universitario Miguel Servet (HUMS) de Zaragoza.

## Stack técnico
- Backend: Python + FastAPI
- Base de datos: SQLite en /data/coloproctologia.db (volumen persistente Railway)
- Frontend: HTML + Tailwind CSS + Chart.js + JavaScript vanilla
- Autenticación: JWT con bcrypt (sin passlib)
- Despliegue: Railway (plan Hobby $5/mes)

## URLs
- Producción: https://web-production-c69f0.up.railway.app
- GitHub: https://github.com/cgroche82/coloproctologia-app

## Credenciales por defecto
- Admin: admin / coloproct2024

## Estructura
- main.py — FastAPI app principal
- database.py — SQLAlchemy, 4 tablas separadas por tipo de cirugía
- auth.py — JWT + bcrypt (SIN passlib, usa import bcrypt directamente)
- schemas.py — Pydantic models
- routers/colorrectal.py — CRUD Cirugía Colorrectal
- routers/proctologia.py — CRUD Proctología
- routers/funcionales.py — CRUD Trastornos Funcionales
- routers/general.py — CRUD Cirugía General
- routers/stats.py — Estadísticas y KPIs dashboard
- routers/export.py — Exportación CSV y Excel
- templates/index.html — SPA completa
- static/js/app.js — Lógica frontend
- static/logo_hums.jpg — Logo Hospital Miguel Servet

## 4 tipos de cirugía con tablas separadas
1. Cirugía Colorrectal (cirugia_colorrectal) — incluye campos oncológicos y seguimiento
2. Proctología (proctologia)
3. Trastornos Funcionales (trastornos_funcionales)
4. Cirugía General (cirugia_general)

## Bugs conocidos / pendientes de arreglar
- Dashboard Global da Internal Server Error
- Exportación Excel con columnas desordenadas (campos específicos antes que comunes)
- Dashboard Colorrectal necesita más métricas (ver lista en conversación)
- Dashboard Proctología/Funcionales/General necesita métricas básicas
- Paso 4 formulario Proctología/Funcionales/General: eliminar sección oncológica

## Configuración Railway
- Volumen: /data (1GB)
- Región: europe-west4 (Países Bajos)
- Variable de entorno: SECRET_KEY=coloproctologia_hums_2024

## Notas importantes
- auth.py usa bcrypt directamente (import bcrypt), NO passlib
- Las rutas de los routers usan "" en lugar de "/" para evitar error 405
- Python 3.11 (no 3.14 — incompatible con pydantic-core)
- El archivo .python-version contiene "3.11.9"
