#!/usr/bin/env python
import sys
from pmagpy import pmag
from pmagpy import convert_2_magic as convert


def main():
    """
    NAME
        mini_magic.py

    DESCRIPTION
        converts the Yale minispin format to magic_measurements format files

    SYNTAX
        mini_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
        -A: don't average replicate measurements
        -vol: volume assumed for measurement in cm^3 (default 12 cc)
        -DM NUM: MagIC data model (2 or 3, default 3)

    INPUT
        Must put separate experiments (all AF, thermal,  etc.) in
           seperate files

        Format of Yale MINI files:
        LL-SI-SP_STEP, Declination, Inclination, Intensity (mA/m), X,Y,Z


    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
# initialize some stuff
    methcode = "LP-NO"
    demag = "N"

#
# get command line arguments
#
    data_model_num = int(float(pmag.get_named_arg("-DM", 3)))
    user = pmag.get_named_arg("-usr", "")
    dir_path = pmag.get_named_arg("-WD", ".")
    inst = pmag.get_named_arg("-inst", "")
    magfile = pmag.get_named_arg("-f", reqd=True)
    magfile = pmag.resolve_file_name(magfile, dir_path)
    if "-A" in args:
        noave = 1
    else:
        noave = 0

    if data_model_num == 2:
        meas_file = pmag.get_named_arg("-F", "magic_measurements.txt")
    else:
        meas_file = pmag.get_named_arg("-F", "measurements.txt")
    meas_file = pmag.resolve_file_name(meas_file, dir_path)
    volume = pmag.get_named_arg("-vol", 12) # assume a volume of 12 cc if not provided
    methcode = pmag.get_named_arg("-LP", "LP-NO")
    #ind = args.index("-LP")
    #codelist = args[ind+1]
    #codes = codelist.split(':')
    #if "AF" in codes:
    #    demag = 'AF'
    #    methcode = "LT-AF-Z"
    #if "T" in codes:
    #    demag = "T"

    convert.mini(magfile, dir_path, meas_file, data_model_num,
            volume, noave, inst, user, methcode)



if __name__ == "__main__":
    main()
