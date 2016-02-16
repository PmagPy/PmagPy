#! /usr/bin/env python
import sys
import pmagpy.pmag as pmag

def main():
    """
        NAME
            nrm_specimens_magic.py
    
        DESCRIPTION
            converts NRM data in a magic_measurements type file to 
            geographic and tilt corrected data in a pmag_specimens type file
    
        SYNTAX
           nrm_specimens_magic.py [-h][command line options]
        
        OPTIONS:
            -h prints the help message and quits
            -f MFILE: specify input file
            -fsa SFILE: specify er_samples format file [with orientations]
            -F PFILE: specify output file
            -A  do not average replicate measurements
            -crd [g, t]: specify coordinate system ([g]eographic or [t]ilt adjusted)
                 NB: you must have the  SFILE in this directory

        DEFAULTS
            MFILE: magic_measurements.txt
            PFILE: nrm_specimens.txt
            SFILE: er_samples.txt
            coord: specimen
            average replicate measurements?: YES

        
    """
#
#   define some variables
#
    beg,end,pole,geo,tilt,askave,save=0,0,[],0,0,0,0
    samp_file=1
    args=sys.argv
    geo,tilt,orient=0,0,0
    doave=1
    user,comment,doave,coord="","",1,""
    dir_path='.'
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    meas_file=dir_path+"/magic_measurements.txt"
    pmag_file=dir_path+"/nrm_specimens.txt"
    samp_file=dir_path+"/er_samples.txt"
    if "-A" in args: doave=0
    if "-f" in args:
        ind=args.index("-f")
        meas_file=sys.argv[ind+1]
    if "-F" in args:
        ind=args.index("-F")
        pmag_file=dir_path+'/'+sys.argv[ind+1]
    speclist=[]
    if "-fsa" in args:
        ind=args.index("-fsa")
        samp_file=dir_path+'/'+sys.argv[ind+1]
    if "-crd" in args:
        ind=args.index("-crd")
        coord=sys.argv[ind+1]
        if coord=="g":
            geo,orient=1,1
        if coord=="t":
            tilt,orient,geo=1,1,1
#
# read in data
    if samp_file!="":
        samp_data,file_type=pmag.magic_read(samp_file)
        if file_type != 'er_samples':
           print file_type
           print "This is not a valid er_samples file " 
           sys.exit()
        else: print samp_file,' read in with ',len(samp_data),' records'
    else:
        print 'no orientations - will create file in specimen coordinates'
        geo,tilt,orient=0,0,0
    #
    #
    meas_data,file_type=pmag.magic_read(meas_file)
    if file_type != 'magic_measurements':
        print file_type
        print file_type,"This is not a valid magic_measurements file " 
        sys.exit()
    #
    if orient==1:
    # set orientation priorities
        SO_methods=[]
        orientation_priorities={'0':'SO-SUN','1':'SO-GPS-DIFF','2':'SO-SIGHT-BACK','3':'SO-CMD-NORTH','4':'SO-MAG'}
        for rec in samp_data:
           if "magic_method_codes" in rec:
               methlist=rec["magic_method_codes"]
               for meth in methlist.split(":"):
                   if "SO" in meth and "SO-POM" not in meth.strip():
                       if meth.strip() not in SO_methods: SO_methods.append(meth.strip())
    #
    # sort the sample names
    #
    sids=pmag.get_specs(meas_data)
    #
    #
    PmagSpecRecs=[]
    for s in sids:
        skip=0
        recnum=0
        PmagSpecRec={}
        PmagSpecRec["er_analyst_mail_names"]=user
        method_codes,inst_code=[],""
    # find the data from the meas_data file for this sample
    #
    #  collect info for the PmagSpecRec dictionary
    #
        meas_meth=[]
        for rec in  meas_data: # copy of vital stats to PmagSpecRec from first spec record
           if rec["er_specimen_name"]==s: 
               PmagSpecRec["er_specimen_name"]=s
               PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
               PmagSpecRec["er_site_name"]=rec["er_site_name"]
               PmagSpecRec["er_location_name"]=rec["er_location_name"]
               PmagSpecRec["er_citation_names"]="This study"
               PmagSpecRec["magic_instrument_codes"]=""
               if "magic_experiment_name" not in rec.keys():
                   rec["magic_experiment_name"]=""
               if "magic_instrument_codes" not in rec.keys():
                   rec["magic_instrument_codes"]=""
               else:
                   PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
               if len(rec["magic_instrument_codes"]) > len(inst_code):
                   inst_code=rec["magic_instrument_codes"]
                   PmagSpecRec["magic_instrument_codes"]=inst_code  # copy over instruments
               break
    #
    # now check for correct method labels for all measurements
    #
        nrm_data=[]
        for meas_rec in meas_data:
            if meas_rec['er_specimen_name']==PmagSpecRec['er_specimen_name']:
                meths=meas_rec["magic_method_codes"].split(":")
                for meth in meths:
                    if meth.strip() not in meas_meth:meas_meth.append(meth)
                if "LT-NO" in meas_meth:nrm_data.append(meas_rec)
    #
        data,units=pmag.find_dmag_rec(s,nrm_data)
    #
        datablock=data
        #
        # find replicate measurements at NRM step and average them
        #
        Specs=[]
        if doave==1:
            step_meth,avedata=pmag.vspec(data)
            if len(avedata) != len(datablock):
                method_codes.append("DE-VM")
                SpecRec=avedata[0]
                print 'averaging data '
            else: SpecRec=data[0]
            Specs.append(SpecRec)
        else:
            for spec in data:Specs.append(spec)
        for SpecRec in Specs:
        #
        # do geo or stratigraphic correction now
        #
            if geo==1:
        #
        # find top priority orientation method
                redo,p=1,0
                if len(SO_methods)<=1: 
                    az_type=SO_methods[0] 
                    orient=pmag.find_samp_rec(PmagSpecRec["er_sample_name"],samp_data,az_type)
                    if orient["sample_azimuth"]  !="": method_codes.append(az_type)
                    redo=0
                while redo==1:
                    if p>=len(orientation_priorities):
                        print "no orientation data for ",s 
                        skip,redo=1,0
                        break
                    az_type=orientation_priorities[str(p)]
                    orient=pmag.find_samp_rec(PmagSpecRec["er_sample_name"],samp_data,az_type)
                    if orient["sample_azimuth"]  !="":
                        method_codes.append(az_type.strip())
                        redo=0
                    elif orient["sample_azimuth"]  =="":
                        p+=1
            #
            #  if stratigraphic selected,  get stratigraphic correction
            #
                if skip==0 and orient["sample_azimuth"]!="" and orient["sample_dip"]!="":
                    d_geo,i_geo=pmag.dogeo(SpecRec[1],SpecRec[2],orient["sample_azimuth"],orient["sample_dip"])
                    SpecRec[1]=d_geo
                    SpecRec[2]=i_geo
                    if tilt==1 and "sample_bed_dip" in orient.keys() and orient['sample_bed_dip']!="": 
                        d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,orient["sample_bed_dip_direction"],orient["sample_bed_dip"])
                        SpecRec[1]=d_tilt
                        SpecRec[2]=i_tilt
            if skip==0:
                PmagSpecRec["specimen_dec"]='%7.1f ' %(SpecRec[1])
                PmagSpecRec["specimen_inc"]='%7.1f ' %(SpecRec[2])
                if geo==1 and tilt==0:PmagSpecRec["specimen_tilt_correction"]='0'
                if geo==1 and tilt==1: PmagSpecRec["specimen_tilt_correction"]='100'
                if geo==0 and tilt==0: PmagSpecRec["specimen_tilt_correction"]='-1'
                PmagSpecRec["specimen_direction_type"]='l'
                PmagSpecRec["magic_method_codes"]="LT-NO"
                if len(method_codes) != 0:
                    methstring=""
                    for meth in method_codes:
                        methstring=methstring+ ":" +meth
                    PmagSpecRec["magic_method_codes"]=methstring[1:]
                PmagSpecRec["specimen_description"]="NRM data"
                PmagSpecRecs.append(PmagSpecRec)
    pmag.magic_write(pmag_file,PmagSpecRecs,'pmag_specimens')
    print "Data saved in ",pmag_file

if __name__ == "__main__":
    main()
