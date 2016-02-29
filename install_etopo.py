#!/usr/bin/env python
import os
from os import path
from mpl_toolkits.basemap import basemap_datadir
from pmagpy import check_updates
pmag_dir = check_updates.get_pmag_dir()
print "installing etopo20 files from ", path.join(pmag_dir, 'data_files', 'etopo20', 'etopo20*')
print "to the basemap data directory: ",basemap_datadir
command='cp ' + path.join(pmag_dir, 'data_files', 'etopo20', 'etopo20*')  + " "+ basemap_datadir
os.system(command)
