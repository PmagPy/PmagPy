#!/usr/bin/env python

from __future__ import division
from __future__ import absolute_import
from past.utils import old_div
import unittest
import numpy
import copy
import sys
#if '/Users/nebula/Python' not in sys.path:
#    sys.path.append('/Users/nebula/Python')
#print sys.path
#from SPD_project.lib import lib_arai_plot_statistics as lib_arai
#from SPD_project import spd
import SPD.lib.lib_arai_plot_statistics as lib_arai
import SPD.spd as spd
from SPD.test_instance import example, SCAT_spec, SCAT_spec2 # pre-made, ready to go PintPars object

from SPD.tests import known_values



# could use this directly in here:
#import new_lj_thellier_gui_spd as tgs
#gui = tgs.Arai_GUI()
#thing = PintPars(gui.Data, '0238x6011044', 473., 623.)
#    specimens = spd.gui.Data.keys()
#    thing1 = spd.PintPars(spd.gui.Data, specimens[3], 523., 773.)
#    thing1.calculate_all_statistics()
#    thing2 = spd.PintPars(spd.gui.Data, specimens[4], 273., 798.)
#    thing2.calculate_all_statistics()
#    thing3 = spd.PintPars(spd.gui.Data, specimens[5], 598, 698)
#    thing3.calculate_all_statistics()



#class CheckParams(unittest.TestCase):

#    # no init
#    ref = "reference"
#    obj = copy.deepcopy(spec)
#    obj_pars = obj.pars.copy()
#    #obj.arai_plot_statistics()
#    obj.calculate_all_statistics()
#    obj_new_pars = obj.pars
#    pre_calculation_pars = ['specimen_int_n', 'specimen_lab_dc_field']
#    post_calculation_pars = ['tmin', 'tmax', 'B_lab', 'R_corr2', 'vector_diffs_segment', 'delta_x_prime', 'partial_vds', 'V_Free', 'zdata_mass_center', 'B_anc', 'count_IZ', 'NRM_dev', 'SCAT', 'count_ZI', 'specimen_int', 'x_err', 'Z', 'specimen_b_sigma', 'vector_diffs', 'specimen_YT', 'specimen_vds', 'Inc_Anc', 'Inc_Free', 'specimen_n', 'Zstar', 'max_diff', 'tau_Anc', 'MAD_Free', 'R_det2', 'Dec_Anc', 'FRAC', 'GAP-MAX', 'y_prime', 'best_fit_vector_Free', 'delta_y_prime', 'Dec_Free', 'tau_Free', 'x_tag', 'B_anc_sigma', 'alpha', 'best_fit_vector_Anc', 'specimen_fvds', 'specimen_b_beta', 'MAD_Anc', 'V_Anc', 'specimen_b', 'specimen_g', 'specimen_XT', 'specimen_f', 'y_tag', 'specimen_k', 'specimen_q', 'DANG', 'lab_dc_field', 'specimen_w', 'x_prime', 'SSE', 'specimen_g_lim', 'y_err', 'max_ptrm_check_percent', 'max_ptrm_check', 'sum_ptrm_checks', 'sum_abs_ptrm_checks', 'delta_CK', 'DRAT', 'length_best_fit_line', 'max_DEV', 'CDRAT', 'CDRAT_prime', 'DRATS', 'DRATS_prime', 'mean_DRAT', 'mean_DRAT_prime', 'mean_DEV', 'mean_DEV_prime', 'delta_pal', 'n_tail', 'tail_check_max', 'tail_check_diffs', 'delta_TR', 'DRAT_tail', 'MD_VDS', 'theta', 'gamma', 'n_ptrm', 'IZZI_MD', 'ptrm_checks_included_temps', 'n_add', 'delta_AC', 'AC_Checks_segment', 'ptrm_checks', 'fail_arai_beta_box_scatter', "fail_ptrm_beta_box_scatter", "fail_tail_beta_box_scatter", 'scat_bounding_line_high', 'scat_bounding_line_low', 'y_Arai_mean', 'x_Arai_mean', 'ptrms_tau_Free', 'pTRM_MAD_Free', 'ptrms_angle_Free', 'specimen_PCA_sigma_min_Free', 'specimen_PCA_sigma_int_Free', 'specimen_PCA_sigma_max_Free', 'ptrms_inc_Free', 'ptrms_dec_Free', 'ptrm_dir', 'ptrm_cart']

#
#    def test_for_params_before(self):
#        for par in self.pre_calculation_pars:
#            self.assertIn(par, self.obj_pars.keys())
#
#    def test_for_params_after(self):
#        """
#        check that calculate_all_statistics() generates all expected pars
#        """
#        for par in self.post_calculation_pars:
#            self.assertIn(par, self.obj_new_pars.keys())

#    def test_for_extra_params(self):
#        """
#        check that calculate_all_statistics doesn't generate any unexpected pars
#        """
#        for par in self.obj_new_pars.keys():
#            self.assertIn(par, self.post_calculation_pars)
#
#    def test_params_are_not_empty(self):
#        for par in self.obj_pars.keys():
#            value = self.obj_pars[par]
#           # print value
#            self.assertIsNotNone(value)

class CheckInitialAttributeValues(unittest.TestCase):
    obj = copy.deepcopy(example)
    obj_attributes = {'s':obj.s, 'datablock': obj.datablock, 'x_Arai': obj.x_Arai, 'y_Arai': obj.y_Arai, 't_Arai': obj.t_Arai, 'x_Arai_segment': obj.x_Arai_segment, 'y_Arai_segment': obj.y_Arai_segment, "x_Arai_mean": obj.x_Arai_mean, "y_Arai_mean": obj.y_Arai_mean, "x_tail_check": obj.x_tail_check, 'y_tail_check': obj.y_tail_check, 'tail_checks_temperatures': obj.tail_checks_temperatures, 'tail_checks_starting_temperatures': obj.tail_checks_starting_temperatures, 'x_ptrm_check': obj.x_ptrm_check, 'y_ptrm_check': obj.y_ptrm_check, 'ptrm_checks_temperatures': obj.ptrm_checks_temperatures, 'ptrm_checks_starting_temperatures': obj.ptrm_checks_starting_temperatures, 'zijdblock': obj.zijdblock, 'z_temperatures': obj.z_temperatures, 'start': obj.start, 'end': obj.end, 'pars': obj.pars, 'specimen_Data': obj.specimen_Data, 'tmin': obj.tmin, 'tmax': obj.tmax, 'tmin_K': obj.tmin_K, 'tmax_K': obj.tmax_K}
    known_values = known_values.initial_values

    # test a bunch of the initial values against known expected values.  this indirectly tests get_data and such.  I don't know, maybe that will be enough.  Then I can do more thorough tests for the other stuff.
    def test_name(self):
        self.assertEqual(self.obj.s, '0238x6011044')

    def test_known_values(self):
        for key, value in self.known_values.items():  # goes through all values
            if type(value) == int or type(value) == float: # can't iterate over int type or float
               # print type(value)
                self.assertEqual(value, self.obj_attributes[key])
            elif type(value) != type(None) and type(value) != dict:
               # print type(value)
                for num, item in enumerate(value):
                    message = "%s: known value = %s; obj_attribute = %s" %(key, value[:150], self.obj_attributes[key][:150])
                    if type(item) == float or type(item) == numpy.float64:
                        self.assertEqual(round(self.obj_attributes[key][num], 8), round(item, 8), message)
                    else:
                        self.assertEqual(self.obj_attributes[key][num], item, message)


class CheckYorkRegression(unittest.TestCase):

    obj = copy.deepcopy(example)
    obj.York_Regression()
    known_values = known_values.York_Regression_values
    obj_pars = obj.pars

    def test_York_Regression(self):
        for key, value in self.known_values.items():  # goes through all values
            if type(value) == int or type(value) == float: # can't iterate over int type or float
               # print type(value)
                self.assertAlmostEqual(value, self.obj_pars[key])

            elif value.any() and type(value) != dict:
               # print type(value)
                for num, item in enumerate(value):
                    message = "%s: known value = %s; obj_attribute = %s" %(key, value[:150], self.obj_pars[key][:150])
                    if type(item) == float or type(item) == numpy.float64:
                        self.assertAlmostEqual(round(self.obj_pars[key][num], 8), round(item, 8), message)
                    else:
                        self.assertAlmostEqual(self.obj_pars[key][num], item, message)




class CheckVDSsequence(unittest.TestCase): # adequate

    obj = copy.deepcopy(example)
    obj.York_Regression()
    result = obj.get_vds()
#    stuff['vds'] = -.1
# should be 0238x6011044, 473., 623
    ref_fvds = 0.1360813531595344
    ref_vds = 1.2591254846197817
    ref_GAP_MAX = 0.32852441013324574
    ref_vector_diffs_segment = [0.031295984827684566, 0.024151118628312387, 0.036482667142194579, 0.059128016249387697, 0.034082675643388412, 0.090581343759213978]
    ref_partial_vds = 0.27572180625018161

    def test_against_known_values(self): # just testing with values verified in thellier_gui.  not a brilliant test, but fine
        #print self.result.keys()
        self.assertAlmostEqual(self.result['specimen_fvds'], self.ref_fvds)
        self.assertAlmostEqual(self.result['specimen_vds'], self.ref_vds)
        self.assertAlmostEqual(self.result['GAP-MAX'], self.ref_GAP_MAX)
        self.assertAlmostEqual(self.result['vector_diffs_segment'], self.ref_vector_diffs_segment)
        self.assertAlmostEqual(self.result['partial_vds'], self.ref_partial_vds)


#zdata = [[1, 2, 3], [3, 4, 5], [4, 5.5, 6]]
#2, 2, 2.  1, 1.5, 1.  4, 5.5, 6.


    def test_for_negative_values(self):
        for k, v in list(self.result.items()):
            if isinstance(v,int):
                self.assertGreaterEqual(v, 0) # none of these stats can possibly be negative numbers


class CheckSCAT(unittest.TestCase): # NOT DONE
    obj = copy.deepcopy(example)
    b = -1.
    slope_err_threshold = .25
    x_mean, y_mean = 3, 2
    beta_threshold = .25

    def test_SCAT_box(self):
#        def get_SCAT_box(slope, slope_err, x_mean, y_mean, beta_threshold = .1):
        ref_y_max = 6.5
        ref_x_max = 7.
        ref_low_bound_result = 1.8846153846153846
        ref_high_bound_result = 4.642857142857142
        result = lib_arai.get_SCAT_box(self.b, self.x_mean, self.y_mean, self.beta_threshold)
        self.assertAlmostEqual(ref_low_bound_result, result[0](2.))
        self.assertAlmostEqual(ref_high_bound_result, result[1](2.))
        self.assertAlmostEqual(ref_x_max, result[2])
        self.assertAlmostEqual(ref_y_max, result[3])
        #print result
        #print result[0](2) # low_bound
        #print result[1](2) # high bound

    def test_in_SCAT_box(self):
        low_bound, high_bound, x_max, y_max, low_line, high_line = lib_arai.get_SCAT_box(self.b,
                self.x_mean, self.y_mean, self.beta_threshold)
        good = [(2., 1.9), (1., 5.), (5., 1.8)]
        bad = [(1., 2.), (3., 4), (7.1, .2)]
#        def in_SCAT_box(x, y, low_bound, high_bound, x_max, y_max):
        for xy in good:
            result = lib_arai.in_SCAT_box(xy[0], xy[1], low_bound, high_bound, x_max, y_max)
            self.assertTrue(result)
        for xy in bad:
            result = lib_arai.in_SCAT_box(xy[0], xy[1], low_bound, high_bound, x_max, y_max)
            self.assertFalse(result)

    def test_SCAT_points(self):
        x_Arai_segment = [1., 2.]
        y_Arai_segment = [4.5, 1.]
        tmin = 20.
        tmax = 40.
        ptrm_checks_temperatures = [10, 20, 30, 40]
        ptrm_checks_starting_temperatures = [20, 30, 40, 50]
        x_ptrm_check = [1, 2, 3, 4]
        y_ptrm_check = [4., 3., 2., 0.]
        tail_checks_temperatures = [15., 25., 35., 45.]
        tail_checks_starting_temperatures = [25., 35., 45., 55.]
        x_tail_check = [1.5, 2.5, 3.5, 4.5]
        y_tail_check = [4.5, 3.5, 2.5, 1.5]
        ref_points = [(1., 4.5), (2., 1.), (2., 3.), (3., 2.), (2.5, 3.5)]
        result = lib_arai.get_SCAT_points(x_Arai_segment, y_Arai_segment, tmin, tmax, ptrm_checks_temperatures, ptrm_checks_starting_temperatures, x_ptrm_check, y_ptrm_check, tail_checks_temperatures, tail_checks_starting_temperatures, x_tail_check, y_tail_check)
        #print "result (in test_SCAT_points)", result
        for xy in result[0]:
            self.assertIn(xy, ref_points)
        #print result, ref_points

    def test_SCAT(self):
#def get_SCAT(points, low_bound, high_bound, x_max, y_max):
        points = [(2., 1.9), (1., 4.5), (5., .2)]
        points1 = [(2., 1.9), (1., 4.5), (3.5, .1)]
        points2 =  [(2., 1.9), (1., 4.5), (3.5, -.1)]
        points3 = [(2., 1.9), (1., 4.5), (4., 4.)]
        def low_bound(x):
            y = 3.5/-4.3333335 * x + 3.5
            return y
        def high_bound(x):
            y = 6.5/-7. * x + 6.5
            return y
        x_max = 7
        y_max = 6.5
        result = lib_arai.get_SCAT(points, low_bound, high_bound, x_max, y_max)
        result1 = lib_arai.get_SCAT(points1, low_bound, high_bound, x_max, y_max)
        result2 = lib_arai.get_SCAT(points2, low_bound, high_bound, x_max, y_max)
        result3 = lib_arai.get_SCAT(points3, low_bound, high_bound, x_max, y_max)
        self.assertTrue(result)
        self.assertFalse(result1)
        self.assertFalse(result2)
        self.assertFalse(result3)

    def test_SCAT_real_data(self):
        thing = SCAT_spec #spd.PintPars(spd.gui.Data, '0238x6011044', 273., 673.) # 0, 400
        #thing.York_Regression()
        #print thing.tmin_K, thing.tmax_K
        thing1 = SCAT_spec2 #spd.PintPars(spd.gui.Data, '0238x6011044', 273., 698.) # 0, 425
        #thing1.York_Regression()
        #print thing1.tmin_K, thing1.tmax_K
        self.assertEqual('Fail', thing.get_SCAT())
        self.assertEqual('Pass', thing1.get_SCAT())





class CheckFrac(unittest.TestCase): # basically good to go

    #print example.pars
    obj = copy.deepcopy(example)
    obj.pars['specimen_vds'] = 2
    obj.pars['vector_diffs_segment'] = [1., 1.5, 3.]
    # trying it a little differently:
    vds = 2
    vector_diffs_segment = [1., 1.5, 3.]

    def test_FRAC(self):
        frac = lib_arai.get_FRAC(self.vds, self.vector_diffs_segment)
        self.assertEqual(frac, 2.75)

    def test_FRAC_with_zero_vds(self):
        self.assertRaises(ValueError, lib_arai.get_FRAC, 0, self.vector_diffs_segment)

    def test_FRAC_with_negative_input(self):
        self.assertRaises(ValueError, lib_arai.get_FRAC, 1, [1., -.1, 2.])

    def test_lib_vs_actual(self): # checks that it is calculated the same in lib and in practice
        self.obj.pars['vds'] = 2
        self.obj.pars['vector_diffs_segment'] = [1., 1.5, 3.]
        frac = lib_arai.get_FRAC(self.vds, self.vector_diffs_segment)
        obj_frac = self.obj.get_FRAC()
        self.assertEqual(frac, obj_frac)



class CheckR_corr2(unittest.TestCase):
    obj = copy.deepcopy(example)
    R_corr2 = obj.get_R_corr2()
    x_segment, y_segment = numpy.array([1., 5., 9.]), numpy.array([0., 2., 7.])
    x_avg = old_div(sum(x_segment), len(x_segment))
    y_avg = old_div(sum(y_segment), len(y_segment))
    ref_numerator = 28.**2
    ref_denominator = 32. * 26.

    def testPositiveOutput(self):
        """should produce positive output"""
        self.assertGreater(self.R_corr2, 0)

    def testSimpleInput(self):
        """should produce expected output with simple input"""
        r = lib_arai.get_R_corr2(self.x_avg, self.y_avg, self.x_segment, self.y_segment)
        self.assertEqual((old_div(self.ref_numerator,self.ref_denominator)), r)

#    def testDivideByZero(self):
#        """should raise ValueError when attempting to divide by zero"""
#        #print 'testing divide by zero'
#        self.assertRaises(ValueError, lib_arai.get_R_corr2, 1., 1., numpy.array([1.]), numpy.array([1.]))

class CheckR_det2(unittest.TestCase): # acceptable working test
    y_segment = [1., 2.5, 3]
    y_avg = 2.
    y_prime = [1., 2., 3.]

    def test_simple_input(self):
        result = lib_arai.get_R_det2(self.y_segment, self.y_avg, self.y_prime)
        self.assertEqual((1 - old_div(.25,2.25)), result)


class CheckZigzag(unittest.TestCase):
    x = [0., 4., 5.]
    y = [3., 2., 0.]
    y_int = 3.
    x_int = 5.
    n = len(x)
    reference_b_wiggle = [0, .25, old_div(3.,5.)]

    slope = 1.2
    Z = 1.3599999999999999

# above is correct

    Z_star = 113.33333333333333
#    Z_star = 88.
    obj = copy.deepcopy(example)
    obj.x_Arai, obj.y_Arai = x, y
    obj.pars['specimen_YT'], obj.pars['specimen_XT'] = y_int, x_int
    obj.pars['specimen_b'], obj.n = slope, n

    def testWiggleB(self):
        for num, b in enumerate(self.reference_b_wiggle):
            result = lib_arai.get_b_wiggle(self.x[num], self.y[num], self.y_int)
            self.assertAlmostEqual(result, b)

    def testZ(self):
        # x_segment, y_segment, x_int, y_int, slope
        result = lib_arai.get_Z(self.x, self.y, self.x_int, self.y_int, self.slope)
        self.assertAlmostEqual(self.Z, result)

    def testZStar(self):
        result = lib_arai.get_Zstar(self.x, self.y, self.x_int, self.y_int, self.slope, self.n)
        self.assertAlmostEqual(self.Z_star, result)


class CheckIZZI_MD(unittest.TestCase):
    points = numpy.array([1., 2., 3.])
    norm = 4.
    ref_normed_points = numpy.array([.25, .5, .75])

    x = numpy.array([4, 6, 12])
    y = numpy.array([8, 4, 2])
    norm_x = lib_arai.get_normed_points(x, norm)
    #print "x", x
    #print "norm", norm
    #print "norm_x", norm_x
    norm_y = lib_arai.get_normed_points(y, norm)
    #print "norm_y", norm_y
    ref_xy = [(4, 8), (6, 4), (12, 2)] # not normed

    L1 = numpy.sqrt(1.25)
    L2 = numpy.sqrt(2.5)
    L3 = numpy.sqrt(6.25)

    phi = 0.321750554
    H = 0.790569415
    A = .625
    triangle = {'triangle_phi': phi, 'triangle_H': H, 'triangle_A': A}

    first_line = [(norm_x[0], norm_y[0]), (norm_x[2], norm_y[2])]
    first_line_slope = -.75 # correct
    # b = y - mx
    first_y_int = 2.75
    second_line = [(norm_x[1], norm_y[1])]
    second_y_int = 2.125
    sign = 1.

    def testPointNorming(self): # satisfactory
        result = lib_arai.get_normed_points(self.points, self.norm)
        for num, point in enumerate(result):
            self.assertAlmostEqual(self.ref_normed_points[num], point)

    def testXyArray(self):  # satisfactory
        xy_array = lib_arai.get_xy_array(self.x, self.y)
        for num, i in enumerate(xy_array):
            self.assertAlmostEqual(i, self.ref_xy[num])


suite = []
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckInitialAttributeValues))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckR_corr2))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckR_det2))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckSCAT))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckVDSsequence))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckYorkRegression))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckZigzag))
suite.append(unittest.TestLoader().loadTestsFromTestCase(CheckIZZI_MD))

full_suite = unittest.TestLoader().loadTestsFromTestCase(CheckFrac)

for s in suite[1:]:
    full_suite.addTests(s)

def run_all_tests():
    unittest.TextTestRunner(verbosity=2).run(full_suite)

if __name__ == "__main__":
    #unittest.TextTestRunner(verbosity=2).run(full_suite)
    unittest.main()
