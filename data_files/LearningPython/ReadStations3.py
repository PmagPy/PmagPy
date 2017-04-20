#!/usr/bin/env python
from __future__ import print_function
import sys
Lats,Lons,StaIDs,StaName=[],[],[] ,[]# creates lists to put things in
if '-f' in sys.argv:  # look in list of command line arguments
    file=sys.argv[sys.argv.index('-f')+1] # find index of '-f' and increment by one
StationNFO=open(file,'r').readlines() # open file
for line  in StationNFO:
    nfo=line.strip('\n').split() # strips off the line ending and splits on spaces
    Lats.append(float(nfo[0])) # puts float of 1st column into Lats
    Lons.append(float(nfo[1]))# puts float of 2nd column into Lons
    StaIDs.append(int(nfo[2])) # puts integer of 3rd column into StaIDs
    StaName.append(nfo[3])# puts the ID string into StaName
    print(Lats[-1],Lons[-1],StaIDs[-1]) # prints out last thing appended
