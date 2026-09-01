"""Assemble the PmagPy Apps page.

What is here now is the foundation the hub is built on — the page served at
``/``, on the shared shell, with the applications reachable beside it. The Home
page itself (the dataset as its subject, the workflow strip, the analysis
cards) is designed from a mock first and lands next; see HUB_PLAN.md §2.
"""
from __future__ import annotations

import os
from urllib.parse import quote

import panel as pn

from pmagpy_panel import datasets, shell
from pmagpy_panel.theme import MUTED_STYLE, SECTION_STYLE
from . import APP

shell.setup()

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
LOGO = os.path.join(ASSETS, "pmagpy_logo_white.png")
DEFAULT_EXAMPLE = "McMurdo"


def app_link(app_id: str, directory: str) -> str:
    """The URL that opens an application on a directory, on the server this page came from."""
    return f"/{app_id}?dir={quote(directory)}"


def build_body(directory: str) -> shell.Body:
    """The page's body: the directory it holds and the way into each application."""
    name = os.path.basename(directory.rstrip("/")) or directory
    main = pn.Column(
        pn.pane.HTML(f'<div style="{SECTION_STYLE}">MagIC directory</div>'
                     f'<h2 style="margin:4px 0 2px 0">{name}</h2>'
                     f'<div style="{MUTED_STYLE}">{directory}</div>'),
        pn.pane.HTML(f'<div style="{SECTION_STYLE};margin-top:24px">Analyze</div>'
                     f'<p><a href="{app_link("pmagpy_directions", directory)}">PmagPy Directions &rarr;</a></p>'),
        sizing_mode="stretch_width", max_width=900, margin=(20, 40),
    )
    return shell.Body(info=APP, main=main)


def create_app(directory: str):
    """Build the page for a MagIC directory. Returns a servable Panel template."""
    return shell.template(build_body(directory), logo=LOGO)


def serve_default():
    """The page for the directory this session asked for: ``?dir=``, then ``PMAGPY_APPS_DIR``, then the example."""
    return create_app(datasets.session_directory(APP.env_prefixes, datasets.example_dir(DEFAULT_EXAMPLE)))
