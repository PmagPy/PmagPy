#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import range
import sys
import os
import numpy
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.new_builder as nb


def main():
    """
    NAME
        quick_hyst.py

    DESCRIPTION
        makes plots of hysteresis data

    SYNTAX
        quick_hyst.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is measurements.txt
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    plots = 0
    pltspec = ""
    verbose = pmagplotlib.verbose
    #version_num = pmag.get_version()
    dir_path = pmag.get_named_arg_from_sys('-WD', '.')
    dir_path = os.path.realpath(dir_path)
    meas_file = pmag.get_named_arg_from_sys('-f', 'measurements.txt')
    fmt = pmag.get_named_arg_from_sys('-fmt', 'png')
    if '-sav' in args:
        verbose = 0
        plots = 1
    if '-spc' in args:
        ind = args.index("-spc")
        pltspec = args[ind+1]
        verbose = 0
        plots = 1
    #
    con = nb.Contribution(dir_path, read_tables=['measurements'],
                          custom_filenames={'measurements': meas_file})
    # get as much name data as possible (used for naming plots)
    if not 'measurements' in con.tables:
        print("-W- No measurement file found")
        return
    con.propagate_location_to_measurements()

    if 'measurements' not in con.tables:
        print(main.__doc__)
        print('bad file')
        sys.exit()
    meas_container = con.tables['measurements']
    #meas_df = meas_container.df

    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    HystRecs = []
    HDD = {}
    HDD['hyst'] = 1
    pmagplotlib.plot_init(HDD['hyst'], 5, 5)
    #
    # get list of unique experiment names and specimen names
    #
    sids = []
    hyst_data = meas_container.get_records_for_code('LP-HYS')
    #experiment_names = hyst_data['experiment_name'].unique()
    if not len(hyst_data):
        print("-W- No hysteresis data found")
        return
    sids = hyst_data['specimen'].unique()

    # if 'treat_temp' is provided, use that value, otherwise assume 300
    hyst_data['treat_temp'].where(hyst_data['treat_temp'].notnull(), '300', inplace=True)
    # start at first specimen, or at provided specimen ('-spc')
    k = 0
    if pltspec != "":
        try:
            print(sids)
            k = list(sids).index(pltspec)
        except ValueError:
            print('-W- No specimen named: {}.'.format(pltspec))
            print('-W- Please provide a valid specimen name')
            return
    intlist = ['magn_moment', 'magn_volume', 'magn_mass']

    while k < len(sids):
        locname, site, sample, synth = '', '', '', ''
        s = sids[k]
        if verbose:
            print(s, k + 1, 'out of ', len(sids))
        # B, M for hysteresis, Bdcd,Mdcd for irm-dcd data
        B, M = [], []
        # get all measurements for this specimen
        spec = hyst_data[hyst_data['specimen'] == s]
        # get names
        if 'location' in spec:
            locname = spec['location'][0]
        if 'site' in spec:
            site = spec['sample'][0]
        if 'sample' in spec:
            sample = spec['sample'][0]

        # get all records with non-blank values in any intlist column
        # find intensity data
        for int_column in intlist:
            if int_column in spec.columns:
                int_col = int_column
                break
        meas_data = spec[spec[int_column].notnull()]
        if len(meas_data) == 0:
            break
        #
        c = ['k-', 'b-', 'c-', 'g-', 'm-', 'r-', 'y-']
        cnum = 0
        Temps = []
        xlab, ylab, title = '', '', ''
        Temps = meas_data['treat_temp'].unique()
        for t in Temps:
            print('working on t: ', t)
            t_data = meas_data[meas_data['treat_temp'] == t]
            m = int_col
            B = t_data['meas_field_dc'].astype(float).values
            M = t_data[m].astype(float).values
            # now plot the hysteresis curve(s)
            #
            if len(B) > 0:
                B = numpy.array(B)
                M = numpy.array(M)
                if t == Temps[-1]:
                    xlab = 'Field (T)'
                    ylab = m
                    title = 'Hysteresis: ' + s
                if t == Temps[0]:
                    pmagplotlib.clearFIG(HDD['hyst'])
                pmagplotlib.plotXY(HDD['hyst'],B,M,sym=c[cnum],xlab=xlab,ylab=ylab,title=title)
                pmagplotlib.plotXY(HDD['hyst'],[1.1*B.min(),1.1*B.max()],[0,0],sym='k-',xlab=xlab,ylab=ylab,title=title)
                pmagplotlib.plotXY(HDD['hyst'],[0,0],[1.1*M.min(),1.1*M.max()],sym='k-',xlab=xlab,ylab=ylab,title=title)
                if verbose:
                    pmagplotlib.drawFIGS(HDD)
                cnum += 1
                if cnum == len(c):
                    cnum = 0
  #
        files = {}
        if plots:
            if pltspec != "":
                s = pltspec
            for key in list(HDD.keys()):
                if pmagplotlib.isServer:
                    if synth == '':
                        files[key] = "LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                    else:
                        files[key] = 'SY:_'+synth+'_TY:_'+key+'_.'+fmt
                else:
                    if synth == '':
                        filename = ''
                        for item in [locname, site, sample, s, key]:
                            if item:
                                item = item.replace(' ', '_')
                                filename += item + '_'
                        if filename.endswith('_'):
                            filename = filename[:-1]
                        filename += ".{}".format(fmt)
                        files[key] = filename
                    else:
                        files[key] = "{}_{}.{}".format(synth, key, fmt)

            pmagplotlib.saveP(HDD, files)
            if pltspec != "":
                sys.exit()
        if verbose:
            pmagplotlib.drawFIGS(HDD)
            ans = input("S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans == "a":
                files = {}
                for key in list(HDD.keys()):
                    if pmagplotlib.isServer: # use server plot naming convention
                        files[key] = "LO:_"+locname+'_SI:_'+site+'_SA:_'+sample+'_SP:_'+s+'_TY:_'+key+'_.'+fmt
                    else: # use more readable plot naming convention
                        filename = ''
                        for item in [locname, site, sample, s, key]:
                            if item:
                                item = item.replace(' ', '_')
                                filename += item + '_'
                        if filename.endswith('_'):
                            filename = filename[:-1]
                        filename += ".{}".format(fmt)
                        files[key] = filename

                pmagplotlib.saveP(HDD, files)
            if ans == '':
                k += 1
            if ans == "p":
                del HystRecs[-1]
                k -= 1
            if ans == 'q':
                print("Good bye")
                sys.exit()
            if ans == 's':
                keepon = 1
                specimen = input('Enter desired specimen name (or first part there of): ')
                while keepon == 1:
                    try:
                        k = sids.index(specimen)
                        keepon = 0
                    except:
                        tmplist = []
                        for qq in range(len(sids)):
                            if specimen in sids[qq]:
                                tmplist.append(sids[qq])
                        print(specimen, " not found, but this was: ")
                        print(tmplist)
                        specimen = input('Select one or try again\n ')
                        k = sids.index(specimen)
        else:
            k += 1
        if len(B) == 0:
            if verbose:
                print('skipping this one - no hysteresis data')
            k += 1

if __name__ == "__main__":
    main()
