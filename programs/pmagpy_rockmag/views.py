"""
The panes: the dataset block, the experiment index, and one view per
experiment type.

Each view is a Panel layout over one ``pmagpy.rockmag`` plotting function: the
widgets are the arguments the function takes, and the view's "show code" block
is the call it is making. A view is built from a :class:`Session`, or — in a
notebook — straight from a measurements DataFrame::

    MpmsDcView(measurements).panel()
"""
from __future__ import annotations

import warnings
from typing import Optional

import numpy as np
import panel as pn
from bokeh.layouts import gridplot

from pmagpy import rockmag
from pmagpy_panel import code
from pmagpy_panel.chooser import DirectoryChooser
from pmagpy_panel.theme import MUTED_STYLE, SECTION_STYLE, kpi, style_figure
from . import plots
from .session import RECENT_FILE, Session, as_session, env

MPMS_DC_SERIES = (("fc_data", "FC"), ("zfc_data", "ZFC"), ("rtsirm_cool_data", "RTSIRM cooling"),
                  ("rtsirm_warm_data", "RTSIRM warming"))


def section(title: str) -> pn.pane.HTML:
    return pn.pane.HTML(f'<div style="{SECTION_STYLE}">{title}</div>', margin=(10, 0, 0, 0))


def muted(text: str) -> str:
    return f'<div style="{MUTED_STYLE}">{text}</div>'


def preamble(session: Session) -> list:
    """The lines that get `measurements` into a notebook the way the RockmagPy notebooks do."""
    lines = ["import pmagpy.rockmag as rmag", "import pmagpy.contribution_builder as cb", ""]
    if session.directory:
        lines += [code.assign("contribution", code.call("cb.Contribution", session.directory)),
                  "measurements = contribution.tables['measurements'].df"]
    else:
        lines += ["# measurements: the DataFrame this view was given"]
    return lines


# ----------------------------------------------------------------------------- dataset + index
class DataView(DirectoryChooser):
    """Switch between MagIC directories (the toolkit's chooser, counting experiments)."""

    def __init__(self, session: Session, chooser=None, chooser_available=None):
        super().__init__(
            session, recent_file=RECENT_FILE, chooser=chooser, chooser_available=chooser_available,
            chooser_stub=env("CHOOSER_STUB"),
            count=lambda s: f"{s.experiments['specimen'].nunique()} specimens · {len(s.experiments)} experiments",
            note="Any MagIC directory with rock-magnetic measurements; the experiment types found decide the views.")


class ExperimentIndex:
    """The side column's index: experiments by type, and the current specimen's own."""

    def __init__(self, session: Session):
        self.s = session
        self.types = pn.pane.HTML("", sizing_mode="stretch_width")
        self.current = pn.pane.HTML("", sizing_mode="stretch_width")
        session.param.watch(lambda e: self.refresh(), ["directory", "specimen"])
        self.refresh()

    def refresh(self) -> None:
        rows = [f'<tr><td>{t.label}</td><td style="text-align:right"><b>{n_spec}</b></td>'
                f'<td style="text-align:right;{MUTED_STYLE}">{n_exp}</td></tr>'
                for t, n_spec, n_exp in self.s.type_counts()]
        unclaimed = self.s.unclaimed()
        if len(unclaimed):
            rows.append(f'<tr><td style="{MUTED_STYLE}">not plotted here</td>'
                        f'<td style="text-align:right;{MUTED_STYLE}">{unclaimed["specimen"].nunique()}</td>'
                        f'<td style="text-align:right;{MUTED_STYLE}">{len(unclaimed)}</td></tr>')
        if rows:
            head = (f'<tr style="{MUTED_STYLE}"><th style="text-align:left;font-weight:normal">type</th>'
                    f'<th style="text-align:right;font-weight:normal">specimens</th>'
                    f'<th style="text-align:right;font-weight:normal">experiments</th></tr>')
            self.types.object = f'<table style="width:100%;border-collapse:collapse">{head}{"".join(rows)}</table>'
        else:
            self.types.object = muted("no experiments")
        spec = self.s.specimen
        own = self.s.experiments[self.s.experiments["specimen"] == spec] if spec else self.s.experiments.iloc[0:0]
        items = "".join(f'<li><code>{r.method_codes}</code> <span style="{MUTED_STYLE}">{r.n} steps</span></li>'
                        for r in own.itertuples())
        self.current.object = (f'<div><b>{spec}</b></div><ul style="margin:4px 0 0 0;padding-left:18px">{items}</ul>'
                               if spec else muted("no specimen"))

    def panel(self) -> pn.Column:
        return pn.Column(section("Experiments"), self.types, section("Specimen"), self.current,
                         sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- MPMS DC
class MpmsDcView:
    """FC / ZFC / RTSIRM cycling curves and their derivatives: ``rockmag.plot_mpms_dc``.

    Controls are the function's own arguments — the derivative panels and
    dropping the first/last point of each series (the MPMS's settling points).
    """

    TYPE = "mpms_dc"

    def __init__(self, session):
        self.s = as_session(session)
        self.specimen = pn.widgets.Select(name="Specimen", options=[], width=320)
        self.derivative = pn.widgets.Checkbox(name="dM/dT panels", value=True, margin=(26, 5, 0, 10))
        self.drop_first = pn.widgets.Checkbox(name="drop first point", value=False, margin=(26, 5, 0, 10))
        self.drop_last = pn.widgets.Checkbox(name="drop last point", value=False, margin=(26, 5, 0, 10))
        self.series = pn.pane.HTML("", sizing_mode="stretch_width")
        self.plot = pn.pane.Bokeh(sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.figure = None

        self.specimen.param.watch(self._on_specimen, "value")
        for w in (self.derivative, self.drop_first, self.drop_last):
            w.param.watch(lambda e: self.refresh(), "value")
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")
        self.reset()

    # ----- state --------------------------------------------------------------
    def reset(self) -> None:
        """New data: offer the specimens with an MPMS DC experiment, keep the session's if it has one."""
        options = self.s.specimens(self.TYPE)
        before = self.specimen.value
        self.specimen.options = options
        self.specimen.value = self.s.specimen if self.s.specimen in options else (options[0] if options else None)
        if self.specimen.value == before:                 # otherwise the change itself refreshed
            self.refresh()

    def _on_specimen(self, event) -> None:
        if event.new:
            self.s.specimen = event.new
        self.refresh()

    def _follow_session(self, event) -> None:
        if event.new in self.specimen.options and event.new != self.specimen.value:
            self.specimen.value = event.new

    # ----- the plot -----------------------------------------------------------
    def data(self) -> Optional[tuple]:
        """The four series for the chosen specimen, or None when there is nothing to plot."""
        if not self.specimen.value or self.s.measurements is None:
            return None
        return rockmag.extract_mpms_data_dc(self.s.measurements, self.specimen.value)

    def refresh(self) -> None:
        series = self.data()
        if series is None or all(df is None or df.empty for df in series):
            self.figure = None
            self.plot.object = None
            self.series.object = muted("no FC, ZFC or RTSIRM experiment in this directory")
            self.code.set(preamble(self.s))
            return
        kwargs = dict(interactive=True, plot_derivative=self.derivative.value, return_figure=True, show_plot=False)
        if self.drop_first.value:
            kwargs["drop_first"] = True
        if self.drop_last.value:
            kwargs["drop_last"] = True
        self.figure = rockmag.plot_mpms_dc(*series, **kwargs)
        for fig in self.figure.children:
            style_figure(fig[0])
        self.plot.object = self.figure
        present = [f"{label} <b>{len(df)}</b>" for (_, label), df in zip(MPMS_DC_SERIES, series) if df is not None and len(df)]
        self.series.object = muted(" · ".join(present) + " points")
        names = [name for name, _ in MPMS_DC_SERIES]
        shown = {k: v for k, v in kwargs.items() if k not in ("return_figure", "show_plot")}
        self.code.set(preamble(self.s) + [
            code.assign(names, code.call("rmag.extract_mpms_data_dc", code.Name("measurements"), self.specimen.value)),
            code.call("rmag.plot_mpms_dc", *(code.Name(n) for n in names), **shown),
        ])

    # ----- layout -------------------------------------------------------------
    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.specimen, self.derivative, self.drop_first, self.drop_last),
                         self.series, self.plot, self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- Verwey
VERWEY_DEFAULTS = dict(background=(60, 250), excluded=(75, 150), poly_deg=3)
VERWEY_METHODS = {"LP-FC": "FC", "LP-ZFC": "ZFC"}
WEAK_LOSS = 0.005
"""A remanence loss below this fraction of the curve's range is called out as no clear transition."""


class VerweyView:
    """The Verwey transition from an FC or ZFC warming curve: ``rockmag.calc_verwey_estimate``.

    A polynomial is fitted to dM/dT over the background range, leaving out the
    excluded range where the transition is; the transition temperature is the
    peak of what remains (the zero crossing of its derivative) and the
    remanence loss its integral. The sliders are the function's arguments.
    """

    TYPE = "mpms_dc"

    def __init__(self, session):
        self.s = as_session(session)
        self.specimen = pn.widgets.Select(name="Specimen", options=[], width=320)
        self.method = pn.widgets.RadioButtonGroup(name="Curve", options={v: k for k, v in VERWEY_METHODS.items()},
                                                  button_type="default", margin=(24, 5, 0, 10))
        self.background = pn.widgets.RangeSlider(name="Background fit range (K)", start=0, end=300, step=1,
                                                 value=VERWEY_DEFAULTS["background"], width=300)
        self.excluded = pn.widgets.RangeSlider(name="Excluded from the fit (K)", start=0, end=300, step=1,
                                               value=VERWEY_DEFAULTS["excluded"], width=300)
        self.poly_deg = pn.widgets.IntSlider(name="Polynomial degree", start=1, end=5, value=VERWEY_DEFAULTS["poly_deg"],
                                             width=180)
        self.reset_btn = pn.widgets.Button(name="Reset", width=80, margin=(24, 5, 0, 10))
        self.result = pn.pane.HTML("", sizing_mode="stretch_width")
        self.plot = pn.pane.Bokeh(sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.figure = None
        self.estimate = None                      # (T_v, remanence loss, r²) of what is plotted

        self.specimen.param.watch(self._on_specimen, "value")
        self.method.param.watch(lambda e: self.refresh(), "value")
        for w in (self.background, self.excluded, self.poly_deg):
            w.param.watch(lambda e: self.refresh(), "value_throttled")     # once the slider is released
        self.reset_btn.on_click(lambda e: self.set_parameters(**VERWEY_DEFAULTS))
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")
        self.reset()

    # ----- state --------------------------------------------------------------
    def reset(self) -> None:
        exps = self.s.experiments
        has_curve = exps["method_codes"].isin(list(VERWEY_METHODS))
        options = list(dict.fromkeys(exps.loc[has_curve, "specimen"]))
        before = self.specimen.value
        self.specimen.options = options
        self.specimen.value = self.s.specimen if self.s.specimen in options else (options[0] if options else None)
        if self.specimen.value == before:
            self._on_specimen(None)

    def set_parameters(self, background=None, excluded=None, poly_deg=None) -> None:
        """Set the fit parameters from code (the Reset button, a notebook, a test) and refresh."""
        if background is not None:
            self.background.value = tuple(background)
        if excluded is not None:
            self.excluded.value = tuple(excluded)
        if poly_deg is not None:
            self.poly_deg.value = int(poly_deg)
        self.refresh()

    def _on_specimen(self, event) -> None:
        """Offer only the curves this specimen has (FC, ZFC or both) and plot the current one."""
        spec = self.specimen.value
        if not spec:
            self.refresh()
            return
        self.s.specimen = spec
        own = set(self.s.experiments.loc[self.s.experiments["specimen"] == spec, "method_codes"])
        before = self.method.value
        self.method.options = {label: m for m, label in VERWEY_METHODS.items() if m in own}
        if self.method.value not in self.method.options.values() and self.method.options:
            self.method.value = next(iter(self.method.options.values()))
        if self.method.value == before:                       # otherwise the change itself refreshed
            self.refresh()

    def _follow_session(self, event) -> None:
        if event.new in self.specimen.options and event.new != self.specimen.value:
            self.specimen.value = event.new

    # ----- the estimate -------------------------------------------------------
    def curve(self):
        """``(temps, mags)`` of the chosen specimen's FC or ZFC curve, or None."""
        if not self.specimen.value or self.s.measurements is None:
            return None
        fc, zfc, _, _ = rockmag.extract_mpms_data_dc(self.s.measurements, self.specimen.value)
        df = fc if self.method.value == "LP-FC" else zfc
        if df is None or df.empty:
            return None
        return df["meas_temp"].reset_index(drop=True).astype(float), df["magn_mass"].reset_index(drop=True).astype(float)

    def parameters(self) -> dict:
        """The keyword arguments the sliders stand for, in the function's order."""
        return dict(t_range_background_min=int(self.background.value[0]), t_range_background_max=int(self.background.value[1]),
                    excluded_t_min=int(self.excluded.value[0]), excluded_t_max=int(self.excluded.value[1]),
                    poly_deg=int(self.poly_deg.value))

    def refresh(self) -> None:
        curve = self.curve()
        if curve is None:
            self.figure = self.estimate = None
            self.plot.object = None
            self.result.object = muted("no FC or ZFC warming curve for this specimen")
            self.code.set(preamble(self.s))
            return
        temps, mags = curve
        params = self.parameters()
        try:
            result = rockmag.calc_verwey_estimate(temps.copy(), mags.copy(), **params)
        except Exception as ex:                                            # too few points in the ranges, usually
            self.figure = self.estimate = None
            self.plot.object = None
            self.result.object = (f'<div style="color:#b91c1c">The fit failed with these ranges: {ex}. '
                                  f'Widen the background range or narrow the excluded one.</div>')
            self.code.set(self._code(params))
            return
        verwey_t, loss, r2 = float(result[1]), float(result[2]), float(result[3])
        self.estimate = (verwey_t, loss, r2)
        title = f"{self.specimen.value} · {VERWEY_METHODS[self.method.value]}"
        m_fig, d_fig = plots.verwey_figures(temps, mags, result, self.excluded.value, title=title)
        self.figure = gridplot([[m_fig, d_fig]], sizing_mode="stretch_width")
        self.plot.object = self.figure
        self.result.object = kpi([("T<sub>V</sub>", f"{verwey_t:.1f} K"), ("remanence loss", f"{loss:.3g} Am²/kg"),
                                  ("background fit r²", f"{r2:.3f}")])
        lo, hi = self.excluded.value
        if loss <= WEAK_LOSS * float(mags.max() - mags.min()) or not lo <= verwey_t <= hi:
            self.result.object += muted("no clear loss of remanence above the background inside the excluded range — "
                                        "this curve may have no Verwey transition; the estimate is where the residual "
                                        "happens to peak")
        self.code.set(self._code(params))

    def _code(self, params: dict) -> list:
        df = "fc_data" if self.method.value == "LP-FC" else "zfc_data"
        return preamble(self.s) + [
            code.assign(["fc_data", "zfc_data", "rtsirm_cool_data", "rtsirm_warm_data"],
                        code.call("rmag.extract_mpms_data_dc", code.Name("measurements"), self.specimen.value)),
            f"temps, mags = {df}['meas_temp'], {df}['magn_mass']",
            code.assign(["verwey_temperature", "remanence_loss"],
                        code.call("rmag.verwey_estimate", code.Name("temps"), code.Name("mags"), **params)),
        ]

    # ----- layout -------------------------------------------------------------
    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.specimen, self.method, self.reset_btn),
                         pn.Row(self.background, self.excluded, self.poly_deg),
                         self.result, self.plot, self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- Goethite
GOETHITE_DEFAULTS = dict(fit_range=(150, 290), poly_deg=2)


class GoethiteView:
    """Goethite removal from RTSIRM cycling curves: ``rockmag.calc_goethite_removal``.

    A polynomial fitted to the warming curve over the fit range — where the
    remanence change is goethite's alone — is subtracted from both the
    warming and the cooling curve, leaving the other minerals' behaviour.
    """

    TYPE = "mpms_dc"

    def __init__(self, session):
        self.s = as_session(session)
        self.specimen = pn.widgets.Select(name="Specimen", options=[], width=320)
        self.fit_range = pn.widgets.RangeSlider(name="Goethite fit range (K)", start=0, end=300, step=1,
                                                value=GOETHITE_DEFAULTS["fit_range"], width=300)
        self.poly_deg = pn.widgets.IntSlider(name="Polynomial degree", start=1, end=5, value=GOETHITE_DEFAULTS["poly_deg"],
                                             width=180)
        self.reset_btn = pn.widgets.Button(name="Reset", width=80, margin=(24, 5, 0, 10))
        self.result = pn.pane.HTML("", sizing_mode="stretch_width")
        self.plot = pn.pane.Bokeh(sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.figure = None
        self.removal = None                       # calc_goethite_removal's dict for what is plotted

        self.specimen.param.watch(self._on_specimen, "value")
        for w in (self.fit_range, self.poly_deg):
            w.param.watch(lambda e: self.refresh(), "value_throttled")
        self.reset_btn.on_click(lambda e: self.set_parameters(**GOETHITE_DEFAULTS))
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")
        self.reset()

    # ----- state --------------------------------------------------------------
    def reset(self) -> None:
        """Offer the specimens with both RTSIRM curves."""
        exps = self.s.experiments
        by_spec = exps[exps["method_codes"].isin(["LP-CW-SIRM:LP-MC", "LP-CW-SIRM:LP-MW"])].groupby("specimen")["method_codes"].nunique()
        options = [spec for spec in dict.fromkeys(exps["specimen"]) if by_spec.get(spec, 0) == 2]
        before = self.specimen.value
        self.specimen.options = options
        self.specimen.value = self.s.specimen if self.s.specimen in options else (options[0] if options else None)
        if self.specimen.value == before:
            self.refresh()

    def set_parameters(self, fit_range=None, poly_deg=None) -> None:
        if fit_range is not None:
            self.fit_range.value = tuple(fit_range)
        if poly_deg is not None:
            self.poly_deg.value = int(poly_deg)
        self.refresh()

    def _on_specimen(self, event) -> None:
        if event.new:
            self.s.specimen = event.new
        self.refresh()

    def _follow_session(self, event) -> None:
        if event.new in self.specimen.options and event.new != self.specimen.value:
            self.specimen.value = event.new

    # ----- the removal --------------------------------------------------------
    def curves(self) -> Optional[tuple]:
        """``(rtsirm_warm, rtsirm_cool)`` DataFrames, or None."""
        if not self.specimen.value or self.s.measurements is None:
            return None
        _, _, cool, warm = rockmag.extract_mpms_data_dc(self.s.measurements, self.specimen.value)
        if warm is None or cool is None or warm.empty or cool.empty:
            return None
        return warm, cool

    def parameters(self) -> dict:
        return dict(t_min=int(self.fit_range.value[0]), t_max=int(self.fit_range.value[1]), poly_deg=int(self.poly_deg.value))

    def refresh(self) -> None:
        curves = self.curves()
        if curves is None:
            self.figure = self.removal = None
            self.plot.object = None
            self.result.object = muted("no RTSIRM warming and cooling pair for this specimen")
            self.code.set(preamble(self.s))
            return
        warm, cool = curves
        params = self.parameters()
        try:
            self.removal = rockmag.calc_goethite_removal(warm, cool, **params)
        except (ValueError, TypeError) as ex:
            self.figure = self.removal = None
            self.plot.object = None
            self.result.object = f'<div style="color:#b91c1c">The fit failed: {ex}. Widen the fit range or lower the degree.</div>'
            self.code.set(self._code(params))
            return
        rows = plots.goethite_figures(self.removal, self.fit_range.value, title=self.specimen.value)
        self.figure = gridplot(rows, sizing_mode="stretch_width")
        self.plot.object = self.figure
        low = int(self.removal["warm_temps"].idxmin())                  # the warming curve's coldest point
        measured = float(self.removal["warm_mags"].iloc[low])
        left = float(self.removal["warm_corrected"].iloc[low])
        removed = f"{100 * (1 - left / measured):.0f} %" if measured else "—"
        self.result.object = kpi([(f"warming remanence at {self.removal['warm_temps'].iloc[low]:.0f} K", f"{measured:.3g} Am²/kg"),
                                  ("after goethite removal", f"{left:.3g} Am²/kg"), ("removed", removed)])
        self.code.set(self._code(params))

    def _code(self, params: dict) -> list:
        return preamble(self.s) + [
            code.assign(["fc_data", "zfc_data", "rtsirm_cool_data", "rtsirm_warm_data"],
                        code.call("rmag.extract_mpms_data_dc", code.Name("measurements"), self.specimen.value)),
            code.assign(["rtsirm_warm_corrected", "rtsirm_cool_corrected"],
                        code.call("rmag.goethite_removal", code.Name("rtsirm_warm_data"), code.Name("rtsirm_cool_data"),
                                  **params, return_data=True)),
        ]

    # ----- layout -------------------------------------------------------------
    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.specimen, self.fit_range, self.poly_deg, self.reset_btn),
                         self.result, self.plot, self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- AC susceptibility
class AcSusceptibilityView:
    """In-phase and quadrature AC susceptibility against temperature: ``rockmag.plot_mpms_ac``.

    One experiment at a time (an MPMS run sweeps several frequencies); the
    controls are the function's ``phase`` and ``frequency`` arguments.
    """

    TYPE = "mpms_ac"
    PHASES = {"in phase": "in", "out of phase": "out", "both": "both"}

    def __init__(self, session):
        self.s = as_session(session)
        self.experiment = pn.widgets.Select(name="Experiment", options={}, width=420)
        self.phase = pn.widgets.RadioButtonGroup(name="Phase", options=self.PHASES, value="in", button_type="default",
                                                 margin=(24, 5, 0, 10))
        self.frequency = pn.widgets.Select(name="Frequency", options={"all": None}, value=None, width=140)
        self.plot = pn.pane.Bokeh(sizing_mode="stretch_width")
        self.code = code.CodePane()
        self.figure = None

        self.experiment.param.watch(self._on_experiment, "value")
        self.phase.param.watch(lambda e: self.refresh(), "value")
        self.frequency.param.watch(lambda e: self.refresh(), "value")
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")
        self.reset()

    # ----- state --------------------------------------------------------------
    def reset(self) -> None:
        exps = self.s.experiments_of(self.TYPE)
        options = {f"{r.specimen} · {r.experiment}": r.experiment for r in exps.itertuples()}
        before = self.experiment.value
        self.experiment.options = options
        own = [e for spec, e in zip(exps["specimen"], exps["experiment"]) if spec == self.s.specimen]
        self.experiment.value = own[0] if own else (next(iter(options.values())) if options else None)
        if self.experiment.value == before:
            self._on_experiment(None)

    def _on_experiment(self, event) -> None:
        exp = self.experiment.value
        if exp:
            exps = self.s.experiments
            self.s.specimen = exps.loc[exps["experiment"] == exp, "specimen"].iloc[0]
            freqs = sorted(self.data()["meas_freq"].dropna().unique().tolist())
            before = self.frequency.value
            self.frequency.options = {"all": None, **{f"{f:g} Hz": f for f in freqs}}
            if self.frequency.value not in freqs:
                self.frequency.value = None
            if self.frequency.value != before:
                return                                                    # the change refreshed
        self.refresh()

    def _follow_session(self, event) -> None:
        exps = self.s.experiments_of(self.TYPE)
        own = exps.loc[exps["specimen"] == event.new, "experiment"].tolist()
        if own and self.experiment.value not in own:
            self.experiment.value = own[0]

    # ----- the plot -----------------------------------------------------------
    def data(self):
        if not self.experiment.value or self.s.measurements is None:
            return None
        return rockmag.experiment_selection(self.s.measurements, self.experiment.value)

    def refresh(self) -> None:
        experiment = self.data()
        if experiment is None or experiment.empty or "meas_freq" not in experiment:
            self.figure = None
            self.plot.object = None
            self.code.set(preamble(self.s))
            return
        kwargs = dict(phase=self.phase.value, interactive=True, return_figure=True, show_plot=False)
        if self.frequency.value is not None:
            kwargs["frequency"] = self.frequency.value
        self.figure = rockmag.plot_mpms_ac(experiment, **kwargs)
        for fig in self.figure.children:
            style_figure(fig[0])
        self.plot.object = self.figure
        shown = {k: v for k, v in kwargs.items() if k not in ("return_figure", "show_plot")}
        self.code.set(preamble(self.s) + [
            code.assign("experiment", code.call("rmag.experiment_selection", code.Name("measurements"), self.experiment.value)),
            code.call("rmag.plot_mpms_ac", code.Name("experiment"), **shown),
        ])

    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.experiment, self.phase, self.frequency), self.plot, self.code.panel(),
                         sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- thermomagnetic curves
THERMOMAG_TYPES = ("chi_t", "ms_t")
"""High-temperature runs that share the heating/cooling-branch preprocessing: χ(T) and in-field M(T)."""
THERMOMAG_COLUMNS = ("susc_chi_mass", "susc_chi_volume", "susc_chi_qdr_mass", "magn_mass", "magn_volume", "magn_moment")
TEMP_UNITS = {"°C": "C", "K": "K"}


def thermomag_column(experiment) -> Optional[str]:
    """The measurement column a thermomagnetic run was recorded in (susceptibility before magnetization)."""
    for column in THERMOMAG_COLUMNS:
        if column in experiment and experiment[column].notna().any():
            return column
    return None


class ThermomagView:
    """The experiment picker and preprocessing controls shared by the χ–T and Curie views.

    The controls are the arguments of ``rockmag.prepare_thermomag_branches``
    that both ``plot_chi_T`` and ``curie_temperature_estimates`` pass through:
    ``temp_unit``, ``smooth_window`` (a width in that unit) and ``remove_holder``.
    """

    TYPE = "chi_t"
    LOW_TEMPERATURE = 320.0
    """A run staying below this (K) is an MPMS one and is shown in kelvin; furnace runs in °C."""

    def __init__(self, session):
        self.s = as_session(session)
        self.experiment = pn.widgets.Select(name="Experiment", options={}, width=380)
        self.temp_unit = pn.widgets.RadioButtonGroup(name="Temperature", options=TEMP_UNITS, value="C", width=90,
                                                     button_type="default", margin=(24, 5, 0, 10))
        self.smooth_window = pn.widgets.IntSlider(name="smoothing window (degrees)", start=0, end=50, step=1, value=0,
                                                  width=170)
        self.remove_holder = pn.widgets.Checkbox(name="subtract holder", value=True, width=130, margin=(28, 5, 0, 10))
        self.code = code.CodePane()
        self.figure = None
        self._quiet = False                                      # widgets being set by adopt(): hold the refresh

        self.experiment.param.watch(self._on_experiment, "value")
        self.temp_unit.param.watch(self._changed, "value")
        self.smooth_window.param.watch(self._changed, "value_throttled")
        self.remove_holder.param.watch(self._changed, "value")
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")

    # ----- state --------------------------------------------------------------
    def _experiments(self):
        return self.s.experiments[self.s.experiments["type"].isin(THERMOMAG_TYPES)]

    def reset(self) -> None:
        exps = self._experiments()
        options = {f"{r.specimen} · {r.experiment}": r.experiment for r in exps.itertuples()}
        before = self.experiment.value
        self.experiment.options = options
        own = exps.loc[exps["specimen"] == self.s.specimen, "experiment"].tolist()
        self.experiment.value = own[0] if own else (next(iter(options.values())) if options else None)
        if self.experiment.value == before:
            self._on_experiment(None)

    def _on_experiment(self, event) -> None:
        exp = self.experiment.value
        if exp:
            exps = self.s.experiments
            self.s.specimen = exps.loc[exps["experiment"] == exp, "specimen"].iloc[0]
            self._quiet = True
            try:
                self.adopt(self.data())
            finally:
                self._quiet = False
        self.refresh()

    def _changed(self, event) -> None:
        if not self._quiet:
            self.refresh()

    def adopt(self, experiment) -> None:
        """Defaults that follow the run: kelvin for a low-temperature (MPMS) one, °C for a furnace one."""
        temps = experiment["meas_temp"].dropna() if "meas_temp" in experiment else []
        self.temp_unit.value = "K" if len(temps) and temps.max() < self.LOW_TEMPERATURE else "C"

    def _follow_session(self, event) -> None:
        exps = self._experiments()
        own = exps.loc[exps["specimen"] == event.new, "experiment"].tolist()
        if own and self.experiment.value not in own:
            self.experiment.value = own[0]

    # ----- the data -----------------------------------------------------------
    def data(self):
        if not self.experiment.value or self.s.measurements is None:
            return None
        return rockmag.experiment_selection(self.s.measurements, self.experiment.value)

    def preprocessing(self, column: str) -> dict:
        """The keyword arguments both core functions take, in their signature order."""
        return dict(magnetic_column=column, temp_unit=self.temp_unit.value,
                    smooth_window=int(self.smooth_window.value), remove_holder=bool(self.remove_holder.value))

    def set_parameters(self, temp_unit=None, smooth_window=None, remove_holder=None) -> None:
        """Set the preprocessing controls from code (a notebook, a test) and refresh."""
        if temp_unit is not None:
            self.temp_unit.value = temp_unit
        if smooth_window is not None:
            self.smooth_window.value = smooth_window
        if remove_holder is not None:
            self.remove_holder.value = remove_holder
        self.refresh()

    def controls(self) -> pn.Row:
        return pn.Row(self.experiment, self.temp_unit, self.smooth_window, self.remove_holder)

    def refresh(self) -> None:                                                  # pragma: no cover - subclasses
        raise NotImplementedError


class ChiTView(ThermomagView):
    """A thermomagnetic curve with its derivative and reciprocal: ``rockmag.plot_chi_T``.

    Also plots the in-field M(T) runs (LP-MST) since the function only needs
    to be told the column; the y axis is labelled from it.
    """

    def __init__(self, session):
        super().__init__(session)
        self.derivative = pn.widgets.Checkbox(name="derivative", value=True, margin=(28, 5, 0, 10))
        self.inverse = pn.widgets.Checkbox(name="reciprocal", value=False, margin=(28, 5, 0, 10))
        self.plot = pn.pane.Bokeh(sizing_mode="stretch_width")
        self.derivative.param.watch(self._changed, "value")
        self.inverse.param.watch(self._changed, "value")
        self.reset()

    def refresh(self) -> None:
        experiment = self.data()
        column = thermomag_column(experiment) if experiment is not None else None
        if column is None:
            self.figure = None
            self.plot.object = None
            self.code.set(preamble(self.s))
            return
        kwargs = dict(**self.preprocessing(column), plot_derivative=bool(self.derivative.value),
                      plot_inverse=bool(self.inverse.value), interactive=True)
        figs = list(rockmag.plot_chi_T(experiment, **kwargs, return_figure=True, figsize=(6, 4), show_plot=False))
        for fig in figs:
            style_figure(fig)
        rows = [[figs[0]]] + ([figs[1:]] if len(figs) > 1 else [])
        self.figure = gridplot(rows, sizing_mode="stretch_width", toolbar_location="right")
        self.plot.object = self.figure
        shown = kwargs
        self.code.set(preamble(self.s) + [
            code.assign("experiment", code.call("rmag.experiment_selection", code.Name("measurements"), self.experiment.value)),
            code.call("rmag.plot_chi_T", code.Name("experiment"), **shown),
        ])

    def panel(self) -> pn.Column:
        row = self.controls()
        row.extend([self.derivative, self.inverse])
        return pn.Column(row, self.plot, self.code.panel(), sizing_mode="stretch_width")


CURIE_METHODS = {"inflection": "inflection (dM/dT minimum)", "max_curvature": "maximum curvature",
                 "two_tangent": "two tangents", "inverse_susceptibility": "Curie–Weiss 1/χ",
                 "landau": "Landau fit", "ms_squared_extrapolation": "Ms² extrapolation"}
"""Every estimator ``curie_temperature_estimates`` knows, with the label the view shows."""
CURIE_DEFAULTS = {"susceptibility": ("inflection", "max_curvature", "inverse_susceptibility"),
                  "magnetization": ("inflection", "max_curvature", "two_tangent", "landau")}
"""The function's own default method sets per data type; Ms² extrapolation is magnetization-only."""
BRANCHES = ("heating", "cooling")


class CurieView(ThermomagView):
    """Curie-temperature estimates by several methods: ``rockmag.curie_temperature_estimates``
    tabulated, and ``rockmag.plot_curie_estimates`` showing each construction.
    """

    def __init__(self, session):
        super().__init__(session)
        self.methods = pn.widgets.CheckBoxGroup(name="Methods", options=dict(CURIE_METHODS), value=[], inline=True,
                                                margin=(8, 10, 0, 10))
        self.branches = pn.widgets.CheckBoxGroup(name="Branches", options=list(BRANCHES), value=list(BRANCHES),
                                                 inline=True, margin=(8, 10, 0, 10))
        self.table = pn.pane.HTML(sizing_mode="stretch_width")
        self.plot = pn.pane.Matplotlib(dpi=100, tight=True, sizing_mode="stretch_width")
        self.estimates = None
        self.data_type = None
        self.methods.param.watch(self._changed, "value")
        self.branches.param.watch(self._changed, "value")
        self.reset()

    def adopt(self, experiment) -> None:
        """Switching between χ(T) and M(T) data changes the methods on offer and picks the function's defaults."""
        super().adopt(experiment)
        column = thermomag_column(experiment)
        data_type = rockmag._resolve_thermomag_data_type(None, column) if column else None
        if data_type is not None and data_type != self.data_type:
            self.data_type = data_type
            self.methods.options = {label: m for m, label in CURIE_METHODS.items()
                                    if data_type == "magnetization" or m != "ms_squared_extrapolation"}
            self.methods.value = list(CURIE_DEFAULTS[data_type])

    def set_methods(self, methods) -> None:
        self.methods.value = list(methods)

    def refresh(self) -> None:
        experiment = self.data()
        column = thermomag_column(experiment) if experiment is not None else None
        methods, branches = list(self.methods.value), list(self.branches.value)
        if column is None or not methods or not branches:
            self.estimates = None
            self.figure = None
            self.plot.object = None
            self.table.object = muted("pick at least one method and one branch") if column else ""
            self.code.set(preamble(self.s))
            return
        kwargs = dict(methods=methods, **self.preprocessing(column), branches=branches)
        try:
            self.estimates = rockmag.curie_temperature_estimates(experiment, **kwargs)
            self.figure, _ = rockmag.plot_curie_estimates(experiment, **kwargs, figsize=(9, 3.2 * self._panels(methods)),
                                                          return_figure=True)
        except (ValueError, RuntimeError, np.linalg.LinAlgError) as ex:
            self.estimates = None
            self.figure = None
            self.plot.object = None
            self.table.object = f'<div style="color:#b00">The estimate failed: {ex}</div>'
            self.code.set(preamble(self.s))
            return
        self.plot.object = self.figure
        self.table.object = self._table_html()
        self.code.set(preamble(self.s) + [
            code.assign("experiment", code.call("rmag.experiment_selection", code.Name("measurements"), self.experiment.value)),
            code.assign("estimates", code.call("rmag.curie_temperature_estimates", code.Name("experiment"), **kwargs)),
            code.call("rmag.plot_curie_estimates", code.Name("experiment"), **kwargs),
        ])

    @staticmethod
    def _panels(methods) -> int:
        return 1 + int(bool({"inflection", "max_curvature"} & set(methods))) + int("inverse_susceptibility" in methods)

    def _table_html(self) -> str:
        unit = "°C" if self.temp_unit.value == "C" else "K"
        rows = []
        for r in self.estimates.itertuples():
            if np.isfinite(r.curie_temp):
                value = f"{r.curie_temp:.1f}" + (f" ± {r.curie_temp_stderr:.1f}" if np.isfinite(r.curie_temp_stderr) else "")
            else:
                value = "—"
            rows.append(f"<tr><td>{r.branch}</td><td>{CURIE_METHODS.get(r.method, r.method)}</td>"
                        f'<td style="text-align:right;font-variant-numeric:tabular-nums">{value}</td>'
                        f'<td style="{MUTED_STYLE}">{r.notes}</td></tr>')
        head = (f"<tr><th>branch</th><th>method</th><th style='text-align:right'>T<sub>C</sub> ({unit})</th>"
                f"<th>note</th></tr>")
        return ('<table style="border-collapse:collapse;font-size:13px;margin:6px 0">'
                '<style>.curie td,.curie th{padding:3px 12px 3px 0;vertical-align:top;border-bottom:1px solid #eee}</style>'
                f'<tbody class="curie">{head}{"".join(rows)}</tbody></table>')

    def panel(self) -> pn.Column:
        label = lambda text: pn.pane.HTML(f'<div style="{SECTION_STYLE}">{text}</div>', width=80, margin=(12, 0, 0, 0))
        return pn.Column(self.controls(), pn.Row(label("Methods"), self.methods), pn.Row(label("Branches"), self.branches),
                         self.table, self.plot, self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- hysteresis
MAGNETIZATION_COLUMNS = {"magn_mass": "Am²/kg", "magn_volume": "A/m", "magn_moment": "Am²"}
"""The MagIC magnetization columns a loop may be recorded in, with the unit each implies."""
HYST_FIELD = "meas_field_dc"
CENTERING = {"legacy": "legacy", "iterative": "iterative"}
HYST_PARAMETERS = (("Ms", "M<sub>s</sub>", "mag"), ("Mr", "M<sub>r</sub>", "mag"), ("Bc", "B<sub>c</sub>", "field"),
                   ("Brh", "B<sub>rh</sub>", "field"), ("sigma", "σ", ""), ("chi_HF", "χ<sub>HF</sub>", "chi"))
"""The characteristic parameters ``process_hyst_loop`` returns, in the order shown, and how each is formatted."""
HYST_QUALITY = (("Q", "Q"), ("Qf", "Q<sub>f</sub>"), ("FNL", "F<sub>NL</sub>"), ("FNL60", "F<sub>NL60</sub>"),
                ("FNL70", "F<sub>NL70</sub>"), ("FNL80", "F<sub>NL80</sub>"), ("Fnl_lin", "F<sub>nl/lin</sub>"))
"""The Jackson & Solheid (2010) data-quality statistics, in the order shown."""


def magnetization_column(experiment) -> Optional[str]:
    """The magnetization column an experiment was recorded in (mass-normalised first)."""
    for column in MAGNETIZATION_COLUMNS:
        if column in experiment and experiment[column].notna().any():
            return column
    return None


class HysteresisView:
    """One hysteresis loop through the IRM decision tree: ``rockmag.process_hyst_loop``.

    The loop is gridded, centred, drift-corrected and slope-corrected, with
    the raw and corrected loops and the Mrh/Mih/Me curves overlaid in the
    function's own figure. The controls are its arguments: the centering
    protocol, forcing the non-linear approach-to-saturation fit, and the two
    overrides of the decision tree's early exits (open and linear loops).
    """

    TYPE = "hys"

    def __init__(self, session):
        self.s = as_session(session)
        self.experiment = pn.widgets.Select(name="Experiment", options={}, width=340)
        self.centering = pn.widgets.RadioButtonGroup(name="Centering", options=CENTERING, value="legacy", width=150,
                                                     button_type="default", margin=(24, 5, 0, 10))
        self.nl_fit = pn.widgets.Checkbox(name="non-linear HF fit", value=False, width=130, margin=(28, 5, 0, 10))
        self.fit_open = pn.widgets.Checkbox(name="fit open loop", value=False, width=110, margin=(28, 5, 0, 10))
        self.fit_linear = pn.widgets.Checkbox(name="fit linear loop", value=False, width=110, margin=(28, 5, 0, 10))
        self.result = pn.pane.HTML("", sizing_mode="stretch_width")
        self.quality = pn.pane.HTML("", width=330, margin=(10, 0, 0, 20))
        self.plot = pn.pane.Bokeh()
        self.code = code.CodePane()
        self.figure = None
        self.results = None                       # the dict process_hyst_loop returned for what is plotted

        self.experiment.param.watch(self._on_experiment, "value")
        for w in (self.centering, self.nl_fit, self.fit_open, self.fit_linear):
            w.param.watch(lambda e: self.refresh(), "value")
        self.s.param.watch(lambda e: self.reset(), "directory")
        self.s.param.watch(self._follow_session, "specimen")
        self.reset()

    # ----- state --------------------------------------------------------------
    def _experiments(self):
        return self.s.experiments_of(self.TYPE)

    def reset(self) -> None:
        exps = self._experiments()
        options = {f"{r.specimen} · {r.experiment}": r.experiment for r in exps.itertuples()}
        before = self.experiment.value
        self.experiment.options = options
        own = exps.loc[exps["specimen"] == self.s.specimen, "experiment"].tolist()
        self.experiment.value = own[0] if own else (next(iter(options.values())) if options else None)
        if self.experiment.value == before:
            self._on_experiment(None)

    def _on_experiment(self, event) -> None:
        exp = self.experiment.value
        if exp:
            exps = self.s.experiments
            self.s.specimen = exps.loc[exps["experiment"] == exp, "specimen"].iloc[0]
        self.refresh()

    def _follow_session(self, event) -> None:
        exps = self._experiments()
        own = exps.loc[exps["specimen"] == event.new, "experiment"].tolist()
        if own and self.experiment.value not in own:
            self.experiment.value = own[0]

    def set_parameters(self, centering_protocol=None, NL_fit=None, fit_open_loop=None, fit_linear_loop=None) -> None:
        """Set the controls from code (a notebook, a test) and refresh."""
        if centering_protocol is not None:
            self.centering.value = centering_protocol
        if NL_fit is not None:
            self.nl_fit.value = NL_fit
        if fit_open_loop is not None:
            self.fit_open.value = fit_open_loop
        if fit_linear_loop is not None:
            self.fit_linear.value = fit_linear_loop
        self.refresh()

    # ----- the loop -----------------------------------------------------------
    def data(self):
        if not self.experiment.value or self.s.measurements is None:
            return None
        return rockmag.experiment_selection(self.s.measurements, self.experiment.value)

    def options(self) -> dict:
        """The keyword arguments the controls stand for; only those off their defaults, in signature order."""
        chosen = dict(NL_fit=bool(self.nl_fit.value), centering_protocol=self.centering.value,
                      fit_open_loop=bool(self.fit_open.value), fit_linear_loop=bool(self.fit_linear.value))
        defaults = dict(NL_fit=False, centering_protocol="legacy", fit_open_loop=False, fit_linear_loop=False)
        return {k: v for k, v in chosen.items() if v != defaults[k]}

    def refresh(self) -> None:
        experiment = self.data()
        column = magnetization_column(experiment) if experiment is not None else None
        if column is None or HYST_FIELD not in experiment:
            self.results = self.figure = None
            self.plot.object = None
            self.result.object = muted("no hysteresis loop in this directory") if experiment is None else \
                muted("this experiment has no field and magnetization columns to process")
            self.quality.object = ""
            self.code.set(preamble(self.s))
            return
        options = self.options()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.results = rockmag.process_hyst_loop(experiment[HYST_FIELD], experiment[column], self.s.specimen,
                                                     show_results_table=False, show_plot=False, **options)
        self.figure = self.results["plot"]
        if self.figure is not None:
            style_figure(self.figure)
            self.figure.legend.location = "top_left"                     # the loop's empty corner
            self.figure.legend.label_text_font_size = "9pt"
        self.plot.object = self.figure
        self.result.object = self._result_html(MAGNETIZATION_COLUMNS[column], caught)
        self.quality.object = self._quality_html()
        self.code.set(preamble(self.s) + [
            code.assign("experiment", code.call("rmag.experiment_selection", code.Name("measurements"), self.experiment.value)),
            code.assign("results", code.call("rmag.process_hyst_loop", code.Name(f"experiment['{HYST_FIELD}']"),
                                             code.Name(f"experiment['{column}']"), self.s.specimen, **options)),
        ])

    # ----- the results --------------------------------------------------------
    @staticmethod
    def _value(key, value, unit) -> str:
        if value is None or not np.isfinite(value):
            return "—"
        if key == "field":
            return f"{1e3 * value:.1f} mT"
        if key == "mag":
            return f"{value:.4g} {unit}"
        if key == "chi":
            return f"{value:.3g} m³/kg"
        return f"{value:.3f}"

    def _result_html(self, unit, caught) -> str:
        r = self.results
        items = [(label, self._value(kind, r.get(name), unit)) for name, label, kind in HYST_PARAMETERS]
        if all(np.isfinite(r.get(k, np.nan)) for k in ("Mr", "Ms")) and r["Ms"]:
            items.insert(2, ("M<sub>r</sub>/M<sub>s</sub>", f"{r['Mr'] / r['Ms']:.3f}"))
        html = kpi(items)
        if r["loop_is_linear"]:
            html += muted("the loop is statistically linear (paramagnetic or diamagnetic material dominates): only "
                          "χ<sub>HF</sub> from the whole-loop regression is reported — tick <i>fit linear loop</i> "
                          "to process it anyway")
        elif r["loop_is_closed"] is False and not r["loop_is_linear"] and "Ms" in r and not np.isfinite(r["Ms"]):
            html += muted("the loop remains open at the highest fields, so M<sub>s</sub> and χ<sub>HF</sub> cannot be "
                          "separated: M<sub>r</sub>, B<sub>rh</sub> and the quality statistics are reported — tick "
                          "<i>fit open loop</i> if the loop looks closed and drift is tripping the test")
        for w in caught:
            if issubclass(w.category, RuntimeWarning) and "remains open" not in str(w.message):
                html += muted(str(w.message))
        return html

    def _quality_html(self) -> str:
        r = self.results
        rows = []
        for name, label in HYST_QUALITY:
            value = r.get(name)
            shown = "—" if value is None or not np.isfinite(value) else f"{value:.2f}"
            rows.append(f'<tr><td>{label}</td><td style="text-align:right;font-variant-numeric:tabular-nums">{shown}</td></tr>')
        flags = []
        for name, yes, no in (("loop_is_linear", "linear", "not linear"), ("loop_is_closed", "closed", "open"),
                              ("loop_is_saturated", "saturated", "not saturated")):
            if r.get(name) is not None:
                flags.append(yes if r[name] else no)
        if r.get("loop_is_saturated") is not None and r.get("Ms") is not None and np.isfinite(r.get("Ms", np.nan)):
            flags.append("linear high-field fit" if r["loop_is_saturated"] else "non-linear high-field fit")
        if r.get("measured_descending_first") is not None:
            flags.append("measured from " + ("positive" if r["measured_descending_first"] else "negative") + " saturation")
        return ('<table style="border-collapse:collapse;font-size:13px">'
                '<style>.hystq td{padding:3px 12px 3px 0;border-bottom:1px solid #eee}</style>'
                f'<tbody class="hystq"><tr><th style="text-align:left" colspan="2">Data quality</th></tr>{"".join(rows)}'
                f'</tbody></table><div style="{MUTED_STYLE};margin-top:8px">{" · ".join(flags)}</div>')

    # ----- layout -------------------------------------------------------------
    def panel(self) -> pn.Column:
        return pn.Column(pn.Row(self.experiment, self.centering, self.nl_fit, self.fit_open, self.fit_linear),
                         self.result, pn.Row(self.plot, self.quality), self.code.panel(), sizing_mode="stretch_width")


# ----------------------------------------------------------------------------- the set of views
TABS = (("mpms_dc", "MPMS DC", MpmsDcView), ("verwey", "Verwey", VerweyView), ("goethite", "Goethite", GoethiteView),
        ("mpms_ac", "AC susceptibility", AcSusceptibilityView), ("chi_t", "χ–T", ChiTView), ("curie", "Curie", CurieView),
        ("hys", "Hysteresis", HysteresisView))
"""``(key, tab label, view class)`` in tab order. Experiment types without a view are listed in the index only."""
