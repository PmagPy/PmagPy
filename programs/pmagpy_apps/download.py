"""
The "Download from MagIC…" dialog: a public contribution, by ID or by DOI, into a folder.

This is the first piece of the Import page and the one that needs no files of
the user's own: paste ``20340`` or ``10.1130/G53450.1``, and the contribution's
tables land in the folder named below, which Home then opens, and the folder's
conversion log (``pmagpy_conversions.json``) records where they came from: an
entry of format ``magic`` with the contribution's id, version and reference DOI,
dated (:func:`pmagpy.magic_project.record_download`). The work —
finding the contribution for a DOI, fetching the file, unpacking it — is
:mod:`pmagpy.magic_project`'s; the dialog only runs it off the event loop
(the server keeps serving while a large contribution comes down) and says what
is happening.

A folder that already holds MagIC tables is not overwritten on one click: the
first click asks where the contribution's tables go, as an unpack on the Convert
page does -- into a new folder ``MagIC_<YYYY-MM-DD>/`` inside it (the default;
nothing is overwritten), or replacing its tables, the old ones kept in
``backup_before_pmagpy_apps/`` -- and the second downloads. A replace leaves
exactly the contribution's tables: any other MagIC table there is kept in the
backup too and removed, and the message names it. The tables are written all
or nothing. On a working copy the folder offered is the study's own,
where Convert writes too; a folder that ships with PmagPy is not written into.
"""
from __future__ import annotations

import asyncio
import html
import os
from typing import Callable, Optional
from urllib.parse import quote

import panel as pn

from pmagpy import magic_project as mp
from pmagpy.convert_registry import MAGIC_TABLES, NEW_FOLDER, REPLACE, dated_folder, where_choices
from pmagpy.magic_metadata import BACKUP_DIR
from pmagpy_panel import datasets, runtime
from pmagpy_panel.theme import MUTED_STYLE

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"
WARN_COLOR = "#b45309"


def present_tables(folder: str) -> list:
    """The MagIC tables already in the folder (``contribution.txt`` among them), as file names."""
    return [f"{t}.txt" for t in ("contribution",) + MAGIC_TABLES if os.path.isfile(os.path.join(folder, f"{t}.txt"))]


def holds_magic_tables(folder: str) -> bool:
    """True when any MagIC table is already in the folder: a download asks first where its tables go."""
    return bool(present_tables(folder))


def ships_with_pmagpy(folder: str) -> bool:
    """True for a folder inside the application or a checkout's or install's ``data_files``: never written into."""
    path = os.path.realpath(folder)
    return any(path == root or path.startswith(root + os.sep) for root in datasets.shipped_roots())


def default_folder(magic_id: int) -> str:
    """Where a contribution goes when no directory is open and none is typed: ``<PmagPy folder>/MagIC_<id>``
    (``~/PmagPy`` unless ``--output`` names another; :func:`pmagpy_panel.datasets.output_base`)."""
    return os.path.join(datasets.output_base(), f"MagIC_{magic_id}")


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
                                           placeholder=os.path.join(datasets.shorten_home(datasets.output_base()), "MagIC_<id>")
                                           + " unless you name one")
        self.download_btn = pn.widgets.Button(name="Download", button_type="success", width=130, margin=(23, 10, 5, 10))
        # a folder that has tables: where the contribution's go, asked before anything is fetched
        self.where = pn.widgets.RadioBoxGroup(options={}, inline=False, visible=False, margin=(0, 10, 5, 10))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24)
        self._confirming = False
        self._asked = ""                        # the folder the question is about
        self.download_btn.on_click(self._download)
        self.reference.param.watch(lambda e: self._download() if e.new else None, "enter_pressed")
        self.reference.param.watch(lambda e: self._cancel_confirm(), "value")
        self.folder.param.watch(lambda e: self._cancel_confirm(), "value")
        self.where.param.watch(lambda e: self._label_confirm(), "value")
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    def refresh(self) -> None:
        """Point the folder field at the session's study -- the study itself when the session is on its
        working copy, as Convert writes into it. Blank on the start page, when the default folder (the
        placeholder) is where the download goes."""
        directory = getattr(self.s, "directory", "") or ""
        self.folder.value = (datasets.working_copy_source(directory) or directory) if directory else ""

    # ----- where the tables go ------------------------------------------------------------
    def _ask_where(self, folder: str) -> None:
        """The first click into a folder that has tables: ask where the contribution's tables go."""
        self.where.options = where_choices(folder, folder, BACKUP_DIR)
        self.where.value = NEW_FOLDER
        self.where.visible = self._confirming = True
        self._asked = folder
        self._label_confirm()
        self._say(f"<b>{html.escape(os.path.basename(folder.rstrip(os.sep)))}</b> has MagIC tables already "
                  f"({html.escape(', '.join(present_tables(folder)))}). Choose where the contribution's tables go "
                  "and click again.", WARN_COLOR)

    def _label_confirm(self) -> None:
        if not self._confirming:
            return
        self.download_btn.width = 330
        if self.where.value == REPLACE:
            self.download_btn.name, self.download_btn.button_type = "Confirm: replace the tables", "danger"
        else:
            name = os.path.basename(dated_folder(self._asked))
            self.download_btn.name, self.download_btn.button_type = f"Confirm: download into {name}/", "warning"

    def _cancel_confirm(self) -> None:
        self._confirming = False
        self.where.visible = False
        self.download_btn.name, self.download_btn.button_type, self.download_btn.width = "Download", "success", 130

    def _folder(self, magic_id: int) -> str:
        """The folder named for the download: the one typed, else the session's study, else the default."""
        directory = getattr(self.s, "directory", "") or ""
        typed = (self.folder.value.strip() or datasets.working_copy_source(directory) or directory
                 or default_folder(magic_id))
        return os.path.abspath(os.path.expanduser(typed))

    # ----- the download -------------------------------------------------------------------
    def _say(self, text: str, color: str = "") -> None:
        style = f"color:{color}" if color else MUTED_STYLE
        self.message.object = f'<div style="{style}">{text}</div>'

    async def _download(self, event=None) -> bool:
        """Find, fetch and unpack, reporting each stage; open the folder in the session when done.

        Into a folder that has tables the first click asks where the tables go (:meth:`_ask_where`)
        and nothing is fetched; the second writes into a dated folder inside it, or replaces its
        tables with the old ones kept in ``backup_before_pmagpy_apps/``.
        """
        try:
            kind, value = mp.parse_contribution_reference(self.reference.value)
        except ValueError as err:
            self._say(html.escape(str(err)), FAIL_COLOR)
            return False
        self.download_btn.disabled = True
        loop = asyncio.get_running_loop()
        target, made = "", False
        try:
            if kind == "doi":
                self._say(f"Looking up {html.escape(value)} in MagIC …")
                found = await loop.run_in_executor(None, self.find, value)
                if not found:
                    self._say(f"MagIC has no public contribution with reference DOI {html.escape(value)}.", FAIL_COLOR)
                    return False
                ref, magic_id = found[0], found[0].id
                versions = f" — {len(found)} versions, taking the latest" if len(found) > 1 else ""
                self._say(f"Found {ref.label}{versions}. Downloading …")
            else:
                magic_id = int(value)
                self._say(f"Downloading MagIC contribution {magic_id} …")
            folder = self._folder(magic_id)
            if ships_with_pmagpy(folder):
                self._cancel_confirm()
                self._say(f"<b>{html.escape(datasets.shorten_home(folder))}</b> ships with PmagPy, and a download is "
                          "not written into it: type another folder.", FAIL_COLOR)
                return False
            target, backup = folder, None
            if holds_magic_tables(folder):
                if not self._confirming or folder != self._asked:
                    self._ask_where(folder)
                    return False
                if self.where.value == REPLACE:
                    backup = os.path.join(folder, BACKUP_DIR)
                else:
                    target = dated_folder(folder)
            self._cancel_confirm()
            text = await loop.run_in_executor(None, self.fetch, magic_id)
            self._say(f"Unpacking {len(text) / 1e6:.1f} MB into {html.escape(target)} …")
            made = not os.path.isdir(target)

            def work():
                with mp.StagedExport(target, backup=backup, originals=True, replace_tables=bool(backup)) as stage:
                    written = mp.unpack_contribution(text, stage.dir, magic_id)
                return written, stage.removed
            tables, removed = await loop.run_in_executor(None, work)
            ref = mp.describe_contribution(text)
            if ref.id == 0:
                ref = mp.ContributionRef(id=magic_id)
            mp.record_download(target, ref, tables)
        except (mp.MagicDownloadError, OSError) as err:
            if made:
                try:
                    os.rmdir(target)                      # only while it is empty: nothing was written
                except OSError:
                    pass
            self._say(html.escape(str(err)), FAIL_COLOR)
            return False
        finally:
            self.download_btn.disabled = False
        if not self.s.load(target):
            self._say(html.escape(self.s.status), FAIL_COLOR)
            return False
        lines = [f"{ref.label} · {len(tables)} tables · {html.escape(target)}"]
        if target != folder:
            lines.append(f"written into {html.escape(os.path.basename(target))}/")
        elif backup:
            lines.append(f"the tables replaced are kept in {BACKUP_DIR}/")
            if removed:
                lines.append(html.escape(mp.removed_note(removed, BACKUP_DIR)))
                self.s.status = f"{self.s.status} · {mp.removed_note(removed, BACKUP_DIR)}"
        stale = datasets.working_copy_source(self.s.directory) and datasets.stale_copy_note(self.s.directory)
        if stale:
            lines.append(f"the working copy the applications use, {html.escape(datasets.shorten_home(self.s.directory))}, "
                         f"was made before and does not have them ({datasets.copy_remedy(self.s.directory)})")
        self._say(" · ".join(lines), WARN_COLOR if stale else OK_COLOR)
        location = runtime.location()
        if location is not None:
            location.search = f"?dir={quote(target)}"
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
            self.folder, self.where, self.message,
            width=width)
