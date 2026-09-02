"""
pmagpy.magic_metadata: the UI-free layer under the hub's Metadata page.

Every test builds a small MagIC directory in ``tmp_path`` so the behaviour
being checked is visible in the test itself; nothing depends on the shipped
example data except the data model, which is read offline.
"""
import os

import pandas as pd
import pytest

from pmagpy import magic_metadata as mm
from pmagpy import magic_project as mp


def write(directory, table, rows):
    """Write ``rows`` (list of dicts) as ``<table>.txt`` in the MagIC 3 layout."""
    df = pd.DataFrame(rows).fillna("")
    return mp.magic_write(os.path.join(str(directory), table + ".txt"), df, table)


@pytest.fixture
def study(tmp_path):
    """One location, two sites, three samples, specimens and a few measurements."""
    write(tmp_path, "locations", [{"location": "Zavkhan", "location_type": "Outcrop", "citations": "This study"}])
    write(tmp_path, "sites", [
        {"site": "Z11", "location": "Zavkhan", "lat": "47.05", "lon": "96.20", "lithologies": "Basalt"},
        {"site": "Z12", "location": "Zavkhan", "lat": "47.10", "lon": "96.30", "lithologies": ""},
    ])
    write(tmp_path, "samples", [
        {"sample": "Z11.1", "site": "Z11", "azimuth": "10", "dip": "20"},
        {"sample": "Z11.2", "site": "Z11", "azimuth": "11", "dip": "21"},
        {"sample": "Z13.1", "site": "Z13", "azimuth": "12", "dip": "22"},   # Z13 has no sites row
    ])
    write(tmp_path, "specimens", [{"specimen": "Z11.1a", "sample": "Z11.1"}])
    write(tmp_path, "measurements", [
        {"measurement": "1", "experiment": "Z11.1a_LP-DIR-T", "specimen": "Z11.1a", "quality": "g"},
        {"measurement": "2", "experiment": "Z11.2a_LP-DIR-T", "specimen": "Z11.2a", "quality": "g"},
    ])
    return str(tmp_path)


# ---------------------------------------------------------------------------
# The data model as columns
# ---------------------------------------------------------------------------
class TestColumns:
    def test_a_column_carries_type_vocabulary_bounds_and_requiredness(self):
        lat = mm.column("sites", "lat")
        assert lat.is_numeric and lat.minimum == -90 and lat.maximum == 90 and lat.unit
        assert lat.required                                            # MagIC wants every site placed
        assert mm.column("sites", "height").required is False
        site = mm.column("sites", "site")
        assert site.required and site.label == "Site Name"
        litho = mm.column("sites", "lithologies")
        assert litho.is_list and litho.required and "Basalt" in litho.vocabulary
        quality = mm.column("sites", "result_quality")
        assert set(quality.vocabulary) >= {"g", "b"}
        assert mm.column("sites", "no_such_column") is None

    def test_required_columns_of_each_table_are_known(self):
        assert "lithologies" in mm.required_columns("sites")
        assert "method_codes" in mm.required_columns("samples") and "azimuth" not in mm.required_columns("samples")
        assert "location" in mm.required_columns("locations")

    def test_columns_are_in_data_model_order_and_cached(self):
        first = mm.columns("specimens")
        assert list(first) == sorted(first, key=lambda c: first[c].position)
        assert mm.columns("specimens") is first


class TestOrderColumns:
    def test_name_then_parent_then_required_then_the_rest_then_unknown(self):
        order = mm.order_columns("samples", ["dip", "my_note", "azimuth", "sample", "site", "height"])
        assert order[:2] == ["sample", "site"]
        assert order[-1] == "my_note"                               # not in the model: kept, last
        required = mm.required_columns("samples")
        assert all(c in order for c in required)                    # present or not
        model_pos = {c: col.position for c, col in mm.columns("samples").items()}
        middle = order[2:-1]
        assert middle == sorted(middle, key=model_pos.__getitem__)

    def test_ages_leads_with_the_four_levels(self):
        order = mm.order_columns("ages", ["age", "site", "age_unit"])
        assert order[:4] == ["location", "site", "sample", "specimen"]
        assert "age" in order and "age_unit" in order

    def test_locations_has_no_parent(self):
        assert mm.order_columns("locations", ["location"])[0] == "location"
        assert "site" not in mm.order_columns("locations", ["location"])


# ---------------------------------------------------------------------------
# Reading tables for editing
# ---------------------------------------------------------------------------
class TestEditorFrame:
    def test_cells_come_back_as_the_file_has_them(self, study):
        frame = mm.editor_frame(study, "sites")
        assert frame.exists and frame.key == "site"
        assert frame.df.loc[frame.df.site == "Z11", "lat"].iloc[0] == "47.05"
        assert all(isinstance(v, str) for v in frame.df.to_numpy().ravel())
        assert list(frame.df.columns[:2]) == ["site", "location"]

    def test_a_site_the_samples_name_gets_a_stub_row(self, study):
        frame = mm.editor_frame(study, "sites")
        assert frame.stubs == ["Z13"]
        stub = frame.df[frame.df.site == "Z13"].iloc[0]
        assert stub["lat"] == "" and stub["location"] == ""      # samples carry no location

    def test_a_specimen_only_in_measurements_gets_a_stub_row(self, study):
        frame = mm.editor_frame(study, "specimens")
        assert frame.stubs == ["Z11.2a"]
        assert set(frame.df.specimen) == {"Z11.1a", "Z11.2a"}

    def test_a_missing_table_is_built_from_the_names_below_it(self, study):
        os.remove(os.path.join(study, "specimens.txt"))
        frame = mm.editor_frame(study, "specimens")
        assert frame.exists is False
        assert sorted(frame.stubs) == ["Z11.1a", "Z11.2a"]
        assert "sample" in frame.df.columns and (frame.df["sample"] == "").all()

    def test_a_file_that_is_not_a_magic_table_reads_as_absent(self, tmp_path):
        (tmp_path / "sites.txt").write_text("site\tlat\nZ1\t1\n")
        assert mm.read_table(str(tmp_path), "sites") is None

    def test_the_ages_table_is_owed_nothing(self, study):
        frame = mm.editor_frame(study, "ages")
        assert frame.exists is False and frame.stubs == []
        assert list(frame.df.columns[:4]) == ["location", "site", "sample", "specimen"]


# ---------------------------------------------------------------------------
# Saving
# ---------------------------------------------------------------------------
class TestSaveTable:
    def test_empty_columns_and_nameless_rows_are_left_out(self, study):
        frame = mm.editor_frame(study, "sites")
        df = frame.df.copy()
        df.loc[df.site == "Z13", "location"] = "Zavkhan"
        df = pd.concat([df, pd.DataFrame([mm.blank_row("sites", df.columns)])], ignore_index=True)
        assert (df["geologic_classes"] == "").all()
        mm.save_table(study, "sites", df)
        back = mm.read_table(study, "sites")
        assert list(back.site) == ["Z11", "Z12", "Z13"]                # the blank row is gone
        assert "geologic_classes" not in back.columns
        assert "lithologies" in back.columns                           # one value keeps the column
        assert back.loc[back.site == "Z13", "location"].iloc[0] == "Zavkhan"

    def test_the_original_is_backed_up_once(self, study):
        original = open(os.path.join(study, "sites.txt")).read()
        frame = mm.editor_frame(study, "sites")
        mm.save_table(study, "sites", frame.df)
        assert mm.backup_exists(study, "sites")
        backup = os.path.join(study, mm.BACKUP_DIR, "sites.txt")
        assert open(backup).read() == original
        df = frame.df.copy()
        df.loc[0, "lat"] = "1"
        mm.save_table(study, "sites", df)
        assert open(backup).read() == original                          # the second save does not overwrite it

    def test_a_table_with_nothing_left_is_removed(self, study):
        df = mm.editor_frame(study, "specimens").df
        df["specimen"] = ""
        mm.save_table(study, "specimens", df)
        assert not os.path.exists(os.path.join(study, "specimens.txt"))
        assert mm.backup_exists(study, "specimens")

    def test_ages_rows_need_a_level_name(self, study):
        df = pd.DataFrame([{"location": "", "site": "Z11", "sample": "", "specimen": "", "age": "780", "age_unit": "Ma"},
                           {"location": "", "site": "", "sample": "", "specimen": "", "age": "1", "age_unit": "Ma"}])
        mm.save_table(study, "ages", df)
        back = mm.read_table(study, "ages")
        assert len(back) == 1 and back.site.iloc[0] == "Z11"
        assert "location" not in back.columns

    def test_the_saved_table_reads_back_through_the_contribution(self, study):
        frame = mm.editor_frame(study, "sites")
        df = frame.df.copy()
        df.loc[df.site == "Z13", "location"] = "Zavkhan"
        mm.save_table(study, "sites", df)
        from pmagpy import contribution_builder as cb
        con = cb.Contribution(study, read_tables=["sites"], dmodel=mp.data_model(True))
        assert list(con.tables["sites"].df.index) == ["Z11", "Z12", "Z13"]


# ---------------------------------------------------------------------------
# Filling in what the other tables know
# ---------------------------------------------------------------------------
class TestFilling:
    def test_defaults_go_into_blank_cells_only(self):
        df = pd.DataFrame({"site": ["a", "b"], "citations": ["", "Smith 2020"], "result_quality": ["", ""]})
        out, n = mm.fill_defaults(df)
        assert n == 3
        assert list(out.citations) == ["This study", "Smith 2020"]
        assert list(out.result_quality) == ["g", "g"]
        assert df.citations.iloc[0] == ""                              # the input is not touched

    def test_a_blank_row_carries_the_defaults(self):
        row = mm.blank_row("sites", ["site", "citations", "lat", "result_type"])
        assert row == {"site": "", "citations": "This study", "lat": "", "result_type": "i"}

    def test_location_bounds_come_from_the_site_coordinates(self, study):
        assert mm.location_bounds(study) == {"Zavkhan": {"lat_n": "47.1", "lat_s": "47.05",
                                                         "lon_e": "96.3", "lon_w": "96.2"}}

    def test_bounds_fall_back_to_samples_when_sites_have_none(self, study):
        sites = mm.read_table(study, "sites").drop(columns=["lat", "lon"])
        mm.save_table(study, "sites", sites, backup=False)
        samples = mm.read_table(study, "samples")
        samples["location"] = "Zavkhan"
        samples["lat"] = ["1", "2", "3"]
        samples["lon"] = ["10", "20", "30"]
        mm.save_table(study, "samples", samples, backup=False)
        assert mm.location_bounds(study)["Zavkhan"] == {"lat_n": "3", "lat_s": "1", "lon_e": "30", "lon_w": "10"}

    def test_fill_location_bounds_respects_what_is_there(self, study):
        df = pd.DataFrame([{"location": "Zavkhan", "lat_n": "48", "lat_s": "", "lon_e": "", "lon_w": ""},
                           {"location": "Elsewhere", "lat_n": "", "lat_s": "", "lon_e": "", "lon_w": ""}])
        out, n = mm.fill_location_bounds(study, df)
        assert n == 3
        assert out.loc[0, "lat_n"] == "48" and out.loc[0, "lat_s"] == "47.05"
        assert out.loc[1, "lat_n"] == ""                               # no sites: nothing to say

    def test_copy_down_fills_blank_cells_from_the_parent(self, study):
        frame = mm.editor_frame(study, "samples")
        df = frame.df.copy()
        df["lat"] = ["", "46.0", ""]
        out, n = mm.fill_from_parent(study, "samples", df, ["lat", "lon", "lithologies"])
        by = out.set_index("sample")
        assert by.loc["Z11.1", "lat"] == "47.05" and by.loc["Z11.1", "lon"] == "96.20"
        assert by.loc["Z11.2", "lat"] == "46.0"                        # already had one
        assert by.loc["Z13.1", "lat"] == ""                            # its site has no row
        assert by.loc["Z11.1", "lithologies"] == "Basalt"
        assert n == 1 + 2 + 2                                          # lat: Z11.1 only; lon and lithologies: both Z11 samples

    def test_copy_down_counts_only_cells_it_filled(self, study):
        df = mm.editor_frame(study, "samples").df
        out, n = mm.fill_from_parent(study, "samples", df, ["lon"])
        assert n == 2                                                  # Z11.1 and Z11.2; Z13 has no site row
        assert list(out.lon) == ["96.20", "96.20", ""]

    def test_locations_have_no_parent_to_copy_from(self, study):
        df = mm.editor_frame(study, "locations").df
        out, n = mm.fill_from_parent(study, "locations", df, ["lat"])
        assert n == 0 and out.equals(df)


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------
class TestCheckTable:
    def test_findings_name_the_cell_and_the_missing_required_columns(self, study):
        sites = mm.read_table(study, "sites")
        sites.loc[0, "lat"] = "95"
        mm.save_table(study, "sites", sites, backup=False)
        findings = mm.check_table(study, "sites")
        cells = [f for f in findings if f.row]
        assert any(f.row == "Z11" and f.column == "lat" for f in cells), findings
        table_wide = {f.column for f in findings if not f.row and f.column}
        assert "geologic_classes" in table_wide and "geologic_types" in table_wide
        assert all(f.problem == "required column, not in the table" for f in findings if not f.row and f.column)

    def test_a_table_the_validator_likes_has_no_findings(self, tmp_path):
        write(tmp_path, "locations", [{"location": "L", "location_type": "Outcrop", "lat_n": "1", "lat_s": "0",
                                       "lon_e": "1", "lon_w": "0", "geologic_classes": "Igneous",
                                       "lithologies": "Basalt", "age": "1", "age_unit": "Ma",
                                       "citations": "This study", "method_codes": "GM-ARAR"}])
        assert mm.check_table(str(tmp_path), "locations") == []

    def test_an_absent_table_has_no_findings(self, study):
        assert mm.check_table(study, "ages") == []


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------
@pytest.fixture
def judged(tmp_path):
    """Specimens with directional statistics and a criteria table that judges them."""
    write(tmp_path, "specimens", [
        {"specimen": "a", "dir_mad_free": "2.5", "dir_n_measurements": "8", "dir_polarity": "n"},
        {"specimen": "b", "dir_mad_free": "7.0", "dir_n_measurements": "8", "dir_polarity": "r"},
        {"specimen": "c", "dir_mad_free": "4.0", "dir_n_measurements": "3", "dir_polarity": "n"},
        {"specimen": "d", "dir_mad_free": "", "dir_n_measurements": "5", "dir_polarity": ""},
    ])
    write(tmp_path, "criteria", [
        {"criterion": "DE-SPEC", "table_column": "specimens.dir_mad_free", "criterion_operation": "<=", "criterion_value": "5"},
        {"criterion": "DE-SPEC", "table_column": "specimens.dir_n_measurements", "criterion_operation": ">=", "criterion_value": "4"},
        {"criterion": "NPOLE", "table_column": "specimen.dir_polarity", "criterion_operation": "=", "criterion_value": "n"},
        {"criterion": "DE-SITE", "table_column": "sites.dir_k", "criterion_operation": ">=", "criterion_value": "50"},
        {"criterion": "IE-SPEC", "table_column": "specimens.int_b_beta", "criterion_operation": "<=", "criterion_value": "0.1"},
    ])
    return str(tmp_path)


class TestCriteria:
    def test_the_criteria_table_is_edited_like_the_others(self, judged):
        assert "criteria" in mm.TABLES
        frame = mm.editor_frame(judged, "criteria")
        assert list(frame.df.columns[:4]) == ["criterion", "table_column", "criterion_operation", "criterion_value"]
        assert frame.stubs == [] and frame.exists is True and len(frame.df) == 5
        assert mm.required_columns("criteria") == ["criterion", "table_column", "criterion_operation", "criterion_value"]
        assert mm.column("criteria", "criterion_operation").vocabulary[:5] == ("<", "<=", "=", ">", ">=")
        assert mm.column("criteria", "criterion").unit == ""          # the model has no unit column here
        fresh = mm.editor_frame(judged + "/nowhere", "criteria")
        assert list(fresh.df.columns) == list(mm.CRITERIA_COLUMNS) and fresh.exists is False

    def test_saving_drops_rows_with_nothing_in_their_required_cells(self, judged):
        df = mm.editor_frame(judged, "criteria").df
        assert "citations" not in df.columns                      # not in the file, not required: added on request
        df["citations"] = ""
        df = pd.concat([df, pd.DataFrame([mm.blank_row("criteria", df.columns)])], ignore_index=True)
        assert df.iloc[-1]["citations"] == "This study" and df.iloc[-1]["criterion"] == ""
        mm.save_table(judged, "criteria", df, backup=False)
        assert len(mm.read_table(judged, "criteria")) == 5

    def test_default_criteria_are_pmagpy_defaults_in_the_3_0_vocabulary(self):
        from pmagpy import pmag, magic_project as mp
        df = mm.default_criteria()
        assert list(df.columns) == list(mm.CRITERIA_COLUMNS)
        assert set(df.criterion) == {"DE-SPEC", "DE-SAMP", "DE-SITE", "IE-SPEC", "IE-SITE"}
        assert (df.citations == "This study").all()
        # every 2.5 default that MagIC's criteria_map translates is here, with its value and operation
        crit_map = mp.data_model(True).crit_map.dropna()
        legacy = {k: v for k, v in pmag.default_criteria(0)[0].items() if v and k in crit_map.index}
        legacy = {k: v for k, v in legacy.items() if k not in ("pmag_criteria_code", "criteria_definition", "er_citation_names")}
        ours = {(r.table_column, r.criterion_operation): r.criterion_value for r in df.itertuples()}
        for key, value in legacy.items():
            mapped = crit_map.loc[key]["criteria_map"]
            assert ours[(mapped["table_column"], mapped["criterion_operation"])] == value, key
        assert len(ours) == len({(m["criteria_map"]["table_column"], m["criteria_map"]["criterion_operation"])
                                 for m in (crit_map.loc[k] for k in legacy)})

    def test_adding_defaults_skips_the_rows_already_there(self, judged):
        df = mm.editor_frame(judged, "criteria").df
        out, n = mm.add_default_criteria(df)
        assert n == len(mm.default_criteria()) - 3           # DE-SPEC mad_free, DE-SITE dir_k and IE-SPEC b_beta are there
        assert len(out) == 5 + n and list(out.columns[:4]) == list(mm.CRITERIA_COLUMNS[:4])
        again, m = mm.add_default_criteria(out)
        assert m == 0 and len(again) == len(out)

    def test_table_columns_name_every_result_column(self):
        cols = mm.table_columns()
        assert "specimens.dir_mad_free" in cols and "sites.dir_k" in cols and "measurements.treat_ac_field" in cols
        assert cols.index("specimens.specimen") < cols.index("sites.site")
        assert mm.split_table_column("specimens.dir_mad_free") == ("specimens", "dir_mad_free", "")
        table, column, slip = mm.split_table_column("site.dir_polarity")
        assert (table, column) == ("sites", "dir_polarity") and "not 'site'" in slip
        assert mm.split_table_column("dir_mad_free")[2] and mm.split_table_column("moons.phase")[2]

    def test_criterion_mask_reads_numbers_and_text(self):
        s = pd.Series(["2.5", "7", "", "abc"])
        passing, blank, problem = mm.criterion_mask(s, "<=", "5")
        assert list(passing) == [True, False, False, False] and list(blank) == [False, False, True, False] and problem == ""
        assert list(mm.criterion_mask(s, ">", "5")[0]) == [False, True, False, False]
        assert list(mm.criterion_mask(pd.Series(["n", "r", "", "n"]), "=", "n")[0]) == [True, False, False, True]
        assert list(mm.criterion_mask(pd.Series(["5.0", "5", "6"]), "=", "5")[0]) == [True, True, False]
        assert list(mm.criterion_mask(pd.Series(["LP-DIR-T", "LP-PI-TRM", ""]), "contains", "DIR")[0]) == [True, False, False]
        assert list(mm.criterion_mask(pd.Series(["LP-DIR-T", "LP-PI-TRM", ""]), "does not contain", "DIR")[0]) == [False, True, False]
        assert list(mm.criterion_mask(pd.Series(["mc01a", "sc01a"]), "begins with", "mc")[0]) == [True, False]
        assert "not a number" in mm.criterion_mask(s, "<", "five")[2]
        assert "not a criterion operation" in mm.criterion_mask(s, "approximately", "5")[2]

    def test_check_criteria_counts_passing_and_blank_rows_and_names_what_it_cannot_judge(self, judged):
        df = mm.editor_frame(judged, "criteria").df
        checks = {c.table_column: c for c in mm.check_criteria(judged, df)}
        mad = checks["specimens.dir_mad_free"]
        assert (mad.rows, mad.passing, mad.blank, mad.failing) == (4, 2, 1, 1) and mad.problem == ""
        assert mad.summary() == "2 of 4 pass, 1 blank"
        assert checks["specimens.dir_n_measurements"].passing == 3
        polarity = checks["specimen.dir_polarity"]
        assert polarity.table == "sites" or polarity.table == "specimens"
        assert (polarity.passing, polarity.blank) == (2, 1) and "not 'specimen'" in polarity.note and polarity.problem == ""
        assert checks["sites.dir_k"].problem == "no sites.txt in the directory"
        assert checks["specimens.int_b_beta"].problem == "specimens.txt has no column int_b_beta"
        blank = pd.concat([df, pd.DataFrame([{c: "" for c in df.columns}])], ignore_index=True)
        assert len(mm.check_criteria(judged, blank)) == 5                     # an empty row is not a criterion

    def test_passing_rows_applies_the_criteria_aimed_at_one_table(self, judged):
        spec = mm.read_table(judged, "specimens")
        crit = mm.read_table(judged, "criteria")
        ok = mm.passing_rows(spec, crit, "specimens", "DE-SPEC")
        assert list(spec.specimen[ok]) == ["a"]                                # b: MAD 7; c: 3 steps; d: no MAD
        lenient = mm.passing_rows(spec, crit, "specimens", "DE-SPEC", blank_fails=False)
        assert list(spec.specimen[lenient]) == ["a", "d"]
        assert not mm.passing_rows(spec, crit, "specimens").any()            # IE-SPEC names a column the table lacks
        assert mm.passing_rows(spec, crit, "locations").all()                # nothing aimed at the frame's table
        assert list(spec.specimen[mm.passing_rows(spec, crit, "specimens", "NPOLE")]) == ["a", "c"]


def test_plain_column_name_strips_the_validators_decoration():
    assert mp.plain_column_name("value_pass_lat_checkMax") == "lat"
    assert mp.plain_column_name("value_pass_lithologies_cv2") == "lithologies"
    assert mp.plain_column_name("presence_pass_site_required") == "site"
    assert mp.plain_column_name("type_pass_dip_test_type") == "dip"
    assert mp.plain_column_name("lat") == "lat"
