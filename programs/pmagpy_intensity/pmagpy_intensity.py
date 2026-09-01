"""
PmagPy Intensity — Panel application launcher.

    panel serve programs/pmagpy_intensity/pmagpy_intensity.py --show
    PMAGPY_INTENSITY_DIR=/path/to/magic/dir panel serve programs/pmagpy_intensity/pmagpy_intensity.py --show

``PMAGPY_INTENSITY_DIR`` selects the MagIC directory (default
``data_files/3_0/Megiddo``); ``PMAGPY_INTENSITY_OUTPUT`` redirects everything the
app writes (sessions, MagIC tables, figures) away from the data directory.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# the app is imported as the top-level package ``pmagpy_intensity`` (not through
# ``programs``, whose __init__ pins a GUI matplotlib backend for the wx programs)
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))          # repo root: pmagpy

from pmagpy_intensity.app import serve_default  # noqa: E402

app = serve_default()
app.servable()
