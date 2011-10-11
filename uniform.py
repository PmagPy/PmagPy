#! /usr/bin/env python
import math,random,sys,pmag

def main():
    """
    NAME
        uniform.py

    DESCRIPTION
        draws N directions from uniform distribution on a sphere
    
    SYNTAX 
        uniform.py [-h][command line options]
        -h prints help message and quits
        -i interactive entry of N and output file
        -n N, specify N on the command line (default is 100)
        -F file, specify output file name, default is standard output
    """
    outf=""
    N=100
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-i' in sys.argv:
        N=int(raw_input("Desired number of uniform directions "))
        outf=raw_input("Output file for saving? ")
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outf=sys.argv[ind+1]
    if outf!="": out=open(outf,'w')
    if '-n' in sys.argv:
        ind=sys.argv.index('-n')
        N=int(sys.argv[ind+1])
    dirs=pmag.get_unf(N)
    for dir in dirs:
        if outf!="": 
            out.write('%7.1f %7.1f \n'%(dir[0],dir[1]))
        else: 
            print '%7.1f %7.1f'%(dir[0],dir[1])
main()
