#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag


def main():
    """
    NAME
        magic_select.py

    DESCRIPTION
        picks out records and dictitem options saves to magic_special file

    SYNTAX
        magic_select.py [command line optins]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input magic format file
        -F FILE: specify output magic format file
        -dm : data model (default is 3.0, otherwise use 2.5)
        -key KEY string [T,F,has, not, eval,min,max]
           returns records where the value of the key either:
               matches exactly the string (T)
               does not match the string (F)
               contains the string (has)
               does not contain the string (not)
               the value equals the numerical value of the string (eval)
               the value is greater than the numerical value of the string (min)
               the value is less than the numerical value of the string (max)
      NOTES
         for age range:
             use KEY: age (converts to Ma, takes mid point of low, high if no value for age.
         for paleolat:
             use KEY: model_lat (uses lat, if age<5 Ma, else, model_lat, or attempts calculation from average_inc if no model_lat.) returns estimate in model_lat key

      EXAMPLE:
         # here I want to output all records where the site column exactly matches "MC01"
         magic_select.py -f samples.txt -key site MC01 T -F select_samples.txt

    """
    dir_path = "."
    flag = ''
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        magic_file = dir_path+'/'+sys.argv[ind+1]
    else:
        print(main.__doc__)
        print('-W- "-f" is a required option')
        sys.exit()
    if '-dm' in sys.argv:
        ind = sys.argv.index('-dm')
        data_model_num=sys.argv[ind+1]
        if data_model_num!='3':data_model_num=2.5
    else : data_model_num=3
    if '-F' in sys.argv:
        ind = sys.argv.index('-F')
        outfile = dir_path+'/'+sys.argv[ind+1]
    else:
        print(main.__doc__)
        print('-W- "-F" is a required option')
        sys.exit()
    if '-key' in sys.argv:
        ind = sys.argv.index('-key')
        grab_key = sys.argv[ind+1]
        v = sys.argv[ind+2]
        flag = sys.argv[ind+3]
    else:
        print(main.__doc__)
        print('-key is required')
        sys.exit()
    #
    # get data read in
    Data, file_type = pmag.magic_read(magic_file)
    if grab_key == 'age':
        grab_key = 'average_age'
        Data = pmag.convert_ages(Data,data_model=data_model_num)
    if grab_key == 'model_lat':
        Data = pmag.convert_lat(Data)
        Data = pmag.convert_ages(Data,data_model=data_model_num)
    #print(Data[0])
    Selection = pmag.get_dictitem(Data, grab_key, v, flag, float_to_int=True)
    if len(Selection) > 0:
        pmag.magic_write(outfile, Selection, file_type)
    else:
        print('no data matched your criteria')


if __name__ == "__main__":
    main()
