#!/usr/bin/env/pythonw

import sys, os
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from functools import reduce


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
