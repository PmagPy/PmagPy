"""
Bokeh figures for the anisotropy views: eigenvectors on an equal-area net
(specimens, and the mean with its confidence ellipses), the bootstrap
eigenvalue distributions, and the shape plots (Jelinek P'–T, Flinn F–L).

Everything drawn here is computed by ``pmagpy.anisotropy``; this module only
puts it on a canvas. The markers follow PmagPy's convention (``ipmag.plot_aniso``):
V1 red squares, V2 blue triangles, V3 black circles. Eigenvectors are axes,
so every direction is plotted in the lower hemisphere and an ellipse that
crosses the horizon continues at its antipode.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure

from pmagpy import demag
from pmagpy.anisotropy import bootstrap_ellipses, hext_ellipses
from pmagpy_panel.nets import net_figure
from pmagpy_panel.theme import MUTED_STYLE, style_figure  # noqa: F401  (MUTED_STYLE re-exported for views)

AXES = (("v1", "square", "#c8102e", "V1"), ("v2", "triangle", "#1f4e9c", "V2"), ("v3", "circle", "#2b2b2b", "V3"))
COMPARISON_COLOR = "#1a7f5a"
NET_SIZE = 360


def _xy(dec, inc):
    """Equal-area coordinates of axes: every direction flipped into the lower hemisphere first."""
    dec, inc = np.asarray(dec, float), np.asarray(inc, float)
    dec = np.where(inc < 0, (dec + 180) % 360, dec)
    return demag.equal_area_xy(dec, np.abs(inc))


def _ellipse_segments(points: np.ndarray):
    """Split an ellipse's (dec, inc) points where it crosses the horizon; each run drawn on the lower hemisphere."""
    if len(points) == 0:
        return [], []
    upper = points[:, 1] < 0
    breaks = np.flatnonzero(np.diff(upper.astype(int)) != 0) + 1
    xs, ys = [], []
    for run in np.split(np.arange(len(points)), breaks):
        x, y = _xy(points[run, 0], points[run, 1])
        xs.append(list(x))
        ys.append(list(y))
    return xs, ys


def specimen_net(tensors: pd.DataFrame, size: int = NET_SIZE, title: str = "eigenvectors of the specimens"):
    """Every specimen's three eigenvectors on an equal-area net, with hover."""
    fig = net_figure(title, size, tools="pan,wheel_zoom,reset,save")
    for key, marker, color, label in AXES:
        if not len(tensors):
            continue
        x, y = _xy(tensors[f"{key}_dec"], tensors[f"{key}_inc"])
        src = ColumnDataSource(dict(x=x, y=y, specimen=tensors["specimen"].astype(str),
                                    dec=tensors[f"{key}_dec"], inc=np.abs(tensors[f"{key}_inc"]),
                                    tau=tensors[f"tau{key[1]}"]))
        r = fig.scatter("x", "y", source=src, marker=marker, size=8, color=color, alpha=0.75,
                        line_color=color, legend_label=label)
        fig.add_tools(HoverTool(renderers=[r], tooltips=[("specimen", "@specimen"), (label, "@dec{0.0} / @inc{0.0}"),
                                                         ("τ", "@tau{0.0000}")]))
    if len(tensors):
        fig.legend.location = "bottom_left"
        fig.legend.label_text_font_size = "8pt"
        fig.legend.glyph_height = 12
        fig.legend.glyph_width = 12
        fig.legend.spacing = 0
        fig.legend.padding = 4
        fig.legend.background_fill_alpha = 0.7
    return fig


def mean_net(stats: Optional[dict], size: int = NET_SIZE, show_hext: bool = True, show_bootstrap: bool = True,
             cloud: bool = False, comparison: Optional[tuple] = None, title: str = "mean eigenvectors"):
    """The mean tensor's eigenvectors with their Hext (solid) and bootstrap (dashed) ellipses.

    Args:
        stats: ``anisotropy.group_statistics`` result, or None for an empty net.
        show_hext, show_bootstrap: draw the ellipses the statistics contain.
        cloud: also scatter the bootstrap eigenvectors.
        comparison: a ``(dec, inc)`` direction to mark (a field direction, a
            structural axis) — drawn as a green star.
    """
    fig = net_figure(title, size, tools="pan,wheel_zoom,reset,save")
    if stats is None:
        return fig
    hpars = stats.get("hext")
    boot = stats.get("bootstrap")
    if cloud and boot is not None:
        vectors = boot["vectors"]
        for i, (key, marker, color, label) in enumerate(AXES):
            x, y = _xy(vectors[:, i, 0], vectors[:, i, 1])
            fig.scatter(x, y, marker=marker, size=3, color=color, alpha=0.15, line_color=None)
    if show_hext and hpars is not None:
        for key, ell in hext_ellipses(hpars).items():
            xs, ys = _ellipse_segments(ell)
            color = dict((a[0], a[2]) for a in AXES)[key]
            fig.multi_line(xs, ys, color=color, line_width=1.5)
    if show_bootstrap and boot is not None and hpars is not None:
        for key, ell in bootstrap_ellipses(hpars, boot["params"]).items():
            xs, ys = _ellipse_segments(ell)
            color = dict((a[0], a[2]) for a in AXES)[key]
            fig.multi_line(xs, ys, color=color, line_width=1.5, line_dash="dashed")
    for key, marker, color, label in AXES:
        x, y = _xy([stats[f"{key}_dec"]], [stats[f"{key}_inc"]])
        src = ColumnDataSource(dict(x=x, y=y, dec=[stats[f"{key}_dec"]], inc=[abs(stats[f"{key}_inc"])],
                                    tau=[stats[f"tau{key[1]}"]]))
        r = fig.scatter("x", "y", source=src, marker=marker, size=13, color=color, line_color="white", line_width=1.2,
                        legend_label=label)
        fig.add_tools(HoverTool(renderers=[r], tooltips=[(label, "@dec{0.0} / @inc{0.0}"), ("τ", "@tau{0.0000}")]))
    if comparison is not None:
        x, y = _xy([comparison[0]], [comparison[1]])
        fig.scatter(x, y, marker="star", size=16, color=COMPARISON_COLOR, line_color="white",
                    legend_label="comparison")
    fig.legend.location = "bottom_left"
    fig.legend.label_text_font_size = "8pt"
    fig.legend.glyph_height = 12
    fig.legend.glyph_width = 12
    fig.legend.spacing = 0
    fig.legend.padding = 4
    fig.legend.background_fill_alpha = 0.7
    return fig


def eigenvalue_cdf(taus: np.ndarray, bounds: Optional[dict] = None, width: int = 420, height: int = 300):
    """Cumulative distributions of the bootstrapped eigenvalues, with the confidence bounds as vertical lines."""
    fig = figure(width=width, height=height, tools="pan,wheel_zoom,reset,save", x_axis_label="eigenvalue τ",
                 y_axis_label="cumulative fraction", title="bootstrap eigenvalue distributions")
    style_figure(fig)
    fig.title.text_font_size = "10pt"
    taus = np.asarray(taus, float)
    if taus.size == 0:
        return fig
    n = len(taus)
    frac = np.arange(1, n + 1) / n
    for i, (key, marker, color, label) in enumerate(AXES):
        fig.line(np.sort(taus[:, i]), frac, color=color, line_width=1.8, legend_label=f"τ{i + 1}")
        if bounds is not None:
            for edge in bounds[f"tau{i + 1}"]:
                fig.add_layout(Span(location=edge, dimension="height", line_color=color, line_dash="dashed",
                                    line_width=1))
    fig.legend.location = "bottom_right"
    fig.legend.label_text_font_size = "8pt"
    fig.legend.background_fill_alpha = 0.7
    return fig


def _shape_figure(tensors, mean, xcol, ycol, x_label, y_label, title, width, height):
    fig = figure(width=width, height=height, tools="pan,wheel_zoom,box_zoom,reset,save", x_axis_label=x_label,
                 y_axis_label=y_label, title=title)
    style_figure(fig)
    fig.title.text_font_size = "10pt"
    if len(tensors):
        src = ColumnDataSource(dict(x=tensors[xcol], y=tensors[ycol], specimen=tensors["specimen"].astype(str)))
        r = fig.scatter("x", "y", source=src, marker="circle", size=8, color="#8c8c8c", line_color="#2b2b2b",
                        alpha=0.85)
        fig.add_tools(HoverTool(renderers=[r], tooltips=[("specimen", "@specimen"), (x_label, "@x{0.000}"),
                                                         (y_label, "@y{0.000}")]))
    if mean is not None:
        fig.scatter([mean[xcol]], [mean[ycol]], marker="diamond", size=14, color="#e76f51", line_color="white",
                    legend_label="mean tensor")
        fig.legend.location = "top_left"
        fig.legend.label_text_font_size = "8pt"
        fig.legend.background_fill_alpha = 0.7
    return fig


def jelinek_plot(tensors: pd.DataFrame, mean: Optional[dict] = None, width: int = 420, height: int = 360):
    """Jelinek (1981) plot: shape factor T against corrected anisotropy degree P'; oblate above T = 0."""
    fig = _shape_figure(tensors, mean, "aniso_pp", "aniso_t", "P′", "T", "Jelinek plot", width, height)
    fig.add_layout(Span(location=0, dimension="width", line_color="#9aa1ab", line_dash="dotted"))
    fig.y_range.start, fig.y_range.end = -1.05, 1.05
    if len(tensors):
        fig.x_range.start = 1.0
    return fig


def flinn_plot(tensors: pd.DataFrame, mean: Optional[dict] = None, width: int = 420, height: int = 360):
    """Flinn diagram: lineation L = τ1/τ2 against foliation F = τ2/τ3; the diagonal separates prolate from oblate."""
    fig = _shape_figure(tensors, mean, "aniso_f", "aniso_l", "F = τ₂/τ₃", "L = τ₁/τ₂", "Flinn diagram", width, height)
    if len(tensors):
        top = float(max(tensors["aniso_f"].max(), tensors["aniso_l"].max(), 1.0)) * 1.02
        fig.line([1, top], [1, top], color="#9aa1ab", line_dash="dotted")
        fig.x_range.start = fig.y_range.start = 1.0
    return fig
