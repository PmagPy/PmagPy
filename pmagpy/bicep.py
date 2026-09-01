"""
BiCEP: Bias Corrected Estimation of Paleointensity.

Cych, B., Morzfeld, M., & Tauxe, L. (2021). Bias Corrected Estimation of
Paleointensity (BiCEP): An improved methodology for obtaining paleointensity
estimates. Geochemistry, Geophysics, Geosystems, 22, e2021GC009755.
https://doi.org/10.1029/2021GC009755

The idea: a specimen's paleointensity estimate is biased in proportion to how
curved its Arai plot is, so instead of accepting or rejecting specimens one at
a time, fit every specimen in a site at once under the constraint that its
estimate ``B_j`` is linear in its Arai curvature ``k_j``,

    B_j = B_site + c k_j + e_j ,        e_j ~ Normal(0, sigma_B)

and read the site paleointensity off the intercept. Each specimen contributes a
circle fitted to its own Arai plot, so a specimen whose plot is poorly
described by a line *or* a circle has an uncertain ``k_j`` and little influence
on the site fit, while a linear specimen pins it down.

This is an independent implementation from the paper, not a port: the
reference GUI (https://github.com/bcych/BiCEP_GUI) declares CC BY-SA 4.0 in
its repository while its package metadata says MIT, and that conflict is not
ours to resolve, so no code was taken from it. Please cite the paper above
whenever a result from this module is published.

Samplers
--------
``stan``      the full model in Stan through cmdstanpy -- the fastest and
              best-diagnosed option, and the only one that reports
              divergences. Optional: ordinary specimen analysis never needs it.
``mcmc``      a self-contained blocked Metropolis-within-Gibbs sampler over
              the same posterior, in numpy: each specimen's circle is a small
              random-walk block and the site line is drawn from its exact
              conditional. No extra dependency, deterministic for a given seed.
``bootstrap`` not a posterior at all: a weighted straight-line fit of B_j on
              k_j with a bootstrap interval. Instant, useful while choosing
              specimens, and always labelled as an approximation.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from pmagpy import pint_stats as ps

CITATION = ("Cych, B., Morzfeld, M., & Tauxe, L. (2021). Bias Corrected Estimation of "
            "Paleointensity (BiCEP): An improved methodology for obtaining paleointensity "
            "estimates. Geochemistry, Geophysics, Geosystems, 22, e2021GC009755.")
DOI = "10.1029/2021GC009755"

#: a specimen whose lowest remaining NRM is more than this fraction of the
#: initial NRM was not demagnetized far enough for the scaling to mean
#: anything, and is left out (Cych et al., 2021, section 2.2.1)
MAX_RESIDUAL_NRM = 0.25
#: the paper's prior range for the site intensity
B_SITE_RANGE = (0.0, 250.0)
#: the paper's preferred model: a half-normal prior on the specimen scatter
SIGMA_B_PRIOR_SD = 5.0
METHODS = ("stan", "mcmc", "bootstrap")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
@dataclass
class BicepSpecimen:
    """One specimen's scaled Arai plot, ready for the site fit."""
    name: str
    x: np.ndarray               # pTRM gained, scaled (see scale_arai)
    y: np.ndarray               # NRM remaining, scaled the same way
    blab: float                 # microtesla
    k_prime: float = np.nan     # the curvature of the scaled data (starting value)
    b: float = np.nan           # the straight-line slope over the same points
    b_anc: float = np.nan       # |b| * blab, the uncorrected estimate
    included: bool = True
    note: str = ""

    @property
    def n(self) -> int:
        return len(self.x)


def scale_arai(x: Sequence[float], y: Sequence[float]) -> Tuple[np.ndarray, np.ndarray, str]:
    """Scale an Arai plot the way BiCEP does, or say why it cannot be used.

    The pTRMs are scaled by the largest pTRM so that the fit does not depend
    on the laboratory field; the smallest pTRM and the smallest remaining NRM
    are subtracted so that a partially used plot still starts at the origin.
    A specimen whose remaining NRM never falls below a quarter of the initial
    NRM is rejected: the scaling assumes the NRM was essentially replaced.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3:
        return x, y, "fewer than three Arai points"
    if y[0] <= 0:
        return x, y, "the NRM is zero"
    x_max = float(np.max(x))
    if x_max <= 0:
        return x, y, "no pTRM was gained"
    if float(np.min(y)) > MAX_RESIDUAL_NRM * float(y[0]):
        return x, y, (f"the remaining NRM never falls below "
                      f"{MAX_RESIDUAL_NRM:.0%} of the initial NRM")
    xs = (x - float(np.min(x))) / x_max
    ys = (y - float(np.min(y))) / x_max
    return xs, ys, ""


def prepare(specimens: Sequence[Tuple[str, Sequence[float], Sequence[float], float]]
            ) -> List[BicepSpecimen]:
    """Build the site's specimen list from ``(name, x, y, blab_uT)`` tuples."""
    out = []
    for name, x, y, blab in specimens:
        xs, ys, problem = scale_arai(x, y)
        fit = ps.york_regression(xs, ys) if not problem else {}
        curv = ps.arai_curvature(xs, ys) if not problem else {"k": np.nan}
        b = fit.get("b", np.nan)
        out.append(BicepSpecimen(name=name, x=xs, y=ys, blab=float(blab),
                                 k_prime=curv.get("k", np.nan), b=b,
                                 b_anc=abs(b) * float(blab) if np.isfinite(b) else np.nan,
                                 included=not problem, note=problem))
    return out


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------
# Cych et al. (2021) reparameterise the circle after Chernov & Lesort (2005),
# because fitting (centre, radius) directly has several minima -- four even for
# a straight Arai plot, since a huge circle can sit on any side. Instead:
#
#   phi   the angle to the horizontal of the line from the origin to the centre
#   dist  the distance from the origin to where that line first meets the circle
#   k     the signed curvature, 1/radius, zero for a straight plot
#
# The centre is then at ``(dist + 1/k) * (cos phi, sin phi)``. This is worth the
# indirection twice over: the posterior becomes unimodal, and the specimen's
# intensity depends on phi alone while its curvature is k alone, so the two
# quantities the site model relates are separate parameters.

#: the widest curvature entertained, in the scaled coordinates (radius >= 1/5)
K_LIMIT = 5.0


def circle_centre(phi: float, dist: float, k: float) -> Tuple[float, float, float]:
    """Centre and radius of the circle described by (phi, dist, k)."""
    radius = np.inf if k == 0 else 1.0 / k
    offset = dist + (0.0 if k == 0 else 1.0 / k)
    return offset * math.cos(phi), offset * math.sin(phi), abs(radius)


def circle_intensity(phi: float, blab: float) -> float:
    """The paleointensity a fitted circle implies, in microtesla (equation 17).

    The Arai "slope" of a circular arc is the tangent to the circle where the
    line from the origin to the centre touches it, which is ``-1/tan(phi)``, so
    the intensity is ``B_lab / tan(phi)``. For a straight plot the circle edge
    *is* that tangent, and this reduces to the ordinary slope estimate.
    """
    t = math.tan(phi)
    if not np.isfinite(t) or t <= 0:
        return np.nan
    return blab / t


def circle_distances(x: np.ndarray, y: np.ndarray, phi: float, dist: float,
                     k: float) -> np.ndarray:
    """Perpendicular distance from each Arai point to the circle.

    Written so that ``k = 0`` is the straight-line limit rather than a
    division by zero: with ``u`` along the origin-to-centre direction and ``v``
    across it, the distance is ``(-2u + (u^2 + v^2) k) / (1 + s)`` where
    ``s = sqrt(1 - 2 u k + (u^2 + v^2) k^2)``, which tends to ``-u`` as k tends
    to zero.
    """
    c, s_ = math.cos(phi), math.sin(phi)
    u = x * c + y * s_ - dist
    v = -x * s_ + y * c
    q = u * u + v * v
    inside = 1.0 - 2.0 * u * k + q * k * k
    if np.any(inside < 0):
        return np.full(len(x), np.nan)
    root = np.sqrt(inside)
    return (-2.0 * u + q * k) / (1.0 + root)


@dataclass
class _Packed:
    """The parameter vector layout: phi, dist and k per specimen, then the site."""
    n: int

    @property
    def size(self) -> int:
        return 3 * self.n + 3

    def unpack(self, theta: np.ndarray):
        n = self.n
        return (theta[0:n], theta[n:2 * n], theta[2 * n:3 * n],
                theta[3 * n], theta[3 * n + 1], theta[3 * n + 2])


def log_posterior(theta: np.ndarray, specimens: Sequence[BicepSpecimen],
                  layout: _Packed, sigma_b_prior_sd: float = SIGMA_B_PRIOR_SD,
                  dist_max: Optional[np.ndarray] = None) -> float:
    """log p(parameters | Arai data), up to a constant.

    The per-specimen noise is integrated out analytically under the
    uninformative prior ``p(sigma) ~ 1/sigma`` (equation 8 of the paper), which
    leaves ``-n/2 log(sum of squared distances)`` per specimen and three
    parameters per specimen instead of four.
    """
    phi, dist, k, b_site, c, log_sigma_b = layout.unpack(theta)
    if not np.all(np.isfinite(theta)):
        return -np.inf
    if not (B_SITE_RANGE[0] <= b_site <= B_SITE_RANGE[1]):
        return -np.inf
    if np.any(phi <= 1e-6) or np.any(phi >= math.pi / 2 - 1e-6):
        return -np.inf
    if np.any(dist < 0) or np.any(np.abs(k) > K_LIMIT):
        return -np.inf
    if dist_max is not None and np.any(dist > dist_max):
        return -np.inf
    sigma_b = math.exp(log_sigma_b)
    total = 0.0
    predicted = np.empty(len(specimens))
    for j, spec in enumerate(specimens):
        d = circle_distances(spec.x, spec.y, phi[j], dist[j], k[j])
        if not np.all(np.isfinite(d)):
            return -np.inf
        sse = float(d @ d)
        if sse <= 0:
            sse = 1e-30
        total += -0.5 * spec.n * math.log(sse)
        value = circle_intensity(phi[j], spec.blab)
        if not np.isfinite(value):
            return -np.inf
        predicted[j] = value
    residual = predicted - (b_site + c * k)
    total += -0.5 * float(residual @ residual) / (sigma_b ** 2) - len(specimens) * log_sigma_b
    # half-normal prior on the specimen scatter, plus the log Jacobian of the
    # exponential transform; flat priors on phi, dist, k, c and B_site
    total += -0.5 * (sigma_b / sigma_b_prior_sd) ** 2 + log_sigma_b
    return total


def specimen_start(spec: BicepSpecimen) -> Tuple[float, float, float]:
    """A least-squares starting point for one specimen, as (phi, dist, k)."""
    curv = ps.arai_curvature(spec.x, spec.y)
    fit = ps.york_regression(spec.x, spec.y)
    slope = fit.get("b", -1.0)
    if not np.isfinite(slope) or slope >= 0:
        slope = -1.0
    phi = math.atan2(1.0, -slope)                 # tan(phi) = -1/slope
    phi = min(max(phi, 1e-3), math.pi / 2 - 1e-3)
    a, b, r = curv.get("a"), curv.get("b"), curv.get("r")
    if a is not None and np.isfinite(a) and np.isfinite(b) and np.isfinite(r) and r > 0:
        centre = math.hypot(a, b)
        k = curv["k"]
        if np.isfinite(k) and abs(k) < K_LIMIT:
            dist = max(centre - r, 0.0) if k > 0 else max(r - centre, 0.0)
            if np.isfinite(dist):
                return phi, float(dist), float(k)
    # a straight plot: the tangent line touches at the foot of the perpendicular
    y_int = fit.get("y_int", 1.0)
    dist = abs(y_int) * math.sin(phi) if np.isfinite(y_int) else 0.5
    return phi, float(dist), 0.0


def initial_guess(specimens: Sequence[BicepSpecimen]) -> np.ndarray:
    """Each specimen's own circle, then the site line through (k, B)."""
    n = len(specimens)
    theta = np.zeros(3 * n + 3)
    b_values, k_values = [], []
    for j, spec in enumerate(specimens):
        phi, dist, k = specimen_start(spec)
        theta[j], theta[n + j], theta[2 * n + j] = phi, dist, k
        value = circle_intensity(phi, spec.blab)
        if np.isfinite(value):
            b_values.append(value)
            k_values.append(k)
    if len(b_values) >= 2 and np.ptp(k_values) > 0:
        slope, intercept = np.polyfit(k_values, b_values, 1)
    else:
        slope = 0.0
        intercept = float(np.mean(b_values)) if b_values else 20.0
    theta[3 * n] = float(min(max(intercept, 1.0), B_SITE_RANGE[1] - 1.0))
    theta[3 * n + 1] = float(slope)
    theta[3 * n + 2] = math.log(max(float(np.std(b_values)) if len(b_values) > 1 else 2.0, 0.5))
    return theta


def distance_bounds(specimens: Sequence[BicepSpecimen]) -> np.ndarray:
    """An upper bound on ``dist`` per specimen, from the extent of its own data."""
    return np.array([2.0 * float(np.max(np.hypot(s.x, s.y))) + 1.0 for s in specimens])


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
@dataclass
class BicepResult:
    """A site's BiCEP posterior and its diagnostics."""
    site: str
    method: str
    specimens: List[str] = field(default_factory=list)
    excluded: Dict[str, str] = field(default_factory=dict)
    b_site: float = np.nan
    ci_low: float = np.nan
    ci_high: float = np.nan
    slope: float = np.nan
    sigma_b: float = np.nan
    samples: Optional[np.ndarray] = None          # posterior draws of B_site
    slope_samples: Optional[np.ndarray] = None
    specimen_k: Dict[str, float] = field(default_factory=dict)
    specimen_b: Dict[str, float] = field(default_factory=dict)
    r_hat: float = np.nan
    ess: float = np.nan
    divergences: int = 0
    n_draws: int = 0
    seed: int = 0
    seconds: float = 0.0
    warnings: List[str] = field(default_factory=list)
    ppc: Dict[str, float] = field(default_factory=dict)

    @property
    def converged(self) -> bool:
        """The usual thresholds: R-hat below 1.05, ESS above 400, no divergences."""
        return (np.isfinite(self.r_hat) and self.r_hat < 1.05
                and np.isfinite(self.ess) and self.ess > 400 and self.divergences == 0)

    def summary(self) -> str:
        if not np.isfinite(self.b_site):
            return f"{self.site}: no result"
        return (f"{self.site}: {self.b_site:.1f} µT "
                f"[{self.ci_low:.1f}, {self.ci_high:.1f}] (95% credible), "
                f"N = {len(self.specimens)}")

    def methods_block(self) -> str:
        """A paragraph to paste into a methods section, with the citation."""
        sampler = {"stan": "Hamiltonian Monte Carlo in Stan (cmdstanpy)",
                   "mcmc": "a blocked Metropolis-within-Gibbs sampler",
                   "bootstrap": "a weighted linear fit with a bootstrap interval "
                                "(an approximation, not the BiCEP posterior)"}[self.method]
        return (f"Site {self.site} paleointensity was estimated with the Bias Corrected "
                f"Estimation of Paleointensity (BiCEP) method of Cych et al. (2021), as "
                f"implemented in PmagPy Intensity, using {len(self.specimens)} specimens and "
                f"{sampler} ({self.n_draws} posterior draws, seed {self.seed}). "
                f"The site estimate is {self.b_site:.1f} µT with a 95% credible interval of "
                f"{self.ci_low:.1f}–{self.ci_high:.1f} µT"
                + (f" (R-hat {self.r_hat:.3f}, effective sample size {self.ess:.0f}, "
                   f"{self.divergences} divergent transitions)." if self.method != "bootstrap"
                   else ".")
                + f"\n\n{CITATION} https://doi.org/{DOI}")

    def to_dict(self) -> dict:
        out = {k: v for k, v in asdict(self).items() if k not in ("samples", "slope_samples")}
        out["samples"] = None if self.samples is None else [float(v) for v in self.samples]
        out["slope_samples"] = None if self.slope_samples is None else \
            [float(v) for v in self.slope_samples]
        return out


# ---------------------------------------------------------------------------
# Availability of the optional sampler
# ---------------------------------------------------------------------------
def stan_status() -> dict:
    """Whether the Stan sampler can run here, and what to do if it cannot."""
    try:
        import cmdstanpy
    except ImportError:
        return {"available": False, "reason": "cmdstanpy is not installed",
                "hint": "pip install cmdstanpy, then python -m cmdstanpy.install_cmdstan",
                "cmdstan": None, "version": None}
    try:
        path = cmdstanpy.cmdstan_path()
    except Exception as exc:
        return {"available": False, "reason": f"CmdStan is not installed ({exc})",
                "hint": "python -m cmdstanpy.install_cmdstan", "cmdstan": None,
                "version": getattr(cmdstanpy, "__version__", None)}
    return {"available": True, "reason": "", "hint": "", "cmdstan": path,
            "version": getattr(cmdstanpy, "__version__", None)}


STAN_MODEL = """
// BiCEP (Cych, Morzfeld & Tauxe, 2021, doi:10.1029/2021GC009755).
// One circle per specimen fitted to its scaled Arai plot, with the intensity
// each circle implies constrained to be linear in that circle's curvature.
data {
  int<lower=1> S;                 // specimens
  int<lower=1> N;                 // Arai points, all specimens together
  array[N] int<lower=1, upper=S> spec;
  vector[N] x;
  vector[N] y;
  vector<lower=0>[S] blab;        // microtesla
  vector[S] x_mid;                // centroid of each specimen's scaled Arai plot
  vector[S] y_mid;
  real<lower=0> sigma_b_prior_sd;
  real<lower=0> b_site_max;
}
parameters {
  vector[S] x_c;
  vector[S] y_c;
  vector<lower=0>[S] radius;
  vector<lower=0>[S] sigma;
  real<lower=0, upper=b_site_max> b_site;
  real slope;
  real<lower=0> sigma_b;
}
transformed parameters {
  vector[S] k;
  vector[S] b_spec;
  for (s in 1:S) {
    real rr = radius[s] * radius[s];
    real dy = sqrt(fmax(rr - x_c[s] * x_c[s], 1e-12));
    real dx = sqrt(fmax(rr - y_c[s] * y_c[s], 1e-12));
    // the intersection on the same side as the data is the one the plot uses
    real y0 = y_c[s] > y_mid[s] ? y_c[s] - dy : y_c[s] + dy;
    real x0 = x_c[s] > x_mid[s] ? x_c[s] - dx : x_c[s] + dx;
    b_spec[s] = blab[s] * y0 / fmax(x0, 1e-9);
    // Paterson (2011) signs the curvature by where the centre lies
    k[s] = (x_c[s] <= x_mid[s] && y_c[s] <= y_mid[s]) ? -inv(radius[s]) : inv(radius[s]);
  }
}
model {
  for (n in 1:N) {
    real d = sqrt(square(x[n] - x_c[spec[n]]) + square(y[n] - y_c[spec[n]])) - radius[spec[n]];
    d ~ normal(0, sigma[spec[n]]);
  }
  sigma_b ~ normal(0, sigma_b_prior_sd);      // half-normal through the constraint
  b_spec ~ normal(b_site + slope * k, sigma_b);
}
"""


# ---------------------------------------------------------------------------
# Samplers
# ---------------------------------------------------------------------------
def run(specimens: Sequence[BicepSpecimen], site: str = "", method: str = "auto",
        draws: int = 2000, warmup: int = 1000, chains: int = 4, seed: int = 20210,
        sigma_b_prior_sd: float = SIGMA_B_PRIOR_SD, progress: Optional[Callable] = None,
        cancel: Optional[Callable[[], bool]] = None) -> BicepResult:
    """Estimate a site's paleointensity with BiCEP.

    Args:
        specimens: from :func:`prepare`; those with ``included`` False are skipped.
        method: ``'stan'``, ``'mcmc'``, ``'bootstrap'`` or ``'auto'``
            (Stan when it is installed, otherwise the ensemble sampler).
        seed: fixes the draws, so a run is reproducible and a test is stable.
        progress: called as ``progress(fraction, message)``.
        cancel: polled during sampling; return True to stop and report partial
            draws rather than leaving the interface stuck.
    """
    used = [s for s in specimens if s.included and s.n >= 3]
    excluded = {s.name: (s.note or "excluded by the analyst")
                for s in specimens if s not in used}
    result = BicepResult(site=site, method=method, specimens=[s.name for s in used],
                         excluded=excluded, seed=seed)
    if len(used) < 2:
        result.warnings.append("BiCEP needs at least two specimens; "
                               f"{len(used)} are available")
        result.method = method if method != "auto" else "bootstrap"
        return result
    if method == "auto":
        method = "stan" if stan_status()["available"] else "mcmc"
    result.method = method
    started = time.time()
    if method == "stan":
        _run_stan(used, result, draws, warmup, chains, seed, sigma_b_prior_sd, progress)
    elif method == "mcmc":
        _run_mcmc(used, result, draws, warmup, chains, seed, sigma_b_prior_sd,
                  progress, cancel)
    elif method == "bootstrap":
        _run_bootstrap(used, result, draws, seed)
    else:
        raise ValueError(f"unknown BiCEP method {method!r}; choose one of {METHODS}")
    result.seconds = time.time() - started
    return result


def _initial_spread(layout: _Packed, start: np.ndarray) -> np.ndarray:
    """How far to scatter the starting walkers in each parameter.

    An affine-invariant ensemble can only explore the volume its walkers span,
    so the scatter has to be of the order of the posterior width rather than a
    token jitter: a few hundredths of a radian in phi, a percent in dist, a few
    hundredths in curvature, and a few microtesla in the site intensity.
    """
    n = layout.n
    spread = np.empty(layout.size)
    spread[0:n] = 0.02                                    # phi, radians
    spread[n:2 * n] = 0.02 * (1.0 + np.abs(start[n:2 * n]))
    spread[2 * n:3 * n] = 0.03                            # curvature
    spread[3 * n] = 2.0                                   # B_site, microtesla
    spread[3 * n + 1] = max(5.0, 0.2 * abs(start[3 * n + 1]))
    spread[3 * n + 2] = 0.2
    return spread


def _summarise(result: BicepResult, samples: np.ndarray, slope: np.ndarray,
               chains: Optional[np.ndarray] = None) -> None:
    result.samples = samples
    result.slope_samples = slope
    result.n_draws = len(samples)
    if len(samples) == 0:
        return
    result.b_site = float(np.median(samples))
    result.ci_low, result.ci_high = [float(v) for v in np.percentile(samples, [2.5, 97.5])]
    result.slope = float(np.median(slope))
    if chains is not None and chains.ndim == 2 and chains.shape[0] > 1:
        result.r_hat = float(gelman_rubin(chains))
        result.ess = float(effective_sample_size(chains))


def _run_mcmc(specimens, result, draws, warmup, chains, seed, sigma_b_prior_sd,
              progress, cancel) -> None:
    """Blocked Metropolis-within-Gibbs over the same posterior.

    The model separates cleanly: given every specimen's circle, the site line
    is an ordinary linear regression of ``B_j`` on ``k_j``, which can be drawn
    from directly; given the site line, each specimen's three parameters are a
    small random-walk update. Alternating the two mixes far faster than moving
    all of them together, and needs nothing beyond numpy.
    """
    layout = _Packed(len(specimens))
    dist_max = distance_bounds(specimens)
    start = initial_guess(specimens)
    n = layout.n
    chain_means, site_draws, slope_draws, kept = [], [], [], []
    accepted_total = attempted_total = 0

    for chain in range(max(chains, 1)):
        rng = np.random.default_rng(seed + 1013 * chain)
        theta = start.copy()
        if chain:
            theta[0:n] += rng.normal(0, 0.02, n)
            theta[2 * n:3 * n] += rng.normal(0, 0.03, n)
            theta[3 * n] = float(min(max(theta[3 * n] + rng.normal(0, 3.0), 1.0),
                                     B_SITE_RANGE[1] - 1.0))
        step_size = np.tile(np.array([0.01, 0.01, 0.01]), (n, 1))
        this_chain = []
        for it in range(warmup + draws):
            if cancel is not None and cancel():
                result.warnings.append(
                    f"cancelled during chain {chain + 1} after {it} of {warmup + draws} steps")
                break
            # --- each specimen's circle, one block at a time --------------
            for j in range(n):
                current = _specimen_logp(theta, j, specimens, layout, sigma_b_prior_sd)
                proposal = theta.copy()
                proposal[j] += rng.normal(0, step_size[j, 0])
                proposal[n + j] += rng.normal(0, step_size[j, 1])
                proposal[2 * n + j] += rng.normal(0, step_size[j, 2])
                if not (0 < proposal[j] < math.pi / 2) or proposal[n + j] < 0 or \
                        proposal[n + j] > dist_max[j] or abs(proposal[2 * n + j]) > K_LIMIT:
                    attempted_total += 1
                    continue
                trial = _specimen_logp(proposal, j, specimens, layout, sigma_b_prior_sd)
                attempted_total += 1
                if np.isfinite(trial) and math.log(rng.random()) < trial - current:
                    theta = proposal
                    accepted_total += 1
                    if it < warmup:
                        step_size[j] *= 1.02
                elif it < warmup:
                    step_size[j] *= 0.995
            # --- the site line, drawn directly ----------------------------
            phi, _, k, _, _, log_sigma_b = layout.unpack(theta)
            b_spec = np.array([circle_intensity(phi[j], specimens[j].blab) for j in range(n)])
            if np.all(np.isfinite(b_spec)):
                theta[3 * n], theta[3 * n + 1] = _draw_site_line(b_spec, k, math.exp(log_sigma_b), rng)
                theta[3 * n + 2] = _draw_log_sigma_b(b_spec, k, theta[3 * n], theta[3 * n + 1],
                                                     theta[3 * n + 2], sigma_b_prior_sd, rng)
            if it >= warmup:
                this_chain.append(float(theta[3 * n]))
                site_draws.append(float(theta[3 * n]))
                slope_draws.append(float(theta[3 * n + 1]))
                if len(kept) < 4000:
                    kept.append(theta.copy())
            if progress is not None and it % 50 == 0:
                done = (chain * (warmup + draws) + it + 1) / (max(chains, 1) * (warmup + draws))
                progress(done, f"chain {chain + 1}/{max(chains, 1)}, step {it + 1}/{warmup + draws}")
        chain_means.append(this_chain)
        if result.warnings and "cancelled" in result.warnings[-1]:
            break

    length = min((len(c) for c in chain_means if c), default=0)
    grouped = np.array([c[:length] for c in chain_means if c]) if length > 8 else None
    _summarise(result, np.asarray(site_draws), np.asarray(slope_draws), grouped)
    if attempted_total:
        rate = accepted_total / attempted_total
        if rate < 0.05 or rate > 0.9:
            result.warnings.append(f"the specimen acceptance rate was {rate:.0%}, "
                                   f"which suggests the chain did not move freely")
    if kept:
        _finish(result, specimens, kept, layout)


def _specimen_logp(theta, j, specimens, layout, sigma_b_prior_sd) -> float:
    """The part of the log posterior that one specimen's parameters affect."""
    n = layout.n
    phi, dist, k = theta[j], theta[n + j], theta[2 * n + j]
    spec = specimens[j]
    d = circle_distances(spec.x, spec.y, phi, dist, k)
    if not np.all(np.isfinite(d)):
        return -np.inf
    sse = float(d @ d)
    if sse <= 0:
        sse = 1e-30
    value = circle_intensity(phi, spec.blab)
    if not np.isfinite(value):
        return -np.inf
    sigma_b = math.exp(theta[3 * n + 2])
    residual = value - (theta[3 * n] + theta[3 * n + 1] * k)
    return -0.5 * spec.n * math.log(sse) - 0.5 * (residual / sigma_b) ** 2


def _draw_site_line(b_spec: np.ndarray, k: np.ndarray, sigma_b: float, rng) -> Tuple[float, float]:
    """Draw (B_site, slope) from their exact conditional: a linear regression."""
    design = np.column_stack((np.ones(len(k)), k))
    xtx = design.T @ design
    try:
        cov = np.linalg.inv(xtx) * sigma_b ** 2
        mean = np.linalg.solve(xtx, design.T @ b_spec)
    except np.linalg.LinAlgError:
        return float(np.mean(b_spec)), 0.0
    for _ in range(20):
        draw = rng.multivariate_normal(mean, cov)
        if B_SITE_RANGE[0] <= draw[0] <= B_SITE_RANGE[1]:
            return float(draw[0]), float(draw[1])
    return float(min(max(mean[0], B_SITE_RANGE[0]), B_SITE_RANGE[1])), float(mean[1])


def _draw_log_sigma_b(b_spec, k, b_site, slope, log_sigma_b, prior_sd, rng) -> float:
    """A one-dimensional Metropolis step on the specimen scatter."""
    residual = b_spec - (b_site + slope * k)

    def logp(value):
        sigma = math.exp(value)
        return (-0.5 * float(residual @ residual) / sigma ** 2 - len(residual) * value
                - 0.5 * (sigma / prior_sd) ** 2 + value)
    proposal = log_sigma_b + rng.normal(0, 0.2)
    if math.log(rng.random()) < logp(proposal) - logp(log_sigma_b):
        return float(proposal)
    return float(log_sigma_b)


def _run_stan(specimens, result, draws, warmup, chains, seed, sigma_b_prior_sd, progress) -> None:
    status = stan_status()
    if not status["available"]:
        result.warnings.append(f"Stan is not available: {status['reason']}. {status['hint']}")
        return
    import cmdstanpy
    import tempfile
    if progress is not None:
        progress(0.05, "compiling the Stan model")
    model = _compiled_model()
    x = np.concatenate([s.x for s in specimens])
    y = np.concatenate([s.y for s in specimens])
    index = np.concatenate([np.full(s.n, j + 1) for j, s in enumerate(specimens)])
    data = {"S": len(specimens), "N": len(x), "spec": index.tolist(),
            "x": x.tolist(), "y": y.tolist(), "blab": [s.blab for s in specimens],
            "x_mid": [float(np.mean(s.x)) for s in specimens],
            "y_mid": [float(np.mean(s.y)) for s in specimens],
            "sigma_b_prior_sd": sigma_b_prior_sd, "b_site_max": B_SITE_RANGE[1]}
    if progress is not None:
        progress(0.2, "sampling")
    with tempfile.TemporaryDirectory() as tmp:
        fit = model.sample(data=data, chains=chains, iter_warmup=warmup, iter_sampling=draws,
                           seed=seed, output_dir=tmp, show_progress=False, show_console=False)
        site = fit.stan_variable("b_site")
        slope = fit.stan_variable("slope")
        per_chain = np.asarray(site).reshape(chains, -1)
        _summarise(result, np.asarray(site), np.asarray(slope), per_chain)
        try:
            summary = fit.summary()
            result.r_hat = float(summary.loc["b_site", "R_hat"])
            result.ess = float(summary.loc["b_site", "ESS_bulk"])
        except Exception:
            pass
        try:
            result.divergences = int(sum(fit.method_variables()["divergent__"].sum(axis=0)))
        except Exception:
            result.divergences = 0
        try:
            k = np.asarray(fit.stan_variable("k"))
            b = np.asarray(fit.stan_variable("b_spec"))
            for j, spec in enumerate(specimens):
                result.specimen_k[spec.name] = float(np.median(k[:, j]))
                result.specimen_b[spec.name] = float(np.median(b[:, j]))
        except Exception:
            pass
    _posterior_predictive(result, specimens)


_MODEL_CACHE: dict = {}


def model_path() -> str:
    """Where the Stan program is written so that CmdStan can compile it once.

    Kept beside the installed package so that an installed copy works offline;
    falls back to the user's cache directory when the package is read-only.
    """
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stan")
    for base in (here, os.path.join(os.path.expanduser("~"), ".pmagpy", "stan")):
        try:
            os.makedirs(base, exist_ok=True)
            path = os.path.join(base, "bicep.stan")
            if not os.path.exists(path) or open(path).read() != STAN_MODEL:
                with open(path, "w") as fh:
                    fh.write(STAN_MODEL)
            return path
        except OSError:
            continue
    raise OSError("nowhere writable to put the Stan model")


def _compiled_model():
    import cmdstanpy
    path = model_path()
    if path not in _MODEL_CACHE:
        _MODEL_CACHE[path] = cmdstanpy.CmdStanModel(stan_file=path)
    return _MODEL_CACHE[path]


def compile_model() -> str:
    """Compile the Stan model now, so that the first analysis does not wait.

    Returns the path to the compiled executable; raises if Stan is missing.
    """
    model = _compiled_model()
    model.compile()
    return str(model.exe_file)


def _run_bootstrap(specimens, result, draws, seed) -> None:
    """A weighted line through (k, B), resampled. Not the BiCEP posterior."""
    rng = np.random.default_rng(seed)
    k = np.array([s.k_prime for s in specimens], dtype=float)
    b = np.array([s.b_anc for s in specimens], dtype=float)
    good = np.isfinite(k) & np.isfinite(b)
    k, b = k[good], b[good]
    names = [s.name for s, g in zip(specimens, good) if g]
    result.specimen_k = dict(zip(names, map(float, k)))
    result.specimen_b = dict(zip(names, map(float, b)))
    if len(k) < 2:
        result.warnings.append("too few specimens with a finite curvature")
        return
    intercepts, slopes = [], []
    for _ in range(max(draws, 200)):
        pick = rng.integers(0, len(k), len(k))
        if np.ptp(k[pick]) == 0:
            intercepts.append(float(np.mean(b[pick])))
            slopes.append(0.0)
            continue
        slope, intercept = np.polyfit(k[pick], b[pick], 1)
        intercepts.append(float(intercept))
        slopes.append(float(slope))
    _summarise(result, np.asarray(intercepts), np.asarray(slopes))
    result.warnings.append("the bootstrap option is a fast approximation, not the BiCEP "
                           "posterior; report a Stan or ensemble run")
    _posterior_predictive(result, specimens)


def _finish(result: BicepResult, specimens, draws, layout) -> None:
    """Record each specimen's posterior median curvature and intensity."""
    draws = np.asarray(draws)
    phi = draws[:, 0:layout.n]
    k = draws[:, 2 * layout.n:3 * layout.n]
    for j, spec in enumerate(specimens):
        values = [circle_intensity(phi[w, j], spec.blab) for w in range(len(draws))]
        values = [v for v in values if np.isfinite(v)]
        if values:
            result.specimen_b[spec.name] = float(np.median(values))
        result.specimen_k[spec.name] = float(np.median(k[:, j]))
    _posterior_predictive(result, specimens)


def _posterior_predictive(result: BicepResult, specimens) -> None:
    """How well the fitted line explains the specimens it was fitted to."""
    k = np.array([result.specimen_k.get(s.name, np.nan) for s in specimens])
    b = np.array([result.specimen_b.get(s.name, np.nan) for s in specimens])
    good = np.isfinite(k) & np.isfinite(b)
    if good.sum() < 2 or not np.isfinite(result.b_site):
        return
    predicted = result.b_site + result.slope * k[good]
    residual = b[good] - predicted
    result.sigma_b = float(np.std(residual, ddof=1)) if good.sum() > 1 else np.nan
    spread = float(np.var(b[good]))
    result.ppc = {"rms_residual": float(np.sqrt(np.mean(residual ** 2))),
                  "max_residual": float(np.max(np.abs(residual))),
                  "r_squared": float(1 - np.mean(residual ** 2) / spread) if spread else np.nan,
                  "n": int(good.sum())}


# ---------------------------------------------------------------------------
# Convergence diagnostics
# ---------------------------------------------------------------------------
def gelman_rubin(chains: np.ndarray) -> float:
    """R-hat (Gelman & Rubin, 1992) for a (chains, draws) array."""
    chains = np.asarray(chains, dtype=float)
    m, n = chains.shape
    if m < 2 or n < 2:
        return np.nan
    means = chains.mean(axis=1)
    variances = chains.var(axis=1, ddof=1)
    w = float(np.mean(variances))
    b = n * float(np.var(means, ddof=1))
    if w <= 0:
        return np.nan
    var_hat = (n - 1) / n * w + b / n
    return float(math.sqrt(var_hat / w))


def effective_sample_size(chains: np.ndarray) -> float:
    """Effective sample size from the autocorrelation of the pooled chains."""
    chains = np.asarray(chains, dtype=float)
    m, n = chains.shape
    if m < 1 or n < 4:
        return np.nan
    means = chains.mean(axis=1)
    variances = chains.var(axis=1, ddof=1)
    w = float(np.mean(variances))
    if w <= 0:
        return float(m * n)
    var_hat = (n - 1) / n * w + (n * float(np.var(means, ddof=1)) / n if m > 1 else 0.0)
    rho_sum, t = 0.0, 1
    while t < n - 2:
        rho_t = 1.0 - (w - _mean_autocov(chains, t)) / var_hat
        rho_t1 = 1.0 - (w - _mean_autocov(chains, t + 1)) / var_hat
        if rho_t + rho_t1 < 0:
            break
        rho_sum += rho_t + rho_t1
        t += 2
    tau = 1.0 + 2.0 * rho_sum
    return float(m * n / max(tau, 1e-6))


def _mean_autocov(chains: np.ndarray, lag: int) -> float:
    values = []
    for chain in chains:
        centred = chain - chain.mean()
        if lag >= len(centred):
            continue
        values.append(float(np.mean(centred[:len(centred) - lag] * centred[lag:])))
    return float(np.mean(values)) if values else 0.0


# ---------------------------------------------------------------------------
# Saving and loading
# ---------------------------------------------------------------------------
def save(result: BicepResult, path: str) -> str:
    """Write a result. ``.nc`` uses NetCDF when xarray is installed, else JSON."""
    if path.endswith(".nc"):
        try:
            return _save_netcdf(result, path)
        except ImportError:
            path = path[:-3] + ".json"
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result.to_dict(), fh, indent=2, sort_keys=True, default=_json_default)
    return path


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(type(value))


def _save_netcdf(result: BicepResult, path: str) -> str:
    import xarray as xr
    payload = result.to_dict()
    data = xr.Dataset(
        {"b_site": ("draw", np.asarray(result.samples if result.samples is not None else [])),
         "slope": ("draw", np.asarray(result.slope_samples
                                      if result.slope_samples is not None else []))},
        attrs={k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
               for k, v in payload.items()
               if k not in ("samples", "slope_samples") and v is not None})
    data.to_netcdf(path)
    return path


def load(path: str) -> BicepResult:
    """Read back a saved result."""
    if path.endswith(".nc"):
        import xarray as xr
        with xr.open_dataset(path) as data:
            payload = {}
            for key, value in data.attrs.items():
                try:
                    payload[key] = json.loads(value) if isinstance(value, str) and \
                        value[:1] in "[{" else value
                except (json.JSONDecodeError, TypeError):
                    payload[key] = value
            samples = np.asarray(data["b_site"].values)
            slopes = np.asarray(data["slope"].values)
    else:
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        samples = np.asarray(payload.pop("samples") or [])
        slopes = np.asarray(payload.pop("slope_samples") or [])
    fields = {f for f in BicepResult.__dataclass_fields__}
    result = BicepResult(**{k: v for k, v in payload.items() if k in fields})
    result.samples, result.slope_samples = samples, slopes
    return result


# ---------------------------------------------------------------------------
# MagIC output
# ---------------------------------------------------------------------------
def sites_rows(results: Sequence[BicepResult], analysts: str = "") -> List[dict]:
    """MagIC 3 sites rows for a set of BiCEP results.

    Written as ``int_abs`` with ``int_abs_sigma`` from the credible interval and
    the BiCEP method code, so that a BiCEP site result never overwrites the
    specimen interpretations it was computed from.
    """
    rows = []
    for result in results:
        if not np.isfinite(result.b_site):
            continue
        half = (result.ci_high - result.ci_low) / 2.0
        rows.append({
            "site": result.site,
            "int_abs": result.b_site * 1e-6,
            "int_abs_sigma": half * 1e-6 if np.isfinite(half) else None,
            "int_n_specimens": len(result.specimens),
            "method_codes": "IE-SPEC:LP-PI-TRM:DE-BS",
            "description": (f"BiCEP (Cych et al. 2021), {result.method} sampler, "
                            f"95% credible interval {result.ci_low:.1f}-{result.ci_high:.1f} uT"),
            "citations": "This study; " + DOI,
            "analysts": analysts,
            "result_quality": "g" if result.converged or result.method == "bootstrap" else "b",
        })
    return rows
