#!/usr/bin/env python
import sys
from pmagpy import pmag
from pmagpy import convert_2_magic as convert


def main():
    """
    NAME
        huji_sample_magic.py

    DESCRIPTION
        takes tab delimited Hebrew University sample file and converts to MagIC formatted tables

    SYNTAX
        huji_sample_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file
        -Fsa FILE: specify sample output file, default is: samples.txt
        -Fsi FILE: specify site output file, default is: sites.txt
        -Iso:  import sample orientation info - default is to set sample_az/dip to 0,0
        -ncn NCON:  specify naming convention: default is #1 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM:SO-SUN]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
        -loc: location name, default="unknown"
        -DM: data model number (MagIC 2 or 3, default 3)

    INPUT FORMAT
        Input files must be tab delimited:
            Samp  Az Dip Dip_dir Dip
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
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
            NB: all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.

    OUTPUT
            output saved in samples  will overwrite any existing files
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    #
    # initialize variables
    Z = 1
    # get arguments from the command line
    orient_file = pmag.get_named_arg("-f", reqd=True)
    data_model_num = int(float(pmag.get_named_arg("-DM", 3)))
    if data_model_num == 2:
        samp_file = pmag.get_named_arg("-Fsa", "er_samples.txt")
        site_file = pmag.get_named_arg("-Fsi", "er_sites.txt")
    else:
        samp_file = pmag.get_named_arg("-Fsa", "samples.txt")
        site_file = pmag.get_named_arg("-Fsi", "sites.txt")
    samp_con = pmag.get_named_arg("-ncn", "1")
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 3-Z where Z is an integer")
            sys.exit()
        else:
            Z = samp_con.split("-")[1]
            #samp_con = "4"
        print(samp_con)#, Z)
    meths = pmag.get_named_arg("-mcd", 'FS-FD:SO-POM:SO-SUN')
    location_name = pmag.get_named_arg("-loc", "unknown")
    if "-Iso" in args:
        ignore = 0
    else:
        ignore = 1

    convert.huji_sample(orient_file, meths, location_name, samp_con, ignore)



if __name__ == "__main__":
    main()
