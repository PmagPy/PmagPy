"""
Tests for the Anisotropy application: the session, the selection pickers and
the views against the shipped McMurdo example (``data_files/3_0/McMurdo``:
19 AARM tensors in specimen coordinates, rotatable to geographic with the
sample orientations). The statistics themselves are tested in
``pmagpy/test/test_anisotropy.py``; here the views are checked to call them
with what the widgets say and to emit code that reproduces the call. Run
with the apps environment::

    pytest programs/pmagpy_anisotropy/test_app.py -q
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

pn = pytest.importorskip("panel")

from pmagpy import anisotropy  # noqa: E402
from pmagpy_anisotropy import app, session as ss  # noqa: E402
from pmagpy_anisotropy.views import (DataView, EigenvectorsView, ReduceView, SelectionView,  # noqa: E402
                                     ShapeView, SpecimensView)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
EXAMPLE = os.path.join(REPO, "data_files", "3_0", "McMurdo")


@pytest.fixture
def session():
    return ss.Session(EXAMPLE)


def code_text(view) -> str:
    return view.code.text


# ----------------------------------------------------------------------------- the session
class TestSession:
    def test_the_example_loads_in_the_frame_its_tensors_are_in(self, session):
        assert session.directory == EXAMPLE
        assert session.status == "19 specimens with tensors (AARM) · 19 specimen / 0 geographic / 0 tilt-corrected"
        assert session.n_specimens() == 19 and session.types() == ["AARM"]
        assert session.frames() == {"s": 19, "g": 0, "t": 0}
        assert session.frame_counts() == {"s": 19, "g": 19, "t": 0}          # geographic reachable by rotation
        assert session.coordinates == "s" and session.level == "site" and session.group == ss.ALL
        assert session.groups() == [ss.ALL, "mc15", "mc121", "mc142", "mc144", "mc217"]   # natural order
        assert session.groups("location") == [ss.ALL, "McMurdo"]

    def test_the_selection_filters_the_tensor_table(self, session):
        assert len(session.selection()) == 19 and set(session.selection()["source"]) == {"table"}
        session.group = "mc121"
        assert list(session.selection()["specimen"]) == ["mc121d1", "mc121f2", "mc121g1", "mc121k1", "mc121k2"]
        session.coordinates = "g"
        sel = session.selection()
        assert len(sel) == 5 and set(sel["source"]) == {"rotated"} and set(sel["coordinates"]) == {"g"}
        assert session.selection_label() == "mc121 · geographic"
        session.coordinates = "t"
        assert session.selection().empty                                    # no bedding in the example

    def test_a_frame_the_table_does_not_have_is_replaced_by_the_one_it_does(self):
        specimens = pd.read_csv(os.path.join(EXAMPLE, "specimens.txt"), sep="\t", skiprows=1)
        g = specimens[specimens["aniso_s"].notna()].copy()
        g["aniso_tilt_correction"] = 0                                       # a table with geographic tensors only
        s = ss.Session(specimens=g)
        assert s.directory == "" and s.coordinates == "g" and s.n_specimens() == 19
        assert s.frames() == {"s": 0, "g": 19, "t": 0} and s.frame_counts() == {"s": 0, "g": 19, "t": 0}
        assert s.status == "19 specimen rows in memory"
        assert ss.as_session(g).coordinates == "g" and ss.as_session(s) is s

    def test_a_directory_without_specimens_is_refused_with_a_reason(self, tmp_path):
        s = ss.Session(str(tmp_path))
        assert s.specimens is None and "no specimens.txt" in s.status
        assert not ss.has_specimens(str(tmp_path))

    def test_specimens_without_tensors_load_but_have_nothing_to_show(self, tmp_path):
        specimens = pd.read_csv(os.path.join(EXAMPLE, "specimens.txt"), sep="\t", skiprows=1)
        bare = specimens[specimens["aniso_s"].isna()].drop(columns=["aniso_s"])
        with open(tmp_path / "specimens.txt", "w") as fh:
            fh.write("tab\tspecimens\n")
            bare.to_csv(fh, sep="\t", index=False)
        s = ss.Session(str(tmp_path))
        assert s.specimens is not None and s.n_specimens() == 0 and "no anisotropy tensors" in s.status
        assert s.selection().empty and s.groups() == [ss.ALL]


# ----------------------------------------------------------------------------- the pickers
class TestSelectionView:
    def test_widgets_follow_the_session_and_drive_it(self, session):
        view = SelectionView(session)
        assert view.coordinates.options == ["specimen (19)", "geographic (19)*"]   # * = rotated here
        assert view.coordinates.value == "specimen (19)"
        assert not view.aniso_type.visible                                  # one type: nothing to pick
        assert "rotated here" in view.note.object
        # session -> widgets
        session.group = "mc142"
        assert view.group.value == "mc142"
        session.coordinates = "g"
        assert view.coordinates.value == "geographic (19)*"
        # widgets -> session
        view.coordinates.value = "specimen (19)"
        assert session.coordinates == "s"
        view.level.value = "sample"
        assert session.level == "sample" and session.group == ss.ALL
        assert view.group.options[:3] == [ss.ALL, "mc15a", "mc15b"]
        view.group.value = "mc121d"
        assert session.group == "mc121d" and list(session.selection()["specimen"]) == ["mc121d1"]

    def test_a_new_directory_resets_the_pickers(self, session, tmp_path):
        view = SelectionView(session)
        session.group = "mc121"
        shutil.copy(os.path.join(EXAMPLE, "specimens.txt"), tmp_path / "specimens.txt")   # no samples: no rotation
        assert session.load(str(tmp_path))
        assert view.coordinates.options == ["specimen (19)"] and view.group.value == ss.ALL
        assert view.note.object == ""


# ----------------------------------------------------------------------------- the views
class TestEigenvectorsView:
    def test_all_specimens_get_hext_statistics_and_the_reproducing_code(self, session):
        view = EigenvectorsView(session)
        stats = view.stats
        assert stats["n"] == 19 and stats["hext"] is not None and stats["bootstrap"] is None
        expected = anisotropy.group_statistics(list(session.selection()["s"]), hext=True, bootstrap=False)
        assert stats["hext"]["F"] == pytest.approx(expected["hext"]["F"])
        assert stats["v1_dec"] == pytest.approx(expected["v1_dec"])
        assert "F</" in view.summary.object or "F" in view.summary.object
        assert "from the scatter of 19 tensors" in view.table.object
        assert not view.cdf_box.visible and not view.n_bootstraps.visible
        text = code_text(view)
        assert "aniso.tensor_table(specimens, samples, coordinates='s')" in text
        assert "aniso.group_statistics(list(tensors['s']), hext=True, bootstrap=False)" in text
        assert "hext_ellipses = aniso.hext_ellipses(stats['hext'])" in text
        assert "tensors[tensors[" not in text                              # the whole table: no filter line

    def test_bootstrap_follows_the_widgets_and_is_seeded(self, session):
        session.group = "mc121"
        session.coordinates = "g"
        view = EigenvectorsView(session)
        view.set_parameters(bootstrap=True, n_bootstraps=300, seed=7)
        boot = view.stats["bootstrap"]
        assert boot is not None and boot["n_bootstraps"] == 300 and not boot["parametric"]
        assert boot["taus"].shape == (300, 3)
        assert view.cdf_box.visible and view.n_bootstraps.visible and view.parametric.visible
        again = anisotropy.group_statistics(list(session.selection()["s"]), hext=True, bootstrap=True,
                                            n_bootstraps=300, random_seed=7)
        np.testing.assert_allclose(boot["taus"], again["bootstrap"]["taus"])
        assert "bootstrap ζ / η" in view.table.object and "non-parametric bootstrap of 300 draws (seed 7)" in view.table.object
        text = code_text(view)
        assert "tensors = tensors[tensors['site'] == 'mc121']" in text
        assert "coordinates='g'" in text
        # a long call is wrapped one argument per line
        assert ("stats = aniso.group_statistics(\n    list(tensors['s']),\n    hext=True,\n    bootstrap=True,\n"
                "    parametric=False,\n    n_bootstraps=300,\n    random_seed=7,\n)") in text
        assert "boot_ellipses = aniso.bootstrap_ellipses(stats['hext'], stats['bootstrap']['params'])" in text
        assert "tau_bounds = aniso.bootstrap_eigenvalue_bounds(stats['bootstrap']['taus'])" in text
        view.set_parameters(parametric=True)
        assert view.stats["bootstrap"]["parametric"] and "parametric bootstrap" in view.table.object
        view.set_parameters(hext=False)
        assert view.stats["hext"] is None and "rerun with hext=True" in code_text(view)

    def test_a_single_specimen_gets_the_hext_statistics_of_its_own_scatter(self, session):
        session.group = "mc217"                                              # one specimen in the example
        view = EigenvectorsView(session)
        stats = view.stats
        row = session.selection().iloc[0]
        assert stats["n"] == 1 and stats.get("specimen_hext") and stats["bootstrap"] is None
        expected = anisotropy.specimen_hext(row["s"], float(row["aniso_s_sigma"]), int(row["aniso_s_n_measurements"]),
                                            row["aniso_type"])
        assert stats["hext"]["F"] == pytest.approx(expected["F"])
        assert stats["hext"]["e12"] == pytest.approx(expected["e12"])
        assert "from this specimen's measurement scatter" in view.table.object
        text = code_text(view)
        assert ("hext = aniso.specimen_hext(row['s'], row['aniso_s_sigma'], row['aniso_s_n_measurements'], "
                "row['aniso_type'])") in text
        assert "group_statistics" not in text
        view.set_parameters(bootstrap=True)                                  # nothing to bootstrap from one tensor
        assert view.stats["bootstrap"] is None and not view.cdf_box.visible

    def test_an_empty_selection_renders_empty(self, session):
        session.coordinates = "t"
        view = EigenvectorsView(session)
        assert view.stats is None and "nothing selected" in view.summary.object and view.table.object == ""
        assert "group_statistics" not in code_text(view)

    def test_the_view_renders_from_a_dataframe(self):
        specimens = pd.read_csv(os.path.join(EXAMPLE, "specimens.txt"), sep="\t", skiprows=1)
        view = EigenvectorsView(specimens[specimens["aniso_s"].notna()])
        assert view.stats["n"] == 19
        assert "# specimens, samples: the DataFrames this view was given" in code_text(view)
        assert isinstance(view.panel(), pn.Column)


@pytest.fixture
def copy_dir(tmp_path):
    """A McMurdo copy without the measurements (the save never reads them): saves land here."""
    for name in ("specimens.txt", "samples.txt", "sites.txt", "locations.txt", "contribution.txt"):
        shutil.copy(os.path.join(EXAMPLE, name), tmp_path / name)
    return str(tmp_path)


class TestMeanSave:
    def test_the_save_waits_until_one_site_or_sample_is_picked(self, copy_dir):
        s = ss.Session(copy_dir)
        view = EigenvectorsView(s)
        assert view.save.button.disabled and "pick one site" in view.save.note.object
        assert view.save.table == "sites" and view.save.button.name == "Save to sites.txt"
        s.level = "location"
        view.refresh()
        assert view.save.button.disabled and "group by one of those" in view.save.note.object
        s.level = "sample"
        s.group = "mc217a"                                                    # the one-specimen sample
        view.refresh()
        assert view.save.table == "samples" and view.save.button.name == "Save to samples.txt"
        assert view.save.button.disabled and "at least two tensors" in view.save.note.object
        s.group = "mc121k"
        view.refresh()
        assert not view.save.button.disabled and view.save.note.object == ""

    def test_a_site_mean_goes_on_a_row_of_sites_with_its_code_and_a_backup(self, copy_dir):
        s = ss.Session(copy_dir)
        s.group, s.coordinates = "mc121", "g"
        view = EigenvectorsView(s)
        before = pd.read_csv(os.path.join(copy_dir, "sites.txt"), sep="\t", skiprows=1)
        path = view.save.save()
        assert path == os.path.join(copy_dir, "sites.txt")
        sites = pd.read_csv(path, sep="\t", skiprows=1)
        assert len(sites) == len(before) + 1
        row = sites.iloc[-1]
        assert row["site"] == "mc121" and row["location"] == "McMurdo"
        assert row["aniso_type"] == "AARM" and int(row["aniso_tilt_correction"]) == 0
        assert row["method_codes"] == "LP-AN-ARM:AE-H" and row["specimens"] == "mc121d1:mc121f2:mc121g1:mc121k1:mc121k2"
        assert row["software_packages"] == s.project.software_tag and row["citations"] == "This study"
        expected = anisotropy.mean_record(view.stats, "AARM", "g")
        assert row["aniso_v1"] == expected["aniso_v1"] and float(row["aniso_ftest"]) == pytest.approx(expected["aniso_ftest"])
        # the other rows are as they were, the original is kept and the calls are on record
        for column in before.columns:
            assert (sites.iloc[:len(before)][column].fillna("").astype(str).to_numpy()
                    == before[column].fillna("").astype(str).to_numpy()).all(), column
        assert os.path.exists(os.path.join(copy_dir, s.project.backup_dir_name(), "sites.txt"))
        assert "1 row added" in view.save.note.object and "sites.py" in view.save.note.object
        with open(os.path.join(copy_dir, "sites.py")) as fh:
            script = fh.read()
        assert "# ----- mean tensor: mc121 · geographic" in script
        text = code_text(view)
        assert "record = aniso.mean_record(stats, 'AARM', 'g', specimens=list(tensors['specimen']))" in text
        assert "sites = aniso.add_mean_to_table(sites, 'site', 'mc121', record, parent={'location': 'McMurdo'})" in text
        assert "contribution.add_magic_table('sites', df=sites)" in text
        # the code, run as a notebook would on a fresh copy, writes the same row
        fresh = os.path.join(copy_dir, "fresh")
        os.mkdir(fresh)
        for name in ("specimens.txt", "samples.txt", "sites.txt"):
            shutil.copy(os.path.join(EXAMPLE, name), os.path.join(fresh, name))
        exec(text.replace(f"'{copy_dir}'", f"'{fresh}'"), {"__name__": "__notebook__"})
        again = pd.read_csv(os.path.join(fresh, "sites.txt"), sep="\t", skiprows=1)
        assert len(again) == len(before) + 1 and again.iloc[-1]["aniso_v1"] == row["aniso_v1"]
        assert again.iloc[-1]["description"] == row["description"]
        # saving the same mean again changes nothing
        view.refresh()
        view.save.save()
        assert "nothing changed" in view.save.note.object
        assert len(pd.read_csv(path, sep="\t", skiprows=1)) == len(before) + 1

    def test_a_sample_mean_goes_to_samples(self, copy_dir):
        s = ss.Session(copy_dir)
        s.level, s.group = "sample", "mc121k"
        view = EigenvectorsView(s)
        path = view.save.save()
        assert path == os.path.join(copy_dir, "samples.txt")
        samples = pd.read_csv(path, sep="\t", skiprows=1)
        row = samples.iloc[-1]
        assert row["sample"] == "mc121k" and row["site"] == "mc121" and row["specimens"] == "mc121k1:mc121k2"
        assert int(row["aniso_tilt_correction"]) == -1 and row["method_codes"] == "LP-AN-ARM:AE-H"
        assert "samples.py" in view.save.note.object
        assert not os.path.exists(os.path.join(copy_dir, "sites.py"))

    def test_a_dataframe_session_has_nowhere_to_save(self):
        specimens = pd.read_csv(os.path.join(EXAMPLE, "specimens.txt"), sep="\t", skiprows=1)
        view = EigenvectorsView(specimens[specimens["aniso_s"].notna()])
        view.s.group = "mc121"
        view.refresh()
        assert view.save.button.disabled and "in a notebook" in view.save.note.object


class TestShapeView:
    def test_the_mean_tensor_and_the_specimen_ranges(self, session):
        view = ShapeView(session)
        m = view.mean
        expected = anisotropy.group_statistics(list(session.selection()["s"]), hext=False)
        assert m["aniso_pp"] == pytest.approx(expected["aniso_pp"]) and "hext" in m
        assert "P′ (Jelinek)" in view.table.object and ">min</th>" in view.table.object
        assert ("oblate" if m["aniso_t"] > 0 else "prolate") in view.summary.object
        assert "mean = aniso.group_statistics(list(tensors['s']), hext=False)" in code_text(view)
        assert "shape = tensors[['specimen'] + aniso.SHAPE_COLUMNS]" in code_text(view)
        session.group = "mc217"
        assert view.mean["aniso_p"] == pytest.approx(session.selection().iloc[0]["aniso_p"])
        assert ">min</th>" not in view.table.object and "group_statistics" not in code_text(view)
        session.coordinates = "t"
        assert view.mean is None and view.table.object == ""


class TestSpecimensView:
    def test_the_table_shows_the_selection_in_readable_columns(self, session):
        view = SpecimensView(session)
        shown = view.table.value
        assert len(shown) == 19 and list(shown.columns) == SpecimensView.COLUMNS
        row = shown[shown["specimen"] == "mc121d1"].iloc[0]
        t = session.selection().set_index("specimen").loc["mc121d1"]
        assert row["V1"] == f"{t['v1_dec']:.1f} / {t['v1_inc']:.1f}" and row["source"] == "table"
        assert row["tau1"] == round(t["tau1"], 4)
        assert "rotated here" not in view.summary.object
        session.coordinates = "g"
        assert set(view.table.value["source"]) == {"rotated"} and "rotated here" in view.summary.object
        assert "aniso.EIGEN_COLUMNS" in code_text(view)
        session.coordinates = "t"
        assert view.table.value.empty and list(view.table.value.columns) == SpecimensView.COLUMNS


# ----------------------------------------------------------------------------- measurements -> tensors
@pytest.fixture(scope="module")
def aarm_measurements():
    """McMurdo's 323 LP-AN-ARM measurement rows (the 6.6 MB table is mostly demagnetization)."""
    m = pd.read_csv(os.path.join(EXAMPLE, "measurements.txt"), sep="\t", skiprows=1, low_memory=False)
    return m[m["method_codes"].fillna("").str.contains("LP-AN-ARM")].reset_index(drop=True)


@pytest.fixture
def meas_dir(tmp_path, aarm_measurements):
    """A directory with the AARM measurements and the samples but no specimens.txt: Reduce starts it."""
    with open(tmp_path / "measurements.txt", "w") as fh:
        fh.write("tab\tmeasurements\n")
        aarm_measurements.to_csv(fh, sep="\t", index=False)
    shutil.copy(os.path.join(EXAMPLE, "samples.txt"), tmp_path / "samples.txt")
    return str(tmp_path)


class TestReduceView:
    def test_measurements_alone_open_and_reduce_to_the_stored_tensors(self, meas_dir):
        assert ss.can_open(meas_dir) and not ss.has_specimens(meas_dir)
        s = ss.Session(meas_dir)
        assert s.status == f"{meas_dir}: no tensors yet — 18 specimens with AARM measurements (Reduce)"
        assert s.n_specimens() == 0 and s.protocols() == {"AARM": 18}
        view = ReduceView(s)
        assert view.protocol.options == ["AARM"] and view.protocol.value == "AARM" and view.baseline.value
        shown = view.table.value
        assert len(shown) == 18 and list(shown.columns) == ReduceView.COLUMNS[:-1]    # no alteration checks
        stored = pd.read_csv(os.path.join(EXAMPLE, "specimens.txt"), sep="\t", skiprows=1)
        stored = stored[stored["aniso_s"].notna()].set_index("specimen")
        row = shown[shown["specimen"] == "mc121d1"].iloc[0]
        assert row["V1"] == "275.2 / 62.3" and row["aniso_s_n_measurements"] == 9      # positions, as aarm_magic counts
        assert row["aniso_ftest"] == pytest.approx(stored.loc["mc121d1", "aniso_ftest"], abs=1e-3)
        assert "specimens reduced" in view.summary.object and "not reduced" not in view.summary.object
        assert view.problems.object == "" and not view.save.button.disabled
        assert "tensors, problems = aniso.reduce_measurements(measurements, 'AARM', baseline=True)" in code_text(view)
        assert "measurements = contribution.tables['measurements'].df" in code_text(view)
        # without the baseline the residual ARM left after each AF step is fit as if it were acquired
        # in the field: a different tensor (aarm_magic subtracts it; only the antipodal 6-position
        # ATRM design cancels an offset — see test_anisotropy.py)
        sigma = view.tensors.set_index("specimen")["aniso_s_sigma"]
        view.set_parameters(baseline=False)
        assert "baseline=False" in code_text(view)
        again = view.tensors.set_index("specimen")
        assert again["aniso_v1"].loc["mc121d1"] != "0.356621:275.2:62.3"
        assert (again["aniso_s_sigma"] != sigma).all()
        view.set_parameters(baseline=True)
        assert view.tensors.set_index("specimen")["aniso_v1"].loc["mc121d1"] == "0.356621:275.2:62.3"

    def test_the_save_starts_the_specimens_table_and_the_views_follow(self, meas_dir):
        s = ss.Session(meas_dir)
        view = ReduceView(s)
        eigen, pickers, data = EigenvectorsView(s), SelectionView(s), DataView(s, chooser_available=False)
        assert eigen.stats is None and pickers.group.options == [ss.ALL]
        assert "0 specimens with tensors" in data.summary.object
        assert view.save.button.name == "Save to specimens.txt" and not view.save.button.disabled
        path = view.save.save()
        assert path == os.path.join(meas_dir, "specimens.txt")
        specimens = pd.read_csv(path, sep="\t", skiprows=1)
        assert len(specimens) == 18 and set(specimens["aniso_type"]) == {"AARM"}
        assert set(specimens["method_codes"]) == {"LP-AN-ARM:AE-H"}
        assert set(specimens["software_packages"]) == {s.project.software_tag}
        assert set(specimens["experiments"]) == {f"{name}-LP-AN-ARM" for name in specimens["specimen"]}
        assert (specimens["aniso_tilt_correction"] == -1).all() and (specimens["citations"] == "This study").all()
        assert specimens["sample"].isna().all()   # no sample column in these measurements, none listed in samples.txt
        # the session re-read the table it just wrote and every view moved with it
        assert s.version >= 2 and s.n_specimens() == 18
        assert s.status.startswith("18 specimens with tensors (AARM)")
        assert eigen.stats is not None and eigen.stats["n"] == 18
        assert "18 specimens with tensors" in data.summary.object
        assert pickers.group.options == [ss.ALL] and pickers.coordinates.value.startswith("specimen (18)")
        assert "already in specimens.txt as AARM" in view.summary.object
        assert "specimens.py" in view.save.note.object
        text = code_text(view)
        assert "samples = contribution.tables['samples'].df if 'samples' in contribution.tables else None" in text
        assert "specimens = aniso.add_tensors_to_specimens_table(specimens, tensors, samples)" in text
        assert "contribution.add_magic_table('specimens', df=specimens)" in text
        # the emitted code, run on a fresh copy of the measurements, writes the same table
        fresh = os.path.join(meas_dir, "fresh")
        os.mkdir(fresh)
        for name in ("measurements.txt", "samples.txt"):
            shutil.copy(os.path.join(meas_dir, name), os.path.join(fresh, name))
        exec(text.replace(f"'{meas_dir}'", f"'{fresh}'"), {"__name__": "__notebook__"})
        again = pd.read_csv(os.path.join(fresh, "specimens.txt"), sep="\t", skiprows=1)
        assert list(again["aniso_s"]) == list(specimens["aniso_s"])
        # saving the same tensors again replaces them in place
        view.save.save()
        assert len(pd.read_csv(path, sep="\t", skiprows=1)) == 18

    def test_kappabridge_positions_reduce_as_ams_without_a_baseline(self, tmp_path):
        """A k15 conversion with its specimens.txt taken away: fifteen susceptibilities per specimen."""
        from pmagpy import convert_registry as reg
        k15 = os.path.join(REPO, "data_files", "convert_2_magic", "k15_magic", "k15_example.dat")
        d = str(tmp_path)
        assert reg.convert_files(reg.FORMATS["k15"], [k15], {"location": "Trinidad"}, d, record=False).ok
        stored = pd.read_csv(os.path.join(d, "specimens.txt"), sep="\t", skiprows=1)
        stored = stored[stored["aniso_tilt_correction"] == -1].set_index("specimen")
        os.remove(os.path.join(d, "specimens.txt"))
        assert ss.can_open(d)
        s = ss.Session(d)
        assert s.status == f"{d}: no tensors yet — 8 specimens with AMS measurements (Reduce)"
        assert s.protocols() == {"AMS": 8}
        view = ReduceView(s)
        assert view.protocol.options == ["AMS"] and view.protocol.value == "AMS"
        assert view.baseline.disabled                                        # no zero-field step to subtract
        assert "tensors, problems = aniso.reduce_measurements(measurements, 'AMS')" in code_text(view)
        assert "baseline" not in code_text(view)
        shown = view.table.value
        assert len(shown) == 8 and "aniso_alt" not in shown.columns
        assert (shown["aniso_s_n_measurements"] == 15).all()
        row = view.tensors.set_index("specimen").loc["tr245f"]
        np.testing.assert_allclose(anisotropy.parse_s(row["aniso_s"]), anisotropy.parse_s(stored.loc["tr245f", "aniso_s"]),
                                   atol=1e-8)
        assert row["aniso_s_unit"] == "SI" and row["aniso_type"] == "AMS"
        path = view.save.save()
        specimens = pd.read_csv(path, sep="\t", skiprows=1)
        assert len(specimens) == 8 and set(specimens["aniso_type"]) == {"AMS"}
        assert set(specimens["method_codes"]) == {"LP-AN-MS:AE-H"} and set(specimens["aniso_s_unit"]) == {"SI"}
        assert list(specimens["sample"]) == list(specimens["specimen"])      # k15 names the sample on each row
        assert s.status.startswith("8 specimens with tensors (AMS)")
        # one specimen's Hext statistics use the nine degrees of freedom of fifteen scalars
        s.level = "sample"
        s.group = "tr245f"                                                  # the sample is the specimen here
        eigen = EigenvectorsView(s)
        assert eigen.stats["n"] == 1 and eigen.stats.get("specimen_hext")
        expected = anisotropy.specimen_hext(row["aniso_s"], float(row["aniso_s_sigma"]), 15, "AMS")
        assert eigen.stats["hext"]["e12"] == pytest.approx(expected["e12"], abs=1e-3)
        assert eigen.stats["hext"]["e12"] != pytest.approx(
            anisotropy.specimen_hext(row["aniso_s"], float(row["aniso_s_sigma"]), 15)["e12"], abs=1e-3)

    def test_tensors_already_in_the_table_are_counted_and_replaced(self, copy_dir, aarm_measurements):
        with open(os.path.join(copy_dir, "measurements.txt"), "w") as fh:
            fh.write("tab\tmeasurements\n")
            aarm_measurements.to_csv(fh, sep="\t", index=False)
        s = ss.Session(copy_dir)
        view = ReduceView(s)
        assert ">18<" in view.summary.object and "already in specimens.txt as AARM" in view.summary.object
        before = pd.read_csv(os.path.join(copy_dir, "specimens.txt"), sep="\t", skiprows=1)
        view.save.save()
        assert "18 rows updated" in view.save.note.object
        after = pd.read_csv(os.path.join(copy_dir, "specimens.txt"), sep="\t", skiprows=1)
        assert len(after) == len(before)                       # the 19th stored tensor has no measurements here
        assert s.n_specimens() == 19 and s.status.startswith("19 specimens with tensors (AARM)")
        replaced = after[after["specimen"] == "mc121d1"]
        replaced = replaced[replaced["aniso_s"].notna()].iloc[0]
        assert replaced["sample"] == "mc121d" and replaced["software_packages"] == s.project.software_tag
        assert replaced["aniso_v1"] == "0.356621:275.2:62.3"   # lower hemisphere, where the stored one was upper

    def test_a_directory_without_anisotropy_measurements_has_nothing_to_reduce(self, copy_dir):
        s = ss.Session(copy_dir)
        assert s.protocols() == {}
        view = ReduceView(s)
        assert view.protocol.options == [] and view.table.value.empty
        assert view.save.button.disabled and "nothing to reduce" in view.save.note.object
        assert "# nothing to reduce" in code_text(view)

    def test_the_view_renders_from_a_measurements_dataframe(self, aarm_measurements):
        view = ReduceView(aarm_measurements)
        assert len(view.table.value) == 18 and view.protocol.options == ["AARM"]
        assert "# measurements: the DataFrame this view was given" in code_text(view)
        assert view.save.button.disabled and "in a notebook" in view.save.note.object


# ----------------------------------------------------------------------------- the application
class TestApp:
    def test_the_body_has_the_side_column_and_a_tab_per_view(self, session):
        body = app.build_body(session)
        assert [key for key in body.views] == ["eigenvectors", "shape", "specimens", "reduce"]
        assert isinstance(body.views["eigenvectors"], EigenvectorsView)
        assert isinstance(body.selection, SelectionView)
        template = app.create_app(EXAMPLE)
        assert template.session.n_specimens() == 19

    def test_a_directory_that_cannot_be_opened_gets_a_message(self, tmp_path):
        page = app.create_app(str(tmp_path))
        assert isinstance(page, pn.pane.Markdown) and "no specimens.txt" in page.object
