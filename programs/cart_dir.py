#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import numpy
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        cart_dir.py
    
    DESCRIPTION
      converts cartesian coordinates to geomagnetic elements
    
    INPUT (COMMAND LINE ENTRY) 
           x1 x2  x3
        if only two columns, assumes magnitude of unity
    OUTPUT
           declination inclination magnitude
    
    SYNTAX
        cart_dir.py [command line options] [< filename]
    
    OPTIONS 
        -h prints help message and quits
        -i for interactive data entry
        -f FILE to specify input filename
        -F OFILE to specify output filename (also prints to screen)
    
    """
    ofile=""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
        outfile=open(ofile,'w')
    if '-i' in sys.argv:
        cont=1
        while cont==1:
            cart=[]
            try:
                ans=input('X: [ctrl-D  to quit] ')
                cart.append(float(ans))
                ans=input('Y: ')
                cart.append(float(ans))
                ans=input('Z: ')
                cart.append(float(ans))
            except:
                print("\n Good-bye \n")
                sys.exit()
            dir= pmag.cart2dir(cart)  # send dir to dir2cart and spit out result
            print('%7.1f %7.1f %10.3e'%(dir[0],dir[1],dir[2]))
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        inp=numpy.loadtxt(file) # read from a file
    else:
        inp = numpy.loadtxt(sys.stdin,dtype=numpy.float)  # read from standard input
    dir=pmag.cart2dir(inp)
    if len(dir.shape)==1:
        line=dir 
        print('%7.1f %7.1f %10.3e'%(line[0],line[1],line[2]))
        if ofile!="":
           outstring='%7.1f %7.1f %10.8e\n' %(line[0],line[1],line[2]) 
           outfile.write(outstring)
    else: 
        for line in dir:
            print('%7.1f %7.1f %10.3e'%(line[0],line[1],line[2]))
            if ofile!="":
               outstring='%7.1f %7.1f %10.8e\n' %(line[0],line[1],line[2]) 
               outfile.write(outstring)

if __name__ == "__main__":
    main() 
