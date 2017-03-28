#!/usr/bin/env python
from __future__ import print_function
f=open('station.list')
StationNFO=f.readlines()
for line  in StationNFO:
    print(line)
