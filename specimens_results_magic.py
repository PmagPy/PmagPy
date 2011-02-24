#!/usr/bin/env python
import sys,pmag,math
def main():
    """
    NAME
        specimens_results_magic.py

    DESCRIPTION
        combines pmag_specimens.txt file with age, location, acceptance criteria and 
        outputs pmag_results table along with other MagIC tables necessary for uploading to the database

    SYNTAX
        specimens_results_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -usr USER:   identify user, default is ""
        -f: specimen input magic_measurements format file, default is "magic_measurements.txt"
        -fsp: specimen input pmag_specimens format file, default is "pmag_specimens.txt"
        -fsm: sample input er_samples format file, default is "er_samples.txt"
        -fsi: specimen input er_sites format file, default is "er_sites.txt"
        -fla: specify a file with paleolatitudes for calculating VADMs, default is not to calculate VADMS
        -fa AGES: specify er_ages format file with age information
        -crd [s,g,t,b]:   specify coordinate system 
            (s, specimen, g geographic, t, tilt corrected, b, geographic and tilt corrected)
            Default is to skip unoriented specimens
            NB: only the tilt corrected data will appear on the results table, if both g and t are selected.
        -age MIN MAX UNITS:   specify age boundaries and units
        -exc:  use exiting selection criteria (in pmag_criteria.txt file), default is default criteria
        -C: no acceptance criteria
        -aD:  average multiple lines per sample, default is NOT
        -aI:  average multiple specimen intensities per sample, default is NOT
        -aC:  average all components together, default is NOT
        -pol:  calculate polarity averages
        -sam:  save sample level vgps and v[a]dms, default is NOT
        -p: plot directions and look at intensities by site, default is NOT
            -fmt: specify output for saved images, default is svg (only if -p set)
        -lat: use present latitude for calculating VADMs, default is not to calculate VADMs
        -xD: skip directions
        -xI: skip intensities
    OUPUT
        writes pmag_samples, pmag_sites, pmag_results tables
    """
# set defaults
    Comps=[] # list of components
    Names,user=[],""
    Done=[]
    version_num=pmag.get_version()
    args=sys.argv
    DefaultAge=["none"]
    skipdirs,coord,excrit,custom,vgps,average,Iaverage,plotsites,opt=1,0,0,0,0,0,0,0,0
    get_model_lat=0 # this skips VADM calculation altogether, when get_model_lat=1, uses present day
    fmt='svg'
    dir_path="."
    model_lat_file=""
    Caverage=0
    infile='pmag_specimens.txt'
    measfile="magic_measurements.txt"
    sampfile="er_samples.txt"
    sitefile="er_sites.txt"
    agefile="er_ages.txt"
    specout="er_specimens.txt"
    sampout="pmag_samples.txt"
    siteout="pmag_sites.txt"
    resout="pmag_results.txt"
    critout="pmag_criteria.txt"
    sigcutoff,OBJ="",""
    noDir,noInt=0,0
    polarity=0
    coords=[]
    Dcrit,Icrit,nocrit=0,0,0
# get command line stuff
    if "-h" in args:
	print main.__doc__
        sys.exit()
    if '-f' in args:
	ind=args.index("-f")
	measfile=args[ind+1]
    if '-fsp' in args:
	ind=args.index("-fsp")
	infile=args[ind+1]
    if '-fsm' in args:
	ind=args.index("-fsm")
	sampfile=args[ind+1]
    if '-fsi' in args:
	ind=args.index("-fsi")
	sitefile=args[ind+1]
    if "-crd" in args:
	ind=args.index("-crd")
	coord=args[ind+1]
	if coord=='s':coords=['-1']
	if coord=='g':coords=['0']
	if coord=='t':coords=['100']
	if coord=='b':coords=['0','100']
	skipdirs=0
    if "-usr" in args:
        ind=args.index("-usr")
        user=sys.argv[ind+1]
    if "-exc" in args: excrit="1"
    if "-C" in args: 
        Dcrit,Icrit,nocrit=1,1,1
    if "-sam" in args: vgps=1
    if "-pol" in args: polarity=1
    if "-age" in args:
        ind=args.index("-age")
        DefaultAge[0]=args[ind+1]
        DefaultAge.append(args[ind+2])
        DefaultAge.append(args[ind+3])
    if "-aD" in args: average=1
    if "-aI" in args: Iaverage=1
    if "-aC" in args: Caverage=1
    if "-p" in args: 
        plotsites=1
        if "-fmt" in args: 
            ind=args.index("-fmt")
            fmt=args[ind+1]
    if "-fla" in args: 
        ind=args.index("-fla")
        model_lat_file=args[ind+1]
        get_model_lat=2
    if '-lat' in args and get_model_lat==2:
        print "you should set a paleolatitude file OR use present day lat - not both"
        sys.exit()
    if '-lat' in args:get_model_lat=1
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
        infile=dir_path+'/'+infile
        measfile=dir_path+'/'+measfile
        sampfile=dir_path+'/'+sampfile
        sitefile=dir_path+'/'+sitefile
        agefile=dir_path+'/'+agefile
        specout=dir_path+'/'+specout
        sampout=dir_path+'/'+sampout
        siteout=dir_path+'/'+siteout
        resout=dir_path+'/'+resout
        critout=dir_path+'/'+critout
        if model_lat_file!="":model_lat_file=dir_path+'/'+model_lat_file
    if '-xD' in args:noDir=1
    if '-xI' in args:noInt=1
# may still need average, Iaverage,coord, skipdirs, vgps and aveDirs  - will get when necessary
# now down to bidness
    #
    # read in magic_measurements file to get specimen, analyst and instrument names
    #
    master_instlist=[]
    meas_data,file_type=pmag.magic_read(measfile)
    if file_type != 'magic_measurements':
        print file_type
        print file_type,"This is not a valid magic_measurements file "
        sys.exit()
    # read in site data
    SiteNFO,file_type=pmag.magic_read(sitefile)
    if file_type=="bad_file":
        print "Bad er_sites file"
        sys.exit()
    # define the Er_specimen records to create a new er_specimens.txt file
    #
    suniq,ErSpecs=[],[]
    for rec in meas_data:
        if "er_analyst_mail_names" in rec.keys():
            list=rec["er_analyst_mail_names"]
            tmplist=list.split(":")
            for name in tmplist:
                if name not in Names: Names.append(name) 
        if "magic_instrument_codes" in rec.keys():
            list=(rec["magic_instrument_codes"])
            list.strip()
            tmplist=list.split(":")
            for inst in tmplist:
                if inst not in master_instlist:
                    master_instlist.append(inst)
        else:
            rec["magic_instrument_codes"]=""
        if "measurement_standard" not in rec.keys():rec['measurement_standard']='u' # make this an unknown if not specified
        if rec["er_specimen_name"] not in suniq and rec["measurement_standard"]!='s': # exclude standards
            suniq.append(rec["er_specimen_name"])
            ErSpecRec={}
            ErSpecRec["er_citation_names"]="This study"
            ErSpecRec["er_scientist_mail_names"]=user
            ErSpecRec["er_specimen_name"]=rec["er_specimen_name"]
            ErSpecRec["er_sample_name"]=rec["er_sample_name"]
            ErSpecRec["er_site_name"]=rec["er_site_name"]
            ErSpecRec["er_location_name"]=rec["er_location_name"]
    #
    # attach site litho, etc. to specimen if not already there
            kk,GoOn=0,1
            while GoOn==1 and kk<len(SiteNFO):
                found=0
                site=SiteNFO[kk]
                if site["er_site_name"]==ErSpecRec["er_site_name"]:
                    if 'site_class' not in site.keys() or 'site_lithology' not in site.keys() or 'site_type' not in site.keys():
#                        print 'WARNING: class, lithology and type may be missing from er_site.txt file.'
#                        ans=raw_input('[1]Fix the file and try again, [2] continue processing')
#                        if ans!='2': sys.exit()
                        site['site_class']='Not Specified'
                        site['site_lithology']='Not Specified'
                        site['site_type']='Not Specified'
                    found=1
                    if 'specimen_class' not in ErSpecRec.keys():ErSpecRec["specimen_class"]=site['site_class'] 
                    if 'specimen_lithology' not in ErSpecRec.keys():ErSpecRec["specimen_lithology"]=site['site_lithology'] 
                    if 'specimen_type' not in ErSpecRec.keys():ErSpecRec["specimen_type"]=site['site_type'] 
                    GoOn=0
                kk+=1    
            if found==0:
                print ErSpecRec
                raw_input('site record not found for this specimen - return to continue ')
            else:
                ErSpecs.append(ErSpecRec)
    #
    #
    # save the data
    #
    pmag.magic_write(specout,ErSpecs,"er_specimens")
    print " Er_Specimen data (with updated info from site if necessary)  saved in ",specout
    #
    # write out the instrument list
    instout,InstRecs=dir_path+'/magic_instruments.txt',[]
    for inst in master_instlist:
        InstRec={}
        InstRec["magic_instrument_code"]=inst
        InstRecs.append(InstRec)
    if len(InstRecs) >0:
        pmag.magic_write(instout,InstRecs,"magic_instruments")
        print " Instruments data saved in ",instout
    else: 
        print "No instruments found"
    #
    # read in er_samples file
    #
    ErSamps,file_type=pmag.magic_read(sampfile)
    #
    NewErSamps,savenew,height=[],0,0
    for rec in ErSamps:
        if 'sample_height' in rec.keys() and rec['sample_height'].strip()!="": height=1  # there are height data
        if "er_scientist_mail_names" in rec.keys():
            list=rec["er_scientist_mail_names"]
            tmplist=list.split(":")
            for name in tmplist:
                if name not in Names: Names.append(name) 
    # attach site litho, etc. to specimen
        for site in SiteNFO:
            if site["er_site_name"]==rec["er_site_name"]:
                if 'sample_class' not in rec.keys():rec["sample_class"]=site['site_class'] 
                if 'sample_lithology' not in rec.keys():rec["sample_lithology"]=site['site_lithology'] 
                if 'sample_type' not in rec.keys():rec["sample_type"]=site['site_type'] 
        NewErSamps.append(rec)
    #
    #
    # 
    #
    # work on site averages
    #
    for site in SiteNFO:
        if "er_scientist_mail_names" in site.keys():
            list=site["er_scientist_mail_names"]
            tmplist=list.split(":")
    # read in er_age file
    if agefile !="":AgeNFO,file_type=pmag.magic_read(agefile)
    # read in pmag_specimens file
    Data,file_type=pmag.magic_read(infile)
    comment=""
    # identify unique specimen,sample,site names and orientation
    specimens,samples,sites=[],[],[]
    SpecPlanes,SpecDirs,SpecInts,PmagSamps,SiteDirs,SiteInts,PmagSites,PmagCrits,PmagResults=[],[],[],[],[],[],[],[],[]
    NLats,NLons,NormVGPs,RevVGPs,AllVGPs,RLats,RLons=[],[],[],[],[],[],[]
    sig,age_unit=0,""
    first_dup=1
    orient=[]   # geographic coordinates is the default
    for rec in Data:
        if 'specimen_comp_name' not in rec.keys():rec['specimen_comp_name']='A'
        if rec['specimen_comp_name'] not in Comps:Comps.append(rec['specimen_comp_name'])
        if "specimen_tilt_correction" not in rec.keys(): 
            rec["specimen_tilt_correction"]="-1" # assume sample coordinates
        if rec["specimen_tilt_correction"] not in orient: orient.append(rec["specimen_tilt_correction"]) 
        if rec["er_specimen_name"] not in specimens:specimens.append(rec["er_specimen_name"])
        if rec["er_sample_name"] not in samples:samples.append(rec["er_sample_name"])
        if rec["er_site_name"] not in sites:sites.append(rec["er_site_name"])
    if len(orient)==1: coord=orient[0]
    #
    # sort lists
    specimens.sort()
    samples.sort()
    sites.sort()
#
# use existing selection criteria if desired
    if excrit=="1":
        crit_data,file_type=pmag.magic_read(critout)
        print "Acceptance criteria read in from ", critout
    else:
        crit_data=pmag.default_criteria(nocrit)
        if nocrit==0:
            print "Acceptance criteria are defaults"
        else:
            print "No acceptance criteria used "
    for critrec in crit_data:
        if critrec["pmag_criteria_code"]=="DE-SPEC": SpecCrit=critrec
        if critrec["pmag_criteria_code"]=="DE-SAMP": SampCrit=critrec
        if critrec["pmag_criteria_code"]=="IE-SAMP": SampIntCrit=critrec
        if critrec["pmag_criteria_code"]=="IE-SITE": SiteIntCrit=critrec
        if critrec["pmag_criteria_code"]=="DE-SITE": SiteCrit=critrec
        if critrec["pmag_criteria_code"]=="NPOLE": NpoleCrit=critrec
        if critrec["pmag_criteria_code"]=="RPOLE": RpoleCrit=critrec
        if critrec["pmag_criteria_code"]=="IE-SPEC": 
            SpecIntCrit=critrec
            accept_keys=['specimen_int_ptrm_n','specimen_md','specimen_fvds','specimen_b_beta','specimen_dang','specimen_drats','specimen_Z']
            accept={}
            accept['specimen_int_ptrm_n']=2.0
            for critrec in crit_data:
                critrec['er_citation_names']="This study"
                critrec['criteria_definition']="Criteria for selection of specimen direction"
                if critrec["pmag_criteria_code"]=="IE-SPEC":
                    for key in accept_keys:
                        if key not in critrec.keys():
                            accept[key]=-1
                        else:
                            accept[key]=float(critrec[key])
    TmpCrits=[SpecCrit,SpecIntCrit,SampCrit,SiteIntCrit,SiteCrit,NpoleCrit,RpoleCrit]
    #
    # assemble criteria keys
    #
    PmagCrits,critkeys=pmag.fillkeys(TmpCrits)
    pmag.magic_write(critout,PmagCrits,'pmag_criteria')
    print "\n Pmag Criteria stored in ",critout,'\n'
    #
    #
    if skipdirs==0:
        if plotsites==1:
            import pmagplotlib
            EQ={}
            EQ['eqarea']=1
            pmagplotlib.plot_init(EQ['eqarea'],5,5) # define figure 1 as equal area projection
    #
    #now really get down to bidness
    #
    first_result,first_spec,first_samp,first_site=1,1,1,1
    #
    # sort specimen data into directed lines (SpecDirs), planes (SpecPlanes)
    #    or intensity data (SpecInts), only use data meeting criteria
    #
    NewNewErSamps,RestErSamps=[],[]
    if noInt==0:
      print 'Processing specimen intensities in pmag_specimen file'
     
      for spec in specimens:
    #
    # put intensity data in SpecInts, if pass criteria
    #
        for rec in Data:
            if rec['specimen_comp_name'] not in rec.keys():rec['specimen_comp_name']='A'
            if rec['specimen_comp_name'] not in Comps:Comps.append(rec['specimen_comp_name']) # collect all component names
            if rec['er_specimen_name']==spec:
                if "specimen_int" in rec.keys() and rec["specimen_int"]!="":
                    Grade=""
                    if nocrit==0:
                        score,kill=pmag.grade(rec,accept)
                        reason=[]
                        if score==len(accept.keys()):Grade='A'
                        if score==len(accept.keys())-1:Grade='B'
                        if score==len(accept.keys())-2:Grade='C'
                        if score==len(accept.keys())-3:Grade='D'
                        if score<=len(accept.keys())-4:Grade='F'
                        for key in kill.keys():
                            if kill[key]==1:reason.append(key) 
                    if Grade=='A':
                        SpecInts.append(rec) # intensity record
    print 'Processing specimen directions in pmag_specimen file'
    for spec in specimens:
      if noDir==0:
        SpecDir=[]
        for coord in coords:
            SpecCoord,SpecCoords=[],[]
            for rec in Data:
                if rec["er_specimen_name"]==spec and rec['specimen_tilt_correction']==coord:
                    if "er_analyst_mail_names" in rec.keys():  # pick out the mail names
                        list=rec["er_analyst_mail_names"]
                        tmplist=list.split(":")
                        for name in tmplist:
                            if name not in Names: Names.append(name) 
    # direction_type assumed to be directed line if not specified
                    if "specimen_direction_type" not in rec.keys():
                        rec["specimen_direction_type"]='l' 
                    if "magic_instrument_codes" not in rec.keys():
                        rec["magic_instrument_codes"]='' 
                    if "specimen_dec" in rec.keys():
                          if skipdirs!=1:
                            skip=0
                            if "specimen_n" in rec.keys():
                                if nocrit!=1 and rec["specimen_n"]!="":
                                    if "magic_experiment_names" in rec.keys() and "magic_experiment_names" in SpecCrit.keys(): # check for exp to exclude
                                        tmpnames=rec['magic_experiment_names'].split(":")
                                        expnames=[]
                                        for name in tmpnames:expnames.append(name.strip()) 
                                        if SpecCrit['magic_experiment_names'] in expnames: skip=1
                                    if int(rec["specimen_n"])<int(SpecCrit["specimen_n"]):skip=1 
                                    if rec["specimen_mad"]=="" and rec["specimen_alpha95"]!="":
                                        if float(rec["specimen_alpha95"])>float(SpecCrit["specimen_alpha95"]): skip=1
                                    else:
                                        if float(rec["specimen_mad"])>float(SpecCrit["specimen_mad"]): skip=1
                          if skip==0: 
                              SpecCoords.append(rec) # direction record
    #
    # now put them in the master SpecDirs, SpecPlanes, SpecInts lists and re-order er_samples to put so_meth used, first
    #
            addit=0
            if len(SpecCoords)>0 and  'magic_method_codes' in SpecCoords[0].keys():
                meths=SpecCoords[0]['magic_method_codes'].split(':')
                for meth in meths:
                    methstrip=meth.strip()
                    methtype=methstrip.split('-')
                    if 'SO' in methtype:
                        SO_meth=meth.strip()
                        for samprec in NewErSamps:
                            if samprec['er_sample_name']==SpecCoords[0]['er_sample_name'] and 'magic_method_codes' in samprec.keys() and  samprec['er_sample_name'] not in Done:
                                addit=1
                                smeths=samprec['magic_method_codes'].split(':') 
                                methods=[]
                                for smeth in smeths:
                                    methods.append(smeth.strip())
                                if SO_meth in methods:
                                    NewNewErSamps.append(samprec)
                                else:
                                    RestErSamps.append(samprec)
                        Done.append(SpecCoords[0]['er_sample_name'])
        #
    # put directional data in SpecDirs or SpecPlanes, if pass criteria
    #
                if SpecCoords[0]["specimen_direction_type"]=='p':
                    SpecPlanes.append(SpecCoords[0])
                else:
                    SpecDirs.append(SpecCoords[0])
    #
    #  getting stuff into the sample table, averaging if desired
    #
    PmagSamps,SampDirs,SampPlanes,SampInts=[],[],[],[]
    if noDir==0:
        for coord in coords: 
         for comp in Comps:
            for samp in samples:
                PmagSampRec={}
                PmagSampRec['er_citation_names']="This study"
                PmagSampRec["sample_description"]="sample direction"
                PmagSampRec["er_analyst_mail_names"]=user
                PmagSampRec['magic_software_packages']=version_num
                if nocrit!=1:PmagSampRec['pmag_criteria_codes']="DE-SPEC"
    #
    #  fish out all the specimen directed lines for this sample
    #  
                TmpSpec,sdata,SampComps,speclist=[],[],[],""
                for rec in SpecDirs:
                    if rec["er_sample_name"]==samp and rec["specimen_tilt_correction"]==coord:
                        if rec['specimen_comp_name']==comp or Caverage==1: 
                            TmpSpec.append(rec)
                            if comp not in SampComps:SampComps.append(comp)
                        speclist=speclist + rec["er_specimen_name"]+ ":"
                if average==1 and len(TmpSpec)>1: # multiple specimens with best-fit-lines
                    tc=TmpSpec[0]['specimen_tilt_correction']
                    instlist,inst_codes=[],""
                    for rec in TmpSpec:
                        dir=[]
                        dir.append(float(rec["specimen_dec"]))
                        dir.append(float(rec["specimen_inc"]))
                        sdata.append(dir)
                        if "magic_instrument_codes" in rec.keys():
                            list=(rec["magic_instrument_codes"])
                            tmplist=list.split(":")
                            for inst in tmplist:
                                if inst not in instlist: instlist.append(inst)
                        else:
                            rec["magic_instrument_codes"]=""
                        if "magic_method_codes" in rec.keys():
                            methlist=(rec["magic_method_codes"]).strip().split(":")
                        else:methlist=[]
                    fpars=pmag.fisher_mean(sdata)
                    if nocrit!=1:PmagSampRec['pmag_criteria_codes']="DE-SPEC"
                    PmagSampRec["sample_tilt_correction"]=tc
                    PmagSampRec["sample_direction_type"]='l'
                    SampComp=""
                    for c in SampComps:SampComp=SampComp+":"+c
                    PmagSampRec["sample_comp_name"]=SampComp.strip(":")
                    PmagSampRec["sample_dec"]='%7.1f' % (fpars["dec"]) 
                    PmagSampRec["sample_inc"]='%7.1f' % (fpars["inc"])
                    PmagSampRec["sample_n"]='%i '%(fpars["n"])
                    PmagSampRec["sample_n_lines"]='%i '%(fpars["n"])
                    PmagSampRec["sample_n_planes"]='0'
                    PmagSampRec["sample_alpha95"]='%7.1f '%(fpars["alpha95"])
                    speclist=speclist[:-1]
                    PmagSampRec["er_specimen_names"]=speclist
                    for inst in instlist:
                        tmpinst=inst_codes[:]
                        tmpinst.split(":")
                        if inst not in tmpinst: inst_codes=inst_codes+inst+":"
                        inst_codes=inst_codes[:-1]
                    methlist.append("DE-FM")
                    methcodes=""
                    if PmagSampRec['sample_tilt_correction']=='0':methcodes="DA-DIR-GEO"
                    if PmagSampRec['sample_tilt_correction']=='100':methcodes="DA-DIR-TILT"
                    for meth in methlist:
                        methcodes=methcodes+meth+":"
                    PmagSampRec["magic_method_codes"]=methcodes[:-1]
                    PmagSampRec["magic_instrument_codes"]=inst_codes
        #
        # if not averaging,  just copy over everything
        #
                elif len(TmpSpec)==1:
                    spec=TmpSpec[0]
                    PmagSampRec["er_specimen_names"]=spec["er_specimen_name"]
                    PmagSampRec["sample_direction_type"]='l'
                    PmagSampRec["sample_tilt_correction"]=spec['specimen_tilt_correction']
                    PmagSampRec["sample_comp_name"]=spec['specimen_comp_name']
                    PmagSampRec["sample_dec"]=spec["specimen_dec"]
                    PmagSampRec["sample_inc"]=spec["specimen_inc"]
                    PmagSampRec["sample_n"]='1'
                    PmagSampRec["sample_n_lines"]='1'
                    PmagSampRec["sample_n_planes"]='0'
                    PmagSampRec["sample_alpha95"]=""
                    PmagSampRec['magic_method_codes']=spec["magic_method_codes"]
                    PmagSampRec['magic_software_packages']=version_num
                    PmagSampRec["magic_instrument_codes"]=spec["magic_instrument_codes"]
                if len(TmpSpec)>0:
                    PmagSampRec["er_location_name"]=TmpSpec[0]["er_location_name"]
                    PmagSampRec["er_site_name"]=TmpSpec[0]["er_site_name"]
                    PmagSampRec["er_sample_name"]=TmpSpec[0]["er_sample_name"]
                    if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
                    SampDirs.append(PmagSampRec)
                    PmagSamps.append(PmagSampRec)
    #
    # now do the planes
                if len(SpecPlanes) !=0: # now do all best-fit planes
                    for spec in SpecPlanes:
                        if spec['specimen_tilt_correction']==coord and spec['specimen_comp_name']==comp:
                            PmagSampRec={}
                            PmagSampRec['magic_instrument_codes']=spec["magic_instrument_codes"]
                            PmagSampRec['er_citation_names']="This study"
                            PmagSampRec["er_analyst_mail_names"]=user
                            PmagSampRec["sample_description"]="sample direction"
                            PmagSampRec["er_specimen_names"]=spec["er_specimen_name"]
                            PmagSampRec["er_sample_name"]=spec["er_sample_name"]
                            PmagSampRec["er_site_name"]=spec["er_site_name"]
                            PmagSampRec["er_location_name"]=spec["er_location_name"]
                            if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
                            PmagSampRec["sample_n"]='1'
                            PmagSampRec['sample_n_lines']='0'
                            PmagSampRec["sample_n_planes"]='1'
                            PmagSampRec["sample_dec"]=spec["specimen_dec"]
                            PmagSampRec["sample_inc"]=spec["specimen_inc"]
                            PmagSampRec["sample_tilt_correction"]=spec["specimen_tilt_correction"]
                            PmagSampRec["sample_comp_name"]=spec["specimen_comp_name"]
                            PmagSampRec['magic_method_codes']=spec["magic_method_codes"]
                            PmagSampRec["sample_direction_type"]='p'
                            PmagSampRec['magic_software_packages']=version_num
                    SampDirs.append(PmagSampRec)
                    PmagSamps.append(PmagSampRec)
    if len(SpecInts) !=0: # now do all the intensities
      if get_model_lat==0:get_model_lat=1 # remember to ask about model versus geographic latitudes for VADM calculation
      if Iaverage==0: # don't average by sample - just by site
        for spec in SpecInts:
            PmagSampRec={}
            PmagSampRec["sample_description"]="sample intensity"
            PmagSampRec["sample_direction_type"]=""
            PmagSampRec['magic_instrument_codes']=spec["magic_instrument_codes"]
            PmagSampRec['magic_method_codes']=spec["magic_method_codes"]
            PmagSampRec['er_citation_names']="This study"
            PmagSampRec["er_analyst_mail_names"]=user
            PmagSampRec["sample_description"]="sample intensity"
            PmagSampRec["er_specimen_names"]=spec["er_specimen_name"]
            PmagSampRec["er_sample_name"]=spec["er_sample_name"]
            PmagSampRec["er_site_name"]=spec["er_site_name"]
            PmagSampRec["er_location_name"]=spec["er_location_name"]
            if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
            PmagSampRec["sample_int_n"]='1'
            PmagSampRec["sample_int"]=spec["specimen_int"]
            PmagSampRec["sample_int_sigma"]='0'
            PmagSampRec["sample_int_sigma_perc"]='0'
            PmagSampRec["sample_dec"]=""
            PmagSampRec["sample_inc"]=""
            if nocrit!=1:PmagSampRec['pmag_criteria_codes']="IE-SPEC"
            PmagSampRec['magic_software_packages']=version_num
            SampInts.append(PmagSampRec)
            PmagSamps.append(PmagSampRec) 
      else: # averageing multiple specimens per sample
        for samp in samples:
            print "averaging intensities for sample: ",samp
            methcodes=""
            speclist=""
            PmagSampRec={}
            PmagSampRec["sample_description"]="sample intensity"
            PmagSampRec["sample_direction_type"]=""
    #
    # collect all specimen data  for this sample 
    #
            data,instlist,methlist=[],[],[]
            for rec in SpecInts:  # collect all the specimens for this sample
                if rec["er_sample_name"]==samp:
                    PmagSampRec['er_site_name']=rec["er_site_name"]
                    PmagSampRec['er_sample_name']=rec["er_sample_name"]
                    er_location_name=rec["er_location_name"]
                    if "magic_instruments_codes" not in rec.keys():rec["magic_instrument_codes"]=""
                    instlist.append(rec["magic_instrument_codes"])
                    methlist=rec["magic_method_codes"].split(':')
                    if agefile != "":   PmagSampRec=pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_", AgeNFO,DefaultAge)
                    if nocrit!=1:
                        PmagSampRec['pmag_criteria_codes']="IE-SPEC"
                        
                        speclist=speclist+rec["er_specimen_name"]+":"
                        data.append(float(rec["specimen_int"])) 
            if len(data)!=0: # if there are some
                PmagSampRec["er_location_name"]=er_location_name
                PmagSampRec["er_citation_names"]="This study"
                PmagSampRec["er_analyst_mail_names"]=user
                if agefile != "":   PmagSampRec=pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_", AgeNFO,DefaultAge)
                inst_codes=""
                for inst in instlist:
                    tmpinst=inst_codes[:]
                    tmpinst.split(":")
                    if inst not in tmpinst: inst_codes=inst_codes+inst+":"
                inst_codes=inst_codes[:-1]
                PmagSampRec['magic_instrument_codes']=inst_codes
                speclist=speclist[:-1]
                PmagSampRec["er_specimen_names"]=speclist
                if len(data) >1: # if more than one, average
                    b,sig=pmag.gausspars(data) 
                    PmagSampRec["sample_int"]='%8.3e '% (b)
                    PmagSampRec["sample_int_sigma"]='%8.3e '% (sig)
                    sigperc=100.*sig/b
                    PmagSampRec["sample_int_sigma_perc"]='%8.3e '%(sigperc)
                    PmagSampRec["sample_int_n"]='%i '% (len(data))
                if len(data)==1: # if only one, just copy over specimen data
                    b=data[0]
                    PmagSampRec["sample_int"]='%8.3e '% (data[0])
                    PmagSampRec["sample_int_n"]='1'
                    PmagSampRec["sample_int_sigma"]='0'
                methcode=""
                for meth in methlist:
                    methcode=methcode+meth.strip()+":"
                PmagSampRec["magic_method_codes"]=methcode[:-1]
                PmagSampRec['magic_software_packages']=version_num
                SampInts.append(PmagSampRec) #  collect the data into SampInts
                PmagSamps.append(PmagSampRec) #  and samps
    #
    # collect keys from TmpSamps direction and intensity records, make a coherent set of keys
    #
    TmpSamps=PmagSamps[:]
    PmagSamps,sampkeys=pmag.fillkeys(TmpSamps)
    #
    if len(PmagSamps)==0:
        print "no data at the sample level"
        sys.exit()
    pmag.magic_write(sampout,PmagSamps,"pmag_samples")
    #
    # save the data
    #
    print " Sample data saved in ",sampout
    if len(Done)!=0:
        for ersamp in RestErSamps:
            NewNewErSamps.append(ersamp)  # put all the unused sample orientation records at end
        for ersamp in NewErSamps:
            if ersamp['er_sample_name'] not in Done:
                NewNewErSamps.append(ersamp)  # put all the unused sample orientation records at end
        NewErSamps=NewNewErSamps # overwrite NewErSamps 
    if len(NewErSamps)>0:
        pmag.magic_write(sampfile,NewErSamps,"er_samples")
        print " Sample data with inherited site information and re-ordered orientation info saved in ",sampout
    #
    # 
    #
    # work on site averages
    #
    for site in SiteNFO:
        if "er_scientist_mail_names" in site.keys():
            list=site["er_scientist_mail_names"]
            tmplist=list.split(":")
            for name in tmplist:
                if name not in Names: Names.append(name) 
    #
    # create the pmag_site table by averaging samples.
    #
    # do directions first
    #
    print "\n Processing directions \n"
    for site in sites:
      for coord in coords:
       for comp in Comps:
        samplist,speclist,complist="","",[]
        PmagSiteRec,PmagResRec={},{}
        PmagSiteRec["site_description"]=comment
        PmagResRec["result_description"]=comment
        PmagSiteRec['er_site_name']=site
    #
    #
        if average==1: PmagSiteRec['pmag_criteria_codes']="DE-SAMP"
        if average==0: PmagSiteRec['pmag_criteria_codes']="DE-SPEC"
        if agefile != "": PmagSiteRec= pmag.get_age(PmagSiteRec,"er_site_name","site_inferred_",AgeNFO,DefaultAge)
    #
    # collect all directional data  for this site 
    #
        data,instlist=[],[]
        for rec in SampDirs:
    #
    #
            if rec["er_site_name"]==site and rec['sample_tilt_correction']==coord:
              if rec['sample_comp_name']==comp or Caverage==1:
                if "magic_instrument_codes" in rec.keys():instlist.append(rec["magic_instrument_codes"])
                if "sample_alpha95" not in rec.keys(): rec["sample_alpha95"]=""
                if rec['sample_tilt_correction']==coord:
                    if nocrit==1 or (rec["sample_alpha95"] == "" or float(rec["sample_alpha95"]) <= float(SampCrit["sample_alpha95"])):
                        er_location_name=rec["er_location_name"]
                        LnpRec={}
                        LnpRec["magic_method_codes"]=rec["magic_method_codes"]
                        LnpRec["sample_direction_type"]=rec["sample_direction_type"]
                        LnpRec["er_specimen_names"]=rec["er_specimen_names"]
                        LnpRec["sample_n"]=rec["sample_n"]
                        LnpRec["sample_alpha95"]=rec["sample_alpha95"]
                        samplist=samplist+rec["er_sample_name"]+":"
                        speclist=speclist+rec["er_specimen_names"]+":"
                        LnpRec["dec"]= float(rec["sample_dec"])
                        LnpRec["inc"]= float(rec["sample_inc"])
                        LnpRec["tilt_correction"]=coord
                        LnpRec["comp_name"]=comp
                        if comp not in complist:complist.append(comp)
                        data.append(LnpRec)
        for rec in SampPlanes:
    #
            if rec["er_site_name"]==site and rec['sample_tilt_correction']==coord:
              if rec['sample_comp_name']==comp or Caverage==1:
                if "magic_instrument_codes" in rec.keys():instlist.append(rec["magic_instrument_codes"])
                if "sample_alpha95" not in rec.keys(): rec["sample_alpha95"]=""
                if nocrit==1 or rec["sample_alpha95"] == "" or float(rec["sample_alpha95"]) <= float(SampCrit["sample_alpha95"]):
                        er_location_name=rec["er_location_name"]
                        LnpRec={}
                        LnpRec["magic_method_codes"]=rec["magic_method_codes"]
                        LnpRec["sample_direction_type"]='p'
                        LnpRec["er_specimen_names"]=rec["er_specimen_names"]
                        LnpRec["sample_n"]=rec["sample_n"]
                        LnpRec["sample_alpha95"]=rec["sample_alpha95"]
                        samplist=samplist+rec["er_sample_name"]+":"
                        speclist=speclist+rec["er_specimen_names"]+":"
                        LnpRec["dec"]= float(rec["sample_dec"])
                        LnpRec["inc"]= float(rec["sample_inc"])
                        LnpRec["tilt_correction"]=coord
                        LnpRec["comp_name"]=comp
                        if comp not in complist:complist.append(comp)
                        data.append(LnpRec)
    #
    #
    # get site means and vgps, if enough samples
    #
    # do Fisher averaging (using McFadden & McElhinny '88 if planes)
        if len(data) >2:
            PmagSiteRec["er_location_name"]=er_location_name
            PmagSiteRec["er_citation_names"]="This study"
            PmagSiteRec['er_analyst_mail_names']=user
            inst_codes=""
            for inst in instlist:
                tmpinst=inst_codes[:]
                tmpinst.split(":")
                if inst not in tmpinst: inst_codes=inst_codes+inst+":"
            inst_codes=inst_codes[:-1]
            PmagSiteRec['magic_instrument_codes']=inst_codes
            fpars=pmag.dolnp(data,'sample_direction_type') 
            samplist=samplist[:-1]
            speclist=speclist[:-1]
            if average==1: PmagSiteRec["er_sample_names"]=samplist
            if average==0: PmagSiteRec["er_specimen_names"]=speclist
            PmagSiteRec["site_dec"]=fpars["dec"]
            PmagSiteRec["site_inc"]=(fpars["inc"])
            PmagSiteRec["site_tilt_correction"]=coord
            SiteComp=complist[0]
            for c in complist[1:]: SiteComp=SiteComp+":"+c
            PmagSiteRec["site_comp_name"]=SiteComp.strip(':')
            PmagSiteRec["site_n"]=(fpars["n_total"])
            PmagSiteRec["site_n_lines"]=fpars["n_lines"]
            PmagSiteRec["site_n_planes"]=fpars["n_planes"]
            PmagSiteRec["site_r"]=fpars["R"]
            PmagSiteRec["site_k"]=fpars["K"]
            PmagSiteRec["site_alpha95"]=fpars["alpha95"]
            if int(PmagSiteRec["site_n_planes"])>0: 
                PmagSiteRec["magic_method_codes"]="DE-FM-LP"
            elif int(PmagSiteRec["site_n_lines"])>2:
                PmagSiteRec["magic_method_codes"]="DE-FM"
    #
    #  calculate the  site VGPs
    #
    #
    # find location
    #
            for rec in SiteNFO:
                if rec["er_site_name"]==site:
                    lat=float(rec["site_lat"])      
                    lon=float(rec["site_lon"])      
                    PmagSiteRec["site_lat"]='%7.1f'%(lat) # just for convenience - won't be imported
                    PmagSiteRec["site_lon"]='%7.1f'%(lon) # just for convenience - won't be imported
                    if 'site_height' in rec.keys():PmagResRec["average_height"]=rec["site_height"]     
    # collect relevent site information
    #
    #  calculate VGP lat/long, stick in results table
    #
            dec=float(PmagSiteRec["site_dec"])
            inc=float(PmagSiteRec["site_inc"])
            a95=float(PmagSiteRec["site_alpha95"])
            plong,plat,dp,dm=pmag.dia_vgp(dec,inc,a95,lat,lon)
            if coord=='-1':C=' (spec coord) '
            if coord=='0':C=' (geog. coord) '
            if coord=='100':C=' (strat. coord) '
            PmagResRec["pmag_result_name"]="VGP: Site "+C+SiteComp+' comp: '+PmagSiteRec["er_site_name"]
            PmagResRec["result_description"]="Site VGP" +SiteComp+' comp: '+C
            PmagResRec['er_site_names']=site
            PmagResRec['pmag_criteria_codes']=PmagSiteRec["pmag_criteria_codes"]
            PmagResRec['er_citation_names']='This study'
            PmagResRec['er_analyst_mail_names']=user
            PmagResRec["er_location_names"]=PmagSiteRec["er_location_name"]
            PmagResRec["er_site_names"]=PmagSiteRec["er_site_name"]
            if average==1:PmagResRec["er_sample_names"]=PmagSiteRec["er_sample_names"]
            if average==0:PmagResRec["er_specimen_names"]=PmagSiteRec["er_specimen_names"]
            PmagResRec["tilt_correction"]=coord
            PmagResRec["pole_comp_name"]=SiteComp
            PmagResRec["average_dec"]=PmagSiteRec["site_dec"]
            PmagResRec["average_inc"]=PmagSiteRec["site_inc"]
            PmagResRec["average_alpha95"]=PmagSiteRec["site_alpha95"]
            PmagResRec["average_n"]=PmagSiteRec["site_n"]
            PmagResRec["average_nn"]=PmagSiteRec["site_n"]
            PmagResRec["average_n_lines"]=PmagSiteRec["site_n_lines"]
            PmagResRec["average_n_planes"]=PmagSiteRec["site_n_planes"]
            PmagResRec["vgp_n"]=PmagSiteRec["site_n"]
            PmagResRec["average_k"]=PmagSiteRec["site_k"]
            PmagResRec["average_r"]=PmagSiteRec["site_r"]
            PmagResRec["average_lat"]='%10.4f ' %(lat)
            PmagResRec["average_lon"]='%10.4f ' %(lon)
            if agefile != "": PmagResRec= pmag.get_age(PmagResRec,"er_site_names","average_",AgeNFO,DefaultAge)
            PmagResRec["vgp_lat"]='%7.1f ' % (plat)
    #  site_vgp stuff  for later, won't be imported into data base
            PmagSiteRec["site_vgp_lat"]='%7.1f ' % (plat)
            PmagSiteRec["site_vgp_lon"]='%7.1f ' % (plong)
            PmagResRec["vgp_lon"]='%7.1f ' % (plong)
            PmagResRec["vgp_dp"]='%7.1f ' % (dp)
            PmagResRec["vgp_dm"]='%7.1f ' % (dm)
            PmagResRec["magic_method_codes"]= PmagSiteRec["magic_method_codes"]+":"+ "DE-DI"
            if coord=='0':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-GEO"
            if coord=='100':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-TILT"
            PmagResRec["pmag_criteria_codes"]= "DE-SITE"
            if int(PmagSiteRec["site_n"]) >= int(SiteCrit['site_n']):
                if int(PmagSiteRec["site_n_lines"]) >= int(SiteCrit['site_n_lines']):
                    if float(PmagSiteRec["site_k"]) >= float(SiteCrit["site_k"]): 
                        if float(PmagSiteRec["site_alpha95"]) <= float(SiteCrit["site_alpha95"]): 
                            PmagResRec['data_type']='i'
                            PmagResRec['magic_software_packages']=version_num
                            if coord==coords[-1]: PmagResults.append(PmagResRec) # only take last coordinat for results table
                            PmagSiteRec["site_description"]+=" Direction included in Pmag_Results."
    # assign polarity n: colat <45 away from north pole, t:45<colat<135; r: 135<colat - if polarity calculation turned on
    #
            PmagSiteRec['site_polarity']=""
            if polarity==1:
                angle=pmag.angle([0,0],[0,(90-plat)])
                if angle <= 55.: PmagSiteRec["site_polarity"]='n'
                if angle > 55. and angle < 125.: PmagSiteRec["site_polarity"]='t'
                if angle >= 125.: PmagSiteRec["site_polarity"]='r'
    #  with this site directions, plot the site mean data if desired
            PmagSiteRec['magic_software_packages']=version_num
            SiteDirs.append(PmagSiteRec)
            PmagSites.append(PmagSiteRec)
            if plotsites==1:
                print 'Site mean data: '
                print '   dec    inc n_lines n_planes kappa R alpha_95 comp coord'
                print fpars['dec'],fpars['inc'],fpars['n_lines'],fpars['n_planes'],fpars['K'],fpars['R'],fpars['alpha95'],SiteComp,coord
                print 'sample, dec, inc, n_specs/a95,| method codes '
                for i  in range(len(data)):
                    print '%s: %7.1f %7.1f %s / %s | %s' % (data[i]['er_specimen_names'], data[i]['dec'], data[i]['inc'], data[i]['sample_n'], data[i]['sample_alpha95'], data[i]['magic_method_codes']) 
                pmagplotlib.plotLNP(EQ['eqarea'],site,data,fpars,'sample_direction_type')
                plot=raw_input("s[a]ve plot, [q]uit or <return> to continue:   ")
                if plot=='q':
                     print "CUL8R"
                     sys.exit()
                if plot=='a':
                    files={}
                    for key in EQ.keys():
                        files[key]=site+'_'+key+'.'+fmt
                    pmagplotlib.saveP(EQ,files)

    
    # work on intensity averages by site now
    #
    print "\n Processing intensities by site \n"
    ans=""
    if model_lat_file!="":
        if model_lat_file=="":
            model_lat_file=raw_input(" Enter name of model latitude file: [model_lat.txt] ")
            if model_lat_file=="":model_lat_file="model_lat.txt"
        lat_type="IE-MLAT"
        get_model_lat=2
        mlat=open(model_lat_file,'rU')
        ModelLats=[]
        for line in mlat.readlines():
            ModelLat={}
            tmp=line.split()
            ModelLat["er_site_name"]=tmp[0]
            ModelLat["site_model_lat"]=tmp[1]
            ModelLats.append(ModelLat)
    for site in sites:
        methcodes=""
        speclist,samplist="",""
        PmagSiteRec,PmagResRec={},{}
        PmagSiteRec["site_description"]=comment
        PmagResRec["result_description"]=comment
        PmagSiteRec['er_site_name']=site
        PmagResRec["pmag_result_name"]="V[A]DM: Site "+site
        PmagResRec["result_description"]="Site V[A]DM"
        PmagResRec['er_site_names']=site
        if agefile != "":   
           PmagSiteRec=pmag.get_age(PmagSiteRec,"er_site_name","site_inferred_", AgeNFO,DefaultAge)
           PmagResRec=pmag.get_age(PmagResRec,"er_site_names","average_", AgeNFO,DefaultAge)
        for rec in SiteNFO:
            if rec["er_site_name"]==PmagResRec["er_site_names"]:
                PmagResRec["average_lat"]=rec["site_lat"]     
                PmagResRec["average_lon"]=rec["site_lon"]     
                if 'site_height' in rec.keys():PmagResRec["average_height"]=rec["site_height"]     
        PmagSiteRec['pmag_criteria_codes']="IE-SPEC"
        PmagResRec['pmag_criteria_codes']="IE-SPEC"
    #
    # collect all sample data  for this site 
    #
        data,instlist,methlist=[],[],[]
        for rec in SampInts:
            if rec["er_site_name"]==site:
                er_location_name=rec["er_location_name"]
                speclist=speclist+rec["er_specimen_names"]+":"
                samplist=samplist+rec["er_sample_name"]+":"
                data.append(float(rec["sample_int"])) 
                if plotsites==1:print rec['er_sample_name'],' %7.1f'%(1e6*float(rec['sample_int']))
                instlist.append(rec["magic_instrument_codes"])
                methlist=rec["magic_method_codes"].strip().split(":")
                ResMethlist=methlist[:]
        if len(data)!=0:
            PmagSiteRec["er_location_name"]=er_location_name
            PmagSiteRec["er_citation_names"]="This study"
            PmagResRec["er_location_names"]=er_location_name
            PmagResRec["er_citation_names"]="This study"
            PmagSiteRec["er_analyst_mail_names"]=user
            PmagResRec["er_analyst_mail_names"]=user
            inst_codes=""
            for inst in instlist:
                tmpinst=inst_codes[:]
                tmpinst.split(":")
                if inst not in tmpinst: inst_codes=inst_codes+inst+":"
            inst_codes=inst_codes[:-1]
            PmagSiteRec['magic_instrument_codes']=inst_codes
            speclist=speclist[:-1]
            samplist=samplist[:-1]
            PmagSiteRec["er_specimen_names"]=speclist
            PmagResRec["er_specimen_names"]=speclist
            PmagSiteRec["er_sample_names"]=samplist
            PmagResRec["er_sample_names"]=samplist
            if len(data) >1: # average by site
                b,sig=pmag.gausspars(data) 
                PmagSiteRec["site_int"]='%8.3e '% (b)
                PmagSiteRec["site_int_sigma"]='%8.3e '% (sig)
                sigperc=100*sig/b
                PmagSiteRec["site_int_sigma_perc"]='%8.3e '%(sigperc)
                PmagSiteRec["site_int_n"]='%i '% (len(data))
            elif len(data)==1: # just copy over sample data
                b=data[0]
                sig=0
                PmagSiteRec["site_int"]='%8.3e '% (data[0])
                PmagSiteRec["site_int_n"]='1'
                PmagSiteRec["site_int_sigma"]='0'
                PmagSiteRec["site_int_sigma_perc"]='0'
    #
    #  calculate VDM  and VADM (if inc for VDM and lat for VADM are available)
    #
            for rec in SiteDirs:
                if rec["er_site_name"]==site:
                    if rec["site_tilt_correction"]==coord: # samples are oriented
                        inc= float(rec["site_inc"])
                        mlat=pmag.magnetic_lat(inc)
                        vdm=pmag.b_vdm(b,mlat)
                        PmagResRec["vdm"]='%8.3e '% (vdm)
                        PmagSiteRec["site_vdm"]='%8.3e'%(vdm)   # not imported - just for convenience
                        if sig!=0:
                             vdm_sig=pmag.b_vdm(sig,mlat)
                             PmagResRec["vdm_sigma"]='%8.3e '% (vdm_sig)
                        else:
                             PmagResRec["vdm_sigma"]=""
                        PmagResRec["vdm_n"]=PmagSiteRec["site_int_n"]
    #
    # calculate VADM if using lat or model lat
    #
            if get_model_lat!=0: # calculate VADM
                if get_model_lat==1: # use site lat.
                    lat=float(PmagResRec["average_lat"])      
                    ResMethlist.append("")
                if get_model_lat==2:
                    found=0
                    for latrec in ModelLats:
                        if latrec["er_site_name"]==site:
                            lat=float(latrec["site_model_lat"])
                            PmagResRec["model_lat"]='%7.1f ' % (lat)
                            found=1
                    ResMethlist.append(lat_type)
                    if found==0:
                        print "lat not found for: ",site
                        raw_input()
                        sys.exit()
                b=float(PmagSiteRec["site_int"])
                PmagResRec["average_int"]=PmagSiteRec["site_int"]
                PmagResRec["average_int_n"]=PmagSiteRec["site_int_n"]
                PmagResRec["average_int_sigma"]=PmagSiteRec["site_int_sigma"]
                PmagResRec["average_int_sigma_perc"]=PmagSiteRec["site_int_sigma_perc"]
                vadm=pmag.b_vdm(b,lat) 
                PmagResRec["vadm"]='%8.3e '% (vadm)
                PmagSiteRec["site_vadm"]='%8.3e'%(vadm) # not imported - just for convenience
                PmagResRec["vadm_n"]=PmagSiteRec["site_int_n"]
                if sig !=0:
                     vadm_sig=pmag.b_vdm(sig,lat)
                     PmagResRec["vadm_sigma"]='%8.3e '% (vadm_sig)
                else:
                     PmagResRec["vadm_sigma"]=""
            methcode=""
            for meth in ResMethlist:
                if meth!="" and meth!="":methcode=methcode+meth+":"
            PmagResRec["magic_method_codes"]=methcode[:-1]
            PmagResRec["pmag_criteria_codes"]="IE-SITE"
            methcode=""
            for meth in methlist:
                if meth!="" and meth!=" ":methcode=methcode+meth+":"
            PmagSiteRec["magic_method_codes"]=methcode[:-1]
            PmagSiteRec['magic_software_packages']=version_num
            PmagSites.append(PmagSiteRec)
            if int(PmagSiteRec["site_int_n"])>= int(SiteIntCrit["site_int_n"]):
               if float(PmagSiteRec["site_int_sigma"])<= float(SiteIntCrit["site_int_sigma"]) or float(PmagSiteRec["site_int_sigma_perc"])<= float(SiteIntCrit["site_int_sigma_perc"]): 
                   PmagResRec['data_type']='i'
                   if plotsites==1:
                       print "Mean Site intensity:"
                       print "Site name, specimens, B, sigma, sigma%  N, methods"
                       print PmagResRec['er_site_names'],PmagResRec['er_specimen_names'],': %7.2f %7.2f %7.1f %s %s'%(1e6*float(PmagResRec['average_int']),1e6*float(PmagResRec['average_int_sigma']),float(PmagResRec['average_int_sigma_perc']),PmagResRec['average_int_n'],PmagResRec['magic_method_codes'])
                       raw_input()
                   PmagResRec['magic_software_packages']=version_num
                   PmagResults.append(PmagResRec)
                   PmagSiteRec["site_description"]+=" Intensity included in Pmag_Results."
                   PmagSiteRec['magic_software_packages']=version_num
            SiteInts.append(PmagSiteRec)
    #
    # save the Site data
    #
    TmpSites=PmagSites[:]
    PmagSites,sitekeys=pmag.fillkeys(TmpSites)
    pmag.magic_write(siteout,PmagSites,"pmag_sites")
    print " Site data saved in ",siteout
    # collect all the VGPs for each polarity.
    ndirs,rdirs=[],[]
    if polarity==1:
      print "\n Now collecting averages by polarity"
      for PmagSiteRec in SiteDirs:
        skip=0
        if "site_n" not in PmagSiteRec: PmagSiteRec["site_n"]=""
        if nocrit!=1:
            if int(PmagSiteRec["site_n"]) < int(SiteCrit["site_n"]) or int(PmagSiteRec["site_n_lines"]) <int(SiteCrit["site_n_lines"]) or  float(PmagSiteRec["site_k"]) < float(SiteCrit["site_k"]) or float(PmagSiteRec["site_alpha95"]) > float(SiteCrit["site_alpha95"]): skip=1
        if skip ==0:
            if PmagSiteRec["site_polarity"]=='n':
                NormVGPs.append(PmagSiteRec)
                AllVGPs.append(PmagSiteRec)
            if PmagSiteRec["site_polarity"]=='r':
                RevVGPs.append(PmagSiteRec)
                alat=-float(PmagSiteRec["site_vgp_lat"])
                along=float(PmagSiteRec["site_vgp_lon"])-180.
                if along <0:along=along+360.
                TmpSiteRec=PmagSiteRec.copy()
                TmpSiteRec["site_vgp_lat"]='%7.1f ' % (alat)
                TmpSiteRec["site_vgp_lon"]='%7.1f ' % (along)
                ainc=-float(PmagSiteRec["site_inc"])
                adec=float(PmagSiteRec["site_dec"])-180.
                if adec<0:adec=adec+360.
                TmpSiteRec["site_dec"]='%7.1f ' % (adec)
                TmpSiteRec["site_inc"]='%7.1f ' % (ainc)
                AllVGPs.append(TmpSiteRec)
    #
    # get average normal pole
    #
      Nages,npoles,Sites,dir=[],[],[],[]
      if len(NormVGPs) >3:
        print 'doing Normal VGPs'
        PmagResRec={}
        PmagResRec["result_description"]=comment
        PmagResRec["pmag_result_name"]="Normal Pole"
        PmagResRec["result_description"]="Mean of normal directions"
        for SiteRec in NormVGPs:
            Sites.append(SiteRec["er_site_name"])
            pole=[ float(SiteRec["site_vgp_lon"]),float(SiteRec["site_vgp_lat"])]
            npoles.append(pole)
            dir=[ float(SiteRec["site_dec"]),float(SiteRec["site_inc"])]
            ndirs.append(dir)
            if agefile != "": rec=pmag.get_age(SiteRec,'er_site_name','site_inferred_',AgeNFO,DefaultAge)
            if "site_inferred_age" in rec.keys() and rec["site_inferred_age"]!="":
                Nages.append([float(rec["site_inferred_age"]),rec["site_inferred_age_unit"]])
                if age_unit=="":age_unit=rec["site_inferred_age_unit"] 
            try:
                NLats.append(float(SiteRec["site_lat"]))
            except:
                print 'problem with site latitude ',SiteRec["er_site_name"],SiteRec["site_lat"]
                sys.exit()
            try:
                NLons.append(float(SiteRec["site_lon"]))
            except:
                print 'problem with site longitude ',SiteRec["er_site_name"],SiteRec["site_lon"]
                sys.exit()
        PmagResRec["er_location_names"]=NormVGPs[0]["er_location_name"]
        PmagResRec["er_citation_names"]="This study"
        PmagResRec["er_analyst_mail_names"]=user
        sitestring=""
        for site in Sites:
            sitestring=sitestring+site + ":"
        PmagResRec["er_site_names"]=sitestring[:-1]
        PmagResRec["percent_reversed"]="0"
        npars=pmag.fisher_mean(npoles) 
        PmagResRec["vgp_lon"]='%7.1f '% (npars["dec"])
        PmagResRec["vgp_lat"]='%7.1f '% (npars["inc"])
        PmagResRec["vgp_n"]='%i '%(npars["n"])
        PmagResRec["vgp_alpha95"]='%7.1f '% (npars["alpha95"])
        PmagResRec["magic_method_codes"]="DE-VGP"
        PmagResRec["pmag_criteria_codes"]="DE-SITE:NPOLE"
        fpars=pmag.fisher_mean(ndirs)
        PmagResRec["average_dec"]='%7.1f '% (fpars["dec"])
        PmagResRec["average_inc"]='%7.1f '% (fpars["inc"])
        PmagResRec["average_n"]='%i '%(fpars["n"])
        PmagResRec["average_r"]='%5.4f '%(fpars["r"])
        PmagResRec["average_k"]='%7.1f '% (fpars["k"])
        PmagResRec["average_alpha95"]='%7.1f '% (fpars["alpha95"])
        m,x=pmag.gausspars(NLats)
        PmagResRec["average_lat"]='%10.4f ' %(m)
        PmagResRec["average_lat_sigma"]='%10.4f ' %(x)
        m,x=pmag.gausspars(NLons)
        PmagResRec["average_lon"]='%10.4f ' %(m)
        PmagResRec["average_lon_sigma"]='%10.4f ' %(x)
        if len(Nages)>1:
            Adjages,age_unit=pmag.adjust_ages(Nages)
            m,x=pmag.gausspars(Adjages)
            PmagResRec["average_age"]='%10.4e ' %(m)
            PmagResRec["average_age_sigma"]='%10.4e ' %(x)
            PmagResRec["average_age_unit"]=age_unit
        elif len(Nages)==1:
            PmagResRec["average_age"]='%10.4e ' %(Nages[0][0])
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=Nages[0][1]
        else:
            PmagResRec["average_age"]=""
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=""
        PmagResRec['data_type']='a'    
        PmagResRec['magic_software_packages']=version_num
        PmagResults.append(PmagResRec)
    #
    # now get average reverse pole
    #
      Rages,rpoles,Sites,dir,adirs=[],[],[],[],[]
      if len(RevVGPs) > 3:
        PmagResRec={}
        PmagResRec["result_description"]=comment
        angle=""
        PmagResRec["pmag_result_name"]="Reverse pole"
        PmagResRec["result_description"]="Mean of reverse directions"
        for SiteRec in RevVGPs:
            Sites.append(SiteRec["er_site_name"])
            pole=[ float(SiteRec["site_vgp_lon"]),float(SiteRec["site_vgp_lat"])]
            rpoles.append(pole)
            dir=[ float(SiteRec["site_dec"]),float(SiteRec["site_inc"])]
            rdirs.append(dir)
            dir=[float(SiteRec["site_dec"])-180.,-float(SiteRec["site_inc"])]
            adirs.append(dir)
            if agefile != "": rec=pmag.get_age(SiteRec,'er_site_name','site_inferred_',AgeNFO,DefaultAge)
            if "site_inferred_age" in rec.keys() and rec["site_inferred_age"]!="":
                Rages.append([float(rec["site_inferred_age"]),rec["site_inferred_age_unit"]])
                if age_unit=="":age_unit=rec["site_inferred_age_unit"] 
            RLats.append(float(SiteRec["site_lat"]))
            RLons.append(float(SiteRec["site_lon"]))
        PmagResRec["er_location_names"]=RevVGPs[0]["er_location_name"]
        PmagResRec["er_citation_names"]="This study"
        PmagResRec["er_analyst_mail_names"]=user
        sitestring=""
        for site in Sites:
            sitestring=sitestring+site + ":"
        PmagResRec["er_site_names"]=sitestring[:-1]
        PmagResRec["percent_reversed"]="100"
        rpars=pmag.fisher_mean(rpoles) 
        PmagResRec["vgp_lon"]='%7.1f '% (rpars["dec"])
        PmagResRec["vgp_lat"]='%7.1f '% (rpars["inc"])
        PmagResRec["vgp_n"]='%i '%(rpars["n"])
        PmagResRec["vgp_alpha95"]='%7.1f '% (rpars["alpha95"])
        PmagResRec["magic_method_codes"]="DE-VGP"
        PmagResRec["pmag_criteria_codes"]="DE-SITE:RPOLE"
        fpars=pmag.fisher_mean(rdirs)
        PmagResRec["average_dec"]='%7.1f '% (fpars["dec"])
        PmagResRec["average_inc"]='%7.1f '% (fpars["inc"])
        PmagResRec["average_n"]='%i '%(fpars["n"])
        PmagResRec["average_r"]='%5.4f '%(fpars["r"])
        PmagResRec["average_k"]='%7.1f '% (fpars["k"])
        PmagResRec["average_alpha95"]='%7.1f '% (fpars["alpha95"])
        m,x=pmag.gausspars(RLats)
        PmagResRec["average_lat"]='%10.4f ' %(m)
        PmagResRec["average_lat_sigma"]='%10.4f ' %(x)
        m,x=pmag.gausspars(RLons)
        PmagResRec["average_lon"]='%10.4f ' %(m)
        PmagResRec["average_lon_sigma"]='%10.4f ' %(x)
        if len(Rages)>1:
            Adjages,age_unit=pmag.adjust_ages(Rages)
            m,x=pmag.gausspars(Adjages)
            PmagResRec["average_age"]='%10.4e ' %(m)
            PmagResRec["average_age_sigma"]='%10.4e ' %(x)
            PmagResRec["average_age_unit"]=age_unit
        elif len(Rages)==1: 
            PmagResRec["average_age"]='%10.4e ' %(Rages[0][0])
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=age_unit
        else:
            PmagResRec["average_age"]=""
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=""
        PmagResRec['data_type']='a'   
        PmagResRec['magic_software_packages']=version_num
        PmagResults.append(PmagResRec)
    #
        angle='%7.1f '%(pmag.angle([npars["dec"],npars["inc"]],[rpars["dec"],rpars["inc"]])) # angle between two poles
    #
      Ages,Lats,Lons,pole,poles,Sites,dir,dirs=[],[],[],[],[],[],[],[]
      if len(AllVGPs) > 3:
        for lat in NLats: Lats.append(lat)
        for lat in RLats: Lats.append(lat)
        for lon in NLons: Lons.append(lon)
        for lon in RLons: Lons.append(lon)
        for age in Nages: Ages.append(age)
        for age in Rages: Ages.append(age)
        PmagResRec={}
        PmagResRec["result_description"]=comment
        PmagResRec["pmag_result_name"]="Grand Mean pole"
        PmagResRec["result_description"]="Grand Mean of all directions"
        PmagResRec['data_type']='a'   
        for SiteRec in AllVGPs:
            Sites.append(SiteRec["er_site_name"])
            pole=[ float(SiteRec["site_vgp_lon"]),float(SiteRec["site_vgp_lat"])]
            poles.append(pole)
            dir=[ float(SiteRec["site_dec"]),float(SiteRec["site_inc"])]
            dirs.append(dir)
        PmagResRec["er_location_names"]=AllVGPs[0]["er_location_name"]
        PmagResRec["er_citation_names"]="This study"
        PmagResRec["er_analyst_mail_names"]=user
        sitestring=""
        for site in Sites:
            sitestring=sitestring+site + ":"
        PmagResRec["er_site_names"]=sitestring[:-1]
        PmagResRec["percent_reversed"]= '%i '% (100*len(rpoles)/len(poles))
    #
    # get the antipodal angle
    #
        if len(npoles)>2 and len(rpoles)>2: PmagResRec["antipodal"]=angle
        pars=pmag.fisher_mean(poles) 
        PmagResRec["vgp_lon"]='%7.1f '% (pars["dec"])
        PmagResRec["vgp_lat"]='%7.1f '% (pars["inc"])
        PmagResRec["vgp_n"]='%i '%(pars["n"])
        PmagResRec["vgp_alpha95"]='%7.1f '% (pars['alpha95'])
        PmagResRec["magic_method_codes"]="DE-VGP"
        PmagResRec["pmag_criteria_codes"]="DE-SITE"
        fpars=pmag.fisher_mean(dirs)
        PmagResRec["average_dec"]='%7.1f '% (fpars['dec'])
        PmagResRec["average_inc"]='%7.1f '% (fpars['inc'])
        PmagResRec["average_n"]='%i '%(fpars['n'])
        PmagResRec["average_r"]='%5.4f '%(fpars['r'])
        PmagResRec["average_k"]='%7.1f '% (fpars['k'])
        PmagResRec["average_alpha95"]='%7.1f '% (fpars['alpha95'])
        m,x=pmag.gausspars(Lats)
        PmagResRec["average_lat"]='%10.4f ' %(m)
        PmagResRec["average_lat_sigma"]='%10.4f ' %(x)
        m,x=pmag.gausspars(Lons)
        PmagResRec["average_lon"]='%10.4f ' %(m)
        PmagResRec["average_lon_sigma"]='%10.4f ' %(x)
        Adjages,age_unit=pmag.adjust_ages(Ages)
        m,x=pmag.gausspars(Adjages)
        PmagResRec["average_age"]='%10.4e ' %(m)
        PmagResRec["average_age_sigma"]='%10.4e ' %(x)
        PmagResRec["average_age_unit"]=age_unit
    #
    # do reversals test if enough data.  
    #
        print "Please wait while we do a reversal's test - this can take awhile"
        if len(ndirs) > 3 and len(rdirs) > 3:
            V,Vcrit=pmag.watsonsV(ndirs,adirs)
            if V > Vcrit: PmagResRec["reversal_test"]="-"
            if V <= Vcrit: PmagResRec["reversal_test"]="+"
            PmagResRec["magic_method_codes"]=PmagResRec["magic_method_codes"]+":"+"ST-R-2" 
        PmagResRec['data_type']='a'
        PmagResRec['magic_software_packages']=version_num
        PmagResults.append(PmagResRec)
    #
    # do averge V[A]DMs - first collect all the data that pass the SiteIntCrit criteria
    #
    bs,vdms,vadms=[],[],[]
    loclist,sitelist,Iages,ILats,ILons=[],"",[],[],[]
    for site in SiteInts:
        skip=0
        if "site_int_n" in site.keys() and  site["site_int_n"].strip() != "":
            if nocrit!=1:
                if int(site["site_int_n"]) < int(SiteIntCrit['site_int_n']): skip =1
                if float(site["site_int_sigma"]) > float(SiteIntCrit['site_int_sigma']) and float(site['site_int_sigma_perc']) > float(SiteIntCrit['site_int_sigma_perc']): skip =1
            if skip==0:
                sitelist= sitelist+site["er_site_name"] + ":" 
                if site["er_location_name"] not in loclist:loclist.append(site["er_location_name"])
                if "site_int" in site.keys() and site["site_int"]!="" : bs.append(float(site["site_int"]))
                if "site_vdm" in site.keys() and site["site_vdm"]!="" : vdms.append(float(site["site_vdm"]))
                if "site_vadm" in site.keys() and site["site_vadm"]!="" :vadms.append(float(site["site_vadm"]))
                if agefile != "": rec=pmag.get_age(site,'er_site_name',"site_inferred_",AgeNFO,DefaultAge)
                if "site_inferred_age" in rec.keys() and rec["site_inferred_age"]!="":
                    Iages.append((float(rec["site_inferred_age"]),rec["site_inferred_age_unit"]))
                    if age_unit=="":age_unit=rec["site_inferred_age_unit"] 
                for rec in SiteNFO:
                    if rec["er_site_name"]==site["er_site_name"]:
                        lat=float(rec["site_lat"])      
                        lon=float(rec["site_lon"]) 
                        ILats.append(lat)     
                        ILons.append(lon) 
    #
    # a little housekeeping
    #
    if len(bs) > 1:
        PmagResRec={}
        PmagResRec["result_description"]=comment
        PmagResRec["pmag_result_name"]="Average V[A]DM"
        PmagResRec["result_description"]="Average of all V[A]DMs"
        if len(loclist)==1:
            PmagResRec["er_location_names"]=site["er_location_name"]
        else:
            location=""
            for loc in loclist:
                location=location+loc+":"
            PmagResRec["er_location_names"]=location[:-1]
        PmagResRec["er_citation_names"]=site["er_citation_names"]
        PmagResRec["er_analyst_mail_names"]=user
        PmagResRec["pmag_criteria_codes"]="IE-SITE"
    #
    # calculate the averages
    #
        m,sig=pmag.gausspars(bs)
        PmagResRec["average_int"]='%8.3e '% (m)
        PmagResRec["average_int_sigma"]='%8.3e '% (sig)
        PmagResRec["average_int_n"]='%i '% (len(bs))
        sigperc=100*sig/m
        PmagResRec["average_int_sigma_perc"]='%7.1f ' %(sigperc)
        if len(vdms) > 1:
            PmagResRec["vdm_n"]='%i ' % (len(vdms))
            m,sig=pmag.gausspars(vdms)
            PmagResRec["vdm"]='%8.3e '% (m)
            PmagResRec["vdm_sigma"]='%8.3e '% (sig)
        if len(vadms) > 1:
            PmagResRec["vadm_n"]='%i ' % (len(vadms))
            m,sig=pmag.gausspars(vadms)
            PmagResRec["vadm"]='%8.3e '% (m)
            PmagResRec["vadm_sigma"]='%8.3e '% (sig)
        if len(ILats) > 1:
            m,sig=pmag.gausspars(ILats)
            PmagResRec["average_lat"]='%8.4f '% (m)
            PmagResRec["average_lat_sigma"]='%8.4f '% (sig)
            m,sig=pmag.gausspars(ILons)
            PmagResRec["average_lon"]='%8.4f '% (m)
            PmagResRec["average_lon_sigma"]='%8.4f '% (sig)
        if len(Iages) > 1:
            Adjages,age_unit=pmag.adjust_ages(Iages)
            m,x=pmag.gausspars(Adjages)
            PmagResRec["average_age"]='%10.4e ' %(m)
            PmagResRec["average_age_sigma"]='%10.4e ' %(x)
            PmagResRec["average_age_unit"]=age_unit
        elif len(Iages)==1: 
            PmagResRec["average_age"]='%10.4e ' %(Iages[0][0])
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=age_unit
        else:
            PmagResRec["average_age"]=""
            PmagResRec["average_age_sigma"]=""
            PmagResRec["average_age_unit"]=""
        PmagResRec["er_site_names"]=sitelist[:-1]
        PmagResRec["pmag_criteria_codes"]="IE-SITE"
        PmagResRec["magic_method_codes"]=""
        PmagResRec['data_type']='a'
        PmagResRec['magic_software_packages']=version_num
        PmagResults.append(PmagResRec)
    #
    # plot data if plotsite set
    #
    Tmpdir={}
    dirs=[]
    if plotsites==1: 
        if len(ndirs)>0:
            for dir in ndirs: dirs.append(dir)    
        if len(rdirs)>0:
            for dir in rdirs: dirs.append(dir)
        if len(dirs)>0: pmagplotlib.plotEQ(EQ['eqarea'],dirs,"Site means")
    #
    # check if sample VGP/VADM also desired
    #
    if vgps==1: 
        for PmagSampRec in PmagSamps:
            skip=0
            PmagResRec={}
            PmagResRec["er_location_names"]=PmagSampRec["er_location_name"]
            PmagResRec['er_site_names']=PmagSampRec["er_site_name"]
            PmagResRec['er_sample_names']=PmagSampRec["er_sample_name"]
            PmagResRec['er_specimen_names']=PmagSampRec["er_specimen_names"]
            PmagResRec['pmag_criteria_codes']=PmagSampRec["pmag_criteria_codes"]
            PmagResRec['er_citation_names']='This study'
            PmagResRec['er_analyst_mail_names']=user
            if "sample_tilt_correction" not in PmagSampRec.keys():
                PmagResRec["tilt_correction"]="-1" # assume unoriented
            else:  PmagResRec["tilt_correction"]=PmagSampRec["sample_tilt_correction"]
            if "sample_inferred_age" in PmagSampRec.keys():PmagResRec["average_age"]= PmagSampRec["sample_inferred_age"]
            if "sample_inferred_age_sigma" in PmagSampRec.keys():PmagResRec["average_age_sigma"]= PmagSampRec["sample_inferred_age_sigma"]
            if "sample_inferred_age_unit" in PmagSampRec.keys():PmagResRec["average_age_unit"]= PmagSampRec["sample_inferred_age_unit"]
            if "sample_inferred_age_low" in PmagSampRec.keys():
                sigma=0.5*(float(PmagResRec["sample_inferred_age_high"])-float(PmagResRec["sample_inferred_age_low"]))
                age=float(PmagResRec["sample_inferred_age_low"])+sigma
                PmagResRec["average_age"]= '%10.4e'%(age)
                PmagResRec["average_age_sigma"]= '%10.4e'%(sigma)
            if height==1:
                for rec in ErSamps:
                    if 'sample_height' in rec.keys() and rec['er_sample_name']==PmagResRec['er_sample_names']:
                        PmagResRec["average_height"]=rec["sample_height"]
                        break    
            for rec in SiteNFO:
                if rec["er_site_name"]==PmagSampRec["er_site_name"]:
                    lat=float(rec["site_lat"])
                    lon=float(rec["site_lon"])
                    break
            PmagResRec["average_lat"]='%10.4f ' %(lat)
            PmagResRec["average_lon"]='%10.4f ' %(lon)
            if PmagSampRec["sample_direction_type"]=="l":
                if nocrit==1 or rec["sample_alpha95"] == "" or float(rec["sample_alpha95"]) <= float(SampCrit["sample_alpha95"]):
                    PmagResRec["pmag_result_name"]="VGP: Sample "+PmagSampRec["er_sample_name"]
                    PmagResRec["result_description"]="VGP of sample"
                    PmagResRec["average_dec"]=PmagSampRec["sample_dec"]
                    dec=float(PmagSampRec["sample_dec"])
                    PmagResRec["average_inc"]=PmagSampRec["sample_inc"]
                    inc=float(PmagSampRec["sample_inc"])
                    PmagResRec["average_alpha95"]=PmagSampRec["sample_alpha95"]
                    if PmagSampRec['sample_alpha95']!="":
                        a95=float(PmagSampRec["sample_alpha95"])
                    else:
                        a95=0.
                    PmagResRec["average_n"]="1"
                    PmagResRec["vgp_n"]="1"
                    plong,plat,dp,dm=pmag.dia_vgp(dec,inc,a95,lat,lon)
                    PmagResRec["magic_method_codes"]= PmagSampRec["magic_method_codes"]+":"+ "DE-DI"
                    PmagResRec["vgp_lat"]='%7.1f ' % (plat)
                    PmagResRec["vgp_lon"]='%7.1f ' % (plong)
                    PmagResRec['pmag_criteria_codes']='DE-SAMP'
                else:
                    skip=1
    #
    # now do the intensities
    #
            if PmagSampRec["sample_description"]=="sample intensity":
                skip=0
                if nocrit!=1:
                    if int(PmagSampRec["sample_int_n"]) < int(SampIntCrit['sample_int_n']): skip =1
                    if float(PmagSampRec["sample_int_sigma"]) > float(SampIntCrit['sample_int_sigma']) and float(PmagSampRec['sample_int_sigma_perc']) > float(SampIntCrit['sample_int_sigma_perc']): skip =1
                if skip==0:
                    PmagResRec["pmag_result_name"]="V[A]DM: Sample "+PmagSampRec["er_sample_name"]
                    PmagResRec["magic_method_codes"]= PmagSampRec["magic_method_codes"]
                    PmagResRec["result_description"]="V[A]DM of sample"
                    PmagResRec["pmag_criteria_codes"]="IE-SAMP"
                    b=float(PmagSampRec["sample_int"])
                    if (PmagSampRec["sample_int_sigma"])!="":
                        b_sig=float(PmagSampRec["sample_int_sigma"])
                    else:
                        b_sig=""
                    PmagResRec["average_int"]=PmagSampRec["sample_int"]
                    PmagResRec["average_int_n"]=PmagSampRec["sample_int_n"]
                    PmagResRec["average_int_sigma"]=PmagSampRec["sample_int_sigma"]
                    PmagResRec["average_int_sigma_perc"]=PmagSampRec["sample_int_sigma_perc"]
    #
    #  calculate VDM  and VADM (if inc for VDM and lat for VADM are available)
    #
                    if len(SampDirs)>0:
                        for rec in SampDirs:
                            if rec["er_sample_name"]==PmagSampRec["er_sample_name"]:
                                if rec["tilt_correction"]==coord: # sample is oriented
                                    inc=float(rec["sample_inc"])
                                    mlat=pmag.magneti_lat(inc)
                                    vdm=pmag.b_vdm(b,mlat)
                                    PmagResRec["vdm"]='%8.3e '% (vdm)
                                    if b_sig!="":
                                        vdm_sig=pmag.b_vdm(b_sig,mlat)
                                        PmagResRec["vdm_sigma"]='%8.3e '% (vdm_sig)
                                    else:
                                        PmagResRec["vdm_sigma"]=""
    #
    # calculate VADM if using lat or model lat
    #
                    if get_model_lat!=0: # calculate VADM
                        if get_model_lat==2:
                            for latrec in ModelLats:
                                if latrec["er_site_name"]==PmagSampRec["er_site_name"]:
                                    lat=float(latrec["site_model_lat"])
                                    PmagResRec["model_lat"]='%7.1f ' % (lat)
                        vadm=pmag.b_vdm(b,lat) 
                        PmagResRec["vadm"]='%8.3e '% (vadm)
                        PmagResRec["vadm_n"]=PmagSampRec["sample_int_n"]
                        if b_sig!="":
                            vadm_sig=pmag.b_vdm(b_sig,lat)
                            PmagResRec["vadm_sigma"]='%8.3e '% (vadm_sig)
                        else:
                            PmagResRec["vadm_sigma"]=""
                        if 'magic_method_codes' not in PmagResRec.keys():PmagResRec["magic_method_codes"]=""
                        PmagResRec['pmag_criteria_codes']='IE-SAMP'
                    PmagResRec['data_type']='i'
                    PmagResRec['magic_software_packages']=version_num
                    PmagResults.append(PmagResRec)
        
    # save the Results table
    #
    if len(PmagResults)  >0:
        TmpResults=PmagResults[:]
        PmagResults,reskeys=pmag.fillkeys(TmpResults)
        pmag.magic_write(resout,PmagResults,"pmag_results")
        print "results saved in ",resout
    else:
        print  "no results matched your criteria"
    #
    # save the Mailing list table
    #
    if len(Names)  >0:
        Mailnames=[]
        for name in Names:
          if name!="" and "unknown" not in name:
            mailname={}
            mailname["er_mail_name"]=name 
            if 'organization' not in mailname.keys(): mailname["organization"]="SIO"  # these are just dummies - get fixed on upload
            if 'country' not in mailname.keys():    mailname["country"]="U.S.A."
            Mailnames.append(mailname)
        if len(Mailnames)>1:
            pmag.magic_write('er_mailinglist.txt',Mailnames,"er_mailinglist")
            print "Scientists, analysts  saved in er_mailinglist.txt \n"
main()
