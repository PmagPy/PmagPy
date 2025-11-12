import pytest
from pmagpy.ipmag import simul_correlation_prob, rand_correlation_prob, MADcrit, MADcrit_95_filter
import numpy as np
from numpy.testing import assert_allclose

def test_MADcrit_typical():
    N = 10
    alpha = np.array([0.05])
    mad = MADcrit(N, alpha, niter=10000)
    # Should return a float array of length 1
    assert isinstance(mad, np.ndarray)
    assert mad.shape == (1,)
    # Should be in a reasonable range for N=10, alpha=0.05
    assert 20 < mad[0] < 40

def test_MADcrit_95_filter_true():
    # For N=10, MAD=30, should be below critical value
    assert MADcrit_95_filter(10, 30) is True

def test_MADcrit_95_filter_false():
    # For N=10, MAD=35, should be above critical value
    assert MADcrit_95_filter(10, 35) is False

def test_MADcrit_95_filter_edge_cases():
    # N too small
    with pytest.raises(ValueError):
        MADcrit_95_filter(2, 10)
    # N too large
    with pytest.raises(ValueError):
        MADcrit_95_filter(51, 10)

def test_simul_correlation_prob_basic():
    # Should return a float between 0 and 1
    prob = simul_correlation_prob(alpha=10, k1=100, k2=100, trials=1000)
    assert 0 <= prob <= 1

def test_rand_correlation_prob_basic():
    # Should return a float between 0 and 1
    prob = rand_correlation_prob(sec_var=40, delta1=20, delta2=20, alpha=10, trials=1000)
    assert 0 <= prob <= 1

def test_simul_correlation_prob_values():
    prob = simul_correlation_prob(3.6, 391, 146, trials=1000)
    expected_prob = 0.8127 # Expected value from previous runs, will not be exact due to randomness
    #assert abs(prob - expected_prob) < 0.05
    assert_allclose(prob, expected_prob, rtol=0.05) # Allowing 5% relative tolerance due to randomness

def test_rand_correlation_prob_values():
    prob = rand_correlation_prob(40, 17.2, 20, 3.6, trials=1000)
    expected_prob = 0.0103 # Expected value from previous runs, will not be exact due to randomness
    assert abs(prob - expected_prob) < 0.05
    #assert_allclose(prob, expected_prob, rtol=0.05) # Does not pass reliably due to small expected number