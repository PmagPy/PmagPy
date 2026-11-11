#!/usr/bin/env python
import sys
from pmag_env import set_env
set_env.set_backend_if_unset("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib


def main():
    """
    NAME
        lowrie_magic.py

    DESCRIPTION
       plots intensity decay curves for Lowrie experiments

    SYNTAX
        lowrie_magic.py -h [command line options]

    INPUT
       takes measurements formatted input files

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is measurements.txt
        -N do not normalize by maximum magnetization
        -fmt [svg, pdf, eps, png] specify fmt, default is svg
        -sav saves plots and quits
        -DM [3] MagIC data model number
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if len(sys.argv) <= 1:
        print(main.__doc__)
        print('you must supply a file name')
        sys.exit()
    data_model = int(float(pmag.get_named_arg("-DM", 3)))
    if data_model != 3:
        raise SystemExit(
            "-E- lowrie_magic supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before plotting."
        )
    FIG = {}  # plot dictionary
    FIG['lowrie'] = 1  # demag is figure 1
    pmagplotlib.plot_init(FIG['lowrie'], 6, 6)
    norm = 1  # default is to normalize by maximum axis
    in_file = pmag.get_named_arg("-f", "measurements.txt")
    dir_path = pmag.get_named_arg("-WD", ".")
    in_file = pmag.resolve_file_name(in_file, dir_path)
    fmt = pmag.get_named_arg("-fmt", "svg")
    if '-N' in sys.argv:
        norm = 0  # don't normalize
    if '-sav' in sys.argv:
        plot = 1  # silently save and quit
    else:
        plot = 0 # generate plots
    print(in_file)
    # read in data
    PmagRecs, file_type = pmag.magic_read(in_file)
    if file_type != "measurements":
        print('bad input file', file_type)
        sys.exit()

    meth_code_col = 'method_codes'
    spec_col = 'specimen'
    dec_col = 'dir_dec'
    inc_col = 'dir_inc'
    moment_col = 'magn_moment'
    temp_col = "treat_temp"

    PmagRecs = pmag.get_dictitem(
        PmagRecs, meth_code_col, 'LP-IRM-3D', 'has')  # get all 3D IRM records

    if len(PmagRecs) == 0:
        print('no records found with the method code LP-IRM-3D')
        sys.exit()

    specs = pmag.get_dictkey(PmagRecs, spec_col, '')
    sids = []
    for spec in specs:
        if spec not in sids:
            sids.append(spec)  # get list of unique specimen names
    for spc in sids:  # step through the specimen names
        print(spc)
        specdata = pmag.get_dictitem(
            PmagRecs, spec_col, spc, 'T')  # get all this one's data

        DIMs, Temps = [], []
        for dat in specdata:  # step through the data
            DIMs.append([float(dat[dec_col]), float(
                dat[inc_col]), float(dat[moment_col])])
            Temps.append(float(dat[temp_col])-273.)
        carts = pmag.dir2cart(DIMs).transpose()
        if norm == 1:  # want to normalize
            nrm = (DIMs[0][2])  # normalize by NRM
            ylab = "M/M_o"
        else:
            nrm = 1.  # don't normalize
            ylab = "Magnetic moment (Am^2)"
        xlab = "Temperature (C)"
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[0]) / nrm, sym='r-')
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[0]) / nrm, sym='ro')  # X direction
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[1]) / nrm, sym='c-')
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[1]) / nrm, sym='cs')  # Y direction
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[2]) / nrm, sym='k-')
        pmagplotlib.plot_xy(FIG['lowrie'], Temps, abs(carts[2]) / nrm, sym='k^', title=spc, xlab=xlab, ylab=ylab)  # Z direction
        files = {'lowrie': 'lowrie:_'+spc+'_.'+fmt}
        if plot == 0:
            pmagplotlib.draw_figs(FIG)
            ans = input('S[a]ve figure? [q]uit, <return> to continue   ')
            if ans == 'a':
                pmagplotlib.save_plots(FIG, files)
            elif ans == 'q':
                sys.exit()
        else:
            pmagplotlib.save_plots(FIG, files)
        pmagplotlib.clearFIG(FIG['lowrie'])


if __name__ == "__main__":
    main()
