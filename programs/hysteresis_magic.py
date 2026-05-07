#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
from pmagpy import pmag
from pmagpy import rockmag
import numpy as np
import matplotlib.pyplot as plt


def main():
    """
    NAME
        hysteresis_magic.py

    DESCRIPTION
        calculates hysteresis parameters and saves them in 3.0 specimen format file
        makes plots if option selected

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is measurements.txt
        -F: specify specimens.txt output file
        -WD: directory to output files to (default : current directory)
             Note: if using Windows, all figures will output to current directory
        -ID: directory to read files from (default : same as -WD)
        -P: do not make the plots
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
        -n N: number of specimens to process (default 5, use "all" for all)
        -i: interactive mode
    """
    args = sys.argv
    fmt = pmag.get_named_arg('-fmt', 'svg')
    output_dir_path = pmag.get_named_arg('-WD', '.')
    input_dir_path = pmag.get_named_arg('-ID', "")
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    meas_file = pmag.get_named_arg('-f', 'measurements.txt')
    spec_file = pmag.get_named_arg('-F', 'specimens.txt')
    pltspec = pmag.get_named_arg('-spc', "")
    n_specs = pmag.get_named_arg('-n', 5)
    make_plots = '-P' not in args
    save_plots = '-sav' in args
    interactive = '-i' in args
    hysteresis_magic(output_dir_path, input_dir_path, spec_file, meas_file,
                     fmt, save_plots, make_plots, pltspec, n_specs, interactive)


def hysteresis_magic(output_dir_path=".", input_dir_path="", spec_file="specimens.txt",
                     meas_file="measurements.txt", fmt="svg",
                     save_plots=True, make_plots=True, pltspec="", n_specs=5, interactive=False):
    """
    Calculate hysteresis parameters and plot hysteresis data using the rockmag backend.
    Plots match the style of the original pmagplotlib-based implementation.

    Parameters
    ----------
    output_dir_path : str, default "."
        Note: on Windows all figures are saved to the current directory.
    input_dir_path : str, default ""
        Path for input files if different from output_dir_path.
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
        Specimen name to plot; otherwise plot all specimens.
    n_specs : int or "all", default 5
        Number of specimens to process.
    interactive : bool, default False
        Interactively plot and display for each specimen.

    Returns
    -------
    tuple : (bool, list of str)
    """
    if not input_dir_path:
        input_dir_path = output_dir_path
    input_dir_path, output_dir_path = pmag.fix_directories(input_dir_path, output_dir_path)

    meas_file_path = pmag.resolve_file_name(meas_file, input_dir_path)
    spec_file_path = pmag.resolve_file_name(spec_file, input_dir_path)

    version_num = pmag.get_version()
    if not make_plots:
        save_plots = False
    if interactive:
        save_plots = False

    meas_data, file_type = pmag.magic_read(meas_file_path)
    if file_type != 'measurements':
        print('bad file', meas_file_path)
        return False, []

    prior_data = []
    if os.path.isfile(spec_file_path):
        prior_data, _ = pmag.magic_read(spec_file_path)

    hys_data = pmag.get_dictitem(meas_data, 'method_codes', 'LP-HYS', 'has')
    dcd_data = pmag.get_dictitem(meas_data, 'method_codes', 'LP-IRM-DCD', 'has')
    imag_data = pmag.get_dictitem(meas_data, 'method_codes', 'LP-IMAG', 'has')

    sids = []
    for rec in hys_data:
        if rec['specimen'] not in sids:
            sids.append(rec['specimen'])
    if not sids:
        print("-W- No hysteresis data found")
        return False, []

    k = 0
    if pltspec:
        try:
            k = sids.index(pltspec)
        except ValueError:
            print('-W- No specimen named: {}.'.format(pltspec))
            return False, []
    elif n_specs != "all":
        try:
            sids = sids[:int(n_specs)]
        except Exception as e:
            print("Error selecting n_specs:", e)

    HystRecs = []
    while k < len(sids):
        specimen = sids[k]
        if pltspec and specimen != pltspec:
            k += 1
            continue

        print(specimen, k + 1, 'out of ', len(sids))
        HystRec = {'specimen': specimen, 'experiments': '',
                   'citations': 'This study', 'software_packages': version_num}
        spec_figs = {}

        # --- Hysteresis (LP-HYS) ---
        spec_hys = pmag.get_dictitem(hys_data, 'specimen', specimen, 'T')
        B, M, meths = [], [], []
        if spec_hys:
            e = spec_hys[0]['experiment']
            meths = spec_hys[0]['method_codes'].split(':')
            HystRec['experiments'] = e
            HystRec['meas_orient_phi'] = spec_hys[0].get('treat_dc_field_phi', '0')
            HystRec['meas_orient_theta'] = spec_hys[0].get('treat_dc_field_theta', '0')
            for rec in spec_hys:
                B.append(float(rec['meas_field_dc']))
                M.append(float(rec['magn_moment']))

        if B:
            try:
                res = rockmag.process_hyst_loop(np.array(B), np.array(M), specimen,
                                                show_results_table=False, show_plot=False)
                Msat = res['Ms']
                Mr = res['Mr']
                Bc = res['Bc']
                Bcr_hyst = res['Brh']
                chi_HF = res['chi_HF']
                H = res['H']
                Mrh = res['Mrh']

                HystRec['hyst_ms_moment'] = '%8.3e' % Msat
                HystRec['hyst_mr_moment'] = '%8.3e' % Mr
                HystRec['hyst_bc'] = '%8.3e' % Bc
                HystRec['hyst_bcr'] = '%8.3e' % Bcr_hyst
                HystRec['hyst_xhf'] = '%8.2e' % (chi_HF * 4 * np.pi * 1e-7)
                hmeths = list(meths) + ['LP-BCR-HDM']
                HystRec['method_codes'] = ':'.join(m.strip() for m in hmeths if m.strip())
                HystRec['experiments'] = e

                if make_plots:
                    # hyst: red=raw, blue=corrected, normalized to Ms (matches plot_hys/plot_hpars)
                    fig_hyst, ax_hyst = plt.subplots(figsize=(5, 5))
                    ax_hyst.plot(res['gridded_H'], res['gridded_M'] / Msat, 'r')
                    ax_hyst.plot(res['centered_H'], res['slope_corrected_M'] / Msat, 'b')
                    ax_hyst.axhline(0, color='k')
                    ax_hyst.axvline(0, color='k')
                    ax_hyst.set_xlabel('B (T)')
                    ax_hyst.set_ylabel('M/Msat')
                    ax_hyst.set_title(specimen)
                    Mr_norm = Mr / Msat
                    ax_hyst.plot([0, Bc], [Mr_norm, 0], 'bs')
                    bounds = ax_hyst.axis()
                    xtext = bounds[0] + 0.05 * (bounds[1] - bounds[0])
                    ax_hyst.text(xtext, -0.9, 'Ms: %8.2e Am^2' % Msat)
                    ax_hyst.text(xtext, -0.7, 'Mr: %8.2e Am^2' % Mr)
                    ax_hyst.text(xtext, -0.5, 'Bc: %8.2e T' % Bc)
                    ax_hyst.text(xtext, -0.3,
                                 'Xhf: %8.2e m^3' % (chi_HF * 4 * np.pi * 1e-7))
                    plt.tight_layout()
                    spec_figs['hyst'] = fig_hyst

                    # deltaM: blue, zero lines, red Bcr crosshair (matches plot_delta_m)
                    deltaM = 2 * Mrh / Msat
                    fig_dm, ax_dm = plt.subplots(figsize=(5, 5))
                    ax_dm.plot(H, deltaM, 'b')
                    ax_dm.axhline(0, color='k')
                    ax_dm.axvline(0, color='k')
                    if len(deltaM) > 0:
                        ax_dm.plot([0, Bcr_hyst, Bcr_hyst],
                                   [deltaM[0] / 2, deltaM[0] / 2, 0], 'r')
                    ax_dm.set_xlabel('B (T)')
                    ax_dm.set_ylabel('Delta M')
                    ax_dm.set_title(specimen)
                    ax_dm.plot([Bcr_hyst], [0], 'bs')
                    dm_bounds = ax_dm.axis()
                    ax_dm.text(dm_bounds[0] + 0.5 * (dm_bounds[1] - dm_bounds[0]),
                               0.9 * dm_bounds[3],
                               'Bcr: %8.2e T' % Bcr_hyst)
                    plt.tight_layout()
                    spec_figs['deltaM'] = fig_dm

                    # DdeltaM: finite differences (matches plot_d_delta_m)
                    DdeltaM = []
                    for ki in range(2, len(H)):
                        dh = H[ki] - H[ki - 2]
                        DdeltaM.append(
                            abs(deltaM[ki] - deltaM[ki - 2]) / dh if dh != 0 else 0.0)
                    start = len(H) - len(DdeltaM)
                    fig_ddm, ax_ddm = plt.subplots(figsize=(5, 5))
                    ax_ddm.plot(H[start:], DdeltaM, 'b')
                    ax_ddm.set_xlabel('B (T)')
                    ax_ddm.set_ylabel('d(Delta M)/dB')
                    ax_ddm.set_title(specimen)
                    plt.tight_layout()
                    spec_figs['DdeltaM'] = fig_ddm

            except Exception as e:
                print('Error processing hysteresis for %s: %s' % (specimen, e))

        # --- IRM / backfield (LP-IRM-DCD) ---
        spec_dcd = pmag.get_dictitem(dcd_data, 'specimen', specimen, 'T')
        Bdcd, Mdcd, irm_exp = [], [], ''
        if spec_dcd:
            irm_exp = spec_dcd[0]['experiment']
            HystRec['experiments'] = HystRec.get('experiments', '') + ':' + irm_exp
            for rec in spec_dcd:
                Bdcd.append(float(rec['treat_dc_field']))
                Mdcd.append(float(rec['magn_moment']))

        if Bdcd:
            try:
                # Bcr by linear interpolation around zero crossing (matches plot_irm)
                bcr = 0.0
                ki = len(Mdcd) - 1
                for ki in range(len(Mdcd)):
                    if Mdcd[ki] < 0:
                        break
                kmin_irm = max(0, ki - 5)
                Xfit = Bdcd[kmin_irm:ki + 1]
                Yfit = Mdcd[kmin_irm:ki + 1]
                if len(Xfit) >= 2 and any(b < 0 for b in Xfit):
                    poly = np.polyfit(Xfit, Yfit, 1)
                    if poly[0] != 0:
                        bcr = -poly[1] / poly[0]
                HystRec['rem_mr_moment'] = '%8.3e' % Mdcd[0]
                HystRec['rem_bcr'] = '%8.3e' % (-bcr)
                mc = HystRec.get('method_codes', '')
                if 'LP-BCR-BF' not in mc:
                    HystRec['method_codes'] = (mc + ':LP-BCR-BF') if mc else 'LP-BCR-BF'

                if make_plots:
                    # Single-panel normalized IRM (matches plot_irm)
                    if Mdcd[0] != 0:
                        Mnorm_irm = [m / Mdcd[0] for m in Mdcd]
                        irm_title = irm_exp + ':' + '%8.3e' % Mdcd[0]
                    elif Mdcd[-1] != 0:
                        Mnorm_irm = [m / Mdcd[-1] for m in Mdcd]
                        irm_title = irm_exp + ':' + '%8.3e' % Mdcd[-1]
                    else:
                        Mnorm_irm = list(Mdcd)
                        irm_title = irm_exp
                    fig_irm, ax_irm = plt.subplots(figsize=(5, 5))
                    ax_irm.plot(Bdcd, Mnorm_irm)
                    ax_irm.axhline(0, color='k')
                    ax_irm.axvline(0, color='k')
                    ax_irm.set_xlabel('B (T)')
                    ax_irm.set_title(irm_title)
                    plt.tight_layout()
                    spec_figs['irm'] = fig_irm
            except Exception as e:
                print('Error processing IRM for %s: %s' % (specimen, e))

        # --- Initial magnetization (LP-IMAG) ---
        spec_imag_recs = pmag.get_dictitem(imag_data, 'specimen', specimen, 'T')
        if spec_imag_recs and 'hyst_ms_moment' in HystRec:
            try:
                imag_exp = spec_imag_recs[0]['experiment']
                Bimag = [float(r['meas_field_dc']) for r in spec_imag_recs]
                Mimag = [float(r['magn_moment']) for r in spec_imag_recs]
                Ms_val = float(HystRec['hyst_ms_moment'])
                Mnorm_imag = [m / Ms_val for m in Mimag]
                if make_plots:
                    fig_imag, ax_imag = plt.subplots(figsize=(5, 5))
                    ax_imag.plot(Bimag, Mnorm_imag, 'r')
                    ax_imag.axvline(0, color='k')
                    ax_imag.set_xlabel('B (T)')
                    ax_imag.set_ylabel('M/Ms')
                    ax_imag.set_title(imag_exp)
                    plt.tight_layout()
                    spec_figs['imag'] = fig_imag
            except Exception as e:
                print('Error processing IMAG for %s: %s' % (specimen, e))

        if HystRec:
            HystRecs.append(HystRec)

        # --- Plotting / interactive navigation ---
        if make_plots and spec_figs:
            if interactive:
                for fig_obj in spec_figs.values():
                    fig_obj.canvas.draw()
                plt.pause(0.001)
                ans = input(
                    "S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
                if ans == "a":
                    for key, fig_obj in spec_figs.items():
                        outname = specimen + '_' + key + '.' + fmt
                        fig_obj.savefig(outname, format=fmt)
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
                    return True, []
                elif ans == 's':
                    specimen_input = input(
                        'Enter desired specimen name (or first part there of): ')
                    while True:
                        if specimen_input in sids:
                            k = sids.index(specimen_input)
                            break
                        tmplist = [s for s in sids if specimen_input in s]
                        print(specimen_input, ' not found, but this was: ')
                        print(tmplist)
                        specimen_input = input('Select one or try again\n ')
                    for fig_obj in spec_figs.values():
                        plt.close(fig_obj)
                else:
                    k += 1
            elif save_plots:
                for key, fig_obj in spec_figs.items():
                    outname = specimen + '_' + key + '.' + fmt
                    fig_obj.savefig(outname, format=fmt)
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

    # --- Save results ---
    if HystRecs:
        SpecRecs = []
        keys = list(HystRecs[0].keys())
        prior_keys = list(prior_data[0].keys()) if prior_data else []
        for rec in prior_data:
            for key in keys:
                if key not in rec:
                    rec[key] = ''
            if 'LP-HYS' not in rec.get('method_codes', ''):
                SpecRecs.append(rec)
        for rec in HystRecs:
            for key in prior_keys:
                if key not in rec:
                    rec[key] = ''
            prior = pmag.get_dictitem(prior_data, 'specimen', rec['specimen'], 'T')
            if prior and 'sample' in prior[0]:
                rec['sample'] = prior[0]['sample']
            SpecRecs.append(rec)
        spec_out = os.path.join(output_dir_path, os.path.basename(spec_file))
        pmag.magic_write(spec_out, SpecRecs, 'specimens')
        print("hysteresis parameters saved in ", spec_out)
        return True, [spec_out]

    return False, []


if __name__ == "__main__":
    main()
