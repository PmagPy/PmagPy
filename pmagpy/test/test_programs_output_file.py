"""Tests that the -F output-file option of the simple command-line programs works.

These programs opened their -F file with the invalid mode 'w + a', which
raises ValueError before any data are read.
"""

import importlib
import os
import sys

import pytest

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files"
)

# program name -> tracked example input file
PROGRAM_INPUTS = {
    "eigs_s": "eigs_s/eigs_s_example.dat",
    "eq_di": "eq_di/eq_di_example.dat",
    "gobing": "gobing/gobing_example.txt",
    "gofish": "gofish/fishrot.out",
    "gokent": "gokent/gokent_example.txt",
    "goprinc": "goprinc/goprinc_example.txt",
    "incfish": "incfish/incfish_example_inc.dat",
    "s_eigs": "s_eigs/s_eigs_example.dat",
    "s_geo": "s_geo/s_geo_example.dat",
    "s_tilt": "s_tilt/s_tilt_example.dat",
    "stats": "stats/gaussian.out",
    "vector_mean": "vector_mean/vector_mean_example.dat",
}


@pytest.mark.parametrize("program", sorted(PROGRAM_INPUTS))
def test_output_file_matches_stdout(program, tmp_path, monkeypatch, capsys):
    """Output written with -F has the same values the program prints to stdout."""
    module = importlib.import_module("programs." + program)
    infile = os.path.join(DATA_DIR, PROGRAM_INPUTS[program])
    monkeypatch.chdir(tmp_path)

    monkeypatch.setattr(sys, "argv", [program + ".py", "-f", infile])
    module.main()
    printed = capsys.readouterr().out

    outfile = tmp_path / "out.txt"
    monkeypatch.setattr(sys, "argv", [program + ".py", "-f", infile, "-F", str(outfile)])
    module.main()

    written = outfile.read_text()
    assert written.split()
    assert written.split() == printed.split()
