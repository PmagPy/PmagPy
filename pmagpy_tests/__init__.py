import matplotlib
matplotlib.use('WXAgg')
import sys
import os
if "-pip" in sys.argv:
    os.chdir(sys.prefix)

import test_builder
import test_er_magic_dialogs
import test_imports
import test_ipmag
import test_magic_gui
import test_pmag
import test_pmag_gui
import test_thellier_gui
import test_validations
import test_programs
import test_demag_gui
import test_magic_gui2
import test_new_builder
import test_find_pmag_dir
import test_map_magic

__all__ = [test_builder, test_er_magic_dialogs, test_imports, test_ipmag,
           test_magic_gui, test_pmag, test_pmag_gui, test_thellier_gui,
           test_validations, test_programs, test_demag_gui,
           test_magic_gui2, test_new_builder, test_find_pmag_dir,
           test_map_magic]
