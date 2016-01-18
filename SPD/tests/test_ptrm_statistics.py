#!/usr/bin/env python



import numpy
import unittest
#import sys
#sys.path.append('/Users/nebula/Python')
#from SPD_project.lib import lib_ptrm_statistics as lib_ptrm
#from SPD_project import spd
#import SPD.spd as spd
from SPD.test_instance import example
import SPD.lib.lib_ptrm_statistics as lib_ptrm
import SPD.lib.lib_directional_statistics as lib_direct



class CheckpTRMparams(unittest.TestCase):

    tmin = 20.
    tmax = 50.
    x_ptrm = [1., 2., 3., 9., 6.]
    y_ptrm = [7., 6., 4., 2.4, 0.]
    ptrm_temps = [10, 20, 30, 40, 50]
    ptrm_starting_temps = [20, 30, 40, 50, 60]
    ref_n = 4.
    ref_steps = [10, 20, 30, 40]

    x_Arai = [1., 1., 2.5, 5.5, 7., 5., 6., 8.] # ptrm initially acquired at a temp
    t_Arai = [0,  10, 20,  30, 40, 50, 60, 70]
    #    1,   2,   3,  9.
    #  - 1,   2.5, 5.5, 7.
    #    0., -.5,  -2.5, 2.
    ref_max_ptrm_check = 2.5
    ref_sum_ptrm_check = abs(-1.)
    ref_check_percent = (2.5/ 5.5) * 100.
    ref_sum_abs_ptrm_check = 5.

    x_int = 8.5
    ref_delta_CK = 2.5 / 8.5 * 100

    delta_y_prime = 5.
    delta_x_prime = 8.

    ref_L = numpy.sqrt(25 + 64)


    
    def test_n_ptrm(self):
        result = lib_ptrm.get_n_ptrm(self.tmin, self.tmax, self.ptrm_temps, self.ptrm_starting_temps)
        self.assertEqual(self.ref_n, result[0])
        self.assertEqual(self.ref_steps, result[1])

    def test_max_ptrm_check(self):
#def get_max_ptrm_check(ptrm_checks_segment, ptrm_checks, ptrm_x, t_Arai, x_Arai):
        result = lib_ptrm.get_max_ptrm_check(self.ref_steps, self.ptrm_temps, self.x_ptrm, self.t_Arai, self.x_Arai)
        diffs, max_ptrm_diff, sum_ptrm_diffs, check_percent, sum_abs_ptrm_diffs = result[0], result[1], result[2], result[3], result[4]
        print self.ref_max_ptrm_check, max_ptrm_diff
        self.assertAlmostEqual(self.ref_max_ptrm_check, max_ptrm_diff)
        self.assertAlmostEqual(self.ref_sum_ptrm_check, sum_ptrm_diffs)
        self.assertAlmostEqual(self.ref_check_percent, check_percent)
        self.assertAlmostEqual(self.ref_sum_abs_ptrm_check, sum_abs_ptrm_diffs)


    def test_delta_CK(self):
        result = lib_ptrm.get_delta_CK(self.ref_max_ptrm_check, self.x_int)
        self.assertAlmostEqual(self.ref_delta_CK, result)

        
    def test_DRAT(self):
        ref_DRAT = (self.ref_max_ptrm_check / self.ref_L) * 100.
        DRAT, L = lib_ptrm.get_DRAT(self.delta_y_prime, self.delta_x_prime, self.ref_max_ptrm_check)
        self.assertAlmostEqual(ref_DRAT, DRAT)
        self.assertAlmostEqual(self.ref_L, L)

    def test_max_DEV(self):
        result = lib_ptrm.get_max_DEV(self.delta_x_prime, self.ref_max_ptrm_check)
        ref_max_DEV = (2.5 / 8.) * 100
        self.assertAlmostEqual(ref_max_DEV, result)
        
    def test_CDRAT(self):
        CDRAT, CDRAT_prime = lib_ptrm.get_CDRAT(self.ref_L, self.ref_sum_ptrm_check, self.ref_sum_abs_ptrm_check)
        ref_CDRAT, ref_CDRAT_prime = (1. / self.ref_L) * 100., (5. / self.ref_L) * 100
        self.assertAlmostEqual(ref_CDRAT, CDRAT)
        self.assertAlmostEqual(ref_CDRAT_prime, CDRAT_prime)
        
    def test_DRATS(self):
        #ref_DRATS = .9
        ref_DRATS = (1. / 7.) * 100.
        ref_DRATS_prime = (5. / 7.) * 100.
        end = 4
        DRATS, DRATS_prime = lib_ptrm.get_DRATS(self.ref_sum_ptrm_check, self.ref_sum_abs_ptrm_check, self.x_Arai, end)
        self.assertAlmostEqual(ref_DRATS, DRATS)
        self.assertAlmostEqual(ref_DRATS_prime, DRATS_prime)
        
    def test_DRATS_real_data(self):
        ref_drats = 0.928840447566
        DRATS = example.get_DRATS()
        self.assertAlmostEqual(ref_drats, DRATS)

    def test_mean_DRAT(self):
#        (1 / nPTRM) * (ref_sum_ptrm_check / L) = 1/4 * 1/ numpy.sqrt(25 + 64)
#        (1 / nPTRM) * (ref_abs_sum_ptrm_check / L)
#ref_L = numpy.sqrt(25 + 64)        
#    ref_sum_ptrm_check = abs(-1.)
#    ref_sum_abs_ptrm_check = 5.
#  ref_n = 4
        ref_mean_DRAT = 0.026499947000159001 * 100.
        ref_mean_DRAT_prime = 0.13249973500079501 * 100.
        mean_DRAT, mean_DRAT_prime = lib_ptrm.get_mean_DRAT(self.ref_sum_ptrm_check, self.ref_sum_abs_ptrm_check, self.ref_n, self.ref_L)
        self.assertAlmostEqual(ref_mean_DRAT, mean_DRAT)
        self.assertAlmostEqual(ref_mean_DRAT_prime, mean_DRAT_prime)

    def test_mean_DEV(self):
        ref_mean_DEV = (1. / 4.) * ( 1.  / 8.)  * 100
        ref_mean_DEV_prime = (1./ 4.) * (5. / 8.)  * 100
        mean_DEV, mean_DEV_prime = lib_ptrm.get_mean_DEV(self.ref_sum_ptrm_check, self.ref_sum_abs_ptrm_check, self.ref_n, self.delta_x_prime)
        self.assertAlmostEqual(ref_mean_DEV, mean_DEV)
        self.assertAlmostEqual(ref_mean_DEV_prime, mean_DEV_prime)

class CheckDeltaPal(unittest.TestCase):




    PTRMS = [[273, 0.0, 0.0, 0.0, 1], [523.0, 69.195984547975797, -85.42199731414884, 6.2264078715813993e-11, 1], [603.0, 138.12132132012039, -79.813283152904091, 7.7810407785190168e-11, 1], [673.0, 296.70436391944997, -86.096414415937858, 1.6138606721121362e-10, 1], [698.0, 350.77471999577131, -89.449608970360956, 1.7274047823306281e-10, 1], [723.0, 226.10272697074538, -88.137193454724965, 1.8323291051103103e-10, 1], [748.0, 150.62491961707215, -88.889492534540182, 2.3909881832110046e-10, 1], [773.0, 203.96570274646598, -87.738058668399745, 3.536498074608641e-10, 1], [793.0, 166.87540387011842, -87.919831575134225, 4.9746059783505941e-10, 1], [813.0, 73.602827630454939, -87.335958961493617, 6.9425156040192952e-10, 1], [833.0, 82.458063642411261, -87.950064486382914, 8.1559579781133579e-10, 1], [853.0, 73.598960313658907, -87.69967527829273, 8.6723568211981026e-10, 1], [873.0, 78.772421127061136, -87.762195431916041, 8.7680033088499116e-10, 1]]
    PTRM_Checks = [[523.0, 293.66503203853995, -75.775815956214288, 5.5168393286623806e-11], [673.0, 308.40407158865753, -85.909619052774985, 1.5688235416856313e-10], [723.0, 34.699999999999456, -89.265521037368686, 2.0055535218825225e-10], [773.0, 76.688486206439009, -87.336635350080513, 3.2518415837753303e-10], [813.0, 77.10710309043634, -87.213798722007027, 6.8061169115509297e-10], [853.0, 72.744776208874228, -87.817926152279625, 8.6645883210019646e-10]]
    NRM = 1.181323e-09
    y_err = [ 0.416634950813622,  0.393602300132986,  0.29514616239589,   0.258831962130594,  0.231017046142334,  0.187584640271966,  0.077426876476628, -0.08137321460769, -0.313889385036946, -0.450679390818599, -0.501770117063665, -0.512531830837121]
    y_mean = 0.528117669765
    b = -1.32512249833
    start = 1
    end = 12
    y_segment = [ 0.944752620578792,  0.921719969898157,  0.82326383216106,   0.786949631895764, 0.759134715907504,  0.715702310037136,  0.605544546241798,  0.44674445515748, 0.214228284728224, 0.077438278946571, 0.026347552701505, 0.015585838928049]
        
    def test_delta_pal(self):
        delta_pal = lib_ptrm.get_full_delta_pal(self.PTRMS, self.PTRM_Checks, self.NRM, self.y_err, self.y_mean, self.b, self.start, self.end, self.y_segment)

if __name__ == "__main__":
    unittest.main()
