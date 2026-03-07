"""
Tests for core direction/coordinate functions in pmag.py.

These are the most-called functions in the codebase (dir2cart: 88 calls,
cart2dir: 54 calls, angle: 29 calls). Regressions here would silently
break dozens of downstream analyses.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# dir2cart: declination/inclination → Cartesian (x, y, z)
# ---------------------------------------------------------------------------

class TestDir2Cart:
    """Tests for pmag.dir2cart.

    Convention:
        x = North, y = East, z = Down
        dec measured clockwise from North, inc positive downward
    """

    def test_north_horizontal(self):
        """Dec=0, Inc=0 points due north along x-axis."""
        result = pmag.dir2cart([0, 0, 1])
        assert_allclose(result, [1, 0, 0], atol=1e-10)

    def test_east_horizontal(self):
        """Dec=90, Inc=0 points due east along y-axis."""
        result = pmag.dir2cart([90, 0, 1])
        assert_allclose(result, [0, 1, 0], atol=1e-10)

    def test_vertical_down(self):
        """Dec=0, Inc=90 points straight down along z-axis."""
        result = pmag.dir2cart([0, 90, 1])
        assert_allclose(result, [0, 0, 1], atol=1e-10)

    def test_vertical_up(self):
        """Dec=0, Inc=-90 points straight up (negative z)."""
        result = pmag.dir2cart([0, -90, 1])
        assert_allclose(result, [0, 0, -1], atol=1e-10)

    def test_south_horizontal(self):
        """Dec=180, Inc=0 points south (negative x)."""
        result = pmag.dir2cart([180, 0, 1])
        assert_allclose(result, [-1, 0, 0], atol=1e-10)

    def test_intensity_scaling(self):
        """Intensity scales the Cartesian vector proportionally."""
        result = pmag.dir2cart([0, 0, 3.5])
        assert_allclose(result, [3.5, 0, 0], atol=1e-10)

    def test_unit_intensity_default(self):
        """When no intensity given, unit vector is assumed."""
        result = pmag.dir2cart([[0, 0]])
        assert_allclose(result, [[1, 0, 0]], atol=1e-10)

    def test_multiple_directions(self):
        """Array of directions produces matching array of Cartesian vectors."""
        dirs = np.array([[0, 0, 1], [90, 0, 1], [0, 90, 1]])
        result = pmag.dir2cart(dirs)
        expected = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        assert_allclose(result, expected, atol=1e-10)

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        result = pmag.dir2cart([200, 40, 1])
        expected = [-0.71984631, -0.26200263, 0.64278761]
        assert_allclose(result, expected, atol=1e-7)


# ---------------------------------------------------------------------------
# cart2dir: Cartesian (x, y, z) → declination/inclination/intensity
# ---------------------------------------------------------------------------

class TestCart2Dir:
    """Tests for pmag.cart2dir."""

    def test_x_axis_is_north(self):
        """Unit vector along x → dec=0, inc=0, intensity=1."""
        result = pmag.cart2dir([1, 0, 0])
        assert_allclose(result, [0, 0, 1], atol=1e-10)

    def test_y_axis_is_east(self):
        """Unit vector along y → dec=90, inc=0, intensity=1."""
        result = pmag.cart2dir([0, 1, 0])
        assert_allclose(result, [90, 0, 1], atol=1e-10)

    def test_z_axis_is_down(self):
        """Unit vector along z → dec=0, inc=90, intensity=1."""
        result = pmag.cart2dir([0, 0, 1])
        assert_allclose(result, [0, 90, 1], atol=1e-10)

    def test_negative_z_is_up(self):
        """Negative z → negative inclination."""
        result = pmag.cart2dir([0, 0, -1])
        assert_allclose(result, [0, -90, 1], atol=1e-10)

    def test_intensity_preserved(self):
        """Intensity equals vector magnitude."""
        result = pmag.cart2dir([3, 4, 0])
        assert_allclose(result[2], 5.0, atol=1e-10)

    def test_multiple_vectors(self):
        """Array of Cartesian vectors produces matching directions."""
        cart = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        result = pmag.cart2dir(cart)
        expected = np.array([[0, 0, 1], [90, 0, 1], [0, 90, 1]])
        assert_allclose(result, expected, atol=1e-10)

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        result = pmag.cart2dir([0, 1, 0])
        assert_allclose(result, [90, 0, 1], atol=1e-10)


# ---------------------------------------------------------------------------
# Roundtrip: dir2cart ↔ cart2dir should be inverse operations
# ---------------------------------------------------------------------------

class TestDirectionRoundtrip:
    """Roundtrip tests verifying dir2cart and cart2dir are inverses."""

    def test_roundtrip_single_direction(self):
        """dir→cart→dir recovers original dec, inc, intensity."""
        original = [142.3, -37.8, 1.0]
        cart = pmag.dir2cart(original)
        recovered = pmag.cart2dir(cart)
        assert_allclose(recovered, original, atol=1e-10)

    def test_roundtrip_with_intensity(self):
        """Roundtrip preserves non-unit intensity."""
        original = [225.0, 55.0, 42000.0]
        cart = pmag.dir2cart(original)
        recovered = pmag.cart2dir(cart)
        assert_allclose(recovered, original, atol=1e-6)

    def test_roundtrip_cardinal_directions(self):
        """Roundtrip works for all cardinal directions."""
        directions = [
            [0, 0, 1],     # north horizontal
            [90, 0, 1],    # east horizontal
            [180, 0, 1],   # south horizontal
            [270, 0, 1],   # west horizontal
            [0, 90, 1],    # vertical down
            [0, -90, 1],   # vertical up
        ]
        for d in directions:
            cart = pmag.dir2cart(d)
            recovered = pmag.cart2dir(cart)
            assert_allclose(recovered, d, atol=1e-10,
                            err_msg=f"Roundtrip failed for {d}")

    def test_roundtrip_array(self):
        """Roundtrip works for arrays of directions."""
        originals = np.array([
            [10.5, 45.2, 1.0],
            [350.0, -20.0, 1.0],
            [90.0, 0.0, 1.0],
        ])
        cart = pmag.dir2cart(originals)
        recovered = pmag.cart2dir(cart)
        assert_allclose(recovered, originals, atol=1e-10)


# ---------------------------------------------------------------------------
# angle: angular distance between two directions
# ---------------------------------------------------------------------------

class TestAngle:
    """Tests for pmag.angle."""

    def test_same_direction_is_zero(self):
        """Angle between identical directions is 0°."""
        result = pmag.angle([10, 20], [10, 20])
        assert_allclose(result, [0.0], atol=1e-10)

    def test_antipodal_is_180(self):
        """Angle between antipodal directions is 180°."""
        result = pmag.angle([0, 90], [0, -90])
        assert_allclose(result, [180.0], atol=1e-10)

    def test_orthogonal_is_90(self):
        """Angle between orthogonal directions is 90°."""
        result = pmag.angle([0, 0], [90, 0])
        assert_allclose(result, [90.0], atol=1e-10)

    def test_north_to_east_is_90(self):
        """North horizontal to East horizontal = 90°."""
        result = pmag.angle([0, 0], [0, 90])
        assert_allclose(result, [90.0], atol=1e-10)

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        result = pmag.angle([350.0, 10.0], [320.0, 20.0])
        assert_allclose(result, [30.59060998], atol=1e-6)

    def test_multiple_pairs(self):
        """Array input returns angles for each pair."""
        result = pmag.angle(
            [[350.0, 10.0], [320.0, 20.0]],
            [[345, 13], [340, 14]]
        )
        expected = [5.744522410794302, 20.026413431433475]
        assert_allclose(result, expected, atol=1e-6)

    def test_symmetry(self):
        """angle(A, B) == angle(B, A)."""
        ab = pmag.angle([30, 45], [120, -10])
        ba = pmag.angle([120, -10], [30, 45])
        assert_allclose(ab, ba, atol=1e-10)
