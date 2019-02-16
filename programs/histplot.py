#!/usr/bin/env python
import sys
import numpy as np
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from matplotlib import pyplot as plt
from pmagpy import pmagplotlib


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
    fname, fmt = "", 'svg'
    plot = 0
    if '-sav' in sys.argv:
        plot = 1
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        fname = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        outfile = sys.argv[ind+1]
        fmt = ""
    else:
        outfile = 'hist.'+fmt
    if '-N' in sys.argv:
        norm = 0
        ylab = 'Number'
    else:
        norm = 1
        ylab = 'Frequency'
    if '-twin' in sys.argv:
        norm=-1
    binsize = 0
    if '-b' in sys.argv:
        ind = sys.argv.index('-b')
        binsize = int(sys.argv[ind+1])
    if '-xlab' in sys.argv:
        ind = sys.argv.index('-xlab')
        xlab = sys.argv[ind+1]
    else:
        xlab = 'x'
    if fname != "":
        D = np.loadtxt(fname)
    else:
        print('-I- Trying to read from stdin... <ctrl>-c to quit')
        D = np.loadtxt(sys.stdin, dtype=np.float)
    # read in data
    #
    try:
        if not D:
            print('-W- No data found')
            return
    except ValueError:
        pass
    fig = pmagplotlib.plot_init(1, 8, 7)
    try:
        len(D)
    except TypeError:
        D = np.array([D])
    if len(D) < 5:
        print("-W- Not enough points to plot histogram ({} point(s) provided, 5 required)".format(len(D)))
        return
    # if binsize not provided, calculate reasonable binsize
    if not binsize:
        binsize = int(np.around(1 + 3.22 * np.log(len(D))))
    Nbins = int(len(D) / binsize)
    ax = fig.add_subplot(111)
    if norm==1:
        print ('normalizing')
        n, bins, patches = ax.hist(
            D, bins=Nbins, facecolor='#D3D3D3', histtype='stepfilled', color='black', density=True)
        ax.set_ylabel(ylab)
    elif norm==0:
        print ('not normalizing')
        n, bins, patches = ax.hist(
            D, bins=Nbins, facecolor='#D3D3D3', histtype='stepfilled', color='black', density=False)
        ax.set_ylabel(ylab)
    elif norm==-1:
        print ('trying twin')
        n, bins, patches = ax.hist(
            D, bins=Nbins, facecolor='#D3D3D3', histtype='stepfilled', color='black', density=True)
        ax.set_ylabel('Frequency')
        ax2=ax.twinx()
        n, bins, patches = ax2.hist(
            D, bins=Nbins, facecolor='#D3D3D3', histtype='stepfilled', color='black', density=False)
        ax2.set_ylabel('Number',rotation=-90)
    plt.axis([D.min(), D.max(), 0, n.max()+.1*n.max()])
    ax.set_xlabel(xlab)
    name = 'N = ' + str(len(D))
    plt.title(name)
    if plot == 0:
        pmagplotlib.draw_figs({1: 'hist'})
        p = input('s[a]ve to save plot, [q]uit to exit without saving  ')
        if p != 'a':
            sys.exit()
    if pmagplotlib.isServer:
        pmagplotlib.add_borders({'hist': 1}, {'hist': 'Intensity Histogram'})
    plt.savefig(outfile)
    print('plot saved in ', outfile)


if __name__ == "__main__":
    main()
