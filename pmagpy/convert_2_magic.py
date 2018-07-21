#!/usr/bin/env/pythonw

import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from functools import reduce
import pytz
import datetime
import copy
import scipy
from past.utils import old_div


### _2g_bin_magic conversion

def _2g_bin(dir_path=".", mag_file="", meas_file='measurements.txt',
            spec_file="specimens.txt", samp_file="samples.txt", site_file="sites.txt",
            loc_file="locations.txt", or_con='3', specnum=0, samp_con='2', corr='1',
            gmeths="FS-FD:SO-POM", location="unknown", inst="", user="", noave=0, input_dir="",
            lat="", lon=""):

    def skip(N,ind,L):
        for b in range(N):
            ind+=1
            while L[ind]=="":ind+=1
        ind+=1
        while L[ind]=="":ind+=1
        return ind

    #
    # initialize variables
    #
    bed_dip,bed_dip_dir="",""
    sclass,lithology,_type="","",""
    DecCorr=0.
    months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

    # format and fix variables
    if specnum != 0:
        specnum = -specnum
    if input_dir:
        input_dir_path = input_dir
    else:
        input_dir_path = dir_path

    if samp_con:
        Z = 1
        if "4" in samp_con:
            if "-" not in samp_con:
                print("option [4] must be in form 4-Z where Z is an integer")
                return False, "option [4] must be in form 4-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print("option [7] must be in form 7-Z where Z is an integer")
                return False, "option [7] must be in form 7-Z where Z is an integer"
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
        if "6" in samp_con:
            print('Naming convention option [6] not currently supported')
            return False, 'Naming convention option [6] not currently supported'
            #Z=1
            #try:
            #    SampRecs,file_type=pmag.magic_read(os.path.join(input_dir_path, 'er_samples.txt'))
            #except:
            #    print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
            #    return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
            #if file_type == 'bad_file':
            #    print("there is no er_samples.txt file in your input directory - you can't use naming convention #6")
            #    return False, "there is no er_samples.txt file in your input directory - you can't use naming convention #6"
        #else: Z=1

    if not mag_file:
        print("mag file is required input")
        return False, "mag file is required input"
    output_dir_path = dir_path
    mag_file = os.path.join(input_dir_path, mag_file)

    samplist=[]
    try:
        SampRecs,file_type=pmag.magic_read(samp_file)
    except:
        SampRecs=[]
    MeasRecs,SpecRecs,SiteRecs,LocRecs=[],[],[],[]
    try:
        f=open(mag_file,'br')
        input=str(f.read()).strip("b '")
        f.close()
    except Exception as ex:
        print('ex', ex)
        print("bad mag file")
        return False, "bad mag file"
    firstline,date=1,""
    d=input.split('\\xcd')
    for line in d:
        rec=line.split('\\x00')
        if firstline==1:
            firstline=0
            spec,vol="",1
            el=51
            while line[el:el+1]!="\\": spec=spec+line[el];el+=1
            # check for bad sample name
            test=spec.split('.')
            date=""
            if len(test)>1:
                spec=test[0]
                kk=24
                while line[kk]!='\\x01' and line[kk]!='\\x00':
                    kk+=1
                vcc=line[24:kk]
                el=10
                while rec[el].strip()!='':el+=1
                date,comments=rec[el+7],[]
            else:
                el=9
                while rec[el]!='\\x01':el+=1
                vcc,date,comments=rec[el-3],rec[el+7],[]
            specname=spec.lower()
            print('importing ',specname)
            el+=8
            while rec[el].isdigit()==False:
                comments.append(rec[el])
                el+=1
            while rec[el]=="":el+=1
            az=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            pl=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            bed_dip_dir=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            bed_dip=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            if rec[el]=='\\x01':
                bed_dip=180.-bed_dip
                el+=1
                while rec[el]=="":el+=1
            fold_az=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            fold_pl=rec[el]
            el+=1
            while rec[el]=="":el+=1
            if rec[el]!="" and rec[el]!='\\x02' and rec[el]!='\\x01':
                deccorr=float(rec[el])
                az+=deccorr
                bed_dip_dir+=deccorr
                fold_az+=deccorr
                if bed_dip_dir>=360:bed_dip_dir=bed_dip_dir-360.
                if az>=360.:az=az-360.
                if fold_az>=360.:fold_az=fold_az-360.
            else:
                deccorr=0
            if specnum!=0:
                sample=specname[:specnum]
            else:
                sample=specname

            methods=gmeths.split(':')
            if deccorr!="0":
                if 'SO-MAG' in methods:del methods[methods.index('SO-MAG')]
                methods.append('SO-CMD-NORTH')
            meths = reduce(lambda x,y: x+':'+y, methods)
            method_codes=meths
            site=pmag.parse_site(sample,samp_con,Z) # parse out the site name
            SpecRec,SampRec,SiteRec,LocRec={},{},{},{}
            SpecRec["specimen"]=specname
            SpecRec["sample"]=sample
            if vcc.strip()!="":vol=float(vcc)*1e-6 # convert to m^3 from cc
            SpecRec["volume"]='%10.3e'%(vol) #
            SpecRec["geologic_classes"]=sclass
            SpecRec["lithologies"]=lithology
            SpecRec["geologic_types"]=_type
            SpecRecs.append(SpecRec)

            if sample!="" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec["sample"]=sample
                SampRec["site"]=site
                labaz,labdip=pmag.orient(az,pl,or_con) # convert to labaz, labpl
                SampRec["bed_dip"]='%7.1f'%(bed_dip)
                SampRec["bed_dip_direction"]='%7.1f'%(bed_dip_dir)
                SampRec["dip"]='%7.1f'%(labdip)
                SampRec["azimuth"]='%7.1f'%(labaz)
                SampRec["azimuth_dec_correction"]='%7.1f'%(deccorr)
                SampRec["geologic_classes"]=sclass
                SampRec["lithologies"]=lithology
                SampRec["geologic_types"]=_type
                SampRec["method_codes"]=method_codes
                SampRecs.append(SampRec)

            if site!="" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRec["geologic_classes"]=sclass
                SiteRec["lithologies"]=lithology
                SiteRec["geologic_types"]=_type
                SiteRecs.append(SiteRec)

            if location!="" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location']=location
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                #LocRec["geologic_classes"]=sclass
                #LocRec["lithologies"]=lithology
                #LocRec["geologic_types"]=_type
                LocRecs.append(LocRec)

        else:
            MeasRec={}
            MeasRec["treat_temp"]='%8.3e' % (273) # room temp in kelvin
            MeasRec["meas_temp"]='%8.3e' % (273) # room temp in kelvin
            MeasRec["treat_ac_field"]='0'
            MeasRec["treat_dc_field"]='0'
            MeasRec["treat_dc_field_phi"]='0'
            MeasRec["treat_dc_field_theta"]='0'
            meas_type="LT-NO"
            MeasRec["quality"]='g'
            MeasRec["standard"]='u'
            MeasRec["treat_step_num"]='1'
            MeasRec["specimen"]=specname
            el,demag=1,''
            treat=rec[el]
            if treat[-1]=='C':
                demag='T'
            elif treat!='NRM':
                demag='AF'
            el+=1
            while rec[el]=="":el+=1
            MeasRec["dir_dec"]=rec[el]
            cdec=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            MeasRec["dir_inc"]=rec[el]
            cinc=float(rec[el])
            el+=1
            while rec[el]=="":el+=1
            gdec=rec[el]
            el+=1
            while rec[el]=="":el+=1
            ginc=rec[el]
            el=skip(2,el,rec) # skip bdec,binc
#                el=skip(4,el,rec) # skip gdec,ginc,bdec,binc
#                print 'moment emu: ',rec[el]
            MeasRec["magn_moment"]='%10.3e'% (float(rec[el])*1e-3) # moment in Am^2 (from emu)
            MeasRec["magn_volume"]='%10.3e'% (float(rec[el])*1e-3/vol) # magnetization in A/m
            el=skip(2,el,rec) # skip to xsig
            MeasRec["magn_x_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el=skip(3,el,rec) # skip to ysig
            MeasRec["magn_y_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el=skip(3,el,rec) # skip to zsig
            MeasRec["magn_z_sigma"]='%10.3e'% (float(rec[el])*1e-3) # convert from emu
            el+=1 # skip to positions
            MeasRec["meas_n_orient"]=rec[el]
#                    el=skip(5,el,rec) # skip to date
#                    mm=str(months.index(date[0]))
#                    if len(mm)==1:
#                        mm='0'+str(mm)
#                    else:
#                        mm=str(mm)
#                    dstring=date[2]+':'+mm+':'+date[1]+":"+date[3]
#                    MeasRec['measurement_date']=dstring
            MeasRec["instrument_codes"]=inst
            MeasRec["analysts"]=user
            MeasRec["citations"]="This study"
            MeasRec["method_codes"]=meas_type
            if demag=="AF":
                MeasRec["treat_ac_field"]='%8.3e' %(float(treat[:-2])*1e-3) # peak field in tesla
                meas_type="LT-AF-Z"
                MeasRec["treat_dc_field"]='0'
            elif demag=="T":
                MeasRec["treat_temp"]='%8.3e' % (float(treat[:-1])+273.) # temp in kelvin
                meas_type="LT-T-Z"
            MeasRec['method_codes']=meas_type
            MeasRecs.append(MeasRec)

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts=pmag.measurements_methods3(MeasRecs,noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.write_table_to_file('specimens', custom_name=spec_file)
    con.write_table_to_file('samples', custom_name=samp_file)
    con.write_table_to_file('sites', custom_name=site_file)
    con.write_table_to_file('locations', custom_name=loc_file)
    con.write_table_to_file('measurements', custom_name=meas_file)
    return True, meas_file


###  CIT_magic conversion

def cit(dir_path=".", input_dir_path="", magfile="", user="", meas_file="measurements.txt",
            spec_file="specimens.txt", samp_file="samples.txt",
            site_file="sites.txt", loc_file="locations.txt", locname="unknown",
            sitename="", methods=['SO-MAG'], specnum=0, samp_con='3',
            norm='cc', oersted=False, noave=False, meas_n_orient='8',
            labfield=0, phi=0, theta=0):
    """
    Converts CIT formated Magnetometer data into MagIC format for Analysis and contribution to the MagIC database

    Parameters
    -----------
    dir_path : directory to output files to (default : current directory)
    user : colon delimited list of analysts (default : "")
    magfile : magnetometer file (.sam) to convert to MagIC (required)
    meas_file : measurement file name to output (default : measurements.txt)
    spec_file : specimen file name to output (default : specimens.txt)
    samp_file : sample file name to output (default : samples.txt)
    site_file : site file name to output (default : site.txt)
    loc_file : location file name to output (default : locations.txt)
    locname : location name
    methods : colon delimited list of sample method codes. full list here (https://www2.earthref.org/MagIC/method-codes) (default : SO-MAG
    specnum : number of terminal characters that identify a specimen
    norm : is volume or mass normalization using cgs or si units (options : cc,m3,g,kg) (default : cc)
    oersted : demag step vales are in Oersted
    noave : average measurement data or not. False is average, True is don't average. (default : False)
    samp_con : sample naming convention options as follows:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in sitename column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    input_dir_path : if you did not supply a full path with magfile you can put the directory the magfile is in here
    meas_n_orient : Number of different orientations in measurement (default : 8)
    labfield : DC_FIELD in microTesla (default : 0)
    phi : DC_PHI in degrees (default : 0)
    theta : DC_THETA in degrees (default : 0)

    Returns
    -----------
    type - Tuple : (True or False indicating if conversion was sucessful, meas_file name written)
    """

    def get_dc_params(FIRST_GET_DC, specimen, treat_type, yn):
        """
        Prompts user for DC field data if not provided, just an encapsulation function for the above program and should not be used elsewhere.

        Parameters
        -----------
        FIRST_GET_DC : is this the first time you are asking for DC data?
        specimen : what specimen do you want DC data for?
        treat_type : what kind of step was it? PTM, Tail, in field, zero field?
        yn : is DC field constant or varrying? (y = constant, n = varrying)

        Returns
        -----------
        GET_DC_PARAMS : weather or not to rerun this function
        FIRST_GET_DC : same as above
        yn : same as above
        DC_FIELD : field strength in Tesla
        DC_PHI : field azimuth
        DC_THETA : field polar angle
        """
        if FIRST_GET_DC:
            yn = input(
                "Is the DC field used in this IZZI study constant or does it varry between specimen or step? (y=const) [y/N]: ")
            FIRST_GET_DC = False
        if "y" == yn:
            DC_FIELD, DC_PHI, DC_THETA = list(map(float, eval(input(
                "What DC field, Phi, and Theta was used for all steps? (float (in microTesla),float,float): "))))
            GET_DC_PARAMS = False
        else:
            DC_FIELD, DC_PHI, DC_THETA = list(map(float, eval(input(
                "What DC field, Phi, and Theta was used for specimen %s and step %s? (float (in microTesla),float,float): " % (str(specimen), str(treat_type))))))
        return GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD*1e-6, DC_PHI, DC_THETA

    if not input_dir_path:
        try:
            input_dir_path = os.path.split(magfile)[0]
        except IndexError:
            input_dir_path = dir_path

    output_dir_path = dir_path
    try:
        DC_FIELD = float(labfield) * 1e-6
        DC_PHI = float(phi)
        DC_THETA = float(theta)
    except ValueError:
        raise ValueError(
            'problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')
    yn = ''
    if DC_FIELD == 0 and DC_PHI == 0 and DC_THETA == 0:
        print('-I- Required values for labfield, phi, and theta not provided!  Will try to get these interactively')
        GET_DC_PARAMS = True
    else:
        GET_DC_PARAMS = False
    if locname == '' or locname == None:
        locname = 'unknown'
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = samp_con.split("-")[1]
            samp_con = "7"
    else:
        Z = 1

    # get file names and open magfile to start reading data
    if input_dir_path == '':
        input_dir_path = '.'
    magfile = os.path.join(input_dir_path, magfile)
    FIRST_GET_DC = True
    try:
        file_input = open(magfile, 'r')
    except IOError as ex:
        print(("bad sam file name: ", magfile))
        return False, "bad sam file name"
    File = file_input.readlines()
    file_input.close()
    if len(File) == 1:
        File = File[0].split('\r')
        File = [x+"\r\n" for x in File]

    # define initial variables
    SpecRecs, SampRecs, SiteRecs, LocRecs, MeasRecs = [], [], [], [], []
    sids, ln, format, citations = [], 0, 'CIT', "This study"
    formats = ['CIT', '2G', 'APP', 'JRA']

    if File[ln].strip() == 'CIT':
        ln += 1
    LocRec = {}
    LocRec["location"] = locname
    LocRec["citations"] = citations
    LocRec['analysts'] = user
    comment = File[ln]
    if comment == 'CIT':
        format = comment
        ln += 1
    comment = File[ln]
    print(comment)
    ln += 1
    specimens, samples, sites = [], [], []
    if format == 'CIT':
        line = File[ln].split()
        site_lat = line[0]
        site_lon = line[1]
        LocRec["lat_n"] = site_lat
        LocRec["lon_e"] = site_lon
        LocRec["lat_s"] = site_lat
        LocRec["lon_w"] = site_lon
        LocRecs.append(LocRec)
        Cdec = float(line[2])
        for k in range(ln+1, len(File)):
            line = File[k]
            rec = line.split()
            if rec == []:
                continue
            specimen = rec[0]
            specimens.append(specimen)
    for specimen in specimens:
        SpecRec, SampRec, SiteRec = {}, {}, {}
        if specnum != 0:
            sample = specimen[:specnum]
        else:
            sample = specimen
        if sitename:
            site = sitename
        else:
            site = pmag.parse_site(sample, samp_con, Z)
        SpecRec['specimen'] = specimen
        SpecRec['sample'] = sample
        SpecRec['citations'] = citations
        SpecRec['analysts'] = user
        SampRec['sample'] = sample
        SampRec['site'] = site
        SampRec['citations'] = citations
        SampRec['method_codes'] = methods
        SampRec['azimuth_dec_correction'] = '%7.1f' % (Cdec)
        SampRec['analysts'] = user
        SiteRec['site'] = site
        SiteRec['location'] = locname
        SiteRec['citations'] = citations
        SiteRec['lat'] = site_lat
        SiteRec['lon'] = site_lon
        SiteRec['analysts'] = user
        f = open(os.path.join(input_dir_path, specimen), 'r')
        Lines = f.readlines()
        f.close()
        comment = ""
        line = Lines[0].split()
        if len(line) > 2:
            comment = line[2]
        info = Lines[1].split()
        volmass = float(info[-1])
        if volmass == 1.0:
            print('Warning: Specimen volume set to 1.0.')
            print('Warning: If volume/mass really is 1.0, set volume/mass to 1.001')
            print('Warning: specimen method code LP-NOMAG set.')
            SpecRec['weight'] = ""
            SpecRec['volume'] = ""
            SpecRec['method_codes'] = 'LP-NOMAG'
        elif norm == "gm":
            SpecRec['volume'] = ''
            SpecRec['weight'] = '%10.3e' % volmass*1e-3
        elif norm == "kg":
            SpecRec['volume'] = ''
            SpecRec['weight'] = '%10.3e'*volmass
        elif norm == "cc":
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass*1e-6)
        elif norm == "m3":
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass)
        else:
            print('Warning: Unknown normalization unit ',
                  norm, '. Using default of cc')
            SpecRec['weight'] = ""
            SpecRec['volume'] = '%10.3e' % (volmass*1e-6)
        dip = float(info[-2])
        dip_direction = float(info[-3])+Cdec+90.
        sample_dip = -float(info[-4])
        sample_azimuth = float(info[-5])+Cdec-90.
        if len(info) > 5:
            SampRec['height'] = info[-6]
        else:
            SampRec['height'] = '0'
        SampRec['azimuth'] = '%7.1f' % (sample_azimuth)
        SampRec['dip'] = '%7.1f' % (sample_dip)
        SampRec['bed_dip'] = '%7.1f' % (dip)
        SampRec['bed_dip_direction'] = '%7.1f' % (dip_direction)
        SampRec['geologic_classes'] = ''
        SampRec['geologic_types'] = ''
        SampRec['lithologies'] = ''
        if Cdec != 0 or Cdec != "":
            SampRec['method_codes'] = 'SO-CMD-NORTH'
        else:
            SampRec['method_codes'] = 'SO-MAG'
        for line in Lines[2:len(Lines)]:
            if line == '\n':
                continue
            MeasRec = SpecRec.copy()
            MeasRec.pop('sample')
            MeasRec['analysts'] = user
#           Remove volume and weight as they do not exits in the magic_measurement table
            del MeasRec["volume"]
            del MeasRec["weight"]
            # USGS files have blank for an AF demag value when measurement is the NRM. njarboe
            if line[0:6] == 'AF    ':
                line = 'NRM' + line[3:]
            treat_type = line[0:3]
            if treat_type[1] == '.':
                treat_type = 'NRM'
            treat = line[2:6]
            try:
                float(treat)
            except ValueError:
                treat = line[3:6]
                if treat.split() == '':
                    treat = '0'
                try:
                    float(treat)
                except ValueError:
                    treat = line.split()[1]
            if treat_type.startswith('NRM'):
                MeasRec['method_codes'] = 'LT-NO'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('LT') or treat_type.upper().startswith('LN2'):
                MeasRec['method_codes'] = 'LT-LT-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '77'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('AF') or treat_type.startswith('MAF'):
                MeasRec['method_codes'] = 'LT-AF-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field'] = '0'
                else:
                    try:
                        MeasRec['treat_ac_field'] = '%10.3e' % (
                            float(treat)*1e-3)
                    except ValueError as e:
                        print(os.path.join(input_dir_path, specimen))
                        raise e
                if MeasRec['treat_ac_field'] != '0':
                    MeasRec['treat_ac_field'] = '%10.3e' % (
                        float(MeasRec['treat_ac_field'])/10)
            elif treat_type.startswith('ARM'):
                MeasRec['method_codes'] = "LP-ARM"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field'] = '0'
                else:
                    MeasRec['method_codes'] = "LP-ARM-AFD"
                    MeasRec['treat_ac_field'] = '%10.3e' % (float(treat)*1e-3)
            elif treat_type.startswith('IRM'):
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = "LT-IRM"
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = '273'
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif treat_type.startswith('TT'):
                MeasRec['method_codes'] = 'LT-T-Z'
                MeasRec['meas_temp'] = '273'
                if treat.strip() == '':
                    MeasRec['treat_temp'] = '273'
                else:
                    MeasRec['treat_temp'] = '%7.1f' % (float(treat)+273)
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '0':  # assume decimal IZZI format 0 field thus can hardcode the dc fields
                MeasRec['method_codes'] = 'LT-T-Z'
                MeasRec['meas_temp'] = '273'
                try:
                    MeasRec['treat_temp'] = str(int(treat_type) + 273)
                except ValueError as e:
                    print(specimen)
                    raise e
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '1':  # assume decimal IZZI format in constant field
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-T-I'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '2':  # assume decimal IZZI format PTRM step
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-PTRM-I'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '%1.2e' % DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            elif line[4] == '3':  # assume decimal IZZI format PTRM tail check
                if GET_DC_PARAMS:
                    GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(
                        FIRST_GET_DC, specimen, treat_type, yn)
                MeasRec['method_codes'] = 'LT-PTRM-Z'
                MeasRec['meas_temp'] = '273'
                MeasRec['treat_temp'] = str(int(treat_type) + 273)
                MeasRec['treat_dc_field'] = '0'
                MeasRec['treat_dc_field_phi'] = '%1.2f' % DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f' % DC_THETA
                MeasRec['treat_ac_field'] = '0'
            else:
                print("trouble with your treatment steps")
            MeasRec['dir_dec'] = line[46:51]
            MeasRec['dir_inc'] = line[52:58]
#           Some MIT files have and extra digit in the exponent of the magnetude.
#           That makes those files not compliant with the cit measurement file spec.
#           Not sure if we should just print an error message and exit. For now we accept the file and fix it.
#           The first digit of the exponent, which should always be zero, is cut out of the line if column 39 is not ' '
            if line[39] != ' ':
                line = line[0:37] + line[38:]
            M = '%8.2e' % (float(line[31:39])*volmass*1e-3)  # convert to Am2
            MeasRec['magn_moment'] = M
            MeasRec['dir_csd'] = '%7.1f' % (eval(line[41:46]))
            MeasRec["meas_n_orient"] = meas_n_orient
            MeasRec['standard'] = 'u'
            if len(line) > 60:
                MeasRec['instrument_codes'] = line[85:].strip('\n \r \t "')
                MeasRec['magn_x_sigma'] = '%8.2e' % (
                    float(line[58:67])*1e-8)  # (convert e-5emu to Am2)
                MeasRec['magn_y_sigma'] = '%8.2e' % (float(line[67:76])*1e-8)
                MeasRec['magn_z_sigma'] = '%8.2e' % (float(line[76:85])*1e-8)
            MeasRecs.append(MeasRec)
        SpecRecs.append(SpecRec)
        if sample not in samples:
            samples.append(sample)
            SampRecs.append(SampRec)
        if site not in sites:
            sites.append(site)
            SiteRecs.append(SiteRec)

    con = nb.Contribution(output_dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(
        custom_name=spec_file, dir_path=output_dir_path)
    con.tables['samples'].write_magic_file(
        custom_name=samp_file, dir_path=output_dir_path)
    con.tables['sites'].write_magic_file(
        custom_name=site_file, dir_path=output_dir_path)
    con.tables['locations'].write_magic_file(
        custom_name=loc_file, dir_path=output_dir_path)
    con.tables['measurements'].write_magic_file(
        custom_name=meas_file, dir_path=output_dir_path)

    return True, meas_file


### generic_magic conversion

def generic(magfile="", dir_path=".", meas_file="measurements.txt",
            spec_file="specimens.txt", samp_file="samples.txt", site_file = "sites.txt",
            loc_file="locations.txt", user="", labfield=0, labfield_phi=0, labfield_theta=0,
            experiment="", cooling_times_list=[], sample_nc=[1, 0], site_nc=[1, 0],
            location="unknown", lat="", lon="", noave=False):

    # --------------------------------------
    # functions
    # --------------------------------------


    def sort_magic_file(path, ignore_lines_n, sort_by_this_name):
        '''
        reads a file with headers. Each line is stored as a dictionary following the headers.
        Lines are sorted in DATA by the sort_by_this_name header
        DATA[sort_by_this_name]=[dictionary1,dictionary2,...]
        '''
        DATA = {}
        fin = open(path, 'r')
        # ignore first lines
        for i in range(ignore_lines_n):
            fin.readline()
        # header
        line = fin.readline()
        header = line.strip('\n').split('\t')
        # print header
        for line in fin.readlines():
            if line[0] == "#":
                continue
            tmp_data = {}
            tmp_line = line.strip('\n').split('\t')
            # print tmp_line
            for i in range(len(tmp_line)):
                if i >= len(header):
                    continue
                tmp_data[header[i]] = tmp_line[i]
            DATA[tmp_data[sort_by_this_name]] = tmp_data
        fin.close()
        return(DATA)


    def read_generic_file(path, average_replicates):
        '''
        reads a generic file format. If average_replicates==True average replicate measurements.
        Rrturns a Data dictionary with measurements line sorted by specimen
        Data[specimen_name][dict1,dict2,...]
        '''
        Data = {}
        Fin = open(path, 'r')
        header = Fin.readline().strip('\n').split('\t')
        duplicates = []
        for line in Fin.readlines():
            tmp_data = {}
            # found_duplicate=False
            l = line.strip('\n').split('\t')
            for i in range(min(len(header), len(l))):
                tmp_data[header[i]] = l[i]
            specimen = tmp_data['specimen']
            if specimen not in list(Data.keys()):
                Data[specimen] = []
            Data[specimen].append(tmp_data)
        Fin.close()
        # search from duplicates
        for specimen in list(Data.keys()):
            x = len(Data[specimen])-1
            new_data = []
            duplicates = []
            for i in range(1, x):
                while i < len(Data[specimen]) and Data[specimen][i]['treatment'] == Data[specimen][i-1]['treatment'] and Data[specimen][i]['treatment_type'] == Data[specimen][i-1]['treatment_type']:
                    duplicates.append(Data[specimen][i])
                    del(Data[specimen][i])
                if len(duplicates) > 0:
                    if average_replicates:
                        duplicates.append(Data[specimen][i-1])
                        Data[specimen][i-1] = average_duplicates(duplicates)
                        print("-W- WARNING: averaging %i duplicates for specimen %s treatmant %s" %
                              (len(duplicates), specimen, duplicates[-1]['treatment']))
                        duplicates = []
                    else:
                        Data[specimen][i-1] = duplicates[-1]
                        print("-W- WARNING: found %i duplicates for specimen %s treatmant %s. Taking the last measurement only" %
                              (len(duplicates), specimen, duplicates[-1]['treatment']))
                        duplicates = []

                if i == len(Data[specimen])-1:
                    break

        return(Data)


    def average_duplicates(duplicates):
        '''
        avarage replicate measurements.
        '''
        carts_s, carts_g, carts_t = [], [], []
        for rec in duplicates:
            moment = float(rec['moment'])
            if 'dec_s' in list(rec.keys()) and 'inc_s' in list(rec.keys()):
                if rec['dec_s'] != "" and rec['inc_s'] != "":
                    dec_s = float(rec['dec_s'])
                    inc_s = float(rec['inc_s'])
                    cart_s = pmag.dir2cart([dec_s, inc_s, moment])
                    carts_s.append(cart_s)
            if 'dec_g' in list(rec.keys()) and 'inc_g' in list(rec.keys()):
                if rec['dec_g'] != "" and rec['inc_g'] != "":
                    dec_g = float(rec['dec_g'])
                    inc_g = float(rec['inc_g'])
                    cart_g = pmag.dir2cart([dec_g, inc_g, moment])
                    carts_g.append(cart_g)
            if 'dec_t' in list(rec.keys()) and 'inc_t' in list(rec.keys()):
                if rec['dec_t'] != "" and rec['inc_t'] != "":
                    dec_t = float(rec['dec_t'])
                    inc_t = float(rec['inc_t'])
                    cart_t = pmag.dir2cart([dec_t, inc_t, moment])
                    carts_t.append(cart_t)
        if len(carts_s) > 0:
            carts = scipy.array(carts_s)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_s = "%.2f" % mean_dir[0]
            mean_inc_s = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_s, mean_inc_s = "", ""
        if len(carts_g) > 0:
            carts = scipy.array(carts_g)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_g = "%.2f" % mean_dir[0]
            mean_inc_g = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_g, mean_inc_g = "", ""

        if len(carts_t) > 0:
            carts = scipy.array(carts_t)
            x_mean = scipy.mean(carts[:, 0])
            y_mean = scipy.mean(carts[:, 1])
            z_mean = scipy.mean(carts[:, 2])
            mean_dir = pmag.cart2dir([x_mean, y_mean, z_mean])
            mean_dec_t = "%.2f" % mean_dir[0]
            mean_inc_t = "%.2f" % mean_dir[1]
            mean_moment = "%10.3e" % mean_dir[2]
        else:
            mean_dec_t, mean_inc_t = "", ""

        meanrec = {}
        for key in list(duplicates[0].keys()):
            if key in ['dec_s', 'inc_s', 'dec_g', 'inc_g', 'dec_t', 'inc_t', 'moment']:
                continue
            else:
                meanrec[key] = duplicates[0][key]
        meanrec['dec_s'] = mean_dec_s
        meanrec['dec_g'] = mean_dec_g
        meanrec['dec_t'] = mean_dec_t
        meanrec['inc_s'] = mean_inc_s
        meanrec['inc_g'] = mean_inc_g
        meanrec['inc_t'] = mean_inc_t
        meanrec['moment'] = mean_moment
        return meanrec


    def get_upper_level_name(name, nc):
        '''
        get sample/site name from specimen/sample using naming convention
        '''
        if float(nc[0]) == 0:
            if float(nc[1]) != 0:
                number_of_char = int(nc[1])
                high_name = name[:number_of_char]
            else:
                high_name = name
        elif float(nc[0]) == 1:
            if float(nc[1]) != 0:
                number_of_char = int(nc[1])*-1
                high_name = name[:number_of_char]
            else:
                high_name = name
        elif float(nc[0]) == 2:
            d = str(nc[1])
            name_splitted = name.split(d)
            if len(name_splitted) == 1:
                high_name = name_splitted[0]
            else:
                high_name = d.join(name_splitted[:-1])
        else:
            high_name = name
        return high_name


    def merge_pmag_recs(old_recs):
        recs = {}
        recs = copy.deepcopy(old_recs)
        headers = []
        for rec in recs:
            for key in list(rec.keys()):
                if key not in headers:
                    headers.append(key)
        for rec in recs:
            for header in headers:
                if header not in list(rec.keys()):
                    rec[header] = ""
        return recs


    # --------------------------------------
    # start conversion from generic
    # --------------------------------------


    # format and validate variables
    labfield = float(labfield)
    labfield_phi = float(labfield_phi)
    labfield_theta = float(labfield_theta)

    if magfile:
        try:
            input = open(magfile, 'r')
        except:
            print("bad mag file:", magfile)
            return False, "bad mag file"
    else:
        print("mag_file field is required option")
        return False, "mag_file field is required option"

    if not experiment:
        print("-E- Must provide experiment. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see below for format), NLT")
        return False, "Must provide experiment. Please provide experiment type of: Demag, PI, ATRM n (n of positions), CR (see help for format), NLT"

    if experiment == 'ATRM':
        if command_line:
            ind = sys.argv.index("ATRM")
            atrm_n_pos = int(sys.argv[ind+1])
        else:
            atrm_n_pos = 6

    if experiment == 'AARM':
        if command_line:
            ind = sys.argv.index("AARM")
            aarm_n_pos = int(sys.argv[ind+1])
        else:
            aarm_n_pos = 6

    if experiment == 'CR':
        if command_line:
            ind = sys.argv.index("CR")
            cooling_times = sys.argv[ind+1]
            cooling_times_list = cooling_times.split(',')
        # if not command line, cooling_times_list is already set

    # --------------------------------------
    # read data from generic file
    # --------------------------------------

    mag_data = read_generic_file(magfile, not noave)

    # --------------------------------------
    # for each specimen get the data, and translate it to MagIC format
    # --------------------------------------

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    specimens_list = sorted(mag_data.keys())
    for specimen in specimens_list:
        measurement_running_number = 0
        this_specimen_treatments = []  # a list of all treatments
        MeasRecs_this_specimen = []
        LP_this_specimen = []  # a list of all lab protocols
        IZ, ZI = 0, 0  # counter for IZ and ZI steps

        for meas_line in mag_data[specimen]:

            # ------------------
            # trivial MeasRec data
            # ------------------

            MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}

            specimen = meas_line['specimen']
            sample = get_upper_level_name(specimen, sample_nc)
            site = get_upper_level_name(sample, site_nc)
            sample_method_codes = ""
            azimuth, dip, DipDir, Dip = "", "", "", ""

            MeasRec['citations'] = "This study"
            MeasRec["specimen"] = specimen
            MeasRec['analysts'] = user
            MeasRec["instrument_codes"] = ""
            MeasRec["quality"] = 'g'
            MeasRec["treat_step_num"] = "%i" % measurement_running_number
            MeasRec["magn_moment"] = '%10.3e' % (
                float(meas_line["moment"])*1e-3)  # in Am^2
            MeasRec["meas_temp"] = '273.'  # room temp in kelvin

            # ------------------
            #  decode treatments from treatment column in the generic file
            # ------------------

            treatment = []
            treatment_code = str(meas_line['treatment']).split(".")
            treatment.append(float(treatment_code[0]))
            if len(treatment_code) == 1:
                treatment.append(0)
            else:
                treatment.append(float(treatment_code[1]))

            # ------------------
            #  lab field direction
            # ------------------

            if experiment in ['PI', 'NLT', 'CR']:
                if float(treatment[1]) in [0., 3.]:  # zerofield step or tail check
                    MeasRec["treat_dc_field"] = "0"
                    MeasRec["treat_dc_field_phi"] = "0"
                    MeasRec["treat_dc_field_theta"] = "0"
                elif not labfield:
                    print(
                        "-W- WARNING: labfield (-dc) is a required argument for this experiment type")
                    return False, "labfield (-dc) is a required argument for this experiment type"
                else:
                    MeasRec["treat_dc_field"] = '%8.3e' % (float(labfield))
                    MeasRec["treat_dc_field_phi"] = "%.2f" % (
                        float(labfield_phi))
                    MeasRec["treat_dc_field_theta"] = "%.2f" % (
                        float(labfield_theta))
            else:
                MeasRec["treat_dc_field"] = ""
                MeasRec["treat_dc_field_phi"] = ""
                MeasRec["treat_dc_field_theta"] = ""

            # ------------------
            # treatment temperature/peak field
            # ------------------

            if experiment == 'Demag':
                if meas_line['treatment_type'] == 'A':
                    MeasRec['treat_temp'] = "273."
                    MeasRec["treat_ac_field"] = "%.3e" % (treatment[0]*1e-3)
                elif meas_line['treatment_type'] == 'N':
                    MeasRec['treat_temp'] = "273."
                    MeasRec["treat_ac_field"] = ""
                else:
                    MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                    MeasRec["treat_ac_field"] = ""
            else:
                MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                MeasRec["treat_ac_field"] = ""

            # ---------------------
            # Lab treatment
            # Lab protocol
            # ---------------------

            # ---------------------
            # Lab treatment and lab protocoal for NRM:
            # ---------------------

            if float(meas_line['treatment']) == 0:
                LT = "LT-NO"
                LP = ""  # will be filled later after finishing reading all measurements line

            # ---------------------
            # Lab treatment and lab protocoal for paleointensity experiment
            # ---------------------

            elif experiment == 'PI':
                LP = "LP-PI-TRM"
                if treatment[1] == 0:
                    LT = "LT-T-Z"
                elif treatment[1] == 1 or treatment[1] == 10:  # infield
                    LT = "LT-T-I"
                elif treatment[1] == 2 or treatment[1] == 20:  # pTRM check
                    LT = "LT-PTRM-I"
                    LP = LP+":"+"LP-PI-ALT-PTRM"
                elif treatment[1] == 3 or treatment[1] == 30:  # Tail check
                    LT = "LT-PTRM-MD"
                    LP = LP+":"+"LP-PI-BT-MD"
                elif treatment[1] == 4 or treatment[1] == 40:  # Additivity check
                    LT = "LT-PTRM-AC"
                    LP = LP+":"+"LP-PI-BT-MD"
                else:
                    print("-E- unknown measurement code specimen %s treatmemt %s" %
                          (meas_line['specimen'], meas_line['treatment']))
                    MeasRec = {}
                    continue
                # save all treatment in a list
                # we will use this later to distinguidh between ZI / IZ / and IZZI

                this_specimen_treatments.append(float(meas_line['treatment']))
                if LT == "LT-T-Z":
                    if float(treatment[0]+0.1) in this_specimen_treatments:
                        LP = LP+":"+"LP-PI-IZ"
                if LT == "LT-T-I":
                    if float(treatment[0]+0.0) in this_specimen_treatments:
                        LP = LP+":"+"LP-PI-ZI"
            # ---------------------
            # Lab treatment and lab protocoal for demag experiment
            # ---------------------

            elif "Demag" in experiment:
                if meas_line['treatment_type'] == 'A':
                    LT = "LT-AF-Z"
                    LP = "LP-DIR-AF"
                else:
                    LT = "LT-T-Z"
                    LP = "LP-DIR-T"

            # ---------------------
            # Lab treatment and lab protocoal for ATRM experiment
            # ---------------------

            elif experiment in ['ATRM', 'AARM']:

                if experiment == 'ATRM':
                    LP = "LP-AN-TRM"
                    n_pos = atrm_n_pos
                    if n_pos != 6:
                        print(
                            "the program does not support ATRM in %i position." % n_pos)
                        continue

                if experiment == 'AARM':
                    LP = "LP-AN-ARM"
                    n_pos = aarm_n_pos
                    if n_pos != 6:
                        print(
                            "the program does not support AARM in %i position." % n_pos)
                        continue

                if treatment[1] == 0:
                    if experiment == 'ATRM':
                        LT = "LT-T-Z"
                        MeasRec['treat_temp'] = "%.2f" % (treatment[0]+273.)
                        MeasRec["treat_ac_field"] = ""

                    else:
                        LT = "LT-AF-Z"
                        MeasRec['treat_temp'] = "273."
                        MeasRec["treat_ac_field"] = "%.3e" % (
                            treatment[0]*1e-3)
                    MeasRec["treat_dc_field"] = '0'
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    if experiment == 'ATRM':
                        # alteration check as final measurement
                        if float(treatment[1]) == 70 or float(treatment[1]) == 7:
                            LT = "LT-PTRM-I"
                        else:
                            LT = "LT-T-I"
                    else:
                        LT = "LT-AF-I"
                    MeasRec["treat_dc_field"] = '%8.3e' % (float(labfield))

                    # find the direction of the lab field in two ways:

                    # (1) using the treatment coding (XX.1=+x, XX.2=+y, XX.3=+z, XX.4=-x, XX.5=-y, XX.6=-z)
                    tdec = [0, 90, 0, 180, 270, 0, 0, 90, 0]
                    tinc = [0, 0, 90, 0, 0, -90, 0, 0, 90]
                    if treatment[1] < 10:
                        ipos_code = int(treatment[1])-1
                    else:
                        ipos_code = int(old_div(treatment[1], 10))-1

                    # (2) using the magnetization
                    if meas_line["dec_s"] != "":
                        DEC = float(meas_line["dec_s"])
                        INC = float(meas_line["inc_s"])
                    elif meas_line["dec_g"] != "":
                        DEC = float(meas_line["dec_g"])
                        INC = float(meas_line["inc_g"])
                    elif meas_line["dec_t"] != "":
                        DEC = float(meas_line["dec_t"])
                        INC = float(meas_line["inc_t"])
                    if DEC < 0 and DEC > -359:
                        DEC = 360.+DEC

                    if INC < 45 and INC > -45:
                        if DEC > 315 or DEC < 45:
                            ipos_guess = 0
                        if DEC > 45 and DEC < 135:
                            ipos_guess = 1
                        if DEC > 135 and DEC < 225:
                            ipos_guess = 3
                        if DEC > 225 and DEC < 315:
                            ipos_guess = 4
                    else:
                        if INC > 45:
                            ipos_guess = 2
                        if INC < -45:
                            ipos_guess = 5
                    # prefer the guess over the code
                    ipos = ipos_guess
                    # check it
                    if treatment[1] != 7 and treatment[1] != 70:
                        if ipos_guess != ipos_code:
                            print("-W- WARNING: check specimen %s step %s, anistropy measurements, coding does not match the direction of the lab field" % (
                                specimen, meas_line['treatment']))
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (tdec[ipos])
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (tinc[ipos])

            # ---------------------
            # Lab treatment and lab protocoal for cooling rate experiment
            # ---------------------

            elif experiment == "CR":

                cooling_times_list
                LP = "LP-CR-TRM"
                MeasRec["treat_temp"] = '%8.3e' % (
                    float(treatment[0])+273.)  # temp in kelvin

                if treatment[1] == 0:
                    LT = "LT-T-Z"
                    MeasRec["treat_dc_field"] = "0"
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                else:
                    if treatment[1] == 7:  # alteration check as final measurement
                        LT = "LT-PTRM-I"
                    else:
                        LT = "LT-T-I"
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        labfield_phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        labfield_theta)  # labfield theta

                    indx = int(treatment[1])-1
                    # alteration check matjed as 0.7 in the measurement file
                    if indx == 6:
                        cooling_time = cooling_times_list[-1]
                    else:
                        cooling_time = cooling_times_list[indx]
                    MeasRec["measurement_description"] = "cooling_rate" + \
                        ":"+cooling_time+":"+"K/min"

            # ---------------------
            # Lab treatment and lab protocoal for NLT experiment
            # ---------------------

            elif 'NLT' in experiment:
                print(
                    "Dont support yet NLT rate experiment file. Contact rshaar@ucsd.edu")

            # ---------------------
            # method_codes for this measurement only
            # LP will be fixed after all measurement lines are read
            # ---------------------

            MeasRec["method_codes"] = LT+":"+LP

            # --------------------
            # deal with specimen orientation and different coordinate system
            # --------------------

            found_s, found_geo, found_tilt = False, False, False
            if "dec_s" in list(meas_line.keys()) and "inc_s" in list(meas_line.keys()):
                if meas_line["dec_s"] != "" and meas_line["inc_s"] != "":
                    found_s = True
                MeasRec["dir_dec"] = meas_line["dec_s"]
                MeasRec["dir_inc"] = meas_line["inc_s"]
            if "dec_g" in list(meas_line.keys()) and "inc_g" in list(meas_line.keys()):
                if meas_line["dec_g"] != "" and meas_line["inc_g"] != "":
                    found_geo = True
            if "dec_t" in list(meas_line.keys()) and "inc_t" in list(meas_line.keys()):
                if meas_line["dec_t"] != "" and meas_line["inc_t"] != "":
                    found_tilt = True

            # -----------------------------
            # specimen coordinates: no
            # geographic coordinates: yes
            # -----------------------------

            if found_geo and not found_s:
                MeasRec["dir_dec"] = meas_line["dec_g"]
                MeasRec["dir_inc"] = meas_line["inc_g"]
                azimuth = "0"
                dip = "0"

            # -----------------------------
            # specimen coordinates: no
            # geographic coordinates: no
            # -----------------------------
            if not found_geo and not found_s:
                print("-E- ERROR: sample %s does not have dec_s/inc_s or dec_g/inc_g. Ignore specimen %s " %
                      (sample, specimen))
                break

            # -----------------------------
            # specimen coordinates: yes
            # geographic coordinates: yes
            #
            # commant: Ron, this need to be tested !!
            # -----------------------------
            if found_geo and found_s:
                cdec, cinc = float(meas_line["dec_s"]), float(
                    meas_line["inc_s"])
                gdec, ginc = float(meas_line["dec_g"]), float(
                    meas_line["inc_g"])
                az, pl = pmag.get_azpl(cdec, cinc, gdec, ginc)
                azimuth = "%.1f" % az
                dip = "%.1f" % pl

            # -----------------------------
            # specimen coordinates: yes
            # geographic coordinates: no
            # -----------------------------
            if not found_geo and found_s and "Demag" in experiment:
                print("-W- WARNING: missing dip or azimuth for sample %s" % sample)

            # -----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: no
            # -----------------------------
            if found_tilt and not found_geo:
                print(
                    "-E- ERROR: missing geographic data for sample %s. Ignoring tilt-corrected data " % sample)

            # -----------------------------
            # tilt-corrected coordinates: yes
            # geographic coordinates: yes
            # -----------------------------
            if found_tilt and found_geo:
                dec_geo, inc_geo = float(
                    meas_line["dec_g"]), float(meas_line["inc_g"])
                dec_tilt, inc_tilt = float(
                    meas_line["dec_t"]), float(meas_line["inc_t"])
                if dec_geo == dec_tilt and inc_geo == inc_tilt:
                    DipDir, Dip = 0., 0.
                else:
                    DipDir, Dip = pmag.get_tilt(
                        dec_geo, inc_geo, dec_tilt, inc_tilt)

            # -----------------------------
            # samples method codes
            # geographic coordinates: no
            # -----------------------------
            if found_tilt or found_geo:
                sample_method_codes = "SO-NO"

            if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRec['citations'] = "This study"
                SpecRecs.append(SpecRec)
            if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['citations'] = "This study"
                SampRec['azimuth'] = azimuth
                SampRec['dip'] = dip
                SampRec['bed_dip_direction'] = DipDir
                SampRec['bed_dip'] = Dip
                SampRec['method_codes'] = sample_method_codes
                SampRecs.append(SampRec)
            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['citations'] = "This study"
                SiteRec['lat'] = lat
                SiteRec['lon'] = lon
                SiteRecs.append(SiteRec)
            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['citations'] = "This study"
                LocRec['lat_n'] = lat
                LocRec['lon_e'] = lon
                LocRec['lat_s'] = lat
                LocRec['lon_w'] = lon
                LocRecs.append(LocRec)

            MeasRecs_this_specimen.append(MeasRec)
            measurement_running_number += 1
            # -------

        # -------
        # after reading all the measurements lines for this specimen
        # 1) add experiments
        # 2) fix method_codes with the correct lab protocol
        # -------
        LP_this_specimen = []
        for MeasRec in MeasRecs_this_specimen:
            method_codes = MeasRec["method_codes"].split(":")
            for code in method_codes:
                if "LP" in code and code not in LP_this_specimen:
                    LP_this_specimen.append(code)
        # check IZ/ZI/IZZI
        if "LP-PI-ZI" in LP_this_specimen and "LP-PI-IZ" in LP_this_specimen:
            LP_this_specimen.remove("LP-PI-ZI")
            LP_this_specimen.remove("LP-PI-IZ")
            LP_this_specimen.append("LP-PI-BT-IZZI")

        # add the right LP codes and fix experiment name
        for MeasRec in MeasRecs_this_specimen:
            # MeasRec["experiment"]=MeasRec["specimen"]+":"+":".join(LP_this_specimen)
            method_codes = MeasRec["method_codes"].split(":")
            LT = ""
            for code in method_codes:
                if code[:3] == "LT-":
                    LT = code
                    break
            MeasRec["method_codes"] = LT+":"+":".join(LP_this_specimen)
            MeasRec["method_codes"] = MeasRec["method_codes"].strip(":")
            MeasRecs.append(MeasRec)

    # --
    # write tables to file
    # --

    con = nb.Contribution(dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file



### HUJI_magic conversion

def huji(magfile="", dir_path=".", input_dir_path="", datafile="", codelist="",
         meas_file="measurements.txt", spec_file="specimens.txt",
         samp_file="samples.txt", site_file="sites.txt", loc_file="locations.txt",
         user="", specnum=0, samp_con="1", labfield=0, phi=0, theta=0, peakfield=0,
         location="", CR_cooling_times=None, noave=False):

    # format and validate variables
    specnum = int(specnum)
    labfield = float(labfield) * 1e-6
    phi = int(theta)
    theta = int(theta)
    peakfield = float(peakfield)*1e-3
    if not input_dir_path:
        input_dir_path = dir_path

    if magfile:
        try:
            fname = pmag.resolve_file_name(magfile, input_dir_path)
            infile = open(fname, 'r')
        except IOError as ex:
            print(ex)
            print("bad mag file name")
            return False, "bad mag file name"
    else:
        print("mag_file field is a required option")
        return False, "mag_file field is a required option"

    if specnum != 0:
        specnum = -specnum
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "option [4] must be in form 4-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "4"
    if "7" in samp_con:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z = int(samp_con.split("-")[1])
            samp_con = "7"
    else:
        Z = 1

    if codelist:
        codes = codelist.split(':')
    else:
        print("-E- Must select experiment type (codelist/-LP, options are: [AF, T, ANI, TRM, CR])")
        return False, "Must select experiment type (codelist/-LP, options are: [AF, T, ANI, TRM, CR])"
    if "AF" in codes:
        demag = 'AF'
        LPcode = "LP-DIR-AF"
    if "T" in codes:
        demag = "T"
        if not labfield:
            LPcode = "LP-DIR-T"
        if labfield:
            LPcode = "LP-PI-TRM"
        if "ANI" in codes:
            if not labfield:
                print("missing lab field option")
                return False, "missing lab field option"
            LPcode = "LP-AN-TRM"

    if "TRM" in codes:
        demag = "T"
        LPcode = "LP-TRM"
        # trm=1

    if "CR" in codes:
        demag = "T"
        # dc should be in the code
        if not labfield:
            print("missing lab field option")
            return False, "missing lab field option"

        LPcode = "LP-CR-TRM"  # TRM in different cooling rates
        if command_line:
            ind = sys.argv.index("-LP")
            CR_cooling_times = sys.argv[ind+2].split(",")

    version_num = pmag.get_version()

    # --------------------------------------
    # Read the file
    # Assumption:
    # 1. different lab protocolsa are in different files
    # 2. measurements are in the correct order
    # --------------------------------------

    Data = {}
    line_no = 0
    for line in infile.readlines():
        line_no += 1
        this_line_data = {}
        line_no += 1
        instcode = ""
        if len(line) < 2:
            continue
        if line[0] == "#":  # HUJI way of marking bad data points
            continue

        rec = line.strip('\n').split()
        specimen = rec[0]
        date = rec[2].split("/")
        hour = rec[3].split(":")
        treatment_type = rec[4]
        treatment = rec[5].split(".")
        dec_core = rec[6]
        inc_core = rec[7]
        moment_emu = float(rec[-1])

        if specimen not in list(Data.keys()):
            Data[specimen] = []

        # check duplicate treatments:
        # if yes, delete the first and use the second

        if len(Data[specimen]) > 0:
            if treatment == Data[specimen][-1]['treatment']:
                del(Data[specimen][-1])
                print("-W- Identical treatments in file %s magfile line %i: specimen %s, treatment %s ignoring the first. " %
                      (magfile, line_no, specimen, ".".join(treatment)))

        this_line_data = {}
        this_line_data['specimen'] = specimen
        this_line_data['date'] = date
        this_line_data['hour'] = hour
        this_line_data['treatment_type'] = treatment_type
        this_line_data['treatment'] = treatment
        this_line_data['dec_core'] = dec_core
        this_line_data['inc_core'] = inc_core
        this_line_data['moment_emu'] = moment_emu
        this_line_data['azimuth'] = ''
        this_line_data['dip'] = ''
        this_line_data['bed_dip_direction'] = ''
        this_line_data['bed_dip'] = ''
        this_line_data['lat'] = ''
        this_line_data['lon'] = ''
        this_line_data['volume'] = ''
        Data[specimen].append(this_line_data)
    infile.close()
    print("-I- done reading file %s" % magfile)

    if datafile:
        dinfile = open(datafile)
        for line in dinfile.readlines():
            data = line.split()
            if len(data) < 8 or data[0] == '':
                continue
            elif data[0] in list(Data.keys()):
                for i in range(len(Data[data[0]])):
                    Data[data[0]][i]['azimuth'] = data[1]
                    Data[data[0]][i]['dip'] = data[2]
                    try:
                        Data[data[0]][i]['bed_dip_direction'] = float(
                            data[3])+90
                    except ValueError:
                        Data[data[0]][i]['bed_dip_direction'] = ''
                    Data[data[0]][i]['bed_dip'] = data[4]
                    Data[data[0]][i]['lat'] = data[5]
                    Data[data[0]][i]['lon'] = data[6]
                    Data[data[0]][i]['volume'] = data[7]
            else:
                print(
                    "no specimen %s found in magnetometer data file when reading specimen orientation data file, or data file record for specimen too short" % data[0])
        dinfile.close()

    # --------------------------------------
    # Convert to MagIC
    # --------------------------------------

    specimens_list = list(Data.keys())
    specimens_list.sort()

    MeasRecs, SpecRecs, SampRecs, SiteRecs, LocRecs = [], [], [], [], []
    for specimen in specimens_list:
        for i in range(len(Data[specimen])):
            this_line_data = Data[specimen][i]
            methcode = ""
            MeasRec, SpecRec, SampRec, SiteRec, LocRec = {}, {}, {}, {}, {}
            specimen = this_line_data['specimen']
            if specnum != 0:
                sample = this_line_data['specimen'][:specnum]
            else:
                sample = this_line_data['specimen']
            site = pmag.parse_site(sample, samp_con, Z)
            if not location:
                location = site
            if specimen != "" and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else "" for x in SpecRecs]:
                SpecRec['specimen'] = specimen
                SpecRec['sample'] = sample
                SpecRecs.append(SpecRec)
            if sample != "" and sample not in [x['sample'] if 'sample' in list(x.keys()) else "" for x in SampRecs]:
                SampRec['sample'] = sample
                SampRec['site'] = site
                SampRec['azimuth'] = this_line_data['azimuth']
                SampRec['dip'] = this_line_data['dip']
                SampRec['bed_dip_direction'] = this_line_data['bed_dip_direction']
                SampRec['bed_dip'] = this_line_data['bed_dip']
                SampRecs.append(SampRec)
            if site != "" and site not in [x['site'] if 'site' in list(x.keys()) else "" for x in SiteRecs]:
                SiteRec['site'] = site
                SiteRec['location'] = location
                SiteRec['lat'] = this_line_data['lat']
                SiteRec['lon'] = this_line_data['lon']
                SiteRecs.append(SiteRec)
            if location != "" and location not in [x['location'] if 'location' in list(x.keys()) else "" for x in LocRecs]:
                LocRec['location'] = location
                LocRec['lat_n'] = this_line_data['lat']
                LocRec['lon_e'] = this_line_data['lon']
                LocRec['lat_s'] = this_line_data['lat']
                LocRec['lon_w'] = this_line_data['lon']
                LocRecs.append(LocRec)

            MeasRec['specimen'] = specimen
            MeasRec["meas_temp"] = '%8.3e' % (273)  # room temp in kelvin
            MeasRec["magn_moment"] = '%10.3e' % (
                float(this_line_data['moment_emu'])*1e-3)  # moment in Am^2 (from emu)
            MeasRec["dir_dec"] = this_line_data['dec_core']
            MeasRec["dir_inc"] = this_line_data['inc_core']

            date = this_line_data['date']
            hour = this_line_data['hour']
            if len(date[2]) < 4 and float(date[2]) >= 70:
                yyyy = "19"+date[2]
            elif len(date[2]) < 4 and float(date[2]) < 70:
                yyyy = "20"+date[2]
            else:
                yyyy = date[2]
            if len(date[0]) == 1:
                date[0] = "0"+date[0]
            if len(date[1]) == 1:
                date[1] = "0"+date[1]
            dt = ":".join([date[0], date[1], yyyy, hour[0], hour[1], "0"])
            local = pytz.timezone("America/New_York")
            naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp = utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"

            MeasRec['analysts'] = user
            MeasRec["citations"] = "This study"
            MeasRec["instrument_codes"] = "HUJI-2G"
            MeasRec["quality"] = "g"
            MeasRec["meas_n_orient"] = "1"
            MeasRec["standard"] = "u"
            MeasRec["description"] = ""

            # ----------------------------------------
            # AF demag
            # do not support AARM yet
            # ----------------------------------------

            if demag == "AF":
                treatment_type = this_line_data['treatment_type']
                # demag in zero field
                if LPcode != "LP-AN-ARM":
                    MeasRec["treat_ac_field"] = '%8.3e' % (
                        float(this_line_data['treatment'][0])*1e-3)  # peak field in tesla
                    MeasRec["treat_dc_field"] = '0'
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                    if treatment_type == "N":
                        methcode = "LP-DIR-AF:LT-NO"
                    elif treatment_type == "A":
                        methcode = "LP-DIR-AF:LT-AF-Z"
                    else:
                        print(
                            "ERROR in treatment field line %i... exiting until you fix the problem" % line_no)
                        print(this_line_data)
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" % line_no
                # AARM experiment
                else:
                    print("Don't support AARM in HUJI format yet. sorry... ")
                MeasRec["method_codes"] = methcode
                MeasRec["experiment"] = specimen + ":" + LPcode
                MeasRec["treat_step_num"] = "%i" % i
                MeasRec["description"] = ""

                MeasRecs.append(MeasRec)

            # ----------------------------------------
            # Thermal:
            # Thellier experiment: "IZ", "ZI", "IZZI", pTRM checks
            # Thermal demag
            # Thermal cooling rate experiment
            # Thermal NLT
            # ----------------------------------------

            if demag == "T":

                treatment = this_line_data['treatment']
                treatment_type = this_line_data['treatment_type']

                # ----------------------------------------
                # Thellier experimet
                # ----------------------------------------

                if LPcode == "LP-PI-TRM":  # Thelllier experiment
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode
                    if treatment_type == "N" or ((treatment[1] == '0' or treatment[1] == '00') and float(treatment[0]) == 0):
                        LT_code = "LT-NO"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_dc_field"] = '0'
                        MeasRec["treat_temp"] = '273.'

                    elif treatment[1] == '0' or treatment[1] == '00':
                        LT_code = "LT-T-Z"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_dc_field"] = '%8.3e' % (0)
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin

                        # check if this is ZI or IZ:
                        #  check if the same temperature already measured:
                        methcode = "LP-PI-TRM:LP-PI-TRM-ZI"
                        for j in range(0, i):
                            if Data[specimen][j]['treatment'][0] == treatment[0]:
                                if Data[specimen][j]['treatment'][1] == '1' or Data[specimen][j]['treatment'][1] == '10':
                                    methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                                else:
                                    methcode = "LP-PI-TRM:LP-PI-TRM-ZI"

                    elif treatment[1] == '1' or treatment[1] == '10':
                        LT_code = "LT-T-I"
                        # labfield in tesla (convert from microT)
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            phi)  # labfield phi
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            theta)  # labfield theta
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin

                        # check if this is ZI or IZ:
                        #  check if the same temperature already measured:
                        methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                        for j in range(0, i):
                            if Data[specimen][j]['treatment'][0] == treatment[0]:
                                if Data[specimen][j]['treatment'][1] == '0' or Data[specimen][j]['treatment'][1] == '00':
                                    methcode = "LP-PI-TRM:LP-PI-TRM-ZI"
                                else:
                                    methcode = "LP-PI-TRM:LP-PI-TRM-IZ"
                    elif treatment[1] == '2' or treatment[1] == '20':
                        LT_code = "LT-PTRM-I"
                        # labfield in tesla (convert from microT)
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                            phi)  # labfield phi
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                            theta)  # labfield theta
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        methcode = "LP-PI-TRM:LP-PI-TRM-IZ"

                    else:
                        print(
                            "ERROR in treatment field line %i... exiting until you fix the problem" % line_no)
                        return False, "ERROR in treatment field line %i... exiting until you fix the problem" % line_no
                    MeasRec["method_codes"] = LT_code+":"+methcode
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)

                # ----------------------------------------
                # demag experimet
                # ----------------------------------------

                if LPcode == "LP-DIR-T":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode
                    if treatment_type == "N":
                        LT_code = "LT-NO"
                    else:
                        LT_code = "LT-T-Z"
                        methcode = LPcode+":"+"LT-T-Z"
                    MeasRec["treat_dc_field_phi"] = '0'
                    MeasRec["treat_dc_field_theta"] = '0'
                    MeasRec["treat_dc_field"] = '%8.3e' % (0)
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    MeasRec["method_codes"] = LT_code+":"+methcode
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # ATRM measurements
                # The direction of the magnetization is used to determine the
                # direction of the lab field.
                # ----------------------------------------

                if LPcode == "LP-AN-TRM":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    methcode = LPcode

                    if float(treatment[1]) == 0:
                        MeasRec["method_codes"] = "LP-AN-TRM:LT-T-Z"
                        MeasRec["treat_dc_field_phi"] = '0'
                        MeasRec["treat_dc_field_theta"] = '0'
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        MeasRec["treat_dc_field"] = '0'
                    else:
                        if float(treatment[1]) == 7:
                            # alteration check
                            methcode = "LP-AN-TRM:LT-PTRM-I"
                            MeasRec["treat_step_num"] = '7'  # -z
                        else:
                            MeasRec["method_codes"] = "LP-AN-TRM:LT-T-I"
                            inc = float(MeasRec["dir_inc"])
                            dec = float(MeasRec["dir_dec"])
                            if abs(inc) < 45 and (dec < 45 or dec > 315):  # +x
                                tdec, tinc = 0, 0
                                MeasRec["treat_step_num"] = '1'
                            if abs(inc) < 45 and (dec < 135 and dec > 45):
                                tdec, tinc = 90, 0
                                MeasRec["treat_step_num"] = '2'  # +y
                            if inc > 45:
                                tdec, tinc = 0, 90
                                MeasRec["treat_step_num"] = '3'  # +z
                            if abs(inc) < 45 and (dec < 225 and dec > 135):
                                tdec, tinc = 180, 0
                                MeasRec["treat_step_num"] = '4'  # -x
                            if abs(inc) < 45 and (dec < 315 and dec > 225):
                                tdec, tinc = 270, 0
                                MeasRec["treat_step_num"] = '5'  # -y
                            if inc < -45:
                                tdec, tinc = 0, -90
                                MeasRec["treat_step_num"] = '6'  # -z

                        MeasRec["treat_dc_field_phi"] = '%7.1f' % (tdec)
                        MeasRec["treat_dc_field_theta"] = '%7.1f' % (tinc)
                        MeasRec["treat_temp"] = '%8.3e' % (
                            float(treatment[0])+273.)  # temp in kelvin
                        MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # NLT measurements
                # or TRM acquisistion experiment
                # ----------------------------------------

                if LPcode == "LP-TRM":
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    MeasRec["method_codes"] = "LP-TRM:LT-T-I"
                    if float(treatment[1]) == 0:
                        labfield = 0
                    else:
                        labfield = float(float(treatment[1]))*1e-6
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    MeasRec["treat_step_num"] = "%i" % i
                    MeasRec["description"] = ""
                    MeasRecs.append(MeasRec)
                    # continue

                # ----------------------------------------
                # Cooling rate experiments
                # ----------------------------------------

                if LPcode == "LP-CR-TRM":
                    index = int(treatment[1][0])
                    # print index,"index"
                    # print CR_cooling_times,"CR_cooling_times"
                    # print CR_cooling_times[index-1]
                    # print CR_cooling_times[0:index-1]
                    if index == 7 or index == 70:  # alteration check as final measurement
                        meas_type = "LT-PTRM-I:LP-CR-TRM"
                        CR_cooling_time = CR_cooling_times[-1]
                    else:
                        meas_type = "LT-T-I:LP-CR-TRM"
                        CR_cooling_time = CR_cooling_times[index-1]
                    MeasRec["method_codes"] = meas_type
                    MeasRec["experiment"] = specimen + ":" + LPcode
                    MeasRec["treat_temp"] = '%8.3e' % (
                        float(treatment[0])+273.)  # temp in kelvin
                    # labfield in tesla (convert from microT)
                    MeasRec["treat_dc_field"] = '%8.3e' % (labfield)
                    MeasRec["treat_dc_field_phi"] = '%7.1f' % (
                        phi)  # labfield phi
                    MeasRec["treat_dc_field_theta"] = '%7.1f' % (
                        theta)  # labfield theta
                    MeasRec["treat_step_num"] = "%i" % index
                    MeasRec["description"] = "cooling_rate" + \
                        ":"+CR_cooling_time+":"+"K/min"
                    #MeasRec["description"]="%.1f minutes per cooling time"%int(CR_cooling_time)
                    MeasRecs.append(MeasRec)
                    # continue

    con = nb.Contribution(dir_path, read_tables=[])

    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    MeasOuts = pmag.measurements_methods3(MeasRecs, noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasOuts)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file


### MINI_magic conversion

def mini(magfile, dir_path='.', meas_file='measurements.txt',
            data_model_num=3, volume=10, noave=0,
            inst="", user="", demag='N', methcode="LP-NO"):
    # initialize
    citation = 'This study'
    MagRecs = []
    version_num = pmag.get_version()
    try:
        with open(magfile, 'r') as finput:
            lines = finput.readlines()
    except OSError:
        print("bad mag file name")
        return False, "bad mag file name"
    # convert volume
    volume = 1e-6 * float(volume)
    # set col names based on MagIC 2 or 3
    if data_model_num == 2:
        spec_col = "er_specimen_name"
        loc_col = "er_location_name"
        site_col = "er_site_col"
        samp_col = "er_sample_name"
        software_col = "magic_software_packages"
        treat_temp_col = "treatment_temp"
        meas_temp_col = "measurement_temp"
        treat_ac_col = "treatment_ac_field"
        treat_dc_col = "treatment_dc_field"
        treat_dc_phi_col = "treatment_dc_field_phi"
        treat_dc_theta_col = "treatment_dc_field_theta"
        moment_col = "measurement_magn_moment"
        dec_col = "measurement_dec"
        inc_col = "measurement_inc"
        instrument_col = "magic_instrument_codes"
        analyst_col = "er_analyst_mail_names"
        citations_col = "er_citation_names"
        methods_col = "magic_method_codes"
        quality_col = "measurement_flag"
        meas_standard_col = "measurement_standard"
        meas_name_col = "measurement_number"
    else:
        spec_col = "specimen"
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        software_col = "software_packages"
        treat_temp_col = "treat_temp"
        meas_temp_col = "meas_temp"
        treat_ac_col = "treat_ac_field"
        treat_dc_col = "treat_dc_field"
        treat_dc_phi_col = "treat_dc_field_phi"
        treat_dc_theta_col = "treat_dc_field_theta"
        moment_col = "magn_moment"
        dec_col = "dir_dec"
        inc_col = "dir_inc"
        instrument_col = "instrument_codes"
        analyst_col = "analysts"
        citations_col = "citations"
        methods_col = "method_codes"
        quality_col = "quality"
        meas_standard_col = "standard"
        meas_name_col = "measurement"

    # go through the measurements
    for line in lines:
        rec = line.split(',')
        if len(rec) > 1:
            MagRec = {}
            IDs = rec[0].split('_')
            treat = IDs[1]
            MagRec[spec_col] = IDs[0]
            #print(MagRec[spec_col])
            sids = IDs[0].split('-')
            MagRec[loc_col] = sids[0]
            MagRec[site_col] = sids[0]+'-'+sids[1]
            if len(sids) == 2:
                MagRec[samp_col] = IDs[0]
            else:
                MagRec[samp_col] = sids[0]+'-'+sids[1]+'-'+sids[2]
            #print(MagRec)
            MagRec[software_col] = version_num
            MagRec[treat_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[meas_temp_col] = '%8.3e' % (273)  # room temp in kelvin
            MagRec[treat_ac_col] = '0'
            MagRec[treat_dc_col] = '0'
            MagRec[treat_dc_phi_col] = '0'
            MagRec[treat_dc_theta_col] = '0'
            meas_type = "LT-NO"
            if demag == "AF":
                MagRec[treat_ac_col] = '%8.3e' % (
                    float(treat)*1e-3)  # peak field in tesla
            if demag == "T":
                meas_type = "LT-T-Z"
                MagRec[treat_dc_col] = '%8.3e' % (0)
                MagRec[treat_temp_col] = '%8.3e' % (
                    float(treat)+273.)  # temp in kelvin
            if demag == "N":
                meas_type = "LT-NO"
                MagRec[treat_ac_col] = '0'
                MagRec[treat_dc_col] = '0'
            MagRec[moment_col] = '%10.3e' % (
                volume*float(rec[3])*1e-3)  # moment in Am2 (from mA/m)
            MagRec[dec_col] = rec[1]
            MagRec[inc_col] = rec[2]
            MagRec[instrument_col] = inst
            MagRec[analyst_col] = user
            MagRec[citations_col] = citation
            MagRec[methods_col] = methcode.strip(':')
            MagRec[quality_col] = 'g'
            MagRec[meas_standard_col] = 'u'
            MagRec[meas_name_col] = '1'
            MagRecs.append(MagRec)

    if data_model_num == 2:
        MagOuts = pmag.measurements_methods(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'magic_measurements')
    else:
        MagOuts = pmag.measurements_methods3(MagRecs, noave)
        pmag.magic_write(meas_file, MagOuts, 'measurements')
        # nicely parse all the specimen/sample/site/location data
        # and write it to file as well
        dir_path = os.path.split(meas_file)[0]
        con = nb.Contribution(dir_path, read_tables=['measurements'],
                              custom_filenames={'measurements': meas_file})
        con.propagate_measurement_info()
        for table in con.tables:
            con.write_table_to_file(table)
    print("results put in ", meas_file)
    return True, meas_file


### s_magic conversion

def s_magic(sfile, anisfile="specimens.txt", dir_path=".", atype="AMS",
            coord_type="s", sigma=False, samp_con="1", Z=1, specnum=0,
            location="unknown", spec="unknown", sitename="unknown",
            user="", data_model_num=3, name_in_file=False):

    coord_dict = {'s': '-1', 't': '100', 'g': '0'}
    coord = coord_dict.get(coord_type, '-1')
    specnum = -specnum

    if data_model_num == 2:
        specimen_col = "er_specimen_name"
        sample_col = "er_sample_name"
        site_col = "er_site_name"
        loc_col = "er_location_name"
        citation_col = "er_citation_names"
        analyst_col = "er_analyst_mail_names"
        aniso_type_col = "anisotropy_type"
        experiment_col = "magic_experiment_names"
        sigma_col = "anisotropy_sigma"
        unit_col = "anisotropy_unit"
        tilt_corr_col = "anisotropy_tilt_correction"
        method_col = "magic_method_codes"
        outfile_type = "rmag_anisotropy"
    else:
        specimen_col = "specimen"
        sample_col = "sample"
        site_col = "site"
        loc_col = "location"
        citation_col = "citations"
        analyst_col = "analysts"
        aniso_type_col = "aniso_type"
        experiment_col = "experiments"
        sigma_col = "aniso_s_sigma"
        unit_col = "aniso_s_unit"
        tilt_corr_col = "aniso_tilt_correction"
        method_col = "method_codes"
        outfile_type = "specimens"
    # get down to bidness
    sfile = pmag.resolve_file_name(sfile, dir_path)
    anisfile = pmag.resolve_file_name(anisfile, dir_path)
    try:
        with open(sfile, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False, "No such file: {}".format(sfile)
    AnisRecs = []
    citation = "This study"
    # read in data
    for line in lines:
        AnisRec = {}
        rec = line.split()
        if name_in_file:
            k = 1
            spec = rec[0]
        else:
            k = 0
        trace = float(rec[k])+float(rec[k+1])+float(rec[k+2])
        s1 = '%10.9e' % (old_div(float(rec[k]), trace))
        s2 = '%10.9e' % (old_div(float(rec[k+1]), trace))
        s3 = '%10.9e' % (old_div(float(rec[k+2]), trace))
        s4 = '%10.9e' % (old_div(float(rec[k+3]), trace))
        s5 = '%10.9e' % (old_div(float(rec[k+4]), trace))
        s6 = '%10.9e' % (old_div(float(rec[k+5]), trace))
        AnisRec[citation_col] = citation
        AnisRec[specimen_col] = spec
        if specnum != 0:
            AnisRec[sample_col] = spec[:specnum]
        else:
            AnisRec[sample_col] = spec
        #if samp_con == "6":
        #    for samp in Samps:
        #        if samp['er_sample_name'] == AnisRec["er_sample_name"]:
        #            sitename = samp['er_site_name']
        #            location = samp['er_location_name']
        if samp_con != "":
            sitename = pmag.parse_site(AnisRec[sample_col], samp_con, Z)
        AnisRec[loc_col] = location
        AnisRec[site_col] = sitename
        AnisRec[analyst_col] = user
        if atype == 'AMS':
            AnisRec[aniso_type_col] = "AMS"
            AnisRec[experiment_col] = spec+":LP-X"
        else:
            AnisRec[aniso_type_col] = atype
            AnisRec[experiment_col] = spec+":LP-"+atype
        if data_model_num != 3:
            AnisRec["anisotropy_s1"] = s1
            AnisRec["anisotropy_s2"] = s2
            AnisRec["anisotropy_s3"] = s3
            AnisRec["anisotropy_s4"] = s4
            AnisRec["anisotropy_s5"] = s5
            AnisRec["anisotropy_s6"] = s6
        else:
            AnisRec['aniso_s'] = ":".join([str(s) for s in [s1,s2,s3,s4,s5,s6]])
        if sigma:
                AnisRec[sigma_col] = '%10.8e' % (
                    old_div(float(rec[k+6]), trace))
                AnisRec[unit_col] = 'SI'
                AnisRec[tilt_corr_col] = coord
                AnisRec[method_col] = 'LP-' + atype
        AnisRecs.append(AnisRec)
    pmag.magic_write(anisfile, AnisRecs, outfile_type)
    print('data saved in ', anisfile)
    # try to extract location/site/sample info into tables
    con = nb.Contribution(dir_path, custom_filenames={"specimens": anisfile})
    con.propagate_all_tables_info()
    for table in con.tables:
        if table in ['samples', 'sites', 'locations']:
            # add in location name by hand
            if table == 'sites':
                con.tables['sites'].df['location'] = location
            con.write_table_to_file(table)
    return True, anisfile
