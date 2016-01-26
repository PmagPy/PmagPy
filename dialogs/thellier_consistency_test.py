#!/usr/bin/env python

#---------------------------------------------------------------------------
# Author: Ron Shaar
# Revision notes
#
# Rev 1.0 Initial revision August 2012 
#---------------------------------------------------------------------------
import matplotlib
import pylab
import scipy
import os
import time
from pylab import * 
from scipy import *
import  scipy.interpolate
import gzip
#import pmag
import copy
from scipy.optimize import curve_fit
import thellier_interpreter
import thellier_gui_lib
#rcParams.update({"svg.embed_char_paths":False})

def run_thellier_consistency_test(WD, Data,Data_hierarchy,acceptance_criteria,optimizer_group_file_path,optimizer_functions_path,preferences,stat1_range,stat2_range,THERMAL,MICROWAVE):
  """
                      
  """



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
                  Best_interpretations=copy.deepcopy(Best_interpretations_tmp)
                  Best_interpretations_tmp={}
      return Best_interpretations,mean(Best_array),std(Best_array,ddof=1)



  def find_sample_min_max_interpretation (Intensities,acceptance_criteria):

        
        tmp_Intensities={}
        Acceptable_sample_min,Acceptable_sample_max="",""
        for this_specimen in Intensities.keys():
          B_list=copy.deepcopy(Intensities[this_specimen])
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
          B_list=copy.deepcopy(Intensities[this_specimen])
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

  logfile=open(WD+"/consistency_test/consistency_test_optimizer.log",'w')
  start_time = time.time()
  
  accept_new_parameters={}
  #criteria_specimen_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gmax','specimen_b_beta','specimen_scat',
  #               'specimen_dang','specimen_drats','specimen_int_mad','specimen_md','specimen_g','specimen_q']
  criteria_sample_list=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']
  
  criteria_specimen_list=preferences['show_statistics_on_gui']
  
  #high_threshold_value_list=['specimen_gmax','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
  #low_threshold_value_list=['specimen_int_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']
  
  #------------------------------------------------
  # Write header to thellier_optimizer_master_file
  #------------------------------------------------

  thellier_optimizer_master_file=gzip.open(WD+'/consistency_test/consistency_test_log.txt.gz', 'wb')

  String="er_specimen_name\t"+"t_min\t"+"t_max_\t"+"specimen_int_uT\t"
  for crit in criteria_specimen_list:
      String=String+"specimen_"+crit+"\t"
  thellier_optimizer_master_file.write(String[:-1]+"\n")
  String=""
    
  #------------------------------------------------
  # Write header to optimizer output
  #------------------------------------------------

  Optimizer_results_file=open(WD + "/consistency_test/consistency_test_results.txt",'w')
  String="%s\t%s\tTest_Site\tSamples\tB_samples\tTest Site Mean\tTest Site STD\tTest Site [STD/Mean]\n"%(stat1_range[0],stat2_range[0])
  Optimizer_results_file.write(String)

#===========================================================================================================        

  #for crit in criteria_specimen_list + criteria_sample_list:
  #  if acceptance_criteria["specimen_"+crit]['threshold_type'] in ['low','high'] :
  #    logfile.write(  "-I- threshold value %s:%.2f\n"%(crit,acceptance_criteria["specimen_"+crit]['value']))
  #  elif acceptance_criteria["specimen_"+crit]['threshold_type'] == "flag" :
  #    logfile.write(  "-I- threshold value %s:%s\n"%(crit,accept_new_parameters["specimen_"+crit]['value']))
  #  elif acceptance_criteria["specimen_"+crit]['threshold_type'] == "bool" :
  #    logfile.write(  "-I- threshold value %s:%s\n"%(crit,accept_new_parameters["specimen_"+crit]['value']))
        
        
                  
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
  samples_expected_intensity={}
  
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
    if "sample_int" in tmp_data.keys() and  tmp_data['sample_int']!="":
      try:
        samples_expected_intensity[sample]=float(tmp_data['sample_int'])*1e6 # convert form T to uT
      except:
        pass
    if site not in sites_samples.keys():
      sites_samples[site]=[]
    if sample not in sites_samples[site]:
      sites_samples[site].append(sample)



  logfile.write(  "-I- Now looping through all data points in the Arai plot\n")

  thellier_optimizer_master_table={}
  
  n_min=int(acceptance_criteria['specimen_int_n']['value'])

  specimens=Data.keys()
  specimens.sort()


  # check if beta is one of the inspected parameters"
  if stat1_range[0]=="specimen_b_beta":
      beta_range=stat1_range[1]
  elif stat2_range[0]=="specimen_b_beta":
      beta_range=stat2_range[1]
  else:
      if acceptance_criteria["specimen_b_beta"]["value"]!=-999:
          beta_range=[acceptance_criteria["specimen_b_beta"]["value"]]
      else:
          beta_range=[""]
                    
  
  for s in specimens:
    thellier_optimizer_master_table[s]={}    

    t_Arai=Data[s]['t_Arai']
    if len(t_Arai)<4:
      logfile.write(  "-W- skipping specimen %s. few datapints. \n"%s)
      continue
    #--------------------------------------------------------------
    # Save all the interpretation into file and master table
    #--------------------------------------------------------------
    for start in range (0,len(t_Arai)-n_min+1):
      for end in range (start+n_min-1,len(t_Arai)):
        tmin=t_Arai[start]
        tmax=t_Arai[end]
        for beta in beta_range:
            tmp_acceptance_criteria=copy.deepcopy(acceptance_criteria)
            pars=thellier_gui_lib.get_PI_parameters(Data,tmp_acceptance_criteria,preferences,s,tmin,tmax,logfile,THERMAL,MICROWAVE)
            thellier_optimizer_master_table[s][tmin,tmax,beta]=pars
           

  thellier_optimizer_master_file.write( "Done loopping through all points in Arai plot. All specimens\n")
  time_1= time.time() 
  runtime_sec = time_1 - start_time
  m, s = divmod(runtime_sec, 60)
  h, m = divmod(m, 60)
  thellier_optimizer_master_file.write( "-I- runtime from start (hh:mm:ss)" + "%d:%02d:%02ds\n" % (h, m, s))       
        
  
  #-------------------------------------------------                     
  #-------------------------------------------------                     

  Optimizer_data={}
  Optimizer_STDEV_OPT={}

      
#  if stat1_range[0]=="specimen_frac":
#      stat1_range[1]=stat1_range[1]
#  elif stat2_range[0]=="specimen_frac":
#      stat1_range[1]=stat2_range[1]
#  else:
#      stat1_range[1]=[]          
#
#  if stat_range[0]=="specimen_b_beta":
#      stat1_range[1]=stat1_range[1]
#  elif stat2_range[0]=="specimen_b_beta":
#      stat1_range[1]=stat2_range[1]
#  else:
#      stat1_range[1]=[]          
                
  for stat1_value in stat1_range[1]:
    for stat2_value in stat2_range[1]:

      tmp_acceptance_criteria=copy.deepcopy(acceptance_criteria)
      tmp_acceptance_criteria[stat1_range[0]]['value']=stat1_value
      tmp_acceptance_criteria[stat2_range[0]]['value']=stat2_value
      Key="%s,%s"%(str(stat1_value),str(stat2_value))

      Optimizer_data[Key]={}
      for sample in Data_hierarchy['samples'].keys():
        for specimen in Data_hierarchy['samples'][sample]:
          if specimen not in specimens:
            continue

          for t1_t2_beta in thellier_optimizer_master_table[specimen]:
              if t1_t2_beta[2]!="":
                if float(t1_t2_beta[2])!=float(tmp_acceptance_criteria['specimen_b_beta']['value']):
                  continue
              pars=thellier_optimizer_master_table[specimen][t1_t2_beta]
              pars=thellier_gui_lib.check_specimen_PI_criteria(pars,tmp_acceptance_criteria)
              if pars['specimen_fail_criteria']==[]:
                Fail=False
              else:
                thellier_optimizer_master_file.write("key=%s - specimen %s, tmin,tmax =(%.0f,%.0f) fail on %s\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273,",".join(pars['specimen_fail_criteria'])))
                Fail=True
              if Fail:
                continue
                    
              
              #------------
              if sample not in Optimizer_data[Key].keys():
                Optimizer_data[Key][sample]={}                
              if specimen not in Optimizer_data[Key][sample].keys():
                Optimizer_data[Key][sample][specimen]=[]
                
              Optimizer_data[Key][sample][specimen].append(pars)
              thellier_optimizer_master_file.write( "-I- key= %s specimen %s pass tmin,tmax= (%.0f,%.0f)\n"%(Key,specimen,float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273))
            
            

      
  #-------------------------------------------------                     
  # i.e. STDEV_OPT
  #-------------------------------------------------                     

  logfile.write(  "-I- Loop now through statistic #1 and statistic #2 and find the best means\n" )

  for stat1_value in stat1_range[1]:
    for stat2_value in stat2_range[1]:
      Key="%s,%s"%(str(stat1_value),str(stat2_value))
      
      thellier_optimizer_master_file.write("-I- calulating best sample means, %s"%Key)

      #--------------------------------------------------------------
      # sort results
      #--------------------------------------------------------------
      B_specimens={}
      All_grade_A_Recs={}
      for sample in Optimizer_data[Key].keys():
        B_specimens[sample]={}
        for specimen in Optimizer_data[Key][sample].keys():
          if specimen not in B_specimens.keys():
            B_specimens[sample][specimen]=[]
          if specimen not in All_grade_A_Recs.keys():
            All_grade_A_Recs[specimen]={}  
          for pars in Optimizer_data[Key][sample][specimen]:
            B_specimens[sample][specimen].append(pars['specimen_int_uT'])
            TEMP="%.0f,%.0f"%(float(pars["measurement_step_min"])-273,float(pars["measurement_step_max"])-273)
            new_pars={}
            for k in pars.keys():
                new_pars[k]=pars[k]
            All_grade_A_Recs[specimen][TEMP]=pars
          B_specimens[sample][specimen].sort()
 
        if len(B_specimens[sample].keys())<2:
            continue    
                                
        thellier_auto_interpreter=thellier_interpreter.thellier_auto_interpreter(Data,Data_hierarchy,WD,acceptance_criteria,preferences,logfile,THERMAL,MICROWAVE)
        thellier_auto_interpreter.thellier_interpreter_log=logfile
        thellier_auto_interpreter.calc_upper_level_mean(B_specimens,All_grade_A_Recs,sample)
        thellier_interpreter_pars=thellier_auto_interpreter.thellier_interpreter_pars
        interpreter_mean=thellier_interpreter_pars['stdev-opt']['B']
        interpreter_std=thellier_interpreter_pars['stdev-opt']['std']
        interpreter_interval=thellier_interpreter_pars['sample_int_interval_uT']
        if thellier_interpreter_pars['pass_or_fail'] == 'fail':
            thellier_optimizer_master_file.write( "-I- sample/site fail on %s"%(",".join(thellier_interpreter_pars['fail_criteria'])))
        if thellier_interpreter_pars['pass_or_fail'] == 'pass':
            thellier_optimizer_master_file.write( "-I- sample/site %s pass. B=%.2f, STD=%.2f, interval=%.2f"\
        %(sample,interpreter_mean,interpreter_std,interpreter_interval))
        
        # write interpreter data in matrix
        if Key not in Optimizer_STDEV_OPT.keys():
            Optimizer_STDEV_OPT[Key]={}
        if sample not in Optimizer_STDEV_OPT[Key]:
            Optimizer_STDEV_OPT[Key][sample]={}          
        Optimizer_STDEV_OPT[Key][sample]['sample_int_uT']=thellier_interpreter_pars['stdev-opt']['B']
        Optimizer_STDEV_OPT[Key][sample]['sample_int_sigma_uT']=thellier_interpreter_pars['stdev-opt']['std']
        Optimizer_STDEV_OPT[Key][sample]['sample_int_sigma_perc']=thellier_interpreter_pars['stdev-opt']['std_perc']
        Optimizer_STDEV_OPT[Key][sample]['sample_int_interval_uT']=thellier_interpreter_pars['sample_int_interval_uT']
        Optimizer_STDEV_OPT[Key][sample]['sample_int_interavl_perc']=thellier_interpreter_pars['sample_int_interval_perc']             

  #------------------------------------------------------
  # Calcualte the optimization function for different frac and beta
  #------------------------------------------------------

  optimization_functions_matrices={}
    
  for function in optimization_functions:
    optimization_functions_matrices[function]=zeros((len(stat1_range[1]),len(stat2_range[1])))

  stat1_index=0  
  for stat1_value in stat1_range[1]:
    stat2_index=0
    for stat2_value in stat2_range[1]:
      Key="%s,%s"%(str(stat1_value),str(stat2_value))

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
        String="%.2f\t%.2f\t%s\t"%(stat1_value,stat2_value,site)
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

      max_sample_accuracy_uT=0.
      for sample in samples_expected_intensity.keys():
        if sample in Optimizer_STDEV_OPT[Key].keys():
          if 'sample_int_uT_diff_from_expected_uT' in Optimizer_STDEV_OPT[Key][sample].keys():
           max_sample_accuracy_uT= max(max_sample_accuracy_uT,Optimizer_STDEV_OPT[Key][sample]['sample_int_uT_diff_from_expected_uT'])

      max_sample_accuracy_perc=0.
      for sample in samples_expected_intensity.keys():
        if sample in Optimizer_STDEV_OPT[Key].keys():
          if 'sample_int_uT_diff_from_expected_perc' in Optimizer_STDEV_OPT[Key][sample].keys():
           max_sample_accuracy_perc= max(max_sample_accuracy_perc,Optimizer_STDEV_OPT[Key][sample]['sample_int_uT_diff_from_expected_perc'])

      
      for Function in optimization_functions:
        
        #Command="opt_func= %s"%Function
        try:
          optimization_functions_matrices[Function][stat2_index,stat1_index]=eval(Function)
          #optimization_functions_matrices[Function][stat2_index,stat1_index]=opt_func
        except:
          logfile.write(  "-E Error: something is wrong with optimization function %s. Check!\n"%Function)

      stat2_index+=1
    stat1_index+=1
        
  #------------------------------------------------------
  # Make the plots
  #------------------------------------------------------

  #print "WD",WD
  #Command_line="mkdir %s/optimizer/"%(WD)
  try:
    os.mkdir(WD + "/consistency_test/pdf")
  except:
    pass
  try:
    os.mkdir(WD + "/consistency_test/svg")
  except:
    pass


  Fig_counter=0
  for function in optimization_functions:
    if sum(optimization_functions_matrices[function].flatten())==0:
      Fig_counter+=1
      continue
    x,y = meshgrid(stat1_range[1],stat2_range[1])
    cmap = matplotlib.cm.get_cmap('jet')
    figure(Fig_counter,(11,8))
    clf()
    delta_stat1=(stat1_range[1][1]-stat1_range[1][0])/2
    delta_stat2=(stat2_range[1][1]-stat2_range[1][0])/2
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
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = discrete_jet,extent=(stat1_range[1][0]-delta_stat1,stat1_range[1][-1]+delta_stat1,stat2_range[1][-1]+delta_stat2,stat2_range[1][0]-delta_stat2))
    else:
      img = imshow(optimization_functions_matrices[function],interpolation='nearest',cmap = cmap,extent=(stat1_range[1][0]-delta_stat1,stat1_range[1][-1]+delta_stat1,stat2_range[1][-1]+delta_stat2,stat2_range[1][0]-delta_stat2))
      
    xticks(stat1_range[1])
    yticks(stat2_range[1])
    colorbar()

    stat1_index=0
    #if "study_sample_n" in function or "test_group_n" in function:
    if True:
      for stat1_value in stat1_range[1]:
        stat2_index=0
        for stat2_value in stat2_range[1]:
          try:  
            text(stat1_value,stat2_value,"%i"%int(optimization_functions_matrices[function][stat1_index,stat2_index]),fontsize=8,color='gray',horizontalalignment='center',verticalalignment='center')
          except:
              pass  
          stat2_index+=1
        stat1_index+=1

    title("optimization function =\n %s "%function,fontsize=10)
    xlabel(stat1_range[0])
    ylabel(stat2_range[0])
    Ax=gca()
    xticks(rotation=90)
    Ax.set_aspect('auto')
    savefig("%s/consistency_test/pdf/optimization_function_%i"%(WD,Fig_counter) +".pdf")
    savefig("%s/consistency_test/svg/optimization_function_%i"%(WD,Fig_counter) +".svg")
    close()
    Fig_counter+=1        
                
           
  runtime_sec = time.time() - start_time
  m, s = divmod(runtime_sec, 60)
  h, m = divmod(m, 60)
  logfile.write(  "-I- runtime from start (hh:mm:ss) " + "%d:%02d:%02d\n" % (h, m, s))
  logfile.write(  "-I- Finished sucsessfuly.\n")
  logfile.write(  "-I- DONE\n")

  


