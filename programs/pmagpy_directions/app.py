"""Assemble the PmagPy Directions application."""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel import runtime, shell
from pmagpy_panel.theme import TABS_CSS
from .session import APP, Session, session_directory
from .views import DataView, ExportView, InterpretationsView, MeansView, PolesView, SpecimenView

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")


def build_body(session: Session) -> shell.Body:
    """The application's body for a loaded session: side column, tabs, status, chooser dialog.

    This is what the hub mounts; :func:`create_app` wraps the same body in a
    template of its own.
    """
    dataview = DataView(session)
    specimen = SpecimenView(session)
    means = MeansView(session)
    poles = PolesView(session)
    interps = InterpretationsView(session)
    export = ExportView(session)

    # analysis order: interpret specimens, review every fit, then means, poles, export
    tabs = pn.Tabs(("Specimen", specimen.main()), ("Fits", interps.panel()), ("Means", means.panel()),
                   ("Poles", poles.panel()), ("Export", export.panel()), dynamic=True, stylesheets=[TABS_CSS])
    lazy = {1: interps, 2: means, 3: poles}
    for i, view in lazy.items():
        view.set_active(i == tabs.active)

    # the side column follows the active tab: specimen steps, or what is plotted —
    # the fits the table lists on Fits, the plotted fits on Means, the VGPs on Poles.
    # Only Export uses the full width (it writes tables, it plots nothing)
    side_panels = {0: specimen.sidebar(), 1: interps.sidebar(), 2: means.sidebar(), 3: poles.sidebar()}
    side_holder = pn.Column(side_panels[0], sizing_mode="stretch_width")
    full_width_tabs = {4}

    # the hotkeys listener lives beside the tabs, never in a side panel: the side
    # column is swapped per tab, and a component that is off the page cannot report
    main = pn.Column(specimen.hotkeys, tabs, margin=0, sizing_mode="stretch_both")
    body = shell.Body(info=APP, main=main, side=pn.Column(dataview.sidebar(), side_holder, sizing_mode="stretch_width"),
                      header=shell.status_line(session), modal=dataview.modal())

    def _on_tab(event):
        for i, view in lazy.items():
            view.set_active(i == event.new)
        # ↑ ↓ move the selection of the table on show: steps on the Specimen tab, fits on Means
        specimen.arrow_target = means if event.new == 2 else specimen
        show = event.new not in full_width_tabs
        body.show_side(show)
        if show:
            side_holder[:] = [side_panels.get(event.new, side_panels[0])]
    tabs.param.watch(_on_tab, "active")

    def _goto_specimen():
        tabs.active = 0
    means.on_goto = _goto_specimen

    dataview.change_btn.on_click(lambda e: body.open_modal())
    dataview.on_loaded = lambda: body.close_modal()
    return body


def create_app(directory: str, output_dir: str | None = None):
    """Build the page for a MagIC directory. Returns a servable Panel template."""
    session = Session(directory, output_dir, cache=True)
    if session.data is None:
        return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")
    template = shell.template(build_body(session), logo=LOGO, hub_url=runtime.hub_url())
    template.session = session   # handy for tests
    return template


def serve_default():
    """The page for the directory this session asked for: ``?dir=``, then the environment, then McMurdo."""
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    # PMAGPY_DIRECTIONS_OUTPUT is a base: every dataset gets <base>/<dataset>/ (default_output_dir),
    # the first one included
    return create_app(session_directory(os.path.join(repo, "data_files", "3_0", "McMurdo")))
