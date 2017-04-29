#!/usr/bin/env python

from __future__ import print_function
from __future__ import absolute_import
import os
from . import spd
# K temps: [0.0, 100.0, 150.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0, 500.0, 525.0, 550.0]
# C temps: [273, 373.0, 423.0, 473.0, 498.0, 523.0, 548.0, 573.0, 598.0, 623.0, 648.0, 673.0, 698.0, 723.0, 748.0, 773.0, 798.0, 823.0]
from . import new_lj_thellier_gui_spd as tgs
cwd = os.getcwd()
main_dir = cwd + '/SPD'


calculate = ['int_n', 'frac', 'fvds', 'b_sigma', 'b_beta', 'scat', 'g', 'k', 'k_sse', 'z', 'int_mad_anc', 'int_dang', 'int_alpha', 'alpha_prime', 'theta', 'gamma', 'int_ptrm_n', 'ptrm', 'drat', 'mdrat', 'maxdev', 'dpal', 'md', 'tail_drat', 'dtr', 'dac', 'DANG']

#calculate = ['int_n', 'frac', 'f', 'fvds', 'b_sigma', 'b_beta', 'scat', 'g', 'k', 'k_sse', 'z', 'z_md', 'q', 'r_sq', 'coeff_det_sq', 'int_mad', 'int_mad_anc', 'int_dang', 'int_alpha', 'alpha_prime', 'theta', 'int_crm', 'gamma', 'int_ptrm_n', 'ptrm', 'drat', 'drats', 'cdrat', 'mdrat', 'dck', 'maxdev', 'mdev', 'dpal', 'int_ptrm_tail_n', 'md', 'tail_drat', 'dtr', 'dt', 'ac_n', 'dac', 'gmax']

#calculate = ['int_n', 'int_alpha', 'f', 'k', 'drats', 'int_ptrm_tail_n']
#calculate = ['drats']

gui = tgs.Arai_GUI('/magic_measurements.txt', main_dir)
specimens = list(gui.Data.keys())
example = spd.PintPars(gui.Data, '0238x6011044', 473., 623., 'magic', calculate)
example.calculate_all_statistics()
PintPars_example = example

def make_specimens(calculate=calculate):
    for stat in calculate:
        spec = spd.PintPars(gui.Data, '0238x6011044', 473., 623., 'magic', [stat])
        spec.reqd_stats()
        print('---------')
    print(calculate)


def many_specimens(calculate=calculate):
    from itertools import combinations
    c = combinations(calculate, 2)
    for combo in c:
        print('combo', combo)
        spec = spd.PintPars(gui.Data, '0238x6011044', 473., 623., 'magic', combo)
        spec.reqd_stats()
        print('XXXXXXXXXXXXXXX')




#spec.calculate_all_statistics()


SCAT_spec = spd.PintPars(gui.Data, '0238x6011044', 273., 673.) # 0, 400                
SCAT_spec2 = spd.PintPars(gui.Data, '0238x6011044', 273., 698.) # 0, 425 
SCAT_spec.York_Regression()
SCAT_spec2.York_Regression()


#new_spec = spd.PintPars(gui.Data, '0238x5721062', 100. + 273., 525. + 273.)
#new_spec.calculate_all_statistics()
#gui2 = tgs.Arai_GUI('/consistency_tests/Yamamoto_Hushi_2008_magic_measurements.txt', cwd)
#thing2 = spd.PintPars(gui2.Data, 'SW01-01A-2', 100. + 273., 480. + 273.)

#thing2 = PintPars(gui.Data, specimens[0], 473., 623.)
#thing2.calculate_all_statistics()
#thing3 = PintPars(gui.Data, specimens[1], 473., 623.)
#thing3.calculate_all_statistics()
#thing4 = PintPars(gui.Data, specimens[2], 473., 623.)
#thing4.calculate_all_statistics()
#thing5 = PintPars(gui.Data, specimens[3], 473., 623.)
#thing5.calculate_all_statistics()
#thing6 = PintPars(gui.Data, specimens[4], 473., 623.)
#thing6.calculate_all_statistics()


#gui2 = tgs.Arai_GUI('new_magic_measurements.txt')
#gui3 = tgs.Arai_GUI('consistency_tests/Bowles_etal_2006_magic_measurements.txt')
#gui4 = tgs.Arai_GUI('consistency_tests/Donadini_etal_2007_magic_measurements.txt')
#gui5 = tgs.Arai_GUI('consistency_tests/Krasa_2000_magic_measurements.txt')
#gui6 = tgs.Arai_GUI('consistency_tests/Muxworthy_etal_2011_magic_measurements.txt')
#gui7 = tgs.Arai_GUI('consistency_tests/Paterson_etal_2010_magic_measurements.txt')
#gui8 = tgs.Arai_GUI('consistency_tests/Selkin_etal_2000_magic_measurements.txt')
#gui10 = tgs.Arai_GUI('consistency_tests/Yamamoto_etal_2003_magic_measurements.txt')



