"""Tests for the PmagPy Apps page and its launcher.

    pytest programs/pmagpy_apps -q
"""
import asyncio
import os
import shutil

import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import datasets  # noqa: E402
from pmagpy_apps import APP, app, convert, download, home, launch  # noqa: E402
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
        # Intensity is built too now, so its door opens rather than saying "not built yet"
        assert 'href="/pmagpy_intensity?dir=' in bars
        assert "Thellier experiments · IZZI, ZI, IZ" in bars
        assert 'style="--c:#00A8C8;--c-ink:#ffffff" href="/pmagpy_directions' in bars   # the door is the app's colour
        assert 'style="--c:#F4633A;--c-ink:#ffffff" href="/pmagpy_intensity' in bars
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


class TestDownloadFromMagic:
    """The dialog with the network stubbed: the file it 'fetches' is the test's own small contribution."""

    def _dialog(self, session, versions=1):
        from pmagpy.test.test_magic_project import AS_SERVED
        from pmagpy import magic_project as mp
        fetched = []

        def fetch(magic_id):
            fetched.append(magic_id)
            return AS_SERVED.replace("20549", str(magic_id))
        found = [mp.ContributionRef(id=20614 - i, version=versions - i, doi="10.1130/B36634.1") for i in range(versions)]
        dialog = download.DownloadDialog(session, fetch=fetch, find=lambda doi: found if doi == "10.1130/B36634.1" else [])
        dialog.fetched = fetched
        return dialog

    def test_an_empty_directory_is_the_destination_and_home_opens_the_result(self, tmp_path):
        recent = str(tmp_path / "recent.json")
        empty = tmp_path / "new_study"
        empty.mkdir()
        session = home.HubSession(str(empty), recent_file=recent, landing=False)
        view = home.HomeView(session)
        assert view.download_btn.button_type == "primary" and view.change_btn.button_type == "default"
        dialog = self._dialog(session)
        assert dialog.folder.value == str(empty)                          # prefilled with the empty directory
        closed = []
        dialog.on_loaded = lambda: closed.append(True)
        dialog.reference.value = "20549"
        assert asyncio.run(dialog._download()) is True
        assert dialog.fetched == [20549] and closed == [True]
        assert session.directory == str(empty) and session.inventory.is_magic
        assert "MagIC contribution 20549" in view.heading.object and "4 tables" in dialog.message.object
        assert datasets.load_recent(recent) == [str(empty)]
        assert view.download_btn.button_type == "default" and view.change_btn.button_type == "primary"

    def test_a_doi_finds_the_latest_version_and_says_so(self, tmp_path):
        session = home.HubSession(str(tmp_path), landing=False)
        dialog = self._dialog(session, versions=2)
        dialog.reference.value = "https://doi.org/10.1130/B36634.1"
        assert asyncio.run(dialog._download()) is True
        assert dialog.fetched == [20614]
        assert "MagIC contribution 20614" in dialog.message.object
        dialog.reference.value = "10.1130/nothing.here"
        assert asyncio.run(dialog._download()) is False
        assert "no public contribution with reference DOI 10.1130/nothing.here" in dialog.message.object

    def test_it_never_writes_over_a_magic_directory_but_offers_one_beside_it(self, tmp_path):
        session = home.HubSession(MCMURDO, landing=True)
        dialog = self._dialog(session)
        dialog.reference.value = "20549"
        assert asyncio.run(dialog._download()) is False
        assert dialog.fetched == []                                       # refused before any network
        assert "already holds MagIC tables" in dialog.message.object
        assert dialog.folder.value == os.path.join(os.path.dirname(MCMURDO), "MagIC_20549")
        dialog.folder.value = str(tmp_path / "somewhere" / "MagIC_20549")       # a folder that does not exist yet
        assert asyncio.run(dialog._download()) is True
        assert session.directory == str(tmp_path / "somewhere" / "MagIC_20549") and session.landing is False

    def test_nonsense_is_refused_in_place(self, tmp_path):
        session = home.HubSession(str(tmp_path), landing=False)
        dialog = self._dialog(session)
        dialog.reference.value = "McMurdo"
        assert asyncio.run(dialog._download()) is False
        assert "is not a MagIC contribution ID or a DOI" in dialog.message.object
        assert dialog.download_btn.disabled is False

    def test_the_page_carries_both_dialogs_and_shows_one_at_a_time(self):
        session = home.HubSession(MCMURDO)
        body = app.build_body(session)
        chooser, downloader = body.modal
        assert "Download from MagIC" in downloader[0].object
        shown = []
        body.open_modal = lambda: shown.append(True)
        heading_row = body.pages["home"][0]
        for btn, visible in ((heading_row[2], (False, True)), (heading_row[3], (True, False))):
            btn.clicks += 1
            assert (chooser.visible, downloader.visible) == visible
        assert shown == [True, True]


class TestConvert:
    """The Convert page on real example files: the page guesses, the analyst confirms, the tables land."""

    def test_home_offers_convert_as_the_next_step_for_lab_files(self, tmp_path):
        session = home.HubSession(cit_only(tmp_path), landing=False)
        view = home.HomeView(session)
        assert view.convert_btn.button_type == "primary" and view.convert_btn.visible is True
        assert view.download_btn.button_type == view.change_btn.button_type == "default"
        assert "Convert them with the button above" in view.facts.object
        session.load(MCMURDO)
        assert view.convert_btn.button_type == "default" and view.change_btn.button_type == "primary"
        empty = tmp_path / "empty"
        empty.mkdir()
        session.load(str(empty))
        assert view.convert_btn.visible is False                    # nothing to convert yet

    def test_the_page_turns_between_home_and_convert(self, tmp_path):
        session = home.HubSession(cit_only(tmp_path), landing=False)
        body = app.build_body(session)
        home_page, convert_page = body.pages["home"], body.pages["convert"]
        assert home_page.visible is True and convert_page.visible is False
        home_page[0][1].clicks += 1                                  # "Convert files…"
        assert home_page.visible is False and convert_page.visible is True
        convert_page[0][1].clicks += 1                              # "← Home"
        assert home_page.visible is True and convert_page.visible is False

    def test_cit_files_are_guessed_chosen_and_converted(self, tmp_path):
        d = cit_only(tmp_path)
        session = home.HubSession(d, landing=False)
        view = convert.ConvertView(session)
        assert view.format.value == "cit" and view.fmt.label == "CIT"
        assert view.files.value == ["PI47-.sam"]                     # the .sam index is the file the converter takes
        assert "sitename" in view.form.widgets and "lat" not in view.form.widgets    # CIT reads lat/lon from the .sam
        assert view.append.visible is False
        view.form.widgets["location"].value = "Kolob"
        assert asyncio.run(view._convert()) is True
        assert session.inventory.is_magic and session.inventory.counts["specimens"] == 9
        assert "converted" in view.message.object and "measurements" in view.message.object
        assert view.home_btn.button_type == "primary"
        assert view.log.visible is True and "PI47-.sam" in view.log.object
        sites = open(os.path.join(d, "sites.txt")).read()
        assert "Kolob" in sites

    def test_jr6_files_convert_together_and_a_bad_one_is_named(self, tmp_path):
        src = os.path.join(os.path.dirname(CIT), "..", "jr6_magic")
        d = tmp_path / "jr6"
        d.mkdir()
        for name in ("AF.jr6", "TRM.jr6", "SML07.JR6"):
            shutil.copy(os.path.join(src, name), d)
        (d / "junk.jr6").write_text("not a JR6 file\n")
        session = home.HubSession(str(d), landing=False)
        view = convert.ConvertView(session)
        assert view.format.value == "jr6_jr6"
        assert sorted(view.files.value) == ["AF.jr6", "SML07.JR6", "TRM.jr6", "junk.jr6"]
        assert asyncio.run(view._convert()) is True
        assert "3 of 4 files converted" in view.message.object and "junk.jr6" in view.message.object
        assert session.inventory.is_magic and session.inventory.has("demag")

    def test_nothing_chosen_and_a_required_blank_are_refused_in_place(self, tmp_path):
        session = home.HubSession(cit_only(tmp_path), landing=False)
        view = convert.ConvertView(session)
        view.files.value = []
        assert asyncio.run(view._convert()) is False
        assert "Choose the files" in view.message.object
        view.format.value = "generic"
        assert view.files.options == [f.name for f in session.inventory.files]    # generic takes any file
        view.files.value = ["PI47-1a"]
        assert asyncio.run(view._convert()) is False
        assert "Fill in Experiment" in view.message.object                          # generic insists on the experiment
        assert not session.inventory.is_magic

    def test_a_directory_format_needs_no_file_list(self, tmp_path):
        session = home.HubSession(str(tmp_path), landing=False)
        view = convert.ConvertView(session)
        view.format.value = "tdt"
        assert view.files.disabled is True and "reads every file in the directory" in view.notes.object
        view.format.value = "sio"
        assert view.files.disabled is False

    def test_a_contribution_file_unpacks_on_the_same_page(self, tmp_path):
        from pmagpy.test.test_magic_project import AS_SERVED
        (tmp_path / "magic_contribution_20549.txt").write_text(AS_SERVED)
        session = home.HubSession(str(tmp_path), landing=False)
        view = convert.ConvertView(session)
        assert view.format.value == convert.MAGIC_FILE and view.files.value == ["magic_contribution_20549.txt"]
        assert len(view.form.widgets) == 0
        assert asyncio.run(view._convert()) is True
        assert session.inventory.is_magic and "unpacked" in view.message.object

    def test_appending_to_a_magic_directory_is_offered_and_keeps_what_is_there(self, tmp_path):
        d = cit_only(tmp_path)
        session = home.HubSession(d, landing=False)
        view = convert.ConvertView(session)
        assert asyncio.run(view._convert()) is True
        before = session.inventory.counts["measurements"]
        view.refresh()
        assert view.append.visible is True and view.append.value is True
        shutil.copy(os.path.join(os.path.dirname(CIT), "..", "jr6_magic", "AF.jr6"), d)
        session.load(d)
        view.format.value = "jr6_jr6"
        assert view.files.value == ["AF.jr6"]
        assert asyncio.run(view._convert()) is True
        assert session.inventory.counts["measurements"] > before


class TestLauncher:
    def test_serves_the_hub_first_and_every_application_beside_it(self):
        files = launch.application_files()
        # one per importable application on Home's Analyze list, in that order
        assert [os.path.basename(f) for f in files] == ["pmagpy_directions.py",
                                                        "pmagpy_intensity.py"]
        assert os.path.basename(launch.HUB) == "pmagpy_apps.py"
        assert launch.DEFAULT_PORT == 5010
        assert all(os.path.exists(f) for f in [launch.HUB, *files])
