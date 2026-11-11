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
]


@pytest.mark.parametrize(("program", "model_option"), PROGRAMS)
def test_dm2_is_rejected_before_io(program, model_option, tmp_path, monkeypatch):
    module = importlib.import_module(f"programs.{program}")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [program + ".py", model_option, "2"])

    with pytest.raises(SystemExit) as error:
        module.main()

    assert f"{program} supports MagIC Data Model 3 only" in str(error.value)
    assert "Convert Data Model 2 files to Data Model 3" in str(error.value)
    assert not list(tmp_path.iterdir())
