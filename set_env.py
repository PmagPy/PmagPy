import matplotlib
isServer = False
verbose = True

def set_backend(wx=True):
    if wx:
        matplotlib.use('WXAgg')
    else:
        matplotlib.use('TKAgg')

def set_server(boolean=True):
    isServer = boolean

def set_verbose(boolean=True):
    verbose = boolean
