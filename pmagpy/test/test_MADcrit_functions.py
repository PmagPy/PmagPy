import pytest
import numpy as np

from pmagpy.ipmag import MADcrit, MADcrit_95_filter

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