#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

from __future__ import print_function
from builtins import input
from builtins import map
from builtins import zip
from builtins import range
import pandas as pd
import numpy as np
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import pmagpy.new_builder as nb


def save_redo(SpecRecs, inspec):
    print("Saving changes to specimen file")
    pmag.magic_write(inspec, SpecRecs, 'specimens')


def main():
    """
    NAME
        zeq_magic.py

    DESCRIPTION
        reads in magic_measurements formatted file, makes plots of remanence decay
        during demagnetization experiments.  Reads in prior interpretations saved in
        a pmag_specimens formatted file [and  allows re-interpretations of best-fit lines
        and planes and saves (revised or new) interpretations in a pmag_specimens file.
        interpretations are saved in the coordinate system used. Also allows judicious editting of
        measurements to eliminate "bad" measurements.  These are marked as such in the magic_measurements
        input file.  they are NOT deleted, just ignored. ] Bracketed part not yet implemented

    SYNTAX
        zeq_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f  MEASFILE: sets measurements format input file, default: measurements.txt
        -fsp SPECFILE: sets specimens format file with prior interpreations, default: specimens.txt
        -fsa SAMPFILE: sets samples format file sample=>site information, default: samples.txt
        -fsi SITEFILE: sets sites format file with site=>location informationprior interpreations, default: samples.txt
        -Fp PLTFILE: sets filename for saved plot, default is name_type.fmt (where type is zijd, eqarea or decay curve)
        -crd [s,g,t]: sets coordinate system,  g=geographic, t=tilt adjusted, default: specimen coordinate system
        -spc SPEC  plots single specimen SPEC, saves plot with specified format
              with optional -dir settings and quits
        -dir [L,P,F][beg][end]: sets calculation type for principal component analysis, default is none
             beg: starting step for PCA calculation
             end: ending step for PCA calculation
             [L,P,F]: calculation type for line, plane or fisher mean
             must be used with -spc option
        -fmt FMT: set format of saved plot [png,svg,jpg]
        -A:  suppresses averaging of  replicate measurements, default is to average
        -sav: saves all plots without review
    SCREEN OUTPUT:
        Specimen, N, a95, StepMin, StepMax, Dec, Inc, calculation type

    """
    # initialize some variables
    doave, e, b = 1, 0, 0  # average replicates, initial end and beginning step
    intlist = ['magn_moment', 'magn_volume', 'magn_mass', 'magnitude']
    plots, coord = 0, 's'
    noorient = 0
    version_num = pmag.get_version()
    verbose = pmagplotlib.verbose
    calculation_type, fmt = "", "svg"
    user, spec_keys, locname = "", [], ''
    geo, tilt, ask = 0, 0, 0
    PriorRecs = []  # empty list for prior interpretations
    backup = 0
    specimen = ""  # can skip everything and just plot one specimen with bounds e,b
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg_from_sys(
        "-f", default_val="measurements.txt")
    spec_file = pmag.get_named_arg_from_sys(
        "-fsp", default_val="specimens.txt")
    samp_file = pmag.get_named_arg_from_sys("-fsa", default_val="samples.txt")
    site_file = pmag.get_named_arg_from_sys("-fsi", default_val="sites.txt")
    #meas_file = os.path.join(dir_path, meas_file)
    #spec_file = os.path.join(dir_path, spec_file)
    #samp_file = os.path.join(dir_path, samp_file)
    #site_file = os.path.join(dir_path, site_file)
    plot_file = pmag.get_named_arg_from_sys("-Fp", default_val="")
    crd = pmag.get_named_arg_from_sys("-crd", default_val="s")
    if crd == "s":
        coord = "-1"
    elif crd == "t":
        coord = "100"
    else:
        coord = "0"
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    specimen = pmag.get_named_arg_from_sys("-spc", default_val="")
    beg_pca, end_pca = "", ""
    if '-dir' in sys.argv:
        ind = sys.argv.index('-dir')
        direction_type = sys.argv[ind + 1]
        beg_pca = int(sys.argv[ind + 2])
        end_pca = int(sys.argv[ind + 3])
        if direction_type == 'L':
            calculation_type = 'DE-BFL'
        if direction_type == 'P':
            calculation_type = 'DE-BFP'
        if direction_type == 'F':
            calculation_type = 'DE-FM'
    if '-A' in sys.argv:
        doave = 0
    if '-sav' in sys.argv:
        plots, verbose = 1, 0
    #
    first_save = 1
    fnames = {'measurements': meas_file, 'specimens': spec_file,
              'samples': samp_file, 'sites': site_file}
    contribution = nb.Contribution(dir_path, custom_filenames=fnames, read_tables=[
                                   'measurements', 'specimens', 'samples', 'sites'])
#
#   import  specimens

    specimen_cols = ['analysts', 'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_s', 'aniso_s_mean', 'aniso_s_n_measurements', 'aniso_s_sigma', 'aniso_s_unit', 'aniso_tilt_correction', 'aniso_type', 'aniso_v1', 'aniso_v2', 'aniso_v3', 'citations', 'description', 'dir_alpha95', 'dir_comp', 'dir_dec', 'dir_inc', 'dir_mad_free', 'dir_n_measurements', 'dir_tilt_correction', 'experiments', 'geologic_classes',
                     'geologic_types', 'hyst_bc', 'hyst_bcr', 'hyst_mr_moment', 'hyst_ms_moment', 'int_abs', 'int_b', 'int_b_beta', 'int_b_sigma', 'int_corr', 'int_dang', 'int_drats', 'int_f', 'int_fvds', 'int_gamma', 'int_mad_free', 'int_md', 'int_n_measurements', 'int_n_ptrm', 'int_q', 'int_rsc', 'int_treat_dc_field', 'lithologies', 'meas_step_max', 'meas_step_min', 'meas_step_unit', 'method_codes', 'sample', 'software_packages', 'specimen']
    if 'specimens' in contribution.tables:
        #        contribution.propagate_name_down('sample','measurements')
        spec_container = contribution.tables['specimens']
        prior_spec_data = spec_container.get_records_for_code(
            'LP-DIR', strict_match=False)  # look up all prior directional interpretations
#
#  tie sample names to measurement data
#
    else:
        spec_container, prior_spec_data = None, []


#
#   import samples  for orientation info
#
    if 'samples' in contribution.tables:
        #        contribution.propagate_name_down('site','measurements')
        contribution.propagate_cols(col_names=[
                                    'azimuth', 'dip', 'orientation_flag'], target_df_name='measurements', source_df_name='samples')
#
# define figure numbers for equal area, zijderveld,
#  and intensity vs. demagnetiztion step respectively
#
    ZED = {}
    ZED['eqarea'], ZED['zijd'],  ZED['demag'] = 1, 2, 3
    pmagplotlib.plot_init(ZED['eqarea'], 6, 6)
    pmagplotlib.plot_init(ZED['zijd'], 6, 6)
    pmagplotlib.plot_init(ZED['demag'], 6, 6)
#    save_pca=0
    angle, direction_type, setangle = "", "", 0
#   create measurement dataframe
#
    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
#
    meas_data = meas_data[meas_data['method_codes'].str.contains(
        'LT-NO|LT-AF-Z|LT-T-Z|LT-M-Z') == True]  # fish out steps for plotting
    meas_data = meas_data[meas_data['method_codes'].str.contains(
        'AN|ARM|LP-TRM|LP-PI-ARM') == False]  # strip out unwanted experiments
    intensity_types = [
        col_name for col_name in meas_data.columns if col_name in intlist]
    # plot first intensity method found - normalized to initial value anyway -
    # doesn't matter which used
    int_key = intensity_types[0]
    # get all the non-null intensity records of the same type
    meas_data = meas_data[meas_data[int_key].notnull()]
    if 'flag' not in meas_data.columns:
        meas_data['flag'] = 'g'  # set the default flag to good
# need to treat LP-NO specially  for af data, treatment should be zero,
# otherwise 273.
    meas_data['treatment'] = meas_data['treat_ac_field'].where(
        cond=meas_data['treat_ac_field'] != '0', other=meas_data['treat_temp'])
    meas_data['ZI'] = 1  # initialize these to one
    meas_data['instrument_codes'] = ""  # initialize these to blank
#   for unusual case of microwave power....
    if 'treat_mw_power' in meas_data.columns:
        meas_data.loc[meas_data.treat_mw_power != 0,
                     'treatment'] = meas_data.treat_mw_power * meas_data.treat_mw_time
#
# get list of unique specimen names from measurement data
#
    # this is a list of all the specimen names
    specimen_names = meas_data.specimen.unique()
    specimen_names = specimen_names.tolist()
    specimen_names.sort()
#
# set up new DataFrame for this sessions specimen interpretations
#
    data_container = nb.MagicDataFrame(
        dtype='specimens', columns=specimen_cols)
    # this is for interpretations from this session
    current_spec_data = data_container.df
    locname = 'LookItUp'
    if specimen == "":
        k = 0
    else:
        k = specimen_names.index(specimen)
    # let's look at the data now
    while k < len(specimen_names):
        # set the current specimen for plotting
        this_specimen = specimen_names[k]
        if verbose and this_specimen != "":
            print(this_specimen, k + 1, 'out of ', len(specimen_names))
        if setangle == 0:
            angle = ""
        this_specimen_measurements = meas_data[meas_data['specimen'].str.contains(
            this_specimen) == True]  # fish out this specimen
        this_specimen_measurements = this_specimen_measurements[this_specimen_measurements['flag'].str.contains(
            'g') == True]  # fish out this specimen
        if len(this_specimen_measurements) != 0:  # if there are measurements
            #
            #    set up datablock [[treatment,dec, inc, int, direction_type],[....]]
            #
            #
            # figure out the method codes
            #
            units, methods, title = "", "", this_specimen
            # this is a list of all the specimen method codes`
            meas_meths = this_specimen_measurements.method_codes.unique()
            tr = pd.to_numeric(this_specimen_measurements.treatment).tolist()
            if set(tr) == set([0]):
                k += 1
                continue
            for m in meas_meths:
                if 'LT-AF-Z' in m:
                    units = 'T'  # units include tesla
                    tr[0] = 0
                if 'LT-T-Z' in m:
                    units = units + ":K"  # units include kelvin
                if 'LT-M-Z' in m:
                    units = units + ':J'  # units include joules
                    tr[0] = 0
                units = units.strip(':')  # strip off extra colons
                if 'LP-' in m:
                    methods = methods + ":" + m
            decs = pd.to_numeric(this_specimen_measurements.dir_dec).tolist()
            incs = pd.to_numeric(this_specimen_measurements.dir_inc).tolist()
#
#    fix the coordinate system
#
            if coord != '-1':  # need to transform coordinates to geographic

                azimuths = pd.to_numeric(
                    this_specimen_measurements.azimuth).tolist()  # get the azimuths
                # get the azimuths
                dips = pd.to_numeric(this_specimen_measurements.dip).tolist()
                dirs = [decs, incs, azimuths, dips]
                # this transposes the columns and rows of the list of lists
                dirs_geo = np.array(list(map(list, list(zip(*dirs)))))
                decs, incs = pmag.dogeo_V(dirs_geo)
                if coord == '100':  # need to do tilt correction too
                    bed_dip_dirs = pd.to_numeric(
                        this_specimen_measurements.bed_dip_dir).tolist()  # get the azimuths
                    bed_dips = pd.to_numeric(
                        this_specimen_measurements.bed_dip).tolist()  # get the azimuths
                    dirs = [decs, incs, bed_dip_dirs, bed_dips]
                    # this transposes the columns and rows of the list of lists
                    dirs_tilt = np.array(list(map(list, list(zip(*dirs)))))
                    decs, incs = pmag.dotilt_V(dirs_tilt)
                    title = title + '_t'
                else:
                    title = title + '_g'
            if angle == "":
                angle = decs[0]
            ints = pd.to_numeric(this_specimen_measurements[int_key]).tolist()
            ZI = this_specimen_measurements.ZI.tolist()
            flags = this_specimen_measurements.flag.tolist()
            codes = this_specimen_measurements.instrument_codes.tolist()
            datalist = [tr, decs, incs, ints, ZI, flags, codes]
            # this transposes the columns and rows of the list of lists
            datablock = list(map(list, list(zip(*datalist))))
            pmagplotlib.plotZED(ZED, datablock, angle, title, units)
            if verbose:
                pmagplotlib.drawFIGS(ZED)
#
#     collect info for current_specimen_interpretation dictionary
#
            if beg_pca == "" and len(prior_spec_data) != 0:
                #
                #     find prior interpretation
                #
                prior_specimen_interpretations = prior_spec_data[prior_spec_data['specimen'].str.contains(
                    this_specimen) == True]
                beg_pcas = pd.to_numeric(
                    prior_specimen_interpretations.meas_step_min.values).tolist()
                end_pcas = pd.to_numeric(
                    prior_specimen_interpretations.meas_step_max.values).tolist()
                spec_methods = prior_specimen_interpretations.method_codes.tolist()
                # step through all prior interpretations and plot them
                for ind in range(len(beg_pcas)):
                    spec_meths = spec_methods[ind].split(':')
                    for m in spec_meths:
                        if 'DE-BFL' in m:
                            calculation_type = 'DE-BFL'  # best fit line
                        if 'DE-BFP' in m:
                            calculation_type = 'DE-BFP'  # best fit plane
                        if 'DE-FM' in m:
                            calculation_type = 'DE-FM'  # fisher mean
                        if 'DE-BFL-A' in m:
                            calculation_type = 'DE-BFL-A'  # anchored best fit line
                    start, end = tr.index(beg_pcas[ind]), tr.index(
                        end_pcas[ind])  # getting the starting and ending points
                    # calculate direction/plane
                    mpars = pmag.domean(
                        datablock, start, end, calculation_type)
                    if mpars["specimen_direction_type"] != "Error":
                        # put it on the plot
                        pmagplotlib.plotDir(ZED, mpars, datablock, angle)
                        if verbose:
                            pmagplotlib.drawFIGS(ZED)
            else:
                start, end = int(beg_pca), int(end_pca)
                # calculate direction/plane
                mpars = pmag.domean(datablock, start, end, calculation_type)
                if mpars["specimen_direction_type"] != "Error":
                    # put it on the plot
                    pmagplotlib.plotDir(ZED, mpars, datablock, angle)
                    if verbose:
                        pmagplotlib.drawFIGS(ZED)
            if plots == 1 or specimen != "":
                if plot_file == "":
                    basename = title
                else:
                    basename = plot_file
                files = {}
                for key in list(ZED.keys()):
                    files[key] = basename + '_' + key + '.' + fmt
                pmagplotlib.saveP(ZED, files)
                if specimen != "":
                    sys.exit()
            if verbose:
                recnum = 0
                for plotrec in datablock:
                    if units == 'T':
                        print('%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (
                            plotrec[5], recnum, plotrec[0] * 1e3, " mT", plotrec[3], plotrec[1], plotrec[2], plotrec[6]))
                    if units == "K":
                        print('%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (
                            plotrec[5], recnum, plotrec[0] - 273, ' C', plotrec[3], plotrec[1], plotrec[2], plotrec[6]))
                    if units == "J":
                        print('%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (
                            plotrec[5], recnum, plotrec[0], ' J', plotrec[3], plotrec[1], plotrec[2], plotrec[6]))
                    if 'K' in units and 'T' in units:
                        if plotrec[0] >= 1.:
                            print('%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (
                                plotrec[5], recnum, plotrec[0] - 273, ' C', plotrec[3], plotrec[1], plotrec[2], plotrec[6]))
                        if plotrec[0] < 1.:
                            print('%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (
                                plotrec[5], recnum, plotrec[0] * 1e3, " mT", plotrec[3], plotrec[1], plotrec[2], plotrec[6]))
                    recnum += 1
            # we have a current interpretation
            elif mpars["specimen_direction_type"] != "Error":
                #
                # create a new specimen record for the interpreation for this
                # specimen
                this_specimen_interpretation = {
                    col: "" for col in specimen_cols}
#               this_specimen_interpretation["analysts"]=user
                this_specimen_interpretation['software_packages'] = version_num
                this_specimen_interpretation['specimen'] = this_specimen
                this_specimen_interpretation["method_codes"] = calculation_type
                this_specimen_interpretation["meas_step_unit"] = units
                this_specimen_interpretation["meas_step_min"] = tr[start]
                this_specimen_interpretation["meas_step_max"] = tr[end]
                this_specimen_interpretation["dir_dec"] = '%7.1f' % (
                    mpars['specimen_dec'])
                this_specimen_interpretation["dir_inc"] = '%7.1f' % (
                    mpars['specimen_inc'])
                this_specimen_interpretation["dir_dang"] = '%7.1f' % (
                    mpars['specimen_dang'])
                this_specimen_interpretation["dir_n_measurements"] = '%i' % (
                    mpars['specimen_n'])
                this_specimen_interpretation["dir_tilt_correction"] = coord
                methods = methods.replace(" ", "")
                if "T" in units:
                    methods = methods + ":LP-DIR-AF"
                if "K" in units:
                    methods = methods + ":LP-DIR-T"
                if "J" in units:
                    methods = methods + ":LP-DIR-M"
                this_specimen_interpretation["method_codes"] = methods.strip(
                    ':')
                this_specimen_interpretation["experiments"] = this_specimen_measurements.experiment.unique()[
                    0]
#
#   print some stuff
#
                if calculation_type != 'DE-FM':
                    this_specimen_interpretation["dir_mad_free"] = '%7.1f' % (
                        mpars['specimen_mad'])
                    this_specimen_interpretation["dir_alpha95"] = ''
                    if verbose:
                        if units == 'K':
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_mad_free"]), float(this_specimen_interpretation["dir_dang"]), float(
                                this_specimen_interpretation["meas_step_min"]) - 273, float(this_specimen_interpretation["meas_step_max"]) - 273, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        elif units == 'T':
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_mad_free"]), float(this_specimen_interpretation["dir_dang"]), float(
                                this_specimen_interpretation["meas_step_min"]) * 1e3, float(this_specimen_interpretation["meas_step_max"]) * 1e3, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        elif 'T' in units and 'K' in units:
                            if float(this_specimen_interpretation['meas_step_min']) < 1.0:
                                min = float(
                                    this_specimen_interpretation['meas_step_min']) * 1e3
                            else:
                                min = float(
                                    this_specimen_interpretation['meas_step_min']) - 273
                            if float(this_specimen_interpretation['meas_step_max']) < 1.0:
                                max = float(
                                    this_specimen_interpretation['meas_step_max']) * 1e3
                            else:
                                max = float(
                                    this_specimen_interpretation['meas_step_max']) - 273
                            print('%s %i %7.1f %i %i %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_mad_free"]), float(
                                this_specimen_interpretation["dir_dang"]), min, max, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        else:
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_mad_free"]), float(this_specimen_interpretation["dir_dang"]), float(
                                this_specimen_interpretation["meas_step_min"]), float(this_specimen_interpretation["meas_step_max"]), float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                else:
                    this_specimen_interpretation["dir_alpha95"] = '%7.1f' % (
                        mpars['specimen_alpha95'])
                    this_specimen_interpretation["dir_mad_free"] = ''
                    if verbose:
                        if 'K' in units:
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurments"]), float(this_specimen_interpretation["dir_mad_free"]), float(this_specimen_interpretation["dir_dang"]), float(
                                this_specimen_interpretation["meas_step_min"]) - 273, float(this_specimen_interpretation["meas_step_max"]) - 273, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        elif 'T' in units:
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_alpha95"]), float(this_specimen_interpretation["dir_dang"]), float(
                                this_specimen_interpretation["meas_step_min"]) * 1e3, float(this_specimen_interpretation["meas_step_max"]) * 1e3, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        elif 'T' in units and 'K' in units:
                            if float(this_specimen_interpretation['meas_step_min']) < 1.0:
                                min = float(
                                    this_specimen_interpretation['meas_step_min']) * 1e3
                            else:
                                min = float(
                                    this_specimen_interpretation['meas_step_min']) - 273
                            if float(this_specimen_interpretation['meas_step_max']) < 1.0:
                                max = float(
                                    this_specimen_interpretation['meas_step_max']) * 1e3
                            else:
                                max = float(
                                    this_specimen_interpretation['meas_step_max']) - 273
                            print('%s %i %7.1f %i %i %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(
                                this_specimen_interpretation["dir_alpha95"]), min, max, float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                        else:
                            print('%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %s \n' % (this_specimen_interpretation["specimen"], int(this_specimen_interpretation["dir_n_measurements"]), float(this_specimen_interpretation["dir_alpha95"]), float(
                                this_specimen_interpretation["meas_step_min"]), float(this_specimen_interpretation["meas_step_max"]), float(this_specimen_interpretation["dir_dec"]), float(this_specimen_interpretation["dir_inc"]), calculation_type))
                if verbose:
                    saveit = input("Save this interpretation? [y]/n \n")
#   START HERE
#
#         if len(current_spec_data)==0: # no interpretations yet for this session
#             print "no current interpretation"
#             beg_pca,end_pca="",""
#             calculation_type=""
# get the ones that meet the current coordinate system
        else:
            print("no data")
        if verbose:
            input('Ready for next specimen  ')
        k += 1


#
if __name__ == "__main__":
    main()
