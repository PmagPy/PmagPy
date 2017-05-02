#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import string
import pmagpy.pmag as pmag

def main():
    """
    NAME
        lsq_redo.py

    DESCRIPTION
        converts a tab delimited LSQ format to PmagPy redo file and edits the magic_measurements table to mark "bad" measurements.

    SYNTAX
        lsq_redo.py [-h] [command line options]

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify LSQ input file
        -fm MFILE: specify measurements file for editting, default is
            magic_measurements.txt
        -F FILE: specify output file, default is 'zeq_redo'
    """
    letters=string.ascii_uppercase
    for l in string.ascii_lowercase: letters=letters+l
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        inspec=dir_path+'/'+sys.argv[ind+1]
    else:
        zfile=dir_path+'/zeq_redo'
    if '-fm' in sys.argv:
        ind=sys.argv.index('-f')
        meas_file=dir_path+'/'+sys.argv[ind+1]
    else:
        meas_file=dir_path+'/magic_measurements.txt'
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        zfile=dir_path+'/'+sys.argv[ind+1]
    else:
        zfile=dir_path+'/zeq_redo'
    try:
        open(meas_file,"r")
        meas_data,file_type=pmag.magic_read(meas_file)
    except IOError:
        print(main.__doc__)
        print("""You must have a valid measurements file prior to converting
                this LSQ file""")
        sys.exit()
    zredo=open(zfile,"w")
    MeasRecs=[]
#
# read in LSQ file
#
    specs,MeasOuts=[],[]
    prior_spec_data=open(inspec,'r').readlines()
    for line in prior_spec_data:
        if len(line)<2:
            sys.exit()
#        spec=line[0:14].strip().replace(" ","") # get out the specimen name = collapsing spaces
#        rec=line[14:].split() # split up the rest of the line
        rec=line.split('\t')
        spec=rec[0].lower()
        specs.append(spec)
        comp_name=rec[2] # assign component name
        calculation_type="DE-FM"
        if rec[1][0]=="L":
            calculation_type="DE-BFL" # best-fit line
        else:
            calculation_type="DE-BFP" # best-fit line
        lists=rec[7].split('-') # get list of data used
        incl=[]
        for l in lists[0]:
            incl.append(letters.index(l))
        for l in letters[letters.index(lists[0][-1])+1:letters.index(lists[1][0])]:
            incl.append(letters.index(l)) # add in the  in between parts
        for l in lists[1]:
            incl.append(letters.index(l))
        if len(lists)>2:
            for l in letters[letters.index(lists[1][-1])+1:letters.index(lists[2][0])]:
               incl.append(letters.index(l)) # add in the  in between parts
            for l in lists[2]:
                incl.append(letters.index(l))
# now find all the data for this specimen in measurements
        datablock,min,max=[],"",""
        demag='N'
        for s in meas_data:
            if s['er_specimen_name'].lower()==spec.lower():
                meths=s['magic_method_codes'].replace(" ","").split(":")
                if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
                    datablock.append(s)
        if len(datablock)>0:
            for t in datablock:print(t['magic_method_codes'])
            incl_int=len(incl)
            while incl[-1]>len(datablock)-1:
                del incl[-1] # don't include measurements beyond what is in file
            if len(incl)!=incl_int:
                'converting calculation type to best-fit line'
            meths0= datablock[incl[0]]['magic_method_codes'].replace(" ","").split(':')
            meths1= datablock[incl[-1]]['magic_method_codes'].replace(" ","").split(':')
            H0=datablock[incl[0]]['treatment_ac_field']
            T0=datablock[incl[0]]['treatment_temp']
            H1=datablock[incl[-1]]['treatment_ac_field']
            T1=datablock[incl[-1]]['treatment_temp']
            if 'LT-T-Z' in meths1:
               max=T1
               demag="T"
            elif 'LT-AF-Z' in meths1:
               demag="AF"
               max=H1
            if 'LT-NO' in meths0:
                if demag=='T':
                   min=273
                else:
                   min=0
            elif 'LT-T-Z' in meths0:
                min=T0
            else:
                min=H0
            for ind in range(incl[0]):
                MeasRecs.append(datablock[ind])
            for ind in range(incl[0],incl[-1]):
                if ind not in incl: # datapoint not used in calculation
                    datablock[ind]['measurement_flag']='b'
                MeasRecs.append(datablock[ind])
            for ind in range(incl[-1],len(datablock)):
                MeasRecs.append(datablock[ind])
            outstring='%s %s %s %s %s \n'%(spec,calculation_type,min,max,comp_name)
            zredo.write(outstring)
    for s in meas_data: # collect the rest of the measurement data not already included
        if s['er_specimen_name'] not in specs:
            MeasRecs.append(s)
    pmag.magic_write(meas_file,MeasRecs,'magic_measurements')  # write out annotated measurements

if __name__ == "__main__":
    main()
