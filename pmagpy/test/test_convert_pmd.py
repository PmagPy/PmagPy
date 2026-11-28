"""
Tests for convert.pmd, the converter of PMD (Enkin, PaleoMac) files, on
published files written by different programs:

- IssykKul: PaleoMac exports ("Output from PaleoMac") with carriage returns
  alone as line ends, an upper-case V= without a unit, a second header line,
  and steps N000, A002, ...; and PMD files with steps N000, T150, ...
- IvreaVerbano: files with steps 0mT, 5mT, ..., where 100mT runs into the
  first number, and a moment rounded up to 10.00E-10
- IPGP: a PAL file, whose steps are numbers alone

For each file the directions converted to specimen coordinates, rotated with
the converted sample orientation and bedding, must give the geographic (Dg, Ig)
and tilt-corrected (Ds, Is) directions stored in the file.
"""
import os

import numpy as np
import pytest

from pmagpy import pmag
from pmagpy import convert_2_magic as convert
from pmagpy.test.convert_helpers import CONVERT_DIR, convert_into, read_table

PMD_DIR = os.path.join(CONVERT_DIR, 'pmd_magic')


def run_pmd(tmp_path, path, **kwargs):
    """Convert one file without averaging; return the result, measurements and sample."""
    result, out, _ = convert_into(tmp_path, lambda out: convert.pmd(
        os.path.basename(path), input_dir_path=os.path.dirname(path), dir_path=out,
        noave=1, **kwargs))
    if not result[0]:
        return result, None, None
    meas = read_table(os.path.join(out, 'measurements.txt'))
    sample = read_table(os.path.join(out, 'samples.txt')).iloc[0]
    return result, meas, sample


def stored_steps(path):
    """
    The step labels and the Dg, Ig, Ds, Is columns of a PMD file, read here
    independently of the converter: the lines after the column header, with
    the directions as the four numbers before a95, the last number of each line.
    """
    with open(path, 'rb') as f:
        lines = f.read().decode('latin-1').replace('\r\n', '\n').replace('\r', '\n').split('\n')
    start = [i for i, line in enumerate(lines) if line.split()[:1] in (['STEP'], ['Step'], ['PAL'])][0]
    steps = []
    for line in lines[start + 1:]:
        if line.strip():
            fields = line.split()
            steps.append((fields[0], [float(value) for value in fields[-5:-1]]))
    return steps


def misfits(meas, sample, path):
    """Angles (degrees) between the rotated converted directions and those stored in the file."""
    geographic, tilt_corrected = [], []
    for (_, row), (_, (dec_geo, inc_geo, dec_tilt, inc_tilt)) in zip(meas.iterrows(), stored_steps(path)):
        dec, inc = pmag.dogeo(row['dir_dec'], row['dir_inc'], sample['azimuth'], sample['dip'])
        geographic.append(pmag.angle([dec, inc], [dec_geo, inc_geo])[0])
        if (dec_tilt, inc_tilt) != (0, 0):  # files without bedding leave Ds, Is at 0.0
            dec, inc = pmag.dotilt(dec, inc, sample['bed_dip_direction'], sample['bed_dip'])
            tilt_corrected.append(pmag.angle([dec, inc], [dec_tilt, inc_tilt])[0])
    return np.array(geographic), np.array(tilt_corrected)


# file, maximum misfit (degrees), number of steps; the moments of the PaleoMac
# exports are written with two significant digits (misfits up to 1.5 degrees in
# these two files, 2.4 in all 392 such files of the study), the others with three
PUBLISHED = [
    (os.path.join('IssykKul', 'A001.pmd'), 2.0, 17),
    (os.path.join('IssykKul', 'S001.pmd'), 2.0, 13),
    (os.path.join('IssykKul', 'AT036.pmd'), 0.2, 14),
    (os.path.join('IvreaVerbano', 'ossola_AF', 'IVB0101.pmd'), 0.2, 15),
    (os.path.join('IvreaVerbano', 'strona_AF', 'IVB2401.pmd'), 0.2, 15),
    (os.path.join('IvreaVerbano', 'termico', 'IVB0102.pmd'), 0.2, 13),
]


class TestPublishedFiles:

    @pytest.mark.parametrize('name,tolerance,n_steps', PUBLISHED)
    def test_stored_directions_reproduced(self, tmp_path, name, tolerance, n_steps):
        path = os.path.join(PMD_DIR, name)
        result, meas, sample = run_pmd(tmp_path, path)
        assert result[0], result[1]
        assert len(meas) == n_steps == len(stored_steps(path))
        geographic, tilt_corrected = misfits(meas, sample, path)
        assert geographic.max() < tolerance
        assert len(tilt_corrected) == n_steps
        assert tilt_corrected.max() < tolerance

    def test_paleomac_export(self, tmp_path):
        """A001: carriage returns alone, V= without m3, a hade above 90 degrees."""
        path = os.path.join(PMD_DIR, 'IssykKul', 'A001.pmd')
        with open(path, 'rb') as f:
            raw = f.read()
        assert b'\r' in raw and b'\n' not in raw
        result, meas, sample = run_pmd(tmp_path, path)
        assert result[0], result[1]
        assert sample['sample'] == 'A001'
        # a= 279.5   b= 97.0   s= 285.0   d=  21.0
        assert (sample['azimuth'], sample['dip']) == (279.5, -97.0)
        assert (sample['bed_dip_direction'], sample['bed_dip']) == (15.0, 21.0)
        # no date in the header line
        assert 'description' not in meas.columns or meas['description'].isna().all()
        # N000, A002, A004, ...: the NRM and then alternating field steps in mT
        assert meas.iloc[0]['method_codes'] == 'LT-NO:LP-DIR-AF'
        assert meas.iloc[0]['treat_ac_field'] == 0
        assert (meas.iloc[1:]['method_codes'] == 'LT-AF-Z:LP-DIR-AF').all()
        assert meas.iloc[1]['treat_ac_field'] == pytest.approx(0.002)
        # moment from Xc, Yc, Zc (Am^2); the magnetization from the MAG column (A/m)
        assert meas.iloc[0]['magn_moment'] == pytest.approx(np.sqrt(0.27**2 + 0.15**2 + 0.41**2) * 1e-7, rel=1e-3)
        assert meas.iloc[0]['magn_volume'] == pytest.approx(0.47e-2)

    def test_azimuth_above_360(self, tmp_path):
        result, meas, sample = run_pmd(tmp_path, os.path.join(PMD_DIR, 'IssykKul', 'S001.pmd'))
        assert result[0], result[1]
        # a= 363.0   b= 44.0   s= 274.0   d=  25.0
        assert (sample['azimuth'], sample['dip']) == (3.0, -44.0)
        assert (sample['bed_dip_direction'], sample['bed_dip']) == (4.0, 25.0)

    def test_thermal_steps(self, tmp_path):
        """AT036: N000, T150, ..., T685; the first line holds coordinates, not a comment."""
        result, meas, sample = run_pmd(tmp_path, os.path.join(PMD_DIR, 'IssykKul', 'AT036.pmd'))
        assert result[0], result[1]
        assert sample['description'] == '42.22770 76.69290'
        assert meas.iloc[0]['method_codes'] == 'LT-NO:LP-DIR-T'
        assert (meas.iloc[1:]['method_codes'] == 'LT-T-Z:LP-DIR-T').all()
        assert list(meas['treat_temp']) == pytest.approx(
            [273, 423, 573, 673, 723, 773, 803, 828, 848, 873, 908, 928, 943, 958])
        assert (meas['treat_ac_field'] == 0).all()
        assert meas.iloc[0]['description'] == 'Date: 01-05-2018 16:27'

    def test_mt_labels(self, tmp_path):
        """IVB0101: 0mT to 100mT; the label 100mT runs into the first number."""
        path = os.path.join(PMD_DIR, 'IvreaVerbano', 'ossola_AF', 'IVB0101.pmd')
        result, meas, sample = run_pmd(tmp_path, path)
        assert result[0], result[1]
        assert meas.iloc[0]['method_codes'] == 'LT-NO:LP-DIR-AF'
        assert (meas.iloc[1:]['method_codes'] == 'LT-AF-Z:LP-DIR-AF').all()
        assert list(meas['treat_ac_field'] * 1e3) == pytest.approx(
            [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 80, 100])
        last = meas.iloc[-1]
        dec, inc, moment = pmag.cart2dir([-4.46e-10, 1.29e-9, 2.80e-10])
        assert (last['dir_dec'], last['dir_inc']) == pytest.approx((dec, inc), abs=0.05)
        assert last['magn_moment'] == pytest.approx(moment, rel=1e-3)
        # a= 43.0   b=-58.0   s=227.0   d= 90.0
        assert (sample['azimuth'], sample['dip']) == (43.0, 58.0)
        assert (sample['bed_dip_direction'], sample['bed_dip']) == (317.0, 90.0)

    def test_moment_rounded_up(self, tmp_path):
        """IVB2401: Zc written as 10.00E-10 at 0 mT and Yc as 10.00E-09 at 55 mT."""
        result, meas, _ = run_pmd(tmp_path, os.path.join(PMD_DIR, 'IvreaVerbano', 'strona_AF', 'IVB2401.pmd'))
        assert result[0], result[1]
        assert len(meas) == 15
        row = meas[np.isclose(meas['treat_ac_field'], 0.055)].iloc[0]
        dec, inc, moment = pmag.cart2dir([-2.15e-8, 10.00e-9, -6.73e-9])
        assert (row['dir_dec'], row['dir_inc']) == pytest.approx((dec, inc), abs=0.05)

    def test_naming_convention_7(self, tmp_path):
        """IVB0101: site IVB01 from the first five characters."""
        path = os.path.join(PMD_DIR, 'IvreaVerbano', 'ossola_AF', 'IVB0101.pmd')
        result, _, sample = run_pmd(tmp_path, path, samp_con='7-5')
        assert result[0], result[1]
        assert sample['site'] == 'IVB01'


class TestDemagnetizationType:

    def test_dmg_overrides_labels(self, tmp_path, capsys):
        """
        IVB0102 (termico): steps labelled 2mT to 68mT; dmg='t' reads every step
        as thermal, with the values as written, and names the labels it overrides.
        """
        path = os.path.join(PMD_DIR, 'IvreaVerbano', 'termico', 'IVB0102.pmd')
        result, meas, _ = run_pmd(tmp_path, path)
        assert result[0], result[1]
        assert (meas['method_codes'].str.contains('LP-DIR-AF')).all()
        assert meas.iloc[0]['treat_ac_field'] == pytest.approx(0.002)

        result, out, _ = convert_into(tmp_path / 'thermal', lambda out: convert.pmd(
            path, dir_path=out, noave=1, dmg='t'))
        assert result[0], result[1]
        meas = read_table(os.path.join(out, 'measurements.txt'))
        assert (meas['treat_ac_field'] == 0).all()
        assert list(meas['treat_temp'] - 273) == pytest.approx(
            [2, 20, 23, 26, 29, 32, 37, 42, 46, 50, 55, 60, 68])
        assert (meas['method_codes'].str.contains('LP-DIR-T')).all()
        # convert_into hides the printed output, so run once more to see the warning
        convert.pmd(path, dir_path=str(tmp_path / 'thermal' / 'out'), noave=1, dmg='t')
        assert "2mT, 20mT" in capsys.readouterr().out

    def test_pal_file(self, tmp_path):
        """0110C.PMD: a PAL file, steps 0 to 200; thermal by default, alternating field with dmg='af'."""
        path = os.path.join(PMD_DIR, 'IPGP', '0110C.PMD')
        result, meas, _ = run_pmd(tmp_path / 'default', path)
        assert result[0], result[1]
        assert meas['method_codes'].str.endswith('LP-DIR-T').all()
        assert list(meas['treat_temp'] - 273)[:4] == pytest.approx([0, 6, 9, 12])
        assert (meas['treat_ac_field'] == 0).all()

        result, meas, _ = run_pmd(tmp_path / 'af', path, dmg='af')
        assert result[0], result[1]
        assert meas.iloc[0]['method_codes'] == 'LT-NO:LP-DIR-AF'
        assert (meas.iloc[1:]['method_codes'] == 'LT-AF-Z:LP-DIR-AF').all()
        assert list(meas['treat_ac_field'] * 1e3)[:4] == pytest.approx([0, 6, 9, 12])
        assert meas.iloc[-1]['treat_ac_field'] == pytest.approx(0.2)

    def test_numbers_alone_need_dmg(self, tmp_path):
        """The steps of 0110C.PMD under a STEP column header: the type must be given."""
        with open(os.path.join(PMD_DIR, 'IPGP', '0110C.PMD'), 'rb') as f:
            raw = f.read().replace(b' PAL  Xc', b'STEP  Xc')
        path = tmp_path / '0110C.PMD'
        path.write_bytes(raw)
        result, meas, _ = run_pmd(tmp_path / 'default', str(path))
        assert result[0] is False
        assert 'dmg' in result[1]
        result, meas, _ = run_pmd(tmp_path / 'af', str(path), dmg='af')
        assert result[0], result[1]
        assert meas.iloc[1]['treat_ac_field'] == pytest.approx(0.006)

    def test_invalid_dmg(self, tmp_path):
        result, _, _ = run_pmd(tmp_path, os.path.join(PMD_DIR, 'IPGP', '0110C.PMD'), dmg='thermal')
        assert result[0] is False
        assert 'dmg' in result[1]


class TestEncodingAndLabels:

    def test_latin1_greek_keys_and_degree_signs(self, tmp_path):
        """
        AT036 rewritten with the bytes other programs write: alpha and beta for a
        and b (DOS code page 437) and steps 150 and 300 as 150 and a degree sign
        and C (Latin-1 and code page 437); the result is that of the original.
        """
        original = os.path.join(PMD_DIR, 'IssykKul', 'AT036.pmd')
        with open(original, 'rb') as f:
            raw = f.read()
        raw = raw.replace(b'AT036   a=', b'AT036   \xe0=').replace(b'   b=101.5', b'   \xe1=101.5')
        raw = raw.replace(b'\r\nT150 ', b'\r\n150\xb0C').replace(b'\r\nT300 ', b'\r\n300\xf8C')
        path = tmp_path / 'AT036.pmd'
        path.write_bytes(raw)
        result, meas, sample = run_pmd(tmp_path / 'edited', str(path))
        assert result[0], result[1]
        _, expected_meas, expected_sample = run_pmd(tmp_path / 'original', original)
        assert (sample['azimuth'], sample['dip']) == (expected_sample['azimuth'], expected_sample['dip'])
        assert list(meas['treat_temp']) == list(expected_meas['treat_temp'])
        assert list(meas['method_codes']) == list(expected_meas['method_codes'])

    @pytest.mark.parametrize('label,expected', [
        ('NRM', ('NRM', 0)), ('N000', ('NRM', 0)), ('0', ('NRM', 0)), ('0mT', ('NRM', 0)),
        ('H000', ('NRM', 0)), ('H020', ('af', 20)), ('M020', ('af', 20)), ('A002', ('af', 2)),
        ('20mT', ('af', 20)), ('20MT', ('af', 20)), ('20M', ('af', 20)), ('2.5mT', ('af', 2.5)),
        ('T350', ('t', 350)), ('350C', ('t', 350)), ('350\xb0C', ('t', 350)), ('350\xf8C', ('t', 350)),
        ('20', ('', 20)),
    ])
    def test_step_labels(self, label, expected):
        step_type, value = convert._pmd_step(label)
        assert (step_type, value) == pytest.approx(expected)

    @pytest.mark.parametrize('label', ['X20', 'IRM', '', 'T'])
    def test_unknown_step_label(self, label):
        with pytest.raises(ValueError):
            convert._pmd_step(label)

    def test_long_name_against_the_first_key(self):
        specimen, values, date, time = convert._pmd_header(
            'IVB0506BBBa= 99.0   b=-33.0   s=159.0   d= 59.0   v=11.0E-6m3')
        assert specimen == 'IVB0506BBB'
        assert values == [99.0, -33.0, 159.0, 59.0]
        assert (date, time) == ('', '')
