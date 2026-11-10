"""
Tests for ipmag.zeq and for how stored fits are read and drawn by
ipmag.zeq_magic: the summary for fits without a MAD, the fit drawn on the
Zijderveld diagram by pmagplotlib.plot_dir for free lines, anchored lines and
vector means, and the reading of the fit type from MagIC method codes.
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag, pmag


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


@pytest.fixture
def offset_steps():
    """Steps that decay along 030/45, offset from the origin by a constant vector."""
    offset = np.array(pmag.dir2cart([300., 10., 0.3]))
    steps = [np.array(pmag.dir2cart([30., 45., moment])) + offset
             for moment in (1.0, 0.8, 0.6, 0.4, 0.2)]
    directions = np.array([pmag.cart2dir(step) for step in steps])
    return pd.DataFrame({'specimen': 'spc01',
                         'treatment': [0, 100, 200, 300, 400],
                         'intensity': directions[:, 2],
                         'declination': directions[:, 0],
                         'inclination': directions[:, 1]})


def _fit_line(data, calculation_type):
    """Ends of the fit that ipmag.zeq draws on the X,Y projection."""
    ipmag.zeq(data=data, units='C', begin_pca=0, end_pca=4,
              calculation_type=calculation_type, show_data=False)
    green = matplotlib.colors.to_rgba('g')
    fits = [line for line in plt.figure(1).axes[0].lines  # the Zijderveld diagram is figure 1
            if matplotlib.colors.to_rgba(line.get_color()) == green]
    assert len(fits) == 2  # X,Y and X,Z projections
    return np.column_stack([fits[0].get_xdata(), fits[0].get_ydata()])


def _distance_from_origin(ends):
    """Distance of the origin from the line through the two ends."""
    (x1, y1), (x2, y2) = ends
    return abs(x1 * y2 - x2 * y1) / np.hypot(x2 - x1, y2 - y1)


class TestZeq:
    """ipmag.zeq with each kind of line fit."""

    def test_summary_without_mad(self, offset_steps, capsys):
        """A vector mean has no MAD; the summary is printed without one."""
        ipmag.zeq(data=offset_steps, units='C', begin_pca=0, end_pca=4,
                  calculation_type='DE-VM', make_plots=False, show_data=False)
        summary = capsys.readouterr().out.splitlines()[-1].split()
        assert summary[:3] == ['spc01', 'DE-VM', '5']
        assert len(summary) == 7  # specimen, type, N, min, max, dec, inc

    def test_summary_with_mad(self, offset_steps, capsys):
        """A line has a MAD in the summary."""
        ipmag.zeq(data=offset_steps, units='C', begin_pca=0, end_pca=4,
                  calculation_type='DE-BFL', make_plots=False, show_data=False)
        summary = capsys.readouterr().out.splitlines()[-1].split()
        assert summary[:3] == ['spc01', 'DE-BFL', '5']
        assert len(summary) == 8

    def test_free_line_is_drawn_through_centre_of_mass(self, offset_steps):
        assert _distance_from_origin(_fit_line(offset_steps, 'DE-BFL')) > 0.05

    def test_anchored_line_is_drawn_through_origin(self, offset_steps):
        assert _distance_from_origin(_fit_line(offset_steps, 'DE-BFL-A')) < 1e-9

    def test_vector_mean_is_drawn_through_origin(self, offset_steps):
        assert _distance_from_origin(_fit_line(offset_steps, 'DE-VM')) < 1e-9


class TestFitTypeFromMethodCodes:
    """The kind of fit that the method codes of an interpretation describe."""

    @pytest.mark.parametrize("method_codes, expected", [
        ('LP-DIR-T:DE-BFL:DA-DIR', 'DE-BFL'),
        ('LP-DIR-AF:DE-BFL-A:DA-DIR-GEO', 'DE-BFL-A'),
        ('DE-BFL-O:LP-DIR-T', 'DE-BFL-O'),         # not read as a free line
        ('LP-DIR-T:DE-BFP', 'DE-BFP'),
        ('LP-DIR-T:DE-VM:DA-DIR-TILT', 'DE-VM'),
        ('LP-DIR-T:DE-FM-LP', 'DE-FM'),            # a more specific code
        ('LP-DIR-T:DA-DIR', None),                 # no code for the type of fit
        ('', None),
    ])
    def test_fit_type(self, method_codes, expected):
        assert ipmag._fit_type_from_method_codes(method_codes) == expected
