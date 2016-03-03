#!/usr/bin/env python

import shutil
import sys
from os import path
from pmagpy import pmag


def copy_directory(src, dest):
    dest = path.join(dest, 'pmagpy_data_files')
    print '-I- Copying {} to {}'.format(src, dest)
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
        print "Some help"
        sys.exit()
    dest = pmag.get_named_arg_from_sys('-d', None, True)
    data_files = path.join(sys.prefix, 'pmagpy_data_files')
    copy_directory(data_files, dest)


if __name__ == "__main__":
    main()
