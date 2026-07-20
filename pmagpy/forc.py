"""
Tools for processing first-order reversal curve (FORC) measurements.

The staged processing workflow, one-call pipeline, plotting organization, and
FORC colormaps are adapted from FORCme (Brown, 2026).  The numerical core is
implemented directly from the locally weighted polynomial regression method
of Harrison and Feinberg (2008), the variable, anisotropic smoothing method of
Egli (2013), and the active FORCinel 3.08 procedure.  Both published methods
estimate the FORC distribution from a local quadratic fit to the measured
magnetization surface.  Calculations are made directly from measured field
coordinates; a regular grid is used only for the reported result.

The implementation deliberately retains FORCme's recognizable public
workflow while adapting three conditioning choices for PmagPy's input files
and published-method options: one-point calibration blocks are retained,
multiplicative FORCinel drift correction is the default, and lower-branch
subtraction never extends a short first FORC as a constant baseline.  These
compatibility differences are documented at the functions that implement
them; they do not change FORCme-derived names or plotting conventions.

Field values are represented in tesla.  Moments retain the units stored in the
input file, normally A m^2 for MicroMag hybrid-SI files.  The returned FORC
distribution therefore has moment per tesla squared units.

References
----------
Brown, M. (2026), FORCme: Application of machine code and adaptive smoothing
within Python for the rapid processing of First Order Reversal Curves,
version 1.0.0.  FORCme-derived workflow names and colormaps are used under the
MIT License; see ``licenses/FORCme_LICENSE.txt`` in the PmagPy source tree.

Harrison, R. J., and J. M. Feinberg (2008), FORCinel: An improved algorithm
for calculating first-order reversal curve distributions using locally
weighted regression smoothing, Geochemistry, Geophysics, Geosystems, 9,
Q05016, doi:10.1029/2008GC001987.

Egli, R. (2013), VARIFORC: An optimized protocol for calculating non-regular
first-order reversal curve (FORC) diagrams, Global and Planetary Change, 110,
302-320, doi:10.1016/j.gloplacha.2013.08.003.
"""

from dataclasses import dataclass, replace
from pathlib import Path
import re

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.signal import savgol_filter
from scipy.spatial import cKDTree


__all__ = [
    "ForcData",
    "ForcResult",
    "adjust_endpoints",
    "calculate_forc",
    "correct_drift",
    "estimate_field_step",
    "forc_colormap_v1",
    "forc_colormap_v2",
    "forc_colormap_v3",
    "forc_profile",
    "get_forc_cmap",
    "plot_forc",
    "plot_forc_curves",
    "plot_forc_curves_hysteresis",
    "process_forc",
    "read_forc",
    "run_forc_pipeline",
    "subtract_lower_branch",
    "variweight",
    "variforc_smoothing_factors",
]


FLOAT_PATTERN = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
NUMERIC_LINE = re.compile(
    rf"^\s*({FLOAT_PATTERN})\s*,\s*({FLOAT_PATTERN})\s*$"
)
HEADER_VALUE = re.compile(
    rf"^\s*([A-Za-z][A-Za-z0-9 ()/?*._-]*?)\s+({FLOAT_PATTERN})\s*$"
)


@dataclass(frozen=True)
class ForcData:
    """A collection of FORC measurements and calibration observations.

    Parameters:
        field : array-like
            Applied measurement field for every magnetization observation, in
            tesla.
        moment : array-like
            Measured moment.  MicroMag hybrid-SI files normally store A m^2.
        curve : array-like of int
            Zero-based FORC number for every observation.
        reversal_field : array-like
            Reversal field for each FORC, in tesla.
        sequence : array-like
            Acquisition-order coordinate for every observation.  It is used to
            interpolate calibration drift.
        curve_sequence : array-like
            Acquisition-order coordinate for each FORC.
        calibration_field, calibration_moment, calibration_sequence : array-like
            Calibration measurements and their acquisition-order coordinates.
        metadata : dict
            Numeric header values parsed from the source file.
        source : str
            Path of the source file, or a descriptive label for synthetic data.

    Notes:
        ``hc`` and ``hu`` are calculated properties.  With ``hr`` denoting a
        reversal field and ``h`` the measurement field, they are
        ``hc = (h - hr) / 2`` and ``hu = (h + hr) / 2``.
    """

    field: np.ndarray
    moment: np.ndarray
    curve: np.ndarray
    reversal_field: np.ndarray
    sequence: np.ndarray
    curve_sequence: np.ndarray
    calibration_field: np.ndarray
    calibration_moment: np.ndarray
    calibration_sequence: np.ndarray
    metadata: dict
    source: str = ""

    @property
    def hc(self):
        """Return coercivity coordinates for all observations, in tesla."""
        return (self.field - self.reversal_field[self.curve]) / 2.0

    @property
    def hu(self):
        """Return interaction/bias coordinates for all observations, in tesla."""
        return (self.field + self.reversal_field[self.curve]) / 2.0

    @property
    def n_curves(self):
        """Return the number of FORCs."""
        return int(self.reversal_field.size)

    def summary(self):
        """Return a compact dictionary describing the measurement collection."""
        finite = np.isfinite(self.moment)
        return {
            "source": self.source,
            "curves": self.n_curves,
            "measurements": int(self.moment.size),
            "finite_measurements": int(finite.sum()),
            "calibrations": int(self.calibration_moment.size),
            "field_min_T": float(np.nanmin(self.field)),
            "field_max_T": float(np.nanmax(self.field)),
            "reversal_min_T": float(np.nanmin(self.reversal_field)),
            "reversal_max_T": float(np.nanmax(self.reversal_field)),
            "field_step_T": estimate_field_step(self),
        }


@dataclass(frozen=True)
class ForcResult:
    """Result of a locally weighted FORC calculation.

    Parameters:
        hc, hu : two-dimensional arrays
            Coercivity and interaction/bias coordinates of the output grid, in
            tesla.
        rho : two-dimensional array
            FORC distribution in moment per tesla squared.
        moment_fit : two-dimensional array
            Local quadratic estimate of magnetization at each output point.
        rho_error : two-dimensional array
            Estimated standard error of ``rho``.  Values are NaN when error
            calculation was disabled.
        signal_to_noise : two-dimensional array
            Absolute ``rho / rho_error``.
        point_count : two-dimensional array
            Number of measured points used in each local regression.
        sc, sb : two-dimensional arrays
            Horizontal and vertical smoothing factors in field-step units.
        method : str
            ``"loess"`` or ``"variforc"``.
        parameters : dict
            Calculation settings and inferred grid information.
        data : ForcData
            Conditioned measurements used for the calculation.
    """

    hc: np.ndarray
    hu: np.ndarray
    rho: np.ndarray
    moment_fit: np.ndarray
    rho_error: np.ndarray
    signal_to_noise: np.ndarray
    point_count: np.ndarray
    sc: np.ndarray
    sb: np.ndarray
    method: str
    parameters: dict
    data: ForcData


def metadata_value(metadata, key, default=None):
    """Return a case-insensitive numeric metadata value."""
    key_lower = str(key).lower()
    for name, value in metadata.items():
        if str(name).lower() == key_lower:
            return value
    return default


def read_text(path):
    """Read a FORC text file while normalizing line endings."""
    raw = Path(path).expanduser().read_bytes()
    for encoding in ("utf-8", "cp1252", "mac_roman"):
        try:
            return raw.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")


def numeric_groups(lines):
    """Return blank-line-delimited groups of comma-separated numeric pairs."""
    groups = []
    current = []
    for line in lines:
        match = NUMERIC_LINE.match(line)
        if match:
            current.append((float(match.group(1)), float(match.group(2))))
        elif not line.strip() and current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    return groups


def read_forc(path):
    """Read a Princeton Measurements MicroMag FORC text file.

    Parameters:
        path : str or pathlib.Path
            Path to a MicroMag 2900/3900 FORC export.  Both LF/CRLF line
            endings and common legacy encodings are accepted.

    Returns:
        ForcData
            Measurement arrays, curve assignments, calibration observations,
            and numeric header metadata.

    Notes:
        MicroMag exports alternate a one-point calibration block with a FORC
        block.  The parser verifies this pattern against ``HCal`` when that
        header is present.  A fallback classifier also supports generic files
        in which calibration and FORC blocks are not strictly alternating.

    Examples:
        >>> from pmagpy import forc
        >>> data = forc.read_forc("example_FORC")
        >>> data.n_curves > 0
        True
        >>> data.summary()["field_step_T"] > 0
        True
    """
    text = read_text(path)
    lines = text.split("\n")

    data_start = None
    metadata = {}
    for index, line in enumerate(lines):
        match = HEADER_VALUE.match(line)
        if match:
            metadata[match.group(1).strip()] = float(match.group(2))
        if "(T)" in line and data_start is None:
            data_start = index + 1

    if data_start is None:
        for index, line in enumerate(lines):
            if "Field" in line and "Moment" in line:
                data_start = index + 1
                break
    if data_start is None:
        raise ValueError("Could not locate the field/moment data section.")

    groups = numeric_groups(lines[data_start:])
    if not groups:
        raise ValueError("No numeric FORC data blocks were found.")

    hcal = metadata_value(metadata, "HCal")
    alternating = False
    if hcal is not None and len(groups) >= 4:
        even = groups[0::2]
        alternating = all(
            len(group) == 1 and abs(group[0][0] - hcal) <= max(0.01, abs(hcal) * 0.08)
            for group in even
        )

    calibration_groups = []
    forc_groups = []
    if alternating:
        calibration_groups = [(index * 2, group) for index, group in enumerate(groups[0::2])]
        forc_groups = [(index * 2 + 1, group) for index, group in enumerate(groups[1::2])]
    else:
        tolerance = max(0.002, abs(hcal) * 0.03) if hcal is not None else 0.0
        for sequence, group in enumerate(groups):
            is_calibration = (
                hcal is not None
                and len(group) == 1
                and abs(group[0][0] - hcal) <= tolerance
            )
            if is_calibration:
                calibration_groups.append((sequence, group))
            else:
                forc_groups.append((sequence, group))

    if not forc_groups:
        raise ValueError("No FORC measurement blocks were identified.")

    fields = []
    moments = []
    curves = []
    sequences = []
    reversal_fields = []
    curve_sequences = []
    for curve_number, (sequence, group) in enumerate(forc_groups):
        field = np.asarray([row[0] for row in group], dtype=float)
        moment = np.asarray([row[1] for row in group], dtype=float)
        fields.append(field)
        moments.append(moment)
        curves.append(np.full(field.size, curve_number, dtype=int))
        sequences.append(np.full(field.size, float(sequence), dtype=float))
        reversal_fields.append(float(np.nanmin(field)))
        curve_sequences.append(float(sequence))

    calibration_field = np.asarray(
        [group[0][0] for _, group in calibration_groups], dtype=float
    )
    calibration_moment = np.asarray(
        [group[0][1] for _, group in calibration_groups], dtype=float
    )
    calibration_sequence = np.asarray(
        [sequence for sequence, _ in calibration_groups], dtype=float
    )

    return ForcData(
        field=np.concatenate(fields),
        moment=np.concatenate(moments),
        curve=np.concatenate(curves),
        reversal_field=np.asarray(reversal_fields, dtype=float),
        sequence=np.concatenate(sequences),
        curve_sequence=np.asarray(curve_sequences, dtype=float),
        calibration_field=calibration_field,
        calibration_moment=calibration_moment,
        calibration_sequence=calibration_sequence,
        metadata=metadata,
        source=str(Path(path).expanduser()),
    )


def estimate_field_step(data):
    """Estimate the nominal field increment from within-curve differences.

    Parameters:
        data : ForcData
            FORC measurements.

    Returns:
        float
            Median positive absolute field increment, in tesla.
    """
    differences = []
    for curve_number in range(data.n_curves):
        values = data.field[data.curve == curve_number]
        if values.size > 1:
            diff = np.abs(np.diff(values))
            diff = diff[np.isfinite(diff) & (diff > 0)]
            if diff.size:
                differences.append(diff)
    if not differences:
        raise ValueError("At least one FORC must contain two distinct field values.")
    return float(np.median(np.concatenate(differences)))


def smooth_calibrations(moment, smoothing=2):
    """Smooth calibration observations with a local quadratic window."""
    moment = np.asarray(moment, dtype=float)
    if smoothing is None or int(smoothing) <= 0 or moment.size < 5:
        return moment.copy()
    window = min(2 * int(smoothing) + 1, moment.size if moment.size % 2 else moment.size - 1)
    if window < 3:
        return moment.copy()
    return savgol_filter(moment, window_length=window, polyorder=min(2, window - 1), mode="interp")


def correct_drift(data, method="multiplicative", interpolation="linear", smoothing=2):
    """Correct magnetization drift using interleaved calibration measurements.

    Parameters:
        data : ForcData
            Measurements returned by :func:`read_forc`.
        method : {"multiplicative", "forcinel", "egli_equation23", "additive"}
            ``"multiplicative"`` and ``"forcinel"`` follow active FORCinel
            3.08: each moment is multiplied by the initial calibration moment
            divided by the interpolated calibration moment.  The printed
            Egli (2013) equation 23 contains the inverse ratio; the literal
            equation is available as ``"egli_equation23"`` for transparent
            reproduction.  ``"additive"`` subtracts calibration change and is
            provided for comparison with FORCme.
        interpolation : {"linear", "pchip"}
            Interpolation used between calibration observations.
        smoothing : int or None
            Half-width, in calibration observations, of a quadratic
            Savitzky-Golay smoother.  Use 0 or None to retain raw calibrations.

    Returns:
        ForcData
            A new immutable data object with corrected moments.

    Examples:
        >>> corrected = forc.correct_drift(data, method="multiplicative")
        >>> corrected.moment.shape == data.moment.shape
        True
    """
    if data.calibration_moment.size < 2:
        return data

    calibration = smooth_calibrations(data.calibration_moment, smoothing=smoothing)
    if interpolation == "linear":
        drift = np.interp(
            data.sequence,
            data.calibration_sequence,
            calibration,
            left=calibration[0],
            right=calibration[-1],
        )
    elif interpolation == "pchip":
        drift = PchipInterpolator(
            data.calibration_sequence, calibration, extrapolate=True
        )(data.sequence)
    else:
        raise ValueError("interpolation must be 'linear' or 'pchip'.")

    method_lower = str(method).lower()
    if method_lower in {"multiplicative", "forcinel"}:
        scale = max(np.nanmax(np.abs(calibration)), np.finfo(float).tiny)
        if np.any(np.abs(drift) <= scale * 1e-12):
            raise ValueError("Calibration interpolation crosses zero; multiplicative correction is undefined.")
        corrected = data.moment * calibration[0] / drift
    elif method_lower == "egli_equation23":
        if abs(calibration[0]) <= np.finfo(float).tiny:
            raise ValueError("The initial calibration is zero; Egli equation 23 is undefined.")
        corrected = data.moment * drift / calibration[0]
    elif method_lower == "additive":
        corrected = data.moment - (drift - calibration[0])
    else:
        raise ValueError(
            "method must be 'multiplicative', 'forcinel', "
            "'egli_equation23', or 'additive'."
        )

    metadata = dict(data.metadata)
    metadata["drift_correction"] = method_lower
    metadata["drift_interpolation"] = interpolation
    return replace(data, moment=np.asarray(corrected), metadata=metadata)


def linear_endpoint_value(field, moment, target, side):
    """Extrapolate one endpoint from its two nearest interior observations."""
    if side == "first":
        x1, x2 = field[1], field[2]
        y1, y2 = moment[1], moment[2]
    else:
        x1, x2 = field[-2], field[-3]
        y1, y2 = moment[-2], moment[-3]
    if x2 == x1:
        return np.nan
    return y1 + (y2 - y1) * (target - x1) / (x2 - x1)


def adjust_endpoints(data, method="drop", n=1):
    """Remove or replace potentially biased endpoints of every FORC.

    Parameters:
        data : ForcData
            FORC measurements.
        method : {"drop", "linear", "none"}
            ``"drop"`` sets the first and last ``n`` moments of every curve to
            NaN and matches the active FORCinel 3.08 procedure. ``"linear"``
            replaces one endpoint on each side by extrapolation, matching the
            current FORCme behavior. ``"none"`` leaves the data unchanged.
        n : int
            Number of points removed from each side for ``"drop"``.  Linear
            replacement currently supports ``n=1``.

    Returns:
        ForcData
            A new data object with endpoint conditioning applied.
    """
    if method == "none" or int(n) <= 0:
        return data
    if method not in {"drop", "linear"}:
        raise ValueError("method must be 'drop', 'linear', or 'none'.")
    if method == "linear" and int(n) != 1:
        raise ValueError("Linear endpoint replacement currently supports n=1.")

    moment = data.moment.copy()
    for curve_number in range(data.n_curves):
        indices = np.flatnonzero(data.curve == curve_number)
        if method == "drop":
            count = min(int(n), max(1, indices.size // 2))
            moment[indices[:count]] = np.nan
            moment[indices[-count:]] = np.nan
        elif indices.size >= 4:
            field = data.field[indices]
            values = moment[indices]
            moment[indices[0]] = linear_endpoint_value(field, values, field[0], "first")
            moment[indices[-1]] = linear_endpoint_value(field, values, field[-1], "last")

    metadata = dict(data.metadata)
    metadata["endpoint_method"] = method
    metadata["endpoint_count"] = int(n)
    return replace(data, moment=moment, metadata=metadata)


def common_field_axis(data, step=None):
    """Construct a regular field axis spanning the measured FORCs."""
    if step is None:
        step = estimate_field_step(data)
    lower = np.nanmin(data.field)
    upper = np.nanmax(data.field)
    start = np.floor(lower / step) * step
    stop = np.ceil(upper / step) * step
    return np.arange(start, stop + step * 0.5, step)


def subtract_lower_branch(data, n_curves=5, smoothing=2):
    """Subtract a coverage-aware estimate of the lower hysteresis branch.

    Parameters:
        data : ForcData
            FORC measurements.
        n_curves : int
            At each applied field, use up to this many of the lowest-reversal
            curves that contain a finite measurement at that field.  Allowing
            the contributing curves to change with field avoids extrapolating
            a short set of low-reversal curves across unsupported high fields.
        smoothing : int or None
            Half-width of a quadratic Savitzky-Golay smoother applied to the
            coverage-aware median branch.  Use 0 or None to skip smoothing.

    Returns:
        tuple
            ``(corrected_data, branch_field, branch_moment)``.  The final two
            arrays document the subtracted baseline.

    Notes:
        FORCme labels its first acquired FORC as the lower branch and extends
        that curve with constant endpoint values.  In common MicroMag files,
        the first FORC is instead a very short, high-reversal curve.  FORCinel
        pools the lowest-reversal FORCs and enables quadratic LOESS
        extrapolation, but that extrapolation can span most of the positive
        field range for triangular or diamond acquisition grids.

        This implementation uses measured coverage wherever possible.  For
        each field-grid position it selects the lowest-reversal curves that
        actually reach that position, takes their median, and smooths the
        resulting one-dimensional function of applied field.  Only short gaps
        introduced by grid rounding or endpoint removal are extrapolated, with
        a linear edge fit.  Subtracting a function of applied field alone does
        not change the ideal mixed derivative, although lower-branch removal
        remains optional because finite local fits can be affected near data
        boundaries.
    """
    count = min(max(1, int(n_curves)), data.n_curves)
    axis = common_field_axis(data)
    branches = np.full((data.n_curves, axis.size), np.nan, dtype=float)
    for curve_number in range(data.n_curves):
        mask = (data.curve == curve_number) & np.isfinite(data.moment)
        field = data.field[mask]
        moment = data.moment[mask]
        if field.size < 2:
            continue
        order = np.argsort(field)
        field = field[order]
        moment = moment[order]
        values = np.interp(axis, field, moment, left=np.nan, right=np.nan)
        values[(axis < field[0]) | (axis > field[-1])] = np.nan
        branches[curve_number] = values

    reversal_order = np.argsort(data.reversal_field)
    baseline = np.full(axis.size, np.nan, dtype=float)
    support = np.zeros(axis.size, dtype=int)
    for column in range(axis.size):
        available = reversal_order[np.isfinite(branches[reversal_order, column])]
        selected = available[:count]
        support[column] = selected.size
        if selected.size:
            baseline[column] = np.nanmedian(branches[selected, column])

    finite = np.isfinite(baseline)
    if not np.any(finite):
        raise ValueError("No lower-branch curves contain enough finite points.")
    if finite.sum() < 3:
        raise ValueError("The lower-branch estimate has insufficient coverage.")

    interpolated = np.interp(axis, axis[finite], baseline[finite])
    finite_indices = np.flatnonzero(finite)
    edge_width = min(max(3, 2 * int(smoothing or 0) + 1), finite_indices.size)
    first = finite_indices[:edge_width]
    last = finite_indices[-edge_width:]
    if first[0] > 0:
        coefficients = np.polyfit(axis[first], baseline[first], 1)
        interpolated[: first[0]] = np.polyval(coefficients, axis[: first[0]])
    if last[-1] < axis.size - 1:
        coefficients = np.polyfit(axis[last], baseline[last], 1)
        interpolated[last[-1] + 1 :] = np.polyval(coefficients, axis[last[-1] + 1 :])

    if smoothing is not None and int(smoothing) > 0 and interpolated.size >= 5:
        window = min(
            2 * int(smoothing) + 1,
            interpolated.size if interpolated.size % 2 else interpolated.size - 1,
        )
        interpolated = savgol_filter(
            interpolated, window_length=window, polyorder=min(2, window - 1), mode="interp"
        )

    corrected = data.moment - np.interp(data.field, axis, interpolated)
    metadata = dict(data.metadata)
    metadata["lower_branch_curves"] = count
    metadata["lower_branch_method"] = "coverage_median"
    metadata["lower_branch_min_support"] = int(np.min(support[finite]))
    metadata["lower_branch_max_support"] = int(np.max(support))
    return replace(data, moment=corrected, metadata=metadata), axis, interpolated


def output_grid(data, output_step=1, field_step=None):
    """Build the regular Hc-Hu output grid and its physical-domain mask."""
    if field_step is None:
        field_step = estimate_field_step(data)
    spacing = float(field_step) * int(output_step)
    raw_hc = data.hc
    raw_hu = data.hu
    hc_values = np.arange(0.0, np.ceil(np.nanmax(raw_hc) / spacing) * spacing + spacing * 0.5, spacing)
    hu_start = np.floor(np.nanmin(raw_hu) / spacing) * spacing
    hu_stop = np.ceil(np.nanmax(raw_hu) / spacing) * spacing
    hu_values = np.arange(hu_start, hu_stop + spacing * 0.5, spacing)
    hc, hu = np.meshgrid(hc_values, hu_values)

    target_field = hc + hu
    target_reversal = hu - hc
    margin = field_step * 0.55
    valid = (
        (target_reversal >= np.nanmin(data.reversal_field) - margin)
        & (target_reversal <= np.nanmax(data.reversal_field) + margin)
        & (target_field >= target_reversal - margin)
        & (target_field <= np.nanmax(data.field) + margin)
        & (target_field >= np.nanmin(data.field) - margin)
    )
    return hc, hu, valid, float(field_step)


def variweight(u, smoothing_factor):
    """Evaluate the one-dimensional VARIFORC weight function.

    Parameters:
        u : scalar or array-like
            Distance from the output point in field-step units.
        smoothing_factor : scalar or array-like
            Half-width of the regression region in field-step units.

    Returns:
        numpy.ndarray or float
            Weights defined by Egli (2013, equation 6).  They equal one
            throughout the interior, transition continuously across the outer
            field increment, and are zero outside the regression region.
    """
    distance = np.abs(np.asarray(u, dtype=float))
    sf = np.asarray(smoothing_factor, dtype=float)
    distance, sf = np.broadcast_arrays(distance, sf)
    weight = np.zeros(distance.shape, dtype=float)
    inner = distance <= sf - 1.0
    shoulder1 = (distance > sf - 1.0) & (distance <= sf - 0.5)
    shoulder2 = (distance > sf - 0.5) & (distance <= sf)
    weight[inner] = 1.0
    weight[shoulder1] = 1.0 - 2.0 * (distance[shoulder1] - sf[shoulder1] + 1.0) ** 2
    weight[shoulder2] = 2.0 * (distance[shoulder2] - sf[shoulder2]) ** 2
    return float(weight) if weight.ndim == 0 else weight


def variforc_smoothing_factors(
    hc,
    hu,
    field_step,
    sc0=3.0,
    sc1=7.0,
    sb0=3.0,
    sb1=7.0,
    lambda_c=0.07,
    lambda_b=0.07,
    ridge_offset=0.0,
):
    """Calculate local horizontal and vertical VARIFORC smoothing factors.

    Parameters:
        hc, hu : scalar or array-like
            Output coordinates in tesla.
        field_step : float
            Nominal measurement increment in tesla.
        sc0, sc1 : float
            Minimum smoothing at the vertical ridge and background horizontal
            smoothing, respectively.
        sb0, sb1 : float
            Minimum smoothing at the central ridge and background vertical
            smoothing, respectively.
        lambda_c, lambda_b : float
            Linear rates at which smoothing grows away from the ridges.
        ridge_offset : float
            Vertical location of the central ridge in tesla.

    Returns:
        tuple of numpy.ndarray
            ``(sc, sb)`` in field-step units.  The transition formula prevents
            a regression window centered outside a ridge from crossing that
            ridge, matching the active FORCinel 3.08 implementation.
    """
    hc_steps = np.abs(np.asarray(hc, dtype=float)) / float(field_step)
    hu_steps = np.abs(np.asarray(hu, dtype=float) - ridge_offset) / float(field_step)
    sc_linear = (1.0 - lambda_c) * sc1 + lambda_c * hc_steps
    sb_linear = (1.0 - lambda_b) * sb1 + lambda_b * hu_steps
    sc = np.minimum(np.maximum(sc_linear, sc0), np.maximum(sc0, hc_steps))
    sb = np.minimum(np.maximum(sb_linear, sb0), np.maximum(sb0, hu_steps))
    return sc, sb


def quadratic_fit(x, y, moment, weight, field_step, error_method="hc3"):
    """Fit a centered weighted quadratic and return FORC statistics."""
    design = np.column_stack((
        np.ones_like(x),
        x,
        x * x,
        y,
        y * y,
        x * y,
    ))
    weighted_design = design * weight[:, None]
    normal = design.T @ weighted_design
    right = design.T @ (weight * moment)
    try:
        coefficients = np.linalg.solve(normal, right)
        inverse = np.linalg.inv(normal) if error_method is not None else None
    except np.linalg.LinAlgError:
        root_weight = np.sqrt(weight)
        coefficients, _, rank, _ = np.linalg.lstsq(
            design * root_weight[:, None], moment * root_weight, rcond=None
        )
        if rank < 6:
            return np.nan, np.nan, np.nan
        inverse = np.linalg.pinv(normal) if error_method is not None else None

    scale = 4.0 * field_step * field_step
    rho = (coefficients[2] - coefficients[4]) / scale
    if error_method is None:
        return rho, coefficients[0], np.nan

    residual = moment - design @ coefficients
    if error_method == "classic":
        dof = max(1, moment.size - 6)
        variance = np.sum(weight * residual * residual) / dof
        covariance = inverse * variance
    elif error_method == "hc3":
        leverage = weight * np.einsum("ij,jk,ik->i", design, inverse, design)
        adjusted = np.sqrt(weight) * residual / np.maximum(1.0 - leverage, 1e-8)
        root_design = design * np.sqrt(weight)[:, None]
        score = root_design * adjusted[:, None]
        covariance = inverse @ (score.T @ score) @ inverse
    else:
        raise ValueError("error_method must be 'hc3', 'classic', or None.")
    contrast_variance = covariance[2, 2] + covariance[4, 4] - 2.0 * covariance[2, 4]
    error = np.sqrt(max(0.0, contrast_variance)) / scale
    return rho, coefficients[0], error


def empty_result_arrays(shape):
    """Allocate arrays shared by both smoothing algorithms."""
    return (
        np.full(shape, np.nan),
        np.full(shape, np.nan),
        np.full(shape, np.nan),
        np.zeros(shape, dtype=int),
        np.full(shape, np.nan),
        np.full(shape, np.nan),
    )


def finish_result(
    data,
    method,
    hc,
    hu,
    rho,
    moment_fit,
    rho_error,
    point_count,
    sc,
    sb,
    parameters,
):
    """Construct a ForcResult and calculate its signal-to-noise array."""
    with np.errstate(divide="ignore", invalid="ignore"):
        signal_to_noise = np.abs(rho / rho_error)
    signal_to_noise[~np.isfinite(signal_to_noise)] = np.nan
    return ForcResult(
        hc=hc,
        hu=hu,
        rho=rho,
        moment_fit=moment_fit,
        rho_error=rho_error,
        signal_to_noise=signal_to_noise,
        point_count=point_count,
        sc=sc,
        sb=sb,
        method=method,
        parameters=parameters,
        data=data,
    )


def calculate_loess(
    data,
    smoothing_factor=3.0,
    output_step=1,
    min_points=7,
    error_method="hc3",
):
    """Calculate a FORC distribution with Harrison nearest-neighbor LOESS."""
    hc, hu, valid, field_step = output_grid(data, output_step=output_step)
    finite = np.isfinite(data.moment) & np.isfinite(data.hc) & np.isfinite(data.hu)
    points = np.column_stack((data.hc[finite], data.hu[finite])) / field_step
    moments = data.moment[finite]
    tree = cKDTree(points)

    n_observed = int(finite.sum())
    max_curve_points = max(np.count_nonzero(data.curve == curve) for curve in range(data.n_curves))
    n_total = data.n_curves * max_curve_points
    fraction = (2.0 * float(smoothing_factor) + 1.0) ** 2 / n_observed
    neighbors = 1 + int(np.floor(fraction * n_total))
    neighbors = min(n_observed, max(int(min_points) + 1, neighbors))

    targets = np.column_stack((hc[valid], hu[valid])) / field_step
    distance, indices = tree.query(targets, k=neighbors, workers=-1)
    if neighbors == 1:
        distance = distance[:, None]
        indices = indices[:, None]

    rho, moment_fit, rho_error, point_count, sc, sb = empty_result_arrays(hc.shape)
    output_indices = np.flatnonzero(valid)
    for row, output_index in enumerate(output_indices):
        local_distance = distance[row]
        local_indices = indices[row]
        maximum = np.nanmax(local_distance)
        if not np.isfinite(maximum) or maximum <= 0:
            continue
        weight = (1.0 - np.minimum(local_distance / maximum, 1.0) ** 3) ** 3
        keep = weight > 0
        if keep.sum() < min_points:
            continue
        target = targets[row]
        local = points[local_indices[keep]] - target
        values = moments[local_indices[keep]]
        fit = quadratic_fit(
            local[:, 0], local[:, 1], values, weight[keep], field_step, error_method
        )
        rho.flat[output_index], moment_fit.flat[output_index], rho_error.flat[output_index] = fit
        point_count.flat[output_index] = int(keep.sum())
        sc.flat[output_index] = maximum
        sb.flat[output_index] = maximum

    return finish_result(
        data,
        "loess",
        hc,
        hu,
        rho,
        moment_fit,
        rho_error,
        point_count,
        sc,
        sb,
        {
            "smoothing_factor": float(smoothing_factor),
            "neighbors": int(neighbors),
            "n_observed": n_observed,
            "n_total": int(n_total),
            "field_step_T": field_step,
            "output_step": int(output_step),
            "error_method": error_method,
        },
    )


def calculate_variforc(
    data,
    sc0=3.0,
    sc1=7.0,
    sb0=3.0,
    sb1=7.0,
    lambda_c=0.07,
    lambda_b=0.07,
    ridge_offset=0.0,
    output_step=1,
    min_points=7,
    error_method="hc3",
):
    """Calculate a FORC distribution with variable anisotropic smoothing."""
    hc, hu, valid, field_step = output_grid(data, output_step=output_step)
    finite = np.isfinite(data.moment) & np.isfinite(data.hc) & np.isfinite(data.hu)
    points = np.column_stack((data.hc[finite], data.hu[finite])) / field_step
    moments = data.moment[finite]
    tree = cKDTree(points)

    targets = np.column_stack((hc[valid], hu[valid]))
    local_sc, local_sb = variforc_smoothing_factors(
        targets[:, 0],
        targets[:, 1],
        field_step,
        sc0=sc0,
        sc1=sc1,
        sb0=sb0,
        sb1=sb1,
        lambda_c=lambda_c,
        lambda_b=lambda_b,
        ridge_offset=ridge_offset,
    )
    scaled_targets = targets / field_step
    candidate_radius = np.maximum(local_sc, local_sb)
    candidates = tree.query_ball_point(
        scaled_targets, r=candidate_radius, p=np.inf, workers=-1
    )

    rho, moment_fit, rho_error, point_count, sc, sb = empty_result_arrays(hc.shape)
    output_indices = np.flatnonzero(valid)
    for row, output_index in enumerate(output_indices):
        candidate = np.asarray(candidates[row], dtype=int)
        if candidate.size < min_points:
            continue
        local = points[candidate] - scaled_targets[row]
        inside = (
            (np.abs(local[:, 0]) <= local_sc[row])
            & (np.abs(local[:, 1]) <= local_sb[row])
        )
        local = local[inside]
        candidate = candidate[inside]
        if candidate.size < min_points:
            continue
        weight = variweight(local[:, 0], local_sc[row]) * variweight(
            local[:, 1], local_sb[row]
        )
        keep = weight > 0
        if keep.sum() < min_points:
            continue
        fit = quadratic_fit(
            local[keep, 0],
            local[keep, 1],
            moments[candidate[keep]],
            weight[keep],
            field_step,
            error_method,
        )
        rho.flat[output_index], moment_fit.flat[output_index], rho_error.flat[output_index] = fit
        point_count.flat[output_index] = int(keep.sum())
        sc.flat[output_index] = local_sc[row]
        sb.flat[output_index] = local_sb[row]

    return finish_result(
        data,
        "variforc",
        hc,
        hu,
        rho,
        moment_fit,
        rho_error,
        point_count,
        sc,
        sb,
        {
            "sc0": float(sc0),
            "sc1": float(sc1),
            "sb0": float(sb0),
            "sb1": float(sb1),
            "lambda_c": float(lambda_c),
            "lambda_b": float(lambda_b),
            "ridge_offset_T": float(ridge_offset),
            "field_step_T": field_step,
            "output_step": int(output_step),
            "error_method": error_method,
        },
    )


def calculate_forc(data, method="variforc", **kwargs):
    """Calculate a FORC distribution using a published smoothing algorithm.

    Parameters:
        data : ForcData
            Measurements, normally after drift and endpoint conditioning.
        method : {"variforc", "loess"}
            ``"loess"`` selects the Harrison and Feinberg (2008)
            nearest-neighbor tricube method. ``"variforc"`` selects the Egli
            (2013) rectangular, anisotropic, variable-smoothing method.
        **kwargs
            Method-specific settings.  Common options include ``output_step``
            (an integer output-grid decimation), ``min_points``, and
            ``error_method`` (``"hc3"``, ``"classic"``, or None).

    Returns:
        ForcResult
            FORC distribution, uncertainty, signal-to-noise, smoothing maps,
            point counts, and processing metadata.

    Examples:
        >>> result = forc.calculate_forc(
        ...     corrected, method="variforc", sc0=3, sc1=7,
        ...     sb0=3, sb1=7, lambda_c=0.07, lambda_b=0.07,
        ... )
        >>> result.rho.shape == result.hc.shape
        True
    """
    method_lower = str(method).lower()
    if method_lower in {"loess", "forcinel", "harrison"}:
        return calculate_loess(data, **kwargs)
    if method_lower in {"variforc", "egli"}:
        return calculate_variforc(data, **kwargs)
    raise ValueError("method must be 'loess' or 'variforc'.")


def run_forc_pipeline(
    path,
    sample_title=None,
    mode="i",
    file_type="*",
    method="variforc",
    drift=True,
    drift_method="multiplicative",
    drift_fit="linear",
    drift_smoothing=2,
    endpoint_method="drop",
    endpoint_replace_n=1,
    do_lower_branch_subtract=False,
    lower_branch_curves=5,
    lower_branch_smoothing=2,
    **kwargs,
):
    """Run the staged FORCme-style workflow with published FORC algorithms.

    Parameters:
        path : str or pathlib.Path
            Input MicroMag FORC file.  In batch mode, this is a directory.
        sample_title : str or None
            Optional title stored with the output.  When omitted, individual
            and batch results use the input filename stem, matching FORCme's
            automatic-title behavior.
        mode : {"i", "b"}
            FORCme-compatible processing mode: ``"i"`` processes one file and
            returns one output dictionary; ``"b"`` processes every matching
            file independently and returns a list of dictionaries.  FORCme's
            M-space stacking mode is not exposed until PmagPy can preserve
            measured-coordinate uncertainty on a defensible common grid.
        file_type : str
            Glob used to discover files in batch mode.  The default ``"*"``
            includes extensionless MicroMag exports.
        method : {"variforc", "loess"}
            Local-regression algorithm used for the final distribution.
        drift : bool
            Apply calibration drift correction.
        drift_method : {"multiplicative", "forcinel", "egli_equation23", "additive"}
            ``"multiplicative"`` follows active FORCinel 3.08.  ``"additive"``
            reproduces the correction model used by FORCme.
        drift_fit : {"linear", "pchip"}
            Interpolation between calibration measurements.  The familiar
            FORCme name is retained, although linear interpolation is the
            published and default choice.
        drift_smoothing : int or None
            Calibration smoothing half-width.
        endpoint_method : {"drop", "linear", "none"}
            Endpoint treatment.  ``"drop"`` follows active FORCinel;
            ``"linear"`` follows FORCme's replacement workflow.
        endpoint_replace_n : int
            Number of endpoint observations treated on each side.
        do_lower_branch_subtract : bool
            Apply the optional coverage-aware lower-branch centering step.
        lower_branch_curves : int
            Maximum number of locally available low-reversal curves used to
            construct the baseline.
        lower_branch_smoothing : int or None
            Baseline smoothing half-width.
        **kwargs
            Options passed to :func:`calculate_forc`.

    Returns:
        dict or list of dict
            The single-file dictionary intentionally mirrors FORCme's staged
            output style.  It contains ``raw``, ``drift_corrected``,
            ``conditioned``, ``processed``, ``result``, ``rho``, ``Hc``,
            ``Hu``, baseline arrays, the input path, and processing settings.
            Batch mode returns one such dictionary per file.

    Notes:
        This function preserves the recognizable FORCme workflow and parameter
        names while delegating scientific smoothing to the Harrison or Egli
        implementations in this module.  The measured-coordinate regression
        keeps ``method="loess"`` and ``method="variforc"`` directly traceable
        to the two published algorithms and the corresponding FORCinel paths.

    Examples:
        >>> output = forc.run_forc_pipeline("example_FORC", method="variforc")
        >>> output["rho"].shape == output["Hc"].shape
        True
    """
    mode_lower = str(mode).strip().lower()
    input_path = Path(path).expanduser()
    if mode_lower == "b":
        if not input_path.is_dir():
            raise ValueError("Batch mode requires a directory path.")
        files = sorted(
            candidate
            for candidate in input_path.glob(str(file_type))
            if (
                candidate.is_file()
                and not candidate.name.startswith(".")
                and not candidate.name.endswith("_MagIC.txt")
            )
        )
        if not files:
            raise FileNotFoundError(
                f"No files matched {file_type!r} in {str(input_path)!r}."
            )
        return [
            run_forc_pipeline(
                candidate,
                sample_title=sample_title,
                method=method,
                mode="i",
                drift=drift,
                drift_method=drift_method,
                drift_fit=drift_fit,
                drift_smoothing=drift_smoothing,
                endpoint_method=endpoint_method,
                endpoint_replace_n=endpoint_replace_n,
                do_lower_branch_subtract=do_lower_branch_subtract,
                lower_branch_curves=lower_branch_curves,
                lower_branch_smoothing=lower_branch_smoothing,
                **kwargs,
            )
            for candidate in files
        ]
    if mode_lower != "i":
        raise ValueError("mode must be 'i' (individual) or 'b' (batch).")
    if not input_path.is_file():
        raise FileNotFoundError(f"FORC input file not found: {str(input_path)!r}")
    output_title = str(sample_title).strip() if sample_title is not None else ""
    if not output_title:
        output_title = input_path.stem

    raw = read_forc(input_path)
    if drift:
        drift_corrected = correct_drift(
            raw,
            method=drift_method,
            interpolation=drift_fit,
            smoothing=drift_smoothing,
        )
    else:
        drift_corrected = raw
    conditioned = adjust_endpoints(
        drift_corrected, method=endpoint_method, n=endpoint_replace_n
    )

    baseline_field = np.array([], dtype=float)
    baseline_moment = np.array([], dtype=float)
    if do_lower_branch_subtract:
        processed, baseline_field, baseline_moment = subtract_lower_branch(
            conditioned,
            n_curves=lower_branch_curves,
            smoothing=lower_branch_smoothing,
        )
    else:
        processed = conditioned

    result = calculate_forc(processed, method=method, **kwargs)
    return {
        "input_path": str(input_path),
        "sample_title": output_title,
        "raw": raw,
        "drift_corrected": drift_corrected,
        "conditioned": conditioned,
        "processed": processed,
        "forcs_display": conditioned,
        "forcs_rho": processed,
        "baseline_field": baseline_field,
        "baseline_moment": baseline_moment,
        "result": result,
        "rho": result.rho,
        "Hc": result.hc,
        "Hu": result.hu,
        "processing": {
            "method": method,
            "drift": bool(drift),
            "drift_method": drift_method,
            "drift_fit": drift_fit,
            "drift_smoothing": drift_smoothing,
            "endpoint_method": endpoint_method,
            "endpoint_replace_n": int(endpoint_replace_n),
            "do_lower_branch_subtract": bool(do_lower_branch_subtract),
            "lower_branch_curves": int(lower_branch_curves),
            "lower_branch_smoothing": lower_branch_smoothing,
        },
    }


def process_forc(
    path,
    method="variforc",
    drift=True,
    drift_method="multiplicative",
    drift_interpolation="linear",
    drift_smoothing=2,
    endpoints="drop",
    endpoint_count=1,
    lower_branch_curves=0,
    **kwargs,
):
    """Read, condition, and calculate a FORC diagram in one call.

    Parameters:
        path : str or pathlib.Path
            MicroMag FORC text file.
        method : {"variforc", "loess"}
            Published local-regression algorithm.
        drift : bool
            Apply calibration drift correction.
        drift_method : {"multiplicative", "forcinel", "egli_equation23", "additive"}
            Correction model passed to :func:`correct_drift`.  The default
            follows active FORCinel 3.08; the literal printed Egli equation and
            FORCme additive behavior are explicit alternatives.
        drift_interpolation : {"linear", "pchip"}
            Calibration interpolation method.
        drift_smoothing : int or None
            Calibration smoothing half-width.
        endpoints : {"drop", "linear", "none"}
            Endpoint treatment passed to :func:`adjust_endpoints`.
        endpoint_count : int
            Number of endpoints removed from each side when ``endpoints`` is
            ``"drop"``.
        lower_branch_curves : int
            Maximum number of lowest-reversal curves with local field coverage
            used by the optional coverage-aware baseline subtraction.  Zero
            disables subtraction.
        **kwargs
            Options passed to :func:`calculate_forc`.

    Returns:
        ForcResult
            Complete calculation result.  The conditioned measurements are
            available as ``result.data``.

    Examples:
        >>> result = forc.process_forc(
        ...     "example_FORC", method="variforc", output_step=2
        ... )
        >>> fig, ax, colorbar = forc.plot_forc(result)
    """
    output = run_forc_pipeline(
        path,
        method=method,
        drift=drift,
        drift_method=drift_method,
        drift_fit=drift_interpolation,
        drift_smoothing=drift_smoothing,
        endpoint_method=endpoints,
        endpoint_replace_n=endpoint_count,
        do_lower_branch_subtract=int(lower_branch_curves) > 0,
        lower_branch_curves=lower_branch_curves if int(lower_branch_curves) > 0 else 5,
        **kwargs,
    )
    return output["result"]


def plot_forc_curves(data, fraction=0.1, ax=None, color="0.25", linewidth=0.8):
    """Plot a representative subset of measured FORCs.

    Parameters:
        data : ForcData
            Measurements to plot.
        fraction : float
            Fraction of curves shown. Values at least one are interpreted as a
            curve count.
        ax : matplotlib.axes.Axes or None
            Existing axis.  A new figure and axis are created when omitted.
        color, linewidth : matplotlib style options

    Returns:
        tuple
            ``(figure, axis)``.
    """
    if ax is None:
        figure, ax = plt.subplots(figsize=(7, 4.5))
    else:
        figure = ax.figure
    if fraction < 1:
        count = max(1, int(np.ceil(data.n_curves * float(fraction))))
    else:
        count = min(data.n_curves, int(fraction))
    chosen = np.unique(np.linspace(0, data.n_curves - 1, count).astype(int))
    for curve_number in chosen:
        mask = data.curve == curve_number
        ax.plot(data.field[mask] * 1e3, data.moment[mask], color=color, linewidth=linewidth)
    ax.set_xlabel("Applied field, $\\mu_0 H$ (mT)")
    ax.set_ylabel("Moment")
    ax.set_title("First-order reversal curves")
    return figure, ax


def plot_forc_curves_hysteresis(
    data,
    title="FORC curves (H vs M)",
    plot_fraction=0.1,
    figsize=(7, 4.5),
    dpi=120,
    ax=None,
):
    """Plot FORC curves using the familiar FORCme plotting entry point.

    Parameters:
        data : ForcData
            Measurements to plot.
        title : str
            Axis title.
        plot_fraction : float
            Fraction or count of curves passed to :func:`plot_forc_curves`.
        figsize : two-element tuple
            Figure size in inches when a new axis is created.
        dpi : int
            Figure resolution when a new axis is created.
        ax : matplotlib.axes.Axes or None
            Optional existing axis.

    Returns:
        tuple
            ``(figure, axis)``.

    Notes:
        The name and calling pattern follow FORCme.  PmagPy accepts its
        immutable :class:`ForcData` container instead of FORCme ``Segment``
        lists so calibration provenance and curve assignments remain intact.
    """
    if ax is None:
        figure, ax = plt.subplots(figsize=figsize, dpi=dpi)
    else:
        figure = ax.figure
    figure, ax = plot_forc_curves(
        data,
        fraction=plot_fraction,
        ax=ax,
        color="0.25",
        linewidth=0.8,
    )
    ax.set_title(title)
    return figure, ax


def forc_colormap_v1():
    """Return FORCme's version-1 diverging colormap.

    This definition is adapted verbatim in color-stop content from FORCme
    1.0.0 ``forc_colormap_v1`` (Brown, 2026) under the MIT License.  Negative
    values are blue, zero is white, and positive values progress through
    yellow and red to magenta.
    """
    colors = [
        (0.00, "#1f4aa8"),
        (0.22, "#86a6da"),
        (0.50, "#ffffff"),
        (0.62, "#f2e85c"),
        (0.78, "#d94b2a"),
        (0.90, "#c4172a"),
        (1.00, "#d100b5"),
    ]
    return LinearSegmentedColormap.from_list("forcme_v1", colors)


def forc_colormap_v2():
    """Return FORCme's green-red FORC colormap.

    Negative values are light blue, zero is white, and positive values pass
    through green, yellow, and red to purple.  The color-stop content is
    adapted from FORCme 1.0.0 (Brown, 2026) under the MIT License.
    """
    colors = [
        (0.00, "#8fb3ff"),
        (0.50, "#ffffff"),
        (0.55, "#558D36"),
        (0.65, "#f2e85c"),
        (0.82, "#e84d3c"),
        (1.00, "#5b1e73"),
    ]
    return LinearSegmentedColormap.from_list("forcme_v2", colors)


def forc_colormap_v3():
    """Return FORCme's third supplied FORC colormap."""
    colors = [
        (0.00, "#bfc6e8"),
        (0.35, "#e6e9f5"),
        (0.50, "#ffffff"),
        (0.60, "#4cc26b"),
        (0.72, "#f2cf4a"),
        (0.82, "#e84d3c"),
        (0.92, "#c23b8f"),
        (1.00, "#5b1e73"),
    ]
    return LinearSegmentedColormap.from_list("forcme_v3", colors)


def get_forc_cmap(color_scale_version=2):
    """Return a FORCme colormap, defaulting to green-red version 2."""
    registry = {
        1: forc_colormap_v1,
        2: forc_colormap_v2,
        3: forc_colormap_v3,
    }
    return registry.get(int(color_scale_version), forc_colormap_v2)()


def plot_forc(
    result,
    ax=None,
    normalize=True,
    percentile=99.0,
    contours=True,
    cmap=None,
    hc_limits=None,
    hu_limits=None,
):
    """Plot a FORC distribution in coercivity-interaction coordinates.

    Parameters:
        result : ForcResult
            Output from :func:`calculate_forc` or :func:`process_forc`.
        ax : matplotlib.axes.Axes or None
            Existing plot axis.
        normalize : bool
            Divide by the robust absolute color limit.  Normalized plots are
            useful for comparing shape; use ``False`` for quantitative work.
        percentile : float
            Percentile of absolute finite ``rho`` used as the symmetric color
            limit.
        contours : bool
            Overlay positive and negative contour lines.
        cmap : str, matplotlib colormap, or None
            Diverging color map.  ``None`` uses FORCme's green-red version 2
            colormap through :func:`get_forc_cmap`.
        hc_limits, hu_limits : two-element tuple or None
            Optional plot limits in millitesla.

    Returns:
        tuple
            ``(figure, axis, colorbar)``.
    """
    if ax is None:
        figure, ax = plt.subplots(figsize=(7, 5.5))
    else:
        figure = ax.figure
    values = result.rho.copy()
    finite = np.isfinite(values)
    if not finite.any():
        raise ValueError("The FORC result contains no finite values.")
    limit = float(np.nanpercentile(np.abs(values[finite]), percentile))
    if not np.isfinite(limit) or limit <= 0:
        limit = float(np.nanmax(np.abs(values[finite])))
    if normalize and limit > 0:
        values = values / limit
        color_limit = 1.0
        label = "Normalized FORC distribution"
    else:
        color_limit = limit
        label = r"FORC distribution, $\\rho$"
    norm = TwoSlopeNorm(vmin=-color_limit, vcenter=0.0, vmax=color_limit)
    if cmap is None:
        cmap = get_forc_cmap(2)
    image = ax.pcolormesh(
        result.hc * 1e3,
        result.hu * 1e3,
        values,
        shading="auto",
        cmap=cmap,
        norm=norm,
        rasterized=True,
    )
    if contours:
        levels = np.linspace(-color_limit, color_limit, 11)
        levels = levels[np.abs(levels) > color_limit * 1e-12]
        ax.contour(
            result.hc * 1e3,
            result.hu * 1e3,
            values,
            levels=levels,
            colors="k",
            linewidths=0.35,
            alpha=0.55,
        )
    colorbar = figure.colorbar(image, ax=ax, pad=0.02)
    colorbar.set_label(label)
    ax.set_xlabel("Coercivity, $\\mu_0 H_c$ (mT)")
    ax.set_ylabel("Interaction field, $\\mu_0 H_u$ (mT)")
    ax.set_title(f"FORC diagram ({result.method})")
    if hc_limits is not None:
        ax.set_xlim(hc_limits)
    if hu_limits is not None:
        ax.set_ylim(hu_limits)
    return figure, ax, colorbar


def forc_profile(result, axis="hc", value=0.0):
    """Extract the nearest horizontal or vertical profile from a FORC result.

    Parameters:
        result : ForcResult
            Calculated FORC distribution.
        axis : {"hc", "hu"}
            ``"hc"`` returns rho as a function of coercivity at fixed ``hu``.
            ``"hu"`` returns rho as a function of interaction field at fixed
            ``hc``.
        value : float
            Fixed coordinate in tesla.

    Returns:
        tuple of numpy.ndarray
            Coordinate and rho profile arrays.
    """
    if axis == "hc":
        hu_values = result.hu[:, 0]
        row = int(np.nanargmin(np.abs(hu_values - value)))
        return result.hc[row, :].copy(), result.rho[row, :].copy()
    if axis == "hu":
        hc_values = result.hc[0, :]
        column = int(np.nanargmin(np.abs(hc_values - value)))
        return result.hu[:, column].copy(), result.rho[:, column].copy()
    raise ValueError("axis must be 'hc' or 'hu'.")
