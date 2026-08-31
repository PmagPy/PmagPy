"""Assemble the PmagPy Directions application."""
from __future__ import annotations

import os

import panel as pn

from .logger import Splitter
from . import APP_NAME
from .session import Session, env
from .theme import ACCENT, RAW_CSS, TABS_CSS, asset_data_uri
from .views import DataView, ExportView, InterpretationsView, MeansView, PolesView, SpecimenView

pn.extension("tabulator", sizing_mode="stretch_width", raw_css=[RAW_CSS])


def create_app(directory: str, output_dir: str | None = None):
    """Build the template for a MagIC directory. Returns a servable Panel template."""
    session = Session(directory, output_dir, cache=True)
    if session.data is None:
        return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")

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

    # the side column follows the active tab: specimen steps, or the list of what is
    # plotted; the Fits and Export tabs use the full width (no specimen context needed)
    side_panels = {0: specimen.sidebar(), 2: means.sidebar(), 3: poles.sidebar()}
    side_holder = pn.Column(side_panels[0], sizing_mode="stretch_width")
    full_width_tabs = {1, 4}

    def _on_tab(event):
        for i, view in lazy.items():
            view.set_active(i == event.new)
        show = event.new not in full_width_tabs
        side_area.visible = show               # one container: the custom splitter ignores `visible`
        if show:
            side_holder[:] = [side_panels.get(event.new, side_panels[0])]
    tabs.param.watch(_on_tab, "active")

    def _goto_specimen():
        tabs.active = 0
    means.on_goto = _goto_specimen
    status = pn.pane.HTML("", sizing_mode="stretch_width")

    def _status(event=None):
        status.object = (f'<div style="display:flex;gap:18px;align-items:baseline;padding-top:2px">'
                         f'<span style="color:#e5e7eb;font-size:0.85rem">{session.status}</span></div>')
    session.param.watch(_status, "status")
    _status()

    # side column + drag handle + tabs (the template's collapsible sidebar is not used:
    # analysts want to *resize* the step logger column, not hide it)
    side = pn.Column(dataview.sidebar(), side_holder, width=450, sizing_mode="stretch_height",
                     styles={"overflow-y": "auto", "overflow-x": "hidden", "max-height": "calc(100vh - 52px)",
                             "padding-right": "6px"})
    side_area = pn.Row(side, Splitter(width=14, sizing_mode="stretch_height"), width=464,
                       sizing_mode="stretch_height", margin=0)
    # the main pane scrolls on its own, independently of the side column's scrollbar
    main_area = pn.Column(tabs, sizing_mode="stretch_both",
                          styles={"overflow-y": "auto", "overflow-x": "hidden",
                                  "max-height": "calc(100vh - 60px)"})
    body = pn.Row(side_area, main_area, sizing_mode="stretch_both")
    template = pn.template.FastListTemplate(
        title=APP_NAME, logo=asset_data_uri("pmagpy_logo_white.png"), favicon="assets/favicon.png",   # served via --static-dirs (see launch.py)
        main=[body], header=[status], accent=ACCENT, theme_toggle=False, collapsed_sidebar=True,
        main_max_width="100%", raw_css=[RAW_CSS],
    )
    template.modal.append(dataview.modal())
    dataview.change_btn.on_click(lambda e: template.open_modal())
    dataview.on_loaded = template.close_modal
    template.session = session   # handy for tests
    return template


def serve_default():
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    directory = env("DIR", os.path.join(repo, "data_files", "3_0", "McMurdo"))
    # PMAGPY_DIRECTIONS_OUTPUT is a base: every dataset gets <base>/<dataset>/ (default_output_dir),
    # the first one included
    return create_app(directory)
