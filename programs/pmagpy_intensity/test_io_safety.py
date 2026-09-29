"""
The Intensity session's file handling under the conditions a beta tester will meet.

The same failures that were found in PmagPy Directions, checked here for its
sibling: a failed dataset switch, a damaged autosave or legacy .redo, a .redo
of another study, and step flags that must be restored exactly.
"""
import os
import shutil

import pytest

from pmagpy_intensity.session import AUTOSAVE_NAME, Session

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SMALL = os.path.join(REPO, "data_files", "thellier_magic")


def copy_study(target):
    target.mkdir()
    shutil.copy(os.path.join(SMALL, "measurements.txt"), target)
    return str(target)


def digest(directory):
    import hashlib
    return {n: hashlib.md5(open(os.path.join(directory, n), "rb").read()).hexdigest()
            for n in sorted(os.listdir(directory)) if os.path.isfile(os.path.join(directory, n))}


class TestFailedSwitch:
    def test_a_directory_that_fails_to_open_keeps_the_open_study(self, tmp_path):
        a, b = copy_study(tmp_path / "a"), copy_study(tmp_path / "b")
        with open(os.path.join(b, "measurements.txt"), "w") as fh:
            fh.write("tab\tmagic_measurements\ner_specimen_name\nx\n")
        before = digest(b)
        s = Session(a)
        s.auto_interpret([s.specimen])
        data, output = s.data, s.output_dir
        assert not s.load(b)
        assert "Could not open" in s.status and "MagIC 2.5" in s.status
        assert s.data is data and s.output_dir == output and s.directory == a
        s.export_tables()
        assert digest(b) == before


class TestDamagedFiles:
    def test_a_damaged_autosave_is_set_aside(self, tmp_path):
        src = copy_study(tmp_path / "s")
        with open(os.path.join(src, AUTOSAVE_NAME), "wb") as fh:
            fh.write(b"\xff{ not json")
        s = Session(src)
        assert s.data is not None and "could not be read" in s.status
        assert [n for n in os.listdir(src) if n.startswith(AUTOSAVE_NAME + ".unreadable-")]

    def test_a_damaged_legacy_redo_does_not_stop_the_study(self, tmp_path):
        src = copy_study(tmp_path / "s")
        os.mkdir(os.path.join(src, "thellier_GUI.redo"))           # unreadable: a folder by that name
        s = Session(src)
        assert s.data is not None and "could not be read" in s.status

    def test_a_redo_of_another_study_changes_nothing(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        s.auto_interpret(s.data.specimen_names[:5])
        before = {n: (i.imin, i.imax) for n, i in s.data.interpretations.items()}
        other = os.path.join(str(tmp_path), "other.redo")
        with open(other, "w") as fh:
            fh.write("not_here\t373\t773\n")
        with pytest.raises(ValueError):
            s.load_redo(other)
        assert {n: (i.imin, i.imax) for n, i in s.data.interpretations.items()} == before


class TestFlags:
    def test_flags_are_restored_exactly(self, tmp_path):
        src = copy_study(tmp_path / "s")
        s = Session(src)
        spec = s.specimen
        sequence = int(s.spec.steps["sequence"].iloc[3])
        s.toggle_step(sequence)
        s.flush_autosave()
        steps = Session(src).data.specimens[spec].steps
        assert steps.loc[steps["sequence"] == sequence, "quality"].iloc[0] == "b"
