#!/usr/bin/env python

#---------------------------------------------------------------------------
# Author: Ron Shaar
# Revision notes
#
# Rev 1.0 Initial revision August 2012 
#---------------------------------------------------------------------------

import pylab,scipy,os,pmag,math,time
from pylab import *
#from numpy import matrix,cov,double,cumsum,dot,linalg,array,rank
from scipy import optimize
from scipy.optimize import curve_fit
#from operator import itemgetter
import random 
rcParams.update({"svg.embed_char_paths":False})

#import gc
#gc.disable()





def main():
    """

    GENERAL
    ******

    The thellier_auto_interpreter.py program does the following:
    1) Finds all the 'acceptable interpretation' in all specimes (interpretationa that pass the selecting criteria)
    2) Calculates the optimal sample's 'best mean'
     (a 'best mean' is the 'acceptable' interpretation that has a minimum standard deviation).


    INPUTS:
    ******
    
    REQUIRED:
    1) One or more MagIC working directories (MagIC_DIRs):
    Each MagIC directory MUST include magic_measurements.txt. An optional file is rmag_anistropy.txt for anisotropy corrections.
    
    2) Selecting criteria file (pmag_criteria.txt)
    A MagIC format file with the threshold values of the selecting criteria


    OUTPUTS:
    *******
    1) Thellier_auto_interpretation.log:
       The format of the log file is:
        -I- <message>
        -W- WARNING:  <a warning message>
        -E- ERROR: <an error message>

    2) Thellier_auto_interpretation.samples.txt:
        A summary file of the 'best samples means'
        format: <sample> <number of acceptable specimens> <mean: in microT> <sigma: standard deviation of the mean> <sigma/mean> <warning>
        Notice important warnings:
             - specimens with no anistropy correction
             - outlier specimen

    3) Thellier_auto_interpretation.specimens_bounds.txt:
        A summary file of all the 'acceptable' interpretation of all the specimens.
        Format:
        <sample> <specimen> <Anisotropy correction factor> <Anisotropy correction type> <B_lab> <minimum acceptable paleointenisty>  <maximum acceptable paleointenisty>
 <warning>
        
    4) Thellier_auto_interpretation.all.txt:
        A list of all the 'acceptable' interpretation of all the specimens that passed, and the corresponding paleointensity statistics

    5) Thellier_auto_interpretation.specimens.txt:
        A  file that includes all the 'acceptable interpretations' of the specimens that were used in calculating the 'sample best means'
        and the values of the palaeointensity statistics.
        format: <sample> <specimen> <Blab> <Banc> <ATRM_correction_factor> <NLT_correction_factor> ... paleointensity statistics
    
    6) Thellier_auto_interpretation.redo:
        a redo format file with all the interpretation that can be used later by MaGIC.py
 
    
    
    PROCEDURE:
    **********

    1) Read measurement files
        1.1) Read magic_measurement.txt
        1.2) Caluclate non-linear TRM correction using Shaar et al. (2010) procedure.
        1.3) Read anistropy tensor from rmag_anisotropy.txt (The program DOES NOT calualte the tensors!)
        1.4) Read the selection criteria threshold values (format of pmag_criteria.txt)

    2) 2.1) For each specimen:
             all the 'acceptable interpretation' are calculated.
             An 'acceptable' interpretation is a set of temperature bound that passes the selecting criteria for specimen
             Usually, there are more than one 'acceptable' interpretation.

       2.2) For each sample:
             Find the 'best sample mean' by selecting from all the 'acceptable interpretations' of the specimens
             the set of interpretations that yields a minimum standard deviation of the sample mean.
             
    3) Notice that the program does not screen out 'best samples means' using the criteria for samples, only give the 'best means'


    OPTIONS:
    ********

    -h : Prin this help message.

    -WD: (Optional)
                      A list of pathes do all the MagIC working directiories
                      The default is the current working directory
                      example:
                      -WD ~/Documents/Cyprus,./my_files/Timna
                      
                      
    -criteria_file <pmag_criteria.txt format file>
                      a pmag_criteria.txt format file with paleointensity statistics and threshold values

    -exclude (optional)
                      list of specimens that user want to rejected from the calculation.
                      The first column is the specimen name.
                      It second column is comments (recommended to add comments explaining the reasons for rejecting this specimenOUTPUTS:

    -forced_interpretation <FILE>
                      a list of interpretation (Tmin,Tmax) for specimens that the used wish to "force"
                      If a specimen is in this file, then the only 'acceptable interpretation' that the program uses
                      for fidning the 'best sample mean' is the temperature bounds given in this file.
                      Format (tab delinited text):
                      specime_name Tmin Tmax
                          (Tmin and Tmax are in Celcius. room temperature NRM is 0)

    -sample_mean_type (Optional) <comma delimited list>
                      how to generate the sample interpretation and sample coundary of confidence
                      STDEV-OPT: select the interpretation that yield the minimum standard deviation
                      BS: simple botstrap: Each specimen contain several 'acceptable' grade A interpretation (discrete)
                           the bootstrap procedure randomally pick on of these interpretation.

                      BS-PAR: Parametric bootstrap. Each specimen contains a minimum and maximum grade A interpretation.
                              the bootstrap procedure assumes for each specimen uniform distribution between minimum and maximum.

                      example:  -sample_mean_type STDEV-OPT,BS,BS-PAR
         
                      default is all options.
                      

    IMPORTANT NOTES for user:
    **********************
    
    - User need to review each of WARNING and ERRORS in:
            Thellier_auto_interpretation.log
            Thellier_auto_interpretation.specimens_bounds.txt
            Thellier_auto_interpretation.samples.txt

    list of ERROR masseges:
    **************
    To be completed
    
    list of WARNING masseges:
    **************
    To be completed

    List of parameters in criteria_file:
    **************

    specimen_n [3]                  minimum number of datapoints included in best fit line caluclation of the Arai plot.
    specimen_int_ptrm_n' [2]        minimum number of pTRM checks (start counting from NRM, end counting on high temperature step)
    specimen_f' [0.]                Fraction parameter (Coe 1978)
    specimen_fvds [0.]              Fvds parameter (Tuaxe and Staudigel, 2004)
    specimen_frac [0.8]             FRAC parameter (Shaar and Tauxe 2012)
    specimen_gap_max [0.6]     specimen_gap_max (Shaar and Tauxe 2012)
    specimen_b_beta [0.1]           beta parameter (Coe, 1978)
    specimen_dang [100000]          DANG (Tauxe and Staudigel, 2004)
    specimen_drats [100000]         DRATS (Tauxe and Staudigel, 2004)
    specimen_int_mad [5]            Maximum Angle of Deviation  (MAD, Kirschvink, 1980) of the NRM data points
    specimen_md [100000]            MD tail check

    sample_int_n' [3]               minimum number of specimens for sample mean calculation
    sample_int_sigma [6]            minimum standrad deviation of sample mean in Tesla
    sample_int_sigma_perc [10]      minimum 100*(sigma/sample mean) units of percentage
    sample_int_n_outlier_check [6]  minimum number of specimens for which outlier specimen can be rejected.
                                    An outlier is one specimen (and only one specimen) that whatever interpretation is done on the other specimens
                                    it always fall 2*sigma far from the sample's mean. 

 
    """


#-------------------------------------------------------
# definition
#-------------------------------------------------------


    def dir2cart(d):
       # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
        ints=ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
        d=array(d)
        rad=pi/180.
        if len(d.shape)>1: # array of vectors
            decs,incs=d[:,0]*rad,d[:,1]*rad
            if d.shape[1]==3: ints=d[:,2] # take the given lengths
        else: # single vector
            decs,incs=array(d[0])*rad,array(d[1])*rad
            if len(d)==3: 
                ints=array(d[2])
            else:
                ints=array([1.])
        cart= array([ints*cos(decs)*cos(incs),ints*sin(decs)*cos(incs),ints*sin(incs)]).transpose()
        return cart

    def cart2dir(cart): # OLD ONE
        """
        converts a direction to cartesian coordinates
        """
        Dir=[] # establish a list to put directions in
        rad=pi/180. # constant to convert degrees to radians
        R=sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
        if R==0:
           #print 'trouble in cart2dir'
           #print cart
           return [0.0,0.0,0.0]
        D=arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
        if D<0:D=D+360. # put declination between 0 and 360.
        if D>360.:D=D-360.
        Dir.append(D)  # append declination to Dir list
        I=arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
        Dir.append(I) # append inclination to Dir list
        Dir.append(R) # append vector length to Dir list
        return Dir # return the directions list

    def find_close_value( LIST, value):
        diff=inf
        for a in LIST:
            if abs(value-a)<diff:
                diff=abs(value-a)
                result=a
        return(result)

    def find_sample_min_std (Intensities):
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

      # Find the minimum and maximum acceptable sample mean.

      # make a new dictionary named "tmp_Intensities" with all grade A interpretation sorted. 
      tmp_Intensities={}
      Acceptable_sample_min,Acceptable_sample_max="",""
      for this_specimen in Intensities.keys():
        B_list=[B  for B in Intensities[this_specimen]]
        if len(B_list)>0:
            B_list.sort()
            tmp_Intensities[this_specimen]=B_list

      # find the minmum acceptable values
      while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
          B_tmp=[]
          B_tmp_min=1e10
          for specimen in tmp_Intensities.keys():
              B_tmp.append(min(tmp_Intensities[specimen]))
              if min(tmp_Intensities[specimen])<B_tmp_min:
                  specimen_to_remove=specimen
                  B_tmp_min=min(tmp_Intensities[specimen])
          if std(B_tmp)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
              Acceptable_sample_min=mean(B_tmp)
              #print "min value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))
              break
          else:
              tmp_Intensities[specimen_to_remove].remove(B_tmp_min)
              if len(tmp_Intensities[specimen_to_remove])==0:
                  break
                  
      #print "Intensities",Intensities        
      #print "Ron Check mi min sample"
      #print "min:",tmp_Intensities,B_tmp,Acceptable_sample_min
      #print "----"
      #print Intensities
      #print tmp_Intensities
      #print Acceptable_sample_min,Acceptable_sample_max

      # find the maximum acceptable values
      #--------------------
      tmp_Intensities={}
      for this_specimen in Intensities.keys():
        B_list=[B  for B in Intensities[this_specimen]]
        if len(B_list)>0:
            B_list.sort()
            tmp_Intensities[this_specimen]=B_list

      while len(tmp_Intensities.keys())>=float(acceptance_criteria["sample_int_n"]):
          B_tmp=[]
          B_tmp_max=0
          for specimen in tmp_Intensities.keys():
              B_tmp.append(max(tmp_Intensities[specimen]))
              if max(tmp_Intensities[specimen])>B_tmp_max:
                  specimen_to_remove=specimen
                  B_tmp_max=max(tmp_Intensities[specimen])
          if std(B_tmp)<=acceptance_criteria["sample_int_sigma_uT"] or 100*(std(B_tmp)/mean(B_tmp))<=acceptance_criteria["sample_int_sigma_perc"]:
              Acceptable_sample_max=mean(B_tmp)
              #print "max value,std,",mean(B_tmp),std(B_tmp),100*(std(B_tmp)/mean(B_tmp))

              break
          else:
              tmp_Intensities[specimen_to_remove].remove(B_tmp_max)
              if len(tmp_Intensities[specimen_to_remove])<1:
                  break
      #print "Ron Check mi max sample"
      #print "max:",tmp_Intensities,B_tmp,Acceptable_sample_max
      #print "======"

      if Acceptable_sample_min=="" or Acceptable_sample_max=="":
          print "-W- Cant calculate acceptable sample bounds, maybe it is because sample fail sample_int_sigma_uT or sample_int_sigma_perc?"
          #print Intensities
          #print tmp_Intensities
          #print Acceptable_sample_min,Acceptable_sample_max
          return(0.,0.)
      return(Acceptable_sample_min,Acceptable_sample_max)     
                  

        

    # help fuction for tanh best fit
    def tan_h(x, a, b):
        return a*tanh(b*x)

    # Copied from pmag.py
    def doaniscorr(PmagSpecRec,AniSpec):
        """
        takes the 6 element 's' vector and the Dec,Inc, Int 'Dir' data,
        performs simple anisotropy correction. returns corrected Dec, Inc, Int
        """
        AniSpecRec={}
        for key in PmagSpecRec.keys():
            AniSpecRec[key]=PmagSpecRec[key]
        s=zeros((6),'f')
        Dir=zeros((3),'f')
        s[0]=float(AniSpec["anisotropy_s1"])
        s[1]=float(AniSpec["anisotropy_s2"])
        s[2]=float(AniSpec["anisotropy_s3"])
        s[3]=float(AniSpec["anisotropy_s4"])
        s[4]=float(AniSpec["anisotropy_s5"])
        s[5]=float(AniSpec["anisotropy_s6"])
        Dir[0]=float(PmagSpecRec["specimen_dec"])
        Dir[1]=float(PmagSpecRec["specimen_inc"])
        Dir[2]=float(PmagSpecRec["specimen_int"])
        chi=array([[s[0],s[3],s[5]],[s[3],s[1],s[4]],[s[5],s[4],s[2]]])
        chi_inv=linalg.inv(chi)
        trace=chi_inv[0][0]+chi_inv[1][1]+chi_inv[2][2]
        chi_inv=3.*chi_inv/trace
        X=dir2cart(Dir)
        M=array(X)
        H=dot(M,chi_inv)
        cDir= cart2dir(H)
        Hunit=[H[0]/cDir[2],H[1]/cDir[2],H[2]/cDir[2]] # unit vector parallel to Banc
        Zunit=[0,0,-1.] # unit vector parallel to lab field
        Hpar=dot(chi,Hunit) # unit vector applied along ancient field
        Zpar=dot(chi,Zunit) # unit vector applied along lab field
        HparInt=cart2dir(Hpar)[2] # intensity of resultant vector from ancient field
        ZparInt=cart2dir(Zpar)[2] # intensity of resultant vector from lab field
        newint=Dir[2]*ZparInt/HparInt
        if cDir[0]-Dir[0]>90:
            cDir[1]=-cDir[1]
            cDir[0]=(cDir[0]-180.)%360.
        AniSpecRec["specimen_dec"]='%7.1f'%(cDir[0])
        AniSpecRec["specimen_inc"]='%7.1f'%(cDir[1])
        AniSpecRec["specimen_int"]='%9.4e'%(newint)
        AniSpecRec["specimen_correction"]='c'
        if 'magic_method_codes' in AniSpecRec.keys():
            methcodes=AniSpecRec["magic_method_codes"]
        else:
            methcodes=""
        if methcodes=="": methcodes="DA-AC-"+AniSpec['anisotropy_type']
        if methcodes!="": methcodes=methcodes+":DA-AC-"+AniSpec['anisotropy_type']
        AniSpecRec["magic_method_codes"]=methcodes
        return AniSpecRec


    # Copied from pmag.py
    def sortarai(datablock,s,Zdiff):
        """
         sorts data block in to first_Z, first_I, etc.
        """
        first_Z,first_I,zptrm_check,ptrm_check,ptrm_tail=[],[],[],[],[]
        field,phi,theta="","",""
        starthere=0
        Treat_I,Treat_Z,Treat_PZ,Treat_PI,Treat_M=[],[],[],[],[]
        ISteps,ZSteps,PISteps,PZSteps,MSteps=[],[],[],[],[]
        GammaChecks=[] # comparison of pTRM direction acquired and lab field
        Mkeys=['measurement_magn_moment','measurement_magn_volume','measurement_magn_mass','measurement_magnitude']
        rec=datablock[0]
        for key in Mkeys:
            if key in rec.keys() and rec[key]!="":
                momkey=key
                break
    # first find all the steps
        for k in range(len(datablock)):
            rec=datablock[k]
            temp=float(rec["treatment_temp"])
            methcodes=[]
            tmp=rec["magic_method_codes"].split(":")
            for meth in tmp:
                methcodes.append(meth.strip())
            if 'LT-T-I' in methcodes and 'LP-TRM' not in methcodes and 'LP-PI-TRM' in methcodes:
                Treat_I.append(temp)
                ISteps.append(k)
                if field=="":field=float(rec["treatment_dc_field"])
                if phi=="":
                    phi=float(rec['treatment_dc_field_phi'])
                    theta=float(rec['treatment_dc_field_theta'])
    # stick  first zero field stuff into first_Z 
            if 'LT-NO' in methcodes:
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-T-Z' in methcodes: 
                Treat_Z.append(temp)
                ZSteps.append(k)
            if 'LT-PTRM-Z' in methcodes:
                Treat_PZ.append(temp)
                PZSteps.append(k)
            if 'LT-PTRM-I' in methcodes:
                Treat_PI.append(temp)
                PISteps.append(k)
            if 'LT-PTRM-MD' in methcodes:
                Treat_M.append(temp)
                MSteps.append(k)
            if 'LT-NO' in methcodes:
                dec=float(rec["measurement_dec"])
                inc=float(rec["measurement_inc"])
                str=float(rec[momkey])
                first_I.append([273,0.,0.,0.,1])
                first_Z.append([273,dec,inc,str,1])  # NRM step
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
                if "LP-PI-TRM-IZ" in methcodes: 
                    ZI=0    
                else:   
                    ZI=1    
                dec=float(zrec["measurement_dec"])
                inc=float(zrec["measurement_inc"])
                str=float(zrec[momkey])
                first_Z.append([temp,dec,inc,str,ZI])
        # sort out first_I records 
                idec=float(irec["measurement_dec"])
                iinc=float(irec["measurement_inc"])
                istr=float(irec[momkey])
                X=dir2cart([idec,iinc,istr])
                BL=dir2cart([dec,inc,str])
                I=[]
                for c in range(3): I.append((X[c]-BL[c]))
                if I[2]!=0:
                    iDir=cart2dir(I)
                    if Zdiff==0:
                        first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                    else:
                        first_I.append([temp,0.,0.,I[2],ZI])
                    gamma=angle([iDir[0],iDir[1]],[phi,theta])
                else:
                    first_I.append([temp,0.,0.,0.,ZI])
                    gamma=0.0
    # put in Gamma check (infield trm versus lab field)
                if 180.-gamma<gamma:  gamma=180.-gamma
                GammaChecks.append([temp-273.,gamma])
        for temp in Treat_PI: # look through infield steps and find matching Z step
            step=PISteps[Treat_PI.index(temp)]
            rec=datablock[step]
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            brec=datablock[step-1] # take last record as baseline to subtract
            pdec=float(brec["measurement_dec"])
            pinc=float(brec["measurement_inc"])
            pint=float(brec[momkey])
            X=dir2cart([dec,inc,str])
            prevX=dir2cart([pdec,pinc,pint])
            I=[]
            for c in range(3): I.append(X[c]-prevX[c])
            dir1=cart2dir(I)
            if Zdiff==0:
                ptrm_check.append([temp,dir1[0],dir1[1],dir1[2]])
            else:
                ptrm_check.append([temp,0.,0.,I[2]])
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
            X=dir2cart([dec,inc,str])
            prevX=dir2cart([pdec,pinc,pint])
            I=[]
            for c in range(3): I.append(X[c]-prevX[c])
            dir2=cart2dir(I)
            zptrm_check.append([temp,dir2[0],dir2[1],dir2[2]])
        ## get pTRM tail checks together -
        for temp in Treat_M:
            step=MSteps[Treat_M.index(temp)] # tail check step - just do a difference in magnitude!
            rec=datablock[step]
    #        dec=float(rec["measurement_dec"])
    #        inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            if temp in Treat_Z:
                step=ZSteps[Treat_Z.index(temp)]
                brec=datablock[step]
    #        pdec=float(brec["measurement_dec"])
    #        pinc=float(brec["measurement_inc"])
                pint=float(brec[momkey])
    #        X=dir2cart([dec,inc,str])
    #        prevX=dir2cart([pdec,pinc,pint])
    #        I=[]
    #        for c in range(3):I.append(X[c]-prevX[c])
    #        d=cart2dir(I)
    #        ptrm_tail.append([temp,d[0],d[1],d[2]])
                ptrm_tail.append([temp,0,0,str-pint])  # difference - if negative, negative tail!
            else:
                print "-W- EARNING: specimen %s has a tail check with no first zero field step - check input file! for step %.0f"%(s,temp-273.)
    #
    # final check
    #
        if len(first_Z)!=len(first_I):
                   print len(first_Z),len(first_I)
                   print " -W- Something wrong with specimen %s. Better fix it or delete it "
                   #raw_input(" press return to acknowledge message")
        araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks)
        return araiblock,field

                    
#=============================================================
#  Main
#=============================================================

    start_time = time.time()
    
    #------------------------------
    # user definition
    #------------------------------
    

    if '-h' in sys.argv: # check if help is needed
        print main.__doc__
        sys.exit() # graceful quit


    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        dir_pathes=sys.argv[ind+1].split(',')
    else:
        dir_pathes=["./"]
    WD=dir_pathes[0]
        
        
    if '-exclude' in sys.argv:    
            ind=sys.argv.index("-exclude")
            exclude_specimens_file=sys.argv[ind+1]


    if '-criteria_file' in sys.argv:
        ind=sys.argv.index("-criteria_file")
        criteria_file=sys.argv[ind+1]
    else:
        print "-W- WARNING: Missing criteria file"


    if "-forced_interpretation" in sys.argv:
            ind=sys.argv.index("-forced_interpretation")
            forced_interpretation_file=sys.argv[ind+1]

    #DO_SAMPLE_BEST_MEAN,DO_SAMPLE_BOOTSTRP_MEAN,DO_SAMPLE_PARA_BOOTSTRP_MEAN=True,True,True

    
    if "-sample_mean_type" in sys.argv:

      ind=sys.argv.index("-sample_mean_type")
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


    #------------------------------------------------
    # read criteria file
    # Format is as pmag_criteria.txt
    #------------------------------------------------
    
    accept_new_parameters_default={}
    accept_new_parameters_null={}

    #  make a list of default parameters

    accept_new_parameters_default['specimen_n']=3
    accept_new_parameters_default['specimen_int_ptrm_n']=2
    accept_new_parameters_default['specimen_f']=0.
    accept_new_parameters_default['specimen_fvds']=0.
    accept_new_parameters_default['specimen_frac']=0.8
    accept_new_parameters_default['specimen_gap_max']=0.6
    accept_new_parameters_default['specimen_b_beta']=0.1
    accept_new_parameters_default['specimen_dang']=100000
    accept_new_parameters_default['specimen_drats']=100000
    accept_new_parameters_default['specimen_int_mad']=5
    accept_new_parameters_default['specimen_md']=100000
    accept_new_parameters_default['specimen_g']=0
    accept_new_parameters_default['specimen_q']=0
    accept_new_parameters_default['specimen_scat']=True

    accept_new_parameters_default['sample_int_n']=3
    accept_new_parameters_default['sample_int_sigma_uT']=6
    accept_new_parameters_default['sample_int_sigma_perc']=10
    accept_new_parameters_default['sample_int_interval_uT']=1000
    accept_new_parameters_default['sample_int_interval_perc']=1000
    accept_new_parameters_default['sample_int_n_outlier_check']=6

    for key in ( accept_new_parameters_default.keys()):
      accept_new_parameters_null[key]=accept_new_parameters_default[key]
    accept_new_parameters_null['specimen_int_ptrm_n']=0      
    accept_new_parameters_null['specimen_frac']=0
    accept_new_parameters_null['specimen_gap_max']=10
    accept_new_parameters_null['specimen_b_beta']=10000
    accept_new_parameters_null['specimen_int_mad']=100000
    accept_new_parameters_null['specimen_scat']=False
     
    
    if '-criteria_file'  in sys.argv:
        accept_new_parameters=accept_new_parameters_null
    else:
        accept_new_parameters=accept_new_parameters_default
        

    # Define bootstrap N bumber of interations
    BOOTSTRAP_N=1000
    
    # A list of all acceptance criteria used by program
    accept_specimen_keys=['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac','specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
    accept_sample_keys=['sample_int_n','sample_int_sigma_uT','sample_int_sigma_perc','sample_int_interval_uT','sample_int_interval_perc']

    try:  
        print "-I read criteria_file",WD+"/"+criteria_file
       
        fin=open(WD+"/"+criteria_file,'rU')
        line=fin.readline()
        criteria_keys=fin.readline()
        criteria_keys=criteria_keys.strip('\n').split('\t')
        for line in fin.readlines():
            line=line.strip('\n').split('\t')
            for i in range(len(line)):
                if 'pmag_criteria_code' in criteria_keys and "IE-SPEC" in line and "specimen" in criteria_keys[i] :
                  accept_new_parameters[criteria_keys[i]]=float(line[i])
                if 'pmag_criteria_code' in criteria_keys and "IE-SAMP" in line and "sample" in criteria_keys[i] :
                  accept_new_parameters[criteria_keys[i]]=float(line[i])
                if 'pmag_criteria_code' not in criteria_keys:
                    if criteria_keys[i]=="specimen_scat":
                        #print line[i]
                        if line[i]=="TRUE" or line[i]=="True" or line[i]=="1":
                            accept_new_parameters["specimen_scat"]=True
                    elif "sample" in criteria_keys[i] or "specimen" in criteria_keys[i]:
                        accept_new_parameters[criteria_keys[i]]=float(line[i])
            
        fin.close()                            
        print "-I- Threshold values:"
        for key in accept_new_parameters.keys():
            print "-I- thershold value %s: %f"%(key, accept_new_parameters[key])
    except:
        print "-W- cant find citeria file. Use default values:"
        print "-I- Threshold values:"
        for key in accept_new_parameters.keys():
            print "-I- thershold value %s: %f"%(key, accept_new_parameters[key])
        
       
    #------------------------------------------------
    # Initialize output files
    # outfiles are strored in ./thellier_interpreter
    #------------------------------------------------

    Command_line="mkdir ./thellier_interpreter"
    os.system(Command_line)
    All_acceptable_spec_interpretation_outfile=open(WD+"/thellier_interpreter/thellier_interpreter_all.txt",'w')
    Fout_specimens_bounds=open(WD+"/thellier_interpreter/thellier_interpreter_specimens_bounds.txt",'w')

    if DO_SAMPLE_BEST_MEAN:
       Fout_STDEV_OPT_redo=open(WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_redo",'w')
       Fout_STDEV_OPT_specimens=open(WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_specimens.txt",'w')
       Fout_STDEV_OPT_samples=open(WD+"/thellier_interpreter/thellier_interpreter_STDEV-OPT_samples.txt",'w')

       
    if DO_SAMPLE_BOOTSTRP_MEAN:
       #Fout_BS_redo=open(WD+"/thellier_interpreter/thellier_interpreter_BS_redo",'w')
       #Fout_BS_specimens=open(WD+"/thellier_interpreter/thellier_interpreter_BS_specimens.txt",'w')
       Fout_BS_samples=open(WD+"/thellier_interpreter/thellier_interpreter_BS_samples.txt",'w')

    if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       #Fout_BS_PAR_redo=open(WD+"/thellier_interpreter/thellier_interpreter_BS-PAR_redo",'w')
       #Fout_BS_PAR_specimens=open(WD+"/thellier_interpreter/thellier_interpreter_BS-PAR_specimens.txt",'w')
       Fout_BS_PAR_samples=open(WD+"/thellier_interpreter/thellier_interpreter_BS-PAR_samples.txt",'w')

    #------------------------------------------------
    # read exclude file
    # specimens in exclide file are ignored
    #------------------------------------------------

    exclude_specimens=[]
    if '-exclude' in sys.argv:
        fin=open(exclude_specimens_file,'rU')
        for line in fin.readlines():
            tmp=line.split()
            exclude_specimens.append(tmp[0])
            print "-W- WARNING: specimen %s is ignored in calculation"%tmp[0]
        print "-I- DONE reading exclude file %s"%exclude_specimens_file
        fin.close()

    #------------------------------------------------
    # read forced intrepretation
    # User can force program to use a given interpretation
    # The forced interpretation is accpeted only if it passes the criteria
    #------------------------------------------------

    forced_interpretation={}
    if '-forced_interpretation' in sys.argv:
        fin=open(forced_interpretation_file,'rU')
        for line in fin.readlines():
            tmp=line[:-1].split()
            specimen=tmp[0]
            Tmin=float(tmp[1])
            Tmax=float(tmp[2])
            if Tmin>Tmax:
                print "-E- ERROR: problem in forced interpretation of specimen %s"%specimen
            forced_interpretation[specimen]={}
            forced_interpretation[specimen]['Tmin']=Tmin
            forced_interpretation[specimen]['Tmax']=Tmax
            print "-W- WARNING: Specimen %s has forced interpretation. Check file" %specimen
        print "-I- DONE reading forced_interpretation file %s"%forced_interpretation_file
        fin.close() 
        
    #------------------------------------------------
    # Read magic measurement file and sort to blocks
    #------------------------------------------------

    # All data information is stored in Data[secimen]={}
    Data={}
    
    for dir_path in dir_pathes:
        meas_data,file_type=pmag.magic_read(dir_path+"/magic_measurements.txt")
        print "-I- Read magic file from ./%s" %(dir_path)
    
        # get list of unique specimen names
        
        CurrRec=[]
        sids=pmag.get_specs(meas_data) # samples ID's
        #print "get sids"
        
        for s in sids:

            # ignore excluded specimens
            if s in exclude_specimens:
                print "-W- WARNING: specimen %s is in exclude file. Ignoring specimen %s"%(s,s)
                continue
            if s not in Data.keys():
                Data[s]={}
                Data[s]['datablock']=[]
                Data[s]['trmblock']=[]
             
            zijdblock,units=pmag.find_dmag_rec(s,meas_data)
            Data[s]['zijdblock']=zijdblock

        #print "get zij"
            
        for rec in meas_data:
            s=rec["er_specimen_name"]
            if "magic_method_codes" not in rec.keys():
                rec["magic_method_codes"]=""
            #methods=rec["magic_method_codes"].split(":")
            if "LP-PI-TRM" in rec["magic_method_codes"]:
                Data[s]['datablock'].append(rec)
            if "LP-TRM" in rec["magic_method_codes"]:
                Data[s]['trmblock'].append(rec)
        #for s in sids:
            
        specimens=Data.keys()
        specimens.sort()


        
        
    
    
    #------------------------------------------------
    # Read anisotropy file from rmag_anisotropy.txt
    #------------------------------------------------

    for dir_path in dir_pathes:
        try:
            anis_data,file_type=pmag.magic_read(dir_path+'/rmag_anisotropy.txt')
            print "-I- Anisotropy data read  %s/from rmag_anisotropy.txt"%dir_path
            for AniSpec in anis_data:
                s=AniSpec['er_specimen_name']
                if s not in Data.keys():
                    print "-W- WARNING: specimen %s in rmag_anisotropy.txt but not in magic_measurement.txt. Check it !"%s
                    continue
                if 'AniSpec' in Data[s].keys():
                    print "-E- ERROR: more than one anisotropy data for specimen %s Fix it!"%s
                Data[s]['AniSpec']=AniSpec
        except:
            print "-W- Cant read rmag_anistropy.txt"

    #------------------------------------------------
    # Prepare header for "Thellier_auto_interpretation.all.txt" 
    # All the acceptable interpretation are saved in this file
    #------------------------------------------------
    All_acceptable_spec_interpretation_outfile.write("tab\tpmag_specimens\n")
    String="er_specimen_name\tmeasurement_step_min\tmeasurement_step_max\tspecimen_lab_field_dc_uT\tspecimen_int_corr_anisotropy\tspecimen_int_corr_nlt\tspecimen_int_uT\t"
    for key in accept_specimen_keys:
        String=String+key+"\t"
    String=String[:-1]+"\n"
    All_acceptable_spec_interpretation_outfile.write(String)



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
    
    #--------------------------------------------------------------
    # Find the "acceptable" interpretations ("Grade A) of specimens
    # by looping thorugh all data points in the Arai plot
    #--------------------------------------------------------------                    
        
    #specimen=0
    
    # All grade A recs are stored here
    
    All_grade_A_Recs={}
    counter=0
    specimens_counter=len(specimens)
    for s in specimens:
        
        print "\n-I- Srart looping through specimen %s to find all grade A acceptable interpretations" %s
        
        datablock = Data[s]['datablock']

        if len(datablock) <4:
           print "-E- ERROR: skipping specimen %s, data block is too small - moving forward "%s
           continue 

        zijdblock=Data[s]['zijdblock']
        
        araiblock,field=pmag.sortarai(datablock,s,0)

        first_Z=araiblock[0]
        if len(first_Z)<3:
            continue
        

        if len(araiblock[0])!= len(araiblock[1]):
           print "-E- ERROR: unequal length of Z steps and I steps. Skipping specimen %s"% s
           continue

        #--------------------------------------------------------------
        # collect all zijderveld data to array and calculate VDS
        #--------------------------------------------------------------
        
        z_temperatures=[row[0] for row in zijdblock]
        zdata=[]
        vector_diffs=[]
        NRM=zijdblock[0][3]

        for k in range(len(zijdblock)):
            DIR=[zijdblock[k][1],zijdblock[k][2],zijdblock[k][3]/NRM]
            cart=dir2cart(DIR)
            zdata.append([cart[0],cart[1],cart[2]])
            if k>0:
                vector_diffs.append(sqrt(sum((array(zdata[-2])-array(zdata[-1]))**2)))
        vector_diffs.append(sqrt(sum(array(zdata[-1])**2))) # last vector of the vds
        vds=sum(vector_diffs)  # vds calculation       

        zdata=array(zdata)  
        
        #--------------------------------------------------------------
        # collect all Arai plot data points to array 
        #--------------------------------------------------------------

        # collect Arai data points
        zerofields,infields=araiblock[0],araiblock[1]

        x_Arai,y_Arai,t_Arai=[],[],[] # all the data points               

        #NRM=zerofields[0][3]
        infield_temperatures=[row[0] for row in infields]

        # check a correct order of tempertures
        PROBLEM=False
        for i in range (2,len(infield_temperatures)):
            if float(infield_temperatures[i])<float(infield_temperatures[i-1]):
                PROBLEM=True
                break
        if PROBLEM:
            print "-E ERROR: wrong order of temperatures specimen %s. Skipping specimen!"%s
            continue
                        
        
        for k in range(min(len(zerofields),len(infields))):                  
          index_infield=infield_temperatures.index(zerofields[k][0])
          x_Arai.append(infields[index_infield][3]/NRM)
          y_Arai.append(zerofields[k][3]/NRM)

        x_Arai=array(x_Arai)
        y_Arai=array(y_Arai)



        #--------------------------------------------------------------
        # collect all pTRM check to array 
        #--------------------------------------------------------------

##        ptrm_checks = araiblock[2]
##        zerofield_temperatures=[row[0] for row in zerofields]
##
##        x_ptrm_check,y_ptrm_check=[],[]
##        
##        for k in range(len(ptrm_checks)):                  
##          index_zerofield=zerofield_temperatures.index(ptrm_check[k][0])
##          fsc[k][3]/NRM)
##          y_ptrm_check.append(zerofields[index_zerofield][3]/NRM)
##
##        x_ptrm_check=array(x_ptrm_check)  
##        y_ptrm_check=array(y_ptrm_check)

        #--------------------------------------------------------------    
        # looping through all data points in the Arai plot
        #--------------------------------------------------------------
        
        n_min=int(accept_new_parameters['specimen_n'])
        for start in range (0,len(x_Arai)-n_min+1,1):
           for end in range (start+n_min-1,len(x_Arai),1):
               counter+=1
               rec=datablock[0]               
               # get the paleointensity parameters
               #runtime_1 = time.time()

               pars={}
               #pars,errcode=pmag.PintPars(araiblock,zijdblock,start,end)
                


               #runtime_2 = time.time() - runtime_1
               #print "-I- runtime  for PintPars:", runtime_2
               
               # first define essential information 
               pars['measurement_step_unit']="K"
               pars["specimen_lab_field_dc"]=field
               pars["er_specimen_name"]=s
               pars["er_sample_name"]=rec["er_sample_name"]
               #pars["er_site_name"]=rec["er_site_name"]
               #pars['specimen_int_n']=end-start+1
               pars['specimen_n']=end-start+1
               pars["measurement_step_min"]=araiblock[0][start][0]
               pars["measurement_step_max"]=araiblock[0][end][0]


               #-------------------------------------------------
               # calualte PCA of the zerofield steps
               # MAD calculation following Kirschvink (1980)
               # DANG following Tauxe and Staudigel (2004)
               #-------------------------------------------------               

               if pars["measurement_step_min"] not in z_temperatures or pars["measurement_step_max"] not in z_temperatures:
                    print "-E- ERROR specimen %s. temperatures %f or %f in Arai plot but not in Zojderveld plot. Chack data!"%(s,pars["measurement_step_min"],pars["measurement_step_max"])
                    continue
               zstart=z_temperatures.index(pars["measurement_step_min"])
               zend=z_temperatures.index(pars["measurement_step_max"])

               zdata_segment=zdata[zstart:zend+1]

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
                 DIR_PCA=cart2dir(v1*-1)
                 best_fit_vector=v1*-1
               else:
                 DIR_PCA=cart2dir(v1)
                 best_fit_vector=v1

               # MAD Kirschvink (1980)
               if t1==0:t1=1e-10
               MAD=degrees(arctan(sqrt((t2+t3)/t1)))

               # DANG Tauxe and Staudigel 2004
               DANG=degrees( arccos( ( dot(cm, best_fit_vector) )/( sqrt(sum(cm**2)) * sqrt(sum(best_fit_vector**2)))))
               
                
##               print "my PCA: dec,inc,MAD,DANG",DIR_PCA[0],DIR_PCA[1],MAD,DANG
##               print "pmagpy dec,inc,MAD",pars["specimen_dec"],pars["specimen_inc"],pars["specimen_int_mad"],pars["specimen_dang"]
##               
##               if abs(1- pars["specimen_dec"]/DIR_PCA[0]) >0.02:
##                  print "specimen_dec"
##                  exit()
##                  
##               if abs(1- pars["specimen_inc"]/DIR_PCA[1]) >0.02:
##                  print "specimen_inc"
##                  exit()
##                  
##               if abs(1- pars["specimen_int_mad"]/MAD) >0.02:
##                  print "specimen_int_mad"
##                  exit()
##
##               if abs(1- pars["specimen_dang"]/DANG) >0.02:
##                  print "specimen_dang"
##                  exit()


               # best fit PCA direction
               pars["specimen_dec"] =  DIR_PCA[0]
               pars["specimen_inc"] =  DIR_PCA[1]

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
               n=float(pars["specimen_n"])
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

               f_vds=abs((y_prime[0]-y_prime[-1])/vds)

               g_Coe= 1 - (sum((y_prime[:-1]-y_prime[1:])**2) / sum((y_prime[:-1]-y_prime[1:]))**2 )

               q_Coe=abs(york_b)*f_Coe*g_Coe/york_sigma
               
               #check and compare with pmagpy
##               print "my b,sigma,beta,f,fvds,g_Coe,q_Coe",york_b,york_sigma,beta_Coe,f_Coe,f_vds,g_Coe,q_Coe
##               print "pmagpy b,sigma,beta,f,fvds,g_Coe"\
##                     ,pars["specimen_b"],pars["specimen_b_sigma"],pars["specimen_b_beta"],pars["specimen_f"],pars["specimen_fvds"],pars["specimen_g"],pars["specimen_q"]
##
##               
##               if abs(1- pars["specimen_b_beta"]/beta_Coe) >0.02:
##                  print "beta"
##                  exit()
##               if abs(1- pars["specimen_b"]/york_b) >0.02:
##                  print "b"
##                  exit()
##               if abs(1- pars["specimen_b_sigma"]/york_sigma) >0.02:
##                  print "b_sogma"
##                  exit()
##               if abs(1- pars["specimen_f"]/f_Coe) >0.02:
##                  print "f coe"
##                  exit()
##               if abs(1- pars["specimen_fvds"]/f_vds) >0.02:
##                  print "f vds"
##                  exit()
##               if abs(1- pars["specimen_g"]/g_Coe) >0.02:
##                  print "specimen_g"
##                  exit()
##               if abs(1- pars["specimen_q"]/q_Coe) >0.02:
##                  print "specimen_q"
##                  exit()


               pars["specimen_b"]=york_b
               pars["specimen_b_sigma"]=york_sigma
               pars["specimen_b_beta"]=beta_Coe
               pars["specimen_f"]=f_Coe
               pars["specimen_fvds"]=f_vds
               pars["specimen_int"]=-1*field*pars["specimen_b"]
                                

               #-------------------------------------------------
               # pTRM checks:
               # DRAT ()
               # and
               # DRATS (Tauxe and Staudigel 2004)
               # Ron, fix bug in DRATS !
               #-------------------------------------------------
               
               ptrm_checks = araiblock[2]
               zerofield_temperatures=[row[0] for row in zerofields]
                
               x_ptrm_check_in_0_to_end,y_ptrm_check_in_0_to_end=[],[]
               x_ptrm_check_in_start_to_end,y_ptrm_check_in_start_to_end=[],[]
               
               pTRM_diff_in_segment=[]
               x_Arai_compare=[]
               if len(ptrm_checks)==0:
                   pars['specimen_drats']=-1
               else: 
                   for k in range(len(ptrm_checks)):

                       if ptrm_checks[k][0] not in zerofield_temperatures:
                           print "-W- WARNING: temprature %f was found in pTRM check but not in Arai plot"%ptrm_checks[k][0]
                           continue
                       index_zerofield=zerofield_temperatures.index(ptrm_checks[k][0])
                       index_infield=infield_temperatures.index(ptrm_checks[k][0])
                       
                       if index_zerofield != index_infield :
                           print "-E- ERROR: something wrong with Arai plot data of specimen %s. Check measurement file!"%s
                           exit()
                           
                       if index_zerofield <= end: #
                           x_ptrm_check_in_0_to_end.append(ptrm_checks[k][3]/NRM)
                           y_ptrm_check_in_0_to_end.append(zerofields[index_zerofield][3]/NRM)
                           x_Arai_compare.append(infields[index_infield][3]/NRM)

                           if index_zerofield >= start:
                              x_ptrm_check_in_start_to_end.append(ptrm_checks[k][3]/NRM)
                              y_ptrm_check_in_start_to_end.append(zerofields[index_zerofield][3]/NRM)
                            
                   x_ptrm_check_in_0_to_end=array(x_ptrm_check_in_0_to_end)
                   y_ptrm_check_in_0_to_end=array(y_ptrm_check_in_0_to_end)
                   x_ptrm_check_in_start_to_end=array(x_ptrm_check_in_start_to_end)
                   y_ptrm_check_in_start_to_end=array(y_ptrm_check_in_start_to_end)
                   
                                                      
                   x_Arai_compare=array(x_Arai_compare)

                   DRATS=100*(abs(sum(x_ptrm_check_in_0_to_end-x_Arai_compare))/(infields[end][3]/NRM))
                   int_ptrm_n=len(x_ptrm_check_in_0_to_end)
                   if int_ptrm_n > 0:
                       pars['specimen_int_ptrm_n']=int_ptrm_n
                       pars['specimen_drats']=DRATS
                   else:
                       pars['specimen_int_ptrm_n']=int_ptrm_n
                       pars['specimen_drats']=-1


##               print "my DRATS", DRATS
##               print "pmagpy DRATS,",pars["specimen_drats"]
##               if abs(1- pars["specimen_drats"]/DRATS) >0.02:
##                  print "specimen_drats"
##                  raw_input("check drats")


               #-------------------------------------------------
               # Tail check MD
               #-------------------------------------------------


               # collect tail checks 


               ptrm_tail = araiblock[3]
               x_tail_check,y_tail_check,tail_check_temperatures=[],[],[]

               for k in range(len(ptrm_tail)):
                  if ptrm_tail[k][0] in zerofield_temperatures:
                      index_infield=infield_temperatures.index(ptrm_tail[k][0])
                      if index_infield <= end and index_infield >= start:
                          x_tail_check.append(infields[index_infield][3]/NRM)
                          y_tail_check.append(ptrm_tail[k][3]/NRM + zerofields[index_infield][3]/NRM)
                          tail_check_temperatures.append(ptrm_tail[k][0])

               x_tail_check=array(x_tail_check)  
               y_tail_check=array(y_tail_check)
               tail_check_temperatures=array(tail_check_temperatures)

               
               pars['specimen_md']=-1

               # TO DO !
               
               #-------------------------------------------------
               # MD Z check
               #-------------------------------------------------
                               
               pars['specimen_z']=-1

               #-------------------------------------------------                     
               # Calculate the new 'beta box' parameter
               # all datapoints, pTRM checks, and tail-checks, should be inside a "beta box"
               # For definition of "beta box" see Shaar and Tauxe (2012)
               #-------------------------------------------------                     

               if accept_new_parameters['specimen_scat']==True or accept_new_parameters['specimen_scat']=="True" or accept_new_parameters['specimen_scat']=="TRUE" or accept_new_parameters['specimen_scat']==1:
                   pars["fail_arai_beta_box_scatter"]=False
                   pars["fail_ptrm_beta_box_scatter"]=False
                   pars["fail_tail_beta_box_scatter"]=False

                   # best fit line 
                   b=pars['specimen_b']
                   cm_x=mean(array(x_Arai_segment))
                   cm_y=mean(array(y_Arai_segment))
                   a=cm_y-b*cm_x

                   # lines with slope = slope +/- 2*(specimen_b_beta)

                   if 'specimen_b_beta' not in accept_new_parameters.keys():
                     print "-E- ERROR: specimen_beta not in pmag_criteria file, cannot calculate 'beta box' scatter" 

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
                     pars["fail_arai_beta_box_scatter"]=True


                   # check if the pTRM checks data points are in the 'box'

                   # using x_ptrm_check_in_segment (defined above)
                   # using y_ptrm_check_in_segment (defined above)
                   

                   if len(x_ptrm_check_in_start_to_end) > 0:

                      # the two bounding lines
                      ymin=intercept1+x_ptrm_check_in_start_to_end*slop1
                      ymax=intercept2+x_ptrm_check_in_start_to_end*slop2

                      # arrays of "True" or "False"
                      check_1=y_ptrm_check_in_start_to_end>ymax
                      check_2=y_ptrm_check_in_start_to_end<ymin

                      # check if at least one "True" 
                      if (sum(check_1)+sum(check_2))>0:
                        pars["fail_ptrm_beta_box_scatter"]=True


                   if len(x_tail_check) > 0:

                      # the two bounding lines
                      ymin=intercept1+x_tail_check*slop1
                      ymax=intercept2+x_tail_check*slop2

                      # arrays of "True" or "False"
                      check_1=y_tail_check>ymax
                      check_2=y_tail_check<ymin


                      # check if at least one "True" 
                      if (sum(check_1)+sum(check_2))>0:
                        pars["fail_tail_beta_box_scatter"]=True
                        #print "check, fail fail_ptrm_beta_box_scatter"


               #-------------------------------------------------  
               # Calculate the new FRAC parameter (Shaar and Tauxe, 2012).
               # also check that the 'gap' between consecutive measurements is less than 0.5(VDS)
               #
               #-------------------------------------------------  

               ####  def find_specimen_frac(pars,zijdblock,accept_new_parameters,start,end):
               vector_diffs_segment=vector_diffs[zstart:zend]
               FRAC=sum(vector_diffs_segment)/vds
               max_FRAC_gap=max(vector_diffs_segment/sum(vector_diffs_segment))
               
               pars['specimen_frac']=FRAC
               pars['specimen_gap_max']=max_FRAC_gap
               
               #-------------------------------------------------

               
               # check if this was a "forced interpretation"
               if s in forced_interpretation.keys():
                   if float(pars["measurement_step_min"])==forced_interpretation[s]['Tmin']+273. and\
                      float(pars["measurement_step_max"])==forced_interpretation[s]['Tmax']+273.:
                       print "-W- Specimen %s has a forced interpretation Tmin=%.2f Tmax=%.2f."%(s,forced_interpretation[s]['Tmin']+273,forced_interpretation[s]['Tmax']+273.)
                   else:
                       continue
              
               #-------------------------------------------------

                 # dont delete, maybe use it later    
##               keys=pars.keys()
##               keys.sort(); String=""
##               for key in keys:
##                   String=String+"%s: %s  ;  "%(key, pars[key])


               #-------------------------------------------------            
               # check if pass the criteria
               #-------------------------------------------------

               # distinguish between upper threshold value and lower threshold value
               parameters_with_upper_bounds= ['specimen_gap_max','specimen_b_beta','specimen_dang','specimen_drats','specimen_int_mad','specimen_md']
               parameters_with_lower_bounds= ['specimen_n','specimen_int_ptrm_n','specimen_f','specimen_fvds','specimen_frac']
               # check myself
               for key in accept_specimen_keys:
                   if key not in parameters_with_upper_bounds and key not in parameters_with_lower_bounds:
                       print "Health message: Ron, Fix error in parameters_with_upper_bounds parameters_with_lower_bounds! missing key=%s"%key
               

               Reject_Specimen=False
               message_string= "-I- specimen %s (%.0f-%.0f) FAIL on: "%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
               for parameter in parameters_with_upper_bounds:              
                   if parameter in accept_new_parameters.keys():
                       if pars[parameter] > accept_new_parameters[parameter]:
                           message_string=message_string+parameter + "= %f,  " %pars[parameter]
                           Reject_Specimen=True
                       
               for parameter in parameters_with_lower_bounds:
                   if parameter in accept_new_parameters.keys():
                       if pars[parameter] < accept_new_parameters[parameter]:
                           message_string=message_string+parameter + "= %f,  " %pars[parameter]
                           Reject_Specimen=True
                           
               if  accept_new_parameters['specimen_scat']==True or accept_new_parameters['specimen_scat']=="True" or accept_new_parameters['specimen_scat']=="TRUE" or accept_new_parameters['specimen_scat']==1:
                   if pars["fail_arai_beta_box_scatter"]==True:
                       message_string=message_string+ "Arai Scatter ('beta box'), "
                       Reject_Specimen=True

                   if pars["fail_ptrm_beta_box_scatter"]==True:
                       message_string=message_string+ "pTRM check Scatter ('beta box'), "
                       Reject_Specimen=True
                                              
               if Reject_Specimen:
                   print message_string 
                   continue
               else:
                   print "-I- specimen %s (%.0f-%.0f) PASS"%(s,float(pars["measurement_step_min"])-273, float(pars["measurement_step_max"])-273)
             
               #-------------------------------------------------            
               # Calculate anistropy correction factor
               #-------------------------------------------------            
               
               if "AniSpec" in Data[s]:
                   AniSpec=Data[s]['AniSpec']
                   AniSpecRec=doaniscorr(pars,AniSpec)
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
               
               if 'NLT_parameters' in Data[s]:

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
                   #print pars.keys()
                   pars["NLT_specimen_correction_factor"]=-999
               #-------------------------------------------------                    
               # save 'acceptable' (grade A) specimen interpretaion
               #-------------------------------------------------                
               if s not in All_grade_A_Recs.keys():
                   All_grade_A_Recs[s]=[]
               All_grade_A_Recs[s].append(pars)                                

               #--------------------------------------------------------------
               # Save all the grade A interpretation in thellier_interpreter_all.txt
               #--------------------------------------------------------------
    
               String=s+"\t"
               String=String+"%.0f\t"%(float(pars["measurement_step_min"])-273.)
               String=String+"%.0f\t"%(float(pars["measurement_step_max"])-273.)
               String=String+"%.0f\t"%(float(pars["specimen_lab_field_dc"])*1e6)
               if "AC_specimen_correction_factor" in pars.keys():
                   String=String+"%.2f\t"%float(pars["AC_specimen_correction_factor"])
               else:
                   String=String+"-"
               if  float(pars["NLT_specimen_correction_factor"])!=-999:
                   String=String+"%.2f\t"%float(pars["NLT_specimen_correction_factor"])
               else:
                   String=String+"-\t"
               if "NLTC_specimen_int" in  pars.keys():
                   Bancient=float(pars["NLTC_specimen_int"])
               elif  "AC_specimen_int" in pars.keys():
                   Bancient=float(pars["AC_specimen_int"])
               else:
                   Bancient=float(pars["specimen_int"])                   
               
               String=String+"%.1f\t"%(Bancient*1e6)


               for key in accept_specimen_keys:
                   String=String+"%.2f"%(pars[key])+"\t"
               String=String[:-1]+"\n"

               All_acceptable_spec_interpretation_outfile.write(String)
                               
    #--------------------------------------------------------------
    # Sorting all the paleointensties to a single file that contains
    # for each specimen the minimum and the maximum "acceptable" interpretation.
    # thellier_interpreter_specimens_bounds.txt
    #--------------------------------------------------------------

    String="Slecetion criteria:\n"
    for key in accept_new_parameters.keys():
        if "specimen" in key:
            String=String+key+"\t"
    Fout_specimens_bounds.write(String[:-1]+"\n")
       
    if DO_SAMPLE_BEST_MEAN:
       Fout_STDEV_OPT_samples.write(String[:-1]+"\n")
    if DO_SAMPLE_BOOTSTRP_MEAN:
       Fout_BS_samples.write(String[:-1]+"\n")
    if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       Fout_BS_PAR_samples.write(String[:-1]+"\n")

    String=""
    for key in accept_new_parameters.keys():
        if "specimen" in key:
            String=String+"%f"%accept_new_parameters[key]+"\t"        
    Fout_specimens_bounds.write(String[:-1]+"\n")
    
    if DO_SAMPLE_BEST_MEAN:
       Fout_STDEV_OPT_samples.write(String[:-1]+"\n")
       Fout_STDEV_OPT_samples.write("---------------------------------\n")

    if DO_SAMPLE_BOOTSTRP_MEAN:
       Fout_BS_samples.write(String[:-1]+"\n")
       Fout_BS_samples.write("---------------------------------\n")

    if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       Fout_BS_PAR_samples.write(String[:-1]+"\n")
       Fout_BS_PAR_samples.write("---------------------------------\n")


    Fout_specimens_bounds.write("--------------------------------\n")

    Fout_specimens_bounds.write("er_sample_name\ter_specimen_name\tspecimen_int_corr_anisotropy\tAnisotropy_code\tspecimen_int_corr_nlt\tspecimen_lab_field_dc_uT\tspecimen_int_min_uT\tspecimen_int_max_uT\tWARNING\n")



    String="tab\ter_specimens\ner_sample_name\ter_specimen_name\tspecimen_int_uT\tmeasurement_step_min\tmeasurement_step_min\tspecimen_lab_field_dc\tAnisotropy_correction_factor\tNLT_correction_factor\t"
    for key in accept_specimen_keys:
        String=String+key+"\t"        
    if DO_SAMPLE_BEST_MEAN:
       Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
       
    #if DO_SAMPLE_BOOTSTRP_MEAN:
       #Fout_BS_specimens.write(String[:-1]+"\n")
       
    #if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       #Fout_BS_PAR_specimens.write(String[:-1]+"\n")

    
    specimens=All_grade_A_Recs.keys()
    specimens.sort()
    for specimen in specimens:

        sample=All_grade_A_Recs[specimen][0]["er_sample_name"]
        B_lab=float(All_grade_A_Recs[specimen][0]["specimen_lab_field_dc"])*1e6
        B_min,B_max=1e10,0.
        NLT_factor_min,NLT_factor_max=1e10,0.
        all_B_tmp_array=[]

        for rec in All_grade_A_Recs[specimen]:
            if "NLTC_specimen_int" in rec.keys():
                B_anc=float(rec["NLTC_specimen_int"])*1e6
            elif  "AC_specimen_int" in rec.keys():
                B_anc=float(rec["AC_specimen_int"])*1e6
            else:
                B_anc=float(rec["specimen_int"])*1e6
                WARNING="WARNING: No Anistropy correction"
            if "AC_specimen_int" in rec.keys():
                AC_correction_factor=rec["AC_specimen_correction_factor"]
                AC_correction_type=Data[specimen]['AniSpec']["anisotropy_type"]
                WARNING=""

            else:
                AC_correction_factor=1.
                AC_correction_type="-"
                WARNING="WARNING: No Anistropy correction"

                
            if B_anc< B_min:
                B_min=B_anc
            if B_anc > B_max:
                B_max=B_anc
            if rec["NLT_specimen_correction_factor"]!=-999:
                NLT_f=rec['NLT_specimen_correction_factor']
                if NLT_f< NLT_factor_min:
                    NLT_factor_min=NLT_f
                if NLT_f > NLT_factor_max:
                    NLT_factor_max=NLT_f                
            # for bootstrap calculation
        #rec["specimen_max_ratio_4_BS"]=B_min/B_max
        if rec["NLT_specimen_correction_factor"] != -999:
            NLT_factor="%.2f"%(NLT_factor_max)
        else:
            NLT_factor="-"

        if  specimen in forced_interpretation.keys():
            WARNING=WARNING+ " specimen intterpretation is forced. See forced interpretation file; "
        Data[specimen]["Warnings"]=WARNING
        
        String="%s\t%s\t%.2f\t%s\t%s\t%.1f\t%.1f\t%.1f\t%s\n"\
                %(sample,specimen,AC_correction_factor,AC_correction_type,NLT_factor,B_lab,B_min,B_max,WARNING)
        Fout_specimens_bounds.write(String)

    #--------------------------------------------------------------
    # Find the 'best mean':
    # the interprettaions that give
    # the minimum standrad deviation.
    #
    # Outlier check is done only if number of specimen >= accept_new_parameters['sample_int_n_outlier_check']
    # an outlier exists if one (and only one!) specimen has an outlier result defined by:
    # Bmax(specimen_1) < mean[max(specimen_2),max(specimen_3),max(specimen_3)...] - 2*sigma
    # or
    # Bmin(specimen_1) < mean[min(specimen_2),min(specimen_3),min(specimen_3)...] + 2*sigma
    #
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Sort all grade A 'acceptable' specimen to a dictionary 
    #--------------------------------------------------------------

    Redo_data_specimens={}
    Grade_A_samples={}  # Grade_A_samples[sample][specimen] is a list of all the grade A interpretation.

    # prepare header for "Thellier_auto_interpretation.samples.txt"
    if DO_SAMPLE_BEST_MEAN:
        Fout_STDEV_OPT_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_sigma_uT\tsample_int_sigma_perc\tsample_int_interval_uT\tsample_int_interval_perc\tWarning\n")

    # prepare header for "Thellier_interpreter_bootstrap_sample_mean.txt"
    if DO_SAMPLE_BOOTSTRP_MEAN:
       Fout_BS_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")

    if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       Fout_BS_PAR_samples.write("er_sample_name\tsample_int_n\tsample_int_uT\tsample_int_68_low\tsample_int_68_high\tsample_int_95_low\tsample_int_95_high\tsample_int_sigma_uT\tsample_int_sigma_perc\tWARNING\n")

    
    # Sort all grade A interpretation
    for specimen in specimens:
        sample=All_grade_A_Recs[specimen][0]["er_sample_name"]
        if sample not in Grade_A_samples.keys():
            Grade_A_samples[sample]={}
        if specimen not in Grade_A_samples[sample].keys() and len(All_grade_A_Recs[specimen])>0:
            Grade_A_samples[sample][specimen]=[]

        Redo_data_specimens[specimen]={}

        # check for forced interpretation
        if specimen in forced_interpretation.keys() and 'PmagSpecRec' not in forced_interpretation[specimen].keys():
                print "-E- Error: forced interpretation temperture bounds for specimen %s dont pass criteria"%specimen
        if  specimen in forced_interpretation.keys() and 'PmagSpecRec'  in forced_interpretation[specimen].keys():       
            Tmin=forced_interpretation[specimen]['Tmin']
            Tmax=forced_interpretation[specimen]['Tmax']
            print "-W- WARNING: using forced interpretation  for specimen %s: %.0f, %.0f"%(specimen,Tmin,Tmax)
            rec=forced_interpretation[specimen]['PmagSpecRec']
            
            if "NLTC_specimen_int" in rec.keys():
                B_anc=float(rec["NLTC_specimen_int"])*1e6
            elif  "AC_specimen_int" in rec.keys():
                B_anc=float(rec["AC_specimen_int"])*1e6
            else:
                B_anc=float(rec["specimen_int"])*1e6
                
            Grade_A_samples[sample][specimen].append(B_anc)
            
            Redo_data_specimens[specimen][B_anc]=rec

        else:
            for rec in All_grade_A_Recs[specimen]:
                    
                if "NLTC_specimen_int" in rec.keys():
                    B_anc=float(rec["NLTC_specimen_int"])*1e6
                elif  "AC_specimen_int" in rec.keys():
                    B_anc=float(rec["AC_specimen_int"])*1e6
                else:
                    B_anc=float(rec["specimen_int"])*1e6

                Grade_A_samples[sample][specimen].append(B_anc)                
                Redo_data_specimens[specimen][B_anc]=rec


    samples=Grade_A_samples.keys()
    samples.sort()


    #--------------------------------------------------------------
    # Calculate samples means
    #--------------------------------------------------------------
    runtime_start_means = time.time()   # calculate runtime                                                              

    #--------------------------------------------------------------
    # check for outlier specimens 
    #--------------------------------------------------------------
    
    for sample in samples:
        WARNING=""
        # check for outlier specimen
        exclude_specimen=""
        exclude_specimens_list=[]
        if len(Grade_A_samples[sample].keys())>=float(accept_new_parameters['sample_int_n_outlier_check']):            
            all_specimens=Grade_A_samples[sample].keys()
            for specimen in all_specimens:
                B_min_array,B_max_array=[],[]
                for specimen_b in all_specimens:
                    if specimen_b==specimen: continue
                    B_min_array.append(min(Grade_A_samples[sample][specimen_b]))
                    B_max_array.append(max(Grade_A_samples[sample][specimen_b]))
                if max(Grade_A_samples[sample][specimen]) < mean(B_min_array) - 2*std(B_min_array) \
                   or min(Grade_A_samples[sample][specimen]) > mean(B_max_array) + 2*std(B_max_array):
                    if specimen not in exclude_specimens_list:
                        exclude_specimens_list.append(specimen)
                        
            if len(exclude_specimens_list)>1:
                print "-I- checking now if any speimens to exlude due to B_max<average-2*sigma or B_min > average+2*sigma sample %s" %s
                print "-I- more than one specimen can be excluded:",exclude_specimens_list
                exclude_specimens_list=[]

            if len(exclude_specimens_list)==1:
                #print exclude_specimens_list
                exclude_specimen=exclude_specimens_list[0]
                del Grade_A_samples[sample][exclude_specimen]
                print "-W- WARNING: specimen %s is exluded from sample %s because of an outlier result. "%(exclude_specimens_list[0],sample)
                WARNING=WARNING+"excluding specimen %s; "%(exclude_specimens_list[0])

    #--------------------------------------------------------------
    # calcuate 'best means' and write results to files
    #--------------------------------------------------------------
    
        n_no_atrm=0
        for specimen in Grade_A_samples[sample].keys():
            if "No Anistropy" in Data[specimen]["Warnings"]:
                n_no_atrm+=1

        #print sample
        #print "int_n",accept_new_parameters['sample_int_n']
        #print "len",len(Grade_A_samples[sample].keys())
        if len(Grade_A_samples[sample].keys())>=accept_new_parameters['sample_int_n']:
            Best_interpretations,best_mean,best_std=find_sample_min_std(Grade_A_samples[sample])
            sample_acceptable_min,sample_acceptable_max = find_sample_min_max_interpretation (Grade_A_samples[sample],accept_new_parameters)
            sample_int_interval_uT=sample_acceptable_max-sample_acceptable_min
            sample_int_interval_perc=100*((sample_acceptable_max-sample_acceptable_min)/best_mean)       
            print "-I- sample %s 'STDEV mean' interpretation: "%sample,Best_interpretations
            print "-I- sample %s 'STDEV mean=%f, STDEV std=%f "%(sample,best_mean,best_std)
            print "-I- sample %s 'minimum/maximum accepted interpretation  %.2f,%.2f" %(sample,sample_acceptable_min,sample_acceptable_max)
            if best_std <= accept_new_parameters['sample_int_sigma_uT'] or 100*(best_std/best_mean) <= accept_new_parameters['sample_int_sigma_perc']:
                if sample_int_interval_uT <= accept_new_parameters['sample_int_interval_uT'] or sample_int_interval_perc <= accept_new_parameters['sample_int_interval_perc']:
                    # write the interpretation to a redo file
                    for specimen in Grade_A_samples[sample].keys():
                        t_min=int(float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['measurement_step_min']))
                        t_max=int(float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['measurement_step_max']))
                                    
                        Fout_STDEV_OPT_redo.write("%s\t%i\t%i\n"%(specimen,t_min,t_max))

                    # write the interpretation to the specimen file
                        B_lab=float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['specimen_lab_field_dc'])*1e6
                        sample=Redo_data_specimens[specimen][Best_interpretations[specimen]]['er_sample_name']
                        if 'AC_specimen_correction_factor' in Redo_data_specimens[specimen][Best_interpretations[specimen]].keys():
                            Anisotropy_correction_factor="%.2f"%float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['AC_specimen_correction_factor'])
                        else:
                            Anisotropy_correction_factor="-"                
                        if  Redo_data_specimens[specimen][Best_interpretations[specimen]]["NLT_specimen_correction_factor"] != -999:
                            NLT_correction_factor="%.2f"%float(Redo_data_specimens[specimen][Best_interpretations[specimen]]['NLT_specimen_correction_factor'])
                        else:
                            NLT_correction_factor="-"
                        #print Best_interpretations[specimen]
                        
                        #print "-I-",sample,specimen,float(Best_interpretations[specimen]),t_min-273,t_max-273,B_lab,Anisotropy_correction_factor,NLT_correction_factor
                        Fout_STDEV_OPT_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t"\
                                             %(sample,specimen,float(Best_interpretations[specimen]),t_min-273,t_max-273,B_lab,Anisotropy_correction_factor,NLT_correction_factor))
                        String=""
                        for key in accept_specimen_keys:
                            String=String+"%.2f"%(Redo_data_specimens[specimen][Best_interpretations[specimen]][key])+"\t"
                        Fout_STDEV_OPT_specimens.write(String[:-1]+"\n")
                                             
                    # write the interpretation to the sample file
                  
                    if n_no_atrm>0:
                         WARNING=WARNING+"% i specimens with no anisotropy correction; "%int(n_no_atrm)
                    String="%s\t%i\t%.2f\t%.2f\t%.3f\t%.2f\t%.2f\t%s\n"%(sample,len(Best_interpretations),best_mean,best_std,100*(best_std/best_mean),sample_int_interval_uT,sample_int_interval_perc,WARNING)
                    Fout_STDEV_OPT_samples.write(String)
                else:
                 print "-I- sample %s FAIL on sample_int_interval_uT or sample_int_interval_perc"%sample                    
            else:
                 print "-I- sample %s FAIL on sample_int_sigma_uT or sample_int_sigma_perc"%sample
                 
    #--------------------------------------------------------------
    # calcuate 'bootstrap means' and write results to files
    #--------------------------------------------------------------

    
##        # collect all the acceptable grade A specimens and sort them to a matrix
##        if DO_SAMPLE_PARA_BOOTSTRP_MEAN or DO_SAMPLE_PARA_BOOTSTRP_MEAN: 
##           grade_A_collection_matrix=[] 
##           if len(Grade_A_samples[sample].keys())>=accept_new_parameters['sample_int_n']:
##               for specimen in Grade_A_samples[sample].keys():
##                   grade_A_collection_matrix.append([specimen],[])
##                   for B in Grade_A_samples[sample][specimen]:
##                       grade_A_collection_matrix[-1][1].append(B)
##                   grade_A_collection_matrix[-1][1].sort
##                   if max(grade_A_collection_matrix[-1][1])/min(grade_A_collection_matrix[-1][1])>float(accept_new_parameters["specimen_max_ratio_4_BS"]):
##                       grade_A_collection_matrix.pop()
##            
##           if len(grade_A_collection_matrix)>==accept_new_parameters['sample_int_n']:
##               Monte_Carlo_collection=[]
##               for i in range(BOOTSTRAP_N):
##                   specimen_B_collection=random.choice(grade_A_collection_matrix)
##                   if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
##                       Monte_Carlo_collection.append(random.choice(specimen_B_collection))
##                   else:
##                       Monte_Carlo_collection.append(random.uniform(min(specimen_B_collection),max(specimen_B_collection)))
##               Monte_Carlo
##                       
##                   
##                   
##                   
##               
##           
##               
##              specimens_in_list=Grade_A_samples[sample].keys()
####              for specimen in specimens_in_list:
####                  if Grade_A_samples[sample][specimen]["specimen_max_ratio_4_BS"]>float(accept_new_parameters["specimen_max_ratio_4_BS"]):
####                      specimens_in_list.remove(specimen)
##              if len(specimens_in_list)<accept_new_parameters['sample_int_n']:
##                  continue
##               
##              for specimen in  specimens_in_list:
##                  if specimen==exclude_specimen:
##                      continue
##                  for rec in All_grade_A_Recs[specimen]:
##                      Fout_BS_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t"\
##                                              %(sample,specimen,rec['specimen_int_uT'],float(rec['measurement_step_min'])-273,float(rec['measurement_step_max'])-273,float(rec['specimen_lab_field_dc']),float(rec["AC_specimen_correction_factor"]),float(rec["NLT_specimen_correction_factor"])))
##                      String=""
##                      for key in accept_specimen_keys:
##                          String=String+"%.2f"%(rec[key])+"\t"
##                      Fout_BS_specimens.write(String[:-1]+"\n")
##
##                      Fout_BS_redo.write("%s\t%i\t%i\n"%(specimen,int(rec['measurement_step_max']),int(rec['measurement_step_max'])))
##
##              
##              BS_means=[]
##              #specimens_in_list=Grade_A_samples[sample].keys()
##              for i in range(BOOTSTRAP_N):
##                 pseudo_sample_mean=[]
##                 for j in range(len(specimens_in_list)):
##                    #specimen=specimens_in_list[random.randint(0,len(specimens_in_list)-1)]
##                    specimen=random.choice(specimens_in_list)
##                    #index=random.randint(0,len(Grade_A_samples[sample][specimen])-1)
##                    #pseudo_sample_mean.append(Grade_A_samples[sample][specimen][index])
##                    pseudo_sample_mean.append(random.choice(Grade_A_samples[sample][specimen]))
##                 BS_means.append(mean(pseudo_sample_mean))
##              BS_means=array(BS_means)
##              BS_means.sort()
##              sample_median=median(BS_means)
##              sample_std=std(BS_means)
##              sample_68=[BS_means[(0.16)*len(BS_means)],BS_means[(0.84)*len(BS_means)]]
##              sample_95=[BS_means[(0.025)*len(BS_means)],BS_means[(0.975)*len(BS_means)]]
##
##
##              print "-I- simple bootstrap mean sample %s: median=%f, std=%f"%(sample,sample_median,sample_std)              
##              Fout_BS_samples.write("%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n"%\
##                                        (sample,len(Grade_A_samples[sample].keys()),sample_median,sample_68[0],sample_68[1],sample_95[0],sample_95[1],sample_std,100*(sample_std/sample_median),WARNING))
##                                    
##
##    #--------------------------------------------------------------
##    # calcuate 'bootstrap means' and write results to files
##    #--------------------------------------------------------------
##
##           if len(Grade_A_samples[sample].keys())>=accept_new_parameters['sample_int_n']:
##              specimens_in_list=Grade_A_samples[sample].keys()
##
##              for specimen in  specimens_in_list:
##
##                  if specimen==exclude_specimen:
##                      continue
##                  for rec in All_grade_A_Recs[specimen]:
##                      if min(Grade_A_samples[sample][specimen])==rec['specimen_int_uT'] or max(Grade_A_samples[sample][specimen])==rec['specimen_int_uT']:
##                          Fout_BS_PAR_specimens.write("%s\t%s\t%.2f\t%i\t%i\t%.0f\t%s\t%s\t"\
##                                                       %(sample,specimen,rec['specimen_int_uT'],float(rec['measurement_step_min'])-273,float(rec['measurement_step_max'])-273,float(rec['specimen_lab_field_dc']),float(rec["AC_specimen_correction_factor"]),float(rec["NLT_specimen_correction_factor"])))
##                                                                                              
##                          String=""
##                          for key in accept_specimen_keys:
##                              String=String+"%.2f"%(rec[key])+"\t"
##                          Fout_BS_PAR_specimens.write(String[:-1]+"\n")
##
##                          Fout_BS_PAR_redo.write("%s\t%i\t%i\n"%(specimen,int(rec['measurement_step_max']),int(rec['measurement_step_max'])))
##                                                                                              
##
##              
##              BS_PARA_means=[]
##              for i in range(BOOTSTRAP_N):
##                 pseudo_sample_mean=[]
##                 for j in range(len(specimens_in_list)):
##                    specimen=random.choice(specimens_in_list)
##                    pseudo_sample_mean.append(random.uniform(min(Grade_A_samples[sample][specimen]),max(Grade_A_samples[sample][specimen])))
##                 BS_PARA_means.append(mean(pseudo_sample_mean))
##              BS_PARA_means=array(BS_PARA_means)
##              BS_PARA_means.sort()
##              sample_median=median(BS_PARA_means)
##              sample_std=std(BS_PARA_means)
##              sample_68=[BS_PARA_means[(0.16)*len(BS_PARA_means)],BS_PARA_means[(0.84)*len(BS_PARA_means)]]
##              sample_95=[BS_PARA_means[(0.025)*len(BS_PARA_means)],BS_PARA_means[(0.975)*len(BS_PARA_means)]]
##
##              print "-I- parametric bootstrap mean sample %s: median=%f, std=%f"%(sample,sample_median,sample_std)              
##              Fout_BS_PAR_samples.write("%s\t%i\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%.1f\t%s\n"%\
##                                        (sample,len(Grade_A_samples[sample].keys()),sample_median,sample_68[0],sample_68[1],sample_95[0],sample_95[1],sample_std,100*(sample_std/sample_median),WARNING))
##                                   
##
##




    print "-I- runtime  for mean calculation:", time.time() - runtime_start_means, " seconds"
    # close all files

    All_acceptable_spec_interpretation_outfile.close()
    Fout_specimens_bounds.close()

    if DO_SAMPLE_BEST_MEAN:
       Fout_STDEV_OPT_redo.close()
       Fout_STDEV_OPT_specimens.close()
       Fout_STDEV_OPT_samples.close()

       
    if DO_SAMPLE_BOOTSTRP_MEAN:
       #Fout_BS_redo.close()
       #Fout_BS_specimens.close()
       Fout_BS_samples.close()

    if DO_SAMPLE_PARA_BOOTSTRP_MEAN:
       #Fout_BS_PAR_redo.close()
       #Fout_BS_PAR_specimens.close()
       Fout_BS_PAR_samples.close()

    #All_acceptable_spec_interpretation_outfile.close()
    #Fout_specimens_bounds.close()

    #Fout_samples.close()
    #Fout_specimens.close()
    print "-I- Statistics:"
    print "-I- number of specimens analzyed = %i" % specimens_counter    
    print "-I- number of sucsessful 'acceptable' specimens = %i" % len(All_grade_A_Recs.keys())    

    runtime_sec = time.time() - start_time
    m, s = divmod(runtime_sec, 60)
    h, m = divmod(m, 60)
    print "-I- runtime hh:mm:ss is " + "%d:%02d:%02d" % (h, m, s)
    print "-I- Finished sucsessfuly."
    print "-I- DONE"

        
        

                



main()
