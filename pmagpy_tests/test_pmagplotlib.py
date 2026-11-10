import os
import sys
import unittest
import cartopy
import numpy as np
from pmagpy import pmag
from pmagpy import pmagplotlib
from pmag_env import set_env
WD = pmag.get_test_WD()
import matplotlib


class TestPlotMagMap(unittest.TestCase):

    def setUp(self):
        print('sys.platform', sys.platform)
        print('matplotlib backend', matplotlib.get_backend())
        print('matplotlib version', matplotlib.__version__)

    def tearDown(self):
        pass

    @unittest.skipIf(set_env.IS_LINUX and 'discover' in sys.argv, 'test fails on Linux env, works on Linux otherwise')
    def test_success(self):
        date, mod, lon_0, alt, ghfile = 1956.0725, 'cals10k.2', 0, 0, ""  # only date is required
        Ds, Is, Bs, Brs, lons, lats = pmag.do_mag_map(
            date, mod=mod, lon_0=lon_0, alt=alt, file=ghfile)
        res_0 = pmagplotlib.plot_mag_map(
            1, Bs, lons, lats, 'B', date=date, contours=True, lon_0=10, proj="Mollweide")  # plot the field strength
        res_1 = pmagplotlib.plot_mag_map(
            2, Is, lons, lats, 'I', date=date, contours=True)  # plot the inclination
        res_2 = pmagplotlib.plot_mag_map(
            3, Ds, lons, lats, 'D', date=date, contours=True)
        if cartopy.__version__ != "0.16.0":
            for res in [res_0, res_1, res_2]:
                self.assertIsInstance(res, cartopy.mpl.geoaxes.GeoAxesSubplot)
        else:
            for res in [res_1, res_2]:
                self.assertIsInstance(res, cartopy.mpl.geoaxes.GeoAxesSubplot)
        print('completed plot_magmap test')


class TestPlotZijOptions(unittest.TestCase):
    """plot_zij: the default diagram, and the optional axis, frame, labels, colors and fits"""

    def setUp(self):
        from matplotlib import pyplot as plt
        self.plt = plt
        # [step, dec, inc, moment, quality]
        self.datablock = [[273., 10., 45., 4e-5, 'g'], [373., 12., 44., 3e-5, 'g'],
                          [473., 15., 42., 2e-5, 'g'], [573., 14., 43., 1e-5, 'g']]

    def tearDown(self):
        self.plt.close('all')

    def test_default_draws_on_numbered_figure(self):
        pmagplotlib.plot_zij(7, self.datablock, 0, 'spc01')
        fig = self.plt.figure(num=7)
        self.assertEqual(len(fig.axes), 1)
        self.assertEqual(fig.axes[0].get_title(), 'spc01: NRM =  4.00e-05')
        self.assertEqual(len(fig.axes[0].lines), 6)  # 4 plot calls and the 2 axis lines

    def test_axis_of_multipanel_figure(self):
        fig, (ax_left, ax_right) = self.plt.subplots(1, 2)
        ax_left.plot([0, 1], [0, 1])
        n_figures = len(self.plt.get_fignums())
        pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax_right)
        # the diagram is on the axis passed; no figure is made or cleared
        self.assertEqual(len(self.plt.get_fignums()), n_figures)
        self.assertEqual(len(fig.axes), 2)
        self.assertEqual(len(ax_left.lines), 1)
        self.assertEqual(len(ax_right.lines), 6)
        self.assertEqual(ax_right.get_title(), 'spc01: NRM =  4.00e-05')
        self.assertEqual(ax_right.get_ylabel(), 'Circles: Y; Squares: Z')
        self.assertEqual(len(ax_right.texts), 4)  # the step numbers
        # Y and Z increase downward
        self.assertGreater(ax_right.get_ylim()[0], ax_right.get_ylim()[1])

    def test_default_artists(self):
        # the diagram made without any of the options
        fig, ax = self.plt.subplots()
        pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax)
        self.assertTrue(ax.axison)
        self.assertEqual(ax.get_xlabel(), 'X: rotated to Dec =     0.0')
        self.assertEqual([text.get_text() for text in ax.texts], ['0', '1', '2', '3'])
        # the only collections are those of the steps flagged bad (none here)
        self.assertTrue(all(len(c.get_offsets()) == 0 for c in ax.collections))
        self.assertEqual(len(ax.patches), 0)
        colors = [(line.get_marker(), line.get_linestyle(), line.get_color())
                  for line in ax.lines[:4]]
        self.assertEqual(colors, [('o', 'None', 'r'), ('s', 'None', 'w'),
                                  ('None', '-', 'r'), ('None', '-', 'b')])
        self.assertEqual(ax.lines[1].get_markeredgecolor(), 'blue')

    def test_frame_and_axis_labels(self):
        fig, ax = self.plt.subplots()
        pmagplotlib.plot_zij(None, self.datablock, 90, 'spc01', ax=ax, frame=False,
                             axis_labels={'right': 'E', 'top': 'N, Up'}, step_labels=False)
        self.assertFalse(ax.axison)
        self.assertEqual([text.get_text() for text in ax.texts], ['E', 'N, Up'])
        with self.assertRaises(ValueError):
            pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax,
                                 axis_labels={'east': 'E'})

    def test_step_labels(self):
        fig, ax = self.plt.subplots()
        pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax,
                             step_labels=['NRM', '', '', '300 C'])
        self.assertEqual([text.get_text() for text in ax.texts], ['NRM', '300 C'])
        with self.assertRaises(ValueError):
            pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax,
                                 step_labels=['NRM', '300 C'])

    def test_step_and_line_colors(self):
        from matplotlib.colors import to_rgba
        fig, ax = self.plt.subplots()
        step_colors = ['0.5', 'C0', 'C0', 'C0']
        pmagplotlib.plot_zij(None, self.datablock, 0, 'spc01', ax=ax,
                             step_colors=step_colors, line_color='0.8')
        horizontal, vertical = ax.collections[-2:]
        for k, color in enumerate(step_colors):
            self.assertEqual(tuple(horizontal.get_facecolors()[k]), to_rgba(color))
            self.assertEqual(tuple(vertical.get_edgecolors()[k]), to_rgba(color))
        self.assertEqual(tuple(vertical.get_facecolors()[0]), to_rgba('w'))
        self.assertEqual([line.get_color() for line in ax.lines[:2]], ['0.8', '0.8'])

    def test_fits(self):
        from matplotlib.patches import FancyArrowPatch
        # steps on a line toward the origin, declination 30 and inclination 40
        datablock = [[step, 30., 40., moment, 'g'] for step, moment in
                     zip([0., 10., 20., 30., 40.], [5e-5, 4e-5, 3e-5, 2e-5, 1e-5])]
        fit = pmag.domean(datablock, 1, 3, 'DE-BFL')
        fit.update(color='C1', label='component')
        plane = dict(fit, calculation_type='DE-BFP')
        fig, ax = self.plt.subplots()
        pmagplotlib.plot_zij(None, datablock, 0, 'spc01', ax=ax, fits=[fit, plane])
        arrows = [patch for patch in ax.patches if isinstance(patch, FancyArrowPatch)]
        self.assertEqual(len(arrows), 2)  # X,Y and X,Z projections of the line; no plane
        self.assertEqual(ax.get_legend_handles_labels()[1], ['component'])
        # without fits there are no arrows
        fig, ax = self.plt.subplots()
        pmagplotlib.plot_zij(None, datablock, 0, 'spc01', ax=ax)
        self.assertEqual(len(ax.patches), 0)
        # a step of the fit that is not among the good steps
        with self.assertRaises(ValueError):
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
        self.assertEqual(pmagplotlib._zij_fit_ends(treatments, XYZ, plane, 0), (None, None))
        # bounds that are not among the treatments
        for key in ('measurement_step_min', 'measurement_step_max'):
            with self.assertRaises(ValueError):
                pmagplotlib._zij_fit_ends(treatments, XYZ, dict(fit, **{key: 35.}), 0)

    def test_fit_ends_anchored_and_free(self):
        # steps that are offset from the origin: a free line passes through
        # their center of mass and an anchored line through the origin
        treatments = [0., 10., 20., 30.]
        XYZ = pmag.dir2cart([[dec, 40., moment] for dec, moment in
                             zip([30., 32., 35., 40.], [4., 3., 2., 1.])])
        fit = dict(specimen_dec=30., specimen_inc=40., measurement_step_min=0.,
                   measurement_step_max=30.)
        direction = pmag.dir2cart([30., 40., 1.])

        def distance_from_line(point, through):
            offset = np.asarray(through) - point
            return np.linalg.norm(offset - (offset @ direction) * direction)

        for calculation_type, through in (('DE-BFL', XYZ.mean(axis=0)),
                                          ('DE-BFL-A', np.zeros(3)),
                                          ('DE-FM', np.zeros(3)),
                                          ('DE-BFL-O', np.vstack([XYZ, np.zeros(3)]).mean(axis=0))):
            tail, tip = pmagplotlib._zij_fit_ends(
                treatments, XYZ, dict(fit, calculation_type=calculation_type), 0)
            self.assertAlmostEqual(distance_from_line(tail, through), 0.)
            self.assertAlmostEqual(distance_from_line(tip, through), 0.)
            # the arrow points along the direction of the fit
            np.testing.assert_allclose((tip - tail) / np.linalg.norm(tip - tail), direction)
