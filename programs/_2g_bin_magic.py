#!/usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import os
import pmagpy.pmag as pmag

def skip(N,ind,L):
    for b in range(N):
        ind+=1
        while L[ind]=="":ind+=1
    ind+=1
    while L[ind]=="":ind+=1
    return ind
def main(command_line=True, **kwargs):
    """
    NAME
        _2g_bin_magic.py
   
    DESCRIPTION
        takes the binary 2g format magnetometer files and converts them to magic_measurements, er_samples.txt and er_sites.txt file
 
    SYNTAX
        2g_bin_magic.py [command line options]

    OPTIONS
        -f FILE: specify input 2g (binary) file
        -F FILE: specify magic_measurements output file, default is: magic_measurements.txt
        -Fsa FILE: specify output file, default is: er_samples.txt 
        -Fsi FILE: specify output file, default is: er_sites.txt 
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
        Input files are horrible mag binary format (who knows why?)
        Orientation convention:
            [1] Lab arrow azimuth= mag_azimuth; Lab arrow dip=-field_dip
                i.e., field_dip is degrees from vertical down - the hade [default]
            [2] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = -field_dip
                i.e., mag_azimuth is strike and field_dip is hade
            [3] Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
                i.e.,  lab arrow same as field arrow, but field_dip was a hade.
            [4] lab azimuth and dip are same as mag_azimuth, field_dip
            [5] lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
            [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
            [7] all others you will have to either customize your 
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
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
        NB: all others you will have to either customize your
            self or e-mail ltauxe@ucsd.edu for help.

    OUTPUT
            output saved in magic_measurements.txt & er_samples.txt formatted files
              will overwrite any existing files 
    """
    #
    # initialize variables
    #
    mag_file = ''
    specnum=0
    ub_file,samp_file,or_con,corr,meas_file = "","er_samples.txt","3","1","magic_measurements.txt"
    pos_file,site_file="","er_sites.txt"
    noave=1
    args=sys.argv
    bed_dip,bed_dip_dir="",""
    samp_con,Z,average_bedding="2",1,"0"
    meths='FS-FD'
    sclass,lithology,_type="","",""
    user,inst="",""
    DecCorr=0.
    location_name="unknown"
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    gmeths=""
    #
    #
    dir_path='.'
    if command_line:
        if '-WD' in args:
            ind=args.index("-WD")
            dir_path=sys.argv[ind+1]
        if "-h" in args:
            print(main.__doc__)
            return False
        if "-f" in args:
            ind=args.index("-f")
            mag_file=sys.argv[ind+1]
        if "-fpos" in args:
            ind=args.index("-fpos")
            pos_file=sys.argv[ind+1]
        if "-F" in args:
            ind=args.index("-F")
            meas_file=sys.argv[ind+1]
        if "-Fsa" in args:
            ind=args.index("-Fsa")
            samp_file=sys.argv[ind+1]
        if "-Fsi" in args:
            ind=args.index("-Fsi")
            site_file=sys.argv[ind+1]
        if "-ocn" in args:
            ind=args.index("-ocn")
            or_con=sys.argv[ind+1]
        if "-ncn" in args:
            ind=args.index("-ncn")
            samp_con=sys.argv[ind+1]
        if "-mcd" in args:
            ind=args.index("-mcd")
            gmeths=(sys.argv[ind+1])
        if "-loc" in args:
            ind=args.index("-loc")
            location_name=(sys.argv[ind+1])
        if "-spc" in args:
            ind=args.index("-spc")
            specnum=int(args[ind+1])

        if "-ins" in args:
            ind=args.index("-ins")
            inst=args[ind+1]
        if "-a" in args:
            noave=0
        #
        ID = False
        if '-ID' in args:
            ind = args.index('-ID')
            ID = args[ind+1]
        #

    if not command_line:
        dir_path = kwargs.get('dir_path', '.')
        mag_file = kwargs.get('mag_file', '')
        pos_file = kwargs.get('pos_file', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        site_file = kwargs.get('site_file', 'er_sites.txt')
        or_con = kwargs.get('or_con', '3')
        samp_con = kwargs.get('samp_con', '2')
        corr = kwargs.get('corr', '1')
        gmeths = kwargs.get('gmeths', '')
        location_name = kwargs.get('location_name', '')
        specnum = int(kwargs.get('specnum', 0))
        inst = kwargs.get('inst', '')
        noave = kwargs.get('noave', 1) # default is DO average
        ID = kwargs.get('ID', '')

    # format and fix variables acquired from command line args or input with **kwargs
    if specnum!=0:specnum=-specnum

    if ID:
        input_dir_path = ID
    else:
        input_dir_path = dir_path

    if samp_con:
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
        if "6" in samp_con:
            try:
                Samps,file_type=pmag.magic_read(os.path.join(input_dir_path, 'er_samples.txt'))
            except:
                print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
                return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
            if file_type == 'bad_file':
                print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
                return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
                

    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file = os.path.join(input_dir_path, mag_file)
    samp_file = output_dir_path+'/'+samp_file
    site_file = output_dir_path+'/'+site_file
    meas_file= output_dir_path+'/'+meas_file
    samplist=[]
    try:
        Samps,file_type=pmag.magic_read(samp_file)
        for samp in Samps:
            if samp['er_sample_name'] not in samplist: samplist.append(samp['er_sample_name'])
    except:
        Samps=[]
    MagRecs=[]
    try:
        f=open(mag_file,'brU')
        input=str(f.read()).strip("b '")
        f.close()
    except Exception as ex:
        print('ex', ex)
        print("bad mag file")
        return False, "bad mag file"
    firstline,date=1,""
    d=input.split('\\xcd')
    for line in d:
        rec=line.split('\\x00')
        if firstline==1:
            firstline=0
            spec,vol="",1
            el=51
            while line[el:el+1]!="\\": spec=spec+line[el];el+=1
            # check for bad sample name
            test=spec.split('.')
            date=""
            if len(test)>1:
                spec=test[0]
                kk=24
                while line[kk]!='\\x01' and line[kk]!='\\x00':
                    kk+=1
                vcc=line[24:kk]
                el=10
                while rec[el].strip()!='':el+=1
                date,comments=rec[el+7],[]
            else:
                el=9
                while rec[el]!='\\x01':el+=1
                vcc,date,comments=rec[el-3],rec[el+7],[]
            specname=spec.lower()
            print('importing ',specname)
            el+=8
            while rec[el].isdigit()==False:
                comments.append(rec[el])
                el+=1
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
            if rec[el]=='\\x01': 
                bed_dip=180.-bed_dip
                el+=1
                while rec[el]=="":el+=1
            fold_az=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            fold_pl=rec[el]
            el+=1
            while rec[el]=="":el+=1
            if rec[el]!="" and rec[el]!='\\x02' and rec[el]!='\\x01':
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
            if vcc.strip()!="":vol=float(vcc)*1e-6 # convert to m^3 from cc
            SampRec["sample_volume"]='%10.3e'%(vol) # 
            SampRec["sample_class"]=sclass
            SampRec["sample_lithology"]=lithology
            SampRec["sample_type"]=_type
            SampRec["sample_declination_correction"]='%7.1f'%(deccorr)
            methods=gmeths.split(':')
            if deccorr!="0":
                if 'SO-MAG' in methods:del methods[methods.index('SO-MAG')]
                methods.append('SO-CMD-NORTH')
            meths=""
            for meth in methods:meths=meths+meth+":"
            meths=meths[:-1]
            SampRec["magic_method_codes"]=meths
            if int(samp_con)<6 or int(samp_con) == 7: 
                site=pmag.parse_site(SampRec["er_sample_name"],samp_con,Z) # parse out the site name
                SampRec["er_site_name"]=site
            elif len(Samps)>1:
                site,location="",""
                for samp in Samps: 
                    if samp["er_sample_name"] == SampRec["er_sample_name"]:
                        site=samp["er_site_name"]
                        location=samp["er_location_name"]
                        break
                SampRec["er_location_name"]=samp["er_location_name"]
                SampRec["er_site_name"]=samp["er_site_name"]
            if sample not in samplist:
                samplist.append(sample)
                Samps.append(SampRec)
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
#                el=skip(4,el,rec) # skip gdec,ginc,bdec,binc
#                print 'moment emu: ',rec[el]
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
#                    el=skip(5,el,rec) # skip to date
#                    mm=str(months.index(date[0]))
#                    if len(mm)==1:
#                        mm='0'+str(mm)
#                    else:
#                        mm=str(mm)
#                    dstring=date[2]+':'+mm+':'+date[1]+":"+date[3]
#                    MagRec['measurement_date']=dstring
            MagRec["magic_instrument_codes"]=inst
            MagRec["er_analyst_mail_names"]=""
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
    MagOuts, keylist = pmag.fillkeys(MagOuts) 
    pmag.magic_write(meas_file,MagOuts,'magic_measurements')
    print("Measurements put in ",meas_file)
    SampsOut,sampkeys=pmag.fillkeys(Samps)
    pmag.magic_write(samp_file,SampsOut,"er_samples")
    Sites=[]
    for samp in Samps:
        SiteRec={}
        SiteRec['er_site_name']=samp['er_site_name']
        SiteRec['er_location_name']=samp['er_location_name']
        SiteRec['site_definition']='s'
        SiteRec['er_citation_names']='This study'
        if 'sample_class' in list(samp.keys()):SiteRec['site_class']=samp['sample_class']
        if 'sample_lithology' in list(samp.keys()):SiteRec['site_lithology']=samp['sample_lithology']
        if 'sample_type' in list(samp.keys()):SiteRec['site_lithology']=samp['sample_lithology']
        if 'sample_lat' in list(samp.keys()):
            SiteRec['site_lat']=samp['sample_lat']
        else:
            SiteRec['site_lat']="-999"
        if 'sample_lon' in list(samp.keys()):
            SiteRec['site_lon']=samp['sample_lon']
        else:
            SiteRec['site_lon']="-999"
        if 'sample_height' in list(samp.keys()):SiteRec['site_height']=samp['sample_height']
        Sites.append(SiteRec)
    pmag.magic_write(site_file,Sites,'er_sites')
    return True, meas_file

def do_help():
    return main.__doc__

if __name__ == "__main__":
    main()
