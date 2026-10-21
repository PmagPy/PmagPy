"""
The Convert page: the files in the directory, through one of the registry's converters, into MagIC tables.

Everything about a format — which function, which questions, which files it
takes — comes from :mod:`pmagpy.convert_registry`; this page only lays the
questions out (with :class:`pmagpy_panel.forms.Form`), lets the analyst pick
the files, and runs :func:`~pmagpy.convert_registry.convert_files` off the
event loop while it reports each file. When the tables are written the
session reloads the directory and Home fills in.

The tables go into the lab folder the analyst chose, beside the files they came
from -- also when the session is on a working copy of the study
(:func:`pmagpy_panel.datasets.working_directory`): the page then lists the
study's own folder and converts into it. A folder that already has MagIC tables
is not overwritten on one click: adding to them leaves out the files its
conversion log says are in them already (unless the analyst asks for them
again), and converting afresh asks first whether the new tables go into a dated
folder of their own (``MagIC_<date>/``) or replace the old ones, which are then
kept in ``backup_before_pmagpy_apps/``.

A MagIC contribution file (one download from the database, all tables in one
text file) is offered on the same page: it is not a conversion but it is the
other way a directory of files becomes a MagIC directory.
"""
from __future__ import annotations

import asyncio
import html
import os
from datetime import date
from typing import Callable, List, Optional

import panel as pn

from pmagpy import magic_project as mp
from pmagpy.convert_registry import (FORMATS, MAGIC_TABLES, Format, already_converted, convert_files,
                                     directory_inputs, log_name, record_conversion)
from pmagpy.magic_metadata import BACKUP_DIR
from pmagpy_panel import datasets
from pmagpy_panel.forms import Form
from pmagpy_panel.theme import MUTED_STYLE
from pmagpy_panel.widgets import LayoutHold
from .home import CSS, shorten_home
from .inventory import Inventory, take_inventory

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"
WARN_COLOR = "#b45309"
MAGIC_FILE = "magic"       # the pseudo-format for a contribution file
NEW_FOLDER, REPLACE = "folder", "replace"


def dated_folder(directory: str, today: Optional[date] = None) -> str:
    """The folder a fresh set of tables goes to beside old ones: ``MagIC_<YYYY-MM-DD>``, then ``-2``, ``-3`` …"""
    stem = f"MagIC_{(today or date.today()).isoformat()}"
    name, n = stem, 1
    while os.path.exists(os.path.join(directory, name)):
        n += 1
        name = f"{stem}-{n}"
    return os.path.join(directory, name)


def has_tables(directory: str) -> bool:
    """True when any MagIC table is in the folder: a conversion without "add" would replace it."""
    return any(os.path.isfile(os.path.join(directory, f"{t}.txt")) for t in MAGIC_TABLES)


def format_options() -> dict:
    """Select options: label → key, the registry's formats alphabetically, the contribution file last."""
    labels = {fmt.label: key for key, fmt in sorted(FORMATS.items(), key=lambda kv: kv[1].label.lower())}
    labels["MagIC contribution file (unpack)"] = MAGIC_FILE
    return labels


class ConvertView:
    """The Convert page as Panel objects, following the session's directory.

    Args:
        session: the hub's session — ``inventory``, ``directory``, ``load(path)``.
        run: replaces :func:`pmagpy.convert_registry.convert_files`; tests inject one.
    """

    def __init__(self, session, run: Optional[Callable] = None):
        self.s = session
        self.run = run or convert_files
        self.inv: Inventory = session.inventory
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.format = pn.widgets.Select(name="Format", options=format_options(), width=300)
        self.files = pn.widgets.MultiSelect(name="Files to convert", size=8, sizing_mode="stretch_width",
                                            description="Every file chosen goes through the converter; the tables are combined.")
        self.notes = pn.pane.HTML("", sizing_mode="stretch_width")
        self.form = Form()
        self.append = pn.widgets.Checkbox(name="Add to the tables already here", value=False, margin=(12, 10, 5, 10))
        self.run_btn = pn.widgets.Button(name="Convert", button_type="success", width=130, margin=(5, 10, 5, 10))
        # files the log says are in the tables already: left out of an "add", unless asked for again
        self.done_note = pn.pane.HTML("", sizing_mode="stretch_width", visible=False, margin=(0, 10, 0, 10))
        self.again = pn.widgets.Checkbox(name="Convert them again anyway", value=False, visible=False,
                                         margin=(0, 10, 5, 10))
        # a fresh conversion into a folder that has tables: where the new ones go, asked before anything is written
        self.where = pn.widgets.RadioBoxGroup(options={}, inline=False, visible=False, margin=(0, 10, 5, 10))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24)
        self.log = pn.pane.HTML("", sizing_mode="stretch_width", visible=False)
        self._confirming = False
        self.run_btn.on_click(self._convert)
        self.format.param.watch(lambda e: self._format_changed(), "value")
        self.files.param.watch(lambda e: self._choice_changed(), "value")
        self.append.param.watch(lambda e: self._choice_changed(), "value")
        self.where.param.watch(lambda e: self._label_confirm(), "value")
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    # ----- following the directory --------------------------------------------------------------
    @property
    def fmt(self) -> Optional[Format]:
        return FORMATS.get(self.format.value)

    @property
    def folder(self) -> str:
        """Where the lab files are and the tables go: the study itself, also when the session is on its working copy."""
        directory = self.s.directory
        return (datasets.working_copy_source(directory) or directory) if directory else ""

    def refresh(self) -> None:
        """Point the page at the session's study: its own folder's files, and the format they look like."""
        with LayoutHold.batch():
            folder = self.folder
            on_copy = bool(folder) and os.path.realpath(folder) != os.path.realpath(self.s.directory)
            self.inv = inv = take_inventory(folder) if on_copy else self.s.inventory
            lines = f'<div class="path">{html.escape(shorten_home(inv.directory))}</div>'
            if on_copy:
                lines += (f'<div class="path">The lab files are here, and the tables are written here too; the '
                          f'applications work on the copy {html.escape(shorten_home(self.s.directory))}.</div>')
            self.heading.object = (f'<div class="home"><div class="section">Convert</div><h1>{html.escape(inv.name)}</h1>'
                                   f'{lines}</div>')
            if inv.format_key in self.format.options.values():
                self.format.value = inv.format_key
            # any table already here is worth keeping — the samples and sites from a field notebook as much as measurements
            self.append.visible = inv.is_magic or inv.has_level_tables
            self.append.value = inv.is_magic or inv.has_level_tables
            self._format_changed()

    def reset(self) -> None:
        """A fresh page: the directory as it is now, no message or log from last time."""
        self.refresh()
        self.message.object = ""
        self.log.visible = False
        self.home_btn.button_type = "default"

    def _format_changed(self) -> None:
        with LayoutHold.batch():        # the form's fields, the file list's size, notes: one layout
            self._fill_format()
            self._choice_changed()

    def _fill_format(self) -> None:
        inv = self.inv
        fmt = self.fmt
        names = [f.name for f in inv.files]
        if fmt is None:                                   # the contribution file
            self._offer(names, [f.name for f in inv.files if f.role == "MagIC contribution file"])
            self.files.disabled = False
            self.form.set_fields(())
            self._note("One text file with every table in it, as MagIC serves a contribution. It unpacks into "
                       "the tables here.")
            return
        self.form.set_fields(fmt.fields)
        if fmt.takes_directory:
            self._offer(names, [])
            self.files.disabled = True
            self._note(f"{fmt.label} reads every file in the directory; there is nothing to choose. "
                       + (fmt.notes or ""))
            return
        self.files.disabled = False
        accepted = [n for n in names if fmt.accepts(n)]
        # when the guess was this format, the files it recognised are the ones chosen — not every
        # .txt beside a field notebook
        recognised = [f.name for f in inv.files if f.role and f.name in accepted] if inv.format_key == fmt.key else []
        self._offer(accepted or names, recognised or accepted)
        self._note(fmt.notes or "")

    def _offer(self, options, chosen) -> None:
        """The file list: the files this format takes, sized to them, the likely ones chosen."""
        self.files.options = list(options)
        self.files.size = min(10, max(3, len(options)))
        self.files.value = list(chosen)

    def _note(self, text: str) -> None:
        self.notes.object = f'<div style="{MUTED_STYLE};margin:2px 0 6px">{html.escape(text)}</div>' if text else ""

    # ----- running ----------------------------------------------------------------------------------
    def _say(self, text: str, color: str = "") -> None:
        style = f"color:{color}" if color else MUTED_STYLE
        self.message.object = f'<div style="{style}">{text}</div>'

    def _show_log(self, text: str) -> None:
        self.log.visible = bool(text.strip())
        self.log.object = (f'<pre style="font-size:.78rem;line-height:1.4;color:#4b5563;background:#f6f7f9;'
                           f'border:1px solid #e3e6ea;border-radius:6px;padding:10px 12px;max-height:260px;'
                           f'overflow:auto;white-space:pre-wrap">{html.escape(text.strip())}</pre>')

    # ----- what a click would do ---------------------------------------------------------------------
    def _chosen_paths(self) -> List[str]:
        """The files the conversion would read, as paths: the chosen ones, or those a directory format takes."""
        fmt, folder = self.fmt, self.folder
        if fmt is None or not folder:
            return []
        if fmt.takes_directory:
            return [os.path.join(folder, n) for n in directory_inputs(fmt, folder)
                    if os.path.isfile(os.path.join(folder, n))]
        return [os.path.join(folder, n) for n in self.files.value]

    def _already_in(self) -> List[str]:
        """The chosen files the folder's conversion log says are in its tables already (as they are now)."""
        return already_converted(self.folder, self._chosen_paths()) if self.folder else []

    def _choice_changed(self) -> None:
        """Another format, file or "add": nothing waits to be confirmed, and the files converted before are named."""
        self._cancel_confirm()
        done = self._already_in() if self.fmt is not None and self.append.visible and self.append.value else []
        self.done_note.visible = self.again.visible = bool(done)
        if done:
            self.done_note.object = (f'<div style="{MUTED_STYLE}">Already in these tables (pmagpy_conversions.json '
                                     f'lists them), so left out: <b>{html.escape(", ".join(done))}</b></div>')
        else:
            self.again.value = False

    def _cancel_confirm(self) -> None:
        self._confirming = False
        self.where.visible = False
        self.run_btn.name, self.run_btn.button_type, self.run_btn.width = "Convert", "success", 130

    def _ask_where(self, folder: str) -> None:
        """The first click of a fresh conversion into a folder that has tables: ask where the new ones go."""
        name = os.path.basename(dated_folder(folder))
        self.where.options = {f"Into a new folder here, {name}/ (nothing is overwritten)": NEW_FOLDER,
                              f"Replace the tables here (the old ones are kept in {BACKUP_DIR}/)": REPLACE}
        self.where.value = NEW_FOLDER
        self.where.visible = True
        self._confirming = True
        self._label_confirm()
        present = [f"{t}.txt" for t in MAGIC_TABLES if os.path.isfile(os.path.join(folder, f"{t}.txt"))]
        self._say(f"This folder has MagIC tables already ({html.escape(', '.join(present))}). Choose where the new "
                  "tables go and click again, or tick “Add to the tables already here”.", WARN_COLOR)

    def _label_confirm(self) -> None:
        if not self._confirming:
            return
        self.run_btn.width = 260
        if self.where.value == REPLACE:
            self.run_btn.name, self.run_btn.button_type = "Confirm: replace the tables", "danger"
        else:
            name = os.path.basename(dated_folder(self.folder))
            self.run_btn.name, self.run_btn.button_type = f"Confirm: write into {name}/", "warning"

    # ----- running ----------------------------------------------------------------------------------
    async def _convert(self, event=None) -> bool:
        """Run the converter on the chosen files and reload the directory."""
        fmt = self.fmt
        folder = self.folder
        if fmt is None:
            return await self._unpack(folder)
        if not fmt.takes_directory and not self.files.value:
            self._say("Choose the files to convert.", FAIL_COLOR)
            return False
        missing = self.form.missing()
        if missing:
            self._say(f"Fill in {', '.join(missing)}.", FAIL_COLOR)
            return False
        inputs = [folder] if fmt.takes_directory else [os.path.join(folder, n) for n in self.files.value]
        append = self.append.visible and self.append.value
        target, extra, left_out = folder, {}, []
        if append and not self.again.value:
            left_out = self._already_in()
            again = "Tick “Convert them again anyway” to add them a second time."
            if left_out and fmt.takes_directory:
                self._say(f"{html.escape(fmt.label)} reads the whole folder, and "
                          f"<b>{html.escape(', '.join(left_out))}</b> are in these tables already. {again}", FAIL_COLOR)
                return False
            inputs = [p for p in inputs if log_name(p, folder) not in left_out]
            if not inputs:
                self._say(f"Nothing new to convert: <b>{html.escape(', '.join(left_out))}</b> "
                          f"{'is' if len(left_out) == 1 else 'are'} in these tables already. {again}", FAIL_COLOR)
                return False
        elif not append and has_tables(folder):
            if not self._confirming:
                self._ask_where(folder)
                return False
            if self.where.value == REPLACE:
                extra = {"backup": os.path.join(folder, BACKUP_DIR)}
            else:
                target = dated_folder(folder)
                extra = {"magic_dir": folder}
        self._cancel_confirm()
        values = self.form.values()
        self.run_btn.disabled = True
        loop = asyncio.get_running_loop()
        self._say(f"Converting with {html.escape(fmt.label)} …")
        try:
            if target != folder:
                os.mkdir(target)
            result = await loop.run_in_executor(
                None, lambda: self.run(fmt, inputs, values, target, append=append,
                                       report=lambda text: pn.state.execute(lambda: self._say(html.escape(text))),
                                       **extra))
        except OSError as err:
            self._forget(target, folder)
            self._say(f"Could not write into {html.escape(shorten_home(target))}: {html.escape(str(err))}", FAIL_COLOR)
            return False
        finally:
            self.run_btn.disabled = False
        self._show_log(result.log)
        if not result.ok:
            self._forget(target, folder)
            self._say(html.escape(result.message), FAIL_COLOR)
            return False
        if not self.s.load(target):
            self._say(html.escape(self.s.status), FAIL_COLOR)
            return False
        lines = [html.escape(result.message)]
        if target != folder:
            lines.append(f"written into {html.escape(os.path.basename(target))}/")
        elif "backup" in extra:
            lines.append(f"the tables replaced are kept in {BACKUP_DIR}/")
        if left_out:
            lines.append(f"left out, in these tables already: {html.escape(', '.join(left_out))}")
        if result.failed:
            lines.append("; ".join(f"<b>{html.escape(n)}</b>: {html.escape(why)}" for n, why in result.failed))
        copy = self.s.directory if datasets.working_copy_source(self.s.directory) else ""
        if copy:
            lines.append(f"the tables are in {html.escape(shorten_home(target))}; the working copy the applications "
                         f"use, {html.escape(shorten_home(copy))}, was made before and does not have them")
        self._say(" · ".join(lines), OK_COLOR if not (result.failed or copy) else WARN_COLOR)
        self.home_btn.button_type = "primary"
        return True

    @staticmethod
    def _forget(target: str, folder: str) -> None:
        """Remove the dated folder a conversion that wrote nothing had made (only while it is empty)."""
        if target != folder:
            try:
                os.rmdir(target)
            except OSError:
                pass

    async def _unpack(self, directory: str) -> bool:
        chosen = list(self.files.value)
        if len(chosen) != 1:
            self._say("Choose the one contribution file to unpack.", FAIL_COLOR)
            return False
        path = os.path.join(directory, chosen[0])
        self.run_btn.disabled = True
        loop = asyncio.get_running_loop()
        self._say(f"Unpacking {html.escape(chosen[0])} …")
        try:
            def work():
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                return mp.unpack_contribution(text, directory)
            tables = await loop.run_in_executor(None, work)
        except (OSError, mp.MagicDownloadError) as err:
            self._say(html.escape(str(err)), FAIL_COLOR)
            return False
        finally:
            self.run_btn.disabled = False
        record_conversion(directory, "magic", [chosen[0]], tables={t: mp.table_rows(os.path.join(directory, f"{t}.txt")) for t in tables},
                          label="MagIC contribution file")
        if not self.s.load(directory):
            self._say(html.escape(self.s.status), FAIL_COLOR)
            return False
        self._say(f"{html.escape(chosen[0])} unpacked · {len(tables)} tables", OK_COLOR)
        self.home_btn.button_type = "primary"
        return True

    # ----- layout ------------------------------------------------------------------------------------
    def panel(self) -> pn.Column:
        return pn.Column(
            pn.Row(self.heading, self.home_btn, sizing_mode="stretch_width"),
            pn.Row(self.format, self.files, sizing_mode="stretch_width", margin=(10, 0, 0, 0)),
            self.notes,
            self.form.panel(),
            pn.Row(self.run_btn, self.append, sizing_mode="stretch_width", margin=(8, 0, 0, 0)),
            self.done_note, self.again, self.where,
            self.message, self.log,
            # room under the form for an open pick-list (protocols, orientation codes): the page
            # would otherwise end just below it and cut the list off
            sizing_mode="stretch_width", max_width=1100, min_height=720, margin=(18, 40, 40, 40),
        )
