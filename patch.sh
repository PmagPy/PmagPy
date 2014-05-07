#!/bin/bash

# patches issue with Canopy 1.4 where trying to run a wx program in the command line generates this error:  "Please run with a Framework build of python"
# 


cd ~/Library/Enthought/Canopy_64bit/User/bin
cp pythonw python
