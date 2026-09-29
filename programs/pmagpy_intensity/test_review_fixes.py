"""
Regression tests for the pre-beta review of PmagPy Intensity's application
layer: selecting a step to flag it leaves the fit alone, the script written
with an export reproduces it, an in-place export asks first, the reading and
export messages are shown, a restored criteria variant stays in force, and a
study open in both applications keeps the other's results.

Every study is a private copy under ``tmp_path``.
"""
import os
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pandas as pd
import pytest

import pmagpy.paleointensity as pint
from pmagpy import magic_project as mp
from pmagpy_intensity.session import SESSION_NAME, Session
from pmagpy_intensity.views import ExportView, SpecimenView

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SMALL = os.path.join(REPO, "data_files", "thellier_magic")


@pytest.fixture
def study(tmp_path):
    src = tmp_path / "data"
    src.mkdir()
    shutil.copy(os.path.join(SMALL, "measurements.txt"), src)
    return str(src), str(tmp_path / "out")


def read_table(path):
    return pd.read_csv(path, sep="\t", skiprows=1, dtype=str)


class TestStepTable:
    def test_selecting_a_row_to_flag_it_does_not_move_a_bound(self, study):
        src, out = study
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(3, 8)
        frame = view.steps.value
        row = int(frame.index[frame["_arai"] == 1][0])
        view._on_step_click(SimpleNamespace(row=row, column="moment"))
        assert session.bounds() == (3, 8)

    def test_the_flag_keeps_the_fit_s_temperatures(self, study):
        src, out = study
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(3, 8)
        temps = session.spec.arai.temps
        bounds = (float(temps[3]), float(temps[8]))
        frame = view.steps.value
        # the in-field half of a point before the fit
        row = int(frame.index[(frame["_arai"] == 1) & (frame["kind"] == "in field")][0])
        view.steps.selection = [row]
        view._flag_step()
        interp, arai = session.interpretation, session.spec.arai
        assert (float(arai.temps[interp.imin]), float(arai.temps[interp.imax])) == bounds

    def test_clicking_a_step_s_marker_still_moves_the_nearer_bound(self, study):
        src, out = study
        session = Session(src, out)
        view = SpecimenView(session)
        session.set_bounds(3, 8)
        frame = view.steps.value
        row = int(frame.index[frame["_arai"] == 2][0])
        assert frame.loc[row, "step"] == "○"
        view._on_step_click(SimpleNamespace(row=row, column="step"))
        assert session.bounds() == (2, 8)


class TestExportScript:
    def test_the_script_beside_the_tables_reproduces_them(self, study, tmp_path):
        src, out = study
        session = Session(src, out)
        session.autosave_enabled = False
        names = session.data.specimen_names[:6]
        session.auto_interpret(names)
        # decisions an auto-interpretation would not make
        session.data.interpretations[names[0]].quality = "b"
        session.data.set_step_quality(names[1], int(session.data.specimens[names[1]].steps["sequence"].iloc[6]), "b")
        session.criteria_name = "TTA"
        view = ExportView(session)
        view._export()
        script = os.path.join(out, "specimens_export.py")
        text = open(script).read()
        assert "data.load_session" in text and SESSION_NAME in text
        assert "auto_interpret" not in text
        target = str(tmp_path / "again")
        env = dict(os.environ, PYTHONPATH=REPO, MPLBACKEND="Agg")
        run = subprocess.run([sys.executable, script, target], capture_output=True, text=True,
                             env=env, timeout=600)
        assert run.returncode == 0, run.stderr[-2000:]
        exported = read_table(os.path.join(out, "specimens.txt"))
        again = read_table(os.path.join(target, "specimens.txt"))
        key = ["specimen", "meas_step_min", "meas_step_max", "int_abs", "result_quality", "method_codes"]
        assert set(again.columns) == set(exported.columns)
        pd.testing.assert_frame_equal(exported[key].sort_values("specimen").reset_index(drop=True),
                                      again[key].sort_values("specimen").reset_index(drop=True))
        # and nothing was written over the tables it describes
        assert not os.path.exists(os.path.join(out, "reproduced"))


class TestExportPane:
    def test_an_in_place_export_asks_first(self, study):
        src, _ = study
        session = Session(src, src)
        session.autosave_enabled = False
        session.auto_interpret(session.data.specimen_names[:2])
        view = ExportView(session)
        view._export()
        assert not os.path.exists(os.path.join(src, "specimens.txt"))
        assert "Confirm" in view.export_btn.name and "data directory itself" in view.message.object
        view._export()
        assert os.path.exists(os.path.join(src, "specimens.txt"))
        assert view.export_btn.name == "Write MagIC tables"

    def test_the_messages_are_shown(self, study):
        src, out = study
        session = Session(src, out)
        session.data.warnings.append("a reading note the analyst must see")
        view = ExportView(session)
        view._refresh()
        assert "a reading note the analyst must see" in view.messages.object


class TestRestoredCriteria:
    def test_a_preset_with_ziggie_added_is_restored_as_used(self, study):
        src, out = study
        session = Session(src, out)
        session.param.update(criteria_name="TTA", add_ziggie=True)
        session.set_bounds(0, 5)                     # autosaves
        again = Session(src, out)
        assert again.criteria_name == "TTA" and again.add_ziggie
        assert any(c.key == "Ziggie" for c in again.data.criteria.specimen)

    def test_a_criteria_variant_is_restored_from_the_session(self, study):
        src, out = study
        session = Session(src, out)
        variant = pint.CriteriaSet("TTA", specimen=(pint.Criterion("beta", "<=", 0.05),))
        session.data.set_criteria(variant)
        session.set_bounds(0, 5)
        again = Session(src, out)
        assert again.data.criteria.specimen == variant.specimen


class TestTwoApplicationsOnOneStudy:
    def test_a_stale_intensity_export_keeps_what_directions_exported_since(self, study):
        from pmagpy_directions.session import Session as DirectionsSession
        src, _ = study
        intensity = Session(src, src)             # opened first, before Directions writes
        intensity.autosave_enabled = False
        intensity.auto_interpret(intensity.data.specimen_names[:3])
        directions = DirectionsSession(src)
        directions.autosave_enabled = False
        fitted = directions.specimen
        directions.add_component("A", 1, 5)
        directions.export_tables(levels=())
        intensity.export_tables(levels=())
        spec = read_table(os.path.join(src, "specimens.txt"))
        mine = spec[(spec["specimen"] == fitted) & pd.to_numeric(spec.get("dir_dec"), errors="coerce").notna()
                    & ~mp.intensity_rows(spec)]
        assert len(mine) >= 1, "the Directions fit was deleted by the stale Intensity export"
        assert mp.intensity_rows(spec).sum() == 3

    def test_a_stale_directions_export_keeps_what_intensity_exported_since(self, study):
        from pmagpy_directions.session import Session as DirectionsSession
        src, _ = study
        directions = DirectionsSession(src)
        directions.autosave_enabled = False
        directions.add_component("A", 1, 5)
        intensity = Session(src, src)
        intensity.autosave_enabled = False
        intensity.auto_interpret(intensity.data.specimen_names[:3])
        intensity.export_tables(levels=())
        directions.export_tables(levels=())
        spec = read_table(os.path.join(src, "specimens.txt"))
        assert mp.intensity_rows(spec).sum() == 3
