#!/usr/bin/env python
from __future__ import print_function
import sys
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
        di_eq.py
    
    DESCRIPTION
      converts dec, inc pairs to  x,y pairs using equal area projection
      NB: do only upper or lower  hemisphere at a time: does not distinguish between up and down.
    
    SYNTAX
        di_eq.py [command line options] [< filename]
    
    OPTIONS
        -h  prints help message and quits
        -f FILE, input file
    """
    out=""
    UP=0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        DI=numpy.loadtxt(file,dtype=numpy.float)
    else:
        DI = numpy.loadtxt(sys.stdin,dtype=numpy.float)  # read from standard input
    Ds=DI.transpose()[0]
    Is=DI.transpose()[1]
    if len(DI)>1: #array of data
       XY=pmag.dimap_V(Ds,Is)
       for xy in XY:
           print('%f %f'%(xy[0],xy[1]))
    else: # single data point
       XY=pmag.dimap(Ds,Is)
       print('%f %f'%(XY[0],XY[1]))

if __name__ == "__main__":
    main()
