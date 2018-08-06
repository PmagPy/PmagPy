#!/usr/bin/env python
"""
NAME
    agm_magic.py

DESCRIPTION
    converts Micromag agm files to magic format

SYNTAX
    agm_magic.py [-h] [command line options]

OPTIONS
    -bak:  this is a IRM backfield curve
    -f FILE, specify input file, required
    -xy the file format is in B, M with both in cgs units
    -spn SPEC, specimen name, default is base of input file name, e.g. SPEC.agm
    -spc NUM, specify number of characters to designate a  specimen, default = 0
    -ncn NCON,: specify naming convention: default is #1 below
    -loc LOCNAME: specify location/study name.
    -ins INST : specify which instrument was used (e.g, SIO-Maud), default is ""
    -u units:  [cgs,SI], default is cgs
    -F MFILE, specify measurements formatted output file, default is SPECNAME.magic
    -Fsp SPECFILE, specify specimens.txt file relating specimen to the sample; default is SPEC_specimens.txt
    -Fsa SAMPFILE, specify samples.txt file relating samples to  site; default is SPEC_samples.txt
    -Fsi SITEFILE, specify sites.txt file relating site to location; default is SPEC_sites.txt
    -Flo LOCFILE, specify locations.txt file; default is SPEC_locations.txt
    -old : infile is in old format

OUTPUT
    MagIC format files: measurements, specimens, sample, site
"""
import sys
from pmagpy import convert_2_magic as convert


def do_help():
    return __doc__


def main():
    kwargs = {}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-bak' in sys.argv:
        kwargs['bak'] = 1
    if '-new' in sys.argv:
        kwargs['fmt'] = 'new'
    if '-xy' in sys.argv:
        kwargs['fmt'] = 'xy'
    if '-WD' in sys.argv:
        ind = sys.argv.index("-WD")
        kwargs['dir_path'] = sys.argv[ind + 1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind + 1]
    if '-Fsp' in sys.argv:
        ind = sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind + 1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind + 1]
    if '-Fsi' in sys.argv:
        ind = sys.argv.index("-Fsi")
        kwargs['site_file'] = sys.argv[ind + 1]
    if '-Flo' in sys.argv:
        ind = sys.argv.index("-Flo")
        kwargs['loc_file'] = sys.argv[ind + 1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['agm_file'] = sys.argv[ind + 1]
    if "-spc" in sys.argv:
        ind = sys.argv.index("-spc")
        kwargs['specnum'] = int(sys.argv[ind + 1])
    if "-spn" in sys.argv:
        ind = sys.argv.index("-spn")
        kwargs['specimen'] = sys.argv[ind + 1]
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind + 1]
    if "-fsa" in sys.argv:
        ind = sys.argv.index("-fsa")
        kwargs['samp_infile'] = sys.argv[ind + 1]
    if '-syn' in sys.argv:
        syn = 1
        ind = sys.argv.index("-syn")
        kwargs['institution'] = sys.argv[ind + 1]
        kwargs['syntype'] = sys.argv[ind + 2]
        if '-fsy' in sys.argv:
            ind = sys.argv.index("-fsy")
            synfile = sys.argv[ind + 1]
    if "-ins" in sys.argv:
        ind = sys.argv.index("-ins")
        kwargs['ins'] = sys.argv[ind + 1]
    if "-ncn" in sys.argv:
        ind = sys.argv.index("-ncn")
        kwargs['samp_con'] = sys.argv[ind + 1]
    if "-u" in sys.argv:
        ind = sys.argv.index("-u")
        units = sys.argv[ind + 1]
        kwargs['units'] = units
    if "-old" in sys.argv:
        kwargs['fmt'] = 'old'
    else:
        kwargs['fmt'] = 'new'

    convert.agm(**kwargs)


if __name__ == "__main__":
    main()
