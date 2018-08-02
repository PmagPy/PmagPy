#!/usr/bin/env python
from __future__ import print_function
import sys
import string
import pmagpy.pmag as pmag


def main():
    """
    NAME
        mk_redo.py

    DESCRIPTION
        Makes thellier_redo and zeq_redo files from existing pmag_specimens format file

    SYNTAX
        mk_redo.py [-h] [command line options]

    INPUT
        takes specimens.txt formatted input file

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify input file, default is 'specimens.txt'
        -F REDO: specify output file suffix, default is redo so that
            output filenames are 'thellier_redo' for thellier data and 'zeq_redo' for direction only data

    OUTPUT
        makes a thellier_redo or a zeq_redo format file
    """
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    zfile, tfile = 'zeq_redo', 'thellier_redo'
    zredo, tredo = "", ""
    dir_path = pmag.get_named_arg('-WD', '.')
    inspec = pmag.get_named_arg('-f', 'specimens.txt')
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        redo = sys.argv[ind + 1]
        tfile = redo
        zfile = redo
    inspec = pmag.resolve_file_name(inspec, dir_path)
    zfile = pmag.resolve_file_name(zfile, dir_path)
    tfile = pmag.resolve_file_name(tfile, dir_path)
#
# read in data
#
    specs = []
    prior_spec_data, file_type = pmag.magic_read(inspec)
    if file_type != 'specimens':
        print(file_type, " this is not a valid pmag_specimens file")
        sys.exit()
    outstrings = []
    for spec in prior_spec_data:
        tmp = spec["method_codes"].split(":")
        meths = []
        for meth in tmp:
            methods = meth.strip().split('-')
            for m in methods:
                if m not in meths:
                    meths.append(m)
        if 'DIR' in meths:  # DE-BFL, DE-BFP or DE-FM
            specs.append(spec['specimen'])
            if 'dir_comp' in list(spec.keys()) and spec['dir_comp'] != "" and spec['dir_comp'] != " ":
                comp_name = spec['dir_comp']
            else:
                comp_name = string.ascii_uppercase[specs.count(
                    spec['specimen']) - 1]
            calculation_type = "DE-BFL"  # assume default calculation type is best-fit line
            if "BFP" in meths:
                calculation_type = 'DE-BFP'
            elif "FM" in meths:
                calculation_type = 'DE-FM'
            if zredo == "":
                zredo = open(zfile, "w")
            outstring = '%s %s %s %s %s \n' % (
                spec["specimen"], calculation_type, spec["meas_step_min"], spec["meas_step_max"], comp_name)
            if outstring not in outstrings:
                zredo.write(outstring)
            outstrings.append(outstring)  # only writes unique interpretions
        elif "PI" in meths and "TRM" in meths:   # thellier record
            if tredo == "":
                tredo = open(tfile, "w")
            outstring = '%s %i %i \n' % (spec["specimen"], float(
                spec["meas_step_min"]), float(spec["meas_step_max"]))
            if outstring not in outstrings:
                tredo.write(outstring)
            outstrings.append(outstring)  # only writes unique interpretions
    print('Redo files saved to: ', zfile, tfile)


if __name__ == "__main__":
    main()
