#! /usr/bin/env python
from __future__ import print_function
from builtins import str
import sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
import pandas as pd


def main():
    """
        NAME
            nrm_specimens_magic.py

        DESCRIPTION
            converts NRM data in a measurements type file to
            geographic and tilt corrected data in a specimens type file

        SYNTAX
           nrm_specimens_magic.py [-h][command line options]

        OPTIONS:
            -h prints the help message and quits
            -f MFILE: specify input file
            -fsa SFILE: specify samples format file [with orientations]
            -F PFILE: specify output file
            -A  do not average replicate measurements
            -crd [g, t]: specify coordinate system ([g]eographic or [t]ilt adjusted)
                 NB: you must have the  SFILE in this directory

        DEFAULTS
            MFILE: measurements.txt
            PFILE: nrm_specimens.txt
            SFILE: samples.txt
            coord: g
            average replicate measurements?: YES


    """
#
#   define some variables
#
    beg, end, pole, geo, tilt, askave, save = 0, 0, [], 0, 0, 0, 0
    samp_file = 1
    args = sys.argv
    geo, tilt, orient = 0, 0, 0
    doave = 1
    user, comment, doave, coord = "", "", 1, "g"
    geo, orient = 1, 1

    dir_path = '.'
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        dir_path = sys.argv[ind + 1]
    meas_file = dir_path + "/measurements.txt"
    spec_file = dir_path + "/specimens.txt"
    samp_file = dir_path + "/samples.txt"
    out_file = dir_path + "/nrm_specimens.txt"
    if "-A" in args:
        doave = 0
    if "-f" in args:
        ind = args.index("-f")
        meas_file = sys.argv[ind + 1]
    if "-F" in args:
        ind = args.index("-F")
        out_file = dir_path + '/' + sys.argv[ind + 1]
    speclist = []
    if "-fsa" in args:
        ind = args.index("-fsa")
        samp_file = dir_path + '/' + sys.argv[ind + 1]
    if "-crd" in args:
        ind = args.index("-crd")
        coord = sys.argv[ind + 1]
        if coord == "t":
            tilt, orient, geo = 1, 1, 1
#
# read in data
    #
    meas_data = pd.read_csv(meas_file, header=1, sep='\t')
    meas_data = meas_data[meas_data['method_codes'].str.contains(
        'LT-NO') == True]  # fish out NRM data
    meas_data = meas_data[['specimen', 'dir_dec', 'dir_inc']]
    meas_data = meas_data.dropna(subset=['dir_dec', 'dir_inc'])
    meas_data = pd.DataFrame(meas_data)
#   import samples  for orientation info
#
##
    if orient == 1:
        spec_data = pd.read_csv(spec_file, header=1, sep='\t')
        spec_data = spec_data[['specimen', 'sample']]
        meas_data = pd.merge(meas_data, spec_data,
                             how='inner', on=['specimen'])
        samp_data = pd.read_csv(samp_file, header=1, sep='\t')
    #
    sids = meas_data.specimen.unique()  # list of specimen names
    #
    #
    NrmSpecRecs = []
    for spec in sids:
        gdec, ginc, bdec, binc = "", "", "", ""
        this_spec_data = meas_data[meas_data.specimen.str.contains(spec)]
        this_sample = this_spec_data['sample'].iloc[-1]
        this_sample_data = samp_data[samp_data['sample'].str.contains(
            this_sample)]
        this_sample_data = this_sample_data.to_dict('records')
        for m in this_spec_data.to_dict('records'):
            NrmSpecRec = {'specimen': spec, 'sample': this_sample}
            if coord == 'g':
                NrmSpecRec['dir_tilt_correction'] = '0'
            elif coord == 't':
                NrmSpecRec['dir_tilt_correction'] = '100'
            else:
                NrmSpecRec['dir_tilt_correction'] = '-1'
            if not orient:
                NrmSpecRec['dir_dec'] = m['dir_dec']
                NrmSpecRec['dir_inc'] = m['dir_inc']
                NrmSpecRec['method_codes'] = 'SO-NO'
                NrmSpecRecs.append(NrmSpecRec)
            else:  # do geographic correction
                # get the azimuth
                or_info, az_type = pmag.get_orient(
                    this_sample_data, this_sample, data_model=3)
                if 'azimuth' in or_info.keys() and or_info['azimuth'] != "":
                    azimuth = or_info['azimuth']
                    dip = or_info['dip']
                    gdec, ginc = pmag.dogeo(
                        m['dir_dec'], m['dir_inc'], azimuth, dip)
                    if tilt:
                        # try tilt correction
                        if 'bed_dip' in or_info.keys() and or_info['bed_dip'] != "":
                            bed_dip = or_info['bed_dip']
                            bed_dip_dir = or_info['bed_dip_direction']
                            bdec, binc = pmag.dogeo(
                                gdec, ginc, bed_dip_dir, bed_dip)
                            NrmSpecRec['dir_dec'] = bdec
                            NrmSpecRec['dir_inc'] = binc
                            NrmSpecRec['method_codes'] = az_type
                            NrmSpecRecs.append(NrmSpecRec)
                        else:
                            print('no bedding orientation data for ', spec)

                    else:
                        NrmSpecRec['dir_dec'] = gdec
                        NrmSpecRec['dir_inc'] = ginc
                        NrmSpecRec['method_codes'] = az_type
                        NrmSpecRecs.append(NrmSpecRec)
                else:
                    print('no geo orientation data for ', spec)

    pmag.magic_write(out_file, NrmSpecRecs, 'specimens')


if __name__ == "__main__":
    main()
