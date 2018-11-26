#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import ipmag
from pmagpy import pmag


def main():
    """
    NAME
        hysteresis_magic.py

    DESCRIPTION
        calculates hystereis parameters and saves them in 3.0 specimen format file
        makes plots if option selected

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is agm_measurements.txt
        -F: specify specimens.txt output file
        -P: do not make the plots
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    fmt = pmag.get_named_arg('-fmt', 'svg')
    output_dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', "")
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    spec_file = pmag.get_named_arg('-F', 'specimens.txt')
    make_plots = True
    save_plots = False
    if '-P' in args:
        make_plots = False
    if '-sav' in args:
        save_plots = True
    pltspec = pmag.get_named_arg('-spc', 0)
    ipmag.hysteresis_magic(output_dir_path, input_dir_path, spec_file, meas_file,
                           fmt, save_plots, make_plots, pltspec)



if __name__ == "__main__":
    main()
