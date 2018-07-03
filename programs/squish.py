#!/usr/bin/env python
from __future__ import print_function
import sys
import numpy as np
import pmagpy.pmag as pmag
#
def main():
    """
    NAME
        squish.py
    
    DESCRIPTION
      takes dec/inc data and "squishes" with specified flattening factor, flt
      using formula tan(Io)=flt*tan(If)
    
    INPUT 
           declination inclination 
    OUTPUT
           "squished" declincation inclination
    
    SYNTAX
        squish.py [command line options] [< filename]
    
    OPTIONS
        -h print help and quit
        -f FILE, input file
        -F FILE, output file
        -flt FLT, flattening factor [required]
    
    """
    ofile=""
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]  
        out=open(ofile,'w')
    if '-flt' in sys.argv:
        ind=sys.argv.index('-flt')
        flt=float(sys.argv[ind+1])
    else:
        print(main.__doc__)
        sys.exit()  
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        input=np.loadtxt(file)
    else:
        input=np.loadtxt(sys.stdin,dtype=np.float)
# read in inclination data
    di=input.transpose()
    decs,incs=di[0],di[1]
    incnew=pmag.squish(incs,flt)
    for k in range(input.shape[0]):
        if ofile=="":
            print('%7.1f %7.1f'% (decs[k],incnew[k]))
        else:
            out.write('%7.1f %7.1f'% (decs[k],incnew[k])+'\n')
    
if __name__ == "__main__":
    main()

