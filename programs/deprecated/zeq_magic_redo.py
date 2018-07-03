#! /usr/bin/env python
from __future__ import print_function
from builtins import range
import sys
import string
import pmagpy.pmag as pmag

def main():
    """
    NAME
        zeq_magic_redo.py
   
    DESCRIPTION
        Calculate principal components through demagnetization data using bounds and calculation type stored in "redo" file
  
    SYNTAX
        zeq_magic_redo.py [command line options]

    OPTIONS
        -h prints help message
        -usr USER:   identify user, default is ""
        -f: specify input file, default is magic_measurements.txt
        -F: specify output file, default is zeq_specimens.txt
        -fre  REDO: specify redo file, default is "zeq_redo"
        -fsa  SAMPFILE: specify er_samples format file, default is "er_samples.txt"
        -A : don't average replicate measurements, default is yes
        -crd [s,g,t] : 
             specify coordinate system [s,g,t]  [default is specimen coordinates]
                 are specimen, geographic, and tilt corrected respectively
             NB: you must have a SAMPFILE in this directory to rotate from specimen coordinates
        -leg:  attaches "Recalculated from original measurements; supercedes published results. " to comment field
    INPUTS
        zeq_redo format file is:
        specimen_name calculation_type[DE-BFL,DE-BFL-A,DE-BFL-O,DE-BFP,DE-FM]  step_min step_max component_name[A,B,C]
    """
    dir_path='.'
    INCL=["LT-NO","LT-AF-Z","LT-T-Z","LT-M-Z"] # looking for demag data
    beg,end,pole,geo,tilt,askave,save=0,0,[],0,0,0,0
    user,doave,comment= "",1,""
    geo,tilt=0,0
    version_num=pmag.get_version()
    args=sys.argv
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    meas_file,pmag_file,mk_file= dir_path+"/"+"magic_measurements.txt",dir_path+"/"+"zeq_specimens.txt",dir_path+"/"+"zeq_redo"
    samp_file,coord=dir_path+"/"+"er_samples.txt",""
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=sys.argv[ind+1]
    if "-A" in args:doave=0
    if "-leg" in args: comment="Recalculated from original measurements; supercedes published results. "
    if "-f" in args:
        ind=args.index("-f")
        meas_file=dir_path+'/'+sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        pmag_file=dir_path+'/'+sys.argv[ind+1]
    if "-fre" in args:
        ind=args.index("-fre")
        mk_file=dir_path+"/"+args[ind+1]
    try:
        mk_f=open(mk_file,'r')
    except:
        print("Bad redo file")
        sys.exit()
    mkspec,skipped=[],[]
    speclist=[]
    for line in mk_f.readlines():
        tmp=line.split()
        mkspec.append(tmp)
        speclist.append(tmp[0])
    if "-fsa" in args:
        ind=args.index("-fsa")
        samp_file=dir_path+'/'+sys.argv[ind+1]
    if "-crd" in args:
        ind=args.index("-crd")
        coord=sys.argv[ind+1]
        if coord=="g":geo,tilt=1,0
        if coord=="t":geo,tilt=1,1
#
# now get down to bidness
    if geo==1:
        samp_data,file_type=pmag.magic_read(samp_file)
        if file_type != 'er_samples':
            print(file_type)
            print("This is not a valid er_samples file ") 
            sys.exit()
    #
    #
    #

    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print(file_type)
        print(file_type,"This is not a valid magic_measurements file ") 
        sys.exit()
    #
    # sort the specimen names
    #
    k = 0
    print('Processing ',len(speclist), ' specimens - please wait')
    PmagSpecs=[]
    while k < len(speclist):
        s=speclist[k]
        recnum=0
        PmagSpecRec={}
        method_codes,inst_codes=[],[]
    # find the data from the meas_data file for this sample
    #
    #  collect info for the PmagSpecRec dictionary
    #
        meas_meth=[]
        spec=pmag.get_dictitem(meas_data,'er_specimen_name',s,'T')   
        if len(spec)==0:
            print('no data found for specimen:  ',s)
            print('delete from zeq_redo input file...., then try again')
        else: 
          for rec in  spec: # copy of vital stats to PmagSpecRec from first spec record in demag block
           skip=1
           methods=rec["magic_method_codes"].split(":")
           if len(set(methods) & set(INCL))>0:
                   PmagSpecRec["er_analyst_mail_names"]=user
                   PmagSpecRec["magic_software_packages"]=version_num
                   PmagSpecRec["er_specimen_name"]=s
                   PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
                   PmagSpecRec["er_site_name"]=rec["er_site_name"]
                   PmagSpecRec["er_location_name"]=rec["er_location_name"]
                   if "er_expedition_name" in list(rec.keys()):PmagSpecRec["er_expedition_name"]=rec["er_expedition_name"]
                   PmagSpecRec["er_citation_names"]="This study"
                   if "magic_experiment_name" not in list(rec.keys()): rec["magic_experiment_name"]=""
                   PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
                   if "magic_instrument_codes" not in list(rec.keys()): rec["magic_instrument_codes"]=""
                   inst=rec['magic_instrument_codes'].split(":")
                   for I in inst:
                       if I not in inst_codes:  # copy over instruments
                           inst_codes.append(I)
                   meths=rec["magic_method_codes"].split(":")
                   for meth in meths:
                       if meth.strip() not in meas_meth:meas_meth.append(meth)
                   if "LP-DIR-AF" in meas_meth or "LT-AF-Z" in meas_meth: 
                       PmagSpecRec["measurement_step_unit"]="T"
                       if "LP-DIR-AF" not in method_codes:method_codes.append("LP-DIR-AF") 
                   if "LP-DIR-T" in meas_meth or "LT-T-Z" in meas_meth: 
                       PmagSpecRec["measurement_step_unit"]="K"
                       if "LP-DIR-T" not in method_codes:method_codes.append("LP-DIR-T") 
                   if "LP-DIR-M" in meas_meth or "LT-M-Z" in meas_meth: 
                       PmagSpecRec["measurement_step_unit"]="J"
                       if "LP-DIR-M" not in method_codes:method_codes.append("LP-DIR-M") 
    #
    #
        datablock,units=pmag.find_dmag_rec(s,spec) # fish out the demag data for this specimen
    #
        if len(datablock) <2 or s not in speclist : 
            k+=1
#            print 'skipping ', s,len(datablock)
        else:
        #
        # find replicate measurements at given treatment step and average them
        #
#            step_meth,avedata=pmag.vspec(data)
#
#            if len(avedata) != len(datablock):
#                if doave==1: 
#                    method_codes.append("DE-VM")
#                    datablock=avedata
        #
        # do geo or stratigraphic correction now
        #
            if geo==1 or tilt==1:
       # find top priority orientation method
                orient,az_type=pmag.get_orient(samp_data,PmagSpecRec["er_sample_name"])
                if az_type not in method_codes:method_codes.append(az_type)
        #
        #  if tilt selected,  get stratigraphic correction
        #
                tiltblock,geoblock=[],[]
                for rec in datablock:
                    if "sample_azimuth" in list(orient.keys()) and orient["sample_azimuth"]!="":
                        d_geo,i_geo=pmag.dogeo(rec[1],rec[2],float(orient["sample_azimuth"]),float(orient["sample_dip"]))
                        geoblock.append([rec[0],d_geo,i_geo,rec[3],rec[4],rec[5]])
                        if tilt==1 and "sample_bed_dip_direction" in list(orient.keys()): 
                            d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,float(orient["sample_bed_dip_direction"]),float(orient["sample_bed_dip"]))
                            tiltblock.append([rec[0],d_tilt,i_tilt,rec[3],rec[4],rec[5]])
                        elif tilt==1:
                            if PmagSpecRec["er_sample_name"] not in skipped:
                                print('no tilt correction for ', PmagSpecRec["er_sample_name"],' skipping....')
                                skipped.append(PmagSpecRec["er_sample_name"])
                    else:
                        if PmagSpecRec["er_sample_name"] not in skipped:
                            print('no geographic correction for ', PmagSpecRec["er_sample_name"],' skipping....')
                            skipped.append(PmagSpecRec["er_sample_name"])
    #
    #	get beg_pca, end_pca, pca
            if PmagSpecRec['er_sample_name'] not in skipped:
                compnum=-1
                for spec in mkspec:
                    if spec[0]==s:
                        CompRec={}
                        for key in list(PmagSpecRec.keys()):CompRec[key]=PmagSpecRec[key]
                        compnum+=1
                        calculation_type=spec[1]
                        beg=float(spec[2])
                        end=float(spec[3])
                        if len(spec)>4:
                            comp_name=spec[4]
                        else:
                            comp_name=string.uppercase[compnum]
                        CompRec['specimen_comp_name']=comp_name
                        if beg < float(datablock[0][0]):beg=float(datablock[0][0])
                        if end > float(datablock[-1][0]):end=float(datablock[-1][0])
                        for l  in range(len(datablock)):
                            if datablock[l][0]==beg:beg_pca=l
                            if datablock[l][0]==end:end_pca=l
                        if geo==1 and tilt==0:
                            mpars=pmag.domean(geoblock,beg_pca,end_pca,calculation_type)
                            if mpars["specimen_direction_type"]!="Error":
                                CompRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                                CompRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                                CompRec["specimen_tilt_correction"]='0'
                        if geo==1 and tilt==1:
                            mpars=pmag.domean(tiltblock,beg_pca,end_pca,calculation_type)
                            if mpars["specimen_direction_type"]!="Error":
                                CompRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                                CompRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                                CompRec["specimen_tilt_correction"]='100'
                        if geo==0 and tilt==0: 
                            mpars=pmag.domean(datablock,beg_pca,end_pca,calculation_type)
                            if mpars["specimen_direction_type"]!="Error":
                                CompRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                                CompRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                                CompRec["specimen_tilt_correction"]='-1'
                        if mpars["specimen_direction_type"]=="Error": 
                            pass
                        else: 
                            CompRec["measurement_step_min"]='%8.3e '%(datablock[beg_pca][0])
                            try:
                                CompRec["measurement_step_max"]='%8.3e '%(datablock[end_pca][0] )
                            except:
                                print('error in end_pca ',PmagSpecRec['er_specimen_name'])
                            CompRec["specimen_correction"]='u'
                            if calculation_type!='DE-FM':
                                CompRec["specimen_mad"]='%7.1f '%(mpars["specimen_mad"])
                                CompRec["specimen_alpha95"]=""
                            else:
                                CompRec["specimen_mad"]=""
                                CompRec["specimen_alpha95"]='%7.1f '%(mpars["specimen_alpha95"])
                            CompRec["specimen_n"]='%i '%(mpars["specimen_n"])
                            CompRec["specimen_dang"]='%7.1f '%(mpars["specimen_dang"])
                            CompMeths=[]
                            for meth in method_codes:
                                if meth not in CompMeths:CompMeths.append(meth)
                            if calculation_type not in CompMeths:CompMeths.append(calculation_type)
                            if geo==1: CompMeths.append("DA-DIR-GEO")
                            if tilt==1: CompMeths.append("DA-DIR-TILT")
                            if "DE-BFP" not in calculation_type:
                                CompRec["specimen_direction_type"]='l'
                            else:
                                CompRec["specimen_direction_type"]='p'
                            CompRec["magic_method_codes"]=""
                            if len(CompMeths) != 0:
                                methstring=""
                                for meth in CompMeths:
                                    methstring=methstring+ ":" +meth
                                CompRec["magic_method_codes"]=methstring.strip(':')
                            CompRec["specimen_description"]=comment
                            if len(inst_codes) != 0:
                                inststring=""
                                for inst in inst_codes:
                                    inststring=inststring+ ":" +inst
                                CompRec["magic_instrument_codes"]=inststring.strip(':')
                            PmagSpecs.append(CompRec)
            k+=1
    pmag.magic_write(pmag_file,PmagSpecs,'pmag_specimens')
    print("Recalculated specimen data stored in ",pmag_file)

if __name__ == "__main__":
    main()
