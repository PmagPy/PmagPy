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

def Thellier_optimizer(WD, Data,Data_hierarchy,criteria_fixed_paremeters_file,optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range):
  """
                      
  """
  #def __init__(WD, Data,optimizer_group_file_path,optimizer_functions_path,beta_range,frac_range):
  #  print "HELLO WORLD"
  #  #if __name__ == '__main__':

    
      

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

              if std(Best_array_tmp,ddof=1)<best_array_std:
                  Best_array=Best_array_tmp
                  best_array_std=std(Best_array,ddof=1)
                  Best_interpretations=Best_interpretations_tmp
                  Best_interpretations_tmp={}
      return Best_interpretations,mean(Best_array),std(Best_array,ddof=1)



  def find_sample_min_max_interpretation (Intensities,acceptance_criteria):

        
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
            if std(B_tmp,ddof=1)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp,ddof=1)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
                Acceptable_sample_min=mean(B_tmp)
                break
            else:
                tmp_Intensities[sample_to_remove].remove(B_tmp_min)
                if len(tmp_Intensities[sample_to_remove])==0:
                    break
                    
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
            if std(B_tmp,ddof=1)<acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp,ddof=1)/mean(B_tmp))<acceptance_criteria["sample_int_sigma_perc"]:
                Acceptable_sample_max=mean(B_tmp)
                break
            else:
                tmp_Intensities[sample_to_remove].remove(B_tmp_max)
                if len(tmp_Intensities[sample_to_remove])<1:
                    break
        #print "Ron Check mi max sample"
        #print "max:",tmp_Intensities,B_tmp,Acceptable_sample_max
        #print "======"

        if Acceptable_sample_min=="" or Acceptable_sample_max=="":
            #print "-W- Cant calculate acceptable sample bounds"
            return(0.,0.)
        return(Acceptable_sample_min,Acceptable_sample_max)     




  #=============================================================
  #
  #  Main
  #
  #=============================================================

  
  #------------------------------------------------
  # Initialize values
  #------------------------------------------------

  logfile=open(WD+"/optimizer/thellier_optimizer.log",'w')
  start_time = time.time()
  accept_new_parameters={}
  criteria_specimen_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_scat',
                 'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
  criteria_sample_list=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']
  
  high_threshold_value_list=['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
  low_threshold_value_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']

  #------------------------------------------------
  # Write header to thellier_optimizer_master_file
  #------------------------------------------------

  thellier_optimizer_master_file=gzip.open(WD+'/optimizer/thellier_optimizer_interpretation_log.txt.gz', 'wb')

  String="er_specimen_name\t"+"t_min\t"+"t_max_\t"+"specimen_int_uT\t"
  for crit in criteria_specimen_list:
      String=String+crit+"\t"
  thellier_optimizer_master_file.write(String[:-1]+"\n")
  String=""
    
  #------------------------------------------------
  # Write header to optimizer output
  #------------------------------------------------

  Optimizer_results_file=open(WD + "/optimizer/optimizer_results.txt",'w')
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

  accept_new_parameters['specimen_int_n']=0
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

  logfile.write( "-I read ceriteria_file\n ")
 
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

  for crit in criteria_specimen_list + criteria_sample_list:
    try:
      logfile.write(  "-I- threshold value %s:%.2f\n"%(crit,accept_new_parameters[crit]))
    except:
      logfile.write(  "-I- threshold value %s:%s\n"%(crit,accept_new_parameters[crit]))
                  
  #------------------------------------------------
  # read Optimization functions
  #------------------------------------------------

  optimization_functions=[]
  fin=open(WD + "/" + optimizer_functions_path,'rU')
  for line in fin.readlines():
    optimization_functions.append(line.strip('\n'))


  #------------------------------------------------
  # read sites name from magic_measurement file
  # or from sites_sample_file (user defined site-samples file)
  #------------------------------------------------

  sites_samples={}
##
##    if OPTIMIZE_BY_SITE_NAME:
##      pathes=dir_pathes
##    elif OPTIMIZE_BY_LIST:
##      pathes=["./"]
##      
##    for dir_path in pathes:
##      if OPTIMIZE_BY_SITE_NAME:
##        fin=open(dir_path+"magic_measurements.txt",'rU')
##      if OPTIMIZE_BY_LIST:
  
  fin=open(optimizer_group_file_path,'rU')            
  line=fin.readline()
  line=fin.readline()
  header=line.strip('\n').split('\t')
  #print header
  for line in fin.readlines():
    tmp_data={}
    line=line.strip('\n').split('\t')
    #print line
    for i in range(len(line)):
      tmp_data[header[i]]=line[i]
    sample=tmp_data['er_sample_name']
    site=tmp_data['er_group_name']
    if "comments" in tmp_data.keys() and "exclude" in tmp_data['comments']:
      logfile.write(  "-W- WARNING: ignoring sample %s\n"%sample)
      continue
    if site not in sites_samples.keys():
      sites_samples[site]=[]
    if sample not in sites_samples[site]:
      sites_samples[site].append(sample)



  logfile.write(  "-I- Now looping through all data points in the Arai plot\n")

  thellier_optimizer_master_table={}
  
  n_min=int(accept_new_parameters['specimen_int_n'])

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
      logfile.write(  "-W- skipping specimen %s\n"%s)
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
          logfile.write(  "-E- ERROR: specimen %s temperature %f appears in Arai plot but not in Zijderveld plot\n"%(s,tmin))
          continue
        if  tmax not in z_temperatures:
          logfile.write(  "-E- ERROR: specimen %s temperature %f appears in Arai plot but not in Zijderveld plot\n"%(s,tmax))
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
        pars["specimen_PCA_v1"] =  best_fit_vector 
        pars["specimen_PCA_sigma_max"] =  sqrt(t1)
        pars["specimen_PCA_sigma_int"] =  sqrt(t2)
        pars["specimen_PCA_sigma_min"] =  sqrt(t3)

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

        
        pars['specimen_int_n']=end-start+1
        pars["specimen_b"]=york_b
        pars["specimen_YT"]=y_T       
        pars["specimen_b_sigma"]=york_sigma
        pars["specimen_b_beta"]=beta_Coe
        pars["specimen_f"]=f_Coe
        pars["specimen_fvds"]=f_vds
        pars["specimen_g"]=g_Coe
        pars["specimen_q"]=q_Coe

        pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]

##        #-------------------------------------------------
##        # pTRM checks:
##        # DRAT ()
##        # and
##        # DRATS (Tauxe and Staudigel 2004)
##        #-------------------------------------------------
##
##        x_ptrm_check_in_segment,y_ptrm_check_in_segment,x_Arai_compare=[],[],[]
##        x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
##        
##        for k in range(len(Data[s]['ptrm_checks_temperatures'])):
##          if Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
##            if Data[s]['ptrm_checks_temperatures'][k]<=pars["measurement_step_max"]:
##              x_ptrm_check_in_segment.append(Data[s]['x_ptrm_check'][k])
##              y_ptrm_check_in_segment.append(Data[s]['y_ptrm_check'][k])
##              x_Arai_index=t_Arai.index(Data[s]['ptrm_checks_temperatures'][k])
##              x_Arai_compare.append(x_Arai[x_Arai_index])
##        x_ptrm_check_in_segment=array(x_ptrm_check_in_segment)  
##        y_ptrm_check_in_segment=array(y_ptrm_check_in_segment)
##        x_Arai_compare=array(x_Arai_compare)
##                                                               
##                                  
##        DRATS=100*(abs(sum(x_ptrm_check_in_segment-x_Arai_compare))/(x_Arai[end]))
##        int_ptrm_n=len(x_ptrm_check_in_segment)
##        if int_ptrm_n > 0:
##           pars['specimen_int_ptrm_n']=int_ptrm_n
##           pars['specimen_drats']=DRATS
##        else:
##           pars['specimen_int_ptrm_n']=int_ptrm_n
##           pars['specimen_drats']=-1


        #-------------------------------------------------
        # pTRM checks:
        # DRAT ()
        # and
        # DRATS (Tauxe and Staudigel 2004)
        #-------------------------------------------------

        x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end,x_Arai_compare=[],[],[]
        x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
        #x_ptrm_check_for_SCAT,y_ptrm_check_for_SCAT=[],[]
        
        for k in range(len(Data[s]['ptrm_checks_temperatures'])):
          if Data[s]['ptrm_checks_temperatures'][k]<pars["measurement_step_max"] and Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
            x_ptrm_check_in_0_to_end.append(Data[s]['x_ptrm_check'][k])
            y_ptrm_check_in_0_to_end.append(Data[s]['y_ptrm_check'][k])
            x_Arai_index=t_Arai.index(Data[s]['ptrm_checks_temperatures'][k])
            x_Arai_compare.append(x_Arai[x_Arai_index])
            if Data[s]['ptrm_checks_temperatures'][k]>=pars["measurement_step_min"]:
                x_ptrm_check_in_start_to_end.append(Data[s]['x_ptrm_check'][k])
                y_ptrm_check_in_start_to_end.append(Data[s]['y_ptrm_check'][k])
##          if Data[s]['ptrm_checks_temperatures'][k] >=     pars["measurement_step_min"] and Data[s]['ptrm_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
##                x_ptrm_check_for_SCAT.append(Data[s]['x_ptrm_check'][k])
##                y_ptrm_check_for_SCAT.append(Data[s]['y_ptrm_check'][k])
              
        # scat uses a different definistion":
        # use only pTRM that STARTED before the last temperatire step.
        
        x_ptrm_check_in_0_to_end=array(x_ptrm_check_in_0_to_end)  
        y_ptrm_check_in_0_to_end=array(y_ptrm_check_in_0_to_end)
        x_Arai_compare=array(x_Arai_compare)
        x_ptrm_check_in_start_to_end=array(x_ptrm_check_in_start_to_end)
        y_ptrm_check_in_start_to_end=array(y_ptrm_check_in_start_to_end)
##        x_ptrm_check_for_SCAT=array(x_ptrm_check_for_SCAT)
##        y_ptrm_check_for_SCAT=array(y_ptrm_check_for_SCAT)
                               
        DRATS=100*(abs(sum(x_ptrm_check_in_0_to_end-x_Arai_compare))/(x_Arai[end]))
        int_ptrm_n=len(x_ptrm_check_in_0_to_end)
        if int_ptrm_n > 0:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=DRATS
        else:
           pars['specimen_int_ptrm_n']=int_ptrm_n
           pars['specimen_drats']=-1


        #-------------------------------------------------
        # Tail check MD
        #-------------------------------------------------

        # collect tail check data"
        x_tail_check_start_to_end,y_tail_check_start_to_end=[],[]
        #x_tail_check_for_SCAT,y_tail_check_for_SCAT=[],[]

        for k in range(len(Data[s]['tail_check_temperatures'])):
          if Data[s]['tail_check_temperatures'][k] in t_Arai:
              if Data[s]['tail_check_temperatures'][k]<=pars["measurement_step_max"] and Data[s]['tail_check_temperatures'][k] >=pars["measurement_step_min"]:
                   x_tail_check_start_to_end.append(Data[s]['x_tail_check'][k]) 
                   y_tail_check_start_to_end.append(Data[s]['y_tail_check'][k]) 
          #if Data[s]['tail_check_temperatures'][k] >= pars["measurement_step_min"] and Data[s]['tail_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                #x_tail_check_for_SCAT.append(Data[s]['x_tail_check'][k])
                #y_tail_check_for_SCAT.append(Data[s]['y_tail_check'][k])

                
        x_tail_check_start_to_end=array(x_tail_check_start_to_end)
        y_tail_check_start_to_end=array(y_tail_check_start_to_end)
        #x_tail_check_for_SCAT=array(x_tail_check_for_SCAT)
        #y_tail_check_for_SCAT=array(y_tail_check_for_SCAT)
           

           
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

##        if "AniSpec" in Data[s].keys():
##           AniSpec=Data[s]['AniSpec']
##           AniSpecRec=pmag.doaniscorr(pars,AniSpec)
##           pars["AC_specimen_dec"]=AniSpecRec["specimen_dec"]
##           pars["AC_specimen_inc"]=AniSpecRec["specimen_inc"]
##           pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
##           pars["AC_specimen_correction_factor"]=float(pars["AC_specimen_int"])/float(pars["specimen_int"])
##           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6
##
##        else:
##           pars["AC_specimen_correction_factor"]=1.0
##           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6
        if "AniSpec" in Data[s].keys():
           S_matrix=zeros((3,3),'f')
           S_matrix[0,0]=Data[s]['AniSpec']['anisotropy_s1']
           S_matrix[1,1]=Data[s]['AniSpec']['anisotropy_s2']
           S_matrix[2,2]=Data[s]['AniSpec']['anisotropy_s3']
           S_matrix[0,1]=Data[s]['AniSpec']['anisotropy_s4']
           S_matrix[1,0]=Data[s]['AniSpec']['anisotropy_s4']
           S_matrix[1,2]=Data[s]['AniSpec']['anisotropy_s5']
           S_matrix[2,1]=Data[s]['AniSpec']['anisotropy_s5']
           S_matrix[0,2]=Data[s]['AniSpec']['anisotropy_s6']
           S_matrix[2,0]=Data[s]['AniSpec']['anisotropy_s6']

           TRM_anc_unit=array(pars['specimen_PCA_v1'])/sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
           # If Ftest is lower than critical value:
           # set the anisotropy correction tensor to identity matrix
           if 'anisotropy_F_crit' in Data[s]['AniSpec'].keys():
               if  float(Data[s]['AniSpec']['anisotropy_ftest']) < float(Data[s]['AniSpec']['anisotropy_F_crit']):

           #if  float(Data[s]['AniSpec']['anisotropy_F']) < float(Data[s]['AniSpec']['anisotropy_F_crit']):
                 S_matrix=identity(3,'f')


           B_lab_unit=pmag.dir2cart([ Data[s]['Thellier_dc_field_phi'], Data[s]['Thellier_dc_field_theta'],1])
##           print "Quality check"
##           print "phi,thata,1 ",[ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1]
##           #raw_input("---")
           B_lab_unit=array([0,0,-1])
##           print B_lab_unit
##           print B_anc_unit
##           print "S_matrix",S_matrix
##           print "inv(S_matrix)",inv(S_matrix)
##           print "dot(inv(S_matrix),B_anc_unit)",dot(inv(S_matrix),B_anc_unit)
##           print "norm  dot(inv(S_matrix),B_anc_unit)",linalg.norm(dot(inv(S_matrix),B_anc_unit.transpose()))
##           
##           print "linalg.norm(dot((inv(S_matrix),B_lab_unit.transpose())))",linalg.norm(dot(inv(S_matrix),B_lab_unit))
           #pars["Anisotropy_correction_factor"]= linalg.norm(dot(inv(S_matrix),B_anc_unit.transpose()))/linalg.norm(dot(inv(S_matrix),B_lab_unit))

           Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
           pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor

##           print "aniso_factor", pars["Anisotropy_correction_factor"]
           pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])
##           print "aniso_int",pars["AC_specimen_int"]
           
           #AniSpecRec=pmag.doaniscorr(pars,AniSpec)
           #pars["AC_specimen_dec"]=AniSpecRec["specimen_dec"]
           #pars["AC_specimen_inc"]=AniSpecRec["specimen_inc"]
           #pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
           #pars["AC_specimen_int"]=AniSpecRec["specimen_int"]
           #try:
           #    pars["Anisotropy_correction_factor"]=float(pars["AC_specimen_int"])/float(pars["specimen_int"])
           #except:
           #    pars["Anisotropy_correction_factor"]=1.0
           pars["AC_anisotropy_type"]=Data[s]['AniSpec']["anisotropy_type"]
           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6

        else:
           pars["Anisotropy_correction_factor"]=1.0
           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6
           
        #-------------------------------------------------                    
        # NLT and anisotropy correction together in one equation
        # See Shaar et al (2010), Equation (3)
        #-------------------------------------------------

        if 'NLT_parameters' in Data[s].keys():

           alpha=Data[s]['NLT_parameters']['tanh_parameters'][0][0]
           beta=Data[s]['NLT_parameters']['tanh_parameters'][0][1]
           b=float(pars["specimen_b"])
           Fa=pars["Anisotropy_correction_factor"]

           if ((abs(b)*Fa)/alpha) <1.0:
               Banc_NLT=math.atanh( ((abs(b)*Fa)/alpha) ) / beta
               pars["NLTC_specimen_int"]=Banc_NLT
               pars["specimen_int_uT"]=Banc_NLT*1e6

               if "AC_specimen_int" in pars.keys():
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["AC_specimen_int"])
               else:                       
                   pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["specimen_int"])
           else:
               logfile.write(  "-W- WARNING: problematic NLT mesurements specimens %s. Cant do NLT calculation. check data\n"%s)
               pars["NLT_specimen_correction_factor"]=-999
        else:
           pars["NLT_specimen_correction_factor"]=-999

           

        #--------------------------------------------------------------
        # Save all the interpretation into file
        #--------------------------------------------------------------
        String=s+"\t"+"%s\t"%pars["measurement_step_min"]+"%s\t"%pars["measurement_step_max"]+"%s\t"%pars["specimen_int_uT"]
        for crit in criteria_specimen_list:
           if crit != "specimen_scat":
               String=String+"%f"%pars[crit]+"\t"
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
  thellier_optimizer_master_file.write( "-I- runtime from start (hh:mm:ss)" + "%d:%02d:%02ds\n" % (h, m, s))       
        


  #-------------------------------------------------                     
  # Looping through all f and beta, and save the 'acceptable interpretation
  # i.e. the interpretation that pass the criteria 
  #-------------------------------------------------                     

  Optimizer_data={}
  Optimizer_STDEV_OPT={}
  
  for frac in frac_range:
    for beta in beta_range:

      accept_new_parameters['specimen_b_beta']=beta
      accept_new_parameters['specimen_frac']=frac
      Key="%.2f,%.2f"%(float(frac),float(beta))

      Optimizer_data[Key]={}
      for sample in Data_hierarchy['samples'].keys():
        for specimen in Data_hierarchy['samples'][sample]:
          if specimen not in specimens:
            continue
          
          for pars in thellier_optimizer_master_table[specimen]:
            Fail=False
            for crit in high_threshold_value_list:
              if float(pars[crit])>float(accept_new_parameters[crit]):
                thellier_optimizer_master_file.write(  "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,crit))
                Fail=True
            if Fail:
              continue
            for crit in low_threshold_value_list:
              if float(pars[crit])<float(accept_new_parameters[crit]):
                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,crit))
                Fail=True
            if Fail:
              continue
            
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

            #-------------------------------------------------                     

            x_ptrm_check_for_SCAT,y_ptrm_check_for_SCAT=[],[]
            
            for k in range(len(Data[specimen]['ptrm_checks_temperatures'])):

              if Data[specimen]['ptrm_checks_temperatures'][k] >=   pars["measurement_step_min"] and Data[specimen]['ptrm_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                    x_ptrm_check_for_SCAT.append(Data[specimen]['x_ptrm_check'][k])
                    y_ptrm_check_for_SCAT.append(Data[specimen]['y_ptrm_check'][k])
            x_ptrm_check_for_SCAT=array(x_ptrm_check_for_SCAT)
            y_ptrm_check_for_SCAT=array(y_ptrm_check_for_SCAT)

            #-------------------------------------------------                     

            x_tail_check_for_SCAT,y_tail_check_for_SCAT=[],[]

            for k in range(len(Data[specimen]['tail_check_temperatures'])):

              if Data[specimen]['tail_check_temperatures'][k] >= pars["measurement_step_min"] and Data[specimen]['tail_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                    x_tail_check_for_SCAT.append(Data[specimen]['x_tail_check'][k])
                    y_tail_check_for_SCAT.append(Data[specimen]['y_tail_check'][k])     
            x_tail_check_for_SCAT=array(x_tail_check_for_SCAT)
            y_tail_check_for_SCAT=array(y_tail_check_for_SCAT)



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


            if len(x_ptrm_check_for_SCAT) > 0:

        
              # the two bounding lines
              ymin=intercept1+x_ptrm_check_for_SCAT*slop1
              ymax=intercept2+x_ptrm_check_for_SCAT*slop2

              # arrays of "True" or "False"
              check_1=y_ptrm_check_for_SCAT>ymax
              check_2=y_ptrm_check_for_SCAT<ymin

              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on ptrm scat\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
                continue


            # check if the tail checks data points are in the 'box'


            if len(x_tail_check_for_SCAT) > 0:

              # the two bounding lines
              ymin=intercept1+x_tail_check_for_SCAT*slop1
              ymax=intercept2+x_tail_check_for_SCAT*slop2

              # arrays of "True" or "False"
              check_1=y_tail_check_for_SCAT>ymax
              check_2=y_tail_check_for_SCAT<ymin


              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on tail scat\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
                continue


##            #-------------------------------------------------                     
##            # Calculate the new 'MAD box' parameter
##            # all datapoints should be inside teh M"AD box"
##            # defined by the threshold value of MAD
##            # For definitionsee Shaar and Tauxe (2012)
##            #-------------------------------------------------                     
##
##            accept_new_parameters['specimen_mad_scat']="True"
##            pars["specimen_mad_scat"]="Pass"
##            if ('specimen_mad_scat' in accept_new_parameters.keys() and 'specimen_int_mad' in accept_new_parameters.keys()) :
##                if accept_new_parameters['specimen_mad_scat']==True or accept_new_parameters['specimen_mad_scat'] in [1,"True","TRUE",'1']:
##                  
##                    zstart=t_Arai.index(pars["measurement_step_min"])
##                    zend=t_Arai.index(pars["measurement_step_max"])
##                    zdata_segment=Data[specimen]['zdata'][zstart:zend+1]
##
##                    # center of mass 
##                    CM_x=mean(zdata_segment[:,0])
##                    CM_y=mean(zdata_segment[:,1])
##                    CM_z=mean(zdata_segment[:,2])
##                    CM=array([CM_x,CM_y,CM_z])
##
##                    # threshold value for the distance of the point from a line:
##                    # this is depends of MAD
##                    # if MAD= tan-1 [ sigma_perpendicular / sigma_max ]
##                    # then:
##                    # sigma_perpendicular_threshold=tan(MAD_threshold)*sigma_max
##                    sigma_perpendicular_threshold=abs(tan(radians(accept_new_parameters['specimen_int_mad'])) *  pars["specimen_PCA_sigma_max"] )
##                    
##                    for P in zdata_segment:
##                        P_CM=P-CM
##                        best_fit_vector_unit=pars["specimen_PCA_v1"]/sqrt(sum(pars["specimen_PCA_v1"]**2))
##                        CM_P_projection_on_PCA_line=dot(best_fit_vector_unit,P_CM)
##
##                        # Pythagoras
##                        P_CM_length=sqrt(sum((P_CM)**2))
##                        Point_2_PCA_Distance=sqrt((P_CM_length**2-CM_P_projection_on_PCA_line**2))
##
##                        #print "sigma_perpendicular_threshold*2",sigma_perpendicular_threshold*2
##                        if Point_2_PCA_Distance > sigma_perpendicular_threshold*2:
##                            pars["specimen_mad_scat"]="Fail"
##                            index=""
##                            for i in range(len(Data[specimen]['zdata'])):
##                            
##                                if P[0] == Data[specimen]['zdata'][i][0] and P[1] == Data[specimen]['zdata'][i][1] and P[2] == Data[specimen]['zdata'][i][2]:
##                                    index =index+",%i"%i
##                                    break
##                            #print "specimen  %s fail on mad_scat,%i"%(s,index)
##            if pars["specimen_mad_scat"]=="Fail":  
##                thellier_optimizer_master_file.write( "key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on mad scat point no. %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,index))

              
            #------------
            if sample not in  Optimizer_data[Key].keys():
              Optimizer_data[Key][sample]={}
            if specimen not in Optimizer_data[Key][sample].keys():
              Optimizer_data[Key][sample][specimen]=[]
            Optimizer_data[Key][sample][specimen].append(pars['specimen_int_uT'])
            thellier_optimizer_master_file.write( "-I- key= %s specimen %s pass tmin,tmax= (%.0f,%.0f)\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
            
            

      
  #-------------------------------------------------                     
  # Looping through all f and beta, and save the best sample means
  # that pass the criteria
  # i.e. STDEV_OPT
  #-------------------------------------------------                     

  for frac in frac_range:
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
                if max(Optimizer_data[Key][sample][specimen]) < mean(B_min_array) - 2*std(B_min_array,ddof=1) \
                   or min(Optimizer_data[Key][sample][specimen]) > mean(B_max_array) + 2*std(B_max_array,ddof=1):
                    if specimen not in exclude_specimens_list:
                        exclude_specimens_list.append(specimen)
                        
            if len(exclude_specimens_list)>1:
                thellier_optimizer_master_file.write( "-I- check outlier sample =%s; frac=%f,beta=%f,: more than one specimen can be excluded.\n"%(sample,frac,beta))
                exclude_specimens_list=[]

            if len(exclude_specimens_list)==1:
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
    optimization_functions_matrices[function]=zeros((len(beta_range),len(frac_range)))

  f_index=0  
  for frac in frac_range:
    beta_index=0
    for beta in beta_range:      
      Key="%.2f,%.2f"%(float(frac),float(beta))
      # study_n parameter
      # max_group_int_sigma_uT parameter

      study_sample_n=len(Optimizer_STDEV_OPT[Key].keys())
      tmp= Optimizer_STDEV_OPT[Key].keys()
      tmp.sort()
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
          if std(site_B,ddof=1)>max_group_int_sigma_uT:
            max_group_int_sigma_uT=std(site_B,ddof=1)
          if 100*(std(site_B,ddof=1)/mean(site_B)) > max_group_int_sigma_perc:
            max_group_int_sigma_perc=100*(std(site_B,ddof=1)/mean(site_B))


        # Print to optimizer results file
        String="%.2f\t%.2f\t%s\t"%(frac,beta,site)
        for sample_id in site_samples_id:
          String=String+sample_id+":"
        String=String[:-1]+'\t'
        for B in site_B:
          String=String+"%.1f"%(B)+":"
        String=String[:-1]+'\t'
        String=String+"%.2f"%(mean(site_B))+"\t"  
        String=String+"%.2f"%(std(site_B,ddof=1))+"\t"  
        String=String+"%.2f"%(100*(std(site_B,ddof=1)/mean(site_B)))+"\t"  
        #Optimizer_results_file=open("./optimizer/optimzer_%s_results.txt"%sample_mean_method,'a')
        Optimizer_results_file.write(String[:-1]+"\n")
        #Optimizer_results_file.close()



      for Function in optimization_functions:
        
        #Command="opt_func= %s"%Function
        try:
          optimization_functions_matrices[Function][beta_index,f_index]=eval(Function)
          #optimization_functions_matrices[Function][beta_index,f_index]=opt_func
        except:
          logfile.write(  "-E Error: something is wrong with optimization function %s. Check!\n"%Function)

      beta_index+=1
    f_index+=1
        
  #------------------------------------------------------
  # Make the plots
  #------------------------------------------------------

  print "WD",WD
  #Command_line="mkdir %s/optimizer/"%(WD)
  try:
    os.mkdir(WD + "/optimizer/pdf")
  except:
    pass
  try:
    os.mkdir(WD + "/optimizer/svg")
  except:
    pass

  #os.system(Command_line) 
  #Command_line="mkdir %s/optimizer/pdf"%(WD)
  #os.system(Command_line) 
  #Command_line="mkdir %s/optimizer/svg"%(WD)
  #os.system(Command_line) 

  Fig_counter=0
  for function in optimization_functions:
    if sum(optimization_functions_matrices[function].flatten())==0:
      Fig_counter+=1
      continue

    x,y = meshgrid(frac_range,beta_range)
    cmap = matplotlib.cm.get_cmap('jet')
    figure(Fig_counter,(11,8))
    clf()
    delta_f=(frac_range[1]-frac_range[0])/2
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
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = discrete_jet,extent=(frac_range[0]-delta_f,frac_range[-1]+delta_f,beta_range[-1]+delta_s,beta_range[0]-delta_s))
    else:
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = cmap,extent=(frac_range[0]-delta_f,frac_range[-1]+delta_f,beta_range[-1]+delta_s,beta_range[0]-delta_s))
      
    xticks(frac_range)
    yticks(beta_range)
    colorbar()

    f_index=0
    if "study_sample_n" in function or "test_group_n" in function:
      for FRAC in frac_range:
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
  logfile.write(  "-I- runtime from start (hh:mm:ss) " + "%d:%02d:%02d\n" % (h, m, s))
  logfile.write(  "-I- Finished sucsessfuly.\n")
  logfile.write(  "-I- DONE\n")

  


