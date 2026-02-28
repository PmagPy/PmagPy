"""
Tests for the bootstrap fold test in ipmag.py.

Covers make_diddd_array (helper) and the scientific principle underlying
bootstrap_fold_test: pre-tilt magnetization should yield tighter clustering
after tilt correction, while post-tilt magnetization should not.
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag, pmag


# ---------------------------------------------------------------------------
# make_diddd_array: helper to construct fold test input
# ---------------------------------------------------------------------------

class TestMakeDidddArray:
    """Tests for ipmag.make_diddd_array."""

    def test_docstring_example(self):
        """Verify the docstring example."""
        dec = [132.5, 124.3, 142.7, 130.3, 163.2]
        inc = [12.1, 23.2, 34.2, 37.7, 32.6]
        dip_direction = [265.0, 265.0, 265.0, 164.0, 164.0]
        dip = [20.0, 20.0, 20.0, 72.0, 72.0]
        result = ipmag.make_diddd_array(dec, inc, dip_direction, dip)
        assert result.shape == (5, 4)
        assert_allclose(result[0], [132.5, 12.1, 265.0, 20.0])
        assert_allclose(result[-1], [163.2, 32.6, 164.0, 72.0])

    def test_output_is_numpy_array(self):
        """Output is a numpy array, not a list."""
        result = ipmag.make_diddd_array([0], [45], [90], [30])
        assert isinstance(result, np.ndarray)
        assert result.shape == (1, 4)


# ---------------------------------------------------------------------------
# bootstrap_fold_test: smoke test
# ---------------------------------------------------------------------------

class TestBootstrapFoldTest:
    """Smoke test for ipmag.bootstrap_fold_test."""

    def test_runs_without_error(self, seed):
        """Function executes without error on the docstring example data."""
        data = ipmag.make_diddd_array(
            [132.5, 124.3, 142.7, 130.3, 163.2],
            [12.1, 23.2, 34.2, 37.7, 32.6],
            [265.0, 265.0, 265.0, 164.0, 164.0],
            [20.0, 20.0, 20.0, 72.0, 72.0],
        )
        # Low num_sims for speed; just verify no exceptions
        ipmag.bootstrap_fold_test(data, num_sims=10)


# ---------------------------------------------------------------------------
# Fold test principle: tilt correction improves clustering for pre-tilt
# magnetization but not for post-tilt magnetization
# ---------------------------------------------------------------------------

class TestFoldTestPrinciple:
    """Test the scientific principle underlying the bootstrap fold test.

    Uses pmag.dotilt_V and pmag.doprinc directly rather than the full
    bootstrap machinery, so the test is fast and deterministic.
    """

    @staticmethod
    def _make_pretilt_data():
        """Create synthetic pre-tilt magnetization data.

        All directions share a common pre-tilt direction (Dec=0, Inc=45)
        but have different bedding orientations, so they scatter in
        geographic coordinates.
        """
        target_dec, target_inc = 0.0, 45.0
        bedding = [
            (90, 30), (270, 40), (180, 25), (45, 35),
            (135, 50), (315, 20), (0, 45), (225, 30),
        ]
        rows = []
        for dd, dip in bedding:
            # Reverse the tilt to get the geographic direction
            geo_dec, geo_inc = pmag.dotilt(target_dec, target_inc, dd, -dip)
            rows.append([geo_dec, geo_inc, dd, dip])
        return np.array(rows)

    @staticmethod
    def _make_posttilt_data():
        """Create synthetic post-tilt magnetization data.

        All directions share a common geographic direction (Dec=0, Inc=45)
        with different bedding orientations, so tilt correction scatters them.
        """
        bedding = [
            (90, 30), (270, 40), (180, 25), (45, 35),
            (135, 50), (315, 20), (0, 45), (225, 30),
        ]
        rows = []
        for dd, dip in bedding:
            rows.append([0.0, 45.0, dd, dip])
        return np.array(rows)

    def test_pretilt_improves_with_tilt_correction(self):
        """Pre-tilt data clusters better after tilt correction (tau1 increases)."""
        data = self._make_pretilt_data()
        # Geographic (uncorrected): should be scattered
        geo_ppars = pmag.doprinc(data[:, :2].tolist())
        # Tilt-corrected: should be tightly clustered
        D, I = pmag.dotilt_V(data)
        tc_dirs = np.column_stack([D, I]).tolist()
        tc_ppars = pmag.doprinc(tc_dirs)
        assert tc_ppars['tau1'] > geo_ppars['tau1']

    def test_posttilt_worsens_with_tilt_correction(self):
        """Post-tilt data clusters worse after tilt correction (tau1 decreases)."""
        data = self._make_posttilt_data()
        # Geographic (uncorrected): should be perfectly clustered
        geo_ppars = pmag.doprinc(data[:, :2].tolist())
        # Tilt-corrected: should scatter
        D, I = pmag.dotilt_V(data)
        tc_dirs = np.column_stack([D, I]).tolist()
        tc_ppars = pmag.doprinc(tc_dirs)
        assert geo_ppars['tau1'] > tc_ppars['tau1']

    def test_pretilt_corrected_tau1_near_one(self):
        """Tilt correction of pre-tilt data gives tau1 close to 1 (perfect cluster)."""
        data = self._make_pretilt_data()
        D, I = pmag.dotilt_V(data)
        tc_dirs = np.column_stack([D, I]).tolist()
        tc_ppars = pmag.doprinc(tc_dirs)
        assert tc_ppars['tau1'] > 0.99
