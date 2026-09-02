"""
The Convert page: the files in the directory, through one of the registry's converters, into MagIC tables.

Everything about a format — which function, which questions, which files it
takes — comes from :mod:`pmagpy.convert_registry`; this page only lays the
questions out (with :class:`pmagpy_panel.forms.Form`), lets the analyst pick
the files, and runs :func:`~pmagpy.convert_registry.convert_files` off the
event loop while it reports each file. When the tables are written the
session reloads the directory and Home fills in.

A MagIC contribution file (one download from the database, all tables in one
text file) is offered on the same page: it is not a conversion but it is the
other way a directory of files becomes a MagIC directory.
"""
from __future__ import annotations

import asyncio
import html
import os
from typing import Callable, Optional

import panel as pn

from pmagpy import magic_project as mp
from pmagpy.convert_registry import FORMATS, Format, convert_files
from pmagpy_panel.forms import Form
from pmagpy_panel.theme import MUTED_STYLE
from .home import CSS, shorten_home

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"
MAGIC_FILE = "magic"       # the pseudo-format for a contribution file


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
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.format = pn.widgets.Select(name="Format", options=format_options(), width=300)
        self.files = pn.widgets.MultiSelect(name="Files to convert", size=8, sizing_mode="stretch_width",
                                            description="Every file chosen goes through the converter; the tables are combined.")
        self.notes = pn.pane.HTML("", sizing_mode="stretch_width")
        self.form = Form()
        self.append = pn.widgets.Checkbox(name="Add to the tables already here", value=False, margin=(12, 10, 5, 10))
        self.run_btn = pn.widgets.Button(name="Convert", button_type="success", width=130, margin=(5, 10, 5, 10))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24)
        self.log = pn.pane.HTML("", sizing_mode="stretch_width", visible=False)
        self.run_btn.on_click(self._convert)
        self.format.param.watch(lambda e: self._format_changed(), "value")
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    # ----- following the directory --------------------------------------------------------------
    @property
    def fmt(self) -> Optional[Format]:
        return FORMATS.get(self.format.value)

    def refresh(self) -> None:
        """Point the page at the session's directory: its files, and the format they look like."""
        inv = self.s.inventory
        self.heading.object = (f'<div class="home"><div class="section">Convert</div><h1>{html.escape(inv.name)}</h1>'
                               f'<div class="path">{html.escape(shorten_home(inv.directory))}</div></div>')
        if inv.format_key in self.format.options.values():
            self.format.value = inv.format_key
        self.append.visible = inv.is_magic
        self.append.value = inv.is_magic
        self._format_changed()

    def reset(self) -> None:
        """A fresh page: the directory as it is now, no message or log from last time."""
        self.refresh()
        self.message.object = ""
        self.log.visible = False
        self.home_btn.button_type = "default"

    def _format_changed(self) -> None:
        inv = self.s.inventory
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
        self._offer(accepted or names, accepted)
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

    async def _convert(self, event=None) -> bool:
        """Run the converter on the chosen files and reload the directory."""
        fmt = self.fmt
        directory = self.s.directory
        if fmt is None:
            return await self._unpack(directory)
        if not fmt.takes_directory and not self.files.value:
            self._say("Choose the files to convert.", FAIL_COLOR)
            return False
        missing = self.form.missing()
        if missing:
            self._say(f"Fill in {', '.join(missing)}.", FAIL_COLOR)
            return False
        inputs = [directory] if fmt.takes_directory else list(self.files.value)
        values = self.form.values()
        self.run_btn.disabled = True
        loop = asyncio.get_running_loop()
        self._say(f"Converting with {html.escape(fmt.label)} …")
        try:
            result = await loop.run_in_executor(
                None, lambda: self.run(fmt, inputs, values, directory, append=self.append.value,
                                       report=lambda text: pn.state.execute(lambda: self._say(html.escape(text)))))
        finally:
            self.run_btn.disabled = False
        self._show_log(result.log)
        if not result.ok:
            self._say(html.escape(result.message), FAIL_COLOR)
            return False
        if not self.s.load(directory):
            self._say(html.escape(self.s.status), FAIL_COLOR)
            return False
        lines = [html.escape(result.message)]
        if result.failed:
            lines.append("; ".join(f"<b>{html.escape(n)}</b>: {html.escape(why)}" for n, why in result.failed))
        self._say(" · ".join(lines), OK_COLOR if not result.failed else "#b45309")
        self.home_btn.button_type = "primary"
        return True

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
            self.message, self.log,
            sizing_mode="stretch_width", max_width=1100, margin=(18, 40, 40, 40),
        )
