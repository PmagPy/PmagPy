"""Focused tests for the Curie command-line wrapper."""

import os

import numpy as np
import pytest

from programs import curie
from pmagpy import ipmag
from pmagpy import rockmag as rmag

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files"
)
CURIE_EXAMPLE = os.path.join(DATA_DIR, "curie", "curie_example.dat")


@pytest.fixture
def two_column_file(tmp_path):
    path = tmp_path / "curie.txt"
    np.savetxt(path, np.array([
        [300.0, 1.0],
        [350.0, 0.9],
        [400.0, 0.8],
        [450.0, 0.65],
        [500.0, 0.5],
        [550.0, 0.35],
        [600.0, 0.2],
    ]))
    return path


def test_main_uses_default_window_and_method(two_column_file, monkeypatch, capsys):
    captured = {}

    def fake_estimator(T, y, t_range=None, smooth_window=0):
        captured["T"] = T
        captured["y"] = y
        captured["t_range"] = t_range
        captured["smooth_window"] = smooth_window
        return {"max_curvature_temp": 552.0}

    monkeypatch.setattr(curie.rmag, "curie_derivative_estimates", fake_estimator)

    curie.main(["-f", str(two_column_file)])

    assert captured["smooth_window"] == 10.0
    assert captured["t_range"] is None
    assert "max_curvature Curie temperature: 552.00" in capsys.readouterr().out


def test_main_applies_range_and_method(two_column_file, monkeypatch):
    captured = {}

    def fake_estimator(T, y, t_range=None, smooth_window=0):
        captured["T"] = T
        captured["t_range"] = t_range
        return {"inflection_temp": 500.0}

    monkeypatch.setattr(curie.rmag, "curie_derivative_estimates", fake_estimator)

    curie.main([
        "-f", str(two_column_file), "--method", "inflection", "-t", "350", "550",
        "-w", "0",
    ])

    assert np.array_equal(
        captured["T"], np.array([350.0, 400.0, 450.0, 500.0, 550.0])
    )
    assert captured["t_range"] == (350.0, 550.0)


def test_main_rejects_missing_input(tmp_path):
    with pytest.raises(SystemExit) as error:
        curie.main(["-f", str(tmp_path / "missing.txt")])

    assert error.value.code == 2


def test_main_saves_figure(two_column_file, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    curie.main(["-f", str(two_column_file), "-sav", "-fmt", "png"])

    assert (tmp_path / "curie_max_curvature.png").stat().st_size > 0


@pytest.mark.skipif(not os.path.exists(CURIE_EXAMPLE),
                    reason="curie_example.dat not available")
class TestRealData:
    """The CLI must agree with the library's own smoothing path (signal
    smoothed with the window, then derivative smoothing) and reproduce the
    legacy ipmag.curie value (552 C with a 10-degree window) to within a few
    degrees."""

    def _cli_value(self, capsys, *extra):
        curie.main(["-f", CURIE_EXAMPLE, *extra])
        out = capsys.readouterr().out.strip().splitlines()[-1]
        return float(out.split(":")[-1])

    def test_max_curvature_matches_legacy(self, capsys):
        assert self._cli_value(capsys, "-w", "10") == pytest.approx(552.0, abs=5.0)

    @pytest.mark.parametrize("method", curie.METHODS)
    def test_every_method_runs(self, capsys, method):
        """Each estimator runs end to end on real data and returns a
        plausible Curie temperature for this magnetite-dominated sample."""
        value = self._cli_value(capsys, "--method", method)

        assert np.isfinite(value)
        assert 450.0 < value < 650.0

    @pytest.mark.parametrize("method, key", [
        ("max_curvature", "max_curvature_temp"),
        ("inflection", "inflection_temp"),
    ])
    def test_matches_library_path(self, capsys, method, key):
        T, M = np.loadtxt(CURIE_EXAMPLE, unpack=True)
        sT, sM = rmag.smooth_moving_average(T, M, 10)
        expected = rmag.curie_derivative_estimates(sT, sM, smooth_window=10)[key]

        assert self._cli_value(capsys, "--method", method) == pytest.approx(expected, abs=0.01)


def test_ipmag_smooth_warns():
    values = np.linspace(0.0, 1.0, 10)

    with pytest.warns(FutureWarning, match="ipmag.smooth"):
        ipmag.smooth(values, window_len=3)
