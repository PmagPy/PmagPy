"""
One-command launcher for PmagPy Rock Magnetism.

    python programs/pmagpy_rockmag/launch.py                # start (or restart) and open the browser
    python programs/pmagpy_rockmag/launch.py --no-show      # start without opening a browser tab
    python programs/pmagpy_rockmag/launch.py --port 5300 --dir /path/to/magic

The work is done by ``pmagpy_panel.launch``, shared by every application; this
only says which app to serve and what to call its settings.
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                    # programs/, for pmagpy_panel

from pmagpy_panel import launch  # noqa: E402

APP = os.path.join(_HERE, "pmagpy_rockmag.py")

if __name__ == "__main__":
    sys.exit(launch.main(APP, env_prefix="PMAGPY_ROCKMAG_", default_port=5300))
