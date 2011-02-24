#!/usr/bin/env python
import sys,math,pmag
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
        -f FILE, input file
    """
    out=""
    UP=0
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        f=open(file,'rU')
        input=f.readlines()
    else:
        input = sys.stdin.readlines()  # read from standard input
    for line in input:
        rec=line.split()
        d,i=float(rec[0]),float(rec[1]) 
        XY=pmag.dimap(d,i)
        print XY[0],XY[1] # 

main() 
