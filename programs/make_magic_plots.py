#!/usr/bin/env python
import sys
import os
import datetime
import glob
import shutil
from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import version
from pmagpy import contribution_builder as cb
from pmag_env import set_env
from programs import thumbnails
VERBOSE = True


def error_log(msg, loc="", program="", con_id=""):
    con_id = str(con_id)
    with open('errors.txt', 'a') as log:
        log.write(con_id + '\t' + str(datetime.datetime.now()) + '\t' + loc + '\t' + program + '\t' + msg + '\n')
    full_msg = '-W- ' + con_id + '\t' + loc + '\t' + program + '\t' + msg + '\n'
    if VERBOSE:
        print(full_msg)
    sys.stderr.write(full_msg)

def info_log(msg, loc="", program=""):
    with open('log.txt', 'a') as log:
        log.write(str(datetime.datetime.now()) + "\t" + loc + "\t" + program + '\t' + msg + '\n')

def check_for_reqd_cols(data, reqd_cols):
    """
    Check data (PmagPy list of dicts) for required columns
    """
    missing = []
    for col in reqd_cols:
        if col not in data[0]:
            missing.append(col)
    return missing


def main():
    """
    NAME
        make_magic_plots.py

    DESCRIPTION
        inspects magic directory for available data and makes plots

    SYNTAX
        make_magic_plots.py [command line options]

    INPUT
        magic files

    OPTIONS
        -h prints help message and quits
        -f FILE specifies input file name
        -fmt [png,eps,svg,jpg,pdf] specify format, default is png
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    # reset log files
    for fname in ['log.txt', 'errors.txt']:
        f = os.path.join(os.getcwd(), fname)
        if os.path.exists(f):
            os.remove(f)
    image_recs = []
    dirlist = ['./']
    dir_path = os.getcwd()
    #
    if '-fmt' in sys.argv:
        ind = sys.argv.index("-fmt")
        fmt = sys.argv[ind + 1]
    else:
        fmt = 'png'
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        filelist = [sys.argv[ind + 1]]
    else:
        filelist = os.listdir(dir_path)
    ## initialize some variables
    samp_file = 'samples.txt'
    meas_file = 'measurements.txt'
    #loc_key = 'location'
    loc_file = 'locations.txt'
    method_key = 'method_codes'
    dec_key = 'dir_dec'
    inc_key = 'dir_inc'
    tilt_corr_key = "dir_tilt_correction"
    aniso_tilt_corr_key = "aniso_tilt_correction"
    hyst_bcr_key = "hyst_bcr"
    hyst_mr_key = "hyst_mr_moment"
    hyst_ms_key = "hyst_ms_moment"
    hyst_bc_key = "hyst_bc"
    Mkeys = ['magnitude', 'magn_moment', 'magn_volume', 'magn_mass']
    results_file = 'sites.txt'
    hyst_file = 'specimens.txt'
    aniso_file = 'specimens.txt'
    # create contribution and propagate data throughout
    full_con = cb.Contribution()
    full_con.propagate_location_to_measurements()
    full_con.propagate_location_to_specimens()
    full_con.propagate_location_to_samples()
    if not full_con.tables:
        print('-E- No MagIC tables could be found in this directory')
        error_log("No MagIC tables found")
        return
    # try to get the contribution id for error logging
    con_id = ""
    if 'contribution' in full_con.tables:
        if 'id' in full_con.tables['contribution'].df.columns:
            con_id = full_con.tables['contribution'].df.iloc[0]['id']
    # check to see if propagation worked, otherwise you can't plot by location
    lowest_table = None
    for table in full_con.ancestry:
        if table in full_con.tables:
            lowest_table = table
            break

    do_full_directory = False
    # check that locations propagated down to the lowest table in the contribution
    if 'location' in full_con.tables[lowest_table].df.columns:
        if 'locations' not in full_con.tables:
            info_log('location names propagated to {}, but could not be validated'.format(lowest_table))
        # are there any locations in the lowest table?
        elif not all(full_con.tables[lowest_table].df['location'].isnull()):
            locs = full_con.tables['locations'].df.index.unique()
            lowest_locs = full_con.tables[lowest_table].df['location'].unique()
            incorrect_locs = set(lowest_locs).difference(set(locs))
            # are they actual locations?
            if not incorrect_locs:
                info_log('location names propagated to {}'.format(lowest_table))
            else:
                do_full_directory = True
                error_log('location names did not propagate fully to {} table (looks like there are some naming inconsistencies between tables)'.format(lowest_table), con_id=con_id)
        else:
            do_full_directory = True
            error_log('could not propagate location names down to {} table'.format(lowest_table), con_id=con_id)
    else:
        do_full_directory = True
        error_log('could not propagate location names down to {} table'.format(lowest_table), con_id=con_id)

    all_data = {}
    all_data['measurements'] = full_con.tables.get('measurements', None)
    all_data['specimens'] = full_con.tables.get('specimens', None)
    all_data['samples'] = full_con.tables.get('samples', None)
    all_data['sites'] = full_con.tables.get('sites', None)
    all_data['locations'] = full_con.tables.get('locations', None)
    if 'locations' in full_con.tables:
        locations = full_con.tables['locations'].df.index.unique()
    else:
        locations = ['']
    dirlist = [loc for loc in locations if cb.not_null(loc, False) and loc != 'nan']
    if not dirlist:
        dirlist = ["./"]
    if do_full_directory:
        dirlist = ["./"]

    # plot the whole contribution as one location
    if dirlist == ["./"]:
        error_log('plotting the entire contribution as one location', con_id=con_id)
        for fname in os.listdir("."):
            if fname.endswith(".txt"):
                shutil.copy(fname, "tmp_" + fname)

    # if possible, go through all data by location
    # use tmp_*.txt files to separate out by location

    for loc in dirlist:
        print('\nworking on: ', loc)

        def get_data(dtype, loc_name):
            """
            Extract data of type dtype for location loc_name.
            Write tmp_dtype.txt files if possible.
            """
            if cb.not_null(all_data[dtype], False):
                data_container = all_data[dtype]
                if loc_name == "./":
                    data_df = data_container.df
                else:
                    # awkward workaround for chars like "(" and "?" that break in regex
                    try:
                        data_df = data_container.df[data_container.df['location'].astype(str).str.contains(loc_name, na=False)]
                    except: #sre_constants.error:
                        data_df = data_container.df[data_container.df['location'] == loc_name]

                data = data_container.convert_to_pmag_data_list(df=data_df)
                res = data_container.write_magic_file('tmp_{}.txt'.format(dtype), df=data_df)
                if not res:
                    return [], []
                return data, data_df
            return [], []

        meas_data, meas_df = get_data('measurements', loc)
        spec_data, spec_df = get_data('specimens', loc)
        samp_data, samp_df = get_data('samples', loc)
        site_data, site_df = get_data('sites', loc)
        loc_data, loc_df = get_data('locations', loc)

        con = cb.Contribution(read_tables=[])
        con.tables['measurements'] = cb.MagicDataFrame(df=meas_df, dtype="measurements")
        con.tables['specimens'] = cb.MagicDataFrame(df=spec_df, dtype="specimens")
        con.tables['samples'] = cb.MagicDataFrame(df=samp_df, dtype="samples")
        con.tables['sites'] = cb.MagicDataFrame(df=site_df, dtype="sites")
        con.tables['locations'] = cb.MagicDataFrame(df=loc_df, dtype="locations")

        if loc == "./":  # if you can't sort by location, do everything together
            con = full_con
            try:
                meas_data = con.tables['measurements'].convert_to_pmag_data_list()
            except KeyError:
                meas_data = None
            try:
                spec_data = con.tables['specimens'].convert_to_pmag_data_list()
            except KeyError:
                spec_data = None
            try:
                samp_data = con.tables['samples'].convert_to_pmag_data_list()
            except KeyError:
                samp_data = None
            try:
                site_data = con.tables['sites'].convert_to_pmag_data_list()
            except KeyError:
                site_data = None

        crd = 's'
        if 'samples' in con.tables:
            if 'azimuth' in con.tables['samples'].df.columns:
                if any(con.tables['samples'].df['azimuth'].dropna()):
                    crd = 'g'
        if crd == 's':
            print('using specimen coordinates')
        else:
            print('using geographic coordinates')
        if meas_file in filelist and meas_data:  # start with measurement data
            print('working on plotting measurements data')
            data = meas_data
            file_type = 'measurements'
            # looking for  zeq_magic possibilities
            # get all non blank method codes
            AFZrecs = pmag.get_dictitem(data, method_key, 'LT-AF-Z', 'has')
            # get all non blank method codes
            TZrecs = pmag.get_dictitem(data, method_key, 'LT-T-Z', 'has')
            # get all non blank method codes
            MZrecs = pmag.get_dictitem(data, method_key, 'LT-M-Z', 'has')
            # get all dec measurements
            Drecs = pmag.get_dictitem(data, dec_key, '', 'F')
            # get all inc measurements
            Irecs = pmag.get_dictitem(data, inc_key, '', 'F')
            for key in Mkeys:
                Mrecs = pmag.get_dictitem(
                    data, key, '', 'F')  # get intensity data
                if len(Mrecs) > 0:
                    break
            # potential for stepwise demag curves
            if len(AFZrecs) > 0 or len(TZrecs) > 0 or len(MZrecs) > 0 and len(Drecs) > 0 and len(Irecs) > 0 and len(Mrecs) > 0:
                #CMD = 'zeq_magic.py -f tmp_measurements.txt -fsp tmp_specimens.txt -fsa tmp_samples.txt -fsi tmp_sites.txt -sav -fmt ' + fmt + ' -crd ' + crd + " -new"
                CMD = "ipmag.zeq_magic(crd={}, n_plots='all', contribution={}, image_records=True)".format(crd, con)
                print(CMD)
                info_log(CMD, loc)
                res, outfiles, zeq_images = ipmag.zeq_magic(crd=crd, n_plots='all',
                                                            contribution=con, image_records=True)
                image_recs.extend(zeq_images)
            # looking for  thellier_magic possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-PI-TRM', 'has')) > 0:
                #CMD = 'thellier_magic.py -f tmp_measurements.txt -fsp tmp_specimens.txt -sav -fmt ' + fmt
                CMD = "ipmag.thellier_magic(n_specs='all', fmt='png', contribution={}, image_records=True)".format(con)
                print(CMD)
                info_log(CMD, loc)
                res, outfiles, thellier_images = ipmag.thellier_magic(n_specs='all', fmt="png", contribution=con, image_records=True)
                image_recs.extend(thellier_images)
            # looking for hysteresis possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-HYS', 'has')) > 0:  # find hyst experiments
                # check for reqd columns
                missing = check_for_reqd_cols(data, ['treat_temp'])
                if missing:
                    error_log('LP-HYS method code present, but required column(s) [{}] missing'.format(", ".join(missing)), loc, "quick_hyst.py", con_id=con_id)
                else:
                    #CMD = 'quick_hyst.py -f tmp_measurements.txt -sav -fmt ' + fmt
                    CMD = "ipmag.quick_hyst(fmt='png', n_plots='all', contribution={}, image_records=True)".format(con)
                    print(CMD)
                    info_log(CMD, loc)
                    res, outfiles, quick_hyst_recs = ipmag.quick_hyst(fmt="png", n_plots='all', contribution=con, image_records=True)
                    image_recs.extend(quick_hyst_recs)
            # equal area plots of directional data
            # at measurement level (by specimen)
            if data:
                missing = check_for_reqd_cols(data, ['dir_dec', 'dir_inc'])
                if not missing:
                    #CMD = "eqarea_magic.py -f tmp_measurements.txt -obj spc -sav -no-tilt -fmt " + fmt
                    CMD = "ipmag.eqarea_magic(fmt='png', n_plots='all', ignore_tilt=True, plot_by='spc', contribution={}, source_table='measurements', image_records=True)".format(con)
                    print(CMD)
                    info_log(CMD, loc, "eqarea_magic.py")
                    res, outfiles, eqarea_spc_images = ipmag.eqarea_magic(fmt="png", n_plots='all',
                                                                          ignore_tilt=True, plot_by="spc",
                                                                          contribution=con,
                                                                          source_table="measurements",
                                                                          image_records=True)
                    image_recs.extend(eqarea_spc_images)

        else:
            if VERBOSE:
                print('-I- No measurement data found')

        # site data
        if results_file in filelist and site_data:
            print('-I- result file found', results_file)
            data = site_data
            file_type = 'sites'
            print('-I- working on site directions')
            print('number of datapoints: ', len(data), loc)
            dec_key = 'dir_dec'
            inc_key = 'dir_inc'
            int_key = 'int_abs'
            SiteDIs = pmag.get_dictitem(data, dec_key, "", 'F')  # find decs
            SiteDIs = pmag.get_dictitem(
                SiteDIs, inc_key, "", 'F')  # find decs and incs
            dir_data_found = len(SiteDIs)
            print('{} Dec/inc pairs found'.format(dir_data_found))
            if SiteDIs:
                # then convert tilt_corr_key to correct format
                old_SiteDIs = SiteDIs
                SiteDIs = []
                for rec in old_SiteDIs:
                    if tilt_corr_key not in rec:
                        rec[tilt_corr_key] = "0"
                    # make sure tilt_corr_key is a correct format
                    try:
                        rec[tilt_corr_key] = str(int(float(rec[tilt_corr_key])))
                    except ValueError:
                        rec[tilt_corr_key] = "0"
                    SiteDIs.append(rec)

                print('number of individual directions: ', len(SiteDIs))
                # tilt corrected coordinates
                SiteDIs_t = pmag.get_dictitem(SiteDIs, tilt_corr_key, '100',
                                              'T', float_to_int=True)
                print('number of tilt corrected directions: ', len(SiteDIs_t))
                SiteDIs_g = pmag.get_dictitem(
                    SiteDIs, tilt_corr_key, '0', 'T', float_to_int=True)  # geographic coordinates
                print('number of geographic  directions: ', len(SiteDIs_g))
                SiteDIs_s = pmag.get_dictitem(
                    SiteDIs, tilt_corr_key, '-1', 'T', float_to_int=True)  # sample coordinates
                print('number of sample  directions: ', len(SiteDIs_s))
                SiteDIs_x = pmag.get_dictitem(
                    SiteDIs, tilt_corr_key, '', 'T')  # no coordinates
                print('number of no coordinates  directions: ', len(SiteDIs_x))
                if len(SiteDIs_t) > 0 or len(SiteDIs_g) > 0 or len(SiteDIs_s) > 0 or len(SiteDIs_x) > 0:
                    CRD = ""
                    if len(SiteDIs_t) > 0:
                        CRD = ' -crd t'
                        crd = "t"
                    elif len(SiteDIs_g) > 0:
                        CRD = ' -crd g'
                        crd = "g"
                    elif len(SiteDIs_s) > 0:
                        CRD = ' -crd s'
                        crd = "s"
                    #CMD = 'eqarea_magic.py -f tmp_sites.txt -fsp tmp_specimens.txt -fsa tmp_samples.txt -flo tmp_locations.txt -sav -fmt ' + fmt + CRD
                    CMD = "ipmag.eqarea_magic(crd={}, fmt='png', n_plots='all', contribution={}, source_table='sites')".format(crd, con)
                    print(CMD)
                    info_log(CMD, loc)
                    res, outfiles, eqarea_site_recs = ipmag.eqarea_magic(crd=crd, fmt="png", n_plots='all',
                                                                   contribution=con, source_table="sites",
                                                                   image_records=True)
                    image_recs.extend(eqarea_site_recs)
                else:
                    if dir_data_found:
                        error_log('{} dec/inc pairs found, but no equal area plots were made'.format(dir_data_found), loc, "equarea_magic.py", con_id=con_id)
            #
            print('-I- working on VGP map')
            VGPs = pmag.get_dictitem(
                SiteDIs, 'vgp_lat', "", 'F')  # are there any VGPs?
            if len(VGPs) > 0:  # YES!
                #CMD = 'vgpmap_magic.py -f tmp_sites.txt -prj moll -res c -sym ro 5 -sav -fmt png'
                CMD = "ipmag.vgpmap_magic(proj='moll', sym='ro', size=5, fmt='png', contribution={})".format(con)
                print(CMD)
                info_log(CMD, loc, 'vgpmap_magic.py')
                res, outfiles, vgpmap_recs = ipmag.vgpmap_magic(proj='moll', sym='ro', size=5,
                                                                fmt="png", contribution=con,
                                                                image_records=True)
                image_recs.extend(vgpmap_recs)
            else:
                print('-I- No vgps found')

            print('-I- Look for intensities')
            # is there any intensity data?
            if site_data:
                if int_key in site_data[0].keys():
                    # old way, wasn't working right:
                    #CMD = 'magic_select.py  -key ' + int_key + ' 0. has -F tmp1.txt -f tmp_sites.txt'
                    Selection = pmag.get_dictkey(site_data, int_key, dtype="f")
                    selection = [i * 1e6 for i in Selection if i != 0]
                    loc = loc.replace(" ", "_")
                    if loc == "./":
                        loc_name = ""
                    else:
                        loc_name = loc
                    histfile = 'LO:_' + loc_name + \
                        '_TY:_intensities_histogram:_.' + fmt
                    CMD = "histplot.py -twin -b 1 -xlab 'Intensity (uT)' -sav -f intensities.txt -F " + histfile
                    CMD = "ipmag.histplot(data=selection, outfile=histfile, xlab='Intensity (uT)', binsize=1, norm=-1, save_plots=True)".format(histfile)
                    info_log(CMD, loc)
                    print(CMD)
                    ipmag.histplot(data=selection, outfile=histfile, xlab="Intensity (uT)",
                                   binsize=1, norm=-1, save_plots=True)
                    histplot_rec = {'file': histfile, 'type': 'Other', 'title': 'Intensity histogram',
                                    'software_packages': version.version, 'keywords': "",
                                    'timestamp': datetime.date.today().isoformat()}
                    image_recs.append(histplot_rec)
                else:
                    print('-I- No intensities found')
            else:
                print('-I- No intensities found')

        ##
        if hyst_file in filelist and spec_data:
            print('working on hysteresis', hyst_file)
            data = spec_data
            file_type = 'specimens'
            hdata = pmag.get_dictitem(data, hyst_bcr_key, '', 'F')
            hdata = pmag.get_dictitem(hdata, hyst_mr_key, '', 'F')
            hdata = pmag.get_dictitem(hdata, hyst_ms_key, '', 'F')
            # there are data for a dayplot
            hdata = pmag.get_dictitem(hdata, hyst_bc_key, '', 'F')
            if len(hdata) > 0:
                CMD = "ipmag.dayplot_magic(save=True, fmt='png', contribution={}, image_records=True)".format(con)
                info_log(CMD, loc)
                print(CMD)
                res, outfiles, dayplot_recs = ipmag.dayplot_magic(save=True, fmt='png',
                                                                  contribution=con, image_records=True)
                image_recs.extend(dayplot_recs)
            else:
                print('no hysteresis data found')
        if aniso_file in filelist and spec_data:  # do anisotropy plots if possible
            print('working on anisotropy', aniso_file)
            data = spec_data
            file_type = 'specimens'

            # make sure there is some anisotropy data
            if not data:
                print('No anisotropy data found')
            elif 'aniso_s' not in data[0]:
                print('No anisotropy data found')
            else:
                # get specimen coordinates
                if aniso_tilt_corr_key not in data[0]:
                    sdata = data
                else:
                    sdata = pmag.get_dictitem(
                        data, aniso_tilt_corr_key, '-1', 'T', float_to_int=True)
                # get specimen coordinates
                gdata = pmag.get_dictitem(
                    data, aniso_tilt_corr_key, '0', 'T', float_to_int=True)
                # get specimen coordinates
                tdata = pmag.get_dictitem(
                    data, aniso_tilt_corr_key, '100', 'T', float_to_int=True)
                if len(sdata) > 3:
                    CMD = "ipmag.aniso_magic(iboot=0, ihext=1, crd='s', fmt='png', contribution={})".format(con)
                    print(CMD)
                    info_log(CMD, loc)
                    res, files, aniso_recs = ipmag.aniso_magic(iboot=0, ihext=1, crd="s", fmt="png",
                                                               contribution=con, image_records=True)
                    image_recs.extend(aniso_recs)
                if len(gdata) > 3:
                    CMD = "ipmag.aniso_magic(iboot=0, ihext=1, crd='g', fmt='png', contribution={})".format(con)
                    print(CMD)
                    info_log(CMD, loc)
                    res, files, aniso_recs = ipmag.aniso_magic(iboot=0, ihext=1, crd="g", fmt="png",
                                                               contribution=con, image_records=True)
                    image_recs.extend(aniso_recs)
                if len(tdata) > 3:
                    CMD = "ipmag.aniso_magic(iboot=0, ihext=1, crd='g', fmt='png', contribution={})".format(con)
                    print(CMD)
                    info_log(CMD, loc)
                    res, files, aniso_recs = ipmag.aniso_magic(iboot=0, ihext=1, crd="t", fmt="png",
                                                               contribution=con, image_records=True)
                    image_recs.extend(aniso_recs)

        # remove temporary files
        for fname in glob.glob('tmp*.txt'):
            os.remove(fname)

    # now we need full contribution data
    if loc_file in filelist and loc_data:
        #data, file_type = pmag.magic_read(loc_file)  # read in location data
        data = loc_data
        print('-I- working on pole map')
        poles = pmag.get_dictitem(
            data, 'pole_lat', "", 'F')  # are there any poles?
        poles = pmag.get_dictitem(
            poles, 'pole_lon', "", 'F')  # are there any poles?
        if len(poles) > 0:  # YES!
            CMD = 'polemap_magic.py -sav -fmt png -rev gv 40'
            CMD =  'ipmag.polemap_magic(flip=True, rsym="gv", rsymsize=40, fmt="png", contribution={})'.format(full_con)
            print(CMD)
            info_log(CMD, "all locations", "polemap_magic.py")
            res, outfiles, polemap_recs = ipmag.polemap_magic(flip=True, rsym="gv", rsymsize=40,
                                                            fmt="png", contribution=full_con,
                                                            image_records=True)
            image_recs.extend(polemap_recs)
        else:
            print('-I- No poles found')

    if image_recs:
        new_image_file = os.path.join(dir_path, 'new_images.txt')
        old_image_file = os.path.join(dir_path, 'images.txt')
        pmag.magic_write(new_image_file, image_recs, 'images')
        if os.path.exists(old_image_file):
            ipmag.combine_magic([old_image_file, new_image_file], outfile=old_image_file,
                                magic_table="images", dir_path=dir_path)
        else:
            os.rename(new_image_file, old_image_file)
    if set_env.isServer:
        thumbnails.make_thumbnails(dir_path)

if __name__ == "__main__":
    main()
