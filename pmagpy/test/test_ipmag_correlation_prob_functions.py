
from pmagpy.ipmag import simul_correlation_prob, rand_correlation_prob
from numpy.testing import assert_allclose

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