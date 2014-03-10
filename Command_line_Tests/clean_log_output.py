#! /usr/bin/env python

import sys
import traceback
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
#import Rename_me
import PmagPy_tests as PT
import subprocess

def clean_output_file(infile, outfile):
    """Takes an infile and an outfile as arguments.  It takes the relevant portion of the infile and writes it to the outfile """
    a_file = open(infile, 'rU')
    info = a_file.readlines()
    rhino = False
    new_file = open(outfile, 'w')
    for l in info:
        if "rhino" in l:  # 'rhino' is the marker for the relevant output
            rhino = True
        if rhino:
            new_file.write(l)
    print str(outfile) + " is  ready"

def clean_all_output_logs():
    """Cleans all four of the relevant output logs"""
    print "cleaning all output logs"
    clean_output_file('extra_out_full_output.txt', 'extra_out_clean_output.txt')
    clean_output_file('rename_me_full_output.txt', 'rename_me_clean_output.txt')
    clean_output_file('random_full_output.txt', 'random_clean_output.txt')
    clean_output_file('bootstrap_full_output.txt', 'bootstrap_clean_output.txt')
    # add in for whatever else there is ... that's all??
    print "finished cleaning all output logs"
    
if __name__ == "__main__": # so it can be done interactively on the command line, but doesn't have to be.  
# the issue is that you have to run it as a separate call then the initial log creating
    if '-all' in sys.argv:
        clean_all_output_logs()
    else:
        file_in = raw_input("what file do you want to clean?  ")
        file_out = raw_input("what do you want to call the cleaned file?  ")
        clean_output_file(file_in, file_out)
