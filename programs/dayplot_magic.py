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
import matplotlib.pyplot as plt


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

    # Robust column detection for Day plot
    def detect_col(possible_names, columns):
        for name in possible_names:
            if name in columns:
                return name
        return None

    mr_names = ['hyst_mr_mass', 'hyst_mr_moment', 'hyst_mr_volume', 'rem_mr_mass', 'rem_mr_moment']
    ms_names = ['hyst_ms_mass', 'hyst_ms_moment', 'hyst_ms_volume', 'rem_ms_mass', 'rem_ms_moment']
    bcr_names = ['rem_bcr', 'hyst_bcr', 'rem_bcr_mass']
    bc_names = ['hyst_bc', 'rem_bc']

    mr_col = detect_col(mr_names, df.columns)
    ms_col = detect_col(ms_names, df.columns)
    bcr_col = detect_col(bcr_names, df.columns)
    bc_col = detect_col(bc_names, df.columns)

    missing = []
    if not mr_col:
        missing.append(f"Mr (tried: {mr_names})")
    if not ms_col:
        missing.append(f"Ms (tried: {ms_names})")
    if not bcr_col:
        missing.append(f"Bcr (tried: {bcr_names})")
    if not bc_col:
        missing.append(f"Bc (tried: {bc_names})")

    if missing:
        print("Error: Could not find required columns for Day plot:")
        for m in missing:
            print("  -", m)
        print("Available columns:", list(df.columns))
        sys.exit(1)

    # Plot 1: Day plot (Mr/Ms vs Bcr/Bc)
    fig1, ax1 = rockmag.plot_day_plot_MagIC(
        df,
        Mr=mr_col,
        Ms=ms_col,
        Bcr=bcr_col,
        Bc=bc_col,
        show_plot=not save_plots,
        return_figure=True
    )

    # Plot 2 & 3: Squareness vs Bc and vs Bcr
    summary = df.groupby('specimen').agg(
        {mr_col: 'mean', ms_col: 'mean', bcr_col: 'mean', bc_col: 'mean'}
    ).reset_index().dropna()
    Mr_Ms = summary[mr_col] / summary[ms_col]
    Bc = summary[bc_col]
    Bcr = summary[bcr_col]
    scatter_plots = [
        (Bc, Mr_Ms, 'dodgerblue', 'Bc', 'Squareness-Coercivity Plot', '_neelplot'),
        (Bcr, Mr_Ms, 'seagreen', 'Bcr', 'Squareness-Bcr Plot', '_bcrplot')
    ]
    figs = [fig1]
    for x, y, color, xlabel, title, suffix in scatter_plots:
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.scatter(x, y, color=color, marker='s', alpha=1)
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylim(0, 1.0)
        ax.set_ylabel('Mr/Ms', fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='black')
        figs.append(fig)
        fig._pmagplot_suffix = suffix  # attach suffix for saving

    # Save or show plots
    if save_plots:
        for i, fig in enumerate(figs):
            if fig is not None:
                suffix = getattr(fig, '_pmagplot_suffix', '_dayplot') if i > 0 else '_dayplot'
                outname = os.path.splitext(os.path.basename(infile))[0] + f"{suffix}.{fmt}"
                fig.savefig(outname, format=fmt)
                print(f"Saved plot to {outname}")
    else:
        for fig in figs:
            if fig is not None:
                plt.figure(fig.number)
        plt.show()


if __name__ == "__main__":
    main()
