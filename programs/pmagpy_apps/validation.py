"""
The Validation page: the study's tables as MagIC's validator sees them, at a glance.

Every MagIC table in the directory is checked with the rules of the MagIC
website, offline (:func:`pmagpy.magic_project.validation_problems`, which runs
:mod:`pmagpy.magic_validation`), and the page draws what comes back: a line per
table (its rows, the rows with errors, the warnings), a grid of tables by
columns whose cells count the rows with an error there, and the problems in
MagIC's words, grouped, with the rows they name. "Show in Metadata" opens a
table in the Metadata grid with those cells painted, where they are fixed.

The drawing functions (:func:`summary`, :func:`summary_html`, :func:`grid_html`,
:func:`problems_html`) take the problems and return HTML, so that the Convert
page can show the same summary for the tables it has just written.
"""
from __future__ import annotations

import asyncio
import html
import os
from typing import Callable, Dict, List, Optional

import pandas as pd
import panel as pn

from pmagpy import magic_project as mp
from pmagpy_panel.theme import MUTED_STYLE
from pmagpy_panel.widgets import LayoutHold
from .home import CSS, shorten_home

TABLES = ("locations", "sites", "samples", "specimens", "measurements", "ages", "criteria")
FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"
WARN_COLOR = "#b45309"
MAX_NAMES = 6           # row names listed for a problem before "… and n more"

VALIDATION_CSS = """
.vsum { border-collapse:collapse; font-size:.9rem; margin:4px 0 10px }
.vsum td, .vsum th { padding:3px 12px 3px 0; text-align:left; white-space:nowrap }
.vsum th { color:#6b7280; font-weight:500; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em }
.vsum .bar { display:inline-block; height:8px; border-radius:4px; vertical-align:middle; margin-right:6px }
.vsum .ok { color:#1a7f5a } .vsum .err { color:#c0392b; font-weight:600 } .vsum .warn { color:#b45309 }
.vgrid { border-collapse:collapse; font-size:.78rem; margin:6px 0 12px }
.vgrid th { font-weight:500; color:#4b5563; padding:2px 4px; white-space:nowrap }
.vgrid th.col { writing-mode:vertical-rl; transform:rotate(180deg); text-align:left; vertical-align:bottom }
.vgrid td { width:26px; height:22px; text-align:center; border:1px solid #fff; color:#fff; font-weight:600 }
.vgrid td.none { background:#eef0f3; color:#eef0f3 }
.vprob { font-size:.87rem; line-height:1.45; max-height:420px; overflow:auto; border:1px solid #e3e6ea;
         border-radius:6px; padding:8px 14px; background:#fafbfc }
.vprob h4 { margin:10px 0 2px; font-size:.95rem } .vprob h4:first-child { margin-top:0 }
.vprob li { padding:1px 0 } .vprob .names { color:#6b7280 } .vprob b { font-family:ui-monospace,Menlo,monospace }
"""


def table_rows(directory: str, table: str) -> int:
    """The number of rows of a table file (0 when it is not there or cannot be read)."""
    try:
        return len(pd.read_csv(os.path.join(directory, table + ".txt"), sep="\t", header=1, dtype=str,
                               keep_default_na=False, quoting=3))
    except (OSError, ValueError, pd.errors.ParserError):
        return 0


def summary(problems: pd.DataFrame, directory: str, tables=TABLES) -> List[dict]:
    """One dict per table present: ``table``, ``rows``, ``error_rows`` (rows with at least one error),
    ``errors`` (problems, a problem of the whole table counted once), ``table_errors`` and ``warnings``."""
    out = []
    for table in tables:
        if not os.path.exists(os.path.join(directory, table + ".txt")):
            continue
        mine = problems[problems["table"] == table] if len(problems) else problems
        errors = mine[mine["level"] == "error"] if len(mine) else mine
        warnings = mine[mine["level"] == "warning"] if len(mine) else mine
        out.append({"table": table, "rows": table_rows(directory, table),
                    "error_rows": int(errors.loc[errors["row"] > 0, "row"].nunique()) if len(errors) else 0,
                    "errors": int(len(errors)), "table_errors": int((errors["row"] == 0).sum()) if len(errors) else 0,
                    "warnings": int(len(warnings))})
    return out


def summary_html(rows: List[dict]) -> str:
    """A line per table: its rows, a bar of the share of rows with errors, the errors and warnings."""
    if not rows:
        return f'<div style="{MUTED_STYLE}">No MagIC tables here.</div>'
    lines = ['<table class="vsum"><tr><th>Table</th><th>Rows</th><th>Rows with errors</th>'
             '<th>Table-wide</th><th>Warnings</th></tr>']
    for r in rows:
        share = r["error_rows"] / r["rows"] if r["rows"] else 0
        width = 80
        bar = (f'<span class="bar" style="width:{max(2, round(width * share))}px;background:{FAIL_COLOR}"></span>'
               f'<span class="bar" style="width:{width - max(2, round(width * share))}px;background:#d7f0e4"></span>'
               if r["error_rows"] else f'<span class="bar" style="width:{width}px;background:#9fd8bd"></span>')
        status = (f'<span class="err">{r["error_rows"]}</span>' if r["error_rows"] else '<span class="ok">0</span>')
        lines.append(f'<tr><td><b>{html.escape(r["table"])}</b></td><td>{r["rows"]}</td><td>{bar}{status}</td>'
                     f'<td>{"<span class=err>%d</span>" % r["table_errors"] if r["table_errors"] else "0"}</td>'
                     f'<td>{"<span class=warn>%d</span>" % r["warnings"] if r["warnings"] else "0"}</td></tr>')
    return "".join(lines) + "</table>"


def grid_html(problems: pd.DataFrame, tables=TABLES) -> str:
    """Tables by the columns with errors: each cell counts the rows with an error in that column (a whole
    column or table missing counts as one), coloured from pale to deep red."""
    errors = problems[(problems["level"] == "error") & (problems["column"] != "")] if len(problems) else problems
    if not len(errors):
        return ""
    present = [t for t in tables if t in set(errors["table"])]
    columns = list(dict.fromkeys(errors["column"]))
    counts = errors.groupby(["table", "column"])["row"].nunique()
    top = max(int(counts.max()), 1)
    head = "".join(f'<th class="col">{html.escape(c)}</th>' for c in columns)
    body = []
    for table in present:
        cells = []
        for column in columns:
            n = int(counts.get((table, column), 0))
            if not n:
                cells.append('<td class="none">·</td>')
                continue
            alpha = 0.35 + 0.65 * (n / top) ** 0.5
            cells.append(f'<td title="{html.escape(table)}.{html.escape(column)}: {n} row{"s" if n != 1 else ""}" '
                         f'style="background:rgba(192,57,43,{alpha:.2f})">{n if n < 1000 else "1k+"}</td>')
        body.append(f'<tr><th style="text-align:right">{html.escape(table)}</th>{"".join(cells)}</tr>')
    return f'<table class="vgrid"><tr><th></th>{head}</tr>{"".join(body)}</table>'


def problems_html(problems: pd.DataFrame, level: str = "error", table: Optional[str] = None) -> str:
    """The problems in MagIC's words, by table, each with the number of rows and the first row names."""
    rows = problems[problems["level"] == level] if len(problems) else problems
    if table:
        rows = rows[rows["table"] == table]
    if not len(rows):
        return ""
    parts = []
    for name, group in rows.groupby("table", sort=False):
        items = []
        for (column, message), g in group.groupby(["column", "message"], sort=False):
            names = [n for n in dict.fromkeys(g["name"]) if n]
            n_rows = int(g.loc[g["row"] > 0, "row"].nunique())
            listed = ", ".join(html.escape(n) for n in names[:MAX_NAMES])
            more = f" … and {len(names) - MAX_NAMES} more" if len(names) > MAX_NAMES else ""
            # a site (or location) with means has a row per component and coordinate system
            of = f" of {len(names)} {name[:-1] if name.endswith('s') else name}{'s' if len(names) != 1 else ''}" \
                if len(names) != n_rows else ""
            where = (f' <span class="names">· {n_rows} row{"s" if n_rows != 1 else ""}{of}: {listed}{more}</span>'
                     if names else "")
            items.append(f'<li>{"<b>" + html.escape(column) + "</b>: " if column else ""}{html.escape(message)}{where}</li>')
        parts.append(f'<h4>{html.escape(name)} <span class="names">{len(group)} '
                     f'{"errors" if level == "error" else "warnings"}</span></h4><ul>{"".join(items)}</ul>')
    return f'<div class="vprob">{"".join(parts)}</div>'


def verdict(rows: List[dict]) -> str:
    """One sentence: whether the tables pass, and if not how much is wrong."""
    error_rows = sum(r["error_rows"] for r in rows)
    table_errors = sum(r["table_errors"] for r in rows)
    failing = [r["table"] for r in rows if r["error_rows"] or r["table_errors"]]
    if not failing:
        warnings = sum(r["warnings"] for r in rows)
        return "The tables pass MagIC's validator" + (f" ({warnings} warnings)." if warnings else ".")
    parts = ([f"{error_rows} row{'s' if error_rows != 1 else ''} with errors"] if error_rows else []) + \
            ([f"{table_errors} problem{'s' if table_errors != 1 else ''} of whole tables or columns"] if table_errors else [])
    return f"MagIC's validator finds {' and '.join(parts)}, in {', '.join(failing)}."


class ValidationView:
    """The Validation page for the session's directory.

    Args:
        session: the hub's session (``directory``, ``inventory``).
        open_table: called with a table name for "Show in Metadata" (the hub turns to the Metadata page).
    """

    def __init__(self, session, open_table: Optional[Callable[[str], None]] = None):
        self.s = session
        self.open_table = open_table
        self.problems = pd.DataFrame(columns=["level", "table", "column", "message", "row", "name"])
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.check_btn = pn.widgets.Button(name="Check the tables", button_type="primary", width=160)
        self.level = pn.widgets.RadioButtonGroup(options={"Errors": "error", "Warnings": "warning"}, value="error",
                                                 button_type="light", margin=(5, 10))
        self.table = pn.widgets.Select(name="", options={"every table": ""}, value="", width=180, margin=(5, 10))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=22)
        self.summary_pane = pn.pane.HTML("", stylesheets=[VALIDATION_CSS], sizing_mode="stretch_width")
        self.grid_pane = pn.pane.HTML("", stylesheets=[VALIDATION_CSS], sizing_mode="stretch_width")
        self.problems_pane = pn.pane.HTML("", stylesheets=[VALIDATION_CSS], sizing_mode="stretch_width")
        self.open_btns = pn.Row(sizing_mode="stretch_width")
        self.check_btn.on_click(self._check)
        self.level.param.watch(lambda e: self._draw(), "value")
        self.table.param.watch(lambda e: self._draw(), "value")
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    def refresh(self) -> None:
        directory = self.s.directory or ""
        self.heading.object = (f'<div class="home"><div class="section">Validation</div>'
                               f'<h1>{html.escape(os.path.basename(directory.rstrip(os.sep)) or "—")}</h1>'
                               f'<div class="path">{html.escape(shorten_home(directory))}</div></div>')

    def reset(self) -> None:
        """A fresh page, checked at once: the tables may have changed since the last visit."""
        self.refresh()
        self.run()

    def run(self) -> None:
        """Check the tables now (on the event loop's thread; the button runs it off the loop)."""
        directory = self.s.directory
        if not directory:
            return
        self.problems = mp.validation_problems(directory, TABLES)
        self._draw()

    async def _check(self, event=None) -> None:
        directory = self.s.directory
        if not directory:
            return
        self.check_btn.disabled = True
        self._say("Checking with MagIC's rules …")
        try:
            self.problems = await asyncio.get_running_loop().run_in_executor(
                None, lambda: mp.validation_problems(directory, TABLES))
        finally:
            self.check_btn.disabled = False
        self._draw()

    def _say(self, text: str, color: str = "") -> None:
        style = f"color:{color}" if color else MUTED_STYLE
        self.message.object = f'<div style="{style}">{html.escape(text)}</div>'

    def _draw(self) -> None:
        directory = self.s.directory or ""
        rows = summary(self.problems, directory)
        failing = [r["table"] for r in rows if r["error_rows"] or r["table_errors"]]
        with LayoutHold.batch():
            self._say(verdict(rows), FAIL_COLOR if failing else OK_COLOR)
            self.summary_pane.object = summary_html(rows)
            self.grid_pane.object = grid_html(self.problems)
            self.table.options = {"every table": "", **{r["table"]: r["table"] for r in rows}}
            text = problems_html(self.problems, self.level.value, self.table.value or None)
            self.problems_pane.object = text or f'<div style="{MUTED_STYLE}">None.</div>'
            buttons = []
            for table in failing:
                b = pn.widgets.Button(name=f"Show {table} in Metadata", button_type="default", width=210)
                b.on_click(lambda e, t=table: self.open_table and self.open_table(t))
                buttons.append(b)
            self.open_btns.objects = buttons if self.open_table else []

    def panel(self) -> pn.Column:
        return pn.Column(
            pn.Row(self.heading, self.home_btn, sizing_mode="stretch_width"),
            pn.Row(self.check_btn, self.message, sizing_mode="stretch_width", margin=(10, 0, 0, 0)),
            self.summary_pane,
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">Columns with errors, by table: the rows with an error in '
                         'each cell (hover for the count).</div>', sizing_mode="stretch_width"),
            self.grid_pane,
            pn.Row(self.level, self.table, sizing_mode="stretch_width"),
            self.problems_pane,
            self.open_btns,
            sizing_mode="stretch_width", max_width=1100, margin=(18, 40, 40, 40),
        )
