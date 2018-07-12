#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag


def main():
    """
    NAME
        mini_magic.py

    DESCRIPTION
        converts the Yale minispin format to magic_measurements format files

    SYNTAX
        mini_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -ncn NCON:  specify naming convention: default is #1 below
        -A: don't average replicate measurements
        -vol: volume assumed for measurement in cm^3
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

            [8] synthetic - has no site name
            [9] ODP naming convention
            [10] LL-SI-SA-SP_STEP where LL is location, SI is site, SA is sample and SP is specimen and STEP is demagnetization step

    INPUT
        Must put separate experiments (all AF, thermal,  etc.) in
           seperate files

        Format of Yale MINI files:
        LL-SI-SP_STEP, Declination, Inclination, Intensity (mA/m), X,Y,Z


    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
# initialize some stuff
    methcode = "LP-NO"
    demag = "N"
    citation = 'This study'

#
# get command line arguments
#
    data_model_num = int(float(pmag.get_named_arg_from_sys("-DM", 3)))
    user = pmag.get_named_arg_from_sys("-usr", "")
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    inst = pmag.get_named_arg_from_sys("-inst", "")
    magfile = pmag.get_named_arg_from_sys("-f", reqd=True)
    magfile = pmag.resolve_file_name(magfile, dir_path)
    if "-A" in args:
        noave = 1
    else:
        noave = 0

    try:
        finput = open(magfile, 'r')
        lines = finput.readlines()
    except OSError:
        print("bad mag file name")
        sys.exit()
    if data_model_num == 2:
        meas_file = pmag.get_named_arg_from_sys("-F", "magic_measurements.txt")
    else:
        meas_file = pmag.get_named_arg_from_sys("-F", "measurements.txt")
    meas_file = pmag.resolve_file_name(meas_file, dir_path)
    specnum = pmag.get_named_arg_from_sys("-spc", 0)
    specnum = -specnum
    volume = pmag.get_named_arg_from_sys("-vol", 10) # assume a volume of 10 cc if not provided
    volume = 1e-6 * volume
    if '-LP' in args:
        ind = args.index("-LP")
        codelist = args[ind+1]
        codes = codelist.split(':')
        if "AF" in codes:
            demag = 'AF'
            methcode = "LT-AF-Z"
        if "T" in codes:
            demag = "T"
    #
    MagRecs = []
    version_num = pmag.get_version()

    #
    if data_model_num == 2:
        spec_col = "er_specimen_name"
        loc_col = "er_location_name"
        site_col = "er_site_col"
        samp_col = "er_sample_name"
        software_col = "magic_software_packages"
        treat_temp_col = "treatment_temp"
        meas_temp_col = "measurement_temp"
        treat_ac_col = "treatment_ac_field"
        treat_dc_col = "treatment_dc_field"
        treat_dc_phi_col = "treatment_dc_field_phi"
        treat_dc_theta_col = "treatment_dc_field_theta"
        moment_col = "measurement_magn_moment"
        dec_col = "measurement_dec"
        inc_col = "measurement_inc"
        instrument_col = "magic_instrument_codes"
        analyst_col = "er_analyst_mail_names"
        citations_col = "er_citation_names"
        methods_col = "magic_method_codes"
        quality_col = "measurement_flag"
        meas_standard_col = "measurement_standard"
        meas_name_col = "measurement_number"
    else:
        spec_col = "specimen"
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        software_col = "software_packages"
        treat_temp_col = "treat_temp"
        meas_temp_col = "meas_temp"
        treat_ac_col = "treat_ac_field"
        treat_dc_col = "treat_dc_field"
        treat_dc_phi_col = "treat_dc_field_phi"
        treat_dc_theta_col = "treat_dc_field_theta"
        moment_col = "magn_moment"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        instrument_col = "instrument_codes"
        analyst_col = "analysts"
        citations_col = "citations"
        methods_col = "method_codes"
        quality_col = "quality"
        meas_standard_col = "standard"
        meas_name_col = "measurement"

    # go through the measurements
    for line in lines:
        rec = line.split(',')
        if len(rec) > 1:
            MagRec = {}
            IDs = rec[0].split('_')
            treat = IDs[1]
            MagRec[spec_col] = IDs[0]
            #print(MagRec[spec_col])
            sids = IDs[0].split('-')
            MagRec[loc_col] = sids[0]
            MagRec[site_col] = sids[0]+'-'+sids[1]
            if len(sids) == 2:
                MagRec[samp_col] = IDs[0]
            else:
                MagRec[samp_col] = sids[0]+'-'+sids[1]+'-'+sids[2]
            #print(MagRec)
            MagRec[software_col] = version_num
            MagRec[treat_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[meas_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[treat_ac_col] = '0'
            MagRec[treat_dc_col] = '0'
            MagRec[treat_dc_phi_col] = '0'
            MagRec[treat_dc_theta_col] = '0'
            meas_type = "LT-NO"
            if demag == "AF":
                MagRec[treat_ac_col] = '%8.3e' % (
                    float(treat)*1e-3)  # peak field in tesla
            if demag == "T":
                meas_type = "LT-T-Z"
                MagRec[treat_dc_col] = '%8.3e' % (0)
                MagRec[treat_temp_col] = '%8.3e' % (
                    float(treat)+273.)  # temp in kelvin
            if demag == "N":
                meas_type = "LT-NO"
                MagRec[treat_ac_col] = '0'
                MagRec[treat_dc_col] = '0'
            MagRec[moment_col] = '%10.3e' % (
                volume*float(rec[3])*1e-3)  # moment in Am2 (from mA/m)
            MagRec[dec_col] = rec[1]
            MagRec[inc_col] = rec[2]
            MagRec[instrument_col] = inst
            MagRec[analyst_col] = user
            MagRec[citations_col] = citation
            MagRec[methods_col] = methcode.strip(':')
            MagRec[quality_col] = 'g'
            MagRec[meas_standard_col] = 'u'
            MagRec[meas_name_col] = '1'
            MagRecs.append(MagRec)

    if data_model_num == 2:
        MagOuts = pmag.measurements_methods(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    else:
        print(MagRecs[9:14])
        MagOuts = pmag.measurements_methods3(MagRecs, noave)
        pmag.magic_write(meas_file, MagRecs, 'measurements')
    print("results put in ", meas_file)


if __name__ == "__main__":
    main()
