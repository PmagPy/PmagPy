#!/usr/bin/env python
# define some variables
from __future__ import print_function
from builtins import str
import numpy as np
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import pylab as plt
from pylab import meshgrid
import pmagpy.pmag as pmag
has_basemap, Basemap = pmag.import_basemap()
import pmagpy.pmagplotlib as pmagplotlib
from matplotlib import cm
import warnings
warnings.filterwarnings("ignore")


def main():
    """
    NAME
        plot_magmap.py

    DESCRIPTION
        makes a color contour map of desired field model

    SYNTAX
        plot_magmap.py [command line options]

    OPTIONS
        -h prints help and quits
        -f FILE  specify field model file with format:  l m g h
        -fmt [pdf,eps,svg,png]  specify format for output figure  (default is png)
        -mod [arch3k,cals3k,pfm9k,hfm10k,cals10k.2,shadif14k,cals10k.1b] specify model for 3ka to 1900 CE, default is  cals10k
        -alt ALT;  specify altitude in km, default is sealevel (0)
        -age specify date in decimal year, default is 2016
        -lon0: 0 longitude for map, default is 0
        -el: [D,I,B,Br]  specify element for plotting
        -cm: [see https://matplotlib.org/users/colormaps.html] specify color map for plotting (default is RdYlBu)

    """
    cmap = 'RdYlBu'
    date = 2016.
    if not Basemap:
        print(
            "-W- Cannot access the Basemap module, which is required to run plot_magmap.py")
        sys.exit()
    dir_path = '.'
    lincr = 1  # level increment for contours
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
        if fmt == 'jpg':
            print('jpg not a supported option')
            print(main.__doc__)
            sys.exit()
    else:
        fmt = 'png'
    if '-cm' in sys.argv:
        ind = sys.argv.index('-cm')
        cmap = sys.argv[ind+1]
    if '-el' in sys.argv:
        ind = sys.argv.index('-el')
        el = sys.argv[ind+1]
    else:
        el = 'B'
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt = sys.argv[ind+1]
    else:
        alt = 0
    if '-lon0' in sys.argv:
        ind = sys.argv.index('-lon0')
        lon_0 = float(sys.argv[ind+1])
    else:
        lon_0 = 0
    if '-mod' in sys.argv:
        ind = sys.argv.index('-mod')
        mod = sys.argv[ind+1]
        ghfile = ''
    elif '-f' in sys.argv:
        ind = sys.argv.index('-f')
        ghfile = sys.argv[ind+1]
        mod = 'custom'
        date = ''
    else:
        mod, ghfile = 'cals10k', ''
    if '-age' in sys.argv:
        ind = sys.argv.index('-age')
        date = float(sys.argv[ind+1])
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt = float(sys.argv[ind+1])
    else:
        alt = 0
    save = pmag.get_flag_arg_from_sys("-sav")
    if mod == 'custom':
        d = 'Custom'
    else:
        d = str(date)
    Ds, Is, Bs, Brs, lons, lats = pmag.do_mag_map(
        date, mod=mod, lon_0=lon_0, alt=alt, file=ghfile)
    if el == 'D':
        element = Ds
    elif el == 'I':
        element = Is
    elif el == 'B':
        element = Bs
    elif el == 'Br':
        element = Brs
    elif el == 'I':
        element = Is
    else:
        print(main.__doc__)
        sys.exit()
    pmagplotlib.plot_mag_map(1, element, lons, lats, el, lon_0=0, date=date)
    if not save:
        pmagplotlib.draw_figs({'map': 1})
        res = pmagplotlib.save_or_quit()
        if res == 'a':
            figname = 'igrf'+d+'.'+fmt
            print("1 saved in ", figname)
            plt.savefig('igrf'+d+'.'+fmt)
        sys.exit()
    plt.savefig('igrf'+d+'.'+fmt)
    print('Figure saved as: ', 'igrf'+d+'.'+fmt)


if __name__ == "__main__":
    main()
