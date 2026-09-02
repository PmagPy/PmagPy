"""Tests for the PmagPy Apps page and its launcher.

    pytest programs/pmagpy_apps -q
"""
import asyncio
import os
import shutil

import pytest

pn = pytest.importorskip("panel")

from pmagpy_panel import datasets  # noqa: E402
from pmagpy_apps import APP, app, convert, download, home, launch, metadata  # noqa: E402
from pmagpy_apps.inventory import take_inventory  # noqa: E402

MCMURDO = datasets.example_dir("McMurdo")
CIT = os.path.join(os.path.dirname(os.path.dirname(MCMURDO)), "convert_2_magic", "cit_magic", "PI47")


def page_html(tmpl) -> str:
    """Every HTML pane on the page, joined."""
    return "".join(p.object for p in tmpl.body.main.select(pn.pane.HTML))


def small_study(tmp_path) -> str:
    """A MagIC directory with the gaps the Metadata page exists to fill."""
    import pandas as pd
    from pmagpy import magic_project as mp
    d = tmp_path / "study"
    d.mkdir()

    def write(table, rows):
        mp.magic_write(str(d / f"{table}.txt"), pd.DataFrame(rows).fillna(""), table)
    write("locations", [{"location": "Zavkhan", "location_type": "Outcrop"}])
    write("sites", [{"site": "Z11", "location": "Zavkhan", "lat": "47.05", "lon": "96.2", "lithologies": "Basalt"},
                    {"site": "Z12", "location": "Zavkhan", "lat": "95", "lon": "96.3"}])       # 95: off the planet
    write("samples", [{"sample": "Z11.1", "site": "Z11", "azimuth": "10", "dip": "20"},
                      {"sample": "Z13.1", "site": "Z13"}])                                    # Z13 has no sites row
    write("specimens", [{"specimen": "Z11.1a", "sample": "Z11.1"}])
    write("measurements", [{"measurement": "1", "experiment": "e1", "specimen": "Z11.1a", "quality": "g"}])
    return str(d)


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
        assert view.download_btn.button_type == "default"
        assert view.metadata_btn.button_type == "primary"           # the contribution has gaps: the next step is Metadata

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
        for btn, visible in ((heading_row[3], (False, True)), (heading_row[4], (True, False))):     # Download…, Change directory…
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
        assert view.convert_btn.button_type == "default"
        assert view.metadata_btn.button_type == "primary" and view.metadata_btn.visible is True    # McMurdo has undated sites
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


class TestMetadata:
    """The Metadata page: the tables in a grid, gaps filled, the validator's findings on the cells."""

    def test_the_page_turns_between_home_and_metadata(self, tmp_path):
        session = home.HubSession(small_study(tmp_path), landing=False)
        body = app.build_body(session)
        home_page, meta_page = body.pages["home"], body.pages["metadata"]
        assert home_page[0][2].name == "Metadata…" and home_page[0][2].button_type == "primary"   # gaps to fill
        home_page[0][2].clicks += 1
        assert home_page.visible is False and meta_page.visible is True
        meta_page[0][1].clicks += 1                                  # "← Home"
        assert home_page.visible is True and meta_page.visible is False

    def test_the_grid_shows_the_table_with_its_owed_rows_and_required_columns(self, tmp_path):
        session = home.HubSession(small_study(tmp_path), landing=False)
        view = metadata.MetadataView(session)
        assert view.table == "sites" and view.tables.value == "sites"
        labels = list(view.tables.options)
        assert "Sites (2)" in labels and "Samples (2)" in labels and "Ages" in labels    # no ages.txt: no count
        df = view.grid.value
        assert list(df.site) == ["Z11", "Z12", "Z13"] and view.frame.stubs == ["Z13"]
        assert list(df.columns[:2]) == ["site", "location"]
        assert "geologic_classes" in df.columns                     # required, so shown though absent from the file
        assert view.grid.titles["site"] == "site *" and "lat" in view.grid.editors
        assert view.grid.editors["lithologies"]["multiselect"] is True     # a list column picks several
        assert "1 added from samples" in view.note.object and "required and empty" in view.note.object
        assert "Site Name" in view.help.object
        view.tables.value = "specimens"
        assert view.table == "specimens" and list(view.grid.value.specimen) == ["Z11.1a"]
        assert view.parent_fill.visible is True and view.bounds_btn.visible is False

    def test_editing_and_saving_closes_a_gap_the_home_page_showed(self, tmp_path):
        d = small_study(tmp_path)
        session = home.HubSession(d, landing=False)
        view = metadata.MetadataView(session)
        assert any(g.label == "site lithologies" for g in session.inventory.gaps)
        df = view.current()
        df.loc[df.site == "Z12", "lithologies"] = "Basalt:Diabase"
        df.loc[df.site == "Z13", ["location", "lithologies", "lat", "lon"]] = ["Zavkhan", "Basalt", "47.2", "96.4"]
        view.grid.value = df
        view.dirty = True
        assert view.save() is True
        assert not any(g.label == "site lithologies" for g in session.inventory.gaps)
        assert session.inventory.counts["sites"] == 3               # Z13 is a site now
        assert view.frame.stubs == [] and view.dirty is False
        assert "sites.txt written" in view.message.object and metadata.mm.BACKUP_DIR in view.message.object
        assert os.path.exists(os.path.join(d, metadata.mm.BACKUP_DIR, "sites.txt"))
        assert view.home_btn.button_type == "primary"
        assert "geologic_classes" not in open(os.path.join(d, "sites.txt")).readline()   # the empty column is not written

    def test_check_names_the_bad_cell_and_the_missing_columns(self, tmp_path):
        session = home.HubSession(small_study(tmp_path), landing=False)
        view = metadata.MetadataView(session)
        findings = view.check()
        assert any(f.row == "Z12" and f.column == "lat" for f in findings)
        assert any(f.column == "geologic_classes" and not f.row for f in findings)
        assert "objects to" in view.message.object and "required column" in view.findings_pane.object
        styled = view.grid.style._compute().ctx
        assert styled                                                # the stub row and the bad cell are painted
        assert any(metadata.CELL_FAIL.split(":")[1] in str(v) for v in styled.values())

    def test_a_row_and_columns_can_be_added_and_defaults_filled(self, tmp_path):
        session = home.HubSession(small_study(tmp_path), landing=False)
        view = metadata.MetadataView(session)
        view.add_row()
        assert len(view.grid.value) == 4 and view.grid.value.iloc[-1]["site"] == ""
        assert view.grid.value.iloc[-1]["citations"] == "This study"      # Pmag GUI's default for a new row
        view.add_cols.value = ["height", "description"]
        view.add_columns()
        cols = list(view.grid.value.columns)
        assert "height" in cols and "description" in cols
        assert cols.index("height") < cols.index("description")         # data-model order
        assert "height" not in view.add_cols.options.values()
        view.fill_defaults()
        assert (view.grid.value["citations"] == "This study").all()
        assert view.dirty is True

    def test_copy_down_and_bounds_take_what_the_other_tables_know(self, tmp_path):
        d = small_study(tmp_path)
        session = home.HubSession(d, landing=False)
        view = metadata.MetadataView(session)
        view.show("samples")
        assert set(view.parent_fill.options) >= {"lat", "lon", "lithologies"}
        view.parent_fill.value = ["lat", "lon"]
        view.copy_down()
        by = view.grid.value.set_index("sample")
        assert by.loc["Z11.1", "lat"] == "47.05" and by.loc["Z13.1", "lat"] == ""    # Z13 has no site row to copy from
        assert "2 cells copied" in view.message.object
        view.show("locations")
        assert view.bounds_btn.visible is True
        view.fill_bounds()
        row = view.grid.value.iloc[0]
        assert (row["lat_s"], row["lat_n"], row["lon_w"], row["lon_e"]) == ("47.05", "95", "96.2", "96.3")
        assert view.save() is True
        assert not any(g.label == "location bounds" for g in session.inventory.gaps)

    def test_delete_needs_a_selection_and_removes_the_ticked_rows(self, tmp_path):
        session = home.HubSession(small_study(tmp_path), landing=False)
        view = metadata.MetadataView(session)
        view.delete_selected()
        assert "Tick the rows" in view.message.object and len(view.grid.value) == 3
        view.grid.selection = [2]
        view.delete_selected()
        assert list(view.grid.value.site) == ["Z11", "Z12"] and view.dirty is True


class TestLauncher:
    def test_serves_the_hub_first_and_every_application_beside_it(self):
        files = launch.application_files()
        assert [os.path.basename(f) for f in files] == ["pmagpy_directions.py"]
        assert os.path.basename(launch.HUB) == "pmagpy_apps.py"
        assert launch.DEFAULT_PORT == 5010
        assert all(os.path.exists(f) for f in [launch.HUB, *files])
