#!/usr/bin/env python
import sys
import string
import pmagpy.pmag as pmag

def main():
    """
    NAME
        mk_redo.py

    DESCRIPTION
        Makes thellier_redo and zeq_redo files from existing pmag_specimens format file

    SYNTAX 
        mk_redo.py [-h] [command line options]

    INPUT
        takes pmag_specimens.txt formatted input file

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify input file, default is 'pmag_specimens.txt'
        -F REDO: specify output file suffix, default is redo so that 
            output filenames are 'thellier_redo' for thellier data and 'zeq_redo' for direction only data                 

    OUTPUT
        makes a thellier_redo or a zeq_redo format file
    """
    dir_path='.'
    zfile,tfile='zeq_redo','thellier_redo'
    inspec="pmag_specimens.txt"
    zredo,tredo="","" 
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        inspec=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        redo=sys.argv[ind+1]
        tfile=redo
        zfile=redo
    inspec=dir_path+"/"+inspec
    zfile=dir_path+"/"+zfile
    tfile=dir_path+"/"+tfile
#
# read in data
#
    specs=[]
    prior_spec_data,file_type=pmag.magic_read(inspec)
    if file_type != 'pmag_specimens':
        print  file_type, " this is not a valid pmag_specimens file"
        sys.exit()
    outstrings=[]
    for spec in prior_spec_data:
        tmp=spec["magic_method_codes"].split(":")
        meths=[]
        for meth in tmp:
            methods=meth.strip().split('-')
            for m in methods : 
                if m not in meths:meths.append(m)
        if 'DIR' in meths: # DE-BFL, DE-BFP or DE-FM
            specs.append(spec['er_specimen_name']) 
            if 'specimen_comp_name' in spec.keys() and spec['specimen_comp_name']!="" and spec['specimen_comp_name']!=" ":
                comp_name=spec['specimen_comp_name']
            else: 
                comp_name=string.uppercase[specs.count(spec['er_specimen_name'])-1]
            calculation_type="DE-BFL" # assume default calculation type is best-fit line
            if "BFP" in meths: 
                calculation_type='DE-BFP'
            elif "FM" in meths: 
                calculation_type='DE-FM'
            if zredo=="":zredo=open(zfile,"w")
            outstring='%s %s %s %s %s \n'%(spec["er_specimen_name"],calculation_type,spec["measurement_step_min"],spec["measurement_step_max"],comp_name)
            if outstring not in outstrings:
                zredo.write(outstring)
            outstrings.append(outstring) # only writes unique interpretions
        elif "PI" in meths and "TRM" in meths:   # thellier record
            if tredo=="":tredo=open(tfile,"w")
            outstring='%s %i %i \n'%(spec["er_specimen_name"],float(spec["measurement_step_min"]),float(spec["measurement_step_max"]))
            if outstring not in outstrings:
                tredo.write(outstring)
            outstrings.append(outstring) # only writes unique interpretions
    print 'Redo files saved to: ',zfile,tfile
if __name__ == "__main__":
    main()
