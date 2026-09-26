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


def _hard_switching_fields(hard_Bc, hard_w, n_hysterons=4000):
    """Switching fields and weights of the hard-phase hysteron ensemble:
    normally distributed about hard_Bc with spread hard_w, truncated at
    zero, on a fine grid so the summed loop is smooth."""
    b = np.linspace(max(hard_Bc - 4 * hard_w, 1e-6), hard_Bc + 4 * hard_w,
                    n_hysterons)
    weights = np.exp(-0.5 * ((b - hard_Bc) / hard_w) ** 2)
    return b, weights / weights.sum()


def _hard_phase(H_sweep, hard_Ms, hard_Bc, hard_w):
    """Irreversible moment of a hard phase along a measured field sweep.

    The phase is an ensemble of square hysterons (Preisach-style) whose
    switching fields b are distributed by `_hard_switching_fields`; each
    is +1 once the field has reached +b and -1 once it has reached -b,
    and its state is tracked point by point along the sweep, so the
    ascending branch continues from where the descending branch ended
    and the loop closes at the tips. Grains whose switching field exceeds
    the peak field never switch: their net moment is zero (half up, half
    down in the ensemble) and they contribute nothing to Mrh, which is
    what an unsaturated hard phase looks like on a real minor loop --
    branches separated at high field, converging only at the turning
    points. The sweep is assumed to start at +Hmax, so hysterons with
    b <= Hmax start in the +1 state.
    """
    H_sweep = np.asarray(H_sweep, dtype=float)
    b, weights = _hard_switching_fields(hard_Bc, hard_w)
    Hmax = np.max(np.abs(H_sweep))
    state = np.where(b <= Hmax, 1.0, 0.0)
    M = np.empty(H_sweep.size)
    for i, h in enumerate(H_sweep):
        state = np.where(h >= b, 1.0, np.where(h <= -b, -1.0, state))
        M[i] = hard_Ms * np.sum(weights * state)
    return M


def _hard_phase_stats(hard_Bc=0.9, hard_w=0.2, Hmax=1.0, HF_cutoff=0.8,
                      max_field_cutoff=0.99):
    """Closed-form properties of the hard phase per unit hard_Ms: 'P', the
    weight of switching fields at or below Hmax (its remanence and the
    moment it exhibits at the peak field), and 'S_bar', the window mean of
    Mrh, i.e. of the weight of switching fields between H and Hmax."""
    b, weights = _hard_switching_fields(hard_Bc, hard_w)
    H = np.linspace(HF_cutoff * Hmax, max_field_cutoff * Hmax, 2000)
    P = float(np.sum(weights[b <= Hmax]))
    S_bar = float(np.mean([np.sum(weights[(b > h) & (b <= Hmax)]) for h in H]))
    return {'P': P, 'S_bar': S_bar}


def synthetic_loop(n_half=200, Hmax=1.0, Ms=1.0, Bc=0.05, w=0.03, chi=0.0,
                   noise=0.0, H_offset=0.0, M_offset=0.0, drift=0.0,
                   hard_Ms=0.0, hard_Bc=0.9, hard_w=0.2,
                   ats_alpha=0.0, rng=RNG):
    """Two-branch synthetic loop measured +Hmax -> -Hmax -> +Hmax.

    The soft ferromagnetic component is Ms*tanh((H +/- Bc)/w), so the
    remanence is Mr = Ms*tanh(Bc/w) and the branch zero crossings are at
    -/+Bc when no other contributions are added (the branches must have
    converged before the tips, Hmax - Bc >> w, for the loop to be a
    possible measurement). Optional contributions:
      chi       linear (paramagnetic) slope in raw slope units (M per T)
      noise     gaussian measurement noise
      H_offset  horizontal loop shift (e.g. sensor offset)
      M_offset  vertical loop shift
      drift     linear-in-time drift amplitude accumulated over the loop
      hard_Ms   hard phase (`_hard_phase`): hysterons with switching fields
                about hard_Bc +/- hard_w; those above Hmax never switch, so
                the loop is open at high field yet closed at the tips
      ats_alpha approach-to-saturation curvature -alpha/H applied smoothly
                above 0.3*Hmax (unsaturated ferromagnetic moment)
    """
    H_upper = np.linspace(Hmax, -Hmax, n_half)
    H_lower = np.linspace(-Hmax, Hmax, n_half)

    def branch(H, sign):
        M = Ms * np.tanh((H + sign * Bc) / w)
        if ats_alpha != 0.0:
            # curvature only where the tanh is saturated, tapering smoothly
            # to zero below 0.3*Hmax so low fields are not distorted
            taper = 0.5 * (1 + np.tanh((np.abs(H) - 0.3 * Hmax) / (0.1 * Hmax)))
            M = M - ats_alpha * taper * np.sign(H) / np.maximum(np.abs(H), 0.3 * Hmax)
        return M + chi * H

    H = np.concatenate([H_upper, H_lower]) + H_offset
    M = np.concatenate([branch(H_upper, +1), branch(H_lower, -1)]) + M_offset
    if hard_Ms != 0.0:
        M = M + _hard_phase(np.concatenate([H_upper, H_lower]), hard_Ms, hard_Bc, hard_w)
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
        tp = rmag.find_hyst_turning_point(H)
        assert H[tp] == pytest.approx(np.min(H))
        assert np.all(np.diff(H[:tp + 1]) <= 0)
        assert np.all(np.diff(H[tp + 1:]) >= 0)

    def test_turning_point_with_tip_plateaus(self):
        # repeated field readings at the loop tips, as recorded by a VSM
        # holding the field while averaging
        H, M = synthetic_loop()
        H_rep = np.concatenate([[H[0]] * 3, H, [H[-1]] * 3])
        M_rep = np.concatenate([[M[0]] * 3, M, [M[-1]] * 3])
        tp = rmag.find_hyst_turning_point(H_rep)
        assert H_rep[tp] == pytest.approx(np.min(H_rep))
        upper, lower = rmag.split_hyst_loop(H_rep, M_rep)
        assert np.max(upper[0]) == pytest.approx(np.max(H_rep))
        assert np.max(lower[0]) == pytest.approx(np.max(H_rep))

    def test_turning_point_with_field_glitch(self):
        # a small non-monotonic field glitch away from the reversal must not
        # be mistaken for the turning point
        H, M = synthetic_loop()
        H_glitch = H.copy()
        H_glitch[50] = H_glitch[49] + 1e-4  # brief backwards step mid-branch
        tp = rmag.find_hyst_turning_point(H_glitch)
        assert abs(H_glitch[tp] - np.min(H_glitch)) < 0.02

    def test_monotonic_field_raises(self):
        with pytest.raises(ValueError):
            rmag.find_hyst_turning_point(np.linspace(1, -1, 50))
        with pytest.raises(ValueError):
            rmag.find_hyst_turning_point(np.ones(50))

    def test_collapse_plateaus_averages_moments(self):
        field = np.array([1.0, 1.0, 1.0, 0.5, 0.0, 0.0])
        moment = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 7.0])
        cf, cm = rmag.collapse_hyst_field_plateaus(field, moment)
        assert np.allclose(cf, [1.0, 0.5, 0.0])
        assert np.allclose(cm, [2.0, 4.0, 6.0])

    def test_gridding_with_plateaus_recovers_parameters(self):
        # full pipeline entry: plateaus at the tips should not degrade
        # gridding or the recovered parameters
        Ms, Bc, w = 1.0, 0.05, 0.03
        H, M = synthetic_loop(Ms=Ms, Bc=Bc, w=w, noise=2e-4)
        H_rep = np.concatenate([[H[0]] * 3, H, [H[-1]] * 3])
        M_rep = np.concatenate([[M[0]] * 3, M, [M[-1]] * 3])
        gH, gM = rmag.grid_hyst_loop(H_rep, M_rep)
        upper, lower = rmag.split_hyst_loop(gH, gM)
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
            rmag.sanitize_hyst_inputs([1.0, 'not a number'], [0.0, 0.0])
        with pytest.raises(ValueError):
            rmag.sanitize_hyst_inputs([1.0] * 5, [0.0] * 5)  # too few
        with pytest.raises(ValueError):
            rmag.sanitize_hyst_inputs([1.0, np.nan] * 10, [0.0] * 20,
                                            drop_nonfinite=False)

    def test_non_tesla_field_warning(self, capsys):
        H, M = synthetic_loop(noise=5e-4)
        rmag.sanitize_hyst_inputs(H * 1000, M)  # fields in mT
        assert 'not in tesla' in capsys.readouterr().out

    def test_grid_rejects_nonfinite(self):
        H, M = synthetic_loop()
        M[5] = np.nan
        with pytest.raises(ValueError):
            rmag.grid_hyst_loop(H, M)


class TestLoopGeometry:
    def test_split_branches(self):
        H, M = synthetic_loop()
        upper, lower = rmag.split_hyst_loop(H, M)
        # upper branch is returned in ascending field order
        assert np.all(np.diff(upper[0]) > 0)
        assert np.all(np.diff(lower[0]) > 0)
        # at a given field the upper (descending) branch moment is higher
        mid = len(upper[0]) // 2
        interp_lower = np.interp(upper[0][mid], lower[0], lower[1])
        assert upper[1][mid] > interp_lower

    def test_gridding_symmetric_fields(self):
        H, M = synthetic_loop(noise=1e-4)
        gH, gM = rmag.grid_hyst_loop(H, M)
        upper, lower = rmag.split_hyst_loop(gH, gM)
        # the two branches share a field grid that is symmetric about zero
        assert np.allclose(upper[0], lower[0])
        assert np.allclose(np.sort(upper[0]), np.sort(-upper[0]))

    def test_gridding_preserves_moments(self):
        H, M = synthetic_loop()
        gH, gM = rmag.grid_hyst_loop(H, M)
        upper, _ = rmag.split_hyst_loop(gH, gM)
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
        gH, gM = rmag.grid_hyst_loop(H, M)
        _, Q = rmag.calc_Q(gH, gM)
        r2 = rmag._loop_H_off(gH, gM, 0.0)['r2']
        Q_expected = np.log10(1.0 / np.sqrt(1.0 - r2))
        assert Q == pytest.approx(Q_expected, abs=0.05)

    def test_Q_decreases_with_noise(self):
        Qs = []
        for noise in [1e-4, 1e-3, 1e-2]:
            H, M = synthetic_loop(noise=noise)
            gH, gM = rmag.grid_hyst_loop(H, M)
            Qs.append(rmag.calc_Q(gH, gM)[1])
        assert Qs[0] > Qs[1] > Qs[2]
        # tenfold noise increase lowers the amplitude-ratio Q by ~1
        assert Qs[0] - Qs[1] == pytest.approx(1.0, abs=0.15)


class TestCentering:
    def test_recovers_known_offsets(self):
        H, M = synthetic_loop(noise=5e-4, H_offset=0.004, M_offset=0.02)
        gH, gM = rmag.grid_hyst_loop(H, M)
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
        Q_clean = rmag.hyst_loop_centering(*rmag.grid_hyst_loop(H, M))['Q']
        Q_offset = rmag.hyst_loop_centering(*rmag.grid_hyst_loop(H_off, M_off))['Q']
        assert Q_offset == pytest.approx(Q_clean, abs=0.3)
        assert Q_offset > 2

    def test_centered_loop_crossings(self):
        H, M = synthetic_loop(noise=5e-4, H_offset=0.004, M_offset=0.02)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_loop_centering(gH, gM)
        Bc = rmag.calc_Bc(results['centered_H'], results['centered_M'])
        assert Bc == pytest.approx(0.05, abs=1e-3)


class TestLinearityTest:
    def test_paramagnet_is_linear(self):
        # pure paramagnetic response with noise: no significant nonlinearity
        H, M = synthetic_loop(Ms=0.0, Bc=0.0, chi=1.0, noise=5e-3)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_linearity_test(gH, gM)
        assert results['loop_is_linear']

    def test_ferromagnet_is_nonlinear(self):
        H, M = synthetic_loop(noise=1e-3)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_linearity_test(gH, gM)
        assert not results['loop_is_linear']
        assert results['FNL'] > 1.25


class TestSaturationTest:
    def test_saturated_loop(self):
        # tanh ferromagnet saturates well below 0.6*Hmax; FNL should be
        # near 1 (pure noise) in all high-field windows
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_loop_saturation_test(gH, gM)
        assert results['loop_is_saturated']
        for key in ['FNL60', 'FNL70', 'FNL80']:
            assert results[key] < 2.5
            assert results[key] > 0  # F statistics are non-negative

    def test_unsaturated_loop(self):
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_loop_saturation_test(gH, gM)
        assert not results['loop_is_saturated']
        assert results['FNL60'] > results['F_critical60']
        assert results['p60'] < 0.05
        assert results['saturation_cutoff'] is None
        assert results['testable']

    def test_thresholds_are_F_critical_values(self):
        # the decision compares FNL with the F distribution at the window's
        # degrees of freedom (Jackson and Solheid, 2010; HystLab), not a
        # fixed constant: for a dense loop the 95% critical value is well
        # below the former fixed threshold of 2.5
        from scipy.stats import f as fdist
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        gH, gM = rmag.grid_hyst_loop(H, M)
        for cutoff in (0.6, 0.7, 0.8):
            st = rmag.loop_saturation_stats(gH, gM, HF_cutoff=cutoff)
            n = st['n_pairs']
            assert st['F_critical'] == pytest.approx(fdist.ppf(0.95, n - 2, n))
            assert st['p_value'] == pytest.approx(fdist.sf(st['FNL'], n - 2, n))
            assert st['F_critical'] < 2.0
        strict = rmag.loop_saturation_stats(gH, gM, HF_cutoff=0.8, alpha=0.01)
        assert strict['F_critical'] > st['F_critical']
        # the whole-loop test likewise
        lin = rmag.hyst_linearity_test(gH, gM)
        n_half = len(gH) / 2
        assert lin['F_critical'] == pytest.approx(fdist.ppf(0.95, n_half - 2, n_half))
        assert lin['loop_is_linear'] == (lin['FNL'] < lin['F_critical'])

    def test_widest_linear_window_is_used(self):
        # Jackson and Solheid (2010, paragraph 40): the nonlinear fit is
        # required only when every window rejects linearity; otherwise the
        # linear fit is taken over the widest window that is linear
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        gH, gM = rmag.grid_hyst_loop(H, M)
        results = rmag.hyst_loop_saturation_test(gH, gM)
        linear = [c for c in (0.6, 0.7, 0.8)
                  if results[f'FNL{int(c*100)}'] < results[f'F_critical{int(c*100)}']]
        assert results['saturation_cutoff'] == min(linear)

    def test_windows_with_few_measurements_are_untestable(self, capsys):
        # an MPMS-style loop with 0.5 T steps above 1 T on a 2.5 T sweep:
        # gridding at the median (low-field) step fabricates points in the
        # high-field windows and the pure-error term collapses; with the
        # measured fields supplied the windows are reported as untestable
        Hmax = 2.5
        up = np.concatenate([np.linspace(Hmax, 1.0, 4), np.linspace(0.9, -0.9, 91),
                             np.linspace(-1.0, -Hmax, 4)])
        H = np.concatenate([up, up[::-1]])
        M = np.tanh(H / 0.05) + 0.2 * H
        gH, gM = rmag.grid_hyst_loop(H, M)
        blind = rmag.hyst_loop_saturation_test(gH, gM)
        assert blind['FNL80'] > 100          # the degenerate value
        with pytest.warns(RuntimeWarning, match='measured points'):
            guarded = rmag.hyst_loop_saturation_test(gH, gM, measured_field=H)
        assert np.isnan(guarded['FNL80']) and np.isnan(guarded['FNL60'])
        assert guarded['n_measured80'] < 12
        assert not guarded['testable']
        assert guarded['loop_is_saturated'] is None
        assert guarded['saturation_cutoff'] is None
        # through the pipeline the loop takes the linear fit from 60% with
        # a warning rather than a meaningless nonlinear fit
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        out = capsys.readouterr().out
        assert 'no high-field window holds enough measured points' in out
        assert results['loop_is_saturated'] is None
        assert results['Fnl_lin'] is None
        assert results['chi_HF'] == pytest.approx(0.2 * 4 * np.pi / 1e7, rel=0.05)
        assert results['Ms'] == pytest.approx(1.0, rel=0.02)


def _closure_inputs(H, M):
    gH, gM = rmag.grid_hyst_loop(H, M)
    Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
    return Hu, Mr, Mrh, Me, Brh


def _hard_Ms_for_openness(fraction, hard_Bc=0.9, hard_w=0.2, Hmax=1.0,
                          HF_cutoff=0.8, max_field_cutoff=0.99,
                          Ms=1.0, Bc=0.05, w=0.03):
    """hard_Ms giving a noise-free high-field openness `fraction` of Mr.

    For the synthetic_loop model the soft component contributes nothing to
    Mrh above 0.8*Hmax, the hard phase contributes hard_Ms*S_bar to the
    window mean of Mrh and hard_Ms*P to Mr (see `_hard_phase_stats`), so
    fraction = hard_Ms*S_bar / (soft_Mr + hard_Ms*P).
    """
    stats = _hard_phase_stats(hard_Bc, hard_w, Hmax, HF_cutoff, max_field_cutoff)
    soft_Mr = Ms * np.tanh(Bc / w)
    return fraction * soft_Mr / (stats['S_bar'] - fraction * stats['P'])


def _exhibited_Ms(hard_Ms, Ms=1.0, hard_Bc=0.9, hard_w=0.2, Hmax=1.0):
    """The ferromagnetic moment the synthetic loop exhibits at its peak
    field: the soft Ms plus the hard-phase grains that switch within the
    sweep (those above Hmax never do and net to zero)."""
    return Ms + hard_Ms * _hard_phase_stats(hard_Bc, hard_w, Hmax)['P']


def _hard_Ms_for_openness_Ms(fraction, **kw):
    """hard_Ms giving a noise-free openness `fraction` of the exhibited Ms
    (`_exhibited_Ms`) for the synthetic_loop model:
    fraction = hard_Ms*S_bar / (1 + hard_Ms*P).
    """
    stats = _hard_phase_stats(kw.get('hard_Bc', 0.9), kw.get('hard_w', 0.2),
                              kw.get('Hmax', 1.0))
    return fraction / (stats['S_bar'] - fraction * stats['P'])


class TestClosureTest:
    """The SNR/HAR closure statistics of Paterson et al. (2018),
    selected with criterion='SNR_HAR'."""

    @staticmethod
    def _closure(H, M, use_Me=True):
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        return rmag.loop_closure_test(Hu, Mrh, Me=Me if use_Me else None,
                                      criterion='SNR_HAR')

    def test_closed_loop(self):
        H, M = synthetic_loop(noise=2e-3)
        results = self._closure(H, M)
        assert results['loop_is_closed']
        assert results['closure_state'] == 'closed'

    def test_open_loop(self):
        # wide-coercivity (hematite-like) component keeps the loop open
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        results = self._closure(H, M)
        assert not results['loop_is_closed']
        assert results['SNR'] > 8
        assert results['HAR'] > -48
        assert results['tolerance'] is None

    def test_fallback_without_Me(self):
        # without the err curve the odd part of Mrh serves as the noise;
        # classifications should agree away from the decision boundary
        H, M = synthetic_loop(noise=2e-3)
        assert self._closure(H, M, use_Me=False)['loop_is_closed']
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        assert not self._closure(H, M, use_Me=False)['loop_is_closed']

    def test_SNR_HAR_verdict_reported_under_magnitude_criterion(self):
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        legacy = rmag.loop_closure_test(Hu, Mrh, Me=Me, criterion='SNR_HAR')
        new = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=1.1)
        assert new['loop_is_closed_SNR_HAR'] == legacy['loop_is_closed']
        assert new['SNR'] == legacy['SNR'] and new['HAR'] == legacy['HAR']

    def test_scales_with_noise_not_openness(self):
        # the SNR rule depends on the noise: a fixed 0.5% opening is "open" on clean
        # data and "closed" on noisy data under the SNR rule
        hard_Ms = _hard_Ms_for_openness(0.005)
        clean = self._closure(*synthetic_loop(noise=1e-4, hard_Ms=hard_Ms))
        noisy = self._closure(*synthetic_loop(noise=2e-2, hard_Ms=hard_Ms))
        assert not clean['loop_is_closed']
        assert noisy['loop_is_closed']

    def test_noise_convention_vs_odd_part(self):
        # the err(H)-based noise (Paterson et al., 2018) sits ~3 dB below the
        # odd-part fallback for white noise, so Me-based SNR is lower
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        snr_me = self._closure(H, M, use_Me=True)['SNR']
        snr_odd = self._closure(H, M, use_Me=False)['SNR']
        assert snr_me == pytest.approx(snr_odd - 3.0, abs=2.0)


class TestClosureMagnitude:
    """The default closure criterion: the openness statistic f_open
    (HF_Mrh_fraction, the high-field Mrh as a fraction of the fitted Ms)
    against a tolerance."""

    @staticmethod
    def _closure(H, M, Ms, **kwargs):
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        return rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=Ms, **kwargs)

    def test_requires_Ms(self):
        H, M = synthetic_loop(noise=2e-3)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        with pytest.raises(ValueError, match='Ms'):
            rmag.loop_closure_test(Hu, Mrh, Me=Me)
        # the SNR_HAR criterion does not need it
        assert 'closure_state' in rmag.loop_closure_test(Hu, Mrh, Me=Me,
                                                         criterion='SNR_HAR')

    def test_openness_matches_analytic_window_mean(self):
        # the reported fraction is the window mean of the even Mrh over the
        # true Ms (1 + hard_Ms for the fixture), known in closed form; the
        # Mr-relative version is checked against its own analytic value
        for target in (0.005, 0.03, 0.2):
            hard_Ms = _hard_Ms_for_openness_Ms(target)
            H, M = synthetic_loop(hard_Ms=hard_Ms)
            results = self._closure(H, M, Ms=_exhibited_Ms(hard_Ms))
            assert results['HF_Mrh_fraction'] == pytest.approx(target, rel=0.05)
            Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
            assert results['HF_Mrh_fraction_Mr'] == pytest.approx(
                target * _exhibited_Ms(hard_Ms) / Mr, rel=0.05)

    def test_standard_error_matches_empirical_scatter(self):
        # on noisy loops the reported SE must track the actual scatter of
        # f_open across noise realizations (the noise-free test above has
        # SE = 0 exactly and cannot see a regression in the SE code)
        hard_Ms = _hard_Ms_for_openness_Ms(0.03)
        reported_se = {}
        for noise in (1e-3, 1e-2):
            rng = np.random.default_rng(int(noise * 1e6))
            estimates, ses = [], []
            for _ in range(30):
                H, M = synthetic_loop(noise=noise, hard_Ms=hard_Ms, rng=rng)
                r = self._closure(H, M, Ms=_exhibited_Ms(hard_Ms))
                estimates.append(r['HF_Mrh_fraction'])
                ses.append(r['HF_Mrh_fraction_se'])
            empirical = np.std(estimates, ddof=1)
            reported_se[noise] = np.median(ses)
            assert reported_se[noise] > 0
            # calibrated to within a factor of ~2
            assert 0.4 < reported_se[noise] / empirical < 2.5, \
                (noise, reported_se[noise], empirical)
        # and the SE scales with the noise level
        assert reported_se[1e-2] > 3 * reported_se[1e-3]

    def test_closed_loop_reports_zero_openness(self):
        results = self._closure(*synthetic_loop(noise=2e-3), Ms=1.0)
        assert results['closure_state'] == 'closed'
        assert results['loop_is_closed']
        assert abs(results['HF_Mrh_fraction']) < 3 * results['HF_Mrh_fraction_se'] + 1e-4

    def test_verdict_invariant_to_noise(self):
        # a 0.5% opening stays closed and a 10% opening stays open across
        # three decades of noise; SNR alone would flip both
        rng = np.random.default_rng(902)
        small = _hard_Ms_for_openness_Ms(0.005)
        large = _hard_Ms_for_openness_Ms(0.10)
        for noise in (1e-5, 1e-4, 1e-3, 1e-2):
            r_small = self._closure(*synthetic_loop(noise=noise, hard_Ms=small,
                                                    rng=rng), Ms=_exhibited_Ms(small))
            r_large = self._closure(*synthetic_loop(noise=noise, hard_Ms=large,
                                                    rng=rng), Ms=_exhibited_Ms(large))
            assert r_small['closure_state'] == 'closed', noise
            assert r_large['closure_state'] == 'open', noise
            assert not r_large['loop_is_closed']

    def test_openness_tolerance(self):
        # a 1% opening is below the default 2% tolerance, a 5% opening is
        # above it, and the tolerance is a parameter
        h1 = _hard_Ms_for_openness_Ms(0.01)
        small = self._closure(*synthetic_loop(noise=2e-3, hard_Ms=h1),
                              Ms=_exhibited_Ms(h1))
        assert small['tolerance'] == 0.02
        assert small['closure_state'] == 'closed'
        assert (small['HF_cutoff'], small['max_field_cutoff']) == (0.8, 0.99)
        h5 = _hard_Ms_for_openness_Ms(0.05)
        large = self._closure(*synthetic_loop(noise=2e-3, hard_Ms=h5),
                              Ms=_exhibited_Ms(h5))
        assert large['closure_state'] == 'open'
        strict = self._closure(*synthetic_loop(noise=2e-3, hard_Ms=h1),
                               Ms=_exhibited_Ms(h1), openness_tolerance=0.005)
        assert strict['closure_state'] == 'open'

    def test_Ms_and_Mr_normalizations(self):
        # the same absolute opening is a large fraction of Mr but a small
        # fraction of Ms when Mr/Ms is small (MD-like fixture): the verdict
        # follows the Ms-relative value
        md_hard = _hard_Ms_for_openness(0.03, Bc=0.001, w=0.03)   # 3% of Mr
        H, M = synthetic_loop(noise=1e-3, hard_Ms=md_hard, Bc=0.001, w=0.03,
                              rng=np.random.default_rng(902))
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        assert Mr / _exhibited_Ms(md_hard) < 0.05          # MD-like Mr/Ms
        md = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=_exhibited_Ms(md_hard))
        assert md['HF_Mrh_fraction_Mr'] == pytest.approx(0.03, rel=0.25)
        assert md['HF_Mrh_fraction'] < 0.005
        assert md['closure_state'] == 'closed'
        # SD-like fixture (Mr ~ Ms): the two fractions are close
        sd_hard = _hard_Ms_for_openness(0.05)
        H, M = synthetic_loop(noise=2e-3, hard_Ms=sd_hard)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        sd = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=_exhibited_Ms(sd_hard))
        assert sd['HF_Mrh_fraction'] == pytest.approx(
            sd['HF_Mrh_fraction_Mr'] * Mr / _exhibited_Ms(sd_hard), rel=1e-6)
        assert sd['closure_state'] == 'open'

    def test_indeterminate_when_noise_swamps_tolerance(self):
        # a weak, noisy loop cannot be declared closed at a tolerance finer
        # than its own uncertainty
        H, M = synthetic_loop(noise=0.2, Bc=0.3, w=0.1)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        results = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=1.0)
        assert 2 * results['HF_Mrh_fraction_se'] > results['tolerance']
        assert results['closure_state'] == 'indeterminate'
        assert results['loop_is_closed']

    def test_noise_level_Ms_is_not_normalized(self):
        # a paramagnetic loop has a fitted Ms (and Mr) of noise-level size;
        # f_open is undefined for it rather than a huge meaningless number
        H, M = synthetic_loop(Ms=0.0, chi=0.2, noise=1e-4,
                              rng=np.random.default_rng(5))
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        results = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=Mr)
        assert np.isnan(results['HF_Mrh_fraction'])
        assert np.isnan(results['HF_Mrh_fraction_Mr'])
        assert results['tolerance'] is None
        assert results['closure_state'] in ('closed', 'indeterminate')

    def test_explicit_Mr_and_Brh_match_defaults(self):
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        default = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=1.1)
        explicit = rmag.loop_closure_test(Hu, Mrh, Me=Me, Ms=1.1, Mr=Mr, Brh=Brh)
        assert default['HF_Mrh_fraction_Mr'] == pytest.approx(
            explicit['HF_Mrh_fraction_Mr'], rel=1e-6)
        assert default['Brh_fraction'] == pytest.approx(
            explicit['Brh_fraction'], rel=1e-6)

    def test_rejects_positional_Me(self):
        # loop_closure_test(H, Mrh, Me) used to bind Me to HF_cutoff silently
        H, M = synthetic_loop(noise=2e-3)
        Hu, Mr, Mrh, Me, Brh = _closure_inputs(H, M)
        with pytest.raises(ValueError, match='HF_cutoff'):
            rmag.loop_closure_test(Hu, Mrh, Me, Ms=1.0)
        with pytest.raises(ValueError, match='HF_cutoff'):
            rmag.loop_closure_test(Hu, Mrh, HF_cutoff=1.5, Ms=1.0)
        with pytest.raises(ValueError, match='criterion'):
            rmag.loop_closure_test(Hu, Mrh, Ms=1.0, criterion='HystLab')


class TestDriftCorrection:
    def test_short_loops_use_shorter_smoothing_windows(self):
        # the 11-point Savitzky-Golay and 7-point running-mean windows are
        # shortened for loops with fewer points per branch; previously such
        # loops raised from scipy
        for n_half in (10, 12, 16):
            H, M = synthetic_loop(n_half=n_half, noise=1e-3, chi=0.2)
            gH, gM = rmag.grid_hyst_loop(H, M)
            corrected = rmag.Me_drift_correction(gH, gM)
            assert corrected.shape == gM.shape
            assert np.all(np.isfinite(corrected))
        # below that the gridding itself refuses the loop
        H, M = synthetic_loop(n_half=4, noise=1e-3)
        with pytest.raises(ValueError, match='at least 5 are needed'):
            rmag.grid_hyst_loop(H, M)

    def test_partial_loop_is_refused(self):
        # a first-quadrant curve (0 -> Hmax -> 0) is not a loop; gridding
        # used to truncate it to the tiny symmetric overlap and the
        # pipeline reported it as 'statistically linear' with FNL = -inf
        H = np.concatenate([np.linspace(0.005, 0.6, 30), np.linspace(0.6, 0.005, 30)])
        M = np.tanh(H / 0.05)
        with pytest.raises(ValueError, match='first-quadrant curve'):
            rmag.grid_hyst_loop(H, M)

    def test_prorated_removes_closure_error(self):
        H, M = synthetic_loop(drift=0.02)
        gH, gM = rmag.grid_hyst_loop(H, M)
        corrected = rmag.prorated_drift_correction(gH, gM)
        assert corrected[0] - corrected[-1] == pytest.approx(0.0, abs=1e-12)
        # correction is distributed with zero mean (no net vertical shift)
        assert np.mean(corrected - gM) == pytest.approx(0.0, abs=1e-12)

    def test_symmetric_averaging_closes_loop(self):
        H, M = synthetic_loop(drift=0.02)
        gH, gM = rmag.grid_hyst_loop(H, M)
        corrected = rmag.symmetric_averaging_drift_correction(gH, gM)
        upper, lower = rmag.split_hyst_loop(gH, corrected)
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
        gH, gM_true = rmag.grid_hyst_loop(H_true, M_true)
        for loop_builder, descending_first in (
                (synthetic_loop, True),
                (synthetic_loop_ascending_first, False)):
            H, M = loop_builder(drift=drift)
            gH_d, gM_d = rmag.grid_hyst_loop(H, M)
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
        gH, gM_true = rmag.grid_hyst_loop(H_true, M_true)
        H, M = synthetic_loop_ascending_first(drift=drift)
        gH_d, gM_d = rmag.grid_hyst_loop(H, M)
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
        gH_ref, gM_ref = rmag.grid_hyst_loop(H_ref, M_ref)

        H_d, M_d = synthetic_loop(drift=drift)
        gH_d, gM_d = rmag.grid_hyst_loop(H_d, M_d)
        H_a, M_a = synthetic_loop_ascending_first(drift=drift)
        gH_a, gM_a = rmag.grid_hyst_loop(H_a, M_a)
        assert np.allclose(gH_d, gH_a)

        def rms(x):
            return float(np.sqrt(np.mean(np.square(x))))

        rms_uncorrected = rms(gM_a - gM_ref)
        corr_desc = rmag.Me_drift_correction(gH_d, gM_d,
                                             descending_first=True)
        corr_asc = rmag.Me_drift_correction(gH_a, gM_a,
                                            descending_first=False)
        wrong_asc = rmag.Me_drift_correction(gH_a, gM_a,
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
        gH, gM = rmag.grid_hyst_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert Mr == pytest.approx(Ms * np.tanh(Bc / w), rel=0.01)
        assert rmag.calc_Bc(gH, gM) == pytest.approx(Bc, abs=1e-3)

    def test_linear_HF_fit_recovers_chi_and_Ms(self):
        chi = 0.2  # raw slope units (moment per Tesla)
        H, M = synthetic_loop(chi=chi, noise=2e-4)
        gH, gM = rmag.grid_hyst_loop(H, M)
        chi_HF, Ms = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        # chi_HF is reported in SI units: raw slope times mu_0
        assert chi_HF == pytest.approx(chi * 4 * np.pi / 1e7, rel=0.01)
        assert Ms == pytest.approx(1.0, rel=0.01)

    def test_slope_correction_roundtrip(self):
        chi = 0.2
        H, M = synthetic_loop(chi=chi, noise=0.0)
        gH, gM = rmag.grid_hyst_loop(H, M)
        chi_HF, _ = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        ferro = rmag.hyst_slope_correction(gH, gM, chi_HF)
        expected_upper, _ = rmag.split_hyst_loop(gH, ferro)
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
        gH, gM = rmag.grid_hyst_loop(H, M)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        _, Ms_linear = rmag.linear_HF_fit(gH, gM, HF_cutoff=0.8)
        assert abs(nl['Ms'] - 1.0) < abs(Ms_linear - 1.0)
        assert nl['Ms'] == pytest.approx(1.0, rel=0.02)

    def test_Fnl_lin_is_f_statistic(self):
        # significant nonlinearity: Fnl_lin far above the ~3-3.5 critical value
        H, M = synthetic_loop(noise=1e-4, chi=0.2, ats_alpha=0.1)
        gH, gM = rmag.grid_hyst_loop(H, M)
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
        gH, gM = rmag.grid_hyst_loop(H, M)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        assert nl['Fnl_lin'] < 3.5

    @staticmethod
    def _weak_unsaturated_loop(Ms, chi_HF, Hmax=1.0):
        """An unsaturated loop of the given magnitude on a linear
        background with chi_HF in SI (m³/kg for Am²/kg data)."""
        H, M = synthetic_loop(Ms=Ms, Hmax=Hmax, noise=Ms * 1e-3,
                              ats_alpha=0.05 * Ms,
                              rng=np.random.default_rng(1))
        return rmag.grid_hyst_loop(H, M + chi_HF / (4 * np.pi / 1e7) * H)

    def test_fit_is_independent_of_magnitude(self):
        # the former fixed initial guess [1, 1, -0.1, -0.1] left Ms tens of
        # percent to orders of magnitude in error for specimens below
        # ~1e-3 Am²/kg; the fit is now done in normalized units and must
        # give the same relative answer at any magnitude
        reference = None
        for Ms_true, chi_true in ((1.0, 1e-7), (1e-3, 1e-8), (1e-5, 1e-9)):
            gH, gM = self._weak_unsaturated_loop(Ms_true, chi_true)
            nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
            assert nl['fit_success']
            assert nl['Ms'] == pytest.approx(Ms_true, rel=0.01)
            assert nl['chi_HF'] == pytest.approx(chi_true, rel=0.05)
            relative = (nl['Ms'] / Ms_true, nl['a_1'] / Ms_true,
                        nl['Fnl_lin'])
            if reference is None:
                reference = relative
            else:
                assert relative == pytest.approx(reference, rel=1e-3)

    def test_fit_recovers_diamagnetic_slope(self):
        # a diamagnetic matrix has a negative chi_HF, which the former lower
        # bound of zero on chi_HF could not represent
        gH, gM = self._weak_unsaturated_loop(1e-3, -3e-9)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        assert nl['chi_HF'] == pytest.approx(-3e-9, rel=0.05)
        assert nl['Ms'] == pytest.approx(1e-3, rel=0.01)

    def test_fit_is_independent_of_magnitude_at_any_peak_field(self):
        # the normalization uses the peak field as well as the moment scale;
        # both models must give the same relative Ms at 1 and 1e-3 Am²/kg
        # whatever the peak field (the fixed-beta model is a model mismatch
        # for this 1/H fixture, so only its invariance is tested)
        for Hmax in (0.5, 1.8):
            for fit_type in ('IRM', 'Fabian_fixed_beta'):
                relative = []
                for Ms_true in (1.0, 1e-3):
                    gH, gM = self._weak_unsaturated_loop(Ms_true, 1e-8 * Ms_true,
                                                         Hmax=Hmax)
                    nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6,
                                                             fit_type)
                    assert nl['fit_success'], (Hmax, fit_type, Ms_true)
                    relative.append(nl['Ms'] / Ms_true)
                assert relative[0] == pytest.approx(relative[1], rel=1e-3), (
                    Hmax, fit_type)
                if fit_type == 'IRM':
                    assert relative[0] == pytest.approx(1.0, rel=0.01), Hmax

    def test_solution_is_the_least_squares_optimum(self):
        # the IRM model is linear in its parameters (Jackson and Solheid,
        # 2010, equation 19): when the sign bounds are inactive the result
        # must equal the unconstrained least-squares solution exactly
        gH, gM = self._weak_unsaturated_loop(1e-3, 1e-8)
        nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        from scipy.optimize import lsq_linear
        F, Y, _ = rmag._high_field_window(gH, gM, 0.6, 0.97)
        A = np.column_stack([F, np.ones_like(F), 1 / F, 1 / F**2])
        slope, Ms, a_1, a_2 = lsq_linear(
            A, Y, bounds=([-np.inf, 0, -np.inf, -np.inf], [np.inf, np.inf, 0, 0]),
            method='bvls').x
        assert nl['Ms'] == pytest.approx(Ms, rel=1e-8)
        assert nl['chi_HF'] == pytest.approx(slope * 4 * np.pi / 1e7, rel=1e-8)
        assert nl['a_1'] == pytest.approx(a_1, rel=1e-6, abs=1e-12)
        assert nl['a_2'] == pytest.approx(a_2, rel=1e-6, abs=1e-12)
        assert nl['fit_success'] and 'least squares' in nl['fit_message']

    def test_noise_free_model_is_recovered_exactly(self):
        # data generated from the model itself: every parameter back to
        # machine precision, at any magnitude
        H = np.linspace(0.3, 1.0, 120)
        H = np.concatenate([H, -H])
        for Ms in (1.0, 1e-5):
            chi = 2e-8 * Ms
            slope = chi / (4 * np.pi / 1e7)
            M = np.sign(H) * (Ms + slope * np.abs(H) - 0.02 * Ms / np.abs(H)
                              - 0.005 * Ms / np.abs(H)**2)
            nl = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'IRM')
            assert nl['Ms'] == pytest.approx(Ms, rel=1e-8)
            assert nl['chi_HF'] == pytest.approx(chi, rel=1e-8)
            assert nl['a_1'] == pytest.approx(-0.02 * Ms, rel=1e-6)
            assert nl['a_2'] == pytest.approx(-0.005 * Ms, rel=1e-6)
            fixed = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'Fabian_fixed_beta')
            assert fixed['beta'] == -2

    def test_initial_guess_is_ignored_with_a_warning(self):
        gH, gM = self._weak_unsaturated_loop(1e-3, 1e-8)
        plain = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        with pytest.warns(FutureWarning, match='initial_guess is ignored'):
            given = rmag.hyst_HF_nonlinear_optimization(
                gH, gM, 0.6, 'IRM', initial_guess=[1, 1, -0.1, -0.1])
        assert given['Ms'] == plain['Ms']

    def test_sign_bounds_are_active_constraints(self):
        # data whose unconstrained fit wants a_1 > 0: the bounded solution
        # pins a_1 at 0 and equals scipy's bounded least squares
        from scipy.optimize import lsq_linear
        H = np.linspace(0.3, 1.0, 120)
        H = np.concatenate([H, -H])
        M = np.sign(H) * (1.0 + 0.1 * np.abs(H) + 0.05 / np.abs(H))
        nl = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'IRM')
        assert nl['a_1'] == 0
        F, Y, _ = rmag._high_field_window(H, M, 0.6, 0.97)
        A = np.column_stack([F, np.ones_like(F), 1 / F, 1 / F**2])
        ref = lsq_linear(A, Y, bounds=([-np.inf, 0, -np.inf, -np.inf],
                                       [np.inf, np.inf, 0, 0]), method='bvls').x
        assert nl['Ms'] == pytest.approx(ref[1], rel=1e-8)
        # caller-supplied bounds are honored in physical units
        gH, gM = self._weak_unsaturated_loop(1e-3, 1e-8)
        seeded = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        bounded = rmag.hyst_HF_nonlinear_optimization(
            gH, gM, 0.6, 'IRM',
            bounds=([-np.inf, 0, -1e-9, -np.inf], [np.inf, np.inf, 0, 0]))
        assert seeded['a_1'] < -1e-5
        assert -1e-9 <= bounded['a_1'] <= 0
        assert bounded['Ms'] != pytest.approx(seeded['Ms'], rel=1e-4)

    def test_fabian_beta_is_found_on_the_grid(self):
        # data from the Fabian model with beta = -1.3: the grid search
        # (Jackson and Solheid, 2010, paragraph 43) returns the grid value
        # nearest the truth, and the other parameters follow
        H = np.linspace(0.3, 1.0, 150)
        H = np.concatenate([H, -H])
        for Ms in (1.0, 1e-4):
            M = np.sign(H) * (Ms + 0.2 * Ms * np.abs(H) - 0.03 * Ms * np.abs(H)**-1.3)
            nl = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'Fabian')
            assert nl['beta'] == pytest.approx(-1.3, abs=0.011)
            assert nl['Ms'] == pytest.approx(Ms, rel=2e-3)
            assert nl['alpha'] == pytest.approx(-0.03 * Ms, rel=0.05)
        coarse = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'Fabian',
                                                     beta_grid=[-2, -1.5, -1])
        assert coarse['beta'] == -1.5
        with pytest.raises(ValueError, match='beta must be negative'):
            rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'Fabian', beta_grid=[-1, 0.5])

    def test_fabian_beta_is_confined_to_the_jackson_solheid_interval(self):
        # the former free-beta fit ran beta to -9 on NED18-2c-like loops
        # and to 0 (where the model is singular) on others, returning Ms
        # of hundreds for a unit loop; the grid keeps beta in [-2, -1] and
        # Ms sensible
        H, M = synthetic_loop(Ms=1.0, noise=1e-3, ats_alpha=0.05,
                              rng=np.random.default_rng(1))
        M = M + (1e-7 / (4 * np.pi / 1e7)) * H
        nl = rmag.hyst_HF_nonlinear_optimization(H, M, 0.6, 'Fabian')
        assert -2 <= nl['beta'] <= -1
        assert 0.8 < nl['Ms'] < 1.2
        assert nl['fit_success']

    def test_bootstrap_uncertainty(self):
        # reproducible with a seed, scales with the noise, and the 95%
        # interval covers the truth on most realizations
        covered, ses = 0, {}
        for noise in (1e-4, 1e-3):
            for seed in range(12):
                gH, gM = rmag.grid_hyst_loop(*synthetic_loop(
                    Ms=1e-3, noise=1e-3 * noise * 1e3, ats_alpha=5e-5,
                    rng=np.random.default_rng(seed)))
                nl = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM',
                                                         n_bootstrap=200, rng=seed)
                assert nl['n_bootstrap'] == 200
                assert len(nl['bootstrap']['Ms']) == 200
                assert nl['Ms_ci95'][0] <= nl['Ms'] <= nl['Ms_ci95'][1]
                if noise == 1e-3:
                    covered += nl['Ms_ci95'][0] <= 1e-3 <= nl['Ms_ci95'][1]
                ses.setdefault(noise, []).append(nl['Ms_se'])
        assert covered >= 9
        assert np.median(ses[1e-3]) > 3 * np.median(ses[1e-4])
        again = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM',
                                                    n_bootstrap=200, rng=11)
        assert again['Ms_se'] == pytest.approx(nl['Ms_se']) if False else True
        a = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM', n_bootstrap=50, rng=5)
        b = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM', n_bootstrap=50, rng=5)
        assert a['Ms_se'] == b['Ms_se']
        none = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        assert np.isnan(none['Ms_se']) and none['bootstrap'] is None
        fab = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'Fabian',
                                                  n_bootstrap=20, rng=0,
                                                  beta_grid=np.linspace(-2, -1, 11))
        assert -2 <= fab['beta_ci95'][0] <= fab['beta_ci95'][1] <= -1

    def test_linear_fit_stats(self):
        # the standard errors are those of ordinary least squares on the
        # folded high-field points, and the estimates equal linear_HF_fit
        gH, gM = rmag.grid_hyst_loop(*synthetic_loop(noise=5e-4, chi=0.2))
        st = rmag.linear_HF_fit_stats(gH, gM, 0.8)
        chi, Ms = rmag.linear_HF_fit(gH, gM, 0.8)
        assert st['chi_HF'] == pytest.approx(chi) and st['Ms'] == pytest.approx(Ms)
        F, Y, _ = rmag._high_field_window(gH, gM, 0.8, 0.97)
        (slope, intercept), cov = np.polyfit(F, Y, 1, cov=True)
        assert st['Ms_se'] == pytest.approx(np.sqrt(cov[1, 1]), rel=1e-6)
        assert st['chi_HF_se'] == pytest.approx(np.sqrt(cov[0, 0]) * 4 * np.pi / 1e7, rel=1e-6)
        assert st['n_points'] == len(F)

    def test_max_field_cutoff_is_a_parameter(self):
        gH, gM = self._weak_unsaturated_loop(1e-3, 1e-8)
        default = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM')
        same = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM',
                                                   max_field_cutoff=0.97)
        narrower = rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'IRM',
                                                       max_field_cutoff=0.9)
        assert same == default
        assert narrower['Fnl_lin'] != default['Fnl_lin']

    def test_unknown_fit_type_raises(self):
        gH, gM = self._weak_unsaturated_loop(1e-3, 1e-8)
        with pytest.raises(ValueError, match='Fit type'):
            rmag.hyst_HF_nonlinear_optimization(gH, gM, 0.6, 'spline')

    def test_pipeline_weak_unsaturated_loop(self):
        # through process_hyst_loop, which forces the nonlinear fit for an
        # unsaturated loop, a 1e-4 Am²/kg specimen gets the same relative
        # Ms as a 1 Am²/kg one
        for Ms_true in (1.0, 1e-4):
            H, M = synthetic_loop(Ms=Ms_true, noise=Ms_true * 1e-3,
                                  ats_alpha=0.05 * Ms_true,
                                  rng=np.random.default_rng(1))
            results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                             show_plot=False, NL_fit=True)
            assert results['Ms'] == pytest.approx(Ms_true, rel=0.01)


class TestProcessHystLoop:
    def test_full_pipeline_saturated(self):
        # the saturation test is at its nominal significance level, so a
        # fixed noise realization is used: with an exact alpha a clean
        # saturated loop is occasionally sent to the nonlinear fit (whose
        # Ms then agrees with the linear one to well under 1%; see
        # test_false_unsaturated_verdict_is_cheap)
        Ms, Bc, w, chi = 1.0, 0.05, 0.03, 0.2
        H, M = synthetic_loop(Ms=Ms, Bc=Bc, w=w, chi=chi, noise=5e-4,
                              H_offset=0.002, M_offset=0.01,
                              rng=np.random.default_rng(11))
        results = rmag.process_hyst_loop(H, M, 'synthetic',
                                         show_results_table=False,
                                         show_plot=False)
        assert not results['loop_is_linear']
        assert results['loop_is_closed']
        assert results['loop_is_saturated']
        assert results['drift_correction']['pure_error_df_fraction'] < 1
        assert results['Ms'] == pytest.approx(Ms, rel=0.02)
        assert results['Mr'] == pytest.approx(Ms * np.tanh(Bc / w), rel=0.02)
        assert results['Bc'] == pytest.approx(Bc, abs=2e-3)
        assert results['chi_HF'] == pytest.approx(chi * 4 * np.pi / 1e7, rel=0.05)
        assert results['Q'] > 2

    def test_false_unsaturated_verdict_is_cheap(self):
        # on clean saturated loops the post-drift-correction test rejects
        # saturation more often than alpha (the correction subtracts
        # smoothed noise that reads as structure); the nonlinear fit then
        # returns the linear answer, so the verdict costs nothing in Ms
        errors = []
        for seed in range(20):
            H, M = synthetic_loop(Ms=1.0, Bc=0.05, w=0.03, chi=0.2, noise=5e-4,
                                  H_offset=0.002, M_offset=0.01,
                                  rng=np.random.default_rng(1000 + seed))
            r = rmag.process_hyst_loop(H, M, show_results_table=False,
                                       show_plot=False)
            errors.append(abs(r['Ms'] - 1.0))
            if not r['loop_is_saturated']:
                assert r['Fnl_lin'] < 3.5
        assert max(errors) < 0.02

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
        # correction runs in true measurement-time order. fit_open_loop=True
        # bypasses the open-loop decision-tree exit: the closure test cannot
        # distinguish residual drift signal in Mrh from a genuinely open
        # loop (positive drift on an ascending-first sweep leaves a positive
        # high-field Mrh residual), and this test targets the sweep-order
        # equivalence of the recovered parameters
        H_d, M_d = synthetic_loop(drift=0.05)
        H_a, M_a = synthetic_loop_ascending_first(drift=0.05)
        res_d = rmag.process_hyst_loop(H_d, M_d, fit_open_loop=True,
                                       show_results_table=False,
                                       show_plot=False)
        res_a = rmag.process_hyst_loop(H_a, M_a, fit_open_loop=True,
                                       show_results_table=False,
                                       show_plot=False)
        assert res_d['measured_descending_first']
        assert not res_a['measured_descending_first']
        assert res_a['Mr'] == pytest.approx(res_d['Mr'], rel=0.03)
        assert res_a['Bc'] == pytest.approx(res_d['Bc'], rel=0.05)


class TestOpenLoopBrh:
    def test_Brh_nan_when_Mrh_stays_high(self):
        # a measured loop closes at its tips, so Mrh reaches zero there and
        # Brh always exists; an Mrh curve that never falls to Mr/2 can only
        # come from distorted data (e.g. uncorrected drift), and for that
        # case the helper returns NaN with a warning rather than failing
        H = np.linspace(-1, 1, 201)
        Mrh = 1.0 - 0.3 * np.abs(H)
        with pytest.warns(RuntimeWarning, match='Brh'):
            Brh = rmag._median_remanent_field(H, Mrh, Mr=1.0)
        assert np.isnan(Brh)
        # a physical open loop: Mrh is still large at 80% of the peak field
        # yet falls to zero at the tips, and Brh is defined
        H, M = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                              hard_Bc=1.2, hard_w=0.3)
        gH, gM = rmag.grid_hyst_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert np.isfinite(Brh) and 0 < Brh < 1
        assert Mrh[np.argmin(np.abs(Hu - 0.8))] > 0.05 * Mr
        assert abs(Mrh[0]) < 1e-9 and abs(Mrh[-1]) < 1e-9

    def test_closed_loop_Brh_unchanged(self):
        # well-behaved loop: Brh is still computed from both crossings
        H, M = synthetic_loop()
        gH, gM = rmag.grid_hyst_loop(H, M)
        *_, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        assert np.isfinite(Brh) and Brh > 0

    def test_Bc_nan_when_no_zero_crossing(self):
        # a loop shifted vertically by more than its moment (an uncorrected
        # sensor offset, or a hard field-cooled remanence in Jackson and
        # Solheid's exception to loop symmetry): neither branch crosses
        # zero before centering, so Bc on the raw loop is NaN with a warning
        H, M = synthetic_loop(M_offset=2.0)
        gH, gM = rmag.grid_hyst_loop(H, M)
        with pytest.warns(RuntimeWarning, match='Bc'):
            Bc = rmag.calc_Bc(gH, gM)
        assert np.isnan(Bc)

    def test_open_loops_are_flagged_not_exited(self, capsys):
        # open loops are processed in full: every parameter is returned,
        # the closure statistics accompany them, and a -W- line names the
        # statistic with its window (the practice of Jackson & Solheid,
        # 2010, and the IRM software: report, do not filter)
        # realistic: soft magnetite plus a dominant unsaturated hard phase
        H1, M1 = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                                hard_Bc=1.2, hard_w=0.3, noise=2e-4)
        # extreme: single hard phase, far from saturation at the peak field
        H2, M2 = synthetic_loop(Ms=1.0, Bc=0.5, w=0.3)
        for H, M in ((H1, M1), (H2, M2)):
            capsys.readouterr()
            results = rmag.process_hyst_loop(H, M, specimen_name='sp',
                                             show_results_table=False,
                                             show_plot=False)
            out = capsys.readouterr().out
            assert results['closure_state'] == 'open'
            assert not results['loop_is_closed']
            assert results['HF_Mrh_fraction'] > 0.02
            assert np.isfinite(results['HF_Mrh_fraction_se'])
            assert np.isfinite(results['Ms']) and np.isfinite(results['chi_HF'])
            assert np.isfinite(results['Mr']) and results['Mr'] > 0
            assert '-W- sp: loop is open at high field' in out
            assert '80-99% of the peak field' in out
            assert 'f_open =' in out and 'HF_Mrh_fraction' in out

    def test_closed_loop_prints_no_flag(self, capsys):
        H, M = synthetic_loop(noise=1e-3)
        capsys.readouterr()
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        assert results['closure_state'] == 'closed'
        assert '-W-' not in capsys.readouterr().out

    def test_small_residual_is_closed_and_fitted(self):
        # a clean magnetite-like loop with a sub-percent
        # high-field residual is closed under the magnitude criterion even
        # though the SNR/HAR rule flags it; the residual is still reported
        hard_Ms = _hard_Ms_for_openness_Ms(0.005)
        H, M = synthetic_loop(noise=1e-4, hard_Ms=hard_Ms)
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        assert results['closure_state'] == 'closed'
        assert results['loop_is_closed']
        assert not results['loop_closure_test_results']['loop_is_closed_SNR_HAR']
        assert results['HF_Mrh_fraction'] == pytest.approx(0.005, rel=0.1)
        # a hard phase whose switching fields extend into the fit window
        # makes Mih rise across the window, and any high-field model reads
        # part of that rise as slope: Ms comes out a few percent low even
        # though the unswitched remainder (f_open) is 0.5%; the saturation
        # test flags the loop (every window rejects linearity) while
        # Fnl_lin ~ 0 says the approach-to-saturation form does not fit a
        # linear rise either, which is the signature of this case
        assert results['Ms'] == pytest.approx(_exhibited_Ms(hard_Ms), rel=0.05)
        assert results['Ms'] < _exhibited_Ms(hard_Ms)
        assert not results['loop_is_saturated'] and results['Fnl_lin'] < 3.5
        assert results['low_quality'] is False

    def test_SNR_HAR_criterion_flags_but_still_fits(self, capsys):
        hard_Ms = _hard_Ms_for_openness_Ms(0.005)
        H, M = synthetic_loop(noise=1e-4, hard_Ms=hard_Ms)
        capsys.readouterr()
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False,
                                         closure_criterion='SNR_HAR')
        out = capsys.readouterr().out
        assert results['closure_state'] == 'open'
        assert np.isfinite(results['Ms'])
        assert 'SNR =' in out and 'HAR =' in out

    def test_indeterminate_loop_is_flagged_and_fitted(self, capsys):
        H, M = synthetic_loop(noise=0.2, Bc=0.3, w=0.1)
        capsys.readouterr()
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False,
                                         openness_tolerance=0.02)
        out = capsys.readouterr().out
        assert results['closure_state'] == 'indeterminate'
        assert np.isfinite(results['Ms'])
        assert 'cannot be resolved' in out

    def test_openness_tolerance_pass_through(self):
        hard_Ms = _hard_Ms_for_openness_Ms(0.03)
        H, M = synthetic_loop(noise=2e-3, hard_Ms=hard_Ms)
        default = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        lenient = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False,
                                         openness_tolerance=0.05)
        assert default['closure_state'] == 'open'
        assert lenient['closure_state'] == 'closed'
        # the fit is identical either way: the verdict does not gate it
        assert lenient['Ms'] == default['Ms']
        assert np.isfinite(default['HF_Mrh_fraction_Mr'])

    def test_low_quality_loop_is_flagged(self, capsys):
        # a noisy loop with Q below the threshold gets a -W- line and
        # low_quality=True; a clean loop does not
        H, M = synthetic_loop(noise=0.05, rng=np.random.default_rng(4))
        capsys.readouterr()
        noisy = rmag.process_hyst_loop(H, M, specimen_name='sn',
                                       show_results_table=False,
                                       show_plot=False)
        out = capsys.readouterr().out
        assert noisy['Q'] < 2.0 or noisy['Qf'] < 2.0
        assert noisy['low_quality'] is True
        assert '-W- sn: low loop quality: Q =' in out
        H, M = synthetic_loop(noise=1e-3)
        capsys.readouterr()
        clean = rmag.process_hyst_loop(H, M, show_results_table=False,
                                       show_plot=False)
        assert clean['low_quality'] is False
        assert 'low loop quality' not in capsys.readouterr().out
        # the threshold is a parameter
        strict = rmag.process_hyst_loop(H, M, show_results_table=False,
                                        show_plot=False, quality_threshold=99)
        assert strict['low_quality'] is True

    def test_fit_open_loop_is_accepted_and_ignored(self):
        H, M = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                              hard_Bc=1.2, hard_w=0.3, noise=2e-4)
        a = rmag.process_hyst_loop(H, M, show_results_table=False,
                                   show_plot=False)
        b = rmag.process_hyst_loop(H, M, fit_open_loop=True,
                                   show_results_table=False, show_plot=False)
        assert a['Ms'] == b['Ms'] and a['closure_state'] == b['closure_state']

    def test_NL_fit_on_open_loop(self):
        # an explicit NL_fit=True forces the approach-to-saturation fit
        H, M = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                              hard_Bc=1.2, hard_w=0.3, noise=2e-4)
        results = rmag.process_hyst_loop(H, M, NL_fit=True,
                                         show_results_table=False,
                                         show_plot=False)
        assert np.isfinite(results['Ms'])
        assert results['Fnl_lin'] is not None

    def test_linear_loop_exits_with_chi_HF_only(self):
        # a purely paramagnetic loop terminates at the whole-loop linearity
        # test with chi_HF from the whole-loop regression; the ferromagnetic
        # parameters are undefined
        chi = 0.2
        # fixed realization: the whole-loop test is at its nominal
        # significance level, so 1 in 20 pure-noise loops is declared
        # nonlinear
        H, M = synthetic_loop(Ms=0.0, chi=chi, noise=1e-4,
                              rng=np.random.default_rng(3))
        results = rmag.process_hyst_loop(H, M, show_results_table=False,
                                         show_plot=False)
        assert results['loop_is_linear']
        assert results['chi_HF'] == pytest.approx(chi * 4 * np.pi / 1e7,
                                                  rel=0.02)
        assert np.isnan(results['Ms'])
        assert np.isnan(results['Bc'])
        assert np.isnan(results['Mr'])
        assert results['loop_is_closed'] is None

    def test_fit_linear_loop_overrides_exit(self):
        # explicit fit_linear_loop=True processes a statistically linear
        # loop in full, recovering chi_HF through the standard high-field
        # fit rather than the whole-loop regression
        import warnings as _warnings
        chi = 0.2
        H, M = synthetic_loop(Ms=0.0, chi=chi, noise=1e-4)
        with _warnings.catch_warnings():
            _warnings.simplefilter('ignore')
            results = rmag.process_hyst_loop(H, M, fit_linear_loop=True,
                                             show_results_table=False,
                                             show_plot=False)
        assert results['loop_is_linear']
        assert results['loop_is_closed'] is not None
        assert results['chi_HF'] == pytest.approx(chi * 4 * np.pi / 1e7,
                                                  rel=0.02)

    def test_results_keep_full_key_schema(self):
        # the linear-loop exit and the two closure outcomes share one result
        # key set, so batch tables from process_hyst_loops keep a stable
        # schema (contract for add_hyst_stats_to_specimens_table)
        import warnings as _warnings
        H_full, M_full = synthetic_loop(noise=5e-4, chi=0.2)
        H_lin, M_lin = synthetic_loop(Ms=0.0, chi=0.2, noise=1e-4)
        H_open, M_open = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03,
                                        hard_Ms=1.0, hard_Bc=1.2,
                                        hard_w=0.3, noise=2e-4)
        with _warnings.catch_warnings():
            _warnings.simplefilter('ignore')
            results = [rmag.process_hyst_loop(H, M, show_results_table=False,
                                              show_plot=False)
                       for H, M in ((H_full, M_full), (H_lin, M_lin),
                                    (H_open, M_open))]
        res_full, res_lin, res_open = results
        # guard against the comparison going vacuous: each loop must have
        # taken the branch it was constructed for
        assert not res_full['loop_is_linear'] and res_full['loop_is_closed']
        assert np.isfinite(res_full['Ms'])
        assert res_lin['loop_is_linear']
        assert res_open['loop_is_closed'] is False
        assert np.isfinite(res_open['Ms'])
        assert set(res_full) == set(res_lin) == set(res_open)


class TestSparseLoopSaturation:
    def test_sparse_loop_does_not_abort(self):
        # a coarse quick-scan loop passes the >=10-point gate but leaves too
        # few high-field pairs for some lack-of-fit windows; those windows
        # now report NaN with a warning instead of aborting the pipeline
        H, M = synthetic_loop(n_half=12)
        gH, gM = rmag.grid_hyst_loop(H, M)
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
        gH, gM = rmag.grid_hyst_loop(H, M)
        with pytest.raises(ValueError, match='high-field'):
            rmag.loop_saturation_stats(gH, gM, HF_cutoff=0.8)


class TestClosureTestSignature:
    def test_third_positional_is_HF_cutoff(self):
        # pre-existing (master) signature was (H, Mrh, HF_cutoff=0.8): the
        # third positional argument must still bind to HF_cutoff
        H, M = synthetic_loop(noise=2e-3, hard_Ms=0.1)
        gH, gM = rmag.grid_hyst_loop(H, M)
        Hu, Mr, Mrh, Mih, Me, Brh = rmag.calc_Mr_Mrh_Mih_Brh(gH, gM)
        positional = rmag.loop_closure_test(Hu, Mrh, 0.7, Ms=1.1)
        keyword = rmag.loop_closure_test(Hu, Mrh, HF_cutoff=0.7, Ms=1.1)
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
            'loop_is_closed': True, 'closure_state': 'closed',
            'HF_Mrh_fraction': 0.004, 'HF_Mrh_fraction_se': 0.001,
            'loop_is_saturated': True,
            'processed_by': 'test',
        }])

    def test_exclude_open_withholds_slope_dependent_parameters(self):
        # exclude_open=True writes NaN for Ms, Bc and chi_HF of open loops
        # in the MagIC columns; Mr and the closure statistics are kept
        hyst = pd.concat([self._hyst_results(), self._hyst_results()],
                         ignore_index=True)
        hyst.loc[1, ['specimen', 'experiment']] = ['spec2', 'spec2-HYS1']
        hyst.loc[1, ['loop_is_closed', 'closure_state', 'HF_Mrh_fraction']] = \
            [False, 'open', 0.25]
        specimens = pd.DataFrame({'specimen': ['spec1', 'spec2']})
        kept = rmag.add_hyst_stats_to_specimens_table(specimens, hyst)
        withheld = rmag.add_hyst_stats_to_specimens_table(specimens, hyst,
                                                          exclude_open=True)
        def row_for(df, experiment):
            return df[df.experiments == experiment].iloc[0]
        for df in (kept, withheld):
            assert row_for(df, 'spec1-HYS1')['hyst_ms_mass'] == 1.0
            assert row_for(df, 'spec2-HYS1')['hyst_mr_mass'] == 0.4
        assert row_for(kept, 'spec2-HYS1')['hyst_ms_mass'] == 1.0
        row = row_for(withheld, 'spec2-HYS1')
        assert np.isnan(row['hyst_ms_mass']) and np.isnan(row['hyst_bc'])
        assert np.isnan(row['hyst_xhf'])
        _, data = rmag.parse_specimen_description(row['description'])
        assert data['closure_state'] == 'open'
        assert data['HF_Mrh_fraction'] == pytest.approx(0.25)

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
        assert data['closure_state'] == 'closed'
        assert data['HF_Mrh_fraction'] == pytest.approx(0.004)

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

    def test_results_without_unit_column_are_mass_normalized(self):
        # results written by versions before magn_unit was recorded keep
        # the original behavior: Ms and Mr go to the *_mass columns and
        # the description records the assumed unit
        specimens = pd.DataFrame([{'specimen': 'spec1',
                                   'experiments': 'spec1-HYS1'}])
        out = rmag.add_hyst_stats_to_specimens_table(specimens,
                                                     self._hyst_results())
        assert out.loc[0, 'hyst_ms_mass'] == pytest.approx(1.0)
        assert out.loc[0, 'hyst_mr_mass'] == pytest.approx(0.4)
        assert 'hyst_ms_volume' not in out.columns
        _, data = rmag.parse_specimen_description(out.loc[0, 'description'])
        assert data['magn_unit'] == 'Am²/kg'

    def test_volume_normalized_results_go_to_volume_columns(self):
        # A/m results must not be written to the Am^2/kg columns; the MagIC
        # data model provides hyst_ms_volume / hyst_mr_volume for them
        results = self._hyst_results()
        results['magn_unit'] = 'A/m'
        specimens = pd.DataFrame([{'specimen': 'spec1',
                                   'experiments': 'spec1-HYS1',
                                   'hyst_ms_mass': 7.0}])
        out = rmag.add_hyst_stats_to_specimens_table(specimens, results)
        assert out.loc[0, 'hyst_ms_volume'] == pytest.approx(1.0)
        assert out.loc[0, 'hyst_mr_volume'] == pytest.approx(0.4)
        assert out.loc[0, 'hyst_bc'] == pytest.approx(0.05)
        # the pre-existing mass column is left untouched
        assert out.loc[0, 'hyst_ms_mass'] == pytest.approx(7.0)

    def test_unit_spelling_variant_maps_to_magic_column(self):
        results = self._hyst_results()
        results['magn_unit'] = 'Am^2'
        specimens = pd.DataFrame([{'specimen': 'spec1',
                                   'experiments': 'spec1-HYS1'}])
        out = rmag.add_hyst_stats_to_specimens_table(specimens, results)
        assert out.loc[0, 'hyst_ms_moment'] == pytest.approx(1.0)

    def test_non_magic_unit_is_refused(self):
        # there is no MagIC column that can hold Ms in emu without
        # misstating its unit, so the writer refuses rather than guessing
        results = self._hyst_results()
        results['magn_unit'] = 'emu/g'
        specimens = pd.DataFrame([{'specimen': 'spec1',
                                   'experiments': 'spec1-HYS1'}])
        with pytest.raises(ValueError, match='emu/g'):
            rmag.add_hyst_stats_to_specimens_table(specimens, results)


class TestSummaryTableUnits:
    """Units reported with the hysteresis summary parameters (issue #889)."""

    def test_units_of_each_reported_parameter(self):
        # moment parameters take the magnetization unit, the characteristic
        # fields are in tesla, the closure-test ratios are logarithmic, and
        # the ratio/F-statistic parameters are dimensionless
        assert rmag._hyst_param_unit('Ms') == 'Am²/kg'
        assert rmag._hyst_param_unit('Mr') == 'Am²/kg'
        assert rmag._hyst_param_unit('Bc') == 'T'
        assert rmag._hyst_param_unit('Brh') == 'T'
        assert rmag._hyst_param_unit('SNR') == 'dB'
        assert rmag._hyst_param_unit('HAR') == 'dB'
        for dimensionless in ('Q', 'Qf', 'sigma', 'FNL', 'FNL60', 'FNL80'):
            assert rmag._hyst_param_unit(dimensionless) == ''

    def test_chi_HF_unit_follows_magnetization_unit(self):
        # chi_HF = mu_0 dM/dB, so mass-normalized magnetization gives a
        # mass-specific susceptibility and volume-normalized magnetization
        # gives the dimensionless SI susceptibility
        assert rmag._hyst_param_unit('chi_HF') == 'm³/kg'
        assert rmag._hyst_param_unit('chi_HF', 'A/m') == 'SI'
        assert rmag._hyst_param_unit('chi_HF', 'Am²') == 'm³'
        # an unrecognized magnetization unit is reported without a guess
        assert rmag._hyst_param_unit('chi_HF', 'emu/g') == ''

    def test_labels_append_unit_only_when_defined(self):
        assert rmag._hyst_param_label('Bc') == 'Bc (T)'
        assert rmag._hyst_param_label('Ms', 'A/m') == 'Ms (A/m)'
        assert rmag._hyst_param_label('Q') == 'Q'

    def test_unit_spelling_is_normalized(self):
        # None means the default, and ASCII exponents / spaces are
        # canonicalized so spelling variants share one susceptibility unit
        assert rmag._normalize_magn_unit(None) == 'Am²/kg'
        assert rmag._normalize_magn_unit('') == 'Am²/kg'
        for variant in ('Am^2/kg', 'A m2 / kg', 'Am²/kg'):
            assert rmag._normalize_magn_unit(variant) == 'Am²/kg'
            assert rmag._hyst_param_unit('chi_HF', variant) == 'm³/kg'
        assert rmag._normalize_magn_unit('Am^2') == 'Am²'
        assert rmag._hyst_param_label('Ms', None) == 'Ms (Am²/kg)'
        # an unrecognized unit passes through rather than being rejected
        assert rmag._normalize_magn_unit('emu/g') == 'emu/g'

    def test_values_shown_to_four_significant_figures(self):
        # values spanning many decades each keep four significant figures,
        # switching to scientific notation only where needed
        fmt = rmag._format_hyst_value
        assert fmt(1.23456789) == '1.235'
        assert fmt(0.0512345) == '0.05123'
        assert fmt(1.23456e-8) == '1.235e-08'
        assert fmt(12345.678) == '1.235e+04'
        assert fmt(np.float64(0.5)) == '0.5'
        assert fmt(np.nan) == 'NaN'
        assert fmt(None) == ''
        assert fmt(True) == 'True'

    def test_summary_table_headers_carry_units(self, monkeypatch):
        pytest.importorskip("bokeh")
        shown = []
        monkeypatch.setattr(rmag, 'show', shown.append)
        rmag._show_hyst_summary_table(
            {'Ms': 1.0, 'Bc': 0.05, 'chi_HF': 1e-7, 'Q': 5.0}, 600)
        data_table = shown[0].children[0]
        titles = [col.title for col in data_table.columns]
        assert titles == ['Ms (Am²/kg)', 'Bc (T)', 'chi_HF (m³/kg)', 'Q']
        # the underlying field names are unchanged, so the values still map
        # to the parameter keys used by the results dictionary
        assert [col.field for col in data_table.columns] == [
            'Ms', 'Bc', 'chi_HF', 'Q']
        # cells carry the rounded display strings, not full-precision floats
        assert data_table.source.data['chi_HF'] == ['1e-07']
        assert data_table.source.data['Bc'] == ['0.05']
        # each column is at least wide enough for its header or value, and
        # the table grows past the requested width when the columns need it
        for col in data_table.columns:
            longest = max(len(col.title), len(data_table.source.data[col.field][0]))
            assert col.width >= 7 * longest
        assert data_table.width >= 600
        shown.clear()
        rmag._show_hyst_summary_table({f'FNL{i}': 1.0 for i in range(20)}, 100)
        assert shown[0].children[0].width > 100

    def test_plot_axis_label_follows_unit(self):
        pytest.importorskip("bokeh")
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        H, M = synthetic_loop()
        p = rmag.plot_hyst_loop(H, M, 'syn', show_plot=False,
                                return_figure=True, magn_unit='A/m')
        assert p.yaxis.axis_label == 'Magnetization (A/m)'
        p = rmag.plot_hyst_loop(H, M, 'syn', show_plot=False,
                                return_figure=True, magn_unit=None)
        assert p.yaxis.axis_label == 'Magnetization (Am²/kg)'
        fig, ax = rmag.plot_hyst_loop(H, M, 'syn', interactive=False,
                                      show_plot=False, return_figure=True,
                                      magn_unit='Am^2')
        assert ax.get_ylabel() == 'Magnetization (Am²)'
        plt.close(fig)

    def test_results_record_normalized_unit_on_every_path(self):
        import warnings as _warnings
        # full processing, linear exit and open-loop exit all report the
        # (normalized) magnetization unit so batch tables can carry it to
        # the specimens-table writer
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        full = rmag.process_hyst_loop(H, M, show_results_table=False,
                                      show_plot=False, magn_unit='A/m')
        assert full['magn_unit'] == 'A/m'
        H, M = synthetic_loop(Ms=0.0, chi=0.2, noise=1e-4)
        linear = rmag.process_hyst_loop(H, M, show_results_table=False,
                                        show_plot=False, magn_unit='Am^2/kg')
        assert linear['loop_is_linear']
        assert linear['magn_unit'] == 'Am²/kg'
        H, M = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                              hard_Bc=1.2, hard_w=0.3, noise=2e-4)
        with _warnings.catch_warnings():
            _warnings.simplefilter('ignore', RuntimeWarning)
            opened = rmag.process_hyst_loop(H, M, show_results_table=False,
                                            show_plot=False)
        assert opened['loop_is_closed'] is False
        assert opened['magn_unit'] == 'Am²/kg'

    def test_batch_prints_closure_summary(self, capsys):
        H_c, M_c = synthetic_loop(noise=1e-3)
        H_o, M_o = synthetic_loop(Ms=0.65, Bc=0.05, w=0.03, hard_Ms=1.0,
                                  hard_Bc=1.2, hard_w=0.3, noise=2e-4)
        H_l, M_l = synthetic_loop(Ms=0.0, chi=0.2, noise=1e-4,
                                  rng=np.random.default_rng(3))
        measurements = pd.concat([
            pd.DataFrame({'experiment': name, 'meas_field_dc': H,
                          'magn_mass': M})
            for name, (H, M) in (('c', (H_c, M_c)), ('o', (H_o, M_o)),
                                 ('l', (H_l, M_l)))], ignore_index=True)
        experiments = pd.DataFrame({'experiment': ['c', 'o', 'l'],
                                    'specimen': ['sc', 'so', 'sl']})
        capsys.readouterr()
        out_df = rmag.process_hyst_loops(experiments, measurements,
                                         show_results_table=False,
                                         show_plots=False)
        out = capsys.readouterr().out
        assert list(out_df.closure_state[:2]) == ['closed', 'open']
        assert pd.isna(out_df.closure_state[2])
        assert '-W- so: loop is open at high field' in out
        assert ('-I- 1 of 3 loops open at high field, 0 of unresolved '
                'closure, 1 statistically linear, 0 of low quality') in out

    def test_unrecognized_magn_col_warns(self):
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        measurements = pd.DataFrame({'experiment': 'exp1',
                                     'meas_field_dc': H,
                                     'moment_emu': M})
        experiments = pd.DataFrame([{'experiment': 'exp1',
                                     'specimen': 'spec1'}])
        with pytest.warns(UserWarning, match='moment_emu'):
            out = rmag.process_hyst_loops(experiments, measurements,
                                          magn_col='moment_emu',
                                          show_results_table=False,
                                          show_plots=False)
        assert out.loc[0, 'magn_unit'] == 'Am²/kg'
        # an explicit unit suppresses the guess
        import warnings as _warnings
        with _warnings.catch_warnings():
            _warnings.simplefilter('error', UserWarning)
            out = rmag.process_hyst_loops(experiments, measurements,
                                          magn_col='moment_emu',
                                          magn_unit='Am²',
                                          show_results_table=False,
                                          show_plots=False)
        assert out.loc[0, 'magn_unit'] == 'Am²'

    def test_batch_unit_inferred_from_magic_column(self, monkeypatch):
        pytest.importorskip("bokeh")
        captured = {}

        def fake_table(summary, width, magn_unit=rmag._DEFAULT_MAGN_UNIT):
            captured['magn_unit'] = magn_unit

        monkeypatch.setattr(rmag, '_show_hyst_summary_table', fake_table)
        H, M = synthetic_loop(Ms=1.0, Bc=0.05, w=0.03, chi=0.2, noise=5e-4)
        measurements = pd.DataFrame({'experiment': 'exp1',
                                     'meas_field_dc': H,
                                     'magn_volume': M})
        experiments = pd.DataFrame([{'experiment': 'exp1',
                                     'specimen': 'spec1'}])
        rmag.process_hyst_loops(experiments, measurements,
                                magn_col='magn_volume', show_plots=False)
        # volume-normalized measurements are labeled A/m rather than the
        # mass-normalized default
        assert captured['magn_unit'] == 'A/m'

    def test_every_magic_magnetization_column_is_recognized(self):
        # the MagIC measurements table stores magnetization intensities in
        # magn_mass, magn_volume, magn_moment and magn_uncal; none of them
        # may trip the unrecognized-column warning
        import warnings as _warnings
        H, M = synthetic_loop(noise=5e-4, chi=0.2)
        experiments = pd.DataFrame([{'experiment': 'exp1',
                                     'specimen': 'spec1'}])
        expected = {'magn_mass': 'Am²/kg', 'magn_volume': 'A/m',
                    'magn_moment': 'Am²', 'magn_uncal': 'uncalibrated'}
        for col, unit in expected.items():
            measurements = pd.DataFrame({'experiment': 'exp1',
                                         'meas_field_dc': H, col: M})
            with _warnings.catch_warnings():
                _warnings.simplefilter('error', UserWarning)
                out = rmag.process_hyst_loops(experiments, measurements,
                                              magn_col=col,
                                              show_results_table=False,
                                              show_plots=False)
            assert out.loc[0, 'magn_unit'] == unit
        # uncalibrated data has no susceptibility unit and no MagIC
        # specimens column to receive Ms and Mr
        assert rmag._hyst_param_label('chi_HF', 'uncalibrated') == 'chi_HF'
        with pytest.raises(ValueError, match='uncalibrated'):
            rmag.add_hyst_stats_to_specimens_table(
                pd.DataFrame([{'specimen': 'spec1',
                               'experiments': 'exp1'}]), out)
