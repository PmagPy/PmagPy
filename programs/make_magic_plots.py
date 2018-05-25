#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import pandas as pd
from pmagpy import pmag
from pmagpy import new_builder as nb


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
        -DM [2,3] define data model
    """
    dirlist = ['./']
    dir_path = os.getcwd()
    names = os.listdir(dir_path)
    for n in names:
        if 'Location' in n:
            dirlist.append(n)
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
    onedir = None
    new_model = 1
    if '-DM' in sys.argv:
        ind = sys.argv.index("-DM")
        data_model = sys.argv[ind + 1]
        if data_model == '2':
            new_model = 0
    if new_model:
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
    else:
        new_model = 0
        samp_file = 'er_samples.txt'
        azimuth_key = 'sample_azimuth'
        meas_file = 'magic_measurements.txt'
        loc_key = 'er_location_name'
        method_key = 'magic_method_codes'
        dec_key = 'measurement_dec'
        inc_key = 'measurement_inc'
        tilt_corr_key = "tilt_correction"
        aniso_tilt_corr_key = "anisotropy_tilt_correction"
        hyst_bcr_key = "hysteresis_bcr"
        hyst_mr_key = "hysteresis_mr_moment"
        hyst_ms_key = "hysteresis_ms_moment"
        hyst_bc_key = "hysteresis_bc"
        Mkeys = ['measurement_magnitude', 'measurement_magn_moment',
                 'measurement_magn_volume', 'measurement_magn_mass']
        results_file = 'pmag_results.txt'
        hyst_file = 'rmag_hysteresis'
        aniso_file = 'rmag_anisotropy'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if new_model:
        con = nb.Contribution()
        con.propagate_location_to_measurements()
        con.propagate_location_to_specimens()
        con.propagate_location_to_samples()
        if not con.tables:
            print('No MagIC tables could be found in this directory')
            return
        lowest_table = None
        for table in con.ancestry:
            if table in con.tables:
                lowest_table = table
                break
        if 'location' in con.tables[lowest_table].df.columns:
            print('propagation successful')
            locations = con.tables['locations'].df.index.unique()
            dirlist = locations
            onedir = True
            all_data = {}
            all_data['measurements'] = con.tables.get('measurements', None)
            all_data['specimens'] = con.tables.get('specimens', None)
            all_data['samples'] = con.tables.get('samples', None)
            all_data['sites'] = con.tables.get('sites', None)
            all_data['locations'] = con.tables.get('locations', None)
    # go through all data by location
    # either use tmp_*.txt files to separate out by location
    # or Location_* directories
    for loc in dirlist:
        print('\nworking on: ', loc)
        if onedir: # all info is in main directory, sort by location
            if nb.not_null(all_data['measurements']):
                meas_data_all = all_data['measurements']
                meas_data_df = meas_data_all.df[meas_data_all.df['location'] == loc]
                meas_data = meas_data_all.convert_to_pmag_data_list(df=meas_data_df)
                meas_data_all.write_magic_file('tmp_measurements.txt', df=meas_data_df)
            else:
                meas_data = []
            if nb.not_null(all_data['specimens']):
                spec_data_all = all_data['specimens']
                spec_data_df = spec_data_all.df[spec_data_all.df['location'] == loc]
                spec_data = spec_data_all.convert_to_pmag_data_list(df=spec_data_df)
                spec_data_all.write_magic_file('tmp_specimens.txt', df=spec_data_df)
            else:
                spec_data = []
            if nb.not_null(all_data['samples']):
                samp_data_all = all_data['samples']
                samp_data_df = samp_data_all.df[samp_data_all.df['location'] == loc]
                samp_data = samp_data_all.convert_to_pmag_data_list(df=samp_data_df)
                samp_data_all.write_magic_file('tmp_samples.txt', df=samp_data_df)
            else:
                samp_data = []
            if nb.not_null(all_data['sites']):
                site_data_all = all_data['sites']
                site_data_df = site_data_all.df[site_data_all.df['location'] == loc]
                site_data = site_data_all.convert_to_pmag_data_list(df=site_data_df)
                site_data_all.write_magic_file('tmp_sites.txt', df=site_data_df)
            else:
                site_data = []
            if nb.not_null(all_data['locations']):
                location_data_all = all_data['locations']
                location_data_df = location_data_all.df[location_data_all.df['location'] == loc]
                #location_data = location_data_all.convert_to_pmag_data_list(df=location_data_df)
                location_data_all.write_magic_file('tmp_locations.txt', df=location_data_df)
            else:
                location_data = []


        elif loc == "./":  # if you can't sort by location, do everything together
            if new_model:
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
                print('found sample file', samp_file)
                samps, file_type = pmag.magic_read(samp_file)  # read in data
            # get all non blank sample orientations
            Srecs = pmag.get_dictitem(samps, azimuth_key, '', 'F')
            if len(Srecs) > 0:
                crd = 'g'
                print('using geographic coordinates')
            else:
                print('using specimen coordinates')
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
            # get all none blank method codes
            AFZrecs = pmag.get_dictitem(data, method_key, 'LT-AF-Z', 'has')
            # get all none blank method codes
            TZrecs = pmag.get_dictitem(data, method_key, 'LT-T-Z', 'has')
            # get all none blank method codes
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
                if new_model:
                    if onedir:
                        CMD = 'zeq_magic.py -fsp tmp_specimens.txt -sav -fmt ' + fmt + ' -crd ' + crd
                    else:
                        CMD = 'zeq_magic.py -fsp specimens.txt -sav -fmt ' + fmt + ' -crd ' + crd
                else:
                    CMD = 'zeq_magic2.py -fsp pmag_specimens.txt -sav -fmt ' + fmt + ' -crd ' + crd
                print(CMD)
                os.system(CMD)
            # looking for  thellier_magic possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-PI-TRM', 'has')) > 0:
                if new_model:
                    if onedir:
                        CMD = 'thellier_magic.py -fsp tmp_specimens.txt -sav -fmt ' + fmt
                    else:
                        CMD = 'thellier_magic.py -fsp specimens.txt -sav -fmt ' + fmt
                else:
                    CMD = 'thellier_magic2.py -fsp pmag_specimens.txt -sav -fmt ' + fmt
                print(CMD)
                os.system(CMD)
            # looking for hysteresis possibilities
            if len(pmag.get_dictitem(data, method_key, 'LP-HYS', 'has')) > 0:  # find hyst experiments
                if new_model:
                    if onedir:
                        CMD = 'quick_hyst.py -f tmp_measurements.txt -sav -fmt ' + fmt
                    else:
                        CMD = 'quick_hyst.py -f measurements.txt -sav -fmt ' + fmt
                else:
                    CMD = 'quick_hyst2.py -sav -fmt ' + fmt
                print(CMD)
                os.system(CMD)
        if results_file in filelist:  # start with measurement data
            print('result file found', results_file)
            if onedir:
                data = site_data
                file_type = 'sites'
            else:
                data, file_type = pmag.magic_read(results_file)  # read in data
            if loc == './' and len(dirlist) > 1:
                # get all the concatenated location names from data file
                data = pmag.get_dictitem(data, loc_key, ':', 'has')
            print('number of datapoints: ', len(data), loc)
            if new_model:
                print('working on site directions')
                dec_key = 'dir_dec'
                inc_key = 'dir_inc'
                int_key = 'int_abs'
            else:
                print('working on results directions')
                dec_key = 'average_dec'
                inc_key = 'average_inc'
                int_key = 'average_int'
            SiteDIs = pmag.get_dictitem(data, dec_key, "", 'F')  # find decs
            SiteDIs = pmag.get_dictitem(
                SiteDIs, inc_key, "", 'F')  # find decs and incs
            # only individual results - not poles
            if not new_model:
                SiteDIs = pmag.get_dictitem(SiteDIs, 'data_type', 'i', 'has')
            else:
                # get only individual results (if result_type col is available)
                if SiteDIs:
                    if 'result_type' in SiteDIs[0]:
                        SiteDIs = pmag.get_dictitem(SiteDIs, 'result_type', 'i', 'has')
                    # then convert tilt_corr_key to correct format
                    old_SiteDIs = SiteDIs
                    SiteDIs = []
                    for rec in old_SiteDIs:
                        if tilt_corr_key not in rec:
                            break
                        if nb.is_null(rec[tilt_corr_key]) and rec[tilt_corr_key] != 0:
                            rec[tilt_corr_key] = ""
                        else:
                            rec[tilt_corr_key] = str(int(float(rec[tilt_corr_key])))
                        SiteDIs.append(rec)
            print('individual number of directions: ', len(SiteDIs))
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
                if new_model:
                    if onedir:
                        CMD = 'eqarea_magic.py -f tmp_sites.txt -fsp tmp_specimens.txt -fsa tmp_samples.txt -flo tmp_locations.txt -sav -fmt ' + fmt + CRD
                    else:
                        CMD = 'eqarea_magic.py -sav -fmt ' + fmt + CRD
                else:
                    CMD = 'eqarea_magic2.py -sav -crd t -fmt ' + fmt + CRD
                print(CMD)
                os.system(CMD)
            print('working on VGP map')
            VGPs = pmag.get_dictitem(
                SiteDIs, 'vgp_lat', "", 'F')  # are there any VGPs?
            if len(VGPs) > 0:  # YES!
                if onedir:
                    CMD = 'vgpmap_magic.py -f tmp_sites.txt -prj moll -res c -sym ro 5 -sav -fmt png'
                else:
                    CMD = 'vgpmap_magic.py -prj moll -res c -sym ro 5 -sav -fmt png'

            print('working on intensities')
            if not new_model:
                CMD = 'magic_select.py -f ' + results_file + ' -key data_type i T -F tmp.txt'
                os.system(CMD)
                infile = ' tmp.txt'
            else:
                infile = results_file
                if onedir:
                    CMD = 'magic_select.py  -key ' + int_key + ' 0. has -F tmp1.txt -f tmp_sites.txt'
                else:
                    CMD = 'magic_select.py  -key ' + int_key + ' 0. has -F tmp1.txt -f ' + infile
                print(CMD)
                os.system(CMD)
            CMD = "grab_magic_key.py -f tmp1.txt -key " + \
                int_key + " | awk '{print $1*1e6}' >tmp2.txt"
            print(CMD)
            os.system(CMD)
            data, file_type = pmag.magic_read('tmp1.txt')  # read in data
            if new_model:
                locations = pmag.get_dictkey(data, loc_key, "")
            else:
                locations = pmag.get_dictkey(data, loc_key + 's', "")
            if not locations:
                locations = ['']
            histfile = 'LO:_' + locations[0] + \
                '_intensities_histogram:_.' + fmt
            os.system(
                "histplot.py -b 1 -xlab 'Intensity (uT)' -sav -f tmp2.txt -F " + histfile)
            print(
                "histplot.py -b 1 -xlab 'Intensity (uT)' -sav -f tmp2.txt -F " + histfile)
        if hyst_file in filelist:  # start with measurement data
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
                print('dayplot_magic.py -sav -fmt ' + fmt)
                if onedir:
                    os.system('dayplot_magic.py -f tmp_specimens.txt -sav -fmt ' + fmt)
                else:
                    os.system('dayplot_magic.py -sav -fmt ' + fmt)
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
                if new_model:
                    CMD = 'aniso_magic.py -x -B -sav -fmt ' + fmt
                else:
                    CMD = 'aniso_magic2.py -x -B -sav -fmt ' + fmt
                if len(sdata) > 3:
                    CMD = CMD + ' -crd s'
                    print(CMD)
                    os.system(CMD)
                if len(gdata) > 3:
                    CMD = CMD + ' -crd g'
                    print(CMD)
                    os.system(CMD)
                if len(tdata) > 3:
                    CMD = CMD + ' -crd t'
                    print(CMD)
                    os.system(CMD)
        if not onedir and loc != './':
            os.chdir('..')  # change working directories to each location
        os.system('rm tmp*.txt')
    if loc_file in filelist:
        data, file_type = pmag.magic_read(loc_file)  # read in data
        print('working on pole map')
        poles = pmag.get_dictitem(
            data, 'pole_lat', "", 'F')  # are there any pole?
        poles = pmag.get_dictitem(
            poles, 'pole_lon', "", 'F')  # are there any pole?
        if len(poles) > 0:  # YES!
            CMD = 'polemap_magic.py -sav -fmt png'
            print(CMD)
            os.system(CMD)

if __name__ == "__main__":
    main()
