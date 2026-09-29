# programs that require a non-TKAgg backend

prog_env = {'core_depthplot': 'WXAgg',
            'ani_depthplot': 'WXAgg',
            'ani_depthplot2': 'WXAgg',
            # wxPython conversion GUIs; they forced WXAgg themselves before
            # the package init chose the backend
            'tdt_magic': 'WXAgg',
            'livdb_magic': 'WXAgg',
            'demag_gui': 'WXAgg',
            'magic_gui': 'WXAgg',
            'magic_gui2': 'WXAgg',
            'pmag_gui': 'WXAgg',
            'thellier_gui': 'WXAgg',
            'make_magic_plots': 'Agg'}
