"""Toolkit tests import the package as top-level ``pmagpy_panel``."""
import os
import sys

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
