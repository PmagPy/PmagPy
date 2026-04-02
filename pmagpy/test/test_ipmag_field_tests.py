"""
Tests for paleomagnetic field stability tests in ipmag.py.

Covers bootstrap_fold_test (fold test), conglomerate_test_Watson
(conglomerate test), and reversal_test_bootstrap / reversal_test_MM1990
(reversal tests) — the standard field tests used to assess whether
magnetization predates or postdates geological events.
"""
from contextlib import redirect_stdout
from io import StringIO

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
    """Tests for ipmag.bootstrap_fold_test."""

    def test_runs_without_error(self):
        """Function executes without error on the docstring example data."""
        data = ipmag.make_diddd_array(
            [132.5, 124.3, 142.7, 130.3, 163.2],
            [12.1, 23.2, 34.2, 37.7, 32.6],
            [265.0, 265.0, 265.0, 164.0, 164.0],
            [20.0, 20.0, 20.0, 72.0, 72.0],
        )
        # Low num_sims for speed; just verify no exceptions
        ipmag.bootstrap_fold_test(data, num_sims=10, random_seed=0)

    def test_pretilt_optimal_near_100_percent(self):
        """Pre-tilt magnetization: optimal unfolding should be near 100%.

        When directions share a common pre-tilt direction but have diverse
        bedding orientations, the bootstrap fold test should find that
        maximum clustering occurs at ~100% unfolding.
        """
        target_dec, target_inc = 0.0, 45.0
        bedding = [
            (90, 30), (270, 40), (180, 25), (45, 35),
            (135, 50), (315, 20), (0, 45), (225, 30),
        ]
        rows = []
        for dd, dip in bedding:
            geo_dec, geo_inc = pmag.dotilt(target_dec, target_inc, dd, -dip)
            rows.append([geo_dec, geo_inc, dd, dip])
        data = np.array(rows)
        buf = StringIO()
        with redirect_stdout(buf):
            ipmag.bootstrap_fold_test(data, num_sims=50, random_seed=1)
        output = buf.getvalue()
        # Parse the confidence bounds from printed output
        for line in output.splitlines():
            if 'percent unfolding' in line and 'range' not in line:
                parts = line.replace('%', '').split('-')
                lower = int(parts[0].strip())
                upper = int(parts[1].split('percent')[0].strip())
                # Pre-tilt: both bounds should be near 100%
                assert lower >= 80, f"Lower bound {lower}% too low for pre-tilt data"
                assert upper <= 120, f"Upper bound {upper}% too high for pre-tilt data"
                break

    def test_posttilt_optimal_near_0_percent(self):
        """Post-tilt magnetization: optimal unfolding should be near 0%.

        When directions share a common geographic direction with diverse
        bedding, the bootstrap fold test should find maximum clustering
        at ~0% unfolding.
        """
        bedding = [
            (90, 30), (270, 40), (180, 25), (45, 35),
            (135, 50), (315, 20), (0, 45), (225, 30),
        ]
        rows = []
        for dd, dip in bedding:
            rows.append([0.0, 45.0, dd, dip])
        data = np.array(rows)
        buf = StringIO()
        with redirect_stdout(buf):
            ipmag.bootstrap_fold_test(data, num_sims=50, random_seed=2)
        output = buf.getvalue()
        # Parse the confidence bounds from printed output
        for line in output.splitlines():
            if 'percent unfolding' in line and 'range' not in line:
                parts = line.replace('%', '').split('-')
                lower = int(parts[0].strip())
                upper = int(parts[1].split('percent')[0].strip())
                # Post-tilt: both bounds should be near 0%
                assert lower >= -10, f"Lower bound {lower}% too low for post-tilt data"
                assert upper <= 20, f"Upper bound {upper}% too high for post-tilt data"
                break


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


# ---------------------------------------------------------------------------
# conglomerate_test_Watson: Watson's test for conglomerate
# ---------------------------------------------------------------------------

class TestConglomerateTestWatson:
    """Tests for ipmag.conglomerate_test_Watson."""

    def test_too_few_directions(self, capsys):
        """n < 5: should print warning and return None."""
        result = ipmag.conglomerate_test_Watson(R=2.0, n=4)
        captured = capsys.readouterr()
        assert "too few directions for a conglomerate test" in captured.out
        assert result is None

    def test_passes_for_random_data(self, capsys):
        """R < Ro_95: cannot reject randomness hypothesis."""
        result = ipmag.conglomerate_test_Watson(R=4.5, n=10)
        captured = capsys.readouterr()
        assert r"a conglomerate test as the null hypothesis" in captured.out
        assert result['n'] == 10
        assert result['R'] == 4.5
        assert result['Ro_95'] == 5.03
        assert result['Ro_99'] == 5.94

    def test_rejects_randomness_at_95(self, capsys):
        """R > Ro_95: reject randomness at 95% confidence."""
        result = ipmag.conglomerate_test_Watson(R=5.5, n=10)
        captured = capsys.readouterr()
        assert "can be rejected at the 95% confidence level" in captured.out
        assert result['n'] == 10
        assert result['R'] == 5.5
        assert result['Ro_95'] == 5.03

    def test_rejects_randomness_at_99(self, capsys):
        """R > Ro_99: reject randomness at 99% confidence."""
        result = ipmag.conglomerate_test_Watson(R=6.0, n=10)
        captured = capsys.readouterr()
        assert "can be rejected at the 99% confidence level" in captured.out
        assert result['n'] == 10
        assert result['R'] == 6.
        assert result['Ro_99'] == 5.94


# ---------------------------------------------------------------------------
# conglomerate_test_Bayes: Bayesian conglomerate test (Heslop & Roberts, 2018)
# ---------------------------------------------------------------------------

class TestConglomerateTestBayes:
    """Tests for ipmag.conglomerate_test_Bayes.

    Validates the Bayesian conglomerate test against equations and Table 2
    of Heslop & Roberts (2018, JGR: Solid Earth, 123, 1132–1142).
    """

    def test_returns_expected_keys(self, capsys):
        """Function returns dictionary with all expected keys."""
        dec = [0, 90, 180, 270, 45, 135, 225, 315]
        inc = [30, -30, 30, -30, -60, 60, -60, 60]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        assert set(result.keys()) == {'n', 'R', 'BF', 'p_HA', 'support'}
        assert result['n'] == 8

    def test_clustered_directions_favor_unimodal(self, capsys):
        """Tightly clustered directions: p(H_A|R) very small (unimodal)."""
        dec = [0, 2, 358, 1, 359, 3, 357, 0, 1, 2]
        inc = [45, 46, 44, 45, 44, 46, 43, 47, 45, 44]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        assert result['p_HA'] < 0.01
        assert 'Unimodal' in result['support']
        assert 'very strong' in result['support']

    def test_scattered_directions_favor_uniform(self, capsys):
        """Widely scattered directions: p(H_A|R) large (uniform/random)."""
        dec = [12, 85, 167, 248, 325, 53, 199, 291]
        inc = [22, -48, 63, -31, 8, -72, 41, -15]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        assert result['p_HA'] > 0.75
        assert 'Random' in result['support']

    def test_di_block_matches_dec_inc(self, capsys):
        """di_block input gives identical results to separate dec/inc lists."""
        dec = [208.8, 233.3, 220.2, 240.8, 225.4, 23.8, 29.1, 20.0]
        inc = [-51.1, -55.9, -66.0, -85.7, -76.6, -43.4, -69.4, -9.3]
        result_di = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        di_block = [[d, i] for d, i in zip(dec, inc)]
        result_block = ipmag.conglomerate_test_Bayes(di_block=di_block)
        assert_allclose(result_di['R'], result_block['R'])
        assert_allclose(result_di['BF'], result_block['BF'])
        assert_allclose(result_di['p_HA'], result_block['p_HA'])

    def test_raises_on_missing_input(self):
        """ValueError when neither dec/inc nor di_block provided."""
        try:
            ipmag.conglomerate_test_Bayes()
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_raises_on_partial_input(self):
        """ValueError when only dec is provided (no inc)."""
        try:
            ipmag.conglomerate_test_Bayes(dec=[0, 90, 180])
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_high_kappa_fisher_favors_unimodal(self, capsys):
        """Fisher-distributed directions with high kappa favor unimodal.

        Uses fishrot to generate realistic clustered directions (R < N)
        avoiding the R=N edge case where the integral diverges.
        """
        dirs = ipmag.fishrot(k=200, n=10, dec=0, inc=45, random_seed=100)
        dec = [d[0] for d in dirs]
        inc = [d[1] for d in dirs]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        assert result['p_HA'] < 0.05
        assert 'Unimodal' in result['support']

    def test_bayes_factor_relationship(self, capsys):
        """Verify p(H_A|R) = BF / (BF + 1) (Equation 13)."""
        dec = [208.8, 233.3, 220.2, 240.8, 225.4, 23.8, 29.1, 20.0]
        inc = [-51.1, -55.9, -66.0, -85.7, -76.6, -43.4, -69.4, -9.3]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        expected_p_HA = result['BF'] / (1.0 + result['BF'])
        assert_allclose(result['p_HA'], expected_p_HA, rtol=1e-10)

    def test_docstring_example(self, capsys):
        """Docstring example runs and returns reasonable results."""
        dec = [208.8, 233.3, 220.2, 240.8, 225.4, 23.8, 29.1, 20.0]
        inc = [-51.1, -55.9, -66.0, -85.7, -76.6, -43.4, -69.4, -9.3]
        result = ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        assert result['n'] == 8
        assert 0 < result['R'] < 8
        assert result['BF'] > 0
        assert 0 < result['p_HA'] < 1

    def test_prints_output(self, capsys):
        """Function prints summary output to stdout."""
        dec = [208.8, 233.3, 220.2, 240.8, 225.4, 23.8, 29.1, 20.0]
        inc = [-51.1, -55.9, -66.0, -85.7, -76.6, -43.4, -69.4, -9.3]
        ipmag.conglomerate_test_Bayes(dec=dec, inc=inc)
        captured = capsys.readouterr()
        assert "N = 8" in captured.out
        assert "R =" in captured.out
        assert "Bayes factor" in captured.out
        assert "p(H_A|R)" in captured.out
        assert "Result:" in captured.out


# ---------------------------------------------------------------------------
# Reversal tests
# ---------------------------------------------------------------------------

class TestReversalTests:
    """Tests for ipmag reversal test functions."""

    def test_reversal_test_bootstrap_passes_for_antipodal_data(self):
        """Bootstrap reversal test passes for truly antipodal directions."""
        normal = ipmag.fishrot(k=30, n=12, dec=40, inc=60, random_seed=24)
        reverse = ipmag.fishrot(k=30, n=12, dec=220, inc=-60, random_seed=25)
        combined = np.vstack((normal, reverse)).tolist()
        result = ipmag.reversal_test_bootstrap(di_block=combined, verbose=False,
                                               random_seed=26)
        assert result == 1

    def test_reversal_test_bootstrap_h23_returns_tuple(self):
        """Bootstrap H23 reversal test returns a 4-element tuple."""
        normal = ipmag.fishrot(k=30, n=12, dec=40, inc=60, random_seed=27)
        reverse = ipmag.fishrot(k=30, n=12, dec=220, inc=-60, random_seed=28)
        combined = np.vstack((normal, reverse)).tolist()
        result = ipmag.reversal_test_bootstrap_H23(
            di_block=combined,
            num_sims=20,
            alpha=0.1,
            plot=False,
            verbose=False,
            random_seed=29,
        )
        assert result[0] == 1
        assert len(result) == 4

    def test_reversal_test_bootstrap_fails_for_non_antipodal_data(self):
        """Bootstrap reversal test fails for clearly non-antipodal directions.

        Two populations offset by only ~60° (not ~180°) should fail the
        reversal test — they are not consistent with antipodal means.
        """
        pop1 = ipmag.fishrot(k=50, n=15, dec=0, inc=50, random_seed=40)
        pop2 = ipmag.fishrot(k=50, n=15, dec=240, inc=-50, random_seed=41)
        combined = np.vstack((pop1, pop2)).tolist()
        result = ipmag.reversal_test_bootstrap(di_block=combined, verbose=False,
                                               random_seed=42)
        assert result == 0

    def test_reversal_test_mm1990_runs(self):
        """McFadden & McElhinny (1990) reversal test executes successfully."""
        normal = ipmag.fishrot(k=20, n=6, dec=40, inc=60, random_seed=30)
        reverse = ipmag.fishrot(k=20, n=6, dec=220, inc=-60, random_seed=31)
        combined = np.vstack((normal, reverse)).tolist()
        with redirect_stdout(StringIO()):
            result = ipmag.reversal_test_MM1990(
                di_block=combined, plot_CDF=False, plot_stereo=False
            )
        assert isinstance(result, tuple)
        assert result[0] == 1
