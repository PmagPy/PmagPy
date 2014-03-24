#! /usr/bin/env python                                                                                                                        
import sys
import os
from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import subprocess
import PmagPy_tests as PT
import error_logging as EL

#import Extra_output


file_prefix = os.getcwd() + '/'
directory = os.getcwd()

test_file_prefix = file_prefix + 'Command_line_Tests/'
test_directory = directory + '/Command_line_Tests'
print file_prefix
print directory
print os.getcwd()


if __name__ == '__main__':
     obj = env.run(file_prefix + 'angle.py', '-f', test_file_prefix + 'angle.dat', '-F', test_file_prefix + 'zebra_angle_results_new.out')
     print obj.stdout
     print obj.files_created
     print obj.files_updated
     print dir(obj)
     obj = env.run(file_prefix + 'angle.py', '-h')
     print obj.stdout




rename_me_errors_list = open('rename_me_errors_list.txt', 'w')
"""

if __name__ == '__main__':
     if "-r" in sys.argv:
          PT.run_individual_program(rename_me_tests)
     elif "-all" in sys.argv:
          complete_working_test()
          print "remember to delete *_new.out files as needed"
     else:
          new_list = EL.go_through(rename_me_tests, rename_me_errors_list)
          EL.redo_broken_ones(new_list)

"""     
# run as: python Rename_me.py > rename_me_full_output.txt
# then: python clean_output.py
     # input: rename_me_full_output.txt
     # output: rename_me_clean_output.txt



