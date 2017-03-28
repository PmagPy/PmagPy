#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME 
        change_case_magic.py

    DESCRIPTION
        picks out key and converts to upper or lower case

    SYNTAX
        change_case_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file 
        -F FILE: specify output magic format file , default is to overwrite input file
        -keys KEY1:KEY2 specify colon delimited list of keys to convert
        -[U,l] : specify [U]PPER or [l]ower case, default is lower 

    """
    dir_path="./"
    change='l'
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
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        out_file=dir_path+'/'+sys.argv[ind+1]
    else: out_file=magic_file
    if '-keys' in sys.argv:
        ind=sys.argv.index('-keys')
        grab_keys=sys.argv[ind+1].split(":")
    else:
        print(main.__doc__)
        sys.exit()
    if '-U' in sys.argv: change='U'
    #
    #
    # get data read in
    Data,file_type=pmag.magic_read(magic_file) 
    if len(Data)>0:
      for grab_key in grab_keys:
        for rec in Data: 
            if change=='l':
                rec[grab_key]=rec[grab_key].lower()
            else:
                rec[grab_key]=rec[grab_key].upper()
    else:
        print('bad file name')
    pmag.magic_write(out_file,Data,file_type)

if __name__ == "__main__":
    main()
