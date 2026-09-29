"""
The export merge policy and the metadata a new result row inherits.

Regression tests for what the pre-beta review of PmagPy Directions found an
export doing to existing tables: deleting results it had not recomputed (the
tilt-corrected means of a study whose bedding it could not read), carrying an
age from one row and its unit from another, carrying the member list of a
mean that no longer exists, dropping site descriptions, averaging a site's
longitudes across conventions, and writing rows with blank names.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

import pmagpy.demag as dc
from pmagpy import magic_project as mp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
MCMURDO = os.path.join(REPO, "data_files", "3_0", "McMurdo")


class TestCarryMetadata:
    def test_an_age_and_its_unit_come_from_one_row(self):
        existing = pd.DataFrame({"site": ["s1", "s1"], "age": [np.nan, 1730.0],
                                 "age_unit": ["ka", "Years AD"], "lithologies": ["Basalt", np.nan]})
        new = pd.DataFrame({"site": ["s1"], "dir_dec": [10.0]})
        out = mp.carry_metadata(new, existing, "site")
        assert (out["age"].iloc[0], out["age_unit"].iloc[0]) == (1730.0, "Years AD")
        assert out["lithologies"].iloc[0] == "Basalt"

    def test_the_members_of_a_replaced_mean_are_not_carried(self):
        existing = pd.DataFrame({"site": ["s1"], "samples": ["a:b:c"], "lat": [10.0], "lon": [20.0]})
        new = pd.DataFrame({"site": ["s1"], "dir_dec": [10.0]})
        out = mp.carry_metadata(new, existing, "site")
        assert "samples" not in out.columns or out["samples"].isna().all()
        assert (out["lat"].iloc[0], out["lon"].iloc[0]) == (10.0, 20.0)

    def test_a_row_with_its_own_coordinates_keeps_them_both(self):
        existing = pd.DataFrame({"site": ["s1"], "lat": [10.0], "lon": [20.0]})
        new = pd.DataFrame({"site": ["s1"], "lat": [11.0], "lon": [np.nan]})
        out = mp.carry_metadata(new, existing, "site")
        assert out["lat"].iloc[0] == 11.0 and pd.isna(out["lon"].iloc[0])


class TestCarryAnnotations:
    def test_the_description_of_the_replaced_row_is_kept(self):
        existing = pd.DataFrame({"site": ["s1", "s1"], "dir_comp_name": ["A", "A"],
                                 "dir_tilt_correction": [0, 100],
                                 "description": ["basalt flow, geographic", "basalt flow, tilt"]})
        new = pd.DataFrame({"site": ["s1", "s1"], "dir_comp_name": ["A", "A"], "dir_tilt_correction": [100, 0]})
        out = mp.carry_annotations(new, existing, "site")
        assert list(out["description"]) == ["basalt flow, tilt", "basalt flow, geographic"]


class TestMergeResults:
    def test_rows_in_a_system_the_export_did_not_recompute_are_kept(self):
        existing = pd.DataFrame({"site": ["s1", "s1", "s2"], "dir_dec": [1.0, 2.0, 3.0],
                                 "dir_tilt_correction": [0, 100, 100], "method_codes": ["LP-DIR-AF"] * 3})
        new = pd.DataFrame({"site": ["s1"], "dir_dec": [5.0], "dir_tilt_correction": [0]})
        warnings = []
        out = mp.merge_results(existing, new, "site", owned=["s1", "s2"],
                               produced={"s1": {0}, "s2": {0}}, warnings=warnings)
        kept = out[out["dir_tilt_correction"] == 100]
        assert sorted(kept["dir_dec"]) == [2.0, 3.0]
        assert list(out.loc[out["dir_tilt_correction"] == 0, "dir_dec"]) == [5.0]
        assert warnings and "kept 2 existing tilt-corrected" in warnings[0]

    def test_without_produced_the_owned_rows_are_replaced(self):
        existing = pd.DataFrame({"site": ["s1", "s1"], "dir_dec": [1.0, 2.0], "dir_tilt_correction": [0, 100]})
        new = pd.DataFrame({"site": ["s1"], "dir_dec": [5.0], "dir_tilt_correction": [0]})
        out = mp.merge_results(existing, new, "site", owned=["s1"])
        assert list(out["dir_dec"]) == [5.0]

    def test_an_entity_left_without_results_keeps_one_metadata_row(self):
        existing = pd.DataFrame({"site": ["s1", "s1"], "dir_dec": [1.0, 2.0], "dir_tilt_correction": [0, 100],
                                 "age": [np.nan, 5.0], "age_unit": ["Ma", "ka"]})
        out = mp.merge_results(existing, pd.DataFrame(), "site", owned=["s1"])
        assert len(out) == 1 and (out["age"].iloc[0], out["age_unit"].iloc[0]) == (5.0, "ka")


class TestSitePositions:
    def test_longitude_conventions_are_one_meridian(self):
        coords = mp.build_site_coords(pd.DataFrame({"site": ["s", "s"], "lat": [47.0, 47.0],
                                                    "lon": [-91.73, 268.27]}), None)
        lat, lon = coords["s"]
        assert lat == pytest.approx(47.0) and lon % 360 == pytest.approx(268.27)

    def test_across_the_antimeridian(self):
        lat, lon = mp.mean_position([0.0, 0.0], [179.0, -179.0])
        assert abs(lat) < 1e-9 and abs(abs(lon) - 180.0) < 1e-9


class TestOrientationRows:
    def rows(self, *specs):
        return [dict(zip(("azimuth", "dip", "method_codes", "bed_dip_direction", "bed_dip"), spec)) for spec in specs]

    def test_the_highest_ranked_method_supplies_the_azimuth(self):
        warnings = []
        orient = mp.orientation_from_rows(self.rows((10.0, -30.0, "SO-MAG", np.nan, np.nan),
                                                    (12.0, -30.0, "SO-SUN", 90.0, 20.0)), "s", warnings=warnings)
        assert (orient.azimuth, orient.method_codes) == (12.0, ["SO-SUN"])
        assert warnings and "disagree" in warnings[0]

    def test_asc_and_pom_rows_never_supply_the_azimuth(self):
        orient = mp.orientation_from_rows(self.rows((99.0, -30.0, "SO-ASC", np.nan, np.nan),
                                                    (10.0, -30.0, "SO-MAG", np.nan, np.nan)), "s")
        assert orient.azimuth == 10.0

    def test_bedding_falls_back_to_the_site(self):
        orient = mp.orientation_from_rows(self.rows((10.0, -30.0, "SO-MAG", np.nan, np.nan)), "s",
                                          site_bedding=(45.0, 15.0))
        assert (orient.bed_dip_direction, orient.bed_dip) == (45.0, 15.0) and orient.has_tilt


@pytest.fixture(scope="module")
def mcmurdo_copy(tmp_path_factory):
    d = tmp_path_factory.mktemp("mc") / "McMurdo"
    shutil.copytree(MCMURDO, d)
    return str(d)


class TestDirectionsExport:
    def test_site_coordinates_are_written_as_the_table_has_them(self, mcmurdo_copy):
        data = dc.DemagData.from_directory(mcmurdo_copy)
        data.load_components_from_specimens_table()
        sites = data.means_table("site", coords=(dc.COORD_GEOGRAPHIC,))
        source = data._table("sites").drop_duplicates("site").set_index("site")
        written = sites.drop_duplicates("site").set_index("site")
        common = [s for s in written.index if s in source.index and not pd.isna(source.loc[s, "lat"])]
        assert common
        for s in common[:20]:
            assert float(written.loc[s, "lat"]) == float(source.loc[s, "lat"])
            assert float(written.loc[s, "lon"]) == float(source.loc[s, "lon"])

    def test_a_site_mean_lists_the_samples_it_averages(self, mcmurdo_copy):
        data = dc.DemagData.from_directory(mcmurdo_copy)
        data.load_components_from_specimens_table()
        means = data.mean_directions("site", coord=dc.COORD_GEOGRAPHIC)
        row = means.iloc[0]
        samples = row["samples"].split(":")
        assert len(samples) == row["dir_n_samples"]

    def test_a_single_specimen_site_has_no_vgp_error(self, mcmurdo_copy):
        data = dc.DemagData.from_directory(mcmurdo_copy)
        data.load_components_from_specimens_table()
        means = data.mean_directions("site", coord=dc.COORD_GEOGRAPHIC)
        single = means[(means["dir_n_specimens"] == 1) & means["vgp_lat"].notna()]
        if len(single):
            assert single["vgp_dp"].isna().all() and single["vgp_dm"].isna().all()

    def test_no_row_is_written_with_a_blank_name(self, mcmurdo_copy):
        data = dc.DemagData.from_directory(mcmurdo_copy)
        data.load_components_from_specimens_table()
        spec = next(iter(data.specimens.values()))
        spec.site = ""
        for level in ("sample", "site"):
            table = data.means_table(level, coords=(dc.COORD_GEOGRAPHIC,))
            assert (table[level].astype(str).str.strip() != "").all()
        locations = data.locations_table(coords=(dc.COORD_GEOGRAPHIC,))
        assert (locations["location"].astype(str).str.strip() != "").all()

    def test_a_lone_plane_is_not_a_site_mean(self):
        assert dc._is_lone_plane({"dir_n_specimens_lines": 0, "dir_n_specimens_planes": 1})
        assert not dc._is_lone_plane({"dir_n_specimens_lines": 0, "dir_n_specimens_planes": 2})
        assert not dc._is_lone_plane({"dir_n_specimens_lines": 1, "dir_n_specimens_planes": 1})


class TestRegressionsFromTheSecondSweep:
    def test_a_protocol_code_alone_is_not_a_directional_result(self):
        rows = pd.DataFrame({"specimen": ["a", "b"], "method_codes": ["LP-DIR-AF", "LP-DIR-AF:DE-BFL"],
                             "dir_dec": [np.nan, 10.0]})
        assert list(mp.directional_rows(rows)) == [False, True]

    def test_an_ambiguous_replaced_row_lends_nothing(self):
        existing = pd.DataFrame({"location": ["L", "L"], "dir_tilt_correction": [0, 0],
                                 "dir_polarity": ["n", "r"]})
        new = pd.DataFrame({"location": ["L"], "dir_tilt_correction": [0]})
        out = mp.carry_annotations(new, existing, "location")
        assert "dir_polarity" not in out.columns or out["dir_polarity"].isna().all()

    def test_blank_names_do_not_break_the_merge(self):
        existing = pd.DataFrame({"location": ["L", np.nan], "dir_tilt_correction": [0, 0], "description": ["x", "y"]})
        new = pd.DataFrame({"location": ["L"], "dir_tilt_correction": [0]})
        assert mp.carry_annotations(new, existing, "location")["description"].iloc[0] == "x"

    def test_originals_are_only_the_files_the_study_had(self, tmp_path):
        out = str(tmp_path)
        with open(os.path.join(out, "sites.txt"), "w") as fh:
            fh.write("v0")
        with open(os.path.join(out, "made_by_the_app.redo"), "w") as fh:
            fh.write("r0")
        with mp.StagedExport(out, backup=os.path.join(out, "backup"), originals={"sites.txt"}) as stage:
            for name in ("sites.txt", "made_by_the_app.redo"):
                mp.atomic_write_text(os.path.join(stage.dir, name), "v1")
        assert os.path.exists(os.path.join(out, "backup", "sites.txt"))
        assert not os.path.exists(os.path.join(out, "backup", "made_by_the_app.redo"))
        assert os.path.exists(os.path.join(out, "backup", "previous", "made_by_the_app.redo"))


class TestPolarityIsTheAnalystsCall:
    def test_the_rule_is_measured_from_the_reference_pole(self):
        assert dc.vgp_polarity(60.0, 10.0) == "n"                           # 30 degrees from the present pole
        assert dc.vgp_polarity(-70.0, 10.0) == "r"
        assert dc.vgp_polarity(60.0, 10.0, reference=(0.0, 10.0)) == "t"     # 60 degrees from that pole
        assert dc.vgp_polarity(60.0, 10.0, reference=(-60.0, 190.0)) == "r"  # at its antipode
        assert dc.vgp_polarity(60.0, np.nan, reference=(0.0, 10.0)) == ""    # a longitude is needed then

    def test_no_polarity_unless_asked(self, mcmurdo_copy):
        data = dc.DemagData.from_directory(mcmurdo_copy)
        data.load_components_from_specimens_table()
        plain = data.means_table("site", coords=(dc.COORD_GEOGRAPHIC,))
        mine = plain["software_packages"].astype(str).str.contains(dc.APP_ID, na=False)
        assert "dir_polarity" not in plain.columns or plain.loc[mine, "dir_polarity"].isna().all()
        asked = data.means_table("site", coords=(dc.COORD_GEOGRAPHIC,), polarity_pole=dc.PRESENT_NORTH_POLE)
        mine = asked["software_packages"].astype(str).str.contains(dc.APP_ID, na=False) & asked["vgp_lat"].notna()
        assert set(asked.loc[mine, "dir_polarity"]) <= {"n", "r", "t"} and mine.any()
        pole = data.locations_table(coords=(dc.COORD_GEOGRAPHIC,))
        mine = pole["software_packages"].astype(str).str.contains(dc.APP_ID, na=False)
        assert "dir_polarity" not in pole.columns or pole.loc[mine, "dir_polarity"].isna().all()

    def test_an_old_polarity_is_not_carried_to_the_mean_that_replaces_it(self):
        existing = pd.DataFrame({"site": ["s1"], "dir_comp_name": ["A"], "dir_tilt_correction": [0],
                                 "dir_polarity": ["n"], "description": ["flow"]})
        new = pd.DataFrame({"site": ["s1"], "dir_comp_name": ["A"], "dir_tilt_correction": [0]})
        out = mp.carry_annotations(new, existing, "site")
        assert out["description"].iloc[0] == "flow"
        assert "dir_polarity" not in out.columns or out["dir_polarity"].isna().all()
