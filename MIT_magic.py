#!/usr/bin/env python
import pmag,sys
def main():
    """
    NAME
        MIT_magic.py
 
    DESCRIPTION
        converts MIT .sam  format files to magic_measurements format files

    SYNTAX
        MIT_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify .sam format input file, required
        -fsi SITEFILE : specify file with site names and locations [tab delimited magic file]
        -F FILE: specify output  measurements file, default is magic_measurements.txt
        -Fsp FILE: specify output er_specimens.txt file, default is er_specimens.txt
        -Fsi FILE: specify output er_sites.txt file, default is er_sites.txt
        -n [gm,kg,cc,m3]: specify normalization
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -ncn NCON: specify naming convention
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
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length) [default]
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.
 
    """
#        
#
    norm='cc'
    samp_con,Z='3',1        
    meas_file='magic_measurements.txt'
    spec_file='er_specimens.txt'
    samp_file='er_samples.txt'
    site_file='er_sites.txt'
    ErSpecs,ErSamps,ErSites,ErLocs,ErCits=[],[],[],[],[]
    MeasRecs=[]
    specnum,units,locname=0,"1","unknown"
    citation="This study"
    dir_path='.'
    args=sys.argv
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
    if '-n' in args:
        ind=args.index("-n")
        norm=args[ind+1]
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 3-Z where Z is an integer"
                sys.exit()
            else: 
                Z=samp_con.split("-")[1]
                samp_con="4"
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
    magfile=dir_path+'/'+magfile
    spec_file=dir_path+'/'+spec_file
    samp_file=dir_path+'/'+samp_file
    site_file=dir_path+'/'+site_file
    meas_file=dir_path+'/'+meas_file
    try:
        input=open(magfile,'r')
    except:
        print "bad sam file name"
        sys.exit()
    File=input.readlines()
    sids,ln,format=[],0,'CIT'
    formats=['CIT','2G','APP','JRA']
    ErLocRec={}
    ErLocRec["er_location_name"]=locname
    ErLocRec["er_citation_name"]=citation
    comment=File[ln]
    if comment=='CIT':
       format=comment
       ln+=1
    comment=File[ln]
    print comment
    ln+=1
    specimens,samples,sites=[],[],[]
    if format=='CIT':
        line=File[ln].split()
        site_lat=line[0]
        site_lon=line[1]
        ErLocRec["location_begin_lat"]=site_lat
        ErLocRec["location_begin_lon"]=site_lon
        ErLocRec["location_end_lat"]=site_lat
        ErLocRec["location_end_lon"]=site_lon
        ErLocs.append(ErLocRec)
        Cdec=float(line[2])
        for k in range(ln+1,len(File)):
            line=File[k]
            rec=line.split()
            specimen=rec[0]
            specimens.append(specimen)
    for specimen in specimens:
        ErSpecRec,ErSampRec,ErSiteRec={},{},{}
        if specnum!=0:
            sample=specimen[:specnum]
        else: sample=specimen
        site=pmag.parse_site(sample,samp_con,Z)
        ErSpecRec['er_specimen_name']=specimen
        ErSpecRec['er_sample_name']=sample
        ErSpecRec['er_site_name']=site
        ErSpecRec['er_location_name']=locname
        ErSpecRec['er_citation_name']=citation
        ErSampRec['er_sample_name']=sample
        ErSampRec['er_site_name']=site
        ErSampRec['er_location_name']=locname
        ErSampRec['er_citation_name']=citation
        ErSiteRec['er_site_name']=site
        ErSiteRec['er_location_name']=locname
        ErSiteRec['er_citation_name']=citation
        ErSiteRec['site_lat']=site_lat
        ErSiteRec['site_lon']=site_lon
        f=open(dir_path+'/'+specimen,'rU')
        Lines=f.readlines()
        comment=""
        line=Lines[0].split()
        if len(line)>2:comment=line[2]
        info=Lines[1].split()
        vol=float(info[-1])
        if vol!=1.0:
            if norm=='cc':units="1"
            if norm=='m3':units="2"
            ErSampRec['specimen_weight']=""
            if units=="1" or "":
                ErSampRec['specimen_volume']='%10.3e'%(vol*1e-6)
            else: 
                ErSampRec['specimen_volume']='%10.3e'%(vol)
        else:
            if norm=='cc':units="1"
            if norm=='m3':units="2"
            ErSampRec['specimen_volume']=""
            if units=="1" or "":
                ErSampRec['specimen_weight']='%10.3e'%(vol*1e-3)
            else: 
                ErSampRec['specimen_weight']='%10.3e'%(vol)
        dip=float(info[-2])
        dip_direction=float(info[-3])+Cdec+90.
        sample_dip=-float(info[-4])
        sample_azimuth=float(info[-5])+Cdec-90.
        if len(info)>5:
            ErSampRec['sample_height']=info[-6]
        else:
            ErSampRec['sample_height']='0'
        ErSampRec['sample_azimuth']='%7.1f'%(sample_azimuth)
        ErSampRec['sample_dip']='%7.1f'%(sample_dip)
        ErSampRec['sample_bed_dip']='%7.1f'%(dip)
        ErSampRec['sample_bed_dip_direction']='%7.1f'%(dip_direction)
        ErSampRec['sample_class']=''
        ErSampRec['sample_type']=''
        ErSampRec['sample_lithology']=''
        if Cdec!=0 or Cdec!="":
            ErSampRec['magic_method_codes']='SO-CMD-NORTH'
        else:
            ErSampRec['magic_method_codes']='SO-MAG'
        for line in Lines[2:len(Lines)-1]:
            MeasRec=ErSpecRec.copy()
            treat_type=line[0:3]
            treat=line[3:6]
            if treat_type.strip()=='NRM' or treat=="   ":
                MeasRec['magic_method_codes']='LT-NO'
                MeasRec['measurement_temp']='273'
                MeasRec['treatment_temp']='273'
                MeasRec['treatment_dc_field']='0'
                MeasRec['treatment_ac_field']='0'
            elif treat_type.strip()=='AF':
                MeasRec['magic_method_codes']='LT-AF-Z'
                MeasRec['measurement_temp']='273'
                MeasRec['treatment_temp']='273'
                MeasRec['treatment_dc_field']='0'
                MeasRec['treatment_ac_field']='%10.3e'%(float(treat)*1e-3)
            elif treat_type.strip()=='TT':
                MeasRec['magic_method_codes']='LT-T-Z'
                MeasRec['measurement_temp']='273'
                MeasRec['treatment_temp']='%7.1f'%(float(treat)+273)
                MeasRec['treatment_dc_field']='0'
                MeasRec['treatment_ac_field']='0'
            else:
                print "trouble with your treatment steps"
            MeasRec['measurement_dec']=line[46:51]
            MeasRec['measurement_inc']=line[52:58]
            int='%8.2e'%(float(line[31:39])*vol*1e-3) # convert to Am2
            MeasRec['measurement_magn_moment']=int
            MeasRec['measurement_x_sd']='%8.2e'%(float(line[58:67])*1e-8) #(convert e-5emu to Am2)
            MeasRec['measurement_y_sd']='%8.2e'%(float(line[67:76])*1e-8)
            MeasRec['measurement_z_sd']='%8.2e'%(float(line[76:85])*1e-8)
            MeasRec['measurement_csd']='%7.1f'%(eval(line[41:46]))
            MeasRec['magic_instrument_codes']=line[85:]
            MeasRecs.append(MeasRec)
        ErSpecs.append(ErSpecRec)
        if sample not in samples:
            samples.append(sample)
            ErSamps.append(ErSampRec)
        site=pmag.parse_site(sample,samp_con,Z)
        if site not in sites:
            sites.append(site)
            ErSites.append(ErSiteRec)
    pmag.magic_write(spec_file,ErSpecs,'er_specimens')
    print 'specimens stored in ',spec_file
    pmag.magic_write(samp_file,ErSamps,'er_samples')
    print 'samples stored in ',samp_file
    pmag.magic_write(site_file,ErSites,'er_sites')
    Fixed=pmag.measurements_methods(MeasRecs,0)
    pmag.magic_write(meas_file,Fixed,'magic_measurements')
    print 'data stored in ',meas_file
main()
