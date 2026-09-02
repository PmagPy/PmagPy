"""
Tests for the Rock Magnetism application: the experiment index, the session,
and the MPMS DC and Verwey views against the shipped example (MagIC
contribution 20427, ``data_files/3_0/RMB_oxyhydroxides``) and a synthetic
magnetite curve. Run with the apps environment::

    pytest programs/pmagpy_rockmag/test_app.py -q
"""
import os

import numpy as np
import pandas as pd
import pytest

pn = pytest.importorskip("panel")

from pmagpy import rockmag  # noqa: E402
from pmagpy_rockmag import app, session as rs  # noqa: E402
from pmagpy_rockmag.views import GoethiteView, MpmsDcView, VerweyView  # noqa: E402

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


class TestApp:
    def test_create_app_builds_the_template_with_one_tab_per_view(self):
        template = app.create_app(EXAMPLE)
        assert template.session.directory == EXAMPLE
        assert isinstance(app.create_app(os.path.join(EXAMPLE, "nowhere")), pn.pane.Markdown)

    def test_the_body_has_the_index_and_the_views(self, session):
        body = app.build_body(session)
        assert list(body.views) == ["mpms_dc", "verwey", "goethite"]
        assert [name for name, _ in zip(body.main._names, body.main)] == ["MPMS DC", "Verwey", "Goethite"]
        assert body.views["verwey"].specimen.value == body.views["mpms_dc"].specimen.value
        assert body.info.app_id == "pmagpy_rockmag"
