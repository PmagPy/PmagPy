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
    -dm 3: MagIC Data Model 3 is the only supported model
    -i allows interactive  entry of input and output filenames
    -WD specifies a directory to input and output files
    -F specify output file name
    -f specify input file names (quote names containing spaces)
"""
import argparse
import sys
import os
import pmagpy.ipmag as ipmag
import pmagpy.pmag as pmag


def combine(filenames, outfile, dir_path='.', data_model=2.5):
    """Combine a list of filenames, or a single filename."""
    if isinstance(filenames, str):
        filenames = [filenames]
    files = []
    for f in filenames:
        files.append(os.path.join(dir_path, f))
    outfile = (os.path.join(dir_path, outfile))
    ipmag.combine_magic(files, outfile, data_model=data_model)


def main():
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if float(pmag.get_named_arg("-dm", 3)) != 3:
        raise SystemExit(
            "-E- combine_magic supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before combining."
        )
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
        if not outfile:
            return False
    else:  # non-interactive
        parser = argparse.ArgumentParser(description="Combine MagIC files of the same type.")
        parser.add_argument("-WD", default=".")
        parser.add_argument("-F", required=True)
        parser.add_argument("-f", nargs="+", required=True)
        parser.add_argument("-dm", default="3")
        args = parser.parse_args()
        dir_path, outfile, filenames = args.WD, args.F, args.f
        data_model = 3
    combine(filenames, outfile, dir_path, data_model)


if __name__ == "__main__":
    main()
