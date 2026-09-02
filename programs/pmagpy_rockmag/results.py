"""
Results back into the specimens table.

Each analysis ends where the RockmagPy notebooks end: one of
``pmagpy.rockmag``'s ``add_*_to_specimens_table`` writers puts what was
measured on the specimen's row (or its component rows) of ``specimens.txt``,
and the table is written back into the directory it was read from. The
:class:`SpecimenSave` block under a view's result is that step as a button —
it hands the writer to :class:`pmagpy.magic_project.MagicProject`, which copies
the original table once into ``backup_before_pmagpy_rockmag/`` and writes the
new one, and it records the save two ways: the rows it touched carry the
application's software tag, and the calls that made them are appended to
``specimens.py`` beside the table (HUB_PLAN §3: results written to MagIC
tables carry the method codes and the software tag; a script is written
beside every export).

The views supply the writer and the lines of code the writer stands for;
nothing here knows which experiment type they came from.
"""
from __future__ import annotations

import html
import os
from typing import Callable, Optional

import numpy as np
import pandas as pd
import panel as pn

from pmagpy_panel import code
from pmagpy_panel.theme import MUTED_STYLE
from .session import APP, Session

TABLE = "specimens"
SCRIPT = "specimens.py"
OK_COLOR = "#2e7d32"
FAIL_COLOR = "#b00"


def changed_rows(before: pd.DataFrame, after: pd.DataFrame) -> np.ndarray:
    """Boolean mask over `after`: the rows a writer added or altered.

    A specimens table read from disk holds text; a writer coerces the columns
    it fills to numbers, so cells are compared as numbers where both sides
    parse as one (``'0.0500'`` and ``0.05`` are the same value) and as
    stripped text otherwise, with every kind of blank counted as equal.
    Rows beyond the end of `before` are new.
    """
    n = len(before)
    touched = np.ones(len(after), dtype=bool)
    if n == 0:
        return touched
    head = after.iloc[:n]
    same = np.ones(n, dtype=bool)
    for column in after.columns:
        b = head[column]
        a = before[column] if column in before.columns else pd.Series([np.nan] * n, index=before.index)
        a_num, b_num = pd.to_numeric(a, errors="coerce").to_numpy(dtype=float), \
            pd.to_numeric(b, errors="coerce").to_numpy(dtype=float)
        a_txt = a.astype(object).where(a.notna(), "").astype(str).str.strip().to_numpy()
        b_txt = b.astype(object).where(b.notna(), "").astype(str).str.strip().to_numpy()
        numeric = np.isfinite(a_num) & np.isfinite(b_num)
        equal = np.where(numeric, np.isclose(a_num, b_num, rtol=1e-9, atol=0, equal_nan=True), a_txt == b_txt)
        same &= equal
    touched[:n] = ~same
    return touched


class SpecimenSave:
    """The "Save to specimens.txt" step under a view's result.

    A view calls :meth:`reset` whenever its result changes and :meth:`offer`
    when there is a result to save, passing the writer as a function of the
    specimens table and the lines of code that stand for it. The button then
    runs :meth:`save`, which reports what it did in the note and puts the
    save's lines under the view's analysis in the "show code" block.

    In a notebook (a session over a DataFrame, with no directory) there is
    nothing to write to, so the block explains that and stays disabled.
    """

    def __init__(self, session: Session, code_pane: code.CodePane, what: str):
        self.s = session
        self.code = code_pane
        self.what = what                          # "hysteresis parameters", "Bcr", ... for the note and the script
        self.button = pn.widgets.Button(name="Save to specimens.txt", button_type="primary", width=170,
                                        margin=(10, 5, 5, 10))
        self.note = pn.pane.HTML("", sizing_mode="stretch_width", margin=(14, 0, 0, 6))
        self.update: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None
        self.lines: list = []
        self.analysis: list = []
        self.written: Optional[str] = None        # the path of the last table written
        self.button.on_click(lambda e: self.save())
        self.reset()

    # ----- the offer ------------------------------------------------------------
    @property
    def project(self):
        return self.s.project

    def reset(self) -> None:
        """No result to save: the button waits."""
        self.update = None
        self.lines = []
        self.analysis = []
        self.written = None
        self.button.disabled = True
        self.note.object = ""

    def offer(self, update: Callable[[pd.DataFrame], pd.DataFrame], lines: list, analysis: list) -> None:
        """A result is ready: `update(specimens)` returns the table with it written in;
        `lines` are the writer call(s) that `update` stands for and `analysis` the
        view's current code, which the save's lines are shown under.
        """
        self.update, self.lines, self.analysis = update, list(lines), list(analysis)
        self.written = None
        problem = self.problem()
        self.button.disabled = problem is not None
        self.note.object = f'<span style="{MUTED_STYLE}">{problem}</span>' if problem else ""

    def problem(self) -> Optional[str]:
        """Why a save cannot happen here, or None when it can."""
        if self.project is None:
            return "in a notebook, run the writer on your specimens table (see the code) — the app saves into a directory"
        if self.project.table(TABLE) is None:
            return (f"no specimens.txt in {os.path.basename(self.project.directory)} — describe the specimens on the "
                    "Metadata page first, then the results have a row to go to")
        return None

    # ----- the save -------------------------------------------------------------
    def save_lines(self) -> list:
        """The save as notebook lines: read the table, run the writer(s), write the table back."""
        return ["", f"specimens = contribution.tables['{TABLE}'].df", *self.lines,
                f"contribution.tables['{TABLE}'].df = specimens",
                code.call(f"contribution.tables['{TABLE}'].write_magic_file", dir_path=self.project.directory)]

    def save(self) -> Optional[str]:
        """Write the result into ``specimens.txt``; returns the path written, or None with the note saying why not."""
        if self.update is None or self.problem() is not None:
            return None
        project = self.project
        before = project.table(TABLE)
        try:
            after = self.update(before.copy())
        except (ValueError, KeyError) as ex:
            self._say(f"Not saved: {html.escape(str(ex))}", FAIL_COLOR)
            return None
        after = after.reset_index(drop=True)
        touched = changed_rows(before, after)
        if "software_packages" not in after.columns:
            after["software_packages"] = np.nan
        after["software_packages"] = after["software_packages"].astype(object)
        after.loc[touched, "software_packages"] = project.software_tag
        backed_up = project.backup_originals(project.directory, [TABLE + ".txt"])
        path = project.write_table(after, TABLE, project.directory)
        project.contribution.add_magic_table(TABLE)                        # the in-memory table follows the file
        lines = self.analysis + self.save_lines()
        script = self.append_script(lines)
        self.code.set(lines)
        self.written = path
        n_new = int(touched[len(before):].sum())
        n_changed = int(touched[:len(before)].sum())
        parts = [f"{n_changed} row{'s' if n_changed != 1 else ''} updated"] if n_changed else []
        parts += [f"{n_new} row{'s' if n_new != 1 else ''} added"] if n_new else []
        text = f"{self.what} written to specimens.txt ({', '.join(parts) or 'nothing changed'}) · calls appended to {SCRIPT}"
        if backed_up:
            text += f" · original kept in {project.backup_dir_name()}/"
        self._say(text, OK_COLOR)
        return path

    def append_script(self, lines: list) -> str:
        """Add this save's calls to ``specimens.py`` beside the table: a replayable record of every save."""
        target = os.path.join(self.project.directory, SCRIPT)
        block = code.script([f"# ----- {self.what}: {self.s.specimen}"] + lines)
        exists = os.path.exists(target)
        with open(target, "a" if exists else "w", encoding="utf-8") as f:
            if not exists:
                f.write(code.HEADER.format(app=APP.name, what="specimens.txt") + "\n")
            f.write("\n" + block)
        return target

    def _say(self, text: str, color: str) -> None:
        self.note.object = f'<div style="color:{color};font-size:0.85rem">{text}</div>'

    # ----- layout ---------------------------------------------------------------
    def panel(self) -> pn.Row:
        return pn.Row(self.button, self.note, sizing_mode="stretch_width")
