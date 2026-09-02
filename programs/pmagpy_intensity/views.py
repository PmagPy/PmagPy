"""
The panes of PmagPy Intensity. Each view owns its widgets and figures, reads
and mutates the shared :class:`Session`, and redraws when the session changes.

Nothing here computes a statistic: every number shown comes from
``pmagpy.pint_stats`` through ``pmagpy.paleointensity``, so a table and a plot
can never disagree.
"""
from __future__ import annotations

import io
import math
import os
import threading
from typing import Optional

import numpy as np
import pandas as pd
import panel as pn
from bokeh.models.widgets.tables import HTMLTemplateFormatter

import pmagpy.paleointensity as pint
from pmagpy import bicep as bicep_core
from pmagpy import pint_stats as ps
from pmagpy import tdt as tdt_reader

from pmagpy_panel.chooser import DirectoryChooser, shorten
from pmagpy_panel.widgets import HeightSplitter, Hotkeys
from pmagpy_panel.theme import (ACCENT, BUTTON_GROUP_CSS, CHECKBOX_CSS, INPUT_CSS, KPI_ITEM,
                                MUTED_STYLE, SECTION_STYLE, STATS_TABLE_CSS, TABLE_ROW_CSS, kpi)
from . import publication as pub
from .plots import (AraiPlot, ChecksPlot, DecayPlot, GroupPlot, SpecimenZijderveldPlot,
                    StepNetPlot)
from .session import AUTOSAVE_NAME, RECENT_FILE, REDO_NAME, SESSION_NAME, Session, env

#: The four companion figures are a 2 x 2 block beside the Arai plot, and a
#: block only reads as one if its tiles line up. Each figure declares what it
#: needs around its frame (``CHROME_W``/``CHROME_H``), so a tile is defined by
#: its *outer* width and the frame is worked back from it.
TILE = 240                 # outer width of one companion tile
SHORT = 0.62               # the decay and check tiles are wider than they are tall


def tile_frames(tile: int = TILE) -> dict:
    """Frame sizes giving the four companions the same outer width ``tile``."""
    short = max(96, round(tile * SHORT))
    return {"zij": tile - SpecimenZijderveldPlot.CHROME_W,
            "net": tile,                       # net_figure's outer size *is* its size
            "decay": (tile - DecayPlot.CHROME_W, short),
            "checks": (tile - ChecksPlot.CHROME_W, short)}


def captioned(caption: str, fig, width: int = TILE) -> pn.Column:
    """A figure under a small heading.

    Outside the figure rather than as a Bokeh title, because ``net_figure``
    keeps a net circular by having no title row at all -- see the toolkit's
    note there. Doing it the same way for all four keeps the block aligned.
    """
    label = pn.pane.HTML(f'<div style="{SECTION_STYLE};margin:0">{caption}</div>',
                         width=width, height=16, margin=(0, 0, 1, 2))
    return pn.Column(label, fig, width=width, margin=(0, 0, 6, 0))


PASS_COLOR = "#1a7f5a"
FAIL_COLOR = "#c0392b"
NA_COLOR = "#6b7280"

#: Tabulator's group rows default to a heavy grey bar; these are section
#: headings, so they get the same small capitals as every other heading here
GROUP_HEADER_CSS = f"""
.tabulator-row.tabulator-group {{ background: #ffffff !important; border-bottom: 1px solid #d0d4da;
    border-top: none; padding: 9px 4px 3px 4px; font-weight: 600; font-size: 0.82rem;
    letter-spacing: .01em; color: {ACCENT}; }}
.tabulator-row.tabulator-group:hover {{ background: #ffffff !important; }}
.tabulator-row.tabulator-group span {{ color: #6b7280; font-weight: 400; }}
"""


def next_tick(fn):
    """Run ``fn`` under the Bokeh document lock (immediately when not serving)."""
    doc = pn.state.curdoc
    if doc is not None and getattr(doc, "session_context", None) is not None:
        doc.add_next_tick_callback(fn)
    else:
        fn()


def _clip(text: str, width: int) -> str:
    """A message short enough for one line, keeping the start that names the problem."""
    return text if len(text) <= width else text[:width - 1] + "…"


def _stat_html(stat: ps.Stat, decimals: Optional[int] = None) -> str:
    """A statistic at the precision SPD asks for, or the reason it has no value."""
    if stat is None:
        return f'<span style="color:{NA_COLOR}">—</span>'
    if stat.is_value:
        return stat.rounded(decimals)
    tip = stat.reason.replace('"', "'")
    return f'<span style="color:{NA_COLOR}" title="{tip}">{stat.text()}</span>'


class LazyView:
    """A tab that only redraws while it is the visible one."""

    def __init__(self):
        self.active = False
        self._pending = True          # nothing has been drawn yet

    def _lazy_redraw(self, *events):
        if self.active:
            self.redraw()
        else:
            self._pending = True

    def set_active(self, active: bool):
        self.active = active
        if active and self._pending:
            self._pending = False
            self.redraw()


# ---------------------------------------------------------------------------
# Choosing a dataset
# ---------------------------------------------------------------------------
class DataView(DirectoryChooser):
    """Switch between MagIC directories, and import ThellierTool files.

    The widgets and the behaviour are the toolkit's
    :class:`~pmagpy_panel.chooser.DirectoryChooser`, shared with the hub and
    PmagPy Directions; what this adds is what the application counts, what the
    dialog says, and the ``.tdt`` importer, which is this subject's own.
    """

    def __init__(self, session: Session, chooser=None, chooser_available=None):
        super().__init__(
            session, recent_file=RECENT_FILE, chooser=chooser,
            chooser_available=chooser_available, chooser_stub=env("CHOOSER_STUB"),
            count=lambda s: f"{len(s.data.specimens) if s.data else 0} specimens",
            note=("Interpretations are auto-saved per dataset; switching datasets restores "
                  "what you had there."))
        self.tdt_path = pn.widgets.TextInput(
            name="ThellierTool .tdt file or a directory of them", sizing_mode="stretch_width")
        self.tdt_units = pn.widgets.Select(name="moment units", options=["Am^2", "emu", "mA/m"],
                                           width=120)
        self.tdt_volume = pn.widgets.FloatInput(name="volume (cc)", value=12.0, width=110)
        self.tdt_dec = pn.widgets.FloatInput(name="lab field dec", value=0.0, width=110)
        self.tdt_inc = pn.widgets.FloatInput(name="lab field inc", value=90.0, width=110)
        self.tdt_aniso = pn.widgets.Checkbox(name="import an embedded .8n anisotropy block",
                                             value=False)
        self.check_btn = pn.widgets.Button(name="Check", button_type="primary", width=110)
        self.convert_btn = pn.widgets.Button(name="Convert and open", button_type="success",
                                             width=170, disabled=True)
        self.tdt_report = pn.pane.HTML("", sizing_mode="stretch_width")
        self.tdt_table = pn.widgets.Tabulator(pd.DataFrame(), height=220, disabled=True,
                                              sizing_mode="stretch_width", show_index=False)
        self.check_btn.on_click(self._check_tdt)
        self.convert_btn.on_click(self._convert_tdt)

    # ----- ThellierTool import ---------------------------------------------
    def _tdt_files(self):
        target = self.tdt_path.value.strip()
        if not target:
            return []
        return tdt_reader.find_tdt_files(target)

    def _check_tdt(self, event=None):
        files = self._tdt_files()
        if not files:
            self.tdt_report.object = (f'<div style="color:{FAIL_COLOR}">no .tdt file at '
                                      f'{self.tdt_path.value!r}</div>')
            self.convert_btn.disabled = True
            return
        issues, protocols = [], {}
        for path in files:
            parsed = tdt_reader.read(path)
            issues.extend(tdt_reader.validate(parsed, volume_cc=self.tdt_volume.value,
                                              moment_units=self.tdt_units.value))
            protocols[os.path.basename(path)] = parsed.protocol()
        counts = tdt_reader.summarise(issues)
        self.tdt_table.value = tdt_reader.issues_frame(issues)
        colour = PASS_COLOR if counts["ok"] else FAIL_COLOR
        listed = ", ".join(f"{k} ({v})" for k, v in list(protocols.items())[:6])
        self.tdt_report.object = (
            f'<div style="color:{colour}"><b>{len(files)} file(s)</b>: {counts["errors"]} errors, '
            f'{counts["warnings"]} warnings, {counts["notes"]} notes</div>'
            f'<div style="{MUTED_STYLE}">{listed}</div>')
        self.convert_btn.disabled = not counts["ok"]

    def _convert_tdt(self, event=None):
        files = self._tdt_files()
        if not files:
            return
        target = self.tdt_path.value.strip()
        out = os.path.join(target if os.path.isdir(target) else os.path.dirname(target), "magic3")
        result = tdt_reader.to_magic(files, out, volume_cc=self.tdt_volume.value,
                                     moment_units=self.tdt_units.value,
                                     lab_dec=self.tdt_dec.value, lab_inc=self.tdt_inc.value,
                                     import_anisotropy=self.tdt_aniso.value)
        if not result["ok"]:
            self.tdt_report.object = (f'<div style="color:{FAIL_COLOR}">conversion refused; '
                                      f'fix the errors above</div>')
            return
        self.path.value = out
        self.load()

    # ----- layout -----------------------------------------------------------
    def modal(self, *extra, width: int = 760):
        importer = pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Import ThellierTool (.tdt) files</div>'),
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">Every file is checked before anything is '
                         f'written: the table lists each problem with the line it is on.</div>'),
            self.tdt_path,
            pn.Row(self.tdt_units, self.tdt_volume, self.tdt_dec, self.tdt_inc),
            self.tdt_aniso, pn.Row(self.check_btn, self.convert_btn), self.tdt_report,
            self.tdt_table, sizing_mode="stretch_width")
        return super().modal(importer, *extra, width=width)


# ---------------------------------------------------------------------------
# Specimen
# ---------------------------------------------------------------------------
class SpecimenView:
    """One specimen: the Arai plot and its companions, the bounds and the result."""

    COMPANION_GAP = 10

    def __init__(self, session: Session):
        self.s = session
        self.arai = AraiPlot()
        frames = tile_frames()
        self.zij = SpecimenZijderveldPlot(frames["zij"])
        self.net = StepNetPlot(frames["net"])
        self.decay = DecayPlot(*frames["decay"])
        self.checks = ChecksPlot(*frames["checks"])
        # one block, built here so that it exists before main() is asked for it
        self.tiles = [captioned("Zijderveld", self.zij.fig),
                      captioned("Equal area", self.net.fig),
                      captioned("NRM and pTRM", self.decay.fig),
                      captioned("Alteration checks", self.checks.fig)]
        self.companions = pn.GridBox(*self.tiles, ncols=2,
                                     width=2 * TILE + self.COMPANION_GAP)
        self.arai.on_select(self._on_plot_select)

        self.chooser = pn.widgets.Select(name="Specimen", options=[], sizing_mode="stretch_width")
        self.prev_btn = pn.widgets.Button(name="◀", width=44)
        self.next_btn = pn.widgets.Button(name="▶", width=44)
        self.prev_btn.on_click(lambda e: self.s.step_specimen(-1))
        self.next_btn.on_click(lambda e: self.s.step_specimen(1))
        self.chooser.param.watch(lambda e: setattr(self.s, "specimen", e.new), "value")

        self.tmin = pn.widgets.Select(name="from", options={}, width=130)
        self.tmax = pn.widgets.Select(name="to", options={}, width=130)
        self.tmin.param.watch(self._on_bound, "value")
        self.tmax.param.watch(self._on_bound, "value")
        self.auto_btn = pn.widgets.Button(name="Auto", button_type="primary", width=80)
        self.clear_btn = pn.widgets.Button(name="Clear", width=80)
        self.flag_btn = pn.widgets.Button(name="Toggle good/bad", button_type="warning", width=150)
        self.auto_btn.on_click(self._auto)
        self.clear_btn.on_click(lambda e: self.s.delete_interpretation())
        self.flag_btn.on_click(lambda e: self.s.toggle_quality())
        self.copy_level = pn.widgets.Select(name="copy bounds to", width=130,
                                            options={"sample": "sample", "site": "site",
                                                     "whole study": "study"})
        self.copy_btn = pn.widgets.Button(name="Copy", width=80)
        self.copy_btn.on_click(self._copy)
        self.normalize = pn.widgets.Checkbox(name="normalise by NRM", value=True)
        self.show_checks = pn.widgets.Checkbox(name="show checks", value=True)
        self.normalize.link(self.s, value="normalize")
        self.show_checks.link(self.s, value="show_checks")

        self.steps = pn.widgets.Tabulator(
            pd.DataFrame(), height=340, show_index=False, sizing_mode="stretch_width",
            disabled=True, selectable=1, theme="simple", stylesheets=[TABLE_ROW_CSS],
            titles={"step": "", "label": "step", "kind": "type", "moment": "moment",
                    "dec": "dec", "inc": "inc", "quality": ""})
        self.steps.on_click(self._on_step_click)
        self.step_help = pn.pane.HTML(
            f'<div style="{MUTED_STYLE}">Click a step to move the nearer bound; the ⨯ button '
            f'flags a measurement bad. Flagging one half of a Z/I pair removes the whole Arai '
            f'point, and the consequence is reported here.</div>', sizing_mode="stretch_width")
        self.flag_step = pn.widgets.Button(name="Flag the selected step bad/good", width=250)
        self.flag_step.on_click(self._flag_step)
        self.notes = pn.pane.HTML("", sizing_mode="stretch_width")
        self.header = pn.pane.HTML("", sizing_mode="stretch_width")
        self.result = pn.pane.HTML("", sizing_mode="stretch_width")
        self.size = pn.widgets.IntSlider(name="plot size", start=280, end=620,
                                         value=AraiPlot.FRAME, step=10, width=200)
        self.size.param.watch(self._on_size, "value_throttled")
        self.hotkeys = Hotkeys()
        self.hotkeys.param.watch(self._on_hotkey, "n")

        session.param.watch(self._sync, ["specimen", "version", "directory", "normalize",
                                         "show_checks", "criteria_name", "add_ziggie"])
        self._sync()

    # ----- events -----------------------------------------------------------
    def _on_size(self, event):
        frame = int(event.new)
        self.arai.set_frame(frame)
        tile = max(180, round(frame * TILE / AraiPlot.FRAME))
        frames = tile_frames(tile)
        self.zij.set_size(frames["zij"])
        self.net.set_size(frames["net"])
        self.decay.set_size(*frames["decay"])
        self.checks.set_size(*frames["checks"])
        for column in self.tiles:
            column.width = column[0].width = tile
        self.companions.width = 2 * tile + self.COMPANION_GAP
        self.redraw()

    def _on_bound(self, event):
        if self._updating or not self.s.ready:
            return
        lo, hi = self.tmin.value, self.tmax.value
        if lo is None or hi is None:
            return
        self.s.set_bounds(min(lo, hi), max(lo, hi))

    def _on_plot_select(self, indices):
        if not self.s.ready or not indices:
            return
        if len(indices) >= 2:
            self.s.set_bounds(min(indices), max(indices))
        else:
            self.s.move_nearest_bound(int(indices[0]))

    def _on_step_click(self, event):
        if not self.s.ready:
            return
        frame = self.steps.value
        if event.row is None or event.row >= len(frame):
            return
        row = frame.iloc[event.row]
        index = row.get("_arai")
        if index is not None and index == index and index >= 0:
            self.s.move_nearest_bound(int(index))

    def _flag_step(self, event=None):
        if not self.s.ready:
            return
        selection = self.steps.selection
        if not selection:
            self.notes.object = (f'<div style="{MUTED_STYLE}">Select a step in the table '
                                 f'first.</div>')
            return
        frame = self.steps.value
        sequence = int(frame.iloc[selection[0]]["_sequence"])
        flag, notes = self.s.toggle_step(sequence)
        text = "; ".join(notes) if notes else "no other step was affected"
        self.notes.object = (f'<div style="{MUTED_STYLE}">measurement marked '
                             f'<b>{"bad" if flag == "b" else "good"}</b>: {text}</div>')

    def _auto(self, event=None):
        if not self.s.ready:
            return
        interp = self.s.data.auto_interpret(self.s.specimen)
        self.s._changed()
        if interp is not None:
            self.notes.object = f'<div style="{MUTED_STYLE}">{interp.notes}</div>'

    def _copy(self, event=None):
        copied, skipped = self.s.copy_bounds(self.copy_level.value)
        text = f"copied to {copied} specimen(s)"
        if skipped:
            text += f"; skipped {len(skipped)}: " + "; ".join(skipped[:3])
        self.notes.object = f'<div style="{MUTED_STYLE}">{text}</div>'

    def _on_hotkey(self, event):
        key = self.hotkeys.key
        if key == "ArrowLeft":
            self.s.step_specimen(-1)
        elif key == "ArrowRight":
            self.s.step_specimen(1)
        elif key == "[":
            self.s.nudge("min", -1)
        elif key == "]":
            self.s.nudge("min", 1)
        elif key == "{":
            self.s.nudge("max", -1)
        elif key == "}":
            self.s.nudge("max", 1)

    # ----- drawing ----------------------------------------------------------
    _updating = False

    def _sync(self, *events):
        names = self.s.param.specimen.objects
        if list(self.chooser.options) != list(names):
            self.chooser.options = list(names)
        if self.chooser.value != self.s.specimen:
            self.chooser.value = self.s.specimen
        self.redraw()

    def redraw(self, *events):
        if not self.s.ready:
            self.header.object = "<i>no specimen</i>"
            return
        spec, bounds = self.s.spec, self.s.bounds()
        stats = self.s.statistics()
        self.arai.update(spec, bounds, stats, normalize=self.s.normalize,
                         show_checks=self.s.show_checks)
        self.zij.update(spec, bounds)
        self.net.update(spec, bounds, stats)
        self.decay.update(spec, bounds)
        self.checks.update(spec, bounds)
        self._fill_steps(spec, bounds)
        self._fill_bound_widgets(spec, bounds)
        self._fill_header(spec)
        self._fill_result(stats)

    def _fill_steps(self, spec, bounds):
        arai = spec.arai
        inside = set(range(bounds[0], bounds[1] + 1)) if bounds else set()
        temp_to_index = {float(t): i for i, t in enumerate(arai.temps)} if arai else {}
        rows = []
        for _, step in spec.steps.iterrows():
            index = temp_to_index.get(float(step["treat_temp"]), -1)
            marker = "●" if index in inside else ""
            rows.append({"_sequence": int(step["sequence"]), "_arai": index,
                         "step": marker, "label": step["label"],
                         "kind": pint.STEP_LABELS.get(step["kind"], step["kind"]),
                         "moment": f'{step["moment"]:.3e}',
                         "dec": f'{step["dec"]:.1f}', "inc": f'{step["inc"]:.1f}',
                         "quality": "" if step["quality"] == "g" else "⨯"})
        frame = pd.DataFrame(rows)
        self.steps.value = frame
        self.steps.hidden_columns = ["_sequence", "_arai"]

    def _fill_bound_widgets(self, spec, bounds):
        options = {f"{t - pint.KELVIN_OFFSET:.0f}°C": i for i, t in enumerate(spec.arai.temps)}
        if spec.arai.steps and spec.arai.steps[0] == "NRM":
            options = {("NRM" if i == 0 else k): i for i, (k, v) in enumerate(options.items())}
        self._updating = True
        try:
            self.tmin.options = options
            self.tmax.options = options
            if bounds:
                self.tmin.value, self.tmax.value = bounds
        finally:
            self._updating = False

    def _fill_header(self, spec):
        items = [f"<b>{spec.name}</b>",
                 f'<span style="{MUTED_STYLE}">{spec.sample} · {spec.site}</span>',
                 f'<span style="{MUTED_STYLE}">{spec.arai.protocol}</span>',
                 f'<span style="{MUTED_STYLE}">B<sub>lab</sub> {spec.blab_uT:.0f} µT</span>',
                 f'<span style="{MUTED_STYLE}">{spec.arai.n} Arai points</span>']
        if spec.arai.dropped:
            items.append(f'<span style="color:{FAIL_COLOR}" title="'
                         f'{"; ".join(spec.arai.dropped)}">{len(spec.arai.dropped)} note(s)</span>')
        self.header.object = kpi(items)

    def _fill_result(self, stats):
        res = self.s.result
        if res is None:
            self.result.object = (f'<div style="{MUTED_STYLE}">No interpretation: click two '
                                  f'steps on the Arai plot, or press Auto.</div>')
            return
        verdict = ("<span style='color:%s'><b>%s</b></span>" %
                   (PASS_COLOR if res.passed else FAIL_COLOR,
                    "passes " + self.s.data.criteria.name if res.passed
                    else "fails " + self.s.data.criteria.name)) if res.passed is not None else ""
        headline = [f"<b>{res.b_anc:.1f} ± {res.sigma:.1f} µT</b>" if np.isfinite(res.b_anc)
                    else "<b>no estimate</b>",
                    f'<span style="{MUTED_STYLE}">uncorrected {res.b_anc_uncorrected:.1f} µT</span>'
                    if res.corrected else "",
                    f'<span style="{MUTED_STYLE}">n = {stats["n"].text("{:.0f}")}</span>',
                    f'<span style="{MUTED_STYLE}">β {_stat_html(stats.get("beta"))}</span>',
                    f'<span style="{MUTED_STYLE}">FRAC {_stat_html(stats.get("FRAC"))}</span>',
                    f'<span style="{MUTED_STYLE}">k′ {_stat_html(stats.get("k_prime"))}</span>',
                    f'<span style="{MUTED_STYLE}">MAD {_stat_html(stats.get("MAD_Free"))}</span>',
                    f'<span style="{MUTED_STYLE}">DANG {_stat_html(stats.get("DANG"))}</span>',
                    f'<span style="{MUTED_STYLE}">SCAT {_stat_html(stats.get("SCAT"))}</span>',
                    verdict]
        html = kpi([i for i in headline if i])
        if res.failures:
            html += (f'<div style="color:{FAIL_COLOR};font-size:0.85rem">fails: '
                     f'{"; ".join(res.failures)}</div>')
        applied = [f"{k} ×{c.factor:.3f}" for k, c in res.corrections.items() if c.applied]
        if applied:
            html += f'<div style="{MUTED_STYLE}">corrections: {", ".join(applied)}</div>'
        self.result.object = html

    # ----- layout -----------------------------------------------------------
    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Specimen</div>'),
            pn.Row(self.prev_btn, self.chooser, self.next_btn),
            pn.Row(self.tmin, self.tmax),
            pn.Row(self.auto_btn, self.clear_btn, self.flag_btn),
            pn.Row(self.copy_level, self.copy_btn),
            pn.Row(self.normalize, self.show_checks, stylesheets=[CHECKBOX_CSS]),
            self.size,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Steps</div>'),
            self.steps, self.flag_step, self.step_help, self.notes,
            self.hotkeys, sizing_mode="stretch_width")

    def main(self):
        """The Arai plot, and the four companions as one 2 x 2 block beside it.

        The block is one flex item with a width of its own, rather than four
        figures in a column -- which is what a plain Row gave, a thousand pixels
        of companions against five hundred of Arai plot, three of them below the
        fold.

        Together they need about 910 px, which is what a 1440-wide laptop has
        left beside the side column. Narrower than that and the pane scrolls
        horizontally: Bokeh sizes each container to its content and writes the
        result in pixels, so a flex box inside it never re-measures and CSS
        wrapping does not fire. The three things that do adapt are the drag
        handle, the plot-size slider (which scales the block with the Arai
        plot) and the browser's own zoom.
        """
        figures = pn.FlexBox(self.arai.fig, self.companions, flex_wrap="wrap",
                             align_items="flex-start", gap=f"{self.COMPANION_GAP}px",
                             styles={"width": "100%", "min-width": "0"})
        return pn.Column(self.header, figures, self.result, sizing_mode="stretch_width",
                         styles={"min-width": "0", "align-self": "stretch"})


# ---------------------------------------------------------------------------
# Interpretations
# ---------------------------------------------------------------------------
class InterpretationsView(LazyView):
    """Every interpretation in the study, with bulk actions."""

    COLUMNS = ["specimen", "sample", "site", "Tmin", "Tmax", "n", "B (µT)", "± µT",
               "uncorrected", "β", "FRAC", "k′", "MAD", "DANG", "SCAT", "corrections",
               "quality", "verdict", "why"]

    def __init__(self, session: Session):
        super().__init__()
        self.s = session
        self.on_goto = None
        self.table = pn.widgets.Tabulator(
            pd.DataFrame(columns=self.COLUMNS), pagination="local", page_size=25,
            header_filters=True, show_index=False, disabled=True, selectable="checkbox",
            sizing_mode="stretch_width", height=560, theme="simple",
            stylesheets=[TABLE_ROW_CSS, STATS_TABLE_CSS])
        self.goto_btn = pn.widgets.Button(name="Go to specimen", button_type="primary", width=150)
        self.flag_btn = pn.widgets.Button(name="Flag good/bad", button_type="warning", width=140)
        self.delete_btn = pn.widgets.Button(name="Delete", button_type="danger", width=110)
        self.auto_btn = pn.widgets.Button(name="Auto-interpret all", button_type="primary",
                                          width=180)
        self.auto_selected = pn.widgets.Button(name="Auto-interpret selected", width=200)
        self.progress = pn.indicators.Progress(value=0, max=100, sizing_mode="stretch_width",
                                               visible=False)
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.goto_btn.on_click(self._goto)
        self.flag_btn.on_click(self._flag)
        self.delete_btn.on_click(self._delete)
        self.auto_btn.on_click(lambda e: self._auto(None))
        self.auto_selected.on_click(lambda e: self._auto(self._selected()))
        session.param.watch(self._lazy_redraw, ["version", "directory", "criteria_name",
                                                "add_ziggie"])

    def _selected(self):
        frame = self.table.value
        return [frame.iloc[i]["specimen"] for i in self.table.selection if i < len(frame)]

    def _goto(self, event=None):
        names = self._selected()
        if names:
            self.s.go_to(names[0])
            if self.on_goto:
                self.on_goto()

    def _flag(self, event=None):
        for name in self._selected():
            self.s.toggle_quality(name)

    def _delete(self, event=None):
        for name in self._selected():
            self.s.delete_interpretation(name)

    def _auto(self, names):
        targets = names if names else self.s.data.specimen_names
        self.progress.visible = True
        self.message.object = f'<div style="{MUTED_STYLE}">interpreting {len(targets)} specimens…</div>'
        doc = pn.state.curdoc

        def worker():
            def report(fraction, name):
                def apply():
                    self.progress.value = int(100 * fraction)
                if doc is not None and getattr(doc, "session_context", None) is not None:
                    doc.add_next_tick_callback(apply)
                else:
                    apply()
            out = self.s.auto_interpret(targets, progress=report)

            def done():
                self.progress.visible = False
                passed = sum(1 for n in out if self.s.data.result(n) is not None
                             and self.s.data.result(n).passed)
                self.message.object = (f'<div style="{MUTED_STYLE}">interpreted {len(out)} '
                                       f'specimens; {passed} pass '
                                       f'{self.s.data.criteria.name}</div>')
                self.redraw()
            if doc is not None and getattr(doc, "session_context", None) is not None:
                doc.add_next_tick_callback(done)
            else:
                done()
        threading.Thread(target=worker, daemon=True).start()

    def redraw(self, *events):
        if self.s.data is None:
            return
        rows = []
        for res in self.s.data.results():
            stats = res.stats
            rows.append({
                "specimen": res.specimen, "sample": res.sample, "site": res.site,
                "Tmin": round(res.tmin - pint.KELVIN_OFFSET),
                "Tmax": round(res.tmax - pint.KELVIN_OFFSET),
                "n": int(float(stats["n"])) if stats.get("n") else 0,
                "B (µT)": round(res.b_anc, 1) if np.isfinite(res.b_anc) else None,
                "± µT": round(res.sigma, 1) if np.isfinite(res.sigma) else None,
                "uncorrected": round(res.b_anc_uncorrected, 1)
                if np.isfinite(res.b_anc_uncorrected) else None,
                "β": _round(stats.get("beta"), 3), "FRAC": _round(stats.get("FRAC"), 3),
                "k′": _round(stats.get("k_prime"), 3), "MAD": _round(stats.get("MAD_Free"), 1),
                "DANG": _round(stats.get("DANG"), 1),
                "SCAT": stats["SCAT"].text() if stats.get("SCAT") else "n/a",
                "corrections": ", ".join(k for k, c in res.corrections.items() if c.applied),
                "quality": res.quality,
                "verdict": "pass" if res.passed else ("fail" if res.passed is False else "—"),
                "why": "; ".join(res.failures)[:120]})
        frame = pd.DataFrame(rows, columns=self.COLUMNS)
        self.table.value = frame
        accepted = sum(1 for r in self.s.data.results() if self.s.data.is_accepted(r))
        self.summary.object = kpi([
            f"<b>{len(frame)}</b> interpretations",
            f'<span style="{MUTED_STYLE}">{accepted} accepted under '
            f'{self.s.data.criteria.name}</span>',
            f'<span style="{MUTED_STYLE}">{len(self.s.data.specimens)} specimens in the '
            f'study</span>'])

    def panel(self):
        return pn.Column(self.summary,
                         pn.Row(self.goto_btn, self.flag_btn, self.delete_btn,
                                self.auto_selected, self.auto_btn,
                                stylesheets=[BUTTON_GROUP_CSS]),
                         self.progress, self.message, self.table,
                         sizing_mode="stretch_width")

    def sidebar(self):
        return pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Interpretations</div>'),
                         pn.pane.HTML(f'<div style="{MUTED_STYLE}">Filter with the boxes in the '
                                      f'table header. Tick rows to go to a specimen, flag it, '
                                      f'delete it or re-interpret it.</div>'),
                         self.summary, sizing_mode="stretch_width")


def _round(stat, decimals):
    return round(float(stat), decimals) if (stat is not None and stat.is_value) else None


#: what an analyst looks for first in an exported table, in that order
FRONT_COLUMNS = ("specimen", "sample", "site", "location", "int_abs", "int_abs_sigma",
                 "int_corr", "int_corr_anisotropy", "int_corr_cooling_rate", "int_corr_nlt",
                 "meas_step_min", "meas_step_max", "int_n_measurements", "int_b_beta",
                 "int_frac", "int_scat", "result_quality", "method_codes")


def _front(frame: pd.DataFrame) -> pd.DataFrame:
    """Put the identity and the result first; a table sorted alphabetically opens
    on the anisotropy tensor and hides what the export is actually about."""
    lead = [c for c in FRONT_COLUMNS if c in frame.columns]
    return frame[lead + [c for c in frame.columns if c not in lead]] if lead else frame


# ---------------------------------------------------------------------------
# Criteria and statistics
# ---------------------------------------------------------------------------
class CriteriaView(LazyView):
    """Every statistic for the current specimen, as a table you can sort.

    The statistics used to be a stack of paragraphs, one per statistic, which
    is unreadable at forty-eight of them: you cannot compare two values, and
    finding the ones that failed means reading all of it. They are a table now
    -- sortable, filterable, one line each -- and the prose that belongs to one
    statistic (its definition, its equation, where it comes from, why it has no
    value) is shown for the row you select.
    """

    COLUMNS = ["statistic", "value", "units", "criterion", "verdict", "category", "MagIC column"]
    WIDTHS = {"statistic": 130, "value": 110, "units": 70, "criterion": 120, "verdict": 100}
    #: plain values in the cells so that sorting works; the colour is display only
    VALUE_FORMAT = ('<span style="color:<%= isNaN(parseFloat(value)) ? \'#6b7280\' : \'#111\' %>;'
                    'font-style:<%= isNaN(parseFloat(value)) ? \'italic\' : \'normal\' %>">'
                    '<%= value %></span>')
    VERDICT_FORMAT = ('<span style="font-weight:<%= value === \'fail\' ? 700 : 400 %>;color:'
                      '<%= value === \'pass\' ? \'' + PASS_COLOR + '\' : value === \'fail\' ? \''
                      + FAIL_COLOR + '\' : \'' + NA_COLOR + '\' %>"><%= value %></span>')

    def __init__(self, session: Session):
        super().__init__()
        self.s = session
        self.preset = pn.widgets.Select(name="Criteria set", options=list(pint.CRITERIA_SETS),
                                        value=session.criteria_name,
                                        sizing_mode="stretch_width")
        self.preset.link(session, value="criteria_name")
        # and follow it when something else changes it (loading a dataset picks
        # the study's own criteria table)
        session.param.watch(lambda e: setattr(self.preset, "value", e.new)
                            if e.new in self.preset.options else None, "criteria_name")
        self.ziggie = pn.widgets.Checkbox(
            name=f"add Ziggie ≤ {ps.ZIGGIE_CRITERION} (Tully & Paterson, 2025)", value=False)
        self.ziggie.link(session, value="add_ziggie")
        self.search = pn.widgets.TextInput(name="Search statistics", placeholder="frac, tail, k′…",
                                           sizing_mode="stretch_width")
        self.search.param.watch(lambda e: self.redraw(), "value")
        self.category = pn.widgets.MultiChoice(name="Categories", options=ps.categories(),
                                               value=[], sizing_mode="stretch_width")
        self.category.param.watch(lambda e: self.redraw(), "value")
        self.only_tested = pn.widgets.Checkbox(name="only the ones the criteria test",
                                               value=False)
        self.only_tested.param.watch(lambda e: self.redraw(), "value")
        self.criteria_info = pn.pane.HTML("", sizing_mode="stretch_width")
        self.criteria_table = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, height=260,
                                                   disabled=True, sizing_mode="stretch_width",
                                                   theme="simple", stylesheets=[STATS_TABLE_CSS])
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.table = pn.widgets.Tabulator(
            pd.DataFrame(columns=self.COLUMNS), show_index=False, disabled=True, selectable=1,
            height=560, sizing_mode="stretch_width", theme="simple", layout="fit_data_table",
            widths=self.WIDTHS, text_align={"value": "right", "criterion": "right"},
            formatters={"value": HTMLTemplateFormatter(template=self.VALUE_FORMAT),
                        "verdict": HTMLTemplateFormatter(template=self.VERDICT_FORMAT)},
            # the SPD categories are how the standard organises these, and they
            # are the group headings rather than a column that repeats itself
            groupby=["category"], hidden_columns=["key", "category"],
            stylesheets=[TABLE_ROW_CSS, GROUP_HEADER_CSS])
        self.table.param.watch(lambda e: self._show_detail(), "selection")
        self.detail = pn.pane.HTML("", sizing_mode="stretch_width")
        session.param.watch(self._lazy_redraw, ["specimen", "version", "directory",
                                                "criteria_name", "add_ziggie"])

    # ----- the table --------------------------------------------------------
    def _frame(self, stats, verdict) -> pd.DataFrame:
        query = (self.search.value or "").strip().lower()
        wanted = set(self.category.value)
        by_criterion = {row["key"]: row for row in verdict["rows"]}
        rows = []
        for key, spec in ps.CATALOG.items():
            if key not in stats:
                continue
            if wanted and spec.category not in wanted:
                continue
            if query and query not in (key + spec.label + spec.definition).lower():
                continue
            rule = by_criterion.get(key)
            if self.only_tested.value and rule is None:
                continue
            stat = stats[key]
            rows.append({
                "statistic": spec.label,
                "value": stat.rounded(spec.decimals) if stat.is_value else stat.text(),
                "units": spec.units,
                "criterion": rule["criterion"] if rule else "",
                "verdict": "" if rule is None else (
                    "pass" if rule["pass"] is True else
                    "fail" if rule["pass"] is False else "not tested"),
                "category": spec.category,
                "MagIC column": spec.magic_column,
                "key": key})
        return pd.DataFrame(rows, columns=self.COLUMNS + ["key"])

    def redraw(self, *events):
        if not self.s.ready:
            self.table.value = pd.DataFrame(columns=self.COLUMNS + ["key"])
            self.detail.object = "<i>no specimen</i>"
            return
        criteria = self.s.data.criteria
        self.criteria_info.object = (
            f'<div><b>{criteria.name}</b> — {criteria.description}</div>'
            f'<div style="{MUTED_STYLE}">{criteria.citation}'
            + (f' · <a href="https://doi.org/{criteria.doi}" target="_blank">{criteria.doi}</a>'
               if criteria.doi else "") + "</div>")
        stats = self.s.statistics()
        verdict = criteria.evaluate(stats, "specimen")
        self.criteria_table.value = pd.DataFrame([
            {"criterion": row["criterion"], "value": row["value"].rounded(),
             "result": "pass" if row["pass"] else ("fail" if row["pass"] is False
                                                   else "not tested"),
             "why": "" if row["pass"] is not None else row["value"].reason}
            for row in verdict["rows"]])
        frame = self._frame(stats, verdict)
        keep = self.table.value["key"].iloc[self.table.selection[0]] \
            if self.table.selection and len(self.table.value) else None
        self.table.value = frame
        self.table.selection = ([int(i) for i in frame.index[frame["key"] == keep]][:1]
                                if keep is not None else [])
        self._fill_summary(frame, verdict)
        self._show_detail()

    def _fill_summary(self, frame, verdict):
        tested = frame[frame["verdict"] != ""]
        failed = list(tested[tested["verdict"] == "fail"]["statistic"])
        passed = int((tested["verdict"] == "pass").sum())
        if not len(tested):
            note = f'<span style="{MUTED_STYLE}">this set tests none of these</span>'
        elif failed:
            note = (f'<span style="color:{FAIL_COLOR}">fails {", ".join(failed)}</span>')
        else:
            note = f'<span style="color:{PASS_COLOR}">passes every criterion</span>'
        self.summary.object = kpi([f"<b>{len(frame)}</b> statistics",
                                   f"<b>{passed}</b> of {len(tested)} criteria met", note])

    # ----- the selected statistic ------------------------------------------
    def _show_detail(self):
        frame = self.table.value
        if not len(frame):
            self.detail.object = ""
            return
        if not self.table.selection:
            self.detail.object = (f'<div style="{MUTED_STYLE}">Select a statistic for its '
                                  f'definition, its equation and where it comes from.</div>')
            return
        row = frame.iloc[self.table.selection[0]]
        key = row["key"]
        spec = ps.CATALOG[key]
        stat = self.s.statistics().get(key)
        source = spec.citation + (f' (<a href="https://doi.org/{spec.doi}" target="_blank">'
                                  f'{spec.doi}</a>)' if spec.doi else "")
        # the key is only worth showing when it is not the label already
        named = f"{key} · {spec.category}" if key != spec.label else spec.category
        bits = [f'<div style="{SECTION_STYLE}">{spec.label} <span style="{MUTED_STYLE};'
                f'text-transform:none">{named}</span></div>',
                f"<div>{spec.definition}</div>"]
        if spec.equation:
            bits.append(f'<div style="font-family:ui-monospace,Menlo,monospace;'
                        f'background:#f6f7f9;padding:6px 8px;margin:6px 0;'
                        f'border-radius:4px">{spec.equation}</div>')
        value = (f"{stat.rounded(spec.decimals)}{(' ' + spec.units) if spec.units else ''}"
                 if stat is not None and stat.is_value else
                 f'<span style="color:{NA_COLOR}">{stat.text()} — {stat.reason}</span>'
                 if stat is not None else "—")
        bits.append(f"<div><b>value</b> {value}</div>")
        if row["criterion"]:
            bits.append(f'<div><b>criterion</b> {row["criterion"]} — {row["verdict"]}</div>')
        if spec.magic_column:
            bits.append(f'<div style="{MUTED_STYLE}">MagIC column '
                        f'<code>{spec.magic_column}</code></div>')
        bits.append(f'<div style="{MUTED_STYLE}">{source}</div>')
        self.detail.object = ('<div style="border-left:3px solid ' + ACCENT +
                              ';padding:2px 0 2px 10px">' + "".join(bits) + "</div>")

    def sidebar(self):
        return pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Criteria</div>'),
                         self.preset, self.ziggie, self.criteria_info, self.criteria_table,
                         pn.pane.HTML(f'<div style="{SECTION_STYLE}">Find</div>'),
                         self.search, self.category,
                         pn.Row(self.only_tested, stylesheets=[CHECKBOX_CSS]),
                         sizing_mode="stretch_width")

    def panel(self):
        return pn.Column(self.summary, self.table, self.detail, sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# Corrections
# ---------------------------------------------------------------------------
class CorrectionsView(LazyView):
    """Anisotropy, non-linear TRM and cooling rate, with their provenance."""

    USE = {"use if available": None, "always": True, "never": False}

    def __init__(self, session: Session):
        super().__init__()
        self.s = session
        self.detail = pn.pane.HTML("", sizing_mode="stretch_width")
        self.table = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, pagination="local",
                                          page_size=20, header_filters=True, disabled=True,
                                          sizing_mode="stretch_width", height=460, theme="simple",
                                          stylesheets=[TABLE_ROW_CSS])
        # a plain list of labels: an option whose value is None renders blank
        choices = ["use if available", "always", "never"]
        self.aniso = pn.widgets.Select(name="anisotropy", width=170, options=choices,
                                       value=choices[0])
        self.nlt = pn.widgets.Select(name="non-linear TRM", width=170, options=choices,
                                     value=choices[0])
        self.cooling = pn.widgets.Select(name="cooling rate", width=170, options=choices,
                                         value=choices[0])
        for widget, kind in ((self.aniso, "anisotropy"), (self.nlt, "nlt"),
                             (self.cooling, "cooling_rate")):
            widget.param.watch(lambda e, k=kind: self.s.set_correction(k, self.USE[e.new]),
                               "value")
        self.alt_limit = pn.widgets.FloatInput(name="anisotropy alteration limit (%)",
                                               value=5.0, width=220)
        self.alt_limit.param.watch(self._on_limit, "value")
        self.ftest = pn.widgets.Checkbox(name="require Hext's F-test", value=False)
        self.ftest.param.watch(self._on_ftest, "value")
        session.param.watch(self._lazy_redraw, ["specimen", "version", "directory"])

    def _on_limit(self, event):
        self.s.data.anisotropy_alteration_limit = float(event.new) if event.new else None
        self.s.data.invalidate()
        self.s.version += 1

    def _on_ftest(self, event):
        self.s.data.anisotropy_require_ftest = bool(event.new)
        self.s.data.invalidate()
        self.s.version += 1

    def redraw(self, *events):
        if self.s.data is None:
            return
        self._fill_detail()
        rows = []
        for res in self.s.data.results():
            row = {"specimen": res.specimen, "site": res.site,
                   "uncorrected (µT)": round(res.b_anc_uncorrected, 1)
                   if np.isfinite(res.b_anc_uncorrected) else None,
                   "corrected (µT)": round(res.b_anc, 1) if np.isfinite(res.b_anc) else None,
                   "± µT": round(res.sigma, 1) if np.isfinite(res.sigma) else None}
            for kind, label in (("anisotropy", "anisotropy"), ("nlt", "NLT"),
                                ("cooling_rate", "cooling rate")):
                correction = res.corrections.get(kind)
                if correction is None:
                    row[label] = "—"
                elif correction.applied:
                    row[label] = round(correction.factor, 3)
                else:
                    row[label] = correction.message
            rows.append(row)
        self.table.value = pd.DataFrame(rows)

    def _fill_detail(self):
        if not self.s.ready:
            self.detail.object = ""
            return
        name = self.s.specimen
        res = self.s.result
        blocks = [f'<div style="{SECTION_STYLE}">{name}</div>']
        aniso = self.s.data.anisotropy.get(name)
        if aniso:
            hext = aniso.get("hext") or {}
            tau = hext.get("tau") or []
            blocks.append(
                f"<div><b>{aniso['type']}</b> tensor from the {aniso.get('source', '?')}, "
                f"{aniso.get('n_positions', '?')} positions"
                + (f", alteration {aniso['alteration']:.1f}%"
                   if aniso.get("alteration") is not None and np.isfinite(aniso["alteration"])
                   else ", no alteration check")
                + "</div>"
                + (f'<div style="{MUTED_STYLE}">eigenvalues '
                   f'{", ".join(f"{t:.4f}" for t in tau)}; degree '
                   f'{hext.get("degree", float("nan")):.3f}; F {hext.get("F", float("nan")):.1f} '
                   f'(critical {hext.get("F_crit", float("nan")):.2f})</div>' if tau else "")
                + (f'<div style="{MUTED_STYLE}">also measured: '
                   f'{", ".join(aniso.get("alternatives", {}))}</div>'
                   if aniso.get("alternatives") else ""))
        else:
            blocks.append(f'<div style="{MUTED_STYLE}">no anisotropy experiment</div>')
        nlt = self.s.data.nlt.get(name)
        blocks.append(f"<div><b>non-linear TRM</b>: A1 {nlt['A1']:.3g}, A2 {nlt['A2']:.4g} 1/T "
                      f"from {nlt['n']} field steps</div>" if nlt else
                      f'<div style="{MUTED_STYLE}">no TRM acquisition experiment</div>')
        cooling = self.s.data.cooling_rate.get(name)
        if cooling:
            blocks.append(
                f"<div><b>cooling rate</b>: factor "
                f"{cooling.get('factor', float('nan')):.3f} ({cooling.get('flag', '')})"
                + (f", alteration {cooling['alteration']:.1f}%"
                   if np.isfinite(cooling.get("alteration", np.nan)) else "") + "</div>")
        else:
            blocks.append(f'<div style="{MUTED_STYLE}">no cooling-rate experiment</div>')
        if res is not None:
            for kind, correction in res.corrections.items():
                colour = PASS_COLOR if correction.applied else NA_COLOR
                blocks.append(f'<div style="color:{colour}">{kind}: '
                              f'{"applied ×%.4f" % correction.factor if correction.applied else correction.message}'
                              + (f' <span style="{MUTED_STYLE}">({correction.method_code})</span>'
                                 if correction.method_code else "") + "</div>")
            if np.isfinite(res.b_anc_uncorrected) and np.isfinite(res.b_anc):
                blocks.append(f"<div><b>{res.b_anc_uncorrected:.1f} µT</b> uncorrected → "
                              f"<b>{res.b_anc:.1f} ± {res.sigma:.1f} µT</b> corrected</div>")
        self.detail.object = "".join(blocks)

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">This specimen</div>'), self.detail,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Apply</div>'),
            self.aniso, self.nlt, self.cooling,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Anisotropy policy</div>'),
            self.alt_limit, self.ftest,
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">A tensor whose repeat measurement altered '
                         f'by more than the limit is not applied. With both an ATRM and an AARM '
                         f'tensor the AARM one is used, as the legacy GUI did.</div>'),
            sizing_mode="stretch_width")

    def panel(self):
        return pn.Column(self.table, sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# Group results
# ---------------------------------------------------------------------------
class GroupView(LazyView):
    """Sample, site and location means of the accepted specimens."""

    def __init__(self, session: Session):
        super().__init__()
        self.s = session
        self.level = pn.widgets.RadioButtonGroup(name="level", options=["sample", "site",
                                                                        "location"],
                                                 value="site", button_type="primary")
        self.only_accepted = pn.widgets.Checkbox(name="accepted specimens only", value=True)
        self.corrected_only = pn.widgets.Checkbox(name="corrected specimens only", value=False)
        self.weighted = pn.widgets.Checkbox(name="weighted by 1/σ²", value=False)
        for widget in (self.level, self.only_accepted, self.corrected_only, self.weighted):
            widget.param.watch(lambda e: self.redraw(), "value")
        self.group = pn.widgets.Select(name="Group", options=[], sizing_mode="stretch_width")
        self.group.param.watch(lambda e: self._redraw_plot(), "value")
        self.plot = GroupPlot(520, 300)
        self.table = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, disabled=True,
                                          sizing_mode="stretch_width", height=380, theme="simple",
                                          stylesheets=[TABLE_ROW_CSS])
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.members = pn.pane.HTML("", sizing_mode="stretch_width")
        session.param.watch(self._lazy_redraw, ["version", "directory", "criteria_name",
                                                "add_ziggie"])

    def redraw(self, *events):
        if self.s.data is None:
            return
        level = self.level.value
        frame = self.s.data.group_results(level=level, only_accepted=self.only_accepted.value,
                                          weighted=self.weighted.value,
                                          corrected_only=self.corrected_only.value)
        if len(frame):
            display = frame.copy()
            for column in ("int_abs", "int_abs_sigma", "int_abs_sigma_perc", "dBN_percent"):
                if column in display:
                    display[column] = display[column].round(2)
            if "vadm" in display:
                display["vadm"] = display["vadm"].map(
                    lambda v: f"{v:.2e}" if np.isfinite(v) else "")
            display = display.rename(columns={"int_abs": "B (µT)", "int_abs_sigma": "s (µT)",
                                              "int_abs_sigma_perc": "s (%)",
                                              "dBN_percent": "δB_N (%)",
                                              "n": "N", "corrected": "corrected"})
            self.table.value = display.drop(columns=["specimens"], errors="ignore")
            self.group.options = list(frame[level])
            if self.group.value not in self.group.options:
                self.group.value = self.group.options[0] if self.group.options else None
        else:
            self.table.value = pd.DataFrame()
            self.group.options = []
        criteria = self.s.data.criteria
        if not criteria.site:
            verdict = (f'<span style="{MUTED_STYLE}">{criteria.name} sets no site-level '
                       f'criteria</span>')
        else:
            passed = int((frame["passed"] == True).sum()) if len(frame) and "passed" in frame else 0
            verdict = (f'<span style="{MUTED_STYLE}">{passed} of {len(frame)} pass '
                       f'{criteria.name}: {", ".join(c.describe() for c in criteria.site)}</span>')
        self.summary.object = kpi([
            f"<b>{len(frame)}</b> {level}s", verdict,
            f'<span style="{MUTED_STYLE}">{int(frame["n"].sum()) if len(frame) else 0} specimens '
            f'averaged</span>'])
        self._redraw_plot()

    def _redraw_plot(self):
        if self.s.data is None or not self.group.value:
            self.plot.update([])
            self.members.object = ""
            return
        level, name = self.level.value, self.group.value
        results = [r for r in (self.s.data.result(n)
                               for n in self.s.data.specimens_in(level, name)) if r is not None]
        accepted = {r.specimen for r in results if self.s.data.is_accepted(r)}
        values = [r.b_anc for r in results if r.specimen in accepted and np.isfinite(r.b_anc)]
        stats = ps.group_statistics(values)
        self.plot.update(results, mean=float(stats["mean"]) if stats["mean"] else None,
                         sd=float(stats["sd"]) if stats["sd"] else None, accepted=accepted)
        rejected = [r for r in results if r.specimen not in accepted]
        self.members.object = (
            f"<div><b>{name}</b>: {len(accepted)} accepted, {len(rejected)} rejected</div>"
            + (f'<div style="{MUTED_STYLE}">rejected: '
               f'{", ".join(r.specimen + " (" + (r.failures[0] if r.failures else "flagged bad") + ")" for r in rejected[:6])}</div>'
               if rejected else ""))

    def sidebar(self):
        return pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Group</div>'),
                         self.level, self.only_accepted, self.corrected_only, self.weighted,
                         self.group, self.members, sizing_mode="stretch_width")

    def panel(self):
        return pn.Column(self.summary, self.plot.fig, self.table, sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# BiCEP
# ---------------------------------------------------------------------------
class BicepView(LazyView):
    """Bias Corrected Estimation of Paleointensity, per site."""

    def __init__(self, session: Session):
        super().__init__()
        self.s = session
        self.site = pn.widgets.Select(name="Site", options=[], sizing_mode="stretch_width")
        self.method = pn.widgets.Select(name="Sampler", width=170,
                                        options={"automatic": "auto",
                                                 "Stan (HMC)": "stan",
                                                 "Metropolis-within-Gibbs": "mcmc",
                                                 "bootstrap (approximate)": "bootstrap"})
        self.draws = pn.widgets.IntInput(name="draws", value=2000, start=100, end=20000, width=110)
        self.warmup = pn.widgets.IntInput(name="warm-up", value=1000, start=100, end=20000,
                                          width=110)
        self.chains = pn.widgets.IntInput(name="chains", value=4, start=1, end=8, width=90)
        self.seed = pn.widgets.IntInput(name="seed", value=20210, width=110)
        self.prior = pn.widgets.FloatInput(name="σ_B prior (µT)",
                                           value=bicep_core.SIGMA_B_PRIOR_SD, width=130)
        self.only_accepted = pn.widgets.Checkbox(
            name="only specimens accepted by the criteria", value=False)
        self.run_btn = pn.widgets.Button(name="Run BiCEP", button_type="success", width=140)
        self.cancel_btn = pn.widgets.Button(name="Cancel", button_type="danger", width=100,
                                            disabled=True)
        self.progress = pn.indicators.Progress(value=0, max=100, sizing_mode="stretch_width",
                                               visible=False)
        self.status = pn.pane.HTML("", sizing_mode="stretch_width")
        self.install = pn.pane.HTML("", sizing_mode="stretch_width")
        self.result_pane = pn.pane.HTML("", sizing_mode="stretch_width")
        self.specimens = pn.widgets.Tabulator(pd.DataFrame(), show_index=False,
                                              sizing_mode="stretch_width", height=300,
                                              selectable="checkbox", theme="simple",
                                              stylesheets=[TABLE_ROW_CSS])
        self.exclude_btn = pn.widgets.Button(name="Exclude selected", width=170)
        self.include_btn = pn.widgets.Button(name="Include selected", width=170)
        self.audit = pn.pane.HTML("", sizing_mode="stretch_width")
        self.plot = pn.pane.Matplotlib(height=380, sizing_mode="stretch_width", tight=True)
        self.methods = pn.pane.HTML("", sizing_mode="stretch_width")
        self.save_btn = pn.widgets.Button(name="Save posterior", width=150)
        self.save_msg = pn.pane.HTML("", sizing_mode="stretch_width")
        self.run_btn.on_click(self._run)
        self.cancel_btn.on_click(self._cancel)
        self.save_btn.on_click(self._save)
        self.exclude_btn.on_click(lambda e: self._set_included(False))
        self.include_btn.on_click(lambda e: self._set_included(True))
        self.site.param.watch(lambda e: self.redraw(), "value")
        self._cancelled = False
        self._excluded: dict = {}
        self._audit: list = []
        session.param.watch(self._lazy_redraw, ["version", "directory"])
        self._refresh_install()

    def _refresh_install(self):
        status = bicep_core.stan_status()
        if status["available"]:
            self.install.object = (f'<div style="color:{PASS_COLOR}">Stan is available '
                                   f'(cmdstanpy {status["version"]}, CmdStan at '
                                   f'{shorten(status["cmdstan"] or "", 40)}).</div>')
        else:
            self.install.object = (
                f'<div style="{MUTED_STYLE}">Stan is not installed, so the built-in sampler is '
                f'used instead. It needs nothing extra and gives the same posterior, more '
                f'slowly.<br>To use Stan: <code>{status["hint"]}</code><br>'
                f'({status["reason"]})</div>')

    def _sites(self):
        if self.s.data is None:
            return []
        return [s for s in self.s.data.names_at("site")
                if len([n for n in self.s.data.specimens_in("site", s)
                        if self.s.data.result(n) is not None]) >= 2]

    def _prepare(self):
        site = self.site.value
        if not site or self.s.data is None:
            return []
        rows = []
        for name in self.s.data.specimens_in("site", site):
            res = self.s.data.result(name)
            if res is None:
                continue
            if self.only_accepted.value and not self.s.data.is_accepted(res):
                continue
            spec = self.s.data.specimens[name]
            arai = spec.arai
            rows.append((name, arai.x[res.imin:res.imax + 1], arai.y[res.imin:res.imax + 1],
                         spec.blab_uT))
        prepared = bicep_core.prepare(rows)
        for item in prepared:
            if self._excluded.get((site, item.name)):
                item.included = False
                item.note = self._excluded[(site, item.name)]
        return prepared

    def _set_included(self, included: bool):
        frame = self.specimens.value
        site = self.site.value
        for index in self.specimens.selection:
            if index >= len(frame):
                continue
            name = frame.iloc[index]["specimen"]
            if included:
                self._excluded.pop((site, name), None)
                self._audit.append(f"{site}/{name}: included by the analyst")
            else:
                self._excluded[(site, name)] = "excluded by the analyst"
                self._audit.append(f"{site}/{name}: excluded by the analyst")
        self.redraw()

    def _run(self, event=None):
        prepared = self._prepare()
        if len([p for p in prepared if p.included]) < 2:
            self.status.object = (f'<div style="color:{FAIL_COLOR}">at least two specimens are '
                                  f'needed</div>')
            return
        self._cancelled = False
        self.cancel_btn.disabled = False
        self.run_btn.disabled = True
        self.progress.visible = True
        self.status.object = f'<div style="{MUTED_STYLE}">sampling…</div>'
        doc = pn.state.curdoc
        site = self.site.value

        def worker():
            def report(fraction, message):
                def apply():
                    self.progress.value = int(100 * fraction)
                    self.status.object = f'<div style="{MUTED_STYLE}">{message}</div>'
                if doc is not None and getattr(doc, "session_context", None) is not None:
                    doc.add_next_tick_callback(apply)
                else:
                    apply()
            result = bicep_core.run(prepared, site=site, method=self.method.value,
                                    draws=self.draws.value, warmup=self.warmup.value,
                                    chains=self.chains.value, seed=self.seed.value,
                                    sigma_b_prior_sd=self.prior.value, progress=report,
                                    cancel=lambda: self._cancelled)

            def done():
                self.s.bicep_results[site] = result
                self.progress.visible = False
                self.cancel_btn.disabled = True
                self.run_btn.disabled = False
                self.status.object = f'<div style="color:{PASS_COLOR}">{result.summary()}</div>'
                self.redraw()
            if doc is not None and getattr(doc, "session_context", None) is not None:
                doc.add_next_tick_callback(done)
            else:
                done()
        threading.Thread(target=worker, daemon=True).start()

    def _cancel(self, event=None):
        self._cancelled = True
        self.status.object = f'<div style="{MUTED_STYLE}">cancelling…</div>'

    def _save(self, event=None):
        result = self.s.bicep_results.get(self.site.value)
        if result is None:
            return
        path = os.path.join(self.s.output_dir, f"bicep_{self.site.value}.json")
        try:
            written = bicep_core.save(result, path)
            self.save_msg.object = f'<div style="color:{PASS_COLOR}">saved {written}</div>'
        except OSError as exc:
            self.save_msg.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'

    def redraw(self, *events):
        options = self._sites()
        if list(self.site.options) != options:
            self.site.options = options
            if self.site.value not in options:
                self.site.value = options[0] if options else None
        prepared = self._prepare()
        self.specimens.value = pd.DataFrame([
            {"specimen": p.name, "n": p.n, "k′": round(p.k_prime, 3) if np.isfinite(p.k_prime)
             else None, "B (µT)": round(p.b_anc, 1) if np.isfinite(p.b_anc) else None,
             "used": "yes" if p.included else "no", "note": p.note} for p in prepared])
        result = self.s.bicep_results.get(self.site.value)
        if result is None:
            self.result_pane.object = (f'<div style="{MUTED_STYLE}">No BiCEP result for this '
                                       f'site yet. Press Run.</div>')
            self.methods.object = ""
            self.plot.object = None
        else:
            self.result_pane.object = self._result_html(result)
            self.methods.object = (f'<div style="{SECTION_STYLE}">Methods and citation</div>'
                                   f'<pre style="white-space:pre-wrap;font-size:0.82rem">'
                                   f'{result.methods_block()}</pre>')
            self.plot.object = pub.bicep_figure(result, prepared)
        self.audit.object = ("<div style='%s'>%s</div>" %
                             (MUTED_STYLE, "<br>".join(self._audit[-8:]))) if self._audit else ""

    def _result_html(self, result) -> str:
        colour = PASS_COLOR if result.converged or result.method == "bootstrap" else FAIL_COLOR
        items = [f"<b>{result.b_site:.1f} µT</b>" if np.isfinite(result.b_site) else "<b>—</b>",
                 f'<span style="{MUTED_STYLE}">95% credible '
                 f'{result.ci_low:.1f}–{result.ci_high:.1f} µT</span>',
                 f'<span style="{MUTED_STYLE}">N = {len(result.specimens)}</span>',
                 f'<span style="{MUTED_STYLE}">slope {result.slope:+.1f} µT per unit k</span>',
                 f'<span style="{MUTED_STYLE}">sampler {result.method}</span>']
        html = kpi(items)
        if result.method != "bootstrap":
            html += kpi([f'<span style="color:{colour}">R-hat {result.r_hat:.3f}</span>',
                         f'<span style="color:{colour}">ESS {result.ess:.0f}</span>',
                         f'<span style="color:{colour}">{result.divergences} divergences</span>',
                         f'<span style="{MUTED_STYLE}">{result.n_draws} draws, seed '
                         f'{result.seed}, {result.seconds:.1f} s</span>'])
        if result.ppc:
            html += kpi([f'<span style="{MUTED_STYLE}">posterior predictive: RMS residual '
                         f'{result.ppc["rms_residual"]:.2f} µT, R² '
                         f'{result.ppc["r_squared"]:.3f}</span>'])
        for warning in result.warnings:
            html += f'<div style="color:{FAIL_COLOR}">{warning}</div>'
        if result.excluded:
            html += (f'<div style="{MUTED_STYLE}">excluded: '
                     f'{"; ".join(f"{k} ({v})" for k, v in result.excluded.items())}</div>')
        return html

    def sidebar(self):
        return pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">BiCEP</div>'),
            self.site, self.method, pn.Row(self.draws, self.warmup),
            pn.Row(self.chains, self.seed), self.prior, self.only_accepted,
            pn.Row(self.run_btn, self.cancel_btn), self.progress, self.status,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Specimens</div>'),
            pn.Row(self.exclude_btn, self.include_btn), self.audit,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Installation</div>'), self.install,
            sizing_mode="stretch_width")

    def panel(self):
        return pn.Column(self.result_pane, self.plot, self.specimens,
                         pn.Row(self.save_btn, self.save_msg), self.methods,
                         sizing_mode="stretch_width")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
class ExportView:
    """Preview, merge policy, validation, figures and persistence."""

    POLICY = """
The intensity results of the specimens this study has measurements for are
replaced by the current interpretations. Everything else is inherited: the
directional and rock-magnetic rows of the same specimens, the anisotropy
tensors, and all descriptive metadata (locations, ages, lithologies). Only
MagIC 3 columns are written. Site rows carry the mean of the accepted
specimens, its scatter and, where the site has coordinates, a VADM. Every row
records the software, the analyst, the criteria set and the correction method
codes it was produced under. The first export into the data directory copies
the original tables to a backup folder.
"""

    def __init__(self, session: Session):
        self.s = session
        self.analysts = pn.widgets.TextInput(name="Analyst(s)", placeholder="written to analysts",
                                             width=280)
        self.levels = pn.widgets.CheckBoxGroup(name="group levels", value=["site"],
                                               options=["sample", "site"], inline=True)
        self.only_accepted = pn.widgets.Checkbox(name="export accepted specimens only",
                                                 value=False)
        self.weighted = pn.widgets.Checkbox(name="weighted group means", value=False)
        self.measurements = pn.widgets.Checkbox(name="write measurements.txt with the flags",
                                                value=True)
        self.export_btn = pn.widgets.Button(name="Write MagIC tables", button_type="success",
                                            width=200)
        self.validate_btn = pn.widgets.Button(name="Validate", button_type="primary", width=130)
        self.preview = pn.widgets.Tabulator(pd.DataFrame(), show_index=False, disabled=True,
                                            pagination="local", page_size=12, height=360,
                                            sizing_mode="stretch_width", theme="simple")
        self.which = pn.widgets.RadioButtonGroup(options=["specimens", "sites", "criteria"],
                                                 value="specimens", button_type="primary")
        self.which.param.watch(lambda e: self._preview(), "value")
        self.report = pn.pane.HTML("", sizing_mode="stretch_width")
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")
        self.session_path = pn.widgets.TextInput(name="session file", value=SESSION_NAME,
                                                 sizing_mode="stretch_width")
        self.save_session_btn = pn.widgets.Button(name="Save session", width=140)
        self.load_session_btn = pn.widgets.Button(name="Load session", width=140)
        self.save_redo_btn = pn.widgets.Button(name="Save .redo", width=120)
        self.load_redo_btn = pn.widgets.Button(name="Load .redo", width=120)
        self.import_btn = pn.widgets.Button(name="Import from specimens.txt", width=220)
        self.figure_kind = pn.widgets.Select(
            name="figure", width=220,
            options={"Arai plot (this specimen)": "arai",
                     "Arai plot with the checks": "arai_checks",
                     "Site summary": "site",
                     "Study summary": "study"})
        self.figure_format = pn.widgets.Select(name="format", options=["pdf", "svg", "png"],
                                               width=110)
        self.figure_btn = pn.widgets.Button(name="Save figure", button_type="primary", width=140)
        self.figure_preview = pn.pane.Matplotlib(height=420, sizing_mode="stretch_width",
                                                 tight=True)
        self.citations = pn.pane.HTML("", sizing_mode="stretch_width")
        self.export_btn.on_click(self._export)
        self.validate_btn.on_click(self._validate)
        self.save_session_btn.on_click(lambda e: self._session(True))
        self.load_session_btn.on_click(lambda e: self._session(False))
        self.save_redo_btn.on_click(lambda e: self._redo(True))
        self.load_redo_btn.on_click(lambda e: self._redo(False))
        self.import_btn.on_click(self._import)
        self.figure_btn.on_click(self._save_figure)
        session.param.watch(lambda e: self._refresh(), ["version", "directory", "specimen"])
        self._refresh()

    def _refresh(self):
        self._preview()
        self.citations.object = self._citations()

    def _preview(self):
        if self.s.data is None:
            return
        which = self.which.value
        if which == "specimens":
            frame = self.s.data.merged_specimens_table(self.analysts.value,
                                                       self.only_accepted.value)
        elif which == "sites":
            frame = self.s.data.merged_group_table("site", self.analysts.value,
                                                   self.weighted.value)
        else:
            frame = self.s.data.criteria_table()
        self.preview.value = _front(frame).head(400)

    def _export(self, event=None):
        try:
            written = self.s.export_tables(analysts=self.analysts.value,
                                           levels=tuple(self.levels.value),
                                           write_measurements=self.measurements.value,
                                           only_accepted=self.only_accepted.value,
                                           weighted=self.weighted.value)
        except Exception as exc:
            self.message.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'
            return
        listed = "<br>".join(os.path.basename(p) for p in written if p)
        self.message.object = (f'<div style="color:{PASS_COLOR}">wrote {len(written)} files to '
                               f'{self.s.output_dir}</div><div style="{MUTED_STYLE}">{listed}</div>')
        self._validate()

    def _validate(self, event=None):
        try:
            report = self.s.validate_output()
        except Exception as exc:
            self.report.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'
            return
        rows = []
        for table, failure in sorted(report.items()):
            if failure is None:
                rows.append(f'<div style="color:{PASS_COLOR}">✓ {table}</div>')
                continue
            detail = []
            if failure["missing_cols"]:
                detail.append("missing columns: " + ", ".join(failure["missing_cols"]))
            if failure["bad_rows"]:
                detail.append(f'{len(failure["bad_rows"])} bad rows')
            cells = failure["failing_items"]
            if cells:
                detail.append(f"{len(cells)} failing cells")
            rows.append(f'<div style="color:{FAIL_COLOR}">✗ {table}: '
                        f'{"; ".join(detail) or "see the validator"}</div>')
            # cell-level, so the analyst can go to the cell rather than the table
            for cell in cells[:6]:
                where = f'{cell["row"]} · {cell["column"]}' if cell["row"] else cell["column"]
                rows.append(f'<div style="{MUTED_STYLE};padding-left:16px">{where}: '
                            f'{_clip(cell["problem"], 160)}</div>')
            if len(cells) > 6:
                rows.append(f'<div style="{MUTED_STYLE};padding-left:16px">'
                            f'… and {len(cells) - 6} more</div>')
        self.report.object = "".join(rows) or (
            f'<div style="{MUTED_STYLE}">nothing to check yet: write the tables first</div>')

    def _session(self, save: bool):
        path = self.session_path.value.strip() or SESSION_NAME
        if not os.path.isabs(path):
            path = os.path.join(self.s.output_dir, path)
        try:
            if save:
                self.s.save_session(path)
                self.message.object = f'<div style="color:{PASS_COLOR}">saved {path}</div>'
            else:
                n = self.s.load_session(path)
                self.message.object = (f'<div style="color:{PASS_COLOR}">restored {n} '
                                       f'interpretations</div>')
        except (OSError, ValueError) as exc:
            self.message.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'

    def _redo(self, save: bool):
        path = os.path.join(self.s.output_dir, REDO_NAME)
        try:
            if save:
                self.s.save_redo(path)
                self.message.object = f'<div style="color:{PASS_COLOR}">saved {path}</div>'
            else:
                n, problems = self.s.load_redo(path)
                text = f"loaded {n} interpretations"
                if problems:
                    text += f"; {len(problems)} problems: " + "; ".join(problems[:3])
                self.message.object = f'<div style="color:{PASS_COLOR}">{text}</div>'
        except (OSError, ValueError) as exc:
            self.message.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'

    def _import(self, event=None):
        n, problems = self.s.import_from_specimens_table()
        text = f"imported {n} interpretations from specimens.txt"
        if problems:
            text += f"; {len(problems)} did not match a step"
        self.message.object = f'<div style="color:{PASS_COLOR}">{text}</div>'

    def _figure(self):
        kind = self.figure_kind.value
        if kind in ("arai", "arai_checks") and self.s.ready:
            return pub.specimen_figure(self.s.spec, self.s.bounds(), self.s.statistics(),
                                       self.s.result, with_checks=(kind == "arai_checks"))
        if kind == "site" and self.s.ready:
            site = self.s.spec.site
            results = [r for r in (self.s.data.result(n)
                                   for n in self.s.data.specimens_in("site", site))
                       if r is not None]
            return pub.site_figure(site, results,
                                   accepted={r.specimen for r in results
                                             if self.s.data.is_accepted(r)})
        if kind == "study":
            return pub.study_figure(self.s.data)
        return None

    def _save_figure(self, event=None):
        figure = self._figure()
        if figure is None:
            self.message.object = f'<div style="{MUTED_STYLE}">nothing to draw</div>'
            return
        self.figure_preview.object = figure
        name = f"{self.figure_kind.value}_{self.s.specimen or 'study'}.{self.figure_format.value}"
        path = os.path.join(self.s.output_dir, name)
        try:
            os.makedirs(self.s.output_dir, exist_ok=True)
            figure.savefig(path, format=self.figure_format.value, bbox_inches="tight")
            self.message.object = f'<div style="color:{PASS_COLOR}">saved {path}</div>'
        except OSError as exc:
            self.message.object = f'<div style="color:{FAIL_COLOR}">{exc}</div>'

    def _citations(self) -> str:
        used = {("Paterson, G. A., L. Tauxe, A. J. Biggin, R. Shaar and L. C. Jonestrask (2014), "
                 "On improving the selection of Thellier-type paleointensity data, G-cubed.",
                 "10.1002/2013GC005135"),
                ("Standard Paleointensity Definitions v1.2.0 (February 2021).", "")}
        if self.s.data is not None:
            criteria = self.s.data.criteria
            if criteria.citation:
                used.add((criteria.citation, criteria.doi))
            if any(c.key == "Ziggie" for c in criteria.specimen):
                used.add(("Tully, A. W. and G. A. Paterson (2025), Another simple test for the "
                          "presence of multidomain behavior during paleointensity experiments, "
                          "JGR Solid Earth.", "10.1029/2025JB031608"))
            if any(c.key in ("k", "k_prime") for c in criteria.specimen):
                used.add(("Paterson, G. A. (2011), A simple test for the presence of multidomain "
                          "behaviour during paleointensity experiments, JGR.",
                          "10.1029/2011JB008369"))
            if self.s.bicep_results:
                used.add((bicep_core.CITATION, bicep_core.DOI))
        rows = "".join(f"<li>{text}" + (f' <a href="https://doi.org/{doi}" target="_blank">'
                                        f"{doi}</a>" if doi else "") + "</li>"
                       for text, doi in sorted(used))
        return (f'<div style="{SECTION_STYLE}">Cite</div><ul style="font-size:0.85rem">'
                f"{rows}</ul>")

    def panel(self):
        settings = pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">MagIC 3 tables</div>'),
            pn.Row(self.analysts, self.levels),
            pn.Row(self.only_accepted, self.weighted, self.measurements,
                   stylesheets=[CHECKBOX_CSS]),
            pn.Row(self.export_btn, self.validate_btn), self.message, self.report,
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Merge policy</div>'
                         f'<div style="{MUTED_STYLE}">{self.POLICY}</div>'),
            sizing_mode="stretch_width")
        preview = pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Preview</div>'),
                            self.which, self.preview, sizing_mode="stretch_width")
        persistence = pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Session</div>'),
            self.session_path,
            pn.Row(self.save_session_btn, self.load_session_btn, self.save_redo_btn,
                   self.load_redo_btn, self.import_btn, stylesheets=[BUTTON_GROUP_CSS]),
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">The session is auto-saved to '
                         f'{AUTOSAVE_NAME} after every change and restored the next time this '
                         f'directory is opened.</div>'), sizing_mode="stretch_width")
        figures = pn.Column(
            pn.pane.HTML(f'<div style="{SECTION_STYLE}">Publication figures</div>'),
            pn.Row(self.figure_kind, self.figure_format, self.figure_btn),
            self.figure_preview, sizing_mode="stretch_width")
        return pn.Column(settings, pn.layout.Divider(), preview, pn.layout.Divider(),
                         persistence, pn.layout.Divider(), figures, pn.layout.Divider(),
                         self.citations, sizing_mode="stretch_width")
