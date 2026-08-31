"""Bokeh figure builders for the interactive views (all geometry from pmagpy.demag)."""
from __future__ import annotations

import numpy as np
from bokeh.events import Reset, Tap
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, Label, LabelSet, Legend, LegendItem, Span
from bokeh.plotting import figure

import pmagpy.demag as dc
import pmagpy.demag_geo as geo

from .theme import (HORIZONTAL_COLOR, LAND_COLOR, LAND_EDGE, MEAN_COLOR, NET_COLOR, OCEAN_COLOR, SITE_COLOR,
                    VERTICAL_COLOR, style_figure)

NET_TICKS = [(d, i) for d in range(0, 360, 90) for i in range(10, 90, 10)]


def _net(fig, labels=("N", "E", "S", "W")):
    theta = np.linspace(0, 2 * np.pi, 361)
    fig.line(np.cos(theta), np.sin(theta), color=NET_COLOR, line_width=1)
    ticks = np.array([dc.pmag.dimap(d, i) for d, i in NET_TICKS])
    fig.scatter(ticks[:, 0], ticks[:, 1], marker="cross", size=5, color=NET_COLOR, line_width=0.7)
    fig.scatter([0], [0], marker="cross", size=5, color=NET_COLOR)
    for txt, (x, y), align, base in zip(labels, [(0, 1.0), (1.0, 0), (0, -1.0), (-1.0, 0)],
                                        ["center", "left", "center", "right"],
                                        ["bottom", "middle", "top", "middle"]):
        fig.add_layout(Label(x=x, y=y, text=txt, text_font_size="9pt", text_color=NET_COLOR,
                             text_align=align, text_baseline=base, x_offset={"left": 3, "right": -3}.get(align, 0),
                             y_offset={"bottom": 2, "top": -2}.get(base, 0)))


def declutter_labels(x, y, labels, min_sep: float = 0.035):
    """Keep step labels that are at least ``min_sep`` of the plot extent apart (first and last always)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) == 0:
        return labels
    extent = max(np.ptp(x), np.ptp(y), 1e-9)
    out, placed = [], []
    for i, (xi, yi, lab) in enumerate(zip(x, y, labels)):
        keep = i in (0, len(x) - 1) or not placed or \
            min(np.hypot(xi - px, yi - py) for px, py in placed) >= min_sep * extent
        if keep:
            placed.append((xi, yi))
        out.append(lab if keep else "")
    return np.array(out, dtype=object)


def net_figure(title, size: int, tools="tap,pan,wheel_zoom,reset,save", labels=("N", "E", "S", "W")):
    # A square canvas with no axes, no title row, no toolbar strip and equal borders
    # is a square frame by construction, so equal explicit ranges keep the net
    # circular without over-constraining the layout (frame + outer sizes) — which
    # browsers resolve differently. Captions belong outside the figure; the tap
    # tool stays active without a toolbar, so points on the net can still be picked.
    # frame_align=False: Bokeh otherwise aligns the frames of plots that share a
    # layout, so a net stacked above the M/M₀ plot would inherit that plot's wide
    # axis border and be squeezed into an ellipse.
    fig = figure(width=size, height=size, x_range=(-1.13, 1.13), y_range=(-1.13, 1.13), tools=tools,
                 sizing_mode="fixed", min_border=4, toolbar_location=None, frame_align=False,
                 name="equal_area_net")
    style_figure(fig, hide_axes=True)
    _net(fig, labels)
    keep_circular(fig)
    return fig


def keep_circular(fig):
    """Guarantee a net is drawn as a circle whatever the frame's pixel shape.

    Whenever the frame's pixel size changes (or the ranges are reset) the x range
    is rescaled so that data units per pixel are identical in x and y, with the
    y range as the reference. On a square frame this is a no-op; on a frame
    that a browser or layout has made non-square the net gains margin rather
    than becoming an ellipse.
    """
    guard = CustomJS(args=dict(fig=fig), code="""
        const w = fig.inner_width, h = fig.inner_height
        if (!(w > 0 && h > 0)) return
        const xr = fig.x_range, yr = fig.y_range
        const per_px = (yr.end - yr.start) / h
        const cx = (xr.start + xr.end) / 2, half = per_px * w / 2
        if (Math.abs((xr.end - xr.start) - 2 * half) > 1e-9) {
            xr.start = cx - half
            xr.end = cx + half
        }
    """)
    fig.js_on_change("inner_width", guard)
    fig.js_on_change("inner_height", guard)
    fig.js_on_event(Reset, guard)


class ZijderveldPlot:
    """Orthogonal projection with box/tap selection of steps."""

    # outer height = frame + legend strip + toolbar row + borders (measured in the browser)
    FRAME = 520
    TOP = 2              # min_border_top: the frame starts at the top of the canvas
    CHROME = 70
    SIDE = 340           # width of the net / M/M₀ column plots

    def __init__(self, frame=FRAME):
        # a fixed square frame at the very top of the canvas; the outer width/height
        # are given explicitly so the layout reserves the right space. No title (the
        # information line under the plots has it) and the toolbar *below* the
        # frame next to the legend, so nothing sits above the diagram and no strip
        # separates it from the side plots. drag = zoom box (as in the legacy GUI);
        # tap picks a step; box-select stays in the toolbar.
        self.fig = figure(frame_width=frame, frame_height=frame, width=frame + 16, height=frame + self.CHROME,
                          match_aspect=True, tools="box_zoom,box_select,tap,pan,wheel_zoom,reset,save",
                          active_drag="box_zoom", active_tap="tap", sizing_mode="fixed",
                          min_border_left=8, min_border_right=8, min_border_top=self.TOP, toolbar_location="below",
                          frame_align=False, name="zijderveld")
        self.frame = frame
        self._view_key = None
        # a change of the figure's tags makes the client run the plot's own reset
        # (ranges and selection), exactly as the toolbar button would; tags travel
        # with the figure, unlike a detached model
        self._resets = 0
        self.fig.js_on_change("tags", CustomJS(args=dict(fig=self.fig), code="fig.reset.emit()"))
        style_figure(self.fig, hide_axes=True)
        self.fig.add_layout(Span(location=0, dimension="width", line_color=NET_COLOR, line_width=1))
        self.fig.add_layout(Span(location=0, dimension="height", line_color=NET_COLOR, line_width=1))
        self.src = ColumnDataSource(dict(x=[], y_h=[], y_v=[], label=[], text=[], seq=[]))
        self.bad = ColumnDataSource(dict(x=[], y_h=[], y_v=[], label=[]))
        # faint connecting traces beneath solid symbols; a tap must never fade the points
        self.fig.line("x", "y_h", source=self.src, color=HORIZONTAL_COLOR, line_width=1, line_alpha=0.3)
        self.fig.line("x", "y_v", source=self.src, color=VERTICAL_COLOR, line_width=1, line_alpha=0.3)
        solid = dict(nonselection_fill_alpha=1.0, nonselection_line_alpha=1.0, selection_fill_alpha=1.0,
                     selection_line_alpha=1.0)
        rh = self.fig.scatter("x", "y_h", source=self.src, marker="circle", size=9, color=HORIZONTAL_COLOR, **solid)
        rv = self.fig.scatter("x", "y_v", source=self.src, marker="square", size=9, color=VERTICAL_COLOR, **solid)
        bh = self.fig.scatter("x", "y_h", source=self.bad, marker="circle", size=9, fill_color="white",
                              line_color=HORIZONTAL_COLOR, **solid)
        bv = self.fig.scatter("x", "y_v", source=self.bad, marker="square", size=9, fill_color="white",
                              line_color=VERTICAL_COLOR, **solid)
        self.fig.add_layout(LabelSet(x="x", y="y_v", text="text", source=self.src, x_offset=6, y_offset=-4,
                                     text_font_size="8pt", text_color="#6b7280"))
        self.fig.add_tools(HoverTool(renderers=[rh, rv, bh, bv], tooltips=[("step", "@label")]))
        # legend in a strip below the frame: it can never cover axes, labels or data
        legend = Legend(items=[LegendItem(label="horizontal projection (circles)", renderers=[rh, bh]),
                               LegendItem(label="vertical projection (squares)", renderers=[rv, bv])],
                        orientation="horizontal", location="center", click_policy="hide",
                        border_line_color=None, background_fill_alpha=0, padding=0, spacing=24,
                        label_text_font_size="9pt", label_text_color="#374151", glyph_height=14, glyph_width=14)
        self.fig.add_layout(legend, "below")
        self.fig.min_border_bottom = 4
        self.fits = ColumnDataSource(dict(xs=[], ys=[], color=[], name=[]))
        self.fig.multi_line("xs", "ys", source=self.fits, color="color", line_width=2.5)
        # arrowheads at the outward end of each fit line: the fitted direction is the
        # vector removed between the bounds, which points away from the origin
        self.heads = ColumnDataSource(dict(x=[], y=[], angle=[], color=[]))
        self.fig.scatter("x", "y", source=self.heads, marker="triangle", size=12, angle="angle",
                         fill_color="color", line_color="color")
        # axis-end labels at the frame edges: the along-axis coordinate is in screen
        # pixels (the frame is a fixed square), the other one is the axis itself
        # (data 0), so the labels stay at the edges through zoom and pan and never
        # sit on the data
        backing = dict(background_fill_color="white", background_fill_alpha=0.75, text_font_size="11pt")
        edge = frame - 6
        self.lbl_right = Label(x=edge, y=0, x_units="screen", text="", y_offset=5, text_align="right",
                               text_baseline="bottom", **backing)
        self.lbl_left = Label(x=6, y=0, x_units="screen", text="", y_offset=5, text_align="left",
                              text_baseline="bottom", **backing)
        self.lbl_top = Label(x=0, y=edge, y_units="screen", text="", x_offset=6, text_align="left",
                             text_baseline="top", text_color="#374151", **backing)
        self.lbl_bottom_h = Label(x=0, y=6, y_units="screen", text="", x_offset=-6, text_align="right",
                                  text_baseline="bottom", text_color=HORIZONTAL_COLOR, **backing)
        self.lbl_bottom_v = Label(x=0, y=6, y_units="screen", text="", x_offset=6, text_align="left",
                                  text_baseline="bottom", text_color=VERTICAL_COLOR, **backing)
        for lbl in (self.lbl_right, self.lbl_left, self.lbl_top, self.lbl_bottom_h, self.lbl_bottom_v):
            self.fig.add_layout(lbl)

    def on_select(self, callback):
        def handler(attr, old, new):
            if new:
                callback(list(self.src.data["seq"][i] for i in new))
                self.src.selected.indices = []          # the tap has been consumed
        self.src.selected.on_change("indices", handler)

    def reset_view(self):
        """Undo any zoom/pan on the client (what the toolbar's reset button does)."""
        self._resets += 1
        self.fig.tags = ["reset", self._resets]

    def update(self, spec, fits, coord, rotation, label_every, projection):
        # a zoom box belongs to one view of one specimen: switching specimen,
        # coordinates, projection (or the rotation of the "best-fit dec" projection)
        # resets it, editing a fit's bounds keeps it
        key = (spec.name, coord, projection, round(float(rotation), 3))
        if key != self._view_key:
            self._view_key = key
            self.reset_view()
        z = dc.zijderveld_xy(spec.steps, coord, rotation_dec=rotation)
        good = (z["quality"] == "g").values
        text = z["label"].astype(str).copy()
        if label_every == 0:
            text[:] = ""
        elif label_every < 0:
            text[:] = declutter_labels(z["x"].values, z["y_v"].values, text.values)
        elif label_every > 1:
            text[z["sequence"] % label_every != 0] = ""
        self.src.data = dict(x=z["x"][good], y_h=z["y_h"][good], y_v=z["y_v"][good], label=z["label"][good],
                             text=text[good], seq=z["sequence"][good])
        self.bad.data = dict(x=z["x"][~good], y_h=z["y_h"][~good], y_v=z["y_v"][~good], label=z["label"][~good])
        xs, ys, cols, names = [], [], [], []
        hx, hy, hang, hcol = [], [], [], []
        for comp, res, color in fits:
            seg = dc.fit_line_segment(res, spec, coord, rotation_dec=rotation) if res is not None else None
            if seg is None:
                continue
            for ycol in ("y_h", "y_v"):
                px, py = list(seg["x"]), list(seg[ycol])
                xs.append(px); ys.append(py); cols.append(color); names.append(comp.name)
                near, far = (0, 1) if np.hypot(px[0], py[0]) < np.hypot(px[1], py[1]) else (1, 0)
                theta = np.arctan2(py[far] - py[near], px[far] - px[near])
                hx.append(px[far]); hy.append(py[far]); hang.append(theta - np.pi / 2); hcol.append(color)
        self.fits.data = dict(xs=xs, ys=ys, color=cols, name=names)
        self.heads.data = dict(x=hx, y=hy, angle=hang, color=hcol)
        labels = dc.axis_labels(coord, projection, rotation)
        self.lbl_right.text = labels["right"]
        self.lbl_left.text = labels["left"]
        self.lbl_bottom_h.text = labels["bottom_h"]
        self.lbl_bottom_v.text = labels["bottom_v"]
        self.lbl_top.text = ", ".join(t for t in (labels["top_h"], labels["top_v"]) if t)
        # the labels sit on their axis line; when the data push that line towards
        # an edge of the square frame, the text goes on the roomy side of the line
        xs = np.concatenate([z["x"].values, [0.0]])
        ys = np.concatenate([z["y_h"].values, z["y_v"].values, [0.0]])
        axis_on_right = abs(xs.min()) > xs.max()          # vertical axis (x = 0) in the right half
        axis_on_top = abs(ys.min()) > ys.max()            # horizontal axis (y = 0) in the upper half
        side = dict(text_align="right", x_offset=-6) if axis_on_right else dict(text_align="left", x_offset=6)
        self.lbl_top.update(**side)
        self.lbl_bottom_v.update(y=6, **side)              # stacked, both on the same side
        self.lbl_bottom_h.update(y=24, **side)
        vert = dict(text_baseline="top", y_offset=-5) if axis_on_top else dict(text_baseline="bottom", y_offset=5)
        self.lbl_right.update(**vert)
        self.lbl_left.update(**vert)


class StepEqualAreaPlot:
    """Equal-area plot of a specimen's steps with fitted directions and great circles."""

    def __init__(self, size=340):
        self.fig = net_figure(None, size)          # no title: the net speaks for itself
        self.src = ColumnDataSource(dict(x=[], y=[], fill=[], label=[], seq=[]))
        self.fig.line("x", "y", source=self.src, color="#9aa1ab", line_width=0.8)
        pts = self.fig.scatter("x", "y", source=self.src, size=8, fill_color="fill", line_color="#2b2b2b",
                               nonselection_fill_alpha=1.0, nonselection_line_alpha=1.0)
        self.fig.add_tools(HoverTool(renderers=[pts], tooltips=[("step", "@label")]))
        self.dirs = ColumnDataSource(dict(x=[], y=[], color=[], name=[]))
        stars = self.fig.scatter("x", "y", source=self.dirs, marker="star", size=17, fill_color="color",
                                 line_color="#2b2b2b", line_width=0.6)
        self.fig.add_tools(HoverTool(renderers=[stars], tooltips=[("component", "@name")]))
        self.circles = ColumnDataSource(dict(xs=[], ys=[], color=[]))
        self.fig.multi_line("xs", "ys", source=self.circles, color="color", line_width=2)

    def on_select(self, callback):
        def handler(attr, old, new):
            if new:
                callback(list(self.src.data["seq"][i] for i in new))
                self.src.selected.indices = []
        self.src.selected.on_change("indices", handler)

    def update(self, spec, fits, coord):
        dec_col, inc_col = dc.COORD_COLUMNS[coord]
        steps = spec.steps
        x, y = dc.equal_area_xy(steps[dec_col], steps[inc_col])
        fill = np.array(["#2b2b2b"] * len(steps), dtype=object)
        for comp, res, color in fits:
            if res is not None:
                fill[res.imin:res.imax + 1] = color
        fill[(steps[inc_col] < 0).values] = "white"
        self.src.data = dict(x=x, y=y, fill=fill, label=steps["label"], seq=steps["sequence"])
        dx, dy, dcol, names, gxs, gys, gcol = [], [], [], [], [], [], []
        for comp, res, color in fits:
            if res is None:
                continue
            fx, fy = dc.equal_area_xy([res.dir_dec], [res.dir_inc])
            dx.append(fx[0]); dy.append(fy[0]); dcol.append(color); names.append(comp.name)
            if res.direction_type == "p":
                gx, gy = dc.great_circle_xy(res.dir_dec, res.dir_inc)
                gxs.append(list(gx)); gys.append(list(gy)); gcol.append(color)
        self.dirs.data = dict(x=dx, y=dy, color=dcol, name=names)
        self.circles.data = dict(xs=gxs, ys=gys, color=gcol)


class DecayPlot:
    """M/M0 against treatment; open circles mark the bounds of every fit.

    A short, wide rectangle under the net: ``frame_height`` fixes the plot frame
    so that its bottom can be aligned with the Zijderveld frame (``TOP``
    pixels of border above it), and the axis text matches the information line.
    """

    TOP = 8
    AXIS_ROWS = 58          # x-axis ticks + label + bottom border, measured in the browser

    def __init__(self, size=340, height=None, frame_height=None):
        if frame_height is None:
            frame_height = (height or size) - self.TOP - self.AXIS_ROWS
        self.fig = figure(height=height or (frame_height + self.TOP + self.AXIS_ROWS), width=size,
                          frame_height=frame_height, min_border_top=self.TOP, min_border_bottom=4,
                          tools="pan,wheel_zoom,reset,save", frame_align=False,
                          sizing_mode="fixed", x_axis_label="treatment", y_axis_label="M / M₀")
        style_figure(self.fig)
        # the same size as the Zijderveld axis-end labels (the template's theme
        # would otherwise render axis text at 1.25 em)
        self.fig.axis.axis_label_text_font_size = "11pt"
        self.fig.axis.major_label_text_font_size = "10pt"
        self.fig.min_border_right = 1          # the frame reaches the right edge, flush with the net's box
        self.src = ColumnDataSource(dict(x=[], y=[], label=[], color=[]))
        self.fig.line("x", "y", source=self.src, color="#6b7280", line_width=1)
        pts = self.fig.scatter("x", "y", source=self.src, size=7, fill_color="color", line_color="#2b2b2b",
                               line_width=0.5)
        self.fig.add_tools(HoverTool(renderers=[pts], tooltips=[("step", "@label"), ("M/M₀", "@y{0.000}")]))
        self.bounds = ColumnDataSource(dict(x=[], y=[], color=[]))
        self.fig.scatter("x", "y", source=self.bounds, size=17, fill_alpha=0.0, line_color="color", line_width=2)

    def update(self, spec, fits):
        steps = spec.steps
        color = np.array(["#2b2b2b"] * len(steps), dtype=object)
        bx, by, bcol = [], [], []
        for comp, res, col in fits:
            if res is None:
                continue
            color[res.imin:res.imax + 1] = col
            for i in (res.imin, res.imax):
                bx.append(steps["treat_display"][i]); by.append(steps["moment_norm"][i]); bcol.append(col)
        self.src.data = dict(x=steps["treat_display"], y=steps["moment_norm"], label=steps["label"], color=color)
        self.bounds.data = dict(x=bx, y=by, color=bcol)
        self.fig.xaxis.axis_label = {"T": "AF field (mT)", "K": "temperature (°C)"}.get(spec.unit,
                                                                                         f"treatment ({spec.unit})")


class DirectionsPlot:
    """Equal-area plot of many directions (specimen fits or site means) with a Fisher mean."""

    def __init__(self, title="Directions", size=460):
        self.fig = net_figure(None, size)
        self.fig.title.text = title
        self.fig.height = size + 28          # room for the title row above the square frame
        self.src = ColumnDataSource(dict(x=[], y=[], fill=[], line=[], label=[], comp=[]))
        pts = self.fig.scatter("x", "y", source=self.src, size=8, fill_color="fill", line_color="line",
                               line_width=0.8)
        self.fig.add_tools(HoverTool(renderers=[pts], tooltips=[("", "@label"), ("component", "@comp")]))
        self.circles = ColumnDataSource(dict(xs=[], ys=[], color=[]))
        self.fig.multi_line("xs", "ys", source=self.circles, color="color", line_width=1, alpha=0.8)
        # one star + α95 circle per component mean, in the component's colour
        self.mean = ColumnDataSource(dict(x=[], y=[], color=[], name=[]))
        self.a95 = ColumnDataSource(dict(xs=[], ys=[], color=[]))
        self.fig.multi_line("xs", "ys", source=self.a95, color="color", line_width=2)
        stars = self.fig.scatter("x", "y", source=self.mean, marker="star", size=22, fill_color="color",
                                 line_color="#2b2b2b", line_width=0.8)
        self.fig.add_tools(HoverTool(renderers=[stars], tooltips=[("mean", "@name")]))

    def update(self, directions, planes=(), means=(), title=None):
        """directions: iterable of (dec, inc, label, comp_name, colour); means: iterable of (mean dict, colour)."""
        dirs = list(directions)
        if dirs:
            dec = np.array([d[0] for d in dirs], float)
            inc = np.array([d[1] for d in dirs], float)
            x, y = dc.equal_area_xy(dec, inc)
            fill = [d[4] if i >= 0 else "white" for d, i in zip(dirs, inc)]
            self.src.data = dict(x=x, y=y, fill=fill, line=[d[4] for d in dirs], label=[d[2] for d in dirs],
                                 comp=[d[3] for d in dirs])
        else:
            self.src.data = dict(x=[], y=[], fill=[], line=[], label=[], comp=[])
        gxs, gys, gcol = [], [], []
        for pdec, pinc, color in planes:
            gx, gy = dc.great_circle_xy(pdec, pinc)
            gxs.append(list(gx)); gys.append(list(gy)); gcol.append(color)
        self.circles.data = dict(xs=gxs, ys=gys, color=gcol)
        mx, my, mcol, mname, axs, ays, acol = [], [], [], [], [], [], []
        for mean, color in means:
            if mean is None or np.isnan(mean.get("dir_dec", np.nan)):
                continue
            x, y = dc.equal_area_xy([mean["dir_dec"]], [mean["dir_inc"]])
            mx.append(float(x[0])); my.append(float(y[0])); mcol.append(color)
            mname.append(str(mean.get("dir_comp_name", "")))
            a95 = mean.get("dir_alpha95", np.nan)
            if a95 is not None and not np.isnan(a95) and a95 > 0:
                cd, ci = dc.pmag.circ(mean["dir_dec"], mean["dir_inc"], a95)
                cx, cy = dc.equal_area_xy(cd, np.abs(ci))
                axs.append(list(cx)); ays.append(list(cy)); acol.append(color)
        self.mean.data = dict(x=mx, y=my, color=mcol, name=mname)
        self.a95.data = dict(xs=axs, ys=ays, color=acol)
        if title:
            self.fig.title.text = title


class PoleMapPlot:
    """VGPs and the mean pole on an orthographic globe (Natural Earth land, graticule).

    The globe can be re-centred programmatically (``update(..., centre=)``) or
    by clicking it: the clicked point becomes the centre and the new centre is
    reported through ``on_recentre``.
    """

    RADIUS = 1.08

    def __init__(self, size=460, legend_height=30):
        r = self.RADIUS
        self.fig = figure(width=size, height=size + legend_height, x_range=(-r, r), y_range=(-r, r),
                          tools="reset,save", sizing_mode="fixed", min_border=4,
                          toolbar_location=None, frame_align=False, name="pole_map")
        style_figure(self.fig, hide_axes=True)
        keep_circular(self.fig)
        cx, cy = geo.circle_outline()
        self.fig.patch(cx, cy, fill_color=OCEAN_COLOR, line_color=None)
        self.land = ColumnDataSource(dict(xs=[], ys=[]))
        self.holes = ColumnDataSource(dict(xs=[], ys=[]))
        self.fig.patches("xs", "ys", source=self.land, fill_color=LAND_COLOR, line_color=LAND_EDGE, line_width=0.6)
        self.fig.patches("xs", "ys", source=self.holes, fill_color=OCEAN_COLOR, line_color=LAND_EDGE, line_width=0.6)
        self.grat = ColumnDataSource(dict(xs=[], ys=[]))
        self.fig.multi_line("xs", "ys", source=self.grat, color="#9aa3ad", line_width=0.6, line_dash="dotted")
        self.fig.line(cx, cy, color="#2b2b2b", line_width=1.2)
        self.sites = ColumnDataSource(dict(x=[], y=[], label=[]))
        site_r = self.fig.scatter("x", "y", source=self.sites, marker="star", size=16, fill_color=SITE_COLOR,
                                  line_color="#1b3d1b", line_width=0.6)
        self.src = ColumnDataSource(dict(x=[], y=[], fill=[], line=[], label=[], note=[]))
        pts = self.fig.scatter("x", "y", source=self.src, size=8, fill_color="fill", line_color="line", line_width=1)
        self.a95 = ColumnDataSource(dict(xs=[], ys=[]))
        self.fig.multi_line("xs", "ys", source=self.a95, color=MEAN_COLOR, line_width=2)
        self.mean = ColumnDataSource(dict(x=[], y=[]))
        mean_r = self.fig.scatter("x", "y", source=self.mean, marker="hex", size=22, fill_color=MEAN_COLOR,
                                  fill_alpha=0.85, line_color="#2b2b2b", line_width=0.8)
        self.fig.add_tools(HoverTool(renderers=[pts], tooltips=[("", "@label"), ("", "@note")]))
        self.fig.add_tools(HoverTool(renderers=[site_r], tooltips=[("sites", "@label")]))
        self.fig.add_tools(HoverTool(renderers=[mean_r], tooltips=[("", "mean pole")]))
        legend = Legend(items=[LegendItem(label="VGP (open: antipode taken)", renderers=[pts]),
                               LegendItem(label="mean pole + A95", renderers=[mean_r]),
                               LegendItem(label="sampling sites", renderers=[site_r])],
                        orientation="horizontal", location="center", border_line_color=None,
                        background_fill_alpha=0, padding=0, spacing=18, label_text_font_size="9pt",
                        label_text_color="#374151", glyph_height=14, glyph_width=14)
        self.fig.add_layout(legend, "below")
        self.centre = (0.0, 90.0)
        self._recentre_callbacks = []
        self._last = None
        self.fig.on_event(Tap, self._on_tap)

    def on_recentre(self, callback):
        """callback(lon0, lat0) after the globe was clicked."""
        self._recentre_callbacks.append(callback)

    def _on_tap(self, event):
        """The clicked point of the globe becomes the new centre."""
        x, y = getattr(event, "x", None), getattr(event, "y", None)
        if x is None or y is None or x * x + y * y > 1.0:
            return                                        # off the globe
        view, east, north = geo.view_basis(*self.centre)
        depth = np.sqrt(max(0.0, 1.0 - x * x - y * y))
        lon, lat = geo.lon_lat(x * east + y * north + depth * view)
        self.centre = (float(lon[0]), float(lat[0]))
        self._draw_globe()
        for cb in self._recentre_callbacks:
            cb(*self.centre)

    def _draw_globe(self):
        lon0, lat0 = self.centre
        outers, holes = geo.land_patches(lon0, lat0)
        self.land.data = dict(xs=[list(x) for x, y in outers], ys=[list(y) for x, y in outers])
        self.holes.data = dict(xs=[list(x) for x, y in holes], ys=[list(y) for x, y in holes])
        grat = geo.graticule(lon0, lat0)
        self.grat.data = dict(xs=[list(x) for x, y in grat], ys=[list(y) for x, y in grat])
        if self._last is not None:
            self._draw_data(*self._last)

    def update(self, vgps, pole=None, sites=(), centre=None, color="#2b2b2b"):
        """vgps: iterable of (lon, lat, label, flipped); sites: iterable of (lon, lat, name)."""
        if centre is not None:
            self.centre = (float(centre[0]), float(centre[1]))
        self._last = (list(vgps), pole, list(sites), color)
        self._draw_globe()

    def _draw_data(self, vg, pole, sites, color):
        lon0, lat0 = self.centre
        if vg:
            lon = np.array([v[0] for v in vg], float)
            lat = np.array([v[1] for v in vg], float)
            x, y, vis = geo.orthographic_xy(lon, lat, lon0, lat0)
            flipped = np.array([bool(v[3]) if len(v) > 3 else False for v in vg])
            self.hidden = int((~vis).sum())
            self.src.data = dict(x=x[vis], y=y[vis], fill=["white" if f else color for f in flipped[vis]],
                                 line=[color] * int(vis.sum()), label=[v[2] for v, ok in zip(vg, vis) if ok],
                                 note=["antipode taken" if f else "" for f in flipped[vis]])
        else:
            self.hidden = 0
            self.src.data = dict(x=[], y=[], fill=[], line=[], label=[], note=[])
        if sites:
            x, y, vis = geo.orthographic_xy([s[0] for s in sites], [s[1] for s in sites], lon0, lat0)
            self.sites.data = dict(x=x[vis], y=y[vis], label=[s[2] for s, ok in zip(sites, vis) if ok])
        else:
            self.sites.data = dict(x=[], y=[], label=[])
        if pole:
            x, y, vis = geo.orthographic_xy([pole["plon"]], [pole["plat"]], lon0, lat0)
            self.mean.data = dict(x=x[vis], y=y[vis])
            circle = geo.small_circle(pole["plon"], pole["plat"], pole["A95"])
            runs = geo.project_lines([circle], lon0, lat0)
            self.a95.data = dict(xs=[list(x) for x, y in runs], ys=[list(y) for x, y in runs])
        else:
            self.mean.data = dict(x=[], y=[])
            self.a95.data = dict(xs=[], ys=[])
