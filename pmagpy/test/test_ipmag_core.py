import unittest
import random
from contextlib import redirect_stdout
from io import StringIO

import matplotlib
matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

import numpy as np
from numpy.testing import assert_allclose

from pmagpy import ipmag


class TestIpMagCoreFunctions(unittest.TestCase):

    def setUp(self):
        np.random.seed(0)
        random.seed(0)

    def _seed(self, seed):
        np.random.seed(seed)
        random.seed(seed)

    def test_make_di_block_unit_vectors(self):
        dec = [180.3, 179.2]
        inc = [12.1, 13.7]
        expected = [[180.3, 12.1, 1.0], [179.2, 13.7, 1.0]]
        self.assertEqual(ipmag.make_di_block(dec, inc), expected)

    def test_make_di_block_non_unit_vectors(self):
        dec = [180.3, 179.2]
        inc = [12.1, 13.7]
        expected = [[180.3, 12.1], [179.2, 13.7]]
        self.assertEqual(ipmag.make_di_block(dec, inc, unit_vector=False), expected)

    def test_unpack_di_block_returns_components(self):
        di_block = [[180.3, 12.1, 0.5], [179.2, 13.7, 0.7]]
        dec, inc, moment = ipmag.unpack_di_block(di_block)
        assert_allclose(dec, [180.3, 179.2])
        assert_allclose(inc, [12.1, 13.7])
        assert_allclose(moment, [0.5, 0.7])

    def test_unpack_di_block_handles_missing_moment(self):
        di_block = [[10.0, 20.0], [30.0, 40.0]]
        dec, inc, moment = ipmag.unpack_di_block(di_block)
        assert_allclose(dec, [10.0, 30.0])
        assert_allclose(inc, [20.0, 40.0])
        self.assertEqual(moment, [])

    def test_do_flip_with_lists_returns_antipodes(self):
        dec_flip, inc_flip = ipmag.do_flip([1.0, 358.0], [10.0, -5.0])
        assert_allclose(dec_flip, [181.0, 178.0])
        assert_allclose(inc_flip, [-10.0, 5.0])

    def test_do_flip_with_di_block_preserves_unit_vectors(self):
        di_block = [[10.0, 20.0, 0.7], [350.0, -30.0, 0.4]]
        flipped = ipmag.do_flip(di_block=di_block)
        expected = np.array([[190.0, -20.0, 1.0], [170.0, 30.0, 1.0]])
        assert_allclose(np.array(flipped), expected)

    def test_make_diddd_array_shapes_and_values(self):
        dec = [132.5, 124.3]
        inc = [12.1, 23.2]
        dip_direction = [265.0, 164.0]
        dip = [20.0, 72.0]
        result = ipmag.make_diddd_array(dec, inc, dip_direction, dip)
        expected = np.array(
            [[132.5, 12.1, 265.0, 20.0],
             [124.3, 23.2, 164.0, 72.0]],
            dtype=float,
        )
        self.assertEqual(result.shape, (2, 4))
        self.assertEqual(result.dtype.kind, "f")
        assert_allclose(result, expected)

    def test_f_factor_calc_matches_doc_example(self):
        f_factor = ipmag.f_factor_calc(25, 40)
        assert_allclose(f_factor, 0.5557238268604126)

    def test_lat_from_inc_without_uncertainty(self):
        paleo_lat = ipmag.lat_from_inc(45)
        assert_allclose(paleo_lat, 26.56505117707799)

    def test_lat_from_inc_with_uncertainty_returns_bounds(self):
        paleo_lat, paleo_lat_max, paleo_lat_min = ipmag.lat_from_inc(20, a95=5)
        assert_allclose(
            [paleo_lat, paleo_lat_max, paleo_lat_min],
            [10.314104815618196, 13.12426812279171, 7.630740212430057],
        )

    def test_inc_from_lat_matches_inverse_relation(self):
        inc = ipmag.inc_from_lat(45)
        assert_allclose(inc, 63.434948822922)

    def test_lat_from_pole_simple_geometry(self):
        self.assertAlmostEqual(ipmag.lat_from_pole(0, 30, 0, 90), 30.0)
        self.assertAlmostEqual(ipmag.lat_from_pole(0, 0, 0, 90), 0.0, places=9)

    def test_dms2dd(self):
        self.assertAlmostEqual(ipmag.dms2dd(180, 4, 23), 180.07305555555556)

    def test_squish_matches_doc_example(self):
        inclinations = [43, 47, 41]
        squished = ipmag.squish(inclinations, 0.4)
        assert_allclose(
            squished,
            [20.455818908027187, 23.216791019112204, 19.17331436017231],
        )

    def test_unsquish_inverts_squish(self):
        inclinations = [43, 47, 41]
        squished = ipmag.squish(inclinations, 0.4)
        unsquished = ipmag.unsquish(squished, 0.4)
        assert_allclose(unsquished, [43.0, 47.0, 41.0])

    def test_fisher_mean_matches_doc_example(self):
        result = ipmag.fisher_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            "dec": 136.30838974272072,
            "inc": 21.34778402689999,
            "n": 4,
            "r": 3.9812138971889026,
            "k": 159.69251473636305,
            "alpha95": 7.292891411309177,
            "csd": 6.40977432113409,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(float(result[key]), value, places=12)

    def test_fisher_mean_with_di_block_matches_lists(self):
        list_result = ipmag.fisher_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        block_result = ipmag.fisher_mean(
            di_block=[[140, 21], [127, 23], [142, 19], [136, 22]]
        )
        for key in ("dec", "inc", "k", "alpha95"):
            self.assertAlmostEqual(float(list_result[key]), float(block_result[key]), places=12)

    def test_fisher_angular_deviation_confidence_levels(self):
        data_kwargs = {"dec": [140, 127, 142, 136], "inc": [21, 23, 19, 22]}
        result_95 = ipmag.fisher_angular_deviation(confidence=95, **data_kwargs)
        result_63 = ipmag.fisher_angular_deviation(confidence=63, **data_kwargs)
        result_50 = ipmag.fisher_angular_deviation(confidence=50, **data_kwargs)
        assert_allclose(result_95, 11.078622283441636)
        assert_allclose(result_63, 6.40977432113409)
        assert_allclose(result_50, 5.3414786009450745)

    def test_bingham_mean_matches_doc_example(self):
        result = ipmag.bingham_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            "dec": 136.32637167111312,
            "inc": 21.345186780731787,
            "Edec": 220.84075754194578,
            "Einc": -13.745780972597775,
            "Zdec": 280.38894136954474,
            "Zinc": 64.23509410796224,
            "n": 4,
            "Zeta": 9.865337027645111,
            "Eta": 9.911152230693874,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(float(result[key]), value, places=12)

    def test_kent_mean_matches_doc_example(self):
        result = ipmag.kent_mean(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            "dec": 136.30838974272072,
            "inc": 21.34778402689999,
            "n": 4,
            "Zdec": 40.824690028412704,
            "Zinc": 13.739412321974202,
            "Edec": 280.3868355366877,
            "Einc": 64.23659892174419,
            "Zeta": 6.789682324100879,
            "Eta": 0.7298211276091953,
            "R1": 0.9953034742972257,
            "R2": 0.009136654495119367,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(float(result[key]), value, places=12)

    def test_kent_distribution_95_matches_doc_example(self):
        result = ipmag.kent_distribution_95(dec=[140, 127, 142, 136], inc=[21, 23, 19, 22])
        expected = {
            "dec": 136.30838974272072,
            "inc": 21.34778402689999,
            "n": 4,
            "Zdec": 40.824690028412704,
            "Zinc": 13.739412321974202,
            "Edec": 280.3868355366877,
            "Einc": 64.23659892174419,
            "Zeta": 13.677129096579474,
            "Eta": 1.459760703119634,
            "R1": 0.9953034742972257,
            "R2": 0.009136654495119367,
        }
        for key, value in expected.items():
            self.assertAlmostEqual(float(result[key]), value, places=12)

    def test_fishrot_generates_expected_vectors(self):
        self._seed(0)
        data = ipmag.fishrot(k=20, n=5, dec=40, inc=60)
        expected = np.array([
            [44.36493330003563, 46.16886431577514, 1.0],
            [24.021132866372227, 54.0347768434274, 1.0],
            [65.98129870439303, 59.940719510954295, 1.0],
            [68.66482234451149, 65.94811708013496, 1.0],
            [10.801333674957533, 53.956088740026516, 1.0],
        ])
        assert_allclose(data, expected)

    def test_fishrot_returns_dec_inc_arrays(self):
        self._seed(0)
        decs, incs = ipmag.fishrot(k=20, n=5, dec=40, inc=60, di_block=False)
        expected_dec = np.array([44.36493330003563, 24.021132866372227, 65.98129870439303,
                                 68.66482234451149, 10.801333674957533])
        expected_inc = np.array([46.16886431577514, 54.0347768434274, 59.940719510954295,
                                 65.94811708013496, 53.956088740026516])
        assert_allclose(decs, expected_dec)
        assert_allclose(incs, expected_inc)

    def test_fisher_mean_resample_returns_expected_di_block(self):
        self._seed(0)
        data = ipmag.fisher_mean_resample(alpha95=5, n=5, dec=40, inc=60)
        expected = np.array([
            [44.307243604101245, 59.44245287434259, 1.0],
            [41.081694976120616, 58.01758612877827, 1.0],
            [44.052863563455446, 58.30320609082041, 1.0],
            [43.52516750328056, 62.00145090464721, 1.0],
            [39.264700146167485, 59.58393196018479, 1.0],
        ])
        assert_allclose(np.array(data), expected)

    def test_fisher_mean_resample_returns_dec_and_inc_lists(self):
        self._seed(0)
        decs, incs = ipmag.fisher_mean_resample(alpha95=5, n=5, dec=40, inc=60, di_block=False)
        expected_dec = np.array([44.307243604101245, 41.081694976120616, 44.052863563455446,
                                 43.52516750328056, 39.264700146167485])
        expected_inc = np.array([59.44245287434259, 58.01758612877827, 58.30320609082041,
                                 62.00145090464721, 59.58393196018479])
        assert_allclose(decs, expected_dec)
        assert_allclose(incs, expected_inc)

    def test_kentrot_generates_expected_vectors(self):
        self._seed(0)
        kent_input = {
            'dec': 40.824690028412704,
            'inc': 13.739412321974202,
            'Zdec': 136.30838974272072,
            'Zinc': 21.34778402689999,
            'Edec': 280.3868355366877,
            'Einc': 64.23659892174419,
            'R1': 0.9953034742972257,
            'R2': 0.009136654495119367,
        }
        data = ipmag.kentrot(kent_input, n=5)
        expected = np.array([
            [44.39447120932218, 14.245240388482694, 1.0],
            [39.80987633351043, 13.433792471508278, 1.0],
            [45.253025683947214, 15.62450620530529, 1.0],
            [36.34624870281844, 12.032592045340236, 1.0],
            [42.19975931544283, 14.362529462258678, 1.0],
        ])
        assert_allclose(np.array(data), expected)

    def test_kentrot_returns_dec_and_inc_lists(self):
        self._seed(0)
        kent_input = {
            'dec': 40.824690028412704,
            'inc': 13.739412321974202,
            'Zdec': 136.30838974272072,
            'Zinc': 21.34778402689999,
            'Edec': 280.3868355366877,
            'Einc': 64.23659892174419,
            'R1': 0.9953034742972257,
            'R2': 0.009136654495119367,
        }
        decs, incs = ipmag.kentrot(kent_input, n=5, di_block=False)
        expected_dec = np.array([44.39447120932218, 39.80987633351043, 45.253025683947214,
                                 36.34624870281844, 42.19975931544283])
        expected_inc = np.array([14.245240388482694, 13.433792471508278, 15.62450620530529,
                                 12.032592045340236, 14.362529462258678])
        assert_allclose(decs, expected_dec)
        assert_allclose(incs, expected_inc)

    def test_tk03_returns_expected_vectors(self):
        self._seed(0)
        data = ipmag.tk03(n=5, dec=0, lat=0, rev='no')
        expected = np.array([
            [19.513424376252786, 18.18060061952153, 8807.756714571922],
            [1.4626664652715335, 0.7404291657324288, 31136.233258481992],
            [359.55634729793707, -5.569125230598204, 24593.306782132815],
            [354.7762475810901, 2.7914575172515, 25711.103695867663],
            [12.413299649834231, -0.021150016987683644, 18500.50399470462],
        ])
        array_data = np.array(data)
        assert_allclose(array_data, expected)
        self.assertTrue(np.all(array_data[:, 2] > 0))

    def test_mean_bootstrap_confidence_returns_bounds(self):
        self._seed(0)
        pars, boundary = ipmag.mean_bootstrap_confidence(
            dec=[40, 41, 39, 38, 42],
            inc=[60, 61, 59, 62, 58],
            num_sims=20,
        )
        self.assertIn("dec", pars)
        assert_allclose(float(pars["dec"]), 40.03627966362325)
        assert_allclose(float(pars["inc"]), 60.0075508357781)
        assert_allclose(float(pars["T_critical"]), 22.516075590053603)
        boundary_array = np.array(boundary)
        self.assertEqual(boundary_array.shape[1], 3)
        self.assertGreater(boundary_array.shape[0], 100)

    def test_common_mean_bootstrap_identifies_common_mean(self):
        self._seed(0)
        data1 = ipmag.fishrot(k=40, n=20, dec=40, inc=60)
        self._seed(1)
        data2 = ipmag.fishrot(k=45, n=20, dec=40, inc=60)
        self._seed(2)
        result = ipmag.common_mean_bootstrap(data1, data2, NumSims=20, verbose=False)
        self.assertEqual(result, 1)

    def test_common_mean_bootstrap_detects_difference(self):
        self._seed(0)
        data1 = ipmag.fishrot(k=40, n=20, dec=200, inc=-20)
        self._seed(1)
        data2 = ipmag.fishrot(k=45, n=20, dec=20, inc=60)
        self._seed(3)
        result = ipmag.common_mean_bootstrap(data1, data2, NumSims=20, verbose=False)
        self.assertEqual(result, 0)

    def test_common_mean_bootstrap_handles_single_direction(self):
        self._seed(0)
        data1 = ipmag.fishrot(k=40, n=20, dec=40, inc=60)
        self._seed(4)
        result = ipmag.common_mean_bootstrap(data1, [40, 60], NumSims=20, verbose=False)
        self.assertEqual(result, 1)

    def test_common_mean_bootstrap_h23_returns_expected_tuple(self):
        self._seed(5)
        data1 = ipmag.fishrot(k=35, n=15, dec=30, inc=50)
        self._seed(6)
        data2 = ipmag.fishrot(k=37, n=15, dec=32, inc=51)
        self._seed(7)
        result = ipmag.common_mean_bootstrap_H23(
            data1,
            data2,
            num_sims=25,
            alpha=0.1,
            plot=False,
            verbose=False,
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 4)

    def test_common_mean_watson_pass_and_fail(self):
        self._seed(11)
        data1 = ipmag.fishrot(k=40, n=10, dec=40, inc=60)
        self._seed(12)
        data2 = ipmag.fishrot(k=45, n=10, dec=41, inc=59)
        # seed again before Monte Carlo simulation
        self._seed(13)
        with redirect_stdout(StringIO()):
            pass_result = ipmag.common_mean_watson(data1, data2, NumSims=25, plot='no')
        self.assertEqual(pass_result[0], 1)
        self.assertIn(pass_result[3], {'A', 'B', 'C', 'indeterminate'})

        self._seed(14)
        data3 = ipmag.fishrot(k=10, n=10, dec=200, inc=-30)
        self._seed(15)
        data4 = ipmag.fishrot(k=10, n=10, dec=20, inc=40)
        self._seed(16)
        with redirect_stdout(StringIO()):
            fail_result = ipmag.common_mean_watson(data3, data4, NumSims=25, plot='no')
        self.assertEqual(fail_result[0], 0)
        self.assertEqual(fail_result[3], '')

    def test_common_mean_bayes_support_messages(self):
        self._seed(17)
        data1 = ipmag.fishrot(k=40, n=15, dec=45, inc=55)
        self._seed(18)
        data2 = ipmag.fishrot(k=42, n=15, dec=46, inc=54)
        buf = StringIO()
        with redirect_stdout(buf):
            bayes_pass = ipmag.common_mean_bayes(data1, data2)
        self.assertGreater(bayes_pass[1], 0.5)
        self.assertIn('Common mean', bayes_pass[2])

        self._seed(19)
        data3 = ipmag.fishrot(k=20, n=15, dec=120, inc=-30)
        self._seed(20)
        data4 = ipmag.fishrot(k=20, n=15, dec=320, inc=30)
        buf = StringIO()
        with redirect_stdout(buf):
            bayes_fail = ipmag.common_mean_bayes(data3, data4)
        self.assertLess(bayes_fail[1], 0.1)
        self.assertIn('Different means', bayes_fail[2])

    def test_separate_directions_splits_modes(self):
        self._seed(21)
        decs_n, incs_n = ipmag.fishrot(k=30, n=8, dec=10, inc=45, di_block=False)
        self._seed(22)
        decs_r, incs_r = ipmag.fishrot(k=30, n=8, dec=200, inc=-45, di_block=False)
        all_dec = list(decs_n) + list(decs_r)
        all_inc = list(incs_n) + list(incs_r)
        dec1, inc1, dec2, inc2 = ipmag.separate_directions(dec=all_dec, inc=all_inc)
        self.assertEqual(len(dec1), 8)
        self.assertEqual(len(dec2), 8)
        self.assertGreater(np.mean(inc1), 0)
        self.assertLess(np.mean(inc2), 0)

    def test_plot_net_and_plot_di_execute_without_error(self):
        self._seed(23)
        di_block = ipmag.fishrot(k=20, n=10, dec=40, inc=60).tolist()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ipmag.plot_net(ax=ax)
        ipmag.plot_di(di_block=di_block, color='g', marker='^', connect_points=True)
        self.assertEqual(len(fig.axes), 1)
        plt.close(fig)

    def test_reversal_test_bootstrap_passes_for_antipodal_data(self):
        self._seed(24)
        normal = ipmag.fishrot(k=30, n=12, dec=40, inc=60)
        self._seed(25)
        reverse = ipmag.fishrot(k=30, n=12, dec=220, inc=-60)
        combined = np.vstack((normal, reverse)).tolist()
        self._seed(26)
        result = ipmag.reversal_test_bootstrap(di_block=combined, verbose=False)
        self.assertEqual(result, 1)

    def test_reversal_test_bootstrap_h23_returns_tuple(self):
        self._seed(27)
        normal = ipmag.fishrot(k=30, n=12, dec=40, inc=60)
        self._seed(28)
        reverse = ipmag.fishrot(k=30, n=12, dec=220, inc=-60)
        combined = np.vstack((normal, reverse)).tolist()
        self._seed(29)
        result = ipmag.reversal_test_bootstrap_H23(
            di_block=combined,
            num_sims=20,
            alpha=0.1,
            plot=False,
            verbose=False,
        )
        self.assertEqual(result[0], 1)
        self.assertEqual(len(result), 4)

    def test_reversal_test_mm1990_runs(self):
        self._seed(30)
        normal = ipmag.fishrot(k=20, n=6, dec=40, inc=60)
        self._seed(31)
        reverse = ipmag.fishrot(k=20, n=6, dec=220, inc=-60)
        combined = np.vstack((normal, reverse)).tolist()
        self._seed(32)
        with redirect_stdout(StringIO()):
            result = ipmag.reversal_test_MM1990(di_block=combined, plot_CDF=False, plot_stereo=False)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[0], 1)

    def test_fishqq_returns_summary(self):
        self._seed(33)
        directions = ipmag.fishrot(k=40, n=15, dec=200, inc=50).tolist()
        summary = ipmag.fishqq(di_block=directions, plot=True, save=False)
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get('Mode'), 'Mode 1')
        self.assertGreater(summary.get('N', 0), 10)
        plt.close('all')

    def test_igrf_print_formats_output(self):
        buffer = StringIO()
        with redirect_stdout(buffer):
            ipmag.igrf_print([14.314, 61.483, 48992.647])
        output = buffer.getvalue().strip().splitlines()
        self.assertIn('Declination: 14.314', output[0])
        self.assertIn('Inclination: 61.483', output[1])
        self.assertIn('Intensity: 48992.647 nT', output[2])


if __name__ == "__main__":
    unittest.main()
