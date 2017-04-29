#!/usr/bin/env python

#---------------------------------------------------------------------------
# Author: Ron Shaar
# Revision notes
#
# Rev 1.0 Initial revision August 2012
# Rev 2.0 November 2014
#---------------------------------------------------------------------------
import matplotlib
import pylab,scipy
from pylab import *
from scipy import *
#import pmag
import copy
import pmagpy.pmag as pmag

def get_PI_parameters(Data, acceptance_criteria, preferences, s, tmin, tmax, GUI_log, THERMAL,MICROWAVE):
    datablock = Data[s]['datablock']
    pars=copy.deepcopy(Data[s]['pars']) # assignments to pars are assiging to Data[s]['pars']
    import SPD
    import SPD.spd as spd
    Pint_pars = spd.PintPars(Data, str(s), tmin, tmax, 'magic', preferences['show_statistics_on_gui'],acceptance_criteria)
    Pint_pars.reqd_stats() # calculate only statistics indicated in preferences
    if not Pint_pars.pars:
        print("Could not get any parameters for {}".format(Pint_pars))
        return 0
    pars.update(Pint_pars.pars)

    t_Arai=Data[s]['t_Arai']
    x_Arai=Data[s]['x_Arai']
    y_Arai=Data[s]['y_Arai']
    x_tail_check=Data[s]['x_tail_check']
    y_tail_check=Data[s]['y_tail_check']

    zijdblock=Data[s]['zijdblock']
    z_temperatures=Data[s]['z_temp']

    #print tmin,tmax,z_temperatures
    # check tmin
    if tmin not in t_Arai or tmin not in z_temperatures:
        return(pars)

    # check tmax
    if tmax not in t_Arai or tmin not in z_temperatures:
        return(pars)

    start=t_Arai.index(tmin)
    end=t_Arai.index(tmax)

    zstart=z_temperatures.index(tmin)
    zend=z_temperatures.index(tmax)

    zdata_segment=Data[s]['zdata'][zstart:zend+1]

    # replacing PCA for zdata and for ptrms here

## removed a bunch of Ron's commented out old code

    #-------------------------------------------------
    # York regresssion (York, 1967) following Coe (1978)
    # calculate f,fvds,
    # modified from pmag.py
    #-------------------------------------------------

    x_Arai_segment = x_Arai[start:end+1]
    y_Arai_segment = y_Arai[start:end+1]
    # replace thellier_gui code for york regression here

    pars["specimen_int"]=-1*pars['lab_dc_field']*pars["specimen_b"]

    # replace thellier_gui code for ptrm checks, DRAT etc. here
    # also tail checks and SCAT

    #-------------------------------------------------
    # Add missing parts of code from old get_PI
    #-------------------------------------------------

    if MICROWAVE==True:
        LP_code="LP-PI-M"
    else:
        LP_code="LP-PI-TRM"

    count_IZ = Data[s]['steps_Arai'].count('IZ')
    count_ZI = Data[s]['steps_Arai'].count('ZI')
    if count_IZ > 1 and count_ZI > 1:
        pars['magic_method_codes']=LP_code+":"+"LP-PI-BT-IZZI"
    elif count_IZ < 1 and count_ZI > 1:
        pars['magic_method_codes']=LP_code+":"+"LP-PI-ZI"
    elif count_IZ > 1 and count_ZI < 1:
        pars['magic_method_codes']=LP_code+":"+"LP-PI-IZ"
    else:
        pars['magic_method_codes']=LP_code

    if 'ptrm_checks_temperatures' in list(Data[s].keys()) and len(Data[s]['ptrm_checks_temperatures'])>0:
        if MICROWAVE==True:
            pars['magic_method_codes']+=":LP-PI-ALT-PMRM"
        else:
            pars['magic_method_codes']+=":LP-PI-ALT-PTRM"

    if 'tail_check_temperatures' in list(Data[s].keys()) and len(Data[s]['tail_check_temperatures'])>0:
        pars['magic_method_codes']+=":LP-PI-BT-MD"

    if 'additivity_check_temperatures' in list(Data[s].keys()) and len(Data[s]['additivity_check_temperatures'])>0:
        pars['magic_method_codes']+=":LP-PI-BT"

    #-------------------------------------------------
    # Calculate anisotropy correction factor
    #-------------------------------------------------

    if "AniSpec" in list(Data[s].keys()):
        pars["AC_WARNING"]=""
        # if both aarm and atrm tensor axist, try first the aarm. if it fails use the atrm.
        if 'AARM' in list(Data[s]["AniSpec"].keys()) and 'ATRM' in list(Data[s]["AniSpec"].keys()):
            TYPES=['AARM','ATRM']
        else:
            TYPES=list(Data[s]["AniSpec"].keys())
        for TYPE in TYPES:
            red_flag=False
            S_matrix=zeros((3,3),'f')
            S_matrix[0,0]=Data[s]['AniSpec'][TYPE]['anisotropy_s1']
            S_matrix[1,1]=Data[s]['AniSpec'][TYPE]['anisotropy_s2']
            S_matrix[2,2]=Data[s]['AniSpec'][TYPE]['anisotropy_s3']
            S_matrix[0,1]=Data[s]['AniSpec'][TYPE]['anisotropy_s4']
            S_matrix[1,0]=Data[s]['AniSpec'][TYPE]['anisotropy_s4']
            S_matrix[1,2]=Data[s]['AniSpec'][TYPE]['anisotropy_s5']
            S_matrix[2,1]=Data[s]['AniSpec'][TYPE]['anisotropy_s5']
            S_matrix[0,2]=Data[s]['AniSpec'][TYPE]['anisotropy_s6']
            S_matrix[2,0]=Data[s]['AniSpec'][TYPE]['anisotropy_s6']

            #Data[s]['AniSpec']['anisotropy_type']=Data[s]['AniSpec']['anisotropy_type']
            Data[s]['AniSpec'][TYPE]['anisotropy_n']=int(float(Data[s]['AniSpec'][TYPE]['anisotropy_n']))

            this_specimen_f_type=Data[s]['AniSpec'][TYPE]['anisotropy_type']+"_"+"%i"%(int(Data[s]['AniSpec'][TYPE]['anisotropy_n']))
            Ftest_crit={}
            Ftest_crit['ATRM_6']=  3.1059
            Ftest_crit['AARM_6']=  3.1059
            Ftest_crit['AARM_9']= 2.6848
            Ftest_crit['AARM_15']= 2.4558

            # threshold value for Ftest:

            if 'AniSpec' in list(Data[s].keys()) and TYPE in list(Data[s]['AniSpec'].keys())\
                and 'anisotropy_sigma' in  list(Data[s]['AniSpec'][TYPE].keys()) \
                and Data[s]['AniSpec'][TYPE]['anisotropy_sigma']!="":
                # Calculate Ftest. If Ftest exceeds threshold value: set anistropy tensor to identity matrix
                sigma=float(Data[s]['AniSpec'][TYPE]['anisotropy_sigma'])
                nf = 3*int(Data[s]['AniSpec'][TYPE]['anisotropy_n'])-6
                F=calculate_ftest(S_matrix,sigma,nf)
                #print s,"F",F
                Data[s]['AniSpec'][TYPE]['ftest']=F
                #print "s,sigma,nf,F,Ftest_crit[this_specimen_f_type]"
                #print s,sigma,nf,F,Ftest_crit[this_specimen_f_type]
                if acceptance_criteria['specimen_aniso_ftest_flag']['value'] in ['g','1',1,True,'TRUE','True'] :
                    Ftest_threshold=Ftest_crit[this_specimen_f_type]
                    if Data[s]['AniSpec'][TYPE]['ftest'] < Ftest_crit[this_specimen_f_type]:
                        S_matrix=identity(3,'f')
                        pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails F-test; "%(TYPE)
                        red_flag=True
            else:
                Data[s]['AniSpec'][TYPE]['anisotropy_sigma']=""
                Data[s]['AniSpec'][TYPE]['ftest']=99999

            if 'anisotropy_alt' in list(Data[s]['AniSpec'][TYPE].keys()) and Data[s]['AniSpec'][TYPE]['anisotropy_alt']!="":
                if acceptance_criteria['anisotropy_alt']['value'] != -999 and \
                (float(Data[s]['AniSpec'][TYPE]['anisotropy_alt']) > float(acceptance_criteria['anisotropy_alt']['value'])):
                    S_matrix=identity(3,'f')
                    pars["AC_WARNING"]=pars["AC_WARNING"]+"%s tensor fails alteration check: %.1f > %.1f; "%(TYPE,float(Data[s]['AniSpec'][TYPE]['anisotropy_alt']),float(acceptance_criteria['anisotropy_alt']['value']))
                    red_flag=True
            else:
                Data[s]['AniSpec'][TYPE]['anisotropy_alt']=""

            Data[s]['AniSpec'][TYPE]['S_matrix']=S_matrix
        #--------------------------
        # if AARM passes all, use the AARM.
        # if ATRM fail alteration use the AARM
        # if both fail F-test: use AARM
        #--------------------------

        if len(TYPES)>1:
            if "ATRM tensor fails alteration check" in pars["AC_WARNING"]:
                TYPE='AARM'
            elif "ATRM tensor fails F-test" in pars["AC_WARNING"]:
                TYPE='AARM'
            else:
                TYPE=='AARM'
        S_matrix= Data[s]['AniSpec'][TYPE]['S_matrix']

        #---------------------------

        TRM_anc_unit=array(pars['specimen_PCA_v1'])/sqrt(pars['specimen_PCA_v1'][0]**2+pars['specimen_PCA_v1'][1]**2+pars['specimen_PCA_v1'][2]**2)
        B_lab_unit=pmag.dir2cart([ Data[s]['Thellier_dc_field_phi'], Data[s]['Thellier_dc_field_theta'],1])
        #B_lab_unit=array([0,0,-1])
        Anisotropy_correction_factor=linalg.norm(dot(inv(S_matrix),TRM_anc_unit.transpose()))*norm(dot(S_matrix,B_lab_unit))
        pars["Anisotropy_correction_factor"]=Anisotropy_correction_factor
        pars["AC_specimen_int"]= pars["Anisotropy_correction_factor"] * float(pars["specimen_int"])

        pars["AC_anisotropy_type"]=Data[s]['AniSpec'][TYPE]["anisotropy_type"]
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

    if 'NLT_parameters' in list(Data[s].keys()):

        alpha=Data[s]['NLT_parameters']['tanh_parameters'][0][0]
        beta=Data[s]['NLT_parameters']['tanh_parameters'][0][1]
        b=float(pars["specimen_b"])
        Fa=pars["Anisotropy_correction_factor"]

        if ((abs(b)*Fa)/alpha) <1.0:
            Banc_NLT=math.atanh(((abs(b)*Fa)/alpha))/beta
            pars["NLTC_specimen_int"]=Banc_NLT
            pars["specimen_int_uT"]=Banc_NLT*1e6

            if "AC_specimen_int" in list(pars.keys()):
                pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["AC_specimen_int"])
            else:
                pars["NLT_specimen_correction_factor"]=Banc_NLT/float(pars["specimen_int"])
            if ":LP-TRM" not in pars['magic_method_codes']:
                pars['magic_method_codes']+=":LP-TRM:DA-NL"
            pars['specimen_correction']='c'

        else:
            GUI_log.write ("-W- WARNING: problematic NLT mesurements for specimens %s. Cant do NLT calculation. check data\n"%s)
            pars["NLT_specimen_correction_factor"]=-1
    else:
        pars["NLT_specimen_correction_factor"]=-1

    #-------------------------------------------------
    # Calculate the final result with cooling rate correction
    #-------------------------------------------------

    pars["specimen_int_corr_cooling_rate"]=-999
    if 'cooling_rate_data' in list(Data[s].keys()):
        if 'CR_correction_factor' in list(Data[s]['cooling_rate_data'].keys()):
            if Data[s]['cooling_rate_data']['CR_correction_factor'] != -1 and Data[s]['cooling_rate_data']['CR_correction_factor'] !=-999:
                pars["specimen_int_corr_cooling_rate"]=Data[s]['cooling_rate_data']['CR_correction_factor']
                pars['specimen_correction']='c'
                pars["specimen_int_uT"]=pars["specimen_int_uT"]*pars["specimen_int_corr_cooling_rate"]
                if ":DA-CR" not in pars['magic_method_codes']:
                    pars['magic_method_codes']+=":DA-CR"
                if   'CR_correction_factor_flag' in list(Data[s]['cooling_rate_data'].keys()):
                    if Data[s]['cooling_rate_data']['CR_correction_factor_flag']=="calculated":
                        pars['CR_flag']="calculated"
                    else:
                        pars['CR_flag']=""
                if 'CR_correction_factor_flag' in list(Data[s]['cooling_rate_data'].keys()) \
                    and Data[s]['cooling_rate_data']['CR_correction_factor_flag']!="calculated":
                    pars["CR_WARNING"]="inferred cooling rate correction"
    else:
        pars["CR_WARNING"]="no cooling rate correction"

    def combine_dictionaries(d1, d2):
        """
        combines dict1 and dict2 into a new dict.
        if dict1 and dict2 share a key, the value from dict1 is used
        """
        for key, value in d2.items():
            if key not in list(d1.keys()):
                d1[key] = value
        return d1

    Data[s]['pars'] = pars
    #print pars.keys()

    return(pars)

def calculate_ftest(s,sigma,nf):
    chibar=(s[0][0]+s[1][1]+s[2][2])/3.
    t=array(linalg.eigvals(s))
    F=0.4*(t[0]**2+t[1]**2+t[2]**2 - 3*chibar**2)/(float(sigma)**2)
    return(F)

def check_specimen_PI_criteria(pars,acceptance_criteria):
    '''
    # Check if specimen pass Acceptance criteria
    '''
    #if 'pars' not in self.Data[specimen].kes():
    #    return
        
    pars['specimen_fail_criteria']=[]
    for crit in list(acceptance_criteria.keys()):
        if crit not in list(pars.keys()):
            continue
        if acceptance_criteria[crit]['value']==-999:
            continue
        if acceptance_criteria[crit]['category']!='IE-SPEC':
            continue
        cutoff_value=acceptance_criteria[crit]['value']
        if crit=='specimen_scat':
            if pars["specimen_scat"] in ["Fail",'b',0,'0','FALSE',"False",False]:
                pars['specimen_fail_criteria'].append('specimen_scat')
        elif crit=='specimen_k' or crit=='specimen_k_prime':
            if abs(pars[crit])>cutoff_value:
                pars['specimen_fail_criteria'].append(crit)
        # high threshold value:
        elif acceptance_criteria[crit]['threshold_type']=="high":
            if pars[crit]>cutoff_value:
                pars['specimen_fail_criteria'].append(crit)
        elif acceptance_criteria[crit]['threshold_type']=="low":
            if pars[crit]<cutoff_value:
                pars['specimen_fail_criteria'].append(crit)
    return pars

def get_site_from_hierarchy(sample,Data_hierarchy):
    site=""
    sites=list(Data_hierarchy['sites'].keys())
    for S in sites:
        if sample in Data_hierarchy['sites'][S]:
            site=S
            break
    return(site)

def get_location_from_hierarchy(site,Data_hierarchy):
    location=""
    locations=list(Data_hierarchy['locations'].keys())
    for L in locations:
        if site in Data_hierarchy['locations'][L]:
            location=L
            break
    return(location)

