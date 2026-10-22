"""
Tests for the sun compass functions in pmag.py: dosundec, gha and julian.

The reference azimuths are the azimuth of the shadow (the sun's azimuth + 180)
plus the shadow angle. The sun's azimuth, Greenwich hour angle and declination
were calculated with astropy 8.0.2 (get_sun transformed to AltAz for the
azimuth, and apparent sidereal time minus apparent right ascension, true
equator of date, for the hour angle; geometric position, no refraction; IERS
auto-download disabled). The azimuths agree with an independent
implementation of the NOAA solar calculator equations
(https://gml.noaa.gov/grad/solcalc/calcdetails.html) to 0.011 degrees. The cases
include the early-morning and late-afternoon geometry in which the sun is on
the poleward side of the east-west line, which the arcsin solution used before
the fix for #695 placed in the wrong quadrant (errors of 5 to 36 degrees for
these cases), and half-hour time zones, which were truncated to whole hours.
"""
import os
import warnings

import numpy as np
import pandas as pd
import pytest

from pmagpy import ipmag, pmag

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        'data_files')

# (description, local date and time, hours to subtract for UT, lat, lon,
#  shadow_angle, expected azimuth)
SUN_COMPASS_CASES = [
    ('Cyprus docstring example, afternoon', '1994:05:23:16:9', 3, 35, 33, 68, 154.137),
    ('Duluth June solstice 08:00 CDT, sun north of east', '2025:06:21:08:00', -5, 46.8, -92.1, 0, 261.849),
    ('Duluth June solstice 13:00 CDT, near noon', '2025:06:21:13:00', -5, 46.8, -92.1, 0, 354.051),
    ('Duluth June solstice 18:00 CDT, sun north of west', '2025:06:21:18:00', -5, 46.8, -92.1, 0, 94.590),
    ('Duluth June solstice 20:00 CDT, UT on the next day', '2025:06:21:20:00', -5, 46.8, -92.1, 0, 114.900),
    ('Duluth December 10:00 CST', '2025:12:19:10:00', -6, 46.8, -92.1, 0, 330.430),
    ('Minneapolis equinox 09:00 CDT', '2025:03:20:09:00', -5, 44.98, -93.27, 0, 288.098),
    ('Merced July 18:45 PDT, sun north of west', '2022:07:15:18:45', -7, 37.7, -122.5, 0, 102.909),
    ('Graafwater southern winter afternoon', '2025:05:31:15:52', 2, -31.974709, 18.740605, 374, 147.679),
    ('Cape Town December 07:30, sun south of east', '2024:12:21:07:30', 2, -33.9, 18.4, 0, 284.298),
    ('Cape Town December 18:30, sun south of west', '2024:12:21:18:30', 2, -33.9, 18.4, 0, 72.017),
    ('Zavkhan July 06:30, UT on the previous day', '2016:07:10:06:30', 8, 47.9, 96.5, 120, 2.599),
    ('Hawaii June 08:00, tropics, sun north', '2024:06:21:08:00', -10, 19.7, -155.1, 0, 253.548),
    ('Hawaii June 12:30, sun north of the zenith', '2024:06:21:12:30', -10, 19.7, -155.1, 0, 155.073),
    ('Quito equinox 10:00, equator', '2024:03:20:10:00', -5, -0.2, -78.5, 0, 269.380),
    ('Svalbard June 03:00, midnight sun north-east', '2024:06:21:03:00', 2, 78.2, 15.6, 0, 208.238),
    ('Hyderabad November 09:15, UT+5.5', '2024:11:15:09:15', 5.5, 17.4, 78.5, 0, 309.507),
    ('Adelaide January 17:30, UT+10.5, sun south of west', '2025:01:15:17:30', 10.5, -34.9, 138.6, 250, 337.350),
    ("St. John's July 07:00, UT-2.5, sun north of east", '2023:07:04:07:00', -2.5, 47.6, -52.7, 0, 253.230),
]

# (month, day, year, fraction of the day in UT, Greenwich hour angle, declination)
GHA_CASES = [
    (1, 1, 2000, 0.5, 359.1802, -23.0324),
    (10, 20, 2000, 0.5, 3.8201, -10.5461),
    (6, 20, 2024, 0.8687500000, 132.3036, 23.4382),  # June solstice
    (3, 20, 2024, 0.1291666667, 224.6452, 0.0000),   # March equinox
    (11, 3, 2025, 0.3125, 296.6089, -15.1688),
    (5, 23, 1994, 0.5479166667, 18.0775, 20.5960),
]


def angle_difference(a, b):
    """Signed difference a - b of two azimuths in degrees, in [-180, 180)."""
    return (a - b + 180) % 360 - 180


class TestDosundec:
    """Tests for pmag.dosundec."""

    @pytest.mark.parametrize('description, date, delta_u, lat, lon, shadow_angle, expected',
                             SUN_COMPASS_CASES, ids=[case[0] for case in SUN_COMPASS_CASES])
    def test_reference_azimuths(self, description, date, delta_u, lat, lon, shadow_angle, expected):
        """Azimuths agree with astropy reference values to 0.05 degrees."""
        sundata = {'date': date, 'delta_u': delta_u, 'lat': lat, 'lon': lon,
                   'shadow_angle': shadow_angle}
        assert abs(angle_difference(pmag.dosundec(sundata), expected)) < 0.05

    def test_string_inputs(self):
        """orientation_magic passes the values as strings."""
        numbers = {'date': '2025:06:21:18:00', 'delta_u': -5, 'lat': 46.8, 'lon': -92.1,
                   'shadow_angle': 30}
        strings = {key: str(value) for key, value in numbers.items()}
        assert pmag.dosundec(strings) == pytest.approx(pmag.dosundec(numbers))

    def test_half_hour_offset_is_not_truncated(self):
        """09:15 at UT+5.5 is the same instant as 03:45 UT."""
        local = {'date': '2024:11:15:09:15', 'delta_u': 5.5, 'lat': 17.4, 'lon': 78.5,
                 'shadow_angle': 0}
        universal = dict(local, date='2024:11:15:03:45', delta_u=0)
        assert pmag.dosundec(local) == pytest.approx(pmag.dosundec(universal))

    def test_shadow_angle_is_added(self):
        """The shadow angle is added to the azimuth of the shadow, modulo 360."""
        sundata = {'date': '2025:06:21:08:00', 'delta_u': -5, 'lat': 46.8, 'lon': -92.1,
                   'shadow_angle': 0}
        shadow_azimuth = pmag.dosundec(sundata)
        for shadow_angle in (45, 200, 400, -30):
            sundata['shadow_angle'] = shadow_angle
            assert pmag.dosundec(sundata) == pytest.approx((shadow_azimuth + shadow_angle) % 360)

    @pytest.mark.parametrize('lat, lon, date, delta_u', [
        (46.8, -92.1, '2025:06:21', -5),      # Duluth, June solstice
        (-33.9, 18.4, '2024:12:21', 2),       # Cape Town, December solstice
        (78.2, 15.6, '2024:06:21', 2),        # Svalbard, midnight sun
        (19.7, -155.1, '2024:06:21', -10),    # Hawaii, sun north of the zenith at noon
    ])
    def test_azimuth_changes_continuously_through_the_day(self, lat, lon, date, delta_u):
        """No jumps between consecutive minutes over the whole day.

        A quadrant error appears as a jump of up to 180 degrees when the sun
        crosses the east-west line or the hour angle crosses 90 degrees. The
        atan2 solution is continuous, so the night-time minutes are included.
        """
        azimuths = []
        with warnings.catch_warnings():
            # the night-time minutes warn that the sun is below the horizon
            warnings.simplefilter('ignore', UserWarning)
            for minute in range(0, 24 * 60, 1):
                sundata = {'date': '{}:{:02d}:{:02d}'.format(date, minute // 60, minute % 60),
                           'delta_u': delta_u, 'lat': lat, 'lon': lon, 'shadow_angle': 0}
                azimuths.append(pmag.dosundec(sundata))
        steps = np.abs(angle_difference(np.array(azimuths[1:]), np.array(azimuths[:-1])))
        # the sun's azimuth changes by much less than 5 degrees per minute except
        # within about 1 degree of the zenith, which these cases avoid
        assert steps.max() < 5

    def test_warns_when_sun_is_below_horizon(self):
        """A time when the sun is below the horizon (for example a 01:01
        placeholder for a missing time) gives a warning; the azimuth is still
        returned."""
        sundata = {'date': '2025:06:21:01:01', 'delta_u': -5, 'lat': 46.8, 'lon': -92.1,
                   'shadow_angle': 0}
        with pytest.warns(UserWarning, match='below the horizon'):
            azimuth = pmag.dosundec(sundata)
        assert 0 <= azimuth < 360

    @pytest.mark.parametrize('description, date, delta_u, lat, lon, shadow_angle, expected',
                             SUN_COMPASS_CASES, ids=[case[0] for case in SUN_COMPASS_CASES])
    def test_no_warning_in_daylight(self, description, date, delta_u, lat, lon, shadow_angle,
                                    expected):
        """None of the daytime reference cases warn."""
        sundata = {'date': date, 'delta_u': delta_u, 'lat': lat, 'lon': lon,
                   'shadow_angle': shadow_angle}
        with warnings.catch_warnings():
            warnings.simplefilter('error', UserWarning)
            pmag.dosundec(sundata)

    def test_no_warning_at_sunset(self):
        """No warning while part of the sun is still above the horizon.

        At Duluth on 21 June 2025 the sun's center reaches the geometric
        horizon at about 21:00 CDT, and sunset (-0.83 degrees) is at about
        21:06. The warning starts when the center is more than 1 degree below
        the horizon, at about 21:08.
        """
        for minute, expect_warning in ((5, False), (20, True)):
            sundata = {'date': '2025:06:21:21:{:02d}'.format(minute), 'delta_u': -5,
                       'lat': 46.8, 'lon': -92.1, 'shadow_angle': 0}
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always', UserWarning)
                pmag.dosundec(sundata)
            assert bool(caught) == expect_warning, minute

    def test_orientation_magic_sun_compass_azimuths(self, tmp_path):
        """End to end: sun compass azimuths from orientation_magic for the McMurdo example."""
        expected = {'mc123a': 35.706, 'mc123b': 18.176, 'mc123c': 44.411, 'mc123d': 5.146,
                    'mc123e': 144.616, 'mc137a': 177.063, 'mc137b': 157.805, 'mc137c': 163.288}
        ipmag.orientation_magic(input_dir_path=os.path.join(DATA_DIR, 'orientation_magic'),
                                orient_file='orient_example.txt', hours_from_gmt=13,
                                data_model=3, output_dir_path=str(tmp_path))
        samples = pd.read_csv(tmp_path / 'samples.txt', sep='\t', header=1)
        sun = samples[samples['method_codes'].str.contains('SO-SUN')]
        azimuths = dict(zip(sun['sample'], sun['azimuth'].astype(float)))
        assert set(azimuths) == set(expected)
        for sample, azimuth in azimuths.items():
            # orientation_magic writes the azimuth to 0.1 degree
            assert abs(angle_difference(azimuth, expected[sample])) < 0.06, sample


class TestGha:
    """Tests for pmag.gha and pmag.julian."""

    def test_julian_day_of_j2000(self):
        """julian returns the julian day at noon: 2451545 for 2000-01-01."""
        assert pmag.julian(1, 1, 2000) == 2451545

    @pytest.mark.parametrize('mon, day, year, f, expected_gha, expected_dec', GHA_CASES)
    def test_reference_hour_angle_and_declination(self, mon, day, year, f, expected_gha,
                                                  expected_dec):
        """Greenwich hour angle and declination agree with astropy to 0.02 degrees."""
        greenwich_hour_angle, delta = pmag.gha(pmag.julian(mon, day, year), f)
        assert abs(angle_difference(greenwich_hour_angle, expected_gha)) < 0.02
        assert delta == pytest.approx(expected_dec, abs=0.02)
