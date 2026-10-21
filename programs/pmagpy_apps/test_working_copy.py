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
