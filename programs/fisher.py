#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

def spitout(kappa):
    dec,inc= pmag.fshdev(kappa)  # send kappa to fshdev
    print('%7.1f %7.1f ' % (dec,inc))
    return

def main():
    """
    NAME
        fisher.py

    DESCRIPTION
        generates set of Fisher distribed data from specified distribution

    INPUT (COMMAND LINE ENTRY)
    OUTPUT
        dec,  inc

    SYNTAX
        fisher.py [-h] [-i] [command line options]

    OPTIONS
        -h prints help message and quits
        -i for interactive  entry
        -k specify kappa as next argument, default is 20
        -n specify N as next argument, default is 100
        where:
            kappa:  fisher distribution concentration parameter
            N:  number of directions desired

    """
    N,kappa=100,20
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    elif '-i' in sys.argv:
        ans=input('    Kappa: ')
        kappa=float(ans)
        ans=input('    N: ')
        N=int(ans)
    else:
        if '-k' in sys.argv:
            ind=sys.argv.index('-k')
            kappa=float(sys.argv[ind+1])
        if '-n' in sys.argv:
            ind=sys.argv.index('-n')
            N=int(sys.argv[ind+1])
    for k in range(N): spitout(kappa)

if __name__ == '__main__':
    main()
