#!/usr/bin/env python
from __future__ import print_function
import sys
import os
import pmagpy.pmag as pmag
from pmagpy import new_builder as nb


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
        -A: don't average replicate measurements
        -vol: volume assumed for measurement in cm^3 (default 10 cc)
        -DM NUM: MagIC data model (2 or 3, default 3)

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

    if data_model_num == 2:
        meas_file = pmag.get_named_arg_from_sys("-F", "magic_measurements.txt")
    else:
        meas_file = pmag.get_named_arg_from_sys("-F", "measurements.txt")
    meas_file = pmag.resolve_file_name(meas_file, dir_path)
    volume = pmag.get_named_arg_from_sys("-vol", 10) # assume a volume of 10 cc if not provided
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
    convert(magfile, dir_path, meas_file, data_model_num,
            volume, noave, inst, user, demag, methcode)

def convert(magfile, dir_path='.', meas_file='measurements.txt',
            data_model_num=3, volume=10, noave=0,
            inst="", user="", demag='N', methcode="LP-NO"):
    # initialize
    citation = 'This study'
    MagRecs = []
    version_num = pmag.get_version()
    try:
        finput = open(magfile, 'r')
        lines = finput.readlines()
    except OSError:
        print("bad mag file name")
        sys.exit()
    # convert volume
    volume = 1e-6 * float(volume)
    # set col names based on MagIC 2 or 3
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
        MagOuts = pmag.measurements_methods3(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'measurements')
        # nicely parse all the specimen/sample/site/location data
        # and write it to file as well
        dir_path = os.path.split(meas_file)[0]
        con = nb.Contribution(dir_path, read_tables=['measurements'])
        con.propagate_measurement_info()
        for table in con.tables:
            con.write_table_to_file(table)
    print("results put in ", meas_file)


if __name__ == "__main__":
    main()
