#!/usr/bin/env python

from __future__ import print_function
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
        programs_list = os.listdir(programs_WD)
        if not sys.platform in ['win32', 'win62']:
            conversion_scripts = os.listdir(os.path.join(programs_WD,
                                                         'conversion_scripts'))
            programs_list.extend(conversion_scripts)
            conversion_scripts2 = os.listdir(os.path.join(programs_WD,
                                                          'conversion_scripts2'))
            programs_list.extend(conversion_scripts2)
        not_checked = []
        pip_anaconda = False
        if sys.platform in ['win32', 'win62']:
            res = self.env.run('where angle.py')
            if res.stderr:
                pip_anaconda = True
        for prog in programs_list:
            if prog in ['__init__.py', 'program_envs.py', 'template_magic.py']:
                continue
            if 'gui' in prog:
                continue
            if prog.endswith('.pyc') or '#' in prog:
                continue
            if not prog.endswith('.py'):
                not_checked.append(prog)
                continue
            if prog.lower() != prog:
                not_checked.append(prog)
                continue
            if pip_anaconda: #
                prog = prog[:-3]
            print("Testing help message for:", prog)
            res = self.env.run(prog, '-h')
            #except AssertionError as ex:
            #    not_checked.append(prog)
            #    print 'ex', type(ex)
            #    print res
        print('not_checked', not_checked)

    def test_guis(self):
        tests = ['pmag_gui.py', 'magic_gui.py', #'demag_gui.py',
                 'thellier_gui.py']
        pip_anaconda = False
        if sys.platform in ['win32', 'win62']:
            res = self.env.run('where angle.py')
            if res.stderr:
                pip_anaconda = True

        for prog in tests:
            if pip_anaconda: # sys.platform in ['win32', 'win62']:
                prog = prog[:-3]
            print('testing:', prog)
            res = self.env.run(prog, '-h')

    #def test_help(self):
    #    res = self.env.run('template_magic.py', '-h')

    @unittest.skipIf(('Anaconda' not in sys.version.split()[1]) or (sys.version_info >= (3,)), 'only needed for Anaconda')
    def test_guis_anaconda(self):
        tests = ['pmag_gui_anaconda', 'magic_gui_anaconda',
                 'magic_gui2_anaconda',# 'demag_gui_anaconda',
                 'thellier_gui_anaconda']
        pip_anaconda = False
        if sys.platform in ['win32', 'win62']:
            res = self.env.run('where angle.py')
            if res.stderr:
                pip_anaconda = True
        if not pip_anaconda:
            return
        for prog in tests:
            print('testing:', prog)
            #res = self.env.run(prog, '-h')
            res = os.system(prog + " -h")
            self.assertEqual(res, 0)
