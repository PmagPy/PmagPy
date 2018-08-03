#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag


def main():
    """
    NAME
        chi_magic.py

    DESCRIPTION
        plots magnetic susceptibility as a function of frequency and temperature and AC field

    SYNTAX
        chi_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE, specify measurements format file, default "measurements.txt"
        -T IND, specify temperature step to plot
        -e EXP, specify experiment name to plot
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
        -sav save figure and quit

    """
    if "-h" in sys.argv:
        print(main.__doc__)
        return
    infile = pmag.get_named_arg("-f", "measurements.txt")
    dir_path = pmag.get_named_arg("-WD", ".")
    infile = pmag.resolve_file_name(infile, dir_path)
    fmt = pmag.get_named_arg("-fmt", "svg")
    show_plots = True
    if "-sav" in sys.argv:
        show_plots = False
    experiments = pmag.get_named_arg("-e", "")
    # read in data from data model 3 example file
    chi_data_all = pd.read_csv(infile, sep='\t', header=1)

    if not experiments:
        try:
            experiments = chi_data_all.experiment.unique()
        except Exception as ex:
            print(ex)
            experiments = ["all"]
    else:
         experiments = [experiments]

    plotnum = 0
    figs = {}
    fnames = {}
    for exp in experiments:
        if exp == "all":
            chi_data = chi_data_all
        chi_data = chi_data_all[chi_data_all.experiment == exp]
        if len(chi_data) <= 1:
            print('Not enough data to plot {}'.format(exp))
            continue

        plotnum += 1
        pmagplotlib.plot_init(plotnum, 5, 5)  # set up plot
        figs[str(plotnum)] = plotnum
        fnames[str(plotnum)] = exp + '_temperature.{}'.format(fmt)

        # get arrays of available temps, frequencies and fields
        Ts = np.sort(chi_data.meas_temp.unique())
        Fs = np.sort(chi_data.meas_freq.unique())
        Bs = np.sort(chi_data.meas_field_ac.unique())

        # plot chi versus temperature at constant field
        b = Bs.max()
        for num, f in enumerate(Fs):
            this_f = chi_data[chi_data.meas_freq == f]
            this_f = this_f[this_f.meas_field_ac == b]
            plt.plot(this_f.meas_temp, 1e6*this_f.susc_chi_volume,
                     label='%i' % (f)+' Hz')
        plt.legend()
        plt.xlabel('Temperature (K)')
        plt.ylabel('$\chi$ ($\mu$SI)')
        plt.title('B = '+'%7.2e' % (b) + ' T')

        plotnum += 1
        figs[str(plotnum)] = plotnum
        fnames[str(plotnum)] = exp + '_frequency.{}'.format(fmt)

        pmagplotlib.plot_init(plotnum, 5, 5)  # set up plot
        ## plot chi versus frequency at constant B
        b = Bs.max()
        t = Ts.min()
        this_t = chi_data[chi_data.meas_temp == t]
        this_t = this_t[this_t.meas_field_ac == b]
        plt.semilogx(this_t.meas_freq, 1e6 *
                     this_t.susc_chi_volume, label='%i' % (t)+' K')
        plt.legend()
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('$\chi$ ($\mu$SI)')
        plt.title('B = '+'%7.2e' % (b) + ' T')

    if show_plots:
        pmagplotlib.draw_figs(figs)
        ans = input(
            "enter s[a]ve to save files,  [return] to quit ")
        if ans == 'a':
            pmagplotlib.save_plots(figs, fnames)
            sys.exit()
        else:
            sys.exit()

    else:
        pmagplotlib.save_plots(figs, fnames)


if __name__ == "__main__":
    main()
