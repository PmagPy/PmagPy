"""
Tests for plotting and output formatting functions in ipmag.py.

Covers plot_net / plot_di (stereographic projection plotting),
fishqq (Fisher QQ plot), and igrf_print (IGRF output formatting).
"""
from contextlib import redirect_stdout
from io import StringIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pmagpy import ipmag


def _new_scatter_points(ax, before_count):
    """Return total points in collections added after before_count."""
    total = 0
    for coll in ax.collections[before_count:]:
        offsets = coll.get_offsets()
        if len(offsets) > 0:
            total += len(offsets)
    return total


# ---------------------------------------------------------------------------
# plot_net / plot_di: stereographic projection
# ---------------------------------------------------------------------------

class TestPlotNetAndPlotDi:
    """Tests for ipmag.plot_net and ipmag.plot_di."""

    def test_execute_without_error(self):
        """plot_net and plot_di execute without error."""
        di_block = ipmag.fishrot(k=20, n=10, dec=40, inc=60,
                                 random_seed=23).tolist()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ipmag.plot_net(ax=ax)
        ipmag.plot_di(di_block=di_block, color='g', marker='^',
                      connect_points=True)
        assert len(fig.axes) == 1
        plt.close(fig)


class TestPlotDiInputTypes:
    """Verify plot_di handles the full range of dec/inc input types."""

    def setup_method(self):
        self.fig = plt.figure()
        self.fig.add_subplot(111)
        ipmag.plot_net(self.fig.number)
        # record how many collections the stereonet grid created
        self.net_collections = len(self.fig.axes[0].collections)

    def teardown_method(self):
        plt.close(self.fig)

    def _point_count(self):
        return _new_scatter_points(self.fig.axes[0], self.net_collections)

    def test_python_lists(self):
        """plot_di works with Python lists."""
        ipmag.plot_di(dec=[0.0, 90.0, 180.0], inc=[30.0, 45.0, 60.0])
        assert self._point_count() == 3

    def test_numpy_arrays(self):
        """plot_di works with numpy arrays."""
        decs = np.array([10.0, 20.0, 30.0, 40.0])
        incs = np.array([50.0, 60.0, 70.0, 80.0])
        ipmag.plot_di(dec=decs, inc=incs)
        assert self._point_count() == 4

    def test_pandas_series(self):
        """plot_di works with pandas Series."""
        decs = pd.Series([100.0, 200.0, 300.0])
        incs = pd.Series([10.0, 20.0, 30.0])
        ipmag.plot_di(dec=decs, inc=incs)
        assert self._point_count() == 3

    def test_scalar_python_float(self):
        """plot_di works with a single Python float."""
        ipmag.plot_di(dec=45.0, inc=60.0)
        assert self._point_count() == 1

    def test_scalar_numpy_float32(self):
        """plot_di works with numpy.float32 scalars (e.g. from hpars dicts)."""
        ipmag.plot_di(dec=np.float32(120.0), inc=np.float32(45.0))
        assert self._point_count() == 1

    def test_scalar_numpy_float64(self):
        """plot_di works with numpy.float64 scalars."""
        ipmag.plot_di(dec=np.float64(250.0), inc=np.float64(-30.0))
        assert self._point_count() == 1

    def test_di_block(self):
        """plot_di works with di_block (nested list of [dec, inc])."""
        di_block = [[0.0, 30.0], [90.0, 45.0], [180.0, -20.0]]
        ipmag.plot_di(di_block=di_block)
        assert self._point_count() == 3

    def test_hemisphere_separation(self):
        """Positive inclinations plot as filled, negative as open symbols."""
        # 2 lower hemisphere (inc >= 0), 1 upper hemisphere (inc < 0)
        ipmag.plot_di(dec=[0.0, 90.0, 180.0], inc=[45.0, 30.0, -50.0])
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        nonempty = [c for c in new_collections if len(c.get_offsets()) > 0]
        # Two scatter collections: one for lower hemisphere, one for upper
        assert len(nonempty) == 2
        sizes = sorted([len(c.get_offsets()) for c in nonempty])
        assert sizes == [1, 2]

    def test_no_spurious_output(self, capsys):
        """Scalar inputs should not produce TypeError messages."""
        ipmag.plot_di(dec=np.float32(45.0), inc=np.float32(60.0))
        captured = capsys.readouterr()
        assert 'TypeError' not in captured.out


# ---------------------------------------------------------------------------
# plot_di_mean: mean direction with alpha_95 circle
# ---------------------------------------------------------------------------

class TestPlotDiMean:
    """Tests for ipmag.plot_di_mean."""

    def setup_method(self):
        self.fig = plt.figure()
        self.fig.add_subplot(111)
        ipmag.plot_net(self.fig.number)
        self.net_collections = len(self.fig.axes[0].collections)
        self.net_lines = len(self.fig.axes[0].lines)

    def teardown_method(self):
        plt.close(self.fig)

    def test_lower_hemisphere(self):
        """Mean with positive inclination plots as filled marker with a95 circle."""
        ipmag.plot_di_mean(dec=40.0, inc=60.0, a95=5.0)
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        assert len(new_collections) == 1  # one scatter for the mean point
        assert len(new_collections[0].get_offsets()) == 1
        # a95 circle drawn as a line
        new_lines = ax.lines[self.net_lines:]
        assert len(new_lines) == 1

    def test_upper_hemisphere(self):
        """Mean with negative inclination plots as open marker."""
        ipmag.plot_di_mean(dec=200.0, inc=-45.0, a95=8.0)
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        assert len(new_collections) == 1
        # open symbol: facecolor should be white
        fc = new_collections[0].get_facecolors()[0]
        assert np.allclose(fc[:3], [1.0, 1.0, 1.0])  # white RGB

    def test_color_and_marker(self):
        """Custom color and marker are applied."""
        ipmag.plot_di_mean(dec=0.0, inc=30.0, a95=3.0, color='r', marker='s')
        ax = self.fig.axes[0]
        coll = ax.collections[self.net_collections]
        # edge color should be red
        ec = coll.get_edgecolors()[0]
        assert ec[0] > 0.9  # red channel high

    def test_from_fisher_mean(self):
        """Works with output from pmag.fisher_mean (realistic usage)."""
        from pmagpy import pmag
        di_block = ipmag.fishrot(k=50, n=20, dec=350, inc=55,
                                 random_seed=42).tolist()
        fpars = pmag.fisher_mean(di_block)
        ipmag.plot_di_mean(dec=fpars['dec'], inc=fpars['inc'],
                           a95=fpars['alpha95'], color='blue')
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        assert len(new_collections) == 1
        new_lines = ax.lines[self.net_lines:]
        assert len(new_lines) == 1


# ---------------------------------------------------------------------------
# plot_di_mean_ellipse: mean direction with Kent/Bingham ellipse
# ---------------------------------------------------------------------------

class TestPlotDiMeanEllipse:
    """Tests for ipmag.plot_di_mean_ellipse and plot_di_mean_bingham."""

    def setup_method(self):
        self.fig = plt.figure()
        self.fig.add_subplot(111)
        ipmag.plot_net(self.fig.number)
        self.net_collections = len(self.fig.axes[0].collections)

    def teardown_method(self):
        plt.close(self.fig)

    def _make_kent_dict(self):
        """Generate a Kent parameter dict from Fisher-distributed data."""
        from pmagpy import pmag
        di_block = ipmag.fishrot(k=50, n=25, dec=30, inc=50,
                                 random_seed=99).tolist()
        kpars = pmag.dokent(di_block, len(di_block))
        return kpars

    def test_kent_ellipse(self):
        """plot_di_mean_ellipse runs without error with Kent parameters."""
        kpars = self._make_kent_dict()
        ipmag.plot_di_mean_ellipse(kpars, fignum=self.fig.number)
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        # at least one scatter for the mean point
        assert len(new_collections) >= 1

    def test_bingham_alias(self):
        """plot_di_mean_bingham delegates to plot_di_mean_ellipse."""
        kpars = self._make_kent_dict()
        ipmag.plot_di_mean_bingham(kpars, fignum=self.fig.number)
        ax = self.fig.axes[0]
        new_collections = ax.collections[self.net_collections:]
        assert len(new_collections) >= 1

    def test_upper_hemisphere_ellipse(self):
        """Negative inclination mean plots as open symbol."""
        kpars = self._make_kent_dict()
        # force negative inclination
        kpars['inc'] = -kpars['inc']
        ipmag.plot_di_mean_ellipse(kpars, fignum=self.fig.number)
        ax = self.fig.axes[0]
        coll = ax.collections[self.net_collections]
        fc = coll.get_facecolors()[0]
        assert np.allclose(fc[:3], [1.0, 1.0, 1.0])  # white = open symbol


# ---------------------------------------------------------------------------
# fishqq: Fisher QQ plot
# ---------------------------------------------------------------------------

class TestFishqq:
    """Tests for ipmag.fishqq."""

    def test_returns_summary(self):
        """fishqq returns a summary dict with expected keys."""
        directions = ipmag.fishrot(k=40, n=15, dec=200, inc=50,
                                    random_seed=33).tolist()
        summary = ipmag.fishqq(di_block=directions, plot=True, save=False)
        assert isinstance(summary, dict)
        assert summary.get('Mode') == 'Mode 1'
        assert summary.get('N', 0) > 10
        plt.close('all')


# ---------------------------------------------------------------------------
# igrf_print: IGRF output formatting
# ---------------------------------------------------------------------------

class TestIgrfPrint:
    """Tests for ipmag.igrf_print."""

    def test_formats_output(self):
        """igrf_print formats dec, inc, and intensity correctly."""
        buffer = StringIO()
        with redirect_stdout(buffer):
            ipmag.igrf_print([14.314, 61.483, 48992.647])
        output = buffer.getvalue().strip().splitlines()
        assert 'Declination: 14.314' in output[0]
        assert 'Inclination: 61.483' in output[1]
        assert 'Intensity: 48992.647 nT' in output[2]
