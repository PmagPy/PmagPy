#!/usr/bin/env python
from __future__ import print_function
Lats,Lons,StaIDs=[],[],[]
StationNFO=open('station.list').readlines()
for line  in StationNFO:
    nfo=line.strip('\n').split()
    Lats.append(float(nfo[0]))
    Lons.append(float(nfo[1]))
    StaIDs.append(int(nfo[2]))
    print(Lats[-1],Lons[-1],StaIDs[-1])
