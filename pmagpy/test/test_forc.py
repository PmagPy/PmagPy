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
    out = forc.process_forc(mode="i", path=str(micromag_file),
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
    plain = forc.process_forc(**common)
    subtracted = forc.process_forc(do_reference_subtract=True, **common)

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

    out_si = forc.process_forc(mode="i", path=str(si), plot_hyst=False, verbose=False)
    out_cgs = forc.process_forc(mode="i", path=str(cgs), plot_hyst=False, verbose=False)
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
    direct = forc.process_forc(mode="i", path=str(micromag_file),
                                    plot_hyst=False, verbose=False)
    magic_path = forc.export_magic_measurements_from_raw(str(micromag_file))
    viamagic = forc.process_forc(mode="m", path=str(magic_path),
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
    out = forc.process_forc(mode="i", path=str(micromag_file),
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


# ==========================================================================
# VARIFORC variable smoothing
# ==========================================================================
#
# These tests check the implementation on three independent levels: from first
# principles (an analytic surface whose distribution is known exactly), against
# the documented algorithm (Egli's published resolution law, which the
# implementation must reproduce without having been fitted to it), and through
# invariances that must hold whatever the internal batching does.


def ideal_ridge_grid(dH=0.001, ha_lo=-0.20, hi=0.20):
    """A synthetic unit central ridge, following Egli (2013) Eq. 7.

    ``M = -4|Bu|`` is not a physical magnetization curve, but it yields the
    unit ridge ``rho = delta(Bu)`` exactly, so the width of a processed
    vertical profile measures the resolution of the estimator directly.
    """
    Ha = np.arange(ha_lo, 0.05 + dH / 2, dH)
    Hb = np.arange(ha_lo, hi + dH / 2, dH)
    A, B = np.meshgrid(Ha, Hb, indexing="ij")
    Bu = 0.5 * (B + A)
    M = -4.0 * np.abs(Bu)
    M[B < A] = np.nan
    return Ha, Hb, M


def ridge_and_background_grid(dH=0.001, Ms=1.0e-5, noise=0.0, seed=0):
    """A narrow central ridge on a broad background, with a known rho.

    The hysteron density is specified directly in ``(Bc, Bu)`` as the sum of a
    ridge that is narrow in ``Bu`` and a broad background. A horizontal ridge
    requires ``alpha`` and ``beta`` to be correlated, so the up-switched
    fraction has no closed form and is obtained by cumulative integration:

        P_up(Ha, Hb) = C(inf, Ha) + C(Hb, inf) - C(Hb, Ha)

    with ``C`` the two-dimensional cumulative integral of the density. The
    distribution is then ``rho = Ms p(alpha = Hb, beta = Ha)`` exactly.
    """
    fine = dH / 2.0
    axis = np.arange(-0.14, 0.10 + fine / 2, fine)
    A, Bt = np.meshgrid(axis, axis, indexing="ij")       # alpha, beta
    Bc = 0.5 * (A - Bt)
    Bu = 0.5 * (A + Bt)

    def component(bc0, bc_sd, bu_sd, amp):
        return (amp * np.exp(-0.5 * ((Bc - bc0) / bc_sd) ** 2)
                * np.exp(-0.5 * (Bu / bu_sd) ** 2)
                / (2 * np.pi * bc_sd * bu_sd))

    p = component(0.025, 0.012, 0.0010, 1.0) + component(0.020, 0.025, 0.025, 1.2)
    p[A < Bt] = 0.0
    p /= np.trapezoid(np.trapezoid(p, axis, axis=1), axis)
    C = np.cumsum(np.cumsum(p, axis=0), axis=1) * fine * fine

    Ha = np.arange(-0.10, 0.05 + dH / 2, dH)
    Hb = np.arange(-0.10, 0.08 + dH / 2, dH)
    ia = np.searchsorted(axis, Ha)
    ib = np.searchsorted(axis, Hb)
    P_up = (C[-1, :][ia][:, None] + C[:, -1][ib][None, :] - C[np.ix_(ib, ia)].T)
    M = Ms * (2.0 * P_up - 1.0)
    rho_true = Ms * p[np.ix_(ib, ia)].T

    AA, BB = np.meshgrid(Ha, Hb, indexing="ij")
    mask = BB < AA
    M[mask] = np.nan
    rho_true[mask] = np.nan
    if noise:
        M = M + noise * np.random.default_rng(seed).standard_normal(M.shape)
        M[mask] = np.nan
    return Ha, Hb, M, rho_true, 0.5 * (BB - AA), 0.5 * (BB + AA)


def preisach_grid(step=0.001, Ms=1.0e-5, bc0=0.030, sigma=0.008,
                  noise=0.0, seed=0):
    """A separable Preisach assemblage with a closed-form FORC distribution."""
    Ha = np.arange(-0.12, 0.08 + step / 2, step)
    Hb = np.arange(-0.12, 0.08 + step / 2, step)
    A, B = np.meshgrid(Ha, Hb, indexing="ij")
    alpha0, beta0 = bc0, -bc0
    p_up = (norm.cdf(A, beta0, sigma)
            + (1 - norm.cdf(A, beta0, sigma)) * norm.cdf(B, alpha0, sigma))
    M = Ms * (2 * p_up - 1)
    rho_true = Ms * norm.pdf(B, alpha0, sigma) * norm.pdf(A, beta0, sigma)
    mask = B < A
    M[mask] = np.nan
    rho_true[mask] = np.nan
    if noise:
        M = M + noise * np.random.default_rng(seed).standard_normal(M.shape)
        M[mask] = np.nan
    return Ha, Hb, M, rho_true


# ------------------------------------------------------- the weight function

def test_variforc_weight_has_the_documented_shape():
    """Egli Eq. 6: unit core, compact support, and a smooth join between."""
    u = np.linspace(-9, 9, 4001)
    for s in (2.0, 3.5, 7.0):
        w = forc.variforc_weight_1d(u, s)
        assert_allclose(w[np.abs(u) <= s - 1.0], 1.0)
        assert np.all(w[np.abs(u) > s] == 0.0)
        assert np.all((w >= 0.0) & (w <= 1.0))
        # The two quadratic pieces meet at |u| = s - 1/2, both giving 1/2.
        assert forc.variforc_weight_1d(np.array([s - 0.5]), s)[0] == pytest.approx(0.5)
        # Continuous in value and in first derivative: no step in either.
        assert np.max(np.abs(np.diff(w))) < 0.02
        assert np.max(np.abs(np.diff(w, n=2))) < 0.01


def test_variforc_weight_broadcasts_per_node_factors():
    """Each node must be able to carry its own smoothing factor."""
    u = np.linspace(-5, 5, 11)[np.newaxis, :]
    s = np.array([[2.0], [4.0]])
    w = forc.variforc_weight_1d(u, s)
    assert w.shape == (2, 11)
    assert_allclose(w[0], forc.variforc_weight_1d(u[0], 2.0))
    assert_allclose(w[1], forc.variforc_weight_1d(u[0], 4.0))


# --------------------------------------------------- the smoothing factors

def test_smoothing_factors_reduce_to_conventional_processing():
    """Zero growth rate and equal floors give one constant factor everywhere."""
    Bc = np.linspace(0, 0.1, 40)[None, :] * np.ones((40, 1))
    Bu = np.linspace(-0.05, 0.05, 40)[:, None] * np.ones((1, 40))
    s_c, s_b = forc.variforc_smoothing_factors(
        Bc, Bu, dH=0.001, sc0=5, sc1=5, sb0=5, sb1=5, lambda_c=0.0, lambda_b=0.0)
    # Away from the axes the cap max(s0, |H|/dH) exceeds s1, so s == s1.
    interior = (Bc > 0.01) & (np.abs(Bu) > 0.01)
    assert_allclose(s_c[interior], 5.0)
    assert_allclose(s_b[interior], 5.0)


def test_smoothing_factors_grow_away_from_the_origin():
    """Egli Eq. 11-12: the factor increases linearly with distance."""
    dH = 0.001
    Bc = np.array([[0.0, 0.02, 0.05, 0.10]])
    Bu = np.zeros_like(Bc)
    s_c, _ = forc.variforc_smoothing_factors(
        Bc, Bu, dH=dH, sc0=3, sc1=7, sb0=3, sb1=7, lambda_c=0.1, lambda_b=0.1)
    expected = np.minimum(0.9 * 7 + 0.1 * Bc / dH, np.maximum(3.0, Bc / dH))
    assert_allclose(s_c, np.maximum(expected, 1.0))
    assert s_c[0, -1] > s_c[0, 1], "factor must grow with coercivity"


def test_central_ridge_floor_holds_resolution_across_the_ridge():
    """Egli Eq. 14: the vertical factor is pinned to its floor on the ridge."""
    dH = 0.001
    Bu = np.array([[0.0, 0.001, 0.005, 0.05]])
    Bc = np.full_like(Bu, 0.05)
    _, s_b = forc.variforc_smoothing_factors(
        Bc, Bu, dH=dH, sc0=9, sc1=9, sb0=3, sb1=9, lambda_c=0.1, lambda_b=0.1)
    assert s_b[0, 0] == pytest.approx(3.0), "on the ridge, held at the floor"
    assert s_b[0, 1] == pytest.approx(3.0)
    assert s_b[0, 2] > 3.0, "the cap relaxes away from the ridge"
    assert s_b[0, 3] > s_b[0, 2]


def test_ridge_and_diagonal_limits_cap_the_factor_where_asked():
    """Limits away from the axes and along the diagonals both bite."""
    dH = 0.001
    Bc = np.linspace(0.0, 0.10, 101)[None, :] * np.ones((101, 1))
    Bu = np.linspace(-0.05, 0.05, 101)[:, None] * np.ones((1, 101))

    base = forc.variforc_smoothing_factors(Bc, Bu, dH=dH, sc0=9, sc1=9, sb0=9,
                                           sb1=9, lambda_c=0.1, lambda_b=0.1)
    ridged = forc.variforc_smoothing_factors(
        Bc, Bu, dH=dH, sc0=9, sc1=9, sb0=9, sb1=9, lambda_c=0.1, lambda_b=0.1,
        ridge_limits=[("Bu", 0.02, 2.0, dH)])
    on_ridge = np.abs(Bu - 0.02) < 0.0005
    assert np.all(ridged[1][on_ridge] <= 2.0 + 1e-9)
    assert np.all(base[1][on_ridge] > 2.0)
    off = np.abs(Bu - 0.02) > 0.02
    assert_allclose(ridged[1][off], base[1][off])

    with pytest.raises(ValueError, match="ridge_limits axis"):
        forc.variforc_smoothing_factors(Bc, Bu, dH=dH,
                                        ridge_limits=[("nope", 0.0, 2.0, dH)])


def test_diagonal_limits_truncate_the_window_without_shrinking_it():
    """Egli truncates the rectangle's corners rather than shrinking it.

    The distinction matters. Shrinking the whole window over a narrow band
    around a diagonal introduces a step in resolution that shows up as a
    streak in the diagram; clipping the corners leaves resolution along the
    Bc and Bu axes untouched and only removes the diagonal reach.
    """
    dH = 0.001
    Bc = np.linspace(0.0, 0.10, 101)[None, :] * np.ones((101, 1))
    Bu = np.linspace(-0.05, 0.05, 101)[:, None] * np.ones((1, 101))

    limits = [("Hr", -0.02, 2.0, 0.02)]
    truncation = forc.diagonal_truncation_factors(Bc, Bu, dH, limits)
    assert set(truncation) == {"Hr"}

    on_diagonal = np.abs((Bu - Bc) - (-0.02)) < 0.0005
    assert np.all(truncation["Hr"][on_diagonal] == pytest.approx(2.0))
    far = np.abs((Bu - Bc) - (-0.02)) > 0.04
    assert np.all(truncation["Hr"][far] > 2.0), "the limit must relax with distance"

    # The along-axis smoothing factors are untouched by a diagonal limit.
    plain = forc.variforc_smoothing_factors(Bc, Bu, dH=dH, sc0=9, sc1=9,
                                            sb0=9, sb1=9, lambda_c=0.1,
                                            lambda_b=0.1)
    assert plain[0].shape == Bc.shape

    assert forc.diagonal_truncation_factors(Bc, Bu, dH, None) == {}
    with pytest.raises(ValueError, match="diagonal_limits axis"):
        forc.diagonal_truncation_factors(Bc, Bu, dH, [("nope", 0.0, 2.0, dH)])


def test_diagonal_truncation_reduces_the_window_reach(micromag_file):
    """A diagonal limit must actually change the distribution it constrains."""
    out = forc.process_forc(mode="i", path=str(micromag_file),
                                 plot_hyst=False, plot_rho=False, verbose=False)
    Ha, Hb, M = out["Ha_vals_used"], out["Hb_vals_used"], out["M_grid_used"]
    common = dict(sc0=6, sc1=6, sb0=6, sb1=6, lambda_c=0.0, lambda_b=0.0,
                  min_pts=8)

    free = forc.variforc_rho_from_grid(Ha, Hb, M, **common)
    clipped = forc.variforc_rho_from_grid(
        Ha, Hb, M, diagonal_limits=[("Hr", -0.02, 1.5, 0.01)], **common)
    both = np.isfinite(free) & np.isfinite(clipped)
    assert both.sum() > 100
    assert np.max(np.abs(free[both] - clipped[both])) > 0

    hcoerc = forc.find_coercive_field(Ha, Hb, M)
    assert np.isfinite(hcoerc) and hcoerc >= 0


# ------------------------------------------------------- from first principles

def test_variforc_recovers_an_analytic_quadratic_exactly():
    """The rotated second-derivative difference must equal the mixed derivative.

    For a quadratic surface both estimators are exact, so agreement between
    two structurally different formulations -- rho as a mixed derivative in
    (Ha, Hb) and as (1/8)(d2M/dBc2 - d2M/dBu2) in the rotated frame -- checks
    the rotation, the weighting and the coefficient extraction together.
    """
    Ha_vals, Hb_vals, M = quadratic_grid(size=41)
    rho_vari = forc.variforc_rho_from_grid(
        Ha_vals, Hb_vals, M, sc0=4, sc1=4, sb0=4, sb1=4,
        lambda_c=0.0, lambda_b=0.0, min_pts=10)
    rho_loess = forc.loess_rho_from_grid_fast(
        Ha_vals, Hb_vals, M, span_Ha_T=0.006, span_Hb_T=0.006, min_pts=10)

    ok = np.isfinite(rho_vari)
    assert ok.sum() > 400
    assert_allclose(rho_vari[ok], -0.35, atol=1e-8)
    both = ok & np.isfinite(rho_loess)
    assert_allclose(rho_vari[both], rho_loess[both], atol=1e-8)


def test_variforc_recovers_the_preisach_peak():
    """A known Preisach assemblage must be found at its known coordinates."""
    Ha, Hb, M, rho_true = preisach_grid()
    rho = forc.variforc_rho_from_grid(Ha, Hb, M, sc0=3, sc1=3, sb0=3, sb1=3,
                                      lambda_c=0.0, lambda_b=0.0, min_pts=10)
    Bu, Bc = forc.bu_bc_from_ha_hb(Ha, Hb)
    k = np.nanargmax(rho)
    assert Bc.ravel()[k] == pytest.approx(0.030, abs=0.002)
    assert Bu.ravel()[k] == pytest.approx(0.0, abs=0.002)

    # Compare where the regression window is two-sided. A rectangle upright in
    # (Bc, Bu) is a diamond in measurement coordinates, so it meets the
    # Bc = 0 diagonal and the edges of measured space sooner than an
    # axis-aligned window does, and the fit there is necessarily one-sided.
    margin = 4 * 0.001 * np.sqrt(2)
    interior = (np.isfinite(rho) & np.isfinite(rho_true)
                & (Bc > margin)
                & (Ha[:, None] > Ha.min() + margin)
                & (Hb[None, :] < Hb.max() - margin))
    assert interior.sum() > 500
    assert np.max(np.abs(rho[interior] - rho_true[interior])) < 0.05 * np.nanmax(rho_true)


# -------------------------------------------------- against the documented law

def test_variforc_reproduces_the_egli_resolution_law():
    """Egli (2013) Eq. 9: FWHM of a processed unit ridge = (1.076 s_b - 0.468) dH.

    This is a published, quantitative prediction of the algorithm that the
    implementation was not fitted to, so reproducing it checks fidelity to the
    original rather than internal self-consistency.
    """
    dH = 0.001
    Ha, Hb, M = ideal_ridge_grid(dH=dH)
    Bu, Bc = forc.bu_bc_from_ha_hb(Ha, Hb)

    measured, predicted = [], []
    for sb in (2.0, 3.0, 5.0, 8.0):
        rho = forc.variforc_rho_from_grid(
            Ha, Hb, M, sc0=6, sc1=6, sb0=sb, sb1=sb,
            lambda_c=0.0, lambda_b=0.0, dH=dH, min_pts=8)
        band = (Bc > 0.04) & (Bc < 0.06) & (np.abs(Bu) < 0.03) & np.isfinite(rho)
        centres, profile = forc.bin_profile(Bu[band], rho[band], -0.03, 0.03,
                                            n_bins=240)
        peak = forc.profile_peak_and_fwhm(centres, profile, use_abs=False)
        measured.append(peak["fwhm"] / dH)
        predicted.append(1.076 * sb - 0.468)

    measured = np.array(measured)
    predicted = np.array(predicted)
    assert np.all(np.abs(measured - predicted) / predicted < 0.03)

    slope, intercept = np.polyfit([2.0, 3.0, 5.0, 8.0], measured, 1)
    assert slope == pytest.approx(1.076, abs=0.03)
    assert intercept == pytest.approx(-0.468, abs=0.10)


# ----------------------------------------------------------------- invariances

def test_variforc_result_is_independent_of_the_internal_grouping():
    """Batching must not change the answer.

    Nodes are grouped only to choose a shared candidate offset list; each node
    is then weighted by its own exact smoothing factors. The result must
    therefore be independent of the grouping, which is what distinguishes this
    from quantizing the smoothing factors themselves.
    """
    Ha, Hb, M, _ = preisach_grid(noise=1e-9, seed=3)
    kw = dict(sc0=3, sc1=7, sb0=3, sb1=7, lambda_c=0.1, lambda_b=0.1, min_pts=10)
    coarse = forc.variforc_rho_from_grid(Ha, Hb, M, group_ratio=2.0, **kw)
    fine = forc.variforc_rho_from_grid(Ha, Hb, M, group_ratio=1.05, **kw)
    ok = np.isfinite(coarse) & np.isfinite(fine)
    assert ok.sum() > 500
    assert np.max(np.abs(coarse[ok] - fine[ok])) < 1e-6 * np.nanmax(np.abs(fine))


def test_variforc_at_zero_growth_matches_a_constant_window():
    """With no growth and no ridge floors, every node uses the same window."""
    Ha, Hb, M, _ = preisach_grid()
    result = forc.variforc_rho_from_grid(
        Ha, Hb, M, sc0=5, sc1=5, sb0=5, sb1=5, lambda_c=0.0, lambda_b=0.0,
        min_pts=10, return_factors=True)
    interior = (forc.bu_bc_from_ha_hb(Ha, Hb)[1] > 0.02)
    assert_allclose(result["s_c"][interior], 5.0)
    assert_allclose(result["s_b"][interior & (np.abs(
        forc.bu_bc_from_ha_hb(Ha, Hb)[0]) > 0.006)], 5.0)


# ------------------------------------------------- what the method is good for

def test_variable_smoothing_beats_every_constant_window_on_a_ridge():
    """The point of the method: ridge resolution and background suppression at once.

    A narrow ridge on a broad background is the case a single window cannot
    serve. Variable smoothing must resolve the ridge about as well as the small
    window that suits it, while suppressing background noise about as well as
    the large window that suits that.
    """
    Ha, Hb, M, rho_true, Bc, Bu = ridge_and_background_grid(noise=2.0e-8, seed=5)

    peak = np.nanmax(rho_true)
    ridge_region = (np.abs(Bu) < 0.002) & (Bc > 0.012) & (Bc < 0.04)
    background = (np.abs(Bu) > 0.035) & (Bc > 0.03)

    def errors(r):
        rr = np.sqrt(np.nanmean((r[ridge_region] - rho_true[ridge_region]) ** 2)) / peak
        bb = np.nanstd(r[background]) / peak
        return rr, bb

    constants = {}
    for s in (2, 4, 8, 12):
        r = forc.variforc_rho_from_grid(Ha, Hb, M, sc0=s, sc1=s, sb0=s, sb1=s,
                                        lambda_c=0.0, lambda_b=0.0, min_pts=8)
        constants[s] = errors(r)

    variable = errors(forc.variforc_rho_from_grid(
        Ha, Hb, M, sc0=3, sc1=10, sb0=2, sb1=10,
        lambda_c=0.1, lambda_b=0.1, min_pts=8))

    # No single constant window serves both criteria: the one that resolves
    # the ridge best leaves the worst background, and vice versa.
    sharpest = min(constants, key=lambda s: constants[s][0])
    smoothest = min(constants, key=lambda s: constants[s][1])
    assert sharpest < smoothest, "expected a small window to win on the ridge"
    assert constants[sharpest][1] > constants[smoothest][1]
    assert constants[smoothest][0] > constants[sharpest][0]

    # Variable smoothing must beat each of them on the criterion it loses on,
    # which is the property that motivates the method.
    assert variable[1] < constants[sharpest][1], (
        f"background {variable[1]:.3%} vs {constants[sharpest][1]:.3%} for the "
        f"ridge-resolving window s={sharpest}")
    assert variable[0] < constants[smoothest][0], (
        f"ridge error {variable[0]:.3%} vs {constants[smoothest][0]:.3%} for the "
        f"background-suppressing window s={smoothest}")

    # And it must be the best overall on a combined criterion.
    best_total = min(v[0] + 4 * v[1] for v in constants.values())
    assert variable[0] + 4 * variable[1] < best_total


# ------------------------------------------------------------- uncertainty

def test_measurement_noise_estimator_is_accurate():
    """Finite differences along the curves recover an injected noise level."""
    Ha, Hb, M_clean, _ = preisach_grid()
    assert forc.estimate_measurement_noise(M_clean) < 1e-12

    for level in (5e-9, 2e-8):
        _, _, M, _ = preisach_grid(noise=level, seed=11)
        estimate = forc.estimate_measurement_noise(M)
        assert estimate == pytest.approx(level, rel=0.15)


def test_propagated_uncertainty_predicts_the_scatter_of_rho():
    """The standard error must match the spread over independent noise draws."""
    level = 2.0e-8
    kw = dict(sc0=4, sc1=4, sb0=4, sb1=4, lambda_c=0.0, lambda_b=0.0, min_pts=10)
    Ha, Hb, M, _ = preisach_grid(noise=level, seed=0)

    draws = []
    for seed in range(12):
        _, _, Mi, _ = preisach_grid(noise=level, seed=200 + seed)
        draws.append(forc.variforc_rho_from_grid(Ha, Hb, Mi, **kw))
    scatter = np.nanstd(np.array(draws), axis=0, ddof=1)

    result = forc.variforc_rho_from_grid(Ha, Hb, M, estimate_uncertainty=True,
                                         noise=level, **kw)
    predicted = result["rho_sigma"]
    ok = np.isfinite(predicted) & np.isfinite(scatter) & (scatter > 0)
    assert ok.sum() > 500
    ratio = predicted[ok] / scatter[ok]
    # With 12 draws the Monte-Carlo estimate itself carries about 20% scatter.
    assert np.median(ratio) == pytest.approx(1.0, abs=0.15)

    assert result["noise"] == pytest.approx(level)
    snr = result["snr"]
    assert np.nanmax(snr) > 10, "the peak should be highly significant"


# -------------------------------------------------------------------- the API

def test_variforc_settings_translates_a_sample_description():
    """The helper maps what the user can see to the smoothing factors."""
    settings = forc.variforc_settings("central_ridge", smoothing_factor=9,
                                      growth_rate=0.1, central_ridge=4,
                                      central_ridge_position=0.0004)
    assert settings["sb0"] == 4.0 and settings["sb1"] == 9.0
    assert settings["sc0"] == 9.0 and settings["sc1"] == 9.0
    assert settings["lambda_b"] == pytest.approx(0.1)
    assert settings["ridge_limits"] == [("Bu", 0.0004, 4.0, None)]

    regular = forc.variforc_settings("regular", smoothing_factor=6)
    assert regular["sb0"] == regular["sb1"] == 6.0
    assert regular["ridge_limits"] is None

    both = forc.variforc_settings("both_ridges", smoothing_factor=8)
    assert both["sb0"] < both["sb1"] and both["sc0"] < both["sc1"]

    assert set(forc.VARIFORC_PRESETS) == {
        "regular", "central_ridge", "vertical_ridge", "both_ridges"}

    with pytest.raises(ValueError, match="Unknown preset"):
        forc.variforc_settings("nonsense")
    with pytest.raises(ValueError, match="smoothing_factor"):
        forc.variforc_settings("regular", smoothing_factor=0.5)
    with pytest.raises(ValueError, match="growth_rate"):
        forc.variforc_settings("regular", growth_rate=-0.1)


def test_pipeline_selects_variforc_and_records_it(micromag_file):
    """One keyword switches estimator, and the choice is archived."""
    loess = forc.process_forc(mode="i", path=str(micromag_file),
                                   plot_hyst=False, plot_rho=False, verbose=False)
    assert loess["smoothing"] == "loess"
    assert loess["smoothing_params"]["method"] == "loess"

    vari = forc.process_forc(
        mode="i", path=str(micromag_file), smoothing="variforc",
        variforc=forc.variforc_settings("central_ridge", smoothing_factor=5,
                                        growth_rate=0.05, central_ridge=3),
        plot_hyst=False, plot_rho=False, verbose=False)
    assert vari["smoothing"] == "variforc"
    assert vari["smoothing_params"]["preset"] == "central_ridge"
    assert vari["smoothing_params"]["sb0"] == 3.0
    assert np.isfinite(vari["rho"]).sum() > 100
    assert vari["rho"].shape == loess["rho"].shape

    with pytest.raises(ValueError, match="smoothing must be"):
        forc.process_forc(mode="i", path=str(micromag_file),
                               smoothing="nope", plot_hyst=False,
                               plot_rho=False, verbose=False)


def test_variforc_validates_its_inputs():
    """Malformed input fails immediately rather than returning nonsense."""
    Ha, Hb, M, _ = preisach_grid(step=0.004)

    with pytest.raises(ValueError, match="M_grid shape"):
        forc.variforc_rho_from_grid(Ha, Hb, M[:-1])
    with pytest.raises(ValueError, match="strictly increasing"):
        bad = Ha.copy(); bad[3] = bad[2] - 0.001
        forc.variforc_rho_from_grid(bad, Hb, M)
    with pytest.raises(ValueError, match="positive finite smoothing factor"):
        forc.variforc_rho_from_grid(Ha, Hb, M, sb0=0)
    with pytest.raises(ValueError, match="group_ratio"):
        forc.variforc_rho_from_grid(Ha, Hb, M, group_ratio=1.0)
    with pytest.raises(ValueError, match="no finite values"):
        forc.variforc_rho_from_grid(Ha, Hb, np.full_like(M, np.nan))


# ==========================================================================
# Stacking repeat measurement sets
# ==========================================================================

def test_stack_consistency_separates_repeats_from_disagreement():
    """Sets differing only by noise look consistent; a shifted set does not."""
    rng = np.random.default_rng(0)
    _, _, base, _ = preisach_grid()
    noise = 2.0e-8

    repeats = [base + noise * rng.standard_normal(base.shape) for _ in range(4)]
    report = forc.assess_stack_consistency(repeats)
    assert np.all(report["consistent"]), report["discrepancy"]
    assert report["max_discrepancy"] < 5.0
    assert_allclose(report["weights"].sum(), 1.0)

    # A set carrying a systematic gradient, as an uncorrected drift would.
    drifted = base * 1.05 + noise * rng.standard_normal(base.shape)
    report = forc.assess_stack_consistency(repeats + [drifted])
    assert not report["consistent"][-1]
    assert report["discrepancy"][-1] > 10 * np.median(report["discrepancy"][:-1])

    with pytest.raises(ValueError, match="at least two sets"):
        forc.assess_stack_consistency([base])


def test_weighted_stacking_favours_the_quieter_sets():
    """Inverse-variance weights must down-weight noisy sets and reduce error."""
    rng = np.random.default_rng(1)
    _, _, base, _ = preisach_grid()
    quiet = [base + 1.0e-8 * rng.standard_normal(base.shape) for _ in range(3)]
    loud = [base + 8.0e-8 * rng.standard_normal(base.shape) for _ in range(2)]
    grids = quiet + loud

    report = forc.assess_stack_consistency(grids)
    assert report["weights"][:3].min() > report["weights"][3:].max(), report["weights"]

    finite = np.isfinite(base)
    errors = {}
    for method in ("mean", "median", "weighted"):
        stacked, counts = forc._stack_nan_grids(grids, method=method)
        assert np.all(counts[finite] == len(grids))
        errors[method] = np.sqrt(np.mean((stacked[finite] - base[finite]) ** 2))
    # Weighting by noise must beat treating every set equally.
    assert errors["weighted"] < errors["mean"]
    assert errors["weighted"] < min(
        np.sqrt(np.mean((g[finite] - base[finite]) ** 2)) for g in grids)

    with pytest.raises(ValueError, match="stack_method must be"):
        forc._stack_nan_grids(grids, method="nonsense")


# ==========================================================================
# The optional compiled fast path
# ==========================================================================

requires_numba = pytest.mark.skipif(
    not forc.numba_available(), reason="numba is not installed")


def test_engine_selection_validates_and_degrades_gracefully():
    """An unknown engine is rejected; a missing one is reported clearly."""
    Ha, Hb, M, _ = preisach_grid(step=0.004)
    with pytest.raises(ValueError, match="engine must be"):
        forc.variforc_rho_from_grid(Ha, Hb, M, engine="nope")

    # The default must work whether or not numba is installed.
    rho = forc.variforc_rho_from_grid(Ha, Hb, M, engine="auto", min_pts=8)
    assert np.isfinite(rho).any()

    if not forc.numba_available():
        with pytest.raises(ValueError, match="numba is not available"):
            forc.variforc_rho_from_grid(Ha, Hb, M, engine="numba")


@requires_numba
@pytest.mark.parametrize("settings", [
    pytest.param(dict(sc0=5, sc1=5, sb0=5, sb1=5, lambda_c=0.0, lambda_b=0.0),
                 id="constant"),
    pytest.param(dict(sc0=3, sc1=7, sb0=3, sb1=7, lambda_c=0.1, lambda_b=0.1),
                 id="variable"),
    pytest.param(dict(sc0=7, sc1=7, sb0=3, sb1=7, lambda_c=0.1, lambda_b=0.1,
                      ridge_limits=[("Bu", 0.002, 3.0, 0.001)]),
                 id="ridge-limit"),
    pytest.param(dict(sc0=7, sc1=7, sb0=7, sb1=7, lambda_c=0.1, lambda_b=0.1,
                      diagonal_limits=[("Hr", -0.03, 2.0, 0.01)]),
                 id="diagonal-truncation"),
])
def test_numba_and_numpy_engines_agree(settings):
    """The compiled kernel is an optimization, not a different method."""
    Ha, Hb, M, _ = preisach_grid(noise=1e-9, seed=7)
    numpy_rho = forc.variforc_rho_from_grid(Ha, Hb, M, engine="numpy",
                                            min_pts=8, **settings)
    numba_rho = forc.variforc_rho_from_grid(Ha, Hb, M, engine="numba",
                                            min_pts=8, **settings)
    both = np.isfinite(numpy_rho) & np.isfinite(numba_rho)
    assert both.sum() > 500
    scale = np.nanmax(np.abs(numpy_rho[both]))
    assert np.max(np.abs(numpy_rho[both] - numba_rho[both])) < 1e-8 * scale
    # And they must agree on which cells are determinable, not just on values.
    assert np.isfinite(numpy_rho).sum() == pytest.approx(
        np.isfinite(numba_rho).sum(), rel=0.02)


@requires_numba
def test_numba_engine_reproduces_the_fitted_surface_and_uncertainty():
    """The extras follow the same code path in both engines."""
    Ha, Hb, M, _ = preisach_grid(noise=2e-8, seed=9)
    kw = dict(sc0=4, sc1=6, sb0=4, sb1=6, lambda_c=0.05, lambda_b=0.05,
              min_pts=8, noise=2e-8)
    a = forc.variforc_rho_from_grid(Ha, Hb, M, engine="numpy", return_fit=True,
                                    estimate_uncertainty=True, **kw)
    b = forc.variforc_rho_from_grid(Ha, Hb, M, engine="numba", return_fit=True,
                                    estimate_uncertainty=True, **kw)

    ok = np.isfinite(a["M_fit"]) & np.isfinite(b["M_fit"])
    assert ok.sum() > 500
    assert_allclose(a["M_fit"][ok], b["M_fit"][ok], rtol=1e-6,
                    atol=1e-8 * np.nanmax(np.abs(a["M_fit"][ok])))

    ok = np.isfinite(a["rho_sigma"]) & np.isfinite(b["rho_sigma"])
    assert ok.sum() > 500
    assert_allclose(a["rho_sigma"][ok], b["rho_sigma"][ok], rtol=1e-6,
                    atol=1e-8 * np.nanmax(a["rho_sigma"][ok]))
    assert a["noise"] == b["noise"]


@requires_numba
def test_numba_engine_recovers_the_analytic_quadratic():
    """The compiled kernel must be exact on a case with a closed-form answer."""
    Ha_vals, Hb_vals, M = quadratic_grid(size=41)
    rho = forc.variforc_rho_from_grid(
        Ha_vals, Hb_vals, M, sc0=4, sc1=4, sb0=4, sb1=4,
        lambda_c=0.0, lambda_b=0.0, min_pts=10, engine="numba")
    ok = np.isfinite(rho)
    assert ok.sum() > 400
    assert_allclose(rho[ok], -0.35, atol=1e-8)


# ==========================================================================
# First-point anomaly correction
# ==========================================================================

def test_first_point_anomaly_is_measured_against_the_curve_trend():
    """A clean family shows no anomaly; an injected one is recovered."""
    Ha, Hb, M, _ = preisach_grid(step=0.002)
    segments = []
    for i, ha in enumerate(Ha):
        row = M[i]
        ok = np.isfinite(row)
        if ok.sum() < 8:
            continue
        segments.append(forc.Segment(H=Hb[ok], M=row[ok], idx=i, kind="forc",
                                     Ha=float(ha)))
    assert len(segments) > 20

    clean = forc.measure_first_point_anomaly(segments)
    scale = np.nanmax(np.abs(M[np.isfinite(M)]))
    assert np.nanmax(np.abs(clean["anomaly"])) < 1e-3 * scale

    # Inject a first-point offset that varies smoothly with reversal field,
    # which is the signature Egli describes.
    injected = 0.02 * scale
    shifted = []
    for s in segments:
        m = s.M.copy()
        m[0] += injected * (1.0 - (s.Ha - Ha.min()) / (Ha.max() - Ha.min()))
        shifted.append(forc.Segment(H=s.H.copy(), M=m, idx=s.idx,
                                    kind="forc", Ha=s.Ha))
    found = forc.measure_first_point_anomaly(shifted)
    good = found["usable"]
    assert np.nanmax(found["anomaly"][good]) > 0.5 * injected


def test_first_point_correction_fires_only_on_a_real_trend():
    """The correction subtracts a systematic artefact and ignores noise."""
    Ha, Hb, M, _ = preisach_grid(step=0.002)
    rng = np.random.default_rng(3)
    scale = np.nanmax(np.abs(M[np.isfinite(M)]))
    noise = 0.002 * scale

    def family(with_trend):
        out = []
        for i, ha in enumerate(Ha):
            row = M[i].copy()
            ok = np.isfinite(row)
            if ok.sum() < 8:
                continue
            m = row[ok] + noise * rng.standard_normal(ok.sum())
            if with_trend:
                m[0] += 0.03 * scale * (1.0 - (ha - Ha.min()) / (Ha.max() - Ha.min()))
            out.append(forc.Segment(H=Hb[ok], M=m, idx=i, kind="forc",
                                    Ha=float(ha)))
        return out

    corrected, report = forc.correct_first_point_anomaly(family(True),
                                                         verbose=False)
    assert report["applied"], report
    assert report["amplitude"] > 2 * report["scatter"]
    # After correction the residual trend must be gone.
    after = forc.correct_first_point_anomaly(corrected, verbose=False)[1]
    assert not after["applied"]

    # A family with only noise must be left alone.
    _, quiet = forc.correct_first_point_anomaly(family(False), verbose=False)
    assert not quiet["applied"]

    # Too few curves is reported, not crashed on.
    _, tiny = forc.correct_first_point_anomaly(family(True)[:3], verbose=False)
    assert not tiny["applied"] and "too few" in tiny["reason"]


def test_pipeline_can_enable_the_first_point_correction(micromag_file):
    """The option is reachable from the pipeline and leaves clean data alone."""
    plain = forc.process_forc(mode="i", path=str(micromag_file),
                                   plot_hyst=False, plot_rho=False, verbose=False)
    corrected = forc.process_forc(mode="i", path=str(micromag_file),
                                       correct_first_point=True,
                                       plot_hyst=False, plot_rho=False,
                                       verbose=False)
    both = np.isfinite(plain["rho"]) & np.isfinite(corrected["rho"])
    assert both.sum() > 100
    # The synthetic file has no first-point artefact, so nothing should change.
    assert_allclose(plain["rho"][both], corrected["rho"][both], rtol=1e-9)


# ==========================================================================
# Paramagnetic / high-field slope correction
# ==========================================================================

def _forc_family_with_slope(chi_slope=0.0, n=40, dH=0.002):
    """A synthetic FORC family, optionally with a linear high-field slope."""
    Ha_vals = np.arange(-0.08, 0.0 + dH / 2, dH)
    segments = []
    for i, ha in enumerate(Ha_vals):
        H = np.arange(ha, 0.10 + dH / 2, dH)
        # A smooth saturating ferrimagnetic curve plus a linear slope.
        M = 1.0e-6 * np.tanh((H - ha) * 40.0) + chi_slope * H
        segments.append(forc.Segment(H=H, M=M, idx=i, kind="forc", Ha=float(ha)))
    return segments


def test_paramagnetic_correction_removes_an_injected_slope():
    """An injected high-field slope is recovered and removed."""
    slope = 3.0e-6                      # A m^2 / T
    segments = _forc_family_with_slope(chi_slope=slope)

    corrected, report = forc.correct_paramagnetic_slope(
        segments, fit_type="linear", verbose=False)
    assert report["applied"]

    # chi_HF is reported in SI, i.e. the fitted slope times mu_0.
    recovered = report["chi_HF"] / (4 * np.pi / 1e7)
    assert recovered == pytest.approx(slope, rel=0.1)

    def pooled_high_field_slope(segs):
        H = np.concatenate([s.H for s in segs if s.kind == "forc"])
        M = np.concatenate([s.M for s in segs if s.kind == "forc"])
        sel = H > 0.06
        return np.polyfit(H[sel], M[sel], 1)[0]

    before = pooled_high_field_slope(segments)
    after = pooled_high_field_slope(corrected)
    assert abs(after) < 0.15 * abs(before)


def test_paramagnetic_correction_leaves_rho_unchanged():
    """A term linear in the applied field has no mixed derivative."""
    segments = _forc_family_with_slope(chi_slope=3.0e-6)
    corrected, _ = forc.correct_paramagnetic_slope(segments, fit_type="linear",
                                                   verbose=False)

    def distribution(segs):
        curves = [s for s in segs if s.kind == "forc"]
        Ha, Hb, M, _, _ = forc.build_forc_grid(curves, verbose=False)
        return forc.loess_rho_from_grid_fast(Ha, Hb, M, span_Ha_T=0.008,
                                             span_Hb_T=0.008, min_pts=8)

    before, after = distribution(segments), distribution(corrected)
    both = np.isfinite(before) & np.isfinite(after)
    assert both.sum() > 100
    assert np.max(np.abs(before[both] - after[both])) < 1e-6 * np.nanmax(
        np.abs(before[both]))


def test_paramagnetic_correction_declines_without_signal():
    """Degenerate input is reported rather than fitted."""
    empty = [forc.Segment(H=np.array([0.0]), M=np.array([1e-6]), idx=0,
                          kind="cal")]
    out, report = forc.correct_paramagnetic_slope(empty, verbose=False)
    assert not report["applied"] and out is empty

    short = [forc.Segment(H=np.arange(3) * 0.01, M=np.zeros(3), idx=0,
                          kind="forc", Ha=0.0)]
    _, report = forc.correct_paramagnetic_slope(short, verbose=False)
    assert not report["applied"]


def test_branch_mirroring_builds_a_symmetric_loop():
    """The reconstructed loop is closed, even in length, and antisymmetric."""
    H = np.linspace(-0.1, 0.1, 41)
    M = np.tanh(H * 30.0)
    loop_H, loop_M = forc._mirror_branch_into_loop(H, M)
    assert loop_H.size == loop_M.size
    assert loop_H.size % 2 == 0
    half = loop_H.size // 2
    # The two halves are inversion images of one another.
    assert_allclose(loop_H[:half], -loop_H[half:][::-1])
    assert_allclose(loop_M[:half], -loop_M[half:][::-1])


# ==========================================================================
# Marginal coercivity distribution
# ==========================================================================

def test_coercivity_distribution_matches_the_analytic_marginal():
    """For a separable Preisach model the marginal has a closed form.

    With p = f(alpha) h(beta), integrating rho over Bu at fixed Bc is the
    cross-correlation of f and h. For two Gaussians of width sigma separated
    by alpha0 - beta0, that is a Gaussian in Bc centred at (alpha0-beta0)/2
    with standard deviation sigma/sqrt(2). The integral over all coercivities
    is Ms/2, which also checks the Jacobian of the rotation.
    """
    Ms, bc0, sigma = 1.0e-5, 0.030, 0.008
    Ha, Hb, _, rho_true = preisach_grid(step=0.001, Ms=Ms, bc0=bc0, sigma=sigma)

    result = forc.coercivity_distribution(Ha, Hb, rho_true, bin_width=0.001)

    assert result["peak"]["peak_x"] == pytest.approx(bc0, abs=0.001)
    expected_fwhm = 2 * np.sqrt(2 * np.log(2)) * sigma / np.sqrt(2)
    assert result["peak"]["fwhm"] == pytest.approx(expected_fwhm, rel=0.02)
    # dBc dBu = dHa dHb / 2, so the full integral is Ms/2.
    assert result["integral"] == pytest.approx(Ms / 2, rel=1e-3)


def test_coercivity_distribution_is_stable_across_smoothing_levels():
    """Integrating over Bu undoes much of what vertical smoothing does.

    The peak amplitude of the two-dimensional distribution falls steadily as
    the window grows, while the coercivity distribution barely moves. That is
    the practical reason to report it.
    """
    Ha, Hb, M, _ = preisach_grid(step=0.001, noise=5e-9, seed=4)

    peaks_2d, peaks_1d, widths = [], [], []
    for span in (0.004, 0.008, 0.016):
        rho = forc.loess_rho_from_grid_fast(Ha, Hb, M, span_Ha_T=span,
                                            span_Hb_T=span, min_pts=8)
        peaks_2d.append(np.nanmax(rho))
        result = forc.coercivity_distribution(Ha, Hb, rho, bin_width=0.001)
        peaks_1d.append(result["peak"]["peak_x"])
        widths.append(result["peak"]["fwhm"])

    assert peaks_2d[0] > peaks_2d[-1] * 1.3, "the 2D peak should fall with smoothing"
    assert max(peaks_1d) - min(peaks_1d) < 0.004, peaks_1d
    assert (max(widths) - min(widths)) / np.mean(widths) < 0.25, widths


def test_coercivity_distribution_honours_its_window_and_validates_input():
    """Restricting the Bu range restricts the integral; bad input fails early."""
    Ha, Hb, _, rho_true = preisach_grid(step=0.002)

    full = forc.coercivity_distribution(Ha, Hb, rho_true)
    narrow = forc.coercivity_distribution(Ha, Hb, rho_true,
                                          Bu_min=-0.004, Bu_max=0.004)
    assert narrow["Bu_range"] == pytest.approx((-0.004, 0.004))
    assert narrow["integral"] < full["integral"]

    coarse = forc.coercivity_distribution(Ha, Hb, rho_true, bin_width=0.004)
    fine = forc.coercivity_distribution(Ha, Hb, rho_true, bin_width=0.002)
    assert coarse["Bc"].size < fine["Bc"].size
    # The integral is a physical quantity and must not depend on the binning.
    assert coarse["integral"] == pytest.approx(fine["integral"], rel=0.05)

    with pytest.raises(ValueError, match="rho shape"):
        forc.coercivity_distribution(Ha, Hb, rho_true[:-1])
    with pytest.raises(ValueError, match="bin_width"):
        forc.coercivity_distribution(Ha, Hb, rho_true, bin_width=0)
    with pytest.raises(ValueError, match="no finite values"):
        forc.coercivity_distribution(Ha, Hb, np.full_like(rho_true, np.nan))


def test_plot_coercivity_distribution_draws(tmp_path):
    """The plotting helper runs and labels its axes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    Ha, Hb, _, rho_true = preisach_grid(step=0.002)
    result = forc.coercivity_distribution(Ha, Hb, rho_true)
    ax = forc.plot_coercivity_distribution(result, label="test")
    assert "B_c" in ax.get_xlabel()
    assert ax.get_legend() is not None
    plt.close("all")


def test_rho_is_independent_of_the_polynomial_basis():
    """The distribution must not depend on which coordinates the fit is written in.

    `pmagpy.forc` weights and fits in rotated coordinates and reads rho from
    (a_Bc2 - a_Bu2)/4. FORCsensei (Heslop et al., 2020) weights in rotated
    coordinates but fits in measurement coordinates and reads rho from -0.5
    times the mixed coefficient. A quadratic in one pair of coordinates is a
    quadratic in the other, so both must give the same answer; this reproduces
    the second formulation independently and checks that they do.

    The same comparison run against FORCsensei itself agrees to 1e-13 of peak.
    This test carries the invariance without adding a dependency.
    """
    step = 0.002
    Ha_vals, Hb_vals, M, _ = preisach_grid(step=step, noise=2e-9, seed=11)
    dH = step
    sc0, sc1, sb0, sb1, lam = 3.0, 7.0, 3.0, 7.0, 0.1

    ours = forc.variforc_rho_from_grid(
        Ha_vals, Hb_vals, M, sc0=sc0, sc1=sc1, sb0=sb0, sb1=sb1,
        lambda_c=lam, lambda_b=lam, dH=dH, min_pts=8, engine="numpy")

    # Reference: identical weighting, but the quadratic written in (Hr, H)
    # and rho taken as -0.5 times the mixed coefficient.
    A, B = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    keep = np.isfinite(M) & (B >= A)
    Hr, H, m = A[keep], B[keep], M[keep]
    Bc, Bu = 0.5 * (H - Hr), 0.5 * (H + Hr)
    design = np.column_stack((np.ones(H.size), H, Hr, H ** 2, Hr ** 2, H * Hr))
    s_c, s_b = forc.variforc_smoothing_factors(Bc, Bu, dH, sc0=sc0, sc1=sc1,
                                               sb0=sb0, sb1=sb1,
                                               lambda_c=lam, lambda_b=lam)

    reference = np.full(H.size, np.nan)
    for i in range(H.size):
        w = (forc.variforc_weight_1d((Bc - Bc[i]) / dH, s_c[i])
             * forc.variforc_weight_1d((Bu - Bu[i]) / dH, s_b[i]))
        sel = w > 0
        if np.count_nonzero(sel) < 8:
            continue
        root = np.sqrt(w[sel])[:, np.newaxis]
        coefficients = np.linalg.lstsq(design[sel] * root,
                                       m[sel] * root[:, 0], rcond=None)[0]
        reference[i] = -0.5 * coefficients[5]

    theirs = np.full(M.shape, np.nan)
    theirs[keep] = reference

    both = np.isfinite(ours) & np.isfinite(theirs)
    assert both.sum() > 1000
    scale = np.nanmax(np.abs(theirs[both]))
    assert np.max(np.abs(ours[both] - theirs[both])) < 1e-9 * scale


def nonuniform_quadratic_grid(size=29, jitter=0.18, seed=3):
    """Return a quadratic surface on a grid whose field steps are unequal.

    Every synthetic fixture above samples a perfectly regular lattice, which
    is exactly the condition under which a kernel that confuses "index offset
    times median step" with "difference of field values" still gives the right
    answer. Real reversal fields are not evenly spaced, so the spacing here is
    randomly perturbed while remaining monotonic.

    Args:
        size: Number of reversal and applied field values.
        jitter: Fractional perturbation applied to each field step.
        seed: Seed for the perturbation.

    Returns:
        Tuple of reversal fields, applied fields, and the sampled surface.
    """
    rng = np.random.default_rng(seed)

    def axis():
        steps = 1.0 + jitter * rng.uniform(-1.0, 1.0, size - 1)
        pos = np.concatenate([[0.0], np.cumsum(steps)])
        return -0.03 + 0.06 * pos / pos[-1]

    Ha_vals, Hb_vals = axis(), axis()
    Ha, Hb = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    M = (0.2 + 0.3 * Hb - 0.4 * Ha
         + 8.0 * Hb ** 2 + 0.7 * Hb * Ha - 4.0 * Ha ** 2)
    M[Hb < Ha] = np.nan
    return Ha_vals, Hb_vals, M


@pytest.mark.parametrize("engine", ["numpy", "numba"])
def test_variforc_is_exact_on_an_unevenly_spaced_grid(engine):
    """A quadratic must be recovered exactly even when the steps are unequal.

    rho = -0.5 * d2M/dHa dHb, so for this surface the exact value is
    -0.5 * 0.7 everywhere. A kernel that positions neighbours by index rather
    than by field value gets this wrong in proportion to the irregularity of
    the grid, which is how the disagreement with FORCsensei on real data was
    traced.
    """
    if engine == "numba" and not forc.numba_available():
        pytest.skip("numba is not installed")

    Ha_vals, Hb_vals, M = nonuniform_quadratic_grid()
    dH = float(np.median(np.diff(Ha_vals)))
    rho = forc.variforc_rho_from_grid(
        Ha_vals, Hb_vals, M, sc0=3, sc1=3, sb0=3, sb1=3,
        lambda_c=0.0, lambda_b=0.0, dH=dH, min_pts=8, engine=engine)

    interior = np.isfinite(rho)
    assert interior.sum() > 100
    assert np.allclose(rho[interior], -0.5 * 0.7, atol=1e-9)


def test_variforc_engines_agree_on_an_unevenly_spaced_grid():
    """The two engines must build the same neighbourhoods on an irregular grid.

    They previously did not: the NumPy path trimmed its shared candidate list
    with median-spacing estimates, which can drop an offset that the true
    spacing places inside the window.
    """
    if not forc.numba_available():
        pytest.skip("numba is not installed")

    Ha_vals, Hb_vals, M = nonuniform_quadratic_grid(size=33, jitter=0.3, seed=11)
    rng = np.random.default_rng(0)
    M = M + 1e-6 * rng.standard_normal(M.shape) * np.isfinite(M)
    dH = float(np.median(np.diff(Ha_vals)))

    kw = dict(sc0=2, sc1=6, sb0=2, sb1=6, lambda_c=0.15, lambda_b=0.15,
              dH=dH, min_pts=8)
    a = forc.variforc_rho_from_grid(Ha_vals, Hb_vals, M, engine="numpy", **kw)
    b = forc.variforc_rho_from_grid(Ha_vals, Hb_vals, M, engine="numba", **kw)

    both = np.isfinite(a) & np.isfinite(b)
    assert np.array_equal(np.isfinite(a), np.isfinite(b))
    assert np.max(np.abs(a[both] - b[both])) < 1e-9 * np.max(np.abs(a[both]))
