#!/usr/bin/env python

import sys
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
        -DM: specify data model (2 or 3).  Default: 3.  Will output to the appropriate format.


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
            output saved in er_samples.txt and er_sites.txt (or samples.txt and sites.txt if using data model 3.0)
            - this will overwrite any existing files
    """
    args = sys.argv
    if "-h" in args:
        print(main.__doc__)
        sys.exit()
    else:
        info = [['WD', False, '.'], ['ID', False, ''], ['f', False, 'orient.txt'],
                ['app', False, False], ['ocn', False, 1], ['dcn', False, 1],
                ['BCN', False, True], ['ncn', False, '1'], ['gmt', False, 0],
                ['mcd', False, ''], ['a', False, False], ['DM', False, 3]]

        #output_dir_path, input_dir_path, orient_file, append, or_con, dec_correction_con, samp_con, hours_from_gmt, method_codes, average_bedding
        # leave off -Fsa, -Fsi b/c defaults in command_line_extractor
        dataframe = extractor.command_line_dataframe(info)
        checked_args = extractor.extract_and_check_args(args, dataframe)
        output_dir_path, input_dir_path, orient_file, append, or_con, dec_correction_con, bed_correction, samp_con, hours_from_gmt, method_codes, average_bedding, samp_file, site_file, data_model = extractor.get_vars(['WD', 'ID', 'f', 'app', 'ocn', 'dcn', 'BCN', 'ncn', 'gmt', 'mcd', 'a', 'Fsa', 'Fsi', 'DM'], checked_args)
        if input_dir_path == '.':
            input_dir_path = output_dir_path

        if not isinstance(dec_correction_con, int):
            if len(dec_correction_con) > 1:
                dec_correction = int(dec_correction_con.split()[1])
                dec_correction_con = int(dec_correction_con.split()[0])
            else:
                dec_correction = 0
        else:
            dec_correction = 0

        ipmag.orientation_magic(or_con, dec_correction_con, dec_correction, bed_correction, samp_con, hours_from_gmt, method_codes, average_bedding, orient_file, samp_file, site_file, output_dir_path, input_dir_path, append, data_model)


if __name__ == "__main__":
    main()
