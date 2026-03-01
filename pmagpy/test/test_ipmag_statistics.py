"""
Tests for directional statistics wrapper functions in ipmag.py.

Covers ipmag.fisher_mean, ipmag.fisher_angular_deviation,
ipmag.bingham_mean, ipmag.kent_mean, ipmag.kent_distribution_95
(wrappers around pmag.py statistical functions), and MADcrit /
MADcrit_95_filter (PCA quality criteria).
"""
import numpy as np
import pytest
from numpy.testing import assert_allclose

from pmagpy import ipmag


# ---------------------------------------------------------------------------
# fisher_mean: ipmag wrapper
# ---------------------------------------------------------------------------

class TestIpmagFisherMean:
    """Tests for ipmag.fisher_mean."""

    def test_matches_doc_example(self):
        """Verify the docstring example values."""
        result = ipmag.fisher_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            'dec': 136.30838974272072,
            'inc': 21.34778402689999,
            'n': 4,
            'r': 3.9812138971889026,
            'k': 159.69251473636305,
            'alpha95': 7.292891411309177,
            'csd': 6.40977432113409,
        }
        for key, value in expected.items():
            assert_allclose(float(result[key]), value, atol=1e-10,
                            err_msg=f"Mismatch for key '{key}'")

    def test_di_block_matches_lists(self):
        """di_block input gives same result as separate dec/inc lists."""
        list_result = ipmag.fisher_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        block_result = ipmag.fisher_mean(
            di_block=[[140, 21], [127, 23], [142, 19], [136, 22]]
        )
        for key in ('dec', 'inc', 'k', 'alpha95'):
            assert_allclose(float(list_result[key]), float(block_result[key]),
                            atol=1e-10, err_msg=f"Mismatch for key '{key}'")


# ---------------------------------------------------------------------------
# fisher_angular_deviation
# ---------------------------------------------------------------------------

class TestFisherAngularDeviation:
    """Tests for ipmag.fisher_angular_deviation."""

    def test_confidence_levels(self):
        """Different confidence levels return correctly ordered angular deviations."""
        data_kwargs = {'dec': [140, 127, 142, 136], 'inc': [21, 23, 19, 22]}
        result_95 = ipmag.fisher_angular_deviation(confidence=95, **data_kwargs)
        result_63 = ipmag.fisher_angular_deviation(confidence=63, **data_kwargs)
        result_50 = ipmag.fisher_angular_deviation(confidence=50, **data_kwargs)
        assert_allclose(result_95, 11.078622283441636)
        assert_allclose(result_63, 6.40977432113409)
        assert_allclose(result_50, 5.3414786009450745)


# ---------------------------------------------------------------------------
# bingham_mean: ipmag wrapper
# ---------------------------------------------------------------------------

class TestIpmagBinghamMean:
    """Tests for ipmag.bingham_mean."""

    def test_matches_doc_example(self):
        """Verify the docstring example values."""
        result = ipmag.bingham_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            'dec': 136.32637167111312,
            'inc': 21.345186780731787,
            'Edec': 220.84075754194578,
            'Einc': -13.745780972597775,
            'Zdec': 280.38894136954474,
            'Zinc': 64.23509410796224,
            'n': 4,
            'Zeta': 9.865337027645111,
            'Eta': 9.911152230693874,
        }
        for key, value in expected.items():
            assert_allclose(float(result[key]), value, atol=1e-10,
                            err_msg=f"Mismatch for key '{key}'")


# ---------------------------------------------------------------------------
# kent_mean: ipmag wrapper
# ---------------------------------------------------------------------------

class TestIpmagKentMean:
    """Tests for ipmag.kent_mean."""

    def test_matches_doc_example(self):
        """Verify the docstring example values."""
        result = ipmag.kent_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            'dec': 136.30838974272072,
            'inc': 21.34778402689999,
            'n': 4,
            'Zdec': 40.824690028412704,
            'Zinc': 13.739412321974202,
            'Edec': 280.3868355366877,
            'Einc': 64.23659892174419,
            'Zeta': 6.789682324100879,
            'Eta': 0.7298211276091953,
            'R1': 0.9953034742972257,
            'R2': 0.009136654495119367,
        }
        for key, value in expected.items():
            assert_allclose(float(result[key]), value, atol=1e-10,
                            err_msg=f"Mismatch for key '{key}'")


# ---------------------------------------------------------------------------
# kent_distribution_95: ipmag wrapper
# ---------------------------------------------------------------------------

class TestIpmagKentDistribution95:
    """Tests for ipmag.kent_distribution_95."""

    def test_matches_doc_example(self):
        """Verify the docstring example values."""
        result = ipmag.kent_distribution_95(
            dec=[140, 127, 142, 136], inc=[21, 23, 19, 22]
        )
        expected = {
            'dec': 136.30838974272072,
            'inc': 21.34778402689999,
            'n': 4,
            'Zdec': 40.824690028412704,
            'Zinc': 13.739412321974202,
            'Edec': 280.3868355366877,
            'Einc': 64.23659892174419,
            'Zeta': 13.677129096579474,
            'Eta': 1.459760703119634,
            'R1': 0.9953034742972257,
            'R2': 0.009136654495119367,
        }
        for key, value in expected.items():
            assert_allclose(float(result[key]), value, atol=1e-10,
                            err_msg=f"Mismatch for key '{key}'")


# ---------------------------------------------------------------------------
# MADcrit / MADcrit_95_filter: PCA quality criteria
# ---------------------------------------------------------------------------

class TestMADcrit:
    """Tests for ipmag.MADcrit."""

    def test_returns_array(self):
        """MADcrit returns a numpy array of critical values."""
        mad = ipmag.MADcrit(10, np.array([0.05]), niter=10000)
        assert isinstance(mad, np.ndarray)
        assert mad.shape == (1,)

    def test_reasonable_range(self):
        """Critical MAD for N=10, alpha=0.05 is in a reasonable range."""
        mad = ipmag.MADcrit(10, np.array([0.05]), niter=10000)
        assert 20 < mad[0] < 40


class TestMADcrit95Filter:
    """Tests for ipmag.MADcrit_95_filter."""

    def test_below_threshold_returns_true(self):
        """MAD below the critical value passes the filter."""
        assert ipmag.MADcrit_95_filter(10, 30) is True

    def test_above_threshold_returns_false(self):
        """MAD above the critical value fails the filter."""
        assert ipmag.MADcrit_95_filter(10, 35) is False

    def test_edge_cases_raise_value_error(self):
        """N too small or too large raises ValueError."""
        with pytest.raises(ValueError):
            ipmag.MADcrit_95_filter(2, 10)
        with pytest.raises(ValueError):
            ipmag.MADcrit_95_filter(51, 10)
