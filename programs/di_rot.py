#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
  matplotlib.use("TKAgg")
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
        di_rot.py

    DESCRIPTION
        rotates set of directions to new coordinate system

    SYNTAX
        di_rot.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f specify input file, default is standard input
        -F specify output file, default is standard output
        -D D specify  Dec of new coordinate system, default is 0
        -I I specify  Inc of new coordinate system, default is 90
    INTPUT/OUTPUT
        dec  inc   [space delimited]  


    """
    D,I=0.,90.
    outfile=""
    infile=""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
        data=numpy.loadtxt(infile)
    else:
        data=numpy.loadtxt(sys.stdin,dtype=numpy.float)
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=sys.argv[ind+1]
        out=open(outfile,'w')
    if '-D' in sys.argv:
        ind=sys.argv.index('-D')
        D=float(sys.argv[ind+1])
    if '-I' in sys.argv:
        ind=sys.argv.index('-I')
        I=float(sys.argv[ind+1])
    if len(data.shape)>1: # 2-D array
        N=data.shape[0] 
        DipDir,Dip=numpy.ones(N,dtype=numpy.float).transpose()*(D-180.),numpy.ones(N,dtype=numpy.float).transpose()*(90.-I)
        data=data.transpose()
        data=numpy.array([data[0],data[1],DipDir ,Dip]).transpose()
        drot,irot=pmag.dotilt_V(data)
        drot=(drot-180.)%360.  # 
        for k in range(N): 
             if outfile=="":
                print('%7.1f %7.1f ' % (drot[k],irot[k]))
             else:
                out.write('%7.1f %7.1f\n' % (drot[k],irot[k]))
    else: 
        d,i=pmag.dotilt(data[0],data[1],(D-180.),90.-I)
        if outfile=="":
            print('%7.1f %7.1f ' % ((d-180.)%360.,i))
        else:
            out.write('%7.1f %7.1f\n' % ((d-180.)%360.,i))

if __name__ == "__main__":
    main()
