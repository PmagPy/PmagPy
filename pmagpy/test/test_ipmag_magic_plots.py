"""
Tests for the ipmag *_magic plotting functions behind the command-line
programs, which read MagIC tables and save figures: chi_magic, thellier_magic,
zeq_magic, eqarea_magic, quick_hyst, polemap_magic and vgpmap_magic.

The science these functions plot is tested where it is computed (pmag, ipmag.zeq,
rockmag, ...), so the coverage here is: one check that a function plots the
values it reads (chi_magic), one smoke test per function that it saves its
files and describes them in images-table records, and records of known defects.

Each test copies its input tables into a temporary directory and runs there,
because reading a measurements table without a 'measurement' column makes
contribution_builder add one and rewrite the file in place.
"""
import os
import shutil

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir, 'data_files')
MCMURDO_TABLES = ['measurements.txt', 'specimens.txt', 'samples.txt', 'sites.txt',
                  'locations.txt']


@pytest.fixture(autouse=True)
def close_figures():
    """Close the figures each test leaves open."""
    yield
    plt.close('all')


@pytest.fixture
def work_dir(tmp_path, monkeypatch):
    """
    Return a function that copies example data into tmp_path and runs there.

    The returned function takes a directory under data_files and, optionally,
    the names of the files to copy (default: all files), and returns tmp_path
    as a str after changing into it.
    """
    monkeypatch.chdir(tmp_path)

    def copy(subdir, files=None):
        src = os.path.join(DATA_DIR, subdir)
        for fname in (os.listdir(src) if files is None else files):
            path = os.path.join(src, fname)
            if os.path.isfile(path):
                shutil.copy(path, tmp_path)
        return str(tmp_path)
    return copy


def read_table(path):
    """Read a MagIC tab-delimited table into a DataFrame."""
    return pd.read_csv(path, sep='\t', header=1)


def saved_images(directory):
    """Sorted names of the image files in directory."""
    return sorted(f for f in os.listdir(directory)
                  if os.path.splitext(f)[1] in ('.png', '.svg', '.pdf'))


def test_chi_magic_plots_chi_against_temperature(work_dir):
    """one curve per frequency, of chi (in micro SI) at the highest field"""
    experiment = 'IRM-OldBlue-1892'
    d = work_dir('chi_magic', ['measurements.txt'])
    ok, saved = ipmag.chi_magic(os.path.join(d, 'measurements.txt'),
                                experiments=experiment, save_plots=False)
    assert ok and saved == []
    meas = read_table(os.path.join(d, 'measurements.txt'))
    meas = meas[(meas['experiment'] == experiment)
                & (meas['meas_field_ac'] == meas['meas_field_ac'].max())]
    lines = plt.figure(1).axes[0].lines
    frequencies = sorted(meas['meas_freq'].unique())
    assert len(lines) == len(frequencies)
    for line, freq in zip(lines, frequencies):
        this_freq = meas[meas['meas_freq'] == freq]
        np.testing.assert_allclose(line.get_xdata(), this_freq['meas_temp'])
        np.testing.assert_allclose(line.get_ydata(), 1e6 * this_freq['susc_chi_volume'])


@pytest.mark.xfail(strict=True, raises=IndexError, reason=(
    "make_plots in zeq_magic builds the zero-field mask on all of the specimen's "
    "steps and applies it to the thermal subset ('spec_df_th[-cond]'); with "
    "duplicate measurement names, as McMurdo mc15a has, pandas raises "
    "IndexError, which the except ValueError does not catch"))
def test_zeq_magic_specimen_with_duplicate_measurement_names(work_dir):
    """a Thellier specimen with pTRM checks and repeated measurement names plots"""
    d = work_dir('3_0/McMurdo', MCMURDO_TABLES)
    ok, saved = ipmag.zeq_magic(input_dir_path=d, dir_path=d, spec_file='specimens.txt',
                                specimen='mc15a', fmt='png')
    assert ok
    assert sorted(os.path.basename(f) for f in saved) == [
        'mc15a_demag.png', 'mc15a_eqarea.png', 'mc15a_zijd.png']


def test_vgpmap_magic_saves_a_map(work_dir):
    pytest.importorskip('cartopy')
    d = work_dir('3_0/McMurdo', ['sites.txt', 'locations.txt'])
    ok, saved = ipmag.vgpmap_magic(d, fmt='png')
    assert ok
    assert list(saved) == saved_images(d) == ['McMurdo_VGP_map.png']


@pytest.mark.xfail(strict=True, reason=(
    "vgpmap_magic returns files.values, the method, instead of "
    "files.values(), when image_records=True"))
def test_vgpmap_magic_with_image_records(work_dir):
    pytest.importorskip('cartopy')
    d = work_dir('3_0/McMurdo', ['sites.txt', 'locations.txt'])
    ok, saved, image_recs = ipmag.vgpmap_magic(d, fmt='png', image_records=True)
    assert list(saved) == ['McMurdo_VGP_map.png']


def run_with_image_records(name, d):
    """Run one plotting function on its example data with image_records=True."""
    if name == 'thellier_magic':
        return ipmag.thellier_magic(input_dir_path=d, spec='s2s0-03', fmt='png',
                                    image_records=True)
    if name == 'zeq_magic':
        return ipmag.zeq_magic(input_dir_path=d, dir_path=d, fmt='png', n_plots=1,
                               image_records=True)
    if name == 'quick_hyst':
        return ipmag.quick_hyst(d, 'hysteresis_magic_example3.dat', n_plots=2,
                                image_records=True)
    if name == 'eqarea_magic':
        return ipmag.eqarea_magic(dir_path=d, save_plots=True, fmt='png', plot_by='loc',
                                  image_records=True)
    if name == 'polemap_magic':
        return ipmag.polemap_magic(dir_path=d, fmt='png', image_records=True)
    raise ValueError(name)


@pytest.mark.parametrize('name, subdir, files, n_images', [
    ('thellier_magic', 'thellier_magic', ['measurements.txt'], 4),
    ('zeq_magic', 'zeq_magic', ['measurements.txt'], 3),
    ('quick_hyst', 'quick_hyst', ['hysteresis_magic_example3.dat'], 2),
    ('eqarea_magic', 'eqarea_magic', ['sites.txt'], 1),
    ('polemap_magic', '3_0/McMurdo', ['locations.txt'], 1),
    pytest.param('polemap_magic', 'polemap_magic', ['locations.txt'], 1,
                 id='polemap_magic-several-locations',
                 marks=pytest.mark.xfail(strict=True, reason=(
                     "the image record keeps the ':' between location names, "
                     "which save_plots replaces with '_' in the file name"))),
])
def test_saves_plots_and_image_records(work_dir, name, subdir, files, n_images):
    """each wrapper saves its plots and an images-table record naming each file"""
    if name == 'polemap_magic':
        pytest.importorskip('cartopy')
    d = work_dir(subdir, files)
    ok, _, image_recs = run_with_image_records(name, d)
    assert ok
    assert len(image_recs) == n_images
    assert sorted(os.path.basename(rec['file']) for rec in image_recs) == saved_images(d)
    for rec in image_recs:
        assert rec['type'] and rec['software_packages'].startswith('pmagpy')
