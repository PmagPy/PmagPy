#!/usr/bin/env python
import os
from mpl_toolkits.basemap import basemap_datadir
print 'installing etopo20 files in the basemap data directory'
print basemap_datadir
os.system('cp etopo20* ' + basemap_datadir)
