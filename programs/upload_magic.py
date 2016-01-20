#!/usr/bin/env python
import sys
import pmagpy.ipmag as ipmag
import pmagpy.command_line_extractor as extractor

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

    OUTPUT
        upload.txt:  file for uploading to MagIC database
    """    
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    else:
        dataframe = extractor.command_line_dataframe([['cat', False, 0], ['F', False, ''], ['f', False, '']])
        checked_args = extractor.extract_and_check_args(sys.argv, dataframe)
        dir_path, concat = extractor.get_vars(['WD', 'cat'], checked_args)
        ipmag.upload_magic(concat, dir_path)
        

if __name__ == '__main__':
    main()
