#! /usr/bin/env python

import sys
import traceback
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import subprocess

command_line = raw_input("what do you want to run?  ")
 # this may not really work....?

subprocess.call(command_line, shell=True)
