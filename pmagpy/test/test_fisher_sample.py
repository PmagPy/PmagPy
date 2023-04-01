import numpy as np
from numpy.testing import assert_allclose

from pmagpy.ipmag import fishrot

def test_fishrot_type_1():
    res = fishrot(k=10, n=1, di_block=False)
    assert len(res)==2 and res[0].shape == (1,)
    
def test_fishrot_type_1_diblock():
    res = fishrot(k=10, n=1, di_block=True)
    assert res.shape == (1,3)
    
def test_fishrot_type_n():
    res = fishrot(k=10, n=5, di_block=False)
    assert len(res)==2 and res[0].shape == (5,)
    
def test_fishrot_type_n_diblock():
    res = fishrot(k=10, n=5, di_block=True)
    assert res.shape == (5,3)