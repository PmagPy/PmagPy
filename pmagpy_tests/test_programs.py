#!/usr/bin/env python

from scripttest import TestFileEnvironment
import os
import unittest
import shutil
import sys
from pkg_resources import resource_filename
import programs

# set constants
fname = resource_filename(programs.__name__, 'angle.py')
programs_WD = os.path.split(fname)[0]
#env = TestFileEnvironment('./new-test-output')


@unittest.skipIf(sys.platform not in ['darwin', 'win32', 'win62'],
                 "Doesn't work without PmagPy in PYTHONPATH")
class TestProgramsHelp(unittest.TestCase):

    def spawn_tests(self):
        programs = os.listdir(programs_WD)
        not_checked = []
        for prog in programs:
            if prog in ['__init__.py', 'program_envs.py']:
                continue
            if not prog.endswith('.py') or '#' in prog:
                not_checked.append(prog)
                continue
            if prog.lower() != prog:
                continue
            #res = env.run(prog, '-h')
            return prog

    def setUp(self):
        if os.path.exists('./new-test-output'):
            shutil.rmtree('./new-test-output')
        self.env = TestFileEnvironment('./new-test-output')
        #if not os.path.exists('./new-test-output'):
        #    os.mkdir('./new-test-output')

    def tearDown(self):
        if os.path.exists('./new-test-output'):
            shutil.rmtree('./new-test-output')

    def test_cmd_line(self):
        print 'programs_WD', programs_WD
        programs = os.listdir(programs_WD)
        not_checked = []
        for prog in programs:
            print "Testing help message for:", prog
            if prog in ['__init__.py', 'program_envs.py']:
                continue
            if 'gui' in prog:
                continue
            if not prog.endswith('.py') or '#' in prog:
                not_checked.append(prog)
                continue
            if prog.lower() != prog:
                continue
            if sys.platform in ['win32', 'win62']:
                prog = prog[:-3]
            res = self.env.run(prog, '-h')
            #except AssertionError as ex:
            #    not_checked.append(prog)
            #    print 'ex', type(ex)
            #    print res
        print 'not_checked', not_checked

    def test_guis(self):
        tests = ['pmag_gui.py', 'magic_gui.py', #'demag_gui.py',
                 'thellier_gui.py']
        for prog in tests:
            if sys.platform in ['win32', 'win62']:
                prog = prog[:-3]
            print 'testing:', prog
            res = self.env.run(prog, '-h')

    @unittest.skipIf('Anaconda' not in sys.version.split()[1], 'only needed for Anaconda')
    def test_guis_anaconda(self):
        tests = ['pmag_gui_anaconda', 'magic_gui_anaconda',
                 'magic_gui2_anaconda',# 'demag_gui_anaconda',
                 'thellier_gui_anaconda']
        for prog in tests:
            print 'testing:', prog
            #res = self.env.run(prog, '-h')
            res = os.system(prog + " -h")
            self.assertEqual(res, 0)
