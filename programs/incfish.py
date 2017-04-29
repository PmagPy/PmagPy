#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
       incfish.py

    DESCRIPTION
       calculates fisher parameters from inc only data

    INPUT FORMAT
       takes inc data 

    SYNTAX
       incfish.py [options]  [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive filename entry
        -f FILE, specify input file name
        -F FILE, specify output file name
        < filename for reading from standard input
   
    OUTPUT
       mean inc,Fisher inc, N, R, k, a95

    NOTES
        takes the absolute value of inclinations (to take into account reversals),
        but returns gaussian mean if < 50.0, because of polarity ambiguity and 
        lack of bias.

    """
    inc=[]
    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-i' in sys.argv: # ask for filename
        file=input("Enter file name with inc data: ")
        inc=numpy.loadtxt(file)
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        inc=numpy.loadtxt(file)
    else:
        inc = numpy.loadtxt(sys.stdin,dtype=numpy.float)
    ofile=""
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile= sys.argv[ind+1]
        out = open(ofile, 'w + a')
    #
    #get doincfish to do the dirty work:
    fpars= pmag.doincfish(inc)
    outstring='%7.1f %7.1f  %i %8.1f %7.1f %7.1f'%(fpars['ginc'],fpars['inc'],fpars['n'],fpars['r'],fpars['k'],fpars['alpha95'])
    if ofile == "":
        print(outstring)
    else:
        out.write(outstring+'\n')

if __name__ == "__main__":
    main()
