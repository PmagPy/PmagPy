#!/usr/bin/env python
import sys
import os
import numpy as np
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import pandas as pd
from pmagpy import rockmag

def main():
    """
    NAME
        curie.py

    DESCRIPTION
        Plots and interprets Curie temperature data using pmagpy.rockmag functions.
        Uses plot_ms_t for plotting magnetization vs. temperature.

    SYNTAX
        curie.py [command line options]

    OPTIONS
        -h           Prints help message and quits
        -f FILE      Sets M,T input file (required, two columns: T, M)
        -t <min> <max>  Temperature range (optional, restricts plot to range)
        -sav         Save figure and quit
        -fmt [svg,jpg,eps,png,pdf]  Set format for figure output [default: svg]

    EXAMPLES
        curie.py -f ex2.1
        curie.py -f ex2.1 -t 300 700 -fmt png -sav
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        meas_file = sys.argv[ind+1]
    else:
        print("missing -f\n")
        sys.exit()
    t_begin = None
    t_end = None
    if '-t' in sys.argv:
        ind = sys.argv.index('-t')
        t_begin = float(sys.argv[ind+1])
        t_end = float(sys.argv[ind+2])
    save_plot = '-sav' in sys.argv
    fmt = 'svg'
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]

    # Read data (expects two columns: T, M)
    data = np.loadtxt(meas_file)
    T = data[:, 0]
    M = data[:, 1]
    df = pd.DataFrame({"meas_temp": T, "magn_mass": M})

    # Restrict to temperature range if requested (assume input is always Celsius)
    if t_begin is not None and t_end is not None:
        df = df[(df["meas_temp"] >= t_begin) & (df["meas_temp"] <= t_end)]

    # Plot using rockmag.plot_ms_t
    fig = rockmag.plot_ms_t(
        df,
        temperature_column="meas_temp",
        magnetization_column="magn_mass",
        temp_unit="C",
        interactive=False,
        return_figure=True,
        show_plot=not save_plot,
        size=(6, 4),
        legend_location="upper left"
    )

    # Save plot if requested
    if save_plot and fig is not None:
        fig_obj, ax = fig
        outname = os.path.splitext(os.path.basename(meas_file))[0] + f"_curie.{fmt}"
        fig_obj.savefig(outname, format=fmt)
        print(f"Saved plot to {outname}")

if __name__ == "__main__":
    main()
