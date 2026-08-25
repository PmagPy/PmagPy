"""
Tests for matplotlib backend handling in pmagplotlib.

pmagplotlib.plot_init() raises a figure window when running outside a notebook
and outside the server. On a non-GUI backend that call used to raise
NonGuiException (issue #781), which broke plotting from plain scripts, from
pytest, and from notebook front ends whose shell class was not recognized.
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.backend_bases import FigureManagerBase

from pmag_env import set_env
from pmagpy import ipmag, pmagplotlib


class GuiManager(FigureManagerBase):
    """Stand-in for a GUI backend's manager, which overrides show()."""

    def __init__(self):
        self.shown = False

    def show(self):
        self.shown = True


class TestPlotInit:
    """Tests for pmagplotlib.plot_init backend handling."""

    @pytest.mark.parametrize("backend", ["Agg", "pdf", "svg"])
    def test_no_exception_on_non_gui_backends(self, backend):
        """plot_init does not raise on backends with no window (issue #781)."""
        assert not set_env.IS_NOTEBOOK, "test assumes a non-notebook shell"
        assert not pmagplotlib.isServer, "test assumes non-server mode"
        original = matplotlib.get_backend()
        try:
            matplotlib.use(backend, force=True)
            fig = pmagplotlib.plot_init(1, 5, 5)
            assert fig is not None
        finally:
            plt.close("all")
            matplotlib.use(original, force=True)

    def test_version_stamp_still_applied(self):
        """The version stamp is written even when no window can be shown."""
        fig = pmagplotlib.plot_init(1, 5, 5)
        texts = [t.get_text() for t in fig.texts]
        assert any("pmagpy" in t for t in texts), texts
        plt.close(fig)

    def test_show_called_when_backend_is_interactive(self, monkeypatch):
        """A GUI backend still gets its window raised -- no over-correction."""
        manager = GuiManager()
        monkeypatch.setattr(plt, "get_current_fig_manager", lambda: manager)
        fig = pmagplotlib.plot_init(1, 5, 5)
        assert manager.shown is True
        plt.close(fig)


class TestHistplotRegression:
    """The exact call reported in issue #781."""

    def test_histplot_runs_on_non_gui_backend(self):
        """ipmag.histplot no longer raises NonGuiException on Agg."""
        norm = np.random.default_rng(23).normal(size=100)
        ipmag.histplot(data=norm, xlab='Gaussian Deviates',
                       save_plots=False, norm=-1)
        plt.close('all')
