#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME 
        grab_magic_key.py

    DESCRIPTION
        picks out key and saves to file

    SYNTAX
        grab_magic_key.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file 
        -key KEY: specify key to print to standard output 

    """
    dir_path="./"
    if '-WD' in sys.argv: 
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        magic_file=dir_path+'/'+sys.argv[ind+1]
    else:
        print(main.__doc__)
        sys.exit()
    if '-key' in sys.argv:
        ind=sys.argv.index('-key')
        grab_key=sys.argv[ind+1]
    else:
        print(main.__doc__)
        sys.exit()
    #
    #
    # get data read in
    Data,file_type=pmag.magic_read(magic_file) 
    if len(Data)>0:
        for rec in Data: print(rec[grab_key])
    else:
        print('bad file name')

if __name__ == "__main__":
    main()
