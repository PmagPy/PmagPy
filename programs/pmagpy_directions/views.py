"""
The panes of the application. Each view owns its widgets and figures, reads
and mutates the shared ``Session``, and redraws when the session changes.
"""
from __future__ import annotations

import io
import os

import numpy as np
import pandas as pd
import panel as pn

import pmagpy.demag as dc

from . import publication as pub
from .logger import StepLogger
from pmagpy_panel.widgets import HeightSplitter, Hotkeys
from .plots import DecayPlot, DirectionsPlot, PoleMapPlot, StepEqualAreaPlot, ZijderveldPlot
from .session import REDO_NAME, AUTOSAVE_NAME, RECENT_FILE, Session, env
from pmagpy_panel.chooser import DirectoryChooser
from pmagpy_panel.theme import (BUTTON_GROUP_CSS, CHECKBOX_CSS, INPUT_CSS, KPI_ITEM, MUTED_STYLE, SECTION_STYLE,
                    STATS_TABLE_CSS, TABLE_ROW_CSS, kpi, lighten)

FIT_OPTIONS = {f"{v} ({k})": k for k, v in dc.FIT_TYPES.items()}
COORD_OPTIONS = {v: k for k, v in dc.COORD_NAMES.items()}
# the statistics of a mean direction; the VGP it implies belongs to the Poles tab,
# which plots it on the globe, rather than in this table
MEAN_COLUMNS = ["dir_dec", "dir_inc", "dir_alpha95", "dir_k", "dir_r", "dir_n_specimens", "dir_n_samples",
                "dir_n_sites", "dir_n_specimens_lines", "dir_n_specimens_planes"]
SIDE_PLOT = 380      # equal-area net in the side column, inside its 450 px default width


def next_tick(fn):
    """Run ``fn`` under the Bokeh document lock (immediately when not serving)."""
    doc = pn.state.curdoc
    if doc is not None and getattr(doc, "session_context", None) is not None:
        doc.add_next_tick_callback(fn)
    else:
        fn()


def section(text: str):
    return pn.pane.HTML(f'<div style="{SECTION_STYLE}">{text}</div>', margin=(2, 0, 0, 0))


def coord_selector(session):
    """A specimen / geographic / tilt-corrected button group bound to the session's coordinate system."""
    widget = pn.widgets.RadioButtonGroup(options=COORD_OPTIONS, value=session.coord, button_type="primary",
                                         button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
    state = {"syncing": False}

    def push(event):
        if event.new is not None and not state["syncing"]:
            session.coord = event.new

    def pull(event):
        state["syncing"] = True
        try:
            widget.value = event.new
        finally:
            state["syncing"] = False
    widget.param.watch(push, "value")
    session.param.watch(pull, "coord")
    return widget


def plot_box(fig, size):
    """Fixed-width wrapper so that wide tables next to a plot never squeeze it."""
    return pn.Column(fig, width=size + 12, height=size + 40, sizing_mode="fixed")


class LazyView:
    """Mixin: redraw immediately while visible, otherwise remember to redraw on activation."""

    active = True

    def _lazy_redraw(self, *events):
        if self.active:
            self.redraw()
        else:
            self._dirty = True

    def set_active(self, active: bool):
        self.active = active
        if active and getattr(self, "_dirty", False):
            self._dirty = False
            self.redraw()


def _table_height(rows: int, cap: int) -> int:
    """Height for a side table of `rows` rows: its own size, up to `cap`."""
    return int(min(cap, max(96, 46 + 28 * rows)))


def _fmt(v, nd=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    return f"{v:.{nd}f}"


# ===========================================================================
class SpecimenView:
    """Zijderveld / equal-area / M-M0 with the step logger and fit controls."""

    def __init__(self, session: Session):
        self.s = session
        self._pending_bound = None
        self._syncing = False
        s = session

        # --- sidebar widgets -------------------------------------------------
        self.specimen_sel = pn.widgets.Select.from_param(s.param.specimen, name="Specimen")
        self.specimen_sel.description = None            # no "?" help icon (from_param copies the param doc)
        self.prev_btn = pn.widgets.Button(name="◀ previous", width=120)
        self.next_btn = pn.widgets.Button(name="next ▶", width=120)
        self.prev_btn.on_click(lambda e: s.step_specimen(-1))
        self.next_btn.on_click(lambda e: s.step_specimen(+1))
        self.coord_sel = pn.widgets.RadioButtonGroup(options=COORD_OPTIONS, value=s.coord, button_type="primary", button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.coord_sel.param.watch(self._on_coord_widget, "value")
        self.proj_sel = pn.widgets.RadioButtonGroup(
            options={"east": "ew", "north": "ns", "NRM dec": "nrm"}, value=s.projection,
            button_type="primary", button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.proj_sel.param.watch(lambda e: setattr(s, "projection", e.new), "value")
        self.label_sel = pn.widgets.RadioButtonGroup(options={"auto": -1, "all": 1}, value=s.label_every,
                                                     button_type="primary", button_style="outline",
                                                     stylesheets=[BUTTON_GROUP_CSS], width=100)
        self.label_sel.param.watch(lambda e: setattr(s, "label_every", e.new), "value")
        self.logger = StepLogger(height=540, sizing_mode="stretch_width")
        self.logger.param.watch(self._on_logger_click, "clicked")
        self.hotkeys = Hotkeys(width=0, height=0, margin=0)
        self.hotkeys.param.watch(self._on_hotkey, "n")
        same = dict(stylesheets=[INPUT_CSS])
        self.fit_type_sel = pn.widgets.Select(name="Fit type", options=FIT_OPTIONS, value="DE-BFL", width=210, **same)
        self.comp_name = pn.widgets.TextInput(name="Component", value="A", width=110, **same)
        self.tmin_sel = pn.widgets.Select(name="Lower bound", options=[], width=130, **same)
        self.tmax_sel = pn.widgets.Select(name="Upper bound", options=[], width=130, **same)
        self.add_btn = pn.widgets.Button(name="New fit", button_type="success", width=110, margin=(22, 5, 5, 5))
        self.del_btn = pn.widgets.Button(name="Delete", button_type="danger", width=90, margin=(22, 5, 5, 5))
        self.add_btn.on_click(self._new_fit)
        self.del_btn.on_click(lambda e: s.delete_current())
        # live edits of the selected fit
        self.tmin_sel.param.watch(self._on_bound_widget, "value")
        self.tmax_sel.param.watch(self._on_bound_widget, "value")
        self.fit_type_sel.param.watch(self._on_type_widget, "value")
        self.comp_name.param.watch(self._on_name_widget, "value")
        self.hint = pn.pane.HTML(f'<span style="{MUTED_STYLE}">click a step to move the selected fit\'s nearest '
                                 'bound · <b>[</b> <b>]</b> <b>{</b> <b>}</b> nudge bounds · '
                                 '<i>New fit</i>: click two steps · <b>←</b> <b>→</b> specimens</span>',
                                 margin=(2, 0, 0, 12))
        # the one list of fits: statistics + selection (click a row to make it the current fit)
        self.comp_table = pn.widgets.Tabulator(
            pd.DataFrame(), height=150, show_index=False, disabled=True, selectable=1, sortable=False, margin=(0, 5, 5, 5),
            configuration={"headerSort": False}, sizing_mode="stretch_width", text_align="right",
            layout="fit_data_table",
            stylesheets=[TABLE_ROW_CSS])
        self.comp_table.param.watch(self._on_comp_select, "selection")

        # --- figures ---------------------------------------------------------
        self.zij = ZijderveldPlot()
        # the net sits on top of the M/M₀ plot; the M/M₀ frame bottom is aligned with
        # the Zijderveld frame bottom (both measured from the top of the row)
        side = ZijderveldPlot.SIDE
        self.eq = StepEqualAreaPlot(size=side)
        decay_frame = ZijderveldPlot.TOP + ZijderveldPlot.FRAME - side - DecayPlot.TOP
        self.decay = DecayPlot(size=side, frame_height=decay_frame)
        self.zij.on_select(self._on_plot_select)
        self.eq.on_select(self._on_plot_select)
        self.info = pn.pane.HTML("", sizing_mode="stretch_width")
        # the plots and the fits below them share the height of the window: a big
        # screen can give the diagram more, a small one has to take some back
        self.plot_col = pn.Column(self.eq.fig, self.decay.fig, width=side + 10, margin=0,
                                  styles={"overflow": "visible"})
        self.plot_size = HeightSplitter(value=ZijderveldPlot.FRAME, default_value=ZijderveldPlot.FRAME,
                                        minimum=240, maximum=1000)
        self.plot_size.param.watch(self._on_plot_size, "value")

        s.param.watch(self._reset_pending, ["specimen"])
        s.param.watch(self.redraw, ["specimen", "coord", "projection", "label_every", "version", "current"])
        self.redraw()

    # the net and the M/M₀ strip keep their share of the diagram's height
    SIDE_RATIO = ZijderveldPlot.SIDE / ZijderveldPlot.FRAME

    def _on_plot_size(self, event):
        """Rescale the three plots together, as they are built in __init__."""
        frame = int(event.new)
        side = max(140, int(round(frame * self.SIDE_RATIO)))
        self.zij.set_frame(frame)
        self.eq.set_size(side)
        self.decay.set_size(side, ZijderveldPlot.TOP + frame - side - DecayPlot.TOP)
        self.plot_col.width = side + 10

    # --- interaction ----------------------------------------------------------
    def _on_coord_widget(self, event):
        # replacing the group's options (a dataset without bedding after one with it)
        # transiently sets its value to None; only a user's choice reaches the session
        if event.new is not None and not self._syncing:
            self.s.coord = event.new

    def _labels(self):
        return list(self.s.spec.steps["label"])

    def _on_logger_click(self, event):
        click = event.new
        if not click:
            return
        row = int(click["row"])
        if click["button"] == "right":
            self.s.toggle_step(row)
            return
        self._pick(row)

    def _pick(self, row):
        """A step was clicked: move a bound of the selected fit, or build a new fit from two clicks."""
        if self.s.current is not None:
            self.s.move_nearest_bound(self.s.current, row)
            return
        if self._pending_bound is None:
            self._pending_bound = row
            self.logger.marks = {"imin": row}
            self.s.status = f"lower bound {self._labels()[row]} — now click the upper bound"
        else:
            lo, hi = sorted((self._pending_bound, row))
            self._pending_bound = None
            self.logger.marks = {}
            if hi > lo:
                comp = self.s.add_component(self.comp_name.value or self.s.next_fit_name(), lo, hi,
                                            self.fit_type_sel.value)
                labels = self._labels()
                self.s.status = f"fit {comp.name}: {labels[comp.imin]} – {labels[comp.imax]} — auto-saved"

    def _reset_pending(self, *events):
        """A new specimen: forget a half-built fit."""
        if self._pending_bound is not None:
            self._pending_bound = None
            self.logger.marks = {}
            self.s.status = ""

    def _new_fit(self, event=None):
        self.s.current = None
        self._pending_bound = None
        self.logger.marks = {}
        self.comp_name.value = self.s.next_fit_name()
        self.s.status = "new fit: click its lower bound, then its upper bound"

    def _on_bound_widget(self, event):
        if self._syncing or self.s.current is None:
            return
        labels = self._labels()
        if self.tmin_sel.value in labels and self.tmax_sel.value in labels:
            self.s.update_component(self.s.current, imin=labels.index(self.tmin_sel.value),
                                    imax=labels.index(self.tmax_sel.value))

    def _on_type_widget(self, event):
        if not self._syncing and self.s.current is not None:
            self.s.update_component(self.s.current, fit_type=event.new)

    def _on_name_widget(self, event):
        if not self._syncing and self.s.current is not None and event.new.strip():
            self.s.update_component(self.s.current, name=event.new.strip())

    def _on_hotkey(self, event):
        key = self.hotkeys.key
        cur = self.s.current
        if key == "ArrowRight":
            self.s.step_specimen(+1)
        elif key == "ArrowLeft":
            self.s.step_specimen(-1)
        elif cur is not None and key in "[]{}":
            if key == "[":
                self.s.update_component(cur, imin=cur.imin - 1)
            elif key == "]":
                self.s.update_component(cur, imin=cur.imin + 1)
            elif key == "{":
                self.s.update_component(cur, imax=cur.imax - 1)
            elif key == "}":
                self.s.update_component(cur, imax=cur.imax + 1)

    def _on_plot_select(self, seqs):
        if not seqs:
            return
        if len(seqs) == 1:
            next_tick(lambda: self._pick(int(seqs[0])))
            return
        lo, hi = int(min(seqs)), int(max(seqs))

        def apply():
            if self.s.current is not None:
                self.s.update_component(self.s.current, imin=lo, imax=hi)
            elif hi > lo:
                self._pending_bound = None
                self.logger.marks = {}
                self.s.add_component(self.comp_name.value or self.s.next_fit_name(), lo, hi, self.fit_type_sel.value)
        next_tick(apply)

    def _on_comp_select(self, event):
        if self._syncing or not event.new:
            return
        comps = self.s.components()
        if event.new[0] < len(comps):
            comp = comps[event.new[0]]
            # Tabulator selection events arrive outside the Bokeh document lock;
            # the redraw touches Bokeh models, so run it on the next tick.
            next_tick(lambda: setattr(self.s, "current", comp))

    # --- drawing --------------------------------------------------------------
    def redraw(self, *events):
        s = self.s
        if not s.ready:
            return
        spec, coord = s.spec, s.active_coord
        self._syncing = True
        try:
            # a new dataset: the selector must list its specimens (param's own link
            # to the widget is not enough when the objects list is replaced)
            if list(self.specimen_sel.options) != list(s.param.specimen.objects):
                self.specimen_sel.options = list(s.param.specimen.objects)
            self.specimen_sel.value = s.specimen
            self.coord_sel.options = {dc.COORD_NAMES[c]: c for c in spec.available_coords()}
            self.coord_sel.value = coord
            labels = self._labels()
            self.tmin_sel.options = labels
            self.tmax_sel.options = labels
            cur = s.current
            if cur is not None:
                self.comp_name.value, self.fit_type_sel.value = cur.name, cur.fit_type
                self.tmin_sel.value, self.tmax_sel.value = labels[cur.imin], labels[cur.imax]
            else:
                if self.tmin_sel.value not in labels:
                    self.tmin_sel.value = labels[0]
                if self.tmax_sel.value not in labels:
                    self.tmax_sel.value = labels[-1]
        finally:
            self._syncing = False

        fits = s.fits()
        rotation = s.rotation()
        self.zij.update(spec, fits, coord, rotation, s.label_every, s.projection)
        self.eq.update(spec, fits, coord)
        self.decay.update(spec, fits)

        dec_col, inc_col = dc.COORD_COLUMNS[coord]
        steps = spec.steps
        self.logger.rows = [dict(i=int(r.sequence), step=r.label, dec=f"{r[dec_col]:.1f}", inc=f"{r[inc_col]:.1f}",
                                 M=f"{r.moment:.2e}", csd="" if np.isnan(r.csd) else f"{r.csd:.1f}", q=r.quality)
                            for _, r in steps.iterrows()]
        highlight = {}
        cur_res = next((res for c, res, col in fits if cur is not None and c.key() == cur.key()), None)
        if cur is not None and cur_res is not None:
            highlight = {"imin": cur_res.imin, "imax": cur_res.imax, "color": s.color_of(cur.name)}
        self.logger.highlight = highlight

        rows = []
        for comp, res, color in fits:
            row = dict(fit=comp.name, type=comp.fit_type, bounds=f"{labels[comp.imin]} – {labels[comp.imax]}",
                       dec="–", inc="–", MAD="–", DANG="–", α95="–", n=0, q=comp.quality)
            if res is not None:
                row.update(bounds=f"{labels[res.imin]} – {labels[res.imax]}", dec=_fmt(res.dir_dec),
                           inc=_fmt(res.dir_inc), MAD=_fmt(res.dir_mad_free), DANG=_fmt(res.dir_dang),
                           α95=_fmt(res.dir_alpha95), n=res.dir_n_measurements)
            rows.append(row)
        df = pd.DataFrame(rows, columns=["fit", "type", "bounds", "dec", "inc", "MAD", "DANG", "α95", "n", "q"])
        comps = s.components()
        wanted = [comps.index(cur)] if cur in comps else []
        # Rewrite the table only when its content (or colouring) changed: re-assigning
        # the value from inside the table's own selection callback breaks Bokeh's write
        # batch (and the current fit is shown by the selection style, not by the data).
        colors = [color for _, _, color in fits]
        self._syncing = True
        try:
            if not (df.equals(getattr(self, "_comp_df", None)) and colors == getattr(self, "_comp_colors", None)):
                self._comp_df, self._comp_colors = df, colors
                self.comp_table.value = df
                self.comp_table.style.clear()

                def style_row(row, colors=colors):
                    idx = row.name if isinstance(row.name, int) else 0
                    c = colors[idx] if idx < len(colors) else "#ffffff"
                    fill = f"background: {lighten(c, 0.85)}"
                    return [f"border-left: 6px solid {c}; {fill}"] + [fill] * (len(row) - 1)
                if len(df):
                    self.comp_table.style.apply(style_row, axis=1)
            if list(self.comp_table.selection) != wanted:
                self.comp_table.selection = wanted
        finally:
            self._syncing = False

        orient = spec.orientation
        o = "no sample orientation"
        if orient is not None and orient.has_geographic:
            o = f"lab arrow: azimuth {orient.azimuth:g}°, dip {orient.dip:g}°"
            if orient.has_tilt:
                o += f" · bedding: dip direction {orient.bed_dip_direction:g}°, dip {orient.bed_dip:g}°"
        self.info.object = kpi([f"<b>{spec.name}</b>", ("sample", spec.sample), ("site", spec.site), spec.location,
                                f'<span style="{MUTED_STYLE}">{o}</span>'])

    # --- layout -----------------------------------------------------------------
    def sidebar(self):
        return pn.Column(
            self.hotkeys,
            self.specimen_sel, pn.Row(self.prev_btn, self.next_btn,
                                      pn.pane.HTML(f'<span style="{MUTED_STYLE}">← → keys</span>', margin=(12, 0, 0, 4))),
            self.info,
            pn.Row(pn.Column(section("Coordinates"), self.coord_sel, margin=0),
                   pn.Column(section("Step labels"), self.label_sel, width=110, margin=0)),
            section("Zijderveld projection · x axis"), self.proj_sel,
            section("Steps · click = bound, right-click = good/bad"),
            self.logger,
        )

    def main(self):
        return pn.Column(
            pn.Row(pn.pane.Bokeh(self.zij.fig, margin=0), self.plot_col, margin=0),
            self.plot_size,
            # left margin as the table below: the heading lines up with what it labels
            pn.Row(section("Fits · click a row to select it"), self.hint, margin=(0, 0, 0, 5)),
            pn.Row(self.comp_name, self.fit_type_sel, self.tmin_sel, self.tmax_sel,
                   self.add_btn, self.del_btn),
            self.comp_table,
        )


# ===========================================================================
class MeansView(LazyView):
    """Sample / site / location means: plot specimen fits or lower-level means."""

    def __init__(self, session: Session):
        self.s = session
        self.level = pn.widgets.RadioButtonGroup(options=["sample", "site", "location"], value="site",
                                                 button_type="primary", button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.name = pn.widgets.Select(name="Name", options=[], width=220)
        self.comp = pn.widgets.Select(name="Component", options=["all"], value="all", width=140)
        self.show = pn.widgets.RadioButtonGroup(options={"specimens": "specimens"}, value="specimens",
                                                button_type="primary", button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.coord = coord_selector(session)
        # Fisher of the whole set, one Fisher mean per polarity mode (the comparison
        # a reversal test rests on), or the axial Bingham mean with its ellipse
        self.stat = pn.widgets.RadioButtonGroup(options={"Fisher": "fisher", "by polarity": "polarity",
                                                         "Bingham": "bingham"},
                                                value="fisher", button_type="primary", button_style="outline",
                                                stylesheets=[BUTTON_GROUP_CSS])
        self.plot = DirectionsPlot("Directions")
        self.stats = pn.pane.DataFrame(pd.DataFrame(), index=False, sizing_mode="stretch_width",
                                       stylesheets=[STATS_TABLE_CSS])
        self.download = pn.widgets.FileDownload(callback=self._figure_bytes, filename="directions.pdf",
                                                label="Download figure (PDF)", button_type="primary", width=220)
        # the side-column list of the fits (or lower-level means) that are plotted.
        # Planes are listed apart from the lines: their columns are different things
        # (a pole, and the vector it resolves to) and reading them under the same
        # dec/inc heading as a line is what makes the two look alike
        def fits_table(height):
            return pn.widgets.Tabulator(pd.DataFrame(), height=height, show_index=False, disabled=True,
                                        selectable=1, sortable=False, configuration={"headerSort": False},
                                        sizing_mode="stretch_width", layout="fit_data_table", text_align="right",
                                        stylesheets=[TABLE_ROW_CSS])
        self.table = fits_table(520)
        self.plane_table = fits_table(200)
        self.table_head = pn.pane.HTML("", margin=(2, 0, 0, 0))
        self.planes_box = pn.Column(pn.pane.HTML(f'<div style="{SECTION_STYLE}">Pole to the plane and '
                                                 'best fit vector (BFV)</div>', margin=(2, 0, 0, 0)),
                                    self.plane_table, visible=False, sizing_mode="stretch_width")
        # one selection at a time, whichever table it is in
        self.table.param.watch(lambda e: e.new and setattr(self.plane_table, "selection", []), "selection")
        self.plane_table.param.watch(lambda e: e.new and setattr(self.table, "selection", []), "selection")
        self._records, self._plane_records = [], []
        self._table_df = None
        self.goto_btn = pn.widgets.Button(name="Go to specimen", button_type="primary", width=140)
        self.flag_btn = pn.widgets.Button(name="Toggle good/bad", button_type="warning", width=140)
        self.goto_btn.on_click(self._goto)
        self.flag_btn.on_click(self._flag)
        self.on_goto = None          # set by the app: switches to the Specimen tab
        self.level.param.watch(self._on_level, "value")      # options first ...
        for w in (self.level, self.name, self.comp, self.show, self.stat):
            w.param.watch(self.redraw, "value")               # ... then redraw
        session.param.watch(self._on_level, ["version"])
        session.param.watch(self._lazy_redraw, ["coord", "version", "unify_polarity", "flip_polarity"])
        self._on_level()
        self.redraw()

    def _on_level(self, *events):
        s = self.s
        level = self.level.value
        names = s.data.names_at(level)
        self.name.options = names
        if self.name.value not in names:
            self.name.value = names[0] if names else None
        comps = ["all"] + s.data.component_names()
        self.comp.options = comps
        if self.comp.value not in comps:
            self.comp.value = "all"
        options = {"specimens": "specimens"}
        if level == "site":
            options["sample means"] = "samples"
        elif level == "location":
            options["site means"] = "sites"
        self.show.options = options
        if self.show.value not in options.values():
            self.show.value = "specimens"

    def _collect(self):
        """Directions to plot, the mean, and the records listed in the side column."""
        s = self.s
        level, name, coord = self.level.value, self.name.value, s.coord
        comp = None if self.comp.value == "all" else self.comp.value
        over = self.show.value
        if over not in ("specimens", {"site": "samples", "location": "sites"}.get(level)):
            over = "specimens"
        dirs, planes, records, plane_records = [], [], [], []
        by_comp = {}                 # component -> the records its mean is formed from
        if over == "specimens":
            for spec_name in s.data.specimens_in(level, name):
                spec = s.data.specimens[spec_name]
                for c in s.data.components_for(spec_name):
                    if comp and c.name != comp:
                        continue
                    res = s.data.fit(c, coord)
                    color = s.color_of(c.name)
                    is_plane = c.fit_type == "DE-BFP"
                    # a plane's own dec/inc is the pole to it, not a direction: it is
                    # named as such and listed apart from the lines
                    if is_plane:
                        rec = dict(specimen=spec_name, fit=c.name, **{"pole dec": "–", "pole inc": "–"},
                                   MAD="–", **{"bfv dec": "–", "bfv inc": "–"}, n=0, q=c.quality,
                                   _comp=c, _color=color)
                    else:
                        rec = dict(specimen=spec_name, fit=c.name, dec="–", inc="–", MAD="–", n=0,
                                   q=c.quality, _comp=c, _color=color)
                    if res is not None:
                        key = ("pole dec", "pole inc") if is_plane else ("dec", "inc")
                        rec.update({key[0]: _fmt(res.dir_dec), key[1]: _fmt(res.dir_inc)})
                        rec.update(MAD=_fmt(res.dir_mad_free), n=res.dir_n_measurements)
                        if c.quality == "g":
                            if res.direction_type == "p":
                                planes.append((res.dir_dec, res.dir_inc, color))
                            else:
                                dirs.append((res.dir_dec, res.dir_inc, spec_name, c.name, color))
                            by_comp.setdefault(c.name, []).append(
                                {"dir_dec": res.dir_dec, "dir_inc": res.dir_inc,
                                 "dir_type": res.direction_type, "specimen": spec_name, "color": color})
                    (plane_records if is_plane else records).append(rec)
        else:
            lower = over[:-1]
            lower_means = s.data.mean_directions(lower, coord, comp)
            parent_of = {getattr(sp, lower): getattr(sp, level) for sp in s.data.specimens.values()}
            for _, m in lower_means.iterrows():
                if parent_of.get(m[lower]) != name:
                    continue
                color = s.color_of(m["dir_comp_name"])
                dirs.append((m["dir_dec"], m["dir_inc"], m[lower], m["dir_comp_name"], color))
                records.append({lower: m[lower], "fit": m["dir_comp_name"], "dec": _fmt(m["dir_dec"]),
                                "inc": _fmt(m["dir_inc"]), "α95": _fmt(m.get("dir_alpha95")),
                                "n": int(m.get("dir_n_specimens", 0)), "_comp": None, "_color": color,
                                "_specimens": m.get("specimens", "")})
        means = s.data.mean_directions(level, coord, comp, over=over, common_polarity=s.unify_polarity,
                                       flip=s.flip_polarity) if name else pd.DataFrame()
        means = means[means[level] == name] if len(means) else means
        # each great circle carries the point the mean is actually formed from
        # (MM88), resolved per component exactly as the mean is
        vectors = []
        for comp_name, recs in by_comp.items():
            on_planes = [r for r in recs if r["dir_type"] == "p"]
            for rec, (vdec, vinc) in zip(on_planes, dc.plane_best_fit_vectors(recs)):
                vectors.append((vdec, vinc, rec["specimen"], comp_name, rec["color"]))
        resolved = {(v[2], v[3]): (v[0], v[1]) for v in vectors}
        for rec in plane_records:
            vec = resolved.get((rec["specimen"], rec["fit"]))
            if vec is not None:
                rec["bfv dec"], rec["bfv inc"] = _fmt(vec[0]), _fmt(vec[1])
        return dirs, planes, means, records, plane_records, vectors

    def _mean_list(self, means):
        """(mean dict, colour) per component — a star and α95 for each, even when all are shown."""
        return [(m.to_dict(), self.s.color_of(m["dir_comp_name"])) for _, m in means.iterrows()] if len(means) else []

    STAT_LABELS = {"fisher": "Fisher mean", "polarity": "Fisher means, by polarity", "bingham": "Bingham mean"}

    def _alternative_means(self, dirs):
        """Means of the plotted directions under the chosen statistic, per component.

        Planes take no part: both statistics average directions, and a plane
        fit has none of its own until a mean places it on its circle.
        """
        by_comp = {}
        for dec, inc, _label, comp_name, _color in dirs:
            by_comp.setdefault(comp_name, []).append((dec, inc))
        rows = []
        for comp_name, block in by_comp.items():
            found = (dc.fisher_means_by_polarity(block) if self.stat.value == "polarity"
                     else [dc.bingham_mean(block)])
            for mean in found:
                if mean:
                    rows.append({"dir_comp_name": comp_name, **mean})
        return rows

    def _plotted_means(self, means, dirs):
        """(mean dict, colour) pairs for the net and the figure, under the chosen statistic."""
        if self.stat.value == "fisher":
            return self._mean_list(means)
        return [(m, self.s.color_of(m["dir_comp_name"])) for m in self._alternative_means(dirs)]

    def _fill_table(self, table, records, cache):
        """Fill one of the side tables, in the component colours, unless it is unchanged.

        (Re-assigning the value from inside the table's own selection callback
        breaks Bokeh's write batch, so an unchanged table is left alone.)
        """
        df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in records])
        colors = [r["_color"] for r in records]
        if (df.equals(getattr(self, cache, (None, None))[0])
                and colors == getattr(self, cache, (None, None))[1]):
            return
        setattr(self, cache, (df, colors))
        table.value = df
        table.style.clear()
        flags = [r.get("q", "g") for r in records]

        def style_row(row, colors=colors, flags=flags):
            i = row.name if isinstance(row.name, int) else 0
            c = colors[i] if i < len(colors) else "#ffffff"
            fill = f"background: {lighten(c, 0.85)}" + ("; color:#9aa1ab; text-decoration: line-through"
                                                        if i < len(flags) and flags[i] == "b" else "")
            return [f"border-left: 6px solid {c}; {fill}"] + [fill] * (len(row) - 1)
        if len(df):
            table.style.apply(style_row, axis=1)

    def redraw(self, *events):
        if self.s.data is None or not self.name.value:
            return
        dirs, planes, means, records, plane_records, vectors = self._collect()
        title = f"{self.level.value} {self.name.value} · {self.comp.value} · {dc.COORD_NAMES[self.s.coord]}"
        self.plot.update(dirs, planes, self._plotted_means(means, dirs), title=title, plane_vectors=vectors)
        self._records, self._plane_records = records, plane_records
        self._fill_table(self.table, records, "_table_cache")
        self._fill_table(self.plane_table, plane_records, "_plane_cache")
        # the planes table is there only when the data holds planes; both tables take
        # the height of what they hold, so the planes are not pushed out of sight by
        # empty rows above them
        self.planes_box.visible = bool(plane_records)
        self.table.height = _table_height(len(records), 300 if plane_records else 520)
        self.plane_table.height = _table_height(len(plane_records), 220)
        listed = "Lines" if plane_records else "Plotted fits"
        self.table_head.object = f'<div style="{SECTION_STYLE}">{listed} · select a row</div>'
        if self.stat.value == "fisher":
            cols = [c for c in ["dir_comp_name"] + MEAN_COLUMNS if c in means.columns]
            table = means[cols].round(1) if len(means) else pd.DataFrame()
            # a count that is zero throughout says nothing (no planes among the fits,
            # no sites under a sample mean) and only widens the table
            for col in [c for c in table.columns if c.startswith("dir_n_")]:
                if not pd.to_numeric(table[col], errors="coerce").fillna(0).any():
                    table = table.drop(columns=[col])
        else:
            # the alternative statistics are computed on what is plotted, so they
            # report only the columns they define (a Bingham ellipse has no α95)
            alt = pd.DataFrame(self._alternative_means(dirs))
            keep = ["dir_comp_name", "mode", "dir_dec", "dir_inc", "dir_alpha95", "dir_k",
                    "dir_n_specimens", "eta", "zeta"]
            table = alt[[c for c in keep if c in alt.columns]].round(1) if len(alt) else pd.DataFrame()
        self.stats.object = table.rename(columns=lambda c: c.replace("dir_", "").replace("_specimens", "_spec")
                                         .replace("alpha95", "α95").replace("comp_name", "component"))
        self.download.filename = f"{self.level.value}_{self.name.value}_{self.comp.value}.pdf"

    def _selected_record(self):
        for table, records in ((self.table, self._records), (self.plane_table, self._plane_records)):
            sel = table.selection
            if sel and sel[0] < len(records):
                return records[sel[0]]
        return None

    def _goto(self, event=None):
        rec = self._selected_record()
        if rec is None:
            return
        specimen = rec.get("specimen") or (rec.get("_specimens", "").split(":") or [None])[0]
        if specimen in self.s.data.specimens:
            self.s.specimen = specimen
            if rec.get("_comp") is not None:
                self.s.current = rec["_comp"]
            if self.on_goto:
                self.on_goto()

    def _flag(self, event=None):
        rec = self._selected_record()
        if rec is not None and rec.get("_comp") is not None:
            self.s.toggle_component_quality(rec["_comp"])

    def _figure_bytes(self):
        dirs, planes, means, _, _, vectors = self._collect()
        comp = self.comp.value
        title = f"{comp} · {self.level.value} {self.name.value}" if comp != "all" else f"{self.level.value} {self.name.value}"
        fig = pub.directions_figure([(d[0], d[1], d[2], d[4]) for d in dirs], title=title, planes=planes,
                                    caption=f"({dc.COORD_NAMES[self.s.coord]})",
                                    means=self._plotted_means(means, dirs),
                                    mean_label=self.STAT_LABELS[self.stat.value], plane_vectors=vectors)
        buf = io.BytesIO()
        fig.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        return buf

    def sidebar(self):
        return pn.Column(section("Coordinates"), self.coord,
                         section("Level"), self.level, self.name, pn.Row(self.comp, pn.Column(section("Show"), self.show)),
                         section("Statistic"), self.stat,
                         self.table_head, pn.Row(self.goto_btn, self.flag_btn), self.table, self.planes_box)

    def panel(self):
        return pn.Column(pn.Row(plot_box(self.plot.fig, 460), pn.Column(section("Mean"), self.stats, self.download,
                                                                        scroll=True)))


# ===========================================================================
class PolesView(LazyView):
    """Site VGPs and the mean pole on a globe, plus the table behind them."""

    CENTRES = {"pole": "pole", "sites": "sites", "N pole": "north", "S pole": "south", "custom": "custom"}

    def __init__(self, session: Session):
        self.s = session
        self._syncing = False
        self.comp = pn.widgets.Select(name="Component", options=[], width=140)
        self.level = pn.widgets.RadioButtonGroup(options=["site", "sample"], value="site", button_type="primary",
                                                 button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.coord = coord_selector(session)
        self.unify = pn.widgets.Checkbox.from_param(session.param.unify_polarity,
                                                    name="unify polarity (about the principal axis)",
                                                    stylesheets=[CHECKBOX_CSS])
        self.invert = pn.widgets.Checkbox.from_param(session.param.flip_polarity,
                                                     name="flip polarity (report the antipodes)",
                                                     stylesheets=[CHECKBOX_CSS])
        self.centre = pn.widgets.RadioButtonGroup(options=self.CENTRES, value="pole", button_type="primary",
                                                  button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.lon0 = pn.widgets.FloatSlider(name="centre longitude", start=-180, end=360, step=1, value=0, width=195)
        self.lat0 = pn.widgets.FloatSlider(name="centre latitude", start=-90, end=90, step=1, value=90, width=195)
        self.plot = PoleMapPlot()
        self.plot.on_recentre(self._on_recentre)
        self.pole = pn.pane.HTML("", sizing_mode="stretch_width")
        self.notes = pn.pane.HTML("", sizing_mode="stretch_width")
        # short headers and no sort arrows: eight columns have to share the side column
        self.table = pn.widgets.Tabulator(pd.DataFrame(), height=430, show_index=False, disabled=True, sortable=False,
                                          sizing_mode="stretch_width", configuration={"headerSort": False},
                                          layout="fit_columns", text_align="right", stylesheets=[TABLE_ROW_CSS])
        self.download = pn.widgets.FileDownload(callback=self._figure_bytes, filename="vgps.pdf",
                                                label="Download figure (PDF)", button_type="primary", width=220)
        for w in (self.comp, self.level, self.centre):
            w.param.watch(self.redraw, "value")
        for w in (self.lon0, self.lat0):
            w.param.watch(self._on_slider, "value_throttled")
        session.param.watch(self._lazy_redraw, ["coord", "version", "unify_polarity", "flip_polarity"])
        self.redraw()

    # --- data ---------------------------------------------------------------
    def _compute(self):
        s = self.s
        names = s.data.component_names()
        if self.comp.options != names:
            self.comp.options = names
            if self.comp.value not in names:
                self.comp.value = names[0] if names else None
        comp = self.comp.value
        means = s.data.mean_directions(self.level.value, s.coord, comp)
        pole = s.data.mean_pole(s.coord, comp, self.level.value, common_polarity=s.unify_polarity,
                                flip=s.flip_polarity)
        return means, pole

    def _rows(self, means, pole):
        vgps = pole["vgps"] if pole else (means.dropna(subset=["vgp_lat"]) if "vgp_lat" in means else pd.DataFrame())
        key = self.level.value
        return vgps, [(float(v["vgp_lon"]), float(v["vgp_lat"]), str(v[key]), bool(v.get("flipped", False)))
                      for _, v in vgps.iterrows()]

    def _sites(self):
        used = set(self.s.data.names_at("site"))
        return [(lon, lat, name) for name, (lat, lon) in self.s.data.site_coords.items() if name in used]

    def _centre(self, pole, rows, sites):
        mode = self.centre.value
        if mode == "custom":
            return float(self.lon0.value), float(self.lat0.value)
        if mode == "north":
            return 0.0, 90.0
        if mode == "south":
            return 0.0, -90.0
        if mode == "sites":
            if pole and "site_lat" in pole:
                return pole["site_lon"], pole["site_lat"]
            if sites:
                return sites[0][0], sites[0][1]
        if pole:
            return pole["plon"], pole["plat"]
        if rows:
            return rows[0][0], rows[0][1]
        return 0.0, 90.0

    # --- interaction --------------------------------------------------------
    def _on_recentre(self, lon, lat):
        """The globe was clicked: reflect the new centre in the controls (no redraw needed)."""
        self._syncing = True
        try:
            self.centre.value = "custom"
            self.lon0.value, self.lat0.value = round(lon, 1), round(lat, 1)
        finally:
            self._syncing = False
        self._notes(self.plot.hidden)

    def _on_slider(self, event):
        if not self._syncing and self.centre.value == "custom":
            self.redraw()

    # --- drawing ------------------------------------------------------------
    def redraw(self, *events):
        if self.s.data is None or self._syncing:
            return
        means, pole = self._compute()
        vgps, rows = self._rows(means, pole)
        sites = self._sites()
        centre = self._centre(pole, rows, sites)
        if self.centre.value != "custom":
            self._syncing = True
            try:
                self.lon0.value, self.lat0.value = round(centre[0], 1), round(centre[1], 1)
            finally:
                self._syncing = False
        color = self.s.color_of(self.comp.value) if self.comp.value else "#2b2b2b"
        self.plot.update(rows, pole or None, sites, centre=centre, color=color)
        if pole:
            n_inv = int(round(pole["reversed_perc"] * pole["N"] / 100))
            # no "polarity" item: the side column's own controls say what was chosen,
            # and the antipode count says what it did
            items = [("pole", f'{pole["plon"]:.1f}°E, {pole["plat"]:.1f}°N'), ("A95", f'{pole["A95"]:.1f}°'),
                     ("K", f'{pole["K"]:.1f}'), ("N", pole["N"]),
                     ("antipodes taken", f'{n_inv} ({pole["reversed_perc"]:.0f}%)')]
            if "paleolat" in pole:
                items.append(("paleolatitude", f'{pole["paleolat"]:.1f} ± {pole["A95"]:.1f}° '
                                               f'<span style="{MUTED_STYLE}">(sites at {pole["site_lat"]:.1f}°N, '
                                               f'{pole["site_lon"]:.1f}°E)</span>'))
            self.pole.object = kpi(items)
        else:
            self.pole.object = (f'<div style="{MUTED_STYLE}">fewer than two VGPs available '
                                '(site latitude/longitude needed)</div>')
        self._notes(self.plot.hidden)
        key = self.level.value
        cols = [c for c in [key, "vgp_lat", "vgp_lon", "dir_dec", "dir_inc", "dir_alpha95", "dir_n_specimens", "flipped"]
                if c in vgps.columns]
        table = vgps[cols].copy() if len(vgps) else pd.DataFrame()
        if "flipped" in table.columns:
            table["flipped"] = table["flipped"].map({True: "↺", False: ""})
        num = [c for c in table.columns if c not in (key, "flipped")]
        table[num] = table[num].astype(float).round(1)
        self.table.value = table.rename(columns={"dir_dec": "dec", "dir_inc": "inc", "dir_alpha95": "α95",
                                                 "dir_n_specimens": "n", "vgp_lat": "plat", "vgp_lon": "plon",
                                                 "flipped": "flip"})
        self.download.filename = f"vgps_{self.comp.value}_{dc.COORD_NAMES[self.s.coord]}.pdf"

    def _notes(self, hidden):
        parts = [f'<span style="{MUTED_STYLE}">click a point on the globe to centre it there · open symbols: antipode taken</span>']
        if hidden:
            parts.append(f'<span style="color:#b45309">{hidden} VGP(s) on the far hemisphere</span>')
        self.notes.object = " · ".join(parts)

    def _figure_bytes(self):
        means, pole = self._compute()
        vgps, rows = self._rows(means, pole)
        sites = self._sites()
        centre = self._centre(pole, rows, sites)
        title = f"{self.comp.value} VGPs ({dc.COORD_NAMES[self.s.coord]}" + \
            (", polarity flipped)" if self.s.flip_polarity else ")")
        fig = pub.vgp_map_figure(rows, pole or None, sites, centre=centre, title=title,
                                 color=self.s.color_of(self.comp.value) if self.comp.value else "#3b6fb6")
        buf = io.BytesIO()
        fig.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        return buf

    def sidebar(self):
        return pn.Column(section("Coordinates"), self.coord,
                         pn.Row(self.comp, pn.Column(section("Level"), self.level)), self.unify, self.invert,
                         section("Globe centre · click the globe to move it"), self.centre, pn.Row(self.lon0, self.lat0),
                         section("VGPs plotted · plat/plon = VGP, dec/inc = mean direction"), self.table)

    def panel(self):
        return pn.Column(pn.Row(plot_box(self.plot.fig, 460), pn.Column(self.pole, self.notes, self.download)))


# ===========================================================================
class InterpretationsView(LazyView):
    """The *Fits* tab: every fit in the study; jump to a specimen, delete or flag in bulk, propagate a fit."""

    def __init__(self, session: Session):
        self.s = session
        self.table = pn.widgets.Tabulator(pd.DataFrame(), height=560, show_index=False, disabled=True,
                                          selectable="checkbox", sizing_mode="stretch_width",
                                          # local pagination: with "remote" the header
                                          # filters are applied in the browser only and
                                          # current_view (so the side plot) never sees them
                                          pagination="local", page_size=25, header_filters=True,
                                          stylesheets=[
                                              TABLE_ROW_CSS,
                                              ".tabulator-footer { text-align: left !important; } "
                                              ".tabulator-footer .tabulator-footer-contents "
                                              "{ justify-content: flex-start !important; } "
                                              ".tabulator-footer .tabulator-paginator { text-align: left !important; }"])
        self.goto_btn = pn.widgets.Button(name="Go to specimen", button_type="primary", width=140)
        self.delete_btn = pn.widgets.Button(name="Delete selected", button_type="danger", width=140)
        self.flag_btn = pn.widgets.Button(name="Toggle good/bad", button_type="warning", width=140)
        self.copy_site_btn = pn.widgets.Button(name="Copy current fit to site", width=180)
        self.copy_all_btn = pn.widgets.Button(name="Copy current fit to all specimens", width=240)
        self.goto_btn.on_click(self._goto)
        self.delete_btn.on_click(self._delete)
        self.flag_btn.on_click(self._flag)
        self.copy_site_btn.on_click(lambda e: self._copy(site_only=True))
        self.copy_all_btn.on_click(lambda e: self._copy(site_only=False))
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        # one colour picker per fit name: the same name has the same colour on every
        # specimen, in every view and in every exported figure
        self.pickers = {}
        self._syncing = False
        self.colors_row = pn.Row(pn.pane.HTML(f'<span style="{MUTED_STYLE}">color of fit in plots</span>',
                                              margin=(14, 8, 0, 0)))
        # the side column plots what the table shows: the ticked rows, or — with none
        # ticked — every fit the header filters leave listed
        self.plot = DirectionsPlot("Fits", size=SIDE_PLOT)
        self.plot_note = pn.pane.HTML("", sizing_mode="stretch_width")
        # A header filter typed in the browser reaches `table.filters`, but Panel
        # suppresses watchers while it syncs the table's own state back, so the change
        # arrives silently: the value is polled instead while the tab is on show.
        # (The watcher still covers ticking and programmatic filters.)
        self._filters_seen = []
        self._poll = None
        self.table.param.watch(self._redraw_plot, ["selection", "filters"])
        session.param.watch(self._lazy_redraw, ["coord", "version"])
        self.redraw()

    def set_active(self, active: bool):
        super().set_active(active)
        if active and self._poll is None and pn.state.curdoc is not None:
            self._poll = pn.state.add_periodic_callback(self._poll_filters, period=350)
        elif not active and self._poll is not None:
            self._poll.stop()
            self._poll = None

    def _poll_filters(self):
        current = list(self.table.filters or [])
        if current != self._filters_seen:
            self._filters_seen = current
            self._redraw_plot()

    def _sync_pickers(self, names):
        self._syncing = True
        try:
            for name in names:
                if name not in self.pickers:
                    picker = pn.widgets.ColorPicker(name=name, value=self.s.color_of(name), width=64,
                                                    margin=(0, 8, 0, 0))
                    picker.param.watch(lambda e, n=name: self._on_color(n, e.new), "value")
                    self.pickers[name] = picker
                    self.colors_row.append(picker)
                elif self.pickers[name].value != self.s.color_of(name):
                    self.pickers[name].value = self.s.color_of(name)
            for name in [n for n in self.pickers if n not in names]:
                self.colors_row.remove(self.pickers.pop(name))
        finally:
            self._syncing = False

    def _on_color(self, name, color):
        if not self._syncing and color:
            self.s.set_color(name, color)

    def _selected(self):
        comps = self.s.data.components
        return [comps[i] for i in self.table.selection if i < len(comps)]

    def _plotted(self):
        """The fits the side column draws: the ticked rows, or all the filters leave listed.

        Returns (components, what) — ``what`` names the source for the caption.
        """
        sel = self._selected()
        if sel:
            return sel, "ticked"
        comps = self.s.data.components
        # current_view is the filtered (and sorted) frame, indexed as the value frame,
        # which is built row for row from data.components
        view = getattr(self.table, "current_view", None)
        if view is None or len(view) == len(comps):
            return list(comps), "listed"
        return [comps[i] for i in view.index if isinstance(i, (int, np.integer)) and i < len(comps)], "listed"

    def _redraw_plot(self, *events):
        if self.s.data is None:
            return
        comps, what = self._plotted()
        coord = self.s.active_coord
        dirs, planes, flagged = [], [], 0
        for comp in comps:
            if comp.quality != "g":            # flagged bad: excluded here as in the means
                flagged += 1
                continue
            res = self.s.data.fit(comp, coord)
            if res is None:
                continue
            color = self.s.color_of(comp.name)
            if res.direction_type == "p":
                planes.append((res.dir_dec, res.dir_inc, color))
            else:
                dirs.append((res.dir_dec, res.dir_inc, comp.specimen, comp.name, color))
        n = len(dirs) + len(planes)
        self.plot.update(dirs, planes, [], title=dc.COORD_NAMES[coord])
        parts = [f"<b>{n}</b> fit{'s' if n != 1 else ''} ticked in the table" if what == "ticked"
                 else f"<b>{n}</b> of {len(self.s.data.components)} fits listed"]
        if planes:
            parts.append(f"{len(planes)} planes as great circles" if len(planes) > 1
                         else "1 plane as a great circle")
        if flagged:
            parts.append(f"{flagged} flagged bad, not plotted")
        self.plot_note.object = f'<span style="{MUTED_STYLE}">{" · ".join(parts)}</span>'

    def _goto(self, event=None):
        sel = self._selected()
        if sel:
            self.s.specimen = sel[0].specimen
            self.s.current = sel[0]

    def _delete(self, event=None):
        self.s.delete_components(self._selected())

    def _flag(self, event=None):
        for comp in self._selected():
            comp.quality = "b" if comp.quality == "g" else "g"
        self.s._changed()

    def _copy(self, site_only: bool):
        if self.s.current is None:
            return
        if site_only:
            targets = self.s.data.specimens_in("site", self.s.spec.site)
        else:
            targets = self.s.data.specimen_names
        n = self.s.copy_current_to(targets)
        self.s.status = f"copied fit {self.s.current.name} to {n} specimens"

    def redraw(self, *events):
        s = self.s
        if s.data is None:
            return
        coord = s.active_coord
        rows = []
        for comp in s.data.components:
            spec = s.data.specimens[comp.specimen]
            res = s.data.fit(comp, coord)
            labels = spec.steps["label"]
            rows.append(dict(specimen=comp.specimen, site=spec.site, fit=comp.name, type=comp.fit_type,
                             **{"from": labels[comp.imin], "to": labels[comp.imax]},
                             dec=_fmt(res.dir_dec) if res else "–", inc=_fmt(res.dir_inc) if res else "–",
                             MAD=_fmt(res.dir_mad_free) if res else "–", n=res.dir_n_measurements if res else 0,
                             q=comp.quality))
        self.table.value = pd.DataFrame(rows, columns=["specimen", "site", "fit", "type", "from", "to", "dec", "inc",
                                                       "MAD", "n", "q"])
        info = s.study_summary()
        self.summary.object = kpi([f'<b>{info["fits"]}</b> fits',
                                   f'<b>{info["interpreted"]}</b> of {info["specimens"]} specimens interpreted',
                                   f'<b>{info["sites"]}</b> sites'])
        self._sync_pickers(info["components"])
        self._redraw_plot()

    def sidebar(self):
        return pn.Column(section("Fits plotted · tick rows or filter the table"),
                         plot_box(self.plot.fig, SIDE_PLOT), self.plot_note)

    def panel(self):
        return pn.Column(pn.Row(self.summary, self.colors_row),
                         pn.Row(self.goto_btn, self.delete_btn, self.flag_btn, self.copy_site_btn, self.copy_all_btn),
                         self.table)


# ===========================================================================
class ExportView:
    """Write MagIC tables (validated), save/load .redo, export publication figures."""

    POLICY = ('Writes <code>specimens</code>, <code>samples</code>, <code>sites</code>, <code>locations</code> and '
              '<code>measurements</code> tables into the output directory. The directional results of the '
              'specimens, samples, sites and locations of this dataset are replaced by the current '
              'interpretations (a fit deleted here disappears from the tables); every other row — intensity '
              'results, entities without demag data — and all descriptive metadata (coordinates, ages, '
              'lithologies …) are kept. Means, VGPs and poles are written for every coordinate system ticked '
              'below, in the polarity chosen on the Poles tab (one polarity axis for the whole study). Only MagIC 3 '
              'columns are written, and the result is checked with the MagIC validator. When the output directory '
              'is the data directory itself, the original tables are copied once to '
              '<code>backup_before_pmagpy_directions/</code>.')

    def __init__(self, session: Session):
        self.s = session
        self.output_dir = pn.widgets.TextInput.from_param(session.param.output_dir, name="Output directory",
                                                          sizing_mode="stretch_width")
        self.analysts = pn.widgets.TextInput(name="Analyst(s)", value=env("ANALYST", ""), width=240,
                                             placeholder="written to the analysts column", stylesheets=[INPUT_CSS])
        self.coords = pn.widgets.CheckBoxGroup(options=COORD_OPTIONS, value=list(COORD_OPTIONS.values()), inline=True,
                                               stylesheets=[CHECKBOX_CSS])
        self.levels = pn.widgets.CheckBoxGroup(options=["sample", "site", "location"],
                                               value=["sample", "site", "location"], inline=True,
                                               stylesheets=[CHECKBOX_CSS])
        self.site_over = pn.widgets.RadioButtonGroup(options={"specimens": "specimens", "sample means": "samples"},
                                                     value="specimens", button_type="primary", button_style="outline",
                                                     stylesheets=[BUTTON_GROUP_CSS])
        self.mean_coords = pn.widgets.CheckBoxGroup(options=COORD_OPTIONS, value=[dc.COORD_GEOGRAPHIC, dc.COORD_TILT],
                                                    inline=True, stylesheets=[CHECKBOX_CSS])
        self.write_meas = pn.widgets.Checkbox(name="write measurements.txt with good/bad flags", value=True,
                                              stylesheets=[CHECKBOX_CSS])
        self.criteria = pn.widgets.Checkbox.from_param(session.param.apply_criteria, name="apply criteria.txt",
                                                       stylesheets=[CHECKBOX_CSS])
        self.criteria_note = pn.pane.HTML("", sizing_mode="stretch_width")
        session.param.watch(lambda e: self._describe_criteria(), ["version", "apply_criteria"])   # loads bump version
        self._describe_criteria()
        self.write_btn = pn.widgets.Button(name="Write MagIC tables", button_type="primary", width=180)
        self.validate_btn = pn.widgets.Button(name="Validate output tables", width=180)
        self.write_btn.on_click(self._write)
        self.validate_btn.on_click(lambda e: self._validate())
        self.redo_path = pn.widgets.TextInput(name=".redo file", value="", sizing_mode="stretch_width")
        self.save_redo_btn = pn.widgets.Button(name="Save .redo", width=110)
        self.load_redo_btn = pn.widgets.Button(name="Load .redo (replace)", width=160)
        self.import_btn = pn.widgets.Button(name="Import from specimens.txt", width=190)
        self.save_redo_btn.on_click(self._save_redo)
        self.load_redo_btn.on_click(self._load_redo)
        self.import_btn.on_click(self._import)
        self.fig_format = pn.widgets.RadioButtonGroup(options=["pdf", "svg", "png"], value="pdf", button_type="primary",
                                                      button_style="outline", stylesheets=[BUTTON_GROUP_CSS])
        self.fig_layout = pn.widgets.RadioButtonGroup(options={"panels": "panel", "insets": "inset",
                                                               "Zijderveld only": "zijderveld"},
                                                      value="panel", button_type="primary", button_style="outline",
                                                      stylesheets=[BUTTON_GROUP_CSS])
        self.fig_proj = pn.widgets.Select(name="Projection", options={v: k for k, v in dc.PROJECTIONS.items()},
                                          value="ew", width=240)
        self.fig_coord = pn.widgets.Select(name="Coordinates", options=COORD_OPTIONS, value=dc.COORD_GEOGRAPHIC,
                                           width=160)
        self.fig_current_btn = pn.widgets.Button(name="Save current specimen figure", button_type="primary")
        self.fig_all_btn = pn.widgets.Button(name="Save figures for all interpreted specimens")
        self.overview_btn = pn.widgets.Button(name="Save directions overview (one net per component)")
        self.vgp_btn = pn.widgets.Button(name="Save VGP maps (one per component)")
        self.fig_current_btn.on_click(self._save_current_figure)
        self.fig_all_btn.on_click(self._save_all_figures)
        self.overview_btn.on_click(self._save_overview)
        self.vgp_btn.on_click(self._save_vgp_maps)
        self.preview = pn.pane.Matplotlib(None, dpi=100, tight=True, sizing_mode="fixed", width=900, height=600)
        self.preview_btn = pn.widgets.Button(name="Preview current specimen", width=200)
        self.preview_btn.on_click(lambda e: self._preview())
        self.status = pn.pane.Markdown("", sizing_mode="stretch_width")        # export messages only
        self.report = pn.pane.HTML("", sizing_mode="stretch_width")            # validator report
        session.param.watch(lambda e: setattr(self.redo_path, "value", os.path.join(e.new, REDO_NAME)),
                            "output_dir")
        self.redo_path.value = os.path.join(session.output_dir, REDO_NAME)
        # means, poles and figures default to the dataset's best coordinate system
        session.param.watch(lambda e: self._follow_default_coord(), "directory")
        self._follow_default_coord()

    def _describe_criteria(self):
        """The checkbox says how many directional criteria the directory carries; none disables it."""
        n = self.s.criteria_count()
        self.criteria.disabled = n == 0
        self.criteria.name = f"apply the {n} directional criteria in criteria.txt" if n else "apply criteria.txt"
        if n == 0:
            text = ("no <code>criteria.txt</code> with DE-SPEC / DE-SAMP / DE-SITE rows in this directory "
                    "(the hub's Metadata page writes one) - every fit and mean is written as it is")
        elif self.s.apply_criteria:
            failing = len(self.s.data.failing_components())
            text = (f"{failing} fits fail DE-SPEC and are written <code>result_quality</code> 'b' and left out "
                    "of the means; a sample or site mean failing its criterion is written 'b' and left out of "
                    "the level above (location means, poles). Blank statistics do not fail a criterion.")
        else:
            text = "the criteria are not applied: every fit and mean is written as it is"
        self.criteria_note.object = f'<div style="{MUTED_STYLE}">{text}</div>'

    def _follow_default_coord(self):
        """Figures default to the dataset's best coordinate system; means and poles are
        written for every system the dataset supports."""
        if self.s.data is None:
            return
        self.mean_coords.value = list(self.s.default_mean_coords())
        self.fig_coord.value = self.s.data.default_coord()

    # --- MagIC tables ---------------------------------------------------------
    def _write(self, event=None):
        try:
            written = self.s.export_tables(coords=tuple(self.coords.value), levels=tuple(self.levels.value),
                                           mean_coords=tuple(self.mean_coords.value) or None,
                                           site_over=self.site_over.value,
                                           write_measurements=self.write_meas.value,
                                           analysts=self.analysts.value.strip() or None)
        except Exception as exc:
            self.status.object = f"**Export failed:** {exc}"
            return
        lines = [f"- `{p}`" for p in written]
        backup = os.path.join(self.s.output_dir, self.s.BACKUP_DIR)
        if os.path.isdir(backup):
            lines.append(f"- originals kept in `{backup}`")
        dropped = [w for w in self.s.data.warnings if "dropped non-MagIC" in w]
        if dropped:
            lines.append("- " + "; ".join(sorted(set(dropped))))
        self.status.object = "Wrote:\n" + "\n".join(lines)
        self._validate()

    def _validate(self):
        try:
            report = self.s.validate_output()
        except Exception as exc:
            self.report.object = f'<div style="color:#c0392b">Validation failed to run: {exc}</div>'
            return
        rows = []
        for table, result in report.items():
            if result is None:
                rows.append(f'<div><span style="color:#2e8b57">✓</span> <b>{table}</b> passes the MagIC validator</div>')
                continue
            problems = []
            if result["missing_cols"]:
                problems.append("missing required columns: " + ", ".join(result["missing_cols"]))
            if result["missing_groups"]:
                problems.append("needs a column from: " + ", ".join(result["missing_groups"]))
            if result["bad_cols"]:
                problems.append(f'{len(result["bad_rows"])} row(s) with bad values in: ' + ", ".join(result["bad_cols"]))
            # cell-level, so the analyst can go to the cell rather than the table
            cells = result["failing_items"]
            examples = [f'{c["row"]} · {c["column"]}: {c["problem"]}' if c["row"] else f'{c["column"]}: {c["problem"]}'
                        for c in cells[:6]]
            if len(cells) > 6:
                examples.append(f"… and {len(cells) - 6} more")
            detail = "".join(f'<div style="{MUTED_STYLE};margin-left:18px">{e}</div>' for e in examples)
            rows.append(f'<div><span style="color:#c0392b">✗</span> <b>{table}</b>: ' + "; ".join(problems) + detail
                        + '</div>')
        self.report.object = "".join(rows) or f'<div style="{MUTED_STYLE}">no tables to validate</div>'

    # --- .redo ----------------------------------------------------------------
    def _save_redo(self, event=None):
        path = self.redo_path.value or os.path.join(self.s.output_dir, REDO_NAME)
        self.status.object = f"Saved `{self.s.save_redo(path)}`"

    def _load_redo(self, event=None):
        path = self.redo_path.value
        if not os.path.exists(path):
            self.status.object = f"**No such file:** `{path}`"
            return
        n = self.s.load_redo(path)
        self.status.object = f"Loaded {n} fits from `{path}` (replacing the previous interpretations)"

    def _import(self, event=None):
        n = self.s.import_from_specimens_table()
        self.status.object = f"Imported {n} fits from the specimens table of the data directory"

    # --- figures --------------------------------------------------------------
    def _specimen_figure(self, name):
        s = self.s
        spec = s.data.specimens[name]
        coord = self.fig_coord.value if spec.has_coord(self.fig_coord.value) else dc.COORD_SPECIMEN
        fits = s.fits(name, coord)
        return pub.specimen_figure(spec, fits, coord=coord, projection=self.fig_proj.value,
                                   layout=self.fig_layout.value)

    def _preview(self):
        self.preview.object = self._specimen_figure(self.s.specimen)

    def _figures_dir(self):
        return os.path.join(self.s.output_dir, "figures")

    def _save_current_figure(self, event=None):
        fig = self._specimen_figure(self.s.specimen)
        path = os.path.join(self._figures_dir(), f"{self.s.specimen}.{self.fig_format.value}")
        self.status.object = f"Saved `{pub.save_figure(fig, path)}`"
        self.preview.object = fig

    def _save_all_figures(self, event=None):
        names = sorted({c.specimen for c in self.s.data.components}, key=dc._natural_key)
        out = self._figures_dir()
        for name in names:
            pub.save_figure(self._specimen_figure(name), os.path.join(out, f"{name}.{self.fig_format.value}"))
        self.status.object = f"Saved {len(names)} specimen figures to `{out}`"

    def _save_overview(self, event=None):
        coord = self.fig_coord.value
        try:
            fig = pub.components_overview_figure(self.s.data, coord, color_of=self.s.color_of)
        except ValueError as exc:
            self.status.object = f"**No overview:** {exc}"
            return
        path = os.path.join(self._figures_dir(), f"directions_{dc.COORD_NAMES[coord]}.{self.fig_format.value}")
        self.status.object = f"Saved `{pub.save_figure(fig, path)}`"
        self.preview.object = fig

    def _save_vgp_maps(self, event=None):
        coord = self.fig_coord.value
        used = set(self.s.data.names_at("site"))
        sites = [(lon, lat, name) for name, (lat, lon) in self.s.data.site_coords.items() if name in used]
        saved = []
        for comp in self.s.data.component_names():
            pole = self.s.data.mean_pole(coord, comp, "site", common_polarity=self.s.unify_polarity,
                                         flip=self.s.flip_polarity)
            means = self.s.data.mean_directions("site", coord, comp)
            vgps = pole["vgps"] if pole else (means.dropna(subset=["vgp_lat"]) if "vgp_lat" in means else means)
            if len(vgps) == 0:
                continue
            rows = [(v["vgp_lon"], v["vgp_lat"], v["site"], bool(v.get("flipped", False))) for _, v in vgps.iterrows()]
            title = f"{comp} VGPs ({dc.COORD_NAMES[coord]}" + (", polarity flipped)" if self.s.flip_polarity else ")")
            fig = pub.vgp_map_figure(rows, pole or None, sites, title=title, color=self.s.color_of(comp))
            saved.append(pub.save_figure(fig, os.path.join(self._figures_dir(),
                                                           f"vgps_{comp}_{dc.COORD_NAMES[coord]}.{self.fig_format.value}")))
            self.preview.object = fig
        self.status.object = ("Saved:\n" + "\n".join(f"- `{p}`" for p in saved)) if saved else \
            "**No VGPs:** site latitude/longitude are needed"

    def panel(self):
        tables = pn.Column(
            section("MagIC tables"),
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">{self.POLICY}</div>', sizing_mode="stretch_width"),
            pn.Row(pn.Column(pn.pane.HTML("specimen rows in"), self.coords),
                   pn.Column(pn.pane.HTML("means and poles in"), self.mean_coords),
                   pn.Column(pn.pane.HTML("means for"), self.levels),
                   pn.Column(pn.pane.HTML("site means over"), self.site_over)),
            pn.Row(self.analysts, pn.Column(self.write_meas, self.criteria, margin=(28, 10, 0, 10))),
            self.criteria_note,
            pn.Row(self.write_btn, self.validate_btn),
            self.status, self.report,
            section("Fits (.redo)"),
            pn.pane.HTML(f'<div style="{MUTED_STYLE}">Fits are auto-saved to <code>{AUTOSAVE_NAME}</code> in the '
                         'output directory after every change and restored on the next load; the legacy Demag GUI '
                         'reads the same format.</div>'),
            self.redo_path, pn.Row(self.save_redo_btn, self.load_redo_btn, self.import_btn),
        )
        figures = pn.Column(
            section("Publication figures"),
            pn.Row(self.fig_proj, self.fig_coord, pn.Column(section("format"), self.fig_format),
                   pn.Column(section("layout"), self.fig_layout)),
            pn.Row(self.preview_btn, self.fig_current_btn, self.fig_all_btn),
            pn.Row(self.overview_btn, self.vgp_btn),
            self.preview,
        )
        return pn.Column(self.output_dir, tables, pn.layout.Divider(), figures)


# ===========================================================================
class DataView(DirectoryChooser):
    """Switch between MagIC directories.

    The widgets and the behaviour are the toolkit's :class:`DirectoryChooser`,
    shared with the hub and the other applications; this only says what this
    application counts and what it wants the dialog to say.
    """

    def __init__(self, session: Session, chooser=None, chooser_available=None):
        super().__init__(
            session, recent_file=RECENT_FILE, chooser=chooser, chooser_available=chooser_available,
            chooser_stub=env("CHOOSER_STUB"),
            count=lambda s: f"{len(s.data.specimens) if s.data else 0} specimens",
            note="Fits are auto-saved per dataset; switching datasets restores what you had there.")

