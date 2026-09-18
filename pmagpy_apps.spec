# -*- mode: python -*-
"""
PyInstaller specification for the PmagPy Apps desktop application: an edition
of the family (pmagpy_apps.EDITIONS) in its own window, behind a splash screen.

    PMAGPY_BUILD_EDITION=desktop    pyinstaller --noconfirm pmagpy_apps.spec   # PmagPy Apps: Convert + Directions + Intensity
    PMAGPY_BUILD_EDITION=directions pyinstaller --noconfirm pmagpy_apps.spec   # PmagPy Directions: Convert + Directions

(from the repository root, in an environment with pyinstaller and pywebview;
setup_scripts/build_pmagpy_apps.sh wraps this). The entry point is the
edition's programs/pmagpy_apps/desktop_<edition>.py; what the build does at
start-up is described in programs/pmagpy_apps/desktop.py, and how to build and
ship it in programs/pmagpy_apps/DESKTOP.md. A one-folder build (not one-file)
so that the application opens in a moment instead of unpacking itself first.
"""
import os
import platform
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

sys.setrecursionlimit(30000)

from pmagpy import version  # noqa: E402

REPO = os.path.abspath(os.getcwd())
PROGRAMS = os.path.join(REPO, "programs")
sys.path.insert(0, PROGRAMS)
from pmagpy_apps import EDITIONS  # noqa: E402

EDITION = os.environ.get("PMAGPY_BUILD_EDITION", "desktop")
if EDITION not in EDITIONS:
    raise SystemExit(f"PMAGPY_BUILD_EDITION must be one of {sorted(EDITIONS)}, not {EDITION!r}")
ENTRY = os.path.join(PROGRAMS, "pmagpy_apps", {"desktop": "desktop_apps.py"}.get(EDITION, f"desktop_{EDITION}.py"))
APP_NAME = EDITIONS[EDITION].title
APPLICATIONS = EDITIONS[EDITION].applications or ("pmagpy_directions", "pmagpy_intensity")
VERSION = version.version.replace("pmagpy-", "")
MAC = sys.platform == "darwin"
ICON = os.path.join(PROGRAMS, "images", "PmagPy.icns" if MAC else "PmagPy.ico")

# the data the served pages read: the MagIC data model and vocabularies, the
# Natural Earth coastlines of the pole globe, each application's assets, and the
# McMurdo example the start page offers
datas = [
    (os.path.join(REPO, "pmagpy", "data_model"), os.path.join("pmagpy", "data_model")),
    (os.path.join(REPO, "pmagpy", "maps"), os.path.join("pmagpy", "maps")),
    (os.path.join(REPO, "data_files", "3_0", "McMurdo"), os.path.join("data_files", "3_0", "McMurdo")),
    (os.path.join(PROGRAMS, "pmagpy_apps", "assets"), os.path.join("pmagpy_apps", "assets")),
]
for package in ("pmagpy_panel",) + tuple(APPLICATIONS):      # each application's favicon and logo
    assets = os.path.join(PROGRAMS, package, "assets")
    if os.path.isdir(assets):
        datas.append((assets, os.path.join(package, "assets")))
# panel and bokeh ship their JavaScript, CSS and templates as package data
datas += collect_data_files("panel") + collect_data_files("bokeh") + collect_data_files("param")
datas += copy_metadata("bokeh") + copy_metadata("panel") + copy_metadata("param")

# the applications are imported by name at run time (pmagpy_panel.serve), so
# PyInstaller cannot see them from the entry point: they are named here
hiddenimports = (
    collect_submodules("panel.models") + collect_submodules("bokeh.models")
    + ["pmagpy_apps", "pmagpy_apps.app", "pmagpy_apps.desktop", "pmagpy_apps.splash",
       "pmagpy_panel", "pmagpy_panel.serve",
       "pmagpy.demag", "pmagpy.demag_geo", "pmagpy.magic_project", "pmagpy.convert_registry",
       "pmagpy.convert_2_magic", "pmagpy.paleointensity", "pmagpy.pint_stats", "pmagpy.bicep", "pmagpy.tdt",
       "pmag_env", "pmag_env.set_env",
       "scipy.special._ufuncs", "scipy.optimize", "scipy.interpolate", "scipy.stats",
       "pandas._libs.tslibs.timedeltas", "tornado", "markdown", "bleach"]
    + [name for app in APPLICATIONS for name in (app, f"{app}.app")]
)

excludes = [
    "wx", "tkinter", "_tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "qtpy",
    "IPython", "ipykernel", "ipywidgets", "jupyter", "jupyter_client", "jupyter_core", "notebook",
    "cartopy", "geopandas", "fiona", "pyproj", "shapely", "osgeo", "sklearn", "skimage", "astropy",
    "playwright", "pytest", "PyInstaller", "cmdstanpy",          # BiCEP's built-in sampler serves the build
]

a = Analysis(
    [ENTRY],
    # programs/ so that the applications import as top-level packages, never through `programs`
    pathex=[PROGRAMS, REPO],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hooksconfig={"matplotlib": {"backends": ["Agg", "PDF", "SVG", "PS"]}},
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=ICON,
    target_arch=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=APP_NAME)
if MAC:
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=ICON,
        bundle_identifier="org.pmagpy." + APP_NAME.lower().replace(" ", "-"),
        version=VERSION,
        info_plist={
            "CFBundleShortVersionString": VERSION,
            "CFBundleDisplayName": APP_NAME,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "12.0",
            "NSHumanReadableCopyright": "PmagPy contributors · BSD-3",
        },
    )
