"""
Paleointensity statistics: Standard Paleointensity Definitions v1.2.0 and after.

Pure functions over plain numpy arrays. Nothing in this module knows about
MagIC tables, files, plots or any user interface, so every statistic can be
checked against its published equation on its own, from a notebook or a test,
and the application layer can only ever *display* what is computed here.

Reference
---------
Paterson, G. A., L. Tauxe, A. J. Biggin, R. Shaar, and L. C. Jonestrask (2014),
On improving the selection of Thellier-type paleointensity data,
Geochem. Geophys. Geosyst., 15, 1180-1192, doi:10.1002/2013GC005135, and the
accompanying *Standard Paleointensity Definitions* v1.2.0 (February 2021),
https://earthref.org/PmagPy/SPD/DL/SPD_v1.2.0.pdf.

Statistics added since SPD v1.2.0 carry their own citation on the
:class:`StatSpec` entry in :data:`CATALOG` and are listed in
``docs/paleointensity_literature_audit.md``.

Not-applicable states
---------------------
Every statistic is returned as a :class:`Stat`, which carries a state as well
as a value. A statistic that the experiment cannot produce (``dTR`` with no
pTRM tail checks) is ``NOT_APPLICABLE``; one that needs data this study does
not hold (``alpha'`` needs an independent direction) is ``UNAVAILABLE``; one
whose maths degenerates (``sigma_b`` with n = 2) is ``UNDEFINED``. No
statistic is ever reported as ``-999``.
"""
from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "State", "Stat", "ok", "na", "unavailable", "undefined",
    "AraiPoints", "PtrmCheck", "TailCheck", "AdditivityCheck", "Experiment",
    "arai_statistics", "directional_statistics", "ptrm_check_statistics",
    "tail_check_statistics", "additivity_check_statistics", "all_statistics",
    "group_statistics", "CATALOG", "StatSpec",
    "york_regression", "arai_curvature", "ziggie", "izzi_md",
    "anisotropy_correction_factor", "nlt_correction", "cooling_rate_factor",
]


# ---------------------------------------------------------------------------
# Typed results
# ---------------------------------------------------------------------------
class State(enum.Enum):
    """Why a statistic has (or has not) a value."""
    OK = "ok"
    #: the experiment as performed cannot produce it (e.g. no tail checks)
    NOT_APPLICABLE = "not applicable"
    #: it needs data outside this experiment (e.g. an independent direction)
    UNAVAILABLE = "unavailable"
    #: the calculation degenerates for this selection (e.g. n < 3)
    UNDEFINED = "undefined"


@dataclass(frozen=True)
class Stat:
    """One statistic: its value, or an explicit reason there is none."""
    name: str
    value: Optional[float] = None
    state: State = State.OK
    reason: str = ""

    def __bool__(self) -> bool:            # ``if stat:`` asks "is there a value"
        return self.state is State.OK and self.value is not None

    @property
    def is_value(self) -> bool:
        return bool(self)

    def __float__(self) -> float:
        if not self:
            return float("nan")
        return float(self.value)

    def text(self, fmt: str = "{:.3g}") -> str:
        if self.state is not State.OK or self.value is None:
            return {State.NOT_APPLICABLE: "n/a",
                    State.UNAVAILABLE: "—",
                    State.UNDEFINED: "undef."}.get(self.state, "—")
        if isinstance(self.value, (bool, np.bool_)):
            return "pass" if self.value else "fail"
        return fmt.format(self.value)


def ok(name: str, value) -> Stat:
    if value is None:
        return Stat(name, None, State.UNDEFINED, "no value")
    if isinstance(value, (bool, np.bool_)):
        return Stat(name, bool(value), State.OK)
    value = float(value)
    if not np.isfinite(value):
        return Stat(name, None, State.UNDEFINED, "not finite")
    return Stat(name, value, State.OK)


def na(name: str, reason: str) -> Stat:
    return Stat(name, None, State.NOT_APPLICABLE, reason)


def unavailable(name: str, reason: str) -> Stat:
    return Stat(name, None, State.UNAVAILABLE, reason)


def undefined(name: str, reason: str) -> Stat:
    return Stat(name, None, State.UNDEFINED, reason)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
@dataclass
class PtrmCheck:
    """A pTRM check to step ``i`` performed after reaching step ``j``.

    ``x`` is the scalar pTRM of the check (its position on the Arai x axis);
    ``vector`` is the full pTRM check vector in specimen coordinates.
    """
    i: int
    j: int
    x: float
    vector: Optional[np.ndarray] = None


@dataclass
class TailCheck:
    """A pTRM tail check (repeat zero-field step) to step ``i``."""
    i: int
    y: float
    vector: Optional[np.ndarray] = None


@dataclass
class AdditivityCheck:
    """An additivity check: pTRM*(Ti, T0) estimated after reaching Tj."""
    i: int
    j: int
    x: float
    vector: Optional[np.ndarray] = None


@dataclass
class Experiment:
    """Everything a specimen's paleointensity statistics are computed from.

    Attributes:
        x: pTRM gained at every Arai point, length ``nmax``.
        y: NRM remaining at every Arai point, length ``nmax``.
        temps: treatment step of every Arai point (K), length ``nmax``.
        nrm_vectors: (nmax, 3) NRM vectors in specimen coordinates.
        trm_vectors: (nmax, 3) pTRM vectors in specimen coordinates.
        steps: 'ZI' / 'IZ' / 'NRM' label per Arai point (for IZZI_MD).
        blab: laboratory field strength in tesla.
        blab_orient: unit vector of the laboratory field, specimen coordinates.
        ptrm_checks / tail_checks / additivity_checks: check records.
        chrm: an independent characteristic direction as a unit vector, when
            one is known (needed by alpha' and CRM%).
    """
    x: np.ndarray
    y: np.ndarray
    temps: np.ndarray
    nrm_vectors: np.ndarray
    trm_vectors: Optional[np.ndarray] = None
    steps: Optional[Sequence[str]] = None
    blab: float = np.nan
    blab_orient: Optional[np.ndarray] = None
    ptrm_checks: List[PtrmCheck] = field(default_factory=list)
    tail_checks: List[TailCheck] = field(default_factory=list)
    additivity_checks: List[AdditivityCheck] = field(default_factory=list)
    chrm: Optional[np.ndarray] = None

    @property
    def nmax(self) -> int:
        return len(self.x)


@dataclass
class AraiPoints:
    """The selected Arai segment: ``start`` and ``end`` are indices into ``x``/``y``."""
    x: np.ndarray
    y: np.ndarray
    start: int
    end: int

    @property
    def n(self) -> int:
        return self.end - self.start + 1


# ---------------------------------------------------------------------------
# The paleointensity estimate (SPD section 3.2)
# ---------------------------------------------------------------------------
def york_regression(x: np.ndarray, y: np.ndarray) -> dict:
    """Standardized major axis fit of an Arai segment (York, 1966; Coe et al., 1978).

    Returns a dict with ``b``, ``sigma_b``, ``y_int``, ``x_int``, ``xbar``,
    ``ybar``, ``n`` and the points projected onto the best-fit line
    (``x_prime``, ``y_prime``, ``delta_x_prime``, ``delta_y_prime``,
    ``line_length``).

    ``sigma_b`` follows SPD v1.2.0, which corrected the equation to use ``b``
    and not ``|b|`` (v1.2 change 1).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(x)
    out = {"n": n}
    if n < 2:
        return {**out, "b": np.nan, "sigma_b": np.nan, "y_int": np.nan, "x_int": np.nan}
    xbar, ybar = float(np.mean(x)), float(np.mean(y))
    u, v = x - xbar, y - ybar
    sxx, syy, sxy = float(np.sum(u * u)), float(np.sum(v * v)), float(np.sum(u * v))
    if sxx == 0:
        return {**out, "b": np.nan, "sigma_b": np.nan, "y_int": np.nan, "x_int": np.nan,
                "xbar": xbar, "ybar": ybar}
    b = float(np.sign(sxy) * math.sqrt(syy / sxx)) if sxy != 0 else 0.0
    if n > 2:
        num = 2.0 * syy - 2.0 * b * sxy
        sigma_b = math.sqrt(num / ((n - 2) * sxx)) if num >= 0 else np.nan
    else:
        sigma_b = np.nan
    y_int = ybar - b * xbar
    x_int = -y_int / b if b != 0 else np.nan
    # project the selected points onto the best-fit line
    if b != 0:
        rev_x = (y - y_int) / b
        rev_y = b * x + y_int
        x_prime = (x + rev_x) / 2.0
        y_prime = (y + rev_y) / 2.0
    else:
        x_prime, y_prime = x.copy(), np.full_like(y, y_int)
    dxp = float(np.max(x_prime) - np.min(x_prime))
    dyp = float(np.max(y_prime) - np.min(y_prime))
    out.update(b=b, sigma_b=sigma_b, y_int=y_int, x_int=x_int, xbar=xbar, ybar=ybar,
               sxx=sxx, syy=syy, sxy=sxy, x_prime=x_prime, y_prime=y_prime,
               delta_x_prime=dxp, delta_y_prime=dyp,
               line_length=math.hypot(dxp, dyp))
    return out


def vector_difference_sum(nrm_vectors: np.ndarray) -> float:
    """VDS of the whole NRM vector (SPD section 3.3)."""
    v = np.asarray(nrm_vectors, dtype=float)
    if len(v) == 0:
        return np.nan
    last = float(np.linalg.norm(v[-1]))
    if len(v) == 1:
        return last
    return last + float(np.sum(np.linalg.norm(np.diff(v, axis=0), axis=1)))


# ---------------------------------------------------------------------------
# Circle fitting for the Arai plot curvature (Paterson, 2011)
# ---------------------------------------------------------------------------
def _taubin_svd(xy: np.ndarray) -> Tuple[float, float, float]:
    """Algebraic circle fit (Taubin, 1991); returns centre (a, b) and radius r."""
    centroid = xy.mean(axis=0)
    x = xy[:, 0] - centroid[0]
    y = xy[:, 1] - centroid[1]
    z = x * x + y * y
    zmean = z.mean()
    if zmean <= 0:
        return np.nan, np.nan, np.nan
    z0 = (z - zmean) / (2.0 * math.sqrt(zmean))
    zxy = np.column_stack((z0, x, y))
    _, _, vt = np.linalg.svd(zxy)
    a = vt[2].copy()
    a[0] = a[0] / (2.0 * math.sqrt(zmean))
    a = np.append(a, -zmean * a[0])
    if a[0] == 0:
        return np.nan, np.nan, np.nan
    cx = -a[1] / a[0] / 2.0 + centroid[0]
    cy = -a[2] / a[0] / 2.0 + centroid[1]
    disc = a[1] * a[1] + a[2] * a[2] - 4.0 * a[0] * a[3]
    if disc < 0:
        return cx, cy, np.nan
    r = math.sqrt(disc) / abs(a[0]) / 2.0
    return float(cx), float(cy), float(r)


def _circle_variance(xy: np.ndarray, par: Sequence[float]) -> float:
    n = len(xy)
    if n <= 3:
        return np.inf
    d = np.hypot(xy[:, 0] - par[0], xy[:, 1] - par[1]) - par[2]
    return float(d @ d / (n - 3))


def _lma(xy: np.ndarray, par_ini: Sequence[float]) -> Tuple[float, float, float]:
    """Geometric circle fit by Levenberg-Marquardt in algebraic parameters.

    Chernov, N. and C. Lesort (2005), Least squares fitting of circles,
    J. Math. Imag. Vision, 23, 239-251. SPD recommends this over the standard
    non-linear fitters, which converge poorly on near-linear Arai plots.
    """
    factor_up, factor_down = 10.0, 0.04
    lamb, epsilon = 0.01, 1e-6
    iter_max, adjust_max = 50, 20
    xshift = yshift = 0.0
    dx, dy = 1.0, 0.0
    n = len(xy)

    a_new = 1.0 / (2.0 * par_ini[2])
    aabb = (par_ini[0] + xshift) ** 2 + (par_ini[1] + yshift) ** 2
    f_new = (aabb - par_ini[2] ** 2) * a_new
    t_new = math.acos(max(-1.0, min(1.0, -(par_ini[0] + xshift) / math.sqrt(aabb)))) if aabb > 0 else 0.0
    if par_ini[1] + yshift > 0:
        t_new = 2 * math.pi - t_new
    var_new = _circle_variance(xy, par_ini)
    finish = False
    a_old, f_old, t_old, var_old = a_new, f_new, t_new, var_new

    for _ in range(iter_max):
        a_old, f_old, t_old, var_old = a_new, f_new, t_new, var_new
        h = math.sqrt(max(0.0, 1 + 4 * a_old * f_old))
        if a_old == 0:
            break
        a_pt = -h * math.cos(t_old) / (2 * a_old) - xshift
        b_pt = -h * math.sin(t_old) / (2 * a_old) - yshift
        r_old = 1.0 / abs(2 * a_old)

        dd = 1 + 4 * a_old * f_old
        if dd < 0:
            break
        d = math.sqrt(dd)
        ct, st = math.cos(t_old), math.sin(t_old)
        xi = xy[:, 0] + xshift
        yi = xy[:, 1] + yshift
        zi = xi * xi + yi * yi
        ui = xi * ct + yi * st
        vi = -xi * st + yi * ct
        adf = a_old * zi + d * ui + f_old
        sq = np.sqrt(np.maximum(4 * a_old * adf + 1, 0.0))
        den = sq + 1
        gi = 2 * adf / den
        fact = 2 / den * (1 - a_old * gi / np.where(sq == 0, np.nan, sq))
        dgda = fact * (zi + 2 * f_old * ui / d) - gi * gi / np.where(sq == 0, np.nan, sq)
        dgdf = fact * (2 * a_old * ui / d + 1)
        dgdt = fact * d * vi
        if not np.all(np.isfinite(dgda)):
            break
        h11, h12, h13 = float(dgda @ dgda), float(dgda @ dgdf), float(dgda @ dgdt)
        h22, h23, h33 = float(dgdf @ dgdf), float(dgdf @ dgdt), float(dgdt @ dgdt)
        f1, f2, f3 = float(gi @ dgda), float(gi @ dgdf), float(gi @ dgdt)

        for _ in range(adjust_max):
            try:
                g11 = math.sqrt(h11 + lamb)
                g12, g13 = h12 / g11, h13 / g11
                g22 = math.sqrt(h22 + lamb - g12 * g12)
                g23 = (h23 - g12 * g13) / g22
                g33 = math.sqrt(h33 + lamb - g13 * g13 - g23 * g23)
            except (ValueError, ZeroDivisionError):
                lamb *= factor_up
                continue
            d1 = f1 / g11
            d2 = (f2 - g12 * d1) / g22
            d3 = (f3 - g13 * d1 - g23 * d2) / g33
            dt = d3 / g33
            df = (d2 - g23 * dt) / g22
            da = (d1 - g12 * df - g13 * dt) / g11
            a_new, f_new, t_new = a_old - da, f_old - df, t_old - dt

            if 1 + 4 * a_new * f_new < epsilon and lamb > 1:
                xshift += dx
                yshift += dy
                h = math.sqrt(max(0.0, 1 + 4 * a_old * f_old))
                a_tmp = -h * math.cos(t_old) / (2 * a_old) + dx
                b_tmp = -h * math.sin(t_old) / (2 * a_old) + dy
                r_tmp = 1.0 / abs(2 * a_old)
                a_new = 1.0 / (2 * r_tmp)
                aabb = a_tmp * a_tmp + b_tmp * b_tmp
                f_new = (aabb - r_tmp * r_tmp) * a_new
                t_new = math.acos(max(-1.0, min(1.0, -a_tmp / math.sqrt(aabb)))) if aabb > 0 else 0.0
                if b_tmp > 0:
                    t_new = 2 * math.pi - t_new
                var_new = var_old
                break
            if 1 + 4 * a_new * f_new < epsilon:
                lamb *= factor_up
                continue
            d = math.sqrt(1 + 4 * a_new * f_new)
            ct, st = math.cos(t_new), math.sin(t_new)
            ui = (xy[:, 0] + xshift) * ct + (xy[:, 1] + yshift) * st
            zi = (xy[:, 0] + xshift) ** 2 + (xy[:, 1] + yshift) ** 2
            adf = a_new * zi + d * ui + f_new
            sq = np.sqrt(np.maximum(4 * a_new * adf + 1, 0.0))
            gi = 2 * adf / (sq + 1)
            var_new = float(gi @ gi / (n - 3)) if n > 3 else float(gi @ gi)
            h = math.sqrt(1 + 4 * a_new * f_new)
            a_pt_new = -h * math.cos(t_new) / (2 * a_new) - xshift
            b_pt_new = -h * math.sin(t_new) / (2 * a_new) - yshift
            r_new = 1.0 / abs(2 * a_new)
            if var_new <= var_old:
                progress = (abs(a_pt_new - a_pt) + abs(b_pt_new - b_pt) + abs(r_new - r_old)) / (r_new + r_old)
                if progress < epsilon:
                    a_old, f_old, t_old = a_new, f_new, t_new
                    finish = True
                lamb *= factor_down
                break
            lamb *= factor_up
        if finish:
            break

    if a_old == 0 or not np.isfinite(a_old):
        return np.nan, np.nan, np.nan
    h = math.sqrt(max(0.0, 1 + 4 * a_old * f_old))
    return (float(-h * math.cos(t_old) / (2 * a_old) - xshift),
            float(-h * math.sin(t_old) / (2 * a_old) - yshift),
            float(1.0 / abs(2 * a_old)))


def arai_curvature(x, y) -> dict:
    """Curvature of an Arai plot (Paterson, 2011, doi:10.1029/2011JB008369).

    Fits a circle to the (normalised) data and returns ``k`` (signed
    1/radius), the circle centre ``a``/``b``, the radius ``r``, the sum of
    squared errors ``sse`` and the RMS misfit ``rms``.

    Both axes are normalised by their own maxima so that the result does not
    depend on ``B_lab`` or on the NRM intensity. The sign follows SPD: the
    curvature is negative when the circle centre lies below-left of the data
    centroid (convex-up Arai plot), positive otherwise.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or np.max(np.abs(x)) == 0 or np.max(np.abs(y)) == 0:
        return {"k": np.nan, "a": np.nan, "b": np.nan, "r": np.nan, "sse": np.nan, "rms": np.nan}
    xn = x / np.max(x)
    yn = y / np.max(y)
    xy = np.column_stack((xn, yn))
    e1 = _taubin_svd(xy)
    if not np.all(np.isfinite(e1)):
        return {"k": np.nan, "a": np.nan, "b": np.nan, "r": np.nan, "sse": np.nan, "rms": np.nan}
    est = _lma(xy, e1) if len(xn) > 3 else e1
    if not np.all(np.isfinite(est)) or est[2] == 0:
        est = e1
    a, b, r = est
    if not np.isfinite(r) or r == 0:
        return {"k": np.nan, "a": a, "b": b, "r": r, "sse": np.nan, "rms": np.nan}
    resid = np.hypot(xn - a, yn - b) - r
    sse = float(resid @ resid)
    rms = float(math.sqrt(sse / len(xn)))
    k = -1.0 / r if (a <= np.mean(xn) and b <= np.mean(yn)) else 1.0 / r
    return {"k": float(k), "a": float(a), "b": float(b), "r": float(r), "sse": sse, "rms": rms}


# ---------------------------------------------------------------------------
# Ziggie (Tully & Paterson, 2025)
# ---------------------------------------------------------------------------
def _circle_projection(a: float, b: float, r: float, px: float, py: float) -> Tuple[float, float]:
    """The point of the circle (a, b, r) closest to (px, py)."""
    dx, dy = px - a, py - b
    d = math.hypot(dx, dy)
    if d == 0:
        return a + r, b
    return a + r * dx / d, b + r * dy / d


def _arc_length(k: float, a: float, b: float, p1, p2) -> float:
    """Length of the best-fit arc between the projections of ``p1`` and ``p2``."""
    r = abs(1.0 / k)
    x1, y1 = _circle_projection(a, b, r, *p1)
    x2, y2 = _circle_projection(a, b, r, *p2)
    v1 = np.array([a - x1, b - y1], dtype=float)
    v2 = np.array([a - x2, b - y2], dtype=float)
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return np.nan
    v1, v2 = v1 / n1, v2 / n2
    angle = math.atan2(v1[0] * v2[1] - v1[1] * v2[0], v1[0] * v2[0] + v1[1] * v2[1])
    if angle < 0:
        angle += 2 * math.pi
    if k < 0:
        angle = 2 * math.pi - angle
    return r * angle


#: Below this |k'| the best-fit circle is indistinguishable from a line and
#: Ziggie uses the line length instead (Tully & Paterson, 2025: 1/|k'| >= 1000).
ZIGGIE_LINE_FALLBACK_K = 1e-3
#: The criterion proposed by Tully & Paterson (2025) for IZZI experiments.
ZIGGIE_CRITERION = 0.1


def ziggie(x, y) -> dict:
    """Ziggie: Arai-plot zig-zag (Tully & Paterson, 2025, doi:10.1029/2025JB031608).

    ``Ziggie = ln(cumulative line length / length of the best-fit arc)``, both
    measured on the selected segment after normalising x by its maximum and y
    by its maximum. The best-fit arc uses the same circle fit as the curvature
    ``k'``; when ``1/|k'| >= 1000`` the data are better described by a line, so
    the length of the best-fit line (its projected extent) is used instead --
    this also keeps the arc-length numerically stable.

    Returns ``ziggie``, ``cumulative_length``, ``reference_length``,
    ``k_prime``, ``rms`` and ``model`` ('arc' or 'line'). Ziggie is zero for a
    perfectly straight, monotonic segment and grows with zig-zag; it can be
    slightly negative when the circle fit is poor, which the ``rms`` reports.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    out = {"ziggie": np.nan, "cumulative_length": np.nan, "reference_length": np.nan,
           "k_prime": np.nan, "rms": np.nan, "model": ""}
    if len(x) < 3 or np.max(np.abs(x)) == 0 or np.max(np.abs(y)) == 0:
        return out
    xn = x / np.max(x)
    yn = y / np.max(y)
    cum = float(np.sum(np.hypot(np.diff(xn), np.diff(yn))))
    out["cumulative_length"] = cum
    curv = arai_curvature(xn, yn)
    k = curv["k"]
    out["k_prime"] = k
    out["rms"] = curv["rms"]
    if not np.isfinite(k) or abs(k) <= ZIGGIE_LINE_FALLBACK_K:
        fit = york_regression(xn, yn)
        ref = fit.get("line_length", np.nan)
        out["model"] = "line"
    else:
        ref = _arc_length(k, curv["a"], curv["b"], (xn[0], yn[0]), (xn[-1], yn[-1]))
        out["model"] = "arc"
    out["reference_length"] = ref
    if np.isfinite(ref) and ref > 0 and cum > 0:
        out["ziggie"] = float(math.log(cum / ref))
    return out


# ---------------------------------------------------------------------------
# IZZI_MD (Shaar et al., 2011)
# ---------------------------------------------------------------------------
def izzi_md(x, y, steps: Sequence[str]) -> float:
    """IZZI_MD, the signed zig-zag area of an Arai plot (Shaar et al., 2011).

    ``steps`` labels every Arai point 'ZI', 'IZ' or 'NRM'; the first point is
    excluded from the calculation, as in the original work. The area of each
    consecutive triple is signed by whether the mid-point lies above or below
    the line through its neighbours, and the sum is normalised by the length
    of the polyline through the ZI steps.

    For a sequence that is not IZZI every area is taken as positive and every
    point counts toward the normalising length, as the SPD reference
    implementation does; the value is then a plain measure of scatter rather
    than of zig-zag, which is why :func:`arai_statistics` reports it as not
    applicable outside IZZI experiments.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 4 or y[0] == 0:
        return np.nan
    labels = list(steps) if steps is not None else ["ZI"] * len(x)
    xn, yn = x[1:] / y[0], y[1:] / y[0]
    lab = labels[1:]
    if len(xn) < 3:
        return np.nan
    is_izzi = {"ZI", "IZ"} <= set(lab)
    if not is_izzi:
        lab = [None] * len(lab)
    areas, signs = [], []
    zi_flag = np.zeros(len(xn), dtype=bool)
    for j in range(len(xn) - 2):
        x3, y3 = xn[j:j + 3], yn[j:j + 3]
        dx = x3[2] - x3[0]
        slope = (y3[2] - y3[0]) / dx if dx != 0 else np.nan
        a1 = y3[0] - slope * x3[0] if np.isfinite(slope) else np.nan
        a2 = y3[1] - slope * x3[1] if np.isfinite(slope) else np.nan
        mid = lab[j + 1]
        if mid == "IZ":
            zi_flag[j] = zi_flag[j + 2] = True
            sign = -1.0 if a1 < a2 else 1.0
        elif mid == "ZI":
            zi_flag[j + 1] = True
            sign = 1.0 if a1 < a2 else -1.0
        else:                       # not an IZZI sequence: unsigned scatter
            zi_flag[j] = True
            sign = 1.0
        if np.isfinite(a1) and np.isfinite(a2) and a1 == a2:
            sign = 0.0
        areas.append(_polygon_area(x3, y3))
        signs.append(sign)
    zi_idx = np.flatnonzero(zi_flag)
    if len(zi_idx) < 2:
        return np.nan
    zi_len = float(np.sum(np.hypot(np.diff(xn[zi_idx]), np.diff(yn[zi_idx]))))
    if zi_len == 0:
        return np.nan
    return float(np.dot(signs, areas) / zi_len)


def _polygon_area(x, y) -> float:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


# ---------------------------------------------------------------------------
# Directional helpers
# ---------------------------------------------------------------------------
def _angle(a, b) -> float:
    """Angle between two vectors, in degrees, robust near 0 and 180."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    cross = np.linalg.norm(np.cross(a, b))
    dot = float(np.dot(a, b))
    return float(math.degrees(math.atan2(cross, dot)))


def cart_to_dir(v) -> Tuple[float, float, float]:
    """Cartesian (x, y, z) -> (declination, inclination, intensity) in degrees."""
    v = np.asarray(v, dtype=float)
    r = float(np.linalg.norm(v))
    if r == 0:
        return 0.0, 0.0, 0.0
    dec = math.degrees(math.atan2(v[1], v[0])) % 360.0
    inc = math.degrees(math.asin(max(-1.0, min(1.0, v[2] / r))))
    return dec, inc, r


def dir_to_cart(dec: float, inc: float, intensity: float = 1.0) -> np.ndarray:
    d, i = math.radians(dec), math.radians(inc)
    return np.array([intensity * math.cos(i) * math.cos(d),
                     intensity * math.cos(i) * math.sin(d),
                     intensity * math.sin(i)])


def pca(vectors: np.ndarray, anchored: bool = False) -> dict:
    """Kirschvink (1980) principal component analysis of NRM vectors.

    Returns ``dec``, ``inc``, ``mad``, ``direction`` (unit vector),
    ``center`` (the centre of mass) and the eigenvalues ``tau``.
    """
    v = np.asarray(vectors, dtype=float)
    n = len(v)
    out = {"dec": np.nan, "inc": np.nan, "mad": np.nan,
           "direction": np.full(3, np.nan), "center": np.full(3, np.nan), "tau": None, "n": n}
    if n < 2:
        return out
    center = v.mean(axis=0)
    out["center"] = center
    shifted = v if anchored else v - center
    t = shifted.T @ shifted
    tau, vecs = np.linalg.eigh(t)
    order = np.argsort(tau)[::-1]
    tau, vecs = tau[order], vecs[:, order]
    principal = vecs[:, 0]
    reference = v[0] - v[-1]
    if np.dot(principal, reference) < 0:
        principal = -principal
    total = float(np.sum(tau))
    mad = math.degrees(math.atan(math.sqrt(max(0.0, (tau[1] + tau[2]) / tau[0])))) if tau[0] > 0 else np.nan
    dec, inc, _ = cart_to_dir(principal)
    out.update(dec=dec, inc=inc, mad=mad, direction=principal, tau=tau, total=total)
    return out


# ---------------------------------------------------------------------------
# Statistic groups
# ---------------------------------------------------------------------------
def arai_statistics(exp: Experiment, start: int, end: int,
                    beta_threshold: float = 0.1) -> Dict[str, Stat]:
    """SPD section 3: every Arai-plot statistic for the segment [start, end]."""
    x_all = np.asarray(exp.x, dtype=float)
    y_all = np.asarray(exp.y, dtype=float)
    seg = slice(start, end + 1)
    xs, ys = x_all[seg], y_all[seg]
    n = len(xs)
    s: Dict[str, Stat] = {}
    s["n"] = ok("n", n)
    s["nmax"] = ok("nmax", exp.nmax)
    s["Tmin"] = ok("Tmin", exp.temps[start])
    s["Tmax"] = ok("Tmax", exp.temps[end])
    if n < 3:
        for name in ("b", "sigma_b", "B_anc", "sigma_B", "Y_int", "X_int", "f", "f_vds", "FRAC",
                     "beta", "g", "GAP_MAX", "q", "w", "k", "k_prime", "SSE", "R2_corr", "R2_det",
                     "Z", "Z_star", "S", "S_prime", "p_chi2", "IZZI_MD", "Ziggie", "SCAT", "VDS"):
            s[name] = undefined(name, f"n = {n}; at least 3 selected steps are needed")
        return s

    fit = york_regression(xs, ys)
    b, sigma_b = fit["b"], fit["sigma_b"]
    y_int, x_int = fit["y_int"], fit["x_int"]
    s["b"] = ok("b", b)
    s["sigma_b"] = ok("sigma_b", sigma_b)
    s["Y_int"] = ok("Y_int", y_int)
    s["X_int"] = ok("X_int", x_int)
    if np.isfinite(exp.blab):
        s["B_anc"] = ok("B_anc", abs(b) * exp.blab)
        s["sigma_B"] = ok("sigma_B", sigma_b * exp.blab)
    else:
        s["B_anc"] = unavailable("B_anc", "the laboratory field strength is not recorded")
        s["sigma_B"] = unavailable("sigma_B", "the laboratory field strength is not recorded")

    vds = vector_difference_sum(exp.nrm_vectors)
    s["VDS"] = ok("VDS", vds)
    dyp, dxp = fit["delta_y_prime"], fit["delta_x_prime"]
    s["f"] = ok("f", dyp / abs(y_int)) if y_int else undefined("f", "Y_int is zero")
    s["f_vds"] = ok("f_vds", dyp / vds) if vds else undefined("f_vds", "VDS is zero")

    nrm = np.asarray(exp.nrm_vectors, dtype=float)
    seg_diffs = np.linalg.norm(np.diff(nrm[start:end + 1], axis=0), axis=1)
    s["FRAC"] = ok("FRAC", float(np.sum(seg_diffs) / vds)) if vds else undefined("FRAC", "VDS is zero")
    s["beta"] = ok("beta", abs(sigma_b / b)) if b else undefined("beta", "b is zero")

    yp = fit["y_prime"]
    gaps = np.diff(yp)
    s["g"] = ok("g", 1.0 - float(np.sum(gaps ** 2)) / (dyp ** 2)) if dyp else undefined("g", "the fit has no NRM extent")
    s["g_lim"] = ok("g_lim", (n - 2) / (n - 1))
    total_diff = float(np.sum(seg_diffs))
    s["GAP_MAX"] = (ok("GAP_MAX", float(np.max(seg_diffs)) / total_diff) if total_diff
                    else undefined("GAP_MAX", "no NRM is lost over the segment"))
    q = (abs(b) * float(s["f"]) * float(s["g"]) / sigma_b) if (sigma_b and s["f"] and s["g"]) else np.nan
    s["q"] = ok("q", q)
    s["w"] = ok("w", q / math.sqrt(n - 2)) if np.isfinite(q) and n > 2 else undefined("w", "n = 2")

    curv_all = arai_curvature(x_all, y_all)
    s["k"] = ok("k", curv_all["k"])
    s["SSE"] = ok("SSE", curv_all["sse"])
    curv_seg = arai_curvature(xs, ys)
    s["k_prime"] = ok("k_prime", curv_seg["k"])
    s["SSE_prime"] = ok("SSE_prime", curv_seg["sse"])

    zig = ziggie(xs, ys)
    s["Ziggie"] = ok("Ziggie", zig["ziggie"])
    s["Ziggie_rms"] = ok("Ziggie_rms", zig["rms"])

    u, v = xs - fit["xbar"], ys - fit["ybar"]
    sxx, syy, sxy = fit["sxx"], fit["syy"], fit["sxy"]
    s["R2_corr"] = ok("R2_corr", sxy ** 2 / (sxx * syy)) if sxx and syy else undefined("R2_corr", "degenerate segment")
    resid = ys - fit["y_prime"]
    s["R2_det"] = ok("R2_det", 1.0 - float(resid @ resid) / syy) if syy else undefined("R2_det", "degenerate segment")

    # Z and Z* (Yu & Tauxe 2005; Yu 2012), as defined in SPD v1.2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        bi = (y_int - y_all) / x_all
    bi = np.where(np.isfinite(bi), bi, 0.0)
    bi[0] = 0.0
    dummy = np.abs((bi - abs(b)) * x_all)
    z_sum = float(np.sum(dummy[seg]))
    s["Z"] = ok("Z", z_sum / abs(x_int)) if np.isfinite(x_int) and x_int else undefined("Z", "X_int is zero")
    s["Z_star"] = (ok("Z_star", 100.0 * z_sum / abs(y_int) / (n - 1)) if y_int and n > 1
                   else undefined("Z_star", "Y_int is zero"))

    # S, S' and p_chi2 (York 1966; Yu et al. 2000), added in SPD v1.2
    var_x, var_y = sxx / (n - 1), syy / (n - 1)
    denom = b * b * var_x + var_y
    if denom > 0:
        resid_line = ys - b * xs - y_int
        s_stat = float(np.sum(resid_line ** 2) / denom)
        s["S"] = ok("S", s_stat)
        s["S_prime"] = ok("S_prime", s_stat / (n - 2)) if n > 2 else undefined("S_prime", "n = 2")
        s["p_chi2"] = ok("p_chi2", _chi2_sf(s_stat, n - 2)) if n > 2 else undefined("p_chi2", "n = 2")
    else:
        for name in ("S", "S_prime", "p_chi2"):
            s[name] = undefined(name, "the data have no variance")

    if exp.steps is None:
        s["IZZI_MD"] = na("IZZI_MD", "the protocol does not record IZ/ZI step order")
    elif not ({"ZI", "IZ"} <= set(exp.steps)):
        s["IZZI_MD"] = na("IZZI_MD", "IZZI_MD measures IZ/ZI alternation; this experiment has none")
    else:
        value = izzi_md(x_all, y_all, exp.steps)
        s["IZZI_MD"] = ok("IZZI_MD", value) if np.isfinite(value) else \
            undefined("IZZI_MD", "the ZI polyline has zero length")

    s["SCAT"] = _scat(exp, fit, start, end, beta_threshold)
    s["SCAT_beta_threshold"] = ok("SCAT_beta_threshold", beta_threshold)
    return s


def _chi2_sf(stat: float, dof: int) -> float:
    """Upper tail of the chi-squared distribution (no SciPy dependency)."""
    if dof <= 0 or not np.isfinite(stat):
        return np.nan
    if stat <= 0:
        return 1.0
    return float(_gammaincc(dof / 2.0, stat / 2.0))


def _gammaincc(a: float, x: float) -> float:
    """Regularised upper incomplete gamma Q(a, x); Numerical Recipes series/CF."""
    if x < 0 or a <= 0:
        return np.nan
    if x < a + 1.0:
        # series for P(a, x)
        ap, total, term = a, 1.0 / a, 1.0 / a
        for _ in range(1000):
            ap += 1.0
            term *= x / ap
            total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a))
    # continued fraction for Q(a, x)
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) - math.lgamma(a)) * h


def _scat(exp: Experiment, fit: dict, start: int, end: int, beta_threshold: float) -> Stat:
    """SCAT (Shaar & Tauxe, 2013): do the segment and its checks fit in the box?"""
    b = fit["b"]
    if not np.isfinite(b) or b == 0:
        return undefined("SCAT", "the slope is zero")
    sigma_t = beta_threshold * abs(b)
    b1, b2 = b - 2 * sigma_t, b + 2 * sigma_t
    xbar, ybar = fit["xbar"], fit["ybar"]
    a1 = ybar - b1 * xbar     # upper y intercept
    a2 = ybar - b2 * xbar     # lower y intercept
    if b1 == 0 or b2 == 0:
        return undefined("SCAT", "the SCAT box is degenerate")
    a3, a4 = -a2 / b2, -a1 / b1
    box = np.array([[0.0, a2], [0.0, a1], [a3, 0.0], [a4, 0.0]])
    points = [(exp.x[i], exp.y[i]) for i in range(start, end + 1)]
    tmax, tmin = exp.temps[end], exp.temps[start]
    for chk in exp.ptrm_checks:
        # included when the check is inside the segment and was made from at or below Tmax
        if tmin <= exp.temps[chk.i] <= tmax and exp.temps[chk.j] <= tmax:
            points.append((chk.x, exp.y[chk.i]))
    for chk in exp.tail_checks:
        if tmin <= exp.temps[chk.i] <= tmax:
            points.append((exp.x[chk.i], chk.y))
    inside = [_point_in_polygon(px, py, box) for px, py in points]
    return ok("SCAT", bool(np.all(inside)))


def _point_in_polygon(px: float, py: float, poly: np.ndarray, tol: float = 1e-12) -> bool:
    """Ray-casting with a tolerance so that points exactly on an edge count as inside."""
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        # on the segment?
        cross = (x2 - x1) * (py - y1) - (y2 - y1) * (px - x1)
        if abs(cross) <= tol * max(1.0, abs(x2 - x1) + abs(y2 - y1)):
            if min(x1, x2) - tol <= px <= max(x1, x2) + tol and min(y1, y2) - tol <= py <= max(y1, y2) + tol:
                return True
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def directional_statistics(exp: Experiment, start: int, end: int) -> Dict[str, Stat]:
    """SPD section 4: directions, MADs, DANG, NRMdev, theta, gamma, CRM%."""
    s: Dict[str, Stat] = {}
    v = np.asarray(exp.nrm_vectors, dtype=float)[start:end + 1]
    if len(v) < 2:
        for name in ("Dec_Free", "Inc_Free", "MAD_Free", "Dec_Anc", "Inc_Anc", "MAD_Anc",
                     "alpha", "DANG", "NRM_dev", "theta", "gamma"):
            s[name] = undefined(name, "fewer than two selected steps")
        return s
    free = pca(v, anchored=False)
    anc = pca(v, anchored=True)
    s["Dec_Free"] = ok("Dec_Free", free["dec"])
    s["Inc_Free"] = ok("Inc_Free", free["inc"])
    s["MAD_Free"] = ok("MAD_Free", free["mad"])
    s["Dec_Anc"] = ok("Dec_Anc", anc["dec"])
    s["Inc_Anc"] = ok("Inc_Anc", anc["inc"])
    s["MAD_Anc"] = ok("MAD_Anc", anc["mad"])
    s["alpha"] = ok("alpha", _angle(free["direction"], anc["direction"]))

    center = free["center"]
    if np.linalg.norm(center) > 0:
        dang = _angle(free["direction"], center)
        s["DANG"] = ok("DANG", dang)
        fit = york_regression(np.asarray(exp.x)[start:end + 1], np.asarray(exp.y)[start:end + 1])
        y_int = fit["y_int"]
        s["NRM_dev"] = (ok("NRM_dev", math.sin(math.radians(dang)) * float(np.linalg.norm(center))
                           / abs(y_int) * 100.0) if y_int else undefined("NRM_dev", "Y_int is zero"))
    else:
        s["DANG"] = undefined("DANG", "the centre of mass is at the origin")
        s["NRM_dev"] = undefined("NRM_dev", "the centre of mass is at the origin")

    if exp.blab_orient is not None and np.linalg.norm(exp.blab_orient) > 0:
        s["theta"] = ok("theta", _angle(free["direction"], exp.blab_orient))
        if exp.trm_vectors is not None and len(exp.trm_vectors) > end:
            trm_end = np.asarray(exp.trm_vectors, dtype=float)[end]
            if np.linalg.norm(trm_end) > 0:
                s["gamma"] = ok("gamma", _angle(trm_end, exp.blab_orient))
            else:
                s["gamma"] = undefined("gamma", "no pTRM was gained at Tmax")
        else:
            s["gamma"] = na("gamma", "pTRM vectors were not recorded")
    else:
        s["theta"] = unavailable("theta", "the laboratory field direction is not recorded")
        s["gamma"] = unavailable("gamma", "the laboratory field direction is not recorded")

    if exp.chrm is not None and np.linalg.norm(exp.chrm) > 0:
        s["alpha_prime"] = ok("alpha_prime", _angle(anc["direction"], exp.chrm))
        s["CRM_percent"] = _crm_percent(exp, start, end, free)
    else:
        s["alpha_prime"] = unavailable(
            "alpha_prime", "needs an independent measurement of the characteristic direction")
        s["CRM_percent"] = unavailable(
            "CRM_percent", "needs an independent measurement of the characteristic direction")
    return s


def _crm_percent(exp: Experiment, start: int, end: int, free: dict) -> Stat:
    """CRM(%) of Coe et al. (1984): NRM deflected toward B_lab (SPD section 4)."""
    if exp.blab_orient is None:
        return unavailable("CRM_percent", "the laboratory field direction is not recorded")
    chrm = np.asarray(exp.chrm, dtype=float)
    blab = np.asarray(exp.blab_orient, dtype=float)
    phi2 = math.radians(_angle(chrm, blab))
    if math.sin(phi2) == 0:
        return undefined("CRM_percent", "the reference direction is parallel to B_lab")
    v = np.asarray(exp.nrm_vectors, dtype=float)[start:end + 1]
    y = np.asarray(exp.y, dtype=float)[start:end + 1]
    crm = []
    for k, vec in enumerate(v):
        phi1 = math.radians(_angle(vec, chrm))
        crm.append(y[k] * math.sin(phi1) / math.sin(phi2))
    fit = york_regression(np.asarray(exp.x)[start:end + 1], y)
    dxp = fit["delta_x_prime"]
    if not dxp:
        return undefined("CRM_percent", "the fit has no pTRM extent")
    return ok("CRM_percent", 100.0 * max(crm) / dxp)


def ptrm_check_statistics(exp: Experiment, start: int, end: int) -> Dict[str, Stat]:
    """SPD section 5: pTRM check statistics, including delta_pal."""
    names = ("check_percent", "dCK", "DRAT", "maxDEV", "Pck", "CDRAT", "CDRAT_prime",
             "DRATS", "DRATS_prime", "mean_DRAT", "mean_DRAT_prime", "mean_DEV",
             "mean_DEV_prime", "delta_pal")
    s: Dict[str, Stat] = {}
    tmax = exp.temps[end]
    used = [c for c in exp.ptrm_checks if exp.temps[c.i] <= tmax and exp.temps[c.j] <= tmax]
    s["n_pTRM"] = ok("n_pTRM", len(used))
    if not used:
        for name in names:
            s[name] = na(name, "no pTRM checks were performed at or below Tmax")
        return s
    fit = york_regression(np.asarray(exp.x)[start:end + 1], np.asarray(exp.y)[start:end + 1])
    x_int, line_len, dxp = fit["x_int"], fit["line_length"], fit["delta_x_prime"]
    x_end = float(exp.x[end])
    diffs = np.array([c.x - exp.x[c.i] for c in used], dtype=float)
    rel = np.array([(c.x - exp.x[c.i]) / exp.x[c.i] if exp.x[c.i] else np.nan for c in used], dtype=float)
    n_chk = len(used)
    maxabs = float(np.max(np.abs(diffs)))

    s["check_percent"] = (ok("check_percent", 100.0 * float(np.nanmax(np.abs(rel))))
                          if np.any(np.isfinite(rel)) else undefined("check_percent", "a check TRM is zero"))
    s["dCK"] = ok("dCK", 100.0 * maxabs / abs(x_int)) if x_int else undefined("dCK", "X_int is zero")
    s["DRAT"] = ok("DRAT", 100.0 * maxabs / line_len) if line_len else undefined("DRAT", "the fit has no length")
    s["maxDEV"] = ok("maxDEV", 100.0 * maxabs / dxp) if dxp else undefined("maxDEV", "the fit has no pTRM extent")
    s["Pck"] = ok("Pck", 100.0 * maxabs / x_end) if x_end else undefined("Pck", "no pTRM was gained at Tmax")

    total, total_abs = float(np.sum(diffs)), float(np.sum(np.abs(diffs)))
    if line_len:
        s["CDRAT"] = ok("CDRAT", abs(100.0 * total / line_len))
        s["CDRAT_prime"] = ok("CDRAT_prime", abs(100.0 * total_abs / line_len))
        s["mean_DRAT"] = ok("mean_DRAT", abs(100.0 * total / line_len / n_chk))
        s["mean_DRAT_prime"] = ok("mean_DRAT_prime", 100.0 * total_abs / line_len / n_chk)
    else:
        for name in ("CDRAT", "CDRAT_prime", "mean_DRAT", "mean_DRAT_prime"):
            s[name] = undefined(name, "the fit has no length")
    if x_end:
        s["DRATS"] = ok("DRATS", abs(100.0 * total / x_end))
        s["DRATS_prime"] = ok("DRATS_prime", abs(100.0 * total_abs / x_end))
    else:
        s["DRATS"] = undefined("DRATS", "no pTRM was gained at Tmax")
        s["DRATS_prime"] = undefined("DRATS_prime", "no pTRM was gained at Tmax")
    if dxp:
        s["mean_DEV"] = ok("mean_DEV", abs(100.0 * total / dxp / n_chk))
        s["mean_DEV_prime"] = ok("mean_DEV_prime", 100.0 * total_abs / dxp / n_chk)
    else:
        s["mean_DEV"] = undefined("mean_DEV", "the fit has no pTRM extent")
        s["mean_DEV_prime"] = undefined("mean_DEV_prime", "the fit has no pTRM extent")

    s["delta_pal"] = _delta_pal(exp, start, end, fit)
    return s


def _delta_pal(exp: Experiment, start: int, end: int, fit: dict) -> Stat:
    """delta_pal (Leonhardt et al., 2004a): slope change after correcting for alteration.

    The vector difference between each pTRM check and the original pTRM is
    accumulated along the experiment, added to the pTRM vectors, and the
    Arai slope recomputed. Needs the pTRM *vectors*; with scalar checks only,
    it cannot be computed.

    Note on the sign: SPD v1.2.0 prints the vector difference as
    ``TRM_l - pTRM check_l``, the opposite way round from the scalar
    ``dpTRM = check - x`` used everywhere else in the document. The SPD
    reference implementation and the published calibration table both use
    ``check - TRM``, which is what is implemented here -- it reproduces the
    20 calibration values exactly, the printed form does not. See
    ``docs/paleointensity_literature_audit.md``.
    """
    if exp.trm_vectors is None:
        return na("delta_pal", "the pTRM vectors were not recorded")
    checks = [c for c in exp.ptrm_checks if c.vector is not None]
    if not checks:
        return na("delta_pal", "the pTRM check vectors were not recorded")
    trm = np.asarray(exp.trm_vectors, dtype=float)
    to_sum = np.zeros_like(trm)
    for c in checks:
        if 0 <= c.i < len(trm):
            to_sum[c.i] = np.asarray(c.vector, dtype=float) - trm[c.i]
    cumulative = np.cumsum(to_sum, axis=0)
    corr = np.zeros(len(trm))
    for j in range(1, len(trm)):
        corr[j] = float(np.linalg.norm(trm[j] + cumulative[j - 1]))
    xs_corr = corr[start:end + 1]
    ys = np.asarray(exp.y, dtype=float)[start:end + 1]
    if np.all(xs_corr == xs_corr[0]):
        return undefined("delta_pal", "the corrected pTRMs are all equal")
    corr_fit = york_regression(xs_corr, ys)
    b, b_star = fit["b"], corr_fit["b"]
    if not b:
        return undefined("delta_pal", "b is zero")
    return ok("delta_pal", abs(100.0 * (b - b_star) / b))


def tail_check_statistics(exp: Experiment, start: int, end: int) -> Dict[str, Stat]:
    """SPD section 6: pTRM tail check statistics, including delta_t_star."""
    s: Dict[str, Stat] = {}
    tmax = exp.temps[end]
    used = [c for c in exp.tail_checks if exp.temps[c.i] <= tmax]
    s["n_tail"] = ok("n_tail", len(used))
    if not used:
        for name in ("DRAT_tail", "dTR", "MD_VDS", "delta_t_star"):
            s[name] = na(name, "no pTRM tail checks were performed at or below Tmax")
        return s
    fit = york_regression(np.asarray(exp.x)[start:end + 1], np.asarray(exp.y)[start:end + 1])
    y_int, x_int, line_len = fit["y_int"], fit["x_int"], fit["line_length"]
    diffs = np.array([c.y - exp.y[c.i] for c in used], dtype=float)
    maxabs = float(np.max(np.abs(diffs)))
    s["DRAT_tail"] = ok("DRAT_tail", 100.0 * maxabs / line_len) if line_len else \
        undefined("DRAT_tail", "the fit has no length")
    s["dTR"] = ok("dTR", 100.0 * maxabs / abs(y_int)) if y_int else undefined("dTR", "Y_int is zero")
    vds = vector_difference_sum(exp.nrm_vectors)
    s["MD_VDS"] = ok("MD_VDS", 100.0 * maxabs / vds) if vds else undefined("MD_VDS", "VDS is zero")
    s["delta_t_star"] = _delta_t_star(exp, end, fit)
    return s


#: ThellierTool v4.22 angular limits for delta_t_star, adopted by SPD.
DT_STAR_LIM_LOWER = 0.175      # radians (~10 degrees)
DT_STAR_LIM_UPPER = 2.968      # radians (~170 degrees)


def _delta_t_star(exp: Experiment, end: int, fit: dict) -> Stat:
    """delta_t_star: pTRM tail corrected for angular dependence (SPD section 6).

    Leonhardt et al. (2004a, 2004b). Needs the tail-check *vectors* and the
    laboratory field direction, and is defined only when B_lab lies along a
    specimen axis, which is how it is always applied. It does **not** need an
    independent paleointensity estimate: the legacy PmagPy/SPD python port
    returned -999 here because the statistic was never implemented, which is
    what issue #246 reported.
    """
    if exp.blab_orient is None:
        return unavailable("delta_t_star", "the laboratory field direction is not recorded")
    vectors = [c for c in exp.tail_checks if c.vector is not None and exp.temps[c.i] <= exp.temps[end]]
    if not vectors:
        return na("delta_t_star", "the pTRM tail check vectors were not recorded")
    blab = np.asarray(exp.blab_orient, dtype=float)
    norm = np.linalg.norm(blab)
    if norm == 0:
        return unavailable("delta_t_star", "the laboratory field direction is not recorded")
    unit = blab / norm
    axis = int(np.argmax(np.abs(unit)))
    if abs(abs(unit[axis]) - 1.0) > 1e-6:
        return na("delta_t_star",
                  "delta_t* is defined only for a laboratory field along a specimen axis")
    others = [k for k in range(3) if k != axis]
    b, y_int, x_int = fit["b"], fit["y_int"], fit["x_int"]
    if not y_int:
        return undefined("delta_t_star", "Y_int is zero")
    nrm = np.asarray(exp.nrm_vectors, dtype=float)
    t_star = []
    for c in vectors:
        n_vec = nrm[c.i]
        t_vec = np.asarray(c.vector, dtype=float)
        n_norm = np.linalg.norm(n_vec)
        if n_norm == 0:
            continue
        theta = math.radians(_angle(n_vec / n_norm, unit))
        d_h = math.hypot(n_vec[others[0]], n_vec[others[1]]) - math.hypot(t_vec[others[0]], t_vec[others[1]])
        d_z = n_vec[axis] - t_vec[axis]
        f_inc = math.degrees(math.asin(max(-1.0, min(1.0, unit[axis]))))
        n_inc = math.degrees(math.atan2(n_vec[axis], math.hypot(n_vec[others[0]], n_vec[others[1]])))
        inc_diff = f_inc - n_inc
        if DT_STAR_LIM_LOWER < theta < DT_STAR_LIM_UPPER:
            term = d_h / math.tan(theta)
            value = ((-d_z + term) if inc_diff > 0 else (d_z - term)) * abs(b) * 100.0 / abs(y_int)
        elif theta <= DT_STAR_LIM_LOWER:
            value = 0.0
        else:
            denom = abs(x_int) + abs(y_int)
            if not denom:
                continue
            value = -d_z * 100.0 / denom
        t_star.append(value)
    if not t_star:
        return na("delta_t_star", "no usable pTRM tail check vectors at or below Tmax")
    best = max(t_star)
    return ok("delta_t_star", best if best > 0 else 0.0)


def additivity_check_statistics(exp: Experiment, start: int, end: int) -> Dict[str, Stat]:
    """SPD section 7: additivity checks."""
    s: Dict[str, Stat] = {}
    tmax = exp.temps[end]
    used = [c for c in exp.additivity_checks if exp.temps[c.i] <= tmax and exp.temps[c.j] <= tmax]
    s["n_add"] = ok("n_add", len(used))
    if not used:
        s["dAC"] = na("dAC", "no additivity checks were performed at or below Tmax")
        return s
    fit = york_regression(np.asarray(exp.x)[start:end + 1], np.asarray(exp.y)[start:end + 1])
    x_int = fit["x_int"]
    diffs = np.array([c.x - exp.x[c.i] for c in used], dtype=float)
    s["dAC"] = (ok("dAC", 100.0 * float(np.max(np.abs(diffs))) / abs(x_int)) if x_int
                else undefined("dAC", "X_int is zero"))
    return s


def all_statistics(exp: Experiment, start: int, end: int,
                   beta_threshold: float = 0.1) -> Dict[str, Stat]:
    """Every SPD statistic for one selection, in one dictionary."""
    s: Dict[str, Stat] = {}
    s.update(arai_statistics(exp, start, end, beta_threshold))
    s.update(directional_statistics(exp, start, end))
    s.update(ptrm_check_statistics(exp, start, end))
    s.update(tail_check_statistics(exp, start, end))
    s.update(additivity_check_statistics(exp, start, end))
    return s


# ---------------------------------------------------------------------------
# Corrections (SPD sections 8 and 9)
# ---------------------------------------------------------------------------
def anisotropy_tensor(s6: Sequence[float]) -> np.ndarray:
    """The 3x3 anisotropy tensor from the six independent elements s1..s6."""
    s1, s2, s3, s4, s5, s6_ = [float(v) for v in s6]
    return np.array([[s1, s4, s6_],
                     [s4, s2, s5],
                     [s6_, s5, s3]])


#: the standard measurement positions, as (declination, inclination) of the
#: applied field in specimen coordinates, for 6-, 9- and 15-position designs
ANISOTROPY_POSITIONS = {
    6: [(0., 0.), (90., 0.), (0., 90.), (180., 0.), (270., 0.), (0., -90.)],
    9: [(315., 0.), (225., 0.), (180., 0.), (90., -45.), (270., -45.),
        (270., 0.), (180., 45.), (180., -45.), (0., -90.)],
    15: [(315., 0.), (225., 0.), (180., 0.), (135., 0.), (45., 0.),
         (90., -45.), (270., -45.), (270., 0.), (270., 45.), (90., 45.),
         (180., 45.), (180., -45.), (0., -90.), (0., -45.), (0., 45.)],
}


def anisotropy_design_matrix(positions=None) -> np.ndarray:
    """The 3N x 6 design matrix A of an N-position anisotropy experiment.

    SPD v1.2 corrected the last two elements of row 6 from ``P3,3``/``P3,1`` to
    ``P2,2``/``P2,1`` (v1.2 change 2), so that the three rows of each position
    read ``[a 0 0 b 0 c]``, ``[0 b 0 a c 0]``, ``[0 0 c 0 b a]``. That is what
    is built here, and it agrees with the matrix the legacy Thellier GUI uses.

    ``positions`` may be unit vectors (N x 3) or ``(dec, inc)`` pairs; with
    ``None`` the six-position design is used.
    """
    if positions is None:
        positions = ANISOTROPY_POSITIONS[6]
    p = np.asarray(positions, dtype=float)
    if p.ndim != 2 or p.shape[1] not in (2, 3):
        raise ValueError("positions must be N x 3 unit vectors or N x 2 (dec, inc) pairs")
    if p.shape[1] == 2:
        p = np.array([dir_to_cart(d, i, 1.0) for d, i in p])
    n = len(p)
    a = np.zeros((3 * n, 6))
    for i in range(n):
        k = 3 * i
        a[k + 0] = [p[i, 0], 0., 0., p[i, 1], 0., p[i, 2]]
        a[k + 1] = [0., p[i, 1], 0., p[i, 0], p[i, 2], 0.]
        a[k + 2] = [0., 0., p[i, 2], 0., p[i, 1], p[i, 0]]
    return a


def fit_anisotropy_tensor(measurements: np.ndarray, positions=None) -> np.ndarray:
    """Least-squares s (6 elements) from the N x 3 measured remanence vectors."""
    m = np.asarray(measurements, dtype=float).reshape(-1)
    a = anisotropy_design_matrix(positions)
    if len(m) != a.shape[0]:
        raise ValueError(f"expected {a.shape[0]} measurement components, got {len(m)}")
    s, *_ = np.linalg.lstsq(a, m, rcond=None)
    return s


def anisotropy_residual_sigma(measurements: np.ndarray, s6: Sequence[float],
                              positions=None) -> Tuple[float, int]:
    """Hext's sigma and degrees of freedom for a fitted anisotropy tensor.

    ``sigma = sqrt(S / (3N - 6))`` where S is the sum of squared differences
    between the measured components (normalised by the tensor trace) and those
    the tensor predicts (Hext, 1963; Jelinek, 1978).
    """
    raw = np.asarray(measurements, dtype=float).reshape(-1, 3)
    if positions is None:
        positions = ANISOTROPY_POSITIONS[len(raw)]
    p = np.asarray(positions, dtype=float)
    if p.shape[1] == 2:
        p = np.array([dir_to_cart(d, i, 1.0) for d, i in p])
    n = len(p)
    nf = 3 * n - 6
    if nf <= 0:
        return np.nan, nf
    # ``s6`` is normalised to unit trace, so the measurements must be divided
    # by the trace of the tensor they imply before they can be differenced
    trace = _fit_trace(raw, p)
    if trace == 0:
        return np.nan, nf
    chi = anisotropy_tensor(s6)
    predicted = np.array([chi @ p[i] for i in range(n)])
    resid = raw / trace - predicted
    s = float(np.sum(resid ** 2))
    return (math.sqrt(s / nf) if s > 0 else 0.0), nf


def _fit_trace(measurements: np.ndarray, positions: np.ndarray) -> float:
    """The trace of the unnormalised tensor implied by these measurements."""
    a = anisotropy_design_matrix(positions)
    s, *_ = np.linalg.lstsq(a, np.asarray(measurements, dtype=float).reshape(-1), rcond=None)
    return float(np.sum(s[:3]))


def hext_statistics(s6: Sequence[float], sigma: float, nf: int) -> dict:
    """Hext (1963) anisotropy statistics: eigenvalues, F, F12, F23 and F_crit."""
    out = {"F": np.nan, "F12": np.nan, "F23": np.nan, "F_crit": np.nan,
           "tau": None, "degree": np.nan, "passes_ftest": None}
    chi = anisotropy_tensor(s6)
    tau = np.linalg.eigvalsh(chi)[::-1]
    out["tau"] = [float(t) for t in tau]
    out["degree"] = float(tau[0] / tau[2]) if tau[2] else np.nan
    if not np.isfinite(sigma) or sigma <= 0 or nf <= 0:
        return out
    chibar = float(np.sum(np.asarray(s6, dtype=float)[:3])) / 3.0
    out["F"] = 0.4 * (float(np.sum(tau ** 2)) - 3 * chibar ** 2) / sigma ** 2
    out["F12"] = 0.5 * ((tau[0] - tau[1]) / sigma) ** 2
    out["F23"] = 0.5 * ((tau[1] - tau[2]) / sigma) ** 2
    out["F_crit"] = f_critical(5, nf)
    out["passes_ftest"] = bool(out["F"] >= out["F_crit"])
    return out


def f_critical(d1: int, d2: int, alpha: float = 0.05) -> float:
    """The upper (1 - alpha) critical value of the F distribution, by bisection."""
    if d1 <= 0 or d2 <= 0:
        return np.nan
    target = 1.0 - alpha

    def cdf(x):
        if x <= 0:
            return 0.0
        return _betainc(d1 / 2.0, d2 / 2.0, d1 * x / (d1 * x + d2))
    lo, hi = 0.0, 10.0
    while cdf(hi) < target and hi < 1e6:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if cdf(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def anisotropy_correction_factor(s6: Sequence[float], chrm: Sequence[float],
                                 blab_orient: Sequence[float]) -> dict:
    """Anisotropy correction factor c (SPD section 8, after Veitch et al., 1984).

    ``c = |chi B_lab_hat| / |chi B_anc_hat|`` where ``B_anc_hat`` is the unit
    field direction that would produce the observed ChRM. The corrected
    intensity is ``B_anc = c * B_lab * |b|``.

    Returns ``c``, the inferred ancient field direction ``b_anc``, and the
    tensor eigenvalues (for reporting the degree of anisotropy).
    """
    chi = anisotropy_tensor(s6)
    m_hat = np.asarray(chrm, dtype=float)
    m_norm = np.linalg.norm(m_hat)
    if m_norm == 0:
        raise ValueError("the ChRM direction is a zero vector")
    m_hat = m_hat / m_norm
    lab = np.asarray(blab_orient, dtype=float)
    lab_norm = np.linalg.norm(lab)
    if lab_norm == 0:
        raise ValueError("the laboratory field direction is a zero vector")
    lab = lab / lab_norm
    b_anc = np.linalg.solve(chi, m_hat)
    b_anc = b_anc / np.linalg.norm(b_anc)
    trm_lab = chi @ lab
    trm_anc = chi @ b_anc
    denom = float(np.linalg.norm(trm_anc))
    if denom == 0:
        raise ValueError("the anisotropy tensor is singular in the ancient field direction")
    c = float(np.linalg.norm(trm_lab)) / denom
    tau = np.linalg.eigvalsh(chi)[::-1]
    return {"c": c, "b_anc": b_anc, "tau": tau,
            "degree": float(tau[0] / tau[2]) if tau[2] else np.nan}


def nlt_correction(b: float, blab: float, a2: float, c: float = 1.0) -> float:
    """Non-linear TRM correction (Selkin et al., 2007; SPD section 9).

    ``B_anc = atanh(c |b| tanh(A2 B_lab)) / A2``. With ``c`` given, the
    combined anisotropy + non-linear correction of SPD section 9.2 is applied.
    Falls back to the linear estimate when A2 is zero or the argument leaves
    the domain of atanh.
    """
    if not a2:
        return c * abs(b) * blab
    arg = c * abs(b) * math.tanh(a2 * blab)
    if not -1.0 < arg < 1.0:
        return np.nan
    return math.atanh(arg) / a2


def fit_nlt_coefficients(fields: Sequence[float], moments: Sequence[float]) -> Tuple[float, float]:
    """Fit ``TRM = A1 tanh(A2 B)`` to a TRM acquisition series.

    Uses a simple damped Gauss-Newton so that the module keeps no SciPy
    dependency; returns ``(A1, A2)``.
    """
    b = np.asarray(fields, dtype=float)
    m = np.asarray(moments, dtype=float)
    good = np.isfinite(b) & np.isfinite(m)
    b, m = b[good], m[good]
    if len(b) < 2:
        return np.nan, np.nan
    # initial guess: linear slope through the origin, weak-field limit
    slope = float(np.sum(b * m) / np.sum(b * b)) if np.sum(b * b) else 1.0
    a1 = float(np.max(np.abs(m))) if np.max(np.abs(m)) else 1.0
    a2 = slope / a1 if a1 else 1.0
    for _ in range(200):
        t = np.tanh(a2 * b)
        resid = m - a1 * t
        j1 = t
        j2 = a1 * b * (1 - t ** 2)
        jac = np.column_stack((j1, j2))
        try:
            delta, *_ = np.linalg.lstsq(jac, resid, rcond=None)
        except np.linalg.LinAlgError:
            break
        a1 += delta[0]
        a2 += delta[1]
        if np.linalg.norm(delta) < 1e-12 * (abs(a1) + abs(a2) + 1e-30):
            break
    return float(a1), float(a2)


#: A cooling-rate experiment whose repeat at the laboratory rate differs by more
#: than this percentage is treated as altered and yields no correction.
COOLING_RATE_ALTERATION_LIMIT = 5.0


def cooling_rate_factor(rates: Sequence[float], moments: Sequence[float],
                        ancient_rate: float,
                        alteration_check: Optional[Tuple[float, float]] = None) -> dict:
    """Cooling-rate correction factor from a TRM vs ln(cooling rate) experiment.

    TRM is acquired at several laboratory cooling rates; a straight line in
    ``ln(lab rate / rate)`` is extrapolated to the ancient cooling rate and the
    correction factor is ``1 / y0`` where ``y0`` is the extrapolated TRM
    normalised by the TRM at the fastest (laboratory) rate, so that
    ``B_corrected = factor x B_uncorrected`` (Halgedahl et al., 1980;
    Chauvin et al., 2000; implemented as in Shaar & Tauxe, 2013 and the legacy
    Thellier GUI, whose values this reproduces).

    Args:
        rates: laboratory cooling rates, K/min.
        moments: the TRM acquired at each rate.
        ancient_rate: the estimated ancient cooling rate, K/min.
        alteration_check: ``(rate, moment)`` of the repeat measurement at the
            laboratory rate. Its scatter against the other laboratory-rate
            measurements is the alteration test.

    Returns ``factor``, ``slope``, ``intercept``, ``alteration`` (%) and
    ``flag`` -- ``'calculated'``, ``'altered'`` or ``'insufficient data'``.
    """
    r = list(np.asarray(rates, dtype=float))
    m = list(np.asarray(moments, dtype=float))
    if alteration_check is not None:
        r.append(float(alteration_check[0]))
        m.append(float(alteration_check[1]))
    r_arr, m_arr = np.asarray(r, dtype=float), np.asarray(m, dtype=float)
    good = np.isfinite(r_arr) & np.isfinite(m_arr) & (r_arr > 0)
    r_arr, m_arr = r_arr[good], m_arr[good]
    out = {"factor": np.nan, "slope": np.nan, "intercept": np.nan,
           "alteration": np.nan, "flag": "insufficient data"}
    if len(r_arr) < 3 or not (ancient_rate > 0):
        return out
    lab_rate = float(np.max(r_arr))
    fast = m_arr[r_arr == lab_rate]
    if len(fast) == 0 or float(np.mean(fast)) == 0:
        return out
    norm = m_arr / float(np.mean(fast))
    x = np.log(lab_rate / r_arr)
    slope, intercept = np.polyfit(x, norm, 1)
    x0 = math.log(lab_rate / ancient_rate)
    y0 = slope * x0 + intercept
    hi, lo = float(np.max(fast)), float(np.min(fast))
    mid = (hi + lo) / 2.0
    alteration = 0.0 if mid == 0 else 100.0 * abs((hi - lo) / mid)
    out.update(slope=float(slope), intercept=float(intercept), alteration=alteration)
    if alteration > COOLING_RATE_ALTERATION_LIMIT:
        out["flag"] = "altered"
        return out
    if y0 == 0:
        return out
    out["factor"] = float(1.0 / y0)
    out["flag"] = "calculated"
    return out


def alteration_percent(first: float, repeat: float) -> float:
    """delta_TRM: percentage difference between a measurement and its repeat.

    Used for ``delta_TRM_anis`` (SPD section 8.3) and ``delta_TRM_NLT``
    (section 9.3).
    """
    if not first:
        return np.nan
    return abs(first - repeat) / abs(first) * 100.0


# ---------------------------------------------------------------------------
# Group-level statistics (SPD section 10)
# ---------------------------------------------------------------------------
def group_statistics(values: Sequence[float], weights: Optional[Sequence[float]] = None,
                     b_max: Optional[float] = None, s_max: Optional[float] = None,
                     alpha: float = 0.05) -> Dict[str, Stat]:
    """SPD section 10: mean, scatter and the scatter tests of several estimates."""
    v = np.asarray([x for x in values if x is not None and np.isfinite(x)], dtype=float)
    n = len(v)
    s: Dict[str, Stat] = {"N": ok("N", n)}
    if n == 0:
        for name in ("mean", "sd", "weighted_mean", "weighted_sd", "dB_percent", "dBN_percent"):
            s[name] = undefined(name, "no accepted estimates")
        return s
    mean = float(np.mean(v))
    s["mean"] = ok("mean", mean)
    s["sd"] = ok("sd", float(np.std(v, ddof=1))) if n > 1 else undefined("sd", "N = 1")
    if weights is not None:
        w = np.asarray(weights, dtype=float)
        w = w[np.isfinite(w)]
        if len(w) == n and np.sum(w) > 0:
            wm = float(np.sum(w * v) / np.sum(w))
            s["weighted_mean"] = ok("weighted_mean", wm)
            if n > 1:
                wsd = math.sqrt(n * float(np.sum(w * (v - wm) ** 2)) / ((n - 1) * float(np.sum(w))))
                s["weighted_sd"] = ok("weighted_sd", wsd)
            else:
                s["weighted_sd"] = undefined("weighted_sd", "N = 1")
        else:
            s["weighted_mean"] = undefined("weighted_mean", "the weights do not match the estimates")
            s["weighted_sd"] = undefined("weighted_sd", "the weights do not match the estimates")
    if n > 1 and mean:
        sd = float(np.std(v, ddof=1))
        s["dB_percent"] = ok("dB_percent", 100.0 * sd / mean)
        s["dBN_percent"] = _scatter_upper_bound(n, mean, sd, alpha)
        if b_max is not None:
            s["p_dB"] = _p_scatter(n, mean, sd, b_max)
        if s_max is not None:
            s["p_s"] = (ok("p_s", _chi2_cdf((n - 1) * s_max ** 2 / sd ** 2, n - 1))
                        if sd else undefined("p_s", "the scatter is zero"))
    else:
        s["dB_percent"] = undefined("dB_percent", "N = 1" if n == 1 else "the mean is zero")
        s["dBN_percent"] = undefined("dBN_percent", "N = 1" if n == 1 else "the mean is zero")
    return s


def _chi2_cdf(stat: float, dof: int) -> float:
    if dof <= 0 or not np.isfinite(stat):
        return np.nan
    return 1.0 - _chi2_sf(stat, dof)


def _noncentral_t_cdf(t: float, dof: int, ncp: float, terms: int = 400) -> float:
    """CDF of the noncentral t distribution (Lenth, 1989 series)."""
    if dof <= 0 or not np.isfinite(t):
        return np.nan
    if t < 0:
        return 1.0 - _noncentral_t_cdf(-t, dof, -ncp, terms)
    x = t * t / (t * t + dof)
    total = 0.0
    half_ncp2 = ncp * ncp / 2.0
    log_norm = -half_ncp2
    for j in range(terms):
        log_pj = log_norm + j * math.log(half_ncp2) - math.lgamma(j + 1) if half_ncp2 > 0 else \
            (log_norm if j == 0 else -np.inf)
        log_qj = (log_norm + math.log(ncp / math.sqrt(2.0)) + j * math.log(half_ncp2)
                  - math.lgamma(j + 1.5)) if (half_ncp2 > 0 or j == 0) and ncp > 0 else -np.inf
        pj = math.exp(log_pj) if log_pj > -700 else 0.0
        qj = math.exp(log_qj) if log_qj > -700 else 0.0
        if pj == 0.0 and qj == 0.0 and j > 5:
            break
        ip = _betainc(j + 0.5, dof / 2.0, x)
        iq = _betainc(j + 1.0, dof / 2.0, x)
        total += pj * ip + qj * iq
    phi = 0.5 * (1.0 + math.erf(-ncp / math.sqrt(2.0)))
    return min(1.0, max(0.0, phi + 0.5 * total))


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta I_x(a, b) by continued fraction."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log(1 - x))
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbeta + b * math.log(1 - x) + a * math.log(x)) * _betacf(b, a, 1 - x) / b


def _betacf(a: float, b: float, x: float, itmax: int = 300, eps: float = 1e-14) -> float:
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, itmax + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def _p_scatter(n: int, mean: float, sd: float, b_max: float) -> Stat:
    """p_dB (Paterson et al., 2010a): probability the scatter is below b_max."""
    if sd <= 0 or b_max <= 0:
        return undefined("p_dB", "the scatter or the limit is zero")
    ncp = mean * math.sqrt(n) / sd
    t = math.sqrt(n) / b_max
    return ok("p_dB", _noncentral_t_cdf(t, n - 1, ncp))


def _scatter_upper_bound(n: int, mean: float, sd: float, alpha: float = 0.05) -> Stat:
    """dBN(%) (Paterson et al., 2010a): the 95% upper bound on the scatter.

    ``dBN = 100 sqrt(N) / t_nc(1-alpha; N-1; mean sqrt(N)/s)``. The noncentral
    t critical value is found by bisection on the CDF, which avoids a SciPy
    dependency in this module.
    """
    if sd <= 0 or n < 2:
        return undefined("dBN_percent", "the scatter is zero" if sd <= 0 else "N = 1")
    ncp = mean * math.sqrt(n) / sd
    target = 1.0 - alpha
    lo, hi = -50.0, max(50.0, 5 * abs(ncp) + 50.0)
    for _ in range(200):
        mid = (lo + hi) / 2
        if _noncentral_t_cdf(mid, n - 1, ncp) < target:
            lo = mid
        else:
            hi = mid
    tnc = (lo + hi) / 2
    if tnc == 0:
        return undefined("dBN_percent", "the critical value is zero")
    return ok("dBN_percent", 100.0 * math.sqrt(n) / tnc)


# ---------------------------------------------------------------------------
# Catalogue: what each statistic is, in what units, and where it comes from
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class StatSpec:
    """Presentation and provenance metadata for one statistic."""
    key: str
    label: str
    category: str
    definition: str
    equation: str = ""
    units: str = ""
    citation: str = ""
    doi: str = ""
    magic_column: str = ""
    better: str = ""          # 'low', 'high', 'bool' or '' when no sense of good
    decimals: int = 3


def _spec(key, label, category, definition, equation="", units="", citation="", doi="",
          magic_column="", better="", decimals=3) -> Tuple[str, StatSpec]:
    return key, StatSpec(key, label, category, definition, equation, units, citation, doi,
                         magic_column, better, decimals)


SPD14 = "Paterson et al. (2014); SPD v1.2.0"
SPD14_DOI = "10.1002/2013GC005135"

CATALOG: Dict[str, StatSpec] = dict([
    # --- Arai plot ---------------------------------------------------------
    _spec("n", "n", "Arai fit", "Number of Arai points in the selected segment.",
          "n = end - start + 1", "", SPD14, SPD14_DOI, "int_n_measurements", "high", 0),
    _spec("nmax", "n max", "Arai fit", "Total number of Arai plot points.", "", "", SPD14, SPD14_DOI, "", "", 0),
    _spec("Tmin", "T min", "Arai fit", "Lowest treatment step of the selected segment.", "", "K",
          SPD14, SPD14_DOI, "meas_step_min", "", 0),
    _spec("Tmax", "T max", "Arai fit", "Highest treatment step of the selected segment.", "", "K",
          SPD14, SPD14_DOI, "meas_step_max", "", 0),
    _spec("b", "b", "Arai fit", "Slope of the best-fit line, standardized major axis.",
          "b = sign(Sxy) sqrt(Syy / Sxx)", "", SPD14, SPD14_DOI, "int_b", "", 3),
    _spec("sigma_b", "sigma b", "Arai fit", "Standard error of the slope (SPD v1.2 uses b, not |b|).",
          "sigma_b = sqrt((2 Syy - 2 b Sxy) / ((n-2) Sxx))", "", SPD14, SPD14_DOI, "int_b_sigma", "low", 3),
    _spec("B_anc", "B anc", "Arai fit", "Paleointensity estimate before corrections.",
          "B_anc = |b| B_lab", "uT", SPD14, SPD14_DOI, "int_abs", "", 1),
    _spec("sigma_B", "sigma B", "Arai fit", "Standard error of the paleointensity estimate.",
          "sigma_B = sigma_b B_lab", "uT", SPD14, SPD14_DOI, "int_abs_sigma", "low", 1),
    _spec("Y_int", "Y int", "Arai fit", "NRM-axis intercept of the best-fit line.",
          "Y_int = ybar - b xbar", "", SPD14, SPD14_DOI, "", "", 3),
    _spec("X_int", "X int", "Arai fit", "pTRM-axis intercept of the best-fit line.",
          "X_int = -Y_int / b", "", SPD14, SPD14_DOI, "", "", 3),
    _spec("VDS", "VDS", "Arai fit", "Vector difference sum of the whole NRM.",
          "VDS = |NRM_nmax| + sum |NRM_i+1 - NRM_i|", "", SPD14, SPD14_DOI, "", "", 3),
    _spec("f", "f", "Arai fit", "NRM fraction used for the best-fit line (Coe et al., 1978).",
          "f = dy' / |Y_int|", "", SPD14, SPD14_DOI, "int_f", "high", 3),
    _spec("f_vds", "f vds", "Arai fit", "NRM fraction relative to the vector difference sum.",
          "f_vds = dy' / VDS", "", SPD14, SPD14_DOI, "int_fvds", "high", 3),
    _spec("FRAC", "FRAC", "Arai fit", "NRM fraction by vector difference sum (Shaar & Tauxe, 2013).",
          "FRAC = sum_{start}^{end-1} |NRM_i+1 - NRM_i| / VDS", "", SPD14, SPD14_DOI, "int_frac", "high", 3),
    _spec("beta", "beta", "Arai fit", "Relative scatter about the best-fit line.",
          "beta = sigma_b / |b|", "", SPD14, SPD14_DOI, "int_b_beta", "low", 3),
    _spec("g", "g", "Arai fit", "Gap factor: average spacing of the selected points.",
          "g = 1 - sum (y'_i+1 - y'_i)^2 / dy'^2", "", SPD14, SPD14_DOI, "int_g", "high", 3),
    _spec("GAP_MAX", "GAP-MAX", "Arai fit", "Largest single gap, by vector arithmetic.",
          "GAP-MAX = max |NRM_i+1 - NRM_i| / sum |NRM_i+1 - NRM_i|", "", SPD14, SPD14_DOI,
          "int_gmax", "low", 3),
    _spec("q", "q", "Arai fit", "Quality factor of Coe et al. (1978).", "q = f g / beta", "",
          SPD14, SPD14_DOI, "int_q", "high", 1),
    _spec("w", "w", "Arai fit", "Weighting factor of Prevot et al. (1985).", "w = q / sqrt(n-2)", "",
          SPD14, SPD14_DOI, "int_w", "high", 1),
    _spec("k", "k", "Arai fit", "Signed curvature of the best-fit circle to all the data.",
          "k = 1/r, signed by the circle centre relative to the data centroid", "",
          "Paterson (2011)", "10.1029/2011JB008369", "int_k", "low", 3),
    _spec("k_prime", "k'", "Arai fit", "Curvature of the best-fit circle to the selected segment.",
          "as k, over the selected points only", "", "Paterson (2011)", "10.1029/2011JB008369",
          "int_k_prime", "low", 3),
    _spec("SSE", "SSE", "Arai fit", "Quality of the circle fit used for k.",
          "SSE = sum (sqrt((x_i-a)^2 + (y_i-b)^2) - r)^2", "", "Paterson (2011)",
          "10.1029/2011JB008369", "int_k_sse", "low", 3),
    _spec("SSE_prime", "SSE'", "Arai fit", "Quality of the circle fit used for k'.", "", "",
          "Paterson (2011)", "10.1029/2011JB008369", "int_k_prime_sse", "low", 3),
    _spec("Ziggie", "Ziggie", "Arai fit",
          "Zig-zag of the selected segment: log ratio of the polyline length to the best-fit arc. "
          "Proposed criterion Ziggie <= 0.1 for IZZI experiments.",
          "Ziggie = ln(cumulative line length / best-fit arc length)", "",
          "Tully & Paterson (2025)", "10.1029/2025JB031608", "", "low", 3),
    _spec("Ziggie_rms", "Ziggie RMS", "Arai fit",
          "RMS misfit of the circle Ziggie measures against; a large value means the arc is a poor model.",
          "", "", "Tully & Paterson (2025)", "10.1029/2025JB031608", "", "low", 3),
    _spec("SCAT", "SCAT", "Arai fit",
          "Do the selected points and their checks all fall inside the scatter box?",
          "box through (xbar, ybar) with slopes b +/- 2 beta_threshold |b|", "",
          "Shaar & Tauxe (2013)", "10.1002/ggge.20062", "int_scat", "bool", 0),
    _spec("R2_corr", "R^2 corr", "Arai fit", "Square of the Pearson correlation over the segment.",
          "", "", SPD14, SPD14_DOI, "", "high", 3),
    _spec("R2_det", "R^2 det", "Arai fit", "Coefficient of determination of the linear model.",
          "R2_det = 1 - sum (y_i - y'_i)^2 / sum (y_i - ybar)^2", "", SPD14, SPD14_DOI, "", "high", 3),
    _spec("Z", "Z", "Arai fit", "Zig-zag parameter of Yu & Tauxe (2005).",
          "Z = sum x_i |b~_i - |b|| / |X_int|", "", SPD14, SPD14_DOI, "int_z", "low", 1),
    _spec("Z_star", "Z*", "Arai fit", "Zig-zag parameter of Yu (2012).",
          "Z* = 100 sum x_i |b~_i - |b|| / (|Y_int| (n-1))", "", SPD14, SPD14_DOI, "int_z_md", "low", 1),
    _spec("S", "S", "Arai fit", "Goodness of fit minimised by the SMA line (York, 1966).",
          "S = sum (y_i - b x_i - Y_int)^2 / (b^2 var_x + var_y)", "", SPD14, SPD14_DOI, "", "low", 2),
    _spec("S_prime", "S'", "Arai fit", "S per degree of freedom; expectation 1.", "S' = S / (n-2)", "",
          SPD14, SPD14_DOI, "", "low", 2),
    _spec("p_chi2", "p chi2", "Arai fit",
          "Probability that the linear model fits; reject the line at p <= 0.05.",
          "p = 1 - F_chi2(S; n-2)", "", SPD14, SPD14_DOI, "", "high", 3),
    _spec("IZZI_MD", "IZZI_MD", "Arai fit", "Signed zig-zag area of the Arai plot.",
          "sum of signed triangle areas / ZI polyline length", "", "Shaar et al. (2011)",
          "10.1016/j.epsl.2011.08.024", "", "low", 3),
    # --- directional -------------------------------------------------------
    _spec("Dec_Free", "Dec (free)", "Direction", "Declination of the free-floating PCA fit.", "", "deg",
          SPD14, SPD14_DOI, "dir_dec", "", 1),
    _spec("Inc_Free", "Inc (free)", "Direction", "Inclination of the free-floating PCA fit.", "", "deg",
          SPD14, SPD14_DOI, "dir_inc", "", 1),
    _spec("MAD_Free", "MAD (free)", "Direction", "Maximum angular deviation of the free fit.",
          "MAD = atan(sqrt((tau2+tau3)/tau1))", "deg", SPD14, SPD14_DOI, "int_mad_free", "low", 1),
    _spec("Dec_Anc", "Dec (anc)", "Direction", "Declination of the origin-anchored PCA fit.", "", "deg",
          SPD14, SPD14_DOI, "", "", 1),
    _spec("Inc_Anc", "Inc (anc)", "Direction", "Inclination of the origin-anchored PCA fit.", "", "deg",
          SPD14, SPD14_DOI, "", "", 1),
    _spec("MAD_Anc", "MAD (anc)", "Direction", "Maximum angular deviation of the anchored fit.", "", "deg",
          SPD14, SPD14_DOI, "int_mad_anc", "low", 1),
    _spec("alpha", "alpha", "Direction", "Angle between the anchored and free-floating directions.",
          "", "deg", SPD14, SPD14_DOI, "int_alpha", "low", 1),
    _spec("alpha_prime", "alpha'", "Direction",
          "Angle between the anchored direction and an independent measure of the direction.",
          "", "deg", "Kissel & Laj (2004)", "10.1016/j.pepi.2003.11.006", "", "low", 1),
    _spec("theta", "theta", "Direction", "Angle between the applied field and the NRM direction.",
          "", "deg", SPD14, SPD14_DOI, "", "", 1),
    _spec("DANG", "DANG", "Direction",
          "Angle between the free-floating direction and the centre of mass seen from the origin.",
          "", "deg", "Tauxe & Staudigel (2004)", "10.1029/2003GC000635", "int_dang", "low", 1),
    _spec("NRM_dev", "NRM dev", "Direction",
          "Offset of the free-floating component from the origin, as a percentage of the NRM.",
          "NRM_dev = 100 sin(DANG) |centre| / |Y_int|", "%", "Tanaka & Kobayashi (2003)", "",
          "", "low", 1),
    _spec("gamma", "gamma", "Direction",
          "Angle between the pTRM gained at Tmax and the laboratory field; a quick anisotropy check.",
          "", "deg", SPD14, SPD14_DOI, "", "low", 1),
    _spec("CRM_percent", "CRM(%)", "Direction",
          "Deflection of the NRM toward B_lab expected from a chemical remanence.",
          "CRM(%) = 100 max(CRM_i) / dx'", "%", "Coe et al. (1984)", "", "int_crm", "low", 1),
    # --- pTRM checks -------------------------------------------------------
    _spec("n_pTRM", "n pTRM", "pTRM check", "Number of pTRM checks used.", "", "", SPD14, SPD14_DOI,
          "int_n_ptrm", "high", 0),
    _spec("check_percent", "check(%)", "pTRM check",
          "Largest pTRM check difference relative to the pTRM at that step.", "", "%",
          SPD14, SPD14_DOI, "", "low", 1),
    _spec("dCK", "dCK", "pTRM check", "Largest pTRM check difference relative to the total TRM.",
          "dCK = 100 max|dpTRM| / |X_int|", "%", "Leonhardt et al. (2004a)", "10.1029/2004GC000807",
          "int_dck", "low", 1),
    _spec("DRAT", "DRAT", "pTRM check", "Largest pTRM check difference relative to the fit length.",
          "DRAT = 100 max|dpTRM| / L", "%", "Selkin & Tauxe (2000)", "10.1098/rsta.2000.0574",
          "int_drat", "low", 1),
    _spec("maxDEV", "maxDEV", "pTRM check",
          "Largest pTRM check difference relative to the TRM extent of the fit.", "", "%",
          "Blanco et al. (2012)", "", "int_maxdev", "low", 1),
    _spec("Pck", "Pck", "pTRM check",
          "Largest pTRM check difference relative to the pTRM gained at Tmax.",
          "Pck = 100 max|dpTRM| / x_end", "%", "Carvallo et al. (2004); added in SPD v1.2",
          "10.1029/2003GC000638", "", "low", 1),
    _spec("CDRAT", "CDRAT", "pTRM check", "Cumulative DRAT (signed sum).", "", "%",
          "Kissel & Laj (2004)", "10.1016/j.pepi.2003.11.006", "int_cdrat", "low", 1),
    _spec("CDRAT_prime", "CDRAT'", "pTRM check", "Cumulative DRAT of absolute differences.", "", "%",
          SPD14, SPD14_DOI, "", "low", 1),
    _spec("DRATS", "DRATS", "pTRM check",
          "Cumulative pTRM check difference relative to the pTRM at Tmax.", "", "%",
          "Tauxe & Staudigel (2004)", "10.1029/2003GC000635", "int_drats", "low", 1),
    _spec("DRATS_prime", "DRATS'", "pTRM check", "DRATS of absolute differences.", "", "%",
          SPD14, SPD14_DOI, "", "low", 1),
    _spec("mean_DRAT", "mean DRAT", "pTRM check", "Mean pTRM check difference over the fit length.",
          "", "%", SPD14, SPD14_DOI, "int_mdrat", "low", 1),
    _spec("mean_DRAT_prime", "mean DRAT'", "pTRM check", "Mean absolute pTRM check difference over L.",
          "", "%", SPD14, SPD14_DOI, "", "low", 1),
    _spec("mean_DEV", "mean DEV", "pTRM check", "Mean pTRM check deviation over the TRM extent.",
          "", "%", "Blanco et al. (2012)", "", "int_mdev", "low", 1),
    _spec("mean_DEV_prime", "mean DEV'", "pTRM check", "Mean absolute pTRM check deviation.", "", "%",
          SPD14, SPD14_DOI, "", "low", 1),
    _spec("delta_pal", "dpal", "pTRM check",
          "Change in slope after correcting the pTRMs for cumulative alteration.",
          "dpal = 100 (b - b*) / b", "%", "Leonhardt et al. (2004a); Valet et al. (1996)",
          "10.1029/2004GC000807", "int_dpal", "low", 1),
    # --- tail checks -------------------------------------------------------
    _spec("n_tail", "n tail", "pTRM tail check", "Number of pTRM tail checks used.", "", "",
          SPD14, SPD14_DOI, "int_n_tail", "high", 0),
    _spec("DRAT_tail", "DRAT tail", "pTRM tail check",
          "Largest tail check difference relative to the fit length.", "", "%",
          "Biggin et al. (2007)", "", "int_drat_tail", "low", 1),
    _spec("dTR", "dTR", "pTRM tail check", "Largest tail check difference relative to the NRM.",
          "dTR = 100 max|dtail| / |Y_int|", "%", "Leonhardt et al. (2004a)", "10.1029/2004GC000807",
          "int_dtr", "low", 1),
    _spec("MD_VDS", "MD(VDS)", "pTRM tail check",
          "Largest tail check difference relative to the vector difference sum.", "", "%",
          "Tauxe & Staudigel (2004)", "10.1029/2003GC000635", "int_md", "low", 1),
    _spec("delta_t_star", "dt*", "pTRM tail check",
          "Extent of a pTRM tail after correcting for its angular dependence.",
          "piecewise in the angle between B_lab and the NRM; see SPD section 6", "%",
          "Leonhardt et al. (2004a, 2004b)", "10.1029/2004GC000807", "int_dt", "low", 1),
    # --- additivity --------------------------------------------------------
    _spec("n_add", "n add", "Additivity check", "Number of additivity checks used.", "", "",
          SPD14, SPD14_DOI, "int_n_add", "high", 0),
    _spec("dAC", "dAC", "Additivity check",
          "Largest additivity check difference relative to the total TRM.",
          "dAC = 100 max|AC| / |X_int|", "%", "Krasa et al. (2003); Leonhardt et al. (2004a)",
          "10.1016/S0031-9201(03)00060-7", "int_dac", "low", 1),
    # --- corrections -------------------------------------------------------
    _spec("c", "c", "Correction", "Anisotropy correction factor.",
          "c = |chi B_lab_hat| / |chi B_anc_hat|", "", "Veitch et al. (1984); SPD section 8", "",
          "int_corr_anisotropy", "", 3),
    _spec("delta_TRM_anis", "dTRM anis", "Correction",
          "Alteration during the anisotropy experiment (repeat of position 1).", "", "%",
          SPD14, SPD14_DOI, "aniso_alt", "low", 1),
    _spec("A1", "A1", "Correction", "Non-linear TRM scaling coefficient.", "TRM = A1 tanh(A2 B)", "",
          "Selkin et al. (2007)", "10.1016/j.epsl.2007.01.026", "", "", 3),
    _spec("A2", "A2", "Correction", "Non-linear TRM curvature coefficient.", "TRM = A1 tanh(A2 B)", "1/T",
          "Selkin et al. (2007)", "10.1016/j.epsl.2007.01.026", "", "", 5),
    _spec("delta_TRM_NLT", "dTRM NLT", "Correction",
          "Alteration during the TRM acquisition experiment (repeat in B_lab).", "", "%",
          SPD14, SPD14_DOI, "", "low", 1),
    _spec("cooling_rate_factor", "CR factor", "Correction",
          "Cooling-rate correction factor applied to the intensity.", "", "",
          "Halgedahl et al. (1980); Shaar & Tauxe (2013)", "10.1002/ggge.20062",
          "int_corr_cooling_rate", "", 3),
    # --- group -------------------------------------------------------------
    _spec("N", "N", "Group", "Number of accepted estimates in the group.", "", "", SPD14, SPD14_DOI,
          "int_n_specimens", "high", 0),
    _spec("mean", "mean", "Group", "Arithmetic mean of the estimates.", "", "uT", SPD14, SPD14_DOI,
          "int_abs", "", 1),
    _spec("sd", "s", "Group", "Standard deviation of the estimates.", "", "uT", SPD14, SPD14_DOI,
          "int_abs_sigma", "low", 1),
    _spec("weighted_mean", "weighted mean", "Group", "Weighted mean of the estimates.", "", "uT",
          SPD14, SPD14_DOI, "", "", 1),
    _spec("weighted_sd", "weighted s", "Group", "Weighted standard deviation (Heckert & Filliben, 2003).",
          "", "uT", SPD14, SPD14_DOI, "", "low", 1),
    _spec("dB_percent", "dB(%)", "Group", "Standard deviation as a percentage of the mean.",
          "dB = 100 s / m", "%", SPD14, SPD14_DOI, "int_abs_sigma_perc", "low", 1),
    _spec("dBN_percent", "dBN(%)", "Group",
          "Upper 95% confidence bound on the scatter, corrected for small N.",
          "dBN = 100 sqrt(N) / t_nc(1-a; N-1; m sqrt(N)/s)", "%", "Paterson et al. (2010a)",
          "10.1029/2009JB006678", "", "low", 1),
    _spec("p_dB", "p dB", "Group", "Probability that the scatter is at or below dB_max.", "", "",
          "Paterson et al. (2010a)", "10.1029/2009JB006678", "", "", 3),
    _spec("p_s", "p s", "Group", "Probability that the standard deviation is at or below s_max.", "", "",
          "Paterson et al. (2010a)", "10.1029/2009JB006678", "", "", 3),
])


def categories() -> List[str]:
    """The statistic categories, in the order the panel shows them."""
    seen: List[str] = []
    for spec in CATALOG.values():
        if spec.category not in seen:
            seen.append(spec.category)
    return seen


def describe(key: str) -> StatSpec:
    """The catalogue entry for a statistic, or a minimal placeholder."""
    return CATALOG.get(key, StatSpec(key, key, "Other", ""))
