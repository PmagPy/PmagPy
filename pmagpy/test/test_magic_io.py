"""
Reading and writing MagIC 3 table files without harming them.

Regression tests for the file-handling problems found reviewing PmagPy
Directions and PmagPy Intensity before their beta: opening a study rewrote its
measurements.txt, names that look like numbers were changed, tables saved in a
Windows code page were dropped or garbled, and a failed export left a
half-written contribution behind.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from pmagpy import magic_project as mp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DMAG_DIR = os.path.join(REPO, "data_files", "dmag_magic")


def write_table(path, header, rows, table, encoding="utf-8"):
    lines = [f"tab\t{table}", "\t".join(header)] + ["\t".join(str(v) for v in r) for r in rows]
    with open(path, "w", encoding=encoding, newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


@pytest.fixture
def study(tmp_path):
    """A copy of the dmag_magic example contribution."""
    src = tmp_path / "study"
    shutil.copytree(DMAG_DIR, src)
    return str(src)


def unnamed_measurements(directory):
    """Strip the ``measurement`` column, as many older contributions lack it."""
    path = os.path.join(directory, "measurements.txt")
    df = pd.read_csv(path, sep="\t", skiprows=1, dtype=str)
    df = df.drop(columns=["measurement"], errors="ignore")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("tab\tmeasurements\n")
        df.to_csv(fh, sep="\t", index=False)
    return path


class TestReadingWritesNothing:
    def test_a_measurements_table_without_names_is_not_rewritten(self, study):
        path = unnamed_measurements(study)
        before = open(path, "rb").read()
        con = mp.read_contribution(study)
        assert open(path, "rb").read() == before
        meas = con.tables["measurements"].df
        assert meas["measurement"].notna().all() and meas["measurement"].is_unique

    def test_a_read_only_study_can_be_opened(self, study):
        unnamed_measurements(study)
        mode = os.stat(study).st_mode
        for name in os.listdir(study):
            os.chmod(os.path.join(study, name), 0o444)
        os.chmod(study, 0o555)
        try:
            con = mp.read_contribution(study)
            assert len(con.tables["measurements"].df)
        finally:
            os.chmod(study, mode)

    def test_nothing_is_written_anywhere(self, study, tmp_path, monkeypatch):
        unnamed_measurements(study)
        elsewhere = tmp_path / "cwd"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        listing = sorted(os.listdir(study))
        mp.read_contribution(study)
        assert sorted(os.listdir(study)) == listing and os.listdir(elsewhere) == []


class TestNamesStayNames:
    def test_names_that_look_like_numbers_are_kept_as_written(self, tmp_path):
        d = str(tmp_path)
        write_table(os.path.join(d, "measurements.txt"),
                    ["measurement", "experiment", "specimen", "method_codes", "dir_dec", "dir_inc", "magn_moment"],
                    [["m1", "e1", "001", "LT-NO", 10, 20, 1e-6], ["m2", "e1", "001", "LT-AF-Z", 11, 21, 5e-7]],
                    "measurements")
        write_table(os.path.join(d, "specimens.txt"), ["specimen", "sample"], [["001", "1.10"]], "specimens")
        write_table(os.path.join(d, "samples.txt"), ["sample", "site", "azimuth", "dip"],
                    [["1.10", "1e3", 10, -30], ["", "", "", ""]], "samples")
        con = mp.read_contribution(d)
        assert list(con.tables["measurements"].df["specimen"]) == ["001", "001"]
        assert list(con.tables["specimens"].df["sample"]) == ["1.10"]
        assert list(con.tables["samples"].df["site"].dropna()) == ["1e3"]


class TestEncodings:
    def test_a_windows_table_is_read_and_reported(self, study):
        path = os.path.join(study, "sites.txt")
        df = pd.read_csv(path, sep="\t", skiprows=1, dtype=str)
        df.loc[df.index[0], "site"] = df.loc[df.index[0], "site"]
        df["description"] = "Müller's section"
        with open(path, "w", encoding="cp1252") as fh:
            fh.write("tab\tsites\n")
            df.to_csv(fh, sep="\t", index=False)
        warnings = []
        con = mp.read_contribution(study, warnings=warnings)
        assert "sites" in con.tables
        assert (con.tables["sites"].df["description"] == "Müller's section").all()
        assert any("sites.txt is not UTF-8" in w for w in warnings)

    def test_tables_are_written_as_utf8_whatever_the_locale(self, tmp_path, monkeypatch):
        import locale
        monkeypatch.setattr(locale, "getpreferredencoding", lambda *a, **k: "latin-1")
        path = os.path.join(str(tmp_path), "sites.txt")
        mp.magic_write(path, pd.DataFrame({"site": ["a"], "description": ["κ = 42, Müller"]}), "sites")
        text = open(path, "rb").read().decode("utf-8")
        assert text.startswith("tab\tsites\n") and "κ = 42, Müller" in text


class TestBrokenTables:
    @pytest.mark.parametrize("content", ["", "tab\tsamples\n", "tab\tsamples"])
    def test_an_empty_optional_table_does_not_stop_the_study(self, study, content):
        with open(os.path.join(study, "samples.txt"), "w") as fh:
            fh.write(content)
        con = mp.read_contribution(study)
        assert "measurements" in con.tables

    def test_a_table_of_the_wrong_kind_is_left_out_and_named(self, study):
        shutil.copy(os.path.join(study, "sites.txt"), os.path.join(study, "samples.txt"))
        warnings = []
        con = mp.read_contribution(study, warnings=warnings)
        assert "samples" not in con.tables
        assert any(w.startswith("samples.txt was not read") and "'sites'" in w for w in warnings)

    def test_a_magic_2_5_study_says_so(self, tmp_path):
        d = str(tmp_path)
        write_table(os.path.join(d, "measurements.txt"), ["er_specimen_name"], [["a"]], "magic_measurements")
        with pytest.raises(mp.MagicReadError, match="MagIC 2.5"):
            mp.read_contribution(d)


class TestAtomicWrites:
    def test_a_failed_write_leaves_the_old_file(self, tmp_path, monkeypatch):
        path = os.path.join(str(tmp_path), "specimens.txt")
        mp.atomic_write_text(path, "old\n")

        def fail(*args, **kwargs):
            raise OSError("disk full")
        monkeypatch.setattr(os, "replace", fail)
        with pytest.raises(OSError):
            mp.atomic_write_text(path, "new\n")
        assert open(path).read() == "old\n"
        assert os.listdir(str(tmp_path)) == ["specimens.txt"]          # no temporary file left behind


    def test_a_new_file_gets_the_permissions_open_would_give_it(self, tmp_path):
        umask = os.umask(0o022)
        try:
            path = os.path.join(str(tmp_path), "sites.txt")
            mp.atomic_write_text(path, "new\n")
        finally:
            os.umask(umask)
        assert os.stat(path).st_mode & 0o777 == 0o644

    def test_a_replaced_file_keeps_its_permissions(self, tmp_path):
        path = os.path.join(str(tmp_path), "sites.txt")
        with open(path, "w") as fh:
            fh.write("old\n")
        os.chmod(path, 0o664)
        mp.atomic_write_text(path, "new\n")
        assert os.stat(path).st_mode & 0o777 == 0o664


class TestStagedExport:
    def test_the_tables_an_export_replaces_keep_their_permissions(self, tmp_path):
        out = str(tmp_path / "out")
        os.makedirs(out)
        with open(os.path.join(out, "sites.txt"), "w") as fh:
            fh.write("v0")
        os.chmod(os.path.join(out, "sites.txt"), 0o664)
        umask = os.umask(0o022)
        try:
            with mp.StagedExport(out, backup=os.path.join(out, "backup"), originals=True) as stage:
                mp.atomic_write_text(os.path.join(stage.dir, "sites.txt"), "v1")
                mp.atomic_write_text(os.path.join(stage.dir, "samples.txt"), "new")
        finally:
            os.umask(umask)
        assert os.stat(os.path.join(out, "sites.txt")).st_mode & 0o777 == 0o664
        assert os.stat(os.path.join(out, "samples.txt")).st_mode & 0o777 == 0o644

    def test_all_or_nothing(self, tmp_path):
        out = str(tmp_path / "out")
        os.makedirs(out)
        for name in ("specimens.txt", "sites.txt"):
            with open(os.path.join(out, name), "w") as fh:
                fh.write(f"original {name}")
        with pytest.raises(RuntimeError):
            with mp.StagedExport(out, backup=os.path.join(out, "backup"), originals=True) as stage:
                mp.atomic_write_text(os.path.join(stage.dir, "specimens.txt"), "new specimens")
                raise RuntimeError("the sites table could not be made")
        assert open(os.path.join(out, "specimens.txt")).read() == "original specimens.txt"
        assert sorted(os.listdir(out)) == ["sites.txt", "specimens.txt"]

    def test_originals_are_kept_once_and_the_previous_export_every_time(self, tmp_path):
        out = str(tmp_path / "out")
        backup = os.path.join(out, "backup")
        os.makedirs(out)
        with open(os.path.join(out, "sites.txt"), "w") as fh:
            fh.write("v0")
        for version in ("v1", "v2"):
            with mp.StagedExport(out, backup=backup, originals=True) as stage:
                mp.atomic_write_text(os.path.join(stage.dir, "sites.txt"), version)
        assert open(os.path.join(out, "sites.txt")).read() == "v2"
        assert open(os.path.join(backup, "sites.txt")).read() == "v0"
        assert open(os.path.join(backup, "previous", "sites.txt")).read() == "v1"
        assert stage.written == [os.path.join(out, "sites.txt")]
        assert not [n for n in os.listdir(out) if n.startswith(".staging")]

    def test_read_only_tables_can_be_exported_again_and_again(self, tmp_path):
        out = str(tmp_path / "out")
        backup = os.path.join(out, "backup")
        os.makedirs(out)
        with open(os.path.join(out, "sites.txt"), "w") as fh:
            fh.write("v0")
        os.chmod(os.path.join(out, "sites.txt"), 0o444)
        for version in ("v1", "v2", "v3"):
            with mp.StagedExport(out, backup=backup, originals=True) as stage:
                mp.atomic_write_text(os.path.join(stage.dir, "sites.txt"), version)
        assert open(os.path.join(out, "sites.txt")).read() == "v3"
        assert open(os.path.join(backup, "sites.txt")).read() == "v0"
        assert open(os.path.join(backup, "previous", "sites.txt")).read() == "v2"

    def test_a_backup_cut_short_leaves_no_truncated_original(self, tmp_path, monkeypatch):
        """A full disk part way through the backup copy left half a file as the kept "original",
        which the next export then trusted (it is written only once)."""
        import errno
        import shutil
        out = str(tmp_path / "out")
        backup = os.path.join(out, "backup")
        os.makedirs(out)
        with open(os.path.join(out, "measurements.txt"), "w") as fh:
            fh.write("v0" * 1000)
        real_copy2 = shutil.copy2

        def half_then_full(src, dst, *args, **kwargs):
            with open(src, "rb") as a, open(dst, "wb") as b:
                b.write(a.read()[:100])
            raise OSError(errno.ENOSPC, "No space left on device")
        monkeypatch.setattr(mp.shutil, "copy2", half_then_full)
        with pytest.raises(OSError):
            with mp.StagedExport(out, backup=backup, originals=True) as stage:
                mp.atomic_write_text(os.path.join(stage.dir, "measurements.txt"), "v1")
        assert open(os.path.join(out, "measurements.txt")).read() == "v0" * 1000
        assert not os.path.exists(os.path.join(backup, "measurements.txt"))
        assert not [n for n in os.listdir(backup) if n.endswith(".tmp")]
        monkeypatch.setattr(mp.shutil, "copy2", real_copy2)
        with mp.StagedExport(out, backup=backup, originals=True) as stage:
            mp.atomic_write_text(os.path.join(stage.dir, "measurements.txt"), "v1")
        assert open(os.path.join(backup, "measurements.txt")).read() == "v0" * 1000

    def test_staging_folders_left_by_a_killed_export_are_removed_and_live_ones_kept(self, tmp_path):
        """A kill -9 during an export left its .staging-* folder (a full set of tables) for good."""
        import json
        import socket
        import subprocess
        import sys
        import time
        out = str(tmp_path / "out")
        os.makedirs(out)
        ended = subprocess.Popen([sys.executable, "-c", "pass"])
        ended.wait()

        def staging(name, owner=None, age=0.0):
            path = os.path.join(out, name)
            os.makedirs(path)
            with open(os.path.join(path, "specimens.txt"), "w") as fh:
                fh.write("tab\tspecimens\n")
            if owner is not None:
                with open(os.path.join(path, mp.STAGING_OWNER), "w") as fh:
                    json.dump({"pid": owner, "host": socket.gethostname(), "started": time.time()}, fh)
            if age:
                then = time.time() - age
                for entry in [path] + [os.path.join(path, n) for n in os.listdir(path)]:
                    os.utime(entry, (then, then))
            return path

        killed = staging(".staging-killed", owner=ended.pid)
        live = staging(".staging-live", owner=os.getpid())
        old = staging(".staging-old", age=2 * mp.STALE_STAGING_SECONDS)
        recent = staging(".staging-recent")
        with mp.StagedExport(out) as stage:
            mp.atomic_write_text(os.path.join(stage.dir, "sites.txt"), "v1")
        assert sorted(stage.removed_stale) == sorted([killed, old])
        assert os.path.isdir(live) and os.path.isdir(recent)
        assert sorted(n for n in os.listdir(out) if n.startswith(".staging")) == [".staging-live",
                                                                                  ".staging-recent"]
        assert open(os.path.join(out, "sites.txt")).read() == "v1"

    @pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                        reason="needs a folder that POSIX permissions make read-only")
    def test_a_read_only_folder_is_named_not_the_staging_folder(self, tmp_path):
        out = str(tmp_path / "out")
        os.makedirs(out)
        with open(os.path.join(out, "sites.txt"), "w") as fh:
            fh.write("v0")
        os.chmod(out, 0o555)
        try:
            with pytest.raises(PermissionError) as info:
                with mp.StagedExport(out) as stage:
                    mp.atomic_write_text(os.path.join(stage.dir, "sites.txt"), "v1")
        finally:
            os.chmod(out, 0o755)
        message = str(info.value)
        assert out in message and "not writable" in message and ".staging" not in message
        assert os.listdir(out) == ["sites.txt"] and open(os.path.join(out, "sites.txt")).read() == "v0"

    def test_a_separate_output_directory_is_a_complete_contribution(self, study, tmp_path):
        out = str(tmp_path / "out")
        with mp.StagedExport(out) as stage:
            mp.atomic_write_text(os.path.join(stage.dir, "specimens.txt"), "tab\tspecimens\nspecimen\na\n")
        copied = mp.copy_companion_tables(study, out, skip=stage.written)
        names = {os.path.basename(p) for p in copied}
        assert "specimens.txt" not in names and {"measurements.txt", "sites.txt"} <= names


class TestExactValues:
    def test_a_rewritten_table_keeps_every_value(self, study, tmp_path):
        path = os.path.join(study, "measurements.txt")
        _, before = mp.read_table_file(path)
        out = os.path.join(str(tmp_path), "measurements.txt")
        mp.magic_write(out, before, "measurements")
        _, after = mp.read_table_file(out)
        for col in before.columns:
            a, b = before[col], after[col]
            if pd.api.types.is_float_dtype(a):
                assert ((a == b) | (a.isna() & b.isna())).all(), col
            else:
                assert (a.fillna("").astype(str) == b.fillna("").astype(str)).all(), col

    def test_integer_columns_are_written_as_integers(self, tmp_path):
        path = os.path.join(str(tmp_path), "sites.txt")
        mp.magic_write(path, pd.DataFrame({"site": ["a", "b"], "dir_n_specimens": [11.0, np.nan],
                                           "dir_k": [12.0, 3.5]}), "sites")
        lines = open(path).read().splitlines()
        header = lines[1].split("\t")
        first = dict(zip(header, lines[2].split("\t")))
        assert first["dir_n_specimens"] == "11" and first["dir_k"] == "12.0"


class TestLinesAndPlanesK:
    def test_k_keeps_its_precision(self):
        import pmagpy.demag as dc
        assert dc._lnp_k({"n_lines": "4", "n_planes": "0", "R": "3.1176"}) == pytest.approx(3 / (4 - 3.1176))
        assert dc._lnp_k({"n_lines": "2", "n_planes": "2", "R": "3.9"}) == pytest.approx(2.0 / 0.1)


class TestMeasurementFlagWriter:
    def lines(self, tmp_path, text):
        path = os.path.join(str(tmp_path), "measurements.txt")
        with open(path, "w", newline="") as fh:
            fh.write(text)
        return path

    def test_line_endings_are_kept(self, tmp_path):
        path = self.lines(tmp_path, "tab\tmeasurements\r\nmeasurement\tquality\r\nm1\tg\r\nm2\tg\r\n")
        out = os.path.join(str(tmp_path), "out.txt")
        mp.write_measurement_flags(path, out, {1: "b"})
        assert open(out, "rb").read() == b"tab\tmeasurements\r\nmeasurement\tquality\r\nm1\tg\r\nm2\tb\r\n"

    def test_a_stray_carriage_return_is_not_a_blank_line(self, tmp_path):
        path = self.lines(tmp_path, "tab\tmeasurements\r\r\nmeasurement\tquality\r\r\nm1\tg\r\r\n")
        out = os.path.join(str(tmp_path), "out.txt")
        mp.write_measurement_flags(path, out, {})
        assert open(out, "rb").read().count(b"\n") == 3

    def test_a_file_with_cr_cr_lf_after_every_line_is_read_with_its_rows(self, tmp_path):
        """The reader took the blank line after the first as a missing header: "holds no measurements"."""
        path = self.lines(tmp_path, "tab\tmeasurements\r\r\nmeasurement\tquality\r\r\nm1\tg\r\r\nm2\tb\r\r\n")
        table, df = mp.read_table_file(path)
        assert table == "measurements"
        assert list(df["measurement"]) == ["m1", "m2"] and list(df["quality"]) == ["g", "b"]

    def test_no_final_newline_stays_so(self, tmp_path):
        path = self.lines(tmp_path, "tab\tmeasurements\nmeasurement\tquality\nm1\tg")
        out = os.path.join(str(tmp_path), "out.txt")
        mp.write_measurement_flags(path, out, {})
        assert open(out, "rb").read() == open(path, "rb").read()


    def test_a_flag_is_not_written_onto_another_measurement_when_the_rows_moved(self, tmp_path):
        """Same number of rows, other order (sorted by another program): position k is no longer
        the measurement the flag was set on, so this writer declines (the caller writes in full)."""
        path = self.lines(tmp_path, "tab\tmeasurements\nmeasurement\tquality\nm2\tg\nm1\tg\n")
        out = os.path.join(str(tmp_path), "out.txt")
        assert mp.write_measurement_flags(path, out, {1: "b"}, names=["m1", "m2"]) is None
        assert mp.write_measurement_flags(path, out, {1: "b"}, names=["m2", "m1"]) == out
        assert open(out).read() == "tab\tmeasurements\nmeasurement\tquality\nm2\tg\nm1\tb\n"

    def test_a_blank_name_matches_a_blank_cell(self, tmp_path):
        path = self.lines(tmp_path, "tab\tmeasurements\nmeasurement\tquality\nm1\tg\n\tg\n")
        out = os.path.join(str(tmp_path), "out.txt")
        assert mp.write_measurement_flags(path, out, {1: "b"}, names=["m1", None]) == out

class TestRequiredParentColumn:
    def test_an_empty_parent_column_is_kept(self):
        existing = pd.DataFrame({"specimen": ["a"], "sample": [np.nan], "method_codes": ["LP-DIR-AF"],
                                 "lithologies": [np.nan]})
        out = mp.merge_results(existing, pd.DataFrame(), "specimen", owned=["a"])
        assert "sample" in out.columns and "lithologies" not in out.columns


class TestWholeNumbers:
    def test_a_carried_age_is_written_as_it_was(self, tmp_path):
        path = os.path.join(str(tmp_path), "sites.txt")
        mp.magic_write(path, pd.DataFrame({"site": ["a", "b"], "age": [1106.0, np.nan], "lat": [45.5, 46.0]}),
                       "sites")
        rows = [dict(zip(open(path).read().splitlines()[1].split("\t"), line.split("\t")))
                for line in open(path).read().splitlines()[2:]]
        assert rows[0]["age"] == "1106" and rows[0]["lat"] == "45.5"

    def test_text_read_from_a_table_is_written_as_it_was_read(self, tmp_path):
        path = os.path.join(str(tmp_path), "locations.txt")
        mp.magic_write(path, pd.DataFrame({"location": ["Nipigon", "Other", "Carried"],
                                           "lat_n": ["49.0", "1", 1106.0], "lon_e": ["272.0", "2", np.nan]}),
                       "locations")
        lines = open(path).read().splitlines()
        rows = [dict(zip(lines[1].split("\t"), line.split("\t"))) for line in lines[2:]]
        assert [r["lat_n"] for r in rows] == ["49.0", "1", "1106"]
        assert [r["lon_e"] for r in rows] == ["272.0", "2", ""]
