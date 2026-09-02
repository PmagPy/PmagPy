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
from pmagpy_anisotropy.views import EigenvectorsView, SelectionView, ShapeView, SpecimensView  # noqa: E402

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
        expected = anisotropy.specimen_hext(row["s"], float(row["aniso_s_sigma"]), int(row["aniso_s_n_measurements"]))
        assert stats["hext"]["F"] == pytest.approx(expected["F"])
        assert "from this specimen's measurement scatter" in view.table.object
        text = code_text(view)
        assert "hext = aniso.specimen_hext(row['s'], row['aniso_s_sigma'], row['aniso_s_n_measurements'])" in text
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


# ----------------------------------------------------------------------------- the application
class TestApp:
    def test_the_body_has_the_side_column_and_a_tab_per_view(self, session):
        body = app.build_body(session)
        assert [key for key in body.views] == ["eigenvectors", "shape", "specimens"]
        assert isinstance(body.views["eigenvectors"], EigenvectorsView)
        assert isinstance(body.selection, SelectionView)
        template = app.create_app(EXAMPLE)
        assert template.session.n_specimens() == 19

    def test_a_directory_that_cannot_be_opened_gets_a_message(self, tmp_path):
        page = app.create_app(str(tmp_path))
        assert isinstance(page, pn.pane.Markdown) and "no specimens.txt" in page.object
