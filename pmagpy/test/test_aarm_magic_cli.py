"""Tests for the aarm_magic.py command-line program (MagIC data model 3)."""

import os
import shutil
import sys

import numpy as np
import pandas as pd
import pytest

from programs import aarm_magic
from pmagpy import pmag

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files"
)
AARM_MEASUREMENTS = os.path.join(DATA_DIR, "aarm_magic", "aarm_measurements.txt")


def run_aarm_magic(monkeypatch, work_dir, *args):
    """Run aarm_magic.main() in work_dir and return the output specimens table."""
    monkeypatch.chdir(work_dir)
    monkeypatch.setattr(sys, "argv", ["aarm_magic.py", *args])
    aarm_magic.main()
    return pd.read_csv(work_dir / "specimens.txt", sep="\t", header=1)


def write_specimens(path, header, rows):
    with open(path, "w") as f:
        f.write("tab\tspecimens\n")
        f.write("\t".join(header) + "\n")
        for row in rows:
            f.write("\t".join(row) + "\n")


class TestAarmMagicCli:

    def test_nine_position_example(self, tmp_path, monkeypatch):
        """The example 9-position data reproduce the published tensors."""
        shutil.copy(AARM_MEASUREMENTS, tmp_path)
        specs = run_aarm_magic(monkeypatch, tmp_path, "-f", "aarm_measurements.txt")

        assert sorted(specs["specimen"]) == [
            "bg2.01", "bg2.03", "bg2.06", "bg2.07", "bg2.08", "bg2.09", "bg2.12"]
        assert (specs["aniso_type"] == "AARM").all()
        assert (specs["aniso_s_n_measurements"] == 9).all()
        assert (specs["aniso_tilt_correction"] == -1).all()
        # the tensor fit runs in float32 and is written with %f, so the last
        # printed digit can differ between platforms
        bg201 = specs.set_index("specimen").loc["bg2.01"]
        tau1, dec1, inc1 = np.array(bg201["aniso_v1"].split(":"), dtype=float)
        assert tau1 == pytest.approx(0.396615, abs=1e-5)
        assert dec1 == pytest.approx(198.5, abs=0.2)
        assert inc1 == pytest.approx(-53.8, abs=0.2)
        assert bg201["aniso_p"] == pytest.approx(1.347395, abs=1e-5)

    def test_existing_specimen_records_are_kept(self, tmp_path, monkeypatch):
        """AARM results are merged into, not substituted for, specimens.txt."""
        shutil.copy(AARM_MEASUREMENTS, tmp_path)
        write_specimens(
            tmp_path / "specimens.txt",
            ["specimen", "sample", "dir_dec", "dir_inc", "method_codes"],
            [["other.01", "other", "10.0", "20.0", "LP-DIR-AF"],
             ["bg2.01", "bg2", "30.0", "40.0", "LP-DIR-AF"]])
        specs = run_aarm_magic(monkeypatch, tmp_path, "-f", "aarm_measurements.txt")
        specs = specs.set_index("specimen")

        assert len(specs) == 8
        assert specs.loc["other.01", "dir_dec"] == 10.0
        assert pd.isna(specs.loc["other.01", "aniso_type"])
        assert specs.loc["bg2.01", "dir_dec"] == 30.0
        assert specs.loc["bg2.01", "aniso_type"] == "AARM"

    def test_six_position_recovers_known_tensor(self, tmp_path, monkeypatch):
        """A 6-position (+X,+Y,+Z,-X,-Y,-Z) experiment recovers the input tensor."""
        chi = np.array([[1.20, 0.05, -0.03],
                        [0.05, 1.00, 0.02],
                        [-0.03, 0.02, 0.80]]) * 1e-6
        fields = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1],
                           [-1, 0, 0], [0, -1, 0], [0, 0, -1]], dtype=float)
        # small fixed perturbation so the Hext sigma is finite
        noise = 1e-9 * np.array([[1, -2, 1], [-1, 1, 2], [2, 1, -1],
                                 [-2, 1, 1], [1, 2, -1], [1, -1, -2]])
        moments = fields @ chi + noise

        header = ["measurement", "specimen", "experiment", "method_codes",
                  "dir_dec", "dir_inc", "magn_moment", "treat_ac_field",
                  "treat_dc_field", "treat_step_num"]
        rows = []
        for i, moment in enumerate(moments):
            dec, inc, intensity = pmag.cart2dir(moment)
            rows.append(["syn.01-%i" % (2 * i), "syn.01", "syn.01-ARM",
                         "LT-AF-Z:LP-AN-ARM", "0.0", "0.0", "0.0",
                         "0.18", "0", str(2 * i)])
            rows.append(["syn.01-%i" % (2 * i + 1), "syn.01", "syn.01-ARM",
                         "LT-AF-I:LP-AN-ARM", "%.6f" % dec, "%.6f" % inc,
                         "%.6e" % intensity, "0.18", "5e-05", str(2 * i + 1)])
        with open(tmp_path / "aarm_measurements.txt", "w") as f:
            f.write("tab\tmeasurements\n")
            f.write("\t".join(header) + "\n")
            for row in rows:
                f.write("\t".join(row) + "\n")

        specs = run_aarm_magic(monkeypatch, tmp_path, "-f", "aarm_measurements.txt")
        spec = specs.iloc[0]

        assert spec["aniso_s_n_measurements"] == 6
        s = np.array(spec["aniso_s"].split(":"), dtype=float)
        expected = chi / np.trace(chi)
        np.testing.assert_allclose(
            s, [expected[0, 0], expected[1, 1], expected[2, 2],
                expected[0, 1], expected[1, 2], expected[0, 2]], atol=1e-3)
