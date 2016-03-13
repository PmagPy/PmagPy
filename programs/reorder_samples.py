#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
#
#
def main():
    """
    NAME
        reorder_samples.py

    DESCRIPTION
        takes specimen file and reorders sample file with selected orientation methods placed first

    SYNTAX
        reorder_samples.py [command line options]

    OPTIONS
        -h prints help message and quits
        -fsp: specimen input pmag_specimens format file, default is "pmag_specimens.txt"
        -fsm: sample input er_samples format file, default is "er_samples.txt"
        -F: output er_samples format file, default is "er_samples.txt"
    OUPUT
        writes re-ordered er_samples.txt file

    """
    infile='pmag_specimens.txt'
    sampfile="er_samples.txt"
    outfile="er_samples.txt"
# get command line stuff
    if "-h" in sys.argv:
	print main.__doc__
        sys.exit()
    if '-fsp' in sys.argv:
	ind=sys.argv.index("-fsp")
	infile=sys.argv[ind+1]
    if '-fsm' in sys.argv:
	ind=sys.argv.index("-fsm")
	sampfile=sys.argv[ind+1]
    if '-F' in sys.argv:
	ind=sys.argv.index("-F")
	outfile=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
        infile=dir_path+'/'+infile
        sampfile=dir_path+'/'+sampfile
        outfile=dir_path+'/'+outfile
# now do re-ordering 
    pmag.ReorderSamples(infile,sampfile,outfile)

if __name__ == "__main__":
    main()
