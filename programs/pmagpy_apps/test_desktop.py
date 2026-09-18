"""Tests for the editions, the in-process server and the desktop build's pieces.

    pytest programs/pmagpy_panel programs/pmagpy_apps -q
"""
import os
import threading
import urllib.request

import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import datasets, runtime  # noqa: E402
from pmagpy_panel.serve import FamilyServer, family_site, free_port  # noqa: E402
from pmagpy_apps import EDITIONS, EDITION_VAR, app, current_edition, desktop, home, launch, splash  # noqa: E402
from pmagpy_apps.test_app import page_html  # noqa: E402

MCMURDO = datasets.example_dir("McMurdo")


class TestEditions:
    def test_the_full_edition_is_the_default_and_offers_everything(self, monkeypatch):
        monkeypatch.delenv(EDITION_VAR, raising=False)
        assert current_edition() is EDITIONS["full"]
        monkeypatch.setenv(EDITION_VAR, "no-such-edition")
        assert current_edition() is EDITIONS["full"]
        assert EDITIONS["full"].offers("pmagpy_intensity") and EDITIONS["full"].has_page("upload")

    def test_the_directions_edition_is_convert_and_directions_only(self):
        ed = EDITIONS["directions"]
        assert ed.offers("pmagpy_directions") and not ed.offers("pmagpy_intensity")
        assert ed.doors == ("open_btn", "convert_start_btn", "example_btn")
        assert not ed.has_page("download") and not ed.has_page("metadata") and not ed.has_page("upload")
        assert ed.title == "PmagPy Directions"

    def test_the_start_page_shows_only_the_editions_doors(self, tmp_path):
        tmpl = app.create_app(recent_file=str(tmp_path / "recent.json"), edition=EDITIONS["directions"])
        html = page_html(tmpl)
        assert "Open MagIC data" in html and "Convert measurement files" in html and "Explore an example" in html
        assert "Download from MagIC" not in html
        assert EDITIONS["directions"].tagline in html
        # the full edition keeps all four
        full = page_html(app.create_app(recent_file=str(tmp_path / "recent.json")))
        assert "Download from MagIC" in full and "tagline" not in full

    def test_the_directory_page_lists_only_the_editions_applications_and_tools(self):
        tmpl = app.create_app(MCMURDO, edition=EDITIONS["directions"])
        html = page_html(tmpl)
        assert app.app_link("pmagpy_directions", MCMURDO) in html
        for other in ("Intensity", "Rock magnetism", "FORC", "Anisotropy"):
            assert f"<h3>{other}</h3>" not in html
        assert "Metadata" not in html and "Upload" not in html          # neither the strip nor the buttons
        assert set(tmpl.body.pages) == {"home", "convert"}              # the pages left out are not built
        view = [o for o in tmpl.body.main.objects[0].objects if hasattr(o, "objects")]
        assert view                                                      # Home is there ...
        session = home.HubSession(MCMURDO)
        page = home.HomeView(session, edition=EDITIONS["directions"])
        assert not page.metadata_btn.visible and not page.upload_btn.visible and not page.download_btn.visible
        assert page.convert_btn.visible and page.change_btn.visible
        assert [s[0] for s in home.stages(session.inventory, EDITIONS["directions"])] == ["Import", "Analyze"]
        assert [s[0] for s in home.stages(session.inventory)] == ["Import", "Metadata", "Analyze", "Upload"]

    def test_turning_to_a_page_the_edition_left_out_does_nothing(self):
        tmpl = app.create_app(MCMURDO, edition=EDITIONS["directions"])
        tmpl.body.turn_to("metadata")
        assert tmpl.body.pages["home"].visible
        tmpl.body.turn_to("convert")
        assert tmpl.body.pages["convert"].visible and not tmpl.body.pages["home"].visible

    def test_the_launcher_serves_only_the_editions_applications(self, monkeypatch):
        monkeypatch.setenv(EDITION_VAR, "directions")
        files = launch.application_files()
        assert [os.path.basename(f) for f in files] == ["pmagpy_directions.py"]
        monkeypatch.setenv(EDITION_VAR, "full")
        assert len(launch.application_files()) > 1


class TestServe:
    def test_the_site_has_the_hub_at_the_root_and_every_asset_folder(self):
        panels, static = family_site(["pmagpy_directions", "pmagpy_not_installed"])
        assert set(panels) == {"/", "/pmagpy_apps", "/pmagpy_directions"}
        assert panels["/"] is panels["/pmagpy_apps"] is app.serve_default
        assert set(static) == {"pmagpy_apps_assets", "pmagpy_directions_assets"}
        assert all(os.path.isfile(os.path.join(d, "favicon.png")) for d in static.values())
        panels, _ = family_site(["pmagpy_directions"], hub=False)
        assert set(panels) == {"/pmagpy_directions"}

    def test_free_port_prefers_the_one_asked_for(self):
        port = free_port()
        assert 1024 < port < 65536
        assert free_port(port) == port

    def test_the_server_answers_on_a_thread_and_sets_the_hub_url(self, monkeypatch, tmp_path):
        monkeypatch.setenv(EDITION_VAR, "directions")
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", str(tmp_path / "recent.json"))
        server = FamilyServer(["pmagpy_directions"], port=0).start()
        try:
            assert server.thread.is_alive() and os.environ[runtime.HUB_URL_VAR] == server.url
            assert server.wait_ready(timeout=60)
            with urllib.request.urlopen(server.url, timeout=10) as response:
                body = response.read().decode("utf-8", "replace")
            assert response.status == 200 and "PmagPy Apps" in body
            with urllib.request.urlopen(server.url + "pmagpy_apps_assets/favicon.png", timeout=10) as response:
                assert response.status == 200
        finally:
            server.stop()
            server.thread.join(timeout=10)


class TestSplash:
    def test_the_splash_is_self_contained_and_carries_the_magpie(self):
        html = splash.splash_html("PmagPy Directions", "one line", version="PmagPy 1.0")
        assert "data:image/png;base64," in html and "<script" in html and 'id="status"' in html
        assert "PmagPy Directions" in html and "one line" in html and "PmagPy 1.0" in html
        assert "http://" not in html and "https://" not in html           # nothing to fetch before the server is up
        assert splash.status_js('Loading "PmagPy" …') == 'setStatus("Loading \\"PmagPy\\" \\u2026")'

    def test_the_html_escapes_what_it_is_given(self):
        assert "<b>" not in splash.splash_html("<b>x</b>")


class TestDesktop:
    def test_the_environment_is_prepared_for_the_edition(self, monkeypatch, tmp_path):
        monkeypatch.delenv("PMAGPY_APPS_DIR", raising=False)
        monkeypatch.delenv("PMAGPY_DIRECTIONS_OUTPUT", raising=False)
        desktop.prepare_environment(EDITIONS["directions"], directory=str(tmp_path), output=str(tmp_path / "out"))
        assert os.environ[EDITION_VAR] == "directions"
        assert os.environ["PMAGPY_APPS_DIR"] == str(tmp_path)
        assert os.environ["PMAGPY_DIRECTIONS_OUTPUT"] == str(tmp_path / "out")
        assert desktop.bundle_root() is None                                # not frozen here
        assert "MPLCONFIGDIR" not in os.environ or "PmagPy" not in os.environ["MPLCONFIGDIR"]   # only when frozen

    def test_the_cache_dir_is_per_user_and_created(self, monkeypatch, tmp_path):
        monkeypatch.setattr(desktop.os.path, "expanduser", lambda p: str(tmp_path))
        monkeypatch.setattr(desktop.sys, "platform", "darwin")
        path = desktop.cache_dir("PmagPy Directions", "matplotlib")
        assert path == str(tmp_path / "Library" / "Caches" / "PmagPy Directions" / "matplotlib") and os.path.isdir(path)
        monkeypatch.setattr(desktop.sys, "platform", "linux")
        monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
        assert desktop.cache_dir("PmagPy Directions") == str(tmp_path / ".cache" / "PmagPy Directions")

    def test_the_runtime_takes_the_hosts_folder_dialog(self, monkeypatch):
        asked = []

        def dialog(start, prompt):
            asked.append((start, prompt))
            return "/tmp/chosen/"
        runtime.set_folder_dialog(dialog)
        try:
            monkeypatch.setattr(runtime.sys, "platform", "unknown-os")
            assert runtime.native_chooser_available()                       # the host has one, whatever the platform
            assert runtime.native_choose_directory("/nonexistent", "Pick") == "/tmp/chosen"
            assert asked and asked[0][1] == "Pick"
            import asyncio
            assert asyncio.run(runtime.choose_directory(None, "Again")) == "/tmp/chosen"
            runtime.set_folder_dialog(lambda start, prompt: None)
            assert runtime.native_choose_directory() is None
            runtime.set_folder_dialog(lambda start, prompt: 1 / 0)
            assert runtime.native_choose_directory() is None                # a failing dialog is a cancelled one
        finally:
            runtime.set_folder_dialog(None)
        assert runtime.folder_dialog() is None

    def test_headless_main_serves_and_stops(self, monkeypatch, tmp_path):
        """--no-window: the mode the packaged build is checked in."""
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", str(tmp_path / "recent.json"))
        started = {}
        real_start = desktop.start_server

        def start(edition, port, report=lambda text: None):
            server = real_start(edition, port, report)
            started["server"] = server
            threading.Timer(0.5, lambda: server.stop()).start()          # ends the wait loop
            return server
        monkeypatch.setattr(desktop, "start_server", start)
        assert desktop.main(edition="directions", argv=["--no-window"]) == 0
        assert started["server"].url.startswith("http://localhost:")
        started["server"].thread.join(timeout=10)


class TestDesktopEdition:
    def test_the_desktop_edition_adds_intensity_beside_directions(self):
        ed = EDITIONS["desktop"]
        assert ed.applications == ("pmagpy_directions", "pmagpy_intensity")
        assert ed.doors == EDITIONS["directions"].doors and ed.pages == ()
        assert ed.title == "PmagPy Apps"
        here = os.path.dirname(os.path.abspath(desktop.__file__))
        for key, entry in (("desktop", "desktop_apps.py"), ("directions", "desktop_directions.py")):
            assert os.path.isfile(os.path.join(here, entry)), entry    # the spec starts from these

    def test_the_directory_page_offers_both_applications_on_mcmurdo(self):
        html = page_html(app.create_app(MCMURDO, edition=EDITIONS["desktop"]))
        assert app.app_link("pmagpy_directions", MCMURDO) in html
        assert app.app_link("pmagpy_intensity", MCMURDO) in html      # McMurdo has Thellier experiments
        assert "<h3>Rock magnetism</h3>" not in html

    def test_the_site_serves_both_applications(self):
        panels, static = family_site(list(EDITIONS["desktop"].applications))
        assert set(panels) == {"/", "/pmagpy_apps", "/pmagpy_directions", "/pmagpy_intensity"}
        assert "pmagpy_intensity_assets" in static


class TestBundleTrim:
    """The size rules of the packaged build (pmagpy_apps/bundle.py) keep what the family serves."""

    def test_panel_components_the_family_uses_are_kept(self):
        from pmagpy_apps import bundle
        for dest in ("panel/dist/bundled/datatabulator/tabulator-tables@6.4.0/dist/js/tabulator.min.js",
                     "panel/dist/bundled/@microsoft/fast-components@2.30.6/dist/fast-components.js",
                     "panel/dist/bundled/fastlisttemplate/fast_list_template.css",
                     "panel/dist/bundled/fastbasetemplate/fast_template.js",
                     "panel/dist/bundled/fast/js/fast_design.js",
                     "panel/dist/bundled/theme/fast.css",
                     "panel/dist/bundled/font-awesome/css/all.min.css",
                     "panel/dist/bundled/reactiveesm/es-module-shims@^1.10.0/dist/es-module-shims.min.js",
                     "panel/dist/panel.min.js", "panel/dist/panel.json", "panel/dist/css/loading.css",
                     "bokeh/server/static/js/bokeh.min.js", "bokeh/server/static/js/bokeh-mathjax.min.js",
                     "bokeh/server/static/js/bokeh-gl.min.js",
                     "pmagpy/data_model/data_model.json", "data_files/3_0/McMurdo/measurements.txt"):
            assert bundle.keep_data(dest), dest

    def test_what_the_family_never_serves_is_dropped(self):
        from pmagpy_apps import bundle
        for dest in ("panel/dist/bundled/deckglplot/deck.min.js", "panel/dist/bundled/aceplot/ace.js",
                     "panel/dist/bundled/abstractvtkplot/vtk.js", "panel/dist/bundled/plotlyplot/plotly.min.js",
                     "panel/dist/bundled/bootstrap5/css/bootstrap.min.css",
                     "bokeh/server/static/js/bokeh.js", "bokeh/server/static/js/compiler.js",
                     "bokeh/server/static/js/lib/index.d.ts", "panel/dist/panel.js", "panel/dist/panel.js.map"):
            assert not bundle.keep_data(dest), dest

    def test_the_library_chains_are_dropped_and_pillows_core_kept(self):
        from pmagpy_apps import bundle
        for name in ("libicudata.78.3.dylib", "libicuuc.78.dylib", "libsqlite3.0.dylib", "libtk8.6.dylib",
                     "libtcl8.6.dylib"):
            assert not bundle.keep_binary(name), name
        # linked by matplotlib's ft2font (raqm chain), libtiff (webp) and Pillow (xcb): must stay
        for name in ("libfreetype.6.dylib", "libpng16.16.dylib", "libjpeg.8.dylib", "libtiff.6.dylib",
                     "libLerc.4.dylib", "libopenblas.0.dylib", "libpython3.12.dylib",
                     "libraqm.0.dylib", "libharfbuzz.0.dylib", "libglib-2.0.0.dylib", "libwebp.7.dylib",
                     "libxcb.1.dylib", "libXau.6.dylib",
                     "PIL/_imaging.cpython-312-darwin.so", "numpy/_core/_multiarray_umath.cpython-312-darwin.so"):
            assert bundle.keep_binary(name), name

    def test_the_keep_list_covers_what_panels_own_classes_declare(self):
        """Panel serves a template's _css/_js files from bundled/<class name>/ and Tabulator names
        its stylesheets outright: every folder that resolution reaches must be kept."""
        import re
        from pmagpy_apps import bundle
        named = set()
        for cls in pn.template.FastListTemplate.__mro__:
            if vars(cls).get("_css") or vars(cls).get("_js"):       # a class with files of its own
                named.add(cls.__name__.lower())                     # template/base.py: bundled/{tmpl_name}/{file}
        for item in pn.widgets.Tabulator._stylesheets:
            named.update(re.findall(r"bundled/([^/]+)/", str(item)))
        # what a browser asked for on every tab of both applications (bundle_audit.py, 2026-09-18)
        named.update({"@microsoft", "datatabulator", "fast", "fastbasetemplate", "fastlisttemplate",
                      "font-awesome", "reactiveesm", "theme"})
        assert {"fastlisttemplate", "fastbasetemplate", "font-awesome"} <= named
        assert named <= set(bundle.KEEP_BUNDLED), named - set(bundle.KEEP_BUNDLED)

    def test_the_report_accounts_for_every_dropped_file(self, tmp_path):
        from pmagpy_apps import bundle
        f = tmp_path / "x.js"
        f.write_bytes(b"0" * 2_000_000)
        kept, dropped = bundle.trim([("panel/dist/bundled/deckglplot/deck.js", str(f), "DATA"),
                                     ("panel/dist/bundled/theme/fast.css", str(f), "DATA")], bundle.keep_data)
        assert [e[0] for e in kept] == ["panel/dist/bundled/theme/fast.css"] and len(dropped) == 1
        text = bundle.report(dropped, [])
        assert "1 files, 2.0 MB" in text and "panel/dist/bundled/deckglplot" in text and "bundle.py" in text
