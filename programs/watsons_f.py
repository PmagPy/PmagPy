#!/usr/bin/env python
import sys


import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag

def main():
    """
    NAME
       watsonsF.py

    DESCRIPTION
       calculates Watson's F statistic from input files

    INPUT FORMAT
       takes dec/inc as first two columns in two space delimited files
   
    SYNTAX
       watsonsF.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE (with optional second)
        -f2 FILE (second file) 
        -ant,  flip antipodal directions in FILE to opposite direction

    OUTPUT
        Watson's F, critical value from F-tables for 2, 2(N-2) degrees of freedom

    """
    D,D1,D2=[],[],[]
    Flip=0
    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit
    if '-ant' in  sys.argv: Flip=1
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file1=sys.argv[ind+1]
    if '-f2' in sys.argv:
        ind=sys.argv.index('-f2')
        file2=sys.argv[ind+1]
    f=open(file1,'rU')
    for line in f.readlines():
        if '\t' in line:
            rec=line.split('\t') # split each line on space to get records
        else:
            rec=line.split() # split each line on space to get records
        Dec,Inc=float(rec[0]),float(rec[1]) 
        D1.append([Dec,Inc,1.])
        D.append([Dec,Inc,1.])
    f.close()
    if Flip==0:
        f=open(file2,'rU')
        for line in f.readlines():
            rec=line.split()
            Dec,Inc=float(rec[0]),float(rec[1]) 
            D2.append([Dec,Inc,1.])
            D.append([Dec,Inc,1.])
        f.close()
    else:
        D1,D2=pmag.flip(D1)
        for d in D2: D.append(d) 
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_0=pmag.fisher_mean(D)
    pars_1=pmag.fisher_mean(D1)
    pars_2=pmag.fisher_mean(D2)
#
# get F statistic for these
#
    N= len(D)
    R=pars_0['r']
    R1=pars_1['r']
    R2=pars_2['r']
    F=(N-2)*((R1+R2-R)/(N-R1-R2))
    Fcrit=pmag.fcalc(2,2*(N-2))
    print '%7.2f %7.2f'%(F,Fcrit)

if __name__ == "__main__":
    main()

