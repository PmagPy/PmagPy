#!/usr/bin/env python
import sys
import os
import math
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

import operator
OPS = {'<' : operator.lt, '<=' : operator.le,
       '>' : operator.gt, '>=': operator.ge, '=': operator.eq}


def main():
    """
    NAME
       revtest_magic.py

    DESCRIPTION
       calculates bootstrap statistics to test for antipodality

    INPUT FORMAT
       takes dec/inc data from sites table

    SYNTAX
       revtest_magic.py [command line options]

    OPTION
       -h prints help message and quits
       -f FILE, sets pmag_sites filename on command line
       -crd [s,g,t], set coordinate system, default is geographic
       -exc use criteria file to set acceptance criteria (only available for data model 3)
       -fmt [svg,png,jpg], sets format for image output
       -sav saves plot and quits
       -DM [2, 3] MagIC data model num, default is 3

    """
    if '-h' in sys.argv:  # check if help is needed
        print(main.__doc__)
        sys.exit()  # graceful quit
    dir_path = pmag.get_named_arg("-WD", ".")
    coord = pmag.get_named_arg("-crd", "0") # default to geographic coordinates
    if coord == 's':
        coord = '-1'
    elif coord == 'g':
        coord = '0'
    elif coord == 't':
        coord = '100'
    fmt = pmag.get_named_arg("-fmt", "svg")
    if '-sav' in sys.argv:
        plot = 1
    data_model = int(float(pmag.get_named_arg("-DM")))
    if data_model == 2:
        infile = pmag.get_named_arg("-f", "pmag_sites.txt")
        critfile = "pmag_criteria.txt"
        tilt_corr_col = 'site_tilt_correction'
        dec_col = "site_dec"
        inc_col = "site_inc"
        crit_code_col = "pmag_criteria_code"
    else:
        infile = pmag.get_named_arg("-f", "sites.txt")
        critfile = "criteria.txt"
        tilt_corr_col = "dir_tilt_correction"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        crit_code_col = "criterion"
    D = []

#
    infile = pmag.resolve_file_name(infile, dir_path)
    dir_path = os.path.split(infile)[0]
    critfile = pmag.resolve_file_name(critfile, dir_path)
    #
    if data_model == 2:
        Accept = ['site_k', 'site_alpha95', 'site_n', 'site_n_lines']
    else:
        Accept = ['dir_k', 'dir_alpha95', 'dir_n_samples', 'dir_n_specimens_line']
    data, file_type = pmag.magic_read(infile)
    if 'sites' not in file_type:
        print("Error opening file", file_type)
        sys.exit()
#    ordata,file_type=pmag.magic_read(orfile)
    SiteCrits = []
    if '-exc' in sys.argv and data_model != 2:
        crits, file_type = pmag.magic_read(critfile)
        for crit in crits:
            if crit[crit_code_col] == "DE-SITE":
                SiteCrit = crit
                SiteCrits.append(SiteCrit)
    elif '-exc' in sys.argv and data_model == 2:
        print('-W- You have selected the -exc option, which is not available with MagIC data model 2.')
    for rec in data:
        if rec[tilt_corr_col] == coord:
            Dec = float(rec[dec_col])
            Inc = float(rec[inc_col])
            if '-exc' in sys.argv and data_model != 2:
                fail = False
                for SiteCrit in SiteCrits:
                    for key in Accept:
                        if key not in SiteCrit['table_column']:
                            continue
                        if key not in rec:
                            continue
                        if SiteCrit['criterion_value'] != "":
                            op = OPS[SiteCrit['criterion_operation']]
                            if not op(float(rec[key]), float(SiteCrit['criterion_value'])):
                                fail = True
                if not fail:
                    D.append([Dec, Inc, 1.])
            else:
                D.append([Dec, Inc, 1.])
# set up plots

    CDF = {'X': 1, 'Y': 2, 'Z': 3}
    pmagplotlib.plot_init(CDF['X'], 5, 5)
    pmagplotlib.plot_init(CDF['Y'], 5, 5)
    pmagplotlib.plot_init(CDF['Z'], 5, 5)
#
# flip reverse mode
#
    D1, D2 = pmag.flip(D)
    counter, NumSims = 0, 500
#
# get bootstrapped means for each data set
#
    if len(D1) < 5 or len(D2) < 5:
        print('not enough data in two different modes for reversals test')
        sys.exit()
    print('doing first mode, be patient')
    BDI1 = pmag.di_boot(D1)
    print('doing second mode, be patient')
    BDI2 = pmag.di_boot(D2)
    pmagplotlib.plot_com(CDF, BDI1, BDI2, [""])
    files = {}
    for key in list(CDF.keys()):
        files[key] = 'REV'+'_'+key+'.'+fmt
    if plot == 0:
        pmagplotlib.draw_figs(CDF)
        ans = input("s[a]ve plots, [q]uit: ")
        if ans == 'a':
            pmagplotlib.save_plots(CDF, files)
    else:
        pmagplotlib.save_plots(CDF, files)
        sys.exit()


if __name__ == "__main__":
    main()
