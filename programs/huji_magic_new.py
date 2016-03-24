#!/usr/bin/env python
import sys
import pmagpy.pmag

def main(command_line=True, **kwargs):
    """

    NAME
        huji_magic_new.py
 
    DESCRIPTION
        converts HUJI new format files to magic_measurements format files

    SYNTAX
        huji_magic.py [command line options]

    OPTIONS
        -h: prints the help message and quits.
        -usr USER:   identify user, default is ""
        -f FILE: specify input file, required
        -F FILE: specify output file, default is magic_measurements.txt
        -LP [colon delimited list of protocols, include all that apply]
            AF:  af demag
            T: thermal including thellier but not trm acquisition
            N: NRM only
            TRM: trm acquisition
            ANI: anisotropy experiment
            CR: cooling rate experiment.
                The treatment coding of the measurement file should be: XXX.00,XXX.10, XXX.20 ...XX.70 etc. (XXX.00 is optional)
                where XXX in the temperature and .10,.20... are running numbers of the cooling rates steps.
                XXX.00 is optional zerofield baseline. XXX.70 is alteration check.
                syntax in sio_magic is: -LP CR xxx,yyy,zzz,.....xx
                where xx, yyy,zzz...xxx  are cooling time in [K/minutes], seperated by comma, ordered at the same order as XXX.10,XXX.20 ...XX.70
                if you use a zerofield step then no need to specify the cooling rate for the zerofield
            
        -spc NUM : specify number of characters to designate a  specimen, default = 0
        -loc LOCNAME : specify location/study name, must have either LOCNAME or SAMPFILE or be a synthetic
        -dc B PHI THETA: dc lab field (in micro tesla) and phi,theta, default is none
              NB: use PHI, THETA = -1 -1 to signal that it changes, i.e. in anisotropy experiment
        # to do! -ac B : peak AF field (in mT) for ARM acquisition, default is none
        -ncn NCON:  specify naming convention: default is #1 below
        
       Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column -- NOT CURRENTLY SUPPORTED
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.
 
            [8] synthetic - has no site name
            [9] ODP naming convention 
    INPUT
        separate experiments ( AF, thermal, thellier, trm aquisition) should be seperate  files
        (eg. af.txt, thermal.txt, etc.)

        HUJI masurement file format  (space delimited text):   
        Spec lab-running-numbe-code  Date Hour Treatment-type(T/N/A) Treatment(XXX.XX) dec(geo) inc(geo) dec(tilt) inc(tilt)

        ---------

        conventions:
        Spec: specimen name
        Treat:  treatment step
            XXX T in Centigrade
            XXX AF in mT
            for special experiments:
              Thellier:
                XXX.0  first zero field step
                XXX.1  first in field step [XXX.0 and XXX.1 can be done in any order]
                XXX.2  second in-field step at lower temperature (pTRM check)

              ATRM:
                X.00 optional baseline
                X.1 ATRM step (+X)
                X.2 ATRM step (+Y)
                X.3 ATRM step (+Z)
                X.4 ATRM step (-X)
                X.5 ATRM step (-Y)
                X.6 ATRM step (-Z)
                X.7 optional alteration check (+X)

              TRM:
                XXX.YYY  XXX is temperature step of total TRM
                         YYY is dc field in microtesla
         
         Intensity assumed to be total moment in 10^3 Am^2 (emu)
         Declination:  Declination in specimen coordinate system
         Inclination:  Inclination in specimen coordinate system

         Optional metatdata string:  mm/dd/yy;hh:mm;[dC,mT];xx.xx;UNITS;USER;INST;NMEAS
             hh in 24 hours.  
             dC or mT units of treatment XXX (see Treat above) for thermal or AF respectively
             xx.xxx   DC field
             UNITS of DC field (microT, mT)
             INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes, 
                    measured in four positions)
             NMEAS: number of measurements in a single position (1,3,200...)
     
    """
    # initialize some variables
    mag_file = ''
    meas_file="magic_measurements.txt"
    user=""
    specnum = 0
    samp_con = '1'
    labfield = 0
    er_location_name = ''
    codelist = None

    # get command line args
    if command_line:
        args=sys.argv
        if "-h" in args:
            print main.__doc__
            return False
        if "-usr" in args:
            ind=args.index("-usr")
            user=args[ind+1]
        else:
            user=""
        if '-F' in args:
            ind=args.index("-F")
            meas_file=args[ind+1]
        if '-f' in args:
            ind=args.index("-f")
            magfile=args[ind+1]
            print "got magfile:", magfile
        if "-dc" in args:
            ind=args.index("-dc")
            labfield=float(args[ind+1])*1e-6
            phi=float(args[ind+2])
            theta=float(args[ind+3])
        if "-ac" in args:
            ind=args.index("-ac")
            peakfield=float(args[ind+1])*1e-3
        if "-spc" in args:
            ind=args.index("-spc")
            specnum=int(args[ind+1])
        if "-loc" in args:
            ind=args.index("-loc")
            er_location_name=args[ind+1]
        if "-ncn" in args:
            ind=args.index("-ncn")
            samp_con=sys.argv[ind+1]
        if '-LP' in args:
            ind=args.index("-LP")
            codelist=args[ind+1]



        # lab process:

    # unpack key-word args if used as module
    if not command_line:
        user = kwargs.get('user', '')
        meas_file = kwargs.get('meas_file', 'magic_measurements.txt')
        magfile = kwargs.get('magfile', '')
        specnum = int(kwargs.get('specnum', 0))
        labfield = int(kwargs.get('labfield', 0)) *1e-3
        phi = int(kwargs.get('phi', 0))
        theta = int(kwargs.get('theta', 0))
        peakfield = kwargs.get('peakfield', 0)
        if peakfield:
            peakfield = float(peakfield)*1e-3
        er_location_name = kwargs.get('er_location_name', '')
        samp_con = kwargs.get('samp_con', '1')
        codelist = kwargs.get('codelist', '')
        CR_cooling_times=kwargs.get('CR_cooling_times', None)

    # format and validate variables
    if magfile:
        try:
            input=open(magfile,'rU')
        except:
            print "bad mag file name"
            return False, "bad mag file name"
    else: 
        print "mag_file field is required option"
        print main.__doc__
        return False, "mag_file field is required option"
                              
    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print "option [4] must be in form 4-Z where Z is an integer"
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="7"

    if codelist:
        codes=codelist.split(':')
    else:
        print "Must select experiment type (-LP option)"
        return False, "Must select experiment type (-LP option)"
    if "AF" in codes:
        demag='AF' 
        LPcode="LP-DIR-AF"
    if "T" in codes:
        demag="T"
        if not labfield: LPcode="LP-DIR-T"
        if labfield: LPcode="LP-PI-TRM"
        if "ANI" in codes:
            if not labfield:
                print "missing lab field option"
                return False, "missing lab field option"
            LPcode="LP-AN-TRM"

    if "TRM" in codes: 
        demag="T"
        LPcode="LP-TRM"
        #trm=1
                              
    if "CR" in codes:
        demag="T"
        # dc should be in the code
        if not labfield:
            print "missing lab field option"
            return False, "missing lab field option"

        LPcode="LP-TRM-CR" # TRM in different cooling rates
        if command_line:
            ind=args.index("-LP")
            CR_cooling_times=args[ind+2].split(",")


        #print CR_cooling_time ,"CR_cooling_time"

    version_num=pmag.get_version()

    MagRecs=[]
    
    #--------------------------------------
    # Read the file
    # Assumption:
    # 1. different lab protocolsa are in different files
    # 2. measurements are in the correct order
    #--------------------------------------

    Data={}

    line_no=0

    for line in input.readlines():
        line_no+=1
        this_line_data={}
        line_no+=1
        instcode=""
        if len(line)<2:
            continue
        if line[0]=="#": #HUJI way of marking bad data points
            continue
        
        rec=line.strip('\n').split()
        specimen=rec[0]
        date=rec[2].split("/")
        hour=rec[3].split(":")
        treatment_type=rec[4]
        treatment=rec[5].split(".")
        dec_core=rec[6]
        inc_core=rec[7]
        dec_geo=rec[8]
        inc_geo=rec[9]
        dec_tilted=rec[10]
        inc_tilted=rec[11]
        moment_emu=float(rec[12])

        if specimen not in Data.keys():
            Data[specimen]=[]
            
        # check duplicate treatments:
        # if yes, delete the first and use the second

        if len(Data[specimen])>0:
            if treatment==Data[specimen][-1]['treatment']:
                del(Data[specimen][-1])
                print "-W- Identical treatments in file %s magfile line %i: specimen %s, treatment %s ignoring the first. " %(magfile, line_no, specimen,".".join(treatment))

        this_line_data={}
        this_line_data['specimen']=specimen
        this_line_data['date']=date
        this_line_data['hour']=hour
        this_line_data['treatment_type']=treatment_type
        this_line_data['treatment']=treatment
        this_line_data['dec_core']=dec_core
        this_line_data['inc_core']=inc_core
        this_line_data['dec_geo']=dec_geo
        this_line_data['inc_geo']=inc_geo
        this_line_data['dec_tilted']=dec_tilted
        this_line_data['inc_tilted']=inc_tilted
        this_line_data['moment_emu']=moment_emu                                     
        Data[specimen].append(this_line_data)

        
    print "-I- done reading file %s"%magfile

    #--------------------------------------
    # Convert to MagIC
    #--------------------------------------
    
    specimens_list=Data.keys()
    specimens_list.sort()


    MagRecs=[]
    for specimen in  specimens_list:
        for i in range(len(Data[specimen])):
            this_line_data=Data[specimen][i]
            methcode=""
            MagRec={}
            MagRec["er_specimen_name"]=this_line_data['specimen']
            if specnum!=0:
                MagRec["er_sample_name"]=this_line_data['specimen'][:specnum]
            else:
                MagRec["er_sample_name"]=this_line_data['specimen']

            if samp_con=="1":
                MagRec["er_site_name"]=MagRec["er_sample_name"][:-1]
            elif samp_con=="2":
                parts=MagRec["er_sample_name"].split('-')
                MagRec["er_site_name"]= parts[0]
            elif samp_con=="3":
                parts=MagRec["er_sample_name"].split('.')
                MagRec["er_site_name"]= parts[0]
            elif samp_con=='4':
                MagRec["er_site_name"]=MagRec["er_sample_name"][0:-Z]
            elif samp_con=='5':
                MagRec["er_site_name"]=MagRec["er_sample_name"]
            elif samp_con=='7':
                MagRec["er_site_name"]=MagRec["er_sample_name"][0:Z]                
            else:
                MagRec["er_site_name"]=MagRec["er_sample_name"] # site=sample by default
            
            if er_location_name:
                MagRec['er_location_name']=er_location_name
            else:
                MagRec['er_location_name']=MagRec["er_site_name"]
                
            MagRec["measurement_temp"]='%8.3e' % (273) # room temp in kelvin
            MagRec["measurement_magn_moment"]='%10.3e'% (float(this_line_data['moment_emu'])*1e-3) # moment in Am^2 (from emu)
            MagRec["measurement_dec"]=this_line_data['dec_core']
            MagRec["measurement_inc"]=this_line_data['inc_core']
            date=this_line_data['date']
            hour=this_line_data['hour']    

            if float(date[2])>80:
                yyyy="19"+date[2]
            else:
                yyyy="20"+date[2]
            if len (date[0])==1:
                date[0]="0"+date[0]
            if len (date[1])==1:
                date[1]="0"+date[1]
            MagRec["measurement_date"]=":".join([yyyy,date[0],date[1],hour[0],hour[1],"00.00"])
            MagRec["measurement_time_zone"]='JER'
            MagRec['er_analyst_mail_names'] =user         
            MagRec["er_citation_names"]="This study"
            MagRec["magic_instrument_codes"]="HUJI-2G"
            MagRec["measurement_flag"]="g"
            MagRec["measurement_positions"]="1"
            MagRec["measurement_positions"]="1"
            MagRec["measurement_standard"]="u"
            MagRec["measurement_description"]=""
            #MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
            
            #----------------------------------------            
            # AF demag
            # do not support AARM yet
            #----------------------------------------
            
            if demag=="AF":
                
                # demag in zero field
                if LPcode != "LP-AN-ARM":
                    MagRec["treatment_ac_field"]='%8.3e' %(float(this_line_data['treatment'][0])*1e-3) # peak field in tesla
                    MagRec["treatment_dc_field"]='0'
                    MagRec["treatment_dc_field_phi"]='0'
                    MagRec["treatment_dc_field_theta"]='0'
                    if treatment_type=="N":
                        methcode="LP-DIR-AF:LT-NO"
                    elif treatment_type=="A":
                        methcode="LP-DIR-AF:LT-AF-Z"
                    else:
                        print "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                                            
                # AARM experiment    
                else:
                    print "Dont supprot AARM in HUJI format yet. sorry... do be DONE"
                MagRec["magic_method_codes"]=methcode
                MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                MagRec["measurement_number"]="%i"%i
                MagRec["measurement_description"]=""

                MagRecs.append(MagRec)
                                
            #----------------------------------------
            # Thermal:  
            # Thellier experiment: "IZ", "ZI", "IZZI", pTRM checks
            # Thermal demag
            # Thermal cooling rate experiment
            # Thermal NLT
            #----------------------------------------


            if demag=="T": 

                treatment=this_line_data['treatment']
                treatment_type=this_line_data['treatment_type']
                
                    
                #----------------------------------------
                # Thellier experimet
                #----------------------------------------

                if LPcode == "LP-PI-TRM"  : # Thelllier experiment

                    

                    MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                    methcode=LPcode        
                    
                    if treatment_type=="N" or ( (treatment[1]=='0' or  treatment[1]=='00') and float(treatment[0])==0):
                            LT_code="LT-NO"
                            MagRec["treatment_dc_field_phi"]='0' 
                            MagRec["treatment_dc_field_theta"]='0' 
                            MagRec["treatment_dc_field"]='0'
                            MagRec["treatment_temp"]='273.'
                                                                  
                    elif treatment[1]=='0' or  treatment[1]=='00':
                            LT_code="LT-T-Z"
                            MagRec["treatment_dc_field_phi"]='0' 
                            MagRec["treatment_dc_field_theta"]='0' 
                            MagRec["treatment_dc_field"]='%8.3e'%(0)
                            MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

                            # check if this is ZI or IZ:
                            #  check if the same temperature already measured:
                            methcode="LP-PI-TRM:LP-PI-TRM-ZI"
                            for j in range (0,i):
                                if Data[specimen][j]['treatment'][0] == treatment[0]:
                                    if Data[specimen][j]['treatment'][1] == '1' or Data[specimen][j]['treatment'][1] == '10':
                                        methcode="LP-PI-TRM:LP-PI-TRM-IZ"
                                    else:
                                        methcode="LP-PI-TRM:LP-PI-TRM-ZI"
                                                                               
                                    
                    elif treatment[1]=='1' or  treatment[1]=='10':
                            LT_code="LT-T-I"
                            MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                            MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                            MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                            MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

                            # check if this is ZI or IZ:
                            #  check if the same temperature already measured:
                            methcode="LP-PI-TRM:LP-PI-TRM-IZ"
                            for j in range (0,i):
                                if Data[specimen][j]['treatment'][0] == treatment[0]:
                                    if Data[specimen][j]['treatment'][1] == '0' or Data[specimen][j]['treatment'][1] == '00':
                                        methcode="LP-PI-TRM:LP-PI-TRM-ZI"
                                    else:
                                        methcode="LP-PI-TRM:LP-PI-TRM-IZ"
                            
                    elif treatment[1]=='2' or  treatment[1]=='20':
                            LT_code="LT-PTRM-I"
                            MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                            MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                            MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                            MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                            methcode="LP-PI-TRM:LP-PI-TRM-IZ"

                    else:
                            print "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                            return False, "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                    
                    MagRec["magic_method_codes"]=LT_code+":"+methcode
                    MagRec["measurement_number"]="%i"%i            
                    MagRec["measurement_description"]=""
                    MagRecs.append(MagRec)
                    #continue
                    
                                            
                #----------------------------------------
                # demag experimet
                #----------------------------------------


                if LPcode == "LP-DIR-T"  :
                    MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                    methcode=LPcode        
                    
                    if treatment_type=="N":
                        LT_code="LT-NO"
                    else:
                        LT_code="LT-T-Z"
                                            
                        methcode=LPcode+":"+"LT-T-Z"
                    MagRec["treatment_dc_field_phi"]='0' 
                    MagRec["treatment_dc_field_theta"]='0' 
                    MagRec["treatment_dc_field"]='%8.3e'%(0)
                    MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                    MagRec["magic_method_codes"]=LT_code+":"+methcode
                    MagRec["measurement_number"]="%i"%i            
                    MagRec["measurement_description"]=""
                    MagRecs.append(MagRec)
                    #continue
                        

                #----------------------------------------
                # ATRM measurements
                # The direction of the magnetization is used to determine the
                # direction of the lab field.
                #----------------------------------------
                

                if LPcode =="LP-AN-TRM" :
                    
                    MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                    methcode=LPcode        

                    if float(treatment[1])==0:
                        MagRec["magic_method_codes"]="LP-AN-TRM:LT-T-Z"
                        MagRec["treatment_dc_field_phi"]='0'
                        MagRec["treatment_dc_field_theta"]='0'
                        MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                        MagRec["treatment_dc_field"]='0'
                    else:
                        if float(treatment[1])==7:
                            # alteration check
                            methcode="LP-AN-TRM:LT-PTRM-I"
                            MagRec["measurement_number"]='7'# -z
                        else:    
                            MagRec["magic_method_codes"]="LP-AN-TRM:LT-T-I"
                            inc=float(MagRec["measurement_inc"]);dec=float(MagRec["measurement_dec"])
                            if abs(inc)<45 and (dec<45 or dec>315): # +x
                                tdec,tinc=0,0
                                MagRec["measurement_number"]='1'
                            if abs(inc)<45 and (dec<135 and dec>45):
                                tdec,tinc=90,0
                                MagRec["measurement_number"]='2' # +y
                            if inc>45 :
                                tdec,tinc=0,90
                                MagRec["measurement_number"]='3' # +z
                            if abs(inc)<45 and (dec<225 and dec>135):
                                tdec,tinc=180,0
                                MagRec["measurement_number"]='4' # -x
                            if abs(inc)<45 and (dec<315 and dec>225):
                                tdec,tinc=270,0
                                MagRec["measurement_number"]='5'# -y
                            if inc<-45 :
                                tdec,tinc=0,-90
                                MagRec["measurement_number"]='6'# -z
                        
                        MagRec["treatment_dc_field_phi"]='%7.1f' %(tdec)
                        MagRec["treatment_dc_field_theta"]='%7.1f'% (tinc)
                        MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                        MagRec["treatment_dc_field"]='%8.3e'%(labfield)
                    MagRec["measurement_description"]=""
                    MagRecs.append(MagRec)
                    #continue

                #----------------------------------------
                # NLT measurements
                # or TRM acquisistion experiment
                #----------------------------------------

                
                if LPcode == "LP-TRM"  :
                    MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                    MagRec["magic_method_codes"]="LP-TRM:LT-T-I"
                    if float(treatment[1])==0:
                        labfield=0
                    else:
                        labfield=float(float(treatment[1]))*1e-6
                    MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin                
                    MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    MagRec["measurement_number"]="%i"%i            
                    MagRec["measurement_description"]=""
                    MagRecs.append(MagRec)
                    #continue
    

                #----------------------------------------
                # Cooling rate experiments
                #----------------------------------------
                
                if  LPcode =="LP-TRM-CR":
                    index=int(treatment[1][0])
                    #print index,"index"
                    #print CR_cooling_times,"CR_cooling_times"
                    #print CR_cooling_times[index-1]
                    #print CR_cooling_times[0:index-1]
                    CR_cooling_time=CR_cooling_times[index-1]
                    if CR_cooling_time in CR_cooling_times[0:index-1]:
                        MagRec["magic_method_codes"]="LP-TRM-CR"+":" +"LT-PTRM-I"
                    else:    
                        MagRec["magic_method_codes"]="LP-TRM-CR"
                    MagRec["magic_experiment_name"]=specimen+ ":" + LPcode
                    MagRec["treatment_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin                
                    MagRec["treatment_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MagRec["treatment_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MagRec["treatment_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    MagRec["measurement_number"]="%i"%index
                    MagRec["measurement_description"]="%i minutes cooling time"%int(CR_cooling_time)
                    MagRecs.append(MagRec)
                    #continue

    
    pmag.magic_write(meas_file,MagRecs,'magic_measurements')
    print "-I- results put in ",meas_file
    return True, meas_file

def do_help():
    return main.__doc__

if __name__ == "__main__":
    main()
