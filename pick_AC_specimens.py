#!/usr/bin/env python
import pmag,exceptions,sys
def main():
    """
    NAME
        pick_AC_specimens.py
    
    DESCRIPTION
        finds whether anisotropy correction yeilds more tightly 
        grouped intensities  than uncorrected data. 
        picks either all corrected or all uncorrected data and 
        puts in pmag_specimen format file
    
    SYNTAX
        pick_AC_specimens.py [command line options]

    OPTIONS
        -h prints help message and quits
        -fu TFILE uncorrected pmag_specimen format file with thellier interpretations
            created by thellier_magic_redo.py
        -fc AFILE anisotropy corrected pmag_specimen format file
            created by thellier_magic_redo.py
        -fcr CRIT pmag_criteria.txt format file with acceptance criteria
        -opt SIG use the optimizer_thelpars.txt file for criteria
        -F FILE pmag_specimens format output file with "best" set of data

    DEFAULTS
        TFILE: thellier_specimens.txt
        AFILE: AC_specimens.txt
        FILE: TorAC_specimens.txt
    """
    tspec="thellier_specimens.txt"
    aspec="AC_specimens.txt"
    ofile="TorAC_specimens.txt"
    critfile="pmag_criteria.txt"
    dir_path='.'
    ACSamplist,Samplist,sigmin=[],[],10000
    GoodSamps,SpecOuts=[],[]
# get arguments from command line
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-fu' in sys.argv:
        ind=sys.argv.index('-fu')
        tspec=sys.argv[ind+1]
    if '-fc' in sys.argv:
        ind=sys.argv.index('-fc')
        aspec=sys.argv[ind+1]
    if '-fcr' in sys.argv:
        ind=sys.argv.index('-fcr')
        critfile=sys.argv[ind+1]
    if '-opt' in sys.argv:
        ind=sys.argv.index('-opt')
        critfile='optimum_thelpars.txt'
        sigcutoff=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        ofile=sys.argv[ind+1]
    if '-i' in sys.argv:
        file=raw_input(" thellier_specimnens.txt file [thellier_specimens.txt]: ")
        if file!="":tfile=file 
        file=raw_input(" AC_specimnens.txt file [AC_specimens.txt]: ")
        if file!="":afile=file 
        file=raw_input(" pmag_specimnens.txt file [pmag_specimens.txt]: ")
        if file!="":ofile=file 
    # read in pmag_specimens file
    tspec=dir_path+'/'+tspec
    aspec=dir_path+'/'+aspec
    ofile=dir_path+'/'+ofile
    critfile=dir_path+'/'+critfile
    Specs,file_type=pmag.magic_read(tspec)
    Speclist=pmag.get_specs(Specs)
    ACSpecs,file_type=pmag.magic_read(aspec)
    ACspeclist=pmag.get_specs(ACSpecs)
    Crits,file_type=pmag.magic_read(critfile)
    keys=['specimen_int_mad','specimen_drats','specimen_fvds','specimen_b_beta','specimen_Z','specimen_md','specimen_dang']
    accept={}
    for crit in Crits:
        if critfile!='optimum_thelpars.txt':
            if crit['pmag_criteria_code']=='IE-SPEC':
                for key in keys: accept[key]=float(crit[key]) # assign acceptance criteria
                break
        else:
            if float(crit['sample_int_sigma_perc'])==float(sigcutoff):
                for key in keys: accept[key]=float(crit[key])
    print len(accept)
    for spec in Specs:
        grade,kill=pmag.grade(spec,accept)
        if grade==len(accept): 
            if spec["er_sample_name"] not in Samplist:Samplist.append(spec["er_sample_name"])
    for spec in ACSpecs:
        grade,kill=pmag.grade(spec,accept)
        if grade==len(accept): 
            if spec["er_sample_name"] not in ACSamplist:ACSamplist.append(spec["er_sample_name"])
    #
    for samp in Samplist:
        print samp
        useAC,Ints,ACInts,GoodSpecs,AC,UC,ALL,ALLInts=0,[],[],[],[],[],[],[]
        sample_int_sigma_perc=""
        for spec in Specs:
            ThisAC=[]
            if spec["er_sample_name"]==samp:
                grade,kill=pmag.grade(spec,accept)
                if grade==len(accept): 
                    UC.append(spec)
                    print 'UC: ',spec["er_specimen_name"],'%i'%(1e6*float(spec["specimen_int"]))
                    Ints.append(float(spec["specimen_int"]))
        if samp in ACSamplist:
            for spec in ACSpecs:
                if spec["er_sample_name"]==samp:
                    grade,kill=pmag.grade(spec,accept)
                    if grade==len(accept): 
                        AC.append(spec)
                        print 'AC: ',spec["er_specimen_name"],'%i'%(1e6*float(spec["specimen_int"]))
                        ACInts.append(float(spec["specimen_int"]))
                        ThisAC.append(spec["er_specimen_name"]) 
                        ALLInts.append(float(spec["specimen_int"]))
                        ALL.append(spec)
        for spec in UC:
            if spec['er_specimen_name'] not in ThisAC:
                ALLInts.append(float(spec["specimen_int"]))
                ALL.append(spec)
        if len(AC)>2:
            allx,allstd=pmag.gausspars(ALLInts)
            ix,istd=pmag.gausspars(Ints)
            ax,astd=pmag.gausspars(ACInts)
            print "Nall= ",len(ALLInts),allx,allstd,"Ni= ",len(Ints),ix,istd,"Na= ",len(ACInts),ax,astd
            if astd<istd: 
                if astd<allstd:
                    for spec in AC: SpecOuts.append(spec)
                    print 'using AC'
                else:
                    for spec in ALL: 
                        SpecOuts.append(spec)
                        print spec['er_specimen_name'],spec['magic_method_codes'],spec['specimen_int']
                    print 'using ALL'
            else:
                if istd<allstd: 
                    for spec in UC: SpecOuts.append(spec)
                    print 'using UC'
                else:
                    for spec in ALL: 
                        SpecOuts.append(spec)
                        print spec['er_specimen_name'],spec['magic_method_codes'],spec['specimen_int']
                    print 'using ALL'
        else:
            for spec in UC: SpecOuts.append(spec)
            print 'No AC, using UC'
        raw_input()
    pmag.magic_write(SpecOuts,ofile,'pmag_specimens')
    print 'thellier data assessed for AC correction put in ', ofile 
main()
