"""
Tests for the Rock Magnetism application: the experiment index, the session,
and the views against the shipped examples (MagIC contribution 20427,
``data_files/3_0/RMB_oxyhydroxides``, for the low-temperature and
thermomagnetic views; 20213, ``data_files/3_0/ECMB_rockmag``, for the
hysteresis ones) and synthetic curves with known answers. Run with the apps
environment::

    pytest programs/pmagpy_rockmag/test_app.py -q
"""
import os

import numpy as np
import pandas as pd
import pytest

pn = pytest.importorskip("panel")

from pmagpy import rockmag  # noqa: E402
from pmagpy_rockmag import app, session as rs  # noqa: E402
from pmagpy_rockmag.views import (AcSusceptibilityView, ChiTView, CurieView, GoethiteView, HysteresisView,  # noqa: E402
                                  MpmsDcView, VerweyView)

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


class TestApp:
    def test_create_app_builds_the_template_with_one_tab_per_view(self):
        template = app.create_app(EXAMPLE)
        assert template.session.directory == EXAMPLE
        assert isinstance(app.create_app(os.path.join(EXAMPLE, "nowhere")), pn.pane.Markdown)

    def test_the_body_has_the_index_and_the_views(self, session):
        body = app.build_body(session)
        assert list(body.views) == ["mpms_dc", "verwey", "goethite", "mpms_ac", "chi_t", "curie", "hys"]
        assert [name for name, _ in zip(body.main._names, body.main)] == [
            "MPMS DC", "Verwey", "Goethite", "AC susceptibility", "χ–T", "Curie", "Hysteresis"]
        assert body.views["verwey"].specimen.value == body.views["mpms_dc"].specimen.value
        assert body.info.app_id == "pmagpy_rockmag"
