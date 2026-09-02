"""
pmagpy.magic_upload: the UI-free layer under the hub's Upload page.

A small MagIC directory is built in ``tmp_path`` for every test; MagIC's
validator is stood in for by a fake response except in one live test that
runs only with ``PMAGPY_NETWORK_TESTS=1``.
"""
import os

import pandas as pd
import pytest

from pmagpy import ipmag
from pmagpy import magic_project as mp
from pmagpy import magic_upload as mu


def write(directory, table, rows):
    df = pd.DataFrame(rows).fillna("")
    return mp.magic_write(os.path.join(str(directory), table + ".txt"), df, table)


@pytest.fixture
def study(tmp_path):
    """A location with two sites, one with a site mean, and a paleointensity specimen."""
    write(tmp_path, "locations", [{"location": "Zavkhan", "location_type": "Outcrop", "citations": "This study",
                                   "lat_s": "47.05", "lat_n": "47.10", "lon_w": "96.20", "lon_e": "96.30"}])
    write(tmp_path, "sites", [
        {"site": "Z11", "location": "Zavkhan", "lat": "47.05", "lon": "96.20", "lithologies": "Basalt",
         "dir_dec": "12.5", "dir_inc": "-40.2", "dir_n_samples": "6", "dir_k": "120", "dir_r": "5.96",
         "dir_alpha95": "4.2", "dir_tilt_correction": "100", "vgp_lat": "-62.1", "vgp_lon": "310.4"},
        {"site": "Z12", "location": "Zavkhan", "lat": "95", "lon": "96.30"},          # 95: off the planet
    ])
    write(tmp_path, "samples", [{"sample": "Z11.1", "site": "Z11", "azimuth": "10", "dip": "20"}])
    write(tmp_path, "specimens", [{"specimen": "Z11.1a", "sample": "Z11.1", "int_abs": "3.2e-5", "int_abs_sigma": "1e-6",
                                   "int_n_measurements": "8", "meas_step_min": "373", "meas_step_max": "773",
                                   "meas_step_unit": "K"}])
    write(tmp_path, "measurements", [{"measurement": "1", "experiment": "Z11.1a_LP-DIR-T", "specimen": "Z11.1a",
                                      "quality": "g"}])
    return str(tmp_path)


class TestPresentAndCheck:
    def test_present_tables_come_in_upload_order_and_skip_contribution(self, study):
        write(study, "contribution", [{"version": "1", "magic_version": "3.0"}])
        assert mu.present_tables(study) == ["locations", "sites", "samples", "specimens", "measurements"]
        assert mu.present_tables(os.path.join(study, "nowhere")) == []

    def test_check_offline_reports_every_table_and_names_the_bad_cell(self, study, capsys):
        findings = mu.check_offline(study)
        assert set(findings) == {"locations", "sites", "samples", "specimens", "measurements"}
        sites = findings["sites"]
        assert any(f.row == "Z12" and f.column == "lat" for f in sites)              # 95 is beyond the pole
        assert capsys.readouterr().out == ""                                          # the validator's narration is kept in


class TestUploadFile:
    def test_build_writes_one_file_named_for_the_location_with_every_table(self, study):
        up = mu.build_upload_file(study)
        assert up.tables == ["locations", "sites", "samples", "specimens", "measurements"]
        assert up.name.startswith("Zavkhan_") and up.name.endswith(".txt")
        assert os.path.dirname(up.path) == study and up.size > 0
        text = open(up.path, encoding="utf-8").read()
        assert text.splitlines()[0].split("\t") == ["tab ", "locations"]
        assert text.count(mu.UPLOAD_MARKER) == 4                                      # five tables, four separators
        assert "contribution" not in text.split(mu.UPLOAD_MARKER)[0]
        assert mu.is_upload_file(up.path)
        assert not mu.is_upload_file(os.path.join(study, "sites.txt"))                # a lone table is not an upload

    def test_a_second_build_keeps_the_first_and_upload_files_lists_newest_first(self, study):
        first = mu.build_upload_file(study)
        second = mu.build_upload_file(study)
        assert second.path != first.path and os.path.isfile(first.path)
        os.utime(second.path, (2e9, 2e9))                                             # make its age unambiguous
        assert mu.upload_files(study) == [second.name, first.name]

    def test_nothing_to_upload_is_an_error_not_a_file(self, tmp_path):
        with pytest.raises(ValueError):
            mu.build_upload_file(str(tmp_path))
        assert mu.upload_files(str(tmp_path)) == []


class TestOnlineReport:
    RESPONSE = {"status": True, "validation": {
        "errors": [{"table": "sites", "column": "lat", "message": "Value must be at most 90.", "rows": [2]},
                   {"table": "locations", "column": "lithologies", "message": "Missing required column", "rows": []},
                   "something the endpoint said without a table"],
        "warnings": [{"table": "sites", "column": "age", "message": "No age", "rows": ["1", "2"]}]}}

    def test_the_endpoint_reply_becomes_issues_by_table(self, monkeypatch, study):
        monkeypatch.setattr(ipmag, "validate_with_public_endpoint", lambda path, verbose=False: self.RESPONSE)
        report = mu.validate_online(os.path.join(study, "whatever.txt"))
        assert report.reached and not report.ok
        by_table = report.by_table()
        assert set(by_table) == {"sites", "locations", ""}
        assert by_table["sites"][0].rows == [2] and by_table["sites"][0].column == "lat"
        assert report.warnings[0].rows == [1, 2]                                      # strings from the wire become ints

    def test_a_clean_file_is_ok(self, monkeypatch):
        monkeypatch.setattr(ipmag, "validate_with_public_endpoint",
                            lambda path, verbose=False: {"status": True, "validation": {"errors": [], "warnings": []}})
        assert mu.validate_online("x.txt").ok

    def test_network_trouble_is_reported_not_raised(self, monkeypatch):
        def boom(path, verbose=False):
            raise ConnectionError("no route to host")
        monkeypatch.setattr(ipmag, "validate_with_public_endpoint", boom)
        report = mu.validate_online("x.txt")
        assert not report.reached and "no route to host" in report.trouble
        monkeypatch.setattr(ipmag, "validate_with_public_endpoint",
                            lambda path, verbose=False: {"status": False, "validation": [], "warnings": "Status code 502"})
        assert mu.validate_online("x.txt").trouble == "Status code 502"


class TestExport:
    def test_latex_tables_land_in_publication_tables(self, study):
        result = mu.export_tables(study, latex=True)
        names = sorted(os.path.basename(f) for f in result.files)
        assert names == ["directions.tex", "site_info.tex", "specimens.tex"]           # no intensities at site level, no criteria table
        assert all(os.path.dirname(f) == os.path.join(study, mu.EXPORT_DIR) for f in result.files)
        assert result.skipped == []
        directions = open(os.path.join(study, mu.EXPORT_DIR, "directions.tex")).read()
        assert "\\begin{document}\n" in directions and "Z11 & 100 & 12.5 & -40.2" in directions
        assert os.path.isfile(os.path.join(study, "specimens.txt"))                    # the MagIC table is untouched

    def test_excel_or_its_tab_delimited_stand_in_never_overwrites_a_magic_table(self, study):
        result = mu.export_tables(study)
        assert len(result.files) == 3
        assert all(f.endswith((".xlsx", ".tsv")) for f in result.files)
        assert "specimen" in open(os.path.join(study, "specimens.txt")).readline()     # still the MagIC header line

    def test_a_directory_without_directions_or_intensities_exports_site_info_only(self, tmp_path):
        write(tmp_path, "sites", [{"site": "A1", "location": "L", "lat": "1", "lon": "2"}])
        write(tmp_path, "specimens", [{"specimen": "A1a", "sample": "A1"}])
        result = mu.export_tables(str(tmp_path), latex=True)
        assert [os.path.basename(f) for f in result.files] == ["site_info.tex"]
        assert result.skipped == ["specimens"]


@pytest.mark.skipif(not os.environ.get("PMAGPY_NETWORK_TESTS"), reason="set PMAGPY_NETWORK_TESTS=1 to talk to EarthRef")
def test_live_magic_validates_the_small_study(study):
    up = mu.build_upload_file(study)
    report = mu.validate_online(up.path)
    assert report.reached
    assert any(i.table == "sites" and i.column == "lat" for i in report.errors)       # 95 is not a latitude anywhere
