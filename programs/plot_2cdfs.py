#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import scipy
import numpy


import pmagpy.pmagplotlib as pmagplotlib

def main():
    """
    NAME
        plot_2cdfs.py

    DESCRIPTION
        makes plots of cdfs of data in input file 

    SYNTAX
        plot_2cdfs.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE1 FILE2
        -t TITLE
        -fmt [svg,eps,png,pdf,jpg..] specify format of output figure, default is svg
        
    """
    fmt='svg'
    title=""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
       ind=sys.argv.index('-f')
       file=sys.argv[ind+1] 
       X=numpy.loadtxt(file)
       file=sys.argv[ind+2] 
       X2=numpy.loadtxt(file)
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
    pmagplotlib.plot_cdf(CDF['X'],X,'','r','')
    pmagplotlib.plot_cdf(CDF['X'],X2,title,'b','')
    D,p=scipy.stats.ks_2samp(X,X2)
    if p>=.05:
        print(D,p,' not rejected at 95%')
    else:
        print(D,p,' rejected at 95%')
    pmagplotlib.draw_figs(CDF)
    ans= input('S[a]ve  plot, <Return> to quit ')
    if ans=='a':
        files={'X':'CDF_.'+fmt}
        pmagplotlib.save_plots(CDF,files)

if __name__ == "__main__":
    main()
