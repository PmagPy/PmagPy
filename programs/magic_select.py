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
        -dm 3: MagIC Data Model 3 is the only supported model
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
             use KEY: model_lat (uses lat if age < 5 Ma; otherwise uses
             paleolat or model_lat, or estimates from dir_inc). Returns the
             estimate in the paleolat key.

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
    if float(pmag.get_named_arg("-dm", 3)) != 3:
        raise SystemExit(
            "-E- magic_select supports MagIC Data Model 3 only. "
            "Convert Data Model 2 files to Data Model 3 before selecting."
        )
    if '-f' in sys.argv:
        ind = sys.argv.index('-f')
        magic_file = dir_path+'/'+sys.argv[ind+1]
    else:
        print(main.__doc__)
        print('-W- "-f" is a required option')
        sys.exit()
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
    is_model_lat = grab_key == 'model_lat'
    if grab_key == 'age':
        Data = pmag.convert_ages(Data, data_model=3, precision=15)
    if is_model_lat:
        for rec in Data:
            if rec.get('age') or (rec.get('age_low') and rec.get('age_high')):
                pmag.convert_ages([rec], data_model=3, precision=15)
        Data = pmag.convert_lat(Data, data_model=3)
        for rec in Data:
            rec.pop('model_lat', None)
        grab_key = 'paleolat'
    #print(Data[0])
    Selection = pmag.get_dictitem(
        Data, grab_key, v, flag, float_to_int=(grab_key != 'age' and not is_model_lat)
    )
    if len(Selection) > 0:
        pmag.magic_write(outfile, Selection, file_type)
    else:
        print('no data matched your criteria')


if __name__ == "__main__":
    main()
