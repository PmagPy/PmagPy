#!/usr/bin/env python
import sys
from pmagpy import pmag
from pmagpy import ipmag
from pmagpy import command_line_extractor as extractor

def main():
    """
    NAME
        upload_magic.py

    DESCRIPTION
        This program will prepare your MagIC text files  for uploading to the MagIC database
        it will check for all the MagIC text files and skip the missing ones

    SYNTAX
        upload_magic.py

    INPUT
        MagIC txt files

    OPTIONS
        -h prints help message and quits
        -all include all the measurement data, default is only those used in interpretations
        -DM specify MagIC data model 3 (the only supported model). Convert
        Data Model 2 files to Data Model 3 before uploading.

    OUTPUT
        upload file:  file for uploading to MagIC database
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    else:
        data_model_num = pmag.get_named_arg("-DM", 3)
        data_model_num = int(float(data_model_num))
        if data_model_num != 3:
            raise SystemExit(
                "-E- upload_magic supports MagIC Data Model 3 only. "
                "Convert Data Model 2 files to Data Model 3 before uploading."
            )
        dataframe = extractor.command_line_dataframe([['cat', False, 0], ['F', False, ''], ['f', False, '']])
        checked_args = extractor.extract_and_check_args(sys.argv, dataframe)
        dir_path, concat = extractor.get_vars(['WD', 'cat'], checked_args)
        ipmag.upload_magic(concat, dir_path)


if __name__ == '__main__':
    main()
