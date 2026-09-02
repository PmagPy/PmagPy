"""
Tests for the MPMS low-temperature functions in ``pmagpy.rockmag``: the Verwey
estimate against a synthetic magnetite curve with a known transition, and its
behaviour on a curve with no transition at all.

    pytest pmagpy/test/test_rockmag_mpms.py -q
"""
import numpy as np
import pandas as pd
import pytest

from pmagpy import rockmag


def magnetite_curve(t_v=120.0, loss=0.3, width=4.0):
    """An FC warming curve: a gently curved background plus a `loss` step down at `t_v`."""
    temps = np.arange(10.0, 301.0, 2.0)
    mags = 1.0 - 0.001 * temps - 1e-6 * temps ** 2 + loss * (1 - np.tanh((temps - t_v) / width)) / 2
    return pd.Series(temps), pd.Series(mags)


class TestVerweyEstimate:
    def test_a_known_transition_temperature_and_loss_are_recovered(self):
        temps, mags = magnetite_curve(t_v=120.0, loss=0.3)
        result = rockmag.calc_verwey_estimate(temps, mags, t_range_background_min=60, t_range_background_max=250,
                                              excluded_t_min=75, excluded_t_max=150, poly_deg=3)
        _, verwey_t, remanence_loss, r_squared = result[:4]
        assert abs(verwey_t - 120.0) < 0.5
        assert abs(remanence_loss - 0.3) < 0.01
        assert r_squared > 0.99

    def test_the_transition_is_found_wherever_it_is_placed(self):
        for t_v in (100.0, 110.0, 125.0):
            temps, mags = magnetite_curve(t_v=t_v)
            verwey_t = rockmag.calc_verwey_estimate(temps, mags, 60, 250, 75, 150, 3)[1]
            assert abs(verwey_t - t_v) < 0.5

    def test_a_curve_without_a_transition_returns_rather_than_raising(self):
        # the residual then peaks at an end of the background range; the zero
        # crossing used to index past the start of the second derivative there
        temps, mags = magnetite_curve(loss=0.0)
        mags = mags + 0.02 * np.exp(-temps / 30)                      # a paramagnetic-looking tail, no step
        result = rockmag.calc_verwey_estimate(temps, mags, 60, 250, 75, 150, 3)
        verwey_t, remanence_loss = result[1], result[2]
        assert np.isfinite(verwey_t) and 60 <= verwey_t <= 250
        assert abs(remanence_loss) < 1e-3


class TestZeroCrossing:
    def test_the_crossing_is_bracketed_at_the_range_ends(self):
        temps = pd.Series(np.arange(0.0, 10.0))
        rising = pd.Series(-(temps - 12.0) ** 2)                       # maximum at the last point
        falling = pd.Series(-(temps + 3.0) ** 2)                       # maximum at the first point
        for dM_dT in (rising, falling):
            crossing = rockmag.calc_zero_crossing(temps, dM_dT)[-1]     # no IndexError / KeyError
            assert np.isfinite(crossing)
