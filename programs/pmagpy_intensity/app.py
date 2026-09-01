"""Assemble the PmagPy Intensity application."""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel.widgets import Splitter
from pmagpy_panel.theme import ACCENT, RAW_CSS, TABS_CSS, asset_data_uri
from . import APP_NAME
from .session import Session, env
from .views import (BicepView, CorrectionsView, CriteriaView, DataView, ExportView, GroupView,
                    InterpretationsView, SpecimenView)

pn.extension("tabulator", sizing_mode="stretch_width", raw_css=[RAW_CSS])

SIDE_WIDTH = 460      # default width of the side column
HANDLE_WIDTH = 14     # the drag handle between the side column and the main pane
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def create_app(directory: str, output_dir: str | None = None):
    """Build the template for a MagIC directory. Returns a servable Panel template."""
    session = Session(directory, output_dir, cache=True)
    if session.data is None:
        return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")

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

    def _on_tab(event):
        for index, view in lazy.items():
            view.set_active(index == event.new)
        show = event.new not in full_width_tabs
        side_area.visible = show
        if show:
            side_holder[:] = [side_panels.get(event.new, side_panels[0])]
    tabs.param.watch(_on_tab, "active")

    def _goto_specimen():
        tabs.active = 0
    interps.on_goto = _goto_specimen

    status = pn.pane.HTML("", sizing_mode="stretch_width")

    def _status(event=None):
        summary = session.study_summary()
        extra = ""
        if summary:
            extra = (f' · {summary["interpreted"]} interpreted · {summary["accepted"]} accepted'
                     f' · {summary["sites"]} sites')
        status.object = (f'<div style="display:flex;gap:18px;align-items:baseline;padding-top:2px">'
                         f'<span style="color:#e5e7eb;font-size:0.85rem">{session.status}'
                         f'{extra}</span></div>')
    session.param.watch(_status, ["status", "version"])
    _status()

    side = pn.Column(dataview.sidebar(), side_holder, width=SIDE_WIDTH,
                     sizing_mode="stretch_height",
                     styles={"overflow-y": "auto", "overflow-x": "hidden",
                             "max-height": "calc(100vh - 52px)", "padding-right": "6px"})
    splitter = Splitter(width=HANDLE_WIDTH, sizing_mode="stretch_height",
                        panel_default=SIDE_WIDTH)
    side_area = pn.Row(side, splitter, width=SIDE_WIDTH + HANDLE_WIDTH,
                       sizing_mode="stretch_height", margin=0)
    main_area = pn.Column(tabs, sizing_mode="stretch_both",
                          styles={"overflow-y": "auto", "overflow-x": "auto",
                                  "min-width": "0", "max-height": "calc(100vh - 60px)",
                                  "padding-left": "8px"})
    body = pn.Row(side_area, main_area, sizing_mode="stretch_both")
    template = pn.template.FastListTemplate(
        title=APP_NAME, logo=asset_data_uri(os.path.join(ASSETS, "pmagpy_logo_white.png")),
        favicon="assets/favicon.png",                # served via --static-dirs (see launch.py)
        main=[body], header=[status], accent=ACCENT, theme_toggle=False, collapsed_sidebar=True,
        main_max_width="100%", raw_css=[RAW_CSS],
    )
    template.modal.append(dataview.modal())
    dataview.change_btn.on_click(lambda e: template.open_modal())
    dataview.on_loaded = template.close_modal
    template.session = session       # handy for tests
    return template


def serve_default():
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    directory = env("DIR", os.path.join(repo, "data_files", "3_0", "Megiddo"))
    return create_app(directory)
