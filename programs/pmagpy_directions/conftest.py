"""App tests import the package as top-level ``pmagpy_directions`` (see pmagpy_directions.py)."""
import os
import sys
import tempfile

import matplotlib

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                            # programs/
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))           # repo root
matplotlib.use("Agg")

# the PmagPy folder (copies of the examples, contributions downloaded from MagIC) is a temporary
# one: a test run never writes into the user's ~/PmagPy, also when a test clears the setting
import tempfile as _tempfile                                           # noqa: E402
from pmagpy_panel import datasets as _datasets                         # noqa: E402
_PMAGPY_HOME = _tempfile.mkdtemp(prefix="pmagpy_home_test_")
_datasets.DEFAULT_HOME = _PMAGPY_HOME
os.environ.setdefault("PMAGPY_APPS_OUTPUT", _PMAGPY_HOME)
# session.py binds its recent-directories file at import; keep the test run's
# loads out of the user's shared ~/.pmagpy list
_TMP = tempfile.mkdtemp(prefix="pmagpy_directions_test_")
os.environ.setdefault("PMAGPY_DIRECTIONS_RECENT", os.path.join(_TMP, "recent.json"))
# ... and the arrangement of the plot cards out of the user's own
os.environ.setdefault("PMAGPY_DIRECTIONS_LAYOUT", os.path.join(_TMP, "layout.json"))
