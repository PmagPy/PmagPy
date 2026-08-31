"""
Tests for the application layer: session state and persistence, the export
policy (never write into the source directory), publication figures and the
step logger's row model. Run with the demag-playground environment::

    pytest programs/pmagpy_directions/test_app.py -q
"""
import os
import shutil

import matplotlib
import numpy as np
import pandas as pd
import pytest

matplotlib.use("Agg")

import pmagpy.demag as dc  # noqa: E402
from pmagpy_directions import publication as pub  # noqa: E402
from pmagpy_directions.session import AUTOSAVE_NAME, Session  # noqa: E402
from pmagpy_directions.theme import ComponentColors, lighten  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DMAG_DIR = os.path.join(REPO, "data_files", "dmag_magic")


@pytest.fixture
def workdir(tmp_path):
    """A private copy of the example contribution plus a separate output directory."""
    src = tmp_path / "data"
    shutil.copytree(DMAG_DIR, src)
    for stray in src.glob("*.redo"):
        stray.unlink()
    out = tmp_path / "out"
    return str(src), str(out)


# --------------------------------------------------------------------------
class TestSession:
    def test_load_imports_and_autosaves(self, workdir):
        src, out = workdir
        s = Session(src, out)
        assert s.data is not None and len(s.data.components) > 100
        assert s.specimen == s.data.specimen_names[0]
        assert s.current is not None and s.current.specimen == s.specimen
        # editing writes the autosave into the output directory, not the data directory
        s.add_component("Z", 1, 5)
        assert os.path.exists(os.path.join(out, AUTOSAVE_NAME))
        assert not os.path.exists(os.path.join(src, AUTOSAVE_NAME))

    def test_autosave_is_restored_on_reload(self, workdir):
        src, out = workdir
        s = Session(src, out)
        s.specimen = "jm002a1"
        s.add_component("Z", 2, 7, "DE-BFP")
        s.toggle_current_quality()
        n_before = len(s.data.components)
        s2 = Session(src, out)
        assert "restored" in s2.status
        assert len(s2.data.components) == n_before
        z = [c for c in s2.data.components if c.specimen == "jm002a1" and c.name == "Z"][0]
        assert (z.imin, z.imax, z.fit_type, z.quality) == (2, 7, "DE-BFP", "b")
        assert s2.specimen == "jm002a1"          # the 'current_' specimen is remembered

    def test_colors_are_keyed_by_component_name(self, workdir):
        src, out = workdir
        s = Session(src, out)
        s.specimen = "jm002a1"
        s.add_component("HT", 1, 5)
        s.specimen = "jm002c1"
        s.add_component("HT", 1, 5)
        fits_a = dict((c.name, col) for c, r, col in s.fits("jm002a1"))
        fits_c = dict((c.name, col) for c, r, col in s.fits("jm002c1"))
        assert fits_a["HT"] == fits_c["HT"]
        assert fits_a["A"] != fits_a["HT"]

    def test_step_toggle_and_fit_cache(self, workdir):
        src, out = workdir
        s = Session(src, out)
        s.specimen = "jm002a1"
        comp = s.add_component("Z", 1, 10)
        n1 = s.data.fit(comp, dc.COORD_SPECIMEN).dir_n_measurements
        s.toggle_step(4)
        n2 = s.data.fit(comp, dc.COORD_SPECIMEN).dir_n_measurements
        assert n2 == n1 - 1
        s.toggle_step(4)
        assert s.data.fit(comp, dc.COORD_SPECIMEN).dir_n_measurements == n1

    def test_copy_current_to_site(self, workdir):
        src, out = workdir
        s = Session(src, out)
        s.specimen = "jm002a1"
        s.add_component("Q", 2, 9)
        targets = s.data.specimens_in("site", "jm002")
        n = s.copy_current_to(targets)
        assert n >= 1
        for name in targets:
            comps = [c for c in s.data.components_for(name) if c.name == "Q"]
            if comps:
                assert comps[0].fit_type == "DE-BFL"

    def test_export_writes_only_to_output_dir(self, workdir):
        src, out = workdir
        before = {f: os.path.getmtime(os.path.join(src, f)) for f in os.listdir(src)}
        s = Session(src, out)
        s.specimen = "jm002a1"
        s.toggle_step(3)
        written = s.export_tables(levels=("sample", "site"))
        names = {os.path.basename(p) for p in written}
        assert {"specimens.txt", "measurements.txt", "samples.txt", "sites.txt", "pmagpy_directions.redo"} <= names
        for p in written:
            assert os.path.dirname(os.path.realpath(p)) == os.path.realpath(out)
        after = {f: os.path.getmtime(os.path.join(src, f)) for f in os.listdir(src)}
        assert before == after                     # source contribution untouched
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", header=1)
        spec = s.data.specimens["jm002a1"]
        row = meas[(meas["specimen"] == "jm002a1") & (meas["measurement"].astype(str) == spec.steps.loc[3, "measurement"])]
        assert (row["quality"] == "b").all()
        specs = pd.read_csv(os.path.join(out, "specimens.txt"), sep="\t", header=1)
        assert set(specs["dir_tilt_correction"].dropna().unique()) >= {-1, 0, 100}
        # the written contribution reloads with the same interpretations
        for f in ("samples.txt", "sites.txt", "locations.txt"):
            if not os.path.exists(os.path.join(out, f)):
                shutil.copy(os.path.join(src, f), out)
        again = dc.DemagData.from_directory(out)
        assert again.load_components_from_specimens_table() == len(s.data.components)


# --------------------------------------------------------------------------
class TestPublication:
    @pytest.fixture(scope="class")
    def data(self):
        d = dc.DemagData.from_directory(DMAG_DIR)
        d.load_components_from_specimens_table()
        return d

    @pytest.mark.parametrize("layout", ["panel", "inset", "zijderveld"])
    @pytest.mark.parametrize("projection", ["ew", "ns", "nrm", "fit"])
    def test_specimen_figure_layouts(self, data, layout, projection, tmp_path):
        colors = ComponentColors()
        spec = data.specimens["jm002a1"]
        fits = [(c, data.fit(c, dc.COORD_GEOGRAPHIC), colors(c.name)) for c in data.components_for("jm002a1")]
        fig = pub.specimen_figure(spec, fits, coord=dc.COORD_GEOGRAPHIC, projection=projection, layout=layout)
        n_axes = {"panel": 3, "inset": 3, "zijderveld": 1}[layout]
        assert len(fig.axes) == n_axes
        path = pub.save_figure(fig, str(tmp_path / f"{layout}_{projection}.pdf"))
        assert os.path.getsize(path) > 1000

    def test_thermal_plane_specimen_and_formats(self, data, tmp_path):
        colors = ComponentColors()
        spec = data.specimens["jm002d1"]
        fits = [(c, data.fit(c, dc.COORD_SPECIMEN), colors(c.name)) for c in data.components_for("jm002d1")]
        assert any(r is not None and r.direction_type == "p" for _, r, _ in fits)
        fig = pub.specimen_figure(spec, fits, coord=dc.COORD_SPECIMEN)
        for fmt in ("png", "svg", "pdf"):
            assert os.path.exists(pub.save_figure(fig, str(tmp_path / "fig"), fmt=fmt))

    def test_directions_and_vgp_figures(self, data, tmp_path):
        means = data.mean_directions("site", dc.COORD_GEOGRAPHIC, component="A")
        row = means.iloc[0].to_dict()
        dirs = [(r.dir_dec, r.dir_inc, r.specimen, "#2a9d8f") for r in data.fit_all(dc.COORD_GEOGRAPHIC)
                if data.specimens[r.specimen].site == row["site"] and r.dir_comp == "A"]
        fig = pub.directions_figure(dirs, row, title="site")
        assert len(fig.axes) == 1
        pub.save_figure(fig, str(tmp_path / "site.png"))
        pole = data.mean_pole(dc.COORD_GEOGRAPHIC, component="A")
        fig = pub.vgp_figure([(v.vgp_lon, v.vgp_lat, v.site) for _, v in pole["vgps"].iterrows()], pole)
        pub.save_figure(fig, str(tmp_path / "pole.svg"))

    def test_division_rule(self):
        assert pub._nice_division(4.6e-6) == 1e-6
        assert pub._nice_division(5.9e-7) == 1e-7
        assert pub._nice_division(1.0e-6) == 1e-7


# --------------------------------------------------------------------------
class TestTheme:
    def test_component_colors_stable_and_distinct(self):
        colors = ComponentColors()
        first = [colors(n) for n in ("HT", "LT", "A", "B", "hem")]
        assert len(set(first)) == 5
        assert colors("HT") == first[0]
        colors.assign("HT", "#123456")
        assert colors("HT") == "#123456"

    def test_lighten(self):
        assert lighten("#000000", 1.0).lower() == "#ffffff"
        assert lighten("#2a9d8f", 0.0).lower() == "#2a9d8f"


# --------------------------------------------------------------------------
class TestLoggerRows:
    def test_logger_component_row_model(self, workdir):
        pytest.importorskip("panel")
        from pmagpy_directions.logger import StepLogger
        src, out = workdir
        logger = StepLogger()
        logger.rows = [dict(i=0, step="NRM", dec="1.0", inc="2.0", M="1e-6", csd="", q="g")]
        logger.highlight = {"imin": 0, "imax": 0, "color": "#2a9d8f"}
        received = []
        logger.param.watch(lambda e: received.append(e.new), "clicked")
        logger.clicked = {"row": 0, "button": "right", "n": 1}
        assert received and received[0]["button"] == "right"


class TestDataView:
    def test_native_chooser_loads_the_chosen_directory(self, workdir, tmp_path):
        pytest.importorskip("panel")
        import time
        from pmagpy_directions.views import DataView
        src, out = workdir
        s = Session(src, out)
        other = tmp_path / "other"
        shutil.copytree(DMAG_DIR, other)
        for stray in other.glob("*.redo"):
            stray.unlink()
        view = DataView(s, chooser=lambda start: str(other), chooser_available=True)
        assert not view.native_btn.disabled
        view._browse_native()
        for _ in range(100):                      # the chooser runs in a worker thread
            if s.directory == str(other) and view.path.value == str(other):
                break
            time.sleep(0.1)
        assert s.directory == str(other)
        assert view.path.value == str(other)

    def test_cancelled_chooser_keeps_the_session(self, workdir):
        pytest.importorskip("panel")
        import time
        from pmagpy_directions.views import DataView
        src, out = workdir
        s = Session(src, out)
        view = DataView(s, chooser=lambda start: None, chooser_available=True)
        view._browse_native()
        time.sleep(0.5)
        assert s.directory == src and "No folder chosen" in view.message.object

    def test_chooser_unavailable_disables_button(self, workdir):
        pytest.importorskip("panel")
        from pmagpy_directions.views import DataView
        src, out = workdir
        view = DataView(Session(src, out), chooser_available=False)
        assert view.native_btn.disabled

    def test_native_chooser_helper_never_raises(self, monkeypatch):
        from pmagpy_directions import session as sess
        monkeypatch.setattr(sess.sys if hasattr(sess, "sys") else __import__("sys"), "platform", "unknown-os")
        assert sess.native_choose_directory("/nonexistent") is None


class TestDatasetCache:
    def test_sessions_share_a_cached_dataset(self, workdir):
        src, out = workdir
        a = Session(src, out, cache=True)
        a.specimen = "jm002a1"
        a.add_component("Z", 1, 6)
        b = Session(src, out, cache=True)
        assert b.data is a.data                       # same object, interpretations included
        assert any(c.name == "Z" for c in b.data.components_for("jm002a1"))
        c = Session(src, out)                          # default: a fresh load
        assert c.data is not a.data


# --------------------------------------------------------------------------
# globe, overview figure, Poles and Export views
# --------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_DMAG = os.path.join(_HERE, "..", "..", "data_files", "dmag_magic")


@pytest.fixture(scope="module")
def study():
    data = dc.DemagData.from_directory(_DMAG)
    data.load_components_from_specimens_table()
    return data


class TestMapsAndOverview:
    def test_vgp_map_figure(self, study, tmp_path):
        pole = study.mean_pole(dc.COORD_GEOGRAPHIC, "A", "site")
        rows = [(v.vgp_lon, v.vgp_lat, v.site, bool(v.flipped)) for _, v in pole["vgps"].iterrows()]
        sites = [(lon, lat, name) for name, (lat, lon) in study.site_coords.items()]
        fig = pub.vgp_map_figure(rows, pole, sites, title="A VGPs")
        path = pub.save_figure(fig, str(tmp_path / "map.png"))
        assert os.path.getsize(path) > 10000
        ax = fig.axes[0]
        assert ax.get_aspect() == 1.0 and len(ax.patches) > 20        # land polygons were drawn
        fig = pub.vgp_map_figure(rows, None, (), centre=(0, -90))    # no pole, custom centre
        assert fig.axes

    def test_components_overview_figure(self, study):
        fig = pub.components_overview_figure(study, dc.COORD_GEOGRAPHIC, color_of=ComponentColors())
        assert len(fig.axes) == len(study.component_names())
        with pytest.raises(ValueError):
            pub.components_overview_figure(study, dc.COORD_GEOGRAPHIC, components=[])

    def test_directions_figure_places_text_in_empty_corners(self, study):
        dirs = [(300.0, 20.0, "s1", "#123456"), (310.0, 25.0, "s2", "#123456")]
        fig = pub.directions_figure(dirs, {"dir_dec": 305.0, "dir_inc": 22.0, "dir_alpha95": 4.0, "dir_k": 30.0,
                                           "dir_n_specimens": 2}, title="HT", caption="(geographic)")
        texts = [t.get_text() for t in fig.axes[0].texts]
        assert "HT" in texts and "(geographic)" in texts and any("Fisher mean" in t for t in texts)


class TestPolesView:
    def test_globe_follows_controls_and_click(self, tmp_path):
        from pmagpy_directions.views import PolesView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = PolesView(s)
        assert view.plot.fig.name == "pole_map"
        assert len(view.plot.land.data["xs"]) > 20
        assert "pole" in view.pole.object and len(view.table.value) > 2
        pole_centre = view.plot.centre
        view.centre.value = "north"
        assert view.plot.centre == (0.0, 90.0)
        view.centre.value = "sites"
        assert abs(view.plot.centre[1] - 71) < 5                   # Jan Mayen
        view.centre.value = "pole"
        assert view.plot.centre == pytest.approx(pole_centre)
        # click: the clicked point becomes the new centre and the controls switch to custom
        from types import SimpleNamespace
        before = view.plot.centre
        view.plot._on_tap(SimpleNamespace(x=0.5, y=0.0))          # 30° east of the centre on the equator line
        assert view.centre.value == "custom"
        assert view.plot.centre != before
        assert view.lon0.value == pytest.approx(view.plot.centre[0], abs=0.1)
        view.plot._on_tap(SimpleNamespace(x=0.0, y=0.0))          # the centre itself: nothing moves
        moved = view.plot.centre
        view.plot._on_tap(SimpleNamespace(x=1.5, y=0.0))          # off the globe: ignored
        assert view.plot.centre == moved
        # polarity unification off: reversed VGPs move to the far hemisphere
        view.unify.value = False
        assert view.plot.hidden >= 0 and "flip" in view.table.value.columns
        # flip polarity: the mean pole moves to its antipode and the export follows
        view.unify.value = True
        view.centre.value = "pole"
        before = s.data.mean_pole(s.active_coord, view.comp.value, "site")
        view.invert.value = True
        assert s.flip_polarity and "flipped" in view.pole.object
        assert view.plot.centre[1] == pytest.approx(-before["plat"])
        s.export_tables(levels=("location",), write_measurements=False)
        loc = pd.read_csv(tmp_path / "locations.txt", sep="\t", skiprows=1)
        row = loc[loc["pole_comp_name"] == view.comp.value].iloc[0]
        assert row["pole_lat"] == pytest.approx(round(-before["plat"], 1))


class TestExportView:
    def test_write_validate_and_figures(self, tmp_path):
        from pmagpy_directions.views import ExportView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = ExportView(s)
        view.analysts.value = "Tester"
        view._write()
        assert "Wrote:" in view.status.object
        for name in ("specimens.txt", "samples.txt", "sites.txt", "locations.txt", "measurements.txt", "pmagpy_directions.redo"):
            assert (tmp_path / name).exists(), name
        assert "specimens" in view.report.object and ("✓" in view.report.object or "✗" in view.report.object)
        spec = pd.read_csv(tmp_path / "specimens.txt", sep="\t", skiprows=1, dtype=str)
        mine = spec[spec["software_packages"].fillna("").str.contains(dc.APP_ID)]
        assert len(mine) and (mine["analysts"] == "Tester").all()
        assert not (tmp_path / Session.BACKUP_DIR).exists()      # output dir is not the data dir: no backup
        view._save_overview()
        assert f"directions_{dc.COORD_NAMES[s.data.default_coord()]}" in view.status.object
        view._save_vgp_maps()
        assert "vgps_A" in view.status.object

    def test_in_place_export_backs_up_originals(self, tmp_path):
        src = tmp_path / "data"
        shutil.copytree(_DMAG, src)
        s = Session(str(src), output_dir=str(src))
        s.export_tables(levels=("site",), write_measurements=False)
        backup = src / Session.BACKUP_DIR
        assert (backup / "specimens.txt").exists() and (backup / "sites.txt").exists()
        assert not (backup / "measurements.txt").exists()
        original = open(os.path.join(_DMAG, "sites.txt")).read()
        assert open(backup / "sites.txt").read() == original      # the copy is the untouched original
        s.export_tables(levels=("site",), write_measurements=False)   # a second export keeps the first backup
        assert open(backup / "sites.txt").read() == original


class TestColors:
    def test_picker_changes_every_view_and_persists(self, tmp_path):
        from pmagpy_directions.views import InterpretationsView, MeansView, SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        specimen, interps, means = SpecimenView(s), InterpretationsView(s), MeansView(s)
        name = s.data.component_names()[0]
        assert set(interps.pickers) == set(s.data.component_names())
        interps.pickers[name].value = "#123456"
        assert s.color_of(name) == "#123456"
        assert all(c.color == "#123456" for c in s.data.components if c.name == name)
        assert all(col == "#123456" for c, _, col in s.fits(s.specimen) if c.name == name)
        assert "#123456" in specimen._comp_colors or not [c for c in s.components() if c.name == name]
        # the auto-saved .redo carries the colour, so a fresh session restores it
        again = Session(_DMAG, output_dir=str(tmp_path))
        assert again.color_of(name) == "#123456"
        # a name that disappears loses its picker
        s.delete_components([c for c in s.data.components if c.name == name])
        assert name not in interps.pickers


class TestSwitchingDatasets:
    def test_views_follow_a_dataset_switch(self, tmp_path):
        from pmagpy_directions.views import InterpretationsView, MeansView, PolesView, SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path / "a"))
        views = [SpecimenView(s), InterpretationsView(s), MeansView(s), PolesView(s)]
        mcmurdo = os.path.join(_HERE, "..", "..", "data_files", "3_0", "McMurdo")
        assert s.load(mcmurdo, str(tmp_path / "b"))
        sel = views[0].specimen_sel
        assert len(sel.options) == len(s.data.specimens) == 1034
        assert sel.value == s.specimen and s.specimen in s.data.specimens
        assert views[0].logger.rows and views[0].logger.rows[0]["step"] in ("NRM", "0")
        assert len(views[2].name.options) > 100                     # site list of the new dataset
        assert "pole" in views[3].pole.object
        assert s.load(_DMAG, str(tmp_path / "a"))                  # and back
        assert len(sel.options) == 176 and sel.value == s.specimen
        assert s.coord == s.data.default_coord() == views[0].coord_sel.value


class TestMeansView:
    def test_means_per_component_and_coordinate_selector(self, tmp_path):
        from pmagpy_directions.views import MeansView, PolesView, SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        specimen, means, poles = SpecimenView(s), MeansView(s), PolesView(s)
        means.level.value, means.comp.value = "site", "all"
        # give the current site a second named component so that two means exist
        first = s.data.components_for(s.specimen)[0]
        s.add_component("B", first.imin, first.imax, "DE-FM")
        means.name.value = s.spec.site
        n_comps = len({c.name for c in s.data.components if s.data.specimens[c.specimen].site == means.name.value})
        assert len(means.plot.mean.data["x"]) == n_comps >= 2          # one star per component
        assert len(set(means.plot.mean.data["color"])) == n_comps       # in the component colours
        assert len(means.plot.a95.data["xs"]) >= 1
        # the coordinate selector drives the shared session coordinate and every tab follows
        means.coord.value = dc.COORD_GEOGRAPHIC
        assert s.coord == dc.COORD_GEOGRAPHIC and specimen.coord_sel.value == dc.COORD_GEOGRAPHIC
        assert poles.coord.value == dc.COORD_GEOGRAPHIC
        assert "geographic" in means.plot.fig.title.text
        poles.coord.value = dc.COORD_SPECIMEN
        assert s.coord == dc.COORD_SPECIMEN and means.coord.value == dc.COORD_SPECIMEN
        assert "pole" in poles.pole.object or "fewer" in poles.pole.object
        # the PDF carries every component's mean too
        fig = pub.directions_figure([(10, 20, "a", "#123456")], means=[({"dir_dec": 10, "dir_inc": 20, "dir_alpha95": 5,
                                                                        "dir_k": 30, "dir_n_specimens": 3, "dir_comp_name": "A"}, "#123456"),
                                                                       ({"dir_dec": 200, "dir_inc": -20, "dir_alpha95": 4,
                                                                        "dir_k": 40, "dir_n_specimens": 4, "dir_comp_name": "B"}, "#654321")])
        texts = [t.get_text() for t in fig.axes[0].texts]
        assert any(t.startswith("A:") for t in texts) and any(t.startswith("B:") for t in texts)
