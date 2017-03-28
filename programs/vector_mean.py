#!/usr/bin/env python
from __future__ import print_function
import sys
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
       vector_mean.py

    DESCRIPTION
       calculates vector mean of vector data

    INPUT FORMAT
       takes dec, inc, int from an input file

    SYNTAX
       vector_mean.py [command line options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -f FILE, specify input file
        -F FILE, specify output file
        < filename for reading from standard input
   
    OUTPUT
       mean dec, mean inc, R, N

    """
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
    else:
        file = sys.stdin  # read from standard input
    ofile=""
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    DIIs=numpy.loadtxt(file,dtype=numpy.float) # read in the data
#
    vpars,R=pmag.vector_mean(DIIs)
    outstring='%7.1f %7.1f   %10.3e %i'%(vpars[0],vpars[1],R,len(DIIs))
    if ofile == "":
        print(outstring)
    else:
        out.write(outstring + "\n")
    #
if __name__ == "__main__":
    main()
