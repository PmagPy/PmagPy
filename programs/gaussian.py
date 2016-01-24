#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        gaussian.py

    DESCRIPTION
        generates set of normally distribed data from specified distribution

    INPUT (COMMAND LINE ENTRY)
    OUTPUT
        x 

    SYNTAX
        gaussian.py [command line options]

    OPTIONS
        -h prints help message and quits
        -s specify standard deviation as next argument, default is 1
        -n specify N as next argument, default is 100
        -m specify mean as next argument, default is 0
        -F specify output file

    """
    N,mean,sigma=100,0,1.
    outfile=""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    else:
        if '-s' in sys.argv:
            ind=sys.argv.index('-s')
            sigma=float(sys.argv[ind+1])
        if '-n' in sys.argv:
            ind=sys.argv.index('-n')
            N=int(sys.argv[ind+1])
        if '-m' in sys.argv:
            ind=sys.argv.index('-m')
            mean=float(sys.argv[ind+1])
        if '-F' in sys.argv:
            ind=sys.argv.index('-F')
            outfile=sys.argv[ind+1]
            out=open(outfile,'w')
    for k in range(N): 
        x='%f'%(pmag.gaussdev(mean,sigma))  # send kappa to fshdev
        if outfile=="":
            print x
        else:
           out.write(x+'\n')

if __name__ == "__main__":
    main()
