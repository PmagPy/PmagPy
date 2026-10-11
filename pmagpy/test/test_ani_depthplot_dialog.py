"""Static checks that the anisotropy-vs-depth GUI dialog uses MagIC data model 3.

These parse the source rather than import it so they run without wxPython.
"""

import ast
from pathlib import Path

import pytest

DIALOGS = Path(__file__).resolve().parents[2] / "dialogs" / "pmag_menu_dialogs.py"
LEGACY_NAMES = ("rmag_anisotropy", "er_samples", "er_ages", "magic_measurements")


@pytest.fixture(scope="module")
def dialog():
    tree = ast.parse(DIALOGS.read_text())
    return next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == "Ani_depthplot")


def _ipmag_functions(node):
    return {
        child.attr
        for child in ast.walk(node)
        if isinstance(child, ast.Attribute)
        and isinstance(child.value, ast.Name) and child.value.id == "ipmag"
    }


def test_dialog_plots_with_the_data_model_3_function(dialog):
    assert _ipmag_functions(dialog) == {"ani_depthplot"}


def test_dialog_has_no_data_model_2_file_names(dialog):
    strings = [child.value for child in ast.walk(dialog)
               if isinstance(child, ast.Constant) and isinstance(child.value, str)]

    legacy = [s for s in strings if any(name in s for name in LEGACY_NAMES)]

    assert legacy == []


def test_dialog_offers_the_data_model_3_tables(dialog):
    strings = {child.value for child in ast.walk(dialog)
               if isinstance(child, ast.Constant) and isinstance(child.value, str)}

    assert {"specimens.txt", "sites.txt", "samples.txt", "ages.txt",
            "measurements.txt"} <= strings
