#!/usr/bin/env python
from __future__ import print_function
import sys
import pmagpy.pmag as pmag
#
#


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
        -Fsa FILE: specify sample output file, default is: er_samples.txt
        -Fsi FILE: specify site output file, default is: er_sites.txt
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
            output saved in er_samples.txt  will overwrite any existing files
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    #
    # initialize variables
    #
    version_num = pmag.get_version()
    or_con = '3'
    #
    #
    orient_file = pmag.get_named_arg_from_sys("-f", reqd=True)
    samp_file = pmag.get_named_arg_from_sys("-Fsa", "er_samples.txt")
    site_file = pmag.get_named_arg_from_sys("-Fsi", "er_sites.txt")
    samp_con = pmag.get_named_arg_from_sys("-ncn", "1")
    Z = 1
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
    #
    # read in file to convert
    #
    azfile = open(orient_file, 'r')
    AzDipDat = azfile.readlines()
    azfile.close()
    SampOut = []
    SiteOut = []
    for line in AzDipDat[1:]:
        orec = line.split()
        if len(orec) > 1:
            labaz, labdip = pmag.orient(float(orec[1]), float(orec[2]), or_con)
            bed_dip_dir = (orec[3])
            bed_dip = (orec[4])
            SampRec = {}
            SiteRec = {}
            SampRec["er_location_name"] = location_name
            SampRec["er_citation_names"] = "This study"
            SiteRec["er_location_name"] = location_name
            SiteRec["er_citation_names"] = "This study"
            SiteRec["site_class"] = ""
            SiteRec["site_lithology"] = ""
            SiteRec["site_type"] = ""
            SiteRec["site_definition"] = "s"
            SiteRec["er_citation_names"] = "This study"
    #
    # parse information common to all orientation methods
    #
            SampRec["er_sample_name"] = orec[0]
            SampRec["sample_bed_dip_direction"] = orec[3]
            SampRec["sample_bed_dip"] = orec[4]
            SiteRec["site_bed_dip_direction"] = orec[3]
            SiteRec["site_bed_dip"] = orec[4]
            if ignore == 0:
                SampRec["sample_dip"] = '%7.1f' % (labdip)
                SampRec["sample_azimuth"] = '%7.1f' % (labaz)
            else:
                SampRec["sample_dip"] = '0'
                SampRec["sample_azimuth"] = '0'
            SampRec["sample_lat"] = orec[5]
            SampRec["sample_lon"] = orec[6]
            SiteRec["site_lat"] = orec[5]
            SiteRec["site_lon"] = orec[6]
            methods = meths.split(":")
            SampRec["magic_method_codes"] = meths
            # parse out the site name
            site = pmag.parse_site(orec[0], samp_con, Z)
            SampRec["er_site_name"] = site
            SampRec['magic_software_packages'] = version_num
            SiteRec["er_site_name"] = site
            SiteRec['magic_software_packages'] = version_num
            SampOut.append(SampRec)
            SiteOut.append(SiteRec)
    pmag.magic_write(samp_file, SampOut, "er_samples")
    print("Sample info saved in ", samp_file)
    pmag.magic_write(site_file, SiteOut, "er_sites")
    print("Site info saved in ", site_file)


if __name__ == "__main__":
    main()
