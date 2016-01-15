#!/usr/bin/env python


import numpy
import sys
import os
from itertools import combinations
import SPD.spd as spd



# maybe automate a way to go through multiple magic_measurements.txt files in a directory
# or just have as input all the files and make a "gui" object with each
#  get list of specimens.  go through them with tmin = min possible and tmax = max possible
# use list(s) to get order of tabbed file nice
# make sure you use the correct files (the ones that you have comparisons for)


infile = 'consistency_tests/Yamamoto_Hushi_2008_magic_measurements.txt' #'consistency_tests/Yamamoto_etal_2003_magic_measurements.txt' #'consistency_tests/Tanaka_etal_2012_magic_measurements.txt' #'consistency_tests/Selkin_etal_2000_magic_measurements.txt'#'consistency_tests/Pick_Tauxe_93_magic_measurements.txt'#'consistency_tests/Paterson_etal_2010_magic_measurements.txt' #'consistency_tests/Muxworthy_etal_2011_magic_measurements.txt' #'consistency_tests/Krasa_2000_magic_measurements.txt'#'consistency_tests/Donadini_etal_2007_magic_measurements.txt' #'consistency_tests/Biggin_etal_2007_magic_measurements.txt'#'consistency_tests/Bowles_etal_2006_magic_measurements.txt'#
outfile ='consistency_tests/Yamamoto_Hushi_2008.out.csv' #'consistency_tests/Yamamoto_etal_2003.out.csv' #'consistency_tests/Tanaka_etal_2012.out.csv'#'consistency_tests/Selkin_etal_2000.out.csv' #'consistency_tests/Pick_Tauxe_93.out.csv' #'consistency_tests/Paterson_etal_2010.out.csv' #'consistency_tests/Muxworthy_etal_2011.out.csv' #consistency_tests/Krasa_2000.out.csv'#'consistency_tests/Donadini_etal_2007.out.csv' #'consistency_tests/Biggin_etal_2007.out.csv'# 'consistency_tests/Bowles_etal_2006.out.csv'# 

print sys.argv

if '-f' in sys.argv:
    print 'ffffffff'
    infile_ind = sys.argv.index('-f') + 1
    infile = sys.argv[infile_ind]

if '-F' in sys.argv:
    outfile_ind = sys.argv.index('-F') + 1
    outfile = sys.argv[outfile_ind]
    

# will need to put IZZI_MD back in, theoretically
        
basic_stats = ['s', 'specimen_n', 'tmin', 'tmax'] # start, end  # removed these two because no equivalent in Greig's code

arai_plot_stats = ['specimen_b', 'specimen_b_sigma', 'B_lab', 'B_anc', 'B_anc_sigma', 'specimen_YT', 'specimen_XT', 'specimen_vds',  'delta_x_prime', 'delta_y_prime', 'specimen_f', 'specimen_fvds', 'FRAC', 'specimen_b_beta', 'specimen_g', 'GAP-MAX', 'specimen_q', 'specimen_w', 'specimen_k', 'SSE', 'SCAT', 'R_corr2', 'R_det2', 'Z', 'Zstar']#, 'IZZI_MD']  #  'x_prime', 'y_prime',  # removed these two because they are listy and it sucks

directional_stats = ['Dec_Free', 'Dec_Anc', 'Inc_Free', 'Inc_Anc', 'MAD_Free', 'MAD_Anc', 'alpha', 'theta', 'DANG', 'NRM_dev', 'gamma']

ptrm_stats = ['n_ptrm', 'max_ptrm_check_percent', 'delta_CK', 'DRAT', 'max_DEV', 'CDRAT', 'CDRAT_prime', 'DRATS', 'DRATS_prime', 'mean_DRAT', 'mean_DRAT_prime', 'mean_DEV', 'mean_DEV_prime', 'delta_pal']

tail_stats = ['n_tail', 'DRAT_tail', 'delta_TR', 'MD_VDS']

additivity_stats = ['n_add', 'delta_AC']

long_list = arai_plot_stats + directional_stats + ptrm_stats + tail_stats + additivity_stats




import SPD.new_lj_thellier_gui_spd as tgs

print "starting thingee"

print 'outfile', outfile
print 'infile', infile
read_in = open(infile, 'r')
print read_in
print read_in.readline()
print read_in.readline()
print read_in.readline()
print read_in.readline()
# create tab file

def init_outfile(outfile):
    out = open(outfile, 'w+')
    for stat in basic_stats:
        out.write(stat + '\t')
    for stat in long_list:
        out.write(stat + '\t')
    out.write('\n')
    return out


# iterate through list of magic_measurements files and fill outfile

cwd = os.getcwd() + '/'
directory = cwd + '/consistency_tests'
gui = tgs.Arai_GUI(infile, cwd)
data = gui.Data

def check_at_temperature(gui, out, tmin_index, tmax_index, rep=0):
    print "checking at tmin: {}, tmax: {}".format(tmin_index, tmax_index)
    specimen_names = gui.Data.keys()
    for s in specimen_names:
        try:
            spec = spd.PintPars(gui.Data, s, gui.Data[s]['t_Arai'][tmin_index], gui.Data[s]['t_Arai'][tmax_index])
            spec.s = spec.s.replace('-', '_')
            #spec.s = spec.s + "_rep_" + str(rep)
            spec.s = spec.s + "_" + str(tmin_index) + "_" + str(tmax_index)
            print spec.s, spec.tmin, spec.tmax
            spec.calculate_all_statistics()
            out.write("s: {} \t n: {} \t Tmin: {} \t Tmax: {} \t".format(str(spec.s), str(spec.pars['specimen_n']), str(spec.tmin_K), str(spec.tmax_K)))
            for stat in long_list:
                if type(spec.pars[stat]) == numpy.ndarray:  # catches arrays to prevent extra newlines being auto-inserted
                    out.write(str(stat) + ": " + numpy.array_str(spec.pars[stat], max_line_width=10000000) + '\t')
                else:
                    out.write(str(stat) + ": " + str(spec.pars[stat]) + '\t')
            out.write('\n')
        except IndexError as ex:
            print ex
            print type(ex)
    #out.write('Next temperature\n')
#out.close()




out = init_outfile(outfile)
print type(out)
#check_at_temperature(gui, out, 0, 6)

#check_at_temperature(gui, out, 0, 19)
#out.close()




def get_combos(nmax=20):
    lst = range(nmax)
    combos = []
    for i in lst:
        start = i
        for n in lst[i+2:]:
            combos.append((start, n))
    return combos

combos = get_combos()
print combos


for num, c in enumerate(combos):
    check_at_temperature(gui, out, c[0], c[1], num)

out.close()


        
ignore = """
lst = range(10)
combinations = []
for n, i in enumerate(lst):
    ind = lst.index(i)
    for z in lst[ind+2:]:
        combinations.append((i,z))
print combinations
    
    
"""
