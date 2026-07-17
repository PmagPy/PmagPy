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
import pandas as pd
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


def synthetic_loop_ascending_first(n_half=200, Hmax=1.0, Ms=1.0, Bc=0.05,
                                   w=0.03, drift=0.0):
    """Same physics as synthetic_loop but measured -Hmax -> +Hmax -> -Hmax.

    The drift is the same linear-in-time law, so processing this loop and its
    descending-first twin should recover the same loop parameters.
    """
    H_lower = np.linspace(-Hmax, Hmax, n_half)
    H_upper = np.linspace(Hmax, -Hmax, n_half)
    M_lower = Ms * np.tanh((H_lower - Bc) / w)
    M_upper = Ms * np.tanh((H_upper + Bc) / w)
    H = np.concatenate([H_lower, H_upper])
    M = np.concatenate([M_lower, M_upper])
    M = M + drift * np.linspace(0, 1, M.size)
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
        return rmag.loop_closure_test(Hu, Mrh, Me=Me if use_Me else None)

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

    def test_measured_descending_first_detection(self):
        H_desc, _ = synthetic_loop()
        H_asc, _ = synthetic_loop_ascending_first()
        assert rmag.measured_descending_first(H_desc)
        assert not rmag.measured_descending_first(H_asc)

    def test_prorated_time_order_aware(self):
        # a linear-in-time drift is removed exactly (up to a constant and
        # gridding interpolation error) when the prorated ramp runs in the
        # loop's true measurement-time order -- for either sweep order
        drift = 0.05
        H_true, M_true = synthetic_loop()
        gH, gM_true = rmag.grid_hysteresis_loop(H_true, M_true)
        for loop_builder, descending_first in (
                (synthetic_loop, True),
                (synthetic_loop_ascending_first, False)):
            H, M = loop_builder(drift=drift)
            gH_d, gM_d = rmag.grid_hysteresis_loop(H, M)
            corrected = rmag.prorated_drift_correction(
                gH_d, gM_d, descending_first=descending_first)
            residual = corrected - gM_true
            # residual is a constant shift, not a branch-dependent ramp
            assert np.std(residual) == pytest.approx(0.0, abs=drift / 50)

    def test_prorated_wrong_order_leaves_ramp(self):
        # applying the ramp with the wrong time sense leaves a residual of
        # the drift's magnitude, confirming the flag changes the result
        drift = 0.05
        H_true, M_true = synthetic_loop()
        gH, gM_true = rmag.grid_hysteresis_loop(H_true, M_true)
        H, M = synthetic_loop_ascending_first(drift=drift)
        gH_d, gM_d = rmag.grid_hysteresis_loop(H, M)
        wrong = rmag.prorated_drift_correction(gH_d, gM_d,
                                               descending_first=True)
        assert np.std(wrong - gM_true) > drift / 10

    def test_Me_correction_order_symmetric(self):
        # identical physics and identical drift law measured in the two sweep
        # orders: once the correction runs in true measurement-time order the
        # two orders are treated identically (the equivalence mapping is
        # exact) and both move the loop toward the drift-free truth, whereas
        # the wrong time sense actively corrupts the loop
        drift = 0.05
        H_ref, M_ref = synthetic_loop()
        gH_ref, gM_ref = rmag.grid_hysteresis_loop(H_ref, M_ref)

        H_d, M_d = synthetic_loop(drift=drift)
        gH_d, gM_d = rmag.grid_hysteresis_loop(H_d, M_d)
        H_a, M_a = synthetic_loop_ascending_first(drift=drift)
        gH_a, gM_a = rmag.grid_hysteresis_loop(H_a, M_a)
        assert np.allclose(gH_d, gH_a)

        def rms(x):
            return float(np.sqrt(np.mean(np.square(x))))

        rms_uncorrected = rms(gM_a - gM_ref)
        corr_desc = rmag.drift_correction_Me(gH_d, gM_d,
                                             descending_first=True)
        corr_asc = rmag.drift_correction_Me(gH_a, gM_a,
                                            descending_first=False)
        wrong_asc = rmag.drift_correction_Me(gH_a, gM_a,
                                             descending_first=True)

        # both sweep orders receive the same (correct) treatment
        assert rms(corr_asc - gM_ref) == pytest.approx(
            rms(corr_desc - gM_ref), rel=1e-6)
        # the correct time sense improves on the uncorrected loop; the wrong
        # time sense makes it worse than not correcting at all
        assert rms(corr_asc - gM_ref) < rms_uncorrected
        assert rms(wrong_asc - gM_ref) > rms_uncorrected


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

    def test_pipeline_ascending_first_matches_descending(self):
        # the same loop physics with the same drift law, measured in the two
        # sweep orders, must process to the same Mr and Bc now that the drift
        # correction runs in true measurement-time order
        H_d, M_d = synthetic_loop(drift=0.05)
        H_a, M_a = synthetic_loop_ascending_first(drift=0.05)
        res_d = rmag.process_hyst_loop(H_d, M_d, show_results_table=False,
                                       show_plot=False)
        res_a = rmag.process_hyst_loop(H_a, M_a, show_results_table=False,
                                       show_plot=False)
        assert res_d['measured_descending_first']
        assert not res_a['measured_descending_first']
        assert res_a['Mr'] == pytest.approx(res_d['Mr'], rel=0.03)
        assert res_a['Bc'] == pytest.approx(res_d['Bc'], rel=0.05)


class TestOpenLoopBrh:
    def test_Brh_nan_when_Mrh_stays_high(self):
        # hematite-like loop measured far short of saturation: Mrh never
        # falls to Mr/2 in the measured range, so Brh is NaN with a warning
        # rather than a TypeError (None arithmetic)
        H, M = synthetic_loop(Ms=1.0, Bc=1.5, w=1.0)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        with pytest.warns(RuntimeWarning, match='Brh'):
            Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert np.isnan(Brh)
        assert np.isfinite(Mr) and Mr > 0
        assert np.all(np.isfinite(Mrh))

    def test_closed_loop_Brh_unchanged(self):
        # well-behaved loop: Brh is still computed from both crossings
        H, M = synthetic_loop()
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        *_, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert np.isfinite(Brh) and Brh > 0

    def test_Bc_nan_when_no_zero_crossing(self):
        # loop measured far below the coercivity of its hard component:
        # neither branch crosses zero, so Bc is NaN with a warning
        H, M = synthetic_loop(Ms=1.0, Bc=1.5, w=1.0)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        with pytest.warns(RuntimeWarning, match='Bc'):
            Bc = rmag.calc_Bc(gH, gM)
        assert np.isnan(Bc)

    def test_pipeline_survives_open_loops(self):
        # process_hyst_loop must complete on exactly the open-loop specimens
        # the closure test is designed to flag, reporting NaN for the
        # undefined parameters rather than crashing
        import warnings as _warnings
        # realistic: soft magnetite plus a dominant unsaturated hard phase
        H1, M1 = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                                hard_Bc=2.0, hard_w=1.5, noise=2e-4)
        # extreme: single hard phase, magnetization never reverses
        H2, M2 = synthetic_loop(Ms=1.0, Bc=1.5, w=1.0)
        for H, M in ((H1, M1), (H2, M2)):
            with _warnings.catch_warnings():
                _warnings.simplefilter('ignore')
                results = rmag.process_hyst_loop(H, M,
                                                 show_results_table=False,
                                                 show_plot=False)
            assert not results['loop_is_closed']
            assert np.isnan(results['Brh'])


class TestSparseLoopSaturation:
    def test_sparse_loop_does_not_abort(self):
        # a coarse quick-scan loop passes the >=10-point gate but leaves too
        # few high-field pairs for some lack-of-fit windows; those windows
        # now report NaN with a warning instead of aborting the pipeline
        H, M = synthetic_loop(n_half=12)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        with pytest.warns(RuntimeWarning, match='saturation test window'):
            results = rmag.hyst_loop_saturation_test(gH, gM)
        assert 'saturation_cutoff' in results
        # at least one window was skipped -> its FNL is NaN
        fnls = [results['FNL60'], results['FNL70'], results['FNL80']]
        assert any(np.isnan(v) for v in fnls)

    def test_direct_call_still_raises(self):
        # loop_saturation_stats itself keeps its informative error for
        # direct callers
        H, M = synthetic_loop(n_half=12)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        with pytest.raises(ValueError, match='high-field'):
            rmag.loop_saturation_stats(gH, gM, HF_cutoff=0.8)


class TestClosureTestSignature:
    def test_third_positional_is_HF_cutoff(self):
        # pre-existing (master) signature was (H, Mrh, HF_cutoff=0.8): the
        # third positional argument must still bind to HF_cutoff
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        gH, gM = rmag.grid_hysteresis_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        positional = rmag.loop_closure_test(Hu, Mrh, 0.7)
        keyword = rmag.loop_closure_test(Hu, Mrh, HF_cutoff=0.7)
        assert positional == keyword


class TestHystStatsDescriptionJSON:
    @staticmethod
    def _hyst_results():
        return pd.DataFrame([{
            'specimen': 'spec1', 'experiment': 'spec1-HYS1',
            'Ms': 1.0, 'Mr': 0.4, 'Bc': 0.05, 'chi_HF': 1e-7,
            'Q': 5.0, 'Qf': 6.0, 'sigma': 0.5, 'Brh': 0.08,
            'FNL': 1.0, 'FNL60': 1.1, 'FNL70': 1.2, 'FNL80': 1.3,
            'Fnl_lin': None, 'loop_is_linear': False,
            'loop_is_closed': True, 'loop_is_saturated': True,
            'processed_by': 'test',
        }])

    def test_round_trip_with_unmixing_payload(self):
        # a cell already holding the unmixing writer's 'text | JSON' payload
        # must survive the hysteresis writer: both structured payloads and
        # the free text are preserved and re-parseable
        import json
        unmix_payload = json.dumps({'coercivity_unmixing': {'B1': 30.0}})
        specimens = pd.DataFrame([{
            'specimen': 'spec1', 'experiments': 'spec1-HYS1:spec1-BF1',
            'description': f'sample notes | {unmix_payload}',
        }])
        out = rmag.add_hyst_stats_to_specimens_table(specimens,
                                                     self._hyst_results())
        text, data = rmag.parse_specimen_description(
            out.loc[0, 'description'])
        assert text == 'sample notes'
        assert data['coercivity_unmixing'] == {'B1': 30.0}
        assert data['Q'] == pytest.approx(5.0)
        assert data['loop_is_closed'] is True

    def test_legacy_dict_cell_migrated(self):
        # legacy str(dict) cells written by older versions are parsed and
        # migrated to the JSON convention rather than corrupted
        specimens = pd.DataFrame([{
            'specimen': 'spec1', 'experiments': 'spec1-HYS1',
            'description': str({'old_stat': 1.5}),
        }])
        out = rmag.add_hyst_stats_to_specimens_table(specimens,
                                                     self._hyst_results())
        text, data = rmag.parse_specimen_description(
            out.loc[0, 'description'])
        assert data['old_stat'] == pytest.approx(1.5)
        assert data['Brh'] == pytest.approx(0.08)
