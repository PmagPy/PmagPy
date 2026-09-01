"""
PmagPy Directions — a Panel application for interpreting demagnetization data in
MagIC 3 format.

What is specific to demagnetization lives here; what any of these applications
would need — the theme, the drag handles, the equal-area net, choosing a MagIC
directory, the launcher — comes from ``pmagpy_panel``, which the paleointensity
application shares, and the science comes from ``pmagpy.demag``.

Modules
-------
logger       the step "logger": every measurement step in sequence; left
             click sets fit bounds, right click toggles good/bad
plots        Bokeh figure builders for the interactive views
publication  matplotlib figures for publication-quality export
session      the analysis state shared by all views (wraps pmagpy.demag)
views        the panes: Specimen, Means (sample/site/location), Poles,
             Fits, Export
app          assembles the template; ``create_app()`` is the entry point
launch       thin wrapper over ``pmagpy_panel.launch``
"""

APP_NAME = "PmagPy Directions"
