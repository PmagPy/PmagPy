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
from .logger import Hotkeys, StepLogger
from .plots import DecayPlot, DirectionsPlot, PoleMapPlot, StepEqualAreaPlot, ZijderveldPlot
from .session import (REDO_NAME, AUTOSAVE_NAME, Session, env, load_recent, looks_like_magic_dir,
                      native_choose_directory, native_chooser_available)
from .theme import BUTTON_GROUP_CSS, CHECKBOX_CSS, INPUT_CSS, KPI_ITEM, MUTED_STYLE, SECTION_STYLE, kpi, lighten

FIT_OPTIONS = {f"{v} ({k})": k for k, v in dc.FIT_TYPES.items()}
COORD_OPTIONS = {v: k for k, v in dc.COORD_NAMES.items()}
MEAN_COLUMNS = ["dir_dec", "dir_inc", "dir_alpha95", "dir_k", "dir_r", "dir_n_specimens", "dir_n_samples",
                "dir_n_sites", "dir_n_specimens_lines", "dir_n_specimens_planes", "vgp_lat", "vgp_lon",
                "vgp_dp", "vgp_dm"]


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
            stylesheets=[".tabulator-row.tabulator-selected { background-color: #dbe4f3 !important; "
                         "color: #111 !important; font-weight: 600; }"])
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

        s.param.watch(self._reset_pending, ["specimen"])
        s.param.watch(self.redraw, ["specimen", "coord", "projection", "label_every", "version", "current"])
        self.redraw()

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
            pn.Row(pn.pane.Bokeh(self.zij.fig, margin=0),
                   pn.Column(self.eq.fig, self.decay.fig, width=ZijderveldPlot.SIDE + 10, margin=0,
                             styles={"overflow": "visible"}),
                   margin=0),
            pn.Row(section("Fits · click a row to select it"), self.hint, margin=0),
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
        self.plot = DirectionsPlot("Directions")
        self.stats = pn.pane.DataFrame(pd.DataFrame(), index=False, sizing_mode="stretch_width")
        self.download = pn.widgets.FileDownload(callback=self._figure_bytes, filename="directions.pdf",
                                                label="Download figure (PDF)", button_type="primary", width=220)
        # the side-column list of the fits (or lower-level means) that are plotted
        self.table = pn.widgets.Tabulator(pd.DataFrame(), height=520, show_index=False, disabled=True, selectable=1,
                                          sortable=False, configuration={"headerSort": False},
                                          sizing_mode="stretch_width", layout="fit_data_table", text_align="right")
        self._records = []
        self._table_df = None
        self.goto_btn = pn.widgets.Button(name="Go to specimen", button_type="primary", width=140)
        self.flag_btn = pn.widgets.Button(name="Toggle good/bad", button_type="warning", width=140)
        self.goto_btn.on_click(self._goto)
        self.flag_btn.on_click(self._flag)
        self.on_goto = None          # set by the app: switches to the Specimen tab
        self.level.param.watch(self._on_level, "value")      # options first ...
        for w in (self.level, self.name, self.comp, self.show):
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
        dirs, planes, records = [], [], []
        if over == "specimens":
            for spec_name in s.data.specimens_in(level, name):
                spec = s.data.specimens[spec_name]
                for c in s.data.components_for(spec_name):
                    if comp and c.name != comp:
                        continue
                    res = s.data.fit(c, coord)
                    color = s.color_of(c.name)
                    rec = dict(specimen=spec_name, fit=c.name, type="plane" if c.fit_type == "DE-BFP" else "line",
                               dec="–", inc="–", MAD="–", n=0, q=c.quality, _comp=c, _color=color)
                    if res is not None:
                        rec.update(dec=_fmt(res.dir_dec), inc=_fmt(res.dir_inc), MAD=_fmt(res.dir_mad_free),
                                   n=res.dir_n_measurements)
                        if c.quality == "g":
                            if res.direction_type == "p":
                                planes.append((res.dir_dec, res.dir_inc, color))
                            else:
                                dirs.append((res.dir_dec, res.dir_inc, spec_name, c.name, color))
                    records.append(rec)
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
        return dirs, planes, means, records

    def _mean_list(self, means):
        """(mean dict, colour) per component — a star and α95 for each, even when all are shown."""
        return [(m.to_dict(), self.s.color_of(m["dir_comp_name"])) for _, m in means.iterrows()] if len(means) else []

    def redraw(self, *events):
        if self.s.data is None or not self.name.value:
            return
        dirs, planes, means, records = self._collect()
        title = f"{self.level.value} {self.name.value} · {self.comp.value} · {dc.COORD_NAMES[self.s.coord]}"
        self.plot.update(dirs, planes, self._mean_list(means), title=title)
        self._records = records
        df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in records])
        colors = [r["_color"] for r in records]
        if not (df.equals(self._table_df) and colors == getattr(self, "_table_colors", None)):
            self._table_df, self._table_colors = df, colors
            self.table.value = df
            self.table.style.clear()
            flags = [r.get("q", "g") for r in records]

            def style_row(row, colors=colors, flags=flags):
                i = row.name if isinstance(row.name, int) else 0
                c = colors[i] if i < len(colors) else "#ffffff"
                fill = f"background: {lighten(c, 0.85)}" + ("; color:#9aa1ab; text-decoration: line-through"
                                                            if i < len(flags) and flags[i] == "b" else "")
                return [f"border-left: 6px solid {c}; {fill}"] + [fill] * (len(row) - 1)
            if len(df):
                self.table.style.apply(style_row, axis=1)
        cols = [c for c in ["dir_comp_name"] + MEAN_COLUMNS if c in means.columns]
        table = means[cols].round(1) if len(means) else pd.DataFrame()
        self.stats.object = table.rename(columns=lambda c: c.replace("dir_", "").replace("_specimens", "_spec")
                                         .replace("alpha95", "α95").replace("comp_name", "component"))
        self.download.filename = f"{self.level.value}_{self.name.value}_{self.comp.value}.pdf"

    def _selected_record(self):
        sel = self.table.selection
        return self._records[sel[0]] if sel and sel[0] < len(self._records) else None

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
        dirs, planes, means, _ = self._collect()
        comp = self.comp.value
        title = f"{comp} · {self.level.value} {self.name.value}" if comp != "all" else f"{self.level.value} {self.name.value}"
        fig = pub.directions_figure([(d[0], d[1], d[2], d[4]) for d in dirs], title=title, planes=planes,
                                    caption=f"({dc.COORD_NAMES[self.s.coord]})", means=self._mean_list(means))
        buf = io.BytesIO()
        fig.savefig(buf, format="pdf", bbox_inches="tight")
        buf.seek(0)
        return buf

    def sidebar(self):
        return pn.Column(section("Coordinates"), self.coord,
                         section("Level"), self.level, self.name, pn.Row(self.comp, pn.Column(section("Show"), self.show)),
                         section("Plotted fits · select a row"), pn.Row(self.goto_btn, self.flag_btn), self.table)

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
                                          layout="fit_columns", text_align="right")
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
            items = [("pole", f'{pole["plon"]:.1f}°E, {pole["plat"]:.1f}°N'), ("A95", f'{pole["A95"]:.1f}°'),
                     ("K", f'{pole["K"]:.1f}'), ("N", pole["N"]),
                     ("antipodes taken", f'{n_inv} ({pole["reversed_perc"]:.0f}%)'),
                     ("polarity", "flipped" if self.s.flip_polarity else "as computed")]
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
                                          pagination="remote", page_size=25, header_filters=True,
                                          stylesheets=[
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
        session.param.watch(self._lazy_redraw, ["coord", "version"])
        self.redraw()

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
            items = result["failing_items"]
            examples = []
            try:
                for _, item in items.head(3).iterrows():
                    issues = item.get("issues", {})
                    examples.append(f"{item.name}: " + "; ".join(str(v) for v in dict(issues).values()))
            except Exception:
                pass
            detail = "".join(f'<div style="{MUTED_STYLE};margin-left:18px">{e}</div>' for e in examples)
            rows.append(f'<div><span style="color:#c0392b">✗</span> <b>{table}</b>: ' + "; ".join(problems) + detail
                        + f'<div style="{MUTED_STYLE};margin-left:18px">full list in {table}_errors.txt</div></div>')
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
            pn.Row(self.analysts, pn.Column(self.write_meas, margin=(28, 10, 0, 10))),
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
class DataView:
    """Switch between MagIC directories: a compact block for the side column and a
    modal with recent directories, a path field and a directory browser."""

    def __init__(self, session: Session, chooser=native_choose_directory, chooser_available=None):
        import sys
        self.s = session
        self.on_loaded = None       # callback set by the app (closes the modal)
        self.chooser = chooser
        self.chooser_available = native_chooser_available() if chooser_available is None else chooser_available
        self.summary = pn.pane.HTML("", sizing_mode="stretch_width")
        self.change_btn = pn.widgets.Button(name="Change data…", button_type="primary", width=140)
        app_name = {"darwin": "Finder", "win32": "Explorer"}.get(sys.platform, "the system dialog")
        self.native_btn = pn.widgets.Button(name=f"Browse with {app_name}…", button_type="primary", width=220,
                                            disabled=not self.chooser_available)
        self.native_btn.on_click(self._browse_native)
        self.recent = pn.widgets.Select(name="Recent directories", options=[], size=6, sizing_mode="stretch_width")
        self.path = pn.widgets.TextInput(name="MagIC directory (must contain measurements.txt)",
                                         value=session.directory, sizing_mode="stretch_width")
        self.browser = pn.widgets.FileSelector(directory=os.path.dirname(session.directory) or os.getcwd(),
                                               only_files=False, show_hidden=False, height=240,
                                               name="select a directory, then Load")
        self.load_btn = pn.widgets.Button(name="Load", button_type="success", width=120)
        self.message = pn.pane.HTML("", sizing_mode="stretch_width")
        self.recent.param.watch(lambda e: setattr(self.path, "value", e.new) if e.new else None, "value")
        self.browser.param.watch(self._on_browse, "value")
        self.load_btn.on_click(self._load)
        session.param.watch(lambda e: self._refresh(), ["directory", "output_dir"])
        self._refresh()

    def _browse_native(self, event=None):
        """Run the system folder dialog off the server thread, then load the choice."""
        import threading
        self.native_btn.disabled = True
        self.message.object = f'<div style="{MUTED_STYLE}">Choose a folder in the dialog that just opened …</div>'
        start = self.path.value.strip() or self.s.directory
        # the document must be captured here: pn.state.curdoc is not visible from the
        # worker thread, and model updates without the document lock are lost or
        # half-applied (the app then shows the old dataset under the new name)
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

    def _refresh(self):
        s = self.s
        n = len(s.data.specimens) if s.data else 0
        self.summary.object = kpi([("<b>" + os.path.basename(s.directory.rstrip("/")) + "</b>", ""),
                                   f'<span style="{MUTED_STYLE}">{n} specimens</span>',
                                   f'<span style="{MUTED_STYLE}" title="{s.directory}">{_shorten(s.directory)}</span>'])
        recent = load_recent()
        self.recent.options = {(_shorten(d, 70)): d for d in recent}
        self.path.value = s.directory

    def _on_browse(self, event):
        if not event.new:
            return
        chosen = event.new[0]
        self.path.value = chosen if os.path.isdir(chosen) else os.path.dirname(chosen)

    def _load(self, event=None):
        target = os.path.expanduser(self.path.value.strip())
        if not looks_like_magic_dir(target):
            self.message.object = (f'<div style="color:#c0392b">No <code>measurements.txt</code> in '
                                   f'<code>{target}</code></div>')
            return
        self.message.object = f'<div style="{MUTED_STYLE}">Loading {target} …</div>'
        if self.s.load(target):
            self.message.object = f'<div style="{MUTED_STYLE}">{self.s.status}</div>'
            if self.on_loaded:
                self.on_loaded()
        else:
            self.message.object = f'<div style="color:#c0392b">{self.s.status}</div>'

    def sidebar(self):
        return pn.Column(section("Data"), pn.Row(self.summary, self.change_btn))

    def modal(self):
        fallback = pn.Card(self.browser, title="In-page browser (for sessions served from another machine)",
                           collapsed=True, sizing_mode="stretch_width")
        return pn.Column(
            pn.pane.HTML('<h3 style="margin:0 0 6px 0">Open a MagIC directory</h3>'
                         f'<div style="{MUTED_STYLE}">Fits are auto-saved per dataset; switching '
                         'datasets restores what you had there.</div>'),
            pn.Row(self.native_btn, self.message),
            self.recent, pn.Row(self.path, self.load_btn), fallback, width=760,
        )


def _shorten(path: str, n: int = 48) -> str:
    return path if len(path) <= n else "…" + path[-(n - 1):]
