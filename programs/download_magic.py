#!/usr/bin/env python
import sys
import pmagpy.command_line_extractor as extractor
import pmagpy.ipmag as ipmag

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
        takes either the upload.txt file created by upload_magic.py or the file
        exported by the MagIC v2.2 console software (downloaded from the MagIC database
        or output by the Console on your PC).

    OPTIONS
        -h prints help message and quits
        -i allows interactive entry of filename
        -f FILE specifies input file name
        -O do not overwrite duplicate Location_* directories while downloading
    """
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    # interactive entry
    if '-i' in sys.argv:
        infile=raw_input("Magic txt file for unpacking? ")
        dir_path = '.'
        input_dir_path = '.'
    # non-interactive
    else:
        dataframe = extractor.command_line_dataframe([['O', False, True]])
        checked_args = extractor.extract_and_check_args(sys.argv, dataframe)
        infile, dir_path, input_dir_path, overwrite = extractor.get_vars(['f', 'WD', 'ID', 'O'], checked_args)

    ipmag.download_magic(infile, dir_path, input_dir_path, overwrite)


                        
if __name__ == '__main__':
    main()

