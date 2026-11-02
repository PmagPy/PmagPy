"""Coordinate fallback in aniso_magic, with independent tensor rotations."""
import numpy as np
import pandas as pd
import pytest
from scipy.spatial.transform import Rotation

from pmagpy import contribution_builder as cb
from pmagpy import ipmag


def matrix(values):
    a, b, c, d, e, f = values
    return np.array([[a, d, f], [d, b, e], [f, e, c]])


def contribution(tmp_path):
    con = cb.Contribution(str(tmp_path), read_tables=[])
    con.add_magic_table_from_data('specimens', [
        dict(specimen='a', sample='s', aniso_s='.5:.3:.2:.01:.02:.03',
             aniso_tilt_correction=-1, aniso_s_n_measurements=15, aniso_s_sigma=.001),
        dict(specimen='b', sample='s', aniso_s='.4:.35:.25:-.02:.01:.04',
             aniso_tilt_correction=-1, aniso_s_n_measurements=15, aniso_s_sigma=.001)])
    con.add_magic_table_from_data('samples', [
        dict(sample='s', site='site', azimuth=37., dip=-23.,
             bed_dip_direction=121., bed_dip=32.)])
    con.add_magic_table_from_data('sites', [dict(site='site', location='loc')])
    return con


@pytest.mark.parametrize('frame,correction', [('g', 0), ('t', 100)])
def test_aniso_rotates_requested_frame(tmp_path, monkeypatch, frame, correction):
    con = contribution(tmp_path)
    original = con.tables['specimens'].df.copy(deep=True)
    seen = []
    monkeypatch.setattr(ipmag, 'plot_aniso', lambda number, data, **kw: seen.append(data.copy()) or {})
    assert ipmag.aniso_magic(contribution=con, crd=frame, save_plots=False)[0]
    assert set(seen[0]['aniso_tilt_correction']) == {correction}
    # Geographic basis: rotate about Y by -dip, then Z by azimuth.
    rotation = Rotation.from_euler('z', 37., degrees=True).as_matrix() @ Rotation.from_euler('y', 23., degrees=True).as_matrix()
    if frame == 't':
        strike = np.deg2rad(121. - 90.)
        axis = np.array([np.cos(strike), np.sin(strike), 0.])
        rotation = Rotation.from_rotvec(-np.deg2rad(32.) * axis).as_matrix() @ rotation
    for before, after in zip(original['aniso_s'], seen[0]['aniso_s']):
        s = matrix([float(x) for x in before.split(':')])
        result = matrix([float(x) for x in after.split(':')])
        np.testing.assert_allclose(result, rotation @ s @ rotation.T, atol=7e-8)
    pd.testing.assert_series_equal(con.tables['specimens'].df['aniso_s'], original['aniso_s'])
    pd.testing.assert_series_equal(con.tables['specimens'].df['aniso_tilt_correction'], original['aniso_tilt_correction'])


@pytest.mark.parametrize('problem', ['missing', 'nan', 'nullable', 'conflicting'])
def test_aniso_retains_fallback_without_complete_orientation(tmp_path, monkeypatch, problem):
    con = contribution(tmp_path)
    samples = con.tables['samples'].df
    if problem == 'missing':
        con.tables['samples'].df = samples.drop(columns=['dip'])
    elif problem == 'nan':
        samples.loc['s', 'dip'] = np.nan
    elif problem == 'nullable':
        for name in ['azimuth', 'dip']:
            samples[name] = samples[name].astype('string')
        samples.loc['s', 'dip'] = pd.NA
    else:
        other = samples.copy()
        other['dip'] = 40.
        con.tables['samples'].df = pd.concat([samples, other])
    seen = []
    monkeypatch.setattr(ipmag, 'plot_aniso', lambda number, data, **kw: seen.append(data.copy()) or {})
    assert ipmag.aniso_magic(contribution=con, crd='g', save_plots=False, verbose=False)[0]
    assert set(seen[0]['aniso_tilt_correction']) == {-1}
