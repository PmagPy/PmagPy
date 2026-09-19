import importlib
import matplotlib
import sys
import os
isServer = False
verbose = True
IS_WIN = True if sys.platform in ['win32', 'win64'] else False
IS_LINUX = True if 'linux' in sys.platform else False
IS_FROZEN = getattr(sys, 'frozen', False)
try:
    if IS_FROZEN:
        raise RuntimeError
    get_ipython = importlib.import_module('IPython').get_ipython
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


def backend_already_chosen():
    """Report whether a matplotlib backend has already been selected.

    matplotlib starts with an "auto" placeholder in place of a backend name
    and only replaces it when something asks for one: an explicit
    ``matplotlib.use()`` call, the ``MPLBACKEND`` environment variable
    (which Jupyter kernels set to the inline backend), or the first import of
    pyplot. Until then nothing has expressed a preference and a command-line
    program is free to pick the GUI backend it wants.

    Returns:
        bool: True if a backend has been set or resolved, False if matplotlib
        is still waiting to auto-select one.
    """
    get_backend_or_none = getattr(matplotlib.rcParams, "_get_backend_or_none", None)
    if get_backend_or_none is not None:
        return get_backend_or_none() is not None
    # older matplotlib without the helper: compare against the sentinel directly
    from matplotlib import rcsetup
    current = dict.__getitem__(matplotlib.rcParams, "backend")
    return current is not rcsetup._auto_backend_sentinel


def set_backend_if_unset(preferred="TKAgg"):
    """Select a GUI backend for a command-line program without clobbering
    a backend that has already been chosen.

    The modules under ``programs/`` need an interactive backend when run from
    the command line so that figures open in windows. When those same modules
    are imported into a notebook the backend must be left alone, otherwise the
    inline backend is replaced and figures stop appearing (issue #909). The
    same applies when a script, test suite, or the ``MPLBACKEND`` environment
    variable has already picked a backend.

    Args:
        preferred (str): backend to request when none has been chosen yet,
            e.g. "TKAgg" or "WXAgg".

    Returns:
        bool: True if the backend was changed to ``preferred``, False if an
        existing choice (or the notebook) was respected.
    """
    if IS_NOTEBOOK:
        return False
    if backend_already_chosen():
        return False
    matplotlib.use(preferred)
    return True

def set_server(boolean=True):
    isServer = boolean

def set_verbose(boolean=True):
    verbose = boolean
