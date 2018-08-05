#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       revtest.py

    DESCRIPTION
       calculates bootstrap statistics to test for antipodality

    INPUT FORMAT
       takes dec/inc as first two columns in space delimited file
   
    SYNTAX
       revtest.py [-h] [command line options]
    
    OPTION
       -h prints help message and quits
       -f FILE, sets input filename on command line
       -fmt [svg,png,jpg], sets format for image output
       -sav saves the figures silently and quits
               

    """
    fmt,plot='svg',0
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        data=numpy.loadtxt(file).transpose()
        D=numpy.array([data[0],data[1]]).transpose()
    else: 
        print('-f is a required switch')
        print(main.__doc__)
        print(sys.exit())
    if '-fmt' in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-sav' in sys.argv:plot=1
# set up plots
    d=""
    CDF={'X':1,'Y':2,'Z':3}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plot_init(CDF['Y'],5,5)
    pmagplotlib.plot_init(CDF['Z'],5,5)
#
# flip reverse mode
#
    D1,D2=pmag.flip(D)
    counter,NumSims=0,500
#
# get bootstrapped means for each data set
#
    print('doing first mode, be patient')
    BDI1=pmag.di_boot(D1)
    print('doing second mode, be patient')
    BDI2=pmag.di_boot(D2)
    pmagplotlib.plot_com(CDF,BDI1,BDI2,[""])
    files={}
    for key in list(CDF.keys()):
        files[key]='REV'+'_'+key+'.'+fmt 
    if plot==0:
        pmagplotlib.draw_figs(CDF)
        ans=  input("s[a]ve plots, [q]uit: ")
        if ans=='a':
            pmagplotlib.save_plots(CDF,files)
        print('good bye')
        sys.exit()
    else:
        pmagplotlib.save_plots(CDF,files)

if __name__ == "__main__":
    main()
