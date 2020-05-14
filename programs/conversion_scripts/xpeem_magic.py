#!/usr/bin/env python
import sys,os
from math import log10, floor

def main():
    """
    NAME
        xpeem_magic_measurements.py

    DESCRIPTION
        Converts XPEEM measurement files into a MagIC format measurement file
        Run in the same directory as the XPEEM files and no other files should be present.
        File names should be in the form of SPECIMEN_NAME-XPEEM_TYPE
        For example: TeA01-r1offR 
        The program will label the measurement is from specimen TeA01 and
        the experiment name will be TeA01-r1offR

        The measurement files will be put in a directory named "measurements".

    SYNTAX
        xpeem_magic_measurements.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -x_spacing: set the x_spacing of the measurement in meters. Required
        -y_spacing: set the y_spacing of the measurement in meters. Required
        -meas_num: set the starting measurement name number. default:1
        -experiment_num: set the starting expiriment number. default:1
                         This is the number that is used for labeling the measurement file.
                         e.g., measurement1.txt, measurement2.txt, etc.

        -citations: list of citations (":" between entries). default: "This study". 
                    "This study" can be used for the study this MagIC contribution 
                    will be associated with. Will be added when the data is published.
                    Use DOIs for other studies.

        -method_codes: method_codes used for all measurements
                       (":" between multiple entries)
                       LP-XPEEM will be automatically added if not already in the list 
                       Default: LP-XPEEM
    """

    if '-h' in sys.argv: # check if help is needed
        print(main.__doc__)
        sys.exit() # graceful quit
    if '-d' in sys.argv:
        ind=sys.argv.index('-d')
        dir_name=sys.argv[ind+1]
    else:
        dir_name=""
    if '-x_spacing' in sys.argv:
        ind=sys.argv.index('-x_spacing')
        x_spacing=float(sys.argv[ind+1])
    else:
        print("the -x_spacing flag must be set")
        exit()
    if '-y_spacing' in sys.argv:
        ind=sys.argv.index('-y_spacing')
        y_spacing=float(sys.argv[ind+1])
    else:
        print("the -y_spacing flag must be set")
        exit()
    if '-meas_num' in sys.argv:
        ind=sys.argv.index('-meas_num')
        meas_num=int(sys.argv[ind+1])
    else:
        meas_num=1
    if '-experiment_num' in sys.argv:
        ind=sys.argv.index('-experiment_num')
        experiment_num=int(sys.argv[ind+1])
    else:
        experiment_num=1
    if '-citations' in sys.argv:
        ind=sys.argv.index('-citations')
        citations=sys.argv[ind+1]
    else:
        citations='This study'

    method_codes=''
    if '-method_codes' in sys.argv:
        ind=sys.argv.index('-method_codes')
        method_codes=sys.argv[ind+1]
        if 'LP-XPEEM' not in method_codes:
           method_codes=method_codes+':LP-XPEEM'
    else:
        method_codes='LP-XPEEM'
    
    print("start")
    file_list=os.listdir()
    if '.DS_Store' in file_list:
        file_list.remove('.DS_Store')
    os.system('mkdir measurements')
    for file in sorted(file_list):
        experiment_name=file[:-4]
        print("file=",file)
        specimen=file.split('-')
        specimen=specimen[0]
        mf=open('measurements/measurements'+str(experiment_num)+'.txt','w')
        mf.write('tab\tmeasurements\n')
        mf.write('* experiment\t'+experiment_name+'\n')
        mf.write('* specimen\t'+ specimen+'\n')
        mf.write('* standard\tu\n')
        mf.write('* quality\tg\n')
        mf.write('* method_codes\t'+ method_codes+'\n')
        mf.write('* citations\t'+ citations+'\n')
        mf.write('* derived_value\t'+ 'XPEEM,*,10.1088/1742-6596/430/1/012127\n')
        mf.write('measurement\tderived_value\tmeas_pos_x\tmeas_pos_y\n')
        xf=open(file,'r') 
        line = xf.readline() 
        if ',' in line:
            split_char=','
        elif '\t' in line:
            split_char='\t'
        elif '  ' in line:
            split_char='  '
        else:
            print('The separator between values is not a comma, tab, or two spaces. Exiting.')
            exit()
        y=0
        while line != "":
            line=line[:-1]  #remove newline
            values=line.split(split_char)
            x=0
            for value in values:
                mline=str(meas_num)+'\t'+value+'\t'+str(x*x_spacing)+'\t'+str(y*y_spacing)+'\n'
                mf.write(mline)
                x+=1
                meas_num+=1
            y+=1
            line = xf.readline() 
        experiment_num+=1
        xf.close()
        mf.close()
    print("end")

def do_help():
    """
    returns help string of script
    """
    return __doc__

if __name__ == "__main__":
    main()
