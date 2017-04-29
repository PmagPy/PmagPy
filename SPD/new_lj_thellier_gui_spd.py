from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
#============================================================================================
from builtins import input
from builtins import range
from builtins import object
from past.utils import old_div
global CURRENT_VRSION
CURRENT_VRSION = "v.2.03"
#import matplotlib

import numpy
import sys
import os
#import pylab,scipy
##try:
##    import pmag
##except:
##    pass
try:
    import thellier_gui_preferences
except:
    pass
#import copy
#import stat
#import subprocess
#import time
#import random
#import copy

#from pylab import *  # this stuff is being used, don't know all where

#from scipy.optimize import curve_fit

#import thellier_consistency_test


class Arai_GUI(object):
    """ The main frame of the application
    """
    title = "PmagPy Thellier GUI %s"%CURRENT_VRSION
    
    def __init__(self, magic_file = "magic_measurements.txt", WD = "."):
#        print " calling __init__ Arai_gui instance"
#        self.redo_specimens={}

        self.WD = WD
 #       accept_new_parameters_default,accept_new_parameters_null=self.get_default_criteria()    # inialize Null selecting criteria
#        self.accept_new_parameters_null=accept_new_parameters_null
#        self.accept_new_parameters_default=accept_new_parameters_default
        #self.accept_new_parameters=copy.deepcopy(accept_new_parameters_default)
#        preferences=[]
#        self.dpi = 100
        self.magic_file= WD + magic_file
#        self.preferences=preferences
        # inialize selecting criteria
#        accept_new_parameters=self.read_criteria_from_file(self.WD+"/pmag_criteria.txt")          
#        self.accept_new_parameters=accept_new_parameters
        #self.accept_new_parameters=accept_new_parameters
        self.Data,self.Data_hierarchy,self.Data_info={},{},{}

        self.Data_info=self.get_data_info() # get all ages, locations etc. (from er_ages, er_sites, er_locations)
#        print "arai_GUI initialization calling self.get_data()"
        self.Data,self.Data_hierarchy=self.get_data() # Get data from magic_measurements and rmag_anistropy if exist.

        self.Data_samples={}
        self.last_saved_pars={}
        self.specimens=list(self.Data.keys())         # get list of specimens
        self.specimens.sort()                   # get list of specimens

#        self.get_previous_interpretation() # get interpretations from pmag_specimens.txt.  don't even have pmag_specimens.txt
#        print "data info: ", self.Data_info
    
    
        # def get_PI_parameters() should be here (moved to end of file)
    #----------------------------------------------------------------------
                          
    def classy_read_magic_file(self,path,ignore_lines_n,sort_by_this_name): # only called for 'pmag_specimens.txt'
        print("calling classy_read_magic_file() in thellier_gui_spd_lj.py")
        print(path)
        print("not using because we aren't doing the self.get_previous_interpretation call, which is the only function that calls for this one.")

#===========================================================
# calculate PI statistics
#===========================================================


    def get_default_criteria(self):
      #------------------------------------------------
      # read criteria file
      # Format is as pmag_criteria.txt
      #------------------------------------------------
      print("calling get_default_criteria()")
      print("not really using this")
      return False

      
    def get_data(self):
#      print "calling get_data()"
#      print "self", self
#      print "self.Data", self.Data
#      print "magic file:", self.magic_file

      def tan_h(x, a, b): # not called....
#          print "calling tan_h in get_data()"
          return a*tanh(b*x)
    

      #------------------------------------------------
      # Read magic measurement file and sort to blocks
      #------------------------------------------------

      # All data information is stored in Data[specimen]={}
      Data={}
      Data_hierarchy={}
      Data_hierarchy['samples']={}
      Data_hierarchy['specimens']={}

      try:
          meas_data,file_type=self.magic_read(self.magic_file) # returns a tuple of lists of dictionaries.  seems like same stuff as in magic_measurements.txt, but in a different order
# read[1] == file type, i.e. "magic_measurements"
# len(read[0]) == 287
# read[0][0] looks like:  {'treatment_ac_field': '0', 'treatment_dc_field_theta': '90', 'measurement_temp': '273', 'er_citation_names': 'This study', 'measurement_magn_moment': '2.01e-09', 'treatment_temp': '273', 'measurement_number': '1', 'measurement_standard': 'u', 'er_site_name': '0238x', 'er_sample_name': '0238x601104', 'treatment_dc_field_phi': '0', 'measurement_inc': '-8.8', 'er_location_name': '238', 'measurement_dec': '257.6', 'magic_experiment_name': '0238x6011043:LP-PI-TRM:LP-PI-ALT-PTRM:LP-PI-BT-MD:LP-PI-BT-IZZI', 'measurement_flag': 'g', 'er_specimen_name': '0238x6011043', 'measurement_csd': '0.7', 'treatment_dc_field': '0', 'magic_method_codes': 'LT-NO:LP-PI-TRM:LP-PI-ALT-PTRM:LP-PI-BT-MD:LP-PI-BT-IZZI'}
# read[0][1]:
#{'treatment_ac_field': '0', 'treatment_dc_field_theta': '90', 'measurement_temp': '273', 'er_citation_names': 'This study', 'measurement_magn_moment': '1.98e-09', 'treatment_temp': '373', 'measurement_number': '1', 'measurement_standard': 'u', 'er_site_name': '0238x', 'er_sample_name': '0238x601104', 'treatment_dc_field_phi': '0', 'measurement_inc': '-8.1', 'er_location_name': '238', 'measurement_dec': '255.7', 'magic_experiment_name': '0238x6011043:LP-PI-TRM:LP-PI-ALT-PTRM:LP-PI-BT-MD:LP-PI-BT-IZZI', 'measurement_flag': 'g', 'er_specimen_name': '0238x6011043', 'measurement_csd': '0.7', 'treatment_dc_field': '4e-05', 'magic_method_codes': 'LT-T-I:LP-PI-TRM-IZ:LP-PI-TRM:LP-PI-ALT-PTRM:LP-PI-BT-MD:LP-PI-BT-IZZI'}
# so, first is a zero field, heated to 273 and measured at 273.  second is infield, heated to 373 but measured at 273.  
# actual measurements: measurement_magn_moment, measurement_inc, measurement_dec, and measurement_csd.  inc == inclination (how a compass would want to point down through the earth to get to the N pole, at least while in northern hemisphere)  magn_moment = "The product of the pole strength of a magnet and the distance between the poles."  dec == declination.  
      except:
          print("-E- ERROR: Cant read magic_measurement.txt file. File is corrupted.")
          return {},{}

      #print "done Magic read %s " %self.magic_file

      print("-I- Read magic file  %s\n"%self.magic_file)

      # get list of unique specimen names
      
      CurrRec=[]
      #print "get sids"
      sids=self.get_specs(meas_data) # samples ID's.  for rec in data: spec=rec["er_specimen_name"]

      #print "done get sids"

      #print "initialize blocks"
      
      for s in sids:

          if s not in list(Data.keys()): # if a record doesn't already exist for this specimen
              Data[s]={}
              Data[s]['datablock']=[]
              Data[s]['trmblock']=[]
              Data[s]['zijdblock']=[]
          #zijdblock,units=pmag.find_dmag_rec(s,meas_data)
          #Data[s]['zijdblock']=zijdblock


      #print "done initialize blocks"

      #print "sorting meas data"
          
      for rec in meas_data:  # iterates through RECORDS, not specimens.  puts records into appropriate blocks
          s=rec["er_specimen_name"]
          Data[s]['T_or_MW']="T"
          sample=rec["er_sample_name"]

          if  "LP-PI-M" in rec["magic_method_codes"]:
              # if Paleointensity experiment: Microwave demagnetization. 
             Data[s]['T_or_MW']="MW"
          else:
             Data[s]['T_or_MW']="T"
    
          if "magic_method_codes" not in list(rec.keys()):
              rec["magic_method_codes"]=""
          methods=rec["magic_method_codes"].split(":") # LJ UNCOMMENTED THIS, NOT SURE IF IT WORKS!!!
#          print "METHODS", methods
          if "LP-PI-TRM" in rec["magic_method_codes"] or "LP-PI-M" in rec["magic_method_codes"]:
              # if using a lab trm field or Microwave demagnetization:
              Data[s]['datablock'].append(rec)
              # identify the lab DC field
              if ("LT-PTRM-I" in rec["magic_method_codes"] and 'LP-TRM' not in rec["magic_method_codes"] ) or "LT-PMRM-I" in rec["magic_method_codes"]:
                  # if (pTRM check(After zero field step, perform an in field cooling) and NOT TRM acquisition) or pMRM check (After zero field step, perform an in field cooling after heating to lower T with microwave radiation)
                  Data[s]['Thellier_dc_field_uT']=float(rec["treatment_dc_field"])
                  Data[s]['Thellier_dc_field_phi']=float(rec['treatment_dc_field_phi'])
                  Data[s]['Thellier_dc_field_theta']=float(rec['treatment_dc_field_theta'])

                
          if "LP-TRM" in rec["magic_method_codes"]:
              # if TRM acquisition:
              Data[s]['trmblock'].append(rec)

          if "LP-AN-TRM" in rec["magic_method_codes"]:
              # if Anisotropy measurement (TRM acquisition):
              if 'atrmblock' not in list(Data[s].keys()):
                Data[s]['atrmblock']=[]
              Data[s]['atrmblock'].append(rec)


          if "LP-AN-ARM" in rec["magic_method_codes"]:
              # if Anisotropy measurement(ARM acquisition. Measure of anisotropy of anhysteretic susceptibility (AAS) via ARM acquisition (AARM)):
              if 'aarmblock' not in list(Data[s].keys()):
                Data[s]['aarmblock']=[]
              Data[s]['aarmblock'].append(rec)

          if "LP-CR-TRM" in rec["magic_method_codes"]:
              # could not find this code on earthref.org.  must relate to cooling rate, though.
              if 'crblock' not in list(Data[s].keys()):
                Data[s]['crblock']=[]
              Data[s]['crblock'].append(rec)

          #---- Zijderveld block

          EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] # list of excluded lab protocols
          # Anisotropy measurement(ARM acquisition), Anisotropy measurement: TRM acquisition, ARM Acquisition: AF demagnetization, No ARM2, TRM acquisition: AF demagnitization, TRM acquisition, TRM acquisition: Thermal demagnitization, Susceptibility measurement.
          #INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
          INC=["LT-NO","LT-T-Z","LT-M-Z"]
          # No treatments applied before measurement, Specimen cooling: In zero field, Using microwave radiation: In zero field.
          methods=rec["magic_method_codes"].split(":")
          for i in range (len(methods)):
               methods[i]=methods[i].strip()
          if 'measurement_flag' not in list(rec.keys()): rec['measurement_flag']='g'
          skip=1
          for meth in methods:
               if meth in INC:
                   skip=0
          for meth in EX:
               if meth in methods:skip=1
          if skip==0:                      # control flow verifies that an IN method was used, and no EX methods were.  if this is fulfilled, then tr (treatment temperature, or microwave power) is set
             if  'treatment_temp' in list(rec.keys()):
                 tr = float(rec["treatment_temp"])
             elif "treatment_mw_power" in list(rec.keys()):
                 tr = float(rec["treatment_mw_power"])
                 
             if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
                 # if using a laboratory TRM with in-field step then zero-field step or using a microwave TRM with a zero-field step then in-field step. 
                 ZI=0
             else:
                 ZI=1
             Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
             if tr !="":
                 dec,inc,int = "","",""
                 if "measurement_dec" in list(rec.keys()) and rec["measurement_dec"] != "":
                     dec=float(rec["measurement_dec"])
                 if "measurement_inc" in list(rec.keys()) and rec["measurement_inc"] != "":
                     inc=float(rec["measurement_inc"])
                 for key in Mkeys: # grabs whichever magnetic measurement is present in the file
                     if key in list(rec.keys()) and rec[key]!="":int=float(rec[key])
                 if 'magic_instrument_codes' not in list(rec.keys()):rec['magic_instrument_codes']=''
                 #datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 if Data[s]['T_or_MW']=="T":  
                     if tr==0.: tr=273.  # if thermal, and treatment temp has not been set, set it to 273
                 Data[s]['zijdblock'].append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
                 #print methods

       
          if sample not in list(Data_hierarchy['samples'].keys()):
              Data_hierarchy['samples'][sample]=[]
          if s not in Data_hierarchy['samples'][sample]:
              Data_hierarchy['samples'][sample].append(s)

          Data_hierarchy['specimens'][s]=sample

#          samples have many specimens.  
          
      #print "done sorting meas data"
      
      self.specimens=list(Data.keys())
#      self.s = self.specimens[0]  # LORI convenience ADDITION
      self.specimens.sort()

      
      #------------------------------------------------
      # Read anisotropy file from rmag_anisotropy.txt
      #------------------------------------------------
      # not doing any of this right now: no rmag_anisotropy.txt
      #if self.WD != "":
      rmag_anis_data=[]
      results_anis_data=[]
      try:
          rmag_anis_data,file_type=self.magic_read(self.WD+'/rmag_anisotropy.txt')
          print( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
      except:
          print("-W- WARNING cant find rmag_anisotropy in working directory\n")

      try:
          results_anis_data,file_type=self.magic_read(self.WD+'/rmag_results.txt')
          print( "-I- Anisotropy data read  %s/from rmag_anisotropy.txt\n"%self.WD)
          
      except:
          print("-W- WARNING cant find rmag_anisotropy in working directory\n")

          
      for AniSpec in rmag_anis_data:
          s=AniSpec['er_specimen_name']

          if s not in list(Data.keys()):
              print("-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !\n"%s)
              continue
          if 'AniSpec' in list(Data[s].keys()):
              print("-W- WARNING: more than one anisotropy data for specimen %s !\n"%s)
          TYPE=AniSpec['anisotropy_type']
          if 'AniSpec' not in list(Data[s].keys()):
              Data[s]['AniSpec']={}
          Data[s]['AniSpec'][TYPE]=AniSpec
        
      for AniSpec in results_anis_data:
          s=AniSpec['er_specimen_names']
          if s not in list(Data.keys()):
              print("-W- WARNING: specimen %s in rmag_results.txt but not in magic_measurement.txt. Check it !\n"%s)
              continue
          TYPE=AniSpec['anisotropy_type']         
          if 'AniSpec' in list(Data[s].keys()) and TYPE in  list(Data[s]['AniSpec'].keys()):
              Data[s]['AniSpec'][TYPE].update(AniSpec)
              if 'result_description' in list(AniSpec.keys()):
                result_description=AniSpec['result_description'].split(";")
                for description in result_description:
                    if "Critical F" in description:
                       desc=description.split(":")
                       Data[s]['AniSpec'][TYPE]['anisotropy_F_crit']=float(desc[1])
                
                          
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
      #print "searching NLT data" (Non Linear TRM data)
      # may not be important for now.... since my data don't have a trmblock

      for s in self.specimens:
          datablock = Data[s]['datablock']
          trmblock = Data[s]['trmblock']  # if "LP-TRM" in rec["magic_method_codes"]: add to trmblock, but this never happens with my samples
          Data[s]['trmblock'].append(rec)


          if len(trmblock)<2:
              continue

          B_NLT,M_NLT=[],[]  # ?? what are these?

          # find temperature of NLT acquisition
          NLT_temperature=float(trmblock[0]['treatment_temp'])
          
                 
          # search for Blab used in the IZZI experiment (need it for the following calculation)
          found_labfield=False  
          for rec in datablock:  
              if float(rec['treatment_dc_field'])!=0:
                  labfield=float(rec['treatment_dc_field'])
                  found_labfield=True
                  break
          if not found_labfield:
              continue

          # collect the data from trmblock
          M_baseline=0.
          for rec in trmblock:

              # if there is a baseline in TRM block, then use it 
              if float(rec['treatment_dc_field'])==0:
                  M_baseline=float(rec['measurement_magn_moment'])
              B_NLT.append(float(rec['treatment_dc_field']))
              M_NLT.append(float(rec['measurement_magn_moment']))

          # collect more data from araiblock


          for rec in datablock:
              if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field']) !=0:
                  B_NLT.append(float(rec['treatment_dc_field']))
                  M_NLT.append(float(rec['measurement_magn_moment']))
                  
    
          # If cnat find baseline in trm block
          #  search for baseline in the Data block. 
          if M_baseline==0:
              m_tmp=[]
              for rec in datablock:
                  if float(rec['treatment_temp'])==NLT_temperature and float(rec['treatment_dc_field'])==0:
                     m_tmp.append(float(rec['measurement_magn_moment']))
                     print("-I- Found basleine for NLT measurements in datablock, specimen %s\n"%s)         
              if len(m_tmp)>0:
                  M_baseline=mean(m_tmp)
              

          ####  Ron dont delete it ### print "-I- Found %i NLT datapoints for specimen %s: B="%(len(B_NLT),s),numpy.numpy.array(B_NLT)*1e6
    
          #substitute baseline
          M_NLT = numpy.array(M_NLT)-M_baseline
          B_NLT = numpy.array(B_NLT)  
          # calculate M/B ratio for each step, and compare them
          # If cant do NLT correction: check a difference in M/B ratio
          # > 5% : WARNING
          # > 10%: ERROR           

          slopes=old_div(M_NLT,B_NLT) #  B = B_anc / B_lab ??

          if len(trmblock)==2:
              if old_div(max(slopes),min(slopes))<1.05:
                  print("-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n"%s)         
              elif old_div(max(slopes),min(slopes))<1.1:
                  print("-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" %(s,old_div(max(slopes),min(slopes))))
                  #print("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)
              else:
                  print("-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements may be required  !\n" %(s,old_div(max(slopes),min(slopes))))
                  #print("-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT)
                  
          # NLT procedure following Shaar et al (2010)        
          
          if len(trmblock)>2:
              B_NLT=append([0.],B_NLT)
              M_NLT=append([0.],M_NLT)
              
              try:
                  #print s,B_NLT, M_NLT    
                  # First try to fit tanh function (add point 0,0 in the begining)
                  alpha_0=max(M_NLT)
                  beta_0=2e4
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT,p0=(alpha_0,beta_0))
                  M_lab=popt[0]*math.tanh(labfield*popt[1])

                  # Now  fit tanh function to the normalized curve
                  M_NLT_norm=old_div(M_NLT,M_lab)
                  popt, pcov = curve_fit(tan_h, B_NLT, M_NLT_norm,p0=(old_div(popt[0],M_lab),popt[1]))
                  Data[s]['NLT_parameters']={}
                  Data[s]['NLT_parameters']['tanh_parameters']=(popt, pcov)
                  Data[s]['NLT_parameters']['B_NLT']=B_NLT
                  Data[s]['NLT_parameters']['M_NLT_norm']=M_NLT_norm
                  
                  print("-I-  tanh parameters for specimen %s were calculated sucsessfuly\n"%s)
                                  
              except RuntimeError:
                  print( "-W- WARNING: Cant fit tanh function to NLT data specimen %s. Ignore NLT data for specimen %s. Instead check [max(M/B)]/ [min(M/B)] \n"%(s,s))
                  #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  
                  # Cant do NLT correction. Instead, check a difference in M/B ratio
                  # The maximum difference allowd is 5%
                  # if difference is larger than 5%: WARNING            
                  
                  if old_div(max(slopes),min(slopes))<1.05:
                      print("-I- 2 NLT measurement for specimen %s. [max(M/B)/ [min(M/B)] < 1.05.\n"%s)         
                  elif old_div(max(slopes),min(slopes))<1.1:
                      print("-W- WARNING: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  (   > 1.05 and  < 1.1 ). More NLT mrasurements may be required.\n" %(s,old_div(max(slopes),min(slopes))))
                      #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  else:
                      print("-E- ERROR: 2 NLT measurement for specimen %s. [max(M/B)]/ [min(M/B)] is %.2f  ( > 1.1 ). More NLT mrasurements may be required  !\n" %(s,old_div(max(slopes),min(slopes))))
                      #print "-I- NLT meaurements specime %s: B,M="%s,B_NLT,M_NLT
                  
      #print "done searching NLT data"
              
      print("-I- Done calculating non linear TRM parameters for all specimens\n")


      #------------------------------------------------
      # Calculate cooling rate experiments
      #  may not be important...
      #
      #
      #
      #
      #------------------------------------------------

      for s in self.specimens:
          datablock = Data[s]['datablock']
          trmblock = Data[s]['trmblock']
          if 'crblock' in list(Data[s].keys()):
              if len(Data[s]['crblock'])<3:
                  del Data[s]['crblock']
                  continue

              sample=Data_hierarchy['specimens'][s]
              # in MagIC format that cooling rate is in K/My
##              try:
##                  ancient_cooling_rate=float(self.Data_info["er_samples"][sample]['sample_cooling_rate'])
##                  ancient_cooling_rate=ancient_cooling_rate/(1e6*365*24*60) # change to K/minute
##              except:
##                  print("-W- Cant find ancient cooling rate estimation for sample %s"%sample)
##                  continue                  
              try:
                  ancient_cooling_rate=float(self.Data_info["er_samples"][sample]['sample_cooling_rate'])
                  ancient_cooling_rate=old_div(ancient_cooling_rate,(1e6*365*24*60)) # change to K/minute
              except:
                  print("-W- Cant find ancient cooling rate estimation for sample %s"%sample)
                  continue
              self.Data_info["er_samples"]
              cooling_rate_data={}
              cooling_rate_data['pairs']=[]
              cooling_rates_list=[]
              cooling_rate_data['alteration_check']=[]
              for rec in Data[s]['crblock']:
                  magic_method_codes=rec['magic_method_codes'].strip(' ').strip('\n').split(":")
                  measurement_description=rec['measurement_description'].strip(' ').strip('\n').split(":")
                  if "LT-T-Z" in magic_method_codes:
                      # if Specimen cooling: In zero field
                      cooling_rate_data['baseline']=float(rec['measurement_magn_moment'])
                      continue
                
                  index=measurement_description.index("K/min")
                  cooling_rate=float(measurement_description[index-1])
                  cooling_rates_list.append(cooling_rate)
                  moment=float(rec['measurement_magn_moment'])
                  if "LT-T-I" in magic_method_codes:
                      # if Specimen cooling: In laboratory field
                      cooling_rate_data['pairs'].append([cooling_rate,moment])
                  if "LT-PTRM-I" in magic_method_codes:
                      #if pTRM check: After zero field step, perform an in field cooling. 
                      cooling_rate_data['alteration_check']=[cooling_rate,moment]
              lab_cooling_rate=max(cooling_rates_list) 
              cooling_rate_data['lab_cooling_rate']= lab_cooling_rate                  

              #lab_cooling_rate = self.Data[self.s]['cooling_rate_data']['lab_cooling_rate']
              moments=[]
              lab_fast_cr_moments=[]
              lan_cooling_rates=[]
              for pair in cooling_rate_data['pairs']:
                    lan_cooling_rates.append(math.log(old_div(cooling_rate_data['lab_cooling_rate'],pair[0])))
                    moments.append(pair[1])
                    if pair[0]==cooling_rate_data['lab_cooling_rate']:
                        lab_fast_cr_moments.append(pair[1])
              #print s, cooling_rate_data['alteration_check']
              lan_cooling_rates.append(math.log(old_div(cooling_rate_data['lab_cooling_rate'],cooling_rate_data['alteration_check'][0])))
              lab_fast_cr_moments.append(cooling_rate_data['alteration_check'][1])
              moments.append(cooling_rate_data['alteration_check'][1])        

              lab_fast_cr_moment=mean(lab_fast_cr_moments)
              moment_norm=old_div(numpy.array(moments),lab_fast_cr_moment)
              (a,b)=polyfit(lan_cooling_rates, moment_norm, 1)
              #ancient_cooling_rate=0.41
              x0=math.log(old_div(lab_cooling_rate,ancient_cooling_rate))
              y0=a*x0+b
              MAX=max(lab_fast_cr_moments)
              MIN=min(lab_fast_cr_moments)
                      
              alteration_check_perc=100*abs(old_div((MAX-MIN),mean(MAX,MIN)))
              #print s,alteration_check_perc
              #print "--"
              cooling_rate_data['ancient_cooling_rate']=ancient_cooling_rate
              cooling_rate_data['CR_correction_factor']=-999
              cooling_rate_data['lan_cooling_rates']=lan_cooling_rates
              cooling_rate_data['moment_norm']=moment_norm
              cooling_rate_data['polyfit']=[a,b]
              cooling_rate_data['CR_correction_factor_flag']=""
              if y0<=1:
                  cooling_rate_data['CR_correction_factor_flag']=cooling_rate_data['CR_correction_factor_flag']+"bad CR measurement data "
                  cooling_rate_data['CR_correction_factor']=-999

              if alteration_check_perc>5:
                  cooling_rate_data['CR_correction_factor_flag']=cooling_rate_data['CR_correction_factor_flag']+"alteration < 5% "
                  cooling_rate_data['CR_correction_factor']=-999
              if y0>1 and alteration_check_perc<=5:    
                  cooling_rate_data['CR_correction_factor_flag']="calculated"
                  cooling_rate_data['CR_correction_factor']=old_div(1,(y0))
                  
              Data[s]['cooling_rate_data']= cooling_rate_data     
              # at present not generated for my particular specimens
              
               
      # go over all specimens. if there is a specimen with no cooling rate data
      # use the mean cooling rate corretion of the othr specimens from the same sample
      # this cooling rate correction is flagges as "inferred"

      for sample in list(Data_hierarchy['samples'].keys()):
          CR_corrections=[]
          for s in Data_hierarchy['samples'][sample]:
              if 'cooling_rate_data' in list(Data[s].keys()):
                  if 'CR_correction_factor' in list(Data[s]['cooling_rate_data'].keys()):
                      if 'CR_correction_factor_flag' in list(Data[s]['cooling_rate_data'].keys()):
                          if Data[s]['cooling_rate_data']['CR_correction_factor_flag']=='calculated':
                              CR_corrections.append(Data[s]['cooling_rate_data']['CR_correction_factor'])
          if len(CR_corrections) > 0:
              mean_CR_correction=mean(CR_corrections)
          else:
              mean_CR_correction=-1
          if mean_CR_correction != -1:
              for s in Data_hierarchy['samples'][sample]:
                  if 'cooling_rate_data' not in list(Data[s].keys()):
                      Data[s]['cooling_rate_data']={}
                  if 'CR_correction_factor' not in list(Data[s]['cooling_rate_data'].keys()) or\
                     Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
                        Data[s]['cooling_rate_data']['CR_correction_factor']=mean_CR_correction
                        Data[s]['cooling_rate_data']['CR_correction_factor_flag']="inferred"
      
      #------------------------------------------------
      # sort Arai block
      #------------------------------------------------

      #print "sort blocks to arai, zij. etc."

      for s in self.specimens:
        # collected the data
        datablock = Data[s]['datablock']
        zijdblock=Data[s]['zijdblock']  # seems like zijdblock only includes steps done in zero field

        if len(datablock) <4:
           print("-E- ERROR: skipping specimen %s, not enough measurements - moving forward \n"%s)
           del Data[s]
           sample=Data_hierarchy['specimens'][s]
           del Data_hierarchy['specimens'][s]
           Data_hierarchy['samples'][sample].remove(s)
           continue 
        araiblock,field=self.sortarai(datablock,s,0)
    

        Data[s]['araiblock']=araiblock  # temp, declination, inclination, magnetic moment, ?.  
        Data[s]['pars']={}
        Data[s]['pars']['lab_dc_field']=field
        Data[s]['pars']['er_specimen_name']=s
        Data[s]['pars']['er_sample_name']=Data_hierarchy['specimens'][s]

        Data[s]['lab_dc_field']=field
        Data[s]['er_specimen_name']=s   
        Data[s]['er_sample_name']=Data_hierarchy['specimens'][s]
        
        first_Z=araiblock[0]  # all the specimen's zerofield measurements
        #if len(first_Z)<3:
            #continue

        if len(araiblock[0])!= len(araiblock[1]):
           print( "-E- ERROR: unequal length of Z steps and I steps. Check specimen %s"% s)
           #continue

      # Fix zijderveld block for Thellier-Thellier protocol (II)
      # (take the vector subtruiction instead of the zerofield steps)
      #araiblock,field=self.sortarai(Data[s]['datablock'],s,0)
      #if "LP-PI-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-M-II" in Data[s]['datablock'][0]["magic_method_codes"] or "LP-PI-T-II" in Data[s]['datablock'][0]["magic_method_codes"]:
      #    for zerofield in araiblock[0]:
      #        Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])
        if "LP-PI-II" in datablock[0]["magic_method_codes"] or "LP-PI-M-II" in datablock[0]["magic_method_codes"] or "LP-PI-T-II" in datablock[0]["magic_method_codes"]:
          for zerofield in araiblock[0]:
              Data[s]['zijdblock'].append([zerofield[0],zerofield[1],zerofield[2],zerofield[3],0,'g',""])


        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------

        z_temperatures=[row[0] for row in zijdblock]
        zdata=[]
        vector_diffs=[]
        NRM=zijdblock[0][3]  ## NRM before anything has been done to the sample

        for k in range(len(zijdblock)):
            DIR=[zijdblock[k][1],zijdblock[k][2],old_div(zijdblock[k][3],NRM)]
            cart=self.dir2cart(DIR)
            zdata.append(numpy.array([cart[0],cart[1],cart[2]]))
            if k>0:
                vector_diffs.append(numpy.sqrt(sum((numpy.array(zdata[-2])-numpy.array(zdata[-1]))**2)))
        vector_diffs.append(numpy.sqrt(sum(numpy.array(zdata[-1])**2))) # last vector of the vds
        vds=sum(vector_diffs)  # vds calculation       
        zdata=numpy.array(zdata)
    
        Data[s]['vector_diffs']=numpy.array(vector_diffs)
        Data[s]['vds']=vds
        Data[s]['zdata']=zdata
        Data[s]['z_temp']=z_temperatures
        
      #--------------------------------------------------------------    
      # Rotate zijderveld plot
      #--------------------------------------------------------------

        DIR_rot=[]
        CART_rot=[]
        # rotate to be as NRM
        NRM_dir=self.cart2dir(Data[s]['zdata'][0])
         
        NRM_dec=NRM_dir[0]
        NRM_dir[0]=0
        CART_rot.append(self.dir2cart(NRM_dir))

        
        for i in range(1,len(Data[s]['zdata'])):
          DIR=self.cart2dir(Data[s]['zdata'][i])
          DIR[0]=DIR[0]-NRM_dec
          CART_rot.append(numpy.array(self.dir2cart(DIR)))
          #print numpy.array(dir2cart(DIR))
          
        CART_rot=numpy.array(CART_rot)
        Data[s]['zij_rotated']=CART_rot
        #--------------------------------------------------------------
        # collect all Arai plot data points to array 
        #--------------------------------------------------------------
    
        # collect Arai data points
        zerofields,infields=araiblock[0],araiblock[1]  # first_Z, first_I
        
        Data[s]['NRMS']=zerofields
        Data[s]['PTRMS']=infields
        Data[s]['NRM']=NRM
        
        x_Arai,y_Arai=[],[] # all the data points               
        t_Arai=[]
        steps_Arai=[]              

        #NRM=zerofields[0][3]    #  this is the first measurement of NRM, before anything has been done to the sample
        infield_temperatures=[row[0] for row in infields]

        for k in range(len(zerofields)):                  
          index_infield=infield_temperatures.index(zerofields[k][0])
          x_Arai.append(old_div(infields[index_infield][3],NRM))   #  from infields point: x = magnetic strength / NRM
          y_Arai.append(old_div(zerofields[k][3],NRM))  # from corresponding zerofield point: y = magnetic strength / NRM
          t_Arai.append(zerofields[k][0])  # temperature.  .
          if zerofields[k][4]==1:   
            steps_Arai.append('ZI')
          else:
            steps_Arai.append('IZ')        
        x_Arai=numpy.array(x_Arai)
        y_Arai=numpy.array(y_Arai)
        #else:
        #    Data[s]['pars']['magic_method_codes']=""
        Data[s]['x_Arai']=x_Arai
        Data[s]['y_Arai']=y_Arai
        Data[s]['t_Arai']=t_Arai
        Data[s]['steps_Arai']=steps_Arai


        #--------------------------------------------------------------
        # collect all pTRM check to array 
        #--------------------------------------------------------------

        ptrm_checks = araiblock[2]
        zerofield_temperatures=[row[0] for row in zerofields]

        x_ptrm_check,y_ptrm_check,ptrm_checks_temperatures,=[],[],[]
        x_ptrm_check_starting_point,y_ptrm_check_starting_point,ptrm_checks_starting_temperatures=[],[],[]
        for k in range(len(ptrm_checks)):
          if ptrm_checks[k][0] in zerofield_temperatures:
            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec=datablock[i]                
                if "LT-PTRM-I" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_checks[k][0]:
                    starting_temperature=(float(datablock[i-1]['treatment_temp']))

                    try:
                        index=t_Arai.index(starting_temperature)
                        x_ptrm_check_starting_point.append(x_Arai[index])
                        y_ptrm_check_starting_point.append(y_Arai[index])
                        ptrm_checks_starting_temperatures.append(starting_temperature)

                        index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                        x_ptrm_check.append(old_div(ptrm_checks[k][3],NRM))
                        y_ptrm_check.append(old_div(zerofields[index_zerofield][3],NRM))
                        ptrm_checks_temperatures.append(ptrm_checks[k][0])
                    except:
                        pass
                    
                # microwave
                if "LT-PMRM-I" in rec['magic_method_codes'] and float(rec['treatment_mw_power'])==ptrm_checks[k][0]:
                    starting_temperature=(float(datablock[i-1]['treatment_mw_power']))
                    
                    try:
                        index=t_Arai.index(starting_temperature)
                        x_ptrm_check_starting_point.append(x_Arai[index])
                        y_ptrm_check_starting_point.append(y_Arai[index])
                        ptrm_checks_starting_temperatures.append(starting_temperature)

                        index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                        x_ptrm_check.append(old_div(ptrm_checks[k][3],NRM))
                        y_ptrm_check.append(old_div(zerofields[index_zerofield][3],NRM))
                        ptrm_checks_temperatures.append(ptrm_checks[k][0])
                    except:
                        pass

                    
        x_ptrm_check=numpy.array(x_ptrm_check)  
        ptrm_check=numpy.array(y_ptrm_check)
        ptrm_checks_temperatures=numpy.array(ptrm_checks_temperatures)
        Data[s]['PTRM_Checks'] = ptrm_checks
        Data[s]['x_ptrm_check']=x_ptrm_check
        Data[s]['y_ptrm_check']=y_ptrm_check        
        Data[s]['ptrm_checks_temperatures']=ptrm_checks_temperatures
        Data[s]['x_ptrm_check_starting_point']=numpy.array(x_ptrm_check_starting_point)
        Data[s]['y_ptrm_check_starting_point']=numpy.array(y_ptrm_check_starting_point)               
        Data[s]['ptrm_checks_starting_temperatures']=numpy.array(ptrm_checks_starting_temperatures)
##        if len(ptrm_checks_starting_temperatures) != len(ptrm_checks_temperatures):
##            print s
##            print Data[s]['ptrm_checks_temperatures']
##            print Data[s]['ptrm_checks_starting_temperatures']
##            print "help"
            
        #--------------------------------------------------------------
        # collect tail checks 
        #--------------------------------------------------------------


        ptrm_tail = araiblock[3]
        #print ptrm_tail
        x_tail_check,y_tail_check,tail_check_temperatures=[],[],[]
        x_tail_check_starting_point,y_tail_check_starting_point,tail_checks_starting_temperatures=[],[],[]

        for k in range(len(ptrm_tail)):
          if ptrm_tail[k][0] in zerofield_temperatures:

            # find the starting point of the pTRM check:
            for i in range(len(datablock)):
                rec=datablock[i]                
                if "LT-PTRM-MD" in rec['magic_method_codes'] and float(rec['treatment_temp'])==ptrm_tail[k][0]:
                    starting_temperature=(float(datablock[i-1]['treatment_temp']))
                    try:

                        index=t_Arai.index(starting_temperature)
                        x_tail_check_starting_point.append(x_Arai[index])
                        y_tail_check_starting_point.append(y_Arai[index])
                        tail_checks_starting_temperatures.append(starting_temperature)

                        index_infield=infield_temperatures.index(ptrm_tail[k][0])
                        x_tail_check.append(old_div(infields[index_infield][3],NRM))
                        y_tail_check.append(old_div(ptrm_tail[k][3],NRM) + old_div(zerofields[index_infield][3],NRM))
                        tail_check_temperatures.append(ptrm_tail[k][0])

                        break
                    except:
                        pass


##              index_infield=infield_temperatures.index(ptrm_tail[k][0])
##              x_tail_check.append(infields[index_infield][3]/NRM)
##              y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
##              tail_check_temperatures.append(ptrm_tail[k][0])

        x_tail_check=numpy.array(x_tail_check)  
        y_tail_check=numpy.array(y_tail_check)
        tail_check_temperatures=numpy.array(tail_check_temperatures)
        x_tail_check_starting_point=numpy.array(x_tail_check_starting_point)
        y_tail_check_starting_point=numpy.array(y_tail_check_starting_point)
        tail_checks_starting_temperatures=numpy.array(tail_checks_starting_temperatures)
        
        Data[s]['TAIL_Checks'] = ptrm_tail
        Data[s]['x_tail_check']=x_tail_check
        Data[s]['y_tail_check']=y_tail_check
        Data[s]['tail_check_temperatures']=tail_check_temperatures
        Data[s]['x_tail_check_starting_point']=x_tail_check_starting_point
        Data[s]['y_tail_check_starting_point']=y_tail_check_starting_point
        Data[s]['tail_checks_starting_temperatures']=tail_checks_starting_temperatures


        #--------------------------------------------------------------     
        # collect additivity checks                                                                 
        #--------------------------------------------------------------      

        
        additivity_checks = araiblock[6]
        x_AC,y_AC,AC_temperatures,AC=[],[],[],[]
        x_AC_starting_point,y_AC_starting_point,AC_starting_temperatures=[],[],[]
        
        tmp_data_block=list(numpy.array(datablock, copy=True))
        for k in range(len(additivity_checks)):
          if additivity_checks[k][0] in zerofield_temperatures:
            for i in range(len(tmp_data_block)):
                rec=tmp_data_block[i]
                if "LT-PTRM-AC" in rec['magic_method_codes'] and float(rec['treatment_temp'])==additivity_checks[k][0]:
                    del(tmp_data_block[i])
                    break

            # find the infield step that comes before the additivity check                                               
            foundit=False
            for j in range(i-1,1,-1):
                if "LT-T-I" in tmp_data_block[j]['magic_method_codes']:
                  found_starting_temperature=True
                  starting_temperature=float(tmp_data_block[j]['treatment_temp']);
                  break
            #for j in range(len(Data[s]['t_Arai'])):                        
            #    print Data[s]['t_Arai'][j]                                                   
            #    if float(Data[s]['t_Arai'][j])==additivity_checks[k][0]:                    
            #      found_zerofield_step=True                                                           
            #      pTRM=Data[s]['x_Arai'][j]                                                             
            #      AC=Data[s]['x_Arai'][j]-additivity_checks[k][3]/NRM                           
            #      break                                                                    

            if found_starting_temperature:
                try:
                    index=t_Arai.index(starting_temperature)
                    x_AC_starting_point.append(x_Arai[index])
                    y_AC_starting_point.append(y_Arai[index])
                    AC_starting_temperatures.append(starting_temperature)

                    index_zerofield=zerofield_temperatures.index(additivity_checks[k][0])
                    x_AC.append(old_div(additivity_checks[k][3],NRM))
                    y_AC.append(old_div(zerofields[index_zerofield][3],NRM))
                    AC_temperatures.append(additivity_checks[k][0])
                    index_pTRMs=t_Arai.index(additivity_checks[k][0])
                    AC.append(old_div(additivity_checks[k][3],NRM) - x_Arai[index_pTRMs]) 
                    # above is not using pTRM_star, but x_add_check -  pTRM(Ti)
                    #lj
                    # this is the intensity from the additivity checks araiblock normed by the initial nrm, - the equivalent ptrm value from the previous infield step (I think).  x_Arai is also taken directly from direction (intensity)
                    #print " "
                    #print "x_AC_starting_point", x_AC_starting_point[-1]
                    #print "x_AC", x_AC[-1]
                    #print 'additivity_checks[k][3]/NRM - x_Arai[index_pTRMs]'
                    #print 'index_pTRMs', index_pTRMs
                    #print 'AC = ', additivity_checks[k][3]/NRM, '-', x_Arai[index_pTRMs]
                    #print ""
                    #lj

                except:
                    pass

        x_AC=numpy.array(x_AC)
        y_AC=numpy.array(y_AC)
        AC_temperatures=numpy.array(AC_temperatures)
        x_AC_starting_point=numpy.array(x_AC_starting_point)
        y_AC_starting_point=numpy.array(y_AC_starting_point)
        AC_starting_temperatures=numpy.array(AC_starting_temperatures)
        AC=numpy.array(AC)

        Data[s]['additivity_checks'] = additivity_checks
        Data[s]['AC']=AC
        Data[s]['x_additivity_check']=x_AC
        Data[s]['y_additivity_check']=y_AC
        Data[s]['additivity_check_temperatures']=AC_temperatures
        Data[s]['x_additivity_check_starting_point']=x_AC_starting_point
        Data[s]['y_additivity_check_starting_point']=y_AC_starting_point
        Data[s]['additivity_check_starting_temperatures']=AC_starting_temperatures
      



        
      print("-I- number of specimens in this project directory: %i\n"%len(self.specimens))
      print("-I- number of samples in this project directory: %i\n"%len(list(Data_hierarchy['samples'].keys())))

      #print "done sort blocks to arai, zij. etc."
#      print "returning Data, data_hierarchy.  This is the completion of self.get_data().  printing Data['0238x5721062']"
#      print str(Data["0238x5721062"])[:500] + "...."
#      print "done with get_data"
      return(Data,Data_hierarchy)





      
 # zebra.  end of get_data()

    #--------------------------------------------------------------    
    # Read all information file (er_locations, er_samples, er_sites, er_ages)
    #--------------------------------------------------------------
    def get_data_info(self):
#        print "calling get_data_info()"
        Data_info={}
        data_er_samples={}
        data_er_ages={}
        data_er_sites={}

    
        # samples
        # read_magic_file takes 2 args
        # other_read_magic_file takes 4 args (including self) 
        def read_magic_file(path,sort_by_this_name):
            # called for er_ages, er_sites, er_samples
#            print "Calling read_magic_file() in get_data_info"
 #           print path
            DATA={}
            fin=open(path,'r')
            fin.readline()
            line=fin.readline()
            header=line.strip('\n').split('\t')
            for line in fin.readlines():
                tmp_data={}
                tmp_line=line.strip('\n').split('\t')
                for i in range(len(tmp_line)):
                    tmp_data[header[i]]=tmp_line[i]
                DATA[tmp_data[sort_by_this_name]]=tmp_data
            fin.close()        
 #           print "Data from read_magic_file in get_data info:  ", DATA
            return(DATA)
        
        try:
            data_er_samples=read_magic_file(self.WD+"/er_samples.txt",'er_sample_name')
        except:
            print("-W- Cant find er_sample.txt in project directory\n")
    
        try:
            data_er_sites=read_magic_file(self.WD+"/er_sites.txt",'er_site_name')
        except:
            print ("-W- Cant find er_sites.txt in project directory\n")

        try:
            data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_sample_name')
        except:
            try:
                data_er_ages=read_magic_file(self.WD+"/er_ages.txt",'er_site_name')
            except:    
                print ("-W- Cant find er_ages in project directory\n")
    

        Data_info["er_samples"]=data_er_samples
        Data_info["er_sites"]=data_er_sites
        Data_info["er_ages"]=data_er_ages
        
#        print "data_info"
#        print str(Data_info)[:500]
        return(Data_info)

    #--------------------------------------------------------------    
    # Read previose interpretation from pmag_specimens.txt (if exist)
    #--------------------------------------------------------------
    # deleted #    def get_previous_interpretation(self):
    def get_previous_interpretation(self):
        print("calling get_previous_interpretation()")
        print("but not actually using")
        return False


#===========================================================
#  definitions inherited from pmag.py
#===========================================================
    
                
    def cart2dir(self,cart):
        """
        converts a direction to cartesian coordinates
        """
#        print "calling cart2dir(), not in anything"
        cart=numpy.array(cart)
        rad=old_div(numpy.pi,180.) # constant to convert degrees to radians
        if len(cart.shape)>1:
            Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
        else: #single vector
            Xs,Ys,Zs=cart[0],cart[1],cart[2]
        Rs=numpy.sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
        Decs=(old_div(numpy.arctan2(Ys,Xs),rad))%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
        try:
            Incs=old_div(numpy.arcsin(old_div(Zs,Rs)),rad) # calculate inclination (converting to degrees) # 
        except:
            print('trouble in cart2dir') # most likely division by zero somewhere
            return numpy.zeros(3)
            
        return numpy.array([Decs,Incs,Rs]).transpose() # return the directions list


    def dir2cart(self,d):
#        print "calling dir2cart(), not in anything"
       # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
        ints=numpy.ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
        d = numpy.array(d)
        rad=old_div(numpy.pi,180.)
        if len(d.shape)>1: # array of vectors
            decs,incs=d[:,0]*rad,d[:,1]*rad
            if d.shape[1]==3: ints=d[:,2] # take the given lengths
        else: # single vector
            decs,incs=numpy.array(d[0])*rad,numpy.array(d[1])*rad
            if len(d)==3: 
                ints=numpy.array(d[2])
            else:
                ints=numpy.array([1.])
        cart= numpy.array([ints*numpy.cos(decs)*numpy.cos(incs),ints*numpy.sin(decs)*numpy.cos(incs),ints*numpy.sin(incs)]).transpose()
        return cart



    def magic_read(self,infile):
        """ 
        reads  a Magic template file, puts data in a list of dictionaries
        """
#        print "calling magic_read(self, infile)", infile
        hold,magic_data,magic_record,magic_keys=[],[],{},[]
        try:
            f=open(infile,"r")
        except:
            return [],'bad_file'
        d = f.readline()[:-1].strip('\n')
        if d[0]=="s" or d[1]=="s":
            delim='space'
        elif d[0]=="t" or d[1]=="t":
            delim='tab'
        else: 
            print('error reading ', infile)
            sys.exit()
        if delim=='space':file_type=d.split()[1]
        if delim=='tab':file_type=d.split('\t')[1]
        if file_type=='delimited':
            if delim=='space':file_type=d.split()[2]
            if delim=='tab':file_type=d.split('\t')[2]
        if delim=='space':line =f.readline()[:-1].split()
        if delim=='tab':line =f.readline()[:-1].split('\t')
        for key in line:
            magic_keys.append(key)
        lines=f.readlines()
        for line in lines[:-1]:
            line.replace('\n','')
            if delim=='space':rec=line[:-1].split()
            if delim=='tab':rec=line[:-1].split('\t')
            hold.append(rec)
        line = lines[-1].replace('\n','')
        if delim=='space':rec=line[:-1].split()
        if delim=='tab':rec=line.split('\t')
        hold.append(rec)
        for rec in hold:
            magic_record={}
            if len(magic_keys) != len(rec):
                
                print("Warning: Uneven record lengths detected: ")
                #print magic_keys
                #print rec
            for k in range(len(rec)):
               magic_record[magic_keys[k]]=rec[k].strip('\n')
            magic_data.append(magic_record)
        magictype=file_type.lower().split("_")
        Types=['er','magic','pmag','rmag']
        if magictype in Types:file_type=file_type.lower()
#        print "magic data from magic_read:"
#        print str(magic_data)[:500] + "..."
#        print "file_type", file_type
        return magic_data,file_type


    def get_specs(self,data):
        """
         takes a magic format file and returns a list of unique specimen names
        """
    # sort the specimen names
    #
#        print "calling get_specs()"
        speclist=[]
        for rec in data:
          spec=rec["er_specimen_name"]
          if spec not in speclist:speclist.append(spec)
        speclist.sort()
        #print speclist
        return speclist
    


    def sortarai(self,datablock,s,Zdiff):
        """
         sorts data block in to first_Z, first_I, etc.
        """
#        print "calling sortarai()"
        first_Z,first_I,zptrm_check,ptrm_check,ptrm_tail=[],[],[],[],[]
        field,phi,theta="","",""
        starthere=0
        Treat_I,Treat_Z,Treat_PZ,Treat_PI,Treat_M,Treat_AC=[],[],[],[],[],[]
        ISteps,ZSteps,PISteps,PZSteps,MSteps,ACSteps=[],[],[],[],[],[]
        GammaChecks=[] # comparison of pTRM direction acquired and lab field
        Mkeys=['measurement_magn_moment','measurement_magn_volume','measurement_magn_mass','measurement_magnitude']
        rec=datablock[0]  # finds which type of magnetic measurement is present in magic_measurements.txt, then assigns momkey to that value
        for key in Mkeys:
            if key in list(rec.keys()) and rec[key]!="":
                momkey=key
                break
    # first find all the steps
        for k in range(len(datablock)):  # iterates through records.  
            rec=datablock[k]
            if "treatment_temp" in list(rec.keys()):
                temp=float(rec["treatment_temp"])
            elif "treatment_mw_power" in list(rec.keys()):
                temp=float(rec["treatment_mw_power"])
                
            methcodes=[]
            tmp=rec["magic_method_codes"].split(":")
            for meth in tmp:
                methcodes.append(meth.strip())
                # methchodes contains all codes for a particular record
            # for thellier-thellier
            if 'LT-T-I' in methcodes and 'LP-PI-TRM' in methcodes and 'LP-TRM' not in methcodes :
                # IF specimen cooling AND using a laboratory trm AND NOT trm acquisition
                Treat_I.append(temp)
                ISteps.append(k)
                if field=="":field=float(rec["treatment_dc_field"])
                if phi=="":
                    phi=float(rec['treatment_dc_field_phi'])
                    theta=float(rec['treatment_dc_field_theta'])
                    
            # for Microwave
            if 'LT-M-I' in methcodes and 'LP-PI-M' in methcodes :
                # if using microwave radiation in lab field AND using microwave demagnetisation 
                Treat_I.append(temp)
                ISteps.append(k)
                if field=="":field=float(rec["treatment_dc_field"])
                if phi=="":
                    phi=float(rec['treatment_dc_field_phi'])
                    theta=float(rec['treatment_dc_field_theta'])

    # stick  first zero field stuff into first_Z 
            if 'LT-NO' in methcodes:
                # if no treatments applied before measurements
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-T-Z' in methcodes or 'LT-M-Z' in methcodes: 
                # if specimen cooling in zero field OR using microwave radiation: In zero field
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-PTRM-Z' : # maybe this should be in methcodes ??  note I no longer understand
                # if pTRM tail check
                Treat_PZ.append(temp)
                PZSteps.append(k)
            if 'LT-PTRM-I' in methcodes or 'LT-PMRM-I' in methcodes:
                # if pTRM check
                Treat_PI.append(temp)
                PISteps.append(k)
            if 'LT-PTRM-MD' in methcodes:
                # if pTRM tail check
                Treat_M.append(temp)
                MSteps.append(k)
            if 'LT-PTRM-AC' in methcodes or 'LT-PMRM-AC' in methcodes:
                Treat_AC.append(temp)
                ACSteps.append(k)
            if 'LT-NO' in methcodes:
                # if no treatments applied before measurement
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                str=float(rec[momkey])
                if 'LP-PI-M'  not in methcodes:
                    # if not using microwave demagnetisation
                    first_I.append([273,0.,0.,0.,1])
                    first_Z.append([273,dec,inc,str,1])  # NRM step
                else:
                    first_I.append([0,0.,0.,0.,1])
                    first_Z.append([0,dec,inc,str,1])  # NRM step
                    
                    # the block above seems to be sorting out into wheter it is Treat_Z (zero field), Treat_I (infield), a ptrm check, or a ptrm tail check. so, each record has been appended to whichever of those it belongs in. 
        #---------------------
        # find  IZ and ZI
        #---------------------
        
                
        for temp in Treat_I: # look through infield steps and find matching Z step
            if temp in Treat_Z: # found a match
                istep=ISteps[Treat_I.index(temp)]
                irec=datablock[istep]
                methcodes=[]
                tmp=irec["magic_method_codes"].split(":")
                for meth in tmp: methcodes.append(meth.strip())
                brec=datablock[istep-1] # take last record as baseline to subtract  
                zstep=ZSteps[Treat_Z.index(temp)]
                zrec=datablock[zstep]
        # sort out first_Z records 
                if "LP-PI-TRM-IZ" in methcodes or "LP-PI-M-IZ" in methcodes: 
                    ZI=0    
                else:   
                    ZI=1    
                dec=float(zrec["measurement_dec"])
                inc=float(zrec["measurement_inc"])
                str=float(zrec[momkey])
                first_Z.append([temp,dec,inc,str,ZI])
        # sort out first_I records 
                #print 'irec', irec # full data set for infield measurement
                #print 'zrec', zrec # coresponding zerofield measurement
                idec=float(irec["measurement_dec"])
                iinc=float(irec["measurement_inc"])
                istr=float(irec[momkey])
                X=self.dir2cart([idec,iinc,istr])
                BL=self.dir2cart([dec,inc,str])
                I=[]
                for c in range(3): 
                    I.append((X[c]-BL[c]))
                iDir=self.cart2dir(I)
                first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                now_ignore = """
                #if I[2]!=0: # lj PUT THIS BACK
                if True:
                    iDir=self.cart2dir(I)
                    if Zdiff==0:
                        print "Zdiff == 0, appending to first_I" #lj
                        print [temp,iDir[0],iDir[1],iDir[2],ZI] #lj
                        first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                    else:
                        print "Zdiff != 0, appending to first_I" #lj
                        print [temp,0.,0.,I[2],ZI]  #lj
                        first_I.append([temp,0.,0.,I[2],ZI])
##                    gamma=angle([iDir[0],iDir[1]],[phi,theta])
                else:
                    print "0,0,0 appending to first_I"
                    print [temp,0.,0.,0.,ZI]
                    first_I.append([temp,0.,0.,0.,ZI])
##                    gamma=0.0
##    # put in Gamma check (infield trm versus lab field)
##                if 180.-gamma<gamma:
##                    gamma=180.-gamma
##                GammaChecks.append([temp-273.,gamma])
                 """

        #---------------------
        # find Thellier Thellier protocol
        #---------------------
        if 'LP-PI-II'in methcodes or 'LP-PI-T-II' in methcodes or 'LP-PI-M-II' in methcodes:
            for i in range(1,len(Treat_I)): # look through infield steps and find matching Z step
                if Treat_I[i] == Treat_I[i-1]:
                    # ignore, if there are more than 
                    temp= Treat_I[i]
                    irec1=datablock[ISteps[i-1]]
                    dec1=float(irec1["measurement_dec"])
                    inc1=float(irec1["measurement_inc"])
                    moment1=float(irec1["measurement_magn_moment"])
                    if len(first_I)<2:
                        dec_initial=dec1;inc_initial=inc1
                    cart1=numpy.array(self.dir2cart([dec1,inc1,moment1]))
                    irec2=datablock[ISteps[i]]
                    dec2=float(irec2["measurement_dec"])
                    inc2=float(irec2["measurement_inc"])
                    moment2=float(irec2["measurement_magn_moment"])
                    cart2=numpy.array(self.dir2cart([dec2,inc2,moment2]))

                    # check if its in the same treatment
                    if Treat_I[i] == Treat_I[i-2] and dec2!=dec_initial and inc2!=inc_initial:
                        continue
                    if dec1!=dec2 and inc1!=inc2:
                        zerofield=old_div((cart2+cart1),2)
                        infield=old_div((cart2-cart1),2)

                        DIR_zerofield=self.cart2dir(zerofield)
                        DIR_infield=self.cart2dir(infield)

                        first_Z.append([temp,DIR_zerofield[0],DIR_zerofield[1],DIR_zerofield[2],0])
                        print("appending to first_I") # LJ remove this
                        print([temp,DIR_infield[0],DIR_infield[1],DIR_infield[2],0]) # LJ remove this
                        first_I.append([temp,DIR_infield[0],DIR_infield[1],DIR_infield[2],0])
    

        #---------------------
        # find  pTRM checks
        #---------------------
                    
        for temp in Treat_PI: # look through infield steps and find matching Z step
            if 'LP-PI-II' not in methcodes:
                step=PISteps[Treat_PI.index(temp)]
                rec=datablock[step]
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                str=float(rec[momkey])
                brec=datablock[step-1] # take last record as baseline to subtract
                pdec=float(brec["measurement_dec"])
                pinc=float(brec["measurement_inc"])
                pint=float(brec[momkey])
                X=self.dir2cart([dec,inc,str])
                prevX=self.dir2cart([pdec,pinc,pint])
                I=[]
                for c in range(3): I.append(X[c]-prevX[c])
                dir1=self.cart2dir(I)
                if Zdiff==0:
                    ptrm_check.append([temp,dir1[0],dir1[1],dir1[2]])
                else:
                    ptrm_check.append([temp,0.,0.,I[2]])
            else:
                step=PISteps[Treat_PI.index(temp)]
                rec=datablock[step]
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                moment=float(rec["measurement_magn_moment"])
                for zerofield in first_Z:
                    if zerofield[0]==temp:
                        M1=numpy.array(self.dir2cart([dec,inc,moment]))
                        M2=numpy.array(self.dir2cart([zerofield[1],zerofield[2],zerofield[3]]))
                        diff=M1-M2
                        diff_cart=self.cart2dir(diff)
                        ptrm_check.append([temp,diff_cart[0],diff_cart[1],diff_cart[2]])
                        
                        
                        
    # in case there are zero-field pTRM checks (not the SIO way)
        for temp in Treat_PZ:
            step=PZSteps[Treat_PZ.index(temp)]
            rec=datablock[step]
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            brec=datablock[step-1]
            pdec=float(brec["measurement_dec"])
            pinc=float(brec["measurement_inc"])
            pint=float(brec[momkey])
            X=self.dir2cart([dec,inc,str])
            prevX=self.dir2cart([pdec,pinc,pint])
            I=[]
            for c in range(3): I.append(X[c]-prevX[c])
            dir2=self.cart2dir(I)
            zptrm_check.append([temp,dir2[0],dir2[1],dir2[2]])
        ## get pTRM tail checks together -
        for temp in Treat_M:
            step=MSteps[Treat_M.index(temp)] # tail check step - just do a difference in magnitude!
            rec=datablock[step]
            str=float(rec[momkey])
            if temp in Treat_Z:
                step=ZSteps[Treat_Z.index(temp)]
                brec=datablock[step]
                pint=float(brec[momkey])
                ptrm_tail.append([temp,0,0,str-pint])  # difference - if negative, negative tail!
            else:
                print(s, '  has a tail check with no first zero field step - check input file! for step',temp-273.)
    #
    # final check
    #
        if len(first_Z)!=len(first_I):
                   print(len(first_Z),len(first_I))
                   print(" Something wrong with this specimen! Better fix it or delete it ")
                   input(" press return to acknowledge message")

       #---------------------                                                                         
        # find  Additivity (patch by rshaar)                                                           
        #---------------------                                                                         

        additivity_check=[]
        for i in range(len(Treat_AC)):
            step_0=ACSteps[i]
            temp=Treat_AC[i]
            dec0=float(datablock[step_0]["measurement_dec"])
            inc0=float(datablock[step_0]["measurement_inc"])
            moment0=float(datablock[step_0]['measurement_magn_moment'])
            V0=self.dir2cart([dec0,inc0,moment0])

            # find the infield step that comes before the additivity check                             
            foundit=False
            for j in range(step_0,1,-1):
                if "LT-T-I" in datablock[j]['magic_method_codes']:
                  foundit=True ; break
            if foundit:
                dec1=float(datablock[j]["measurement_dec"])
                inc1=float(datablock[j]["measurement_inc"])
                moment1=float(datablock[j]['measurement_magn_moment'])
                #lj
                start_temp=float(datablock[j]['treatment_temp']);
                #lj
                V1=self.dir2cart([dec1,inc1,moment1]) 

                I=[]
                #print "temp (K)", temp - 273
                #print "start_temp (K)", start_temp - 273
                #print "dec0: {}, inc0: {}, moment0: {}".format(dec0, inc0, moment0)
                #print "V0: ", V0
                #print "dec1: {}, inc1: {}, moment1: {}".format(dec1, inc1,moment1)
                #print "V1: ", V1
                #print "---"
                for c in range(3): I.append(V1[c]-V0[c])
                dir1=self.cart2dir(I)
                additivity_check.append([temp,dir1[0],dir1[1],dir1[2]])
        
        araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks,additivity_check)

#        print "done with sortarai()"
#        print "araiblock[0] (first_Z) "
        #  [[273, 277.5, 79.6, 1.66e-09, 1], .....]
#        print araiblock[0]
#        print "araiblock[0][0]:"
#        print araiblock[0][0]
#        print "araiblock[1] (first_I)"
#        print araiblock[1]
#        print "araiblock[2] (ptrm_check)"
#        print araiblock[2]
#        print "araiblock[3] (ptrm_tail)"
#        print araiblock[3]
#        print "araiblock[4] (zptrm_check)"
#        print araiblock[4]
#        print "araiblock[5] (GammaChecks) "
#        print araiblock[5]
#        print "field ", field
        return araiblock,field

#if True:
#    gui = Arai_GUI('new_magic_measurements.txt')
if False:
    gui = Arai_GUI()
    specimens = list(gui.Data.keys())
    print(specimens.sort())
    print("SPECIMENS")
    from . import spd
    print(specimens)
    things = []
    for n, s in enumerate(specimens):
        print("looping: ")
        print(s)
        print(gui.Data[s]['t_Arai'])
        tmin = gui.Data[s]['t_Arai'][0]
        tmax = gui.Data[s]['t_Arai'][-1]
        print("tmin is: %s" %(tmin))
        print("tmax is: %s" %(tmax))
        thing = spd.PintPars(gui.Data, s, tmin, tmax)
        things.append(thing)
    thing = things[0]
    thing1 = things[1]
    thing2 = things[2]
    thing3 = things[3]
    thing4 = things[4]
    thing5 = things[5]
    thing.calculate_all_statistics()
    thing1.calculate_all_statistics()
    thing2.calculate_all_statistics()
    thing3.calculate_all_statistics()
    thing4.calculate_all_statistics()
    thing5.calculate_all_statistics()





# not currently getting used in your process, but probs has useful code.  a lot of overlap with what's in spd.py
    def get_PI_parameters(self,s,tmin,tmax):
        print("calling get_PI_parameters() from thellier_gui_spd_lj.py")
        not_called = """
        print "self", self, str(self.Data)[:500] + "..."


        def calculate_ftest(s,sigma,nf):
            print "calling calculate_ftest() in get_PI_parameters()"
            chibar=(s[0][0]+s[1][1]+s[2][2])/3.
            t=numpy.array(linalg.eigvals(s))
            F=0.4*(t[0]**2+t[1]**2+t[2]**2 - 3*chibar**2)/(float(sigma)**2)

            return(F)

 
#        calcualte statisics 
 
        
        print "calculating statistics"
        pars=self.Data[s]['pars']
        datablock = self.Data[s]['datablock']
        pars=self.Data[s]['pars']
        print "new pars", pars
        # get MagIC mothod codes:

        #pars['magic_method_codes']="LP-PI-TRM" # thellier Method
        
        
        t_Arai=self.Data[s]['t_Arai']
        x_Arai=self.Data[s]['x_Arai']
        y_Arai=self.Data[s]['y_Arai']
        x_tail_check=self.Data[s]['x_tail_check']
        y_tail_check=self.Data[s]['y_tail_check']

        zijdblock=self.Data[s]['zijdblock']        
        z_temperatures=self.Data[s]['z_temp']
        print "got through a few stats"
        #print tmin,tmax,z_temperatures
        # check tmin
        if tmin not in t_Arai or tmin not in z_temperatures:
            print "t_Arai   ", t_Arai
            print "z_temperatures  ", z_temperatures
            print "tmin not in t_Arai or not in z_temperatures"
            return(pars)
        
        # check tmax
        if tmax not in t_Arai or tmin not in z_temperatures:
            print "returning pars because tmax not in t_Arai"
            return(pars)

        print "got past first 2 if statements"

        start=t_Arai.index(tmin)
        end=t_Arai.index(tmax)

        if end-start < float(self.accept_new_parameters['specimen_int_n'] -1):
          print "returning pars because??"
          return(pars)
                                                 
        #-------------------------------------------------
        # calualte PCA of the zerofield steps
        # MAD calculation following Kirschvink (1980)
        # DANG following Tauxe and Staudigel (2004)
        #-------------------------------------------------               
         
        pars["measurement_step_min"]=float(tmin)
        pars["measurement_step_max"]=float(tmax)
 
        zstart=z_temperatures.index(tmin)
        zend=z_temperatures.index(tmax)

        zdata_segment=self.Data[s]['zdata'][zstart:zend+1]

        print "elephant"
        #  PCA in 2 lines
        M = (zdata_segment-mean(zdata_segment.T,axis=1)).T # subtract the mean (along columns)
        [eigenvalues,eigenvectors] = linalg.eig(cov(M)) # attention:not always sorted

        # sort eigenvectors and eigenvalues
        eigenvalues=list(eigenvalues)
        tmp=[0,1,2]
        t1=max(eigenvalues);index_t1=eigenvalues.index(t1);tmp.remove(index_t1)
        t3=min(eigenvalues);index_t3=eigenvalues.index(t3);tmp.remove(index_t3)
        index_t2=tmp[0];t2=eigenvalues[index_t2]
        v1=real(numpy.array(eigenvectors[:,index_t1]))
        v2=real(numpy.array(eigenvectors[:,index_t2]))
        v3=real(numpy.array(eigenvectors[:,index_t3]))

        # chech if v1 is the "right" polarity
        cm=numpy.array(mean(zdata_segment.T,axis=1)) # center of mass
        v1_plus=v1*numpy.sqrt(sum(cm**2))
        v1_minus=v1*-1*numpy.sqrt(sum(cm**2))
        test_v=zdata_segment[0]-zdata_segment[-1]

        if numpy.sqrt(sum((v1_minus-test_v)**2)) < numpy.sqrt(sum((v1_plus-test_v)**2)):
         DIR_PCA=self.cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=self.cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=math.degrees(arctan(numpy.sqrt((t2+t3)/t1)))

        # DANG Tauxe and Staudigel 2004
        DANG=math.degrees( arccos( ( dot(cm, best_fit_vector) )/( numpy.sqrt(sum(cm**2)) * numpy.sqrt(sum(best_fit_vector**2)))))


        # best fit PCA direction
        pars["specimen_dec"] =  DIR_PCA[0]
        pars["specimen_inc"] =  DIR_PCA[1]
        pars["specimen_PCA_v1"] =best_fit_vector
        if t1 <0 or t1==0:
            t1=1e-10
        if t2 <0 or t2==0:
            t2=1e-10
        if t3 <0 or t3==0:
            t3=1e-10
            
        pars["specimen_PCA_sigma_max"] =  numpy.sqrt(t1)
        pars["specimen_PCA_sigma_int"] =  numpy.sqrt(t2)
        pars["specimen_PCA_sigma_min"] =  numpy.sqrt(t3)
            

        # MAD Kirschvink (1980)
        pars["specimen_int_mad"]=MAD
        pars["specimen_dang"]=DANG


        #-------------------------------------------------
        # calualte PCA of the pTRMs over the entire temperature range
        # and calculate the angular difference to the lab field
        # MAD calculation following Kirschvink (1980)
        #-------------------------------------------------
        
        PTRMS = self.Data[s]['PTRMS'][1:]
        CART_pTRMS_orig=numpy.array([self.dir2cart(row[1:4]) for row in PTRMS])
        #CART_pTRMS=[row/numpy.sqrt(sum((numpy.array(row)**2))) for row in CART_pTRMS_orig]
##        print "CART_pTRMS_orig",CART_pTRMS_orig
##        print "----"
        
        #  PCA in 2 lines
        M = (CART_pTRMS_orig-mean(CART_pTRMS_orig.T,axis=1)).T # subtract the mean (along columns)
        [eigenvalues,eigenvectors] = linalg.eig(cov(M)) # attention:not always sorted

        # sort eigenvectors and eigenvalues
        eigenvalues=list(eigenvalues)
        tmp=[0,1,2]
        t1=max(eigenvalues);index_t1=eigenvalues.index(t1);tmp.remove(index_t1)
        t3=min(eigenvalues);index_t3=eigenvalues.index(t3);tmp.remove(index_t3)
        index_t2=tmp[0];t2=eigenvalues[index_t2]
        v1=real(numpy.array(eigenvectors[:,index_t1]))
        v2=real(numpy.array(eigenvectors[:,index_t2]))
        v3=real(numpy.array(eigenvectors[:,index_t3]))

        # chech if v1 is the "right" polarity
        cm=numpy.array(mean(CART_pTRMS_orig.T,axis=1)) # center of mass
        v1_plus=v1*numpy.sqrt(sum(cm**2))
        v1_minus=v1*-1*numpy.sqrt(sum(cm**2))
        test_v=CART_pTRMS_orig[0]-CART_pTRMS_orig[-1]

        if numpy.sqrt(sum((v1_minus-test_v)**2)) > numpy.sqrt(sum((v1_plus-test_v)**2)):
         DIR_PCA=self.cart2dir(v1*-1)
         best_fit_vector=v1*-1
        else:
         DIR_PCA=self.cart2dir(v1)
         best_fit_vector=v1

        # MAD Kirschvink (1980)
        MAD=math.degrees(arctan(numpy.sqrt((t2+t3)/t1)))


        # best fit PCA direction
        pars["specimen_ptrms_dec"] =  DIR_PCA[0]
        pars["specimen_ptrms_inc"] =  DIR_PCA[1]
        pars["specimen_ptrms_mad"]=MAD
        B_lab_unit=self.dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
        pars["specimen_ptrms_angle"]=math.degrees(math.acos(dot(best_fit_vector,B_lab_unit)/(numpy.sqrt(sum(best_fit_vector**2)) * numpy.sqrt(sum(B_lab_unit**2)))))

##        print "specimen_ptrms_dec",pars["specimen_ptrms_dec"]
##        print "specimen_ptrms_inc",pars["specimen_ptrms_inc"]
##        print "B_lab_unit,v1",B_lab_unit,v1
##        print "specimen_ptrms_angle", pars["specimen_ptrms_angle"]

##        #-------------------------------------------------                     
##        # Calculate the new 'MAD box' parameter
##        # all datapoints should be inside teh M"AD box"
##        # defined by the threshold value of MAD
##        # For definitionsee Shaar and Tauxe (2012)
##        #-------------------------------------------------                     
##
##        pars["specimen_mad_scat"]="Pass"
##        self.accept_new_parameters['specimen_mad_scat']=True
##        if 'specimen_mad_scat' in self.accept_new_parameters.keys() and 'specimen_int_mad' in self.accept_new_parameters.keys() :
##            if self.accept_new_parameters['specimen_mad_scat']==True or self.accept_new_parameters['specimen_mad_scat'] in [1,"True","TRUE",'1']:
##
##                # center of mass 
##                CM_x=mean(zdata_segment[:,0])
##                CM_y=mean(zdata_segment[:,1])
##                CM_z=mean(zdata_segment[:,2])
##                CM=numpy.array([CM_x,CM_y,CM_z])
##
##                # threshold value for the distance of the point from a line:
##                # this is depends of MAD
##                # if MAD= tan-1 [ sigma_perpendicular / sigma_max ]
##                # then:
##                # sigma_perpendicular_threshold=tan(MAD_threshold)*sigma_max
##                sigma_perpendicular_threshold=abs(tan(radians(self.accept_new_parameters['specimen_int_mad'])) *  pars["specimen_PCA_sigma_max"] )
##                
##                # Line from
##                #print "++++++++++++++++++++++++++++++++++"
##                
##                for P in zdata_segment:
##                    # Find the line  P_CM that connect P to the center of mass
##                    #print "P",P
##                    #print "CM",CM
##                    P_CM=P-CM
##                    #print "P_CM",P_CM
##                    
##                    #  the dot product of vector P_CM with the unit direction vector of the best-fit liene. That's the projection of P_CM on the PCA line 
##                    best_fit_vector_unit=best_fit_vector/numpy.sqrt(sum(best_fit_vector**2))
##                    #print "best_fit_vector_unit",best_fit_vector_unit
##                    CM_P_projection_on_PCA_line=dot(best_fit_vector_unit,P_CM)
##                    #print "CM_P_projection_on_PCA_line",CM_P_projection_on_PCA_line
##
##                    # Pythagoras
##                    P_CM_length=numpy.sqrt(sum((P_CM)**2))
##                    Point_2_PCA_Distance=numpy.sqrt((P_CM_length**2-CM_P_projection_on_PCA_line**2))
##                    #print "Point_2_PCA_Distance",Point_2_PCA_Distance
##
##
##                    #print "sigma_perpendicular_threshold*2",sigma_perpendicular_threshold*2
##                    if Point_2_PCA_Distance > sigma_perpendicular_threshold*2:
##                        pars["specimen_mad_scat"]="Fail"
##                        index=999
##                        for i in range(len(self.Data[s]['zdata'])):
##                        
##                            if P[0] == self.Data[s]['zdata'][i][0] and P[1] == self.Data[s]['zdata'][i][1] and P[2] == self.Data[s]['zdata'][i][2]:
##                                index =i
##                                break
##                        #print "specimen  %s fail on mad_scat,%i"%(s,index)
##                        
##                    
##                    
##                    #CM_P_projection_on_PCA_line_length=numpy.sqrt(sum((CM_P_projection_on_PCA_line_length)**2))
        

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
        york_b=-1* numpy.sqrt( sum(y_err**2) / sum(x_err**2) )

        # york sigma
        york_sigma= numpy.sqrt ( (2 * sum(y_err**2) - 2*york_b*sum(x_err*y_err)) / ( (n-2) * sum(x_err**2) ) )

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

        f_vds=abs((y_prime[0]-y_prime[-1])/self.Data[s]['vds'])

        g_Coe= 1 - (sum((y_prime[:-1]-y_prime[1:])**2) / sum((y_prime[:-1]-y_prime[1:]))**2 )

        q_Coe=abs(york_b)*f_Coe*g_Coe/york_sigma


        count_IZ= self.Data[self.s]['steps_Arai'].count('IZ')
        count_ZI= self.Data[self.s]['steps_Arai'].count('ZI')
        if count_IZ >1 and count_ZI >1:
            pars['magic_method_codes']="LP-PI-BT-IZZI"
        elif count_IZ <1 and count_ZI >1:
            pars['magic_method_codes']="LP-PI-ZI"
        elif count_IZ >1 and count_ZI <1:
            pars['magic_method_codes']="LP-PI-IZ"            
        else:
            pars['magic_method_codes']=""
            
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
        pars['magic_method_codes']+=":IE-TT"
        if 'x_ptrm_check' in self.Data[self.s].keys():
            if len(self.Data[self.s]['x_ptrm_check'])>0:
                pars['magic_method_codes']+=":LP-PI-ALT-PTRM"
        if 'x_tail_check' in self.Data[self.s].keys():
            if len(self.Data[self.s]['x_tail_check'])>0:
                pars['magic_method_codes']+=":LP-PI-BT-MD"


        #-------------------------------------------------
        # pTRM checks:
        # DRAT ()
        # and
        # DRATS (Tauxe and Staudigel 2004)
        #-------------------------------------------------

        x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end,x_Arai_compare=[],[],[]
        x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
        x_ptrm_check_for_SCAT,y_ptrm_check_for_SCAT=[],[]

        stop_scat_collect=False
        for k in range(len(self.Data[s]['ptrm_checks_temperatures'])):
          if self.Data[s]['ptrm_checks_temperatures'][k]<pars["measurement_step_max"] and self.Data[s]['ptrm_checks_temperatures'][k] in t_Arai:
            x_ptrm_check_in_0_to_end.append(self.Data[s]['x_ptrm_check'][k])
            y_ptrm_check_in_0_to_end.append(self.Data[s]['y_ptrm_check'][k])
            x_Arai_index=t_Arai.index(self.Data[s]['ptrm_checks_temperatures'][k])
            x_Arai_compare.append(x_Arai[x_Arai_index])
            if self.Data[s]['ptrm_checks_temperatures'][k]>=pars["measurement_step_min"]:
                x_ptrm_check_in_start_to_end.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_in_start_to_end.append(self.Data[s]['y_ptrm_check'][k])
          if self.Data[s]['ptrm_checks_temperatures'][k] >= pars["measurement_step_min"] and self.Data[s]['ptrm_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                x_ptrm_check_for_SCAT.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_for_SCAT.append(self.Data[s]['y_ptrm_check'][k])
          # If triangle is within the interval but started after the upper temperature bound, then one pTRM check is included
          # For example: if T_max=480, the traingle in 450 fall far, and it started at 500, then it is included
          # the ateration occured between 450 and 500, we dont know when.
          if  stop_scat_collect==False and \
             self.Data[s]['ptrm_checks_temperatures'][k] < pars["measurement_step_max"] and self.Data[s]['ptrm_checks_starting_temperatures'][k] > pars["measurement_step_max"] :
                x_ptrm_check_for_SCAT.append(self.Data[s]['x_ptrm_check'][k])
                y_ptrm_check_for_SCAT.append(self.Data[s]['y_ptrm_check'][k])
                stop_scat_collect=True
              
              
        # scat uses a different definistion":
        # use only pTRM that STARTED before the last temperatire step.
        
        x_ptrm_check_in_0_to_end=numpy.array(x_ptrm_check_in_0_to_end)  
        y_ptrm_check_in_0_to_end=numpy.array(y_ptrm_check_in_0_to_end)
        x_Arai_compare=numpy.array(x_Arai_compare)
        x_ptrm_check_in_start_to_end=numpy.array(x_ptrm_check_in_start_to_end)
        y_ptrm_check_in_start_to_end=numpy.array(y_ptrm_check_in_start_to_end)
        x_ptrm_check_for_SCAT=numpy.array(x_ptrm_check_for_SCAT)
        y_ptrm_check_for_SCAT=numpy.array(y_ptrm_check_for_SCAT)
                               
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
        x_tail_check_for_SCAT,y_tail_check_for_SCAT=[],[]

        for k in range(len(self.Data[s]['tail_check_temperatures'])):
          if self.Data[s]['tail_check_temperatures'][k] in t_Arai:
              if self.Data[s]['tail_check_temperatures'][k]<=pars["measurement_step_max"] and self.Data[s]['tail_check_temperatures'][k] >=pars["measurement_step_min"]:
                   x_tail_check_start_to_end.append(self.Data[s]['x_tail_check'][k]) 
                   y_tail_check_start_to_end.append(self.Data[s]['y_tail_check'][k]) 
          if self.Data[s]['tail_check_temperatures'][k] >= pars["measurement_step_min"] and self.Data[s]['tail_checks_starting_temperatures'][k] <= pars["measurement_step_max"] :
                x_tail_check_for_SCAT.append(self.Data[s]['x_tail_check'][k])
                y_tail_check_for_SCAT.append(self.Data[s]['y_tail_check'][k])

                
        x_tail_check_start_to_end=numpy.array(x_tail_check_start_to_end)
        y_tail_check_start_to_end=numpy.array(y_tail_check_start_to_end)
        x_tail_check_for_SCAT=numpy.array(x_tail_check_for_SCAT)
        y_tail_check_for_SCAT=numpy.array(y_tail_check_for_SCAT)

        #-------------------------------------------------                     
        # Tail check : TO DO !
        pars['specimen_md']=-1  
        #-------------------------------------------------                     

        #-------------------------------------------------                     
        # Calculate the new 'beta box' parameter
        # all datapoints, pTRM checks, and tail-checks, should be inside a "beta box"
        # For definition of "beta box" see Shaar and Tauxe (2012)
        #-------------------------------------------------                     

        if self.accept_new_parameters['specimen_scat']==True or self.accept_new_parameters['specimen_scat'] in [1,"True","TRUE",'1']:
        
            pars["fail_arai_beta_box_scatter"]=False
            pars["fail_ptrm_beta_box_scatter"]=False
            pars["fail_tail_beta_box_scatter"]=False
            
            # best fit line 
            b=pars['specimen_b']
            cm_x=mean(numpy.array(x_Arai_segment))
            cm_y=mean(numpy.array(y_Arai_segment))
            a=cm_y-b*cm_x

            # lines with slope = slope +/- 2*(specimen_b_beta)

            if 'specimen_b_beta' not in self.accept_new_parameters.keys():
             print ("-E- ERROR: specimen_beta not in pmag_criteria file, cannot calculate 'beta box' scatter\n") 

            b_beta_threshold=self.accept_new_parameters['specimen_b_beta']

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

            pars['specimen_scat_bounding_line_high']=[intercept2,slop2]
            pars['specimen_scat_bounding_line_low']=[intercept1,slop1]
            
            # check if the Arai data points are in the 'box'

            x_Arai_segment=numpy.array(x_Arai_segment)
            y_Arai_segment=numpy.array(y_Arai_segment)

            # the two bounding lines
            ymin=intercept1+x_Arai_segment*slop1
            ymax=intercept2+x_Arai_segment*slop2

            # arrays of "True" or "False"
            check_1=y_Arai_segment>ymax
            check_2=y_Arai_segment<ymin

            # check if at least one "True" 
            if (sum(check_1)+sum(check_2))>0:
             pars["fail_arai_beta_box_scatter"]=True
             #print "check, fail beta box"


            # check if the pTRM checks data points are in the 'box'

            # using x_ptrm_check_in_segment (defined above)
            # using y_ptrm_check_in_segment (defined above)


            if len(x_ptrm_check_for_SCAT) > 0:

              # the two bounding lines
              ymin=intercept1+x_ptrm_check_for_SCAT*slop1
              ymax=intercept2+x_ptrm_check_for_SCAT*slop2

              # arrays of "True" or "False"
              check_1=y_ptrm_check_for_SCAT>ymax
              check_2=y_ptrm_check_for_SCAT<ymin


              # check if at least one "True" 
              if (sum(check_1)+sum(check_2))>0:
                pars["fail_ptrm_beta_box_scatter"]=True
                #print "check, fail fail_ptrm_beta_box_scatter"
                
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
                pars["fail_tail_beta_box_scatter"]=True
                #print "check, fail fail_ptrm_beta_box_scatter"

            if pars["fail_tail_beta_box_scatter"] or pars["fail_ptrm_beta_box_scatter"] or pars["fail_arai_beta_box_scatter"]:
                  pars["specimen_scat"]="Fail"
            else:
                  pars["specimen_scat"]="Pass"
        else:
            pars["specimen_scat"]="N/A"
        #-------------------------------------------------  
        # Calculate the new FRAC parameter (Shaar and Tauxe, 2012).
        # also check that the 'gap' between consecutive measurements is less than 0.5(VDS)
        #
        #-------------------------------------------------  

        vector_diffs=self.Data[s]['vector_diffs']
        vector_diffs_segment=vector_diffs[zstart:zend]
        FRAC=sum(vector_diffs_segment)/self.Data[s]['vds']
        max_FRAC_gap=max(vector_diffs_segment/sum(vector_diffs_segment))

        pars['specimen_frac']=FRAC
        pars['specimen_gmax']=max_FRAC_gap

        #-------------------------------------------------  
        # Check if specimen pass Acceptance criteria
        #-------------------------------------------------  

        pars['specimen_fail_criteria']=[]
        for key in self.high_threshold_velue_list:
            if key in ['specimen_gmax','specimen_b_beta']:
                value=round(pars[key],2)
            elif key in ['specimen_dang','specimen_int_mad']:
                value=round(pars[key],1)
            else:
                value=pars[key]
                
            if value>float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        for key in self.low_threshold_velue_list:
            if key in ['specimen_f','specimen_fvds','specimen_frac','specimen_g','specimen_q']:
                value=round(pars[key],2)
            else: 
                value=pars[key]
            if value < float(self.accept_new_parameters[key]):
                pars['specimen_fail_criteria'].append(key)
        if 'specimen_scat' in pars.keys():
            if pars["specimen_scat"]=="Fail":
                pars['specimen_fail_criteria'].append('specimen_scat')
        if 'specimen_mad_scat' in pars.keys():
            if pars["specimen_mad_scat"]=="Fail":
                pars['specimen_fail_criteria'].append('specimen_mad_scat')

    
        #-------------------------------------------------                     
        # Calculate the direction of pTMRMS
        #-------------------------------------------------                     


        #-------------------------------------------------            
        # Calculate anistropy correction factor
        #-------------------------------------------------            

        if "AniSpec" in self.Data[s].keys():
           pars["AC_WARNING"]=""
           # if both aarm and atrm tensor axist, try first the aarm. if it fails use the atrm.
           if 'AARM' in self.Data[s]["AniSpec"].keys() and 'ATRM' in self.Data[s]["AniSpec"].keys():
               TYPES=['AARM','ATRM']
           else:
               TYPES=self.Data[s]["AniSpec"].keys()
           for TYPE in TYPES:
               red_flag=False
               S_matrix=numpy.zeros((3,3),'f')
               S_matrix[0,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s1']
               S_matrix[1,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s2']
               S_matrix[2,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s3']
               S_matrix[0,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
               S_matrix[1,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s4']
               S_matrix[1,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
               S_matrix[2,1]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s5']
               S_matrix[0,2]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']
               S_matrix[2,0]=self.Data[s]['AniSpec'][TYPE]['anisotropy_s6']

               #self.Data[s]['AniSpec']['anisotropy_type']=self.Data[s]['AniSpec']['anisotropy_type']
               self.Data[s]['AniSpec'][TYPE]['anisotropy_n']=int(float(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))

               this_specimen_f_type=self.Data[s]['AniSpec'][TYPE]['anisotropy_type']+"_"+"%i"%(int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n']))
               
               Ftest_crit={} 
               Ftest_crit['ATRM_6']=  3.1059
               Ftest_crit['AARM_6']=  3.1059
               Ftest_crit['AARM_9']= 2.6848
               Ftest_crit['AARM_15']= 2.4558

               # threshold value for Ftest:
               
               if 'AniSpec' in self.Data[s].keys() and TYPE in self.Data[s]['AniSpec'].keys()\
                  and 'anisotropy_sigma' in  self.Data[s]['AniSpec'][TYPE].keys() \
                  and self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']!="":
                  # Calculate Ftest. If Ftest exceeds threshold value: set anistropy tensor to identity matrix
                   sigma=float(self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma'])             
                   nf = 3*int(self.Data[s]['AniSpec'][TYPE]['anisotropy_n'])-6
                   F=calculate_ftest(S_matrix,sigma,nf)
                   #print s,"F",F
                   self.Data[s]['AniSpec'][TYPE]['ftest']=F
                   #print "s,sigma,nf,F,Ftest_crit[this_specimen_f_type]"
                   #print s,sigma,nf,F,Ftest_crit[this_specimen_f_type]
                   if self.accept_new_parameters['check_aniso_ftest']:
                       Ftest_threshold=Ftest_crit[this_specimen_f_type]
                       if self.Data[s]['AniSpec'][TYPE]['ftest'] < Ftest_crit[this_specimen_f_type]:
                           S_matrix=identity(3,'f')
                           pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails F-test; "%(TYPE)
                           red_flag=True
                           
               else:
                   self.Data[s]['AniSpec'][TYPE]['anisotropy_sigma']=""
                   self.Data[s]['AniSpec'][TYPE]['ftest']=1e10
     
                
               if 'anisotropy_alt' in self.Data[s]['AniSpec'][TYPE].keys() and self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']!="":
                   if float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']) > float(self.accept_new_parameters['anisotropy_alt']):
                       S_matrix=identity(3,'f')
                       pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails alteration check: %.1f%% > %.1f%%; "%(TYPE,float(self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']),float(self.accept_new_parameters['anisotropy_alt']))
                       red_flag=True
               else:
                   self.Data[s]['AniSpec'][TYPE]['anisotropy_alt']=""

                   
               # if AARM passes, use the AARM.    
               if TYPE=='AARM' and red_flag==False:
                   break
               else:
                   pass
           TRM_anc_unit=numpy.array(pars['specimen_PCA_v1'])/numpy.sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
           B_lab_unit=self.dir2cart([ self.Data[s]['Thellier_dc_field_phi'], self.Data[s]['Thellier_dc_field_theta'],1])
           #B_lab_unit=numpy.array([0,0,-1])
           Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
           pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor
           pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])
           
           pars["AC_anisotropy_type"]=self.Data[s]['AniSpec'][TYPE]["anisotropy_type"]
           pars["specimen_int_uT"]=float(pars["AC_specimen_int"])*1e6
           if TYPE=='AARM':
               if ":LP-AN-ARM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-AN-ARM:AE-H:DA-AC-AARM"
                  pars['specimen_correction']='c'
                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor
           if TYPE=='ATRM':
               if ":LP-AN-TRM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-AN-TRM:AE-H:DA-AC-ATRM"
                  pars['specimen_correction']='c' 
                  pars['specimen_int_corr_anisotropy']=Anisotropy_correction_factor

 
        else:
           pars["Anisotropy_correction_factor"]=1.0
           pars["specimen_int_uT"]=float(pars["specimen_int"])*1e6
           pars["AC_WARNING"]="No anistropy correction"
           pars['specimen_correction']='u' 

        pars["specimen_int_corr_anisotropy"]=pars["Anisotropy_correction_factor"]   
        #-------------------------------------------------                    
        # NLT and anisotropy correction together in one equation
        # See Shaar et al (2010), Equation (3)
        #-------------------------------------------------

        if 'NLT_parameters' in self.Data[s].keys():

           alpha=self.Data[s]['NLT_parameters']['tanh_parameters'][0][0]
           beta=self.Data[s]['NLT_parameters']['tanh_parameters'][0][1]
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
               if ":LP-TRM" not in pars['magic_method_codes']:
                  pars['magic_method_codes']+=":LP-TRM:DA-NL"
               pars['specimen_correction']='c' 

           else:
               print ("-W- WARNING: problematic NLT mesurements for specimens %s. Cant do NLT calculation. check data\n"%s)
               pars["NLT_specimen_correction_factor"]=-1
        else:
           pars["NLT_specimen_correction_factor"]=-1

        #-------------------------------------------------                    
        # Calculate the final result with cooling rate correction
        #-------------------------------------------------

        pars["specimen_int_corr_cooling_rate"]=-999
        if 'cooling_rate_data' in self.Data[s].keys():
            if 'CR_correction_factor' in self.Data[s]['cooling_rate_data'].keys():
                if self.Data[s]['cooling_rate_data']['CR_correction_factor'] != -1 and self.Data[s]['cooling_rate_data']['CR_correction_factor'] !=-999:
                    pars["specimen_int_corr_cooling_rate"]=self.Data[s]['cooling_rate_data']['CR_correction_factor']
                    pars['specimen_correction']='c'
                    pars["specimen_int_uT"]=pars["specimen_int_uT"]*pars["specimen_int_corr_cooling_rate"]
                    if ":DA-CR" not in pars['magic_method_codes']:
                      pars['magic_method_codes']+=":DA-CR"
                    if 'CR_correction_factor_flag' in self.Data[s]['cooling_rate_data'].keys() \
                       and self.Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
                        pars["CR_WARNING"]="inferred cooling rate correction"
                    
                
        else:
            pars["CR_WARNING"]="no cooling rate correction"
            
##            sample=self.Data_hierarchy['specimens'][self.s]
##            if sample in Data_info["er_samples"]:
##                if 'sample_type' in Data_info["er_samples"][sample].keys():
##                    if Data_info["er_samples"][sample]['sample_type'] in ["Baked Clay","Baked Mud",

        print "pars before importing spd:  ", pars
        import spd
        print "imported spd"
        specimen = self.s
        pint_pars = spd.PintPars(self.Data,specimen,tmin,tmax)
        print "about to 'calculate all statistics'"
        print "pint_pars.calculate_all_statistics()"
        pint_pars.calculate_all_statistics()
        print "giraffes are awesome"
#        return(pars) original
        return pint_pars
"""    
