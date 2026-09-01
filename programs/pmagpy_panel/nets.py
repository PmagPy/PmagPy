"""
Equal-area net primitives.

A net is the one figure every one of these applications draws, and the one that
is easy to get subtly wrong: a net that is not circular misreads directions. The
square-frame construction and the guard that keeps it circular whatever the
browser does to the layout live here so that no application has to rediscover
them, and so that a fix reaches all of them.
"""
from __future__ import annotations

import numpy as np
from bokeh.events import Reset
from bokeh.models import CustomJS, Label
from bokeh.plotting import figure

import pmagpy.demag as dc

from .theme import NET_COLOR, style_figure


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
