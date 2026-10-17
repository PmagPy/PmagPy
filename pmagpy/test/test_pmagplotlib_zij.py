"""
Tests for the axis limits of pmagplotlib.plot_zij.

The frame of the Zijderveld plot used to be set exactly at the extremes of
the data. With all of the data on one side of the origin, the axis lines then
fell on the edges of the frame where they could not be seen, and the points at
the extremes (usually the NRM) were clipped by the frame (issue #922, found
while revisiting issue #554).
"""
import matplotlib.pyplot as plt
import numpy as np
import pytest

from pmagpy import pmag, pmagplotlib


def make_datablock(decs, incs, ints, qualities=None):
    """Build a [step, dec, inc, M, type, quality] datablock for plot_zij."""
    if qualities is None:
        qualities = ['g'] * len(decs)
    return [[float(step), dec, inc, intensity, '', quality]
            for step, (dec, inc, intensity, quality)
            in enumerate(zip(decs, incs, ints, qualities))]


def frame_limits():
    """Return (low, high) of the x and y axes of the current plot."""
    x_low, x_high = sorted(plt.gca().get_xlim())
    y_low, y_high = sorted(plt.gca().get_ylim())
    return x_low, x_high, y_low, y_high


# declination, inclination pairs that put X, Y and Z on a single side of the
# origin, and one set of directions that straddles it
ONE_SIDED = {
    "all negative (west and up)": ([255.9, 252.6, 251.1, 250.2],
                                   [-58.5, -57.5, -57.0, -60.5]),
    "all positive (northeast and down)": ([40., 42., 45., 50.],
                                          [50., 48., 45., 40.]),
    "X positive, Z negative": ([10., 12., 15., 20.],
                               [-35., -40., -45., -50.]),
}
INTENSITIES = [1.0, 0.8, 0.6, 0.4]


class TestPlotZijLimits:
    """Tests for the frame of the Zijderveld plot."""

    def teardown_method(self):
        plt.close("all")

    @pytest.mark.parametrize("case", sorted(ONE_SIDED))
    def test_points_are_inside_the_frame(self, case):
        """No point sits on the edge of the frame, where it would be clipped."""
        decs, incs = ONE_SIDED[case]
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, INTENSITIES), 0,
                             "spec", norm=True)
        xyz = pmag.dir2cart(np.column_stack([decs, incs, INTENSITIES]))
        x_low, x_high, y_low, y_high = frame_limits()
        assert x_low < xyz[:, 0].min() and xyz[:, 0].max() < x_high
        for component in (xyz[:, 1], xyz[:, 2]):
            assert y_low < component.min() and component.max() < y_high

    @pytest.mark.parametrize("case", sorted(ONE_SIDED))
    def test_origin_is_inside_the_frame(self, case):
        """The axis lines through the origin are not on an edge of the frame."""
        decs, incs = ONE_SIDED[case]
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, INTENSITIES), 0,
                             "spec", norm=True)
        x_low, x_high, y_low, y_high = frame_limits()
        assert x_low < 0 < x_high
        assert y_low < 0 < y_high

    @pytest.mark.parametrize("case", sorted(ONE_SIDED))
    def test_axis_lines_span_the_frame(self, case):
        """The lines through the origin run from edge to edge of the frame."""
        decs, incs = ONE_SIDED[case]
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, INTENSITIES), 0,
                             "spec", norm=True)
        axis = plt.gca()
        figure = axis.figure
        figure.canvas.draw()
        frame = axis.get_window_extent()
        horizontal, vertical = [], []
        for line in axis.lines:
            if line.get_color() != 'k':
                continue
            extent = line.get_window_extent(figure.canvas.get_renderer())
            if np.isclose(extent.height, 0, atol=2):
                horizontal.append(extent)
            if np.isclose(extent.width, 0, atol=2):
                vertical.append(extent)
        assert len(horizontal) == 1 and len(vertical) == 1
        assert np.isclose(horizontal[0].x0, frame.x0, atol=2)
        assert np.isclose(horizontal[0].x1, frame.x1, atol=2)
        assert np.isclose(vertical[0].y0, frame.y0, atol=2)
        assert np.isclose(vertical[0].y1, frame.y1, atol=2)

    def test_horizontal_component_larger_than_the_others(self):
        """A Y component larger than X and Z is still inside the frame."""
        decs, incs = [88., 89., 90., 91.], [5., 5., 5., 5.]
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, INTENSITIES), 0,
                             "spec", norm=True)
        xyz = pmag.dir2cart(np.column_stack([decs, incs, INTENSITIES]))
        x_low, x_high, y_low, y_high = frame_limits()
        assert xyz[:, 1].max() > max(xyz[:, 0].max(), xyz[:, 2].max())
        assert y_low < xyz[:, 1].min() and xyz[:, 1].max() < y_high

    def test_step_flagged_bad_is_inside_the_frame(self):
        """A bad step beyond the good data does not fall outside the frame."""
        decs, incs = ONE_SIDED["all positive (northeast and down)"]
        decs, incs = decs + [45.], incs + [45.]
        intensities = INTENSITIES + [3.0]
        qualities = ['g', 'g', 'g', 'g', 'b']
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, intensities,
                                               qualities), 0, "spec", norm=True)
        bad = pmag.dir2cart([45., 45., 3.0])
        x_low, x_high, y_low, y_high = frame_limits()
        assert x_low < bad[0] < x_high
        assert y_low < bad[1] < y_high
        assert y_low < bad[2] < y_high

    def test_axes_are_equal_and_down_is_down(self):
        """The plot keeps an equal aspect with positive (down) at the bottom."""
        decs, incs = ONE_SIDED["all positive (northeast and down)"]
        pmagplotlib.plot_zij(1, make_datablock(decs, incs, INTENSITIES), 0,
                             "spec", norm=True)
        axis = plt.gca()
        bottom, top = axis.get_ylim()
        assert bottom > top
        assert axis.get_aspect() in ("equal", 1.0)
