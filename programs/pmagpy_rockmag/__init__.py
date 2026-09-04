"""
PmagPy Rock Magnetism — a Panel application for rock-magnetic experiments in
MagIC 3 format: one view per experiment type, each a figure from the
corresponding ``pmagpy.rockmag`` plotting function with the controls its
``*_interactive`` notebook widget exposes, now as Panel widgets driving the
same pure function.

What is specific to rock magnetism lives here; what any of the applications
would need — the theme, choosing a MagIC directory, the launcher, "show code"
— comes from ``pmagpy_panel``, and the science comes from ``pmagpy.rockmag``
(and later ``pmagpy.forc``).

Modules
-------
session      the loaded measurements and the experiment index every view shares
views        the dataset block, the experiment index and one view per
             experiment type (MPMS DC first)
app          assembles the template; ``create_app()`` is the entry point
launch       thin wrapper over ``pmagpy_panel.launch``

Every view also renders in a notebook: ``MpmsDcView(measurements).panel()``
under ``pn.extension()`` is the cell that replaces the ipywidgets
``plot_mpms_dc_interactive``.
"""

APP_NAME = "PmagPy Rock Magnetism"
