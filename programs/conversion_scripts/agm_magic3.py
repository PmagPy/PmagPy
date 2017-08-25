#!/usr/bin/env python
"""
NAME
    agm_magic.py

DESCRIPTION
    converts Micromag agm files to magic format

SYNTAX
    agm_magic.py [-h] [command line options]

OPTIONS
    -usr USER:   identify user, default is "" - put in quotation marks!
    -bak:  this is a IRM backfield curve
    -f FILE, specify input file, required
    -Fsp SPECFILE, specify specimens.txt file relating specimen to the sample; default is specimens.txt 
    -Fsa SAMPFILE, specify samples.txt file relating samples to  site; default is samples.txt 
    -Fsi SITEFILE, specify sites.txt file relating site to location; default is sites.txt 
    -Flo LOCFILE, specify locations.txt file; default is locations.txt 
    -F MFILE, specify measurements formatted output file, default is agm.magic
    -spn SPEC, specimen name, default is base of input file name, e.g. SPECNAME.agm
    -spc NUM, specify number of characters to designate a  specimen, default = 0
    -ncn NCON,: specify naming convention: default is #1 below
    -loc LOCNAME: specify location/study name.
    -ins INST : specify which instrument was used (e.g, SIO-Maud), default is ""
    -u units:  [cgs,SI], default is cgs

OUTPUT
    MagIC format files: measurements, specimens, sample, site
"""
from __future__ import print_function
from builtins import input
from builtins import str
import sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
import pytz, datetime

def convert(**kwargs):
    # initialize some stuff
    citations='This study'
    units='cgs'
    meth="LP-HYS"
    version_num=pmag.get_version()
    args=sys.argv
    Samps=[]
    noave=1

    #get args
    user = kwargs.get('user', '')
    dir_path = kwargs.get('dir_path', '.')
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt') # sample outfile
    site_file = kwargs.get('samp_file', 'site.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # location outfile
    agm_file = kwargs.get('agm_file', '')
    specnum = kwargs.get('specnum', 0)
    samp_con = kwargs.get('samp_con', '1')
    location = kwargs.get('location', 'unknown')
    samp_infile = kwargs.get('samp_infile', '')
    spec_infile = kwargs.get('spec_infile', '')
    inst = kwargs.get('ins', '')
    institution = kwargs.get('institution', '')
    syn = kwargs.get('syn', 0)
    syntype = kwargs.get('syntype', '')
    inst = kwargs.get('ins', '')
    bak=kwargs.get('bak', 0)
    specimen=kwargs.get('spn',0)
    units=kwargs.get('units',0)
    if bak:
        meth="LP-IRM-DCD"
        output = output_dir_path+"/irm.magic"
    fmt=kwargs.get('new',0)
    if fmt: 
        fmt='new'
    if not fmt: 
        fmt='old'
    if specnum!=0:
        specnum=-specnum
    if "4" == samp_con[0]:
        if "-" not in samp_con:
            print("naming convention option [4] must be in form 4-Z where Z is an integer")
            print('---------------')
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="4"
    if "7" == samp_con[0]:
        if "-" not in samp_con:
            print("option [7] must be in form 7-Z where Z is an integer")
            return False, "option [7] must be in form 7-Z where Z is an integer"
        else:
            Z=samp_con.split("-")[1]
            samp_con="7"
    else: Z = 0

    # read stuff in
    if samp_infile:
        Samps, file_type=pmag.magic_read(samp_infile)
    if spec_infile:
        Specs, file_type=pmag.magic_read(spec_infile)
    if agm_file:
        Data = pmag.open_file(agm_file)
        if not Data:
            print("you must provide a valid agm_file")
            return False, "you must provide a valid agm_file"
        if not specimen: 
            specimen=agm_file.split('.')[0] # grab the specimen name from the input file name
    if not agm_file:
        print(__doc__)
        print("agm_file field is required option")
        return False, "agm_file field is required option"
    
    if "ASCII" not in Data[0]:fmt='new'
    measnum,start=1,""
    if fmt=='new': # new Micromag formatted file
        end=2
        for skip in range(len(Data)):
            line=Data[skip]
            rec=line.strip('\n').strip('\r').split()
            if 'Units' in line:units=rec[-1]
            if "Raw" in rec:
                start=skip+2
            if "Field" in rec and "Moment" in rec and start=="":
                start=skip+2
                break
    else:
        start = 2
        end=1


    MeasRecs,SpecRecs,SampRecs,SiteRecs,LocRecs=[],[],[],[],[]
    version_num=pmag.get_version()

    ##################################
    # parse data
    stop=len(Data)-end
    for line in Data[start:stop]: # skip header stuff
        MeasRec,SpecRec,SampRec,SiteRec,LocRec={},{},{},{},{}
        # take care of some paper work
        if syn==0:
                MeasRec["specimen"]=specimen
                if specnum!=0:
                    sample=specimen[:specnum]
                else:
                    sample=specimen
                if samp_infile and Samps: # if samp_infile was provided AND yielded sample data
                    samp=pmag.get_dictitem(Samps,'sample',sample,'T')
                    if len(samp)>0:
                        location=samp[0]["location"]
                        site=samp[0]["site"]
                    else:
                        location=''
                        site=''
                else:
                    site=pmag.parse_site(sample,samp_con,Z)
                if location!='' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                    LocRec['location'] = location
                    LocRecs.append(LocRec)
                if site!='' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                    SiteRec['location'] = location
                    SiteRec['site'] = site
                    SiteRecs.append(SiteRec)
                if sample!='' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                    SampRec['site'] = site
                    SampRec['sample'] = sample
                    SampRecs.append(SampRec)
                if specimen!='' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                    SpecRec["specimen"]=specimen
                    SpecRec['sample'] = sample
                    SpecRecs.append(SpecRec)
        else:
                SampRec["material_type"]=syntype
                MeasRec["specimen"]=specimen
                if specnum!=0:
                    sample=specimen[:specnum]
                else:
                    sample=specimen
                site=pmag.parse_site(sample,samp_con,Z)
                if location!='' and location not in [x['location'] if 'location' in list(x.keys()) else '' for x in LocRecs]:
                    LocRec['location'] = location
                    LocRecs.append(LocRec)
                if site!='' and site not in [x['site'] if 'site' in list(x.keys()) else '' for x in SiteRecs]:
                    SiteRec['location'] = location
                    SiteRec['site'] = site
                    SiteRecs.append(SiteRec)
                if sample!='' and sample not in [x['sample'] if 'sample' in list(x.keys()) else '' for x in SampRecs]:
                    SampRec['site'] = site
                    SampRec['sample'] = sample
                    SampRecs.append(SampRec)
                if specimen!='' and specimen not in [x['specimen'] if 'specimen' in list(x.keys()) else '' for x in SpecRecs]:
                    SpecRec["specimen"]=specimen
                    SpecRec['sample'] = sample
                    SpecRecs.append(SpecRec)
        MeasRec['instrument_codes']=inst
        MeasRec['institution']=institution
        MeasRec['method_codes']=meth
        MeasRec['experiment']=specimen+':'+meth
        rec=list(line.strip('\n').strip('\r').split(','))
        if rec[0]!="":
            if units=='cgs':
                field =float(rec[0])*1e-4 # convert from oe to tesla
            else:
                field =float(rec[0]) # field in tesla
            if meth=="LP-HYS":
                MeasRec['meas_field_dc']='%10.3e'%(field) 
                MeasRec['treat_dc_field']='0'
            else:
                MeasRec['meas_field_dc']='0'
                MeasRec['treat_dc_field']='%10.3e'%(field) 
            if units=='cgs':
                MeasRec['magn_moment']='%10.3e'%(float(rec[1])*1e-3) # convert from emu to Am^2
            else:
                MeasRec['magn_moment']='%10.3e'%(float(rec[1])) # Am^2
            MeasRec['treat_temp']='273' # temp in kelvin
            MeasRec['meas_temp']='273' # temp in kelvin
            MeasRec['quality']='g'
            MeasRec['standard']='u'
            MeasRec['treat_step_num']='%i'%(measnum)
            MeasRec['measurement']=specimen+":"+meth+'%i'%(measnum)
            measnum+=1
            MeasRec['software_packages']=version_num
            MeasRec['description']=""
            MeasRecs.append(MeasRec) 
    # we have to relabel LP-HYS method codes.  initial loop is LP-IMT, minor loops are LP-M  - do this in measurements_methods function
    if meth=='LP-HYS':   
        recnum=0
        while float(MeasRecs[recnum]['meas_field_dc'])<float(MeasRecs[recnum+1]['meas_field_dc']) and recnum+1<len(MeasRecs): # this is LP-IMAG
            MeasRecs[recnum]['method_codes']='LP-IMAG'
            MeasRecs[recnum]['experiment']=MeasRecs[recnum]['specimen']+":"+'LP-IMAG'
            recnum+=1
#
    con = nb.Contribution(output_dir_path,read_tables=[])

    # create MagIC tables
    con.add_magic_table_from_data(dtype='specimens', data=SpecRecs)
    con.add_magic_table_from_data(dtype='samples', data=SampRecs)
    con.add_magic_table_from_data(dtype='sites', data=SiteRecs)
    con.add_magic_table_from_data(dtype='locations', data=LocRecs)
    #MeasOuts=pmag.measurements_methods3(MeasRecs,noave)
    con.add_magic_table_from_data(dtype='measurements', data=MeasRecs)
    # write MagIC tables to file
    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

def do_help():
    return __doc__

def main():
    kwargs = {}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-bak' in sys.argv: kwargs['bak']=1
    if '-new' in sys.argv: kwargs['fmt']='new'
    if '-WD' in sys.argv:
        ind=sys.argv.index("-WD")
        kwargs['dir_path']=sys.argv[ind+1]
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
    if '-f' in sys.argv:
        ind=sys.argv.index("-f")
        kwargs['agm_file']=sys.argv[ind+1]
    if "-spc" in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=int(sys.argv[ind+1])
    if "-spn" in sys.argv:
        ind=sys.argv.index("-spn")
        kwargs['specimen']=int(sys.argv[ind+1])
    if "-loc" in sys.argv:
        ind=sys.argv.index("-loc")
        kwargs['location']=sys.argv[ind+1]
    if "-fsa" in sys.argv:
        ind=sys.argv.index("-fsa")
        kwargs['samp_infile'] = sys.argv[ind+1]
    if '-syn' in sys.argv:
        syn=1
        ind=sys.argv.index("-syn")
        kwargs['institution']=sys.argv[ind+1]
        kwargs['syntype']=sys.argv[ind+2]
        if '-fsy' in sys.argv:
            ind=sys.argv.index("-fsy")
            synfile=sys.argv[ind+1]
    if "-ins" in sys.argv:
        ind=sys.argv.index("-ins")
        kwargs['ins']=sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if "-u" in sys.argv:
        ind=args.index("-u")
        units=args[ind+1]


    convert(**kwargs)

if __name__ == "__main__":
    main()

