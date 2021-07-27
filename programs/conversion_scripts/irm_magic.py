#!/usr/bin/env python
"""
NAME
    irm_magic.py

DESCRIPTION
    Creates MagIC file from an IRM excel file. If you have multiple Excel files you will have to run the
    program for each Excel file and combine each type of file (locations.txt, sites.txt, etc.) manually 
    using "combine_magic.py"

    The program creates the standard file names for MagIC uploading (locations.txt, sites.txt, sample.txt,
    specimens.txt, measurements.txt) and creates measurements files of each Excel measurement worksheet name 
    attached so that individual table conversions can be inspected, if desired. You will have to fill in the 
    meta-data missing in these files before they will pass data verification. Many empty required data columns 
    have been included in the files for convenience.

SYNTAX
    irm_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits
    -ID DIRECTORY: directory for input files, default = current directory
    -WD DIRECTORY: directory for output files, default = current directory
    -f FILE: the IRM Excel data file name, required 
       (the file name flag may be ommited and just the file name used, if no other flags are present)
    -cite CITATION: specify the citation, default = This study (use "This study" unless you already 
                    have the DOI for the paper the dataset is associated with.
    -M flag: the MPMSdc file type (default:0) 
             use 0 for IRM file type as of July 7th, 2021. Data has header with the specimen name on 4 columns
             use 1 for earlier type where the first two header columns are "specimen" and the specimen name
             example IRM data file Sprain is of this type
EXAMPLE
    Command line for the example dataset:
    irm_magic.py example.xlsx -   (example dataset yet to be choosen)


"""

import sys
from pmagpy import convert_2_magic as convert

def do_help():
    """
    returns help string of script
    """
    return __doc__


def main():
    kwargs = {}
    if '-h' in sys.argv:
        help(__name__)
        sys.exit()
    if '-ID' in sys.argv:
        ind=sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['input_dir_path'] = './'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        kwargs['output_dir_path'] = sys.argv[ind+1]
    else:
        kwargs['output_dir_path'] = './'
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        kwargs['mag_file'] = sys.argv[ind+1]
    elif len(sys.argv) == 2:
        kwargs['mag_file'] = sys.argv[1]
    else:
        print("You must specify the IRM excel data file name with the -f flag.") 
        exit()
    if '-cit' in sys.argv:
        ind=sys.argv.index('-cit')
        kwargs['citation'] = sys.argv[ind+1]
    else:
        kwargs['citation'] = 'This study'
    if '-M' in sys.argv:
        ind=sys.argv.index('-M')
        kwargs['MPMSdc_type'] = sys.argv[ind+1]
    else:
        kwargs['MPMSdc_type'] = '0'
        
    convert.irm(**kwargs)

if __name__ == "__main__":
    main()
