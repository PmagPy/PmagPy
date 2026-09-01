"""Tests for the PmagPy Apps page and its launcher.

    pytest programs/pmagpy_apps -q
"""
import os

import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import datasets  # noqa: E402
from pmagpy_apps import APP, app, launch  # noqa: E402

MCMURDO = datasets.example_dir("McMurdo")


class TestPage:
    def test_the_page_names_the_directory_and_opens_directions_on_it(self):
        tmpl = app.create_app(MCMURDO)
        assert tmpl.title == APP.name == "PmagPy Apps"
        assert tmpl.favicon == "/pmagpy_apps_assets/favicon.png"
        html = "".join(pane.object for pane in tmpl.body.main)
        assert "McMurdo" in html
        assert app.app_link("pmagpy_directions", MCMURDO) in html

    def test_links_carry_the_directory_on_the_query_string(self):
        link = app.app_link("pmagpy_directions", "/data/My Site/magic")
        assert link == "/pmagpy_directions?dir=/data/My%20Site/magic"

    def test_default_falls_back_to_the_shipped_example(self, monkeypatch):
        monkeypatch.delenv("PMAGPY_APPS_DIR", raising=False)
        assert app.serve_default().body.main[0].object.count("McMurdo") >= 1


class TestLauncher:
    def test_serves_the_hub_first_and_every_application_beside_it(self):
        files = launch.application_files()
        assert [os.path.basename(f) for f in files] == ["pmagpy_directions.py"]
        assert os.path.basename(launch.HUB) == "pmagpy_apps.py"
        assert launch.DEFAULT_PORT == 5010
        assert all(os.path.exists(f) for f in [launch.HUB, *files])
