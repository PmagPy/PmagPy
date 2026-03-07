"""
Tests for plotting and output formatting functions in ipmag.py.

Covers plot_net / plot_di (stereographic projection plotting),
fishqq (Fisher QQ plot), and igrf_print (IGRF output formatting).
These are smoke tests verifying that functions execute without error
and produce expected output.
"""
from contextlib import redirect_stdout
from io import StringIO

import matplotlib.pyplot as plt

from pmagpy import ipmag


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
