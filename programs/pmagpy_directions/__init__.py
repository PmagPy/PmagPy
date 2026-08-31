"""
PmagPy Directions — a Panel application for interpreting demagnetization data in
MagIC 3 format.

Modules
-------
theme        colours (components are coloured by *name* across the whole
             study), CSS and Bokeh figure styling
logger       the step "logger": every measurement step in sequence; left
             click sets fit bounds, right click toggles good/bad
plots        Bokeh figure builders for the interactive views
publication  matplotlib figures for publication-quality export
session      the analysis state shared by all views (wraps pmagpy.demag)
views        the panes: Specimen, Means (sample/site/location), Poles,
             Fits, Export
app          assembles the template; ``create_app()`` is the entry point
"""

APP_NAME = "PmagPy Directions"
