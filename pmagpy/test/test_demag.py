"""
Tests for the MagIC 3-native demag core.

The regression targets are the directional interpretations already stored in
``data_files/dmag_magic/specimens.txt`` (produced by the legacy Demag GUI):
re-fitting every one of them with the new core must reproduce the published
dec/inc/MAD/n values.
"""
import os

import numpy as np
import pandas as pd
import pytest

import pmagpy.pmag as pmag

from pmagpy.demag import (DemagData, COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT,
                        zijderveld_xy, equal_area_xy, fit_line_segment,
                        great_circle_xy, step_label, build_orientation, plane_best_fit_vectors,
                        add_transformed_coordinates, unify_polarity, merge_results, carry_metadata,
                        trim_to_model, validate_directory, is_metadata_column)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DMAG_DIR = os.path.join(REPO, "data_files", "dmag_magic")
MCMURDO_DIR = os.path.join(REPO, "data_files", "3_0", "McMurdo")


@pytest.fixture(scope="module")
def dmag():
    return DemagData.from_directory(DMAG_DIR)


@pytest.fixture(scope="module")
def published():
    df = pd.read_csv(os.path.join(DMAG_DIR, "specimens.txt"), sep="\t", header=1)
    return df[df["dir_comp"].notna()]


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
class TestLoading:
    def test_specimens_and_hierarchy(self, dmag):
        assert len(dmag.specimens) > 150  # 265 specimens in this example file have column-shifted rows
        spec = dmag.specimens["jm002a1"]
        assert spec.sample == "jm002a"
        assert spec.site == "jm002"
        assert spec.location != ""

    def test_af_step_table(self, dmag):
        steps = dmag.specimens["jm002a1"].steps
        assert list(steps["treat_type"][:2]) == ["NRM", "AF"]
        assert steps["treat_unit"].iloc[0] == "T"   # NRM inherits the AF unit
        assert steps["label"].iloc[0] == "NRM"
        assert steps["label"].iloc[1] == "5 mT"
        np.testing.assert_allclose(steps["treat_value"].iloc[1], 0.005)
        assert steps["moment_norm"].iloc[0] == 1.0
        assert (steps["sequence"].values == np.arange(len(steps))).all()
        assert set(steps["quality"]) <= {"g", "b"}

    def test_thermal_step_table(self, dmag):
        steps = dmag.specimens["jm002d1"].steps
        assert "T" in set(steps["treat_type"])
        thermal = steps[steps["treat_type"] == "T"]
        assert thermal["treat_unit"].iloc[0] == "K"
        assert thermal["label"].iloc[-1].endswith("°C")

    def test_orientation_and_coordinates(self, dmag):
        spec = dmag.specimens["jm002a1"]
        assert spec.orientation.has_geographic
        assert spec.has_coord(COORD_GEOGRAPHIC)
        # bedding present (flat) -> tilt-corrected equals geographic
        assert spec.has_coord(COORD_TILT)
        np.testing.assert_allclose(spec.steps["dec_t"], spec.steps["dec_g"])
        # geographic transform agrees with pmag.dogeo step by step
        row = spec.steps.iloc[3]
        dec_g, inc_g = pmag.dogeo(row["dec_s"], row["inc_s"], spec.orientation.azimuth, spec.orientation.dip)
        np.testing.assert_allclose([row["dec_g"], row["inc_g"]], [dec_g, inc_g], atol=1e-6)

    def test_multirow_samples_table_picks_orientation_row(self, dmag):
        samp_df = dmag._table("samples")
        # jm002a has one orientation row and one result row with NaN azimuth
        assert (samp_df["sample"] == "jm002a").sum() >= 2
        orient = build_orientation(samp_df, "jm002a")
        assert orient.azimuth == 93.0 and orient.dip == -56.0
        assert "SO-GPS-DIFF" in orient.method_codes
        assert "SO-POM" not in orient.method_codes

    def test_site_coords(self, dmag):
        lat, lon = dmag.site_coords["jm002"]
        assert 70 < lat < 72 and 351 < lon < 352

    def test_vds(self, dmag):
        spec = dmag.specimens["jm002a1"]
        vds = spec.vds()
        assert vds >= 1.0  # at least the NRM magnitude
        assert vds < 5.0

    def test_step_labels(self):
        assert step_label(0.01, "T", "AF") == "10 mT"
        assert step_label(773.0, "K", "T") == "500°C"
        assert step_label(0.0, "T", "NRM") == "NRM"


# --------------------------------------------------------------------------
# fitting against the published interpretations
# --------------------------------------------------------------------------
class TestFits:
    def test_line_fit_matches_published_values(self, dmag):
        # jm002a1 component A: 0.01-0.15 T, DE-BFL -> 195.0 / 49.6, MAD 1.3, n = 11
        imin = dmag.step_index_for_value("jm002a1", 0.01, "T")
        imax = dmag.step_index_for_value("jm002a1", 0.15, "T")
        comp = dmag.add_component("jm002a1", "A", imin, imax, "DE-BFL")
        res = dmag.fit(comp, COORD_SPECIMEN)
        assert res.dir_n_measurements == 11
        np.testing.assert_allclose([res.dir_dec, res.dir_inc], [195.0, 49.6], atol=0.05)
        np.testing.assert_allclose(res.dir_mad_free, 1.3, atol=0.05)
        assert res.meas_step_min == 0.01 and res.meas_step_max == 0.15
        assert res.meas_step_unit == "T"
        assert res.method_codes == "DA-DIR:DE-BFL:LP-DIR-AF"
        geo = dmag.fit(comp, COORD_GEOGRAPHIC)
        np.testing.assert_allclose([geo.dir_dec, geo.dir_inc], [62.2, 70.8], atol=0.05)
        assert geo.method_codes == "DA-DIR-GEO:DE-BFL:LP-DIR-AF:SO-GPS-DIFF"
        tilt = dmag.fit(comp, COORD_TILT)
        assert "DA-DIR-TILT" in tilt.method_codes
        dmag.remove_component(comp)

    def test_plane_fit_matches_published_values(self, dmag):
        # jm002d1 component A: 273-858 K, DE-BFP -> 261.1 / -0.1, MAD 2.4, n = 13
        imin = dmag.step_index_for_value("jm002d1", 273.0, "K")
        imax = dmag.step_index_for_value("jm002d1", 858.0, "K")
        assert imin == 0  # 273 K is the NRM step
        comp = dmag.add_component("jm002d1", "A", imin, imax, "DE-BFP")
        res = dmag.fit(comp, COORD_SPECIMEN)
        assert res.direction_type == "p"
        assert res.dir_n_measurements == 13
        np.testing.assert_allclose([res.dir_dec, res.dir_inc], [261.1, -0.1], atol=0.05)
        np.testing.assert_allclose(res.dir_mad_free, 2.4, atol=0.05)
        assert res.meas_step_min == 273.0 and res.meas_step_max == 858.0
        assert res.meas_step_unit == "K"
        assert np.isnan(res.dir_dang)
        dmag.remove_component(comp)

    def test_all_published_interpretations_reproduce(self, dmag, published):
        """Import every published interpretation and re-fit it.

        data_files/dmag_magic is an imperfect example (1056 column-shifted
        measurement rows, repeated treatment steps whose published fits used
        the second occurrence), so this asserts a high reproduction rate with
        only small residuals; the exact-match regression is TestMcMurdo.
        """
        dmag.clear_components()
        n = dmag.load_components_from_specimens_table(COORD_SPECIMEN)
        assert n > 150
        checked, failures = 0, []
        for coord in (COORD_SPECIMEN, COORD_GEOGRAPHIC):
            pub = published[published["dir_tilt_correction"] == coord]
            for res in dmag.fit_all(coord):
                match = pub[(pub["specimen"] == res.specimen) & (pub["dir_comp"] == res.dir_comp)]
                if len(match) != 1:
                    continue
                m = match.iloc[0]
                checked += 1
                ang = pmag.angle([res.dir_dec, res.dir_inc], [m["dir_dec"], m["dir_inc"]])[0]
                # planes are axial: pole may be reported antipodal
                if res.direction_type == "p":
                    ang = min(ang, 180 - ang)
                if ang > 0.2 or abs(res.dir_mad_free - m["dir_mad_free"]) > 0.11 \
                        or res.dir_n_measurements != int(m["dir_n_measurements"]):
                    failures.append((res.specimen, res.dir_comp, coord, ang,
                                     res.dir_mad_free, m["dir_mad_free"],
                                     res.dir_n_measurements, m["dir_n_measurements"]))
        assert checked > 250
        assert len(failures) < 0.2 * checked, f"{len(failures)} of {checked} mismatches, e.g. {failures[:5]}"
        # residual differences are one or two steps at a bound, never a different direction
        assert all(f[3] < 1.5 and abs(f[6] - f[7]) <= 2 for f in failures), failures[:5]
        dmag.clear_components()

    def test_fisher_and_anchored_fits(self, dmag):
        comp = dmag.add_component("jm002a1", "F", 1, 12, "DE-FM")
        res = dmag.fit(comp, COORD_SPECIMEN)
        assert not np.isnan(res.dir_alpha95)
        assert np.isnan(res.dir_mad_free)
        fm = pmag.fisher_mean(dmag.specimens["jm002a1"].steps[["dec_s", "inc_s"]].values[1:13].tolist())
        np.testing.assert_allclose([res.dir_dec, res.dir_inc], [fm["dec"], fm["inc"]], atol=1e-6)
        anchored = dmag.add_component("jm002a1", "An", 1, 12, "DE-BFL-A")
        res_a = dmag.fit(anchored, COORD_SPECIMEN)
        assert res_a.direction_type == "l"
        dmag.clear_components("jm002a1")

    def test_bad_step_bounds_snap(self, dmag):
        spec = dmag.specimens["jm002a1"]
        original = spec.steps["quality"].copy()
        spec.steps.loc[1, "quality"] = "b"
        comp = dmag.add_component("jm002a1", "A", 1, 12, "DE-BFL")
        res = dmag.fit(comp, COORD_SPECIMEN)
        assert res.imin == 2
        assert res.dir_n_measurements == 11
        spec.steps["quality"] = original
        dmag.clear_components("jm002a1")

    def test_too_few_points_returns_none(self, dmag):
        comp = dmag.add_component("jm002a1", "A", 3, 4, "DE-BFP")
        assert dmag.fit(comp, COORD_SPECIMEN) is None
        dmag.clear_components("jm002a1")


# --------------------------------------------------------------------------
# means, VGPs and export
# --------------------------------------------------------------------------
class TestMeansAndExport:
    def test_site_mean_and_vgp(self, dmag):
        dmag.clear_components()
        dmag.load_components_from_specimens_table(COORD_SPECIMEN)
        means = dmag.mean_directions(level="site", coord=COORD_GEOGRAPHIC)
        assert len(means) > 10
        row = means[(means["site"] == "jm002") & (means["dir_comp_name"] == "A")].iloc[0]
        assert row["dir_n_specimens"] >= 3
        assert {"vgp_lat", "vgp_lon", "vgp_dp", "vgp_dm"} <= set(means.columns)
        # cross-check the Fisher mean of lines+planes with pmag.dolnp directly
        recs = []
        for res in dmag.fit_all(COORD_GEOGRAPHIC, None):
            spec = dmag.specimens[res.specimen]
            if spec.site == "jm002" and res.dir_comp == "A" and res.result_quality == "g":
                recs.append({"dir_dec": res.dir_dec, "dir_inc": res.dir_inc,
                             "dir_tilt_correction": 0, "dir_type": res.direction_type})
        ref = pmag.dolnp(recs, "dir_type")
        np.testing.assert_allclose([row["dir_dec"], row["dir_inc"]],
                                   [float(ref["dec"]), float(ref["inc"])], atol=0.06)
        plon, plat, dp, dm = pmag.dia_vgp(row["dir_dec"], row["dir_inc"], row["dir_alpha95"], row["lat"], row["lon"])
        np.testing.assert_allclose([row["vgp_lat"], row["vgp_lon"]], [plat, plon], atol=1e-6)

    def test_sample_means(self, dmag):
        means = dmag.mean_directions(level="sample", coord=COORD_SPECIMEN)
        assert len(means) > 100
        assert "sample" in means.columns

    def test_specimens_table_and_write(self, dmag, tmp_path):
        table = dmag.specimens_table()
        required = {"specimen", "sample", "dir_comp", "dir_dec", "dir_inc",
                    "dir_mad_free", "dir_n_measurements", "dir_tilt_correction", "meas_step_min",
                    "meas_step_max", "meas_step_unit", "method_codes", "result_quality"}
        assert required <= set(table.columns)
        assert not {"site", "location"} & set(table.columns)     # not columns of the MagIC specimens table
        assert set(table["dir_tilt_correction"].unique()) == {-1, 0, 100}
        # three rows (one per coordinate system) for a fully oriented specimen
        assert (table[(table["specimen"] == "jm002a1") & (table["dir_comp"] == "A")]).shape[0] == 3
        path = dmag.write_specimens(str(tmp_path))
        assert os.path.exists(path)
        back = pd.read_csv(path, sep="\t", header=1)
        assert back["specimen"].nunique() >= table["specimen"].nunique()
        # a fresh DemagData built from the written directory reimports the same components
        import shutil
        for name in ("measurements.txt", "samples.txt", "sites.txt", "locations.txt"):
            shutil.copy(os.path.join(DMAG_DIR, name), tmp_path / name)
        again = DemagData.from_directory(str(tmp_path))
        n = again.load_components_from_specimens_table(COORD_SPECIMEN)
        assert n == len(dmag.components)

    def test_write_site_means(self, dmag, tmp_path):
        path = dmag.write_means("site", str(tmp_path), coord=COORD_GEOGRAPHIC)
        back = pd.read_csv(path, sep="\t", header=1)
        assert "vgp_lat" in back.columns and "dir_alpha95" in back.columns

    def test_json_round_trip(self, dmag):
        text = dmag.components_to_json()
        n_before = len(dmag.components)
        dmag.clear_components()
        assert dmag.components_from_json(text) == n_before
        assert len(dmag.components) == n_before


# --------------------------------------------------------------------------
# plotting geometry
# --------------------------------------------------------------------------
class TestGeometry:
    def test_zijderveld_projection(self, dmag):
        spec = dmag.specimens["jm002a1"]
        z = zijderveld_xy(spec.steps, COORD_SPECIMEN)
        assert len(z) == spec.n_steps
        # NRM vector has unit length after normalisation
        np.testing.assert_allclose(np.hypot(np.hypot(z["x"][0], z["y_h"][0]), z["y_v"][0]), 1.0)
        # rotating to the NRM declination puts the NRM on the +x axis
        zr = zijderveld_xy(spec.steps, COORD_SPECIMEN, rotation_dec=spec.steps["dec_s"].iloc[0])
        assert abs(zr["y_h"][0]) < 1e-9 and zr["x"][0] > 0

    def test_equal_area(self):
        x, y = equal_area_xy([0.0, 90.0], [90.0, 0.0])
        np.testing.assert_allclose([x[0], y[0]], [0.0, 0.0], atol=1e-9)
        np.testing.assert_allclose(np.hypot(x[1], y[1]), 1.0)

    def test_line_segment_and_great_circle(self, dmag):
        comp = dmag.add_component("jm002a1", "A", 1, 12, "DE-BFL")
        res = dmag.fit(comp, COORD_SPECIMEN)
        seg = fit_line_segment(res, dmag.specimens["jm002a1"], COORD_SPECIMEN)
        assert seg.shape == (2, 3)
        plane = dmag.add_component("jm002a1", "P", 1, 12, "DE-BFP")
        resp = dmag.fit(plane, COORD_SPECIMEN)
        assert fit_line_segment(resp, dmag.specimens["jm002a1"], COORD_SPECIMEN) is None
        gx, gy = great_circle_xy(resp.dir_dec, resp.dir_inc)
        assert len(gx) > 10 and np.all(np.hypot(gx, gy) <= 1.0 + 1e-9)
        dmag.clear_components("jm002a1")

    def test_synthetic_tilt_correction(self, dmag):
        spec = dmag.specimens["jm002a1"]
        orient = build_orientation(dmag._table("samples"), "jm002a")
        orient.bed_dip_direction, orient.bed_dip = 45.0, 20.0
        steps = add_transformed_coordinates(spec.steps.drop(columns=["dec_g", "inc_g", "dec_t", "inc_t"]), orient)
        row = steps.iloc[2]
        dec_t, inc_t = pmag.dotilt(row["dec_g"], row["inc_g"], 45.0, 20.0)
        np.testing.assert_allclose([row["dec_t"], row["inc_t"]], [dec_t, inc_t], atol=1e-6)


@pytest.fixture(scope="module")
def mcmurdo():
    return DemagData.from_directory(MCMURDO_DIR)


class TestMcMurdo:
    def test_loads_mixed_af_thermal_contribution(self, mcmurdo):
        assert len(mcmurdo.specimens) > 500
        units = {s.unit for s in mcmurdo.specimens.values()}
        assert "T" in units and "K" in units

    def test_published_interpretations_reproduce(self, mcmurdo):
        """992 legacy-GUI interpretations (AF and thermal, lines and planes) must re-fit identically."""
        pub = pd.read_csv(os.path.join(MCMURDO_DIR, "specimens.txt"), sep="\t", header=1)
        pub = pub[pub["dir_comp"].notna() & pub["meas_step_min"].notna() & (pub["dir_tilt_correction"] == -1)]
        mcmurdo.clear_components()
        n = mcmurdo.load_components_from_specimens_table(COORD_SPECIMEN)
        assert n == len(pub)  # intensity rows must not be imported as components
        checked, failures = 0, []
        for res in mcmurdo.fit_all(COORD_SPECIMEN):
            match = pub[(pub["specimen"] == res.specimen) & (pub["dir_comp"] == res.dir_comp)]
            if len(match) != 1:
                continue
            m = match.iloc[0]
            checked += 1
            ang = pmag.angle([res.dir_dec, res.dir_inc], [m["dir_dec"], m["dir_inc"]])[0]
            if res.direction_type == "p":
                ang = min(ang, 180 - ang)
            mad_ok = np.isnan(m["dir_mad_free"]) or abs(res.dir_mad_free - m["dir_mad_free"]) <= 0.11
            if ang > 0.2 or not mad_ok or res.dir_n_measurements != int(m["dir_n_measurements"]):
                failures.append((res.specimen, res.dir_comp, round(float(ang), 2), res.dir_mad_free,
                                 m["dir_mad_free"], res.dir_n_measurements, m["dir_n_measurements"]))
        assert checked > 900
        assert failures == [], f"{len(failures)} of {checked} mismatches, e.g. {failures[:5]}"
        assert len(mcmurdo.fit_all(COORD_GEOGRAPHIC)) > 900


# --------------------------------------------------------------------------
# optional external dataset (set DEMAG_EXTRA_DATA to a MagIC directory that
# holds legacy Demag GUI interpretations, e.g. Fairchild et al. 2017)
# --------------------------------------------------------------------------
EXTRA_DIR = os.environ.get("DEMAG_EXTRA_DATA", "")


@pytest.mark.skipif(not os.path.isdir(EXTRA_DIR), reason="DEMAG_EXTRA_DATA not set or missing")
def test_external_dataset_reproduces_all_coordinate_systems():
    data = DemagData.from_directory(EXTRA_DIR)
    pub = pd.read_csv(os.path.join(EXTRA_DIR, "specimens.txt"), sep="\t", header=1)
    pub = pub[pub["dir_comp"].notna() & pub["meas_step_min"].notna()]
    n = data.load_components_from_specimens_table(COORD_SPECIMEN)
    assert n == (pub["dir_tilt_correction"] == -1).sum()
    for coord in (COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT):
        p = pub[pub["dir_tilt_correction"] == coord]
        if not len(p):
            continue
        checked, failures = 0, []
        for res in data.fit_all(coord):
            match = p[(p["specimen"] == res.specimen) & (p["dir_comp"] == res.dir_comp)]
            if len(match) != 1:
                continue
            m = match.iloc[0]
            checked += 1
            ang = pmag.angle([res.dir_dec, res.dir_inc], [m["dir_dec"], m["dir_inc"]])[0]
            if res.direction_type == "p":
                ang = min(ang, 180 - ang)
            if ang > 0.2 or res.dir_n_measurements != int(m["dir_n_measurements"]):
                # The legacy GUI's data-model-3 path ignored the measurements
                # 'quality' column, so fits whose bounds enclose a step flagged
                # 'b' were published with that step included. The core honours
                # the flag; such fits are the only mismatches tolerated here.
                quality = data.specimens[res.specimen].steps["quality"].values
                comp = next(c for c in data.components if c.specimen == res.specimen and c.name == res.dir_comp)
                if (quality[comp.imin:comp.imax + 1] == "b").any():
                    continue
                failures.append((res.specimen, res.dir_comp, coord, float(ang), res.dir_n_measurements,
                                 m["dir_n_measurements"]))
        assert checked > 0
        assert failures == [], f"coord {coord}: {len(failures)} of {checked} mismatches, e.g. {failures[:5]}"


# --------------------------------------------------------------------------
# .redo intermediary, quality write-back, means of means, mean pole
# --------------------------------------------------------------------------
class TestRedoAndPersistence:
    def test_redo_round_trip(self, dmag, tmp_path):
        dmag.clear_components()
        dmag.load_components_from_specimens_table(COORD_SPECIMEN)
        comp = dmag.add_component("jm002a1", "B", 3, 7, "DE-BFP", "b", "#4ED740")
        before = {c.key(): (c.imin, c.imax, c.fit_type, c.quality, c.color) for c in dmag.components}
        path = dmag.write_redo(str(tmp_path / "test.redo"), current_specimen="jm002a1")
        lines = open(path).read().splitlines()
        assert any(line.startswith("current_jm002a1\t") for line in lines)
        b_line = [line for line in lines if "\tB\t" in line][0].split("\t")
        assert b_line[1] == "DE-BFP" and b_line[5] == "#4ED740" and b_line[6] == "b"
        assert float(b_line[2]) == 0.015 and float(b_line[3]) == 0.05   # tesla
        dmag.clear_components()
        n, current = dmag.read_redo(path)
        assert current == "jm002a1"
        assert n == len(before)
        after = {c.key(): (c.imin, c.imax, c.fit_type, c.quality, c.color) for c in dmag.components}
        assert {k: v[:4] for k, v in after.items()} == {k: v[:4] for k, v in before.items()}
        assert after[("jm002a1", "B")][4] == "#4ED740"
        dmag.clear_components()

    def test_redo_thermal_bounds_use_kelvin_and_zero_for_nrm(self, dmag, tmp_path):
        dmag.clear_components()
        dmag.add_component("jm002d1", "A", 0, 12, "DE-BFP")
        path = dmag.write_redo(str(tmp_path / "t.redo"))
        parts = open(path).read().split("\t")
        assert parts[2] == "0" and parts[3] == "858"
        dmag.clear_components()
        n, _ = dmag.read_redo(path)
        assert n == 1 and dmag.components[0].imin == 0 and dmag.components[0].imax == 12
        dmag.clear_components()

    def test_quality_written_to_measurements(self, dmag, tmp_path):
        spec = dmag.specimens["jm002a1"]
        original = spec.steps["quality"].copy()
        dmag.toggle_step_quality("jm002a1", 4)
        assert spec.steps.loc[4, "quality"] == "b"
        path = dmag.write_measurements(str(tmp_path))
        assert os.path.dirname(os.path.realpath(path)) == os.path.realpath(str(tmp_path))   # never the source file
        back = pd.read_csv(path, sep="\t", header=1)
        row = back[(back["specimen"] == "jm002a1") & (back["measurement"].astype(str) == spec.steps.loc[4, "measurement"])]
        assert len(row) >= 1 and (row["quality"] == "b").all()
        spec.steps["quality"] = original
        dmag.write_measurements(str(tmp_path))

    def test_site_means_over_samples_and_location_over_sites(self, dmag):
        dmag.clear_components()
        dmag.load_components_from_specimens_table(COORD_SPECIMEN)
        over_samples = dmag.mean_directions("site", COORD_GEOGRAPHIC, component="A", over="samples")
        assert "dir_n_samples" in over_samples.columns and len(over_samples) > 10
        over_specimens = dmag.mean_directions("site", COORD_GEOGRAPHIC, component="A")
        m1 = over_samples[over_samples["site"] == "jm002"].iloc[0]
        m2 = over_specimens[over_specimens["site"] == "jm002"].iloc[0]
        assert pmag.angle([m1["dir_dec"], m1["dir_inc"]], [m2["dir_dec"], m2["dir_inc"]])[0] < 5
        loc = dmag.mean_directions("location", COORD_GEOGRAPHIC, component="A", over="sites")
        assert len(loc) >= 1 and "dir_n_sites" in loc.columns and loc["dir_n_sites"].iloc[0] > 5
        with pytest.raises(ValueError):
            dmag.mean_directions("sample", COORD_GEOGRAPHIC, over="sites")

    def test_mean_pole(self, dmag):
        pole = dmag.mean_pole(COORD_GEOGRAPHIC, component="A")
        assert pole and pole["N"] > 5 and 0 < pole["A95"] < 90
        assert -90 <= pole["plat"] <= 90 and 0 <= pole["plon"] < 360
        # every VGP used lies within 90 degrees of the pole after polarity unification
        for _, v in pole["vgps"].iterrows():
            assert pmag.angle([v["vgp_lon"], v["vgp_lat"]], [pole["plon"], pole["plat"]])[0] <= 90
        dmag.clear_components()

    def test_projection_helpers(self, dmag):
        from pmagpy.demag import projection_rotation, axis_labels
        spec = dmag.specimens["jm002a1"]
        assert projection_rotation(spec, COORD_SPECIMEN, "ns") == 0.0
        assert projection_rotation(spec, COORD_SPECIMEN, "ew") == 90.0
        np.testing.assert_allclose(projection_rotation(spec, COORD_SPECIMEN, "nrm"), spec.steps["dec_s"].iloc[0])
        assert projection_rotation(spec, COORD_SPECIMEN, "fit", fit_dec=123.0) == 123.0
        assert axis_labels(COORD_GEOGRAPHIC, "ew")["right"] == "E"
        assert axis_labels(COORD_GEOGRAPHIC, "ew")["top_h"] == "N"
        assert axis_labels(COORD_GEOGRAPHIC, "ns")["bottom_h"] == "E"


@pytest.mark.skipif(not os.path.isdir(EXTRA_DIR), reason="DEMAG_EXTRA_DATA not set or missing")
def test_external_redo_matches_specimens_table():
    redo = os.path.join(EXTRA_DIR, "demag_last_session.redo")
    if not os.path.exists(redo):
        pytest.skip("no .redo file in external dataset")
    data = DemagData.from_directory(EXTRA_DIR)
    n, _ = data.read_redo(redo)
    from_redo = {c.key(): (c.imin, c.imax, c.fit_type) for c in data.components}
    data.load_components_from_specimens_table(COORD_SPECIMEN)
    from_table = {c.key(): (c.imin, c.imax, c.fit_type) for c in data.components}
    shared = set(from_redo) & set(from_table)
    assert len(shared) > 0.9 * len(from_table)
    assert all(from_redo[k] == from_table[k] for k in shared)


# --------------------------------------------------------------------------
# polarity, export policy, validation
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def study():
    """dmag_magic with its published interpretations loaded (a separate instance)."""
    data = DemagData.from_directory(DMAG_DIR)
    data.load_components_from_specimens_table()
    return data


class TestBestFitVectors:
    """dir_bfv_*: where a plane's direction falls once the lines pin it down (MM88)."""

    RECORDS = [{"dir_dec": 10.0, "dir_inc": 45.0, "dir_type": "l"},
               {"dir_dec": 20.0, "dir_inc": 50.0, "dir_type": "l"},
               {"dir_dec": 200.0, "dir_inc": 10.0, "dir_type": "p"},
               {"dir_dec": 300.0, "dir_inc": -20.0, "dir_type": "p"}]

    @staticmethod
    def _cart(dec, inc):
        return np.asarray(pmag.dir2cart([dec, inc, 1.0]), dtype=float).ravel()

    def test_vectors_lie_on_their_great_circles(self):
        vectors = plane_best_fit_vectors(self.RECORDS)
        planes = [r for r in self.RECORDS if r["dir_type"] == "p"]
        assert len(vectors) == len(planes)
        for rec, (dec, inc) in zip(planes, vectors):
            # on the great circle means perpendicular to its pole
            dot = float(np.dot(self._cart(rec["dir_dec"], rec["dir_inc"]), self._cart(dec, inc)))
            assert dot == pytest.approx(0.0, abs=1e-9)

    def test_the_vectors_are_the_ones_dolnp_averages(self):
        """Replacing every plane by its best-fit vector must reproduce dolnp's mean."""
        vectors = plane_best_fit_vectors(self.RECORDS)
        resultant = np.sum([self._cart(r["dir_dec"], r["dir_inc"]) for r in self.RECORDS if r["dir_type"] == "l"]
                           + [self._cart(d, i) for d, i in vectors], axis=0)
        dec, inc = pmag.cart2dir(list(resultant / np.linalg.norm(resultant)))[:2]
        lnp = pmag.dolnp(self.RECORDS, "dir_type")
        assert dec == pytest.approx(float(lnp["dec"]), abs=0.05)
        assert inc == pytest.approx(float(lnp["inc"]), abs=0.05)

    def test_sets_without_a_plane(self):
        assert plane_best_fit_vectors([]) == []
        assert plane_best_fit_vectors([self.RECORDS[0]]) == []

    def test_planes_alone_meet_where_their_circles_cross(self):
        # with no line to converge on, two circles leave one intersection
        vectors = plane_best_fit_vectors([r for r in self.RECORDS if r["dir_type"] == "p"])
        assert len(vectors) == 2
        assert vectors[0] == pytest.approx(vectors[1], abs=0.1)

    def test_mcmurdo_planes_resolve_towards_their_site_mean(self, mcmurdo):
        mcmurdo.clear_components()
        mcmurdo.load_components_from_specimens_table()
        planes = [c for c in mcmurdo.components if c.fit_type == "DE-BFP"]
        assert len(planes) > 50
        vectors = mcmurdo.best_fit_vectors(COORD_GEOGRAPHIC)
        assert len(vectors) == len(planes)
        means = mcmurdo.mean_directions("site", COORD_GEOGRAPHIC)
        for comp in planes[:12]:
            dec, inc = vectors[(comp.specimen, comp.name)]
            result = mcmurdo.fit(comp, COORD_GEOGRAPHIC)
            # on its own great circle ...
            assert float(np.dot(self._cart(result.dir_dec, result.dir_inc),
                                self._cart(dec, inc))) == pytest.approx(0.0, abs=1e-9)
            # ... and no further from the site mean than the pole-to-plane it came from
            site = mcmurdo.specimens[comp.specimen].site
            row = means[(means["site"] == site) & (means["dir_comp_name"] == comp.name)]
            if len(row):
                mean = self._cart(row["dir_dec"].iloc[0], row["dir_inc"].iloc[0])
                assert np.dot(mean, self._cart(dec, inc)) > np.dot(mean, self._cart(result.dir_dec, result.dir_inc))

    def test_specimens_table_carries_the_vectors_per_coordinate_system(self, mcmurdo):
        mcmurdo.clear_components()
        mcmurdo.load_components_from_specimens_table()
        table = mcmurdo.specimens_table(coords=(COORD_SPECIMEN, COORD_GEOGRAPHIC))
        planes = table["method_codes"].str.contains("DE-BFP", na=False)
        assert table.loc[planes, "dir_bfv_dec"].notna().all()
        assert not table.loc[~planes, "dir_bfv_dec"].notna().any()   # never on a line fit
        # the direction is resolved in each system separately, so the rows differ
        both = table[planes].groupby("specimen")["dir_bfv_dec"].nunique()
        assert (both > 1).any()


class TestPolarity:
    def test_unify_polarity_uses_the_principal_axis_and_the_majority(self):
        rng = np.random.default_rng(0)
        normal = [[(rng.normal(0, 3)) % 360, 60 + rng.normal(0, 3)] for _ in range(10)]
        reversed_ = [[180 + rng.normal(0, 3), -60 + rng.normal(0, 3)] for _ in range(8)]
        unified, flipped = unify_polarity(normal + reversed_)
        assert flipped.sum() == 8 and flipped[10:].all()
        assert all(i > 0 for _, i in unified)
        # with the reversed group in the majority the normal ones are inverted instead
        unified, flipped = unify_polarity(normal[:6] + reversed_)
        assert flipped.sum() == 6 and flipped[:6].all()
        assert all(i < 0 for _, i in unified)

    def test_mixed_polarity_does_not_bias_the_axis(self):
        # a 50/50 split: a Fisher mean of the raw set would be meaningless, the
        # principal axis is still the common axis
        normal = [[0, 60], [5, 58], [355, 62], [2, 61]]
        reversed_ = [[180, -60], [185, -58], [175, -62], [182, -61]]
        unified, flipped = unify_polarity(normal + reversed_)
        decs = np.array([d for d, _ in unified])
        assert flipped.sum() == 4
        assert (np.minimum(decs, 360 - decs) < 10).all() or (np.abs(decs - 180) < 10).all()

    def test_mean_pole_reports_flips_and_paleolatitude(self, study):
        pole = study.mean_pole(COORD_GEOGRAPHIC, "A", "site")
        assert {"plon", "plat", "A95", "K", "N", "reversed_perc", "site_lat", "site_lon", "paleolat"} <= set(pole)
        assert "flipped" in pole["vgps"].columns
        assert -90 <= pole["paleolat"] <= 90
        raw = study.mean_pole(COORD_GEOGRAPHIC, "A", "site", common_polarity=False)
        assert raw["reversed_perc"] == 0 and not raw["vgps"]["flipped"].any()

    def test_flip_reports_the_antipodes(self, study):
        pole = study.mean_pole(COORD_GEOGRAPHIC, "A", "site")
        flipped = study.mean_pole(COORD_GEOGRAPHIC, "A", "site", flip=True)
        assert flipped["plon"] == pytest.approx((pole["plon"] + 180) % 360)
        assert flipped["plat"] == pytest.approx(-pole["plat"])
        assert flipped["A95"] == pytest.approx(pole["A95"]) and flipped["N"] == pole["N"]
        assert flipped["paleolat"] == pytest.approx(-pole["paleolat"])
        assert flipped["reversed_perc"] == pytest.approx(100 - pole["reversed_perc"])
        assert (flipped["vgps"]["flipped"] == ~pole["vgps"]["flipped"]).all()
        # the location mean direction follows the same choice
        loc = study.mean_directions("location", COORD_GEOGRAPHIC, "A", over="sites")
        loc_f = study.mean_directions("location", COORD_GEOGRAPHIC, "A", over="sites", flip=True)
        assert loc_f["dir_dec"].iloc[0] == pytest.approx((loc["dir_dec"].iloc[0] + 180) % 360)
        assert loc_f["dir_inc"].iloc[0] == pytest.approx(-loc["dir_inc"].iloc[0])
        table = study.locations_table(coord=COORD_GEOGRAPHIC, flip=True)
        row = table[table["pole_comp_name"] == "A"].iloc[0]
        assert row["pole_lat"] == pytest.approx(round(flipped["plat"], 1))
        # flip without unification inverts everything
        raw = study.mean_pole(COORD_GEOGRAPHIC, "A", "site", common_polarity=False, flip=True)
        assert raw["vgps"]["flipped"].all() and raw["reversed_perc"] == 100

    def test_location_mean_is_unified_but_site_means_are_not(self, study):
        loc = study.mean_directions("location", COORD_GEOGRAPHIC, "A", over="sites")
        assert "reversed_perc" in loc.columns
        site = study.mean_directions("site", COORD_GEOGRAPHIC, "A")
        assert (site["reversed_perc"] == 0).all()


class TestExportPolicy:
    def _existing(self):
        return pd.DataFrame([
            {"site": "A", "dir_dec": 10.0, "dir_inc": 50.0, "lat": 44.0, "lon": -92.0, "age": 1100, "lithologies": "Basalt",
             "method_codes": "LP-DIR-AF:DE-FM"},
            {"site": "A", "int_abs": 4e-5, "dir_dec": 12.0, "lat": 44.0, "lon": -92.0, "method_codes": "LP-PI-TRM:DE-BFL"},
            {"site": "B", "dir_dec": 200.0, "dir_inc": -40.0, "lat": 45.0, "lon": -91.0, "method_codes": "LP-DIR-T:DE-FM"},
            {"site": "C", "dir_dec": 30.0, "dir_inc": 20.0, "lat": 46.0, "lon": -90.0, "lithologies": "Rhyolite",
             "method_codes": "LP-DIR-T:DE-FM"},
        ])

    def test_merge_replaces_owned_directional_rows_only(self):
        existing = self._existing()
        new = pd.DataFrame([{"site": "A", "dir_dec": 11.0, "dir_inc": 51.0, "method_codes": "LP-DIR-AF:DE-FM:DE-DI"}])
        merged = merge_results(existing, new, "site", owned=["A", "C"])
        a_rows = merged[merged["site"] == "A"]
        assert len(a_rows) == 2                                  # the intensity row survives, the old mean is gone
        assert a_rows["int_abs"].notna().sum() == 1
        assert (a_rows.loc[a_rows["int_abs"].isna(), "dir_dec"] == 11.0).all()
        b_rows = merged[merged["site"] == "B"]                   # not owned: untouched
        assert len(b_rows) == 1 and b_rows["dir_dec"].iloc[0] == 200.0
        c_rows = merged[merged["site"] == "C"]                   # owned, no new mean: metadata stub only
        assert len(c_rows) == 1 and pd.isna(c_rows["dir_dec"].iloc[0]) and c_rows["lithologies"].iloc[0] == "Rhyolite"

    def test_carry_metadata_fills_only_empty_metadata(self):
        existing = self._existing()
        new = pd.DataFrame([{"site": "A", "dir_dec": 11.0, "lat": np.nan}, {"site": "C", "dir_dec": 1.0, "lat": 1.0}])
        out = carry_metadata(new, existing, "site")
        assert out.loc[0, "lat"] == 44.0 and out.loc[0, "age"] == 1100 and out.loc[0, "lithologies"] == "Basalt"
        assert out.loc[1, "lat"] == 1.0                          # a value already present is kept
        assert "dir_inc" not in out.columns                      # results are never carried over
        assert not is_metadata_column("dir_dec") and not is_metadata_column("int_abs") and is_metadata_column("lat")

    def test_trim_to_model_drops_foreign_columns(self):
        df = pd.DataFrame([{"specimen": "x", "sample": "y", "dir_dec": 1.0, "location": "L", "foo": 1}])
        warnings = []
        out = trim_to_model(df, "specimens", warnings)
        assert set(out.columns) == {"specimen", "sample", "dir_dec"} and warnings

    def test_specimens_table_is_model_clean_with_geology(self, study):
        table = study.merged_specimens_table()
        known = set(study._data_model(True).dm["specimens"].index) if hasattr(dmag, "_data_model") else None
        from pmagpy.demag import _data_model
        known = set(_data_model(True).dm["specimens"].index)
        assert set(table.columns) <= known
        mine = table[table["software_packages"].fillna("").str.contains("pmagpy_directions")]
        assert len(mine) > 0 and mine["lithologies"].notna().all()
        # every measured specimen has a row
        assert set(study.specimen_names) <= set(table["specimen"].astype(str))

    def test_locations_table_has_pole_and_geology(self, study):
        loc = study.locations_table(coord=COORD_GEOGRAPHIC)
        mine = loc[loc["software_packages"].fillna("").str.contains("pmagpy_directions")]
        assert len(mine) >= 1
        row = mine[mine["pole_comp_name"] == "A"].iloc[0]
        assert {"pole_lat", "pole_lon", "pole_alpha95", "pole_k", "pole_n_sites", "paleolat", "pole_reversed_perc"} <= set(loc.columns)
        assert "DE-VGP" in row["method_codes"] and row["pole_n_sites"] >= 2
        assert isinstance(row["geologic_classes"], str) and isinstance(row["lithologies"], str)
        assert "lat_s" in loc.columns and row["lat_s"] <= row["lat_n"]

    def test_site_rows_use_the_di_code_and_no_vgp_in_samples(self, study, dmag):
        sites = study.means_table("site", coord=COORD_GEOGRAPHIC)
        mine = sites[sites["software_packages"].fillna("").str.contains("pmagpy_directions")]
        assert mine["method_codes"].str.contains("DE-DI").all()
        samples = study.means_table("sample", coord=COORD_GEOGRAPHIC)
        assert not {"vgp_lat", "vgp_lon", "location"} & set(samples.columns)
        mine = samples[samples["software_packages"].fillna("").str.contains("pmagpy_directions")]
        if "lat" in samples.columns:            # a sample's own coordinates may be inherited, never the site's
            source = dmag._table("samples")
            assert mine["lat"].isna().all() or "lat" in source.columns

    def test_import_falls_back_to_other_coordinate_systems(self):
        data = DemagData.from_directory(DMAG_DIR)
        table = data.contribution.tables["specimens"]
        df = table.df
        tilt = pd.to_numeric(df["dir_tilt_correction"], errors="coerce")
        table.df = df[tilt == COORD_GEOGRAPHIC]              # only geographic rows remain
        n_geo = data.load_components_from_specimens_table()
        assert n_geo > 0
        data.clear_components()
        assert data.load_components_from_specimens_table(coord=COORD_SPECIMEN) == 0
        data.clear_components()
        assert data.load_components_from_specimens_table(coord=COORD_GEOGRAPHIC) == n_geo

    def test_validate_directory_reports_per_table(self, study, tmp_path):
        out = str(tmp_path)
        study.write_specimens(out)
        study.write_means("site", out, coord=COORD_GEOGRAPHIC)
        report = validate_directory(out)
        assert set(report) == {"specimens", "sites"}
        for result in report.values():
            assert result is None or {"bad_rows", "bad_cols", "missing_cols", "failing_items"} <= set(result)


class TestDefaultCoordinates:
    def _expected(self, data):
        cov = data.coord_coverage()
        if cov[COORD_TILT] >= 0.5:
            return COORD_TILT
        if cov[COORD_GEOGRAPHIC] >= 0.5:
            return COORD_GEOGRAPHIC
        return COORD_SPECIMEN

    def test_default_follows_orientation_and_bedding(self, dmag, mcmurdo):
        for data in (dmag, mcmurdo):
            assert data.default_coord() == self._expected(data)
        assert dmag.default_coord() == COORD_TILT            # azimuth/dip and bedding recorded
        # strip the bedding: geographic; strip the orientations: specimen
        from copy import deepcopy
        import numpy as np
        stripped = deepcopy(dmag)
        for sp in stripped.specimens.values():
            sp.steps["dec_t"] = np.nan
        assert stripped.default_coord() == COORD_GEOGRAPHIC
        for sp in stripped.specimens.values():
            sp.steps["dec_g"] = np.nan
        assert stripped.default_coord() == COORD_SPECIMEN

    def test_majority_rule_and_best_coord(self, dmag):
        from copy import deepcopy
        import numpy as np
        data = deepcopy(dmag)
        names = data.specimen_names
        for name in names[: int(0.6 * len(names))]:            # bedding missing for 60 % of the specimens
            data.specimens[name].steps["dec_t"] = np.nan
        assert data.default_coord() == COORD_GEOGRAPHIC
        assert data.best_coord(names[0], COORD_TILT) == COORD_GEOGRAPHIC
        assert data.best_coord(names[-1], COORD_TILT) == COORD_TILT
        data.specimens[names[0]].steps["dec_g"] = np.nan
        assert data.best_coord(names[0], COORD_TILT) == COORD_SPECIMEN
        assert data.best_coord(names[-1], COORD_SPECIMEN) == COORD_SPECIMEN     # never upgrades
