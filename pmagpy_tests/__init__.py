from __future__ import absolute_import
import matplotlib
matplotlib.use('WXAgg')
import sys
import os
if "-pip" in sys.argv:
    os.chdir(sys.prefix)

from . import test_builder
from . import test_er_magic_dialogs
from . import test_imports
from . import test_ipmag
from . import test_magic_gui
from . import test_pmag
from . import test_pmag_gui
from . import test_thellier_gui
from . import test_validations
from . import test_programs
from . import test_demag_gui
from . import test_magic_gui2
from . import test_new_builder
from . import test_find_pmag_dir
from . import test_map_magic

__all__ = [test_builder, test_er_magic_dialogs, test_imports, test_ipmag,
           test_magic_gui, test_pmag, test_pmag_gui, test_thellier_gui,
           test_validations, test_programs, test_demag_gui,
           test_magic_gui2, test_new_builder, test_find_pmag_dir,
           test_map_magic]
