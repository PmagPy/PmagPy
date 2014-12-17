#!/usr/bin/env python
f=open('station.list','rU')
StationNFO=f.readlines()
for line  in StationNFO:
    print line
