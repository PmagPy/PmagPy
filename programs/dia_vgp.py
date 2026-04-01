#!/usr/bin/env python

from builtins import input
from builtins import range
import sys
import pmagpy.pmag as pmag

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
                print('%7.1f %7.1f %7.1f %7.1f'%(plong,plat,dp,dm)) # print out returned stuff
            except:
                print("\n Good-bye\n")
                sys.exit()
            
    elif '-f' in sys.argv: # manual input of file name
        ind = sys.argv.index('-f')
        file = sys.argv[ind + 1]
        with open(file, 'r') as f:
            for line in f:
                vals = [float(el) for el in line.split()]
                if len(vals) == 5:
                    plong, plat, dp, dm = pmag.dia_vgp(*vals)
                    print('%7.1f %7.1f %7.1f %7.1f' % (plong, plat, dp, dm))
    else:
        for line in sys.stdin:
            vals = [float(el) for el in line.split()]
            if len(vals) == 5:
                plong, plat, dp, dm = pmag.dia_vgp(*vals)
                print('%7.1f %7.1f %7.1f %7.1f' % (plong, plat, dp, dm))

if __name__ == "__main__":
    main()
