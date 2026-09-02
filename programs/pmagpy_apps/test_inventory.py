"""Tests for the directory inventory Home is drawn from.

    pytest programs/pmagpy_apps -q
"""
import os
import shutil

import pytest

pytest.importorskip("pandas")

from pmagpy_panel import datasets  # noqa: E402
from pmagpy_apps.inventory import take_inventory  # noqa: E402

MCMURDO = datasets.example_dir("McMurdo")
DATA_FILES = os.path.dirname(os.path.dirname(MCMURDO))
OSLER = os.path.join(DATA_FILES, "3_0", "Osler")         # sites and locations only, so not an "example dir"
CIT = os.path.join(DATA_FILES, "convert_2_magic", "cit_magic", "PI47")


class TestMagicDirectory:
    inv = take_inventory(MCMURDO)

    def test_counts_come_from_the_tables(self):
        assert self.inv.is_magic and not self.inv.is_empty
        assert self.inv.counts == {"locations": 1, "sites": 141, "samples": 1418, "specimens": 1046,
                                   "measurements": 25470}
        assert self.inv.tables["measurements"].rows == 25470
        assert "contribution" in self.inv.tables      # read, for the id — but never listed

    def test_experiment_kinds_are_read_from_the_method_codes(self):
        kinds = {k.key: k for k in self.inv.kinds}
        assert list(kinds) == ["demag", "pi", "hys", "aniso"]     # in the order the rules are declared
        assert kinds["demag"].specimens == 639 and kinds["demag"].details == ["AF", "thermal"]
        assert kinds["pi"].label == "Thellier" and kinds["pi"].details == ["IZZI", "ZI", "IZ"]
        assert kinds["aniso"].detail == "ARM"
        assert self.inv.has("demag", "pi") and not self.inv.has("forc")

    def test_contribution_and_analysis_state(self):
        assert self.inv.contribution["id"] == "13436"           # not "13436.0"
        assert self.inv.contribution["reference"].startswith("10.1029/")
        assert self.inv.analysis["specimens_interpreted"] == 1002
        assert self.inv.analysis["site_means"] == 133

    def test_gaps_are_ranked_largest_first(self):
        assert [g.label for g in self.inv.gaps][0] == "site ages"
        assert self.inv.gaps[0].n == 8
        assert all(a.n >= b.n for a, b in zip(self.inv.gaps, self.inv.gaps[1:]))

    def test_files_beside_the_tables_are_listed_without_a_role(self):
        names = [f.name for f in self.inv.files]
        assert "extra_specimens.txt" in names
        assert all(f.role == "" for f in self.inv.files)


class TestOtherDirectories:
    def test_cit_lab_files_are_recognised(self, tmp_path):
        for name in os.listdir(CIT):
            if not name.endswith(".txt"):
                shutil.copy(os.path.join(CIT, name), tmp_path)
        inv = take_inventory(str(tmp_path))
        assert not inv.is_magic and not inv.is_empty
        assert inv.format_guess == "CIT"
        roles = {f.name: f.role for f in inv.files}
        assert roles["PI47-.sam"] == "CIT index"
        assert roles["PI47-1a"] == "CIT specimen"

    def test_tables_without_measurements_are_not_a_magic_directory(self):
        inv = take_inventory(OSLER)
        assert "sites" in inv.tables and not inv.is_magic

    def test_an_empty_directory(self, tmp_path):
        inv = take_inventory(str(tmp_path))
        assert inv.is_empty and inv.error == ""
        assert inv.counts == {} and inv.kinds == [] and inv.files == []

    def test_a_missing_directory_is_reported_not_raised(self, tmp_path):
        inv = take_inventory(str(tmp_path / "nowhere"))
        assert "not a directory" in inv.error
