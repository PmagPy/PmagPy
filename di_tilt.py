#!/usr/bin/env python
import pmag,sys,exceptions
def spitout(line):
    rec=line.split()  # split each line on the spaces
    Dec=float(rec[0]) # assign first column to dec - convert to floating point
    Inc=float(rec[1]) # 2nd column => inc
    Dip_dir=float(rec[2])  # 3rd column => azimuth
    Dip=float(rec[3]) # 4th column => plunge
    dec,inc=pmag.dotilt(Dec,Inc,Dip_dir,Dip) # call dogeo from pmag module
    print '%7.1f %7.1f '%(dec,inc)
    return dec,inc
def main():
    """
    NAME
       di_tilt.py

    DESCRIPTION
       rotates geographic coordinate dec, inc data to stratigraphic
       coordinates using the dip and dip direction (strike+90, dip if dip to right of strike)

    INPUT FORMAT
        declination inclination dip_direction  dip

    SYNTAX
       di_tilt.py [-h][-i][-f FILE] [< filename ]

    OPTIONS
        -h prints help message and quits
        -i for interactive data entry
        -f FILE command line entry of file name
         otherwise put data in input format in space delimited file


    OUTPUT:
        declination inclination
 """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-i' in sys.argv: # interactive flag
        while 1:
            try:
                Dec=float(raw_input("Declination: <cntl-D> to quit "))
            except:
                print "\n Good-bye\n"
                sys.exit()
            Inc=float(raw_input("Inclination: "))
            Dip_dir=float(raw_input("Dip direction: "))
            Dip=float(raw_input("Dip: "))
            print '%7.1f %7.1f'%(pmag.dotilt(Dec,Inc,Dip_dir,Dip))
    elif '-f' in sys.argv:
        ind=sys.argv.index('-f')
        file=sys.argv[ind+1]
        f=open(file,'rU')
        data=f.readlines()
    else:
        data=sys.stdin.readlines() # read in the data from the datafile
    for line in data: # step through line by line
        dec,inc=spitout(line)
main()
