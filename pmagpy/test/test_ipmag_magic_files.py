"""
ipmag.download_magic, ipmag.combine_magic and ipmag.orientation_magic:
the file-level MagIC helpers the hub's Download and Convert pages use.

Everything is written into ``tmp_path``; the repository's example files are
only read.  No network.
"""
import os
import shutil

import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag
from pmagpy import pmag

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data_files")
DOWNLOAD = os.path.join(DATA, "download_magic", "magic_contribution_19340.txt")
COMBINE = os.path.join(DATA, "combine_magic")
ORIENT = os.path.join(DATA, "orientation_magic")


def read_table(path):
    return pd.read_csv(path, sep="\t", header=1, dtype=str, keep_default_na=False)


def tables_in(path):
    """{table: number of rows} by reading the MagIC upload/download format directly."""
    counts, table, rows = {}, None, 0
    with open(path, encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f if line.strip()]
    for line in lines:
        if line.startswith(">>>>"):
            if table:
                counts[table] = rows - 1                    # first data line was the header
            table, rows = None, 0
        elif line.startswith("tab"):
            table = line.split("\t")[1]
        elif table:
            rows += 1
    if table:
        counts[table] = rows - 1
    return counts


TWO_LOCATIONS = "\n".join([
    "tab delimited\tlocations",
    "location\tlocation_type\tcitations",
    "Loc A\tOutcrop\tThis study",
    "Loc B\tOutcrop\tThis study",
    ">>>>>>>>>>",
    "tab delimited\tsites",
    "site\tlocation\tlat\tlon\tmethod_codes",
    "A1\tLoc A\t10\t20\t LP-DIR-AF : LT-AF-Z ",
    "A2\tLoc A\t11\t21\tLP-DIR-T",
    "B1\tLoc B\t-5\t100\tLP-DIR-T",
    ">>>>>>>>>>",
    "tab delimited\tsamples",
    "sample\tsite\tazimuth\tdip",
    "A1a\tA1\t10\t-20",
    "B1a\tB1\t0\t0",
    "",
])


class TestDownloadMagic:
    def test_a_downloaded_contribution_unpacks_into_one_file_per_table(self, tmp_path, capsys):
        assert ipmag.download_magic(DOWNLOAD, dir_path=str(tmp_path)) is True
        expected = tables_in(DOWNLOAD)
        assert set(expected) == {"contribution", "locations", "sites", "samples", "specimens",
                                 "measurements", "criteria", "ages"}
        for table, n_rows in expected.items():
            df = read_table(tmp_path / (table + ".txt"))
            assert len(df) == n_rows, table
        ages = read_table(tmp_path / "ages.txt").set_index("site")
        assert ages.loc["sr01", "age"] == "3.4" and ages.loc["sr01", "age_unit"] == "ka"
        assert "working on:  'measurements'" in capsys.readouterr().out

    def test_the_text_of_a_download_unpacks_without_a_file_and_method_codes_lose_their_spaces(self, tmp_path):
        assert ipmag.download_magic(dir_path=str(tmp_path), txt=TWO_LOCATIONS, print_progress=False)
        assert sorted(os.listdir(tmp_path)) == ["locations.txt", "samples.txt", "sites.txt"]
        sites = read_table(tmp_path / "sites.txt").set_index("site")
        assert sites.loc["A1", "method_codes"] == "LP-DIR-AF:LT-AF-Z"
        assert list(sites.index) == ["A1", "A2", "B1"]

    def test_separate_locs_makes_a_directory_per_location_and_refuses_to_clobber_one(self, tmp_path):
        assert ipmag.download_magic(dir_path=str(tmp_path), txt=TWO_LOCATIONS, separate_locs=True,
                                    print_progress=False)
        loc_1, loc_2 = tmp_path / "Location_1", tmp_path / "Location_2"
        assert loc_1.is_dir() and loc_2.is_dir()
        a_sites = read_table(loc_1 / "sites.txt")
        b_sites = read_table(loc_2 / "sites.txt")
        assert list(a_sites["site"]) == ["A1", "A2"] and list(b_sites["site"]) == ["B1"]
        assert list(read_table(loc_2 / "samples.txt")["sample"]) == ["B1a"]     # location propagated down
        assert list(read_table(loc_1 / "locations.txt")["location"]) == ["Loc A"]
        # the same unpack again: the location directories exist, so without overwrite it stops
        assert ipmag.download_magic(dir_path=str(tmp_path), txt=TWO_LOCATIONS, separate_locs=True,
                                    print_progress=False) is False
        assert ipmag.download_magic(dir_path=str(tmp_path), txt=TWO_LOCATIONS, separate_locs=True,
                                    overwrite=True, print_progress=False) is True

    def test_input_and_output_directories_may_differ(self, tmp_path):
        source = tmp_path / "in"
        source.mkdir()
        shutil.copy(DOWNLOAD, source / "download.txt")
        out = tmp_path / "out"
        out.mkdir()
        assert ipmag.download_magic("download.txt", dir_path=str(out), input_dir_path=str(source),
                                    print_progress=False)
        assert (out / "sites.txt").is_file() and not (source / "sites.txt").exists()


class TestCombineMagic:
    def test_two_measurement_files_become_one_with_a_fresh_sequence(self, tmp_path):
        outfile = str(tmp_path / "measurements.txt")
        result = ipmag.combine_magic(["af_measurements.txt", "therm_measurements.txt"], outfile,
                                     input_dir_path=COMBINE)
        assert result == outfile
        af = read_table(os.path.join(COMBINE, "af_measurements.txt"))
        therm = read_table(os.path.join(COMBINE, "therm_measurements.txt"))
        combined = read_table(outfile)
        assert len(combined) == len(af) + len(therm)
        assert set(combined["experiment"]) == set(af["experiment"]) | set(therm["experiment"])
        assert list(combined["sequence"].astype(int)) == list(range(1, len(combined) + 1))

    def test_a_file_combined_with_itself_keeps_each_row_once(self, tmp_path):
        outfile = str(tmp_path / "measurements.txt")
        source = os.path.join(COMBINE, "af_measurements.txt")
        assert ipmag.combine_magic([source, source], outfile)
        assert len(read_table(outfile)) == len(read_table(source))

    def test_a_table_other_than_measurements_is_recognised_from_its_header(self, tmp_path):
        pmag.magic_write(str(tmp_path / "a_sites.txt"), [{"site": "A1", "location": "L", "lat": "1"}], "sites")
        pmag.magic_write(str(tmp_path / "b_sites.txt"), [{"site": "B1", "location": "L", "lon": "2"}], "sites")
        outfile = str(tmp_path / "sites.txt")
        assert ipmag.combine_magic(["a_sites.txt", "b_sites.txt"], outfile, input_dir_path=str(tmp_path))
        with open(outfile) as f:
            assert f.readline().split("\t")[1].strip() == "sites"
        sites = read_table(outfile).set_index("site")
        assert float(sites.loc["A1", "lat"]) == 1 and float(sites.loc["B1", "lon"]) == 2
        assert sites.loc["A1", "lon"] == "" and sites.loc["B1", "lat"] == ""             # not NaN on disk

    def test_nothing_to_combine_and_a_2_5_file_are_refused(self, tmp_path, capsys):
        assert ipmag.combine_magic(["nowhere.txt"], str(tmp_path / "out.txt")) is False
        assert "no valid file paths" in capsys.readouterr().out
        old = tmp_path / "magic_measurements.txt"
        old.write_text("tab\tmagic_measurements\ner_specimen_name\tmeasurement_dec\nsp1\t10\n")
        assert ipmag.combine_magic([str(old)], str(tmp_path / "out.txt")) is False
        assert "MagIC 2.5 file" in capsys.readouterr().out


def orient_rows(path):
    """{(sample, method code that sets the azimuth): row} from an orientation_magic samples table."""
    rows = {}
    for _, row in read_table(path).iterrows():
        source = [code for code in row["method_codes"].split(":") if code.startswith("SO-")]
        rows[(row["sample"], source[-1] if source else "")] = row
    return rows


class TestOrientationMagic:
    """data_files/orientation_magic/orient_example.txt: 8 McMurdo samples, two sites, sun compass."""

    @pytest.fixture
    def converted(self, tmp_path):
        ok, message = ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                              output_dir_path=str(tmp_path), method_codes="FS-FD")
        assert ok and message is None
        return tmp_path

    def test_every_sample_gets_a_magnetic_a_declination_corrected_and_a_sun_compass_azimuth(self, converted):
        rows = orient_rows(converted / "samples.txt")
        assert len(rows) == 24 and {k[1] for k in rows} == {"SO-MAG", "SO-CMD-NORTH", "SO-SUN"}
        mag = rows[("mc123a", "SO-MAG")]
        assert float(mag["azimuth"]) == 258.0 and float(mag["dip"]) == -38.0       # Pomeroy: dip = -hade
        assert mag["method_codes"] == "FS-FD:SO-MAG"
        # declination correction from the IGRF at the site on the sampling date
        x, y, z, _ = pmag.doigrf(163.72913, -78.25435, 0, 2004 + 1 / 12)
        igrf_dec = pmag.cart2dir([x, y, z])[0]
        corrected = rows[("mc123a", "SO-CMD-NORTH")]
        assert float(corrected["azimuth"]) == pytest.approx((258.0 + igrf_dec) % 360, abs=0.05)
        assert float(corrected["azimuth_dec_correction"]) == pytest.approx(igrf_dec, abs=0.05)
        assert "Declination correction calculated from IGRF" in corrected["description"]
        # sun compass: shadow angle 260.5 at 16:58 local = GMT (hours_from_gmt=0)
        sun = pmag.dosundec({"date": "2004:1:15:16:58", "delta_u": 0, "lat": -78.25435,
                             "lon": 163.72913, "shadow_angle": "260.5"})
        assert float(rows[("mc123a", "SO-SUN")]["azimuth"]) == pytest.approx(sun, abs=0.05)
        assert rows[("mc123a", "SO-SUN")]["timestamp"] == "2004:1:15:16:58"

    def test_bedding_is_declination_corrected_and_inherited_by_the_samples_that_leave_it_blank(self, converted):
        rows = orient_rows(converted / "samples.txt")
        first = rows[("mc123a", "SO-MAG")]
        assert float(first["bed_dip"]) == 4
        assert float(first["bed_dip_direction"]) == pytest.approx((12 + float(rows[("mc123a", "SO-CMD-NORTH")]["azimuth_dec_correction"])) % 360, abs=0.05)
        for sample in ["mc123b", "mc123e", "mc137c"]:                                # blank in the file
            row = rows[(sample, "SO-MAG")]
            assert row["bed_dip"] == first["bed_dip"]
            assert row["bed_dip_direction"] == first["bed_dip_direction"]

    def test_sites_carry_the_location_and_the_first_samples_geology(self, converted):
        sites = read_table(converted / "sites.txt").set_index("site")
        assert list(sites.index) == ["mc123", "mc137"]
        assert set(sites["location"]) == {"McMurdo"}                                 # from the file's header line
        assert "sample_type" not in sites.columns
        assert sites.loc["mc123", "lithologies"] == "basalt"
        assert sites.loc["mc123", "geologic_classes"] == "igneous:extrusive"
        assert sites.loc["mc123", "geologic_types"] == "lava flow"
        assert float(sites.loc["mc137", "lat"]) == -78.26133 and float(sites.loc["mc137", "lon"]) == 163.25737
        samples = read_table(converted / "samples.txt")
        assert set(samples["location"]) == {"McMurdo"} and set(samples["site"]) == {"mc123", "mc137"}

    def test_a_supplied_declination_or_none_at_all_replaces_the_igrf(self, tmp_path):
        ok, _ = ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                        output_dir_path=str(tmp_path), dec_correction_con=2, dec_correction=10)
        assert ok
        rows = orient_rows(tmp_path / "samples.txt")
        assert float(rows[("mc123a", "SO-CMD-NORTH")]["azimuth"]) == 268.0
        assert "supplied by user" in rows[("mc123a", "SO-CMD-NORTH")]["description"]
        ok, _ = ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                        output_dir_path=str(tmp_path), dec_correction_con=3)
        assert ok
        rows = orient_rows(tmp_path / "samples.txt")
        assert {k[1] for k in rows} == {"SO-MAG", "SO-SUN"}                         # already corrected: no CMD rows
        with pytest.raises(Exception, match="declincation correction"):
            ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                    output_dir_path=str(tmp_path), dec_correction_con=2)

    def test_the_orientation_convention_maps_the_field_arrow_to_the_lab_arrow(self, tmp_path):
        ok, _ = ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                        output_dir_path=str(tmp_path), or_con=3, dec_correction_con=3)
        assert ok
        rows = orient_rows(tmp_path / "samples.txt")
        assert float(rows[("mc123a", "SO-MAG")]["dip"]) == 90 - 38                  # [3]: lab dip = 90 - hade

    def test_average_bedding_writes_the_fisher_mean_of_the_bedding_poles_into_every_sample(self, tmp_path):
        orient = tmp_path / "orient.txt"
        orient.write_text("\n".join([
            "tab\tTest",
            "sample_name\tlat\tlong\tmag_azimuth\tfield_dip\tbedding_dip_direction\tbedding_dip",
            "ts01a\t45\t10\t100\t30\t90\t10",
            "ts01b\t45\t10\t110\t30\t120\t20",
            "",
        ]))
        ok, _ = ipmag.orientation_magic(input_dir_path=str(tmp_path), orient_file="orient.txt",
                                        output_dir_path=str(tmp_path), dec_correction_con=3,
                                        average_bedding=True)
        assert ok
        poles = pmag.fisher_mean([[90, 10 - 90, 1], [120, 20 - 90, 1]])
        samples = read_table(tmp_path / "samples.txt")
        assert len(samples) == 2 and poles["dec"] != 90                              # a true average, not the first row
        assert samples["bed_dip_direction"].astype(float).tolist() == pytest.approx([poles["dec"]] * 2, abs=0.05)
        assert samples["bed_dip"].astype(float).tolist() == pytest.approx([poles["inc"] + 90] * 2, abs=0.05)

    def test_appending_keeps_the_samples_already_in_the_table(self, tmp_path):
        ok, _ = ipmag.orientation_magic(input_dir_path=ORIENT, orient_file="orient_example.txt",
                                        output_dir_path=str(tmp_path), dec_correction_con=3)
        assert ok
        n_first = len(read_table(tmp_path / "samples.txt"))
        (tmp_path / "more.txt").write_text("\n".join([
            "tab\tMcMurdo",
            "sample_name\tlat\tlong\tmag_azimuth\tfield_dip",
            "mc200a\t-78.3\t163.3\t50\t20",
            "",
        ]))
        ok, _ = ipmag.orientation_magic(input_dir_path=str(tmp_path), orient_file="more.txt",
                                        output_dir_path=str(tmp_path), dec_correction_con=3, append=True)
        assert ok
        samples = read_table(tmp_path / "samples.txt")
        assert len(samples) == n_first + 1
        assert set(samples["sample"]) >= {"mc123a", "mc137c", "mc200a"}
        assert list(read_table(tmp_path / "sites.txt")["site"]) == ["mc200", "mc123", "mc137"]

    def test_a_missing_file_or_latitude_is_reported_not_raised(self, tmp_path, capsys):
        ok, message = ipmag.orientation_magic(input_dir_path=str(tmp_path), orient_file="absent.txt",
                                              output_dir_path=str(tmp_path))
        assert ok is False and "No such file" in message
        (tmp_path / "orient.txt").write_text("tab\tTest\nsample_name\tlat\tlong\tmag_azimuth\tfield_dip\nts01a\t\t10\t100\t30\n")
        ok, message = ipmag.orientation_magic(input_dir_path=str(tmp_path), orient_file="orient.txt",
                                              output_dir_path=str(tmp_path))
        assert ok is False and "Latitude is required" in message
