# CONTEXTO DEL PROYECTO

> Documento de continuidad: si se reinicia el chat, **leer esto primero**.
> Recoge el estado, las decisiones tomadas y sus porqués.
> Última actualización: 28/07/2026.

---

## 1. Qué es

Registro quirúrgico de la Unidad de Coloproctología del Hospital Universitario
Miguel Servet (HUMS), Zaragoza.

- **Repositorio:** https://github.com/cgroche82/coloproctologia-app
- **Credenciales iniciales:** `admin` / `coloproct2024`
- **Stack:** Python 3.11 + FastAPI + SQLite + HTML/Tailwind/Chart.js/JS vanilla
- **Autenticación:** JWT + bcrypt (`import bcrypt` directo, **NO** passlib)

## 2. Cómo se ejecuta

| Para qué | Comando |
|---|---|
| Desarrollo (recarga automática, BD aparte) | `venv/Scripts/python.exe dev_server.py` → puerto 8010 |
| Compilar el ejecutable | `build_exe.bat` → `dist/RegistroColoproctologia/` |
| Carpeta lista para el hospital | `APP - Registro Coloproctologia HUMS/` (ignorada por git) |

`dev_server.py` usa `dev_coloproctologia.db`, nunca la base del hospital.

---

## 3. Decisión de fondo: la app es OFFLINE

Se retiró de Railway por protección de datos. Ahora es un ejecutable Windows:
`launcher.py` levanta uvicorn en `127.0.0.1` y abre Chrome (o Edge) con `--app=`
para que no se vea la barra de direcciones.

**Se aloja en un buzón compartido con bloqueo de un usuario a la vez.** Motivo:
SQLite no garantiza los bloqueos de fichero sobre SMB y dos equipos escribiendo
a la vez pueden corromper la base **sin dar ningún error**. Se prefirió impedir
la concurrencia a asumir ese riesgo.

### Trampas ya resueltas (no reintroducirlas)

- **No activar WAL** en SQLite: necesita memoria compartida, no funciona en red.
- **`--user-data-dir` es obligatorio** al lanzar el navegador. Sin él Chrome
  delega en una ventana ya abierta y sale al instante, dejando el servidor
  huérfano. Hay un diálogo modal de respaldo por si aun así ocurriera.
- **`log_config=None` en uvicorn**: su formateador llama a `isatty()` sobre
  stdout, que no existe en un `.exe` sin consola y hace petar el arranque.
- **Ficheros de bloqueo ocultos**: Windows impide sobrescribir un fichero
  oculto con modo `"w"`, así que `_write_owner` lo borra antes de recrearlo.
  El bloqueo se abre en `"a+"`, que sí lo admite.
- **onedir, no onefile**: desde unidad de red onefile descomprime ~50 MB en
  cada arranque (10-15 s de espera cada vez).
- **`app.js` se sirve con `?v=<mtime>`**: sin eso el navegador cachea una
  interfaz antigua contra un backend nuevo. Pasó durante el desarrollo.

### Pendiente con Informática del hospital

Firma digital del `.exe` (SmartScreen), excepción de antivirus (PyInstaller da
falsos positivos) y directivas AppLocker, que suelen prohibir ejecutables en
unidades de red. **Este último puede tumbar el plan entero: probarlo pronto.**

---

## 4. Arquitectura de datos

### Tabla única (no cuatro)

Antes había 4 tablas por tipo de cirugía. Ahora hay **una sola tabla
`registros` con campo `tipo_id`**, para que crear un grupo sea insertar una
fila y no modificar el esquema.

`migracion_tabla_unica.py` traspasa las tablas antiguas al arrancar. Es
idempotente y **no las borra**: quedan como red de seguridad.

### Los 7 grupos

Son los mismos que la app de Lista de Espera, para poder importar su Excel sin
traducir nada:

`Neoplasias` (oncológico) · `Colon Benigno` · `EII` · `Reconstrucciones` ·
`Proctología` · `Cirugía General` · `Neuromodulación`

Se crean, renombran y eliminan desde **Ajustes**. Cada uno lleva una casilla
**"tiene seguimiento oncológico"** que activa el bloque TNM en el formulario,
sus gráficas y sus columnas al exportar.

### Catálogos editables

`tipos_cirugia`, `diagnosticos`, `intervenciones`, `cirujanos`. Se siembran
desde `seed_catalogos.py` (idempotente, no pisa lo editado).

**Clave para entenderlo todo:** los registros guardan diagnóstico, intervención
y cirujano como **TEXTO**, no como referencia. Por eso:

- Borrar o renombrar uno **nunca altera los casos ya grabados**.
- No hacen falta vigencias por fecha como en Lista de Espera (allí sí, porque
  había columnas que se recalculaban al vuelo).
- **El grupo es la excepción**: se referencia por identificador, así que no se
  puede borrar ni ocultar uno que tenga casos. Se bloquea diciendo cuántos hay.

---

## 5. Funcionalidades

### Registro y consulta
- Formulario de 4 pasos. **Sólo son obligatorios NHC, fecha y grupo**: los
  casos importados no traen sexo, ASA ni cirujano y deben poder guardarse.
- Edad: si pones fecha de nacimiento se calcula y se bloquea; si no, se teclea.
- Base de datos con filtros, búsqueda por NHC y pestañas por grupo.
- Dashboard global + un panel por grupo, con bloque oncológico condicional.

### Exportación
- CSV y Excel, **una hoja por grupo** con su color. Sólo los grupos
  oncológicos llevan las 67 columnas con TNM; el resto, 28.

### Seguridad de datos (sólo admin)
- Backup `.db`, restaurar `.db` (valida los bytes mágicos de SQLite),
  importar CSV.
- Cambio de contraseña propia y de cualquier usuario.
- Recuperación por código de 6 dígitos válido 30 min, **visible sólo en los
  logs del servidor** (efímero, en RAM: se pierde al reiniciar).

### Importador de Lista de Espera
Dos pasos: `/analizar` (no escribe nada) → pantalla de revisión → `/confirmar`.

Sobre el Excel real de 109 filas: 106 nuevos, 2 repetidos dentro del propio
fichero, 1 sin grupo. Reimportar el mismo fichero inserta 0.

---

## 6. Hallazgos del Excel de Lista de Espera

Analizado sobre `lista_intervenidos (4).xlsx` (109 filas). **El fichero es de
planificación, no un parte quirúrgico**: lo importado es un punto de partida
que hay que repasar contra el parte real.

- **Las hojas SON los grupos.** No hay que adivinar nada.
- **La hoja "Sin grupo" son 44 filas** (registros anteriores a que Lista de
  Espera tuviera grupos): 43 neoplasias y 1 proctología. Se propone grupo por
  palabras clave y el usuario lo revisa.
- **91 diagnósticos distintos** en texto libre, mayúsculas, sin tildes, con TNM
  incrustado y erratas (`NEOPLSASIA`). Sólo 16 casan exactos.
- **El emparejamiento por similitud es peligroso.** Con umbral 0.75 asignaba
  `NEOPLASIA DERECHA` y `NEOPLASIA DE DESCENDENTE` a *Neoplasia de Recto* con
  0.86 y 0.76 de confianza. Por eso el umbral está en **0.90** y sólo se
  propone, nunca se aplica solo.
- **Sexo H/M**: confirmado por el usuario, H=Hombre, M=Mujer. Invertirlo
  cambiaría el sexo de 23 pacientes en silencio.
- **Cirujanos sólo por apellido** (`GRACIA`, `SAUDI` sin tilde). Se normaliza.
  **`CUADAL` no está en el catálogo** y se avisa.
- **12 procedimientos con "VS"** (`SIGMOIDECTOMIA VS HARTMANN`): son la duda
  del cirujano antes de operar. Se ofrecen ambas opciones para que elija.
- **Columna "Diagnóstico 2" vacía** en todo el fichero: ignorable.
- **NO se importa "Apellidos y nombre".** La app sólo guarda NHC y esa decisión
  de protección de datos debe conservarse.

---

## 7. Fallos corregidos (no repetirlos)

| Fallo | Causa y arreglo |
|---|---|
| 405 al guardar | `@router.post("/")` genera `/api/x/`; el frontend llamaba a `/api/x`. Usar `""` en los decoradores. |
| Dashboard global daba 500 | `GROUP BY` sobre un alias que sólo existía en el primer SELECT del UNION. Se eliminó el SQL crudo. |
| Excel con columnas desordenadas | SQLAlchemy devuelve el orden de la tabla. Se definieron listas explícitas. |
| **Editar duplicaba el registro** | `editRecord` ponía `editMode=true` y luego `clearForm()` lo reseteaba. Invertido el orden. |
| **Editar destruía datos históricos** | Si el cirujano o diagnóstico se había desactivado, el `<select>` se quedaba en blanco y al guardar borraba el dato. `populateForm` ahora añade la opción marcándola "(retirado)". |
| Desplegables mostraban inactivos | `refrescarCatalogo` mutaba y restauraba la global. Se separó `CATALOGO`/`CIRUJANOS` (activos) de `*_ADMIN` (todo). |
| Cirujanas no casaban al importar | `^(DR\|DRA)\.` — la alternancia probaba "DR" primero y dejaba `"A. GASCON"`. Se usa `^DRA?\.`. |
| BD no persistía en Railway | El volumen estaba en `/data` y la app escribía en `/app/data`. |
| Paginación de "Todos" | Pedía 20 a cada una de las 4 tablas y se quedaba con 20 de 80. La tabla única lo resuelve. |

---

## 8. Ficheros

```
main.py                    App FastAPI, auth, búsqueda global, arranque
database.py                Modelos, Registro (tabla única), catálogos
auth.py                    JWT + bcrypt (NO passlib)
schemas.py                 Pydantic
seed_catalogos.py          Siembra inicial de los 7 grupos y catálogos
migracion_tabla_unica.py   Traspaso de las 4 tablas antiguas
launcher.py                Lanzador offline: bloqueo, servidor, navegador
dev_server.py              Servidor de desarrollo con BD aparte
routers/registros.py       CRUD de intervenciones
routers/catalogos.py       CRUD de grupos, diagnósticos, intervenciones, cirujanos
routers/importador.py      Importación de Lista de Espera en dos pasos
routers/stats.py           Estadísticas: /global y /tipo/{id}
routers/export.py          CSV, Excel, backup, restaurar, importar CSV
templates/index.html       SPA completa
static/js/app.js           Frontend
coloproctologia.spec       PyInstaller (sintaxis 6.x)
build_exe.bat              Compilación
LEEME_OFFLINE.md           Guía de instalación para el hospital
```

**`.gitignore` bloquea `*.db`**: la base con datos de pacientes nunca debe
subirse al repositorio.

---

## 9. Pendiente

- [ ] Probar el `.exe` en un equipo del hospital y desde la carpeta de red
      (AppLocker, antivirus, SmartScreen).
- [ ] Repasar los 106 casos importados contra el parte quirúrgico: 85 quedaron
      sin diagnóstico del catálogo y 12 con el procedimiento por decidir.
- [ ] Recompilar el `.exe` con todo lo nuevo antes de llevarlo al hospital.
- [ ] Valorar con el responsable de protección de datos que la base **no está
      cifrada**: la confidencialidad depende de los permisos de la carpeta.
