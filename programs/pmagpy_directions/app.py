"""Assemble the PmagPy Directions application."""
from __future__ import annotations

import os

import panel as pn

from pmagpy_panel import datasets, runtime, shell
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
    # the tabs that are not on show draw nothing until they are opened: the page is
    # ready when the Specimen tab is, not after every mean in the study is computed
    means = MeansView(session, active=False)
    poles = PolesView(session, active=False)
    interps = InterpretationsView(session, active=False)
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
    side = shell.SidePanels({0: specimen.sidebar(), 1: interps.sidebar(), 2: means.sidebar(), 3: poles.sidebar()})
    full_width_tabs = {4}

    # the hotkeys listener lives beside the tabs, never in a side panel: the side
    # column is swapped per tab, and a component that is off the page cannot report
    main = pn.Column(specimen.hotkeys, tabs, margin=0, sizing_mode="stretch_both")
    body = shell.Body(info=APP, main=main, side=pn.Column(dataview.sidebar(), side.column, sizing_mode="stretch_width"),
                      header=shell.status_line(session), modal=dataview.modal())

    def _on_tab(event):
        for i, view in lazy.items():
            view.set_active(i == event.new)
        # ↑ ↓ move the selection of the table on show: steps on the Specimen tab, fits on Means
        specimen.arrow_target = means if event.new == 2 else specimen
        show = event.new not in full_width_tabs
        body.show_side(show)
        if show:
            side.show(event.new)
    tabs.param.watch(_on_tab, "active")

    def _goto_specimen():
        tabs.active = 0
    means.on_goto = _goto_specimen

    dataview.change_btn.on_click(lambda e: body.open_modal())
    dataview.on_loaded = lambda: body.close_modal()
    dataview.busy = main             # a spinner over the plots while the next dataset is read
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
    """The page for the directory this session asked for: ``?dir=``, then the environment, then McMurdo.

    The page is served at once with a loading line and fills in when the dataset
    has been read (:func:`pmagpy_panel.shell.deferred_template`): a study of a
    thousand specimens takes a second or two, and the analyst sees the header
    and the spinner instead of a blank tab. ``session`` is set on the template
    once the body is built (immediately outside a served session).
    """
    # PMAGPY_DIRECTIONS_OUTPUT is a base: every dataset gets <base>/<dataset>/ (default_output_dir),
    # the first one included. The example is found wherever this copy of PmagPy keeps
    # its data files — a checkout, a wheel's sys.prefix, or the packaged build's bundle
    directory = session_directory(datasets.example_dir("McMurdo"))
    name = os.path.basename(directory.rstrip("/")) or directory
    holder = {}

    def build():
        session = Session(directory, None, cache=True)
        holder["session"] = session
        if session.data is None:
            return pn.pane.Markdown(f"## Could not load `{directory}`\n\n{session.status}")
        return build_body(session)
    template = shell.deferred_template(APP, LOGO, build, hub_url=runtime.hub_url(), loading=f"Loading {name} …")
    template.session = holder.get("session")
    return template
