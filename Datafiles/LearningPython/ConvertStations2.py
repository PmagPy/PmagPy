#!/usr/bin/env python
import UTM # imports the UTM module
outfile=open('mynewfile','w') # creates outfile object
Ellipsoid=23-1 # UTMs code for WGS-84
StationNFO=open('station.list').readlines()
for line  in StationNFO:
    nfo=line.strip('\n').split()
    lat=float(nfo[0])
    lon=float(nfo[1])
    StaName= nfo[3]
    Zone,Easting, Northing=UTM.LLtoUTM(Ellipsoid,lon,lat)
    outfile.write('%s  %s  %s  %s\n'%(StaName, Easting, Northing, Zone))
