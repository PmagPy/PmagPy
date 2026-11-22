"""
Tests for the IODP converters in convert_2_magic.

Two families are covered:

* the older LIMS converters: iodp_srm (section-half SRM csv files),
  iodp_jr6 (JR6 spinner text files) and iodp_samples (LIMS sample csv files)
* the LORE workflow: iodp_samples_csv builds the specimens, samples, sites and
  locations tables that iodp_dscr_lore, iodp_jr6_lore and iodp_kly4s_lore then
  draw on, and iodp_srm_lore converts archive-half SRM data on its own

Expected values are computed from the rows of the input files (unit
conversions, naming conventions, method codes) rather than copied from the
converter output. Every converter writes into a temporary directory, never
into data_files. Tests marked xfail(strict=True) record known defects in the
converters: they start to pass, and so fail the suite, once the defect is
fixed, which is the reminder to remove the mark.
"""
import os

import numpy as np
import pandas as pd
import pytest

from pmagpy import convert_2_magic as convert
from pmagpy.test.convert_helpers import WD, model_columns, read_table, table_type

SRM_DIR = os.path.join(WD, 'data_files', 'convert_2_magic', 'iodp_srm_magic')
JR6_DIR = os.path.join(WD, 'data_files', 'convert_2_magic', 'iodp_jr6_magic')
UTESTA_SRM_DIR = os.path.join(WD, 'data_files', 'UTESTA', 'SRM_data')
U999A_DIR = os.path.join(WD, 'data_files', 'iodp_magic', 'U999A')
HOLE_LAT, HOLE_LON = -56.557775, -42.64212833333333


# ---------------------------------------------------------------- helpers

def write_subset(src, dest, keep):
    """
    Copy the header and the data lines that pass a test into a new file, so a
    converter can be run on a few rows of a large input file. The lines are
    copied as read, with line endings normalized.

    Args:
        src (str): input file
        dest (str): file to write
        keep (callable): called with each data line, True to keep it

    Returns:
        str: dest
    """
    with open(src, encoding='utf-8') as f:
        lines = f.readlines()
    with open(dest, 'w', encoding='utf-8') as f:
        f.writelines([lines[0]] + [line for line in lines[1:] if keep(line)])
    return dest


def angle_between(dec1, inc1, dec2, inc2):
    """
    The angle between two directions.

    Args:
        dec1, inc1 (float): first direction, degrees
        dec2, inc2 (float): second direction, degrees

    Returns:
        float: the angle in degrees
    """
    def unit_vector(dec, inc):
        dec, inc = np.radians(dec), np.radians(inc)
        return np.array([np.cos(inc) * np.cos(dec), np.cos(inc) * np.sin(dec), np.sin(inc)])
    cos_angle = np.dot(unit_vector(dec1, inc1), unit_vector(dec2, inc2))
    return np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))


def lore_specimen_name(row, offset_key):
    """
    The specimen name the LORE converters build from a row of a LORE csv
    file: exp-SiteHole-CoreType-Sect-A/W-offset, with the offset as a float.

    Args:
        row (pandas.Series): row of a LORE csv file
        offset_key (str): name of the offset column

    Returns:
        str: the specimen name
    """
    return '{}-{}{}-{}{}-{}-{}-{}'.format(row['Exp'], row['Site'], row['Hole'],
                                         row['Core'], row['Type'], row['Sect'],
                                         row['A/W'], float(row[offset_key]))


@pytest.fixture(autouse=True, scope='module')
def separate_cwd(tmp_path_factory):
    """
    Run the module from an empty working directory, so that nothing a
    converter writes relative to the working directory lands in the repository.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(tmp_path_factory.mktemp('cwd'))
        yield


# -------------------------------------------------------- converted outputs
# Each module-scoped fixture runs one converter once; the tests below and the
# data-model check share the output.

@pytest.fixture(scope='module')
def srm_janus(tmp_path_factory):
    """
    iodp_srm on the first 40 rows of each of the two sections in a LIMS (Janus)
    section-half export, with custom output file names.
    """
    out = tmp_path_factory.mktemp('srm_janus')
    rows_per_section = {}

    def first_rows(line):
        section = tuple(line.split(',')[3:6])  # Core, Type, Sect
        rows_per_section[section] = rows_per_section.get(section, 0) + 1
        return rows_per_section[section] <= 40

    raw_file = write_subset(os.path.join(SRM_DIR, 'IODP_Janus_312_U1256.csv'),
                            str(out / 'janus.csv'), first_rows)
    names = dict(meas_file='srm_measurements.txt', spec_file='srm_specimens.txt',
                 samp_file='srm_samples.txt', site_file='srm_sites.txt',
                 loc_file='srm_locations.txt')
    result = convert.iodp_srm(csv_file='janus.csv', input_dir_path=str(out),
                              dir_path=str(out), lat=HOLE_LAT, lon=HOLE_LON, **names)
    return result, out, names, raw_file


@pytest.fixture(scope='module')
def jr6_out(tmp_path_factory):
    """iodp_jr6 on the one-line JR6 example file."""
    out = tmp_path_factory.mktemp('jr6')
    result = convert.iodp_jr6('test.jr6', input_dir_path=JR6_DIR, dir_path=str(out),
                              site='U999A', expedition='999', volume=7)
    return result, out


@pytest.fixture(scope='module')
def samples_out(tmp_path_factory):
    """iodp_samples on a LIMS sample export from Expedition 318."""
    out = tmp_path_factory.mktemp('iodp_samples')
    result = convert.iodp_samples('samples_318_U1359_B.csv', input_dir_path=SRM_DIR,
                                  output_dir_path=str(out))
    return result, out


@pytest.fixture(scope='module')
def lore_out(tmp_path_factory):
    """
    The LORE workflow for hole U999A in one directory: iodp_samples_csv first,
    then the discrete SRM, JR6 and KLY4S data that refer to its specimens.
    """
    out = str(tmp_path_factory.mktemp('lore'))
    results = {}
    results['samples_csv'] = convert.iodp_samples_csv(
        'samples_17_5_2019.csv', input_dir_path=U999A_DIR, dir_path=out,
        comp_depth_key='Top depth CSF-B (m)', lat=HOLE_LAT, lon=HOLE_LON, exp_name='999')
    results['dscr'] = convert.iodp_dscr_lore(
        'srmdiscrete_17_5_2019.csv', input_dir_path=os.path.join(U999A_DIR, 'SRM_discrete_data'),
        dir_path=out, meas_file='dscr_measurements.txt')
    results['jr6'] = convert.iodp_jr6_lore(
        'spinner_17_5_2019.csv', input_dir_path=os.path.join(U999A_DIR, 'JR6_data'),
        dir_path=out, meas_file='jr6_measurements.txt')
    results['kly4s'] = convert.iodp_kly4s_lore(
        'ex-kappa_17_5_2019.csv', input_dir_path=os.path.join(U999A_DIR, 'KLY4S_data'),
        dir_path=out, meas_out='kly4s_measurements.txt', spec_out='kly4s_specimens.txt',
        actual_volume=7)
    return results, out


SRM_ARCHIVE = os.path.join(U999A_DIR, 'SRM_archive_data', 'srmsection_17_5_2019.csv')
# one archive-half position (core 1H, section 1, offset 0 cm) measured in two
# runs, so its NRM appears twice
ONE_POSITION = '"999","U999","A","1","H","1","A","0.0",'


def run_srm_lore(out_dir, noave):
    """
    Run iodp_srm_lore on the rows of ONE_POSITION.

    Args:
        out_dir (pathlib.Path): directory for the input subset and the output
        noave (bool): True to keep replicate measurements separate

    Returns:
        tuple: the converter's return value, and the raw rows as a DataFrame
    """
    subset = write_subset(SRM_ARCHIVE, str(out_dir / 'srm.csv'),
                          lambda line: line.startswith(ONE_POSITION))
    result = convert.iodp_srm_lore('srm.csv', input_dir_path=str(out_dir), dir_path=str(out_dir),
                                   noave=noave, lat=HOLE_LAT, lon=HOLE_LON)
    return result, pd.read_csv(subset)


@pytest.fixture(scope='module')
def srm_lore_out(tmp_path_factory):
    """iodp_srm_lore on one archive-half position, replicates kept separate."""
    out = tmp_path_factory.mktemp('srm_lore')
    result, raw = run_srm_lore(out, noave=True)
    return result, out, raw


# ------------------------------------------------------------ iodp_srm (LIMS)

class TestIodpSrm:

    def test_janus_section_half_export(self, srm_janus):
        """
        one measurement per data row, with the corrected direction, the
        intensity times the default 15.59 cc as moment, AF steps in tesla, and
        continuous-measurement names exp-SiteHole-CoreType_SectHalf-offset
        """
        (ran, meas_file), out, names, raw_file = srm_janus
        assert ran
        assert meas_file == names['meas_file']
        for fname in names.values():
            assert os.path.isfile(os.path.join(out, fname))
        raw = pd.read_csv(raw_file, dtype=str)
        meas = read_table(os.path.join(out, meas_file))
        assert len(meas) == len(raw)
        nrm_row = raw[raw['Demag level (mT)'] == '0'].iloc[0]
        af_row = raw[raw['Demag level (mT)'] != '0'].iloc[0]
        for row in (nrm_row, af_row):
            specimen = '{}-{}{}-{}{}_{}{}-{}'.format(row['Exp'], row['Site'], row['Hole'],
                                                    row['Core'].zfill(3), row['Type'],
                                                    row['Sect'], row['A/W'], row['Offset (cm)'])
            field = float(row['Demag level (mT)']) * 1e-3
            rec = meas[(meas.specimen == specimen) & np.isclose(meas.treat_ac_field, field)]
            assert len(rec) == 1
            rec = rec.iloc[0]
            assert rec.dir_dec == pytest.approx(float(
                row['Declination background & tray corrected (deg)']))
            assert rec.dir_inc == pytest.approx(float(
                row['Inclination background & tray corrected (deg)']))
            assert rec.magn_moment == pytest.approx(float(
                row['Intensity background & tray corrected (A/m)']) * 15.59e-6, rel=1e-3)
            expected_code = 'LT-NO' if field == 0 else 'LT-AF-Z'
            assert rec.method_codes.split(':')[0] == expected_code
        specimens = read_table(os.path.join(out, names['spec_file']))
        samples = read_table(os.path.join(out, names['samp_file']))
        locations = read_table(os.path.join(out, names['loc_file']))
        assert set(meas.specimen) == set(specimens.specimen)
        assert len(samples) == raw[['Core', 'Type']].drop_duplicates().shape[0]
        assert list(locations.location) == ['U1256D']
        assert locations.lat_n[0] == pytest.approx(HOLE_LAT)

    def test_amp_escaped_headers(self, tmp_path):
        """
        a LIMS export whose headers spell & as &amp; converts the same way;
        cores are padded to three digits in the names
        """
        write_subset(os.path.join(UTESTA_SRM_DIR, 'srmsection-XXX-UTEST-A.csv'),
                     str(tmp_path / 'section.csv'), lambda line: line.startswith('XXX,UTEST,A,1,H,1,'))
        ran, meas_file = convert.iodp_srm(csv_file='section.csv', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(tmp_path / 'section.csv', dtype=str)
        meas = read_table(os.path.join(tmp_path, meas_file))
        assert len(meas) == len(raw)
        row = raw.iloc[0]
        rec = meas[(meas.specimen == 'XXX-UTESTA-001H_1A-' + row['Offset (cm)'])
                   & np.isclose(meas.treat_ac_field, float(row['Demag level (mT)']) * 1e-3)].iloc[0]
        assert rec.dir_dec == pytest.approx(float(
            row['Declination background &amp; tray corrected (deg)']))
        assert rec.dir_inc == pytest.approx(float(
            row['Inclination background &amp; tray corrected (deg)']))
        assert rec.timestamp == '2015-04-10T06:45:00Z'

    @pytest.mark.xfail(strict=True, raises=UnboundLocalError,
                       reason='iodp_srm only knows the degree-sign headers as the mis-decoded '
                              'byte string (\\xc2\\xb0) or the typo (\\n{DEGREE SIGN}), so the UTF-8 (°) headers of newer LIMS exports '
                              'leave dec_key unset')
    def test_degree_sign_headers(self, tmp_path):
        """a LIMS export with (°) in the direction headers converts"""
        write_subset(os.path.join(SRM_DIR, 'SRM_318_U1359_B_A.csv'), str(tmp_path / 'srm.csv'),
                     lambda line: line.startswith('318-U1359B-3H-2-A,'))
        ran, meas_file = convert.iodp_srm(csv_file='srm.csv', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(tmp_path / 'srm.csv')
        meas = read_table(os.path.join(tmp_path, meas_file))
        assert len(meas) == len(raw)
        assert meas.dir_dec.iloc[0] == pytest.approx(
            raw['Declination background + tray corrected (°)'].iloc[0])


# ------------------------------------------------------------------ iodp_jr6

def jr6_line(step, x, y, z, exponent):
    """
    A line of an IODP JR6 file (columns: specimen, step, -z, y, x, exponent,
    then orientation fields).

    Args:
        step (str): treatment label, e.g. NRM, AD020, TD300
        x, y, z (float): magnetization components, in units of 10**exponent A/m
        exponent (int): power of ten of the components

    Returns:
        str: the line
    """
    return '0_6599951 {:<8} {:.2f} {:.2f} {:.2f} {} 0 0 0 0 0 0 12 0 12 0 0\n'.format(
        step, -z, y, x, exponent)


class TestIodpJr6:

    def test_converts_spinner_file(self, jr6_out):
        """
        the x, y, -z components and exponent become a direction and a
        magnetization, and the moment is that magnetization times the volume
        """
        (ran, meas_file), out = jr6_out
        assert ran
        for fname in ['measurements.txt', 'specimens.txt', 'samples.txt', 'sites.txt',
                      'locations.txt']:
            assert os.path.isfile(os.path.join(out, fname))
        # test.jr6: 0_6599951 NRM 21.02 -2.87 -2.02 -3 ...
        x, y, z = -2.02, -2.87, -21.02
        magn_volume = np.sqrt(x**2 + y**2 + z**2) * 1e-3
        meas = read_table(os.path.join(out, meas_file))
        assert len(meas) == 1
        rec = meas.iloc[0]
        assert rec.specimen == '0_6599951'
        assert rec.method_codes.split(':')[0] == 'LT-NO'
        assert rec.dir_dec == pytest.approx(np.degrees(np.arctan2(y, x)) % 360, abs=0.05)
        assert rec.dir_inc == pytest.approx(np.degrees(np.arcsin(z * 1e-3 / magn_volume)), abs=0.05)
        assert rec.magn_volume == pytest.approx(magn_volume, rel=1e-4)
        assert rec.magn_moment == pytest.approx(magn_volume * 7e-6, rel=1e-4)
        samples = read_table(os.path.join(out, 'samples.txt'))
        assert samples.method_codes[0] == 'LP-NO:FS-C-DRILL-IODP:SP-SS-C:SO-V'
        assert read_table(os.path.join(out, 'locations.txt')).location[0] == '999U999A'

    def test_treatment_steps(self, tmp_path):
        """
        each treatment label gives its method code and its treatment in SI:
        AF steps in tesla, thermal steps in kelvin, ARM with a 50 uT bias field
        """
        steps = ['NRM', 'AD020', 'A40', 'TD300', 'T400', 'ARM050', 'IRM100']
        with open(tmp_path / 'steps.jr6', 'w') as f:
            for i, step in enumerate(steps):
                f.write(jr6_line(step, 1.0 + i, 2.0, -3.0, -3))
        ran, meas_file = convert.iodp_jr6('steps.jr6', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        meas = read_table(os.path.join(tmp_path, meas_file)).fillna(0)
        expected = [  # method code, treat_ac_field (T), treat_dc_field (T), treat_temp (K)
            ('LT-NO', 0, 0, 273),
            ('LT-AF-Z', 0.020, 0, 273),
            ('LT-AF-Z', 0.040, 0, 273),
            ('LT-T-Z', 0, 0, 573),
            ('LT-T-Z', 0, 0, 673),
            ('LT-AF-I', 0.050, 50e-6, 273),
            ('LT-IRM', 0, 0.100, 273),
        ]
        assert len(meas) == len(expected)
        for (_, rec), (code, ac_field, dc_field, temp) in zip(meas.iterrows(), expected):
            assert rec.method_codes.split(':')[0] == code
            assert rec.treat_ac_field == pytest.approx(ac_field)
            assert rec.treat_dc_field == pytest.approx(dc_field)
            assert rec.treat_temp == pytest.approx(temp)

    @pytest.mark.xfail(strict=True, raises=NameError,
                       reason='the unknown-treatment branch of iodp_jr6 refers to an '
                              'undefined variable `row`')
    def test_unknown_treatment(self, tmp_path):
        """a treatment label iodp_jr6 does not know returns False"""
        with open(tmp_path / 'bad.jr6', 'w') as f:
            f.write(jr6_line('XYZ10', 1.0, 2.0, -3.0, -3))
        ran, _ = convert.iodp_jr6('bad.jr6', input_dir_path=str(tmp_path), dir_path=str(tmp_path))
        assert not ran


# -------------------------------------------------------------- iodp_samples

class TestIodpSamples:

    def test_lims_sample_export(self, samples_out):
        """
        one sample per row with an interval in its label, named
        exp-SiteHole-CoreType-Sect-Half-interval with the core padded to four
        characters, and the volume converted from cc to m^3
        """
        (ran, samp_file), out = samples_out
        assert ran
        assert samp_file == os.path.join(str(out), 'samples.txt')
        raw = pd.read_csv(os.path.join(SRM_DIR, 'samples_318_U1359_B.csv'), dtype=str)
        with_interval = raw[raw['Label Id'].str.split().str.len() > 1]
        samples = read_table(samp_file)
        assert len(samples) == len(with_interval)
        row = with_interval.iloc[0]   # 318-U1359B-2H-1-W 40/42-Tauxe
        rec = samples.iloc[0]
        assert rec['sample'] == '318-U1359B-002H-1-W-40'
        assert rec.site == rec['sample']
        assert rec.sample_alternatives == row['Text Id']
        assert rec.core_depth == pytest.approx(float(row['Top Depth (m)']))
        assert rec.sample_volume == pytest.approx(float(row['Volume (cc)']) * 1e-6)
        assert rec.method_codes == 'FS-C-DRILL-IODP:SP-SS-C:SO-V'


# --------------------------------------------------------- the LORE workflow

class TestIodpSamplesCsv:

    def test_builds_the_tables(self, lore_out):
        """
        one specimen, sample and site per complete row, all with the same name,
        volume in m^3, depths on the sites, and one location per hole
        """
        results, out = lore_out
        ran, samp_file = results['samples_csv']
        assert ran
        assert samp_file == os.path.join(out, 'samples.txt')
        raw = pd.read_csv(os.path.join(U999A_DIR, 'samples_17_5_2019.csv'))
        complete = raw.dropna(subset=['Hole', 'Type', 'Sect', 'Top offset (cm)',
                                      'Top depth CSF-A (m)', 'A/W'])
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        samples = read_table(samp_file)
        sites = read_table(os.path.join(out, 'sites.txt'))
        locations = read_table(os.path.join(out, 'locations.txt'))
        names = [lore_specimen_name(row, 'Top offset (cm)') for _, row in complete.iterrows()]
        assert list(specimens.specimen) == names
        assert list(samples['sample']) == names
        assert list(sites.site) == names
        assert specimens.volume.values == pytest.approx(complete['Volume (cm3)'].values * 1e-6)
        assert sites.core_depth.values == pytest.approx(complete['Top depth CSF-A (m)'].values)
        assert sites.composite_depth.values == pytest.approx(complete['Top depth CSF-B (m)'].values)
        assert list(sites.lat) == pytest.approx([HOLE_LAT] * len(sites))
        assert list(sites.lon) == pytest.approx([HOLE_LON] * len(sites))
        assert list(locations.location) == ['U999A']
        assert locations.lat_s[0] == pytest.approx(HOLE_LAT)

    @pytest.mark.xfail(strict=True,
                       reason='iodp_samples_csv looks for an existing specimens file '
                              'relative to the working directory, not dir_path, so the '
                              'one in dir_path is overwritten')
    def test_keeps_existing_specimens(self, tmp_path):
        """specimens already in dir_path are kept when new ones are added"""
        out = tmp_path / 'out'
        out.mkdir()
        (out / 'specimens.txt').write_text('tab\tspecimens\nspecimen\tsample\nold-spec\told-samp\n')
        convert.iodp_samples_csv('samples_17_5_2019.csv', input_dir_path=U999A_DIR,
                                 dir_path=str(out))
        assert 'old-spec' in read_table(out / 'specimens.txt').specimen.values

    @pytest.mark.xfail(strict=True,
                       reason="samples tables from iodp_samples_csv and iodp_srm_lore set "
                              "result_type twice ('i', then 'g') and never set result_quality")
    @pytest.mark.parametrize('converter', ['samples_csv', 'srm_lore'])
    def test_sample_result_quality(self, converter, lore_out, srm_lore_out):
        """samples are written with result_type 'i' and result_quality 'g'"""
        if converter == 'samples_csv':
            samples = read_table(os.path.join(lore_out[1], 'samples.txt'))
        else:
            samples = read_table(os.path.join(srm_lore_out[1], 'srm_arch_samples.txt'))
        assert (samples.result_type == 'i').all()
        assert (samples.result_quality == 'g').all()


class TestIodpDscrLore:

    def test_discrete_srm_measurements(self, lore_out):
        """
        each row becomes a measurement matched by its LORE test number: the
        drift-corrected direction, the magnetization times 7 cc as moment, and
        in-line AF steps in tesla
        """
        results, out = lore_out
        ran, meas_file = results['dscr']
        assert ran
        assert meas_file == os.path.join(out, 'dscr_measurements.txt')
        raw = pd.read_csv(os.path.join(U999A_DIR, 'SRM_discrete_data', 'srmdiscrete_17_5_2019.csv'))
        meas = read_table(meas_file)
        assert len(meas) == len(raw)
        meas.index = meas.external_database_ids
        for _, row in raw.iterrows():
            rec = meas.loc['LORE[{}]'.format(row['Test No.'])]
            assert rec.specimen == lore_specimen_name(row, 'Offset (cm)')
            assert rec.dir_dec == pytest.approx(row['Declination background & drift corrected (deg)'])
            assert rec.dir_inc == pytest.approx(row['Inclination background & drift corrected (deg)'])
            assert rec.magn_volume == pytest.approx(row['Intensity background & drift corrected (A/m)'])
            assert rec.magn_moment == pytest.approx(
                row['Intensity background & drift corrected (A/m)'] * 7e-6)
            assert rec.treat_ac_field == pytest.approx(row['Treatment Value'] * 1e-3)
            expected_code = 'LT-AF-Z' if row['Treatment Type'] == 'IN-LINE AF DEMAG' else 'LT-NO'
            assert rec.method_codes.split(':')[0] == expected_code

    def test_warns_about_unknown_specimens(self, tmp_path, capsys):
        """a specimen that is not in the specimens table is named in a warning"""
        convert.iodp_samples_csv('samples_17_5_2019.csv', input_dir_path=U999A_DIR,
                                 dir_path=str(tmp_path))
        capsys.readouterr()
        convert.iodp_dscr_lore('srmdiscrete_17_5_2019.csv',
                               input_dir_path=os.path.join(U999A_DIR, 'SRM_discrete_data'),
                               dir_path=str(tmp_path))
        out = capsys.readouterr().out
        assert '999-U999A-1H-2-W-140.0' in out and 'not found in specimens table' in out


class TestIodpJr6Lore:

    def test_spinner_measurements(self, lore_out):
        """
        the sample-coordinate directions rotated with azimuth 0 and plunge -90
        match the geographic directions LIMS gives; AF and ARM steps get their
        method codes and fields in tesla
        """
        results, out = lore_out
        ran, meas_file = results['jr6']
        assert ran
        raw = pd.read_csv(os.path.join(U999A_DIR, 'JR6_data', 'spinner_17_5_2019.csv'))
        meas = read_table(meas_file)
        assert len(meas) == len(raw)
        meas.index = meas.external_database_ids
        for _, row in raw.iterrows():
            rec = meas.loc['LORE[{}]'.format(row['Test No.'])]
            assert rec.specimen == lore_specimen_name(row, 'Top offset (cm)')
            # LIMS rounds both directions to 0.1 degree, so compare the angle
            # between them; near-vertical directions differ more in declination
            assert angle_between(rec.dir_dec, rec.dir_inc,
                                 row['Declination (geographic) (°)'],
                                 row['Inclination (geographic) (°)']) < 0.2
            assert rec.magn_moment == pytest.approx(row['Intensity raw (A/m)'] * 7e-6)
        af_step = meas.loc['LORE[113381431]']     # AD 50 mT
        assert af_step.method_codes.split(':')[0] == 'LT-AF-Z'
        assert af_step.treat_ac_field == pytest.approx(0.05)
        arm_step = meas.loc['LORE[113381321]']    # ARM 100 mT
        assert arm_step.method_codes.split(':')[0] == 'LT-AF-I'
        assert arm_step.treat_ac_field == pytest.approx(0.1)
        assert arm_step.treat_dc_field == pytest.approx(50e-6)


class TestIodpKly4sLore:

    def test_ams_specimens_and_bulk_susceptibility(self, lore_out):
        """
        bulk susceptibility is rescaled from the nominal to the actual volume;
        the normalized tensor becomes aniso_s and the eigenvalues, divided by
        three, and eigenvectors become aniso_v1..v3
        """
        results, out = lore_out
        ran, meas_file = results['kly4s']
        assert ran
        raw = pd.read_csv(os.path.join(U999A_DIR, 'KLY4S_data', 'ex-kappa_17_5_2019.csv'))
        meas = read_table(meas_file)
        specimens = read_table(os.path.join(out, 'kly4s_specimens.txt'))
        assert len(meas) == len(specimens) == len(raw)
        row, rec, spec = raw.iloc[0], meas.iloc[0], specimens.iloc[0]
        name = lore_specimen_name(row, 'Top offset (cm)')
        assert rec.specimen == spec.specimen == name
        assert rec.susc_chi_volume == pytest.approx(
            row['Bulk susceptibility(SI)'] * row['Sample volume (CC)'] / 7)
        assert spec.volume == pytest.approx(7e-6)
        s_cols = ['K11', 'K22', 'K33', 'K12', 'K23', 'K13']
        assert [float(s) for s in spec.aniso_s.split(':')] == pytest.approx(
            [row['Normalized tensor ' + col] for col in s_cols])
        tau1, dec1, inc1 = (float(v) for v in spec.aniso_v1.split(':'))
        assert tau1 == pytest.approx(row['Kmax susceptibility (SI)'] / 3)
        assert (dec1, inc1) == pytest.approx((row['Kmax dec (deg)'], row['Kmax inc (deg)']))
        assert spec.aniso_type == 'AMS'
        assert spec.method_codes == 'LP-X:AE-H:LP-AN-MS'


class TestIodpSrmLore:

    def test_archive_half_measurements(self, srm_lore_out):
        """
        with noave each row is a measurement: drift-corrected direction and
        magnetization, moment from the x, y, z moments, AF steps in tesla, and
        the specimen, sample and site tables written alongside
        """
        (ran, meas_file), out, raw = srm_lore_out
        assert ran
        for fname in ['srm_arch_specimens.txt', 'srm_arch_samples.txt', 'srm_arch_sites.txt']:
            assert os.path.isfile(os.path.join(out, fname))
        meas = read_table(meas_file)
        assert len(meas) == len(raw)
        meas.index = meas.external_database_ids
        for _, row in raw.iterrows():
            rec = meas.loc['LORE[{}]'.format(row['Test No.'])]
            assert rec.specimen == '999-U999A-1H-1-A-0.0'
            assert rec.dir_dec == pytest.approx(row['Declination background & drift corrected (deg)'])
            assert rec.dir_inc == pytest.approx(row['Inclination background & drift corrected (deg)'])
            assert rec.magn_volume == pytest.approx(row['Intensity background & drift corrected (A/m)'])
            assert rec.magn_moment == pytest.approx(np.linalg.norm(
                [row['Magnetic moment x (Am²)'], row['Magnetic moment y (Am²)'],
                 row['Magnetic moment z (Am²)']]))
            assert rec.treat_ac_field == pytest.approx(row['Treatment Value'] * 1e-3)
            expected_code = 'LT-AF-Z' if row['Treatment Type'] == 'IN-LINE AF DEMAG' else 'LT-NO'
            assert rec.method_codes.split(':')[0] == expected_code
        sites = read_table(os.path.join(out, 'srm_arch_sites.txt'))
        assert sites.composite_depth.iloc[0] == pytest.approx(raw['Depth CSF-B (m)'].iloc[0])
        assert sites.lat.iloc[0] == pytest.approx(HOLE_LAT)

    def test_replicates_are_averaged(self, tmp_path):
        """
        by default the two NRM measurements of the position become one record,
        the vector mean of their moments, marked DE-VM
        """
        (ran, meas_file), raw = run_srm_lore(tmp_path, noave=False)
        assert ran
        meas = read_table(meas_file)
        nrm_rows = raw[raw['Treatment Type'] == 'NRM']
        assert len(nrm_rows) == 2
        assert len(meas) == len(raw) - 1
        nrm = meas[meas.method_codes.str.split(':').str[0] == 'LT-NO']
        assert len(nrm) == 1
        assert 'DE-VM' in nrm.method_codes.iloc[0].split(':')
        decs = np.radians(nrm_rows['Declination background & drift corrected (deg)'].values)
        incs = np.radians(nrm_rows['Inclination background & drift corrected (deg)'].values)
        moments = np.linalg.norm(nrm_rows[['Magnetic moment x (Am²)', 'Magnetic moment y (Am²)',
                                           'Magnetic moment z (Am²)']].values, axis=1)
        mean = (moments[:, None] * np.column_stack([np.cos(incs) * np.cos(decs),
                                                    np.cos(incs) * np.sin(decs),
                                                    np.sin(incs)])).mean(axis=0)
        norm = np.linalg.norm(mean)
        assert nrm.dir_dec.iloc[0] == pytest.approx(np.degrees(np.arctan2(mean[1], mean[0])) % 360,
                                                    abs=0.1)
        assert nrm.dir_inc.iloc[0] == pytest.approx(np.degrees(np.arcsin(mean[2] / norm)), abs=0.1)
        assert nrm.magn_moment.iloc[0] == pytest.approx(norm, rel=1e-3)

    @pytest.mark.xfail(strict=True,
                       reason='iodp_srm_lore writes one specimen, sample and site row per '
                              'measurement row, so a position measured several times is '
                              'repeated in those tables')
    def test_one_row_per_specimen(self, srm_lore_out):
        """the specimens, samples and sites tables list each name once"""
        _, out, _ = srm_lore_out
        assert read_table(os.path.join(out, 'srm_arch_specimens.txt')).specimen.is_unique
        assert read_table(os.path.join(out, 'srm_arch_samples.txt'))['sample'].is_unique
        assert read_table(os.path.join(out, 'srm_arch_sites.txt')).site.is_unique


# -------------------------------------------------- shared failure behaviour

@pytest.mark.parametrize('converter', [
    pytest.param('kly4s'),
    pytest.param('dscr', marks=pytest.mark.xfail(
        strict=True, raises=FileNotFoundError,
        reason='iodp_dscr_lore reads the specimens table without checking it exists')),
    pytest.param('jr6', marks=pytest.mark.xfail(
        strict=True, raises=FileNotFoundError,
        reason='iodp_jr6_lore reads the specimens table without checking it exists')),
])
def test_lore_converters_need_a_specimens_table(converter, tmp_path):
    """
    without the specimens table from iodp_samples_csv the LORE measurement
    converters return False rather than raising
    """
    if converter == 'kly4s':
        result = convert.iodp_kly4s_lore('ex-kappa_17_5_2019.csv', dir_path=str(tmp_path),
                                         input_dir_path=os.path.join(U999A_DIR, 'KLY4S_data'))
    elif converter == 'dscr':
        result = convert.iodp_dscr_lore('srmdiscrete_17_5_2019.csv', dir_path=str(tmp_path),
                                        input_dir_path=os.path.join(U999A_DIR, 'SRM_discrete_data'))
    else:
        result = convert.iodp_jr6_lore('spinner_17_5_2019.csv', dir_path=str(tmp_path),
                                       input_dir_path=os.path.join(U999A_DIR, 'JR6_data'))
    assert result[0] is False


# ------------------------------------------------- columns in the data model

def not_in_model(reason):
    """xfail mark for an output file with columns that are not in the data model"""
    return pytest.mark.xfail(strict=True, reason=reason)


@pytest.mark.parametrize('fixture_name, fname', [
    ('srm_janus', 'srm_measurements.txt'),
    ('srm_janus', 'srm_specimens.txt'),
    pytest.param('srm_janus', 'srm_samples.txt', marks=not_in_model(
        'iodp_srm puts core_depth and composite_depth, site columns, in samples')),
    ('srm_janus', 'srm_sites.txt'),
    ('srm_janus', 'srm_locations.txt'),
    ('jr6_out', 'measurements.txt'),
    ('jr6_out', 'specimens.txt'),
    ('jr6_out', 'samples.txt'),
    ('jr6_out', 'sites.txt'),
    ('jr6_out', 'locations.txt'),
    pytest.param('samples_out', 'samples.txt', marks=not_in_model(
        'iodp_samples writes citation, core_depth, expedition_name, location and '
        'sample_volume, none of them samples columns')),
    pytest.param('lore_out', 'specimens.txt', marks=not_in_model(
        'iodp_samples_csv writes specimen_name_alternatives for specimen_alternatives')),
    pytest.param('lore_out', 'samples.txt', marks=not_in_model(
        'iodp_samples_csv writes azimuth_correction for azimuth_dec_correction')),
    ('lore_out', 'sites.txt'),
    ('lore_out', 'locations.txt'),
    ('lore_out', 'dscr_measurements.txt'),
    ('lore_out', 'jr6_measurements.txt'),
    pytest.param('lore_out', 'kly4s_measurements.txt', marks=not_in_model(
        'iodp_kly4s_lore writes experiments, a specimens column, in measurements')),
    pytest.param('lore_out', 'kly4s_specimens.txt', marks=not_in_model(
        'iodp_kly4s_lore writes specimen_name_alternatives for specimen_alternatives')),
    ('srm_lore_out', 'srm_arch_measurements.txt'),
    pytest.param('srm_lore_out', 'srm_arch_specimens.txt', marks=not_in_model(
        'iodp_srm_lore writes specimen_name_alternatives for specimen_alternatives')),
    pytest.param('srm_lore_out', 'srm_arch_samples.txt', marks=not_in_model(
        'iodp_srm_lore puts core_depth and composite_depth (sites columns) in samples, and '
        'azimuth_correction for azimuth_dec_correction')),
    ('srm_lore_out', 'srm_arch_sites.txt'),
])
def test_output_columns_are_in_the_data_model(fixture_name, fname, request):
    """every column a converter writes is a column of that table in MagIC 3"""
    out = request.getfixturevalue(fixture_name)[1]
    path = os.path.join(out, fname)
    columns = model_columns(table_type(path))
    unknown = [col for col in read_table(path).columns if col not in columns]
    assert unknown == []
