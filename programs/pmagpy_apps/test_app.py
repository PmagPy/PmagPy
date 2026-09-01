"""Tests for the PmagPy Apps page and its launcher.

    pytest programs/pmagpy_apps -q
"""
import os
import shutil

import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import datasets  # noqa: E402
from pmagpy_apps import APP, app, home, launch  # noqa: E402
from pmagpy_apps.inventory import take_inventory  # noqa: E402

MCMURDO = datasets.example_dir("McMurdo")
CIT = os.path.join(os.path.dirname(os.path.dirname(MCMURDO)), "convert_2_magic", "cit_magic", "PI47")


def page_html(tmpl) -> str:
    """Every HTML pane on the page, joined."""
    return "".join(p.object for p in tmpl.body.main.select(pn.pane.HTML))


def cit_only(tmp_path) -> str:
    d = tmp_path / "PI47"
    d.mkdir()
    for name in os.listdir(CIT):
        if not name.endswith(".txt"):
            shutil.copy(os.path.join(CIT, name), d)
    return str(d)


class TestPage:
    def test_the_page_names_the_directory_and_opens_directions_on_it(self):
        tmpl = app.create_app(MCMURDO)
        assert tmpl.title == APP.name == "PmagPy Apps"
        assert tmpl.favicon == "/pmagpy_apps_assets/favicon.png"
        html = page_html(tmpl)
        assert "McMurdo" in html and "MagIC contribution 13436" in html
        assert app.app_link("pmagpy_directions", MCMURDO) in html
        assert "contribution.txt" not in html          # never user-visible

    def test_links_carry_the_directory_on_the_query_string(self):
        link = app.app_link("pmagpy_directions", "/data/My Site/magic")
        assert link == "/pmagpy_directions?dir=/data/My%20Site/magic"

    def test_default_falls_back_to_the_shipped_example_as_a_landing(self, monkeypatch, tmp_path):
        monkeypatch.delenv("PMAGPY_APPS_DIR", raising=False)
        recent = str(tmp_path / "recent.json")
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", recent)
        datasets.remember_recent(recent, str(tmp_path))
        html = page_html(app.serve_default())
        assert "McMurdo" in html
        assert "Recent" in html and home.home_link(str(tmp_path)) in html    # the landing lists where to go
        assert datasets.load_recent(recent) == [str(tmp_path)]                # the example is not itself "recent"

    def test_a_directory_asked_for_is_not_a_landing(self, monkeypatch, tmp_path):
        recent = str(tmp_path / "recent.json")
        monkeypatch.setattr(datasets, "SHARED_RECENT_FILE", recent)
        datasets.remember_recent(recent, str(tmp_path))
        monkeypatch.setenv("PMAGPY_APPS_DIR", MCMURDO)
        html = page_html(app.serve_default())
        assert "McMurdo" in html and "Recent" not in html
        assert datasets.load_recent(recent)[0] == MCMURDO

    def test_the_header_status_follows_the_session(self):
        session = home.HubSession(MCMURDO)
        body = app.build_body(session)
        assert "McMurdo loaded · 8 tables" in body.header.object


class TestThreeStates:
    def test_magic_directory(self):
        inv = take_inventory(MCMURDO)
        names = [s[0] for s in home.stages(inv)]
        assert names == ["Import", "Metadata", "Analyze", "Upload"]
        meta = home.stages(inv)[1]
        assert meta[1] == "warn" and meta[2] == "site ages missing (8) · 3 more gaps"   # one gap named, never a list
        assert "1,002 specimens interpreted" in home.stages(inv)[2][2]
        bars = home.bars_html(inv)
        assert 'href="/pmagpy_directions?dir=' in bars                  # Directions is built and has demag steps
        assert "no FORC measurements in this directory" in bars
        assert "Thellier experiments · IZZI, ZI, IZ · not built yet" in bars
        assert 'style="--c:#00A8C8;--c-ink:#ffffff" href="/pmagpy_directions' in bars   # the door is the app's colour
        assert '--c:#FFB627;--c-ink:#1b1b1b' in bars                                    # shut doors keep theirs, faintly
        aside = home.aside_html(inv, [])
        assert "Tables" not in aside and "measurements.txt" not in aside     # the counts line already says it
        assert "Other files" in aside and "extra_specimens.txt" in aside

    def test_a_tidy_magic_directory_has_no_aside_at_all(self, tmp_path):
        for name in ("measurements", "specimens", "sites"):
            shutil.copy(os.path.join(MCMURDO, f"{name}.txt"), tmp_path)
        inv = take_inventory(str(tmp_path))
        assert inv.is_magic and home.aside_html(inv, []) == ""
        session = home.HubSession(str(tmp_path), landing=False)
        view = home.HomeView(session)
        assert view.aside.visible is False and view.spacer.visible is False
        session.load(MCMURDO)
        assert view.aside.visible is True

    def test_lab_files_waiting_to_convert(self, tmp_path):
        inv = take_inventory(cit_only(tmp_path))
        imp, meta, ana, up = home.stages(inv)
        assert imp[3] is True and imp[2] == "10 files to convert · CIT?"   # a guess, offered with a question mark
        assert meta[2] == ana[2] == up[2] == "after import"
        assert "look like CIT specimen files" in home.facts_html(inv)
        assert "no measurements yet" in home.bars_html(inv) and "href" not in home.bars_html(inv)
        assert "CIT index" in home.aside_html(inv, [])

    def test_empty_directory(self, tmp_path):
        inv = take_inventory(str(tmp_path))
        imp = home.stages(inv)[0]
        assert imp[2] == "convert files, or download from MagIC"
        assert "by its ID or DOI" in home.facts_html(inv)
        aside = home.aside_html(inv, [MCMURDO, str(tmp_path)])
        assert "none" in aside
        assert home.home_link(MCMURDO) in aside and str(tmp_path) not in aside.split("Recent")[1].split("<li>")[0]


class TestOpenDirectory:
    def test_opening_a_directory_reloads_the_page_and_remembers_it(self, tmp_path):
        recent = str(tmp_path / "recent.json")
        datasets.remember_recent(recent, str(tmp_path))
        session = home.HubSession(MCMURDO, recent_file=recent, landing=True)
        view = home.HomeView(session)
        dialog = home.open_directory(session)
        assert "Recent" in view.aside.object
        closed = []
        dialog.on_loaded = lambda: closed.append(True)
        target = cit_only(tmp_path)
        dialog.path.value = target
        assert dialog.load() is True                              # no measurements.txt needed here
        assert session.directory == target and closed == [True]
        assert "PI47" in view.heading.object and "10 files to convert" in view.strip.object
        assert "Recent" not in view.aside.object                 # picked: the page is about this directory now
        assert datasets.load_recent(recent) == [target, str(tmp_path)]
        assert list(dialog.recent.options.values())[0] == target   # the dialog keeps the list

    def test_a_path_that_is_not_a_directory_is_refused_in_place(self, tmp_path):
        session = home.HubSession(MCMURDO)
        dialog = home.open_directory(session)
        dialog.path.value = str(tmp_path / "nowhere")
        assert dialog.load() is False
        assert "is not a directory" in dialog.message.object
        assert session.directory == MCMURDO

    def test_any_existing_directory_opens_even_an_empty_one(self, tmp_path):
        session = home.HubSession(MCMURDO)
        assert session.load(str(tmp_path)) is True
        assert session.inventory.is_empty and session.status.endswith("· empty")

    def test_recent_lists_only_directories_that_still_exist(self, tmp_path):
        recent = str(tmp_path / "recent.json")
        gone = tmp_path / "gone"
        gone.mkdir()
        datasets.remember_recent(recent, str(gone))
        gone.rmdir()
        session = home.HubSession(MCMURDO, recent_file=recent, landing=False)
        assert session.recent() == [MCMURDO]


class TestLauncher:
    def test_serves_the_hub_first_and_every_application_beside_it(self):
        files = launch.application_files()
        assert [os.path.basename(f) for f in files] == ["pmagpy_directions.py"]
        assert os.path.basename(launch.HUB) == "pmagpy_apps.py"
        assert launch.DEFAULT_PORT == 5010
        assert all(os.path.exists(f) for f in [launch.HUB, *files])
