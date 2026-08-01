"""
Tests for convert.cit, the CIT-format converter.

Coverage:
- Basic conversion of a .sam file into the five MagIC 3.0 tables
- Record counts and MagIC 3.0 headers in each output file
- The oersted flag's effect on AF demag step scaling (Gauss vs milliTesla)
- Actionable error reporting on invalid inputs
"""
import os

import pytest

from pmagpy import convert_2_magic as convert
from pmagpy import contribution_builder as cb


# USGS Boring volcanic field test data: 9 specimens, 7 AF demag steps each.
USGS_BL9_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, os.pardir,
    'data_files', 'convert_2_magic', 'cit_magic', 'USGS', 'bl9-1'
)

_BL9_BASE_OPTIONS = {
    'input_dir_path': USGS_BL9_DIR,
    'magfile': 'bl9-1.sam',
    'sitename': 'BL9001',
    'methods': ['FS-FD', 'SO-SM', 'LT-AF-Z'],
    'noave': True,
}


@pytest.fixture
def tmp_cwd(tmp_path, monkeypatch):
    """Run with CWD inside a per-test tmp_path so converter outputs land there."""
    monkeypatch.chdir(tmp_path)
    yield tmp_path


def _run_bl9(**overrides):
    options = {**_BL9_BASE_OPTIONS, **overrides}
    return convert.cit(**options)


class TestCitBasicConversion:
    """convert.cit produces all five MagIC 3.0 tables with the expected structure."""

    def test_returns_success_tuple(self, tmp_cwd):
        program_ran, outfile = _run_bl9()
        assert program_ran is True
        assert outfile == 'measurements.txt'

    def test_creates_all_magic_tables(self, tmp_cwd):
        _run_bl9()
        for fname in ('specimens.txt', 'samples.txt', 'sites.txt',
                      'locations.txt', 'measurements.txt'):
            assert os.path.isfile(fname), f'{fname} was not created'

    def test_files_have_magic_3_header(self, tmp_cwd):
        _run_bl9()
        for fname, table_type in [('specimens.txt', 'specimens'),
                                  ('samples.txt', 'samples'),
                                  ('sites.txt', 'sites'),
                                  ('locations.txt', 'locations'),
                                  ('measurements.txt', 'measurements')]:
            with open(fname) as f:
                header = f.readline().rstrip('\n').rstrip()
            assert header.startswith('tab\t'), f'{fname} missing MagIC tab marker'
            assert header.endswith(table_type), f'{fname} header mismatch: {header!r}'

    def test_record_counts(self, tmp_cwd):
        """9 specimens × 7 AF demag steps = 63 measurements; 1 site, 1 location."""
        _run_bl9()
        assert len(cb.MagicDataFrame('specimens.txt').df) == 9
        assert len(cb.MagicDataFrame('samples.txt').df) == 9
        assert len(cb.MagicDataFrame('sites.txt').df) == 1
        assert len(cb.MagicDataFrame('locations.txt').df) == 1
        assert len(cb.MagicDataFrame('measurements.txt').df) == 63

    def test_sitename_arg_is_honored(self, tmp_cwd):
        _run_bl9()
        site_df = cb.MagicDataFrame('sites.txt').df
        assert site_df['site'].tolist() == ['BL9001']

    def test_locname_default_is_unknown(self, tmp_cwd):
        _run_bl9()
        loc_df = cb.MagicDataFrame('locations.txt').df
        assert loc_df['location'].tolist() == ['unknown']

    def test_locname_arg_is_honored(self, tmp_cwd):
        _run_bl9(locname='Boring volcanic field')
        loc_df = cb.MagicDataFrame('locations.txt').df
        assert loc_df['location'].tolist() == ['Boring volcanic field']

    def test_measurements_link_to_known_specimens(self, tmp_cwd):
        """Every measurement's specimen ID appears in the specimens table."""
        _run_bl9()
        meas_specs = set(cb.MagicDataFrame('measurements.txt').df['specimen'].unique())
        known_specs = set(cb.MagicDataFrame('specimens.txt').df['specimen'].unique())
        assert meas_specs <= known_specs


class TestCitOerstedScaling:
    """The oersted flag controls whether AF demag steps are read as Gauss or milliTesla."""

    def test_default_is_gauss_interpretation(self, tmp_cwd):
        """Default oersted=True: .sam AF steps in Gauss (Tesla = G * 1e-4)."""
        _run_bl9()
        meas_df = cb.MagicDataFrame('measurements.txt')
        af_steps_T = sorted(meas_df.df['treat_ac_field'].astype(float).unique())
        # bl9-1.sam records AF demag at 0, 100, 200, 300, 450, 600, 800 G
        expected_T = [0.0, 0.01, 0.02, 0.03, 0.045, 0.06, 0.08]
        assert len(af_steps_T) == len(expected_T)
        for got, exp in zip(af_steps_T, expected_T):
            assert got == pytest.approx(exp, abs=1e-6)

    def test_oersted_false_is_millitesla_interpretation(self, tmp_cwd):
        """oersted=False: .sam AF steps in milliTesla (Tesla = mT * 1e-3)."""
        _run_bl9(oersted=False)
        meas_df = cb.MagicDataFrame('measurements.txt')
        af_steps_T = sorted(meas_df.df['treat_ac_field'].astype(float).unique())
        # Same raw .sam values reinterpreted as mT → 10x the Gauss interpretation
        expected_T = [0.0, 0.1, 0.2, 0.3, 0.45, 0.6, 0.8]
        assert len(af_steps_T) == len(expected_T)
        for got, exp in zip(af_steps_T, expected_T):
            assert got == pytest.approx(exp, abs=1e-6)


class TestCitFailureModes:
    """convert.cit reports actionable failures for invalid inputs rather than raising."""

    def test_no_magfile_returns_error(self, tmp_cwd):
        program_ran, message = convert.cit()
        assert program_ran is False
        assert 'sam file' in message.lower()

    def test_invalid_samp_con_returns_error(self, tmp_cwd):
        # Naming convention [4] requires a -Z suffix (e.g. "4-3")
        program_ran, message = _run_bl9(samp_con='4')
        assert program_ran is False
        assert '4-Z' in message
