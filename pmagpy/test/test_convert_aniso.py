"""
Tests of the convert_2_magic converters of anisotropy of magnetic
susceptibility data: kly4s, k15, s_magic and sufar4 (the IODP LORE kly4s
converter is in test_convert_iodp.py).

Expected values are read off the input files in data_files/convert_2_magic.
Tests marked xfail(strict=True) record known defects: they start to pass, and so
fail the suite, once the defect is fixed, which is the reminder to remove the mark.
"""
import os

import numpy as np
import pytest

from pmagpy import convert_2_magic as convert
from pmagpy import pmag
from pmagpy.test.convert_helpers import CONVERT_DIR, convert_into, read_table


def in_dir(*parts):
    """the path of a directory in data_files/convert_2_magic"""
    return os.path.join(CONVERT_DIR, *parts)


def tensor(aniso_s):
    """the six elements of a colon-delimited aniso_s value"""
    return np.array([float(value) for value in aniso_s.split(':')])


def ams_rows(specimens, specimen):
    """the anisotropy records of a specimen, by aniso_tilt_correction"""
    rows = specimens[(specimens['specimen'] == specimen) & specimens['aniso_s'].notnull()]
    return rows.set_index('aniso_tilt_correction')


def ams_row(specimens, specimen, tilt_correction):
    """the first anisotropy record of a specimen in a coordinate system"""
    rows = ams_rows(specimens, specimen)
    return rows.loc[[tilt_correction]].iloc[0]


@pytest.fixture(scope='module')
def run(tmp_path_factory):
    """runs a converter into a new temporary directory and returns the output directory"""
    def _run(name, call):
        result, out_dir, cwd = convert_into(tmp_path_factory.mktemp(name), call)
        assert result[0] is True, result
        return out_dir
    return _run


class TestKly4s:
    """
    SIO KLY4S files. The first line of KLY4S_magic_example.dat is
    318-U1359B-011H-1-W-75: the normalized tensor 0.3415264 0.3403534 0.3181202
    -0.0006608 0.0000948 0.0023186, sigma 2.284E-4, bulk susceptibility
    1.26728E-4, in a field of 300 A/m.
    """

    SPECIMEN = '318-U1359B-011H-1-W-75'

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('kly4s', lambda out: convert.kly4s(
            'KLY4S_magic_example.dat', input_dir_path=in_dir('kly4s_magic'), dir_path=out))

    def test_bulk_susceptibility(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 26
        first = meas.iloc[0]
        assert first['specimen'] == self.SPECIMEN
        assert first['susc_chi_volume'] == pytest.approx(1.26728e-4)
        assert first['meas_field_ac'] == pytest.approx(300 * 4e-7 * np.pi, rel=1e-3)
        assert 'LP-X' in first['method_codes']

    def test_tensor(self, out):
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        assert specimens.loc[specimens['aniso_s'].notnull(), 'specimen'].nunique() == 26
        row = ams_row(specimens, self.SPECIMEN, -1)
        np.testing.assert_allclose(tensor(row['aniso_s']), [0.3415264, 0.3403534, 0.3181202,
                                                            -0.0006608, 0.0000948, 0.0023186])
        assert row['aniso_s_sigma'] == pytest.approx(2.284e-4)
        assert row['aniso_type'] == 'AMS'
        assert row['method_codes'] == 'LP-X:AE-H:LP-AN-MS'

    def test_samples_and_sites(self, out):
        """the sample, site and location of each specimen are in the samples and sites tables"""
        specimens = read_table(os.path.join(out, 'specimens.txt')).drop_duplicates('specimen')
        assert specimens.set_index('specimen').loc[self.SPECIMEN, 'sample'] == self.SPECIMEN
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        assert len(samples) == 26
        # naming convention 1: the site is the sample name without its last character
        assert samples.loc[self.SPECIMEN, 'site'] == self.SPECIMEN[:-1]
        sites = read_table(os.path.join(out, 'sites.txt'))
        assert sites['site'].is_unique
        assert set(sites['site']) == set(samples['site'])
        assert set(sites['location']) == {'unknown'}

    def test_azdip_orientation(self, tmp_path):
        """the orientation in an AZDIP file goes to the samples table in the output directory"""
        with open(os.path.join(in_dir('kly4s_magic'), 'KLY4S_magic_example.dat')) as f:
            lines = f.readlines()[:2]
        in_dir_path = tmp_path / 'in'
        in_dir_path.mkdir()
        with open(str(in_dir_path / 'kly4s.dat'), 'w') as f:
            f.writelines(lines)
        # name, azimuth and hade of the drill direction, bedding strike and dip
        with open(str(in_dir_path / 'azdip.txt'), 'w') as f:
            f.write('{} 40 30 100 20\n'.format(self.SPECIMEN))
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.kly4s(
            'kly4s.dat', azdip_infile='azdip.txt', input_dir_path=str(in_dir_path), dir_path=out))
        assert result[0] is True, result
        assert os.listdir(cwd) == []
        samples = read_table(os.path.join(out_dir, 'samples.txt')).set_index('sample')
        assert len(samples) == 2
        # orientation convention 3: dip = 90 - hade; the dip is to the right of the
        # strike (right-hand rule), so the dip direction is the strike + 90
        oriented = samples.loc[self.SPECIMEN]
        assert (oriented['azimuth'], oriented['dip']) == (40, 60)
        assert (oriented['bed_dip_direction'], oriented['bed_dip']) == (190, 20)
        assert samples.loc['318-U1359B-011H-2-W-76', ['azimuth', 'dip']].isnull().all()
        specimens = read_table(os.path.join(out_dir, 'specimens.txt'))
        assert set(ams_rows(specimens, self.SPECIMEN).index) == {-1, 0, 100}

    def write_input(self, in_dir_path):
        """the first two lines of the example, and a samples table orienting the first"""
        with open(os.path.join(in_dir('kly4s_magic'), 'KLY4S_magic_example.dat')) as f:
            lines = f.readlines()[:2]
        with open(os.path.join(in_dir_path, 'kly4s.dat'), 'w') as f:
            f.writelines(lines)
        with open(os.path.join(in_dir_path, 'samples.txt'), 'w') as f:
            f.write('tab\tsamples\n'
                    'sample\tsite\tazimuth\tdip\tbed_dip_direction\tbed_dip\tmethod_codes\n'
                    '{}\tsite1\t40\t60\t120\t20\tSO-MAG\n'.format(self.SPECIMEN))
        return [float(value) for value in lines[0].split()[1:7]]

    def test_samples_file_orientation(self, tmp_path):
        """the orientation in a samples table rotates the tensor to geographic and tilt corrected"""
        in_dir_path = str(tmp_path / 'in')
        os.makedirs(in_dir_path)
        s = self.write_input(in_dir_path)
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.kly4s(
            'kly4s.dat', samp_infile='samples.txt', input_dir_path=in_dir_path, dir_path=out))
        assert result[0] is True, result
        specimens = read_table(os.path.join(out_dir, 'specimens.txt'))
        rows = ams_rows(specimens, self.SPECIMEN)
        geographic = pmag.dosgeo(s, 40, 60)
        np.testing.assert_allclose(tensor(rows.loc[0, 'aniso_s']), geographic, atol=1e-6)
        np.testing.assert_allclose(tensor(rows.loc[100, 'aniso_s']),
                                   pmag.dostilt(geographic, 120, 20), atol=1e-6)
        assert 'SO-MAG' in rows.loc[0, 'method_codes'].split(':')
        samples = read_table(os.path.join(out_dir, 'samples.txt')).set_index('sample')
        assert (samples.loc[self.SPECIMEN, 'azimuth'], samples.loc[self.SPECIMEN, 'dip']) == (40, 60)

    def test_samples_file_is_not_overwritten(self, tmp_path):
        """a samples table read in from the output directory is left as it is"""
        out_dir = str(tmp_path / 'work')
        os.makedirs(out_dir)
        self.write_input(out_dir)
        with open(os.path.join(out_dir, 'samples.txt')) as f:
            before = f.read()
        result, _, cwd = convert_into(tmp_path, lambda out: convert.kly4s(
            'kly4s.dat', samp_infile='samples.txt', dir_path=out_dir))
        assert result[0] is True, result
        with open(os.path.join(out_dir, 'samples.txt')) as f:
            assert f.read() == before


class TestK15:
    """
    15-position susceptibility files (k15_example.dat). tr245f: azimuth 80 and
    dip -46, bedding strike 204 and dip 25, then 15 susceptibilities in 10^-6 SI.
    """

    TR245F = [995, 999, 993, 995, 1000, 1004, 999, 1001, 1004, 999, 998, 997, 1002, 998, 997]

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('k15', lambda out: convert.k15('k15_example.dat', input_dir_path=in_dir('k15_magic'),
                                                  dir_path=out))

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 8 * 15
        tr245f = meas[meas['specimen'] == 'tr245f']
        np.testing.assert_allclose(tr245f['susc_chi_volume'], np.array(self.TR245F) * 1e-6)

    def test_orientation(self, out):
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        tr245f = samples.loc['tr245f']
        assert (tr245f['azimuth'], tr245f['dip']) == (80, -46)
        # the dip direction is 90 degrees clockwise from the strike
        assert (tr245f['bed_dip_direction'], tr245f['bed_dip']) == (294, 25)

    def test_tensor(self, out):
        """the specimen tensor is normalized by its trace and rotated with the orientation"""
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        in_specimen = ams_row(specimens, 'tr245f', -1)
        s_specimen = tensor(in_specimen['aniso_s'])
        assert s_specimen[:3].sum() == pytest.approx(1)
        assert in_specimen['aniso_s_mean'] == pytest.approx(np.mean(self.TR245F) * 1e-6)
        s_geographic = tensor(ams_row(specimens, 'tr245f', 0)['aniso_s'])
        np.testing.assert_allclose(s_geographic, pmag.dosgeo(s_specimen, 80, -46), atol=1e-8)

    @pytest.mark.xfail(strict=True, reason='the data model 3 branch for the tilt corrected record '
                                           'never sets aniso_s or the tilt correction, so the '
                                           'specimen coordinate tensor is written twice and the '
                                           'tilt corrected one is missing')
    def test_one_tensor_per_coordinate_system(self, out):
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        rows = ams_rows(specimens, 'tr245f')
        assert sorted(rows.index) == [-1, 0, 100]

    # not strict: whether the eigenvalues come out complex depends on the NumPy version
    @pytest.mark.xfail(strict=False, reason="the eigenvalues in aniso_v1-3 are written as complex "
                                            "numbers, e.g. '(0.33521363+0j)', with some NumPy versions")
    def test_eigenvectors(self, out):
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        for value in specimens['aniso_v1'].dropna():
            [float(part) for part in value.split(':')]

    @pytest.mark.xfail(strict=True, reason='the experiment name is made from the last line of '
                                           "susceptibilities, e.g. '998.:LP-AN-MS'")
    def test_experiment_name(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert set(meas.loc[meas['specimen'] == 'tr245f', 'experiment']) == {'tr245f:LP-AN-MS'}


class TestSMagic:
    """
    Files of six tensor elements per line (s_magic_example.dat), without
    specimen names; the first line is 0.33455709 0.33192658 0.33351630
    -0.00043562 0.00092779 0.00105006.
    """

    def test_tensors_and_names(self, run):
        out = run('s_magic', lambda out: convert.s_magic(
            's_magic_example.dat', input_dir_path=in_dir('s_magic'), dir_path=out,
            spec='abcd-efg', specnum=1, samp_con='2', location='place'))
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        assert len(specimens) == 8
        np.testing.assert_allclose(tensor(specimens['aniso_s'].iloc[0]),
                                   [0.33455709, 0.33192658, 0.33351630,
                                    -0.00043562, 0.00092779, 0.00105006])
        assert set(specimens['aniso_type']) == {'AMS'}
        assert set(specimens['specimen']) == {'abcd-efg'}
        samples = read_table(os.path.join(out, 'samples.txt'))
        # one character off the specimen name, then the site name up to the '-'
        assert set(zip(samples['sample'], samples['site'])) == {('abcd-ef', 'abcd')}
        sites = read_table(os.path.join(out, 'sites.txt'))
        assert list(sites['location']) == ['place']

    def test_coordinates_and_method_codes(self, run):
        """the coordinate system, unit and method codes are written also without sigma"""
        out = run('s_magic_coord', lambda out: convert.s_magic(
            's_magic_example.dat', input_dir_path=in_dir('s_magic'), dir_path=out,
            coord_type='g'))
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        assert set(specimens['aniso_tilt_correction']) == {0}
        assert set(specimens['method_codes']) == {'LP-X:AE-H:LP-AN-MS'}
        assert set(specimens['aniso_s_unit']) == {'Normalized by trace'}

    def test_naming_convention_6(self, tmp_path):
        """convention 6 is not supported, which gives (False, message)"""
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.s_magic(
            's_magic_example.dat', input_dir_path=in_dir('s_magic'), dir_path=out, samp_con='6'))
        assert result[0] is False
        assert '6' in result[1]
        assert os.listdir(out_dir) == []


class TestSufar4:
    """
    AGICO SUFAR 4 ascii files. The first block of sufar4-asc_magic_example.txt
    is 318-U1356A-1R-1-W-83: mean susceptibility 56.74E-06 from 15 positions,
    normed tensor 0.9984 1.0089 0.9927 0.0030 0.0020 -0.0031.
    """

    def test_measurements_and_tensor(self, run):
        out = run('sufar4', lambda out: convert.sufar4(
            'sufar4-asc_magic_example.txt', input_dir_path=in_dir('sufar_asc_magic'), dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 290
        # names are lower case unless preserve_case is set
        first = meas.iloc[0]
        assert first['specimen'] == '318-u1356a-1r-1-w-83'
        assert first['susc_chi_volume'] == pytest.approx(56.74e-6)
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        row = ams_row(specimens, '318-u1356a-1r-1-w-83', -1)
        # normalized by the trace (3) instead of by the mean
        np.testing.assert_allclose(tensor(row['aniso_s']),
                                   np.array([0.9984, 1.0089, 0.9927, 0.0030, 0.0020, -0.0031]) / 3,
                                   atol=1e-4)
        assert row['aniso_s_n_measurements'] == 15

    def test_preserve_case(self, run):
        out = run('sufar4_case', lambda out: convert.sufar4(
            'sufar4-asc_magic_example.txt', input_dir_path=in_dir('sufar_asc_magic'), dir_path=out,
            preserve_case=True))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert meas['specimen'].iloc[0] == '318-U1356A-1R-1-W-83'
