# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['PdfMerger.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\Solan\\Downloads\\Release-24.08.0-0\\poppler-24.08.0\\Library\\bin', 'poppler-24.08.0\\Library\\bin')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PdfMerger',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\Solan\\Downloads\\pdf things\\Mask group (1).ico'],
)
