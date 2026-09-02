"""The CIT converter on the cases real studies put in front of it.

    pytest pmagpy/test/test_convert_cit.py -q

Each test writes a small CIT study (a ``.sam`` index and the specimen files it
lists) in the fixed-column layout the CIT programs produce, converts it through
the registry, and reads the tables back. The cases come from converting the
group's Sibley, Michipicoten and Zavkhan studies and comparing with the tables
made years earlier: strikes that wrap past north, "sun compass" specimen
comments, a ``TT`` step recorded without a temperature, an ``Other:`` line,
replicate steps, and a volume of exactly 1.0.
"""
import os

import pandas as pd

from pmagpy import convert_registry as reg

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


def convert(directory, **values):
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
        convert(str(tmp_path))
        samp = read(tmp_path, "samples").iloc[0]
        assert float(samp["azimuth"]) == 280.0 and float(samp["bed_dip_direction"]) == 30.0
        assert float(samp["dip"]) == -8.0 and float(samp["bed_dip"]) == 17.8

    def test_orientation_method_read_from_the_specimen_comment(self, tmp_path):
        write_study(tmp_path, specimens=[
            ("T1-1a", "sun compass orientation", FLAT, DEMAG),
            ("T1-2a", "mag compass orientation (IGRF corrected)", FLAT, DEMAG),
            ("T1-3a", "", FLAT, DEMAG)])
        convert(str(tmp_path))
        codes = read(tmp_path, "samples").set_index("sample")["method_codes"]
        assert codes["T1-1"] == "SO-SUN"
        assert codes["T1-2"] == "SO-MAG:SO-CMD-NORTH"
        assert codes["T1-3"] == "SO-MAG", "no correction in the header and none claimed: the caller's code alone"

    def test_header_declination_correction_is_applied_and_recorded(self, tmp_path):
        write_study(tmp_path, header_latlon=" 47.7 -85.8   5.0", specimens=[("T1-1a", "", FLAT, DEMAG)])
        convert(str(tmp_path), methods="SO-SM")
        samp = read(tmp_path, "samples").iloc[0]
        assert samp["method_codes"] == "SO-SM:SO-CMD-NORTH" and float(samp["azimuth_dec_correction"]) == 5.0
        assert abs(float(samp["azimuth"]) - (153.3 + 5 - 90)) < 1e-6

    def test_site_coordinates_come_from_the_header(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, DEMAG)])
        convert(str(tmp_path), location="Michipicoten")
        site = read(tmp_path, "sites").iloc[0]
        assert (site["lat"], site["lon"], site["location"]) == ("47.7", "-85.8", "Michipicoten")


class TestSpecimens:
    def test_volume_of_one_means_not_normalized(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, DEMAG)])
        result = convert(str(tmp_path))
        spec = read(tmp_path, "specimens").iloc[0]
        assert spec["method_codes"] == "LP-NOMAG" and spec["volume"] == ""
        assert result.log.count("T1-1a volume/mass is 1.0") == 1, "one warning per specimen, not three"
        meas = read(tmp_path, "measurements")
        assert "LP-NOMAG" not in ":".join(meas["method_codes"]), "the specimen's code is not a treatment"
        assert abs(float(meas["magn_moment"].iloc[0]) - 2.0e-7) < 1e-12, "emu to Am2"

    def test_mass_normalization_in_grams_and_kilograms(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT.replace("  1.0", " 12.5"), DEMAG)])
        convert(str(tmp_path), norm="g")
        spec = read(tmp_path, "specimens").iloc[0]
        assert abs(float(spec["weight"]) - 12.5e-3) < 1e-9 and spec["volume"] == ""
        convert(str(tmp_path), norm="kg")
        assert abs(float(read(tmp_path, "specimens").iloc[0]["weight"]) - 12.5) < 1e-9


class TestMeasurements:
    def test_replicate_steps_are_kept_by_default(self, tmp_path):
        twice = DEMAG + [measurement("TT 200", 250.0, 22.0)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, twice)])
        convert(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert len(meas) == 4 and "DE-VM" not in ":".join(meas["method_codes"])
        convert(str(tmp_path), noave=False)
        meas = read(tmp_path, "measurements")
        assert len(meas) == 3 and "DE-VM" in meas["method_codes"].iloc[-1]

    def test_a_tt_step_without_a_temperature_is_room_temperature_not_the_declination(self, tmp_path):
        lines = [measurement("NRM", 233.4, 39.6), measurement("TT", 292.2, 40.0), measurement("TT 100", 249.9, 29.0)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, lines)])
        result = convert(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert [float(t) for t in meas["treat_temp"]] == [273.0, 273.0, 373.0]
        # at room temperature it is an NRM measurement (measurements_methods3 says so); the note stays
        assert meas["method_codes"].iloc[1].startswith("LT-NO") and "missing" in meas["description"].iloc[1]
        assert "TT step without a temperature" in result.log

    def test_an_unknown_treatment_is_skipped_with_a_warning(self, tmp_path):
        lines = DEMAG + [measurement("Other:", 336.9, -18.1), measurement("TT 300", 248.6, 17.5)]
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, lines)])
        result = convert(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert len(meas) == 4 and float(meas["treat_temp"].iloc[-1]) == 573.0
        assert "T1-1a: treatment 'Other:' not understood" in result.log

    def test_liquid_nitrogen_step(self, tmp_path):
        write_study(tmp_path, specimens=[("T1-1a", "", FLAT, [measurement("NRM", 233.4, 39.6), measurement("LN2", 249.4, 32.4)])])
        convert(str(tmp_path))
        meas = read(tmp_path, "measurements")
        assert meas["method_codes"].iloc[1].startswith("LT-LT-Z") and float(meas["treat_temp"].iloc[1]) == 77.0
        assert (meas["dir_dec"].astype(float).tolist(), meas["dir_inc"].astype(float).tolist()) == ([233.4, 249.4], [39.6, 32.4])
