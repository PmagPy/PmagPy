#!/usr/bin/env python
from builtins import map
import matplotlib
matplotlib.use("TkAgg")
import pylab,numpy
from readEQs import *
from mpl_toolkits.basemap import Basemap
EQs=readEQs('merged_catalog.xml')
Lats,Lons=[],[]
for eq in EQs:
    Lats.append(float(eq['latitude']))
    Lons.append(float(eq['longitude']))
#map=Basemap(projection='moll',lon_0=0,resolution='c',area_thresh=1000.)
map=Basemap(projection='moll',lon_0=0,resolution='c')
map.drawcoastlines()
map.drawmapboundary()
map.drawmeridians(numpy.arange(0,360,30)) # draws longitudes from list
map.drawparallels(numpy.arange(-60,90,30)) # draws latitudes from list
X,Y=list(map(Lons,Lats)) # calculates the projection of the X,Y
pylab.plot(X,Y,'ro') # uses pylab's plot to plot these arrays
#pylab.show() #
pylab.savefig('map.eps')
