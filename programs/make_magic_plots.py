#!/usr/bin/env python
import sys
import os
import datetime
from pmagpy import pmag
from pmagpy import contribution_builder as cb
VERBOSE = True


def error_log(msg, loc="", program=""):
    with open('errors.txt', 'a') as log:
        log.write(str(datetime.datetime.now()) + '\t' + loc + '\t' + program + '\t' + msg + '\n')
    if VERBOSE:
        print('-W- ' + loc + '\t' + program + '\t' + msg + '\n')

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
    inspects magic directory for available plots.

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
    dirlist = ['./']
    dir_path = os.getcwd()
    names = os.listdir(dir_path)
    onedir = True
    for n in names:
        if 'Location' in n:
            dirlist.append(n)
            onedir = False
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
    azimuth_key = 'azimuth'
    meas_file = 'measurements.txt'
    loc_key = 'location'
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
    con = cb.Contribution()
    con.propagate_location_to_measurements()
    con.propagate_location_to_specimens()
    con.propagate_location_to_samples()
    if not con.tables:
        print('-E- No MagIC tables could be found in this directory')
        error_log("No MagIC tables found")
        return
    # check to see if propagation worked, otherwise plotting will be difficult
    lowest_table = None
    for table in con.ancestry:
        if table in con.tables:
            lowest_table = table
            break
    if 'location' in con.tables[lowest_table].df.columns:
        if not all(con.tables[lowest_table].df['location'].isnull()):
            info_log('location names propagated to {}'.format(lowest_table))
        else:
            error_log('could not propagate location names down to {} table'.format(lowest_table))
    else:
        error_log('could not propagate location names down to {} table'.format(lowest_table))

    all_data = {}
    all_data['measurements'] = con.tables.get('measurements', None)
    all_data['specimens'] = con.tables.get('specimens', None)
    all_data['samples'] = con.tables.get('samples', None)
    all_data['sites'] = con.tables.get('sites', None)
    all_data['locations'] = con.tables.get('locations', None)
    if onedir:
        locations = con.tables['locations'].df.index.unique()
        dirlist = [loc for loc in locations if cb.not_null(loc) and loc != 'nan']


    # go through all data by location
    # either use tmp_*.txt files to separate out by location
    # or Location_* directories
    for loc in dirlist:
        print('\nworking on: ', loc)

        if onedir: # all info is in main directory, sort by location
            def get_data(dtype, loc_name):
                """
                Extract data of type dtype for location loc_name.
                Write tmp_dtype.txt files if possible.
                """
                if cb.not_null(all_data[dtype]):
                    data_container = all_data[dtype]
                    data_df = data_container.df[data_container.df['location'] == loc_name]
                    data = data_container.convert_to_pmag_data_list(df=data_df)
                    res = data_container.write_magic_file('tmp_{}.txt'.format(dtype), df=data_df)
                    if not res:
                        return []
                    return data

            meas_data = get_data('measurements', loc)
            spec_data = get_data('specimens', loc)
            samp_data = get_data('samples', loc)
            site_data = get_data('sites', loc)
            location_data = get_data('locations', loc)


        elif loc == "./":  # if you can't sort by location, do everything together
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
        else: # if there are Location_* directories, change WD for each location
            os.chdir(loc)

        crd = 's'
        if samp_file in filelist:  # find coordinate systems
            if onedir:
                samps = samp_data
                file_type = "samples"
            else:
                print('-I- found sample file', samp_file)
                samps, file_type = pmag.magic_read(samp_file)  # read in data
            # get all non blank sample orientations
            Srecs = pmag.get_dictitem(samps, azimuth_key, '', 'F')
            if len(Srecs) > 0:
                crd = 'g'
                print('using geographic coordinates')
            else:
                print('using specimen coordinates')
        else:
            if VERBOSE:
                print('-I- No sample data found')
        if meas_file in filelist:  # start with measurement data
            print('working on measurements data')
            if onedir:
                data = meas_data
                file_type = 'measurements'
            else:
                data, file_type = pmag.magic_read(meas_file)  # read in data
            if loc == './' and len(dirlist) > 1:
                # get all the blank location names from data file
                data = pmag.get_dictitem(data, loc_key, '', 'T')
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
                if onedir:
                    CMD = 'zeq_magic.py -f tmp_measurements.txt -fsp tmp_specimens.txt -fsa tmp_samples.txt -fsi tmp_sites.txt -sav -fmt ' + fmt + ' -crd ' + crd
                else:
                    CMD = 'zeq_magic.py -fsp specimens.txt -sav -fmt ' + fmt + ' -crd ' + crd
                print(CMD)
                info_log(CMD, loc)
                os.system(CMD)
            # looking for  thellier_magic possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-PI-TRM', 'has')) > 0:
                if onedir:
                    CMD = 'thellier_magic.py -f tmp_measurements.txt -fsp tmp_specimens.txt -sav -fmt ' + fmt
                else:
                    CMD = 'thellier_magic.py -fsp specimens.txt -sav -fmt ' + fmt
                print(CMD)
                info_log(CMD, loc)
                os.system(CMD)
            # looking for hysteresis possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-HYS', 'has')) > 0:  # find hyst experiments
                # check for reqd columns
                missing = check_for_reqd_cols(data, ['treat_temp'])
                if missing:
                    error_log('LP-HYS method code present, but required column(s) [{}] missing'.format(", ".join(missing)), loc, "quick_hyst.py")
                else:
                    if onedir:
                        CMD = 'quick_hyst.py -f tmp_measurements.txt -sav -fmt ' + fmt
                    else:
                        CMD = 'quick_hyst.py -f measurements.txt -sav -fmt ' + fmt
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)
        else:
            if VERBOSE:
                print('-I- No measurement data found')

        if results_file in filelist: # site data
            print('-I- result file found', results_file)
            if onedir:
                data = site_data
                file_type = 'sites'
            else:
                data, file_type = pmag.magic_read(results_file)  # read in data
            if loc == './' and len(dirlist) > 1:
                # get all the concatenated location names from data file
                data = pmag.get_dictitem(data, loc_key, ':', 'has')
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
            # only individual results - not poles
            # get only individual results (if result_type col is available)
            if SiteDIs:
                if 'result_type' in SiteDIs[0]:
                    SiteDIs = pmag.get_dictitem(SiteDIs, 'result_type', 'i', 'has')
                # then convert tilt_corr_key to correct format
                old_SiteDIs = SiteDIs
                SiteDIs = []
                for rec in old_SiteDIs:
                    if tilt_corr_key not in rec:
                        error_log("Directional data found, but missing {}, can't plot directions".format(tilt_corr_key), loc, "eqarea_magic.py")
                        break
                    if cb.is_null(rec[tilt_corr_key]) and rec[tilt_corr_key] != 0:
                        rec[tilt_corr_key] = ""
                    else:
                        rec[tilt_corr_key] = str(int(float(rec[tilt_corr_key])))
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
                    elif len(SiteDIs_g) > 0:
                        CRD = ' -crd g'
                    elif len(SiteDIs_s) > 0:
                        CRD = ' -crd s'
                    if onedir:
                        CMD = 'eqarea_magic.py -f tmp_sites.txt -fsp tmp_specimens.txt -fsa tmp_samples.txt -flo tmp_locations.txt -sav -fmt ' + fmt + CRD
                    else:
                        CMD = 'eqarea_magic.py -sav -fmt ' + fmt + CRD
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)
                else:
                    if dir_data_found:
                        error_log('{} dec/inc pairs found, but no equal area plots were made'.format(dir_data_found), loc, "equare_magic.py")
            #
            print('-I- working on VGP map')
            VGPs = pmag.get_dictitem(
                SiteDIs, 'vgp_lat', "", 'F')  # are there any VGPs?
            if len(VGPs) > 0:  # YES!
                if onedir:
                    CMD = 'vgpmap_magic.py -f tmp_sites.txt -prj moll -res c -sym ro 5 -sav -fmt png'
                else:
                    CMD = 'vgpmap_magic.py -prj moll -res c -sym ro 5 -sav -fmt png'
            else:
                print('-I- No vgps found')

            print('-I- Look for intensities')
            # is there any intensity data?
            if site_data:
                if int_key in site_data[0].keys():
                    infile = results_file
                    if onedir:
                        CMD = 'magic_select.py  -key ' + int_key + ' 0. has -F tmp1.txt -f tmp_sites.txt'
                    else:
                        CMD = 'magic_select.py  -key ' + int_key + ' 0. has -F tmp1.txt -f ' + infile
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)


                    ## should be able to do something like this instead of calling grab_magic_key
                    ##Selection = pmag.get_dictitem(site_data, int_key, '0.', 'has', float_to_int=True)

                    CMD = "grab_magic_key.py -f tmp1.txt -key " + \
                        int_key + " | awk '{print $1*1e6}' >tmp2.txt"
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)

                    data, file_type = pmag.magic_read('tmp1.txt')  # read in data
                    locations = pmag.get_dictkey(data, loc_key, "")
                    if not locations:
                        locations = ['']
                    locations = set(locations)
                    histfile = 'LO:_' + ":".join(locations) + \
                        '_TY:_intensities_histogram:_.' + fmt
                    # maybe run histplot.main here instead, so you can return an error message
                    CMD = "histplot.py -b 1 -xlab 'Intensity (uT)' -sav -f tmp2.txt -F " + histfile
                    os.system(CMD)
                    info_log(CMD, loc)
                    print(CMD)

        ##
        if hyst_file in filelist:
            print('working on hysteresis', hyst_file)
            if onedir:
                data = spec_data
                file_type = 'specimens'
            else:
                data, file_type = pmag.magic_read(hyst_file)  # read in data
            if loc == './' and len(dirlist) > 1:
                # get all the blank location names from data file
                data = pmag.get_dictitem(data, loc_key, '', 'T')
            hdata = pmag.get_dictitem(data, hyst_bcr_key, '', 'F')
            hdata = pmag.get_dictitem(hdata, hyst_mr_key, '', 'F')
            hdata = pmag.get_dictitem(hdata, hyst_ms_key, '', 'F')
            # there are data for a dayplot
            hdata = pmag.get_dictitem(hdata, hyst_bc_key, '', 'F')
            if len(hdata) > 0:
                if onedir:
                    CMD = 'dayplot_magic.py -f tmp_specimens.txt -sav -fmt ' + fmt
                else:
                    CMD = 'dayplot_magic.py -sav -fmt ' + fmt
                info_log(CMD, loc)
                print(CMD)
            else:
                print('no hysteresis data found')
        if aniso_file in filelist:  # do anisotropy plots if possible
            print('working on anisotropy', aniso_file)
            if onedir:
                data = spec_data
                file_type = 'specimens'
            else:
                data, file_type = pmag.magic_read(aniso_file)  # read in data
            if loc == './' and len(dirlist) > 1:
                # get all the blank location names from data file
                data = pmag.get_dictitem(data, loc_key, '', 'T')

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
                CRD = ""
                CMD = 'aniso_magic.py -x -B -sav -fmt ' + fmt
                if len(sdata) > 3:
                    CMD = CMD + ' -crd s'
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)
                if len(gdata) > 3:
                    CMD = CMD + ' -crd g'
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)
                if len(tdata) > 3:
                    CMD = CMD + ' -crd t'
                    print(CMD)
                    info_log(CMD, loc)
                    os.system(CMD)
        if not onedir and loc != './':
            os.chdir('..')  # change working directories to each location
        os.system('rm tmp*.txt')
    if loc_file in filelist:
        data, file_type = pmag.magic_read(loc_file)  # read in location data
        print('-I- working on pole map')
        poles = pmag.get_dictitem(
            data, 'pole_lat', "", 'F')  # are there any poles?
        poles = pmag.get_dictitem(
            poles, 'pole_lon', "", 'F')  # are there any poles?
        if len(poles) > 0:  # YES!
            CMD = 'polemap_magic.py -sav -fmt png'
            print(CMD)
            info_log(CMD, loc)
            os.system(CMD)
        else:
            print('-I- No poles found')

if __name__ == "__main__":
    main()
