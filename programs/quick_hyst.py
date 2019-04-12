#!/usr/bin/env python
from pmag_env import set_env
import pmagpy.contribution_builder as cb
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
from pmagpy import ipmag
import sys
import os
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")


def main():
    """
    NAME
        quick_hyst.py

    DESCRIPTION
        makes plots of hysteresis data

    SYNTAX
        quick_hyst.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is measurements.txt
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    pltspec = ""
    verbose = pmagplotlib.verbose
    dir_path = pmag.get_named_arg('-WD', '.')
    dir_path = os.path.realpath(dir_path)
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    fmt = pmag.get_named_arg('-fmt', 'png')
    save_plots = False
    interactive = True
    if '-sav' in args:
        verbose = False
        save_plots = True
        interactive = False
    if '-spc' in args:
        ind = args.index("-spc")
        pltspec = args[ind+1]
        verbose = False
        save_plots = True
    ipmag.quick_hyst(dir_path, meas_file, save_plots,
                     interactive, fmt, pltspec, verbose)




if __name__ == "__main__":
    main()
