"""
Tests for the Rock Magnetism application: the experiment index, the session,
and the views against the shipped examples (MagIC contribution 20427,
``data_files/3_0/RMB_oxyhydroxides``, for the low-temperature and
thermomagnetic views; 20213, ``data_files/3_0/ECMB_rockmag``, for the
hysteresis and backfield ones; ``data_files/3_0/FORC_example`` for the FORC
one) and synthetic curves with known answers. Run with the apps environment::

    pytest programs/pmagpy_rockmag/test_app.py -q
"""
import os
import shutil
import sys
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import brentq
from scipy.special import erf

pn = pytest.importorskip("panel")

from pmagpy import forc, rockmag  # noqa: E402
from pmagpy_rockmag import app, results, session as rs  # noqa: E402
from pmagpy_rockmag.views import (AcSusceptibilityView, BackfieldView, ChiTView, CurieView, ForcView,  # noqa: E402
                                  GoethiteView, HysteresisView, MpmsDcView, UnmixingView, VerweyView)

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pmagpy", "test"))
from test_forc import write_micromag  # noqa: E402  the synthetic MicroMag run with a known FORC distribution

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EXAMPLE = os.path.join(REPO, "data_files", "3_0", "RMB_oxyhydroxides")
FOUR_CURVES = "ferroxyhyte_Princeton-1985-M1-1"
TWO_CURVES = "lepidocrocite_AA 17531_1"                     # FC and ZFC only


@pytest.fixture(scope="module")
def session():
    return rs.Session(EXAMPLE)


def magnetite_curve(t_v=120.0, loss=0.3, width=4.0):
    """An FC warming curve: a linear background plus a `loss` Am²/kg step down at `t_v`."""
    temps = np.arange(10.0, 301.0, 2.0)
    mags = 1.0 - 0.001 * temps - 1e-6 * temps ** 2 + loss * (1 - np.tanh((temps - t_v) / width)) / 2
    return pd.DataFrame({"specimen": "syn", "method_codes": "LP-FC", "experiment": "syn_FC",
                         "meas_temp": temps, "magn_mass": mags})


class TestExperimentIndex:
    def test_types_are_recognised_from_whole_method_codes(self):
        m = pd.DataFrame({"specimen": ["a", "a", "a", "b", "b", "c"],
                          "method_codes": ["LP-FC", "LP-CW-SIRM:LP-MW", "LP-X:LP-X-T:LP-X-F", "LP-X-T", "LP-HYS", "LP-DIR-AF"],
                          "experiment": ["e1", "e2", "e3", "e4", "e5", "e6"]})
        index = rs.experiment_index(m)
        assert list(index["type"]) == ["mpms_dc", "mpms_dc", "mpms_ac", "chi_t", "hys", ""]
        assert list(index["n"]) == [1] * 6
        assert rs.experiment_index(None).empty and list(rs.experiment_index(None).columns) == list(index.columns)

    def test_a_prefix_code_is_not_matched_as_a_substring(self):
        t = rs.TYPES_BY_KEY["mpms_dc"]
        assert t.matches("LP-CW-SIRM:LP-MC") and not t.matches("LP-FC-X") and not t.matches("XLP-FC")
        assert rs.TYPES_BY_KEY["hys"].matches("LP-HYS-T")


class TestSession:
    def test_the_example_loads_with_its_types_counted(self, session):
        assert session.directory == EXAMPLE
        assert session.status == "9 specimens · 40 experiments · 4 experiment types"
        counts = {t.key: (n_spec, n_exp) for t, n_spec, n_exp in session.type_counts()}
        assert counts == {"mpms_dc": (8, 30), "mpms_ac": (5, 5), "chi_t": (2, 2), "ms_t": (3, 3)}
        assert session.unclaimed().empty
        assert session.specimens("mpms_dc")[0] == FOUR_CURVES and TWO_CURVES in session.specimens("mpms_dc")
        assert session.specimen == session.specimens()[0]

    def test_a_directory_without_measurements_is_refused_with_a_reason(self, tmp_path):
        s = rs.Session(str(tmp_path))
        assert s.measurements is None and "no measurements.txt" in s.status
        assert not s.load(str(tmp_path))

    def test_a_session_from_a_dataframe_needs_no_directory(self, session):
        s = rs.as_session(session.measurements)
        assert s.directory == "" and len(s.experiments) == 40
        assert rs.as_session(session) is session


class TestMpmsDcView:
    def test_the_view_plots_the_four_curves_and_writes_the_call_that_made_them(self, session):
        view = MpmsDcView(session)
        assert view.specimen.value == FOUR_CURVES
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [0, 1], [1, 0], [1, 1]]
        assert "FC <b>59</b>" in view.series.object and "RTSIRM warming <b>59</b>" in view.series.object
        lines = view.code.text.splitlines()
        assert lines[0] == "import pmagpy.rockmag as rmag"
        assert f"contribution = cb.Contribution('{EXAMPLE}')" in lines
        assert ("fc_data, zfc_data, rtsirm_cool_data, rtsirm_warm_data = "
                f"rmag.extract_mpms_data_dc(measurements, '{FOUR_CURVES}')") in lines
        assert "    plot_derivative=True," in lines and "drop_first" not in view.code.text
        assert "show_plot" not in view.code.text                       # notebook defaults, not the app's plumbing

    def test_the_code_runs_and_reproduces_the_figure(self, session):
        view = MpmsDcView(session)
        view.drop_first.value = True
        namespace = {}
        exec(view.code.text, namespace)                                 # cb.Contribution reads the directory again
        assert len(namespace["fc_data"]) == 59
        assert "drop_first=True" in view.code.text

    def test_a_specimen_with_only_fc_and_zfc_gets_its_derivative_below_not_beside(self, session):
        view = MpmsDcView(session)
        view.specimen.value = TWO_CURVES
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [1, 0]]
        assert session.specimen == TWO_CURVES                           # the choice is shared with the other views
        assert "RTSIRM" not in view.series.object
        view.derivative.value = False
        assert [pos for _, *pos in view.figure.children] == [[0, 0]]

    def test_the_view_follows_the_session_only_to_specimens_it_can_plot(self, session):
        view = MpmsDcView(session)
        session.specimen = FOUR_CURVES
        assert view.specimen.value == FOUR_CURVES
        session.specimen = "ferroxyhyte_Princeton-1985-M1-2"            # χ–T only
        assert view.specimen.value == FOUR_CURVES

    def test_the_view_renders_from_a_dataframe_as_in_a_notebook(self, session):
        view = MpmsDcView(session.measurements)
        assert view.figure is not None
        assert "# measurements: the DataFrame this view was given" in view.code.text
        assert isinstance(view.panel(), pn.Column)

    def test_nothing_to_plot_is_said_not_raised(self):
        m = pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-HYS"], "experiment": ["e"]})
        view = MpmsDcView(m)
        assert view.figure is None and "no FC, ZFC or RTSIRM" in view.series.object


class TestVerweyView:
    def test_a_known_transition_is_recovered_and_the_code_reproduces_it(self):
        view = VerweyView(magnetite_curve(t_v=120.0, loss=0.3))
        t_v, loss, r2 = view.estimate
        assert abs(t_v - 120.0) < 0.5 and abs(loss - 0.3) < 0.01
        assert view.method.options == {"FC": "LP-FC"}                    # no ZFC curve to offer
        assert "120.0 K" in view.result.object and "no clear loss" not in view.result.object
        namespace = {"rmag": rockmag, "measurements": magnetite_curve()}
        exec("\n".join(view.code.text.splitlines()[3:]), namespace)     # past the preamble: the calls themselves
        assert abs(namespace["verwey_temperature"] - t_v) < 1e-6
        assert "t_range_background_min=60," in view.code.text and "poly_deg=3," in view.code.text

    def test_the_sliders_are_the_functions_arguments(self):
        view = VerweyView(magnetite_curve())
        view.set_parameters(background=(20, 280), excluded=(100, 140), poly_deg=1)
        assert view.parameters() == dict(t_range_background_min=20, t_range_background_max=280,
                                         excluded_t_min=100, excluded_t_max=140, poly_deg=1)
        assert abs(view.estimate[0] - 120.0) < 0.5
        view.set_parameters(background=(200, 250), excluded=(210, 240))  # the transition is outside the fit range
        assert abs(view.estimate[0] - 120.0) > 50 and "no clear loss" in view.result.object
        view.set_parameters(background=(60, 62), excluded=(60, 62))      # too few points to fit
        assert view.estimate is None and "fit failed" in view.result.object

    def test_the_example_has_no_magnetite_and_says_so_for_every_curve(self, session):
        view = VerweyView(session)
        assert view.specimen.value == FOUR_CURVES and view.method.options == {"FC": "LP-FC", "ZFC": "LP-ZFC"}
        for method in ("LP-FC", "LP-ZFC"):
            view.method.value = method
            assert view.estimate is not None and view.estimate[1] < 0.01 and "no clear loss" in view.result.object
        assert "zfc_data['meas_temp']" in view.code.text
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [0, 1]]

    def test_a_specimen_with_one_curve_only_offers_that_curve(self, session):
        view = VerweyView(session)
        view.method.value = "LP-ZFC"
        view.specimen.value = TWO_CURVES                                 # FC and ZFC, no RTSIRM: both offered
        assert view.method.options == {"FC": "LP-FC", "ZFC": "LP-ZFC"} and view.method.value == "LP-ZFC"
        fc_only = pd.DataFrame({"specimen": ["a", "b"], "method_codes": ["LP-FC", "LP-ZFC"], "experiment": ["e1", "e2"],
                                "meas_temp": [[10.0, 20.0]] * 2, "magn_mass": [[1.0, 0.9]] * 2}).explode(["meas_temp", "magn_mass"])
        view = VerweyView(fc_only)
        assert view.specimen.options == ["a", "b"] and view.method.options == {"FC": "LP-FC"}
        view.specimen.value = "b"
        assert view.method.options == {"ZFC": "LP-ZFC"} and view.method.value == "LP-ZFC"


class TestGoethiteView:
    def test_the_view_offers_specimens_with_both_rtsirm_curves_and_writes_the_call(self, session):
        view = GoethiteView(session)
        assert view.specimen.value == FOUR_CURVES and TWO_CURVES not in view.specimen.options
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [0, 1], [1, 0], [1, 1]]
        assert set(view.removal) >= {"fit", "warm_corrected", "cool_corrected"}
        assert "warming remanence at 10 K" in view.result.object and "removed" in view.result.object
        last = view.code.text.splitlines()
        assert "rtsirm_warm_corrected, rtsirm_cool_corrected = rmag.goethite_removal(" in last
        assert "    t_min=150," in last and "    poly_deg=2," in last and "    return_data=True," in last
        namespace = {"rmag": rockmag, "measurements": session.measurements}
        exec("\n".join(last[5:]), namespace)                             # runs the matplotlib function, no window
        assert len(namespace["rtsirm_warm_corrected"]) == 59

    def test_parameters_reach_the_function_and_a_bad_range_is_reported(self, session):
        view = GoethiteView(session)
        view.set_parameters(fit_range=(200, 280), poly_deg=1)
        assert view.parameters() == dict(t_min=200, t_max=280, poly_deg=1)
        assert len(view.removal["fit"].coefficients) == 2
        view.set_parameters(fit_range=(289, 291))
        assert view.removal is None and "fit failed" in view.result.object
        view.set_parameters(**{"fit_range": (150, 290), "poly_deg": 2})
        assert view.removal is not None

    def test_nothing_to_remove_is_said_not_raised(self):
        m = pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                          "meas_temp": [10.0], "magn_mass": [1.0]})
        view = GoethiteView(m)
        assert view.specimen.options == [] and view.figure is None and "no RTSIRM" in view.result.object


class TestAcSusceptibilityView:
    def test_the_view_plots_one_experiment_with_the_functions_phase_and_frequency(self, session):
        session.specimen = FOUR_CURVES
        view = AcSusceptibilityView(session)
        assert view.experiment.value == "IRM-OldBlue-LP-X:LP-X-T:LP-X-F-9652"      # the session specimen's run
        assert list(view.frequency.options) == ["all", "1 Hz", "5.62 Hz", "31.59 Hz", "177.56 Hz", "997.34 Hz"]
        assert [pos for _, *pos in view.figure.children] == [[0, 0]]
        assert view.code.text.splitlines()[-2:] == [
            "experiment = rmag.experiment_selection(measurements, 'IRM-OldBlue-LP-X:LP-X-T:LP-X-F-9652')",
            "rmag.plot_mpms_ac(experiment, phase='in', interactive=True)"]
        view.phase.value = "both"
        view.frequency.value = 997.34
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [0, 1]]
        assert view.code.text.endswith("rmag.plot_mpms_ac(experiment, phase='both', interactive=True, frequency=997.34)")
        namespace = {"rmag": rockmag, "measurements": session.measurements}
        exec("\n".join(view.code.text.splitlines()[5:-1]), namespace)
        assert len(namespace["experiment"]) == 150

    def test_changing_experiment_follows_the_specimen_and_reoffers_frequencies(self, session):
        view = AcSusceptibilityView(session)
        view.frequency.value = 997.34
        session.specimen = "goethite_AA 19496-1"                        # a run with a different frequency set
        assert view.experiment.value == "IRM-BigRed-LP-X:LP-X-T:LP-X-F-9645"
        assert view.frequency.value == 997.34 and "3.16 Hz" in view.frequency.options
        view.experiment.value = "IRM-OldBlue-LP-X:LP-X-T:LP-X-F-9654"
        assert session.specimen == "lepidocrocite_Pfizer_1"
        session.specimen = TWO_CURVES                                    # no AC run: the view keeps its own
        assert session.specimen == TWO_CURVES and view.experiment.value == "IRM-OldBlue-LP-X:LP-X-T:LP-X-F-9654"

    def test_nothing_to_plot_is_said_not_raised(self):
        m = pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                          "meas_temp": [10.0], "magn_mass": [1.0]})
        view = AcSusceptibilityView(m)
        assert view.experiment.options == {} and view.figure is None


CHI_T = "IRM-KappaF-LP-X-T-3413"                             # ferroxyhyte_Princeton-1985-M1-2, 297–976 K
IN_FIELD_MT = "ferroxyhyte_Princeton-1985-M1-1-LP-MST-DC-9652"  # an MPMS in-field run, 10–300 K, magn_mass


def ms_curve(tc_c=580.0, beta=0.5):
    """A heating + cooling mean-field M(T) experiment with a known Curie temperature and a holder offset."""
    tc = tc_c + 273.15
    temps = np.arange(300.0, 973.0, 3.0)
    mags = np.where(temps < tc, np.clip(1 - temps / tc, 0, None) ** beta, 0.0) + 0.02
    heating = pd.DataFrame({"meas_temp": temps, "magn_mass": mags})
    cooling = pd.DataFrame({"meas_temp": temps[::-1], "magn_mass": 0.9 * mags[::-1] + 0.002})
    experiment = pd.concat([heating, cooling], ignore_index=True)
    experiment["specimen"], experiment["experiment"], experiment["method_codes"] = "syn", "syn_MST", "LP-MST"
    return experiment


class TestChiTView:
    def test_the_view_plots_a_susceptibility_run_with_the_functions_options(self, session):
        session.specimen = "ferroxyhyte_Princeton-1985-M1-2"
        view = ChiTView(session)
        assert view.experiment.value == CHI_T
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [1, 0]]          # curve over its derivative
        view.inverse.value = True
        assert [pos for _, *pos in view.figure.children] == [[0, 0], [1, 0], [1, 1]]
        assert [f[0].yaxis.axis_label for f in view.figure.children] == ["χ (m³ kg⁻¹)", "dχ/dT", "1/χ"]
        view.set_parameters(temp_unit="K", smooth_window=10, remove_holder=False)
        lines = view.code.text.splitlines()
        assert lines[5] == f"experiment = rmag.experiment_selection(measurements, '{CHI_T}')"
        assert lines[6:] == ["rmag.plot_chi_T(", "    experiment,", "    magnetic_column='susc_chi_mass',",
                             "    temp_unit='K',", "    smooth_window=10,", "    remove_holder=False,",
                             "    plot_derivative=True,", "    plot_inverse=True,", "    interactive=True,", ")"]
        namespace = {"rmag": rockmag, "measurements": session.measurements}
        exec("\n".join(lines[5:]) .replace("interactive=True,", "interactive=True, show_plot=False,"), namespace)

    def test_an_in_field_magnetization_run_is_plotted_from_its_own_column(self, session):
        session.specimen = FOUR_CURVES
        view = ChiTView(session)
        assert view.experiment.value == IN_FIELD_MT
        assert "magnetic_column='magn_mass'," in view.code.text
        assert [f[0].yaxis.axis_label for f in view.figure.children] == ["M (Am² kg⁻¹)", "dM/dT"]
        assert view.temp_unit.value == "K"                                       # a 10–300 K run is shown in kelvin
        view.experiment.value = CHI_T
        assert view.temp_unit.value == "C" and "temp_unit='C'," in view.code.text

    def test_a_dataframe_and_nothing_to_plot(self):
        view = ChiTView(ms_curve())
        assert view.experiment.value == "syn_MST" and len(view.figure.children) == 2
        assert view.code.text.splitlines()[3] == "# measurements: the DataFrame this view was given"
        empty = ChiTView(pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                                       "meas_temp": [10.0], "magn_mass": [1.0]}))
        assert empty.experiment.options == {} and empty.figure is None


class TestCurieView:
    def test_a_known_curie_temperature_is_recovered_by_every_magnetization_method(self):
        view = CurieView(ms_curve(tc_c=580.0))
        assert view.data_type == "magnetization"
        assert view.methods.value == ["inflection", "max_curvature", "two_tangent", "landau"]   # the function's default
        assert "Ms² extrapolation" in view.methods.options and "Curie–Weiss 1/χ" in view.methods.options
        view.set_methods(["inflection", "max_curvature", "two_tangent", "landau", "ms_squared_extrapolation"])
        heating = view.estimates[view.estimates["branch"] == "heating"].set_index("method")["curie_temp"]
        assert len(heating) == 5 and np.isfinite(heating).all()
        assert (abs(heating - 580.0) < 5).all(), heating
        assert len(view.figure.axes) == 2                                        # curve + derivative panel
        assert "580" in view.table.object or "58" in view.table.object
        lines = view.code.text.splitlines()
        assert lines[4] == "experiment = rmag.experiment_selection(measurements, 'syn_MST')"
        assert lines[5:9] == ["estimates = rmag.curie_temperature_estimates(", "    experiment,",
                              "    methods=['inflection', 'max_curvature', 'two_tangent', 'landau', 'ms_squared_extrapolation'],",
                              "    magnetic_column='magn_mass',"]
        namespace = {"rmag": rockmag, "measurements": ms_curve()}
        plot_line = lines.index("rmag.plot_curie_estimates(")
        exec("\n".join(lines[4:plot_line]), namespace)                             # the estimate call only
        assert len(namespace["estimates"]) == 10

    def test_susceptibility_offers_the_curie_weiss_method_and_switches_defaults(self, session):
        session.specimen = FOUR_CURVES                                          # its run is in-field M(T)
        view = CurieView(session)
        assert view.experiment.value == IN_FIELD_MT and view.data_type == "magnetization"
        view.experiment.value = CHI_T
        assert session.specimen == "ferroxyhyte_Princeton-1985-M1-2"
        assert view.data_type == "susceptibility"
        assert view.methods.value == ["inflection", "max_curvature", "inverse_susceptibility"]
        assert "Ms² extrapolation" not in view.methods.options
        assert len(view.figure.axes) == 3                                        # + the 1/χ panel
        curie_weiss = view.estimates[view.estimates["method"] == "inverse_susceptibility"]
        assert np.isfinite(curie_weiss["curie_temp_stderr"]).all()
        assert "T<sub>C</sub> (°C)" in view.table.object
        view.set_parameters(smooth_window=10)
        assert "T<sub>C</sub> (°C)" in view.table.object and "smooth_window=10," in view.code.text
        view.experiment.value = IN_FIELD_MT
        assert view.methods.value == ["inflection", "max_curvature", "two_tangent", "landau"]
        assert "T<sub>C</sub> (K)" in view.table.object and "temp_unit='K'," in view.code.text

    def test_nothing_selected_says_so_and_a_failure_is_reported(self):
        view = CurieView(ms_curve())
        view.branches.value = []
        assert "pick at least one method" in view.table.object and view.figure is None
        view.branches.value = ["heating"]
        assert len(view.estimates) == 4
        view.set_methods([])
        assert "pick at least one method" in view.table.object


ECMB = os.path.join(REPO, "data_files", "3_0", "ECMB_rockmag")      # MagIC 20213: VSM loops, backfield, MPMS
ECMB_LOOP = "IRM-VSM3-LP-HYS-218845"                                   # NED1-5c, ±1 T


@pytest.fixture(scope="module")
def ecmb():
    return rs.Session(ECMB)


def hysteresis_loop(ms=1.0, bc=0.02, chi_hf=0.0, width=0.03, noise=0.0, seed=0):
    """A ±1 T loop of tanh branches with coercivity `bc` (T) on a paramagnetic slope, from positive saturation."""
    fields = np.linspace(1.0, -1.0, 201)
    down = ms * np.tanh((fields + bc) / width) + chi_hf / (4 * np.pi / 1e7) * fields
    up = ms * np.tanh((fields[::-1] - bc) / width) + chi_hf / (4 * np.pi / 1e7) * fields[::-1]
    field = np.concatenate([fields, fields[::-1]])
    mags = np.concatenate([down, up]) + np.random.default_rng(seed).normal(0, noise, 2 * len(fields))
    return pd.DataFrame({"specimen": "syn", "method_codes": "LP-HYS", "experiment": "syn_HYS",
                         "meas_field_dc": field, "magn_mass": mags})


class TestHysteresisView:
    def test_a_loop_of_the_example_is_processed_and_the_code_reproduces_it(self, ecmb, monkeypatch):
        view = HysteresisView(ecmb)
        assert view.experiment.value == ECMB_LOOP and ecmb.specimen == "NED1-5c"
        r = view.results
        assert r["loop_is_closed"] and not r["loop_is_linear"] and np.isfinite(r["Ms"])
        assert "M<sub>r</sub>/M<sub>s</sub> <b>0.168</b>" in view.result.object
        assert "B<sub>c</sub> <b>14.3 mT</b>" in view.result.object
        assert "F<sub>NL</sub>" in view.quality.object and "non-linear high-field fit" in view.quality.object
        assert view.figure is r["plot"] and view.plot.object is view.figure
        lines = view.code.text.splitlines()
        assert lines[5:] == [f"experiment = rmag.experiment_selection(measurements, '{ECMB_LOOP}')",
                             "results = rmag.process_hyst_loop(experiment['meas_field_dc'], experiment['magn_mass'], 'NED1-5c')"]
        monkeypatch.setattr(rockmag, "show", lambda *a, **k: None)          # the notebook call shows table and plot
        namespace = {"rmag": rockmag, "measurements": ecmb.measurements}
        exec("\n".join(lines[5:]), namespace)
        assert namespace["results"]["Bc"] == pytest.approx(r["Bc"])

    def test_the_controls_are_the_functions_arguments(self, ecmb):
        view = HysteresisView(ecmb)
        legacy_bc = view.results["Bc"]
        view.set_parameters(centering_protocol="iterative", NL_fit=True, fit_open_loop=True, fit_linear_loop=True)
        assert view.code.text.splitlines()[6:] == [
            "results = rmag.process_hyst_loop(", "    experiment['meas_field_dc'],", "    experiment['magn_mass'],",
            "    'NED1-5c',", "    NL_fit=True,", "    centering_protocol='iterative',", "    fit_open_loop=True,",
            "    fit_linear_loop=True,", ")"]
        assert view.results["Bc"] == pytest.approx(legacy_bc, rel=0.05)     # the centering protocols agree here
        view.set_parameters(centering_protocol="legacy", NL_fit=False, fit_open_loop=False, fit_linear_loop=False)
        assert view.code.text.splitlines()[-1].endswith("'NED1-5c')")

    def test_changing_experiment_follows_the_specimen_both_ways(self, ecmb):
        view = HysteresisView(ecmb)
        view.experiment.value = "IRM-VSM3-LP-HYS-218855"
        assert ecmb.specimen == "NED6-6c" and "'NED6-6c'" in view.code.text
        ecmb.specimen = "NED18-2c"
        assert view.experiment.value == "IRM-VSM3-LP-HYS-218847"
        ecmb.specimen = "NED1-5c"

    def test_a_synthetic_loop_gives_back_its_parameters(self):
        view = HysteresisView(hysteresis_loop(ms=1.0, bc=0.02, chi_hf=2e-7))
        r = view.results
        assert r["Ms"] == pytest.approx(1.0, rel=0.02)
        assert r["Bc"] == pytest.approx(0.02, rel=0.05)
        assert r["chi_HF"] == pytest.approx(2e-7, rel=0.05)
        assert view.code.text.splitlines()[3] == "# measurements: the DataFrame this view was given"

    def test_a_linear_loop_takes_the_decision_trees_exit_and_says_so(self):
        loop = hysteresis_loop(ms=0.0, chi_hf=2e-7, noise=1e-4)
        view = HysteresisView(loop)
        r = view.results
        assert r["loop_is_linear"] and not np.isfinite(r["Ms"])
        assert "statistically linear" in view.result.object and "M<sub>s</sub> <b>—</b>" in view.result.object
        assert r["chi_HF"] == pytest.approx(2e-7, rel=0.05)
        view.set_parameters(fit_linear_loop=True)
        assert not view.results["loop_is_linear"] or np.isfinite(view.results["Bc"])

    def test_nothing_to_process_is_said_not_raised(self):
        view = HysteresisView(pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                                            "meas_temp": [10.0], "magn_mass": [1.0]}))
        assert view.experiment.options == {} and view.results is None and "no hysteresis loop" in view.result.object


ECMB_BACKFIELD = "IRM-VSM3-LP-BCR-BF-218846"                # NED1-5c
TWO_COMPONENTS = ((0.6, 1.3, 0.3), (0.4, 2.0, 0.2))        # (fraction, log10 B_mean in mT, dispersion)


def remanence_left(log_b, components=TWO_COMPONENTS):
    """The fraction of a saturation remanence left after a backfield of 10**log_b mT, for log-Gaussian components."""
    return sum(f * (1 - 0.5 * (1 + erf((log_b - mu) / (dp * np.sqrt(2))))) for f, mu, dp in components)


def backfield_curve(components=TWO_COMPONENTS, n=80, noise=0.0, seed=0):
    """A backfield curve from the saturation remanence (field 0, M = 1) through 0.3 mT–1 T in log steps."""
    log_b = np.linspace(-0.5, 3.0, n)
    mags = 2 * remanence_left(log_b, components) - 1 + np.random.default_rng(seed).normal(0, noise, n)
    return pd.DataFrame({"specimen": "syn", "method_codes": "LP-BCR-BF", "experiment": "syn_BCR",
                         "treat_dc_field": np.concatenate([[0.0], -(10 ** log_b) / 1e3]),
                         "magn_mass": np.concatenate([[1.0], mags])})


class TestBackfieldView:
    def test_the_example_curve_gives_bcr_and_the_code_reproduces_it(self, ecmb):
        view = BackfieldView(ecmb)
        assert view.experiment.value == ECMB_BACKFIELD and ecmb.specimen == "NED1-5c"
        assert view.Bcr == pytest.approx(0.02636, abs=5e-5) and "B<sub>cr</sub> <b>26.4 mT</b>" in view.result.object
        assert len(view.processed) == 99 and view.drop_first.value and view.drop_first.disabled
        assert len(view.figure.children) == 3 and view.plot.object is view.figure
        lines = view.code.text.splitlines()
        assert lines[5:] == [f"experiment = rmag.experiment_selection(measurements, '{ECMB_BACKFIELD}')",
                             "experiment, Bcr = rmag.process_backfield_data(experiment, smooth_mode='spline', drop_first=True)",
                             "rmag.plot_backfield_data(experiment, Bcr=Bcr, interactive=True)"]
        namespace = {"rmag": rockmag, "measurements": ecmb.measurements}
        exec("\n".join(lines[5:-1]), namespace)
        assert namespace["Bcr"] == pytest.approx(view.Bcr)
        assert list(namespace["experiment"]["smoothed_magn_mass_shift"]) == list(view.processed["smoothed_magn_mass_shift"])

    def test_the_smoothing_controls_are_the_functions_arguments(self, ecmb):
        view = BackfieldView(ecmb)
        raw = view.processed["smoothed_magn_mass_shift"].to_numpy()
        view.set_parameters(smooth_frac=0.2)
        assert view.code.text.splitlines()[6:12] == ["experiment, Bcr = rmag.process_backfield_data(", "    experiment,",
                                                     "    smooth_mode='spline',", "    smooth_frac=0.2,",
                                                     "    drop_first=True,", ")"]
        assert not np.allclose(view.processed["smoothed_magn_mass_shift"].to_numpy(), raw)
        assert view.Bcr == pytest.approx(0.02636, abs=5e-5)                 # Bcr is read off the raw curve
        view.set_parameters(smooth_frac=0.0)

    def test_changing_experiment_follows_the_specimen_both_ways(self, ecmb):
        view = BackfieldView(ecmb)
        view.experiment.value = "IRM-VSM3-LP-BCR-BF-218850"
        assert ecmb.specimen == "NED2-8c" and view.Bcr == pytest.approx(0.0344, abs=1e-4)
        ecmb.specimen = "NED18-2c"
        assert view.experiment.value == "IRM-VSM3-LP-BCR-BF-218848" and view.Bcr == pytest.approx(0.0210, abs=1e-4)
        ecmb.specimen = "NED1-5c"

    def test_a_synthetic_curve_gives_back_its_bcr_with_the_sirm_point_dropped(self):
        view = BackfieldView(backfield_curve())
        expected = 10 ** brentq(lambda log_b: remanence_left(log_b) - 0.5, -0.5, 3.0) / 1e3
        assert view.Bcr == pytest.approx(expected, rel=2e-3)
        assert len(view.processed) == 80 and np.isfinite(view.processed["log_dc_field"]).all()
        assert view.code.text.splitlines()[3] == "# measurements: the DataFrame this view was given"

    def test_nothing_to_plot_is_said_not_raised(self):
        view = BackfieldView(pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                                           "meas_temp": [10.0], "magn_mass": [1.0]}))
        assert view.experiment.options == {} and view.Bcr is None and "no backfield curve" in view.result.object


class TestUnmixingView:
    @pytest.fixture(scope="class")
    def synthetic(self):
        return UnmixingView(backfield_curve())

    def test_two_log_gaussian_components_are_recovered_by_every_method(self, synthetic):
        for method in ["spectrum", "curve", "maxunmix"]:
            synthetic.set_unmixing(method=method, n_components=2, vary_skew=False)
            params = synthetic.result["params"]
            assert params["proportion"].to_numpy() == pytest.approx([0.6, 0.4], abs=0.01), method
            assert params["log10_B_mean"].to_numpy() == pytest.approx([1.3, 2.0], abs=0.01), method
            assert params["sd_log"].to_numpy() == pytest.approx([0.3, 0.2], abs=0.01), method
            assert synthetic.result["stats"]["r_squared"] > 0.999
        synthetic.set_unmixing(method="spectrum")
        assert "B<sub>mean</sub> (mT)" in synthetic.table.object and "r² <b>1.0000</b>" in synthetic.table.object

    def test_noise_does_not_move_the_components_much(self):
        view = UnmixingView(backfield_curve(noise=0.005))
        assert view.result["params"]["log10_B_mean"].to_numpy() == pytest.approx([1.3, 2.0], abs=0.02)
        assert view.result["params"]["proportion"].to_numpy() == pytest.approx([0.6, 0.4], abs=0.02)

    def test_choose_n_runs_the_selection_and_enters_the_code_until_the_slider_is_moved(self, synthetic):
        synthetic.set_unmixing(n_components=1)
        assert synthetic.selection is None and "select_n_components" not in synthetic.code.text
        synthetic.choose_n()
        assert synthetic.n_components.value == 2
        assert list(synthetic.selection["selected"]) == [False, True, False, False]
        assert "2 components chosen by the parsimony rule" in synthetic.table.object
        lines = synthetic.code.text.splitlines()
        assert lines[5:7] == ["experiment, Bcr = rmag.process_backfield_data(experiment, smooth_mode='spline', drop_first=True)",
                              "x, M = experiment['log_dc_field'], experiment['magn_mass_shift']"]
        assert lines[7] == ("n_components, selection, fits = rmag.select_n_components(x, M, method='spectrum', "
                            "max_components=4, vary_skew=False)")
        assert "    n_components=n_components," in lines and lines[-1] == \
            "rmag.plot_coercivity_unmixing(result, title='syn · 2 components')"
        synthetic.set_unmixing(n_components=3)                               # a hand-picked count drops the rule
        assert synthetic.selection is None and "select_n_components" not in synthetic.code.text
        assert "n_components=3," in synthetic.code.text.splitlines()[-2]
        synthetic.set_unmixing(n_components=2)

    def test_the_code_reproduces_the_fit(self, synthetic, monkeypatch):
        import matplotlib
        matplotlib.use("Agg")
        synthetic.set_unmixing(method="curve", n_components=2, vary_skew=True)
        lines = synthetic.code.text.splitlines()
        assert lines[-2] == "result = rmag.unmix_coercivity(x, M, method='curve', n_components=2, vary_skew=True)"
        namespace = {"rmag": rockmag, "measurements": synthetic.s.measurements}
        exec("\n".join(lines[4:-1]), namespace)
        assert namespace["result"]["params"]["B_mean_mT"].to_numpy() == \
            pytest.approx(synthetic.result["params"]["B_mean_mT"].to_numpy())
        synthetic.set_unmixing(method="spectrum", vary_skew=False)

    def test_the_example_curve_is_unmixed(self, ecmb):
        view = UnmixingView(ecmb)
        assert view.experiment.value == ECMB_BACKFIELD and view.result["n_components"] == 2
        assert view.result["method"] == "spectrum" and view.plot.object is view.figure
        assert "NED1-5c · 2 components" in view.code.text
        view.set_unmixing(method="curve", n_components=3)
        assert view.result["stats"]["r_squared"] > 0.999

    def test_a_failed_fit_is_reported_not_raised(self, monkeypatch):
        def fail(*a, **k):
            raise RuntimeError("no convergence")
        monkeypatch.setattr(rockmag, "unmix_coercivity", fail)
        view = UnmixingView(backfield_curve())
        assert view.result is None and "The fit failed: no convergence" in view.table.object
        assert view.code.text.splitlines()[-1].startswith("experiment, Bcr = rmag.process_backfield_data")


FORC = os.path.join(REPO, "data_files", "3_0", "FORC_example")
FORC_EXPERIMENT = "LP-FORC-conventional_example"


class TestForcView:
    @pytest.fixture(scope="class")
    def example(self):
        return ForcView(rs.Session(FORC))

    @pytest.fixture(scope="class")
    def synthetic(self, tmp_path_factory):
        """The quadratic synthetic run of ``test_forc`` as a MagIC table in memory: rho = -0.5 × 0.7e-6 everywhere."""
        raw = tmp_path_factory.mktemp("forc") / "synthetic_specimen.txt"
        write_micromag(raw)
        magic_path = forc.export_magic_measurements_from_raw(str(raw))
        return pd.read_csv(magic_path, sep="\t", header=1)

    def test_the_example_run_is_processed_and_the_code_reproduces_it(self, example):
        view, session = example, example.s
        assert view.experiment.value == FORC_EXPERIMENT and session.specimen == "conventional_example"
        assert len(view.out["forcs_display"]) == 119 and view.out["rho"].shape == (119, 162)
        assert view.out["drift_corrected"] and view.out["n_calibration_points"] == 120
        for text in ("curves <b>119</b>", "field step <b>2.83 mT</b>", "drift <b>120 calibration points</b>",
                     "LOESS span <b>14.1 × 16.9 mT</b>", "B<sub>c</sub> <b>2.49 mT</b>"):
            assert text in view.result.object
        assert view.plot.object is view.figure is view.out["fig_rho"] and len(view.curves.object.renderers) == 2
        # the header window a MagIC table gives is the run's field range; the view frames the distribution instead
        assert view._window == {"Bu_max": pytest.approx(0.218, abs=1e-3), "Bc_max": pytest.approx(0.2372, abs=1e-3)}
        assert view.Bu_max.value == view.Bc_max.value == 120.0
        assert view.out["plot_limits"] == {"Bu_min_lim": -0.12, "Bu_max_lim": 0.12, "Bc_min_lim": 0.0, "Bc_max_lim": 0.12}
        lines = view.code.text.splitlines()
        assert lines[2] == "import pmagpy.forc as forc" and lines[6:] == [
            f"experiment = rmag.experiment_selection(measurements, '{FORC_EXPERIMENT}')",
            "out = forc.process_forc_dataframe(experiment, Bu_min=-0.12, Bu_max=0.12, Bc_max=0.12)"]
        namespace = {"rmag": rockmag, "forc": forc, "measurements": session.measurements}
        exec("\n".join(lines[6:]).replace("(experiment,", "(experiment, plot_rho=False, verbose=False,"), namespace)
        np.testing.assert_allclose(namespace["out"]["rho"], view.out["rho"], rtol=1e-6, equal_nan=True)

    def test_the_controls_are_the_pipelines_arguments_off_their_defaults(self, example):
        view = example
        loess_rho = view.out["rho"].copy()
        view.set_parameters(smoothing="variforc", preset="central_ridge", smoothing_factor=9, Bc_max=100, Bu_max=100,
                            color_scale_version=2, show_contours=False)
        assert not view.smooth_strength.visible and view.preset.visible and view.smoothing_factor.visible
        lines = view.code.text.splitlines()
        assert lines[7:] == ["out = forc.process_forc_dataframe(", "    experiment,", "    smoothing='variforc',",
                             "    variforc=forc.variforc_settings('central_ridge', smoothing_factor=9),",
                             "    Bu_min=-0.1,", "    Bu_max=0.1,", "    Bc_max=0.1,", "    color_scale_version=2,", "    show_contours=False,", ")"]
        assert "VARIFORC <b>central ridge · sf 9</b>" in view.result.object
        assert view.out["plot_limits"]["Bc_max_lim"] == pytest.approx(0.1) and view.out["plot_limits"]["Bu_min_lim"] == pytest.approx(-0.1)
        assert not np.allclose(view.out["rho"], loess_rho, equal_nan=True)
        namespace = {"rmag": rockmag, "forc": forc, "measurements": view.s.measurements}
        exec("\n".join(lines[6:]).replace("    experiment,", "    experiment, plot_rho=False, verbose=False,"), namespace)
        np.testing.assert_allclose(namespace["out"]["rho"], view.out["rho"], rtol=1e-6, equal_nan=True)
        # the default factor and the header window are not written; a moved LOESS strength is
        view.set_parameters(smoothing="loess", smooth_strength=1.5, Bc_max=view._window["Bc_max"] * 1e3,
                            Bu_max=view._window["Bu_max"] * 1e3, color_scale_version=1, show_contours=True)
        assert view.code.text.splitlines()[7] == "out = forc.process_forc_dataframe(experiment, smooth_strength=1.5)"
        assert view.smooth_strength.visible and not view.preset.visible
        assert view.out["plot_limits"]["Bc_max_lim"] == pytest.approx(view._window["Bc_max"])
        view.set_parameters(smooth_strength=1.0, Bc_max=120, Bu_max=120)

    def test_a_synthetic_run_gives_back_its_known_distribution(self, synthetic):
        view = ForcView(synthetic)
        assert view.experiment.value == "LP-FORC-synthetic_specimen" and view.s.specimen == "synthetic_specimen"
        assert view.code.text.splitlines()[4] == "# measurements: the DataFrame this view was given"
        assert "curves <b>40</b>" in view.result.object and "field step <b>5.00 mT</b>" in view.result.object
        rho = view.out["rho"]
        finite = np.isfinite(rho)
        assert finite.sum() > 2000
        # rho = -0.5 × d²M/dHa dHb with the mixed coefficient 0.7e-6; LOESS is exact away from the edges
        assert np.nanmedian(rho) == pytest.approx(-0.35e-6, rel=1e-4)
        assert np.mean(np.abs(rho[finite] + 0.35e-6) < 0.35e-8) > 0.8
        view.set_parameters(smoothing="variforc", preset="both_ridges")
        rho = view.out["rho"]
        assert np.nanmedian(rho) == pytest.approx(-0.35e-6, rel=1e-2)
        assert view.code.text.splitlines()[-5:] == ["    variforc=forc.variforc_settings('both_ridges'),", "    Bu_min=-0.22,",
                                                   "    Bu_max=0.22,", "    Bc_max=0.22,", ")"]

    def test_nothing_to_plot_is_said_not_raised(self):
        view = ForcView(pd.DataFrame({"specimen": ["a"], "method_codes": ["LP-FC"], "experiment": ["e"],
                                      "meas_temp": [10.0], "magn_mass": [1.0]}))
        assert view.experiment.options == {} and view.out is None and "no FORC run" in view.result.object
        assert view.code.text.splitlines()[2] == "import pmagpy.forc as forc"



def read_table(path):
    """A MagIC table as pandas reads it (the header line skipped)."""
    return pd.read_csv(path, sep="\t", header=1)


class TestSpecimenSave:
    """Results into specimens.txt through MagicProject, on copies of the examples."""

    @pytest.fixture()
    def ecmb_copy(self, tmp_path):
        d = str(tmp_path / "ECMB")
        shutil.copytree(ECMB, d)
        return d

    def test_hysteresis_parameters_go_to_the_experiments_row(self, ecmb_copy):
        s = rs.Session(ecmb_copy)
        view = HysteresisView(s)
        assert not view.save.button.disabled and view.save.note.object == ""
        before = read_table(os.path.join(ecmb_copy, "specimens.txt"))
        path = view.save.save()
        assert path == os.path.join(ecmb_copy, "specimens.txt")
        after = read_table(path)
        row = after[after["experiments"] == ECMB_LOOP].iloc[0]
        assert row["hyst_bc"] == pytest.approx(view.results["Bc"])
        assert row["hyst_ms_mass"] == pytest.approx(view.results["Ms"])
        assert row["software_packages"] == s.project.software_tag and row["software_packages"].endswith(":pmagpy_rockmag")
        assert len(after) == len(before)
        # only that row changed; the original is kept beside, byte for byte
        untouched = after["experiments"] != ECMB_LOOP
        for column in before.columns:
            assert (before.loc[untouched, column].fillna("").astype(str).str.strip().to_numpy()
                    == after.loc[untouched, column].fillna("").astype(str).str.strip().to_numpy()).all(), column
        backup = os.path.join(ecmb_copy, "backup_before_pmagpy_rockmag", "specimens.txt")
        with open(backup) as f, open(os.path.join(ECMB, "specimens.txt")) as g:
            assert f.read() == g.read()
        assert "1 row updated" in view.save.note.object and "backup_before_pmagpy_rockmag/" in view.save.note.object
        # the code pane now reads analysis then save, and the same lines went to specimens.py
        lines = view.code.text.splitlines()
        start = lines.index("specimens = contribution.tables['specimens'].df")
        assert lines[start - 2].startswith("results = rmag.process_hyst_loop(") and lines[start - 1] == ""
        assert lines[start + 1:start + 4] == [f"results.update(specimen='NED1-5c', experiment='{ECMB_LOOP}')",
                                              "specimens = rmag.add_hyst_stats_to_specimens_table(specimens, results)",
                                              "contribution.tables['specimens'].df = specimens"]
        assert lines[start + 4].startswith("contribution.tables['specimens'].write_magic_file(")
        with open(os.path.join(ecmb_copy, "specimens.py")) as f:
            script = f.read()
        assert script.startswith("# written by PmagPy Rock Magnetism — the calls that made specimens.txt\n")
        assert "# ----- hysteresis parameters: NED1-5c" in script and view.code.text in script
        # the in-memory table followed the file, so a second save changes nothing
        view.refresh()
        assert view.save.note.object == "" and not view.save.button.disabled
        view.save.save()
        assert "nothing changed" in view.save.note.object

    def test_the_saved_code_reproduces_the_table_in_a_notebook(self, ecmb_copy, tmp_path, monkeypatch):
        s = rs.Session(ecmb_copy)
        view = HysteresisView(s)
        view.save.save()
        app_table = read_table(os.path.join(ecmb_copy, "specimens.txt"))
        notebook = str(tmp_path / "notebook")
        shutil.copytree(ECMB, notebook)
        monkeypatch.setattr(rockmag, "show", lambda *a, **k: None)
        exec(view.code.text.replace(ecmb_copy, notebook), {})
        nb_table = read_table(os.path.join(notebook, "specimens.txt"))
        for column in ("hyst_bc", "hyst_ms_mass", "hyst_mr_mass", "hyst_xhf"):
            assert nb_table.loc[nb_table["experiments"] == ECMB_LOOP, column].iloc[0] == pytest.approx(
                app_table.loc[app_table["experiments"] == ECMB_LOOP, column].iloc[0])
        assert len(nb_table) == len(app_table)

    def test_bcr_and_components_share_the_table_and_the_script(self, ecmb_copy):
        s = rs.Session(ecmb_copy)
        backfield = BackfieldView(s)
        backfield.save.save()
        table = read_table(os.path.join(ecmb_copy, "specimens.txt"))
        assert table.loc[table["experiments"] == ECMB_BACKFIELD, "rem_bcr"].iloc[0] == pytest.approx(backfield.Bcr)
        lines = backfield.code.text.splitlines()
        assert lines[lines.index("specimens = contribution.tables['specimens'].df") + 1] == \
            f"rmag.add_Bcr_to_specimens_table(specimens, '{ECMB_BACKFIELD}', Bcr)"
        unmixing = UnmixingView(s)
        assert unmixing.experiment.value == ECMB_BACKFIELD
        n_before = len(table)
        unmixing.save.save()
        assert "2 rows added" in unmixing.save.note.object
        table = read_table(os.path.join(ecmb_copy, "specimens.txt"))
        rows = table[table["rem_cmf"].notna() & (table["experiments"] == ECMB_BACKFIELD)]
        assert len(table) == n_before + 2 and len(rows) == 2
        assert sorted(rows["rem_cmf"] * 1e3) == pytest.approx(sorted(unmixing.result["params"]["B_median_mT"]))
        assert (rows["rem_n_comp"] == 2).all() and np.allclose(rows["rem_bcr"], unmixing.Bcr)
        assert (rows["method_codes"] == "LP-BCR-BF").all() and (rows["software_packages"] == s.project.software_tag).all()
        lines = unmixing.code.text.splitlines()
        start = lines.index("specimens = contribution.tables['specimens'].df")
        assert lines[start + 1:start + 7] == [
            "components = rmag.coercivity_components_table(", "    result,", f"    '{ECMB_BACKFIELD}',", "    'NED1-5c',",
            "    Bcr=Bcr,", ")"]
        assert lines[start + 7] == "specimens = rmag.add_unmixing_to_specimens_table(specimens, components)"
        # saving the fit again replaces its rows rather than adding to them
        unmixing.refresh()
        unmixing.save.save()
        assert len(read_table(os.path.join(ecmb_copy, "specimens.txt"))) == n_before + 2
        with open(os.path.join(ecmb_copy, "specimens.py")) as f:
            script = f.read()
        assert script.count("# written by") == 1 and script.count("# ----- Bcr: NED1-5c") == 1
        assert script.count("# ----- coercivity components: NED1-5c") == 2
        assert len(os.listdir(os.path.join(ecmb_copy, "backup_before_pmagpy_rockmag"))) == 1

    def test_the_curie_estimate_to_save_is_picked_heating_first(self, tmp_path):
        d = str(tmp_path / "RMB")
        shutil.copytree(EXAMPLE, d)
        s = rs.Session(d)
        s.specimen = "ferroxyhyte_Princeton-1985-M1-2"                  # its run is CHI_T: heating and cooling, in °C
        view = CurieView(s)
        specimen = s.specimen
        assert view.experiment.value == CHI_T and view.chosen.visible
        labels = list(view.chosen.options)
        assert len(labels) == 6 and labels[0].startswith("heating · inflection") and labels[0].endswith(" °C")
        assert [label.split(" · ")[0] for label in labels] == ["heating"] * 3 + ["cooling"] * 3
        assert view.chosen.value == ("inflection", "heating")
        view.chosen.value = ("inflection", "cooling")
        expected = view.estimates.set_index(["method", "branch"]).loc[("inflection", "cooling"), "curie_temp"] + 273.15
        with warnings.catch_warnings():
            warnings.simplefilter("error")                      # the specimen-name fallback must not leak out
            view.save.save()
        table = read_table(os.path.join(d, "specimens.txt"))
        row = table[table["specimen"] == specimen].iloc[0]
        assert row["critical_temp"] == pytest.approx(expected) and row["critical_temp_type"] == "Curie"  # kelvin
        assert "'curie_branch': 'cooling'" in row["description"]
        lines = view.code.text.splitlines()
        assert lines[-1] == ")" and any(l.startswith("contribution.tables['specimens'].write_magic_file(") for l in lines)
        assert f"    '{CHI_T}'," in lines and "    branch='cooling'," in lines
        assert "1 row updated" in view.save.note.object
        # a branch switched off leaves the picker: the pick follows
        view.branches.value = ["heating"]
        assert all(label.startswith("heating") for label in view.chosen.options)
        assert view.chosen.value == ("inflection", "heating")
        # a run measured on cooling only offers cooling; the pick moves with it and stays put coming back,
        # so one choice of estimator carries through a batch of specimens
        view.branches.value = list(view.branches.options)
        view.experiment.value = IN_FIELD_MT
        assert all(label.startswith("cooling") for label in view.chosen.options) and len(view.chosen.options) == 4
        assert view.chosen.value == ("inflection", "cooling")
        view.experiment.value = CHI_T
        assert view.chosen.value == ("inflection", "cooling")

    def test_where_nothing_can_be_saved_the_button_says_why(self, tmp_path):
        in_memory = HysteresisView(hysteresis_loop())
        assert in_memory.save.button.disabled and "in a notebook" in in_memory.save.note.object
        assert in_memory.save.save() is None
        bare = str(tmp_path / "bare")
        os.makedirs(bare)
        shutil.copy(os.path.join(ECMB, "measurements.txt"), bare)
        view = HysteresisView(rs.Session(bare))
        assert view.save.button.disabled and "no specimens.txt" in view.save.note.object and "Metadata" in view.save.note.object
        # a writer that finds no row to write to is reported, not raised, and nothing is written
        d = str(tmp_path / "ECMB")
        shutil.copytree(ECMB, d)
        table = read_table(os.path.join(d, "specimens.txt"))
        table = table[table["experiments"] != ECMB_BACKFIELD]
        table.to_csv(os.path.join(d, "specimens.txt"), sep="\t", index=False)
        with open(os.path.join(d, "specimens.txt")) as f:
            body = f.read()
        with open(os.path.join(d, "specimens.txt"), "w") as f:
            f.write("tab delimited\tspecimens\n" + body)
        s = rs.Session(d)
        view = BackfieldView(s)
        assert not view.save.button.disabled
        assert view.save.save() is None
        assert "Not saved:" in view.save.note.object and "no specimens row matches" in view.save.note.object
        assert not os.path.exists(os.path.join(d, "backup_before_pmagpy_rockmag"))
        assert not os.path.exists(os.path.join(d, "specimens.py"))

    def test_changed_rows_compares_numbers_as_numbers_and_blanks_as_equal(self):
        before = pd.DataFrame({"specimen": ["a", "b", "c"], "hyst_bc": ["0.0500", "", None], "note": ["x", "y", None]})
        after = pd.DataFrame({"specimen": ["a", "b", "c", "d"], "hyst_bc": [0.05, np.nan, 0.1, 0.2],
                              "note": ["x", "y ", np.nan, ""], "new": [np.nan, np.nan, np.nan, 1.0]})
        assert list(results.changed_rows(before, after)) == [False, False, True, True]
        assert list(results.changed_rows(before.iloc[:0], after)) == [True] * 4


class TestApp:
    def test_create_app_builds_the_template_with_one_tab_per_view(self):
        template = app.create_app(EXAMPLE)
        assert template.session.directory == EXAMPLE
        assert isinstance(app.create_app(os.path.join(EXAMPLE, "nowhere")), pn.pane.Markdown)

    def test_the_body_has_the_index_and_the_views(self, session):
        body = app.build_body(session)
        assert list(body.views) == ["mpms_dc", "verwey", "goethite", "mpms_ac", "chi_t", "curie", "hys", "bcr", "unmix", "forc"]
        assert [name for name, _ in zip(body.main._names, body.main)] == [
            "MPMS DC", "Verwey", "Goethite", "χ AC", "χ–T", "Curie", "Hysteresis", "Backfield", "Unmixing", "FORC"]
        assert body.views["verwey"].specimen.value == body.views["mpms_dc"].specimen.value
        assert body.info.app_id == "pmagpy_rockmag"
