"""
Tests for random direction sampling functions in ipmag.py.

Covers fishrot (Fisher-distributed random directions), fisher_mean_resample
(random resampling from Fisher mean), kentrot (Kent-distributed random
directions), and tk03 (TK03.GAD statistical field model).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag


# ---------------------------------------------------------------------------
# fishrot: Fisher-distributed random directions
# ---------------------------------------------------------------------------

class TestFishrot:
    """Tests for ipmag.fishrot."""

    def test_di_block_shape_single(self):
        """n=1, di_block=True returns shape (1, 3)."""
        res = ipmag.fishrot(k=10, n=1, di_block=True)
        assert res.shape == (1, 3)

    def test_di_block_shape_multiple(self):
        """n=5, di_block=True returns shape (5, 3)."""
        res = ipmag.fishrot(k=10, n=5, di_block=True)
        assert res.shape == (5, 3)

    def test_dec_inc_arrays_single(self):
        """n=1, di_block=False returns two length-1 arrays."""
        res = ipmag.fishrot(k=10, n=1, di_block=False)
        assert len(res) == 2 and res[0].shape == (1,)

    def test_dec_inc_arrays_multiple(self):
        """n=5, di_block=False returns two length-5 arrays."""
        res = ipmag.fishrot(k=10, n=5, di_block=False)
        assert len(res) == 2 and res[0].shape == (5,)

    def test_unit_vectors(self):
        """All returned intensities should be 1.0."""
        data = ipmag.fishrot(k=20, n=50, dec=40, inc=60, random_seed=0)
        assert_allclose(data[:, 2], 1.0)

    def test_mean_near_target(self):
        """Fisher mean of a large sample should be near the target direction."""
        data = ipmag.fishrot(k=50, n=500, dec=40, inc=60, random_seed=0)
        mean = ipmag.fisher_mean(dec=data[:, 0].tolist(),
                                 inc=data[:, 1].tolist())
        assert abs(mean['dec'] - 40) < 3
        assert abs(mean['inc'] - 60) < 3

    def test_reproducibility(self):
        """Same seed produces identical output."""
        a = ipmag.fishrot(k=20, n=10, dec=40, inc=60, random_seed=42)
        b = ipmag.fishrot(k=20, n=10, dec=40, inc=60, random_seed=42)
        assert_allclose(a, b)

    def test_di_block_false_matches_di_block_true(self):
        """di_block=False returns the same dec/inc as di_block=True."""
        block = ipmag.fishrot(k=20, n=5, dec=40, inc=60, random_seed=7)
        decs, incs = ipmag.fishrot(k=20, n=5, dec=40, inc=60, di_block=False,
                                   random_seed=7)
        assert_allclose(decs, block[:, 0])
        assert_allclose(incs, block[:, 1])


# ---------------------------------------------------------------------------
# fisher_mean_resample: random resampling from Fisher mean
# ---------------------------------------------------------------------------

class TestFisherMeanResample:
    """Tests for ipmag.fisher_mean_resample."""

    def test_mean_near_target(self):
        """Resampled mean should be near the input direction."""
        data = ipmag.fisher_mean_resample(alpha95=5, n=200, dec=40, inc=60,
                                          random_seed=0)
        arr = np.array(data)
        mean = ipmag.fisher_mean(dec=arr[:, 0].tolist(),
                                 inc=arr[:, 1].tolist())
        assert abs(mean['dec'] - 40) < 3
        assert abs(mean['inc'] - 60) < 3

    def test_reproducibility(self):
        """Same seed produces identical output."""
        a = ipmag.fisher_mean_resample(alpha95=5, n=10, dec=40, inc=60,
                                       random_seed=0)
        b = ipmag.fisher_mean_resample(alpha95=5, n=10, dec=40, inc=60,
                                       random_seed=0)
        assert_allclose(np.array(a), np.array(b))

    def test_di_block_false_returns_separate_lists(self):
        """di_block=False returns separate dec and inc lists."""
        decs, incs = ipmag.fisher_mean_resample(
            alpha95=5, n=5, dec=40, inc=60, di_block=False, random_seed=0
        )
        assert len(decs) == 5
        assert len(incs) == 5


# ---------------------------------------------------------------------------
# kentrot: Kent-distributed random directions
# ---------------------------------------------------------------------------

class TestKentrot:
    """Tests for ipmag.kentrot."""

    KENT_INPUT = {
        'dec': 40.824690028412704,
        'inc': 13.739412321974202,
        'Zdec': 136.30838974272072,
        'Zinc': 21.34778402689999,
        'Edec': 280.3868355366877,
        'Einc': 64.23659892174419,
        'R1': 0.9953034742972257,
        'R2': 0.009136654495119367,
    }

    def test_mean_near_target(self):
        """Mean of Kent-distributed sample should be near the mean direction."""
        data = ipmag.kentrot(self.KENT_INPUT, n=200, random_seed=0)
        arr = np.array(data)
        mean = ipmag.fisher_mean(dec=arr[:, 0].tolist(),
                                 inc=arr[:, 1].tolist())
        assert abs(mean['dec'] - self.KENT_INPUT['dec']) < 5
        assert abs(mean['inc'] - self.KENT_INPUT['inc']) < 5

    def test_unit_vectors(self):
        """All returned intensities should be 1.0."""
        data = ipmag.kentrot(self.KENT_INPUT, n=50, random_seed=0)
        arr = np.array(data)
        assert_allclose(arr[:, 2], 1.0)

    def test_reproducibility(self):
        """Same seed produces identical output."""
        a = ipmag.kentrot(self.KENT_INPUT, n=10, random_seed=42)
        b = ipmag.kentrot(self.KENT_INPUT, n=10, random_seed=42)
        assert_allclose(np.array(a), np.array(b))

    def test_di_block_false_returns_separate_arrays(self):
        """di_block=False returns separate dec and inc arrays."""
        decs, incs = ipmag.kentrot(self.KENT_INPUT, n=5, di_block=False,
                                   random_seed=0)
        assert len(decs) == 5
        assert len(incs) == 5


# ---------------------------------------------------------------------------
# tk03: TK03.GAD statistical field model
# ---------------------------------------------------------------------------

class TestTk03:
    """Tests for ipmag.tk03."""

    def test_positive_intensities(self):
        """All intensities should be positive."""
        data = ipmag.tk03(n=50, dec=0, lat=0, rev='no', random_seed=0)
        arr = np.array(data)
        assert np.all(arr[:, 2] > 0)

    def test_mean_near_gad(self):
        """Mean direction should be near the GAD field for specified latitude."""
        data = ipmag.tk03(n=500, dec=0, lat=45, rev='no', random_seed=0)
        arr = np.array(data)
        mean = ipmag.fisher_mean(dec=arr[:, 0].tolist(),
                                 inc=arr[:, 1].tolist())
        # GAD inclination at 45° latitude: arctan(2*tan(45°)) ≈ 63.4°
        expected_inc = np.degrees(np.arctan(2 * np.tan(np.radians(45))))
        assert abs(mean['dec'] - 0) < 10
        assert abs(mean['inc'] - expected_inc) < 10

    def test_reproducibility(self):
        """Same seed produces identical output."""
        a = ipmag.tk03(n=10, dec=0, lat=0, rev='no', random_seed=0)
        b = ipmag.tk03(n=10, dec=0, lat=0, rev='no', random_seed=0)
        assert_allclose(np.array(a), np.array(b))

    def test_reversals_included(self):
        """rev='yes' should produce both polarities."""
        data = ipmag.tk03(n=200, dec=0, lat=45, rev='yes', random_seed=0)
        arr = np.array(data)
        incs = arr[:, 1]
        has_positive = np.any(incs > 0)
        has_negative = np.any(incs < 0)
        assert has_positive and has_negative
