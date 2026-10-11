"""Tests for the ani_depthplot.py command-line program (MagIC data model 3)."""

import os
import sys

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
