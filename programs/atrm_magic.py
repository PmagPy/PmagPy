#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div
import os
import sys
import numpy
import pmagpy.pmag as pmag
from pmagpy.mapping import map_magic


def main():
    """
    NAME
        atrm_magic.py

    DESCRIPTION
        Converts ATRM  data to best-fit tensor (6 elements plus sigma)
         Original program ARMcrunch written to accomodate ARM anisotropy data
          collected from 6 axial directions (+X,+Y,+Z,-X,-Y,-Z) using the
          off-axis remanence terms to construct the tensor. A better way to
          do the anisotropy of ARMs is to use 9,12 or 15 measurements in
          the Hext rotational scheme.

    SYNTAX
        atrm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, default is atrm_measurements.txt
        -Fa FILE: specify anisotropy output file, default is trm_anisotropy.txt (MagIC 2.5 only)
        -Fr FILE: specify results output file, default is atrm_results.txt (MagIC 2.5 only)
        -Fsi FILE: specify output file, default is specimens.txt (MagIC 3 only)
        -DM DATA_MODEL: specify MagIC 2 or MagIC 3, default is 3

    INPUT
        Input for the present program is a TRM acquisition data with an optional baseline.
      The order of the measurements is:
    Decs=[0,90,0,180,270,0,0,90,0]
    Incs=[0,0,90,0,0,-90,0,0,90]
     The last two measurements are optional

    """
    # initialize some parameters
    args = sys.argv
    user = ""
    meas_file = "atrm_measurements.txt"
    rmag_anis = "trm_anisotropy.txt"
    rmag_res = "atrm_results.txt"
    dir_path = '.'
    #
    # get name of file from command line
    #
    if '-WD' in args:
        ind = args.index('-WD')
        dir_path = args[ind + 1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-usr" in args:
        ind = args.index("-usr")
        user = sys.argv[ind + 1]
    if "-f" in args:
        ind = args.index("-f")
        meas_file = sys.argv[ind + 1]
    if "-Fa" in args:
        ind = args.index("-Fa")
        rmag_anis = args[ind + 1]
    if "-Fr" in args:
        ind = args.index("-Fr")
        rmag_res = args[ind + 1]
    data_model_num = int(pmag.get_named_arg_from_sys("-DM", 3))
    spec_file = pmag.get_named_arg_from_sys("-Fsi", "specimens.txt")
    spec_file = os.path.join(dir_path, spec_file)

    meas_file = dir_path + '/' + meas_file
    rmag_anis = dir_path + '/' + rmag_anis
    rmag_res = dir_path + '/' + rmag_res

    # read in data
    if data_model_num == 3:
        meas_data = []
        meas_data3, file_type = pmag.magic_read(meas_file)
        if file_type != 'measurements':
            print(file_type, "This is not a valid measurements file ")
            sys.exit()
        # convert meas_data to 2.5
        for rec in meas_data3:
            meas_map = map_magic.meas_magic3_2_magic2_map
            meas_data.append(map_magic.mapping(rec, meas_map))
    else:
        meas_data, file_type = pmag.magic_read(meas_file)
        if file_type != 'magic_measurements':
            print(file_type, "This is not a valid magic_measurements file ")
            sys.exit()

    meas_data = pmag.get_dictitem(
        meas_data, 'magic_method_codes', 'LP-AN-TRM', 'has')
    #
    #
    # get sorted list of unique specimen names
    ssort = []
    for rec in meas_data:
        spec = rec["er_specimen_name"]
        if spec not in ssort:
            ssort.append(spec)
    sids = sorted(ssort)
    #
    #
    # work on each specimen
    #
    specimen, npos = 0, 6
    RmagSpecRecs, RmagResRecs = [], []
    SpecRecs, SpecRecs3 = [], []
    while specimen < len(sids):
        nmeas = 0
        s = sids[specimen]
        RmagSpecRec = {}
        RmagResRec = {}
        BX, X = [], []
        method_codes = []
        Spec0 = ""
    #
    # find the data from the meas_data file for this sample
        # and get dec, inc, int and convert to x,y,z
        #
        # fish out data for this specimen name
        data = pmag.get_dictitem(meas_data, 'er_specimen_name', s, 'T')
        if len(data) > 5:
            RmagSpecRec["rmag_anisotropy_name"] = data[0]["er_specimen_name"]
            RmagSpecRec["er_location_name"] = data[0].get("er_location_name", "")
            RmagSpecRec["er_specimen_name"] = data[0]["er_specimen_name"]
            RmagSpecRec["er_sample_name"] = data[0].get("er_sample_name", "")
            RmagSpecRec["er_site_name"] = data[0].get("er_site_name", "")
            RmagSpecRec["magic_experiment_names"] = RmagSpecRec["rmag_anisotropy_name"] + ":ATRM"
            RmagSpecRec["er_citation_names"] = "This study"
            RmagResRec["rmag_result_name"] = data[0]["er_specimen_name"] + ":ATRM"
            RmagResRec["er_location_names"] = data[0].get("er_location_names", "")
            RmagResRec["er_specimen_names"] = data[0]["er_specimen_name"]
            RmagResRec["er_sample_names"] = data[0].get("er_sample_name", "")
            RmagResRec["er_site_names"] = data[0].get("er_site_name", "")
            RmagResRec["magic_experiment_names"] = RmagSpecRec["rmag_anisotropy_name"] + ":ATRM"
            RmagResRec["er_citation_names"] = "This study"
            RmagSpecRec["anisotropy_type"] = "ATRM"
            if "magic_instrument_codes" in list(data[0].keys()):
                RmagSpecRec["magic_instrument_codes"] = data[0]["magic_instrument_codes"]
            else:
                RmagSpecRec["magic_instrument_codes"] = ""
                RmagSpecRec["anisotropy_description"] = "Hext statistics adapted to ATRM"
            for rec in data:
                meths = rec['magic_method_codes'].strip().split(':')
                Dir = []
                Dir.append(float(rec["measurement_dec"]))
                Dir.append(float(rec["measurement_inc"]))
                Dir.append(float(rec["measurement_magn_moment"]))
                if "LT-T-Z" in meths:
                    BX.append(pmag.dir2cart(Dir))  # append baseline steps
                elif "LT-T-I" in meths:
                    X.append(pmag.dir2cart(Dir))
                    nmeas += 1
    #
        if len(BX) == 1:
            for i in range(len(X) - 1):
                BX.append(BX[0])  # assume first 0 field step as baseline
        elif len(BX) == 0:  # assume baseline is zero
            for i in range(len(X)):
                BX.append([0., 0., 0.])  # assume baseline of 0
        elif len(BX) != len(X):  # if BX isn't just one measurement or one in between every infield step, just assume it is zero
            print('something odd about the baselines - just assuming zero')
            for i in range(len(X)):
                BX.append([0., 0., 0.])  # assume baseline of 0
        if nmeas < 6:  # must have at least 6 measurements right now -
            print('skipping specimen ', s, ' too few measurements')
            specimen += 1
        else:
            # B matrix made from design matrix for positions
            B, H, tmpH = pmag.designATRM(npos)
        #
        # subtract optional baseline and put in a work array
        #
            work = numpy.zeros((nmeas, 3), 'f')
            for i in range(nmeas):
                for j in range(3):
                    # subtract baseline, if available
                    work[i][j] = X[i][j] - BX[i][j]
        #
        # calculate tensor elements
        # first put ARM components in w vector
        #
            w = numpy.zeros((npos * 3), 'f')
            index = 0
            for i in range(npos):
                for j in range(3):
                    w[index] = work[i][j]
                    index += 1
            s = numpy.zeros((6), 'f')  # initialize the s matrix
            for i in range(6):
                for j in range(len(w)):
                    s[i] += B[i][j] * w[j]
            trace = s[0] + s[1] + s[2]   # normalize by the trace
            for i in range(6):
                s[i] = old_div(s[i], trace)
            a = pmag.s2a(s)

        #------------------------------------------------------------
        #  Calculating dels is different than in the Kappabridge
        #  routine. Use trace normalized tensor (a) and the applied
        #  unit field directions (tmpH) to generate model X,Y,Z
        #  components. Then compare these with the measured values.
        #------------------------------------------------------------
            S = 0.
            comp = numpy.zeros((npos * 3), 'f')
            for i in range(npos):
                for j in range(3):
                    index = i * 3 + j
                    compare = a[j][0] * tmpH[i][0] + a[j][1] * \
                        tmpH[i][1] + a[j][2] * tmpH[i][2]
                    comp[index] = compare
            for i in range(npos * 3):
                d = old_div(w[i], trace) - comp[i]  # del values
                S += d * d
            nf = float(npos * 3. - 6.)  # number of degrees of freedom
            if S > 0:
                sigma = numpy.sqrt(old_div(S, nf))
            else:
                sigma = 0
            hpars = pmag.dohext(nf, sigma, s)
        #
        # prepare for output
        #
            RmagSpecRec["anisotropy_s1"] = '%8.6f' % (s[0])
            RmagSpecRec["anisotropy_s2"] = '%8.6f' % (s[1])
            RmagSpecRec["anisotropy_s3"] = '%8.6f' % (s[2])
            RmagSpecRec["anisotropy_s4"] = '%8.6f' % (s[3])
            RmagSpecRec["anisotropy_s5"] = '%8.6f' % (s[4])
            RmagSpecRec["anisotropy_s6"] = '%8.6f' % (s[5])
            RmagSpecRec["anisotropy_mean"] = '%8.3e' % (old_div(trace, 3))
            RmagSpecRec["anisotropy_sigma"] = '%8.6f' % (sigma)
            RmagSpecRec["anisotropy_unit"] = "Am^2"
            RmagSpecRec["anisotropy_n"] = '%i' % (npos)
            RmagSpecRec["anisotropy_tilt_correction"] = '-1'
            # used by thellier_gui - must be taken out for uploading
            RmagSpecRec["anisotropy_F"] = '%7.1f ' % (hpars["F"])
            # used by thellier_gui - must be taken out for uploading
            RmagSpecRec["anisotropy_F_crit"] = hpars["F_crit"]
            RmagResRec["anisotropy_t1"] = '%8.6f ' % (hpars["t1"])
            RmagResRec["anisotropy_t2"] = '%8.6f ' % (hpars["t2"])
            RmagResRec["anisotropy_t3"] = '%8.6f ' % (hpars["t3"])
            RmagResRec["anisotropy_v1_dec"] = '%7.1f ' % (hpars["v1_dec"])
            RmagResRec["anisotropy_v2_dec"] = '%7.1f ' % (hpars["v2_dec"])
            RmagResRec["anisotropy_v3_dec"] = '%7.1f ' % (hpars["v3_dec"])
            RmagResRec["anisotropy_v1_inc"] = '%7.1f ' % (hpars["v1_inc"])
            RmagResRec["anisotropy_v2_inc"] = '%7.1f ' % (hpars["v2_inc"])
            RmagResRec["anisotropy_v3_inc"] = '%7.1f ' % (hpars["v3_inc"])
            RmagResRec["anisotropy_ftest"] = '%7.1f ' % (hpars["F"])
            RmagResRec["anisotropy_ftest12"] = '%7.1f ' % (hpars["F12"])
            RmagResRec["anisotropy_ftest23"] = '%7.1f ' % (hpars["F23"])
            RmagResRec["result_description"] = 'Critical F: ' + \
                hpars["F_crit"] + ';Critical F12/F13: ' + hpars["F12_crit"]
            if hpars["e12"] > hpars["e13"]:
                RmagResRec["anisotropy_v1_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v1_zeta_dec"] = '%7.1f ' % (
                    hpars['v2_dec'])
                RmagResRec["anisotropy_v1_zeta_inc"] = '%7.1f ' % (
                    hpars['v2_inc'])
                RmagResRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v2_zeta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
                RmagResRec["anisotropy_v1_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v1_eta_dec"] = '%7.1f ' % (
                    hpars['v3_dec'])
                RmagResRec["anisotropy_v1_eta_inc"] = '%7.1f ' % (
                    hpars['v3_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v3_eta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v3_eta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
            else:
                RmagResRec["anisotropy_v1_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v1_zeta_dec"] = '%7.1f ' % (
                    hpars['v3_dec'])
                RmagResRec["anisotropy_v1_zeta_inc"] = '%7.1f ' % (
                    hpars['v3_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v3_zeta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
                RmagResRec["anisotropy_v1_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v1_eta_dec"] = '%7.1f ' % (
                    hpars['v2_dec'])
                RmagResRec["anisotropy_v1_eta_inc"] = '%7.1f ' % (
                    hpars['v2_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v2_eta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v2_eta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
            if hpars["e23"] > hpars['e12']:
                RmagResRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e23'])
                RmagResRec["anisotropy_v2_zeta_dec"] = '%7.1f ' % (
                    hpars['v3_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"] = '%7.1f ' % (
                    hpars['v3_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e23'])
                RmagResRec["anisotropy_v3_zeta_dec"] = '%7.1f ' % (
                    hpars['v2_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"] = '%7.1f ' % (
                    hpars['v2_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v3_eta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v3_eta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v2_eta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v2_eta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
            else:
                RmagResRec["anisotropy_v2_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e12'])
                RmagResRec["anisotropy_v2_zeta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e23'])
                RmagResRec["anisotropy_v3_eta_dec"] = '%7.1f ' % (
                    hpars['v2_dec'])
                RmagResRec["anisotropy_v3_eta_inc"] = '%7.1f ' % (
                    hpars['v2_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"] = '%7.1f ' % (
                    hpars['e13'])
                RmagResRec["anisotropy_v3_zeta_dec"] = '%7.1f ' % (
                    hpars['v1_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"] = '%7.1f ' % (
                    hpars['v1_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"] = '%7.1f ' % (
                    hpars['e23'])
                RmagResRec["anisotropy_v2_eta_dec"] = '%7.1f ' % (
                    hpars['v3_dec'])
                RmagResRec["anisotropy_v2_eta_inc"] = '%7.1f ' % (
                    hpars['v3_inc'])
            RmagResRec["tilt_correction"] = '-1'
            RmagResRec["anisotropy_type"] = 'ATRM'
            RmagResRec["magic_method_codes"] = 'LP-AN-TRM:AE-H'
            RmagSpecRec["magic_method_codes"] = 'LP-AN-TRM:AE-H'
            RmagResRec["magic_software_packages"] = pmag.get_version()
            RmagSpecRec["magic_software_packages"] = pmag.get_version()
            RmagSpecRecs.append(RmagSpecRec)
            RmagResRecs.append(RmagResRec)
            specimen += 1
        if data_model_num == 3:
            SpecRec = RmagResRec.copy()
            SpecRec.update(RmagSpecRec)
            SpecRecs.append(SpecRec)

    # finished iterating through specimens,
    # now we need to write out the data to files
    if data_model_num == 3:
        # translate records
        for rec in SpecRecs:
            rec3 = map_magic.convert_aniso('magic3', rec)
            SpecRecs3.append(rec3)

        # write output to 3.0 specimens file
        pmag.magic_write(spec_file, SpecRecs3, 'specimens')
        print("specimen data stored in {}".format(spec_file))

    else:
        # write output to 2.5 rmag_ files
        pmag.magic_write(rmag_anis, RmagSpecRecs, 'rmag_anisotropy')
        print("specimen tensor elements stored in ", rmag_anis)
        pmag.magic_write(rmag_res, RmagResRecs, 'rmag_results')
        print("specimen statistics and eigenparameters stored in ", rmag_res)


if __name__ == "__main__":
    main()
