#!/usr/bin/env python
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

    """
    dir_path="."
    flag=''
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        magic_file=dir_path+'/'+sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        outfile=dir_path+'/'+sys.argv[ind+1]
    else:
        print main.__doc__
        sys.exit()
    if '-key' in sys.argv:
        ind=sys.argv.index('-key')
        grab_key=sys.argv[ind+1]
        v=sys.argv[ind+2]
        flag=sys.argv[ind+3]
    else:
        print main.__doc__
        print '-key is required'
        sys.exit()
    #
    # get data read in
    Data,file_type=pmag.magic_read(magic_file) 
    if grab_key =='age': 
        grab_key='average_age'
        Data=pmag.convert_ages(Data)
    if grab_key =='model_lat': 
        Data=pmag.convert_lat(Data)
        Data=pmag.convert_ages(Data)
    Selection=pmag.get_dictitem(Data,grab_key,v,flag)
    if len(Selection)>0:
        pmag.magic_write(outfile,Selection,file_type)
    else:
        print 'no data matched your criteria'

if __name__ == "__main__":
    main()
