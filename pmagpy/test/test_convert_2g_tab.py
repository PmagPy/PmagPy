"""
Tests for convert._2g_tab, the converter of the tab-delimited exports (.DAT)
of the 2G Enterprises magnetometer software. The real files are from Han et
al. (2022), in data_files/convert_2_magic/2g_tab_magic/han2022 (see its
README); they hold thermal steps in specimen coordinates only. The column
selection of other laboratories (alternating field steps in Oe, a volume,
the sample orientation and bedding with the rotated directions, susceptibility
rows) is tested with files written by the tests from known values.
"""
import contextlib
import io
import math
import os

import numpy as np
import pandas as pd
import pytest

from pmagpy import pmag
from pmagpy import convert_2_magic as convert
from pmagpy.test.convert_helpers import CONVERT_DIR, read_table

HAN = os.path.join(CONVERT_DIR, '2g_tab_magic', 'han2022')


def run(tmp_path, mag_file, input_dir_path=HAN, **kwargs):
    """
    Convert from an empty working directory into tmp_path/out.

    Returns:
        tuple: (ok, message, what was printed, output directory)
    """
    out_dir = os.path.join(str(tmp_path), 'out')
    cwd = os.path.join(str(tmp_path), 'cwd')
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(cwd, exist_ok=True)
    start = os.getcwd()
    printed = io.StringIO()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(printed):
            ok, message = convert._2g_tab(mag_file=mag_file, dir_path=out_dir,
                                          input_dir_path=input_dir_path, **kwargs)
    finally:
        os.chdir(start)
    assert os.listdir(cwd) == []
    return ok, message, printed.getvalue(), out_dir


def raw_rows(path):
    """the rows of a 2G export with as many fields as the header, as dicts"""
    with open(path, 'rb') as f:
        lines = [line for line in f.read().decode('latin-1').splitlines() if line.strip()]
    head = lines[0].split('\t')
    return [dict(zip(head, line.split('\t'))) for line in lines[1:] if len(line.split('\t')) == len(head)]


def write_export(path, columns, rows):
    """write a 2G tab-delimited export with the given columns and rows (lists of strings)"""
    with open(path, 'w', newline='') as f:
        f.write('\t'.join(columns) + '\r\n')
        for row in rows:
            f.write('\t'.join(row) + '\r\n')


# --- the Han et al. (2022) files

def test_units_directions_and_method_codes(tmp_path):
    ok, message, printed, out = run(tmp_path, 'SYJLC3-29.DAT')
    assert ok, message
    meas = read_table(os.path.join(out, 'measurements.txt'))
    raw = raw_rows(os.path.join(HAN, 'SYJLC3-29.DAT'))
    # 25 rows, one of which holds two steps on one line and is left out
    assert len(raw) == 24 and len(meas) == 24
    assert list(meas.specimen.unique()) == ['SYJLC3-29']
    for (_, m), r in zip(meas.iterrows(), raw):
        corr = [float(r[axis + ' corr']) for axis in 'XYZ']
        # the moment of the components, emu to Am^2
        assert m.magn_moment == pytest.approx(math.sqrt(sum(c ** 2 for c in corr)) * 1e-3, rel=1e-4)
        # without a volume the Intensity column is that moment, in emu
        assert m.magn_moment == pytest.approx(float(r['Intensity']) * 1e-3, rel=1e-3)
        # directions in specimen coordinates, as in the file and as given by the components
        assert m.dir_dec == pytest.approx(float(r['Declination: Unrotated']))
        assert m.dir_inc == pytest.approx(float(r['Inclination: Unrotated']))
        assert pmag.angle([m.dir_dec, m.dir_inc], pmag.cart2dir(corr)[:2])[0] < 0.01
        temp = float(r['Temp C'])
        if temp == 25:  # the room temperature of the NRM rows
            assert m.method_codes == 'LT-NO:LP-DIR-T'
            assert m.treat_temp == 273
        else:
            assert m.method_codes == 'LT-T-Z:LP-DIR-T'
            assert m.treat_temp == pytest.approx(temp + 273)
        assert m.treat_ac_field == 0
    assert (meas.method_codes == 'LT-NO:LP-DIR-T').sum() == 2
    # the two steps on line 17 are left out, with a warning
    assert 'line 17 has 23 fields, not 12 as the header (two rows on one line?)' in printed
    assert not set(meas.treat_temp.round()) & {585 + 273, 600 + 273}
    # repeated steps are kept (noave=True): three rows at 80 C
    assert (meas.treat_temp.round() == 353).sum() == 3
    assert list(meas.treat_step_num) == list(range(1, 25))
    # no volume, so no magn_volume
    assert 'magn_volume' not in meas.columns or meas.magn_volume.isnull().all()
    spec = read_table(os.path.join(out, 'specimens.txt'))
    assert list(spec.method_codes) == ['LP-DIR-T']
    assert 'volume' not in spec.columns or spec.volume.isnull().all()
    # the files hold no orientation: the sample has none
    samp = read_table(os.path.join(out, 'samples.txt'))
    assert samp.loc[0, 'sample'] == 'SYJLC3-29' and samp.loc[0, 'site'] == 'SYJLC3'
    assert 'azimuth' not in samp.columns or samp.azimuth.isnull().all()
    assert samp.loc[0, 'method_codes'] == 'SO-NO'


def test_interrupted_measurement(tmp_path):
    ok, message, printed, out = run(tmp_path, 'SYTJG5-205.DAT')
    assert ok, message
    assert 'line 4 has 9 fields, not 12 as the header (an interrupted measurement?)' in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    # the step is kept once, from the row that repeats it
    at_150 = meas[meas.treat_temp.round() == 150 + 273]
    assert len(at_150) == 1
    assert at_150.dir_dec.iloc[0] == pytest.approx(302.42)


def test_names_differing_in_case(tmp_path):
    ok, message, printed, out = run(tmp_path, 'SYJLCK-4.DAT')
    assert ok, message
    assert 'the names SYJLCK-4, SYJLCk-4 differ only in case and are read as one specimen, SYJLCk-4' in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert list(meas.specimen.unique()) == ['SYJLCk-4']
    assert len(meas) == 24


def test_specimen_in_two_files_and_row_without_temperature(tmp_path):
    files = ['SYTJG5-179.DAT', 'SYTJG5-179 .DAT']
    ok, message, printed, out = run(tmp_path, files)
    assert ok, message
    assert 'specimen SYTJG5-179 is in 2 files (SYTJG5-179.DAT, SYTJG5-179 .DAT)' in printed
    # the row with Temp C NA between 350 and 400 C is not taken for an NRM
    assert 'SYTJG5-179.DAT: 1 row(s) with no treatment value (no temperature or field) left out' in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert list(meas.specimen.unique()) == ['SYTJG5-179']  # without the trailing space
    temps = list((meas.treat_temp - 273).round())
    # the rows of the files in the order given: the first file to 400 C, the second from its NRM
    assert temps[:9] == [0, 80, 150, 200, 250, 300, 350, 400, 0]
    assert temps[9] == 450 and temps[-1] == 690
    assert len(meas) == 8 + 16
    assert (meas.method_codes == 'LT-NO:LP-DIR-T').sum() == 2
    assert list(meas.treat_step_num) == list(range(1, 25))


def test_components_that_disagree_with_the_directions(tmp_path):
    ok, message, printed, out = run(tmp_path, 'SYDBG4G-2-1.DAT')
    assert ok, message
    assert 'SYDBG4g-2-1: 1 row(s) have a direction more than 0.5 degrees from that of their X/Y/Z corr' in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    row = meas[meas.treat_temp.round() == 620 + 273].iloc[0]
    # the direction is the one in the file; the description says how far the components are from it
    assert row.dir_dec == pytest.approx(231.88) and row.dir_inc == pytest.approx(-71.02)
    assert 'the direction of the X/Y/Z corr components is 26.05 degrees' in row.description
    assert 'times that of the Intensity column' in row.description
    others = meas[meas.treat_temp.round() != 620 + 273]
    assert 'description' not in meas.columns or others.description.isnull().all()


def test_average_repeats(tmp_path):
    ok, message, printed, out = run(tmp_path, 'SYJLC3-29.DAT', noave=False)
    assert ok, message
    meas = read_table(os.path.join(out, 'measurements.txt'))
    # two NRM rows and three rows at 80 C are each averaged
    assert len(meas) == 24 - 1 - 2
    raw = raw_rows(os.path.join(HAN, 'SYJLC3-29.DAT'))
    at_80 = [r for r in raw if r['Temp C'] == '80.00']
    mean = np.mean([[float(r[axis + ' corr']) for axis in 'XYZ'] for r in at_80], axis=0)
    dec, inc, moment = pmag.cart2dir(mean)
    row = meas[meas.treat_temp.round() == 353].iloc[0]
    assert row.method_codes == 'LT-T-Z:LP-DIR-T:DE-VM'
    assert row.description == 'mean of 3 measurements'
    assert pmag.angle([row.dir_dec, row.dir_inc], [dec, inc])[0] < 0.02
    assert row.magn_moment == pytest.approx(moment * 1e-3, rel=1e-3)


def test_naming_and_all_files_of_a_folder(tmp_path):
    ok, message, printed, out = run(tmp_path, '', samp_con='2', specnum=0)
    assert ok, message
    spec = read_table(os.path.join(out, 'specimens.txt'))
    assert sorted(spec.specimen) == ['SYDBG4g-2-1', 'SYJLC3-29', 'SYJLCk-4', 'SYTJG5-179', 'SYTJG5-205']
    sites = read_table(os.path.join(out, 'sites.txt'))
    assert sorted(sites.site) == ['SYDBG4g', 'SYJLC3', 'SYJLCk', 'SYTJG5']
    # specnum: the last character of the specimen name designates the specimen
    ok, message, printed, out = run(tmp_path, 'SYJLC3-29.DAT', specnum=1)
    samp = read_table(os.path.join(out, 'samples.txt'))
    assert list(samp['sample']) == ['SYJLC3-2']


def test_not_a_tab_export(tmp_path):
    binary = os.path.join(CONVERT_DIR, '2g_bin_magic', 'mn1', 'mn001-1a.dat')
    ok, message, printed, out = run(tmp_path, binary)
    assert not ok
    assert 'not a 2G tab-delimited export' in message


# --- other column selections, written from known values

COLUMNS = ['Sample ID', 'Treatment Type', 'AF Z', 'Temp C', 'Intensity',
           'Declination: Sample Rotated', 'Inclination: Sample Rotated',
           'Declination: Formation Rotated', 'Inclination: Formation Rotated',
           'Declination: Unrotated', 'Inclination: Unrotated',
           'Sample Azimiuth', 'Sample Dip', 'Formation Dip Azimuth', 'Formation Dip', 'Mag Dev',
           'Volume', 'X corr', 'Y corr', 'Z corr', 'MS corr', 'X corr']


def oriented_rows(azimuth=142., sample_dip=30., bed_dip_direction=45., bed_dip=20., volume=10.,
                  treatment='Degauss X, Y, & Z', convention_dip=None):
    """
    Rows of an export with alternating field steps (Oe), a volume, the sample
    orientation and bedding, and a susceptibility row after each step. The
    rotated directions are calculated with MagIC dip = Sample Dip - 90, or
    with convention_dip if given.
    """
    dip = sample_dip - 90. if convention_dip is None else convention_dip
    rows = []
    steps = [(0, 300., 40., 2e-5), (50, 305., 35., 1.5e-5), (100, 310., 30., 1e-5), (200, 320., 20., 4e-6)]
    for field, dec, inc, moment in steps:
        x, y, z = pmag.dir2cart([dec, inc, moment])
        geo = pmag.dogeo(dec, inc, azimuth, dip)
        tilt = pmag.dotilt(geo[0], geo[1], bed_dip_direction, bed_dip)
        corr = ['%.4E' % x, '%.4E' % y, '%.4E' % z]
        rows.append(['SC01', treatment if field else 'None', str(field), 'NA', '%.4E' % (moment / volume),
                     '%.2f' % geo[0], '%.2f' % geo[1], '%.2f' % tilt[0], '%.2f' % tilt[1],
                     '%.2f' % dec, '%.2f' % inc, '%.2f' % azimuth, '%.2f' % sample_dip,
                     '%.2f' % bed_dip_direction, '%.2f' % bed_dip, '0.00', '%.2f' % volume]
                    + corr + ['NA', corr[0]])
        rows.append(['SC01', 'None', '0', 'NA', 'NA'] + ['NA'] * 6 + ['NA'] * 4 + ['0.00', '%.2f' % volume]
                    + ['NA'] * 3 + ['1.2E+1', 'NA'])
    return rows


def test_alternating_field_volume_and_orientation(tmp_path):
    path = os.path.join(str(tmp_path), 'oriented.DAT')
    write_export(path, COLUMNS, oriented_rows())
    ok, message, printed, out = run(tmp_path, path, input_dir_path='')
    assert ok, message
    # susceptibility rows are counted, not converted
    assert 'oriented.DAT: 4 row(s) without a direction (e.g. susceptibility) left out' in printed
    # the orientation reproduces the rotated directions: no warning about them
    assert 'Rotated columns' not in printed and 'repeated' not in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert len(meas) == 4
    assert list(meas.method_codes) == ['LT-NO:LP-DIR-AF'] + ['LT-AF-Z:LP-DIR-AF'] * 3
    # Oe to tesla: 50 Oe is 5 mT
    assert list(meas.treat_ac_field) == pytest.approx([0, 0.005, 0.01, 0.02])
    assert (meas.treat_temp == 273).all()
    # emu to Am^2, and A/m with the volume of 10 cm^3
    assert list(meas.magn_moment) == pytest.approx([2e-8, 1.5e-8, 1e-8, 4e-9], rel=1e-3)
    assert list(meas.magn_volume) == pytest.approx([2e-3, 1.5e-3, 1e-3, 4e-4], rel=1e-3)
    spec = read_table(os.path.join(out, 'specimens.txt'))
    assert spec.volume[0] == pytest.approx(1e-5)
    samp = read_table(os.path.join(out, 'samples.txt')).iloc[0]
    assert samp.azimuth == pytest.approx(142) and samp.dip == pytest.approx(-60)
    assert samp.bed_dip_direction == pytest.approx(45) and samp.bed_dip == pytest.approx(20)
    # the stored rotated directions follow from the converted orientation
    raw = [r for r in raw_rows(path) if r['Declination: Unrotated'] != 'NA']
    for (_, m), r in zip(meas.iterrows(), raw):
        geo = pmag.dogeo(m.dir_dec, m.dir_inc, samp.azimuth, samp.dip)
        assert pmag.angle(geo, [float(r['Declination: Sample Rotated']),
                                float(r['Inclination: Sample Rotated'])])[0] < 0.05
        tilt = pmag.dotilt(geo[0], geo[1], samp.bed_dip_direction, samp.bed_dip)
        assert pmag.angle(tilt, [float(r['Declination: Formation Rotated']),
                                 float(r['Inclination: Formation Rotated'])])[0] < 0.05


def test_orientation_that_does_not_reproduce_the_rotated_directions(tmp_path):
    # rotated directions calculated with another dip convention: reported
    path = os.path.join(str(tmp_path), 'other_convention.DAT')
    write_export(path, COLUMNS, oriented_rows(convention_dip=30.))
    ok, message, printed, out = run(tmp_path, path, input_dir_path='')
    assert ok, message
    assert 'SC01: the geographic directions calculated from the sample orientation differ from the ' \
           'Sample Rotated columns' in printed


def test_default_orientation_and_thermal_treatment(tmp_path):
    path = os.path.join(str(tmp_path), 'thermal.DAT')
    rows = oriented_rows(azimuth=0., sample_dip=90., bed_dip_direction=0., bed_dip=0., treatment='Thermal Demag')
    for row in rows:  # temperatures in Temp C; the NRM at room temperature
        if row[1] == 'Thermal Demag' or row[4] != 'NA':
            row[1], row[3] = 'Thermal Demag', {'0': '20.00', '50': '150.00', '100': '300.00', '200': '450.00'}[row[2]]
            row[2] = '0'
    write_export(path, COLUMNS, rows)
    ok, message, printed, out = run(tmp_path, path, input_dir_path='')
    assert ok, message
    assert 'is azimuth 0 and Sample Dip 90, the default of the 2G software' in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert list(meas.method_codes) == ['LT-NO:LP-DIR-T'] + ['LT-T-Z:LP-DIR-T'] * 3
    assert list(meas.treat_temp) == pytest.approx([273, 423, 573, 723])


def test_intensity_divided_by_a_volume_not_in_the_file(tmp_path):
    # the Intensity column is the moment divided by 6 cm^3, but the file has no Volume column
    columns = ['Sample ID', 'AF Z', 'Intensity', 'Declination: Unrotated', 'Inclination: Unrotated',
               'X corr', 'Y corr', 'Z corr']
    rows = []
    for field, dec, inc, moment in [(20, 209.86, -35.42, 5.7653e-6), (110, 201.64, -36.13, 1.1223e-5)]:
        x, y, z = pmag.dir2cart([dec, inc, moment])
        rows.append(['KT049', str(field), '%.4E' % (moment / 6), '%.2f' % dec, '%.2f' % inc,
                     '%.4E' % x, '%.4E' % y, '%.4E' % z])
    path = os.path.join(str(tmp_path), 'no_volume.dat')
    write_export(path, columns, rows)
    ok, message, printed, out = run(tmp_path, path, input_dir_path='')
    assert ok, message
    assert ('KT049: in 2 row(s) the Intensity column is the moment of the X/Y/Z corr components divided '
            'by about 6 cm3') in printed
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert list(meas.magn_moment) == pytest.approx([5.7653e-9, 1.1223e-8], rel=1e-3)
    assert list(meas.treat_ac_field) == pytest.approx([0.002, 0.011])
    # the volume parameter gives magn_volume
    ok, message, printed, out = run(tmp_path, path, input_dir_path='', volume=6)
    meas = read_table(os.path.join(out, 'measurements.txt'))
    assert list(meas.magn_volume) == pytest.approx([5.7653e-9 / 6e-6, 1.1223e-8 / 6e-6], rel=1e-3)


def test_long_core_not_converted(tmp_path):
    columns = ['Sample ID', 'Meas. type', 'Declination: Unrotated', 'Inclination: Unrotated',
               'Intensity', 'Volume', 'X corr', 'Y corr', 'Z corr']
    path = os.path.join(str(tmp_path), 'core.DAT')
    write_export(path, columns, [['MD06', 'SAMPLE/CONTINUOUS', '93.18', '7.98', '2.3E-7', '1',
                                  '-2.3E-7', '4.0E-6', '8.1E-7']])
    ok, message, printed, out = run(tmp_path, path, input_dir_path='')
    assert not ok
    assert 'long-core (continuous) measurements are not converted' in message


@pytest.mark.parametrize('row, expected', [
    ({'Treatment Type': 'None', 'AF Z': '0', 'Temp C': 'NA'}, ('NRM', 0.)),
    ({'Treatment Type': 'Degauss X, Y, & Z', 'AF X': '0', 'AF Y': '0', 'AF Z': '0'}, ('NRM', 0.)),
    ({'Treatment Type': 'Degauss Z', 'AF Z': '300'}, ('AF', 0.03)),
    ({'Treatment Type': 'Thermal Demag', 'Temp C': '20.00'}, ('NRM', 0.)),
    ({'Treatment Type': 'Thermal Demag', 'Temp C': '57.00'}, ('T', 330.)),
    ({'Treatment Type': 'Thermal Demag', 'Temp C': 'NA'}, ('skip', 'no temperature')),
    ({'Treatment Type': 'Degauss Z - ARM axial', 'AF Z': '1000'}, ('skip', 'treatment type Degauss Z - ARM axial')),
    ({'Treatment Type': 'IRM', 'IRM Gauss': '1000'}, ('skip', 'treatment type IRM')),
    ({'Temp C': '25.00'}, ('NRM', 0.)),
    ({'Temp C': '585.00'}, ('T', 858.)),
    ({'Temp C': 'NA'}, ('skip', 'no treatment value (no temperature or field)')),
    ({'Temp C': '-196'}, ('skip', 'temperature below 0 C')),
    ({'AF Z': '150', 'Temp C': '350'}, ('skip', 'both an alternating field and a temperature')),
    ({'AF Z': '150'}, ('AF', 0.015)),
])
def test_treatment(row, expected):
    kind, value = convert._2g_tab_treatment(row)
    assert kind == expected[0]
    if isinstance(expected[1], float):
        assert value == pytest.approx(expected[1])
    else:
        assert value == expected[1]
