#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        UCSC_leg_magic.py
 
    DESCRIPTION
        converts UCSC legacy format files to magic_measurements format files

    SYNTAX
        UCSC_leg_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify  input file, or
        -fin INDEX: specify  index file for reading whole directory: default is index.txt
        -F FILE: specify output file, default is magic_measurements.txt
        -Fsa: specify er_samples format file for appending, default is new er_samples.txt
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -loc LOCNAME : specify location/study name
        -A: don't average replicate measurements
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] sample = site
            [6] all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.
 
    INPUT
        Format of UCSC legacy files:   
         
        Spec Treat CDec CInc GDec GInc SDec SInc Int [optional A95]
          Treat is HX where X is AF field in Oe, TX where X is T in C,  or NRM
        
         Intensity assumed to be total moment in (emu/cc) with a 10cc specimen volume
         CDec:  Declination in specimen coordinate system
         CInc:  Declination in specimen coordinate system
         GDec:  Declination in geographic coordinate system
         GInc:  Declination in geographic coordinate system
         SDec:  Declination in stratigraphic coordinate system
         SInc:  Declination in stratigraphic coordinate system
   index file:  must be formatted:
         FILENAME  SITE
    """
# initialize some stuff
    noave=0
    methcode,inst="",""
    samp_con,Z='4',3
    missing=1
    demag="N"
    er_location_name=""
    citation='This study'
    args=sys.argv
    methcode="LP-NO"
    specnum=-1
    MagRecs=[]
    version_num=pmag.get_version()
    Samps=[] # keeps track of sample orientations
    DIspec=[]
    MagFiles=[]
#
# get command line arguments
#
    user=""
    mag_file=""
    ind_file=""
    dir_path='.'
    ErSamps,ErSites=[],[]
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    samp_file=dir_path+'/er_samples.txt'
    site_file=dir_path+'/er_sites.txt'
    meas_file=dir_path+"/magic_measurements.txt"
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=dir_path+'/'+args[ind+1]
    if '-Fsi' in args:
        ind=args.index("-Fsi")
        site_file=dirpath+'.'+args[ind+1]
    try:
        open(site_file,'rU')
        ErSites,file_type=pmag.magic_read(site_file)
        print 'site information will be appended to ', site_file 
    except:
        print site_file,' not found: site information will be stored in new er_sites.txt file'
        site_file=dir_path+'/er_sites.txt'
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=dirpath+'/'+args[ind+1]
    try:
        open(samp_file,'rU')
        ErSamps,file_type=pmag.magic_read(samp_file)
        print 'sample information will be appended to ', samp_file 
    except:
        print samp_file,' not found: sample information will be stored in new er_samples.txt file'
        samp_file=dir_path+'/er_samples.txt'
    if '-f' in args:
        ind=args.index("-f")
        mag_file=args[ind+1]
        site=mag_file.split('.')[0]
        magfile=dir_path+'/'+mag_file
        try:
            input=open(magfile,'rU')
            MagFiles.append([magfile,site])
        except:
            print "bad input file name"
            sys.exit()
    elif '-fin' in args:
        ind=args.index("-fin")
        ind_file=args[ind+1]
        ind_file=dir_path+'/'+ind_file
        try:
            index_file=open(ind_file,'rU')
        except:
            print "bad index file name"
            sys.exit()
    elif '-fin' not in args:
        ind_file=dir_path+'/index.txt'
        try:
            index_file=open(ind_file,'rU')
        except:
            print "bad index file name"
            sys.exit()
    if ind_file!="": 
        Files=index_file.readlines()
        for file in Files:
            rec=file.split()
            MagFiles.append(rec)
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    else:
        print "-loc  is required option"
        print main.__doc__
        sys.exit()
    if "-A" in args: noave=1
    Sites=[]
    for file in MagFiles:
        site=file[1] # attach site name either from file name or from index file
        if site not in Sites:
            Sites.append(site)
            ErSiteRec={'er_location_name': er_location_name,'er_site_name':site,'er_citation_names':citation,'site_definition':'s','site_lat':'','site_lon':"",'site_class':"",'site_lithology':"",'site_type':""}
            ErSites.append(ErSiteRec)
        print 'processing file: ',file[0],' for site: ',site
        data=open(dir_path+'/'+file[0],'rU').readlines() # read in data from file
        firstrec=data[0].split()
        if firstrec[0]=='FILE': # this file has a header, must look for start of data
            for k in range(len(data)):
                if data[k][0]=='-': break    
        else:
            k=-1
        while k<len(data)-1:
            k+=1
            line=data[k]
            if len(line)>2: # skip stupid terminal lines
                line=line.replace(' T  ',' T') # make columns consistent
                line=line.replace(' H  ',' H') # make columns consistent
                line=line.replace(' T ',' T') # make columns consistent
                line=line.replace(' H ',' H') # make columns consistent
                rec=line.split()
                if len(rec)<2: break # skip junk
                MagRec={}
                MagRec['er_location_name']=er_location_name
                MagRec['magic_software_packages']=version_num
                MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                MagRec["treatment_ac_field"]='0'
                meas_type="LT-NO"
                MagRec["measurement_flag"]='g'
                MagRec["measurement_standard"]='u'
                MagRec["measurement_number"]='1'
                MagRec["er_specimen_name"]=rec[0]
                if specnum!=0:
                    MagRec["er_sample_name"]=rec[0][:specnum]
                else:
                    MagRec["er_sample_name"]=rec[0]
     #           site=pmag.parse_site(MagRec['er_sample_name'],samp_con,Z)
                MagRec["er_site_name"]=site
                MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[8])*1e-4) # # int is in emu/cc; assuming 10cc, this converts to Am^2 
    #
                if samp_file!="" and MagRec["er_sample_name"] not in Samps:        # create er_samples.txt file with these data 
                    cdec,cinc=float(rec[2]),float(rec[3])
                    gdec,ginc=float(rec[4]),float(rec[5])
                    az,pl=pmag.get_azpl(cdec,cinc,gdec,ginc)
                    bdec,binc=float(rec[6]),float(rec[7])
                    if rec[4]!=rec[6] and rec[5]!=rec[7]:
                        dipdir,dip=pmag.get_tilt(gdec,ginc,bdec,binc)
                    else:
                        dipdir,dip=0,0
                    ErSampRec={}
                    ErSampRec['er_citation_names']='This study'
                    ErSampRec['er_location_name']=MagRec['er_location_name']
                    ErSampRec['er_site_name']=MagRec['er_site_name']
                    ErSampRec['er_sample_name']=MagRec['er_sample_name']
                    ErSampRec['sample_azimuth']='%7.1f'%(az)
                    ErSampRec['sample_dip']='%7.1f'%(pl)
                    ErSampRec['sample_bed_dip_direction']='%7.1f'%(dipdir)
                    ErSampRec['sample_bed_dip']='%7.1f'%(dip)
                    ErSampRec['sample_description']='az,pl,dip_dir and dip recalculated from [c,g,b][dec,inc] in UCSC legacy file'
                    ErSampRec['magic_method_codes']='SO-NO'
                    ErSamps.append(ErSampRec)
                    Samps.append(ErSampRec['er_sample_name'])
                MagRec["measurement_dec"]=rec[2]
                MagRec["measurement_inc"]=rec[3]
                MagRec["er_analyst_mail_names"]=""
                MagRec["er_citation_names"]="This study"
                demag=rec[1][0]
                if demag!='N':
                    treat=float(rec[1][1:])
                else:
                    treat=0
                if demag=="H":
                    MagRec["treatment_ac_field"]='%8.3e' %(treat*1e-4) # convert from oe to tesla
                    meas_type="LT-AF-Z"
                elif demag=="T":
                    MagRec["treatment_temp"]='%8.3e' % (treat+273.) # temp in kelvin
                    meas_type="LT-T-Z"
                MagRec['magic_method_codes']=meas_type
                MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "results put in ",meas_file
    pmag.magic_write(samp_file,ErSamps,'er_samples')
    print "sample orientations put in ",samp_file
    pmag.magic_write(site_file,ErSites,'er_sites')
    print "site names put in ",site_file
main()
