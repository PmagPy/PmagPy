#!/usr/bin/env python

# https://makerhacks.com/thumbnail-images-using-python/

import sys
import os
import glob
from PIL import Image
from pmagpy import pmag

def main(directory):
    # get all the jpg files from the current folder
    directory = os.path.realpath(directory)
    for infile in glob.glob(os.path.join(directory, "*.png")):
        if infile.endswith('thumb.png'):
            continue
        im = Image.open(infile)
    # convert to thumbnail image
        im.thumbnail((128, 128), Image.ANTIALIAS)
    # prefix thumbnail file with T_
        im.save(infile[:-4] + ".thumb.png", "PNG")


if __name__ == "__main__":
    if "-h" in sys.argv:
        print('Make thumbnails for every png in current directory, or use: thumbnails.py -WD <directory>')
        print('Output files will follow the naming convention: "original_filename.thumb.png"')
    else:
        directory = pmag.get_named_arg("-WD", ".")
        main(directory)
