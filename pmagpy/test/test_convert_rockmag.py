"""
Tests of the convert_2_magic converters of rock magnetic experiments: agm
(MicroMag hysteresis loops and backfield curves) and mst (Curie temperature
experiments, magnetization against temperature).

Expected values are read off the input files in data_files/convert_2_magic.
"""
import os

import pytest

from pmagpy import convert_2_magic as convert
from pmagpy.test.convert_helpers import CONVERT_DIR, convert_into, read_table

AGM_DIR = os.path.join(CONVERT_DIR, 'agm_magic')


def data_lines(path):
    """
    The numbers in a text file, skipping header and footer lines.

    Args:
        path (str): the file

    Returns:
        list: one list of floats per line of numbers
    """
    with open(path) as f:
        lines = f.read().splitlines()
    return [[float(value) for value in line.replace(',', ' ').split()] for line in lines
            if line.strip() and not line.startswith('"')]


@pytest.fixture(scope='module')
def run(tmp_path_factory):
    """runs a converter into a new temporary directory and returns the output directory"""
    def _run(name, call):
        result, out_dir, cwd = convert_into(tmp_path_factory.mktemp(name), call)
        assert result[0] is True, result
        return result[1], out_dir
    return _run


class TestAgm:
    """
    MicroMag files in the old format: a header line, then pairs of field in Oe
    and moment, both taken to be in cgs units (units='cgs', the default).
    """

    def test_hysteresis_loop(self, run):
        meas_file, out = run('agm', lambda out: convert.agm(
            'agm_magic_example.agm', input_dir_path=AGM_DIR, dir_path=out, fmt='old',
            specimen='IS01a-1'))
        # the output files are named after the specimen
        assert os.path.basename(meas_file) == 'IS01a-1.magic'
        assert {'IS01a-1_specimens.txt', 'samples.txt', 'sites.txt'} <= set(os.listdir(out))
        meas = read_table(os.path.join(out, 'IS01a-1.magic'))
        raw = data_lines(os.path.join(AGM_DIR, 'agm_magic_example.agm'))
        assert len(meas) == len(raw)
        assert set(meas['method_codes']) == {'LP-HYS'}
        assert set(meas['specimen']) == {'IS01a-1'}
        # +1.201200E+04,+4.575500E+04: Oe to T, emu to Am^2
        assert list(meas['meas_field_dc']) == pytest.approx([field * 1e-4 for field, _ in raw], rel=1e-3)
        assert list(meas['magn_moment']) == pytest.approx([moment * 1e-3 for _, moment in raw], rel=1e-3)

    def test_backfield(self, run):
        meas_file, out = run('agm_irm', lambda out: convert.agm(
            'agm_magic_example.irm', input_dir_path=AGM_DIR, dir_path=out, fmt='old', bak=True,
            specimen='IS01a-1', instrument='SIO-FLO'))
        meas = read_table(os.path.join(out, 'IS01a-1.magic'))
        raw = data_lines(os.path.join(AGM_DIR, 'agm_magic_example.irm'))
        assert len(meas) == len(raw)
        assert set(meas['method_codes']) == {'LP-IRM-DCD'}
        assert set(meas['instrument_codes']) == {'SIO-FLO'}
        # each backfield is applied and removed: the remanence is measured in zero field
        assert list(meas['treat_dc_field']) == pytest.approx([row[0] * 1e-4 for row in raw], rel=1e-3)
        assert set(meas['meas_field_dc']) == {0}
        assert list(meas['magn_moment']) == pytest.approx([row[1] * 1e-3 for row in raw], rel=1e-3)


class TestMst:
    """
    Curie temperature files (curie_example.dat): temperature in C and the
    uncalibrated magnetization, measured in the lab field; the example has the
    warming curve only, from 138.2 to 697.2 C.
    """

    def test_measurements(self, run):
        meas_file, out = run('mst', lambda out: convert.mst(
            'curie_example.dat', spec_name='abcde', location='place',
            input_dir_path=os.path.join(CONVERT_DIR, 'mst_magic'), dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        raw = data_lines(os.path.join(CONVERT_DIR, 'mst_magic', 'curie_example.dat'))
        assert len(meas) == len(raw)
        assert set(meas['specimen']) == {'abcde'}
        # the sample, site and location are in their own tables
        specimens = read_table(os.path.join(out, 'specimens.txt')).set_index('specimen')
        sample = specimens.loc['abcde', 'sample']
        site = read_table(os.path.join(out, 'samples.txt')).set_index('sample').loc[sample, 'site']
        assert read_table(os.path.join(out, 'sites.txt')).set_index('site').loc[site, 'location'] == 'place'
        assert list(meas['meas_temp']) == pytest.approx([temp + 273 for temp, _ in raw], abs=0.1)
        assert list(meas['magn_uncal']) == pytest.approx([mag for _, mag in raw], rel=1e-3)
        assert list(meas['treat_dc_field']) == pytest.approx([0.5] * len(raw))
        # after the first measurement, warming (LP-MW-I) or cooling (LP-MC-I) in field
        expected = ['LP-NO']
        for previous, current in zip(raw, raw[1:]):
            if current[0] > previous[0]:
                expected.append('LP-MW-I')
            elif current[0] < previous[0]:
                expected.append('LP-MC-I')
            else:
                expected.append(None)
        codes = [code if isinstance(code, str) else None for code in meas['method_codes']]
        assert codes == expected

    def test_measurements_file_name(self, run):
        """a measurements file with another name is the one the other tables are made from"""
        meas_file, out = run('mst_name', lambda out: convert.mst(
            'curie_example.dat', spec_name='abcde', meas_file='curie.txt',
            input_dir_path=os.path.join(CONVERT_DIR, 'mst_magic'), dir_path=out))
        assert meas_file == os.path.join(out, 'curie.txt')
        assert sorted(os.listdir(out)) == ['curie.txt', 'locations.txt', 'samples.txt',
                                           'sites.txt', 'specimens.txt']
        assert 'sample' not in read_table(meas_file).columns
        assert list(read_table(os.path.join(out, 'specimens.txt'))['specimen']) == ['abcde']
