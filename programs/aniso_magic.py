#!/usr/bin/env python
#  -*- python-indent-offset: 4; -*-
#pylint: disable=invalid-name,wrong-import-position,line-too-long
#import draw
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
from pmagpy import ipmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.contribution_builder as cb


def old():
    """
    NAME
        aniso_magic.py

    DESCRIPTION
        plots anisotropy data with either bootstrap or hext ellipses

    SYNTAX
        aniso_magic.py [-h] [command line options]
    OPTIONS
        -h plots help message and quits
        -usr USER: set the user name
        -f AFILE, specify specimens.txt formatted file for input
        -fsa SAMPFILE, specify samples.txt file (required to plot by site)
        -fsi SITEFILE, specify site file (required to include location information)
        -x Hext [1963] and bootstrap
        -B DON'T do bootstrap, do Hext
        -par Tauxe [1998] parametric bootstrap
        -v plot bootstrap eigenvectors instead of ellipses
        -sit plot by site instead of entire file
        -crd [s,g,t] coordinate system, default is specimen (g=geographic, t=tilt corrected)
        -P don't make any plots - just fill in the specimens, samples, sites tables
        -sav don't make the tables - just save all the plots
        -fmt [svg, jpg, eps] format for output images, png default
        -gtc DEC INC  dec,inc of pole to great circle [down(up) in green (cyan)
        -d Vi DEC INC; Vi (1,2,3) to compare to direction DEC INC
        -n N; specifies the number of bootstraps - default is 1000
    DEFAULTS
       AFILE:  specimens.txt
       plot bootstrap ellipses of Constable & Tauxe [1987]
    NOTES
       minor axis: circles
       major axis: triangles
       principal axis: squares
       directions are plotted on the lower hemisphere
       for bootstrapped eigenvector components: Xs: blue, Ys: red, Zs: black
"""
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    verbose = pmagplotlib.verbose
    dir_path = pmag.get_named_arg("-WD", ".")
    input_dir_path = pmag.get_named_arg("-ID", "")
    num_bootstraps = pmag.get_named_arg("-n", 1000)
    ipar = pmag.get_flag_arg_from_sys("-par", true=1, false=0)
    ihext = pmag.get_flag_arg_from_sys("-x", true=1, false=0)
    ivec = pmag.get_flag_arg_from_sys("-v", true=1, false=0)
    iplot = pmag.get_flag_arg_from_sys("-P", true=0, false=1)
    isite = pmag.get_flag_arg_from_sys("-sit", true=1, false=0)
    iboot, vec = 1, 0
    infile = pmag.get_named_arg('-f', 'specimens.txt')
    samp_file = pmag.get_named_arg('-fsa', 'samples.txt')
    site_file = pmag.get_named_arg('-fsi', 'sites.txt')
    #outfile = pmag.get_named_arg("-F", "rmag_results.txt")
    fmt = pmag.get_named_arg("-fmt", "png")
    crd = pmag.get_named_arg("-crd", "s")
    comp, Dir, PDir = 0, [], []
    user = pmag.get_named_arg("-usr", "")
    if '-B' in args:
        iboot, ihext = 0, 1
    plots, verbose = 0, True
    if '-sav' in args:
        plots = 1
        verbose = 0
    if '-gtc' in args:
        ind = args.index('-gtc')
        d, i = float(args[ind+1]), float(args[ind+2])
        PDir.append(d)
        PDir.append(i)
    if '-d' in args:
        comp = 1
        ind = args.index('-d')
        vec = int(args[ind+1])-1
        Dir = [float(args[ind+2]), float(args[ind+3])]

    ipmag.aniso_magic_old(infile=infile, samp_file=samp_file, site_file=site_file,
                      ipar=ipar, ihext=ihext, ivec=ivec, iplot=iplot, isite=isite, iboot=iboot, vec=vec,
                      Dir=Dir, PDir=PDir, comp=comp, user=user,
                      fmt=fmt, crd=crd, verbose=verbose, plots=plots,
                      num_bootstraps=num_bootstraps, dir_path=dir_path,
                      input_dir_path=input_dir_path)

def main():
    """
    NAME
        aniso_magic.py

    DESCRIPTION
        plots anisotropy data with either bootstrap or hext ellipses

    SYNTAX
        aniso_magic.py [-h] [command line options]
    OPTIONS
        -h plots help message and quits
        -f AFILE, specify specimens.txt formatted file for input
        -fsa SAMPFILE, specify samples.txt file (required to plot by site)
        -fsi SITEFILE, specify site file (required to include location information)
        -x Hext [1963] and bootstrap
        -B DON'T do bootstrap, do Hext
        -par Tauxe [1998] parametric bootstrap
        -v plot bootstrap eigenvectors instead of ellipses
        -sit plot by site instead of entire file
        -crd [s,g,t] coordinate system, default is specimen (g=geographic, t=tilt corrected)
        -P don't make any plots - just fill in the specimens, samples, sites tables
        -sav don't make the tables - just save all the plots
        -fmt [svg, jpg, eps] format for output images, png default
        -gtc DEC INC  dec,inc of pole to great circle [down(up) in green (cyan)
        -d Vi DEC INC; Vi (1,2,3) to compare to direction DEC INC
        -n N; specifies the number of bootstraps - default is 1000
    DEFAULTS
       AFILE:  specimens.txt
       plot bootstrap ellipses of Constable & Tauxe [1987]
    NOTES
       minor axis: circles
       major axis: triangles
       principal axis: squares
       directions are plotted on the lower hemisphere
       for bootstrapped eigenvector components: Xs: blue, Ys: red, Zs: black
"""

    args = sys.argv
    if '-h' in args:
        print(main.__doc__)
        return
    dir_path = pmag.get_named_arg("-WD", ".")
    if '-ID' in args and dir_path == '.':
        dir_path = pmag.get_named_arg("-ID", ".")
    iboot, vec = 1, 0
    num_bootstraps = pmag.get_named_arg("-n", 1000)
    ipar = pmag.get_flag_arg_from_sys("-par", true=1, false=0)
    ihext = pmag.get_flag_arg_from_sys("-x", true=1, false=0)
    ivec = pmag.get_flag_arg_from_sys("-v", true=1, false=0)
    if ivec:
        vec = 3
    #iplot = pmag.get_flag_arg_from_sys("-P", true=0, false=1)
    isite = pmag.get_flag_arg_from_sys("-sit", true=1, false=0)
    infile = pmag.get_named_arg('-f', 'specimens.txt')
    samp_file = pmag.get_named_arg('-fsa', 'samples.txt')
    site_file = pmag.get_named_arg('-fsi', 'sites.txt')
    #outfile = pmag.get_named_arg("-F", "rmag_results.txt")
    fmt = pmag.get_named_arg("-fmt", "png")
    crd = pmag.get_named_arg("-crd", "s")
    comp, Dir, PDir = 0, [], []
    user = pmag.get_named_arg("-usr", "")
    if '-B' in args:
        iboot, ihext = 0, 1
    save_plots, verbose, interactive = False, True, True
    if '-sav' in args:
        save_plots = True
        verbose = False
        interactive = False
    if '-gtc' in args:
        ind = args.index('-gtc')
        d, i = float(args[ind+1]), float(args[ind+2])
        PDir.append(d)
        PDir.append(i)
    if '-d' in args:
        comp = 1
        ind = args.index('-d')
        vec = int(args[ind+1])-1
        Dir = [float(args[ind+2]), float(args[ind+3])]
    ipmag.aniso_magic_nb(infile, samp_file, site_file, verbose,
                         ipar, ihext, ivec, isite, False, iboot,
                         vec, Dir, PDir, crd, num_bootstraps,
                         dir_path, save_plots=save_plots, interactive=interactive,
                         fmt=fmt)




if __name__ == "__main__":
    if "-old" in sys.argv:
        old()
    else:
        main()
