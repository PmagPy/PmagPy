#!/usr/bin/env python
import string,sys,pmag,exceptions,struct
#
#
def skip(N,ind,L):
    for b in range(N):
        ind+=1
        while L[ind]=="":ind+=1
    ind+=1
    while L[ind]=="":ind+=1
    return ind
def main():
    """
    NAME
        UB_magic.py
   
    DESCRIPTION
        takes University of Barcelona format magnetometer files and converts them to magic_measurements and er_samples.txt
 
    SYNTAX
        UB_magic.py [command line options]

    OPTIONS
        -f FILE: specify master txt file
        -fpos FILE: specify stratigraphic position  file (.saf format)
        -F FILE: specify magic_measurements output file, default is: magic_measurements.txt
        -Fsa FILE: specify output file, default is: er_samples.txt 
        -ncn NCON:  specify naming convention: default is #2 below
        -ocn OCON:  specify orientation convention, default is #5 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
             SO-SUN   orientation with sun compass
        -loc: location name, default="unknown"
        -spc NUM : specify number of characters to designate a  specimen, default = 0     
        -ins INST : specify instsrument name
        -a: average replicate measurements

    INPUT FORMAT
        Input files are horrible 2G binary format (who knows why?)
        Orientation convention:
            [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
                i.e., field_dip is degrees from vertical down - the hade [default]
            [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
                i.e., mag_azimuth is strike and field_dip is hade
            [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
                e.g. field_dip is degrees from horizontal of drill direction
            [4] lab azimuth and dip are same as mag_azimuth, field_dip
            [5] lab azimuth and dip are same as mag_azimuth, field_dip-90
            [6] all others you will have to either customize your 
                self or e-mail ltauxe@ucsd.edu for help.  
       
         Magnetic declination convention:
             Az will use supplied declination to correct azimuth 
    
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
 
    OUTPUT
            output saved in magic_measurements.txt & er_samples.txt formatted files
              will overwrite any existing files 
    """
    #
    # initialize variables
    #
    specnum=0
    ub_file,samp_file,or_con,corr,meas_file = "","er_samples.txt","3","1","magic_measurements.txt"
    pos_file=""
    noave=1
    args=sys.argv
    bed_dip,bed_dip_dir="",""
    samp_con,Z,average_bedding="2",1,"0"
    meths='FS-FD'
    sclass,lithology,type="","",""
    user,inst="",""
    DecCorr=0.
    location_name="unknown"
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    gmeths=""
    #
    #
    dir_path='.'
    if '-WD' in args:
        ind=args.index("-WD")
        dir_path=sys.argv[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-f" in args:
        ind=args.index("-f")
        ub_file=sys.argv[ind+1]
    if "-fpos" in args:
        ind=args.index("-fpos")
        pos_file=sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        meas_file=sys.argv[ind+1]
    if "-Fsa" in args:
        ind=args.index("-Fsa")
        samp_file=sys.argv[ind+1]
    if "-ocn" in args:
        ind=args.index("-ocn")
        or_con=sys.argv[ind+1]
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
    if "-mcd" in args:
        ind=args.index("-mcd")
        gmeths=(sys.argv[ind+1])
    if "-loc" in args:
        ind=args.index("-loc")
        location_name=(sys.argv[ind+1])
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-ins" in args:
        ind=args.index("-ins")
        inst=args[ind+1]
    if "-a" in args:noave=0
    #
    #
    ub_file=dir_path+'/'+ub_file
    if pos_file!="":pos_file=dir_path+'/'+pos_file
    samp_file=dir_path+'/'+samp_file
    meas_file=dir_path+'/'+meas_file
    samplist=[]
    try:
        SampOut,file_type=pmag.magic_read(samp_file)
        for rec in SampOut:
            if samp['er_sample_name'] not in samplist: samplist.append(samp['er_sample_name'])
    except:
        SampOut=[]
    PosData=[]
    if pos_file != "":
        p=open(pos_file,'rU')
        PosIn=p.readlines()
        p.close()
        for line in PosIn:
            srec=line.split()[0].split(',')
            Prec={'er_site_name':srec[0],'sample_height':srec[1]}
            PosData.append(Prec)
    mastfile=open(ub_file,'rU')
    Files=mastfile.readlines()
    mastfile.close()
    MagRecs,SampRecs=[],[]
    for file in Files:
      cfile=file.split()[0]
      if cfile!='end':
        cfile=dir_path+'/'+file.split()[0]+'.dat'
        f=open(cfile,'rU')
        input=f.read()
        f.close()
        firstline=1
        d=input.split('\xcd')
        for line in d:
                rec=line.split('\x00')
                if firstline==1:
                    firstline=0
                    specname,vol="",1
                    for c in line[15:23]:
                        if c!='\x00':specname=specname+c 
                    print 'importing ',specname
                    el=9
                    while rec[el]!='\x01':el+=1
                    vcc,date,comment=rec[el-3],rec[el+7],rec[el+8]
                    el+=10
                    while rec[el]=="":el+=1
                    az=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    pl=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    bed_dip_dir=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    bed_dip=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    if rec[el]=='\x01': 
                        bed_dip=180.-bed_dip
                        el+=1
                        while rec[el]=="":el+=1
                    fold_az=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    fold_pl=rec[el]
                    el+=1
                    while rec[el]=="":el+=1
                    if rec[el]!="":
                        deccorr=float(rec[el])
                        az+=deccorr
                        bed_dip_dir+=deccorr
                        fold_az+=deccorr
                        if bed_dip_dir>=360:bed_dip_dir=bed_dip_dir-360.
                        if az>=360.:az=az-360.
                        if fold_az>=360.:fold_az=fold_az-360.
                    else:
                        deccorr=0
                    if specnum!=0:
                        sample=specname[:specnum]
                    else:
                        sample=specname
                    if sample not in samplist:
                        samplist.append(sample)
                        SampRec={}
                        SampRec["er_sample_name"]=sample
                        SampRec["er_location_name"]=location_name
                        SampRec["er_citation_names"]="This study"
                        labaz,labdip=pmag.orient(az,pl,or_con) # convert to labaz, labpl
        #
        # parse information common to all orientation methods
        #
                        SampRec["sample_bed_dip"]='%7.1f'%(bed_dip)
                        SampRec["sample_bed_dip_direction"]='%7.1f'%(bed_dip_dir)
                        SampRec["sample_dip"]='%7.1f'%(labdip)
                        SampRec["sample_azimuth"]='%7.1f'%(labaz)
                        if vcc!="":vol=float(vcc)*1e-6 # convert to m^3 from cc
                        SampRec["sample_volume"]='%10.3e'%(vol) # 
                        SampRec["sample_class"]=sclass
                        SampRec["sample_lithology"]=lithology
                        SampRec["sample_type"]=type
                        SampRec["sample_declination_correction"]='%7.1f'%(deccorr)
                        methods=gmeths.split(':')
                        if deccorr!="0":
                            if 'SO-MAG' in methods:del methods[methods.index('SO-MAG')]
                            methods.append('SO-CMD-NORTH')
                        meths=""
                        for meth in methods:meths=meths+meth+":"
                        meths=meths[:-1]
                        SampRec["magic_method_codes"]=meths
                        site=pmag.parse_site(SampRec["er_sample_name"],samp_con,Z) # parse out the site name
                        SampRec["er_site_name"]=site
    #
    # find position data
    #
                    if PosData!=[]:
                        SampRec['sample_height']=""
                        for srec in PosData:
                            if srec['er_site_name']==site:
                                SampRec['sample_height']=srec['sample_height']
                                break
                    SampOut.append(SampRec)
                else:
                    MagRec={}
                    MagRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                    MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                    MagRec["treatment_ac_field"]='0'
                    MagRec["treatment_dc_field"]='0'
                    MagRec["treatment_dc_field_phi"]='0'
                    MagRec["treatment_dc_field_theta"]='0'
                    meas_type="LT-NO"
                    MagRec["measurement_flag"]='g'
                    MagRec["measurement_standard"]='u'
                    MagRec["measurement_number"]='1'
                    MagRec["er_specimen_name"]=specname
                    MagRec["er_sample_name"]=SampRec['er_sample_name']
                    MagRec["er_site_name"]=SampRec['er_site_name']
                    MagRec["er_location_name"]=location_name
                    el,demag=1,''
                    treat=rec[el]
                    if treat[-1]=='C':
                        demag='T'
                    elif treat!='NRM':
                        demag='AF'  
                    el+=1
                    while rec[el]=="":el+=1
                    MagRec["measurement_dec"]=rec[el]
                    cdec=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    MagRec["measurement_inc"]=rec[el]
                    cinc=float(rec[el])
                    el+=1
                    while rec[el]=="":el+=1
                    gdec=rec[el]
                    el+=1
                    while rec[el]=="":el+=1
                    ginc=rec[el]
                    el=skip(2,el,rec) # skip bdec,binc
#                    el=skip(4,el,rec) # skip gdec,ginc,bdec,binc
#                    print 'moment emu: ',rec[el]
                    MagRec["measurement_magn_moment"]='%10.3e'% (float(rec[el])*1e-3) # moment in Am^2 (from emu)
                    MagRec["measurement_magn_volume"]='%10.3e'% (float(rec[el])*1e-3/vol) # magnetization in A/m
                    el=skip(2,el,rec) # skip to xsig
                    MagRec["measurement_sd_x"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
                    el=skip(3,el,rec) # skip to ysig
                    MagRec["measurement_sd_y"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
                    el=skip(3,el,rec) # skip to zsig
                    MagRec["measurement_sd_z"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
                    el+=1 # skip to positions
                    MagRec["measurement_positions"]=rec[el]
                    el=skip(5,el,rec) # skip to date
                    date=rec[el].split()
                    mm=str(months.index(date[0]))
                    if len(mm)==1:
                        mm='0'+str(mm)
                    else:
                        mm=str(mm)
                    dstring=date[2]+':'+mm+':'+date[1]+":"+date[3]
                    MagRec['measurement_date']=dstring
                    MagRec["magic_instrument_codes"]=inst
                    MagRec["er_analyst_mail_names"]="unknown"
                    MagRec["er_citation_names"]="This study"
                    MagRec["magic_method_codes"]=meas_type
                    if demag=="AF":
                        MagRec["treatment_ac_field"]='%8.3e' %(float(treat[:-2])*1e-3) # peak field in tesla
                        meas_type="LT-AF-Z"
                        MagRec["treatment_dc_field"]='0'
                    elif demag=="T":
                        MagRec["treatment_temp"]='%8.3e' % (float(treat[:-1])+273.) # temp in kelvin
                        meas_type="LT-T-Z"
                    MagRec['magic_method_codes']=meas_type
                    MagRecs.append(MagRec) 
    MagOuts=pmag.measurements_methods(MagRecs,noave)
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print "Measurements put in ",meas_file
    pmag.magic_write(samp_file,SampOut,"er_samples")
    print "Sample orientation info  saved in ", samp_file
    print "Good bye"
main()
