# Registro Quirúrgico Coloproctología - HUMS

## Descripción
App web para registro quirúrgico de la Unidad de Cirugía Coloproctología del 
Hospital Universitario Miguel Servet (HUMS) de Zaragoza.

## Stack técnico
- Backend: Python + FastAPI
- Base de datos: SQLite
- Frontend: HTML + Tailwind CSS + Chart.js + JavaScript vanilla
- Autenticación: JWT con bcrypt (sin passlib)
- Despliegue: **offline** (ejecutable Windows) — ver `LEEME_OFFLINE.md`

## Modo de despliegue

Por protección de datos la aplicación se ha retirado de internet y funciona
**offline** en equipos del hospital:

- `launcher.py` arranca uvicorn en 127.0.0.1 y abre Chrome (o Edge) con
  `--app=` para que no se vea la barra de direcciones
- Empaquetado con PyInstaller (`coloproctologia.spec`, `build_exe.bat`)
- La BD vive junto al ejecutable; el lanzador fija `DB_PATH` antes de importar
- Alojado en un buzón compartido, con **bloqueo de instancia única**: sólo una
  persona puede tenerla abierta a la vez

**Por qué el bloqueo:** SQLite no garantiza los bloqueos de fichero sobre SMB.
Dos equipos escribiendo a la vez pueden corromper la BD sin error visible. El
bloqueo es por rango de bytes, así que el SO lo libera solo si el proceso muere
(verificado: matar el proceso de golpe no deja bloqueo fantasma).

El código de Railway se conserva y sigue funcionando si algún día se reactiva.

## URLs
- Producción: https://web-production-c69f0.up.railway.app
- GitHub: https://github.com/cgroche82/coloproctologia-app

## Credenciales por defecto
- Admin: admin / coloproct2024

## Estructura
- launcher.py — lanzador offline (bloqueo, servidor local, Chrome/Edge modo app)
- coloproctologia.spec / build_exe.bat — empaquetado PyInstaller
- LEEME_OFFLINE.md — guía de instalación para el hospital
- main.py — FastAPI app principal
- database.py — SQLAlchemy, 4 tablas separadas por tipo de cirugía + recreate_engine()
- auth.py — JWT + bcrypt (SIN passlib, usa import bcrypt directamente)
- schemas.py — Pydantic models
- routers/colorrectal.py — CRUD Cirugía Colorrectal
- routers/proctologia.py — CRUD Proctología
- routers/funcionales.py — CRUD Trastornos Funcionales
- routers/general.py — CRUD Cirugía General
- routers/stats.py — Estadísticas y KPIs dashboard
- routers/export.py — Exportación CSV y Excel + backup/restaurar/importar CSV
- templates/index.html — SPA completa
- static/js/app.js — Lógica frontend
- static/logo_hums.jpg — Logo Hospital Miguel Servet

## 4 tipos de cirugía con tablas separadas
1. Cirugía Colorrectal (cirugia_colorrectal) — incluye campos oncológicos y seguimiento
2. Proctología (proctologia)
3. Trastornos Funcionales (trastornos_funcionales)
4. Cirugía General (cirugia_general)

## Funcionalidades implementadas
- Formulario wizard 4 pasos con 4 tipos de cirugía
- Base de datos con búsqueda, filtros y paginación
- Dashboard global y por tipo con gráficos (Chart.js)
- Exportación CSV y Excel con columnas ordenadas
- Autenticación JWT con panel de gestión de usuarios
- **Backup completo** de la BD (.db) — solo admin (`GET /api/export/backup`)
- **Restaurar backup** (.db) con validación SQLite y confirmación — solo admin (`POST /api/export/restore`)
- **Importar CSV** sin borrar registros existentes, detección automática de tipo de cirugía — solo admin (`POST /api/export/import-csv`)
- Logo HUMS y texto "Unidad de Cirugía Coloproctología" en pantalla de login
- **Cambiar propia contraseña** — botón de llave en topbar, requiere contraseña actual (`POST /api/auth/change-password`)
- **Admin cambia contraseña de cualquier usuario** — botón en tabla de usuarios (`PATCH /api/admin/usuarios/{uid}/password`)
- **Recuperación por código temporal** — enlace "¿Olvidaste tu contraseña?" en login; genera código de 6 dígitos de un solo uso válido 30 min, visible solo en logs de Railway (`POST /api/auth/recovery-code` + `POST /api/auth/reset-password`)

## Configuración Railway
- Volumen: /data (1GB) — mountPath="/data" en railway.toml
- Región: europe-west4 (Países Bajos)
- Variable de entorno: SECRET_KEY=coloproctologia_hums_2024

## Notas importantes
- auth.py usa bcrypt directamente (import bcrypt), NO passlib
- Las rutas de los routers usan "" en lugar de "/" para evitar error 405
- Python 3.11 (no 3.14 — incompatible con pydantic-core)
- El archivo .python-version contiene "3.11.9"
- DB en /data/coloproctologia.db (volumen Railway en /data). Si se cambia mountPath hay que actualizar también database.py
- Los códigos de recuperación de contraseña son efímeros (solo en memoria RAM); se pierden al reiniciar el servidor
- Bug edición corregido: clearForm() reseteaba editMode → ahora se llama antes de asignar editMode/editId/editTipo
- NO activar modo WAL en SQLite: no funciona sobre unidades de red (requiere memoria compartida)
- El navegador se lanza con `--user-data-dir` en disco local para forzar un proceso propio al que esperar (si no, Chrome delega en una instancia existente y sale al instante)
- `.gitignore` bloquea `*.db`: la base de datos con datos de pacientes nunca debe subirse al repositorio
