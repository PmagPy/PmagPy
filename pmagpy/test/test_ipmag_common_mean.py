"""
Tests for common mean comparison functions in ipmag.py.

Covers mean_bootstrap_confidence, common_mean_bootstrap,
common_mean_bootstrap_H23, common_mean_watson, and common_mean_bayes —
methods for testing whether two directional datasets share a common mean.
"""
from contextlib import redirect_stdout
from io import StringIO

import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag, pmag


# ---------------------------------------------------------------------------
# mean_bootstrap_confidence
# ---------------------------------------------------------------------------

class TestMeanBootstrapConfidence:
    """Tests for ipmag.mean_bootstrap_confidence."""

    def test_returns_bounds(self):
        """Mean matches Fisher mean and boundary array has expected shape."""
        dec = [40, 41, 39, 38, 42]
        inc = [60, 61, 59, 62, 58]
        fisher = ipmag.fisher_mean(dec=dec, inc=inc)
        pars, boundary = ipmag.mean_bootstrap_confidence(
            dec=dec, inc=inc, num_sims=20, random_seed=0,
        )
        assert_allclose(float(pars['dec']), fisher['dec'], atol=0.1)
        assert_allclose(float(pars['inc']), fisher['inc'], atol=0.1)
        assert float(pars['T_critical']) > 0
        boundary_array = np.array(boundary)
        assert boundary_array.shape[1] == 3
        assert len(boundary_array) > 0


# ---------------------------------------------------------------------------
# common_mean_bootstrap
# ---------------------------------------------------------------------------

class TestCommonMeanBootstrap:
    """Tests for ipmag.common_mean_bootstrap."""

    def test_identifies_common_mean(self):
        """Detects a common mean for data drawn from the same distribution."""
        data1 = ipmag.fishrot(k=40, n=20, dec=40, inc=60, random_seed=0)
        data2 = ipmag.fishrot(k=45, n=20, dec=40, inc=60, random_seed=1)
        result = ipmag.common_mean_bootstrap(data1, data2, NumSims=20,
                                             verbose=False, random_seed=2)
        assert result == 1

    def test_detects_difference(self):
        """Detects different means for data from widely separated distributions."""
        data1 = ipmag.fishrot(k=40, n=20, dec=200, inc=-20, random_seed=0)
        data2 = ipmag.fishrot(k=45, n=20, dec=20, inc=60, random_seed=1)
        result = ipmag.common_mean_bootstrap(data1, data2, NumSims=20,
                                             verbose=False, random_seed=3)
        assert result == 0

    def test_handles_single_direction(self):
        """Handles comparison of dataset against a single direction."""
        data1 = ipmag.fishrot(k=40, n=20, dec=40, inc=60, random_seed=0)
        result = ipmag.common_mean_bootstrap(data1, [40, 60], NumSims=20,
                                             verbose=False, random_seed=4)
        assert result == 1


# ---------------------------------------------------------------------------
# common_mean_bootstrap_H23
# ---------------------------------------------------------------------------

class TestCommonMeanBootstrapH23:
    """Tests for ipmag.common_mean_bootstrap_H23."""

    def test_returns_expected_tuple(self):
        """Returns a 4-element tuple."""
        data1 = ipmag.fishrot(k=35, n=15, dec=30, inc=50, random_seed=5)
        data2 = ipmag.fishrot(k=37, n=15, dec=32, inc=51, random_seed=6)
        result = ipmag.common_mean_bootstrap_H23(
            data1,
            data2,
            num_sims=25,
            alpha=0.1,
            plot=False,
            verbose=False,
            random_seed=7,
        )
        assert isinstance(result, tuple)
        assert len(result) == 4

    @staticmethod
    def run_with_eigenvector_sign(monkeypatch, sign, data1, data2):
        """Run the test with np.linalg.eig returning eigenvectors multiplied by sign."""
        eig = np.linalg.eig

        def signed_eig(A):
            D, V = eig(A)
            return D, sign * V

        monkeypatch.setattr(np.linalg, "eig", signed_eig)
        result = ipmag.common_mean_bootstrap_H23(
            data1, data2, num_sims=200, plot=False, random_seed=42)
        monkeypatch.setattr(np.linalg, "eig", eig)
        return np.array(result, dtype=float)

    def test_independent_of_eigenvector_sign(self, monkeypatch):
        """Regression: the eigenvector for the common mean has an arbitrary sign. When
        it came back antipodal to the data, each sample was rotated by ~180 degrees
        onto it, which changed the bootstrap critical value and p-value."""
        data1 = ipmag.fishrot(k=20, n=20, dec=30, inc=50, random_seed=8)
        data2 = ipmag.fishrot(k=25, n=15, dec=40, inc=58, random_seed=9)
        as_returned = self.run_with_eigenvector_sign(monkeypatch, 1, data1, data2)
        flipped = self.run_with_eigenvector_sign(monkeypatch, -1, data1, data2)
        assert_allclose(flipped, as_returned, rtol=1e-12)

    def test_nearly_identical_datasets(self, monkeypatch):
        """Regression: for a dataset compared with itself after a round trip through
        Cartesian coordinates, an antipodal eigenvector gave nearly antiparallel
        vectors to form_Q, whose output was not a rotation, and a critical value
        many times too large. The result should match comparing the dataset with
        itself exactly."""
        data1 = np.array(ipmag.fishrot(k=20, n=20, dec=30, inc=50, random_seed=8))
        data2 = pmag.cart2dir(pmag.dir2cart(data1))[:, :2]
        exact = self.run_with_eigenvector_sign(monkeypatch, 1, data1, data1)
        for sign in [1, -1]:
            round_trip = self.run_with_eigenvector_sign(monkeypatch, sign, data1, data2)
            assert_allclose(round_trip, exact, rtol=1e-6, atol=1e-9)


# ---------------------------------------------------------------------------
# common_mean_watson
# ---------------------------------------------------------------------------

class TestCommonMeanWatson:
    """Tests for ipmag.common_mean_watson."""

    def test_pass_and_fail(self):
        """Passes for similar means and fails for different means."""
        data1 = ipmag.fishrot(k=40, n=10, dec=40, inc=60, random_seed=11)
        data2 = ipmag.fishrot(k=45, n=10, dec=41, inc=59, random_seed=12)
        with redirect_stdout(StringIO()):
            pass_result = ipmag.common_mean_watson(data1, data2, NumSims=25,
                                                   plot='no', random_seed=13)
        assert pass_result[0] == 1
        assert pass_result[3] in {'A', 'B', 'C', 'indeterminate'}

        data3 = ipmag.fishrot(k=10, n=10, dec=200, inc=-30, random_seed=14)
        data4 = ipmag.fishrot(k=10, n=10, dec=20, inc=40, random_seed=15)
        with redirect_stdout(StringIO()):
            fail_result = ipmag.common_mean_watson(data3, data4, NumSims=25,
                                                   plot='no', random_seed=16)
        assert fail_result[0] == 0
        assert fail_result[3] == ''


# ---------------------------------------------------------------------------
# common_mean_bayes
# ---------------------------------------------------------------------------

class TestCommonMeanBayes:
    """Tests for ipmag.common_mean_bayes."""

    def test_support_messages(self):
        """Returns correct support messages for common vs. different means."""
        data1 = ipmag.fishrot(k=40, n=15, dec=45, inc=55, random_seed=17)
        data2 = ipmag.fishrot(k=42, n=15, dec=46, inc=54, random_seed=18)
        with redirect_stdout(StringIO()):
            bayes_pass = ipmag.common_mean_bayes(data1, data2)
        assert bayes_pass[1] > 0.5
        assert 'Common mean' in bayes_pass[2]

        data3 = ipmag.fishrot(k=20, n=15, dec=120, inc=-30, random_seed=19)
        data4 = ipmag.fishrot(k=20, n=15, dec=320, inc=30, random_seed=20)
        with redirect_stdout(StringIO()):
            bayes_fail = ipmag.common_mean_bayes(data3, data4)
        assert bayes_fail[1] < 0.1
        assert 'Different means' in bayes_fail[2]
