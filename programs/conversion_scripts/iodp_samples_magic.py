#!/usr/bin/env python
#import pmag,sys,string
import sys
import pmagpy.command_line_extractor as extractor
from pmagpy import convert_2_magic as convert

def main():
    """
    iodp_samples_magic.py
    OPTIONS:
        -f FILE, input csv file
        -Fsa FILE, output samples file for updating, default is to overwrite existing samples file
    """
    if "-h" in sys.argv:
        print(main.__doc__)
        sys.exit()

    dataframe = extractor.command_line_dataframe([['WD', False, '.'], ['ID', False, '.'], ['f', True, ''], ['Fsa', False, 'samples.txt']])
    args = sys.argv
    checked_args = extractor.extract_and_check_args(args, dataframe)
    samp_file, output_samp_file, output_dir_path, input_dir_path = extractor.get_vars(['f', 'Fsa', 'WD', 'ID'], checked_args)
    ran, error = convert.iodp_samples_csv(samp_file, samp_file=output_samp_file, dir_path=output_dir_path,
                                          input_dir_path=input_dir_path)
    if not ran:
        print("-W- " + error)


if __name__ == "__main__":
    main()
