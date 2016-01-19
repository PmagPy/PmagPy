#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        extract_methods.py
 
    DESCRIPTION
        reads in a magic table and creates a file with method codes

    SYNTAX
        extract_methods.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -f FILE: specify magic format input file, default is magic_measurements.txt
        -F FILE: specify method code output file, default is magic_methods.txt
    """
    citation='This study'
    args=sys.argv
    outfile='magic_methods.txt'
    infile='magic_measurements.txt'
#
# get command line arguments
#
    dir_path='.'
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if '-F' in args:
        ind=args.index("-F")
        outfile=args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        infile=args[ind+1]
    infile=dir_path+'/'+infile
    outfile=dir_path+'/'+outfile
    data,file_type=pmag.magic_read(infile)
    MethRecs=[]
    methods=[]
    for rec in data:
        meths=rec['magic_method_codes'].split(":")
        for meth in meths:
            if meth not in methods:
                MethRec={}
                methods.append(meth)
                MethRec['magic_method_code']=meth
                MethRecs.append(MethRec)
    pmag.magic_write(outfile,MethRecs,'magic_methods')

if __name__ == "__main__":
    main()
