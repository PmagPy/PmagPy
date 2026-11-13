"""Regression tests for the DM3 paths of the legacy-model CLI commands."""

import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest


DATA = Path(__file__).resolve().parents[2] / "data_files"


@pytest.mark.parametrize("model_args", [[], ["-DM", "3"], ["-DM", "3.0"]])
@pytest.mark.parametrize(
    ("program", "input_file", "output_tables"),
    [
        ("azdip_magic", DATA / "azdip_magic" / "azdip_magic_example.dat", ["samples"]),
        ("orientation_magic", DATA / "orientation_magic" / "orient_example.txt",
         ["samples", "sites"]),
    ],
)
def test_orientation_converters_use_dm3(
    program, input_file, output_tables, model_args, tmp_path, monkeypatch
):
    module = importlib.import_module(f"programs.{program}")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [program, "-f", str(input_file), *model_args])

    module.main()

    for table in output_tables:
        output = tmp_path / (table + ".txt")
        assert output.read_text(encoding="utf-8").splitlines()[0].split()[-1] == table


@pytest.mark.parametrize("model_args", [[], ["-dm", "3"], ["-dm", "3.0"]])
def test_pt_rot_writes_dm3_locations(model_args, tmp_path, monkeypatch):
    from programs import pt_rot

    input_file = tmp_path / "points.txt"
    input_file.write_text("10 20 saf 0\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["pt_rot", "-f", "points.txt", "-F", "out.txt", *model_args]
    )

    pt_rot.main()

    lines = (tmp_path / "out.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0].split()[-1] == "locations"
    assert {"pole_lon", "pole_lat"} <= set(lines[1].split("\t"))


@pytest.mark.parametrize(
    ("point", "sequential", "expected_lon"),
    [
        ("10 20", True, 40),
        ("10 20 eur 10", False, 40),
        ("10 20 saf 10 eur", False, 340),
        ("10 20 saf 10", False, 10),
    ],
)
def test_pt_rot_location_coordinates(point, sequential, expected_lon, tmp_path, monkeypatch):
    from programs import pt_rot

    (tmp_path / "points.txt").write_text(point + "\n", encoding="utf-8")
    (tmp_path / "poles.txt").write_text("90 0 30\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pt_rot.frp, "get_pole", lambda plate, age: [90, 0, 30])
    input_args = ["-ff", "points.txt", "poles.txt"] if sequential else ["-f", "points.txt"]
    monkeypatch.setattr(sys, "argv", ["pt_rot", *input_args, "-F", "out.txt"])

    pt_rot.main()

    records = pd.read_csv("out.txt", sep="\t", header=1)
    assert records.loc[0, "pole_lon"] == pytest.approx(expected_lon)
    assert records.loc[0, "pole_lat"] == pytest.approx(20)


@pytest.mark.parametrize("model_args", [[], ["-DM", "3"], ["-DM", "3.0"]])
def test_core_depthplot_passes_dm3(model_args, tmp_path, monkeypatch):
    pytest.importorskip("wx")
    from programs import core_depthplot

    calls = []

    def plot(*args):
        calls.append(args)
        return object(), "plot.png"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["core_depthplot", "-sav", *model_args])
    monkeypatch.setattr(core_depthplot.ipmag, "core_depthplot", plot)
    monkeypatch.setattr(core_depthplot.plt, "savefig", lambda name: None)

    core_depthplot.main()

    assert len(calls) == 1
    assert calls[0][-1] == 3


def test_core_depthplot_saves_dm3_plot(tmp_path, monkeypatch):
    pytest.importorskip("wx")
    from programs import core_depthplot

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["core_depthplot", "-ID", str(DATA / "core_depthplot"),
         "-fsa", "samples.txt", "-LP", "AF", "15", "-sav", "-fmt", "png"],
    )

    core_depthplot.main()

    plots = list(tmp_path.glob("*.png"))
    assert len(plots) == 1
    assert plots[0].stat().st_size > 0


@pytest.mark.parametrize("model_args", [[], ["-dm", "3"], ["-dm", "3.0"]])
def test_magic_select_uses_dm3_age(model_args, tmp_path, monkeypatch):
    from programs import magic_select
    from pmagpy import pmag

    (tmp_path / "sites.txt").write_text(
        "tab\tsites\nsite\tage\tage_unit\nS1\t2500\tka\nS2\t2900\tka\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["magic_select", "-f", "sites.txt", "-F", "selected.txt",
         "-key", "age", "2.5", "eval", *model_args],
    )

    magic_select.main()

    records, table = pmag.magic_read("selected.txt")
    assert table == "sites"
    assert [record["site"] for record in records] == ["S1"]
    assert float(records[0]["age"]) == 2.5
    assert records[0]["age_unit"] == "Ma"


def test_magic_select_uses_dm3_model_lat(tmp_path, monkeypatch):
    from programs import magic_select

    (tmp_path / "sites.txt").write_text(
        "tab\tsites\nsite\tage\tage_unit\tlat\tpaleolat\tdir_inc\tage_low\tage_high\n"
        "young\t1000\tka\t33.25\t20\t\t\t\n"
        "old\t10\tMa\t15\t42\t\t\t\n"
        "inclination\t6\tMa\t\t\t45\t\t\n"
        "no_age\t\t\t\t-12\t\t\t\n"
        "boundary\t5000\tka\t10\t50\t\t\t\n"
        "near_boundary\t4999.99\tka\t11.5\t50\t\t\t\n"
        "range\t\tka\t45.25\t\t\t1000\t3000\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["magic_select", "-f", "sites.txt", "-F", "selected.txt",
         "-key", "model_lat", "-90", "min"],
    )

    magic_select.main()

    records = pd.read_csv("selected.txt", sep="\t", header=1).set_index("site")
    assert "model_lat" not in records.columns
    assert records["paleolat"].to_dict() == {
        "young": 33.25, "old": 42, "inclination": 26.6, "no_age": -12,
        "boundary": 50, "near_boundary": 11.5, "range": 45.25,
    }
    assert records.loc["young", "age"] == 1
    assert records.loc["young", "age_unit"] == "Ma"
    assert records.loc["range", "age"] == 2

    monkeypatch.setattr(
        sys, "argv",
        ["magic_select", "-f", "sites.txt", "-F", "selected.txt",
         "-key", "model_lat", "33.25", "eval"],
    )
    magic_select.main()
    selected = pd.read_csv("selected.txt", sep="\t", header=1)
    assert selected["site"].tolist() == ["young"]
    assert selected.loc[0, "paleolat"] == 33.25


def test_magic_select_rejects_unknown_age_unit_for_model_lat(tmp_path, monkeypatch):
    from programs import magic_select

    (tmp_path / "sites.txt").write_text(
        "tab\tsites\nsite\tage\tage_unit\tlat\nS1\t1000\tunknown\t33\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["magic_select", "-f", "sites.txt", "-F", "selected.txt",
         "-key", "model_lat", "0", "min"],
    )

    with pytest.raises(ValueError, match="Unsupported or missing age unit"):
        magic_select.main()

    assert not (tmp_path / "selected.txt").exists()


def test_convert_lat_preserves_legacy_fields_and_handles_dm3_zeroes():
    from pmagpy import pmag

    legacy = {"average_age": "1", "site_lat": "12"}
    assert pmag.convert_lat([legacy])[0]["model_lat"] == "12"
    records = [{"age": 0, "lat": 0}, {"paleolat": 0}, {"dir_inc": 0}]
    assert [float(rec["paleolat"]) for rec in pmag.convert_lat(records, 3)] == [0, 0, 0]


@pytest.mark.parametrize(
    ("methods", "args", "expected"),
    [
        (("DE-BFL", "DE-FM"), [], [[1.0, 10.0], [2.0, 20.0]]),
        (("LP-IRM", "LP-TRM"), ["-mcd", "LP-TRM"], [[2.0, 20.0]]),
    ],
)
def test_strip_magic_plots_dm3_method_codes(methods, args, expected, tmp_path, monkeypatch):
    from programs import strip_magic

    (tmp_path / "sites.txt").write_text(
        "tab\tsites\nsite\tcore_depth\tdir_dec\tmethod_codes\n"
        f"S1\t1\t10\t{methods[0]}\nS2\t2\t20\t{methods[1]}\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["strip_magic", "-f", "sites.txt", "-x", "pos", "-y", "dec", "-sav", *args],
    )
    plotted = []
    monkeypatch.setattr(strip_magic.pmagplotlib, "isServer", False)
    monkeypatch.setattr(strip_magic.pmagplotlib, "plot_init", lambda *args: None)
    monkeypatch.setattr(strip_magic.pmagplotlib, "plot_strat",
                        lambda fig, data, labels: plotted.append(data))
    monkeypatch.setattr(strip_magic.pmagplotlib, "save_plots", lambda *args: None)

    strip_magic.main()

    assert plotted == [expected]


@pytest.mark.parametrize("interactive", [False, True])
def test_combine_magic_dm3(interactive, tmp_path, monkeypatch):
    from programs import combine_magic

    input_dir = tmp_path / "input files" if interactive else tmp_path
    input_dir.mkdir(exist_ok=True)
    for name in ("S1", "S2"):
        (input_dir / (name + ".txt")).write_text(
            f"tab\tsites\nsite\n{name}\n", encoding="utf-8"
        )
    monkeypatch.chdir(tmp_path)
    if interactive:
        answers = iter([str(input_dir / "S1.txt"), str(input_dir / "S2.txt"),
                        "", "combined.txt"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
        args = ["-i", "-dm", "3.0"]
    else:
        args = ["-dm", "3.0", "-F", "combined.txt", "-f", "S1.txt", "S2.txt"]
    monkeypatch.setattr(sys, "argv", ["combine_magic", *args])

    combine_magic.main()

    header = (tmp_path / "combined.txt").read_text(encoding="utf-8").splitlines()[0]
    assert header.split()[-1] == "sites"
    records = pd.read_csv("combined.txt", sep="\t", header=1)
    assert set(records["site"]) == {"S1", "S2"}


@pytest.mark.parametrize("absolute", [False, True])
def test_combine_magic_noninteractive_paths_with_spaces(absolute, tmp_path, monkeypatch):
    from programs import combine_magic

    input_dir = tmp_path / "input files"
    input_dir.mkdir()
    filenames = []
    for name in ("S1", "S2"):
        filename = input_dir / f"{name} file.txt"
        filename.write_text(f"tab\tsites\nsite\n{name}\n", encoding="utf-8")
        filenames.append(str(filename) if absolute else filename.name)
    monkeypatch.setattr(
        sys, "argv",
        ["combine_magic", "-WD", str(input_dir), "-F", "combined output.txt",
         "-f", *filenames],
    )

    combine_magic.main()

    records = pd.read_csv(input_dir / "combined output.txt", sep="\t", header=1)
    assert set(records["site"]) == {"S1", "S2"}


def test_combine_magic_helper_accepts_single_path_with_spaces(tmp_path, monkeypatch):
    from programs import combine_magic

    calls = []
    monkeypatch.setattr(
        combine_magic.ipmag, "combine_magic",
        lambda filenames, outfile, data_model: calls.append((filenames, outfile, data_model)),
    )

    combine_magic.combine("input file.txt", "output file.txt", str(tmp_path), 3)

    assert calls == [([str(tmp_path / "input file.txt")],
                      str(tmp_path / "output file.txt"), 3)]


@pytest.mark.parametrize("interactive", [False, True])
def test_download_magic_dm3(interactive, tmp_path, monkeypatch):
    from programs import download_magic
    from pmagpy import pmag

    (tmp_path / "download.txt").write_text(
        "tab\tsites\nsite\tmethod_codes\nS1\tLP-DIR-AF\n>>>>>>>>>>\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    if interactive:
        monkeypatch.setattr("builtins.input", lambda prompt: "download.txt")
        args = ["-i", "-DM", "3.0"]
    else:
        args = ["-f", "download.txt", "-DM", "3.0"]
    monkeypatch.setattr(sys, "argv", ["download_magic", *args])

    download_magic.main()

    records, table = pmag.magic_read("sites.txt")
    assert table == "sites"
    assert records[0]["site"] == "S1"
