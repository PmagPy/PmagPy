#!/usr/bin/env python
import pmag,exceptions,sys,pmagplotlib
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
        pick_AC_specimens.py [-h][-i][-fu TFILE][-fc AFILE][-F FILE]

    OPTIONS
        -h prints help message and quits
        -i allows interactive setting of file names
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
        FILE: pmag_specimens.txt
    """
    tspec="thellier_specimens.txt"
    aspec="AC_specimens.txt"
    ofile="pmag_specimens.txt"
    critfile="pmag_criteria.txt"
    ACSamplist,Samplist,sigmin=[],[],10000
    GoodSamps,SpecOuts=[],[]
    P={'cdf':1}
    pmagplotlib.plot_init(P['cdf'],5,5)
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
    Diff=[]
    for aspec in ACSpecs:
            grade,kill=pmag.grade(aspec,accept)
            if grade==len(accept): 
                print 'AC: ',aspec["er_specimen_name"],'%i'%(1e6*float(aspec["specimen_int"]))
                aint=(1e6*float(aspec["specimen_int"]))
                for spec in Specs:
                    if spec["er_specimen_name"]==aspec['er_specimen_name']:
                        print 'UC: ',spec["er_specimen_name"],'%i'%(1e6*float(spec["specimen_int"]))
                        int=(1e6*float(spec["specimen_int"]))
                        Diff.append(100.*abs(aint-int)/aint)
    x,s=pmag.gausspars(Diff)
    print x,s
    Diff.sort()
    print Diff[0],Diff[-1]
    pmagplotlib.plotCDF(P['cdf'],Diff,'% Difference','r')
    pmagplotlib.drawFIGS(P)
    raw_input()
main()



