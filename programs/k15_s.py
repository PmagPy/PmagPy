#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        k15_s.py
    
    DESCRIPTION
        converts .k15 format data to .s format.
          assumes Jelinek Kappabridge measurement scheme

    SYNTAX
        k15_s.py  [-h][-i][command line options][<filename]

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of options
        -f FILE, specifies input file, default: standard input
        -F FILE, specifies output file, default: standard output
        -crd [g, t] specifies [g]eographic rotation, 
           or geographic AND tectonic rotation
    
    INPUT
        name [az,pl,strike,dip], followed by
        3 rows of 5 measurements for each specimen
 
    OUTPUT
        least squares matrix elements and sigma:
        x11,x22,x33,x12,x23,x13,sigma
    """
    firstline,itilt,igeo,linecnt,key=1,0,0,0,""
    out=""
    data,k15=[],[]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv:
        file=input("Input file name [.k15 format]: ")
        f=open(file,'r')
        data=f.readlines()
        f.close()
        file=input("Output file name [.s format]: ")
        out=open(file,'w')
        print (" [g]eographic, [t]ilt corrected, ")
        tg=input(" [return for specimen coordinates]: ")  
        if tg=='g': 
            igeo=1
        elif tg=='t':
            igeo,itilt=1,1
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
        data=f.readlines()
        f.close()
    else:
        data= sys.stdin.readlines()
    if len(data)==0:
        print(main.__doc__)
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        file=sys.argv[ind+1]
        out=open(file,'w')
    if '-crd' in sys.argv:
        ind=sys.argv.index('-crd')
        tg=sys.argv[ind+1] 
        if tg=='g':igeo=1
        if tg=='t': igeo,itilt=1,1
    for line in data:
        rec=line.split()
        if firstline==1:
            firstline=0
            nam=rec[0]
            if igeo==1: az,pl=float(rec[1]),float(rec[2])
            if itilt==1: bed_az,bed_dip=90.+float(rec[3]),float(rec[4])
        else: 
            linecnt+=1
            for i in range(5):
                k15.append(float(rec[i]))
            if linecnt==3:
                sbar,sigma,bulk=pmag.dok15_s(k15) 
                if igeo==1: sbar=pmag.dosgeo(sbar,az,pl) 
                if itilt==1: sbar=pmag.dostilt(sbar,bed_az,bed_dip) 
                outstring=""
                for s in sbar:outstring+='%10.8f '%(s)
                outstring+='%10.8f'%(sigma)
                if out=="":
                    print(outstring)
                else:
                    out.write(outstring+'\n')
                linecnt,firstline,k15=0,1,[]
#
if __name__ == "__main__":
    main()
