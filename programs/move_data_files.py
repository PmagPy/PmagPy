#!/usr/bin/env python

from __future__ import print_function
import shutil
import sys
from os import path
from pmagpy import pmag


def copy_directory(src, dest):
    dest = path.join(dest, 'data_files')
    print('-I- Copying {} to {}'.format(src, dest))
    try:
        shutil.copytree(src, dest)
        # Directories are the same
    except shutil.Error as e:
        print('Directory not copied. Error: %s' % e)
        # Any error saying that the directory doesn't exist
    except OSError as e:
        print('Directory not copied. Error: %s' % e)


def main():
    if '-h' in sys.argv:
        print("Choose the folder where you want the PmagPy data files to be.")
        print("Navigate to that folder, and use the command: 'move_data_files.py -d .'")
        print("Alternatively, you may use the full path to the directory of your choice from anywhere in the file system: 'move_data_files.py -d /Users/***/Desktop' where *** is your username")
        sys.exit()
    dest = pmag.get_named_arg_from_sys('-d', None, True)
    data_files = path.join(sys.prefix, 'data_files')
    copy_directory(data_files, dest)


if __name__ == "__main__":
    main()
