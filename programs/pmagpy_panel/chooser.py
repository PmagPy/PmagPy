"""
Choosing which MagIC directory an application is looking at.

Both applications need the same thing: a compact block in the side column
saying which dataset is open, and a dialog for opening a different one — the
system folder chooser, a list of recently opened directories, a path field, and
an in-page browser for sessions served from another machine. The behaviour is
in :mod:`pmagpy_panel.datasets`; the widgets are here, so that the two
applications cannot drift apart in how a dataset is opened.

An application composes it: :meth:`DirectoryChooser.sidebar` goes at the top of
the side column, :meth:`DirectoryChooser.modal` is the dialog, and anything
subject-specific (PmagPy Intensity adds a ThellierTool importer) is appended by
the application to the column the chooser returns.

The session it is given only has to answer ``directory``, ``output_dir``,
``status`` and ``load(path)``; both applications' sessions do.
"""
from __future__ import annotations

import os
import sys
import threading
from typing import Callable, Optional

import panel as pn

from . import datasets
from .theme import MUTED_STYLE, SECTION_STYLE, kpi

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"


def shorten(path: str, width: int = 52) -> str:
    """A path short enough for a side column, keeping the end that identifies it."""
    return path if len(path) <= width else "…" + path[-(width - 1):]


class DirectoryChooser:
    """The dataset block and the "open a different one" dialog.

    Args:
        session: the application's session; needs ``directory``, ``output_dir``,
            ``status`` and ``load(path)``.
        recent_file: where this application remembers its recent directories.
        chooser: the system folder dialog; injected so tests can answer it.
        chooser_available: whether a system dialog can be shown at all.
        count: called with the session to describe what is loaded
            ("590 specimens"); each application counts its own thing.
        note: a sentence under the dialog's heading.
    """

    def __init__(self, session, recent_file: str,
                 chooser: Optional[Callable] = None,
                 chooser_available: Optional[bool] = None,
                 count: Optional[Callable] = None,
                 note: str = ""):
        self.s = session
        self.recent_file = recent_file
        self.on_loaded = None                 # set by the app: closes the modal
        self.chooser = chooser or datasets.native_choose_directory
        self.chooser_available = (datasets.native_chooser_available()
                                  if chooser_available is None else chooser_available)
        self._count = count or (lambda s: "")
        self.note = note

        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.change_btn = pn.widgets.Button(name="Change data…", button_type="primary", width=140)
        app = {"darwin": "Finder", "win32": "Explorer"}.get(sys.platform, "the system dialog")
        self.native_btn = pn.widgets.Button(name=f"Browse with {app}…", button_type="primary",
                                            width=220, disabled=not self.chooser_available)
        self.recent = pn.widgets.Select(name="Recent directories", options=[], size=6,
                                        sizing_mode="stretch_width")
        self.path = pn.widgets.TextInput(
            name="MagIC directory (must contain measurements.txt)",
            value=getattr(session, "directory", ""), sizing_mode="stretch_width")
        self.browser = pn.widgets.FileSelector(
            directory=os.path.dirname(getattr(session, "directory", "") or "") or os.getcwd(),
            only_files=False, show_hidden=False, height=240,
            name="select a directory, then Load")
        self.load_btn = pn.widgets.Button(name="Load", button_type="success", width=120)
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")

        self.native_btn.on_click(self._browse_native)
        self.recent.param.watch(lambda e: setattr(self.path, "value", e.new) if e.new else None,
                                "value")
        self.browser.param.watch(self._on_browse, "value")
        self.load_btn.on_click(self._load)
        session.param.watch(lambda e: self.refresh(), ["directory", "output_dir"])
        self.refresh()

    # ----- state ------------------------------------------------------------
    def refresh(self) -> None:
        directory = getattr(self.s, "directory", "") or ""
        name = os.path.basename(directory.rstrip("/")) or "(none)"
        self.summary.object = kpi([
            f"<b>{name}</b>",
            f'<span style="{MUTED_STYLE}">{self._count(self.s)}</span>',
            f'<span style="{MUTED_STYLE}" title="{directory}">{shorten(directory)}</span>'])
        self.recent.options = {shorten(d, 70): d for d in datasets.load_recent(self.recent_file)}
        self.path.value = directory

    # ----- events -----------------------------------------------------------
    def _on_browse(self, event) -> None:
        if not event.new:
            return
        chosen = event.new[0]
        self.path.value = chosen if os.path.isdir(chosen) else os.path.dirname(chosen)

    def _browse_native(self, event=None) -> None:
        """Run the system folder dialog off the server thread, then load the choice."""
        self.native_btn.disabled = True
        self.message.object = (f'<div style="{MUTED_STYLE}">Choose a folder in the dialog that '
                               f'just opened …</div>')
        start = self.path.value.strip() or getattr(self.s, "directory", "")
        # the document must be captured here: pn.state.curdoc is not visible from
        # the worker thread, and model updates without the document lock are lost
        # or half-applied
        doc = pn.state.curdoc

        def worker():
            chosen = self.chooser(start)

            def apply():
                self.native_btn.disabled = not self.chooser_available
                if chosen:
                    self.path.value = chosen
                    self._load()
                else:
                    self.message.object = f'<div style="{MUTED_STYLE}">No folder chosen.</div>'
            if doc is not None and getattr(doc, "session_context", None) is not None:
                doc.add_next_tick_callback(apply)
            else:
                apply()
        threading.Thread(target=worker, daemon=True).start()

    def _load(self, event=None) -> bool:
        target = os.path.expanduser(self.path.value.strip())
        if not target:
            return False
        if not datasets.looks_like_magic_dir(target):
            self.message.object = (f'<div style="color:{FAIL_COLOR}">No <code>measurements.txt</code>'
                                   f' in <code>{target}</code></div>')
            return False
        self.message.object = f'<div style="{MUTED_STYLE}">Loading {target} …</div>'
        if self.s.load(target):
            self.message.object = f'<div style="color:{OK_COLOR}">{self.s.status}</div>'
            if self.on_loaded:
                self.on_loaded()
            return True
        self.message.object = f'<div style="color:{FAIL_COLOR}">{self.s.status}</div>'
        return False

    # ----- layout -----------------------------------------------------------
    def sidebar(self) -> pn.Column:
        return pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Data</div>'),
                         self.summary, self.change_btn, sizing_mode="stretch_width")

    def modal(self, *extra, width: int = 760) -> pn.Column:
        """The dialog, with anything the application wants to add underneath."""
        fallback = pn.Card(self.browser, collapsed=True, sizing_mode="stretch_width",
                           title="In-page browser (for sessions served from another machine)")
        block = pn.Column(
            pn.pane.HTML('<h3 style="margin:0 0 6px 0">Open a MagIC directory</h3>'
                         + (f'<div style="{MUTED_STYLE}">{self.note}</div>' if self.note else "")),
            pn.Row(self.native_btn, self.message),
            self.recent, pn.Row(self.path, self.load_btn), fallback,
            sizing_mode="stretch_width")
        if not extra:
            return pn.Column(block, width=width)
        return pn.Column(block, pn.layout.Divider(), *extra, width=width,
                         sizing_mode="stretch_height")
