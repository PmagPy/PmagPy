#!/usr/bin/env python

# https://makerhacks.com/thumbnail-images-using-python/

import sys
import os
import glob
from PIL import Image
from pmagpy import pmag

def main(directory, fmt):
    # get all the jpg files from the current folder
    directory = os.path.realpath(directory)
    for infile in glob.glob(os.path.join(directory, "*.{}".format(fmt))):
        if infile.endswith('thumb.{}'.format(fmt)):
            continue
        im = Image.open(infile)
    # convert to thumbnail image
        im.thumbnail((128, 128), Image.ANTIALIAS)
    # add .thumb to file extension
        im.save(infile[:-4] + ".thumb.{}".format(fmt), fmt)


if __name__ == "__main__":
    if "-h" in sys.argv:
        print('Make thumbnails for every png in current directory, or use: thumbnails.py -WD <directory>')
        print('Specify input/output format with: -fmt <format>.   Tested formats include [jpg, png]')
        print('Output files will follow the naming convention: "original_filename.thumb.fmt"')
    else:
        main(pmag.get_named_arg("-WD", "."), pmag.get_named_arg("-fmt", "png"))
