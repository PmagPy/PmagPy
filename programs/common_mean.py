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
       common_mean.py

    DESCRIPTION
       calculates bootstrap statistics to test for common mean

    INPUT FORMAT
       takes dec/inc as first two columns in two space delimited files
   
    SYNTAX
       common_mean.py [command line options]
    
    OPTIONS
       -h prints help message and quits
       -f FILE, input file 
       -f2 FILE, optional second file to compare with first file
       -dir D I, optional direction to compare with input file
       -fmt [svg,jpg,pnd,pdf] set figure format [default is svg]
    NOTES
       must have either F2 OR dir but not both
     

    """
    d,i,file2="","",""
    fmt,plot='svg',0
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-sav' in sys.argv: plot=1
    if '-fmt'  in sys.argv:
        ind=sys.argv.index('-fmt')
        fmt=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file1=sys.argv[ind+1]
    if '-f2' in sys.argv:
        ind=sys.argv.index('-f2')
        file2=sys.argv[ind+1]
    if '-dir' in sys.argv:
        ind=sys.argv.index('-dir')
        d=float(sys.argv[ind+1])
        i=float(sys.argv[ind+2])
    D1=numpy.loadtxt(file1,dtype=numpy.float)
    if file2!="": D2=numpy.loadtxt(file2,dtype=numpy.float)
#
    counter,NumSims=0,1000
#
# get bootstrapped means for first data set
#
    print("Doing first set of directions, please be patient..")
    BDI1=pmag.di_boot(D1)
#
#   convert to cartesian coordinates X1,X2, Y1,Y2 and Z1, Z2
#
    if d=="": # repeat for second data set
        print("Doing second  set of directions, please be patient..")
        BDI2=pmag.di_boot(D2)
    else:
        BDI2=[]
# set up plots
    CDF={'X':1,'Y':2,'Z':3}
    pmagplotlib.plot_init(CDF['X'],4,4)
    pmagplotlib.plot_init(CDF['Y'],4,4)
    pmagplotlib.plot_init(CDF['Z'],4,4)
# draw the cdfs
    pmagplotlib.plotCOM(CDF,BDI1,BDI2,[d,i])
    files={}
    files['X']='CD_X.'+fmt
    files['Y']='CD_Y.'+fmt
    files['Z']='CD_Z.'+fmt
    if plot==0:
        pmagplotlib.drawFIGS(CDF)
        ans=input("S[a]ve plots, <Return> to quit ")
        if ans=="a":
            pmagplotlib.saveP(CDF,files)
        else:
            sys.exit()
        
    else: 
        pmagplotlib.saveP(CDF,files)
        sys.exit()
if __name__ == "__main__":
    main()

