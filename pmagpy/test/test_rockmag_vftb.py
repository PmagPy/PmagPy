"""
pmagpy.rockmag on variable field translation balance (VFTB) curves converted
with convert_2_magic.vftb: a back-field curve that starts at zero field
and a hysteresis loop that begins with the initial magnetization curve,
both of which stopped the functions, and the warning for a loop measured at
too few fields. The files are in
data_files/convert_2_magic/vftb_magic/garrotxa (see the README there).
"""
import contextlib
import io
import os
import shutil
import tempfile
import unittest

import numpy as np

from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert
from pmagpy import rockmag

WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
INPUT_DIR = os.path.join(WD, 'data_files', 'convert_2_magic', 'vftb_magic', 'garrotxa')


def converted(name):
    """The measurements of one VFTB file, converted with convert_2_magic.vftb."""
    out = tempfile.mkdtemp()
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            ok, outfile = convert.vftb(name, dir_path=out, input_dir_path=INPUT_DIR, meas_outfile='m.txt',
                                       spec_outfile='s.txt', samp_outfile='sa.txt', site_outfile='si.txt',
                                       loc_outfile='l.txt', specimen='GTX0208B', location='La Garrotxa')
        assert ok, outfile
        return cb.MagicDataFrame(os.path.join(out, 'm.txt')).df.reset_index(drop=True)
    finally:
        shutil.rmtree(out)


class TestVftbRockmag(unittest.TestCase):

    def test_backfield_curve_from_zero_field(self):
        """Bcr of a curve whose first step is at zero field, without drop_first: the zero crossing"""
        df = converted('GTX0208B.coe')
        curve = df[['treat_dc_field', 'magn_mass']].astype(float)
        self.assertEqual(curve['treat_dc_field'].iloc[0], 0)
        # spline smoothing, so that the test does not need the optional statsmodels (LOWESS); Bcr is
        # the zero crossing of the curve whatever the smoothing
        experiment, bcr = rockmag.process_backfield_data(curve.copy(), smooth_mode='spline')
        # the zero crossing of the measured curve, by linear interpolation
        field, moment = -curve['treat_dc_field'].values, curve['magn_mass'].values
        k = int(np.flatnonzero(np.diff(np.sign(moment)) != 0)[0])
        crossing = field[k] - moment[k] * (field[k + 1] - field[k]) / (moment[k + 1] - moment[k])
        self.assertAlmostEqual(bcr, crossing, places=6)
        self.assertAlmostEqual(bcr * 1e3, 23.60, places=2)
        self.assertEqual(len(experiment), len(curve) - 1)
        # the same as dropping the first step by hand
        self.assertEqual(bcr, rockmag.process_backfield_data(curve.copy(), smooth_mode='spline',
                                                             drop_first=True)[1])

    def test_hysteresis_loop_with_initial_curve(self):
        """the initial curve before the loop is left out, and the loop is processed"""
        df = converted('GTX0208B.hys')
        field, magnetization = df['meas_field_dc'].astype(float).values, df['magn_mass'].astype(float).values
        loop_field, loop_magnetization, dropped = rockmag.drop_hyst_initial_curve(field, magnetization)
        # the initial curve: from -8.37 mT up to the peak field, the first of three sweeps
        self.assertAlmostEqual(field[0], -8.37e-3, places=6)
        self.assertEqual(loop_field[0], field.max())
        self.assertTrue(np.all(np.diff(field[:dropped + 1]) > 0))
        with contextlib.redirect_stdout(io.StringIO()):
            result = rockmag.process_hyst_loop(field, magnetization, 'GTX0208B', show_results_table=False,
                                               show_plot=False, n_bootstrap=0)
            expected = rockmag.process_hyst_loop(loop_field, loop_magnetization, 'GTX0208B',
                                                 show_results_table=False, show_plot=False, n_bootstrap=0)
        for key in ('Ms', 'Mr', 'Bc'):
            self.assertTrue(np.isfinite(result[key]))
            self.assertEqual(result[key], expected[key])
        # a loop without an initial curve is not changed
        same_field, same_magnetization, none = rockmag.drop_hyst_initial_curve(loop_field, loop_magnetization)
        self.assertEqual(none, 0)
        self.assertTrue(np.array_equal(same_field, loop_field))


    def test_sparse_loop_warning(self):
        """a VFTB loop (about 20 points a branch) is gridded too coarsely, and process_hyst_loop warns"""
        import warnings
        df = converted('GTX0208B.hys')
        field, magnetization = df['meas_field_dc'].astype(float).values, df['magn_mass'].astype(float).values
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            rockmag.process_hyst_loop(field, magnetization, 'GTX0208B', show_results_table=False,
                                      show_plot=False, n_bootstrap=0)
        messages = [str(w.message) for w in caught if 'points between zero and the peak field' in str(w.message)]
        self.assertEqual(len(messages), 1)
        self.assertIn('GTX0208B', messages[0])
        self.assertIn('unreliable', messages[0])

    def test_dense_loop_no_warning(self):
        """a loop measured densely (McMurdo example, about 250 points a branch) gives no such warning"""
        import warnings
        import pandas as pd
        meas = pd.read_csv(os.path.join(WD, 'data_files', '3_0', 'McMurdo', 'measurements.txt'), sep='\t',
                           header=1, low_memory=False)
        loops = meas[meas['method_codes'].fillna('').str.contains('LP-HYS')]
        experiment, loop = next(iter(loops.groupby('experiment')))
        field, moment = loop['meas_field_dc'].astype(float).values, loop['magn_moment'].astype(float).values
        grid, _ = rockmag.grid_hyst_loop(*rockmag.sanitize_hyst_inputs(field, moment))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            n_points = rockmag.warn_sparse_hyst_grid(grid, experiment)
        self.assertGreaterEqual(n_points, 70)
        self.assertFalse([w for w in caught if 'points between zero and the peak field' in str(w.message)])


if __name__ == '__main__':
    unittest.main()
