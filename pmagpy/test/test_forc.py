"""Tests for FORC reading, conditioning, smoothing and profile extraction.

The numerical tests are anchored on cases with closed-form answers: a
quadratic magnetization surface whose mixed derivative is a known constant,
and a Preisach assemblage whose FORC distribution is a known analytic
function. The remaining tests exercise the file readers and the field
conventions against synthetic MicroMag exports written by the fixtures below.
"""

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.stats import norm

from pmagpy import forc


# ---------------------------------------------------------------- fixtures

def quadratic_grid(size=25):
    """Return a triangular grid sampled from a known quadratic surface."""
    Ha_vals = np.linspace(-0.03, 0.03, size)   # reversal fields
    Hb_vals = np.linspace(-0.03, 0.03, size)   # applied fields
    Ha, Hb = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    M = (
        0.2
        + 0.3 * Hb
        - 0.4 * Ha
        + 8.0 * Hb ** 2
        + 0.7 * Hb * Ha
        - 4.0 * Ha ** 2
    )
    M[Hb < Ha] = np.nan
    return Ha_vals, Hb_vals, M


def write_micromag(path, n_forc=40, ha_min=-0.20, ha_max=0.02, h_max=0.25,
                   step=0.005, drift_amp=0.0, units="SI", eq_header=False,
                   third_column=False, descending=True):
    """Write a synthetic MicroMag FORC export.

    Args:
        path: Destination file.
        n_forc: Number of reversal curves.
        ha_min: Most negative reversal field, in tesla.
        ha_max: Least negative reversal field, in tesla.
        h_max: Maximum applied field and calibration field, in tesla.
        step: Applied-field increment, in tesla.
        drift_amp: Total drift in moment accumulated over the run, in A m^2.
        units: ``"SI"`` writes tesla and A m^2, ``"cgs"`` writes Oe and emu.
        eq_header: Use the older ``Name = value`` header style.
        third_column: Append a temperature column to each data row.
        descending: Measure from the highest reversal field downwards, as
            MicroMag does.

    Returns:
        The reversal fields written, in measurement order.
    """
    fs = 1.0 if units == "SI" else 1.0e4      # T -> Oe
    ms = 1.0 if units == "SI" else 1.0e3      # A m^2 -> emu
    sep = (lambda k, v: f"{k}           = {v:+.6E}") if eq_header else (lambda k, v: f"{k}\t{v:.6g}")

    lines = ["MicroMag 2900/3900 Data File (Series 0016.002)",
             "Direct moment vs. field; First-order reversal curves", "",
             "INSTRUMENT",
             f"Units of measure{'  :  cgs' if units == 'cgs' else chr(9) + 'SiMuNaughtH'}",
             "", "SCRIPT",
             sep("HCal", h_max * fs), sep("HSat", 1.5 * h_max * fs),
             sep("Hb1", -0.05 * fs), sep("Hb2", 0.05 * fs),
             sep("Hc1", 0.0), sep("Hc2", 0.2 * fs),
             sep("NForc", n_forc), ""]
    if not eq_header:
        cols = ("Field (Oe), Moment (emu)", "    (Oe)         (emu)") if units == "cgs" \
            else ("Field (T), Moment (Am2)", "    (T)          (Am2)")
        lines += [cols[0], cols[1], ""]
    else:
        lines += [sep("NData", 0), ""]

    Has = np.linspace(ha_max, ha_min, n_forc) if descending else np.linspace(ha_min, ha_max, n_forc)
    for k, Ha in enumerate(Has):
        drift = drift_amp * k / max(1, n_forc - 1)
        cal_m = (1.0e-6 + drift) * ms
        tail = ",+2.947547E+02" if third_column else ""
        lines.append(f"{h_max * fs:.9g},{cal_m:.9g}{tail}")
        lines.append("")
        Hb = np.arange(Ha, h_max + 0.5 * step, step)
        M = 1.0e-6 * (0.3 * Hb - 0.4 * Ha + 8.0 * Hb ** 2
                      + 0.7 * Hb * Ha - 4.0 * Ha ** 2) + drift
        for b, m in zip(Hb, M):
            lines.append(f"{b * fs:.9g},{m * ms:.9g}{tail}")
        lines += ["", ""]

    path.write_text("\n".join(lines))
    return Has


@pytest.fixture
def micromag_file(tmp_path):
    """A standard SI MicroMag FORC export."""
    p = tmp_path / "synthetic_specimen.txt"
    write_micromag(p)
    return p


# ------------------------------------------------- LOESS mixed derivative

def test_loess_rho_recovers_quadratic_mixed_derivative():
    """Local quadratic fits recover an exactly known FORC distribution."""
    Ha_vals, Hb_vals, M = quadratic_grid()
    rho = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.01, span_Hb_T=0.01, min_pts=10,
    )

    finite = np.isfinite(rho)
    assert finite.sum() > 200
    # rho = -0.5 * d2M/(dHa dHb), and the mixed coefficient is 0.7.
    assert_allclose(rho[finite], -0.35, rtol=0.0, atol=3e-10)


def test_loess_rho_is_independent_of_chunk_size_with_missing_data():
    """Chunking bounds memory without changing sparse-grid results."""
    Ha_vals, Hb_vals, M = quadratic_grid(size=31)
    M[::4, 2::5] = np.nan
    original = M.copy()

    small_chunks = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.008, span_Hb_T=0.008,
        min_pts=10, chunk_size=7,
    )
    large_chunks = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.008, span_Hb_T=0.008,
        min_pts=10, chunk_size=256,
    )

    # Batched einsum accumulation order varies slightly across NumPy versions.
    assert_allclose(small_chunks, large_chunks, rtol=1e-9, atol=1e-10)
    assert_allclose(M, original)
    assert np.isnan(small_chunks[~np.isfinite(M)]).all()
    assert np.isfinite(small_chunks).sum() > 200


def test_loess_rho_supports_irregular_field_spacing_and_validates_shape():
    """Measured irregular grids work, while malformed inputs fail early."""
    Ha_vals, Hb_vals, M = quadratic_grid(size=9)

    with pytest.raises(ValueError, match="M_grid shape"):
        forc.loess_rho_from_grid_fast(Ha_vals, Hb_vals, M[:-1])

    irregular_Hb = Hb_vals.copy()
    irregular_Hb[4] += 0.0001
    Ha, Hb = np.meshgrid(Ha_vals, irregular_Hb, indexing="ij")
    irregular_M = (
        0.2 + 0.3 * Hb - 0.4 * Ha + 8.0 * Hb ** 2 + 0.7 * Hb * Ha - 4.0 * Ha ** 2
    )
    irregular_M[Hb < Ha] = np.nan
    rho = forc.loess_rho_from_grid_fast(
        Ha_vals, irregular_Hb, irregular_M,
        span_Ha_T=0.02, span_Hb_T=0.02, min_pts=8,
    )
    assert_allclose(rho[np.isfinite(rho)], -0.35, rtol=0.0, atol=3e-10)

    descending_Hb = irregular_Hb.copy()
    descending_Hb[4] = descending_Hb[3] - 0.001
    with pytest.raises(ValueError, match="strictly increasing"):
        forc.loess_rho_from_grid_fast(Ha_vals, descending_Hb, irregular_M)

    with pytest.raises(ValueError, match="chunk_size"):
        forc.loess_rho_from_grid_fast(Ha_vals, Hb_vals, M, chunk_size=0)


def test_loess_rho_matches_analytic_preisach_distribution():
    """A separable Preisach assemblage has a closed-form FORC distribution.

    For hysteron density p(alpha, beta) the up-switched set after reversing at
    Ha and remeasuring to Hb is {beta <= Ha} U {alpha <= Hb}, giving
    rho = Ms * p(alpha = Hb, beta = Ha). Placing the density off the Bu = 0
    axis makes the assignment of the two field labels observable: swapping
    them would mirror the recovered peak in Bc.
    """
    Ms = 1.0e-5
    bc0, bu0 = 0.040, -0.015
    alpha0, beta0 = bu0 + bc0, bu0 - bc0
    sigma = 0.008

    step = 0.001
    Ha_vals = np.arange(-0.12, 0.08 + step / 2, step)
    Hb_vals = np.arange(-0.12, 0.08 + step / 2, step)
    Ha, Hb = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")

    p_up = norm.cdf(Ha, beta0, sigma) + (1 - norm.cdf(Ha, beta0, sigma)) * norm.cdf(Hb, alpha0, sigma)
    M = Ms * (2 * p_up - 1)
    M[Hb < Ha] = np.nan

    rho = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.003, span_Hb_T=0.003, min_pts=10,
    )
    rho_exact = Ms * norm.pdf(Hb, alpha0, sigma) * norm.pdf(Ha, beta0, sigma)
    rho_exact[Hb < Ha] = np.nan

    Bu, Bc = forc.bu_bc_from_ha_hb(Ha_vals, Hb_vals)
    k = np.nanargmax(rho)
    assert Bc.ravel()[k] == pytest.approx(bc0, abs=1.5 * step)
    assert Bu.ravel()[k] == pytest.approx(bu0, abs=1.5 * step)

    ok = np.isfinite(rho) & np.isfinite(rho_exact)
    # LOESS broadens the peak slightly; the shape must still track the analytic
    # surface closely everywhere.
    assert np.max(np.abs(rho[ok] - rho_exact[ok])) < 0.03 * np.nanmax(rho_exact)


# --------------------------------------------------------- field convention

def test_segment_ha_is_the_reversal_field(micromag_file):
    """Ha labels the reversal field and bounds the applied field from below."""
    segs, _ = forc.phase1_prepare_segments_dual(
        str(micromag_file), export_magic=False, verbose=False)
    forcs = [s for s in segs if s.kind == "forc"]
    assert forcs
    for s in forcs:
        assert s.Ha == pytest.approx(float(np.nanmin(s.H)))
        assert np.nanmin(s.H) >= s.Ha - 1e-12


def test_grid_axes_and_rotation_follow_the_literature_convention(micromag_file):
    """Rows are reversal fields, columns applied fields, and Bc is positive."""
    out = forc.run_forc_pipeline(mode="i", path=str(micromag_file),
                                 plot_hyst=False, verbose=False)
    Ha, Hb, rho = out["Ha_vals_used"], out["Hb_vals_used"], out["rho"]
    assert rho.shape == (Ha.size, Hb.size)

    Bu, Bc = forc.bu_bc_from_ha_hb(Ha, Hb)
    finite = np.isfinite(rho)
    assert finite.any()
    # rho is only defined on the physical half-plane Hb >= Ha, i.e. Bc >= 0.
    assert (Bc[finite] >= -1e-12).all()
    assert_allclose(Bc + Bu, np.broadcast_to(Hb[None, :], Bc.shape))
    assert_allclose(Bu - Bc, np.broadcast_to(Ha[:, None], Bc.shape))


def test_bc_and_bu_are_reported_in_the_rotated_literature_coordinates():
    """Bc = (Hb - Ha)/2 and Bu = (Hb + Ha)/2, so a curve's own point has Bc = 0."""
    Ha_vals = np.array([-0.03, -0.02, -0.01])
    Hb_vals = np.array([-0.03, -0.01, 0.01])
    Bu, Bc = forc.bu_bc_from_ha_hb(Ha_vals, Hb_vals)
    assert Bc.shape == (3, 3)
    # Row i, column j corresponds to reversal Ha_vals[i] and applied Hb_vals[j].
    assert Bc[0, 0] == pytest.approx(0.0)
    assert Bu[0, 0] == pytest.approx(-0.03)
    assert Bc[0, 2] == pytest.approx(0.5 * (0.01 - (-0.03)))
    assert Bu[0, 2] == pytest.approx(0.5 * (0.01 + (-0.03)))
    # The upper triangle, where the applied field is below the reversal field,
    # is unphysical and carries negative Bc.
    assert Bc[2, 0] < 0


# ------------------------------------------------------- drift correction

def test_drift_is_recovered_from_the_calibration_points(tmp_path):
    """Injected calibration drift is measured and removed."""
    p = tmp_path / "drifting.txt"
    drift_amp = 4.0e-7
    write_micromag(p, n_forc=30, drift_amp=drift_amp)

    tags, _ = forc.read_header_tags_and_data_start(str(p))
    HCal = float(tags["HCal"])
    segs = forc.read_segments_raw(str(p), HCal=HCal, verbose=False)
    segs = forc.split_cal_first_point(segs, HCal=HCal)

    drift_at_seg, cal_pos, cal_M = forc.compute_drift_from_cals(segs, fit="linear")
    assert cal_M.size == 30
    # The calibration moment climbs linearly by drift_amp across the run.
    assert cal_M[-1] - cal_M[0] == pytest.approx(drift_amp, rel=1e-9)
    assert_allclose(np.diff(cal_M), drift_amp / 29, rtol=1e-6)

    corrected = forc.apply_drift_correction(segs, drift_at_seg)
    cal_after = np.array([s.M[0] for s in corrected if s.kind == "cal"])
    assert_allclose(cal_after, cal_after[0], atol=1e-18)


def test_drift_correction_needs_at_least_two_calibration_points():
    """A single calibration point cannot define a drift trend."""
    one = [forc.Segment(H=np.array([1.0]), M=np.array([1e-6]), idx=0, kind="cal")]
    with pytest.raises(ValueError, match="calibration"):
        forc.compute_drift_from_cals(one)


# ------------------------------------------------- reference-curve subtraction

def test_reference_curve_is_the_lowest_reversal_field_curve(micromag_file):
    """The default reference spans the widest field range, not the first measured."""
    segs, _ = forc.phase1_prepare_segments_dual(
        str(micromag_file), export_magic=False, verbose=False)
    forcs = [s for s in segs if s.kind == "forc"]

    # MicroMag measures from the highest reversal field downwards, so the
    # first-measured curve is the shortest one near saturation.
    assert forcs[0].Ha > forcs[-1].Ha
    chosen = forc.select_reference_curve(forcs)
    assert chosen.Ha == pytest.approx(min(s.Ha for s in forcs))
    assert chosen.H.size == max(s.H.size for s in forcs)

    with pytest.raises(ValueError, match="reference must be"):
        forc.select_reference_curve(forcs, reference="nonsense")


def test_reference_subtraction_leaves_rho_unchanged(micromag_file):
    """A baseline that depends only on the applied field cancels in the mixed derivative."""
    common = dict(mode="i", path=str(micromag_file), plot_hyst=False, verbose=False)
    plain = forc.run_forc_pipeline(**common)
    subtracted = forc.run_forc_pipeline(do_reference_subtract=True, **common)

    assert_allclose(plain["Ha_vals_used"], subtracted["Ha_vals_used"])
    assert_allclose(plain["Hb_vals_used"], subtracted["Hb_vals_used"])
    both = np.isfinite(plain["rho"]) & np.isfinite(subtracted["rho"])
    assert both.sum() > 100
    peak = np.nanmax(np.abs(plain["rho"]))

    # Away from the boundary the cancellation is exact: a baseline that is a
    # function of the applied field alone has no mixed derivative. Within a
    # smoothing window of the edge the local fit is one-sided and the
    # interpolated baseline is only piecewise linear, so cells there do shift.
    from scipy.ndimage import binary_erosion
    radius = int(np.ceil(plain["loess_params"]["ry"])) + 1
    interior = binary_erosion(both, structure=np.ones((3, 3)), iterations=radius)
    assert interior.sum() > 50
    # Parts per million of the peak; the residual is double-precision
    # cancellation between two different arithmetic paths, not physics.
    assert np.max(np.abs(plain["rho"][interior] - subtracted["rho"][interior])) < 1e-6 * peak

    # Both paths must also recover the analytic value. The fixture surface has
    # a mixed coefficient of 0.7e-6, so rho = -0.5 * 0.7e-6 = -3.5e-7.
    for label, result in (("plain", plain), ("subtracted", subtracted)):
        assert_allclose(result["rho"][interior], -3.5e-7, rtol=1e-4,
                        err_msg=f"{label} run does not recover the analytic rho")


# ------------------------------------------------------------ file reading

def test_reads_cgs_files_and_converts_to_si(tmp_path):
    """A cgs export gives the same physics as the identical SI export."""
    si = tmp_path / "si.txt"
    cgs = tmp_path / "cgs.txt"
    write_micromag(si, units="SI")
    write_micromag(cgs, units="cgs")

    assert forc.read_file_units(str(cgs))["field_unit"] == "Oe"
    assert forc.read_file_units(str(si))["field_unit"] == "T"

    tags_si, _ = forc.read_header_tags_and_data_start(str(si))
    tags_cgs, _ = forc.read_header_tags_and_data_start(str(cgs))
    assert tags_cgs["HCal"] == pytest.approx(tags_si["HCal"], rel=1e-9)

    out_si = forc.run_forc_pipeline(mode="i", path=str(si), plot_hyst=False, verbose=False)
    out_cgs = forc.run_forc_pipeline(mode="i", path=str(cgs), plot_hyst=False, verbose=False)
    assert_allclose(out_cgs["Ha_vals_used"], out_si["Ha_vals_used"], rtol=1e-9, atol=1e-12)
    both = np.isfinite(out_si["rho"]) & np.isfinite(out_cgs["rho"])
    assert both.sum() > 100
    assert_allclose(out_cgs["rho"][both], out_si["rho"][both], rtol=1e-6)


def test_reads_equals_style_headers_and_three_column_data(tmp_path):
    """Older Series 0015 exports use 'Name = value' and may carry a temperature column."""
    p = tmp_path / "old_style.txt"
    write_micromag(p, units="cgs", eq_header=True, third_column=True)

    tags, data_start = forc.read_header_tags_and_data_start(str(p))
    assert tags["HCal"] == pytest.approx(0.25, rel=1e-6)
    assert data_start > 0

    segs, _ = forc.phase1_prepare_segments_dual(str(p), export_magic=False, verbose=False)
    forcs = [s for s in segs if s.kind == "forc"]
    assert len(forcs) == 40
    assert np.isfinite(forcs[-1].H).all()


def test_mislabelled_cgs_file_is_rejected_rather_than_silently_rescaled(tmp_path):
    """Oersted values read as tesla would be off by 10^4; that must not pass."""
    p = tmp_path / "unlabelled_cgs.txt"
    write_micromag(p, units="cgs")
    # Strip the units declaration so the reader would otherwise assume SI.
    text = "\n".join(l for l in p.read_text().split("\n") if "Units of measure" not in l)
    p.write_text(text)

    assert forc.read_file_units(str(p))["source"] == "assumed SI"
    with pytest.raises(ValueError, match="not a plausible laboratory field"):
        forc.read_segments_raw(str(p), verbose=False)


def test_header_limits_are_read_as_bias_and_coercivity_bounds(micromag_file):
    """MicroMag Hb2/Hc2 are diagram display limits, not reversal/applied fields."""
    Bu_max, Bc_max = forc.read_forc_header_limits(str(micromag_file))
    assert Bu_max == pytest.approx(0.05)
    assert Bc_max == pytest.approx(0.2)


# ---------------------------------------------------------- MagIC round trip

def test_magic_export_is_a_readable_measurements_table(micromag_file, tmp_path):
    """The export carries the MagIC preamble and a calibrated moment column."""
    written = forc.export_magic_measurements_from_raw(str(micromag_file))
    assert written.parent.name == "MagIC"

    lines = written.read_text().split("\n")
    assert lines[0].split("\t") == ["tab delimited", "measurements"]
    headers = lines[1].split("\t")
    assert "magn_moment" in headers and "meas_field_dc" in headers

    row = dict(zip(headers, lines[2].split("\t")))
    assert row["method_codes"] == "LP-FORC"
    assert float(row["magn_moment"]) != 0.0
    assert row["magn_uncal"] == ""
    # ISO-8601, not the locale-dependent US ordering.
    assert row["timestamp"][4] == "-" and row["timestamp"][7] == "-"


def test_magic_round_trip_reproduces_the_distribution(micromag_file):
    """Raw -> MagIC -> processed gives the same FORC distribution."""
    direct = forc.run_forc_pipeline(mode="i", path=str(micromag_file),
                                    plot_hyst=False, verbose=False)
    magic_path = forc.export_magic_measurements_from_raw(str(micromag_file))
    viamagic = forc.run_forc_pipeline(mode="m", path=str(magic_path),
                                      plot_hyst=False, verbose=False)
    if isinstance(viamagic, list):
        viamagic = viamagic[0]

    assert_allclose(viamagic["Ha_vals_used"], direct["Ha_vals_used"], rtol=1e-9, atol=1e-12)
    assert_allclose(viamagic["Hb_vals_used"], direct["Hb_vals_used"], rtol=1e-9, atol=1e-12)
    both = np.isfinite(direct["rho"]) & np.isfinite(viamagic["rho"])
    assert both.sum() > 100
    assert_allclose(viamagic["rho"][both], direct["rho"][both], rtol=1e-6, atol=1e-12)


# ----------------------------------------------------------------- profiles

def test_profile_binning_follows_the_requested_window(micromag_file):
    """Bins are sized from the requested axis, not a fixed count over all data."""
    out = forc.run_forc_pipeline(mode="i", path=str(micromag_file),
                                 plot_hyst=False, verbose=False)
    Ha, Hb, rho = out["Ha_vals_used"], out["Hb_vals_used"], out["rho"]

    _, step = forc.estimate_steps(Ha, Hb)
    narrow = forc.slice_profile_smoothed(Ha, Hb, rho, mode="Bu", target=0.0,
                                         x_min=0.0, x_max=0.05)
    wide = forc.slice_profile_smoothed(Ha, Hb, rho, mode="Bu", target=0.0,
                                       x_min=0.0, x_max=0.20)
    # Both are binned at the grid step, so the narrow window simply gets fewer
    # bins rather than finer ones. Rounding to a whole bin count means the two
    # widths agree only to within one bin over the shorter axis.
    assert narrow["bin_width"] == pytest.approx(step, rel=0.15)
    assert wide["bin_width"] == pytest.approx(step, rel=0.15)
    assert narrow["n_bins"] < wide["n_bins"]
    assert narrow["x"][0] >= 0.0 and narrow["x"][-1] <= 0.05

    explicit = forc.slice_profile_smoothed(Ha, Hb, rho, mode="Bu", target=0.0,
                                           x_min=0.0, x_max=0.05, bin_width=0.001)
    assert explicit["n_bins"] == 50

    with pytest.raises(ValueError, match="Profile axis is empty"):
        forc.slice_profile_smoothed(Ha, Hb, rho, mode="Bu", target=0.0,
                                    x_min=0.05, x_max=0.05)


def test_profile_peak_and_fwhm_on_a_gaussian():
    """FWHM of a Gaussian is 2*sqrt(2*ln2)*sigma, recovered by interpolation."""
    x = np.linspace(-1.0, 1.0, 2001)
    sigma = 0.1
    y = np.exp(-0.5 * (x - 0.2) ** 2 / sigma ** 2)
    pk = forc.profile_peak_and_fwhm(x, y)
    assert pk["peak_x"] == pytest.approx(0.2, abs=1e-3)
    assert pk["peak_y"] == pytest.approx(1.0, rel=1e-6)
    assert pk["fwhm"] == pytest.approx(2 * np.sqrt(2 * np.log(2)) * sigma, rel=1e-3)
    assert pk["left_x"] < pk["peak_x"] < pk["right_x"]

    assert np.isnan(forc.profile_peak_and_fwhm([0.0, 1.0], [1.0, 2.0])["fwhm"])


def test_ridge_profile_follows_a_sloping_crest():
    """A crest that drifts in Bu with coercivity is tracked, not cut across."""
    step = 0.002
    Ha_vals = np.arange(-0.30, 0.10 + step / 2, step)
    Hb_vals = np.arange(-0.30, 0.10 + step / 2, step)
    Ha, Hb = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    Bc = 0.5 * (Hb - Ha)
    Bu = 0.5 * (Hb + Ha)

    # Ridge centred on Bu = -0.25 * Bc, so the crest slopes downwards.
    slope = -0.25
    rho = np.exp(-0.5 * ((Bu - slope * Bc) / 0.010) ** 2) * np.exp(-0.5 * ((Bc - 0.05) / 0.030) ** 2)
    rho[Hb < Ha] = np.nan

    ridge = forc.ridge_profile(Ha_vals, Hb_vals, rho, Bu_min=-0.10, Bu_max=0.05,
                               Bc_min=0.005, Bc_max=0.15, smooth_sigma_bins=1.0)
    ok = np.isfinite(ridge["bc"]) & np.isfinite(ridge["bu"])
    assert ok.sum() > 20
    # The tracked crest must sit on the analytic ridge line.
    assert np.max(np.abs(ridge["bu"][ok] - slope * ridge["bc"][ok])) < 3 * step
    assert ridge["peak"]["peak_x"] == pytest.approx(0.05, abs=0.01)
    assert np.all(np.diff(ridge["arc_length"]) >= -1e-15)

    # The fixed-Bu cut through the peak crosses the ridge and is narrower.
    fixed = forc.slice_profile_smoothed(Ha_vals, Hb_vals, rho, mode="Bu",
                                        target=slope * 0.05, x_min=0.005, x_max=0.15,
                                        smooth_sigma_bins=1.0)
    assert ridge["peak"]["fwhm"] > fixed["peak"]["fwhm"]


def test_ridge_tracking_resolves_open_bounds():
    """Omitted Bu/Bc bounds fall back to the finite data range rather than failing."""
    step = 0.002
    # The applied-field axis must reach well above the reversal-field axis, or
    # the physical triangle pinches out the Bu = 0 line at modest coercivity.
    Ha_vals = np.arange(-0.20, 0.02 + step / 2, step)
    Hb_vals = np.arange(-0.20, 0.20 + step / 2, step)
    Ha, Hb = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    Bc, Bu = 0.5 * (Hb - Ha), 0.5 * (Hb + Ha)
    rho = np.exp(-0.5 * (Bu / 0.012) ** 2) * np.exp(-0.5 * ((Bc - 0.04) / 0.020) ** 2)
    rho[Hb < Ha] = np.nan

    track = forc.track_bu_offset_vs_bc(Ha_vals, Hb_vals, rho)
    assert track["bc"].size > 0
    assert track["ranges"]["Bc_min"] == 0.0
    assert np.isfinite(track["ranges"]["Bc_max"])
    assert track["bc"].shape == track["bu"].shape == track["rho"].shape

    # Open bounds span the whole measured range, and at high Bc the physical
    # triangle admits only a narrow band of Bu, so the crest is pushed off
    # axis there whatever the distribution looks like. Over the coercivity
    # range the ridge actually occupies, it sits on Bu = 0 as a symmetric
    # ridge must.
    core = track["bc"] < 0.08
    assert core.sum() > 10
    assert np.max(np.abs(track["bu"][core])) < 3 * step


def test_ridge_tracking_handles_a_wholly_negative_distribution():
    """With no positive signal there is no ridge, and the tracker must not crash."""
    Ha_vals, Hb_vals, M = quadratic_grid(size=21)
    rho = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.01, span_Hb_T=0.01, min_pts=10)
    assert np.nanmax(rho) < 0

    track = forc.track_bu_offset_vs_bc(Ha_vals, Hb_vals, rho)
    assert track["bc"].size > 0
    assert np.isfinite(track["rho"]).all()


# ---------------------------------------------------------- smoothing guess

def test_loess_guess_measures_fill_over_the_physical_half_plane():
    """The structurally empty half of the array must not count as missing data."""
    Ha_vals, Hb_vals, M = quadratic_grid(size=41)
    guess = forc.guess_loess_params(Ha_vals, Hb_vals, M)
    # Every physical cell is populated in this synthetic surface.
    assert guess["fill_fraction"] == pytest.approx(1.0, abs=1e-9)
    assert guess["span_Ha_T"] > 0 and guess["span_Hb_T"] > 0
    assert guess["min_pts_suggested"] >= 6


def test_gaussian_smoothing_preserves_nan_gaps_and_area():
    """Smoothing spans gaps without inventing values where there are none."""
    y = np.ones(101)
    y[40:45] = np.nan
    smoothed = forc.gaussian_smooth_1d_nan(y, sigma_bins=3.0)
    assert np.isfinite(smoothed).all()
    assert_allclose(smoothed, 1.0, rtol=1e-9)

    assert_allclose(forc.gaussian_smooth_1d_nan(y, sigma_bins=0), y)
    assert_allclose(forc.gaussian_smooth_1d_nan(y, sigma_bins=None), y)
