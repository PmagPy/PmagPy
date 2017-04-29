#!/usr/bin/env python
from __future__ import print_function
import sys
import string

def main():
    """
    NAME
        pmm_redo.py

    DESCRIPTION
        converts the UCSC PMM files format to PmagPy redo file

    SYNTAX 
        pmm_redo.py [-h] [command line options]

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify input file
        -F FILE: specify output file, default is 'zeq_redo' 
    """
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    zfile=dir_path+'/zeq_redo'
    if '-h' in sys.argv:
        print(main.__doc__)
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        inspec=dir_path+'/'+sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        zfile=dir_path+'/'+sys.argv[ind+1]
    zredo=open(zfile,"w")
#
# read in PMM file
#
    specs=[]
    prior_spec_data=open(inspec,'r').readlines()
    for line in prior_spec_data:
      rec=line.split(',')
      if rec[0][0]!='"' and rec[0]!="ID" and len(rec)>2: # skip all the header stuff
            spec=rec[0]
            specs.append(spec) 
            comp_name=string.uppercase[specs.count(spec)-1] # assign component names
            calculation_type="DE-FM"
            if rec[1].strip()=='DirPCA': calculation_type="DE-BFL" # assume default calculation type is best-fit line
            if rec[1].strip()=='DirOPCA': calculation_type="DE-BFL-A" # anchored best-fit line
            if rec[1].strip()=='GCPCA' or rec[1]=='GCnPCA' : calculation_type="DE-BFP" # best-fit plane
            steps=rec[2].strip().split('-')
            min,max=steps[0],steps[1]
            beg,end="",""
            if min=="NRM":  
               beg=0   
            elif min[0]=='M' or min[0]=='H':
                beg=float(min[1:])*1e-3 # convert to T from mT
            elif min[-1]=='M':
                beg=float(min[:-1])*1e-3 # convert to T from mT
            elif min[0]=='T':
                beg=float(min[1:])+273 # convert to C to kelvin
            if max[0]=='M' or max[0]=='H':
                end=float(max[1:])*1e-3 # convert to T from mT
            elif max[0]=='T':
                end=float(max[1:])+273 # convert to C to kelvin
            elif max[-1]=='M':
                end=float(max[1:])*1e-3 # convert to T from mT
            if beg==0:beg=273
            outstring='%s %s %s %s %s \n'%(spec,calculation_type,beg,end,comp_name)
            zredo.write(outstring)

if __name__ == "__main__":
    main()        
