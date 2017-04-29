#!/usr/bin/env python
#
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        s_eigs.py

    DESCRIPTION 
        converts .s format data to eigenparameters.
 
    SYNTAX
        s_eigs.py [-h][options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of file name
        -f FILE specifies filename on command line
        -F FILE specifies output file
        < filename, reads from standard input (Unix like operating systems only) 

    INPUT
        x11,x22,x33,x12,x23,x13
  
    OUTPUT
        tau_i, dec_i inc_i of eigenvectors 
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    elif '-i' in sys.argv:
        file=input("Enter filename for processing: ")
        f=open(file,'r')
        data=f.readlines()
        f.close()
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1] 
        f=open(file,'r')
        data=f.readlines()
        f.close()
    else: 
        data=sys.stdin.readlines()
    ofile = ""
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
        out=open(ofile, "w + a")
    for line in data:
        s=[]
        rec=line.split()
        for i in range(6):
            s.append(float(rec[i]))
        tau,Vdirs=pmag.doseigs(s)
        outstring='%10.8f %6.2f %6.2f %10.8f %6.2f %6.2f %10.8f %6.2f %6.2f'%(tau[2],Vdirs[2][0],Vdirs[2][1],tau[1],Vdirs[1][0],Vdirs[1][1],tau[0],Vdirs[0][0],Vdirs[0][1])
        if ofile == "":
            print(outstring)
        else:
            out.write(outstring+'\n')
#
if __name__ == "__main__":
    main() 

