#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
#
#
def main():
    """
    NAME
        parse_measurements.py

    DESCRIPTION
        takes measurments file and creates specimen and instrument files

    SYNTAX
        parse_measurements.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE magic_measurements input file, default is "magic_measurements.txt"
        -fsi FILE er_sites input file, default is none
        -Fsp  FILE specimen output er_specimens format file, default is "er_specimens.txt"
        -Fin FILE instrument output  magic_instruments format file, default is "magic_instruments.txt"
    OUPUT
        writes er_specimens and magic_instruments formatted files

    """
    infile='magic_measurements.txt'
    sitefile=""
    specout="er_specimens.txt"
    instout="magic_instruments.txt"
# get command line stuff
    if "-h" in sys.argv:
	print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
	ind=sys.argv.index("-f")
	infile=sys.argv[ind+1]
    if '-fsi' in sys.argv:
	ind=sys.argv.index("-fsi")
	sitefile=sys.argv[ind+1]
    if '-Fsp' in sys.argv:
	ind=sys.argv.index("-Fsp")
	specout=sys.argv[ind+1]
    if '-Fin' in sys.argv:
	ind=sys.argv.index("-Fin")
	instout=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        dir_path=sys.argv[ind+1]
        infile=dir_path+'/'+infile
        if sitefile!="":sitefile=dir_path+'/'+sitefile
        specout=dir_path+'/'+specout
        instout=dir_path+'/'+instout
# now do re-ordering 
    pmag.ParseMeasFile(infile,sitefile,instout,specout)

if __name__ == "__main__":
    main()
