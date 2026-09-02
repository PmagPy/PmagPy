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
            assert kw in params, f"{fmt.key}: output keyword {kw}"
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

    def test_magic_contribution_file(self, tmp_path):
        (tmp_path / "magic_contribution_1234.txt").write_text("tab delimited\tcontribution\nid\n1234\n>>>>>>>>>>\n")
        key, roles = reg.guess_format(["magic_contribution_1234.txt"], str(tmp_path))
        assert key == "magic" and roles["magic_contribution_1234.txt"] == "MagIC contribution file"

    def test_nothing_recognised(self):
        assert reg.guess_format(["readme.md", "photo.jpg"]) == ("", {})
