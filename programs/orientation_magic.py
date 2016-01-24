#!/usr/bin/env python
import sys
#import os
#import pmagpy.pmag as pmag
import pmagpy.command_line_extractor as extractor
import pmagpy.ipmag as ipmag
#
#
def main():
    """
    NAME
        orientation_magic.py
   
    DESCRIPTION
        takes tab delimited field notebook information and converts to MagIC formatted tables
 
    SYNTAX
        orientation_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file, default is: orient.txt
        -Fsa FILE: specify output file, default is: er_samples.txt 
        -Fsi FILE: specify output site location file, default is: er_sites.txt 
        -app  append/update these data in existing er_samples.txt, er_sites.txt files
        -ocn OCON:  specify orientation convention, default is #1 below
        -dcn DCON [DEC]: specify declination convention, default is #1 below
            if DCON = 2, you must supply the declination correction 
        -BCN don't correct bedding_dip_dir for magnetic declination -already corrected 
        -ncn NCON:  specify naming convention: default is #1 below
        -a: averages all bedding poles and uses average for all samples: default is NO
        -gmt HRS:  specify hours to subtract from local time to get GMT: default is 0
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used

    
        Orientation convention:
            Samples are oriented in the field with a "field arrow" and measured in the laboratory with a "lab arrow". The lab arrow is the positive X direction of the right handed coordinate system of the specimen measurements. The lab and field arrows may  not be the same. In the MagIC database, we require the orientation (azimuth and plunge) of the X direction of the measurements (lab arrow). Here are some popular conventions that convert the field arrow azimuth (mag_azimuth in the orient.txt file) and dip (field_dip in orient.txt) to the azimuth and plunge  of the laboratory arrow (sample_azimuth and sample_dip in er_samples.txt). The two angles, mag_azimuth and field_dip are explained below. 

            [1] Standard Pomeroy convention of azimuth and hade (degrees from vertical down) 
                 of the drill direction (field arrow).  lab arrow azimuth= sample_azimuth = mag_azimuth; 
                 lab arrow dip = sample_dip =-field_dip. i.e. the lab arrow dip is minus the hade.
            [2] Field arrow is the strike  of the plane orthogonal to the drill direction,
                 Field dip is the hade of the drill direction.  Lab arrow azimuth = mag_azimuth-90 
                 Lab arrow dip = -field_dip 
            [3] Lab arrow is the same as the drill direction; 
                 hade was measured in the field.  
                 Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
            [4] lab azimuth and dip are same as mag_azimuth, field_dip : use this for unoriented samples too
            [5] Same as AZDIP convention explained below - 
                azimuth and inclination of the drill direction are mag_azimuth and field_dip; 
                lab arrow is as in [1] above. 
                lab azimuth is same as mag_azimuth,lab arrow dip=field_dip-90
            [6] Lab arrow azimuth = mag_azimuth-90; Lab arrow dip = 90-field_dip
            [7] all others you will have to either customize your 
                self or e-mail ltauxe@ucsd.edu for help.  
       
         Magnetic declination convention:
            [1] Use the IGRF value at the lat/long and date supplied [default]
            [2] Will supply declination correction
            [3] mag_az is already corrected in file 
            [4] Correct mag_az but not bedding_dip_dir
    
         Sample naming convention:
            [1] XXXXY: where XXXX is an arbitrary length site designation and Y
                is the single character sample designation.  e.g., TG001a is the
                first sample from site TG001.    [default]
            [2] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
            [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
            [5] site name = sample name
            [6] site name entered in site_name column in the orient.txt format input file  
            [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
            NB: all others you will have to either customize your 
                self or e-mail ltauxe@ucsd.edu for help.  
    OUTPUT
            output saved in er_samples.txt and er_sites.txt - will overwrite any existing files 
    """
    args = sys.argv
    if "-h" in args:
        print main.__doc__
        sys.exit()
    else:
        info = [['WD', False, '.'], ['ID', False, '.'], ['f', False, 'orient.txt'], ['app', False, False], ['ocn', False, 1], ['dcn', False, 1], ['BCN', False, True], ['ncn', False, '1'], ['gmt', False, 0], ['mcd', False, ''], ['a', False, False]]

        #output_dir_path, input_dir_path, orient_file, append, or_con, dec_correction_con, samp_con, hours_from_gmt, method_codes, average_bedding
        # leave off -Fsa, -Fsi b/c defaults in command_line_extractor
        dataframe = extractor.command_line_dataframe(info)
        checked_args = extractor.extract_and_check_args(args, dataframe)
        output_dir_path, input_dir_path, orient_file, append, or_con, dec_correction_con, bed_correction, samp_con, hours_from_gmt, method_codes, average_bedding, samp_file, site_file = extractor.get_vars(['WD', 'ID', 'f', 'app', 'ocn', 'dcn', 'BCN', 'ncn', 'gmt', 'mcd', 'a', 'Fsa', 'Fsi'], checked_args)

        if not isinstance(dec_correction_con, int):
            if len(dec_correction_con) > 1:
                dec_correction = int(dec_correction_con.split()[1])
                dec_correction_con = int(dec_correction_con.split()[0])
            else:
                dec_correction = 0
        else:
            dec_correction = 0

        ipmag.orientation_magic(or_con, dec_correction_con, dec_correction, bed_correction, samp_con, hours_from_gmt, method_codes, average_bedding, orient_file, samp_file, site_file, output_dir_path, input_dir_path, append)

    #def orientation_magic(or_con=1, dec_correction_con=1, dec_correction=0, bed_correction=True, samp_con='1', hours_from_gmt=0, method_codes='', average_bedding=False, orient_file='orient.txt', samp_file='er_samples.txt', site_file='er_sites.txt', output_dir_path='.', input_dir_path='.', append=False):
    

##example use:
##make a pandas dataframe with three columns:
## col 1 is the command-line flag (minus the '-'), common ones include f, F, fsa, Fsa, etc.
## col 2 is a boolean for if the flag is required or not
## col 3 is a default value to use if the flag is not provided
#dataframe = command_line_dataframe([['sav', False, 0], ['fmt', False, 'svg'], ['s', False, 20]])
## get the args from the command line:
#args = sys.argv
## check through the args to make sure that reqd args are present, defaults are used as needed, and invalid args are ignored
#checked_args = extract_and_check_args(args, dataframe)
## assign values to variables based on their associated command-line flag
#fmt, size, plot = get_vars(['fmt', 's', 'sav'], checked_args)
#print "fmt:", fmt, "size:", size, "plot:", plot

            
    
    ignore="""
    #
    # initialize variables
    #
    stratpos=""
    args=sys.argv
    date,lat,lon="","",""  # date of sampling, latitude (pos North), longitude (pos East)
    bed_dip,bed_dip_dir="",""
    participantlist=""
    Lats,Lons=[],[] # list of latitudes and longitudes
    SampOuts,SiteOuts,ImageOuts=[],[],[]  # lists of Sample records and Site records
    samplelist,sitelist,imagelist=[],[],[]
    samp_con,Z,average_bedding,DecCorr="1",1,"0",0.
    newbaseline,newbeddir,newbeddip="","",""
    meths=''
    delta_u="0"
    sclass,lithology,type="","",""
    newclass,newlith,newtype='','',''
    user=""
    BPs=[]# bedding pole declinations, bedding pole inclinations
    #
    #
    dir_path,AddTo='.',0
    if "-WD" in args:
        ind=args.index("-WD")
        dir_path=sys.argv[ind+1]
    if "-ID" in args:
        ind = args.index("-ID")
        input_dir_path = args[ind+1]
    else:
        input_dir_path = dir_path
    output_dir_path = dir_path
    orient_file,samp_file,or_con,corr = input_dir_path+"/orient.txt", output_dir_path+"/er_samples.txt","1","1"
    site_file = output_dir_path+"/er_sites.txt"
    image_file= output_dir_path+"/er_images.txt"
    SampRecs,SiteRecs,ImageRecs=[],[],[]
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-f" in args:
        ind=args.index("-f")
        orient_file = os.path.join(input_dir_path, sys.argv[ind+1])
    if "-Fsa" in args:
        ind=args.index("-Fsa")
        samp_file = os.path.join(output_dir_path, sys.argv[ind+1])
    if "-Fsi" in args:
        ind=args.index("-Fsi")
        site_file= os.path.join(output_dir_path, sys.argv[ind+1])
    if '-app' in args:
        AddTo=1
        try:
            SampRecs,file_type=pmag.magic_read(samp_file)
            print 'sample data to be appended to: ', samp_file
        except:
            print 'problem with existing file: ',samp_file, ' will create new.'
        try:
            SiteRecs,file_type=pmag.magic_read(site_file)
            print 'site data to be appended to: ',site_file
        except:
            print 'problem with existing file: ',site_file,' will create new.'
        try:
            ImageRecs,file_type=pmag.magic_read(image_file)
            print 'image data to be appended to: ',image_file
        except:
            print 'problem with existing file: ',image_file,' will create new.'
    if "-ocn" in args:
        ind=args.index("-ocn")
        or_con=sys.argv[ind+1]
    if "-dcn" in args:
        ind=args.index("-dcn")
        corr=sys.argv[ind+1] 
        if corr=="2":
            DecCorr=float(sys.argv[ind+2])
        elif corr=="3":
            DecCorr=0.
    if '-BCN' in args:
        BedCorr=0
    else:
        BedCorr=1
    if "-ncn" in args:
        ind=args.index("-ncn")
        samp_con=sys.argv[ind+1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z=samp_con.split("-")[1]
                samp_con="7"
    if "-gmt" in args:
        ind=args.index("-gmt")
        delta_u=(sys.argv[ind+1])
    if "-mcd" in args:
        ind=args.index("-mcd")
        meths=(sys.argv[ind+1])
    if "-a" in args: average_bedding="1"
    #
    # read in file to convert
    #
    OrData,location_name=pmag.magic_read(orient_file)
    #
    # step through the data sample by sample
    #
    for OrRec in OrData:
        if 'mag_azimuth' not in OrRec.keys():OrRec['mag_azimuth']=""
        if 'field_dip' not in OrRec.keys():OrRec['field_dip']=""
        if OrRec['mag_azimuth']==" ":OrRec["mag_azimuth"]=""
        if OrRec['field_dip']==" ":OrRec["field_dip"]=""
        if 'sample_description' in OrRec.keys():
            sample_description=OrRec['sample_description']
        else:
            sample_description=""
        if 'sample_igsn' in OrRec.keys():
            sample_igsn=OrRec['sample_igsn']
        else:
            sample_igsn=""
        if 'sample_texture' in OrRec.keys():
            sample_texture=OrRec['sample_texture']
        else:
            sample_texture=""
        if 'sample_cooling_rate' in OrRec.keys():
            sample_cooling_rate=OrRec['sample_cooling_rate']
        else:
            sample_cooling_rate=""
        if 'cooling_rate_corr' in OrRec.keys():
            cooling_rate_corr=OrRec['cooling_rate_corr']
            if 'cooling_rate_mcd' in OrRec.keys():
                cooling_rate_mcd=OrRec['cooling_rate_mcd']
            else:
                cooling_rate_mcd='DA-CR'
        else:
            cooling_rate_corr=""
            cooling_rate_mcd=""
        sample_orientation_flag='g'
        if 'sample_orientation_flag' in OrRec.keys():
            if OrRec['sample_orientation_flag']=='b' or OrRec["mag_azimuth"]=="": 
                sample_orientation_flag='b'
        methcodes=meths  # initialize method codes
        if meths!='':
            if 'method_codes' in OrRec.keys() and OrRec['method_codes'].strip()!="":methcodes=methcodes+":"+OrRec['method_codes'] # add notes 
        else:
            if 'method_codes' in OrRec.keys() and OrRec['method_codes'].strip()!="":methcodes=OrRec['method_codes'] # add notes 
        codes=methcodes.replace(" ","").split(":")
        MagRec={}
        MagRec["er_location_name"]=location_name
        MagRec["er_citation_names"]="This study"
        MagRec['sample_orientation_flag']=sample_orientation_flag
        MagRec['sample_igsn']=sample_igsn
        MagRec['sample_texture']=sample_texture
        MagRec['sample_cooling_rate']=sample_cooling_rate
        MagRec['cooling_rate_corr']=cooling_rate_corr
        MagRec['cooling_rate_mcd']=cooling_rate_mcd
    #
    # parse information common to all orientation methods
    #
        MagRec["er_sample_name"]=OrRec["sample_name"]
        if "IGSN" in OrRec.keys():
            MagRec["sample_igsn"]=OrRec["IGSN"]
        else:
            MagRec["sample_igsn"]=""
        MagRec["sample_height"],MagRec["sample_bed_dip_direction"],MagRec["sample_bed_dip"]="","",""
        if "er_sample_alternatives" in OrRec.keys():MagRec["er_sample_alternatives"]=OrRec["sample_alternatives"]
        sample=OrRec["sample_name"]
        if OrRec['mag_azimuth']=="" and OrRec['field_dip']!="":
            OrRec['mag_azimuth']='999'
        if OrRec["mag_azimuth"]!="":
            labaz,labdip=pmag.orient(float(OrRec["mag_azimuth"]),float(OrRec["field_dip"]),or_con)
            if labaz<0:labaz+=360.
        else:
            labaz,labdip="",""
        if  OrRec['mag_azimuth']=='999':labaz=""
        if "GPS_baseline" in OrRec.keys() and OrRec['GPS_baseline']!="":newbaseline=OrRec["GPS_baseline"]
        if newbaseline!="":baseline=float(newbaseline)
        if 'participants' in OrRec.keys() and OrRec['participants']!="" and OrRec['participants']!=participantlist: 
            participantlist=OrRec['participants']
        MagRec['er_scientist_mail_names']=participantlist
        newlat=OrRec["lat"]
        if newlat!="":lat=float(newlat)
        if lat=="":
            print "No latitude specified for ! ",sample
            sys.exit()
        MagRec["sample_lat"]='%11.5f'%(lat)
        newlon=OrRec["long"]
        if newlon!="":lon=float(newlon)
        if lon=="":
            print "No longitude specified for ! ",sample
            sys.exit()
        MagRec["sample_lon"]='%11.5f'%(lon)
        if 'bedding_dip_direction' in OrRec.keys(): newbeddir=OrRec["bedding_dip_direction"]
        if newbeddir!="":bed_dip_dir=OrRec['bedding_dip_direction']
        if 'bedding_dip' in OrRec.keys(): newbeddip=OrRec["bedding_dip"]
        if newbeddip!="":bed_dip=OrRec['bedding_dip']
        MagRec["sample_bed_dip"]=bed_dip
        MagRec["sample_bed_dip_direction"]=bed_dip_dir
        if "sample_class" in OrRec.keys():newclass=OrRec["sample_class"]
        if newclass!="":sclass=newclass
        if sclass=="": sclass="Not Specified"
        MagRec["sample_class"]=sclass
        if "sample_lithology" in OrRec.keys():newlith=OrRec["sample_lithology"]
        if newlith!="":lithology=newlith
        if lithology=="": lithology="Not Specified"
        MagRec["sample_lithology"]=lithology
        if "sample_type" in OrRec.keys():newtype=OrRec["sample_type"]
        if newtype!="":type=newtype
        if type=="": type="Not Specified"
        MagRec["sample_type"]=type
        if labdip!="":
            MagRec["sample_dip"]='%7.1f'%labdip
        else:
            MagRec["sample_dip"]=""
        if "date" in OrRec.keys() and OrRec["date"]!="":
            newdate=OrRec["date"]
            if newdate!="":date=newdate
            mmddyy=date.split('/')
            yy=int(mmddyy[2])
            if yy>50: 
                yy=1900+yy
            else:
                yy=2000+yy
            decimal_year=yy+float(mmddyy[0])/12
            sample_date='%i:%s:%s'%(yy,mmddyy[0],mmddyy[1])
            MagRec["sample_date"]=sample_date
        if labaz!="":
            MagRec["sample_azimuth"]='%7.1f'%(labaz)
        else:
            MagRec["sample_azimuth"]=""
        if "stratigraphic_height" in OrRec.keys():
            if OrRec["stratigraphic_height"]!="": 
                MagRec["sample_height"]=OrRec["stratigraphic_height"]
                stratpos=OrRec["stratigraphic_height"]
            elif OrRec["stratigraphic_height"]=='-1':
                MagRec["sample_height"]=""   # make empty
            else:
                MagRec["sample_height"]=stratpos   # keep last record if blank
#
        if corr=="1" and MagRec['sample_azimuth']!="": # get magnetic declination (corrected with igrf value)
            x,y,z,f=pmag.doigrf(lon,lat,0,decimal_year)
            Dir=pmag.cart2dir( (x,y,z)) 
            DecCorr=Dir[0]
        if "bedding_dip" in OrRec.keys(): 
            if OrRec["bedding_dip"]!="":
                MagRec["sample_bed_dip"]=OrRec["bedding_dip"]
                bed_dip=OrRec["bedding_dip"]
            else:
                MagRec["sample_bed_dip"]=bed_dip
        else: MagRec["sample_bed_dip"]='0'
        if "bedding_dip_direction" in OrRec.keys():
            if OrRec["bedding_dip_direction"]!="" and BedCorr==1: 
                dd=float(OrRec["bedding_dip_direction"])+DecCorr
                if dd>360.:dd=dd-360.
                MagRec["sample_bed_dip_direction"]='%7.1f'%(dd)
                dip_dir=MagRec["sample_bed_dip_direction"]
            else: 
                MagRec["sample_bed_dip_direction"]=OrRec['bedding_dip_direction']
        else: MagRec["sample_bed_dip_direction"]='0'
        if average_bedding!="0": BPs.append([float(MagRec["sample_bed_dip_direction"]),float(MagRec["sample_bed_dip"])-90.,1.])
        if MagRec['sample_azimuth']=="" and MagRec['sample_dip']=="":
            MagRec["sample_declination_correction"]=''
            methcodes=methcodes+':SO-NO'
        MagRec["magic_method_codes"]=methcodes
        MagRec['sample_description']=sample_description
    #
    # work on the site stuff too
        if 'site_name' in OrRec.keys():
            site=OrRec['site_name']
        else:
            site=pmag.parse_site(OrRec["sample_name"],samp_con,Z) # parse out the site name
        MagRec["er_site_name"]=site
        site_description="" # overwrite any prior description
        if 'site_description' in OrRec.keys() and OrRec['site_description']!="":
            site_description=OrRec['site_description'].replace(",",";")
        if "image_name" in OrRec.keys():
            images=OrRec["image_name"].split(":")
            if "image_look" in OrRec.keys():
                looks=OrRec['image_look'].split(":")
            else:
                looks=[]
            if "image_photographer" in OrRec.keys():
                photographers=OrRec['image_photographer'].split(":")
            else:
                photographers=[]
            for image in images:
                if image !="" and image not in imagelist:
                    imagelist.append(image)
                    ImageRec={}
                    ImageRec['er_image_name']=image
                    ImageRec['image_type']="outcrop"
                    ImageRec['image_date']=sample_date
                    ImageRec['er_citation_names']="This study"
                    ImageRec['er_location_name']=location_name
                    ImageRec['er_site_name']=MagRec['er_site_name']
                    k=images.index(image)
                    if len(looks)>k:
                        ImageRec['er_image_description']="Look direction: "+looks[k]
                    elif len(looks)>=1:
                        ImageRec['er_image_description']="Look direction: "+looks[-1]
                    else:
                        ImageRec['er_image_description']="Look direction: unknown"
                    if len(photographers)>k:
                        ImageRec['er_photographer_mail_names']=photographers[k]
                    elif len(photographers)>=1:
                        ImageRec['er_photographer_mail_names']=photographers[-1]
                    else:
                        ImageRec['er_photographer_mail_names']="unknown"
                    ImageOuts.append(ImageRec)
        if site not in sitelist:
    	    sitelist.append(site) # collect unique site names
    	    SiteRec={}
    	    SiteRec["er_site_name"]=site 
            SiteRec["site_definition"]="s"
    	    SiteRec["er_location_name"]=location_name
    	    SiteRec["er_citation_names"]="This study"
            SiteRec["site_lat"]=MagRec["sample_lat"]
            SiteRec["site_lon"]=MagRec["sample_lon"]
            SiteRec["site_height"]=MagRec["sample_height"]
            SiteRec["site_class"]=MagRec["sample_class"]
            SiteRec["site_lithology"]=MagRec["sample_lithology"]
            SiteRec["site_type"]=MagRec["sample_type"]
            SiteRec["site_description"]=site_description
            SiteOuts.append(SiteRec)
        if sample not in samplelist:
            samplelist.append(sample)
            if MagRec['sample_azimuth']!="": # assume magnetic compass only
                MagRec['magic_method_codes']=MagRec['magic_method_codes']+':SO-MAG'
                MagRec['magic_method_codes']=MagRec['magic_method_codes'].strip(":")
            SampOuts.append(MagRec)
            if MagRec['sample_azimuth']!="" and corr!='3':
                az=labaz+DecCorr
                if az>360.:az=az-360.
                CMDRec={}
                for key in MagRec.keys():
                    CMDRec[key]=MagRec[key] # make a copy of MagRec
                CMDRec["sample_azimuth"]='%7.1f'%(az)
                CMDRec["magic_method_codes"]=methcodes+':SO-CMD-NORTH'
                CMDRec["magic_method_codes"]=CMDRec['magic_method_codes'].strip(':')
                CMDRec["sample_declination_correction"]='%7.1f'%(DecCorr)
                if corr=='1':
                    CMDRec['sample_description']=sample_description+':Declination correction calculated from IGRF'
                else:
                    CMDRec['sample_description']=sample_description+':Declination correction supplied by user'
                CMDRec["sample_description"]=CMDRec['sample_description'].strip(':')
                SampOuts.append(CMDRec)
            if "mag_az_bs" in OrRec.keys() and OrRec["mag_az_bs"] !="" and OrRec["mag_az_bs"]!=" ":
                SRec={}
                for key in MagRec.keys():
                    SRec[key]=MagRec[key] # make a copy of MagRec
                labaz=float(OrRec["mag_az_bs"])
                az=labaz+DecCorr
                if az>360.:az=az-360.
                SRec["sample_azimuth"]='%7.1f'%(az)
                SRec["sample_declination_correction"]='%7.1f'%(DecCorr)
                SRec["magic_method_codes"]=methcodes+':SO-SIGHT-BACK:SO-CMD-NORTH'
                SampOuts.append(SRec)
    #
    # check for suncompass data
    #
            if "shadow_angle" in OrRec.keys() and OrRec["shadow_angle"]!="":  # there are sun compass data
                if delta_u=="":
                    delta_u=raw_input("Enter hours to SUBTRACT from time for  GMT: [0] ")
                    if delta_u=="":delta_u="0"
                SunRec,sundata={},{}
                shad_az=float(OrRec["shadow_angle"])
                sundata["date"]='%i:%s:%s:%s'%(yy,mmddyy[0],mmddyy[1],OrRec["hhmm"])
#                if eval(delta_u)<0:
#                        MagRec["sample_time_zone"]='GMT'+delta_u+' hours'
#                else:
#                    MagRec["sample_time_zone"]='GMT+'+delta_u+' hours'
                sundata["delta_u"]=delta_u
                sundata["lon"]='%7.1f'%(lon)   
                sundata["lat"]='%7.1f'%(lat)  
                sundata["shadow_angle"]=OrRec["shadow_angle"]
                sundec=pmag.dosundec(sundata)
                for key in MagRec.keys():
                    SunRec[key]=MagRec[key]  # make a copy of MagRec
                SunRec["sample_azimuth"]='%7.1f'%(sundec) 
                SunRec["sample_declination_correction"]=''
                SunRec["magic_method_codes"]=methcodes+':SO-SUN'
                SunRec["magic_method_codes"]=SunRec['magic_method_codes'].strip(':')
                SampOuts.append(SunRec)
    #
    # check for differential GPS data
    #
            if "prism_angle" in OrRec.keys() and OrRec["prism_angle"]!="":  # there are diff GPS data   
                GPSRec={}
                for key in MagRec.keys():
                    GPSRec[key]=MagRec[key]  # make a copy of MagRec
                prism_angle=float(OrRec["prism_angle"])
                laser_angle=float(OrRec["laser_angle"])
                if OrRec["GPS_baseline"]!="": baseline=float(OrRec["GPS_baseline"]) # new baseline
                gps_dec=baseline+laser_angle+prism_angle-90.
                while gps_dec>360.:
                    gps_dec=gps_dec-360.
                while gps_dec<0:
                    gps_dec=gps_dec+360. 
                for key in MagRec.keys():
                    GPSRec[key]=MagRec[key]  # make a copy of MagRec
                GPSRec["sample_azimuth"]='%7.1f'%(gps_dec) 
                GPSRec["sample_declination_correction"]=''
                GPSRec["magic_method_codes"]=methcodes+':SO-GPS-DIFF'
                SampOuts.append(GPSRec)
            if "GPS_Az" in OrRec.keys() and OrRec["GPS_Az"]!="":  # there are differential GPS Azimuth data   
                GPSRec={}
                for key in MagRec.keys():
                    GPSRec[key]=MagRec[key]  # make a copy of MagRec
                GPSRec["sample_azimuth"]='%7.1f'%(float(OrRec["GPS_Az"])) 
                GPSRec["sample_declination_correction"]=''
                GPSRec["magic_method_codes"]=methcodes+':SO-GPS-DIFF'
                SampOuts.append(GPSRec)
        if average_bedding!="0":  
            fpars=pmag.fisher_mean(BPs)
            print 'over-writing all bedding with average '
    Samps=[]
    for  rec in SampOuts:
        if average_bedding!="0":
            rec['sample_bed_dip_direction']='%7.1f'%(fpars['dec'])
            rec['sample_bed_dip']='%7.1f'%(fpars['inc']+90.)
            Samps.append(rec)
        else:
            Samps.append(rec)
    for rec in SampRecs:
        if rec['er_sample_name'] not in samplelist: # overwrite prior for this sample 
            Samps.append(rec)
    for rec in SiteRecs:
        if rec['er_site_name'] not in sitelist: # overwrite prior for this sample
            SiteOuts.append(rec)
    for rec in ImageRecs:
        if rec['er_image_name'] not in imagelist: # overwrite prior for this sample
            ImageOuts.append(rec)
    print 'saving data...'
    SampsOut,keys=pmag.fillkeys(Samps)
    Sites,keys=pmag.fillkeys(SiteOuts)
    pmag.magic_write(samp_file,SampsOut,"er_samples")
    pmag.magic_write(site_file,Sites,"er_sites")
    print "Data saved in ", samp_file,' and ',site_file
    if len(ImageOuts)>0:
        Images,keys=pmag.fillkeys(ImageOuts)
        pmag.magic_write(image_file,Images,"er_images")
        print "Image info saved in ",image_file
"""
main()

