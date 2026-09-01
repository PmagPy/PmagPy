"""
MagIC 3-native core for interactive demagnetization analysis.

This module is the UI-independent heart of a fresh-start replacement for
``programs/demag_gui.py``. It reads a MagIC 3 contribution with
``pmagpy.contribution_builder.Contribution``, builds one tidy step table per
specimen (SI units, all three coordinate systems side by side), fits
components with ``pmag.domean``, computes sample/site means with
``pmag.dolnp`` and VGPs with ``pmag.dia_vgp``, and writes results straight
back into MagIC 3 tables using MagIC 3 column names throughout. There is no
2.5 <-> 3.0 translation layer anywhere.

The numerics are deliberately delegated to ``pmagpy.pmag`` so that any UI
built on top (Panel, Dash, marimo, ...) produces results that are identical
to the command-line tools and to the legacy GUI.

Design conventions
------------------
* A specimen's demagnetization steps are identified by their integer position
  ``sequence`` (0..n-1) in the specimen's ordered step table. Component bounds
  are stored as sequence indices, which makes them robust to duplicate
  treatment values and trivially mappable to a click on a plot. SI treatment
  values (T for AF, K for thermal) are derived from the bounding steps on
  export and matched to the nearest step on import.
* Coordinate systems use the MagIC ``dir_tilt_correction`` integers
  (-1 specimen, 0 geographic, 100 tilt-corrected) everywhere.
* All public results use MagIC 3 column names (``dir_dec``, ``dir_mad_free``,
  ``meas_step_min`` ...).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

import pmagpy.pmag as pmag
import pmagpy.contribution_builder as cb

try:
    from pmagpy import version as _pmagpy_version
    PMAGPY_VERSION = _pmagpy_version.version
except Exception:  # pragma: no cover
    PMAGPY_VERSION = "pmagpy"

APP_ID = "pmagpy_directions"          # the app this core serves (PmagPy Directions); written to software_packages
SOFTWARE_TAG = f"{PMAGPY_VERSION}:{APP_ID}"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT = -1, 0, 100
COORD_NAMES = {COORD_SPECIMEN: "specimen",
               COORD_GEOGRAPHIC: "geographic",
               COORD_TILT: "tilt-corrected"}
COORD_CODES = {name: code for code, name in COORD_NAMES.items()}
# DA-DIR ("direction correction") marks specimen-coordinate rows, as the legacy
# Demag GUI and pmag_gui have always written them
COORD_METHOD_CODES = {COORD_SPECIMEN: ["DA-DIR"],
                      COORD_GEOGRAPHIC: ["DA-DIR-GEO"],
                      COORD_TILT: ["DA-DIR-GEO", "DA-DIR-TILT"]}
COORD_COLUMNS = {COORD_SPECIMEN: ("dec_s", "inc_s"),
                 COORD_GEOGRAPHIC: ("dec_g", "inc_g"),
                 COORD_TILT: ("dec_t", "inc_t")}

FIT_TYPES = {"DE-BFL": "best-fit line",
             "DE-BFL-A": "anchored line",
             "DE-BFL-O": "line through origin",
             "DE-BFP": "best-fit plane",
             "DE-FM": "Fisher mean"}
LINE_FITS = ("DE-BFL", "DE-BFL-A", "DE-BFL-O", "DE-FM")

# measurement-level method codes that define a demagnetization step
INCLUDED_STEP_CODES = ("LT-NO", "LT-AF-Z", "LT-T-Z", "LT-M-Z", "LT-LT-Z")
# experiment protocols whose steps must never be treated as demag data
EXCLUDED_PROTOCOL_CODES = ("LP-AN-ARM", "LP-AN-TRM", "LP-ARM-AFD", "LP-ARM2-AFD",
                           "LP-TRM-AFD", "LP-TRM", "LP-TRM-TD", "LP-X", "LP-PI-ARM")
INTENSITY_COLUMNS = ("magn_moment", "magn_volume", "magn_mass", "magn_uncal")
# orientation codes that are never the primary azimuth source
NON_PRIMARY_SO_CODES = ("SO-ASC", "SO-POM")
KELVIN_OFFSET = 273.0


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _is_null(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _to_float(value, default=np.nan) -> float:
    try:
        if _is_null(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _codes(method_codes) -> list[str]:
    if _is_null(method_codes):
        return []
    return [c.strip() for c in str(method_codes).split(":") if c.strip()]


def _join_codes(codes) -> str:
    return ":".join(sorted(set(c for c in codes if c)))


def _natural_key(name: str):
    """Sort key that orders 'sp2' before 'sp10'."""
    import re
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", str(name))]


def display_value(value_si: float, unit: str, treat_type: str = "") -> float:
    """Convert an SI treatment value to display units (mT or degrees C)."""
    if treat_type == "NRM":
        return 0.0
    if unit == "T":
        return value_si * 1e3
    if unit == "K":
        return value_si - KELVIN_OFFSET
    return value_si


def step_label(value_si: float, unit: str, treat_type: str = "") -> str:
    """Human readable label for a treatment step ('NRM', '10 mT', '500°C')."""
    if treat_type == "NRM":
        return "NRM"
    value = display_value(value_si, unit, treat_type)
    if unit == "T":
        return f"{value:g} mT"
    if unit == "K":
        return f"{value:.0f}°C"
    if unit == "J":
        return f"{value:g} J"
    return f"{value:g}"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class Orientation:
    """Sample orientation used for the specimen -> geographic -> tilt chain."""
    sample: str
    azimuth: float = np.nan
    dip: float = np.nan
    bed_dip_direction: float = np.nan
    bed_dip: float = np.nan
    method_codes: list[str] = field(default_factory=list)

    @property
    def has_geographic(self) -> bool:
        return not (np.isnan(self.azimuth) or np.isnan(self.dip))

    @property
    def has_tilt(self) -> bool:
        return self.has_geographic and not (np.isnan(self.bed_dip_direction)
                                            or np.isnan(self.bed_dip))


@dataclass
class SpecimenData:
    """One specimen's demagnetization steps plus hierarchy and orientation."""
    name: str
    sample: str
    site: str
    location: str
    steps: pd.DataFrame
    orientation: Optional[Orientation] = None
    protocol_codes: list[str] = field(default_factory=list)

    @property
    def n_steps(self) -> int:
        return len(self.steps)

    @property
    def nrm(self) -> float:
        return float(self.steps["moment"].iloc[0]) if self.n_steps else np.nan

    @property
    def unit(self) -> str:
        """Dominant step unit ('T' or 'K'); 'T:K' if both protocols present."""
        units = [u for u in self.steps["treat_unit"].unique() if u]
        return ":".join(sorted(units))

    def has_coord(self, coord: int) -> bool:
        dec_col, _ = COORD_COLUMNS[coord]
        return dec_col in self.steps.columns and self.steps[dec_col].notna().any()

    def available_coords(self) -> list[int]:
        return [c for c in (COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT) if self.has_coord(c)]

    def vds(self) -> float:
        """Vector difference sum normalised by NRM (good steps only)."""
        good = self.steps[self.steps["quality"] == "g"]
        if len(good) == 0:
            return np.nan
        cart = cartesian(good, COORD_SPECIMEN)
        diffs = np.linalg.norm(np.diff(cart, axis=0), axis=1)
        return float(diffs.sum() + np.linalg.norm(cart[-1]))


@dataclass
class Component:
    """A directional interpretation of one specimen (a 'fit').

    ``color`` is optional presentation metadata carried through the .redo
    file; user interfaces normally colour components by name instead.
    """
    specimen: str
    name: str = "A"
    imin: int = 0
    imax: int = -1
    fit_type: str = "DE-BFL"
    quality: str = "g"
    color: Optional[str] = None

    def key(self) -> tuple:
        return (self.specimen, self.name)


# ---------------------------------------------------------------------------
# Zijderveld projection semantics (shared by every front end)
# ---------------------------------------------------------------------------
PROJECTIONS = {"ew": "X = East",
               "ns": "X = North",
               "nrm": "X = NRM declination"}


def projection_rotation(spec: "SpecimenData", coord: int, mode: str = "nrm",
                        fit_dec: Optional[float] = None) -> float:
    """Declination mapped onto the Zijderveld x axis for a projection mode."""
    if mode == "ns":
        return 0.0
    if mode == "ew":
        return 90.0
    if mode == "fit" and fit_dec is not None and not np.isnan(fit_dec):
        return float(fit_dec)
    dec_col = COORD_COLUMNS[coord][0]
    return float(spec.steps[dec_col].iloc[0])


def axis_labels(coord: int, mode: str, rotation: float = 0.0) -> dict:
    """Axis-end labels for a Zijderveld diagram.

    Returns a dict with keys ``right``, ``left`` (ends of the x axis),
    ``top_h``/``bottom_h`` (horizontal projection, y axis) and
    ``top_v``/``bottom_v`` (vertical projection). Follows the legacy
    convention that E/S and Down plot towards the bottom.
    """
    if coord == COORD_SPECIMEN:
        if mode == "ns":
            return dict(right="x", left="−x", top_h="−y", bottom_h="y", top_v="−z (up)", bottom_v="z (down)")
        if mode == "ew":
            return dict(right="y", left="−y", top_h="x", bottom_h="−x", top_v="−z (up)", bottom_v="z (down)")
        return dict(right=f"x′ ({rotation:.0f}°)", left="", top_h="", bottom_h="y′", top_v="up", bottom_v="down")
    if mode == "ns":
        return dict(right="N", left="S", top_h="W", bottom_h="E", top_v="Up", bottom_v="Down")
    if mode == "ew":
        return dict(right="E", left="W", top_h="N", bottom_h="S", top_v="Up", bottom_v="Down")
    return dict(right=f"N′ ({rotation:.0f}°)", left="", top_h="", bottom_h="E′", top_v="Up", bottom_v="Down")


@dataclass
class DirectionResult:
    """Result of fitting a Component in one coordinate system (MagIC 3 names)."""
    specimen: str
    dir_comp: str
    dir_tilt_correction: int
    dir_dec: float
    dir_inc: float
    dir_n_measurements: int
    meas_step_min: float
    meas_step_max: float
    meas_step_unit: str
    method_codes: str
    result_quality: str
    fit_type: str
    dir_mad_free: float = np.nan
    dir_dang: float = np.nan
    dir_alpha95: float = np.nan
    center_of_mass: tuple = (0.0, 0.0, 0.0)
    imin: int = 0
    imax: int = 0

    @property
    def direction_type(self) -> str:
        return "p" if self.fit_type == "DE-BFP" else "l"

    def to_record(self) -> dict:
        """MagIC 3 specimens-table columns only."""
        rec = {
            "specimen": self.specimen,
            "dir_comp": self.dir_comp,
            "dir_tilt_correction": self.dir_tilt_correction,
            "dir_dec": round(self.dir_dec, 1),
            "dir_inc": round(self.dir_inc, 1),
            "dir_n_measurements": int(self.dir_n_measurements),
            "meas_step_min": self.meas_step_min,
            "meas_step_max": self.meas_step_max,
            "meas_step_unit": self.meas_step_unit,
            "method_codes": self.method_codes,
            "result_quality": self.result_quality,
            "result_type": "i",
        }
        if not np.isnan(self.dir_mad_free):
            rec["dir_mad_free"] = round(self.dir_mad_free, 1)
        if not np.isnan(self.dir_dang):
            rec["dir_dang"] = round(self.dir_dang, 1)
        if not np.isnan(self.dir_alpha95):
            rec["dir_alpha95"] = round(self.dir_alpha95, 1)
        return rec


# ---------------------------------------------------------------------------
# Geometry helpers (UI independent)
# ---------------------------------------------------------------------------
def cartesian(steps: pd.DataFrame, coord: int = COORD_SPECIMEN, normalize: bool = True) -> np.ndarray:
    """Return an (n, 3) array of x, y, z for the steps in the given coordinates.

    Args:
        steps: step table (or a slice of one) from ``SpecimenData.steps``.
        coord: -1, 0 or 100 (MagIC dir_tilt_correction code).
        normalize: divide moments by the NRM (first step of the full table),
            so that vectors are dimensionless. When ``steps`` is a slice the
            ``moment_norm`` column is used, which was normalised on load.

    Returns:
        ndarray of shape (n, 3); rows are NaN where the coordinate system is
        unavailable.
    """
    dec_col, inc_col = COORD_COLUMNS[coord]
    if dec_col not in steps.columns:
        return np.full((len(steps), 3), np.nan)
    mags = steps["moment_norm"].values if normalize else steps["moment"].values
    di = np.column_stack([steps[dec_col].values, steps[inc_col].values, mags])
    if len(di) == 0:
        return np.zeros((0, 3))
    return np.asarray(pmag.dir2cart(di), dtype=float).reshape(-1, 3)


def rotate_about_vertical(cart: np.ndarray, rotation_dec: float) -> np.ndarray:
    """Rotate cartesian vectors so that declination ``rotation_dec`` maps to x."""
    if rotation_dec == 0 or len(cart) == 0:
        return cart
    theta = np.radians(rotation_dec)
    c, s = np.cos(theta), np.sin(theta)
    rot = np.array([[c, s, 0.0], [-s, c, 0.0], [0.0, 0.0, 1.0]])
    return cart @ rot.T


def zijderveld_xy(steps: pd.DataFrame, coord: int = COORD_SPECIMEN,
                  rotation_dec: float = 0.0) -> pd.DataFrame:
    """Orthogonal (Zijderveld) projection of a specimen's steps.

    Follows the convention of the legacy Demag GUI: ``x`` is the (optionally
    rotated) north component, ``y_h`` is minus east (horizontal projection,
    red circles) and ``y_v`` is minus down (vertical projection, blue squares),
    so that east and down both plot toward the bottom of the diagram.

    Returns:
        DataFrame with columns sequence, label, quality, x, y_h, y_v.
    """
    cart = rotate_about_vertical(cartesian(steps, coord), rotation_dec)
    out = pd.DataFrame({
        "sequence": steps["sequence"].values,
        "label": steps["label"].values,
        "quality": steps["quality"].values,
        "x": cart[:, 0],
        "y_h": -cart[:, 1],
        "y_v": -cart[:, 2],
    })
    return out


def equal_area_xy(dec, inc) -> tuple[np.ndarray, np.ndarray]:
    """Equal-area (Schmidt) projection coordinates for arrays of dec/inc."""
    dec = np.atleast_1d(np.asarray(dec, dtype=float))
    inc = np.atleast_1d(np.asarray(inc, dtype=float))
    if len(dec) == 0:
        return np.array([]), np.array([])
    xy = np.asarray(pmag.dimap_V(dec, inc), dtype=float).reshape(-1, 2)
    return xy[:, 0], xy[:, 1]


def great_circle_xy(pole_dec: float, pole_inc: float, npts: int = 181) -> tuple[np.ndarray, np.ndarray]:
    """Equal-area coordinates of the great circle whose pole is (dec, inc).

    Only the lower-hemisphere half of the circle is returned so that the
    trace can be drawn as one continuous line.
    """
    decs, incs = pmag.circ(pole_dec, pole_inc, 90.0, npts=npts)
    decs, incs = np.asarray(decs), np.asarray(incs)
    keep = incs >= 0
    if keep.sum() == 0:
        keep = ~keep
        incs = -incs
        decs = (decs + 180.0) % 360.0
    return equal_area_xy(decs[keep], incs[keep])


def fit_line_segment(result: DirectionResult, spec: SpecimenData, coord: int,
                     rotation_dec: float = 0.0) -> Optional[pd.DataFrame]:
    """End points of a best-fit line for drawing on a Zijderveld diagram.

    The line passes through the centre of mass of the fitted steps (or the
    origin for anchored fits) along the fitted direction; its extent is the
    projection of the bounding steps onto that line.

    Returns:
        DataFrame with two rows (x, y_h, y_v) or None for plane fits.
    """
    if result.direction_type != "l":
        return None
    cart = cartesian(spec.steps, coord)
    sub = cart[result.imin:result.imax + 1]
    good = spec.steps["quality"].values[result.imin:result.imax + 1] == "g"
    sub = sub[good]
    if len(sub) == 0:
        return None
    direction = np.asarray(pmag.dir2cart([result.dir_dec, result.dir_inc, 1.0]), dtype=float).ravel()
    centre = np.asarray(result.center_of_mass, dtype=float)
    if result.fit_type in ("DE-BFL-A", "DE-BFL-O"):
        centre = np.zeros(3)
    t = (sub - centre) @ direction
    ends = np.vstack([centre + t.min() * direction, centre + t.max() * direction])
    if result.fit_type == "DE-BFL-O":
        ends = np.vstack([np.zeros(3), centre + t.max() * direction])
    ends = rotate_about_vertical(ends, rotation_dec)
    return pd.DataFrame({"x": ends[:, 0], "y_h": -ends[:, 1], "y_v": -ends[:, 2]})


def plane_best_fit_vectors(records) -> List[Tuple[float, float]]:
    """Best-fit vectors of the planes in a set of directions (McFadden & McElhinny, 1988).

    Combining lines and planes places every plane's direction at the point of
    its great circle that lies closest to the mean of the whole set, found by
    the iteration of MM88. ``pmag.dolnp`` computes those points to reach the
    mean but does not report them; this repeats its set-up to return them.

    Args:
        records: dicts as ``mean_directions`` builds them — ``dir_dec``,
            ``dir_inc`` and ``dir_type`` ('l' or 'p') — for one group.

    Returns:
        (dec, inc) per plane, in the order the planes appear in ``records``;
        empty when the set holds no plane. A set of planes alone has no mean
        to converge on: MM88 starts the iteration from a fixed direction, and
        that is what pmag.dolnp does for the mean as well.
    """
    if not records:
        return []
    _, n_lines, poles, n_planes, lines_sum = pmag.process_data_for_mean(records, "dir_type")
    if not n_planes:
        return []
    if n_lines == 0:
        start = list(np.asarray(pmag.dir2cart([180., -45., 1.]), dtype=float).ravel())
    else:
        norm = float(np.sqrt(sum(c ** 2 for c in lines_sum)))
        start = [c / norm for c in lines_sum]
    # calculate_best_fit_vectors returns one vector per pole, in the order of `poles`
    vectors = pmag.calculate_best_fit_vectors(list(poles), list(lines_sum), start, n_planes)
    out = []
    for vec in vectors:
        dec, inc = pmag.cart2dir(list(vec))[:2]
        out.append((float(dec), float(inc)))
    return out


def polarity_axis(directions) -> list:
    """The common axis of a set of directions (or VGPs): the principal eigenvector of the
    orientation tensor, pointed towards the majority."""
    block = [[float(d), float(i)] for d, i in directions]
    if not block:
        return [0.0, 90.0]
    if len(block) == 1:
        return block[0]
    principal = pmag.doprinc(block)
    ref = [float(principal["dec"]), float(principal["inc"])]
    angles = np.array([pmag.angle([d, i], ref)[0] for d, i in block], dtype=float)
    if (angles > 90).sum() * 2 > len(block):
        ref = [(ref[0] + 180.0) % 360.0, -ref[1]]
    return ref


def unify_polarity(directions, reference=None) -> tuple[list, np.ndarray]:
    """Flip directions (dec/inc or VGP lon/lat pairs) to a common polarity.

    The reference axis is the principal eigenvector of the orientation
    tensor (``pmag.doprinc``), which — unlike a Fisher mean of a mixed
    polarity set — does not depend on how many directions are reversed. The
    axis is pointed towards the majority of the directions and every
    direction more than 90° from it is replaced by its antipode.

    Args:
        directions: iterable of (dec, inc) or (lon, lat) pairs in degrees.
        reference: optional (dec, inc) to use instead of the principal axis.

    Returns:
        (unified list of [dec, inc], boolean array of which entries were flipped)
    """
    block = [[float(d), float(i)] for d, i in directions]
    if len(block) == 0:
        return [], np.zeros(0, dtype=bool)
    ref = [float(v) for v in (reference if reference is not None else polarity_axis(block))]
    angles = np.array([pmag.angle([d, i], ref)[0] for d, i in block], dtype=float)
    flipped = angles > 90
    unified = [[(d + 180.0) % 360.0, -i] if f else [d, i] for (d, i), f in zip(block, flipped)]
    return unified, flipped


def fisher_means_by_polarity(directions) -> List[dict]:
    """A Fisher mean of each polarity mode, the comparison a reversal test rests on.

    The modes are separated about the principal direction
    (``pmag.separate_directions``), so the split does not depend on how many
    directions are reversed, and each is then averaged on its own — which a
    mean of the set brought to one polarity hides.

    The modes are reported largest first and are *not* labelled normal and
    reversed: which one is which follows from the polarity of its VGP (see
    ``vgp_polarity``), not from the directions themselves — in the southern
    hemisphere normal polarity is the steeply negative mode. The Poles tab
    settles that from the site coordinates.

    Args:
        directions: iterable of (dec, inc) pairs in degrees.

    Returns:
        One dict per mode present, largest first, with MagIC style keys plus
        ``mode`` (1 or 2). A mode of a single direction carries no statistics.
    """
    block = [[float(d), float(i)] for d, i in directions]
    if not block:
        return []
    if len(block) == 1:
        return [{"mode": 1, "dir_dec": block[0][0], "dir_inc": block[0][1], "dir_n_specimens": 1}]
    modes = [[list(d) for d in mode] for mode in pmag.separate_directions(block)]
    out = []
    for mode in sorted(modes, key=len, reverse=True):
        if not len(mode):
            continue
        rec = {"mode": len(out) + 1, "dir_n_specimens": len(mode)}
        if len(mode) == 1:
            rec.update({"dir_dec": mode[0][0], "dir_inc": mode[0][1]})
        else:
            mean = pmag.fisher_mean(mode)
            rec.update({"dir_dec": float(mean["dec"]), "dir_inc": float(mean["inc"]),
                        "dir_alpha95": float(mean["alpha95"]), "dir_k": float(mean["k"]),
                        "dir_r": float(mean["r"])})
        out.append(rec)
    return out


def bingham_mean(directions) -> dict:
    """The Bingham mean of a set of directions, with its confidence ellipse.

    Bingham statistics describe an axial distribution, so — unlike Fisher —
    the result does not depend on the polarity the directions are recorded
    in, and the confidence region is an ellipse (Eta, Zeta) rather than a
    circle. MagIC has no columns for those semi-axes, so this is reported in
    the application rather than written to the tables.

    Args:
        directions: iterable of (dec, inc) pairs in degrees; at least two.

    An axis has two ends and the eigen decomposition returns whichever one it
    lands on — for a site of steeply upward directions that is as often the
    downward end, which would plot the mean across the net from the very
    directions it averages. The axis is therefore pointed at the data, the
    same way ``polarity_axis`` points the principal direction at the majority.

    Returns:
        dict with ``dir_dec``, ``dir_inc``, ``dir_n_specimens`` and the
        ellipse (``eta``, ``eta_dec``, ``eta_inc``, ``zeta``, ``zeta_dec``,
        ``zeta_inc``), or an empty dict when there is too little data.
    """
    block = [[float(d), float(i)] for d, i in directions]
    if len(block) < 2:
        return {}
    b = pmag.dobingham(block)
    # the ellipse comes from an eigen decomposition that numpy may hand back as
    # complex with a zero imaginary part; take the real part rather than let the
    # cast warn
    real = lambda key: float(np.real(b[key]))                      # noqa: E731
    dec, inc = real("dec"), real("inc")
    if pmag.angle([dec, inc], polarity_axis(block))[0] > 90:
        dec, inc = (dec + 180.0) % 360.0, -inc
    return {"dir_dec": dec, "dir_inc": inc,
            "dir_n_specimens": int(b["n"]),
            "eta": real("Eta"), "eta_dec": real("Edec"), "eta_inc": real("Einc"),
            "zeta": real("Zeta"), "zeta_dec": real("Zdec"), "zeta_inc": real("Zinc")}


def antipode(dec, inc) -> tuple[float, float]:
    """The antipode of a direction or of a VGP (lon/lat)."""
    return (float(dec) + 180.0) % 360.0, -float(inc)


def _unify_records(recs: list, common_polarity: bool = True, flip: bool = False,
                   reference=None) -> tuple[list, float]:
    """Bring dir_dec/dir_inc records to a common polarity and optionally invert the set.

    Args:
        reference: axis to unify about (default: the records' own principal axis);
            a study-wide axis keeps every location's polarity choice consistent.

    Returns:
        (records, percentage of records that were inverted relative to their input)
    """
    block = [[r["dir_dec"], r["dir_inc"]] for r in recs]
    flipped = np.zeros(len(block), dtype=bool)
    if common_polarity and (len(block) > 1 or reference is not None):
        block, flipped = unify_polarity(block, reference)
    if flip:
        block = [list(antipode(d, i)) for d, i in block]
        flipped = ~flipped
    out = []
    for r, (d, i) in zip(recs, block):
        r = dict(r)
        r["dir_dec"], r["dir_inc"] = d, i
        out.append(r)
    return out, float(100.0 * flipped.mean()) if len(block) else 0.0


def paleolatitude(pole_lon: float, pole_lat: float, site_lon: float, site_lat: float) -> float:
    """Paleolatitude of a site given a (north) pole: 90° minus the site–pole distance."""
    return 90.0 - float(pmag.angle([site_lon, site_lat], [pole_lon, pole_lat])[0])


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def _first_valid(series: pd.Series):
    """First non-null value of a Series or None."""
    valid = series.dropna()
    valid = valid[valid.astype(str).str.strip() != ""]
    return valid.iloc[0] if len(valid) else None


def build_orientation(samp_df: Optional[pd.DataFrame], sample: str) -> Optional[Orientation]:
    """Pick the orientation row for a sample from a MagIC 3 samples table.

    MagIC 3 tables may hold several rows per sample (orientation rows, result
    rows). Rows flagged ``orientation_quality == 'b'`` are skipped, the first
    row with both azimuth and dip provides the geographic transform, and
    bedding is taken from the same row or, failing that, from any row of the
    sample that carries it.
    """
    if samp_df is None or "sample" not in samp_df.columns:
        return None
    rows = samp_df[samp_df["sample"].astype(str) == str(sample)]
    if len(rows) == 0:
        return None
    if "orientation_quality" in rows.columns:
        rows = rows[rows["orientation_quality"].astype(str).str.strip() != "b"]
    if len(rows) == 0:
        return None
    orient = Orientation(sample=str(sample))
    if "azimuth" in rows.columns and "dip" in rows.columns:
        az = pd.to_numeric(rows["azimuth"], errors="coerce")
        dip = pd.to_numeric(rows["dip"], errors="coerce")
        ok = az.notna() & dip.notna()
        if ok.any():
            row = rows[ok].iloc[0]
            orient.azimuth = float(az[ok].iloc[0])
            orient.dip = float(dip[ok].iloc[0])
            so_codes = [c for c in _codes(row.get("method_codes", ""))
                        if c.startswith("SO-") and c not in NON_PRIMARY_SO_CODES]
            orient.method_codes = so_codes
            for col, attr in (("bed_dip_direction", "bed_dip_direction"), ("bed_dip", "bed_dip")):
                if col in rows.columns:
                    val = _to_float(row.get(col))
                    if np.isnan(val):
                        val = _to_float(_first_valid(pd.to_numeric(rows[col], errors="coerce")))
                    setattr(orient, attr, val)
    return orient


def _intensity_column(meas_df: pd.DataFrame) -> Optional[str]:
    for col in INTENSITY_COLUMNS:
        if col in meas_df.columns and pd.to_numeric(meas_df[col], errors="coerce").notna().any():
            return col
    return None


def build_step_table(spec_meas: pd.DataFrame, intensity_col: str, warnings: Optional[list] = None) -> pd.DataFrame:
    """Turn a specimen's measurement rows into an ordered demag step table.

    Rows are kept in file order. Only zero-field demagnetization steps are
    retained (see ``INCLUDED_STEP_CODES`` / ``EXCLUDED_PROTOCOL_CODES``), so
    in-field Thellier steps, pTRM checks, ARM/TRM acquisition and anisotropy
    experiments are dropped. Steps without an intensity are skipped (and
    reported in ``warnings``) rather than given a made-up moment.
    """
    records = []
    for pos, row in spec_meas.iterrows():
        codes = _codes(row.get("method_codes", ""))
        if any(c in EXCLUDED_PROTOCOL_CODES for c in codes):
            continue
        if not any(c in INCLUDED_STEP_CODES for c in codes):
            continue
        dec = _to_float(row.get("dir_dec"))
        inc = _to_float(row.get("dir_inc"))
        if np.isnan(dec) or np.isnan(inc):
            continue
        moment = _to_float(row.get(intensity_col))
        if np.isnan(moment):
            if warnings is not None:
                warnings.append(f"{row.get('specimen', '?')}: measurement {row.get('measurement', pos)} "
                                f"has no {intensity_col}; step skipped")
            continue
        if "LT-NO" in codes:
            treat_type, value, unit = "NRM", 0.0, ""
        elif "LT-AF-Z" in codes:
            treat_type, value, unit = "AF", _to_float(row.get("treat_ac_field"), 0.0), "T"
        elif "LT-T-Z" in codes or "LT-LT-Z" in codes:
            treat_type, value, unit = "T", _to_float(row.get("treat_temp"), KELVIN_OFFSET), "K"
        elif "LT-M-Z" in codes:
            power = _to_float(row.get("treat_mw_power"))
            time = _to_float(row.get("treat_mw_time"))
            value = power * time if not (np.isnan(power) or np.isnan(time)) else _to_float(row.get("treat_step_num"), 0.0)
            treat_type, unit = "MW", "J"
        else:
            continue
        quality = "b" if str(row.get("quality", "g")).strip() == "b" else "g"
        records.append({
            "meas_pos": int(pos),
            "measurement": str(row.get("measurement", "")),
            "experiment": str(row.get("experiment", "")),
            "treat_type": treat_type,
            "treat_value": value,
            "treat_unit": unit,
            "dec_s": dec,
            "inc_s": inc,
            "moment": moment,
            "csd": _to_float(row.get("dir_csd")),
            "quality": quality,
            "method_codes": ":".join(codes),
        })
    steps = pd.DataFrame(records)
    if len(steps) == 0:
        return steps
    # Duplicate rows (repeated NRM measurements from a second experiment,
    # re-measured steps) are deliberately kept: the legacy GUI keeps them, the
    # published interpretations count them, and the step logger shows them so
    # that the analyst can flag one of them bad if that is what they want.
    # NRM steps inherit the unit of the following demag protocol
    units = steps["treat_unit"].replace("", np.nan).bfill().ffill().fillna("")
    steps["treat_unit"] = units
    steps.insert(0, "sequence", np.arange(len(steps)))
    steps["label"] = [step_label(v, u, t) for v, u, t in
                      zip(steps["treat_value"], steps["treat_unit"], steps["treat_type"])]
    steps["treat_display"] = [display_value(v, u, t) for v, u, t in
                              zip(steps["treat_value"], steps["treat_unit"], steps["treat_type"])]
    nrm = steps["moment"].iloc[0]
    steps["moment_norm"] = steps["moment"] / nrm if nrm else steps["moment"]
    return steps


def add_transformed_coordinates(steps: pd.DataFrame, orientation: Optional[Orientation]) -> pd.DataFrame:
    """Add dec_g/inc_g and dec_t/inc_t columns using pmag.dogeo_V / dotilt_V."""
    steps = steps.copy()
    for col in ("dec_g", "inc_g", "dec_t", "inc_t"):
        steps[col] = np.nan
    if orientation is None or not orientation.has_geographic or len(steps) == 0:
        return steps
    n = len(steps)
    geo_in = np.column_stack([steps["dec_s"].values, steps["inc_s"].values,
                              np.full(n, orientation.azimuth), np.full(n, orientation.dip)])
    dec_g, inc_g = pmag.dogeo_V(geo_in)
    steps["dec_g"], steps["inc_g"] = np.asarray(dec_g, float), np.asarray(inc_g, float)
    if orientation.has_tilt:
        tilt_in = np.column_stack([steps["dec_g"].values, steps["inc_g"].values,
                                   np.full(n, orientation.bed_dip_direction), np.full(n, orientation.bed_dip)])
        dec_t, inc_t = pmag.dotilt_V(tilt_in)
        steps["dec_t"], steps["inc_t"] = np.asarray(dec_t, float), np.asarray(inc_t, float)
    return steps


def _protocol_codes(steps: pd.DataFrame) -> list[str]:
    codes = []
    types = set(steps["treat_type"])
    if "AF" in types:
        codes.append("LP-DIR-AF")
    if "T" in types:
        codes.append("LP-DIR-T")
    if "MW" in types:
        codes.append("LP-DIR-M")
    return codes


_DATA_MODEL = {}


def _data_model(offline: bool = True):
    """The MagIC 3 data model, parsed once per process.

    With ``offline`` the bundled copies of the data model *and* of the controlled
    vocabularies are used (``pmag_env.set_env.OFFLINE``), so loading a directory
    never waits on earthref.org — the vocabulary fetch otherwise runs once per
    process with several 3-second timeouts.
    """
    if offline not in _DATA_MODEL:
        from pmagpy import data_model3
        if offline:
            try:
                from pmag_env import set_env
                set_env.OFFLINE = True
            except ImportError:  # pragma: no cover
                pass
        _DATA_MODEL[offline] = data_model3.DataModel(offline=offline)
    return _DATA_MODEL[offline]


# ---------------------------------------------------------------------------
# Export policy helpers (MagIC 3 tables)
# ---------------------------------------------------------------------------
# MagIC method codes: DE-DI = "pole latitude and longitude calculation from mean
# declination-inclination" (a site VGP), DE-VGP = "pole latitude and longitude
# calculation from mean VGP" (a paleomagnetic pole averaged from site VGPs)
VGP_CODE = "DE-DI"
POLE_CODE = "DE-VGP"
PCA_CODE = "LP-DC4"        # IAGA DC4: principal component analysis (written to means built from PCA fits)


def vgp_polarity(vgp_lat: float) -> str:
    """MagIC ``dir_polarity`` from a VGP latitude, as the legacy Demag GUI assigned it:
    within 55° of the north pole 'n', within 55° of the south pole 'r', else 't'."""
    if vgp_lat is None or np.isnan(vgp_lat):
        return ""
    colat = 90.0 - float(vgp_lat)
    return "n" if colat <= 55.0 else ("r" if colat >= 125.0 else "t")

# columns that hold results rather than descriptive metadata; everything else
# of an existing row is inherited by the row that replaces it
_RESULT_PREFIXES = ("dir_", "vgp_", "pole_", "int_", "aniso_", "hyst_", "rem_", "meas_", "vadm", "vdm", "pdm",
                    "padm", "paleolat", "critical_temp", "susc_", "curie", "magn_", "treat_", "result_")
_RESULT_COLUMNS = {"method_codes", "citations", "software_packages", "description", "analysts", "experiments",
                   "measurements", "criteria", "result_names", "timestamp"}


def is_metadata_column(column: str) -> bool:
    return not (column.startswith(_RESULT_PREFIXES) or column in _RESULT_COLUMNS)


def carry_metadata(new: pd.DataFrame, existing: Optional[pd.DataFrame], key: str,
                   columns: Optional[tuple] = None) -> pd.DataFrame:
    """Fill empty metadata cells of ``new`` rows from existing rows with the same key.

    Args:
        new: rows about to be written (must have column ``key``).
        existing: the table as read from the contribution (may be None).
        key: 'specimen', 'sample', 'site' or 'location'.
        columns: restrict to these columns (default: every metadata column).
    """
    if existing is None or len(new) == 0 or key not in new.columns or key not in existing.columns:
        return new
    cols = [c for c in existing.columns if c != key and is_metadata_column(c)]
    if columns is not None:
        cols = [c for c in cols if c in columns]
    if not cols:
        return new
    source = existing[[key] + cols].copy()
    source[key] = source[key].astype(str)
    for c in cols:
        source[c] = source[c].where(source[c].astype(str).str.strip().replace("nan", "") != "")
    firsts = source.groupby(key, sort=False)[cols].first()
    new = new.copy()
    keys = new[key].astype(str)
    for c in cols:
        fill = keys.map(firsts[c])
        if c not in new.columns:
            new[c] = fill
        else:
            empty = new[c].isna() | (new[c].astype(str).str.strip() == "")
            new[c] = new[c].where(~empty, fill)
    return new


def merge_results(existing: Optional[pd.DataFrame], new: pd.DataFrame, key: str, owned) -> pd.DataFrame:
    """Replace the directional rows of the entities the app owns; keep everything else.

    ``owned`` are the entity names (specimens, samples ...) the app has
    measurement data for: their old directional rows are dropped whether or
    not a new result exists (a deleted interpretation must disappear), and an
    entity left without any row keeps one metadata-only row so that the
    table hierarchy stays intact.
    """
    if existing is None or len(existing) == 0:
        return new
    if key not in existing.columns:
        return pd.concat([existing, new], ignore_index=True, sort=False)
    owned = set(str(o) for o in owned)
    names = existing[key].astype(str)
    # a directional result has a direction; rows that merely cite a fit code
    # count too unless they hold an intensity result (paleointensity rows carry
    # DE-BFL for the direction of the NRM segment and must survive)
    directional = pd.Series(False, index=existing.index)
    if "dir_dec" in existing.columns:
        directional |= pd.to_numeric(existing["dir_dec"], errors="coerce").notna()
    codes = existing["method_codes"].fillna("").astype(str) if "method_codes" in existing.columns else None
    if codes is not None:
        directional |= codes.str.contains("LP-DIR|DE-BF|DE-FM|DE-DI|DE-VGP", regex=True)
    # paleointensity rows carry the direction of the NRM segment (dir_dec, DE-BFL)
    # but are intensity results: they are never replaced by a demag interpretation
    intensity = pd.Series(False, index=existing.index)
    for col in ("int_abs", "int_rel", "int_abs_sigma"):
        if col in existing.columns:
            intensity |= pd.to_numeric(existing[col], errors="coerce").notna()
    if codes is not None:
        intensity |= codes.str.contains("LP-PI", regex=False)
    directional &= ~intensity
    keep = existing[~(directional & names.isin(owned))]
    new_names = set(new[key].astype(str)) if len(new) and key in new.columns else set()
    gone = (owned & set(names)) - set(keep[key].astype(str)) - new_names
    if gone:
        meta_cols = [c for c in existing.columns if c == key or is_metadata_column(c)]
        lost = existing[names.isin(gone)][meta_cols].copy()
        lost[key] = lost[key].astype(str)
        stub = lost.groupby(key, sort=False, as_index=False).first()
        keep = pd.concat([keep, stub], ignore_index=True, sort=False)
    keep = keep.dropna(axis=1, how="all")
    return pd.concat([keep, new], ignore_index=True, sort=False)


def trim_to_model(df: pd.DataFrame, table: str, warnings: Optional[list] = None) -> pd.DataFrame:
    """Drop columns that are not part of the MagIC 3 data model for ``table``."""
    if len(df) == 0:
        return df
    known = set(_data_model(True).dm[table].index)
    extra = [c for c in df.columns if c not in known]
    if extra and warnings is not None:
        warnings.append(f"{table}: dropped non-MagIC columns {extra}")
    return df.drop(columns=extra)


def validate_directory(dir_path: str, tables=("specimens", "samples", "sites", "locations", "measurements")) -> dict:
    """Run pmagpy's MagIC validator on the tables in a directory.

    Returns:
        dict table -> None when the table passes (or is absent), otherwise a
        dict with ``bad_rows``, ``bad_cols``, ``missing_cols`` and
        ``failing_items`` as produced by ``validate_upload3.validate_table``.
    """
    import warnings as _warnings
    from pmagpy import validate_upload3
    present = [t for t in tables if os.path.exists(os.path.join(dir_path, t + ".txt"))]
    con = cb.Contribution(dir_path, read_tables=present, dmodel=_data_model(True))
    report = {}
    for table in present:
        if table not in con.tables:
            continue
        with _warnings.catch_warnings():          # the validator's pandas chatter is not ours to fix here
            _warnings.simplefilter("ignore")
            fail = validate_upload3.validate_table(con, table, output_dir=dir_path)
        if not fail:
            report[table] = None
        else:
            _, bad_rows, bad_cols, missing_cols, missing_groups, failing_items = fail
            report[table] = {"bad_rows": list(bad_rows), "bad_cols": list(bad_cols),
                             "missing_cols": list(missing_cols), "missing_groups": list(missing_groups),
                             "failing_items": failing_items}
    return report


# ---------------------------------------------------------------------------
# The session object
# ---------------------------------------------------------------------------
class DemagData:
    """A MagIC 3 contribution prepared for interactive demag interpretation.

    Attributes:
        contribution: the underlying ``cb.Contribution``.
        specimens: ordered dict of specimen name -> ``SpecimenData``.
        hierarchy: DataFrame indexed by specimen with sample, site, location.
        site_coords: dict site -> (lat, lon) from the sites table.
        components: list of ``Component`` interpretations.
    """

    def __init__(self, contribution: cb.Contribution):
        self.contribution = contribution
        self.specimens: dict[str, SpecimenData] = {}
        self.components: list[Component] = []
        self.warnings: list[str] = []
        self._fit_cache: dict = {}
        self._build()

    def invalidate(self) -> None:
        """Drop cached fits (call after editing step flags or step tables directly)."""
        self._fit_cache.clear()

    # ----- construction ----------------------------------------------------
    @classmethod
    def from_directory(cls, directory: str, meas_file: str = "measurements.txt",
                       offline_data_model: bool = True) -> "DemagData":
        """Read measurements/specimens/samples/sites/locations from a directory.

        Args:
            offline_data_model: use the MagIC data model bundled with pmagpy
                instead of fetching it from EarthRef (faster, works offline).
        """
        con = cb.Contribution(directory, custom_filenames={"measurements": meas_file},
                              read_tables=["measurements", "specimens", "samples", "sites", "locations"],
                              dmodel=_data_model(offline_data_model))
        return cls(con)

    def _table(self, name: str) -> Optional[pd.DataFrame]:
        table = self.contribution.tables.get(name)
        if table is None or table.df is None or len(table.df) == 0:
            return None
        return table.df.reset_index(drop=True)

    def _build(self) -> None:
        meas = self._table("measurements")
        if meas is None:
            raise ValueError("Contribution has no measurements table")
        if "method_codes" not in meas.columns or "specimen" not in meas.columns:
            raise ValueError("measurements table needs 'specimen' and 'method_codes' columns")
        intensity_col = _intensity_column(meas)
        if intensity_col is None:
            raise ValueError("measurements table needs one of %s" % (INTENSITY_COLUMNS,))
        self.intensity_column = intensity_col
        meas = meas.copy()
        meas["specimen"] = meas["specimen"].astype(str)

        spec_df, samp_df = self._table("specimens"), self._table("samples")
        site_df, loc_df = self._table("sites"), self._table("locations")
        self.hierarchy = self._build_hierarchy(meas, spec_df, samp_df, site_df)
        self.site_coords = self._build_site_coords(site_df, samp_df)

        for name, spec_meas in meas.groupby("specimen", sort=False):
            steps = build_step_table(spec_meas, intensity_col, self.warnings)
            if len(steps) < 2:
                continue
            sample, site, location = self.hierarchy.loc[name, ["sample", "site", "location"]]
            orientation = build_orientation(samp_df, sample) if sample else None
            steps = add_transformed_coordinates(steps, orientation)
            self.specimens[name] = SpecimenData(name=name, sample=sample, site=site,
                                                location=location, steps=steps,
                                                orientation=orientation,
                                                protocol_codes=_protocol_codes(steps))
        if not self.specimens:
            raise ValueError("No specimens with demagnetization steps found")

    @staticmethod
    def _build_hierarchy(meas, spec_df, samp_df, site_df) -> pd.DataFrame:
        specimens = pd.Index(meas["specimen"].unique(), name="specimen")
        hier = pd.DataFrame(index=specimens, columns=["sample", "site", "location"], dtype=object)

        def lookup(df, key, value):
            if df is None or key not in df.columns or value not in df.columns:
                return {}
            sub = df[[key, value]].dropna()
            sub = sub[sub[value].astype(str).str.strip() != ""]
            return dict(zip(sub[key].astype(str), sub[value].astype(str)))

        spec_to_samp = lookup(meas, "specimen", "sample")
        spec_to_samp.update({k: v for k, v in lookup(spec_df, "specimen", "sample").items()})
        samp_to_site = lookup(meas, "sample", "site")
        samp_to_site.update(lookup(samp_df, "sample", "site"))
        site_to_loc = lookup(meas, "site", "location")
        site_to_loc.update(lookup(site_df, "site", "location"))

        hier["sample"] = [spec_to_samp.get(s, "") for s in specimens]
        hier["site"] = [samp_to_site.get(s, "") for s in hier["sample"]]
        hier["location"] = [site_to_loc.get(s, "") for s in hier["site"]]
        return hier

    @staticmethod
    def _build_site_coords(site_df, samp_df) -> dict:
        coords = {}
        for df, key in ((site_df, "site"), (samp_df, "site")):
            if df is None or not {key, "lat", "lon"} <= set(df.columns):
                continue
            sub = df[[key, "lat", "lon"]].copy()
            sub["lat"] = pd.to_numeric(sub["lat"], errors="coerce")
            sub["lon"] = pd.to_numeric(sub["lon"], errors="coerce")
            sub = sub.dropna()
            for site, grp in sub.groupby(key):
                coords.setdefault(str(site), (float(grp["lat"].mean()), float(grp["lon"].mean())))
        return coords

    # ----- convenience accessors -------------------------------------------
    @property
    def specimen_names(self) -> list[str]:
        return list(self.specimens)

    def coord_coverage(self) -> dict:
        """Fraction of specimens for which each coordinate system is available."""
        n = max(len(self.specimens), 1)
        return {c: sum(sp.has_coord(c) for sp in self.specimens.values()) / n
                for c in (COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT)}

    def default_coord(self, min_fraction: float = 0.5) -> int:
        """The coordinate system to open a dataset in.

        Tilt-corrected when bedding is recorded, geographic when only sample
        orientations are, specimen coordinates otherwise — judged over the
        majority of the specimens (``min_fraction``), so that a handful of
        oriented samples in an otherwise unoriented collection does not set
        the default.
        """
        coverage = self.coord_coverage()
        for coord in (COORD_TILT, COORD_GEOGRAPHIC):
            if coverage[coord] >= min_fraction:
                return coord
        return COORD_SPECIMEN

    def best_coord(self, specimen: str, requested: int) -> int:
        """``requested`` if the specimen supports it, else the next one down the ladder."""
        spec = self.specimens[specimen]
        for coord in [requested] + [c for c in (COORD_GEOGRAPHIC, COORD_SPECIMEN) if c < requested]:
            if spec.has_coord(coord):
                return coord
        return COORD_SPECIMEN

    def specimens_in(self, level: str, name: str) -> list[str]:
        """Specimen names belonging to a sample/site/location."""
        return [s for s in self.specimens if getattr(self.specimens[s], level) == name]

    def names_at(self, level: str) -> list[str]:
        """Unique sample/site/location names that have demag data."""
        seen = []
        for s in self.specimens.values():
            v = getattr(s, level)
            if v not in seen:
                seen.append(v)
        return seen

    # ----- components ------------------------------------------------------
    def components_for(self, specimen: str) -> list[Component]:
        return [c for c in self.components if c.specimen == specimen]

    def component_names(self) -> list[str]:
        names = []
        for c in self.components:
            if c.name not in names:
                names.append(c.name)
        return names

    def add_component(self, specimen: str, name: str, imin: int, imax: int,
                      fit_type: str = "DE-BFL", quality: str = "g", color: Optional[str] = None) -> Component:
        """Create (or replace) a component for a specimen."""
        if specimen not in self.specimens:
            raise KeyError(specimen)
        if fit_type not in FIT_TYPES:
            raise ValueError(f"unknown fit type {fit_type}")
        n = self.specimens[specimen].n_steps
        imin, imax = int(imin) % n, int(imax) % n
        if imin > imax:
            imin, imax = imax, imin
        comp = Component(specimen, str(name), imin, imax, fit_type, quality, color)
        self.components = [c for c in self.components if c.key() != comp.key()]
        self.components.append(comp)
        return comp

    def set_step_quality(self, specimen: str, index: int, quality: str) -> None:
        """Flag one measurement step 'g' or 'b' (kept in memory until measurements are written)."""
        if quality not in ("g", "b"):
            raise ValueError(quality)
        self.specimens[specimen].steps.loc[int(index), "quality"] = quality
        self._fit_cache = {k: v for k, v in self._fit_cache.items() if k[0] != specimen}

    def toggle_step_quality(self, specimen: str, index: int) -> str:
        steps = self.specimens[specimen].steps
        new = "b" if steps.loc[int(index), "quality"] == "g" else "g"
        self.set_step_quality(specimen, index, new)
        return new

    def remove_component(self, comp: Component) -> None:
        self.components = [c for c in self.components if c.key() != comp.key()]

    def clear_components(self, specimen: Optional[str] = None) -> None:
        if specimen is None:
            self.components = []
        else:
            self.components = [c for c in self.components if c.specimen != specimen]

    # ----- bounds <-> SI values -------------------------------------------
    def step_index_for_value(self, specimen: str, value_si: float, unit: str) -> Optional[int]:
        """Nearest step index for an SI treatment value (MagIC meas_step_*)."""
        steps = self.specimens[specimen].steps
        value = _to_float(value_si)
        if np.isnan(value):
            return None
        is_nrm_value = value == 0 or (unit == "K" and abs(value - KELVIN_OFFSET) < 1e-6)
        if is_nrm_value:
            nrm = steps.index[steps["treat_type"] == "NRM"]
            if len(nrm):
                return int(steps.loc[nrm[0], "sequence"])
        cand = steps[(steps["treat_unit"] == unit) & (steps["treat_type"] != "NRM")]
        if len(cand) == 0:
            cand = steps[steps["treat_type"] != "NRM"]
        if len(cand) == 0:
            return None
        diffs = (cand["treat_value"] - value).abs()
        return int(cand.loc[diffs.idxmin(), "sequence"])

    def _si_bound(self, spec: SpecimenData, index: int) -> tuple[float, str]:
        row = spec.steps.iloc[index]
        unit = row["treat_unit"]
        if row["treat_type"] == "NRM":
            return (KELVIN_OFFSET if unit == "K" else 0.0), unit
        return float(row["treat_value"]), unit

    # ----- .redo files (legacy Demag GUI intermediary format) -------------
    # One tab-separated line per fit:
    #   specimen  fit_type  tmin  tmax  name  color  flag
    # with SI bounds (K for thermal, T for AF, 0 for the NRM step) and the
    # currently displayed specimen marked with a "current_" prefix.
    def write_redo(self, path: str, current_specimen: Optional[str] = None) -> str:
        """Write all components to a legacy-compatible .redo file."""
        lines = []
        by_spec = {}
        for c in self.components:
            by_spec.setdefault(c.specimen, []).append(c)
        if current_specimen and current_specimen not in by_spec:
            lines.append(f"current_{current_specimen}")
        for specimen in sorted(by_spec, key=_natural_key):
            spec = self.specimens[specimen]
            for comp in by_spec[specimen]:
                prefix = "current_" if specimen == current_specimen else ""
                bounds = []
                for index in (comp.imin, comp.imax):
                    value, unit = self._si_bound(spec, index)
                    row = spec.steps.iloc[index]
                    if row["treat_type"] == "NRM":
                        bounds.append("0")
                    elif unit == "T":
                        bounds.append("%.2e" % value)
                    elif unit == "K":
                        bounds.append("%.0f" % value)
                    else:
                        bounds.append("%g" % value)
                lines.append("\t".join([prefix + specimen, comp.fit_type, bounds[0], bounds[1],
                                        comp.name, comp.color or "", comp.quality]))
        with open(path, "w") as fh:
            fh.write("\n".join(lines) + ("\n" if lines else ""))
        return path

    def _unit_for_redo_value(self, spec: SpecimenData, value: float) -> str:
        units = [u for u in spec.steps["treat_unit"].unique() if u]
        if len(units) == 1:
            return units[0]
        return "T" if value < 1.0 else "K"   # tesla values are tiny, kelvin values are hundreds

    def read_redo(self, path: str, replace: bool = True) -> tuple[int, Optional[str]]:
        """Load components from a .redo file.

        Returns:
            (number of components loaded, name of the 'current_' specimen if any)
        """
        if replace:
            self.components = []
        current = None
        n_added = 0
        with open(path) as fh:
            for raw in fh.read().splitlines():
                if not raw.strip():
                    continue
                parts = raw.split("\t")
                specimen = parts[0]
                if specimen.startswith("current_"):
                    specimen = specimen[len("current_"):]
                    current = specimen
                if len(parts) < 5 or specimen not in self.specimens:
                    continue
                fit_type = parts[1].strip()
                if fit_type not in FIT_TYPES:
                    continue
                spec = self.specimens[specimen]
                vmin, vmax = _to_float(parts[2]), _to_float(parts[3])
                if np.isnan(vmin) or np.isnan(vmax):
                    continue
                imin = self.step_index_for_value(specimen, vmin, self._unit_for_redo_value(spec, vmin))
                imax = self.step_index_for_value(specimen, vmax, self._unit_for_redo_value(spec, vmax))
                if imin is None or imax is None:
                    continue
                color = parts[5].strip() if len(parts) > 5 and parts[5].strip() else None
                quality = "b" if len(parts) > 6 and parts[6].strip() == "b" else "g"
                self.add_component(specimen, parts[4].strip() or "A", imin, imax, fit_type, quality, color)
                n_added += 1
        return n_added, current

    def load_components_from_specimens_table(self, coord: Optional[int] = None) -> int:
        """Import prior interpretations stored in the contribution's specimens table.

        MagIC 3 stores one row per (specimen, dir_comp, dir_tilt_correction).
        Step bounds are coordinate independent, so each component is taken
        from the first coordinate system that stores it (specimen, then
        geographic, then tilt-corrected) unless ``coord`` restricts the import
        to one system. Rows without a recognised ``DE-*`` fit code or without
        step bounds are ignored, as are paleointensity rows.

        Returns:
            number of components imported.
        """
        spec_df = self._table("specimens")
        if spec_df is None:
            return 0
        needed = {"specimen", "meas_step_min", "meas_step_max", "meas_step_unit", "method_codes"}
        if not needed <= set(spec_df.columns):
            return 0
        rows = spec_df.copy()
        # Only directional results: paleointensity rows also carry meas_step_min/max
        # (the Thellier temperature range) and often a DE-BFL code, but no dir_dec.
        if "dir_dec" in rows.columns:
            rows = rows[pd.to_numeric(rows["dir_dec"], errors="coerce").notna()]
        tilt = pd.to_numeric(rows["dir_tilt_correction"], errors="coerce") if "dir_tilt_correction" in rows.columns \
            else pd.Series(np.nan, index=rows.index)
        if coord is not None:
            rows = rows[(tilt == coord) | tilt.isna()]
        else:
            rank = tilt.map({COORD_SPECIMEN: 0, COORD_GEOGRAPHIC: 1, COORD_TILT: 2}).fillna(3)
            rows = rows.assign(_rank=rank).sort_values("_rank", kind="stable")
        seen = set()
        n_added = 0
        for _, row in rows.iterrows():
            spec = str(row["specimen"])
            if spec not in self.specimens:
                continue
            codes = _codes(row["method_codes"])
            fit_types = [c for c in codes if c in FIT_TYPES]
            if not fit_types or "DE-BLANKET" in codes or any(c.startswith("LP-PI") for c in codes):
                continue
            unit = str(row["meas_step_unit"]).strip()
            imin = self.step_index_for_value(spec, row["meas_step_min"], unit)
            imax = self.step_index_for_value(spec, row["meas_step_max"], unit)
            if imin is None or imax is None:
                continue
            name = row.get("dir_comp") if "dir_comp" in rows.columns else None
            key = (spec, str(name).strip()) if not _is_null(name) else (spec, imin, imax, fit_types[0])
            if key in seen:            # the same component in another coordinate system
                continue
            seen.add(key)
            if _is_null(name):
                # unnamed component: pick the first free letter for this specimen
                taken = {c.name for c in self.components_for(spec)}
                name = next(ch for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if ch not in taken)
            quality = "b" if str(row.get("result_quality", "g")).strip() == "b" else "g"
            self.add_component(spec, str(name), imin, imax, fit_types[0], quality)
            n_added += 1
        return n_added

    # ----- fitting ---------------------------------------------------------
    def _snap_bounds(self, spec: SpecimenData, imin: int, imax: int) -> tuple[int, int]:
        q = spec.steps["quality"].values
        while imin < imax and q[imin] == "b":
            imin += 1
        while imax > imin and q[imax] == "b":
            imax -= 1
        return imin, imax

    def fit(self, comp: Component, coord: int = COORD_SPECIMEN) -> Optional[DirectionResult]:
        """Fit a component with ``pmag.domean`` in the requested coordinates.

        Returns None when the coordinate system is unavailable for the
        specimen or fewer than two good steps fall inside the bounds.
        """
        spec = self.specimens[comp.specimen]
        if not spec.has_coord(coord):
            return None
        key = (comp.specimen, comp.name, comp.imin, comp.imax, comp.fit_type, comp.quality, coord)
        if key in self._fit_cache:
            return self._fit_cache[key]
        result = self._fit_uncached(spec, comp, coord)
        self._fit_cache[key] = result
        return result

    def _fit_uncached(self, spec: SpecimenData, comp: Component, coord: int) -> Optional[DirectionResult]:
        dec_col, inc_col = COORD_COLUMNS[coord]
        imin, imax = self._snap_bounds(spec, comp.imin, comp.imax)
        n_good = int((spec.steps["quality"].values[imin:imax + 1] == "g").sum())
        if imax <= imin or n_good < 2 or (comp.fit_type == "DE-BFP" and n_good < 3):
            return None
        block = spec.steps[["treat_value", dec_col, inc_col, "moment_norm"]].copy()
        block["zi"] = 0
        block["quality"] = spec.steps["quality"].values
        datablock = block.values.tolist()
        try:
            mpars = pmag.domean(datablock, imin, imax, comp.fit_type)
        except Exception as exc:  # numerical failure inside domean
            self.warnings.append(f"{comp.specimen}/{comp.name}: {exc}")
            return None
        if mpars.get("specimen_direction_type") == "Error" or "specimen_dec" not in mpars:
            return None
        (vmin, umin), (vmax, umax) = self._si_bound(spec, imin), self._si_bound(spec, imax)
        unit = umin if umin == umax else f"{umin}:{umax}"
        in_range = spec.steps.iloc[imin:imax + 1]
        codes = set(_protocol_codes(in_range)) | {comp.fit_type} | set(COORD_METHOD_CODES[coord])
        if coord != COORD_SPECIMEN and spec.orientation is not None:
            codes |= set(spec.orientation.method_codes)
        dang = _to_float(mpars.get("specimen_dang"))
        if comp.fit_type in ("DE-FM", "DE-BFP") or dang < 0:
            dang = np.nan
        return DirectionResult(
            specimen=comp.specimen, dir_comp=comp.name, dir_tilt_correction=coord,
            dir_dec=float(mpars["specimen_dec"]), dir_inc=float(mpars["specimen_inc"]),
            dir_n_measurements=int(mpars["specimen_n"]),
            meas_step_min=vmin, meas_step_max=vmax, meas_step_unit=unit,
            method_codes=_join_codes(codes), result_quality=comp.quality,
            fit_type=comp.fit_type,
            dir_mad_free=_to_float(mpars.get("specimen_mad")),
            dir_dang=dang,
            dir_alpha95=_to_float(mpars.get("specimen_alpha95")),
            center_of_mass=tuple(float(v) for v in mpars.get("center_of_mass", (0, 0, 0))),
            imin=imin, imax=imax)

    def fit_all(self, coord: int = COORD_SPECIMEN, specimen: Optional[str] = None) -> list[DirectionResult]:
        comps = self.components if specimen is None else self.components_for(specimen)
        results = [self.fit(c, coord) for c in comps]
        return [r for r in results if r is not None]

    # ----- higher-level means ---------------------------------------------
    def mean_directions(self, level: str = "site", coord: int = COORD_GEOGRAPHIC,
                        component: Optional[str] = None, include_bad: bool = False,
                        over: str = "specimens", common_polarity: bool = True,
                        flip: bool = False) -> pd.DataFrame:
        """Fisher means of lines and planes (McFadden & McElhinny, 1988) per group.

        Args:
            level: 'sample', 'site' or 'location'.
            coord: coordinate system of the specimen directions averaged.
            component: restrict to one dir_comp name (None = each name separately).
            include_bad: include components flagged result_quality 'b'.
            over: 'specimens' averages specimen directions directly; 'samples'
                (for sites) or 'sites' (for locations) averages the means of
                the next level down with a plain Fisher mean.
            common_polarity: at the location level, bring the directions to a
                common polarity about their principal axis before averaging
                (a location typically mixes normal and reversed sites); the
                share of inverted directions is reported as ``reversed_perc``.
                Sample and site means are never unified: mixed polarity within
                a site is something the analyst must see.
            flip: at the location level, report the antipode of the (unified)
                directions — the polarity an analyst wants to report is a
                choice the principal axis cannot make.

        Returns:
            DataFrame with MagIC 3 style columns (``dir_dec``, ``dir_inc``,
            ``dir_alpha95``, ``dir_k``, ``dir_r``, ``dir_n_specimens`` ...) and,
            where site coordinates are known, ``vgp_lat``/``vgp_lon``/``vgp_dp``/``vgp_dm``.
        """
        if level not in ("sample", "site", "location"):
            raise ValueError(level)
        if over != "specimens":
            return self._mean_of_means(level, coord, component, include_bad, over, common_polarity, flip)
        results = self.fit_all(coord)
        rows = []
        for r in results:
            if r.result_quality == "b" and not include_bad:
                continue
            if component is not None and r.dir_comp != component:
                continue
            spec = self.specimens[r.specimen]
            rows.append({"group": getattr(spec, level), "site": spec.site,
                         "location": spec.location, "dir_comp": r.dir_comp,
                         "dir_dec": r.dir_dec, "dir_inc": r.dir_inc,
                         "dir_tilt_correction": coord, "method_codes": r.method_codes,
                         "dir_type": r.direction_type, "specimen": r.specimen})
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        # one polarity axis per component for the whole study, so that every
        # location's mean (and the flip) is reported in the same polarity
        axes = {name: polarity_axis(g[["dir_dec", "dir_inc"]].values) for name, g in df.groupby("dir_comp")} \
            if level == "location" and common_polarity else {}
        out = []
        for (group, comp_name), grp in df.groupby(["group", "dir_comp"], sort=False):
            recs = grp.to_dict("records")
            reversed_perc = 0.0
            if level == "location" and (common_polarity or flip):
                recs, reversed_perc = _unify_records(recs, common_polarity, flip, axes.get(comp_name))
            lnp = pmag.dolnp(recs, "dir_type")
            if not lnp:
                continue
            rec = {level: group, "dir_comp_name": comp_name, "dir_tilt_correction": coord,
                   "reversed_perc": reversed_perc,
                   "dir_dec": _to_float(lnp.get("dec")), "dir_inc": _to_float(lnp.get("inc")),
                   "dir_alpha95": _to_float(lnp.get("alpha95")), "dir_k": _to_float(lnp.get("K")),
                   "dir_r": _to_float(lnp.get("R")),
                   "dir_n_specimens": int(_to_float(lnp.get("n_total"), 0)),
                   "dir_n_specimens_lines": int(_to_float(lnp.get("n_lines"), 0)),
                   "dir_n_specimens_planes": int(_to_float(lnp.get("n_planes"), 0)),
                   "specimens": ":".join(grp["specimen"]),
                   "dir_n_samples": len({self.specimens[sp].sample for sp in grp["specimen"]}),
                   "site": grp["site"].iloc[0], "location": grp["location"].iloc[0]}
            codes = set()
            for mc in grp["method_codes"]:
                codes |= set(_codes(mc))
            codes.add("DE-FM-LP" if rec["dir_n_specimens_planes"] else "DE-FM")
            if any(c.startswith("DE-BFL") for c in codes):
                codes.add(PCA_CODE)
            rec["method_codes"] = _join_codes(codes)
            site_for_vgp = group if level == "site" else rec["site"]
            if level in ("sample", "site") and site_for_vgp in self.site_coords:
                lat, lon = self.site_coords[site_for_vgp]
                a95 = rec["dir_alpha95"] if not np.isnan(rec["dir_alpha95"]) else 0.0
                plon, plat, dp, dm = pmag.dia_vgp(rec["dir_dec"], rec["dir_inc"], a95, lat, lon)
                rec.update({"lat": lat, "lon": lon, "vgp_lat": float(plat), "vgp_lon": float(plon),
                            "vgp_dp": float(dp), "vgp_dm": float(dm)})
            out.append(rec)
        return pd.DataFrame(out)

    def best_fit_vectors(self, coord: int = COORD_GEOGRAPHIC, level: str = "site",
                         include_bad: bool = False) -> dict:
        """Where each plane's direction falls once it is combined with the lines around it.

        A plane fit constrains its direction to a great circle; the level's
        lines-and-planes mean (McFadden & McElhinny, 1988) places it at the
        point of that circle closest to the mean. This is the direction MagIC
        stores as ``dir_bfv_dec`` / ``dir_bfv_inc`` on the specimen, so it is
        resolved per group and component, exactly as the mean is.

        Args:
            coord: coordinate system the directions are taken in.
            level: group the planes are resolved within ('sample', 'site' or
                'location'); the site is what the legacy GUI used.
            include_bad: include components flagged ``result_quality`` 'b'.

        Returns:
            {(specimen, component name): (dec, inc)} for every plane fit that
            a mean could be formed for.
        """
        if level not in ("sample", "site", "location"):
            raise ValueError(level)
        groups: dict = {}
        for r in self.fit_all(coord):
            if r.result_quality == "b" and not include_bad:
                continue
            spec = self.specimens[r.specimen]
            key = (getattr(spec, level), r.dir_comp)
            groups.setdefault(key, []).append(
                {"dir_dec": r.dir_dec, "dir_inc": r.dir_inc, "dir_type": r.direction_type,
                 "dir_tilt_correction": coord, "method_codes": r.method_codes, "specimen": r.specimen})
        out = {}
        for (_, comp_name), recs in groups.items():
            planes = [rec for rec in recs if rec["dir_type"] == "p"]
            if not planes:
                continue
            vectors = plane_best_fit_vectors(recs)
            for rec, (dec, inc) in zip(planes, vectors):
                out[(rec["specimen"], comp_name)] = (dec, inc)
        return out

    def _mean_of_means(self, level, coord, component, include_bad, over, common_polarity=True,
                       flip=False) -> pd.DataFrame:
        lower = {"site": "sample", "location": "site"}.get(level)
        if lower is None or over != lower + "s":
            raise ValueError(f"cannot average {over} into {level} means")
        lower_means = self.mean_directions(lower, coord, component, include_bad, over="specimens")
        if len(lower_means) == 0:
            return lower_means
        parent_of = {}
        for spec in self.specimens.values():
            parent_of[getattr(spec, lower)] = getattr(spec, level)
        lower_means = lower_means.copy()
        lower_means["group"] = lower_means[lower].map(parent_of)
        out = []
        n_col = {"site": "dir_n_samples", "location": "dir_n_sites"}[level]
        axes = {name: polarity_axis(g[["dir_dec", "dir_inc"]].values)
                for name, g in lower_means.groupby("dir_comp_name")} if level == "location" and common_polarity else {}
        for (group, comp_name), grp in lower_means.groupby(["group", "dir_comp_name"], sort=False):
            # A lower-level mean made only of planes is still a plane (its
            # dec/inc is a pole), so it enters the next level as a plane and
            # the lines-and-planes mean of McFadden & McElhinny is used again.
            recs = [{"dir_dec": m["dir_dec"], "dir_inc": m["dir_inc"], "dir_tilt_correction": coord,
                     "dir_type": "l" if int(m.get("dir_n_specimens_lines", 1) or 0) > 0 else "p"}
                    for _, m in grp.iterrows()]
            reversed_perc = 0.0
            if level == "location" and (common_polarity or flip):
                recs, reversed_perc = _unify_records(recs, common_polarity, flip, axes.get(comp_name))
            lnp = pmag.dolnp(recs, "dir_type")
            rec = {level: group, "dir_comp_name": comp_name, "dir_tilt_correction": coord,
                   "reversed_perc": reversed_perc,
                   "dir_dec": _to_float(lnp.get("dec")), "dir_inc": _to_float(lnp.get("inc")),
                   "dir_alpha95": _to_float(lnp.get("alpha95")), "dir_k": _to_float(lnp.get("K")),
                   "dir_r": _to_float(lnp.get("R")), n_col: int(_to_float(lnp.get("n_total"), len(recs))),
                   "dir_n_specimens_lines": int(_to_float(lnp.get("n_lines"), 0)),
                   "dir_n_specimens_planes": int(_to_float(lnp.get("n_planes"), 0)),
                   "dir_n_specimens": int(grp["dir_n_specimens"].sum()),
                   lower + "s": ":".join(grp[lower].astype(str)),
                   "location": grp["location"].iloc[0] if "location" in grp else group,
                   "method_codes": _join_codes(set(c for mc in grp["method_codes"] for c in _codes(mc))
                                               | {"DE-FM-LP" if any(r["dir_type"] == "p" for r in recs) else "DE-FM"})}
            if level == "site":
                rec["site"] = group
                if group in self.site_coords:
                    lat, lon = self.site_coords[group]
                    a95 = rec["dir_alpha95"] if not np.isnan(rec["dir_alpha95"]) else 0.0
                    plon, plat, dp, dm = pmag.dia_vgp(rec["dir_dec"], rec["dir_inc"], a95, lat, lon)
                    rec.update({"lat": lat, "lon": lon, "vgp_lat": float(plat), "vgp_lon": float(plon),
                                "vgp_dp": float(dp), "vgp_dm": float(dm)})
            out.append(rec)
        return pd.DataFrame(out)

    def mean_pole(self, coord: int = COORD_GEOGRAPHIC, component: Optional[str] = None,
                  level: str = "site", common_polarity: bool = True,
                  location: Optional[str] = None, flip: bool = False) -> dict:
        """Fisher mean of the VGPs of one level (a paleomagnetic pole).

        Args:
            common_polarity: bring the VGPs to a common polarity about their
                principal axis (``unify_polarity``) before averaging; the
                ``flipped`` column of the returned VGP table records which ones
                were inverted relative to the stored VGPs.
            location: restrict to the sites of one location (None = all).
            flip: report the antipodes of the (unified) VGPs and pole — the
                unification points at the majority, the analyst chooses the
                polarity; ``paleolat`` changes sign accordingly.

        Returns:
            dict with plon, plat, A95, K, N, R, the DataFrame of VGPs used
            (``vgps``), the percentage of reversed VGPs (``reversed_perc``)
            and, when site coordinates are known, the mean sampling location
            (``site_lon``/``site_lat``) with its ``paleolat`` — empty dict if
            fewer than two VGPs are available.
        """
        means = self.mean_directions(level, coord, component)
        if len(means) == 0 or "vgp_lat" not in means.columns:
            return {}
        reference = None
        if location is not None and "location" in means.columns:
            # the polarity axis comes from the whole study, so that the poles of
            # different locations are reported in one consistent polarity
            study = means.dropna(subset=["vgp_lat", "vgp_lon"])
            if len(study) > 1:
                reference = polarity_axis(study[["vgp_lon", "vgp_lat"]].values)
            means = means[means["location"] == location]
        vgps = means.dropna(subset=["vgp_lat", "vgp_lon"]).copy()
        if len(vgps) < 2:
            return {}
        block = vgps[["vgp_lon", "vgp_lat"]].values.tolist()
        flipped = np.zeros(len(block), dtype=bool)
        if common_polarity:
            block, flipped = unify_polarity(block, reference)
        if flip:
            block = [list(antipode(lon, lat)) for lon, lat in block]
            flipped = ~flipped
        vgps["vgp_lon"], vgps["vgp_lat"] = [b[0] for b in block], [b[1] for b in block]
        vgps["flipped"] = flipped
        fm = pmag.fisher_mean(block)
        pole = {"plon": float(fm["dec"]), "plat": float(fm["inc"]), "A95": float(fm["alpha95"]),
                "K": float(fm["k"]), "N": int(fm["n"]), "R": float(fm["r"]), "vgps": vgps,
                "reversed_perc": float(100.0 * flipped.mean())}
        if {"lat", "lon"} <= set(vgps.columns) and vgps["lat"].notna().any():
            sites = vgps.dropna(subset=["lat", "lon"])
            cart = np.asarray(pmag.dir2cart(np.column_stack([sites["lon"], sites["lat"],
                                                             np.ones(len(sites))])), dtype=float).reshape(-1, 3)
            centre = pmag.cart2dir(cart.sum(axis=0))
            pole["site_lon"], pole["site_lat"] = float(centre[0]), float(centre[1])
            pole["paleolat"] = paleolatitude(pole["plon"], pole["plat"], pole["site_lon"], pole["site_lat"])
        return pole

    # ----- export ----------------------------------------------------------
    # Every table the app writes follows the same policy:
    #   * new rows carry only MagIC 3 columns of that table (``trim_to_model``);
    #   * new rows inherit the descriptive metadata (geology, ages, coordinates,
    #     names ...) of the rows they replace (``carry_metadata``), so a site
    #     keeps its lat/lon and lithology when its mean is rewritten;
    #   * the app owns the directional results of every specimen/sample/site/
    #     location it has measurements for: those rows are replaced, all other
    #     rows (intensity results, other studies' entities) are kept
    #     (``merge_results``).
    def _stamp(self, df: pd.DataFrame, analysts: Optional[str] = None) -> pd.DataFrame:
        if len(df) == 0:
            return df
        df = df.copy()
        df["citations"] = "This study"
        df["software_packages"] = SOFTWARE_TAG
        if analysts:
            df["analysts"] = analysts
        return df

    def specimens_table(self, coords=(COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT),
                        analysts: Optional[str] = None) -> pd.DataFrame:
        """MagIC 3 specimens rows for every component in every available coordinate system."""
        rows = []
        n_comps = {s: len(self.components_for(s)) for s in self.specimens}
        # a plane only gains a direction once its site's lines pin it down (MM88),
        # and that direction differs per coordinate system, as the mean does
        bfv = {coord: self.best_fit_vectors(coord) for coord in coords}
        for comp in self.components:
            spec = self.specimens[comp.specimen]
            for coord in coords:
                result = self.fit(comp, coord)
                if result is None:
                    continue
                rec = result.to_record()
                rec.update({"sample": spec.sample, "dir_n_comps": n_comps[comp.specimen]})
                vector = bfv[coord].get((comp.specimen, comp.name)) if result.direction_type == "p" else None
                if vector is not None:
                    rec["dir_bfv_dec"], rec["dir_bfv_inc"] = round(vector[0], 1), round(vector[1], 1)
                rows.append(rec)
        return self._stamp(pd.DataFrame(rows), analysts)

    def merged_specimens_table(self, coords=(COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT),
                               analysts: Optional[str] = None) -> pd.DataFrame:
        """New directional rows merged with the rows already in the contribution.

        Geology and lithology (required by MagIC) are inherited from the
        existing specimen rows, failing that from the samples table.
        """
        new = self.specimens_table(coords, analysts)
        existing = self._table("specimens")
        new = carry_metadata(new, existing, "specimen")
        samples = self._table("samples")
        if samples is not None and len(new):
            new = carry_metadata(new, samples, "sample", columns=("geologic_classes", "geologic_types", "lithologies"))
        merged = merge_results(existing, new, "specimen", owned=self.specimen_names)
        # every measured specimen must appear in the specimens table (MagIC
        # checks measurements.specimen against it): add a minimal row for the
        # ones without an interpretation and without any existing row
        present = set(merged["specimen"].astype(str)) if len(merged) else set()
        missing = [n for n in self.specimen_names if n not in present]
        if missing:
            stub = pd.DataFrame({"specimen": missing, "sample": [self.specimens[n].sample for n in missing]})
            if samples is not None:
                stub = carry_metadata(stub, samples, "sample",
                                      columns=("geologic_classes", "geologic_types", "lithologies", "citations"))
            merged = pd.concat([merged, stub], ignore_index=True, sort=False)
        return trim_to_model(merged, "specimens", self.warnings)

    def write_specimens(self, dir_path: str, coords=(COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT),
                        custom_name: Optional[str] = None, analysts: Optional[str] = None) -> Optional[str]:
        """Write the merged specimens table as a MagIC 3 tab-delimited file."""
        df = self.merged_specimens_table(coords, analysts)
        if len(df) == 0:
            return None
        mdf = cb.MagicDataFrame(dtype="specimens", df=df)
        return mdf.write_magic_file(custom_name=custom_name, dir_path=dir_path)

    def write_measurements(self, dir_path: str, custom_name: str = "measurements.txt") -> Optional[str]:
        """Write the measurements table with the current good/bad (``quality``) flags.

        The file is always written inside ``dir_path`` (``custom_name`` is a
        bare file name); the source file the contribution was read from is
        never touched.
        """
        table = self.contribution.tables.get("measurements")
        if table is None:
            return None
        df = table.df
        if "quality" not in df.columns:
            df["quality"] = "g"
        col = df.columns.get_loc("quality")
        for spec in self.specimens.values():
            df.iloc[spec.steps["meas_pos"].values, col] = spec.steps["quality"].values
        target = os.path.join(os.path.realpath(dir_path), os.path.basename(custom_name))
        return table.write_magic_file(custom_name=target, dir_path=dir_path)

    def _coords_arg(self, coord, coords):
        if coords is not None:
            return tuple(coords)
        return (COORD_GEOGRAPHIC if coord is None else coord,)

    def means_table(self, level: str, coord: Optional[int] = None, over: str = "specimens",
                    analysts: Optional[str] = None, coords=None) -> pd.DataFrame:
        """Sample or site means (and VGPs for sites) merged into the existing table.

        One row per (entity, component, coordinate system): pass ``coords`` to
        write geographic and tilt-corrected rows side by side, as the legacy
        GUI did (``coord`` alone writes one system).
        """
        if level not in ("sample", "site"):
            raise ValueError("means_table handles samples and sites; use locations_table for locations")
        parts = [self.mean_directions(level=level, coord=c, over=over) for c in self._coords_arg(coord, coords)]
        parts = [p for p in parts if len(p)]
        if not parts:
            return pd.DataFrame()
        means = pd.concat(parts, ignore_index=True, sort=False)
        means["result_type"] = "a"
        means["result_quality"] = "g"
        if level == "site" and "vgp_lat" in means.columns:
            has_vgp = means["vgp_lat"].notna()
            means.loc[has_vgp, "method_codes"] = [_join_codes(_codes(mc) + [VGP_CODE])
                                                  for mc in means.loc[has_vgp, "method_codes"]]
            means.loc[has_vgp, "dir_polarity"] = [vgp_polarity(v) for v in means.loc[has_vgp, "vgp_lat"]]
        for col in ("dir_dec", "dir_inc", "dir_alpha95", "dir_k", "dir_r", "vgp_lat", "vgp_lon", "vgp_dp", "vgp_dm",
                    "lat", "lon"):
            if col in means.columns:
                means[col] = pd.to_numeric(means[col], errors="coerce").round(4 if col in ("lat", "lon") else 1)
        internal = ["reversed_perc"]                 # helper columns of mean_directions, not MagIC columns
        if level == "sample":           # sample coordinates and VGPs belong to sites, never to sample rows
            internal += ["lat", "lon", "location", "vgp_lat", "vgp_lon", "vgp_dp", "vgp_dm"]
        means = means.drop(columns=[c for c in internal if c in means.columns])
        table = level + "s"
        existing = self._table(table)
        new = carry_metadata(self._stamp(means, analysts), existing, level)
        merged = merge_results(existing, new, level, owned=self.names_at(level))
        return trim_to_model(merged, table, self.warnings)

    def write_means(self, level: str, dir_path: str, coord: Optional[int] = None,
                    custom_name: Optional[str] = None, over: str = "specimens",
                    analysts: Optional[str] = None, common_polarity: bool = True,
                    flip: bool = False, coords=None) -> Optional[str]:
        """Write sample or site means (and VGPs) merged into the existing table.

        ``common_polarity`` and ``flip`` apply to the location level only (see
        ``mean_directions`` / ``mean_pole``); ``coords`` writes one row per
        coordinate system."""
        if level == "location":
            return self.write_locations(dir_path, coord=coord, custom_name=custom_name, over=over, analysts=analysts,
                                        common_polarity=common_polarity, flip=flip, coords=coords)
        df = self.means_table(level, coord=coord, over=over, analysts=analysts, coords=coords)
        if len(df) == 0:
            return None
        mdf = cb.MagicDataFrame(dtype=level + "s", df=df)
        return mdf.write_magic_file(custom_name=custom_name, dir_path=dir_path)

    def locations_table(self, coord: Optional[int] = None, over: str = "sites",
                        analysts: Optional[str] = None, common_polarity: bool = True,
                        flip: bool = False, coords=None) -> pd.DataFrame:
        """Location rows: the mean direction per component plus the paleomagnetic pole.

        One row per (location, component, coordinate system). The pole is the
        Fisher mean of the site VGPs of the location (``mean_pole``), with the
        polarity axis taken from the whole study so that every location is
        reported in the same polarity; ``pole_reversed_perc``, ``paleolat`` and
        ``dir_polarity`` follow the MagIC definitions. The geographic extent
        (``lat_s`` ...) is derived from the site coordinates when the existing
        table does not carry it.
        """
        parts = [self.mean_directions("location", coord=c, over=over, common_polarity=common_polarity, flip=flip)
                 for c in self._coords_arg(coord, coords)]
        parts = [p for p in parts if len(p)]
        if not parts:
            return pd.DataFrame()
        means = pd.concat(parts, ignore_index=True, sort=False)
        rows = []
        for _, m in means.iterrows():
            loc, comp, coord = m["location"], m["dir_comp_name"], int(m["dir_tilt_correction"])
            rev = float(m.get("reversed_perc", 0.0) or 0.0)
            rec = {"location": loc, "dir_tilt_correction": coord, "result_type": "a", "result_quality": "g",
                   "description": f"{comp} component" + (f"; directions brought to a common polarity "
                                                          f"({rev:.0f}% inverted)" if rev else ""),
                   "method_codes": m["method_codes"]}
            for col in ("dir_dec", "dir_inc", "dir_alpha95", "dir_k", "dir_r", "dir_n_sites", "dir_n_samples",
                        "dir_n_specimens"):
                if col in m and not _is_null(m[col]):
                    rec[col] = round(float(m[col]), 1) if col.startswith("dir_") and "n_" not in col else int(m[col])
            pole = self.mean_pole(coord, comp, "site", common_polarity=common_polarity, location=loc, flip=flip)
            if pole:
                rec.update({"pole_lat": round(pole["plat"], 1), "pole_lon": round(pole["plon"], 1),
                            "pole_alpha95": round(pole["A95"], 1), "pole_k": round(pole["K"], 1),
                            "pole_r": round(pole["R"], 4), "pole_n_sites": pole["N"], "pole_comp_name": comp,
                            "pole_reversed_perc": round(pole["reversed_perc"], 1)})
                if "paleolat" in pole:
                    rec["paleolat"] = round(pole["paleolat"], 1)
                rec["dir_polarity"] = vgp_polarity(pole["plat"])
                rec["method_codes"] = _join_codes(_codes(rec["method_codes"]) + [POLE_CODE])
            sites = [s for s in self.site_coords if s in self.names_at("site")
                     and any(sp.site == s and sp.location == loc for sp in self.specimens.values())]
            if sites:
                lats = [self.site_coords[s][0] for s in sites]
                lons = [self.site_coords[s][1] for s in sites]
                rec.update({"lat_s": round(min(lats), 4), "lat_n": round(max(lats), 4),
                            "lon_w": round(min(lons), 4), "lon_e": round(max(lons), 4)})
            rows.append(rec)
        new = self._stamp(pd.DataFrame(rows), analysts)
        existing = self._table("locations")
        new = carry_metadata(new, existing, "location")
        new = self._aggregate_site_geology(new)
        merged = merge_results(existing, new, "location", owned=self.names_at("location"))
        return trim_to_model(merged, "locations", self.warnings)

    def _aggregate_site_geology(self, locations: pd.DataFrame) -> pd.DataFrame:
        """Fill empty geologic_classes/lithologies of location rows with the union of the
        values recorded for their sites (MagIC requires them at every level)."""
        sites = self._table("sites")
        if sites is None or len(locations) == 0 or "location" not in sites.columns:
            return locations
        locations = locations.copy()
        for col in ("geologic_classes", "lithologies"):      # the two the locations table carries
            if col not in sites.columns:
                continue
            if col not in locations.columns:
                locations[col] = np.nan
            locations[col] = locations[col].astype(object)
            union = {}
            for loc, grp in sites.groupby(sites["location"].astype(str)):
                values = []
                for cell in grp[col].dropna().astype(str):
                    values += [v.strip() for v in cell.split(":") if v.strip()]
                if values:
                    union[loc] = ":".join(sorted(set(values)))
            empty = locations[col].isna() | (locations[col].astype(str).str.strip() == "")
            locations.loc[empty, col] = locations.loc[empty, "location"].astype(str).map(union)
        return locations

    def write_locations(self, dir_path: str, coord: Optional[int] = None, custom_name: Optional[str] = None,
                        over: str = "sites", analysts: Optional[str] = None, common_polarity: bool = True,
                        flip: bool = False, coords=None) -> Optional[str]:
        df = self.locations_table(coord=coord, over=over, analysts=analysts, common_polarity=common_polarity,
                                  flip=flip, coords=coords)
        if len(df) == 0:
            return None
        mdf = cb.MagicDataFrame(dtype="locations", df=df)
        return mdf.write_magic_file(custom_name=custom_name, dir_path=dir_path)

    # ----- persistence of the interpretation state -------------------------
    def components_to_json(self) -> str:
        payload = []
        for c in self.components:
            spec = self.specimens[c.specimen]
            payload.append({**asdict(c),
                            "step_min_label": spec.steps["label"].iloc[c.imin],
                            "step_max_label": spec.steps["label"].iloc[c.imax]})
        return json.dumps({"software": SOFTWARE_TAG, "components": payload}, indent=1)

    def components_from_json(self, text: str) -> int:
        data = json.loads(text)
        n = 0
        for c in data.get("components", []):
            if c["specimen"] in self.specimens:
                self.add_component(c["specimen"], c["name"], c["imin"], c["imax"],
                                   c.get("fit_type", "DE-BFL"), c.get("quality", "g"))
                n += 1
        return n

    def save_components(self, path: str) -> str:
        with open(path, "w") as fh:
            fh.write(self.components_to_json())
        return path

    def load_components(self, path: str) -> int:
        with open(path) as fh:
            return self.components_from_json(fh.read())
