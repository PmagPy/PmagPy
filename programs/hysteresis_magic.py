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
import numpy as np
import matplotlib.pyplot as plt


def main():
    """
    NAME
        hysteresis_magic.py

    DESCRIPTION
        Calculates hysteresis parameters and saves them in MagIC 3.0 specimen format file.
        Makes static plots if option selected. Uses new backend (pmagpy.rockmag) for all
        calculations and plotting.

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h           Prints help message and quits
        -f FILE      Specify input file, default is measurements.txt
        -F FILE      Specify specimens.txt output file
        -WD DIR      Directory to output files to (default: current directory)
        -ID DIR      Directory to read files from (default: same as -WD)
        -P           Do not make plots
        -spc SPEC    Specify a single specimen name to process and quit
        -sav         Save all plots and quit
        -fmt FMT     Output plot format: png, svg, eps, jpg (default: svg)
        -n N         Process only the first N specimens (or "all" for all)
        -i           Interactive mode: pause after each specimen for navigation
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()

    output_dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', output_dir_path)
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    spec_file = pmag.get_named_arg('-F', 'specimens.txt')
    fmt = pmag.get_named_arg('-fmt', 'svg')
    pltspec = pmag.get_named_arg('-spc', '')
    n_specs = pmag.get_named_arg('-n', 5)
    make_plots = '-P' not in args
    save_plots = '-sav' in args
    interactive = '-i' in args

    hysteresis_magic(
        output_dir_path=output_dir_path,
        input_dir_path=input_dir_path,
        spec_file=spec_file,
        meas_file=meas_file,
        fmt=fmt,
        save_plots=save_plots,
        make_plots=make_plots,
        pltspec=pltspec,
        n_specs=n_specs,
        interactive=interactive,
    )


def hysteresis_magic(output_dir_path=".", input_dir_path="", spec_file="specimens.txt",
                     meas_file="measurements.txt", fmt="svg",
                     save_plots=True, make_plots=True, pltspec="", n_specs=5, interactive=False):
    """
    Calculate hysteresis parameters and plot hysteresis data using the rockmag backend.

    Parameters
    ----------
    output_dir_path : str, default "."
        Directory to write output files and plots.
    input_dir_path : str, default ""
        Directory to read input files from (defaults to output_dir_path).
    spec_file : str, default "specimens.txt"
        Output MagIC specimens file.
    meas_file : str, default "measurements.txt"
        Input MagIC measurements file.
    fmt : str, default "svg"
        Plot format: svg, png, jpg, pdf, eps.
    save_plots : bool, default True
        If True, save all plots to files.
    make_plots : bool, default True
        If False, suppress all plotting (also sets save_plots=False).
    pltspec : str, default ""
        Name of a single specimen to process; all others are skipped.
    n_specs : int or "all", default 5
        Number of specimens to process; use "all" for all specimens.
    interactive : bool, default False
        If True, pause after each specimen for user input.
        (Implies save_plots=False; user can save with 'a'.)

    Returns
    -------
    tuple
        (success: bool, output_files: list of str)
    """
    if not input_dir_path:
        input_dir_path = output_dir_path
    os.makedirs(output_dir_path, exist_ok=True)

    meas_path = os.path.join(input_dir_path, meas_file)
    if not os.path.isfile(meas_path):
        print(f"Measurement file not found: {meas_path}")
        return False, []

    measurements = pd.read_csv(meas_path, sep='\t', skiprows=1)

    # Detect magnetization column: prefer mass-normalized, fall back to moment
    magn_col = None
    for col in ['magn_mass', 'magn_moment', 'magn_volume']:
        if col in measurements.columns:
            magn_col = col
            break
    if magn_col is None:
        magn_col = next((c for c in measurements.columns if 'magn_' in c), None)
    if magn_col is None:
        print("No magnetization column found in measurement file.")
        return False, []

    version_num = pmag.get_version()
    if not make_plots:
        save_plots = False
    if interactive:
        save_plots = False

    # Load existing specimens data to merge with new results
    spec_path = os.path.join(output_dir_path, os.path.basename(spec_file))
    prior_recs = []
    if os.path.isfile(spec_path):
        try:
            prior_recs = pd.read_csv(spec_path, sep='\t', skiprows=1).to_dict('records')
        except Exception:
            pass

    # Split measurements by experiment type
    hys_df = measurements[measurements['method_codes'].str.contains('LP-HYS', na=False)]
    dcd_df = measurements[measurements['method_codes'].str.contains('LP-IRM-DCD', na=False)]
    imag_df = measurements[measurements['method_codes'].str.contains('LP-IMAG', na=False)]

    sids = hys_df['specimen'].drop_duplicates().tolist()
    if not sids:
        print("No LP-HYS (hysteresis) data found.")
        return False, []

    # Determine starting index and trim specimen list
    if pltspec:
        if pltspec not in sids:
            print(f"Specimen {pltspec} not found in hysteresis data.")
            return False, []
        k = sids.index(pltspec)
    else:
        k = 0
        if n_specs != "all":
            try:
                sids = sids[:int(n_specs)]
            except Exception as e:
                print("Error selecting n_specs:", e)

    HystRecs = []
    while k < len(sids):
        specimen = sids[k]
        # With pltspec, skip any specimen that isn't the requested one
        if pltspec and specimen != pltspec:
            k += 1
            continue

        print(specimen, k + 1, 'out of', len(sids))
        HystRec = {
            'specimen': specimen,
            'experiments': '',
            'method_codes': '',
            'citations': 'This study',
            'software_packages': version_num,
        }
        spec_figs = {}  # key -> matplotlib Figure for this specimen

        # --- Hysteresis (LP-HYS) ---
        spec_hys = hys_df[hys_df['specimen'] == specimen]
        if not spec_hys.empty:
            exp_name = spec_hys['experiment'].iloc[0] if 'experiment' in spec_hys.columns else ''
            HystRec['experiments'] = exp_name
            B = spec_hys['meas_field_dc'].values.astype(float)
            M = spec_hys[magn_col].values.astype(float)
            try:
                res = rockmag.process_hyst_loop(B, M, specimen,
                                                show_results_table=False, show_plot=False)
                HystRec['hyst_ms_moment'] = res['Ms']
                HystRec['hyst_mr_moment'] = res['Mr']
                HystRec['hyst_bc'] = res['Bc']
                HystRec['hyst_xhf'] = res['chi_HF']
                HystRec['method_codes'] = 'LP-HYS'
                if make_plots:
                    fig, ax = plt.subplots(figsize=(6, 6))
                    ax.plot(res['gridded_H'], res['gridded_M'],
                            color='orange', label='raw loop')
                    ax.plot(res['centered_H'], res['slope_corrected_M'],
                            color='blue', label='slope corrected')
                    ax.set_title(f'{specimen} hysteresis loop')
                    ax.set_xlabel('Field (T)')
                    ax.set_ylabel('Magnetization')
                    ax.legend(loc='lower right')
                    ax.grid(True)
                    ax.text(0.02, 0.98,
                            f"Ms: {res['Ms']:.3e}\n"
                            f"Mr: {res['Mr']:.3e}\n"
                            f"Bc: {res['Bc']:.3e} T\n"
                            f"chi_HF: {res['chi_HF']:.3e}",
                            transform=ax.transAxes, fontsize=9,
                            verticalalignment='top',
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
                    plt.tight_layout()
                    spec_figs['hyst'] = fig

                    # deltaM plot: 2*Mrh (upper minus lower branch) vs field
                    H = res['H']
                    deltaM = 2 * res['Mrh']
                    fig_dm, ax_dm = plt.subplots(figsize=(5, 5))
                    ax_dm.plot(H, deltaM, 'k-')
                    ax_dm.set_title(f'{specimen} deltaM')
                    ax_dm.set_xlabel('Field (T)')
                    ax_dm.set_ylabel('deltaM')
                    ax_dm.grid(True)
                    plt.tight_layout()
                    spec_figs['deltaM'] = fig_dm

                    # DdeltaM plot: derivative of deltaM -- coercivity spectrum
                    dH = np.gradient(H)
                    with np.errstate(divide='ignore', invalid='ignore'):
                        DdeltaM = np.where(dH != 0,
                                           np.gradient(deltaM) / dH,
                                           0.0)
                    fig_ddm, ax_ddm = plt.subplots(figsize=(5, 5))
                    ax_ddm.plot(H, DdeltaM, 'k-')
                    ax_ddm.set_title(f'{specimen} DdeltaM')
                    ax_ddm.set_xlabel('Field (T)')
                    ax_ddm.set_ylabel('DdeltaM')
                    ax_ddm.grid(True)
                    plt.tight_layout()
                    spec_figs['DdeltaM'] = fig_ddm
            except Exception as e:
                print(f"Error processing hysteresis for {specimen}: {e}")

        # --- IRM / backfield (LP-IRM-DCD) ---
        spec_dcd = dcd_df[dcd_df['specimen'] == specimen].copy()
        if not spec_dcd.empty:
            try:
                # Only drop first row if it is at zero or positive field
                # (log10(-field) is undefined for field >= 0).
                drop_first_irm = spec_dcd['treat_dc_field'].iloc[0] >= 0
                irm_df, Bcr = rockmag.backfield_data_processing(spec_dcd,
                                                                magnetization=magn_col,
                                                                smooth_mode='spline',
                                                                drop_first=drop_first_irm)
                HystRec['rem_bcr'] = Bcr
                HystRec['rem_mr_moment'] = spec_dcd[magn_col].max()
                if make_plots:
                    fig_irm, _ = rockmag.plot_backfield_data(
                        irm_df,
                        field='treat_dc_field',
                        magnetization=magn_col,
                        Bcr=Bcr,
                        interactive=False,
                        return_figure=True,
                        show_plot=False,
                    )
                    spec_figs['irm'] = fig_irm
            except Exception as e:
                print(f"Error processing IRM for {specimen}: {e}")

        # --- Initial magnetization (LP-IMAG) ---
        spec_imag = imag_df[imag_df['specimen'] == specimen]
        if not spec_imag.empty and 'hyst_ms_moment' in HystRec:
            try:
                Bimag = spec_imag['meas_field_dc'].values.astype(float)
                Mimag = spec_imag[magn_col].values.astype(float)
                Mnorm = Mimag / HystRec['hyst_ms_moment']
                if make_plots:
                    fig_imag, ax_imag = plt.subplots(figsize=(5, 5))
                    ax_imag.plot(Bimag, Mnorm, 'r.-')
                    ax_imag.set_title(f'{specimen} Initial Magnetization')
                    ax_imag.set_xlabel('Field (T)')
                    ax_imag.set_ylabel('M/Ms')
                    ax_imag.grid(True)
                    plt.tight_layout()
                    spec_figs['imag'] = fig_imag
            except Exception as e:
                print(f"Error processing IMAG for {specimen}: {e}")

        HystRecs.append(HystRec)

        # --- Plotting / interactive navigation ---
        if make_plots:
            if interactive:
                # Draw without blocking so input() is reachable
                for fig_obj in spec_figs.values():
                    fig_obj.canvas.draw()
                plt.pause(0.001)
                ans = input(
                    "S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
                if ans == "a":
                    for key, fig_obj in spec_figs.items():
                        outname = os.path.join(output_dir_path,
                                               f"{specimen}_{key}.{fmt}")
                        fig_obj.savefig(outname, format=fmt)
                        print(f"Saved: {outname}")
                    # 'a' does not advance (legacy behavior: press Enter to continue)
                if ans == '':
                    for fig_obj in spec_figs.values():
                        plt.close(fig_obj)
                    k += 1
                elif ans == 'p':
                    if HystRecs:
                        HystRecs.pop()
                    for fig_obj in spec_figs.values():
                        plt.close(fig_obj)
                    k -= 1
                elif ans == 'q':
                    for fig_obj in spec_figs.values():
                        plt.close(fig_obj)
                    print("Good bye")
                    break
                elif ans == 's':
                    spec_input = input(
                        'Enter desired specimen name (or first part there of): ')
                    while True:
                        if spec_input in sids:
                            k = sids.index(spec_input)
                            break
                        matches = [s for s in sids if spec_input in s]
                        print(f"{spec_input} not found, but this was: {matches}")
                        spec_input = input('Select one or try again\n ')
                    for fig_obj in spec_figs.values():
                        plt.close(fig_obj)
            elif save_plots:
                for key, fig_obj in spec_figs.items():
                    outname = os.path.join(output_dir_path,
                                           f"{specimen}_{key}.{fmt}")
                    fig_obj.savefig(outname, format=fmt)
                    print(f"Saved: {outname}")
                for fig_obj in spec_figs.values():
                    plt.close(fig_obj)
                k += 1
            else:
                plt.show()
                for fig_obj in spec_figs.values():
                    plt.close(fig_obj)
                k += 1
        else:
            k += 1

    # --- Save results to specimens file ---
    if HystRecs:
        # Preserve prior records not from LP-HYS processing
        kept_prior = [r for r in prior_recs
                      if 'LP-HYS' not in r.get('method_codes', '')]
        all_recs = kept_prior + HystRecs
        # Align all records to the same column set
        all_keys = set()
        for rec in all_recs:
            all_keys.update(rec.keys())
        for rec in all_recs:
            for key in all_keys:
                if key not in rec:
                    rec[key] = ''
        out_df = pd.DataFrame(all_recs).drop_duplicates()
        spec_out = os.path.join(output_dir_path, os.path.basename(spec_file))
        with open(spec_out, 'w') as f:
            f.write('tab\tspecimens\n')
            out_df.to_csv(f, sep='\t', index=False)
        print(f"Hysteresis parameters saved in {spec_out}")
        return True, [spec_out]

    return False, []


if __name__ == "__main__":
    main()
