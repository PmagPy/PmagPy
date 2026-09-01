"""
One-command launcher for PmagPy Directions.

    python programs/pmagpy_directions/launch.py                # start (or restart) and open the browser
    python programs/pmagpy_directions/launch.py --no-show      # start without opening a browser tab
    python programs/pmagpy_directions/launch.py --port 5200 --dir /path/to/magic --output /path/to/out

The work is done by ``pmagpy_panel.launch``, which both of these applications
share; this only says which app to serve and what to call its settings. Run it
from any working directory; it uses the Python interpreter it is started with
(activate the environment that has panel installed first).
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                    # programs/, for pmagpy_panel

from pmagpy_panel import launch  # noqa: E402

APP = os.path.join(_HERE, "pmagpy_directions.py")

if __name__ == "__main__":
    sys.exit(launch.main(APP, env_prefix="PMAGPY_DIRECTIONS_", default_port=5100))
