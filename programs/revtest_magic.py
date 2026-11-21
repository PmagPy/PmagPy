#!/usr/bin/env python
import sys
import os
import math
from pmag_env import set_env
set_env.set_backend_if_unset("TKAgg")

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
       -DM 3 (the only supported data model)

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
    data_model = float(pmag.get_named_arg("-DM", 3))
    if data_model != 3:
        raise SystemExit(
            "-E- revtest_magic supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before testing."
        )
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
    Accept = ['dir_k', 'dir_alpha95', 'dir_n_samples', 'dir_n_specimens_line']
    data, file_type = pmag.magic_read(infile)
    if 'sites' not in file_type:
        print("Error opening file", file_type)
        sys.exit()
#    ordata,file_type=pmag.magic_read(orfile)
    SiteCrits = []
    if '-exc' in sys.argv:
        crits, file_type = pmag.magic_read(critfile)
        for crit in crits:
            if crit[crit_code_col] == "DE-SITE":
                SiteCrit = crit
                SiteCrits.append(SiteCrit)
    for rec in data:
        if rec[tilt_corr_col] == coord:
            Dec = float(rec[dec_col])
            Inc = float(rec[inc_col])
            if '-exc' in sys.argv:
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
