"""
Tests of the convert_2_magic converters of remanence (demagnetization) data:
bgc, generic, huji, huji_sample, jr6_txt, jr6_jr6, ldeo, livdb, mini, pmd, sio
and utrecht. (_2g_bin, cit, rs3 and tdt have their own test files; the IODP
converters are in test_convert_iodp.py.)

Expected values are read off the input files in data_files/convert_2_magic and
converted by hand (emu to Am^2, mT to T, C to K, ...); where a file also records
the direction in geographic coordinates, the sample orientation the converter
writes is checked by rotating the specimen direction with it. Tests marked
xfail(strict=True) record known defects: they start to pass, and so fail the
suite, once the defect is fixed, which is the reminder to remove the mark.
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


def direction(x, y, z):
    """
    Declination, inclination and length of a vector in MagIC specimen
    coordinates (x north, y east, z down).

    Returns:
        tuple: (dec, inc, length)
    """
    length = np.sqrt(x ** 2 + y ** 2 + z ** 2)
    return np.degrees(np.arctan2(y, x)) % 360, np.degrees(np.arcsin(z / length)), length


def assert_geographic(dec, inc, azimuth, dip, expected, tolerance):
    """the specimen direction rotated with the sample orientation is the expected one"""
    geo = pmag.dogeo(dec, inc, azimuth, dip)
    assert pmag.angle(list(geo), list(expected))[0] < tolerance


@pytest.fixture(scope='module')
def run(tmp_path_factory):
    """runs a converter into a new temporary directory and returns the output directory"""
    def _run(name, call):
        result, out_dir, cwd = convert_into(tmp_path_factory.mktemp(name), call)
        assert result[0] is True, result
        return out_dir
    return _run


class TestBgc:
    """
    Berkeley Geochronology Center files. 96MT.05.01 is a thermal and AF
    demagnetization: X, Y, Z in emu, INT in emu/cc, a volume of 6.9 cc, and times
    in the timezone given (US/Pacific by default).
    """

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('bgc', lambda out: convert.bgc('96MT.05.01', input_dir_path=in_dir('bgc_magic'),
                                                  dir_path=out))

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 19
        nrm = meas.iloc[0]
        # 14.04.97 16:48:20  -1  0.0  11.0  3.96e-06 -4.13e-06 2.36e-06 ... INT 8.97e-07
        dec, inc, moment = direction(3.96e-6, -4.13e-6, 2.36e-6)
        assert nrm['dir_dec'] == pytest.approx(dec)
        assert nrm['dir_inc'] == pytest.approx(inc)
        assert nrm['magn_moment'] == pytest.approx(moment * 1e-3)
        # INT, 8.97e-07 emu/cc, is the moment over the volume rounded
        assert nrm['magn_volume'] == pytest.approx(moment * 1e-3 / 6.9e-6)
        assert nrm['magn_volume'] == pytest.approx(8.97e-7 * 1e3, rel=1e-3)
        assert nrm['timestamp'] == '1997-04-14T23:48:20Z'
        assert nrm['method_codes'].startswith('LT-NO')
        # 16.04.97 12:26:23  -1  130.0: a heating to 130 C
        assert meas.iloc[2]['method_codes'].startswith('LT-T-Z')
        assert meas.iloc[2]['treat_temp'] == 403
        # 19.04.97 11:13:06  7  6.0: an AF step of 6 mT
        assert meas.iloc[6]['method_codes'].startswith('LT-AF-Z')
        assert meas.iloc[6]['treat_ac_field'] == pytest.approx(0.006)

    def test_append(self, tmp_path):
        """with append, a second file adds its specimen to the tables of the first"""
        def call(out):
            convert.bgc('BC0-3A', input_dir_path=in_dir('bgc_magic'), dir_path=out)
            return convert.bgc('96MT.05.01', input_dir_path=in_dir('bgc_magic'), dir_path=out,
                               append=True)
        result, out_dir, cwd = convert_into(tmp_path, call)
        assert result[0] is True
        specimens = read_table(os.path.join(out_dir, 'specimens.txt'))
        assert list(specimens['specimen']) == ['BC0-3A', '96MT.05.01']
        meas = read_table(os.path.join(out_dir, 'measurements.txt'))
        assert set(meas['specimen']) == {'BC0-3A', '96MT.05.01'}
        assert (meas['specimen'] == '96MT.05.01').sum() == 19


class TestGeneric:
    """generic_magic_example.txt: AF demagnetization, moments in emu, fields in mT"""

    def test_measurements(self, run):
        out = run('generic', lambda out: convert.generic(
            magfile=os.path.join(in_dir('generic_magic'), 'generic_magic_example.txt'),
            dir_path=out, experiment='Demag'))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 23
        assert list(meas['specimen'].unique()) == ['sr01e2', 'sr01g2']
        # sr01e2  0  A  2.93E-02  200.6  27.9 / sr01e2  10  A  2.83E-02  201  27.7
        nrm, af_10 = meas.iloc[0], meas.iloc[1]
        assert nrm['method_codes'].startswith('LT-NO')
        assert (nrm['dir_dec'], nrm['dir_inc']) == (200.6, 27.9)
        assert nrm['magn_moment'] == pytest.approx(2.93e-5)
        assert af_10['method_codes'].startswith('LT-AF-Z')
        assert af_10['treat_ac_field'] == pytest.approx(0.010)
        assert af_10['magn_moment'] == pytest.approx(2.83e-5)

    def test_experiment_is_required(self, tmp_path):
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.generic(
            magfile=os.path.join(in_dir('generic_magic'), 'generic_magic_example.txt'), dir_path=out))
        assert result[0] is False
        assert result[1].startswith('Must provide experiment')


class TestHuji:
    """
    HUJI files (new format). The first line of Massada_AF_HUJI_new_format.txt is
    the NRM of M5-110D: dec/inc 197.6/28.4 in specimen coordinates, 1.42E-05 emu.
    """

    def test_measurements(self, run):
        out = run('huji', lambda out: convert.huji(
            magfile='Massada_AF_HUJI_new_format.txt', input_dir_path=in_dir('huji_magic'),
            dir_path=out, codelist='AF'))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 616
        assert meas['specimen'].nunique() == 56
        nrm, af_5 = meas.iloc[0], meas.iloc[1]
        assert nrm['specimen'] == 'M5-110D'
        assert nrm['method_codes'].startswith('LT-NO')
        assert (nrm['dir_dec'], nrm['dir_inc']) == (197.6, 28.4)
        assert nrm['magn_moment'] == pytest.approx(1.42e-8)
        assert af_5['method_codes'].startswith('LT-AF-Z')
        assert af_5['treat_ac_field'] == pytest.approx(0.005)
        samples = read_table(os.path.join(out, 'samples.txt'))
        assert dict(zip(samples['sample'], samples['site']))['M5-110D'] == 'M5-110'

    def test_experiment_type_is_required(self, tmp_path):
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.huji(
            magfile='Massada_AF_HUJI_new_format.txt', input_dir_path=in_dir('huji_magic'),
            dir_path=out))
        assert result[0] is False
        assert result[1].startswith('Must select experiment type')


class TestHujiSample:
    """
    HUJI orientation files: magdelkrum_datafile.txt has the azimuth and dip of
    each sample, the bedding and the latitude and longitude.
    """

    @pytest.mark.parametrize('ignore_dip, azimuth', [(True, 0), (False, 22)])
    def test_samples_and_sites(self, run, ignore_dip, azimuth):
        out = run('huji_sample', lambda out: convert.huji_sample(
            'magdelkrum_datafile.txt', input_dir_path=in_dir('huji_magic'), dir_path=out,
            ignore_dip=ignore_dip, location_name='Magdelkrum'))
        samples = read_table(os.path.join(out, 'samples.txt'))
        assert len(samples) == 57
        # mk118  22  21  0  0  35.23788  32.92075
        mk118 = samples.set_index('sample').loc['mk118']
        assert mk118['site'] == 'mk11'
        assert mk118['azimuth'] == azimuth
        assert (mk118['lat'], mk118['lon']) == (35.23788, 32.92075)
        sites = read_table(os.path.join(out, 'sites.txt'))
        assert 'mk11' in set(sites['site'])
        # the location is in the sites table
        assert set(sites['location']) == {'Magdelkrum'}
        # one row per site
        assert sites['site'].is_unique
        assert set(sites['site']) == set(samples['site'])

    def test_bedding(self, tmp_path):
        """the file gives the bedding strike; the dip direction is 90 degrees to its right"""
        in_dir_path = tmp_path / 'in'
        in_dir_path.mkdir()
        with open(str(in_dir_path / 'orient.txt'), 'w') as f:
            f.write('Sample ID\tAlpha (azi)\tBetha(dip)\tStrike\tdip\tLat\tLong\n'
                    'ab11\t22\t21\t30\t20\t35.2\t32.9\n'
                    'ab12\t30\t15\t300\t10\t35.2\t32.9\n')
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.huji_sample(
            'orient.txt', input_dir_path=str(in_dir_path), dir_path=out))
        assert result[0] is True, result
        samples = read_table(os.path.join(out_dir, 'samples.txt')).set_index('sample')
        assert list(samples['bed_dip_direction']) == [120, 30]
        assert list(samples['bed_dip']) == [20, 10]
        sites = read_table(os.path.join(out_dir, 'sites.txt'))
        assert list(sites['site']) == ['ab1']
        assert (sites.iloc[0]['bed_dip_direction'], sites.iloc[0]['bed_dip']) == (120, 20)


class TestJr6Txt:
    """
    AGICO JR6 text files (AP12.txt). AP12-01A: the mean of the NRM is
    56.28E-03 A/m at 344/-15 in specimen and 2/-21 in geographic coordinates;
    the specimen angles are 19 and 7 with the orientation parameters 12 0 12 90.
    """

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('jr6_txt', lambda out: convert.jr6_txt('AP12.txt', input_dir_path=in_dir('jr6_magic'),
                                                          dir_path=out))

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 69
        assert meas['specimen'].nunique() == 9
        nrm = meas.iloc[0]
        assert nrm['specimen'] == 'AP12-01A'
        assert (nrm['dir_dec'], nrm['dir_inc']) == (344, -15)
        assert nrm['magn_volume'] == pytest.approx(56.28e-3)
        assert nrm['magn_moment'] == pytest.approx(56.28e-3 * 12e-6)  # default volume 12 cc
        assert nrm['timestamp'] == '2014-05-08T00:00:00Z'
        af_steps = meas[meas['specimen'] == 'AP12-01B']
        assert af_steps['method_codes'].iloc[1].startswith('LT-AF-Z')
        assert af_steps['treat_ac_field'].iloc[1] == pytest.approx(0.002)

    def test_orientation(self, out):
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        assert (samples.loc['AP12-01', 'azimuth'], samples.loc['AP12-01', 'dip']) == (19, -7)
        # the geographic direction in the file is given to the nearest degree
        assert_geographic(344, -15, 19, -7, (2, -21), 1)


class TestJr6Jr6:
    """
    AGICO JR6 files (AF.jr6). The first line, BR14B NRM, has X, Y, Z = -1.01,
    1.02, -6.95 times 10^-1 A/m, the sample azimuth 342 and dip 28 with the
    orientation parameters 12 90 12 0, and no bedding (0 0).
    """

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('jr6_jr6', lambda out: convert.jr6_jr6('AF.jr6', input_dir_path=in_dir('jr6_magic'),
                                                          dir_path=out))

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 655
        assert meas['specimen'].nunique() == 57
        nrm = meas[meas['specimen'] == 'BR14B'].iloc[0]
        dec, inc, intensity = direction(-1.01, 1.02, -6.95)
        assert nrm['method_codes'].startswith('LT-NO')
        assert nrm['dir_dec'] == pytest.approx(dec, abs=1e-3)
        assert nrm['dir_inc'] == pytest.approx(inc, abs=1e-3)
        assert nrm['magn_volume'] == pytest.approx(intensity * 0.1, rel=1e-5)
        assert nrm['magn_moment'] == pytest.approx(intensity * 0.1 * 12e-6, rel=1e-5)
        af_10 = meas[meas['specimen'] == 'BR14B'].iloc[1]
        assert af_10['treat_ac_field'] == pytest.approx(0.010)

    def test_orientation(self, out):
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        # P2 = 90: the dip of the X axis is the plunge minus 90
        assert (samples.loc['BR14', 'azimuth'], samples.loc['BR14', 'dip']) == (342, -62)

    @pytest.mark.xfail(strict=True, reason='bed_dip_direction and bed_dip are copied from the '
                                           'sample azimuth and dip')
    def test_bedding(self, out):
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        assert samples.loc['BR14', 'bed_dip'] == 0


class TestLdeo:
    """
    LDEO files. The first line of ldeo_magic_example.dat is the NRM of is031c2:
    J 461.6 (10^-7 Am^2), dec/inc 163.9/17.5 in specimen coordinates.
    """

    def test_measurements(self, run):
        out = run('ldeo', lambda out: convert.ldeo('ldeo_magic_example.dat', codelist='AF',
                                                   input_dir_path=in_dir('ldeo_magic'), dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert meas['specimen'].nunique() == 35
        is039g2 = meas[meas['specimen'] == 'is039g2']
        assert len(is039g2) == 13
        nrm = meas.iloc[0]
        assert nrm['specimen'] == 'is031c2'
        assert nrm['method_codes'].startswith('LT-NO')
        assert (nrm['dir_dec'], nrm['dir_inc']) == (163.9, 17.5)
        assert nrm['magn_moment'] == pytest.approx(461.6e-7)
        # is039g2  2.5  SD  0  200.300  191.3  3.8
        af = is039g2.iloc[1]
        assert af['method_codes'].startswith('LT-AF-Z')
        assert af['treat_ac_field'] == pytest.approx(0.0025)
        assert (af['dir_dec'], af['dir_inc']) == (191.3, 3.8)
        assert af['magn_moment'] == pytest.approx(200.3e-7)


class TestLivdb:
    """
    Liverpool database files of paleointensity experiments (Thellier IZZI and
    microwave experiments). A .livdb line is the treatment temperature in C,
    two unused fields, the moment x, y, z in 1e-9 Am^2, ..., the lab field in
    microtesla, its phi and theta, ... and the step type (Z, I, P for a pTRM check).
    The measurements tables in each folder were made by the converter and
    checked when the example data were added, and must stay the same.
    """

    # the first lines of TH_IZZI+/ATPI_Thellier.livdb: T (C), x, y, z, lab field (uT), type
    # lines 1 and 3-7 of TH_IZZI+/ATPI_Thellier.livdb (line 2 is a 5 mT AF
    # cleaning step): T (C), x, y, z, lab field (uT), step type
    IZZI_STEPS = [(0, -505.095, 286.555, -427.045, 0, 'Z'), (400, -442.655, 39.025, -267.6, 0, 'Z'),
                  (400, -433.735, 25.645, -396.94, 30, 'I'), (500, -388.02, 23.415, -447.115, 30, 'I'),
                  (500, -386.905, 0, -258.68, 0, 'Z'), (400, -377.985, 3.345, -389.135, 30, 'P')]

    def test_izzi_steps(self, run):
        """moments, directions, temperatures, lab field and step codes from the raw lines"""
        out = run('livdb_izzi', lambda out: convert.livdb(
            os.path.join(in_dir('livdb_magic'), 'TH_IZZI+'), output_dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        meas = meas[meas['specimen'] == 'ATPIPV04-1A']
        meas = meas[meas['treat_ac_field'].isna() | (meas['treat_ac_field'] == 0)].iloc[:len(self.IZZI_STEPS)]
        code = {'Z': 'LT-T-Z', 'I': 'LT-T-I', 'P': 'LT-PTRM-I'}
        for (temp, x, y, z, field, step), (_, row) in zip(self.IZZI_STEPS, meas.iterrows()):
            dec, inc, moment = direction(x, y, z)
            assert row['dir_dec'] == pytest.approx(dec, abs=0.01)
            assert row['dir_inc'] == pytest.approx(inc, abs=0.01)
            assert row['magn_moment'] == pytest.approx(moment * 1e-9, rel=1e-3)
            assert row['treat_temp'] == temp + 273
            assert row['treat_dc_field'] == pytest.approx(field * 1e-6)
            expected = 'LT-NO' if temp == 0 else code[step]
            assert row['method_codes'].startswith(expected), (temp, step, row['method_codes'])

    @pytest.mark.parametrize('folder', ['TH_IZZI+', 'MW_C+', 'MW_IZZI+andC++', 'MW_OT+', 'MW_P'])
    def test_matches_the_reference_tables(self, run, folder):
        out = run('livdb', lambda out: convert.livdb(os.path.join(in_dir('livdb_magic'), folder),
                                                     output_dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        reference = read_table(os.path.join(in_dir('livdb_magic'), folder, 'measurements.txt'))
        assert len(meas) == len(reference)
        for col in ['specimen', 'method_codes']:
            assert list(meas[col]) == list(reference[col])
        for col in ['dir_dec', 'dir_inc', 'magn_moment', 'treat_temp', 'treat_dc_field',
                    'treat_dc_field_phi', 'treat_dc_field_theta']:
            if col in reference:
                np.testing.assert_allclose(meas[col], reference[col], rtol=1e-6, err_msg=col)

    @pytest.mark.parametrize('options, sample, site', [
        ({}, 'ATPIPV04-1A', 'ATPIPV04-1A'),
        ({'samp_name_con': 2, 'samp_num_chars': 1}, 'ATPIPV04-1', 'ATPIPV04-1'),
        ({'samp_name_con': 3, 'samp_num_chars': '-'}, 'ATPIPV04', 'ATPIPV04'),
        ({'samp_name_con': 2, 'samp_num_chars': 1, 'site_name_con': 3, 'site_num_chars': '-'},
         'ATPIPV04-1', 'ATPIPV04'),
    ])
    def test_naming(self, run, options, sample, site):
        """sample (and site) names from the specimen (sample) name minus some characters, or up to a delimiter"""
        out = run('livdb_naming', lambda out: convert.livdb(
            os.path.join(in_dir('livdb_magic'), 'TH_IZZI+'), output_dir_path=out, **options))
        specimens = read_table(os.path.join(out, 'specimens.txt')).set_index('specimen')
        assert specimens.loc['ATPIPV04-1A', 'sample'] == sample
        samples = read_table(os.path.join(out, 'samples.txt')).set_index('sample')
        assert samples.loc[sample, 'site'] == site


class TestMini:
    """
    Yale minispin files (Peru_rev1.txt): specimen_step, dec, inc, magnetization
    in mA/m. Cup-1-1_50 is an AF step of 50 mT, at 126.9/34.3, 4.393 mA/m.
    """

    def test_measurements(self, tmp_path):
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.mini(
            'Peru_rev1.txt', input_dir_path=in_dir('mini_magic'), dir_path=out, methcode='AF'))
        assert result[0] is True
        assert result[1] == os.path.join(out_dir, 'measurements.txt')
        assert os.listdir(cwd) == []
        meas = read_table(os.path.join(out_dir, 'measurements.txt'))
        assert len(meas) == 103
        cup = meas[meas['specimen'] == 'Cup-1-1']
        assert list(cup['treat_ac_field']) == pytest.approx([0.05, 0.10, 0.15, 0.20, 0.25])
        assert set(cup['method_codes']) == {'LT-AF-Z:LP-DIR-AF'}
        first = cup.iloc[0]
        assert (first['dir_dec'], first['dir_inc']) == (126.9, 34.3)
        # default volume 12 cc; the moment is written with four digits
        assert first['magn_moment'] == pytest.approx(4.393e-3 * 12e-6, rel=1e-3)
        samples = read_table(os.path.join(out_dir, 'samples.txt')).set_index('sample')
        assert samples.loc['Cup-1-1', 'site'] == 'Cup-1'
        # J-99-1_2_50: specimen J-99-1_2 (a '_' in the name, like J-99-1-3) at 50 mT
        j99 = meas[meas['specimen'] == 'J-99-1_2']
        assert list(j99['treat_ac_field']) == pytest.approx([0.05])
        assert (j99.iloc[0]['dir_dec'], j99.iloc[0]['dir_inc']) == (305.1, -36.4)
        specimens = read_table(os.path.join(out_dir, 'specimens.txt')).set_index('specimen')
        assert len(specimens) == 35
        assert specimens.loc['J-99-1_2', 'sample'] == 'J-99-1'
        assert samples.loc['J-99-1', 'site'] == 'J-99'


class TestPmd:
    """
    PaleoMag .pmd files (ss0207a.pmd): Xc, Yc, Zc in Am^2, the magnetization in
    A/m, and the direction in geographic (Dg, Ig) coordinates; the core azimuth
    a=282.6 and hade b=68.5, no bedding.
    """

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('pmd', lambda out: convert.pmd('ss0207a.pmd', input_dir_path=in_dir('pmd_magic', 'UCSC', 'PMD'),
                                                  dir_path=out))

    # STEP, Xc, Yc, Zc, MAG, Dg, Ig of the first three lines
    STEPS = [(0.000, 3.23e-6, 5.88e-6, 4.94e-5, 4.53, 289.7, 17.6),
             (0.006, 1.53e-6, 5.07e-6, 4.13e-5, 3.78, 290.0, 19.2),
             (0.012, -1.29e-6, 4.13e-6, 2.37e-5, 2.19, 293.5, 24.2)]

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 8
        assert meas.iloc[0]['method_codes'].startswith('LT-NO')
        assert meas.iloc[1]['method_codes'].startswith('LT-AF-Z')
        for (field, x, y, z, mag, _, _), (_, row) in zip(self.STEPS, meas.iterrows()):
            dec, inc, moment = direction(x, y, z)
            assert row['treat_ac_field'] == pytest.approx(field)
            assert row['dir_dec'] == pytest.approx(dec, abs=0.1)
            assert row['dir_inc'] == pytest.approx(inc, abs=0.1)
            assert row['magn_moment'] == pytest.approx(moment, rel=1e-3)
            assert row['magn_volume'] == pytest.approx(mag)

    def test_orientation(self, out):
        sample = read_table(os.path.join(out, 'samples.txt')).iloc[0]
        assert (sample['azimuth'], sample['dip']) == (282.6, -68.5)
        meas = read_table(os.path.join(out, 'measurements.txt'))
        for (_, _, _, _, _, dec_geo, inc_geo), (_, row) in zip(self.STEPS, meas.iterrows()):
            assert_geographic(row['dir_dec'], row['dir_inc'], sample['azimuth'], sample['dip'],
                              (dec_geo, inc_geo), 0.2)


class TestSio:
    """
    SIO files (sio_af_example.dat): specimen, AF field in mT, csd, moment in
    emu, dec, inc. The first line is sc12b1 at 0 mT, 2.878E-2 emu, 185.0/9.3;
    the steps from 100 mT up are measured three times.
    """

    def test_measurements(self, run):
        out = run('sio', lambda out: convert.sio('sio_af_example.dat', codelist='AF',
                                                 input_dir_path=in_dir('sio_magic'), dir_path=out))
        meas = read_table(os.path.join(out, 'measurements.txt'))
        # 10 single steps and 4 averages of three
        assert len(meas) == 14
        nrm, af_5 = meas.iloc[0], meas.iloc[1]
        assert nrm['method_codes'].startswith('LT-NO')
        assert (nrm['dir_dec'], nrm['dir_inc']) == (185.0, 9.3)
        assert nrm['magn_moment'] == pytest.approx(2.878e-5)
        assert af_5['method_codes'].startswith('LT-AF-Z')
        assert af_5['treat_ac_field'] == pytest.approx(0.005)
        assert af_5['magn_moment'] == pytest.approx(2.864e-5)
        # sc12b1  100.00  1.186E-2 188.1 9.9 / 1.183E-2 188.1 10.1 / 1.188E-2 185.4 10.1
        replicates = [(188.1, 9.9, 1.186e-5), (188.1, 10.1, 1.183e-5), (185.4, 10.1, 1.188e-5)]
        mean = np.mean([pmag.dir2cart(rep) for rep in replicates], axis=0)
        dec, inc, moment = pmag.cart2dir(mean)
        af_100 = meas[np.isclose(meas['treat_ac_field'], 0.1)]
        assert len(af_100) == 1
        assert af_100['dir_dec'].iloc[0] == pytest.approx(dec, abs=0.1)
        assert af_100['dir_inc'].iloc[0] == pytest.approx(inc, abs=0.1)
        assert af_100['magn_moment'].iloc[0] == pytest.approx(moment, rel=1e-3)


class TestUtrecht:
    """
    Utrecht files (Utrecht_Example.af). The header of KO_86.1 has the azimuth
    288, dip 39, volume 10.5 cc, and bedding strike 169 and dip 15 (dip direction 259); the
    measurements are A, B, C in pAm^2 (MagIC x = -B, y = C, z = -A).
    """

    @pytest.fixture(scope='class')
    def out(self, run):
        return run('utrecht', lambda out: convert.utrecht('Utrecht_Example.af', input_dir_path=in_dir('utrecht_magic'),
                                                          dir_path=out))

    def test_measurements(self, out):
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert len(meas) == 350
        assert meas['specimen'].nunique() == 25
        # 0,-1.48E+03,4.58E+02,2.82E+03,0.99,5/31/2007,4:09:48 PM
        nrm = meas.iloc[0]
        dec, inc, moment = direction(-4.58e2, 2.82e3, 1.48e3)
        assert nrm['specimen'] == 'KO_86.1'
        assert nrm['method_codes'].startswith('LT-NO')
        assert nrm['dir_dec'] == pytest.approx(dec)
        assert nrm['dir_inc'] == pytest.approx(inc)
        assert nrm['magn_moment'] == pytest.approx(moment * 1e-12)
        assert nrm['magn_volume'] == pytest.approx(moment * 1e-12 / 10.5e-6)
        assert meas.iloc[1]['treat_ac_field'] == pytest.approx(0.005)

    def test_orientation(self, out):
        """
        the converter takes the second header angle as a plunge and writes
        dip = angle - 90; the file holds no geographic direction to check this
        against, so this guards the convention rather than verifying it
        """
        samples = read_table(os.path.join(out, 'samples.txt'))
        first = samples.iloc[0]
        assert (first['azimuth'], first['dip'], first['bed_dip_direction']) == (288, -51, 259)

    def test_bed_dip(self, out):
        with open(os.path.join(out, 'samples.txt')) as f:
            lines = f.read().splitlines()
        # a header line, the column names, and one line per sample
        samples = read_table(os.path.join(out, 'samples.txt'))
        assert len(lines) == 2 + len(samples)
        assert samples.iloc[0]['bed_dip'] == 15

    def test_timestamps(self, out):
        """the times are on a 12-hour clock in Utrecht (UTC+2 in summer)"""
        meas = read_table(os.path.join(out, 'measurements.txt'))
        first = meas.groupby('specimen', sort=False)['timestamp'].first()
        # KO_86.1: 0,-1.48E+03,4.58E+02,2.82E+03,0.99,5/31/2007,4:09:48 PM
        assert first['KO_86.1'] == '2007-05-31T14:09:48Z'
        # KO_86.3: 0.0, 2.0363E+3, 6.0421E+2, 2.8818E+3,0.99,6/9/2007,8:22:55 AM
        assert first['KO_86.3'] == '2007-06-09T06:22:55Z'

    @pytest.mark.parametrize('end', ['"END"\r\n', ''])
    def test_line_endings_and_white_space(self, tmp_path, end):
        """Windows line endings, white space and blank lines, and no END line"""
        in_dir_path = tmp_path / 'in'
        in_dir_path.mkdir()
        with open(str(in_dir_path / 'example.th'), 'w', newline='') as f:
            f.write('"ROBOT", "2G DC"\r\n'
                    '"AB1.1", 1586, 288, 39, 10.5, 169, 15 \r\n'
                    '0, -1.48E+03, 4.58E+02, 2.82E+03, 0.99, 5/31/2007, 16:09:48\r\n'
                    ' 100.0, -1.59E+03, 2.42E+01, 2.79E+03, 0.99, 5/31/2007, 16:30:00\r\n'
                    '9999 \r\n'
                    '\r\n'
                    '"AB2.1", 1586, 200, 30, 10.5, 169, 25\r\n'
                    '0, -1.48E+03, 4.58E+02, 2.82E+03, 0.99, 5/31/2007, 12:05:00 AM\r\n'
                    '9999\r\n' + end)
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.utrecht(
            'example.th', input_dir_path=str(in_dir_path), dir_path=out, specnum=0))
        assert result[0] is True, result
        samples = read_table(os.path.join(out_dir, 'samples.txt'))
        assert list(zip(samples['azimuth'], samples['bed_dip'])) == [(288, 15), (200, 25)]
        meas = read_table(os.path.join(out_dir, 'measurements.txt'))
        assert list(meas['timestamp']) == ['2007-05-31T14:09:48Z', '2007-05-31T14:30:00Z',
                                           '2007-05-30T22:05:00Z']
        assert list(meas['treat_temp']) == pytest.approx([273, 373, 273])
        assert set(meas['instrument_codes']) == {'Utrecht_2G DC'}

    def test_lines_without_date(self, tmp_path):
        """a measurement line may end before the date and time"""
        in_dir_path = tmp_path / 'in'
        in_dir_path.mkdir()
        with open(str(in_dir_path / 'example.af'), 'w') as f:
            f.write('ROBOT,2G DC\n'
                    'AB1.1,1586,288,39,10.5,169,15\n'
                    '0,-1.48E+03,4.58E+02,2.82E+03,0.99\n'
                    '5,-1.59E+03,2.42E+01,2.79E+03,0.99,5/31/2007,4:09:48 PM\n'
                    '9999\nEND\n')
        result, out_dir, cwd = convert_into(tmp_path, lambda out: convert.utrecht(
            'example.af', input_dir_path=str(in_dir_path), dir_path=out, specnum=0))
        assert result[0] is True, result
        meas = read_table(os.path.join(out_dir, 'measurements.txt'))
        assert len(meas) == 2
        assert meas['timestamp'].isnull().iloc[0]
        assert meas['timestamp'].iloc[1] == '2007-05-31T14:09:48Z'
        assert list(meas['dir_csd']) == [0.99, 0.99]
