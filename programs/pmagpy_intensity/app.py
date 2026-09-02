"""Assemble the PmagPy Intensity application."""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel import runtime, shell
from pmagpy_panel.theme import TABS_CSS
from .session import APP, Session, session_directory
from .views import (BicepView, CorrectionsView, CriteriaView, DataView, ExportView, GroupView,
                    InterpretationsView, SpecimenView)

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")

#: The Specimen tab wants the Arai plot and a 2 x 2 block of companions beside
#: it, which needs about 910 px of main pane -- what a 1440-wide laptop has
#: left over at this width.
SIDE_WIDTH = 400


def build_body(session: Session) -> shell.Body:
    """The application's body for a loaded session: side column, tabs, status, chooser dialog.

    This is what the hub mounts; :func:`create_app` wraps the same body in a
    template of its own.
    """
    dataview = DataView(session)
    specimen = SpecimenView(session)
    interps = InterpretationsView(session)
    criteria = CriteriaView(session)
    corrections = CorrectionsView(session)
    groups = GroupView(session)
    bicep = BicepView(session)
    export = ExportView(session)

    # the analysis order: interpret a specimen, review every interpretation,
    # understand why each passed or failed, correct, average, and export
    tabs = pn.Tabs(("Specimen", specimen.main()),
                   ("Interpretations", interps.panel()),
                   ("Criteria & statistics", criteria.panel()),
                   ("Corrections", corrections.panel()),
                   ("Group results", groups.panel()),
                   ("BiCEP", bicep.panel()),
                   ("Export", export.panel()),
                   dynamic=True, stylesheets=[TABS_CSS])
    lazy = {1: interps, 2: criteria, 3: corrections, 4: groups, 5: bicep}
    for index, view in lazy.items():
        view.set_active(index == tabs.active)

    side_panels = {0: specimen.sidebar(), 1: interps.sidebar(), 2: criteria.sidebar(),
                   3: corrections.sidebar(), 4: groups.sidebar(), 5: bicep.sidebar()}
    side_holder = pn.Column(side_panels[0], sizing_mode="stretch_width")
    full_width_tabs = {6}          # only Export uses the whole width

    def status() -> str:
        summary = session.study_summary()
        if not summary:
            return session.status
        return (f'{session.status} · {summary["interpreted"]} interpreted'
                f' · {summary["accepted"]} accepted · {summary["sites"]} sites')

    header = shell.status_line(session, status)
    session.param.watch(lambda e: header.refresh(), "version")

    body = shell.Body(
        info=APP, main=tabs, header=header, modal=dataview.modal(), side_width=SIDE_WIDTH,
        side=pn.Column(dataview.sidebar(), side_holder, sizing_mode="stretch_width"))

    def _on_tab(event):
        for index, view in lazy.items():
            view.set_active(index == event.new)
        show = event.new not in full_width_tabs
        body.show_side(show)
        if show:
            side_holder[:] = [side_panels.get(event.new, side_panels[0])]
    tabs.param.watch(_on_tab, "active")

    def _goto_specimen():
        tabs.active = 0
    interps.on_goto = _goto_specimen

    dataview.change_btn.on_click(lambda e: body.open_modal())
    dataview.on_loaded = lambda: body.close_modal()
    return body


def create_app(directory: str, output_dir: str | None = None):
    """Build the page for a MagIC directory. Returns a servable Panel template."""
    session = Session(directory, output_dir, cache=True)
    if session.data is None:
        return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")
    template = shell.template(build_body(session), logo=LOGO, hub_url=runtime.hub_url())
    template.session = session       # handy for tests
    return template


def serve_default():
    """The page for the directory this session asked for: ``?dir=``, then the environment, then Megiddo."""
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return create_app(session_directory(os.path.join(repo, "data_files", "3_0", "Megiddo")))
