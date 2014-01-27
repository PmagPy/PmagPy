#!/usr/bin/env python
import sys
from . import pmagplotlib
from . import pmag


def main():
    """
    NAME
       watsonsV.py

    DESCRIPTION
       calculates Watson's V statistic from input files

    INPUT FORMAT
       takes dec/inc as first two columns in two space delimited files

    SYNTAX
       watsonsV.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE (with optional second)
        -f2 FILE (second file)
        -ant,  flip antipodal directions in FILE to opposite direction
        -P  (don't plot)

    OUTPUT
        Watson's V and the Monte Carlo Critical Value Vc.
        in plot, V is solid and Vc is dashed.

    """
    D1, D2 = [], []
    Flip = 0
    plot = 1
    if '-h' in sys.argv:  # check if help is needed
        print main.__doc__
        sys.exit()  # graceful quit
    if '-ant' in sys.argv:
        Flip = 1
    if '-P' in sys.argv:
        plot = 0
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        file1 = sys.argv[ind + 1]
    f = open(file1, 'rU')
    for line in f.readlines():
        rec = line.split()
        Dec, Inc = float(rec[0]), float(rec[1])
        D1.append([Dec, Inc, 1.])
    f.close()
    if '-f2' in sys.argv:
        ind = sys.argv.index('-f2')
        file2 = sys.argv[ind + 1]
        f = open(file2, 'rU')
        for line in f.readlines():
            if '\t' in line:
                # split each line on space to get records
                rec = line.split('\t')
            else:
                rec = line.split()  # split each line on space to get records
            Dec, Inc = float(rec[0]), float(rec[1])
            if Flip == 0:
                D2.append([Dec, Inc, 1.])
            else:
                D1.append([Dec, Inc, 1.])
        f.close()
        if Flip == 1:
            D1, D2 = pmag.flip(D1)
#
    counter, NumSims = 0, 5000
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_1 = pmag.fisher_mean(D1)
    pars_2 = pmag.fisher_mean(D2)
#
# get V statistic for these
#
    V = pmag.vfunc(pars_1, pars_2)
#
# do monte carlo simulation of datasets with same kappas, but common mean
#
    Vp = []  # set of Vs from simulations
    if plot == 1:
        print "Doing ", NumSims, " simulations"
    for k in range(NumSims):
        counter += 1
        if counter == 50:
            if plot == 1:
                print k + 1
            counter = 0
        Dirp = []
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
        for i in range(pars_1["n"]):
            Dirp.append(pmag.fshdev(pars_1["k"]))
        pars_p1 = pmag.fisher_mean(Dirp)
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
        Dirp = []
        for i in range(pars_2["n"]):
            Dirp.append(pmag.fshdev(pars_2["k"]))
        pars_p2 = pmag.fisher_mean(Dirp)
# get the V for these
        Vk = pmag.vfunc(pars_p1, pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th one)
#
    Vp.sort()
    k = int(.95 * NumSims)
    print "Watson's V,  Vcrit: "
    print '   %10.1f %10.1f' % (V, Vp[k])
    if plot == 1:
        CDF = {'cdf': 1}
        pmagplotlib.plot_init(CDF['cdf'], 5, 5)
        pmagplotlib.plotCDF(CDF['cdf'], Vp, "Watson's V", 'r', "")
        pmagplotlib.plotVs(CDF['cdf'], [V], 'g', '-')
        pmagplotlib.plotVs(CDF['cdf'], [Vp[k]], 'b', '--')
        pmagplotlib.drawFIGS(CDF)
        files, fmt = {}, 'svg'
        if file2 != "":
            files['cdf'] = 'WatsonsV_' + file1 + '_' + file2 + '.' + fmt
        else:
            files['cdf'] = 'WatsonsV_' + file1 + '.' + fmt
        if pmagplotlib.isServer:
            black = '#000000'
            purple = '#800080'
            titles = {}
            titles['cdf'] = 'Cumulative Distribution'
            CDF = pmagplotlib.addBorders(CDF, titles, black, purple)
            pmagplotlib.saveP(CDF, files)
        else:
            ans = raw_input(" S[a]ve to save plot, [q]uit without saving:  ")
            if ans == "a":
                pmagplotlib.saveP(CDF, files)
main()
