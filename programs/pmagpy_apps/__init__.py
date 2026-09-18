"""
PmagPy Apps — the front door to the PmagPy Panel applications.

The family's home: the pages that hold a MagIC directory, convert magnetometer
files into it, describe it, and hand it to an analysis application — PmagPy
Directions, PmagPy Intensity and the rest — which are mounted into this page
rather than opened as separate programs. It is the successor to
``programs/pmag_gui.py``; the plan is ``programs/pmagpy_panel/HUB_PLAN.md``.

Every analysis application still launches on its own (its own ``launch.py``,
its own port); this package is additive. It knows the applications; they do not
know it.

Modules
-------
app          assembles the page; ``create_app()`` is the entry point
launch       the ``pmagpy-apps`` command: serves this page at ``/`` with the
             applications beside it
desktop      the packaged build: the family in its own window, behind a
             splash screen, with the server in the same process
splash       the splash screen's HTML

An *edition* (:class:`Edition`) is the subset of the family a build offers;
``PMAGPY_APPS_EDITION`` selects it, and the desktop build of PmagPy Directions
is the ``directions`` edition.
"""
import os
from dataclasses import dataclass
from typing import Optional

from pmagpy_panel import AppInfo

APP_NAME = "PmagPy Apps"
APP = AppInfo(name=APP_NAME, app_id="pmagpy_apps", env_prefixes=("PMAGPY_APPS_",))


@dataclass(frozen=True)
class Edition:
    """Which part of the family a build offers.

    The whole family is one code base; an *edition* is the subset a particular
    build puts in front of the analyst. The packaged desktop build ships the
    Directions edition — convert measurement files, then interpret directions —
    so that experience can be iterated on while the other applications are
    built out; ``pmagpy-apps`` from a Python install is the full edition.

    Attributes:
        key: the name on ``PMAGPY_APPS_EDITION``.
        title: what the window and the splash screen are called.
        tagline: one line under the start page's lead (empty for none).
        applications: the ``app_id`` of every application served and listed;
            None means every one that is installed.
        doors: the start page's doors, by :class:`~pmagpy_apps.home.HomeView`
            attribute, in order.
        pages: the directory page's tools beyond Convert: any of ``"download"``,
            ``"metadata"``, ``"upload"``.
    """
    key: str
    title: str
    tagline: str
    applications: Optional[tuple]
    doors: tuple
    pages: tuple

    def offers(self, app_id: str) -> bool:
        return self.applications is None or app_id in self.applications

    def has_page(self, page: str) -> bool:
        return page in self.pages


ALL_DOORS = ("open_btn", "download_start_btn", "convert_start_btn", "example_btn")
EDITIONS = {
    "full": Edition("full", APP_NAME, "", None, ALL_DOORS, ("download", "metadata", "upload")),
    "directions": Edition("directions", "PmagPy Directions",
                          "Convert measurement files into MagIC tables, then interpret the directions.",
                          ("pmagpy_directions",), ("open_btn", "convert_start_btn", "example_btn"), ()),
}
EDITION_VAR = "PMAGPY_APPS_EDITION"


def current_edition() -> Edition:
    """The edition this process serves: ``PMAGPY_APPS_EDITION``, else the full family."""
    return EDITIONS.get(os.environ.get(EDITION_VAR, "full"), EDITIONS["full"])
