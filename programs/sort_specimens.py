#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        sort_specimens.py

    DESCRIPTION
        Reads in a pmag_specimen formatted file and separates it into different components (A,B...etc.)

    SYNTAX 
        sort_specimens.py [-h] [command line options]

    INPUT
        takes pmag_specimens.txt formatted input file

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify input file, default is 'pmag_specimens.txt'

    OUTPUT
        makes pmag_specimen formatted files with input filename plus _X_Y 
        where X is the component name and Y is s,g,t for coordinate system
    """
    dir_path='.'
    inspec="pmag_specimens.txt"
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        inspec=sys.argv[ind+1]
    basename=inspec.split('.')[:-1]
    inspec=dir_path+"/"+inspec
    ofile_base=dir_path+"/"+basename[0]
#
# read in data
#
    prior_spec_data,file_type=pmag.magic_read(inspec)
    if file_type != 'pmag_specimens':
        print(file_type, " this is not a valid pmag_specimens file")
        sys.exit()
# get list of specimens in file, components, coordinate systems available
    specs,comps,coords=[],[],[]
    for spec in prior_spec_data:
        if spec['er_specimen_name'] not in specs:specs.append(spec['er_specimen_name'])
        if 'specimen_comp_name' not in list(spec.keys()):spec['specimen_comp_name']='A'
        if 'specimen_tilt_correction'  not in list(spec.keys()):spec['tilt_correction']='-1' # assume specimen coordinates
        if spec['specimen_comp_name'] not in comps:comps.append(spec['specimen_comp_name'])
        if spec['specimen_tilt_correction'] not in coords:coords.append(spec['specimen_tilt_correction'])
# work on separating out components, coordinate systems by specimen
    for coord in coords:
        print(coord)
        for comp in comps:
            print(comp)
            speclist=[]
            for spec in prior_spec_data:
                if spec['specimen_tilt_correction']==coord and spec['specimen_comp_name']==comp:speclist.append(spec)
            ofile=ofile_base+'_'+coord+'_'+comp+'.txt'
            pmag.magic_write(ofile,speclist,'pmag_specimens')
            print('coordinate system: ',coord,' component name: ',comp,' saved in ',ofile)

if __name__ == "__main__":
    main()
