"""
Tests for the hysteresis loop processing suite in rockmag.py.

The processing follows the protocol of Jackson and Solheid (2010,
doi:10.1029/2009GC002932): loop gridding, symmetry-based centering, the Q
signal-to-noise quality factor, drift correction, whole-loop and high-field
linearity F tests, loop closure testing, and linear vs. nonlinear
(approach-to-saturation) high-field fitting. Synthetic loops with known
parameters (Ms, Mr, Bc, chi_HF) provide analytical expectations.
"""
import numpy as np
import pytest

from pmagpy import rockmag as rmag


RNG = np.random.default_rng(2026)


def synthetic_loop(n_half=200, Hmax=1.0, Ms=1.0, Bc=0.05, w=0.03, chi=0.0,
                   noise=0.0, H_offset=0.0, M_offset=0.0, drift=0.0,
                   hard_Ms=0.0, hard_Bc=0.7, hard_w=0.5,
                   ats_alpha=0.0, rng=RNG):
    """Two-branch synthetic loop measured +Hmax -> -Hmax -> +Hmax.

    The ferromagnetic component is Ms*tanh((H +/- Bc)/w), so the remanence is
    Mr = Ms*tanh(Bc/w) and the branch zero crossings are at -/+Bc when no
    other contributions are added. Optional contributions:
      chi       linear (paramagnetic) slope in raw slope units (M per T)
      noise     gaussian measurement noise
      H_offset  horizontal loop shift (e.g. sensor offset)
      M_offset  vertical loop shift
      drift     linear-in-time drift amplitude accumulated over the loop
      hard_Ms   wide-coercivity component that stays open at Hmax
      ats_alpha approach-to-saturation curvature -alpha/H applied smoothly
                above 0.3*Hmax (unsaturated ferromagnetic moment)
    """
    H_upper = np.linspace(Hmax, -Hmax, n_half)
    H_lower = np.linspace(-Hmax, Hmax, n_half)

    def branch(H, sign):
        M = Ms * np.tanh((H + sign * Bc) / w)
        if hard_Ms != 0.0:
            M = M + hard_Ms * np.tanh((H + sign * hard_Bc) / hard_w)
        if ats_alpha != 0.0:
            # curvature only where the tanh is saturated, tapering smoothly
            # to zero below 0.3*Hmax so low fields are not distorted
            taper = 0.5 * (1 + np.tanh((np.abs(H) - 0.3 * Hmax) / (0.1 * Hmax)))
            M = M - ats_alpha * taper * np.sign(H) / np.maximum(np.abs(H), 0.3 * Hmax)
        return M + chi * H

    H = np.concatenate([H_upper, H_lower]) + H_offset
    M = np.concatenate([branch(H_upper, +1), branch(H_lower, -1)]) + M_offset
    M = M + drift * np.linspace(0, 1, M.size)
    if noise:
        M = M + noise * rng.standard_normal(M.size)
    return H, M


class TestTurningPointAndPlateaus:
    """Robust branch splitting (issue #876): plateaus, glitches, and the
    plateau-collapse helper."""

    def test_turning_point_simple(self):
        H, M = synthetic_loop()
        tp = rmag.find_hysteresis_turning_point(H)
        assert H[tp] == pytest.approx(np.min(H))
        assert np.all(np.diff(H[:tp + 1]) <= 0)
        assert np.all(np.diff(H[tp + 1:]) >= 0)

    def test_turning_point_with_tip_plateaus(self):
        # repeated field readings at the loop tips, as recorded by a VSM
        # holding the field while averaging
        H, M = synthetic_loop()
        H_rep = np.concatenate([[H[0]] * 3, H, [H[-1]] * 3])
        M_rep = np.concatenate([[M[0]] * 3, M, [M[-1]] * 3])
        tp = rmag.find_hysteresis_turning_point(H_rep)
        assert H_rep[tp] == pytest.approx(np.min(H_rep))
        upper, lower = rmag.split_hysteresis_loop(H_rep, M_rep)
        assert np.max(upper[0]) == pytest.approx(np.max(H_rep))
        assert np.max(lower[0]) == pytest.approx(np.max(H_rep))

    def test_turning_point_with_field_glitch(self):
        # a small non-monotonic field glitch away from the reversal must not
        # be mistaken for the turning point
        H, M = synthetic_loop()
        H_glitch = H.copy()
        H_glitch[50] = H_glitch[49] + 1e-4  # brief backwards step mid-branch
        tp = rmag.find_hysteresis_turning_point(H_glitch)
        assert abs(H_glitch[tp] - np.min(H_glitch)) < 0.02

    def test_monotonic_field_raises(self):
        with pytest.raises(ValueError):
            rmag.find_hysteresis_turning_point(np.linspace(1, -1, 50))
        with pytest.raises(ValueError):
            rmag.find_hysteresis_turning_point(np.ones(50))

    def test_collapse_plateaus_averages_moments(self):
        field = np.array([1.0, 1.0, 1.0, 0.5, 0.0, 0.0])
        moment = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 7.0])
        cf, cm = rmag.collapse_hysteresis_field_plateaus(field, moment)
        assert np.allclose(cf, [1.0, 0.5, 0.0])
        assert np.allclose(cm, [2.0, 4.0, 6.0])

    def test_gridding_with_plateaus_recovers_parameters(self):
        # full pipeline entry: plateaus at the tips should not degrade
        # gridding or the recovered parameters
        Ms, Bc, w = 1.0, 0.05, 0.03
        H, M = synthetic_loop(Ms=Ms, Bc=Bc, w=w, noise=2e-4)
        H_rep = np.concatenate([[H[0]] * 3, H, [H[-1]] * 3])
        M_rep = np.concatenate([[M[0]] * 3, M, [M[-1]] * 3])
        gH, gM = rmag.grid_hysteresis_loop(H_rep, M_rep)
        upper, lower = rmag.split_hysteresis_loop(gH, gM)
        assert np.allclose(upper[0], lower[0])
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert Mr == pytest.approx(Ms * np.tanh(Bc / w), rel=0.01)
        assert rmag.calc_Bc(gH, gM) == pytest.approx(Bc, abs=1e-3)


class TestInputHandling:
    """The processing functions must accept data from any stream, not just
    MagIC measurement tables: plain lists, numeric strings, either field
    sweep order, and files containing non-finite rows."""

    def test_plain_lists_and_numeric_strings(self):
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        from_arrays = rmag.process_hyst_loop(H, M, show_results_table=False,
                                             show_plot=False)
        from_lists = rmag.process_hyst_loop(list(H), list(M),
                                            show_results_table=False,
                                            show_plot=False)
        from_strings = rmag.process_hyst_loop([str(x) for x in H],
                                              [str(x) for x in M],
                                              show_results_table=False,
                                              show_plot=False)
        assert from_lists['Ms'] == pytest.approx(from_arrays['Ms'])
        assert from_strings['Ms'] == pytest.approx(from_arrays['Ms'])

    def test_ascending_first_sweep_order(self):
        # a loop measured from negative saturation upward must give the same
        # parameters as the same loop measured from positive saturation down
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        half = len(H) // 2
        H_asc = np.concatenate([H[half:], H[:half]])
        M_asc = np.concatenate([M[half:], M[:half]])
        r_desc = rmag.process_hyst_loop(H, M, show_results_table=False,
                                        show_plot=False)
        r_asc = rmag.process_hyst_loop(H_asc, M_asc, show_results_table=False,
                                       show_plot=False)
        assert r_asc['Mr'] == pytest.approx(r_desc['Mr'], rel=0.01)
        assert r_asc['Ms'] == pytest.approx(r_desc['Ms'], rel=0.01)
        assert r_asc['Bc'] == pytest.approx(r_desc['Bc'], rel=0.02)
        assert r_asc['Mr'] > 0

    def test_nonfinite_pairs_dropped(self, capsys):
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        M_bad = M.copy()
        M_bad[[10, 200]] = np.nan
        r_bad = rmag.process_hyst_loop(H, M_bad, show_results_table=False,
                                       show_plot=False)
        r_clean = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        assert 'dropping 2 measurement(s)' in capsys.readouterr().out
        assert r_bad['Ms'] == pytest.approx(r_clean['Ms'], rel=0.01)

    def test_sanitize_errors(self):
        with pytest.raises(ValueError):
            rmag.sanitize_hysteresis_inputs([1.0, 'not a number'], [0.0, 0.0])
        with pytest.raises(ValueError):
            rmag.sanitize_hysteresis_inputs([1.0] * 5, [0.0] * 5)  # too few
        with pytest.raises(ValueError):
            rmag.sanitize_hysteresis_inputs([1.0, np.nan] * 10, [0.0] * 20,
                                            drop_nonfinite=False)

    def test_non_tesla_field_warning(self, capsys):
        H, M = synthetic_loop(noise=5e-4)
        rmag.sanitize_hysteresis_inputs(H * 1000, M)  # fields in mT
        assert 'not in tesla' in capsys.readouterr().out

    def test_grid_rejects_nonfinite(self):
        H, M = synthetic_loop()
        M[5] = np.nan
        with pytest.raises(ValueError):
            rmag.grid_hysteresis_loop(H, M)


class TestLoopGeometry:
    def test_split_branches(self):
        H, M = synthetic_loop()
        upper, lower = rmag.split_hysteresis_loop(H, M)
        # upper branch is returned in ascending field order
        assert np.all(np.diff(upper[0]) > 0)
        assert np.all(np.diff(lower[0]) > 0)
        # at a given field the upper (descending) branch moment is higher
        mid = len(upper[0]) // 2
        interp_lower = np.interp(upper[0][mid], lower[0], lower[1])
        assert upper[1][mid] > interp_lower

    def test_gridding_symmetric_fields(self):
        H, M = synthetic_loop(noise=1e-4)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        upper, lower = rmag.split_hysteresis_loop(gH, gM)
        # the two branches share a field grid that is symmetric about zero
        assert np.allclose(upper[0], lower[0])
        assert np.allclose(np.sort(upper[0]), np.sort(-upper[0]))

    def test_gridding_preserves_moments(self):
        H, M = synthetic_loop()
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        upper, _ = rmag.split_hysteresis_loop(gH, gM)
        expected = np.tanh((upper[0] + 0.05) / 0.03)
        assert np.allclose(upper[1], expected, atol=2e-3)


class TestQualityFactor:
    def test_Q_matches_hystlab_convention(self):
        # Q = log10(1/sqrt(1 - R^2)) of the branch-symmetry regression --
        # the convention of the IRM software and HystLab (Paterson et al.,
        # 2018, eq. 4), which those authors document as the definition used
        # for the values reported in Jackson and Solheid (2010) even though
        # the equation printed in that paper omits the square root
        H, M = synthetic_loop(noise=1e-3)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        _, Q = rmag.calc_Q(gH, gM)
        r2 = rmag.loop_H_off(gH, gM, 0.0)['r2']
        Q_expected = np.log10(1.0 / np.sqrt(1.0 - r2))
        assert Q == pytest.approx(Q_expected, abs=0.05)

    def test_Q_decreases_with_noise(self):
        Qs = []
        for noise in [1e-4, 1e-3, 1e-2]:
            H, M = synthetic_loop(noise=noise)
            gH, gM = rmag.grid_hysteresis_loop(H, M)
            Qs.append(rmag.calc_Q(gH, gM)[1])
        assert Qs[0] > Qs[1] > Qs[2]
        # tenfold noise increase lowers the amplitude-ratio Q by ~1
        assert Qs[0] - Qs[1] == pytest.approx(1.0, abs=0.15)


class TestCentering:
    def test_recovers_known_offsets(self):
        H, M = synthetic_loop(noise=5e-4, H_offset=0.004, M_offset=0.02)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_loop_centering(gH, gM)
        assert results['opt_H_offset'] == pytest.approx(0.004, abs=5e-4)
        assert results['opt_M_offset'] == pytest.approx(0.02, abs=2e-3)

    def test_Q_reflects_post_centering_quality(self):
        # Q must be computed after offset correction (Jackson and Solheid,
        # 2010, section 3; HystLab computes Q on offset-corrected curves) --
        # otherwise a loop offset depresses Q below the decision gate that
        # controls whether the offset correction is applied at all
        H, M = synthetic_loop(noise=5e-4)
        H_off, M_off = synthetic_loop(noise=5e-4, H_offset=0.002, M_offset=0.01)
        Q_clean = rmag.hyst_loop_centering(*rmag.grid_hysteresis_loop(H, M))['Q']
        Q_offset = rmag.hyst_loop_centering(*rmag.grid_hysteresis_loop(H_off, M_off))['Q']
        assert Q_offset == pytest.approx(Q_clean, abs=0.3)
        assert Q_offset > 2

    def test_centered_loop_crossings(self):
        H, M = synthetic_loop(noise=5e-4, H_offset=0.004, M_offset=0.02)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_loop_centering(gH, gM)
        Bc = rmag.calc_Bc(results['centered_H'], results['centered_M'])
        assert Bc == pytest.approx(0.05, abs=1e-3)


class TestLinearityTest:
    def test_paramagnet_is_linear(self):
        # pure paramagnetic response with noise: no significant nonlinearity
        H, M = synthetic_loop(Ms=0.0, Bc=0.0, chi=1.0, noise=5e-3)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_linearity_test(gH, gM)
        assert results['loop_is_linear']

    def test_ferromagnet_is_nonlinear(self):
        H, M = synthetic_loop(noise=1e-3)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_linearity_test(gH, gM)
        assert not results['loop_is_linear']
        assert results['FNL'] > 1.25


class TestSaturationTest:
    def test_saturated_loop(self):
        # tanh ferromagnet saturates well below 0.6*Hmax; FNL should be
        # near 1 (pure noise) in all high-field windows
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_loop_saturation_test(gH, gM)
        assert results['loop_is_saturated']
        for key in ['FNL60', 'FNL70', 'FNL80']:
            assert results[key] < 2.5
            assert results[key] > 0  # F statistics are non-negative

    def test_unsaturated_loop(self):
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        results = rmag.hyst_loop_saturation_test(gH, gM)
        assert not results['loop_is_saturated']
        assert results['FNL60'] > 2.5
        assert results['saturation_cutoff'] == 0.92


class TestClosureTest:
    @staticmethod
    def _closure(H, M, use_Me=True):
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        return rmag.loop_closure_test(Hu, Mrh, Me if use_Me else None)

    def test_closed_loop(self):
        H, M = synthetic_loop(noise=2e-3)
        results = self._closure(H, M)
        assert results['loop_is_closed']

    def test_open_loop(self):
        # wide-coercivity (hematite-like) component keeps the loop open
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        results = self._closure(H, M)
        assert not results['loop_is_closed']
        assert results['SNR'] > 8
        assert results['HAR'] > -48

    def test_fallback_without_Me(self):
        # without the err curve the odd part of Mrh serves as the noise;
        # classifications should agree away from the decision boundary
        H, M = synthetic_loop(noise=2e-3)
        assert self._closure(H, M, use_Me=False)['loop_is_closed']
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        assert not self._closure(H, M, use_Me=False)['loop_is_closed']

    def test_noise_convention_vs_odd_part(self):
        # the err(H)-based noise (HystLab convention) sits ~3 dB below the
        # odd-part fallback for white noise, so Me-based SNR is lower
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        snr_me = self._closure(H, M, use_Me=True)['SNR']
        snr_odd = self._closure(H, M, use_Me=False)['SNR']
        assert snr_me == pytest.approx(snr_odd - 3.0, abs=2.0)


class TestDriftCorrection:
    def test_prorated_removes_closure_error(self):
        H, M = synthetic_loop(drift=0.02)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        corrected = rmag.prorated_drift_correction(gH, gM)
        assert corrected[0] - corrected[-1] == pytest.approx(0.0, abs=1e-12)
        # correction is distributed with zero mean (no net vertical shift)
        assert np.mean(corrected - gM) == pytest.approx(0.0, abs=1e-12)

    def test_symmetric_averaging_closes_loop(self):
        H, M = synthetic_loop(drift=0.02)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        corrected = rmag.symmetric_averaging_drift_corr(gH, gM)
        upper, lower = rmag.split_hysteresis_loop(gH, corrected)
        # branches meet at both tips after correction
        assert upper[1][0] == pytest.approx(lower[1][0], abs=1e-12)
        assert upper[1][-1] == pytest.approx(lower[1][-1], abs=1e-12)


class TestParameterRecovery:
    def test_Mr_Bc_recovery(self):
        Ms, Bc, w = 1.0, 0.05, 0.03
        H, M = synthetic_loop(Ms=Ms, Bc=Bc, w=w, noise=2e-4)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert Mr == pytest.approx(Ms * np.tanh(Bc / w), rel=0.01)
        assert rmag.calc_Bc(gH, gM) == pytest.approx(Bc, abs=1e-3)

    def test_linear_HF_fit_recovers_chi_and_Ms(self):
        chi = 0.2  # raw slope units (moment per Tesla)
        H, M = synthetic_loop(chi=chi, noise=2e-4)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        chi_HF, Ms = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        # chi_HF is reported in SI units: raw slope times mu_0
        assert chi_HF == pytest.approx(chi * 4 * np.pi / 1e7, rel=0.01)
        assert Ms == pytest.approx(1.0, rel=0.01)

    def test_slope_correction_roundtrip(self):
        chi = 0.2
        H, M = synthetic_loop(chi=chi, noise=0.0)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        chi_HF, _ = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        ferro = rmag.hyst_slope_correction(gH, gM, chi_HF)
        expected_upper, _ = rmag.split_hysteresis_loop(gH, ferro)
        assert np.allclose(
            expected_upper[1],
            np.tanh((expected_upper[0] + 0.05) / 0.03),
            atol=5e-3,
        )


class TestNonlinearFit:
    def test_ats_fit_beats_linear_fit(self):
        # unsaturated loop: linear high-field fitting underestimates Ms
        # while approach-to-saturation fitting recovers it
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        _, Ms_linear = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        assert abs(nl['Ms'] - 1.0) < abs(Ms_linear - 1.0)
        assert nl['Ms'] == pytest.approx(1.0, rel=0.02)

    def test_Fnl_lin_is_f_statistic(self):
        # significant nonlinearity: Fnl_lin far above the ~3-3.5 critical value
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        assert nl['Fnl_lin'] > 3.5
        # verify against a direct computation of eq. 21
        HF = np.where((np.abs(gH) >= 0.6 * np.max(np.abs(gH))) &
                      (np.abs(gH) <= 0.97 * np.max(np.abs(gH))))[0]
        HF_field = np.abs(gH[HF])
        HF_mag = np.where(gH[HF] >= 0, gM[HF], -gM[HF])
        slope, intercept = np.polyfit(HF_field, HF_mag, 1)
        SSD_lin = np.sum((HF_mag - (slope * HF_field + intercept)) ** 2)
        pred = rmag.IRM_nonlinear_fit(HF_field, nl['chi_HF'], nl['Ms'],
                                      nl['a_1'], nl['a_2'])
        SSD_nl = np.sum((HF_mag - pred) ** 2)
        n = len(HF_mag)
        expected = ((SSD_lin - SSD_nl) / 2) / (SSD_nl / (n - 4))
        assert nl['Fnl_lin'] == pytest.approx(expected, rel=1e-6)

    def test_insignificant_when_saturated(self):
        # saturated loop: nonlinear terms should not significantly improve fit
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        assert nl['Fnl_lin'] < 3.5


class TestProcessHystLoop:
    def test_full_pipeline_saturated(self):
        Ms, Bc, w, chi = 1.0, 0.05, 0.03, 0.2
        H, M = synthetic_loop(Ms=Ms, Bc=Bc, w=w, chi=chi, noise=5e-4,
                              H_offset=0.002, M_offset=0.01)
        results = rmag.process_hyst_loop(H, M, 'synthetic',
                                         show_results_table=False,
                                         show_plot=False)
        assert not results['loop_is_linear']
        assert results['loop_is_closed']
        assert results['loop_is_saturated']
        assert results['Ms'] == pytest.approx(Ms, rel=0.02)
        assert results['Mr'] == pytest.approx(Ms * np.tanh(Bc / w), rel=0.02)
        assert results['Bc'] == pytest.approx(Bc, abs=2e-3)
        assert results['chi_HF'] == pytest.approx(chi * 4 * np.pi / 1e7, rel=0.05)
        assert results['Q'] > 2

    def test_full_pipeline_unsaturated(self):
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        results = rmag.process_hyst_loop(H, M, 'synthetic',
                                         show_results_table=False,
                                         show_plot=False)
        assert not results['loop_is_saturated']
        assert results['Fnl_lin'] is not None
        assert results['Ms'] == pytest.approx(1.0, rel=0.03)
