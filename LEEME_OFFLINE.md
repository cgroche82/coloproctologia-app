# Versión offline — Registro Quirúrgico Coloproctología (HUMS)

Aplicación de escritorio para equipos del hospital. **No usa internet**: el
servidor corre dentro del propio ejecutable, en `127.0.0.1`, y los datos nunca
salen del ordenador ni de la carpeta compartida.

---

## Compilar el ejecutable

En un PC con Python 3.11 instalado, desde la carpeta del proyecto:

```bash
build_exe.bat
```

Tarda 1-3 minutos. Genera `dist\RegistroColoproctologia\` con el ejecutable y
todas sus dependencias (Python incluido: los equipos destino **no** necesitan
tener Python).

---

## Instalar en el hospital

1. Copiar la carpeta **completa** `RegistroColoproctologia` al buzón compartido.
2. Crear un acceso directo a `RegistroColoproctologia.exe` en el escritorio de
   cada usuario que la vaya a usar.
3. Al primer arranque se crea `coloproctologia.db` dentro de esa misma carpeta.

Estructura resultante:

```
\\servidor\buzon\RegistroColoproctologia\
├── RegistroColoproctologia.exe     ← ejecutable
├── coloproctologia.db              ← base de datos (se crea sola)
├── registro_app.log                ← registro de incidencias
├── _internal\                      ← dependencias, no tocar
├── .coloproctologia.lock           ← control de acceso, no tocar
└── .coloproctologia.owner          ← control de acceso, no tocar
```

**Credenciales iniciales:** `admin` / `coloproct2024` — cámbiala en el primer
acceso desde el icono de la llave en la barra superior.

---

## Un usuario a la vez

SQLite no garantiza los bloqueos de fichero sobre unidades de red (SMB). Si dos
equipos escribiesen a la vez sobre el mismo `.db`, la base de datos podría
corromperse **sin dar ningún error visible**.

Para evitarlo la aplicación sólo permite una instancia abierta en toda la red.
Si alguien intenta abrirla mientras otro la usa, ve:

```
⚠  La aplicación ya está abierta por otro usuario.

    Usuario: mgarcia
    Equipo:  PC-CONSULTA-3
    Desde:   27/07/2026 09:14
```

El bloqueo lo libera el sistema operativo automáticamente al cerrar la
aplicación, **incluso si el programa se cuelga o el PC se apaga de golpe**
(comprobado). No hay que borrar ningún fichero a mano.

> Si el bloqueo se quedase atascado tras un corte de red, cerrar la aplicación
> en todos los equipos y borrar `.coloproctologia.lock` y
> `.coloproctologia.owner`. Asegurarse antes de que nadie la tiene abierta.

---

## Copias de seguridad

La sección **Exportación** incluye, para el administrador:

- **Descargar Backup** — copia del `.db` completo con fecha en el nombre.
- **Restaurar Backup** — reemplaza la base de datos actual.
- **Importar CSV** — añade registros sin borrar los existentes.

Conviene descargar un backup periódicamente y guardarlo en otra ubicación.
Hacerlo siempre con el resto de usuarios fuera de la aplicación.

---

## Resolución de problemas

| Síntoma | Causa probable y solución |
|---|---|
| Windows bloquea el `.exe` ("editor desconocido") | El ejecutable no está firmado digitalmente. Pulsar *Más información → Ejecutar de todas formas*, o pedir a Informática que lo autorice. |
| El antivirus lo pone en cuarentena | Falso positivo habitual con PyInstaller. Informática debe añadir la carpeta como excepción. |
| "No se puede ejecutar desde una ubicación de red" | Directiva AppLocker/SRP del hospital. Requiere que Informática autorice la ruta del buzón compartido. |
| Tarda en abrir | Normal desde unidad de red la primera vez. Los siguientes arranques son más rápidos por la caché de Windows. |
| Se abre con barra de direcciones | No se encontró Chrome ni Edge y se usó el navegador por defecto. Funciona igual. |
| No arranca y no dice nada | Revisar `registro_app.log` en la carpeta de la aplicación. |

---

## Nota sobre protección de datos

La base de datos **no está cifrada**. La confidencialidad depende de los
permisos de la carpeta compartida, que debe estar restringida al personal
autorizado de la unidad. Conviene consultarlo con el responsable de protección
de datos del hospital antes de introducir datos reales de pacientes.
