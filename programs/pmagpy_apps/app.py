"""Assemble the PmagPy Apps page.

The page served at ``/`` is Home (:mod:`.home`): the start page until a
directory is open, then that directory as its subject, the workflow strip, the
applications as a list. The directory comes from ``?dir=``, then
``PMAGPY_APPS_DIR``; with neither the start page shows, offering a folder
("Change directory…" swaps it later without leaving the page), a download from
MagIC (a public contribution into a folder, then opened) and the shipped McMurdo
example. "Convert files…" turns the page over to Convert (:mod:`.convert`),
which comes back Home when the tables are written; "Metadata…" turns it over to
the tables in a grid (:mod:`.metadata`); "Upload…" to the upload builder.
"""
from __future__ import annotations

import os

import panel as pn

from typing import Optional

from pmagpy_panel import datasets, shell
from . import APP, EDITIONS, Edition, current_edition
from .convert import ConvertView
from .download import DownloadDialog
from .home import HomeView, HubSession, app_link, open_directory  # noqa: F401  (app_link re-exported)

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")


def build_body(session: HubSession, chooser_stub: str = "", edition: Optional[Edition] = None) -> shell.Body:
    """Home, Convert, Metadata and Upload for the session's directory, one shown at a time; the modal holds both dialogs.

    Args:
        edition: the pages and applications to offer; the full family by
            default. The pages an edition leaves out are not built at all.
    """
    edition = edition or EDITIONS["full"]
    view = HomeView(session, edition=edition)
    convert = ConvertView(session)
    tools = {}
    if edition.has_page("metadata"):
        from .metadata import MetadataView
        tools["metadata"] = MetadataView(session)
    if edition.has_page("upload"):
        from .upload import UploadView
        tools["upload"] = UploadView(session)
    chooser = open_directory(session, chooser_stub=chooser_stub)
    download = DownloadDialog(session)
    panes = {"chooser": chooser.modal(), "download": download.modal()}
    pages = {"home": view.panel(), "convert": convert.panel()}
    pages.update({name: tool.panel() for name, tool in tools.items()})
    for name in pages:
        if name != "home":
            pages[name].visible = False
    body = shell.Body(info=APP, main=pn.Column(*pages.values(), sizing_mode="stretch_width"),
                      header=shell.status_line(session), modal=pn.Column(*panes.values()))

    def show(which: str) -> None:
        for name, pane in panes.items():
            pane.visible = name == which
        body.open_modal()

    # the chooser serves two doors: its heading says which, and a folder chosen for conversion goes on to Convert
    chooser_heading = panes["chooser"][0][0]
    heading_for = {"open": chooser_heading.object, "convert": chooser.heading_html(
        "Choose the folder of measurement files", "The files are converted into MagIC tables in the same folder.")}
    to_convert = []

    def show_chooser(purpose: str) -> None:
        chooser_heading.object = heading_for[purpose]
        to_convert[:] = [purpose == "convert"]
        show("chooser")

    def chooser_loaded() -> None:
        body.close_modal()
        if to_convert and to_convert[0] and not session.inventory.is_magic:
            turn_to("convert")
        to_convert[:] = []

    def turn_to(which: str) -> None:
        if which not in pages:
            return
        for name, page in pages.items():
            page.visible = name == which
        if which == "convert":
            convert.reset()
        elif which in tools:
            tools[which].reset()

    view.change_btn.on_click(lambda e: show_chooser("open"))
    view.open_btn.on_click(lambda e: show_chooser("open"))
    view.convert_start_btn.on_click(lambda e: show_chooser("convert"))
    view.download_btn.on_click(lambda e: show("download"))
    view.download_start_btn.on_click(lambda e: show("download"))
    view.convert_btn.on_click(lambda e: turn_to("convert"))
    view.metadata_btn.on_click(lambda e: turn_to("metadata"))
    view.upload_btn.on_click(lambda e: turn_to("upload"))
    convert.home_btn.on_click(lambda e: turn_to("home"))
    for tool in tools.values():
        tool.home_btn.on_click(lambda e: turn_to("home"))
    chooser.busy = body.main             # a spinner over the page while a directory is read
    chooser.on_loaded = chooser_loaded
    download.on_loaded = lambda: body.close_modal()
    body.pages = pages           # for the tests and any host that wants to turn the page
    body.turn_to = turn_to
    body.chooser, body.downloader = chooser, download
    return body


def create_app(directory: str = "", recent_file: str = "", edition: Optional[Edition] = None):
    """Build the page: the start page when `directory` is empty, else the page for that directory.
    Returns a servable Panel template."""
    session = HubSession(directory, recent_file=recent_file)
    return shell.template(build_body(session, edition=edition), logo=LOGO)


def serve_default():
    """The page for the directory this session asked for — ``?dir=``, then ``PMAGPY_APPS_DIR`` — or the start
    page; in the edition ``PMAGPY_APPS_EDITION`` names."""
    asked = datasets.session_directory(APP.env_prefixes, default="")
    return create_app(asked, recent_file=datasets.shared_recent_file(), edition=current_edition())
