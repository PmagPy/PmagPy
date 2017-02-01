#!/usr/bin/env python
"""
NAME
    cit_magic.py

DESCRIPTION
    converts CIT and .sam  format files to magic_measurements format files

SYNTAX
    cit_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -usr USER: Colon delimited list of analysts, default is "" 
    -f FILE: specify .sam format input file, required
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt 
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -n [gm,kg,cc,m3]: specify normalization
    -A: don't average replicate measurements
    -spc NUM : specify number of characters to designate a  specimen, default = 0
    -ncn NCON: specify naming convention
    -loc LOCNAME : specify location/study name, must have either LOCNAME or SITEFILE or be a synthetic
    -mcd [FS-FD:SO-MAG,.....] colon delimited list for method codes applied to all specimens in .sam file
    -dc (B, PHI, THETA): dc lab field (in microTesla), phi,and theta must be input as a tuple "(DC,PHI,THETA)". If not input user will be asked for values, this is advantagious if there are differing dc fields between steps or specimens. Note: this currently only works with the decimal IZZI naming convetion (XXX.0,1,2 where XXX is the treatment temperature and 0 is a zero field step, 1 is in field, and 2 is a PTRM check). For some reason all other steps are hardcoded dc_field = 0.
    -ac B : peak AF field (in mT) for ARM acquisition, default is none
    -mno: specify measurement orientation number (meas_n_orient in data model 3.0) (default = 8)

INPUT
    Best to put separate experiments (all AF, thermal, thellier, trm aquisition, Shaw, etc.)

NOTES:
     Sample naming convention:
    [1] XXXXY: where XXXX is an arbitrary length site designation and Y
        is the single character sample designation.  e.g., TG001a is the
        first sample from site TG001.    [default]
    [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
    [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
    [5] site name = sample name
    [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
    [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    NB: all others you will have to either customize your
        self or e-mail ltauxe@ucsd.edu for help.
"""
import os,sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from pandas import DataFrame

def main(**kwargs):
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
    norm : is volume or mass using cgs or si units (options : cc,m3) (default : cc)
    avg : average measurement data or not. False is average, True is don't average. (default : False)
    samp_con : sample naming convention options as follows:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    input_dir_path : if you did not supply a full path with magfile you can put the directory the magfile is in here
    meas_n_orient : Number of different orientations in measurement (default : 8)
    dc_params : tuple which gives (DC_FIELD,DC_PHI,DC_THETA) and DC_FIELD is in microTesla (default : (0,0,0))

    Returns
    -----------
    type - Tuple : (True or False indicating if conversion was sucessful, meas_file name written)
    """
    dir_path = kwargs.get('dir_path', '.')
    user = kwargs.get('user', '')
    meas_file = kwargs.get('meas_file', 'measurements.txt') # outfile
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt') # sample outfile
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # location outfile
    locname = kwargs.get('locname', 'unknown')
    methods = kwargs.get('methods', ['SO-MAG'])
    specnum = -int(kwargs.get('specnum', 0))
    norm = kwargs.get('norm', 'cc')
    avg = kwargs.get('avg', 0)  # 0 means do average, 1 means don't
    samp_con = kwargs.get('samp_con', '3')
    magfile = kwargs.get('magfile', '')
    input_dir_path = kwargs.get('input_dir_path',os.path.split(magfile)[0])
    meas_n_orient = kwargs.get('meas_n_orient','8')
    output_dir_path = dir_path
    DC_FIELD,DC_PHI,DC_THETA = map(float, kwargs.get('dc_params', (0,0,0)))
    DC_FIELD *= 1e-6
    yn = ''
    if DC_FIELD==0 and DC_PHI==0 and DC_THETA==0: GET_DC_PARAMS=True
    else: GET_DC_PARAMS=False
    if locname=='' or locname==None: locname = 'unknown'
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 4-Z where Z is an integer")
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"
    else: Z=1

    #get file names and open magfile to start reading data
    if input_dir_path=='': input_dir_path='.'
    magfile = os.path.join(input_dir_path, magfile)
    spec_file = os.path.join(output_dir_path, spec_file)
    samp_file = os.path.join(output_dir_path, samp_file)
    site_file = os.path.join(output_dir_path, site_file)
    meas_file= os.path.join(output_dir_path, meas_file)
    FIRST_GET_DC=True
    try:
        file_input=open(magfile,'r')
    except Exception as ex:
        print("bad sam file name: ", magfile)
        return False, "bad sam file name"
    File = file_input.readlines()
    if len(File) == 1: File = File[0].split('\r'); File = [x+"\r\n" for x in File]

    #define initial variables
    Specs,Samps,Sites,Locs,MeasRecs=[],[],[],[],[]
    sids,ln,format,citation=[],0,'CIT',"This study"
    formats=['CIT','2G','APP','JRA']

    if File[ln].strip()=='CIT': ln+=1
    LocRec={}
    LocRec["location"]=locname
    LocRec["citation"]=citation
    LocRec['analysts']=user
    comment=File[ln]
    if comment=='CIT':
       format=comment
       ln+=1
    comment=File[ln]
    print(comment)
    ln+=1
    specimens,samples,sites=[],[],[]
    if format=='CIT':
        line=File[ln].split()
        site_lat=line[0]
        site_lon=line[1]
        LocRec["lat_n"]=site_lat
        LocRec["lon_e"]=site_lon
        LocRec["lat_s"]=site_lat
        LocRec["lon_w"]=site_lon
        Locs.append(LocRec)
        Cdec=float(line[2])
        for k in range(ln+1,len(File)):
            line=File[k]
            rec=line.split()
            if rec == []: continue
            specimen=rec[0]
            specimens.append(specimen)
    for specimen in specimens:
        SpecRec,SampRec,SiteRec={},{},{}
        if specnum!=0:
            sample=specimen[:specnum]
        else: sample=specimen
        site=pmag.parse_site(sample,samp_con,Z)
        SpecRec['specimen']=specimen
        SpecRec['sample']=sample
        SpecRec['citation']=citation
        SpecRec['analysts']=user
        SampRec['sample']=sample
        SampRec['site']=site
        SampRec['citation']=citation
        SampRec['method_codes']=methods
        SampRec['azimuth_dec_correction']='%7.1f'%(Cdec)
        SampRec['analysts']=user
        SiteRec['site']=site
        SiteRec['location']=locname
        SiteRec['citation']=citation
        SiteRec['lat']=site_lat
        SiteRec['lon']=site_lon
        SiteRec['analysts']=user
        f=open(input_dir_path+'/'+specimen,'rU')
        Lines=f.readlines()
        comment=""
        line=Lines[0].split()
        if len(line)>2:
            comment=line[2]
        info=Lines[1].split()
        vol=float(info[-1])
        if vol!=1.0:
            if norm=='cc':units="1"
            if norm=='m3':units="2"
            SpecRec['weight']=""
            if units=="1" or "":
                SpecRec['volume']='%10.3e'%(vol*1e-6)
            else:
                SpecRec['volume']='%10.3e'%(vol)
        else:
            if norm=='cc':units="1"
            if norm=='m3':units="2"
            SpecRec['volume']=""
            if units=="1" or "":
                SpecRec['weight']='%10.3e'%(vol*1e-3)
            else:
                SpecRec['weight']='%10.3e'%(vol)
        dip=float(info[-2])
        dip_direction=float(info[-3])+Cdec+90.
        sample_dip=-float(info[-4])
        sample_azimuth=float(info[-5])+Cdec-90.
        if len(info)>5:
            SampRec['height']=info[-6]
        else:
            SampRec['height']='0'
        SampRec['azimuth']='%7.1f'%(sample_azimuth)
        SampRec['dip']='%7.1f'%(sample_dip)
        SampRec['bed_dip']='%7.1f'%(dip)
        SampRec['bed_dip_direction']='%7.1f'%(dip_direction)
        SampRec['geologic_class']=''
        SampRec['geologic_type']=''
        SampRec['lithologies']=''
        if Cdec!=0 or Cdec!="":
            SampRec['method_codes']='SO-CMD-NORTH'
        else:
            SampRec['method_codes']='SO-MAG'
        for line in Lines[2:len(Lines)]:
            #print 'line:', line
            MeasRec=SpecRec.copy()
            MeasRec.pop('sample')
            MeasRec['analysts']=user
#           Remove volume and weight as they do not exits in the magic_measurement table
            del MeasRec["volume"]
            del MeasRec["weight"]
            treat_type=line[0:3]
            if treat_type[1] == '.':
                treat_type = 'NRM'
            treat=line[2:6]
            try: float(treat)
            except ValueError: treat = line[3:6]
            if treat_type.startswith('NRM'):
                MeasRec['method_codes']='LT-NO'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']='273'
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            elif treat_type.startswith('AF'):
                MeasRec['method_codes']='LT-AF-Z'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']='273'
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field']='0'
                else:
                    MeasRec['treat_ac_field']='%10.3e'%(float(treat)*1e-3)
            elif treat_type.startswith('ARM'):
                MeasRec['method_codes']="LP-ARM"
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']='273'
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                if treat.strip() == '':
                    MeasRec['treat_ac_field']='0'
                else:
                    MeasRec['method_codes']="LP-ARM-AFD"
                    MeasRec['treat_ac_field']='%10.3e'%(float(treat)*1e-3)
            elif treat_type.startswith('TT'):
                MeasRec['method_codes']='LT-T-Z'
                MeasRec['meas_temp']='273'
                if treat.strip() == '':
                    MeasRec['treat_temp']='273'
                else:
                    MeasRec['treat_temp']='%7.1f'%(float(treat)+273)
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            elif treat_type.startswith('LT') or treat_type.upper().startswith('LN2'):
                MeasRec['method_codes']='LT-LT-Z'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']='77'
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            elif line[4] == '0': #assume decimal IZZI format 0 field thus can hardcode the dc fields
                MeasRec['method_codes']='LT-T-Z'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']=str(int(treat_type) + 273)
                MeasRec['treat_dc_field']='0'
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            elif line[4] == '1': #assume decimal IZZI format in constant field
                if GET_DC_PARAMS: GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(FIRST_GET_DC,specimen,treat_type,yn)
                MeasRec['method_codes']='LT-T-I'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']=str(int(treat_type) + 273)
                MeasRec['treat_dc_field']='%1.2e'%DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            elif line[4] == '2': #assume decimal IZZI format PTRM step
                if GET_DC_PARAMS: GET_DC_PARAMS, FIRST_GET_DC, yn, DC_FIELD, DC_PHI, DC_THETA = get_dc_params(FIRST_GET_DC,specimen,treat_type,yn)
                MeasRec['method_codes']='LT-PTRM-I'
                MeasRec['meas_temp']='273'
                MeasRec['treat_temp']=str(int(treat_type) + 273)
                MeasRec['treat_dc_field']='%1.2e'%DC_FIELD
                MeasRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
                MeasRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
                MeasRec['treat_ac_field']='0'
            else:
                print("trouble with your treatment steps")
            MeasRec['dir_dec']=line[46:51]
            MeasRec['dir_inc']=line[52:58]
            M='%8.2e'%(float(line[31:39])*vol*1e-3) # convert to Am2
            MeasRec['magn_moment']=M
            MeasRec['dir_csd']='%7.1f'%(eval(line[41:46]))
            MeasRec["meas_n_orient"]=meas_n_orient
            MeasRec['standard']='u'
            if len(line)>60:
                MeasRec['instrument_codes']=line[85:].strip('\n \r \t "')
                MeasRec['magn_x_sigma']='%8.2e'%(float(line[58:67])*1e-8) #(convert e-5emu to Am2)
                MeasRec['magn_y_sigma']='%8.2e'%(float(line[67:76])*1e-8)
                MeasRec['magn_z_sigma']='%8.2e'%(float(line[76:85])*1e-8)
            MeasRecs.append(MeasRec)
        Specs.append(SpecRec)
        if sample not in samples:
            samples.append(sample)
            Samps.append(SampRec)
        site=pmag.parse_site(sample,samp_con,Z)
        if site not in sites:
            sites.append(site)
            Sites.append(SiteRec)

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_empty_magic_table('specimens')
    con.add_empty_magic_table('samples')
    con.add_empty_magic_table('sites')
    con.add_empty_magic_table('locations')
    con.add_empty_magic_table('measurements')

    con.tables['specimens'].df = DataFrame(Specs)
    con.tables['samples'].df = DataFrame(Samps)
    con.tables['sites'].df = DataFrame(Sites)
    con.tables['locations'].df = DataFrame(Locs)
    Fixed=pmag.measurements_methods3(MeasRecs,avg)
    con.tables['measurements'].df = DataFrame(Fixed)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    print('specimens stored in ',spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    print('samples stored in ',samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    print('sites stored in ', site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    print('locations stored in ', loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)
    print('data stored in ',meas_file)

    return True, meas_file


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
        yn = raw_input("Is the DC field used in this IZZI study constant or does it varry between specimen or step? (y=const) [y/N]: ")
        FIRST_GET_DC = False
    if "y" == yn: DC_FIELD,DC_PHI,DC_THETA = map(float, input("What DC field, Phi, and Theta was used for all steps? (float (in microTesla),float,float): ")); GET_DC_PARAMS=False
    else: DC_FIELD,DC_PHI,DC_THETA = map(float,input("What DC field, Phi, and Theta was used for specimen %s and step %s? (float (in microTesla),float,float): "%(str(specimen),str(treat_type))))
    return GET_DC_PARAMS,FIRST_GET_DC,yn,DC_FIELD*1e-6,DC_PHI,DC_THETA

def do_help():
    """
    returns help string of script
    """
    return __doc__

if __name__ == "__main__":
    kwargs = {}
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        kwargs['dir_path']=sys.argv[ind+1]
    if "-h" in sys.argv:
        print(__doc__)
        sys.exit()
    if "-usr" in sys.argv:
        ind=sys.argv.index("-usr")
        kwargs['user']=sys.argv[ind+1]
    if '-F' in sys.argv:
        ind=sys.argv.index("-F")
        kwargs['meas_file']=sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind=sys.argv.index("-Fsa")
        kwargs['samp_file']=sys.argv[ind+1]
    if '-Fsi' in sys.argv:   # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv:
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-loc' in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['locname']=sys.argv[ind+1]
    if '-mcd' in sys.argv:
        ind=sys.argv.index("-mcd")
        kwargs['methods']=sys.argv[ind+1]
    else:
        kwargs['methods']='SO-MAG'
    if '-spc' in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=sys.argv[ind+1]
    if '-n' in sys.argv:
        ind=sys.argv.index("-n")
        kwargs['norm']=sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['avg'] = True
    if '-dc' in sys.argv:
        ind=sys.argv.index('-dc')
        kwargs['dc_params']=sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['magfile']=sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path']=sys.argv[ind+1]
    else:
        kwargs['input_dir_path'] = os.path.split(kwargs['magfile'])[0]
    if '-mno' in sys.argv:
        ind = sys.argv.index('-mno')
        kwargs['meas_n_orient'] = sys.argv[ind+1]

    main(**kwargs)
