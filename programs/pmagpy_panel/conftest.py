"""Toolkit tests import the package as top-level ``pmagpy_panel``."""
import os
import sys

import matplotlib

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                            # programs/
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))           # repo root
matplotlib.use("Agg")
