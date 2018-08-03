from __future__ import absolute_import
import matplotlib
matplotlib.use('WXAgg')
import sys
import os
if "-pip" in sys.argv:
    os.chdir(sys.prefix)

import pmagpy_tests.test_builder as test_builder
import pmagpy_tests.test_er_magic_dialogs as test_er_magic_dialogs
import pmagpy_tests.test_ipmag as test_ipmag
import pmagpy_tests.test_magic_gui as test_magic_gui
import pmagpy_tests.test_pmag as test_pmag
import pmagpy_tests.test_pmag_gui as test_pmag_gui
import pmagpy_tests.test_thellier_gui as test_thellier_gui
import pmagpy_tests.test_validations as test_validations
import pmagpy_tests.test_programs as test_programs
import pmagpy_tests.test_demag_gui as test_demag_gui
import pmagpy_tests.test_magic_gui2 as test_magic_gui2
import pmagpy_tests.test_contribution_builder as test_contribution_builder
import pmagpy_tests.test_find_pmag_dir as test_find_pmag_dir
import pmagpy_tests.test_map_magic as test_map_magic

__all__ = [test_builder, test_er_magic_dialogs, test_ipmag,
           test_magic_gui, test_pmag, test_pmag_gui, test_thellier_gui,
           test_validations, test_programs, test_demag_gui,
           test_magic_gui2, test_contribution_builder, test_find_pmag_dir,
           test_map_magic]
