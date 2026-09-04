"""
PmagPy Rock Magnetism — Panel application launcher.

    panel serve programs/pmagpy_rockmag/pmagpy_rockmag.py --show
    PMAGPY_ROCKMAG_DIR=/path/to/magic/dir panel serve programs/pmagpy_rockmag/pmagpy_rockmag.py --show

``PMAGPY_ROCKMAG_DIR`` selects the MagIC directory (default
``data_files/3_0/RMB_oxyhydroxides``, MagIC contribution 20427).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# the app is imported as the top-level package ``pmagpy_rockmag`` (not through
# ``programs``, whose __init__ pins a GUI matplotlib backend for the wx programs)
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))          # repo root: pmagpy

from pmagpy_rockmag.app import serve_default  # noqa: E402

app = serve_default()
app.servable()
