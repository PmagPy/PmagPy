#!/usr/bin/env python
"""
NAME
    combine_magic.py

DESCRIPTION
    Combines magic format files of the same type together.

SYNTAX
    combine_magic.py [-h] [-i] -F filename -f file1 file2 ....

OPTIONS
    -h prints help message
    -dm specify data model (default: 3.0)
    -i allows interactive  entry of input and output filenames
    -WD specifies a directory to input and output files
    -F specify output file name [must come BEFORE input file names]
    -f specify input file names [ must come last]
"""
import sys
import os
import pmagpy.ipmag as ipmag
import pmagpy.command_line_extractor as extractor


def combine(filenames, outfile, dir_path='.', data_model=2.5):
    files = []
    for f in filenames.split():
        files.append(os.path.join(dir_path, f))
    outfile = (os.path.join(dir_path, outfile))
    ipmag.combine_magic(files, outfile, data_model=data_model)


def main():
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-i" in sys.argv:  # interactive
        dir_path = "."
        dataset, datasets, filenames = [], [], []
        data_model = 3
        while True:
            infile = input(
                '\n\n Enter magic files for combining, <return>  when done: ')
            if infile == '':
                break
            if os.path.isfile(infile):
                filenames.append(os.path.realpath(infile))
            else:
                print("-W- You have not provided a valid filename.\nIf the file is not in your current working directory, you will need to provide the full path to the file")
        outfile = input('\n\n Enter name for new combined file: ')
        filenames = str(", ".join(filenames))
        if not outfile:
            return False
    else:  # non-interactive
        dataframe = extractor.command_line_dataframe(
            [["F", True, ''], ["dm", False, 3]])
        args = extractor.extract_and_check_args(sys.argv, dataframe)
        data_model, dir_path, outfile, filenames = extractor.get_vars(
            ["dm", "WD", "F", "f"], args)
    combine(filenames, outfile, dir_path, data_model)


if __name__ == "__main__":
    main()
