"""
The "Download from MagIC…" dialog: a public contribution, by ID or by DOI, into a folder.

This is the first piece of the Import page and the one that needs no files of
the user's own: paste ``20340`` or ``10.1130/G53450.1``, and the contribution's
tables land in the folder named below, which Home then opens. The work —
finding the contribution for a DOI, fetching the file, unpacking it — is
:mod:`pmagpy.magic_project`'s; the dialog only runs it off the event loop
(the server keeps serving while a large contribution comes down) and says what
is happening.

The download never writes into a folder that already holds MagIC tables. When
the folder given does, the dialog says so and offers a new folder named after
the contribution beside it.
"""
from __future__ import annotations

import asyncio
import os
from typing import Callable, Optional
from urllib.parse import quote

import panel as pn

from pmagpy import magic_project as mp
from pmagpy_panel import runtime
from pmagpy_panel.theme import MUTED_STYLE

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"


MAGIC_TABLES = ("contribution", "locations", "sites", "samples", "specimens", "measurements", "ages", "images")


def holds_magic_tables(folder: str) -> bool:
    """True when any MagIC table is already in the folder — a download must not land on top of it."""
    return any(os.path.exists(os.path.join(folder, f"{t}.txt")) for t in MAGIC_TABLES)


def suggested_folder(taken: str, magic_id: int) -> str:
    """A new folder for a contribution, beside one that is already a MagIC directory."""
    return os.path.join(os.path.dirname(taken.rstrip(os.sep)) or taken, f"MagIC_{magic_id}")


DEFAULT_BASE = os.path.join("~", "MagIC")


def default_folder(magic_id: int) -> str:
    """Where a contribution goes when no directory is open and none is typed: ``~/MagIC/MagIC_<id>``."""
    return os.path.join(os.path.expanduser(DEFAULT_BASE), f"MagIC_{magic_id}")


class DownloadDialog:
    """The dialog's widgets and the download they run.

    Args:
        session: the hub's session — ``directory``, ``load(path) -> bool``,
            ``status``; its directory is the default destination.
        fetch: replaces :func:`pmagpy.magic_project.fetch_contribution`; tests
            inject one so nothing here touches the network.
        find: replaces :func:`pmagpy.magic_project.find_contributions` likewise.
    """

    def __init__(self, session, fetch: Optional[Callable] = None, find: Optional[Callable] = None):
        self.s = session
        self.fetch = fetch or mp.fetch_contribution
        self.find = find or mp.find_contributions
        self.on_loaded: Optional[Callable[[], None]] = None      # set by the app: closes the modal
        self.reference = pn.widgets.TextInput(name="Contribution ID or DOI", placeholder="20340  ·  10.1130/G53450.1",
                                              sizing_mode="stretch_width")
        self.folder = pn.widgets.TextInput(name="Into folder", sizing_mode="stretch_width",
                                           placeholder=os.path.join(DEFAULT_BASE, "MagIC_<id>") + " unless you name one")
        self.download_btn = pn.widgets.Button(name="Download", button_type="success", width=130, margin=(23, 10, 5, 10))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24)
        self.download_btn.on_click(self._download)
        self.reference.param.watch(lambda e: self._download() if e.new else None, "enter_pressed")
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    def refresh(self) -> None:
        """Point the folder field at the session's directory: an empty one is the usual destination. Blank
        on the start page, when the default folder (the placeholder) is where the download goes."""
        self.folder.value = getattr(self.s, "directory", "") or ""

    # ----- the download -------------------------------------------------------------------
    def _say(self, text: str, color: str = "") -> None:
        style = f"color:{color}" if color else MUTED_STYLE
        self.message.object = f'<div style="{style}">{text}</div>'

    async def _download(self, event=None) -> bool:
        """Find, fetch and unpack, reporting each stage; open the folder in the session when done."""
        try:
            kind, value = mp.parse_contribution_reference(self.reference.value)
        except ValueError as err:
            self._say(str(err), FAIL_COLOR)
            return False
        self.download_btn.disabled = True
        loop = asyncio.get_running_loop()
        try:
            if kind == "doi":
                self._say(f"Looking up {value} in MagIC …")
                found = await loop.run_in_executor(None, self.find, value)
                if not found:
                    self._say(f"MagIC has no public contribution with reference DOI {value}.", FAIL_COLOR)
                    return False
                ref, magic_id = found[0], found[0].id
                versions = f" — {len(found)} versions, taking the latest" if len(found) > 1 else ""
                self._say(f"Found {ref.label}{versions}. Downloading …")
            else:
                magic_id = int(value)
                self._say(f"Downloading MagIC contribution {magic_id} …")
            typed = self.folder.value.strip() or self.s.directory or default_folder(magic_id)
            folder = os.path.abspath(os.path.expanduser(typed))
            if holds_magic_tables(folder):
                self.folder.value = suggested_folder(folder, magic_id)
                self._say(f"<b>{os.path.basename(folder)}</b> already holds MagIC tables, which a download will not write "
                          f"over. The folder above is now <b>{os.path.basename(self.folder.value)}</b> beside it: "
                          "press Download again, or type another.", FAIL_COLOR)
                return False
            text = await loop.run_in_executor(None, self.fetch, magic_id)
            self._say(f"Unpacking {len(text) / 1e6:.1f} MB into {folder} …")
            tables = await loop.run_in_executor(None, mp.unpack_contribution, text, folder, magic_id)
            ref = mp.describe_contribution(text)
            if ref.id == 0:
                ref = mp.ContributionRef(id=magic_id)
        except mp.MagicDownloadError as err:
            self._say(str(err), FAIL_COLOR)
            return False
        finally:
            self.download_btn.disabled = False
        if not self.s.load(folder):
            self._say(self.s.status, FAIL_COLOR)
            return False
        self._say(f"{ref.label} · {len(tables)} tables · {folder}", OK_COLOR)
        location = runtime.location()
        if location is not None:
            location.search = f"?dir={quote(folder)}"
        if self.on_loaded:
            self.on_loaded()
        return True

    # ----- layout --------------------------------------------------------------------------
    def modal(self, width: int = 720) -> pn.Column:
        return pn.Column(
            pn.pane.HTML('<h3 style="margin:0 0 6px 0">Download from MagIC</h3>'
                         f'<div style="{MUTED_STYLE}">A public contribution, by its MagIC ID or the DOI of the paper. '
                         'Its tables land in the folder below and Home opens it.</div>'),
            pn.Row(self.reference, self.download_btn),
            self.folder, self.message,
            width=width)
