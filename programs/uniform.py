#! /usr/bin/env python
from __future__ import print_function
import sys
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
        uniform.py

    DESCRIPTION
        draws N directions from uniform distribution on a sphere
    
    SYNTAX 
        uniform.py [-h][command line options]
        -h prints help message and quits
        -n N, specify N on the command line (default is 100)
        -F file, specify output file name, default is standard output
    """
    outf=""
    N=100
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outf=sys.argv[ind+1]
    if outf!="": out=open(outf,'w')
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        N=int(sys.argv[ind+1])
    dirs=pmag.get_unf(N)
    if outf=='':
        for dir in dirs:
            print('%7.1f %7.1f'%(dir[0],dir[1]))
    else:
        numpy.savetxt(outf,dirs,fmt='%7.1f %7.1f')

if __name__ == "__main__":
    main()
