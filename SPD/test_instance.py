#!/usr/bin/env python

import os
import spd
# K temps: [0.0, 100.0, 150.0, 200.0, 225.0, 250.0, 275.0, 300.0, 325.0, 350.0, 375.0, 400.0, 425.0, 450.0, 475.0, 500.0, 525.0, 550.0]
# C temps: [273, 373.0, 423.0, 473.0, 498.0, 523.0, 548.0, 573.0, 598.0, 623.0, 648.0, 673.0, 698.0, 723.0, 748.0, 773.0, 798.0, 823.0]
import new_lj_thellier_gui_spd as tgs
cwd = os.getcwd()
main_dir = cwd + '/SPD'

gui = tgs.Arai_GUI('/magic_measurements.txt', main_dir)
specimens = gui.Data.keys()
spec = spd.PintPars(gui.Data, '0238x6011044', 473., 623.)
spec.calculate_all_statistics()


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



