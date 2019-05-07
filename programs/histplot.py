#!/usr/bin/env python
from pmagpy import pmag
from pmagpy import pmagplotlib
from matplotlib import pyplot as plt
import sys
import os
import numpy as np
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import ipmag


def main():
    """
    NAME
       histplot.py

    DESCRIPTION
       makes histograms for data

    OPTIONS
       -h prints help message and quits
       -f input file name
       -b binsize
       -fmt [svg,png,pdf,eps,jpg] specify format for image, default is svg
       -sav save figure and quit
       -F output file name, default is hist.fmt
       -N don't normalize
       -twin plot both normalized and un-normalized y axes
       -xlab Label of X axis
       -ylab Label of Y axis

    INPUT FORMAT
        single variable

    SYNTAX
       histplot.py [command line options] [<file]

    """
    interactive = True
    save_plots = False
    if '-sav' in sys.argv:
        save_plots = True
        interactive = False
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    fmt = pmag.get_named_arg('-fmt', 'svg')
    fname = pmag.get_named_arg('-f', '')
    outfile = pmag.get_named_arg("-F", "")
    norm = 1
    if '-N' in sys.argv:
        norm = 0
    if '-twin' in sys.argv:
        norm = - 1
    binsize = pmag.get_named_arg('-b', 0)
    if '-xlab' in sys.argv:
        ind = sys.argv.index('-xlab')
        xlab = sys.argv[ind+1]
    else:
        xlab = 'x'
    data = []
    if not fname:
        print('-I- Trying to read from stdin... <ctrl>-c to quit')
        data = np.loadtxt(sys.stdin, dtype=np.float)

    ipmag.histplot(fname, data, outfile, xlab, binsize, norm,
             fmt, save_plots, interactive)


if __name__ == "__main__":
    main()
