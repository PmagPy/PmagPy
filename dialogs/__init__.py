"""GUI dialog package with lazy submodule loading."""

from importlib import import_module


_SUBMODULES = {
    'ErMagicBuilder': 'ErMagicBuilder',
    'demag_dialogs': 'demag_dialogs',
    'demag_interpretation_editor': 'demag_interpretation_editor',
    'grid_frame3': 'grid_frame3',
    'magic_grid3': 'magic_grid3',
    'pmag_gui_dialogs': 'pmag_gui_dialogs',
    'pmag_er_magic_dialogs': 'pmag_er_magic_dialogs',
    'pmag_menu_dialogs': 'pmag_menu_dialogs',
    'pmag_widgets': 'pmag_widgets',
    'thellier_consistency_test': 'thellier_consistency_test',
    'thellier_gui_dialogs': 'thellier_gui_dialogs',
    'thellier_gui_lib': 'thellier_gui_lib',
    'thellier_interpreter': 'thellier_interpreter',
}

__all__ = list(_SUBMODULES)


def __getattr__(name):
    if name not in _SUBMODULES:
        raise AttributeError(f"module 'dialogs' has no attribute {name!r}")
    module = import_module(f'.{_SUBMODULES[name]}', __name__)
    globals()[name] = module
    return module


def __dir__():
    return sorted(list(globals()) + __all__)
