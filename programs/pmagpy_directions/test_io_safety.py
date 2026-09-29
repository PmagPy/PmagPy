"""
The session's file handling under the conditions a beta tester will meet.

Each test reproduces a failure found reviewing PmagPy Directions before its
beta: a failed dataset switch that sent later writes into the wrong
directory, a damaged autosave that made a study unopenable, a .redo from
another study that wiped the fits, step flags lost on restart, re-measured
steps resolved to the bad measurement, and datasets with the same folder name
sharing one output folder.
"""
import os
import shutil

import pandas as pd
import pytest

import pmagpy.demag as dc
from pmagpy_directions import session as sess
from pmagpy_directions.session import AUTOSAVE_NAME, Session
from pmagpy_panel import datasets

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DMAG_DIR = os.path.join(REPO, "data_files", "dmag_magic")


def copy_study(target):
    shutil.copytree(DMAG_DIR, target)
    for stray in target.glob("*.redo"):
        stray.unlink()
    return str(target)


@pytest.fixture
def two(tmp_path):
    return copy_study(tmp_path / "a"), copy_study(tmp_path / "b")


def digest(directory):
    import hashlib
    return {n: hashlib.md5(open(os.path.join(directory, n), "rb").read()).hexdigest()
            for n in sorted(os.listdir(directory)) if os.path.isfile(os.path.join(directory, n))}


class TestFailedSwitch:
    def test_a_directory_that_fails_to_open_is_never_written_to(self, two):
        a, b = two
        with open(os.path.join(b, "measurements.txt"), "w") as fh:
            fh.write("this is not a MagIC table\n")
        before = digest(b)
        s = Session(a)
        s.add_component("Z", 1, 5)
        assert not s.load(b)
        assert "Could not open" in s.status
        assert s.directory == a and s.output_dir == a
        s.add_component("Y", 2, 6)                # an edit and an export of the dataset still open ...
        s.export_tables()
        assert digest(b) == before                # ... go to that dataset, not to the one that failed
        assert os.path.exists(os.path.join(a, AUTOSAVE_NAME))


class TestDamagedAutosave:
    @pytest.mark.parametrize("content", [b"\xff\xfe\x00garbage", b"{not json", b"[1, 2, 3]"])
    def test_the_study_still_opens_and_the_file_is_set_aside(self, tmp_path, content):
        src = copy_study(tmp_path / "s")
        with open(os.path.join(src, AUTOSAVE_NAME), "wb") as fh:
            fh.write(content)
        s = Session(src)
        assert s.data is not None and len(s.data.components) > 100      # the published fits instead
        assert "could not be read" in s.status and "imported" in s.status
        assert not os.path.exists(os.path.join(src, AUTOSAVE_NAME))
        assert [n for n in os.listdir(src) if n.startswith(AUTOSAVE_NAME + ".unreadable-")]

    def test_an_empty_autosave_does_not_hide_the_published_fits(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        s.data.clear_components()
        s.autosave()
        s2 = Session(src)
        assert len(s2.data.components) > 100 and "passed over" in s2.status


class TestRedoOfAnotherStudy:
    def test_load_redo_replace_leaves_the_fits_when_nothing_matches(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        before = [(c.specimen, c.name, c.imin, c.imax) for c in s.data.components]
        other = os.path.join(str(tmp_path), "other.redo")
        with open(other, "w") as fh:
            fh.write("not_here\tDE-BFL\t0\t0.02\tA\t\tg\n")
        with pytest.raises(ValueError, match="no fits of specimens in this study"):
            s.load_redo(other)
        assert [(c.specimen, c.name, c.imin, c.imax) for c in s.data.components] == before

    def test_an_unreadable_redo_leaves_the_fits(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        n = len(s.data.components)
        with pytest.raises(OSError):
            s.load_redo(str(tmp_path))                  # a folder, as a typed path can be
        assert len(s.data.components) == n


class TestFlagsSurviveARestart:
    def test_a_step_flagged_bad_is_bad_after_reopening(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        s.specimen = "jm002a1"
        n_good = int((s.spec.steps["quality"] == "g").sum())
        s.toggle_step(3)
        s.flush_autosave()
        s2 = Session(src)
        steps = s2.data.specimens["jm002a1"].steps
        assert steps["quality"].iloc[3] == "b" and int((steps["quality"] == "g").sum()) == n_good - 1
        assert "restored" in s2.status

    def test_a_step_flagged_good_again_stays_good(self, tmp_path):
        src = copy_study(tmp_path / "s")
        meas = os.path.join(src, "measurements.txt")
        df = pd.read_csv(meas, sep="\t", skiprows=1, dtype=str)
        first = df.index[(df["specimen"] == "jm002a1")][2]
        df.loc[first, "quality"] = "b"
        with open(meas, "w") as fh:
            fh.write("tab\tmeasurements\n")
            df.to_csv(fh, sep="\t", index=False)
        s = Session(src)
        s.specimen = "jm002a1"
        index = int(s.spec.steps.index[s.spec.steps["quality"] == "b"][0])
        s.toggle_step(index)
        s.flush_autosave()
        assert Session(src).data.specimens["jm002a1"].steps["quality"].iloc[index] == "g"


class TestRemeasuredSteps:
    def test_a_bound_on_a_remeasured_step_takes_the_good_measurement(self):
        steps = pd.DataFrame({"sequence": range(4), "treat_type": ["NRM", "T", "T", "T"],
                              "treat_value": [0.0, 373.0, 473.0, 473.0], "treat_unit": ["K"] * 4,
                              "quality": ["g", "g", "b", "g"], "label": ["NRM", "100°C", "200°C", "200°C"],
                              "measurement": ["m0", "m1", "m2", "m3"]})
        data = dc.DemagData.__new__(dc.DemagData)
        data.warnings = []
        data.specimens = {"x": dc.SpecimenData("x", "", "", "", steps)}
        assert data.step_index_for_value("x", 473.0, "K") == 3
        assert data.step_index_for_value("x", 373.0, "K") == 1
        # the legacy mixed-protocol convention: a tesla value labelled K on a thermal-only specimen
        # finds nothing close and says so
        data.step_index_for_value("x", 523.0, "K")
        assert data.warnings and "no step at 250°C" in data.warnings[0]

    def test_bounds_in_display_units_are_understood(self):
        steps = pd.DataFrame({"sequence": range(3), "treat_type": ["NRM", "AF", "AF"],
                              "treat_value": [0.0, 0.01, 0.02], "treat_unit": ["T"] * 3,
                              "quality": ["g"] * 3, "label": ["NRM", "10 mT", "20 mT"],
                              "measurement": ["m0", "m1", "m2"]})
        data = dc.DemagData.__new__(dc.DemagData)
        data.warnings = []
        data.specimens = {"x": dc.SpecimenData("x", "", "", "", steps)}
        assert data.step_index_for_value("x", 20, "mT") == 2
        assert data.step_index_for_value("x", 0.02, "K") == 2         # tesla value mislabelled
        assert not data.warnings


class TestEditsOnDisk:
    def test_a_table_changed_on_disk_is_read_again(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src, cache=True)
        first = s.data
        s2 = Session(src, cache=True)
        assert s2.data is first                              # unchanged files: the dataset in memory
        path = os.path.join(src, "samples.txt")
        with open(path, "a") as fh:
            fh.write("\n")
        os.utime(path, None)
        s3 = Session(src, cache=True)
        assert s3.data is not first


class TestOutputFolders:
    def test_studies_with_the_same_folder_name_get_their_own_output(self, tmp_path):
        a = str(tmp_path / "one" / "MagIC")
        b = str(tmp_path / "two" / "MagIC")
        base = str(tmp_path / "out")
        oa, ob = datasets.default_output_dir(a, base), datasets.default_output_dir(b, base)
        assert oa != ob and os.path.basename(oa).startswith("MagIC-")
        assert datasets.default_output_dir(a, base) == oa           # and the same one every time


class TestExportPane:
    def test_an_in_place_export_asks_first(self, tmp_path):
        from pmagpy_directions.views import ExportView
        src = copy_study(tmp_path / "s")
        before = digest(src)
        view = ExportView(Session(src))
        view._write()
        assert "writes into the data directory itself" in view.status.object
        assert digest(src) == before                                   # nothing written yet
        view._write()
        assert "Wrote:" in view.status.object
        assert os.path.exists(os.path.join(src, Session.BACKUP_DIR, "specimens.txt"))

    def test_the_output_field_does_not_move_the_autosave(self, tmp_path):
        from pmagpy_directions.views import ExportView
        src = copy_study(tmp_path / "s")
        s = Session(src)
        view = ExportView(s)
        view.output_dir.value = str(tmp_path / "elsewhere")
        view._write()
        assert os.path.exists(tmp_path / "elsewhere" / "specimens.txt")
        assert s.output_dir == src and s.autosave_path.startswith(src)

    def test_a_redo_of_another_study_is_refused_with_a_message(self, tmp_path):
        from pmagpy_directions.views import ExportView
        src = copy_study(tmp_path / "s")
        s = Session(src)
        n = len(s.data.components)
        other = tmp_path / "other.redo"
        other.write_text("not_here\tDE-BFL\t0\t0.02\tA\t\tg\n")
        view = ExportView(s)
        view.redo_path.value = str(other)
        view._load_redo()
        assert "Not loaded" in view.status.object and len(s.data.components) == n

    def test_messages_from_reading_are_shown(self, tmp_path):
        from pmagpy_directions.views import ExportView
        src = copy_study(tmp_path / "s")
        with open(os.path.join(src, "locations.txt"), "w") as fh:
            fh.write("tab\tsites\nsite\nx\n")                         # the wrong kind of table
        s = Session(src)
        assert "Export → Messages" in s.status
        view = ExportView(s)
        assert "locations.txt was not read" in view.messages.object


class TestCriteria:
    def test_a_criterion_that_cannot_be_evaluated_is_set_aside(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        criteria = pd.DataFrame({"criterion": ["DE-SPEC", "DE-SPEC"],
                                 "table_column": ["specimens.dir_mad_free", "specimens.dir_n_measurements"],
                                 "criterion_operation": ["=<", ">="], "criterion_value": ["5°", "four"]})
        assert s.data.set_criteria(criteria) == 1
        assert any("cannot be evaluated" in w for w in s.data.warnings)
        assert len(s.data.failing_components()) < len(s.data.components)


class TestFailurePage:
    def test_a_directory_that_cannot_be_opened_offers_the_chooser(self, tmp_path):
        from pmagpy_directions.app import create_app
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / "measurements.txt").write_text("nothing here\n")
        page = create_app(str(bad))
        text = str(page[0].object)
        assert "Could not open" in text and "not a MagIC table" in text
