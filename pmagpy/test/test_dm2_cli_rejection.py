"""Tests that DM3-only CLI programs reject MagIC Data Model 2."""

import importlib
import sys

import pytest


PROGRAMS = [
    ("foldtest_magic", "-DM"),
    ("irmaq_magic", "-DM"),
    ("lnp_magic", "-DM"),
    ("lowrie_magic", "-DM"),
    ("revtest_magic", "-DM"),
    ("strip_magic", "-DM"),
    ("trmaq_magic", "-DM"),
    ("scalc_magic", "-dm"),
    ("magic_select", "-dm"),
    ("combine_magic", "-dm"),
    ("download_magic", "-DM"),
    ("azdip_magic", "-DM"),
    ("orientation_magic", "-DM"),
    ("core_depthplot", "-DM"),
    ("pt_rot", "-dm"),
]


@pytest.mark.parametrize(("program", "model_option"), PROGRAMS)
def test_dm2_is_rejected_before_io(program, model_option, tmp_path, monkeypatch):
    if program == "core_depthplot":
        pytest.importorskip("wx")
    module = importlib.import_module(f"programs.{program}")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [program + ".py", model_option, "2"])

    with pytest.raises(SystemExit) as error:
        module.main()

    assert f"{program} supports MagIC Data Model 3 only" in str(error.value)
    assert "Convert Data Model 2 files to Data Model 3" in str(error.value)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(("program", "model_option"), PROGRAMS[-7:])
def test_dm25_is_rejected_before_io(program, model_option, tmp_path, monkeypatch):
    if program == "core_depthplot":
        pytest.importorskip("wx")
    module = importlib.import_module(f"programs.{program}")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [program + ".py", model_option, "2.5"])

    with pytest.raises(SystemExit, match="supports MagIC Data Model 3 only"):
        module.main()

    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("model", ["3.1", "3.5", "3.9"])
def test_foldtest_rejects_nonintegral_models_before_io(model, tmp_path, monkeypatch):
    from programs import foldtest_magic

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["foldtest_magic", "-DM", model])

    with pytest.raises(SystemExit, match="supports MagIC Data Model 3 only"):
        foldtest_magic.main()

    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(("program", "model_option"), [
    ("combine_magic", "-dm"), ("download_magic", "-DM"),
])
def test_interactive_dm2_is_rejected_before_prompt(program, model_option, monkeypatch):
    module = importlib.import_module(f"programs.{program}")
    monkeypatch.setattr(sys, "argv", [program, "-i", model_option, "2"])
    monkeypatch.setattr("builtins.input", lambda prompt: pytest.fail("unexpected prompt"))

    with pytest.raises(SystemExit, match="supports MagIC Data Model 3 only"):
        module.main()
