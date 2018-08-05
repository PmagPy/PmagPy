#!/usr/bin/env python
import sys
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")
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
        -f FILE, specify magic_measurements format file
        -T IND, specify temperature step to plot
        -e EXP, specify experiment name to plot
        -fmt [svg,jpg,png,pdf] set figure format [default is svg]
        -sav save figure and quit

    DEFAULTS
         FILE: magic_measurements.txt
         IND: first
         SPEC: step through one by one
    """
    cont, FTinit, BTinit, k = "", 0, 0, 0
    meas_file = "magic_measurements.txt"
    spec = ""
    Tind, cont = 0, ""
    EXP = ""
    fmt = 'svg'  # default image type for saving
    plot = 0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-i' in sys.argv:
        fname = input(
            "Input magic_measurements file name? [magic_measurements.txt]  ")
        if fname != "":
            meas_file = fname
    if '-e' in sys.argv:
        ind = sys.argv.index('-e')
        EXP = sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        meas_file = sys.argv[ind+1]
    if '-T' in sys.argv:
        ind = sys.argv.index('-T')
        Tind = int(sys.argv[ind+1])
    if '-fmt' in sys.argv:
        ind = sys.argv.index('-fmt')
        fmt = sys.argv[ind+1]
    if '-sav' in sys.argv:
        plot = 1
    #
    meas_data, file_type = pmag.magic_read(meas_file)
    #
    # get list of unique experiment names
    #
    # initialize some variables (a continuation flag, plot initialization flags and the experiment counter
    experiment_names = []
    for rec in meas_data:
        if rec['magic_experiment_name'] not in experiment_names:
            experiment_names.append(rec['magic_experiment_name'])
    #
    # hunt through by experiment name
    if EXP != "":
        try:
            k = experiment_names.index(EXP)
        except:
            print("Bad experiment name")
            sys.exit()
    while k < len(experiment_names):
        e = experiment_names[k]
        if EXP == "":
            print(e, k+1, 'out of ', len(experiment_names))
    #
    #  initialize lists of data, susceptibility, temperature, frequency and field
        X, T, F, B = [], [], [], []
        for rec in meas_data:
            methcodes = rec['magic_method_codes']
            meths = methcodes.strip().split(':')
            if rec['magic_experiment_name'] == e and "LP-X" in meths:  # looking for chi measurement
                if 'measurement_temp' not in list(rec.keys()):
                    rec['measurement_temp'] = '300'  # set defaults
                if 'measurement_freq' not in list(rec.keys()):
                    rec['measurement_freq'] = '0'  # set defaults
                if 'measurement_lab_field_ac' not in list(rec.keys()):
                    rec['measurement_lab_field_ac'] = '0'  # set default
                if 'measurement_x' in rec.keys():
                    # backward compatibility
                    X.append(float(rec['measurement_x']))
                else:
                    # data model 2.5
                    X.append(float(rec['measurement_chi_volume']))
                T.append(float(rec['measurement_temp']))
                F.append(float(rec['measurement_freq']))
                B.append(float(rec['measurement_lab_field_ac']))
    #
    # get unique list of Ts,Fs, and Bs
    #
        Ts, Fs, Bs = [], [], []
        for k in range(len(X)):   # hunt through all the measurements
            if T[k] not in Ts:
                Ts.append(T[k])  # append if not in list
            if F[k] not in Fs:
                Fs.append(F[k])
            if B[k] not in Bs:
                Bs.append(B[k])
        Ts.sort()  # sort list of temperatures, frequencies and fields
        Fs.sort()
        Bs.sort()
        if '-x' in sys.argv:
            k = len(experiment_names)+1  # just plot the one
        else:
            k += 1  # increment experiment number
    #
    # plot chi versus T and F holding B constant
    #
        plotnum = 1  # initialize plot number to 1
        if len(X) > 2:  # if there are any data to plot, continue
            b = Bs[-1]  # keeping field constant and at maximum
            XTF = []  # initialize list of chi versus Temp and freq
            for f in Fs:   # step through frequencies sequentially
                XT = []  # initialize list of chi versus temp
                for kk in range(len(X)):  # hunt through all the data
                    if F[kk] == f and B[kk] == b:  # select data with given freq and field
                        XT.append([X[kk], T[kk]])  # append to list
                XTF.append(XT)  # append list to list of frequencies
            if len(XT) > 1:  # if there are any temperature dependent data
                pmagplotlib.plot_init(plotnum, 5, 5)  # initialize plot
                # call the plotting function
                pmagplotlib.plot_xtf(plotnum, XTF, Fs, e, b)
                if plot == 0:
                    pmagplotlib.draw_figs({'fig': plotnum})  # make it visible
                plotnum += 1  # increment plot number
            f = Fs[0]  # set frequency to minimum
            XTB = []  # initialize list if chi versus Temp and field
            for b in Bs:  # step through field values
                XT = []  # initial chi versus temp list for this field
                for kk in range(len(X)):  # hunt through all the data
                    if F[kk] == f and B[kk] == b:  # select data with given freq and field
                        XT.append([X[kk], T[kk]])  # append to list
                XTB.append(XT)
            if len(XT) > 1:  # if there are any temperature dependent data
                pmagplotlib.plot_init(plotnum, 5, 5)  # set up plot
                # call the plotting function
                pmagplotlib.plot_xtb(plotnum, XTB, Bs, e, f)
                if plot == 0:
                    pmagplotlib.draw_figs({'fig': plotnum})
                plotnum += 1  # increment plot number
            if '-i' in sys.argv:
                for ind in range(len(Ts)):  # print list of temperatures available
                    print(ind, int(Ts[ind]))
                cont = input(
                    "Enter index of desired temperature step, s[a]ve plots, [return] to quit ")
                if cont == 'a':
                    files = {}
                    PLTS = {}
                    for p in range(1, plotnum):
                        key = str(p)
                        files[key] = e+'_'+key+'.'+fmt
                        PLTS[key] = key
                    pmagplotlib.save_plots(PLTS, files)
                    cont = input(
                        "Enter index of desired temperature step, s[a]ve plots, [return] to quit ")
                if cont == "":
                    cont = 'q'
            while cont != "q":
                if '-i' in sys.argv:
                    Tind = int(cont)  # set temperature index
                b = Bs[-1]  # set field to max available
                XF = []  # initial chi versus frequency list
                for kk in range(len(X)):  # hunt through the data
                    if T[kk] == Ts[Tind] and B[kk] == b:  # if temperature and field match,
                        XF.append([X[kk], F[kk]])  # append the data
                if len(XF) > 1:  # if there are any data to plot
                    if FTinit == 0:  # if not already initialized, initialize plot
                        # print 'initializing ',plotnum
                        pmagplotlib.plot_init(plotnum, 5, 5)
                        FTinit = 1
                        XFplot = plotnum
                        plotnum += 1  # increment plotnum
                    pmagplotlib.plot_xft(XFplot, XF, Ts[Tind], e, b)
                    if plot == 0:
                        pmagplotlib.draw_figs({'fig': plotnum})
                else:
                    print(
                        '\n *** Skipping susceptibitily-frequency plot as a function of temperature *** \n')
                f = Fs[0]  # set frequency to minimum available
                XB = []  # initialize chi versus field list
                for kk in range(len(X)):  # hunt through the data
                    # if temperature and field match those desired
                    if T[kk] == Ts[Tind] and F[kk] == f:
                        XB.append([X[kk], B[kk]])  # append the data to list
                if len(XB) > 4:  # if there are any data
                    if BTinit == 0:  # if plot not already initialized
                        pmagplotlib.plot_init(plotnum, 5, 5)  # do it
                        BTinit = 1
                    # and call plotting function
                    pmagplotlib.plot_xbt(plotnum, XB, Ts[Tind], e, f)
                    if plot == 0:
                        pmagplotlib.draw_figs({'fig': plotnum})
                else:
                    print(
                        'Skipping susceptibitily - AC field plot as a function of temperature')
                files = {}
                PLTS = {}
                for p in range(1, plotnum):
                    key = str(p)
                    files[key] = e+'_'+key+'.'+fmt
                    PLTS[key] = p
                if '-i' in sys.argv:
                    # just in case you forgot, print out a new list of temperatures
                    for ind in range(len(Ts)):
                        print(ind, int(Ts[ind]))
                    # ask for new temp
                    cont = input(
                        "Enter index of next temperature step, s[a]ve plots,  [return] to quit ")
                    if cont == "":
                        sys.exit()
                    if cont == 'a':
                        pmagplotlib.save_plots(PLTS, files)
                        cont = input(
                            "Enter index of desired temperature step, s[a]ve plots, [return] to quit ")
                        if cont == "":
                            sys.exit()
                elif plot == 0:
                    ans = input(
                        "enter s[a]ve to save files,  [return] to quit ")
                    if ans == 'a':
                        pmagplotlib.save_plots(PLTS, files)
                        sys.exit()
                    else:
                        sys.exit()
                else:
                    pmagplotlib.save_plots(PLTS, files)
                    sys.exit()


if __name__ == "__main__":
    main()
