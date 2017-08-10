#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import random
import pmagpy.pmag as pmag


def main():
    """
    NAME
        tk03.py

    DESCRIPTION
        generates set of vectors drawn from TK03.gad at given lat and
        rotated about vertical axis by given Dec

    INPUT (COMMAND LINE ENTRY)
    OUTPUT
        dec,  inc, int

    SYNTAX
        tk03.py [command line options] [> OutputFileName]

    OPTIONS
        -n N specify N, default is 100
        -d D specify mean Dec, default is 0
        -lat LAT specify latitude, default is 0
        -rev include reversals
        -t INT  truncates  intensities to >INT uT
        -G2 FRAC  specify average g_2^0 fraction (default is 0)
        -G3 FRAC  specify average g_3^0 fraction (default is 0)
    """
    N, L, D, R = 100, 0., 0., 0
    G2, G3 = 0., 0.
    cnt = 1
    Imax = 0
    if len(sys.argv) != 0 and '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    else:
        if '-n' in sys.argv:
            ind = sys.argv.index('-n')
            N = int(sys.argv[ind + 1])
        if '-d' in sys.argv:
            ind = sys.argv.index('-d')
            D = float(sys.argv[ind + 1])
        if '-lat' in sys.argv:
            ind = sys.argv.index('-lat')
            L = float(sys.argv[ind + 1])
        if '-t' in sys.argv:
            ind = sys.argv.index('-t')
            Imax = 1e3 * float(sys.argv[ind + 1])
        if '-rev' in sys.argv:
            R = 1
        if '-G2' in sys.argv:
            ind = sys.argv.index('-G2')
            G2 = float(sys.argv[ind + 1])
        if '-G3' in sys.argv:
            ind = sys.argv.index('-G3')
            G3 = float(sys.argv[ind + 1])
    for k in range(N):
        gh = pmag.mktk03(8, k, G2, G3)  # terms and random seed
        # get a random longitude, between 0 and 359
        lon = random.randint(0, 360)
        vec = pmag.getvec(gh, L, lon)  # send field model and lat to getvec
        if vec[2] >= Imax:
            vec[0] += D
            if k % 2 == 0 and R == 1:
                vec[0] += 180.
                vec[1] = -vec[1]
            if vec[0] >= 360.:
                vec[0] -= 360.
            print('%7.1f %7.1f %8.2f ' % (vec[0], vec[1], vec[2]))


if __name__ == "__main__":
    main()
