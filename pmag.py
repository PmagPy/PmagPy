import  numpy,string,sys
from numpy import random
import numpy.linalg
import exceptions
import os
import check_updates
def get_version():
    version=check_updates.get_version()
    return version
def sort_diclist(undecorated,sort_on):
    decorated=[(dict_[sort_on],dict_) for dict_ in undecorated]
    decorated.sort()
    return[dict_ for (key, dict_) in decorated]

def get_dictitem(In,k,v,flag):  
    # returns a list of dictionaries from list In with key,k  = value, v . CASE INSENSITIVE # allowed keywords:
    try:
        if flag=="T":return [dict for dict in In if dict[k].lower()==v.lower()] # return that which is
        if flag=="F":return [dict for dict in In if dict[k].lower()!=v.lower()] # return that which is not
        if flag=="has":return [dict for dict in In if v.lower() in dict[k].lower()] # return that which is contained
        if flag=="not":return [dict for dict in In if v.lower() not in dict[k].lower()] # return that which is not contained
        if flag=="eval":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])==float(v)] # return that which is
        if flag=="min":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])>=float(v)] # return that which is greater than
        if flag=="max":
            A=[dict for dict in In if dict[k]!=''] # find records with no blank values for key
            return [dict for dict in A if float(dict[k])<=float(v)] # return that which is less than
    except Exception, err:
        return []

def get_dictkey(In,k,dtype): 
    # returns list of given key from input list of dictionaries
    Out=[]
    for d in In: 
        if dtype=='': Out.append(d[k]) 
        if dtype=='f':Out.append(float(d[k]))
        if dtype=='int':Out.append(int(d[k]))
    return Out 
        

def find(f,seq):
    for item in seq:
       if f in item: return item
    return ""

def get_orient(samp_data,er_sample_name):
    # set orientation priorities
    EX=["SO-ASC","SO-POM"]
    orient={'er_sample_name':er_sample_name,'sample_azimuth':"",'sample_dip':"",'sample_description':""}
    orients=get_dictitem(samp_data,'er_sample_name',er_sample_name,'T') # get all the orientation data for this sample
    if len(orients)>0:orient=orients[0] # re-initialize to first one
    methods=get_dictitem(orients,'magic_method_codes','SO-','has')
    methods=get_dictkey(methods,'magic_method_codes','') # get a list of all orientation methods for this sample
    SO_methods=[]
    for methcode in methods:
        meths=methcode.split(":")
        for meth in meths:
           if meth.strip() not in EX:SO_methods.append(meth)
   # find top priority orientation method
    if len(SO_methods)==0:
        print "no orientation data for ",er_sample_name
        az_type="SO-NO"
    else:
        SO_priorities=set_priorities(SO_methods,0)
        az_type=SO_methods[SO_methods.index(SO_priorities[0])]
        orient=get_dictitem(orients,'magic_method_codes',az_type,'has')[0] # re-initialize to best one
    return orient,az_type
    

def cooling_rate(SpecRec,SampRecs,crfrac,crtype):
    CrSpecRec,frac,crmcd={},0,'DA-CR'
    for key in SpecRec.keys():CrSpecRec[key]=SpecRec[key]
    if len(SampRecs)>0:
        frac=.01*float(SampRecs[0]['cooling_rate_corr'])
        if 'DA-CR' in SampRecs[0]['cooling_rate_mcd']:
            crmcd=SampRecs[0]['cooling_rate_mcd']
        else:
            crmcd='DA-CR'
    elif crfrac!=0:
        frac=crfrac
        crmcd=crtype
    if frac!=0:
        inten=frac*float(CrSpecRec['specimen_int'])
        CrSpecRec["specimen_int"]='%9.4e '%(inten) # adjust specimen intensity by cooling rate correction
        CrSpecRec['magic_method_codes'] = CrSpecRec['magic_method_codes']+':crmcd'
        CrSpecRec["specimen_correction"]='c'
        return CrSpecRec
    else:
        return []


def convert_lat(Recs):
    """
    uses lat, for age<5Ma, model_lat if present, else tries to use average_inc to estimate plat.
    """
    New=[]
    for rec in Recs:
        if 'model_lat' in rec.keys() and rec['model_lat']!="":
             New.append(rec)
        elif 'average_age'  in rec.keys() and rec['average_age']!="" and  float(rec['average_age'])<=5.: 
            if 'site_lat' in rec.keys() and rec['site_lat']!="":
                 rec['model_lat']=rec['site_lat']
                 New.append(rec)
        elif 'average_inc' in rec.keys() and rec['average_inc']!="":
            rec['model_lat']='%7.1f'%(plat(float(rec['average_inc']))) 
            New.append(rec)
    return New

def convert_ages(Recs):
    """
    converts ages to Ma
    """
    New=[]
    for rec in Recs:
        age=''
        agekey=find('age',rec.keys())
        if agekey!="":
            keybase=agekey.split('_')[0]+'_'
            if rec[keybase+'age']!="": 
                age=float(rec[keybase+"age"])
            elif rec[keybase+'age_low']!="" and rec[keybase+'age_high']!='':
                age=float(rec[keybase+'age_low'])  +(float(rec[keybase+'age_high'])-float(rec[keybase+'age_low']))/2.
            if age!='':
                rec[keybase+'age_unit']
                if rec[keybase+'age_unit']=='Ma':
                    rec[keybase+'age']='%10.4e'%(age)
                elif rec[keybase+'age_unit']=='ka' or rec[keybase+'age_unit']=='Ka':
                    rec[keybase+'age']='%10.4e'%(age*.001)
                elif rec[keybase+'age_unit']=='Years AD (+/-)':
                    rec[keybase+'age']='%10.4e'%((2011-age)*1e-6)
                elif rec[keybase+'age_unit']=='Years BP':
                    rec[keybase+'age']='%10.4e'%((age)*1e-6)
                rec[keybase+'age_unit']='Ma'
                New.append(rec)
            else:
                if 'er_site_names' in rec.keys():
                    print 'problem in convert_ages:', rec['er_site_names']
                elif 'er_site_name' in rec.keys():
                    print 'problem in convert_ages:', rec['er_site_name']
                else:
                    print 'problem in convert_ages:', rec
        else:
            print 'no age key:', rec
    return New

def getsampVGP(SampRec,SiteNFO):
    site=get_dictitem(SiteNFO,'er_site_name',SampRec['er_site_name'],'T')
    try:
        lat=float(site['site_lat'])    
        lon=float(site['site_lon'])
        dec = float(SampRec['sample_dec'])
        inc = float(SampRec['sample_inc'])
        if SampRec['sample_alpha95']!="":
            a95=float(SampRec['sample_alpha95'])
        else:
            a95=0
        plong,plat,dp,dm=dia_vgp(dec,inc,a95,lat,lon)         
        ResRec={}
        ResRec['pmag_result_name']='VGP Sample: '+SampRec['er_sample_name']
        ResRec['er_location_names']=SampRec['er_location_name']
        ResRec['er_citation_names']="This study"
        ResRec['er_site_name']=SampRec['er_site_name']
        ResRec['average_dec']=SampRec['sample_dec']
        ResRec['average_inc']=SampRec['sample_inc']
        ResRec['average_alpha95']=SampRec['sample_alpha95']
        ResRec['tilt_correction']=SampRec['sample_tilt_correction']
        ResRec['pole_comp_name']=SampleRec['sample_comp_name']
        ResRec['vgp_lat']='%7.1f'%(plat)
        ResRec['vgp_lon']='%7.1f'%(plon)
        ResRec['vgp_dp']='%7.1f'%(dp)
        ResRec['vgp_dm']='%7.1f'%(dm)
        ResRec['magic_method_codes']=SampRec['magic_method_codes']+":DE-DI"
        return ResRec
    except:
        return ""

def getsampVDM(SampRec,SampNFO):
    samp=get_dictitem(SampNFO,'er_sample_name',SampRec['er_sample_name'],'T')[0]
    lat=float(samp['sample_lat'])    
    int = float(SampRec['sample_int'])
    vdm=b_vdm(int,lat)     
    if 'sample_int_sigma' in SampRec.keys() and  SampRec['sample_int_sigma']!="":
        sig=b_vdm(float(SampRec['sample_int_sigma']),lat)
        sig='%8.3e'%(sig)
    else:
        sig=""
    ResRec={}
    ResRec['pmag_result_name']='V[A]DM Sample: '+SampRec['er_sample_name']
    ResRec['er_location_names']=SampRec['er_location_name']
    ResRec['er_citation_names']="This study"
    ResRec['er_site_names']=SampRec['er_site_name']
    ResRec['er_sample_names']=SampRec['er_sample_name']
    if 'sample_dec' in SampRec.keys():
        ResRec['average_dec']=SampRec['sample_dec']
    else:
        ResRec['average_dec']=""
    if 'sample_inc' in SampRec.keys():
        ResRec['average_inc']=SampRec['sample_inc']
    else:
        ResRec['average_inc']=""
    ResRec['average_int']=SampRec['sample_int']
    ResRec['vadm']='%8.3e'%(vdm)
    ResRec['vadm_sigma']=sig
    ResRec['magic_method_codes']=SampRec['magic_method_codes']
    ResRec['model_lat']=samp['sample_lat']
    return ResRec

def getfield(irmunits,coil,treat):
# calibration of ASC Impulse magnetizer
    if coil=="3": m,b=0.0071,-0.004 # B=mh+b where B is in T, treat is in Volts
    if coil=="2": m,b=0.00329,-0.002455 # B=mh+b where B is in T, treat is in Volts
    if coil=="1": m,b=0.0002,-0.0002 # B=mh+b where B is in T, treat is in Volts
    return float(treat)*m+b 
     

def sortbykeys(input,sort_list):
    Output = []
    List=[] # get a list of what to be sorted by second key
    for rec in input:
        if rec[sort_list[0]] not in List:List.append(rec[sort_list[0]])
    for current in List: # step through input finding all records of current
        Currents=[]
        for rec in input:
            if rec[sort_list[0]]==current:Currents.append(rec)
        Current_sorted=sort_diclist(Currents,sort_list[1])
        for rec in Current_sorted:
            Output.append(rec)
    return Output

def get_list(data,key): # return a colon delimited list of unique key values
    keylist=[]
    for rec in data:
        keys=rec[key].split(':')
        for k in keys: 
            if k not in keylist:keylist.append(k)
    keystring=""
    if len(keylist)==0:return keystring
    for k in keylist:keystring=keystring+':'+k
    return keystring[1:]

def ParseSiteFile(site_file):
    Sites,file_type=magic_read(site_file)
    LocNames,Locations=[],[]
    for site in Sites:
        if site['er_location_name'] not in LocNames: # new location name
            LocNames.append(site['er_location_name'])
            sites_locs=get_dictitem(Sites,'er_location_name',site['er_location_name'],'T') # get all sites for this loc
            lats=get_dictkey(sites_locs,'site_lat','f') # get all the latitudes as floats
            lons=get_dictkey(sites_locs,'site_lon','f') # get all the longitudes as floats
            LocRec={'er_citation_names':'This study','er_location_name':site['er_location_name'],'location_type':''}
            LocRec['location_begin_lat']=str(min(lats))
            LocRec['location_end_lat']=str(max(lats))
            LocRec['location_begin_lon']=str(min(lons))
            LocRec['location_end_lon']=str(max(lons))
            Locations.append(LocRec)
    return Locations

def ParseMeasFile(measfile,sitefile,instout,specout): # fix up some stuff for uploading
    #
    # read in magic_measurements file to get specimen, and instrument names
    #
    master_instlist=[]
    InstRecs=[]
    meas_data,file_type=magic_read(measfile)
    if file_type != 'magic_measurements':
        print file_type,"This is not a valid magic_measurements file "
        sys.exit()
    # read in site data
    if sitefile!="":
        SiteNFO,file_type=magic_read(sitefile)
        if file_type=="bad_file":
            print "Bad  or no er_sites file - lithology, etc will not be imported"
    else:
        SiteNFO=[]
    # define the Er_specimen records to create a new er_specimens.txt file
    #
    suniq,ErSpecs=[],[]
    for rec in meas_data:
# fill in some potentially missing fields
        if "magic_instrument_codes" in rec.keys():
            list=(rec["magic_instrument_codes"])
            list.strip()
            tmplist=list.split(":")
            for inst in tmplist:
                if inst not in master_instlist:
                    master_instlist.append(inst)
                    InstRec={}
                    InstRec["magic_instrument_code"]=inst
                    InstRecs.append(InstRec)
        if "measurement_standard" not in rec.keys():rec['measurement_standard']='u' # make this an unknown if not specified
        if rec["er_specimen_name"] not in suniq and rec["measurement_standard"]!='s': # exclude standards
            suniq.append(rec["er_specimen_name"])
            ErSpecRec={}
            ErSpecRec["er_citation_names"]="This study"
            ErSpecRec["er_specimen_name"]=rec["er_specimen_name"]
            ErSpecRec["er_sample_name"]=rec["er_sample_name"]
            ErSpecRec["er_site_name"]=rec["er_site_name"]
            ErSpecRec["er_location_name"]=rec["er_location_name"]
    #
    # attach site litho, etc. to specimen if not already there
            sites=get_dictitem(SiteNFO,'er_site_name',rec['er_site_name'],'T')
            if len(sites)==0:
                site={}
                print 'site record in er_sites table not found for: ',rec['er_site_name']
            else:
                site=sites[0]
            if 'site_class' not in site.keys() or 'site_lithology' not in site.keys() or 'site_type' not in site.keys():
                site['site_class']='Not Specified'
                site['site_lithology']='Not Specified'
                site['site_type']='Not Specified'
            if 'specimen_class' not in ErSpecRec.keys():ErSpecRec["specimen_class"]=site['site_class'] 
            if 'specimen_lithology' not in ErSpecRec.keys():ErSpecRec["specimen_lithology"]=site['site_lithology'] 
            if 'specimen_type' not in ErSpecRec.keys():ErSpecRec["specimen_type"]=site['site_type'] 
            if 'specimen_volume' not in ErSpecRec.keys():ErSpecRec["specimen_volume"]=""
            if 'specimen_weight' not in ErSpecRec.keys():ErSpecRec["specimen_weight"]=""
            ErSpecs.append(ErSpecRec)
    #
    #
    # save the data
    #
    magic_write(specout,ErSpecs,"er_specimens")
    print " Er_Specimen data (with updated info from site if necessary)  saved in ",specout
    #
    # write out the instrument list
    if len(InstRecs) >0:
        magic_write(instout,InstRecs,"magic_instruments")
        print " Instruments data saved in ",instout
    else: 
        print "No instruments found"

def ReorderSamples(specfile,sampfile,outfile): # take care of re-ordering sample table, putting used orientations first
    UsedSamps,RestSamps=[],[]
    Specs,filetype=magic_read(specfile) # read in specimen file
    Samps,filetype=magic_read(sampfile) # read in sample file
    for rec in Specs: # hunt through specimen by specimen
        meths=rec['magic_method_codes'].strip().strip('\n').split(':')
        for meth in meths:
            methtype=meth.strip().strip('\n').split('-')
            if 'SO' in methtype:
                SO_meth=meth # find the orientation method code
        samprecs=get_dictitem(Samps,'er_sample_name',rec['er_sample_name'],'T')
        used=get_dictitem(samprecs,'magic_method_codes',SO_meth,'has') 
        if len(used)>0:
            UsedSamps.append(used[0])
        else:
            print 'orientation not found for: ',rec['er_specimen_name']
        rest=get_dictitem(samprecs,'magic_method_codes',SO_meth,'not') 
        for rec in rest:
            RestSamps.append(rec)
    for rec in RestSamps:
        UsedSamps.append(rec) # append the unused ones to the end of the file
    magic_write(outfile,UsedSamps,'er_samples')

def orient(mag_azimuth,field_dip,or_con):
    """
    uses specified orientation convention to convert user supplied orientations
    to laboratory azimuth and plunge
    """
#
    if mag_azimuth==-999:return "",""
    if or_con=="1": # lab_mag_az=mag_az;  sample_dip = -dip
        return mag_azimuth, -field_dip
    if or_con=="2":
        return mag_azimuth-90.,-field_dip
    if or_con=="3": # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth, 90.-field_dip
    if or_con=="4": # lab_mag_az=mag_az;  sample_dip = dip
        return mag_azimuth, field_dip
    if or_con=="5": # lab_mag_az=mag_az;  sample_dip = dip-90.
        return mag_azimuth, field_dip-90.
    if or_con=="6": # lab_mag_az=mag_az-90.;  sample_dip = 90.-dip
        return mag_azimuth-90., 90.-field_dip
    if or_con=="7": # lab_mag_az=mag_az;  sample_dip = 90.-dip
        return mag_azimuth-90., 90.-field_dip
    print "Error in orientation convention"


def get_Sb(data):
    """
    returns vgp scatter for data set
    """
    Sb,N=0.,0.
    for  rec in data:
                delta=90.-abs(float(rec['vgp_lat']))
                if rec['average_k']!="0":
                    k=float(rec['average_k'])
                    L=float(rec['average_lat'])*numpy.pi/180. # latitude in radians
                    Nsi=float(rec['average_nn'])
                    K=k/(2.*(1.+3.*numpy.sin(L)**2)/(5.-3.*numpy.sin(L)**2))
                    Sw=81./numpy.sqrt(K)
                else:
                    Sw,Nsi=0,1
                Sb+=delta**2-(Sw**2)/Nsi
                N+=1.
    return numpy.sqrt( Sb/float(N-1.) )
def default_criteria(nocrit):
    Crits={}
    if nocrit==0: # use default criteria
# 
# set some sort of quasi-reasonable default criteria
#   
        Crits['pmag_criteria_code']='ACCEPT'
        Crits['criteria_definition']='acceptance criteria for study'
        Crits['er_citation_names']='This study'
        Crits['specimen_mad']='5'
        Crits['specimen_alpha95']='5'
        Crits['specimen_n']='4'
        Crits['specimen_int_ptrm_n']='2'
        Crits['specimen_drats']='20'
        Crits['specimen_b_beta']='0.1'
        Crits['specimen_md']='15'
        Crits['specimen_fvds']='0.7'
        Crits['specimen_q']='1.0'
        Crits['specimen_dang']='10'
        Crits['specimen_int_mad']='10'
    #    Crits['measurement_step_min']='1000'
    #    Crits['measurement_step_max']='0'
        Crits['sample_alpha95']='10'
        Crits['sample_int_n']='2'
        Crits['sample_int_sigma']='5e-6'
        Crits['sample_int_sigma_perc']='15'
        Crits['site_int_n']='2'
        Crits['site_int_sigma']='5e-6' 
        Crits['site_int_sigma_perc']='15'
        Crits['site_n']='5'
        Crits['site_n_lines']='4'
        Crits['site_k']='50'
        Crits['site_alpha95']='180'
    else:
        Crits['pmag_criteria_code']='ACCEPT'
        Crits['criteria_definition']='acceptance criteria for study'
        Crits['er_citation_names']='This study'
        Crits['specimen_mad']='180'
        Crits['specimen_alpha95']='180'
        Crits['specimen_n']='0'
        Crits['specimen_int_ptrm_n']='0'
        Crits['specimen_drats']='180'
        Crits['specimen_b_beta']='100'
        Crits['specimen_md']='100'
        Crits['specimen_fvds']='0'
        Crits['specimen_q']='0'
        Crits['specimen_dang']='180'
        Crits['specimen_int_mad']='180'
    #    Crits['measurement_step_min']='0'
    #    Crits['measurement_step_max']='0'
        Crits['sample_alpha95']='180'
        Crits['sample_int_n']='0'
        Crits['sample_int_sigma']='100'
        Crits['sample_int_sigma_perc']='100'
        Crits['site_int_n']='0'
        Crits['site_int_sigma']='100'
        Crits['site_int_sigma_perc']='1000'
        Crits['site_n']='0'
        Crits['site_n_lines']='0'
        Crits['site_k']='0'
        Crits['site_alpha95']='180'
    return [Crits]

def grade(PmagRec,accept,type): 
    """
    Finds the 'grade' (pass/fail; A/F) of a record (specimen,sample,site) given the acceptance criteria
    """
    GREATERTHAN=['specimen_q','site_k','site_n','site_n_lines','site_int_n','measurement_step_min','measurement_step_max','specimen_int_ptrm_n','specimen_fvds','specimen_frac','specimen_f','specimen_n','specimen_int_n','sample_int_n'] # these statistics must be exceede to pass, all others must be less than (except specimen_scat, which must be true)
    ISTRUE=['specimen_scat']
    kill=[] # criteria that kill the record
    for key in PmagRec.keys():
        if PmagRec[key]!="":
            if key in accept.keys() and type in key and accept[key]!="": # check if this is one of the acceptance criteria
                if key in ISTRUE: # boolean must be true
                    if PmagRec[key]!=True:
                        kill.append(key)
                if key in GREATERTHAN:
                    if eval(PmagRec[key])<eval(accept[key]):
                        kill.append(key)
                else:
                    if eval(PmagRec[key])>eval(accept[key]):
                        kill.append(key)
    return kill
    
#
def flip(D):
    """
     flip reverse mode
    """
    ppars=doprinc(D) # get principle direction
    D1,D2=[],[]
    for rec in D:
        ang=angle([rec[0],rec[1]],[ppars['dec'],ppars['inc']])
        if ang>90.:
            d,i=(rec[0]-180.)%360.,-rec[1]
            D2.append([d,i,1.])
        else:
            D1.append([rec[0],rec[1],1.])
    return D1,D2
#
def dia_vgp(*args): # new function interface by J.Holmes, SIO, 6/1/2011
    """
    converts declination, inclination, alpha95 to VGP, dp, dm
    """
    # test whether arguments are one 2-D list or 5 floats 
    if len(args) == 1: # args comes in as a tuple of multi-dim lists.
        largs=list(args).pop() # scrap the tuple.
        (decs, dips, a95s, slats, slongs) = zip(*largs) # reorganize the lists so that we get columns of data in each var.       
    else:
        # When args > 1, we are receiving five floats. This usually happens when the invoking script is 
        # executed in interactive mode.
        (decs, dips, a95s, slats, slongs) = (args)
       
    # We send all incoming data to numpy in an array form. Even if it means a 1x1 matrix. That's OKAY. Really.
    (dec, dip, a95, slat, slong) = (numpy.array(decs), numpy.array(dips), numpy.array(a95s), \
                                    numpy.array(slats), numpy.array(slongs)) # package columns into arrays
    rad=numpy.pi/180. # convert to radians
    dec,dip,a95,slat,slong=dec*rad,dip*rad,a95*rad,slat*rad,slong*rad
    p=numpy.arctan2(2.0,numpy.tan(dip))
    plat=numpy.arcsin(numpy.sin(slat)*numpy.cos(p)+numpy.cos(slat)*numpy.sin(p)*numpy.cos(dec))
    beta=(numpy.sin(p)*numpy.sin(dec))/numpy.cos(plat)
    
    #------------------------------------------------------------------------------------------------------------
    # The deal with "boolmask":
    # We needed a quick way to assign matrix values based on a logic decision, in this case setting boundaries
    # on out-of-bounds conditions. Creating a matrix of boolean values the size of the original matrix and using 
    # it to "mask" the assignment solves this problem nicely. The downside to this is that Numpy complains if you 
    # attempt to mask a non-matrix, so we have to check for array type and do a normal assignment if the type is 
    # scalar. These checks are made before calculating for the rest of the function.
    #------------------------------------------------------------------------------------------------------------

    boolmask = beta > 1. # create a mask of boolean values
    if isinstance(beta,numpy.ndarray):
        beta[boolmask] = 1. # assigns 1 only to elements that mask TRUE.
    else: # Numpy gets upset if you try our masking trick with a scalar or a 0-D matrix.
        if boolmask:
            beta = 1.
    boolmask = beta < -1.
    if isinstance(beta,numpy.ndarray):
        beta[boolmask] = -1. # assigns -1 only to elements that mask TRUE.
    else:
        if boolmask:
            beta = -1.

    beta=numpy.arcsin(beta)
    plong = slong+numpy.pi-beta
    if (numpy.cos(p) > numpy.sin(slat)*numpy.sin(plat)).any():
        boolmask = (numpy.cos(p) > (numpy.sin(slat)*numpy.sin(plat)))
        if isinstance(plong,numpy.ndarray):
            plong[boolmask] = (slong+beta)[boolmask]
        else:
            if boolmask:
                plong = slong+beta
        
    boolmask = (plong < 0)
    if isinstance(plong,numpy.ndarray):
        plong[boolmask] = plong[boolmask]+2*numpy.pi
    else:
        if boolmask:
            plong = plong+2*numpy.pi

    boolmask = (plong > 2*numpy.pi)
    if isinstance(plong,numpy.ndarray):
        plong[boolmask] = plong[boolmask]-2*numpy.pi
    else:
        if boolmask:
            plong = plong-2*numpy.pi

    dm=a95* (numpy.cos(slat)/numpy.cos(dip))/rad
    dp=a95*(1+3*(numpy.sin(slat)**2))/(2*rad)
    plat,plong=plat/rad,plong/rad
    return plong.tolist(),plat.tolist(),dp.tolist(),dm.tolist()

def int_pars(x,y,vds):
    """
     calculates York regression and Coe parameters (with Tauxe Fvds)
    """
# first do linear regression a la York
    xx,yer,xer,xyer,yy,xsum,ysum,xy=0.,0.,0.,0.,0.,0.,0.,0.
    xprime,yprime=[],[]
    pars={}
    pars["specimen_int_n"]=len(x)
    n=float(len(x))
    if n<=2:
        print "shouldn't be here at all!"
        return pars,1
    for i in range(len(x)):
        xx+=x[i]**2.
        yy+=y[i]**2.
        xy+=x[i]*y[i]
        xsum+=x[i]
        ysum+=y[i]
    xsig=numpy.sqrt((xx-(xsum**2./n))/(n-1.))
    ysig=numpy.sqrt((yy-(ysum**2./n))/(n-1.))
    sum=0
    for i in range(int(n)):
        yer+= (y[i]-ysum/n)**2.
        xer+= (x[i]-xsum/n)**2.
        xyer+= (y[i]-ysum/n)*(x[i]-xsum/n)
    slop=-numpy.sqrt(yer/xer)
    pars["specimen_b"]=slop
    s1=2.*yer-2.*slop*xyer
    s2=(n-2.)*xer
    sigma=numpy.sqrt(s1/s2)
    pars["specimen_b_sigma"]=sigma
    s=(xy-(xsum*ysum/n))/(xx-(xsum**2.)/n)
    r=(s*xsig)/ysig
    pars["specimen_rsc"]=r**2.
    ytot=abs(ysum/n-slop*xsum/n)
    for i in range(int(n)):
        xprime.append((slop*x[i]+y[i]-ytot)/(2.*slop))
        yprime.append(((slop*x[i]+y[i]-ytot)/2.)+ytot)
    sumdy,dy=0,[]
    dyt = abs(yprime[0]-yprime[int(n)-1])
    for i in range((int(n)-1)):
        dy.append(abs(yprime[i+1]-yprime[i]))
        sumdy+= dy[i]**2.
    f=dyt/ytot
    pars["specimen_f"]=f
    pars["specimen_ytot"]=ytot
    ff=dyt/vds
    pars["specimen_fvds"]=ff
    ddy=(1./dyt)*sumdy
    g=1.-ddy/dyt
    pars["specimen_g"]=g
    q=abs(slop)*f*g/sigma
    pars["specimen_q"]=q
    pars["specimen_b_beta"]=-sigma/slop
    return pars,0

def dovds(data):
    """
     calculates vector difference sum for demagnetization data
    """
    vds,X=0,[]
    for rec in data:
        X.append(dir2cart(rec))
    for k  in range(len(X)-1):
        xdif=X[k+1][0]-X[k][0]
        ydif=X[k+1][1]-X[k][1]
        zdif=X[k+1][2]-X[k][2]
        vds+=numpy.sqrt(xdif**2+ydif**2+zdif**2)
    vds+=numpy.sqrt(X[-1][0]**2+X[-1][1]**2+X[-1][2]**2)
    return vds
def vspec_magic(data):
    """
   takes average vector of replicate measurements
    """
    vdata,Dirdata,step_meth=[],[],""
    if len(data)==0:return vdata
    treat_init=["treatment_temp", "treatment_temp_decay_rate", "treatment_temp_dc_on", "treatment_temp_dc_off", "treatment_ac_field", "treatment_ac_field_decay_rate", "treatment_ac_field_dc_on", "treatment_ac_field_dc_off", "treatment_dc_field", "treatment_dc_field_decay_rate", "treatment_dc_field_ac_on", "treatment_dc_field_ac_off", "treatment_dc_field_phi", "treatment_dc_field_theta"]
    treats=[]
#
# find keys that are used
#
    for key in treat_init:
        if key in data[0].keys():treats.append(key)  # get a list of keys
    stop={}
    stop["er_specimen_name"]="stop"
    for key in treats:
        stop[key]="" # tells program when to quit and go home
    data.append(stop)
#
# set initial states
#
    DataState0,newstate={},0
    for key in treats:
        DataState0[key]=data[0][key] # set beginning treatment
    k,R=1,0
    for i in range(k,len(data)):
        Dirdata,DataStateCurr,newstate=[],{},0
        for key in treats:  # check if anything changed
	    DataStateCurr[key]=data[i][key] 
            if DataStateCurr[key].strip() !=  DataState0[key].strip(): newstate=1 # something changed
        if newstate==1:
            if i==k: # sample is unique 
                vdata.append(data[i-1])
            else: # measurement is not unique
                print "averaging: records " ,k,i
                for l in range(k-1,i):
                    Dirdata.append([float(data[l]['measurement_dec']),float(data[l]['measurement_inc']),float(data[l]['measurement_magn_moment'])])
                dir,R=vector_mean(Dirdata)
                Fpars=fisher_mean(Dirdata)
                vrec=data[i-1]
                vrec['measurement_dec']='%7.1f'%(dir[0])
                vrec['measurement_inc']='%7.1f'%(dir[1])
                vrec['measurement_magn_moment']='%8.3e'%(R/(i-k+1))
                vrec['measurement_csd']='%7.1f'%(Fpars['csd'])
                vrec['measurement_positions']='%7.1f'%(Fpars['n'])
                vrec['measurement_description']='average of multiple measurements'
                if "magic_method_codes" in vrec.keys():
                    meths=vrec["magic_method_codes"].strip().split(":")
                    if "DE-VM" not in meths:meths.append("DE-VM")
                    methods=""
                    for meth in meths:
                        methods=methods+meth+":"
                    vrec["magic_method_codes"]=methods[:-1]
                else: vrec["magic_method_codes"]="DE-VM"
                vdata.append(vrec)
# reset state to new one
            for key in treats:
                DataState0[key]=data[i][key] # set beginning treatment
            k=i+1
            if data[i]["er_specimen_name"] =="stop":
                del data[-1]  # get rid of dummy stop sign
                return vdata,treats # bye-bye

#
def get_specs(data):
    """
     takes a magic format file and returns a list of unique specimen names
    """
# sort the specimen names
#
    speclist=[]
    for rec in data:
      spec=rec["er_specimen_name"]
      if spec not in speclist:speclist.append(spec)
    speclist.sort()
    return speclist


def vector_mean(data):
    """
    calculates the vector mean of a given set of vectors
    """
    R,Xbar,X=0,[0,0,0],[]
    for rec in data:
        X.append(dir2cart(rec))
    for i in range(len(X)):
        for c in range(3):
           Xbar[c]+=X[i][c]
    for c in range(3):
        R+=Xbar[c]**2
    R=numpy.sqrt(R)
    for c in range(3):
        Xbar[c]=Xbar[c]/R    
    dir=cart2dir(Xbar)
    return dir, R 
def mark_dmag_rec(s,ind,data):
    """
    edits demagnetization data to mark "bad" points with measurement_flag
    """
    datablock=[]
    for rec in  data:
        if rec['er_specimen_name']==s:
            meths=rec['magic_method_codes'].split(':')
            if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
                datablock.append(rec)
    dmagrec=datablock[ind]
    for k in  range(len(data)):
        meths=data[k]['magic_method_codes'].split(':')
        if 'LT-NO' in meths or 'LT-AF-Z' in meths or 'LT-T-Z' in meths:
            if data[k]['er_specimen_name']==s:
                if data[k]['treatment_temp']==dmagrec['treatment_temp'] and data[k]['treatment_ac_field']==dmagrec['treatment_ac_field']:
                    if data[k]['measurement_dec']==dmagrec['measurement_dec'] and data[k]['measurement_inc']==dmagrec['measurement_inc'] and data[k]['measurement_magn_moment']==dmagrec['measurement_magn_moment']:
                        if data[k]['measurement_flag']=='g':
                            flag='b'
                        else:
                            flag='g'
                        data[k]['measurement_flag']=flag
                        break
    return data


def mark_samp(Samps,data,crd):




    return Samps

def find_dmag_rec(s,data):
    """
    returns demagnetization data for specimen s from the data - excludes other kinds of experiments and "bad" measurements
    """
    EX=["LP-AN-ARM","LP-AN-TRM","LP-ARM-AFD","LP-ARM2-AFD","LP-TRM-AFD","LP-TRM","LP-TRM-TD","LP-X"] # list of excluded lab protocols
    INC=["LT-NO","LT-AF-Z","LT-T-Z", "LT-M-Z", "LP-PI-TRM-IZ", "LP-PI-M-IZ"]
    datablock,tr=[],""
    therm_flag,af_flag,mw_flag=0,0,0
    units=[]
    spec_meas=get_dictitem(data,'er_specimen_name',s,'T')
    for rec in spec_meas:
           if 'measurement_flag' not in rec.keys():rec['measurement_flag']='g'
           skip=1
           tr=""
           methods=rec["magic_method_codes"].split(":")
           for meth in methods:
               if meth.strip() in INC:
                   skip=0
           for meth in EX:
               if meth in methods:skip=1
           if skip==0:
               if "LT-NO" in methods: 
                   tr = float(rec["treatment_temp"])
               if "LT-AF-Z" in methods: 
                   af_flag=1
                   tr = float(rec["treatment_ac_field"])
                   if "T" not in units:units.append("T")
               if "LT-T-Z" in methods: 
                   therm_flag=1
                   tr = float(rec["treatment_temp"])
                   if "K" not in units:units.append("K")
               if "LT-M-Z" in methods: 
                   mw_flag=1
                   tr = float(rec["treatment_mw_power"])*float(rec["treatment_mw_time"])
                   if "J" not in units:units.append("J")
               if "LP-PI-TRM-IZ" in methods or "LP-PI-M-IZ" in methods:  # looking for in-field first thellier or microwave data - otherwise, just ignore this
                   ZI=0
               else:
                   ZI=1
               Mkeys=['measurement_magnitude','measurement_magn_moment','measurement_magn_volume','measurement_magn_mass']
               if tr !="":
                   dec,inc,int = "","",""
                   if "measurement_dec" in rec.keys() and rec["measurement_dec"] != "":
                       dec=float(rec["measurement_dec"])
                   if "measurement_inc" in rec.keys() and rec["measurement_inc"] != "":
                       inc=float(rec["measurement_inc"])
                   for key in Mkeys:
                       if key in rec.keys() and rec[key]!="":int=float(rec[key])
                   if 'magic_instrument_codes' not in rec.keys():rec['magic_instrument_codes']=''
                   datablock.append([tr,dec,inc,int,ZI,rec['measurement_flag'],rec['magic_instrument_codes']])
    if therm_flag==1:
        for k in range(len(datablock)):
            if datablock[k][0]==0.: datablock[k][0]=273.
    if af_flag==1:
        for k in range(len(datablock)):
            if datablock[k][0]>=273 and datablock[k][0]<=323: datablock[k][0]=0.
    meas_units=""
    if len(units)>0:
        for u in units:meas_units=meas_units+u+":"
        meas_units=meas_units[:-1]
    return datablock,meas_units
 

def magic_read(infile):
    """ 
    reads  a Magic template file, puts data in a list of dictionaries
    """
    hold,magic_data,magic_record,magic_keys=[],[],{},[]
    try:
        f=open(infile,"rU")
    except:
        return [],'bad_file'
    d = f.readline()[:-1].strip('\n')
    if d[0]=="s" or d[1]=="s":
        delim='space'
    elif d[0]=="t" or d[1]=="t":
        delim='tab'
    else: 
        print 'error reading ', infile
        sys.exit()
    if delim=='space':file_type=d.split()[1]
    if delim=='tab':file_type=d.split('\t')[1]
    if file_type=='delimited':
        if delim=='space':file_type=d.split()[2]
        if delim=='tab':file_type=d.split('\t')[2]
    if delim=='space':line =f.readline()[:-1].split()
    if delim=='tab':line =f.readline()[:-1].split('\t')
    for key in line:
        magic_keys.append(key)
    lines=f.readlines()
    for line in lines[:-1]:
        line.replace('\n','')
        if delim=='space':rec=line[:-1].split()
        if delim=='tab':rec=line[:-1].split('\t')
        hold.append(rec)
    line = lines[-1].replace('\n','')
    if delim=='space':rec=line[:-1].split()
    if delim=='tab':rec=line.split('\t')
    hold.append(rec)
    for rec in hold:
        magic_record={}
        if len(magic_keys) != len(rec):
            print "Warning: Uneven record lengths detected: ",rec
        for k in range(len(rec)):
           magic_record[magic_keys[k]]=rec[k].strip('\n')
        magic_data.append(magic_record)
    magictype=file_type.lower().split("_")
    Types=['er','magic','pmag','rmag']
    if magictype in Types:file_type=file_type.lower()
    return magic_data,file_type
#
def upload_read(infile,table):
    """
    reads  a table from a MagIC upload (or downloaded) txt file, 
     puts data in a list of dictionaries
    """
    delim='tab'
    hold,magic_data,magic_record,magic_keys=[],[],{},[]
    f=open(infile,"rU")
#
# look for right table
#
    line =f.readline()[:-1]
    file_type=line.split('\t')[1]
    if file_type=='delimited': file_type=line.split('\t')[2]
    if delim=='tab':
        line =f.readline()[:-1].split('\t')
    else:
        print "only tab delimitted files are supported now"
        sys.exit()
    while file_type!=table:
        while line[0][0:5] in f.readlines() !=">>>>>":
            pass
        line =f.readline()[:-1]
        file_type=line.split('\t')[1]
        if file_type=='delimited': file_type=line.split('\t')[2]
        ine =f.readline()[:-1].split('\t')
    while line[0][0:5] in f.readlines() !=">>>>>":
        for key in line:
            magic_keys.append(key)
        for line in f.readlines():
            rec=line[:-1].split('\t')
            hold.append(rec)
        for rec in hold:
            magic_record={}
            if len(magic_keys) != len(rec):
                print "Uneven record lengths detected: ",rec
                raw_input("Return to continue.... ")
            for k in range(len(magic_keys)):
                magic_record[magic_keys[k]]=rec[k]
            magic_data.append(magic_record)
    return magic_data
#
#
def putout(ofile,keylist,Rec):
    """
    writes out a magic format record to ofile
    """
    pmag_out=open(ofile,'a')
    outstring=""
    for key in keylist:
        try:
           outstring=outstring+'\t'+Rec[key].strip()
        except:
           print key,Rec[key]
           raw_input()
    outstring=outstring+'\n'
    pmag_out.write(outstring[1:])
    pmag_out.close()

def first_rec(ofile,Rec,file_type): 
    """
    opens the file ofile as a magic template file with headers as the keys to Rec
    """
    keylist=[]
    pmag_out=open(ofile,'w')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    for key in Rec.keys():
        keystring=keystring+'\t'+key.strip()
        keylist.append(key)
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist

def magic_write(ofile,Recs,file_type):
    """
    writes out a magic format list of dictionaries to ofile
    """
    pmag_out=open(ofile,'w')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    keylist=[]
    for key in Recs[0].keys():
        keylist.append(key)
    keylist.sort()
    for key in keylist:
        keystring=keystring+'\t'+key.strip()
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    for Rec in Recs:
        outstring=""
        for key in keylist:
           try:
              outstring=outstring+'\t'+str(Rec[key].strip())
           except:
              if 'er_specimen_name' in Rec.keys():
                  print Rec['er_specimen_name'] 
              elif 'er_specimen_names' in Rec.keys():
                  print Rec['er_specimen_names'] 
              print key,Rec[key]
              raw_input()
        outstring=outstring+'\n'
        pmag_out.write(outstring[1:])
    pmag_out.close()


def dotilt(dec,inc,bed_az,bed_dip):
    """
    does a tilt correction on dec,inc using bedding dip direction bed_az and dip bed_dip
    """
    rad=numpy.pi/180. # converts from degrees to radians
    X=dir2cart([dec,inc,1.]) # get cartesian coordinates of dec,inc
# get some sines and cosines of new coordinate system
    sa,ca= -numpy.sin(bed_az*rad),numpy.cos(bed_az*rad) 
    cdp,sdp= numpy.cos(bed_dip*rad),numpy.sin(bed_dip*rad) 
# do the rotation
    xc=X[0]*(sa*sa+ca*ca*cdp)+X[1]*(ca*sa*(1.-cdp))+X[2]*sdp*ca
    yc=X[0]*ca*sa*(1.-cdp)+X[1]*(ca*ca+sa*sa*cdp)-X[2]*sa*sdp
    zc=X[0]*ca*sdp-X[1]*sdp*sa-X[2]*cdp
# convert back to direction:
    Dir=cart2dir([xc,yc,-zc])
    return Dir[0],Dir[1] # return declination, inclination of rotated direction


def dotilt_V(input):
    """
    does a tilt correction on dec,inc using bedding dip direction bed_az and dip bed_dip
    """
    input=input.transpose() 
    dec, inc, bed_az, bed_dip =input[0],input[1],input[2],input[3]  # unpack input array into separate arrays
    rad=numpy.pi/180. # convert to radians
    Dir=numpy.array([dec,inc]).transpose()
    X=dir2cart(Dir).transpose() # get cartesian coordinates
    N=numpy.size(dec)

# get some sines and cosines of new coordinate system
    sa,ca= -numpy.sin(bed_az*rad),numpy.cos(bed_az*rad) 
    cdp,sdp= numpy.cos(bed_dip*rad),numpy.sin(bed_dip*rad) 
# do the rotation
    xc=X[0]*(sa*sa+ca*ca*cdp)+X[1]*(ca*sa*(1.-cdp))+X[2]*sdp*ca
    yc=X[0]*ca*sa*(1.-cdp)+X[1]*(ca*ca+sa*sa*cdp)-X[2]*sa*sdp
    zc=X[0]*ca*sdp-X[1]*sdp*sa-X[2]*cdp
# convert back to direction:
    cart=numpy.array([xc,yc,-zc]).transpose()
    Dir=cart2dir(cart).transpose()
    return Dir[0],Dir[1] # return declination, inclination arrays of rotated direction


def dogeo(dec,inc,az,pl):
    """
    rotates dec,in into geographic coordinates using az,pl as azimuth and plunge of X direction
    """
    A1,A2,A3=[],[],[] # set up lists for rotation vector
    Dir=[dec,inc,1.] # put dec inc in direction list and set  length to unity
    X=dir2cart(Dir) # get cartesian coordinates
#
#   set up rotation matrix
#
    A1=dir2cart([az,pl,1.])
    A2=dir2cart([az+90.,0,1.])
    A3=dir2cart([az-180.,90.-pl,1.])
#
# do rotation
#
    xp=A1[0]*X[0]+A2[0]*X[1]+A3[0]*X[2]
    yp=A1[1]*X[0]+A2[1]*X[1]+A3[1]*X[2]
    zp=A1[2]*X[0]+A2[2]*X[1]+A3[2]*X[2]
#
# transform back to dec,inc
#
    Dir_geo=cart2dir([xp,yp,zp])
    return Dir_geo[0],Dir_geo[1]    # send back declination and inclination
def dogeo_V(input):
    """
    rotates dec,in into geographic coordinates using az,pl as azimuth and plunge of X direction
    handles  array for  input 
    """
    input=input.transpose() 
    dec, inc, az, pl =input[0],input[1],input[2],input[3]  # unpack input array into separate arrays
    Dir=numpy.array([dec,inc]).transpose()
    X=dir2cart(Dir).transpose() # get cartesian coordinates
    N=numpy.size(dec)
    A1=dir2cart(numpy.array([az,pl,numpy.ones(N)]).transpose()).transpose()
    A2=dir2cart(numpy.array([az+90.,numpy.zeros(N),numpy.ones(N)]).transpose()).transpose()
    A3=dir2cart(numpy.array([az-180.,90.-pl,numpy.ones(N)]).transpose()).transpose()

# do rotation
#
    xp=A1[0]*X[0]+A2[0]*X[1]+A3[0]*X[2]
    yp=A1[1]*X[0]+A2[1]*X[1]+A3[1]*X[2]
    zp=A1[2]*X[0]+A2[2]*X[1]+A3[2]*X[2]
    cart=numpy.array([xp,yp,zp]).transpose()
#
# transform back to dec,inc
#
    Dir_geo=cart2dir(cart).transpose()
    return Dir_geo[0],Dir_geo[1]    # send back declination and inclination arrays

def dodirot(D,I,Dbar,Ibar):
    d,irot=dogeo(D,I,Dbar,90.-Ibar)
    drot=d-180.
#    drot,irot=dogeo(D,I,Dbar,Ibar)
    if drot<360.:drot=drot+360.
    if drot>360.:drot=drot-360.
    return drot,irot

def find_samp_rec(s,data,az_type):
    """
    find the orientation info for samp s
    """
    datablock,or_error,bed_error=[],0,0
    orient={}
    orient["sample_dip"]=""
    orient["sample_azimuth"]=""
    orient['sample_description']=""
    for rec in data:
        if rec["er_sample_name"].lower()==s.lower():
           if 'sample_orientation_flag' in  rec.keys() and rec['sample_orientation_flag']=='b': 
               orient['sample_orientation_flag']='b'
               return orient
           if "magic_method_codes" in rec.keys() and az_type != "0":
               methods=rec["magic_method_codes"].replace(" ","").split(":")
               if az_type in methods and "sample_azimuth" in rec.keys() and rec["sample_azimuth"]!="": orient["sample_azimuth"]= float(rec["sample_azimuth"])
               if "sample_dip" in rec.keys() and rec["sample_dip"]!="": orient["sample_dip"]=float(rec["sample_dip"])
               if "sample_bed_dip_direction" in rec.keys() and rec["sample_bed_dip_direction"]!="":orient["sample_bed_dip_direction"]=float(rec["sample_bed_dip_direction"])
               if "sample_bed_dip" in rec.keys() and rec["sample_bed_dip"]!="":orient["sample_bed_dip"]=float(rec["sample_bed_dip"])
           else: 
               if "sample_azimuth" in rec.keys():orient["sample_azimuth"]=float(rec["sample_azimuth"])
               if "sample_dip" in rec.keys(): orient["sample_dip"]=float(rec["sample_dip"])
               if "sample_bed_dip_direction" in rec.keys(): orient["sample_bed_dip_direction"]=float(rec["sample_bed_dip_direction"])
               if "sample_bed_dip" in rec.keys(): orient["sample_bed_dip"]=float(rec["sample_bed_dip"])
               if 'sample_description' in rec.keys(): orient['sample_description']=rec['sample_description']
        if orient["sample_azimuth"]!="": break
    return orient

def vspec(data):
    """
    takes the vector mean of replicate measurements at a give step
    """
    vdata,Dirdata,step_meth=[],[],[]
    tr0=data[0][0] # set beginning treatment
    data.append("Stop")
    k,R=1,0
    for i in range(k,len(data)):
        Dirdata=[]
        if data[i][0] != tr0: 
            if i==k: # sample is unique
                vdata.append(data[i-1])
                step_meth.append(" ")
            else: # sample is not unique
                for l in range(k-1,i):
                    Dirdata.append([data[l][1],data[l][2],data[l][3]])
                dir,R=vector_mean(Dirdata)
                vdata.append([data[i-1][0],dir[0],dir[1],R/(i-k+1),'1','g'])
                step_meth.append("DE-VM")
            tr0=data[i][0]
            k=i+1
            if tr0=="stop":break
    del data[-1]
    return step_meth,vdata

def Vdiff(D1,D2):
    """
    finds the vector difference between two directions D1,D2
    """
    A=dir2cart([D1[0],D1[1],1.])
    B=dir2cart([D2[0],D2[1],1.])
    C=[]
    for i in range(3):
        C.append(A[i]-B[i])
    return cart2dir(C)

def angle(D1,D2):
    """
    finds the angle between lists of two directions D1,D2
    """
    D1=numpy.array(D1)
    if len(D1.shape)>1:
        D1=D1[:,0:2] # strip off intensity
    else: D1=D1[:2]
    D2=numpy.array(D2)
    if len(D2.shape)>1:
        D2=D2[:,0:2] # strip off intensity
    else: D2=D2[:2]
    X1=dir2cart(D1) # convert to cartesian from polar
    X2=dir2cart(D2)
    angles=[] # set up a list for angles
    for k in range(X1.shape[0]): # single vector
        angle= numpy.arccos(numpy.dot(X1[k],X2[k]))*180./numpy.pi # take the dot product
        angle=angle%360.
        angles.append(angle)
    return numpy.array(angles)

def cart2dir(cart):
    """
    converts a direction to cartesian coordinates
    """
    cart=numpy.array(cart)
    rad=numpy.pi/180. # constant to convert degrees to radians
    if len(cart.shape)>1:
        Xs,Ys,Zs=cart[:,0],cart[:,1],cart[:,2]
    else: #single vector
        Xs,Ys,Zs=cart[0],cart[1],cart[2]
    Rs=numpy.sqrt(Xs**2+Ys**2+Zs**2) # calculate resultant vector length
    Decs=(numpy.arctan2(Ys,Xs)/rad)%360. # calculate declination taking care of correct quadrants (arctan2) and making modulo 360.
    try:
        Incs=numpy.arcsin(Zs/Rs)/rad # calculate inclination (converting to degrees) # 
    except:
        print 'trouble in cart2dir' # most likely division by zero somewhere
        return numpy.zeros(3)
        
    return numpy.array([Decs,Incs,Rs]).transpose() # return the directions list

#def cart2dir(cart): # OLD ONE
#    """
#    converts a direction to cartesian coordinates
#    """
#    Dir=[] # establish a list to put directions in
#    rad=numpy.pi/180. # constant to convert degrees to radians
#    R=numpy.sqrt(cart[0]**2+cart[1]**2+cart[2]**2) # calculate resultant vector length
#    if R==0:
#       print 'trouble in cart2dir'
#       print cart
#       return [0.0,0.0,0.0]
#    D=numpy.arctan2(cart[1],cart[0])/rad  # calculate declination taking care of correct quadrants (arctan2)
#    if D<0:D=D+360. # put declination between 0 and 360.
#    if D>360.:D=D-360.
#    Dir.append(D)  # append declination to Dir list
#    I=numpy.arcsin(cart[2]/R)/rad # calculate inclination (converting to degrees)
#    Dir.append(I) # append inclination to Dir list
#    Dir.append(R) # append vector length to Dir list
#    return Dir # return the directions list
#
def tauV(T):
    """
    gets the eigenvalues (tau) and eigenvectors (V) from matrix T
    """
    t,V,tr=[],[],0.
    ind1,ind2,ind3=0,1,2
    evalues,evectmps=numpy.linalg.eig(T)
    evectors=numpy.transpose(evectmps)  # to make compatible with Numeric convention
    for tau in evalues:
        tr+=tau
    if tr!=0:
        for i in range(3):
            evalues[i]=evalues[i]/tr
    else:
        return t,V
# sort evalues,evectors
    t1,t2,t3=0.,0.,1.
    for k in range(3):
        if evalues[k] > t1: 
            t1,ind1=evalues[k],k 
        if evalues[k] < t3: 
            t3,ind3=evalues[k],k 
    for k in range(3):
        if evalues[k] != t1 and evalues[k] != t3: 
            t2,ind2=evalues[k],k
    V.append(evectors[ind1])
    V.append(evectors[ind2])
    V.append(evectors[ind3])
    t.append(t1)
    t.append(t2)
    t.append(t3)
    return t,V

def Tmatrix(X):
    """
    gets the orientation matrix (T) from data in X
    """
    T=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    for row in X:
        for k in range(3):
            for l in range(3):
                T[k][l] += row[k]*row[l]
    return T


def dir2cart(d):
   # converts list or array of vector directions, in degrees, to array of cartesian coordinates, in x,y,z
    ints=numpy.ones(len(d)).transpose() # get an array of ones to plug into dec,inc pairs
    d=numpy.array(d)
    rad=numpy.pi/180.
    if len(d.shape)>1: # array of vectors
        decs,incs=d[:,0]*rad,d[:,1]*rad
        if d.shape[1]==3: ints=d[:,2] # take the given lengths
    else: # single vector
        decs,incs=numpy.array(d[0])*rad,numpy.array(d[1])*rad
        if len(d)==3: 
            ints=numpy.array(d[2])
        else:
            ints=numpy.array([1.])
    cart= numpy.array([ints*numpy.cos(decs)*numpy.cos(incs),ints*numpy.sin(decs)*numpy.cos(incs),ints*numpy.sin(incs)]).transpose()
    return cart


def findrec(s,data):
    """
    finds all the records belonging to s in data
    """
    datablock=[]
    for rec in data:
       if s==rec[0]:
           datablock.append([rec[1],rec[2],rec[3],rec[4]])
    return datablock

def domean(indata,start,end,calculation_type):
    """
     gets average direction using fisher or pca (line or plane) methods
    """
    mpars={}
    datablock=[]
    ind=0
    for rec in indata:
        if len(rec)<6:rec.append('g')
        if rec[5]=='b' and ind==start: 
            mpars["specimen_direction_type"]="Error"
            print "Can't select 'bad' point as start for PCA"
            return mpars 
        if rec[5]=='b' and ind<start: 
            start-=1
        if rec[5]=='g':
            datablock.append(rec) # use only good data
        else:
            end-=1
        ind+=1
    mpars["calculation_type"]=calculation_type
    rad=numpy.pi/180.
    if end>len(datablock)-1 or end<start : end=len(datablock)-1
    control,data,X,Nrec=[],[],[],float(end-start+1)
    cm=[0.,0.,0.]
#
#  get cartesian coordinates
#
    fdata=[]
    for k in range(start,end+1):
        if calculation_type == 'DE-BFL' or calculation_type=='DE-BFL-A' or calculation_type=='DE-BFL-O' :  # best-fit line
            data=[datablock[k][1],datablock[k][2],datablock[k][3]]
        else: 
            data=[datablock[k][1],datablock[k][2],1.0] # unit weight
        fdata.append(data)
        cart= dir2cart(data)
        X.append(cart)
    if calculation_type=='DE-BFL-O': # include origin as point
#        X.append([0.,0.,0.])
        pass
    if calculation_type=='DE-FM': # for fisher means
        fpars=fisher_mean(fdata)    
        mpars["specimen_direction_type"]='l'
        mpars["specimen_dec"]=fpars["dec"]
        mpars["specimen_inc"]=fpars["inc"]
        mpars["specimen_alpha95"]=fpars["alpha95"]
        mpars["specimen_n"]=fpars["n"]
        mpars["specimen_r"]=fpars["r"]
        mpars["measurement_step_min"]=datablock[start][0]
        mpars["measurement_step_max"]=datablock[end][0]
        mpars["center_of_mass"]=cm
        mpars["specimen_dang"]=-1
        return mpars
#
#	get center of mass for principal components (DE-BFL or DE-BFP)
#
    for cart in X:
        for l in range(3):
            cm[l]+=cart[l]/Nrec
    mpars["center_of_mass"]=cm

#
#   transform to center of mass (if best-fit line)
#
    if calculation_type!='DE-BFP': mpars["specimen_direction_type"]='l'
    if calculation_type=='DE-BFL' or calculation_type=='DE-BFL-O': # not for planes or anchored lines
        for k in range(len(X)):
            for l in range(3):
               X[k][l]=X[k][l]-cm[l]
    else:
        mpars["specimen_direction_type"]='p'
#
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t,V=tauV(T)
    if t[2]<0:t[2]=0 # make positive
    if t==[]:
        mpars["specimen_direction_type"]="Error"
        print "Error in calculation"
        return mpars 
    v1,v3=V[0],V[2]
    if calculation_type=='DE-BFL-A':
        Dir,R=vector_mean(fdata) 
        mpars["specimen_direction_type"]='l'
        mpars["specimen_dec"]=Dir[0]
        mpars["specimen_inc"]=Dir[1]
        mpars["specimen_n"]=len(fdata)
        mpars["measurement_step_min"]=datablock[start][0]
        mpars["measurement_step_max"]=datablock[end][0]
        mpars["center_of_mass"]=cm
        s1=numpy.sqrt(t[0])
        MAD=numpy.arctan(numpy.sqrt(t[1]+t[2])/s1)/rad
        mpars["specimen_mad"]=MAD # I think this is how it is done - i never anchor the "PCA" - check
        return mpars
    if calculation_type!='DE-BFP':
#
#   get control vector for principal component direction
#
        rec=[datablock[start][1],datablock[start][2],datablock[start][3]]
        P1=dir2cart(rec)
        rec=[datablock[end][1],datablock[end][2],datablock[end][3]]
        P2=dir2cart(rec)
#
#   get right direction along principal component
##
        for k in range(3):
            control.append(P1[k]-P2[k])
        dot = 0
        for k in range(3):
            dot += v1[k]*control[k]
        if dot<-1:dot=-1
        if dot>1:dot=1
        if numpy.arccos(dot) > numpy.pi/2.:
            for k in range(3):
                v1[k]=-v1[k]
#   get right direction along principal component
#
        s1=numpy.sqrt(t[0])
        Dir=cart2dir(v1)
        MAD=numpy.arctan(numpy.sqrt(t[1]+t[2])/s1)/rad
    if calculation_type=="DE-BFP":
        Dir=cart2dir(v3)
        MAD=numpy.arctan(numpy.sqrt(t[2]/t[1]+t[2]/t[0]))/rad
#
#  	get angle with  center of mass
#
    CMdir=cart2dir(cm)
    Dirp=[Dir[0],Dir[1],1.]
    dang=angle(CMdir,Dirp)
    mpars["specimen_dec"]=Dir[0]
    mpars["specimen_inc"]=Dir[1]
    mpars["specimen_mad"]=MAD
    mpars["specimen_n"]=int(Nrec)
    mpars["specimen_dang"]=dang[0]
    mpars["measurement_step_min"]=datablock[start][0]
    mpars["measurement_step_max"]=datablock[end][0]
    return mpars

def circ(dec,dip,alpha):
    """
    function to calculate points on an circle about dec,dip with angle alpha
    """
    rad=numpy.pi/180.
    D_out,I_out=[],[]
    dec,dip,alpha=dec*rad ,dip*rad,alpha*rad
    dec1=dec+numpy.pi/2.
    isign=1
    if dip!=0: isign=(abs(dip)/dip)
    dip1=(dip-isign*(numpy.pi/2.))
    t=[[0,0,0],[0,0,0],[0,0,0]]
    v=[0,0,0]
    t[0][2]=numpy.cos(dec)*numpy.cos(dip)
    t[1][2]=numpy.sin(dec)*numpy.cos(dip)
    t[2][2]=numpy.sin(dip)
    t[0][1]=numpy.cos(dec)*numpy.cos(dip1)
    t[1][1]=numpy.sin(dec)*numpy.cos(dip1)
    t[2][1]=numpy.sin(dip1)
    t[0][0]=numpy.cos(dec1)
    t[1][0]=numpy.sin(dec1)
    t[2][0]=0   
    for i in range(101): 
        psi=float(i)*numpy.pi/50. 
        v[0]=numpy.sin(alpha)*numpy.cos(psi) 
        v[1]=numpy.sin(alpha)*numpy.sin(psi) 
        v[2]=numpy.sqrt(abs(1.-v[0]**2 - v[1]**2))
        elli=[0,0,0]
        for j in range(3):
            for k in range(3):
                elli[j]=elli[j] + t[j][k]*v[k] 
        Dir=cart2dir(elli)
        D_out.append(Dir[0])
        I_out.append(Dir[1])
    return D_out,I_out


def PintPars(araiblock,zijdblock,start,end):
    """
     calculate the paleointensity magic parameters  make some definitions
    """
    methcode,ThetaChecks,DeltaChecks,GammaChecks="","","",""
    zptrm_check=[]
    first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks=araiblock[0],araiblock[1],araiblock[2],araiblock[3],araiblock[4],araiblock[5]  
    if len(araiblock)>6: 
        ThetaChecks=araiblock[6] # used only for perpendicular method of paleointensity
        DeltaChecks=araiblock[7] # used only for perpendicular  method of paleointensity
    xi,yi,diffcum=[],[],0
    xiz,xzi,yiz,yzi=[],[],[],[]
    Nptrm,dmax=0,-1e-22
# check if even zero and infield steps
    if len(first_Z)>len(first_I): 
        maxe=len(first_I)-1
    else: maxe=len(first_Z)-1
    if end==0 or end > maxe:
        end=maxe
# get the MAD, DANG, etc. for directional data
    bstep=araiblock[0][start][0]
    estep=araiblock[0][end][0]
    zstart,zend=0,len(zijdblock)
    for k in range(len(zijdblock)): 
        zrec=zijdblock[k]
        if zrec[0]==bstep:zstart=k
        if zrec[0]==estep:zend=k
    PCA=domean(zijdblock,zstart,zend,'DE-BFL')  
    D,Diz,Dzi,Du=[],[],[],[]  # list of NRM vectors, and separated by zi and iz
    for rec in zijdblock:
        D.append((rec[1],rec[2],rec[3])) 
        Du.append((rec[1],rec[2])) 
        if rec[4]==1:
            Dzi.append((rec[1],rec[2]))  # if this is ZI step
        else:
            Diz.append((rec[1],rec[2]))  # if this is IZ step
# calculate the vector difference sum
    vds=dovds(D)
    b_zi,b_iz=[],[]
# collect data included in ZigZag calculation
    if end+1>=len(first_Z):
        stop=end-1
    else:
        stop=end
    for k in range(start,end+1):
       for l in range(len(first_I)):
           irec=first_I[l]
           if irec[0]==first_Z[k][0]: 
               xi.append(irec[3])
               yi.append(first_Z[k][3])
    pars,errcode=int_pars(xi,yi,vds) 
    if errcode==1:return pars,errcode
#    for k in range(start,end+1):
    for k in range(len(first_Z)-1):
        for l in range(k):
            if first_Z[k][3]/vds>0.1:   # only go down to 10% of NRM.....
               irec=first_I[l]
               if irec[4]==1 and first_I[l+1][4]==0: # a ZI step
                   xzi=irec[3]
                   yzi=first_Z[k][3]
                   xiz=first_I[l+1][3]
                   yiz=first_Z[k+1][3]
                   slope=numpy.arctan2((yzi-yiz),(xiz-xzi))
                   r=numpy.sqrt( (yzi-yiz)**2+(xiz-xzi)**2)
                   if r>.1*vds:b_zi.append(slope) # suppress noise
               elif irec[4]==0 and first_I[l+1][4]==1: # an IZ step
                   xiz=irec[3]
                   yiz=first_Z[k][3]
                   xzi=first_I[l+1][3]
                   yzi=first_Z[k+1][3]
                   slope=numpy.arctan2((yiz-yzi),(xzi-xiz))
                   r=numpy.sqrt( (yiz-yzi)**2+(xzi-xiz)**2)
                   if r>.1*vds:b_iz.append(slope) # suppress noise
#
    ZigZag,Frat,Trat=-1,0,0
    if len(Diz)>2 and len(Dzi)>2:
        ZigZag=0
        dizp=fisher_mean(Diz) # get Fisher stats on IZ steps
        dzip=fisher_mean(Dzi) # get Fisher stats on ZI steps
        dup=fisher_mean(Du) # get Fisher stats on all steps
#
# if directions are TOO well grouped, can get false positive for ftest, so
# angles must be > 3 degrees apart.
#
        if angle([dizp['dec'],dizp['inc']],[dzip['dec'],dzip['inc']])>3.: 
            F=(dup['n']-2.)* (dzip['r']+dizp['r']-dup['r'])/(dup['n']-dzip['r']-dizp['r']) # Watson test for common mean
            nf=2.*(dup['n']-2.) # number of degees of freedom
            ftest=fcalc(2,nf)
            Frat=F/ftest
            if Frat>1.:
                ZigZag=Frat # fails zigzag on directions
                methcode="SM-FTEST"
# now do slopes 
    if len(b_zi)>2 and len(b_iz)>2:
        bzi_m,bzi_sig=gausspars(b_zi)  # mean, std dev
        biz_m,biz_sig=gausspars(b_iz) 
        n_zi=float(len(b_zi))
        n_iz=float(len(b_iz))
        b_diff=abs(bzi_m-biz_m) # difference in means
#
# avoid false positives - set 3 degree slope difference here too
        if b_diff>3*numpy.pi/180.:
            nf=n_zi+n_iz-2.  # degrees of freedom
            svar= ((n_zi-1.)*bzi_sig**2 + (n_iz-1.)*biz_sig**2)/nf
            T=(b_diff)/numpy.sqrt(svar*(1.0/n_zi + 1.0/n_iz)) # student's t
            ttest=tcalc(nf,.05) # t-test at 95% conf.
            Trat=T/ttest
            if Trat>1  and Trat>Frat:
                ZigZag=Trat # fails zigzag on directions
                methcode="SM-TTEST"
    pars["specimen_Z"]=ZigZag 
    pars["method_codes"]=methcode
# do drats
    if len(ptrm_check) != 0:
        diffcum,drat_max=0,0
        for prec in ptrm_check:
            step=prec[0]
            endbak=end
            zend=end
            while zend>len(zijdblock)-1:
               zend=zend-2  # don't count alteration that happens after this step
            if step <zijdblock[zend][0]:
                Nptrm+=1
                for irec in first_I:
                    if irec[0]==step:break
                diffcum+=prec[3]-irec[3]
                if abs(prec[3]-irec[3])>drat_max:drat_max=abs(prec[3]-irec[3])
        pars["specimen_drats"]=(100*abs(diffcum)/first_I[zend][3])
        pars["specimen_drat"]=(100*abs(drat_max)/first_I[zend][3])
    elif len(zptrm_check) != 0:
        diffcum=0
        for prec in zptrm_check:
            step=prec[0]
            endbak=end
            zend=end
            while zend>len(zijdblock)-1:
               zend=zend-1
            if step <zijdblock[zend][0]:
                Nptrm+=1
                for irec in first_I:
                    if irec[0]==step:break
                diffcum+=prec[3]-irec[3]
        pars["specimen_drats"]=(100*abs(diffcum)/first_I[zend][3])
    else: 
        pars["specimen_drats"]=-1
        pars["specimen_drat"]=-1
# and the pTRM tails
    if len(ptrm_tail) != 0:
        for trec in ptrm_tail:
            step=trec[0]
            for irec in first_I:
                if irec[0]==step:break
            if abs(trec[3]) >dmax:dmax=abs(trec[3])
        pars["specimen_md"]=(100*dmax/vds)
    else: pars["specimen_md"]=-1
    pars["measurement_step_min"]=bstep
    pars["measurement_step_max"]=estep
    pars["specimen_dec"]=PCA["specimen_dec"]
    pars["specimen_inc"]=PCA["specimen_inc"]
    pars["specimen_int_mad"]=PCA["specimen_mad"]
    pars["specimen_dang"]=PCA["specimen_dang"]
    #pars["specimen_int_ptrm_n"]=len(ptrm_check) # this is WRONG!
    pars["specimen_int_ptrm_n"]=Nptrm
# and the ThetaChecks
    if ThetaChecks!="":
        t=0
        for theta in ThetaChecks:
            if theta[0]>=bstep and theta[0]<=estep and theta[1]>t:t=theta[1]
        pars['specimen_theta']=t
    else:
        pars['specimen_theta']=-1
# and the DeltaChecks
    if DeltaChecks!="":
        d=0
        for delta in DeltaChecks:
            if delta[0]>=bstep and delta[0]<=estep and delta[1]>d:d=delta[1]
        pars['specimen_delta']=d
    else:
        pars['specimen_delta']=-1
    pars['specimen_gamma']=-1
    if GammaChecks!="":
        for gamma in GammaChecks:
            if gamma[0]<=estep: pars['specimen_gamma']=gamma[1]
    return pars,0

def getkeys(table):
    """
    customize by commenting out unwanted keys
    """
    keys=[]
    if table=="ER_expedition": 
        pass 
    if table=="ER_citations":
        keys.append("er_citation_name")
        keys.append("long_authors")
        keys.append("year")
        keys.append("title")
        keys.append("citation_type")
        keys.append("doi")
        keys.append("journal")
        keys.append("volume")
        keys.append("pages")
        keys.append("book_title")
        keys.append("book_editors")
        keys.append("publisher")
        keys.append("city")
    if table=="ER_locations":
        keys.append("er_location_name")
        keys.append("er_scientist_mail_names" )
#        keys.append("er_location_alternatives" )
        keys.append("location_type" )
        keys.append("location_begin_lat")
        keys.append("location_begin_lon" )
#        keys.append("location_begin_elevation" )
        keys.append("location_end_lat" )
        keys.append("location_end_lon" )
#        keys.append("location_end_elevation" )
        keys.append("continent_ocean" )
        keys.append("country" )
        keys.append("region" )
        keys.append("plate_block" )
        keys.append("terrane" )
        keys.append("tectonic_setting" )
#        keys.append("er_citation_names")
    if table=="ER_Formations":
        keys.append("er_formation_name")
        keys.append("formation_class")
        keys.append("formation_lithology")
        keys.append("formation_paleo_environment")
        keys.append("formation_thickness")
        keys.append("formation_description")
    if table=="ER_sections":
        keys.append("er_section_name")
        keys.append("er_section_alternatives")
        keys.append("er_expedition_name")
        keys.append("er_location_name")
        keys.append("er_formation_name")
        keys.append("er_member_name")
        keys.append("section_definition")
        keys.append("section_class")
        keys.append("section_lithology")
        keys.append("section_type")
        keys.append("section_n")
        keys.append("section_begin_lat")
        keys.append("section_begin_lon")
        keys.append("section_begin_elevation")
        keys.append("section_begin_height")
        keys.append("section_begin_drill_depth")
        keys.append("section_begin_composite_depth")
        keys.append("section_end_lat")
        keys.append("section_end_lon")
        keys.append("section_end_elevation")
        keys.append("section_end_height")
        keys.append("section_end_drill_depth")
        keys.append("section_end_composite_depth")
        keys.append("section_azimuth")
        keys.append("section_dip")
        keys.append("section_description")
        keys.append("er_scientist_mail_names")
        keys.append("er_citation_names")
    if table=="ER_sites":
        keys.append("er_location_name")
        keys.append("er_site_name")
#        keys.append("er_site_alternatives")
#        keys.append("er_formation_name")
#        keys.append("er_member_name")
#        keys.append("er_section_name")
        keys.append("er_scientist_mail_names")
        keys.append("site_class")
#        keys.append("site_type")
#        keys.append("site_lithology")
#        keys.append("site_height")
#        keys.append("site_drill_depth")
#        keys.append("site_composite_depth")
#        keys.append("site_lithology")
#        keys.append("site_description")
        keys.append("site_lat")
        keys.append("site_lon")
#        keys.append("site_location_precision")
#        keys.append("site_elevation")
    if table == "ER_samples" :
        keys.append("er_location_name")
        keys.append("er_site_name")
#       keys.append("er_sample_alternatives")
        keys.append("sample_azimuth")
        keys.append("sample_dip")
        keys.append("sample_bed_dip")
        keys.append("sample_bed_dip_direction")
#       keys.append("sample_cooling_rate")
#       keys.append("sample_type")
#       keys.append("sample_lat")
#       keys.append("sample_lon")
        keys.append("magic_method_codes")
    if table == "ER_ages" :
#       keys.append("er_location_name")
#       keys.append("er_site_name")
#       keys.append("er_section_name")
#       keys.append("er_formation_name")
#       keys.append("er_member_name")
#       keys.append("er_site_name")
#       keys.append("er_sample_name")
#       keys.append("er_specimen_name")
#       keys.append("er_fossil_name")
#       keys.append("er_mineral_name")
#       keys.append("tiepoint_name")
        keys.append("age")
        keys.append("age_sigma")
        keys.append("age_unit")
        keys.append("age_range_low")
        keys.append("age_range_hi")
        keys.append("timescale_eon")
        keys.append("timescale_era")
        keys.append("timescale_period")
        keys.append("timescale_epoch")
        keys.append("timescale_stage")
        keys.append("biostrat_zone")
        keys.append("conodont_zone")
        keys.append("magnetic_reversal_chron")
        keys.append("astronomical_stage")
#       keys.append("age_description")
#       keys.append("magic_method_codes")
#       keys.append("er_timescale_citation_names")
#       keys.append("er_citation_names")
    if table == "MAGIC_measurements" :
        keys.append("er_location_name")
        keys.append("er_site_name")
        keys.append("er_sample_name")
        keys.append("er_specimen_name")
        keys.append("measurement_positions")
        keys.append("treatment_temp")
        keys.append("treatment_ac_field")
        keys.append("treatment_dc_field")
        keys.append("treatment_dc_field_phi")
        keys.append("treatment_dc_field_theta")
        keys.append("magic_experiment_name")
        keys.append("magic_instrument_codes")
        keys.append("measurement_temp")
        keys.append("magic_method_codes")
        keys.append("measurement_inc")
        keys.append("measurement_dec")
        keys.append("measurement_magn_moment")
        keys.append("measurement_csd")
    return  keys


def getnames():
    """
    get mail names
    """
    namestring=""
    addmore=1
    while addmore:
        scientist=raw_input("Enter  name  - <Return> when done ")
        if scientist != "":
            namestring=namestring+":"+scientist
        else:
            namestring=namestring[1:]
            addmore=0
    return namestring

def magic_help(keyhelp):
    """
    returns a help message for a give magic key
    """
    helpme={}
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_location_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["location_type"]=	"Location type"
    helpme["location_begin_lat"]=	"Begin of section or core or outcrop -- latitude"
    helpme["location_begin_lon"]=	"Begin of section or core or outcrop -- longitude"
    helpme["location_begin_elevation"]=	"Begin of section or core or outcrop -- elevation relative to sealevel"
    helpme["location_end_lat"]=	"Ending of section or core -- latitude "
    helpme["location_end_lon"]=	"Ending of section or core -- longitude "
    helpme["location_end_elevation"]=	"Ending of section or core -- elevation relative to sealevel"
    helpme["location_geoid"]=	"Geoid used in determination of latitude and longitude:  WGS84, GEOID03, USGG2003, GEOID99, G99SSS , G99BM, DEFLEC99 "
    helpme["continent_ocean"]=	"Name for continent or ocean island region"
    helpme["ocean_sea"]=	"Name for location in an ocean or sea"
    helpme["country"]=	"Country name"
    helpme["region"]=	"Region name"
    helpme["plate_block"]=	"Plate or tectonic block name"
    helpme["terrane"]=	"Terrane name"
    helpme["tectonic_setting"]=	"Tectonic setting"
    helpme["location_description"]=	"Detailed description"
    helpme["location_url"]=	"Website URL for the location explicitly"
    helpme["er_scientist_mail_names"]=	"Colon-delimited list of names for scientists who described location"
    helpme["er_citation_names"]=	"Colon-delimited list of citations"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_formation_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["formation_class"]=	"General lithology class: igneous, metamorphic or sedimentary"
    helpme["formation_lithology"]=	"Lithology: e.g., basalt, sandstone, etc."
    helpme["formation_paleo_enviroment"]=	"Depositional environment"
    helpme["formation_thickness"]=	"Formation thickness"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_member_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["member_class"]=	"General lithology type"
    helpme["member_lithology"]=	"Lithology"
    helpme["member_paleo_environment"]=	"Depositional environment"
    helpme["member_thickness"]=	"Member thickness"
    helpme["member_description"]=	"Detailed description"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_section_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["section_definition"]=	"General definition of section"
    helpme["section_class"]=	"General lithology type"
    helpme["section_lithology"]=	"Section lithology or archeological classification"
    helpme["section_type"]=	"Section type"
    helpme["section_n"]=	"Number of subsections included composite (stacked) section"
    helpme["section_begin_lat"]=	"Begin of section or core -- latitude"
    helpme["section_begin_lon"]=	"Begin of section or core -- longitude"
    helpme["section_begin_elevation"]=	"Begin of section or core -- elevation relative to sealevel"
    helpme["section_begin_height"]=	"Begin of section or core -- stratigraphic height"
    helpme["section_begin_drill_depth"]=	"Begin of section or core -- depth in MBSF as used by ODP"
    helpme["section_begin_composite_depth"]=	"Begin of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_end_lat"]=	"End of section or core -- latitude "
    helpme["section_end_lon"]=	"End of section or core -- longitude "
    helpme["section_end_elevation"]=	"End of section or core -- elevation relative to sealevel"
    helpme["section_end_height"]=	"End of section or core -- stratigraphic height"
    helpme["section_end_drill_depth"]=	"End of section or core -- depth in MBSF as used by ODP"
    helpme["section_end_composite_depth"]=	"End of section or core -- composite depth in MBSF as used by ODP"
    helpme["section_azimuth"]=	"Section azimuth as measured clockwise from the north"
    helpme["section_dip"]=	"Section dip as measured into the outcrop"
    helpme["section_description"]=	"Detailed description"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_site_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["site_definition"]=	"General definition of site"
    helpme["site_class"]=	"[A]rchaeologic,[E]xtrusive,[I]ntrusive,[M]etamorphic,[S]edimentary"
    helpme["site_lithology"]=	"Site lithology or archeological classification"
    helpme["site_type"]=	"Site type: slag, lava flow, sediment layer, etc."
    helpme["site_lat"]=	"Site location -- latitude"
    helpme["site_lon"]=	"Site location -- longitude"
    helpme["site_location_precision"]=	"Site location -- precision in latitude and longitude"
    helpme["site_elevation"]=	"Site location -- elevation relative to sealevel"
    helpme["site_height"]=	"Site location -- stratigraphic height"
    helpme["site_drill_depth"]=	"Site location -- depth in MBSF as used by ODP"
    helpme["site_composite_depth"]=	"Site location -- composite depth in MBSF as used by ODP"
    helpme["site_description"]=	"Detailed description"
    helpme["magic_method_codes"]=	"Colon-delimited list of method codes"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["er_sample_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["sample_class"]=	"General lithology type"
    helpme["sample_lithology"]=	"Sample lithology or archeological classification"
    helpme["sample_type"]=	"Sample type"
    helpme["sample_texture"]=	"Sample texture"
    helpme["sample_alteration"]=	"Sample alteration grade"
    helpme["sample_alteration_type"]=	"Sample alteration type"
    helpme["sample_lat"]=	"Sample location -- latitude"
    helpme["sample_lon"]=	"Sample location -- longitude"
    helpme["sample_location_precision"]=	"Sample location -- precision in latitude and longitude"
    helpme["sample_elevation"]=	"Sample location -- elevation relative to sealevel"
    helpme["sample_height"]=	"Sample location -- stratigraphic height"
    helpme["sample_drill_depth"]=	"Sample location -- depth in MBSF as used by ODP"
    helpme["sample_composite_depth"]=	"Sample location -- composite depth in MBSF as used by ODP"
    helpme["sample_date"]=	"Sampling date"
    helpme["sample_time_zone"]=	"Sampling time zone"
    helpme["sample_azimuth"]=	"Sample azimuth as measured clockwise from the north"
    helpme["sample_dip"]=	"Sample dip as measured into the outcrop"
    helpme["sample_bed_dip_direction"]=	"Direction of the dip of a paleo-horizontal plane in the bedding"
    helpme["sample_bed_dip"]=	"Dip of the bedding as measured to the right of strike direction"
    helpme["sample_cooling_rate"]=	"Estimated ancient in-situ cooling rate per Ma"
    helpme["er_specimen_name"]=	"Name for specimen"
    helpme["er_specimen_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_section_name"]=	"Name for section or core"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["specimen_class"]=	"General lithology type"
    helpme["specimen_lithology"]=	"Specimen lithology or archeological classification"
    helpme["specimen_type"]=	"Specimen type"
    helpme["specimen_texture"]=	"Specimen texture"
    helpme["specimen_alteration"]=	"Specimen alteration grade"
    helpme["specimen_alteration_type"]=	"Specimen alteration type"
    helpme["specimen_elevation"]=	"Specimen location -- elevation relative to sealevel"
    helpme["specimen_height"]=	"Specimen location -- stratigraphic height"
    helpme["specimen_drill_depth"]=	"Specimen location -- depth in MBSF as used by ODP"
    helpme["specimen_composite_depth"]=	"Specimen location -- composite depth in MBSF as used by ODP"
    helpme["specimen_azimuth"]=	"Specimen azimuth as measured clockwise from the north"
    helpme["specimen_dip"]=	"Specimen dip as measured into the outcrop"
    helpme["specimen_volume"]=	"Specimen volume"
    helpme["specimen_weight"]=	"Specimen weight"
    helpme["specimen_density"]=	"Specimen density"
    helpme["specimen_size"]=	"Specimen grain size fraction"
    helpme["er_expedition_name"]=	"Name for seagoing or land expedition"
    helpme["er_location_name"]=	"Name for location or drill site"
    helpme["er_formation_name"]=	"Name for formation"
    helpme["er_member_name"]=	"Name for member"
    helpme["er_site_name"]=	"Name for site"
    helpme["er_sample_name"]=	"Name for sample"
    helpme["er_specimen_name"]=	"Name for specimen"
    helpme["er_fossil_name"]=	"Name for fossil"
    helpme["er_mineral_name"]=	"Name for mineral"
    helpme["GM-ALPHA"]=	"Age determination by using alpha counting"
    helpme["GM-ARAR"]=	"40Ar/39Ar age determination"
    helpme["GM-ARAR-AP"]=	"40Ar/39Ar age determination: Age plateau"
    helpme["GM-ARAR-II"]=	"40Ar/39Ar age determination: Inverse isochron"
    helpme["GM-ARAR-NI"]=	"40Ar/39Ar age determination: Normal isochron"
    helpme["GM-ARAR-TF"]=	"40Ar/39Ar age determination: Total fusion or recombined age"
    helpme["GM-C14"]=	"Radiocarbon age determination"
    helpme["GM-C14-AMS"]=	"Radiocarbon age determination: AMS"
    helpme["GM-C14-BETA"]=	"Radiocarbon age determination: Beta decay counting"
    helpme["GM-C14-CAL"]=	"Radiocarbon age determination: Calibrated"
    helpme["GM-CC"]=	"Correlation chronology"
    helpme["GM-CC-ARCH"]=	"Correlation chronology: Archeology"
    helpme["GM-CC-ARM"]=	"Correlation chronology: ARM"
    helpme["GM-CC-ASTRO"]=	"Correlation chronology: Astronomical"
    helpme["GM-CC-CACO3"]=	"Correlation chronology: Calcium carbonate"
    helpme["GM-CC-COLOR"]=	"Correlation chronology: Color or reflectance"
    helpme["GM-CC-GRAPE"]=	"Correlation chronology: Gamma Ray Polarimeter Experiment"
    helpme["GM-CC-IRM"]=	"Correlation chronology: IRM"
    helpme["GM-CC-ISO"]=	"Correlation chronology: Stable isotopes"
    helpme["GM-CC-REL"]=	"Correlation chronology: Relative chronology other than stratigraphic successions"
    helpme["GM-CC-STRAT"]=	"Correlation chronology: Stratigraphic succession"
    helpme["GM-CC-TECT"]=	"Correlation chronology: Tectites and microtectites"
    helpme["GM-CC-TEPH"]=	"Correlation chronology: Tephrochronology"
    helpme["GM-CC-X"]=	"Correlation chronology: Susceptibility"
    helpme["GM-CHEM"]=	"Chemical chronology"
    helpme["GM-CHEM-AAR"]=	"Chemical chronology: Amino acid racemization"
    helpme["GM-CHEM-OH"]=	"Chemical chronology: Obsidian hydration"
    helpme["GM-CHEM-SC"]=	"Chemical chronology: Stoan coatings CaCO3"
    helpme["GM-CHEM-TH"]=	"Chemical chronology: Tephra hydration"
    helpme["GM-COSMO"]=	"Cosmogenic age determination"
    helpme["GM-COSMO-AL26"]=	"Cosmogenic age determination: 26Al"
    helpme["GM-COSMO-AR39"]=	"Cosmogenic age determination: 39Ar"
    helpme["GM-COSMO-BE10"]=	"Cosmogenic age determination: 10Be"
    helpme["GM-COSMO-C14"]=	"Cosmogenic age determination: 14C"
    helpme["GM-COSMO-CL36"]=	"Cosmogenic age determination: 36Cl"
    helpme["GM-COSMO-HE3"]=	"Cosmogenic age determination: 3He"
    helpme["GM-COSMO-KR81"]=	"Cosmogenic age determination: 81Kr"
    helpme["GM-COSMO-NE21"]=	"Cosmogenic age determination: 21Ne"
    helpme["GM-COSMO-NI59"]=	"Cosmogenic age determination: 59Ni"
    helpme["GM-COSMO-SI32"]=	"Cosmogenic age determination: 32Si"
    helpme["GM-DENDRO"]=	"Dendrochronology"
    helpme["GM-ESR"]=	"Electron Spin Resonance"
    helpme["GM-FOSSIL"]=	"Age determined from fossil record"
    helpme["GM-FT"]=	"Fission track age determination"
    helpme["GM-HIST"]=	"Historically recorded geological event"
    helpme["GM-INT"]=	"Age determination through interpolation between at least two geological units of known age"
    helpme["GM-INT-L"]=	"Age determination through interpolation between at least two geological units of known age: Linear"
    helpme["GM-INT-S"]=	"Age determination through interpolation between at least two geological units of known age: Cubic spline"
    helpme["GM-ISO"]=	"Age determined by isotopic dating, but no further details available"
    helpme["GM-KAR"]=	"40K-40Ar age determination"
    helpme["GM-KAR-I"]=	"40K-40Ar age determination: Isochron"
    helpme["GM-KAR-MA"]=	"40K-40Ar age determination: Model age"
    helpme["GM-KCA"]=	"40K-40Ca age determination"
    helpme["GM-KCA-I"]=	"40K-40Ca age determination: Isochron"
    helpme["GM-KCA-MA"]=	"40K-40Ca age determination: Model age"
    helpme["GM-LABA"]=	"138La-138Ba age determination"
    helpme["GM-LABA-I"]=	"138La-138Ba age determination: Isochron"
    helpme["GM-LABA-MA"]=	"138La-138Ba age determination: Model age"
    helpme["GM-LACE"]=	"138La-138Ce age determination"
    helpme["GM-LACE-I"]=	"138La-138Ce age determination: Isochron"
    helpme["GM-LACE-MA"]=	"138La-138Ce age determination: Model age"
    helpme["GM-LICHE"]=	"Lichenometry"
    helpme["GM-LUHF"]=	"176Lu-176Hf age determination"
    helpme["GM-LUHF-I"]=	"176Lu-176Hf age determination: Isochron"
    helpme["GM-LUHF-MA"]=	"176Lu-176Hf age determination: Model age"
    helpme["GM-LUM"]=	"Luminescence"
    helpme["GM-LUM-IRS"]=	"Luminescence: Infrared stimulated luminescence"
    helpme["GM-LUM-OS"]=	"Luminescence: Optically stimulated luminescence"
    helpme["GM-LUM-TH"]=	"Luminescence: Thermoluminescence"
    helpme["GM-MOD"]=	"Model curve fit to available age dates"
    helpme["GM-MOD-L"]=	"Model curve fit to available age dates: Linear"
    helpme["GM-MOD-S"]=	"Model curve fit to available age dates: Cubic spline"
    helpme["GM-MORPH"]=	"Geomorphic chronology"
    helpme["GM-MORPH-DEF"]=	"Geomorphic chronology: Rate of deformation"
    helpme["GM-MORPH-DEP"]=	"Geomorphic chronology: Rate of deposition"
    helpme["GM-MORPH-POS"]=	"Geomorphic chronology: Geomorphology position"
    helpme["GM-MORPH-WEATH"]=	"Geomorphic chronology: Rock and mineral weathering"
    helpme["GM-NO"]=	"Unknown geochronology method"
    helpme["GM-O18"]=	"Oxygen isotope dating"
    helpme["GM-PBPB"]=	"207Pb-206Pb age determination"
    helpme["GM-PBPB-C"]=	"207Pb-206Pb age determination: Common Pb"
    helpme["GM-PBPB-I"]=	"207Pb-206Pb age determination: Isochron"
    helpme["GM-PLEO"]=	"Pleochroic haloes"
    helpme["GM-PMAG-ANOM"]=	"Paleomagnetic age determination: Magnetic anomaly identification"
    helpme["GM-PMAG-APWP"]=	"Paleomagnetic age determination: Comparing paleomagnetic data to APWP"
    helpme["GM-PMAG-ARCH"]=	"Paleomagnetic age determination: Archeomagnetism"
    helpme["GM-PMAG-DIR"]=	"Paleomagnetic age determination: Directions"
    helpme["GM-PMAG-POL"]=	"Paleomagnetic age determination: Polarities"
    helpme["GM-PMAG-REGSV"]=	"Paleomagnetic age determination: Correlation to a regional secular variation curve"
    helpme["GM-PMAG-RPI"]=	"Paleomagnetic age determination: Relative paleointensity"
    helpme["GM-PMAG-VEC"]=	"Paleomagnetic age determination: Full vector"
    helpme["GM-RATH"]=	"226Ra-230Th age determination"
    helpme["GM-RBSR"]=	"87Rb-87Sr age determination"
    helpme["GM-RBSR-I"]=	"87Rb-87Sr age determination: Isochron"
    helpme["GM-RBSR-MA"]=	"87Rb-87Sr age determination: Model age"
    helpme["GM-REOS"]=	"187Re-187Os age determination"
    helpme["GM-REOS-I"]=	"187Re-187Os age determination: Isochron"
    helpme["GM-REOS-MA"]=	"187Re-187Os age determination: Model age"
    helpme["GM-REOS-PT"]=	"187Re-187Os age determination: Pt normalization of 186Os"
    helpme["GM-SCLERO"]=	"Screlochronology"
    helpme["GM-SHRIMP"]=	"SHRIMP age dating"
    helpme["GM-SMND"]=	"147Sm-143Nd age determination"
    helpme["GM-SMND-I"]=	"147Sm-143Nd age determination: Isochron"
    helpme["GM-SMND-MA"]=	"147Sm-143Nd age determination: Model age"
    helpme["GM-THPB"]=	"232Th-208Pb age determination"
    helpme["GM-THPB-I"]=	"232Th-208Pb age determination: Isochron"
    helpme["GM-THPB-MA"]=	"232Th-208Pb age determination: Model age"
    helpme["GM-UPA"]=	"235U-231Pa age determination"
    helpme["GM-UPB"]=	"U-Pb age determination"
    helpme["GM-UPB-CC-T0"]=	"U-Pb age determination: Concordia diagram age, upper intersection"
    helpme["GM-UPB-CC-T1"]=	"U-Pb age determination: Concordia diagram age, lower intersection"
    helpme["GM-UPB-I-206"]=	"U-Pb age determination: 238U-206Pb isochron"
    helpme["GM-UPB-I-207"]=	"U-Pb age determination: 235U-207Pb isochron"
    helpme["GM-UPB-MA-206"]=	"U-Pb age determination: 238U-206Pb model age"
    helpme["GM-UPB-MA-207"]=	"U-Pb age determination: 235U-207Pb model age"
    helpme["GM-USD"]=	"Uranium series disequilibrium age determination"
    helpme["GM-USD-PA231-TH230"]=	"Uranium series disequilibrium age determination: 231Pa-230Th"
    helpme["GM-USD-PA231-U235"]=	"Uranium series disequilibrium age determination: 231Pa-235U"
    helpme["GM-USD-PB210"]=	"Uranium series disequilibrium age determination: 210Pb"
    helpme["GM-USD-RA226-TH230"]=	"Uranium series disequilibrium age determination: 226Ra-230Th"
    helpme["GM-USD-RA228-TH232"]=	"Uranium series disequilibrium age determination: 228Ra-232Th"
    helpme["GM-USD-TH228-TH232"]=	"Uranium series disequilibrium age determination: 228Th-232Th"
    helpme["GM-USD-TH230"]=	"Uranium series disequilibrium age determination: 230Th"
    helpme["GM-USD-TH230-TH232"]=	"Uranium series disequilibrium age determination: 230Th-232Th"
    helpme["GM-USD-TH230-U234"]=	"Uranium series disequilibrium age determination: 230Th-234U"
    helpme["GM-USD-TH230-U238"]=	"Uranium series disequilibrium age determination: 230Th-238U"
    helpme["GM-USD-U234-U238"]=	"Uranium series disequilibrium age determination: 234U-238U"
    helpme["GM-UTH"]=	"238U-230Th age determination"
    helpme["GM-UTHHE"]=	"U-Th-He age determination"
    helpme["GM-UTHPB"]=	"U-Th-Pb age determination"
    helpme["GM-UTHPB-CC-T0"]=	"U-Th-Pb age determination: Concordia diagram intersection age, upper intercept"
    helpme["GM-UTHPB-CC-T1"]=	"U-Th-Pb age determination: Concordia diagram intersection age, lower intercept"
    helpme["GM-VARVE"]=	"Age determined by varve counting"
    helpme["tiepoint_name"]=	"Name for tiepoint horizon"
    helpme["tiepoint_alternatives"]=	"Colon-delimited list of alternative names and abbreviations"
    helpme["tiepoint_height"]=	"Tiepoint stratigraphic height relative to reference tiepoint"
    helpme["tiepoint_height_sigma"]=	"Tiepoint stratigraphic height uncertainty"
    helpme["tiepoint_elevation"]=	"Tiepoint elevation relative to sealevel"
    helpme["tiepoint_type"]=	"Tiepoint type"
    helpme["age"]=	"Age"
    helpme["age_sigma"]=	"Age -- uncertainty"
    helpme["age_range_low"]=	"Age -- low range"
    helpme["age_range_high"]=	"Age -- high range"
    helpme["age_unit"]=	"Age -- unit"
    helpme["timescale_eon"]=	"Timescale eon"
    helpme["timescale_era"]=	"Timescale era"
    helpme["timescale_period"]=	"Timescale period"
    helpme["timescale_epoch"]=	"Timescale epoch"
    helpme["timescale_stage"]=	"Timescale stage"
    helpme["biostrat_zone"]=	"Biostratigraphic zone"
    helpme["conodont_zone"]=	"Conodont zone"
    helpme["magnetic_reversal_chron"]=	"Magnetic reversal chron"
    helpme["astronomical_stage"]=	"Astronomical stage name"
    helpme["oxygen_stage"]=	"Oxygen stage name"
    helpme["age_culture_name"]=	"Age culture name"
    return helpme[keyhelp]

def dosundec(sundata):
    """
    returns the declination for a given set of suncompass data
    """
    rad=numpy.pi/180.
    iday=0
    timedate=sundata["date"]
    timedate=timedate.split(":") 
    year=int(timedate[0])
    mon=int(timedate[1])
    day=int(timedate[2])
    hours=float(timedate[3])
    min=float(timedate[4])
    du=int(sundata["delta_u"])
    hrs=hours-du
    if hrs > 24:
        day+=1
        hrs=hrs-24
    if hrs < 0:
        day=day-1
        hrs=hrs+24
    julian_day=julian(mon,day,year)
    utd=(hrs+min/60.)/24.
    greenwich_hour_angle,delta=gha(julian_day,utd)
    H=greenwich_hour_angle+float(sundata["lon"])
    if H > 360: H=H-360
    lat=float(sundata["lat"])
    if H > 90 and H < 270:lat=-lat
# now do spherical trig to get azimuth to sun
    lat=(lat)*rad
    delta=(delta)*rad
    H=H*rad
    ctheta=numpy.sin(lat)*numpy.sin(delta)+numpy.cos(lat)*numpy.cos(delta)*numpy.cos(H)
    theta=numpy.arccos(ctheta)
    beta=numpy.cos(delta)*numpy.sin(H)/numpy.sin(theta)
#
#       check which beta
#
    beta=numpy.arcsin(beta)/rad
    if delta < lat: beta=180-beta
    sunaz=180-beta
    suncor=(sunaz+float(sundata["shadow_angle"]))%360. #  mod 360
    return suncor

def gha(julian_day,f):
    """
    returns greenwich hour angle
    """
    rad=numpy.pi/180.
    d=julian_day-2451545.0+f
    L= 280.460 + 0.9856474*d
    g=  357.528 + 0.9856003*d
    L=L%360.
    g=g%360.
# ecliptic longitude
    lamb=L+1.915*numpy.sin(g*rad)+.02*numpy.sin(2*g*rad)
# obliquity of ecliptic
    epsilon= 23.439 - 0.0000004*d
# right ascension (in same quadrant as lambda)
    t=(numpy.tan((epsilon*rad)/2))**2
    r=1/rad
    rl=lamb*rad
    alpha=lamb-r*t*numpy.sin(2*rl)+(r/2)*t*t*numpy.sin(4*rl)
#       alpha=mod(alpha,360.0)
# declination
    delta=numpy.sin(epsilon*rad)*numpy.sin(lamb*rad)
    delta=numpy.arcsin(delta)/rad
# equation of time
    eqt=(L-alpha)
#
    utm=f*24*60
    H=utm/4+eqt+180
    H=H%360.0
    return H,delta


def julian(mon,day,year):
    """
    returns julian day
    """
    ig=15+31*(10+12*1582)
    if year == 0: 
        print "Julian no can do"
        return
    if year < 0: year=year+1
    if mon > 2:  
        julian_year=year
        julian_month=mon+1
    else:
        julian_year=year-1
        julian_month=mon+13
    j1=int(365.25*julian_year)
    j2=int(30.6001*julian_month)
    j3=day+1720995
    julian_day=j1+j2+j3
    if day+31*(mon+12*year) >= ig:
        jadj=int(0.01*julian_year)
        julian_day=julian_day+2-jadj+int(0.25*jadj)
    return julian_day

def fillkeys(Recs):
    """
    reconciles keys of dictionaries within Recs.
    """
    keylist,OutRecs=[],[]
    for rec in Recs:
        for key in rec.keys(): 
            if key not in keylist:keylist.append(key)
    for rec in  Recs:
        for key in keylist:
            if key not in rec.keys(): rec[key]=""
        OutRecs.append(rec)
    return OutRecs,keylist

def fisher_mean(data):
    """
    calculates fisher parameters for data
    """
    R,Xbar,X,fpars=0,[0,0,0],[],{}
    N=len(data)
    if N <2:
       return fpars
    X=dir2cart(data)
    #for rec in data:
    #    X.append(dir2cart([rec[0],rec[1],1.]))
    for i in range(len(X)):
        for c in range(3):
           Xbar[c]+=X[i][c]
    for c in range(3):
        R+=Xbar[c]**2
    R=numpy.sqrt(R)
    for c in range(3):
        Xbar[c]=Xbar[c]/R    
    dir=cart2dir(Xbar)
    fpars["dec"]=dir[0]
    fpars["inc"]=dir[1]
    fpars["n"]=N
    fpars["r"]=R
    if N!=R:
        k=(N-1.)/(N-R)
        fpars["k"]=k
        csd=81./numpy.sqrt(k)
    else:
        fpars['k']='inf'
        csd=0.
    b=20.**(1./(N-1.)) -1
    a=1-b*(N-R)/R
    if a<-1:a=-1
    a95=numpy.arccos(a)*180./numpy.pi
    fpars["alpha95"]=a95
    fpars["csd"]=csd
    if a<0: fpars["alpha95"] = 180.0
    return fpars
 
def gausspars(data):
    """
    calculates gaussian statistics for data
    """
    N,mean,d=len(data),0.,0.
    if N<1: return "",""
    if N==1: return data[0],0
    for j in range(N):
       mean+=data[j]/float(N)
    for j in range(N):
       d+=(data[j]-mean)**2 
    stdev=numpy.sqrt(d*(1./(float(N-1))))
    return mean,stdev

def weighted_mean(data):
    """
    calculates weighted mean of data
    """
    W,N,mean,d=0,len(data),0,0
    if N<1: return "",""
    if N==1: return data[0][0],0
    for x in data:
       W+=x[1] # sum of the weights
    for x in data:
       mean+=(float(x[1])*float(x[0]))/float(W)
    for x in data:
       d+=(float(x[1])/float(W))*(float(x[0])-mean)**2 
    stdev=numpy.sqrt(d*(1./(float(N-1))))
    return mean,stdev


def lnpbykey(data,key0,key1): # calculate a fisher mean of key1 data for a group of key0 
    PmagRec={}
    if len(data)>1:
        for rec in data:
            rec['dec']=float(rec[key1+'_dec'])
            rec['inc']=float(rec[key1+'_inc'])
        fpars=dolnp(data,key1+'_direction_type')
        PmagRec[key0+"_dec"]=fpars["dec"]
        PmagRec[key0+"_inc"]=fpars["inc"]
        PmagRec[key0+"_n"]=(fpars["n_total"])
        PmagRec[key0+"_n_lines"]=fpars["n_lines"]
        PmagRec[key0+"_n_planes"]=fpars["n_planes"]
        PmagRec[key0+"_r"]=fpars["R"]
        PmagRec[key0+"_k"]=fpars["K"]
        PmagRec[key0+"_alpha95"]=fpars["alpha95"]
        if int(PmagRec[key0+"_n_planes"])>0:
            PmagRec["magic_method_codes"]="DE-FM-LP"
        elif int(PmagRec[key0+"_n_lines"])>2:
            PmagRec["magic_method_codes"]="DE-FM"
    elif len(data)==1:
        PmagRec[key0+"_dec"]=data[0][key1+'_dec']
        PmagRec[key0+"_inc"]=data[0][key1+'_inc']
        PmagRec[key0+"_n"]='1'
        if data[0][key1+'_direction_type']=='l': 
            PmagRec[key0+"_n_lines"]='1'
            PmagRec[key0+"_n_planes"]='0'
        if data[0][key1+'_direction_type']=='p': 
            PmagRec[key0+"_n_planes"]='1'
            PmagRec[key0+"_n_lines"]='0'
        PmagRec[key0+"_alpha95"]=""
        PmagRec[key0+"_r"]=""
        PmagRec[key0+"_k"]=""
        PmagRec[key0+"_direction_type"]="l"
    return PmagRec


def dolnp(data,direction_type_key):
    """
    returns fisher mean, a95 for data  using method of mcfadden and mcelhinny '88 for lines and planes
    """
    if "tilt_correction" in data[0].keys(): 
        tc=data[0]["tilt_correction"]
    else:
        tc='-1'
    n_lines,n_planes=0,0
    X,L,fdata,dirV=[],[],[],[0,0,0]
    E=[0,0,0]
    fpars={}
#
# sort data  into lines and planes and collect cartesian coordinates
    for rec in data:
        cart=dir2cart([rec["dec"],rec["inc"]])[0]
        if direction_type_key in rec.keys() and rec[direction_type_key]=='p': # this is a pole to a plane
            n_planes+=1
            L.append(cart) # this is the "EL, EM, EN" array of MM88
        else: # this is a line
            n_lines+=1
            fdata.append([rec["dec"],rec["inc"],1.]) # collect data for fisher calculation
            X.append(cart)
            E[0]+=cart[0] 
            E[1]+=cart[1] 
            E[2]+=cart[2] 
# set up initial points on the great circles
    V,XV=[],[]
    if n_planes !=0:
        if n_lines==0:
            V=dir2cart([180.,-45.,1.]) # set the initial direction arbitrarily
        else:
           R=numpy.sqrt(E[0]**2+E[1]**2+E[2]**2) 
           for c in E:
               V.append(c/R) # set initial direction as mean of lines
        U=E[:]   # make a copy of E
        for pole in L:
            XV.append(vclose(pole,V)) # get some points on the great circle
            for c in range(3):
               U[c]=U[c]+XV[-1][c]
# iterate to find best agreement
        angle_tol=1.
        while angle_tol > 0.1:
            angles=[]
            for k in range(n_planes): 
               for c in range(3): U[c]=U[c]-XV[k][c]
               R=numpy.sqrt(U[0]**2+U[1]**2+U[2]**2)
               for c in range(3):V[c]=U[c]/R
               XX=vclose(L[k],V)
               ang=XX[0]*XV[k][0]+XX[1]*XV[k][1]+XX[2]*XV[k][2]
               angles.append(numpy.arccos(ang)*180./numpy.pi)
               for c in range(3):
                   XV[k][c]=XX[c]
                   U[c]=U[c]+XX[c]
               amax =-1
               for ang in angles:
                   if ang > amax:amax=ang
               angle_tol=amax
# calculating overall mean direction and R
        U=E[:]
        for dir in XV:
            for c in range(3):U[c]=U[c]+dir[c]
        R=numpy.sqrt(U[0]**2+U[1]**2+U[2]**2)
        for c in range(3):U[c]=U[c]/R
# get dec and inc of solution points on gt circles
        dirV=cart2dir(U)
# calculate modified Fisher stats fo fit
        n_total=n_lines+n_planes
        NP=n_lines+0.5*n_planes
        if NP<1.1:NP=1.1
        if n_total-R !=0:
            K=(NP-1.)/(n_total-R)
            fac=(20.**(1./(NP-1.))-1.)
            fac=fac*(NP-1.)/K
            a=1.-fac/R
            a95=a
            if abs(a) > 1.0: a95=1.
            if a<0:a95=-a95
            a95=numpy.arccos(a95)*180./numpy.pi
        else: 
            a95=0.
            K='inf'
    else:
        dir=fisher_mean(fdata)
        n_total,R,K,a95=dir["n"],dir["r"],dir["k"],dir["alpha95"]
        dirV[0],dirV[1]=dir["dec"],dir["inc"]
    fpars["tilt_correction"]=tc
    fpars["n_total"]='%i '% (n_total)
    fpars["n_lines"]='%i '% (n_lines)
    fpars["n_planes"]='%i '% (n_planes)
    fpars["R"]='%5.4f '% (R)
    if K!='inf':
        fpars["K"]='%6.0f '% (K)
    else:
        fpars["K"]=K
    fpars["alpha95"]='%7.1f '% (a95)
    fpars["dec"]='%7.1f '% (dirV[0])
    fpars["inc"]='%7.1f '% (dirV[1])
    return fpars

def vclose(L,V):
    """
    gets the closest vector
    """
    lam,X=0,[]
    for k in range(3):
        lam=lam+V[k]*L[k] 
    beta=numpy.sqrt(1.-lam**2)
    for k in range(3):
        X.append( ((V[k]-lam*L[k])/beta))
    return X

   
def scoreit(pars,PmagSpecRec,accept,text,verbose):
    """
    gets a grade for a given set of data, spits out stuff
    """
    s=PmagSpecRec["er_specimen_name"]
    PmagSpecRec["measurement_step_min"]='%8.3e' % (pars["measurement_step_min"])
    PmagSpecRec["measurement_step_max"]='%8.3e' % (pars["measurement_step_max"])
    PmagSpecRec["measurement_step_unit"]=pars["measurement_step_unit"]
    PmagSpecRec["specimen_int_n"]='%i'%(pars["specimen_int_n"])
    PmagSpecRec["specimen_lab_field_dc"]='%8.3e'%(pars["specimen_lab_field_dc"])
    PmagSpecRec["specimen_int"]='%8.3e '%(pars["specimen_int"])
    PmagSpecRec["specimen_b"]='%5.3f '%(pars["specimen_b"])
    PmagSpecRec["specimen_q"]='%5.1f '%(pars["specimen_q"])
    PmagSpecRec["specimen_f"]='%5.3f '%(pars["specimen_f"])
    PmagSpecRec["specimen_fvds"]='%5.3f'%(pars["specimen_fvds"])
    PmagSpecRec["specimen_b_beta"]='%5.3f'%(pars["specimen_b_beta"])
    PmagSpecRec["specimen_int_mad"]='%7.1f'%(pars["specimen_int_mad"])
    PmagSpecRec["specimen_dec"]='%7.1f'%(pars["specimen_dec"])
    PmagSpecRec["specimen_inc"]='%7.1f'%(pars["specimen_inc"])
    PmagSpecRec["specimen_dang"]='%7.1f '%(pars["specimen_dang"])
    PmagSpecRec["specimen_drats"]='%7.1f '%(pars["specimen_drats"])
    PmagSpecRec["specimen_int_ptrm_n"]='%i '%(pars["specimen_int_ptrm_n"])
    PmagSpecRec["specimen_rsc"]='%6.4f '%(pars["specimen_rsc"])
    PmagSpecRec["specimen_md"]='%i '%(int(pars["specimen_md"]))
    PmagSpecRec["specimen_b_sigma"]='%5.3f '%(pars["specimen_b_sigma"])
    #PmagSpecRec["specimen_Z"]='%7.1f'%(pars["specimen_Z"])
  # check score
   #
    kill=grade(PmagSpecRec,accept,'specimen')
    Grade=""
    if len(kill)==0:
        Grade='A'
    else:
        Grade='F'
    pars["specimen_grade"]=Grade
    if verbose==0:
        return pars,kill
    diffcum=0
    if pars['measurement_step_unit']=='K':
        outstr= "specimen     Tmin  Tmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  Gmax \n"
        pars_out= (s,(pars["measurement_step_min"]-273),(pars["measurement_step_max"]-273),(pars["specimen_int_n"]),1e6*(pars["specimen_lab_field_dc"]),1e6*(pars["specimen_int"]),pars["specimen_b"],pars["specimen_q"],pars["specimen_f"],pars["specimen_fvds"],pars["specimen_b_beta"],pars["specimen_int_mad"],pars["specimen_dang"],pars["specimen_drats"],pars["specimen_int_ptrm_n"],pars["specimen_grade"],numpy.sqrt(pars["specimen_rsc"]),int(pars["specimen_md"]), pars["specimen_b_sigma"],pars['specimen_gamma'])
        outstring= '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f' % pars_out +'\n'
    elif pars['measurement_step_unit']=='J':
        outstr= "specimen     Wmin  Wmax  N  lab_field  B_anc  b  q  f(coe)  Fvds  beta  MAD  Dang  Drats  Nptrm  Grade  R  MD%  sigma  ThetaMax DeltaMax GammaMax\n"
        pars_out= (s,(pars["measurement_step_min"]),(pars["measurement_step_max"]),(pars["specimen_int_n"]),1e6*(pars["specimen_lab_field_dc"]),1e6*(pars["specimen_int"]),pars["specimen_b"],pars["specimen_q"],pars["specimen_f"],pars["specimen_fvds"],pars["specimen_b_beta"],pars["specimen_int_mad"],pars["specimen_dang"],pars["specimen_drats"],pars["specimen_int_ptrm_n"],pars["specimen_grade"],numpy.sqrt(pars["specimen_rsc"]),int(pars["specimen_md"]), pars["specimen_b_sigma"],pars["specimen_theta"],pars["specimen_delta"],pars["specimen_gamma"])
        outstring= '%s %4.0f %4.0f %i %4.1f %4.1f %5.3f %5.1f %5.3f %5.3f %5.3f  %7.1f %7.1f %7.1f %s %s %6.3f %i %5.3f %7.1f %7.1f %7.1f' % pars_out +'\n'               
    if pars["specimen_grade"]!="A":
        print '\n killed by:'
        print kill
        print '\n'
    print outstr
    print outstring
    return pars,kill

def b_vdm(B,lat):
    """ 
    Converts field values in tesla to v(a)dm in Am^2
    """
    rad=numpy.pi/180.
    fact=((6.371e6)**3)*1e7 # changed radius of the earth from 3.367e6 3/12/2010
    colat=(90.-lat) * rad
    return fact*B/(numpy.sqrt(1+3*(numpy.cos(colat)**2)))

def vdm_b(vdm,lat):
    """ 
    Converts v(a)dm to  field values in tesla 
    """
    rad=numpy.pi/180.
    fact=((6.371e6)**3)*1e7 # changed radius of the earth from 3.367e6 3/12/2010
    colat=(90.-lat) * rad
    return vdm*(numpy.sqrt(1+3*(numpy.cos(colat)**2)))/fact

def binglookup(w1i,w2i):
    """
    Bingham statistics lookup table.
    """ 
    K={'0.06': {'0.02': ['-25.58', '-8.996'], '0.06': ['-9.043', '-9.043'], '0.04': ['-13.14', '-9.019']}, '0.22': {'0.08': ['-6.944', '-2.644'], '0.02': ['-25.63', '-2.712'], '0.20': ['-2.649', '-2.354'], '0.06': [ '-9.027', '-2.673'], '0.04': ['-13.17', '-2.695'], '0.14': ['-4.071', '-2.521'], '0.16': ['-3.518', '-2.470'], '0.10': ['-5.658', '-2.609'], '0.12': ['-4.757', '-2.568'], '0.18': ['-3.053', '-2.414'], '0.22': ['-2.289', '-2.289']}, '0.46': {'0.02': ['-25.12', '-0.250'], '0.08': ['-6.215', '0.000'], '0.06': ['-8.371', '-0.090'], '0.04': ['-12.58', '-0.173']}, '0.44': {'0.08': ['-6.305', '-0.186'], '0.02': ['-25.19', '-0.418'], '0.06': ['-8.454', '-0.270'], '0.04': ['-12.66', '-0.347'], '0.10': ['-4.955', '-0.097'], '0.12': ['-3.992', '0.000']}, '0.42': {'0.08': ['-6.388', '-0.374'], '0.02': ['-25.5', '-0.589'], '0.06': [ '-8.532', '-0.452'], '0.04': ['-12.73', '-0.523'], '0.14': ['-3.349', '-0.104'], '0.16': ['-2.741', '0.000'], '0.10': ['-5.045', '-0.290'], '0.12': ['-4.089', '-0.200']}, '0.40': {'0.08': ['-6.466', '-0.564'], '0.02': ['-25.31', '-0.762'], '0.20': ['-1.874', '-0.000'], '0.06': ['-8.604', '-0.636'], '0.04': ['-12.80', '-0.702'], '0.14': ['-3.446', '-0.312'], '0.16': ['-2.845', '-0.215'], '0.10': ['-5.126', '-0.486'] , '0.12': ['-4.179', '-0.402'], '0.18': ['-2.330', '-0.111']}, '0.08': {'0.02': ['-25.6', '-6.977'], '0.08': ['-7.035', '-7.035'], '0.06': ['-9.065', '-7.020'], '0.04': ['-13.16', '-6.999']}, '0.28': {'0.08': ['-6.827', '-1.828'], '0.28': ['-1.106', '-1.106'], '0.02': ['-25.57', '-1.939'], '0.20': ['-2.441', '-1.458'], '0.26': ['-1.406', '-1.203'], '0.24': ['-1.724', '-1.294'], '0.06': ['-8.928', '-1.871'], '0.04': ['-13.09', '-1.908'], '0.14': ['-3.906', '-1.665'], '0.16': ['-3.338', '-1.601'], '0.10': ['-5.523', '-1.779'], '0.12': ['-4.606', '-1.725'], '0.18': ['-2.859', '-1.532'], '0.22': ['-2.066', '-1.378']}, '0.02': {'0.02': ['-25.55','-25.55']}, '0.26': {'0.08': ['-6.870', '-2.078'], '0.02': ['-25.59', '-2.175'], '0.20': ['-2.515', '-1.735'], '0.26': ['-1.497', '-1.497'], '0.24': ['-1.809', '-1.582'], '0.06': ['-8.96 6', '-2.117'], '0.04': ['-13.12', '-2.149'], '0.14': ['-3.965', '-1.929'], '0.16': ['-3.403', '-1.869'], '0.10': ['-5.573', '-2.034'], '0.12': ['-4.661', '-1.984'], '0.18': ['-2.928', '-1.805'], '0.22': ['-2.1 46', '-1.661']}, '0.20': {'0.08': ['-6.974', '-2.973'], '0.02': ['-25.64', '-3.025'], '0.20': ['-2.709', '-2.709'], '0.06': ['-9.05', '-2.997'], '0.04': ['-13.18', '-3.014'], '0.14': ['-4.118', '-2.863'], '0.1 6': ['-3.570', '-2.816'], '0.10': ['-5.694', '-2.942'], '0.12': ['-4.799', '-2.905'], '0.18': ['-3.109', '-2.765']}, '0.04': {'0.02': ['-25.56', '-13.09'], '0.04': ['-13.11', '-13.11']}, '0.14': {'0.08': ['-7.  033', '-4.294'], '0.02': ['-25.64', '-4.295'], '0.06': ['-9.087', '-4.301'], '0.04': ['-13.20', '-4.301'], '0.14': ['-4.231', '-4.231'], '0.10': ['-5.773', '-4.279'], '0.12': ['-4.896', '-4.258']}, '0.16': {'0 .08': ['-7.019', '-3.777'], '0.02': ['-25.65', '-3.796'], '0.06': ['-9.081', '-3.790'], '0.04': ['-13.20', '-3.796'], '0.14': ['-4.198', '-3.697'], '0.16': ['-3.659', '-3.659'], '0.10': ['-5.752', '-3.756'], ' 0.12': ['-4.868', '-3.729']}, '0.10': {'0.02': ['-25.62', '-5.760'], '0.08': ['-7.042', '-5.798'], '0.06': ['-9.080', '-5.791'], '0.10': ['-5.797', '-5.797'], '0.04': ['-13.18', '-5.777']}, '0.12': {'0.08': [' -7.041', '-4.941'], '0.02': ['-25.63', '-4.923'], '0.06': ['-9.087', '-4.941'], '0.04': ['-13.19', '-4.934'], '0.10': ['-5.789', '-4.933'], '0.12': ['-4.917', '-4.917']}, '0.18': {'0.08': ['-6.999', '-3.345'], '0.02': ['-25.65', '-3.381'], '0.06': ['-9.068', '-3.363'], '0.04': ['-13.19', '-3.375'], '0.14': ['-4.160', '-3.249'], '0.16': ['-3.616', '-3.207'], '0.10': ['-5.726', '-3.319'], '0.12': ['-4.836', '-3.287'] , '0.18': ['-3.160', '-3.160']}, '0.38': {'0.08': ['-6.539', '-0.757'], '0.02': ['-25.37', '-0.940'], '0.20': ['-1.986', '-0.231'], '0.24': ['-1.202', '0.000'], '0.06': ['-8.670', '-0.824'], '0.04': ['-12.86', '-0.885'], '0.14': ['-3.536', '-0.522'], '0.16': ['-2.941', '-0.432'], '0.10': ['-5.207', '-0.684'], '0.12': ['-4.263', '-0.606'], '0.18': ['-2.434', '-0.335'], '0.22': ['-1.579', '-0.120']}, '0.36': {'0.08': ['-6.606', '-9.555'], '0.28': ['-0.642', '0.000'], '0.02': ['-25.42', '-1.123'], '0.20': ['-2.089', '-0.464'], '0.26': ['-0.974', '-0.129'], '0.24': ['-1.322', '-0.249'], '0.06': ['-8.731', '-1.017'], '0.04': ['-12.91', '-1.073'], '0.14': ['-3.620', '-0.736'], '0.16': ['-3.032', '-0.651'], '0.10': ['-5.280', '-0.887'], '0.12': ['-4.342', '-0.814'], '0.18': ['-2.531', '-0.561'], '0.22': ['-1.690', '-0.360']}, '0.34 ': {'0.08': ['-6.668', '-1.159'], '0.28': ['-0.771', '-0.269'], '0.02': ['-25.46', '-1.312'], '0.20': ['-2.186', '-0.701'], '0.26': ['-1.094', '-0.389'], '0.24': ['-1.433', '-0.500'], '0.06': ['-8.788', '-1.21 6'], '0.32': ['-0.152', '0.000'], '0.04': ['-12.96', '-1.267'], '0.30': ['-0.459', '-0.140'], '0.14': ['-3.699', '-0.955'], '0.16': ['-3.116', '-0.876'], '0.10': ['-5.348', '-1.096'], '0.12': ['-4.415', '-1.02 8'], '0.18': ['-2.621', '-0.791'], '0.22': ['-1.794', '-0.604']}, '0.32': {'0.08': ['-6.725', '-1.371'], '0.28': ['-0.891', '-0.541'], '0.02': ['-25.50', '-1.510'], '0.20': ['-2.277', '-0.944'], '0.26': ['-1.2 06', '-0.653'], '0.24': ['-1.537', '-0.756'], '0.06': ['-8.839', '-1.423'], '0.32': ['-0.292', '-0.292'], '0.04': ['-13.01', '-1.470'], '0.30': ['-0.588', '-0.421'], '0.14': ['-3.773', '-1.181'], '0.16': ['-3.  195', '-1.108'], '0.10': ['-5.411', '-1.313'], '0.12': ['-4.484', '-1.250'], '0.18': ['-2.706', '-1.028'], '0.22': ['-1.891', '-0.853']}, '0.30': {'0.08': ['-6.778', '-1.596'], '0.28': ['-1.002', '-0.819'], '0 .02': ['-25.54', '-1.718'], '0.20': ['-2.361', '-1.195'], '0.26': ['-1.309', '-0.923'], '0.24': ['-1.634', '-1.020'], '0.06': ['-8.886', '-1.641'], '0.04': ['-13.05', '-1.682'], '0.30': ['-0.708', '-0.708'], ' 0.14': ['-3.842', '-1.417'], '0.16': ['-3.269', '-1.348'], '0.10': ['-5.469', '-1.540'], '0.12': ['-4.547', '-1.481'], '0.18': ['-2.785', '-1.274'], '0.22': ['-1.981', '-1.110']}, '0.24': {'0.08': ['-6.910', ' -2.349'], '0.02': ['-25.61', '-2.431'], '0.20': ['-2.584', '-2.032'], '0.24': ['-1.888', '-1.888'], '0.06': ['-8.999', '-2.382'], '0.04': ['-23.14', '-2.410'], '0.14': ['-4.021', '-2.212'], '0.16': ['-3.463', '-2.157'], '0.10': ['-5.618', '-2.309'], '0.12': ['-4.711', '-2.263'], '0.18': ['-2.993', '-2.097'], '0.22': ['-2.220', '-1.963']}}
    w1,w2=0.,0.
    wstart,incr=0.01,0.02
    if w1i < wstart: w1='%4.2f'%(wstart+incr/2.)
    if w2i < wstart: w2='%4.2f'%(wstart+incr/2.)
    wnext=wstart+incr
    while wstart <0.5:
        if w1i >=wstart and w1i <wnext :  
            w1='%4.2f'%(wstart+incr/2.)
        if w2i >=wstart and w2i <wnext :  
            w2='%4.2f'%(wstart+incr/2.)
        wstart+=incr
        wnext+=incr
    k1,k2=float(K[w2][w1][0]),float(K[w2][w1][1])
    return  k1,k2

def cdfout(data,file):
    """
    spits out the cdf for data to file
    """
    f=open(file,"w")
    data.sort()
    for j in range(len(data)):
        y=float(j)/float(len(data))
        out=str(data[j])+' '+str(y)+ '\n'
        f.write(out)

def dobingham(data):
    """
    gets bingham parameters for data
    """
    control,X,bpars=[],[],{}
    N=len(data)
    if N <2:
       return bpars
#
#  get cartesian coordinates
#
    for rec in data:
        X.append(dir2cart([rec[0],rec[1],1.]))
#
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
    t,V=tauV(T)
    w1,w2,w3=t[2],t[1],t[0]
    k1,k2=binglookup(w1,w2)
    PDir=cart2dir(V[0])
    EDir=cart2dir(V[1])
    ZDir=cart2dir(V[2])
    if PDir[1] < 0: 
        PDir[0]+=180.
        PDir[1]=-PDir[1]
    PDir[0]=PDir[0]%360. 
    bpars["dec"]=PDir[0]
    bpars["inc"]=PDir[1]
    bpars["Edec"]=EDir[0]
    bpars["Einc"]=EDir[1]
    bpars["Zdec"]=ZDir[0]
    bpars["Zinc"]=ZDir[1]
    bpars["n"]=N
#
#  now for Bingham ellipses.
#
    fac1,fac2=-2*N*(k1)*(w3-w1),-2*N*(k2)*(w3-w2)
    sig31,sig32=numpy.sqrt(1./fac1), numpy.sqrt(1./fac2)
    bpars["Zeta"],bpars["Eta"]=2.45*sig31*180./numpy.pi,2.45*sig32*180./numpy.pi
    return  bpars


def doflip(dec,inc):
   """
   flips lower hemisphere data to upper hemisphere
   """
   if inc <0:
       inc=-inc
       dec=(dec+180.)%360.
   return dec,inc

def doincfish(inc):
    """
    gets fisher mean inc from inc only data
    """
    rad,SCOi,SSOi=numpy.pi/180.,0.,0. # some definitions
    abinc=[]
    for i in inc:abinc.append(abs(i))
    MI,std=gausspars(abinc) # get mean inc and standard deviation
    fpars={}
    N=len(inc)  # number of data
    fpars['n']=N
    fpars['ginc']=MI
    if MI<30:
        fpars['inc']=MI
        fpars['k']=0 
        fpars['alpha95']=0 
        fpars['csd']=0 
        fpars['r']=0 
        print 'WARNING: mean inc < 30, returning gaussian mean'
        return fpars
    for i in inc:  # sum over all incs (but take only positive inc)
        coinc=(90.-abs(i))*rad
        SCOi+= numpy.cos(coinc)
        SSOi+= numpy.sin(coinc)
    Oo=(90.0-MI)*rad # first guess at mean
    SCFlag = -1  # sign change flag
    epsilon = float(N)*numpy.cos(Oo) # RHS of zero equations
    epsilon+= (numpy.sin(Oo)**2-numpy.cos(Oo)**2)*SCOi
    epsilon-= 2.*numpy.sin(Oo)*numpy.cos(Oo)*SSOi
    while SCFlag < 0: # loop until cross zero
        if MI > 0 : Oo-=(.01*rad)  # get steeper
        if MI < 0 : Oo+=(.01*rad)  # get shallower
        prev=epsilon
        epsilon = float(N)*numpy.cos(Oo) # RHS of zero equations
        epsilon+= (numpy.sin(Oo)**2.-numpy.cos(Oo)**2.)*SCOi
        epsilon-= 2.*numpy.sin(Oo)*numpy.cos(Oo)*SSOi
        if abs(epsilon) > abs(prev): MI=-1*MI  # reverse direction
        if epsilon*prev < 0: SCFlag = 1 # changed sign
    S,C=0.,0.  # initialize for summation
    for i in inc:
        coinc=(90.-abs(i))*rad
        S+= numpy.sin(Oo-coinc)
        C+= numpy.cos(Oo-coinc)
    k=(N-1.)/(2.*(N-C))
    Imle=90.-(Oo/rad)
    fpars["inc"]=Imle
    fpars["r"],R=2.*C-N,2*C-N
    fpars["k"]=k
    f=fcalc(2,N-1)
    a95= 1. - (0.5)*(S/C)**2 - (f/(2.*C*k))
#    b=20.**(1./(N-1.)) -1.
#    a=1.-b*(N-R)/R
#    a95=numpy.arccos(a)*180./numpy.pi
    csd=81./numpy.sqrt(k)
    fpars["alpha95"]=a95
    fpars["csd"]=csd
    return fpars

def dokent(data,NN):
    """
    gets Kent  parameters for data
    """
    X,kpars=[],{}
    N=len(data)
    if N <2:
       return kpars
#
#  get fisher mean and convert to co-inclination (theta)/dec (phi) in radians
#
    fpars=fisher_mean(data)
    pbar=fpars["dec"]*numpy.pi/180.
    tbar=(90.-fpars["inc"])*numpy.pi/180.
#
#   initialize matrices
#
    H=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    w=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    b=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    gam=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
    xg=[]
#
#  set up rotation matrix H
#
    H=[ [numpy.cos(tbar)*numpy.cos(pbar),-numpy.sin(pbar),numpy.sin(tbar)*numpy.cos(pbar)],[numpy.cos(tbar)*numpy.sin(pbar),numpy.cos(pbar),numpy.sin(pbar)*numpy.sin(tbar)],[-numpy.sin(tbar),0.,numpy.cos(tbar)]]
#
#  get cartesian coordinates of data
#
    for rec in data:
        X.append(dir2cart([rec[0],rec[1],1.]))
#
#   put in T matrix
#
    T=Tmatrix(X)
    for i in range(3):
        for j in range(3):
            T[i][j]=T[i][j]/float(N)
#
# compute B=H'TH
#
    for i in range(3):
        for j in range(3):
            for k in range(3):
                w[i][j]+=T[i][k]*H[k][j]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                b[i][j]+=H[k][i]*w[k][j]
#
# choose a rotation w about North pole to diagonalize upper part of B
#
    psi = 0.5*numpy.arctan(2.*b[0][1]/(b[0][0]-b[1][1]))
    w=[[numpy.cos(psi),-numpy.sin(psi),0],[numpy.sin(psi),numpy.cos(psi),0],[0.,0.,1.]]
    for i in range(3):
        for j in range(3):
            gamtmp=0.
            for k in range(3):
                gamtmp+=H[i][k]*w[k][j]      
            gam[i][j]=gamtmp
    for i in range(N):
        xg.append([0.,0.,0.])
        for k in range(3):  
            xgtmp=0.
            for j in range(3):
                xgtmp+=gam[j][k]*X[i][j]
            xg[i][k]=xgtmp
# compute asymptotic ellipse parameters
#
    xmu,sigma1,sigma2=0.,0.,0.
    for  i in range(N):
        xmu+= xg[i][2]
        sigma1=sigma1+xg[i][1]**2
        sigma2=sigma2+xg[i][0]**2
    xmu=xmu/float(N)
    sigma1=sigma1/float(N)
    sigma2=sigma2/float(N)
    g=-2.0*numpy.log(0.05)/(float(NN)*xmu**2)
    if numpy.sqrt(sigma1*g)<1:zeta=numpy.arcsin(numpy.sqrt(sigma1*g))
    if numpy.sqrt(sigma2*g)<1:eta=numpy.arcsin(numpy.sqrt(sigma2*g))
    if numpy.sqrt(sigma1*g)>=1.:zeta=numpy.pi/2.
    if numpy.sqrt(sigma2*g)>=1.:eta=numpy.pi/2.
#
#  convert Kent parameters to directions,angles
#
    kpars["dec"]=fpars["dec"]
    kpars["inc"]=fpars["inc"]
    kpars["n"]=NN
    ZDir=cart2dir([gam[0][1],gam[1][1],gam[2][1]])
    EDir=cart2dir([gam[0][0],gam[1][0],gam[2][0]])
    kpars["Zdec"]=ZDir[0]
    kpars["Zinc"]=ZDir[1]
    kpars["Edec"]=EDir[0]
    kpars["Einc"]=EDir[1]
    if kpars["Zinc"]<0:
        kpars["Zinc"]=-kpars["Zinc"]
        kpars["Zdec"]=(kpars["Zdec"]+180.)%360.
    if kpars["Einc"]<0:
        kpars["Einc"]=-kpars["Einc"]
        kpars["Edec"]=(kpars["Edec"]+180.)%360.
    kpars["Zeta"]=zeta*180./numpy.pi
    kpars["Eta"]=eta*180./numpy.pi
    return kpars


def doprinc(data):
    """
    gets principal components from data
    """
    ppars={}
    rad=numpy.pi/180.
    X=dir2cart(data)
    #for rec in data:
    #    dir=[]
    #    for c in rec: dir.append(c)
    #    cart= (dir2cart(dir))
    #    X.append(cart)
#   put in T matrix
#
    T=numpy.array(Tmatrix(X))
#
#   get sorted evals/evects
#
    t,V=tauV(T)
    Pdir=cart2dir(V[0])
    ppars['Edir']=cart2dir(V[1]) # elongation direction
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['dec']=dec
    ppars['inc']=inc
    ppars['N']=len(data)
    ppars['tau1']=t[0]
    ppars['tau2']=t[1]
    ppars['tau3']=t[2]
    Pdir=cart2dir(V[1])
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['V2dec']=dec
    ppars['V2inc']=inc
    Pdir=cart2dir(V[2])
    dec,inc=doflip(Pdir[0],Pdir[1])
    ppars['V3dec']=dec
    ppars['V3inc']=inc
    return ppars


def PTrot(EP,Lats,Lons):
    """ Does rotation of points on a globe  by finite rotations, using method of Cox and Hart 1986, box 7-3. """
# gets user input of Rotation pole lat,long, omega for plate and converts to radians
    E=dir2cart([EP[1],EP[0],1.])
    omega=EP[2]*numpy.pi/180.
    RLats,RLons=[],[]
    for k in range(len(Lats)):
      if Lats[k]<=90.: # peel off delimiters
# converts to rotation pole to cartesian coordinates
        A=dir2cart([Lons[k],Lats[k],1.])
# defines cartesian coordinates of the pole A
        R=[[0.,0.,0.],[0.,0.,0.],[0.,0.,0.]]
        R[0][0]=E[0]*E[0]*(1-numpy.cos(omega)) + numpy.cos(omega)
        R[0][1]=E[0]*E[1]*(1-numpy.cos(omega)) - E[2]*numpy.sin(omega)
        R[0][2]=E[0]*E[2]*(1-numpy.cos(omega)) + E[1]*numpy.sin(omega)
        R[1][0]=E[1]*E[0]*(1-numpy.cos(omega)) + E[2]*numpy.sin(omega)
        R[1][1]=E[1]*E[1]*(1-numpy.cos(omega)) + numpy.cos(omega)
        R[1][2]=E[1]*E[2]*(1-numpy.cos(omega)) - E[0]*numpy.sin(omega)
        R[2][0]=E[2]*E[0]*(1-numpy.cos(omega)) - E[1]*numpy.sin(omega)
        R[2][1]=E[2]*E[1]*(1-numpy.cos(omega)) + E[0]*numpy.sin(omega)
        R[2][2]=E[2]*E[2]*(1-numpy.cos(omega)) + numpy.cos(omega)
# sets up rotation matrix
        Ap=[0,0,0]
        for i in range(3):
            for j in range(3):
                Ap[i]+=R[i][j]*A[j]
# does the rotation
        Prot=cart2dir(Ap)
        RLats.append(Prot[1])
        RLons.append(Prot[0])
      else:  # preserve delimiters
        RLats.append(Lats[k])
        RLons.append(Lons[k])
    return RLats,RLons

def dread(infile,cols):
    """
     reads in specimen, tr, dec, inc int into data[].  position of
     tr, dec, inc, int determined by cols[]
    """
    data=[]
    f=open(infile,"rU")
    for line in f.readlines():
        tmp=line.split()
        rec=(tmp[0],float(tmp[cols[0]]),float(tmp[cols[1]]),float(tmp[cols[2]]),
          float(tmp[cols[3]]) )
        data.append(rec)
    return data

def fshdev(k):
    """
     returns a direction from distribution with TM=0,90 and kappa of k
    """
    R1=random.random()
    R2=random.random()
    L=numpy.exp(-2*k)
    a=R1*(1-L)+L
    fac=numpy.sqrt((-numpy.log(a))/(2*k))
    inc=90.-2*numpy.arcsin(fac)*180./numpy.pi
    dec=2*numpy.pi*R2*180./numpy.pi
    return dec,inc

def lowes(infile,outfile):
    """
    gets Lowe's power spectrum from infile - writes to ofile
    """  
    ll=1
    pow=0
    f=open(infile,'rU')
    o=open(outfile,'w')
    out=''
    for line in f.xreadlines():
     data=line.split()
     l,m,s=int(data[0]),int(data[1]),1e-3*float(data[2])
     if l == ll:
      pow=pow+s**2
     if l != ll:
      out=out+str(ll)+' '+str((ll+1)*pow) +'\n'
      pow=s**2
      ll=l
    out=out+str(l)+' '+str((l+1)*pow) +'\n'
    o.write(out)

def magnetic_lat(inc):
    """
    returns magnetic latitude from inclination
    """
    rad=numpy.pi/180.
    paleo_lat=numpy.arctan( 0.5*numpy.tan(inc*rad))/rad
    return paleo_lat

def check_F(AniSpec):
    s=numpy.zeros((6),'f')
    sigma=float(AniSpec["anisotropy_sigma"])
    if AniSpec['anisotropy_type']=='AMS':
        nf=int(AniSpec["anisotropy_n"])-6
    else:
        nf=3*int(AniSpec["anisotropy_n"])-6
    s[0]=float(AniSpec["anisotropy_s1"])
    s[1]=float(AniSpec["anisotropy_s2"])
    s[2]=float(AniSpec["anisotropy_s3"])
    s[3]=float(AniSpec["anisotropy_s4"])
    s[4]=float(AniSpec["anisotropy_s5"])
    s[5]=float(AniSpec["anisotropy_s6"])
    chibar=(s[0]+s[1]+s[2])/3.
    tau,Vdir=doseigs(s)
    t2sum=0
    for i in range(3): t2sum+=tau[i]**2
    F=0.4*(t2sum-3*chibar**2)/(sigma**2)
    Fcrit=fcalc(5,nf)
    if F>Fcrit: # anisotropic
        chi=numpy.array([[s[0],s[3],s[5]],[s[3],s[1],s[4]],[s[5],s[4],s[2]]])
        chi_inv=numpy.linalg.inv(chi)
        #trace=chi_inv[0][0]+chi_inv[1][1]+chi_inv[2][2] # don't normalize twice
        #chi_inv=3.*chi_inv/trace
    else: # isotropic
        chi_inv=numpy.array([[1.,0,0],[0,1.,0],[0,0,1.]]) # make anisotropy tensor identity tensor
        chi=chi_inv
    return chi,chi_inv

def Dir_anis_corr(InDir,AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc 'InDir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc
    """
    Dir=numpy.zeros((3),'f')
    Dir[0]=InDir[0]
    Dir[1]=InDir[1]
    Dir[2]=1.
    chi,chi_inv=check_F(AniSpec)
    if chi[0][0]==1.:return Dir # isotropic
    X=dir2cart(Dir)
    M=numpy.array(X)
    H=numpy.dot(M,chi_inv)
    return cart2dir(H)

def doaniscorr(PmagSpecRec,AniSpec):
    """
    takes the 6 element 's' vector and the Dec,Inc, Int 'Dir' data,
    performs simple anisotropy correction. returns corrected Dec, Inc, Int
    """
    AniSpecRec={}
    for key in PmagSpecRec.keys():
        AniSpecRec[key]=PmagSpecRec[key]
    Dir=numpy.zeros((3),'f')
    Dir[0]=float(PmagSpecRec["specimen_dec"])
    Dir[1]=float(PmagSpecRec["specimen_inc"])
    Dir[2]=float(PmagSpecRec["specimen_int"])
# check if F test passes!   
    chi,chi_inv=check_F(AniSpec)
    if chi[0][0]==1.: # isotropic
        cDir=[Dir[0],Dir[1]] # no change
        newint=Dir[2]
    else:
        X=dir2cart(Dir)
        M=numpy.array(X)
        H=numpy.dot(M,chi_inv)
        cDir= cart2dir(H)
        Hunit=[H[0]/cDir[2],H[1]/cDir[2],H[2]/cDir[2]] # unit vector parallel to Banc
        Zunit=[0,0,-1.] # unit vector parallel to lab field
        Hpar=numpy.dot(chi,Hunit) # unit vector applied along ancient field
        Zpar=numpy.dot(chi,Zunit) # unit vector applied along lab field
        HparInt=cart2dir(Hpar)[2] # intensity of resultant vector from ancient field
        ZparInt=cart2dir(Zpar)[2] # intensity of resultant vector from lab field
        newint=Dir[2]*ZparInt/HparInt
        if cDir[0]-Dir[0]>90:
            cDir[1]=-cDir[1]
            cDir[0]=(cDir[0]-180.)%360.
    AniSpecRec["specimen_dec"]='%7.1f'%(cDir[0])
    AniSpecRec["specimen_inc"]='%7.1f'%(cDir[1])
    AniSpecRec["specimen_int"]='%9.4e'%(newint)
    AniSpecRec["specimen_correction"]='c'
    if 'magic_method_codes' in AniSpecRec.keys():
        methcodes=AniSpecRec["magic_method_codes"]
    else:
        methcodes=""
    if methcodes=="": methcodes="DA-AC-"+AniSpec['anisotropy_type']
    if methcodes!="": methcodes=methcodes+":DA-AC-"+AniSpec['anisotropy_type']
    if chi[0][0]==1.: # isotropic 
        AniSpecRec["magic_method_codes"]=methcodes+':DA-AC-ISO' # indicates anisotropy was checked and no change necessary
    return AniSpecRec

def vfunc(pars_1,pars_2):
    """
    returns 2*(Sw-Rw) for Watson's V
    """
    cart_1=dir2cart([pars_1["dec"],pars_1["inc"],pars_1["r"]])
    cart_2=dir2cart([pars_2['dec'],pars_2['inc'],pars_2["r"]])
    Sw=pars_1['k']*pars_1['r']+pars_2['k']*pars_2['r'] # k1*r1+k2*r2
    xhat_1=pars_1['k']*cart_1[0]+pars_2['k']*cart_2[0] # k1*x1+k2*x2
    xhat_2=pars_1['k']*cart_1[1]+pars_2['k']*cart_2[1] # k1*y1+k2*y2
    xhat_3=pars_1['k']*cart_1[2]+pars_2['k']*cart_2[2] # k1*z1+k2*z2
    Rw=numpy.sqrt(xhat_1**2+xhat_2**2+xhat_3**2)
    return 2*(Sw-Rw)

def vgp_di(plat,plong,slat,slong):
    """
    returns direction for a given observation site from a Virtual geomagnetic pole
    """
    rad,signdec=numpy.pi/180.,1.
    delphi=abs(plong-slong)
    if delphi!=0:signdec=(plong-slong)/delphi
    if slat==90.:slat=89.99
    thetaS=(90.-slat)*rad
    thetaP=(90.-plat)*rad
    delphi=delphi*rad
    cosp=numpy.cos(thetaS)*numpy.cos(thetaP)+numpy.sin(thetaS)*numpy.sin(thetaP)*numpy.cos(delphi)
    thetaM=numpy.arccos(cosp)
    cosd=(numpy.cos(thetaP)-numpy.cos(thetaM)*numpy.cos(thetaS))/(numpy.sin(thetaM)*numpy.sin(thetaS))
    C=abs(1.-cosd**2)
    if C!=0:
         dec=-numpy.arctan(cosd/numpy.sqrt(abs(C)))+numpy.pi/2.
    else:  
        dec=numpy.arccos(cosd)
    if -numpy.pi<signdec*delphi and signdec<0: dec=2.*numpy.pi-dec  # checking quadrant 
    if signdec*delphi> numpy.pi: dec=2.*numpy.pi-dec
    dec=(dec/rad)%360.
    inc=(numpy.arctan2(2.*numpy.cos(thetaM),numpy.sin(thetaM)))/rad
    return  dec,inc

def watsonsV(Dir1,Dir2):
    """
    calculates Watson's V statisting for two sets of directions
    """
    counter,NumSims=0,500
#
# first calculate the fisher means and cartesian coordinates of each set of Directions
#
    pars_1=fisher_mean(Dir1)
    pars_2=fisher_mean(Dir2)
#
# get V statistic for these
#
    V=vfunc(pars_1,pars_2)
#
# do monte carlo simulation of datasets with same kappas, but common mean
# 
    Vp=[] # set of Vs from simulations
    print "Doing ",NumSims," simulations"
    for k in range(NumSims):
        counter+=1
        if counter==50:
            print k+1
            counter=0
        Dirp=[]
# get a set of N1 fisher distributed vectors with k1, calculate fisher stats
        for i in range(pars_1["n"]):
            Dirp.append(fshdev(pars_1["k"]))
        pars_p1=fisher_mean(Dirp)
# get a set of N2 fisher distributed vectors with k2, calculate fisher stats
        Dirp=[]
        for i in range(pars_2["n"]):
            Dirp.append(fshdev(pars_2["k"]))
        pars_p2=fisher_mean(Dirp)
# get the V for these
        Vk=vfunc(pars_p1,pars_p2)
        Vp.append(Vk)
#
# sort the Vs, get Vcrit (95th one)
#
    Vp.sort()
    k=int(.95*NumSims)
    return V,Vp[k]


def dimap(D,I):
    """
    FUNCTION TO MAP DECLINATION, INCLINATIONS INTO EQUAL AREA PROJECTION, X,Y

    Usage:     dimap(D, I)
    Argin:     Declination (float) and Inclination (float)

    """
### DEFINE FUNCTION VARIABLES
    XY=[0.,0.]                                     # initialize equal area projection x,y

### GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    X=dir2cart([D,I,1.])

### CHECK IF Z = 1 AND ABORT
    if X[2] ==1.0: return XY                       # return [0,0]

### TAKE THE ABSOLUTE VALUE OF Z
    if X[2]<0:X[2]=-X[2]                           # this only works on lower hemisphere projections

### CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    R=numpy.sqrt( 1.-X[2])/(numpy.sqrt(X[0]**2+X[1]**2)) # from Collinson 1983
    XY[1],XY[0]=X[0]*R,X[1]*R

### RETURN XY[X,Y]
    return XY

def dimap_V(D,I):
    """
    FUNCTION TO MAP DECLINATION, INCLINATIONS INTO EQUAL AREA PROJECTION, X,Y

    Usage:     dimap_V(D, I)
        D and I are both numpy arrays

    """
### GET CARTESIAN COMPONENTS OF INPUT DIRECTION
    DI=numpy.array([D,I]).transpose() # 
    X=dir2cart(DI).transpose()
### CALCULATE THE X,Y COORDINATES FOR THE EQUAL AREA PROJECTION
    R=numpy.sqrt( 1.-abs(X[2]))/(numpy.sqrt(X[0]**2+X[1]**2)) # from Collinson 1983
    XY=numpy.array([X[1]*R,X[0]*R]).transpose()

### RETURN XY[X,Y]
    return XY

def getmeths(method_type):
    """
    returns MagIC  method codes available  for a given type
    """
    meths=[]
    if method_type=='GM':
        meths.append('GM-PMAG-APWP')
        meths.append('GM-ARAR')
        meths.append('GM-ARAR-AP')
        meths.append('GM-ARAR-II')
        meths.append('GM-ARAR-NI')
        meths.append('GM-ARAR-TF')
        meths.append('GM-CC-ARCH')
        meths.append('GM-CC-ARCHMAG')
        meths.append('GM-C14')
        meths.append('GM-FOSSIL')
        meths.append('GM-FT')
        meths.append('GM-INT-L')
        meths.append('GM-INT-S')
        meths.append('GM-ISO')
        meths.append('GM-KAR')
        meths.append('GM-PMAG-ANOM')
        meths.append('GM-PMAG-POL')
        meths.append('GM-PBPB')
        meths.append('GM-RATH')
        meths.append('GM-RBSR')
        meths.append('GM-RBSR-I')
        meths.append('GM-RBSR-MA')
        meths.append('GM-SMND')
        meths.append('GM-SMND-I')
        meths.append('GM-SMND-MA')
        meths.append('GM-CC-STRAT')
        meths.append('GM-LUM-TH')
        meths.append('GM-UPA')
        meths.append('GM-UPB')
        meths.append('GM-UTH')
        meths.append('GM-UTHHE')
    else: pass 
    return meths

def first_up(ofile,Rec,file_type): 
    """
    writes the header for a MagIC template file
    """
    keylist=[]
    pmag_out=open(ofile,'a')
    outstring="tab \t"+file_type+"\n"
    pmag_out.write(outstring)
    keystring=""
    for key in Rec.keys():
        keystring=keystring+'\t'+key
        keylist.append(key)
    keystring=keystring + '\n'
    pmag_out.write(keystring[1:])
    pmag_out.close()
    return keylist

def average_int(data,keybase,outkey): # returns dictionary with average intensities from list of arbitrary dictinaries.
    Ints,DataRec=[],{}
    for r in data:Ints.append(float(r[keybase+'_int']))
    if len(Ints)>1:
        b,sig=gausspars(Ints)
        sigperc=100.*sig/b
        DataRec[outkey+"_int_sigma"]='%8.3e '% (sig)
        DataRec[outkey+"_int_sigma_perc"]='%5.1f '%(sigperc)
    else: # if only one, just copy over specimen data
        b=Ints[0]
        DataRec[outkey+"_int_sigma"]=''
        DataRec[outkey+"_int_sigma_perc"]=''
    DataRec[outkey+"_int"]='%8.3e '%(b)
    DataRec[outkey+"_int_n"]='%i '% (len(data))
    return DataRec
 
def get_age(Rec,sitekey,keybase,Ages,DefaultAge):
    """
    finds the age record for a given site
    """
    site=Rec[sitekey]
    gotone=0
    if len(Ages)>1:
        for agerec in Ages:
            if agerec["er_site_name"]==site:
                if "age" in agerec.keys() and agerec["age"]!="":
                    Rec[keybase+"age"]=agerec["age"]
                    gotone=1
                if "age_unit" in agerec.keys(): Rec[keybase+"age_unit"]=agerec["age_unit"]
                if "age_sigma" in agerec.keys(): Rec[keybase+"age_sigma"]=agerec["age_sigma"]
    if gotone==0 and len(DefaultAge)>1:
        sigma=0.5*(float(DefaultAge[1])-float(DefaultAge[0]))
        age=float(DefaultAge[0])+sigma
        Rec[keybase+"age"]= '%10.4e'%(age)
        Rec[keybase+"age_sigma"]= '%10.4e'%(sigma)
        Rec[keybase+"age_unit"]=DefaultAge[2]
    return Rec
#
def adjust_ages(AgesIn):
    """
    Function to adjust ages to a common age_unit
    """
# get a list of age_units first
    age_units,AgesOut,factors,factor,maxunit,age_unit=[],[],[],1,1,"Ma"
    for agerec in AgesIn:
        if agerec[1] not in age_units:
            age_units.append(agerec[1])
            if agerec[1]=="Ga":
                factors.append(1e9)
                maxunit,age_unit,factor=1e9,"Ga",1e9
            if agerec[1]=="Ma":
                if maxunit==1:maxunit,age_unt,factor=1e6,"Ma",1e6
                factors.append(1e6)
            if agerec[1]=="Ka":
                factors.append(1e3)
                if maxunit==1:maxunit,age_unit,factor=1e3,"Ka",1e3
            if "Years" in agerec[1].split():factors.append(1)
    if len(age_units)==1: # all ages are of same type
        for agerec in AgesIn: 
            AgesOut.append(agerec[0])
    elif len(age_units)>1:
        for agerec in AgesIn:  # normalize all to largest age unit
            if agerec[1]=="Ga":AgesOut.append(agerec[0]*1e9/factor)
            if agerec[1]=="Ma":AgesOut.append(agerec[0]*1e6/factor)
            if agerec[1]=="Ka":AgesOut.append(agerec[0]*1e3/factor)
            if "Years" in agerec[1].split():
                if agerec[1]=="Years BP":AgesOut.append(agerec[0]/factor)
                if agerec[1]=="Years Cal BP":AgesOut.append(agerec[0]/factor)
                if agerec[1]=="Years AD (+/-)":AgesOut.append((1950-agerec[0])/factor) # convert to years BP first
                if agerec[1]=="Years Cal AD (+/-)":AgesOut.append((1950-agerec[0])/factor)
    return AgesOut,age_unit
#
def gaussdev(mean,sigma):
    """
    returns a number drawn from a gaussian distribution with given mean, sigma
    """
    return random.normal(mean,sigma) # return gaussian deviate
#
def get_unf(N):
#
# subroutine to retrieve N uniformly distributed directions
# using Fisher et al. (1987) way.
#
# get uniform direcctions (x,y,z)
    z=random.uniform(-1.,1.,size=N)
    t=random.uniform(0.,360.,size=N)
    i=numpy.arcsin(z)*180./numpy.pi
    return numpy.array([t,i]).transpose()

#def get_unf(N): #Jeff's way
#    """
#     subroutine to retrieve N uniformly distributed directions
#    """
#    nmax,k=5550,66   # initialize stuff for uniform distribution
#    di,xn,yn,zn=[],[],[],[]
##
## get uniform direcctions (x,y,z)
#    for  i in range(1,k):
#        m = int(2*float(k)*numpy.sin(numpy.pi*float(i)/float(k)))
#        for j in range(m):
#            x=numpy.sin(numpy.pi*float(i)/float(k))*numpy.cos(2.*numpy.pi*float(j)/float(m))
#            y=numpy.sin(numpy.pi*float(i)/float(k))*numpy.sin(2.*numpy.pi*float(j)/float(m))
#            z=numpy.cos(numpy.pi*float(i)/float(k))
#            r=numpy.sqrt(x**2+y**2+z**2)
#            xn.append(x/r)      
#            yn.append(y/r)       
#            zn.append(z/r) 
##
## select N random phi/theta from unf dist.
#
#    while len(di)<N:
#        ind=random.randint(0,len(xn)-1)
#        dir=cart2dir((xn[ind],yn[ind],zn[ind]))
#        di.append([dir[0],dir[1]])
#    return di 
##
def s2a(s):
    """
     convert 6 element "s" list to 3,3 a matrix (see Tauxe 1998)
    """
    a=numpy.zeros((3,3,),'f') # make the a matrix
    for i in range(3):
        a[i][i]=s[i]
    a[0][1],a[1][0]=s[3],s[3]
    a[1][2],a[2][1]=s[4],s[4]
    a[0][2],a[2][0]=s[5],s[5]
    return a
#
def a2s(a):
    """
     convert 3,3 a matrix to 6 element "s" list  (see Tauxe 1998)
    """
    s=numpy.zeros((6,),'f') # make the a matrix
    for i in range(3):
        s[i]=a[i][i]
    s[3]=a[0][1]
    s[4]=a[1][2]
    s[5]=a[0][2]
    return s

def doseigs(s):
    """
    convert s format for eigenvalues and eigenvectors
    """
#
    A=s2a(s) # convert s to a (see Tauxe 1998)
    tau,V=tauV(A) # convert to eigenvalues (t), eigenvectors (V)
    Vdirs=[]
    for v in V: # convert from cartesian to direction
        Vdir= cart2dir(v)
        if Vdir[1]<0:
            Vdir[1]=-Vdir[1]
            Vdir[0]=(Vdir[0]+180.)%360.
        Vdirs.append([Vdir[0],Vdir[1]])
    return tau,Vdirs
#
#
def doeigs_s(tau,Vdirs):
    """
     get elements of s from eigenvaulues - note that this is very unstable
    """
#
    V=[]
    t=numpy.zeros((3,3,),'f') # initialize the tau diagonal matrix
    for j in range(3): t[j][j]=tau[j] # diagonalize tau
    for k in range(3):
        V.append(dir2cart([Vdirs[k][0],Vdirs[k][1],1.0]))
    V=numpy.transpose(V)
    tmp=numpy.dot(V,t)
    chi=numpy.dot(tmp,numpy.transpose(V))
    return a2s(chi)
#
#
def fcalc(col,row):
    """
  looks up f from ftables F(row,col), where row is number of degrees of freedom - this is 95% confidence (p=0.05)
    """
#
    ftest=numpy.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
[1, 161.469, 199.493, 215.737, 224.5, 230.066, 234.001, 236.772, 238.949, 240.496, 241.838, 242.968, 243.88, 244.798, 245.26, 245.956, 246.422, 246.89, 247.36, 247.596, 248.068],
[2, 18.5128, 18.9995, 19.1642, 19.2467, 19.2969, 19.3299, 19.3536, 19.371, 19.3852, 19.3963, 19.4043, 19.4122, 19.4186, 19.425, 19.4297, 19.4329, 19.4377, 19.4409, 19.4425, 19.4457],
[3, 10.1278, 9.5522, 9.2767, 9.1173, 9.0133, 8.9408, 8.8868, 8.8452, 8.8124, 8.7857, 8.7635, 8.7446, 8.7287, 8.715, 8.7028, 8.6923, 8.683, 8.6745, 8.667, 8.6602],
[4, 7.7087, 6.9444, 6.5915, 6.3882, 6.2561, 6.1631, 6.0943, 6.0411, 5.9988, 5.9644, 5.9359, 5.9117, 5.8912, 5.8733, 5.8578, 5.844, 5.8319, 5.8211, 5.8113, 5.8025],
[5, 6.608, 5.7861, 5.4095, 5.1922, 5.0503, 4.9503, 4.8759, 4.8184, 4.7725, 4.735, 4.7039, 4.6777, 4.6552, 4.6358, 4.6187, 4.6038, 4.5904, 4.5785, 4.5679, 4.5581],
[6, 5.9874, 5.1433, 4.757, 4.5337, 4.3874, 4.2838, 4.2067, 4.1468, 4.099, 4.06, 4.0275, 3.9999, 3.9764, 3.956, 3.9381, 3.9223, 3.9083, 3.8957, 3.8844, 3.8742],
[7, 5.5914, 4.7374, 4.3469, 4.1204, 3.9715, 3.866, 3.787, 3.7257, 3.6767, 3.6366, 3.603, 3.5747, 3.5504, 3.5292, 3.5107, 3.4944, 3.4799, 3.4669, 3.4552, 3.4445],
[8, 5.3177, 4.459, 4.0662, 3.8378, 3.6875, 3.5806, 3.5004, 3.4381, 3.3881, 3.3472, 3.313, 3.2839, 3.259, 3.2374, 3.2184, 3.2017, 3.1867, 3.1733, 3.1613, 3.1503],
[9, 5.1174, 4.2565, 3.8626, 3.6331, 3.4817, 3.3738, 3.2928, 3.2296, 3.1789, 3.1373, 3.1025, 3.0729, 3.0475, 3.0255, 3.0061, 2.989, 2.9737, 2.96, 2.9476, 2.9365],
[10, 4.9647, 4.1028, 3.7083, 3.4781, 3.3258, 3.2171, 3.1355, 3.0717, 3.0204, 2.9782, 2.9429, 2.913, 2.8872, 2.8648, 2.845, 2.8276, 2.812, 2.7981, 2.7855, 2.774],
[11, 4.8443, 3.9823, 3.5875, 3.3567, 3.2039, 3.0946, 3.0123, 2.948, 2.8962, 2.8536, 2.8179, 2.7876, 2.7614, 2.7386, 2.7186, 2.7009, 2.6851, 2.6709, 2.6581, 2.6464],
[12, 4.7472, 3.8853, 3.4903, 3.2592, 3.1059, 2.9961, 2.9134, 2.8486, 2.7964, 2.7534, 2.7173, 2.6866, 2.6602, 2.6371, 2.6169, 2.5989, 2.5828, 2.5684, 2.5554, 2.5436],
[13, 4.6672, 3.8055, 3.4106, 3.1791, 3.0255, 2.9153, 2.8321, 2.7669, 2.7144, 2.6711, 2.6347, 2.6037, 2.5769, 2.5536, 2.5331, 2.5149, 2.4987, 2.4841, 2.4709, 2.4589],
[14, 4.6001, 3.7389, 3.3439, 3.1122, 2.9582, 2.8477, 2.7642, 2.6987, 2.6458, 2.6021, 2.5655, 2.5343, 2.5073, 2.4837, 2.463, 2.4446, 2.4282, 2.4134, 2.4, 2.3879],
[15, 4.543, 3.6824, 3.2874, 3.0555, 2.9013, 2.7905, 2.7066, 2.6408, 2.5877, 2.5437, 2.5068, 2.4753, 2.4481, 2.4244, 2.4034, 2.3849, 2.3683, 2.3533, 2.3398, 2.3275],
[16, 4.494, 3.6337, 3.2389, 3.0069, 2.8524, 2.7413, 2.6572, 2.5911, 2.5377, 2.4935, 2.4564, 2.4247, 2.3973, 2.3733, 2.3522, 2.3335, 2.3167, 2.3016, 2.288, 2.2756],
[17, 4.4513, 3.5916, 3.1968, 2.9647, 2.81, 2.6987, 2.6143, 2.548, 2.4943, 2.4499, 2.4126, 2.3807, 2.3531, 2.329, 2.3077, 2.2888, 2.2719, 2.2567, 2.2429, 2.2303],
[18, 4.4139, 3.5546, 3.1599, 2.9278, 2.7729, 2.6613, 2.5767, 2.5102, 2.4563, 2.4117, 2.3742, 2.3421, 2.3143, 2.29, 2.2686, 2.2496, 2.2325, 2.2172, 2.2033, 2.1906],
[19, 4.3808, 3.5219, 3.1274, 2.8951, 2.7401, 2.6283, 2.5435, 2.4768, 2.4227, 2.378, 2.3402, 2.308, 2.28, 2.2556, 2.2341, 2.2149, 2.1977, 2.1823, 2.1683, 2.1555],
[20, 4.3512, 3.4928, 3.0984, 2.8661, 2.7109, 2.599, 2.514, 2.4471, 2.3928, 2.3479, 2.31, 2.2776, 2.2495, 2.2249, 2.2033, 2.184, 2.1667, 2.1511, 2.137, 2.1242],
[21, 4.3248, 3.4668, 3.0725, 2.8401, 2.6848, 2.5727, 2.4876, 2.4205, 2.3661, 2.3209, 2.2829, 2.2504, 2.2222, 2.1975, 2.1757, 2.1563, 2.1389, 2.1232, 2.109, 2.096],
[22, 4.3009, 3.4434, 3.0492, 2.8167, 2.6613, 2.5491, 2.4638, 2.3965, 2.3419, 2.2967, 2.2585, 2.2258, 2.1975, 2.1727, 2.1508, 2.1313, 2.1138, 2.098, 2.0837, 2.0707],
[23, 4.2794, 3.4221, 3.028, 2.7955, 2.64, 2.5276, 2.4422, 2.3748, 2.3201, 2.2747, 2.2364, 2.2036, 2.1752, 2.1503, 2.1282, 2.1086, 2.091, 2.0751, 2.0608, 2.0476],
[24, 4.2597, 3.4029, 3.0088, 2.7763, 2.6206, 2.5082, 2.4226, 2.3551, 2.3003, 2.2547, 2.2163, 2.1834, 2.1548, 2.1298, 2.1077, 2.088, 2.0703, 2.0543, 2.0399, 2.0267],
[25, 4.2417, 3.3852, 2.9913, 2.7587, 2.603, 2.4904, 2.4047, 2.3371, 2.2821, 2.2365, 2.1979, 2.1649, 2.1362, 2.1111, 2.0889, 2.0691, 2.0513, 2.0353, 2.0207, 2.0075],
[26, 4.2252, 3.369, 2.9752, 2.7426, 2.5868, 2.4741, 2.3883, 2.3205, 2.2655, 2.2197, 2.1811, 2.1479, 2.1192, 2.094, 2.0716, 2.0518, 2.0339, 2.0178, 2.0032, 1.9898],
[27, 4.21, 3.3542, 2.9603, 2.7277, 2.5719, 2.4591, 2.3732, 2.3053, 2.2501, 2.2043, 2.1656, 2.1323, 2.1035, 2.0782, 2.0558, 2.0358, 2.0179, 2.0017, 1.987, 1.9736],
[28, 4.196, 3.3404, 2.9467, 2.7141, 2.5581, 2.4453, 2.3592, 2.2913, 2.236, 2.1901, 2.1512, 2.1179, 2.0889, 2.0636, 2.0411, 2.021, 2.0031, 1.9868, 1.972, 1.9586],
[29, 4.1829, 3.3276, 2.9341, 2.7014, 2.5454, 2.4324, 2.3463, 2.2783, 2.2229, 2.1768, 2.1379, 2.1045, 2.0755, 2.05, 2.0275, 2.0074, 1.9893, 1.973, 1.9582, 1.9446],
[30, 4.1709, 3.3158, 2.9223, 2.6896, 2.5335, 2.4205, 2.3343, 2.2662, 2.2107, 2.1646, 2.1255, 2.0921, 2.0629, 2.0374, 2.0148, 1.9946, 1.9765, 1.9601, 1.9452, 1.9317],
[31, 4.1597, 3.3048, 2.9113, 2.6787, 2.5225, 2.4094, 2.3232, 2.2549, 2.1994, 2.1531, 2.1141, 2.0805, 2.0513, 2.0257, 2.003, 1.9828, 1.9646, 1.9481, 1.9332, 1.9196],
[32, 4.1491, 3.2945, 2.9011, 2.6684, 2.5123, 2.3991, 2.3127, 2.2444, 2.1888, 2.1425, 2.1033, 2.0697, 2.0404, 2.0147, 1.992, 1.9717, 1.9534, 1.9369, 1.9219, 1.9083],
[33, 4.1392, 3.2849, 2.8915, 2.6589, 2.5027, 2.3894, 2.303, 2.2346, 2.1789, 2.1325, 2.0933, 2.0596, 2.0302, 2.0045, 1.9817, 1.9613, 1.943, 1.9264, 1.9114, 1.8977],
[34, 4.13, 3.2759, 2.8826, 2.6499, 2.4936, 2.3803, 2.2938, 2.2253, 2.1696, 2.1231, 2.0838, 2.05, 2.0207, 1.9949, 1.972, 1.9516, 1.9332, 1.9166, 1.9015, 1.8877],
[35, 4.1214, 3.2674, 2.8742, 2.6415, 2.4851, 2.3718, 2.2852, 2.2167, 2.1608, 2.1143, 2.0749, 2.0411, 2.0117, 1.9858, 1.9629, 1.9424, 1.924, 1.9073, 1.8922, 1.8784],
[36, 4.1132, 3.2594, 2.8663, 2.6335, 2.4771, 2.3637, 2.2771, 2.2085, 2.1526, 2.1061, 2.0666, 2.0327, 2.0032, 1.9773, 1.9543, 1.9338, 1.9153, 1.8986, 1.8834, 1.8696],
[37, 4.1055, 3.2519, 2.8588, 2.6261, 2.4696, 2.3562, 2.2695, 2.2008, 2.1449, 2.0982, 2.0587, 2.0248, 1.9952, 1.9692, 1.9462, 1.9256, 1.9071, 1.8904, 1.8752, 1.8613],
[38, 4.0981, 3.2448, 2.8517, 2.619, 2.4625, 2.349, 2.2623, 2.1935, 2.1375, 2.0909, 2.0513, 2.0173, 1.9877, 1.9617, 1.9386, 1.9179, 1.8994, 1.8826, 1.8673, 1.8534],
[39, 4.0913, 3.2381, 2.8451, 2.6123, 2.4558, 2.3422, 2.2555, 2.1867, 2.1306, 2.0839, 2.0442, 2.0102, 1.9805, 1.9545, 1.9313, 1.9107, 1.8921, 1.8752, 1.8599, 1.8459],
[40, 4.0848, 3.2317, 2.8388, 2.606, 2.4495, 2.3359, 2.249, 2.1802, 2.124, 2.0773, 2.0376, 2.0035, 1.9738, 1.9476, 1.9245, 1.9038, 1.8851, 1.8682, 1.8529, 1.8389],
[41, 4.0786, 3.2257, 2.8328, 2.6, 2.4434, 2.3298, 2.2429, 2.174, 2.1178, 2.071, 2.0312, 1.9971, 1.9673, 1.9412, 1.9179, 1.8972, 1.8785, 1.8616, 1.8462, 1.8321],
[42, 4.0727, 3.2199, 2.8271, 2.5943, 2.4377, 2.324, 2.2371, 2.1681, 2.1119, 2.065, 2.0252, 1.991, 1.9612, 1.935, 1.9118, 1.8909, 1.8722, 1.8553, 1.8399, 1.8258],
[43, 4.067, 3.2145, 2.8216, 2.5888, 2.4322, 2.3185, 2.2315, 2.1625, 2.1062, 2.0593, 2.0195, 1.9852, 1.9554, 1.9292, 1.9059, 1.885, 1.8663, 1.8493, 1.8338, 1.8197],
[44, 4.0617, 3.2093, 2.8165, 2.5837, 2.4271, 2.3133, 2.2262, 2.1572, 2.1009, 2.0539, 2.014, 1.9797, 1.9499, 1.9236, 1.9002, 1.8794, 1.8606, 1.8436, 1.8281, 1.8139],
[45, 4.0566, 3.2043, 2.8115, 2.5787, 2.4221, 2.3083, 2.2212, 2.1521, 2.0958, 2.0487, 2.0088, 1.9745, 1.9446, 1.9182, 1.8949, 1.874, 1.8551, 1.8381, 1.8226, 1.8084],
[46, 4.0518, 3.1996, 2.8068, 2.574, 2.4174, 2.3035, 2.2164, 2.1473, 2.0909, 2.0438, 2.0039, 1.9695, 1.9395, 1.9132, 1.8898, 1.8688, 1.85, 1.8329, 1.8173, 1.8031],
[47, 4.0471, 3.1951, 2.8024, 2.5695, 2.4128, 2.299, 2.2118, 2.1427, 2.0862, 2.0391, 1.9991, 1.9647, 1.9347, 1.9083, 1.8849, 1.8639, 1.845, 1.8279, 1.8123, 1.798],
[48, 4.0426, 3.1907, 2.7981, 2.5653, 2.4085, 2.2946, 2.2074, 2.1382, 2.0817, 2.0346, 1.9946, 1.9601, 1.9301, 1.9037, 1.8802, 1.8592, 1.8402, 1.8231, 1.8075, 1.7932],
[49, 4.0384, 3.1866, 2.7939, 2.5611, 2.4044, 2.2904, 2.2032, 2.134, 2.0774, 2.0303, 1.9902, 1.9558, 1.9257, 1.8992, 1.8757, 1.8547, 1.8357, 1.8185, 1.8029, 1.7886],
[50, 4.0343, 3.1826, 2.79, 2.5572, 2.4004, 2.2864, 2.1992, 2.1299, 2.0734, 2.0261, 1.9861, 1.9515, 1.9214, 1.8949, 1.8714, 1.8503, 1.8313, 1.8141, 1.7985, 1.7841],
[51, 4.0303, 3.1788, 2.7862, 2.5534, 2.3966, 2.2826, 2.1953, 2.126, 2.0694, 2.0222, 1.982, 1.9475, 1.9174, 1.8908, 1.8673, 1.8462, 1.8272, 1.8099, 1.7942, 1.7798],
[52, 4.0266, 3.1752, 2.7826, 2.5498, 2.3929, 2.2789, 2.1916, 2.1223, 2.0656, 2.0184, 1.9782, 1.9436, 1.9134, 1.8869, 1.8633, 1.8422, 1.8231, 1.8059, 1.7901, 1.7758],
[53, 4.023, 3.1716, 2.7791, 2.5463, 2.3894, 2.2754, 2.1881, 2.1187, 2.062, 2.0147, 1.9745, 1.9399, 1.9097, 1.8831, 1.8595, 1.8383, 1.8193, 1.802, 1.7862, 1.7718],
[54, 4.0196, 3.1683, 2.7757, 2.5429, 2.3861, 2.272, 2.1846, 2.1152, 2.0585, 2.0112, 1.971, 1.9363, 1.9061, 1.8795, 1.8558, 1.8346, 1.8155, 1.7982, 1.7825, 1.768],
[55, 4.0162, 3.165, 2.7725, 2.5397, 2.3828, 2.2687, 2.1813, 2.1119, 2.0552, 2.0078, 1.9676, 1.9329, 1.9026, 1.876, 1.8523, 1.8311, 1.812, 1.7946, 1.7788, 1.7644],
[56, 4.0129, 3.1618, 2.7694, 2.5366, 2.3797, 2.2656, 2.1781, 2.1087, 2.0519, 2.0045, 1.9642, 1.9296, 1.8993, 1.8726, 1.8489, 1.8276, 1.8085, 1.7912, 1.7753, 1.7608],
[57, 4.0099, 3.1589, 2.7665, 2.5336, 2.3767, 2.2625, 2.1751, 2.1056, 2.0488, 2.0014, 1.9611, 1.9264, 1.896, 1.8693, 1.8456, 1.8244, 1.8052, 1.7878, 1.772, 1.7575],
[58, 4.0069, 3.1559, 2.7635, 2.5307, 2.3738, 2.2596, 2.1721, 2.1026, 2.0458, 1.9983, 1.958, 1.9233, 1.8929, 1.8662, 1.8424, 1.8212, 1.802, 1.7846, 1.7687, 1.7542],
[59, 4.0039, 3.1531, 2.7608, 2.5279, 2.371, 2.2568, 2.1693, 2.0997, 2.0429, 1.9954, 1.9551, 1.9203, 1.8899, 1.8632, 1.8394, 1.8181, 1.7989, 1.7815, 1.7656, 1.751],
[60, 4.0012, 3.1504, 2.7581, 2.5252, 2.3683, 2.254, 2.1665, 2.097, 2.0401, 1.9926, 1.9522, 1.9174, 1.887, 1.8603, 1.8364, 1.8151, 1.7959, 1.7784, 1.7625, 1.748],
[61, 3.9985, 3.1478, 2.7555, 2.5226, 2.3657, 2.2514, 2.1639, 2.0943, 2.0374, 1.9899, 1.9495, 1.9146, 1.8842, 1.8574, 1.8336, 1.8122, 1.793, 1.7755, 1.7596, 1.745],
[62, 3.9959, 3.1453, 2.753, 2.5201, 2.3631, 2.2489, 2.1613, 2.0917, 2.0348, 1.9872, 1.9468, 1.9119, 1.8815, 1.8547, 1.8308, 1.8095, 1.7902, 1.7727, 1.7568, 1.7422],
[63, 3.9934, 3.1428, 2.7506, 2.5176, 2.3607, 2.2464, 2.1588, 2.0892, 2.0322, 1.9847, 1.9442, 1.9093, 1.8789, 1.852, 1.8282, 1.8068, 1.7875, 1.77, 1.754, 1.7394],
[64, 3.9909, 3.1404, 2.7482, 2.5153, 2.3583, 2.244, 2.1564, 2.0868, 2.0298, 1.9822, 1.9417, 1.9068, 1.8763, 1.8495, 1.8256, 1.8042, 1.7849, 1.7673, 1.7514, 1.7368],
[65, 3.9885, 3.1381, 2.7459, 2.513, 2.356, 2.2417, 2.1541, 2.0844, 2.0274, 1.9798, 1.9393, 1.9044, 1.8739, 1.847, 1.8231, 1.8017, 1.7823, 1.7648, 1.7488, 1.7342],
[66, 3.9862, 3.1359, 2.7437, 2.5108, 2.3538, 2.2395, 2.1518, 2.0821, 2.0251, 1.9775, 1.937, 1.902, 1.8715, 1.8446, 1.8207, 1.7992, 1.7799, 1.7623, 1.7463, 1.7316],
[67, 3.9841, 3.1338, 2.7416, 2.5087, 2.3516, 2.2373, 2.1497, 2.0799, 2.0229, 1.9752, 1.9347, 1.8997, 1.8692, 1.8423, 1.8183, 1.7968, 1.7775, 1.7599, 1.7439, 1.7292],
[68, 3.9819, 3.1317, 2.7395, 2.5066, 2.3496, 2.2352, 2.1475, 2.0778, 2.0207, 1.973, 1.9325, 1.8975, 1.867, 1.84, 1.816, 1.7945, 1.7752, 1.7576, 1.7415, 1.7268],
[69, 3.9798, 3.1297, 2.7375, 2.5046, 2.3475, 2.2332, 2.1455, 2.0757, 2.0186, 1.9709, 1.9303, 1.8954, 1.8648, 1.8378, 1.8138, 1.7923, 1.7729, 1.7553, 1.7393, 1.7246],
[70, 3.9778, 3.1277, 2.7355, 2.5027, 2.3456, 2.2312, 2.1435, 2.0737, 2.0166, 1.9689, 1.9283, 1.8932, 1.8627, 1.8357, 1.8117, 1.7902, 1.7707, 1.7531, 1.7371, 1.7223],
[71, 3.9758, 3.1258, 2.7336, 2.5007, 2.3437, 2.2293, 2.1415, 2.0717, 2.0146, 1.9669, 1.9263, 1.8912, 1.8606, 1.8336, 1.8096, 1.7881, 1.7686, 1.751, 1.7349, 1.7202],
[72, 3.9739, 3.1239, 2.7318, 2.4989, 2.3418, 2.2274, 2.1397, 2.0698, 2.0127, 1.9649, 1.9243, 1.8892, 1.8586, 1.8316, 1.8076, 1.786, 1.7666, 1.7489, 1.7328, 1.7181],
[73, 3.9721, 3.1221, 2.73, 2.4971, 2.34, 2.2256, 2.1378, 2.068, 2.0108, 1.9631, 1.9224, 1.8873, 1.8567, 1.8297, 1.8056, 1.784, 1.7646, 1.7469, 1.7308, 1.716],
[74, 3.9703, 3.1204, 2.7283, 2.4954, 2.3383, 2.2238, 2.1361, 2.0662, 2.009, 1.9612, 1.9205, 1.8854, 1.8548, 1.8278, 1.8037, 1.7821, 1.7626, 1.7449, 1.7288, 1.714],
[75, 3.9685, 3.1186, 2.7266, 2.4937, 2.3366, 2.2221, 2.1343, 2.0645, 2.0073, 1.9595, 1.9188, 1.8836, 1.853, 1.8259, 1.8018, 1.7802, 1.7607, 1.7431, 1.7269, 1.7121],
[76, 3.9668, 3.117, 2.7249, 2.4921, 2.3349, 2.2204, 2.1326, 2.0627, 2.0055, 1.9577, 1.917, 1.8819, 1.8512, 1.8241, 1.8, 1.7784, 1.7589, 1.7412, 1.725, 1.7102],
[77, 3.9651, 3.1154, 2.7233, 2.4904, 2.3333, 2.2188, 2.131, 2.0611, 2.0039, 1.956, 1.9153, 1.8801, 1.8494, 1.8223, 1.7982, 1.7766, 1.7571, 1.7394, 1.7232, 1.7084],
[78, 3.9635, 3.1138, 2.7218, 2.4889, 2.3318, 2.2172, 2.1294, 2.0595, 2.0022, 1.9544, 1.9136, 1.8785, 1.8478, 1.8206, 1.7965, 1.7749, 1.7554, 1.7376, 1.7214, 1.7066],
[79, 3.9619, 3.1123, 2.7203, 2.4874, 2.3302, 2.2157, 2.1279, 2.0579, 2.0006, 1.9528, 1.912, 1.8769, 1.8461, 1.819, 1.7948, 1.7732, 1.7537, 1.7359, 1.7197, 1.7048],
[80, 3.9604, 3.1107, 2.7188, 2.4859, 2.3287, 2.2142, 2.1263, 2.0564, 1.9991, 1.9512, 1.9105, 1.8753, 1.8445, 1.8174, 1.7932, 1.7716, 1.752, 1.7342, 1.718, 1.7032],
[81, 3.9589, 3.1093, 2.7173, 2.4845, 2.3273, 2.2127, 2.1248, 2.0549, 1.9976, 1.9497, 1.9089, 1.8737, 1.8429, 1.8158, 1.7916, 1.77, 1.7504, 1.7326, 1.7164, 1.7015],
[82, 3.9574, 3.1079, 2.716, 2.483, 2.3258, 2.2113, 2.1234, 2.0534, 1.9962, 1.9482, 1.9074, 1.8722, 1.8414, 1.8143, 1.7901, 1.7684, 1.7488, 1.731, 1.7148, 1.6999],
[83, 3.956, 3.1065, 2.7146, 2.4817, 2.3245, 2.2099, 2.122, 2.052, 1.9947, 1.9468, 1.906, 1.8707, 1.8399, 1.8127, 1.7886, 1.7669, 1.7473, 1.7295, 1.7132, 1.6983],
[84, 3.9546, 3.1051, 2.7132, 2.4803, 2.3231, 2.2086, 2.1206, 2.0506, 1.9933, 1.9454, 1.9045, 1.8693, 1.8385, 1.8113, 1.7871, 1.7654, 1.7458, 1.728, 1.7117, 1.6968],
[85, 3.9532, 3.1039, 2.7119, 2.479, 2.3218, 2.2072, 2.1193, 2.0493, 1.9919, 1.944, 1.9031, 1.8679, 1.8371, 1.8099, 1.7856, 1.7639, 1.7443, 1.7265, 1.7102, 1.6953],
[86, 3.9519, 3.1026, 2.7106, 2.4777, 2.3205, 2.2059, 2.118, 2.048, 1.9906, 1.9426, 1.9018, 1.8665, 1.8357, 1.8085, 1.7842, 1.7625, 1.7429, 1.725, 1.7088, 1.6938],
[87, 3.9506, 3.1013, 2.7094, 2.4765, 2.3193, 2.2047, 2.1167, 2.0467, 1.9893, 1.9413, 1.9005, 1.8652, 1.8343, 1.8071, 1.7829, 1.7611, 1.7415, 1.7236, 1.7073, 1.6924],
[88, 3.9493, 3.1001, 2.7082, 2.4753, 2.318, 2.2034, 2.1155, 2.0454, 1.9881, 1.94, 1.8992, 1.8639, 1.833, 1.8058, 1.7815, 1.7598, 1.7401, 1.7223, 1.706, 1.691],
[89, 3.9481, 3.0988, 2.707, 2.4741, 2.3169, 2.2022, 2.1143, 2.0442, 1.9868, 1.9388, 1.8979, 1.8626, 1.8317, 1.8045, 1.7802, 1.7584, 1.7388, 1.7209, 1.7046, 1.6896],
[90, 3.9469, 3.0977, 2.7058, 2.4729, 2.3157, 2.2011, 2.1131, 2.043, 1.9856, 1.9376, 1.8967, 1.8613, 1.8305, 1.8032, 1.7789, 1.7571, 1.7375, 1.7196, 1.7033, 1.6883],
[91, 3.9457, 3.0965, 2.7047, 2.4718, 2.3146, 2.1999, 2.1119, 2.0418, 1.9844, 1.9364, 1.8955, 1.8601, 1.8292, 1.802, 1.7777, 1.7559, 1.7362, 1.7183, 1.702, 1.687],
[92, 3.9446, 3.0955, 2.7036, 2.4707, 2.3134, 2.1988, 2.1108, 2.0407, 1.9833, 1.9352, 1.8943, 1.8589, 1.828, 1.8008, 1.7764, 1.7546, 1.735, 1.717, 1.7007, 1.6857],
[93, 3.9435, 3.0944, 2.7025, 2.4696, 2.3123, 2.1977, 2.1097, 2.0395, 1.9821, 1.934, 1.8931, 1.8578, 1.8269, 1.7996, 1.7753, 1.7534, 1.7337, 1.7158, 1.6995, 1.6845],
[94, 3.9423, 3.0933, 2.7014, 2.4685, 2.3113, 2.1966, 2.1086, 2.0385, 1.981, 1.9329, 1.892, 1.8566, 1.8257, 1.7984, 1.7741, 1.7522, 1.7325, 1.7146, 1.6982, 1.6832],
[95, 3.9412, 3.0922, 2.7004, 2.4675, 2.3102, 2.1955, 2.1075, 2.0374, 1.9799, 1.9318, 1.8909, 1.8555, 1.8246, 1.7973, 1.7729, 1.7511, 1.7314, 1.7134, 1.6971, 1.682],
[96, 3.9402, 3.0912, 2.6994, 2.4665, 2.3092, 2.1945, 2.1065, 2.0363, 1.9789, 1.9308, 1.8898, 1.8544, 1.8235, 1.7961, 1.7718, 1.75, 1.7302, 1.7123, 1.6959, 1.6809],
[97, 3.9392, 3.0902, 2.6984, 2.4655, 2.3082, 2.1935, 2.1054, 2.0353, 1.9778, 1.9297, 1.8888, 1.8533, 1.8224, 1.7951, 1.7707, 1.7488, 1.7291, 1.7112, 1.6948, 1.6797],
[98, 3.9381, 3.0892, 2.6974, 2.4645, 2.3072, 2.1925, 2.1044, 2.0343, 1.9768, 1.9287, 1.8877, 1.8523, 1.8213, 1.794, 1.7696, 1.7478, 1.728, 1.71, 1.6936, 1.6786],
[99, 3.9371, 3.0882, 2.6965, 2.4636, 2.3062, 2.1916, 2.1035, 2.0333, 1.9758, 1.9277, 1.8867, 1.8513, 1.8203, 1.7929, 1.7686, 1.7467, 1.7269, 1.709, 1.6926, 1.6775],
[100, 3.9361, 3.0873, 2.6955, 2.4626, 2.3053, 2.1906, 2.1025, 2.0323, 1.9748, 1.9267, 1.8857, 1.8502, 1.8193, 1.7919, 1.7675, 1.7456, 1.7259, 1.7079, 1.6915, 1.6764],
[101, 3.9352, 3.0864, 2.6946, 2.4617, 2.3044, 2.1897, 2.1016, 2.0314, 1.9739, 1.9257, 1.8847, 1.8493, 1.8183, 1.7909, 1.7665, 1.7446, 1.7248, 1.7069, 1.6904, 1.6754],
[102, 3.9342, 3.0854, 2.6937, 2.4608, 2.3035, 2.1888, 2.1007, 2.0304, 1.9729, 1.9248, 1.8838, 1.8483, 1.8173, 1.7899, 1.7655, 1.7436, 1.7238, 1.7058, 1.6894, 1.6744],
[103, 3.9333, 3.0846, 2.6928, 2.4599, 2.3026, 2.1879, 2.0997, 2.0295, 1.972, 1.9238, 1.8828, 1.8474, 1.8163, 1.789, 1.7645, 1.7427, 1.7229, 1.7048, 1.6884, 1.6733],
[104, 3.9325, 3.0837, 2.692, 2.4591, 2.3017, 2.187, 2.0989, 2.0287, 1.9711, 1.9229, 1.8819, 1.8464, 1.8154, 1.788, 1.7636, 1.7417, 1.7219, 1.7039, 1.6874, 1.6723],
[105, 3.9316, 3.0828, 2.6912, 2.4582, 2.3009, 2.1861, 2.098, 2.0278, 1.9702, 1.922, 1.881, 1.8455, 1.8145, 1.7871, 1.7627, 1.7407, 1.7209, 1.7029, 1.6865, 1.6714],
[106, 3.9307, 3.082, 2.6903, 2.4574, 2.3, 2.1853, 2.0971, 2.0269, 1.9694, 1.9212, 1.8801, 1.8446, 1.8136, 1.7862, 1.7618, 1.7398, 1.72, 1.702, 1.6855, 1.6704],
[107, 3.9299, 3.0812, 2.6895, 2.4566, 2.2992, 2.1845, 2.0963, 2.0261, 1.9685, 1.9203, 1.8792, 1.8438, 1.8127, 1.7853, 1.7608, 1.7389, 1.7191, 1.7011, 1.6846, 1.6695],
[108, 3.929, 3.0804, 2.6887, 2.4558, 2.2984, 2.1837, 2.0955, 2.0252, 1.9677, 1.9195, 1.8784, 1.8429, 1.8118, 1.7844, 1.7599, 1.738, 1.7182, 1.7001, 1.6837, 1.6685],
[109, 3.9282, 3.0796, 2.6879, 2.455, 2.2976, 2.1828, 2.0947, 2.0244, 1.9669, 1.9186, 1.8776, 1.8421, 1.811, 1.7835, 1.7591, 1.7371, 1.7173, 1.6992, 1.6828, 1.6676],
[110, 3.9274, 3.0788, 2.6872, 2.4542, 2.2968, 2.1821, 2.0939, 2.0236, 1.9661, 1.9178, 1.8767, 1.8412, 1.8102, 1.7827, 1.7582, 1.7363, 1.7164, 1.6984, 1.6819, 1.6667],
[111, 3.9266, 3.0781, 2.6864, 2.4535, 2.2961, 2.1813, 2.0931, 2.0229, 1.9653, 1.917, 1.8759, 1.8404, 1.8093, 1.7819, 1.7574, 1.7354, 1.7156, 1.6975, 1.681, 1.6659],
[112, 3.9258, 3.0773, 2.6857, 2.4527, 2.2954, 2.1806, 2.0924, 2.0221, 1.9645, 1.9163, 1.8751, 1.8396, 1.8085, 1.7811, 1.7566, 1.7346, 1.7147, 1.6967, 1.6802, 1.665],
[113, 3.9251, 3.0766, 2.6849, 2.452, 2.2946, 2.1798, 2.0916, 2.0213, 1.9637, 1.9155, 1.8744, 1.8388, 1.8077, 1.7803, 1.7558, 1.7338, 1.7139, 1.6958, 1.6793, 1.6642],
[114, 3.9243, 3.0758, 2.6842, 2.4513, 2.2939, 2.1791, 2.0909, 2.0206, 1.963, 1.9147, 1.8736, 1.8381, 1.8069, 1.7795, 1.755, 1.733, 1.7131, 1.695, 1.6785, 1.6633],
[115, 3.9236, 3.0751, 2.6835, 2.4506, 2.2932, 2.1784, 2.0902, 2.0199, 1.9623, 1.914, 1.8729, 1.8373, 1.8062, 1.7787, 1.7542, 1.7322, 1.7123, 1.6942, 1.6777, 1.6625],
[116, 3.9228, 3.0744, 2.6828, 2.4499, 2.2925, 2.1777, 2.0895, 2.0192, 1.9615, 1.9132, 1.8721, 1.8365, 1.8054, 1.7779, 1.7534, 1.7314, 1.7115, 1.6934, 1.6769, 1.6617],
[117, 3.9222, 3.0738, 2.6821, 2.4492, 2.2918, 2.177, 2.0888, 2.0185, 1.9608, 1.9125, 1.8714, 1.8358, 1.8047, 1.7772, 1.7527, 1.7307, 1.7108, 1.6927, 1.6761, 1.6609],
[118, 3.9215, 3.0731, 2.6815, 2.4485, 2.2912, 2.1763, 2.0881, 2.0178, 1.9601, 1.9118, 1.8707, 1.8351, 1.804, 1.7765, 1.752, 1.7299, 1.71, 1.6919, 1.6754, 1.6602],
[119, 3.9208, 3.0724, 2.6808, 2.4479, 2.2905, 2.1757, 2.0874, 2.0171, 1.9594, 1.9111, 1.87, 1.8344, 1.8032, 1.7757, 1.7512, 1.7292, 1.7093, 1.6912, 1.6746, 1.6594],
[120, 3.9202, 3.0718, 2.6802, 2.4472, 2.2899, 2.175, 2.0868, 2.0164, 1.9588, 1.9105, 1.8693, 1.8337, 1.8026, 1.775, 1.7505, 1.7285, 1.7085, 1.6904, 1.6739, 1.6587],
[121, 3.9194, 3.0712, 2.6795, 2.4466, 2.2892, 2.1744, 2.0861, 2.0158, 1.9581, 1.9098, 1.8686, 1.833, 1.8019, 1.7743, 1.7498, 1.7278, 1.7078, 1.6897, 1.6732, 1.6579],
[122, 3.9188, 3.0705, 2.6789, 2.446, 2.2886, 2.1737, 2.0855, 2.0151, 1.9575, 1.9091, 1.868, 1.8324, 1.8012, 1.7736, 1.7491, 1.727, 1.7071, 1.689, 1.6724, 1.6572],
[123, 3.9181, 3.0699, 2.6783, 2.4454, 2.288, 2.1731, 2.0849, 2.0145, 1.9568, 1.9085, 1.8673, 1.8317, 1.8005, 1.773, 1.7484, 1.7264, 1.7064, 1.6883, 1.6717, 1.6565],
[124, 3.9176, 3.0693, 2.6777, 2.4448, 2.2874, 2.1725, 2.0842, 2.0139, 1.9562, 1.9078, 1.8667, 1.831, 1.7999, 1.7723, 1.7478, 1.7257, 1.7058, 1.6876, 1.6711, 1.6558],
[125, 3.9169, 3.0687, 2.6771, 2.4442, 2.2868, 2.1719, 2.0836, 2.0133, 1.9556, 1.9072, 1.866, 1.8304, 1.7992, 1.7717, 1.7471, 1.725, 1.7051, 1.6869, 1.6704, 1.6551],
[126, 3.9163, 3.0681, 2.6765, 2.4436, 2.2862, 2.1713, 2.083, 2.0126, 1.955, 1.9066, 1.8654, 1.8298, 1.7986, 1.771, 1.7464, 1.7244, 1.7044, 1.6863, 1.6697, 1.6544],
[127, 3.9157, 3.0675, 2.6759, 2.443, 2.2856, 2.1707, 2.0824, 2.0121, 1.9544, 1.906, 1.8648, 1.8291, 1.7979, 1.7704, 1.7458, 1.7237, 1.7038, 1.6856, 1.669, 1.6538],
[128, 3.9151, 3.0669, 2.6754, 2.4424, 2.285, 2.1701, 2.0819, 2.0115, 1.9538, 1.9054, 1.8642, 1.8285, 1.7974, 1.7698, 1.7452, 1.7231, 1.7031, 1.685, 1.6684, 1.6531],
[129, 3.9145, 3.0664, 2.6749, 2.4419, 2.2845, 2.1696, 2.0813, 2.0109, 1.9532, 1.9048, 1.8636, 1.828, 1.7967, 1.7692, 1.7446, 1.7225, 1.7025, 1.6843, 1.6677, 1.6525],
[130, 3.914, 3.0659, 2.6743, 2.4414, 2.2839, 2.169, 2.0807, 2.0103, 1.9526, 1.9042, 1.863, 1.8273, 1.7962, 1.7685, 1.744, 1.7219, 1.7019, 1.6837, 1.6671, 1.6519],
[131, 3.9134, 3.0653, 2.6737, 2.4408, 2.2834, 2.1685, 2.0802, 2.0098, 1.9521, 1.9037, 1.8624, 1.8268, 1.7956, 1.768, 1.7434, 1.7213, 1.7013, 1.6831, 1.6665, 1.6513],
[132, 3.9129, 3.0648, 2.6732, 2.4403, 2.2829, 2.168, 2.0796, 2.0092, 1.9515, 1.9031, 1.8619, 1.8262, 1.795, 1.7674, 1.7428, 1.7207, 1.7007, 1.6825, 1.6659, 1.6506],
[133, 3.9123, 3.0642, 2.6727, 2.4398, 2.2823, 2.1674, 2.0791, 2.0087, 1.951, 1.9026, 1.8613, 1.8256, 1.7944, 1.7668, 1.7422, 1.7201, 1.7001, 1.6819, 1.6653, 1.65],
[134, 3.9118, 3.0637, 2.6722, 2.4392, 2.2818, 2.1669, 2.0786, 2.0082, 1.9504, 1.902, 1.8608, 1.8251, 1.7939, 1.7662, 1.7416, 1.7195, 1.6995, 1.6813, 1.6647, 1.6494],
[135, 3.9112, 3.0632, 2.6717, 2.4387, 2.2813, 2.1664, 2.0781, 2.0076, 1.9499, 1.9015, 1.8602, 1.8245, 1.7933, 1.7657, 1.7411, 1.719, 1.6989, 1.6808, 1.6641, 1.6488],
[136, 3.9108, 3.0627, 2.6712, 2.4382, 2.2808, 2.1659, 2.0775, 2.0071, 1.9494, 1.901, 1.8597, 1.824, 1.7928, 1.7651, 1.7405, 1.7184, 1.6984, 1.6802, 1.6635, 1.6483],
[137, 3.9102, 3.0622, 2.6707, 2.4378, 2.2803, 2.1654, 2.077, 2.0066, 1.9488, 1.9004, 1.8592, 1.8235, 1.7922, 1.7646, 1.74, 1.7178, 1.6978, 1.6796, 1.663, 1.6477],
[138, 3.9098, 3.0617, 2.6702, 2.4373, 2.2798, 2.1649, 2.0766, 2.0061, 1.9483, 1.8999, 1.8586, 1.823, 1.7917, 1.7641, 1.7394, 1.7173, 1.6973, 1.6791, 1.6624, 1.6471],
[139, 3.9092, 3.0613, 2.6697, 2.4368, 2.2794, 2.1644, 2.0761, 2.0056, 1.9478, 1.8994, 1.8581, 1.8224, 1.7912, 1.7635, 1.7389, 1.7168, 1.6967, 1.6785, 1.6619, 1.6466],
[140, 3.9087, 3.0608, 2.6692, 2.4363, 2.2789, 2.1639, 2.0756, 2.0051, 1.9473, 1.8989, 1.8576, 1.8219, 1.7907, 1.763, 1.7384, 1.7162, 1.6962, 1.678, 1.6613, 1.646],
[141, 3.9083, 3.0603, 2.6688, 2.4359, 2.2784, 2.1634, 2.0751, 2.0046, 1.9469, 1.8984, 1.8571, 1.8214, 1.7901, 1.7625, 1.7379, 1.7157, 1.6957, 1.6775, 1.6608, 1.6455],
[142, 3.9078, 3.0598, 2.6683, 2.4354, 2.2779, 2.163, 2.0747, 2.0042, 1.9464, 1.8979, 1.8566, 1.8209, 1.7897, 1.762, 1.7374, 1.7152, 1.6952, 1.6769, 1.6603, 1.645],
[143, 3.9073, 3.0594, 2.6679, 2.435, 2.2775, 2.1625, 2.0742, 2.0037, 1.9459, 1.8975, 1.8562, 1.8204, 1.7892, 1.7615, 1.7368, 1.7147, 1.6946, 1.6764, 1.6598, 1.6444],
[144, 3.9068, 3.0589, 2.6675, 2.4345, 2.277, 2.1621, 2.0737, 2.0033, 1.9455, 1.897, 1.8557, 1.82, 1.7887, 1.761, 1.7364, 1.7142, 1.6941, 1.6759, 1.6592, 1.6439],
[145, 3.9064, 3.0585, 2.667, 2.4341, 2.2766, 2.1617, 2.0733, 2.0028, 1.945, 1.8965, 1.8552, 1.8195, 1.7882, 1.7605, 1.7359, 1.7137, 1.6936, 1.6754, 1.6587, 1.6434],
[146, 3.906, 3.0581, 2.6666, 2.4337, 2.2762, 2.1612, 2.0728, 2.0024, 1.9445, 1.8961, 1.8548, 1.819, 1.7877, 1.7601, 1.7354, 1.7132, 1.6932, 1.6749, 1.6582, 1.6429],
[147, 3.9055, 3.0576, 2.6662, 2.4332, 2.2758, 2.1608, 2.0724, 2.0019, 1.9441, 1.8956, 1.8543, 1.8186, 1.7873, 1.7596, 1.7349, 1.7127, 1.6927, 1.6744, 1.6578, 1.6424],
[148, 3.9051, 3.0572, 2.6657, 2.4328, 2.2753, 2.1604, 2.072, 2.0015, 1.9437, 1.8952, 1.8539, 1.8181, 1.7868, 1.7591, 1.7344, 1.7123, 1.6922, 1.6739, 1.6573, 1.6419],
[149, 3.9046, 3.0568, 2.6653, 2.4324, 2.2749, 2.1599, 2.0716, 2.0011, 1.9432, 1.8947, 1.8534, 1.8177, 1.7864, 1.7587, 1.734, 1.7118, 1.6917, 1.6735, 1.6568, 1.6414],
[150, 3.9042, 3.0564, 2.6649, 2.4319, 2.2745, 2.1595, 2.0711, 2.0006, 1.9428, 1.8943, 1.853, 1.8172, 1.7859, 1.7582, 1.7335, 1.7113, 1.6913, 1.673, 1.6563, 1.641],
[151, 3.9038, 3.056, 2.6645, 2.4315, 2.2741, 2.1591, 2.0707, 2.0002, 1.9424, 1.8939, 1.8526, 1.8168, 1.7855, 1.7578, 1.7331, 1.7109, 1.6908, 1.6726, 1.6558, 1.6405],
[152, 3.9033, 3.0555, 2.6641, 2.4312, 2.2737, 2.1587, 2.0703, 1.9998, 1.942, 1.8935, 1.8521, 1.8163, 1.785, 1.7573, 1.7326, 1.7104, 1.6904, 1.6721, 1.6554, 1.64],
[153, 3.903, 3.0552, 2.6637, 2.4308, 2.2733, 2.1583, 2.0699, 1.9994, 1.9416, 1.8931, 1.8517, 1.8159, 1.7846, 1.7569, 1.7322, 1.71, 1.6899, 1.6717, 1.6549, 1.6396],
[154, 3.9026, 3.0548, 2.6634, 2.4304, 2.2729, 2.1579, 2.0695, 1.999, 1.9412, 1.8926, 1.8513, 1.8155, 1.7842, 1.7565, 1.7318, 1.7096, 1.6895, 1.6712, 1.6545, 1.6391],
[155, 3.9021, 3.0544, 2.6629, 2.43, 2.2725, 2.1575, 2.0691, 1.9986, 1.9407, 1.8923, 1.8509, 1.8151, 1.7838, 1.7561, 1.7314, 1.7091, 1.6891, 1.6708, 1.654, 1.6387],
[156, 3.9018, 3.054, 2.6626, 2.4296, 2.2722, 2.1571, 2.0687, 1.9982, 1.9403, 1.8918, 1.8505, 1.8147, 1.7834, 1.7557, 1.7309, 1.7087, 1.6886, 1.6703, 1.6536, 1.6383],
[157, 3.9014, 3.0537, 2.6622, 2.4293, 2.2717, 2.1568, 2.0684, 1.9978, 1.94, 1.8915, 1.8501, 1.8143, 1.7829, 1.7552, 1.7305, 1.7083, 1.6882, 1.6699, 1.6532, 1.6378],
[158, 3.901, 3.0533, 2.6618, 2.4289, 2.2714, 2.1564, 2.068, 1.9974, 1.9396, 1.8911, 1.8497, 1.8139, 1.7826, 1.7548, 1.7301, 1.7079, 1.6878, 1.6695, 1.6528, 1.6374],
[159, 3.9006, 3.0529, 2.6615, 2.4285, 2.271, 2.156, 2.0676, 1.997, 1.9392, 1.8907, 1.8493, 1.8135, 1.7822, 1.7544, 1.7297, 1.7075, 1.6874, 1.6691, 1.6524, 1.637],
[160, 3.9002, 3.0525, 2.6611, 2.4282, 2.2706, 2.1556, 2.0672, 1.9967, 1.9388, 1.8903, 1.8489, 1.8131, 1.7818, 1.754, 1.7293, 1.7071, 1.687, 1.6687, 1.6519, 1.6366],
[161, 3.8998, 3.0522, 2.6607, 2.4278, 2.2703, 2.1553, 2.0669, 1.9963, 1.9385, 1.8899, 1.8485, 1.8127, 1.7814, 1.7537, 1.7289, 1.7067, 1.6866, 1.6683, 1.6515, 1.6361],
[162, 3.8995, 3.0518, 2.6604, 2.4275, 2.27, 2.155, 2.0665, 1.9959, 1.9381, 1.8895, 1.8482, 1.8124, 1.781, 1.7533, 1.7285, 1.7063, 1.6862, 1.6679, 1.6511, 1.6357],
[163, 3.8991, 3.0515, 2.6601, 2.4271, 2.2696, 2.1546, 2.0662, 1.9956, 1.9377, 1.8892, 1.8478, 1.812, 1.7806, 1.7529, 1.7282, 1.7059, 1.6858, 1.6675, 1.6507, 1.6353],
[164, 3.8987, 3.0512, 2.6597, 2.4268, 2.2693, 2.1542, 2.0658, 1.9953, 1.9374, 1.8888, 1.8474, 1.8116, 1.7803, 1.7525, 1.7278, 1.7055, 1.6854, 1.6671, 1.6503, 1.6349],
[165, 3.8985, 3.0508, 2.6594, 2.4264, 2.2689, 2.1539, 2.0655, 1.9949, 1.937, 1.8885, 1.8471, 1.8112, 1.7799, 1.7522, 1.7274, 1.7052, 1.685, 1.6667, 1.6499, 1.6345],
[166, 3.8981, 3.0505, 2.6591, 2.4261, 2.2686, 2.1536, 2.0651, 1.9945, 1.9367, 1.8881, 1.8467, 1.8109, 1.7795, 1.7518, 1.727, 1.7048, 1.6846, 1.6663, 1.6496, 1.6341],
[167, 3.8977, 3.0502, 2.6587, 2.4258, 2.2683, 2.1533, 2.0648, 1.9942, 1.9363, 1.8878, 1.8464, 1.8105, 1.7792, 1.7514, 1.7266, 1.7044, 1.6843, 1.6659, 1.6492, 1.6338],
[168, 3.8974, 3.0498, 2.6584, 2.4254, 2.268, 2.1529, 2.0645, 1.9939, 1.936, 1.8874, 1.846, 1.8102, 1.7788, 1.7511, 1.7263, 1.704, 1.6839, 1.6656, 1.6488, 1.6334],
[169, 3.8971, 3.0495, 2.6581, 2.4251, 2.2676, 2.1526, 2.0641, 1.9936, 1.9357, 1.8871, 1.8457, 1.8099, 1.7785, 1.7507, 1.7259, 1.7037, 1.6835, 1.6652, 1.6484, 1.633],
[170, 3.8967, 3.0492, 2.6578, 2.4248, 2.2673, 2.1523, 2.0638, 1.9932, 1.9353, 1.8868, 1.8454, 1.8095, 1.7781, 1.7504, 1.7256, 1.7033, 1.6832, 1.6648, 1.6481, 1.6326],
[171, 3.8965, 3.0488, 2.6575, 2.4245, 2.267, 2.152, 2.0635, 1.9929, 1.935, 1.8864, 1.845, 1.8092, 1.7778, 1.75, 1.7252, 1.703, 1.6828, 1.6645, 1.6477, 1.6323],
[172, 3.8961, 3.0485, 2.6571, 2.4242, 2.2667, 2.1516, 2.0632, 1.9926, 1.9347, 1.8861, 1.8447, 1.8088, 1.7774, 1.7497, 1.7249, 1.7026, 1.6825, 1.6641, 1.6473, 1.6319],
[173, 3.8958, 3.0482, 2.6568, 2.4239, 2.2664, 2.1513, 2.0628, 1.9923, 1.9343, 1.8858, 1.8443, 1.8085, 1.7771, 1.7493, 1.7246, 1.7023, 1.6821, 1.6638, 1.647, 1.6316],
[174, 3.8954, 3.0479, 2.6566, 2.4236, 2.266, 2.151, 2.0626, 1.9919, 1.934, 1.8855, 1.844, 1.8082, 1.7768, 1.749, 1.7242, 1.7019, 1.6818, 1.6634, 1.6466, 1.6312],
[175, 3.8952, 3.0476, 2.6563, 2.4233, 2.2658, 2.1507, 2.0622, 1.9916, 1.9337, 1.8852, 1.8437, 1.8078, 1.7764, 1.7487, 1.7239, 1.7016, 1.6814, 1.6631, 1.6463, 1.6309],
[176, 3.8948, 3.0473, 2.6559, 2.423, 2.2655, 2.1504, 2.0619, 1.9913, 1.9334, 1.8848, 1.8434, 1.8075, 1.7761, 1.7483, 1.7236, 1.7013, 1.6811, 1.6628, 1.646, 1.6305],
[177, 3.8945, 3.047, 2.6556, 2.4227, 2.2652, 2.1501, 2.0616, 1.991, 1.9331, 1.8845, 1.8431, 1.8072, 1.7758, 1.748, 1.7232, 1.7009, 1.6808, 1.6624, 1.6456, 1.6302],
[178, 3.8943, 3.0467, 2.6554, 2.4224, 2.2649, 2.1498, 2.0613, 1.9907, 1.9328, 1.8842, 1.8428, 1.8069, 1.7755, 1.7477, 1.7229, 1.7006, 1.6805, 1.6621, 1.6453, 1.6298],
[179, 3.8939, 3.0465, 2.6551, 2.4221, 2.2646, 2.1495, 2.0611, 1.9904, 1.9325, 1.8839, 1.8425, 1.8066, 1.7752, 1.7474, 1.7226, 1.7003, 1.6801, 1.6618, 1.645, 1.6295],
[180, 3.8936, 3.0462, 2.6548, 2.4218, 2.2643, 2.1492, 2.0608, 1.9901, 1.9322, 1.8836, 1.8422, 1.8063, 1.7749, 1.7471, 1.7223, 1.7, 1.6798, 1.6614, 1.6446, 1.6292],
[181, 3.8933, 3.0458, 2.6545, 2.4216, 2.264, 2.149, 2.0605, 1.9899, 1.9319, 1.8833, 1.8419, 1.806, 1.7746, 1.7468, 1.7219, 1.6997, 1.6795, 1.6611, 1.6443, 1.6289],
[182, 3.8931, 3.0456, 2.6543, 2.4213, 2.2638, 2.1487, 2.0602, 1.9896, 1.9316, 1.883, 1.8416, 1.8057, 1.7743, 1.7465, 1.7217, 1.6994, 1.6792, 1.6608, 1.644, 1.6286],
[183, 3.8928, 3.0453, 2.654, 2.421, 2.2635, 2.1484, 2.0599, 1.9893, 1.9313, 1.8827, 1.8413, 1.8054, 1.774, 1.7462, 1.7214, 1.6991, 1.6789, 1.6605, 1.6437, 1.6282],
[184, 3.8925, 3.045, 2.6537, 2.4207, 2.2632, 2.1481, 2.0596, 1.989, 1.9311, 1.8825, 1.841, 1.8051, 1.7737, 1.7459, 1.721, 1.6987, 1.6786, 1.6602, 1.6434, 1.6279],
[185, 3.8923, 3.0448, 2.6534, 2.4205, 2.263, 2.1479, 2.0594, 1.9887, 1.9308, 1.8822, 1.8407, 1.8048, 1.7734, 1.7456, 1.7208, 1.6984, 1.6783, 1.6599, 1.643, 1.6276],
[186, 3.892, 3.0445, 2.6531, 2.4202, 2.2627, 2.1476, 2.0591, 1.9885, 1.9305, 1.8819, 1.8404, 1.8045, 1.7731, 1.7453, 1.7205, 1.6981, 1.678, 1.6596, 1.6428, 1.6273],
[187, 3.8917, 3.0442, 2.6529, 2.4199, 2.2624, 2.1473, 2.0588, 1.9882, 1.9302, 1.8816, 1.8401, 1.8042, 1.7728, 1.745, 1.7202, 1.6979, 1.6777, 1.6593, 1.6424, 1.627],
[188, 3.8914, 3.044, 2.6526, 2.4197, 2.2621, 2.1471, 2.0586, 1.9879, 1.9299, 1.8814, 1.8399, 1.804, 1.7725, 1.7447, 1.7199, 1.6976, 1.6774, 1.659, 1.6421, 1.6267],
[189, 3.8912, 3.0437, 2.6524, 2.4195, 2.2619, 2.1468, 2.0583, 1.9877, 1.9297, 1.8811, 1.8396, 1.8037, 1.7722, 1.7444, 1.7196, 1.6973, 1.6771, 1.6587, 1.6418, 1.6264],
[190, 3.8909, 3.0435, 2.6521, 2.4192, 2.2617, 2.1466, 2.0581, 1.9874, 1.9294, 1.8808, 1.8393, 1.8034, 1.772, 1.7441, 1.7193, 1.697, 1.6768, 1.6584, 1.6416, 1.6261],
[191, 3.8906, 3.0432, 2.6519, 2.4189, 2.2614, 2.1463, 2.0578, 1.9871, 1.9292, 1.8805, 1.8391, 1.8032, 1.7717, 1.7439, 1.719, 1.6967, 1.6765, 1.6581, 1.6413, 1.6258],
[192, 3.8903, 3.043, 2.6516, 2.4187, 2.2611, 2.1461, 2.0575, 1.9869, 1.9289, 1.8803, 1.8388, 1.8029, 1.7714, 1.7436, 1.7188, 1.6964, 1.6762, 1.6578, 1.641, 1.6255],
[193, 3.8901, 3.0427, 2.6514, 2.4184, 2.2609, 2.1458, 2.0573, 1.9866, 1.9286, 1.88, 1.8385, 1.8026, 1.7712, 1.7433, 1.7185, 1.6961, 1.6759, 1.6575, 1.6407, 1.6252],
[194, 3.8899, 3.0425, 2.6512, 2.4182, 2.2606, 2.1456, 2.057, 1.9864, 1.9284, 1.8798, 1.8383, 1.8023, 1.7709, 1.7431, 1.7182, 1.6959, 1.6757, 1.6572, 1.6404, 1.6249],
[195, 3.8896, 3.0422, 2.6509, 2.418, 2.2604, 2.1453, 2.0568, 1.9861, 1.9281, 1.8795, 1.838, 1.8021, 1.7706, 1.7428, 1.7179, 1.6956, 1.6754, 1.657, 1.6401, 1.6247],
[196, 3.8893, 3.042, 2.6507, 2.4177, 2.2602, 2.1451, 2.0566, 1.9859, 1.9279, 1.8793, 1.8377, 1.8018, 1.7704, 1.7425, 1.7177, 1.6953, 1.6751, 1.6567, 1.6399, 1.6244],
[197, 3.8891, 3.0418, 2.6504, 2.4175, 2.26, 2.1448, 2.0563, 1.9856, 1.9277, 1.879, 1.8375, 1.8016, 1.7701, 1.7423, 1.7174, 1.6951, 1.6748, 1.6564, 1.6396, 1.6241],
[198, 3.8889, 3.0415, 2.6502, 2.4173, 2.2597, 2.1446, 2.0561, 1.9854, 1.9274, 1.8788, 1.8373, 1.8013, 1.7699, 1.742, 1.7172, 1.6948, 1.6746, 1.6562, 1.6393, 1.6238],
[199, 3.8886, 3.0413, 2.65, 2.417, 2.2595, 2.1444, 2.0558, 1.9852, 1.9272, 1.8785, 1.837, 1.8011, 1.7696, 1.7418, 1.7169, 1.6946, 1.6743, 1.6559, 1.6391, 1.6236],
[200, 3.8883, 3.041, 2.6497, 2.4168, 2.2592, 2.1441, 2.0556, 1.9849, 1.9269, 1.8783, 1.8368, 1.8008, 1.7694, 1.7415, 1.7166, 1.6943, 1.6741, 1.6557, 1.6388, 1.62]])
    return ftest[row][col]

def tcalc(nf,p):
    """
     t-table for nf degrees of freedom (95% confidence)
    """
#
    if p==.05:
        if nf> 2: t= 4.3027
        if nf> 3: t= 3.1824
        if nf> 4: t= 2.7765
        if nf> 5: t= 2.5706
        if nf> 6: t= 2.4469
        if nf> 7: t= 2.3646
        if nf> 8: t= 2.3060
        if nf> 9: t= 2.2622
        if nf> 10: t= 2.2281
        if nf> 11: t= 2.2010
        if nf> 12: t= 2.1788
        if nf> 13: t= 2.1604
        if nf> 14: t= 2.1448
        if nf> 15: t= 2.1315
        if nf> 16: t= 2.1199
        if nf> 17: t= 2.1098
        if nf> 18: t= 2.1009
        if nf> 19: t= 2.0930
        if nf> 20: t= 2.0860
        if nf> 21: t= 2.0796
        if nf> 22: t= 2.0739
        if nf> 23: t= 2.0687
        if nf> 24: t= 2.0639
        if nf> 25: t= 2.0595
        if nf> 26: t= 2.0555
        if nf> 27: t= 2.0518
        if nf> 28: t= 2.0484
        if nf> 29: t= 2.0452
        if nf> 30: t= 2.0423
        if nf> 31: t= 2.0395
        if nf> 32: t= 2.0369
        if nf> 33: t= 2.0345
        if nf> 34: t= 2.0322
        if nf> 35: t= 2.0301
        if nf> 36: t= 2.0281
        if nf> 37: t= 2.0262
        if nf> 38: t= 2.0244
        if nf> 39: t= 2.0227
        if nf> 40: t= 2.0211
        if nf> 41: t= 2.0195
        if nf> 42: t= 2.0181
        if nf> 43: t= 2.0167
        if nf> 44: t= 2.0154
        if nf> 45: t= 2.0141
        if nf> 46: t= 2.0129
        if nf> 47: t= 2.0117
        if nf> 48: t= 2.0106
        if nf> 49: t= 2.0096
        if nf> 50: t= 2.0086
        if nf> 51: t= 2.0076
        if nf> 52: t= 2.0066
        if nf> 53: t= 2.0057
        if nf> 54: t= 2.0049
        if nf> 55: t= 2.0040
        if nf> 56: t= 2.0032
        if nf> 57: t= 2.0025
        if nf> 58: t= 2.0017
        if nf> 59: t= 2.0010
        if nf> 60: t= 2.0003
        if nf> 61: t= 1.9996
        if nf> 62: t= 1.9990
        if nf> 63: t= 1.9983
        if nf> 64: t= 1.9977
        if nf> 65: t= 1.9971
        if nf> 66: t= 1.9966
        if nf> 67: t= 1.9960
        if nf> 68: t= 1.9955
        if nf> 69: t= 1.9949
        if nf> 70: t= 1.9944
        if nf> 71: t= 1.9939
        if nf> 72: t= 1.9935
        if nf> 73: t= 1.9930
        if nf> 74: t= 1.9925
        if nf> 75: t= 1.9921
        if nf> 76: t= 1.9917
        if nf> 77: t= 1.9913
        if nf> 78: t= 1.9908
        if nf> 79: t= 1.9905
        if nf> 80: t= 1.9901
        if nf> 81: t= 1.9897
        if nf> 82: t= 1.9893
        if nf> 83: t= 1.9890
        if nf> 84: t= 1.9886
        if nf> 85: t= 1.9883
        if nf> 86: t= 1.9879
        if nf> 87: t= 1.9876
        if nf> 88: t= 1.9873
        if nf> 89: t= 1.9870
        if nf> 90: t= 1.9867
        if nf> 91: t= 1.9864
        if nf> 92: t= 1.9861
        if nf> 93: t= 1.9858
        if nf> 94: t= 1.9855
        if nf> 95: t= 1.9852
        if nf> 96: t= 1.9850
        if nf> 97: t= 1.9847
        if nf> 98: t= 1.9845
        if nf> 99: t= 1.9842
        if nf> 100: t= 1.9840
        return t
#
    elif p==.01:
        if nf> 2: t= 9.9250
        if nf> 3: t= 5.8408
        if nf> 4: t= 4.6041
        if nf> 5: t= 4.0321
        if nf> 6: t= 3.7074
        if nf> 7: t= 3.4995
        if nf> 8: t= 3.3554
        if nf> 9: t= 3.2498
        if nf> 10: t= 3.1693
        if nf> 11: t= 3.1058
        if nf> 12: t= 3.0545
        if nf> 13: t= 3.0123
        if nf> 14: t= 2.9768
        if nf> 15: t= 2.9467
        if nf> 16: t= 2.9208
        if nf> 17: t= 2.8982
        if nf> 18: t= 2.8784
        if nf> 19: t= 2.8609
        if nf> 20: t= 2.8453
        if nf> 21: t= 2.8314
        if nf> 22: t= 2.8188
        if nf> 23: t= 2.8073
        if nf> 24: t= 2.7970
        if nf> 25: t= 2.7874
        if nf> 26: t= 2.7787
        if nf> 27: t= 2.7707
        if nf> 28: t= 2.7633
        if nf> 29: t= 2.7564
        if nf> 30: t= 2.7500
        if nf> 31: t= 2.7440
        if nf> 32: t= 2.7385
        if nf> 33: t= 2.7333
        if nf> 34: t= 2.7284
        if nf> 35: t= 2.7238
        if nf> 36: t= 2.7195
        if nf> 37: t= 2.7154
        if nf> 38: t= 2.7116
        if nf> 39: t= 2.7079
        if nf> 40: t= 2.7045
        if nf> 41: t= 2.7012
        if nf> 42: t= 2.6981
        if nf> 43: t= 2.6951
        if nf> 44: t= 2.6923
        if nf> 45: t= 2.6896
        if nf> 46: t= 2.6870
        if nf> 47: t= 2.6846
        if nf> 48: t= 2.6822
        if nf> 49: t= 2.6800
        if nf> 50: t= 2.6778
        if nf> 51: t= 2.6757
        if nf> 52: t= 2.6737
        if nf> 53: t= 2.6718
        if nf> 54: t= 2.6700
        if nf> 55: t= 2.6682
        if nf> 56: t= 2.6665
        if nf> 57: t= 2.6649
        if nf> 58: t= 2.6633
        if nf> 59: t= 2.6618
        if nf> 60: t= 2.6603
        if nf> 61: t= 2.6589
        if nf> 62: t= 2.6575
        if nf> 63: t= 2.6561
        if nf> 64: t= 2.6549
        if nf> 65: t= 2.6536
        if nf> 66: t= 2.6524
        if nf> 67: t= 2.6512
        if nf> 68: t= 2.6501
        if nf> 69: t= 2.6490
        if nf> 70: t= 2.6479
        if nf> 71: t= 2.6469
        if nf> 72: t= 2.6458
        if nf> 73: t= 2.6449
        if nf> 74: t= 2.6439
        if nf> 75: t= 2.6430
        if nf> 76: t= 2.6421
        if nf> 77: t= 2.6412
        if nf> 78: t= 2.6403
        if nf> 79: t= 2.6395
        if nf> 80: t= 2.6387
        if nf> 81: t= 2.6379
        if nf> 82: t= 2.6371
        if nf> 83: t= 2.6364
        if nf> 84: t= 2.6356
        if nf> 85: t= 2.6349
        if nf> 86: t= 2.6342
        if nf> 87: t= 2.6335
        if nf> 88: t= 2.6329
        if nf> 89: t= 2.6322
        if nf> 90: t= 2.6316
        if nf> 91: t= 2.6309
        if nf> 92: t= 2.6303
        if nf> 93: t= 2.6297
        if nf> 94: t= 2.6291
        if nf> 95: t= 2.6286
        if nf> 96: t= 2.6280
        if nf> 97: t= 2.6275
        if nf> 98: t= 2.6269
        if nf> 99: t= 2.6264
        if nf> 100: t= 2.6259
        return t   
        return t
    else:
        return 0
#
def sbar(Ss):
    """
    calculate average s,sigma from list of "s"s.
    """
    npts=len(Ss)
    Ss=numpy.array(Ss).transpose()
    avd,avs=[],[]
    #D=numpy.array([Ss[0],Ss[1],Ss[2],Ss[3]+0.5*(Ss[0]+Ss[1]),Ss[4]+0.5*(Ss[1]+Ss[2]),Ss[5]+0.5*(Ss[0]+Ss[2])]).transpose()
    D=numpy.array([Ss[0],Ss[1],Ss[2],Ss[3]+0.5*(Ss[0]+Ss[1]),Ss[4]+0.5*(Ss[1]+Ss[2]),Ss[5]+0.5*(Ss[0]+Ss[2])])
    for j in range(6):
        avd.append(numpy.average(D[j]))
        avs.append(numpy.average(Ss[j]))
    D=D.transpose()
    #for s in Ss:
    #    print 'from sbar: ',s
    #    D.append(s[:]) # append a copy of s
    #    D[-1][3]=D[-1][3]+0.5*(s[0]+s[1])
    #    D[-1][4]=D[-1][4]+0.5*(s[1]+s[2])
    #    D[-1][5]=D[-1][5]+0.5*(s[0]+s[2])
    #    for j in range(6):
    #        avd[j]+=(D[-1][j])/float(npts)
    #        avs[j]+=(s[j])/float(npts)
#   calculate sigma
    nf=(npts-1)*6 # number of degrees of freedom
    s0=0
    Dels=(D-avd)**2
    s0=numpy.sum(Dels)
    sigma=numpy.sqrt(s0/float(nf))
    return nf,sigma,avs
def dohext(nf,sigma,s):
    """
    calculates hext parameters for nf, sigma and s
    """
#
    if nf==-1:return hextpars 
    f=numpy.sqrt(2.*fcalc(2,nf))
    t2sum=0
    tau,Vdir=doseigs(s)
    for i in range(3): t2sum+=tau[i]**2
    chibar=(s[0]+s[1]+s[2])/3.
    hpars={}
    hpars['F_crit']='%s'%(fcalc(5,nf))
    hpars['F12_crit']='%s'%(fcalc(2,nf))
    hpars["F"]=0.4*(t2sum-3*chibar**2)/(sigma**2)
    hpars["F12"]=0.5*((tau[0]-tau[1])/sigma)**2
    hpars["F23"]=0.5*((tau[1]-tau[2])/sigma)**2
    hpars["v1_dec"]=Vdir[0][0]
    hpars["v1_inc"]=Vdir[0][1]
    hpars["v2_dec"]=Vdir[1][0]
    hpars["v2_inc"]=Vdir[1][1]
    hpars["v3_dec"]=Vdir[2][0]
    hpars["v3_inc"]=Vdir[2][1]
    hpars["t1"]=tau[0]
    hpars["t2"]=tau[1]
    hpars["t3"]=tau[2]
    hpars["e12"]=numpy.arctan((f*sigma)/(2*abs(tau[0]-tau[1])))*180./numpy.pi
    hpars["e23"]=numpy.arctan((f*sigma)/(2*abs(tau[1]-tau[2])))*180./numpy.pi
    hpars["e13"]=numpy.arctan((f*sigma)/(2*abs(tau[0]-tau[2])))*180./numpy.pi
    return hpars
#
#
def design(npos):
    """
     make a design matrix for an anisotropy experiment
    """
    if npos==15:
#
# rotatable design of Jelinek for kappabridge (see Tauxe, 1998)
#
        A=numpy.array([[.5,.5,0,-1.,0,0],[.5,.5,0,1.,0,0],[1,.0,0,0,0,0],[.5,.5,0,-1.,0,0],[.5,.5,0,1.,0,0],[0,.5,.5,0,-1.,0],[0,.5,.5,0,1.,0],[0,1.,0,0,0,0],[0,.5,.5,0,-1.,0],[0,.5,.5,0,1.,0],[.5,0,.5,0,0,-1.],[.5,0,.5,0,0,1.],[0,0,1.,0,0,0],[.5,0,.5,0,0,-1.],[.5,0,.5,0,0,1.]]) #  design matrix for 15 measurment positions
    elif npos==6:
        A=numpy.array([[1.,0,0,0,0,0],[0,1.,0,0,0,0],[0,0,1.,0,0,0],[.5,.5,0,1.,0,0],[0,.5,.5,0,1.,0],[.5,0,.5,0,0,1.]]) #  design matrix for 6 measurment positions

    else:
        print "measurement protocol not supported yet "
        sys.exit()
    B=numpy.dot(numpy.transpose(A),A)
    B=numpy.linalg.inv(B)
    B=numpy.dot(B,numpy.transpose(A))
    return A,B
#
#
def dok15_s(k15):
    """
    calculates least-squares matrix for 15 measurements from Jelinek [1976]
    """
#
    A,B=design(15) #  get design matrix for 15 measurements
    sbar=numpy.dot(B,k15) # get mean s
    t=(sbar[0]+sbar[1]+sbar[2]) # trace
    bulk=t/3. # bulk susceptibility
    Kbar=numpy.dot(A,sbar)  # get best fit values for K
    dels=k15-Kbar  # get deltas
    dels,sbar=dels/t,sbar/t# normalize by trace
    So= sum(dels**2) 
    sigma=numpy.sqrt(So/9.) # standard deviation
    return sbar,sigma,bulk
#
def cross(v, w):
    """
     cross product of two vectors
    """
    x = v[1]*w[2] - v[2]*w[1]
    y = v[2]*w[0] - v[0]*w[2]
    z = v[0]*w[1] - v[1]*w[0]
    return [x, y, z]
#
def dosgeo(s,az,pl):
    """
     rotates  matrix a to az,pl returns  s
    """
#
    a=s2a(s) # convert to 3,3 matrix
#  first get three orthogonal axes
    X1=dir2cart((az,pl,1.))
    X2=dir2cart((az+90,0.,1.))
    X3=cross(X1,X2)
    A=numpy.transpose([X1,X2,X3])
    b=numpy.zeros((3,3,),'f') # initiale the b matrix
    for i in range(3):
        for j in range(3): 
            dum=0
            for k in range(3): 
                for l in range(3): 
                    dum+=A[i][k]*A[j][l]*a[k][l]
            b[i][j]=dum 
    return a2s(b)
#
#
def dostilt(s,bed_az,bed_dip):
    """
     rotate "s" data to stratigraphic coordinates
    """
    tau,Vdirs=doseigs(s)
    Vrot=[] 
    for evec in Vdirs:
        d,i=dotilt(evec[0],evec[1],bed_az,bed_dip)
        Vrot.append([d,i])
    return doeigs_s(tau,Vrot)
#
#
def apseudo(Ss,ipar,sigma):
    """
     draw a bootstrap sample of Ss
    """
#
    Is=random.randint(0,len(Ss)-1,size=len(Ss)) # draw N random integers
    Ss=numpy.array(Ss)
    if ipar==0:
        BSs=Ss[Is]
    else: # need to recreate measurement - then do the parametric stuffr
        A,B=design(6) # get the design matrix for 6 measurements
        K,BSs=[],[]
        for k in range(len(Ss)):
            K.append(numpy.dot(A,Ss[k]))
        Pars=numpy.random.normal(K,sigma)
        for k in range(len(Ss)):
            BSs.append(numpy.dot(B,Pars[k]))
    return numpy.array(BSs)
#
def sbootpars(Taus,Vs):
    """
     get bootstrap parameters for s data
    """
#
    Tau1s,Tau2s,Tau3s=[],[],[]
    V1s,V2s,V3s=[],[],[]
    nb=len(Taus)
    bpars={}
    for k in range(nb):
        Tau1s.append(Taus[k][0])
        Tau2s.append(Taus[k][1])
        Tau3s.append(Taus[k][2])
        V1s.append(Vs[k][0])
        V2s.append(Vs[k][1])
        V3s.append(Vs[k][2])
    x,sig=gausspars(Tau1s) 
    bpars["t1_sigma"]=sig
    x,sig=gausspars(Tau2s) 
    bpars["t2_sigma"]=sig
    x,sig=gausspars(Tau3s) 
    bpars["t3_sigma"]=sig
    kpars=dokent(V1s,len(V1s))
    bpars["v1_dec"]=kpars["dec"]
    bpars["v1_inc"]=kpars["inc"]
    bpars["v1_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v1_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v1_zeta_dec"]=kpars["Zdec"]
    bpars["v1_zeta_inc"]=kpars["Zinc"]
    bpars["v1_eta_dec"]=kpars["Edec"]
    bpars["v1_eta_inc"]=kpars["Einc"]
    kpars=dokent(V2s,len(V2s))
    bpars["v2_dec"]=kpars["dec"]
    bpars["v2_inc"]=kpars["inc"]
    bpars["v2_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v2_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v2_zeta_dec"]=kpars["Zdec"]
    bpars["v2_zeta_inc"]=kpars["Zinc"]
    bpars["v2_eta_dec"]=kpars["Edec"]
    bpars["v2_eta_inc"]=kpars["Einc"]
    kpars=dokent(V3s,len(V3s))
    bpars["v3_dec"]=kpars["dec"]
    bpars["v3_inc"]=kpars["inc"]
    bpars["v3_zeta"]=kpars["Zeta"]*numpy.sqrt(nb)
    bpars["v3_eta"]=kpars["Eta"]*numpy.sqrt(nb)
    bpars["v3_zeta_dec"]=kpars["Zdec"]
    bpars["v3_zeta_inc"]=kpars["Zinc"]
    bpars["v3_eta_dec"]=kpars["Edec"]
    bpars["v3_eta_inc"]=kpars["Einc"]
    return bpars
#
#
def s_boot(Ss,ipar):
    """
     returns bootstrap parameters for S data
    """
    npts=len(Ss)
# get average s for whole dataset
    nf,Sigma,avs=sbar(Ss)
    Tmean,Vmean=doseigs(avs) # get eigenvectors of mean tensor
#
# now do bootstrap to collect Vs and taus of bootstrap means
#
    nb,Taus,Vs=1000,[],[]  # number of bootstraps, list of bootstrap taus and eigenvectors
#

    for k in range(nb): # repeat nb times
#        if k%50==0:print k,' out of ',nb
        BSs=apseudo(Ss,ipar,Sigma) # get a pseudosample - if ipar=1, do a parametric bootstrap
        nf,sigma,avbs=sbar(BSs) # get bootstrap mean s
        tau,Vdirs=doseigs(avbs) # get bootstrap eigenparameters
        Taus.append(tau)
        Vs.append(Vdirs)
    return Tmean,Vmean,Taus,Vs

#
def designAARM(npos):
#
    """  
    calculates B matrix for AARM calculations.  
    """
    if npos!=9:
        print 'Sorry - only 9 positions available'
        sys.exit()
    Dec=[315.,225.,180.,135.,45.,90.,270.,270.,270.,90.,180.,180.,0.,0.,0.]
    Dip=[0.,0.,0.,0.,0.,-45.,-45.,0.,45.,45.,45.,-45.,-90.,-45.,45.]
    index9=[0,1, 2,5,6,7,10,11,12]
    H=[]
    for ind in range(15):
        Dir=[Dec[ind],Dip[ind],1.]
        H.append(dir2cart(Dir))  # 15 field directionss
#
# make design matrix A
#
    A=numpy.zeros((npos*3,6),'f')
    tmpH=numpy.zeros((npos,3),'f') # define tmpH
    if npos == 9:
        for i in range(9):
            k=index9[i]
            ind=i*3
            A[ind][0]=H[k][0]
            A[ind][3]=H[k][1]
            A[ind][5]=H[k][2]
            ind=i*3+1
            A[ind][3]=H[k][0]
            A[ind][1]=H[k][1]
            A[ind][4]=H[k][2]
            ind=i*3+2
            A[ind][5]=H[k][0]
            A[ind][4]=H[k][1]
            A[ind][2]=H[k][2]
            for j in range(3):
                tmpH[i][j]=H[k][j]
        At=numpy.transpose(A)
        ATA=numpy.dot(At,A)
        ATAI=numpy.linalg.inv(ATA)
        B=numpy.dot(ATAI,At)
    else:
        print "B matrix not yet supported"
        sys.exit()
    return B,H,tmpH
#
def designATRM(npos):
#
    """
    calculates B matrix for ATRM calculations.
    """
    #if npos!=6:
    #    print 'Sorry - only 6 positions available'
    #    sys.exit()
    Dec=[0,0,  0,90,180,270,0] # for shuhui only
    Dip=[90,-90,0,0,0,0,90]
    Dec=[0,90,0,180,270,0,0,90,0]
    Dip=[0,0,90,0,0,-90,0,0,90]
    H=[]
    for ind in range(6):
        Dir=[Dec[ind],Dip[ind],1.]
        H.append(dir2cart(Dir))  # 6 field directionss
#
# make design matrix A
#
    A=numpy.zeros((npos*3,6),'f')
    tmpH=numpy.zeros((npos,3),'f') # define tmpH
    #if npos == 6:
    #    for i in range(6):
    for i in range(6):
            ind=i*3
            A[ind][0]=H[i][0]
            A[ind][3]=H[i][1]
            A[ind][5]=H[i][2]
            ind=i*3+1
            A[ind][3]=H[i][0]
            A[ind][1]=H[i][1]
            A[ind][4]=H[i][2]
            ind=i*3+2
            A[ind][5]=H[i][0]
            A[ind][4]=H[i][1]
            A[ind][2]=H[i][2]
            for j in range(3):
                tmpH[i][j]=H[i][j]
    At=numpy.transpose(A)
    ATA=numpy.dot(At,A)
    ATAI=numpy.linalg.inv(ATA)
    B=numpy.dot(ATAI,At)
    #else:
    #    print "B matrix not yet supported"
    #    sys.exit()
    return B,H,tmpH

#
def domagicmag(file,Recs):
    """
    converts a magic record back into the SIO mag format
    """
    for rec in Recs:
        type=".0"
        meths=[]
        tmp=rec["magic_method_codes"].split(':') 
        for meth in tmp:
            meths.append(meth.strip())
        if 'LT-T-I' in meths: type=".1"
        if 'LT-PTRM-I' in meths: type=".2"
        if 'LT-PTRM-MD' in meths: type=".3"
        treatment=float(rec["treatment_temp"])-273
        tr='%i'%(treatment)+type
        inten='%8.7e '%(float(rec["measurement_magn_moment"])*1e3)
        outstring=rec["er_specimen_name"]+" "+tr+" "+rec["measurement_csd"]+" "+inten+" "+rec["measurement_dec"]+" "+rec["measurement_inc"]+"\n"
        file.write(outstring)
#
#
def cleanup(first_I,first_Z):
    """
     cleans up unbalanced steps
     failure can be from unbalanced final step, or from missing steps,
     this takes care of  missing steps
    """
    cont=0
    Nmin=len(first_I)
    if len(first_Z)<Nmin:Nmin=len(first_Z)
    for kk in range(Nmin):
        if first_I[kk][0]!=first_Z[kk][0]:
            print "\n WARNING: "
            if first_I[kk]<first_Z[kk]:
                del first_I[kk] 
            else:
                del first_Z[kk] 
            print "Unmatched step number: ",kk+1,'  ignored'
            cont=1
        if cont==1: return first_I,first_Z,cont
    return first_I,first_Z,cont
#
#
def sortarai(datablock,s,Zdiff):
    """
     sorts data block in to first_Z, first_I, etc.
    """
    first_Z,first_I,zptrm_check,ptrm_check,ptrm_tail=[],[],[],[],[]
    field,phi,theta="","",""
    starthere=0
    Treat_I,Treat_Z,Treat_PZ,Treat_PI,Treat_M=[],[],[],[],[]
    ISteps,ZSteps,PISteps,PZSteps,MSteps=[],[],[],[],[]
    GammaChecks=[] # comparison of pTRM direction acquired and lab field
    Mkeys=['measurement_magn_moment','measurement_magn_volume','measurement_magn_mass','measurement_magnitude']
    rec=datablock[0]
    for key in Mkeys:
        if key in rec.keys() and rec[key]!="":
            momkey=key
            break
# first find all the steps
    for k in range(len(datablock)):
	rec=datablock[k]
        temp=float(rec["treatment_temp"])
        methcodes=[]
        tmp=rec["magic_method_codes"].split(":")
        for meth in tmp:
            methcodes.append(meth.strip())
        if 'LT-T-I' in methcodes and 'LP-TRM' not in methcodes and 'LP-PI-TRM' in methcodes:
            Treat_I.append(temp)
            ISteps.append(k)
            if field=="":field=float(rec["treatment_dc_field"])
            if phi=="":
                phi=float(rec['treatment_dc_field_phi'])
                theta=float(rec['treatment_dc_field_theta'])
# stick  first zero field stuff into first_Z 
        if 'LT-NO' in methcodes:
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-T-Z' in methcodes: 
            Treat_Z.append(temp)
            ZSteps.append(k)
        if 'LT-PTRM-Z' in methcodes:
            Treat_PZ.append(temp)
            PZSteps.append(k)
        if 'LT-PTRM-I' in methcodes:
            Treat_PI.append(temp)
            PISteps.append(k)
        if 'LT-PTRM-MD' in methcodes:
            Treat_M.append(temp)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec[momkey])
            first_I.append([273,0.,0.,0.,1])
            first_Z.append([273,dec,inc,str,1])  # NRM step
    for temp in Treat_I: # look through infield steps and find matching Z step
        if temp in Treat_Z: # found a match
            istep=ISteps[Treat_I.index(temp)]
            irec=datablock[istep]
            methcodes=[]
            tmp=irec["magic_method_codes"].split(":")
            for meth in tmp: methcodes.append(meth.strip())
            brec=datablock[istep-1] # take last record as baseline to subtract  
            zstep=ZSteps[Treat_Z.index(temp)]
            zrec=datablock[zstep]
    # sort out first_Z records 
            if "LP-PI-TRM-IZ" in methcodes: 
                ZI=0    
            else:   
                ZI=1    
            dec=float(zrec["measurement_dec"])
            inc=float(zrec["measurement_inc"])
            str=float(zrec[momkey])
            first_Z.append([temp,dec,inc,str,ZI])
    # sort out first_I records 
            idec=float(irec["measurement_dec"])
            iinc=float(irec["measurement_inc"])
            istr=float(irec[momkey])
            X=dir2cart([idec,iinc,istr])
            BL=dir2cart([dec,inc,str])
            I=[]
            for c in range(3): I.append((X[c]-BL[c]))
            if I[2]!=0:
                iDir=cart2dir(I)
                if Zdiff==0:
                    first_I.append([temp,iDir[0],iDir[1],iDir[2],ZI])
                else:
                    first_I.append([temp,0.,0.,I[2],ZI])
                gamma=angle([iDir[0],iDir[1]],[phi,theta])
            else:
                first_I.append([temp,0.,0.,0.,ZI])
                gamma=0.0
# put in Gamma check (infield trm versus lab field)
            if 180.-gamma<gamma:  gamma=180.-gamma
            GammaChecks.append([temp-273.,gamma])
    for temp in Treat_PI: # look through infield steps and find matching Z step
        step=PISteps[Treat_PI.index(temp)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        brec=datablock[step-1] # take last record as baseline to subtract
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec[momkey])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir1=cart2dir(I)
        if Zdiff==0:
            ptrm_check.append([temp,dir1[0],dir1[1],dir1[2]])
        else:
            ptrm_check.append([temp,0.,0.,I[2]])
# in case there are zero-field pTRM checks (not the SIO way)
    for temp in Treat_PZ:
        step=PZSteps[Treat_PZ.index(temp)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        brec=datablock[step-1]
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec[momkey])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir2=cart2dir(I)
        zptrm_check.append([temp,dir2[0],dir2[1],dir2[2]])
    ## get pTRM tail checks together -
    for temp in Treat_M:
        step=MSteps[Treat_M.index(temp)] # tail check step - just do a difference in magnitude!
        rec=datablock[step]
#        dec=float(rec["measurement_dec"])
#        inc=float(rec["measurement_inc"])
        str=float(rec[momkey])
        if temp in Treat_Z:
            step=ZSteps[Treat_Z.index(temp)]
            brec=datablock[step]
#        pdec=float(brec["measurement_dec"])
#        pinc=float(brec["measurement_inc"])
            pint=float(brec[momkey])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
#        ptrm_tail.append([temp,d[0],d[1],d[2]])
            ptrm_tail.append([temp,0,0,str-pint])  # difference - if negative, negative tail!
        else:
            print s, '  has a tail check with no first zero field step - check input file! for step',temp-273.
#
# final check
#
    if len(first_Z)!=len(first_I):
               print len(first_Z),len(first_I)
               print " Something wrong with this specimen! Better fix it or delete it "
               raw_input(" press return to acknowledge message")
    araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks)
    return araiblock,field

def sortmwarai(datablock,exp_type):
    """
     sorts microwave double heating data block in to first_Z, first_I, etc.
    """
    first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check=[],[],[],[],[]
    field,phi,theta="","",""
    POWT_I,POWT_Z,POWT_PZ,POWT_PI,POWT_M=[],[],[],[],[]
    ISteps,ZSteps,PZSteps,PISteps,MSteps=[],[],[],[],[]
    rad=numpy.pi/180.
    ThetaChecks=[] # 
    DeltaChecks=[]
    GammaChecks=[]
# first find all the steps
    for k in range(len(datablock)):
        rec=datablock[k]
        powt=int(float(rec["treatment_mw_energy"]))
        methcodes=[]
        tmp=rec["magic_method_codes"].split(":")
        for meth in tmp: methcodes.append(meth.strip())
        if 'LT-M-I' in methcodes and 'LP-MRM' not in methcodes:
            POWT_I.append(powt)
            ISteps.append(k)
            if field=="":field=float(rec['treatment_dc_field'])
            if phi=="":
                phi=float(rec['treatment_dc_field_phi'])
                theta=float(rec['treatment_dc_field_theta'])
        if 'LT-M-Z' in methcodes:
            POWT_Z.append(powt)
            ZSteps.append(k)
        if 'LT-PMRM-Z' in methcodes:
            POWT_PZ.append(powt)
            PZSteps.append(k)
        if 'LT-PMRM-I' in methcodes:
            POWT_PI.append(powt)
            PISteps.append(k)
        if 'LT-PMRM-MD' in methcodes:
            POWT_M.append(powt)
            MSteps.append(k)
        if 'LT-NO' in methcodes:
            dec=float(rec["measurement_dec"])
            inc=float(rec["measurement_inc"])
            str=float(rec["measurement_magn_moment"])
            first_I.append([0,0.,0.,0.,1])
            first_Z.append([0,dec,inc,str,1])  # NRM step
    if exp_type=="LP-PI-M-D":
# now look trough infield steps and  find matching Z step
        for powt in POWT_I:
            if powt in POWT_Z: 
                istep=ISteps[POWT_I.index(powt)]
                irec=datablock[istep]
                methcodes=[]
                tmp=irec["magic_method_codes"].split(":")
                for meth in tmp: methcodes.append(meth.strip())
                brec=datablock[istep-1] # take last record as baseline to subtract  
                zstep=ZSteps[POWT_Z.index(powt)]
                zrec=datablock[zstep]
    # sort out first_Z records
                if "LP-PI-M-IZ" in methcodes: 
                    ZI=0
                else:
                    ZI=1
                dec=float(zrec["measurement_dec"])
                inc=float(zrec["measurement_inc"])
                str=float(zrec["measurement_magn_moment"])
                first_Z.append([powt,dec,inc,str,ZI])
    # sort out first_I records
                idec=float(irec["measurement_dec"])
                iinc=float(irec["measurement_inc"])
                istr=float(irec["measurement_magn_moment"])
                X=dir2cart([idec,iinc,istr])
                BL=dir2cart([dec,inc,str])
                I=[]
                for c in range(3): I.append((X[c]-BL[c]))
                iDir=cart2dir(I)
                first_I.append([powt,iDir[0],iDir[1],iDir[2],ZI])
# put in Gamma check (infield trm versus lab field)
                gamma=angle([iDir[0],iDir[1]],[phi,theta])
                GammaChecks.append([powt,gamma])
    elif exp_type=="LP-PI-M-S":
# find last zero field step before first infield step
        lzrec=datablock[ISteps[0]-1]
        irec=datablock[ISteps[0]]
        ndec=float(lzrec["measurement_dec"])
        ninc=float(lzrec["measurement_inc"])
        nstr=float(lzrec["measurement_magn_moment"])
        NRM=dir2cart([ndec,ninc,nstr])
        fdec=float(irec["treatment_dc_field_phi"])
        finc=float(irec["treatment_dc_field_theta"])
        Flab=dir2cart([fdec,finc,1.])
        for step in ISteps:
            irec=datablock[step]
            rdec=float(irec["measurement_dec"])
            rinc=float(irec["measurement_inc"])
            rstr=float(irec["measurement_magn_moment"])
            theta1=angle([ndec,ninc],[rdec,rinc])
            theta2=angle([rdec,rinc],[fdec,finc])
            powt=int(float(irec["treatment_mw_energy"]))
            ThetaChecks.append([powt,theta1+theta2])
            p=(180.-(theta1+theta2))
            nstr=rstr*(numpy.sin(theta2*rad)/numpy.sin(p*rad))
            tmstr=rstr*(numpy.sin(theta1*rad)/numpy.sin(p*rad))
            first_Z.append([powt,ndec,ninc,nstr,1])
            first_I.append([powt,dec,inc,tmstr,1])
# check if zero field steps are parallel to assumed NRM
        for step in ZSteps:
            zrec=datablock[step]
            powt=int(float(zrec["treatment_mw_energy"]))
            zdec=float(zrec["measurement_dec"])
            zinc=float(zrec["measurement_inc"])
            delta=angle([ndec,ninc],[zdec,zinc])
            DeltaChecks.append([powt,delta])
    # get pTRMs together - take previous record and subtract
    for powt in POWT_PI:
        step=PISteps[POWT_PI.index(powt)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        brec=datablock[step-1] # take last record as baseline to subtract  
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir1=cart2dir(I)
        ptrm_check.append([powt,dir1[0],dir1[1],dir1[2]])
    ## get zero field pTRM  checks together 
    for powt in POWT_PZ:
        step=PZSteps[POWT_PZ.index(powt)]
        rec=datablock[step]
        dec=float(rec["measurement_dec"])
        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        brec=datablock[step-1]
        pdec=float(brec["measurement_dec"])
        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
        X=dir2cart([dec,inc,str])
        prevX=dir2cart([pdec,pinc,pint])
        I=[]
        for c in range(3): I.append(X[c]-prevX[c])
        dir2=cart2dir(I)
        zptrm_check.append([powt,dir2[0],dir2[1],dir2[2]])
    ## get pTRM tail checks together - 
    for powt in POWT_M:
        step=MSteps[POWT_M.index(powt)] # tail check step
        rec=datablock[step]
#        dec=float(rec["measurement_dec"])
#        inc=float(rec["measurement_inc"])
        str=float(rec["measurement_magn_moment"])
        step=ZSteps[POWT_Z.index(powt)]
        brec=datablock[step]
#        pdec=float(brec["measurement_dec"])
#        pinc=float(brec["measurement_inc"])
        pint=float(brec["measurement_magn_moment"])
#        X=dir2cart([dec,inc,str])
#        prevX=dir2cart([pdec,pinc,pint])
#        I=[]
#        for c in range(3):I.append(X[c]-prevX[c])
#        d=cart2dir(I)
 #       ptrm_tail.append([powt,d[0],d[1],d[2]])
        ptrm_tail.append([powt,0,0,str-pint])  # just do absolute magnitude difference # not vector diff
    #  check
    #
        if len(first_Z)!=len(first_I):
                   print len(first_Z),len(first_I)
                   print " Something wrong with this specimen! Better fix it or delete it "
                   raw_input(" press return to acknowledge message")
                   print MaxRec
    araiblock=(first_Z,first_I,ptrm_check,ptrm_tail,zptrm_check,GammaChecks,ThetaChecks,DeltaChecks)
    return araiblock,field
    
    #
def doigrf(long,lat,alt,date):
    """
#       calculates the interpolated (<2010) or extrapolated (>2010) main field and
#       secular variation coefficients and passes these to the Malin and Barraclough
#       routine to calculate the IGRF field. dgrf coefficients for 1945 to 2005, igrf for pre 1945 and post 2010 
#       from http://www.ngdc.noaa.gov/IAGA/vmod/igrf.html 
#
#      for dates prior to 1900, this program uses coefficients from the GUFM1 model of Jackson et al. 2000
#    
#
#       input:
#       date  = Required date in years and decimals of a year (A.D.)
#       alt   = height above mean sea level in km (itype = 1 assumed)
#       lat   = latitude in degrees (-90 to 90)
#       long  = east longitude in degrees (0 to 360 or -180 to 180)
# Output:
#       x     = north component of the magnetic force in nT
#       y     = east component of the magnetic force in nT
#       z     = downward component of the magnetic force in nT
#       f     = total magnetic force in nT
#
#       To check the results you can run the interactive program at the NGDC
#        http://www.ngdc.noaa.gov/geomagmodels/IGRFWMM.jsp
    """

#
#
    gh,sv=[],[]
    igrf1900=[-31543, -2298, 5922, -677, 2905, -1061, 924, 1121, 1022, -1469, -330, 1256, 3, 572, 523, 876, 628, 195, 660, -69, -361, -210, 134, -75, -184, 328, -210, 264, 53, 5, -33, -86, -124, -16, 3, 63, 61, -9, -11, 83, -217, 2, -58, -35, 59, 36, -90, -69, 70, -55, -45, 0, -13, 34, -10, -41, -1, -21, 28, 18, -12, 6, -22, 11, 8, 8, -4, -14, -9, 7, 1, -13, 2, 5, -9, 16, 5, -5, 8, -18, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 8, 2, 10, -1, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 2, 4, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1905=[-31464, -2298, 5909, -728, 2928, -1086, 1041, 1065, 1037, -1494, -357, 1239, 34, 635, 480, 880, 643, 203, 653, -77, -380, -201, 146, -65, -192, 328, -193, 259, 56, -1, -32, -93, -125, -26, 11, 62, 60, -7, -11, 86, -221, 4, -57, -32, 57, 32, -92, -67, 70, -54, -46, 0, -14, 33, -11, -41, 0, -20, 28, 18, -12, 6, -22, 11, 8, 8, -4, -15, -9, 7, 1, -13, 2, 5, -8, 16, 5, -5, 8, -18, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 8, 2, 10, 0, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 2, 4, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1910=[-31354, -2297, 5898, -769, 2948, -1128, 1176, 1000, 1058, -1524, -389, 1223, 62, 705, 425, 884, 660, 211, 644, -90, -400, -189, 160, -55, -201, 327, -172, 253, 57, -9, -33, -102, -126, -38, 21, 62, 58, -5, -11, 89, -224, 5, -54, -29, 54, 28, -95, -65, 71, -54, -47, 1, -14, 32, -12, -40, 1, -19, 28, 18, -13, 6, -22, 11, 8, 8, -4, -15, -9, 6, 1, -13, 2, 5, -8, 16, 5, -5, 8, -18, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 8, 2, 10, 0, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 2, 4, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1915=[-31212, -2306, 5875, -802, 2956, -1191, 1309, 917, 1084, -1559, -421, 1212, 84, 778, 360, 887, 678, 218, 631, -109, -416, -173, 178, -51, -211, 327, -148, 245, 58, -16, -34, -111, -126, -51, 32, 61, 57, -2, -10, 93, -228, 8, -51, -26, 49, 23, -98, -62, 72, -54, -48, 2, -14, 31, -12, -38, 2, -18, 28, 19, -15, 6, -22, 11, 8, 8, -4, -15, -9, 6, 2, -13, 3, 5, -8, 16, 6, -5, 8, -18, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 8, 2, 10, 0, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 1, 4, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1920=[-31060, -2317, 5845, -839, 2959, -1259, 1407, 823, 1111, -1600, -445, 1205, 103, 839, 293, 889, 695, 220, 616, -134, -424, -153, 199, -57, -221, 326, -122, 236, 58, -23, -38, -119, -125, -62, 43, 61, 55, 0, -10, 96, -233, 11, -46, -22, 44, 18, -101, -57, 73, -54, -49, 2, -14, 29, -13, -37, 4, -16, 28, 19, -16, 6, -22, 11, 7, 8, -3, -15, -9, 6, 2, -14, 4, 5, -7, 17, 6, -5, 8, -19, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 9, 2, 10, 0, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 1, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1925=[-30926, -2318, 5817, -893, 2969, -1334, 1471, 728, 1140, -1645, -462, 1202, 119, 881, 229, 891, 711, 216, 601, -163, -426, -130, 217, -70, -230, 326, -96, 226, 58, -28, -44, -125, -122, -69, 51, 61, 54, 3, -9, 99, -238, 14, -40, -18, 39, 13, -103, -52, 73, -54, -50, 3, -14, 27, -14, -35, 5, -14, 29, 19, -17, 6, -21, 11, 7, 8, -3, -15, -9, 6, 2, -14, 4, 5, -7, 17, 7, -5, 8, -19, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 9, 2, 10, 0, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 1, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1930=[-30805, -2316, 5808, -951, 2980, -1424, 1517, 644, 1172, -1692, -480, 1205, 133, 907, 166, 896, 727, 205, 584, -195, -422, -109, 234, -90, -237, 327, -72, 218, 60, -32, -53, -131, -118, -74, 58, 60, 53, 4, -9, 102, -242, 19, -32, -16, 32, 8, -104, -46, 74, -54, -51, 4, -15, 25, -14, -34, 6, -12, 29, 18, -18, 6, -20, 11, 7, 8, -3, -15, -9, 5, 2, -14, 5, 5, -6, 18, 8, -5, 8, -19, 8, 10, -20, 1, 14, -12, 5, 12, -3, 1, -2, -2, 9, 3, 10, 0, -2, -2, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 1, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1935=[-30715, -2306, 5812, -1018, 2984, -1520, 1550, 586, 1206, -1740, -494, 1215, 146, 918, 101, 903, 744, 188, 565, -226, -415, -90, 249, -114, -241, 329, -51, 211, 64, -33, -64, -136, -115, -76, 64, 59, 53, 4, -8, 104, -246, 25, -25, -15, 25, 4, -106, -40, 74, -53, -52, 4, -17, 23, -14, -33, 7, -11, 29, 18, -19, 6, -19, 11, 7, 8, -3, -15, -9, 5, 1, -15, 6, 5, -6, 18, 8, -5, 7, -19, 8, 10, -20, 1, 15, -12, 5, 11, -3, 1, -3, -2, 9, 3, 11, 0, -2, -2, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -1, 2, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    igrf1940=[-30654, -2292, 5821, -1106, 2981, -1614, 1566, 528, 1240, -1790, -499, 1232, 163, 916, 43, 914, 762, 169, 550, -252, -405, -72, 265, -141, -241, 334, -33, 208, 71, -33, -75, -141, -113, -76, 69, 57, 54, 4, -7, 105, -249, 33, -18, -15, 18, 0, -107, -33, 74, -53, -52, 4, -18, 20, -14, -31, 7, -9, 29, 17, -20, 5, -19, 11, 7, 8, -3, -14, -10, 5, 1, -15, 6, 5, -5, 19, 9, -5, 7, -19, 8, 10, -21, 1, 15, -12, 5, 11, -3, 1, -3, -2, 9, 3, 11, 1, -2, -2, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -1, 2, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1945=[-30594, -2285, 5810, -1244, 2990, -1702, 1578, 477, 1282, -1834, -499, 1255, 186, 913, -11, 944, 776, 144, 544, -276, -421, -55, 304, -178, -253, 346, -12, 194, 95, -20, -67, -142, -119, -82, 82, 59, 57, 6, 6, 100, -246, 16, -25, -9, 21, -16, -104, -39, 70, -40, -45, 0, -18, 0, 2, -29, 6, -10, 28, 15, -17, 29, -22, 13, 7, 12, -8, -21, -5, -12, 9, -7, 7, 2, -10, 18, 7, 3, 2, -11, 5, -21, -27, 1, 17, -11, 29, 3, -9, 16, 4, -3, 9, -4, 6, -3, 1, -4, 8, -3, 11, 5, 1, 1, 2, -20, -5, -1, -1, -6, 8, 6, -1, -4, -3, -2, 5, 0, -2, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1950=[-30554, -2250, 5815, -1341, 2998, -1810, 1576, 381, 1297, -1889, -476, 1274, 206, 896, -46, 954, 792, 136, 528, -278, -408, -37, 303, -210, -240, 349, 3, 211, 103, -20, -87, -147, -122, -76, 80, 54, 57, -1, 4, 99, -247, 33, -16, -12, 12, -12, -105, -30, 65, -55, -35, 2, -17, 1, 0, -40, 10, -7, 36, 5, -18, 19, -16, 22, 15, 5, -4, -22, -1, 0, 11, -21, 15, -8, -13, 17, 5, -4, -1, -17, 3, -7, -24, -1, 19, -25, 12, 10, 2, 5, 2, -5, 8, -2, 8, 3, -11, 8, -7, -8, 4, 13, -1, -2, 13, -10, -4, 2, 4, -3, 12, 6, 3, -3, 2, 6, 10, 11, 3, 8, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1955=[-30500, -2215, 5820, -1440, 3003, -1898, 1581, 291, 1302, -1944, -462, 1288, 216, 882, -83, 958, 796, 133, 510, -274, -397, -23, 290, -230, -229, 360, 15, 230, 110, -23, -98, -152, -121, -69, 78, 47, 57, -9, 3, 96, -247, 48, -8, -16, 7, -12, -107, -24, 65, -56, -50, 2, -24, 10, -4, -32, 8, -11, 28, 9, -20, 18, -18, 11, 9, 10, -6, -15, -14, 5, 6, -23, 10, 3, -7, 23, 6, -4, 9, -13, 4, 9, -11, -4, 12, -5, 7, 2, 6, 4, -2, 1, 10, 2, 7, 2, -6, 5, 5, -3, -5, -4, -1, 0, 2, -8, -3, -2, 7, -4, 4, 1, -2, -3, 6, 7, -2, -1, 0, -3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1960=[-30421, -2169, 5791, -1555, 3002, -1967, 1590, 206, 1302, -1992, -414, 1289, 224, 878, -130, 957, 800, 135, 504, -278, -394, 3, 269, -255, -222, 362, 16, 242, 125, -26, -117, -156, -114, -63, 81, 46, 58, -10, 1, 99, -237, 60, -1, -20, -2, -11, -113, -17, 67, -56, -55, 5, -28, 15, -6, -32, 7, -7, 23, 17, -18, 8, -17, 15, 6, 11, -4, -14, -11, 7, 2, -18, 10, 4, -5, 23, 10, 1, 8, -20, 4, 6, -18, 0, 12, -9, 2, 1, 0, 4, -3, -1, 9, -2, 8, 3, 0, -1, 5, 1, -3, 4, 4, 1, 0, 0, -1, 2, 4, -5, 6, 1, 1, -1, -1, 6, 2, 0, 0, -7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1965=[-30334, -2119, 5776, -1662, 2997, -2016, 1594, 114, 1297, -2038, -404, 1292, 240, 856, -165, 957, 804, 148, 479, -269, -390, 13, 252, -269, -219, 358, 19, 254, 128, -31, -126, -157, -97, -62, 81, 45, 61, -11, 8, 100, -228, 68, 4, -32, 1, -8, -111, -7, 75, -57, -61, 4, -27, 13, -2, -26, 6, -6, 26, 13, -23, 1, -12, 13, 5, 7, -4, -12, -14, 9, 0, -16, 8, 4, -1, 24, 11, -3, 4, -17, 8, 10, -22, 2, 15, -13, 7, 10, -4, -1, -5, -1, 10, 5, 10, 1, -4, -2, 1, -2, -3, 2, 2, 1, -5, 2, -2, 6, 4, -4, 4, 0, 0, -2, 2, 3, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1970=[-30220, -2068, 5737, -1781, 3000, -2047, 1611, 25, 1287, -2091, -366, 1278, 251, 838, -196, 952, 800, 167, 461, -266, -395, 26, 234, -279, -216, 359, 26, 262, 139, -42, -139, -160, -91, -56, 83, 43, 64, -12, 15, 100, -212, 72, 2, -37, 3, -6, -112, 1, 72, -57, -70, 1, -27, 14, -4, -22, 8, -2, 23, 13, -23, -2, -11, 14, 6, 7, -2, -15, -13, 6, -3, -17, 5, 6, 0, 21, 11, -6, 3, -16, 8, 10, -21, 2, 16, -12, 6, 10, -4, -1, -5, 0, 10, 3, 11, 1, -2, -1, 1, -3, -3, 1, 2, 1, -5, 3, -1, 4, 6, -4, 4, 0, 1, -1, 0, 3, 3, 1, -1, -4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1975=[-30100, -2013, 5675, -1902, 3010, -2067, 1632, -68, 1276, -2144, -333, 1260, 262, 830, -223, 946, 791, 191, 438, -265, -405, 39, 216, -288, -218, 356, 31, 264, 148, -59, -152, -159, -83, -49, 88, 45, 66, -13, 28, 99, -198, 75, 1, -41, 6, -4, -111, 11, 71, -56, -77, 1, -26, 16, -5, -14, 10, 0, 22, 12, -23, -5, -12, 14, 6, 6, -1, -16, -12, 4, -8, -19, 4, 6, 0, 18, 10, -10, 1, -17, 7, 10, -21, 2, 16, -12, 7, 10, -4, -1, -5, -1, 10, 4, 11, 1, -3, -2, 1, -3, -3, 1, 2, 1, -5, 3, -2, 4, 5, -4, 4, -1, 1, -1, 0, 3, 3, 1, -1, -5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1980=[-29992, -1956, 5604, -1997, 3027, -2129, 1663, -200, 1281, -2180, -336, 1251, 271, 833, -252, 938, 782, 212, 398, -257, -419, 53, 199, -297, -218, 357, 46, 261, 150, -74, -151, -162, -78, -48, 92, 48, 66, -15, 42, 93, -192, 71, 4, -43, 14, -2, -108, 17, 72, -59, -82, 2, -27, 21, -5, -12, 16, 1, 18, 11, -23, -2, -10, 18, 6, 7, 0, -18, -11, 4, -7, -22, 4, 9, 3, 16, 6, -13, -1, -15, 5, 10, -21, 1, 16, -12, 9, 9, -5, -3, -6, -1, 9, 7, 10, 2, -6, -5, 2, -4, -4, 1, 2, 0, -5, 3, -2, 6, 5, -4, 3, 0, 1, -1, 2, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1985=[-29873, -1905, 5500, -2072, 3044, -2197, 1687, -306, 1296, -2208, -310, 1247, 284, 829, -297, 936, 780, 232, 361, -249, -424, 69, 170, -297, -214, 355, 47, 253, 150, -93, -154, -164, -75, -46, 95, 53, 65, -16, 51, 88, -185, 69, 4, -48, 16, -1, -102, 21, 74, -62, -83, 3, -27, 24, -2, -6, 20, 4, 17, 10, -23, 0, -7, 21, 6, 8, 0, -19, -11, 5, -9, -23, 4, 11, 4, 14, 4, -15, -4, -11, 5, 10, -21, 1, 15, -12, 9, 9, -6, -3, -6, -1, 9, 7, 9, 1, -7, -5, 2, -4, -4, 1, 3, 0, -5, 3, -2, 6, 5, -4, 3, 0, 1, -1, 2, 4, 3, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1990=[-29775, -1848, 5406, -2131, 3059, -2279, 1686, -373, 1314, -2239, -284, 1248, 293, 802, -352, 939, 780, 247, 325, -240, -423, 84, 141, -299, -214, 353, 46, 245, 154, -109, -153, -165, -69, -36, 97, 61, 65, -16, 59, 82, -178, 69, 3, -52, 18, 1, -96, 24, 77, -64, -80, 2, -26, 26, 0, -1, 21, 5, 17, 9, -23, 0, -4, 23, 5, 10, -1, -19, -10, 6, -12, -22, 3, 12, 4, 12, 2, -16, -6, -10, 4, 9, -20, 1, 15, -12, 11, 9, -7, -4, -7, -2, 9, 7, 8, 1, -7, -6, 2, -3, -4, 2, 2, 1, -5, 3, -2, 6, 4, -4, 3, 0, 1, -2, 3, 3, 3, -1, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf1995=[-29692, -1784, 5306, -2200, 3070, -2366, 1681, -413, 1335, -2267, -262, 1249, 302, 759, -427, 940, 780, 262, 290, -236, -418, 97, 122, -306, -214, 352, 46, 235, 165, -118, -143, -166, -55, -17, 107, 68, 67, -17, 68, 72, -170, 67, -1, -58, 19, 1, -93, 36, 77, -72, -69, 1, -25, 28, 4, 5, 24, 4, 17, 8, -24, -2, -6, 25, 6, 11, -6, -21, -9, 8, -14, -23, 9, 15, 6, 11, -5, -16, -7, -4, 4, 9, -20, 3, 15, -10, 12, 8, -6, -8, -8, -1, 8, 10, 5, -2, -8, -8, 3, -3, -6, 1, 2, 0, -4, 4, -1, 5, 4, -5, 2, -1, 2, -2, 5, 1, 1, -2, 0, -7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    dgrf2000=[-29619.4, -1728.2, 5186.1, -2267.7, 3068.4, -2481.6, 1670.9, -458.0, 1339.6, -2288.0, -227.6, 1252.1, 293.4, 714.5, -491.1, 932.3, 786.8, 272.6, 250.0, -231.9, -403.0, 119.8, 111.3, -303.8, -218.8, 351.4, 43.8, 222.3, 171.9, -130.4, -133.1, -168.6, -39.3, -12.9, 106.3, 72.3, 68.2, -17.4, 74.2, 63.7, -160.9, 65.1, -5.9, -61.2, 16.9, 0.7, -90.4, 43.8, 79.0, -74.0, -64.6, 0.0, -24.2, 33.3, 6.2, 9.1, 24.0, 6.9, 14.8, 7.3, -25.4, -1.2, -5.8, 24.4, 6.6, 11.9, -9.2, -21.5, -7.9, 8.5, -16.6, -21.5, 9.1, 15.5, 7.0, 8.9, -7.9, -14.9, -7.0, -2.1, 5.0, 9.4, -19.7, 3.0, 13.4, -8.4, 12.5, 6.3, -6.2, -8.9, -8.4, -1.5, 8.4, 9.3, 3.8, -4.3, -8.2, -8.2, 4.8, -2.6, -6.0, 1.7, 1.7, 0.0, -3.1, 4.0, -0.5, 4.9, 3.7, -5.9, 1.0, -1.2, 2.0, -2.9, 4.2, 0.2, 0.3, -2.2, -1.1, -7.4, 2.7, -1.7, 0.1, -1.9, 1.3, 1.5, -0.9, -0.1, -2.6, 0.1, 0.9, -0.7, -0.7, 0.7, -2.8, 1.7, -0.9, 0.1, -1.2, 1.2, -1.9, 4.0, -0.9, -2.2, -0.3, -0.4, 0.2, 0.3, 0.9, 2.5, -0.2, -2.6, 0.9, 0.7, -0.5, 0.3, 0.3, 0.0, -0.3, 0.0, -0.4, 0.3, -0.1, -0.9, -0.2, -0.4, -0.4, 0.8, -0.2, -0.9, -0.9, 0.3, 0.2, 0.1, 1.8, -0.4, -0.4, 1.3, -1.0, -0.4, -0.1, 0.7, 0.7, -0.4, 0.3, 0.3, 0.6, -0.1, 0.3, 0.4, -0.2, 0.0, -0.5, 0.1, -0.9]
    dgrf2005=[-29554.63, -1669.05, 5077.99, -2337.24, 3047.69, -2594.50, 1657.76, -515.43, 1336.30, -2305.83, -198.86, 1246.39, 269.72, 672.51, -524.72, 920.55, 797.96, 282.07, 210.65, -225.23, -379.86, 145.15, 100.00, -305.36, -227.00, 354.41, 42.72, 208.95, 180.25, -136.54, -123.45, -168.05, -19.57, -13.55, 103.85, 73.60, 69.56, -20.33, 76.74, 54.75, -151.34, 63.63, -14.58, -63.53, 14.58, 0.24, -86.36, 50.94, 79.88, -74.46, -61.14, -1.65, -22.57, 38.73, 6.82, 12.30, 25.35, 9.37, 10.93, 5.42, -26.32, 1.94, -4.64, 24.80, 7.62, 11.20, -11.73, -20.88, -6.88, 9.83, -18.11, -19.71, 10.17, 16.22, 9.36, 7.61, -11.25, -12.76, -4.87, -0.06, 5.58, 9.76, -20.11, 3.58, 12.69, -6.94, 12.67, 5.01, -6.72, -10.76, -8.16, -1.25, 8.10, 8.76, 2.92, -6.66, -7.73, -9.22, 6.01, -2.17, -6.12, 2.19, 1.42, 0.10, -2.35, 4.46, -0.15, 4.76, 3.06, -6.58, 0.29, -1.01, 2.06, -3.47, 3.77, -0.86, -0.21, -2.31, -2.09, -7.93, 2.95, -1.60, 0.26, -1.88, 1.44, 1.44, -0.77, -0.31, -2.27, 0.29, 0.90, -0.79, -0.58, 0.53, -2.69, 1.80, -1.08, 0.16, -1.58, 0.96, -1.90, 3.99, -1.39, -2.15, -0.29, -0.55, 0.21, 0.23, 0.89, 2.38, -0.38, -2.63, 0.96, 0.61, -0.30, 0.40, 0.46, 0.01, -0.35, 0.02, -0.36, 0.28, 0.08, -0.87, -0.49, -0.34, -0.08, 0.88, -0.16, -0.88, -0.76, 0.30, 0.33, 0.28, 1.72, -0.43, -0.54, 1.18, -1.07, -0.37, -0.04, 0.75, 0.63, -0.26, 0.21, 0.35, 0.53, -0.05, 0.38, 0.41, -0.22, -0.10, -0.57, -0.18, -0.82]
    igrf2010=[-29496.5, -1585.9, 4945.1, -2396.6, 3026.0, -2707.7, 1668.6, -575.4, 1339.7, -2326.3, -160.5, 1231.7, 251.7, 634.2, -536.8, 912.6, 809.0, 286.4, 166.6, -211.2, -357.1, 164.4, 89.7, -309.2, -231.1, 357.2, 44.7, 200.3, 188.9, -141.2, -118.1, -163.1, 0.1, -7.7, 100.9, 72.8, 68.6, -20.8, 76.0, 44.2, -141.4, 61.5, -22.9, -66.3, 13.1, 3.1, -77.9, 54.9, 80.4, -75.0, -57.8, -4.7, -21.2, 45.3, 6.6, 14.0, 24.9, 10.4, 7.0, 1.6, -27.7, 4.9, -3.4, 24.3, 8.2, 10.9, -14.5, -20.0, -5.7, 11.9, -19.3, -17.4, 11.6, 16.7, 10.9, 7.1, -14.1, -10.8, -3.7, 1.7, 5.4, 9.4, -20.5, 3.4, 11.6, -5.3, 12.8, 3.1, -7.2, -12.4, -7.4, -0.8, 8.0, 8.4, 2.2, -8.4, -6.1, -10.1, 7.0, -2.0, -6.3, 2.8, 0.9, -0.1, -1.1, 4.7, -0.2, 4.4, 2.5, -7.2, -0.3, -1.0, 2.2, -4.0, 3.1, -2.0, -1.0, -2.0, -2.8, -8.3, 3.0, -1.5, 0.1, -2.1, 1.7, 1.6, -0.6, -0.5, -1.8, 0.5, 0.9, -0.8, -0.4, 0.4, -2.5, 1.8, -1.3, 0.2, -2.1, 0.8, -1.9, 3.8, -1.8, -2.1, -0.2, -0.8, 0.3, 0.3, 1.0, 2.2, -0.7, -2.5, 0.9, 0.5, -0.1, 0.6, 0.5, 0.0, -0.4, 0.1, -0.4, 0.3, 0.2, -0.9, -0.8, -0.2, 0.0, 0.8, -0.2, -0.9, -0.8, 0.3, 0.3, 0.4, 1.7, -0.4, -0.6, 1.1, -1.2, -0.3, -0.1, 0.8, 0.5, -0.2, 0.1, 0.4, 0.5, 0.0, 0.4, 0.4, -0.2, -0.3, -0.5, -0.3, -0.8]
    sv2010_15=[11.4, 16.7, -28.8, -11.3, -3.9, -23.0, 2.7, -12.9, 1.3, -3.9, 8.6, -2.9, -2.9, -8.1, -2.1, -1.4, 2.0, 0.4, -8.9, 3.2, 4.4, 3.6, -2.3, -0.8, -0.5, 0.5, 0.5, -1.5, 1.5, -0.7, 0.9, 1.3, 3.7, 1.4, -0.6, -0.3, -0.3, -0.1, -0.3, -2.1, 1.9, -0.4, -1.6, -0.5, -0.2, 0.8, 1.8, 0.5, 0.2, -0.1, 0.6, -0.6, 0.3, 1.4, -0.2, 0.3, -0.1, 0.1, -0.8, -0.8, -0.3, 0.4, 0.2, -0.1, 0.1, 0.0, -0.5, 0.2, 0.3, 0.5, -0.3, 0.4, 0.3, 0.1, 0.2, -0.1, -0.5, 0.4, 0.2, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    colat = 90.-lat                                         
#! convert to colatitude for MB routine
    if long>0: long=long+360.                       
# ensure all positive east longitudes
    itype = 1                                                       
# use geodetic coordinates
    if date<-10000:
        print 'too old'
        sys.exit()
    if date<-2000:
        import cals10k # goes back to 8000 BC now
        date0=date-date%10
        field1=numpy.array(cals10k.coeffs(date0))
        field2=numpy.array(cals10k.coeffs(date0+10))
        gh=field1
        sv=(field2-field1)/10.
        x,y,z,f=magsyn(gh,sv,date0,date,itype,alt,colat,long)
    elif date<1800:
        import cals3k # goes back to 2000 BC now
        date0=date-date%10
        field1=numpy.array(cals3k.coeffs(date0))
        field2=numpy.array(cals3k.coeffs(date0+10.))
        gh=field1
        sv=(field2-field1)/10.
        x,y,z,f=magsyn(gh,sv,date0,date,itype,alt,colat,long)
    elif date<1900:
        import cals3k # goes back to 2000 BC now
        date0=1800
        field1=numpy.array(cals3k.coeffs(date0))
        field2=[-31543, -2298, 5922, -677, 2905, -1061, 924, 1121, 1022, -1469, -330, 1256, 3, 572, 523, 876, 628, 195, 660, -69, -361, -210, 134, -75, -184, 328, -210, 264, 53, 5, -33, -86, -124, -16, 3, 63, 61, -9, -11, 83, -217, 2, -58, -35, 59, 36, -90, -69, 70, -55, -45, 0, -13, 34, -10, -41, -1, -21, 28, 18, -12, 6, -22, 11, 8, 8, -4, -14, -9, 7, 1, -13, 2, 5, -9, 16, 5, -5, 8, -18, 8, 10, -20, 1, 14, -11, 5, 12, -3, 1, -2, -2, 8, 2, 10, -1, -2, -1, 2, -3, -4, 2, 2, 1, -5, 2, -2, 6, 6, -4, 4, 0, 0, -2, 2, 4, 2, 0, 0, -6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        field2=field2[0:120]
        gh=field1
        sv=(field2-field1)/100.
        x,y,z,f=magsyn(gh,sv,date0,date,itype,alt,colat,long)
    elif date<1905:
        for i in range(len(igrf1900)):
            gh.append(igrf1900[i])
            sv.append((igrf1905[i]-igrf1900[i])/5.)
        x,y,z,f=magsyn(gh,sv,1900.,date,itype,alt,colat,long)
    elif date<1910:
        for i in range(len(igrf1905)):
            gh.append(igrf1905[i])
            sv.append((igrf1910[i]-igrf1905[i])/5.)
        x,y,z,f=magsyn(gh,sv,1905.,date,itype,alt,colat,long)
    elif date<1915:
        for i in range(len(igrf1910)):
            gh.append(igrf1910[i])
            sv.append((igrf1915[i]-igrf1910[i])/5.)
        x,y,z,f=magsyn(gh,sv,1910.,date,itype,alt,colat,long)
    elif date<1920:
        for i in range(len(igrf1915)):
            gh.append(igrf1915[i])
            sv.append((igrf1920[i]-igrf1915[i])/5.)
        x,y,z,f=magsyn(gh,sv,1915.,date,itype,alt,colat,long)
    elif date<1925:
        for i in range(len(igrf1920)):
            gh.append(igrf1920[i])
            sv.append((igrf1925[i]-igrf1920[i])/5.)
        x,y,z,f=magsyn(gh,sv,1915.,date,itype,alt,colat,long)
    elif date<1930:
        for i in range(len(igrf1925)):
            gh.append(igrf1925[i])
            sv.append((igrf1930[i]-igrf1925[i])/5.)
        x,y,z,f=magsyn(gh,sv,1925.,date,itype,alt,colat,long)
    elif date<1935:
        for i in range(len(igrf1930)):
            gh.append(igrf1930[i])
            sv.append((igrf1935[i]-igrf1930[i])/5.)
        x,y,z,f=magsyn(gh,sv,1930.,date,itype,alt,colat,long)
    elif date<1940:
        for i in range(len(igrf1935)):
            gh.append(igrf1935[i])
            sv.append((igrf1940[i]-igrf1935[i])/5.)
        x,y,z,f=magsyn(gh,sv,1935.,date,itype,alt,colat,long)
    elif date<1945:
        for i in range(len(igrf1940)):
            gh.append(igrf1940[i])
            sv.append((dgrf1945[i]-igrf1940[i])/5.)
        x,y,z,f=magsyn(gh,sv,1940.,date,itype,alt,colat,long)
    elif date<1950:
        for i in range(len(dgrf1945)):
            gh.append(dgrf1945[i])
            sv.append((dgrf1950[i]-dgrf1945[i])/5.)
        x,y,z,f=magsyn(gh,sv,1940.,date,itype,alt,colat,long)
    elif date<1955:
        for i in range(len(dgrf1950)):
            gh.append(dgrf1950[i])
            sv.append((dgrf1955[i]-dgrf1950[i])/5.)
        x,y,z,f=magsyn(gh,sv,1950.,date,itype,alt,colat,long)
    elif date<1960:
        for i in range(len(dgrf1955)):
            gh.append(dgrf1955[i])
            sv.append((dgrf1960[i]-dgrf1955[i])/5.)
        x,y,z,f=magsyn(gh,sv,1955.,date,itype,alt,colat,long)
    elif date<1965:
        for i in range(len(dgrf1960)):
            gh.append(dgrf1960[i])
            sv.append((dgrf1965[i]-dgrf1960[i])/5.)
        x,y,z,f=magsyn(gh,sv,1960.,date,itype,alt,colat,long)
    elif date<1970:
        for i in range(len(dgrf1965)):
            gh.append(dgrf1965[i])
            sv.append((dgrf1970[i]-dgrf1965[i])/5.)
        x,y,z,f=magsyn(gh,sv,1965.,date,itype,alt,colat,long)
    elif date<1975:
        for i in range(len(dgrf1970)):
            gh.append(dgrf1970[i])
            sv.append((dgrf1975[i]-dgrf1970[i])/5.)
        x,y,z,f=magsyn(gh,sv,1970.,date,itype,alt,colat,long)
    elif date<1980:
        for i in range(len(dgrf1975)):
            gh.append(dgrf1975[i])
            sv.append((dgrf1980[i]-dgrf1975[i])/5.)
        x,y,z,f=magsyn(gh,sv,1975,date,itype,alt,colat,long)
    elif date<1985:
        for i in range(len(dgrf1980)):
            gh.append(dgrf1980[i])
            sv.append((dgrf1985[i]-dgrf1980[i])/5.)
        x,y,z,f=magsyn(gh,sv,1980.,date,itype,alt,colat,long)
    elif date<1990:
        for i in range(len(dgrf1985)):
            gh.append(dgrf1985[i])
            sv.append((dgrf1990[i]-dgrf1985[i])/5.)
        x,y,z,f=magsyn(gh,sv,1985,date,itype,alt,colat,long)
    elif date<1995:
        for i in range(len(dgrf1990)):
            gh.append(dgrf1990[i])
            sv.append((dgrf1995[i]-dgrf1990[i])/5.)
        x,y,z,f=magsyn(gh,sv,1990.,date,itype,alt,colat,long)
    elif date<2000:
        for i in range(len(dgrf1995)):
            gh.append(dgrf1995[i])
            sv.append((dgrf1990[i]-dgrf1995[i])/5.)
        x,y,z,f=magsyn(gh,sv,1995.,date,itype,alt,colat,long)
    elif date<2005:
        for i in range(len(dgrf2000)):
            gh.append(dgrf2000[i])
            sv.append((dgrf2005[i]-dgrf2000[i])/5.)
        x,y,z,f=magsyn(gh,sv,2000.,date,itype,alt,colat,long)
    elif date<2010:
        for i in range(len(dgrf2005)):
            gh.append(dgrf2005[i])
            sv.append((igrf2010[i]-dgrf2005[i])/5.)
        x,y,z,f=magsyn(gh,sv,2005.,date,itype,alt,colat,long)
    else:
        for i in range(len(igrf2010)):
            gh.append(igrf2010[i])
            sv.append(sv2010_15[i])
        x,y,z,f=magsyn(gh,sv,2010.,date,itype,alt,colat,long)
    return x,y,z,f
#
def magsyn(gh,sv,b,date,itype,alt,colat,elong):
    """
# Computes x, y, z, and f for a given date and position, from the
# spherical harmonic coeifficients of the International Geomagnetic
# Reference Field (IGRF).
# From Malin and Barraclough (1981), Computers and Geosciences, V.7, 401-405.
#
# Input:
#       date  = Required date in years and decimals of a year (A.D.)
#       itype = 1, if geodetic coordinates are used, 2 if geocentric
#       alt   = height above mean sea level in km (if itype = 1)
#       alt   = radial distance from the center of the earth (itype = 2)
#       colat = colatitude in degrees (0 to 180)
#       elong = east longitude in degrees (0 to 360)
#               gh        = main field values for date (calc. in igrf subroutine)
#               sv        = secular variation coefficients (calc. in igrf subroutine)
#               begin = date of dgrf (or igrf) field prior to required date
#
# Output:
#       x     - north component of the magnetic force in nT
#       y     - east component of the magnetic force in nT
#       z     - downward component of the magnetic force in nT
#       f     - total magnetic force in nT
#
#       NB: the coordinate system for x,y, and z is the same as that specified
#       by itype.
#
# Modified 4/9/97 to use DGRFs from 1945 to 1990 IGRF
# Modified 10/13/06 to use  1995 DGRF, 2005 IGRF and sv coefficient
# for extrapolation beyond 2005. Coefficients from Barton et al. PEPI, 97: 23-26
# (1996), via web site for NOAA, World Data Center A. Modified to use
#degree and
# order 10 as per notes in Malin and Barraclough (1981). 
# coefficients for DGRF 1995 and IGRF 2005 are from http://nssdcftp.gsfc.nasa.gov/models/geomagnetic/igrf/fortran_code/
# igrf subroutine calculates
# the proper main field and secular variation coefficients (interpolated between
# dgrf values or extrapolated from 1995 sv values as appropriate).
    """
#
#       real gh(120),sv(120),p(66),q(66),cl(10),sl(10)
#               real begin,dateq
    p=numpy.zeros((66),'f')
    q=numpy.zeros((66),'f')
    cl=numpy.zeros((10),'f')
    sl=numpy.zeros((10),'f')
    begin=b
    t = date - begin
    r = alt
    one = colat*0.0174532925
    ct = numpy.cos(one)
    st = numpy.sin(one)
    one = elong*0.0174532925
    cl[0] = numpy.cos(one)
    sl[0] = numpy.sin(one)
    x,y,z = 0.0,0.0,0.0
    cd,sd = 1.0,0.0
    l,ll,m,n = 1,0,1,0
    if itype!=2:
#
# if required, convert from geodectic to geocentric
        a2 = 40680925.0
        b2 = 40408585.0
        one = a2 * st * st
        two = b2 * ct * ct
        three = one + two
        rho = numpy.sqrt(three)
        r = numpy.sqrt(alt*(alt+2.0*rho) + (a2*one+b2*two)/three)
        cd = (alt + rho) /r
        sd = (a2 - b2) /rho * ct * st /r
        one = ct
        ct = ct*cd - st*sd
        st  = st*cd + one*sd
    ratio = 6371.2 /r
    rr = ratio * ratio
#
# compute Schmidt quasi-normal coefficients p and x(=q)
    p[0] = 1.0
    p[2] = st
    q[0] = 0.0
    q[2] = ct
    for k in range(1,66):
        if n < m:   # else go to 2
            m = 0
            n = n + 1
            rr = rr * ratio
            fn = n
            gn = n - 1
# 2
        fm = m
        if k != 2: # else go to 4
            if m == n:   # else go to 3
                one = numpy.sqrt(1.0 - 0.5/fm)
                j = k - n - 1
                p[k] = one * st * p[j]
                q[k] = one * (st*q[j] + ct*p[j])
                cl[m-1] = cl[m-2]*cl[0] - sl[m-2]*sl[0]
                sl[m-1] = sl[m-2]*cl[0] + cl[m-2]*sl[0]
            else:
# 3
                gm = m * m
                one = numpy.sqrt(fn*fn - gm)
                two = numpy.sqrt(gn*gn - gm) /one
                three = (fn + gn) /one
                i = k - n
                j = i - n + 1
                p[k] = three*ct*p[i] - two*p[j]
                q[k] = three*(ct*q[i] - st*p[i]) - two*q[j]
#
# synthesize x, y, and z in geocentric coordinates.
# 4
        one = (gh[l-1] + sv[ll+l-1]*t)*rr
        if m != 0: # else go to 7
            two = (gh[l] + sv[ll+l]*t)*rr
            three = one*cl[m-1] + two*sl[m-1]
            x = x + three*q[k]
            z = z - (fn + 1.0)*three*p[k]
            if st != 0.0: # else go to 5
                y = y + (one*sl[m-1] - two*cl[m-1])*fm*p[k]/st
            else: 
# 5
                y = y + (one*sl[m-1] - two*cl[m-1])*q[k]*ct
            l = l + 2
        else: 
# 7
            x = x + one*q[k]
            z = z - (fn + 1.0)*one*p[k]
            l = l + 1
        m = m + 1
#
# convert to coordinate system specified by itype
    one = x
    x = x*cd + z*sd
    z = z*cd - one*sd
    f = numpy.sqrt(x*x + y*y + z*z)
#
    return x,y,z,f
#
#
def measurements_methods(meas_data,noave):
    """
    get list of unique specs
    """
#
    version_num=get_version()
    sids=get_specs(meas_data)
# list  of measurement records for this specimen
#
# step through spec by spec 
#
    SpecTmps,SpecOuts=[],[]
    for spec in sids:
        TRM,IRM3D,ATRM=0,0,0
        expcodes=""
# first collect all data for this specimen and do lab treatments
        SpecRecs=get_dictitem(meas_data,'er_specimen_name',spec,'T') # list  of measurement records for this specimen
        for rec in SpecRecs:
            tmpmeths=rec['magic_method_codes'].split(":")
            meths=[]
            if "LP-TRM" in tmpmeths:TRM=1 # catch these suckers here!
            if "LP-IRM-3D" in tmpmeths: 
                IRM3D=1 # catch these suckers here!
            elif "LP-AN-TRM" in tmpmeths: 
                ATRM=1 # catch these suckers here!
#
# otherwise write over existing method codes
#
# find NRM data (LT-NO)
#
            elif float(rec["measurement_temp"])>=273. and float(rec["measurement_temp"]) < 323.:   
# between 0 and 50C is room T measurement
                if ("measurement_dc_field" not in rec.keys() or float(rec["measurement_dc_field"])==0 or rec["measurement_dc_field"]=="") and ("measurement_ac_field" not in rec.keys() or float(rec["measurement_ac_field"])==0 or rec["measurement_ac_field"]==""): 
# measurement done in zero field!
                    if  "treatment_temp" not in rec.keys() or rec["treatment_temp"].strip()=="" or (float(rec["treatment_temp"])>=273. and float(rec["treatment_temp"]) < 298.):   
# between 0 and 50C is room T treatment
                        if "treatment_ac_field" not in rec.keys() or rec["treatment_ac_field"] =="" or float(rec["treatment_ac_field"])==0: 
# no AF
                            if "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0:# no IRM!
                                if "LT-NO" not in meths:meths.append("LT-NO")
                            elif "LT-IRM" not in meths:
                                meths.append("LT-IRM") # it's an IRM
#
# find AF/infield/zerofield
#
                        elif "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0: # no ARM
                            if "LT-AF-Z" not in meths:meths.append("LT-AF-Z")
                        else: # yes ARM
                            if "LT-AF-I" not in meths: meths.append("LT-AF-I")
#
# find Thermal/infield/zerofield
#
                    elif float(rec["treatment_temp"])>323:  # treatment done at  high T
                        if TRM==1:
                            if "LT-T-I" not in meths: meths.append("LT-T-I") # TRM - even if zero applied field! 
                        elif "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0.: # no TRM
                            if  "LT-T-Z" not in meths: meths.append("LT-T-Z") # don't overwrite if part of a TRM experiment!
                        else: # yes TRM
                            if "LT-T-I" not in meths: meths.append("LT-T-I")
#
# find low-T infield,zero field
#
                    else:  # treatment done at low T
                        if "treatment_dc_field" not in rec.keys() or rec["treatment_dc_field"]=="" or float(rec["treatment_dc_field"])==0: # no field
                            if "LT-LT-Z" not in meths:meths.append("LT-LT-Z")
                        else: # yes field
                            if "LT-LT-I" not in meths:meths.append("LT-LT-I")
                if "measurement_chi_volume" in rec.keys() or "measurement_chi_mass" in rec.keys():
                    if  "LP-X" not in meths:meths.append("LP-X")
                elif "measurement_lab_dc_field" in rec.keys() and rec["measurement_lab_dc_field"]!=0: # measurement in presence of dc field and not susceptibility; hysteresis!
                    if  "LP-HYS" not in meths:
                        hysq=raw_input("Is this a hysteresis experiment? [1]/0")
                        if hysq=="" or hysq=="1":
                            meths.append("LP-HYS")
                        else:
                            metha=raw_input("Enter the lab protocol code that best describes this experiment ")
                            meths.append(metha)
                methcode=""
                for meth in meths:
                    methcode=methcode+meth.strip()+":"
                rec["magic_method_codes"]=methcode[:-1] # assign them back
#
# done with first pass, collect and assign provisional method codes
            if "measurement_description" not in rec.keys():rec["measurement_description"]=""
            rec["er_citation_names"]="This study"
            SpecTmps.append(rec)
# ready for second pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
    for spec in sids:
        MD,pTRM,IZ,ZI=0,0,0,0 # these are flags for the lab protocol codes
        expcodes=""
        NewSpecs,SpecMeths=[],[]
        experiment_name,measnum="",1
        if IRM3D==1:experiment_name="LP-IRM-3D"
        if ATRM==1:experiment_name="LP-AN-TRM"
        NewSpecs=get_dictitem(SpecTmps,'er_specimen_name',spec,'T')
#
# first look for replicate measurements
#
        Ninit=len(NewSpecs)
        if noave!=1:
            vdata,treatkeys=vspec_magic(NewSpecs) # averages replicate measurements, returns treatment keys that are being used
            if len(vdata)!=len(NewSpecs):
                print spec,'started with ',Ninit,' ending with ',len(vdata)
                NewSpecs=vdata
                print "Averaged replicate measurements"
#
# now look through this specimen's records - try to figure out what experiment it is
#
        if len(NewSpecs)>1: # more than one meas for this spec - part of an unknown experiment
            SpecMeths=get_list(NewSpecs,'magic_method_codes').split(":")
            if "LT-T-I" in  SpecMeths and experiment_name=="": # TRM steps, could be TRM acquisition, Shaw or a Thellier experiment or TDS experiment
    #
    # collect all the infield steps and look for changes in dc field vector
    #
                Steps=[]
                for rec in  NewSpecs: 
                    methods=get_list(NewSpecs,'magic_method_codes').split(":")
                    if "LT-T-I" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        ANIS=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS==1:
                            experiment_name="LP-AN-TRM"
                if experiment_name=="":  # could be TRM  acquisition or Shaw?
                    if "LT-AF-I" in SpecMeths and "LT-AF-Z" in SpecMeths: # must be Shaw :(
                        experiment_name="LP-PI-TRM:LP-PI-ALT-AFARM"
                    elif TRM==0: # catch a TRM acquisition experiment not already labelled
                        field0=rec_bak["treatment_dc_field"]
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            field=rec["treatment_dc_field"]
                            if field!=field0: TRM=1  # changing DC field strength means must be TRM acquisition 
                        if TRM==1:
                            experiment_name="LP-TRM"
                    else: # we already knew it was a trm acquisition experiment 
                        TRM=1
                        experiment_name="LP-TRM"
                TI=1
          
            else: TI= 0 # no infield steps at all
            if "LT-T-Z" in  SpecMeths and experiment_name=="": # thermal demag steps
                if TI==0: 
                    experiment_name="LP-DIR-T" # just ordinary thermal demag
                
                elif TRM!=1: # heart pounding - could be some  kind of TRM normalized paleointensity or LP-TRM-TD experiment 
                    Temps=[]
                    for step in Steps: # check through the infield steps - if all at same temperature, then must be a demag of a total TRM with checks
                        if step['treatment_temp'] not in Temps:Temps.append(step['treatment_temp'])
                    if len(Temps)>1: 
                        experiment_name="LP-PI-TRM" # paleointensity normalized by TRM 
                    else: 
                        experiment_name="LP-TRM-TD" # thermal demag of a lab TRM (could be part of a LP-PI-TDS experiment)
                TZ=1
            else: TZ= 0 # no zero field steps at all
            if "LT-AF-I" in  SpecMeths: # ARM steps
                Steps=[]
                for rec in  NewSpecs: 
                    tmp=rec["magic_method_codes"].split(":")
                    methods=[]
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-AF-I" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        ANIS=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS==1:
                            experiment_name="LP-AN-ARM"
                if experiment_name=="":  # not anisotropy of ARM - acquisition?   
                        field0=rec_bak["treatment_dc_field"]
                        ARM=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            field=rec["treatment_dc_field"]
                            if field!=field0: ARM=1
                        if ARM==1:
                            experiment_name="LP-ARM"
                AFI=1
            else: AFI= 0 # no ARM steps at all
            if "LT-AF-Z" in  SpecMeths and experiment_name=="": # AF demag steps
                if AFI==0: 
                    experiment_name="LP-DIR-AF" # just ordinary AF demag
                else: # heart pounding - a pseudothellier?
                    experiment_name="LP-PI-ARM" 
                AFZ=1
            else: AFZ= 0 # no AF demag at all
            if "LT-IRM" in SpecMeths: # IRM
                Steps=[]
                for rec in  NewSpecs: 
                    tmp=rec["magic_method_codes"].split(":")
                    methods=[]
                    for meth in tmp:
                        methods.append(meth.strip())
                    if "LT-IRM" in methods:Steps.append(rec)  # get all infield steps together
                rec_bak=Steps[0]
                if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                    if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                        phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                        ANIS=0
                        for k in range(1,len(Steps)):
                            rec=Steps[k]
                            phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                            if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                        if ANIS==1:experiment_name="LP-AN-IRM"
                if experiment_name=="":  # not anisotropy of IRM - acquisition?   
                    field0=rec_bak["treatment_dc_field"]
                    IRM=0 
                    for k in range(1,len(Steps)):
                        rec=Steps[k]
                        field=rec["treatment_dc_field"]
                        if field!=field0: IRM=1
                    if IRM==1:experiment_name="LP-IRM"
                IRM=1
            else: IRM=0 # no IRM at all
            if "LP-X" in SpecMeths: # susceptibility run
                Steps=get_dictitem(NewSpecs,'magic_method_codes','LT-X','has')
                if len(Steps)>0:
                    rec_bak=Steps[0]
                    if "treatment_dc_field_phi" in rec_bak.keys() and "treatment_dc_field_theta" in rec_bak.keys():   
                        if rec_bak["treatment_dc_field_phi"] !="" and rec_bak["treatment_dc_field_theta"]!="":   # at least there is field orientation info
                            phi0,theta0=rec_bak["treatment_dc_field_phi"],rec_bak["treatment_dc_field_theta"]
                            ANIS=0
                            for k in range(1,len(Steps)):
                                rec=Steps[k]
                                phi,theta=rec["treatment_dc_field_phi"],rec["treatment_dc_field_theta"]
                                if phi!=phi0 or theta!=theta0: ANIS=1   # if direction changes, is some sort of anisotropy experiment
                            if ANIS==1:experiment_name="LP-AN-MS"
            else: CHI=0 # no susceptibility at all
    #
    # now need to deal with special thellier experiment problems - first clear up pTRM checks and  tail checks
    # 
            if experiment_name=="LP-PI-TRM": # is some sort of thellier experiment
                rec_bak=NewSpecs[0]
                tmp=rec_bak["magic_method_codes"].split(":")
                methbak=[]
                for meth in tmp:
                    methbak.append(meth.strip()) # previous steps method codes
                for k in range(1,len(NewSpecs)):
                    rec=NewSpecs[k]
                    tmp=rec["magic_method_codes"].split(":")
                    meths=[]
                    for meth in tmp:
                        meths.append(meth.strip()) # get this guys method codes
    #
    # check if this is a pTRM check
    #
                    if float(rec["treatment_temp"])<float(rec_bak["treatment_temp"]): # went backward
                        if "LT-T-I" in meths and "LT-T-Z" in methbak:  #must be a pTRM check after first z 
    #
    # replace LT-T-I method code with LT-PTRM-I
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-I":methcode=methcode+meth.strip()+":"
                            methcodes=methcodes+"LT-PTRM-I"
                            meths=methcodes.split(":")
                            pTRM=1
                        elif "LT-T-Z" in meths and "LT-T-I" in methbak:  # must be pTRM check after first I
    #
    # replace LT-T-Z method code with LT-PTRM-Z
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-Z":methcode=methcode+meth+":"
                            methcodes=methcodes+"LT-PTRM-Z"
                            meths=methcodes.split(":")
                            pTRM=1
                    methcodes=""
                    for meth in meths:
                        methcodes=methcodes+meth.strip()+":"
                    rec["magic_method_codes"]=methcodes[:-1]  #  attach new method code
                    rec_bak=rec # next previous record
                    tmp=rec_bak["magic_method_codes"].split(":")
                    methbak=[]
                    for meth in tmp:
                        methbak.append(meth.strip()) # previous steps method codes
    #
    # done with assigning pTRM checks.  data should be "fixed" in NewSpecs
    #
    # now let's find out which steps are infield zerofield (IZ) and which are zerofield infield (ZI)
    #
                rec_bak=NewSpecs[0]
                tmp=rec_bak["magic_method_codes"].split(":")
                methbak=[]
                for meth in tmp:
                    methbak.append(meth.strip()) # previous steps method codes
                if "LT-NO" not in methbak: # first measurement is not NRM
                    if "LT-T-I" in methbak: IZorZI="LP-PI-TRM-IZ" # first pair is IZ
                    if "LT-T-Z" in methbak: IZorZI="LP-PI-TRM-ZI" # first pair is ZI
                    if IZorZI not in methbak:methbak.append(IZorZI)
                    methcode=""
                    for meth in methbak:
                        methcode=methcode+meth+":"
                    NewSpecs[0]["magic_method_codes"]=methcode[:-1]  # fix first heating step when no NRM
                else: IZorZI="" # first measurement is NRM and not one of a pair
                for k in range(1,len(NewSpecs)): # hunt through measurements again
                    rec=NewSpecs[k]
                    tmp=rec["magic_method_codes"].split(":")
                    meths=[]
                    for meth in tmp:
                        meths.append(meth.strip()) # get this guys method codes
    #
    # check if this start a new temperature step of a infield/zerofield pair
    #
                    if float(rec["treatment_temp"])>float(rec_bak["treatment_temp"]) and "LT-PTRM-I" not in methbak: # new pair?
                        if "LT-T-I" in meths:  # infield of this pair
                                IZorZI="LP-PI-TRM-IZ" 
                                IZ=1 # at least one IZ pair
                        elif "LT-T-Z" in meths: #zerofield 
                                IZorZI="LP-PI-TRM-ZI" 
                                ZI=1 # at least one ZI pair
                    elif float(rec["treatment_temp"])>float(rec_bak["treatment_temp"]) and "LT-PTRM-I" in methbak and IZorZI!="LP-PI-TRM-ZI": # new pair after out of sequence PTRM check?
                        if "LT-T-I" in meths:  # infield of this pair
                                IZorZI="LP-PI-TRM-IZ" 
                                IZ=1 # at least one IZ pair
                        elif "LT-T-Z" in meths: #zerofield 
                                IZorZI="LP-PI-TRM-ZI" 
                                ZI=1 # at least one ZI pair
                    if float(rec["treatment_temp"])==float(rec_bak["treatment_temp"]): # stayed same temp
                        if "LT-T-Z" in meths and "LT-T-I" in methbak and IZorZI=="LP-PI-TRM-ZI":  #must be a tail check
    #
    # replace LT-T-Z method code with LT-PTRM-MD
    #
                            methcodes=""
                            for meth in meths:
                                if meth!="LT-T-Z":methcode=methcode+meth+":"
                            methcodes=methcodes+"LT-PTRM-MD"
                            meths=methcodes.split(":")
                            MD=1
    # fix method codes
                    if "LT-PTRM-I" not in meths and "LT-PTRM-MD" not in meths and IZorZI not in meths:meths.append(IZorZI)
                    newmeths=[]
                    for meth in meths:
                        if meth not in newmeths:newmeths.append(meth)  # try to get uniq set
                    methcode=""
                    for meth in newmeths:
                        methcode=methcode+meth+":"
                    rec["magic_method_codes"]=methcode[:-1] 
                    rec_bak=rec # moving on to next record, making current one the backup
                    methbak=rec_bak["magic_method_codes"].split(":") # get last specimen's method codes in a list
                   
    #
    # done with this specimen's records, now  check if any pTRM checks or MD checks
    #
                if pTRM==1:experiment_name=experiment_name+":LP-PI-ALT-PTRM"
                if MD==1:experiment_name=experiment_name+":LP-PI-BT-MD"
                if IZ==1 and ZI==1:experiment_name=experiment_name+":LP-PI-BT-IZZI"
                if IZ==1 and ZI==0:experiment_name=experiment_name+":LP-PI-IZ" # Aitken method
                if IZ==0 and ZI==1:experiment_name=experiment_name+":LP-PI-ZI" # Coe method
                IZ,ZI,pTRM,MD=0,0,0,0  # reset these for next specimen
                for rec in NewSpecs: # fix the experiment name for all recs for this specimen and save in SpecOuts
    # assign an experiment name to all specimen measurements from this specimen
                    if experiment_name!="":
                        rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                    rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                    measnum+=1
                    SpecOuts.append(rec)
            elif experiment_name=="LP-PI-TRM:LP-PI-ALT-AFARM": # is a Shaw experiment!
                ARM,TRM=0,0
                for rec in NewSpecs: # fix the experiment name for all recs for this specimen and save in SpecOuts
    # assign an experiment name to all specimen measurements from this specimen
    # make the second ARM in Shaw experiments LT-AF-I-2, stick in the AF of ARM and TRM codes
                    meths=rec["magic_method_codes"].split(":")
                    if ARM==1:
                        if "LT-AF-I" in meths:
                            del meths[meths.index("LT-AF-I")]
                            meths.append("LT-AF-I-2")
                            ARM=2
                        if "LT-AF-Z" in meths and TRM==0 :
                            meths.append("LP-ARM-AFD")
                    if TRM==1 and ARM==1:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-TRM-AFD")
                    if ARM==2:
                        if "LT-AF-Z" in meths:
                            meths.append("LP-ARM2-AFD")
                    newcode=""
                    for meth in meths:
                        newcode=newcode+meth+":"
                    rec["magic_method_codes"]=newcode[:-1]
                    if "LT-AF-I" in meths:ARM=1
                    if "LT-T-I" in meths:TRM=1
                    rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                    rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                    measnum+=1
                    SpecOuts.append(rec)
            else:  # not a Thellier-Thellier  or a Shaw experiemnt
                for rec in  NewSpecs: 
                    if experiment_name=="":
                        rec["magic_method_codes"]="LT-NO"
                        rec["magic_experiment_name"]=spec+":LT-NO"
                        rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                        measnum+=1
                    else:
                        if experiment_name not in rec['magic_method_codes']:
                            rec["magic_method_codes"]=rec["magic_method_codes"]+":"+experiment_name
                            rec["magic_method_codes"]=rec["magic_method_codes"].strip(':')
                        rec['measurement_number']='%i'%(measnum)  # assign measurement numbers
                        measnum+=1
                        rec["magic_experiment_name"]=spec+":"+experiment_name
                    rec["magic_software_packages"]=version_num
                    SpecOuts.append(rec)
        else:
            NewSpecs[0]["magic_experiment_name"]=spec+":"+NewSpecs[0]['magic_method_codes'].split(':')[0]
            NewSpecs[0]["magic_software_packages"]=version_num
            SpecOuts.append(NewSpecs[0]) # just copy over the single record as is
    return SpecOuts

def mw_measurements_methods(MagRecs):
# first collect all data for this specimen and do lab treatments
    MD,pMRM,IZ,ZI=0,0,0,0 # these are flags for the lab protocol codes
    expcodes=""
    NewSpecs,SpecMeths=[],[]
    experiment_name=""
    phi,theta="",""
    Dec,Inc="","" # NRM direction
    ZI,IZ,MD,pMRM="","","",""
    k=-1
    POWT_I,POWT_Z=[],[]
    ISteps,ZSteps=[],[]
    k=-1
    for rec in MagRecs:
        k+=1
# ready for pass through, step through specimens, check whether ptrm, ptrm tail checks, or AARM, etc.
#
#
# collect all the experimental data for this specimen
# and look through this specimen's records - try to figure out what experiment it is
#
        meths=rec["magic_method_codes"].split(":")
        powt=int(float(rec["treatment_mw_energy"]))
        for meth in meths:
            if meth not in SpecMeths:SpecMeths.append(meth)  # collect all the methods for this experiment
        if "LT-M-I" in meths: # infield step
            POWT_I.append(powt)
            ISteps.append(k)
            if phi=="": # first one
                phi=float(rec["treatment_dc_field_phi"])
                theta=float(rec["treatment_dc_field_theta"])
        if "LT-M-Z" in meths: # zero field  step
            POWT_Z.append(powt)
            ZSteps.append(k)
            if phi=="": # first one
                Dec=float(rec["measurement_dec"])
                Inc=float(rec["measurement_inc"])
    if "LT-M-I" not in  SpecMeths: # just microwave demag
        experiment_name="LP-DIR-M"
    else: # Microwave infield steps , some sort of LP-PI-M experiment
        experiment_name="LP-PI-M"
        if "LT-PMRM-Z"  in  SpecMeths or "LT-PMRM-I" in SpecMeths: # has pTRM checks
            experiment_name=experiment_name+":LP-PI-ALT-PMRM"
        if Dec!="" and phi!="":
            ang=angle([Dec,Inc],[phi,theta]) # angle between applied field and NRM
            if ang>= 0 and ang< 2: experiment_name=experiment_name+":LP-NRM-PAR"
            if ang> 88 and ang< 92: experiment_name=experiment_name+":LP-NRM-PERP"
            if ang> 178 and ang< 182: experiment_name=experiment_name+":LP-NRM-APAR"
#
# now check whether there are z pairs for all I steps or is this a single heating experiment
#  
        noZ=0
        for powt in POWT_I:
            if powt not in POWT_Z:noZ=1 # some I's missing their Z's
        if noZ==1:
            meths = experiment_name.split(":")
            if  "LP-NRM-PERP" in meths: # this is a single  heating experiment
                experiment_name=experiment_name+":LP-PI-M-S"
            else:
                print "Trouble interpreting file - missing zerofield steps? "
                sys.exit()
        else: # this is a double heating experiment
            experiment_name=experiment_name+":LP-PI-M-D"
  # check for IZ or ZI pairs
            for  istep in ISteps: # look for first zerofield step with this power
                rec=MagRecs[istep]
                powt_i=int(float(rec["treatment_mw_energy"]))
                IZorZI,step="",-1
                while IZorZI =="" and step<len(ZSteps)-1:
                    step+=1
                    zstep=ZSteps[step]
                    zrec=MagRecs[zstep]  
                    powt_z=int(float(zrec["treatment_mw_energy"]))
                    if powt_i==powt_z:  # found a match
                        if zstep < istep: # zero field first
                            IZorZI="LP-PI-M-ZI"
                            ZI=1 # there is at least one ZI step
                            break
                        else: # in field first
                            IZorZI="LP-PI-M-IZ"
                            IZ=1 # there is at least one ZI step
                            break
                if IZorZI!="":
                    MagRecs[istep]['magic_method_codes']= MagRecs[istep]['magic_method_codes']+':'+IZorZI
                    MagRecs[zstep]['magic_method_codes']= MagRecs[zstep]['magic_method_codes']+':'+IZorZI
            print POWT_Z
            print POWT_I
            for  istep in ISteps: # now look for MD checks (zero field)
              if istep+2<len(MagRecs):  # only if there is another step to consider
                irec=MagRecs[istep]
                powt_i=int(float(irec["treatment_mw_energy"]))
                print istep,powt_i,ZSteps[POWT_Z.index(powt_i)]
                if powt_i in POWT_Z and ZSteps[POWT_Z.index(powt_i)] < istep:  # if there is a previous zero field step at same  power
                    nrec=MagRecs[istep+1] # next step
                    nmeths=nrec['magic_method_codes'].split(":")
                    powt_n=int(float(nrec["treatment_mw_energy"]))
                    if 'LT-M-Z' in nmeths and powt_n==powt_i:  # the step after this infield was a zero field at same energy 
                        MD=1  # found a second zero field  match
                        mdmeths=MagRecs[istep+1]['magic_method_codes'].split(":")
                        mdmeths[0]="LT-PMRM-MD" # replace method code with tail check code
                        methods=""
                        for meth in mdmeths:methods=methods+":"+meth
                        MagRecs[istep+1]['magic_method_codes']=methods[1:]
            if MD==1: experiment_name=experiment_name+":LP-PI-BT-MD"
            if IZ==1:
                if ZI==1: 
                    experiment_name=experiment_name+":LP-PI-BT-IZZI"
                else:
                    experiment_name=experiment_name+":LP-PI-M-IZ"
            else:
                if ZI==1: 
                    experiment_name=experiment_name+":LP-PI-M-ZI"
                else:
                    print "problem in measurements_methods - no ZI or IZ in double heating experiment"
                    sys.exit()
    for rec in MagRecs: 
        if 'er_synthetic_name' in rec.keys() and rec['er_synthetic_name']!="":
            rec['magic_experiment_name']=rec['er_synthetic_name']+":"+experiment_name
        else:
            rec['magic_experiment_name']=rec['er_specimen_name']+":"+experiment_name
        rec['magic_method_codes']=rec['magic_method_codes']+":"+experiment_name
    return MagRecs

def parse_site(sample,convention,Z):
    """
    parse the site name from the sample name using the specified convention
    """
    site=sample # default is that site = sample
#
#
# Sample is final letter on site designation eg:  TG001a (used by SIO lab in San Diego)
    if convention=="1":
        return sample[:-1] # peel off terminal character
#
# Site-Sample format eg:  BG94-1  (used by PGL lab in Beijing)
#
    if convention=="2":
        parts=sample.split('-')
        return parts[0]
#
# Sample is XXXX.YY where XXX is site and YY is sample 
#
    if convention=="3":
        parts=sample.split('.')
        return parts[0]
#
# Sample is XXXXYYY where XXX is site desgnation and YYY is Z long integer
#
    if convention=="4":
       k=int(Z)
       return sample[0:-k]  # peel off Z characters from site
    
    if convention=="5": # sample == site
        return sample
    
    if convention=="7": # peel off Z characters for site
       k=int(Z)
       return sample[0:k]  
  
    if convention=="8": # peel off Z characters for site
       return ""
    if convention=="9": # peel off Z characters for site
       return sample

    print "Error in site parsing routine"
    sys.exit()
def get_samp_con():
    """
     get sample naming  convention
    """
#
    samp_con,Z="",""
    while samp_con=="":
        samp_con=raw_input("""
        Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.  	 [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length) 
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.  
            select one:  
""")
    #
        if samp_con=="" or  samp_con =="1":
            samp_con,Z="1",1
        if "4" in samp_con: 
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                samp_con=""
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con: 
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                samp_con=""
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
        if samp_con.isdigit()==False or int(samp_con)>7: 
            print "Try again\n "
            samp_con=""
    return samp_con,Z

def get_tilt(dec_geo,inc_geo,dec_tilt,inc_tilt):
#
    """
    Function to return dip and dip direction used to convert geo to tilt coordinates
    """
# strike is horizontal line equidistant from two input directions
    SCart=[0,0,0] # cartesian coordites of Strike
    SCart[2]=0.  # by definition
    GCart=dir2cart([dec_geo,inc_geo,1.]) # cartesian coordites of Geographic D
    TCart=dir2cart([dec_tilt,inc_tilt,1.]) # cartesian coordites of Tilt D
    X=(TCart[1]-GCart[1])/(GCart[0]-TCart[0])
    SCart[1]=numpy.sqrt(1/(X**2+1.))
    SCart[0]=SCart[1]*X
    SDir=cart2dir(SCart)
    DipDir=(SDir[0]+90.)%360.
# D is creat circle distance between geo direction and strike
# theta is GCD between geo and tilt (on unit sphere).  use law of cosines
# to get small cirlce between geo and tilt (dip)
    cosd = GCart[0]*SCart[0]+GCart[1]*SCart[1]  # cosine of angle between two
    d=numpy.arccos(cosd)
    cosTheta=GCart[0]*TCart[0]+GCart[1]*TCart[1]+GCart[2]*TCart[2]
    Dip =(180./numpy.pi)*numpy.arccos(-((cosd**2-cosTheta)/numpy.sin(d)**2))
    return DipDir,Dip
#
def get_azpl(cdec,cinc,gdec,ginc):
    """
     gets azimuth and pl from specimen dec inc (cdec,cinc) and gdec,ginc (geographic)  coordinates
    """
    TOL=1e-4
    rad=numpy.pi/180.
    Xp=dir2cart([gdec,ginc,1.])
    X=dir2cart([cdec,cinc,1.])
    # find plunge first
    az,pl,zdif,ang=0.,-90.,1.,360.
    while  zdif>TOL and pl<180.:
        znew=X[0]*numpy.sin(pl*rad)+X[2]*numpy.cos(pl*rad)
        zdif=abs(Xp[2]-znew)
        pl+=.01

    while ang>0.1 and az<360.:
        d,i=dogeo(cdec,cinc,az,pl)
        ang=angle([gdec,ginc],[d,i])
        az+=.01
    return az-.01,pl-.01

def set_priorities(SO_methods,ask):
    """
     figure out which sample_azimuth to use, if multiple orientation methods
    """
    # if ask set to 1, then can change priorities
    SO_defaults=['SO-SUN','SO-GPS-DIFF','SO-SIGHT','SO-SIGHT-BS','SO-CMD-NORTH','SO-MAG','SO-SM','SO-REC','SO-V','SO-NO']
    SO_priorities,prior_list=[],[]
    if len(SO_methods) >= 1:
        for l in range(len(SO_defaults)):
            if SO_defaults[l] in SO_methods:
                SO_priorities.append(SO_defaults[l])
    pri,change=0,"1"
    if ask==1:
        print  """These methods of sample orientation were found:  
      They have been assigned a provisional priority (top = zero, last = highest number) """
        for m in range(len(SO_defaults)):
            if SO_defaults[m] in SO_methods:
                SO_priorities[SO_methods.index(SO_defaults[m])]=pri
                pri+=1
        while change=="1":
            prior_list=SO_priorities 
            for m in range(len(SO_methods)):
                print SO_methods[m],SO_priorities[m]
            change=raw_input("Change these?  1/[0] ")
            if change!="1":break
        SO_priorities=[]
        for l in range(len(SO_methods)):
             print SO_methods[l]
             print " Priority?   ",prior_list
             pri=int(raw_input())
             SO_priorities.append(pri)
             del prior_list[prior_list.index(pri)]
    return SO_priorities
#
# 
def get_EOL(file):
    """
     find EOL of input file (whether mac,PC or unix format)
    """
    f=open(file,'r')
    firstline=f.read(350)
    EOL=""
    for k in range(350):
        if firstline[k:k+2] == "\r\n":
            print file, ' appears to be a dos file'
            EOL='\r\n'
            break
    if EOL=="":
        for k in range(350):
            if firstline[k] == "\r":
                print file, ' appears to be a mac file'
                EOL='\r'
    if EOL=="":
        print file, " appears to be a  unix file"
        EOL='\n'
    f.close()
    return EOL
# 
def sortshaw(s,datablock):
    """
     sorts data block in to ARM1,ARM2 NRM,TRM,ARM1,ARM2=[],[],[],[]
     stick  first zero field stuff into first_Z 
    """
    for rec in datablock:
        methcodes=rec["magic_method_codes"].split(":")
        step=float(rec["treatment_ac_field"])
        str=float(rec["measurement_magn_moment"])
        if "LT-NO" in methcodes:
            NRM.append([0,str])
        if "LT-T-I" in methcodes:
            TRM.append([0,str])
            field=float(rec["treatment_dc_field"])
        if "LT-AF-I" in methcodes:
            ARM1.append([0,str])
        if "LT-AF-I-2" in methcodes:
            ARM2.append([0,str])
        if "LT-AF-Z" in methcodes:
            if "LP-ARM-AFD" in methcodes:
                ARM1.append([step,str])
            elif "LP-TRM-AFD" in methcodes:
                TRM.append([step,str])
            elif "LP-ARM2-AFD" in methcodes:
                ARM2.append([step,str])
            else:
                NRM.append([step,str])
    cont=1
    while cont==1:
        if len(NRM)!=len(TRM):
            print "Uneven NRM/TRM steps: "
            NRM,TRM,cont=cleanup(TRM,NRM)
        else:cont=0
    cont=1
    while cont==1:
        if len(ARM1)!=len(ARM2):
            print "Uneven ARM1/ARM2 steps: "
            ARM1,ARM2,cont=cleanup(ARM2,ARM1)
        else:cont=0
#
# final check
#
    if len(NRM)!=len(TRM) or len(ARM1)!=len(ARM2):
               print len(NRM),len(TRM),len(ARM1),len(ARM2)
               print " Something wrong with this specimen! Better fix it or delete it "
               raw_input(" press return to acknowledge message")
# now do the ratio to "fix" NRM/TRM data
# a
    TRM_ADJ=[]
    for kk in range(len(TRM)):
        step=TRM[kk][0]
        for k in range(len(ARM1)):
            if  ARM1[k][0]==step:
                TRM_ADJ.append([step,TRM[kk][1]*ARM1[k][1]/ARM2[k][1]])
                break
    shawblock=(NRM,TRM,ARM1,ARM2,TRM_ADJ)
    return shawblock,field
#
#
def makelist(List):
    """
     makes a colon delimited list from List
    """
    clist=""
    for element in List:
        clist=clist+element+":"
    return clist[:-1]
#
def getvec(gh,lat,long):
#
    """
       evaluates the vector at a given latitude (long=0) for a specified set of coefficients
        Lisa Tauxe 2/26/2007
    """

#
#
    sv=[]
    pad=120-len(gh)
    for x in range(pad):gh.append(0.)
    for x in range(len(gh)):sv.append(0.)
#! convert to colatitude for MB routine
    itype = 1 
    colat = 90.-lat
    date,alt=2000.,0. # use a dummy date and altitude
    x,y,z,f=magsyn(gh,sv,date,date,itype,alt,colat,long)
    vec=cart2dir([x,y,z])
    vec[2]=f
    return vec
#
def s_l(l,alpha):
    """
    get sigma as a function of degree l from Constable and Parker (1988)
    """
    a2=alpha**2
    c_a=0.547
    s_l=numpy.sqrt(((c_a**(2.*l))*a2)/((l+1.)*(2.*l+1.)))
    return s_l
#
def mktk03(terms,seed,G2,G3):
    """
    generates a list of gauss coefficients drawn from the TK03.gad distribution
    """
#random.seed(n)
    p=0
    n=seed
    gh=[]
    g10,sfact,afact=-18e3,3.8,2.4
    g20=G2*g10
    g30=G3*g10
    alpha=g10/afact
    s1=s_l(1,alpha)
    s10=sfact*s1
    gnew=random.normal(g10,s10)
    if p==1:print 1,0,gnew,0
    gh.append(gnew)
    gh.append(random.normal(0,s1))
    gnew=gh[-1]
    gh.append(random.normal(0,s1))
    hnew=gh[-1]
    if p==1:print 1,1,gnew,hnew
    for l in range(2,terms+1):
        for m in range(l+1):
            OFF=0.0
            if l==2 and m==0:OFF=g20
            if l==3 and m==0:OFF=g30
            s=s_l(l,alpha)
            j=(l-m)%2
            if j==1:
                s=s*sfact
            gh.append(random.normal(OFF,s))
            gnew=gh[-1]
            if m==0:
                hnew=0
            else: 
                gh.append(random.normal(0,s))
                hnew=gh[-1]
            if p==1:print l,m,gnew,hnew
    return gh
#
#
def pinc(lat):
    """
    calculate paleoinclination from latitude
    """
    rad = numpy.pi/180.
    tanl=numpy.tan(lat*rad)
    inc=numpy.arctan(2.*tanl)
    return inc/rad
#
def plat(inc):
    """
    calculate paleolat from inclination
    """
    rad = numpy.pi/180.
    tani=numpy.tan(inc*rad)
    lat=numpy.arctan(tani/2.)
    return lat/rad
#
#
def pseudo(DIs):
    """
     draw a bootstrap sample of Directions
    """
#
    Inds=numpy.random.randint(len(DIs),size=len(DIs))
    D=numpy.array(DIs)
    return D[Inds]
#
def di_boot(DIs):
    """
     returns bootstrap parameters for Directional data
    """
# get average DI for whole dataset
    fpars=fisher_mean(DIs)
#
# now do bootstrap to collect BDIs  bootstrap means
#
    nb,BDIs=5000,[]  # number of bootstraps, list of bootstrap directions
#
    
    for k in range(nb): # repeat nb times
#        if k%50==0:print k,' out of ',nb
        pDIs= pseudo(DIs) # get a pseudosample 
        bfpars=fisher_mean(pDIs) # get bootstrap mean bootstrap sample
        BDIs.append([bfpars['dec'],bfpars['inc']])
    return BDIs

def pseudosample(x):
    """
     draw a bootstrap sample of x
    """
#
    BXs=[]
    for k in range(len(x)):
        ind=random.randint(0,len(x)-1)
        BXs.append(x[ind])
    return BXs 

def get_plate_data(plate):
    """
    returns the pole list for a given plate"
    """
    if plate=='AF':
       apwp="""
0.0        90.00    0.00
1.0        88.38  182.20
2.0        86.76  182.20
3.0        86.24  177.38
4.0        86.08  176.09
5.0        85.95  175.25
6.0        85.81  174.47
7.0        85.67  173.73
8.0        85.54  173.04
9.0        85.40  172.39
10.0       85.26  171.77
11.0       85.12  171.19
12.0       84.97  170.71
13.0       84.70  170.78
14.0       84.42  170.85
15.0       84.10  170.60
16.0       83.58  169.22
17.0       83.06  168.05
18.0       82.54  167.05
19.0       82.02  166.17
20.0       81.83  166.63
21.0       82.13  169.10
22.0       82.43  171.75
23.0       82.70  174.61
24.0       82.96  177.69
25.0       83.19  180.98
26.0       83.40  184.50
27.0       82.49  192.38
28.0       81.47  198.49
29.0       80.38  203.25
30.0       79.23  207.04
31.0       78.99  206.32
32.0       78.96  204.60
33.0       78.93  202.89
34.0       78.82  201.05
35.0       78.54  198.97
36.0       78.25  196.99
37.0       77.95  195.10
38.0       77.63  193.30
39.0       77.30  191.60
40.0       77.56  192.66
41.0       77.81  193.77
42.0       78.06  194.92
43.0       78.31  196.13
44.0       78.55  197.38
45.0       78.78  198.68
46.0       79.01  200.04
47.0       79.03  201.22
48.0       78.92  202.23
49.0       78.81  203.22
50.0       78.67  204.34
51.0       78.30  206.68
52.0       77.93  208.88
53.0       77.53  210.94
54.0       77.12  212.88
55.0       76.70  214.70
56.0       76.24  216.60
57.0       75.76  218.37
58.0       75.27  220.03
59.0       74.77  221.58
60.0       74.26  223.03
61.0       73.71  225.04
62.0       73.06  228.34
63.0       72.35  231.38
64.0       71.60  234.20
65.0       71.49  234.96
66.0       71.37  235.71
67.0       71.26  236.45
68.0       71.14  237.18
69.0       71.24  236.94
70.0       71.45  236.27
71.0       71.65  235.59
72.0       71.85  234.89
73.0       72.04  234.17
74.0       72.23  233.45
75.0       72.42  232.70
76.0       71.97  236.12
77.0       70.94  241.83
78.0       69.76  246.94
79.0       68.44  251.48
80.0       68.01  252.16
81.0       67.68  252.45
82.0       67.36  252.72
83.0       67.03  252.99
84.0       66.91  252.32
85.0       66.91  251.01
86.0       66.91  249.71
87.0       66.89  248.40
88.0       66.87  247.10
89.0       66.83  245.80
90.0       66.78  244.50
91.0       66.73  243.21
92.0       66.66  243.44
93.0       66.59  244.66
94.0       66.51  245.88
95.0       66.86  247.10
96.0       67.26  248.35
97.0       67.64  249.65
98.0       68.02  250.99
99.0       68.38  252.38
100.0      68.73  253.81
101.0      67.73  253.53
102.0      66.39  252.89
103.0      65.05  252.31
104.0      63.71  251.79
105.0      62.61  252.26
106.0      61.86  254.08
107.0      61.10  255.82
108.0      60.31  257.47
109.0      59.50  259.05
110.0      58.67  260.55
111.0      57.94  261.67
112.0      57.64  261.52
113.0      57.33  261.38
114.0      57.03  261.23
115.0      56.73  261.09
116.0      56.42  260.95
117.0      55.57  260.90
118.0      54.35  260.90
119.0      53.14  260.90
120.0      51.92  260.90
121.0      51.40  260.83
122.0      50.96  260.76
123.0      50.58  260.83
124.0      50.45  261.47
125.0      50.32  262.11
126.0      50.19  262.74
127.0      50.06  263.37
128.0      49.92  264.00
129.0      49.78  264.62
130.0      49.63  265.25
131.0      49.50  265.76
132.0      49.50  265.41
133.0      49.50  265.06
134.0      49.50  264.71
135.0      48.67  264.80
136.0      47.50  265.07
137.0      46.32  265.34
138.0      45.14  265.59
139.0      43.95  265.83
140.0      42.75  265.17
141.0      41.53  264.17
142.0      40.30  263.20
143.0      41.89  262.76
144.0      43.49  262.29
145.0      45.08  261.80
146.0      46.67  261.29
147.0      48.25  260.74
148.0      49.84  260.15
149.0      51.42  259.53
150.0      52.99  258.86
151.0      54.57  258.14
152.0      56.14  257.37
153.0      57.70  256.52
154.0      59.05  255.88
155.0      58.56  257.68
156.0      57.79  258.80
157.0      56.41  258.47
158.0      55.04  258.16
159.0      53.78  257.93
160.0      53.60  258.23
161.0      53.41  258.52
162.0      53.23  258.81
163.0      53.04  259.10
164.0      52.85  259.38
165.0      52.67  259.67
166.0      52.48  259.95
167.0      52.29  260.22
168.0      52.10  260.50
169.0      54.10  259.90
170.0      56.10  259.24
171.0      57.63  259.26
172.0      59.05  259.48
173.0      60.47  259.71
174.0      61.88  259.97
175.0      63.30  260.25
176.0      64.71  260.56
177.0      65.90  261.33
178.0      66.55  263.15
179.0      67.21  263.56
180.0      67.88  262.97
181.0      68.56  262.34
182.0      69.23  261.68
183.0      69.06  261.18
184.0      68.32  260.84
185.0      67.58  260.53
186.0      66.84  260.23
187.0      66.09  259.95
188.0      65.35  259.68
189.0      64.61  259.43
190.0      63.87  259.19
191.0      63.12  258.97
192.0      62.63  258.67
193.0      62.24  258.34
194.0      61.86  258.02
195.0      62.06  256.25
196.0      62.62  253.40
197.0      63.13  250.46
198.0      63.56  247.41
"""
    if plate=='ANT':
       apwp="""
0.0        90.00    0.00
1.0        88.48  178.80
2.0        86.95  178.80
3.0        86.53  172.26
4.0        86.46  169.30
5.0        86.41  166.81
6.0        86.35  164.39
7.0        86.29  162.05
8.0        86.22  159.79
9.0        86.15  157.62
10.0       86.07  155.53
11.0       85.98  153.53
12.0       85.88  151.77
13.0       85.63  151.47
14.0       85.39  151.20
15.0       85.10  150.74
16.0       84.60  149.57
17.0       84.10  148.60
18.0       83.60  147.78
19.0       83.10  147.07
20.0       82.99  146.90
21.0       83.46  147.46
22.0       83.93  148.10
23.0       84.40  148.85
24.0       84.87  149.74
25.0       85.34  150.80
26.0       85.80  152.10
27.0       85.57  166.36
28.0       85.09  178.53
29.0       84.44  188.22
30.0       83.67  195.72
31.0       83.55  194.37
32.0       83.58  191.03
33.0       83.60  187.66
34.0       83.52  184.03
35.0       83.23  180.01
36.0       82.91  176.34
37.0       82.56  172.99
38.0       82.19  169.96
39.0       81.80  167.20
40.0       82.22  166.10
41.0       82.64  164.87
42.0       83.05  163.49
43.0       83.46  161.94
44.0       83.86  160.19
45.0       84.26  158.20
46.0       84.65  155.91
47.0       84.85  155.14
48.0       84.94  155.56
49.0       85.02  156.00
50.0       85.11  156.86
51.0       85.22  161.60
52.0       85.29  166.52
53.0       85.33  171.57
54.0       85.33  176.65
55.0       85.30  181.70
56.0       85.23  187.68
57.0       85.11  193.43
58.0       84.94  198.85
59.0       84.74  203.89
60.0       84.49  208.51
61.0       84.23  214.70
62.0       83.87  224.68
63.0       83.35  233.34
64.0       82.70  240.60
65.0       82.75  243.15
66.0       82.78  245.72
67.0       82.80  248.32
68.0       82.80  250.92
69.0       83.19  251.41
70.0       83.74  250.94
71.0       84.29  250.38
72.0       84.84  249.70
73.0       85.39  248.86
74.0       85.94  247.79
75.0       86.48  246.39
76.0       86.07  261.42
77.0       84.60  277.45
78.0       82.89  286.25
79.0       81.08  291.58
80.0       80.93  293.29
81.0       80.96  294.72
82.0       80.98  296.17
83.0       81.00  297.62
84.0       81.51  298.75
85.0       82.37  299.83
86.0       83.22  301.18
87.0       84.06  302.91
88.0       84.90  305.21
89.0       85.73  308.41
90.0       86.54  313.11
91.0       87.31  320.59
92.0       87.40  334.40
93.0       86.93  346.81
94.0       86.36  355.67
95.0       85.61    7.48
96.0       84.70   16.06
97.0       83.71   22.06
98.0       82.68   26.39
99.0       81.61   29.65
100.0      80.52   32.16
101.0      80.70   31.28
102.0      81.18   29.47
103.0      81.66   27.45
104.0      82.13   25.19
105.0      82.14   22.30
106.0      81.49   19.18
107.0      80.81   16.51
108.0      80.11   14.20
109.0      79.40   12.20
110.0      78.68   10.45
111.0      78.05    9.62
112.0      77.79   11.65
113.0      77.52   13.60
114.0      77.23   15.46
115.0      76.94   17.24
116.0      76.63   18.94
117.0      76.60   18.39
118.0      76.74   16.34
119.0      76.88   14.25
120.0      76.99   12.12
121.0      76.94   12.67
122.0      76.86   13.53
123.0      76.68   14.35
124.0      76.08   15.08
125.0      75.48   15.75
126.0      74.88   16.36
127.0      74.27   16.93
128.0      73.66   17.46
129.0      73.06   17.95
130.0      72.45   18.41
131.0      71.90   18.79
132.0      71.87   18.70
133.0      71.84   18.61
134.0      71.81   18.53
135.0      71.81   15.55
136.0      71.74   11.34
137.0      71.59    7.18
138.0      71.34    3.11
139.0      71.01  359.16
140.0      71.25  355.22
141.0      71.67  351.10
142.0      72.00  346.80
143.0      72.09  352.56
144.0      72.01  358.32
145.0      71.77    3.99
146.0      71.36    9.46
147.0      70.80   14.67
148.0      70.10   19.55
149.0      69.28   24.10
150.0      68.35   28.28
151.0      67.32   32.13
152.0      66.21   35.64
153.0      65.02   38.85
154.0      63.85   41.25
155.0      63.30   38.84
156.0      63.13   36.67
157.0      63.86   34.84
158.0      64.58   32.92
159.0      65.17   31.04
160.0      64.92   30.50
161.0      64.66   29.97
162.0      64.40   29.44
163.0      64.14   28.93
164.0      63.87   28.43
165.0      63.61   27.93
166.0      63.34   27.44
167.0      63.07   26.97
168.0      62.80   26.50
169.0      61.86   30.42
170.0      60.82   34.09
171.0      59.74   36.31
172.0      58.64   38.08
173.0      57.52   39.75
174.0      56.37   41.31
175.0      55.21   42.78
176.0      54.03   44.17
177.0      52.92   45.01
178.0      51.98   44.71
179.0      51.38   45.20
180.0      51.02   46.19
181.0      50.64   47.16
182.0      50.26   48.12
183.0      50.50   48.18
184.0      51.16   47.63
185.0      51.82   47.07
186.0      52.47   46.49
187.0      53.13   45.89
188.0      53.78   45.28
189.0      54.43   44.64
190.0      55.07   43.98
191.0      55.71   43.31
192.0      56.19   42.92
193.0      56.61   42.67
194.0      57.03   42.41
195.0      57.37   43.88
196.0      57.62   46.54
197.0      57.80   49.23
198.0      57.93   51.94
"""
    if plate=='AU':
       apwp="""
0.0        90.00    0.00
1.0        88.81  204.00
2.0        87.62  204.00
3.0        87.50  207.24
4.0        87.58  216.94
5.0        87.58  227.69
6.0        87.51  238.13
7.0        87.35  247.65
8.0        87.14  255.93
9.0        86.87  262.92
10.0       86.56  268.74
11.0       86.22  273.56
12.0       85.87  277.29
13.0       85.52  278.11
14.0       85.18  278.81
15.0       84.87  279.00
16.0       84.71  277.55
17.0       84.54  276.18
18.0       84.37  274.90
19.0       84.20  273.69
20.0       83.80  275.43
21.0       83.01  280.56
22.0       82.18  284.64
23.0       81.31  287.92
24.0       80.42  290.60
25.0       79.52  292.83
26.0       78.60  294.70
27.0       77.32  290.94
28.0       76.00  287.87
29.0       74.65  285.33
30.0       73.28  283.19
31.0       72.98  283.37
32.0       72.95  284.09
33.0       72.92  284.80
34.0       72.92  285.21
35.0       72.97  284.91
36.0       73.03  284.61
37.0       73.09  284.31
38.0       73.14  284.01
39.0       73.20  283.70
40.0       72.83  285.38
41.0       72.45  286.99
42.0       72.06  288.54
43.0       71.65  290.02
44.0       71.24  291.44
45.0       70.81  292.80
46.0       70.38  294.10
47.0       70.08  294.79
48.0       69.88  295.11
49.0       69.68  295.42
50.0       69.46  295.67
51.0       69.01  295.35
52.0       68.55  295.05
53.0       68.10  294.75
54.0       67.65  294.47
55.0       67.20  294.20
56.0       66.69  293.91
57.0       66.18  293.63
58.0       65.68  293.37
59.0       65.17  293.11
60.0       64.66  292.87
61.0       63.96  292.74
62.0       62.84  292.87
63.0       61.72  292.99
64.0       60.60  293.10
65.0       60.35  293.65
66.0       60.09  294.19
67.0       59.84  294.72
68.0       59.58  295.24
69.0       59.76  295.88
70.0       60.14  296.57
71.0       60.51  297.28
72.0       60.88  298.00
73.0       61.24  298.75
74.0       61.60  299.51
75.0       61.96  300.28
76.0       60.92  301.16
77.0       58.95  302.00
78.0       56.98  302.76
79.0       55.00  303.44
80.0       54.72  303.90
81.0       54.63  304.34
82.0       54.53  304.79
83.0       54.44  305.22
84.0       54.82  305.66
85.0       55.51  306.11
86.0       56.20  306.57
87.0       56.89  307.05
88.0       57.58  307.55
89.0       58.26  308.07
90.0       58.95  308.61
91.0       59.63  309.17
92.0       59.80  310.34
93.0       59.62  311.90
94.0       59.42  313.45
95.0       59.46  315.65
96.0       59.50  317.94
97.0       59.49  320.23
98.0       59.44  322.51
99.0       59.36  324.79
100.0      59.23  327.05
101.0      59.10  326.62
102.0      58.98  325.52
103.0      58.84  324.43
104.0      58.69  323.34
105.0      58.29  322.95
106.0      57.53  323.57
107.0      56.75  324.16
108.0      55.98  324.73
109.0      55.20  325.27
110.0      54.42  325.80
111.0      53.81  326.35
112.0      53.88  327.12
113.0      53.94  327.88
114.0      53.99  328.65
115.0      54.04  329.42
116.0      54.08  330.19
117.0      53.91  330.07
118.0      53.59  329.36
119.0      53.26  328.66
120.0      52.93  327.97
121.0      52.97  328.13
122.0      53.04  328.39
123.0      53.03  328.78
124.0      52.70  329.69
125.0      52.35  330.59
126.0      52.00  331.47
127.0      51.65  332.34
128.0      51.29  333.20
129.0      50.92  334.04
130.0      50.54  334.87
131.0      50.18  335.59
132.0      50.01  335.53
133.0      49.83  335.48
134.0      49.65  335.42
135.0      48.86  334.35
136.0      47.78  332.89
137.0      46.68  331.50
138.0      45.57  330.16
139.0      44.44  328.88
140.0      43.86  327.11
141.0      43.50  325.14
142.0      43.10  323.20
143.0      44.00  325.32
144.0      44.85  327.50
145.0      45.66  329.75
146.0      46.43  332.06
147.0      47.15  334.44
148.0      47.81  336.88
149.0      48.43  339.38
150.0      48.99  341.94
151.0      49.49  344.55
152.0      49.93  347.22
153.0      50.31  349.93
154.0      50.48  352.37
155.0      49.32  352.03
156.0      48.45  351.31
157.0      48.28  349.67
158.0      48.09  348.05
159.0      47.87  346.61
160.0      47.53  346.69
161.0      47.19  346.77
162.0      46.84  346.85
163.0      46.50  346.93
164.0      46.16  347.00
165.0      45.82  347.08
166.0      45.48  347.15
167.0      45.14  347.23
168.0      44.80  347.30
169.0      45.48  349.99
170.0      46.09  352.74
171.0      46.20  354.95
172.0      46.16  357.01
173.0      46.09  359.07
174.0      45.98    1.12
175.0      45.83    3.16
176.0      45.65    5.19
177.0      45.27    6.85
178.0      44.51    7.68
179.0      44.31    8.58
180.0      44.50    9.55
181.0      44.67   10.52
182.0      44.84   11.51
183.0      45.02   11.29
184.0      45.22   10.27
185.0      45.42    9.24
186.0      45.60    8.20
187.0      45.77    7.16
188.0      45.93    6.11
189.0      46.09    5.05
190.0      46.23    3.99
191.0      46.36    2.92
192.0      46.52    2.20
193.0      46.68    1.62
194.0      46.84    1.03
195.0      47.67    1.40
196.0      48.95    2.45
197.0      50.22    3.54
198.0      51.48    4.70
"""
    if plate=='EU':
       apwp="""
0.0        90.00    0.00
1.0        88.43  178.70
2.0        86.86  178.70
3.0        86.34  172.60
4.0        86.18  169.84
5.0        86.05  167.60
6.0        85.91  165.51
7.0        85.77  163.55
8.0        85.62  161.73
9.0        85.46  160.03
10.0       85.31  158.44
11.0       85.15  156.95
12.0       84.97  155.67
13.0       84.70  155.37
14.0       84.42  155.10
15.0       84.08  154.59
16.0       83.51  153.18
17.0       82.92  152.01
18.0       82.34  151.01
19.0       81.75  150.16
20.0       81.55  149.86
21.0       81.93  150.29
22.0       82.30  150.76
23.0       82.68  151.28
24.0       83.05  151.85
25.0       83.43  152.49
26.0       83.80  153.20
27.0       83.47  162.05
28.0       83.00  169.89
29.0       82.41  176.64
30.0       81.74  182.37
31.0       81.53  181.04
32.0       81.43  178.14
33.0       81.30  175.32
34.0       81.08  172.47
35.0       80.66  169.55
36.0       80.22  166.89
37.0       79.76  164.46
38.0       79.29  162.23
39.0       78.80  160.20
40.0       79.13  159.12
41.0       79.45  157.97
42.0       79.77  156.75
43.0       80.08  155.46
44.0       80.39  154.08
45.0       80.69  152.62
46.0       80.98  151.05
47.0       81.13  150.65
48.0       81.19  151.08
49.0       81.25  151.51
50.0       81.31  152.21
51.0       81.38  155.38
52.0       81.43  158.60
53.0       81.44  161.83
54.0       81.44  165.08
55.0       81.40  168.30
56.0       81.33  172.18
57.0       81.22  175.97
58.0       81.07  179.66
59.0       80.89  183.21
60.0       80.67  186.61
61.0       80.49  190.87
62.0       80.37  197.35
63.0       80.14  203.60
64.0       79.80  209.50
65.0       79.85  210.35
66.0       79.90  211.20
67.0       79.94  212.07
68.0       79.99  212.94
69.0       80.20  211.11
70.0       80.46  207.98
71.0       80.69  204.68
72.0       80.89  201.23
73.0       81.05  197.65
74.0       81.18  193.94
75.0       81.27  190.14
76.0       81.59  195.53
77.0       81.79  207.82
78.0       81.61  220.13
79.0       81.07  231.45
80.0       81.02  232.09
81.0       81.05  231.62
82.0       81.07  231.16
83.0       81.09  230.69
84.0       81.26  227.31
85.0       81.47  221.76
86.0       81.59  216.00
87.0       81.63  210.12
88.0       81.58  204.25
89.0       81.45  198.51
90.0       81.23  192.99
91.0       80.94  187.78
92.0       81.02  185.31
93.0       81.39  184.44
94.0       81.76  183.50
95.0       82.43  179.95
96.0       83.10  175.40
97.0       83.71  169.92
98.0       84.25  163.35
99.0       84.71  155.53
100.0      85.05  146.45
101.0      84.53  152.65
102.0      83.71  160.59
103.0      82.79  166.60
104.0      81.81  171.23
105.0      81.32  175.20
106.0      81.60  179.66
107.0      81.82  184.38
108.0      81.98  189.32
109.0      82.08  194.43
110.0      82.12  199.63
111.0      82.03  203.00
112.0      81.66  199.22
113.0      81.26  195.76
114.0      80.83  192.62
115.0      80.37  189.76
116.0      79.90  187.17
117.0      79.19  187.67
118.0      78.34  189.84
119.0      77.47  191.71
120.0      76.59  193.35
121.0      76.23  193.12
122.0      75.94  192.71
123.0      75.74  192.46
124.0      75.95  192.77
125.0      76.16  193.09
126.0      76.38  193.42
127.0      76.59  193.76
128.0      76.79  194.12
129.0      77.00  194.48
130.0      77.21  194.85
131.0      77.38  195.04
132.0      77.22  193.47
133.0      77.04  191.93
134.0      76.86  190.44
135.0      76.26  192.29
136.0      75.46  195.27
137.0      74.62  197.94
138.0      73.76  200.34
139.0      72.87  202.49
140.0      71.59  202.74
141.0      70.15  202.29
142.0      68.70  201.90
143.0      69.87  198.07
144.0      70.94  193.81
145.0      71.91  189.09
146.0      72.75  183.89
147.0      73.44  178.23
148.0      73.97  172.14
149.0      74.31  165.73
150.0      74.47  159.11
151.0      74.42  152.44
152.0      74.17  145.90
153.0      73.74  139.63
154.0      73.26  134.46
155.0      73.88  136.15
156.0      74.11  138.70
157.0      73.41  142.81
158.0      72.65  146.58
159.0      71.89  149.70
160.0      71.74  149.67
161.0      71.60  149.65
162.0      71.46  149.63
163.0      71.31  149.61
164.0      71.17  149.58
165.0      71.03  149.56
166.0      70.89  149.54
167.0      70.74  149.52
168.0      70.60  149.50
169.0      70.64  140.48
170.0      70.23  131.62
171.0      69.98  125.23
172.0      69.67  119.51
173.0      69.17  114.01
174.0      68.51  108.79
175.0      67.69  103.90
176.0      66.74   99.36
177.0      66.01   95.57
178.0      66.01   92.81
179.0      65.66   91.06
180.0      65.09   90.02
181.0      64.52   89.02
182.0      63.93   88.07
183.0      63.89   88.62
184.0      64.20   90.17
185.0      64.49   91.77
186.0      64.77   93.39
187.0      65.02   95.05
188.0      65.26   96.73
189.0      65.48   98.45
190.0      65.67  100.19
191.0      65.85  101.96
192.0      65.88  103.25
193.0      65.85  104.31
194.0      65.82  105.38
195.0      64.95  105.43
196.0      63.53  104.86
197.0      62.11  104.35
198.0      60.68  103.89
"""
    if plate=='GL':
       apwp="""
0.0        90.00    0.00
1.0        88.33  180.70
2.0        86.67  180.70
3.0        86.14  175.33
4.0        85.95  173.39
5.0        85.79  171.94
6.0        85.62  170.59
7.0        85.45  169.35
8.0        85.28  168.19
9.0        85.11  167.12
10.0       84.94  166.12
11.0       84.76  165.19
12.0       84.57  164.34
13.0       84.22  163.81
14.0       83.88  163.34
15.0       83.49  162.61
16.0       82.96  160.83
17.0       82.42  159.31
18.0       81.88  157.98
19.0       81.33  156.83
20.0       81.12  156.68
21.0       81.41  157.94
22.0       81.70  159.28
23.0       81.98  160.72
24.0       82.26  162.26
25.0       82.53  163.92
26.0       82.80  165.70
27.0       82.16  172.55
28.0       81.43  178.31
29.0       80.63  183.13
30.0       79.78  187.17
31.0       79.55  186.15
32.0       79.47  183.99
33.0       79.37  181.86
34.0       79.20  179.58
35.0       78.84  176.94
36.0       78.45  174.48
37.0       78.05  172.17
38.0       77.63  170.01
39.0       77.20  168.00
40.0       77.40  168.23
41.0       77.61  168.47
42.0       77.81  168.71
43.0       78.01  168.97
44.0       78.21  169.23
45.0       78.42  169.50
46.0       78.62  169.78
47.0       78.58  170.26
48.0       78.38  170.84
49.0       78.18  171.41
50.0       77.97  172.10
51.0       77.62  174.07
52.0       77.26  175.92
53.0       76.88  177.68
54.0       76.50  179.33
55.0       76.10  180.90
56.0       75.72  182.56
57.0       75.33  184.14
58.0       74.93  185.63
59.0       74.52  187.05
60.0       74.10  188.40
61.0       73.71  190.34
62.0       73.39  193.73
63.0       73.02  196.99
64.0       72.60  200.10
65.0       72.58  200.61
66.0       72.56  201.13
67.0       72.53  201.64
68.0       72.51  202.15
69.0       72.64  201.35
70.0       72.83  199.97
71.0       73.02  198.55
72.0       73.19  197.11
73.0       73.35  195.64
74.0       73.50  194.14
75.0       73.65  192.62
76.0       73.70  196.06
77.0       73.52  202.77
78.0       73.14  209.26
79.0       72.57  215.41
80.0       72.42  216.02
81.0       72.32  216.04
82.0       72.23  216.07
83.0       72.14  216.09
84.0       72.16  214.56
85.0       72.23  211.98
86.0       72.27  209.39
87.0       72.28  206.78
88.0       72.25  204.19
89.0       72.19  201.60
90.0       72.09  199.04
91.0       71.96  196.50
92.0       72.14  195.56
93.0       72.55  195.67
94.0       72.96  195.79
95.0       73.76  195.21
96.0       74.60  194.49
97.0       75.44  193.69
98.0       76.28  192.80
99.0       77.11  191.79
100.0      77.94  190.65
101.0      77.17  190.62
102.0      76.01  190.85
103.0      74.85  191.04
104.0      73.70  191.21
105.0      73.00  192.27
106.0      72.98  194.70
107.0      72.94  197.12
108.0      72.86  199.52
109.0      72.76  201.90
110.0      72.62  204.25
111.0      72.45  205.69
112.0      72.21  203.68
113.0      71.94  201.72
114.0      71.66  199.82
115.0      71.35  197.98
116.0      71.03  196.20
117.0      70.33  195.81
118.0      69.39  196.30
119.0      68.44  196.75
120.0      67.49  197.16
121.0      67.17  196.83
122.0      66.91  196.42
123.0      66.74  196.16
124.0      66.92  196.46
125.0      67.11  196.77
126.0      67.30  197.09
127.0      67.48  197.41
128.0      67.67  197.73
129.0      67.85  198.06
130.0      68.04  198.39
131.0      68.19  198.60
132.0      68.11  197.59
133.0      68.02  196.59
134.0      67.93  195.60
135.0      67.26  196.33
136.0      66.33  197.70
137.0      65.39  198.98
138.0      64.45  200.17
139.0      63.49  201.28
140.0      62.22  201.09
141.0      60.81  200.42
142.0      59.40  199.80
143.0      60.73  197.43
144.0      62.01  194.85
145.0      63.24  192.06
146.0      64.41  189.02
147.0      65.52  185.72
148.0      66.54  182.13
149.0      67.48  178.26
150.0      68.32  174.08
151.0      69.04  169.61
152.0      69.64  164.86
153.0      70.11  159.86
154.0      70.43  155.41
155.0      70.72  157.56
156.0      70.56  159.72
157.0      69.42  161.65
158.0      68.26  163.38
159.0      67.19  164.78
160.0      67.04  164.60
161.0      66.90  164.42
162.0      66.76  164.24
163.0      66.62  164.06
164.0      66.47  163.88
165.0      66.33  163.71
166.0      66.19  163.54
167.0      66.04  163.37
168.0      65.90  163.20
169.0      67.23  156.43
170.0      68.24  148.97
171.0      69.04  143.36
172.0      69.69  138.01
173.0      70.17  132.36
174.0      70.47  126.50
175.0      70.57  120.51
176.0      70.48  114.53
177.0      70.45  109.51
178.0      70.93  106.46
179.0      70.89  104.04
180.0      70.54  102.15
181.0      70.16  100.33
182.0      69.76   98.58
183.0      69.64   99.18
184.0      69.68  101.32
185.0      69.70  103.47
186.0      69.69  105.62
187.0      69.65  107.76
188.0      69.59  109.89
189.0      69.50  112.01
190.0      69.39  114.11
191.0      69.25  116.18
192.0      69.07  117.58
193.0      68.88  118.69
194.0      68.68  119.77
195.0      67.88  118.87
196.0      66.66  116.82
197.0      65.42  114.97
198.0      64.15  113.29
"""
    if plate=='IN':
       apwp="""
0.0        90.00    0.00
1.0        88.57  197.10
2.0        87.14  197.10
3.0        86.82  197.10
4.0        86.76  201.35
5.0        86.70  205.94
6.0        86.62  210.32
7.0        86.52  214.48
8.0        86.40  218.38
9.0        86.26  222.02
10.0       86.11  225.39
11.0       85.95  228.51
12.0       85.77  231.10
13.0       85.46  231.14
14.0       85.15  231.18
15.0       84.84  230.71
16.0       84.54  228.40
17.0       84.23  226.34
18.0       83.92  224.49
19.0       83.59  222.82
20.0       83.40  225.11
21.0       83.32  233.06
22.0       83.11  240.67
23.0       82.79  247.72
24.0       82.37  254.09
25.0       81.87  259.74
26.0       81.30  264.70
27.0       79.78  264.31
28.0       78.25  264.03
29.0       76.73  263.81
30.0       75.20  263.63
31.0       74.95  264.21
32.0       75.01  264.98
33.0       75.06  265.75
34.0       75.09  266.19
35.0       75.05  265.83
36.0       75.02  265.47
37.0       74.98  265.11
38.0       74.94  264.75
39.0       74.90  264.40
40.0       74.38  266.62
41.0       73.83  268.69
42.0       73.26  270.63
43.0       72.68  272.45
44.0       72.09  274.14
45.0       71.48  275.74
46.0       70.85  277.23
47.0       70.10  277.93
48.0       69.27  278.14
49.0       68.45  278.34
50.0       67.56  278.48
51.0       66.19  278.29
52.0       64.82  278.12
53.0       63.45  277.97
54.0       62.07  277.83
55.0       60.70  277.70
56.0       58.96  277.66
57.0       57.23  277.62
58.0       55.49  277.58
59.0       53.75  277.55
60.0       52.02  277.52
61.0       50.04  277.70
62.0       47.49  278.32
63.0       44.95  278.88
64.0       42.40  279.40
65.0       41.10  279.80
66.0       39.80  280.18
67.0       38.50  280.54
68.0       37.19  280.90
69.0       36.48  281.11
70.0       36.03  281.27
71.0       35.58  281.43
72.0       35.13  281.58
73.0       34.68  281.74
74.0       34.23  281.89
75.0       33.78  282.04
76.0       32.33  283.04
77.0       30.21  284.54
78.0       28.07  285.98
79.0       25.92  287.36
80.0       25.05  287.84
81.0       24.33  288.22
82.0       23.61  288.59
83.0       22.89  288.95
84.0       22.55  289.11
85.0       22.46  289.12
86.0       22.37  289.13
87.0       22.29  289.15
88.0       22.20  289.16
89.0       22.11  289.17
90.0       22.02  289.18
91.0       21.94  289.20
92.0       21.59  289.76
93.0       21.07  290.69
94.0       20.55  291.61
95.0       20.43  292.63
96.0       20.34  293.67
97.0       20.24  294.70
98.0       20.14  295.73
99.0       20.04  296.76
100.0      19.92  297.79
101.0      18.99  297.44
102.0      17.86  296.75
103.0      16.72  296.07
104.0      15.58  295.40
105.0      14.47  295.17
106.0      13.41  295.58
107.0      12.35  295.98
108.0      11.28  296.39
109.0      10.22  296.79
110.0       9.15  297.18
111.0       8.25  297.49
112.0       7.98  297.44
113.0       7.71  297.38
114.0       7.44  297.33
115.0       7.18  297.27
116.0       6.91  297.22
117.0       6.09  297.02
118.0       4.90  296.72
119.0       3.71  296.43
120.0       2.52  296.13
121.0       1.90  296.20
122.0       1.34  296.31
123.0       0.80  296.53
124.0       0.32  297.16
125.0      -0.16  297.78
126.0      -0.64  298.41
127.0      -1.12  299.04
128.0      -1.60  299.67
129.0      -2.09  300.30
130.0      -2.57  300.93
131.0      -3.01  301.50
132.0      -3.16  301.53
133.0      -3.31  301.56
134.0      -3.46  301.59
135.0      -4.41  301.48
136.0      -5.71  301.30
137.0      -7.01  301.12
138.0      -8.31  300.94
139.0      -9.61  300.75
140.0     -10.62  299.98
141.0     -11.51  298.94
142.0     -12.40  297.90
143.0     -10.89  298.80
144.0      -9.37  299.69
145.0      -7.85  300.58
146.0      -6.33  301.45
147.0      -4.81  302.32
148.0      -3.29  303.19
149.0      -1.76  304.06
150.0      -0.24  304.92
151.0       1.28  305.78
152.0       2.81  306.65
153.0       4.33  307.52
154.0       5.61  308.38
155.0       4.72  309.22
156.0       3.82  309.62
157.0       2.88  309.03
158.0       1.94  308.43
159.0       1.08  307.93
160.0       0.88  308.24
161.0       0.68  308.55
162.0       0.49  308.85
163.0       0.29  309.16
164.0       0.09  309.47
165.0      -0.11  309.78
166.0      -0.30  310.08
167.0      -0.50  310.39
168.0      -0.70  310.70
169.0       1.16  311.47
170.0       3.03  312.25
171.0       4.29  313.12
172.0       5.40  314.02
173.0       6.51  314.92
174.0       7.62  315.83
175.0       8.72  316.74
176.0       9.83  317.65
177.0      10.65  318.58
178.0      10.83  319.52
179.0      11.31  320.00
180.0      11.98  320.18
181.0      12.66  320.35
182.0      13.33  320.53
183.0      13.28  320.28
184.0      12.74  319.76
185.0      12.21  319.24
186.0      11.67  318.72
187.0      11.13  318.20
188.0      10.59  317.69
189.0      10.05  317.17
190.0       9.51  316.66
191.0       8.96  316.15
192.0       8.62  315.75
193.0       8.36  315.40
194.0       8.10  315.04
195.0       8.76  314.48
196.0      10.03  313.78
197.0      11.30  313.07
198.0      12.56  312.35
"""
    if plate=='NA':
       apwp="""
0.0        90.00    0.00
1.0        88.33  180.70
2.0        86.67  180.70
3.0        86.14  175.33
4.0        85.95  173.39
5.0        85.79  171.94
6.0        85.62  170.59
7.0        85.45  169.35
8.0        85.28  168.19
9.0        85.11  167.12
10.0       84.94  166.12
11.0       84.76  165.19
12.0       84.57  164.34
13.0       84.22  163.81
14.0       83.88  163.34
15.0       83.49  162.61
16.0       82.96  160.83
17.0       82.42  159.31
18.0       81.88  157.98
19.0       81.33  156.83
20.0       81.12  156.68
21.0       81.41  157.94
22.0       81.70  159.28
23.0       81.98  160.72
24.0       82.26  162.26
25.0       82.53  163.92
26.0       82.80  165.70
27.0       82.16  172.55
28.0       81.43  178.31
29.0       80.63  183.13
30.0       79.78  187.17
31.0       79.55  186.15
32.0       79.47  183.99
33.0       79.37  181.86
34.0       79.20  179.56
35.0       78.86  176.88
36.0       78.50  174.36
37.0       78.12  171.99
38.0       77.72  169.78
39.0       77.30  167.70
40.0       77.61  167.72
41.0       77.92  167.75
42.0       78.23  167.77
43.0       78.54  167.80
44.0       78.85  167.83
45.0       79.16  167.86
46.0       79.48  167.89
47.0       79.55  168.32
48.0       79.47  169.01
49.0       79.38  169.70
50.0       79.28  170.59
51.0       79.05  173.39
52.0       78.79  176.08
53.0       78.52  178.64
54.0       78.22  181.08
55.0       77.90  183.40
56.0       77.51  185.86
57.0       77.09  188.16
58.0       76.65  190.32
59.0       76.20  192.35
60.0       75.74  194.24
61.0       75.25  196.69
62.0       74.73  200.49
63.0       74.14  204.02
64.0       73.50  207.30
65.0       73.48  207.86
66.0       73.46  208.42
67.0       73.43  208.98
68.0       73.41  209.53
69.0       73.65  208.66
70.0       74.01  207.12
71.0       74.35  205.51
72.0       74.68  203.84
73.0       75.00  202.09
74.0       75.30  200.27
75.0       75.59  198.38
76.0       75.52  201.87
77.0       75.06  208.70
78.0       74.41  215.06
79.0       73.59  220.85
80.0       73.50  221.21
81.0       73.50  221.00
82.0       73.50  220.79
83.0       73.50  220.58
84.0       73.72  218.91
85.0       74.06  216.16
86.0       74.37  213.31
87.0       74.63  210.35
88.0       74.86  207.30
89.0       75.04  204.16
90.0       75.18  200.96
91.0       75.27  197.71
92.0       75.55  196.67
93.0       75.95  197.15
94.0       76.36  197.65
95.0       77.18  197.76
96.0       78.05  197.83
97.0       78.92  197.91
98.0       79.79  198.01
99.0       80.66  198.13
100.0      81.53  198.27
101.0      80.82  196.53
102.0      79.71  194.75
103.0      78.60  193.30
104.0      77.48  192.12
105.0      76.75  192.71
106.0      76.59  195.69
107.0      76.40  198.60
108.0      76.18  201.42
109.0      75.93  204.14
110.0      75.65  206.77
111.0      75.39  208.27
112.0      75.32  205.66
113.0      75.23  203.07
114.0      75.11  200.52
115.0      74.96  198.02
116.0      74.78  195.56
117.0      74.13  194.52
118.0      73.19  194.41
119.0      72.24  194.30
120.0      71.29  194.21
121.0      70.97  193.62
122.0      70.71  192.99
123.0      70.54  192.59
124.0      70.71  193.06
125.0      70.89  193.53
126.0      71.06  194.01
127.0      71.24  194.50
128.0      71.41  195.00
129.0      71.58  195.51
130.0      71.75  196.03
131.0      71.90  196.38
132.0      71.88  195.14
133.0      71.85  193.90
134.0      71.81  192.67
135.0      71.10  193.14
136.0      70.08  194.23
137.0      69.06  195.23
138.0      68.04  196.14
139.0      67.01  196.96
140.0      65.77  196.26
141.0      64.44  195.02
142.0      63.10  193.90
143.0      64.58  191.66
144.0      66.02  189.16
145.0      67.42  186.37
146.0      68.76  183.24
147.0      70.04  179.71
148.0      71.23  175.75
149.0      72.34  171.28
150.0      73.33  166.27
151.0      74.19  160.69
152.0      74.88  154.55
153.0      75.40  147.91
154.0      75.73  141.88
155.0      76.02  144.73
156.0      75.85  147.65
157.0      74.69  150.19
158.0      73.49  152.38
159.0      72.39  154.07
160.0      72.26  153.82
161.0      72.13  153.57
162.0      71.99  153.32
163.0      71.86  153.07
164.0      71.73  152.83
165.0      71.60  152.59
166.0      71.47  152.36
167.0      71.33  152.13
168.0      71.20  151.90
169.0      72.50  143.28
170.0      73.38  133.55
171.0      74.04  126.09
172.0      74.51  118.88
173.0      74.74  111.36
174.0      74.71  103.74
175.0      74.42   96.27
176.0      73.90   89.17
177.0      73.49   83.36
178.0      73.72   79.48
179.0      73.50   76.79
180.0      72.99   75.03
181.0      72.46   73.37
182.0      71.92   71.80
183.0      71.85   72.55
184.0      72.07   74.85
185.0      72.26   77.20
186.0      72.43   79.60
187.0      72.56   82.04
188.0      72.67   84.51
189.0      72.74   87.01
190.0      72.79   89.52
191.0      72.80   92.04
192.0      72.74   93.81
193.0      72.65   95.23
194.0      72.54   96.64
195.0      71.70   96.06
196.0      70.36   94.36
197.0      69.01   92.87
198.0      67.64   91.56
"""
    if plate=='SA':
       apwp="""
0.0        90.00    0.00
1.0        88.48  176.30
2.0        86.95  176.30
3.0        86.53  168.76
4.0        86.45  164.50
5.0        86.37  160.76
6.0        86.28  157.18
7.0        86.17  153.79
8.0        86.06  150.58
9.0        85.93  147.57
10.0       85.79  144.75
11.0       85.64  142.12
12.0       85.48  139.77
13.0       85.24  138.58
14.0       84.99  137.49
15.0       84.69  136.40
16.0       84.13  135.05
17.0       83.57  133.95
18.0       83.00  133.01
19.0       82.44  132.22
20.0       82.25  131.54
21.0       82.61  130.86
22.0       82.97  130.10
23.0       83.33  129.26
24.0       83.69  128.32
25.0       84.05  127.28
26.0       84.40  126.10
27.0       84.43  135.88
28.0       84.29  145.47
29.0       84.01  154.39
30.0       83.60  162.34
31.0       83.39  160.95
32.0       83.23  157.53
33.0       83.04  154.27
34.0       82.75  151.13
35.0       82.23  148.16
36.0       81.69  145.56
37.0       81.14  143.29
38.0       80.57  141.28
39.0       80.00  139.50
40.0       80.29  138.06
41.0       80.58  136.53
42.0       80.86  134.91
43.0       81.14  133.19
44.0       81.40  131.36
45.0       81.66  129.42
46.0       81.90  127.36
47.0       82.03  126.70
48.0       82.09  127.04
49.0       82.15  127.39
50.0       82.22  128.02
51.0       82.37  131.28
52.0       82.49  134.65
53.0       82.59  138.13
54.0       82.66  141.69
55.0       82.70  145.30
56.0       82.74  149.45
57.0       82.73  153.61
58.0       82.69  157.75
59.0       82.61  161.83
60.0       82.50  165.80
61.0       82.43  170.84
62.0       82.42  178.70
63.0       82.28  186.40
64.0       82.00  193.70
65.0       82.08  194.90
66.0       82.15  196.11
67.0       82.22  197.36
68.0       82.28  198.62
69.0       82.50  196.70
70.0       82.76  193.22
71.0       82.99  189.49
72.0       83.19  185.52
73.0       83.36  181.34
74.0       83.48  176.96
75.0       83.58  172.44
76.0       83.88  180.55
77.0       83.90  198.12
78.0       83.37  214.31
79.0       82.41  227.29
80.0       82.34  228.63
81.0       82.39  228.88
82.0       82.44  229.14
83.0       82.48  229.40
84.0       82.82  226.98
85.0       83.33  222.26
86.0       83.78  216.82
87.0       84.17  210.58
88.0       84.48  203.56
89.0       84.70  195.83
90.0       84.82  187.59
91.0       84.83  179.15
92.0       85.11  176.27
93.0       85.63  177.19
94.0       86.15  178.37
95.0       87.04  175.29
96.0       87.94  168.69
97.0       88.78  152.46
98.0       89.26  101.14
99.0       88.81   47.96
100.0      87.98   31.01
101.0      88.51   36.07
102.0      89.29   63.58
103.0      89.30  145.49
104.0      88.53  174.06
105.0      88.07  189.19
106.0      88.01  213.41
107.0      87.64  233.01
108.0      87.08  246.23
109.0      86.42  254.90
110.0      85.70  260.77
111.0      85.15  264.12
112.0      85.38  263.70
113.0      85.61  263.23
114.0      85.84  262.72
115.0      86.08  262.14
116.0      86.31  261.48
117.0      86.05  255.65
118.0      85.41  248.40
119.0      84.71  242.98
120.0      83.97  238.86
121.0      83.74  236.57
122.0      83.55  234.54
123.0      83.39  233.53
124.0      83.33  236.16
125.0      83.26  238.74
126.0      83.18  241.27
127.0      83.09  243.73
128.0      82.98  246.12
129.0      82.86  248.43
130.0      82.73  250.66
131.0      82.62  252.43
132.0      82.80  250.74
133.0      82.98  248.95
134.0      83.15  247.08
135.0      82.42  244.60
136.0      81.28  242.47
137.0      80.14  240.84
138.0      79.00  239.54
139.0      77.85  238.48
140.0      76.82  234.91
141.0      75.79  230.78
142.0      74.70  227.20
143.0      76.33  226.82
144.0      77.95  226.34
145.0      79.58  225.72
146.0      81.20  224.87
147.0      82.82  223.63
148.0      84.44  221.68
149.0      86.04  218.15
150.0      87.61  209.92
151.0      88.97  176.54
152.0      88.68   89.32
153.0      87.22   67.59
154.0      85.89   60.82
155.0      86.78   50.54
156.0      87.70   41.70
157.0      88.96   60.27
158.0      89.26  158.76
159.0      88.19  190.34
160.0      88.08  197.32
161.0      87.94  203.47
162.0      87.79  208.80
163.0      87.62  213.39
164.0      87.43  217.35
165.0      87.23  220.75
166.0      87.03  223.70
167.0      86.82  226.26
168.0      86.60  228.50
169.0      88.64  230.93
170.0      89.31   38.96
171.0      87.78   36.39
172.0      86.36   34.32
173.0      84.94   33.40
174.0      83.53   32.89
175.0      82.11   32.55
176.0      80.69   32.32
177.0      79.48   31.11
178.0      78.71   27.80
179.0      78.03   27.66
180.0      77.42   29.28
181.0      76.79   30.75
182.0      76.16   32.10
183.0      76.35   32.76
184.0      77.09   33.06
185.0      77.83   33.40
186.0      78.58   33.77
187.0      79.32   34.20
188.0      80.06   34.69
189.0      80.80   35.27
190.0      81.54   35.93
191.0      82.28   36.73
192.0      82.77   37.91
193.0      83.16   39.32
194.0      83.55   40.91
195.0      83.19   47.69
196.0      82.21   55.93
197.0      81.11   62.23
198.0      79.92   67.11
"""
    return apwp
#
def bc02(data):
    """
     get APWP from Besse and Courtillot 2002 paper
    """
    
    plate,site_lat,site_lon,age=data[0],data[1],data[2],data[3]
    apwp=get_plate_data(plate)
    recs=apwp.split()
    #
    # put it into  usable form in plate_data
    #
    k,plate_data=0,[]
    while k<len(recs)-3:
        rec=[float(recs[k]),float(recs[k+1]),float(recs[k+2])]
        plate_data.append(rec)
        k=k+3
    
    #
    # find the right pole for the age
    #
    for i in range(len(plate_data)):
        if age >= plate_data[i][0] and age <= plate_data[i+1][0]:
           if (age-plate_data[i][0]) < (plate_data[i][0]-age):
              rec=i
           else:
              rec=i+1
           break
    pole_lat=plate_data[rec][1]
    pole_lon=plate_data[rec][2]
    return pole_lat,pole_lon

def linreg(x,y):
    """
    does a linear regression
    """
    if len(x)!=len(y):
        print 'x and y must be same length'
        sys.exit()
    xx,yy,xsum,ysum,xy,n,sum=0,0,0,0,0,len(x),0
    linpars={}
    for i in range(n):
        xx+=x[i]*x[i]
        yy+=y[i]*y[i]
        xy+=x[i]*y[i]
        xsum+=x[i]
        ysum+=y[i]
        xsig=numpy.sqrt((xx-xsum**2/n)/(n-1.))
        ysig=numpy.sqrt((yy-ysum**2/n)/(n-1.))
    linpars['slope']=(xy-(xsum*ysum/n))/(xx-(xsum**2)/n)
    linpars['b']=(ysum-linpars['slope']*xsum)/n
    linpars['r']=(linpars['slope']*xsig)/ysig
    for i in range(n):
        a=y[i]-linpars['b']-linpars['slope']*x[i]
        sum+=a
    linpars['sigma']=sum/(n-2.)
    linpars['n']=n
    return linpars


def squish(incs,f):
    """
    returns 'flattened' inclination, assuming factor, f and King (1955) formula
    """
    incs=incs*numpy.pi/180. # convert to radians
    tincnew=f*numpy.tan(incs) # multiply tangent by flattening factor
    return numpy.arctan(tincnew)*180./numpy.pi


def get_TS(ts):
    if ts=='ck95':
        TS=[0,0.780,0.990,1.070,1.770,1.950,2.140,2.150,2.581,3.040,3.110,3.220,3.330,3.580,4.180,4.290,4.480,4.620,4.800,4.890,4.980,5.230,5.894,6.137,6.269,6.567,6.935,7.091,7.135,7.170,7.341,7.375,7.432,7.562,7.650,8.072,8.225,8.257,8.699,9.025,9.230,9.308,9.580,9.642,9.740,9.880,9.920,10.949,11.052,11.099,11.476,11.531,11.935,12.078,12.184,12.401,12.678,12.708,12.775,12.819,12.991,13.139,13.302,13.510,13.703,14.076,14.178,14.612,14.800,14.888,15.034,15.155,16.014,16.293,16.327,16.488,16.556,16.726,17.277,17.615,18.281,18.781,19.048,20.131,20.518,20.725,20.996,21.320,21.768,21.859,22.151,22.248,22.459,22.493,22.588,22.750,22.804,23.069,23.353,23.535,23.677,23.800,23.999,24.118,24.730,24.781,24.835,25.183,25.496,25.648,25.823,25.951,25.992,26.554,27.027,27.972,28.283,28.512,28.578,28.745,29.401,29.662,29.765,30.098,30.479,30.939,33.058,33.545,34.655,34.940,35.343,35.526,35.685,36.341,36.618,37.473,37.604,37.848,37.920,38.113,38.426,39.552,39.631,40.130,41.257,41.521,42.536,43.789,46.264,47.906,49.037,49.714,50.778,50.946,51.047,51.743,52.364,52.663,52.757,52.801,52.903,53.347,55.904,56.391,57.554,57.911,60.920,61.276,62.499,63.634,63.976,64.745,65.578,67.610,67.735,68.737,71.071,71.338,71.587,73.004,73.291,73.374,73.619,79.075,83.000]
        Labels=[['C1n',0],['C1r',0.78],['C2',1.77],['C2An',2.581],['C2Ar',3.58],['C3n',4.18],['C3r',5.23],['C3An',5.894],['C3Ar',6.567],['C3Bn',6.935],['C3Br',7.091],['C4n',7.432],['C4r',8.072],['C4An',8.699],['C4Ar',9.025],['C5n',9.74],['C5r',10.949],['C5An',11.935],['C5Ar',12.401],['C5AAn',12.991],['C5AAr',13.139],['C5ABn',13.302],['C5ABr',13.51],['C5ACn',13.703],['C5ACr',14.076],['C5ADn',14.178],['C5ADr',14.612],['C5Bn',14.8],['C5Br',15.155],['C5Cn',16.014],['C5Cr',16.726],['C5Dn',17.277],['C5Dr',17.615],['C5En',18.281],['C5Er',18.781],['C6n',19.048],['C6r',20.131],['C6An',20.518],['C6Ar',21.32],['C6AAn',21.768],['C6AAr',21.859],['C6Bn',22.588],['C6Br',23.069],['C6Cn',23.353],['C6Cr',24.118],['C7n',24.73],['C7r',25.183],['C7A',25.496],['C8n',25.823],['C8r',26.554],['C9n',27.027],['C9r',27.972],['C10n',28.283],['C10r',28.745],['C11n',29.401],['C11r',30.098],['C12n',30.479],['C12r',30.939],['C13n',33.058],['C13r',33.545],['C15n',34.655],['C15r',34.94],['C16n',35.343],['C16r',36.341],['C17n',36.618],['C17r',38.113],['C18n',38.426],['C18r',40.13],['C19n',41.257],['C19r',41.521],['C20n',42.536],['C20r',43.789],['C21n',46.264],['C21r',47.906],['C22n',49.037],['C22r',49.714],['C23n',50.778],['C23r',51.743],['C24n',52.364],['C24r',53.347],['C25n',55.904],['C25r',56.391],['C26n',57.554],['C26r',57.911],['C27n',60.92],['C27r',61.276],['C28n',62.499],['C28r',63.634],['C29n',63.976],['C29r',64.745],['C30n',65.578],['C30r',67.61],['C31n',67.735],['C31r',68.737],['C32n',71.071],['C32r',73.004],['C33n',73.619],['C33r',79.075],['C34n',83]]
        return TS,Labels
    if ts=='gts04':
        TS=[0,0.781,0.988,1.072,1.778,1.945,2.128,2.148,2.581,3.032,3.116,3.207,3.33,3.596,4.187,4.3,4.493,4.631,4.799,4.896,4.997,5.235,6.033,6.252,6.436,6.733,7.14,7.212,7.251,7.285,7.454,7.489,7.528,7.642,7.695,8.108,8.254,8.3,8.769,9.098,9.312,9.409,9.656,9.717,9.779,9.934,9.987,11.04,11.118,11.154,11.554,11.614,12.014,12.116,12.207,12.415,12.73,12.765,12.82,12.878,13.015,13.183,13.369,13.605,13.734,14.095,14.194,14.581,14.784,14.877,15.032,15.16,15.974,16.268,16.303,16.472,16.543,16.721,17.235,17.533,17.717,17.74,18.056,18.524,18.748,20,20.04,20.213,20.439,20.709,21.083,21.159,21.403,21.483,21.659,21.688,21.767,21.936,21.992,22.268,22.564,22.754,22.902,23.03,23.249,23.375,24.044,24.102,24.163,24.556,24.915,25.091,25.295,25.444,25.492,26.154,26.714,27.826,28.186,28.45,28.525,28.715,29.451,29.74,29.853,30.217,30.627,31.116,33.266,33.738,34.782,35.043,35.404,35.567,35.707,36.276,36.512,37.235,37.345,37.549,37.61,37.771,38.032,38.975,39.041,39.464,40.439,40.671,41.59,42.774,45.346,47.235,48.599,49.427,50.73,50.932,51.057,51.901,52.648,53.004,53.116,53.167,53.286,53.808,56.665,57.18,58.379,58.737,61.65,61.983,63.104,64.128,64.432,65.118,65.861,67.696,67.809,68.732,70.961,71.225,71.474,72.929,73.231,73.318,73.577,79.543,84]
        Labels=[['C1n',0.000],['C1r',0.781],['C2',1.778],['C2An',2.581],['C2Ar',3.596],['C3n',4.187],['C3r',5.235],['C3An',6.033],['C3Ar',6.733],['C3Bn',7.140],['C3Br',7.212],['C4n',7.528],['C4r',8.108],['C4An',8.769],['C4Ar',9.098],['C5n',9.779],['C5r',11.040],['C5An',12.014],['C5Ar',12.415],['C5AAn',13.015],['C5AAr',13.183],['C5ABn',13.369],['C5ABr',13.605],['C5ACn',13.734],['C5ACr',14.095],['C5ADn',14.194],['C5ADr',14.581],['C5Bn',14.784],['C5Br',15.160],['C5Cn',15.974],['C5Cr',16.721],['C5Dn',17.235],['C5Dr',17.533],['C5En',18.056],['C5Er',18.524],['C6n',18.748],['C6r',19.772],['C6An',20.040],['C6Ar',20.709],['C6AAn',21.083],['C6AAr',21.159],['C6Bn',21.767],['C6Br',22.268],['C6Cn',22.564],['C6Cr',23.375],['C7n',24.044],['C7r',24.556],['C7A',24.919],['C8n',25.295],['C8r',26.154],['C9n',26.714],['C9r',27.826],['C10n',28.186],['C11n',29.451],['C11r',30.217],['C12n',30.627],['C12r',31.116],['C13n',33.266],['C13r',33.738],['C15n',34.782],['C15r',35.043],['C16n',35.404],['C16r',36.276],['C17n',36.512],['C17r',37.771],['C18n',38.032],['C18r',39.464],['C19n',40.439],['C19r',40.671],['C20n',41.590],['C20r',42.774],['C21n',45.346],['C21r',47.235],['C22n',48.599],['C22r',49.427],['C23n',50.730],['C23r',51.901],['C24n',52.648],['C24r',53.808],['C25n',56.665],['C25r',57.180],['C26n',58.379],['C26r',58.737],['C27n',61.650],['C27r',61.938],['C28n',63.104],['C28r',64.128],['C29n',64.432],['C29r',65.118],['C30n',65.861],['C30r',67.696],['C31n',67.809],['C31r',68.732],['C32n',70.961],['C32r',72.929],['C33n',73.577],['C33r',79.543],['C34n',84.000]]
 
    return TS,Labels
    print "Time Scale Option Not Available"
    sys.exit()

