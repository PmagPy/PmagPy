#!/usr/bin/env python
"""
NAME
    generic_magic.py

DESCRIPTION
    converts magnetometer files in generic format to MagIC measurements format

SYNTAX
    generic_magic.py [command line options]

OPTIONS
    -h: shows this help message
    -usr USER: identify user, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt

    -exp EXPERIMENT-TYPE
        Demag:
            AF and/or Thermal
        PI:
            paleointenisty thermal experiment (ZI/IZ/IZZI)
        ATRM n:

            ATRM in n positions (n=6)

        AARM n:
            AARM in n positions
        CR:
            cooling rate experiment
            The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
            where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
            XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
            syntax in sio_magic is: -LP CR xxx,yyy,zzz,.....xx -A
            where xx, yyy,zzz...xxx  are cooling rates in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70

            No need to specify the cooling rate for the zerofield
            It is important to add to the command line the -A option so the measurements will not be averaged.
            But users need to make sure that there are no duplicate meaurements in the file

        NLT:
            non-linear-TRM experiment

    -samp X Y
        specimen-sample naming convention.
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from specimen --> sample OR which delimiter to use
        X=0 Y=n: specimen is distinguished from sample by n initial characters.
                 (example: "generic_magic.py -samp 0 4"
                  if n=4 then and specimen = mgf13a then sample = mgf13)
        X=1 Y=n: specimen is distiguished from sample by n terminate characters.
                 (example: "generic_magic.py -samp 1 1)
                  if n=1 then and specimen = mgf13a then sample = mgf13)
        X=2 Y=c: specimen is distinguishing from sample by a delimiter.
                 (example: "generic_magic.py -samp 2 -"
                  if c=- then and specimen = mgf13-a then sample = mgf13)
        default: sample is the same as specimen name

    -site X Y
        sample-site naming convention.
        X determines which kind of convention (initial characters, terminal characters, or delimiter
        Y determines how many characters to remove to go from sample --> site OR which delimiter to use
        X=0 Y=n: sample is distiguished from site by n initial characters.
                 (example: "generic_magic.py --site 0 3"
                  if n=3 then and sample = mgf13 then sample = mgf)
        X=1 Y=n: sample is distiguished from site by n terminate characters.
                 (example: "generic_magic.py --site 1 2"
                  if n=2 and sample = mgf13 then site = mgf)
        X=2 Y=c: specimen is distiguishing from sample by a delimiter.
                 (example: "generic_magic.py -site 2 -"
                  if c='-' and sample = 'mgf-13' then site = mgf)
        default: site name is the same as sample name

    -loc LOCNAME: specify location/study name.
    -lat LAT: latitude of site (also used as bounding latitude for location)
    -lon LON: longitude of site (also used as bounding longitude for location)
    -dc B PHI THETA:
        B: dc lab field (in micro tesla)
        PHI (declination). takes numbers from 0 to 360
        THETA (inclination). takes numbers from -90 to 90
        NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment.
    -A: don't average replicate measurements. Take the last measurement from replicate measurements.

INPUT

    A generic file is a tab-delimited file. Each column should have a header.
    The file must include the following headers (the order of the columns is not important):

        specimen
            string specifying specimen name

        treatment:
            a number with one or two decimal point (X.Y)
            coding for thermal demagnetization:
                0.0 or 0 is NRM.
                X is temperature in celsius
                Y is always 0
            coding for AF demagnetization:
                0.0 or 0 is NRM.
                X is AF peak field in mT
                Y is always 0
            coding for Thellier-type experiment:
                0.0 or 0 is NRM
                X is temperature in celsius
                Y=0: zerofield
                Y=1: infield
                Y=2: pTRM check
                Y=3: pTRM tail check
                Y=4: Additivity check
                # Ron, Add also 5 for Thellier protocol
            coding for ATRM experiment (6 poitions):
                X is temperature in celsius
                Y=0: zerofield baseline to be subtracted
                Y=1: +x
                Y=2: -x
                Y=3: +y
                Y=4: -y
                Y=5: +z
                Y=6: -z
                Y=7: alteration check
            coding for NLT experiment:
                X is temperature in celsius
                Y=0: zerofield baseline to be subtracted
                Y!=0: oven field  in microT
            coding for CR experiment:
                see "OPTIONS" list above

        treatment_type:
            N: NRM
            A: AF
            T: Thermal

        moment:
            magnetic moment in emu !!

    In addition, at least one of the following headers are required:

        dec_s:
            declination in specimen coordinate system (0 to 360)
        inc_s:
            inclination in specimen coordinate system (-90 to 90)

        dec_g:
            declination in geographic coordinate system (0 to 360)
        inc_g:
            inclination in geographic coordinate system (-90 to 90)

        dec_t:
            declination in tilt-corrected coordinate system (0 to 360)
        inc_t:
            inclination in tilt-corrected coordinate system (-90 to 90)
"""
from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
from past.utils import old_div
import sys, copy, os
import scipy
from pmagpy import pmag
import pmagpy.new_builder as nb

    #--------------------------------------
    # functions
    #--------------------------------------


def sort_magic_file(path,ignore_lines_n,sort_by_this_name):
    '''
    reads a file with headers. Each line is stored as a dictionary following the headers.
    Lines are sorted in DATA by the sort_by_this_name header
    DATA[sort_by_this_name]=[dictionary1,dictionary2,...]
    '''
    DATA={}
    fin=open(path,'r')
    #ignore first lines
    for i in range(ignore_lines_n):
        fin.readline()
    #header
    line=fin.readline()
    header=line.strip('\n').split('\t')
    #print header
    for line in fin.readlines():
        if line[0]=="#":
            continue
        tmp_data={}
        tmp_line=line.strip('\n').split('\t')
        #print tmp_line
        for i in range(len(tmp_line)):
            if i>= len(header):
                continue
            tmp_data[header[i]]=tmp_line[i]
        DATA[tmp_data[sort_by_this_name]]=tmp_data
    fin.close()
    return(DATA)

def read_generic_file(path,average_replicates):
    '''
    reads a generic file format. If average_replicates==True average replicate measurements.
    Rrturns a Data dictionary with measurements line sorted by specimen
    Data[specimen_name][dict1,dict2,...]
    '''
    Data={}
    Fin=open(path,'r')
    header=Fin.readline().strip('\n').split('\t')
    duplicates=[]
    for line in Fin.readlines():
        tmp_data={}
        #found_duplicate=False
        l=line.strip('\n').split('\t')
        for i in range(min(len(header),len(l))):
            tmp_data[header[i]]=l[i]
        specimen=tmp_data['specimen']
        if specimen not in list(Data.keys()):
            Data[specimen]=[]
        Data[specimen].append(tmp_data)
    Fin.close()
    # search fro duplicates
    for specimen in list(Data.keys()):
        x=len(Data[specimen])-1
        new_data=[]
        duplicates=[]
        for i in range(1,x):
            while i< len(Data[specimen]) and Data[specimen][i]['treatment']==Data[specimen][i-1]['treatment'] and Data[specimen][i]['treatment_type']==Data[specimen][i-1]['treatment_type']:
               duplicates.append(Data[specimen][i])
               del(Data[specimen][i])
            if len(duplicates)>0:
               if average_replicates:
                   duplicates.append(Data[specimen][i-1])
                   Data[specimen][i-1]=average_duplicates(duplicates)
                   print("-W- WARNING: averaging %i duplicates for specimen %s treatmant %s"%(len(duplicates),specimen,duplicates[-1]['treatment']))
                   duplicates=[]
               else:
                   Data[specimen][i-1]=duplicates[-1]
                   print("-W- WARNING: found %i duplicates for specimen %s treatmant %s. Taking the last measurement only"%(len(duplicates),specimen,duplicates[-1]['treatment']))
                   duplicates=[]

            if i==len(Data[specimen])-1:
                break

    return(Data)

def average_duplicates(duplicates):
    '''
    avarage replicate measurements.
    '''
    carts_s,carts_g,carts_t=[],[],[]
    for rec in duplicates:
        moment=float(rec['moment'])
        if 'dec_s' in list(rec.keys()) and 'inc_s' in list(rec.keys()):
            if rec['dec_s']!="" and rec['inc_s']!="":
                dec_s=float(rec['dec_s'])
                inc_s=float(rec['inc_s'])
                cart_s=pmag.dir2cart([dec_s,inc_s,moment])
                carts_s.append(cart_s)
        if 'dec_g' in list(rec.keys()) and 'inc_g' in list(rec.keys()):
            if rec['dec_g']!="" and rec['inc_g']!="":
                dec_g=float(rec['dec_g'])
                inc_g=float(rec['inc_g'])
                cart_g=pmag.dir2cart([dec_g,inc_g,moment])
                carts_g.append(cart_g)
        if 'dec_t' in list(rec.keys()) and 'inc_t' in list(rec.keys()):
            if rec['dec_t']!="" and rec['inc_t']!="":
                dec_t=float(rec['dec_t'])
                inc_t=float(rec['inc_t'])
                cart_t=pmag.dir2cart([dec_t,inc_t,moment])
                carts_t.append(cart_t)
    if len(carts_s)>0:
        carts=scipy.array(carts_s)
        x_mean=scipy.mean(carts[:,0])
        y_mean=scipy.mean(carts[:,1])
        z_mean=scipy.mean(carts[:,2])
        mean_dir=pmag.cart2dir([x_mean,y_mean,z_mean])
        mean_dec_s="%.2f"%mean_dir[0]
        mean_inc_s="%.2f"%mean_dir[1]
        mean_moment="%10.3e"%mean_dir[2]
    else:
        mean_dec_s,mean_inc_s="",""
    if len(carts_g)>0:
        carts=scipy.array(carts_g)
        x_mean=scipy.mean(carts[:,0])
        y_mean=scipy.mean(carts[:,1])
        z_mean=scipy.mean(carts[:,2])
        mean_dir=pmag.cart2dir([x_mean,y_mean,z_mean])
        mean_dec_g="%.2f"%mean_dir[0]
        mean_inc_g="%.2f"%mean_dir[1]
        mean_moment="%10.3e"%mean_dir[2]
    else:
        mean_dec_g,mean_inc_g="",""

    if len(carts_t)>0:
        carts=scipy.array(carts_t)
        x_mean=scipy.mean(carts[:,0])
        y_mean=scipy.mean(carts[:,1])
        z_mean=scipy.mean(carts[:,2])
        mean_dir=pmag.cart2dir([x_mean,y_mean,z_mean])
        mean_dec_t="%.2f"%mean_dir[0]
        mean_inc_t="%.2f"%mean_dir[1]
        mean_moment="%10.3e"%mean_dir[2]
    else:
        mean_dec_t,mean_inc_t="",""

    meanrec={}
    for key in list(duplicates[0].keys()):
        if key in ['dec_s','inc_s','dec_g','inc_g','dec_t','inc_t','moment']:
            continue
        else:
            meanrec[key]=duplicates[0][key]
    meanrec['dec_s']=mean_dec_s
    meanrec['dec_g']=mean_dec_g
    meanrec['dec_t']=mean_dec_t
    meanrec['inc_s']=mean_inc_s
    meanrec['inc_g']=mean_inc_g
    meanrec['inc_t']=mean_inc_t
    meanrec['moment']=mean_moment
    return meanrec

def get_upper_level_name(name,nc):
    '''
    get sample/site name from specimen/sample using naming convention
    '''
    if float(nc[0])==0:
        if float(nc[1])!=0:
            number_of_char=int(nc[1])
            high_name=name[:number_of_char]
        else:
            high_name=name
    elif float(nc[0])==1:
        if float(nc[1])!=0:
            number_of_char=int(nc[1])*-1
            high_name=name[:number_of_char]
        else:
            high_name=name
    elif float(nc[0])==2:
        d=str(nc[1])
        name_splitted=name.split(d)
        if len(name_splitted)==1:
            high_name=name_splitted[0]
        else:
            high_name=d.join(name_splitted[:-1])
    else:
        high_name=name
    return high_name

def merge_pmag_recs(old_recs):
    recs={}
    recs=copy.deepcopy(old_recs)
    headers=[]
    for rec in recs:
        for key in list(rec.keys()):
            if key not in headers:
                headers.append(key)
    for rec in recs:
        for header in headers:
            if header not in list(rec.keys()):
                rec[header]=""
    return recs

def convert(**kwargs):

    # unpack keyword args
    user = kwargs.get('user', '')
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt')
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt')
    loc_file = kwargs.get('loc_file', 'locations.txt')
    magfile = kwargs.get('magfile', '')
    labfield = float(kwargs.get('labfield', 0))*1e-6
    labfield_phi = float(kwargs.get('labfield_phi', 0))
    labfield_theta = float(kwargs.get('labfield_theta', 0))
    experiment = kwargs.get('experiment', '')
    cooling_times_list = kwargs.get('cooling_times_list', [])
    sample_nc = kwargs.get('sample_nc', [1, 0])
    site_nc = kwargs.get('site_nc', [1, 0])
    location = kwargs.get('location', 'unknown')
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    noave = kwargs.get('noave', False) # False is default, means do average
    WD = kwargs.get('WD', '.')
    output_dir_path=WD

    # format and validate variables
    if magfile:
        try:
            input=open(magfile,'r')
        except:
            print("bad mag file:",magfile)
            return False, "bad mag file"
    else:
        print("mag_file field is required option")
        print(__doc__)
        return False, "mag_file field is required option"

    if not experiment:
        print("-exp is required option. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see below for format), NLT")
        print(__doc__)
        return False, "-exp is required option"

    if experiment=='ATRM':
        if command_line:
            ind=sys.argv.index("ATRM")
            atrm_n_pos=int(sys.argv[ind+1])
        else:
            atrm_n_pos = 6

    if experiment=='AARM':
        if command_line:
            ind=sys.argv.index("AARM")
            aarm_n_pos=int(sys.argv[ind+1])
        else:
            aarm_n_pos = 6

    if  experiment=='CR':
        if command_line:
            ind=sys.argv.index("CR")
            cooling_times=sys.argv[ind+1]
            cooling_times_list=cooling_times.split(',')
        # if not command line, cooling_times_list is already set

    #--------------------------------------
    # read data from generic file
    #--------------------------------------

    mag_data=read_generic_file(magfile,not noave)

    #--------------------------------------
    # for each specimen get the data, and translate it to MagIC format
    #--------------------------------------

    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    specimens_list=sorted(mag_data.keys())
    for specimen in specimens_list:
        measurement_running_number=0
        this_specimen_treatments=[] # a list of all treatments
        MeasRecs_this_specimen=[]
        LP_this_specimen=[] # a list of all lab protocols
        IZ,ZI=0,0 # counter for IZ and ZI steps

        for meas_line in mag_data[specimen]:

            #------------------
            # trivial MeasRec data
            #------------------

            MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}

            specimen=meas_line['specimen']
            sample=get_upper_level_name(specimen,sample_nc)
            site=get_upper_level_name(sample,site_nc)
            sample_method_codes=""
            azimuth,dip,DipDir,Dip="","","",""

            MeasRec['citations']="This study"
            MeasRec["specimen"]=specimen
            MeasRec['analysts']=user
            MeasRec["instrument_codes"]=""
            MeasRec["quality"]='g'
            MeasRec["treat_step_num"]="%i"%measurement_running_number
            MeasRec["magn_moment"]='%10.3e'%(float(meas_line["moment"])*1e-3) # in Am^2
            MeasRec["meas_temp"]='273.' # room temp in kelvin

            #------------------
            #  decode treatments from treatment column in the generic file
            #------------------

            treatment=[]
            treatment_code=str(meas_line['treatment']).split(".")
            treatment.append(float(treatment_code[0]))
            if len(treatment_code)==1:
                treatment.append(0)
            else:
                treatment.append(float(treatment_code[1]))

            #------------------
            #  lab field direction
            #------------------

            if experiment in ['PI','NLT','CR']:

                if float(treatment[1])==0:
                    MeasRec["treat_dc_field"]="0"
                    MeasRec["treat_dc_field_phi"]="0"
                    MeasRec["treat_dc_field_theta"]="0"
                elif not labfield:
                    print("-W- WARNING: labfield (-dc) is a required argument for this experiment type")
                    return False, "labfield (-dc) is a required argument for this experiment type"

                else:
                    MeasRec["treat_dc_field"]='%8.3e'%(float(labfield))
                    MeasRec["treat_dc_field_phi"]="%.2f"%(float(labfield_phi))
                    MeasRec["treat_dc_field_theta"]="%.2f"%(float(labfield_theta))
            else:
                MeasRec["treat_dc_field"]=""
                MeasRec["treat_dc_field_phi"]=""
                MeasRec["treat_dc_field_theta"]=""

            #------------------
            # treatment temperature/peak field
            #------------------

            if experiment == 'Demag':
                if meas_line['treatment_type']=='A':
                    MeasRec['treat_temp']="273."
                    MeasRec["treat_ac_field"]="%.3e"%(treatment[0]*1e-3)
                elif meas_line['treatment_type']=='N':
                    MeasRec['treat_temp']="273."
                    MeasRec["treat_ac_field"]=""
                else:
                    MeasRec['treat_temp']="%.2f"%(treatment[0]+273.)
                    MeasRec["treat_ac_field"]=""
            else:
                    MeasRec['treat_temp']="%.2f"%(treatment[0]+273.)
                    MeasRec["treat_ac_field"]=""


            #---------------------
            # Lab treatment
            # Lab protocol
            #---------------------

            #---------------------
            # Lab treatment and lab protocoal for NRM:
            #---------------------

            if float(meas_line['treatment'])==0:
                LT="LT-NO"
                LP="" # will be filled later after finishing reading all measurements line

            #---------------------
            # Lab treatment and lab protocoal for paleointensity experiment
            #---------------------

            elif experiment =='PI':
                LP="LP-PI-TRM"
                if treatment[1]==0:
                    LT="LT-T-Z"
                elif  treatment[1]==1 or treatment[1]==10: # infield
                    LT="LT-T-I"
                elif treatment[1]==2 or treatment[1]==20:  # pTRM check
                    LT="LT-PTRM-I"
                    LP=LP+":"+"LP-PI-ALT-PTRM"
                elif treatment[1]==3 or treatment[1]==30: # Tail check
                    LT="LT-PTRM-MD"
                    LP=LP+":"+"LP-PI-BT-MD"
                elif treatment[1]==4 or treatment[1]==40: # Additivity check
                    LT="LT-PTRM-AC"
                    LP=LP+":"+"LP-PI-BT-MD"
                else:
                    print("-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['specimen'],meas_line['treatment']))
                    MeasRec={}
                    continue
                # save all treatment in a list
                # we will use this later to distinguidh between ZI / IZ / and IZZI

                this_specimen_treatments.append(float(meas_line['treatment']))
                if LT=="LT-T-Z":
                    if float(treatment[0]+0.1) in this_specimen_treatments:
                        LP=LP+":"+"LP-PI-IZ"
                if LT=="LT-T-I":
                    if float(treatment[0]+0.0) in this_specimen_treatments:
                        LP=LP+":"+"LP-PI-ZI"
            #---------------------
            # Lab treatment and lab protocoal for demag experiment
            #---------------------

            elif "Demag" in experiment:
                if meas_line['treatment_type']=='A':
                    LT="LT-AF-Z"
                    LP="LP-DIR-AF"
                else:
                    LT="LT-T-Z"
                    LP="LP-DIR-T"

            #---------------------
            # Lab treatment and lab protocoal for ATRM experiment
            #---------------------

            elif experiment in ['ATRM','AARM']:

                if experiment=='ATRM':
                    LP="LP-AN-TRM"
                    n_pos=atrm_n_pos
                    if n_pos!=6:
                        print("the program does not support ATRM in %i position."%n_pos)
                        continue

                if experiment=='AARM':
                    LP="LP-AN-ARM"
                    n_pos=aarm_n_pos
                    if n_pos!=6:
                        print("the program does not support AARM in %i position."%n_pos)
                        continue

                if treatment[1]==0:
                    if experiment=='ATRM':
                        LT="LT-T-Z"
                        MeasRec['treat_temp']="%.2f"%(treatment[0]+273.)
                        MeasRec["treat_ac_field"]=""

                    else:
                        LT="LT-AF-Z"
                        MeasRec['treat_temp']="273."
                        MeasRec["treat_ac_field"]="%.3e"%(treatment[0]*1e-3)
                    MeasRec["treat_dc_field"]='0'
                    MeasRec["treat_dc_field_phi"]='0'
                    MeasRec["treat_dc_field_theta"]='0'
                else:
                    if experiment=='ATRM':
                        if float(treatment[1])==70 or float(treatment[1])==7: # alteration check as final measurement
                            LT="LT-PTRM-I"
                        else:
                            LT="LT-T-I"
                    else:
                        LT="LT-AF-I"
                    MeasRec["treat_dc_field"]='%8.3e'%(float(labfield))

                    # find the direction of the lab field in two ways:

                    # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                    tdec=[0,90,0,180,270,0,0,90,0]
                    tinc=[0,0,90,0,0,-90,0,0,90]
                    if treatment[1] < 10:
                        ipos_code=int(treatment[1])-1
                    else:
                        ipos_code=int(old_div(treatment[1],10))-1

                    # (2) using the magnetization
                    if meas_line["dec_s"]!="":
                        DEC=float(meas_line["dec_s"])
                        INC=float(meas_line["inc_s"])
                    elif meas_line["dec_g"]!="":
                        DEC=float(meas_line["dec_g"])
                        INC=float(meas_line["inc_g"])
                    elif meas_line["dec_t"]!="":
                        DEC=float(meas_line["dec_t"])
                        INC=float(meas_line["inc_t"])
                    if DEC<0 and DEC>-359:
                        DEC=360.+DEC

                    if INC < 45 and INC > -45:
                        if DEC>315  or DEC<45: ipos_guess=0
                        if DEC>45 and DEC<135: ipos_guess=1
                        if DEC>135 and DEC<225: ipos_guess=3
                        if DEC>225 and DEC<315: ipos_guess=4
                    else:
                        if INC >45: ipos_guess=2
                        if INC <-45: ipos_guess=5
                    # prefer the guess over the code
                    ipos=ipos_guess
                    # check it
                    if treatment[1]!= 7 and treatment[1]!= 70:
                        if ipos_guess!=ipos_code:
                            print("-W- WARNING: check specimen %s step %s, anistropy measurements, coding does not match the direction of the lab field"%(specimen,meas_line['treatment']))
                    MeasRec["treat_dc_field_phi"]='%7.1f' %(tdec[ipos])
                    MeasRec["treat_dc_field_theta"]='%7.1f'% (tinc[ipos])

            #---------------------
            # Lab treatment and lab protocoal for cooling rate experiment
            #---------------------

            elif experiment == "CR":

                cooling_times_list
                LP="LP-CR-TRM"
                MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

                if treatment[1]==0:
                    LT="LT-T-Z"
                    MeasRec["treat_dc_field"]="0"
                    MeasRec["treat_dc_field_phi"]='0'
                    MeasRec["treat_dc_field_theta"]='0'
                else:
                    if treatment[1]==7: # alteration check as final measurement
                            LT="LT-PTRM-I"
                    else:
                            LT="LT-T-I"
                    MeasRec["treat_dc_field"]='%8.3e'%(labfield)
                    MeasRec["treat_dc_field_phi"]='%7.1f' % (labfield_phi) # labfield phi
                    MeasRec["treat_dc_field_theta"]='%7.1f' % (labfield_theta) # labfield theta

                    indx=int(treatment[1])-1
                    # alteration check matjed as 0.7 in the measurement file
                    if indx==6:
                        cooling_time= cooling_times_list[-1]
                    else:
                        cooling_time=cooling_times_list[indx]
                    MeasRec["measurement_description"]="cooling_rate"+":"+cooling_time+":"+"K/min"


            #---------------------
            # Lab treatment and lab protocoal for NLT experiment
            #---------------------

            elif 'NLT' in experiment :
                print("Dont support yet NLT rate experiment file. Contact rshaar@ucsd.edu")

            #---------------------
            # method_codes for this measurement only
            # LP will be fixed after all measurement lines are read
            #---------------------

            MeasRec["method_codes"]=LT+":"+LP

            #--------------------
            # deal with specimen orientation and different coordinate system
            #--------------------

            found_s,found_geo,found_tilt=False,False,False
            if "dec_s" in list(meas_line.keys()) and "inc_s" in list(meas_line.keys()):
                if meas_line["dec_s"]!="" and meas_line["inc_s"]!="":
                    found_s=True
                MeasRec["dir_dec"]=meas_line["dec_s"]
                MeasRec["dir_inc"]=meas_line["inc_s"]
            if "dec_g" in list(meas_line.keys()) and "inc_g" in list(meas_line.keys()):
                if meas_line["dec_g"]!="" and meas_line["inc_g"]!="":
                    found_geo=True
            if "dec_t" in list(meas_line.keys()) and "inc_t" in list(meas_line.keys()):
                if meas_line["dec_t"]!="" and meas_line["inc_t"]!="":
                    found_tilt=True

            #-----------------------------
            # specimen coordinates: no
            # geographic coordinates: yes
            #-----------------------------

            if found_geo and not found_s:
                MeasRec["dir_dec"]=meas_line["dec_g"]
                MeasRec["dir_inc"]=meas_line["inc_g"]
                azimuth="0"
                dip="0"

            #-----------------------------
            # specimen coordinates: no
            # geographic coordinates: no
            #-----------------------------
            if not found_geo and not found_s:
                print("-E- ERROR: sample %s does not have dec_s/inc_s or dec_g/inc_g. Ignore specimen %s "%(sample,specimen))
                break

            #-----------------------------
            # specimen coordinates: yes
            # geographic coordinates: yes
            #
            # commant: Ron, this need to be tested !!
            #-----------------------------
            if found_geo and found_s:
                cdec,cinc=float(meas_line["dec_s"]),float(meas_line["inc_s"])
                gdec,ginc=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                az,pl=pmag.get_azpl(cdec,cinc,gdec,ginc)
                azimuth="%.1f"%az
                dip="%.1f"%pl

            #-----------------------------
            # specimen coordinates: yes
            # geographic coordinates: no
            #-----------------------------
            if not found_geo and found_s and "Demag" in experiment:
                print("-W- WARNING: missing dip or azimuth for sample %s"%sample)

            #-----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: no
            #-----------------------------
            if found_tilt and not found_geo:
                    print("-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data "%sample)

            #-----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: yes
            #-----------------------------
            if found_tilt and found_geo:
                dec_geo,inc_geo=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                dec_tilt,inc_tilt=float(meas_line["dec_t"]),float(meas_line["inc_t"])
                if dec_geo==dec_tilt and inc_geo==inc_tilt:
                    DipDir,Dip=0.,0.
                else:
                    DipDir,Dip=pmag.get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt)

            #-----------------------------
            # samples method codes
            # geographic coordinates: no
            #-----------------------------
            if found_tilt or found_geo:
                sample_method_codes="SO-NO"


            if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRec['citations'] = "This study"
                SpecRecs.append(SpecRec)
            if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['citations'] = "This study"
                SampRec['azimuth'] = azimuth
                SampRec['dip'] = dip
                SampRec['bed_dip_direction'] = DipDir
                SampRec['bed_dip'] = Dip
                SampRec['method_codes']=sample_method_codes
                SampRecs.append(SampRec)
            if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['citations'] = "This study"
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRecs.append(SiteRec)
            if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['citations'] = "This study"
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRecs.append(LocRec)

            MeasRecs_this_specimen.append(MeasRec)
            measurement_running_number+=1
            #-------

        #-------
        # after reading all the measurements lines for this specimen
        # 1) add experiments
        # 2) fix method_codes with the correct lab protocol
        #-------
        LP_this_specimen=[]
        for MeasRec in MeasRecs_this_specimen:
            method_codes=MeasRec["method_codes"].split(":")
            for code in method_codes:
                if "LP" in code and code not in LP_this_specimen:
                    LP_this_specimen.append(code)
        # check IZ/ZI/IZZI
        if "LP-PI-ZI" in   LP_this_specimen and "LP-PI-IZ" in   LP_this_specimen:
            LP_this_specimen.remove("LP-PI-ZI")
            LP_this_specimen.remove("LP-PI-IZ")
            LP_this_specimen.append("LP-PI-BT-IZZI")

        # add the right LP codes and fix experiment name
        for MeasRec in MeasRecs_this_specimen:
            MeasRec["experiments"]=MeasRec["specimen"]+":"+":".join(LP_this_specimen)
            method_codes=MeasRec["method_codes"].split(":")
            LT=""
            for code in method_codes:
                if code[:3]=="LT-":
                    LT=code;
                    break
            MeasRec["method_codes"]=LT+":"+":".join(LP_this_specimen)
            MeasRecs.append(MeasRec)

    #--
    # write tables to file
    #--

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts=pmag.measurements_methods3(MeasRecs,noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

def do_help():
    return __doc__

def main():
    kwargs={}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if "-usr" in sys.argv:
        ind=sys.argv.index("-usr")
        kwargs['user']=sys.argv[ind+1]
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        kwargs['dir_path']=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        kwargs['meas_file']=sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file'] = sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv:
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['magfile']=sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind=sys.argv.index("-dc")
        kwargs['labfield']=sys.argv[ind+1]
        kwargs['labfield_phi']=sys.argv[ind+2]
        kwargs['labfield_theta']=sys.argv[ind+3]
    if '-exp' in sys.argv:
        ind=sys.argv.index("-exp")
        kwargs['experiment']=sys.argv[ind+1]
    if "-samp" in sys.argv:
        ind=sys.argv.index("-samp")
        kwargs['sample_nc']=[]
        kwargs['sample_nc'].append(sys.argv[ind+1])
        kwargs['sample_nc'].append(sys.argv[ind+2])
    if "-site" in sys.argv:
        ind=sys.argv.index("-site")
        kwargs['site_nc']=[]
        kwargs['site_nc'].append(sys.argv[ind+1])
        kwargs['site_nc'].append(sys.argv[ind+2])
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-A" in sys.argv: kwargs['noave']=True

    convert(**kwargs)

if __name__ == '__main__':
    main()
