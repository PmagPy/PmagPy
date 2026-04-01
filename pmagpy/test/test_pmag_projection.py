"""
Tests for equal-area projection functions in pmag.py.

Covers dimap (single direction) and dimap_V (vectorized) — the core
functions that map declination/inclination pairs to x,y coordinates
in equal-area (Lambert azimuthal) projection.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# dimap: single direction equal-area projection
# ---------------------------------------------------------------------------

class TestDimap:
    """Tests for pmag.dimap."""

    def test_north_horizontal(self):
        """D=0, I=0 projects to the outer rim at top (y=1, x=0)."""
        xy = pmag.dimap(0, 0)
        assert_allclose(xy[0], 0.0, atol=1e-10)
        assert_allclose(xy[1], 1.0, atol=1e-10)

    def test_east_horizontal(self):
        """D=90, I=0 projects to the outer rim at right (x=1, y=0)."""
        xy = pmag.dimap(90, 0)
        assert_allclose(xy[0], 1.0, atol=1e-10)
        assert_allclose(xy[1], 0.0, atol=1e-10)

    def test_south_horizontal(self):
        """D=180, I=0 projects to the outer rim at bottom."""
        xy = pmag.dimap(180, 0)
        assert_allclose(xy[0], 0.0, atol=1e-6)
        assert_allclose(xy[1], -1.0, atol=1e-6)

    def test_west_horizontal(self):
        """D=270, I=0 projects to the outer rim at left."""
        xy = pmag.dimap(270, 0)
        assert_allclose(xy[0], -1.0, atol=1e-6)
        assert_allclose(xy[1], 0.0, atol=1e-6)

    def test_vertical_down_projects_to_origin(self):
        """D=0, I=90 (straight down) projects to the center."""
        xy = pmag.dimap(0, 90)
        assert_allclose(xy, [0.0, 0.0], atol=1e-10)

    def test_vertical_up_projects_to_origin(self):
        """D=0, I=-90 (straight up) also projects to center (lower hemisphere)."""
        xy = pmag.dimap(0, -90)
        assert_allclose(xy, [0.0, 0.0], atol=1e-10)

    def test_horizontal_on_unit_circle(self):
        """Horizontal directions (I=0) project to the unit circle."""
        for dec in [0, 45, 90, 135, 180, 225, 270, 315]:
            xy = pmag.dimap(dec, 0)
            r = np.sqrt(xy[0]**2 + xy[1]**2)
            assert_allclose(r, 1.0, atol=1e-6,
                            err_msg=f"D={dec} not on unit circle")

    def test_steeper_inclination_closer_to_center(self):
        """Steeper inclination projects closer to the origin."""
        r_shallow = np.sqrt(sum(x**2 for x in pmag.dimap(0, 30)))
        r_steep = np.sqrt(sum(x**2 for x in pmag.dimap(0, 60)))
        assert r_shallow > r_steep

    def test_opposite_inclinations_same_radius(self):
        """Positive and negative inclinations map to the same radius."""
        xy_pos = pmag.dimap(45, 30)
        xy_neg = pmag.dimap(45, -30)
        r_pos = np.sqrt(xy_pos[0]**2 + xy_pos[1]**2)
        r_neg = np.sqrt(xy_neg[0]**2 + xy_neg[1]**2)
        assert_allclose(r_pos, r_neg, atol=1e-10)

    def test_equal_area_property(self):
        """Equal-area projection: r = sqrt(2) * sin(theta/2) where theta = colatitude."""
        inc = 45
        theta = np.radians(90 - inc)  # colatitude
        expected_r = np.sqrt(2) * np.sin(theta / 2)
        xy = pmag.dimap(0, inc)
        actual_r = np.sqrt(xy[0]**2 + xy[1]**2)
        assert_allclose(actual_r, expected_r, atol=1e-6)

    def test_360_equals_0(self):
        """D=360 is equivalent to D=0."""
        xy_0 = pmag.dimap(0, 45)
        xy_360 = pmag.dimap(360, 45)
        assert_allclose(xy_0, xy_360, atol=1e-10)


# ---------------------------------------------------------------------------
# dimap_V: vectorized equal-area projection
# ---------------------------------------------------------------------------

class TestDimapV:
    """Tests for pmag.dimap_V (vectorized version)."""

    def test_docstring_example(self):
        """Verify the docstring example."""
        result = pmag.dimap_V([35, 60, 20], [70, 80, -10])
        assert result.shape == (3, 2)

    def test_single_direction_matches_dimap(self):
        """dimap_V with one direction matches dimap output."""
        xy_scalar = pmag.dimap(45, 30)
        xy_vec = pmag.dimap_V([45], [30])
        assert_allclose(xy_vec[0], xy_scalar, atol=1e-10)

    def test_multiple_directions_match_dimap(self):
        """dimap_V results match individual dimap calls."""
        decs = [0, 90, 180, 270, 45]
        incs = [0, 30, 60, -45, 90]
        result = pmag.dimap_V(decs, incs)
        for i, (d, inc) in enumerate(zip(decs, incs)):
            expected = pmag.dimap(d, inc)
            assert_allclose(result[i], expected, atol=1e-6,
                            err_msg=f"Mismatch at D={d}, I={inc}")

    def test_output_shape(self):
        """Output has shape (N, 2)."""
        result = pmag.dimap_V([0, 90, 180], [45, 45, 45])
        assert result.shape == (3, 2)

    def test_dimap_dispatches_to_V_for_arrays(self):
        """dimap automatically dispatches to dimap_V for array input."""
        result = pmag.dimap([0, 90], [45, 45])
        assert result.shape == (2, 2)
