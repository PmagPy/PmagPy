
import sys
from importlib import import_module

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
_SUBMODULES = {
    'pmag': 'pmag',
    'ipmag': 'ipmag',
    'rockmag': 'rockmag',
    'pmagplotlib': 'pmagplotlib',
    'find_pmag_dir': 'find_pmag_dir',
    'version': 'version',
    'controlled_vocabularies': 'controlled_vocabularies2',
    'data_model3': 'data_model3',
    'contribution_builder': 'contribution_builder',
    'mapping': 'mapping',
}

__all__ = list(_SUBMODULES)


def __getattr__(name):
    if name not in _SUBMODULES:
        raise AttributeError(f"module 'pmagpy' has no attribute {name!r}")
    module = import_module(f'.{_SUBMODULES[name]}', __name__)
    globals()[name] = module
    return module


def __dir__():
    return sorted(list(globals().keys()) + __all__)
