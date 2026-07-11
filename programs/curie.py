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
        -u [C,K]     Temperature units in input file [default: C]
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
    input_temp_unit = 'C'
    if '-u' in sys.argv:
        ind = sys.argv.index('-u')
        input_temp_unit = sys.argv[ind+1].upper()
        if input_temp_unit not in ('C', 'K'):
            print("-u must be 'C' or 'K'")
            sys.exit(1)
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
    T_input = data[:, 0]
    M = data[:, 1]

    # Normalize to Kelvin for rockmag.plot_ms_t, which assumes Kelvin input.
    if input_temp_unit == 'C':
        T_kelvin = T_input + 273.15
    else:
        T_kelvin = T_input
    df = pd.DataFrame({"meas_temp": T_kelvin, "magn_mass": M})

    # Restrict to temperature range in the same units as input, then convert to Kelvin.
    if t_begin is not None and t_end is not None:
        if input_temp_unit == 'C':
            t_begin_k = t_begin + 273.15
            t_end_k = t_end + 273.15
        else:
            t_begin_k = t_begin
            t_end_k = t_end
        df = df[(df["meas_temp"] >= t_begin_k) & (df["meas_temp"] <= t_end_k)]

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
