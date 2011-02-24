#!/usr/bin/env python
import pmag,exceptions,sys
def main():
    """
    NAME
        compare_specimens.py
    
    DESCRIPTION
        finds  anisotropy corrected data and 
        compares with uncorrected. 
    
    SYNTAX
        compare_specimens.py [-h][-i][-t TSPEC][-a ACSPEC]

    OPTIONS
        -h prints help message and quits
        -i allows interactive setting of file names
        -fu TFILE uncorrected pmag_specimen format file with thellier interpretations
            created by thellier_magic_redo.py
        -fc AFILE anisotropy corrected pmag_specimen format file
            created by thellier_magic_redo.py
        -fcr CRIT pmag_criteria.txt format file with acceptance criteria
    DEFAULTS
        TFILE: thellier_specimens.txt
        AFILE: AC_specimens.txt
        CRIT: no  grade
    """
    tspec="thellier_specimens.txt"
    aspec="AC_specimens.txt"
    critfile=""
    ACSamplist,Samplist,sigmin=[],[],10000
    GoodSamps,SpecOuts=[],[]
# get arguments from command line
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-fu' in sys.argv:
        ind=sys.argv.index('-fu')
        tspec=sys.argv[ind+1]
    if '-fc' in sys.argv:
        ind=sys.argv.index('-fc')
        aspec=sys.argv[ind+1]
    if '-fcr' in sys.argv:
        ind=sys.argv.index('-fcr')
        critfile=sys.argv[ind+1]
    # read in pmag_specimens file
    Specs,file_type=pmag.magic_read(tspec)
    Speclist=pmag.get_specs(Specs)
    ACSpecs,file_type=pmag.magic_read(aspec)
    print len(Speclist),' uncorrected data read in from ',tspec
    print len(ACSpecs),' anisotropy corrected data read in from ',aspec
    keys=['specimen_int_mad','specimen_drats','specimen_fvds','specimen_b_beta','specimen_Z','specimen_md','specimen_dang']
    if critfile!="":
        accept={}
        Crits,file_type=pmag.magic_read(critfile)
        for crit in Crits:
            if critfile!='optimum_thelpars.txt':
                if crit['pmag_criteria_code']=='IE-SPEC':
                    for key in keys: accept[key]=float(crit[key]) # assign acceptance criteria
                    break
            else:
                if float(crit['sample_int_sigma_perc'])==float(sigcutoff):
                    for key in keys: accept[key]=float(crit[key])
    else:
        Crits=""
    ACspeclist=pmag.get_specs(ACSpecs)
    for spec in Specs:
            if spec["er_sample_name"] not in Samplist:Samplist.append(spec["er_sample_name"])
    for spec in ACSpecs:
            if spec["er_sample_name"] not in ACSamplist:ACSamplist.append(spec["er_sample_name"])
    #
    for samp in Samplist:
        useAC,Ints,ACInts,GoodSpecs,AC,UC=0,[],[],[],[],[]
        for spec in Specs:
            if spec["er_sample_name"]==samp:
                    if critfile!="":
                        grade,kill=pmag.grade(spec,accept)
                        if grade==len(accept):grade='A'
                        if grade<=len(accept)-1:grade='B'
                        if grade<=len(accept)-2:grade='C'
                        if grade<=len(accept)-3:grade='F'
                    else:
                        grade=""
                    print 'UC: ',spec['er_specimen_name'],'%7.1f'%(1e6*float(spec['specimen_int'])),grade
                    if samp in ACSamplist:
                        for aspec in ACSpecs:
                            if aspec["er_specimen_name"]==spec['er_specimen_name']:
                                if critfile!="":
                                    grade,kill=pmag.grade(aspec,accept)
                                    if grade==len(accept):grade='A'
                                    if grade<=len(accept)-1:grade='B'
                                    if grade<=len(accept)-2:grade='C'
                                    if grade<=len(accept)-3:grade='F'
                                else:
                                    grade=""
                                print '  AC: ',aspec['er_specimen_name'],'%7.1f'%(1e6*float(aspec['specimen_int'])),grade
                                break
        raw_input('<return> to continue\n')
main()
