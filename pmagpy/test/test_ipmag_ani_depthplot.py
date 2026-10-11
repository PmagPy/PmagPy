"""Baseline tests for ipmag.ani_depthplot (MagIC data model 3)."""

import os

import matplotlib.pyplot as plt
import pandas as pd
import pytest
from matplotlib.figure import Figure

from pmagpy import contribution_builder as cb
from pmagpy import ipmag

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "data_files"
)
ANISO_DIR = os.path.join(DATA_DIR, "ani_depthplot")
UTESTA_DIR = os.path.join(DATA_DIR, "UTESTA", "UTESTA_MagIC3")
SUMMARY_FILE = "CoreSummary_XXX_UTESTA.csv"

# only core_depth is propagated from sites to samples, so composite_depth is never found
composite_depth_bug = pytest.mark.xfail(
    raises=KeyError, strict=True,
    reason="ani_depthplot cannot use composite_depth held in sites.txt")


@pytest.fixture(autouse=True)
def close_figures():
    """ani_depthplot draws on matplotlib's global figure 1."""
    yield
    plt.close("all")


def test_missing_specimens_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    plot, message = ipmag.ani_depthplot()

    assert plot is False
    assert message == "missing required file type: specimens"


def test_plots_without_measurements_file():
    """A nonexistent measurements file only drops the bulk susceptibility panel."""
    plot, names = ipmag.ani_depthplot(dir_path=ANISO_DIR, meas_file="fake.txt")

    assert isinstance(plot, Figure)
    assert names == ["U1361A_ani_depthplot.svg"]
    assert len(plot.axes) == 4


def test_measurements_add_bulk_susceptibility_panel():
    plot, names = ipmag.ani_depthplot(dir_path=ANISO_DIR)

    assert isinstance(plot, Figure)
    assert names == ["U1361A_ani_depthplot.svg"]
    assert len(plot.axes) == 5
    assert plot.axes[-1].get_xlabel() == "Bulk Susc. (uSI)"


def test_depth_axis_defaults_to_data_range():
    plot, _ = ipmag.ani_depthplot(dir_path=ANISO_DIR)

    ax = plot.axes[0]
    depths = ax.lines[0].get_ydata()
    assert ax.get_ylabel() == "Depth (mbsf)"
    assert ax.get_ylim() == (max(depths), min(depths))


def test_depth_range_limits_plotted_data():
    plot, names = ipmag.ani_depthplot(dmin=20, dmax=40, depth_scale="core_depth",
                                      fmt="png", dir_path=ANISO_DIR)

    ax = plot.axes[0]
    depths = ax.lines[0].get_ydata()
    assert names == ["U1361A_ani_depthplot.png"]
    assert len(depths) > 0
    assert all(20 < depth < 40 for depth in depths)
    assert ax.get_ylim() == (40, 20)


@composite_depth_bug
def test_composite_depth_scale_is_labelled():
    plot, _ = ipmag.ani_depthplot(depth_scale="composite_depth", dir_path=ANISO_DIR)

    assert plot.axes[0].get_ylabel() == "Depth (mcd)"


def test_legacy_depth_scale_name_is_accepted():
    """The GUI and CLI pass sample_core_depth rather than core_depth."""
    plot, _ = ipmag.ani_depthplot(depth_scale="sample_core_depth",
                                  dir_path=ANISO_DIR)

    assert plot.axes[0].get_ylabel() == "Depth (mbsf)"


@pytest.mark.xfail(
    int(pd.__version__.split(".")[0]) >= 3, raises=KeyError, strict=True,
    reason="ani_depthplot reads age_unit with df['age_unit'][0], removed in pandas 3")
def test_age_file_switches_to_age_axis():
    plot, names = ipmag.ani_depthplot(age_file="ages.txt", dir_path=ANISO_DIR)

    assert names == ["U1361A_ani_depthplot.svg"]
    assert plot.axes[0].get_ylabel().startswith("Age (")


def test_missing_age_file_falls_back_to_core_depth():
    plot, _ = ipmag.ani_depthplot(age_file="no_such_ages.txt", dir_path=ANISO_DIR)

    assert plot.axes[0].get_ylabel() == "Depth (mbsf)"


def test_summary_file_marks_core_tops():
    without_summary, _ = ipmag.ani_depthplot(dir_path=UTESTA_DIR,
                                             depth_scale="core_depth")
    n_lines = len(without_summary.axes[0].lines)
    plt.close("all")

    with_summary, names = ipmag.ani_depthplot(dir_path=UTESTA_DIR,
                                              sum_file=SUMMARY_FILE,
                                              depth_scale="core_depth")

    assert names == ["UTESTA_ani_depthplot.svg"]
    assert len(with_summary.axes[0].lines) > n_lines


def test_contribution_object_replaces_file_arguments():
    con = cb.Contribution(ANISO_DIR)

    plot, names = ipmag.ani_depthplot(dmin=20, dmax=40, depth_scale="core_depth",
                                      fmt="png", contribution=con)

    assert isinstance(plot, Figure)
    assert names == ["U1361A_ani_depthplot.png"]
    assert plot.axes[0].get_ylim() == (40, 20)


def test_depth_range_without_data_returns_message():
    plot, message = ipmag.ani_depthplot(dmin=10000, dmax=20000, dir_path=ANISO_DIR)

    assert plot is False
    assert message in ("no data to plot", "No data to plot")
