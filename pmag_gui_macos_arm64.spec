# -*- mode: python -*-

# PyInstaller specification for the Apple-silicon-only macOS application.

import os
import platform
import sys
from pmagpy import version
sys.setrecursionlimit(30000)

if sys.platform != 'darwin' or platform.machine() != 'arm64':
    raise SystemExit('pmag_gui must be built natively on Apple silicon (arm64)')

app_name = "pmag_gui_{}".format(version.version[7:])
current_dir = os.getcwd()

block_cipher = None

files = [('{}/pmagpy/data_model/*.json'.format(current_dir), './pmagpy/data_model/'),
         ('{}/dialogs/help_files/*.html'.format(current_dir), './dialogs/help_files')
        ]


a = Analysis(['programs/pmag_gui.py'],
             pathex=[current_dir],
             binaries=[],
             datas=files,
             hiddenimports=[    'scipy.misc', 
                                'scipy.differentiate',
                                'scipy.datasets', 
                                'scipy.odr', 
                                'scipy.io', 'scipy.fftpack', 
                                'scipy.cluster','scipy.optimize', 'scipy.interpolate',
                                'scipy._lib.messagestream',
                                'pandas._libs.tslibs.timedeltas'],
             hooksconfig={
                        "matplotlib": {
                        "backends": "WXAgg",  # collect wxpython backends
                        },
                },
             hookspath=[],
             runtime_hooks=[],
             excludes=['IPython', 'ipykernel', 'ipywidgets', 'jupyter',
                       'jupyter_client', 'jupyter_core', 'notebook', 'traitlets',
                       'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'qtpy',
                       'tkinter', 'gi', 'cartopy', 'geopandas', 'fiona',
                       'pyproj', 'shapely', 'osgeo', 'folium', 'branca',
                       'sklearn', 'skimage', 'astropy', 'imageio', 'altair'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          #name='pmag_gui',
          exclude_binaries=True,
          name=app_name,
          debug=False,
          strip=False,
          upx=True,
          target_arch='arm64',
          console=False, icon='./programs/images/pmagpy_logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=app_name)
app = BUNDLE(coll,
             name=app_name + ".app",
             icon='./programs/images/pmagpy_logo.ico',
             bundle_identifier=None)
