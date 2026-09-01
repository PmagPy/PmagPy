"""Regression tests for the Thellier GUI plot layout."""

import ast
from pathlib import Path


THELLIER_GUI = (
    Path(__file__).resolve().parents[2] / "programs" / "thellier_gui.py"
)


def _names(node):
    """Return identifier and attribute names contained in an AST node."""
    return {
        child.id if isinstance(child, ast.Name) else child.attr
        for child in ast.walk(node)
        if isinstance(child, (ast.Name, ast.Attribute))
    }


def test_main_plot_columns_preserve_their_aspect_ratios():
    """Both halves of the plot panel use wx's aspect-preserving sizer flag."""
    tree = ast.parse(THELLIER_GUI.read_text())
    assignments = {
        target.id: value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
        for value in (node.value,)
    }
    plot_sizer_flags = assignments["plot_sizer_flags"]
    assert "SHAPED" in _names(plot_sizer_flags)

    shaped_items = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or len(node.args) < 3:
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "Add":
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        if node.func.value.id != "sizer_plots_outer":
            continue
        if "plot_sizer_flags" not in _names(node.args[2]):
            continue
        shaped_items.update(_names(node.args[0]))

    assert {"canvas1", "sizer_grid_plots"} <= shaped_items
