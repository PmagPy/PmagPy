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

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))                    # programs/, for a checkout run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))   # repo root, for pmagpy

from pmagpy_panel import launch  # noqa: E402

HUB = os.path.join(_HERE, "pmagpy_apps.py")
DEFAULT_PORT = 5010


def application_files() -> list:
    """The served files of the analysis applications installed beside this one.

    One entry per application on Home's Analyze list that can actually be
    imported, so adding an application to that list is the only place it has to
    be named -- a door that leads somewhere and a page served under the hub
    cannot then disagree.
    """
    import importlib.util

    # absolute: this file is also run as a script (``python .../launch.py``), and
    # then it has no package for a relative import to resolve against
    from pmagpy_apps.home import APPLICATIONS
    files = []
    for app in APPLICATIONS:
        # find_spec, not import_module: the same test as Application.built, and it
        # locates the package without running the application
        spec = importlib.util.find_spec(app.app_id)
        origin = getattr(spec, "origin", None) if spec is not None else None
        if not origin:
            continue
        served = os.path.join(os.path.dirname(origin), f"{app.app_id}.py")
        if os.path.exists(served):
            files.append(served)
    return files


def main(argv=None) -> int:
    return launch.main([HUB, *application_files()], env_prefix="PMAGPY_APPS_",
                       default_port=DEFAULT_PORT, argv=argv, index=True)


if __name__ == "__main__":
    sys.exit(main())
