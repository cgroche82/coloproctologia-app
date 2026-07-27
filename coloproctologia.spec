# -*- mode: python ; coding: utf-8 -*-
"""
Especificación PyInstaller — Registro Quirúrgico Coloproctología (HUMS)

Compilar con:   pyinstaller coloproctologia.spec --noconfirm

Genera dist/RegistroColoproctologia/ (modo onedir). Se eligió onedir en vez de
onefile porque desde una carpeta de red onefile descomprime ~50 MB en el disco
local en cada arranque, lo que añade 10-15 s de espera cada vez que se abre.

Sintaxis de PyInstaller 6.x (sin cipher ni block_cipher, eliminados en 6.0).
"""

import os

icono = 'static/logo_hums.ico' if os.path.exists('static/logo_hums.ico') else None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        # uvicorn carga estos por nombre en tiempo de ejecución
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # dialecto SQLite de SQLAlchemy
        'sqlalchemy.dialects.sqlite',
        # autenticación
        'bcrypt',
        'jose',
        'jose.backends',
        'jose.backends.cryptography_backend',
        # exportación Excel
        'openpyxl',
        'openpyxl.cell._writer',
        # módulos propios cargados desde launcher
        'main',
        'auth',
        'database',
        'schemas',
        'routers',
        'routers.colorrectal',
        'routers.proctologia',
        'routers.funcionales',
        'routers.general',
        'routers.stats',
        'routers.export',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RegistroColoproctologia',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # sin ventana de consola negra
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icono,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RegistroColoproctologia',
)
