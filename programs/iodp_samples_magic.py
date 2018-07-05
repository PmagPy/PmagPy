#!/usr/bin/env python
#import pmag,sys,string
from __future__ import print_function
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
        print(main.__doc__)
        sys.exit()

    dataframe = extractor.command_line_dataframe([['WD', False, '.'], ['ID', False, '.'], ['f', True, ''], ['Fsa', False, 'samples.txt'], ['DM', False, 3]])
    args = sys.argv
    checked_args = extractor.extract_and_check_args(args, dataframe)
    samp_file, output_samp_file, output_dir_path, input_dir_path, data_model_num = extractor.get_vars(['f', 'Fsa', 'WD', 'ID', 'DM'], checked_args)
    data_model_num = int(float(data_model_num))
    if '-Fsa' not in args and data_model_num == 2:
        output_samp_file = "er_samples.txt"
    ran, error = ipmag.iodp_samples_magic(samp_file, output_samp_file, output_dir_path, input_dir_path, data_model_num=data_model_num)
    if not ran:
        print("-W- " + error)


if __name__ == "__main__":
    main()
