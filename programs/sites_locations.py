#!/usr/bin/env python
import sys
import pmagpy.pmag as pmag

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
    LocNames,Locations=[],[]
    for site in Sites:
        if site['er_location_name'] not in LocNames: # new location name
            LocNames.append(site['er_location_name'])
            sites_locs=pmag.get_dictitem(Sites,'er_location_name',site['er_location_name'],'T') # get all sites for this loc
            lats=pmag.get_dictkey(sites_locs,'site_lat','f') # get all the latitudes as floats
            lons=pmag.get_dictkey(sites_locs,'site_lon','f') # get all the longitudes as floats
            LocRec={'er_citation_names':'This study','er_location_name':site['er_location_name'],'location_type':''}
            LocRec['location_begin_lat']=str(min(lats))
            LocRec['location_end_lat']=str(max(lats))
            LocRec['location_begin_lon']=str(min(lons))
            LocRec['location_end_lon']=str(max(lons))
            Locations.append(LocRec)
    if len(Locations)>0:
        pmag.magic_write(loc_file,Locations,"er_locations")
        print "Locations written to: ",loc_file

if __name__ == "__main__":
    main()
