#!/usr/bin/env python
"""

NAME
    huji_magic.py

DESCRIPTION
    converts HUJI format files to magic_measurements format files

SYNTAX
    huji_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is ""
    -ID: directory for input file if not included in -f flag
    -f FILE: specify infile file, required
    -fd FILE: specify HUJI datafile with sample orientations
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt
    -Fsi FILE: specify output sites.txt file, default is sites.txt
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -A: don't average replicate measurements
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

    -spc NUM : specify number of characters to designate a specimen, default = 0
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
         INST:  instrument code, number of axes, number of positions (e.g., G34 is 2G, three axes, measured in four positions)
         NMEAS: number of measurements in a single position (1,3,200...)
"""
from __future__ import print_function
from builtins import range
import sys,os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
import pytz, datetime

def convert(**kwargs):

    user = kwargs.get('user', '')
    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # Loc outfile
    magfile = kwargs.get('magfile', '')
    datafile = kwargs.get('datafile', '')
    specnum = int(kwargs.get('specnum', 0))
    labfield = int(kwargs.get('labfield', 0)) *1e-6
    phi = int(kwargs.get('phi', 0))
    theta = int(kwargs.get('theta', 0))
    peakfield = kwargs.get('peakfield', 0)
    if peakfield:
        peakfield = float(peakfield)*1e-3
    location = kwargs.get('location', '')
    samp_con = kwargs.get('samp_con', '1')
    codelist = kwargs.get('codelist', '')
    CR_cooling_times = kwargs.get('CR_cooling_times', None)
    noave = kwargs.get('noave', False)

    # format and validate variables
    if magfile:
        try:
            infile=open(os.path.join(input_dir_path,magfile),'r')
        except IOError:
            print("bad mag file name")
            return False, "bad mag file name"
    else:
        print("mag_file field is required option")
        print(__doc__)
        return False, "mag_file field is required option"

    if specnum!=0:
        specnum=-specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=int(samp_con.split("-")[1])
            samp_con="7"
    else: Z=1

    if codelist:
        codes=codelist.split(':')
    else:
        print("Must select experiment type (-LP option)")
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
                print("missing lab field option")
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
            print("missing lab field option")
            return False, "missing lab field option"

        LPcode="LP-CR-TRM" # TRM in different cooling rates
        if command_line:
            ind=sys.argv.index("-LP")
            CR_cooling_times=sys.argv[ind+2].split(",")

    version_num=pmag.get_version()

    #--------------------------------------
    # Read the file
    # Assumption:
    # 1. different lab protocolsa are in different files
    # 2. measurements are in the correct order
    #--------------------------------------

    Data={}
    line_no=0
    for line in infile.readlines():
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
        moment_emu=float(rec[-1])

        if specimen not in list(Data.keys()):
            Data[specimen]=[]

        # check duplicate treatments:
        # if yes, delete the first and use the second

        if len(Data[specimen])>0:
            if treatment==Data[specimen][-1]['treatment']:
                del(Data[specimen][-1])
                print("-W- Identical treatments in file %s magfile line %i: specimen %s, treatment %s ignoring the first. " %(magfile, line_no, specimen,".".join(treatment)))

        this_line_data={}
        this_line_data['specimen']=specimen
        this_line_data['date']=date
        this_line_data['hour']=hour
        this_line_data['treatment_type']=treatment_type
        this_line_data['treatment']=treatment
        this_line_data['dec_core']=dec_core
        this_line_data['inc_core']=inc_core
        this_line_data['moment_emu']=moment_emu
        this_line_data['azimuth']=''
        this_line_data['dip']=''
        this_line_data['bed_dip_direction']=''
        this_line_data['bed_dip']=''
        this_line_data['lat']=''
        this_line_data['lon']=''
        this_line_data['volume']=''
        Data[specimen].append(this_line_data)
    infile.close()
    print("-I- done reading file %s"%magfile)

    if datafile:
        dinfile = open(datafile)
        for line in dinfile.readlines():
            data = line.split()
            if len(data)<8 or data[0]=='': continue
            elif data[0] in list(Data.keys()):
                for i in range(len(Data[data[0]])):
                    Data[data[0]][i]['azimuth'] = data[1]
                    Data[data[0]][i]['dip'] = data[2]
                    try: Data[data[0]][i]['bed_dip_direction'] = float(data[3])+90
                    except ValueError: Data[data[0]][i]['bed_dip_direction'] = ''
                    Data[data[0]][i]['bed_dip'] = data[4]
                    Data[data[0]][i]['lat'] = data[5]
                    Data[data[0]][i]['lon'] = data[6]
                    Data[data[0]][i]['volume'] = data[7]
            else:
                print("no specimen %s found in magnetometer data file when reading specimen orientation data file, or data file record for specimen too short"%data[0])
        dinfile.close()

    #--------------------------------------
    # Convert to MagIC
    #--------------------------------------

    specimens_list=list(Data.keys())
    specimens_list.sort()

    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    for specimen in specimens_list:
        for i in range(len(Data[specimen])):
            this_line_data=Data[specimen][i]
            methcode=""
            MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
            specimen=this_line_data['specimen']
            if specnum!=0:
                sample=this_line_data['specimen'][:specnum]
            else:
                sample=this_line_data['specimen']
            site=pmag.parse_site(sample,samp_con,Z)
            if not location:
                location=site
            if specimen!="" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRecs.append(SpecRec)
            if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['azimuth'] = this_line_data['azimuth']
                SampRec['dip'] = this_line_data['dip']
                SampRec['bed_dip_direction'] = this_line_data['bed_dip_direction']
                SampRec['bed_dip'] = this_line_data['bed_dip']
                SampRecs.append(SampRec)
            if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = this_line_data['lat']
                SiteRec['lon'] = this_line_data['lon']
                SiteRecs.append(SiteRec)
            if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location']=location
                LocRec['lat_n'] = this_line_data['lat']
                LocRec['lon_e'] = this_line_data['lon']
                LocRec['lat_s'] = this_line_data['lat']
                LocRec['lon_w'] = this_line_data['lon']
                LocRecs.append(LocRec)

            MeasRec['specimen'] = specimen
            MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
            MeasRec["magn_moment"]='%10.3e'% (float(this_line_data['moment_emu'])*1e-3) # moment in Am^2 (from emu)
            MeasRec["dir_dec"]=this_line_data['dec_core']
            MeasRec["dir_inc"]=this_line_data['inc_core']

            date=this_line_data['date']
            hour=this_line_data['hour']
            if len(date[2])<4 and float(date[2])>=70:
                yyyy="19"+date[2]
            elif len(date[2])<4 and float(date[2])<70:
                yyyy="20"+date[2]
            else: yyyy=date[2]
            if len (date[0])==1:
                date[0]="0"+date[0]
            if len (date[1])==1:
                date[1]="0"+date[1]
            dt=":".join([date[0],date[1],yyyy,hour[0],hour[1],"0"])
            local = pytz.timezone("America/New_York")
            naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp=utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"

            MeasRec['analysts']=user
            MeasRec["citations"]="This study"
            MeasRec["instrument_codes"]="HUJI-2G"
            MeasRec["quality"]="g"
            MeasRec["meas_n_orient"]="1"
            MeasRec["standard"]="u"
            MeasRec["description"]=""

            #----------------------------------------
            # AF demag
            # do not support AARM yet
            #----------------------------------------

            if demag=="AF":
                treatment_type=this_line_data['treatment_type']
                # demag in zero field
                if LPcode != "LP-AN-ARM":
                    MeasRec["treat_ac_field"]='%8.3e' %(float(this_line_data['treatment'][0])*1e-3) # peak field in tesla
                    MeasRec["treat_dc_field"]='0'
                    MeasRec["treat_dc_field_phi"]='0'
                    MeasRec["treat_dc_field_theta"]='0'
                    if treatment_type=="N":
                        methcode="LP-DIR-AF:LT-NO"
                    elif treatment_type=="A":
                        methcode="LP-DIR-AF:LT-AF-Z"
                    else:
                        print("ERROR in treatment field line %i... exiting until you fix the problem" %line_no)
                        print(this_line_data)
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                # AARM experiment
                else:
                    print("Dont supprot AARM in HUJI format yet. sorry... do be DONE")
                MeasRec["method_codes"]=methcode
                MeasRec["experiments"]=specimen+ ":" + LPcode
                MeasRec["treat_step_num"]="%i"%i
                MeasRec["description"]=""

                MeasRecs.append(MeasRec)

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
                    MeasRec["experiments"]=specimen+ ":" + LPcode
                    methcode=LPcode
                    if treatment_type=="N" or ( (treatment[1]=='0' or  treatment[1]=='00') and float(treatment[0])==0):
                            LT_code="LT-NO"
                            MeasRec["treat_dc_field_phi"]='0'
                            MeasRec["treat_dc_field_theta"]='0'
                            MeasRec["treat_dc_field"]='0'
                            MeasRec["treat_temp"]='273.'

                    elif treatment[1]=='0' or  treatment[1]=='00':
                            LT_code="LT-T-Z"
                            MeasRec["treat_dc_field_phi"]='0'
                            MeasRec["treat_dc_field_theta"]='0'
                            MeasRec["treat_dc_field"]='%8.3e'%(0)
                            MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

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
                            MeasRec["treat_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                            MeasRec["treat_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                            MeasRec["treat_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                            MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin

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
                            MeasRec["treat_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                            MeasRec["treat_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                            MeasRec["treat_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                            MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                            methcode="LP-PI-TRM:LP-PI-TRM-IZ"

                    else:
                            print("ERROR in treatment field line %i... exiting until you fix the problem" %line_no)
                            return False, "ERROR in treatment field line %i... exiting until you fix the problem" %line_no
                    MeasRec["method_codes"]=LT_code+":"+methcode
                    MeasRec["treat_step_num"]="%i"%i
                    MeasRec["description"]=""
                    MeasRecs.append(MeasRec)

                #----------------------------------------
                # demag experimet
                #----------------------------------------

                if LPcode == "LP-DIR-T"  :
                    MeasRec["experiments"]=specimen+ ":" + LPcode
                    methcode=LPcode
                    if treatment_type=="N":
                        LT_code="LT-NO"
                    else:
                        LT_code="LT-T-Z"
                        methcode=LPcode+":"+"LT-T-Z"
                    MeasRec["treat_dc_field_phi"]='0'
                    MeasRec["treat_dc_field_theta"]='0'
                    MeasRec["treat_dc_field"]='%8.3e'%(0)
                    MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                    MeasRec["method_codes"]=LT_code+":"+methcode
                    MeasRec["treat_step_num"]="%i"%i
                    MeasRec["description"]=""
                    MeasRecs.append(MeasRec)
                    #continue

                #----------------------------------------
                # ATRM measurements
                # The direction of the magnetization is used to determine the
                # direction of the lab field.
                #----------------------------------------

                if LPcode =="LP-AN-TRM":
                    MeasRec["experiments"]=specimen+ ":" + LPcode
                    methcode=LPcode

                    if float(treatment[1])==0:
                        MeasRec["method_codes"]="LP-AN-TRM:LT-T-Z"
                        MeasRec["treat_dc_field_phi"]='0'
                        MeasRec["treat_dc_field_theta"]='0'
                        MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                        MeasRec["treat_dc_field"]='0'
                    else:
                        if float(treatment[1])==7:
                            # alteration check
                            methcode="LP-AN-TRM:LT-PTRM-I"
                            MeasRec["treat_step_num"]='7'# -z
                        else:
                            MeasRec["method_codes"]="LP-AN-TRM:LT-T-I"
                            inc=float(MeasRec["dir_inc"]);dec=float(MeasRec["dir_dec"])
                            if abs(inc)<45 and (dec<45 or dec>315): # +x
                                tdec,tinc=0,0
                                MeasRec["treat_step_num"]='1'
                            if abs(inc)<45 and (dec<135 and dec>45):
                                tdec,tinc=90,0
                                MeasRec["treat_step_num"]='2' # +y
                            if inc>45 :
                                tdec,tinc=0,90
                                MeasRec["treat_step_num"]='3' # +z
                            if abs(inc)<45 and (dec<225 and dec>135):
                                tdec,tinc=180,0
                                MeasRec["treat_step_num"]='4' # -x
                            if abs(inc)<45 and (dec<315 and dec>225):
                                tdec,tinc=270,0
                                MeasRec["treat_step_num"]='5'# -y
                            if inc<-45 :
                                tdec,tinc=0,-90
                                MeasRec["treat_step_num"]='6'# -z

                        MeasRec["treat_dc_field_phi"]='%7.1f' %(tdec)
                        MeasRec["treat_dc_field_theta"]='%7.1f'% (tinc)
                        MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                        MeasRec["treat_dc_field"]='%8.3e'%(labfield)
                    MeasRec["description"]=""
                    MeasRecs.append(MeasRec)
                    #continue

                #----------------------------------------
                # NLT measurements
                # or TRM acquisistion experiment
                #----------------------------------------

                if LPcode == "LP-TRM"  :
                    MeasRec["experiments"]=specimen+ ":" + LPcode
                    MeasRec["method_codes"]="LP-TRM:LT-T-I"
                    if float(treatment[1])==0:
                        labfield=0
                    else:
                        labfield=float(float(treatment[1]))*1e-6
                    MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                    MeasRec["treat_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MeasRec["treat_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    MeasRec["treat_step_num"]="%i"%i
                    MeasRec["description"]=""
                    MeasRecs.append(MeasRec)
                    #continue

                #----------------------------------------
                # Cooling rate experiments
                #----------------------------------------

                if  LPcode =="LP-CR-TRM":
                    index=int(treatment[1][0])
                    #print index,"index"
                    #print CR_cooling_times,"CR_cooling_times"
                    #print CR_cooling_times[index-1]
                    #print CR_cooling_times[0:index-1]
                    if index==7 or index==70: # alteration check as final measurement
                            meas_type="LT-PTRM-I:LP-CR-TRM"
                            CR_cooling_time=CR_cooling_times[-1]
                    else:
                            meas_type="LT-T-I:LP-CR-TRM"
                            CR_cooling_time=CR_cooling_times[index-1]
                    MeasRec["method_codes"]=meas_type
                    MeasRec["experiments"]=specimen+ ":" + LPcode
                    MeasRec["treat_temp"]='%8.3e' % (float(treatment[0])+273.) # temp in kelvin
                    MeasRec["treat_dc_field"]='%8.3e' % (labfield) # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field_phi"]='%7.1f' % (phi) # labfield phi
                    MeasRec["treat_dc_field_theta"]='%7.1f' % (theta) # labfield theta
                    MeasRec["treat_step_num"]="%i"%index
                    MeasRec["description"]="cooling_rate"+":"+CR_cooling_time+":"+"K/min"
                    #MeasRec["description"]="%.1f minutes per cooling time"%int(CR_cooling_time)
                    MeasRecs.append(MeasRec)
                    #continue

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
        ind = sys.argv.index('-WD')
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv: # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['magfile']=sys.argv[ind+1]
    if '-fd' in sys.argv:
        ind=sys.argv.index("-fd")
        kwargs['datafile']=sys.argv[ind+1]
    if "-dc" in sys.argv:
        ind=sys.argv.index("-dc")
        kwargs['labfield']=float(sys.argv[ind+1])
        kwargs['phi']=float(sys.argv[ind+2])
        kwargs['theta']=float(sys.argv[ind+3])
    if "-ac" in sys.argv:
        ind=sys.argv.index("-ac")
        kwargs['peakfield']=float(sys.argv[ind+1])*1e-3
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if '-LP' in sys.argv:
        ind=sys.argv.index("-LP")
        kwargs['codelist']=sys.argv[ind+1]
    if '-A' in sys.argv:
        kwargs['noave']=True

    convert(**kwargs)

if __name__ == "__main__":
    main()
