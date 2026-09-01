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
from typing import Callable, Optional

import panel as pn

from . import AppInfo
from .theme import ACCENT, RAW_CSS, asset_data_uri
from .widgets import Splitter

SIDE_WIDTH = 450       # default width of the side column
HANDLE_WIDTH = 14      # the drag handle between the side column and the main pane
HEADER_HEIGHT = 52     # the template's header, which the panes sit under
STATUS_STYLE = "color:#e5e7eb;font-size:0.85rem"


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
    """The header's way back to the hub, for an application served under one."""
    return pn.pane.HTML(
        f'<a href="{hub_url}" style="{STATUS_STYLE};text-decoration:none;white-space:nowrap;'
        f'padding-right:14px;border-right:1px solid rgba(255,255,255,.35);margin-right:4px">'
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
        main=[workspace.layout], header=header, accent=ACCENT, theme_toggle=False,
        collapsed_sidebar=True, main_max_width="100%", raw_css=[RAW_CSS],
    )
    if body.modal is not None:
        tmpl.modal.append(body.modal)
        body.open_modal = tmpl.open_modal
        body.close_modal = tmpl.close_modal
    tmpl.workspace = workspace
    tmpl.body = body
    return tmpl
