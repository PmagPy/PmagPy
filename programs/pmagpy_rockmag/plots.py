"""
Bokeh figure builders for the views whose core function has no interactive
plot of its own (the matplotlib ``verwey_estimate`` draws from
``calc_verwey_estimate``; here the same numbers go to Bokeh).

Each builder takes the core function's result, never the measurements table,
so what is drawn is exactly what the analyst's notebook call would compute.
"""
from __future__ import annotations

import numpy as np
from bokeh.models import BasicTickFormatter, BoxAnnotation, HoverTool
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
    fig.yaxis.formatter = BasicTickFormatter(precision=2)               # 3.00e-4, not 3.000e-4, on small remanences
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


WARM_COLOR = "#d62728"             # as in rockmag.goethite_removal
COOL_COLOR = "#17becf"


def goethite_figures(result: dict, fit_range: tuple, title: str = ""):
    """The four goethite-removal panels from ``calc_goethite_removal``'s result.

    Args:
        result: the dict ``calc_goethite_removal`` returned.
        fit_range: ``(t_min, t_max)`` shaded on the measured panel.
        title: put on the measured panel (the specimen).
    Returns:
        ``[[measured, corrected], [derivative, corrected derivative]]`` — rows for ``gridplot``.
    """
    r = result
    measured = _figure(title or "RTSIRM", "M (Am²/kg)", height=340)
    measured.add_layout(BoxAnnotation(left=fit_range[0], right=fit_range[1], fill_color=EXCLUDED_COLOR, fill_alpha=0.25,
                                      line_width=0))
    _series(measured, r["warm_temps"], r["warm_mags"], WARM_COLOR, "RTSIRM warming", "circle")
    _series(measured, r["cool_temps"], r["cool_mags"], COOL_COLOR, "RTSIRM cooling", "circle")
    measured.line(r["warm_temps"], r["warm_fit"], color=WARM_COLOR, line_dash="dashed", line_width=2,
                  legend_label="goethite fit")
    measured.legend.location = "top_right"

    corrected = _figure("Goethite removed", "M (Am²/kg)", height=340)
    _series(corrected, r["warm_temps"], r["warm_corrected"], WARM_COLOR, "warming − fit", "square")
    _series(corrected, r["cool_temps"], r["cool_corrected"], COOL_COLOR, "cooling − fit", "square")
    corrected.legend.location = "top_right"

    derivative = _figure("Derivative", "dM/dT (Am²/kg/K)", height=340)
    _series(derivative, r["cool_derivative"]["T"], r["cool_derivative"]["dM_dT"], COOL_COLOR, "cooling", "circle")
    _series(derivative, r["warm_derivative"]["T"], r["warm_derivative"]["dM_dT"], WARM_COLOR, "warming", "circle")
    derivative.legend.location = "bottom_right"

    corrected_derivative = _figure("Derivative, goethite removed", "dM/dT (Am²/kg/K)", height=340)
    _series(corrected_derivative, r["cool_corrected_derivative"]["T"], r["cool_corrected_derivative"]["dM_dT"],
            COOL_COLOR, "cooling − fit", "square")
    _series(corrected_derivative, r["warm_corrected_derivative"]["T"], r["warm_corrected_derivative"]["dM_dT"],
            WARM_COLOR, "warming − fit", "square")
    corrected_derivative.legend.location = "bottom_right"

    rows = [[measured, corrected], [derivative, corrected_derivative]]
    for fig in rows[0] + rows[1]:
        fig.legend.click_policy = "hide"
        fig.legend.label_text_font_size = "9pt"
        fig.legend.background_fill_alpha = 0.7
    return rows


def forc_curves_figure(forcs, title: str = "", y_label: str = "Moment (Am²)", height: int = 420):
    """The reversal curves a FORC run measured, after the pipeline's drift and endpoint conditioning.

    Args:
        forcs: ``out["forcs_display"]`` of ``pmagpy.forc.process_forc`` — ``Segment`` objects with
            ``H`` (T) and ``M`` arrays, one per reversal curve.
        title: the specimen, say.
        y_label: the moment column's unit.
    Returns:
        A Bokeh figure, fields in mT, one line per curve.
    """
    tools = [HoverTool(tooltips=[("B", "@xs{0.0} mT")], line_policy="nearest"), "pan,box_zoom,wheel_zoom,reset,save"]
    fig = figure(title=title, x_axis_label="Field (mT)", y_axis_label=y_label, tools=tools, width=460, height=height)
    fig.yaxis.formatter = BasicTickFormatter(precision=2)
    fig.multi_line(xs=[1e3 * np.asarray(seg.H) for seg in forcs], ys=[np.asarray(seg.M) for seg in forcs],
                   line_color=MAGNETITE_COLOR, line_width=0.8, line_alpha=0.6)
    fig.line([0, 0], [min(np.nanmin(seg.M) for seg in forcs), max(np.nanmax(seg.M) for seg in forcs)],
             line_color="#9aa1ab", line_dash="dotted")
    return style_figure(fig)
