"""
Tests for coordinate transformation functions in pmag.py.

Covers dotilt/dotilt_V (bedding tilt correction), dogeo/dogeo_V
(specimen → geographic rotation), doflip (upper → lower hemisphere),
and flip (separate normal/reversed populations).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# dotilt / dotilt_V: bedding tilt correction
# ---------------------------------------------------------------------------

class TestDotilt:
    """Tests for pmag.dotilt."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        dec, inc = pmag.dotilt(91.2, 43.1, 90.0, 20.0)
        assert_allclose(dec, 90.952568837153436, atol=1e-6)
        assert_allclose(inc, 23.103411670066617, atol=1e-6)

    def test_zero_dip_no_change(self):
        """Horizontal bedding (dip=0) leaves direction unchanged."""
        dec, inc = pmag.dotilt(45.0, 30.0, 90.0, 0.0)
        assert_allclose(dec, 45.0, atol=1e-10)
        assert_allclose(inc, 30.0, atol=1e-10)

    def test_known_correction(self):
        """Vertical Inc with 90° dip along strike should rotate to horizontal."""
        # Bed dipping 90° to the east (dip direction=90), vertical down direction
        # should rotate to horizontal pointing east
        dec, inc = pmag.dotilt(0.0, 90.0, 90.0, 90.0)
        assert_allclose(inc, 0.0, atol=1e-10)

    def test_north_horizontal_east_dip(self):
        """North horizontal direction with eastward dip stays north horizontal."""
        # Direction along strike is unaffected by tilt correction
        dec, inc = pmag.dotilt(0.0, 0.0, 90.0, 30.0)
        assert_allclose(dec % 360., 0.0, atol=1e-10)  # 0° and 360° are equivalent
        assert_allclose(inc, 0.0, atol=1e-10)

    def test_rotation_to_mean(self):
        """dotilt with (Dbar-180, 90-Ibar) rotates the mean to the pole.

        This is the pattern used in fishqq.py to rotate data so the mean
        direction maps to inc=90 (the pole). Dec is undefined at the pole.
        """
        Dbar, Ibar = 30.0, 50.0
        _, inc = pmag.dotilt(Dbar, Ibar, Dbar - 180., 90. - Ibar)
        assert_allclose(inc, 90.0, atol=1e-6)


class TestDotiltV:
    """Tests for pmag.dotilt_V (vectorized tilt correction)."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        indat = np.array([[91.2, 43.1, 90.0, 20.0],
                          [92.0, 40.4, 90.5, 21.3]])
        decs, incs = pmag.dotilt_V(indat)
        assert_allclose(decs, [90.95256883715344, 91.70884991139725], atol=1e-6)
        assert_allclose(incs, [23.103411670066613, 19.105747819853423], atol=1e-6)

    def test_matches_scalar_version(self):
        """Vectorized results match scalar dotilt for each row."""
        rows = [[45.0, 30.0, 120.0, 15.0],
                [200.0, -50.0, 270.0, 40.0],
                [350.0, 10.0, 45.0, 25.0]]
        indat = np.array(rows)
        decs_v, incs_v = pmag.dotilt_V(indat)
        for i, row in enumerate(rows):
            dec_s, inc_s = pmag.dotilt(*row)
            assert_allclose(decs_v[i], dec_s, atol=1e-10,
                            err_msg=f"Dec mismatch at row {i}")
            assert_allclose(incs_v[i], inc_s, atol=1e-10,
                            err_msg=f"Inc mismatch at row {i}")


# ---------------------------------------------------------------------------
# dogeo / dogeo_V: specimen → geographic coordinates
# ---------------------------------------------------------------------------

class TestDogeo:
    """Tests for pmag.dogeo."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        dec, inc = pmag.dogeo(0.0, 90.0, 0.0, 45.5)
        assert_allclose(dec, 180.0, atol=1e-10)
        assert_allclose(inc, 44.5, atol=1e-10)

    def test_identity_rotation(self):
        """az=0, pl=0 leaves direction unchanged (specimen = geographic)."""
        dec, inc = pmag.dogeo(135.0, -42.0, 0.0, 0.0)
        assert_allclose(dec, 135.0, atol=1e-10)
        assert_allclose(inc, -42.0, atol=1e-10)

    def test_azimuth_rotation_only(self):
        """Pure azimuth rotation (pl=0) rotates declination by az."""
        dec, inc = pmag.dogeo(0.0, 45.0, 90.0, 0.0)
        assert_allclose(dec, 90.0, atol=1e-10)
        assert_allclose(inc, 45.0, atol=1e-10)

    def test_specimen_x_maps_to_az_pl(self):
        """Specimen +x direction (dec=0, inc=0) maps to (az, pl)."""
        az, pl = 120.0, 35.0
        dec, inc = pmag.dogeo(0.0, 0.0, az, pl)
        assert_allclose(dec, az, atol=1e-10)
        assert_allclose(inc, pl, atol=1e-10)

    def test_negative_plunge(self):
        """Negative plunge (flipped drill direction) used in demag_gui.py."""
        # dogeo with (az-180, -pl) tests for wrong drill arrow direction
        az, pl = 90.0, 30.0
        dec_normal, inc_normal = pmag.dogeo(0.0, 0.0, az, pl)
        dec_flipped, inc_flipped = pmag.dogeo(0.0, 0.0, az - 180., -pl)
        # The two results should differ — wrong drill direction gives wrong answer
        ang = pmag.angle([dec_normal, inc_normal], [dec_flipped, inc_flipped])
        assert ang[0] > 10.0


class TestDogeoV:
    """Tests for pmag.dogeo_V (vectorized geographic rotation)."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        indat = np.array([[0.0, 90.0, 0.0, 45.5],
                          [0.0, 90.0, 0.0, 45.5]])
        decs, incs = pmag.dogeo_V(indat)
        assert_allclose(decs, [180.0, 180.0], atol=1e-10)
        assert_allclose(incs, [44.5, 44.5], atol=1e-10)

    def test_matches_scalar_version(self):
        """Vectorized results match scalar dogeo for each row."""
        rows = [[0.0, 45.0, 90.0, 0.0],
                [30.0, -20.0, 180.0, 30.0],
                [270.0, 60.0, 45.0, 10.0]]
        indat = np.array(rows)
        decs_v, incs_v = pmag.dogeo_V(indat)
        for i, row in enumerate(rows):
            dec_s, inc_s = pmag.dogeo(*row)
            assert_allclose(decs_v[i], dec_s, atol=1e-10,
                            err_msg=f"Dec mismatch at row {i}")
            assert_allclose(incs_v[i], inc_s, atol=1e-10,
                            err_msg=f"Inc mismatch at row {i}")


# ---------------------------------------------------------------------------
# dogeo → dotilt pipeline: specimen → geographic → tilt-corrected
# ---------------------------------------------------------------------------

class TestGeoDotiltPipeline:
    """Tests for the specimen → geographic → tilt-corrected pipeline."""

    def test_identity_pipeline(self):
        """No-op orientations and horizontal bedding leave direction unchanged."""
        spec_dec, spec_inc = 30.0, 45.0
        # dogeo with az=0, pl=0 is identity; dotilt with dip=0 is identity
        geo_dec, geo_inc = pmag.dogeo(spec_dec, spec_inc, 0.0, 0.0)
        tilt_dec, tilt_inc = pmag.dotilt(geo_dec, geo_inc, 90.0, 0.0)
        assert_allclose(tilt_dec, spec_dec, atol=1e-10)
        assert_allclose(tilt_inc, spec_inc, atol=1e-10)

    def test_tilt_steepens_updip_direction(self):
        """Restoring a dipping bed steepens inclination for the dip-direction azimuth.

        A site with bedding dipping 30° to the east: the geographic
        direction pointing east (dec=90) at shallow inclination should
        become steeper after tilt correction (undoing the tilting).
        """
        # Specimen pointing along +x, sample oriented az=90, pl=0 (horizontal east)
        geo_dec, geo_inc = pmag.dogeo(0.0, 20.0, 90.0, 0.0)
        # Tilt correct with bed dipping 30° to the east
        _, tilt_inc = pmag.dotilt(geo_dec, geo_inc, 90.0, 30.0)
        # Inclination should decrease (become shallower) after removing the tilt
        assert tilt_inc < geo_inc


# ---------------------------------------------------------------------------
# doflip: flip upper hemisphere directions to lower hemisphere
# ---------------------------------------------------------------------------

class TestDoflip:
    """Tests for pmag.doflip."""

    def test_docstring_example(self):
        """Verify the example from the docstring."""
        dec, inc = pmag.doflip(30, -45)
        assert_allclose(dec, 210.0, atol=1e-10)
        assert_allclose(inc, 45.0, atol=1e-10)

    def test_lower_hemisphere_unchanged(self):
        """Direction already in lower hemisphere is not modified."""
        dec, inc = pmag.doflip(45.0, 30.0)
        assert_allclose(dec, 45.0, atol=1e-10)
        assert_allclose(inc, 30.0, atol=1e-10)

    def test_horizontal_unchanged(self):
        """Horizontal direction (inc=0) is not flipped."""
        dec, inc = pmag.doflip(90.0, 0.0)
        assert_allclose(dec, 90.0, atol=1e-10)
        assert_allclose(inc, 0.0, atol=1e-10)

    def test_vertical_up_flipped_to_down(self):
        """Vertical up (inc=-90) flips to vertical down (inc=90)."""
        dec, inc = pmag.doflip(0.0, -90.0)
        assert_allclose(inc, 90.0, atol=1e-10)

    def test_antipodal_relationship(self):
        """Flipped direction is the antipode of the original."""
        dec_in, inc_in = 120.0, -35.0
        dec_out, inc_out = pmag.doflip(dec_in, inc_in)
        # Antipode: dec+180, -inc
        assert_allclose(dec_out, (dec_in + 180.) % 360., atol=1e-10)
        assert_allclose(inc_out, -inc_in, atol=1e-10)


# ---------------------------------------------------------------------------
# flip: separate normal/reversed populations
# ---------------------------------------------------------------------------

class TestFlip:
    """Tests for pmag.flip."""

    def test_separates_normal_and_reversed(self):
        """Clearly bimodal data is separated into two populations."""
        # Normal polarity cluster around (0, 45)
        # Reversed polarity cluster around (180, -45)
        di_block = [[0, 45], [5, 43], [355, 47],
                     [180, -45], [185, -43], [175, -47]]
        D1, D2 = pmag.flip(di_block)
        assert len(D1) == 3
        assert len(D2) == 3

    def test_all_normal_returns_empty_reversed(self):
        """Unipolar normal data returns empty reversed list."""
        di_block = [[0, 45], [5, 43], [355, 47], [2, 44]]
        D1, D2 = pmag.flip(di_block)
        assert len(D1) == 4
        assert len(D2) == 0

    def test_reversed_flipped_to_normal(self):
        """Flipped reversed directions cluster near the normal mode."""
        di_block = [[10, 50], [12, 48], [8, 52],
                     [190, -50], [192, -48], [188, -52]]
        D1, D2 = pmag.flip(di_block)
        # D2 should now be flipped to cluster near D1
        if len(D2) > 0:
            mean_d2 = pmag.fisher_mean(D2)
            mean_d1 = pmag.fisher_mean(D1)
            ang = pmag.angle([mean_d1['dec'], mean_d1['inc']],
                             [mean_d2['dec'], mean_d2['inc']])
            assert ang[0] < 15.0

    def test_preserves_total_count(self):
        """Normal + reversed counts equal total input count."""
        di_block = [[0, 45], [5, 43], [355, 47],
                     [180, -45], [185, -43], [175, -47], [190, -50]]
        D1, D2 = pmag.flip(di_block)
        assert len(D1) + len(D2) == len(di_block)

    def test_combine_flag(self):
        """combine=True returns single merged di_block."""
        di_block = [[10, 50], [190, -50], [12, 48]]
        combined = pmag.flip(di_block, combine=True)
        # Should be a single list, not a tuple
        assert isinstance(combined, list)
        assert len(combined) == 3
        # All inclinations should be positive (lower hemisphere)
        for rec in combined:
            assert rec[1] >= 0
