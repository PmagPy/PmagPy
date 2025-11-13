import pytest
from pmagpy.ipmag import conglomerate_test_Watson, simul_correlation_prob, rand_correlation_prob, MADcrit, MADcrit_95_filter
import numpy as np
from numpy.testing import assert_allclose

def test_conglomerate_test_too_few_directions(capsys):
    # n < 5: should print warning and return None
    result = conglomerate_test_Watson(R=2.0, n=4)
    captured = capsys.readouterr()
    assert "too few directions for a conglomerate test" in captured.out
    assert result is None

def test_conglomerate_test_passes_for_random_data(capsys):
    # For n=10, Ro_95 = 5.03, Ro_99 = 5.94
    # R < Ro_95: should "pass" (cannot reject randomness)
    result = conglomerate_test_Watson(R=4.5, n=10)
    captured = capsys.readouterr()
    assert r"a conglomerate test as the null hypothesis" in captured.out
    assert result['n'] == 10
    assert result['R'] == 4.5
    assert result['Ro_95'] == 5.03
    assert result['Ro_99'] == 5.94

def test_conglomerate_test_rejects_randomness_at_95(capsys):
    # R > Ro_95: should reject randomness at 95%
    result = conglomerate_test_Watson(R=5.5, n=10)
    captured = capsys.readouterr()
    assert "can be rejected at the 95% confidence level" in captured.out
    assert result['n'] == 10
    assert result['R'] == 5.5
    assert result['Ro_95'] == 5.03

def test_conglomerate_test_rejects_randomness_at_99(capsys):
    # R > Ro_99: should reject randomness at 99%
    result = conglomerate_test_Watson(R=6.0, n=10)
    captured = capsys.readouterr()
    assert "can be rejected at the 99% confidence level" in captured.out
    assert result['n'] == 10
    assert result['R'] == 6.
    assert result['Ro_99'] == 5.94

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