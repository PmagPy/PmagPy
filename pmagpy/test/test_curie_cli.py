"""Focused tests for the Curie command-line wrapper."""

import numpy as np
import pytest

from programs import curie
from pmagpy import ipmag


@pytest.fixture
def two_column_file(tmp_path):
    path = tmp_path / "curie.txt"
    np.savetxt(path, np.array([
        [300.0, 1.0],
        [400.0, 0.8],
        [500.0, 0.5],
        [600.0, 0.2],
    ]))
    return path


def test_main_uses_default_max_curvature(two_column_file, monkeypatch, capsys):
    captured = {}

    def fake_estimator(T, y, t_range=None, smooth_window=0):
        captured["T"] = T
        captured["y"] = y
        captured["t_range"] = t_range
        captured["smooth_window"] = smooth_window
        return {"max_curvature_temp": 552.0}

    monkeypatch.setattr(curie.rockmag, "curie_derivative_estimates", fake_estimator)

    curie.main(["-f", str(two_column_file), "-w", "10"])

    assert captured["smooth_window"] == 10.0
    assert captured["t_range"] is None
    assert "max_curvature Curie temperature: 552.0" in capsys.readouterr().out


def test_main_applies_range_and_method(two_column_file, monkeypatch):
    captured = {}

    def fake_estimator(T, y, t_range=None, smooth_window=0):
        captured["T"] = T
        captured["t_range"] = t_range
        return {"inflection_temp": 500.0}

    monkeypatch.setattr(curie.rockmag, "curie_derivative_estimates", fake_estimator)

    curie.main([
        "-f", str(two_column_file), "--method", "inflection", "-t", "350", "550"
    ])

    assert np.array_equal(captured["T"], np.array([400.0, 500.0]))
    assert captured["t_range"] == (350.0, 550.0)


def test_main_rejects_missing_input(tmp_path):
    with pytest.raises(SystemExit) as error:
        curie.main(["-f", str(tmp_path / "missing.txt")])

    assert error.value.code == 2


def test_ipmag_smooth_warns():
    values = np.linspace(0.0, 1.0, 10)

    with pytest.warns(FutureWarning, match="ipmag.smooth"):
        ipmag.smooth(values, window_len=3)
