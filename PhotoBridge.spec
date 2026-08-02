# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PhotoBridge
This bundles the desktop GUI (entry point), backend, and frontend assets
into a single PhotoBridge.exe with no external Python dependency.

Uses --onedir mode to keep all dependencies together in dist/PhotoBridge/
"""

import sys
import os

block_cipher = None

# Get project root from current working directory
# (the spec file should be run from the project root)
project_root = os.getcwd()

a = Analysis(
    [os.path.join(project_root, 'desktop_gui', 'gui_app.py')],
    pathex=[project_root, os.path.join(project_root, 'backend')],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'frontend'), 'frontend'),
    ],
    hiddenimports=[
        'app',
        'app.main',
        'app.config',
        'app.logger',
        'app.media',
        'app.scanner',
        'app.paths',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
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
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'desktop_gui', 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PhotoBridge'
)

