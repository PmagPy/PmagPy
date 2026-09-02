"""Tests for the MagIC download layer in pmagpy.magic_project.

    pytest pmagpy/test/test_magic_project.py -q

Everything runs offline against a small contribution file written here, in the
shape EarthRef serves (a byte-order mark, CRLF line ends, ``tab delimited``
headers, ``>>>>>>>>>>`` separators). One live test fetches the smallest of the
group's contributions and runs only with ``PMAGPY_NETWORK_TESTS=1``.
"""
import os

import pandas as pd
import pytest

from pmagpy import magic_project as mp

CONTRIBUTION = (
    "tab delimited\tcontribution\n"
    "id\tversion\ttimestamp\tcontributor\tdata_model_version\treference\tlab_names\n"
    "20549\t1\t2025-07-14T18:00:00.000Z\t@yiming_zhang\t3.0\t10.1029/2025TC009333\tUC Berkeley:IRM\n"
    ">>>>>>>>>>\n"
    "tab delimited\tsites\n"
    "site\tlocation\tlat\tlon\n"
    "S1\tL\t44.98\t-93.23\n"
    ">>>>>>>>>>\n"
    "tab delimited\tspecimens\n"
    "specimen\tsample\n"
    "S1-1a\tS1-1\n"
    ">>>>>>>>>>\n"
    "tab delimited\tmeasurements\n"
    "measurement\texperiment\tspecimen\tmethod_codes\ttreat_temp\tdir_dec\tdir_inc\tmagn_moment\n"
    "1\tS1-1a_LP-DIR-T\tS1-1a\tLT-NO\t273\t10.0\t45.0\t1e-8\n"
    "2\tS1-1a_LP-DIR-T\tS1-1a\tLT-T-Z\t373\t11.0\t44.0\t9e-9\n"
)
AS_SERVED = "﻿" + CONTRIBUTION.replace("\n", "\r\n")
NO_ID = "﻿" + ("tab delimited\tcontribution\r\ndescription\r\nan older contribution\r\n>>>>>>>>>>\r\n"
                    + CONTRIBUTION.split(">>>>>>>>>>\n", 1)[1].replace("\n", "\r\n"))


class TestParseReference:
    @pytest.mark.parametrize("text, expected", [
        ("20340", ("id", "20340")),
        ("  MagIC 20340 ", ("id", "20340")),
        ("https://earthref.org/MagIC/20340/", ("id", "20340")),
        ("10.7288/V4/MAGIC/20340", ("id", "20340")),
        ("doi:10.7288/v4/magic/16403", ("id", "16403")),
        ("10.1130/G53450.1", ("doi", "10.1130/G53450.1")),
        ("https://doi.org/10.1029/2021GC009909", ("doi", "10.1029/2021GC009909")),
        ("doi: 10.1002/2013GC005180", ("doi", "10.1002/2013GC005180")),
    ])
    def test_ids_and_dois_in_the_forms_people_paste(self, text, expected):
        assert mp.parse_contribution_reference(text) == expected

    @pytest.mark.parametrize("text", ["", "McMurdo", "10.1130", "https://earthref.org/MagIC/"])
    def test_anything_else_is_refused_with_the_text_quoted(self, text):
        with pytest.raises(ValueError, match="is not a MagIC contribution ID or a DOI"):
            mp.parse_contribution_reference(text)


class TestReadingTheFile:
    def test_tables_and_the_contribution_row_survive_the_bom_and_crlf(self):
        assert mp.contribution_tables(AS_SERVED) == ["contribution", "sites", "specimens", "measurements"]
        ref = mp.describe_contribution(AS_SERVED)
        assert ref == mp.ContributionRef(id=20549, version=1, doi="10.1029/2025TC009333", contributor="@yiming_zhang",
                                         timestamp="2025-07-14T18:00:00.000Z", lab_names=("UC Berkeley", "IRM"))
        assert ref.label == "MagIC contribution 20549 (version 1)"

    def test_pmagpy_written_files_say_tab_not_tab_delimited(self):
        assert mp.contribution_tables("tab\tsites\nsite\nS1\n") == ["sites"]

    def test_a_contribution_row_without_an_id_describes_as_id_0(self):
        assert mp.describe_contribution(NO_ID) == mp.ContributionRef(id=0)
        assert mp.describe_contribution("no tables here") == mp.ContributionRef(id=0)


class TestUnpacking:
    def test_tables_become_files_a_magic_directory_reads(self, tmp_path):
        out = tmp_path / "new"                                       # created on the way
        tables = mp.unpack_contribution(AS_SERVED, str(out))
        assert tables == ["contribution", "sites", "specimens", "measurements"]
        assert sorted(os.listdir(out)) == ["contribution.txt", "measurements.txt", "sites.txt", "specimens.txt"]
        meas = pd.read_csv(out / "measurements.txt", sep="\t", skiprows=1)
        assert list(meas["treat_temp"]) == [273, 373]
        contrib = pd.read_csv(out / "contribution.txt", sep="\t", skiprows=1, dtype=str)
        assert contrib.loc[0, "id"] == "20549" and contrib.loc[0, "reference"] == "10.1029/2025TC009333"

    def test_the_id_it_was_fetched_by_is_written_when_the_row_lacks_one(self, tmp_path):
        mp.unpack_contribution(NO_ID, str(tmp_path), magic_id=16403)
        contrib = pd.read_csv(tmp_path / "contribution.txt", sep="\t", skiprows=1, dtype=str)
        assert contrib.loc[0, "id"] == "16403" and contrib.loc[0, "description"] == "an older contribution"
        assert "doi" not in contrib.columns                          # nothing invented

    def test_text_without_tables_is_refused_before_anything_is_written(self, tmp_path):
        with pytest.raises(mp.MagicDownloadError, match="no tables"):
            mp.unpack_contribution("<html>not found</html>", str(tmp_path / "x"))
        assert not (tmp_path / "x").exists()


class FakeResponse:
    def __init__(self, status_code, payload=None, text="", reason=""):
        self.status_code, self._payload, self.text, self.reason = status_code, payload, text, reason

    def json(self):
        return self._payload


class TestTalkingToMagic:
    ROWS = [
        {"id": 19390, "version": 1, "reference": "10.1130/B36634.1", "contributor": "@polarwander",
         "timestamp": "2022-01-01T00:00:00Z", "lab_names": ["UC Berkeley"]},
        {"id": 20614, "version": 2, "reference": "10.1130/B36634.1", "contributor": "@polarwander",
         "timestamp": "2025-01-01T00:00:00Z", "lab_names": ["UC Berkeley"]},
        {"id": 11111, "version": 1, "reference": "10.1130/B36634.2", "contributor": "@someone",
         "timestamp": "", "lab_names": []},                            # the phrase search also matches this one
    ]

    def test_find_keeps_only_that_doi_newest_version_first(self, monkeypatch):
        import requests
        seen = {}

        def get(url, params=None, timeout=None):
            seen.update(url=url, params=params)
            return FakeResponse(200, {"results": self.ROWS})
        monkeypatch.setattr(requests, "get", get)
        found = mp.find_contributions("10.1130/B36634.1")
        assert [r.id for r in found] == [20614, 19390]
        assert found[0].version == 2 and found[0].lab_names == ("UC Berkeley",)
        assert seen["url"].endswith("/search/contributions") and seen["params"]["query"] == '"10.1130/B36634.1"'

    def test_find_with_nothing_matching_is_an_empty_list_not_an_error(self, monkeypatch):
        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(204))
        assert mp.find_contributions("10.1130/nothing") == []

    def test_fetch_returns_the_text_and_names_the_id_when_there_is_none(self, monkeypatch):
        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(200, text=AS_SERVED))
        assert mp.fetch_contribution(20549) == AS_SERVED
        monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(204))
        with pytest.raises(mp.MagicDownloadError, match="no public contribution with ID 99999999"):
            mp.fetch_contribution(99999999)
        monkeypatch.setattr(requests, "get", lambda *a, **k: FakeResponse(401, reason="Unauthorized"))
        with pytest.raises(mp.MagicDownloadError, match="private"):
            mp.fetch_contribution(1, share_key="wrong")

    def test_no_connection_is_one_sentence(self, monkeypatch):
        import requests

        def get(*a, **k):
            raise requests.exceptions.ConnectionError("boom")
        monkeypatch.setattr(requests, "get", get)
        with pytest.raises(mp.MagicDownloadError, match="Could not reach MagIC"):
            mp.fetch_contribution(20549)

    def test_download_by_doi_takes_the_latest_version_and_reports_each_stage(self, monkeypatch, tmp_path):
        monkeypatch.setattr(mp, "find_contributions", lambda doi, **k: [mp._contribution_ref(r) for r in self.ROWS[1::-1]])
        monkeypatch.setattr(mp, "fetch_contribution", lambda magic_id, **k: AS_SERVED.replace("20549", str(magic_id)))
        said = []
        ref = mp.download_contribution("https://doi.org/10.1130/B36634.1", str(tmp_path), report=said.append)
        assert ref.id == 20614
        assert said[0] == "Looking up 10.1130/B36634.1 in MagIC …"
        assert "2 versions; taking the latest" in said[1]
        assert said[-1] == "MagIC contribution 20614 (version 1): 4 tables written."
        assert os.path.exists(tmp_path / "measurements.txt")


@pytest.mark.skipif(not os.environ.get("PMAGPY_NETWORK_TESTS"), reason="set PMAGPY_NETWORK_TESTS=1 to talk to EarthRef")
def test_live_the_smallest_group_contribution_downloads_and_unpacks(tmp_path):
    ref = mp.download_contribution("20549", str(tmp_path))
    assert ref.id == 20549 and ref.doi == "10.1029/2025TC009333"
    assert os.path.exists(tmp_path / "measurements.txt")
    assert mp.find_contributions("10.1029/2025TC009333")[0].id == 20549
