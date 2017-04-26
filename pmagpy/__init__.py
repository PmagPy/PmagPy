import sys
if sys.version_info >= (3,):
    raise Exception("""
You are running Python {}.
This version of pmagpy is only compatible with Python 2.
Make sure you have pip >= 9.0 to avoid this kind of issue,
as well as setuptools >= 24.2:

 $ pip install pip setuptools --upgrade

Then you should be able to download the correct version of pmagpy:

 $ pip install pmagpy --upgrade

If this still gives you an error, please report the issue:
https://github.com/PmagPy/PmagPy/issues

Thanks!

""".format(sys.version))
import pmag
import ipmag
import pmagplotlib
import find_pmag_dir
import version
import controlled_vocabularies2 as controlled_vocabularies
import data_model3
import new_builder
import mapping
#import set_env

__all__ = [pmag, ipmag, pmagplotlib, find_pmag_dir, version,
           controlled_vocabularies, data_model3, new_builder,
           mapping]
