#!/usr/bin/env python
from . import pmag
import sys


def spitout(line):
    dat = []  # initialize list for  dec,inc,slat,slon
    line.replace('\t', ' ')
    rec = line.split()  # split each line on space to get records
    for element in rec:  # step through dec,inc, int
        # append floating point variable to dat list
        dat.append(float(element))
    # call vgp_di function from pmag module
    dec, inc = pmag.vgp_di(dat[0], dat[1], dat[2], dat[3])
    print '%7.1f %7.1f' % (dec, inc)  # print out returned stuff
    return dec, inc


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
        print main.__doc__
        sys.exit()
    if '-i' in sys.argv:  # if one is -i
        while True:
            try:
                ans = raw_input(
                    "Input Pole Latitude [positive north]: <cntrl-D to quit>  ")
                # assign input to plat, after conversion to floating point
                plat = float(ans)
                ans = raw_input("Input Pole Longitude [positive east]:  ")
                plon = float(ans)
                ans = raw_input("Input Site Latitude:  ")
                slat = float(ans)
                ans = raw_input("Input Site Longitude:  ")
                slong = float(ans)
                # call vgp_di function from pmag module
                dec, inc = pmag.vgp_di(plat, plon, slat, slong)
                print '%7.1f %7.1f' % (dec, inc)  # print out returned stuff
            except EOFError:
                print "\n Good-bye\n"
                sys.exit()

    elif '-f' in sys.argv:  # manual input of file name
        ind = sys.argv.index('-f')
        file = sys.argv[ind + 1]
        f = open(file, 'rU')
        input = f.readlines()  # read from standard input
        # read in the data (as string variable), line by line
        for line in input:
            dec, inc = spitout(line)
    else:
        input = sys.stdin.readlines()  # read from standard input
        # read in the data (as string variable), line by line
        for line in input:
            spitout(line)
main()
