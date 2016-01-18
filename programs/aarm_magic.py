#!/usr/bin/env python
import sys
import numpy
import pmagpy.pmag as pmag

def main():
    """
    NAME
        aarm_magic.py

    DESCRIPTION
        Converts AARM  data to best-fit tensor (6 elements plus sigma)
         Original program ARMcrunch written to accomodate ARM anisotropy data
          collected from 6 axial directions (+X,+Y,+Z,-X,-Y,-Z) using the
          off-axis remanence terms to construct the tensor. A better way to
          do the anisotropy of ARMs is to use 9,12 or 15 measurements in
          the Hext rotational scheme.
    
    SYNTAX 
        aarm_magic.py [-h][command line options]

    OPTIONS
        -h prints help message and quits
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, default is aarm_measurements.txt
        -crd [s,g,t] specify coordinate system, requires er_samples.txt file
        -fsa  FILE: specify er_samples.txt file, default is er_samples.txt
        -Fa FILE: specify anisotropy output file, default is arm_anisotropy.txt
        -Fr FILE: specify results output file, default is aarm_results.txt

    INPUT  
        Input for the present program is a series of baseline, ARM pairs.
      The baseline should be the AF demagnetized state (3 axis demag is
      preferable) for the following ARM acquisition. The order of the
      measurements is:
    
           positions 1,2,3, 6,7,8, 11,12,13 (for 9 positions)
           positions 1,2,3,4, 6,7,8,9, 11,12,13,14 (for 12 positions)
           positions 1-15 (for 15 positions)
    """
    # initialize some parameters
    args=sys.argv
    user=""
    meas_file="aarm_measurements.txt"
    samp_file="er_samples.txt"
    rmag_anis="arm_anisotropy.txt"
    rmag_res="aarm_results.txt"
    dir_path='.'
    #
    # get name of file from command line
    #
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-usr" in args:
        ind=args.index("-usr")
        user=sys.argv[ind+1]
    if "-f" in args:
        ind=args.index("-f")
        meas_file=sys.argv[ind+1]
    coord='-1'
    if "-crd" in sys.argv:
        ind=sys.argv.index("-crd")
        coord=sys.argv[ind+1]
        if coord=='s':coord='-1'
        if coord=='g':coord='0'
        if coord=='t':coord='100'
        if "-fsa" in args:
            ind=args.index("-fsa")
            samp_file=sys.argv[ind+1]
    if "-Fa" in args:
        ind=args.index("-Fa")
        rmag_anis=args[ind+1]
    if "-Fr" in args:
        ind=args.index("-Fr")
        rmag_res=args[ind+1]
    meas_file=dir_path+'/'+meas_file
    samp_file=dir_path+'/'+samp_file
    rmag_anis=dir_path+'/'+rmag_anis
    rmag_res=dir_path+'/'+rmag_res
    # read in data
    meas_data,file_type=pmag.magic_read(meas_file)
    meas_data=pmag.get_dictitem(meas_data,'magic_method_codes','LP-AN-ARM','has')
    if file_type != 'magic_measurements':
        print file_type
        print file_type,"This is not a valid magic_measurements file " 
        sys.exit()
    if coord!='-1': # need to read in sample data
        samp_data,file_type=pmag.magic_read(samp_file)
        if file_type != 'er_samples':
            print file_type
            print file_type,"This is not a valid er_samples file " 
            print "Only specimen coordinates will be calculated"
            coord='-1'
    #
    # sort the specimen names
    #
    ssort=[]
    for rec in meas_data:
      spec=rec["er_specimen_name"]
      if spec not in ssort: ssort.append(spec)
    if len(ssort)>1:
        sids=sorted(ssort)
    else:
        sids=ssort
    #
    # work on each specimen
    #
    specimen=0
    RmagSpecRecs,RmagResRecs=[],[]
    while specimen < len(sids):
        s=sids[specimen]
        data=[]
        RmagSpecRec={}
        RmagResRec={}
        method_codes=[]
    #
    # find the data from the meas_data file for this sample
    #
        data=pmag.get_dictitem(meas_data,'er_specimen_name',s,'T')
    #
    # find out the number of measurements (9, 12 or 15)
    #
        npos=len(data)/2
        if npos==9:
        #
        # get dec, inc, int and convert to x,y,z
        #
            B,H,tmpH=pmag.designAARM(npos)  # B matrix made from design matrix for positions
            X=[]
            for rec in data:
                Dir=[]
                Dir.append(float(rec["measurement_dec"]))
                Dir.append(float(rec["measurement_inc"]))
                Dir.append(float(rec["measurement_magn_moment"]))
                X.append(pmag.dir2cart(Dir))
        #
        # subtract baseline and put in a work array
        #
            work=numpy.zeros((npos,3),'f')
            for i in range(npos):
                for j in range(3):
                    work[i][j]=X[2*i+1][j]-X[2*i][j]
        #
        # calculate tensor elements
        # first put ARM components in w vector
        #
            w=numpy.zeros((npos*3),'f')
            index=0
            for i in range(npos):
                for j in range(3):
                    w[index]=work[i][j] 
                    index+=1
            s=numpy.zeros((6),'f') # initialize the s matrix
            for i in range(6):
                for j in range(len(w)):
                    s[i]+=B[i][j]*w[j] 
            trace=s[0]+s[1]+s[2]   # normalize by the trace
            for i in range(6):
                s[i]=s[i]/trace
            a=pmag.s2a(s)
        #------------------------------------------------------------
        #  Calculating dels is different than in the Kappabridge
        #  routine. Use trace normalized tensor (a) and the applied
        #  unit field directions (tmpH) to generate model X,Y,Z
        #  components. Then compare these with the measured values.
        #------------------------------------------------------------
            S=0.
            comp=numpy.zeros((npos*3),'f')
            for i in range(npos):
                for j in range(3):
                    index=i*3+j
                    compare=a[j][0]*tmpH[i][0]+a[j][1]*tmpH[i][1]+a[j][2]*tmpH[i][2]
                    comp[index]=compare
            for i in range(npos*3):
                d=w[i]/trace - comp[i] # del values
                S+=d*d
            nf=float(npos*3-6) # number of degrees of freedom
            if S >0: 
                sigma=numpy.sqrt(S/nf)
            else: sigma=0
            RmagSpecRec["rmag_anisotropy_name"]=data[0]["er_specimen_name"]
            RmagSpecRec["er_location_name"]=data[0]["er_location_name"]
            RmagSpecRec["er_specimen_name"]=data[0]["er_specimen_name"]
            RmagSpecRec["er_sample_name"]=data[0]["er_sample_name"]
            RmagSpecRec["er_site_name"]=data[0]["er_site_name"]
            RmagSpecRec["magic_experiment_names"]=RmagSpecRec["rmag_anisotropy_name"]+":AARM"
            RmagSpecRec["er_citation_names"]="This study"
            RmagResRec["rmag_result_name"]=data[0]["er_specimen_name"]+":AARM"
            RmagResRec["er_location_names"]=data[0]["er_location_name"]
            RmagResRec["er_specimen_names"]=data[0]["er_specimen_name"]
            RmagResRec["er_sample_names"]=data[0]["er_sample_name"]
            RmagResRec["er_site_names"]=data[0]["er_site_name"]
            RmagResRec["magic_experiment_names"]=RmagSpecRec["rmag_anisotropy_name"]+":AARM"
            RmagResRec["er_citation_names"]="This study"
            if "magic_instrument_codes" in data[0].keys():
                RmagSpecRec["magic_instrument_codes"]=data[0]["magic_instrument_codes"]
            else:  
                RmagSpecRec["magic_instrument_codes"]=""
            RmagSpecRec["anisotropy_type"]="AARM"
            RmagSpecRec["anisotropy_description"]="Hext statistics adapted to AARM"
            if coord!='-1': # need to rotate s
    # set orientation priorities
                SO_methods=[]
                for rec in samp_data:
                   if "magic_method_codes" not in rec:
                       rec['magic_method_codes']='SO-NO'
                   if "magic_method_codes" in rec:
                       methlist=rec["magic_method_codes"]
                       for meth in methlist.split(":"):
                           if "SO" in meth and "SO-POM" not in meth.strip():
                               if meth.strip() not in SO_methods: SO_methods.append(meth.strip())
                SO_priorities=pmag.set_priorities(SO_methods,0)
# continue here
                redo,p=1,0
                if len(SO_methods)<=1:
                    az_type=SO_methods[0]
                    orient=pmag.find_samp_rec(RmagSpecRec["er_sample_name"],samp_data,az_type)
                    if orient["sample_azimuth"]  !="": method_codes.append(az_type)
                    redo=0
                while redo==1:
                    if p>=len(SO_priorities):
                        print "no orientation data for ",s
                        orient["sample_azimuth"]=""
                        orient["sample_dip"]=""
                        method_codes.append("SO-NO")
                        redo=0
                    else:
                        az_type=SO_methods[SO_methods.index(SO_priorities[p])]
                        orient=pmag.find_samp_rec(PmagSpecRec["er_sample_name"],samp_data,az_type)
                        if orient["sample_azimuth"]  !="":
                            method_codes.append(az_type)
                            redo=0
                    p+=1
                az,pl=orient['sample_azimuth'],orient['sample_dip']
                s=pmag.dosgeo(s,az,pl) # rotate to geographic coordinates
                if coord=='100': 
                    sampe_bed_dir,sample_bed_dip=orient['sample_bed_dip_direction'],orient['sample_bed_dip']
                    s=pmag.dostilt(s,bed_dir,bed_dip) # rotate to geographic coordinates
            hpars=pmag.dohext(nf,sigma,s)
        #
        # prepare for output
        #
            RmagSpecRec["anisotropy_s1"]='%8.6f'%(s[0])
            RmagSpecRec["anisotropy_s2"]='%8.6f'%(s[1])
            RmagSpecRec["anisotropy_s3"]='%8.6f'%(s[2])
            RmagSpecRec["anisotropy_s4"]='%8.6f'%(s[3])
            RmagSpecRec["anisotropy_s5"]='%8.6f'%(s[4])
            RmagSpecRec["anisotropy_s6"]='%8.6f'%(s[5])
            RmagSpecRec["anisotropy_mean"]='%8.3e'%(trace/3)
            RmagSpecRec["anisotropy_sigma"]='%8.6f'%(sigma)
            RmagSpecRec["anisotropy_unit"]="Am^2"
            RmagSpecRec["anisotropy_n"]='%i'%(npos)
            RmagSpecRec["anisotropy_tilt_correction"]=coord
            RmagSpecRec["anisotropy_F"]='%7.1f '%(hpars["F"]) # used by thellier_gui - must be taken out for uploading
            RmagSpecRec["anisotropy_F_crit"]=hpars["F_crit"] # used by thellier_gui - must be taken out for uploading
            RmagResRec["anisotropy_t1"]='%8.6f '%(hpars["t1"])
            RmagResRec["anisotropy_t2"]='%8.6f '%(hpars["t2"])
            RmagResRec["anisotropy_t3"]='%8.6f '%(hpars["t3"])
            RmagResRec["anisotropy_v1_dec"]='%7.1f '%(hpars["v1_dec"])
            RmagResRec["anisotropy_v2_dec"]='%7.1f '%(hpars["v2_dec"])
            RmagResRec["anisotropy_v3_dec"]='%7.1f '%(hpars["v3_dec"])
            RmagResRec["anisotropy_v1_inc"]='%7.1f '%(hpars["v1_inc"])
            RmagResRec["anisotropy_v2_inc"]='%7.1f '%(hpars["v2_inc"])
            RmagResRec["anisotropy_v3_inc"]='%7.1f '%(hpars["v3_inc"])
            RmagResRec["anisotropy_ftest"]='%7.1f '%(hpars["F"])
            RmagResRec["anisotropy_ftest12"]='%7.1f '%(hpars["F12"])
            RmagResRec["anisotropy_ftest23"]='%7.1f '%(hpars["F23"])
            RmagResRec["result_description"]='Critical F: '+hpars["F_crit"]+';Critical F12/F13: '+hpars["F12_crit"]
            if hpars["e12"]>hpars["e13"]:
                RmagResRec["anisotropy_v1_zeta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v1_zeta_dec"]='%7.1f '%(hpars['v2_dec'])
                RmagResRec["anisotropy_v1_zeta_inc"]='%7.1f '%(hpars['v2_inc'])
                RmagResRec["anisotropy_v2_zeta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v2_zeta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"]='%7.1f '%(hpars['v1_inc'])
                RmagResRec["anisotropy_v1_eta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v1_eta_dec"]='%7.1f '%(hpars['v3_dec'])
                RmagResRec["anisotropy_v1_eta_inc"]='%7.1f '%(hpars['v3_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v3_eta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v3_eta_inc"]='%7.1f '%(hpars['v1_inc'])
            else:
                RmagResRec["anisotropy_v1_zeta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v1_zeta_dec"]='%7.1f '%(hpars['v3_dec'])
                RmagResRec["anisotropy_v1_zeta_inc"]='%7.1f '%(hpars['v3_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v3_zeta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"]='%7.1f '%(hpars['v1_inc'])
                RmagResRec["anisotropy_v1_eta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v1_eta_dec"]='%7.1f '%(hpars['v2_dec'])
                RmagResRec["anisotropy_v1_eta_inc"]='%7.1f '%(hpars['v2_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v2_eta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v2_eta_inc"]='%7.1f '%(hpars['v1_inc'])
            if hpars["e23"]>hpars['e12']:
                RmagResRec["anisotropy_v2_zeta_semi_angle"]='%7.1f '%(hpars['e23'])
                RmagResRec["anisotropy_v2_zeta_dec"]='%7.1f '%(hpars['v3_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"]='%7.1f '%(hpars['v3_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"]='%7.1f '%(hpars['e23'])
                RmagResRec["anisotropy_v3_zeta_dec"]='%7.1f '%(hpars['v2_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"]='%7.1f '%(hpars['v2_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v3_eta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v3_eta_inc"]='%7.1f '%(hpars['v1_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v2_eta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v2_eta_inc"]='%7.1f '%(hpars['v1_inc'])
            else:
                RmagResRec["anisotropy_v2_zeta_semi_angle"]='%7.1f '%(hpars['e12'])
                RmagResRec["anisotropy_v2_zeta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v2_zeta_inc"]='%7.1f '%(hpars['v1_inc'])
                RmagResRec["anisotropy_v3_eta_semi_angle"]='%7.1f '%(hpars['e23'])
                RmagResRec["anisotropy_v3_eta_dec"]='%7.1f '%(hpars['v2_dec'])
                RmagResRec["anisotropy_v3_eta_inc"]='%7.1f '%(hpars['v2_inc'])
                RmagResRec["anisotropy_v3_zeta_semi_angle"]='%7.1f '%(hpars['e13'])
                RmagResRec["anisotropy_v3_zeta_dec"]='%7.1f '%(hpars['v1_dec'])
                RmagResRec["anisotropy_v3_zeta_inc"]='%7.1f '%(hpars['v1_inc'])
                RmagResRec["anisotropy_v2_eta_semi_angle"]='%7.1f '%(hpars['e23'])
                RmagResRec["anisotropy_v2_eta_dec"]='%7.1f '%(hpars['v3_dec'])
                RmagResRec["anisotropy_v2_eta_inc"]='%7.1f '%(hpars['v3_inc'])
            RmagResRec["tilt_correction"]='-1'
            RmagResRec["anisotropy_type"]='AARM'
            RmagResRec["magic_method_codes"]='LP-AN-ARM:AE-H'
            RmagSpecRec["magic_method_codes"]='LP-AN-ARM:AE-H'
            RmagResRec["magic_software_packages"]=pmag.get_version()
            RmagSpecRec["magic_software_packages"]=pmag.get_version()
            specimen+=1
            RmagSpecRecs.append(RmagSpecRec)
            RmagResRecs.append(RmagResRec)
        else:
            print 'skipping specimen ',s,' only 9 positions supported','; this has ',npos
            specimen+=1
    if rmag_anis=="":rmag_anis="rmag_anisotropy.txt"
    pmag.magic_write(rmag_anis,RmagSpecRecs,'rmag_anisotropy')
    print "specimen tensor elements stored in ",rmag_anis
    if rmag_res=="":rmag_res="rmag_results.txt"
    pmag.magic_write(rmag_res,RmagResRecs,'rmag_results')
    print "specimen statistics and eigenparameters stored in ",rmag_res

if __name__ == "__main__":
    main()
