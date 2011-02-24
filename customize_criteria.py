#!/usr/bin/env python
import pmag,sys
def main():
    """
    NAME
        customize_criteria.py

    DESCRIPTION
        Allows user to specify acceptance criteria, saves them in pmag_criteria.txt

    SYNTAX
        customize_criteria.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -f IFILE, reads in existing criteria
        -F OFILE, writes to pmag_criteria format file

    DEFAULTS
         IFILE: pmag_criteria.txt
         OFILE: pmag_criteria.txt
  
    OUTPUT
        creates a pmag_criteria.txt formatted output file
    """
    infile,critout="","pmag_criteria.txt"
    SpecCrit={}
#
# set some sort of quasi-reasonable default criteria
#
    SpecCrit['pmag_criteria_code']='DE-SPEC'
    SpecCrit['specimen_mad']='5.49'
    SpecCrit['specimen_alpha95']='5.49'
    SpecCrit['specimen_n']='4'
    SpecIntCrit={}
    SpecIntCrit['pmag_criteria_code']='IE-SPEC'
    SpecIntCrit['specimen_int_ptrm_n']='2'
    SpecIntCrit['specimen_drats']='20.5'
    SpecIntCrit['specimen_b_beta']='0.1'
    SpecIntCrit['specimen_md']='15'
    SpecIntCrit['specimen_fvds']='0.7'
    SpecIntCrit['specimen_q']='1.0'
    SpecIntCrit['specimen_dang']='10.5'
    SpecIntCrit['specimen_int_mad']='10.5'
    SpecIntCrit['specimen_Z']='4'
    #SpecIntCrit['measurement_step_min']='373'
    #SpecIntCrit['measurement_step_max']='623'
    SampCrit={}
    SampCrit['pmag_criteria_code']='DE-SAMP'
    SampCrit['sample_alpha95']='10.49'
    SampIntCrit={}
    SampIntCrit['pmag_criteria_code']='IE-SAMP'
    SampIntCrit['sample_int_n']='2'
    SampIntCrit['sample_int_sigma']='5.5e-6'
    SampIntCrit['sample_int_sigma_perc']='15.5'
    SiteIntCrit={}
    SiteIntCrit['pmag_criteria_code']='IE-SITE'
    SiteIntCrit['site_int_n']='2'
    SiteIntCrit['site_int_sigma']='5.5e-6'
    SiteIntCrit['site_int_sigma_perc']='15.5'
    SiteCrit={}
    SiteCrit['pmag_criteria_code']='DE-SITE'
    SiteCrit['site_n']='5'
    SiteCrit['site_n_lines']='4'
    SiteCrit['site_k']='100'
    SiteCrit['site_alpha95']='180'
    NpoleCrit={}
    NpoleCrit['pmag_criteria_code']='NPOLE'
    NpoleCrit['site_polarity']="n"
    RpoleCrit={}
    RpoleCrit['pmag_criteria_code']='RPOLE'
    RpoleCrit['site_polarity']="r"
# parse command line options
    if  '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        infile=sys.argv[ind+1]
        crit_data,file_type=pmag.magic_read(infile)
        if file_type!='pmag_criteria':
            print 'bad input file'
            print main.__doc__
            sys.exit()
        for critrec in crit_data:
            if critrec["pmag_criteria_code"]=="DE-SPEC": SpecCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SPEC": SpecIntCrit=critrec
            if critrec["pmag_criteria_code"]=="DE-SAMP": SampCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SAMP": SampIntCrit=critrec
            if critrec["pmag_criteria_code"]=="IE-SITE": SiteIntCrit=critrec
            if critrec["pmag_criteria_code"]=="DE-SITE": SiteCrit=critrec
            if critrec["pmag_criteria_code"]=="NPOLE": NpoleCrit=critrec
            if critrec["pmag_criteria_code"]=="RPOLE": RpoleCrit=critrec
        print "Acceptance criteria read in from ", infile
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        critout=sys.argv[ind+1]
    Dcrit,Icrit,nocrit=0,0,0
    custom='1'
    crit=raw_input(" [0] Use no acceptance criteria?\n [1] full vector\n [2] direction only\n [3] intensity only \n ")
    if crit=="0": nocrit=1
    if crit=="1": Dcrit,Icrit=1,1
    if crit=="2": Dcrit,Icrit=1,0
    if crit=="3": Dcrit,Icrit=0,1
    if nocrit==1:
        print 'Using no selection criteria '
        SpecCrit={}
        SpecCrit['pmag_criteria_code']='DE-SPEC'
        SpecCrit['specimen_mad']='180.'
        SpecCrit['specimen_alpha95']='180.'
        SpecCrit['specimen_n']='0'
        SpecIntCrit={}
        SpecIntCrit['pmag_criteria_code']='IE-SPEC'
        SpecIntCrit['specimen_int_ptrm_n']='0'
        SpecIntCrit['specimen_drats']='100'
        SpecIntCrit['specimen_b_beta']='5'
        SpecIntCrit['specimen_md']='100'
        SpecIntCrit['specimen_fvds']='0'
        SpecIntCrit['specimen_q']='0'
        SpecIntCrit['specimen_dang']='180.'
        SpecIntCrit['specimen_Z']='100.'
        SpecIntCrit['specimen_int_mad']='180.'
        #SpecIntCrit['measurement_step_min']='373'
        SpecIntCrit['measurement_step_max']='0'
        SampCrit={}
        SampCrit['pmag_criteria_code']='DE-SAMP'
        SampCrit['sample_alpha95']='180.'
        SampIntCrit={}
        SampIntCrit['pmag_criteria_code']='IE-SAMP'
        SampIntCrit['sample_int_n']='0'
        SampIntCrit['sample_int_sigma']='1000'
        SampIntCrit['sample_int_sigma_perc']='500'
        SiteIntCrit={}
        SiteIntCrit['pmag_criteria_code']='IE-SITE'
        SiteIntCrit['site_int_n']='0'
        SiteIntCrit['site_int_sigma']='1000'
        SiteIntCrit['site_int_sigma_perc']='500'
        SiteCrit={}
        SiteCrit['pmag_criteria_code']='DE-SITE'
        SiteCrit['site_n']='0'
        SiteCrit['site_n_lines']='0'
        SiteCrit['site_k']='0'
        SiteCrit['site_alpha95']='180'
        NpoleCrit={}
        NpoleCrit['pmag_criteria_code']='NPOLE'
        NpoleCrit['site_polarity']="n"
        RpoleCrit={}
        RpoleCrit['pmag_criteria_code']='RPOLE'
        RpoleCrit['site_polarity']="r"
    while custom=='1':
       if  Dcrit==1:
            for key in SpecCrit.keys():
                if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and SpecCrit[key]!="":
                    print key, SpecCrit[key]
                    new=raw_input("Enter new criterion (return to keep default) ")
                    if new != "": SpecCrit[key]=(new)
            for key in SampCrit.keys():
                if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and SampCrit[key]!="":
                    print key, SampCrit[key]
                    new=raw_input("Enter new criterion (return to keep default) ")
                    if new != "": SampCrit[key]=(new)
            for key in SiteCrit.keys():
                if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and SiteCrit[key]!="":
                    print key, SiteCrit[key]
                    new=raw_input("Enter new criterion (return to keep default) ")
                    if new != "": SiteCrit[key]=(new)
       if Icrit==1:
            for key in SpecIntCrit.keys():
                if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and SpecIntCrit[key]!="":
                   print key, SpecIntCrit[key]
                   new=raw_input("Enter new criterion (return to keep default) ")
                   if new != "": SpecIntCrit[key]=(new)
            for key in SiteIntCrit.keys():
                if key!='pmag_criteria_code' and key!='er_citation_names' and key!='criteria_definition' and SiteIntCrit[key]!="":
                   print key, SiteIntCrit[key]
                   new=raw_input("Enter new criterion (return to keep default) ")
                   if new != "": SiteIntCrit[key]=(new)
       custom=raw_input("Customize criteria again ? 1/[0]")
    SpecCrit['er_citation_names']="This study"
    SpecIntCrit['er_citation_names']="This study"
    SampCrit['er_citation_names']="This study"
    SampIntCrit['er_citation_names']="This study"
    SiteIntCrit['er_citation_names']="This study"
    SiteCrit['er_citation_names']="This study"
    NpoleCrit['er_citation_names']="This study"
    RpoleCrit['er_citation_names']="This study"
    SpecCrit['criteria_definition']="Criteria for selection of specimen direction"
    SpecIntCrit['criteria_definition']="Criteria for selection of specimen intensity"
    SampCrit['criteria_definition']="Criteria for selection of sample direction"
    SiteIntCrit['criteria_definition']="Criteria for selection of site intensity"
    SiteCrit['criteria_definition']="Criteria for selection of site direction"
    NpoleCrit['criteria_definition']="Criteria for inclusion in normal mean"
    RpoleCrit['criteria_definition']="Criteria for inclusion in reverse mean"
    TmpCrits,PmagCrits=[],[]
    TmpCrits.append(SpecCrit)
    TmpCrits.append(SpecIntCrit)
    TmpCrits.append(SampCrit)
    TmpCrits.append(SampIntCrit)
    TmpCrits.append(SiteIntCrit)
    TmpCrits.append(SiteCrit)
    TmpCrits.append(NpoleCrit)
    TmpCrits.append(RpoleCrit)
    #
    # assemble criteria keys
    #
    PmagCrits,critkeys=pmag.fillkeys(TmpCrits)
    pmag.magic_write(critout,PmagCrits,'pmag_criteria')
    print "Criteria saved in pmag_criteria.txt"

    pmag.magic_write(critout,TmpCrits,'pmag_criteria')
    print "\n Pmag Criteria stored in ",critout,'\n'
main()
