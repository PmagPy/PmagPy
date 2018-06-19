#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from past.utils import old_div
import sys
import math
import pmagpy.pmag as pmag

def main():
    """
    NAME
        eq_di.py
    
    DESCRIPTION
      converts x,y pairs digitized from equal area projection to dec inc data
    
    SYNTAX
        eq_di.py [command line options] [< filename]
    
    OPTIONS
        -f FILE, input file
        -F FILE, specifies output file name 
        -up if data are upper hemisphere
    """
    out=""
    UP=0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        dat=[]
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]  
        f=open(file,'r')
        input=f.readlines()
    else:
        input = sys.stdin.readlines()  # read from standard input
    # NEW
    ofile = ""
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
        out=open(ofile, 'w + a')
    # end NEW
    if '-up' in sys.argv: UP=1
    for line in input:
        rec=line.split()
        x,y=float(rec[1]),float(rec[0])  # swap x,y cartesian for x,y geographic
        #d,i=pmag.doeqdi(x,y)
        r=math.sqrt(x**2+y**2)
        z=1.-r**2
        t=math.asin(z)
        if UP==1:t=-t
        if x==0.:
            if y<0:
                p=3.*math.pi/2.
            else:
                p=old_div(math.pi,2.)
        else:
            p=math.atan2(y,x)
        d,i=p*180./math.pi,t*180./math.pi
        if d<0:d+=360.
        # new
        outstring = '%7.1f %7.1f'%(d,i)
        if ofile == "":
           # print '%7.1f %7.1f'%(d,i)
            print(outstring)
        else:
            out.write(outstring+'\n')
        #end
if __name__ == "__main__":
    main()
