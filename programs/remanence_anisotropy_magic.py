#!/usr/bin/env python

#import matplotlib

from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div
import sys
import pylab
from pylab import *
import scipy
import os
import pmagpy.pmag as pmag

def main():
    """
    NAME
        remanence_aniso_magic.py

    DESCRIPTION
        This program is similar to aarm_magic.py and atrm_magic.py with minor modifications.

        Converts magic measurement file with ATRM/AARM data to best-fit tensor (6 elements plus sigma)
        following Hext (1963), and calculates F-test statistics.
        
        Comments:
        - infield steps are marked with method codes LT-T-I:LP-AN-TRM; LT-AF-I:LP-AN-ARM
        - zerofield steps are marked with method codes LT-T-Z:LP-AN-TRM; LT-AF-Z:LP-AN-ARM
        - alteration check is marked with method codes LT-PTRM-I:LP-AN-TRM
        please notice;
        - ATRM: The program uses treatment_dc_field_phi/treatment_dc_field_theta columns to infer the direction of the applied field
                 (this is a change from atrm_magic.py)
        - ATRM: zerofield (baseline) magnetization is subtructed from all infield measurements
        - AARM: The program uses measurement number (running number) to to infer the direction of the applied field
                assuming the SIO protocol for 6,9,15 measurements scheme.
                See cookbook for diagram and details.
        - AARM: zerofield (baseline) are assumed to be before any infield, and the baseline is subtructed from the 
                subsequent infield magnetization.
      
    SYNTAX 
        remanence_aniso_magic.py [-h] [command line options]

    OPTIONS
        -h prints help message and quits
        -f FILE: specify input file, default is magic_measurements.txt

    INPUT  
        magic measurement file with ATRM and/or AARM data.
        if both types of measurements exist then the program calculates both.
        
    OUTPUT  
        rmag_anisotropy.log
                -I- information
                -W- Warning
                -E- Error
        rmag_anistropy.txt:
            This file contains in addition to some some magic information the following:
                - anistropy tensor s1 to s6 normalized by the trace:
                    |Mx|   |s1 s4 s6|   |Bx|
                    |My| = |s4 s2 s5| . |By|
                    |Mz|   |s6 s5 s3|   |Bz|
                - anisotropy_sigma (Hext, 1963)
                - anisotropy_alt (altertion check for ATRM in units of %):
                    100* [abs(M_first-Mlast)/max(M_first,M_last)]
                -                     
        rmag_results.txt:
            This file contains in addition to some  magic information the follow(ing:
                - anisotropy_t1,anisotropy_t2,anisotropy_t3 : eigenvalues
                - anisotropy_v*_dec,anisotropy_v*_inc: declination/inclination of the eigenvectors
                - anisotropy_ftest,anisotropy_ftest12,anisotropy_ftest13 
                - (the crtical F for 95% confidence level of anistropy is given in result_description column).
                
                
    """


    #==================================================================================
    
    meas_file="magic_measurements.txt"
    args=sys.argv
    dir_path='.'
    #
    # get name of file from command line
    #
    if '-WD' in args:
        ind=args.index('-WD')
        dir_path=args[ind+1]
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if "-f" in args:
        ind=args.index("-f")
        meas_file=sys.argv[ind+1]
    else:
        meas_file=dir_path+'/'+meas_file
    WD=dir_path

    
    #======================================
    # functions
    #======================================

    def get_Data(magic_file):
    
        #------------------------------------------------
        # Read magic measurement file and sort to blocks
        #------------------------------------------------
        Data={}
        try:
            meas_data,file_type=pmag.magic_read(magic_file)
        except:
            print("-E- ERROR: Cant read magic_measurement.txt file. File is corrupted.")
            return Data
            
        # get list of unique specimen names
        
        #sids=pmag.get_specs(meas_data) # samples ID's
        
        for rec in meas_data:
            s=rec["er_specimen_name"]
            method_codes= rec["magic_method_codes"].strip('\n')
            method_codes.replace(" ","")
            methods=method_codes.split(":")
            if "LP-AN-TRM" in methods:
                if s not in list(Data.keys()):
                    Data[s]={}
                if 'atrmblock' not in list(Data[s].keys()):
                    Data[s]['atrmblock']=[]
                Data[s]['atrmblock'].append(rec)
            
            
            if "LP-AN-ARM" in methods:
                if s not in list(Data.keys()):
                    Data[s]={}
                if 'aarmblock' not in list(Data[s].keys()):
                    Data[s]['aarmblock']=[]
                Data[s]['aarmblock'].append(rec)
        return (Data)        

    #======================================
    # better to put this one in pmagpy
    #======================================
        
    def calculate_aniso_parameters(B,K):
    
        aniso_parameters={}
        S_bs=dot(B,K)
        
        # normalize by trace
        trace=S_bs[0]+S_bs[1]+S_bs[2]
        S_bs=old_div(S_bs,trace)
        s1,s2,s3,s4,s5,s6=S_bs[0],S_bs[1],S_bs[2],S_bs[3],S_bs[4],S_bs[5]
        s_matrix=[[s1,s4,s6],[s4,s2,s5],[s6,s5,s3]]
        
        # calculate eigen vector,
        t,evectors=eig(s_matrix)
        # sort vectors
        t=list(t)
        t1=max(t)
        ix_1=t.index(t1)
        t3=min(t)
        ix_3=t.index(t3)
        for tt in range(3):
            if t[tt]!=t1 and t[tt]!=t3:
                t2=t[tt]
                ix_2=t.index(t2)
                
        v1=[evectors[0][ix_1],evectors[1][ix_1],evectors[2][ix_1]]
        v2=[evectors[0][ix_2],evectors[1][ix_2],evectors[2][ix_2]]
        v3=[evectors[0][ix_3],evectors[1][ix_3],evectors[2][ix_3]]
    
    
        DIR_v1=pmag.cart2dir(v1)
        DIR_v2=pmag.cart2dir(v2)
        DIR_v3=pmag.cart2dir(v3)
    
                            
        aniso_parameters['anisotropy_s1']="%f"%s1
        aniso_parameters['anisotropy_s2']="%f"%s2
        aniso_parameters['anisotropy_s3']="%f"%s3
        aniso_parameters['anisotropy_s4']="%f"%s4
        aniso_parameters['anisotropy_s5']="%f"%s5
        aniso_parameters['anisotropy_s6']="%f"%s6
        aniso_parameters['anisotropy_degree']="%f"%(old_div(t1,t3))
        aniso_parameters['anisotropy_t1']="%f"%t1
        aniso_parameters['anisotropy_t2']="%f"%t2
        aniso_parameters['anisotropy_t3']="%f"%t3
        aniso_parameters['anisotropy_v1_dec']="%.1f"%DIR_v1[0]
        aniso_parameters['anisotropy_v1_inc']="%.1f"%DIR_v1[1]
        aniso_parameters['anisotropy_v2_dec']="%.1f"%DIR_v2[0]
        aniso_parameters['anisotropy_v2_inc']="%.1f"%DIR_v2[1]
        aniso_parameters['anisotropy_v3_dec']="%.1f"%DIR_v3[0]
        aniso_parameters['anisotropy_v3_inc']="%.1f"%DIR_v3[1]
    
        # modified from pmagpy:
        if old_div(len(K),3)==9 or old_div(len(K),3)==6 or old_div(len(K),3)==15:
            n_pos=old_div(len(K),3)
            tmpH = Matrices[n_pos]['tmpH']
            a=s_matrix
            S=0.
            comp=zeros((n_pos*3),'f')
            for i in range(n_pos):
                for j in range(3):
                    index=i*3+j
                    compare=a[j][0]*tmpH[i][0]+a[j][1]*tmpH[i][1]+a[j][2]*tmpH[i][2]
                    comp[index]=compare
            for i in range(n_pos*3):
                d=old_div(K[i],trace) - comp[i] # del values
                S+=d*d
            nf=float(n_pos*3-6) # number of degrees of freedom
            if S >0: 
                sigma=math.sqrt(old_div(S,nf))
            hpars=pmag.dohext(nf,sigma,[s1,s2,s3,s4,s5,s6])
            
            aniso_parameters['anisotropy_sigma']="%f"%sigma
            aniso_parameters['anisotropy_ftest']="%f"%hpars["F"]
            aniso_parameters['anisotropy_ftest12']="%f"%hpars["F12"]
            aniso_parameters['anisotropy_ftest23']="%f"%hpars["F23"]
            aniso_parameters['result_description']="Critical F: %s"%(hpars['F_crit'])
            aniso_parameters['anisotropy_F_crit']="%f"%float(hpars['F_crit'])
            aniso_parameters['anisotropy_n']=n_pos
            
        return(aniso_parameters)
    
    
    #======================================
    # Main
    #======================================
          
    
        
    aniso_logfile=open(WD+"/rmag_anisotropy.log",'w')
    aniso_logfile.write("------------------------\n")
    aniso_logfile.write( "-I- Start rmag anisrotropy script\n")
    aniso_logfile.write( "------------------------\n")

    Data=get_Data(meas_file)
    #try:    
    #    Data=get_Data(meas_file)
    #except:
    #    aniso_logfile.write( "-E- Cant open measurement file %s\n" %meas_file)
    #    print "-E- Cant open measurement file %s\n exiting" %meas_file
    #    exit()
        
    aniso_logfile.write( "-I-  Open measurement file %s\n" %meas_file)
    
        
    Data_anisotropy={}                
    specimens=list(Data.keys())
    specimens.sort()
    
    
    
    #-----------------------------------
    # Prepare rmag_anisotropy.txt file for writing
    #-----------------------------------
    
    rmag_anisotropy_file =open(WD+"/rmag_anisotropy.txt",'w')
    rmag_anisotropy_file.write("tab\trmag_anisotropy\n")
    
    rmag_results_file =open(WD+"/rmag_results.txt",'w')
    rmag_results_file.write("tab\trmag_results\n")
    
    rmag_anistropy_header=['er_specimen_name','er_sample_name','er_site_name','anisotropy_type','anisotropy_n','anisotropy_description','anisotropy_s1','anisotropy_s2','anisotropy_s3','anisotropy_s4','anisotropy_s5','anisotropy_s6','anisotropy_sigma','anisotropy_alt','magic_experiment_names','magic_method_codes']
    
    String=""
    for i in range (len(rmag_anistropy_header)):
        String=String+rmag_anistropy_header[i]+'\t'
    rmag_anisotropy_file.write(String[:-1]+"\n")
    
    
    
    rmag_results_header=['er_specimen_names','er_sample_names','er_site_names','anisotropy_type','magic_method_codes','magic_experiment_names','result_description','anisotropy_t1','anisotropy_t2','anisotropy_t3','anisotropy_ftest','anisotropy_ftest12','anisotropy_ftest23',\
                            'anisotropy_v1_dec','anisotropy_v1_inc','anisotropy_v2_dec','anisotropy_v2_inc','anisotropy_v3_dec','anisotropy_v3_inc']
    
    
    String=""
    for i in range (len(rmag_results_header)):
        String=String+rmag_results_header[i]+'\t'
    rmag_results_file.write(String[:-1]+"\n")
    
    #-----------------------------------
    # Matrices definitions:
    # A design matrix
    # B dot(inv(dot(A.transpose(),A)),A.transpose())
    # tmpH is used for sigma calculation (9,15 measurements only)
    # 
    #  Anisotropy tensor:
    #
    # |Mx|   |s1 s4 s6|   |Bx|
    # |My| = |s4 s2 s5| . |By|
    # |Mz|   |s6 s5 s3|   |Bz|
    #
    # A matrix (measurement matrix):
    # Each mesurement yields three lines in "A" matrix
    #
    # |Mi  |   |Bx 0  0   By  0   Bz|   |s1|
    # |Mi+1| = |0  By 0   Bx  Bz  0 | . |s2|
    # |Mi+2|   |0  0  Bz  0   By  Bx|   |s3|
    #                                   |s4|
    #                                   |s5|
    #
    #-----------------------------------
    
    Matrices={}
    
    for n_pos in [6,9,15]:
    
        Matrices[n_pos]={}
        
        A=zeros((n_pos*3,6),'f')
    
        if n_pos==6:
            positions=[[0.,0.,1.],[90.,0.,1.],[0.,90.,1.],\
                    [180.,0.,1.],[270.,0.,1.],[0.,-90.,1.]]
    
        if n_pos==15:
            positions=[[315.,0.,1.],[225.,0.,1.],[180.,0.,1.],[135.,0.,1.],[45.,0.,1.],\
                    [90.,-45.,1.],[270.,-45.,1.],[270.,0.,1.],[270.,45.,1.],[90.,45.,1.],\
                    [180.,45.,1.],[180.,-45.,1.],[0.,-90.,1.],[0,-45.,1.],[0,45.,1.]]
        if n_pos==9:
            positions=[[315.,0.,1.],[225.,0.,1.],[180.,0.,1.],\
                    [90.,-45.,1.],[270.,-45.,1.],[270.,0.,1.],\
                    [180.,45.,1.],[180.,-45.,1.],[0.,-90.,1.]]
    
        
        tmpH=zeros((n_pos,3),'f') # define tmpH
        for i in range(len(positions)):
            CART=pmag.dir2cart(positions[i])
            a=CART[0];b=CART[1];c=CART[2]
            A[3*i][0]=a
            A[3*i][3]=b
            A[3*i][5]=c
    
            A[3*i+1][1]=b
            A[3*i+1][3]=a
            A[3*i+1][4]=c
    
            A[3*i+2][2]=c
            A[3*i+2][4]=b
            A[3*i+2][5]=a
            
            tmpH[i][0]=CART[0]
            tmpH[i][1]=CART[1]
            tmpH[i][2]=CART[2]
    
        B=dot(inv(dot(A.transpose(),A)),A.transpose())
    
        Matrices[n_pos]['A']=A
        Matrices[n_pos]['B']=B
        Matrices[n_pos]['tmpH']=tmpH
    
    
    
    
    
    for specimen in specimens:
    
        if 'atrmblock' in list(Data[specimen].keys()):
            
            #-----------------------------------
            # aTRM 6 positions
            #-----------------------------------
                
            aniso_logfile.write("-I- Start calculating ATRM tensor for specimen %s\n "%specimen)
            atrmblock=Data[specimen]['atrmblock']
            if len(atrmblock)<6:
                aniso_logfile.write("-W- specimen %s has not enough measurementf for ATRM calculation\n"%specimen)
                continue
            
            B=Matrices[6]['B']
                                
            Reject_specimen = False
    
            # The zero field step is a "baseline"
    
            # Search the baseline in the ATRM measurement
            
            baseline=""
            Alteration_check=""
            Alteration_check_index=""
            baselines=[]
    
            # search for baseline in atrm blocks
            for rec in atrmblock:
                dec=float(rec['measurement_dec'])
                inc=float(rec['measurement_inc'])
                moment=float(rec['measurement_magn_moment'])
                # find the temperature of the atrm
                if float(rec['treatment_dc_field'])!=0 and float(rec['treatment_temp'])!=273:
                    atrm_temperature=float(rec['treatment_temp'])
                # find baseline
                if float(rec['treatment_dc_field'])==0 and float(rec['treatment_temp'])!=273:
                    baselines.append(array(pmag.dir2cart([dec,inc,moment])))
                # Find alteration check
                #print rec['measurement_number']
            
            if len(baselines)!=0:
                aniso_logfile.write( "-I- found ATRM baseline for specimen %s\n"%specimen)
                baselines=array(baselines)
                baseline=array([mean(baselines[:,0]),mean(baselines[:,1]),mean(baselines[:,2])])                                 
                
            else:
                baseline=zeros(3,'f')
                aniso_logfile.write( "-I- No aTRM baseline for specimen %s\n"%specimen)
                        
            # sort measurements
            
            M=zeros([6,3],'f')
            
            for rec in atrmblock:
    
                dec=float(rec['measurement_dec'])
                inc=float(rec['measurement_inc'])
                moment=float(rec['measurement_magn_moment'])
                CART=array(pmag.dir2cart([dec,inc,moment]))-baseline
                
                if float(rec['treatment_dc_field'])==0: # Ignore zero field steps
                    continue
                if  "LT-PTRM-I" in rec['magic_method_codes'].split(":"): #  alteration check
                    Alteration_check=CART
                    Alteration_check_dc_field_phi=float(rec['treatment_dc_field_phi'])
                    Alteration_check_dc_field_theta=float(rec['treatment_dc_field_theta'])
                    if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==0 :
                        Alteration_check_index=0
                    if Alteration_check_dc_field_phi==90 and Alteration_check_dc_field_theta==0 :
                        Alteration_check_index=1
                    if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==90 :
                        Alteration_check_index=2
                    if Alteration_check_dc_field_phi==180 and Alteration_check_dc_field_theta==0 :
                        Alteration_check_index=3
                    if Alteration_check_dc_field_phi==270 and Alteration_check_dc_field_theta==0 :
                        Alteration_check_index=4
                    if Alteration_check_dc_field_phi==0 and Alteration_check_dc_field_theta==-90 :
                        Alteration_check_index=5
                    aniso_logfile.write(  "-I- found alteration check  for specimen %s\n"%specimen)
                    continue
                
                treatment_dc_field_phi=float(rec['treatment_dc_field_phi'])
                treatment_dc_field_theta=float(rec['treatment_dc_field_theta'])
                treatment_dc_field=float(rec['treatment_dc_field'])
                
                #+x, M[0]
                if treatment_dc_field_phi==0 and treatment_dc_field_theta==0 :
                    M[0]=CART
                #+Y , M[1]
                if treatment_dc_field_phi==90 and treatment_dc_field_theta==0 :
                    M[1]=CART
                #+Z , M[2]
                if treatment_dc_field_phi==0 and treatment_dc_field_theta==90 :
                    M[2]=CART
                #-x, M[3]
                if treatment_dc_field_phi==180 and treatment_dc_field_theta==0 :
                    M[3]=CART
                #-Y , M[4]
                if treatment_dc_field_phi==270 and treatment_dc_field_theta==0 :
                    M[4]=CART
                #-Z , M[5]
                if treatment_dc_field_phi==0 and treatment_dc_field_theta==-90 :
                    M[5]=CART
        
            # check if at least one measurement in missing
            for i in range(len(M)):
                if M[i][0]==0 and M[i][1]==0 and M[i][2]==0: 
                    aniso_logfile.write( "-E- ERROR: missing atrm data for specimen %s\n"%(specimen))
                    Reject_specimen=True
    
            # alteration check        
    
            anisotropy_alt=0
            if Alteration_check!="":
                for i in range(len(M)):
                    if Alteration_check_index==i:
                        M_1=sqrt(sum((array(M[i])**2)))
                        M_2=sqrt(sum(Alteration_check**2))
                        diff=abs(M_1-M_2)
                        diff_ratio=old_div(diff,mean([M_1,M_2]))
                        diff_ratio_perc=100*diff_ratio
                        if diff_ratio_perc > anisotropy_alt:
                            anisotropy_alt=diff_ratio_perc
            else:
                aniso_logfile.write( "-W- Warning: no alteration check for specimen %s \n "%specimen )
    
            # Check for maximum difference in anti parallel directions.
            # if the difference between the two measurements is more than maximum_diff
            # The specimen is rejected
            
            # i.e. +x versus -x, +y versus -y, etc.s
    
            for i in range(3):
                M_1=sqrt(sum(array(M[i])**2))
                M_2=sqrt(sum(array(M[i+3])**2))
                
                diff=abs(M_1-M_2)
                diff_ratio=old_div(diff,max(M_1,M_2))
                diff_ratio_perc=100*diff_ratio
                
                if diff_ratio_perc>anisotropy_alt:
                    anisotropy_alt=diff_ratio_perc
                    
            if not Reject_specimen:
            
                # K vector (18 elements, M1[x], M1[y], M1[z], ... etc.) 
                K=zeros(18,'f')
                K[0],K[1],K[2]=M[0][0],M[0][1],M[0][2]
                K[3],K[4],K[5]=M[1][0],M[1][1],M[1][2]
                K[6],K[7],K[8]=M[2][0],M[2][1],M[2][2]
                K[9],K[10],K[11]=M[3][0],M[3][1],M[3][2]
                K[12],K[13],K[14]=M[4][0],M[4][1],M[4][2]
                K[15],K[16],K[17]=M[5][0],M[5][1],M[5][2]
    
                if specimen not in list(Data_anisotropy.keys()):
                    Data_anisotropy[specimen]={}
                aniso_parameters=calculate_aniso_parameters(B,K)
                Data_anisotropy[specimen]['ATRM']=aniso_parameters
                Data_anisotropy[specimen]['ATRM']['anisotropy_alt']="%.2f"%anisotropy_alt               
                Data_anisotropy[specimen]['ATRM']['anisotropy_type']="ATRM"
                Data_anisotropy[specimen]['ATRM']['er_sample_name']=atrmblock[0]['er_sample_name']
                Data_anisotropy[specimen]['ATRM']['er_specimen_name']=specimen
                Data_anisotropy[specimen]['ATRM']['er_site_name']=atrmblock[0]['er_site_name']
                Data_anisotropy[specimen]['ATRM']['anisotropy_description']='Hext statistics adapted to ATRM'
                Data_anisotropy[specimen]['ATRM']['magic_experiment_names']=specimen+";ATRM"
                Data_anisotropy[specimen]['ATRM']['magic_method_codes']="LP-AN-TRM:AE-H"
                #Data_anisotropy[specimen]['ATRM']['rmag_anisotropy_name']=specimen
    
    
        if 'aarmblock' in list(Data[specimen].keys()):    
    
            #-----------------------------------
            # AARM - 6, 9 or 15 positions
            #-----------------------------------
                
            aniso_logfile.write( "-I- Start calculating AARM tensors specimen %s\n"%specimen)
    
            aarmblock=Data[specimen]['aarmblock']
            if len(aarmblock)<12:
                aniso_logfile.write( "-W- WARNING: not enough aarm measurement for specimen %s\n"%specimen)
                continue
            elif len(aarmblock)==12:
                n_pos=6
                B=Matrices[6]['B']
                M=zeros([6,3],'f')
            elif len(aarmblock)==18:
                n_pos=9
                B=Matrices[9]['B']
                M=zeros([9,3],'f')
            # 15 positions
            elif len(aarmblock)==30:
                n_pos=15
                B=Matrices[15]['B']
                M=zeros([15,3],'f')
            else:
                aniso_logfile.write( "-E- ERROR: number of measurements in aarm block is incorrect sample %s\n"%specimen)
                continue
                
            Reject_specimen = False
    
            for i in range(n_pos):
                for rec in aarmblock:
                    if float(rec['measurement_number'])==i*2+1:
                        dec=float(rec['measurement_dec'])
                        inc=float(rec['measurement_inc'])
                        moment=float(rec['measurement_magn_moment'])                    
                        M_baseline=array(pmag.dir2cart([dec,inc,moment]))
                        
                    if float(rec['measurement_number'])==i*2+2:
                        dec=float(rec['measurement_dec'])
                        inc=float(rec['measurement_inc'])
                        moment=float(rec['measurement_magn_moment'])                    
                        M_arm=array(pmag.dir2cart([dec,inc,moment]))
                M[i]=M_arm-M_baseline
    
                
            K=zeros(3*n_pos,'f')
            for i in range(n_pos):
                K[i*3]=M[i][0]
                K[i*3+1]=M[i][1]
                K[i*3+2]=M[i][2]            
    
            if specimen not in list(Data_anisotropy.keys()):
                Data_anisotropy[specimen]={}
            aniso_parameters=calculate_aniso_parameters(B,K)
            Data_anisotropy[specimen]['AARM']=aniso_parameters
            Data_anisotropy[specimen]['AARM']['anisotropy_alt']=""               
            Data_anisotropy[specimen]['AARM']['anisotropy_type']="AARM"
            Data_anisotropy[specimen]['AARM']['er_sample_name']=aarmblock[0]['er_sample_name']
            Data_anisotropy[specimen]['AARM']['er_site_name']=aarmblock[0]['er_site_name']
            Data_anisotropy[specimen]['AARM']['er_specimen_name']=specimen
            Data_anisotropy[specimen]['AARM']['anisotropy_description']='Hext statistics adapted to AARM'
            Data_anisotropy[specimen]['AARM']['magic_experiment_names']=specimen+";AARM"
            Data_anisotropy[specimen]['AARM']['magic_method_codes']="LP-AN-ARM:AE-H"
            #Data_anisotropy[specimen]['AARM']['rmag_anisotropy_name']=specimen
            
    
    #-----------------------------------   
    
    specimens=list(Data_anisotropy.keys())
    specimens.sort
    
    # remove previous anistropy data, and replace with the new one:
    s_list=list(Data.keys())
    for sp in s_list:
        if 'AniSpec' in list(Data[sp].keys()):
            del  Data[sp]['AniSpec']
    for specimen in specimens:
        # if both AARM and ATRM axist prefer the AARM !!
        if 'AARM' in list(Data_anisotropy[specimen].keys()):
            TYPES=['AARM']
        if 'ATRM' in list(Data_anisotropy[specimen].keys()):
            TYPES=['ATRM']
        if  'AARM' in list(Data_anisotropy[specimen].keys()) and 'ATRM' in list(Data_anisotropy[specimen].keys()):
            TYPES=['ATRM','AARM']
            aniso_logfile.write( "-W- WARNING: both aarm and atrm data exist for specimen %s. using AARM by default. If you prefer using one of them, delete the other!\n"%specimen)
        for TYPE in TYPES:
            String=""
            for i in range (len(rmag_anistropy_header)):
                try:
                    String=String+Data_anisotropy[specimen][TYPE][rmag_anistropy_header[i]]+'\t'
                except:
                    String=String+"%f"%(Data_anisotropy[specimen][TYPE][rmag_anistropy_header[i]])+'\t'
            rmag_anisotropy_file.write(String[:-1]+"\n")
    
            String=""
            Data_anisotropy[specimen][TYPE]['er_specimen_names']=Data_anisotropy[specimen][TYPE]['er_specimen_name']
            Data_anisotropy[specimen][TYPE]['er_sample_names']=Data_anisotropy[specimen][TYPE]['er_sample_name']
            Data_anisotropy[specimen][TYPE]['er_site_names']=Data_anisotropy[specimen][TYPE]['er_site_name']
            for i in range (len(rmag_results_header)):
                try:
                    String=String+Data_anisotropy[specimen][TYPE][rmag_results_header[i]]+'\t'
                except:
                    String=String+"%f"%(Data_anisotropy[specimen][TYPE][rmag_results_header[i]])+'\t'
            rmag_results_file.write(String[:-1]+"\n")
    
            if 'AniSpec' not in Data[specimen]:
                Data[specimen]['AniSpec']={}
            Data[specimen]['AniSpec'][TYPE]=Data_anisotropy[specimen][TYPE]
    
    aniso_logfile.write("------------------------\n")
    aniso_logfile.write("-I-  remanence_aniso_magic script finished sucsessfuly\n")
    aniso_logfile.write( "------------------------\n")
    
    rmag_anisotropy_file.close()
    print("Anisotropy tensors elements are saved in rmag_anistropy.txt")
    print("Other anisotropy statistics are saved in rmag_results.txt")
    print("log file is  in rmag_anisotropy.log")


if __name__ == "__main__":    
    main()
