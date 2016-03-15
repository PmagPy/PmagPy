#!/usr/bin/env python
#import pmag,sys,string
import sys
import pmagpy.ipmag as ipmag
import pmagpy.command_line_extractor as extractor

def main():
    """ 
    iodp_samples_magic.py
    OPTIONS:
        -f FILE, input csv file
        -Fsa FILE, output er_samples.txt file for updating, default is to overwrite er_samples.txt
    """
    if "-h" in sys.argv:
        print main.__doc__
        sys.exit()
        
    dataframe = extractor.command_line_dataframe([['WD', False, '.'], ['ID', False, '.'], ['f', True, ''], ['Fsa', False, None]])
    args = sys.argv
    checked_args = extractor.extract_and_check_args(args, dataframe)
    samp_file, output_samp_file, output_dir_path, input_dir_path = extractor.get_vars(['f', 'Fsa', 'WD', 'ID'], checked_args)
    ipmag.iodp_samples_magic(samp_file, output_samp_file, output_dir_path, input_dir_path)


if __name__ == "__main__":
    main()
