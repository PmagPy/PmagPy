# -*- mode: python -*-

# this is an example.spec file

import os
import sys
from pmagpy import version
sys.setrecursionlimit(30000)
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
                                'scipy.datasets', 
                                'scipy.odr', 
                                'scipy.io', 'scipy.fftpack', 
                                'scipy.cluster','scipy.optimize', 'scipy.interpolate',
                                'scipy._lib.messagestream',
                                'pandas._libs.tslibs.timedeltas',
                                'pandas.concat', 'wget', 'pkg_resources.py2_warn'],
             hooksconfig={
                        "matplotlib": {
                        "backends": "WXAgg",  # collect wxpython backends
                        },
                },
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          #name='pmag_gui',
          name=app_name,
          debug=False,
          strip=False,
          upx=True,
          console=False, icon='./programs/images/pmagpy_logo.ico')
app = BUNDLE(exe,
             name=app_name + ".app",
             icon='./programs/images/pmagpy_logo.ico',
             bundle_identifier=None)
