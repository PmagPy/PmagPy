"""
Bokeh figure builders for PmagPy Intensity.

All the geometry comes from ``pmagpy.paleointensity`` and ``pmagpy.pint_stats``,
so a figure never computes anything a table could disagree with. The four
specimen figures are an Arai plot, a Zijderveld diagram of the zero-field
steps, an equal-area net of those directions, and a magnetization-decay curve;
a fifth draws the pTRM, tail and additivity checks as differences.
"""
from __future__ import annotations

import numpy as np
from bokeh.events import Reset, Tap
from bokeh.models import (BoxAnnotation, ColumnDataSource, CustomJS, FactorRange, HoverTool,
                          Label, LabelSet, Legend, LegendItem, Span, Whisker)
from bokeh.plotting import figure

import pmagpy.paleointensity as pint
from pmagpy import pint_stats as ps

from pmagpy_panel.nets import declutter_labels, keep_circular, net_figure
from pmagpy_panel.theme import (HORIZONTAL_COLOR, MEAN_COLOR, NET_COLOR, POINT_EDGE, POINT_FILL,
                                VERTICAL_COLOR, style_figure)

#: the selected segment, the excluded points, and the three kinds of check
SEGMENT_COLOR = "#1f4e9c"
EXCLUDED_COLOR = "#9aa3ad"
PTRM_COLOR = "#2a9d8f"
TAIL_COLOR = "#e76f51"
ADD_COLOR = "#7b5ea7"
ZI_COLOR = "#1f4e9c"
IZ_COLOR = "#c8102e"
BAD_COLOR = "#c0392b"


class AraiPlot:
    """The Arai plot: pTRM gained against NRM remaining, with the checks.

    Tap picks a step (the caller moves the nearer bound); box-select sets both
    bounds at once. The selected segment is drawn with its best-fit line, and
    the SCAT box is shown when the statistics have one.
    """

    FRAME = 430
    CHROME = 74

    def __init__(self, frame: int = FRAME):
        self.frame = frame
        self.fig = figure(frame_width=frame, frame_height=frame, width=frame + 70,
                          height=frame + self.CHROME, match_aspect=False,
                          tools="box_zoom,box_select,tap,pan,wheel_zoom,reset,save",
                          active_drag="box_zoom", active_tap="tap", sizing_mode="fixed",
                          min_border_left=54, min_border_right=8, min_border_top=6,
                          toolbar_location="below", frame_align=False, name="arai")
        style_figure(self.fig)
        self.fig.xaxis.axis_label = "pTRM gained"
        self.fig.yaxis.axis_label = "NRM remaining"
        self._resets = 0
        self.fig.js_on_change("tags", CustomJS(args=dict(fig=self.fig), code="fig.reset.emit()"))

        self.scat = BoxAnnotation(fill_color=SEGMENT_COLOR, fill_alpha=0.06,
                                  line_color=SEGMENT_COLOR, line_alpha=0.25, visible=False)
        self.fig.add_layout(self.scat)
        self.line = ColumnDataSource(dict(x=[], y=[]))
        self.fig.line("x", "y", source=self.line, color=SEGMENT_COLOR, line_width=2)

        self.src = ColumnDataSource(dict(x=[], y=[], label=[], text=[], seq=[], step=[], color=[]))
        self.sel = ColumnDataSource(dict(x=[], y=[], label=[]))
        self.bad = ColumnDataSource(dict(x=[], y=[], label=[]))
        solid = dict(nonselection_fill_alpha=1.0, nonselection_line_alpha=1.0,
                     selection_fill_alpha=1.0, selection_line_alpha=1.0)
        self.fig.line("x", "y", source=self.src, color=EXCLUDED_COLOR, line_width=1, line_alpha=0.5)
        points = self.fig.scatter("x", "y", source=self.src, marker="circle", size=9,
                                  fill_color="color", line_color=POINT_EDGE, **solid)
        chosen = self.fig.scatter("x", "y", source=self.sel, marker="circle", size=13,
                                  fill_color=None, line_color=SEGMENT_COLOR, line_width=2, **solid)
        flagged = self.fig.scatter("x", "y", source=self.bad, marker="x", size=12,
                                   line_color=BAD_COLOR, line_width=2, **solid)
        self.fig.add_layout(LabelSet(x="x", y="y", text="text", source=self.src, x_offset=6,
                                     y_offset=4, text_font_size="8pt", text_color="#6b7280"))

        self.ptrm = ColumnDataSource(dict(x=[], y=[], xs=[], ys=[], label=[]))
        self.tail = ColumnDataSource(dict(x=[], y=[], xs=[], ys=[], label=[]))
        self.add = ColumnDataSource(dict(x=[], y=[], xs=[], ys=[], label=[]))
        self.fig.multi_line("xs", "ys", source=self.ptrm, color=PTRM_COLOR, line_width=1)
        self.fig.multi_line("xs", "ys", source=self.tail, color=TAIL_COLOR, line_width=1)
        self.fig.multi_line("xs", "ys", source=self.add, color=ADD_COLOR, line_width=1)
        p = self.fig.scatter("x", "y", source=self.ptrm, marker="triangle", size=10,
                             fill_color=PTRM_COLOR, line_color=PTRM_COLOR, **solid)
        t = self.fig.scatter("x", "y", source=self.tail, marker="square", size=9,
                             fill_color="white", line_color=TAIL_COLOR, line_width=2, **solid)
        a = self.fig.scatter("x", "y", source=self.add, marker="diamond", size=11,
                             fill_color=ADD_COLOR, line_color=ADD_COLOR, **solid)
        self.check_renderers = [p, t, a]
        self.fig.add_tools(HoverTool(renderers=[points, chosen, flagged, p, t, a],
                                     tooltips=[("step", "@label")]))
        legend = Legend(items=[LegendItem(label="ZI / IZ steps", renderers=[points]),
                               LegendItem(label="pTRM check", renderers=[p]),
                               LegendItem(label="tail check", renderers=[t]),
                               LegendItem(label="additivity check", renderers=[a])],
                        orientation="horizontal", location="center", click_policy="hide",
                        border_line_color=None, background_fill_alpha=0, padding=0, spacing=18,
                        label_text_font_size="9pt", label_text_color="#374151",
                        glyph_height=14, glyph_width=14)
        self.fig.add_layout(legend, "below")
        self.fig.min_border_bottom = 4

    # ----- interaction ------------------------------------------------------
    def on_select(self, callback):
        """``callback(indices)`` on a tap or a box selection of Arai points."""
        def _tap(event):
            indices = self.src.selected.indices
            if indices:
                callback(list(indices))
        self.src.selected.on_change("indices", lambda attr, old, new: new and callback(list(new)))
        self.fig.on_event(Tap, lambda event: None)

    def reset_view(self) -> None:
        self._resets += 1
        self.fig.tags = [self._resets]

    def set_frame(self, frame: int) -> None:
        self.frame = frame
        self.fig.frame_width = frame
        self.fig.frame_height = frame
        self.fig.width = frame + 70
        self.fig.height = frame + self.CHROME

    # ----- drawing ----------------------------------------------------------
    def update(self, spec, bounds, stats=None, normalize=True, show_checks=True,
               label_every: int = -1) -> None:
        arai = spec.arai if spec is not None else None
        if arai is None or arai.n == 0:
            for src in (self.src, self.sel, self.bad, self.ptrm, self.tail, self.add, self.line):
                src.data = {k: [] for k in src.data}
            self.scat.visible = False
            return
        scale = arai.y[0] if (normalize and arai.y[0]) else 1.0
        x, y = arai.x / scale, arai.y / scale
        labels = [f"{t - pint.KELVIN_OFFSET:.0f}" for t in arai.temps]
        labels[0] = "NRM"
        inside = set(range(bounds[0], bounds[1] + 1)) if bounds else set()
        colors = [SEGMENT_COLOR if i in inside else EXCLUDED_COLOR for i in range(arai.n)]
        text = self._thin_labels(x, y, labels, label_every)
        self.src.data = dict(x=list(x), y=list(y), label=[f"{l}°C" for l in labels], text=text,
                             seq=list(range(arai.n)), step=list(arai.steps), color=colors)
        if bounds:
            self.sel.data = dict(x=[x[bounds[0]], x[bounds[1]]], y=[y[bounds[0]], y[bounds[1]]],
                                 label=[f"{labels[bounds[0]]}°C", f"{labels[bounds[1]]}°C"])
        else:
            self.sel.data = dict(x=[], y=[], label=[])

        flagged = spec.steps[spec.steps["quality"] == "b"]
        self.bad.data = dict(x=[], y=[], label=[])
        if len(flagged):
            bx, by, bl = [], [], []
            for _, row in flagged.iterrows():
                temp = float(row["treat_temp"])
                where = np.flatnonzero(np.isclose(arai.temps, temp))
                if len(where):
                    bx.append(float(x[where[0]]))
                    by.append(float(y[where[0]]))
                    bl.append(f"{temp - pint.KELVIN_OFFSET:.0f}°C flagged bad")
            self.bad.data = dict(x=bx, y=by, label=bl)

        if show_checks:
            self._draw_checks(arai, x, y, scale)
        else:
            for src in (self.ptrm, self.tail, self.add):
                src.data = {k: [] for k in src.data}

        self.line.data = dict(x=[], y=[])
        self.scat.visible = False
        if bounds and stats and stats.get("b") and stats["b"].is_value:
            b = float(stats["b"])
            xs = x[bounds[0]:bounds[1] + 1]
            ys = y[bounds[0]:bounds[1] + 1]
            fit = ps.york_regression(xs, ys)
            lo, hi = float(np.min(xs)), float(np.max(xs))
            self.line.data = dict(x=[lo, hi],
                                  y=[fit["y_int"] + fit["b"] * lo, fit["y_int"] + fit["b"] * hi])
            self._draw_scat(fit, stats)

    def _draw_scat(self, fit, stats) -> None:
        threshold = stats.get("SCAT_beta_threshold")
        if not (threshold and threshold.is_value) or not np.isfinite(fit["b"]) or fit["b"] == 0:
            return
        sigma = float(threshold) * abs(fit["b"])
        b1, b2 = fit["b"] - 2 * sigma, fit["b"] + 2 * sigma
        a1 = fit["ybar"] - b1 * fit["xbar"]
        a2 = fit["ybar"] - b2 * fit["xbar"]
        if b1 == 0 or b2 == 0:
            return
        self.scat.left, self.scat.right = 0.0, max(-a1 / b1, -a2 / b2)
        self.scat.bottom, self.scat.top = 0.0, max(a1, a2)
        self.scat.visible = True

    def _draw_checks(self, arai, x, y, scale) -> None:
        def rows(checks, kind):
            px, py, xs, ys, labels = [], [], [], [], []
            for chk in checks:
                if kind == "tail":
                    cx, cy = float(x[chk.i]), float(chk.y / scale)
                    ox, oy = float(x[chk.i]), float(y[chk.i])
                else:
                    cx, cy = float(chk.x / scale), float(y[chk.i])
                    ox, oy = float(x[chk.i]), float(y[chk.i])
                px.append(cx)
                py.append(cy)
                xs.append([ox, cx])
                ys.append([oy, cy])
                temp = arai.temps[chk.i] - pint.KELVIN_OFFSET
                if kind == "tail":
                    labels.append(f"tail check to {temp:.0f}°C")
                else:
                    peak = arai.temps[chk.j] - pint.KELVIN_OFFSET
                    labels.append(f"{'pTRM' if kind == 'ptrm' else 'additivity'} check to "
                                  f"{temp:.0f}°C after {peak:.0f}°C")
            return dict(x=px, y=py, xs=xs, ys=ys, label=labels)
        self.ptrm.data = rows(arai.ptrm_checks, "ptrm")
        self.tail.data = rows(arai.tail_checks, "tail")
        self.add.data = rows(arai.additivity_checks, "add")

    @staticmethod
    def _thin_labels(x, y, labels, label_every: int) -> list:
        if label_every == 0:
            return [""] * len(labels)
        if label_every == 1:
            return list(labels)
        keep = declutter_labels(np.asarray(x, dtype=float), np.asarray(y, dtype=float), labels)
        return list(keep)


class SpecimenZijderveldPlot:
    """The zero-field steps as an orthogonal projection."""

    def __init__(self, size: int = 320):
        self.size = size
        self.fig = figure(frame_width=size, frame_height=size, width=size + 20,
                          height=size + 60, match_aspect=True,
                          tools="box_zoom,pan,wheel_zoom,reset,save", active_drag="box_zoom",
                          sizing_mode="fixed", min_border_left=8, min_border_right=8,
                          min_border_top=2, toolbar_location="below", frame_align=False,
                          name="zijderveld")
        style_figure(self.fig, hide_axes=True)
        self.fig.add_layout(Span(location=0, dimension="width", line_color=NET_COLOR, line_width=1))
        self.fig.add_layout(Span(location=0, dimension="height", line_color=NET_COLOR, line_width=1))
        self.src = ColumnDataSource(dict(x=[], y_h=[], y_v=[], label=[]))
        self.fig.line("x", "y_h", source=self.src, color=HORIZONTAL_COLOR, line_width=1, line_alpha=0.35)
        self.fig.line("x", "y_v", source=self.src, color=VERTICAL_COLOR, line_width=1, line_alpha=0.35)
        h = self.fig.scatter("x", "y_h", source=self.src, marker="circle", size=8,
                             color=HORIZONTAL_COLOR)
        v = self.fig.scatter("x", "y_v", source=self.src, marker="square", size=8,
                             color=VERTICAL_COLOR)
        self.sel = ColumnDataSource(dict(x=[], y_h=[], y_v=[], label=[]))
        self.fig.scatter("x", "y_h", source=self.sel, marker="circle", size=12, fill_color=None,
                         line_color=SEGMENT_COLOR, line_width=2)
        self.fig.scatter("x", "y_v", source=self.sel, marker="square", size=12, fill_color=None,
                         line_color=SEGMENT_COLOR, line_width=2)
        self.fig.add_tools(HoverTool(renderers=[h, v], tooltips=[("step", "@label")]))

    def set_size(self, size: int) -> None:
        self.size = size
        self.fig.frame_width = self.fig.frame_height = size
        self.fig.width, self.fig.height = size + 20, size + 60

    def update(self, spec, bounds) -> None:
        if spec is None or spec.arai is None:
            self.src.data = {k: [] for k in self.src.data}
            self.sel.data = {k: [] for k in self.sel.data}
            return
        z = pint.zijderveld_xy(spec)
        labels = [f"{t - pint.KELVIN_OFFSET:.0f}°C" for t in z["temps"]]
        self.src.data = dict(x=list(z["h_x"]), y_h=list(z["h_y"]), y_v=list(z["v_y"]), label=labels)
        if bounds:
            lo, hi = bounds
            self.sel.data = dict(x=[z["h_x"][lo], z["h_x"][hi]], y_h=[z["h_y"][lo], z["h_y"][hi]],
                                 y_v=[z["v_y"][lo], z["v_y"][hi]],
                                 label=[labels[lo], labels[hi]])
        else:
            self.sel.data = {k: [] for k in self.sel.data}


class StepNetPlot:
    """Equal-area net of the zero-field directions, with the fitted direction."""

    def __init__(self, size: int = 320):
        self.size = size
        self.fig = net_figure("", size)
        self.src = ColumnDataSource(dict(x=[], y=[], label=[], fill=[]))
        self.sel = ColumnDataSource(dict(x=[], y=[], label=[]))
        self.mean = ColumnDataSource(dict(x=[], y=[], label=[]))
        r = self.fig.scatter("x", "y", source=self.src, marker="circle", size=8,
                             fill_color="fill", line_color=POINT_EDGE)
        self.fig.scatter("x", "y", source=self.sel, marker="circle", size=12, fill_color=None,
                         line_color=SEGMENT_COLOR, line_width=2)
        # the toolkit's convention: a circle is a measured direction, a square is
        # a mean, and a derived symbol takes the dark edge
        m = self.fig.scatter("x", "y", source=self.mean, marker="square", size=11,
                             fill_color=MEAN_COLOR, line_color=POINT_EDGE)
        self.fig.add_tools(HoverTool(renderers=[r, m], tooltips=[("", "@label")]))
        keep_circular(self.fig)

    def set_size(self, size: int) -> None:
        self.size = size
        self.fig.frame_width = self.fig.frame_height = size
        self.fig.width = self.fig.height = size + 20

    def update(self, spec, bounds, stats=None) -> None:
        if spec is None or spec.arai is None:
            for src in (self.src, self.sel, self.mean):
                src.data = {k: [] for k in src.data}
            return
        decs, incs = [], []
        for vec in spec.arai.nrm_vectors:
            dec, inc, _ = ps.cart_to_dir(vec)
            decs.append(dec)
            incs.append(inc)
        x, y = _equal_area(decs, incs)
        labels = [f"{t - pint.KELVIN_OFFSET:.0f}°C  {d:.1f}/{i:.1f}"
                  for t, d, i in zip(spec.arai.temps, decs, incs)]
        self.src.data = dict(x=list(x), y=list(y), label=labels,
                             fill=[POINT_FILL if i >= 0 else "white" for i in incs])
        if bounds:
            lo, hi = bounds
            self.sel.data = dict(x=[x[lo], x[hi]], y=[y[lo], y[hi]],
                                 label=[labels[lo], labels[hi]])
        else:
            self.sel.data = {k: [] for k in self.sel.data}
        if stats and stats.get("Dec_Free") and stats["Dec_Free"].is_value:
            mx, my = _equal_area([float(stats["Dec_Free"])], [float(stats["Inc_Free"])])
            self.mean.data = dict(x=list(mx), y=list(my),
                                  label=[f"fit {float(stats['Dec_Free']):.1f}/"
                                         f"{float(stats['Inc_Free']):.1f}"])
        else:
            self.mean.data = {k: [] for k in self.mean.data}


class DecayPlot:
    """NRM remaining and pTRM gained against temperature."""

    def __init__(self, size: int = 320, height: int = 200):
        self.fig = figure(frame_width=size, frame_height=height, width=size + 70,
                          height=height + 60, tools="pan,box_zoom,wheel_zoom,reset,save",
                          sizing_mode="fixed", toolbar_location="below", frame_align=False,
                          min_border_left=54, name="decay")
        style_figure(self.fig)
        self.fig.xaxis.axis_label = "temperature (°C)"
        self.fig.yaxis.axis_label = "M / NRM"
        self.nrm = ColumnDataSource(dict(x=[], y=[]))
        self.trm = ColumnDataSource(dict(x=[], y=[]))
        self.fig.line("x", "y", source=self.nrm, color=VERTICAL_COLOR, line_width=2)
        n = self.fig.scatter("x", "y", source=self.nrm, marker="circle", size=7,
                             color=VERTICAL_COLOR)
        self.fig.line("x", "y", source=self.trm, color=PTRM_COLOR, line_width=2, line_dash="dashed")
        t = self.fig.scatter("x", "y", source=self.trm, marker="square", size=7, color=PTRM_COLOR)
        self.bounds = ColumnDataSource(dict(x=[], y=[]))
        self.fig.scatter("x", "y", source=self.bounds, marker="circle", size=13, fill_color=None,
                         line_color=SEGMENT_COLOR, line_width=2)
        legend = Legend(items=[LegendItem(label="NRM remaining", renderers=[n]),
                               LegendItem(label="pTRM gained", renderers=[t])],
                        orientation="horizontal", location="center", border_line_color=None,
                        background_fill_alpha=0, padding=0, spacing=18,
                        label_text_font_size="9pt", label_text_color="#374151")
        self.fig.add_layout(legend, "below")

    def set_size(self, size: int, height: int) -> None:
        self.fig.frame_width, self.fig.frame_height = size, height
        self.fig.width, self.fig.height = size + 70, height + 60

    def update(self, spec, bounds) -> None:
        if spec is None or spec.arai is None:
            for src in (self.nrm, self.trm, self.bounds):
                src.data = {k: [] for k in src.data}
            return
        arai = spec.arai
        scale = arai.y[0] if arai.y[0] else 1.0
        temps = arai.temps - pint.KELVIN_OFFSET
        self.nrm.data = dict(x=list(temps), y=list(arai.y / scale))
        self.trm.data = dict(x=list(temps), y=list(arai.x / scale))
        if bounds:
            lo, hi = bounds
            self.bounds.data = dict(x=[temps[lo], temps[hi]],
                                    y=[arai.y[lo] / scale, arai.y[hi] / scale])
        else:
            self.bounds.data = {k: [] for k in self.bounds.data}


class ChecksPlot:
    """The alteration checks as differences against temperature."""

    def __init__(self, size: int = 320, height: int = 190):
        self.fig = figure(frame_width=size, frame_height=height, width=size + 70,
                          height=height + 60, tools="pan,box_zoom,wheel_zoom,reset,save",
                          sizing_mode="fixed", toolbar_location="below", frame_align=False,
                          min_border_left=54, name="checks")
        style_figure(self.fig)
        self.fig.xaxis.axis_label = "temperature (°C)"
        self.fig.yaxis.axis_label = "difference (% of the fit)"
        self.fig.add_layout(Span(location=0, dimension="width", line_color=NET_COLOR,
                                 line_width=1, line_dash="dotted"))
        self.sources = {}
        renderers = []
        for kind, color, marker, label in (("ptrm", PTRM_COLOR, "triangle", "pTRM check"),
                                           ("tail", TAIL_COLOR, "square", "tail check"),
                                           ("add", ADD_COLOR, "diamond", "additivity check")):
            src = ColumnDataSource(dict(x=[], y=[], label=[]))
            self.sources[kind] = src
            renderer = self.fig.scatter("x", "y", source=src, marker=marker, size=10,
                                        fill_color=color, line_color=color)
            self.fig.segment("x", 0, "x", "y", source=src, color=color, line_width=1)
            renderers.append(LegendItem(label=label, renderers=[renderer]))
        self.fig.add_tools(HoverTool(tooltips=[("", "@label")]))
        legend = Legend(items=renderers, orientation="horizontal", location="center",
                        border_line_color=None, background_fill_alpha=0, padding=0, spacing=18,
                        label_text_font_size="9pt", label_text_color="#374151")
        self.fig.add_layout(legend, "below")

    def set_size(self, size: int, height: int) -> None:
        self.fig.frame_width, self.fig.frame_height = size, height
        self.fig.width, self.fig.height = size + 70, height + 60

    def update(self, spec, bounds) -> None:
        empty = {k: [] for k in ("x", "y", "label")}
        if spec is None or spec.arai is None or bounds is None:
            for src in self.sources.values():
                src.data = dict(empty)
            return
        arai = spec.arai
        fit = ps.york_regression(arai.x[bounds[0]:bounds[1] + 1], arai.y[bounds[0]:bounds[1] + 1])
        length = fit.get("line_length") or 1.0
        for kind, checks in (("ptrm", arai.ptrm_checks), ("tail", arai.tail_checks),
                             ("add", arai.additivity_checks)):
            x, y, labels = [], [], []
            for chk in checks:
                temp = arai.temps[chk.i] - pint.KELVIN_OFFSET
                if kind == "tail":
                    diff = chk.y - arai.y[chk.i]
                else:
                    diff = chk.x - arai.x[chk.i]
                x.append(float(temp))
                y.append(float(100.0 * diff / length))
                labels.append(f"{temp:.0f}°C: {100.0 * diff / length:+.1f}%")
            self.sources[kind].data = dict(x=x, y=y, label=labels)


class GroupPlot:
    """Specimen intensities within a group, with the mean and its scatter."""

    def __init__(self, size: int = 460, height: int = 300):
        # a categorical x axis: one slot per specimen, named on the axis
        self.fig = figure(frame_width=size, frame_height=height, width=size + 80,
                          height=height + 60, tools="pan,box_zoom,wheel_zoom,reset,save",
                          sizing_mode="fixed", toolbar_location="below", frame_align=False,
                          min_border_left=60, name="groups", x_range=FactorRange())
        style_figure(self.fig)
        self.fig.xaxis.axis_label = "specimen"
        self.fig.yaxis.axis_label = "intensity (µT)"
        self.fig.xaxis.major_label_orientation = 0.9
        self.src = ColumnDataSource(dict(x=[], y=[], lower=[], upper=[], color=[], label=[]))
        renderer = self.fig.scatter("x", "y", source=self.src, marker="circle", size=10,
                                    fill_color="color", line_color=POINT_EDGE)
        self.fig.add_layout(Whisker(source=self.src, base="x", upper="upper", lower="lower",
                                    line_color=EXCLUDED_COLOR))
        self.mean = Span(location=0, dimension="width", line_color=MEAN_COLOR, line_width=2)
        self.band = BoxAnnotation(fill_color=MEAN_COLOR, fill_alpha=0.08, visible=False)
        self.fig.add_layout(self.mean)
        self.fig.add_layout(self.band)
        self.fig.add_tools(HoverTool(renderers=[renderer], tooltips=[("", "@label")]))

    def update(self, results, mean=None, sd=None, accepted=None) -> None:
        names = [r.specimen for r in results]
        self.fig.x_range.factors = names
        accepted = accepted or set()
        self.src.data = dict(
            x=names, y=[r.b_anc for r in results],
            lower=[r.b_anc - (r.sigma if np.isfinite(r.sigma) else 0) for r in results],
            upper=[r.b_anc + (r.sigma if np.isfinite(r.sigma) else 0) for r in results],
            color=[SEGMENT_COLOR if r.specimen in accepted else EXCLUDED_COLOR for r in results],
            label=[f"{r.specimen}: {r.b_anc:.1f} µT" +
                   ("" if r.specimen in accepted else " (rejected)") for r in results])
        if mean is not None and np.isfinite(mean):
            self.mean.location = float(mean)
            if sd is not None and np.isfinite(sd):
                self.band.bottom, self.band.top = float(mean - sd), float(mean + sd)
                self.band.visible = True
            else:
                self.band.visible = False
        else:
            self.band.visible = False


def _equal_area(decs, incs):
    """Lower-hemisphere equal-area coordinates for a list of directions."""
    decs = np.radians(np.asarray(decs, dtype=float))
    incs = np.radians(np.abs(np.asarray(incs, dtype=float)))
    r = np.sqrt(1.0 - np.sin(incs)) / np.sqrt(2.0) * np.sqrt(2.0)
    return r * np.sin(decs), r * np.cos(decs)
