"""Assemble the PmagPy Anisotropy application."""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel import runtime, shell
from pmagpy_panel.theme import TABS_CSS
from .session import APP, Session, session_directory
from .views import TABS, DataView, Inventory, SelectionView

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")
DEFAULT_EXAMPLE = "McMurdo"


def build_body(session: Session) -> shell.Body:
    """The application's body: side column (dataset, selection, inventory), one tab per view, status, chooser."""
    dataview = DataView(session)
    selection = SelectionView(session)
    inventory = Inventory(session)
    views = {key: cls(session) for key, _, cls in TABS}
    tabs = pn.Tabs(*[(label, views[key].panel()) for key, label, _ in TABS], dynamic=True, stylesheets=[TABS_CSS])

    body = shell.Body(info=APP, main=tabs,
                      side=pn.Column(dataview.sidebar(), selection.panel(), inventory.panel(),
                                     sizing_mode="stretch_width"),
                      header=shell.status_line(session), modal=dataview.modal(), side_width=380)
    body.views = views                    # handy for tests
    body.selection = selection
    dataview.change_btn.on_click(lambda e: body.open_modal())
    dataview.on_loaded = lambda: body.close_modal()
    return body


def create_app(directory: str):
    """Build the page for a MagIC directory. Returns a servable Panel template."""
    session = Session(directory)
    if session.specimens is None:
        return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")
    template = shell.template(build_body(session), logo=LOGO, hub_url=runtime.hub_url())
    template.session = session
    return template


def serve_default():
    """The page for the directory this session asked for: ``?dir=``, then the environment, then the example."""
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return create_app(session_directory(os.path.join(repo, "data_files", "3_0", DEFAULT_EXAMPLE)))
