#!/usr/bin/env python
import pmag,sys,string
def main():
    """
    NAME
        FIN_magic.py
 
    DESCRIPTION
        converts FINNISH format files to magic_measurements format files

    SYNTAX
        FIN_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify index file with list of files for importing [default is index.txt]
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsp FILE: specify output er_specimens.txt file, default is er_specimens.txt
        -Fsi FILE: specify output er_sites.txt file, default is er_sites.txt
        -n [gm,kg,cc,m3]: specify normalization
        -spc NUM : specify number of characters to designate a  specimen, default = 1
        -ncn NCON: specify naming convention [default is #2 below]
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SITEFILE or be a synthetic
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        -ac B : peak AF field (in mT) for ARM acquisition, default is none

    INPUT
        Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.) 

    NOTES:
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
 
    """
#        
#
    norm='cc'
    samp_con,Z='2',1        
    meas_file='magic_measurements.txt'
    spec_file='er_specimens.txt'
    samp_file='er_samples.txt'
    site_file='er_sites.txt'
    magfile='index.txt'
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MeasRecs=[]
    specnum,unis,locname=-1,"1","unknown"
    citation="This study"
    dir_path='.'
    args=sys.argv
    labfield,phi,theta="","",""
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        meas_file=args[ind+1]
    if '-Fsp' in args:
        ind=args.index("-Fsp")
        spec_file=args[ind+1]
    if '-Fsa' in args:
        ind=args.index("-Fsa")
        samp_file=args[ind+1]
    if '-loc' in args:
        ind=args.index("-loc")
        locname=args[ind+1]
    if '-spc' in args:
        ind=args.index("-spc")
        specnum=-int(args[ind+1])
    if '-dc' in args:
        ind=args.index("-dc")
        labfield=float(args[ind+1])*1e-6
        phi=args[ind+2]
        theta=args[ind+3]
    if '-n' in args:
        ind=args.index("-n")
        norm=args[ind+1]
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else: 
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
    magfile=dir_path+'/'+magfile
    spec_file=dir_path+'/'+spec_file
    samp_file=dir_path+'/'+samp_file
    site_file=dir_path+'/'+site_file
    meas_file=dir_path+'/'+meas_file
    try:
        input=open(magfile,'rU')
    except:
        print "bad sam file name"
        sys.exit()
    Files=input.readlines()
    sids,ln=[],0
    specimens,samples,sites=[],[],[]
    for file in Files:
        Zsteps,Isteps=[],[]
        print 'processing ',file.split()[0]
        data=open(file.split()[0],'rU').readlines()
# parse out header info
        line= data[0]
        k=6
        while k<len(line) and line[k]==' ':k+=1
        inst=line[k:]
        line= data[1]
        rec=line.split(':')
        specimen=rec[1].split()[0].lower()
        if specnum!=0:
            sample=specimen[:specnum]
        else: sample=specimen
        site=pmag.parse_site(sample,samp_con,Z)
        line= data[2]
        rec=line.split(':')
        lithology=rec[1]
        line=data[7]
        rec=line.split() 
        site_lat=rec[0]
        site_lon=rec[1]
#        sample_azimuth=(float(rec[2])-90.)
#        if sample_azimuth<0:sample_azimuth+=360.
##        sample_dip=(90.-float(rec[3]))
        dip=float(rec[5])
        if dip!=0:
            dip_direction=(float(rec[4])-90.)
        else:
            dip_direction=0
        if dip_direction<0:dip_direction+=360.
        sample_azimuth=0
        sample_dip=0 
## the data are in geographic coordinates already
        vol=float(rec[6])
        weight=float(rec[7])
        line= data[8]
        treat_type=line[:2]
        ErSpecRec,ErSampRec,ErSiteRec={},{},{}
        ErSpecRec['er_specimen_name']=specimen
        ErSpecRec['er_sample_name']=sample
        ErSpecRec['er_site_name']=site
        ErSpecRec['er_location_name']=locname
        ErSpecRec['er_citation_name']=citation
        ErSampRec['er_sample_name']=sample
        ErSampRec['er_site_name']=site
        ErSampRec['er_location_name']=locname
        ErSampRec['er_citation_name']=citation
        ErSiteRec['sample_lat']=site_lat
        ErSiteRec['sample_lon']=site_lon
        ErSiteRec['er_site_name']=site
        ErSiteRec['er_location_name']=locname
        ErSiteRec['er_citation_name']=citation
        ErSiteRec['site_lat']=site_lat
        ErSiteRec['site_lon']=site_lon
        if weight!=0:
            ErSpecRec['specimen_weight']='%10.3e'%(weight*1e-3) # convert to kg
        else: 
            ErSpecRec['specimen_weight']=""
        if vol!=0:
            if norm=='cc':units="1"
            if norm=='m3':units="2"
            if units=="1" or "":
                ErSpecRec['specimen_volume']='%10.3e'%(vol*1e-6)
            else: 
                ErSpecRec['specimen_volume']='%10.3e'%(vol)
        else:
            ErSpecRec['specimen_volume']=""
        ErSampRec['sample_azimuth']='%7.1f'%(sample_azimuth)
        ErSampRec['sample_dip']='%7.1f'%(sample_dip)
        ErSampRec['sample_bed_dip']='%7.1f'%(dip)
        ErSampRec['sample_bed_dip_direction']='%7.1f'%(dip_direction)
        ErSampRec['sample_class']=''
        ErSampRec['sample_type']=''
        ErSampRec['sample_lithology']=lithology
        ErSampRec['magic_method_codes']="SO-CMD-NORTH"
        lastrec=data[-1]
        while len(lastrec.split())<2: # stripping off blanks at end
            del data[-1]
            lastrec=data[-1]
        for line in data[9:]:
            MeasRec=ErSpecRec.copy()
            MeasRec['measurement_standard']='u'
            MeasRec['measurement_temp']='273'
            rec=line.split()
            if len(rec)==1:
                rec=line.split('\t')
            treat=rec[0].strip()
            if treat=="0":
                MeasRec['magic_method_codes']='LT-NO'
                MeasRec['treatment_temp']='273'
                MeasRec['treatment_dc_field']='0'
                MeasRec['treatment_dc_field_phi']=''
                MeasRec['treatment_dc_field_theta']=''
                MeasRec['treatment_ac_field']='0'
            else:
                if treat_type.strip()=='AF':
                    MeasRec['magic_method_codes']='LT-AF-Z'
                    MeasRec['treatment_temp']='273'
                    MeasRec['treatment_dc_field']='0'
                    MeasRec['treatment_dc_field_phi']=''
                    MeasRec['treatment_dc_field_theta']=''
                    MeasRec['treatment_ac_field']='%10.3e'%(float(treat)*1e-4) # convert from Oe
                elif treat_type.strip()=='TH':
                    if labfield=="":
                        MeasRec['magic_method_codes']='LT-T-Z'
                        MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                        MeasRec['treatment_dc_field']='0'
                        MeasRec['treatment_dc_field_phi']=''
                        MeasRec['treatment_dc_field_theta']=''
                        MeasRec['treatment_ac_field']='0'
                    else:
                        if treat not in Zsteps:
                            print 'first Z: ',treat
                            Zsteps.append(treat)
                            MeasRec['magic_method_codes']='LT-T-Z'
                            MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                            MeasRec['treatment_dc_field']='0'
                            MeasRec['treatment_dc_field_phi']=''
                            MeasRec['treatment_dc_field_theta']=''
                            MeasRec['treatment_ac_field']='0'
                        elif treat not in Isteps:
                            print 'first I: ',treat
                            Isteps.append(treat)
                            MeasRec['magic_method_codes']='LT-T-I'
                            MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                            MeasRec['treatment_dc_field']='%10.3e'%(labfield)
                            MeasRec['treatment_dc_field_phi']=phi
                            MeasRec['treatment_dc_field_theta']=theta
                            MeasRec['treatment_ac_field']='0'
                        elif treat in Isteps:
                            if float(treat)<float(Zsteps[-1]):
                                print 'pTRM ',treat
                                MeasRec['magic_method_codes']='LT-PTRM-Z'
                                MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                                MeasRec['treatment_dc_field']=''
                                MeasRec['treatment_dc_field_phi']=''
                                MeasRec['treatment_dc_field_theta']=''
                                MeasRec['treatment_ac_field']='0'
                            else:
                                print 'pTRM tail ',treat
                                MeasRec['magic_method_codes']='LT-PTRM-MD'
                                MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                                MeasRec['treatment_dc_field']=''
                                MeasRec['treatment_dc_field_phi']=''
                                MeasRec['treatment_dc_field_theta']=''
                                MeasRec['treatment_ac_field']='0'
            MeasRec['measurement_dec']=rec[1]
            MeasRec['measurement_inc']=rec[2]
            intens='%8.2e'%(float(rec[3])*1e-3) # convert to A/m 
            MeasRec['measurement_magn_volume']=intens
            MeasRec['measurement_csd']='%7.1f'%(eval(rec[5]))
            MeasRec['magic_instrument_codes']=inst
            MeasRecs.append(MeasRec)
        ErSpecs.append(ErSpecRec)
        if sample not in samples:
            samples.append(sample)
            ErSamps.append(ErSampRec)
        if site not in sites:
            sites.append(site)
            ErSites.append(ErSiteRec)
    pmag.magic_write(spec_file,ErSpecs,'er_specimens')
    print 'specimens stored in ',spec_file
    pmag.magic_write(samp_file,ErSamps,'er_samples')
    print 'samples stored in ',samp_file
    pmag.magic_write(site_file,ErSites,'er_sites')
    Fixed=pmag.measurements_methods(MeasRecs,1)
    pmag.magic_write(meas_file,Fixed,'magic_measurements')
    print 'data stored in ',meas_file
main()
