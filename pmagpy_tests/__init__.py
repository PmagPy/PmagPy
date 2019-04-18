from __future__ import absolute_import
import matplotlib
matplotlib.use('WXAgg')
import sys
import os
if "-pip" in sys.argv:
    os.chdir(sys.prefix)

from pmagpy_tests import test_builder
from pmagpy_tests import test_er_magic_dialogs
from pmagpy_tests import test_ipmag
from pmagpy_tests import test_magic_gui
from pmagpy_tests import test_pmag
from pmagpy_tests import test_pmag_gui
from pmagpy_tests import test_thellier_gui
from pmagpy_tests import test_validations
from pmagpy_tests import test_programs
from pmagpy_tests import test_demag_gui
from pmagpy_tests import test_magic_gui2
from pmagpy_tests import test_contribution_builder
from pmagpy_tests import test_find_pmag_dir
from pmagpy_tests import test_map_magic

__all__ = [test_builder, test_er_magic_dialogs, test_ipmag,
           test_magic_gui, test_pmag, test_pmag_gui, test_thellier_gui,
           test_validations, test_programs, test_demag_gui,
           test_magic_gui2, test_contribution_builder, test_find_pmag_dir,
           test_map_magic]
