"""
Publication-quality figures (matplotlib) in the style of Fairchild et al.
(2017, Lithosphere, Fig. 4): a Zijderveld diagram with grey filled circles
(horizontal projection) and squares (vertical projection), thick coloured
best-fit lines with an arrowhead pointing away from the origin (the
component's direction), step labels, axis-end
labels (N,Up / S,Down / E / W), a "divisions are 10⁻ⁿ Am²" note, and inset
equal-area and M/NRM panels whose points are coloured by component.

All functions return a ``matplotlib.figure.Figure``; ``save_figure`` writes
PNG/PDF/SVG. Nothing here imports Panel or Bokeh, so the same code serves
batch export from scripts and notebooks.
"""
from __future__ import annotations

import logging
import math
import os
from typing import Iterable, Optional

import matplotlib

logging.getLogger("fontTools").setLevel(logging.ERROR)   # quiet font-subsetting chatter on PDF export
import numpy as np
from matplotlib.figure import Figure
from matplotlib.legend_handler import HandlerPatch
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

import pmagpy.demag as dc
import pmagpy.demag_geo as geo

from .theme import (COMPONENT_PALETTE, LAND_COLOR, LAND_EDGE, MEAN_COLOR, NET_COLOR, OCEAN_COLOR, POINT_EDGE,
                    POINT_FILL, SITE_COLOR)

matplotlib.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
    "font.size": 9,
    "axes.linewidth": 0.8,
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
    "svg.fonttype": "none",
})

FitTriple = tuple  # (Component, DirectionResult | None, color)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _nice_division(nrm: float) -> float:
    """Tick spacing: the power of ten at or below half of the NRM moment."""
    if not nrm or not np.isfinite(nrm) or nrm <= 0:
        return 0.2
    return 10.0 ** math.floor(math.log10(nrm / 2.0))


def _superscript(exp: int) -> str:
    table = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")
    return str(exp).translate(table)


def _draw_net(ax, ticks=True, labels=("N", "E", "S", "W")):
    theta = np.linspace(0, 2 * np.pi, 361)
    ax.plot(np.cos(theta), np.sin(theta), color=NET_COLOR, lw=0.8)
    if ticks:
        for d in (0, 90, 180, 270):
            xy = np.array([dc.pmag.dimap(d, i) for i in range(10, 90, 10)])
            ax.plot(xy[:, 0], xy[:, 1], "+", color=NET_COLOR, ms=4, mew=0.6)
        ax.plot([0], [0], "+", color=NET_COLOR, ms=4, mew=0.6)
    if labels:
        for txt, (x, y), ha, va in zip(labels, [(0, 1.02), (1.02, 0), (0, -1.02), (-1.02, 0)],
                                       ["center", "left", "center", "right"], ["bottom", "center", "top", "center"]):
            if txt:
                ax.text(x, y, txt, ha=ha, va=va, fontsize=8, color=NET_COLOR)
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(-1.12, 1.12)
    ax.set_aspect("equal")
    ax.axis("off")


def _equal_area_points(ax, dec, inc, colors, size=18, zorder=3):
    dec, inc = np.asarray(dec, float), np.asarray(inc, float)
    if len(dec) == 0:
        return
    x, y = dc.equal_area_xy(dec, inc)
    lower = inc >= 0
    colors = np.asarray(colors, dtype=object)
    ax.scatter(x[lower], y[lower], s=size, c=list(colors[lower]), edgecolors=POINT_EDGE, linewidths=0.5, zorder=zorder)
    ax.scatter(x[~lower], y[~lower], s=size, facecolors="white", edgecolors=list(colors[~lower]), linewidths=0.9,
               zorder=zorder)


# ---------------------------------------------------------------------------
# specimen figure
# ---------------------------------------------------------------------------
class _ArrowHandler(HandlerPatch):
    """Legend entry for the least-squares fits: a short arrow."""

    def create_artists(self, legend, orig_handle, xdescent, ydescent, width, height, fontsize, trans):
        y = ydescent + height / 2
        band = Line2D([xdescent, xdescent + width], [y, y], color=orig_handle.get_edgecolor(), lw=5, alpha=0.3,
                      solid_capstyle="butt", transform=trans)
        arrow = FancyArrowPatch((xdescent, y), (xdescent + width, y), arrowstyle="-|>", mutation_scale=9,
                                color=orig_handle.get_edgecolor(), lw=1.6, transform=trans)
        return [band, arrow]


def _sci(value: float) -> str:
    """1.45e-07 -> '1.45×10⁻⁷'."""
    if not np.isfinite(value) or value == 0:
        return "–"
    mant, exp = f"{value:.2e}".split("e")
    return f"{float(mant):.2f}×10{_superscript(int(exp))}"


def _fit_short(fit_type: str) -> str:
    return {"DE-BFL": "line", "DE-BFL-A": "anchored line", "DE-BFL-O": "line through origin",
            "DE-BFP": "plane", "DE-FM": "Fisher mean"}.get(fit_type, fit_type)


def specimen_figure(spec: dc.SpecimenData, fits: Iterable[FitTriple], coord: int = dc.COORD_GEOGRAPHIC,
                    projection: str = "ew", label_every: int = 1, title: Optional[str] = None,
                    layout: str = "panel", figsize=None) -> Figure:
    """Zijderveld diagram with equal-area and M/NRM panels for one specimen.

    Styled after Slotznick et al. (2023) and Fairchild et al. (2017): open
    circles (horizontal projection) and squares (vertical projection) joined
    by thin lines, least-squares fits as translucent bands with an arrowhead
    pointing away from the origin and the component name beside them, step
    labels, axis-end labels, a "divisions are 10⁻ⁿ Am²" note, an equal-area
    panel with the fitted directions and an M/NRM curve with a bracket over
    the steps of every fit.

    Args:
        spec: the specimen (``DemagData.specimens[name]``).
        fits: iterable of (Component, DirectionResult or None, colour).
        coord: MagIC ``dir_tilt_correction`` code of the coordinate system.
        projection: 'ew' (x = East), 'ns', 'nrm' or 'fit'.
        label_every: label every n-th step (0 = no labels; 1 = all, thinned
            where symbols pile up).
        title: figure title (default: "specimen <name>").
        layout: 'panel' places the equal-area and M/NRM plots in a column to
            the right of the Zijderveld diagram (never overlaps anything);
            'inset' places them inside the diagram's emptiest quadrants;
            'zijderveld' draws only the diagram.
    """
    fits = [f for f in fits]
    insets = layout == "inset"
    if figsize is None:
        figsize = (10.0, 6.2) if layout == "panel" else (6.5, 6.5)
    steps = spec.steps
    if not spec.has_coord(coord):
        coord = dc.COORD_SPECIMEN
    dec_col, inc_col = dc.COORD_COLUMNS[coord]
    fit_dec = None
    for comp, res, _ in fits:
        if res is not None and res.direction_type == "l":
            fit_dec = res.dir_dec
            break
    rotation = dc.projection_rotation(spec, coord, projection, fit_dec)
    labels = dc.axis_labels(coord, projection, rotation)
    z = dc.zijderveld_xy(steps, coord, rotation_dec=rotation)
    good = (z["quality"] == "g").values

    fig = Figure(figsize=figsize)
    rect = [0.03, 0.05, 0.58, 0.86] if layout == "panel" else [0.06, 0.06, 0.88, 0.86]
    ax = fig.add_axes(rect)
    ax.set_aspect("equal")
    ax.axis("off")

    # data: thin lines through the good points, open symbols; excluded steps as crosses
    ax.plot(z["x"][good], z["y_h"][good], "-", color="#4a4a4a", lw=0.8, zorder=1)
    ax.plot(z["x"][good], z["y_v"][good], "-", color="#4a4a4a", lw=0.8, zorder=1)
    ax.scatter(z["x"][good], z["y_h"][good], marker="o", s=32, facecolors="white", edgecolors="#111111",
               linewidths=0.8, zorder=3, label="horizontal projection")
    ax.scatter(z["x"][good], z["y_v"][good], marker="s", s=30, facecolors="white", edgecolors="#111111",
               linewidths=0.8, zorder=3, label="vertical projection")
    if (~good).any():
        ax.scatter(z["x"][~good], z["y_h"][~good], marker="x", s=28, c="#9a9a9a", linewidths=0.9, zorder=3,
                   label="excluded step")
        ax.scatter(z["x"][~good], z["y_v"][~good], marker="x", s=28, c="#9a9a9a", linewidths=0.9, zorder=3)

    # least-squares fits: translucent band + arrow pointing away from the origin
    name_anchor = {}
    for comp, res, color in fits:
        if res is None:
            continue
        seg = dc.fit_line_segment(res, spec, coord, rotation_dec=rotation)
        if seg is None:
            continue
        longest = None
        for ycol in ("y_h", "y_v"):
            p0 = np.array([seg["x"][0], seg[ycol][0]])
            p1 = np.array([seg["x"][1], seg[ycol][1]])
            # the arrow shows the component's direction: the vector removed between the
            # bounds, which points *away* from the origin (a common student misconception
            # is that the fitted line points in toward the origin)
            if np.hypot(*p0) > np.hypot(*p1):
                p0, p1 = p1, p0
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=7, alpha=0.30, solid_capstyle="butt", zorder=2)
            ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=13, color=color, lw=1.8,
                                         zorder=2.5, shrinkA=0, shrinkB=0))
            length = float(np.hypot(*(p1 - p0)))
            if longest is None or length > longest[0]:
                longest = (length, p0, p1)
        if longest is not None:
            _, p0, p1 = longest
            d = p1 - p0
            normal = np.array([-d[1], d[0]])
            normal = normal / (np.linalg.norm(normal) or 1.0)
            name_anchor[comp.name] = ((p0 + p1) / 2, normal, color)

    # axes through the origin with tick divisions in absolute moment units
    xs = np.concatenate([z["x"].values, [0.0]])
    ys = np.concatenate([z["y_h"].values, z["y_v"].values, [0.0]])
    pad = 0.08 * max(np.ptp(xs), np.ptp(ys), 1e-9)
    xmin, xmax = xs.min() - pad, xs.max() + pad
    ymin, ymax = ys.min() - pad, ys.max() + pad
    extent = max(xmax - xmin, ymax - ymin)

    for name, (mid, normal, color) in name_anchor.items():
        # put the label on the side of the line that faces away from the origin
        if np.dot(normal, mid) < 0:
            normal = -normal
        pos = mid + normal * 0.07 * extent
        ax.annotate(name, pos, ha="center", va="center", fontsize=9, fontweight="bold", color=color, zorder=6,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

    # step labels next to the vertical-projection symbols, thinned where the
    # symbols pile up (the first and last steps are always labelled); labels
    # crowding the origin are dropped so the axis labels stay legible
    if label_every:
        placed = []
        n = len(z)
        for i, (x, y, lab) in enumerate(zip(z["x"], z["y_v"], z["label"])):
            if i % label_every and i not in (0, n - 1):
                continue
            if i not in (0, n - 1):
                if placed and min(np.hypot(x - px, y - py) for px, py in placed) < 0.035 * extent:
                    continue
                if np.hypot(x, y) < 0.05 * extent:
                    continue
            placed.append((x, y))
            ax.annotate(lab, (x, y), xytext=(4, -3), textcoords="offset points", fontsize=7, color="#333")
    ax.plot([xmin, xmax], [0, 0], color=NET_COLOR, lw=0.9, zorder=0)
    ax.plot([0, 0], [ymin, ymax], color=NET_COLOR, lw=0.9, zorder=0)
    division = _nice_division(spec.nrm)
    step = division / spec.nrm if spec.nrm else 0.2
    tick_len = 0.012 * max(xmax - xmin, ymax - ymin)
    for t in np.arange(step, xmax, step):
        ax.plot([t, t], [-tick_len, tick_len], color=NET_COLOR, lw=0.7)
    for t in np.arange(-step, xmin, -step):
        ax.plot([t, t], [-tick_len, tick_len], color=NET_COLOR, lw=0.7)
    for t in np.arange(step, ymax, step):
        ax.plot([-tick_len, tick_len], [t, t], color=NET_COLOR, lw=0.7)
    for t in np.arange(-step, ymin, -step):
        ax.plot([-tick_len, tick_len], [t, t], color=NET_COLOR, lw=0.7)
    exp = int(math.floor(math.log10(division)))
    mant = division / 10 ** exp
    div_txt = ("divisions are %s10%s Am²" % (("%g×" % mant) if mant != 1 else "", _superscript(exp)))
    ax.set_xlim(xmin - pad, xmax + pad)
    ax.set_ylim(ymin - 2 * pad, ymax + pad)
    # titles are anchored to the figure, not to the axes: with an equal aspect a
    # tall diagram shrinks its axes box and axes titles would collide
    top = rect[1] + rect[3] + 0.015
    fig.text(rect[0], top, title or f"specimen {spec.name}", ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(rect[0] + rect[2], top, f"NRM = {_sci(spec.nrm)} Am²\n{dc.COORD_NAMES[coord]} coordinates\n{div_txt}",
             ha="right", va="top", fontsize=8.5, style="italic", color="#333")

    # quadrant occupancy (data points and fit arrows) decides where the
    # insets and the legend go
    pts_x = [z["x"].values, z["x"].values]
    pts_y = [z["y_h"].values, z["y_v"].values]
    for comp, res, color in fits:
        seg = dc.fit_line_segment(res, spec, coord, rotation_dec=rotation) if res is not None else None
        if seg is not None:
            for ycol in ("y_h", "y_v"):
                pts_x.append(np.linspace(seg["x"][0], seg["x"][1], 12))
                pts_y.append(np.linspace(seg[ycol][0], seg[ycol][1], 12))
    xf = (np.concatenate(pts_x) - xmin) / (xmax - xmin)
    yf = (np.concatenate(pts_y) - ymin) / (ymax - ymin)
    counts = {"TL": ((xf < .5) & (yf > .5)).sum(), "TR": ((xf >= .5) & (yf > .5)).sum(),
              "BL": ((xf < .5) & (yf <= .5)).sum(), "BR": ((xf >= .5) & (yf <= .5)).sum()}
    order = sorted(counts, key=lambda q: (counts[q], q))
    # with an equal aspect the axes box is resized at draw time: settle it now
    # so that figure-level placements below use the real box
    ax.apply_aspect()
    box = ax.get_position()
    w, h = box.width, box.height

    def quadrant_box(q, fw=0.33, fh=0.33, margin=0.08):
        # keep clear of the axis-end labels, which sit at the top/bottom/sides of the box
        x = box.x0 + (0.02 if "L" in q else 0.98 - fw) * w
        y = box.y0 + (margin if "B" in q else 1.0 - margin - fh) * h
        return [x, y, fw * w, fh * h]
    handles, texts = ax.get_legend_handles_labels()
    if name_anchor:
        handles.append(FancyArrowPatch((0, 0), (1, 0), color="#555555"))
        texts.append("least-squares fits")
    legend_kw = dict(frameon=True, fontsize=8, handletextpad=0.5, borderpad=0.5, title="vector component symbols",
                     title_fontsize=8, handler_map={FancyArrowPatch: _ArrowHandler()}, edgecolor="#c8ccd2")
    if layout == "panel":
        # a strip under the diagram: it can never cover data or axis labels
        fig.legend(handles, texts, loc="lower left", bbox_to_anchor=(0.03, 0.0), ncol=len(texts), **legend_kw)
    else:
        legend_loc = {"TL": "upper left", "TR": "upper right", "BL": "lower left", "BR": "lower right"}
        anchor = {"TL": (0.02, 0.92), "TR": (0.98, 0.92), "BL": (0.02, 0.08), "BR": (0.98, 0.08)}
        q = order[2]
        ax.legend(handles, texts, loc=legend_loc[q], bbox_to_anchor=anchor[q], **legend_kw)

    # axis-end labels and the divisions note are figure-level text with a white
    # backing so that they stay legible even where an inset overlaps an axis
    def fig_label(x, y, text, ha, va, **kw):
        fx, fy = fig.transFigure.inverted().transform(ax.transData.transform((x, y)))
        fig.text(fx, fy, text, ha=ha, va=va, fontsize=kw.pop("fontsize", 9), zorder=20,
                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.9), **kw)
    fig_label(xmax, 0, " " + labels["right"], "left", "center")
    if labels["left"]:
        fig_label(xmin, 0, labels["left"] + " ", "right", "center")
    top = ", ".join(t for t in (labels["top_h"], labels["top_v"]) if t)
    bottom = ", ".join(t for t in (labels["bottom_h"], labels["bottom_v"]) if t)
    fig_label(0, ymax, top, "center", "bottom")
    fig_label(0, ymin, bottom, "center", "top")

    if layout == "zijderveld":
        return fig
    if layout == "panel":
        eq_pos = [0.63, 0.50, 0.35, 0.44]
        dec_pos = [0.70, 0.09, 0.27, 0.30]
    else:
        eq_pos = quadrant_box(order[0])
        dec_box = quadrant_box(order[1], fw=0.30, fh=0.30, margin=0.14)
        dec_pos = [dec_box[0] + 0.14 * dec_box[2], dec_box[1] + 0.20 * dec_box[3], 0.82 * dec_box[2],
                   0.70 * dec_box[3]]

    # equal-area panel: steps in grey, fitted directions in the component colour
    ax_eq = fig.add_axes(eq_pos)
    _draw_net(ax_eq)
    x, y = dc.equal_area_xy(steps[dec_col], steps[inc_col])
    ax_eq.plot(x, y, "-", color="#b0b0b0", lw=0.6, zorder=1)
    _equal_area_points(ax_eq, steps[dec_col], steps[inc_col], [POINT_FILL] * len(steps), size=9)
    fit_handles, fit_texts = [], []
    step_labels = list(steps["label"])
    for comp, res, color in fits:
        if res is None:
            continue
        if res.direction_type == "p":
            gx, gy = dc.great_circle_xy(res.dir_dec, res.dir_inc)
            ax_eq.plot(gx, gy, color=color, lw=1.4)
        _equal_area_points(ax_eq, [res.dir_dec], [res.dir_inc], [color], size=55, zorder=6)
        fit_handles.append(Line2D([], [], marker="o", ls="", markerfacecolor=color if res.dir_inc >= 0 else "white",
                                  markeredgecolor=color if res.dir_inc < 0 else POINT_EDGE, markersize=7))
        fit_texts.append(f"{comp.name}: {step_labels[res.imin]}–{step_labels[res.imax]} ({_fit_short(comp.fit_type)})")
    if layout == "panel":            # in the inset layout the right-hand title already names the coordinates
        ax_eq.text(1.08, -1.08, dc.COORD_NAMES[coord], ha="right", va="bottom", fontsize=8, color="#333")
    if fit_texts:
        if layout == "panel":
            fig.legend(fit_handles, fit_texts, loc="center", bbox_to_anchor=(0.815, 0.455), frameon=False,
                       fontsize=8, ncol=1 if len(fit_texts) <= 2 else 2, handletextpad=0.3, columnspacing=1.0)
        else:
            ax_eq.legend(fit_handles, fit_texts, loc="upper center", bbox_to_anchor=(0.5, -0.04), frameon=False,
                         fontsize=7, handletextpad=0.3)

    # M/NRM decay with a bracket over the steps of every fit
    ax_dec = fig.add_axes(dec_pos)
    xt = steps["treat_display"].values.astype(float)
    mn = steps["moment_norm"].values.astype(float)
    ax_dec.plot(xt, mn, "-", color="#4a4a4a", lw=0.8, zorder=1)
    ax_dec.scatter(xt, mn, s=16, facecolors="white", edgecolors="#111111", linewidths=0.7, zorder=3)
    if (~good).any():
        ax_dec.scatter(xt[~good], mn[~good], marker="x", s=18, c="#9a9a9a", linewidths=0.8, zorder=4)
    brackets = []
    span = max(np.ptp(xt), 1e-9)
    for comp, res, color in fits:
        if res is None:
            continue
        x0, x1 = xt[res.imin], xt[res.imax]
        yb = float(np.nanmax(mn[res.imin:res.imax + 1])) + 0.10
        for bx0, bx1, by in brackets:                       # stack brackets that overlap in x
            if x0 <= bx1 + 0.02 * span and x1 >= bx0 - 0.02 * span and abs(by - yb) < 0.12:
                yb = by + 0.14
        yb = min(yb, 1.22)
        brackets.append((x0, x1, yb))
        ax_dec.plot([x0, x0, x1, x1], [yb - 0.035, yb, yb, yb - 0.035], color=color, lw=1.4, zorder=5)
        ax_dec.text((x0 + x1) / 2, yb + 0.015, comp.name, ha="center", va="bottom", fontsize=8, color=color,
                    fontweight="bold", zorder=6)
    ax_dec.set_ylim(0, 1.36)
    ax_dec.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax_dec.set_ylabel("M / NRM", fontsize=8)
    unit = spec.unit
    ax_dec.set_xlabel({"T": "AF field (mT)", "K": "temperature (°C)"}.get(unit, "treatment"), fontsize=8)
    ax_dec.tick_params(labelsize=7, length=2)
    for side in ("top", "right"):
        ax_dec.spines[side].set_visible(False)
    return fig


# ---------------------------------------------------------------------------
# equal-area figures for sample / site / location levels
# ---------------------------------------------------------------------------
_CORNERS = {"TR": (1.06, 1.04, "right", "top"), "TL": (-1.06, 1.04, "left", "top"),
            "BR": (1.06, -1.04, "right", "bottom"), "BL": (-1.06, -1.04, "left", "bottom")}


def _empty_corners(x, y):
    """Corner keys ordered from emptiest to fullest (points beyond 0.5 radius count)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    counts = {"TR": ((x > 0.25) & (y > 0.25)).sum(), "TL": ((x < -0.25) & (y > 0.25)).sum(),
              "BR": ((x > 0.25) & (y < -0.25)).sum(), "BL": ((x < -0.25) & (y < -0.25)).sum()}
    return sorted(counts, key=lambda k: (counts[k], ["TR", "BR", "TL", "BL"].index(k)))


def directions_figure(directions, mean: Optional[dict] = None, title: str = "", planes=(),
                      caption: str = "", figsize=(4.4, 4.4), legend: bool = True, ax=None,
                      mean_color: str = MEAN_COLOR, means=None,
                      mean_label: str = "Fisher mean") -> Figure:
    """Equal-area plot of directions with an optional Fisher mean and α95.

    In the style of Slotznick et al. (2023): lower-hemisphere directions are
    filled, upper-hemisphere ones open, the title (e.g. the component name)
    and a caption (e.g. "tilt corrected") sit inside the net in its emptiest
    corner and the Fisher statistics in the next emptiest.

    Args:
        directions: iterable of (dec, inc, label, color).
        mean: dict with dir_dec, dir_inc, dir_alpha95 (and optionally dir_k,
            dir_n_specimens ...) as returned by ``DemagData.mean_directions``.
        planes: iterable of (pole_dec, pole_inc, color) great circles.
        caption: text under the title (coordinate system, level ...).
        legend: draw the Fisher statistics block.
        ax: draw into an existing axes (used by ``components_overview_figure``).
        means: iterable of (mean dict, colour) — one star and α95 per component
            (used when every component is shown at once); ``mean`` is then ignored.
        mean_label: heading of the statistics block, for figures whose mean is
            not a Fisher mean of the whole set (by polarity, or Bingham).
    """
    if ax is None:
        fig = Figure(figsize=figsize)
        ax = fig.add_axes([0.03, 0.03, 0.94, 0.94])
    else:
        fig = ax.figure
    _draw_net(ax)
    dirs = list(directions)
    px, py = np.array([]), np.array([])
    if dirs:
        dec = [d[0] for d in dirs]
        inc = [d[1] for d in dirs]
        cols = [d[3] for d in dirs]
        _equal_area_points(ax, dec, inc, cols, size=22)
        px, py = dc.equal_area_xy(dec, inc)
    for pdec, pinc, color in planes:
        gx, gy = dc.great_circle_xy(pdec, pinc)
        ax.plot(gx, gy, color=color, lw=0.9, alpha=0.8)
    corners = _empty_corners(px, py)
    stats_lines, stats_colors = [], []
    if means is None:
        means = [(mean, mean_color)] if mean else []
    for m, color in means:
        if not m or np.isnan(m.get("dir_dec", np.nan)):
            continue
        mx, my = dc.equal_area_xy([m["dir_dec"]], [m["dir_inc"]])
        ax.scatter(mx, my, marker="s", s=95, c=color, edgecolors=POINT_EDGE, linewidths=0.6, zorder=6)
        a95 = m.get("dir_alpha95", np.nan)
        if a95 and not np.isnan(a95) and a95 > 0:
            cd, ci = dc.pmag.circ(m["dir_dec"], m["dir_inc"], a95)
            cx, cy = dc.equal_area_xy(cd, np.abs(ci))
            ax.plot(cx, cy, color=color, lw=1.3, zorder=5)
        n = m.get("dir_n_specimens", m.get("dir_n_sites", m.get("dir_n_samples", "")))
        k = m.get("dir_k", np.nan)
        parts = [f"dec = {m['dir_dec']:.1f}°", f"inc = {m['dir_inc']:.1f}°"]
        if a95 and not np.isnan(a95):
            parts.append(f"α$_{{95}}$ = {a95:.1f}°")
        if k is not None and not np.isnan(k):
            parts.append(f"k = {k:.1f}")
        if n != "":
            parts.append(f"n = {n}")
        if len(means) > 1:            # several components: one compact line each, in the component's colour
            stats_lines.append(f"{m.get('dir_comp_name', '')}: " + ", ".join(parts))
            stats_colors.append(color)
        else:
            stats_lines = parts
            stats_colors = ["#222"] * len(parts)
    if title:
        x, y, ha, va = _CORNERS[corners[0]]
        text = ax.text(x, y, title, ha=ha, va=va, fontsize=11, fontweight="bold", zorder=8)
        if caption:
            dy = -0.17 if va == "top" else 0.17
            ax.text(x, y + dy + (0.0 if va == "top" else 0.0), caption, ha=ha, va=va, fontsize=8.5, color="#333",
                    zorder=8)
    if legend and stats_lines:
        x, y, ha, va = _CORNERS[corners[1] if title else corners[0]]
        if len(set(stats_colors)) <= 1:
            ax.text(x, y, mean_label + "\n" + "\n".join(stats_lines), ha=ha, va=va, fontsize=8.5, zorder=8,
                    linespacing=1.35, color="#222")
        else:
            step = 0.09 if va == "top" else -0.09
            plural = mean_label + "s" if mean_label.endswith("mean") else mean_label
            ax.text(x, y, plural, ha=ha, va=va, fontsize=8.5, zorder=8, color="#222")
            for k, (line, color) in enumerate(zip(stats_lines, stats_colors)):
                ax.text(x, y - step * (k + 1), line, ha=ha, va=va, fontsize=7.5, zorder=8, color=color)
    return fig


def components_overview_figure(data: dc.DemagData, coord: int, components=None, level: str = "location",
                               name: Optional[str] = None, color_of=None, panel_size: float = 3.4) -> Figure:
    """One equal-area net per component with every good specimen fit and its Fisher mean.

    Mirrors the "directions for all specimens" row of Slotznick et al.
    (2023): each panel is titled with the component name, captioned with the
    coordinate system and annotated with the Fisher statistics.

    Args:
        data: the study.
        coord: MagIC ``dir_tilt_correction`` code.
        components: component names to show (default: all, in first-seen order).
        level/name: restrict to one sample/site/location (default: everything).
        color_of: callable name -> colour (default: a palette by order).
    """
    comps = list(components) if components is not None else data.component_names()
    if not comps:
        raise ValueError("no components to plot")
    if color_of is None:
        palette = COMPONENT_PALETTE
        color_of = lambda n: palette[comps.index(n) % len(palette)]        # noqa: E731
    fig = Figure(figsize=(panel_size * len(comps), panel_size + 0.2))
    width = 1.0 / len(comps)
    for k, comp in enumerate(comps):
        ax = fig.add_axes([k * width + 0.01 * width, 0.02, 0.98 * width, 0.94])
        dirs, planes = [], []
        for c in data.components:
            if c.name != comp or c.quality != "g":
                continue
            spec = data.specimens[c.specimen]
            if name is not None and getattr(spec, level) != name:
                continue
            res = data.fit(c, coord)
            if res is None:
                continue
            if res.direction_type == "p":
                planes.append((res.dir_dec, res.dir_inc, color_of(comp)))
            else:
                dirs.append((res.dir_dec, res.dir_inc, c.specimen, color_of(comp)))
        means = data.mean_directions(level, coord, comp)
        mean = None
        if len(means):
            if name is not None:
                sel = means[means[level] == name]
                mean = sel.iloc[0].to_dict() if len(sel) else None
            elif len(means) == 1:
                mean = means.iloc[0].to_dict()
        directions_figure(dirs, mean, title=comp, planes=planes, caption=f"({dc.COORD_NAMES[coord]})", ax=ax)
    return fig


def vgp_figure(vgps, pole: Optional[dict] = None, title: str = "", figsize=(4.5, 4.5)) -> Figure:
    """VGPs (and mean pole with A95) on an equal-area projection centred on the north pole.

    Args:
        vgps: iterable of (lon, lat, label).
        pole: dict with plon, plat, A95 from ``DemagData.mean_pole``.
    """
    fig = Figure(figsize=figsize)
    ax = fig.add_axes([0.05, 0.05, 0.9, 0.86])
    _draw_net(ax, labels=("0°", "90°E", "180°", "90°W"))
    for lat_ring in (30, 60):
        rx, ry = dc.equal_area_xy(np.arange(0, 361, 2.0), np.full(181, float(lat_ring)))
        ax.plot(rx, ry, ":", color="#b5bac2", lw=0.6)
    vg = list(vgps)
    if vg:
        lon = np.array([v[0] for v in vg], float)
        lat = np.array([v[1] for v in vg], float)
        _equal_area_points(ax, lon, lat, [POINT_FILL] * len(vg), size=20)
    if pole:
        px, py = dc.equal_area_xy([pole["plon"]], [pole["plat"]])
        ax.scatter(px, py, marker="s", s=100, c=MEAN_COLOR, edgecolors=POINT_EDGE, linewidths=0.6, zorder=6)
        cd, ci = dc.pmag.circ(pole["plon"], pole["plat"], pole["A95"])
        cx, cy = dc.equal_area_xy(cd, np.abs(ci))
        ax.plot(cx, cy, color=MEAN_COLOR, lw=1.2)
        ax.text(1.1, -1.1, "pole %.1f°E, %.1f°N\nA95 %.1f, K %.0f, N %d" % (
            pole["plon"], pole["plat"], pole["A95"], pole["K"], pole["N"]), ha="right", va="bottom", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d0d4da"))
    if title:
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    return fig


def vgp_map_figure(vgps, pole: Optional[dict] = None, sites=(), centre=None, title: str = "",
                   color: str = "#3b6fb6", figsize=(5.4, 5.9), caption: Optional[str] = None) -> Figure:
    """VGPs, the mean pole with its A95 and the sampling sites on an orthographic globe.

    The globe shows Natural Earth land and a 30° graticule so that the
    reader sees poles on the Earth rather than directions on a net (cf.
    Swanson-Hysell et al., 2025, Geology, Fig. 2D).

    Args:
        vgps: iterable of (lon, lat, label) or (lon, lat, label, flipped);
            flipped VGPs (antipode taken for a common polarity) are open symbols.
        pole: dict from ``DemagData.mean_pole`` (plon, plat, A95, K, N, paleolat ...).
        sites: iterable of (lon, lat, name) sampling sites, drawn as a star.
        centre: (lon, lat) of the globe centre; default the mean pole.
        caption: text block replacing the automatic pole statistics.
    """
    vg, sites = list(vgps), list(sites)
    if centre is None:
        if pole:
            centre = (pole["plon"], pole["plat"])
        elif vg:
            centre = (vg[0][0], vg[0][1])
        else:
            centre = (0.0, 90.0)
    lon0, lat0 = float(centre[0]), float(centre[1])
    fig = Figure(figsize=figsize)
    ax = fig.add_axes([0.03, 0.13, 0.94, 0.80])
    ax.set_aspect("equal")
    ax.axis("off")
    cx, cy = geo.circle_outline()
    ax.fill(cx, cy, color=OCEAN_COLOR, zorder=0)
    outers, holes = geo.land_patches(lon0, lat0)
    for x, y in outers:
        ax.fill(x, y, color=LAND_COLOR, ec=LAND_EDGE, lw=0.4, zorder=1)
    for x, y in holes:
        ax.fill(x, y, color=OCEAN_COLOR, ec=LAND_EDGE, lw=0.4, zorder=1)
    for x, y in geo.graticule(lon0, lat0):
        ax.plot(x, y, ":", color="#9aa3ad", lw=0.5, zorder=2)
    ax.plot(cx, cy, color="#2b2b2b", lw=1.0, zorder=3)
    hidden = 0
    if vg:
        lon = np.array([v[0] for v in vg], float)
        lat = np.array([v[1] for v in vg], float)
        x, y, vis = geo.orthographic_xy(lon, lat, lon0, lat0)
        flipped = np.array([bool(v[3]) if len(v) > 3 else False for v in vg])
        hidden = int((~vis).sum())
        keep = vis & ~flipped
        ax.scatter(x[keep], y[keep], s=24, c=color, edgecolors="#2b2b2b", linewidths=0.5, zorder=5,
                   label="virtual geomagnetic poles")
        keep = vis & flipped
        if keep.any():
            ax.scatter(x[keep], y[keep], s=24, facecolors="white", edgecolors=color, linewidths=0.9, zorder=5,
                       label="VGPs (antipode taken)")
    if sites:
        x, y, vis = geo.orthographic_xy([s[0] for s in sites], [s[1] for s in sites], lon0, lat0)
        ax.scatter(x[vis], y[vis], marker="*", s=170, c=SITE_COLOR, edgecolors="#1b3d1b", linewidths=0.5, zorder=6,
                   label="study location")
    if pole:
        x, y, vis = geo.orthographic_xy([pole["plon"]], [pole["plat"]], lon0, lat0)
        ax.scatter(x[vis], y[vis], marker="s", s=150, c=MEAN_COLOR, alpha=0.85, edgecolors="#2b2b2b", linewidths=0.6,
                   zorder=7, label="mean paleomagnetic pole")
        circle = geo.small_circle(pole["plon"], pole["plat"], pole["A95"])
        for xs, ys in geo.project_lines([circle], lon0, lat0):
            ax.plot(xs, ys, color=MEAN_COLOR, lw=1.3, zorder=7)
        if caption is None:
            lines = [f"pole longitude = {pole['plon']:.1f}°E", f"pole latitude = {pole['plat']:.1f}°N",
                     f"A$_{{95}}$ = {pole['A95']:.1f}°   K = {pole['K']:.1f}   N = {pole['N']}"]
            if "paleolat" in pole:
                lines.append(f"paleolatitude = {pole['paleolat']:.1f} ± {pole['A95']:.1f}°")
            caption = "\n".join(lines)
    if caption:
        ax.text(-1.06, 1.06, caption, ha="left", va="top", fontsize=8, zorder=10,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#d0d4da"))
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=8, bbox_to_anchor=(0.5, 0.01),
                   handletextpad=0.4, columnspacing=1.4)
    if hidden:
        fig.text(0.97, 0.125, f"{hidden} VGP(s) on the far hemisphere", ha="right", va="bottom", fontsize=7,
                 color="#6b7280")
    if title:
        ax.set_title(title, loc="left", fontsize=11, fontweight="bold")
    return fig


# ---------------------------------------------------------------------------
# saving
# ---------------------------------------------------------------------------
def save_figure(fig: Figure, path: str, fmt: Optional[str] = None, dpi: int = 300) -> str:
    """Write a figure as PNG, PDF or SVG (format from ``fmt`` or the extension)."""
    fmt = (fmt or os.path.splitext(path)[1].lstrip(".") or "pdf").lower()
    if not path.lower().endswith("." + fmt):
        path = os.path.splitext(path)[0] + "." + fmt
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, format=fmt, dpi=dpi, bbox_inches="tight")
    return path
