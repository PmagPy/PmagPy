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
into data_files.
"""
import os
import subprocess
import sys

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
# AF demagnetization sequences, in January and in March, so its NRM appears twice
ONE_POSITION = '"999","U999","A","1","H","1","A","0.0",'
# a position (core 1H, section 3, offset 0 cm) with steps repeated one after
# the other: 15 mT twice and 10 mT three times
REPEATS_POSITION = '"999","U999","A","1","H","3","A","0.0",'


def run_srm_lore(out_dir, noave, position=ONE_POSITION):
    """
    Run iodp_srm_lore on the rows of one position.

    Args:
        out_dir (pathlib.Path): directory for the input subset and the output
        noave (bool): True to keep replicate measurements separate
        position (str): start of the lines of the position

    Returns:
        tuple: the converter's return value, and the raw rows as a DataFrame
    """
    subset = write_subset(SRM_ARCHIVE, str(out_dir / 'srm.csv'),
                          lambda line: line.startswith(position))
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
            assert rec.external_database_ids == 'LIMS[{}]'.format(row['Test No.'])
        specimens = read_table(os.path.join(out, names['spec_file']))
        samples = read_table(os.path.join(out, names['samp_file']))
        locations = read_table(os.path.join(out, names['loc_file']))
        assert set(meas.specimen) == set(specimens.specimen)
        assert specimens.volume.values == pytest.approx(15.59e-6)  # m^3
        assert len(samples) == raw[['Core', 'Type']].drop_duplicates().shape[0]
        sites = read_table(os.path.join(out, names['site_file']))
        assert list(sites.site) == ['312-U1256D']
        assert sites.core_depth[0] == pytest.approx(float(raw['Depth CSF-A (m)'].iloc[0]))
        assert sites.composite_depth[0] == pytest.approx(float(raw['Depth CSF-B (m)'].iloc[0]))
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

    def test_degree_sign_headers(self, tmp_path):
        """
        a LIMS export with (°) in the direction headers converts; rows
        without a direction are skipped
        """
        write_subset(os.path.join(SRM_DIR, 'SRM_318_U1359_B_A.csv'), str(tmp_path / 'srm.csv'),
                     lambda line: line.startswith('318-U1359B-3H-2-A,'))
        ran, meas_file = convert.iodp_srm(csv_file='srm.csv', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(tmp_path / 'srm.csv', dtype=str)
        dec_key = 'Declination background + tray corrected (°)'
        inc_key = 'Inclination background + tray corrected  (°)'
        with_direction = raw.dropna(subset=[dec_key, inc_key])
        meas = read_table(os.path.join(tmp_path, meas_file))
        assert len(meas) == len(with_direction)
        meas.index = meas.specimen
        for _, row in with_direction.iterrows():
            rec = meas.loc['318-U1359B-003H_2A-' + row[' Interval Bot (cm) on SECT']]
            assert rec.dir_dec == pytest.approx(float(row[dec_key]))
            assert rec.dir_inc == pytest.approx(float(row[inc_key]))

    @pytest.mark.parametrize('treatment', ['Alternating Frequency Demagnetization',
                                           'Thermal Demagnetization'])
    def test_lims_discrete_steps(self, tmp_path, treatment):
        """
        a LIMS discrete export whose levels are in 'Treatment type' and
        'Treatment Value (mT or °C)' (its demag level is 0) gives one record
        per step: offline AF steps in tesla, thermal steps in kelvin (the
        thermal case relabels the AF steps and adds 100 to their levels)
        """
        position = '"344","U1414","A","1","H","2","","37.0",'
        write_subset(os.path.join(SRM_DIR, 'IODP_LIMS_SRMdiscrete_344_1414A.csv'),
                     str(tmp_path / 'srm.csv'), lambda line: line.startswith(position))
        if treatment.startswith('Thermal'):
            subset = pd.read_csv(tmp_path / 'srm.csv', dtype=str, keep_default_na=False)
            stepped = subset['Treatment type'] != ''
            subset.loc[stepped, 'Treatment type'] = treatment
            subset.loc[stepped, 'Treatment Value (mT or °C)'] = [
                str(float(value) + 100) for value in subset.loc[stepped, 'Treatment Value (mT or °C)']]
            subset.drop(columns=['Unnamed: 32']).to_csv(tmp_path / 'srm.csv', index=False)
        ran, meas_file = convert.iodp_srm(csv_file='srm.csv', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(tmp_path / 'srm.csv')
        meas = read_table(os.path.join(tmp_path, meas_file)).fillna(0)
        assert len(raw) == 12
        assert len(meas) == len(raw)
        assert not meas.method_codes.str.contains('DE-VM').any()
        for (_, rec), (_, row) in zip(meas.iterrows(), raw.iterrows()):
            assert rec.dir_dec == pytest.approx(row['Declination background & tray corrected (deg)'])
            code = rec.method_codes.split(':')[0]
            if pd.isna(row['Treatment type']):
                assert code == 'LT-NO'
            elif treatment.startswith('Alternating'):
                assert code == 'LT-AF-Z'
                assert rec.treat_ac_field == pytest.approx(row['Treatment Value (mT or °C)'] * 1e-3)
                assert rec.instrument_codes == 'IODP-SRM:IODP-DTECH'
            else:
                assert code == 'LT-T-Z'
                assert rec.treat_temp == pytest.approx(row['Treatment Value (mT or °C)'] + 273)

    @pytest.mark.parametrize('label', ['Declination background + tray corrected (°)',
                                       'Declination background + tray corrected (Â°)',
                                       'Declination background + tray corrected (deg)'])
    def test_header_label(self, label):
        """the degree sign, also as read with the wrong encoding, is spelled deg"""
        assert convert.iodp_header_label(label) == 'Declination background + tray corrected (deg)'

    def test_missing_column(self, tmp_path):
        """a file without a declination column returns False rather than raising"""
        raw = pd.read_csv(os.path.join(SRM_DIR, 'IODP_Janus_312_U1256.csv'), nrows=5)
        raw.drop(columns=['Declination background & tray corrected (deg)']).to_csv(
            tmp_path / 'srm.csv', index=False)
        ran, message = convert.iodp_srm(csv_file='srm.csv', input_dir_path=str(tmp_path),
                                        dir_path=str(tmp_path))
        assert ran is False
        assert 'declination' in message


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
        characters; a specimen of the same name with the volume converted from
        cc to m^3, and a site with the depth in the hole as location
        """
        (ran, samp_file), out = samples_out
        assert ran
        assert samp_file == os.path.join(str(out), 'samples.txt')
        raw = pd.read_csv(os.path.join(SRM_DIR, 'samples_318_U1359_B.csv'), dtype=str)
        with_interval = raw[raw['Label Id'].str.split().str.len() > 1]
        samples = read_table(samp_file)
        specimens = read_table(os.path.join(out, 'specimens.txt'))
        sites = read_table(os.path.join(out, 'sites.txt'))
        locations = read_table(os.path.join(out, 'locations.txt'))
        assert len(samples) == len(specimens) == len(sites) == len(with_interval)
        row = with_interval.iloc[0]   # 318-U1359B-2H-1-W 40/42-Tauxe
        rec = samples.iloc[0]
        assert rec['sample'] == '318-U1359B-002H-1-W-40'
        assert rec.site == rec['sample']
        assert rec.sample_alternatives == row['Text Id']
        assert rec.method_codes == 'FS-C-DRILL-IODP:SP-SS-C:SO-V'
        assert rec.citations == 'This study'
        spec = specimens.iloc[0]
        assert spec.specimen == spec['sample'] == rec['sample']
        assert spec.volume == pytest.approx(float(row['Volume (cc)']) * 1e-6)
        site = sites.iloc[0]
        assert site.site == rec['sample']
        assert site.core_depth == pytest.approx(float(row['Top Depth (m)']))
        assert site.location == 'U1359B'
        assert list(locations.location) == ['U1359B']
        assert locations.expedition_name[0] == 318

    def test_keeps_other_records(self, tmp_path):
        """
        records already in the specimens, sites and locations tables are kept,
        and the samples go into output_samp_file in the output directory
        """
        (tmp_path / 'specimens.txt').write_text('tab\tspecimens\nspecimen\tsample\nold-spec\told-samp\n')
        (tmp_path / 'sites.txt').write_text('tab\tsites\nsite\tlocation\nold-site\told-loc\n')
        ran, samp_file = convert.iodp_samples('samples_318_U1359_B.csv', input_dir_path=SRM_DIR,
                                              output_dir_path=str(tmp_path),
                                              output_samp_file='lims_samples.txt')
        assert ran
        assert samp_file == os.path.join(str(tmp_path), 'lims_samples.txt')
        assert '318-U1359B-002H-1-W-40' in read_table(samp_file)['sample'].values
        specimens = read_table(tmp_path / 'specimens.txt')
        assert {'old-spec', '318-U1359B-002H-1-W-40'} <= set(specimens.specimen)
        sites = read_table(tmp_path / 'sites.txt')
        assert {'old-site', '318-U1359B-002H-1-W-40'} <= set(sites.site)

    def test_quoted_headers(self, tmp_path):
        """the composite depth of a LORE export with quoted headers reaches the sites"""
        ran, _ = convert.iodp_samples('samples_17_5_2019.csv', input_dir_path=U999A_DIR,
                                      output_dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(os.path.join(U999A_DIR, 'samples_17_5_2019.csv'))
        sites = read_table(tmp_path / 'sites.txt')
        assert len(sites) == len(raw)
        assert sites.composite_depth.values == pytest.approx(raw['Top depth CSF-B (m)'].values)


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

    def test_keeps_existing_specimens(self, tmp_path):
        """specimens already in dir_path are kept when new ones are added"""
        out = tmp_path / 'out'
        out.mkdir()
        (out / 'specimens.txt').write_text('tab\tspecimens\nspecimen\tsample\nold-spec\told-samp\n')
        convert.iodp_samples_csv('samples_17_5_2019.csv', input_dir_path=U999A_DIR,
                                 dir_path=str(out))
        specimens = read_table(out / 'specimens.txt').specimen.values
        assert 'old-spec' in specimens
        assert '999-U999A-1H-1-W-10.0' in specimens

    def test_location_of_each_hole(self, tmp_path):
        """the sites of a file with two holes are in the location of their own hole"""
        raw = pd.read_csv(os.path.join(U999A_DIR, 'samples_17_5_2019.csv'))
        raw.loc[raw['Sect'] == 1, 'Hole'] = 'B'
        raw.to_csv(tmp_path / 'two_holes.csv', index=False)
        ran, _ = convert.iodp_samples_csv('two_holes.csv', input_dir_path=str(tmp_path),
                                          dir_path=str(tmp_path))
        assert ran
        sites = read_table(tmp_path / 'sites.txt')
        assert set(sites.location) == {'U999A', 'U999B'}
        for _, site in sites.iterrows():
            assert site.site.split('-')[1] == site.location
        assert set(read_table(tmp_path / 'locations.txt').location) == {'U999A', 'U999B'}

    def test_2015_layout(self, tmp_path):
        """
        a LIMS sample export of about 2015 (Text identifier, Volume (cc))
        converts, with the volume in m^3
        """
        ran, _ = convert.iodp_samples_csv('samples-XXX-UTEST-A.csv',
                                          input_dir_path=os.path.join(WD, 'data_files', 'UTESTA'),
                                          dir_path=str(tmp_path))
        assert ran
        raw = pd.read_csv(os.path.join(WD, 'data_files', 'UTESTA', 'samples-XXX-UTEST-A.csv'))
        specimens = read_table(tmp_path / 'specimens.txt')
        assert list(specimens.specimen) == [lore_specimen_name(row, 'Top offset (cm)')
                                            for _, row in raw.iterrows()]
        assert list(specimens.specimen_alternatives) == list(raw['Text identifier'])
        assert specimens.volume.values == pytest.approx(raw['Volume (cc)'].values * 1e-6)

    def test_older_layout(self, tmp_path):
        """
        a LIMS sample export of 2010 (Label Id, Section, ...) returns False
        and points to iodp_samples
        """
        ran, message = convert.iodp_samples_csv('samples_318_U1359_B.csv', input_dir_path=SRM_DIR,
                                                dir_path=str(tmp_path))
        assert ran is False
        assert 'iodp_samples' in message

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

    def test_order_of_measurement(self, lore_out):
        """
        the steps of each specimen follow the timestamps, which here differ
        from the order of the test numbers (70 mT and 75 mT of 1H-1-W-26.0)
        """
        results, out = lore_out
        meas = read_table(results['dscr'][1])
        raw = pd.read_csv(os.path.join(U999A_DIR, 'SRM_discrete_data', 'srmdiscrete_17_5_2019.csv'))
        for specimen, recs in meas.groupby('specimen', sort=False):
            assert list(recs.treat_ac_field) == sorted(recs.treat_ac_field), specimen
            assert list(recs.sequence) == sorted(recs.sequence), specimen
        cube = raw[raw['Offset (cm)'] == 26.0].set_index('Treatment Value')
        assert cube.loc[75, 'Test No.'] < cube.loc[70, 'Test No.']

    def test_older_layout(self, tmp_path):
        """an older LIMS discrete export returns False and points to iodp_srm"""
        convert.iodp_samples_csv('samples_17_5_2019.csv', input_dir_path=U999A_DIR,
                                 dir_path=str(tmp_path))
        ran, message = convert.iodp_dscr_lore('IODP_LIMS_SRMdiscrete_344_1414A.csv',
                                              input_dir_path=SRM_DIR, dir_path=str(tmp_path))
        assert ran is False
        assert 'iodp_srm' in message
        assert not os.path.exists(tmp_path / 'measurements.txt')

    def test_command_line_failure(self, tmp_path):
        """iodp_dscr_magic.py prints the message and exits with status 1 on failure"""
        script = os.path.join(WD, 'programs', 'conversion_scripts', 'iodp_dscr_magic.py')
        result = subprocess.run([sys.executable, script, '-f', 'srmdiscrete_17_5_2019.csv',
                                 '-ID', os.path.join(U999A_DIR, 'SRM_discrete_data'),
                                 '-WD', str(tmp_path)],
                                capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=WD))
        assert result.returncode == 1, result.stdout + result.stderr
        assert 'samples table' in result.stdout

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

    def test_older_layout(self, tmp_path):
        """
        an older LIMS section export returns False, points to iodp_srm and
        writes nothing
        """
        write_subset(os.path.join(UTESTA_SRM_DIR, 'srmsection-XXX-UTEST-A.csv'),
                     str(tmp_path / 'section.csv'), lambda line: line.startswith('XXX,UTEST,A,1,H,1,'))
        out = tmp_path / 'out'
        out.mkdir()
        ran, message = convert.iodp_srm_lore('section.csv', input_dir_path=str(tmp_path),
                                             dir_path=str(out))
        assert ran is False
        assert 'iodp_srm' in message
        assert os.listdir(out) == []

    def test_runs_are_kept_apart(self, tmp_path):
        """
        by default the two NRMs of the position, measured two months apart
        with AF steps in between, stay two records in the order of measurement
        """
        (ran, meas_file), raw = run_srm_lore(tmp_path, noave=False)
        assert ran
        meas = read_table(meas_file)
        assert len(meas) == len(raw)
        assert not meas.method_codes.str.contains('DE-VM').any()
        nrm_rows = raw[raw['Treatment Type'] == 'NRM'].sort_values('Timestamp (UTC)')
        assert len(nrm_rows) == 2
        nrm = meas[meas.method_codes.str.split(':').str[0] == 'LT-NO']
        assert list(nrm.dir_dec) == pytest.approx(
            list(nrm_rows['Declination background & drift corrected (deg)']))
        assert list(nrm.dir_inc) == pytest.approx(
            list(nrm_rows['Inclination background & drift corrected (deg)']))

    def test_replicates_are_averaged(self, tmp_path):
        """
        by default measurements of the same step one after the other become one
        record, the vector mean of their moments, marked DE-VM
        """
        (ran, meas_file), raw = run_srm_lore(tmp_path, noave=False, position=REPEATS_POSITION)
        assert ran
        meas = read_table(meas_file)
        raw = raw.sort_values('Timestamp (UTC)')
        # consecutive measurements at the same step
        groups = [group for _, group in raw.groupby(
            (raw['Treatment Value'] != raw['Treatment Value'].shift()).cumsum())]
        assert sorted(len(group) for group in groups if len(group) > 1) == [2, 3]
        assert len(meas) == len(groups)
        for (_, rec), group in zip(meas.iterrows(), groups):
            assert rec.treat_ac_field == pytest.approx(group['Treatment Value'].iloc[0] * 1e-3)
            decs = np.radians(group['Declination background & drift corrected (deg)'].values)
            incs = np.radians(group['Inclination background & drift corrected (deg)'].values)
            moments = np.linalg.norm(group[['Magnetic moment x (Am²)', 'Magnetic moment y (Am²)',
                                            'Magnetic moment z (Am²)']].values, axis=1)
            mean = (moments[:, None] * np.column_stack([np.cos(incs) * np.cos(decs),
                                                        np.cos(incs) * np.sin(decs),
                                                        np.sin(incs)])).mean(axis=0)
            norm = np.linalg.norm(mean)
            assert ('DE-VM' in rec.method_codes.split(':')) == (len(group) > 1)
            assert rec.dir_dec == pytest.approx(np.degrees(np.arctan2(mean[1], mean[0])) % 360,
                                                abs=0.1)
            assert rec.dir_inc == pytest.approx(np.degrees(np.arcsin(mean[2] / norm)), abs=0.1)
            assert rec.magn_moment == pytest.approx(norm, rel=1e-3)

    def test_one_row_per_specimen(self, srm_lore_out):
        """the specimens, samples and sites tables list each name once"""
        _, out, _ = srm_lore_out
        assert read_table(os.path.join(out, 'srm_arch_specimens.txt')).specimen.is_unique
        assert read_table(os.path.join(out, 'srm_arch_samples.txt'))['sample'].is_unique
        assert read_table(os.path.join(out, 'srm_arch_sites.txt')).site.is_unique

    def test_specimen_volume_and_text_id(self, srm_lore_out):
        """
        the specimen gets the Text ID of its section half and, as volume, the
        raw moment over the raw intensity that LIMS used
        """
        _, out, raw = srm_lore_out
        spec = read_table(os.path.join(out, 'srm_arch_specimens.txt')).iloc[0]
        assert spec.specimen_alternatives == raw['Text ID'].iloc[0]
        raw_moment = np.linalg.norm(raw[['Magnetic moment x (Am²)', 'Magnetic moment y (Am²)',
                                         'Magnetic moment z (Am²)']].values, axis=1)
        assert spec.volume == pytest.approx(np.median(raw_moment / raw['Intensity raw (A/m)']))


# -------------------------------------------------- shared failure behaviour

@pytest.mark.parametrize('converter', ['kly4s', 'dscr', 'jr6'])
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


@pytest.mark.parametrize('converter', [convert.iodp_samples_csv, convert.iodp_srm_lore,
                                       convert.iodp_dscr_lore, convert.iodp_jr6_lore])
def test_missing_input_file(converter, tmp_path):
    """a missing input file returns False and a message rather than raising"""
    ran, message = converter('missing.csv', input_dir_path=str(tmp_path), dir_path=str(tmp_path))
    assert ran is False
    assert 'missing.csv' in message
    assert os.listdir(tmp_path) == []


# ------------------------------------------------- columns in the data model

@pytest.mark.parametrize('fixture_name, fname', [
    ('srm_janus', 'srm_measurements.txt'),
    ('srm_janus', 'srm_specimens.txt'),
    ('srm_janus', 'srm_samples.txt'),
    ('srm_janus', 'srm_sites.txt'),
    ('srm_janus', 'srm_locations.txt'),
    ('jr6_out', 'measurements.txt'),
    ('jr6_out', 'specimens.txt'),
    ('jr6_out', 'samples.txt'),
    ('jr6_out', 'sites.txt'),
    ('jr6_out', 'locations.txt'),
    ('samples_out', 'samples.txt'),
    ('samples_out', 'specimens.txt'),
    ('samples_out', 'sites.txt'),
    ('samples_out', 'locations.txt'),
    ('lore_out', 'specimens.txt'),
    ('lore_out', 'samples.txt'),
    ('lore_out', 'sites.txt'),
    ('lore_out', 'locations.txt'),
    ('lore_out', 'dscr_measurements.txt'),
    ('lore_out', 'jr6_measurements.txt'),
    ('lore_out', 'kly4s_measurements.txt'),
    ('lore_out', 'kly4s_specimens.txt'),
    ('srm_lore_out', 'srm_arch_measurements.txt'),
    ('srm_lore_out', 'srm_arch_specimens.txt'),
    ('srm_lore_out', 'srm_arch_samples.txt'),
    ('srm_lore_out', 'srm_arch_sites.txt'),
])
def test_output_columns_are_in_the_data_model(fixture_name, fname, request):
    """every column a converter writes is a column of that table in MagIC 3"""
    out = request.getfixturevalue(fixture_name)[1]
    path = os.path.join(out, fname)
    columns = model_columns(table_type(path))
    unknown = [col for col in read_table(path).columns if col not in columns]
    assert unknown == []
