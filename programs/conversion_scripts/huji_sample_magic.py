#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag


def main():
    """
    NAME
        huji_sample_magic.py

    DESCRIPTION
        takes tab delimited Hebrew University sample file and converts to MagIC formatted tables

    SYNTAX
        huji_sample_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file
        -Fsa FILE: specify sample output file, default is: samples.txt
        -Fsi FILE: specify site output file, default is: sites.txt
        -Iso:  import sample orientation info - default is to set sample_az/dip to 0,0
        -ncn NCON:  specify naming convention: default is #1 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD:SO-POM]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
        -loc: location name, default="unknown"
        -DM: data model number (MagIC 2 or 3, default 3)

    INPUT FORMAT
        Input files must be tab delimited:
            Samp  Az Dip Dip_dir Dip
        Orientation convention:
             Lab arrow azimuth = mag_azimuth; Lab arrow dip = 90-field_dip
                e.g. field_dip is degrees from horizontal of drill direction

         Magnetic declination convention:
             Az is already corrected in file

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

    OUTPUT
            output saved in samples  will overwrite any existing files
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    #
    # initialize variables
    Z = 1
    # get arguments from the command line
    orient_file = pmag.get_named_arg_from_sys("-f", reqd=True)
    data_model_num = int(float(pmag.get_named_arg_from_sys("-DM", 3)))
    if data_model_num == 2:
        samp_file = pmag.get_named_arg_from_sys("-Fsa", "er_samples.txt")
        site_file = pmag.get_named_arg_from_sys("-Fsi", "er_sites.txt")
    else:
        samp_file = pmag.get_named_arg_from_sys("-Fsa", "samples.txt")
        site_file = pmag.get_named_arg_from_sys("-Fsi", "sites.txt")
    samp_con = pmag.get_named_arg_from_sys("-ncn", "1")
    if "4" in samp_con:
        if "-" not in samp_con:
            print("option [4] must be in form 3-Z where Z is an integer")
            sys.exit()
        else:
            Z = samp_con.split("-")[1]
            samp_con = "4"
        print(samp_con, Z)
    meths = pmag.get_named_arg_from_sys("-mcd", 'FS-FD:SO-POM:SO-SUN')
    location_name = pmag.get_named_arg_from_sys("-loc", "unknown")
    if "-Iso" in args:
        ignore = 0
    else:
        ignore = 1

    convert(orient_file, meths, location_name, samp_con, Z, ignore)


def convert(orient_file, meths='FS-FD:SO-POM:SO-SUN', location_name='unknown',
            samp_con="1", Z=1, ignore_dip=True, data_model_num=3,
            samp_file="samples.txt", site_file="sites.txt"):
    version_num = pmag.get_version()
    if data_model_num == 2:
        loc_col = "er_location_name"
        site_col = "er_site_name"
        samp_col = "er_sample_name"
        citation_col = "er_citation_names"
        class_col = "site_class"
        lithology_col = "site_lithology"
        definition_col = "site_definition"
        type_col = "site_type"
        sample_bed_dip_direction_col = "sample_bed_dip_direction"
        sample_bed_dip_col = "sample_bed_dip"
        site_bed_dip_direction_col = "site_bed_dip_direction"
        site_bed_dip_col = "site_bed_dip"
        sample_dip_col = "sample_dip"
        sample_az_col = "sample_azimuth"
        sample_lat_col = "sample_lat"
        sample_lon_col = "sample_lon"
        site_lat_col = "site_lat"
        site_lon_col = "site_lon"
        meth_col = "magic_method_codes"
        software_col = "magic_software_packages"
    else:
        loc_col = "location"
        site_col = "site"
        samp_col = "sample"
        citation_col = "citations"
        class_col = "class"
        lithology_col = "lithology"
        definition_col = "definition"
        type_col = "type"
        sample_bed_dip_direction_col = 'bed_dip_direction'
        sample_bed_dip_col = 'bed_dip'
        site_bed_dip_direction_col = 'bed_dip_direction'
        site_bed_dip_col = "bed_dip"
        sample_dip_col = "dip"
        sample_az_col = "azimuth"
        sample_lat_col = "lat"
        sample_lon_col = "lon"
        site_lat_col = "lat"
        site_lon_col = "lon"
        meth_col = "method_codes"
        software_col = "software_packages"
    #
    # read in file to convert
    #
    with open(orient_file, 'r') as azfile:
        AzDipDat = azfile.readlines()
    SampOut = []
    SiteOut = []
    for line in AzDipDat[1:]:
        orec = line.split()
        if len(orec) > 1:
            labaz, labdip = pmag.orient(float(orec[1]), float(orec[2]), '3')
            bed_dip_dir = (orec[3])
            bed_dip = (orec[4])
            SampRec = {}
            SiteRec = {}
            SampRec[loc_col] = location_name
            SampRec[citation_col] = "This study"
            SiteRec[loc_col] = location_name
            SiteRec[citation_col] = "This study"
            SiteRec[class_col] = ""
            SiteRec[lithology_col] = ""
            SiteRec[type_col] = ""
            SiteRec[definition_col] = "s"
    #
    # parse information common to all orientation methods
    #
            SampRec[samp_col] = orec[0]
            SampRec[sample_bed_dip_direction_col] = orec[3]
            SampRec[sample_bed_dip_col] = orec[4]
            SiteRec[site_bed_dip_direction_col] = orec[3]
            SiteRec[site_bed_dip_col] = orec[4]
            if not ignore_dip:
                SampRec[sample_dip_col] = '%7.1f' % (labdip)
                SampRec[sample_az_col] = '%7.1f' % (labaz)
            else:
                SampRec[sample_dip_col] = '0'
                SampRec[sample_az_col] = '0'
            SampRec[sample_lat_col] = orec[5]
            SampRec[sample_lon_col] = orec[6]
            SiteRec[site_lat_col] = orec[5]
            SiteRec[site_lon_col] = orec[6]
            SampRec[meth_col] = meths
            # parse out the site name
            site = pmag.parse_site(orec[0], samp_con, Z)
            SampRec[site_col] = site
            SampRec[software_col] = version_num
            SiteRec[site_col] = site
            SiteRec[software_col] = version_num
            SampOut.append(SampRec)
            SiteOut.append(SiteRec)
    if data_model_num == 2:
        pmag.magic_write(samp_file, SampOut, "er_samples")
        pmag.magic_write(site_file, SiteOut, "er_sites")
    else:
        pmag.magic_write(samp_file, SampOut, "samples")
        pmag.magic_write(site_file, SiteOut, "sites")

    print("Sample info saved in ", samp_file)
    print("Site info saved in ", site_file)





if __name__ == "__main__":
    main()
