"""
Good/bad flags on a study that both applications work on.

Each application writes only the flags it changed since the file was last in
step with it, onto measurements.txt as it is on disk: a step flagged good
again after an export is written good, and a flag the other application set
in the meantime is not undone -- neither by an export nor by restoring a
session. (Found in the final pre-beta check: after "flag, export, unflag,
export" the file kept the flag, and PmagPy Intensity reopening with its
autosave erased a flag PmagPy Directions had set on a zero-field step.)
"""
import os
import shutil

import pandas as pd

from pmagpy_directions.session import Session as DirectionsSession
from pmagpy_intensity.session import Session as IntensitySession

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SMALL = os.path.join(REPO, "data_files", "thellier_magic")


def study(tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    shutil.copy(os.path.join(SMALL, "measurements.txt"), src)
    return str(src)


def disk_flag(src, pos):
    df = pd.read_csv(os.path.join(src, "measurements.txt"), sep="\t", skiprows=1, dtype=str, keep_default_na=False)
    return df["quality"].iloc[pos]


class TestUnflagAfterExport:
    def test_intensity(self, tmp_path):
        src = study(tmp_path)
        s = IntensitySession(src)
        sequence = int(s.spec.steps["sequence"].iloc[3])
        pos = int(s.spec.steps["meas_pos"].iloc[3])
        s.toggle_step(sequence)
        s.export_tables()
        assert disk_flag(src, pos) == "b"
        s.toggle_step(sequence)
        s.export_tables()
        assert disk_flag(src, pos) == "g"
        s.flush_autosave()
        steps = IntensitySession(src).data.specimens[s.specimen].steps
        assert steps.loc[steps["meas_pos"] == pos, "quality"].iloc[0] == "g"

    def test_directions(self, tmp_path):
        src = study(tmp_path)
        s = DirectionsSession(src)
        pos = int(s.spec.steps["meas_pos"].iloc[3])
        s.toggle_step(3)
        s.export_tables()
        assert disk_flag(src, pos) == "b"
        s.toggle_step(3)
        s.export_tables()
        assert disk_flag(src, pos) == "g"
        s.flush_autosave()
        again = DirectionsSession(src)
        assert again.data.specimens[s.specimen].steps["quality"].iloc[3] == "g"


class TestTheOtherApplicationsFlags:
    def test_intensity_reopening_keeps_a_directions_flag(self, tmp_path):
        src = study(tmp_path)
        pint = IntensitySession(src)                          # works first, and leaves an autosave
        pint.auto_interpret([pint.specimen])
        pint.flush_autosave()
        pint.autosave()
        d = DirectionsSession(src)                            # then flags a zero-field step of the same specimen
        d.specimen = pint.specimen
        pos = int(d.spec.steps["meas_pos"].iloc[2])
        d.toggle_step(2)
        d.export_tables()
        assert disk_flag(src, pos) == "b"
        again = IntensitySession(src)                         # restores its autosave onto the file as it is now
        steps = again.data.specimens[pint.specimen].steps
        mine = steps["meas_pos"] == pos
        assert mine.any()                                     # a zero-field step: both applications have it
        assert steps.loc[mine, "quality"].iloc[0] == "b"
        again.export_tables()
        assert disk_flag(src, pos) == "b"


class TestOpeningMakesNoInterpretation:
    def test_equal_bounds_from_the_selectors_are_ignored(self, tmp_path):
        from pmagpy_intensity.views import SpecimenView
        src = study(tmp_path)
        s = IntensitySession(src)
        s.data.interpretations.clear()
        view = SpecimenView(s)
        view.tmin.value = view.tmax.value = list(view.tmin.options.values())[0]
        view._on_bound(None)
        assert s.specimen not in s.data.interpretations
