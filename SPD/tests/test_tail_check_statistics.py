#!/usr/bin/env python                                                                                            

import numpy
import unittest
import copy
import sys
#sys.path.append('/Users/nebula/Python')
#from SPD_project import spd
#from SPD_project.lib import lib_tail_check_statistics as lib_tail
import SPD.lib.lib_tail_check_statistics as lib_tail


#class CheckpTRMparams(unittest.TestCase): 

class CheckTailSelection(unittest.TestCase):

    tmax = 50
    y_Arai = [4, 3.9, 3.5, 3, 2., 1.]
    t_Arai = [10, 20, 30, 40, 50, 60]
    y_tail = [3.5, 4.2, 3., 1.4, .6 ]
    tail_temps = [10, 30, 40, 50, 60]
    #obj = copy.deepcopy(spd.thing)
    ref_n_tail = 4

#                [4,    3.5, 3,  2.,   1., .5]
#-               [3.5,  4.2, 3., 1., .6 ]
    ref_tail_check_max = .7
    ref_diffs = [ .5, -.7,  0,  .6]

    ref_L = 3.

    y_int = 4.5
    vds = 1.25

    def test_n_tail(self):
        ref_n_tail = 4
#        ref_tail_section.  specifying this is not neacessary if we always start at the first tail check.  need to check that this is so
        n_tail = lib_tail.get_n_tail(self.tmax, self.tail_temps)
        self.assertEqual(ref_n_tail, n_tail)

    #def test_n_tail_real_data(self):
    #    n_tail = self.obj.get_n_tail()
    #    self.assertEqual(self.ref_n_tail, n_tail)
              
    def test_max_tail_check(self):
        tail_check_max, tail_check_diffs = lib_tail.get_max_tail_check(self.y_Arai, self.y_tail, self.t_Arai, self.tail_temps, self.ref_n_tail)
        for num, diff in enumerate(tail_check_diffs):
            self.assertAlmostEqual(self.ref_diffs[num], diff)
        self.assertAlmostEqual(self.ref_tail_check_max, tail_check_max)

    def test_DRAT_tail(self):
        ref_DRAT_tail = (.7 / 3.) * 100
        DRAT_tail = lib_tail.get_DRAT_tail(self.ref_tail_check_max, self.ref_L)
        self.assertAlmostEqual(ref_DRAT_tail, DRAT_tail)
        # max_tail_check / best_fit line  * 100
        
    def test_delta_TR(self):
        ref_delta_TR = (.7 / 4.5) * 100.
        delta_TR = lib_tail.get_delta_TR(self.ref_tail_check_max, self.y_int)
        self.assertAlmostEqual(ref_delta_TR, delta_TR)
        

    def test_MD_VDS(self):
        ref_MD_VDS = (self.ref_tail_check_max / self.vds) * 100.
        MD_VDS = lib_tail.get_MD_VDS(self.ref_tail_check_max, self.vds)
        self.assertAlmostEqual(ref_MD_VDS, MD_VDS)
        

if __name__ == '__main__':
    unittest.main()
