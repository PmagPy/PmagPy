#!/usr/bin/env python

from __future__ import print_function
from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

def spitout(line):
    print (line)
    if len(line) > 1:
        (dec,inc,a95,slat,slon) = (line)
        output = pmag.dia_vgp(dec,inc,a95,slat,slon)
    else:
        line = line[0]
        output = pmag.dia_vgp(line)
    return output

def printout(output): # print out returned stuff
    if len(output) > 1:
        if isinstance(output[0],list):        
            for i in range(len(output[0])):
                print('%7.1f %7.1f %7.1f %7.1f'%(output[0][i],output[1][i],output[2][i],output[3][i]))
        else:
            print('%7.1f %7.1f %7.1f %7.1f'%(output[0],output[1],output[2],output[3]))     

def main():
    """
    NAME
        dia_vgp.py
    DESCRIPTION
      converts declination inclination alpha95 to virtual geomagnetic pole, dp and dm
    
    SYNTAX
        dia_vgp.py [-h] [-i] [-f FILE] [< filename]
    
    OPTIONS
        -h prints help message and quits
        -i interactive data entry
        -f FILE to specify file name on the command line
    
    INPUT 
      for file entry:
        D I A95 SLAT SLON      
      where:
         D: declination
         I: inclination
         A95: alpha_95
         SLAT: site latitude (positive north)
         SLON: site longitude (positive east)
               
    OUTPUT
        PLON PLAT DP DM
        where:
             PLAT: pole latitude 
             PLON: pole longitude (positive east)
             DP: 95% confidence angle in parallel 
             DM: 95% confidence angle in meridian 
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv: # if one is -i
        cont=1
        while cont==1:
            try:
                ans=input("Input Declination: <cntrl-D to quit>  ")
                Dec=float(ans)  # assign input to Dec, after conversion to floating point
                ans=input("Input Inclination:  ")
                Inc =float(ans)
                ans=input("Input Alpha 95:  ")
                a95 =float(ans)
                ans=input("Input Site Latitude:  ")
                slat =float(ans)
                ans=input("Input Site Longitude:  ")
                slon =float(ans)
                plong,plat,dp,dm = pmag.dia_vgp(Dec,Inc,a95,slat,slon)
                #plong,plat,dp,dm=spitout(Dec,Inc,a95,slat,slong)  # call dia_vgp function from pmag module
                print('%7.1f %7.1f %7.1f %7.1f'%(plong,plat,dp,dm)) # print out returned stuff
            except:
                print("\n Good-bye\n")
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
        inlist  = []
        for line in f.readlines():
            inlist.append([])
            # loop over the elements, split by whitespace
            for el in line.split():
                inlist[-1].append(float(el))
        spitout(inlist)

    else:
        lines = sys.stdin.readlines()  # read from standard input
        inlist  = []
        for line in lines:   # read in the data (as string variable), line by line
            inlist.append([])
            # loop over the elements, split by whitespace
            for el in line.split():
                inlist[-1].append(float(el))
        spitout(inlist)

if __name__ == "__main__":
    main()
