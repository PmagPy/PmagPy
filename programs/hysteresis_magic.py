#!/usr/bin/env python
# -*- python-indent-offset: 4; -*-

import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.pmag as pmag
import pmagpy.contribution_builder as cb
from pmag_env import set_env


def main():
    """
    NAME
        hysteresis_magic.py

    DESCRIPTION
        calculates hystereis parameters and saves them in 3.0 specimen format file
        makes plots if option selected

    SYNTAX
        hysteresis_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specify input file, default is agm_measurements.txt
        -F: specify specimens.txt output file
        -P: do not make the plots
        -spc SPEC: specify specimen name to plot and quit
        -sav save all plots and quit
        -fmt [png,svg,eps,jpg]
    """
    args = sys.argv
    PLT = 1
    plots = 0
    fmt = pmag.get_named_arg('-fmt', 'svg')
    dir_path = pmag.get_named_arg('-WD', '.')
    dir_path = os.path.realpath(dir_path)
    verbose = pmagplotlib.verbose
    version_num = pmag.get_version()
    user = pmag.get_named_arg('-usr', '')
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    meas_file = pmag.get_named_arg('-f', 'agm_measurements.txt')
    spec_file = pmag.get_named_arg('-F', 'specimens.txt')
    if '-P' in args:
        PLT = 0
        irm_init, imag_init = -1, -1
    if '-sav' in args:
        verbose = 0
        plots = 1
    pltspec = pmag.get_named_arg('-spc', 0)
    if pltspec:
        #pltspec= args[ind+1]
        verbose = 0
        plots = 1
    spec_file = dir_path+'/'+spec_file
    meas_file = dir_path+'/'+meas_file
    SpecRecs = []
    #
    #
    meas_data, file_type = pmag.magic_read(meas_file)
    if file_type != 'measurements':
        print(main.__doc__)
        print('bad file')
        sys.exit()
    #
    # initialize some variables
    # define figure numbers for hyst,deltaM,DdeltaM curves
    HystRecs, RemRecs = [], []
    HDD = {}
    if verbose:
        if verbose and PLT:
            print("Plots may be on top of each other - use mouse to place ")
    if PLT:
        HDD['hyst'], HDD['deltaM'], HDD['DdeltaM'] = 1, 2, 3
        pmagplotlib.plot_init(HDD['DdeltaM'], 5, 5)
        pmagplotlib.plot_init(HDD['deltaM'], 5, 5)
        pmagplotlib.plot_init(HDD['hyst'], 5, 5)
        imag_init = 0
        irm_init = 0
    else:
        HDD['hyst'], HDD['deltaM'], HDD['DdeltaM'], HDD['irm'], HDD['imag'] = 0, 0, 0, 0, 0
    #
    if spec_file:
        prior_data, file_type = pmag.magic_read(spec_file)
    #
    # get list of unique experiment names and specimen names
    #
    experiment_names, sids = [], []
    hys_data = pmag.get_dictitem(meas_data, 'method_codes', 'LP-HYS', 'has')
    dcd_data = pmag.get_dictitem(
        meas_data, 'method_codes', 'LP-IRM-DCD', 'has')
    imag_data = pmag.get_dictitem(meas_data, 'method_codes', 'LP-IMAG', 'has')
    for rec in hys_data:
        if rec['experiment'] not in experiment_names:
            experiment_names.append(rec['experiment'])
        if rec['specimen'] not in sids:
            sids.append(rec['specimen'])
    #
    k = 0
    if pltspec:
        k = sids.index(pltspec)
        print(sids[k])
    while k < len(sids):
        specimen = sids[k]
        # initialize a new specimen hysteresis record
        HystRec = {'specimen': specimen, 'experiment': ""}
        if verbose and PLT:
            print(specimen, k+1, 'out of ', len(sids))
    #
    #
        # B,M for hysteresis, Bdcd,Mdcd for irm-dcd data
        B, M, Bdcd, Mdcd = [], [], [], []
        Bimag, Mimag = [], []  # Bimag,Mimag for initial magnetization curves
        # fish out all the LP-HYS data for this specimen
        spec_data = pmag.get_dictitem(hys_data, 'specimen', specimen, 'T')
        if len(spec_data) > 0:
            meths = spec_data[0]['method_codes'].split(':')
            e = spec_data[0]['experiment']
            HystRec['experiment'] = spec_data[0]['experiment']
            for rec in spec_data:
                B.append(float(rec['meas_field_dc']))
                M.append(float(rec['magn_moment']))
        # fish out all the data for this specimen
        spec_data = pmag.get_dictitem(dcd_data, 'specimen', specimen, 'T')
        if len(spec_data) > 0:
            HystRec['experiment'] = HystRec['experiment'] + \
                ':'+spec_data[0]['experiment']
            irm_exp = spec_data[0]['experiment']
            for rec in spec_data:
                Bdcd.append(float(rec['treat_dc_field']))
                Mdcd.append(float(rec['magn_moment']))
        # fish out all the data for this specimen
        spec_data = pmag.get_dictitem(imag_data, 'specimen', specimen, 'T')
        if len(spec_data) > 0:
            imag_exp = spec_data[0]['experiment']
            for rec in spec_data:
                Bimag.append(float(rec['meas_field_dc']))
                Mimag.append(float(rec['magn_moment']))
    #
    # now plot the hysteresis curve
    #
        if len(B) > 0:
            hmeths = []
            for meth in meths:
                hmeths.append(meth)

            hpars = pmagplotlib.plot_hdd(HDD, B, M, e)
            if verbose and PLT:
                if not set_env.IS_WIN:
                    pmagplotlib.draw_figs(HDD)
    #
            if verbose:
                pmagplotlib.plot_hpars(HDD, hpars, 'bs')
            HystRec['hyst_mr_moment'] = hpars['hysteresis_mr_moment']
            HystRec['hyst_ms_moment'] = hpars['hysteresis_ms_moment']
            HystRec['hyst_bc'] = hpars['hysteresis_bc']
            HystRec['hyst_bcr'] = hpars['hysteresis_bcr']
            HystRec['hyst_xhf'] = hpars['hysteresis_xhf']
            HystRec['experiments'] = e
            HystRec['software_packages'] = version_num
            if hpars["magic_method_codes"] not in hmeths:
                hmeths.append(hpars["magic_method_codes"])
            methods = ""
            for meth in hmeths:
                methods = methods+meth.strip()+":"
            HystRec["method_codes"] = methods[:-1]
            HystRec["citations"] = "This study"
    #
        if len(Bdcd) > 0:
            rmeths = []
            for meth in meths:
                rmeths.append(meth)
            if verbose and PLT:
                print('plotting IRM')
            if irm_init == 0:
                HDD['irm'] = 5 if 'imag' in HDD else 4
                pmagplotlib.plot_init(HDD['irm'], 5, 5)
                irm_init = 1
            rpars = pmagplotlib.plot_irm(HDD['irm'], Bdcd, Mdcd, irm_exp)
            HystRec['rem_mr_moment'] = rpars['remanence_mr_moment']
            HystRec['rem_bcr'] = rpars['remanence_bcr']
            HystRec['experiments'] = specimen+':'+irm_exp
            if rpars["magic_method_codes"] not in meths:
                meths.append(rpars["magic_method_codes"])
            methods = ""
            for meth in rmeths:
                methods = methods+meth.strip()+":"
            HystRec["method_codes"] = HystRec['method_codes']+':'+methods[:-1]
            HystRec["citations"] = "This study"
        else:
            if irm_init:
                pmagplotlib.clearFIG(HDD['irm'])
        if len(Bimag) > 0:
            if verbose and PLT:
                print('plotting initial magnetization curve')
# first normalize by Ms
            Mnorm = []
            for m in Mimag:
                Mnorm.append(m / float(hpars['hysteresis_ms_moment']))
            if imag_init == 0:
                HDD['imag'] = 4
                pmagplotlib.plot_init(HDD['imag'], 5, 5)
                imag_init = 1
            pmagplotlib.plot_imag(HDD['imag'], Bimag, Mnorm, imag_exp)
        else:
            if imag_init:
                pmagplotlib.clearFIG(HDD['imag'])
        if len(list(HystRec.keys())) > 0:
            HystRecs.append(HystRec)
    #
        files = {}
        if plots:
            if pltspec:
                s = pltspec
            else:
                s = specimen
            files = {}
            for key in list(HDD.keys()):
                files[key] = s+'_'+key+'.'+fmt
            pmagplotlib.save_plots(HDD, files)
            if pltspec:
                sys.exit()
        if verbose and PLT:
            pmagplotlib.draw_figs(HDD)
            ans = input(
                "S[a]ve plots, [s]pecimen name, [q]uit, <return> to continue\n ")
            if ans == "a":
                files = {}
                for key in list(HDD.keys()):
                    files[key] = specimen+'_'+key+'.'+fmt
                pmagplotlib.save_plots(HDD, files)
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
                specimen = input(
                    'Enter desired specimen name (or first part there of): ')
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
        if len(B) == 0 and len(Bdcd) == 0:
            if verbose:
                print('skipping this one - no hysteresis data')
            k += 1
        if k < len(sids):
            # must re-init figs for Windows to keep size
            if PLT and set_env.IS_WIN:
                pmagplotlib.plot_init(HDD['DdeltaM'], 5, 5)
                pmagplotlib.plot_init(HDD['deltaM'], 5, 5)
                pmagplotlib.plot_init(HDD['hyst'], 5, 5)
                if len(Bimag) > 0:
                    HDD['imag'] = 4
                    pmagplotlib.plot_init(HDD['imag'], 5, 5)
                if len(Bdcd) > 0:
                    HDD['irm'] = 5 if 'imag' in HDD else 4
                    pmagplotlib.plot_init(HDD['irm'], 5, 5)
            elif not PLT and set_env.IS_WIN:
                HDD['hyst'], HDD['deltaM'], HDD['DdeltaM'], HDD['irm'], HDD['imag'] = 0, 0, 0, 0, 0
    if len(HystRecs) > 0:
        #  go through prior_data, clean out prior results and save combined file as spec_file
        SpecRecs, keys = [], list(HystRecs[0].keys())
        if len(prior_data) > 0:
            prior_keys = list(prior_data[0].keys())
        else:
            prior_keys = []
        for rec in prior_data:
            for key in keys:
                if key not in list(rec.keys()):
                    rec[key] = ""
            if 'LP-HYS' not in rec['method_codes']:
                SpecRecs.append(rec)
        for rec in HystRecs:
            for key in prior_keys:
                if key not in list(rec.keys()):
                    rec[key] = ""
            prior = pmag.get_dictitem(
                prior_data, 'specimen', rec['specimen'], 'T')
            if len(prior) > 0 and 'sample' in list(prior[0].keys()):
                # pull sample name from prior specimens table
                rec['sample'] = prior[0]['sample']
            SpecRecs.append(rec)
        # drop unnecessary/duplicate rows
        dir_path = os.path.split(spec_file)[0]
        con = cb.Contribution(dir_path, read_tables=[])
        con.add_magic_table_from_data('specimens', SpecRecs)
        con.tables['specimens'].drop_duplicate_rows(
            ignore_cols=['specimen', 'sample', 'citations', 'software_packages'])
        con.tables['specimens'].df = con.tables['specimens'].df.drop_duplicates()
        con.write_table_to_file('specimens', custom_name=spec_file)
        # old way:
        # pmag.magic_write(spec_file,SpecRecs,"specimens")
        if verbose:
            print("hysteresis parameters saved in ", spec_file)


if __name__ == "__main__":
    main()
