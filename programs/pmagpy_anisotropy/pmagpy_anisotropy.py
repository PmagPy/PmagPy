"""
PmagPy Anisotropy — Panel application launcher.

    panel serve programs/pmagpy_anisotropy/pmagpy_anisotropy.py --show
    PMAGPY_ANISOTROPY_DIR=/path/to/magic/dir panel serve programs/pmagpy_anisotropy/pmagpy_anisotropy.py --show

``PMAGPY_ANISOTROPY_DIR`` selects the MagIC directory (default
``data_files/3_0/McMurdo``, the AARM tensors of the McMurdo Sound dikes).
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
# the app is imported as the top-level package ``pmagpy_anisotropy`` (not through
# ``programs``, whose __init__ pins a GUI matplotlib backend for the wx programs)
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))          # repo root: pmagpy

from pmagpy_anisotropy.app import serve_default  # noqa: E402

app = serve_default()
app.servable()
