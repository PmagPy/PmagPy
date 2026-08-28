# -*- mode: python ; coding: utf-8 -*-

"""Optimized, one-directory Pmag GUI build for 64-bit Windows."""

import importlib.util
import os
import platform
import sys

from pmagpy import version


if platform.system() != 'Windows' or sys.maxsize <= 2**32:
    raise SystemExit('pmag_gui_windows.spec must be built with 64-bit Python on Windows')

sys.setrecursionlimit(30000)

app_name = "pmag_gui_{}_Windows".format(version.version[7:])
current_dir = os.getcwd()
block_cipher = None

files = [
    (os.path.join(current_dir, 'pmagpy', 'data_model', '*.json'), './pmagpy/data_model/'),
    (os.path.join(current_dir, 'dialogs', 'help_files', '*.html'), './dialogs/help_files'),
]

hidden_imports = [
    'scipy.misc',
    'scipy.datasets',
    'scipy.odr',
    'scipy.io',
    'scipy.fftpack',
    'scipy.cluster',
    'scipy.optimize',
    'scipy.interpolate',
    'scipy._lib.messagestream',
    'pandas._libs.tslibs.timedeltas',
]
if importlib.util.find_spec('scipy.differentiate') is not None:
    hidden_imports.append('scipy.differentiate')

excluded_modules = [
    'IPython', 'ipykernel', 'ipywidgets', 'jupyter', 'jupyter_client',
    'jupyter_core', 'notebook', 'traitlets',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'qtpy', 'tkinter', 'gi',
    'cartopy', 'geopandas', 'fiona', 'pyproj', 'shapely', 'osgeo',
    'folium', 'branca', 'sklearn', 'skimage', 'astropy', 'imageio', 'altair',
]

a = Analysis(
    ['programs/pmag_gui.py'],
    pathex=[current_dir],
    binaries=[],
    datas=files,
    hiddenimports=hidden_imports,
    hooksconfig={'matplotlib': {'backends': 'WXAgg'}},
    hookspath=[],
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# A base Conda installation can remain on PATH while another environment is
# active. Prefer the Intel runtimes belonging to the active environment so
# SciPy extensions do not pick up ABI-incompatible DLLs in frozen builds.
for dll_name in ('libifcoremd.dll', 'libmmd.dll'):
    dll_path = os.path.join(sys.prefix, 'Library', 'bin', dll_name)
    if os.path.isfile(dll_path):
        for index, (dest_name, _source_path, typecode) in enumerate(a.binaries):
            if dest_name.lower() == dll_name.lower():
                a.binaries[index] = (dest_name, dll_path, typecode)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon='./programs/images/pmagpy_logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=app_name,
)
