#!/usr/bin/env python
from __future__ import print_function
from builtins import str
import sys
import pmagpy.pmag as pmag
import pmagpy.command_line_extractor as extractor
import pmagpy.ipmag as ipmag
#
#
def main():
    """
    NAME
        azdip_magic.py

    DESCRIPTION
        takes space delimited AzDip file and converts to MagIC formatted tables

    SYNTAX
        azdip_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file
        -Fsa FILE: specify output file, default is: er_samples.txt/samples.txt
        -ncn NCON:  specify naming convention: default is #1 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
        -loc: location name, default="unknown"
        -app appends to existing samples file, default is to overwrite

    INPUT FORMAT
        Input files must be space delimited:
            Samp  Az Dip Strike Dip
        Orientation convention:
             Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
                e.g. field_dip is degrees from horizontal of drill direction

         Magnetic declination convention:
             Az is already corrected in file

       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

    OUTPUT
            output saved in samples file  will overwrite any existing files
    """

    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()

    dataframe = extractor.command_line_dataframe([['f', False, 'orient.txt'], ['Fsa', False, 'samples.txt'], ['ncn', False, "1"], ['mcd', False, 'FS-FD'], ['loc', False, 'unknown'], ['app', False, False], ['WD', False, '.'], ['ID', False, '.'], ['DM', False, 3]])
    checked_args = extractor.extract_and_check_args(args, dataframe)
    #print('checked_args:', checked_args)
    orient_file, samp_file, samp_con, method_codes, location_name, append, output_dir, input_dir, data_model = extractor.get_vars(['f', 'Fsa', 'ncn', 'mcd', 'loc', 'app', 'WD', 'ID', 'DM'], checked_args)

    if len(str(samp_con)) > 1:
        samp_con, Z = samp_con.split('-')
        Z = float(Z)
    else:
        Z = 1

    ipmag.azdip_magic(orient_file, samp_file, samp_con, Z, method_codes, location_name, append, output_dir, input_dir, data_model)

if __name__ == "__main__":
    main()
