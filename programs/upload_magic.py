#!/usr/bin/env python
from __future__ import print_function
import sys
from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import command_line_extractor as extractor

def main():
    """
    NAME
        upload_magic.py

    DESCRIPTION
        This program will prepare your PMAG text files created by the programs nfo_magic.py,
        zeq_magic.py, thellier_magic.py, mag_magic, specimens_results_magic.py and so on.
        it will check for all the MagIC text files and skip the missing ones

    SYNTAX
        upload_magic.py

    INPUT
        MagIC txt files

    OPTIONS
        -h prints help message and quits
        -all include all the measurement data, default is only those used in interpretations
        -DM specify which MagIC data model number to use (2 or 3).  Default is 3.

    OUTPUT
        upload.txt:  file for uploading to MagIC database
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    else:
        data_model_num = pmag.get_named_arg_from_sys("-DM", 3)
        dataframe = extractor.command_line_dataframe([['cat', False, 0], ['F', False, ''], ['f', False, '']])
        checked_args = extractor.extract_and_check_args(sys.argv, dataframe)
        dir_path, concat = extractor.get_vars(['WD', 'cat'], checked_args)
        if data_model_num == 2:
            ipmag.upload_magic(concat, dir_path)
        else:
            ipmag.upload_magic3(concat, dir_path)


if __name__ == '__main__':
    main()
