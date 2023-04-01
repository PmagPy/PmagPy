import numpy as np
from numpy.testing import assert_allclose

from pmagpy.pmag import dodirot, dodirot_V

def test_dodirot_type():
    assert isinstance(dodirot(0,90,5,85), tuple)

def test_dodirot_1():
    assert_allclose(dodirot(0,90,5,85), (5.0, 85.0), rtol=10e-4)
    
def test_dodirot_V_type():
    di_array = np.array([[0,90],[0,90],[0,90]])
    assert isinstance(dodirot_V(di_array,5,15), np.ndarray)

def test_dodirot_V_1():
    di_array = np.array([[0,90],[0,90],[0,90]])
    result = np.array([[ 5., 15.],
                       [ 5., 15.],
                       [ 5., 15.]])
    assert_allclose(dodirot_V(di_array,5,15), result, rtol=10e-4)