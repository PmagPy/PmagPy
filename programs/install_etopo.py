#!/usr/bin/env python
from __future__ import print_function
import os
from os import path
import sys
from pmagpy import pmag


def main():
    try:
        from mpl_toolkits.basemap import basemap_datadir
    except:
        print("-E- Could not import the basemap module...")
    else:
        # allow user to specify what directory to find the data_files in
        custom_dir = pmag.get_named_arg_from_sys('-source-dir', default_val="")
        if os.path.isdir(custom_dir):
            data_dir = custom_dir
        # if user didn't specify a directory, find the etopo20 directory
        else:
            # if installed by pip, etopo20 is in sys.prefix
            pip_data_dir = os.path.join(sys.prefix, 'data_files', 'etopo20')
            if os.path.isdir(pip_data_dir):
                data_dir = pip_data_dir
            else:
                # if not installed by pip, etopo20 is in the local PmagPy directory
                from pmagpy import find_pmag_dir
                pmag_dir = find_pmag_dir.get_pmag_dir()
                data_dir = os.path.join(pmag_dir, 'data_files', 'etopo20')
        # if none of those options worked, warn the user:
        if not os.path.isdir(data_dir):
            print("-W- Could not find data_files to copy in {}".format(data_dir))
            print("-I- You can run this program with the command line flag -source-dir to specify the location of the etopo20 directory.")
            print("-I- For example: 'install_etopo.py -source-dir ~/Python/PmagPy/data_files/etopo20'")
            return
        print("installing etopo20 files from ", path.join(data_dir, 'etopo20*'))
        print("to the basemap data directory: ",basemap_datadir)
        command = 'cp ' + path.join(data_dir, 'etopo20*')  + " "+ basemap_datadir
        os.system(command)

if __name__ == "__main__":
    main()
