"""
pmagpy-convert: the converter registry as a command.

The command is built from the same Formats the hub's Convert page is, so the
tests check that every field becomes an option, that the options reach the
converter as the registry's values do, and that the conversion lands where a
script's would -- tables and log alike.
"""
import argparse
import io
import os
import shutil

import pytest

from pmagpy import convert_cli as cli
from pmagpy import convert_registry as reg

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data_files", "convert_2_magic")


def example(rel):
    return os.path.join(DATA, rel)


def run(*args):
    out = io.StringIO()
    code = cli.main(list(args), out=out)
    return code, out.getvalue()


class TestOptionsFromFields:
    def test_every_format_builds_a_parser_with_one_option_per_field(self):
        for fmt in reg.FORMATS.values():
            parser = cli.build_parser(fmt)
            dests = {a.dest for a in parser._actions}
            assert {f.name for f in fmt.fields} <= dests, fmt.key
            assert ("files" in dests) is (not fmt.takes_directory), fmt.key

    def test_names_dash_and_a_bool_on_by_default_is_turned_off(self):
        cit = reg.FORMATS["cit"]
        assert cli.option_name(next(f for f in cit.fields if f.name == "samp_con")) == "--samp-con"
        assert cli.option_name(next(f for f in cit.fields if f.name == "noave")) == "--no-noave"      # default True
        assert cli.option_name(next(f for f in reg.FORMATS["sio"].fields if f.name == "noave")) == "--noave"
        ns = cli.build_parser(cit).parse_args(["x.sam", "--no-noave"])
        assert cli.field_values(cit, ns) == {"noave": False}
        ns = cli.build_parser(reg.FORMATS["sio"]).parse_args(["x.dat", "--noave"])
        assert cli.field_values(reg.FORMATS["sio"], ns) == {"noave": True}

    def test_values_are_typed_and_only_the_given_ones_are_passed(self):
        sio = reg.FORMATS["sio"]
        ns = cli.build_parser(sio).parse_args(["a.dat", "b.dat", "--codelist", "AF", "T", "--specnum", "1",
                                              "--labfield", "25", "--location", "Hawaii"])
        assert ns.files == ["a.dat", "b.dat"]
        assert cli.field_values(sio, ns) == {"codelist": ["AF", "T"], "specnum": 1, "labfield": 25.0, "location": "Hawaii"}

    def test_a_choice_outside_the_list_is_refused(self, capsys):
        with pytest.raises(SystemExit) as exc:
            cli.build_parser(reg.FORMATS["sio"]).parse_args(["a.dat", "--codelist", "XYZ"])
        assert exc.value.code == 2 and "invalid choice" in capsys.readouterr().err
        with pytest.raises(SystemExit):
            cli.build_parser(reg.FORMATS["sio"]).parse_args(["a.dat", "--specnum", "one"])

    def test_help_spells_out_naming_codes_choices_and_defaults(self):
        text = cli.build_parser(reg.FORMATS["sio"]).format_help()
        assert "--samp-con CODE" in text and "4 = XXXX[YYY]" in text and "Default 1." in text
        codelist = next(f for f in reg.FORMATS["sio"].fields if f.name == "codelist")
        assert "AF = AF demagnetization" in cli.field_help(codelist)
        assert "--noave" in text and "Keep replicate measurements. Without this: average replicate measurements." in " ".join(text.split())
        cit = cli.build_parser(reg.FORMATS["cit"]).format_help()          # CIT keeps them by default, so the flag is the other way
        assert "--no-noave" in cit and "Average replicate measurements. Without this: keep replicate measurements." in " ".join(cit.split())
        plain = next(f for f in reg.FORMATS["2g_bin"].fields if f.kind == "bool" and not f.choices)   # a one-way checkbox
        assert "unless this is given." in cli.field_help(plain)
        assert "Example: pmagpy-convert sio sio_af_example.dat --location Hawaii --specnum 1 --codelist AF" in text
        assert "pmagpy.convert_2_magic.sio" in text
        tdt = cli.build_parser(reg.FORMATS["tdt"]).format_help()
        assert "Reads the whole directory given by --dir" in tdt
        assert "FILE" not in tdt.split("options:")[0].split("usage:")[1]          # no files in a directory format's usage
        assert "Needs specimens.txt in --dir first." in cli.build_parser(reg.FORMATS["iodp_dscr"]).format_help()

    def test_a_blank_choice_is_not_offered(self):
        text = cli.build_parser(reg.FORMATS["sio"]).format_help()
        assert "--coil {1,2,3}" in text


class TestRunning:
    def test_no_arguments_lists_the_formats(self):
        code, text = run()
        assert code == 0 and "  sio" in text and "  cit" in text and "CIT (.sam)" in text and "tdt" in text
        assert "a directory" in text                                            # tdt, livdb
        assert run("--help")[0] == 0

    def test_an_unknown_format_is_refused_with_a_hint(self):
        code, text = run("SIO", "a.dat")
        assert code == 2 and "no format called 'SIO'" in text and "Did you mean sio" in text

    def test_a_conversion_writes_the_tables_and_the_log_where_a_script_would(self, tmp_path):
        d = str(tmp_path)
        code, text = run("sio", example("sio_magic/sio_af_example.dat"), "--codelist", "AF", "--location", "Hawaii",
                         "--specnum", "1", "--dir", d)
        assert code == 0, text
        assert "converted" in text and f"Tables written to {d}" in text
        assert os.path.exists(os.path.join(d, "measurements.txt"))
        (entry,) = reg.read_conversions(d)
        assert entry["format"] == "sio" and entry["files"] == ["sio_af_example.dat"]
        assert entry["values"] == {"codelist": ["AF"], "location": "Hawaii", "specnum": 1}

    def test_files_are_found_from_the_directory_and_append_and_no_record_are_honoured(self, tmp_path):
        d = str(tmp_path)
        shutil.copy(example("sio_magic/sio_af_example.dat"), tmp_path / "af.dat")
        shutil.copy(example("sio_magic/sio_thermal_example.dat"), tmp_path / "thermal.dat")
        code, text = run("sio", "af.dat", "--codelist", "AF", "--dir", d)
        assert code == 0, text
        n = sum(1 for _ in open(tmp_path / "measurements.txt"))
        code, text = run("sio", "thermal.dat", "--codelist", "T", "--labfield", "25", "--dir", d, "--append",
                         "--no-record", "--log")
        assert code == 0, text
        assert sum(1 for _ in open(tmp_path / "measurements.txt")) > n
        assert "── thermal.dat" in text                                          # --log prints the converter's output
        assert len(reg.read_conversions(d)) == 1                                # --no-record

    def test_a_directory_format_reads_dir(self, tmp_path):
        for name in os.listdir(example("tdt_magic")):
            if name.lower().endswith(".tdt"):
                shutil.copy(example(os.path.join("tdt_magic", name)), tmp_path)
        code, text = run("tdt", "--dir", str(tmp_path), "--location", "ATPI")
        assert code == 0, text
        assert os.path.exists(tmp_path / "measurements.txt")
        (entry,) = reg.read_conversions(str(tmp_path))
        assert entry["files"] and all(f.lower().endswith(".tdt") for f in entry["files"])

    def test_a_failed_conversion_exits_1_and_names_the_file(self, tmp_path):
        bad = tmp_path / "junk.jr6"
        bad.write_text("not a jr6 file\n")
        code, text = run("jr6_jr6", str(bad), "--dir", str(tmp_path))
        assert code == 1 and "Nothing converted" in text
        assert not os.path.exists(tmp_path / "measurements.txt")

    def test_a_naming_code_without_its_count_is_a_usage_error(self, tmp_path, capsys):
        with pytest.raises(SystemExit) as exc:
            run("sio", example("sio_magic/sio_af_example.dat"), "--samp-con", "4", "--dir", str(tmp_path))
        assert exc.value.code == 2 and "needs the number of characters" in capsys.readouterr().err

    def test_setup_py_installs_the_command(self):
        import ast
        setup_py = os.path.join(os.path.dirname(os.path.dirname(HERE)), "setup.py")
        assert "'pmagpy-convert=pmagpy.convert_cli:main'" in open(setup_py).read()
        ast.parse(open(setup_py).read())
