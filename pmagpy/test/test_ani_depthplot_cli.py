"""Tests for the ani_depthplot.py command-line program (MagIC data model 3)."""

import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("wx")

from programs import ani_depthplot  # noqa: E402

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files"
)
ANISO_DIR = os.path.join(DATA_DIR, "ani_depthplot")


def run_ani_depthplot(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["ani_depthplot.py", *args])
    return ani_depthplot.main()


def test_dm2_is_rejected(monkeypatch):
    with pytest.raises(SystemExit) as error:
        run_ani_depthplot(monkeypatch, "-DM", "2")

    assert "Convert Data Model 2 files to Data Model 3" in str(error.value)


def test_save_quietly_writes_plot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    run_ani_depthplot(monkeypatch, "-WD", ANISO_DIR, "-sav", "-fmt", "png")

    assert (tmp_path / "U1361A_ani_depthplot.png").stat().st_size > 0


def test_depth_range_is_applied(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    run_ani_depthplot(monkeypatch, "-WD", ANISO_DIR, "-sav", "-fmt", "png",
                      "-d", "20", "40")

    assert (tmp_path / "U1361A_ani_depthplot.png").stat().st_size > 0


def test_custom_age_file_is_used(tmp_path, monkeypatch):
    custom_age_file = tmp_path / "custom_ages.txt"
    age_data = Path(ANISO_DIR, "ages.txt").read_text()
    custom_age_file.write_text(age_data.replace("\tMa\t", "\tka\t"))

    original_ani_depthplot = ani_depthplot.ipmag.ani_depthplot

    def check_custom_age_unit(*args, **kwargs):
        plot, names = original_ani_depthplot(*args, **kwargs)
        assert plot.axes[0].get_ylabel() == "Age (ka)"
        return plot, names

    monkeypatch.setattr(ani_depthplot.ipmag, "ani_depthplot",
                        check_custom_age_unit)
    monkeypatch.chdir(tmp_path)
    run_ani_depthplot(monkeypatch, "-WD", ANISO_DIR, "-fa",
                      str(custom_age_file), "-sav", "-fmt", "png")

    assert (tmp_path / "U1361A_ani_depthplot.png").stat().st_size > 0
