#!/usr/bin/env python
from __future__ import print_function
from builtins import input
import sys
import pmagpy.pmag as pmag

def spitout(line):
    dat=[]  # initialize list for  dec,inc,slat,slon
    line.replace('\t',' ')
    rec=line.split() # split each line on space to get records
    for element in rec : # step through dec,inc, int
        dat.append(float(element)) # append floating point variable to dat list
    dec,inc=pmag.vgp_di(dat[0],dat[1],dat[2],dat[3])  # call vgp_di function from pmag module
    print('%7.1f %7.1f'%(dec,inc)) # print out returned stuff
    return dec,inc

def main():
    """
    NAME
        vgp_di.py
    DESCRIPTION
      converts site latitude, longitude and pole latitude, longitude to declination, inclination
    
    SYNTAX
        vgp_di.py [-h] [-i] [-f FILE] [< filename]
    
    OPTIONS
        -h prints help message and quits
        -i interactive data entry
        -f FILE to specify file name on the command line
    
    INPUT 
      for file entry:
        PLAT PLON  SLAT SLON    
      where:
         PLAT: pole latitude 
         PLON: pole longitude (positive east)
         SLAT: site latitude (positive north)
         SLON: site longitude (positive east)
               
    OUTPUT
        D I
        where:
           D: declination
           I: inclination
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv: # if one is -i
        while 1:
            try:
                ans=input("Input Pole Latitude [positive north]: <cntrl-D to quit>  ")
                plat=float(ans)  # assign input to plat, after conversion to floating point
                ans=input("Input Pole Longitude [positive east]:  ")
                plon =float(ans)
                ans=input("Input Site Latitude:  ")
                slat =float(ans)
                ans=input("Input Site Longitude:  ")
                slong =float(ans)
                dec,inc=pmag.vgp_di(plat,plon,slat,slong)  # call vgp_di function from pmag module
                print('%7.1f %7.1f'%(dec,inc)) # print out returned stuff
            except EOFError:
                print("\n Good-bye\n")
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'r')
        input = f.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            dec,inc= spitout(line)
    else:
        input = sys.stdin.readlines()  # read from standard input
        for line in input:   # read in the data (as string variable), line by line
            spitout(line)

if __name__ == "__main__":
    main()
