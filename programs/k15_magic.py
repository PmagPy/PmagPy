#!/usr/bin/env python
#
from __future__ import print_function
import sys
import pmagpy.ipmag as ipmag
import pmagpy.command_line_extractor as extractor

def main():
    """
    NAME
        k15_magic.py

    DESCRIPTION
        converts .k15 format data to magic_measurements  format.
        assums Jelinek Kappabridge measurement scheme
   
    SYNTAX 
        k15_magic.py [-h] [command line options]
    
    OPTIONS
        -h prints help message and quits
        -f KFILE: specify .k15 format input file
        -F MFILE: specify magic_measurements format output file
        -Fsa SFILE, specify er_samples format file for output 
        -Fa AFILE, specify rmag_anisotropy format file for output
        -Fr RFILE, specify rmag_results format file for output
        -loc LOC: specify location name for study
    #-ins INST: specify instrument that measurements were made on # not implemented
        -spc NUM: specify number of digits for specimen ID, default is 0
        -ncn NCOM: specify naming convention (default is #1)
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXXYYY:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
            NB: all others you will have to either customize your
                self or e-mail ltauxe@ucsd.edu for help.


    DEFAULTS
        MFILE: k15_measurements.txt
        SFILE: er_samples.txt
        AFILE: rmag_anisotropy.txt
        RFILE: rmag_results.txt
        LOC: unknown
        INST: unknown
        
    INPUT
      name [az,pl,strike,dip], followed by
      3 rows of 5 measurements for each specimen

    """
    args = sys.argv
    if '-h' in args:
        print(do_help())
        sys.exit()

    #def k15_magic(k15file, specnum=0, sample_naming_con='1', er_location_name="unknown", measfile='magic_measurements.txt', sampfile="er_samples.txt", aniso_outfile='rmag_anisotropy.txt', result_file="rmag_results.txt", input_dir_path='.', output_dir_path='.'):

    dataframe = extractor.command_line_dataframe([['f', True, ''], ['F', False, 'magic_measurements.txt'], ['Fsa', False, 'er_samples.txt'], ['Fa', False, 'rmag_anisotropy.txt'], ['Fr', False, 'rmag_results.txt'], ['spc', False, 0], ['ncn', False, '1'], ['loc', False, 'unknown'], ['WD', False, '.'], ['ID', False, '.']])
    checked_args = extractor.extract_and_check_args(args, dataframe)
    k15file, measfile, sampfile, aniso_outfile, result_file, specnum, sample_naming_con, location_name, output_dir_path, input_dir_path = extractor.get_vars(['f', 'F', 'Fsa', 'Fa', 'Fr', 'spc', 'ncn', 'loc', 'WD', 'ID'], checked_args)
    program_ran, error_message = ipmag.k15_magic(k15file, specnum=specnum, sample_naming_con=sample_naming_con, er_location_name=location_name, measfile=measfile, sampfile=sampfile, aniso_outfile=aniso_outfile, result_file=result_file, input_dir_path=input_dir_path, output_dir_path=output_dir_path)

## assign values to variables based on their associated command-line flag
#fmt, size, plot = get_vars(['fmt', 's', 'sav'], checked_args)
#print "fmt:", fmt, "size:", size, "plot:", plot


    """
#
# initialize some variables
#
    version_num=pmag.get_version()
    specnum=0
    sampfile, measfile="er_samples.txt","k15_measurements.txt"
    anisfile='rmag_anisotropy.txt'
    syn=0
    er_location_name="unknown"
    inst="unknown"
    itilt,igeo,linecnt,key=0,0,0,"" 
    first_save=1
    k15,specnum=[],0 
    citation='This study'
    dir_path='.'
    if '-WD' in sys.argv:
        ind=sys.argv.index('-WD')
        dir_path=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        input_dir_path = sys.argv[ind+1]
    else:
        input_dir_path = dir_path
    output_dir_path = dir_path
# pick off stuff from command line

        
    if '-f' in sys.argv:
        ind=sys.argv.index('-f')
        k15file=sys.argv[ind+1] 
    if '-F' in sys.argv:
        ind=sys.argv.index('-F')
        measfile=sys.argv[ind+1] 
    if '-Fsa' in sys.argv:
        ind=sys.argv.index('-Fsa')
        sampfile=sys.argv[ind+1]
    resfile = pmag.get_named_arg_from_sys('-Fr', 'rmag_results.txt')
    if '-Fa' in sys.argv:
        ind=sys.argv.index('-Fa')
        anisfile=sys.argv[ind+1] 
    if '-loc' in sys.argv:
        ind=sys.argv.index('-loc')
        er_location_name=sys.argv[ind+1] 
    if '-spc' in sys.argv:
        ind=sys.argv.index('-spc')
        specnum=-int(sys.argv[ind+1])
    samp_con,Z="1",""
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if samp_con=='6':
            Samps,filetype=pmag.magic_read(dirpath+'/er_samples.txt')
    sampfile = os.path.join(output_dir_path, sampfile)
    measfile= os.path.join(output_dir_path, measfile)
    anisfile= os.path.join(output_dir_path, anisfile)
    resfile= os.path.join(output_dir_path, resfile)
    k15file = os.path.join(input_dir_path, k15file)
    try:
        SampRecs,filetype=pmag.magic_read(sampfile) # append new records to existing
        samplist=[]
        for samp in SampRecs:
            if samp['er_sample_name'] not in samplist:samplist.append(samp['er_sample_name'])
    except IOError:
        SampRecs=[]
    # measurement directions for Jelinek 1977 protocol:
    Decs=[315,225,180,135,45,90,270,270,270,90,180,180,0,0,0]
    Incs=[0,0,0,0,0,-45,-45,0,45,45,45,-45,-90,-45,45]
    # some defaults to read in  .k15 file format
    # list of measurements and default number of characters for specimen ID
# some magic default definitions
    #
    # read in data
    input=open(k15file,'r')
    MeasRecs,SpecRecs,AnisRecs,ResRecs=[],[],[],[]
    # read in data
    MeasRec,SpecRec,SampRec,SiteRec,AnisRec,ResRec={},{},{},{},{},{}
    for line in input.readlines():
            linecnt+=1
            rec=line.split()
            if linecnt==1:
                MeasRec["magic_method_codes"]=""
                SpecRec["magic_method_codes"]=""
                SampRec["magic_method_codes"]=""
                AnisRec["magic_method_codes"]=""
                SiteRec["magic_method_codes"]=""
                ResRec["magic_method_codes"]=""
                MeasRec["magic_software_packages"]=version_num
                SpecRec["magic_software_packages"]=version_num
                SampRec["magic_software_packages"]=version_num
                AnisRec["magic_software_packages"]=version_num
                SiteRec["magic_software_packages"]=version_num
                ResRec["magic_software_packages"]=version_num
                MeasRec["magic_method_codes"]="LP-X"
                MeasRec["measurement_flag"]="g"
                MeasRec["measurement_standard"]="u"
                MeasRec["er_citation_names"]="This study"
                SpecRec["er_citation_names"]="This study"
                SampRec["er_citation_names"]="This study"
                AnisRec["er_citation_names"]="This study"
                ResRec["er_citation_names"]="This study"
                MeasRec["er_specimen_name"]=rec[0]
                MeasRec["magic_experiment_name"]=rec[0]+":LP-AN-MS"
                AnisRec["magic_experiment_names"]=rec[0]+":AMS"
                ResRec["magic_experiment_names"]=rec[0]+":AMS"
                SpecRec["er_specimen_name"]=rec[0]
                AnisRec["er_specimen_name"]=rec[0]
                SampRec["er_specimen_name"]=rec[0]
                ResRec["rmag_result_name"]=rec[0]
                if specnum!=0: MeasRec["er_sample_name"]=rec[0][:specnum]
                if specnum==0: MeasRec["er_sample_name"]=rec[0]
                SampRec["er_sample_name"]=MeasRec["er_sample_name"]
                SpecRec["er_sample_name"]=MeasRec["er_sample_name"]
                AnisRec["er_sample_name"]=MeasRec["er_sample_name"]
                ResRec["er_sample_names"]=MeasRec["er_sample_name"]
                if samp_con=="6":
                    for samp in Samps:
                        if samp['er_sample_name']==AnisRec["er_sample_name"]:
                            sitename=samp['er_site_name']
                            er_location_name=samp['er_location_name']
                elif samp_con!="":
                    sitename=pmag.parse_site(AnisRec['er_sample_name'],samp_con,Z)
                MeasRec["er_site_name"]=sitename
                MeasRec["er_location_name"]=er_location_name
                SampRec["er_site_name"]=MeasRec["er_site_name"]
                SpecRec["er_site_name"]=MeasRec["er_site_name"]
                AnisRec["er_site_name"]=MeasRec["er_site_name"]
                ResRec["er_site_names"]=MeasRec["er_site_name"]
                SampRec["er_location_name"]=MeasRec["er_location_name"]
                SpecRec["er_location_name"]=MeasRec["er_location_name"]
                AnisRec["er_location_name"]=MeasRec["er_location_name"]
                ResRec["er_location_names"]=MeasRec["er_location_name"]
                if len(rec)>=3: 
                    SampRec["sample_azimuth"],SampRec["sample_dip"]=rec[1],rec[2]
                    az,pl,igeo=float(rec[1]),float(rec[2]),1
                if len(rec)==5: 
                    SampRec["sample_bed_dip_direction"],SampRec["sample_bed_dip"]= '(%7.1f)'%(90.+float(rec[3])),(rec[4])
                    bed_az,bed_dip,itilt,igeo=90.+float(rec[3]),float(rec[4]),1,1
            else: 
                for i in range(5):
                    k15.append(1e-6*float(rec[i])) # assume measurements in micro SI
                if linecnt==4:
                    sbar,sigma,bulk=pmag.dok15_s(k15) 
                    hpars=pmag.dohext(9,sigma,sbar) 
                    MeasRec["treatment_temp"]='%8.3e' % (273) # room temp in kelvin
                    MeasRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
                    for i in range(15):
                        NewMeas=copy.deepcopy(MeasRec)
                        NewMeas["measurement_orient_phi"]='%7.1f' %(Decs[i])
                        NewMeas["measurement_orient_theta"]='%7.1f'% (Incs[i])
                        NewMeas["measurement_chi_volume"]='%12.10f'% (k15[i])
                        NewMeas["measurement_number"]='%i'% (i+1)
                        NewMeas["magic_experiment_name"]=rec[0]+":LP-AN-MS"
                        MeasRecs.append(NewMeas)
                    if SampRec['er_sample_name'] not in samplist:
                        SampRecs.append(SampRec)
                        samplist.append(SampRec['er_sample_name'])
                    SpecRecs.append(SpecRec)
                    AnisRec["anisotropy_type"]="AMS"
                    ResRec["anisotropy_type"]="AMS"
                    AnisRec["anisotropy_s1"]='%12.10f'%(sbar[0])
                    AnisRec["anisotropy_s2"]='%12.10f'%(sbar[1])
                    AnisRec["anisotropy_s3"]='%12.10f'%(sbar[2])
                    AnisRec["anisotropy_s4"]='%12.10f'%(sbar[3])
                    AnisRec["anisotropy_s5"]='%12.10f'%(sbar[4])
                    AnisRec["anisotropy_s6"]='%12.10f'%(sbar[5])
                    AnisRec["anisotropy_mean"]='%12.10f'%(bulk)
                    AnisRec["anisotropy_sigma"]='%12.10f'%(sigma)
                    AnisRec["anisotropy_unit"]='SI'
                    AnisRec["anisotropy_n"]='15'
                    AnisRec["anisotropy_tilt_correction"]='-1'
                    AnisRec["magic_method_codes"]='LP-X:AE-H:LP-AN-MS'
                    AnisRecs.append(AnisRec)
                    ResRec["magic_method_codes"]='LP-X:AE-H:LP-AN-MS'
                    ResRec["anisotropy_tilt_correction"]='-1'
                    ResRec["anisotropy_t1"]='%12.10f'%(hpars['t1'])
                    ResRec["anisotropy_t2"]='%12.10f'%(hpars['t2'])
                    ResRec["anisotropy_t3"]='%12.10f'%(hpars['t3'])
                    ResRec["anisotropy_fest"]='%12.10f'%(hpars['F'])
                    ResRec["anisotropy_ftest12"]='%12.10f'%(hpars['F12'])
                    ResRec["anisotropy_ftest23"]='%12.10f'%(hpars['F23'])
                    ResRec["anisotropy_v1_dec"]='%7.1f'%(hpars['v1_dec'])
                    ResRec["anisotropy_v2_dec"]='%7.1f'%(hpars['v2_dec'])
                    ResRec["anisotropy_v3_dec"]='%7.1f'%(hpars['v3_dec'])
                    ResRec["anisotropy_v1_inc"]='%7.1f'%(hpars['v1_inc'])
                    ResRec["anisotropy_v2_inc"]='%7.1f'%(hpars['v2_inc'])
                    ResRec["anisotropy_v3_inc"]='%7.1f'%(hpars['v3_inc'])
                    ResRec['anisotropy_v1_eta_dec']=ResRec['anisotropy_v2_dec']
                    ResRec['anisotropy_v1_eta_inc']=ResRec['anisotropy_v2_inc']
                    ResRec['anisotropy_v1_zeta_dec']=ResRec['anisotropy_v3_dec']
                    ResRec['anisotropy_v1_zeta_inc']=ResRec['anisotropy_v3_inc']
                    ResRec['anisotropy_v2_eta_dec']=ResRec['anisotropy_v1_dec']
                    ResRec['anisotropy_v2_eta_inc']=ResRec['anisotropy_v1_inc']
                    ResRec['anisotropy_v2_zeta_dec']=ResRec['anisotropy_v3_dec']
                    ResRec['anisotropy_v2_zeta_inc']=ResRec['anisotropy_v3_inc']
                    ResRec['anisotropy_v3_eta_dec']=ResRec['anisotropy_v1_dec']
                    ResRec['anisotropy_v3_eta_inc']=ResRec['anisotropy_v1_inc']
                    ResRec['anisotropy_v3_zeta_dec']=ResRec['anisotropy_v2_dec']
                    ResRec['anisotropy_v3_zeta_inc']=ResRec['anisotropy_v2_inc']
                    ResRec["anisotropy_v1_eta_semi_angle"]='%7.1f'%(hpars['e12'])
                    ResRec["anisotropy_v1_zeta_semi_angle"]='%7.1f'%(hpars['e13'])
                    ResRec["anisotropy_v2_eta_semi_angle"]='%7.1f'%(hpars['e12'])
                    ResRec["anisotropy_v2_zeta_semi_angle"]='%7.1f'%(hpars['e23'])
                    ResRec["anisotropy_v3_eta_semi_angle"]='%7.1f'%(hpars['e13'])
                    ResRec["anisotropy_v3_zeta_semi_angle"]='%7.1f'%(hpars['e23'])
                    ResRec["result_description"]='Critical F: '+hpars["F_crit"]+';Critical F12/F13: '+hpars["F12_crit"]
                    ResRecs.append(ResRec)
                    if igeo==1: 
                        sbarg=pmag.dosgeo(sbar,az,pl) 
                        hparsg=pmag.dohext(9,sigma,sbarg) 
                        AnisRecG=copy.copy(AnisRec)
                        ResRecG=copy.copy(ResRec)
                        AnisRecG["anisotropy_s1"]='%12.10f'%(sbarg[0])
                        AnisRecG["anisotropy_s2"]='%12.10f'%(sbarg[1])
                        AnisRecG["anisotropy_s3"]='%12.10f'%(sbarg[2])
                        AnisRecG["anisotropy_s4"]='%12.10f'%(sbarg[3])
                        AnisRecG["anisotropy_s5"]='%12.10f'%(sbarg[4])
                        AnisRecG["anisotropy_s6"]='%12.10f'%(sbarg[5])
                        AnisRecG["anisotropy_tilt_correction"]='0'
                        ResRecG["anisotropy_tilt_correction"]='0'
                        ResRecG["anisotropy_v1_dec"]='%7.1f'%(hparsg['v1_dec'])
                        ResRecG["anisotropy_v2_dec"]='%7.1f'%(hparsg['v2_dec'])
                        ResRecG["anisotropy_v3_dec"]='%7.1f'%(hparsg['v3_dec'])
                        ResRecG["anisotropy_v1_inc"]='%7.1f'%(hparsg['v1_inc'])
                        ResRecG["anisotropy_v2_inc"]='%7.1f'%(hparsg['v2_inc'])
                        ResRecG["anisotropy_v3_inc"]='%7.1f'%(hparsg['v3_inc'])
                        ResRecG['anisotropy_v1_eta_dec']=ResRecG['anisotropy_v2_dec']
                        ResRecG['anisotropy_v1_eta_inc']=ResRecG['anisotropy_v2_inc']
                        ResRecG['anisotropy_v1_zeta_dec']=ResRecG['anisotropy_v3_dec']
                        ResRecG['anisotropy_v1_zeta_inc']=ResRecG['anisotropy_v3_inc']
                        ResRecG['anisotropy_v2_eta_dec']=ResRecG['anisotropy_v1_dec']
                        ResRecG['anisotropy_v2_eta_inc']=ResRecG['anisotropy_v1_inc']
                        ResRecG['anisotropy_v2_zeta_dec']=ResRecG['anisotropy_v3_dec']
                        ResRecG['anisotropy_v2_zeta_inc']=ResRecG['anisotropy_v3_inc']
                        ResRecG['anisotropy_v3_eta_dec']=ResRecG['anisotropy_v1_dec']
                        ResRecG['anisotropy_v3_eta_inc']=ResRecG['anisotropy_v1_inc']
                        ResRecG['anisotropy_v3_zeta_dec']=ResRecG['anisotropy_v2_dec']
                        ResRecG['anisotropy_v3_zeta_inc']=ResRecG['anisotropy_v2_inc']
                        ResRecG["result_description"]='Critical F: '+hpars["F_crit"]+';Critical F12/F13: '+hpars["F12_crit"]
                        ResRecs.append(ResRecG)
                        AnisRecs.append(AnisRecG)
                    if itilt==1: 
                        sbart=pmag.dostilt(sbarg,bed_az,bed_dip) 
                        hparst=pmag.dohext(9,sigma,sbart)
                        AnisRecT=copy.copy(AnisRec)
                        ResRecT=copy.copy(ResRec)
                        AnisRecT["anisotropy_s1"]='%12.10f'%(sbart[0])
                        AnisRecT["anisotropy_s2"]='%12.10f'%(sbart[1])
                        AnisRecT["anisotropy_s3"]='%12.10f'%(sbart[2])
                        AnisRecT["anisotropy_s4"]='%12.10f'%(sbart[3])
                        AnisRecT["anisotropy_s5"]='%12.10f'%(sbart[4])
                        AnisRecT["anisotropy_s6"]='%12.10f'%(sbart[5])
                        AnisRecT["anisotropy_tilt_correction"]='100'
                        ResRecT["anisotropy_v1_dec"]='%7.1f'%(hparst['v1_dec'])
                        ResRecT["anisotropy_v2_dec"]='%7.1f'%(hparst['v2_dec'])
                        ResRecT["anisotropy_v3_dec"]='%7.1f'%(hparst['v3_dec'])
                        ResRecT["anisotropy_v1_inc"]='%7.1f'%(hparst['v1_inc'])
                        ResRecT["anisotropy_v2_inc"]='%7.1f'%(hparst['v2_inc'])
                        ResRecT["anisotropy_v3_inc"]='%7.1f'%(hparst['v3_inc'])
                        ResRecT['anisotropy_v1_eta_dec']=ResRecT['anisotropy_v2_dec']
                        ResRecT['anisotropy_v1_eta_inc']=ResRecT['anisotropy_v2_inc']
                        ResRecT['anisotropy_v1_zeta_dec']=ResRecT['anisotropy_v3_dec']
                        ResRecT['anisotropy_v1_zeta_inc']=ResRecT['anisotropy_v3_inc']
                        ResRecT['anisotropy_v2_eta_dec']=ResRecT['anisotropy_v1_dec']
                        ResRecT['anisotropy_v2_eta_inc']=ResRecT['anisotropy_v1_inc']
                        ResRecT['anisotropy_v2_zeta_dec']=ResRecT['anisotropy_v3_dec']
                        ResRecT['anisotropy_v2_zeta_inc']=ResRecT['anisotropy_v3_inc']
                        ResRecT['anisotropy_v3_eta_dec']=ResRecT['anisotropy_v1_dec']
                        ResRecT['anisotropy_v3_eta_inc']=ResRecT['anisotropy_v1_inc']
                        ResRecT['anisotropy_v3_zeta_dec']=ResRecT['anisotropy_v2_dec']
                        ResRecT['anisotropy_v3_zeta_inc']=ResRecT['anisotropy_v2_inc']
                        ResRecT["anisotropy_tilt_correction"]='100'
                        ResRecT["result_description"]='Critical F: '+hpars["F_crit"]+';Critical F12/F13: '+hpars["F12_crit"]
                        ResRecs.append(ResRecT)
                        AnisRecs.append(AnisRecT)
                    k15,linecnt=[],0
                    MeasRec,SpecRec,SampRec,SiteRec,AnisRec={},{},{},{},{}
    pmag.magic_write(sampfile,SampRecs,'er_samples')
    pmag.magic_write(anisfile,AnisRecs,'rmag_anisotropy')
    pmag.magic_write(resfile,ResRecs,'rmag_results')
    pmag.magic_write(measfile,MeasRecs,'magic_measurements')
    print "Data saved to: ",sampfile,anisfile,resfile,measfile
"""

def do_help():
    return main.__doc__

if __name__ == "__main__":
    main()
