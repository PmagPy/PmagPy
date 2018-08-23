#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from matplotlib import pyplot as plt
import numpy
import pmagpy.pmag as pmag
from pmagpy import pmagplotlib
#


def main():
    """
    NAME
        igrf.py
    DESCRIPTION
        This program calculates igrf field values
    using the routine of Malin and  Barraclough (1981)
    based on d/igrfs from 1900 to 2010.
    between 1900 and 1000BCE, it uses CALS3K.4, ARCH3K.1
    Prior to 1000BCE, it uses PFM9k or CALS10k-4b
    Calculates reference field vector at  specified location and time.

    SYNTAX
       igrf.py [-h] [-i] -f FILE  [< filename]
    OPTIONS:
       -h prints help message and quits
       -i for interactive data entry
       -f FILE  specify file name with input data
       -fgh FILE specify file with custom field coefficients in format:  l m g h
       -F FILE  specify output file name
       -ages MIN MAX INCR: specify age minimum in years (+/- AD), maximum and increment, default is line by line
       -loc LAT LON;  specify location, default is line by line
       -alt ALT;  specify altitude in km, default is sealevel (0)
       -plt; make a plot of the time series
       -sav, saves plot and quits
       -fmt [pdf,jpg,eps,svg]  specify format for output figure  (default is svg)
       -mod [arch3k,cals3k,pfm9k,hfm10k,cals10k.2,shadif14k,cals10k.1b] specify model for 3ka to 1900 AD, default is cals10k
             NB:  program uses IGRF12 for dates 1900 to 2015.

    INPUT FORMAT
      interactive entry:
           date: decimal year
           alt:  altitude in km
           lat: positive north
           lon: positive east
       for file entry:
           space delimited string: date  alt   lat long
    OUTPUT  FORMAT
        Declination Inclination Intensity (nT) date alt lat long
    MODELS:  ARCH3K: (Korte et al., 2009);CALS3K (Korte & Contable, 2011); CALS10k (is .1b of Korte et al., 2011); PFM9K (Nilsson et al., 2014); HFM10k (is HFM.OL1.A1 of Constable et al., 2016); CALS10k_2 (is cals10k.2 of Constable et al., 2016), SHADIF14k (SHA.DIF.14K of Pavon-Carrasco et al., 2014).
    """
    plot, fmt = 0, 'svg'
    mod, alt, make_plot, lat, lon = 'cals10k', 0, 0, 0, 0
    if '-loc' in sys.argv:
        ind = sys.argv.index('-loc')
        lat = float(sys.argv[ind+1])
        lon = float(sys.argv[ind+2])
    if '-alt' in sys.argv:
        ind = sys.argv.index('-alt')
        alt = float(sys.argv[ind+1])
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if len(sys.argv) != 0 and '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-mod' in sys.argv:
        ind = sys.argv.index('-mod')
        mod = sys.argv[ind+1]
    if '-fgh' in sys.argv:
        ind = sys.argv.index('-fgh')
        ghfile = sys.argv[ind+1]
        lmgh = numpy.loadtxt(ghfile)
        gh = []
        lmgh = numpy.loadtxt(ghfile).transpose()
        gh.append(lmgh[2][0])
        for i in range(1, lmgh.shape[1]):
            gh.append(lmgh[2][i])
            gh.append(lmgh[3][i])
        mod = 'custom'
        inp = [[0, alt, lat, lon]]
    elif '-f' in sys.argv:
        ind = sys.argv.index('-f')
        file = sys.argv[ind+1]
        inp = numpy.loadtxt(file)
    elif '-i' in sys.argv:
        while 1:
            try:
                line = []
                if mod != 'custom':
                    line.append(
                        float(input("Decimal year: <cntrl-D to quit> ")))
                else:
                    line.append(0)
                alt = input("Elevation in km [0] ")
                if alt == "":
                    alt = "0"
                line.append(float(alt))
                line.append(float(input("Latitude (positive north) ")))
                line.append(float(input("Longitude (positive east) ")))
                if mod == '':
                    x, y, z, f = pmag.doigrf(
                        line[3] % 360., line[2], line[1], line[0])
                elif mod == 'custom':
                    x, y, z, f = pmag.docustom(
                        line[3] % 360., line[2], line[1], gh)
                else:
                    x, y, z, f = pmag.doigrf(
                        line[3] % 360., line[2], line[1], line[0], mod=mod)
                Dir = pmag.cart2dir((x, y, z))
                print('%8.2f %8.2f %8.0f' % (Dir[0], Dir[1], f))
            except EOFError:
                print("\n Good-bye\n")
                sys.exit()
    elif '-ages' in sys.argv:
        ind = sys.argv.index('-ages')
        agemin = float(sys.argv[ind+1])
        agemax = float(sys.argv[ind+2])
        ageincr = float(sys.argv[ind+3])
        ages = numpy.arange(agemin, agemax, ageincr)
        lats = numpy.ones(len(ages))*lat
        lons = numpy.ones(len(ages))*lon
        alts = numpy.ones(len(ages))*alt
        inp = numpy.array([ages, alts, lats, lons]).transpose()
    else:
        inp = numpy.loadtxt(sys.stdin, dtype=numpy.float)
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        outfile = sys.argv[ind+1]
        out = open(outfile, 'w')
    else:
        outfile = ""
    if '-sav' in sys.argv:
        plot = 1
    if '-plt' in sys.argv:
        make_plot = 1
        Ages, Decs, Incs, Ints, VADMs = [], [], [], [], []
    for line in inp:
        if mod != 'custom':
            x, y, z, f = pmag.doigrf(
                line[3] % 360., line[2], line[1], line[0], mod=mod)
        else:
            x, y, z, f = pmag.docustom(line[3] % 360., line[2], line[1], gh)
        Dir = pmag.cart2dir((x, y, z))
        if outfile != "":
            out.write('%8.2f %8.2f %8.0f %7.1f %7.1f %7.1f %7.1f\n' %
                      (Dir[0], Dir[1], f, line[0], line[1], line[2], line[3]))
        elif make_plot:
            Ages.append(line[0])
            if Dir[0] > 180:
                Dir[0] = Dir[0]-360.0
            Decs.append(Dir[0])
            Incs.append(Dir[1])
            Ints.append(f*1e-3)
            VADMs.append(pmag.b_vdm(f*1e-9, line[2])*1e-21)
        else:
            print('%8.2f %8.2f %8.0f %7.1f %7.1f %7.1f %7.1f' %
                  (Dir[0], Dir[1], f, line[0], line[1], line[2], line[3]))
    if make_plot:
        pmagplotlib.plot_init(1, 7, 9)
        fig = plt.figure(num=1, figsize=(7, 9))
        fig.add_subplot(411)
        plt.plot(Ages, Decs)
        plt.ylabel('Declination ($^{\circ}$)')
        fig.add_subplot(412)
        plt.plot(Ages, Incs)
        plt.ylabel('Inclination ($^{\circ}$)')
        fig.add_subplot(413)
        plt.plot(Ages, Ints)
        plt.ylabel('Intensity ($\mu$T)')
        fig.add_subplot(414)
        plt.plot(Ages, VADMs)
        plt.ylabel('VADMs (ZAm$^2$)')
        plt.xlabel('Ages')
        # show plot
        if plot == 0:
            pmagplotlib.draw_figs({'time series': 1})
            ans = input("S[a]ve to save figure, <Return>  to quit  ")
            if ans == 'a':
                plt.savefig('igrf.'+fmt)
                print('Figure saved as: ', 'igrf.'+fmt)
        # save plot without showing
        else:
            plt.savefig('igrf.'+fmt)
            print('Figure saved as: ', 'igrf.'+fmt)
        sys.exit()


if __name__ == "__main__":
    main()
