"""
Tests for inclination shallowing (E/I) functions.

Covers ipmag.squish / unsquish (flattening/unflattening inclinations),
ipmag.f_factor_calc (flattening factor calculation), pmag.find_f
(core E/I algorithm), and ipmag.find_ei (bootstrap E/I correction).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag, pmag


# ---------------------------------------------------------------------------
# squish / unsquish: additional analytical tests
# ---------------------------------------------------------------------------

class TestFFactorCalc:
    """Tests for ipmag.f_factor_calc."""

    def test_docstring_example(self):
        """Verify the f_factor_calc docstring example."""
        f_factor = ipmag.f_factor_calc(25, 40)
        assert_allclose(f_factor, 0.5557238268604126)


class TestSquish:
    """Tests for ipmag.squish."""

    def test_f_equals_one_no_change(self):
        """Flattening factor of 1.0 leaves inclinations unchanged."""
        incs = [43, 47, 41, -30, 0, 90]
        result = ipmag.squish(incs, 1.0)
        assert_allclose(result, incs, atol=1e-10)

    def test_single_value_input(self):
        """squish handles a single scalar inclination."""
        result = ipmag.squish(45, 0.5)
        assert isinstance(result, float)
        # tan(45°)=1, f*1=0.5, arctan(0.5)=26.57°
        assert_allclose(result, np.degrees(np.arctan(0.5)), atol=1e-10)

    def test_antisymmetry(self):
        """Squishing negative inclination gives negative of squishing positive."""
        f = 0.6
        pos = ipmag.squish(45, f)
        neg = ipmag.squish(-45, f)
        assert_allclose(neg, -pos, atol=1e-10)

    def test_flattening_reduces_inclination(self):
        """Squishing with f < 1 makes inclination shallower (closer to 0)."""
        inc = 60.0
        result = ipmag.squish(inc, 0.5)
        assert abs(result) < abs(inc)

    def test_zero_inclination_unchanged(self):
        """Horizontal direction (inc=0) is unaffected by any flattening factor."""
        assert_allclose(ipmag.squish(0, 0.3), 0.0, atol=1e-10)


class TestUnsquish:
    """Tests for ipmag.unsquish."""

    def test_f_equals_one_no_change(self):
        """Unflattening factor of 1.0 leaves inclinations unchanged."""
        incs = [43, 47, 41, -30]
        result = ipmag.unsquish(incs, 1.0)
        assert_allclose(result, incs, atol=1e-10)

    def test_single_value_input(self):
        """unsquish handles a single scalar inclination."""
        result = ipmag.unsquish(26.565, 0.5)
        assert isinstance(result, float)
        # arctan((1/0.5)*tan(26.565°)) ≈ arctan(2*0.5) = arctan(1) = 45°
        assert_allclose(result, 45.0, atol=0.01)

    def test_unsquish_steepens_inclination(self):
        """Unsquishing makes inclination steeper (farther from 0)."""
        inc = 30.0
        result = ipmag.unsquish(inc, 0.5)
        assert abs(result) > abs(inc)


class TestSquishUnsquishRoundtrip:
    """Roundtrip tests verifying squish and unsquish are exact inverses."""

    def test_roundtrip_list(self):
        """unsquish(squish(incs, f), f) recovers the original inclinations."""
        incs = [43, 47, 41, -30, 15, 72]
        f = 0.4
        squished = ipmag.squish(incs, f)
        recovered = ipmag.unsquish(squished, f)
        assert_allclose(recovered, incs, atol=1e-10)

    def test_roundtrip_scalar(self):
        """Roundtrip works for a single scalar value."""
        inc = 55.0
        f = 0.7
        recovered = ipmag.unsquish(ipmag.squish(inc, f), f)
        assert_allclose(recovered, inc, atol=1e-10)

    def test_roundtrip_multiple_f_values(self):
        """Roundtrip holds for a range of flattening factors."""
        inc = 60.0
        for f in [0.2, 0.4, 0.6, 0.8, 1.0]:
            recovered = ipmag.unsquish(ipmag.squish(inc, f), f)
            assert_allclose(recovered, inc, atol=1e-10,
                            err_msg=f"Roundtrip failed for f={f}")

    def test_roundtrip_negative_inclination(self):
        """Roundtrip preserves sign for negative (southern hemisphere) inclinations."""
        incs = [-20, -45, -70]
        f = 0.5
        recovered = ipmag.unsquish(ipmag.squish(incs, f), f)
        assert_allclose(recovered, incs, atol=1e-10)


# ---------------------------------------------------------------------------
# pmag.find_f: core E/I algorithm
# ---------------------------------------------------------------------------

class TestFindF:
    """Tests for pmag.find_f."""

    def test_docstring_example_returns_lists(self):
        """find_f returns four lists of equal length."""
        directions = np.array([[140, 21], [127, 23], [142, 19], [136, 22]])
        Es, Is, Fs, V2s = pmag.find_f(directions)
        assert len(Es) == len(Is) == len(Fs) == len(V2s)
        assert len(Es) > 0

    def test_elongation_increases_as_f_decreases(self):
        """Elongation generally increases as flattening factor decreases."""
        directions = np.array([[140, 21], [127, 23], [142, 19],
                                [136, 22], [131, 25], [145, 18]])
        Es, Is, Fs, V2s = pmag.find_f(directions)
        if len(Fs) > 1:
            # F values decrease through the list; elongation should trend up
            assert Fs[0] > Fs[-1]
            assert Es[-1] >= Es[0]

    def test_f_values_between_zero_and_one(self):
        """All returned f values are in (0, 1]."""
        directions = np.array([[140, 21], [127, 23], [142, 19],
                                [136, 22], [131, 25], [145, 18]])
        Es, Is, Fs, V2s = pmag.find_f(directions)
        if Fs != [0]:
            for f in Fs:
                assert 0 < f <= 1.0


# ---------------------------------------------------------------------------
# ipmag.find_ei: bootstrap E/I correction (smoke test)
# ---------------------------------------------------------------------------

class TestFindEi:
    """Tests for ipmag.find_ei."""

    def test_returns_values_and_recovers_f(self):
        """find_ei recovers a flattening factor close to the known input.

        Generate TK03 secular variation directions (which have the
        latitude-dependent elongation that the E/I method requires),
        apply known flattening (f=0.6), then verify find_ei recovers
        an f-factor within ±0.15 of the true value.
        """
        # TK03 at lat=30 gives proper secular variation with elongation
        dirs = ipmag.tk03(n=100, dec=0, lat=30, rev='no', random_seed=0)
        decs = [d[0] for d in dirs]
        incs = [d[1] for d in dirs]
        # Squish to simulate inclination shallowing with f=0.6
        squished_incs = ipmag.squish(incs, 0.6)
        data = list(zip(decs, squished_incs))
        result = ipmag.find_ei(data, nb=20, return_values=True)
        # Should return (flat_f, I, E, F) tuple
        assert len(result) == 4
        flat_f, I, E, F = result
        assert isinstance(flat_f, (int, float, np.floating))
        # Recovered f should be close to the input value of 0.6
        assert 0.45 < flat_f < 0.75, (
            f"Recovered f={flat_f} outside expected range for input f=0.6"
        )
