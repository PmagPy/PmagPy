"""
The Metadata page: the locations, sites, samples, specimens, ages and criteria tables in a grid.

What Pmag GUI's ErMagicBuilder did, on the shell: one table at a time in an
editable grid whose columns, order, vocabularies and help all come from the
MagIC data model through :mod:`pmagpy.magic_metadata`. The page adds the rows
a table is owed by the table beneath it (a site the samples name but the sites
table lacks), lets the analyst add columns from the model, fills in what the
other tables already know (location bounds from the site coordinates, a
sample's coordinates from its site), checks a table with PmagPy's validator
and paints the cells it objects to, and writes the table back through the
same writer every other application uses — after copying the original once
into ``backup_before_pmagpy_apps/``.

The criteria table is edited in the same grid (what Pmag GUI's
``CustomizeCriteria`` was for): PmagPy's default acceptance criteria can be
added in a click, the ``table_column`` cell picks from every column of the
MagIC tables, and *Check* evaluates each criterion against the table it names
— how many rows pass, how many have no value — beside the validator's findings.
"""
from __future__ import annotations

import html
from typing import Dict, List, Optional

import pandas as pd
import panel as pn

from pmagpy import magic_metadata as mm
from pmagpy_panel.theme import MUTED_STYLE
from .home import CSS, fmt, shorten_home

FAIL_COLOR = "#c0392b"
OK_COLOR = "#1a7f5a"
WARN_COLOR = "#b45309"
CELL_FAIL = "background-color:#fde2e0"
CELL_STUB = "background-color:#fff7db"
PAGE_SIZE = 25

LABELS = {"locations": "Locations", "sites": "Sites", "samples": "Samples", "specimens": "Specimens", "ages": "Ages",
          "criteria": "Criteria"}

GRID_CSS = """
.tabulator { font-size: 13px; }
.tabulator .tabulator-header .tabulator-col .tabulator-col-content .tabulator-col-title { font-weight: 600; }
.tabulator-row .tabulator-cell { padding: 5px 8px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
"""

HELP_CSS = """
.help { font-size:.88rem; color:#2b2b2b; line-height:1.45 }
.help h4 { margin:0 0 2px; font-size:1rem; font-weight:650 }
.help .name { font-family:ui-monospace,Menlo,monospace; font-size:.82rem; color:#6b7280 }
.help .grp { color:#6b7280; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; margin-top:6px }
.help p { margin:6px 0 }
.help .req { color:#b45309; font-weight:600 }
.help ul { margin:4px 0 0; padding-left:18px; max-height:260px; overflow:auto }
.help li { padding:1px 0 }
.help .ex { font-family:ui-monospace,Menlo,monospace; font-size:.8rem }
.findings { font-size:.85rem; color:#2b2b2b; margin:12px 0 0; padding-left:18px; max-height:300px; overflow:auto; word-break:break-word }
.findings li { padding:2px 0 }
.findings b { font-family:ui-monospace,Menlo,monospace; font-weight:600 }
.findings .ok { color:#1a7f5a } .findings .bad { color:#c0392b } .findings .dim { color:#6b7280 }
"""


def column_help_html(table: str, name: str) -> str:
    """What one column means: label, description, unit, bounds, vocabulary, examples."""
    col = mm.column(table, name)
    if col is None:
        return (f'<div class="help"><h4>{html.escape(name)}</h4><p class="grp">not in the MagIC data model</p>'
                f"<p>This column is kept as it is and written back, but MagIC will not read it.</p></div>")
    bits = [f"<h4>{html.escape(col.label)}</h4>", f'<div class="name">{html.escape(col.name)}</div>',
            f'<div class="grp">{html.escape(col.group)} · {html.escape(col.dtype)}'
            + (" · <span class='req'>required</span>" if col.required else "") + "</div>"]
    if col.description:
        bits.append(f"<p>{html.escape(col.description)}</p>")
    facts = []
    if col.unit:
        facts.append(f"unit {html.escape(col.unit)}")
    if col.minimum is not None or col.maximum is not None:
        lo = f"{col.minimum:g}" if col.minimum is not None else "…"
        hi = f"{col.maximum:g}" if col.maximum is not None else "…"
        facts.append(f"from {lo} to {hi}")
    if col.is_list:
        facts.append("colon-delimited list")
    if facts:
        bits.append(f'<p style="{MUTED_STYLE}">{" · ".join(facts)}</p>')
    if col.vocabulary:
        bits.append(f"<p><b>Controlled vocabulary</b> ({len(col.vocabulary)} values)</p><ul>"
                    + "".join(f"<li>{html.escape(v)}</li>" for v in col.vocabulary) + "</ul>")
    elif col.suggested:
        bits.append(f"<p><b>Suggested values</b> ({len(col.suggested)})</p><ul>"
                    + "".join(f"<li>{html.escape(v)}</li>" for v in col.suggested) + "</ul>")
    if col.examples:
        bits.append("<p>Examples: " + ", ".join(f'<span class="ex">{html.escape(e)}</span>' for e in col.examples[:4]) + "</p>")
    return f'<div class="help">{"".join(bits)}</div>'


def editors_for(table: str, names) -> Dict[str, dict]:
    """Tabulator editors: a searchable list for vocabulary columns (multiple for list columns), text elsewhere.

    On the criteria table ``table_column`` picks from every column of the
    MagIC tables and ``criterion`` from the names PmagPy's tools use.
    """
    editors = {}
    for name in names:
        col = mm.column(table, name)
        values = list(col.vocabulary or col.suggested) if col else []
        if table == "criteria" and name == "table_column":
            values = mm.table_columns()
        elif table == "criteria" and name == "criterion":
            values = list(mm.CRITERION_NAMES)
        if values:
            editors[name] = {"type": "list", "values": values, "autocomplete": True, "listOnEmpty": True,
                             "freetext": True, "allowEmpty": True, "multiselect": bool(col.is_list),
                             "placeholder": "type to search"}
        else:
            editors[name] = "input"
    return editors


def findings_html(findings: List[mm.Finding]) -> str:
    """The validator's findings as a list, cells grouped by column."""
    if not findings:
        return ""
    by_col: Dict[str, List[mm.Finding]] = {}
    for f in findings:
        by_col.setdefault(f.column, []).append(f)
    items = []
    for col, fs in by_col.items():
        table_wide = [f for f in fs if not f.row]
        cells = [f for f in fs if f.row]
        if table_wide:
            items.append(f"<li><b>{html.escape(col) or 'table'}</b>: {html.escape(table_wide[0].problem)}</li>")
        if cells:
            problems = sorted({f.problem for f in cells})
            rows = ", ".join(html.escape(f.row) for f in cells[:6]) + (f" and {len(cells) - 6} more" if len(cells) > 6 else "")
            items.append(f"<li><b>{html.escape(col)}</b> in {len(cells)} row{'s' if len(cells) != 1 else ''} "
                         f"({rows}): {html.escape('; '.join(problems))}</li>")
    return f'<ul class="findings">{"".join(items)}</ul>'


def criteria_html(checks: List[mm.CriterionCheck]) -> str:
    """Each criterion with how the table it names fares: "DE-SPEC specimens.dir_mad_free <= 5: 913 of 1374 pass, 385 blank"."""
    if not checks:
        return ""
    items = []
    for c in checks:
        head = f"<b>{html.escape(c.criterion) or '?'}</b> {html.escape(c.table_column)} {html.escape(c.operation)} {html.escape(c.value)}"
        if c.problem:
            items.append(f'<li>{head}: <span class="bad">{html.escape(c.problem)}</span></li>')
        else:
            cls = "ok" if c.passing else "dim"
            items.append(f'<li>{head}: <span class="{cls}">{html.escape(c.summary())}</span></li>')
    return f'<ul class="findings">{"".join(items)}</ul>'


class MetadataView:
    """The Metadata page as Panel objects, following the session's directory.

    Args:
        session: the hub's session — ``inventory``, ``directory``, ``load(path)``.
    """

    def __init__(self, session):
        self.s = session
        self.table = "sites"
        self.frame: Optional[mm.EditorFrame] = None
        self.findings: List[mm.Finding] = []
        self.checks: List[mm.CriterionCheck] = []
        self.dirty = False
        self.heading = pn.pane.HTML("", stylesheets=[CSS], sizing_mode="stretch_width")
        self.home_btn = pn.widgets.Button(name="← Home", button_type="default", width=110, margin=(30, 0, 0, 0))
        self.tables = pn.widgets.RadioButtonGroup(options={LABELS[t]: t for t in mm.TABLES}, value="sites",
                                                  button_type="default", button_style="outline")
        self.note = pn.pane.HTML("", sizing_mode="stretch_width", min_height=22)
        self.grid = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, pagination="local", page_size=PAGE_SIZE,
                                         selectable="checkbox", layout="fit_data_table", sizing_mode="stretch_width",
                                         stylesheets=[GRID_CSS], theme="simple", height=520,
                                         configuration={"columnDefaults": {"maxWidth": 320}})
        self.save_btn = pn.widgets.Button(name="Save", button_type="success", width=100)
        self.check_btn = pn.widgets.Button(name="Check", button_type="default", width=100)
        self.add_row_btn = pn.widgets.Button(name="Add row", button_type="default", width=100)
        self.delete_btn = pn.widgets.Button(name="Delete selected", button_type="default", width=140)
        self.fill_btn = pn.widgets.Button(name="Fill defaults", button_type="default", width=120)
        self.bounds_btn = pn.widgets.Button(name="Bounds from sites", button_type="default", width=150, visible=False)
        self.ages_btn = pn.widgets.Button(name="Fill ages", button_type="default", width=100, visible=False)
        self.defaults_btn = pn.widgets.Button(name="Add default criteria", button_type="default", width=170, visible=False)
        self.parent_fill = pn.widgets.MultiChoice(name="Copy down from the table above", options=[], width=320,
                                                  placeholder="columns to copy from each row's parent", visible=False)
        self.parent_btn = pn.widgets.Button(name="Copy down", button_type="default", width=100, visible=False,
                                            margin=(23, 5, 5, 5))
        self.add_cols = pn.widgets.MultiChoice(name="Add columns", options=[], width=420,
                                               placeholder="search the MagIC data model", max_items=20)
        self.add_cols_btn = pn.widgets.Button(name="Add", button_type="default", width=70, margin=(23, 5, 5, 5))
        self.message = pn.pane.HTML("", sizing_mode="stretch_width", min_height=24)
        self.findings_pane = pn.pane.HTML("", stylesheets=[HELP_CSS], width=300)
        self.help = pn.pane.HTML("", stylesheets=[HELP_CSS], width=300)

        self.tables.param.watch(lambda e: self.show(e.new), "value")
        self.grid.on_edit(self._edited)
        self.grid.on_click(self._clicked)
        self.save_btn.on_click(lambda e: self.save())
        self.check_btn.on_click(lambda e: self.check())
        self.add_row_btn.on_click(lambda e: self.add_row())
        self.delete_btn.on_click(lambda e: self.delete_selected())
        self.fill_btn.on_click(lambda e: self.fill_defaults())
        self.bounds_btn.on_click(lambda e: self.fill_bounds())
        self.ages_btn.on_click(lambda e: self.fill_ages())
        self.defaults_btn.on_click(lambda e: self.add_default_criteria())
        self.parent_btn.on_click(lambda e: self.copy_down())
        self.add_cols_btn.on_click(lambda e: self.add_columns())
        session.param.watch(lambda e: self.refresh(), "directory")
        self.refresh()

    # ----- following the directory --------------------------------------------------------------
    def refresh(self) -> None:
        """Point the page at the session's directory and show the current table afresh."""
        inv = self.s.inventory
        self.heading.object = (f'<div class="home"><div class="section">Metadata</div><h1>{html.escape(inv.name)}</h1>'
                               f'<div class="path">{html.escape(shorten_home(inv.directory))}</div></div>')
        counts = {t: inv.counts.get(t) or (inv.tables[t].rows if t in inv.tables else 0) for t in mm.TABLES}
        self.tables.options = {f"{LABELS[t]} ({fmt(counts[t])})" if counts[t] else LABELS[t]: t for t in mm.TABLES}
        self.show(self.table)

    def reset(self) -> None:
        """A fresh page: the directory as it is now, no message from last time."""
        self.refresh()
        self.message.object = ""
        self.home_btn.button_type = "default"

    def show(self, table: str) -> None:
        """Read ``table`` into the grid."""
        self.table = table
        if self.tables.value != table:
            self.tables.value = table
        self.frame = mm.editor_frame(self.s.directory, table)
        self.findings = []
        self.dirty = False
        self._load_grid(self.frame.df)
        self._describe()
        self.help.object = column_help_html(table, mm.NAME_COLUMN.get(table, "criterion" if table == "criteria" else "location"))
        self.findings_pane.object = ""
        self.message.object = ""
        self.bounds_btn.visible = table == "locations"
        self.ages_btn.visible = table in mm.AGED_TABLES
        self.ages_btn.description = ("Undated sites take their row in ages.txt, else their location's age" if table == "sites"
                                     else "Undated locations take their row in ages.txt, else the age span of their sites")
        self.defaults_btn.visible = table == "criteria"
        down = table in mm.PARENT
        self.parent_fill.visible = self.parent_btn.visible = down
        if down:
            parent = mm.read_table(self.s.directory, mm.PARENT[table])
            pkey = mm.NAME_COLUMN[mm.PARENT[table]]
            self.parent_fill.options = [c for c in (parent.columns if parent is not None else [])
                                        if c != pkey and c in mm.columns(table) and mm.column(table, c).group in
                                        ("Geography", "Geology", "Age", "Result") and (parent[c].astype(str).str.strip() != "").any()]
            self.parent_fill.value = []
        shown = set(self.frame.df.columns)
        self.add_cols.options = {f"{c.name} — {c.label}": c.name for c in mm.columns(table).values() if c.name not in shown}
        self.add_cols.value = []

    def _load_grid(self, df: pd.DataFrame) -> None:
        names = list(df.columns)
        required = set(mm.required_columns(self.table))
        self.grid.editors = editors_for(self.table, names)
        self.grid.titles = {c: c + " *" for c in names if c in required}
        self.grid.header_tooltips = {c: (mm.column(self.table, c).description or c) if mm.column(self.table, c) else c
                                     for c in names}
        self.grid.frozen_columns = [names[0]] if names else []
        self.grid.value = df.reset_index(drop=True)
        self.grid.selection = []
        self._paint()

    def _describe(self) -> None:
        f = self.frame
        n = len(f.df)
        bits = [f"{fmt(n)} row{'s' if n != 1 else ''}"]
        if not f.exists:
            bits.append(f"no {self.table}.txt yet")
        if f.stubs:
            below = mm.CHILD.get(self.table, "")
            bits.append(f"{fmt(len(f.stubs))} added from {below} (highlighted) — fill them in and save")
        blank = [c for c in mm.required_columns(self.table) if c in f.df.columns and (f.df[c].astype(str).str.strip() == "").all()]
        if blank:
            bits.append(f"required and empty: {', '.join(blank)}")
        self.note.object = f'<div style="{MUTED_STYLE}">{html.escape(" · ".join(bits))}</div>'

    # ----- painting the grid --------------------------------------------------------------------
    def _paint(self) -> None:
        """Colour the stub rows and the cells the validator objected to."""
        df = self.grid.value
        if df is None or len(df) == 0:
            return
        key = mm.NAME_COLUMN.get(self.table)
        stubs = set(self.frame.stubs) if self.frame else set()
        fails = {(f.row, f.column) for f in self.findings if f.row and f.column}
        bad_rows = {f.row for f in self.findings if f.row and not f.column}

        def styles(frame: pd.DataFrame) -> pd.DataFrame:
            out = pd.DataFrame("", index=frame.index, columns=frame.columns)
            if key and key in frame.columns:
                names = frame[key].astype(str)
                if stubs:
                    out.loc[names.isin(stubs), :] = CELL_STUB
                for (row, column) in fails:
                    if column in frame.columns:
                        out.loc[names == row, column] = CELL_FAIL
                if bad_rows:
                    out.loc[names.isin(bad_rows), :] = CELL_FAIL
            return out

        self.grid.style.clear()            # the last paint's function would otherwise stay in the queue
        self.grid.style.apply(styles, axis=None)

    # ----- editing ------------------------------------------------------------------------------
    def _edited(self, event) -> None:
        """A cell was typed in: a multiselect list comes back as a Python list, written colon-delimited."""
        value = event.value
        if isinstance(value, (list, tuple)):
            joined = ":".join(str(v) for v in value if str(v).strip())
            self.grid.patch({event.column: [(event.row, joined)]})
        elif value is None:
            self.grid.patch({event.column: [(event.row, "")]})
        self.dirty = True
        self.save_btn.button_type = "success"
        self._say("Unsaved changes.")

    def _clicked(self, event) -> None:
        if getattr(event, "column", None):
            self.help.object = column_help_html(self.table, event.column)

    def current(self) -> pd.DataFrame:
        """The grid as it stands, every cell a string."""
        return self.grid.value.fillna("").astype(str)

    def add_row(self) -> None:
        df = self.current()
        row = mm.blank_row(self.table, df.columns)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        self._replace(df)
        self.grid.page = max(1, (len(df) + PAGE_SIZE - 1) // PAGE_SIZE)
        self._say("A blank row at the end; give it a name.")

    def delete_selected(self) -> None:
        chosen = list(self.grid.selection)
        if not chosen:
            self._say("Tick the rows to delete first.", WARN_COLOR)
            return
        df = self.current().drop(index=chosen).reset_index(drop=True)
        self._replace(df)
        self._say(f"{len(chosen)} row{'s' if len(chosen) != 1 else ''} removed — not yet saved.")

    def add_columns(self) -> None:
        names = list(self.add_cols.value)
        if not names:
            self._say("Pick the columns to add.", WARN_COLOR)
            return
        df = self.current()
        for name in names:
            if name not in df.columns:
                df[name] = mm.DEFAULTS.get(name, "")
        df = df[mm.order_columns(self.table, df.columns)]
        self._replace(df)
        self.add_cols.options = {k: v for k, v in self.add_cols.options.items() if v not in names}
        self.add_cols.value = []
        self._say(f"Added {', '.join(names)}.")

    def fill_defaults(self) -> None:
        df, n = mm.fill_defaults(self.current())
        if n:
            self._replace(df)
        self._say(f"{n} cell{'s' if n != 1 else ''} filled with the usual defaults ({', '.join(f'{k}={v}' for k, v in mm.DEFAULTS.items() if k in df.columns)})."
                  if n else "Nothing to fill: every default column is already filled in.")

    def fill_bounds(self) -> None:
        df, n = mm.fill_location_bounds(self.s.directory, self.current())
        if n:
            self._replace(df[mm.order_columns(self.table, df.columns)])
            self._say(f"{n} bound{'s' if n != 1 else ''} filled from the site coordinates.")
        else:
            self._say("No site coordinates to take bounds from, or the bounds are already filled.", WARN_COLOR)

    def fill_ages(self) -> None:
        """Date the undated rows from ages.txt and from the level above (sites) or below (locations)."""
        df, counts, notes = mm.fill_ages(self.s.directory, self.table, self.current())
        n = sum(counts.values())
        if n:
            self._replace(df[mm.order_columns(self.table, df.columns)])
        what = "site" if self.table == "sites" else "location"
        said = {"ages": "from ages.txt", "location": "from their location", "sites": "from the span of their sites"}
        parts = [f"{k} {said[src]}" for src, k in counts.items()]
        if n:
            text = f"{n} {what}{'s' if n != 1 else ''} dated: " + ", ".join(parts) + "."
        else:
            text = f"No {what} to date: every {what} has an age, or nothing else knows one."
        if notes:
            text += " Not spanned — " + "; ".join(html.escape(x) for x in notes) + "."
        self._say(text, "" if n else WARN_COLOR)

    def add_default_criteria(self) -> None:
        """Append PmagPy's default acceptance criteria (the rows the table does not have yet)."""
        df, n = mm.add_default_criteria(self.current())
        if n:
            self._replace(df)
            self.grid.page = max(1, (len(df) + PAGE_SIZE - 1) // PAGE_SIZE)
            self._say(f"{n} default criteri{'a' if n != 1 else 'on'} added — PmagPy's usual thresholds; edit the values to the study's, then save.")
        else:
            self._say("Every default criterion is already in the table.")

    def copy_down(self) -> None:
        cols = list(self.parent_fill.value)
        if not cols:
            self._say("Choose the columns to copy from the table above.", WARN_COLOR)
            return
        df, n = mm.fill_from_parent(self.s.directory, self.table, self.current(), cols)
        if n:
            self._replace(df[mm.order_columns(self.table, df.columns)])
        self._say(f"{n} cell{'s' if n != 1 else ''} copied from the {mm.PARENT[self.table]} table." if n
                  else "Nothing copied: those cells are already filled, or the parent rows have no value.")

    def _replace(self, df: pd.DataFrame) -> None:
        self._load_grid(df)
        self.dirty = True

    # ----- checking and saving ------------------------------------------------------------------
    def check(self) -> List[mm.Finding]:
        """Validate the table as saved on disk (saving first when the grid has changes).

        On the criteria table the check also evaluates every criterion against
        the table it names and lists how many rows pass.
        """
        if self.dirty:
            self.save()
        self.findings = mm.check_table(self.s.directory, self.table)
        self._paint()
        self.findings_pane.object = findings_html(self.findings)
        if self.table == "criteria":
            self.checks = mm.check_criteria(self.s.directory, self.current())
            self.findings_pane.object += criteria_html(self.checks)
            stuck = sum(1 for c in self.checks if c.problem)
            said = f"{len(self.checks)} criteri{'a' if len(self.checks) != 1 else 'on'} evaluated against the tables"
            if stuck:
                said += f"; {stuck} could not be (see the list)"
            if not self.findings:
                self._say(said + ". The table passes PmagPy's MagIC validator.", FAIL_COLOR if stuck else OK_COLOR)
                return self.findings
            self._say(said + ". The validator objects, see below.", FAIL_COLOR)
            return self.findings
        if not self.findings:
            self._say(f"{LABELS[self.table]} pass PmagPy's MagIC validator.", OK_COLOR)
        else:
            cells = sum(1 for f in self.findings if f.row)
            cols = sum(1 for f in self.findings if not f.row)
            parts = ([f"{cells} cell{'s' if cells != 1 else ''}"] if cells else []) + \
                    ([f"{cols} required column{'s' if cols != 1 else ''} missing"] if cols else [])
            self._say("The validator objects to " + " and ".join(parts) + ".", FAIL_COLOR)
        return self.findings

    def save(self) -> bool:
        """Write the table, reload the session so Home's gaps follow, and keep the grid as saved."""
        df = self.current()
        try:
            mm.save_table(self.s.directory, self.table, df)
        except (OSError, ValueError) as err:
            self._say(f"Not saved: {html.escape(str(err))}", FAIL_COLOR)
            return False
        self.s.load(self.s.directory)     # also calls refresh() through the watcher, which re-reads the table
        self.dirty = False
        self._say(f"{self.table}.txt written" + (f" · original kept in {mm.BACKUP_DIR}/" if mm.backup_exists(self.s.directory, self.table) else ""),
                  OK_COLOR)
        self.home_btn.button_type = "primary"
        return True

    def _say(self, text: str, color: str = "") -> None:
        style = f"color:{color}" if color else MUTED_STYLE
        self.message.object = f'<div style="{style}">{text}</div>'

    # ----- layout ------------------------------------------------------------------------------------
    def panel(self) -> pn.Column:
        tools = pn.Row(self.save_btn, self.check_btn, pn.Spacer(width=14), self.add_row_btn, self.delete_btn,
                       self.fill_btn, self.bounds_btn, self.ages_btn, self.defaults_btn, sizing_mode="stretch_width", margin=(6, 0, 0, 0))
        fills = pn.Row(self.add_cols, self.add_cols_btn, pn.Spacer(width=30), self.parent_fill, self.parent_btn,
                       sizing_mode="stretch_width")
        return pn.Column(
            pn.Row(self.heading, self.home_btn, sizing_mode="stretch_width"),
            pn.Row(self.tables, margin=(10, 0, 0, 0)),
            tools,
            pn.Row(self.note, self.message, sizing_mode="stretch_width"),
            pn.Row(self.grid, pn.Spacer(width=20),
                   pn.Column(self.help, self.findings_pane, width=300),
                   sizing_mode="stretch_width"),
            fills,
            sizing_mode="stretch_width", max_width=1400, margin=(18, 40, 40, 40),
        )
