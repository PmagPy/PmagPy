#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
import sys
from past.utils import old_div
import pmagpy.pmag as pmag


def main():
    """
    NAME
        s_magic.py

    DESCRIPTION
        converts .s format data to magic_measurements  format.

    SYNTAX
        s_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -DM DATA_MODEL_NUM data model number (default is 3)
        -f SFILE specifies the .s file name
        -sig last column has sigma
        -typ Anisotropy type:  AMS,AARM,ATRM (default is AMS)
        -F RFILE specifies the rmag_anisotropy file name
        -usr USER specify username
        -loc location specify location/study name
        -spc NUM : specify number of characters to
              designate a  specimen, default = 0
        -spn SPECNAME, this specimen has the name SPECNAME
        -n first column has specimen name
        -crd [s,g,t], specify coordinate system of data
           s=specimen,g=geographic,t=tilt adjusted, default is 's'
        -ncn NCON: naming convention
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] sample = site
            [6] sample, site, location info in er_samples.txt -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
            NB: all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.


    DEFAULT
        RFILE:  rmag_anisotropy.txt

    INPUT
        X11,X22,X33,X12,X23,X13  (.s format file)
        X11,X22,X33,X12,X23,X13,sigma (.s format file with -sig option)
        SID, X11,X22,X33,X12,X23,X13  (.s format file with -n option)

    OUTPUT
        rmag_anisotropy.txt format file

    NOTE
        because .s files do not have specimen names or location information, the output MagIC files
        will have to be changed prior to importing to data base.
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    data_model_num = pmag.get_named_arg_from_sys("-DM", 3)
    sfile = pmag.get_named_arg_from_sys("-f", reqd=True)
    if data_model_num == 2:
        anisfile = pmag.get_named_arg_from_sys("-F", "rmag_anisotropy.txt")
    else:
        anisfile = pmag.get_named_arg_from_sys("-F", "specimens.txt")
    location = pmag.get_named_arg_from_sys("-loc", "unknown")
    user = pmag.get_named_arg_from_sys("-usr", "")
    sitename = pmag.get_named_arg_from_sys("unknown", "")
    specnum = pmag.get_named_arg_from_sys("-spc", 0)
    specnum = -specnum
    dir_path = pmag.get_named_arg_from_sys("-WD", ".")
    name = pmag.get_flag_arg_from_sys("-n")
    sigma = pmag.get_flag_arg_from_sys("-sig")
    print('sigma', sigma)
    spec = pmag.get_named_arg_from_sys("-spn", "unknown")
    atype = pmag.get_named_arg_from_sys("-typ", 'AMS')
    #if '-sig' in sys.argv:
    #    sigma = 1
    print('name', name)
    print('sigma', sigma)
    #if "-n" in sys.argv:
    #    name = 1
    coord_type = pmag.get_named_arg_from_sys("-crd", 's')
    coord_dict = {'s': '-1', 't': '100', 'g': '0'}
    coord = coord_dict.get(coord_type, '-1')
    samp_con, Z = "", 1
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        samp_con = sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if samp_con == '6':
            print("option [6] is not currently supported")
            return
            #Samps, filetype = pmag.magic_read(dirpath+'/er_samples.txt')
    #
    # get down to bidness
    sfile = pmag.resolve_file_name(sfile, dir_path)
    anisfile = pmag.resolve_file_name(anisfile, dir_path)
    with open(sfile, 'r') as f:
        lines = f.readlines()
    AnisRecs = []
    citation = "This study"
    # read in data
    for line in lines:
        AnisRec = {}
        rec = line.split()
        if name == 1:
            k = 1
            spec = rec[0]
        else:
            k = 0
        trace = float(rec[k])+float(rec[k+1])+float(rec[k+2])
        s1 = '%10.9e' % (old_div(float(rec[k]), trace))
        s2 = '%10.9e' % (old_div(float(rec[k+1]), trace))
        s3 = '%10.9e' % (old_div(float(rec[k+2]), trace))
        s4 = '%10.9e' % (old_div(float(rec[k+3]), trace))
        s5 = '%10.9e' % (old_div(float(rec[k+4]), trace))
        s6 = '%10.9e' % (old_div(float(rec[k+5]), trace))
        AnisRec["er_citation_names"] = citation
        AnisRec["er_specimen_name"] = spec
        if specnum != 0:
            AnisRec["er_sample_name"] = spec[:specnum]
        else:
            AnisRec["er_sample_name"] = spec
        #if samp_con == "6":
        #    for samp in Samps:
        #        if samp['er_sample_name'] == AnisRec["er_sample_name"]:
        #            sitename = samp['er_site_name']
        #            location = samp['er_location_name']
        if samp_con != "":
            sitename = pmag.parse_site(AnisRec['er_sample_name'], samp_con, Z)
        AnisRec["er_location_name"] = location
        AnisRec["er_site_name"] = sitename
        AnisRec["er_anylist_mail_names"] = user
        if atype == 'AMS':
            AnisRec["anisotropy_type"] = "AMS"
            AnisRec["magic_experiment_names"] = spec+":LP-X"
        else:
            AnisRec["anisotropy_type"] = atype
            AnisRec["magic_experiment_names"] = spec+":LP-"+atype
        AnisRec["anisotropy_s1"] = s1
        AnisRec["anisotropy_s2"] = s2
        AnisRec["anisotropy_s3"] = s3
        AnisRec["anisotropy_s4"] = s4
        AnisRec["anisotropy_s5"] = s5
        AnisRec["anisotropy_s6"] = s6
        if sigma == 1:
            AnisRec["anisotropy_sigma"] = '%10.8e' % (
                old_div(float(rec[k+6]), trace))
        AnisRec["anisotropy_unit"] = 'SI'
        AnisRec["anisotropy_tilt_correction"] = coord
        AnisRec["magic_method_codes"] = 'LP-' + atype
        AnisRecs.append(AnisRec)
    pmag.magic_write(anisfile, AnisRecs, 'rmag_anisotropy')
    print('data saved in ', anisfile)


    #
if __name__ == "__main__":
    main()
