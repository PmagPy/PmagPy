"""
PmagPy Anisotropy — a Panel application for the anisotropy of magnetic
susceptibility and remanence (AMS, AARM, ATRM) in MagIC 3 format: the
eigenvectors of a group of specimens on equal-area nets with the Hext and
bootstrap statistics of their mean tensor, the shape of the fabric on Jelinek
and Flinn plots, and the tensor table itself, in specimen, geographic or
tilt-corrected coordinates.

What is specific to anisotropy lives here; what any of the applications would
need — the theme, choosing a MagIC directory, the launcher, "show code" —
comes from ``pmagpy_panel``, and the science comes from ``pmagpy.anisotropy``
over the tensor functions of ``pmagpy.pmag`` (``sbar``, ``dohext``,
``s_boot``, ``sbootpars``).

Modules
-------
session      the specimens/samples tables and the selection every view shares
             (group, coordinate frame, anisotropy type)
views        the dataset block, the selection pickers, the inventory, and the
             Eigenvectors / Shape / Specimens views
plots        the Bokeh figures
app          assembles the template; ``create_app()`` is the entry point
launch       thin wrapper over ``pmagpy_panel.launch``

Every view also renders in a notebook: ``EigenvectorsView(specimens).panel()``
under ``pn.extension()``.
"""

APP_NAME = "PmagPy Anisotropy"
