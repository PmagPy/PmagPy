"""
Tests for the application layer of PmagPy Intensity: session state and
persistence, the views' behaviour, the export policy (never write into the
source directory unless that is the output directory), BiCEP, and the
publication figures. Run with an environment that has panel and bokeh::

    pytest programs/pmagpy_intensity/test_app.py -q
"""
import json
import os
import shutil

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

import pmagpy.paleointensity as pint          # noqa: E402
from pmagpy import bicep as bicep_core        # noqa: E402
from pmagpy import pint_stats as ps           # noqa: E402
from pmagpy import tdt as tdt_reader          # noqa: E402
from pmagpy_intensity import publication as pub                       # noqa: E402
from pmagpy_intensity.session import AUTOSAVE_NAME, REDO_NAME, Session  # noqa: E402
from pmagpy_intensity.views import (BicepView, CorrectionsView, CriteriaView, DataView,  # noqa: E402
                                    ExportView, GroupView, InterpretationsView, SpecimenView)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SMALL = os.path.join(REPO, "data_files", "thellier_magic")
MEGIDDO = os.path.join(REPO, "data_files", "3_0", "Megiddo")


def _wait(condition, timeout: float = 30.0) -> bool:
    """Wait for a background worker (the views run long jobs off the server thread)."""
    import time
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(0.05)
    return False


@pytest.fixture
def workdir(tmp_path):
    """A private copy of a small contribution plus a separate output directory."""
    src = tmp_path / "data"
    src.mkdir()
    shutil.copy(os.path.join(SMALL, "measurements.txt"), src)
    return str(src), str(tmp_path / "out")


@pytest.fixture(scope="module")
def study():
    session = Session(MEGIDDO, cache=False)
    session.autosave_enabled = False
    return session


# ---------------------------------------------------------------------------
class TestSession:
    def test_a_directory_loads_and_picks_an_interpreted_specimen(self, workdir):
        src, out = workdir
        session = Session(src, out)
        assert session.data is not None and len(session.data.specimens) > 200
        assert session.specimen in session.data.specimens
        assert "specimens" in session.status

    def test_editing_auto_saves_into_the_output_directory_only(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 4)
        assert os.path.exists(os.path.join(out, AUTOSAVE_NAME))
        assert not os.path.exists(os.path.join(src, AUTOSAVE_NAME))

    def test_the_session_is_restored_next_time(self, workdir):
        src, out = workdir
        first = Session(src, out)
        name = first.specimen
        first.set_bounds(1, 5)
        again = Session(src, out)
        assert "restored" in again.status
        assert (again.data.interpretations[name].imin,
                again.data.interpretations[name].imax) == (1, 5)

    def test_a_corrupt_autosave_does_not_stop_the_load(self, workdir):
        src, out = workdir
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, AUTOSAVE_NAME), "w") as fh:
            fh.write("{not json")
        session = Session(src, out)
        assert session.data is not None

    def test_stepping_through_specimens_wraps(self, workdir):
        src, out = workdir
        session = Session(src, out)
        names = session.param.specimen.objects
        session.specimen = names[0]
        session.step_specimen(-1)
        assert session.specimen == names[-1]
        session.step_specimen(1)
        assert session.specimen == names[0]

    def test_moving_the_nearer_bound(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(2, 8)
        assert session.move_nearest_bound(3) == "min"
        assert session.bounds() == (3, 8)
        assert session.move_nearest_bound(9) == "max"
        assert session.bounds() == (3, 9)

    def test_nudging_a_bound(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(2, 8)
        session.nudge("min", 1)
        session.nudge("max", -1)
        assert session.bounds() == (3, 7)

    def test_flagging_a_step_reports_the_consequence(self, workdir):
        src, out = workdir
        session = Session(src, out)
        arai = session.spec.arai
        flag, notes = session.toggle_step(arai.rows[2]["i"])
        assert flag == "b"
        assert any("in-field half" in n for n in notes)

    def test_changing_the_criteria_set_changes_the_verdicts(self, study):
        study.criteria_name = "CCRIT"
        strict = sum(1 for r in study.data.results() if r.passed)
        study.criteria_name = "TTB"
        loose = sum(1 for r in study.data.results() if r.passed)
        study.criteria_name = "CCRIT"
        assert strict != loose

    def test_the_ziggie_option_adds_a_criterion(self, study):
        study.add_ziggie = True
        try:
            assert any(c.key == "Ziggie" for c in study.data.criteria.specimen)
        finally:
            study.add_ziggie = False
        assert not any(c.key == "Ziggie" for c in study.data.criteria.specimen)

    def test_the_study_summary_counts_what_the_header_shows(self, study):
        summary = study.study_summary()
        assert summary["specimens"] > 500
        assert summary["interpreted"] > 300
        assert summary["anisotropy"] > 100
        assert "IZZI" in summary["protocols"]


# ---------------------------------------------------------------------------
class TestExport:
    def test_export_writes_only_into_the_output_directory(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 6)
        written = session.export_tables(analysts="A Tester")
        assert written
        for path in written:
            assert os.path.realpath(path).startswith(os.path.realpath(out))
        assert not os.path.exists(os.path.join(src, "specimens.txt"))
        specimens = pd.read_csv(os.path.join(out, "specimens.txt"), sep="\t", skiprows=1,
                                dtype=str)
        assert (specimens["analysts"].dropna() == "A Tester").all()
        assert (specimens["software_packages"].dropna() == pint.SOFTWARE_TAG).all()

    def test_an_in_place_export_backs_up_the_originals_once(self, workdir):
        src, _ = workdir
        session = Session(src, src)
        session.set_bounds(0, 6)
        session.export_tables()
        backup = os.path.join(src, session.data.project.backup_dir_name())
        assert os.path.exists(os.path.join(backup, "measurements.txt"))
        stamp = os.path.getmtime(os.path.join(backup, "measurements.txt"))
        session.export_tables()
        assert os.path.getmtime(os.path.join(backup, "measurements.txt")) == stamp

    def test_the_written_tables_validate(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 6)
        session.export_tables()
        report = session.validate_output()
        for table, failure in report.items():
            assert not (failure or {}).get("bad_rows"), f"{table}: {failure}"

    def test_the_redo_file_round_trips(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(1, 7)
        path = session.save_redo(os.path.join(out, REDO_NAME))
        again = Session(src, os.path.join(out, "second"))
        n, problems = again.load_redo(path)
        assert n >= 1 and problems == []
        assert again.data.interpretations[session.specimen].imin == 1


# ---------------------------------------------------------------------------
class TestSpecimenView:
    def test_the_view_draws_and_follows_the_specimen(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        assert view.chooser.value == session.specimen
        assert len(view.arai.src.data["x"]) == session.spec.arai.n
        session.step_specimen(1)
        assert view.chooser.value == session.specimen

    def test_the_step_table_marks_the_selected_range(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(1, 4)
        marked = (view.steps.value["step"] == "●").sum()
        assert marked >= 4

    def test_tapping_a_point_moves_the_nearer_bound(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(2, 8)
        view._on_plot_select([3])
        assert session.bounds() == (3, 8)

    def test_a_box_selection_sets_both_bounds(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        view._on_plot_select([2, 3, 4, 5])
        assert session.bounds() == (2, 5)

    def test_the_keyboard_moves_bounds_and_specimens(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(2, 8)
        view.hotkeys.key = "]"
        view.hotkeys.n += 1
        assert session.bounds() == (3, 8)
        first = session.specimen
        view.hotkeys.key = "ArrowRight"
        view.hotkeys.n += 1
        assert session.specimen != first

    def test_the_result_line_reports_the_verdict_and_the_reason(self, study):
        view = SpecimenView(study)
        study.specimen = "hz05a1"
        assert "µT" in view.result.object
        assert "CCRIT" in view.result.object or "This study" in view.result.object

    def test_resizing_keeps_the_arai_frame_square(self, workdir):
        src, out = workdir
        view = SpecimenView(Session(src, out))
        view.size.value = 500
        view._on_size(type("E", (), {"new": 500})())
        assert view.arai.fig.frame_width == view.arai.fig.frame_height == 500

    def test_flagging_a_step_from_the_table_explains_itself(self, workdir):
        src, out = workdir
        session = Session(src, out)
        view = SpecimenView(session)
        frame = view.steps.value
        row = int(frame.index[frame["kind"] == "in field"][1])
        view.steps.selection = [row]
        view._flag_step()
        assert "marked" in view.notes.object


# ---------------------------------------------------------------------------
class TestInterpretationsView:
    def test_the_table_lists_every_interpretation_with_its_verdict(self, study):
        view = InterpretationsView(study)
        view.set_active(True)
        frame = view.table.value
        assert len(frame) == len(study.data.interpretations)
        assert set(frame["verdict"]) <= {"pass", "fail", "—"}
        assert "why" in frame.columns

    def test_a_failure_says_which_criterion_and_what_the_value_was(self, study):
        view = InterpretationsView(study)
        view.set_active(True)
        failed = view.table.value[view.table.value["verdict"] == "fail"]
        assert len(failed)
        assert failed["why"].str.contains("got").any()

    def test_bulk_flagging_and_deleting(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 5)
        view = InterpretationsView(session)
        view.set_active(True)
        view.table.selection = [0]
        name = view.table.value.iloc[0]["specimen"]
        view._flag()
        assert session.data.interpretations[name].quality == "b"
        view._delete()
        assert name not in session.data.interpretations


# ---------------------------------------------------------------------------
class TestCriteriaView:
    def test_every_statistic_is_listed_with_its_definition(self, study):
        study.specimen = "hz05a1"
        view = CriteriaView(study)
        view.set_active(True)
        html = view.table.object
        for label in ("FRAC", "DRAT", "Ziggie", "dt*"):
            assert label in html
        assert "doi.org" in html

    def test_a_not_applicable_statistic_says_why(self, study):
        study.specimen = "hz05a1"
        view = CriteriaView(study)
        view.set_active(True)
        assert "n/a" in view.table.object or "—" in view.table.object
        assert "title=" in view.table.object          # the reason is the tooltip

    def test_the_search_box_narrows_the_list(self, study):
        view = CriteriaView(study)
        view.set_active(True)
        view.search.value = "tail"
        html = view.table.object
        assert "DRAT tail" in html
        assert "GAP-MAX" not in html

    def test_the_criteria_table_shows_pass_fail_and_not_tested(self, study):
        study.criteria_name = "TTA"
        view = CriteriaView(study)
        view.set_active(True)
        results = set(view.criteria_table.value["result"])
        assert results <= {"pass", "fail", "not tested"}
        study.criteria_name = "CCRIT"

    def test_no_statistic_is_shown_as_minus_999(self, study):
        view = CriteriaView(study)
        view.set_active(True)
        assert "-999" not in view.table.object


# ---------------------------------------------------------------------------
class TestCorrectionsView:
    def test_the_table_shows_corrected_and_uncorrected(self, study):
        view = CorrectionsView(study)
        view.set_active(True)
        frame = view.table.value
        assert {"uncorrected (µT)", "corrected (µT)", "anisotropy", "cooling rate"} <= set(frame.columns)
        differing = frame[frame["uncorrected (µT)"] != frame["corrected (µT)"]]
        assert len(differing) > 10

    def test_the_detail_names_the_tensor_and_its_provenance(self, study):
        study.specimen = "hz05a1"
        view = CorrectionsView(study)
        view.set_active(True)
        assert "ATRM" in view.detail.object or "AARM" in view.detail.object
        assert "measurements" in view.detail.object
        assert "DA-" in view.detail.object

    def test_raising_the_alteration_limit_applies_more_corrections(self, study):
        view = CorrectionsView(study)
        view.set_active(True)
        applied = lambda: sum(1 for r in study.data.results()
                              if r.corrections.get("anisotropy")
                              and r.corrections["anisotropy"].applied)
        before = applied()
        view.alt_limit.value = 100.0
        after = applied()
        view.alt_limit.value = 5.0
        assert after > before

    def test_switching_a_correction_off_is_reflected(self, study):
        study.specimen = "hz05a1"
        view = CorrectionsView(study)
        view.set_active(True)
        study.set_correction("anisotropy", False)
        try:
            assert "switched off" in view.detail.object or \
                "switched off" in str(study.result.corrections["anisotropy"].message)
        finally:
            study.set_correction("anisotropy", None)


# ---------------------------------------------------------------------------
class TestGroupView:
    def test_site_means_are_listed_and_plotted(self, study):
        view = GroupView(study)
        view.set_active(True)
        assert len(view.table.value) > 3
        assert len(view.plot.src.data["x"]) >= 1
        assert "sites" in view.summary.object

    def test_rejected_specimens_are_named(self, study):
        view = GroupView(study)
        view.set_active(True)
        for site in view.group.options[:8]:
            view.group.value = site
            if "rejected" in view.members.object:
                return
        pytest.skip("no site in this study has a rejected specimen")

    def test_switching_level_changes_the_table(self, study):
        view = GroupView(study)
        view.set_active(True)
        sites = len(view.table.value)
        view.level.value = "sample"
        samples = len(view.table.value)
        view.level.value = "site"
        assert samples >= sites


# ---------------------------------------------------------------------------
class TestBicepView:
    def test_the_panel_lists_sites_and_specimens(self, study):
        view = BicepView(study)
        view.set_active(True)
        assert view.site.options
        assert len(view.specimens.value) >= 2
        assert "Stan" in view.install.object

    def test_a_bootstrap_run_produces_a_result_and_a_figure(self, study):
        view = BicepView(study)
        view.set_active(True)
        view.method.value = "bootstrap"
        view.draws.value = 200
        view._run()
        _wait(lambda: bool(study.bicep_results))
        assert study.bicep_results
        result = next(iter(study.bicep_results.values()))
        assert np.isfinite(result.b_site)
        assert "approximation" in " ".join(result.warnings)
        view.redraw()
        assert view.plot.object is not None
        assert "Cych" in view.methods.object

    def test_excluding_a_specimen_is_recorded(self, study):
        view = BicepView(study)
        view.set_active(True)
        view.specimens.selection = [0]
        view._set_included(False)
        assert view.specimens.value.iloc[0]["used"] == "no"
        assert "excluded by the analyst" in view.audit.object
        view.specimens.selection = [0]
        view._set_included(True)
        assert view.specimens.value.iloc[0]["used"] == "yes"


# ---------------------------------------------------------------------------
class TestExportView:
    def test_the_preview_switches_between_tables(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 6)
        view = ExportView(session)
        view.which.value = "specimens"
        assert "specimen" in view.preview.value.columns
        view.which.value = "criteria"
        assert "table_column" in view.preview.value.columns

    def test_writing_and_validating(self, workdir):
        src, out = workdir
        session = Session(src, out)
        session.set_bounds(0, 6)
        view = ExportView(session)
        view._export()
        assert "wrote" in view.message.object
        assert "✓" in view.report.object or "✗" in view.report.object

    def test_the_merge_policy_is_stated_on_the_pane(self, workdir):
        src, out = workdir
        view = ExportView(Session(src, out))
        panel = view.panel()
        assert "inherited" in ExportView.POLICY
        assert panel is not None

    def test_the_citations_follow_what_was_used(self, study):
        view = ExportView(study)
        assert "2013GC005135" in view.citations.object
        study.add_ziggie = True
        try:
            view._refresh()
            assert "2025JB031608" in view.citations.object
        finally:
            study.add_ziggie = False

    def test_a_figure_can_be_saved(self, study, tmp_path):
        study.specimen = "hz05a1"
        study.output_dir = str(tmp_path)
        view = ExportView(study)
        view.figure_kind.value = "arai"
        view._save_figure()
        assert any(p.suffix == ".pdf" for p in tmp_path.iterdir())


# ---------------------------------------------------------------------------
class TestPublication:
    def test_a_specimen_figure_carries_the_statistics(self, study):
        study.specimen = "hz05a1"
        figure = pub.specimen_figure(study.spec, study.bounds(), study.statistics(), study.result)
        texts = " ".join(t.get_text() for ax in figure.axes for t in ax.texts)
        assert "hz05a1" in texts
        assert "µT" in texts
        assert "FRAC" in texts

    @pytest.mark.parametrize("fmt", ["pdf", "svg", "png"])
    def test_every_format_writes(self, study, tmp_path, fmt):
        study.specimen = "hz05a1"
        figure = pub.specimen_figure(study.spec, study.bounds(), study.statistics(), study.result)
        path = tmp_path / f"spec.{fmt}"
        figure.savefig(path, format=fmt, bbox_inches="tight")
        assert path.stat().st_size > 1000

    def test_the_site_figure_marks_the_rejected_specimens(self, study):
        site = study.data.names_at("site")[0]
        results = [r for r in (study.data.result(n)
                               for n in study.data.specimens_in("site", site)) if r is not None]
        figure = pub.site_figure(site, results, accepted={results[0].specimen})
        assert figure.axes[0].get_ylabel().startswith("paleointensity")

    def test_the_study_figure_lists_the_group_means(self, study):
        figure = pub.study_figure(study.data)
        assert "means" in figure.axes[0].get_title()

    def test_figures_can_be_made_without_the_application(self):
        data = pint.PintData.from_directory(SMALL)
        name = data.specimen_names[0]
        data.set_interpretation(name, 0, 5)
        figure = pub.specimen_figure(data.specimens[name], (0, 5), data.statistics(name),
                                     data.result(name))
        assert figure is not None

    def test_a_batch_of_figures(self, tmp_path):
        data = pint.PintData.from_directory(SMALL)
        names = data.specimen_names[:3]
        for name in names:
            data.set_interpretation(name, 0, min(5, data.specimens[name].arai.n - 1))
        written = pub.all_specimen_figures(data, str(tmp_path), specimens=names)
        assert len(written) == 3


# ---------------------------------------------------------------------------
class TestDataView:
    def test_the_native_chooser_loads_what_it_returns(self, workdir, tmp_path):
        src, out = workdir
        other = tmp_path / "other"
        other.mkdir()
        shutil.copy(os.path.join(SMALL, "measurements.txt"), other)
        session = Session(src, out)
        view = DataView(session, chooser=lambda start=None: str(other), chooser_available=True)
        view._browse_native()
        import time
        for _ in range(100):
            if session.directory == str(other):
                break
            time.sleep(0.05)
        assert session.directory == str(other)

    def test_a_directory_without_measurements_is_refused(self, workdir, tmp_path):
        src, out = workdir
        session = Session(src, out)
        view = DataView(session, chooser_available=False)
        view.path.value = str(tmp_path / "empty")
        view._load()
        assert "measurements.txt" in view.message.object
        assert session.directory == src

    def test_the_tdt_importer_reports_before_it_writes(self, workdir, tmp_path):
        src, out = workdir
        session = Session(src, out)
        view = DataView(session, chooser_available=False)
        bad = tmp_path / "bad.tdt"
        bad.write_text("Thellier-tdt\n45 0 0 0 0\nSP1\t0.0\t100\t10\t30\n"
                       "SP1\t100.1\t95\t10\t30\n")
        view.tdt_path.value = str(bad)
        view._check_tdt()
        assert "errors" in view.tdt_report.object
        assert view.convert_btn.disabled
        assert len(view.tdt_table.value)

    def test_a_good_tdt_file_converts_and_opens(self, workdir, tmp_path):
        src, out = workdir
        session = Session(src, out)
        view = DataView(session, chooser_available=False)
        good = tmp_path / "SP1.tdt"
        rows = ["Thellier-tdt", "45\t0\t0\t0\t0", "SP1\t0.0\t100\t10\t30"]
        for i, temp in enumerate((100, 200, 300, 400, 500)):
            rows.append(f"SP1\t{temp}.0\t{95 - 15 * i}\t10\t30")
            rows.append(f"SP1\t{temp}.1\t{97 - 10 * i}\t12\t45")
        good.write_text("\n".join(rows) + "\n")
        view.tdt_path.value = str(good)
        view.tdt_units.value = "Am^2"
        view._check_tdt()
        assert not view.convert_btn.disabled
        view._convert_tdt()
        assert "SP1" in session.data.specimens


# ---------------------------------------------------------------------------
class TestApp:
    def test_the_template_assembles_with_its_own_assets(self, workdir):
        from pmagpy_intensity.app import ASSETS, create_app
        src, out = workdir
        template = create_app(src, out)
        assert template.title == "PmagPy Intensity"
        for name in ("favicon.png", "pmagpy_logo_white.png"):
            assert os.path.exists(os.path.join(ASSETS, name))
        assert template.session.data is not None

    def test_the_tabs_are_the_documented_ones(self, workdir):
        from pmagpy_intensity.app import create_app
        src, out = workdir
        template = create_app(src, out)
        tabs = template.main[0][1][0]
        names = list(tabs._names)
        assert names[:3] == ["Specimen", "Interpretations", "Criteria & statistics"]
        assert names[-1] == "Export"
