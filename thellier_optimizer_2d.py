#!/usr/bin/env python

#---------------------------------------------------------------------------
# Author: Ron Shaar
# Revision notes
#
# Rev 1.0 Initial revision August 2012 
#---------------------------------------------------------------------------

import matplotlib
import pylab,scipy,os,time
from pylab import * 
from scipy import *
import  scipy.interpolate
import gzip
import pmag
from scipy.optimize import curve_fit

rcParams.update({"svg.embed_char_paths":False})

class main():
  """
  (See Shaar and Tauxe. 2012b for details and examples)

  GENERAL
  ******
  
  The Thellier_optimizer.py program does the following:
  1) Chooses the optimal temperature bounds in Arai plots of all specimens (Instead of doing it manually).
  2) Calculates the optimal sample's 'best mean'
     (a 'best mean' is the sample mean that passs the criteria with a minimum standard deviation).
  3) Finds the optimal set of selecting criteria that yield minimum scattering of the data within 'test sites'.
     (a 'test site' is a site with more than one sample that should have, by definition, the same paleointensity value)


  Test Sites
  ************
  
  TEST-SITES are sites with at least 2 samples that should have (by assumption) the same paleointensity value.
  Examples for TEST-SITES are contemporaneous cooling units such as pottery/slag samples found in the same archaeological context
  or ontemporaneous lava flows.

  Choosing the appropriate TEST SITES is the most important stage in running the program becasue it includes strict
  assumptions about the data set.

  Use can define TEST-SITES in two ways, using one of the following files 
  1) SITE_SAMPLE_FILE (recommended): a file that contain a list of samples and sites. The format os the file in as er_samples.txt (see details below)
  2) Magic_measurements.txt: The program read the site_name for each sample/specimen directly from the magic_measurements.txt file.
     All sites, in this case, are 'test sites'

  INPUTS (for formats see OPTIONS below):
  *******************************************************

  1) One or more MagIC working directories (MagIC_DIRs):
    Each MagIC directory MUST include magic_measurements.txt. An optional file is rmag_anistropy.txt for anisotropy corrections.
  2) A Fixed_criteria_file (FIXED_CRITERIA_FILE):
    FIXED_CRITERIA_FILE  contains a list of paleointensity parametes that are used as selecting criteria.
    These parameters are set to fixed values during the optimization procedure (while the program looks for the optimal f and SC parameters). 
  3) A list of 'test-sites' and their corresponding sample names (SITE_SAMPLE_FILE):
    If the user does not provide this list, the program uses the er_site_name column in the magic_measurements.txt file to assign specimens to samples and samples to sites,
    and all sites are treated as test-sites (if they contain more than one sample).
  4) A list of optimization_functions (OPTIMIZATION_FUNCTIONS_FILE):
    The program calculates optimization functions for different values of f and SC the values.
    Suggested optimization function:
    (SS_max < <SS_threshold>) and  N:
     which means: setting a threshold for the maximum standard deviation of 'test-sites' (SS_threshold); and choosing f and SC that maximize the total number of samples that passed the criteria (N) 
    

  OUTPUTS:
  ********

  Output files are arranged in folders for simplicity.
  (Notice that output files in the ./run directory can be large and exceed 1GB).
  ./run: A folder with all the outputs of Thellier_auto_interpretation.py (see fiffernt documentation for Thellier_auto_interpretation.py)
  ./optimizer/optimzer.results.txt (A txt file with the optimization results).
      Each line contain: f;SC;'Test-Site' name; A list of all the samples in the 'test-sits' that passed; 'best-mean' of samples; test-site mean; test-site standard deviation.
  ./optimizer/pdf/optimization_function_*.pdf (color-map of the optimization functions values for differnt f, SC- pdf format)
  ./optimizer/svg/optimization_function_*.svg (color-map of the optimization functions values for differnt f, SC - svg format)



  PROCEDURE:
  **********
  A) For each f and SC:
    1) Run Thellier_auto_interpretation.py (see different documentation)
       The procedure of the Thellier_auto_interpretation.py is as follow:
       1.1) For each specimen:
            Loop through all the possible temperature bounds in the Arai plot,
            and save only the interpretation (temperature bounds) that pass the selecting criteria ('acceptable interpretations')
       1.2) For each sample:
            finds the 'best sample mean' by selecting from all the 'acceptable interpretations'
            the choice that yields a minimum standard deviation of the sample mean.
  B) For each f and SC:
       Screen out the 'best sample mean' that pass the criteria for samples.
       Caluclate the values of optimization functions using the 'best sample mean' of samples from the TEST SITES.


  OPTIONS:
  *******
   -WD: (Optional)
                      A list of pathes do all the MagIC working directiories
                      example:
                      -WD ~/Documents/Cyprus,./my_files/Timna
  

   -optimize_by_site_name: (optional)
                      "er_sample_name" and "er_site_same" columns in magic_measurements.txt
                      are used to define 'test sites'
                      if the other option (-optimize_by_list) is not used, then this is the default.

  -optimize_by_list <site-sample_file>: (optional)
                      The format of the site-sample_file is similar to er_samples.txt
                      A tab delimited text that contains a list of samples and test-sites:
                        first line is:tab   er_samples
                        next line is header: er_sample_name	er_site_name  comments
                        and next line contains the information
                        if the line"exclude" appears in the 'comments' column then the sample is exlcuded from the optimization calculation.

  -criteria_fixed_paremeters <fixed_criteria_file>: (Required)
                      A file with the fixed parameters values that are not included in the optimization algorithm.                   
                      The format is similar to pmag_criteria.txt (tab delimited text).
                      The following parameters must appear:
                        specimen_int_mad, specimen_n, specimen_int_ptrm_n,specimen_max_f_diff
                        sample_int_n, sample_int_sigma_uT, sample_int_sigma_perc

                      ??RON?? Otherwise use the default:
                      ??RON?? specimen_int_mad=5; specimen_n=3; specimen_int_ptrm_n=2
                      ??RON?? sample_int_n=3,sample_int_sigma_uT=6?,sample_int_sigma_perc=10?
                      
  -optimization_functions <optimization_function_file> (Required)
                      Each line in this file includes an optimization function (can be more than one)
                      The optimization function uses the following parameters:
                      N = N_samples: Total number of samples in the study that pass the criteria
                      SS_max = Site-Scatter-Max: The site with the maximum standrad deviation
                      SS_std = Site-Scatter-standrad-deviation. Site-Scatter is the standrad deviation of each site.
                               SS_std is the standrad deviation of all the Site-Scatter
                      Examples:
                      N 
                      SS_max
                      SS_std
                      N/SS_max
                      if SS_max>6:N

                      The functions [N] and [if SS_max>XXX(value is microT) :N] are recommended.
  

  -beta_range <start,end,step>: (Required)
                      The range of beta parameters used for the optimization.
                      example (recommended): -beta_range 0.04,0.30,0.02
                      
  -f_range <start,end,step>: (Required)
                      The range of FRAC parameter used for the optimization. f should be larger than 0.75
                      exaple (recommended): -f_range 0.76,0.92,0.02


  Example (Cyprus Data):
  
  Thellier_optimizer.1.0.py  -optimize_by_list  optimizer_site_samples.txt  -WD Cyprus -criteria_fixed_paremeters pmag_fixed_criteria.txt -optimization_functions optimization_functions.txt -beta_range 0.08,0.32,0.02 -f_range 0.76,0.94,0.02 > optimizer.log
                      
  """


  #=============================================================
  # definition
  #=============================================================

##  def find_key(Dict, sample):
##      """return the key of dictionary dic given the value"""
##      for site in Dict.keys():
##        if sample in Dict[site]:
##          found_site=site
##      return found_site

  def tan_h(x, a, b):
      return a*tanh(b*x)



  def find_sample_min_std (Intensities):


      def find_close_value( LIST, value):
          diff=inf
          for a in LIST:
              if abs(value-a)<diff:
                  diff=abs(value-a)
                  result=a
          return(result)


      Best_array=[]
      best_array_std=inf
      Best_array_tmp=[]
      Best_interpretations={}
      Best_interpretations_tmp={}
      
      for this_specimen in Intensities.keys():
          for value in Intensities[this_specimen]:
              Best_interpretations_tmp[this_specimen]=value
              Best_array_tmp=[value]
              all_other_specimens=Intensities.keys()
              all_other_specimens.remove(this_specimen)
              
              for other_specimen in all_other_specimens:
                  closest_value=find_close_value(Intensities[other_specimen], value)
                  Best_array_tmp.append(closest_value)
                  Best_interpretations_tmp[other_specimen]=closest_value                   

              if std(Best_array_tmp)<best_array_std:
                  Best_array=Best_array_tmp
                  best_array_std=std(Best_array)
                  Best_interpretations=Best_interpretations_tmp
                  Best_interpretations_tmp={}
      return Best_interpretations,mean(Best_array),std(Best_array)



  def find_sample_min_max_interpretation (Intensities,acceptance_criteria):

  ##      Min_array=[]
  ##      Min_array_std=inf
  ##      Min_array_tmp=[]
  ##      Min_interpretations={}
  ##      Min_interpretations_tmp={}

        
        tmp_Intensities={}
        Acceptable_sample_min,Acceptable_sample_max="",""
        for this_specimen in Intensities.keys():
          B_list=Intensities[this_specimen]
          if len(B_list)>0:
              B_list.sort()
              tmp_Intensities[this_specimen]=B_list

        # find min values
        while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
            B_tmp=[]
            B_tmp_min=1e10
            for sample in tmp_Intensities.keys():
                B_tmp.append(min(tmp_Intensities[sample]))
                if min(tmp_Intensities[sample])<B_tmp_min:
                    sample_to_remove=sample
                    B_tmp_min=min(tmp_Intensities[sample])
            if std(B_tmp)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                Acceptable_sample_min=mean(B_tmp)
                break
            else:
                tmp_Intensities[sample_to_remove].remove(B_tmp_min)
                if len(tmp_Intensities[sample_to_remove])==0:
                    break
                    
        #print "Intensities",Intensities        
        #print "Ron Check mi min sample"
        #print "min:",tmp_Intensities,B_tmp,Acceptable_sample_min
        #print "----"

        #--------------------
        tmp_Intensities={}
        for this_specimen in Intensities.keys():
          B_list=Intensities[this_specimen]
          if len(B_list)>0:
              B_list.sort()
              tmp_Intensities[this_specimen]=B_list

        # find max values
        counter=0
        while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
            counter+=1
            B_tmp=[]
            B_tmp_max=0
            #print "iteration %i"%counter
            #print tmp_Intensities
            for sample in tmp_Intensities.keys():
                B_tmp.append(max(tmp_Intensities[sample]))
                if max(tmp_Intensities[sample])>B_tmp_max:
                    sample_to_remove=sample
                    B_tmp_max=max(tmp_Intensities[sample])
            if std(B_tmp)<acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<acceptance_criteria["sample_int_sigma_perc"]:
                Acceptable_sample_max=mean(B_tmp)
                break
            else:
                print "removing sample %s"%sample_to_remove
                tmp_Intensities[sample_to_remove].remove(B_tmp_max)
                if len(tmp_Intensities[sample_to_remove])<1:
                    break
        #print "Ron Check mi max sample"
        #print "max:",tmp_Intensities,B_tmp,Acceptable_sample_max
        #print "======"

        if Acceptable_sample_min=="" or Acceptable_sample_max=="":
            print "-W- Cant calculate acceptable sample bounds"
            return(0.,0.)
        return(Acceptable_sample_min,Acceptable_sample_max)     




  #=============================================================
  #
  #  Main
  #
  #=============================================================



  if '-h' in sys.argv: # check if help is needed
      print main.__doc__
      sys.exit() # graceful quit


  if '-WD' in sys.argv:
      ind=sys.argv.index("-WD")
      #dir_pathes_string=sys.argv[ind+1]
      #dir_pathes=dir_pathes_string.split(',')
      WD=sys.argv[ind+1]
  else:
##      dir_pathes=["./"]
##      dir_pathes_string = "-WD ./"
      WD="./"

      
  if '-optimize_by_site_name' in sys.argv:
      OPTIMIZE_BY_SITE_NAME=True
  else:
      OPTIMIZE_BY_SITE_NAME=False

      
  if '-optimize_by_list' in sys.argv:
      ind=sys.argv.index("-optimize_by_list")
      sites_sample_file=sys.argv[ind+1]
      OPTIMIZE_BY_SITE_NAME=False
      OPTIMIZE_BY_LIST=True
  else:
      OPTIMIZE_BY_LIST=False

  if '-criteria_fixed_paremeters' in sys.argv:
      ind=sys.argv.index("-criteria_fixed_paremeters")
      criteria_fixed_paremeters_file=sys.argv[ind+1]
  else:
      criteria_fixed_paremeters_file="/optimizer/pmag_fixed_criteria.txt"
      
  if '-optimization_functions' in sys.argv:
      ind=sys.argv.index("-optimization_functions")    
      optimization_function_file=sys.argv[ind+1]
  else:
      print "Missing optimization functions file . Exiting"
      exit()
      
  if '-beta_range' in sys.argv:
      ind=sys.argv.index("-beta_range")
      beta_range=sys.argv[ind+1]
      beta_range=beta_range.split(',')
      beta_range=arange(float(beta_range[0]),float(beta_range[1])+float(beta_range[2]),float(beta_range[2]))
  else:
      print "Missing beta_range range. Exiting"
      exit()

  if '-f_range' in sys.argv:
      ind=sys.argv.index("-f_range")
      f_range=sys.argv[ind+1]
      f_range=f_range.split(',')
      f_range=arange(float(f_range[0]),float(f_range[1])+float(f_range[2]),float(f_range[2]))
  else:
      print "Missing FRAC range. Exiting"
      exit()
    
  if "-forced_interpretation" in sys.argv:
    ind=sys.argv.index("-forced_interpretation")
    forced_interpretation_file=sys.argv[ind+1]
    Forced_interpretation_string="-forced_interpretation forced_interpretation_file"
  else:
    Forced_interpretation_string=""    


  if "-sample_mean_type" in sys.argv:
      sample_mean_types_string=sys.argv.index("-sample_mean_type")
      sample_mean_types=sys.argv[ind+1]
      sample_mean_types=sample_mean_types.split(',')

      if "STDEV-OPT" in sample_mean_types:
         DO_SAMPLE_BEST_MEAN=True
      else:
         DO_SAMPLE_BEST_MEAN=False
         
      if "BS" in sample_mean_types:
         DO_SAMPLE_BOOTSTRP_MEAN=True
      else:
         DO_SAMPLE_BOOTSTRP_MEAN=False
         
      if "BS-PAR" in sample_mean_types:
         DO_SAMPLE_PARA_BOOTSTRP_MEAN=True
      else:               
         DO_SAMPLE_PARA_BOOTSTRP_MEAN=False

  else:
     sample_mean_types_string=""
     DO_SAMPLE_BEST_MEAN,DO_SAMPLE_BOOTSTRP_MEAN,DO_SAMPLE_PARA_BOOTSTRP_MEAN= True,True,True
     

#===========================================================================================================


  #------------------------------------------------
  # Initialize values
  #------------------------------------------------


  start_time = time.time()

  accept_new_parameters={}
  criteria_specimen_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_scat',
                 'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
  criteria_sample_list=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']
  
  high_threshold_value_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
  low_threshold_value_list=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

  #------------------------------------------------
  # Write header to thellier_optimizer_master_file
  #------------------------------------------------

  thellier_optimizer_master_file=gzip.open(WD+'/optimizer/thellier_optimizer_interpretation_log.txt.gz', 'wb')

  String="er_specimen_name\t"+"t_min\t"+"t_max_\t"+"specimen_int_uT\t"
  for key in criteria_specimen_list:
      String=String+key+"\t"
  thellier_optimizer_master_file.write(String[:-1]+"\n")
  String=""
    
  #------------------------------------------------
  # Write header to optimizer output
  #------------------------------------------------

  Optimizer_results_file=open(WD + "/optimizer/optimzer_results.txt",'w')
  String="specimen_frac\tspecimen_beta\tTest_Site\tSamples\tB_samples\tTest Site Mean\tTest Site STD\tTest Site [STD/Mean]\n"
  Optimizer_results_file.write(String)

#===========================================================================================================        

  #------------------------------------------------
  # read fixed criteria file
  # Format is as pmag_criteria.txt
  # Required parameters:
  # specimen_n; specimen_int_ptrm_n; specimen_int_mad 
  # sample_int_sigma_uT ; sample_int_sigma_perc ; sample_int_n ; sample_int_n_outlier_check
  #------------------------------------------------



  # initialize to null value

  accept_new_parameters['specimen_n']=0
  accept_new_parameters['specimen_int_ptrm_n']=0
  accept_new_parameters['specimen_f']=0.
  accept_new_parameters['specimen_fvds']=0.
  accept_new_parameters['specimen_frac']=0
  accept_new_parameters['specimen_gap_max']=0.0
  accept_new_parameters['specimen_b_beta']=100000
  accept_new_parameters['specimen_dang']=100000
  accept_new_parameters['specimen_drats']=100000
  accept_new_parameters['specimen_int_mad']=100000
  accept_new_parameters['specimen_md']=100000
  accept_new_parameters['specimen_g']=0
  accept_new_parameters['specimen_q']=0
  accept_new_parameters['specimen_scat']=False

  # initialize to null value sample
  accept_new_parameters['sample_int_n']=0
  accept_new_parameters['sample_int_sigma_uT']=10000
  accept_new_parameters['sample_int_sigma_perc']=10000
  accept_new_parameters['sample_int_interval_uT']=10000
  accept_new_parameters['sample_int_interval_perc']=10000
  accept_new_parameters['sample_int_n_outlier_check']=10000
  
  # A list of all acceptance criteria used by program

  print "-I read ceriteria_file "
 
  fin=open(WD+ "/" + criteria_fixed_paremeters_file,'rU')
  fin.readline()
  criteria_keys=fin.readline()
  criteria_keys=criteria_keys.strip('\n').split('\t')
  for line in fin.readlines():
      line=line[:-1].split('\t')
      accepet_tmp={}
      for i in range(len(line)):
        if criteria_keys[i]=="specimen_scat" and  ( str(line[i]) == "True" or line[i] == True or str(line[i]) == "TRUE" or line[i]=='1' ):
          accept_new_parameters['specimen_scat']=True
        if criteria_keys[i]=="specimen_scat" and  ( str(line[i]) == "False" or line[i] == False or str(line[i]) == "FALSE" or line[i]=='0' ):
          accept_new_parameters['specimen_scat']=False          
        if 'pmag_criteria_code' in criteria_keys and "IE-SPEC" in line and "specimen" in criteria_keys[i] :
          accept_new_parameters[criteria_keys[i]]=float(line[i])
        if 'pmag_criteria_code' in criteria_keys and "IE-SAMP" in line and "sample" in criteria_keys[i] :
          accept_new_parameters[criteria_keys[i]]=float(line[i])
        if 'pmag_criteria_code' not in criteria_keys:
            if "sample" in criteria_keys[i] or "specimen" in criteria_keys[i]:
              if criteria_keys[i]!="specimen_scat":
                accept_new_parameters[criteria_keys[i]]=float(line[i])
  fin.close()

  for key in criteria_specimen_list + criteria_sample_list:
    print "-I- threshold value %s:"%(key),accept_new_parameters[key]
  #------------------------------------------------
  # read Optimization functions
  #------------------------------------------------

  optimization_functions=[]
  fin=open(WD + "/" + optimization_function_file,'rU')
  for line in fin.readlines():
    optimization_functions.append(line.strip('\n'))


  #------------------------------------------------
  # read sites name from magic_measurement file
  # or from sites_sample_file (user defined site-samples file)
  #------------------------------------------------

  sites_samples={}

  if OPTIMIZE_BY_SITE_NAME:
    pathes=dir_pathes
  elif OPTIMIZE_BY_LIST:
    pathes=["./"]
    
  for dir_path in pathes:
    if OPTIMIZE_BY_SITE_NAME:
      fin=open(dir_path+"magic_measurements.txt",'rU')
    if OPTIMIZE_BY_LIST:
      fin=open(sites_sample_file,'rU')            
    line=fin.readline()
    line=fin.readline()
    header=line.strip('\n').split('\t')
    for line in fin.readlines():
      tmp_data={}
      line=line.strip('\n').split('\t')
      for i in range(len(line)):
        tmp_data[header[i]]=line[i]
      sample=tmp_data['er_sample_name']
      site=tmp_data['er_group_name']
      if "comments" in tmp_data.keys() and "exclude" in tmp_data['comments']:
        print "-W- WARNING: ignoring sample %s"%sample
        continue
      if site not in sites_samples.keys():
        sites_samples[site]=[]
      if sample not in sites_samples[site]:
        sites_samples[site].append(sample)


  #------------------------------------------------
  # Read magic measurement file and sort to blocks
  #------------------------------------------------

  # All data information is stored in Data[secimen]={}
  Data={}
  Data_hierarchy={}

  # read magic file  
  meas_data,file_type=pmag.magic_read(WD+"/"+"magic_measurements.txt")
  print "-I- Read magic file %s" %(WD+"/"+"magic_measurements.txt")

  # get list of unique specimen names
  
  CurrRec=[]
  sids=pmag.get_specs(meas_data) # samples ID's
  
  for s in sids:

      if s not in Data.keys():
          Data[s]={}
          Data[s]['datablock']=[]
          Data[s]['trmblock']=[]

      zijdblock,units=pmag.find_dmag_rec(s,meas_data)
      Data[s]['zijdblock']=zijdblock

      
  for rec in meas_data:
      s=rec["er_specimen_name"]
      sample=rec["er_sample_name"]
      if sample not in Data_hierarchy.keys():
          Data_hierarchy[sample]=[]
      if s not in Data_hierarchy[sample]:
          Data_hierarchy[sample].append(s)
      
      if "magic_method_codes" not in rec.keys():
          rec["magic_method_codes"]=""
      #methods=rec["magic_method_codes"].split(":")
      if "LP-PI-TRM" in rec["magic_method_codes"]:
          Data[s]['datablock'].append(rec)
      if "LP-TRM" in rec["magic_method_codes"]:
          Data[s]['trmblock'].append(rec)
              
  specimens=Data.keys()
  specimens.sort()

  #------------------------------------------------
  # Read anisotropy file from rmag_anisotropy.txt
  #------------------------------------------------

  anis_data=[]
  try:
      anis_data,file_type=pmag.magic_read(WD+'/rmag_anisotropy.txt')
      print "-I- Anisotropy data read  %s/from rmag_anisotropy.txt"%WD
  except:
      print "-W- WARNING cant find rmag_anistropy in working directory"
      
  for AniSpec in anis_data:
      s=AniSpec['er_specimen_name']

      if s not in Data.keys():
          print "-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !"%s
          continue
      if 'AniSpec' in Data[s].keys():
          print "-E- ERROR: more than one anisotropy data for specimen %s Fix it!"%s
      Data[s]['AniSpec']=AniSpec
      
  #------------------------------------------------
  # Calculate Non Linear TRM parameters
  # Following Shaar et al. (2010):
  #
  # Procedure:
  #
  # A) If there are only 2 NLT measurement: C
  #
  #   Cant do NLT correctio procedure (few data points).
  #   Instead, check the different in the ratio (M/B) in the two measurements.
  #   slop_diff = max(first slope, second slope)/min(first slope, second slope)
  #   if: 1.1 > slop_diff > 1.05 : WARNING
  #   if: > slop_diff > 1s.1 : WARNING
  #
  # B) If there are at least 3 NLT measurement:
  #
  # 1) Read the NLT measurement file
  #   If there is no baseline measurement in the NLT experiment:
  #    then take the baseline from the zero-field step of the IZZI experiment.
  #
  # 2) Fit tanh function of the NLT measurement normalized by M[oven field]
  #   M/M[oven field] = alpha * tanh (beta*B)
  #   alpha and beta are used for the Banc calculation using equation (3) in Shaar et al. (2010):
  #   Banc= tanh^-1[(b*Fa)/alpha]/beta where Fa  is anistropy correction factor and 'b' is the Arai plot slope.
  #
  # 3) If best fit function algorithm does not converge, check NLT data using option (A) above.
  #    If 
  #
  #------------------------------------------------



  # Searching and sorting NLT Data 

  for s in specimens:
      datablock = Data[s]['datablock']
      trmblock = Data[s]['trmblock']

      if len(trmblock)<2:
          continue

      B_NLT,M_NLT=[],[]

      # find temperature of NLT acquisition
      NLT_temperature=float(trmblock[0]['treatment_temp'])
      
      # search for baseline in the Data block
      M_baseline=0.
      for rec in datablock:
          if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field'])==0:
             M_baseline=float(rec['measurement_magn_moment'])
             
      # search for Blab used in the IZZI experiment (need it for the following calculation)
      for rec in datablock:  
          if float(rec['treatment_dc_field'])!=0:
              labfield=float(rec['treatment_dc_field'])

      for rec in trmblock:

          # if there is a baseline in TRM block, then use it 
          if float(rec['treatment_dc_field'])==0:
              M_baseline=float(rec['measurement_magn_moment'])
          B_NLT.append(float(rec['treatment_dc_field']))
          M_NLT.append(float(rec['measurement_magn_moment']))
          
      print "-I- Found %i NLT datapoints for specimen %s: B="%(len(B_NLT),s),array(B_NLT)*1e6

      #substitute baseline
      M_NLT=array(M_NLT)-M_baseline

      # calculate M/B ratio for each step, and compare them
      # If cant do NLT correction: check a difference in M/B ratio
      # > 5% : WARNING
      # > 10%: ERROR           

      slopes=M_NLT/B_NLT

      if len(trmblock)==2:
          if max(slopes)/min(slopes)<1.05:
              print "-I- 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] < 1.05."%s         
          elif max(slopes)/min(slopes)<1.1:
              print "-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements are required  !" %(s,max(slopes)/min(slopes))
              print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
          else:
              print "-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements are required  !" %(s,max(slopes)/min(slopes))
              print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
              
      # NLT procedure following Shaar et al (2010)        
      
      if len(trmblock)>2:
          B_NLT=append([0.],B_NLT)
          M_NLT=append([0.],M_NLT)
          
          try:
              # First try to fit tanh function (add point 0,0 in the begining)
              alpha_0=max(M_NLT)
              beta_0=2e4
              popt, pcov = curve_fit(tan_h, B_NLT, M_NLT,p0=(alpha_0,beta_0))
              M_lab=popt[0]*math.tanh(labfield*popt[1])

              # Now  fit tanh function to the normalized curve
              M_NLT_norm=M_NLT/M_lab
              popt, pcov = curve_fit(tan_h, B_NLT, M_NLT_norm,p0=(popt[0]/M_lab,popt[1]))
              Data[s]['NLT_parameters']=(popt, pcov)
              print "-I- calculated tanh parameters for specimen %s"%s
                              
          except RuntimeError:
              print "-W- WARNING: Cant fit tanh function to NLT data specimen %s. Ignore NLT data for specimen %s. Instead check [max(M/B)]/ [min(M/B)] "%(s,s)
              print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
              
              # Cant do NLT correction. Instead, check a difference in M/B ratio
              # The maximum difference allowd is 5%
              # if difference is larger than 5%: WARNING            
              
              if max(slopes)/min(slopes)<1.05:
                  print "-I- 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] < 1.05."%s         
              elif max(slopes)/min(slopes)<1.1:
                  print "-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements are required  !" %(s,max(slopes)/min(slopes))
                  print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
              else:
                  print "-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements are required  !" %(s,max(slopes)/min(slopes))
                  print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
              
          
  print "-I- Done calculating non linear TRM parameters"
            
  #------------------------------------------------
  # sort Arai block
  #------------------------------------------------


  for s in specimens:
    datablock = Data[s]['datablock']
    zijdblock=Data[s]['zijdblock']
    if len(datablock) <4:
       print "-E- ERROR: skipping specimen %s, data block is too small - moving forward "%s
       continue

    
    araiblock,field=pmag.sortarai(datablock,s,0)
    Data[s]['araiblok']=araiblock
    Data[s]['pars']={}
    Data[s]['pars']['lab_dc_field']=field
    Data[s]['pars']['er_specimen_name']=s   
    
    first_Z=araiblock[0]

    if len(araiblock[0])!= len(araiblock[1]):
       print "-E- ERROR: unequal length of Z steps and I steps. Check specimen %s"% s
       print "-E- Program is exiting now until it fixed...sorry"    

    #--------------------------------------------------------------
    # collect all zijderveld data to array and calculate VDS
    #--------------------------------------------------------------

    z_temperatures=[row[0] for row in zijdblock]
    zdata=[]
    vector_diffs=[]
    NRM=zijdblock[0][3]

    for k in range(len(zijdblock)):
        DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
        cart=pmag.dir2cart(DIR)
        zdata.append(array([cart[0],cart[1],cart[2]]))
        if k>0:
            vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))
    vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector of the vds
    vds=sum(vector_diffs)  # vds calculation       
    zdata=array(zdata)

    Data[s]['vector_diffs']=array(vector_diffs)
    Data[s]['vds']=vds
    Data[s]['zdata']=zdata
    Data[s]['z_temp']=z_temperatures
    
    #--------------------------------------------------------------
    # collect all Arai plot data points to array 
    #--------------------------------------------------------------

    # collect Arai data points
    zerofields,infields=araiblock[0],araiblock[1]

    Data[s]['NRMS']=zerofields
    Data[s]['PTRMS']=infields
    
    x_Arai,y_Arai=[],[] # all the data points               
    t_Arai=[]
    steps_Arai=[]              

    infield_temperatures=[row[0] for row in infields]
    zerofield_temperatures=[row[0] for row in zerofields]

    # check a correct order of tempertures
    PROBLEM=False
    for i in range (2,len(infield_temperatures)):
        if float(infield_temperatures[i])<float(infield_temperatures[i-1]):
            PROBLEM=True
            break
    if PROBLEM:
        print "-E ERROR: wrong order of temperatures specimen %s. Skipping specimen!"%s
        del(Data[s])
        #specimens.remove(s)
        continue

    # check a correct order of tempertures
    PROBLEM=False
    for i in range (2,len(zerofield_temperatures)):
        if float(zerofield_temperatures[i])<float(zerofield_temperatures[i-1]):
            PROBLEM=True
            break
    if PROBLEM:
        print "-E ERROR: wrong order of temperatures specimen %s. Skipping specimen!"%s
        del(Data[s])
        #specimens.remove(s)
        continue



    for k in range(len(zerofields)):                  
      index_infield=infield_temperatures.index(zerofields[k][0])
      x_Arai.append(infields[index_infield][3]/NRM)
      y_Arai.append(zerofields[k][3]/NRM)
      t_Arai.append(zerofields[k][0])
      if zerofields[k][4]==1:
        steps_Arai.append('ZI')
      else:
        steps_Arai.append('IZ')        
    x_Arai=array(x_Arai)
    y_Arai=array(y_Arai)
    
    Data[s]['x_Arai']=x_Arai
    Data[s]['y_Arai']=y_Arai
    Data[s]['t_Arai']=t_Arai
    Data[s]['steps_Arai']=steps_Arai


    #--------------------------------------------------------------
    # collect all pTRM check to array 
    #--------------------------------------------------------------

    ptrm_checks = araiblock[2]
    zerofield_temperatures=[row[0] for row in zerofields]

    x_ptrm_check,y_ptrm_check,ptrm_checks_temperatures=[],[],[]

    for k in range(len(ptrm_checks)):
      if ptrm_checks[k][0] in zerofield_temperatures:
        index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
        x_ptrm_check.append(ptrm_checks[k][3]/NRM)
        y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
        ptrm_checks_temperatures.append(ptrm_checks[k][0])
      
    x_ptrm_check=array(x_ptrm_check)  
    ptrm_check=array(y_ptrm_check)
    ptrm_checks_temperatures=array(ptrm_checks_temperatures)
    Data[s]['x_ptrm_check']=x_ptrm_check
    Data[s]['y_ptrm_check']=y_ptrm_check
    Data[s]['ptrm_checks_temperatures']=ptrm_checks_temperatures


    #--------------------------------------------------------------
    # collect tail checks 
    #--------------------------------------------------------------


    ptrm_tail = araiblock[3]
    #print ptrm_tail
    x_tail_check,y_tail_check=[],[]

    for k in range(len(ptrm_tail)):                  
      index_infield=infield_temperatures.index(ptrm_tail[k][0])
      x_tail_check.append(infields[index_infield][3]/NRM)
      y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)

    x_tail_check=array(x_tail_check)  
    y_tail_check=array(y_tail_check)

    Data[s]['x_tail_check']=x_tail_check
    Data[s]['y_tail_check']=y_tail_check

  print "-I- Done reading and sorting measurements files"
  

  #--------------------------------------------------------------    
  # looping through all data points in the Arai plot
  # and calculate all the parameters except scat (because beta is needed for that)
  #--------------------------------------------------------------

  print "-I- Now looping through all data points in the Arai plot"

  thellier_optimizer_master_table={}
  
  n_min=int(accept_new_parameters['specimen_n'])

  specimens=Data.keys()
  specimens.sort()
  
  for s in specimens:
    thellier_optimizer_master_table[s]=[]
    
    datablock = Data[s]['datablock']
    t_Arai=Data[s]['t_Arai']
    x_Arai=Data[s]['x_Arai']
    y_Arai=Data[s]['y_Arai']
    x_tail_check=Data[s]['x_tail_check']
    y_tail_check=Data[s]['y_tail_check']

    zijdblock=Data[s]['zijdblock']        
    z_temperatures=Data[s]['z_temp']
    
    if len(t_Arai)<4:
      print "-W- skipping specimen %s"%s
      continue
    for start in range (0,len(t_Arai)-n_min+1):
      for end in range (start+n_min-1,len(t_Arai)):
        pars={}
        pars['lab_dc_field']=Data[s]['pars']['lab_dc_field']
        pars['er_specimen_name']=s

        
        tmin=t_Arai[start]
        tmax=t_Arai[end]

        #-------------------------------------------------
        # calualte PCA of the zerofield steps
        # MAD calculation following Kirschvink (1980)
        # DANG following Tauxe and Staudigel (2004)
        #-------------------------------------------------               
         
        pars["measurement_step_min"]=float(tmin)
        pars["measurement_step_max"]=float(tmax)

        if  tmin not in z_temperatures:
          print "-E- ERROR: specimen %s temperature %f apears in Arai plot but not in Zijderveld plot"%(s,tmin)
          continue
        if  tmax not in z_temperatures:
          print "-E- ERROR: specimen %s temperature %f apears in Arai plot but not in Zijderveld plot"%(s,tmax)
          continue

        zstart=z_temperatures.index(tmin)
        zend=z_temperatures.index(tmax)

        if zend-zstart<3:
          continue
        zdata_segment=Data[s]['zdata'][zstart:zend+1]

        #  PCA in 2 lines
        M = (zdata_segment-mean(zdata_segment.T,axis=1)).T # subtract the mean (along columns)
        [eigenvalues,eigenvectors] = linalg.eig(cov(M)) # attention:not always sorted

        # sort eigenvectors and eigenvalues
        eigenvalues=list(real(eigenvalues))
        tmp=[0,1,2]
        t1=max(eigenvalues);index_t1=eigenvalues.index(t1);tmp.remove(index_t1)
        t3=min(eigenvalues);index_t3=eigenvalues.index(t3);tmp.remove(index_t3)
        index_t2=tmp[0];t2=eigenvalues[index_t2]
        v1=real(array(eigenvectors[:,index_t1]))
        v2=real(array(eigenvectors[:,index_t2]))
        v3=real(array(eigenvectors[:,index_t3]))

        # chech if v1 is the "right" polarity
        cm=array(mean(zdata_segment.T,axis=1)) # center of mass
        v1_plus=v1*sqrt(sum(cm**2))
        v1_minus=v1*-1*sqrt(sum(cm**2))
        test_v=zdata_segment[0]-zdata_segment[-1]

        if sqrt(sum((v1_minus-test_v)**2)) < sqrt(sum((v1_plus-test_v)**2)):
         DIR_PCA=pmag.cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=pmag.cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=degrees(arctan(sqrt((t2+t3)/t1)))

        # DANG Tauxe and Staudigel 2004
        DANG=degrees( arccos( ( dot(cm, best_fit_vector) )/( sqrt(sum(cm**2)) * sqrt(sum(best_fit_vector**2)))))


        # best fit PCA direction
        pars["specimen_dec"] =  DIR_PCA[0]
        pars["specimen_inc"] =  DIR_PCA[1]
        pars["specimen_zij_v1_cart"] =  best_fit_vector

        # MAD Kirschvink (1980)
        pars["specimen_int_mad"]=MAD
        pars["specimen_dang"]=DANG


        #-------------------------------------------------
        # York regresssion (York, 1967) following Coe (1978)
        # calculate f,fvds,
        # modified from pmag.py
        #-------------------------------------------------               

        x_Arai_segment= x_Arai[start:end+1]
        y_Arai_segment= y_Arai[start:end+1]

        x_Arai_mean=mean(x_Arai_segment)
        y_Arai_mean=mean(y_Arai_segment)

        # equations (2),(3) in Coe (1978) for b, sigma
        n=end-start+1
        x_err=x_Arai_segment-x_Arai_mean
        y_err=y_Arai_segment-y_Arai_mean

        # York b
        york_b=-1* sqrt( sum(y_err**2) / sum(x_err**2) )

        # york sigma
        york_sigma= sqrt ( (2 * sum(y_err**2) - 2*york_b*sum(x_err*y_err)) / ( (n-2) * sum(x_err**2) ) )

        # beta  parameter                
        beta_Coe=abs(york_sigma/york_b)

        # y_T is the intercept of the extrepolated line
        # through the center of mass (see figure 7 in Coe (1978))
        y_T = y_Arai_mean - york_b* x_Arai_mean

        # calculate the extarplated data points for f and fvds
        # (see figure 7 in Coe (1978))

        x_tag=(y_Arai_segment - y_T ) / york_b
        y_tag=york_b*x_Arai_segment + y_T

        # intersect of the dashed square and the horizontal dahed line  next to delta-y-5 in figure 7, Coe (1978)
        x_prime=(x_Arai_segment+x_tag) / 2
        y_prime=(y_Arai_segment+y_tag) / 2

        f_Coe=abs((y_prime[0]-y_prime[-1])/y_T)

        f_vds=abs((y_prime[0]-y_prime[-1])/Data[s]['vds'])

        g_Coe= 1 - (sum((y_prime[:-1]-y_prime[1:])**2) / sum((y_prime[:-1]-y_prime[1:]))**2 )

        q_Coe=abs(york_b)*f_Coe*g_Coe/york_sigma

        
        pars['specimen_n']=end-start+1
        pars["specimen_b"]=york_b
        pars["specimen_YT"]=y_T       
        pars["specimen_b_sigma"]=york_sigma
        pars["specimen_b_beta"]=beta_Coe
        pars["specimen_f"]=f_Coe
        pars["specimen_fvds"]=f_vds
        pars["specimen_g"]=g_Coe
        pars["specimen_q"]=q_Coe

        pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]

        #-------------------------------------------------
        # pTRM checks:
        # DRAT ()
        # and
        # DRATS (Tauxe and Staudigel 2004)
        #-------------------------------------------------

        x_ptrm_check_in_segment,y_ptrm_check_in_segment,x_Arai_compare=[],[],[]
        
        for k in range(len(Data[s]['ptrm_checks_temperatures'])):
          if Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
            if Data[s]['ptrm_checks_temperatures'][k]<=pars["measurement_step_max"]:
              x_ptrm_check_in_segment.append(Data[s]['x_ptrm_check'][k])
              y_ptrm_check_in_segment.append(Data[s]['y_ptrm_check'][k])
              x_Arai_index=t_Arai.index(Data[s]['ptrm_checks_temperatures'][k])
              x_Arai_compare.append(x_Arai[x_Arai_index])
        x_ptrm_check_in_segment=array(x_ptrm_check_in_segment)  
        y_ptrm_check_in_segment=array(y_ptrm_check_in_segment)
        x_Arai_compare=array(x_Arai_compare)
                                                               
                                  
        DRATS=100*(abs(sum(x_ptrm_check_in_segment-x_Arai_compare))/(x_Arai[end]))
        int_ptrm_n=len(x_ptrm_check_in_segment)
        if int_ptrm_n > 0:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=DRATS
        else:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=-1

        #-------------------------------------------------
        # Tail check MD
        #-------------------------------------------------
           
        pars['specimen_md']=-1

        # TO DO !


        #-------------------------------------------------  
        # Calculate the new FRAC parameter (Shaar and Tauxe, 2012).
        # also check that the 'gap' between consecutive measurements is less than 0.5(VDS)
        #
        #-------------------------------------------------  

        vector_diffs=Data[s]['vector_diffs']
        vector_diffs_segment=vector_diffs[zstart:zend]
        FRAC=sum(vector_diffs_segment)/Data[s]['vds']
        max_FRAC_gap=max(vector_diffs_segment/sum(vector_diffs_segment))

        pars['specimen_frac']=FRAC
        pars['specimen_gap_max']=max_FRAC_gap


        # avoid pathological cases when specimen_frac is very small (less than 10%)
        if pars['specimen_frac'] < 0.1:
          continue
        #-------------------------------------------------            
        # Calculate anistropy correction factor
        #-------------------------------------------------            

        if "AniSpec" in Data[s].keys():
           AniSpec=Data[s]['AniSpec']
           AniSpecRec=pmag.doaniscorr(pars,AniSpec)
           pars["AC_specimen_dec"]=AniSpecRec["specimen_dec"]
           pars["AC_specimen_inc"]=AniSpecRec["specimen_inc"]
           pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
           pars["AC_specimen_correction_factor"]=float(pars["AC_specimen_int"])/float(pars["specimen_int"])
           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6

        else:
           pars["AC_specimen_correction_factor"]=1.0
           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6

           
        #-------------------------------------------------                    
        # NLT and anisotropy correction together in one equation
        # See Shaar et al (2010), Equation (3)
        #-------------------------------------------------

        if 'NLT_parameters' in Data[s].keys():

           alpha=Data[s]['NLT_parameters'][0][0]
           beta=Data[s]['NLT_parameters'][0][1]
           b=float(pars["specimen_b"])
           Fa=pars["AC_specimen_correction_factor"]

           if ((abs(b)*Fa)/alpha) <1.0:
               Banc_NLT=math.atanh( ((abs(b)*Fa)/alpha) ) / beta
               pars["NLTC_specimen_int"]=Banc_NLT
               pars["specimen_int_uT"]=Banc_NLT*1e6

               if "AC_specimen_int" in pars.keys():
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["AC_specimen_int"])
               else:                       
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["specimen_int"])
           else:
               print "-W- WARNING: problematic NLT mesurements specimens %s. Cant do NLT calculation. check data"%s
               pars["NLT_specimen_correction_factor"]=-999
        else:
           pars["NLT_specimen_correction_factor"]=-999

           

        #--------------------------------------------------------------
        # Save all the interpretation into file
        #--------------------------------------------------------------
        String=s+"\t"+"%s\t"%pars["measurement_step_min"]+"%s\t"%pars["measurement_step_max"]+"%s\t"%pars["specimen_int_uT"]
        for key in criteria_specimen_list:
           if key != "specimen_scat":
               String=String+"%f"%pars[key]+"\t"
           #elif key=="specimen_scat":
           #    String=String+"%s"%pars[key]+"\t"
           #elif  key=="specimen_n" or  key=="specimen_int_ptrm_n":
           #    String=String+"%i"%pars[key]+"\t"
               
        thellier_optimizer_master_file.write(String[:-1]+"\n")
        thellier_optimizer_master_table[s].append(pars)

  thellier_optimizer_master_file.write( "Done loopping through all points in Arai plot. All specimens\n")
  time_1= time.time() 
  runtime_sec = time_1 - start_time
  m, s = divmod(runtime_sec, 60)
  h, m = divmod(m, 60)
  thellier_optimizer_master_file.write( "-I- runtime from start (hh:mm:ss)" + "%d:%02d:%02d" % (h, m, s))       
        


  #-------------------------------------------------                     
  # Looping through all f and beta, and save the 'acceptable interpretation
  # i.e. the interpretation that pass the criteria 
  #-------------------------------------------------                     

  Optimizer_data={}
  Optimizer_STDEV_OPT={}
  #print "-I- f_range",f_range
  #print "-I- beta_range",beta_range
  
  for frac in f_range:
    for beta in beta_range:

      accept_new_parameters['specimen_b_beta']=beta
      accept_new_parameters['specimen_frac']=frac
      Key="%.2f,%.2f"%(float(frac),float(beta))

      Optimizer_data[Key]={}
      
      for sample in Data_hierarchy.keys():
        for specimen in Data_hierarchy[sample]:

          if specimen not in specimens:
            continue
          
          for pars in thellier_optimizer_master_table[specimen]:
            Fail=False
            for key in high_threshold_value_list:
              if float(pars[key])>float(accept_new_parameters[key]):
                thellier_optimizer_master_file.write(  "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,key))
                Fail=True
            if Fail: continue
            for key in low_threshold_value_list:
              if float(pars[key])<float(accept_new_parameters[key]):
                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,key))
                Fail=True
            if Fail: continue
            #-------------------------------------------------                     
            # Calculate the new 'beta box' parameter using beta
            # all datapoints, pTRM checks, and tail-checks, should be inside a "beta box"
            # For definition of "beta box" see Shaar and Tauxe (2012)
            #-------------------------------------------------                     


            datablock = Data[specimen]['datablock']
            t_Arai=Data[specimen]['t_Arai']
            x_Arai=Data[specimen]['x_Arai']
            y_Arai=Data[specimen]['y_Arai']
            x_tail_check=Data[specimen]['x_tail_check']
            y_tail_check=Data[specimen]['y_tail_check']


            start=t_Arai.index(pars["measurement_step_min"])
            end=t_Arai.index(pars["measurement_step_max"])

            x_Arai_segment= x_Arai[start:end+1]
            y_Arai_segment= y_Arai[start:end+1]

            x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end=[],[]
            x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
            
            for k in range(len(Data[specimen]['ptrm_checks_temperatures'])):
              if Data[specimen]['ptrm_checks_temperatures'][k] in t_Arai:
                if Data[specimen]['ptrm_checks_temperatures'][k]<=pars["measurement_step_max"]:
                  x_ptrm_check_in_0_to_end.append(Data[specimen]['x_ptrm_check'][k])
                  y_ptrm_check_in_0_to_end.append(Data[specimen]['y_ptrm_check'][k])
                  if Data[specimen]['ptrm_checks_temperatures'][k]>=pars["measurement_step_min"]:
                    x_ptrm_check_in_start_to_end.append(Data[specimen]['x_ptrm_check'][k])
                    y_ptrm_check_in_start_to_end.append(Data[specimen]['y_ptrm_check'][k])

                  
                  #x_Arai_index=t_Arai.index(Data[specimen]['ptrm_checks_temperatures'][k])
            x_ptrm_check_in_0_to_end=array(x_ptrm_check_in_0_to_end)  
            y_ptrm_check_in_0_to_end=array(y_ptrm_check_in_0_to_end)
            x_ptrm_check_in_start_to_end=array(x_ptrm_check_in_start_to_end)
            y_ptrm_check_in_start_to_end=array(y_ptrm_check_in_start_to_end)
            #-----------------------

            b=pars['specimen_b']
            cm_x=mean(array(x_Arai_segment))
            cm_y=mean(array(y_Arai_segment))
            a=cm_y-b*cm_x

            # lines with slope = slope +/- 2*(specimen_b_beta)

            b_beta_threshold=accept_new_parameters['specimen_b_beta']

            two_sigma_beta_threshold=2*b_beta_threshold
            two_sigma_slope_threshold=abs(two_sigma_beta_threshold*b)
                 
            # a line with a  shallower  slope  (b + 2*beta*b) passing through the center of mass
            b1=b+two_sigma_slope_threshold
            a1=cm_y-b1*cm_x

            # bounding line with steeper  slope (b - 2*beta*b) passing through the center of mass
            b2=b-two_sigma_slope_threshold
            a2=cm_y-b2*cm_x

            # lower bounding line of the 'beta box'
            slop1=a1/((a2/b2))
            intercept1=a1

            # higher bounding line of the 'beta box'
            slop2=a2/((a1/b1))
            intercept2=a2       

            #pars['specimen_scat_bounding_line_high']=[intercept2,slop2]
            #pars['specimen_scat_bounding_line_low']=[intercept1,slop1]
            
            # check if the Arai data points are in the 'box'

            x_Arai_segment=array(x_Arai_segment)
            y_Arai_segment=array(y_Arai_segment)

            # the two bounding lines
            ymin=intercept1+x_Arai_segment*slop1
            ymax=intercept2+x_Arai_segment*slop2

            # arrays of "True" or "False"
            check_1=y_Arai_segment>ymax
            check_2=y_Arai_segment<ymin

            # check if at least one "True" 
            if (sum(check_1)+sum(check_2))>0:
             thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on scat\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
             continue 


            if len(x_ptrm_check_in_start_to_end) > 0:

        
              # the two bounding lines
              ymin=intercept1+x_ptrm_check_in_start_to_end*slop1
              ymax=intercept2+x_ptrm_check_in_start_to_end*slop2

              # arrays of "True" or "False"
              check_1=y_ptrm_check_in_start_to_end>ymax
              check_2=y_ptrm_check_in_start_to_end<ymin

              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on ptrm scat\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
                continue
              
            #------------
            if sample not in  Optimizer_data[Key].keys():
              Optimizer_data[Key][sample]={}
            if specimen not in Optimizer_data[Key][sample].keys():
              Optimizer_data[Key][sample][specimen]=[]
            Optimizer_data[Key][sample][specimen].append(pars['specimen_int_uT'])
            thellier_optimizer_master_file.write( "-I- key= %s specimen %s pass tmin,tmax= (%.0f,%.0f) "%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))

            

      
  #-------------------------------------------------                     
  # Looping through all f and beta, and save the best sample means
  # that pass the criteria
  # i.e. STDEV_OPT
  #-------------------------------------------------                     

  for frac in f_range:
    for beta in beta_range:
      Key="%.2f,%.2f"%(float(frac),float(beta))
      Optimizer_STDEV_OPT[Key]={}
      #--------------------------------------------------------------
      # check for outlier specimens in each sample
      #--------------------------------------------------------------
      for sample in Optimizer_data[Key].keys():
        exclude_specimens_list=[]   
        if len(Optimizer_data[Key][sample].keys())>=float(accept_new_parameters['sample_int_n_outlier_check']):            
            all_specimens=Optimizer_data[Key][sample].keys()
            for specimen in all_specimens:
                B_min_array,B_max_array=[],[]
                for specimen_b in all_specimens:
                    if specimen_b==specimen: continue
                    B_min_array.append(min(Optimizer_data[Key][sample][specimen_b]))
                    B_max_array.append(max(Optimizer_data[Key][sample][specimen_b]))
                if max(Optimizer_data[Key][sample][specimen]) < mean(B_min_array) - 2*std(B_min_array) \
                   or min(Optimizer_data[Key][sample][specimen]) > mean(B_max_array) + 2*std(B_max_array):
                    if specimen not in exclude_specimens_list:
                        exclude_specimens_list.append(specimen)
                        
            if len(exclude_specimens_list)>1:
                #print "-I- checking now if any speimens to exlude due to B_max<average-2*sigma or B_min > average+2*sigma sample %s" %s
                thellier_optimizer_master_file.write( "-I- check outlier sample =%s; frac=%f,beta=%f,: more than one specimen can be excluded.\n"%(sample,frac,beta))
                exclude_specimens_list=[]

            if len(exclude_specimens_list)==1:
                #print exclude_specimens_list
                exclude_specimen=exclude_specimens_list[0]
                del Optimizer_data[Key][sample][exclude_specimen]
                thellier_optimizer_master_file.write( "-W- WARNING: frac=%f,beta=%f, specimen %s is exluded from sample %s because is is an outlier.\n "%(frac,beta,exclude_specimens_list[0],sample))

        #--------------------------------------------------------------
        # find the best mean
        #--------------------------------------------------------------


        if len(Optimizer_data[Key][sample].keys())>=accept_new_parameters['sample_int_n']:
           Best_interpretations,best_mean,best_std=find_sample_min_std(Optimizer_data[Key][sample])
           sample_acceptable_min,sample_acceptable_max = find_sample_min_max_interpretation (Optimizer_data[Key][sample],accept_new_parameters)
           sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
           sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)
           if best_std <= (accept_new_parameters['sample_int_sigma_uT']) or 100*(best_std/best_mean) <= accept_new_parameters['sample_int_sigma_perc']:
             if sample_int_interval_uT <= accept_new_parameters['sample_int_interval_uT'] or sample_int_interval_perc <= accept_new_parameters['sample_int_interval_perc']:
             
               #thellier_optimizer_master_file.write( "-I- 'best mean interpretations' frac=%f; beta=%f;  sample %s: "%(frac,beta,sample))
               #String="" 
               #for BB in Best_interpretations:
               #  String=String + "%.2f,"%(BB)
               thellier_optimizer_master_file.write( String+"\n")                                      
               thellier_optimizer_master_file.write( "-I- 'best mean' pass. frac=%f; beta=%f  sample %s: mean=%f, std=%f, accepted_interval=%f \n"%(frac,beta,sample,best_mean,best_std,sample_int_interval_uT))

               #if Key not in Optimizer_STDEV_OPT.keys():
               #  Optimizer_STDEV_OPT[Key]={}
               if sample not in Optimizer_STDEV_OPT[Key]:
                 Optimizer_STDEV_OPT[Key][sample]={}          
               Optimizer_STDEV_OPT[Key][sample]['sample_int_uT']=best_mean
               Optimizer_STDEV_OPT[Key][sample]['sample_int_sigma_uT']=best_std
               Optimizer_STDEV_OPT[Key][sample]['sample_int_sigma_perc']=100*(best_std/best_mean)
               Optimizer_STDEV_OPT[Key][sample]['sample_int_interval_uT']=best_std
               Optimizer_STDEV_OPT[Key][sample]['sample_int_interavl_perc']=100*(best_std/best_mean)
             else:
               thellier_optimizer_master_file.write("-I- 'best mean' fail on accepted_interval. frac=%f; beta=%f  sample %s: mean=%f, std=%f, accepted_interval=%f \n"%(frac,beta,sample,best_mean,best_std,sample_int_interval_uT))
           else:
             thellier_optimizer_master_file.write("-I- 'best mean' fail on sigma. frac=%f; beta=%f  sample %s: mean=%f, std=%f, accepted_interval=%f \n"%(frac,beta,sample,best_mean,best_std,sample_int_interval_uT))
             

  #------------------------------------------------------
  # Calcualte the optimization function for different frac and beta
  #------------------------------------------------------

  optimization_functions_matrices={}
    
  for function in optimization_functions:
    optimization_functions_matrices[function]=zeros((len(beta_range),len(f_range)))

  f_index=0  
  for frac in f_range:
    beta_index=0
    for beta in beta_range:      
      Key="%.2f,%.2f"%(float(frac),float(beta))
      # study_n parameter
      # max_group_int_sigma_uT parameter

      study_sample_n=len(Optimizer_STDEV_OPT[Key].keys())
      #print "===="
      tmp= Optimizer_STDEV_OPT[Key].keys()
      tmp.sort()
      #print Key
      #print tmp
      #print Key,"study_n",len(Optimizer_STDEV_OPT[Key].keys()),Optimizer_STDEV_OPT[Key].keys()
      max_group_int_sigma_uT=0
      max_group_int_sigma_perc=0
      test_group_n=0
      
      for site in sites_samples:
        site_B=[];site_samples_id=[]
        for sample in sites_samples[site]:
          if sample in Optimizer_STDEV_OPT[Key].keys():
            site_B.append(Optimizer_STDEV_OPT[Key][sample]['sample_int_uT'])
            site_samples_id.append(sample)
            
        site_B=array(site_B)
        if len ( site_B)>1:
          test_group_n+=1
          if std(site_B)>max_group_int_sigma_uT:
            max_group_int_sigma_uT=std(site_B)
          if 100*(std(site_B)/mean(site_B)) > max_group_int_sigma_perc:
            max_group_int_sigma_perc=100*(std(site_B)/mean(site_B))


        # Print to optimizer results file
        String="%.2f\t%.2f\t%s\t"%(frac,beta,site)
        for sample_id in site_samples_id:
          String=String+sample_id+":"
        String=String[:-1]+'\t'
        for B in site_B:
          String=String+"%.1f"%(B)+":"
        String=String[:-1]+'\t'
        String=String+"%.2f"%(mean(site_B))+"\t"  
        String=String+"%.2f"%(std(site_B))+"\t"  
        String=String+"%.2f"%(100*(std(site_B)/mean(site_B)))+"\t"  
        #Optimizer_results_file=open("./optimizer/optimzer_%s_results.txt"%sample_mean_method,'a')
        Optimizer_results_file.write(String[:-1]+"\n")
        #Optimizer_results_file.close()



      for Function in optimization_functions:
        
        Command="opt_func= %s"%Function
        try:
          exec Command
          optimization_functions_matrices[Function][beta_index,f_index]=opt_func
          #print "Key",Key
          #print "function",Function
          #print "opt_func",opt_func
        except:
          print "-E Error: something is wrong with optimization function %s. Check!"%Function

      beta_index+=1
    f_index+=1
        
  #print     optimization_functions_matrices    
  #------------------------------------------------------
  # Make the plots
  #------------------------------------------------------

  
  Command_line="mkdir %s/optimizer/"%(WD)
  os.system(Command_line) 
  Command_line="mkdir %s/optimizer/pdf"%(WD)
  os.system(Command_line) 
  Command_line="mkdir %s/optimizer/svg"%(WD)
  os.system(Command_line) 

  Fig_counter=0
  for function in optimization_functions:
    #print function
    #print optimization_functions_matrices[function]
    if sum(optimization_functions_matrices[function].flatten())==0:
      Fig_counter+=1
      continue

    x,y = meshgrid(f_range,beta_range)
    cmap = matplotlib.cm.get_cmap('jet')
    figure(Fig_counter,(8,8))
    clf()
    delta_f=(f_range[1]-f_range[0])/2
    delta_s=(beta_range[1]-beta_range[0])/2
    if "study_sample_n" in function:
      Flattened=optimization_functions_matrices[function].flatten()
      N_colors=max(Flattened)-min(Flattened)
      cdict = cmap._segmentdata.copy()
      colors_i = linspace(0,1.,N_colors)
      indices = linspace(0,1.,N_colors+1)
      for COLOR in ('red','green','blue'):
          # Find the N colors
          D = array(cdict[COLOR])
          I = scipy.interpolate.interp1d(D[:,0], D[:,1])
          colors = I(colors_i)
          # Place these colors at the correct indices.
          A = zeros((N_colors+1,3), float)
          A[:,0] = indices
          A[1:,1] = colors
          A[:-1,2] = colors
          # Create a tuple for the dictionary.
          L = []
          for l in A:
              L.append(tuple(l))
          cdict[COLOR] = tuple(L)
      discrete_jet=matplotlib.colors.LinearSegmentedColormap('colormap',cdict,1024)
      #Cmap=cmap_discretize(cmap,max(Flattened))
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = discrete_jet,extent=(f_range[0]-delta_f,f_range[-1]+delta_f,beta_range[-1]+delta_s,beta_range[0]-delta_s))
    else:
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = cmap,extent=(f_range[0]-delta_f,f_range[-1]+delta_f,beta_range[-1]+delta_s,beta_range[0]-delta_s))
      
    xticks(f_range)
    yticks(beta_range)
    colorbar()

    f_index=0
    if "study_sample_n" in function or "test_group_n" in function:
      for FRAC in f_range:
        beta_index=0
        for beta in beta_range:
          text(FRAC,beta,"%i"%int(optimization_functions_matrices[function][beta_index,f_index]),fontsize=8,color='gray',horizontalalignment='center',verticalalignment='center')
          beta_index+=1
        f_index+=1

    title("optimization function =\n %s "%function,fontsize=10)
    xlabel("frac")
    ylabel("beta")
    Ax=gca()
    xticks(rotation=90)
    Ax.set_aspect('auto')
    savefig("%s/optimizer/pdf/optimization_function_%i"%(WD,Fig_counter) +".pdf")
    savefig("%s/optimizer/svg/optimization_function_%i"%(WD,Fig_counter) +".svg")

    Fig_counter+=1        
                

       
                    
  runtime_sec = time.time() - start_time
  m, s = divmod(runtime_sec, 60)
  h, m = divmod(m, 60)
  print "-I- runtime from start (hh:mm:ss) " + "%d:%02d:%02d" % (h, m, s)
  print "-I- Finished sucsessfuly."
  print "-I- DONE"

main()
  
