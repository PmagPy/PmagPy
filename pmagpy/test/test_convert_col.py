"""
Tests for convert.col, the converter of Paleomagnetism.org collection (.col)
files: the treatments and method codes of the measurements, their quality and
moments, the orientation convention and its check against the directions
stored in each file, the stored fits written to the specimens table, and the
samples, sites and location. The test files are in
data_files/convert_2_magic/col_magic.
"""
import contextlib
import io
import json
import os
import unittest

from pmagpy import pmag
from pmagpy import contribution_builder as cb
from pmagpy import convert_2_magic as convert

# the root of the repository, which holds data_files and is where the output
# of the converters is written and removed again
WD = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class TestColMagic(unittest.TestCase):
    """
    Paleomagnetism.org .col files; the expected values are read off the test
    files (see data_files/convert_2_magic/col_magic/README.md).
    """

    def setUp(self):
        os.chdir(WD)
        self.input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'col_magic')
        self.filelist = ['specimens.txt', 'samples.txt', 'sites.txt', 'locations.txt',
                         'measurements.txt', 'changed.col', 'changed_2.col']

    def tearDown(self):
        pmag.remove_files(self.filelist, WD)
        os.chdir(WD)

    def read(self, table):
        return cb.MagicDataFrame(os.path.join(WD, table + '.txt')).df

    def convert(self, **kwargs):
        """convert, by default with a type for the untyped specimens of 21E.col; returns what was printed"""
        options = {'input_dir_path': self.input_dir, 'demag': 'AF'}
        options.update(kwargs)
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed):
            program_ran, outfile = convert.col(**options)
        self.assertTrue(program_ran, outfile)
        return printed.getvalue()

    def stored(self, file_name):
        """the specimens of a test file, by name"""
        with open(os.path.join(self.input_dir, file_name)) as f:
            return {spec['name']: spec for spec in json.load(f)['specimens']}

    def changed(self, file_name, change, out='changed.col'):
        """a copy of a test file, changed by change(specimens), written to the working directory"""
        with open(os.path.join(self.input_dir, file_name)) as f:
            col = json.load(f)
        change(col['specimens'])
        with open(os.path.join(WD, out), 'w') as f:
            json.dump(col, f)
        return os.path.join(WD, out)

    def measurements(self, specimen):
        meas = self.read('measurements')
        return meas[meas['specimen'] == specimen].reset_index(drop=True)

    def fits(self, specimen):
        df = self.read('specimens')
        return df[(df['specimen'] == specimen) & df['dir_tilt_correction'].notna()]

    def fit(self, specimen, tilt_correction, component=None):
        rows = self.fits(specimen)
        rows = rows[rows['dir_tilt_correction'].astype(float) == tilt_correction]
        if component is not None:
            rows = rows[rows['dir_comp'] == component]
        self.assertEqual(len(rows), 1)
        return rows.iloc[0]

    def assertDirection(self, row, vector, tolerance=1e-3, axial=False):
        stored = pmag.cart2dir([vector['x'], vector['y'], vector['z']])[:2]
        misfit = pmag.angle([float(row['dir_dec']), float(row['dir_inc'])], stored)[0]
        if axial:
            misfit = min(misfit, 180 - misfit)
        self.assertLess(misfit, tolerance)

    def test_col_with_no_files(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'pmd_magic')
        program_ran, error_message = convert.col(input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, 'no .col files found')

    def test_col_not_a_collection(self):
        input_dir = os.path.join(WD, 'data_files', 'convert_2_magic', 'rs3_magic')
        program_ran, error_message = convert.col(mag_file='PRG2-1C.rs3', input_dir_path=input_dir)
        self.assertFalse(program_ran)
        self.assertIn('is not a Paleomagnetism.org collection', error_message)

    def test_col_naming_convention_needs_z(self):
        program_ran, error_message = convert.col(input_dir_path=self.input_dir, samp_con='4')
        self.assertFalse(program_ran)
        self.assertIn('must be in form 4-Z', error_message)

    def test_col_demagnetization_type(self):
        # the two specimens of 21E.col have no type in the file and plain numbers as step labels
        program_ran, error_message = convert.col(input_dir_path=self.input_dir)
        self.assertFalse(program_ran)
        self.assertIn('2 specimen(s) have no demagnetization type (21E1A, 21E4A)', error_message)
        # a type for each specimen
        self.convert(mag_file='21E.col', demag={'21E1A': 'AF', '21E4A': 'T'})
        self.assertTrue(self.measurements('21E1A')['method_codes'].str.endswith(':LP-DIR-AF').all())
        thermal = self.measurements('21E4A')
        self.assertTrue(thermal['method_codes'].str.endswith(':LP-DIR-T').all())
        self.assertAlmostEqual(float(thermal.iloc[-1]['treat_temp']), 140 + 273)
        # a type given for all is used only where the file and the labels give none
        printed = self.convert(demag='T')
        self.assertIn('LT-AF-Z', self.measurements('28E1A').iloc[-1]['method_codes'])
        self.assertIn('LT-T-Z', self.measurements('21E1A').iloc[-1]['method_codes'])
        # ... with a warning, since its steps go to 140 only
        self.assertIn('check the type given with demag of 2 specimen(s): 21E1A (thermal, steps to 140)', printed)
        # a dictionary overrides the type in the file
        self.convert(mag_file='NE02-Circ_subset.col', demag={'NE2.12': 'AF'})
        rows = self.measurements('NE2.12')
        self.assertEqual(rows.iloc[1]['method_codes'], 'LT-AF-Z:LP-DIR-AF')
        self.assertAlmostEqual(float(rows.iloc[1]['treat_ac_field']), 0.005)

    def test_col_type_from_step_labels(self):
        # labels with units give the type: 20mT, AF 40 are alternating field; 350C, T350 thermal
        def label(specimens):
            specimens[0]['steps'] = [dict(step, step='NRM' if k == 0 else step['step'] + 'mT')
                                     for k, step in enumerate(specimens[0]['steps'])]
            specimens[1]['steps'] = [dict(step, step='T' + step['step'])
                                     for k, step in enumerate(specimens[1]['steps'])]
        path = self.changed('21E.col', label)
        self.convert(mag_file=path, demag='')
        first, last = self.measurements('21E1A').iloc[0], self.measurements('21E1A').iloc[-1]
        self.assertEqual(first['method_codes'], 'LT-NO:LP-DIR-AF')
        self.assertEqual(last['method_codes'], 'LT-AF-Z:LP-DIR-AF')
        self.assertAlmostEqual(float(last['treat_ac_field']), 0.14)
        last = self.measurements('21E4A').iloc[-1]
        self.assertEqual(last['method_codes'], 'LT-T-Z:LP-DIR-T')
        self.assertAlmostEqual(float(last['treat_temp']), 140 + 273)

    def test_col_unreadable_step_label(self):
        def label(specimens):
            specimens[0]['steps'][3]['step'] = 'x'
        path = self.changed('28E.col', label)
        program_ran, error_message = convert.col(mag_file=path)
        self.assertFalse(program_ran)
        self.assertEqual(error_message, '28E1A (changed): the treatment of step x could not be read')

    def test_col_measurements(self):
        with contextlib.redirect_stdout(io.StringIO()):
            program_ran, outfile = convert.col(input_dir_path=self.input_dir, demag='AF')
        self.assertTrue(program_ran)
        self.assertEqual(os.path.realpath(outfile), os.path.join(WD, 'measurements.txt'))
        meas = self.read('measurements')
        # 28E.col 59 steps, 21E.col 30, NE02-Circ_subset.col 90
        self.assertEqual(len(meas), 179)
        self.assertEqual(len(meas['measurement'].unique()), len(meas))
        rows = self.measurements('28E1A')
        first, last = rows.iloc[0], rows.iloc[-1]
        self.assertEqual(first['method_codes'], 'LT-NO:LP-DIR-AF')
        self.assertEqual(last['method_codes'], 'LT-AF-Z:LP-DIR-AF')
        self.assertEqual(first['experiment'], '28E1A_LP-DIR-AF')
        self.assertAlmostEqual(float(first['treat_temp']), 273)
        self.assertAlmostEqual(float(first['treat_ac_field']), 0)
        self.assertAlmostEqual(float(last['treat_ac_field']), 0.14)
        self.assertAlmostEqual(float(first['dir_dec']), 131.4, places=1)
        self.assertAlmostEqual(float(first['dir_inc']), 10.1, places=1)
        # no volume in the file: the magnetization (3810 microA/m) only
        self.assertAlmostEqual(float(first['magn_volume']), 3.81e-3)
        self.assertTrue(rows['magn_moment'].isna().all())
        # thermal steps; the NRM is at 273 K
        rows = self.measurements('NE2.11A')
        self.assertEqual(rows.iloc[0]['method_codes'], 'LT-NO:LP-DIR-T')
        self.assertAlmostEqual(float(rows.iloc[0]['treat_temp']), 273)
        self.assertEqual(rows.iloc[1]['method_codes'], 'LT-T-Z:LP-DIR-T')
        self.assertAlmostEqual(float(rows.iloc[1]['treat_temp']), 5 + 273)
        # with a volume (10.5 cm3): the magnetization and the moment
        nrm = self.measurements('NE2.1A').iloc[0]
        self.assertAlmostEqual(float(nrm['magn_volume']) / 781981.1165e-6, 1, places=6)
        self.assertAlmostEqual(float(nrm['magn_moment']) / (float(nrm['magn_volume']) * 10.5e-6), 1, places=9)
        specimens = self.read('specimens')
        self.assertAlmostEqual(float(specimens[specimens['specimen'] == 'NE2.1A'].iloc[0]['volume']), 10.5e-6)

    def test_col_quality(self):
        self.convert()
        # steps hidden in Paleomagnetism.org that no fit uses
        rows = self.measurements('28E1A')
        self.assertEqual(list(rows['quality']), ['b', 'b'] + ['g'] * 13)
        self.assertEqual(rows.iloc[0]['description'], 'hidden in Paleomagnetism.org')
        self.assertEqual(list(self.measurements('28E5B')['quality']), ['b'] * 9 + ['g'] * 5)
        # a step inside the range of a fit that the fit leaves out (35 mT of the plane of NE2.17)
        rows = self.measurements('NE2.17')
        self.assertEqual(list(rows[rows['quality'] == 'b']['treat_ac_field'].astype(float)), [0.035])
        # steps outside every fit are good
        self.assertTrue((self.measurements('28E2B')['quality'] == 'g').all())

    def test_col_quality_of_repeated_labels(self):
        # a hidden repeat of a step label: the fit uses the visible step, the hidden one is b
        def repeat(specimens):
            steps = specimens[0]['steps']
            steps.insert(5, dict(steps[4], visible=False))   # a hidden second '20'
        self.convert(mag_file=self.changed('28E.col', repeat))
        rows = self.measurements('28E1A')
        self.assertEqual(list(rows['quality'][:7]), ['b', 'b', 'g', 'g', 'g', 'b', 'g'])
        self.assertEqual(int(self.fit('28E1A', -1)['dir_n_measurements']), 11)

    def test_col_skipped_step_used_by_another_fit(self):
        def second_fit(specimens):
            fit = dict(specimens[0]['interpretations'][0], steps=['30', '40', '50'], group='second')
            specimens[0]['interpretations'][0]['steps'].remove('40')
            specimens[0]['interpretations'].append(fit)
        printed = self.convert(mag_file=self.changed('28E.col', second_fit), tolerance=180)
        self.assertIn('in 1 specimen(s) a fit cannot be re-made from the measurements', printed)
        self.assertIn('28E1A', printed)
        # the step is used by the second fit, so it stays good
        self.assertTrue((self.measurements('28E1A')['quality'][2:] == 'g').all())

    def test_col_assumed_volumes(self):
        def assumed(specimens):
            # a JR6 file, whose importer sets 10 cm3: magnetizations only
            specimens[0].update(format='JR6', volume=10)
            # moments read with an assumed volume (Paleomagnetism.org's MagIC import): moments only
            specimens[1].update(volume=10, volumeAssumed=True)
            # Utrecht files imported by 2.0.0-2.0.1 hold moments (pAm2)
            specimens[2].update(format='UTRECHT', version='2.0.1', volume=10.5)
        self.convert(mag_file=self.changed('28E.col', assumed))
        steps = self.stored('28E.col')
        length = pmag.cart2dir([steps['28E1A']['steps'][0][k] for k in 'xyz'])[2]
        nrm = self.measurements('28E1A').iloc[0]
        self.assertAlmostEqual(float(nrm['magn_volume']), length * 1e-6)
        self.assertTrue(self.measurements('28E1A')['magn_moment'].isna().all())
        length = pmag.cart2dir([steps['28E2B']['steps'][0][k] for k in 'xyz'])[2]
        nrm = self.measurements('28E2B').iloc[0]
        self.assertAlmostEqual(float(nrm['magn_moment']) / (length * 1e-12 * 10), 1, places=9)
        self.assertTrue(self.measurements('28E2B')['magn_volume'].isna().all())
        length = pmag.cart2dir([steps['28E4A']['steps'][0][k] for k in 'xyz'])[2]
        nrm = self.measurements('28E4A').iloc[0]
        self.assertAlmostEqual(float(nrm['magn_moment']) / (length * 1e-12), 1, places=9)
        self.assertAlmostEqual(float(nrm['magn_volume']) / (length * 1e-12 / 10.5e-6), 1, places=9)
        specimens = self.read('specimens').set_index('specimen')
        self.assertTrue(specimens.loc[['28E1A', '28E2B'], 'volume'].isna().all())

    def test_col_orientation(self):
        self.convert()
        samples = self.read('samples').set_index('sample')
        # coreDip = 90 + dip; coreDip -5 gives a dip of -95
        self.assertAlmostEqual(float(samples.loc['28E4A', 'azimuth']), 232.8)
        self.assertAlmostEqual(float(samples.loc['28E4A', 'dip']), -95)
        # bedding strike 45, dip 40 (right-hand rule)
        self.assertAlmostEqual(float(samples.loc['28E4A', 'bed_dip_direction']), 135)
        self.assertAlmostEqual(float(samples.loc['28E4A', 'bed_dip']), 40)
        self.assertAlmostEqual(float(samples.loc['28E4A', 'lon']), 360 - 63.0315)
        # the stored geographic and tectonic directions are written, and reproduced by the orientation
        stored = self.stored('28E.col')['28E4A']['interpretations'][0]
        for tilt_correction, frame in ((-1, 'specimen'), (0, 'geographic'), (100, 'tectonic')):
            self.assertDirection(self.fit('28E4A', tilt_correction), stored[frame]['coordinates'])
        row = self.fit('28E4A', -1)
        geographic = pmag.dogeo(float(row['dir_dec']), float(row['dir_inc']),
                                float(samples.loc['28E4A', 'azimuth']), float(samples.loc['28E4A', 'dip']))
        self.assertDirection({'dir_dec': geographic[0], 'dir_inc': geographic[1]}, stored['geographic']['coordinates'])

    def test_col_orientation_check(self):
        # a changed core azimuth no longer reproduces the stored geographic directions
        def turn(specimens):
            specimens[0]['coreAzimuth'] += 10
        path = self.changed('28E.col', turn)
        program_ran, error_message = convert.col(mag_file=path)
        self.assertFalse(program_ran)
        self.assertIn('28E1A (changed): a fit rotated with the converted orientation differs from the '
                      'geographic direction stored in the file by 8.1 degrees', error_message)

    def test_col_fits(self):
        self.convert()
        # a free line: DE-BFL, MAD in dir_mad_free, and DANG
        row = self.fit('28E1A', -1)
        self.assertEqual(row['method_codes'], 'LP-DIR-AF:DE-BFL:DA-DIR')
        self.assertEqual(row['dir_comp'], 'ChRM')
        self.assertAlmostEqual(float(row['dir_mad_free']), 2.2518, places=4)
        self.assertEqual(int(row['dir_n_measurements']), 11)
        self.assertAlmostEqual(float(row['meas_step_min']), 0.02)
        self.assertAlmostEqual(float(row['meas_step_max']), 0.14)
        self.assertEqual(row['meas_step_unit'], 'T')
        self.assertGreaterEqual(float(row['dir_dang']), 0)
        self.assertEqual(row['software_packages'], 'Paleomagnetism.org 2.4.0')
        self.assertEqual(self.fit('28E1A', 0)['method_codes'], 'LP-DIR-AF:DE-BFL:DA-DIR-GEO')
        self.assertEqual(self.fit('28E1A', 100)['method_codes'], 'LP-DIR-AF:DE-BFL:DA-DIR-TILT')
        # an anchored line
        row = self.fit('28E4A', -1)
        self.assertEqual(row['method_codes'], 'LP-DIR-AF:DE-BFL-A:DA-DIR')
        self.assertAlmostEqual(float(row['dir_mad_anc']), 1.3229, places=4)
        # a plane: the pole, in three coordinate systems
        stored = self.stored('NE02-Circ_subset.col')['NE2.17']['interpretations'][0]
        for tilt_correction, frame in ((-1, 'specimen'), (0, 'geographic'), (100, 'tectonic')):
            row = self.fit('NE2.17', tilt_correction)
            self.assertIn('DE-BFP', row['method_codes'])
            self.assertDirection(row, stored[frame]['coordinates'], axial=True)
            self.assertEqual(row['description'], 'pole to the best-fit plane through the origin')
        # a plane fitted to a mean direction: the fitted line is in the description
        self.assertEqual(len(self.fits('NE2.11B')), 3)
        self.assertIn('fitted to a mean direction', self.fit('NE2.11B', 0)['description'])
        # specimens without fits: one row with the step range
        specimens = self.read('specimens')
        rows = specimens[specimens['specimen'] == '28E2B']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows.iloc[0]['method_codes'], 'LP-DIR-AF')
        self.assertAlmostEqual(float(rows.iloc[0]['meas_step_max']), 0.14)
        # without interpretations
        self.convert(interpretations=False)
        self.assertEqual(len(self.read('specimens')), 12)

    def test_col_components_numbered(self):
        def second_fit(specimens):
            specimens[0]['interpretations'].append(dict(specimens[0]['interpretations'][0],
                                                        steps=['80', '100', '120', '140']))
        self.convert(mag_file=self.changed('28E.col', second_fit))
        self.assertEqual(sorted(set(self.fits('28E1A')['dir_comp'])), ['ChRM', 'ChRM_2'])
        self.assertAlmostEqual(float(self.fit('28E1A', -1, 'ChRM_2')['meas_step_min']), 0.08)

    def test_col_fits_remade_from_measurements(self):
        # as zeq_magic does: pmag.domean from meas_step_min to meas_step_max, b steps left out
        self.convert()
        meas, specimens = self.read('measurements'), self.read('specimens')
        lines = specimens[specimens['method_codes'].str.contains('DE-BFL') &
                          (specimens['dir_tilt_correction'].astype(float) == -1)]
        self.assertEqual(len(lines), 6)
        for _, fit in lines.iterrows():
            rows = meas[meas['experiment'] == fit['experiments']].reset_index(drop=True)
            column = 'treat_ac_field' if fit['meas_step_unit'] == 'T' else 'treat_temp'
            treatments = list(rows[column].astype(float))
            moment = rows['magn_moment'].fillna(rows['magn_volume']) if 'magn_moment' in rows else rows['magn_volume']
            block = [[treatments[k], float(rows.loc[k, 'dir_dec']), float(rows.loc[k, 'dir_inc']),
                      float(moment[k]), '', rows.loc[k, 'quality']] for k in range(len(rows))]
            start, end = treatments.index(float(fit['meas_step_min'])), treatments.index(float(fit['meas_step_max']))
            code = [c for c in fit['method_codes'].split(':') if c.startswith('DE-')][0]
            mpars = pmag.domean(block, start, end, code)
            misfit = pmag.angle([mpars['specimen_dec'], mpars['specimen_inc']],
                                [float(fit['dir_dec']), float(fit['dir_inc'])])[0]
            self.assertLess(misfit, 1e-3, fit['specimen'])
            self.assertEqual(mpars['specimen_n'], int(fit['dir_n_measurements']))

    def test_col_samples_sites_and_location(self):
        self.convert()
        # the default site is the collection
        sites = self.read('sites').set_index('site')
        self.assertEqual(sorted(sites.index), ['21E', '28E', 'NE02-Circ_subset'])
        site = sites.loc['NE02-Circ_subset']
        self.assertEqual(site['lithologies'], 'Basalt:Silty Clay')
        self.assertEqual(site['geologic_classes'], 'Igneous:Sedimentary')
        self.assertEqual(site['geologic_types'], 'Not Specified')
        self.assertEqual(site['location'], 'unknown')
        self.assertAlmostEqual(float(site['age']), 74)
        self.assertAlmostEqual(float(site['age_low']), 70.6)
        self.assertAlmostEqual(float(site['age_high']), 77)
        self.assertEqual(site['age_unit'], 'Ma')
        self.assertAlmostEqual(float(site['lat']), 43.370818)
        samples = self.read('samples').set_index('sample')
        self.assertEqual(samples.loc['NE2.11A', 'site'], 'NE02-Circ_subset')
        self.assertEqual(samples.loc['NE2.11A', 'method_codes'], 'LP-DIR-T')
        self.assertEqual(samples.loc['28E1A', 'geologic_classes'], 'Intrusive')
        # one location holds all sites: the Caribbean and Japan, across 180 degrees
        locations = self.read('locations')
        self.assertEqual(len(locations), 1)
        location = locations.iloc[0]
        self.assertEqual(location['location_type'], 'Region')
        self.assertAlmostEqual(float(location['lat_s']), 18.0261111)
        self.assertAlmostEqual(float(location['lat_n']), 43.370818)
        self.assertAlmostEqual(float(location['lon_w']), 145.633416)
        self.assertAlmostEqual(float(location['lon_e']), 360 - 63.0315)
        self.assertAlmostEqual(float(location['age_low']), 27)
        self.assertAlmostEqual(float(location['age_high']), 77)
        self.assertEqual(location['method_codes'], 'LP-DIR-AF:LP-DIR-T')
        # a naming convention: here each sample is its own site
        self.convert(samp_con='5', location='Test area', location_type='Outcrop')
        self.assertEqual(len(self.read('sites')), 12)
        self.assertEqual(set(self.read('sites')['location']), {'Test area'})
        self.assertEqual(self.read('locations').iloc[0]['location_type'], 'Outcrop')

    def test_col_metadata_for_what_the_files_lack(self):
        def strip(specimens):
            for spec in specimens:
                spec.update(latitude=None, longitude=None, age=None, ageMin=None, ageMax=None,
                            geology=None, lithology=None)
        self.convert(mag_file=self.changed('28E.col', strip), lat=10, lon=-20, age=5, age_low=4, age_high=6,
                     geologic_classes='Igneous', geologic_types='Lava Flow', lithologies='Basalt',
                     citations='10.1000/example', meth_code='FS-FD:SO-MAG', user='analyst')
        site = self.read('sites').iloc[0]
        self.assertAlmostEqual(float(site['lat']), 10)
        self.assertAlmostEqual(float(site['lon']), 340)
        self.assertAlmostEqual(float(site['age']), 5)
        self.assertAlmostEqual(float(site['age_low']), 4)
        self.assertEqual((site['geologic_classes'], site['geologic_types'], site['lithologies']),
                         ('Igneous', 'Lava Flow', 'Basalt'))
        sample = self.read('samples').iloc[0]
        self.assertEqual(sample['method_codes'], 'LP-DIR-AF:FS-FD:SO-MAG')
        self.assertEqual(sample['analysts'], 'analyst')
        location = self.read('locations').iloc[0]
        self.assertEqual(location['location_type'], 'Outcrop')
        self.assertEqual(location['lithologies'], 'Basalt')
        for table in ('measurements', 'specimens', 'samples', 'sites', 'locations'):
            self.assertEqual(set(self.read(table)['citations']), {'10.1000/example'})
        # what the files give is kept
        self.convert(mag_file='28E.col', lat=10, lon=-20, age=5, lithologies='Basalt')
        site = self.read('sites').iloc[0]
        self.assertAlmostEqual(float(site['lat']), 18.0307222, places=6)
        self.assertAlmostEqual(float(site['age']), 28.5)
        self.assertEqual(site['lithologies'], 'Andesite')
        # without a lithology the column is left empty, to be filled in before uploading
        self.convert(mag_file=self.changed('28E.col', strip))
        self.assertTrue(self.read('sites')['lithologies'].isna().all() if 'lithologies' in self.read('sites')
                        else True)
        self.assertEqual(self.read('sites').iloc[0]['geologic_classes'], 'Not Specified')

    def test_col_orientation_conflicts(self):
        def same_sample(specimens):
            specimens[1]['sample'] = specimens[0]['sample']
        printed = self.convert(mag_file=self.changed('28E.col', same_sample))
        self.assertIn('1 sample(s) have specimens (or copies of a specimen) with different orientations', printed)
        self.assertEqual(len(self.read('samples')), 3)

    def test_col_same_specimen_in_two_files(self):
        # the same file twice: each specimen and fit is written once
        self.convert(mag_file=['28E.col', '28E.col'])
        self.assertEqual(len(self.read('measurements')), 59)
        self.assertEqual(len(self.fits('28E1A')), 3)
        # a copy with other measurements is a further experiment of the specimen
        def remeasured(specimens):
            for step in specimens[0]['steps']:
                step['x'] *= 2
        self.convert(mag_file=['28E.col', self.changed('28E.col', remeasured)])
        meas = self.measurements('28E1A')
        self.assertEqual(sorted(set(meas['experiment'])), ['28E1A_LP-DIR-AF', '28E1A_LP-DIR-AF_2'])
        self.assertEqual(len(self.read('measurements')), 59 + 15)
        self.assertEqual(len(self.read('measurements')['measurement'].unique()), 59 + 15)


if __name__ == '__main__':
    unittest.main()
