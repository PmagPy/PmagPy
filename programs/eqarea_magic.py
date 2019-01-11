#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
from pmagpy import ipmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.contribution_builder as cb



def main():
    """
    NAME
        eqarea_magic.py

    DESCRIPTION
       makes equal area projections from declination/inclination data

    SYNTAX
        eqarea_magic.py [command line options]

    INPUT
       takes magic formatted sites, samples, specimens, or measurements

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file from magic, default='sites.txt'
         supported types=[measurements, specimens, samples, sites]
        -fsp FILE: specify specimen file name, (required if you want to plot measurements by sample)
                default='specimens.txt'
        -fsa FILE: specify sample file name, (required if you want to plot specimens by site)
                default='samples.txt'
        -fsi FILE: specify site file name, default='sites.txt'
        -flo FILE: specify location file name, default='locations.txt'

        -obj OBJ: specify  level of plot  [all, sit, sam, spc], default is all
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is geographic, unspecified assumed geographic
        -fmt [svg,png,jpg] format for output plots
        -ell [F,K,B,Be,Bv] plot Fisher, Kent, Bingham, Bootstrap ellipses or Boostrap eigenvectors
        -c plot as colour contour
        -cm CM use color map CM [default is coolwarm]
        -sav save plot and quit quietly
        -no-tilt data are unoriented, allows plotting of measurement dec/inc
    NOTE
        all: entire file; sit: site; sam: sample; spc: specimen
    """
    # extract arguments from sys.argv
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", default_val=".")
    input_dir_path = pmag.get_named_arg('-ID', '')
    if not input_dir_path:
        input_dir_path = dir_path
    in_file = pmag.get_named_arg("-f", default_val="sites.txt")
    in_file = pmag.resolve_file_name(in_file, input_dir_path)
    if "-ID" not in sys.argv:
        input_dir_path = os.path.split(in_file)[0]

    plot_by = pmag.get_named_arg("-obj", default_val="all").lower()
    spec_file = pmag.get_named_arg("-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")
    loc_file = pmag.get_named_arg("-flo", default_val="locations.txt")
    ignore_tilt = False
    if '-no-tilt' in sys.argv:
        ignore_tilt = True
    color_map = "coolwarm"
    if '-c' in sys.argv:
        contour = True
        if '-cm' in sys.argv:
            ind = sys.argv.index('-cm')
            color_map = sys.argv[ind+1]
        else:
            color_map = 'coolwarm'
    else:
        contour = False
    interactive = True
    save_plots = False
    if '-sav' in sys.argv:
        save_plots = True
        interactive = False
    plot_ell = False
    if '-ell' in sys.argv:
        plot_ell = pmag.get_named_arg("-ell", "F")
    crd = pmag.get_named_arg("-crd", default_val="g")
    fmt = pmag.get_named_arg("-fmt", "svg")
    ipmag.eqarea_magic(in_file, dir_path, input_dir_path, spec_file, samp_file, site_file, loc_file,
                       plot_by, crd, ignore_tilt, save_plots, fmt, contour, color_map,
                       plot_ell, "all", interactive)



if __name__ == "__main__":
    main()
