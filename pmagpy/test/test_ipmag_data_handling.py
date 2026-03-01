"""
Tests for data handling and conversion functions in ipmag.py.

Covers make_di_block / unpack_di_block (direction block construction),
do_flip (antipodal directions), separate_directions (normal/reverse
splitting), and dms2dd (degree-minute-second to decimal degree conversion).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag


# ---------------------------------------------------------------------------
# make_di_block / unpack_di_block
# ---------------------------------------------------------------------------

class TestMakeDiBlock:
    """Tests for ipmag.make_di_block."""

    def test_unit_vectors(self):
        """Default output includes unit intensity as third element."""
        dec = [180.3, 179.2]
        inc = [12.1, 13.7]
        expected = [[180.3, 12.1, 1.0], [179.2, 13.7, 1.0]]
        assert ipmag.make_di_block(dec, inc) == expected

    def test_non_unit_vectors(self):
        """unit_vector=False omits the intensity column."""
        dec = [180.3, 179.2]
        inc = [12.1, 13.7]
        expected = [[180.3, 12.1], [179.2, 13.7]]
        assert ipmag.make_di_block(dec, inc, unit_vector=False) == expected


class TestUnpackDiBlock:
    """Tests for ipmag.unpack_di_block."""

    def test_returns_components(self):
        """Unpacks a di_block with intensity into dec, inc, moment."""
        di_block = [[180.3, 12.1, 0.5], [179.2, 13.7, 0.7]]
        dec, inc, moment = ipmag.unpack_di_block(di_block)
        assert_allclose(dec, [180.3, 179.2])
        assert_allclose(inc, [12.1, 13.7])
        assert_allclose(moment, [0.5, 0.7])

    def test_handles_missing_moment(self):
        """Unpacks a di_block without intensity (moment is empty list)."""
        di_block = [[10.0, 20.0], [30.0, 40.0]]
        dec, inc, moment = ipmag.unpack_di_block(di_block)
        assert_allclose(dec, [10.0, 30.0])
        assert_allclose(inc, [20.0, 40.0])
        assert moment == []


# ---------------------------------------------------------------------------
# do_flip: antipodal direction conversion
# ---------------------------------------------------------------------------

class TestDoFlip:
    """Tests for ipmag.do_flip."""

    def test_with_lists_returns_antipodes(self):
        """Flipping dec/inc lists returns antipodal directions."""
        dec_flip, inc_flip = ipmag.do_flip([1.0, 358.0], [10.0, -5.0])
        assert_allclose(dec_flip, [181.0, 178.0])
        assert_allclose(inc_flip, [-10.0, 5.0])

    def test_with_di_block_preserves_unit_vectors(self):
        """Flipping a di_block normalizes intensity to 1.0."""
        di_block = [[10.0, 20.0, 0.7], [350.0, -30.0, 0.4]]
        flipped = ipmag.do_flip(di_block=di_block)
        expected = np.array([[190.0, -20.0, 1.0], [170.0, 30.0, 1.0]])
        assert_allclose(np.array(flipped), expected)


# ---------------------------------------------------------------------------
# separate_directions: normal/reverse mode splitting
# ---------------------------------------------------------------------------

class TestSeparateDirections:
    """Tests for ipmag.separate_directions."""

    def test_splits_modes(self):
        """Correctly separates normal and reverse polarity directions."""
        decs_n, incs_n = ipmag.fishrot(k=30, n=8, dec=10, inc=45, di_block=False,
                                       random_seed=21)
        decs_r, incs_r = ipmag.fishrot(k=30, n=8, dec=200, inc=-45, di_block=False,
                                       random_seed=22)
        all_dec = list(decs_n) + list(decs_r)
        all_inc = list(incs_n) + list(incs_r)
        dec1, inc1, dec2, inc2 = ipmag.separate_directions(dec=all_dec, inc=all_inc)
        assert len(dec1) == 8
        assert len(dec2) == 8
        assert np.mean(inc1) > 0
        assert np.mean(inc2) < 0


# ---------------------------------------------------------------------------
# dms2dd: degree-minute-second to decimal degree
# ---------------------------------------------------------------------------

class TestDms2dd:
    """Tests for ipmag.dms2dd."""

    def test_basic_conversion(self):
        """Converts 180° 4' 23\" to decimal degrees."""
        result = ipmag.dms2dd(180, 4, 23)
        assert_allclose(result, 180.07305555555556, atol=1e-10)

    def test_zero_minutes_seconds(self):
        """Whole degrees with zero minutes and seconds."""
        result = ipmag.dms2dd(45, 0, 0)
        assert_allclose(result, 45.0, atol=1e-10)

    def test_thirty_minutes_is_half_degree(self):
        """30 minutes equals 0.5 degrees."""
        result = ipmag.dms2dd(0, 30, 0)
        assert_allclose(result, 0.5, atol=1e-10)

    def test_seconds_only(self):
        """3600 seconds equals 1 degree."""
        result = ipmag.dms2dd(0, 0, 3600)
        assert_allclose(result, 1.0, atol=1e-10)

    def test_negative_degrees(self):
        """Negative degrees (southern hemisphere) preserved."""
        result = ipmag.dms2dd(-33, 51, 36)
        # -33 + 51/60 + 36/3600 = -33 + 0.86 = -32.14
        assert_allclose(result, -33 + 51/60 + 36/3600, atol=1e-10)

    def test_string_inputs_accepted(self):
        """String numeric inputs are converted correctly."""
        result = ipmag.dms2dd('45', '30', '0')
        assert_allclose(result, 45.5, atol=1e-10)
