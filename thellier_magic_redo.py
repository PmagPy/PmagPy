#!/usr/bin/env python
import sys,pmag,math,exceptions,nlt,string
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
        -CR PERC TYPE: apply a cooling rate correction.  
            PERC should be a percentage of original (say reduce to 90%)
            TYPE should be one of the following:
               EG (for educated guess); PS (based on pilots); TRM (based on comparison of two TRMs) 
        -Fcr  CRout: specify pmag_specimen format file for cooling rate corrected data
        -ANI: there are anisotropy data to correct thellier results
        -fan ANIFILE: specify rmag_anisotropy format file, default is rmag_anisotropy.txt 
        -Fac  ACout: specify pmag_specimen format file for anisotropy corrected data
                 default is AC_specimens.txt
        -NLT: there are non-linear trm data in the measurements file to correct thellier results
        -fnl NLTFILE: specify magic_measurments format file, default is magic_measurements.txt
        -Fnl NLTout: specify pmag_specimen format file for non-linear trm corrected data
                 default is NLT_specimens.txt
        -z use z component differenences for pTRM calculation
    """
    dir_path='.'
    critout=""
    version_num=pmag.get_version()
    field,first_save=-1,1
    spec,recnum,start,end=0,0,0,0
    frac=0
    NltRecs,PmagSpecs,AniSpecRecs,NltSpecRecs,CRSpecs=[],[],[],[],[]
    meas_file,pmag_file,mk_file="magic_measurements.txt","thellier_specimens.txt","thellier_redo"
    anis_file="rmag_anisotropy.txt"
    anisout,nltout="AC_specimens.txt","NLT_specimens.txt"
    crout="CR_specimens.txt"
    nlt_file=""
    
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
    if "-CR" in args:
        ind=args.index("-CR")
        frac=.01*float(sys.argv[ind+1])
        crtype=sys.argv[ind+2]
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
        nltrm=1
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
    critout=dir_path+"/"+critout
    try:
        open(critout,'rU')
        accept_keys=['specimen_int_ptrm_n','specimen_md','specimen_fvds','specimen_b_beta','specimen_dang','specimen_drats','specimen_Z']
        crit_data,file_type=pmag.magic_read(critout)
        print "Acceptance criteria read in from ", critout
        accept={}
        accept['specimen_int_ptrm_n']=2.0
        for critrec in crit_data:
            if critrec["pmag_criteria_code"]=="IE-SPEC":
                for key in accept_keys:
                    if key not in critrec.keys():
                        accept[key]=-1
                    else:
                        accept[key]=float(critrec[key])
    except:
        critout="" # no acceptance criteria specified
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
        nlt_data=meas_data  # look for trm acquisition data in the meas_data file
    else:
        nlt_file=dir_path+"/"+nlt_file 
        nlt_data,file_type=pmag.magic_read(nlt_file)
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
        for rec in meas_data:
            if rec["er_specimen_name"].lower()==s.lower(): 
                if "magic_instrument_codes" not in rec.keys():
                    rec["magic_instrument_codes"]="unknown"
                meths=rec["magic_method_codes"]
                for meth in meths:meth.strip()   # get rid of annoying spaces in method codes
                if "LP-PI-TRM" in meths: datablock.append(rec)
    #
    #  collect info for the PmagSpecRec dictionary
    #
        if len(datablock)>0:
            rec=datablock[0]
            PmagSpecRec["er_specimen_name"]=s
            PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
            PmagSpecRec["er_site_name"]=rec["er_site_name"]
            PmagSpecRec["er_location_name"]=rec["er_location_name"]
            PmagSpecRec["measurement_step_unit"]="K"
            PmagSpecRec["specimen_correction"]='u'
            if "magic_instrument_codes" not in rec.keys():
                PmagSpecRec["magic_instrument_codes"]="unknown"
            else:
                PmagSpecRec["magic_instrument_codes"]=rec["magic_instrument_codes"]
            if "magic_experiment_name" not in rec.keys():
                rec["magic_experiment_name"]=""
            else:
                PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
            meths=rec["magic_method_codes"].split(":")
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
                    pars,errcode=pmag.PintPars(araiblock,zijdblock,start,end)
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
                    PmagSpecRec["specimen_int_ptrm_n"]='%i '%(pars["specimen_int_ptrm_n"])
                    PmagSpecRec["specimen_rsc"]='%6.4f '%(pars["specimen_rsc"])
                    PmagSpecRec["specimen_md"]='%i '%(int(pars["specimen_md"]))
                    if PmagSpecRec["specimen_md"]=='-1':PmagSpecRec["specimen_md"]=""
                    PmagSpecRec["specimen_b_sigma"]='%5.3f '%(pars["specimen_b_sigma"])
                    if "IE-TT" not in  methcodes:methcodes.append("IE-TT")
                    methods=""
                    for meth in methcodes:
                        methods=methods+meth+":"
                    PmagSpecRec["magic_method_codes"]=methods[:-1]
                    PmagSpecRec["magic_software_packages"]=version_num
                    PmagSpecRec["specimen_description"]=comment
                    if critout!="":
                        score,kill=pmag.grade(PmagSpecRec,accept)
                        Grade=""
                        if score==len(accept.keys()):Grade='A'
                        if score==len(accept.keys())-1:Grade='B'
                        if score==len(accept.keys())-2:Grade='C'
                        if score==len(accept.keys())-3:Grade='D'
                        if score<=len(accept.keys())-4:Grade='F'
                        PmagSpecRec["specimen_grade"]=Grade
                    else:
                        PmagSpecRec["specimen_grade"]=""
                    if nltrm==0 and anis==0 and frac!=0: # apply cooling rate correction
                        CrSpecRec={}
                        for key in PmagSpecRec.keys():CrSpecRec[key]=PmagSpecRec[key]
                        inten=frac*float(CrSpecRec['specimen_int'])
                        CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
                        CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':DA-CR-'+crtype
                        CrSpecRec["specimen_correction"]='c'
                        CRSpecs.append(CrSpecRec)
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
                        NltRecs=[]
                        for NltRec in nlt_data:
                            if NltRec['er_specimen_name']==PmagSpecRec["er_specimen_name"]:
                                meths=NltRec["magic_method_codes"].split(":")
                                for meth in meths:meth.strip()
                                if "LP-TRM" in meths: NltRecs.append(NltRec)
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
                                if anis==0 and frac!=0:
                                    CrSpecRec={}
                                    for key in NltSpecRec.keys():CrSpecRec[key]=NltSpecRec[key]
                                    inten=frac*float(CrSpecRec['specimen_int'])
                                    CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
                                    CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':DA-CR-'+crtype
                                    CRSpecs.append(CrSpecRec)
                                NltSpecRecs.append(NltSpecRec)
    #
    # check on anisotropy correction
                        if anis==1:
                            if NltSpecRec!="":  
                                Spc=NltSpecRec
                            else: # find uncorrected data
                                Spc=PmagSpecRec
                            for AniSpec in anis_data:
                                if AniSpec["er_specimen_name"]==PmagSpecRec["er_specimen_name"]:
                                    AniSpecRec=pmag.thellier_anis_corr(Spc,AniSpec)
                                    AniSpecRec['specimen_grade']=PmagSpecRec['specimen_grade']
                                    inst_codes=Spc["magic_instrument_codes"]
                                    if "magic_instrument_codes" in AniSpec.keys():
                                        if inst_codes=="unknown":
                                            inst_codes=AniSpec["magic_instrument_codes"]
                                        else:
                                            inst_codes=inst_codes+":"+AniSpec["magic_instrument_codes"]
                                    AniSpecRec["magic_instrument_codes"]=inst_codes
                                    AniSpecRec["specimen_correction"]='c'
                                    AniSpecRec["magic_software_packages"]=version_num
                                    if frac!=0:
                                        CrSpecRec={}
                                        for key in AniSpecRec.keys():CrSpecRec[key]=AniSpecRec[key]
                                        inten=frac*float(CrSpecRec['specimen_int'])
                                        CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
                                        CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':DA-CR-'+crtype
                                        CRSpecs.append(CrSpecRec)
                                    AniSpecRecs.append(AniSpecRec) 
                                    break
                    elif anis==1:
                        for AniSpec in anis_data:
                            if AniSpec["er_specimen_name"]==PmagSpecRec["er_specimen_name"]:
                                AniSpecRec=pmag.thellier_anis_corr(PmagSpecRec,AniSpec)
                                AniSpecRec['specimen_grade']=PmagSpecRec['specimen_grade']
                                inst_codes=PmagSpecRec["magic_instrument_codes"]
                                if "magic_instrument_codes" in AniSpec.keys():
                                    if inst_codes=="unknown":
                                        inst_codes=AniSpec["magic_instrument_codes"]
                                    else:
                                        inst_codes=inst_codes+":"+AniSpec["magic_instrument_codes"]
                                AniSpecRec["magic_instrument_codes"]=inst_codes
                                AniSpecRec["specimen_correction"]='c'
                                AniSpecRec["magic_software_packages"]=version_num
                                if frac!=0:
                                    CrSpecRec={}
                                    for key in AniSpecRec.keys():CrSpecRec[key]=AniSpecRec[key]
                                    inten=frac*float(CrSpecRec['specimen_int'])
                                    CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
                                    CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':DA-CR-'+crtype
                                    CRSpecs.append(CrSpecRec)
                                AniSpecRecs.append(AniSpecRec) 
                                break
                spec +=1
        else:
            print "skipping ",s
            spec+=1
    pmag_file=dir_path+'/'+pmag_file
    pmag.magic_write(pmag_file,PmagSpecs,'pmag_specimens')
    if anis==1:
        anisout=dir_path+'/'+anisout
        pmag.magic_write(anisout,AniSpecRecs,'pmag_specimens')
    if nltrm==1:
        nltout=dir_path+'/'+nltout
        pmag.magic_write(nltout,NltSpecRecs,'pmag_specimens')
    if frac!=0:
        crout=dir_path+'/'+crout
        pmag.magic_write(crout,CRSpecs,'pmag_specimens')
main()
