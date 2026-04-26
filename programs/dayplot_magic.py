#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import pmag
from pmagpy import rockmag
import pandas as pd


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
    if '-sav' in sys.argv:
        save_plots = True
    infile = pmag.get_named_arg("-f", "specimens.txt")
    infile_path = os.path.join(dir_path, infile)
    if not os.path.isfile(infile_path):
        print(f"Specimens file not found: {infile_path}")
        sys.exit(1)
    # Read specimens table
    df = pd.read_csv(infile_path, sep='\t', skiprows=1)
    # Plot Day plot using rockmag
    fig, ax = rockmag.plot_day_plot_MagIC(df, show_plot=not save_plots, return_figure=True)
    if save_plots and fig is not None:
        outname = os.path.splitext(os.path.basename(infile))[0] + f"_dayplot.{fmt}"
        fig.savefig(outname, format=fmt)
        print(f"Saved plot to {outname}")


if __name__ == "__main__":
    main()
