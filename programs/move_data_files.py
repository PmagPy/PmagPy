#!/usr/bin/env python

"""
Move data_files directory from default location (sys.prefix) or specified location
to chosen directory.
Results in PmagPy-data directory which contains notebooks and data_files.
"""

import shutil
import sys
import os
from os import path
from pmagpy import pmag
from pmagpy import find_pmag_dir


def copy_directory(src, dest):
    dest = path.join(dest, 'data_files')
    print('-I- Copying {} to {}'.format(src, dest))
    try:
        shutil.copytree(src, dest)
        # Directories are the same
    except shutil.Error as error:
        print('-W- Directory not copied. Error: %s' % error)
        # Any error saying that the directory doesn't exist
    except OSError as error:
        print('-W- Directory not copied. Error: %s' % error)
        print("    If you have a developer install, move_data_files.py won't work.  Simply navigate to your PmagPy directory.  You can find data_files, PmagPy.ipynb and PmagPy-cli.ipynb there.")


def main():
    if '-h' in sys.argv:
        print("    Help for move_data_files.py:")
        print("    Choose the folder where you want the PmagPy data files to be.")
        print("    Navigate to that folder, and use the command: 'move_data_files.py'")
        print("    Alternatively, you may use the full path to the directory of your choice from anywhere in the file system, using the '-d' flag: 'move_data_files.py -d /Users/***/Desktop' where *** is your username")
        print("    **IMPORTANT** If you have a developer install, this won\'t work.  Simply navigate to your PmagPy directory.  You can find data_files, PmagPy.ipynb and PmagPy-cli.ipynb there.")
        sys.exit()
    # create PmagPy-data directory
    dest = pmag.get_named_arg('-d', '.', False)
    dest = path.realpath(dest)
    dest = path.join(dest, 'PmagPy-data')
    if not path.exists(dest):
        try:
            os.mkdir(dest)
        except FileNotFoundError:
            pass
    # get source of data_files
    source = pmag.get_named_arg('-s', sys.prefix, False)
    source = path.realpath(source)
    if source.endswith('data_files') or source.endswith('data_files/'):
        source = path.split(source)[0]
    # copy data_files to PmagPy-data directory
    data_files = path.join(source, 'data_files')
    copy_directory(data_files, dest)
    # now try to get notebooks
    pmagpy_dir = find_pmag_dir.get_pmag_dir()
    for notebook in ['PmagPy.ipynb', 'PmagPy-cli.ipynb']:
        # for pip install
        notebook_location = path.join(dest, 'data_files', notebook)
        if path.exists(notebook_location):
            shutil.copy(path.join(dest, 'data_files', notebook), path.join(dest, notebook))
        # for developer install
        elif pmagpy_dir:
            if path.exists(path.join(pmagpy_dir, notebook)):
                shutil.copy(path.join(pmagpy_dir, notebook), path.join(dest, notebook))


if __name__ == "__main__":
    main()
