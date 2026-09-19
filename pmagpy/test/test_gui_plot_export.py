"""Regression tests for plot exports used by standalone GUI builds."""

import ast
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
import pytest

from dialogs.plot_export import save_figure


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_BACKENDS = {"WXAgg", "Agg", "PDF", "SVG", "PS"}
SPEC_FILES = (
    "pmag_gui_macos_arm64.spec",
    "pmag_gui_windows.spec",
)


def _matplotlib_backends(spec_path):
    """Return the Matplotlib backends configured in a PyInstaller spec."""
    tree = ast.parse(spec_path.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "Analysis":
            continue
        for keyword in node.keywords:
            if keyword.arg == "hooksconfig":
                hooks_config = ast.literal_eval(keyword.value)
                return set(hooks_config["matplotlib"]["backends"])
    raise AssertionError("Analysis hooksconfig not found in {}".format(spec_path))


@pytest.mark.parametrize("spec_name", SPEC_FILES)
def test_standalone_specs_include_plot_export_backends(spec_name):
    """Standalone builds include every writer offered by GUI save controls."""
    backends = _matplotlib_backends(REPOSITORY_ROOT / spec_name)

    assert REQUIRED_BACKENDS <= backends


@pytest.mark.parametrize("extension", ("png", "pdf", "svg", "eps"))
def test_save_figure_preserves_live_figure_state(tmp_path, extension):
    """Exporting does not replace or resize the canvas displayed by a GUI."""
    figure = Figure(figsize=(5, 3), dpi=100)
    canvas = FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.plot([0, 1], [0, 1])
    original_size = tuple(figure.get_size_inches())
    original_dpi = figure.dpi
    output_path = tmp_path / "plot.{}".format(extension)

    save_figure(figure, output_path, dpi=300)

    assert output_path.is_file()
    assert output_path.stat().st_size > 0
    assert figure.canvas is canvas
    assert tuple(figure.get_size_inches()) == original_size
    assert figure.dpi == original_dpi
