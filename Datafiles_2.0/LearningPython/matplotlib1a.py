#!/usr/bin/env python
import matplotlib
matplotlib.use("TkAgg") 
import pylab 
pylab.ion()  # turn on interactivity
pylab.plot([1,2,3]) 
pylab.ylabel('Y') 
pylab.draw() # draw  the current plot
ans=raw_input('press [s] to save figure, any other key to quit: ')
if ans=='s':
    pylab.savefig('myfig.eps')
