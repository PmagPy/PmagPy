#!/usr/bin/env python
import string,sys,pmag
def main():
    """
    NAME
        generic_magic.py
 
    DESCRIPTION
        converts magnetometer files in generic format to magic_measurements format

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
            specify er_samples.txt file for sample orientation data. default is er_samples.txt
        -F FILE
            specify output file, default is magic_measurements.txt
        
        ???-Fsy: specify er_synthetics file, default is er_sythetics.txt
        
        #-Fsa:
        #    specify output er_samples file, default is NONE 
       
        -exp EXPERIMENT-TYPE 
            Demag:
                AF and/or Thermal
            PI:
                paleointenisty thermal experiment (ZI/IZ/IZZI)
            ATRM-6:
                ATRM in six positions
            CR:
                cooling rate experiment
            NLT:
                non-linear-TRM experiment
                
        -samp X Y
            specimen-sample naming convention.
            X=1 Y=n: specimen is distiguished from sample by n terminate characters.
                     (example: if n=1 then specimen = mgf13a and sample = mgf13)
            X=2 Y=c: specimen is distiguishing from sample by a delimiter.
                     (example: if c=- then specimen = mgf13-a and sample = mgf13)

        -site X Y
            sample-site naming convention.
            X=1 Y=n: sample is distiguished from site by n terminate characters.
                     (example: if n=2 then sample = mgf13 and site = mg)
            X=2 Y=c: specimen is distiguishing from sample by a delimiter.
                     (example: if c=- then sample = mgf-13 and site = mg)
        
        -loc LOCNAM 
            specify location/study name.
        
        -dc B PHI THETA:
            B: dc lab field (in micro tesla)
            PHI (declination). takes numbers from 0 to 360
            THETA (inclination). takes numbers from -90 to 90
              
            NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment.
              
        -A: don't average replicate measurements. Take the last measurement from replicate measurements.

    INPUT
    
        A generic file is a tab-delimited file. Each columns should have a header.
        The file must include the follwing headers. The order of the columns is not important.
        specimen:
            string specifying specimen name
        treatment:
            a number with one or two decimal point (X.Y) 
            coding for thermal demagnetization:  
                0.0 or 0 is NRM.
                X is temperature in celcsius
                Y is always 0
            coding for AF demagnetization:
                0.0 or 0 is NRM.
                X is AF peak field in mT
                Y is always 0
            coding for Thellier-type experiment: 
                0.0 or 0 is NRM
                X is temperature in celcsius
                Y=0: zerofield               
                Y=1: infield               
                Y=2: pTRM check               
                Y=3: pTRM tail check               
                Y=4: Additivity check  
                # Ron, Add also 5 for Thellier protocol             
       treatment_type:
           N: NRM 
           A: AF
           T: Thermal 
       moment:
           magnetic moment in emu !!            
       
       In addition. at least one of the following headers are requiered:    
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
            
    
    Testing:
        1) make a genetric file with AF
        2) make a genetric file with Thermal
        3) make a genetric file with Thermal + AF 
        4) make a genetric file with IZZI 
        5) check duplicates option
                                        
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
        fin=open(path,'rU')
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
        Fin=open(path,'rU')
        header=Fin.readline().strip('\n').split('\t')
        
        for line in Fin.readlines():
            tmp_data={}
            duplicates=[]
            found_duplicate=False
            l=line.strip('\n').split('\t')
            for i in range(min(len(header),len(l))):
                tmp_data[header[i]]=l[i]
            specimen=tmp_data['specimen']
            if specimen not in Data.keys():
                Data[specimen]=[]
                Data[specimen].append(tmp_data)
                continue
            
            # check replicates
            if tmp_data['treatment']==Data[specimen][-1]['treatment'] and tmp_data['treatment_type']==Data[specimen][-1]['treatment_type']:
                found_duplicate=True
                duplicates.append(tmp_data)
                continue
            else:                           
                if len(duplicates)>0:
                    Data[specimen].append(average_duplicates(duplicates))
                duplicate=False
                duplicates=[]
                Data[specimen].append(tmp_data)                            
           
        return(Data)               

    def average_duplicates(duplicates):
        '''
        avarage replicate measurements.
        '''        
        print "Ron, dont forget to add duplicate measuremens function"
        return duplicates[-1]
    
    def get_upper_level_name(name,nc):
        '''
        get sample/site name from specimen/sample using naming convention
        '''
        if nc[0]==1:
            number_of_char=int(nc[1])*-1
            high_name=name[:number_of_char]
        elif nc[0]==2:
            d=str(nc[1])
            name_splitted=name.split(d)
            if len(name_splitted)==1:
                high_name=name_splitted[0]
            else:
                high_name=d.join(name_splitted[:-1])
        return high_name
                            
    
    #--------------------------------------
    # get command line arguments
    #--------------------------------------

    args=sys.argv
    user=""
    if "-h" in args:
        print main.__doc__
        sys.exit()
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
        try:
            open(samp_file,'rU')
            ErSamps,file_type=pmag.magic_read(samp_file)
            print 'sample information will be appended to new er_samples.txt file'
        except:
            print 'sample information will be stored in new er_samples.txt file'
    if '-f' in args:
        ind=args.index("-f")
        magfile=args[ind+1]
        try:
            input=open(magfile,'rU')
        except:
            print "bad mag file:",magfile
            sys.exit()
    else: 
        print "mag_file field is required option"
        print main.__doc__
        sys.exit()
    
    if "-dc" in args:
        ind=args.index("-dc")
        labfield=float(args[ind+1])*1e-6
        phi=float(args[ind+2])
        theta=float(args[ind+3])
    if '-exp' in args:
        ind=args.index("-exp")
        experiment=args[ind+1]        
    else: 
        print "-LP is required option"
        print main.__doc__
        sys.exit()

    if "-samp" in args:
        ind=args.index("-samp")
        sample_nc=[]
        sample_nc[0]=args[ind+1]
        sample_nc[1]=args[ind+2]

    if "-site" in args:
        ind=args.index("-site")
        site_nc=[]
        site_nc[0]=args[ind+1]
        site_nc[1]=args[ind+2]
    if "-loc" in args:
        ind=args.index("-loc")
        er_location_name=args[ind+1]
    else:
        er_location_name=""
    if "-A" in args:
        noave=1                

    #--------------------------------------
    # read data from er_samples.txt
    #--------------------------------------

    if "-fsa" in args:
        ind=args.index("-fsa")
        er_sample_file=args[ind+1]
    else:
        er_sample_file="er_samples.txt"

    er_sample_data={}
    try:
        er_sample_data=sort_magic_file(er_sample_file,'er_sample_name')
    except:
        print "-I- Cant find file er_samples.txt"
            
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
    specimens_list=mag_data.keys()
    specimens_list.sort()
    for specimen in specimens_list:
        measurement_running_number=0
        this_specimen_treatments=[] # a list of all treatments
        MagRecs_this_specimen=[]
        LP_this_specimen=[] # a list of all lab protocols
        IZ,ZI=0,0 # counter for IZ and ZI steps
        
        for meas_line in mag_data:            
            
            #------------------
            # trivial MagRec data
            #------------------

            MagRec={}
            MagRec['er_citation_names']="This study"
            MagRec["er_specimen_name"]=meas_line['specimen']
            MagRec["er_sample_name"]=get_upper_level_name(MagRec["er_specimen_name"],nc)
            MagRec["er_site_name"]=get_upper_level_name(MagRec["er_sample_name"],nc)
            MagRec['er_location_name']=er_location_name
            MagRec['er_analyst_mail_names']=user 
            MagRec["magic_instrument_codes"]="" 
            MagRec["measurement_flag"]='g'
            MagRec["measurement_number"]="%i"%measurement_running_number
            
            MagRec["measurement_magn_moment"]='%10.3e'%(float(meas_line["moment"])*1e-3) # in Am^2
            MagRec["measurement_temp"]='273.' # room temp in kelvin
            if experiment in ['PI','NLT','CR']:                        
                MagRec["treatment_dc_field"]='%8.3e'%(float(labfield[0])*1e-6)
                MagRec["treatment_dc_field_phi"]="%.2f"%(float(labfield[1]))
                MagRec["treatment_dc_field_theta"]="%.2f"%(float(labfield[2]))
            else:
                MagRec["treatment_dc_field"]=""
                MagRec["treatment_dc_field_phi"]=""
                MagRec["treatment_dc_field_theta"]=""
            
            print "Ron, dont forget    magic_experiment_name !!"

            #------------------
            #  decode treatments from treatment column in the generic file 
            #------------------

            treatment=float(str(meas_line['treatment']).split("."))
            treatment[0]=float(treatment[0])
            if len(treatment)==0:
                treatment[1]=0
            else:
                treatment[1]=float(treatment[1])

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
            
            if float['treatment']==0:
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
                    print "-E- unknown measurement code specimen %s treatmemt %s"%(meas_line['specimen'],meas_line['treatment'])
                    MagRec={}
                    continue
                # save all treatment in a list 
                # we will use this later to distinguidh between ZI / IZ / and IZZI
                
                this_specimen_treatments.append(float(meas_line['treatment']))
                if LT=="LT-T-Z":
                    if int(meas_line['treatment'])+0.1 in this_specimen_treatments:
                        LP==LP+":"+"LP-PI-IZ"
                if LT=="LT-T-I":
                    if int(meas_line['treatment'])+0.0 in this_specimen_treatments:
                        LP==LP+":"+"LP-PI-ZI"
                
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
                                
            elif 'ATRM' in experiment :
                LP="LP-AN-TRM"
                if treatment[1]==0:
                    LT="LT-T-Z"
                    MagRec["treatment_dc_field_phi"]='0'
                    MagRec["treatment_dc_field_theta"]='0'
                else:
                            
                    # find the direction of the lab field in two ways:
                    
                    # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                    tdec=[0,90,0,180,270,0,0,90,0]
                    tinc=[0,0,90,0,0,-90,0,0,90]
                    if treatment[1] < 10:
                        ipos_code=int(treatment[1])-1
                    else:
                        ipos_code=int(treatment[1]/10)-1
                    
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
                            print "-W- WARNING: check specimen %s step %s, ATRM measurements, coding does not match the direction of the lab field"%(specimen,meas_line['Treatment'])
                    MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec[ipos])
                    MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc[ipos])
                        
                    if float(treatment[1])==70 or float(treatment[1])==7: # alteration check as final measurement
                            LT="LT-PTRM-I"
                    else:
                            LT="LT-T-I"

            #---------------------                    
            # Lab treatment and lab protocoal for cooling rate experiment
            #---------------------
                                                        
            elif 'CR' in experiment :
                print "Dont support yet cooling rate experiment file. Contact rshaar@ucsd.edu"
    

            #---------------------                    
            # Lab treatment and lab protocoal for NLT experiment
            #---------------------
            
            elif 'NLT' in experiment :
                print "Dont support yet NLT rate experiment file. Contact rshaar@ucsd.edu"

            #---------------------                                        
            # magic_method_codes for this measurement only
            # LP will be fixed after all measurement lines are read
            #---------------------
            
            MagRec["magic_method_codes"]=LP+":"+LT

            #---------------------  
            # Demag experiments only:                                      
            # search if orientation data exists in er_samples.txt
            # if not: create one and save
            #---------------------

            # see if core azimuth and tilt-corrected data are in er_samples.txt
            sample=MagRec["er_sample_name"]
            found_sample_azimuth,found_sample_dip,found_sample_bed_dip_direction,found_sample_bed_dip=False,False,False,False
            if sample in er_sample_data.keys():
                if "sample_azimuth" in er_sample_data[sample].keys() and er_sample_data[sample]['sample_azimuth'] !="":
                    sample_azimuth=float(er_sample_data[sample]['sample_azimuth'])
                    found_sample_azimuth=True
                if "sample_dip" in er_sample_data[sample].keys() and er_sample_data[sample]['sample_dip']!="":
                    sample_dip=float(er_sample_data[sample]['sample_dip'])
                    found_sample_dip=True
                if "sample_bed_dip_direction" in er_sample_data[sample].keys() and er_sample_data[sample]['sample_bed_dip_direction']!="":
                    sample_bed_dip_direction=float(er_sample_data[sample]['sample_bed_dip_direction'])
                    found_sample_bed_dip_direction=True
                if "sample_bed_dip" in er_sample_data[sample].keys() and er_sample_data[sample]['sample_bed_dip']!="":
                    sample_bed_dip=float(er_sample_data[sample]['sample_bed_dip'])
                    found_sample_bed_dip=True
            else:
                er_sample_data[sample]={}
            
            #--------------------
            # deal with specimen orientation and different coordinate system
            #--------------------

            found_s,found_geo,found_tilt=False,False,False
            if "dec_s" in meas_line.keys() and "inc_s" in meas_line.keys():
                found_s=True
                MagRec["measurement_dec"]=meas_line["dec_s"]
                MagRec["measurement_inc"]=meas_line["inc_s"]
            if "dec_g" in meas_line.keys() and "inc_g" in meas_line.keys():
                found_geo=True
            if "dec_t" in meas_line.keys() and "inc_t" in meas_line.keys():
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
                        print "-W- WARNING: delete core azimuth/plunge in er_samples.txt\n\
                        becasue dec_s and inc_s are unavaialable" 

            #-----------------------------                                                
            # specimen coordinates: no
            # geographic coordinates: no
            #-----------------------------                    
            if not found_geo and not found_s:
                print "-E- ERROR: sample %s does not have dec_s/inc_s or dec_g/inc_g. Ignore specimen %s "%(sample,specimen)
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
                        print "-E- ERROR in sample_azimuth sample %s. Check it! using the value in er_samples.txt"%sample
                        
                    if float(er_sample_data[sample]['sample_dip'])!= pl:
                        print "-E- ERROR in sample_dip sample %s. Check it! using the value in er_samples.txt"%sample
                    
            #-----------------------------                                                
            # specimen coordinates: yes
            # geographic coordinates: no
            #-----------------------------                    
            if not found_geo and found_s:
                if found_sample_dip and found_sample_azimuth:
                    pass
                    # (nothing to do)
                else:
                    print "-W- WARNING: missing sample_dip or sample_azimuth for sample %s"%sample

            #-----------------------------                                                
            # tilt-corrected coordinates: yes
            # geographic coordinates: no
            #-----------------------------                    
            if found_tilt and not found_geo:
                    print "-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data "%sample
            if found_tilt and found_geo:
                dec_geo,inc_geo=float(meas_line["dec_g"]),float(meas_line["inc_g"])
                dec_tilt,inc_tilt=float(meas_line["dec_t"]),float(meas_line["inc_t"])
                if dec_geo==dec_tilt and inc_geo==inc_tilt:
                    DipDir,Dip=0.,0. 
                else:
                    DipDir,Dip=pmag.get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt)
                    
                if not found_sample_bed_dip_direction or not found_sample_bed_dip:
                    print "-I- calculating dip and dip direction used for tilt correction sample %s. results are put in er_samples.txt"%sample
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
            if sample in er_sample_data.keys():
                er_sample_data[sample]['er_sample_name']=sample
                er_sample_data[sample]['er_site_name']=MagRec["er_site_name"]
                er_sample_data[sample]['er_location_name']=MagRec["er_location_name"]

            MagRec["magic_method_codes"]=LT
            MagRecs_this_specimen.append(MagRec)

            if LP!="" and LP not in this_specimen_LP:
                LP_this_specimen.append(LP)
            
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
                if "LT" in code:
                    LT=code;break            
            MagRec["magic_method_codes"]=LT+":"+":".join(LP_this_specimen)
        MagRecs.append(MagRec)   
                                


