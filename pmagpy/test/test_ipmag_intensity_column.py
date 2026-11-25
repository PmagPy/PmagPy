"""
Tests for the choice of the magnetization column for each specimen in
ipmag.zeq_magic and ipmag.thellier_magic (contribution_builder.get_intensity_col
with require_complete=True).

A MagIC contribution can combine specimens whose files give a moment (2G binary
files: magn_moment and magn_volume) with specimens whose files give only a
moment per volume (Remasoft .rs3 and ThellierTool .TDT files in A/m, with no
volume: magn_volume). The table used here is made by the PmagPy converters from
three files of the La Garrotxa archive (Vernet Tarragó, 2026, Zenodo
10.5281/zenodo.20326424, CC BY 4.0), already in data_files: GTX080201A.dat (2G),
OL01-2B.rs3 and GTX0206B1.TDT.
"""
import contextlib
import io
import os
import shutil

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert
from pmagpy import ipmag

DATA = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'data_files', 'convert_2_magic')


@pytest.fixture(autouse=True)
def close_figures():
    yield
    plt.close('all')


def _read(path):
    return pd.read_csv(path, sep='\t', skiprows=1, dtype=str)


def _write(df, path, table):
    with open(path, 'w') as f:
        f.write('tab\t{}\n'.format(table))
        df.to_csv(f, sep='\t', index=False)


@pytest.fixture
def mixed_table(tmp_path):
    """One MagIC folder holding a 2G specimen (magn_moment and magn_volume), a .rs3 specimen and a
    Thellier-Coe .TDT specimen (magn_volume only), with the orientations of the first two samples."""
    for name in ('rs3', 'tdt', 'out_2g', 'out_rs3', 'out_tdt', 'magic'):
        (tmp_path / name).mkdir()
    shutil.copy(os.path.join(DATA, 'rs3_magic', 'garrotxa', 'OL01-2B.rs3'), tmp_path / 'rs3')
    shutil.copy(os.path.join(DATA, 'tdt_magic', 'garrotxa', 'GTX0206B1.TDT'), tmp_path / 'tdt')
    with contextlib.redirect_stdout(io.StringIO()):
        assert convert._2g_bin(dir_path=str(tmp_path / 'out_2g'), specname=True,
                               mag_file=os.path.join(DATA, '2g_bin_magic', 'Vernet2026', 'GTX080201A.dat'))[0]
        assert convert.rs3(input_dir_path=str(tmp_path / 'rs3'), dir_path=str(tmp_path / 'out_rs3'),
                           specname=True, m_rows='T')[0]
        assert convert.tdt(str(tmp_path / 'tdt'), output_dir_path=str(tmp_path / 'out_tdt'), spec_name_con=2,
                           moment_units='A/m', lab_dec=0, lab_inc=-90)[0]
    for table in ('measurements', 'specimens', 'samples', 'sites', 'locations'):
        frames = [_read(tmp_path / out / '{}.txt'.format(table)) for out in ('out_2g', 'out_rs3', 'out_tdt')]
        df = pd.concat(frames, ignore_index=True)
        if table != 'measurements':
            df = df.drop_duplicates(subset=[table[:-1]])
        _write(df, tmp_path / 'magic' / '{}.txt'.format(table), table)
    return tmp_path / 'magic'


def _magnetization_columns(folder):
    meas = _read(folder / 'measurements.txt')
    return {spec: [col for col in ('magn_moment', 'magn_volume') if g[col].notna().any()]
            for spec, g in meas.groupby('specimen')}


def test_mixed_table(mixed_table):
    """the table has the magnetization columns these tests are about"""
    assert _magnetization_columns(mixed_table) == {'GTX080201A': ['magn_moment', 'magn_volume'],
                                                   'OL01-2B': ['magn_volume'],
                                                   'GTX0206B1': ['magn_volume']}


def test_get_intensity_col_require_complete():
    data = pd.DataFrame({'magn_moment': [1e-5, np.nan, np.nan], 'magn_volume': [1.0, 2.0, 3.0]})
    # the first column with any value, as before
    assert cb.get_intensity_col(data) == 'magn_moment'
    # the first column with a value in every row
    assert cb.get_intensity_col(data, require_complete=True) == 'magn_volume'
    # blank strings are not values
    data = pd.DataFrame({'magn_moment': ['1e-5', ' '], 'magn_mass': ['1', '2']})
    assert cb.get_intensity_col(data, require_complete=True) == 'magn_mass'
    # no column is complete: the first column with any value
    data = pd.DataFrame({'magn_moment': [np.nan, 1e-5], 'magn_volume': [1.0, np.nan]})
    assert cb.get_intensity_col(data, require_complete=True) == 'magn_moment'
    assert cb.get_intensity_col(data[[]], require_complete=True) == ''


@pytest.mark.parametrize('crd', ['s', 'g'])
def test_zeq_magic_specimen_with_magn_volume_only(mixed_table, crd):
    """the .rs3 specimen is drawn although other specimens of the table have magn_moment; in
    geographic coordinates zeq_magic stopped with an IndexError, all its rows having been left out"""
    os.chdir(mixed_table)
    ok, files = ipmag.zeq_magic(spec_file='specimens.txt', specimen='OL01-2B', crd=crd, save_plots=True,
                                fmt='png', n_plots=1)
    assert ok
    assert 'OL01-2B_zijd.png' in files


def test_zeq_magic_specimen_with_magn_moment(mixed_table):
    """the 2G specimen is drawn as before"""
    os.chdir(mixed_table)
    ok, files = ipmag.zeq_magic(spec_file='specimens.txt', specimen='GTX080201A', crd='g', save_plots=True,
                                fmt='png', n_plots=1)
    assert ok
    assert 'GTX080201A_zijd.png' in files


def test_zeq_magic_table_with_magn_volume_only(mixed_table):
    """a table without magn_moment can be drawn"""
    meas = _read(mixed_table / 'measurements.txt')
    _write(meas[meas.specimen == 'OL01-2B'].drop(columns='magn_moment'), mixed_table / 'measurements.txt',
           'measurements')
    os.chdir(mixed_table)
    ok, files = ipmag.zeq_magic(spec_file='specimens.txt', specimen='OL01-2B', save_plots=True, fmt='png',
                                n_plots=1)
    assert ok
    assert 'OL01-2B_zijd.png' in files


def test_zeq_magic_warns_without_orientation(mixed_table, capsys):
    """geographic coordinates for a sample without orientation: drawn in specimen coordinates, with a
    warning (there was none)"""
    samples = _read(mixed_table / 'samples.txt')
    samples.loc[samples['sample'] == 'OL01-2B', ['azimuth', 'dip']] = np.nan
    _write(samples, mixed_table / 'samples.txt', 'samples')
    os.chdir(mixed_table)
    ok, files = ipmag.zeq_magic(spec_file='specimens.txt', specimen='OL01-2B', crd='g', save_plots=True,
                                fmt='png', n_plots=1)
    assert ok
    assert 'No orientation for sample OL01-2B: plotted in specimen coordinates' in capsys.readouterr().out


def test_thellier_magic_specimen_with_magn_volume_only(mixed_table):
    """the Thellier-Coe specimen is found and drawn although another specimen of the table has
    magn_moment ("could not find specimen" before)"""
    ok, files = ipmag.thellier_magic(input_dir_path=str(mixed_table), dir_path=str(mixed_table),
                                     spec='GTX0206B1', fmt='png')
    assert ok
    assert any(f.endswith('GTX0206B1_arai.png') for f in np.ravel(files))


def test_thellier_magic_lists_thellier_specimens(mixed_table):
    """the specimens drawn are those of Thellier-type experiments, not every specimen with a moment"""
    ok, files = ipmag.thellier_magic(input_dir_path=str(mixed_table), dir_path=str(mixed_table), n_specs=1,
                                     fmt='png')
    assert ok
    assert any(os.path.basename(f).startswith('GTX0206B1_') for f in np.ravel(files))
