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
    """

    name: str
    app_id: str
    env_prefixes: tuple = ()
