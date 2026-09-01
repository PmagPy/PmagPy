"""
Shared Panel toolkit for the PmagPy MagIC 3 applications.

PmagPy Directions (``programs/pmagpy_directions``, the successor to Demag GUI)
and the paleointensity application being built alongside it are the same kind
of program: a Panel front end over a UI-independent core in ``pmagpy``, reading
and writing MagIC 3 tables. Everything they share in the *presentation* — how
they look, how the panels are dragged, how an equal-area net is drawn, how a
MagIC directory is chosen and remembered — lives here, so that the two are one
application in two subjects rather than two applications that resemble each
other.

Together the applications are **PmagPy Apps**; ``programs/pmagpy_apps`` is the
hub that serves them side by side (``pmagpy-apps``), and HUB_PLAN.md beside
this file is its plan.

Modules
-------
theme     colours, CSS and Bokeh figure styling; ``ComponentColors`` keeps a
          name's colour the same across a whole study
widgets   the custom components: the panel splitters and the hotkey listener
nets      equal-area primitives — a square, circular net that stays circular
shell     the page: an application builds a ``Body``, a host (``template()``
          or the hub) wraps it and fills its modal and side-column hooks
runtime   how the family is running — the session's URL, the system folder
          dialog, where the hub is; the only platform-specific code
datasets  a MagIC directory as a thing to choose, remember and validate, and
          the environment settings that point an app at one
launch    the one-command launcher (dev mode, restarts, opens the browser)

What is *not* here: anything that knows about demagnetization or about
paleointensity. The science belongs in ``pmagpy`` (``pmagpy/demag.py`` for the
directions core), and the panes that present it belong to each application.

An application supplies its own identity — its name, the id it stamps on files
and the environment prefixes it answers to — through ``AppInfo``; nothing here
holds global state, so both applications can be imported into one process (the
tests do exactly that).
"""
from __future__ import annotations

from dataclasses import dataclass

FAMILY_COLOR = "#1f4e9c"      # the hub's blue: the family, and any application without a colour of its own

# One colour per application, by app_id. It is the header of that application
# and its door on the hub's Analyze list, so the two are recognisably the same
# thing; the hub itself stays FAMILY_COLOR.
APP_COLORS = {
    "pmagpy_directions": "#00A8C8",
    "pmagpy_intensity": "#F4633A",
    "pmagpy_rockmag": "#A8CF3A",
    "pmagpy_forc": "#FFB627",
    "pmagpy_anisotropy": "#8E6BBE",
}


def app_color(app_id: str) -> str:
    """The application's colour, or the family's when it has none of its own."""
    return APP_COLORS.get(app_id, FAMILY_COLOR)


def text_on(color: str) -> str:
    """White or near-black, whichever reads on a header of this colour (WCAG relative luminance)."""
    r, g, b = (int(color.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    luminance = 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]
    return "#1b1b1b" if luminance > 0.45 else "#ffffff"


@dataclass(frozen=True)
class AppInfo:
    """What distinguishes one of these applications from the other.

    Args:
        name: shown in the header, e.g. "PmagPy Directions".
        app_id: identifier stamped on the files it writes and on
            ``software_packages`` in the MagIC tables, e.g. "pmagpy_directions".
        env_prefixes: prefixes of the environment settings it answers to, most
            specific first — the second and later ones are kept for
            compatibility with names an earlier build used.
        color: the application's colour; looked up from :data:`APP_COLORS` by
            ``app_id`` when not given.
    """

    name: str
    app_id: str
    env_prefixes: tuple = ()
    color: str = ""

    def __post_init__(self):
        if not self.color:
            object.__setattr__(self, "color", app_color(self.app_id))
