#!/usr/bin/env python
from __future__ import division
from __future__ import print_function
from builtins import str
from builtins import range
from past.utils import old_div
import sys
import scipy
import copy
import os
from pmagpy import pmag

def main(command_line=True, **kwargs):
    """
    NAME
        generic_magic.py

    DESCRIPTION
        converts magnetometer files in generic format to MagIC measurements format

    SYNTAX
        generic_magic.py [command line options]

    OPTIONS
        -h
            prints the help message and quits.
        -usr USER
            identify user, default is ""
        -f FILE:
            specify path to input file, required
        -fsa SAMPFILE:
            specify the samples file for sample orientation data. default is er_samples.txt
        -F FILE
            specify output file, default is magic_measurements.txt

        -Fsa FILE
            specify output file, default is er_samples.txt

        -exp EXPERIMENT-TYPE
            Demag:
                AF and/or Thermal
            PI:
                paleointenisty thermal experiment (ZI/IZ/IZZI/TT)
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

        -loc LOCNAM
            specify location/study name.

        -dc B PHI THETA:
            B: dc lab field (in micro tesla)
            PHI (declination). takes numbers from 0 to 360
            THETA (inclination). takes numbers from -90 to 90

            NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment.

        -A: don't average replicate measurements. Take the last measurement from replicate measurements.

        -WD working directory

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
                    Y=1: infield (IZZI, IZ, ZI, and Thellier protocol- first infield)
                    Y=2: pTRM check
                    Y=3: pTRM tail check
                    Y=4: Additivity check
                    Y=5: Thellier protocol: second infield
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



            #    if tmp_data['treatment']==Data[specimen][-1]['treatment'] and tmp_data['treatment_type']==Data[specimen][-1]['treatment_type']:
            #
            ## check replicates
            #if tmp_data['treatment']==Data[specimen][-1]['treatment'] and tmp_data['treatment_type']==Data[specimen][-1]['treatment_type']:
            #    #found_duplicate=True
            #    duplicates.append(Data[specimen][-1])
            #    duplicates.append(tmp_data)
            #    del(Data[specimen][-1])
            #    continue
            #else:
            #    if len(duplicates)>0:
            #        if average_replicates:
            #            Data[specimen].append(average_duplicates(duplicates))
            #            print "-W- WARNING: averaging %i duplicates for specimen %s treatmant %s"%(len(duplicates),specimen,duplicates[-1]['treatment'])
            #        else:
            #            Data[specimen].append(duplicates[-1])
            #            print "-W- WARNING: found %i duplicates for specimen %s treatmant %s. Taking the last measurement only"%(len(duplicates),specimen,duplicates[-1]['treatment'])
            #    duplicates=[]
            #    Data[specimen].append(tmp_data)


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


    # initialize some variables
    experiment = ''
    sample_nc = [1, 0]
    site_nc = [1, 0]
    meas_file = "magic_measurements.txt"
    labfield = 0

    #--------------------------------------
    # get command line arguments
    #--------------------------------------

    if command_line:
        args=sys.argv
        user=""
        if "-h" in args:
            print(main.__doc__)
            return False
        if "-usr" in args:
            ind=args.index("-usr")
            user=args[ind+1]
        else:
            user=""
        if '-F' in args:
            ind=args.index("-F")
            meas_file=args[ind+1]
        if '-Fsa' in args:
            ind=args.index("-Fsa")
            samp_file=args[ind+1]
        else:
            samp_file="er_samples.txt"

        if '-f' in args:
            ind=args.index("-f")
            magfile=args[ind+1]
            
        if "-dc" in args:
            ind=args.index("-dc")
            labfield=float(args[ind+1])*1e-6
            labfield_phi=float(args[ind+2])
            labfield_theta=float(args[ind+3])
        if '-exp' in args:
            ind=args.index("-exp")
            experiment=args[ind+1]
        if "-samp" in args:
            ind=args.index("-samp")
            sample_nc=[]
            sample_nc.append(args[ind+1])
            sample_nc.append(args[ind+2])
        if "-site" in args:
            ind=args.index("-site")
            site_nc=[]
            site_nc.append(args[ind+1])
            site_nc.append(args[ind+2])
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        else:
            er_location_name=""
        if "-A" in args:
            noave=1
        else:
            noave=0

        if "-WD" in args:
            ind=args.index("-WD")
            WD=args[ind+1]
            os.chdir(WD)

    # unpack keyword args if using as module
    if not command_line:
        user = kwargs.get('user', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        samp_file = kwargs.get('samp_file', 'er_samples.txt')
        magfile = kwargs.get('magfile', '')
        labfield = int(kwargs.get('labfield', 0))
        if labfield:
            labfield *= 1e-6
        labfield_phi = int(kwargs.get('labfield_phi', 0))
        labfield_theta = int(kwargs.get('labfield_theta', 0))
        experiment = kwargs.get('experiment', '')
        cooling_times = kwargs.get('cooling_times_list', '')
        sample_nc = kwargs.get('sample_nc', [1, 0])
        site_nc = kwargs.get('site_nc', [1, 0])
        er_location_name = kwargs.get('er_location_name', '')
        noave = kwargs.get('noave', 0) # 0 is default, means do average
        WD = kwargs.get('WD', '.')
        #os.chdir(WD)

    # format and validate variables
    if magfile:
        try:
            input=open(magfile,'r')
        except:
            print("bad mag file:",magfile)
            return False, "bad mag file"
    else:
        print("mag_file field is required option")
        print(main.__doc__)
        return False, "mag_file field is required option"

    if not experiment:
        print("-exp is required option. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see below for format), NLT")
        print(main.__doc__)
        return False, "-exp is required option"

    if experiment=='ATRM':
        if command_line:
            ind=args.index("ATRM")
            atrm_n_pos=int(args[ind+1])
        else:
            atrm_n_pos = 6

    if experiment=='AARM':
        if command_line:
            ind=args.index("AARM")
            aarm_n_pos=int(args[ind+1])
        else:
            aarm_n_pos = 6

    if  experiment=='CR':
        if command_line:
            ind=args.index("CR")
            cooling_times=args[ind+1]
        cooling_times_list=cooling_times.split(',')
        # if not command line, cooling_times_list is already set




    #--------------------------------------
    # read data from er_samples.txt
    #--------------------------------------

    #if "-fsa" in args:
    #   ind=args.index("-fsa")
    #    er_sample_file=args[ind+1]
    #else:
    #    er_sample_file="er_samples.txt"

    er_sample_data={}
    #er_sample_data=sort_magic_file(samp_file,1,'er_sample_name')
    try:
        er_sample_data=sort_magic_file(samp_file,1,'er_sample_name')
        print("-I- Found er_samples.txt")
        print('-I- sample information will be appended to existing er_samples.txt file')
    except:
        print("-I- Cant find file er_samples.txt")
        print('-I- sample information will be stored in new er_samples.txt file')

    #--------------------------------------
    # read data from generic file
    #--------------------------------------

    if  noave:
        mag_data=read_generic_file(magfile,False)
    else:
        mag_data=read_generic_file(magfile,True)

    #--------------------------------------
    # for each specimen get the data, and translate it to MagIC format
    #--------------------------------------

    ErSamplesRecs=[]
    MagRecs=[]
    specimens_list=list(mag_data.keys())
    specimens_list.sort()
    for specimen in specimens_list:
        measurement_running_number=0
        this_specimen_treatments=[] # a list of all treatments
        MagRecs_this_specimen=[]
        LP_this_specimen=[] # a list of all lab protocols
        IZ,ZI=0,0 # counter for IZ and ZI steps

        for meas_line in mag_data[specimen]:

            #------------------
            # trivial MagRec data
            #------------------

            MagRec={}
            MagRec['er_citation_names']="This study"
            MagRec["er_specimen_name"]=meas_line['specimen']
            MagRec["er_sample_name"]=get_upper_level_name(MagRec["er_specimen_name"],sample_nc)
            MagRec["er_site_name"]=get_upper_level_name(MagRec["er_sample_name"],site_nc)
            MagRec['er_location_name']=er_location_name
            MagRec['er_analyst_mail_names']=user
            MagRec["magic_instrument_codes"]=""
            MagRec["measurement_flag"]='g'
            MagRec["measurement_number"]="%i"%measurement_running_number

            MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["moment"])*1e-3) # in Am^2
            MagRec["measurement_temp"]='273.' # room temp in kelvin

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
                    MagRec["treatment_dc_field"]="0"
                    MagRec["treatment_dc_field_phi"]="0"
                    MagRec["treatment_dc_field_theta"]="0"
                elif not labfield:
                    print("-W- WARNING: labfield (-dc) is a required argument for this experiment type")
                    return False, "labfield (-dc) is a required argument for this experiment type"

                else:
                    MagRec["treatment_dc_field"]='%8.3e'%(float(labfield))
                    MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield_phi))
                    MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield_theta))
            else:
                MagRec["treatment_dc_field"]=""
                MagRec["treatment_dc_field_phi"]=""
                MagRec["treatment_dc_field_theta"]=""

            #------------------
            # treatment temperature/peak field
            #------------------

            if experiment == 'Demag':
                if meas_line['treatment_type']=='A':
                    MagRec['treatment_temp']="273."
                    MagRec["treatment_ac_field"]="%.3e"%(treatment[0]*1e-3)
                elif meas_line['treatment_type']=='N':
                    MagRec['treatment_temp']="273."
                    MagRec["treatment_ac_field"]=""
                else:
                    MagRec['treatment_temp']="%.2f"%(treatment[0]+273.)
                    MagRec["treatment_ac_field"]=""
            else:
                    MagRec['treatment_temp']="%.2f"%(treatment[0]+273.)
                    MagRec["treatment_ac_field"]=""


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
                elif treatment[1]==5 or treatment[1]==50: # Thellier protocol, second infield step
                    LT="LT-T-I"
                    LP=LP+":"+"LP-PI-II"
                    
                    # adjust field direction in thellier protocol 
                    MagRec["treatment_dc_field_phi"]="%.2f"%( (float(labfield_phi) +180.0)%360.    )
                    MagRec["treatment_dc_field_theta"]="%.2f"%( float(labfield_theta)*-1 )

                else:
                    print("-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['specimen'],meas_line['treatment']))
                    MagRec={}
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
                    #MagRec['treatment_temp']="273."
                    #MagRec["treatment_ac_field"]=""
                    LP="LP-AN-ARM"
                    n_pos=aarm_n_pos
                    if n_pos!=6:
                        print("the program does not support AARM in %i position."%n_pos)
                        continue

                if treatment[1]==0:
                    if experiment=='ATRM':
                        LT="LT-T-Z"
                        MagRec['treatment_temp']="%.2f"%(treatment[0]+273.)
                        MagRec["treatment_ac_field"]=""

                    else:
                        LT="LT-AF-Z"
                        MagRec['treatment_temp']="273."
                        MagRec["treatment_ac_field"]="%.3e"%(treatment[0]*1e-3)
                    MagRec["treatment_dc_field"]='0'
                    MagRec["treatment_dc_field_phi"]='0'
                    MagRec["treatment_dc_field_theta"]='0'
                else:
                    if experiment=='ATRM':
                        if float(treatment[1])==70 or float(treatment[1])==7: # alteration check as final measurement
                            LT="LT-PTRM-I"
                        else:
                            LT="LT-T-I"
                    else:
                        LT="LT-AF-I"
                    MagRec["treatment_dc_field"]='%8.3e'%(float(labfield))

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
                    MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                    MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])


            #---------------------
            # Lab treatment and lab protocoal for cooling rate experiment
            #---------------------

            elif experiment == "CR":

                cooling_times_list
                LP="LP-CR-TRM"
                MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

                if treatment[1]==0:
                    LT="LT-T-Z"
                    MagRec["treatment_dc_field"]="0"
                    MagRec["treatment_dc_field_phi"]='0'
                    MagRec["treatment_dc_field_theta"]='0'
                else:
                    if treatment[1]==7: # alteration check as final measurement
                            LT="LT-PTRM-I"
                    else:
                            LT="LT-T-I"
                    MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                    MagRec["treatment_dc_field_phi"]='%7.1f' % (labfield_phi) # labfield phi
                    MagRec["treatment_dc_field_theta"]='%7.1f' % (labfield_theta) # labfield theta

                    indx=int(treatment[1])-1
                    # alteration check matjed as 0.7 in the measurement file
                    if indx==6:
                        cooling_time= cooling_times_list[-1]
                    else:
                        cooling_time=cooling_times_list[indx]
                    MagRec["measurement_description"]="cooling_rate"+":"+cooling_time+":"+"K/min"


            #---------------------
            # Lab treatment and lab protocoal for NLT experiment
            #---------------------

            elif 'NLT' in experiment :
                print("Dont support yet NLT rate experiment file. Contact rshaar@ucsd.edu")

            #---------------------
            # magic_method_codes for this measurement only
            # LP will be fixed after all measurement lines are read
            #---------------------

            MagRec["magic_method_codes"]=LT+":"+LP

            #---------------------
            # Demag experiments only:
            # search if orientation data exists in er_samples.txt
            # if not: create one and save
            #---------------------

            # see if core azimuth and tilt-corrected data are in er_samples.txt
            sample=MagRec["er_sample_name"]
            found_sample_azimuth,found_sample_dip,found_sample_bed_dip_direction,found_sample_bed_dip=False,False,False,False
            if sample in list(er_sample_data.keys()):
                if "sample_azimuth" in list(er_sample_data[sample].keys()) and er_sample_data[sample]['sample_azimuth'] !="":
                    sample_azimuth=float(er_sample_data[sample]['sample_azimuth'])
                    found_sample_azimuth=True
                if "sample_dip" in list(er_sample_data[sample].keys()) and er_sample_data[sample]['sample_dip']!="":
                    sample_dip=float(er_sample_data[sample]['sample_dip'])
                    found_sample_dip=True
                if "sample_bed_dip_direction" in list(er_sample_data[sample].keys()) and er_sample_data[sample]['sample_bed_dip_direction']!="":
                    sample_bed_dip_direction=float(er_sample_data[sample]['sample_bed_dip_direction'])
                    found_sample_bed_dip_direction=True
                if "sample_bed_dip" in list(er_sample_data[sample].keys()) and er_sample_data[sample]['sample_bed_dip']!="":
                    sample_bed_dip=float(er_sample_data[sample]['sample_bed_dip'])
                    found_sample_bed_dip=True
            else:
                er_sample_data[sample]={}

            #--------------------
            # deal with specimen orientation and different coordinate system
            #--------------------

            found_s,found_geo,found_tilt=False,False,False
            if "dec_s" in list(meas_line.keys()) and "inc_s" in list(meas_line.keys()):
                if meas_line["dec_s"]!="" and meas_line["inc_s"]!="":
                    found_s=True
                MagRec["measurement_dec"]=meas_line["dec_s"]
                MagRec["measurement_inc"]=meas_line["inc_s"]
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
                MagRec["measurement_dec"]=meas_line["dec_g"]
                MagRec["measurement_inc"]=meas_line["inc_g"]

                # core azimuth/plunge is not in er_samples.txt
                if not found_sample_dip or not found_sample_azimuth:
                    er_sample_data[sample]['sample_azimuth']="0"
                    er_sample_data[sample]['sample_dip']="0"

                # core azimuth/plunge is in er_samples.txt
                else:
                    sample_azimuth=float(er_sample_data[sample]['sample_azimuth'])
                    sample_dip=float(er_sample_data[sample]['sample_dip'])
                    if sample_azimuth!=0 and sample_dip!=0:
                        print("-W- WARNING: delete core azimuth/plunge in er_samples.txt\n\
                        becasue dec_s and inc_s are unavaialable")

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

                # core azimuth/plunge is not in er_samples.txt:
                # calculate core az/pl and add it to er_samples.txt
                if not found_sample_dip or not found_sample_azimuth:
                    er_sample_data[sample]['sample_azimuth']="%.1f"%az
                    er_sample_data[sample]['sample_dip']="%.1f"%pl

                # core azimuth/plunge is in er_samples.txt
                else:
                    if float(er_sample_data[sample]['sample_azimuth'])!= az:
                        print("-E- ERROR in sample_azimuth sample %s. Check it! using the value in er_samples.txt"%sample)

                    if float(er_sample_data[sample]['sample_dip'])!= pl:
                        print("-E- ERROR in sample_dip sample %s. Check it! using the value in er_samples.txt"%sample)

            #-----------------------------
            # specimen coordinates: yes
            # geographic coordinates: no
            #-----------------------------
            if not found_geo and found_s:
                if found_sample_dip and found_sample_azimuth:
                    pass
                    # (nothing to do)
                else:
                    if "Demag" in experiment:
                        print("-W- WARNING: missing sample_dip or sample_azimuth for sample %s"%sample)

            #-----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: no
            #-----------------------------
            if found_tilt and not found_geo:
                    print("-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data "%sample)
            if found_tilt and found_geo:
                dec_geo,inc_geo=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                dec_tilt,inc_tilt=float(meas_line["dec_t"]),float(meas_line["inc_t"])
                if dec_geo==dec_tilt and inc_geo==inc_tilt:
                    DipDir,Dip=0.,0.
                else:
                    DipDir,Dip=pmag.get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt)

                if not found_sample_bed_dip_direction or not found_sample_bed_dip:
                    print("-I- calculating dip and dip direction used for tilt correction sample %s. results are put in er_samples.txt"%sample)
                    er_sample_data[sample]['sample_bed_dip_direction']="%.1f"%DipDir
                    er_sample_data[sample]['sample_bed_dip']="%.1f"%Dip

            #-----------------------------
            # er_samples method codes
            # geographic coordinates: no
            #-----------------------------
            if found_tilt or found_geo:
                er_sample_data[sample]['magic_method_codes']="SO-NO"


            #-----------------
            # er_samples_data
            #-----------------
            if sample in list(er_sample_data.keys()):
                er_sample_data[sample]['er_sample_name']=sample
                er_sample_data[sample]['er_site_name']=MagRec["er_site_name"]
                er_sample_data[sample]['er_location_name']=MagRec["er_location_name"]

            #MagRec["magic_method_codes"]=LT
            MagRecs_this_specimen.append(MagRec)

            #if LP!="" and LP not in LP_this_specimen:
            #    LP_this_specimen.append(LP)

            measurement_running_number+=1
            #-------

        #-------
        # after reading all the measurements lines for this specimen
        # 1) add magic_experiment_name
        # 2) fix magic_method_codes with the correct lab protocol
        #-------
        LP_this_specimen=[]
        for MagRec in MagRecs_this_specimen:
            magic_method_codes=MagRec["magic_method_codes"].split(":")
            for code in magic_method_codes:
                if "LP" in code and code not in LP_this_specimen:
                    LP_this_specimen.append(code)
        # check IZ/ZI/IZZI
        if "LP-PI-ZI" in   LP_this_specimen and "LP-PI-IZ" in   LP_this_specimen:
            LP_this_specimen.remove("LP-PI-ZI")
            LP_this_specimen.remove("LP-PI-IZ")
            LP_this_specimen.append("LP-PI-BT-IZZI")

        # add the right LP codes and fix experiment name
        for MagRec in MagRecs_this_specimen:
            MagRec["magic_experiment_name"]=MagRec["er_specimen_name"]+":"+":".join(LP_this_specimen)
            magic_method_codes=MagRec["magic_method_codes"].split(":")
            LT=""
            for code in magic_method_codes:
                if code[:3]=="LT-":
                    LT=code;
                    break
            MagRec["magic_method_codes"]=LT+":"+":".join(LP_this_specimen)

            MagRecs.append(MagRec)

    #--
    # write magic_measurements.txt
    #--
    MagRecs_fixed=merge_pmag_recs(MagRecs)
    pmag.magic_write(meas_file,MagRecs_fixed,'magic_measurements')
    print("-I- MagIC file is saved in  %s"%meas_file)

    #--
    # write er_samples.txt
    #--
    ErSamplesRecs=[]
    samples=list(er_sample_data.keys())
    samples.sort()
    for sample in samples:
        ErSamplesRecs.append(er_sample_data[sample])
    ErSamplesRecs_fixed=merge_pmag_recs(ErSamplesRecs)
    pmag.magic_write(samp_file,ErSamplesRecs_fixed,'er_samples')
    return True, meas_file

def do_help():
    return main.__doc__

if __name__ == '__main__':
    main()
