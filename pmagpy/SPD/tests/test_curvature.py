#!/usr/bin/env python

import numpy
import unittest
#import sys
#sys.path.append('/Users/nebula/Python')
#from SPD_project.lib import lib_curvature as lib_k
import SPD.lib.lib_curvature as lib_k


class CheckCircle(unittest.TestCase):
    
    def test_for_too_few_values(self):
        XY = [[1,2],[3,4],[5,10]]
        Par = [1,2,7]
        self.assertRaises(Warning, lib_k.VarCircle, XY, Par)

    def test_var_circle(self):
        XY = [[1.,2.], [3.,2.], [4.,7.], [7., 9.]]
        Par = [1,3,5]
        result = lib_k.VarCircle(XY, Par)
        ref_circle = 35.786506482616396
        self.assertAlmostEqual(ref_circle, result)

        
class CheckTaubinSVD(unittest.TestCase):

    def test_taubin_svd(self):
        XY = [[1.,2.], [3.,2.], [4.,7.], [7., 9.]]
        ref_a, ref_b, ref_r = 10.150772636178328, 1.2388221329539486, 8.3248933499238511
        result = lib_k.TaubinSVD(XY)
        self.assertAlmostEqual(ref_a, result[0])
        self.assertAlmostEqual(ref_b, result[1])
        self.assertAlmostEqual(ref_r, result[2])
    
class CheckLMA(unittest.TestCase):

    def test_LMA(self):
        xy = numpy.array([[1,1],[0.,-2.], [.5,3.], [4., 5.]])
        par_ini = [21.2500,   -9.5000,   22.5347]
        result = lib_k.LMA(xy, par_ini)
        ref_a, ref_b, ref_r = 6.4081037896973703, -0.7768791340451443, 6.3717959414186254
        self.assertAlmostEqual(ref_a, result[0])
        self.assertAlmostEqual(ref_b, result[1])
        self.assertAlmostEqual(ref_r, result[2])

class CheckAraiCurvature(unittest.TestCase):

    def test_Arai_Curvature(self):# this will have to be changed if norming was done in error
        x_real = [0.1218238 ,  0.18767432,  0.21711849,  0.32091412,  0.48291503, 0.72423703,  1.03139876]
        y_real = [ 0.98795181,  0.95783133,  0.96987952,  0.98192771,  0.93373494, 0.90361446,  0.81325301]
        result = lib_k.AraiCurvature(x_real, y_real)
        ref_k, ref_a, ref_b, ref_SSE = -0.32125602341857323, -0.010592347506742775, -2.1199858242798424, 8.4994e-04
        self.assertAlmostEqual(ref_k, result[0])
        self.assertAlmostEqual(ref_a, result[1])
        self.assertAlmostEqual(ref_b, result[2])
        self.assertAlmostEqual(ref_SSE, result[3])


if __name__ == "__main__":
    unittest.main()
