"""
Tests for correlation probability functions in ipmag.py.

Covers simul_correlation_prob and rand_correlation_prob — Monte Carlo
methods for assessing whether two apparent polar wander paths are
significantly correlated.
"""
from numpy.testing import assert_allclose

from pmagpy import ipmag


# ---------------------------------------------------------------------------
# simul_correlation_prob
# ---------------------------------------------------------------------------

class TestSimulCorrelationProb:
    """Tests for ipmag.simul_correlation_prob."""

    def test_returns_probability(self):
        """Returns a float between 0 and 1."""
        prob = ipmag.simul_correlation_prob(alpha=10, k1=100, k2=100, trials=1000)
        assert 0 <= prob <= 1

    def test_reference_value(self):
        """Matches a known reference value within stochastic tolerance."""
        prob = ipmag.simul_correlation_prob(3.6, 391, 146, trials=1000)
        expected_prob = 0.8127
        assert_allclose(prob, expected_prob, rtol=0.05)


# ---------------------------------------------------------------------------
# rand_correlation_prob
# ---------------------------------------------------------------------------

class TestRandCorrelationProb:
    """Tests for ipmag.rand_correlation_prob."""

    def test_returns_probability(self):
        """Returns a float between 0 and 1."""
        prob = ipmag.rand_correlation_prob(
            sec_var=40, delta1=20, delta2=20, alpha=10, trials=1000
        )
        assert 0 <= prob <= 1

    def test_reference_value(self):
        """Matches a known reference value within stochastic tolerance."""
        prob = ipmag.rand_correlation_prob(40, 17.2, 20, 3.6, trials=1000)
        expected_prob = 0.0103
        assert abs(prob - expected_prob) < 0.05
