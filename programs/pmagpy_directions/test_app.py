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
from pmagpy_panel.theme import ComponentColors, lighten  # noqa: E402

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
        import asyncio
        from pmagpy_directions.views import DataView
        src, out = workdir
        s = Session(src, out)
        other = tmp_path / "other"
        shutil.copytree(DMAG_DIR, other)
        for stray in other.glob("*.redo"):
            stray.unlink()
        view = DataView(s, chooser=lambda start: str(other), chooser_available=True)
        assert not view.native_btn.disabled
        asyncio.run(view._browse_native())      # the dialog is a coroutine; the server keeps serving meanwhile
        assert s.directory == str(other)
        assert view.path.value == str(other)

    def test_cancelled_chooser_keeps_the_session(self, workdir):
        pytest.importorskip("panel")
        import asyncio
        from pmagpy_directions.views import DataView
        src, out = workdir
        s = Session(src, out)
        view = DataView(s, chooser=lambda start: None, chooser_available=True)
        asyncio.run(view._browse_native())
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
        # the flip shows in the pole itself and in the control, not in a label saying so
        assert s.flip_polarity and f'{-before["plat"]:.1f}°N' in view.pole.object
        assert "polarity" not in view.pole.object
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

    def test_criteria_are_opt_in_and_reach_the_written_tables(self, tmp_path):
        from pmagpy_directions.views import ExportView
        from pmagpy.magic_project import magic_write
        src = tmp_path / "data"
        shutil.copytree(_DMAG, src)
        out = tmp_path / "out"
        s = Session(str(src), output_dir=str(out))
        view = ExportView(s)
        assert view.criteria.disabled and s.criteria_count() == 0 and "no <code>criteria.txt" in view.criteria_note.object
        magic_write(str(src / "criteria.txt"), pd.DataFrame([
            {"criterion": "DE-SPEC", "table_column": "specimens.dir_mad_free", "criterion_operation": "<=",
             "criterion_value": "2.0", "citations": "This study"},
            {"criterion": "IE-SPEC", "table_column": "specimens.int_b_beta", "criterion_operation": "<=",
             "criterion_value": "0.1", "citations": "This study"}]), "criteria")
        assert s.load(str(src), str(out))
        assert s.criteria_count() == 1 and not view.criteria.disabled and "1 directional" in view.criteria.name
        assert not s.apply_criteria and "not applied" in view.criteria_note.object
        version = s.version
        s.apply_criteria = True                                    # the checkbox is bound to this
        assert s.version == version + 1 and s.data.criteria is not None
        failing = s.data.failing_components()
        assert len(failing) > 20 and f"{len(failing)} fits fail DE-SPEC" in view.criteria_note.object
        view._write()
        spec = pd.read_csv(out / "specimens.txt", sep="\t", skiprows=1, dtype=str)
        mine = spec[spec["software_packages"].fillna("").str.contains(dc.APP_ID)]
        bad = mine[mine["result_quality"] == "b"]
        assert set(zip(bad["specimen"], bad["dir_comp"])) == failing
        sites = pd.read_csv(out / "sites.txt", sep="\t", skiprows=1, dtype=str)
        written = sites[sites["software_packages"].fillna("").str.contains(dc.APP_ID)]
        coords = s.default_mean_coords()
        with_criteria = sum(s.data.mean_directions("site", c)["dir_n_specimens"].sum() for c in coords)
        without = sum(s.data.mean_directions("site", c, include_bad=True)["dir_n_specimens"].sum() for c in coords)
        assert written["dir_n_specimens"].astype(float).sum() == with_criteria < without
        s.apply_criteria = False                                   # off again: nothing is flagged
        assert s.data.criteria is None and s.data.failing_components() == set()
        assert (s.data.specimens_table(coords=(dc.COORD_GEOGRAPHIC,))["result_quality"] == "g").all()

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
        assert "#123456" in specimen._comp_look[0] or not [c for c in s.components() if c.name == name]
        # the auto-saved .redo carries the colour, so a fresh session restores it
        again = Session(_DMAG, output_dir=str(tmp_path))
        assert again.color_of(name) == "#123456"
        # a name that disappears loses its picker
        s.delete_components([c for c in s.data.components if c.name == name])
        assert name not in interps.pickers


class TestApp:
    def test_template_assembles_with_its_own_assets(self, tmp_path):
        """The whole application builds, logo included.

        The pieces were all covered and the assembly was not, so when the theme
        moved to pmagpy_panel and took the logo's path with it, only the browser
        suite noticed. Assets belong to an application, not to the toolkit.
        """
        from pmagpy_directions.app import create_app
        template = create_app(_DMAG, output_dir=str(tmp_path))
        assert template.title == "PmagPy Directions"
        assert template.logo.startswith("data:image/png;base64,")
        assert template.session.data is not None


class TestSpecimenView:
    def test_tiled_panels_fit_their_figures_and_remember_the_layout(self, tmp_path):
        """The panels tile the canvas; each figure is fitted to its panel, in one batch, and
        a rearrangement (a drop, a divider, the height) is kept for the next session."""
        from pmagpy_directions.plots import DecayPlot, ZijderveldPlot
        from pmagpy_directions.views import SpecimenView, LAYOUT_FILE
        from pmagpy_panel.widgets import LayoutHold, TileCanvas
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        canvas = view.canvas
        assert canvas.tree == SpecimenView.DEFAULT_TREE and canvas.height == SpecimenView.HEIGHT
        assert canvas.rects == []                          # nothing to place until the browser gives a width

        canvas.width_px = 1000
        rects = dict(zip(canvas.titles, canvas.rects))
        zij = rects[view.ZIJ]
        assert (zij["x"], zij["y"], zij["h"]) == (0, 0, SpecimenView.HEIGHT) and zij["w"] == 496
        bw, bh = canvas.sizes[view.ZIJ]
        assert view.zij.fig.frame_width == bw - 18                       # the frame takes the panel's shape
        assert view.zij.fig.frame_height == bh - ZijderveldPlot.CHROME - 4
        assert view.zij.lbl_right.x == bw - 24 and view.zij.lbl_top.y == view.zij.fig.frame_height - 6
        assert view.zij.legend.orientation == "horizontal"
        ew, eh = canvas.sizes[view.EQ]
        assert view.eq.fig.width == view.eq.fig.height == min(ew, eh) - 6
        dw, dh = canvas.sizes[view.DECAY]
        assert view.decay.fig.width == dw - 6
        assert view.decay.fig.frame_height == dh - DecayPlot.TOP - DecayPlot.AXIS_ROWS - 6
        hold = LayoutHold.of_session()
        assert hold.begin == hold.end >= 1

        # the M/M₀ panel dropped on the diagram's lower edge: under it, full width of the old half
        canvas.drop = {"src": view.DECAY, "dst": view.ZIJ, "zone": "bottom", "n": 1}
        rects = dict(zip(canvas.titles, canvas.rects))
        assert rects[view.DECAY]["y"] > rects[view.ZIJ]["y"] and rects[view.DECAY]["x"] == 0
        assert rects[view.EQ]["h"] == SpecimenView.HEIGHT                 # its sibling took its place
        assert all(r["y"] + r["h"] <= SpecimenView.HEIGHT for r in rects.values())   # nothing below the canvas
        assert view.decay.fig.width == canvas.sizes[view.DECAY][0] - 6
        # a divider moved
        canvas.split = {"path": [], "ratio": 0.6, "n": 2}
        assert abs(canvas.tree[1] - 0.6) < 1e-9
        canvas.drop = {"src": view.ZIJ, "dst": view.EQ, "zone": "left", "n": 3}     # a narrow diagram: room is made for it
        bw, bh = canvas.sizes[view.ZIJ]
        assert view.zij.legend.orientation == "vertical" and view.zij.fig.width <= bw
        assert view.zij.fig.height <= bh
        # the height handle
        view.plot_size.value = 700
        assert canvas.height == 700 and max(r["y"] + r["h"] for r in canvas.rects) == 700
        kept = canvas.tree
        again = SpecimenView(s)
        assert again.canvas.tree == kept and again.canvas.height == 700
        view._reset_layout()
        assert canvas.tree == SpecimenView.DEFAULT_TREE and canvas.height == SpecimenView.HEIGHT
        assert SpecimenView(s).canvas.tree == SpecimenView.DEFAULT_TREE
        os.remove(LAYOUT_FILE)

    def test_the_level_card_shows_the_specimens_group(self, tmp_path):
        """The hierarchical card plots the good fits of the current specimen's site, its means, and rings the current fit."""
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        card = view.levels
        site = s.spec.site
        n_fits = sum(1 for sp in s.data.specimens_in("site", site) for c in s.data.components_for(sp)
                     if c.quality == "g" and c.fit_type != "DE-BFP")
        assert len(card.plot.src.data["x"]) == n_fits
        assert site in card.plot.fig.title.text
        assert len(card.plot.mean.data["x"]) >= 1 and "α95" in card.stats.object
        assert len(card.plot.mark_src.data["x"]) == (1 if s.current is not None and s.current.fit_type != "DE-BFP" else 0)
        card.stat.value = "bingham"
        assert "η / ζ" in card.stats.object
        card.level.value = "sample"
        assert s.spec.sample in card.plot.fig.title.text

    def test_the_colour_picker_recolours_every_fit_of_the_name(self, tmp_path):
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        name = s.current.name
        assert view.color_pick.value == s.color_of(name) and not view.color_pick.disabled
        view.color_pick.value = "#123456"
        assert s.color_of(name) == "#123456"
        assert all(c.color == "#123456" for c in s.data.components if c.name == name)
        assert view.zij.fits.data["color"][0] == "#123456"

    def test_fit_arrows_point_along_the_fitted_direction(self, tmp_path):
        """The arrowhead sits at the end the fitted direction points to (first minus last step),
        whichever end is nearer the origin -- in both projections."""
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        checked = 0
        for spec_name in s.data.specimen_names[:40]:
            s.specimen = spec_name
            coord = s.active_coord
            heads = view.zij.heads.data
            k = 0
            for comp, res, _ in s.fits():
                seg = dc.fit_line_segment(res, s.spec, coord, rotation_dec=s.rotation()) if res is not None else None
                if seg is None:
                    continue
                for ycol in ("y_h", "y_v"):
                    assert heads["x"][k] == seg["x"][1] and heads["y"][k] == seg[ycol][1]
                    k += 1
                cart = dc.cartesian(s.spec.steps, coord)
                direction = np.asarray(dc.pmag.dir2cart([res.dir_dec, res.dir_inc, 1.0])).ravel()
                assert (cart[res.imin] - cart[res.imax]) @ direction > 0       # domean's orientation
                checked += 1
        assert checked > 10

    def test_upward_fit_directions_are_hollow_stars(self, tmp_path):
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        seen = set()
        for spec_name in s.data.specimen_names:
            s.specimen = spec_name
            d = view.eq.dirs.data
            for inc, fill, line, name in zip(d["inc"], d["fill"], d["line"], d["name"]):
                color = s.color_of(name)
                if inc < 0:
                    assert fill == "white" and line == color
                    seen.add("up")
                else:
                    assert fill == color
                    seen.add("down")
            if seen == {"up", "down"}:
                break
        assert "down" in seen

    def test_only_the_selected_fit_row_is_coloured_and_bold(self, tmp_path):
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        s.add_component("B", 0, 3)                     # a second fit beside the specimen's own
        comps = s.components()
        assert len(comps) >= 2
        for chosen in (0, 1):
            s.current = comps[chosen]
            styles = view.comp_table._get_style_data()["data"]
            for row, cells in styles.items():
                css = dict(cells[2])
                if row == chosen:
                    assert css["font-weight"] == "700" and css["background"] != "#ffffff"
                else:
                    assert css["font-weight"] == "400" and css["background"] == "#ffffff"

    def test_a_bad_step_is_faded_and_left_out_of_the_path(self, tmp_path):
        """Flagging a step bad fades its symbol on the net and the M/M₀ strip and breaks the connecting line there."""
        from pmagpy_directions.plots import BAD_ALPHA
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        n = s.spec.n_steps
        assert list(view.eq.src.data["alpha"]) == [1.0] * n and len(view.eq.path.data["x"]) == n
        assert list(view.decay.src.data["alpha"]) == [1.0] * n and len(view.decay.path.data["x"]) == n

        s.toggle_step(4)
        assert s.spec.steps["quality"].iloc[4] == "b"
        for plot in (view.eq, view.decay):
            alpha = list(plot.src.data["alpha"])
            assert alpha[4] == BAD_ALPHA and alpha.count(1.0) == n - 1
            assert len(plot.src.data["x"]) == n                    # the symbol itself is still drawn
            assert len(plot.path.data["x"]) == n - 1               # the line skips it
        assert list(view.decay.path.data["x"]) == [x for i, x in enumerate(view.decay.src.data["x"]) if i != 4]

        s.toggle_step(4)
        assert list(view.eq.src.data["alpha"]) == [1.0] * n and len(view.decay.path.data["x"]) == n

    def test_new_fit_creates_and_selects_a_fit_at_once(self, tmp_path):
        """New fit makes a fit immediately (after the last one, or over all steps); clicks then move its bounds."""
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        n = s.spec.n_steps
        s.delete_components(s.components())
        assert s.current is None

        view._new_fit()
        first = s.current
        assert first is not None and (first.imin, first.imax) == (0, n - 1)
        assert first.fit_type == view.fit_type_sel.value
        assert first.name in view.comp_table.value["fit"].tolist()
        assert "tap a point" in s.status

        # the next plot taps shape the new fit rather than starting another one
        view._pick(3)
        assert (first.imin, first.imax) == (3, n - 1) and len(s.components()) == 1
        view._pick(n - 3)
        assert (first.imin, first.imax) == (3, n - 3)

        # a second new fit starts where the last one ends, and gets the next letter
        view._new_fit()
        second = s.current
        assert second is not first and (second.imin, second.imax) == (n - 3, n - 1)
        assert [c.name for c in s.components()] == [first.name, second.name] == ["A", "B"]

        # nothing left above the last fit: the new one spans everything again
        view._new_fit()
        assert (s.current.imin, s.current.imax) == (0, n - 1)

    def test_clicking_a_step_selects_it_and_arrows_move_the_selection(self, tmp_path):
        """A left click in the logger selects a step (no bound moves); it is ringed on all three plots."""
        from pmagpy_directions.views import SpecimenView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = SpecimenView(s)
        n = s.spec.n_steps
        cur = s.current
        bounds = (cur.imin, cur.imax)
        assert view.step is None and view.logger.selected == -1
        for plot in (view.zij, view.eq, view.decay):
            assert plot.mark_src.data["x"] == []

        view.logger.clicked = {"row": 5, "button": "left", "n": 1}
        assert view.step == 5 and view.logger.selected == 5
        assert (cur.imin, cur.imax) == bounds                        # the fit is untouched
        # the ring sits on the step: on the Zijderveld in both projections
        zx, zy = view.zij.mark_src.data["x"], view.zij.mark_src.data["y"]
        assert zx == [view.zij._xy[0][5]] * 2 and zy == [view.zij._xy[1][5], view.zij._xy[2][5]]
        assert view.eq.mark_src.data["x"] == [view.eq.src.data["x"][5]]
        assert view.decay.mark_src.data["x"] == [view.decay.src.data["x"][5]]

        # ↑ ↓ move it, clamped to the table
        view.hotkeys.key = "ArrowDown"; view.hotkeys.n += 1
        assert view.step == 6
        view.hotkeys.key = "ArrowUp"; view.hotkeys.n += 1
        view.hotkeys.key = "ArrowUp"; view.hotkeys.n += 1
        assert view.step == 4
        view.select_step(n - 1)
        view.hotkeys.key = "ArrowDown"; view.hotkeys.n += 1
        assert view.step == n - 1
        assert view.decay.mark_src.data["x"] == [view.decay.src.data["x"][n - 1]]

        # the ring follows a redraw (a coordinate change moves the points)
        s.coord = dc.COORD_GEOGRAPHIC
        assert view.eq.mark_src.data["x"] == [view.eq.src.data["x"][n - 1]]

        # clicking the selected step again clears the selection; a right click still flags
        view.logger.clicked = {"row": n - 1, "button": "left", "n": 2}
        assert view.step is None and view.eq.mark_src.data["x"] == []
        view.logger.clicked = {"row": 2, "button": "right", "n": 3}
        assert s.spec.steps["quality"].iloc[2] == "b" and view.step is None
        s.toggle_step(2)

        # from nothing, ↓ starts at the first step; a new specimen clears the selection
        view.hotkeys.key = "ArrowDown"; view.hotkeys.n += 1
        assert view.step == 0
        s.step_specimen(+1)
        assert view.step is None and view.logger.selected == -1
        for plot in (view.zij, view.eq, view.decay):
            assert plot.mark_src.data["x"] == []


class TestInterpretationsView:
    def test_side_plot_follows_the_table(self, tmp_path):
        """The Fits side column plots the ticked rows, or everything the filters leave listed."""
        from pmagpy_directions.views import InterpretationsView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = InterpretationsView(s)
        good = [c for c in s.data.components if c.quality == "g"]

        # nothing ticked: every listed (unfiltered) fit is on the net
        plotted = len(view.plot.src.data["x"]) + len(view.plot.circles.data["xs"])
        assert plotted == len(good) and "listed" in view.plot_note.object
        assert view.plot.fig.name == "equal_area_net"

        # ticking rows narrows the plot to those fits
        rows = [i for i, c in enumerate(s.data.components) if c.quality == "g"][:3]
        view.table.selection = rows
        assert len(view.plot.src.data["x"]) + len(view.plot.circles.data["xs"]) == len(rows)
        assert "ticked in the table" in view.plot_note.object
        specs = set(view.plot.src.data["label"])
        assert specs <= {s.data.components[i].specimen for i in rows}

        # a header filter narrows it as well, once the ticks are cleared
        view.table.selection = []
        one = s.data.components[rows[0]].specimen
        view.table.filters = [{"field": "specimen", "type": "=", "value": one}]
        listed = len(view.plot.src.data["x"]) + len(view.plot.circles.data["xs"])
        assert 0 < listed < len(good)
        assert set(view.plot.src.data["label"]) <= {one}

        # planes are drawn as great circles, flagged fits are left out and reported
        view.table.filters = []
        flagged = next(c for c in s.data.components if c.quality == "g")
        flagged.quality = "b"
        s._changed()
        assert len(view.plot.src.data["x"]) + len(view.plot.circles.data["xs"]) == len(good) - 1
        assert "1 flagged bad" in view.plot_note.object


    def test_clicking_a_row_draws_that_fit_on_the_orthogonal_plot(self, tmp_path):
        """The Fits tab's Zijderveld diagram shows the clicked fit's specimen, its bounds ringed."""
        from types import SimpleNamespace
        from pmagpy_directions.views import InterpretationsView
        s = Session(_DMAG, output_dir=str(tmp_path))
        view = InterpretationsView(s)
        assert view.focus is s.current                     # at first, the Specimen tab's fit
        i, comp = next((i, c) for i, c in enumerate(s.data.components)
                       if c.specimen != s.specimen and c.fit_type == "DE-BFL")
        view._on_row_click(SimpleNamespace(row=i))
        assert view.focus is comp and comp.specimen in view.zij_caption.object
        n = s.data.specimens[comp.specimen].n_steps
        good = (s.data.specimens[comp.specimen].steps["quality"] == "g").sum()
        assert len(view.zij.src.data["x"]) == good and len(view.zij.bad.data["x"]) == n - good
        assert len(view.zij.bounds.data["x"]) == 4           # first and last step, both projections

    def test_batch_edit_and_add(self, tmp_path):
        """Apply a name, type and bounds to the ticked fits; add a fit to the ticked specimens."""
        s = Session(_DMAG, output_dir=str(tmp_path))
        steps = s.treatment_steps()
        lines = [c for c in s.data.components if c.fit_type == "DE-BFL"][:4]
        own = list(s.data.specimens[lines[0].specimen].steps["label"])       # one specimen's treatments
        lo, hi = steps[own[1]], steps[own[-2]]
        n, skipped = s.edit_components(lines, fit_type="DE-BFL-A", lower=lo, upper=hi)
        assert n + len(skipped) == len(lines) and n >= 1
        for c in lines:
            if c.fit_type == "DE-BFL-A":
                spec = s.data.specimens[c.specimen]
                assert c.imin == s.data.step_index_for_value(c.specimen, *lo)
                assert c.imax == s.data.step_index_for_value(c.specimen, *hi) and c.imax < spec.n_steps
        # a rename to a name the specimen already uses is refused for that fit
        b = s.data.add_component(lines[0].specimen, "B", 0, 2)
        n, skipped = s.edit_components([lines[0]], name="b")
        assert n == 0 and "already has a fit named B" in skipped[0]
        # a thermal bound means nothing to an AF specimen: skipped, not snapped to some step
        units = {sp: set(s.data.specimens[sp].steps["treat_unit"]) for sp in s.data.specimen_names}
        other = next((c for c in s.data.components if c.fit_type == "DE-BFL"
                      and lo[1] not in units[c.specimen]), None)
        if other is not None:
            n, skipped = s.edit_components([other], lower=lo)
            assert n == 0 and "no step of that treatment" in skipped[0]
        # adding: one fit per specimen, named and coloured as the study's own
        targets = [c.specimen for c in lines]
        before = len(s.data.components)
        n, _ = s.add_fit_to(targets + targets[:1], " b ", "DE-BFL")
        assert n == len(set(targets))                                         # once per specimen
        added = [c for c in s.data.components if c.name == "B"]
        assert {c.specimen for c in added} == set(targets)                   # "b" is the study's "B"
        assert all(c.color == s.color_of("B") for c in added)

    def test_a_typed_name_takes_the_studys_spelling_and_colour(self, tmp_path):
        s = Session(_DMAG, output_dir=str(tmp_path))
        first, second = s.data.specimen_names[:2]
        s.data.add_component(first, "mt", 0, 2)
        assert s.known_name(" M T ") == "mt" and s.known_name("brand-new") == "brand-new"
        s.specimen = second
        comp = s.add_component("zz-tmp", 0, 2)
        assert s.rename_component(comp, "MT")
        assert comp.name == "mt" and comp.color == s.color_of("mt")
        assert "coloured as the 1 other mt fit" in s.status


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

    def test_planes_show_the_vector_the_mean_is_formed_from(self, tmp_path):
        """A great circle on the net carries the point its direction resolves to."""
        import numpy as np
        import pmagpy.pmag as pmag
        from pmagpy_directions.views import MeansView
        mcmurdo = os.path.join(_HERE, "..", "..", "data_files", "3_0", "McMurdo")
        s = Session(mcmurdo, output_dir=str(tmp_path))
        means = MeansView(s)
        means.level.value, means.comp.value = "site", "all"
        means.name.value = "mc01"                       # two plane fits among its eight
        dirs, planes, _means, lines, plane_rows, vectors = means._collect()
        assert len(planes) == 2 and len(vectors) == len(planes)
        assert len(means.plot.vectors.data["x"]) == len(planes)

        # the planes are listed apart from the lines, under their own headings, so a
        # pole to a plane is never read as a direction
        assert len(plane_rows) == 2 and means.planes_box.visible
        assert not any(r["fit"] == "" for r in lines)
        assert set(plane_rows[0]) >= {"pole dec", "pole inc", "bfv dec", "bfv inc"}
        assert "dec" not in plane_rows[0] and "pole dec" not in lines[0]
        assert all(r["bfv dec"] != "–" for r in plane_rows)

        cart = lambda d, i: np.asarray(pmag.dir2cart([d, i, 1.0]), dtype=float).ravel()  # noqa: E731
        for (pdec, pinc, _c), (vdec, vinc, spec, comp, _col) in zip(planes, vectors):
            # the vector lies on that plane's great circle: perpendicular to its pole
            assert float(np.dot(cart(pdec, pinc), cart(vdec, vinc))) == pytest.approx(0, abs=1e-9)
            assert spec.startswith("mc01") and comp == "A"
        # and it is the direction the export writes for that specimen
        stored = s.data.best_fit_vectors(s.active_coord)
        for vdec, vinc, spec, comp, _col in vectors:
            assert stored[(spec, comp)] == pytest.approx((vdec, vinc), abs=0.01)

    def test_selected_fit_is_ringed_on_the_net_and_arrows_move_it(self, tmp_path):
        """Selecting a row (or ↑ ↓) singles out that fit on the net: a ring, or a heavy great circle for a plane."""
        from pmagpy_directions.views import MeansView, SpecimenView
        mcmurdo = os.path.join(_HERE, "..", "..", "data_files", "3_0", "McMurdo")
        s = Session(mcmurdo, output_dir=str(tmp_path))
        specimen, means = SpecimenView(s), MeansView(s)
        means.level.value, means.comp.value = "site", "all"
        means.name.value = "mc01"
        assert means.plot.mark_src.data["x"] == [] and means.plot.mark_circle_src.data["xs"] == []
        n_lines, n_planes = len(means._records), len(means._plane_records)
        assert n_lines >= 2 and n_planes == 2

        means.table.selection = [1]
        rec = means._records[1]
        x, y = dc.equal_area_xy([rec["_dec"]], [rec["_inc"]])
        assert means.plot.mark_src.data == {"x": [float(x[0])], "y": [float(y[0])]}
        assert means.plot.mark_circle_src.data["xs"] == []

        # ↑ ↓ reach the Means view only while its tab shows (the app routes them)
        specimen.arrow_target = means
        for _ in range(n_lines - 2):                                    # from row 1 to the last line
            specimen.hotkeys.key = "ArrowDown"; specimen.hotkeys.n += 1
        assert means.table.selection == [n_lines - 1] and means.plane_table.selection == []
        specimen.hotkeys.key = "ArrowDown"; specimen.hotkeys.n += 1      # ... on into the planes table
        assert means.table.selection == [] and means.plane_table.selection == [0]
        assert means.plot.mark_src.data["x"] == [] and len(means.plot.mark_circle_src.data["xs"]) == 1
        pdec, pinc = means._plane_records[0]["_dec"], means._plane_records[0]["_inc"]
        gx, _gy = dc.great_circle_xy(pdec, pinc)
        assert means.plot.mark_circle_src.data["xs"][0] == list(gx)
        specimen.hotkeys.key = "ArrowDown"; specimen.hotkeys.n += 1
        specimen.hotkeys.key = "ArrowDown"; specimen.hotkeys.n += 1      # clamped at the last plane
        assert means.plane_table.selection == [n_planes - 1]
        specimen.hotkeys.key = "ArrowUp"; specimen.hotkeys.n += 1
        specimen.hotkeys.key = "ArrowUp"; specimen.hotkeys.n += 1
        assert means.table.selection == [n_lines - 1] and means.plot.mark_circle_src.data["xs"] == []

        # a fit flagged bad is not plotted, so nothing is ringed for it
        means.table.selection = [0]
        means._flag()
        assert means._records[0]["q"] == "b" and means.plot.mark_src.data["x"] == []
        means._flag()
        assert means.plot.mark_src.data["x"] != []

    def test_statistic_selector_switches_what_is_averaged(self, tmp_path):
        """Fisher of the whole set, a mean per polarity mode, or the axial Bingham mean."""
        from pmagpy_directions.views import MeansView
        s = Session(_DMAG, output_dir=str(tmp_path))
        means = MeansView(s)
        means.level.value, means.comp.value = "location", "all"
        means.name.value = means.name.options[0]
        fisher_stars = len(means.plot.mean.data["x"])
        assert fisher_stars >= 1 and "component" in means.stats.object.columns

        means.stat.value = "polarity"
        table = means.stats.object
        assert "mode" in table.columns and "polarity" not in table.columns
        assert len(means.plot.mean.data["x"]) == len(table)     # a star per mode
        assert (table["n_spec"] > 0).all()

        means.stat.value = "bingham"
        table = means.stats.object
        assert {"eta", "zeta"} <= set(table.columns) and "α95" not in table.columns
        assert len(means.plot.mean.data["x"]) == len(table)
        assert len(means.plot.a95.data["xs"]) == 0              # an ellipse is not an α95 circle
        # the figure names the statistic rather than always saying Fisher
        assert "Bingham" in means.STAT_LABELS[means.stat.value]
        means.download.callback()                               # the PDF still builds

        means.stat.value = "fisher"
        assert len(means.plot.mean.data["x"]) == fisher_stars


class TestAutosaveDebounce:
    """Every edit used to rewrite the whole .redo; edits now coalesce into one write."""

    class FakeDoc:
        """Enough of a Bokeh document: timeout callbacks that a test fires by hand."""
        session_context = object()

        def __init__(self):
            self.pending = {}
            self.n = 0

        def add_timeout_callback(self, fn, ms):
            self.n += 1
            self.pending[self.n] = (fn, ms)
            return self.n

        def remove_timeout_callback(self, handle):
            if handle not in self.pending:
                raise ValueError(handle)
            del self.pending[handle]

        def fire(self):
            for fn, _ in list(self.pending.values()):
                fn()
            self.pending.clear()

    def test_outside_a_session_the_autosave_is_immediate(self, workdir):
        src, out = workdir
        s = Session(src, out)
        s.add_component("Z", 1, 5)
        assert os.path.exists(os.path.join(out, AUTOSAVE_NAME))

    def test_inside_a_session_edits_coalesce_into_one_write(self, workdir, monkeypatch):
        from pmagpy_directions import session as sess
        src, out = workdir
        s = Session(src, out)
        doc = self.FakeDoc()
        monkeypatch.setattr(sess, "_server_document", lambda: doc)
        writes = []
        real = s.data.save_components
        monkeypatch.setattr(s.data, "save_components", lambda path, **kw: writes.append(path) or real(path, **kw))
        cur = s.current
        for _ in range(5):
            s.update_component(cur, imin=cur.imin + 1)
        assert writes == [] and len(doc.pending) == 1                 # five edits, one pending write
        _, ms = next(iter(doc.pending.values()))
        assert ms == int(sess.AUTOSAVE_DELAY * 1000)
        doc.fire()
        assert writes == [s.autosave_path] and s._autosave_pending is None
        # a dataset switch flushes what is pending before the output directory moves on
        s.update_component(cur, imax=cur.imax - 1)
        assert len(doc.pending) == 1
        s.load(src, out)
        assert len(writes) == 2 and not doc.pending
        # so does an export (the reload made a new dataset object: patch its writer too)
        real = s.data.save_components
        monkeypatch.setattr(s.data, "save_components", lambda path, **kw: writes.append(path) or real(path, **kw))
        cur = s.current
        s.update_component(cur, imax=cur.imax + 1)
        assert len(doc.pending) == 1
        s.export_tables(coords=(dc.COORD_SPECIMEN,), levels=(), write_measurements=False)
        assert writes[2] == s.autosave_path and len(writes) == 3      # the flush (the export's .redo is a separate file)
        assert os.path.exists(os.path.join(out, sess.REDO_NAME))
        assert s._autosave_pending is None and not doc.pending


class TestLazyFirstDraw:
    def test_views_built_for_hidden_tabs_draw_nothing_until_shown(self, tmp_path):
        pytest.importorskip("panel")
        from pmagpy_directions.views import InterpretationsView, MeansView, PolesView
        s = Session(_DMAG, output_dir=str(tmp_path))
        means, poles, fits = MeansView(s, active=False), PolesView(s, active=False), InterpretationsView(s, active=False)
        assert len(means.table.value) == 0 and len(poles.table.value) == 0 and len(fits.table.value) == 0
        assert means._dirty and poles._dirty and fits._dirty
        means.set_active(True)
        poles.set_active(True)
        fits.set_active(True)
        assert len(fits.table.value) == len(s.data.components) > 0
        assert len(means.table.value) > 0 and not means._dirty
        # the default is still to draw at once
        assert len(MeansView(s).table.value) > 0

    def test_a_single_group_mean_equals_its_row_in_the_full_table(self, tmp_path):
        s = Session(_DMAG, output_dir=str(tmp_path))
        full = s.data.mean_directions("site", dc.COORD_GEOGRAPHIC)
        site = full["site"].iloc[0]
        one = s.data.mean_directions("site", dc.COORD_GEOGRAPHIC, group=site)
        assert list(one["site"]) == [site] * len(one)
        pd.testing.assert_frame_equal(one.reset_index(drop=True), full[full["site"] == site].reset_index(drop=True))
        # at the location level the polarity axis is the whole study's, so the row is the same too
        full = s.data.mean_directions("location", dc.COORD_GEOGRAPHIC)
        loc = full["location"].iloc[0]
        one = s.data.mean_directions("location", dc.COORD_GEOGRAPHIC, group=loc)
        pd.testing.assert_frame_equal(one.reset_index(drop=True), full[full["location"] == loc].reset_index(drop=True))
        assert len(s.data.mean_directions("site", dc.COORD_GEOGRAPHIC, group="no-such-site")) == 0


class TestFrozenBuild:
    def test_the_code_stamp_survives_a_missing_source_directory(self, monkeypatch):
        from pmagpy_directions import session as sess
        monkeypatch.setattr(sess.os.path, "isdir", lambda p: False)
        assert sess._code_stamp() >= 0.0                                # the core files still date it
        monkeypatch.setattr(sess.os.path, "exists", lambda p: False)
        assert sess._code_stamp() == 0.0                                # nothing on disk at all: no crash


class TestServeDefault:
    def test_the_default_dataset_is_the_shipped_example_wherever_it_lives(self, monkeypatch, tmp_path):
        """The packaged build flattens programs/ away, so the example must not be found relative to this file."""
        pytest.importorskip("panel")
        from pmagpy_panel import datasets
        from pmagpy_directions import app
        monkeypatch.delenv("PMAGPY_DIRECTIONS_DIR", raising=False)
        monkeypatch.delenv("DEMAG_DIR", raising=False)
        monkeypatch.setenv("PMAGPY_DIRECTIONS_OUTPUT", str(tmp_path))
        seen = {}
        monkeypatch.setattr(app, "build_body", lambda session: seen.setdefault("dir", session.directory) and _stub_body(session))
        tmpl = app.serve_default()
        assert seen["dir"] == datasets.example_dir("McMurdo") != ""
        assert tmpl.session is not None and tmpl.session.directory == seen["dir"]
        assert tmpl.body is not None


def _stub_body(session):
    import panel as pn
    from pmagpy_panel import shell
    from pmagpy_directions.session import APP
    return shell.Body(info=APP, main=pn.Column(), side=pn.Column())
