#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.contribution_builder as cb


def main():
    """
    NAME
        eqarea_magic.py

    DESCRIPTION
       makes equal area projections from declination/inclination data

    SYNTAX
        eqarea_magic.py [command line options]

    INPUT
       takes magic formatted sites, samples, specimens, or measurements

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file from magic, default='sites.txt'
         supported types=[measurements, specimens, samples, sites]
        -fsp FILE: specify specimen file name, (required if you want to plot measurements by sample)
                default='specimens.txt'
        -fsa FILE: specify sample file name, (required if you want to plot specimens by site)
                default='samples.txt'
        -fsi FILE: specify site file name, default='sites.txt'
        -flo FILE: specify location file name, default='locations.txt'

        -obj OBJ: specify  level of plot  [all, sit, sam, spc], default is all
        -crd [s,g,t]: specify coordinate system, [s]pecimen, [g]eographic, [t]ilt adjusted
                default is geographic, unspecified assumed geographic
        -fmt [svg,png,jpg] format for output plots
        -ell [F,K,B,Be,Bv] plot Fisher, Kent, Bingham, Bootstrap ellipses or Boostrap eigenvectors
        -c plot as colour contour
        -cm CM use color map CM [default is coolwarm]
        -sav save plot and quit quietly
        -no-tilt data are unoriented, allows plotting of measurement dec/inc
    NOTE
        all: entire file; sit: site; sam: sample; spc: specimen
    """
    # initialize some default variables
    FIG = {}  # plot dictionary
    FIG['eqarea'] = 1  # eqarea is figure 1
    plotE = 0
    plt = 0  # default to not plotting
    verbose = pmagplotlib.verbose
    # extract arguments from sys.argv
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", default_val=".")
    pmagplotlib.plot_init(FIG['eqarea'], 5, 5)
    in_file = pmag.get_named_arg("-f", default_val="sites.txt")
    in_file = pmag.resolve_file_name(in_file, dir_path)
    if "-WD" not in sys.argv:
        dir_path = os.path.split(in_file)[0]
    #full_in_file = os.path.join(dir_path, in_file)
    plot_by = pmag.get_named_arg("-obj", default_val="all").lower()
    spec_file = pmag.get_named_arg("-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg("-fsi", default_val="sites.txt")
    loc_file = pmag.get_named_arg("-flo", default_val="locations.txt")
    ignore_tilt = False
    if '-no-tilt' in sys.argv:
        ignore_tilt = True
    if plot_by == 'all':
        plot_key = 'all'
    elif plot_by == 'sit':
        plot_key = 'site'
    elif plot_by == 'sam':
        plot_key = 'sample'
    elif plot_by == 'spc':
        plot_key = 'specimen'
    else:
        plot_by = 'all'
        plot_key = 'all'
    if '-c' in sys.argv:
        contour = 1
        if '-cm' in sys.argv:
            ind = sys.argv.index('-cm')
            color_map = sys.argv[ind+1]
        else:
            color_map = 'coolwarm'
    else:
        contour = 0
    if '-sav' in sys.argv:
        plt = 1
        verbose = 0
    if '-ell' in sys.argv:
        plotE = 1
        ind = sys.argv.index('-ell')
        ell_type = sys.argv[ind+1]
        ell_type = pmag.get_named_arg("-ell", "F")
        dist = ell_type.upper()
        # if dist type is unrecognized, use Fisher
        if dist not in ['F', 'K', 'B', 'BE', 'BV']:
            dist = 'F'
        if dist == "BV":
            FIG['bdirs'] = 2
            pmagplotlib.plot_init(FIG['bdirs'], 5, 5)
    crd = pmag.get_named_arg("-crd", default_val="g")
    if crd == "s":
        coord = "-1"
    elif crd == "t":
        coord = "100"
    else:
        coord = "0"

    fmt = pmag.get_named_arg("-fmt", "svg")

    dec_key = 'dir_dec'
    inc_key = 'dir_inc'
    tilt_key = 'dir_tilt_correction'
    # Dir_type_keys=['','site_direction_type','sample_direction_type','specimen_direction_type']

    #
    fnames = {"specimens": spec_file, "samples": samp_file,
              'sites': site_file, 'locations': loc_file}
    contribution = cb.Contribution(dir_path, custom_filenames=fnames,
                                   single_file=in_file)

    try:
        contribution.propagate_location_to_samples()
        contribution.propagate_location_to_specimens()
        contribution.propagate_location_to_measurements()
    except KeyError as ex:
        pass

    # the object that contains the DataFrame + useful helper methods:
    table_name = list(contribution.tables.keys())[0]
    data_container = contribution.tables[table_name]
    # the actual DataFrame:
    data = data_container.df

    if plot_key != "all" and plot_key not in data.columns:
        print("-E- You can't plot by {} with the data provided".format(plot_key))
        return

    # add tilt key into DataFrame columns if it isn't there already
    if tilt_key not in data.columns:
        data.loc[:, tilt_key] = None

    if verbose:
        print(len(data), ' records read from ', in_file)

    # find desired dec,inc data:
    dir_type_key = ''
    #
    # get plotlist if not plotting all records
    #
    plotlist = []
    if plot_key != "all":
        # return all where plot_key is not blank
        if plot_key not in data.columns:
            print('Can\'t plot by "{}".  That header is not in infile: {}'.format(
                plot_key, in_file))
            return
        plots = data[data[plot_key].notnull()]
        plotlist = plots[plot_key].unique()  # grab unique values
    else:
        plotlist.append('All')

    for plot in plotlist:
        if verbose:
            print(plot)
        if plot == 'All':
            # plot everything at once
            plot_data = data
        else:
            # pull out only partial data
            plot_data = data[data[plot_key] == plot]

        DIblock = []
        GCblock = []
        # SLblock, SPblock = [], []
        title = plot
        mode = 1
        k = 0

        if dec_key not in plot_data.columns:
            print("-W- No dec/inc data")
            continue
        # get all records where dec & inc values exist
        plot_data = plot_data[plot_data[dec_key].notnull()
                              & plot_data[inc_key].notnull()]
        if plot_data.empty:
            continue
        # this sorting out is done in get_di_bock
        # if coord == '0':  # geographic, use records with no tilt key (or tilt_key 0)
        #    cond1 = plot_data[tilt_key].fillna('') == coord
        #    cond2 = plot_data[tilt_key].isnull()
        #    plot_data = plot_data[cond1 | cond2]
        # else:  # not geographic coordinates, use only records with correct tilt_key
        #    plot_data = plot_data[plot_data[tilt_key] == coord]

        # get metadata for naming the plot file
        locations = data_container.get_name('location', df_slice=plot_data)
        site = data_container.get_name('site', df_slice=plot_data)
        sample = data_container.get_name('sample', df_slice=plot_data)
        specimen = data_container.get_name('specimen', df_slice=plot_data)

        # make sure method_codes is in plot_data
        if 'method_codes' not in plot_data.columns:
            plot_data['method_codes'] = ''

        # get data blocks
        # would have to ignore tilt to use measurement level data
        DIblock = data_container.get_di_block(df_slice=plot_data,
                                              tilt_corr=coord, excl=['DE-BFP'], ignore_tilt=ignore_tilt)
        #SLblock = [[ind, row['method_codes']] for ind, row in plot_data.iterrows()]
        # get great circles
        great_circle_data = data_container.get_records_for_code('DE-BFP', incl=True,
                                                                use_slice=True, sli=plot_data)

        if len(great_circle_data) > 0:
            gc_cond = great_circle_data[tilt_key] == coord
            GCblock = [[float(row[dec_key]), float(row[inc_key])]
                       for ind, row in great_circle_data[gc_cond].iterrows()]
            #SPblock = [[ind, row['method_codes']] for ind, row in great_circle_data[gc_cond].iterrows()]

        if len(DIblock) > 0:
            if contour == 0:
                pmagplotlib.plot_eq(FIG['eqarea'], DIblock, title)
            else:
                pmagplotlib.plot_eq_cont(
                    FIG['eqarea'], DIblock, color_map=color_map)
        else:
            pmagplotlib.plot_net(FIG['eqarea'])
        if len(GCblock) > 0:
            for rec in GCblock:
                pmagplotlib.plot_circ(FIG['eqarea'], rec, 90., 'g')
        if len(DIblock) == 0 and len(GCblock) == 0:
            if verbose:
                print("no records for plotting")
            continue
            # sys.exit()
        if plotE == 1:
            ppars = pmag.doprinc(DIblock)  # get principal directions
            nDIs, rDIs, npars, rpars = [], [], [], []
            for rec in DIblock:
                angle = pmag.angle([rec[0], rec[1]], [
                                   ppars['dec'], ppars['inc']])
                if angle > 90.:
                    rDIs.append(rec)
                else:
                    nDIs.append(rec)
            if dist == 'B':  # do on whole dataset
                etitle = "Bingham confidence ellipse"
                bpars = pmag.dobingham(DIblock)
                for key in list(bpars.keys()):
                    if key != 'n' and verbose:
                        print("    ", key, '%7.1f' % (bpars[key]))
                    if key == 'n' and verbose:
                        print("    ", key, '       %i' % (bpars[key]))
                npars.append(bpars['dec'])
                npars.append(bpars['inc'])
                npars.append(bpars['Zeta'])
                npars.append(bpars['Zdec'])
                npars.append(bpars['Zinc'])
                npars.append(bpars['Eta'])
                npars.append(bpars['Edec'])
                npars.append(bpars['Einc'])
            if dist == 'F':
                etitle = "Fisher confidence cone"
                if len(nDIs) > 2:
                    fpars = pmag.fisher_mean(nDIs)
                    for key in list(fpars.keys()):
                        if key != 'n' and verbose:
                            print("    ", key, '%7.1f' % (fpars[key]))
                        if key == 'n' and verbose:
                            print("    ", key, '       %i' % (fpars[key]))
                    mode += 1
                    npars.append(fpars['dec'])
                    npars.append(fpars['inc'])
                    npars.append(fpars['alpha95'])  # Beta
                    npars.append(fpars['dec'])
                    isign = abs(fpars['inc']) / fpars['inc']
                    npars.append(fpars['inc']-isign*90.)  # Beta inc
                    npars.append(fpars['alpha95'])  # gamma
                    npars.append(fpars['dec']+90.)  # Beta dec
                    npars.append(0.)  # Beta inc
                if len(rDIs) > 2:
                    fpars = pmag.fisher_mean(rDIs)
                    if verbose:
                        print("mode ", mode)
                    for key in list(fpars.keys()):
                        if key != 'n' and verbose:
                            print("    ", key, '%7.1f' % (fpars[key]))
                        if key == 'n' and verbose:
                            print("    ", key, '       %i' % (fpars[key]))
                    mode += 1
                    rpars.append(fpars['dec'])
                    rpars.append(fpars['inc'])
                    rpars.append(fpars['alpha95'])  # Beta
                    rpars.append(fpars['dec'])
                    isign = abs(fpars['inc']) / fpars['inc']
                    rpars.append(fpars['inc']-isign*90.)  # Beta inc
                    rpars.append(fpars['alpha95'])  # gamma
                    rpars.append(fpars['dec']+90.)  # Beta dec
                    rpars.append(0.)  # Beta inc
            if dist == 'K':
                etitle = "Kent confidence ellipse"
                if len(nDIs) > 3:
                    kpars = pmag.dokent(nDIs, len(nDIs))
                    if verbose:
                        print("mode ", mode)
                    for key in list(kpars.keys()):
                        if key != 'n' and verbose:
                            print("    ", key, '%7.1f' % (kpars[key]))
                        if key == 'n' and verbose:
                            print("    ", key, '       %i' % (kpars[key]))
                    mode += 1
                    npars.append(kpars['dec'])
                    npars.append(kpars['inc'])
                    npars.append(kpars['Zeta'])
                    npars.append(kpars['Zdec'])
                    npars.append(kpars['Zinc'])
                    npars.append(kpars['Eta'])
                    npars.append(kpars['Edec'])
                    npars.append(kpars['Einc'])
                if len(rDIs) > 3:
                    kpars = pmag.dokent(rDIs, len(rDIs))
                    if verbose:
                        print("mode ", mode)
                    for key in list(kpars.keys()):
                        if key != 'n' and verbose:
                            print("    ", key, '%7.1f' % (kpars[key]))
                        if key == 'n' and verbose:
                            print("    ", key, '       %i' % (kpars[key]))
                    mode += 1
                    rpars.append(kpars['dec'])
                    rpars.append(kpars['inc'])
                    rpars.append(kpars['Zeta'])
                    rpars.append(kpars['Zdec'])
                    rpars.append(kpars['Zinc'])
                    rpars.append(kpars['Eta'])
                    rpars.append(kpars['Edec'])
                    rpars.append(kpars['Einc'])
            else:  # assume bootstrap
                if dist == 'BE':
                    if len(nDIs) > 5:
                        BnDIs = pmag.di_boot(nDIs)
                        Bkpars = pmag.dokent(BnDIs, 1.)
                        if verbose:
                            print("mode ", mode)
                        for key in list(Bkpars.keys()):
                            if key != 'n' and verbose:
                                print("    ", key, '%7.1f' % (Bkpars[key]))
                            if key == 'n' and verbose:
                                print("    ", key, '       %i' % (Bkpars[key]))
                        mode += 1
                        npars.append(Bkpars['dec'])
                        npars.append(Bkpars['inc'])
                        npars.append(Bkpars['Zeta'])
                        npars.append(Bkpars['Zdec'])
                        npars.append(Bkpars['Zinc'])
                        npars.append(Bkpars['Eta'])
                        npars.append(Bkpars['Edec'])
                        npars.append(Bkpars['Einc'])
                    if len(rDIs) > 5:
                        BrDIs = pmag.di_boot(rDIs)
                        Bkpars = pmag.dokent(BrDIs, 1.)
                        if verbose:
                            print("mode ", mode)
                        for key in list(Bkpars.keys()):
                            if key != 'n' and verbose:
                                print("    ", key, '%7.1f' % (Bkpars[key]))
                            if key == 'n' and verbose:
                                print("    ", key, '       %i' % (Bkpars[key]))
                        mode += 1
                        rpars.append(Bkpars['dec'])
                        rpars.append(Bkpars['inc'])
                        rpars.append(Bkpars['Zeta'])
                        rpars.append(Bkpars['Zdec'])
                        rpars.append(Bkpars['Zinc'])
                        rpars.append(Bkpars['Eta'])
                        rpars.append(Bkpars['Edec'])
                        rpars.append(Bkpars['Einc'])
                    etitle = "Bootstrapped confidence ellipse"
                elif dist == 'BV':
                    sym = {'lower': ['o', 'c'], 'upper': [
                        'o', 'g'], 'size': 3, 'edgecolor': 'face'}
                    if len(nDIs) > 5:
                        BnDIs = pmag.di_boot(nDIs)
                        pmagplotlib.plot_eq_sym(
                            FIG['bdirs'], BnDIs, 'Bootstrapped Eigenvectors', sym)
                    if len(rDIs) > 5:
                        BrDIs = pmag.di_boot(rDIs)
                        if len(nDIs) > 5:  # plot on existing plots
                            pmagplotlib.plot_di_sym(FIG['bdirs'], BrDIs, sym)
                        else:
                            pmagplotlib.plot_eq(
                                FIG['bdirs'], BrDIs, 'Bootstrapped Eigenvectors')
            if dist == 'B':
                if len(nDIs) > 3 or len(rDIs) > 3:
                    pmagplotlib.plot_conf(FIG['eqarea'], etitle, [], npars, 0)
            elif len(nDIs) > 3 and dist != 'BV':
                pmagplotlib.plot_conf(FIG['eqarea'], etitle, [], npars, 0)
                if len(rDIs) > 3:
                    pmagplotlib.plot_conf(FIG['eqarea'], etitle, [], rpars, 0)
            elif len(rDIs) > 3 and dist != 'BV':
                pmagplotlib.plot_conf(FIG['eqarea'], etitle, [], rpars, 0)

        for key in list(FIG.keys()):
            files = {}
            filename = pmag.get_named_arg('-fname')
            if filename:  # use provided filename
                filename += '.' + fmt
            elif pmagplotlib.isServer:  # use server plot naming convention
                filename = 'LO:_'+locations+'_SI:_'+site+'_SA:_'+sample + \
                    '_SP:_'+specimen+'_CO:_'+crd+'_TY:_'+key+'_.'+fmt
            elif plot_key == 'all':
                filename = 'all'
                if 'location' in plot_data.columns:
                    locs = plot_data['location'].unique()
                    loc_string = "_".join(
                        [str(loc).replace(' ', '_') for loc in locs])
                    filename += "_" + loc_string
                filename += "_" + crd + "_" + key
                filename += ".{}".format(fmt)
            else:  # use more readable naming convention
                filename = ''
                # fix this if plot_by is location , for example
                use_names = {'location': [locations], 'site': [locations, site],
                             'sample': [locations, site, sample],
                             'specimen': [locations, site, sample, specimen]}
                use = use_names[plot_key]
                use.extend([crd, key])
                # [locations, site, sample, specimen, crd, key]:
                for item in use:
                    if item:
                        item = item.replace(' ', '_')
                        filename += item + '_'
                if filename.endswith('_'):
                    filename = filename[:-1]
                filename += ".{}".format(fmt)

            files[key] = filename

        if pmagplotlib.isServer:
            black = '#000000'
            purple = '#800080'
            titles = {}
            titles['eqarea'] = 'Equal Area Plot'
            FIG = pmagplotlib.add_borders(FIG, titles, black, purple)
            pmagplotlib.save_plots(FIG, files)

        elif plt:
            pmagplotlib.save_plots(FIG, files)
            continue
        if verbose:
            pmagplotlib.draw_figs(FIG)
            ans = input(" S[a]ve to save plot, [q]uit, Return to continue:  ")
            if ans == "q":
                sys.exit()
            if ans == "a":
                pmagplotlib.save_plots(FIG, files)
        continue


if __name__ == "__main__":
    main()
