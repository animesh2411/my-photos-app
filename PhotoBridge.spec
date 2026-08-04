# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PhotoBridge.
Bundles desktop_gui (entry point), backend, and frontend assets into
a single PhotoBridge.exe with no external Python dependency.

Build with:  pyinstaller PhotoBridge.spec
Output:      dist/PhotoBridge/PhotoBridge.exe
"""

import os

block_cipher = None

a = Analysis(
    ['desktop_gui/gui_app.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        # Static web frontend assets (HTML, CSS, JS, icons, manifest)
        ('frontend', 'frontend'),
        # Desktop app icon
        ('desktop_gui/icon.ico', 'desktop_gui'),
        # Backend Python modules (bundled as data so app.* imports work)
        ('backend/app', 'app'),
        ('backend/run.py', '.'),
    ],
    hiddenimports=[
        # Uvicorn internals that are imported dynamically
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
        # FastAPI / Starlette internals
        'starlette.responses',
        'starlette.routing',
        'starlette.staticfiles',
        'starlette.middleware',
        'multipart',
        'multipart.multipart',
        # App modules
        'app.config',
        'app.scanner',
        'app.media',
        'app.logger',
        'app.main',
        'app.paths',
        # PIL / Pillow
        'PIL',
        'PIL.Image',
        'PIL.ExifTags',
        # pillow-heif (optional, may not be installed)
        'pillow_heif',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'IPython',
        'notebook',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PhotoBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window — Tkinter GUI only
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='desktop_gui/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoBridge',
)
