#!/usr/bin/env python

import unittest
#import sys
#sys.path.append('/Users/nebula/Python')
#from SPD_project.lib import lib_additivity_check_statistics as lib_add
import SPD.lib.lib_additivity_check_statistics as lib_add


#class CheckTailSelection(unittest.TestCase):

class CheckAdditivity(unittest.TestCase):

    temps =          [1,  2,  3,  4,  5]
    starting_temps = [2,  3,  4,  5,  6]
    x_add_check =    [0, .2, .4, .5, .7]
    tmax = 4

    ref_incl_temps = [1, 2, 3]
    ref_n_add = 3

#    x_arai at starting temp minus AC check and lower temp
#    .1 - 0, .5 - .2, .8 - .4
#    .1, .2, .4

    x_Arai =      [0, .1, .35, .5, .6,  .8,  1., 1.1]
    t_Arai =      [1,  2, 2.5,  3., 3.5, 4., 5., 6.]

    ptrm_star = { (2, 1): .1, (3, 2): .4,  (4, 3): .3 } # where key[0] is the higher temp and key[1] the lower , value is the expected ptrm acquired between those temperatures 

    ptrm_actual = { (2, 1):  .1, (3,2): .3, (4, 3): .4 }

    additivity_checks = { (2,1): 0, (3,2): .2, (4, 3): .1 }

    add_checks = [0, .2, .1, .6]
    x_int = 2.
    ref_delta_AC = (.2 / 2) * 100.

    # think I additionally need the check diffs.  what I have is just x check values.
    # I believe it will be: pTRM of start temperature - pTRM of additivity check step.  then I can compare those values.  
    # so we are comparing: ptrm(t=2) - ptrm(t=1) (second is heated from room temp), with ptrm(t=2) - ptrm(t=1) (second is demagnetized from first)



#    T_i < T_j
#    pTRM*(T_j, T_i) = pTRM(T_j, T_0) - pTRM(T_i, T_0)
    # means expected value of pTRM gained between i and j should be the same as the pTRM gained between 0 and j minus the pTRM gained between 0 and i
#hello

#   ptrm(T_j, T_i) = pTRM(T_j, T_0) - ptrm(T_j, T_i) # last value is the additivity check taken at temperature i, that was cooled from temperature j
#hello


    def test_data_selection(self):
        incl_temps, n_add = lib_add.get_n_add(self.temps, self.starting_temps, self.tmax)
        for num, temp in enumerate(incl_temps):
            #print temp, self.ref_incl_temps[num]
            self.assertEqual(temp, self.ref_incl_temps[num])
        self.assertEqual(n_add, self.ref_n_add)

    def test_delta_AC(self):
        delta_AC, included_add_checks = lib_add.get_delta_AC(self.ref_n_add, self.add_checks, self.x_int)
        self.assertAlmostEqual(self.ref_delta_AC, delta_AC)


# ignore below
if False:
    def test_pTRM_star(self):
#        def get_ptrm_star(incl_temps, starting_temps, x_Arai, t_Arai):
        ptrm_star = lib_add.get_ptrm_star(self.ref_incl_temps, self.starting_temps, self.x_Arai, self.t_Arai)
        for k, v in ptrm_star.items():
            self.assertAlmostEqual(self.ptrm_star[k], v)


    def test_pTRM_actual(self):
        ptrm_actual = lib_add.get_ptrm_actual(self.ref_incl_temps, self.starting_temps, self.x_Arai, self.t_Arai, self.x_add_check)
        for k, v in ptrm_actual.items():
            self.assertAlmostEqual(self.ptrm_actual[k], v)
        
    def test_ACs(self):
        additivity_checks = lib_add.get_add_checks(self.ptrm_star, self.ptrm_actual)
        for key, check in additivity_checks.items():
            self.assertAlmostEqual(self.additivity_checks[key], check)

# get AC check diffs
# think will be comparing x_Arai at that temp with x_Arai_add at that point

        
        

    def test_delta_AC(self):
        pass
