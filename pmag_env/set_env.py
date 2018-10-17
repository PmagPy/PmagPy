import matplotlib
import sys
isServer = False
verbose = True
IS_WIN = True if sys.platform in ['win32', 'win64'] else False
IS_FROZEN = getattr(sys, 'frozen', False)

def set_backend(wx=True):
    if wx:
        matplotlib.use('WXAgg')
    else:
        matplotlib.use('TKAgg')

def set_server(boolean=True):
    isServer = boolean

def set_verbose(boolean=True):
    verbose = boolean
