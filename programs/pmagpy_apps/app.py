"""Assemble the PmagPy Apps page.

The page served at ``/`` is Home (:mod:`.home`): one directory as its subject,
the workflow strip, the applications as a list. The directory comes from
``?dir=``, then ``PMAGPY_APPS_DIR``, then the shipped McMurdo example, and the
"Change directory…" dialog swaps it without leaving the page; "Download from
MagIC…" fills a folder with a public contribution and opens it.
"""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel import datasets, shell
from . import APP
from .download import DownloadDialog
from .home import HomeView, HubSession, app_link, open_directory  # noqa: F401  (app_link re-exported)

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")
DEFAULT_EXAMPLE = "McMurdo"


def build_body(session: HubSession, chooser_stub: str = "") -> shell.Body:
    """Home for the session's directory; the modal holds both dialogs and shows the one asked for."""
    view = HomeView(session)
    chooser = open_directory(session, chooser_stub=chooser_stub)
    download = DownloadDialog(session)
    panes = {"chooser": chooser.modal(), "download": download.modal()}
    body = shell.Body(info=APP, main=view.panel(), header=shell.status_line(session),
                      modal=pn.Column(*panes.values()))

    def show(which: str) -> None:
        for name, pane in panes.items():
            pane.visible = name == which
        body.open_modal()

    view.change_btn.on_click(lambda e: show("chooser"))
    view.download_btn.on_click(lambda e: show("download"))
    chooser.on_loaded = download.on_loaded = lambda: body.close_modal()
    return body


def create_app(directory: str, recent_file: str = "", landing: bool = False):
    """Build the page for a directory. Returns a servable Panel template.

    Args:
        landing: the directory is the default, not one the user asked for; Home
            then lists the recent directories beside it.
    """
    session = HubSession(directory, recent_file=recent_file, landing=landing)
    return shell.template(build_body(session), logo=LOGO)


def serve_default():
    """The page for the directory this session asked for: ``?dir=``, then ``PMAGPY_APPS_DIR``, then the example."""
    asked = datasets.session_directory(APP.env_prefixes, default="")
    directory = asked or datasets.example_dir(DEFAULT_EXAMPLE)
    return create_app(directory, recent_file=datasets.shared_recent_file(), landing=not asked)
