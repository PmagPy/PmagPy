"""
The session's file handling under the conditions a beta tester will meet.

Each test reproduces a failure found reviewing PmagPy Directions before its
beta: a failed dataset switch that sent later writes into the wrong
directory, a damaged autosave that made a study unopenable, a .redo from
another study that wiped the fits, step flags lost on restart, re-measured
steps resolved to the bad measurement, and datasets with the same folder name
sharing one output folder.
"""
import io
import os
import shutil

import pandas as pd
import pytest

import pmagpy.demag as dc
import pmagpy.magic_project as mp
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


class TestWhatTheWriterSays:
    def test_a_value_with_a_line_break_is_named_in_the_exports_messages(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        table = s.data.merged_specimens_table
        def with_a_break(*args, **kwargs):
            df = table(*args, **kwargs)
            df.loc[df.index[0], "description"] = "first line\nsecond line"
            return df
        s.data.merged_specimens_table = with_a_break
        s.export_tables()
        assert any("held a tab or a line break, written as a space" in w for w in s.data.warnings)


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

    def test_a_tab_opened_after_an_export_shares_the_dataset_of_the_tab_that_exported(self, tmp_path):
        """It read the study again and kept its own copy: the two tabs then overwrote each
        other's autosave, and an edit made in one was gone on the next start."""
        src = copy_study(tmp_path / "s")
        a = Session(src, cache=True)
        a.export_tables()                                   # the table stamp changes
        b = Session(src, cache=True)
        assert b.data is a.data
        b.specimen = b.data.specimen_names[1]
        b.toggle_step(1)
        a.specimen = a.data.specimen_names[2]
        a.toggle_step(1)                                    # a's autosave: b's flag too
        restarted = Session(src)
        for k in (1, 2):
            name = restarted.data.specimen_names[k]
            assert restarted.data.specimens[name].steps["quality"].iloc[1] == "b"


class TestTwoWindows:
    """Two windows on one study, each with its own copy of it: the autosave of the one that wrote first wins,
    and the other says so instead of writing its copy over it."""

    def flag(self, session, k, step=1):
        session.specimen = session.data.specimen_names[k]
        session.toggle_step(step)
        return session.specimen

    def bad(self, session, name, step=1):
        return session.data.specimens[name].steps["quality"].iloc[step] == "b"

    def test_a_window_whose_autosave_another_window_wrote_since_keeps_its_edits_and_says_so(self, tmp_path):
        """Each window wrote its own copy over the other's autosave; the next start restored whichever wrote last."""
        src = copy_study(tmp_path / "s")
        a, b = Session(src), Session(src)
        mine = self.flag(a, 1)
        written = open(os.path.join(src, AUTOSAVE_NAME)).read()
        theirs = self.flag(b, 2)
        assert b.status == sess.guard.ANOTHER_WINDOW
        assert open(os.path.join(src, AUTOSAVE_NAME)).read() == written      # a's autosave stands
        assert self.bad(b, theirs)                                            # b's edit is kept in memory
        self.flag(b, 3)
        assert open(os.path.join(src, AUTOSAVE_NAME)).read() == written
        self.flag(a, 4)                                                       # a goes on auto-saving
        assert a.status != sess.guard.ANOTHER_WINDOW
        reloaded = Session(src)
        assert self.bad(reloaded, mine) and not self.bad(reloaded, theirs)
        b.export_tables()                                                     # an export still writes b's edits
        now = pd.read_csv(os.path.join(src, "measurements.txt"), sep="\t", skiprows=1, dtype=str,
                          keep_default_na=False)
        steps = b.data.specimens[theirs].steps
        assert now.loc[int(steps["meas_pos"].iloc[1]), "quality"] == "b"

    def test_tabs_sharing_one_dataset_are_one_window(self, tmp_path):
        src = copy_study(tmp_path / "s")
        a = Session(src, cache=True)
        b = Session(src, cache=True)
        assert b.data is a.data
        self.flag(a, 1)
        self.flag(b, 2)
        self.flag(a, 3)
        assert sess.guard.ANOTHER_WINDOW not in (a.status, b.status)
        restarted = Session(src)
        assert all(self.bad(restarted, restarted.data.specimen_names[k]) for k in (1, 2, 3))

    def test_a_reload_after_the_warning_reads_the_other_windows_work(self, tmp_path):
        src = copy_study(tmp_path / "s")
        b = Session(src, cache=True)
        a = Session(src)                               # another window with its own copy (another server)
        mine = self.flag(a, 1)
        self.flag(b, 2)
        assert b.status == sess.guard.ANOTHER_WINDOW
        reloaded = Session(src, cache=True)
        assert reloaded.data is not b.data and self.bad(reloaded, mine)

    def test_a_cached_dataset_older_than_the_autosave_is_not_reused(self, tmp_path):
        src = copy_study(tmp_path / "s")
        b = Session(src, cache=True)
        a = Session(src)
        mine = self.flag(a, 1)
        opened = Session(src, cache=True)
        assert opened.data is not b.data and self.bad(opened, mine)

    def test_after_an_export_a_window_with_its_own_copy_does_not_overwrite_the_exporting_one(self, tmp_path):
        """C4: a tab opened after an export read the study again; the two tabs then overwrote each other's autosave."""
        src = copy_study(tmp_path / "s")
        a = Session(src)
        a.export_tables()
        b = Session(src)
        mine = self.flag(a, 1)
        theirs = self.flag(b, 2)
        assert b.status == sess.guard.ANOTHER_WINDOW
        restarted = Session(src)
        assert self.bad(restarted, mine) and not self.bad(restarted, theirs)


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

    def test_a_working_copy_is_written_on_one_click_and_says_so(self, tmp_path, monkeypatch):
        from pmagpy_directions.views import ExportView
        for var in datasets.OUTPUT_BASE_VARS:
            monkeypatch.setenv(var, "placeholder")
            monkeypatch.delenv(var)
        monkeypatch.setenv("PMAGPY_APPS_OUTPUT", str(tmp_path / "base"))
        src = copy_study(tmp_path / "s")
        before = digest(src)
        s = Session(src)
        view = ExportView(s)
        before_copy = digest(s.directory)
        view._write()
        assert "Wrote into the working copy of" in view.status.object and src in view.status.object
        assert "Confirm" not in view.write_btn.name and "data directory itself" not in view.status.object
        assert os.path.exists(os.path.join(s.directory, "specimens.txt"))
        previous = os.path.join(s.directory, Session.BACKUP_DIR, "previous")
        for name in ("measurements.txt", "sites.txt"):                       # the copy's tables are kept all the same
            if name in before_copy:
                assert digest(previous)[name] == before_copy[name]
        assert digest(src) == before

    def test_a_table_its_owner_made_read_only_is_left_as_it_is(self, tmp_path):
        """A write-protected table in a writable folder was replaced by an in-place export (and kept its mode)."""
        src = copy_study(tmp_path / "s")
        for name in ("sites.txt", "measurements.txt"):
            os.chmod(os.path.join(src, name), 0o444)
        protected = {n: open(os.path.join(src, n), "rb").read() for n in ("sites.txt", "measurements.txt")}
        s = Session(src)
        s.specimen = "jm002a1"
        s.toggle_step(3)
        for _ in range(2):                                           # export after export
            written = s.export_tables()
            assert {n: open(os.path.join(src, n), "rb").read() for n in protected} == protected
            assert os.path.join(src, "samples.txt") in written and os.path.join(src, "sites.txt") not in written
        said = [w for w in s.data.warnings if "write-protected" in w]
        assert said and said[-1].startswith(("sites.txt, measurements.txt were left as they are",
                                             "measurements.txt, sites.txt were left as they are"))
        os.chmod(os.path.join(src, "measurements.txt"), 0o644)        # made writable: the flag is still to write
        s.export_tables()
        now = pd.read_csv(os.path.join(src, "measurements.txt"), sep="\t", skiprows=1, dtype=str, keep_default_na=False)
        assert now.loc[int(s.spec.steps["meas_pos"].iloc[3]), "quality"] == "b"

    def test_an_export_to_another_folder_copies_protected_tables_writable(self, tmp_path):
        """The companion tables were copied with their read-only mode, so the new folder's measurements.txt
        was left alone (write-protected) when the analyst then worked in that folder."""
        src = copy_study(tmp_path / "s")
        for name in ("measurements.txt", "contribution.txt"):
            os.chmod(os.path.join(src, name), 0o444)
        out = str(tmp_path / "out")
        s = Session(src)
        written = s.export_tables(output_dir=out)
        for name in ("measurements.txt", "contribution.txt"):
            assert os.path.join(out, name) in written
            assert not mp.is_write_protected(os.path.join(out, name)) and mp.is_write_protected(os.path.join(src, name))
        there = Session(out)
        there.specimen = "jm002a1"
        there.toggle_step(3)
        there.export_tables()
        assert not [w for w in there.data.warnings if "write-protected" in w]
        now = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str, keep_default_na=False)
        assert now.loc[int(there.spec.steps["meas_pos"].iloc[3]), "quality"] == "b"

    def test_in_a_working_copy_a_read_only_table_is_replaced(self, tmp_path, monkeypatch):
        for var in datasets.OUTPUT_BASE_VARS:
            monkeypatch.setenv(var, "placeholder")
            monkeypatch.delenv(var)
        monkeypatch.setenv("PMAGPY_APPS_OUTPUT", str(tmp_path / "base"))
        src = copy_study(tmp_path / "s")
        s = Session(src)
        os.chmod(os.path.join(s.directory, "sites.txt"), 0o444)
        written = s.export_tables()
        assert os.path.join(s.directory, "sites.txt") in written
        assert not [w for w in s.data.warnings if "write-protected" in w]

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


class TestSwitchWithTheExportPaneBuilt:
    def test_a_dataset_loads_while_the_pane_watches_the_session(self, two):
        # a load changes version and directory in one batch; a watcher of both must take both events
        from pmagpy_directions.views import ExportView
        a, b = two
        s = Session(a)
        view = ExportView(s)
        assert s.load(b) and s.directory == b
        assert "nothing to report" in view.messages.object or view.messages.object


class TestRepeatedExports:
    def test_minimal_specimen_rows_stay_complete(self, tmp_path):
        src = copy_study(tmp_path / "s")
        os.remove(os.path.join(src, "specimens.txt"))            # a study of measurements only
        tables = []
        for _ in range(2):
            s = Session(src)
            s.data.clear_components()                            # specimens without a fit: minimal rows only
            s.export_tables()
            spec = pd.read_csv(os.path.join(src, "specimens.txt"), sep="\t", skiprows=1, dtype=str)
            tables.append(spec.drop(columns=["timestamp"], errors="ignore").dropna(axis=1, how="all"))
        first, second = tables
        assert len(first) and first["method_codes"].notna().all() and first["citations"].notna().all()
        pd.testing.assert_frame_equal(first.reset_index(drop=True), second.reset_index(drop=True))

    def test_fits_do_not_multiply_across_export_and_reopen(self, tmp_path):
        src = copy_study(tmp_path / "s")
        n = len(Session(src).data.components)
        for _ in range(3):
            s = Session(src)
            os.remove(s.autosave_path) if os.path.exists(s.autosave_path) else None
            s.export_tables(coords=(dc.COORD_SPECIMEN,))           # other systems' rows are kept
            os.remove(s.autosave_path) if os.path.exists(s.autosave_path) else None
        assert len(Session(src).data.components) == n

    def test_validating_writes_nothing(self, tmp_path):
        src = copy_study(tmp_path / "s")
        meas = os.path.join(src, "measurements.txt")
        df = pd.read_csv(meas, sep="\t", skiprows=1, dtype=str).drop(columns=["measurement"], errors="ignore")
        with open(meas, "w") as fh:
            fh.write("tab\tmeasurements\n")
            df.to_csv(fh, sep="\t", index=False)
        before = digest(src)
        Session(src).validate_output()
        assert digest(src) == before

    def test_a_legacy_redo_is_named_when_the_stored_fits_come_first(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        s.data.write_redo(os.path.join(src, "demag_gui.redo"))
        os.remove(s.autosave_path) if os.path.exists(s.autosave_path) else None
        s2 = Session(src)
        assert "imported" in s2.status and "demag_gui.redo" in s2.status and "was not read" in s2.status


class TestMeasurementsAsWritten:
    def test_an_export_without_edits_leaves_the_file_byte_for_byte(self, tmp_path):
        src = copy_study(tmp_path / "s")
        path = os.path.join(src, "measurements.txt")
        before = open(path, "rb").read()
        Session(src).export_tables()
        assert open(path, "rb").read() == before

    def test_one_flag_is_one_line(self, tmp_path):
        src = copy_study(tmp_path / "s")
        path = os.path.join(src, "measurements.txt")
        before = open(path).read().splitlines()
        s = Session(src)
        s.specimen = "jm002a1"
        s.toggle_step(3)
        s.export_tables()
        after = open(path).read().splitlines()
        assert len(after) == len(before)
        assert sum(a != b for a, b in zip(before, after)) == 1

    def test_flags_exported_elsewhere_are_still_there_after_reopening(self, tmp_path):
        src = copy_study(tmp_path / "s")
        out = str(tmp_path / "out")
        s = Session(src, out)
        s.specimen = "jm002a1"
        s.toggle_step(3)
        s.export_tables()
        s.flush_autosave()
        again = Session(src, out)
        assert again.data.specimens["jm002a1"].steps["quality"].iloc[3] == "b"

    def test_flags_written_by_the_other_application_are_kept(self, tmp_path):
        src = copy_study(tmp_path / "s")
        path = os.path.join(src, "measurements.txt")
        s = Session(src)                                          # opened before the other application writes
        df = pd.read_csv(path, sep="\t", skiprows=1, dtype=str, keep_default_na=False)
        other = df.index[df["specimen"] != "jm002a1"][10]
        lines = open(path).read().splitlines()
        header = lines[1].split("\t")
        fields = lines[other + 2].split("\t")
        fields[header.index("quality")] = "b"
        lines[other + 2] = "\t".join(fields)
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        s.specimen = "jm002a1"
        s.toggle_step(3)
        s.export_tables()
        now = pd.read_csv(path, sep="\t", skiprows=1, dtype=str, keep_default_na=False)
        assert now.loc[other, "quality"] == "b"


class TestMeasurementsChangedOnDisk:
    """Rows added to or removed from measurements.txt while the study is open: that file is left alone."""

    def rows_added(self, path, specimen="jm013d1"):
        """A converter appends a new experiment's rows to the open study's measurements.txt."""
        lines = open(path).read().splitlines()
        header = lines[1].split("\t")
        extra = [line.split("\t") for line in lines[2:] if line.split("\t")[header.index("specimen")] == specimen][:2]
        for k, fields in enumerate(extra):
            fields[header.index("measurement")] = f"new-{k}"
        with open(path, "a") as fh:
            fh.write("".join("\t".join(fields) + "\n" for fields in extra))

    def rows_removed(self, path, specimen="jm013d1", n=3):
        lines = open(path).read().splitlines()
        header = lines[1].split("\t")
        theirs = [i for i, line in enumerate(lines) if i > 1 and line.split("\t")[header.index("specimen")] == specimen]
        with open(path, "w") as fh:
            fh.write("\n".join(line for i, line in enumerate(lines) if i not in theirs[:n]) + "\n")

    @pytest.mark.parametrize("change, said", [("rows_added", "2 rows added, 0 removed"),
                                              ("rows_removed", "0 rows added, 3 removed")])
    def test_the_export_leaves_measurements_alone_and_a_reopen_writes_the_flags(self, tmp_path, change, said):
        """The rows read at opening were written back over the file: appended rows were dropped and
        deleted ones resurrected, with one vague message."""
        src = copy_study(tmp_path / "s")
        path = os.path.join(src, "measurements.txt")
        s = Session(src, cache=True)
        s.specimen = "jm002a1"
        flagged = str(s.spec.steps["measurement"].iloc[3])
        s.toggle_step(3)
        getattr(self, change)(path)
        on_disk = open(path, "rb").read()
        written = s.export_tables()
        assert open(path, "rb").read() == on_disk
        assert os.path.join(src, "specimens.txt") in written and path not in written
        message = [w for w in s.data.warnings if w.startswith("measurements.txt was not written")]
        assert len(message) == 1 and f"({said})" in message[0] and "Reopen the study" in message[0]
        assert "kept in the autosave" in message[0]
        again = Session(src, cache=True)                       # the reopen reads the file again
        assert again.data is not s.data
        steps = again.data.specimens["jm002a1"].steps
        assert steps.loc[steps["measurement"] == flagged, "quality"].iloc[0] == "b"
        again.export_tables()
        now = pd.read_csv(path, sep="\t", skiprows=1, dtype=str, keep_default_na=False)
        mine = now[(now["specimen"] == "jm002a1") & (now["measurement"] == flagged)]
        assert list(mine["quality"]) == ["b"]
        assert len(now) == len(pd.read_csv(io.BytesIO(on_disk), sep="\t", skiprows=1, dtype=str))
        assert not [w for w in again.data.warnings if "was not written" in w]

    def test_an_export_elsewhere_does_not_copy_the_changed_file_without_the_flags(self, tmp_path):
        src = copy_study(tmp_path / "s")
        out = str(tmp_path / "out")
        s = Session(src)
        s.specimen = "jm002a1"
        s.toggle_step(3)
        self.rows_added(os.path.join(src, "measurements.txt"))
        written = s.export_tables(output_dir=out)
        assert not os.path.exists(os.path.join(out, "measurements.txt"))
        assert os.path.join(out, "specimens.txt") in written

    def test_the_export_pane_says_why_and_what_to_do(self, tmp_path):
        from pmagpy_directions.views import ExportView
        src = copy_study(tmp_path / "s")
        s = Session(src)
        view = ExportView(s)
        self.rows_added(os.path.join(src, "measurements.txt"))
        view._write(confirmed=True)
        assert "measurements.txt was not written: it changed on disk since the study was opened " \
               "(2 rows added, 0 removed)" in view.status.object


class TestPolarityControls:
    def test_off_by_default_and_the_pole_is_the_one_given(self, tmp_path):
        from pmagpy_directions.views import ExportView
        view = ExportView(Session(copy_study(tmp_path / "s")))
        assert view.polarity_pole() is None and "not written" in view.polarity_note.object
        view.assign_polarity.value = True
        assert view.polarity_pole() == dc.PRESENT_NORTH_POLE
        view.polarity_reference.value = "given"
        view.pole_lat.value, view.pole_lon.value = -12.5, 305.0
        assert view.polarity_pole() == (-12.5, 305.0) and "-12.5" in view.polarity_note.object
