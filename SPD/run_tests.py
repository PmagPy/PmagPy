#!/usr/bin/env python
# run_tests.py: -*- Python -*-  DESCRIPTIVE TEXT.
# 
#  Copyright (c) 2014 Lori Jonestrask
#  Author: Lori Jonestrask (mintblue87@gmail.com) .

import unittest
import os

cwd = os.getcwd()
loader = unittest.TestLoader()
suite = loader.discover(cwd)
unittest.TextTestRunner(verbosity=2).run(suite)
