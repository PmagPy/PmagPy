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
        "tab\tsites\nsite\tage\tage_unit\nS1\t1000\tka\nS2\t5000\tka\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv",
        ["magic_select", "-f", "sites.txt", "-F", "selected.txt",
         "-key", "age", "1", "eval", *model_args],
    )

    magic_select.main()

    records, table = pmag.magic_read("selected.txt")
    assert table == "sites"
    assert [record["site"] for record in records] == ["S1"]
    assert records[0]["age_unit"] == "Ma"


@pytest.mark.parametrize("interactive", [False, True])
def test_combine_magic_dm3(interactive, tmp_path, monkeypatch):
    from programs import combine_magic

    for name in ("S1", "S2"):
        (tmp_path / (name + ".txt")).write_text(
            f"tab\tsites\nsite\n{name}\n", encoding="utf-8"
        )
    monkeypatch.chdir(tmp_path)
    if interactive:
        answers = iter(["S1.txt", "S2.txt", "", "combined.txt"])
        monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
        args = ["-i", "-dm", "3.0"]
    else:
        args = ["-dm", "3.0", "-F", "combined.txt", "-f", "S1.txt", "S2.txt"]
    monkeypatch.setattr(sys, "argv", ["combine_magic", *args])

    combine_magic.main()

    assert (tmp_path / "combined.txt").read_text(encoding="utf-8").splitlines()[0].split()[-1] == "sites"
    records = pd.read_csv("combined.txt", sep="\t", header=1)
    assert set(records["site"]) == {"S1", "S2"}


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
