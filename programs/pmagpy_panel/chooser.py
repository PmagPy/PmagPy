"""
Choosing which directory an application is looking at.

Every PmagPy application needs the same thing: a compact block saying which
dataset is open, and a dialog for opening a different one — the system folder
chooser, the recently opened directories, a path field, and an in-page browser
for sessions served from another machine. The behaviour is in
:mod:`pmagpy_panel.datasets` and :mod:`pmagpy_panel.runtime`; the widgets are
here, so that the applications cannot drift apart in how a dataset is opened.

An application composes it: :meth:`DirectoryChooser.sidebar` goes at the top
of the side column, :meth:`DirectoryChooser.modal` is the dialog, and anything
subject-specific (an importer for another program's files, say) is appended by
the application to the column the chooser returns. The hub uses the dialog
alone, with ``require_measurements=False``: Home is where a directory with
nothing in it yet starts its life.

The session it is given only has to answer ``directory``, ``status`` and
``load(path) -> bool``; ``output_dir`` is watched when the session has one.
A session that re-reads the same directory (after a save, say) triggers
``directory`` to have the chooser's counts follow.

This began as Yiming Zhang's ``chooser.py`` on the intensity branch; the
system dialog now runs as a coroutine (:func:`pmagpy_panel.runtime.choose_directory`)
rather than on a worker thread, so the server keeps serving while it is open.
"""
from __future__ import annotations

import os
import sys
from typing import Callable, Optional
from urllib.parse import quote

import panel as pn

from . import datasets, runtime
from .theme import MUTED_STYLE, SECTION_STYLE, kpi

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"


def shorten(path: str, width: int = 52) -> str:
    """A path short enough for a side column, keeping the end that identifies it."""
    return path if len(path) <= width else "…" + path[-(width - 1):]


class DirectoryChooser:
    """The dataset block and the "open a different one" dialog.

    Args:
        session: the application's session; needs ``directory``, ``status`` and
            ``load(path) -> bool``.
        recent_file: where the recent directories are remembered — normally
            :func:`datasets.shared_recent_file`, so every application offers
            the same list.
        chooser: a replacement for the system folder dialog, ``(start) -> path
            or None``; tests inject one. By default the dialog is
            :func:`runtime.choose_directory`, answered by `chooser_stub` when
            that is set (the applications read it from their environment).
        chooser_available: whether a system dialog can be shown at all;
            decided from the platform when not given.
        count: called with the session to describe what is loaded ("590
            specimens"); each application counts its own thing.
        title: the dialog's heading.
        note: a sentence under the heading.
        require_measurements: refuse a directory without ``measurements.txt``
            before the session sees it. The analysis applications want this;
            the hub does not.
        update_url: put ``?dir=<directory>`` on the browser's URL after a load,
            so a reload or a bookmark comes back to the same dataset.
    """

    def __init__(self, session, recent_file: str,
                 chooser: Optional[Callable] = None,
                 chooser_available: Optional[bool] = None,
                 chooser_stub: str = "",
                 count: Optional[Callable] = None,
                 title: str = "Open a MagIC directory",
                 note: str = "",
                 require_measurements: bool = True,
                 update_url: bool = True):
        self.s = session
        self.recent_file = recent_file
        self.on_loaded: Optional[Callable[[], None]] = None     # set by the app: closes the modal
        self.chooser = chooser
        self.chooser_stub = chooser_stub
        self.chooser_available = (runtime.native_chooser_available(stub=chooser_stub)
                                  if chooser_available is None else chooser_available)
        self._count = count or (lambda s: "")
        self.title = title
        self.note = note
        self.require_measurements = require_measurements
        self.update_url = update_url

        directory = getattr(session, "directory", "") or ""
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.change_btn = pn.widgets.Button(name="Change data…", button_type="primary", width=140)
        app = {"darwin": "Finder", "win32": "Explorer"}.get(sys.platform, "the system dialog")
        self.native_btn = pn.widgets.Button(name=f"Browse with {app}…", button_type="primary",
                                            width=220, disabled=not self.chooser_available)
        self.recent = pn.widgets.Select(name="Recent directories", options=[], size=6,
                                        sizing_mode="stretch_width", stylesheets=["select { max-width: 100%; }"])
        label = "MagIC directory (must contain measurements.txt)" if require_measurements else "Directory"
        self.path = pn.widgets.TextInput(name=label, value=directory, sizing_mode="stretch_width")
        self.browser = pn.widgets.FileSelector(
            directory=os.path.dirname(directory) or os.getcwd(),
            only_files=False, show_hidden=False, height=240,
            name="select a directory, then Open")
        self.load_btn = pn.widgets.Button(name="Open", button_type="success", width=120)
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")

        self.native_btn.on_click(self._browse_native)
        self.recent.param.watch(lambda e: setattr(self.path, "value", e.new) if e.new else None, "value")
        self.browser.param.watch(self._on_browse, "value")
        self.load_btn.on_click(self.load)
        watched = [p for p in ("directory", "output_dir") if p in session.param]
        session.param.watch(lambda *events: self.refresh(), watched)
        self.refresh()

    # ----- state ------------------------------------------------------------
    def recent_directories(self) -> list:
        """The remembered directories that still exist, most recent first."""
        return [d for d in datasets.load_recent(self.recent_file) if os.path.isdir(d)]

    def refresh(self) -> None:
        directory = getattr(self.s, "directory", "") or ""
        name = os.path.basename(directory.rstrip("/")) or "(none)"
        self.summary.object = kpi([
            f"<b>{name}</b>",
            f'<span style="{MUTED_STYLE}">{self._count(self.s)}</span>',
            f'<span style="{MUTED_STYLE}" title="{directory}">{shorten(directory)}</span>'])
        self.recent.options = {shorten(d, 70): d for d in self.recent_directories()}
        self.path.value = directory

    # ----- events -----------------------------------------------------------
    def _on_browse(self, event) -> None:
        if not event.new:
            return
        chosen = event.new[0]
        self.path.value = chosen if os.path.isdir(chosen) else os.path.dirname(chosen)

    async def _browse_native(self, event=None) -> None:
        """Show the system folder dialog, then open what it returns."""
        self.native_btn.disabled = True
        self.message.object = f'<div style="{MUTED_STYLE}">Choose a folder in the dialog that just opened …</div>'
        start = os.path.expanduser(self.path.value.strip()) or getattr(self.s, "directory", "")
        try:
            if self.chooser is not None:
                chosen = self.chooser(start)
            else:
                chosen = await runtime.choose_directory(start, prompt="Choose a directory", stub=self.chooser_stub)
        finally:
            self.native_btn.disabled = not self.chooser_available
        if chosen:
            self.path.value = chosen
            self.load()
        else:
            self.message.object = f'<div style="{MUTED_STYLE}">No folder chosen.</div>'

    def load(self, event=None) -> bool:
        """Open the directory in the path field. False, with the reason shown, when it cannot."""
        text = self.path.value.strip()
        if not text:
            return False
        target = os.path.abspath(os.path.expanduser(text))
        if not os.path.isdir(target):
            self.message.object = f'<div style="color:{FAIL_COLOR}"><code>{target}</code> is not a directory</div>'
            return False
        if self.require_measurements and not datasets.looks_like_magic_dir(target):
            self.message.object = (f'<div style="color:{FAIL_COLOR}">No <code>measurements.txt</code>'
                                   f' in <code>{target}</code></div>')
            return False
        self.message.object = f'<div style="{MUTED_STYLE}">Loading {target} …</div>'
        if not self.s.load(target):
            self.message.object = f'<div style="color:{FAIL_COLOR}">{self.s.status}</div>'
            return False
        self.message.object = f'<div style="color:{OK_COLOR}">{self.s.status}</div>'
        if self.update_url:
            location = runtime.location()
            if location is not None:
                location.search = f"?dir={quote(target)}"
        if self.on_loaded:
            self.on_loaded()
        return True

    _load = load          # the name the intensity branch's callers use

    # ----- layout -----------------------------------------------------------
    def sidebar(self) -> pn.Column:
        return pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Data</div>'),
                         pn.Row(self.summary, self.change_btn), sizing_mode="stretch_width")

    @staticmethod
    def heading_html(title: str, note: str = "") -> str:
        """The dialog's heading — a host that opens the chooser for more than one purpose sets a new one."""
        return f'<h3 style="margin:0 0 6px 0">{title}</h3>' + (f'<div style="{MUTED_STYLE}">{note}</div>' if note else "")

    def modal(self, *extra, width: int = 760) -> pn.Column:
        """The dialog, with anything the application wants to add underneath; ``[0][0]`` is the heading pane."""
        fallback = pn.Card(self.browser, collapsed=True, sizing_mode="stretch_width",
                           title="In-page browser (for sessions served from another machine)")
        block = pn.Column(
            pn.pane.HTML(self.heading_html(self.title, self.note)),
            pn.Row(self.native_btn, self.message),
            self.recent, pn.Row(self.path, self.load_btn), fallback,
            sizing_mode="stretch_width")
        if not extra:
            return pn.Column(block, width=width)
        return pn.Column(block, pn.layout.Divider(), *extra, width=width, sizing_mode="stretch_height")
