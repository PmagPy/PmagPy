"""pmag.doaniscorr: anisotropy correction of a paleointensity direction and intensity (data model 3)."""
import numpy as np
import pandas as pd
import pytest

from pmagpy import pmag

# diagonal tensor, normalized by its trace as in MagIC: x is the easy axis
# (1.2 times the mean), z the hard axis (0.8 times the mean)
EASY_X = '{}:{}:{}:0:0:0'.format(1.2 / 3, 1.0 / 3, 0.8 / 3)
ISOTROPIC = '{0}:{0}:{0}:0:0:0'.format(1 / 3)


def test_isotropic_tensor_leaves_the_result_unchanged():
    spec = {'dir_dec': 30., 'dir_inc': 40., 'int_abs': 5.0e-5, 'method_codes': 'LP-PI-TRM'}
    # the F test cannot be significant for an isotropic tensor
    aniso = {'aniso_s': ISOTROPIC, 'aniso_type': 'ATRM', 'aniso_s_sigma': 0.01, 'aniso_s_n_measurements': 6}
    out = pmag.doaniscorr(spec, aniso)
    assert (out['dir_dec'], out['dir_inc'], out['int_abs']) == (30., 40., 5.0e-5)
    assert (out['int_corr'], out['int_corr_aniso']) == ('c', 1.)
    assert out['method_codes'] == 'LP-PI-TRM:DA-AC-NN'
    assert spec['method_codes'] == 'LP-PI-TRM'  # the input is not modified


def test_principal_axis_direction_is_kept_and_the_intensity_scaled():
    # the tensor on the specimen's own row, with a sigma small enough to pass the F test
    row = pd.Series({'dir_dec': 0., 'dir_inc': 0., 'int_abs': 1.0e-5, 'method_codes': 'LP-PI-TRM',
                     'aniso_s': EASY_X, 'aniso_type': 'ATRM', 'aniso_s_sigma': 0.001,
                     'aniso_s_n_measurements': 6})
    out = pmag.doaniscorr(row)
    # the NRM lies along a principal axis, so its direction does not change
    assert (out['dir_dec'], out['dir_inc']) == pytest.approx((0., 0.))
    # the lab TRM was acquired along -z (hard axis), the ancient field along x
    # (easy axis): the specimen recorded the ancient field 1.2/0.8 times more
    # efficiently than the lab field, so the intensity comes down by 0.8/1.2
    assert out['int_corr_aniso'] == pytest.approx(0.8 / 1.2)
    assert out['int_abs'] == pytest.approx(1.0e-5 * 0.8 / 1.2)
    assert out['method_codes'] == 'LP-PI-TRM:DA-AC-ATRM'
    # a lab field along the easy axis instead needs no intensity change
    assert pmag.doaniscorr(row, lab_field_dec=0., lab_field_inc=0.)['int_corr_aniso'] == pytest.approx(1.)


def test_off_axis_direction_is_rotated_towards_the_hard_axis():
    # with the easy axis along x, a remanence between x and -z was deflected
    # towards x, so the corrected (ancient field) direction is steeper
    spec = {'dir_dec': 0., 'dir_inc': -45., 'int_abs': 1.0e-5}
    out = pmag.doaniscorr(spec, {'aniso_s': EASY_X, 'aniso_type': 'AARM'})  # no sigma: corrected regardless
    chi_inv = np.diag([1 / 1.2, 1 / 1.0, 1 / 0.8])  # the normalization cancels
    expected = pmag.cart2dir(chi_inv.dot(pmag.dir2cart([0., -45., 1.])))
    assert out['dir_dec'] == pytest.approx(expected[0] % 360, abs=1e-4)  # check_F holds s as float32
    assert out['dir_inc'] == pytest.approx(expected[1], abs=1e-4)
    assert out['dir_inc'] < -45.
    assert out['method_codes'] == 'DA-AC-AARM'
