import matplotlib
isServer = False

def set_backend(wx=True):
    if wx:
        matplotlib.use('WXAgg')
    else:
        matplotlib.use('TKAgg')

def set_server():
    isServer = True
