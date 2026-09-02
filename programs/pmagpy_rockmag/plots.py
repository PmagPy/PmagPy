"""
Bokeh figure builders for the views whose core function has no interactive
plot of its own (the matplotlib ``verwey_estimate`` draws from
``calc_verwey_estimate``; here the same numbers go to Bokeh).

Each builder takes the core function's result, never the measurements table,
so what is drawn is exactly what the analyst's notebook call would compute.
"""
from __future__ import annotations

import numpy as np
from bokeh.models import BoxAnnotation, HoverTool
from bokeh.plotting import figure

from pmagpy_panel.theme import style_figure

MEASUREMENT_COLOR = "#b22222"      # FireBrick, as in rockmag.verwey_estimate
BACKGROUND_COLOR = "#008080"       # Teal
MAGNETITE_COLOR = "#4169e1"        # RoyalBlue
MARK_COLOR = "#ffb6c1"             # Pink star
EXCLUDED_COLOR = "#9aa1ab"


def _figure(title: str, y_label: str, height: int = 400):
    tools = [HoverTool(tooltips=[("T", "@x{0.0}"), ("y", "@y")]), "pan,box_zoom,wheel_zoom,reset,save"]
    fig = figure(title=title, x_axis_label="Temperature (K)", y_axis_label=y_label, tools=tools,
                 sizing_mode="stretch_width", height=height)
    return style_figure(fig)


def _series(fig, x, y, color, label, marker, size=4):
    fig.line(x, y, color=color, legend_label=label)
    fig.scatter(x, y, color=color, marker=marker, size=size, legend_label=label)


def _star(fig, x, y, label):
    fig.scatter([x], [y], marker="star", size=16, color=MARK_COLOR, line_color="black", legend_label=label)


def verwey_figures(temps, mags, result, excluded: tuple, title: str = ""):
    """The two Verwey panels — M(T) and dM/dT with the background fit and the magnetite residual.

    Args:
        temps, mags: the series that went into ``calc_verwey_estimate``.
        result: what it returned (the 10-tuple).
        excluded: ``(t_min, t_max)`` shaded on the derivative panel.
        title: put on the M(T) panel (the specimen and method).
    Returns:
        ``(m_fig, dmdt_fig)``
    """
    (dM_dT_df, verwey_t, remanence_loss, r_squared, temps_background, temps_dM_dT_background,
     mgt_dM_dT, dM_dT_polyfit, background_curve, mgt_curve) = result
    tv_label = f"Verwey estimate ({verwey_t:.1f} K)"

    m_fig = _figure(title or "Remanence", "M (Am²/kg)")
    _series(m_fig, temps, mags, MEASUREMENT_COLOR, "measurement", "circle")
    _series(m_fig, temps_background, background_curve, BACKGROUND_COLOR, "background fit", "square")
    _series(m_fig, temps_background, mgt_curve, MAGNETITE_COLOR, "magnetite (meas. − background)", "diamond")
    _star(m_fig, verwey_t, float(np.interp(verwey_t, temps_background, mgt_curve)), tv_label)
    m_fig.legend.location = "top_right"

    d_fig = _figure("Derivative", "dM/dT (Am²/kg/K)")
    d_fig.add_layout(BoxAnnotation(left=excluded[0], right=excluded[1], fill_color=EXCLUDED_COLOR, fill_alpha=0.25,
                                   line_width=0))
    _series(d_fig, dM_dT_df["T"], dM_dT_df["dM_dT"], MEASUREMENT_COLOR, "measurement", "circle")
    _series(d_fig, temps_dM_dT_background, dM_dT_polyfit, BACKGROUND_COLOR, f"background fit (r² = {r_squared:.3f})",
            "square")
    _series(d_fig, temps_dM_dT_background, mgt_dM_dT, MAGNETITE_COLOR, "magnetite (background − meas.)", "diamond")
    _star(d_fig, verwey_t, float(np.interp(verwey_t, temps_dM_dT_background, mgt_dM_dT)), tv_label)
    d_fig.legend.location = "bottom_right"
    for fig in (m_fig, d_fig):
        fig.legend.click_policy = "hide"
        fig.legend.label_text_font_size = "9pt"
        fig.legend.background_fill_alpha = 0.7
    return m_fig, d_fig
