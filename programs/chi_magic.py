#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import ipmag
from pmagpy import pmag


def main():
    """
    NAME
        chi_magic.py

    DESCRIPTION
        plots magnetic susceptibility as a function of frequency and temperature and AC field

    SYNTAX
        chi_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE, specify measurements format file, default "measurements.txt"
        -T IND, specify temperature step to plot -- NOT IMPLEMENTED
        -e EXP, specify experiment name to plot
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
        -sav save figure and quit

    """
    if "-h" in sys.argv:
        print(main.__doc__)
        return
    infile = pmag.get_named_arg("-f", "measurements.txt")
    dir_path = pmag.get_named_arg("-WD", ".")
    infile = pmag.resolve_file_name(infile, dir_path)
    fmt = pmag.get_named_arg("-fmt", "svg")
    save_plots = False
    interactive = True
    if "-sav" in sys.argv:
        interactive = False
        save_plots = True
    experiments = pmag.get_named_arg("-e", "")
    ipmag.chi_magic(infile, dir_path, experiments, fmt, save_plots, interactive)



if __name__ == "__main__":
    main()
