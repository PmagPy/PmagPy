#!/usr/bin/env python
import sys

def main():
    """
    NAME
        dir_redo.py

    DESCRIPTION
        converts the Cogne DIR format to PmagPy redo file

    SYNTAX 
        dir_redo.py [-h] [command line options]

    OPTIONS
        -h: prints help message and quits
        -f FILE: specify input file
        -F FILE: specify output file, default is 'zeq_redo' 
    """
    dir_path='.'
    zfile='zeq_redo'
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
        zfile=sys.argv[ind+1]
    inspec=dir_path+"/"+inspec
    zfile=dir_path+"/"+zfile
    zredo=open(zfile,"w")
#
# read in DIR file
#
    specs=[]
    prior_spec_data=open(inspec,'rU').readlines()
    for line in prior_spec_data:
        line=line.replace("Dir"," Dir")
        line=line.replace("OKir"," OKir")
        line=line.replace("Fish"," Fish")
        line=line.replace("Man"," Man")
        line=line.replace("GC"," GC")
        line=line.replace("-T","  - T")
        line=line.replace("-M","  - M")
        rec=line.split()
        if len(rec)<2:
            sys.exit() 
        if rec[1]=='Dir' or rec[1]=='GC': # skip all the other stuff
            spec=rec[0]
            specs.append(spec) 
            comp_name=string.uppercase[specs.count(spec)-1] # assign component names
            calculation_type="DE-FM"
            if rec[1]=='Dir' and rec[2]=="Kir": calculation_type="DE-BFL" # assume default calculation type is best-fit line
            if rec[1]=='Dir' and rec[2]=="OKir": calculation_type="DE-BFL-A" # anchored best-fit line
            if rec[1]=='Dir' and rec[2]=="Fish": calculation_type="DE-FM" # fisher mean
            if rec[1]=='GC' : calculation_type="DE-BFP" # best-fit plane
            min,max=rec[3],rec[5]
            beg,end="",""
            if min=="NRM":  beg=0   
            if min[0]=='M':
                beg=float(min[1:])*1e-3 # convert to T from mT
            elif min[0]=='T':
                beg=float(min[1:])+273 # convert to C to kelvin
            if max[0]=='M':
                end=float(max[1:])*1e-3 # convert to T from mT
            elif max[0]=='T':
                end=float(max[1:])+273 # convert to C to kelvin
                if beg==0:beg=273
            outstring='%s %s %s %s %s \n'%(spec,calculation_type,beg,end,comp_name)
            zredo.write(outstring)

if __name__ == "__main__":
    main()        
