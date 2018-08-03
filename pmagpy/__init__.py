from __future__ import absolute_import
import sys
if sys.version_info <= (3,):
    raise Exception("""
You are running Python {}.
This version of pmagpy is only compatible with Python 3.
Make sure you have pip >= 9.0 to avoid this kind of issue,
as well as setuptools >= 24.2:

 $ pip install pip setuptools --upgrade

Then you should be able to download the correct version of pmagpy:

 $ pip install pmagpy --upgrade

If this still gives you an error, please report the issue:
https://github.com/PmagPy/PmagPy/issues

Thanks!

""".format(sys.version))
from . import pmag
from . import ipmag
from . import pmagplotlib
from . import find_pmag_dir
from . import version
from . import controlled_vocabularies2 as controlled_vocabularies
from . import data_model3
from . import contribution_builder
from . import mapping
#import set_env

__all__ = [pmag, ipmag, pmagplotlib, find_pmag_dir, version,
           controlled_vocabularies, data_model3, contribution_builder,
           mapping]
