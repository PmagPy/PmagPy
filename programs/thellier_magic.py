#!/usr/bin/env python

import pandas as pd
import numpy as np
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib

from pmag_env import set_env
if not set_env.isServer:
    import pmagpy.nlt as nlt

import pmagpy.contribution_builder as cb


def main():
    """
    NAME
        thellier_magic.py

    DESCRIPTION
        plots Thellier-Thellier data in version 3.0 format
        Reads saved interpretations from a specimen formatted table, default: specimens.txt

    SYNTAX
        thellier_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f MEAS, set measurements input file, default is 'measurements.txt'
        -fsp PRIOR, set specimens.txt prior interpretations file, default is 'specimens.txt'
        -fcr CRIT, set criteria file for grading.  # not yet implemented
        -fmt [svg,png,jpg], format for images - default is svg
        -sav,  saves plots with out review (in format specified by -fmt key or default)
        -spc SPEC, plots single specimen SPEC, saves plot with specified format
            with optional -b bounds and quits
        -b BEG END: sets  bounds for calculation
           BEG: starting step number for slope calculation
           END: ending step number for slope calculation
        -z use only z component difference for pTRM calculation

    OUTPUT
        figures:
            ALL:  numbers refer to temperature steps in command line window
            1) Arai plot:  closed circles are zero-field first/infield
                           open circles are infield first/zero-field
                           triangles are pTRM checks
                           squares are pTRM tail checks
                           VDS is vector difference sum
                           diamonds are bounds for interpretation
            2) Zijderveld plot:  closed (open) symbols are X-Y (X-Z) planes
                                 X rotated to NRM direction
            3) (De/Re)Magnetization diagram:
                           circles are NRM remaining
                           squares are pTRM gained
            4) equal area projections:
               green triangles are pTRM gained direction
                           red (purple) circles are lower(upper) hemisphere of ZI step directions
                           blue (cyan) squares are lower(upper) hemisphere IZ step directions
            5) Optional:  TRM acquisition
            6) Optional: TDS normalization
        command line window:
            list is: temperature step numbers, temperatures (C), Dec, Inc, Int (units of measuements)
                     list of possible commands: type letter followed by return to select option
                     saving of plots creates image files with specimen, plot type as name
    """
#
#   initializations
#
    version_num = pmag.get_version()
    verbose = pmagplotlib.verbose
#
# default acceptance criteria
#
    accept = pmag.default_criteria(0)[0]  # set the default criteria
#
# parse command line options
#
    plots, fmt, Zdiff = 0, 'svg', 0
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg(
        "-f", default_val="measurements.txt")
    spec_file = pmag.get_named_arg(
        "-fsp", default_val="specimens.txt")
    crit_file = pmag.get_named_arg("-fcr", default_val="criteria.txt")
    spec_file = os.path.join(dir_path, spec_file)
    meas_file = os.path.join(dir_path, meas_file)
    crit_file = os.path.join(dir_path, crit_file)
    fmt = pmag.get_named_arg("-fmt", "svg")
    if '-sav' in sys.argv:
        plots, verbose = 1, 0
    if '-z' in sys.argv:
        Zdiff = 1
    specimen = pmag.get_named_arg("-spc", default_val="")
    if '-b' in sys.argv:
        ind = sys.argv.index('-b')
        start = int(sys.argv[ind + 1])
        end = int(sys.argv[ind + 2])
    else:
        start, end = "", ""
    fnames = {'measurements': meas_file,
              'specimens': spec_file, 'criteria': crit_file}
    contribution = cb.Contribution(dir_path, custom_filenames=fnames, read_tables=[
                                   'measurements', 'specimens', 'criteria'])
#
#   import  prior interpretations  from specimen file
#
    specimen_cols = ['analysts', 'aniso_ftest', 'aniso_ftest12', 'aniso_ftest23', 'aniso_s', 'aniso_s_mean', 'aniso_s_n_measurements', 'aniso_s_sigma', 'aniso_s_unit', 'aniso_tilt_correction', 'aniso_type', 'aniso_v1', 'aniso_v2', 'aniso_v3', 'citations', 'description', 'dir_alpha95', 'dir_comp', 'dir_dec', 'dir_inc', 'dir_mad_free', 'dir_n_measurements', 'dir_tilt_correction', 'experiments', 'geologic_classes',
                     'geologic_types', 'hyst_bc', 'hyst_bcr', 'hyst_mr_moment', 'hyst_ms_moment', 'int_abs', 'int_b', 'int_b_beta', 'int_b_sigma', 'int_corr', 'int_dang', 'int_drats', 'int_f', 'int_fvds', 'int_gamma', 'int_mad_free', 'int_md', 'int_n_measurements', 'int_n_ptrm', 'int_q', 'int_rsc', 'int_treat_dc_field', 'lithologies', 'meas_step_max', 'meas_step_min', 'meas_step_unit', 'method_codes', 'sample', 'software_packages', 'specimen']
    spec_container, prior_spec_data = None, []
    if 'specimens' in contribution.tables:
        spec_container = contribution.tables['specimens']
        if 'method_codes' in spec_container.df.columns:
            # look up all prior intensity interpretations
            prior_spec_data = spec_container.get_records_for_code(
                'LP-PI-TRM', strict_match=False)
    backup = 0
    #
    Mkeys = ['magn_moment', 'magn_volume', 'magn_mass']
#
#   create measurement dataframe
#
    if pmagplotlib.isServer:
        contribution.propagate_location_to_measurements()

    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
#
    meas_data['method_codes'] = meas_data['method_codes'].str.replace(
        " ", "")  # get rid of nasty spaces
    meas_data = meas_data[meas_data['method_codes'].str.contains(
        'LP-PI-TRM|LP-TRM|LP-TRM-TD') == True]  # fish out zero field steps for plotting
    intensity_types = [
        col_name for col_name in meas_data.columns if col_name in Mkeys]
    # plot first intensity method found - normalized to initial value anyway -
    # doesn't matter which used

    int_key = meas_container.find_filled_col(intensity_types)
    if not int_key:
        print("-W- No intensity data found, thellier_magic cannot run")
        return

    # get all the non-null intensity records of the same type
    meas_data = meas_data[meas_data[int_key].notnull()]

    if not len(meas_data):
        print("-W- No intensity data found, thellier_magic cannot run")
        return
    if 'flag' not in meas_data.columns:
        meas_data['flag'] = 'g'  # set the default flag to good
    meas_data = meas_data[meas_data['flag'].str.contains(
        'g') == True]  # only the 'good' measurements
    thel_data = meas_data[meas_data['method_codes'].str.contains(
        'LP-PI-TRM') == True]  # get all the Thellier data
    trm_data = meas_data[meas_data['method_codes'].str.contains(
        'LP-TRM') == True]  # get all the TRM acquisition data
    td_data = meas_data[meas_data['method_codes'].str.contains(
        'LP-TRM-TD') == True]  # get all the TD data
    anis_data = meas_data[meas_data['method_codes'].str.contains(
        'LP-AN') == True]  # get all the anisotropy data
#
# get list of unique specimen names from measurement data
#
    # this is a Series of all the specimen names
    specimen_names = meas_data.specimen.unique()
    specimen_names = specimen_names.tolist()  # turns it into a list
    specimen_names.sort()  # sorts by specimen name
#
# set up new DataFrame for this sessions specimen interpretations
#
    spec_container = cb.MagicDataFrame(
        dtype='specimens', columns=specimen_cols)
    # this is for interpretations from this session
    current_spec_data = spec_container.df
    if specimen == "":  # do all specimens
        k = 0
    else:
        k = specimen_names.index(specimen)  # just do this one
    # define figure numbers for arai, zijderveld and
    #   de-,re-magnetization diagrams
    AZD = {}
    AZD['deremag'], AZD['zijd'], AZD['arai'], AZD['eqarea'] = 1, 2, 3, 4
    pmagplotlib.plot_init(AZD['arai'], 5, 5)
    pmagplotlib.plot_init(AZD['zijd'], 5, 5)
    pmagplotlib.plot_init(AZD['deremag'], 5, 5)
    pmagplotlib.plot_init(AZD['eqarea'], 5, 5)
    if len(trm_data) > 0:
        AZD['TRM'] = 5
        pmagplotlib.plot_init(AZD['TRM'], 5, 5)
    if len(td_data) > 0:
        AZD['TDS'] = 6
        pmagplotlib.plot_init(AZD['TDS'], 5, 5)
    #
    while k < len(specimen_names):
        # set the current specimen for plotting
        this_specimen = specimen_names[k]
        if verbose and this_specimen != "":
            print(this_specimen, k + 1, 'out of ', len(specimen_names))
        if pmagplotlib.isServer:
            this_specimen_measurements = meas_data[meas_data['specimen'] == this_specimen]
            try:
                loc = this_specimen_measurements.loc[:, 'location'].values[0]
            except:
                loc = ""
            try:
                site = this_specimen_measurements.loc[:, 'site'].values[0]
            except:
                site = ""
            try:
                samp = this_specimen_measurements.loc[:, 'sample'].values[0]
            except:
                samp = ""

#
#    set up datablocks
#
        thelblock = thel_data[thel_data['specimen'].str.contains(
            this_specimen) == True]  # fish out this specimen
        trmblock = trm_data[trm_data['specimen'].str.contains(
            this_specimen) == True]  # fish out this specimen
        tdsrecs = td_data[td_data['specimen'].str.contains(
            this_specimen) == True]  # fish out this specimen
        anisblock = anis_data[anis_data['specimen'].str.contains(
            this_specimen) == True]  # fish out the anisotropy data
        if len(prior_spec_data):
            prior_specimen_interpretations = prior_spec_data[prior_spec_data['specimen'].str.contains(
                this_specimen) == True]  # fish out prior interpretation
        else:
            prior_specimen_interpretations = []


#
# sort data into types
#
        araiblock, field = pmag.sortarai(
            thelblock, this_specimen, Zdiff, version=3)
        first_Z = araiblock[0]
        GammaChecks = araiblock[5]
        if len(first_Z) < 3:
            if backup == 0:
                k += 1
                if verbose:
                    print('skipping specimen - moving forward ', this_specimen)
            else:
                k -= 1
                if verbose:
                    print('skipping specimen - moving backward ', this_specimen)
        else:
            backup = 0
            zijdblock, units = pmag.find_dmag_rec(
                this_specimen, thelblock, version=3)
            if start == "" and len(prior_specimen_interpretations) > 0:
                if verbose:
                    print('Looking up saved interpretation....')
#
# get prior interpretation steps
#
                beg_int = pd.to_numeric(
                    prior_specimen_interpretations.meas_step_min.values).tolist()[0]
                end_int = pd.to_numeric(
                    prior_specimen_interpretations.meas_step_max.values).tolist()[0]
            else:
                beg_int, end_int = "", ""
            recnum = 0
            if verbose:
                print("index step Dec   Inc  Int       Gamma")
            for plotrec in zijdblock:
                if plotrec[0] == beg_int:
                    start = recnum  # while we are at it, collect these bounds
                if plotrec[0] == end_int:
                    end = recnum
                if verbose:
                    if GammaChecks != "":
                        gamma = ""
                        for g in GammaChecks:
                            if g[0] == plotrec[0] - 273:
                                gamma = g[1]
                                break
                    if gamma is not "":
                        print('%i     %i %7.1f %7.1f %8.3e %7.1f' % (
                            recnum, plotrec[0] - 273, plotrec[1], plotrec[2], plotrec[3], gamma))
                    else:
                        print('%i     %i %7.1f %7.1f %8.3e ' % (
                            recnum, plotrec[0] - 273, plotrec[1], plotrec[2], plotrec[3]))
                recnum += 1
            for fig in list(AZD.keys()):
                pmagplotlib.clearFIG(AZD[fig])  # clear all figures
            if 'K' in units:
                u = 'K'
            elif 'J' in units:
                u = 'J'
            pmagplotlib.plot_arai_zij(AZD, araiblock, zijdblock,
                               this_specimen, u)
            if verbose:
                pmagplotlib.draw_figs(AZD)
            if cb.is_null(start, False) or cb.is_null(end, False):
                if verbose:
                    ans = input('Return for next specimen, q to quit:  ')
                    if ans == 'q':
                        sys.exit()
                k += 1  # moving on
                start, end = "", ""
                continue

            pars, errcode = pmag.PintPars(
                thelblock, araiblock, zijdblock, start, end, accept, version=3)
            pars['measurement_step_unit'] = "K"
            pars['experiment_type'] = 'LP-PI-TRM'
#
# work on saving interpretations stuff later
#
            if errcode != 1:  # no problem in PintPars
                pars["specimen_lab_field_dc"] = field
                pars["specimen_int"] = -1 * field * pars["specimen_b"]
                pars["er_specimen_name"] = this_specimen
                # pars,kill=pmag.scoreit(pars,this_specimen_interpretation,accept,'',verbose)
                # # deal with this later
                pars["specimen_grade"] = 'None'
                pars['measurement_step_min'] = pars['meas_step_min']
                pars['measurement_step_max'] = pars['meas_step_max']
                if pars['measurement_step_unit'] == 'K':
                    outstr = "specimen     Tmin  Tmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  Gamma_max \n"
                    pars_out = (this_specimen, (pars["meas_step_min"] - 273), (pars["meas_step_max"] - 273), (pars["specimen_int_n"]), 1e6 * (pars["specimen_lab_field_dc"]), 1e6 * (pars["specimen_int"]), pars["specimen_b"], pars["specimen_q"], pars["specimen_f"],
                                pars["specimen_fvds"], pars["specimen_b_beta"], pars["int_mad_free"], pars["int_dang"], pars["int_drats"], pars["int_n_ptrm"], pars["specimen_grade"], np.sqrt(pars["specimen_rsc"]), int(pars["int_md"]), pars["specimen_b_sigma"], pars['specimen_gamma'])
                    outstring = '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f' % pars_out + '\n'
                elif pars['measurement_step_unit'] == 'J':
                    outstr = "specimen     Wmin  Wmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  ThetaMax DeltaMax GammaMax\n"
                    pars_out = (this_specimen, (pars["meas_step_min"]), (pars["meas_step_max"]), (pars["specimen_int_n"]), 1e6 * (pars["specimen_lab_field_dc"]), 1e6 * (pars["specimen_int"]), pars["specimen_b"], pars["specimen_q"], pars["specimen_f"], pars["specimen_fvds"], pars["specimen_b_beta"],
                                pars["specimen_int_mad"], pars["specimen_int_dang"], pars["specimen_drats"], pars["specimen_int_ptrm_n"], pars["specimen_grade"], np.sqrt(pars["specimen_rsc"]), int(pars["specimen_md"]), pars["specimen_b_sigma"], pars["specimen_theta"], pars["specimen_delta"], pars["specimen_gamma"])
                    outstring = '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f %7.1f %7.1f' % pars_out + '\n'
                print(outstr)
                print(outstring)
                pmagplotlib.plot_b(AZD, araiblock, zijdblock, pars)
                mpars = pmag.domean(araiblock[1], start, end, 'DE-BFL')
                if verbose:
                    pmagplotlib.draw_figs(AZD)
                    print('pTRM direction= ', '%7.1f' % (mpars['specimen_dec']), ' %7.1f' % (
                        mpars['specimen_inc']), ' MAD:', '%7.1f' % (mpars['specimen_mad']))
            if len(anisblock) > 0:  # this specimen has anisotropy data
                if verbose:
                    print('Found anisotropy record... but ignoring for now ')
            if plots == 1:
                if fmt != "pmag":
                    files = {}
                    for key in list(AZD.keys()):
                        if pmagplotlib.isServer:
                            files[key] = "LO:_{}_SI:_{}_SA:_{}_SP:_{}_TY:_{}_.{}".format(loc, site, samp, this_specimen, key, fmt)
                        else:
                            files[key] = 'SP:_' + this_specimen + \
                              '_TY:_' + key + '_' + '.' + fmt
                    if pmagplotlib.isServer:
                        black = '#000000'
                        purple = '#800080'
                        titles = {}
                        titles['deremag'] = 'DeReMag Plot'
                        titles['zijd'] = 'Zijderveld Plot'
                        titles['arai'] = 'Arai Plot'
                        titles['TRM'] = 'TRM Acquisition data'
                        titles['eqarea'] = 'Equal Area Plot'
                        AZD = pmagplotlib.add_borders(
                            AZD, titles, black, purple)
                    pmagplotlib.save_plots(AZD, files)
                else:  # save in pmag format
                    print('pmag format no longer supported')
                    #script="grep "+this_specimen+" output.mag | thellier -mfsi"
                    #script=script+' %8.4e'%(field)
                    # min='%i'%((pars["measurement_step_min"]-273))
                    # Max='%i'%((pars["measurement_step_max"]-273))
                    #script=script+" "+min+" "+Max
                    #script=script+" |plotxy;cat mypost >>thellier.ps\n"
                    # pltf.write(script)
                    # pmag.domagicmag(outf,MeasRecs)
            if specimen != "":
                sys.exit()  # syonara
            if verbose:
                ans = input('Return for next specimen, q to quit:  ')
                if ans == 'q':
                    sys.exit()
            start, end  = "", ""
            k += 1  # moving on

#


if __name__ == "__main__":
    main()
