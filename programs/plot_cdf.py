#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        plot_cdf.py

    DESCRIPTION
        makes plots of cdfs of data in input file 

    SYNTAX
        plot_cdf.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE
        -t TITLE
        -fmt [svg,eps,png,pdf,jpg..] specify format of output figure, default is svg
        -sav saves plot and quits
        
    """
    fmt,plot='svg',0
    title=""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-sav' in sys.argv:plot=1
    if '-f' in sys.argv:
       ind=sys.argv.index('-f')
       file=sys.argv[ind+1] 
       X=numpy.loadtxt(file)
#    else:
#       X=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    else:
       print('-f option required')
       print(main.__doc__)
       sys.exit()
    if '-fmt' in sys.argv:
       ind=sys.argv.index('-fmt')
       fmt=sys.argv[ind+1] 
    if '-t' in sys.argv:
       ind=sys.argv.index('-t')
       title=sys.argv[ind+1] 
    CDF={'X':1}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plot_cdf(CDF['X'],X,title,'r','')
    files={'X':'CDF_.'+fmt}
    if plot==0:
        pmagplotlib.draw_figs(CDF)
        ans= input('S[a]ve  plot, <Return> to quit ')
        if ans=='a':
            pmagplotlib.save_plots(CDF,files)
    else:
        pmagplotlib.save_plots(CDF,files)
if __name__ == "__main__":
    main()
