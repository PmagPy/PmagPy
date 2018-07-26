#!/usr/bin/env python
import sys
import os
import pmagpy.pmag as pmag


def main():
    """
    NAME
        mst_magic.py

    DESCRIPTION
        converts MsT data (T,M) to measurements format files

    SYNTAX
        mst_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify T,M  format input file, required
        -fsa SFILE: name with sample, site, location information
        -F FILE: specify output file, default is measurements.txt
        -dc H: specify applied field during measurement, default is 0.5 T
        -syn  : This is a synthetic specimen and has no sample/site/location information
        -spn SPEC: specimen name
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -ncn NCON:  specify naming convention: default is #1 below
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
        INPUT files:
            T M:  T is in Centigrade and M is uncalibrated magnitude

    """
#
# get command line arguments
#

    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    user = pmag.get_named_arg_from_sys("-usr", "")
    labfield = pmag.get_named_arg_from_sys("-dc", '0.5')
    meas_file = pmag.get_named_arg_from_sys("-F", "measurements.txt")
    samp_file = pmag.get_named_arg_from_sys("-fsa", "samples.txt")
    try:
        infile = pmag.get_named_arg_from_sys("-f", reqd=True)
    except pmag.MissingCommandLineArgException:
        print(main.__doc__)
        print("-f  is required option")
        sys.exit()
    specnum = int(pmag.get_named_arg_from_sys("-spc", 0))
    location = pmag.get_named_arg_from_sys("-loc", "")
    specimen_name = pmag.get_named_arg_from_sys("-spn", reqd=True)
    syn = 0
    if "-syn" in args:
        syn = 1
    samp_con = pmag.get_named_arg_from_sys("-ncn", "1")
    if "-ncn" in args:
        ind = args.index("-ncn")
        samp_con = sys.argv[ind+1]
    mst(infile, specimen_name, dir_path, "", meas_file, samp_file,
        user, specnum, samp_con, labfield, location, syn)


def mst(infile, specimen_name, dir_path=".", input_dir_path="",
        meas_file="measurements.txt", samp_infile="samples.txt",
        user="", specnum=0, samp_con="1", labfield=0.5,
        location='', syn=False):

    # deal with input files
    if not input_dir_path:
        input_dir_path = dir_path

    try:
        infile = pmag.resolve_file_name(infile, input_dir_path)
        with open(infile, 'r') as finput:
            data = finput.readlines()
    except (IOError, FileNotFoundError) as ex:
        print(ex)
        print("bad mag file name")
        return False, "bad mag file name"

    samp_file = pmag.resolve_file_name(samp_infile, input_dir_path)
    if os.path.exists(samp_file):
        Samps, file_type = pmag.magic_read(samp_file)
    else:
        Samps = []

    # parse out samp_con
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"


    # initialize some stuff
    specnum = - int(specnum)
    Z = "0"
    citation = 'This study'
    measnum = 1
    MagRecs, specs = [], []
    version_num = pmag.get_version()

    T0 = float(data[0].split()[0])
    for line in data:
        instcode = ""
        if len(line) > 1:
            MagRec = {}
            if syn == 0:
                MagRec['er_location_name'] = location
            MagRec['magic_software_packages'] = version_num
            MagRec["treatment_dc_field"] = labfield
            rec = line.split()
            T = float(rec[0])
            MagRec["measurment_temp"] = '%8.3e' % (
                float(rec[0])+273.)  # temp in kelvin
            if T > T0:
                MagRec["magic_method_codes"] = 'LP-MW-I'
            elif T < T0:
                MagRec["magic_method_codes"] = 'LP-MC-I'
                T0 = T
            else:
                print('skipping repeated temperature step')
                MagRec["magic_method_codes"] = ''
            T0 = T
            MagRec["measurement_magnitude"] = '%10.3e' % (
                float(rec[1]))  # uncalibrated magnitude
            if syn == 0:
                MagRec["er_specimen_name"] = specimen_name
                MagRec["er_site_name"] = ""
                if specnum != 0:
                    MagRec["er_sample_name"] = specimen_name[:specnum]
                else:
                    MagRec["er_sample_name"] = specimen_name
                if Samps:
                    for samp in Samps:
                        if samp["er_sample_name"] == MagRec["er_sample_name"]:
                            MagRec["er_location_name"] = samp["er_location_name"]
                            MagRec["er_site_name"] = samp["er_site_name"]
                            break
                elif int(samp_con) != 6:
                    site = pmag.parse_site(
                        MagRec['er_sample_name'], samp_con, Z)
                    MagRec["er_site_name"] = site
                if MagRec['er_site_name'] == "":
                    print('No site name found for: ',
                          MagRec['er_specimen_name'], MagRec['er_sample_name'])
                if MagRec["er_location_name"] == "":
                    print('no location name for: ', MagRec["er_specimen_name"])
            else:
                MagRec["er_synthetic_name"] = specimen_name
                MagRec["er_location_name"] = ""
                MagRec["er_sample_name"] = ""
                MagRec["er_site_name"] = ""
                MagRec["er_specimen_name"] = ""
            MagRec["magic_instrument_codes"] = instcode
            MagRec["er_analyst_mail_names"] = user
            MagRec["er_citation_names"] = citation
            MagRec["measurement_flag"] = 'g'
            MagRec["measurement_number"] = str(measnum)
            measnum += 1
            MagRecs.append(MagRec)
    for rec in MagRecs:  # sort out the measurements by experiment type
        rec['magic_experiment_name'] = specimen_name
        if rec['magic_method_codes'] == 'LP-MW-I':
            rec["magic_experiment_name"] = specimen_name+':LP-MW-I:Curie'
        elif rec['magic_method_codes'] == 'LP-MC-I':
            rec["magic_experiment_name"] = specimen_name+':LP-MC-I'
    pmag.magic_write(meas_file, MagRecs, 'magic_measurements')
    print("results put in ", meas_file)




if __name__ == "__main__":
    main()
