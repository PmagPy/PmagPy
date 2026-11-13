#!/usr/bin/env python
import os
import sys
import pmagpy.command_line_extractor as extractor
import pmagpy.ipmag as ipmag
from pmagpy import pmag

def main():
    """
    NAME
        download_magic.py

    DESCRIPTION
        unpacks a magic formatted smartbook .txt file from the MagIC database into the
        tab delimited MagIC format txt files for use with the MagIC-Py programs.

    SYNTAX
        download_magic.py command line options]
    INPUT
        takes either the upload.txt file created by upload_magic.py or a file
        downloaded from the MagIC database (http://earthref.org/MagIC)


    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of filename
        -f FILE specifies input file name
        -sep write location data to separate subdirectories (Location_*), (default False)
        -O do not overwrite duplicate Location_* directories while downloading
        -DM 3: MagIC Data Model 3 is the only supported model
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if float(pmag.get_named_arg("-DM", 3)) != 3:
        raise SystemExit(
            "-E- download_magic supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before unpacking."
        )
    overwrite = pmag.get_flag_arg_from_sys("-O", true=False, false=True)
    sep = pmag.get_flag_arg_from_sys("-sep", true=True, false=False)
    data_model = 3
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    # interactive entry
    if '-i' in sys.argv:
        infile=input("Magic txt file for unpacking? ")
        dir_path = '.'
        input_dir_path = '.'
    # non-interactive
    else:
        infile = pmag.get_named_arg("-f", reqd=True)
        dir_path = pmag.get_named_arg("-WD", default_val=".", reqd=False)
        input_dir_path = pmag.get_named_arg("-ID", default_val=".", reqd=False)

    #if '-ID' not in sys.argv and '-WD' in sys.argv:
    #    input_dir_path = dir_path
    if "-WD" not in sys.argv and "-ID" not in sys.argv:
        input_dir_path = os.path.split(infile)[0]
    if not input_dir_path:
        input_dir_path = "."

    ipmag.download_magic(infile, dir_path, input_dir_path, overwrite, True, data_model, sep)



if __name__ == '__main__':
    main()
