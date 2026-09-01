"""
PmagPy Apps — the front door to the PmagPy Panel applications.

The family's home: the pages that hold a MagIC directory, convert magnetometer
files into it, describe it, and hand it to an analysis application — PmagPy
Directions, PmagPy Intensity and the rest — which are mounted into this page
rather than opened as separate programs. It is the successor to
``programs/pmag_gui.py``; the plan is ``programs/pmagpy_panel/HUB_PLAN.md``.

Every analysis application still launches on its own (its own ``launch.py``,
its own port); this package is additive. It knows the applications; they do not
know it.

Modules
-------
app          assembles the page; ``create_app()`` is the entry point
launch       the ``pmagpy-apps`` command: serves this page at ``/`` with the
             applications beside it
"""
from pmagpy_panel import AppInfo

APP_NAME = "PmagPy Apps"
APP = AppInfo(name=APP_NAME, app_id="pmagpy_apps", env_prefixes=("PMAGPY_APPS_",))
