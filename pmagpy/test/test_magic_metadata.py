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


def test_plain_column_name_strips_the_validators_decoration():
    assert mp.plain_column_name("value_pass_lat_checkMax") == "lat"
    assert mp.plain_column_name("value_pass_lithologies_cv2") == "lithologies"
    assert mp.plain_column_name("presence_pass_site_required") == "site"
    assert mp.plain_column_name("type_pass_dip_test_type") == "dip"
    assert mp.plain_column_name("lat") == "lat"
