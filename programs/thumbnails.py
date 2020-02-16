#!/usr/bin/env python

# https://makerhacks.com/thumbnail-images-using-python/

import sys
import os
import glob
from PIL import Image
import datetime
from pmagpy import pmag

def error_log(msg):
    with open('thumbnail_errors.txt', 'a') as log:
        log.write(msg + '\t' + str(datetime.datetime.now()) + '\n')
    sys.stderr.write(msg + '\n')

def make_thumbnails(directory=".", fmt="png"):
    # get all the jpg files from the current folder
    directory = os.path.realpath(directory)
    for infile in glob.glob(os.path.join(directory, "*.{}".format(fmt))):
        if infile.endswith('thumb.{}'.format(fmt)):
            continue
        im = Image.open(infile)
        #
        lower_infile = infile.lower()
        width, height = im.size   # Get dimensions
        if "ty:_eqarea_interpretations" in lower_infile:
            left = 0 + width * .255
            top = 0 + height * .21
            right = width * .77
            bottom = height * .8
        elif "ty:_eqarea_" in lower_infile or "ty:_eq" in lower_infile:
            left = 0 + width * .185
            top = 0 + height * .195
            right = width * .84
            bottom = height * .81
        elif "ty:_vgp_map" in lower_infile:
            left = 0 + width * .05
            top = 0 + height * .25
            right = width * .95
            bottom = height * .75
        elif "ty:_zijd_" in lower_infile:
            left = 0 + width * .15
            top = 0 + height * .16
            right = width * .895
            bottom = height * .85
        elif "ty:_demag_" in lower_infile:
            left = 0 + width * .17
            top = 0 + height * .16
            right = width * .895
            bottom = height * .82
        elif "ty:_deremag_" in lower_infile:
            left = 0 + width * .17
            top = 0 + height * .16
            right = width * .9
            bottom = height * .825
        elif "ty:_arai_" in lower_infile:
            left = 0 + width * .1555
            top = 0 + height * .15
            right = width * .9
            bottom = height * .82
        elif "ty:_hyst_" in lower_infile:
            left = 0 + width * .14
            top = 0 + height * .13
            right = width * .89
            bottom = height * .88
        elif "ty:_pole_map" in lower_infile:
            left = 0 + width * .185
            top = 0 + height * .15
            right = width * .84
            bottom = height * .865
        elif "ty:_intensities_histogram" in lower_infile:
            # include all 4 bounding lines
            left = 0 + width * .124
            top = 0 + height * .155
            right = width * .902
            bottom = height * .86
            #
            # include no bounding lines
            #left = 0 + width * .126
            #top = 0 + height * .16
            #right = width * .895
            #bottom = height * .85
            #
            # include only the bottom bounding line
            #left = 0 + width * .126
            #top = 0 + height * .16
            #right = width * .895
            #bottom = height * .86
        elif "ty:_aniso_data" in lower_infile or "ty:_aniso_conf" in lower_infile:
            left = 0 + width * .215
            top = 0 + height * .115
            right = width * .86
            bottom = height * .875
        elif "ty:_aniso_tcdf" in lower_infile:
            left = 0 + width * .124
            top = 0 + height * .155
            right = width * .902
            bottom = height * .86
        elif "ty:_day" in lower_infile:
            left = 0 + width * .124
            top = 0 + height * .12
            right = width * .902
            bottom = height * .855
        elif "ty:_s-bc" in lower_infile or "ty:_s-bcr" in lower_infile:
            left = 0 + width * .124
            top = 0 + height * .12
            right = width * .902
            bottom = height * .892
        else:
            error_log("Could not crop {}".format(infile))
            im.save(infile[:-4] + ".thumb.{}".format(fmt), fmt, dpi=(300, 300))
            continue
        cropped = im.crop((left, top, right, bottom))
        cropped.thumbnail((300, 300), Image.ANTIALIAS)
        cropped.save(infile[:-4] + ".thumb.{}".format(fmt), fmt, dpi=(300, 300))
        # Pixels ÷ DPI = Inches


if __name__ == "__main__":
    if "-h" in sys.argv:
        print('Make thumbnails for every png in current directory, or use: thumbnails.py -WD <directory>')
        print('Specify input/output format with: -fmt <format>.   Tested formats include [jpg, png]')
        print('Output files will follow the naming convention: "original_filename.thumb.fmt"')
    else:
        make_thumbnails(pmag.get_named_arg("-WD", "."), pmag.get_named_arg("-fmt", "png"))
