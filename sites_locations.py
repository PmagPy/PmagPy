#!/usr/bin/env python
import sys,pmag
def main():
    """
    NAME
        sites_locations.py

    DESCRIPTION
        reads in er_sites.txt file and finds all locations and bounds of locations
        outputs er_locations.txt file

    SYNTAX
        sites_locations.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f: specimen input er_sites format file, default is "er_sites.txt"
        -F: locations table: default is "er_locations.txt"
    """
# set defaults
    site_file="er_sites.txt"
    loc_file="er_locations.txt"
    Names,user=[],"unknown"
    Done=[]
    version_num=pmag.get_version()
    args=sys.argv
    dir_path='.'
# get command line stuff
    if '-WD' in args:
	ind=args.index("-WD")
	dir_path=args[ind+1]
    if "-h" in args:
	print main.__doc__
        sys.exit()
    if '-f' in args:
	ind=args.index("-f")
	site_file=args[ind+1]
    if '-F' in args:
	ind=args.index("-F")
	loc_file=args[ind+1]
    #
    site_file=dir_path+'/'+site_file
    loc_file=dir_path+'/'+loc_file
    Sites,file_type=pmag.magic_read(site_file)
    if file_type != 'er_sites':
        print file_type
        print file_type,"This is not a valid er_sites file "
        sys.exit()
    # read in site data
    #
    LocNames=[]
    for site in Sites:
        if site['er_location_name'] not in LocNames:LocNames.append(site['er_lcoation_name'])
    for loc in LocNames:
        lats,lons=[],[]
        for site in Sites:
            if 'site_lat' in site.keys() and site['site_lat'].strip()!="":
                lats.append(float(site['site_lat'])
            if 'site_lon' in site.keys() and site['site_lon'].strip()!="":
                lon.append(float(site['site_lon'])
        lats.sort()
        lons.sort()
        LocRec={'er_citation_names':'This study','er_location_name':loc,'location_type':'outcrop'}
        LocRec['begin_lat']=str(lats[0])
        LocRec['end_lat']=str(lats[-1])
        LocRec['begin_lon']=str(lons[0])
        LocRec['end_lon']=str(lons[-1])
        Locations.append(LocRec)
    if len(Locations)>1:
        pmag.magic_write(loc_file,Locations,"er_locations")
        print "Locations written to: ",loc_file
main()
