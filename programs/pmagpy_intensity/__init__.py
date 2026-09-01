"""
PmagPy Intensity — a Panel application for Thellier-type paleointensity
analysis of MagIC 3 data.

What is specific to paleointensity lives here; what any of these applications
would need — the theme, the drag handles, the equal-area net, choosing a MagIC
directory, the launcher — comes from ``pmagpy_panel``, which PmagPy Directions
shares, and the science comes from ``pmagpy.paleointensity``,
``pmagpy.pint_stats`` and ``pmagpy.bicep``.

Modules
-------
plots        Bokeh figure builders: Arai, Zijderveld, equal-area, decay, checks
publication  matplotlib figures for publication-quality export
session      the analysis state shared by all views (wraps pmagpy.paleointensity)
views        the panes: Specimen, Interpretations, Criteria & statistics,
             Corrections, Group results, BiCEP, Export
app          assembles the template; ``create_app()`` is the entry point
launch       thin wrapper over ``pmagpy_panel.launch``
"""

APP_NAME = "PmagPy Intensity"
