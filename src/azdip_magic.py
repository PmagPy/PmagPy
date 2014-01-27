#!/usr/bin/env python
import string
import sys
from . import pmag
import exceptions
#
#


def main():
    """
    NAME
        azdip_magic.py

    DESCRIPTION
        takes space delimited AzDip file and converts to MagIC formatted tables

    SYNTAX
        azdip_magic.py [command line options]

    OPTIONS
        -f FILE: specify input file
        -Fsa FILE: specify output file, default is: er_samples.txt
        -ncn NCON:  specify naming convention: default is #1 below
        -mcd: specify sampling method codes as a colon delimited string:  [default is: FS-FD]
             FS-FD field sampling done with a drill
             FS-H field sampling done with hand samples
             FS-LOC-GPS  field location done with GPS
             FS-LOC-MAP  field location done with map
             SO-POM   a Pomeroy orientation device was used
             SO-ASC   an ASC orientation device was used
             SO-MAG   orientation with magnetic compass
        -loc: location name, default="unknown"
        -app appends to existing er_samples.txt file, default is to overwrite

    INPUT FORMAT
        Input files must be space delimited:
            Samp  Az Dip Strike Dip
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
            [5] site name same as sample
            [6] site is entered under a separate column
            [7-Z] [XXXX]YYY:  XXXX is site designation with Z characters with sample name XXXXYYYY
            NB: all others you will have to customize your self
                 or e-mail ltauxe@ucsd.edu for help.

    OUTPUT
            output saved in er_samples.txt  will overwrite any existing files
    """
    #
    # initialize variables
    #
    DEBUG = 0
    version_num = pmag.get_version()
    orient_file, samp_file, or_con, corr = "orient.txt", "er_samples.txt", "3", "1"
    args = sys.argv
    # date of sampling, latitude (pos North), longitude (pos East)
    date, lat, lon = "", "", ""
    bed_dip, bed_dip_dir = "", ""
    participantlist = ""
    sites = []   # list of site names
    Lats, Lons = [], []  # list of latitudes and longitudes
    # lists of Sample records and Site records
    SampRecs, SiteRecs, ImageRecs, imagelist = [], [], [], []
    samp_con, Z, average_bedding = "1", 1, "0"
    newbaseline, newbeddir, newbeddip = "", "", ""
    meths = 'FS-FD'
    delta_u = "0"
    sclass, lithology, type = "", "", ""
    newclass, newlith, newtype = '', '', ''
    user = ""
    corr == "3"
    DecCorr = 0.
    location_name = "unknown"
    #
    #
    if "-h" in args:
        print main.__doc__
        sys.exit()
    if "-f" in args:
        ind = args.index("-f")
        orient_file = sys.argv[ind + 1]
    if "-Fsa" in args:
        ind = args.index("-Fsa")
        samp_file = sys.argv[ind + 1]
    if "-ncn" in args:
        ind = args.index("-ncn")
        samp_con = sys.argv[ind + 1]
        if "4" in samp_con:
            if "-" not in samp_con:
                print "option [4] must be in form 4-Z where Z is an integer"
                sys.exit()
            else:
                Z = samp_con.split("-")[1]
                samp_con = "4"
        if "7" in samp_con:
            if "-" not in samp_con:
                print "option [7] must be in form 7-Z where Z is an integer"
                sys.exit()
            else:
                Z = samp_con.split("-")[1]
                samp_con = "7"
    if "-mcd" in args:
        ind = args.index("-mcd")
        meths = (sys.argv[ind + 1])
    if "-loc" in args:
        ind = args.index("-loc")
        location_name = (sys.argv[ind + 1])
    if '-app' in args:
        try:
            SampRecs, file_type = pmag.magic_read(samp_file)
            print "sample data to be appended to: ", samp_file
        except:
            print 'problem with existing samp file: ', samp_file, ' will create new'
    #
    # read in file to convert
    #
    azfile = open(orient_file, 'rU')
    AzDipDat = azfile.readlines()
    azfile.close()
    SampOut, samplist = [], []
    for line in AzDipDat:
        orec = line.split()
        if len(orec) > 2:
            labaz, labdip = pmag.orient(float(orec[1]), float(orec[2]), or_con)
            bed_dip = float(orec[4])
            if bed_dip != 0:
                # assume dip to right of strike
                bed_dip_dir = float(orec[3]) - 90.
            else:
                bed_dip_dir = float(orec[3])  # assume dip to right of strike
            MagRec = {}
            MagRec["er_location_name"] = location_name
            MagRec["er_citation_names"] = "This study"
    #
    # parse information common to all orientation methods
    #
            MagRec["er_sample_name"] = orec[0]
            MagRec["sample_bed_dip"] = '%7.1f' % (bed_dip)
            MagRec["sample_bed_dip_direction"] = '%7.1f' % (bed_dip_dir)
            MagRec["sample_dip"] = '%7.1f' % (labdip)
            MagRec["sample_azimuth"] = '%7.1f' % (labaz)
            methods = meths.replace(" ", "").split(":")
            OR = 0
            for method in methods:
                type = method.split("-")
                if "SO" in type:
                    OR = 1
            if OR == 0:
                meths = meths + ":SO-NO"
            MagRec["magic_method_codes"] = meths
            # parse out the site name
            site = pmag.parse_site(orec[0], samp_con, Z)
            MagRec["er_site_name"] = site
            MagRec['magic_software_packages'] = version_num
            SampOut.append(MagRec)
            if MagRec['er_sample_name'] not in samplist:
                samplist.append(MagRec['er_sample_name'])
    for samp in SampRecs:
        if samp not in samplist:
            SampOut.append(samp)
    Samps, keys = pmag.fillkeys(SampOut)
    pmag.magic_write(samp_file, Samps, "er_samples")
    print "Data saved in ", samp_file
main()
