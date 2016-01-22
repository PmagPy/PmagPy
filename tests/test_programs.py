#!/usr/bin/env python

from scripttest import TestFileEnvironment
env = TestFileEnvironment('./new-test-output')
import unittest
import os
import sys
import subprocess
import pmagpy.check_updates as check_updates
#import matplotlib
#import pmagpy.pmag as pmag
#import pmagpy.ipmag as ipmag

WD = check_updates.get_pmag_dir()
programs_WD = os.path.join(WD, 'programs')

class TestProgramsHelp(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skipIf(sys.platform not in ['darwin', 'win32', 'win62'], "Doesn't work without PmagPy in PYTHONPATH")
    def test_all(self):
        programs = os.listdir(programs_WD)
        not_checked = []
        for prog in programs:
            print "Testing help message for:", prog
            if prog == '__init__.py':
                continue
            if not prog.endswith('.py'):
                not_checked.append(prog)
                continue
            res = env.run(prog, '-h')
            #except AssertionError as ex:
            #    not_checked.append(prog)
            #    print 'ex', type(ex)
            #    print res
        print 'not_checked', not_checked


