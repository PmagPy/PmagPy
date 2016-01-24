#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag
import pmagpy.nlt as nlt

def main():
    """
    NAME
        thellier_magic_redo.py

    DESCRIPTION
        Calculates paleointensity parameters for thellier-thellier type data using bounds
        stored in the "redo" file

    SYNTAX
        thellier_magic_redo [command line options]

    OPTIONS
        -h prints help message
        -usr USER:   identify user, default is ""
        -fcr CRIT, set criteria for grading
        -f IN: specify input file, default is magic_measurements.txt
        -fre REDO: specify redo file, default is "thellier_redo"
        -F OUT: specify output file, default is thellier_specimens.txt
        -leg:  attaches "Recalculated from original measurements; supercedes published results. " to comment field
        -CR PERC TYPE: apply a blanket cooling rate correction if none supplied in the er_samples.txt file 
            PERC should be a percentage of original (say reduce to 90%)
            TYPE should be one of the following:
               EG (for educated guess); PS (based on pilots); TRM (based on comparison of two TRMs) 
        -ANI:  perform anisotropy correction
        -fsa SAMPFILE: er_samples.txt file with cooling rate correction information, default is NO CORRECTION
        -Fcr  CRout: specify pmag_specimen format file for cooling rate corrected data
        -fan ANIFILE: specify rmag_anisotropy format file, default is rmag_anisotropy.txt 
        -Fac  ACout: specify pmag_specimen format file for anisotropy corrected data
                 default is AC_specimens.txt
        -fnl NLTFILE: specify magic_measurments format file, default is magic_measurements.txt
        -Fnl NLTout: specify pmag_specimen format file for non-linear trm corrected data
                 default is NLT_specimens.txt
        -z use z component differenences for pTRM calculation

    INPUT
        a thellier_redo file is Specimen_name Tmin Tmax (where Tmin and Tmax are in Centigrade)
    """
    dir_path='.'
    critout=""
    version_num=pmag.get_version()
    field,first_save=-1,1
    spec,recnum,start,end=0,0,0,0
    crfrac=0
    NltRecs,PmagSpecs,AniSpecRecs,NltSpecRecs,CRSpecs=[],[],[],[],[]
    meas_file,pmag_file,mk_file="magic_measurements.txt","thellier_specimens.txt","thellier_redo"
    anis_file="rmag_anisotropy.txt"
    anisout,nltout="AC_specimens.txt","NLT_specimens.txt"
    crout="CR_specimens.txt"
    nlt_file=""
    samp_file=""
    comment,user="","unknown"
    anis,nltrm=0,0
    jackknife=0 # maybe in future can do jackknife
    args=sys.argv
    Zdiff=0
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=sys.argv[ind+1]
    if "-leg" in args: comment="Recalculated from original measurements; supercedes published results. "
    cool=0
    if "-CR" in args:
        cool=1
        ind=args.index("-CR")
        crfrac=.01*float(sys.argv[ind+1])
        crtype='DA-CR-'+sys.argv[ind+2]
    if "-Fcr" in args:
        ind=args.index("-Fcr")
        crout=sys.argv[ind+1]
    if "-f" in args:
        ind=args.index("-f")
        meas_file=sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        pmag_file=sys.argv[ind+1]
    if "-fre" in args:
        ind=args.index("-fre")
        mk_file=args[ind+1]
    if "-fsa" in args:
        ind=args.index("-fsa")
        samp_file=dir_path+'/'+args[ind+1]
        Samps,file_type=pmag.magic_read(samp_file)
        SampCRs=pmag.get_dictitem(Samps,'cooling_rate_corr','','F') # get samples cooling rate corrections
        cool=1
        if file_type!='er_samples':
            print 'not a valid er_samples.txt file'
            sys.exit()
    #
    #
    if "-ANI" in args:
        anis=1
        ind=args.index("-ANI")
        if "-Fac" in args:
            ind=args.index("-Fac")
            anisout=args[ind+1]
        if "-fan" in args:
            ind=args.index("-fan")
            anis_file=args[ind+1]
    #
    if "-NLT" in args:
        if "-Fnl" in args:
            ind=args.index("-Fnl")
            nltout=args[ind+1]
        if "-fnl" in args:
            ind=args.index("-fnl")
            nlt_file=args[ind+1]
    if "-z" in args: Zdiff=1
    if '-fcr' in sys.argv: 
        ind=args.index("-fcr")
        critout=sys.argv[ind+1]
#
#  start reading in data:
#
    meas_file=dir_path+"/"+meas_file
    mk_file=dir_path+"/"+mk_file
    accept=pmag.default_criteria(1)[0] # set criteria to none
    if critout!="":
        critout=dir_path+"/"+critout
        crit_data,file_type=pmag.magic_read(critout)
        if file_type!='pmag_criteria':
            print 'bad pmag_criteria file, using no acceptance criteria'
        print "Acceptance criteria read in from ", critout
        for critrec in crit_data:
            if 'sample_int_sigma_uT' in critrec.keys(): # accommodate Shaar's new criterion
                    critrec['sample_int_sigma']='%10.3e'%(eval(critrec['sample_int_sigma_uT'])*1e-6)
            for key in critrec.keys():
                if key not in accept.keys() and critrec[key]!='':
                    accept[key]=critrec[key]
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print file_type
        print file_type,"This is not a valid magic_measurements file " 
        sys.exit()
    try:
        mk_f=open(mk_file,'rU')
    except:
        print "Bad redo file"
        sys.exit()
    mkspec=[]
    speclist=[]
    for line in mk_f.readlines():
        tmp=line.split()
        mkspec.append(tmp)
        speclist.append(tmp[0])
    if anis==1:
        anis_file=dir_path+"/"+anis_file 
        anis_data,file_type=pmag.magic_read(anis_file)
        if file_type != 'rmag_anisotropy':
            print file_type
            print file_type,"This is not a valid rmag_anisotropy file "
            sys.exit()
    if nlt_file=="":
        nlt_data=pmag.get_dictitem(meas_data,'magic_method_codes','LP-TRM','has')  # look for trm acquisition data in the meas_data file
    else:
        nlt_file=dir_path+"/"+nlt_file 
        nlt_data,file_type=pmag.magic_read(nlt_file)
    if len(nlt_data)>0:
        nltrm=1
#
# sort the specimen names and step through one by one
#
    sids=pmag.get_specs(meas_data)
# 
    print 'Processing ',len(speclist),' specimens - please wait '
    while spec < len(speclist):
        s=speclist[spec]
        recnum=0
        datablock=[]
        PmagSpecRec={}
        PmagSpecRec["er_analyst_mail_names"]=user
        PmagSpecRec["er_citation_names"]="This study"
        PmagSpecRec["magic_software_packages"]=version_num
        methcodes,inst_code=[],""
    #
    # find the data from the meas_data file for this specimen
    #
        datablock=pmag.get_dictitem(meas_data,'er_specimen_name',s,'T') 
        datablock=pmag.get_dictitem(datablock,'magic_method_codes','LP-PI-TRM','has') #pick out the thellier experiment data 
        if len(datablock)>0:
            for rec in datablock:
                if "magic_instrument_codes" not in rec.keys(): rec["magic_instrument_codes"]="unknown"
    #
    #  collect info for the PmagSpecRec dictionary
    #
            rec=datablock[0]
            PmagSpecRec["er_specimen_name"]=s
            PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
            PmagSpecRec["er_site_name"]=rec["er_site_name"]
            PmagSpecRec["er_location_name"]=rec["er_location_name"]
            PmagSpecRec["measurement_step_unit"]="K"
            PmagSpecRec["specimen_correction"]='u'
            if "er_expedition_name" in rec.keys():PmagSpecRec["er_expedition_name"]=rec["er_expedition_name"]
            if "magic_instrument_codes" not in rec.keys():
                PmagSpecRec["magic_instrument_codes"]="unknown"
            else:
                PmagSpecRec["magic_instrument_codes"]=rec["magic_instrument_codes"]
            if "magic_experiment_name" not in rec.keys():
                rec["magic_experiment_name"]=""
            else:
                PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
            meths=rec["magic_experiment_name"].split(":")
            for meth in meths:
                if meth.strip() not in methcodes and "LP-" in meth:methcodes.append(meth.strip())
    #
    # sort out the data into first_Z, first_I, ptrm_check, ptrm_tail
    #
            araiblock,field=pmag.sortarai(datablock,s,Zdiff)
            first_Z=araiblock[0]
            first_I=araiblock[1]
            ptrm_check=araiblock[2]
            ptrm_tail=araiblock[3]
            if len(first_I)<3 or len(first_Z)<4:
                spec+=1
                print 'skipping specimen ', s 
            else:
    #
    # get start, end
    #
                for redospec in mkspec:
                    if redospec[0]==s:
    	                b,e=float(redospec[1]),float(redospec[2])
                        break
                if e > float(first_Z[-1][0]):e=float(first_Z[-1][0])
                for recnum in range(len(first_Z)):
            	    if first_Z[recnum][0]==b:start=recnum
            	    if first_Z[recnum][0]==e:end=recnum
                nsteps=end-start
                if nsteps>2:
                    zijdblock,units=pmag.find_dmag_rec(s,meas_data)
                    pars,errcode=pmag.PintPars(datablock,araiblock,zijdblock,start,end,accept)
                    if 'specimen_scat' in pars.keys(): PmagSpecRec['specimen_scat']=pars['specimen_scat']
                    if 'specimen_frac' in pars.keys(): PmagSpecRec['specimen_frac']='%5.3f'%(pars['specimen_frac'])
                    if 'specimen_gmax' in pars.keys(): PmagSpecRec['specimen_gmax']='%5.3f'%(pars['specimen_gmax'])
                    pars['measurement_step_unit']=units
                    pars["specimen_lab_field_dc"]=field
                    pars["specimen_int"]=-1*field*pars["specimen_b"]
                    PmagSpecRec["measurement_step_min"]='%8.3e' % (pars["measurement_step_min"])
                    PmagSpecRec["measurement_step_max"]='%8.3e' % (pars["measurement_step_max"])
                    PmagSpecRec["specimen_int_n"]='%i'%(pars["specimen_int_n"])
                    PmagSpecRec["specimen_lab_field_dc"]='%8.3e'%(pars["specimen_lab_field_dc"])
                    PmagSpecRec["specimen_int"]='%9.4e '%(pars["specimen_int"])
                    PmagSpecRec["specimen_b"]='%5.3f '%(pars["specimen_b"])
                    PmagSpecRec["specimen_q"]='%5.1f '%(pars["specimen_q"])
                    PmagSpecRec["specimen_f"]='%5.3f '%(pars["specimen_f"])
                    PmagSpecRec["specimen_fvds"]='%5.3f'%(pars["specimen_fvds"])
                    PmagSpecRec["specimen_b_beta"]='%5.3f'%(pars["specimen_b_beta"])
                    PmagSpecRec["specimen_int_mad"]='%7.1f'%(pars["specimen_int_mad"])
                    PmagSpecRec["specimen_Z"]='%7.1f'%(pars["specimen_Z"])
                    PmagSpecRec["specimen_gamma"]='%7.1f'%(pars["specimen_gamma"])
                    if pars["method_codes"]!="" and pars["method_codes"] not in methcodes: methcodes.append(pars["method_codes"])
                    PmagSpecRec["specimen_dec"]='%7.1f'%(pars["specimen_dec"])
                    PmagSpecRec["specimen_inc"]='%7.1f'%(pars["specimen_inc"])
                    PmagSpecRec["specimen_tilt_correction"]='-1'
                    PmagSpecRec["specimen_direction_type"]='l'
                    PmagSpecRec["direction_type"]='l' # this is redudant, but helpful - won't be imported
                    PmagSpecRec["specimen_dang"]='%7.1f '%(pars["specimen_dang"])
                    PmagSpecRec["specimen_drats"]='%7.1f '%(pars["specimen_drats"])
                    PmagSpecRec["specimen_drat"]='%7.1f '%(pars["specimen_drat"])
                    PmagSpecRec["specimen_int_ptrm_n"]='%i '%(pars["specimen_int_ptrm_n"])
                    PmagSpecRec["specimen_rsc"]='%6.4f '%(pars["specimen_rsc"])
                    PmagSpecRec["specimen_md"]='%i '%(int(pars["specimen_md"]))
                    if PmagSpecRec["specimen_md"]=='-1':PmagSpecRec["specimen_md"]=""
                    PmagSpecRec["specimen_b_sigma"]='%5.3f '%(pars["specimen_b_sigma"])
                    if "IE-TT" not in  methcodes:methcodes.append("IE-TT")
                    methods=""
                    for meth in methcodes:
                        methods=methods+meth+":"
                    PmagSpecRec["magic_method_codes"]=methods.strip(':')
                    PmagSpecRec["magic_software_packages"]=version_num
                    PmagSpecRec["specimen_description"]=comment
                    if critout!="":
                        kill=pmag.grade(PmagSpecRec,accept,'specimen_int')
                        if len(kill)>0:
                            Grade='F' # fails
                        else:
                            Grade='A' # passes
                        PmagSpecRec["specimen_grade"]=Grade
                    else:
                        PmagSpecRec["specimen_grade"]="" # not graded
                    if nltrm==0 and anis==0 and cool!=0: # apply cooling rate correction
                        SCR=pmag.get_dictitem(SampCRs,'er_sample_name',PmagSpecRec['er_sample_name'],'T') # get this samples, cooling rate correction 
                        CrSpecRec=pmag.cooling_rate(PmagSpecRec,SCR,crfrac,crtype)
                        if CrSpecRec['er_specimen_name']!='none':CrSpecs.append(CrSpecRec)
                    PmagSpecs.append(PmagSpecRec)
                    NltSpecRec=""
    #
    # check on non-linear TRM correction
    #
                    if nltrm==1:
    #
    # find the data from the nlt_data list for this specimen
    #
                        TRMs,Bs=[],[]
                        NltSpecRec=""
                        NltRecs=pmag.get_dictitem(nlt_data,'er_specimen_name',PmagSpecRec['er_specimen_name'],'has') # fish out all the NLT data for this specimen
                        if len(NltRecs) > 2:
                            for NltRec in NltRecs:
                                Bs.append(float(NltRec['treatment_dc_field']))
                                TRMs.append(float(NltRec['measurement_magn_moment']))
                            NLTpars=nlt.NLtrm(Bs,TRMs,float(PmagSpecRec['specimen_int']),float(PmagSpecRec['specimen_lab_field_dc']),0) 
                            if NLTpars['banc']>0:
                                NltSpecRec={}
                                for key in PmagSpecRec.keys():
                                    NltSpecRec[key]=PmagSpecRec[key]
                                NltSpecRec['specimen_int']='%9.4e'%(NLTpars['banc'])  
                                NltSpecRec['magic_method_codes']=PmagSpecRec["magic_method_codes"]+":DA-NL"
                                NltSpecRec["specimen_correction"]='c'
                                NltSpecRec['specimen_grade']=PmagSpecRec['specimen_grade']
                                NltSpecRec["magic_software_packages"]=version_num
                                print NltSpecRec['er_specimen_name'],  ' Banc= ',float(NLTpars['banc'])*1e6
                                if anis==0 and cool!=0:
                                    SCR=pmag.get_dictitem(SampCRs,'er_sample_name',NltSpecRec['er_sample_name'],'T') # get this samples, cooling rate correction 
                                    CrSpecRec=pmag.cooling_rate(NltSpecRec,SCR,crfrac,crtype)
                                    if CrSpecRec['er_specimen_name']!='none':CrSpecs.append(CrSpecRec)
                                NltSpecRecs.append(NltSpecRec)
    #
    # check on anisotropy correction
                        if anis==1:
                            if NltSpecRec!="":  
                                Spc=NltSpecRec
                            else: # find uncorrected data
                                Spc=PmagSpecRec
                            AniSpecs=pmag.get_dictitem(anis_data,'er_specimen_name',PmagSpecRec['er_specimen_name'],'T')
                            if len(AniSpecs)>0:
                                    AniSpec=AniSpecs[0]
                                    AniSpecRec=pmag.doaniscorr(Spc,AniSpec)
                                    AniSpecRec['specimen_grade']=PmagSpecRec['specimen_grade']
                                    AniSpecRec["magic_instrument_codes"]=PmagSpecRec['magic_instrument_codes']
                                    AniSpecRec["specimen_correction"]='c'
                                    AniSpecRec["magic_software_packages"]=version_num
                                    if cool!=0:
                                        SCR=pmag.get_dictitem(SampCRs,'er_sample_name',AniSpecRec['er_sample_name'],'T') # get this samples, cooling rate correction 
                                        CrSpecRec=pmag.cooling_rate(AniSpecRec,SCR,crfrac,crtype)
                                        if CrSpecRec['er_specimen_name']!='none':CrSpecs.append(CrSpecRec)
                                    AniSpecRecs.append(AniSpecRec) 
                    elif anis==1:
                        AniSpecs=pmag.get_dictitem(anis_data,'er_specimen_name',PmagSpecRec['er_specimen_name'],'T')
                        if len(AniSpecs)>0:
                                AniSpec=AniSpecs[0]
                                AniSpecRec=pmag.doaniscorr(PmagSpecRec,AniSpec)
                                AniSpecRec['specimen_grade']=PmagSpecRec['specimen_grade']
                                AniSpecRec["magic_instrument_codes"]=PmagSpecRec["magic_instrument_codes"]
                                AniSpecRec["specimen_correction"]='c'
                                AniSpecRec["magic_software_packages"]=version_num
                                if crfrac!=0:
                                    CrSpecRec={}
                                    for key in AniSpecRec.keys():CrSpecRec[key]=AniSpecRec[key]
                                    inten=frac*float(CrSpecRec['specimen_int'])
                                    CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
                                    CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':DA-CR-'+crtype
                                    CRSpecs.append(CrSpecRec)
                                AniSpecRecs.append(AniSpecRec) 
                spec +=1
        else:
            print "skipping ",s
            spec+=1
    pmag_file=dir_path+'/'+pmag_file
    pmag.magic_write(pmag_file,PmagSpecs,'pmag_specimens')
    print 'uncorrected thellier data saved in: ',pmag_file
    if anis==1 and len(AniSpecRecs)>0:
        anisout=dir_path+'/'+anisout
        pmag.magic_write(anisout,AniSpecRecs,'pmag_specimens')
        print 'anisotropy corrected data saved in: ',anisout
    if nltrm==1 and len(NltSpecRecs)>0:
        nltout=dir_path+'/'+nltout
        pmag.magic_write(nltout,NltSpecRecs,'pmag_specimens')
        print 'non-linear TRM corrected data saved in: ',nltout
    if crfrac!=0:
        crout=dir_path+'/'+crout
        pmag.magic_write(crout,CRSpecs,'pmag_specimens')
        print 'cooling rate corrected data saved in: ',crout

if __name__ == "__main__":
    main()
