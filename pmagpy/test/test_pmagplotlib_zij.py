"""
Tests for pmagplotlib.plot_zij: the axis limits, and the optional arguments
(an existing axis, frame, labels, colors and fits).

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


# ---------------------------------------------------------------------------
# Optional arguments: an existing axis, frame, labels, colors and fits
# ---------------------------------------------------------------------------

# [step, dec, inc, moment, quality]
STEPS = [[273., 10., 45., 4e-5, 'g'], [373., 12., 44., 3e-5, 'g'],
         [473., 15., 42., 2e-5, 'g'], [573., 14., 43., 1e-5, 'g']]


class TestPlotZijOptions:
    """The default diagram, and the optional axis, frame, labels, colors and fits."""

    def teardown_method(self):
        plt.close("all")

    def test_default_draws_on_numbered_figure(self):
        pmagplotlib.plot_zij(7, STEPS, 0, 'spc01')
        fig = plt.figure(num=7)
        assert len(fig.axes) == 1
        assert fig.axes[0].get_title() == 'spc01: NRM =  4.00e-05'
        assert len(fig.axes[0].lines) == 6  # 4 plot calls and the 2 axis lines

    def test_default_artists(self):
        """The diagram made without any of the options."""
        fig, ax = plt.subplots()
        pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax)
        assert ax.axison
        assert ax.get_xlabel() == 'X: rotated to Dec =     0.0'
        assert ax.get_ylabel() == 'Circles: Y; Squares: Z'
        assert [text.get_text() for text in ax.texts] == ['0', '1', '2', '3']
        # the only collections are those of the steps flagged bad (none here)
        assert all(len(c.get_offsets()) == 0 for c in ax.collections)
        assert len(ax.patches) == 0
        styles = [(line.get_marker(), line.get_linestyle(), line.get_color())
                  for line in ax.lines[:4]]
        assert styles == [('o', 'None', 'r'), ('s', 'None', 'w'),
                          ('None', '-', 'r'), ('None', '-', 'b')]
        assert ax.lines[1].get_markeredgecolor() == 'blue'
        # Y and Z increase downward
        assert ax.get_ylim()[0] > ax.get_ylim()[1]

    def test_axis_of_multipanel_figure(self):
        fig, (ax_left, ax_right) = plt.subplots(1, 2)
        ax_left.plot([0, 1], [0, 1])
        n_figures = len(plt.get_fignums())
        pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax_right)
        # the diagram is on the axis passed; no figure is made or cleared
        assert len(plt.get_fignums()) == n_figures
        assert len(fig.axes) == 2
        assert len(ax_left.lines) == 1
        assert len(ax_right.lines) == 6
        assert ax_right.get_title() == 'spc01: NRM =  4.00e-05'

    def test_frame_and_axis_labels(self):
        fig, ax = plt.subplots()
        pmagplotlib.plot_zij(None, STEPS, 90, 'spc01', ax=ax, frame=False,
                             axis_labels={'right': 'E', 'top': 'N, Up'}, step_labels=False)
        assert not ax.axison
        assert [text.get_text() for text in ax.texts] == ['E', 'N, Up']
        with pytest.raises(ValueError):
            pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax, axis_labels={'east': 'E'})

    def test_step_labels(self):
        fig, ax = plt.subplots()
        pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax,
                             step_labels=['NRM', '', '', '300 C'])
        assert [text.get_text() for text in ax.texts] == ['NRM', '300 C']
        with pytest.raises(ValueError):
            pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax, step_labels=['NRM', '300 C'])

    def test_step_and_line_colors(self):
        from matplotlib.colors import to_rgba
        fig, ax = plt.subplots()
        step_colors = ['0.5', 'C0', 'C0', 'C0']
        pmagplotlib.plot_zij(None, STEPS, 0, 'spc01', ax=ax,
                             step_colors=step_colors, line_color='0.8')
        horizontal, vertical = ax.collections[-2:]
        for k, color in enumerate(step_colors):
            assert tuple(horizontal.get_facecolors()[k]) == to_rgba(color)
            assert tuple(vertical.get_edgecolors()[k]) == to_rgba(color)
        assert tuple(vertical.get_facecolors()[0]) == to_rgba('w')
        assert [line.get_color() for line in ax.lines[:2]] == ['0.8', '0.8']

    def test_fits(self):
        from matplotlib.patches import FancyArrowPatch
        # steps on a line toward the origin, declination 30 and inclination 40
        datablock = [[step, 30., 40., moment, 'g'] for step, moment in
                     zip([0., 10., 20., 30., 40.], [5e-5, 4e-5, 3e-5, 2e-5, 1e-5])]
        fit = pmag.domean(datablock, 1, 3, 'DE-BFL')
        fit.update(color='C1', label='component')
        plane = dict(fit, calculation_type='DE-BFP')
        fig, ax = plt.subplots()
        pmagplotlib.plot_zij(None, datablock, 0, 'spc01', ax=ax, fits=[fit, plane])
        arrows = [patch for patch in ax.patches if isinstance(patch, FancyArrowPatch)]
        assert len(arrows) == 2  # X,Y and X,Z projections of the line; no plane
        assert ax.get_legend_handles_labels()[1] == ['component']
        # a step of the fit that is not among the good steps
        with pytest.raises(ValueError):
            pmagplotlib.plot_zij(None, datablock, 0, 'spc01', ax=ax,
                                 fits=[dict(fit, measurement_step_max=35.)])

    def test_fit_ends(self):
        # steps on a line toward the origin, declination 30 and inclination 40
        treatments = [0., 10., 20., 30., 40.]
        XYZ = pmag.dir2cart([[30., 40., moment] for moment in [5., 4., 3., 2., 1.]])
        fit = dict(specimen_dec=30., specimen_inc=40., measurement_step_min=10.,
                   measurement_step_max=30.)
        # the arrow runs along the steps, from beyond the last step of the fit
        # (30) to beyond the first (10): 8% of the length of the fit past each
        tail, tip = pmagplotlib._zij_fit_ends(treatments, XYZ, fit, 0)
        extension = 0.08 * (XYZ[1] - XYZ[3])
        np.testing.assert_allclose(tail, XYZ[3] - extension)
        np.testing.assert_allclose(tip, XYZ[1] + extension)
        # the diagram rotated by 30 puts the line along X
        rotated = pmag.dir2cart([[0., 40., moment] for moment in [5., 4., 3., 2., 1.]])
        tail, tip = pmagplotlib._zij_fit_ends(treatments, rotated, fit, 30)
        np.testing.assert_allclose([tail[1], tip[1]], [0., 0.], atol=1e-12)
        # a plane has no line
        plane = dict(fit, calculation_type='DE-BFP')
        assert pmagplotlib._zij_fit_ends(treatments, XYZ, plane, 0) == (None, None)
        # bounds that are not among the treatments
        for key in ('measurement_step_min', 'measurement_step_max'):
            with pytest.raises(ValueError):
                pmagplotlib._zij_fit_ends(treatments, XYZ, dict(fit, **{key: 35.}), 0)

    @pytest.mark.parametrize("calculation_type, through_origin", [
        ('DE-BFL', False), ('DE-BFL-O', False), ('DE-BFL-A', True), ('DE-FM', True)])
    def test_fit_ends_anchored_and_free(self, calculation_type, through_origin):
        """A free line passes through the center of mass of its steps (with the
        origin, for a line with origin), an anchored line through the origin."""
        treatments = [0., 10., 20., 30.]
        XYZ = pmag.dir2cart([[dec, 40., moment] for dec, moment in
                             zip([30., 32., 35., 40.], [4., 3., 2., 1.])])
        fit = dict(specimen_dec=30., specimen_inc=40., measurement_step_min=0.,
                   measurement_step_max=30., calculation_type=calculation_type)
        direction = pmag.dir2cart([30., 40., 1.])
        if through_origin:
            through = np.zeros(3)
        elif calculation_type == 'DE-BFL-O':
            through = np.vstack([XYZ, np.zeros(3)]).mean(axis=0)
        else:
            through = XYZ.mean(axis=0)
        tail, tip = pmagplotlib._zij_fit_ends(treatments, XYZ, fit, 0)
        for end in (tail, tip):
            offset = through - end
            assert np.linalg.norm(offset - (offset @ direction) * direction) < 1e-9
        # the arrow points along the direction of the fit
        np.testing.assert_allclose((tip - tail) / np.linalg.norm(tip - tail), direction)

