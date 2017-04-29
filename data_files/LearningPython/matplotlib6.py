#!/usr/bin/env python
from builtins import str
from builtins import range
import matplotlib
matplotlib.use("TkAgg")
import pylab
from readEQs import *
EQs=readEQs('merged_catalog.xml')
Fracs,Labels=[],[]
bin0=0
for m in range(1,8):  # assume no magnitudes bigger than 8 last week!
    num=0 # initialize count
    for eq in EQs:
        eqm=float(eq['magnitude'])
        if eqm<m and eqm>bin0:num+=1 # count all magnitudes in this bin
    Fracs.append(float(num))
    Labels.append(str(bin0)+'-'+str(m))
    bin0=m # increment to next bin
pylab.pie(Fracs, labels=Labels) 
pylab.axis('equal') # make the pie round!
pylab.title('Silly Pie Chart')
pylab.show()  
