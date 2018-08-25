#!/usr/bin/env python
#
import sys
import pmagpy.command_line_extractor as extractor
from pmagpy import convert_2_magic as convert


def main():
    """
    NAME
        k15_magic.py

    DESCRIPTION
        converts .k15 format data to magic_measurements  format.
        assums Jelinek Kappabridge measurement scheme

    SYNTAX
        k15_magic.py [-h] [command line options]

    OPTIONS
        -h prints help message and quits
        -DM DATA_MODEL: specify data model 2 or 3 (default 3)
        -f KFILE: specify .k15 format input file
        -F MFILE: specify measurement output file
        -Fsa SFILE, specify sample file for output
        -Fa AFILE, specify specimen file for output [rmag_anisotropy for data model 2 only]
    #-ins INST: specify instrument that measurements were made on # not implemented
        -spc NUM: specify number of digits for specimen ID, default is 0
        -ncn NCOM: specify naming convention (default is #1)
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
            NB: all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.


    DEFAULTS
        MFILE: measurements.txt
        SFILE: samples.txt
        AFILE: specimens.txt

    INPUT
      name [az,pl,strike,dip], followed by
      3 rows of 5 measurements for each specimen

    """
    args = sys.argv
    if '-h' in args:
        print(do_help())
        sys.exit()

    # def k15_magic(k15file, specnum=0, sample_naming_con='1', er_location_name="unknown", measfile='magic_measurements.txt', sampfile="er_samples.txt", aniso_outfile='rmag_anisotropy.txt', result_file="rmag_results.txt", input_dir_path='.', output_dir_path='.'):

    dataframe = extractor.command_line_dataframe([['f', True, ''], ['F', False, 'measurements.txt'], ['Fsa', False, 'samples.txt'], ['Fa', False, 'specimens.txt'], [
                                                 'Fr', False, 'rmag_results.txt'], ['spc', False, 0], ['ncn', False, '1'], ['loc', False, 'unknown'], ['WD', False, '.'], ['ID', False, '.'], ['DM', False, 3]])
    checked_args = extractor.extract_and_check_args(args, dataframe)
    k15file, measfile, sampfile, aniso_outfile, result_file, specnum, sample_naming_con, location_name, output_dir_path, input_dir_path, data_model_num = extractor.get_vars(
        ['f', 'F', 'Fsa', 'Fa', 'Fr', 'spc', 'ncn', 'loc', 'WD', 'ID', 'DM'], checked_args)
    program_ran, error_message = convert.k15(k15file, specnum=specnum, sample_naming_con=sample_naming_con, location=location_name, meas_file=measfile,
                                                 samp_file=sampfile, aniso_outfile=aniso_outfile, result_file=result_file, input_dir_path=input_dir_path, dir_path=output_dir_path, data_model_num=data_model_num)


def do_help():
    return main.__doc__


if __name__ == "__main__":
    main()
