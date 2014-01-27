#!/usr/bin/env python
from . import pmag
import sys
import exceptions
import numpy


def main():
    """
    NAME
        cart_dir.py

    DESCRIPTION
      converts artesian coordinates to geomangetic elements

    INPUT (COMMAND LINE ENTRY)
           x1 x2  x3
        if only two columns, assumes magnitude of unity
    OUTPUT
           declination inclination magnitude

    SYNTAX
        cart_dir.py [command line options] [< filename]

    OPTIONS
        -h prints help message and quits
        -i for interactive data entry
        -f FILE to specify input filename
        -F OFILE to specify output filename (also prints to screen)

    """
    ofile = ""
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        ofile = sys.argv[ind + 1]
        outfile = open(ofile, 'w')
    if '-i' in sys.argv:
        cont = 1
        while cont == 1:
            cart = []
            try:
                ans = raw_input('X: [ctrl-D  to quit] ')
                cart.append(float(ans))
                ans = raw_input('Y: ')
                cart.append(float(ans))
                ans = raw_input('Z: ')
                cart.append(float(ans))
            except:
                print "\n Good-bye \n"
                sys.exit()
            # send dir to dir2cart and spit out result
            dir = pmag.cart2dir(cart)
            print '%7.1f %7.1f %10.3e' % (dir[0], dir[1], dir[2])
    elif '-f' in sys.argv:
        ind = sys.argv.index('-f')
        file = sys.argv[ind + 1]
        input = numpy.loadtxt(file)  # read from a file
    else:
        # read from standard input
        input = numpy.loadtxt(sys.stdin, dtype=numpy.float)
    dir = pmag.cart2dir(input)
    for line in dir:
        print '%7.1f %7.1f %10.3e' % (line[0], line[1], line[2])
        if ofile != "":
            outstring = '%7.1f %7.1f %10.8e\n' % (line[0], line[1], line[2])
            outfile.write(outstring)
main()
