#!/usr/bin/env python
from __future__ import print_function
from builtins import input
from builtins import str
import sys
import pmagpy.pmag as pmag
import pmagpy.contribution_builder as cb
import pytz, datetime

def main():
    """
    NAME
        agm_magic.py

    DESCRIPTION
        converts Micromag agm files to magic format

    SYNTAX
        agm_magic.py [-h] [command line options]

    OPTIONS
        -usr USER:   identify user, default is "" - put in quotation marks!
        -bak:  this is a IRM backfield curve
        -f FILE, specify input file, required
        -fsa SAMPFILE, specify er_samples.txt file relating samples, site and locations names,default is none
        -F MFILE, specify magic measurements formatted output file, default is agm_measurements.txt
        -spn SPEC, specimen name, default is base of input file name, e.g. SPECNAME.agm
        -spc NUM, specify number of characters to designate a  specimen, default = 0
        -Fsp SPECFILE : name of er_specimens.txt file for appending data to
             [default: er_specimens.txt]
        -ncn NCON,: specify naming convention: default is #1 below
        -syn SYN,  synthetic specimen name
        -loc LOCNAME : specify location/study name,
             should have either LOCNAME or SAMPFILE (unless synthetic)
        -ins INST : specify which instrument was used (e.g, SIO-Maud), default is ""
        -u units:  [cgs,SI], default is cgs
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            [8] specimen is a synthetic - it has no sample, site, location information
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

    OUTPUT
        MagIC format files: magic_measurements, er_specimens, er_sample, er_site
    """
    citation='This study'
    MeasRecs=[]
    units='cgs'
    meth="LP-HYS"
    version_num=pmag.get_version()
    args=sys.argv
    fmt='old'
    er_sample_name,er_site_name,er_location_name="","",""
    inst=""
    er_location_name="unknown"
    er_synthetic_name=""
    user=""
    er_site_name=""
    dir_path='.'
    dm=3
    if "-WD" in args:
        ind=args.index("-WD")
        dir_path=args[ind+1]
    if "-ID" in args:
        ind = args.index("-ID")
        input_dir_path = args[ind+1]
    else:
        input_dir_path = dir_path
    output_dir_path = dir_path
    specfile = output_dir_path+'/er_specimens.txt'
    output = output_dir_path+"/agm_measurements.txt"
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-bak" in args:
        meth="LP-IRM-DCD"
        output = output_dir_path+"/irm_measurements.txt"
    if "-new" in args: fmt='new'
    if "-usr" in args:
        ind=args.index("-usr")
        user=args[ind+1]
    if '-F' in args:
        ind=args.index("-F")
        output = output_dir_path+'/'+args[ind+1]
    if '-f' in args:
        ind=args.index("-f")
        agm_file= input_dir_path+'/'+args[ind+1]
        er_specimen_name=args[ind+1].split('.')[0]
    else:
        print("agm_file field is required option")
        print(main.__doc__)
        sys.exit()
    if '-Fsp' in args:
        ind=args.index("-Fsp")
        specfile= output_dir_path+'/'+args[ind+1]
    specnum,samp_con,Z=0,'1',1
    if "-spc" in args:
        ind=args.index("-spc")
        specnum=int(args[ind+1])
        if specnum!=0:specnum=-specnum
    if "-spn" in args:
        ind=args.index("-spn")
        er_specimen_name=args[ind+1]
    #elif "-syn" not in args:
    #    print "you must specify a specimen name"
    #    sys.exit()
    if "-syn" in args:
        ind=args.index("-syn")
        er_synthetic_name=args[ind+1]
        er_specimen_name=""
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    if "-fsa" in args:
        ind=args.index("-fsa")
        sampfile = input_dir_path+'/'+args[ind+1]
        Samps,file_type=pmag.magic_read(sampfile)
        print('sample_file successfully read in')
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    if "-ins" in args:
        ind=args.index("-ins")
        inst=args[ind+1]
    if "-u" in args:
        ind=args.index("-u")
        units=args[ind+1]
    dm = pmag.get_named_arg("-DM", 2)
    ErSpecRecs,filetype=pmag.magic_read(specfile)
    ErSpecRec,MeasRec={},{}
    ErSpecRec['er_citation_names']="This study"
    ErSpecRec['er_specimen_name']=er_specimen_name
    ErSpecRec['er_synthetic_name']=er_synthetic_name
    if specnum!=0:
        ErSpecRec["er_sample_name"]=er_specimen_name[:specnum]
    else:
        ErSpecRec["er_sample_name"]=er_specimen_name
    if "-fsa" in args and er_synthetic_name=="":
        for samp in Samps:
            if samp["er_sample_name"] == ErSpecRec["er_sample_name"]:
                ErSpecRec["er_location_name"]=samp["er_location_name"]
                ErSpecRec["er_site_name"]=samp["er_site_name"]
                break
    elif int(samp_con)!=6 and int(samp_con)!=8:
        site=pmag.parse_site(ErSpecRec['er_sample_name'],samp_con,Z)
        ErSpecRec["er_site_name"]=site
        ErSpecRec["er_location_name"]=er_location_name
    ErSpecRec['er_scientist_mail_names']=user.strip()
    insert=1
    for rec in ErSpecRecs:
        if rec['er_specimen_name']==er_specimen_name:
            insert=0
            break
    if insert==1:
        ErSpecRecs.append(ErSpecRec)
        ErSpecRecs,keylist=pmag.fillkeys(ErSpecRecs)
        pmag.magic_write(specfile,ErSpecRecs,'er_specimens')
        print("specimen name put in ",specfile)
    f=open(agm_file,'r')
    Data=f.readlines()
    if "ASCII" not in Data[0]:fmt='new'
    measnum,start=1,""
    if fmt=='new': # new Micromag formatted file
        end=2
        for skip in range(len(Data)):
            line=Data[skip]
            rec=line.split()
            if 'Units' in line:units=rec[-1]
            if "Raw" in rec:
                start=skip+2
            if "Field" in rec and "Moment" in rec and start=="":
                start=skip+2
                break
    else:
        start = 2
        end=1
    for i in range(start,len(Data)-end): # skip header stuff

        MeasRec={}
        for key in list(ErSpecRec.keys()):
            MeasRec[key]=ErSpecRec[key]
        MeasRec['magic_instrument_codes']=inst
        MeasRec['magic_method_codes']=meth
        if 'er_synthetic_name' in list(MeasRec.keys()) and MeasRec['er_synthetic_name']!="":
            MeasRec['magic_experiment_name']=er_synthetic_name+':'+meth
        else:
            MeasRec['magic_experiment_name']=er_specimen_name+':'+meth
        line=Data[i]
        rec=line.split(',') # data comma delimited
        if rec[0]!='\n':
            if units=='cgs':
                field =float(rec[0])*1e-4 # convert from oe to tesla
            else:
                field =float(rec[0]) # field in tesla
            if meth=="LP-HYS":
                MeasRec['measurement_lab_field_dc']='%10.3e'%(field)
                MeasRec['treatment_dc_field']=''
            else:
                MeasRec['measurement_lab_field_dc']=''
                MeasRec['treatment_dc_field']='%10.3e'%(field)
            if units=='cgs':
                MeasRec['measurement_magn_moment']='%10.3e'%(float(rec[1])*1e-3) # convert from emu to Am^2
            else:
                MeasRec['measurement_magn_moment']='%10.3e'%(float(rec[1])) # Am^2
            MeasRec['treatment_temp']='273' # temp in kelvin
            MeasRec['measurement_temp']='273' # temp in kelvin
            MeasRec['measurement_flag']='g'
            MeasRec['measurement_standard']='u'
            MeasRec['measurement_number']='%i'%(measnum)
            measnum+=1
            MeasRec['magic_software_packages']=version_num
            MeasRecs.append(MeasRec)
# now we have to relabel LP-HYS method codes.  initial loop is LP-IMT, minor loops are LP-M  - do this in measurements_methods function
    if meth=='LP-HYS':
        recnum=0
        while float(MeasRecs[recnum]['measurement_lab_field_dc'])<float(MeasRecs[recnum+1]['measurement_lab_field_dc']) and recnum+1<len(MeasRecs): # this is LP-IMAG
            MeasRecs[recnum]['magic_method_codes']='LP-IMAG'
            MeasRecs[recnum]['magic_experiment_name']=MeasRecs[recnum]['er_specimen_name']+":"+'LP-IMAG'
            recnum+=1
#
    if int(dm)==2:
        pmag.magic_write(output,MeasRecs,'magic_measurements')
    else:
        print ('MagIC 3 is not supported yet')
        sys.exit()
        pmag.magic_write(output,MeasRecs,'measurements')

    print("results put in ", output)

if __name__ == "__main__":
    main()
