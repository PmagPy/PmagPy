#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-
# define some variables

import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

from pmagpy import pmag
from pmagpy import ipmag


def main():
    """
    NAME
        polemap_magic.py

    DESCRIPTION
        makes a map of paleomagnetic poles and a95/dp,dm for pole  in a locations table

    SYNTAX
        polemap_magic.py [command line options]

    OPTIONS
        -h prints help and quits
        -eye  ELAT ELON [specify eyeball location], default is 90., 0.
        -f FILE location format file, [default is locations.txt]
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -etp plot the etopo20 topographpy data (requires high resolution data set)
        -prj PROJ,  specify one of the following:
             ortho = orthographic
             lcc = lambert conformal
             moll = molweide
             merc = mercator
        -sym SYM SIZE: choose a symbol and size, examples:
            ro 20 : small red circles
            bs 30 : intermediate blue squares
            g^ 40 : large green triangles
        -ell  plot dp/dm or a95 ellipses
        -rev RSYM RSIZE : flip reverse poles to normal antipode
        -S:  plot antipodes of all poles
        -age : plot the ages next to the poles
        -crd [g,t] : choose coordinate system, default is to prioritize tilt-corrected
        -fmt [pdf, png, eps...] specify output format, default is pdf
        -sav  save and quit
    DEFAULTS
        FILE: locations.txt
        res:  c
        prj: ortho
        ELAT,ELON = 0,0
        SYM SIZE: ro 40
        RSYM RSIZE: g^ 40

    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", ".")
    # do_plot: default is 0, if -sav in sys.argv should be 1
    save_plots = pmag.get_flag_arg_from_sys("-sav", true=1, false=0)
    interactive = True
    if save_plots:
        interactive = False
    fmt = pmag.get_named_arg("-fmt", "pdf")
    res = pmag.get_named_arg("-res", "c")
    proj = pmag.get_named_arg("-prj", "ortho")
    anti = pmag.get_flag_arg_from_sys("-S", true=1, false=0)
    fancy = pmag.get_flag_arg_from_sys("-etp", true=1, false=0)
    ell = pmag.get_flag_arg_from_sys("-ell", true=1, false=0)
    ages = pmag.get_flag_arg_from_sys("-age", true=1, false=0)
    if '-rev' in sys.argv:
        flip = True
        ind = sys.argv.index('-rev')
        try:
            rsym = (sys.argv[ind + 1])
            rsize = int(sys.argv[ind + 2])
        except (IndexError, ValueError, KeyError):
            flip, rsym, rsize = True, "g^", 40
    else:
        flip, rsym, rsize = False, "g^", 40
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym = (sys.argv[ind + 1])
        size = int(sys.argv[ind + 2])
    else:
        sym, size = 'ro', 40
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0 = float(sys.argv[ind + 1])
        lon_0 = float(sys.argv[ind + 2])
    else:
        lat_0, lon_0 = 90., 0.
    crd = pmag.get_named_arg("-crd", "")
    loc_file = pmag.get_named_arg("-f", "locations.txt")
    ipmag.polemap_magic(loc_file, dir_path, interactive, crd,
                        sym, size, rsym, rsize, fmt, res,
                        proj, flip, anti, fancy, ell, ages, lat_0, lon_0,
                        save_plots)


if __name__ == "__main__":
    main()
