#! /usr/bin/env python

from __future__ import division
from past.utils import old_div
import unittest
import numpy
import copy
import math
import sys
#if '/Users/nebula/Python' not in sys.path:
#    sys.path.append('/Users/nebula/Python')
import SPD.lib.lib_directional_statistics as lib_direct
import SPD.spd as spd
from SPD.test_instance import PintPars_example
#import known_values
#import lib_directional_statistics as lib_direct
PintPars_example.calculate_all_statistics()
#thing1 = spd.thing1

class CheckDecInc(unittest.TestCase):
    
    zdata = [[0., 0., 0.],[1., 1., 1.],[1., 2., 3.], [2., 4., 4.5], [2., 3., 7.5], [0., 0., 0.]]
    zdata_segment = [[1., 1., 1.],[1., 2., 3.], [2., 4., 4.5], [2., 3., 7.5]]

    t_Arai = [1.,1.5, 3, 8, 10, 11]
    tmin = 1.5
    tmax = 10.

    X1_avg = 1.5
    X2_avg = 2.5
    X3_avg = 4.

    X1_prime = [-.5, -.5, .5, .5]
    X2_prime = [-1.5, -.5, 1.5, .5]
    X3_prime = [-3., -1., .5, 3.5]

    X1 = [ 1.,  1.,  2.,  2.] 
    X2 = [ 1.,  2.,  4.,  3.] 
    X3 = [ 1.,   3.,   4.5,  7.5]

    X1_p = numpy.array(X1_prime)
    X2_p = numpy.array(X2_prime)
    X3_p = numpy.array(X3_prime)

    orientation_tensor = lib_direct.get_orientation_tensor(X1_prime, X2_prime, X3_prime) # too complex to want to calculate by hand
#    reference_vector = (-1., -2., -6.5) # not currently testing this

    def test_zdata_segment(self):
        result = lib_direct.get_zdata_segment(self.zdata, self.t_Arai, self.tmin, self.tmax)
        self.assertEqual(result, self.zdata_segment)

    def test_cart_averages(self):
        result = lib_direct.get_cart_primes_and_means(self.zdata_segment, anchored=False)
        self.assertEqual(result['X1_mean'], self.X1_avg)
        self.assertEqual(result['X2_mean'], self.X2_avg)
        self.assertEqual(result['X3_mean'], self.X3_avg)

    def test_cart_primes(self):
        result = lib_direct.get_cart_primes_and_means(self.zdata_segment, anchored=False)
        self.assertEqual(result['X1_prime'], self.X1_prime)
        self.assertEqual(result['X2_prime'], self.X2_prime)
        self.assertEqual(result['X3_prime'], self.X3_prime)

    def test_orientation_tensor(self):
        X1_prime = [1., 2.]
        X2_prime = [1., 1.]
        X3_prime = [-1., -.5]
        orient_tensor = numpy.array([[5., 3., -2.],
                                     [3., 2., -1.5],
                                     [-2., -1.5, 1.25]])
        orient_tensor = orient_tensor
        result = lib_direct.get_orientation_tensor(X1_prime, X2_prime, X3_prime)
        #print "result", result
        #print "orient_tensor", orient_tensor
        v = numpy.allclose(result['orient_tensor'], orient_tensor) # assesses two arrays for if they are approximately eq
        self.assertTrue(v)

    def test_PD_direction(self):
        X1_prime, X2_prime, X3_prime = [1., 3.], [5., 2.], [8., 7.]
        PD = [1., 2., 3.]
        result = lib_direct.get_PD_direction(X1_prime, X2_prime, X3_prime, PD)
        ref_PD = [1., 2., 3.]
        for num, ref in enumerate(ref_PD):
            self.assertAlmostEqual(ref, result[num])
        
    def test_PD_direction_negative(self):
        X1_prime, X2_prime, X3_prime = [1., 3.], [2., 5.], [8., 7.]
        PD = [1., 2., 3.]
        result = lib_direct.get_PD_direction(X1_prime, X2_prime, X3_prime, PD)
        ref_PD = [-1., -2.,-3.]
        #print "ref, result", ref_PD, result
        for num, ref in enumerate(ref_PD):
            self.assertAlmostEqual(ref, result[num])


    def test_get_dec_and_inc(self): # testing full thing with real data
        dec, inc, intenstiy, tau, V, means, PCA_sigma = lib_direct.get_dec_and_inc(PintPars_example.zdata, PintPars_example.t_Arai, PintPars_example.tmin, PintPars_example.tmax, anchored=False)
        self.assertAlmostEqual(dec, 267.4620127216387)
        self.assertAlmostEqual(inc, 86.349431762792364)
        self.assertGreaterEqual(tau[0], tau[1]) 
        self.assertGreaterEqual(tau[1], tau[2])


class CheckMad(unittest.TestCase):
    
    tau1 = .1
    tau2 = .2
    tau3 = .3
    tau = [tau1, tau2, tau3]
    ref_MAD = math.degrees(numpy.arctan(numpy.sqrt(5.)))

    def test_MAD(self):
        MAD = lib_direct.get_MAD(self.tau)
        self.assertAlmostEqual(MAD, self.ref_MAD)


class CheckAlpha(unittest.TestCase):

    d1 = [-1., 2.]
    d2 = [3., 4.]
    ref_alpha = numpy.arccos(old_div(5., (numpy.sqrt(5) * 5))) # 1.1071487177940904
    ref_alpha_degrees = math.degrees(ref_alpha)

    ref_real_alpha = 2.074709711008407

    def test_alpha(self):
        result = lib_direct.get_alpha(self.d1, self.d2)
        self.assertAlmostEqual(self.ref_alpha_degrees, result)

    def test_alpha_real_data(self):
        self.assertAlmostEqual(PintPars_example.pars['specimen_int_alpha'], self.ref_real_alpha)

#    1*3 + 2 * 4

class CheckDang(unittest.TestCase):
    
    v1, v2 = [1., -2., 3.], [0.5, 4., 5.]
#    v2 = 
    dot_product =7.5 # .5 + (-6.) + 15.
    mag1 = numpy.sqrt(14.)#(1 + 4 + 9)
    mag2 = numpy.sqrt(41.25)#(.25 + 16 + 25)
    ref_Dang = math.degrees(numpy.arccos(old_div(7.5, (mag1 * mag2))))

    ref_real_DANG = 2.08192544535
   
    def test_DANG(self):
        #print "STARTING TEST"
        result = lib_direct.get_DANG(self.v1, self.v2)
        self.assertAlmostEqual(result, self.ref_Dang)
    
    def test_DANG_real_values(self):
        # with SPD naming scheme:
        #PintPars_example.get_dec_and_inc()
        #PintPars_example.get_DANG()
        #self.assertAlmostEqual(PintPars_example.pars['DANG'], self.ref_real_DANG)
        # with Magic naming scheme:
        self.assertAlmostEqual(PintPars_example.pars['specimen_int_dang'], self.ref_real_DANG)


class CheckNRMdev(unittest.TestCase):
    dang = 114.59155902616465 # rad2deg(2)
#    X1_avg, X2_avg, X3_avg = 1.5, 5., 7
    X_avg = [1.5, 5., 7.]
    y_int = 7.
    ref_NRM_dev = 113.42997754204494

    def test_NRM_dev(self):
        result = lib_direct.get_NRM_dev(self.dang, self.X_avg, self.y_int)
        self.assertAlmostEqual(self.ref_NRM_dev, result)

    
class CheckTheta(unittest.TestCase):  # need to understand dir2cart, cart2dir better before can sign off on this one.  however, I THINK it is right as is
    ChRM = numpy.array([-0.00281947815208591791, -0.06360887927605490821,  0.99797092193119241177]) 
    # ChRM Dir = ([ 267.46201272,   86.34943176,    1.        ])
    B_lab_dir = [0.0, 90.0, 1.] # different from B_lab_vector... ignore last value

    def test_theta(self):  # FINISH ME!!!!!
        result = lib_direct.get_theta(self.B_lab_dir, self.ChRM)
        self.assertAlmostEqual(result, PintPars_example.pars['specimen_theta'])


    

class CheckGamma(unittest.TestCase):
    B_lab_dir = [0, 90, 1]
    B_lab_cart = lib_direct.dir2cart(B_lab_dir)  # [  6.12323400e-17,   0.00000000e+00,   1.00000000e+00]

    #[3,2,1] --> array([ 33.69006753,  15.50135957,   3.74165739])
    pTRM_dir = [3, 2, 1]
    pTRM_cart = lib_direct.dir2cart(pTRM_dir)

    ref_gamma = 88.

    def testGamma(self):
        result = lib_direct.get_gamma(self.B_lab_dir, self.pTRM_dir)
        self.assertAlmostEqual(87.999999999999986, 88.)
        self.assertAlmostEqual(self.ref_gamma, result)



# trm...
# x,y,z of B_lab ? 
#specimen_Data['Thellier_dc_field_theta'] = 90.0
#specimen_Data['Thellier_dc_field_phi'] = 0.0
#specimen_Data['Thellier_dc_field_uT'] = 4e-05

#datablock[1]['treatment_ac_field'] = 0
#datablock[1]['treatment_dc_field'] = '4e-05'

# what is x,y,z of TRM_i=end.  .

if __name__ == "__main__":
    unittest.main()
