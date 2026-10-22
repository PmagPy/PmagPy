"""
One copy of a study that every application works on.

When the output is kept out of a study (the desktop build, or an output base
set with PMAGPY_APPS_OUTPUT), the first application to open it copies its
tables to <base>/<dataset>-<fingerprint>/, and Directions, Intensity, Rock
Magnetism, Anisotropy and the hub all read and write that folder -- so they
see one set of tables, and the study itself is never written to.
"""
import hashlib
import os
import shutil

import pytest

from pmagpy_panel import datasets

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MCMURDO = os.path.join(REPO, "data_files", "3_0", "McMurdo")


def digest(directory):
    return {n: hashlib.md5(open(os.path.join(directory, n), "rb").read()).hexdigest()
            for n in sorted(os.listdir(directory)) if os.path.isfile(os.path.join(directory, n))}


@pytest.fixture
def study(tmp_path):
    src = tmp_path / "studies" / "McMurdo"
    src.mkdir(parents=True)
    for name in os.listdir(MCMURDO):
        if name.endswith(".txt"):
            shutil.copy(os.path.join(MCMURDO, name), src)
    return str(src)


@pytest.fixture
def base(tmp_path, monkeypatch):
    for var in datasets.OUTPUT_BASE_VARS:
        monkeypatch.setenv(var, "placeholder")
        monkeypatch.delenv(var)
    out = str(tmp_path / "PmagPy")
    monkeypatch.setenv("PMAGPY_APPS_OUTPUT", out)
    monkeypatch.setenv("PMAGPY_DIRECTIONS_RECENT", str(tmp_path / "recent.json"))
    monkeypatch.setenv("PMAGPY_INTENSITY_RECENT", str(tmp_path / "recent.json"))
    return out


class TestTheWorkingCopy:
    def test_without_a_base_the_study_itself(self, study, monkeypatch):
        for var in datasets.OUTPUT_BASE_VARS:
            monkeypatch.setenv(var, "placeholder")
            monkeypatch.delenv(var)
        assert datasets.working_directory(study) == study

    def test_made_once_and_the_study_left_alone(self, study, base):
        before = digest(study)
        copy = datasets.working_directory(study)
        assert os.path.dirname(copy) == base and os.path.basename(copy).startswith("McMurdo-")
        assert {n for n in os.listdir(copy) if n.endswith(".txt")} == {n for n in before}
        assert datasets.working_copy_source(copy) == os.path.realpath(study)
        assert datasets.working_directory(study) == copy                  # the same copy every time
        assert datasets.working_directory(copy) == copy                   # a copy is not copied again
        assert digest(study) == before

    def test_the_copy_is_an_ordinary_folder(self, study, base):
        umask = os.umask(0o022)
        try:
            copy = datasets.working_directory(study)
        finally:
            os.umask(umask)
        assert os.stat(copy).st_mode & 0o777 == 0o755

    def test_files_the_study_gains_are_added_and_edits_in_the_copy_kept(self, study, base):
        copy = datasets.working_directory(study)
        with open(os.path.join(copy, "sites.txt"), "a") as fh:
            fh.write("\n")
        edited = digest(copy)["sites.txt"]
        shutil.copy(os.path.join(study, "sites.txt"), os.path.join(study, "ages_extra.txt"))
        datasets.working_directory(study)
        assert os.path.exists(os.path.join(copy, "ages_extra.txt"))
        assert digest(copy)["sites.txt"] == edited

    def test_a_study_with_a_very_long_folder_name_gets_its_copy(self, tmp_path, base):
        """<name>-<fingerprint> was longer than the 255 bytes a folder name may have."""
        src = tmp_path / ("é" * 130)                        # 260 bytes in UTF-8
        src.mkdir()
        shutil.copy(os.path.join(MCMURDO, "measurements.txt"), src)
        copy = datasets.working_directory(str(src))
        assert os.path.isfile(os.path.join(copy, "measurements.txt"))
        assert len(os.path.basename(copy).encode("utf-8")) <= 255
        assert datasets.working_directory(str(src)) == copy


    def test_a_read_only_study_gives_a_copy_the_applications_can_write(self, study, base):
        import stat
        for name in os.listdir(study):
            os.chmod(os.path.join(study, name), 0o444)
        before = digest(study)
        copy = datasets.working_directory(study)
        for name in before:
            assert os.stat(os.path.join(copy, name)).st_mode & stat.S_IWUSR, name
            assert not os.stat(os.path.join(study, name)).st_mode & stat.S_IWUSR       # the study is left as it was
        assert digest(study) == before


class TestEveryApplicationWorksThere:
    def test_directions_intensity_rockmag_and_the_hub_open_one_folder(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_rockmag.session import Session as RockMag
        from pmagpy_apps.home import HubSession
        before = digest(study)
        d = Directions(study)
        copy = d.directory
        assert copy != study and d.source_directory == os.path.realpath(study)
        assert d.status.startswith("1034 specimens from McMurdo;") and copy not in d.status
        assert Intensity(study).directory == copy
        assert RockMag(study).directory == copy
        assert HubSession(study, recent_file=str(tmp_path / "hub_recent.json")).directory == copy
        # one set of tables: Directions' export is what Intensity reads, and the study is untouched
        d.export_tables()
        pint = Intensity(study)
        assert pint.directory == copy
        spec = open(os.path.join(copy, "specimens.txt")).read()
        assert "pmagpy_directions" in spec
        assert digest(study) == before

    def test_every_page_names_the_study_not_its_fingerprinted_copy(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_apps.home import HubSession, ref_html
        from pmagpy_apps.inventory import take_inventory
        from pmagpy_panel.chooser import DirectoryChooser
        d = Directions(study)
        copy = d.directory
        assert os.path.basename(copy) != "McMurdo" and datasets.study_name(copy) == "McMurdo"
        pint = Intensity(study)
        assert pint.status.startswith("396 specimens from McMurdo;") and copy not in pint.status
        # the side column's block: the study's name, then the copy said once, with the whole story on hover
        chooser = DirectoryChooser(d, recent_file=str(tmp_path / "chooser_recent.json"), count=lambda s: "")
        block = chooser.summary.object
        assert "<b>McMurdo</b>" in block and "working copy · " in block
        assert f"{os.path.realpath(study)} is never written" in block
        assert chooser.path.value == os.path.realpath(study)   # "open another" starts from the study
        # the hub: the study's name heads every page, its path first, the copy under it
        inv = take_inventory(copy)
        assert inv.name == "McMurdo"
        assert HubSession(study, recent_file=str(tmp_path / "hub_recent.json")).status.startswith("McMurdo loaded")
        ref = ref_html(inv)
        assert ref.index(os.path.basename(study)) < ref.index("working copy · ")

    def test_without_a_copy_the_block_shows_the_path(self, study, monkeypatch, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_panel.chooser import DirectoryChooser
        for var in datasets.OUTPUT_BASE_VARS:
            monkeypatch.setenv(var, "placeholder")
            monkeypatch.delenv(var)
        d = Directions(study)
        chooser = DirectoryChooser(d, recent_file=str(tmp_path / "chooser_recent.json"), count=lambda s: "")
        assert "working copy" not in chooser.summary.object and "<b>McMurdo</b>" in chooser.summary.object

    def test_the_recent_list_names_the_study_not_its_copy(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions, load_recent
        import pmagpy_directions.session as sess
        recent = str(tmp_path / "recent_list.json")
        old = sess.RECENT_FILE
        sess.RECENT_FILE = recent
        try:
            Directions(study)
            assert load_recent()[0] == os.path.abspath(study)
        finally:
            sess.RECENT_FILE = old

    def test_a_copy_whose_study_is_gone_is_a_study_of_its_own(self, study, base, tmp_path):
        """A copy handed on (or a study moved since) kept naming a folder that is not there: the
        side block and Home showed it as the study, and the recent list remembered it."""
        from pmagpy_directions.session import Session as Directions, load_recent
        import pmagpy_directions.session as sess
        from pmagpy_apps.home import ref_html
        from pmagpy_apps.inventory import take_inventory
        from pmagpy_panel.chooser import DirectoryChooser
        copy = datasets.working_directory(study)
        moved = str(tmp_path / "colleague" / os.path.basename(copy))
        shutil.copytree(copy, moved)
        gone = str(tmp_path / "studies" / "McMurdo-was-here")
        os.rename(study, gone)
        recorded = os.path.realpath(study)
        assert datasets.working_copy_source(moved) == ""
        assert recorded in datasets.working_copy_note(moved) and "not there any more" in datasets.working_copy_note(moved)
        assert datasets.working_copy_note(datasets.working_directory(gone)) == ""
        assert datasets.study_name(moved) == "McMurdo"
        recent = str(tmp_path / "recent_list.json")
        old = sess.RECENT_FILE
        sess.RECENT_FILE = recent
        try:
            d = Directions(moved)
            assert d.directory == moved and d.source_directory == moved
            assert load_recent()[0] == moved
        finally:
            sess.RECENT_FILE = old
        # the copy is shown as itself, and says once, quietly, where its study used to be
        block = DirectoryChooser(d, recent_file=recent, count=lambda s: "").summary.object
        assert "working copy, its study moved · " in block and block.count(recorded) == 1
        ref = ref_html(take_inventory(moved))
        assert ref.index(os.path.basename(moved)) < ref.index("not there any more") and ref.count(recorded) == 1


def converted(directory, name="lab.dat"):
    """Mark a study as PmagPy's own work: a conversion log beside its tables, as Convert writes."""
    from pmagpy import convert_registry as reg
    reg.record_conversion(directory, "sio", [name], tables={"measurements": 1})
    return directory


class TestStudiesPmagPyMadeAreWorkedOnInPlace:
    def test_the_log_is_the_registry_s(self):
        from pmagpy import convert_registry as reg
        assert datasets.CONVERSION_LOG == reg.CONVERSION_LOG

    def test_every_application_opens_a_converted_study_itself(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_rockmag.session import Session as RockMag
        from pmagpy_apps.home import HubSession, ref_html
        from pmagpy_apps.inventory import take_inventory
        from pmagpy_panel.chooser import DirectoryChooser
        converted(study)
        assert datasets.made_by_pmagpy(study) and datasets.working_directory(study) == study
        d = Directions(study)
        assert d.directory == study and d.source_directory == study
        assert Intensity(study).directory == study and RockMag(study).directory == study
        assert HubSession(study, recent_file=str(tmp_path / "hub_recent.json")).directory == study
        assert not os.path.exists(base) or os.listdir(base) == []                 # no copy was made
        block = DirectoryChooser(d, recent_file=str(tmp_path / "r.json"), count=lambda s: "").summary.object
        assert "working copy" not in block and "<b>McMurdo</b>" in block
        assert "working copy" not in ref_html(take_inventory(study))
        assert d.writes_in_place()                                     # so an export asks first, as in a checkout

    def test_a_study_without_a_log_still_gets_its_copy(self, study, base):
        assert not datasets.made_by_pmagpy(study)
        assert datasets.working_directory(study) != study
        assert not os.path.exists(os.path.join(MCMURDO, datasets.CONVERSION_LOG))    # the example has no log

    def test_a_copy_made_before_the_study_had_a_log_is_kept_and_says_so(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_apps.home import ref_html
        from pmagpy_apps.inventory import take_inventory
        from pmagpy_panel.chooser import DirectoryChooser
        copy = datasets.working_directory(study)
        assert datasets.kept_copy_note(copy) == ""
        converted(study)                      # lab files converted into the downloaded study's folder
        assert datasets.working_directory(study) == copy
        note = datasets.kept_copy_note(copy)
        assert os.path.realpath(study) in note and "made before" in note
        d = Directions(study)
        assert d.directory == copy
        block = DirectoryChooser(d, recent_file=str(tmp_path / "r.json"), count=lambda s: "").summary.object
        assert "earlier working copy · " in block and "made before" in block
        assert "made before" in ref_html(take_inventory(copy))
        assert datasets.made_by_pmagpy(copy) is False             # the copy holds the log too, and is still a copy

    def test_nothing_shipped_or_read_only_is_in_place(self, study, base, monkeypatch, tmp_path):
        import sys
        converted(study)
        monkeypatch.setattr(datasets, "shipped_roots", lambda: [os.path.realpath(os.path.dirname(study))])
        assert not datasets.made_by_pmagpy(study) and datasets.working_directory(study) != study
        monkeypatch.undo()
        app = tmp_path / "PmagPy Apps.app"
        (app / "Contents" / "MacOS").mkdir(parents=True)
        monkeypatch.setattr(sys, "frozen", True, raising=False)
        monkeypatch.setattr(sys, "_MEIPASS", str(app / "Contents" / "Frameworks"), raising=False)
        monkeypatch.setattr(sys, "executable", str(app / "Contents" / "MacOS" / "PmagPy Apps"))
        assert os.path.realpath(str(app)) in datasets.shipped_roots()
        inside = app / "Contents" / "Resources" / "data_files" / "study"
        shutil.copytree(study, inside)
        assert not datasets.made_by_pmagpy(str(inside))
        assert datasets.made_by_pmagpy(study)

    @pytest.mark.skipif(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                        reason="needs a folder that POSIX permissions make read-only")
    def test_a_read_only_converted_study_gets_a_copy(self, study, base):
        converted(study)
        os.chmod(study, 0o555)
        try:
            assert not datasets.made_by_pmagpy(study)
            assert datasets.working_directory(study) != study
        finally:
            os.chmod(study, 0o755)

    def test_the_tdt_importer_logs_what_it_wrote_and_opens_it_in_place(self, study, base, tmp_path):
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_intensity.views import DataView
        from pmagpy import convert_registry as reg
        session = Intensity(study)
        view = DataView(session, chooser_available=False)
        lab = tmp_path / "tdt_lab"
        lab.mkdir()
        rows = ["Thellier-tdt", "45\t0\t0\t0\t0", "SP1\t0.0\t100\t10\t30"]
        for i, temp in enumerate((100, 200, 300, 400, 500)):
            rows.append(f"SP1\t{temp}.0\t{95 - 15 * i}\t10\t30")
            rows.append(f"SP1\t{temp}.1\t{97 - 10 * i}\t12\t45")
        (lab / "SP1.tdt").write_text("\n".join(rows) + "\n")
        view.tdt_path.value = str(lab)
        view.tdt_units.value = "Am^2"
        view._check_tdt()
        view._convert_tdt()
        out = str(lab / "magic3")
        (entry,) = reg.read_conversions(out)
        assert entry["files"] == ["SP1.tdt"] and entry["stamps"]["SP1.tdt"]["sha1"]
        assert entry["tables"]["measurements"] == 11 and entry["values"]["moment_units"] == "Am^2"
        assert session.directory == out and "SP1" in session.data.specimens


def tdt_lab(tmp_path, name="tdt_lab"):
    """A folder holding one ThellierTool file, SP1.tdt, that checks clean."""
    lab = tmp_path / name
    lab.mkdir()
    rows = ["Thellier-tdt", "45\t0\t0\t0\t0", "SP1\t0.0\t100\t10\t30"]
    for i, temp in enumerate((100, 200, 300, 400, 500)):
        rows.append(f"SP1\t{temp}.0\t{95 - 15 * i}\t10\t30")
        rows.append(f"SP1\t{temp}.1\t{97 - 10 * i}\t12\t45")
    (lab / "SP1.tdt").write_text("\n".join(rows) + "\n")
    return lab


class TestTheTdtImportAsksBeforeReplacing:
    """Importing .tdt files again into a magic3/ that has tables asks first, as Convert does."""

    def importer(self, study, lab):
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_intensity.views import DataView
        session = Intensity(study)
        view = DataView(session, chooser_available=False)
        view.tdt_path.value = str(lab)
        view.tdt_units.value = "Am^2"
        view._check_tdt()
        return session, view

    def test_again_into_a_new_dated_folder_by_default(self, study, tmp_path):
        from datetime import date
        from pmagpy import convert_registry as reg
        lab = tdt_lab(tmp_path)
        session, view = self.importer(study, lab)
        view._convert_tdt()
        magic3 = str(lab / "magic3")
        before = digest(magic3)
        view._check_tdt()
        view._convert_tdt()                                             # the first click asks
        new = f"MagIC_{date.today().isoformat()}"
        assert view.tdt_where.visible and view.tdt_where.value == reg.NEW_FOLDER
        assert view.convert_btn.name == f"Confirm: write into {new}/"
        assert "magic3/ has MagIC tables already" in view.tdt_report.object
        assert digest(magic3) == before and not (lab / new).exists()
        view._convert_tdt()
        assert session.directory == str(lab / new) and digest(magic3) == before
        (entry,) = reg.read_conversions(str(lab / new))
        assert entry["files"] == ["SP1.tdt"] and reg.lab_folder(str(lab / new)) == str(lab)
        assert view.convert_btn.name == "Convert and open" and not view.tdt_where.visible

    def test_or_replacing_with_the_old_tables_kept(self, study, tmp_path):
        from pmagpy import convert_registry as reg
        lab = tdt_lab(tmp_path)
        session, view = self.importer(study, lab)
        view._convert_tdt()
        magic3 = lab / "magic3"
        first = (magic3 / "measurements.txt").read_text()
        view.tdt_units.value = "emu"                                    # imported again in other units
        view._check_tdt()
        view._convert_tdt()
        view.tdt_where.value = reg.REPLACE
        assert view.convert_btn.name == "Confirm: replace the tables" and view.convert_btn.button_type == "danger"
        view._convert_tdt()
        assert session.directory == str(magic3)
        assert (magic3 / "backup_before_pmagpy_apps" / "measurements.txt").read_text() == first
        assert (magic3 / "measurements.txt").read_text() != first
        assert len(reg.read_conversions(str(magic3))) == 2

    def test_another_path_withdraws_the_question(self, study, tmp_path):
        lab = tdt_lab(tmp_path)
        session, view = self.importer(study, lab)
        view._convert_tdt()
        view._check_tdt()
        view._convert_tdt()
        assert view.tdt_where.visible
        view.tdt_path.value = str(lab / "SP1.tdt")
        assert not view.tdt_where.visible and view.convert_btn.name == "Convert and open"


class TestContributionsFromMagicGetACopy:
    """A folder of tables that came from MagIC is someone's record: it is worked on in a copy, also when
    its tables were unpacked by Convert or lab files were converted into it since."""

    def test_a_contribution_file_unpacked_by_convert_is_worked_on_in_a_copy(self, study, base):
        from pmagpy import convert_registry as reg
        os.remove(os.path.join(study, "contribution.txt"))           # an older file, served without one
        reg.record_conversion(study, "magic", ["magic_contribution_13436.txt"], tables={"measurements": 1},
                              label="MagIC contribution file")
        assert datasets.from_magic(study) and not datasets.made_by_pmagpy(study)
        copy = datasets.working_directory(study)
        assert copy != study and datasets.working_copy_source(copy) == os.path.realpath(study)
        assert reg.read_conversions(study)[0]["format"] == "magic"             # the log keeps the unpack

    def test_a_download_with_lab_files_converted_into_it_is_worked_on_in_a_copy(self, study, base, tmp_path):
        from pmagpy import convert_registry as reg
        from pmagpy_apps.home import HubSession, ref_html
        from pmagpy_apps.inventory import take_inventory
        assert os.path.isfile(os.path.join(study, "contribution.txt"))         # as MagIC serves every contribution
        reg.record_conversion(study, "jr6_jr6", ["AF.jr6", "TRM.jr6"], append=True, tables={"measurements": 9})
        assert datasets.from_magic(study) and not datasets.made_by_pmagpy(study)
        session = HubSession(study, recent_file=str(tmp_path / "hub_recent.json"))
        assert session.directory != study and datasets.working_copy_source(session.directory) == os.path.realpath(study)
        assert "contribution from MagIC, with lab files PmagPy converted added to it" in ref_html(take_inventory(session.directory))
        assert datasets.kept_copy_note(session.directory) == ""

    def test_a_download_alone_says_nothing_more(self, study, base):
        copy = datasets.working_directory(study)
        assert datasets.from_magic(study) and datasets.magic_copy_note(copy) == ""

    def test_tables_a_conversion_replaced_are_pmagpy_s_own(self, study, base):
        from pmagpy import convert_registry as reg
        reg.record_conversion(study, "magic", ["mc.txt"], tables={"measurements": 1})
        reg.record_conversion(study, "jr6_jr6", ["AF.jr6"], tables={"measurements": 9})      # replaced them
        assert not datasets.from_magic(study) and datasets.made_by_pmagpy(study)
        assert datasets.working_directory(study) == study


class TestOnlyMarkedFoldersAreCopies:
    def test_a_study_kept_under_the_base_gets_a_copy_of_its_own(self, base):
        kept = os.path.join(base, "MyStudy")
        os.makedirs(kept)
        shutil.copy(os.path.join(MCMURDO, "measurements.txt"), kept)
        assert not datasets.is_working_copy(kept, base)
        copy = datasets.working_directory(kept)
        assert copy != kept and os.path.basename(copy).startswith("MyStudy-")
        assert datasets.is_working_copy(copy, base) and datasets.working_directory(copy) == copy

    def test_a_converted_study_under_the_base_is_worked_on_in_place(self, base):
        kept = os.path.join(base, "MyLab")
        os.makedirs(kept)
        shutil.copy(os.path.join(MCMURDO, "measurements.txt"), kept)
        converted(kept)
        assert datasets.working_directory(kept) == kept

    def test_a_marked_folder_anywhere_is_a_copy(self, study, tmp_path):
        moved = str(tmp_path / "elsewhere")
        shutil.copytree(datasets.working_directory(study, base=str(tmp_path / "b")), moved)
        assert datasets.is_working_copy(moved) and datasets.working_directory(moved, base=str(tmp_path / "b")) == moved


class TestTheBundledExampleIsKeyedByName:
    def test_the_example_s_copy_is_named_after_it_alone(self, base):
        assert datasets.is_bundled_example(MCMURDO)
        copy = datasets.working_directory(MCMURDO)
        assert copy == os.path.join(base, "McMurdo-example")
        assert datasets.working_copy_source(copy) == os.path.realpath(MCMURDO) and datasets.study_name(copy) == "McMurdo"

    def test_a_study_called_mcmurdo_is_not_the_example(self, study, base):
        assert not datasets.is_bundled_example(study)
        assert os.path.basename(datasets.working_directory(study)) != "McMurdo-example"

    def test_the_example_in_a_moved_or_updated_application_keeps_its_copy(self, base, tmp_path, monkeypatch):
        import sys
        copy = datasets.working_directory(MCMURDO)
        with open(os.path.join(copy, "sites.txt"), "a") as fh:
            fh.write("\n")                                  # work done on the example
        edited = digest(copy)["sites.txt"]
        for where in ("Downloads", "Applications"):        # the .app moved, or a newer version installed
            app = tmp_path / where / "PmagPy Apps.app"
            bundled = app / "Contents" / "Resources" / "data_files" / "3_0" / "McMurdo"
            shutil.copytree(MCMURDO, bundled)
            (bundled / "new_in_this_version.txt").write_text("x\n")
            monkeypatch.setattr(sys, "frozen", True, raising=False)
            monkeypatch.setattr(sys, "_MEIPASS", str(app / "Contents" / "Resources"), raising=False)
            monkeypatch.setattr(sys, "executable", str(app / "Contents" / "MacOS" / "PmagPy Apps"))
            assert datasets.is_bundled_example(str(bundled))
            assert datasets.working_directory(str(bundled)) == copy
            assert datasets.working_copy_source(copy) == os.path.realpath(bundled) and datasets.working_copy_note(copy) == ""
            assert digest(copy)["sites.txt"] == edited                       # existing files kept
            assert os.path.exists(os.path.join(copy, "new_in_this_version.txt"))   # an updated example's new files added


class TestAStaleCopy:
    def test_the_copy_records_what_it_was_made_from(self, study, base):
        import json
        copy = datasets.working_directory(study)
        marker = json.load(open(os.path.join(copy, datasets.WORKING_COPY_MARKER)))
        stamp = marker["files"]["measurements.txt"]
        assert stamp["size"] == os.path.getsize(os.path.join(study, "measurements.txt")) and len(stamp["sha1"]) == 40
        assert datasets.copy_changes(copy) == [] and datasets.stale_copy_note(copy) == ""
        # a file the study gains later is added, and recorded
        shutil.copy(os.path.join(study, "sites.txt"), os.path.join(study, "extra.txt"))
        datasets.working_directory(study)
        assert "extra.txt" in json.load(open(os.path.join(copy, datasets.WORKING_COPY_MARKER)))["files"]

    def test_a_study_that_changed_says_so_and_only_its_contents_count(self, study, base):
        copy = datasets.working_directory(study)
        os.utime(os.path.join(study, "sites.txt"), (1, 1))             # touched (moved, unpacked again): same contents
        assert datasets.copy_changes(copy) == []
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        os.remove(os.path.join(study, "ages.txt")) if os.path.exists(os.path.join(study, "ages.txt")) else None
        changed = datasets.copy_changes(copy)
        assert "measurements.txt" in changed and "sites.txt" not in changed
        note = datasets.stale_copy_note(copy)
        assert "has changed since this working copy was made on " in note and "measurements.txt" in note

    def test_a_copy_made_before_copies_recorded_their_files_is_unknown_not_stale(self, study, base):
        import json
        copy = datasets.working_directory(study)
        path = os.path.join(copy, datasets.WORKING_COPY_MARKER)
        marker = json.load(open(path))
        del marker["files"]
        open(path, "w").write(json.dumps(marker))
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        shutil.copy(os.path.join(study, "sites.txt"), os.path.join(study, "extra.txt"))
        datasets.working_directory(study)                               # adds extra.txt, and stays unknown
        assert datasets.copy_changes(copy) is None and datasets.stale_copy_note(copy) == ""
        assert "files" not in json.load(open(path))

    def test_starting_afresh_keeps_the_old_copy_and_makes_a_new_one(self, study, base, tmp_path):
        from datetime import date
        from pmagpy_directions.session import Session as Directions
        from pmagpy_panel.chooser import DirectoryChooser
        d = Directions(study)
        copy = d.directory
        with open(os.path.join(copy, "specimens.txt"), "a") as fh:
            fh.write("\n")                                              # interpretations exported into the copy
        work = digest(copy)
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        chooser = DirectoryChooser(d, recent_file=str(tmp_path / "r.json"), count=lambda s: "")
        assert chooser.stale.visible and "measurements.txt" in chooser.stale.object
        assert chooser.fresh_btn.visible and chooser.fresh_btn.name == "Start a fresh copy"
        assert chooser.start_fresh() is True
        aside = f"{os.path.realpath(copy)}-{date.today().isoformat()}"
        assert digest(aside) == work                                    # the old copy, whole and untouched
        assert d.directory == copy and digest(copy)["measurements.txt"] == digest(study)["measurements.txt"]
        assert datasets.copy_changes(copy) == [] and not chooser.stale.visible and not chooser.fresh_btn.visible
        # a set-aside copy is not offered a fresh start of its own, and a second one the same day gets -2
        assert datasets.stale_copy_note(aside) and not datasets.can_start_fresh(aside)
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        datasets.set_copy_aside(copy)
        assert os.path.isdir(aside + "-2") and not os.path.exists(copy)

    def test_home_says_so_and_starts_afresh(self, study, base, tmp_path):
        from pmagpy_apps.home import HubSession, HomeView
        session = HubSession(study, recent_file=str(tmp_path / "hub_recent.json"))
        view = HomeView(session)
        copy = session.directory
        assert not view.fresh_btn.visible
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        session.load(study)
        assert view.fresh_btn.visible and "has changed since" in view.ref.object
        assert view.start_fresh() is True
        assert session.directory == copy and not view.fresh_btn.visible
        assert any(n.startswith(os.path.basename(copy) + "-") for n in os.listdir(base))

    def test_a_kept_copy_of_a_converted_study_starts_afresh_in_place(self, study, base, tmp_path):
        from pmagpy_apps.home import HubSession, HomeView
        session = HubSession(study, recent_file=str(tmp_path / "hub_recent.json"))
        copy = session.directory
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        converted(study)                                  # lab files converted into the study since
        session.load(study)
        view = HomeView(session)
        assert session.directory == copy and view.fresh_btn.name == "Work on the study itself"
        assert view.start_fresh() is True and session.directory == study


class TestAWindowOnACopySetAside:
    """"Start a fresh copy" makes a new copy at the old one's path: a window still open on the old copy
    writes neither its autosave nor an export into the new one, and says to reload."""

    def fresh(self, study, tmp_path):
        from pmagpy_apps.home import HubSession, HomeView
        with open(os.path.join(study, "measurements.txt"), "a") as fh:
            fh.write("\n")
        view = HomeView(HubSession(study, recent_file=str(tmp_path / "hub_recent.json")))
        assert view.fresh_btn.visible and view.start_fresh() is True
        return view.s.directory

    def test_each_copy_has_an_id_of_its_own(self, study, base):
        copy = datasets.working_directory(study)
        first = datasets.copy_id(copy)
        assert first and datasets.copy_id(study) is None
        shutil.copy(os.path.join(study, "sites.txt"), os.path.join(study, "extra.txt"))
        datasets.working_directory(study)                      # a file the study gained: the same copy
        assert datasets.copy_id(copy) == first
        aside = os.path.realpath(copy) + "-aside"
        os.rename(copy, aside)
        assert datasets.copy_id(copy) is None and datasets.copy_id(aside) == first
        assert datasets.working_directory(study) == copy and datasets.copy_id(copy) not in (None, first)

    def test_directions_writes_nothing_into_the_new_copy(self, study, base, tmp_path):
        from pmagpy_directions.session import AUTOSAVE_NAME, Session as Directions
        from pmagpy_panel import autosave
        old = Directions(study, cache=True)
        copy = old.directory
        assert self.fresh(study, tmp_path) == copy
        before = digest(copy)
        old.specimen = old.data.specimen_names[1]
        old.toggle_step(1)                                      # an edit in the window left on the old copy
        assert old.status == autosave.COPY_REPLACED and "reload" in old.status
        with pytest.raises(autosave.WorkingCopyReplaced):
            old.export_tables()
        with pytest.raises(OSError):
            old.save_redo(os.path.join(copy, "mine.redo"))
        assert digest(copy) == before and not os.path.exists(os.path.join(copy, AUTOSAVE_NAME))
        reloaded = Directions(study, cache=True)                # a reload reads the new copy, not the old dataset
        assert reloaded.directory == copy and reloaded.data is not old.data
        reloaded.specimen = reloaded.data.specimen_names[1]
        reloaded.toggle_step(1)
        assert reloaded.status != autosave.COPY_REPLACED and os.path.exists(os.path.join(copy, AUTOSAVE_NAME))

    def test_the_export_view_says_to_reload(self, study, base, tmp_path):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_directions.views import ExportView
        old = Directions(study)
        copy = old.directory
        self.fresh(study, tmp_path)
        before = digest(copy)
        view = ExportView(old)
        view._write()
        assert "Export failed" in view.status.object and "reload" in view.status.object
        assert digest(copy) == before

    def test_intensity_writes_nothing_into_the_new_copy(self, study, base, tmp_path):
        from pmagpy_intensity.session import AUTOSAVE_NAME, Session as Intensity
        from pmagpy_panel import autosave
        old = Intensity(study)
        copy = old.directory
        self.fresh(study, tmp_path)
        before = digest(copy)
        old.specimen = old.data.specimen_names[0]
        old.toggle_step(int(old.spec.steps["sequence"].iloc[1]))
        assert old.status == autosave.COPY_REPLACED
        with pytest.raises(autosave.WorkingCopyReplaced):
            old.export_tables()
        with pytest.raises(OSError):
            old.save_session(os.path.join(copy, "mine.json"))
        assert digest(copy) == before and not os.path.exists(os.path.join(copy, AUTOSAVE_NAME))

    def test_intensity_show_code_writes_no_snapshot_anywhere_and_says_to_reload(self, study, base, tmp_path,
                                                                                 monkeypatch):
        import pmagpy_intensity.session as session_module
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_intensity.views import GroupView
        from pmagpy_panel import autosave
        home = tmp_path / "home"
        monkeypatch.setattr(session_module, "CODE_SESSION_HOME", str(home))
        old = Intensity(study)
        copy = old.directory
        self.fresh(study, tmp_path)
        before = digest(copy)
        old.specimen = old.data.specimen_names[0]
        old.toggle_step(int(old.spec.steps["sequence"].iloc[1]))
        assert old.status == autosave.COPY_REPLACED
        with pytest.raises(autosave.WorkingCopyReplaced):
            old.code_session_file()
        group = GroupView(old)
        group.set_active(True)
        group.code.toggle.value = True
        assert f"# {autosave.COPY_REPLACED};" in group.code.text and "reload" in group.code.text
        assert digest(copy) == before and not home.exists()
        assert not [os.path.join(r, n) for r, _, names in os.walk(base) for n in names
                    if n == session_module.CODE_SESSION_NAME]

    def test_the_metadata_page_does_not_save_into_the_new_copy(self, study, base, tmp_path):
        from pmagpy_apps import metadata
        from pmagpy_apps.home import HubSession
        old = HubSession(study, recent_file=str(tmp_path / "r.json"))
        copy = old.directory
        page = metadata.MetadataView(old)
        self.fresh(study, tmp_path)
        before = digest(copy)
        assert page.save() is False
        assert "Not saved" in page.message.object and "reload" in page.message.object
        assert digest(copy) == before
        old.load(study)                                         # a reload opens the new copy and saves there
        assert page.save() is True

    def test_a_study_worked_on_in_place_is_not_affected(self, study, base):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_panel import autosave
        converted(study)
        d = Directions(study)
        assert d.directory == study
        d.specimen = d.data.specimen_names[1]
        d.toggle_step(1)
        assert d.status != autosave.COPY_REPLACED and d.export_tables()


class TestOneClickInAWorkingCopy:
    def test_a_converted_study_worked_on_in_place_still_asks_first(self, study, base):
        from pmagpy_directions.session import Session as Directions
        from pmagpy_directions.views import ExportView
        from pmagpy_intensity.session import Session as Intensity
        from pmagpy_intensity.views import ExportView as IntensityExport
        converted(study)
        before = digest(study)
        view = ExportView(Directions(study))
        view._write()
        assert "data directory itself" in view.status.object and view.write_btn.name.startswith("Confirm")
        pint = Intensity(study)
        pint.autosave_enabled = False
        iview = IntensityExport(pint)
        iview._export()
        assert "data directory itself" in iview.message.object and iview.export_btn.name.startswith("Confirm")
        assert digest(study) == before
