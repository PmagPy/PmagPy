"""
Tests for random sampling functions in pmag.py.

Covers fshdev (Fisher distribution random draws) — used throughout PmagPy
for bootstrap confidence intervals and Monte Carlo simulations.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# fshdev: Fisher distribution random sampling
# ---------------------------------------------------------------------------

class TestFshdev:
    """Tests for pmag.fshdev."""

    def test_returns_dec_inc(self):
        """fshdev returns a (dec, inc) pair."""
        dec, inc = pmag.fshdev(10)
        assert isinstance(float(dec), float)
        assert isinstance(float(inc), float)

    def test_dec_in_range(self):
        """Declination is in [0, 360)."""
        rng = np.random.default_rng(42)
        for _ in range(100):
            dec, _ = pmag.fshdev(10, random_seed=rng)
            assert 0 <= dec < 360

    def test_inc_in_range(self):
        """Inclination is in [-90, 90]."""
        rng = np.random.default_rng(42)
        for _ in range(100):
            _, inc = pmag.fshdev(10, random_seed=rng)
            assert -90 <= inc <= 90

    def test_high_kappa_cluster_near_pole(self):
        """High kappa concentrates directions near the mean (D=0, I=90)."""
        incs = [pmag.fshdev(500, random_seed=i)[1] for i in range(200)]
        mean_inc = np.mean(incs)
        # Mean inclination should be very close to 90
        assert mean_inc > 85.0

    def test_low_kappa_spread(self):
        """Low kappa spreads directions widely."""
        incs = [pmag.fshdev(2, random_seed=i)[1] for i in range(500)]
        std_inc = np.std(incs)
        # With low kappa, standard deviation should be substantial
        assert std_inc > 15.0

    def test_array_input_returns_arrays(self):
        """Array of kappa values returns arrays of dec and inc."""
        kappas = np.array([10, 10, 10, 10, 10])
        decs, incs = pmag.fshdev(kappas)
        assert len(decs) == 5
        assert len(incs) == 5

    def test_array_length_matches_input(self):
        """Output array length matches input kappa array length."""
        n = 50
        kappas = np.full(n, 20.0)
        decs, incs = pmag.fshdev(kappas)
        assert len(decs) == n
        assert len(incs) == n

    def test_mean_direction_near_north_pole(self):
        """Mean of many samples is near (D=0, I=90)."""
        kappas = np.full(1000, 50.0)
        decs, incs = pmag.fshdev(kappas, random_seed=0)
        fpars = pmag.fisher_mean(list(zip(decs, incs)))
        # Mean should be near I=90 (pole)
        assert fpars['inc'] > 85.0

    def test_estimated_kappa_near_input(self):
        """Fisher k from many samples approximates the input kappa."""
        kappas = np.full(500, 30.0)
        decs, incs = pmag.fshdev(kappas, random_seed=0)
        fpars = pmag.fisher_mean(list(zip(decs, incs)))
        # Estimated k should be in the right ballpark (within factor of 2)
        assert 15 < fpars['k'] < 60
