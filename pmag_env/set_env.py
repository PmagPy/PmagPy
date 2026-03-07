import matplotlib
import sys
import os
isServer = False
verbose = True
IS_WIN = True if sys.platform in ['win32', 'win64'] else False
IS_LINUX = True if 'linux' in sys.platform else False
IS_FROZEN = getattr(sys, 'frozen', False)
try:
    from IPython import get_ipython

    ip = get_ipython()
    shell = ip.__class__.__name__ if ip is not None else ""
    IS_NOTEBOOK = shell in {"ZMQInteractiveShell", "Shell"}
except Exception:
    IS_NOTEBOOK = False
OFFLINE = False

def set_backend(wx=True):
    if wx:
        matplotlib.use('WXAgg')
    else:
        matplotlib.use('TKAgg')

def set_server(boolean=True):
    isServer = boolean

def set_verbose(boolean=True):
    verbose = boolean
