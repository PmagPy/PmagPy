"""
PmagPy Apps — the served file.

    pmagpy-apps                                            # after pip install -e '.[apps]'
    python programs/pmagpy_apps/launch.py                  # from a checkout
    panel serve programs/pmagpy_apps/pmagpy_apps.py --show # this page alone

``PMAGPY_APPS_DIR`` selects the MagIC directory (default: the McMurdo example);
``?dir=`` on the URL overrides it for one browser tab.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# the app is imported as the top-level package ``pmagpy_apps`` (not through
# ``programs``, whose __init__ pins a GUI matplotlib backend for the wx programs)
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))          # repo root: pmagpy

from pmagpy_apps.app import serve_default  # noqa: E402

app = serve_default()
app.servable()
