import matplotlib
import sys
import os
isServer = False
verbose = True
IS_WIN = True if sys.platform in ['win32', 'win64'] else False
IS_LINUX = True if 'linux' in sys.platform else False
IS_FROZEN = getattr(sys, 'frozen', False)
IS_NOTEBOOK = True if 'JPY_PARENT_PID' in os.environ else False
OFFLINE = False
#  other way to test for notebook: see if get_ipython raises a NameError

def set_backend(wx=True):
    if wx:
        matplotlib.use('WXAgg')
    else:
        matplotlib.use('TKAgg')

def set_server(boolean=True):
    isServer = boolean

def set_verbose(boolean=True):
    verbose = boolean
