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
        hysteresis_magic.py

    DESCRIPTION
        Calculates hysteresis parameters and saves them in MagIC 3.0 specimen format file.
        Makes plots if option selected.

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h           Prints help message and quits
        -f FILE      Specify input file, default is measurements.txt
        -F FILE      Specify specimens.txt output file
        -WD DIR      Directory to output files to (default: current directory)
                     Note: if using Windows, all figures will output to current directory
        -ID DIR      Directory to read files from (default: same as -WD)
        -P           Do not make the plots
        -spc SPEC    Specify specimen name to plot and quit
        -sav         Save all plots and quit
        -fmt [png,svg,eps,jpg]  Output plot format (default: svg)

    EXAMPLES
        # Basic usage with default files:
        hysteresis_magic.py

        # Specify input and output files:
        hysteresis_magic.py -f my_measurements.txt -F my_specimens.txt

        # Save all plots as PNGs in a specific directory:
        hysteresis_magic.py -WD results -fmt png -sav

        # Plot a specific specimen and quit:
        hysteresis_magic.py -spc Specimen_001
    """

    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    # CLI options
    fmt = pmag.get_named_arg('-fmt', 'svg')
    output_dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', output_dir_path)
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    spec_file = pmag.get_named_arg('-F', 'specimens.txt')
    make_plots = True
    save_plots = False
    if '-P' in args:
        make_plots = False
    if '-sav' in args:
        save_plots = True
    pltspec = pmag.get_named_arg('-spc', 0)

    # Load measurement data
    meas_path = os.path.join(input_dir_path, meas_file)
    if not os.path.isfile(meas_path):
        print(f"Measurement file not found: {meas_path}")
        sys.exit(1)
    measurements = pd.read_csv(meas_path, sep='\t', skiprows=1)

    # Detect magnetization column (support magn_mass, magn_moment, etc.)
    magn_col = next((col for col in measurements.columns if 'magn_' in col), None)
    if magn_col is None:
        raise KeyError("No column containing 'magn_' found in measurement file.")

    # Load specimen data
    spec_path = os.path.join(output_dir_path, spec_file)
    if os.path.isfile(spec_path):
        specimens = pd.read_csv(spec_path, sep='\t', skiprows=1)
    else:
        specimens = pd.DataFrame()

    # If a specific specimen is requested, plot and quit
    if pltspec and pltspec != '0':
        hyst_data = rockmag.extract_hysteresis_data(measurements, pltspec)
        if hyst_data.empty:
            print(f"No hysteresis data found for specimen: {pltspec}")
            sys.exit(1)
        field = hyst_data['meas_field_dc'].values
        magnetization = hyst_data[magn_col].values
        # Always use static Matplotlib plot
        fig_ax = rockmag.plot_hysteresis_loop(
            field, magnetization, pltspec,
            interactive=False, show_plot=make_plots, return_figure=True
        )
        if save_plots and fig_ax is not None:
            fig, ax = fig_ax
            outname = f"{pltspec}_hysteresis.{fmt}"
            outpath = os.path.join(output_dir_path, outname)
            fig.savefig(outpath, format=fmt)
            print(f"Saved plot to {outpath}")
        sys.exit(0)

    # Otherwise, process all specimens in batch
    # Find all unique LP-HYS experiments
    hyst_experiments = measurements[measurements['method_codes'].str.contains('LP-HYS', na=False)]
    if hyst_experiments.empty:
        print("No LP-HYS (hysteresis) data found in measurement file.")
        sys.exit(1)
    # Build experiment/specimen table
    exp_spec_df = hyst_experiments[['experiment', 'specimen']].drop_duplicates().reset_index(drop=True)
    results_df = rockmag.process_hyst_loops(
        exp_spec_df, measurements,
        field_col="meas_field_dc", magn_col=magn_col,
        show_results_table=True, show_plots=False
    )

    # Save results to output_dir_path/specimens.txt if requested
    if not specimens.empty:
        # Update existing specimens table with new results
        for spec in results_df.index:
            for col in ['Ms', 'Mr', 'Bc', 'chi_HF']:
                col_map = {'Ms': 'hyst_ms_mass', 'Mr': 'hyst_mr_mass', 'Bc': 'hyst_bc', 'chi_HF': 'hyst_xhf'}
                if col_map[col] in specimens.columns:
                    specimens.loc[specimens['specimen'] == spec, col_map[col]] = results_df.at[spec, col]
        out_spec_path = os.path.join(output_dir_path, spec_file)
        specimens.to_csv(out_spec_path, sep='\t', index=False)
        print(f"Updated specimen results written to {out_spec_path}")
    else:
        # Write new results table
        out_spec_path = os.path.join(output_dir_path, spec_file)
        results_df.reset_index().to_csv(out_spec_path, sep='\t', index=False)
        print(f"Specimen results written to {out_spec_path}")

    # Optionally save all static plots
    if save_plots:
        for spec in results_df.index:
            hyst_data = rockmag.extract_hysteresis_data(measurements, spec)
            if hyst_data.empty:
                continue
            field = hyst_data['meas_field_dc'].values
            magnetization = hyst_data[magn_col].values
            fig_ax = rockmag.plot_hysteresis_loop(
                field, magnetization, spec,
                interactive=False, show_plot=False, return_figure=True
            )
            if fig_ax is not None:
                fig, ax = fig_ax
                outname = f"{spec}_hysteresis.{fmt}"
                outpath = os.path.join(output_dir_path, outname)
                fig.savefig(outpath, format=fmt)
                print(f"Saved plot to {outpath}")


if __name__ == "__main__":
    main()
