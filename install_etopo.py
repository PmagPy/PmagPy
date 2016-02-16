#!/usr/bin/env python
import os
from mpl_toolkits.basemap import basemap_datadir
print 'installing etopo20 files in the basemap data directory'
print basemap_datadir
p=os.environ['PYTHONPATH'].strip(':')
os.system('cp '+p+'/data_files/etopo20/etopo20* ' + basemap_datadir)
