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
        dayplot_magic.py

    DESCRIPTION
        makes 'day plots' (Day et al. 1977) and squareness/coercivity,
        plots 'linear mixing' curve from Dunlop and Carter-Stiglitz (2006).
          squareness coercivity of remanence (Neel, 1955) plots after
          Tauxe et al. (2002)

    SYNTAX
        dayplot_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input hysteresis file, default is specimens.txt
        -fmt [svg,png,jpg] format for output plots, default svg
        -sav saves plots and quits quietly
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg('-WD', '.')
    fmt = pmag.get_named_arg('-fmt', 'svg')
    save_plots = False
    interactive = True
    if '-sav' in sys.argv:
        save_plots = True
        interactive = False
    infile = pmag.get_named_arg("-f", "specimens.txt")
    ipmag.dayplot_magic(dir_path, infile, save=save_plots,
                        fmt=fmt, interactive=interactive)



if __name__ == "__main__":
    main()
