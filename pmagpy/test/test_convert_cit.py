"""
Tests for convert.cit, the CIT-format converter.

Coverage:
- Basic conversion of a .sam file into the five MagIC 3.0 tables
- Record counts and MagIC 3.0 headers in each output file
- The oersted flag's effect on AF demag step scaling (Gauss vs milliTesla)
- Sample azimuths and bedding dip directions wrapped into [0, 360)
- Actionable error reporting on invalid inputs
- Cases from real studies, through the converter registry (the second half of this file)
"""
import os
import shutil

import pandas as pd
import pytest

from pmagpy import convert_2_magic as convert
from pmagpy import contribution_builder as cb
from pmagpy import convert_registry as reg


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


class TestCitOrientationRange:
    """Strikes under 90 degrees give azimuths in [0, 360), not negative ones."""

    def test_azimuths_are_positive(self, tmp_cwd):
        """BL9001-1 has a core strike of 82.3, i.e. a core azimuth of 352.3 (not -7.7)."""
        _run_bl9()
        samp_df = cb.MagicDataFrame('samples.txt').df
        azimuths = samp_df['azimuth'].astype(float)
        assert ((azimuths >= 0) & (azimuths < 360)).all()
        assert azimuths['BL9001-1'] == pytest.approx(352.3)

    def test_bedding_dip_direction_wraps(self, tmp_cwd):
        """A bedding strike of 300 dips toward 30, not 390."""
        data_dir = tmp_cwd / 'bl9-1'
        shutil.copytree(USGS_BL9_DIR, data_dir)
        spec_file = data_dir / 'BL9001-1'
        lines = spec_file.read_bytes().decode().splitlines(keepends=True)
        lines[1] = '      0  82.3  65.0 300.0  20.0  1.00\r\n'
        spec_file.write_bytes(''.join(lines).encode())
        _run_bl9(input_dir_path=str(data_dir))
        samp_df = cb.MagicDataFrame('samples.txt').df
        assert float(samp_df.loc['BL9001-1', 'bed_dip_direction']) == pytest.approx(30.0)
        assert float(samp_df.loc['BL9001-1', 'bed_dip']) == pytest.approx(20.0)


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

# ----- the cases real studies put in front of the converter -----------------------------
#
# The CIT converter on the cases real studies put in front of it.
#
#     pytest pmagpy/test/test_convert_cit.py -q
#
# Each test writes a small CIT study (a ``.sam`` index and the specimen files it
# lists) in the fixed-column layout the CIT programs produce, converts it through
# the registry, and reads the tables back. The cases come from converting the
# group's Sibley, Michipicoten and Zavkhan studies and comparing with the tables
# made years earlier: strikes that wrap past north, "sun compass" specimen
# comments, a ``TT`` step recorded without a temperature, an ``Other:`` line,
# replicate steps, and a volume of exactly 1.0.

# a measurement line in CIT columns: treatment (0-5), core dec/inc, stratigraphic dec/inc,
# intensity in emu/cc (31-38), CSD (41-45), geographic dec (46-50) and inc (52-57), sigmas
LINE = "{treat:<6} 317.7  31.5 307.2  43.1 {emu:8.2E} {csd:05.1f} {dec:05.1f} {inc:5.1f} 11.94679 2.897120 2.18\n"


def measurement(treat, dec, inc, emu=2.0e-4, csd=2.8):
    return LINE.format(treat=treat, dec=dec, inc=inc, emu=emu, csd=csd)


def write_study(directory, header_latlon=" 47.7 -85.8   0.0", specimens=()):
    """A .sam index and its specimen files; ``specimens`` is (name, comment, sample_line, [lines])."""
    with open(os.path.join(directory, "T1-.sam"), "w") as fh:
        fh.write("test study\n" + header_latlon + "\n" + "".join(name + "\n" for name, *_ in specimens))
    for name, comment, sample_line, lines in specimens:
        with open(os.path.join(directory, name), "w") as fh:
            fh.write(f"{name[:-1]} {name[-1]} {comment}\n{sample_line}\n" + "".join(lines))


def convert_study(directory, **values):
    result = reg.convert_files(reg.FORMATS["cit"], ["T1-.sam"], {"samp_con": "2", "specnum": 1, **values}, directory)
    assert result.ok, result.log
    return result


def read(directory, table):
    return pd.read_csv(os.path.join(directory, f"{table}.txt"), sep="\t", header=1, dtype=str, keep_default_na=False)


# strike 10 with the -90 turns the azimuth negative; bedding strike 300 + 90 passes 360
STEEP = "   44.1  10.0   8.0 300.0  17.8  1.0"
FLAT = "   44.1 153.3   8.0  92.0  17.8  1.0"
DEMAG = [measurement("NRM", 233.4, 39.6), measurement("TT 100", 249.9, 29.0), measurement("TT 200", 252.0, 21.7)]


class TestSamples:
    def test_azimuth_and_dip_direction_stay_within_the_circle(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "mag compass orientation", STEEP, DEMAG)])
        convert_study(str(tmp_path))
        samp = read(tmp_path, "samples").iloc[0]
        assert float(samp["azimuth"]) == 280.0 and float(samp["bed_dip_direction"]) == 30.0
        assert float(samp["dip"]) == -8.0 and float(samp["bed_dip"]) == 17.8

    def test_orientation_method_read_from_the_specimen_comment(self, tmp_path):
        write_study(tmp_path, specimens=[
            ("T1-1a", "sun compass orientation", FLAT, DEMAG),
            ("T1-2a", "mag compass orientation (IGRF corrected)", FLAT, DEMAG),
            ("T1-3a", "", FLAT, DEMAG)])
        convert_study(str(tmp_path))
        codes = read(tmp_path, "samples").set_index("sample")["method_codes"]
        assert codes["T1-1"] == "SO-SUN"
        assert codes["T1-2"] == "SO-MAG:SO-CMD-NORTH"
        assert codes["T1-3"] == "SO-MAG", "no correction in the header and none claimed: the caller's code alone"

    def test_header_declination_correction_is_applied_and_recorded(self, tmp_path):
        write_study(tmp_path, header_latlon=" 47.7 -85.8   5.0", specimens=[("T1-1a", "", FLAT, DEMAG)])
        convert_study(str(tmp_path), methods="SO-SM")
        samp = read(tmp_path, "samples").iloc[0]
        assert samp["method_codes"] == "SO-SM:SO-CMD-NORTH" and float(samp["azimuth_dec_correction"]) == 5.0
        assert abs(float(samp["azimuth"]) - (153.3 + 5 - 90)) < 1e-6

    def test_site_coordinates_come_from_the_header(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, DEMAG)])
        convert_study(str(tmp_path), location="Michipicoten")
        site = read(tmp_path, "sites").iloc[0]
        assert (site["lat"], site["lon"], site["location"]) == ("47.7", "-85.8", "Michipicoten")


class TestSpecimens:
    def test_volume_of_one_means_not_normalized(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, DEMAG)])
        result = convert_study(str(tmp_path))
        spec = read(tmp_path, "specimens").iloc[0]
        assert spec["method_codes"] == "LP-NOMAG" and spec["volume"] == ""
        assert result.log.count("T1-1a volume/mass is 1.0") == 1, "one warning per specimen, not three"
        meas = read(tmp_path, "measurements")
        assert "LP-NOMAG" not in ":".join(meas["method_codes"]), "the specimen's code is not a treatment"
        assert abs(float(meas["magn_moment"].iloc[0]) - 2.0e-7) < 1e-12, "emu to Am2"

    def test_mass_normalization_in_grams_and_kilograms(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT.replace("  1.0", " 12.5"), DEMAG)])
        convert_study(str(tmp_path), norm="g")
        spec = read(tmp_path, "specimens").iloc[0]
        assert abs(float(spec["weight"]) - 12.5e-3) < 1e-9 and spec["volume"] == ""
        convert_study(str(tmp_path), norm="kg")
        assert abs(float(read(tmp_path, "specimens").iloc[0]["weight"]) - 12.5) < 1e-9


class TestMeasurements:
    def test_replicate_steps_are_kept_by_default(self, tmp_path):
        twice = DEMAG + [measurement("TT 200", 250.0, 22.0)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, twice)])
        convert_study(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert len(meas) == 4 and "DE-VM" not in ":".join(meas["method_codes"])
        convert_study(str(tmp_path), noave=False)
        meas = read(tmp_path, "measurements")
        assert len(meas) == 3 and "DE-VM" in meas["method_codes"].iloc[-1]

    def test_a_tt_step_without_a_temperature_is_room_temperature_not_the_declination(self, tmp_path):
        lines = [measurement("NRM", 233.4, 39.6), measurement("TT", 292.2, 40.0), measurement("TT 100", 249.9, 29.0)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, lines)])
        result = convert_study(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert [float(t) for t in meas["treat_temp"]] == [273.0, 273.0, 373.0]
        # at room temperature it is an NRM measurement (measurements_methods3 says so); the note stays
        assert meas["method_codes"].iloc[1].startswith("LT-NO") and "missing" in meas["description"].iloc[1]
        assert "TT step without a temperature" in result.log

    def test_an_unknown_treatment_is_skipped_with_a_warning(self, tmp_path):
        lines = DEMAG + [measurement("Other:", 336.9, -18.1), measurement("TT 300", 248.6, 17.5)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, lines)])
        result = convert_study(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert len(meas) == 4 and float(meas["treat_temp"].iloc[-1]) == 573.0
        assert "T1-1a: treatment 'Other:' not understood" in result.log

    def test_liquid_nitrogen_step(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, [measurement("NRM", 233.4, 39.6), measurement("LN2", 249.4, 32.4)])])
        convert_study(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert meas["method_codes"].iloc[1].startswith("LT-LT-Z") and float(meas["treat_temp"].iloc[1]) == 77.0
        assert (meas["dir_dec"].astype(float).tolist(), meas["dir_inc"].astype(float).tolist()) == ([233.4, 249.4], [39.6, 32.4])
