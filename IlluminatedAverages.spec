# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['illuminated_average_tk.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python311\\tcl\\tcl8.6', 'tcl\\tcl8.6'), ('C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python311\\tcl\\tk8.6', 'tcl\\tk8.6')],
    hiddenimports=['tkinter', 'tkinter.filedialog', 'tkinter.messagebox', 'tkinter.ttk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_tk_runtime_hook.py'],
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
    name='IlluminatedAverages',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
