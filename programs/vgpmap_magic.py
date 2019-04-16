#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

from pmagpy import pmag
from pmagpy import ipmag



def main():
    """
    NAME
        vgpmap_magic.py

    DESCRIPTION
        makes a map of vgps and a95/dp,dm for site means in a sites table

    SYNTAX
        vgpmap_magic.py [command line options]

    OPTIONS
        -h prints help and quits
        -eye  ELAT ELON [specify eyeball location], default is 90., 0.
        -f FILE sites format file, [default is sites.txt]
        -res [c,l,i,h] specify resolution (crude, low, intermediate, high]
        -etp plot the etopo20 topographpy data (requires high resolution data set)
        -prj PROJ,  specify one of the following:
             ortho = orthographic
             lcc = lambert conformal
             moll = molweide
             merc = mercator
        -sym SYM SIZE: choose a symbol and size, examples:
            ro 5 : small red circles
            bs 10 : intermediate blue squares
            g^ 20 : large green triangles
        -ell  plot dp/dm or a95 ellipses
        -rev RSYM RSIZE : flip reverse poles to normal antipode
        -S:  plot antipodes of all poles
        -age : plot the ages next to the poles
        -crd [g,t] : choose coordinate system, default is to plot all site VGPs
        -fmt [pdf, png, eps...] specify output format, default is pdf
        -sav  save and quit
    DEFAULTS
        FILE: sites.txt
        res:  c
        prj: ortho
        ELAT,ELON = 0,0
        SYM SIZE: ro 8
        RSYM RSIZE: g^ 8

    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", ".")
    # plot: default is 0, if -sav in sys.argv should be 1
    interactive = True
    save_plots = pmag.get_flag_arg_from_sys("-sav", true=1, false=0)
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
        flip = 1
        ind = sys.argv.index('-rev')
        rsym = (sys.argv[ind + 1])
        rsize = int(sys.argv[ind + 2])
    else:
        flip, rsym, rsize = 0, "g^", 8
    if '-sym' in sys.argv:
        ind = sys.argv.index('-sym')
        sym = (sys.argv[ind + 1])
        size = int(sys.argv[ind + 2])
    else:
        sym, size = 'ro', 8
    if '-eye' in sys.argv:
        ind = sys.argv.index('-eye')
        lat_0 = float(sys.argv[ind + 1])
        lon_0 = float(sys.argv[ind + 2])
    else:
        lat_0, lon_0 = 90., 0.
    crd = pmag.get_named_arg("-crd", "")
    results_file = pmag.get_named_arg("-f", "sites.txt")
    ipmag.vgpmap_magic(dir_path, results_file, crd, sym, size, rsym, rsize,
                       fmt, res, proj, flip, anti, fancy, ell, ages, lat_0, lon_0,
                       save_plots, interactive)



if __name__ == "__main__":
    main()
