"""
PmagPy Directions — Panel application launcher.

    panel serve programs/pmagpy_directions/pmagpy_directions.py --show
    PMAGPY_DIRECTIONS_DIR=/path/to/magic/dir panel serve programs/pmagpy_directions/pmagpy_directions.py --show

``PMAGPY_DIRECTIONS_DIR`` selects the MagIC directory (default ``data_files/3_0/McMurdo``);
``PMAGPY_DIRECTIONS_OUTPUT`` redirects everything the app writes (auto-saved .redo, MagIC
tables, figures) away from the data directory.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# the app is imported as the top-level package ``pmagpy_directions`` (not through
# ``programs``, whose __init__ pins a GUI matplotlib backend for the wx programs)
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))          # repo root: pmagpy

from pmagpy_directions.app import serve_default  # noqa: E402

app = serve_default()
app.servable()
