"""
Tests for ipmag functions that combine or split MagIC table files:
combine_magic, and download_magic with separate_locs=True.
"""
import os
import shutil

import pandas as pd
import pytest

from pmagpy import contribution_builder as cb
from pmagpy import ipmag

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        os.pardir, os.pardir, 'data_files')
MCMURDO = os.path.join(DATA_DIR, '3_0', 'McMurdo')


def read_table(path):
    """Read a MagIC tab-delimited table into a DataFrame."""
    return pd.read_csv(path, sep='\t', header=1)


@pytest.fixture
def mcmurdo_dir(tmp_path):
    """Copies of the McMurdo tables used to combine."""
    for fname in ['specimens.txt', 'extra_specimens.txt', 'locations.txt',
                  'new_locations.txt']:
        shutil.copy(os.path.join(MCMURDO, fname), tmp_path)
    return tmp_path


class TestCombineMagic:

    def test_duplicate_rows_dropped(self, mcmurdo_dir):
        """rows found in more than one file are written once"""
        outfile = ipmag.combine_magic(['specimens.txt', 'extra_specimens.txt'], 'combined.txt',
                                      magic_table='specimens', dir_path=str(mcmurdo_dir),
                                      input_dir_path=str(mcmurdo_dir))
        assert outfile == os.path.join(str(mcmurdo_dir), 'combined.txt')
        first = read_table(mcmurdo_dir / 'specimens.txt')
        second = read_table(mcmurdo_dir / 'extra_specimens.txt')
        combined = read_table(outfile)
        assert len(combined) < len(first) + len(second)
        assert not combined.duplicated().any()
        assert set(combined['specimen']) == set(first['specimen']) | set(second['specimen'])

    def test_rows_of_each_file_kept(self, mcmurdo_dir):
        """two location tables with different rows give all of the rows"""
        outfile = ipmag.combine_magic(['locations.txt', 'new_locations.txt'], 'combined.txt',
                                      magic_table='locations', dir_path=str(mcmurdo_dir),
                                      input_dir_path=str(mcmurdo_dir))
        assert len(read_table(outfile)) == (len(read_table(mcmurdo_dir / 'locations.txt'))
                                            + len(read_table(mcmurdo_dir / 'new_locations.txt')))

    def test_measurement_sequence_renumbered(self, tmp_path):
        """the sequence column of the combined measurements runs 1..n"""
        shutil.copy(os.path.join(DATA_DIR, 'zeq_magic', 'measurements.txt'), tmp_path)
        meas = cb.MagicDataFrame(str(tmp_path / 'measurements.txt'))
        n_meas = len(meas.df)
        meas.df['specimen'] = meas.df['specimen'] + '_new'
        meas.write_magic_file('new_measurements.txt', dir_path=str(tmp_path))
        outfile = ipmag.combine_magic(['measurements.txt', 'new_measurements.txt'],
                                      'combined.txt', dir_path=str(tmp_path),
                                      input_dir_path=str(tmp_path))
        combined = read_table(outfile)
        assert len(combined) == 2 * n_meas
        assert combined['sequence'].tolist() == list(range(1, 2 * n_meas + 1))

    def test_no_valid_files(self, tmp_path):
        assert ipmag.combine_magic(['missing.txt'], 'combined.txt',
                                   dir_path=str(tmp_path)) is False
        assert not os.path.exists(tmp_path / 'combined.txt')

    def test_data_model_2_file_rejected(self, tmp_path):
        """a MagIC 2.5 table is not combined into a data model 3 file"""
        with open(tmp_path / 'er_samples.txt', 'w') as f:
            f.write('tab\ter_samples\ner_sample_name\ter_site_name\na1\ta\n')
        assert ipmag.combine_magic(['er_samples.txt'], 'combined.txt',
                                   dir_path=str(tmp_path)) is False


def write_two_location_contribution(path):
    """
    Write a small downloaded-contribution file with two locations.

    Each location has two sites, each with one sample, one specimen and two
    measurements.
    """
    tables = {
        'locations': ['location\tlat_n\tlat_s\tlon_e\tlon_w',
                      'Tel Hazor\t33.0\t33.0\t35.6\t35.6',
                      'Tel Megiddo\t32.6\t32.6\t35.2\t35.2'],
        'sites': ['site\tlocation\tlat\tlon'],
        'samples': ['sample\tsite'],
        'specimens': ['specimen\tsample'],
        'measurements': ['measurement\texperiment\tspecimen\tsequence\tmagn_moment'],
    }
    sequence = 0
    for loc, prefix in [('Tel Hazor', 'hz'), ('Tel Megiddo', 'mg')]:
        for n in (1, 2):
            site = '{}{:02d}'.format(prefix, n)
            tables['sites'].append('{}\t{}\t33\t35'.format(site, loc))
            tables['samples'].append('{}a\t{}'.format(site, site))
            tables['specimens'].append('{}a1\t{}a'.format(site, site))
            for step in (1, 2):
                sequence += 1
                tables['measurements'].append('{0}a1-{1}\t{0}a1-LP-DIR-AF\t{0}a1\t{2}\t1e-8'.format(
                    site, step, sequence))
    blocks = ['tab\t{}\n'.format(name) + '\n'.join(lines) for name, lines in tables.items()]
    with open(path, 'w') as f:
        f.write('\n>>>>>>>>>>\n'.join(blocks) + '\n')


def test_download_magic_separate_locations(tmp_path):
    """separate_locs puts each location's rows in its own Location_n directory"""
    write_two_location_contribution(tmp_path / 'magic_contribution.txt')
    assert ipmag.download_magic('magic_contribution.txt', dir_path=str(tmp_path),
                                input_dir_path=str(tmp_path), separate_locs=True)
    found = {}
    for loc_dir in sorted(tmp_path.glob('Location_*')):
        locs = read_table(loc_dir / 'locations.txt')['location'].unique()
        assert len(locs) == 1
        sites = read_table(loc_dir / 'sites.txt')
        assert (sites['location'] == locs[0]).all()
        specimens = read_table(loc_dir / 'specimens.txt')['specimen'].tolist()
        meas = read_table(loc_dir / 'measurements.txt')
        assert set(meas['specimen']) == set(specimens)
        found[locs[0]] = sorted(sites['site'])
    assert found == {'Tel Hazor': ['hz01', 'hz02'], 'Tel Megiddo': ['mg01', 'mg02']}
