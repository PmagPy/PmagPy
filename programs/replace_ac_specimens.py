#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag

def main():
    """
    NAME
        replace_AC_specimens.py
    
    DESCRIPTION
        finds  anisotropy corrected data and 
        replaces that specimen with it.
        puts in pmag_specimen format file
    
    SYNTAX
        replace_AC_specimens.py [command line options]

    OPTIONS
        -h prints help message and quits
        -i allows interactive setting of file names
        -fu TFILE uncorrected pmag_specimen format file with thellier interpretations
            created by thellier_magic_redo.py
        -fc AFILE anisotropy corrected pmag_specimen format file
            created by thellier_magic_redo.py
        -F FILE pmag_specimens format output file 

    DEFAULTS
        TFILE: thellier_specimens.txt
        AFILE: AC_specimens.txt
        FILE: TorAC_specimens.txt
    """
    dir_path='.'
    tspec="thellier_specimens.txt"
    aspec="AC_specimens.txt"
    ofile="TorAC_specimens.txt"
    critfile="pmag_criteria.txt"
    ACSamplist,Samplist,sigmin=[],[],10000
    GoodSamps,SpecOuts=[],[]
# get arguments from command line
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-fu' in sys.argv:
        ind=sys.argv.index('-fu')
        tspec=sys.argv[ind+1]
    if '-fc' in sys.argv:
        ind=sys.argv.index('-fc')
        aspec=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
         
    # read in pmag_specimens file
    tspec=dir_path+'/'+tspec
    aspec=dir_path+'/'+aspec
    ofile=dir_path+'/'+ofile
    Specs,file_type=pmag.magic_read(tspec)
    Specs,file_type=pmag.magic_read(tspec)
    Speclist=pmag.get_specs(Specs)
    ACSpecs,file_type=pmag.magic_read(aspec)
    ACspeclist=pmag.get_specs(ACSpecs)
    for spec in Specs:
            if spec["er_sample_name"] not in Samplist:Samplist.append(spec["er_sample_name"])
    for spec in ACSpecs:
            if spec["er_sample_name"] not in ACSamplist:ACSamplist.append(spec["er_sample_name"])
    #
    for samp in Samplist:
        useAC,Ints,ACInts,GoodSpecs,AC,UC=0,[],[],[],[],[]
        for spec in Specs:
            if spec["er_sample_name"].lower()==samp.lower():
                    UC.append(spec)
        if samp in ACSamplist:
            for spec in ACSpecs:
                if spec["er_sample_name"].lower()==samp.lower():
                        AC.append(spec)
        if len(AC)>0:
            AClist=[]
            for spec in AC: 
                SpecOuts.append(spec)
                AClist.append(spec['er_specimen_name'])
                print('using AC: ',spec['er_specimen_name'],'%7.1f'%(1e6*float(spec['specimen_int'])))
            for spec in UC: 
                if spec['er_specimen_name'] not in AClist:
                   SpecOuts.append(spec)
#                   print 'using UC: ',spec['er_specimen_name'],'%7.1f'%(1e6*float(spec['specimen_int']))
        else:
            for spec in UC: 
                SpecOuts.append(spec)
#                print 'using UC: ',spec['er_specimen_name'],'%7.1f'%(1e6*float(spec['specimen_int']))
    SpecOuts,keys=pmag.fillkeys(SpecOuts)
    pmag.magic_write(ofile,SpecOuts,'pmag_specimens')
    print('thellier data assessed for AC correction put in ', ofile)

if __name__ == "__main__":
    main()
