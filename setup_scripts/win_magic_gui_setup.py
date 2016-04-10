import distutils.core
from distutils.core import setup
import py2exe
import matplotlib
import os
import glob
import sys
sys.setrecursionlimit(3000)
directory = os.getcwd()


help_data = glob.glob(os.path.join(directory, 'dialogs', 'help_files') + os.path.sep + '*')
data_model = glob.glob(os.path.join(directory, 'pmagpy', 'data_model') + os.path.sep + '*')

img_files = [('images', [os.path.join(directory, 'programs', 'images', 'PmagPy.ico')])]
help_files = [('help_files', help_data)]
data_files = [('data_model', data_model)]

all_data_files = matplotlib.get_py2exe_datafiles()
all_data_files.extend(img_files)
all_data_files.extend(help_files)
all_data_files.extend(data_files)


distutils.core.setup(
    options = {
        "py2exe": {
            "dist_dir": "MagIC_GUI_dist",
            "includes": ["scipy", "scipy.special.*", "scipy.linalg.*", "scipy.linalg._decomp_update", "scipy.sparse.*", "scipy.sparse.csgraph.*", "scipy.ndimage", "scipy.ndimage.*", "scipy.linalg.cython_blas"],
            "packages": ["matplotlib", "pytz", "pandas"],
            "dll_excludes": ["MSVCP90.dll", "libzmq.dll", "sodium.dll", "api-ms-win-core-string-l1-1-0.dll", "api-ms-win-core-memory-l1-1-2.dll", "api-ms-win-core-file-l1-2-1.dll", "api-ms-win-core-libraryloader-l1-2-1.dll", "api-ms-win-core-string-l2-1-0.dll", "api-ms-win-core-profile-l1-1-0.dll", "api-ms-win-core-string-obsolete-l1-1-0.dll", "api-ms-win-core-debug-l1-1-1.dll", "api-ms-win-core*.dll", "api-ms-win-core-sidebyside-l1-1-0.dll", "api-ms-win-core-processthreads-l1-1-2.dll", "api-ms-win-core-kernel32-legacy-l1-1-1.dll", "api-ms-win-core-handle-l1-1-0.dll", "api-ms-win-core-timezone-l1-1-0.dll", "api-ms-win-core-processenvironment-l1-2-0.dll", "api-ms-win-core-registry-l1-1-0.dll", "numpy-atlas.dll"],#, "api-ms-win-core-string-l1-1-0.dll", "api-ms-win-core-memory-l1-1-2.dll"]  
        }
    },
    data_files=all_data_files,
    windows=['programs\magic_gui.py']
)

#setup(windows=['simple.py'])

# more dlls to exclude ??
# api-ms-win-core-string-l1-1-0.dll
