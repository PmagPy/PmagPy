"""App tests import the package as top-level ``pmagpy_rockmag`` (see pmagpy_rockmag.py)."""
import os
import sys
import tempfile

import matplotlib

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                            # programs/
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))           # repo root
matplotlib.use("Agg")
# keep the test run's loads out of the user's shared recent-directories list
os.environ.setdefault("PMAGPY_ROCKMAG_RECENT",
                      os.path.join(tempfile.mkdtemp(prefix="pmagpy_rockmag_test_"), "recent.json"))
