"""
The ``pmagpy-apps`` command: serve the family on one port.

    pmagpy-apps                       # start (or restart) and open the browser
    pmagpy-apps --no-show             # start without opening a browser tab
    pmagpy-apps --port 5200 --dir /path/to/magic

This page is served at ``/`` and each application beside it (``/pmagpy_directions``
…), all from one process, so a directory opened here is opened once. The work
is done by ``pmagpy_panel.launch``; this only says which files to serve.
"""
from __future__ import annotations

import importlib
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                    # programs/, for a checkout run as a script

from pmagpy_panel import launch  # noqa: E402

HUB = os.path.join(_HERE, "pmagpy_apps.py")
DEFAULT_PORT = 5010
# the analysis applications, served beside the hub when they are installed
APPLICATIONS = ("pmagpy_directions", "pmagpy_rockmag")


def application_files() -> list:
    """The served files of the analysis applications installed beside this one."""
    files = []
    for name in APPLICATIONS:
        try:
            package = importlib.import_module(name)
        except ImportError:
            continue
        files.append(os.path.join(os.path.dirname(os.path.abspath(package.__file__)), name + ".py"))
    return files


def main(argv=None) -> int:
    return launch.main([HUB, *application_files()], env_prefix="PMAGPY_APPS_",
                       default_port=DEFAULT_PORT, argv=argv, index=True)


if __name__ == "__main__":
    sys.exit(main())
