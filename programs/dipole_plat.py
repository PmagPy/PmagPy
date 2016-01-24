#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME 
        dipole_plat.py

    DESCRIPTION	
        gives paleolatitude from given inclination, assuming GAD field

    SYNTAX
        dipole_plat.py [command line options]<filename

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of latitude
        -f file, specifies file name on command line
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    elif '-f' in sys.argv:
       ind=sys.argv.index('-f')
       file=sys.argv[ind+1]
       f=open(file,'rU')
       data=f.readlines()
    elif '-i' not in sys.argv:
       data=sys.stdin.readlines()
    if '-i' not in sys.argv:
        for line in data:
            rec=line.split()
            print '%7.1f'%(pmag.plat(float(rec[0])))
    else: 
       while 1:
           try:
               inc=raw_input("Inclination for converting to paleolatitude: <cntl-D> to quit ")
               print '%7.1f'%(pmag.plat(float(inc)))
           except:
               print '\n Good-bye \n'
               sys.exit()

if __name__ == "__main__":
    main()
