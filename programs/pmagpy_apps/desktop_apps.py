"""
PmagPy Apps as a desktop application: the entry point the packaged build starts
from (see ``pmagpy_apps.spec`` at the repository root).

    python programs/pmagpy_apps/desktop_apps.py               # from a checkout, with pywebview
    python programs/pmagpy_apps/desktop_apps.py --no-window   # serve only; print the URL

It is the ``desktop`` edition — convert measurement files into MagIC tables,
then interpret directions (PmagPy Directions) and paleointensity (PmagPy
Intensity) — in its own window, behind the splash screen, with the server in
the same process. ``desktop_directions.py`` is the same with Directions alone.
"""
import os
import sys

if not getattr(sys, "frozen", False):                                  # a checkout: find the packages
    _HERE = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(_HERE))
    sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))

from pmagpy_apps import desktop  # noqa: E402

if __name__ == "__main__":
    sys.exit(desktop.main(edition="desktop"))
