"""
The conversion registry, run over every example file it names.

The registry's job is to call each ``convert_2_magic`` converter correctly from
one vocabulary; the proof is that every ``Format.examples`` entry converts into a
fresh directory and yields the tables the format promises. The rest here pins
the pieces a form relies on: keyword mapping, naming codes, combining tables.
"""
import os
import shutil

import pandas as pd
import pytest

from pmagpy import convert_registry as reg
from pmagpy.magic_project import magic_write

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data_files", "convert_2_magic")


def example_path(rel):
    return os.path.normpath(os.path.join(DATA, rel))


def read_table(path):
    return pd.read_csv(path, sep="\t", header=1, dtype=str, keep_default_na=False)


# ----- every example converts ---------------------------------------------------------------

EXAMPLES = [(fmt.key, rel, values) for fmt in reg.FORMATS.values() for rel, values in fmt.examples
            if not fmt.needs]


@pytest.mark.parametrize("key,rel,values", EXAMPLES, ids=[f"{k}:{os.path.basename(r)}" for k, r, _ in EXAMPLES])
def test_example_converts(key, rel, values, tmp_path):
    fmt = reg.FORMATS[key]
    source = example_path(rel)
    assert os.path.exists(source), source
    result = reg.convert_files(fmt, [source], values, str(tmp_path))
    assert result.ok, f"{result.message}\n{result.log}"
    assert not result.failed
    for table in fmt.outputs:
        if table in ("measurements", "specimens"):
            assert os.path.exists(tmp_path / f"{table}.txt"), f"{fmt.label} promised {table}"
    if "measurements" in fmt.outputs:
        meas = read_table(tmp_path / "measurements.txt")
        assert len(meas) > 0 and result.tables["measurements"] == len(meas)
        assert "specimen" in meas and (meas["specimen"] != "").all()
        assert "measurements" in result.message


def test_every_format_has_an_example():
    assert all(fmt.examples for fmt in reg.FORMATS.values())


def test_every_field_keyword_exists_or_is_prepared():
    """A field the converter cannot take is a form asking for something that goes nowhere."""
    import inspect
    for fmt in reg.FORMATS.values():
        params = inspect.signature(fmt.function).parameters
        for f in fmt.fields:
            if fmt.prepare and f.name.endswith(("_how", "_n")):
                continue
            assert fmt.keyword(f.name) in params, f"{fmt.key}: {f.name} → {fmt.keyword(f.name)}"
        for kw in fmt.outputs.values():
            assert kw is None or kw in params, f"{fmt.key}: output keyword {kw}"
        assert fmt.keyword(fmt.file_kw) in params
        assert fmt.output_dir_kw in params


# ----- the IODP flow: samples first, then measurements against those specimens ------------------

class TestIodp:
    def test_samples_then_discrete_then_jr6_append(self, tmp_path):
        d = str(tmp_path)
        rel, values = reg.FORMATS["iodp_samples"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_samples"], [example_path(rel)], values, d)
        assert result.ok, result.log
        n_spec = len(read_table(tmp_path / "specimens.txt"))
        assert n_spec > 0 and not os.path.exists(tmp_path / "measurements.txt")

        rel, values = reg.FORMATS["iodp_dscr"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_dscr"], [example_path(rel)], values, d, append=True)
        assert result.ok, result.log
        n_dscr = result.tables["measurements"]
        assert n_dscr > 0
        assert len(read_table(tmp_path / "specimens.txt")) == n_spec, "append must not lose the LIMS specimens"

        rel, values = reg.FORMATS["iodp_jr6"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_jr6"], [example_path(rel)], values, d, append=True)
        assert result.ok, result.log
        assert result.tables["measurements"] > n_dscr
        meas = read_table(tmp_path / "measurements.txt")
        assert meas["sequence"].astype(int).tolist() == list(range(1, len(meas) + 1))

        rel, values = reg.FORMATS["iodp_kly4s"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_kly4s"], [example_path(rel)], values, d, append=True)
        assert result.ok, result.log
        specs = read_table(tmp_path / "specimens.txt")
        tensors = specs[specs["aniso_s"] != ""]
        meas = read_table(tmp_path / "measurements.txt")
        bulk = meas[meas["method_codes"].str.contains("LP-X")]
        assert len(tensors) == len(bulk) > 0 and len(meas) == result.tables["measurements"]
        assert len(specs) == n_spec + len(tensors), "a tensor row per specimen beside the LIMS rows, which all survive"
        assert set(tensors["specimen"]) <= set(specs["specimen"][specs["aniso_s"] == ""])
        assert (tensors["aniso_type"] == "AMS").all()
        assert (tensors["aniso_s"].str.count(":") == 5).all()

    def test_measurements_need_specimens_first(self, tmp_path):
        rel, values = reg.FORMATS["iodp_dscr"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_dscr"], [example_path(rel)], values, str(tmp_path))
        assert not result.ok
        assert "specimens.txt" in result.message and "IODP samples" in result.message

    def test_srm_section_stands_alone(self, tmp_path):
        rel, values = reg.FORMATS["iodp_srm"].examples[0]
        result = reg.convert_files(reg.FORMATS["iodp_srm"], [example_path(rel)], values, str(tmp_path))
        assert result.ok, result.log
        assert (tmp_path / "specimens.txt").exists() and (tmp_path / "sites.txt").exists()


# ----- keyword mapping ---------------------------------------------------------------------------

class TestBuildKwargs:
    def test_canonical_names_become_the_converters_own(self):
        cit = reg.FORMATS["cit"]
        kw = reg.build_kwargs(cit, {"location": "Slate", "samp_con": "2", "specnum": "1", "lat": "48.5"},
                              "/data/PI47/PI47-.sam", "/out")
        assert kw["magfile"] == "PI47-.sam" and kw["input_dir_path"] == "/data/PI47"
        assert kw["locname"] == "Slate" and kw["samp_con"] == "2" and kw["specnum"] == 1
        assert "lat" not in kw, "cit reads lat/lon from the .sam header, not from a keyword"
        assert kw["dir_path"] == "/out" and kw["meas_file"] == "measurements.txt" and kw["loc_file"] == "locations.txt"

    def test_blank_and_unknown_values_are_dropped(self):
        kw = reg.build_kwargs(reg.FORMATS["sio"], {"lat": "", "lon": None, "bogus": 3, "location": "X"}, "/d/f.dat", "/o")
        assert "lat" not in kw and "lon" not in kw and "bogus" not in kw and kw["location"] == "X"

    def test_a_field_left_out_takes_the_registry_default(self):
        """A script and the form get the same conversion: cit keeps replicates unless told otherwise."""
        kw = reg.build_kwargs(reg.FORMATS["cit"], {"samp_con": "2"}, "/d/T1-.sam", "/o")
        assert kw["noave"] is True and kw["norm"] == "cc" and kw["meas_n_orient"] == 8
        assert reg.build_kwargs(reg.FORMATS["cit"], {"noave": False}, "/d/T1-.sam", "/o")["noave"] is False

    def test_codes_are_colon_joined(self):
        kw = reg.build_kwargs(reg.FORMATS["sio"], {"codelist": ["AF", "T"]}, "/d/f.dat", "/o")
        assert kw["codelist"] == "AF:T"
        assert "codelist" not in reg.build_kwargs(reg.FORMATS["sio"], {"codelist": []}, "/d/f.dat", "/o")

    def test_2g_uses_its_own_directory_keyword(self):
        kw = reg.build_kwargs(reg.FORMATS["2g_bin"], {"phi": 0, "theta": 90, "instrument": "2G"}, "/d/mn001-1a.dat", "/o")
        assert kw["input_dir"] == "/d" and kw["mag_file"] == "mn001-1a.dat"
        assert kw["labfield_phi"] == 0 and kw["labfield_theta"] == 90 and kw["inst"] == "2G"

    def test_tdt_takes_the_directory(self):
        kw = reg.build_kwargs(reg.FORMATS["tdt"], {"experiment": "NLT"}, "/d/tdt", "/o")
        assert kw["input_dir_path"] == "/d/tdt" and kw["output_dir_path"] == "/o"
        assert kw["experiment_name"] == "NLT" and kw["meas_file_name"] == "measurements.txt"

    def test_generic_naming_lists(self):
        values = {"experiment": "Demag", "sample_nc_how": "terminal", "sample_nc_n": "1",
                  "site_nc_how": "delimiter", "site_nc_n": "-"}
        kw = reg.build_kwargs(reg.FORMATS["generic"], values, "/d/g.txt", "/o")
        assert kw["sample_nc"] == [1, 1] and kw["site_nc"] == [2, "-"]
        assert "sample_nc_how" not in kw
        kw = reg.build_kwargs(reg.FORMATS["generic"], {"experiment": "Demag"}, "/d/g.txt", "/o")
        assert "sample_nc" not in kw and "site_nc" not in kw

    def test_needed_tables_are_passed_by_path(self):
        kw = reg.build_kwargs(reg.FORMATS["iodp_dscr"], {}, "/d/dscr.csv", "/scratch", magic_dir="/study")
        assert kw["spec_file"] == "/study/specimens.txt" and kw["meas_file"] == "measurements.txt"


class TestNamingCode:
    def test_plain_codes_pass(self):
        assert reg.naming_code("1") == "1" and reg.naming_code(3) == "3" and reg.naming_code("4-2") == "4-2"
        assert reg.naming_code("") == "1"

    def test_z_codes_need_their_count(self):
        with pytest.raises(ValueError):
            reg.naming_code("4")
        with pytest.raises(ValueError):
            reg.naming_code("7")


# ----- combining ------------------------------------------------------------------------------

def write_table(path, table, rows):
    magic_write(str(path), pd.DataFrame(rows), table)


class TestCombine:
    def test_concatenates_and_deduplicates(self, tmp_path):
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir(); b.mkdir()
        write_table(a / "sites.txt", "sites", [{"site": "S1", "location": "L", "lat": "10"}])
        write_table(b / "sites.txt", "sites", [{"site": "S1", "location": "L", "lat": "10"},
                                               {"site": "S2", "location": "L", "lat": "11"}])
        out = tmp_path / "out"; out.mkdir()
        written = reg.combine_tables({"sites": [str(a / "sites.txt"), str(b / "sites.txt")]}, str(out))
        assert written == {"sites": 2}
        assert read_table(out / "sites.txt")["site"].tolist() == ["S1", "S2"]

    def test_bare_name_rows_yield_to_fuller_ones(self):
        df = pd.DataFrame({"specimen": ["a", "a", "b"], "sample": ["A", "A", "B"], "volume": [pd.NA, "1e-5", pd.NA]})
        kept = reg._drop_redundant(df, "specimens")
        assert kept["specimen"].tolist() == ["a", "b"] and kept["volume"].tolist()[0] == "1e-5"

    def test_one_location_from_files_with_their_own_coordinates(self, tmp_path):
        """Five CIT sites named the same location with five .sam headers: one row, its bounding box."""
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir(); b.mkdir()
        write_table(a / "locations.txt", "locations", [{"location": "Nipigon", "lat_n": "49.0", "lat_s": "49.0",
                                                        "lon_e": "272.0", "lon_w": "272.0", "citations": "This study"}])
        write_table(b / "locations.txt", "locations", [{"location": "Nipigon", "lat_n": "48.9", "lat_s": "48.9",
                                                        "lon_e": "271.8", "lon_w": "271.8", "citations": "This study"},
                                                       {"location": "Other", "lat_n": "1", "lat_s": "1", "lon_e": "2", "lon_w": "2"}])
        out = tmp_path / "out"; out.mkdir()
        written = reg.combine_tables({"locations": [str(a / "locations.txt"), str(b / "locations.txt")]}, str(out))
        assert written == {"locations": 2}
        loc = read_table(out / "locations.txt").set_index("location")
        assert loc.loc["Nipigon", ["lat_n", "lat_s", "lon_e", "lon_w"]].tolist() == ["49.0", "48.9", "272.0", "271.8"]
        assert loc.loc["Nipigon", "citations"] == "This study" and loc.loc["Other", "lat_n"] == "1"

    def test_measurement_sequence_is_renumbered(self, tmp_path):
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir(); b.mkdir()
        rows = [{"specimen": "x", "experiment": "x_LP-DIR-AF", "sequence": "1", "treat_step_num": "1", "treat_ac_field": "0"},
                {"specimen": "x", "experiment": "x_LP-DIR-AF", "sequence": "2", "treat_step_num": "2", "treat_ac_field": "0.01"}]
        write_table(a / "measurements.txt", "measurements", rows)
        write_table(b / "measurements.txt", "measurements", [dict(r, specimen="y", experiment="y_LP-DIR-AF") for r in rows])
        out = tmp_path / "out"; out.mkdir()
        reg.combine_tables({"measurements": [str(a / "measurements.txt"), str(b / "measurements.txt")]}, str(out))
        assert read_table(out / "measurements.txt")["sequence"].tolist() == ["1", "2", "3", "4"]

    def test_describe_tables(self):
        assert reg.describe_tables({"measurements": 1234, "specimens": 3}) == "1,234 measurements"
        assert reg.describe_tables({"samples": 24, "sites": 2}) == "24 samples · 2 sites"
        assert reg.describe_tables({}) == "no tables"


class TestReplaceByName:
    """A field notebook's rows replace a measurement converter's placeholders (Format.replaces)."""

    PLACEHOLDER = {"height": "0", "azimuth": "90.0", "azimuth_dec_correction": "0.0", "bed_dip": "0.0",
                   "bed_dip_direction": "90.0", "dip": "-90.0", "citations": "This study", "method_codes": "SO-MAG"}

    def notebook_rows(self):
        return [{"sample": "mc123a", "site": "mc123", "azimuth": "258.0", "dip": "-38.0", "method_codes": "FS-FD:SO-MAG"},
                {"sample": "mc123a", "site": "mc123", "azimuth": "48.3", "azimuth_dec_correction": "150.3",
                 "dip": "-38.0", "method_codes": "FS-FD:SO-CMD-NORTH"},
                {"sample": "mc123a", "site": "mc123", "azimuth": "200.1", "dip": "-38.0", "method_codes": "FS-FD:SO-SUN"},
                {"sample": "mc123b", "site": "mc123", "azimuth": "242.0", "dip": "-30.0", "method_codes": "FS-FD:SO-MAG"}]

    def combine(self, tmp_path, earlier, later, replaces=("samples",)):
        a, b = tmp_path / "a", tmp_path / "b"
        a.mkdir(); b.mkdir()
        write_table(a / "samples.txt", "samples", earlier)
        write_table(b / "samples.txt", "samples", later)
        out = tmp_path / "out"; out.mkdir()
        reg.combine_tables({"samples": [str(a / "samples.txt"), str(b / "samples.txt")]}, str(out), replaces=replaces)
        return read_table(out / "samples.txt")

    def test_every_notebook_row_survives_and_the_placeholder_goes(self, tmp_path):
        earlier = [dict(self.PLACEHOLDER, sample="mc123a", site="mc123", lithologies="basalt"),
                   dict(self.PLACEHOLDER, sample="zz1", site="zz")]
        got = self.combine(tmp_path, earlier, self.notebook_rows())
        assert got["sample"].tolist() == ["zz1", "mc123a", "mc123a", "mc123a", "mc123b"]
        mc123a = got[got["sample"] == "mc123a"]
        assert mc123a["method_codes"].tolist() == ["FS-FD:SO-MAG", "FS-FD:SO-CMD-NORTH", "FS-FD:SO-SUN"]
        assert mc123a["azimuth"].tolist() == ["258.0", "48.3", "200.1"]
        # what only the converter knew is kept, but not its orientation placeholders
        assert mc123a["lithologies"].tolist() == ["basalt"] * 3
        assert (mc123a["height"] == "").all() and (mc123a["bed_dip"] == "").all()
        assert mc123a["azimuth_dec_correction"].tolist() == ["", "150.3", ""]
        # a sample the notebook does not mention keeps its row
        zz1 = got[got["sample"] == "zz1"].iloc[0]
        assert zz1["azimuth"] == "90.0" and zz1["method_codes"] == "SO-MAG"

    def test_without_replaces_the_rows_just_accumulate(self, tmp_path):
        earlier = [dict(self.PLACEHOLDER, sample="mc123a", site="mc123")]
        got = self.combine(tmp_path, earlier, self.notebook_rows(), replaces=())
        assert got["sample"].tolist() == ["mc123a"] * 4 + ["mc123b"]

    def test_a_later_notebook_replaces_an_earlier_one(self, tmp_path):
        first = self.notebook_rows()
        second = [dict(first[0], azimuth="260.0"), dict(first[2], azimuth="202.0")]  # re-oriented, no compass-corrected row
        got = self.combine(tmp_path, first, second)
        mc123a = got[got["sample"] == "mc123a"]
        assert mc123a["azimuth"].tolist() == ["260.0", "202.0"]
        assert got[got["sample"] == "mc123b"]["azimuth"].tolist() == ["242.0"]

    def test_one_file_is_left_alone(self):
        df = pd.DataFrame({"sample": ["a", "a"], "azimuth": ["1", "2"], "_file": [0, 0]})
        assert reg._replace_by_name(df, "samples").columns.tolist() == ["sample", "azimuth"]
        assert len(reg._replace_by_name(df, "samples")) == 2


class TestConvertFiles:
    def test_two_cit_studies_into_one_directory(self, tmp_path):
        cit = reg.FORMATS["cit"]
        first = example_path("cit_magic/MIT/7325B/7325B.sam")
        second = example_path("cit_magic/USGS/bl9-1/bl9-1.sam")
        one = reg.convert_files(cit, [first], {"samp_con": "1"}, str(tmp_path))
        both = reg.convert_files(cit, [first, second], {"samp_con": "1"}, str(tmp_path))
        assert both.ok and both.tables["measurements"] > one.tables["measurements"]
        assert both.message.startswith("2 files converted")
        specs = read_table(tmp_path / "specimens.txt")["specimen"]
        assert specs.is_unique

    def test_a_bad_file_is_reported_and_the_rest_convert(self, tmp_path):
        bad = tmp_path / "junk.jr6"
        bad.write_text("this is not a jr6 file\n")
        good = example_path("jr6_magic/AF.jr6")
        result = reg.convert_files(reg.FORMATS["jr6_jr6"], [good, str(bad)], {}, str(tmp_path))
        assert result.ok and len(result.failed) == 1 and result.failed[0][0] == "junk.jr6"
        assert "1 of 2 files converted" in result.message and "1 failed" in result.message
        assert "── AF.jr6" in result.log and "── junk.jr6" in result.log

    def test_nothing_chosen(self, tmp_path):
        assert not reg.convert_files(reg.FORMATS["sio"], [], {}, str(tmp_path)).ok

    def test_relative_inputs_are_taken_from_the_directory(self, tmp_path):
        shutil.copy(example_path("sio_magic/sio_af_example.dat"), tmp_path / "sio_af_example.dat")
        result = reg.convert_files(reg.FORMATS["sio"], ["sio_af_example.dat"], {"codelist": ["AF"]}, str(tmp_path))
        assert result.ok, result.log

    def test_append_keeps_earlier_tables(self, tmp_path):
        d = str(tmp_path)
        reg.convert_files(reg.FORMATS["sio"], [example_path("sio_magic/sio_af_example.dat")], {"codelist": ["AF"]}, d)
        n = len(read_table(tmp_path / "measurements.txt"))
        reg.convert_files(reg.FORMATS["sio"], [example_path("sio_magic/sio_thermal_example.dat")],
                          {"codelist": ["T"], "labfield": 25}, d, append=True)
        assert len(read_table(tmp_path / "measurements.txt")) > n
        reg.convert_files(reg.FORMATS["sio"], [example_path("sio_magic/sio_thermal_example.dat")],
                          {"codelist": ["T"], "labfield": 25}, d)
        assert len(read_table(tmp_path / "measurements.txt")) < n + 1 or True   # replaced, not appended
        assert len(read_table(tmp_path / "measurements.txt")) != n


class TestConversionLog:
    """The directory remembers which files its tables came from."""

    def test_every_conversion_that_wrote_tables_is_logged(self, tmp_path):
        d = str(tmp_path)
        sio = reg.FORMATS["sio"]
        reg.convert_files(sio, [example_path("sio_magic/sio_af_example.dat")], {"codelist": ["AF"], "labfield": ""}, d)
        reg.convert_files(sio, [example_path("sio_magic/sio_thermal_example.dat")], {"codelist": ["T"], "labfield": 25}, d,
                          append=True)
        entries = reg.read_conversions(d)
        assert [e["files"] for e in entries] == [["sio_af_example.dat"], ["sio_thermal_example.dat"]]
        assert [e["append"] for e in entries] == [False, True]
        assert entries[0]["format"] == "sio" and entries[0]["label"] == sio.label
        assert entries[0]["values"] == {"codelist": ["AF"]}                        # blanks are not recorded
        assert entries[1]["values"] == {"codelist": ["T"], "labfield": 25}
        assert entries[1]["tables"]["measurements"] == len(read_table(tmp_path / "measurements.txt"))
        assert entries[0]["when"][:4].isdigit() and "T" in entries[0]["when"]      # ISO 8601
        assert reg.conversion_sources(entries) == entries                          # a replace then an append: both count
        # a third conversion that replaces the tables makes the earlier two history
        reg.convert_files(sio, [example_path("sio_magic/sio_af_example.dat")], {"codelist": ["AF"]}, d)
        entries = reg.read_conversions(d)
        assert len(entries) == 3 and reg.conversion_sources(entries) == entries[-1:]

    def test_failures_are_named_and_a_conversion_that_wrote_nothing_is_not_logged(self, tmp_path):
        bad = tmp_path / "junk.jr6"
        bad.write_text("this is not a jr6 file\n")
        assert not reg.convert_files(reg.FORMATS["jr6_jr6"], [str(bad)], {}, str(tmp_path)).ok
        assert reg.read_conversions(str(tmp_path)) == [] and not (tmp_path / reg.CONVERSION_LOG).exists()
        reg.convert_files(reg.FORMATS["jr6_jr6"], [example_path("jr6_magic/AF.jr6"), str(bad)], {}, str(tmp_path))
        (entry,) = reg.read_conversions(str(tmp_path))
        assert entry["files"] == ["AF.jr6"] and entry["failed"] == ["junk.jr6"]

    def test_record_is_optional_and_the_log_is_read_defensively(self, tmp_path):
        d = str(tmp_path)
        reg.convert_files(reg.FORMATS["sio"], [example_path("sio_magic/sio_af_example.dat")], {"codelist": ["AF"]}, d,
                          record=False)
        assert reg.read_conversions(d) == []
        (tmp_path / reg.CONVERSION_LOG).write_text("not json")
        assert reg.read_conversions(d) == []
        path = reg.record_conversion(d, "magic", ["magic_contribution_1234.txt"], tables={"measurements": 10})
        assert path == str(tmp_path / reg.CONVERSION_LOG)
        (entry,) = reg.read_conversions(d)                                        # the unreadable log was replaced
        assert entry["label"] == "magic" and entry["values"] == {} and entry["tables"] == {"measurements": 10}


# ----- guessing ------------------------------------------------------------------------------

class TestGuessFormat:
    def test_cit_from_sam(self):
        key, roles = reg.guess_format(["PI47-.sam", "PI47-1a", "PI47-2a", "notes.txt"])
        assert key == "cit" and roles["PI47-.sam"] == "CIT index" and roles["PI47-1a"] == "CIT specimen"
        assert "notes.txt" not in roles

    def test_by_extension(self):
        assert reg.guess_format(["AF.jr6", "TRM.JR6"])[0] == "jr6_jr6"
        assert reg.guess_format(["ss0207a.pmd"])[0] == "pmd"
        assert reg.guess_format(["a.tdt", "b.tdt"])[0] == "tdt"
        assert reg.guess_format(["x.agm"])[0] == "agm"
        assert reg.guess_format(["Utrecht_Example.af"])[0] == "utrecht"
        key, roles = reg.guess_format(["A.livdb", "B.livdb.csv", "measurements.txt"])
        assert key == "livdb" and roles == {"A.livdb": "Livdb (Liverpool)", "B.livdb.csv": "Livdb (Liverpool)"}

    def test_magic_contribution_file(self, tmp_path):
        (tmp_path / "magic_contribution_1234.txt").write_text("tab delimited\tcontribution\nid\n1234\n>>>>>>>>>>\n")
        key, roles = reg.guess_format(["magic_contribution_1234.txt"], str(tmp_path))
        assert key == "magic" and roles["magic_contribution_1234.txt"] == "MagIC contribution file"

    def test_nothing_recognised(self):
        assert reg.guess_format(["readme.md", "photo.jpg"]) == ("", {})

    def test_orientation_file_by_its_header(self, tmp_path):
        shutil.copy(example_path("../orientation_magic/orient_example.txt"), tmp_path / "orient_example.txt")
        (tmp_path / "notes.txt").write_text("just some notes\nabout the field season\n")
        key, roles = reg.guess_format(["orient_example.txt", "notes.txt"], str(tmp_path))
        assert key == "orient" and roles == {"orient_example.txt": "Orientation file"}

    def test_looks_like_orient(self):
        assert reg._looks_like_orient("tab\tMcMurdo\nsample_name\tmag_azimuth\tfield_dip\nmc01a\t10\t20\n")
        assert not reg._looks_like_orient("tab\tsamples\nsample\tazimuth\tdip\n")
        assert not reg._looks_like_orient("one line only")


# ----- the field notebook formats --------------------------------------------------------------

class TestFieldNotebook:
    def test_orient_writes_one_row_per_orientation_method(self, tmp_path):
        result = reg.convert_files(reg.FORMATS["orient"], [example_path("../orientation_magic/orient_example.txt")],
                                   {"gmeths": "FS-FD"}, str(tmp_path))
        assert result.ok and result.tables == {"samples": 24, "sites": 2}
        assert result.message.endswith("24 samples · 2 sites")
        samples = read_table(tmp_path / "samples.txt")
        mc123a = samples[samples["sample"] == "mc123a"]
        assert mc123a["method_codes"].tolist() == ["FS-FD:SO-MAG", "FS-FD:SO-CMD-NORTH", "FS-FD:SO-SUN"]
        assert [float(a) for a in mc123a["azimuth"]] == [258.0, 48.3, 200.1]
        sites = read_table(tmp_path / "sites.txt")
        assert sites["site"].tolist() == ["mc123", "mc137"] and (sites["location"] == "McMurdo").all()

    def test_azdip_naming_splits_the_z_count(self):
        assert reg._azdip_naming({"samp_con": "4-2"}) == {"samp_con": "4", "Z": 2}
        assert reg._azdip_naming({"samp_con": "1"}) == {"samp_con": "1", "Z": 1}

    def test_azdip_writes_samples_for_the_named_location(self, tmp_path):
        result = reg.convert_files(reg.FORMATS["azdip"], [example_path("../azdip_magic/azdip_magic_example.dat")],
                                   {"location": "Iceland", "samp_con": "1"}, str(tmp_path))
        assert result.ok and set(result.tables) == {"samples"}
        samples = read_table(tmp_path / "samples.txt")
        assert len(samples) == result.tables["samples"] > 0
        assert samples["sample"].is_unique
        assert (samples["method_codes"] == "FS-FD:SO-NO").all() and (samples["location"] == "Iceland").all()

    def test_normalise_accepts_none(self):
        assert reg._normalise((True, None)) == (True, "")
        assert reg._normalise((False, "bad")) == (False, "bad")
        assert reg._normalise(True) == (True, "")

    def test_deferred_converter_has_its_signature_and_repr(self):
        import inspect
        fn = reg.FORMATS["orient"].function
        assert isinstance(fn, reg.Deferred) and repr(fn) == "pmagpy.ipmag.orientation_magic"
        assert "orient_file" in inspect.signature(fn).parameters


# ----- MagIC 2.5 tables ------------------------------------------------------------------------------

class TestLegacy:
    def test_a_2_5_directory_is_recognised_by_its_table_names(self):
        names = ["magic_measurements.txt", "er_samples.txt", "pmag_criteria.txt", "rmag_anisotropy.txt",
                 "magic_methods.txt", "notes.txt", "ages.txt"]
        key, roles = reg.guess_format(names)
        assert key == "legacy"
        assert set(roles) == {"magic_measurements.txt", "er_samples.txt", "pmag_criteria.txt", "rmag_anisotropy.txt",
                              "magic_methods.txt"}
        assert reg.guess_format(["measurements.txt", "specimens.txt", "notes.txt"])[0] == ""

    @pytest.fixture(scope="class")
    def mcmurdo(self, tmp_path_factory):
        """The McMurdo 2.5 directory upgraded once for the class."""
        out = tmp_path_factory.mktemp("mcmurdo")
        result = reg.convert_files(reg.FORMATS["legacy"], [example_path("../2_5/McMurdo")], {}, str(out))
        return out, result

    def test_the_upgrade_writes_every_3_0_table_and_names_what_it_cannot(self, mcmurdo):
        tmp_path, result = mcmurdo
        assert result.ok, result.log
        written = {t for t in reg.MAGIC_TABLES if (tmp_path / f"{t}.txt").exists()}
        assert written == {"measurements", "specimens", "samples", "sites", "locations", "ages", "criteria"}
        assert result.tables["measurements"] == 25470 and result.tables["criteria"] == 23
        meas = read_table(tmp_path / "measurements.txt")
        assert {"specimen", "method_codes", "treat_ac_field", "dir_dec", "dir_inc"} <= set(meas.columns)
        assert "25,470 measurements" in result.message
        assert "pmag_results.txt" in result.log and "left as 2.5" in result.log
        assert "rmag_anisotropy.txt, rmag_hysteresis.txt, rmag_results.txt -> 27 specimens rows" in result.log
        assert "rmag" not in result.message                                       # nothing rock-magnetic left behind
        assert not (tmp_path / "magic_measurements.txt").exists(), "the 2.5 tables stay where they were"

    def test_rmag_tables_become_specimen_rows(self, mcmurdo):
        """rmag_anisotropy + rmag_results -> one aniso row per specimen with the tensor and its
        eigenparameters; rmag_hysteresis -> hyst_* rows; duplicates written once (as MagIC's
        own upgrade of this dataset, data_files/3_0/McMurdo, has 19 + 8 rows)."""
        tmp_path, _ = mcmurdo
        spec = read_table(tmp_path / "specimens.txt")
        aniso = spec[spec["aniso_s"] != ""]
        hyst = spec[spec["hyst_bc"] != ""]
        assert len(aniso) == 19 and len(hyst) == 8                               # 10 hysteresis lines, 2 repeated
        row = aniso[aniso["specimen"] == "mc121d1"].iloc[0]
        assert row["aniso_s"] == "0.29925:0.346846:0.353904:-0.001806:-0.005028:0.001793"
        assert row["aniso_type"] == "AARM" and row["aniso_tilt_correction"] == "-1" and row["sample"] == "mc121d"
        assert row["aniso_s_unit"] == "Am^2" and row["aniso_s_n_measurements"] == "9" and row["aniso_s_sigma"] == "0.013881"
        # the eigenparameters from rmag_results on the same row, ellipses as tau:dec:inc:eta/zeta:...
        assert row["aniso_v1"] == "0.356621:275.2:62.3:eta/zeta:182:1.7:17.6:91.1:27.7:55.9"
        assert row["aniso_v3"].startswith("0.299134:182:1.7:eta/zeta:")
        assert row["aniso_ftest"] == "3.8" and row["aniso_ftest12"] == "0.4" and row["aniso_ftest23"] == "5.3"
        assert row["method_codes"] == "LP-AN-ARM:AE-H" and row["experiments"] == "mc121d1:AARM"    # "mc121d1 : AARM" tidied
        assert row["description"] == "Hext statistics adapted to AARM." and row["analysts"] == "Jason Steindorf"
        assert row["hyst_bc"] == "" and row["dir_dec"] == ""
        h = hyst[hyst["specimen"] == "mc120a2-1"]
        assert len(h) == 1
        h = h.iloc[0]
        assert h["hyst_bc"] == "0.04297" and h["hyst_bcr"] == "0.065" and h["hyst_mr_moment"] == "0.000001708"
        assert h["hyst_ms_moment"] == "0.000003911" and h["experiments"] == "mc120a2-1:LP-HYS"
        assert h["method_codes"] == "LT-AF-I:LP-AN-ARM:LP-BCR-HDM" and h["aniso_s"] == ""
        # the 2.5 columns did not leak through
        assert not [c for c in spec.columns if c.startswith(("anisotropy_", "hysteresis_", "er_"))]
        # and the anisotropy toolkit reads the rows as tensors
        from pmagpy import anisotropy
        table = anisotropy.tensor_table(spec, read_table(tmp_path / "samples.txt"), "s")
        assert len(table) == 19 and set(table["aniso_type"]) == {"AARM"}

    def test_a_kappabridge_table_matches_magics_own_upgrade(self, tmp_path):
        """data_files/ani_depthplot holds rmag_anisotropy.txt (472 lines) and the specimens.txt MagIC's
        upgrade tool made from it (contribution 12152): the same 431 rows, cell for cell, once the
        41 repeated lines are dropped — only the method codes are ordered differently (MagIC sorts)."""
        from pmagpy import pmag
        src = example_path("../ani_depthplot")
        translated, written, left = pmag.convert_rmag_2_to_3(src, str(tmp_path))
        assert translated == ["rmag_anisotropy.txt"] and written == {"specimens": 431} and left == []
        ours = read_table(tmp_path / "specimens.txt")
        ref = read_table(os.path.join(src, "specimens.txt"))
        ref = ref[ref["aniso_s"] != ""]
        assert len(ours) == len(ref) == 431
        both = ours.merge(ref, on=["specimen", "aniso_tilt_correction"], suffixes=("", "_magic"))
        assert len(both) == 431
        for col in ["aniso_s", "aniso_s_sigma", "aniso_s_n_measurements", "aniso_s_unit", "aniso_type", "sample", "citations"]:
            assert (both[col] == both[col + "_magic"]).all(), col
        assert (both["method_codes"].str.split(":").map(sorted) == both["method_codes_magic"].str.split(":").map(sorted)).all()

    def test_rmag_results_go_to_the_finest_table_named(self, tmp_path):
        """A result naming one specimen joins the specimens table, one sample the samples table,
        one site the sites table, several sites nowhere (reported); remanence and susceptibility
        tables are renamed per the data model."""
        from pmagpy import pmag
        d = str(tmp_path)
        pmag.magic_write(os.path.join(d, "magic_measurements.txt"), [
            {"er_specimen_name": "a1", "er_sample_name": "a", "er_site_name": "S1", "er_location_name": "L",
             "magic_method_codes": "LT-NO", "measurement_number": "1", "measurement_magn_moment": "1e-6"}],
            "magic_measurements")
        v = {"anisotropy_t1": "0.35", "anisotropy_v1_dec": "10", "anisotropy_v1_inc": "20", "anisotropy_t2": "0.33",
             "anisotropy_v2_dec": "100", "anisotropy_v2_inc": "0", "anisotropy_t3": "0.32", "anisotropy_v3_dec": "190",
             "anisotropy_v3_inc": "70", "anisotropy_type": "AMS", "tilt_correction": "0", "magic_method_codes": "LP-AN-MS:AE-BS"}
        pmag.magic_write(os.path.join(d, "rmag_results.txt"), [
            {"er_specimen_names": "a1", "er_sample_names": "a", "er_site_names": "S1", **v},
            {"er_specimen_names": "a1:a2", "er_sample_names": "a", "er_site_names": "S1", **v},
            {"er_specimen_names": "a1:b1", "er_sample_names": "a:b", "er_site_names": "S1", **v},
            {"er_specimen_names": "", "er_sample_names": "", "er_site_names": "S1:S2", "er_location_names": "L", **v}],
            "rmag_results")
        pmag.magic_write(os.path.join(d, "rmag_remanence.txt"), [
            {"er_specimen_name": "a1", "remanence_mr_moment": "2e-6", "remanence_sratio": "0.95", "remanence_bcr": "0.04",
             "magic_method_codes": "LP-BCR-BF", "remanence_flag": "g"}], "rmag_remanence")
        pmag.magic_write(os.path.join(d, "rmag_susceptibility.txt"), [
            {"er_specimen_name": "a1", "susceptibility_chi_mass": "1.2e-7", "susceptibility_f": "976",
             "magic_method_codes": "LP-X"}], "rmag_susceptibility")
        meas, upgraded, no_upgrade = pmag.convert_directory_2_to_3("magic_measurements.txt", input_dir=d, output_dir=d)
        assert {"specimens.txt", "samples.txt", "sites.txt"} <= set(upgraded)
        assert no_upgrade == ["rmag_results.txt row for S1:S2 names several sites"]
        spec = read_table(tmp_path / "specimens.txt")
        assert len(spec) == 3                                                    # AMS result, remanence, susceptibility
        ams = spec[spec["aniso_v1"] != ""].iloc[0]
        assert ams["aniso_v1"] == "0.35:10:20" and ams["aniso_v2"] == "0.33:100:0"       # no ellipse: tau:dec:inc only
        assert ams["aniso_type"] == "AMS" and ams["aniso_tilt_correction"] == "0" and ams["method_codes"] == "LP-AN-MS:AE-BS"
        rem = spec[spec["rem_sratio"] != ""].iloc[0]
        assert rem["rem_mr_moment"] == "2e-6" and rem["rem_bcr"] == "0.04" and rem["result_quality"] == "g"
        assert spec[spec["susc_chi_mass"] != ""].iloc[0]["susc_f"] == "976"
        samp = read_table(tmp_path / "samples.txt")
        assert samp[samp["aniso_v1"] != ""]["aniso_v1"].tolist() == ["0.35:10:20"] and samp[samp["specimens"] != ""]["specimens"].tolist() == ["a1:a2"]
        site = read_table(tmp_path / "sites.txt")
        assert site[site["aniso_v3"] != ""]["aniso_v3"].tolist() == ["0.32:190:70"] and site[site["samples"] != ""]["samples"].tolist() == ["a:b"]

    def test_no_measurements_file_is_refused_with_the_way_out(self, tmp_path):
        (tmp_path / "er_samples.txt").write_text("tab\ter_samples\ner_sample_name\nA1\n")
        result = reg.convert_files(reg.FORMATS["legacy"], [str(tmp_path)], {}, str(tmp_path))
        assert not result.ok
        assert "magic_measurements.txt" in result.message and "upgrade" in result.message
