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
        -i allows interactive setting of FILE and temperature step
        -f FILE, specify measurements format file, default "measurements.txt"
        -T IND, specify temperature step to plot
        -e EXP, specify experiment name to plot
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
        -sav save figure and quit

    DEFAULTS
         FILE: magic_measurements.txt
         IND: first
         SPEC: step through one by one
    """
    if "-h" in sys.argv:
        print(main.__doc__)
        return
    print('ok')
    infile = pmag.get_named_arg("-f", "measurements.txt")
    dir_path = pmag.get_named_arg("-WD", ".")
    infile = pmag.resolve_file_name(infile, dir_path)
    fmt = pmag.get_named_arg("-fmt", "svg")
    show_plots = True
    if "-sav" in sys.argv:
        show_plots = False
    # read in data from data model 3 example file
    chi_data = pd.read_csv(infile, sep='\t', header=1)
    # get arrays of available temps, frequencies and fields
    Ts = np.sort(chi_data.meas_temp.unique())
    Fs = np.sort(chi_data.meas_freq.unique())
    Bs = np.sort(chi_data.meas_field_ac.unique())

    experiments = chi_data.experiment.unique()
    print(experiments)
    print('here')

    # plot chi versus temperature at constant field
    b = Bs.max()
    for num, f in enumerate(Fs):
        this_f = chi_data[chi_data.meas_freq == f]
        this_f = this_f[this_f.meas_field_ac == b]
        plt.plot(this_f.meas_temp, 1e6*this_f.susc_chi_volume,
                 label='%i' % (f)+' Hz')
        #figs['fig_{}'.format(str(num))] = num
    plt.legend()
    plt.xlabel('Temperature (K)')
    plt.ylabel('$\chi$ ($\mu$SI)')
    plt.title('B = '+'%7.2e' % (b) + ' T')

    print('yes')
    # plot chi versus frequency at constant B
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


    plt.plot(2)
    # plot chi versus frequency at constant B
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

    figs = {'fig': 1, 'fig2': 2}
    print(show_plots)
    if show_plots:
        pmagplotlib.drawFIGS(figs)
    else:
        print(figs)
        fnames = {figname: 'something_' + figname + "." +
                  fmt for (figname, fignum) in figs.items()}
        pmagplotlib.saveP(figs, fnames)
        print(fnames)


if __name__ == "__main__":
    main()
