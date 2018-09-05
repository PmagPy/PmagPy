#!/usr/bin/env python

import sys
from pmagpy import pmag
from pmagpy import convert_2_magic as convert


def main():
    """
    NAME
        s_magic.py

    DESCRIPTION
        converts .s format data to measurements  format.

    SYNTAX
        s_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -DM DATA_MODEL_NUM data model number (default is 3)
        -f SFILE specifies the .s file name
        -sig last column has sigma
        -typ Anisotropy type:  AMS,AARM,ATRM (default is AMS)
        -F FILE specifies the specimens formatted file name
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
        FILE:  specimens.txt

    INPUT
        X11,X22,X33,X12,X23,X13  (.s format file)
        X11,X22,X33,X12,X23,X13,sigma (.s format file with -sig option)
        SID, X11,X22,X33,X12,X23,X13  (.s format file with -n option)

    OUTPUT
        specimens.txt format file

    NOTE
        because .s files do not have specimen names or location information, the output MagIC files
        will have to be changed prior to importing to data base.
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    data_model_num = pmag.get_named_arg("-DM", 3)
    data_model_num = int(float(data_model_num))
    sfile = pmag.get_named_arg("-f", reqd=True)
    if data_model_num == 2:
       anisfile = pmag.get_named_arg("-F", "rmag_anisotropy.txt")
    else:
        anisfile = pmag.get_named_arg("-F", "specimens.txt")
    location = pmag.get_named_arg("-loc", "unknown")
    user = pmag.get_named_arg("-usr", "")
    sitename = pmag.get_named_arg("unknown", "")
    specnum = pmag.get_named_arg("-spc", 0)
    specnum = -int(specnum)
    dir_path = pmag.get_named_arg("-WD", ".")
    name = pmag.get_flag_arg_from_sys("-n")
    sigma = pmag.get_flag_arg_from_sys("-sig")
    spec = pmag.get_named_arg("-spn", "unknown")
    atype = pmag.get_named_arg("-typ", 'AMS')
    samp_con = pmag.get_named_arg("-ncn", "1")
    #if '-sig' in sys.argv:
    #    sigma = 1
    #if "-n" in sys.argv:
    #    name = 1
    coord_type = pmag.get_named_arg("-crd", 's')
    convert.s_magic(sfile, anisfile, dir_path, atype,
            coord_type, sigma, samp_con, specnum,
            location, spec, sitename, user, data_model_num, name)
    #



    #
if __name__ == "__main__":
    main()
