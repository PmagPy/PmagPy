"""App tests import the package as top-level ``pmagpy_rockmag`` (see pmagpy_rockmag.py)."""
import os
import sys
import tempfile

import matplotlib
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                            # programs/
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))           # repo root
matplotlib.use("Agg")
# keep the test run's loads out of the user's shared recent-directories list
os.environ.setdefault("PMAGPY_ROCKMAG_RECENT",
                      os.path.join(tempfile.mkdtemp(prefix="pmagpy_rockmag_test_"), "recent.json"))


@pytest.fixture(autouse=True)
def no_browser(monkeypatch):
    """The notebook code the views write ends in ``show()``; running it in a test must not open a browser."""
    from pmagpy import rockmag
    monkeypatch.setattr(rockmag, "show", lambda *a, **k: None)
