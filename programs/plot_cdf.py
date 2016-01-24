#!/usr/bin/env python
import sys
import numpy
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
        
    """
    fmt='svg'
    title=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
       ind=sys.argv.index('-f')
       file=sys.argv[ind+1] 
       X=numpy.loadtxt(file)
#    else:
#       X=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    else:
       print '-f option required'
       print main.__doc__
       sys.exit()
    if '-fmt' in sys.argv:
       ind=sys.argv.index('-fmt')
       fmt=sys.argv[ind+1] 
    if '-t' in sys.argv:
       ind=sys.argv.index('-t')
       title=sys.argv[ind+1] 
    CDF={'X':1}
    pmagplotlib.plot_init(CDF['X'],5,5)
    pmagplotlib.plotCDF(CDF['X'],X,title,'r','')
    pmagplotlib.drawFIGS(CDF)
    ans= raw_input('S[a]ve  plot, <Return> to quit ')
    if ans=='a':
        files={'X':'CDF_.'+fmt}
        pmagplotlib.saveP(CDF,files)

if __name__ == "__main__":
    main()
