"""
The page around an application: body and template, kept apart.

Every PmagPy application is the same page — a header with the logo, the name
and a status line; a side column of controls; a drag handle; a main pane; and
a modal for opening a different dataset. What differs is the *body*: which
side column, which main pane, which status. An application builds a
:class:`Body`; this module wraps it.

Two hosts wrap bodies. :func:`template` makes the application a page of its
own, which is how ``programs/<app>/<app>.py`` serves it and how it has always
run. The hub (``pmagpy_apps``) instead keeps one template and *mounts* a body
into it when the analyst opens that application, so the family is one page and
the dataset is read once. Nothing in an application knows which host it has.

Sizes and the heights that let the two panes scroll independently used to be
copied between the applications' ``app.py`` files; they live here now.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Union

import panel as pn

from . import AppInfo, text_on
from .theme import ACCENT, RAW_CSS, asset_data_uri
from .widgets import Splitter

SIDE_WIDTH = 450       # default width of the side column
HANDLE_WIDTH = 14      # the drag handle between the side column and the main pane
HEADER_HEIGHT = 52     # the template's header, which the panes sit under
STATUS_STYLE = "color:inherit;opacity:.88;font-size:0.85rem"   # follows the header's text colour


def setup(*extensions: str) -> None:
    """Load the Panel extensions the family uses; call once at the top of an ``app.py``.

    ``tabulator`` is always loaded (every application has tables); an application
    adds what else it needs. Calling it again is harmless.
    """
    pn.extension("tabulator", *extensions, sizing_mode="stretch_width", raw_css=[RAW_CSS])


def _nothing() -> None:
    pass


@dataclass
class Body:
    """What an application contributes to a page.

    Args:
        info: the application's identity (name in the header, id on files).
        main: the main pane — usually the application's tabs.
        side: the side column; None when the application has none.
        header: the status line shown in the header; see :func:`status_line`.
        modal: the dialog content (the dataset chooser); the host shows it.
        side_width: the side column's starting width; the analyst drags it from there.
        open_modal, close_modal, show_side: how the body asks its host to show
            or hide the modal, and to hide the side column for a tab that plots
            nothing. The host fills these in when it wraps or mounts the body,
            so wire buttons through the body (``body.open_modal()``), not
            through a template the body cannot see.
    """

    info: AppInfo
    main: pn.viewable.Viewable
    side: Optional[pn.viewable.Viewable] = None
    header: Optional[pn.viewable.Viewable] = None
    modal: Optional[pn.viewable.Viewable] = None
    side_width: int = SIDE_WIDTH
    open_modal: Callable[[], None] = field(default=_nothing, repr=False)
    close_modal: Callable[[], None] = field(default=_nothing, repr=False)
    show_side: Callable[[bool], None] = field(default=lambda show: None, repr=False)


def status_line(session, text: Optional[Callable[[], str]] = None) -> pn.pane.HTML:
    """The header's status line, following ``session.status``.

    Args:
        text: what to show; defaults to the session's ``status`` string. An
            application that appends counts passes its own callable and watches
            whatever else should refresh it.
    """
    pane = pn.pane.HTML("", sizing_mode="stretch_width")
    text = text or (lambda: session.status)

    def refresh(event=None):
        pane.object = (f'<div style="display:flex;gap:18px;align-items:baseline;padding-top:2px">'
                       f'<span style="{STATUS_STYLE}">{text()}</span></div>')
    session.param.watch(refresh, "status")
    refresh()
    pane.refresh = refresh          # for callers that watch more than `status`
    return pane


class SidePanels:
    """The side column's content, one panel per tab, following the tab on show.

    A panel goes into the page the first time its tab is shown and stays
    there; after that a switch only changes which panel is visible. Replacing
    the column's content instead, on every switch, makes the server rebuild
    the panel's models and send them again, plots and all: 430 kB and a fifth
    of a second for the Directions *Fits* panel, whose net holds every fit in
    the study, each time that tab was opened.

    Args:
        panels: the panel for each tab, by tab index.
        default: the tab whose panel is shown first, and for a tab with none.
    """

    def __init__(self, panels: dict, default: int = 0):
        self.panels = panels
        self.default = default
        self.column = pn.Column(panels[default], sizing_mode="stretch_width")

    def show(self, index: int) -> None:
        """Show the panel of tab ``index`` (the default's, if it has none) and hide the rest."""
        panel = self.panels.get(index, self.panels[self.default])
        with pn.io.hold():
            if not any(p is panel for p in self.column.objects):
                self.column.append(panel)
            for p in self.column.objects:
                p.visible = p is panel


def lazy_tabs(*items, **params) -> pn.Tabs:
    """Tabs whose content goes into the page the first time a tab is shown, and stays there.

    Panel's ``dynamic=True`` keeps only the tab on show in the page, so every
    switch rebuilds the tab's models on the server, sends them again and has
    the browser construct them afresh: 100 to 300 kB and a few hundred
    milliseconds for each of the Directions tabs. Keeping every tab in the page
    from the start makes the first page slower instead. Here a tab holds an
    empty placeholder until it is first opened; its content then replaces the
    placeholder, once, and later switches are the browser's alone.

    The content is added before the application's own watchers on ``active``
    run (it is registered first), so the tab appears at once even when a view
    computes for seconds when first shown (Intensity's group results take
    seven): the layout arrives, then its numbers.

    Args:
        items: ``(title, content)`` pairs, as for ``pn.Tabs``.
        params: passed to ``pn.Tabs`` (``dynamic`` is always False).
    """
    items = list(items)
    params["dynamic"] = False
    active = params.get("active", 0)
    tabs = pn.Tabs(*[(title, content if i == active else pn.Column(margin=0))
                     for i, (title, content) in enumerate(items)], **params)
    shown = {active}

    def _add(event):
        i = event.new
        if i is not None and 0 <= i < len(items) and i not in shown:
            shown.add(i)
            tabs[i] = items[i]
    tabs.param.watch(_add, "active")
    return tabs


class Workspace:
    """A body laid out: side column, drag handle, main pane.

    The side column and the main pane scroll independently; the splitter
    resizes both in the browser, and the widths it writes survive the
    re-renders of a tab switch, so a drag needs no round trip to the server.
    ``show_side(False)`` hides the column and the handle together — a tab that
    plots nothing takes the full width.
    """

    def __init__(self, body: Body, handle_width: int = HANDLE_WIDTH):
        self.body = body
        width = body.side_width
        self.side_area = None
        if body.side is not None:
            side = pn.Column(body.side, width=width, sizing_mode="stretch_height",
                             styles={"overflow-y": "auto", "overflow-x": "hidden",
                                     "max-height": f"calc(100vh - {HEADER_HEIGHT}px)",
                                     "padding-right": "6px"})
            splitter = Splitter(width=handle_width, sizing_mode="stretch_height", panel_default=width)
            # one container: the custom splitter ignores `visible` on its own
            self.side_area = pn.Row(side, splitter, width=width + handle_width,
                                    sizing_mode="stretch_height", margin=0)
        # min-width 0 overrides the flex default (min-width: auto, i.e. never narrower than
        # the widest row): without it the pane cannot give width back when the side column
        # is dragged wider, and it would grow over the column instead. The left padding
        # keeps text set flush left clear of the drag handle
        self.main_area = pn.Column(body.main, sizing_mode="stretch_both",
                                   styles={"overflow-y": "auto", "overflow-x": "auto", "min-width": "0",
                                           "max-height": f"calc(100vh - {HEADER_HEIGHT + 8}px)",
                                           "padding-left": "8px" if self.side_area is not None else "0"})
        parts = [self.side_area, self.main_area] if self.side_area is not None else [self.main_area]
        self.layout = pn.Row(*parts, sizing_mode="stretch_both")
        body.show_side = self.show_side

    def show_side(self, show: bool) -> None:
        if self.side_area is not None:
            self.side_area.visible = show


def back_link(hub_url: str) -> pn.pane.HTML:
    """The header's way back to the hub, for an application served under one.

    The link carries the page's query string (``?dir=<the open directory>``,
    which the chooser keeps current) so the hub comes back to that directory's
    page rather than to the start page; with nothing open it is the plain hub.
    """
    return pn.pane.HTML(
        f'<a href="{hub_url}" onclick="this.href=\'{hub_url}\' + (window.location.search || \'\')" '
        f'style="{STATUS_STYLE};text-decoration:none;white-space:nowrap;'
        f'padding-right:14px;border-right:1px solid currentColor;margin-right:4px">'
        f'&larr; PmagPy Apps</a>', margin=(0, 0, 0, 0))


def asset_url(info: AppInfo, name: str) -> str:
    """The URL of a file in the application's ``assets/`` directory, as the launcher serves it.

    The launcher mounts each application's assets at ``/<app_id>_assets`` so that
    several applications on one port do not share one ``/assets``. Under a bare
    ``panel serve`` nothing is mounted and the file is simply not found.
    """
    return f"/{info.app_id}_assets/{name}"


def template(body: Body, logo: str, hub_url: str = "") -> pn.template.FastListTemplate:
    """Make a body a page of its own.

    Args:
        body: what the application built.
        logo: path to the application's own logo (assets belong to an
            application, not to the toolkit); it is embedded in the page. The
            favicon cannot be — Panel wants a URL with a file suffix — so it is
            ``assets/favicon.png`` through :func:`asset_url`.
        hub_url: where the hub is when this application is served under one;
            adds the way back to the header. Empty when it runs alone.

    The header is painted ``body.info.color`` — each application's own, the
    same as its door on the hub — with white or dark text as that colour
    needs; buttons keep the family accent so they look alike everywhere.
    Returns:
        the template, with ``workspace`` (the :class:`Workspace`) and ``body``
        set on it for the application and its tests.
    """
    workspace = Workspace(body)
    header = []
    if hub_url:
        header.append(back_link(hub_url))
    if body.header is not None:
        header.append(body.header)
    tmpl = pn.template.FastListTemplate(
        title=body.info.name, logo=asset_data_uri(logo), favicon=asset_url(body.info, "favicon.png"),
        main=[workspace.layout], header=header, theme_toggle=False,
        header_background=body.info.color, header_color=text_on(body.info.color),   # the application's colour
        accent_base_color=ACCENT,                                                   # buttons stay the family's
        collapsed_sidebar=True, main_max_width="100%", raw_css=[RAW_CSS],
    )
    if body.modal is not None:
        tmpl.modal.append(body.modal)
        body.open_modal = tmpl.open_modal
        body.close_modal = tmpl.close_modal
    tmpl.workspace = workspace
    tmpl.body = body
    return tmpl


def deferred_template(info: AppInfo, logo: str, build: Callable[[], Union[Body, pn.viewable.Viewable]],
                      hub_url: str = "", loading: str = "Loading …",
                      side_width: int = SIDE_WIDTH) -> pn.template.FastListTemplate:
    """A page that shows at once and fills in when its body has been built.

    Reading a study takes seconds; a browser tab that stays blank for those
    seconds looks broken. This serves the header, the application's colour and
    a loading line immediately, runs `build` once the page has rendered
    (``pn.state.onload``) and mounts what it returns — the side column, main
    pane, status line and modal of a :class:`Body`, or a plain viewable (an
    error message) in the main pane. Outside a served session `build` runs at
    once, so a test sees the finished page.

    Args:
        side_width: the side column's starting width, as the application's own
            :class:`Body` would set it.

    Returns:
        the template, with ``body`` (the built :class:`Body`, or None until it
        is built) and ``workspace`` set on it.
    """
    side_holder = pn.Column(sizing_mode="stretch_width")
    main_holder = pn.Column(sizing_mode="stretch_both", loading=True, min_height=300)
    header_holder = pn.Row(pn.pane.HTML(f'<span style="{STATUS_STYLE}">{loading}</span>', margin=(0, 0, 0, 0)),
                           sizing_mode="stretch_width")
    modal_holder = pn.Column()
    frame = Body(info=info, main=main_holder, side=side_holder, header=header_holder, modal=modal_holder,
                 side_width=side_width)
    tmpl = template(frame, logo=logo, hub_url=hub_url)
    tmpl.body = None

    def fill():
        try:
            built = build()
        except Exception as exc:                          # the page must never stay blank
            built = pn.pane.Markdown(f"## {info.name} could not open this dataset\n\n`{exc}`")
        main_holder.loading = False
        if not isinstance(built, Body):
            header_holder[:] = []
            main_holder[:] = [built]
            tmpl.workspace.show_side(False)
            return
        if built.side is not None:
            side_holder[:] = [built.side]
        else:
            tmpl.workspace.show_side(False)
        main_holder[:] = [built.main]
        header_holder[:] = [built.header] if built.header is not None else []
        modal_holder[:] = [built.modal] if built.modal is not None else []
        built.open_modal, built.close_modal = tmpl.open_modal, tmpl.close_modal
        built.show_side = tmpl.workspace.show_side
        tmpl.body = built
    pn.state.onload(fill)
    return tmpl
