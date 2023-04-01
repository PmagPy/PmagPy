from pmagpy import ipmag
from numpy.testing import assert_allclose


def test_IGRF():
    
    result = ipmag.igrf([1999, 30, 20, 50])
    reference = [1.20288657e+00, 2.82331112e+01, 3.9782338913649881e+04]

    print(result, reference)
    
    assert_allclose(result, reference, rtol=.1)


