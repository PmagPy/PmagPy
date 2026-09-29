"""
MagIC 3-native core for Thellier-type paleointensity analysis.

This is the UI-independent heart of PmagPy Intensity, the fresh-start
replacement for ``programs/thellier_gui.py``. It reads a MagIC 3 contribution
with :mod:`pmagpy.magic_project` (shared with PmagPy Directions), builds one
tidy step table and one Arai data set per specimen, computes the full
Standard Paleointensity Definitions suite with :mod:`pmagpy.pint_stats`,
applies the anisotropy, non-linear TRM and cooling-rate corrections, averages
by sample/site/location, and writes MagIC 3 tables back out. There is no
2.5 <-> 3.0 translation layer anywhere: canonical MagIC 3 column names are used
from input through export.

Design conventions
------------------
* An interpretation's bounds are **Arai point indices** (0..n-1 in the
  specimen's ordered Arai table), never temperatures, so duplicate treatment
  steps and unit conversions never bite. SI treatment values are derived from
  the bounding steps on export and matched to the nearest step on import.
* Measurement rows are addressed by their MagIC ``measurement`` name (a stable
  identifier), not by a constructed row label.
* A measurement flagged ``quality = 'b'`` is honoured everywhere. Because an
  Arai point needs *both* halves of a Z/I pair, flagging either half removes
  the point unless a good duplicate of that half exists -- an invalid half-pair
  is never left in a fit (PmagPy/PmagPy#170).
* Statistics are returned as :class:`pmagpy.pint_stats.Stat`, which carries an
  explicit not-applicable / unavailable / undefined state. No ``-999``.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import pmagpy.contribution_builder as cb
from pmagpy import magic_project as mp
from pmagpy import pint_stats as ps
from pmagpy.magic_project import (COORD_GEOGRAPHIC, COORD_SPECIMEN, COORD_TILT, KELVIN_OFFSET, is_null,
                                  carry_metadata, is_metadata_column, split_codes, join_codes,
                                  natural_key, to_float, trim_to_model, validate_directory)

APP_ID = "pmagpy_intensity"          # written to software_packages
SOFTWARE_TAG = mp.software_tag(APP_ID)
PMAGPY_VERSION = mp.PMAGPY_VERSION

# ---------------------------------------------------------------------------
# Method codes
# ---------------------------------------------------------------------------
#: the paleointensity experiment protocols this core understands
PI_PROTOCOLS = ("LP-PI-TRM", "LP-PI-M")
#: the zero-field (demagnetising) half of a Thellier pair
CODES_Z = ("LT-T-Z", "LT-M-Z")
#: the in-field (pTRM acquisition) half of a Thellier pair
CODES_I = ("LT-T-I", "LT-M-I")
CODES_NRM = ("LT-NO",)
CODES_PTRM_CHECK = ("LT-PTRM-I", "LT-PMRM-I")
CODES_TAIL_CHECK = ("LT-PTRM-MD", "LT-PMRM-MD")
CODES_ADDITIVITY = ("LT-PTRM-AC", "LT-PMRM-AC")
#: experiments that share a measurements file with the paleointensity run but
#: are not part of the Arai plot
CODE_TRM_ACQUISITION = "LP-TRM"           # non-linear TRM calibration
CODE_ANISO_TRM = "LP-AN-TRM"
CODE_ANISO_ARM = "LP-AN-ARM"
CODE_COOLING_RATE = "LP-CR-TRM"
EXCLUDED_PROTOCOLS = (CODE_TRM_ACQUISITION, "LP-TRM-TD", CODE_ANISO_TRM, CODE_ANISO_ARM,
                      CODE_COOLING_RATE, "LP-X", "LP-PI-MULT", "LP-PI-REL-PT", "LP-PI-ARM")
#: protocol labels written to the specimens table alongside the result
PROTOCOL_CODES = {"IZZI": "LP-PI-BT-IZZI", "Coe": "LP-PI-TRM-ZI", "Aitken": "LP-PI-TRM-IZ",
                  "Thellier-Thellier": "LP-PI-II"}

STEP_NRM, STEP_Z, STEP_I = "NRM", "Z", "I"
STEP_PTRM, STEP_TAIL, STEP_ADD = "P", "T", "A"
STEP_LABELS = {STEP_NRM: "NRM", STEP_Z: "zero field", STEP_I: "in field",
               STEP_PTRM: "pTRM check", STEP_TAIL: "tail check", STEP_ADD: "additivity check"}

#: method codes recording which corrections were applied
CORRECTION_CODES = {"anisotropy_trm": "DA-AC-ATRM", "anisotropy_arm": "DA-AC-AARM",
                    "cooling_rate": "DA-CR", "nlt": "DA-NL"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class AraiData:
    """The Arai plot of one specimen, built from its step table.

    ``x``/``y`` are the pTRM gained and the NRM remaining at each Arai point;
    ``rows`` maps every point back to the measurement rows it came from.
    """
    x: np.ndarray
    y: np.ndarray
    temps: np.ndarray
    nrm_vectors: np.ndarray
    trm_vectors: np.ndarray
    steps: List[str]
    rows: List[dict]                       # {'z': idx, 'i': idx or None}
    ptrm_checks: List[ps.PtrmCheck] = field(default_factory=list)
    tail_checks: List[ps.TailCheck] = field(default_factory=list)
    additivity_checks: List[ps.AdditivityCheck] = field(default_factory=list)
    check_rows: dict = field(default_factory=dict)   # kind -> [step-table index]
    dropped: List[str] = field(default_factory=list)  # human-readable notes
    protocol: str = ""

    @property
    def n(self) -> int:
        return len(self.x)


@dataclass
class PintSpecimen:
    """One specimen's paleointensity experiment."""
    name: str
    sample: str
    site: str
    location: str
    steps: pd.DataFrame
    blab: float = np.nan                       # tesla
    blab_dir: Optional[np.ndarray] = None      # unit vector, specimen coordinates
    experiments: Tuple[str, ...] = ()
    method_codes: Tuple[str, ...] = ()
    microwave: bool = False
    arai: Optional[AraiData] = None
    warnings: List[str] = field(default_factory=list)

    @property
    def nrm(self) -> float:
        return float(self.arai.y[0]) if self.arai is not None and self.arai.n else np.nan

    @property
    def blab_uT(self) -> float:
        return self.blab * 1e6 if np.isfinite(self.blab) else np.nan

    @property
    def unit(self) -> str:
        return "K"

    def temperature_label(self, index: int) -> str:
        if self.arai is None or not (0 <= index < self.arai.n):
            return ""
        return f"{self.arai.temps[index] - KELVIN_OFFSET:.0f}°C"


@dataclass
class Interpretation:
    """A saved paleointensity interpretation: a specimen and a pair of bounds."""
    specimen: str
    imin: int = 0
    imax: int = -1
    quality: str = "g"
    name: str = "A"
    notes: str = ""
    #: corrections the analyst has switched on for this specimen; ``None``
    #: means "use whatever data are available" (the default). ``True`` applies
    #: the correction even when the anisotropy policy (alteration limit,
    #: F-test) would not -- it is what "always" means, and what a stored
    #: result's DA-AC code says was done.
    use_anisotropy: Optional[bool] = None
    use_nlt: Optional[bool] = None
    use_cooling_rate: Optional[bool] = None
    #: the anisotropy tensor to use when the specimen has more than one
    #: ('ATRM' or 'AARM'); ``None`` takes the default (AARM, as the legacy GUI)
    anisotropy_type: Optional[str] = None

    def key(self) -> tuple:
        return (self.specimen, self.name)


@dataclass
class Correction:
    """One applied correction, with the factor and where it came from."""
    kind: str
    factor: float = np.nan
    applied: bool = False
    method_code: str = ""
    source: str = ""
    detail: dict = field(default_factory=dict)
    message: str = ""


@dataclass
class PintResult:
    """A specimen's paleointensity result: statistics, corrections, provenance."""
    specimen: str
    sample: str = ""
    site: str = ""
    location: str = ""
    imin: int = 0
    imax: int = 0
    tmin: float = np.nan
    tmax: float = np.nan
    blab: float = np.nan
    b_anc_uncorrected: float = np.nan
    b_anc: float = np.nan
    sigma: float = np.nan
    stats: Dict[str, ps.Stat] = field(default_factory=dict)
    corrections: Dict[str, Correction] = field(default_factory=dict)
    quality: str = "g"
    passed: Optional[bool] = None
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def stat(self, key: str) -> ps.Stat:
        return self.stats.get(key, ps.Stat(key, None, ps.State.UNDEFINED, "not computed"))

    @property
    def correction_codes(self) -> List[str]:
        return [c.method_code for c in self.corrections.values() if c.applied and c.method_code]

    @property
    def corrected(self) -> bool:
        return any(c.applied for c in self.corrections.values())


# ---------------------------------------------------------------------------
# Criteria
# ---------------------------------------------------------------------------
#: statistics that carry a sign but are judged by their magnitude. The Arai
#: curvature k (and k' over the selected segment) is signed by the side of the
#: data its best-fit circle's centre lies on, i.e. by which way the plot bends
#: (Paterson, 2011); the published thresholds -- |k'| <= 0.164 (CCRIT), 0.300
#: (RCRIT), 0.270 (the modified sets of Paterson et al., 2014) -- are on the
#: magnitude, and the legacy Thellier GUI tested abs(k) and abs(k') too
#: (dialogs/thellier_gui_lib.py). Testing the signed value let every strongly
#: curved plot of negative k' pass (PmagPy/PmagPy#246).
MAGNITUDE_CRITERIA = ("k", "k_prime")


@dataclass(frozen=True)
class Criterion:
    """One acceptance threshold on one statistic.

    A curvature criterion (:data:`MAGNITUDE_CRITERIA`) is tested on the
    magnitude of the statistic, so ``Criterion("k_prime", "<=", 0.164)``
    means |k'| <= 0.164.
    """
    key: str
    operation: str            # '<=', '>=', '=' , '<', '>'
    value: float | bool

    def test(self, stat: ps.Stat) -> Optional[bool]:
        """True / False, or None when the statistic has no value to test."""
        if not stat:
            return None
        v = stat.value
        if isinstance(self.value, bool):
            return bool(v) == bool(self.value)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if self.key in MAGNITUDE_CRITERIA:
            v = abs(v)
        op = self.operation
        if op == "<=":
            return v <= self.value
        if op == ">=":
            return v >= self.value
        if op == "<":
            return v < self.value
        if op == ">":
            return v > self.value
        return v == self.value

    def describe(self) -> str:
        spec = ps.describe(self.key)
        value = "true" if self.value is True else ("false" if self.value is False else f"{self.value:g}")
        label = f"|{spec.label}|" if self.key in MAGNITUDE_CRITERIA else spec.label
        return f"{label} {self.operation} {value}"


@dataclass
class CriteriaSet:
    """A named set of specimen- and site-level acceptance criteria."""
    name: str
    citation: str = ""
    doi: str = ""
    description: str = ""
    specimen: Tuple[Criterion, ...] = ()
    site: Tuple[Criterion, ...] = ()

    #: site criteria of which passing either one is enough: the scatter of a
    #: mean may be small in microtesla *or* as a percentage, as the legacy
    #: Thellier GUI applies ``int_abs_sigma`` and ``int_abs_sigma_perc``
    #: (a mean fails only when it fails both that are set)
    EITHER = ("sd", "dB_percent")

    def evaluate(self, stats: Dict[str, ps.Stat], level: str = "specimen") -> dict:
        """Test every criterion; report pass / fail / not applicable with reasons."""
        rows, failures, not_applicable = [], [], []
        for crit in (self.specimen if level == "specimen" else self.site):
            stat = stats.get(crit.key, ps.Stat(crit.key, None, ps.State.UNDEFINED, "not computed"))
            verdict = crit.test(stat)
            rows.append({"key": crit.key, "criterion": crit.describe(), "value": stat,
                         "pass": verdict})
        if level != "specimen":
            either = [r for r in rows if r["key"] in self.EITHER]
            if len(either) > 1 and any(r["pass"] is True for r in either):
                for r in either:
                    if r["pass"] is False:
                        r["pass"] = True
                        r["note"] = "passes on the other scatter criterion"
        for r in rows:
            if r["pass"] is False:
                failures.append(f"{r['criterion']} (got {r['value'].text()})")
            elif r["pass"] is None:
                not_applicable.append(f"{r['criterion']} ({r['value'].reason or 'no value'})")
        passed = None if not rows else all(r["pass"] is not False for r in rows)
        return {"rows": rows, "passed": passed, "failures": failures,
                "not_applicable": not_applicable}

    def with_criterion(self, key: str, operation: str, value) -> "CriteriaSet":
        """A copy with one criterion added or replaced (used for the Ziggie option)."""
        kept = tuple(c for c in self.specimen if c.key != key)
        return CriteriaSet(self.name, self.citation, self.doi, self.description,
                           kept + (Criterion(key, operation, value),), self.site)


def _crit(pairs) -> Tuple[Criterion, ...]:
    return tuple(Criterion(k, op, v) for k, op, v in pairs)


#: Named criteria sets, each sourced from its publication. Thresholds for
#: PICRIT03, SELCRIT2, TTA and TTB (and their modified forms) are Table 2 of
#: Paterson et al. (2014); CCRIT/RCRIT and the site-level limits follow
#: Cromwell et al. (2015) as tabulated by Sanchez-Moreno et al. (2025).
CRITERIA_SETS: Dict[str, CriteriaSet] = {}


def _register(cs: CriteriaSet) -> CriteriaSet:
    CRITERIA_SETS[cs.name] = cs
    return cs


_register(CriteriaSet(
    "CCRIT", "Cromwell, Tauxe, Staudigel & Ron (2015)", "10.1016/j.pepi.2014.12.007",
    "Strict criteria calibrated on historic Hawaiian lavas with known field strength.",
    _crit([("n", ">=", 4), ("FRAC", ">=", 0.78), ("beta", "<=", 0.1), ("k_prime", "<=", 0.164),
           ("MAD_Free", "<=", 5), ("DANG", "<=", 10), ("n_pTRM", ">=", 2), ("SCAT", "=", True)]),
    _crit([("N", ">=", 3), ("sd", "<=", 6.0), ("dB_percent", "<=", 15.0)])))

_register(CriteriaSet(
    "RCRIT", "Cromwell, Tauxe, Staudigel & Ron (2015), relaxed variant",
    "10.1016/j.pepi.2014.12.007",
    "The relaxed companion to CCRIT, for material that cannot meet the strict thresholds.",
    _crit([("n", ">=", 4), ("FRAC", ">=", 0.60), ("beta", "<=", 0.1), ("GAP_MAX", "<=", 0.6),
           ("k_prime", "<=", 0.300), ("MAD_Free", "<=", 12), ("DANG", "<=", 10),
           ("n_pTRM", ">=", 2), ("SCAT", "=", True)]),
    _crit([("N", ">=", 3), ("sd", "<=", 6.0), ("dB_percent", "<=", 15.0)])))

_register(CriteriaSet(
    "TTA", "Leonhardt, Heunemann & Krasa (2004), ThellierTool v4.22 class A",
    "10.1029/2004GC000807", "The ThellierTool class A defaults.",
    _crit([("n", ">=", 5), ("f", ">=", 0.5), ("beta", "<=", 0.1), ("q", ">=", 5),
           ("MAD_Anc", "<=", 6), ("alpha", "<=", 15), ("dCK", "<=", 5), ("delta_pal", "<=", 5),
           ("dTR", "<=", 10), ("delta_t_star", "<=", 3)]),
    _crit([("N", ">=", 3), ("sd", "<=", 8.0), ("dB_percent", "<=", 25.0)])))

_register(CriteriaSet(
    "TTB", "Leonhardt, Heunemann & Krasa (2004), ThellierTool v4.22 class B",
    "10.1029/2004GC000807", "The ThellierTool class B defaults.",
    _crit([("n", ">=", 5), ("f", ">=", 0.3), ("beta", "<=", 0.15), ("MAD_Anc", "<=", 15),
           ("alpha", "<=", 15), ("dCK", "<=", 7), ("delta_pal", "<=", 10), ("dTR", "<=", 20),
           ("delta_t_star", "<=", 99)]),
    _crit([("N", ">=", 3), ("sd", "<=", 8.0), ("dB_percent", "<=", 25.0)])))

_register(CriteriaSet(
    "TTA (modified)", "Paterson, Tauxe, Biggin, Shaar & Jonestrask (2014), Table 2",
    "10.1002/2013GC005135",
    "TTA with thresholds relaxed to the 95th percentile of ideal single-domain behaviour.",
    _crit([("n", ">=", 5), ("f", ">=", 0.35), ("beta", "<=", 0.1), ("q", ">=", 5),
           ("MAD_Anc", "<=", 6), ("alpha", "<=", 15), ("dCK", "<=", 7), ("delta_pal", "<=", 10),
           ("dTR", "<=", 10), ("delta_t_star", "<=", 9), ("k_prime", "<=", 0.270)]),
    _crit([("N", ">=", 3), ("sd", "<=", 8.0), ("dB_percent", "<=", 25.0)])))

_register(CriteriaSet(
    "TTB (modified)", "Paterson et al. (2014), Table 2", "10.1002/2013GC005135",
    "TTB with thresholds relaxed to the 99th percentile of ideal single-domain behaviour.",
    _crit([("n", ">=", 5), ("f", ">=", 0.35), ("beta", "<=", 0.15), ("MAD_Anc", "<=", 15),
           ("alpha", "<=", 15), ("dCK", "<=", 9), ("delta_pal", "<=", 18), ("dTR", "<=", 20),
           ("delta_t_star", "<=", 99), ("k_prime", "<=", 0.270)]),
    _crit([("N", ">=", 3), ("sd", "<=", 8.0), ("dB_percent", "<=", 25.0)])))

_register(CriteriaSet(
    "PICRIT03", "Kissel & Laj (2004)", "10.1016/j.pepi.2003.11.006",
    "PICRIT-03, without the alpha' criterion (which needs an independent direction).",
    _crit([("n", ">=", 4), ("f", ">=", 0.35), ("beta", "<=", 0.1), ("q", ">=", 2),
           ("MAD_Anc", "<=", 7), ("n_pTRM", ">=", 3), ("DRAT", "<=", 7), ("CDRAT", "<=", 10)]),
    ()))

_register(CriteriaSet(
    "PICRIT03 (modified)", "Paterson et al. (2014), Table 2", "10.1002/2013GC005135",
    "PICRIT-03 with DRAT and CDRAT relaxed to ideal single-domain behaviour.",
    _crit([("n", ">=", 4), ("f", ">=", 0.35), ("beta", "<=", 0.1), ("q", ">=", 2),
           ("MAD_Anc", "<=", 7), ("n_pTRM", ">=", 3), ("DRAT", "<=", 10), ("CDRAT", "<=", 11),
           ("k_prime", "<=", 0.270)]), ()))

_register(CriteriaSet(
    "SELCRIT2", "Biggin, Perrin & Dekkers (2007)", "10.1016/j.epsl.2007.05.016",
    "SELCRIT2 as used for the Thellier database compilations.",
    _crit([("n", ">=", 4), ("f", ">=", 0.15), ("beta", "<=", 0.1), ("q", ">=", 1),
           ("MAD_Anc", "<=", 15), ("alpha", "<=", 15), ("DRAT", "<=", 10),
           ("DRAT_tail", "<=", 10)]), ()))

_register(CriteriaSet(
    "SELCRIT2 (modified)", "Paterson et al. (2014), Table 2", "10.1002/2013GC005135",
    "SELCRIT2 with the minimum NRM fraction raised to 0.35.",
    _crit([("n", ">=", 4), ("f", ">=", 0.35), ("beta", "<=", 0.1), ("q", ">=", 1),
           ("MAD_Anc", "<=", 15), ("alpha", "<=", 15), ("DRAT", "<=", 10),
           ("DRAT_tail", "<=", 10), ("k_prime", "<=", 0.270)]), ()))

_register(CriteriaSet(
    "None", "", "", "No acceptance criteria: every interpretation is listed as it is.", (), ()))

#: the criteria set the application starts with
DEFAULT_CRITERIA = "CCRIT"

#: how far a .redo's temperature may be from a real step before it is reported (K)
REDO_STEP_TOLERANCE = 1.0

#: the extra criterion Tully & Paterson (2025) recommend for IZZI experiments
ZIGGIE_CRITERION = Criterion("Ziggie", "<=", ps.ZIGGIE_CRITERION)

#: curvature thresholds are *not* universal; these are the published ones,
#: each with the material and protocol it was calibrated on
CURVATURE_PRESETS = {
    "strict (|k| <= 0.164)": (0.164, "Paterson (2011), from 38 specimens of known grain size; "
                                     "adopted by CCRIT for glassy basalt", "10.1029/2011JB008369"),
    "relaxed (|k| <= 0.270)": (0.270, "Paterson (2011) relaxed threshold; used by RCRIT and by the "
                                      "modified criteria sets of Paterson et al. (2014)",
                               "10.1029/2011JB008369"),
    "none": (None, "no curvature criterion", ""),
}


# ---------------------------------------------------------------------------
# Building the step table
# ---------------------------------------------------------------------------
def _step_kind(codes: Sequence[str]) -> Optional[str]:
    """Classify a measurement row of a paleointensity experiment."""
    cset = set(codes)
    if cset & set(CODES_PTRM_CHECK):
        return STEP_PTRM
    if cset & set(CODES_TAIL_CHECK):
        return STEP_TAIL
    if cset & set(CODES_ADDITIVITY):
        return STEP_ADD
    if cset & set(CODES_NRM):
        return STEP_NRM
    if cset & set(CODES_I):
        return STEP_I
    if cset & set(CODES_Z):
        return STEP_Z
    return None


#: why a microwave experiment is not read. Its steps are not temperatures: a
#: zero-field and an in-field step of one Arai point are matched by their
#: step number (``treat_step_num``), with a power, time and absorbed energy
#: that differ between the two, whereas every step here is identified by
#: ``treat_temp``. Read as a thermal experiment, every step would collapse
#: onto one blank temperature.
MICROWAVE_UNSUPPORTED = ("PmagPy Intensity identifies each step by its temperature (treat_temp), and a "
                         "microwave step is identified by its step number and power; microwave "
                         "experiments are not supported yet (the legacy Thellier GUI has a microwave mode)")


def _is_microwave(spec_meas: pd.DataFrame) -> bool:
    """True for a specimen whose paleointensity steps are microwave (LT-M-*) and none thermal."""
    codes = {c for v in spec_meas["method_codes"].fillna("") for c in split_codes(v)}
    return bool(codes & {"LT-M-Z", "LT-M-I"}) and not (codes & {"LT-T-Z", "LT-T-I"})


STEP_SOURCE_COLUMNS = ("method_codes", "dir_dec", "dir_inc", "treat_temp", "treat_dc_field", "treat_dc_field_phi",
                       "treat_dc_field_theta", "quality", "measurement", "description", "specimen", "sequence")


def build_step_table(spec_meas: pd.DataFrame, intensity_col: str,
                     warnings: Optional[list] = None) -> pd.DataFrame:
    """Turn a specimen's paleointensity measurement rows into an ordered step table.

    Rows that belong to another experiment sharing the file (anisotropy, TRM
    acquisition, cooling rate, AF demagnetisation) are left out; they are read
    separately by :class:`PintData`.

    The rows are read as plain dicts and the table built once at the end: a
    study of a few hundred specimens opens in a fraction of the time a
    row-by-row ``iterrows`` pass took.
    """
    n = len(spec_meas)
    if n == 0:
        return pd.DataFrame()
    # only the columns a step is read from: a MagIC measurements table has a hundred
    # columns, and turning every one of them into a dict per row is most of the cost
    wanted = [c for c in STEP_SOURCE_COLUMNS + (intensity_col,) if c in spec_meas.columns]
    records = spec_meas[wanted].to_dict("records")
    for rec, index in zip(records, spec_meas.index):
        rec["_index"] = index
    if "sequence" in spec_meas.columns:
        order = pd.to_numeric(spec_meas["sequence"], errors="coerce").tolist()
        keys = [o if (o is not None and o == o) else float(k) for k, o in enumerate(order)]
    else:
        keys = list(range(n))
    records = [rec for _, rec in sorted(zip(keys, records), key=lambda kv: kv[0])]   # a stable sort

    protocols, excluded = set(PI_PROTOCOLS), set(EXCLUDED_PROTOCOLS)
    rows = []
    for pos, rec in enumerate(records):
        codes = split_codes(rec.get("method_codes", ""))
        cset = set(codes)
        if not (cset & protocols):
            continue
        if cset & excluded:
            continue
        kind = _step_kind(codes)
        if kind is None:
            continue
        moment = to_float(rec.get(intensity_col))
        dec, inc = to_float(rec.get("dir_dec")), to_float(rec.get("dir_inc"))
        if np.isnan(moment) or np.isnan(dec) or np.isnan(inc):
            if warnings is not None:
                measurement = rec.get("measurement")
                if measurement is None or is_null(measurement):
                    measurement = pos
                warnings.append(f"{rec.get('specimen', '?')}: step "
                                f"{measurement} has no direction or moment; skipped")
            continue
        temp = to_float(rec.get("treat_temp"), np.nan)
        if np.isnan(temp):
            temp = KELVIN_OFFSET
        vec = ps.dir_to_cart(dec, inc, moment)
        pair = ""
        if "LP-PI-TRM-ZI" in cset:
            pair = "ZI"
        elif "LP-PI-TRM-IZ" in cset:
            pair = "IZ"
        quality = rec.get("quality", "g")
        quality = "g" if quality is None or is_null(quality) else (str(quality).strip() or "g")
        description = rec.get("description", "")
        description = "" if description is None or is_null(description) else str(description)
        measurement = rec.get("measurement", "")
        measurement = "" if measurement is None or is_null(measurement) else str(measurement)
        rows.append({
            "meas_pos": rec["_index"],
            "measurement": measurement,
            "sequence": len(rows),
            "kind": kind,
            "treat_temp": float(temp),
            "treat_dc_field": to_float(rec.get("treat_dc_field"), 0.0),
            # left NaN when not recorded: a missing direction is unknown, not +x
            "field_phi": to_float(rec.get("treat_dc_field_phi"), np.nan),
            "field_theta": to_float(rec.get("treat_dc_field_theta"), np.nan),
            "dec": dec, "inc": inc, "moment": moment,
            "x": vec[0], "y": vec[1], "z": vec[2],
            "pair": pair,
            "quality": quality,
            "method_codes": join_codes(codes),
            "description": description,
        })
    steps = pd.DataFrame(rows)
    if len(steps):
        labels = [f"{t - KELVIN_OFFSET:.0f}°C" for t in steps["treat_temp"]]
        steps["label"] = ["NRM" if k == STEP_NRM else lab for k, lab in zip(steps["kind"], labels)]
    return steps


#: a laboratory field above this (tesla) is taken to be recorded in the wrong
#: unit: Thellier experiments use tens of microtesla, and MagIC stores
#: ``treat_dc_field`` in tesla, so 40 (meaning 40 uT) would make B_anc 1e6 too large
LAB_FIELD_MAX_TESLA = 1e-3


def _lab_field(steps: pd.DataFrame, warnings: Optional[list] = None,
               specimen: str = "") -> Tuple[float, Optional[np.ndarray]]:
    """The laboratory field strength (T) and unit direction from the in-field steps.

    The direction is None when no in-field step records ``treat_dc_field_phi``
    and ``treat_dc_field_theta``: it is then unknown, and the statistics that
    depend on it (theta, gamma, delta_t*, CRM%) and the anisotropy correction
    say so, rather than being computed against an assumed +x field. That, and
    a field strength that cannot be in tesla, are reported in ``warnings``.
    """
    infield = steps[steps["kind"].isin([STEP_I, STEP_PTRM, STEP_ADD])]
    fields = pd.to_numeric(infield["treat_dc_field"], errors="coerce").dropna()
    fields = fields[fields > 0]
    blab = float(fields.mode().iloc[0]) if len(fields) else np.nan
    if np.isfinite(blab) and blab > LAB_FIELD_MAX_TESLA and warnings is not None:
        warnings.append(f"{specimen}: the laboratory field (treat_dc_field) is {blab:g}, which "
                        f"cannot be tesla; MagIC records it in T (40 uT is 4e-05), so every "
                        f"intensity of this specimen is wrong by the unit's factor")
    if len(infield):
        phi = pd.to_numeric(infield["field_phi"], errors="coerce")
        theta = pd.to_numeric(infield["field_theta"], errors="coerce")
        known = phi.notna() & theta.notna()
        if known.any():
            direction = ps.dir_to_cart(float(phi[known].mode().iloc[0]),
                                       float(theta[known].mode().iloc[0]), 1.0)
        else:
            direction = None
            if warnings is not None:
                warnings.append(f"{specimen}: the laboratory field direction (treat_dc_field_phi, "
                                f"treat_dc_field_theta) is not recorded, so theta, gamma, delta_t*, "
                                f"CRM% and the anisotropy correction are not computed")
    else:
        direction = np.array([0.0, 0.0, -1.0])
    return blab, direction


def _good(steps: pd.DataFrame) -> pd.DataFrame:
    return steps[steps["quality"] != "b"]


def build_arai(steps: pd.DataFrame, warnings: Optional[list] = None) -> Optional[AraiData]:
    """Build the Arai plot from a step table, honouring the ``quality`` flags.

    A Z step and an I step at the same treatment make one Arai point. When one
    half of a pair is flagged bad the good duplicate at that treatment is used
    if there is one; otherwise the whole point is dropped, because half a pair
    cannot define an Arai point (PmagPy/PmagPy#170). Every drop is recorded in
    ``AraiData.dropped``.
    """
    if steps is None or len(steps) == 0:
        return None
    notes: List[str] = []
    usable = steps.copy()
    # the rows as dicts, indexed by (kind, temperature) in table order: every
    # lookup below is a dictionary read rather than a boolean filter of the frame
    records = usable.to_dict("records")
    by_kind_temp: Dict[tuple, list] = {}
    for rec in records:
        by_kind_temp.setdefault((rec["kind"], float(rec["treat_temp"])), []).append(rec)

    def pick(kind: str, temp: float) -> Optional[dict]:
        """The first good row of ``kind`` at ``temp``; None when all are bad."""
        rows = by_kind_temp.get((kind, float(temp)), [])
        if not rows:
            return None
        good = [r for r in rows if r["quality"] != "b"]
        if not good:
            notes.append(f"{temp - KELVIN_OFFSET:.0f}°C {STEP_LABELS[kind]}: every measurement "
                         f"is flagged bad")
            return None
        if len(good) < len(rows):
            notes.append(f"{temp - KELVIN_OFFSET:.0f}°C {STEP_LABELS[kind]}: a flagged duplicate "
                         f"was replaced by a good repeat")
        return good[0]

    nrm_rows = [r for r in records if r["kind"] == STEP_NRM]
    nrm_temps = {float(r["treat_temp"]) for r in nrm_rows}
    # the original Thellier-Thellier protocol has no zero-field step: each
    # temperature is measured twice in antiparallel fields, and the NRM left
    # and the pTRM gained are the half sum and half difference of the pair
    antiparallel = _antiparallel_pairs(usable)
    zero_temps = sorted({float(r["treat_temp"]) for r in records if r["kind"] in (STEP_NRM, STEP_Z)}
                        | set(antiparallel))
    x, y, temps, nrmv, trmv, labels, rows = [], [], [], [], [], [], []
    for temp in zero_temps:
        if temp in antiparallel:
            first, second = antiparallel[temp]
            if first["quality"] == "b" or second["quality"] == "b":
                notes.append(f"{temp - KELVIN_OFFSET:.0f}°C: half of the antiparallel "
                             f"Thellier-Thellier pair is flagged bad, so the point is left out")
                continue
            m1 = np.array([first["x"], first["y"], first["z"]], dtype=float)
            m2 = np.array([second["x"], second["y"], second["z"]], dtype=float)
            zv, pt = (m1 + m2) / 2.0, (m1 - m2) / 2.0
            x.append(float(np.linalg.norm(pt)))
            y.append(float(np.linalg.norm(zv)))
            temps.append(float(temp))
            nrmv.append(zv)
            trmv.append(pt)
            labels.append("II")
            rows.append({"z": int(first["sequence"]), "i": int(second["sequence"]),
                         "temp": float(temp)})
            continue
        kind = STEP_NRM if temp in nrm_temps else STEP_Z
        z_row = pick(kind, temp)
        if z_row is None and kind == STEP_NRM:
            z_row = pick(STEP_Z, temp)
        if z_row is None:
            continue
        i_row = pick(STEP_I, temp)
        has_infield = bool(by_kind_temp.get((STEP_I, float(temp))))
        if has_infield and i_row is None:
            notes.append(f"{temp - KELVIN_OFFSET:.0f}°C: the in-field half of the pair is flagged "
                         f"bad, so the whole Arai point is left out")
            continue
        zv = np.array([z_row["x"], z_row["y"], z_row["z"]], dtype=float)
        if i_row is not None:
            iv = np.array([i_row["x"], i_row["y"], i_row["z"]], dtype=float)
            pt = iv - zv
            label = z_row["pair"] or i_row["pair"] or ("ZI" if z_row["sequence"] < i_row["sequence"] else "IZ")
        elif kind == STEP_NRM or not x:
            # the first step is the NRM: no pTRM has been given yet, so the
            # point belongs at the origin of the pTRM axis
            pt = np.zeros(3)
            label = STEP_NRM
        else:
            # a zero-field step whose temperature was never measured in field
            # has no pTRM to plot against: it is not an Arai point at all, and
            # placing it at x = 0 would drag the fit toward the origin
            notes.append(f"{temp - KELVIN_OFFSET:.0f}°C: a zero-field step with no in-field "
                         f"step, so there is no pTRM to plot it against")
            continue
        x.append(float(np.linalg.norm(pt)))
        y.append(float(np.linalg.norm(zv)))
        temps.append(float(temp))
        nrmv.append(zv)
        trmv.append(pt)
        labels.append(label)
        rows.append({"z": int(z_row["sequence"]), "i": None if i_row is None else int(i_row["sequence"]),
                     "temp": float(temp)})

    if len(x) < 2:
        if warnings is not None and notes:
            warnings.extend(notes)
        return None

    temps_arr = np.array(temps, dtype=float)
    index_of = {t: k for k, t in enumerate(temps)}
    # a bad NRM does not stop the analysis: the first good zero-field step
    # normalises instead (issue #170, and Tauxe's comment on it)
    if labels and labels[0] != STEP_NRM and nrm_rows and all(r["quality"] == "b" for r in nrm_rows):
        notes.append("the NRM step is flagged bad; the first good zero-field step normalises the plot")

    # walk the measurement sequence to attach the checks to the state they were
    # measured against
    ptrm, tail, add = [], [], []
    check_rows = {STEP_PTRM: [], STEP_TAIL: [], STEP_ADD: []}
    peak = None
    last_zero_vec = None
    last_infield_vec = {}

    def peak_index(default: int) -> int:
        """The Arai point the peak temperature corresponds to.

        A check performed after a temperature that has no Arai point of its own
        must still be compared against how far the experiment had got, so the
        nearest point at or below the peak is used rather than the check's own.
        """
        if peak is None:
            return default
        below = [k for k, t in enumerate(temps) if t <= peak]
        return below[-1] if below else default
    for row in sorted(records, key=lambda r: r["sequence"]):
        vec = np.array([row["x"], row["y"], row["z"]], dtype=float)
        kind, temp, bad = row["kind"], float(row["treat_temp"]), row["quality"] == "b"
        if kind == STEP_PTRM and temp in index_of:
            if bad:
                notes.append(f"{temp - KELVIN_OFFSET:.0f}°C pTRM check: flagged bad, left out")
            elif last_zero_vec is not None:
                diff = vec - last_zero_vec
                ptrm.append(ps.PtrmCheck(i=index_of[temp], j=peak_index(index_of[temp]),
                                         x=float(np.linalg.norm(diff)), vector=diff))
                check_rows[STEP_PTRM].append(int(row["sequence"]))
        elif kind == STEP_TAIL and temp in index_of:
            if bad:
                notes.append(f"{temp - KELVIN_OFFSET:.0f}°C tail check: flagged bad, left out")
            else:
                tail.append(ps.TailCheck(i=index_of[temp], y=float(np.linalg.norm(vec)), vector=vec))
                check_rows[STEP_TAIL].append(int(row["sequence"]))
        elif kind == STEP_ADD and temp in index_of:
            base = last_infield_vec.get(peak)
            if bad:
                notes.append(f"{temp - KELVIN_OFFSET:.0f}°C additivity check: flagged bad, left out")
            elif base is not None:
                star = base - vec
                add.append(ps.AdditivityCheck(i=index_of[temp], j=peak_index(index_of[temp]),
                                              x=float(np.linalg.norm(star)), vector=star))
                check_rows[STEP_ADD].append(int(row["sequence"]))
        if kind in (STEP_NRM, STEP_Z, STEP_I) and not bad:
            peak = temp if peak is None else max(peak, temp)
        if kind in (STEP_NRM, STEP_Z, STEP_TAIL) and not bad:
            last_zero_vec = vec
        if kind == STEP_I and not bad:
            last_infield_vec[temp] = vec

    protocol = _protocol_of(labels, tail, add)
    if warnings is not None:
        warnings.extend(notes)
    return AraiData(x=np.array(x), y=np.array(y), temps=temps_arr,
                    nrm_vectors=np.array(nrmv), trm_vectors=np.array(trmv),
                    steps=labels, rows=rows, ptrm_checks=ptrm, tail_checks=tail,
                    additivity_checks=add, check_rows=check_rows, dropped=notes,
                    protocol=protocol)


def _antiparallel_pairs(steps: pd.DataFrame) -> Dict[float, Tuple[pd.Series, pd.Series]]:
    """Temperatures measured twice in antiparallel laboratory fields.

    That is the original Thellier & Thellier (1959) protocol: there is no
    zero-field step, so the NRM remaining and the pTRM gained are the half sum
    and the half difference of the two in-field measurements. Only used when
    the temperature has no zero-field step of its own.
    """
    out: Dict[float, Tuple[pd.Series, pd.Series]] = {}
    zero_temps = set(steps[steps["kind"].isin([STEP_NRM, STEP_Z])]["treat_temp"])
    infield = steps[steps["kind"] == STEP_I]
    for temp, group in infield.groupby("treat_temp"):
        if temp in zero_temps or len(group) < 2:
            continue
        rows = list(group.sort_values("sequence").iterrows())
        first = rows[0][1]
        d1 = ps.dir_to_cart(first["field_phi"], first["field_theta"], 1.0)
        for _, other in rows[1:]:
            d2 = ps.dir_to_cart(other["field_phi"], other["field_theta"], 1.0)
            if float(np.dot(d1, d2)) < -0.9:
                out[float(temp)] = (first, other)
                break
    return out


def _protocol_of(labels: Sequence[str], tail, add) -> str:
    kinds = set(labels) - {STEP_NRM}
    if "II" in kinds:
        return "Thellier-Thellier"
    if {"ZI", "IZ"} <= kinds:
        return "IZZI"
    if kinds == {"ZI"}:
        return "Coe"
    if kinds == {"IZ"}:
        return "Aitken"
    return "Thellier"


def experiment(spec: PintSpecimen, chrm: Optional[np.ndarray] = None) -> Optional[ps.Experiment]:
    """The :class:`pmagpy.pint_stats.Experiment` view of a specimen."""
    a = spec.arai
    if a is None:
        return None
    return ps.Experiment(x=a.x, y=a.y, temps=a.temps, nrm_vectors=a.nrm_vectors,
                         trm_vectors=a.trm_vectors, steps=a.steps, blab=spec.blab_uT,
                         blab_orient=spec.blab_dir, ptrm_checks=a.ptrm_checks,
                         tail_checks=a.tail_checks, additivity_checks=a.additivity_checks,
                         chrm=chrm)


# ---------------------------------------------------------------------------
# Auxiliary experiments: anisotropy, non-linear TRM, cooling rate
# ---------------------------------------------------------------------------
def parse_aniso_s(text) -> Optional[List[float]]:
    """The six tensor elements of a stored ``aniso_s``, or None when it cannot be read.

    MagIC 3 writes ``aniso_s`` colon-delimited (``0.2992 : 0.3468 : ...`` or
    ``a:b:c:d:e:f``); older files and hand-made tables separate the elements
    with spaces or commas, sometimes inside brackets. All are read.
    """
    if text is None or is_null(text):
        return None
    cleaned = str(text)
    for sep in (":", ",", ";", "[", "]", "(", ")"):
        cleaned = cleaned.replace(sep, " ")
    parts = cleaned.split()
    if len(parts) < 6:
        return None
    try:
        return [float(p) for p in parts[:6]]
    except ValueError:
        return None


def anisotropy_from_specimens_table(spec_df: Optional[pd.DataFrame], specimen: str,
                                    prefer: str = "AARM") -> Optional[dict]:
    """Read a stored anisotropy tensor (``aniso_s``) from the specimens table.

    A specimen with both an ATRM and an AARM row gets the ``prefer`` one,
    with the other kept in ``alternatives``, as
    :func:`anisotropy_from_measurements` does.
    """
    if spec_df is None or "aniso_s" not in spec_df.columns:
        return None
    rows = spec_df[(spec_df["specimen"].astype(str) == str(specimen)) & spec_df["aniso_s"].notna()]
    found: Dict[str, dict] = {}
    for _, row in rows.iterrows():
        s6 = parse_aniso_s(row["aniso_s"])
        if s6 is None:
            continue
        kind = str(row.get("aniso_type", "") or "").strip().upper()
        kind = kind if kind in ("ATRM", "AARM") else (kind or "ATRM")
        found.setdefault(kind, {"s": s6, "type": kind, "alteration": to_float(row.get("aniso_alt")),
                                "source": "specimens table"})
    if not found:
        return None
    order = [prefer] + [k for k in ("AARM", "ATRM") if k != prefer] + sorted(found)
    kind = next(k for k in order if k in found)
    chosen = dict(found[kind])
    others = {k: v for k, v in found.items() if k != kind}
    if others:
        chosen["alternatives"] = others
    return chosen


def _vector(rec) -> Optional[np.ndarray]:
    dec, inc = to_float(rec.get("dir_dec")), to_float(rec.get("dir_inc"))
    mom = to_float(rec.get("magn_moment"))
    if np.isnan(dec) or np.isnan(inc) or np.isnan(mom):
        return None
    return ps.dir_to_cart(dec, inc, mom)


def _position_index(phi: float, theta: float, n_pos: int = 6) -> Optional[int]:
    """Which of the standard measurement positions a field direction is."""
    for k, (d, i) in enumerate(ps.ANISOTROPY_POSITIONS.get(n_pos, [])):
        if abs(((phi - d + 180) % 360) - 180) < 1.0 and abs(theta - i) < 1.0:
            return k
    return None


def atrm_from_measurements(meas: pd.DataFrame, specimen: str,
                           thellier_steps: Optional[pd.DataFrame] = None) -> Optional[dict]:
    """Fit an ATRM tensor from the six-position LP-AN-TRM block.

    Each position is measured after a zero-field baseline, which is subtracted
    before the tensor is fitted -- without that subtraction the residual NRM
    biases the tensor and the correction factor with it. The baseline is the
    mean of the zero-field steps inside the ATRM block, falling back to the
    Thellier zero-field step at the same temperature, as the legacy Thellier
    GUI does. A ``LT-PTRM-I`` measurement in the block is the alteration
    check and gives ``aniso_alt``.
    """
    rows = meas[(meas["specimen"].astype(str) == str(specimen)) &
                meas["method_codes"].fillna("").astype(str).str.contains(CODE_ANISO_TRM, regex=False)]
    if len(rows) < 6:
        return None
    rows = rows.copy()
    if "treat_step_num" in rows.columns:
        rows["_n"] = pd.to_numeric(rows["treat_step_num"], errors="coerce")
        rows = rows.sort_values("_n", kind="stable")

    baselines, atrm_temp = [], np.nan
    for _, rec in rows.iterrows():
        field = to_float(rec.get("treat_dc_field"), 0.0)
        temp = to_float(rec.get("treat_temp"), KELVIN_OFFSET)
        if field != 0 and temp != KELVIN_OFFSET:
            atrm_temp = temp
        if field == 0 and temp != KELVIN_OFFSET:
            vec = _vector(rec)
            if vec is not None:
                baselines.append(vec)
    if not baselines and thellier_steps is not None and np.isfinite(atrm_temp):
        match = thellier_steps[(thellier_steps["kind"].isin([STEP_NRM, STEP_Z])) &
                               (thellier_steps["treat_temp"] == atrm_temp)]
        baselines = [np.array([r["x"], r["y"], r["z"]], dtype=float) for _, r in match.iterrows()]
    baseline = np.mean(baselines, axis=0) if baselines else np.zeros(3)

    vectors: Dict[int, np.ndarray] = {}
    check: Optional[Tuple[int, np.ndarray]] = None
    for _, rec in rows.iterrows():
        if to_float(rec.get("treat_dc_field"), 0.0) == 0:
            continue
        vec = _vector(rec)
        if vec is None:
            continue
        vec = vec - baseline
        phi = to_float(rec.get("treat_dc_field_phi"), 0.0)
        theta = to_float(rec.get("treat_dc_field_theta"), 0.0)
        index = _position_index(phi, theta, 6)
        if index is None:
            continue
        if set(split_codes(rec.get("method_codes", ""))) & set(CODES_PTRM_CHECK):
            check = (index, vec)
            continue
        vectors.setdefault(index, vec)
    if len(vectors) < 6:
        return None
    moments = np.array([vectors[k] for k in range(6)])
    positions = ps.ANISOTROPY_POSITIONS[6]
    try:
        s6 = ps.fit_anisotropy_tensor(moments, positions)
    except (ValueError, np.linalg.LinAlgError):
        return None
    alteration = np.nan
    if check is not None:
        index, vec = check
        alteration = ps.alteration_percent(float(np.linalg.norm(moments[index])),
                                           float(np.linalg.norm(vec)))
    s = _normalised(s6)
    sigma, nf = ps.anisotropy_residual_sigma(moments, s, positions)
    return {"s": s, "type": "ATRM", "alteration": alteration, "sigma": sigma, "nf": nf,
            "hext": ps.hext_statistics(s, sigma, nf),
            "n_positions": 6, "baseline_subtracted": bool(baselines), "source": "measurements"}


def aarm_from_measurements(meas: pd.DataFrame, specimen: str) -> Optional[dict]:
    """Fit an AARM tensor from a 6-, 9- or 15-position LP-AN-ARM block.

    Each position is a pair of measurements: an AF demagnetisation (the
    baseline) followed by the ARM acquisition. With ``treat_step_num`` the
    pairs are read by step number; without it (a MagIC download has none)
    they are read in measurement order -- each ARM with the zero-field step
    before it -- and each ARM is placed by its bias-field direction
    (``treat_dc_field_phi/theta``), falling back to the order when the
    directions are not the standard positions.
    """
    rows = meas[(meas["specimen"].astype(str) == str(specimen)) &
                meas["method_codes"].fillna("").astype(str).str.contains(CODE_ANISO_ARM, regex=False)]
    if len(rows) < 12:
        return None
    rows = rows.copy()
    step_num = (pd.to_numeric(rows["treat_step_num"], errors="coerce")
                if "treat_step_num" in rows.columns else pd.Series(np.nan, index=rows.index))
    if step_num.notna().all():
        moments = _aarm_moments_by_step_number(rows.assign(_n=step_num))
    else:
        moments = _aarm_moments_by_order(rows)
    if moments is None:
        return None
    n_pos = len(moments)
    positions = ps.ANISOTROPY_POSITIONS[n_pos]
    try:
        s6 = ps.fit_anisotropy_tensor(np.array(moments), positions)
    except (ValueError, np.linalg.LinAlgError):
        return None
    s = _normalised(s6)
    sigma, nf = ps.anisotropy_residual_sigma(np.array(moments), s, positions)
    return {"s": s, "type": "AARM", "alteration": np.nan, "sigma": sigma, "nf": nf,
            "hext": ps.hext_statistics(s, sigma, nf),
            "n_positions": n_pos, "baseline_subtracted": True, "source": "measurements"}


def _aarm_moments_by_step_number(rows: pd.DataFrame) -> Optional[List[np.ndarray]]:
    """AARM position moments (ARM minus baseline) paired by ``treat_step_num``: 1-2, 3-4, ..."""
    rows = rows.sort_values("_n", kind="stable")
    n_pos = {12: 6, 18: 9, 30: 15}.get(len(rows))
    if n_pos is None:
        return None
    moments = []
    for i in range(n_pos):
        base = rows[rows["_n"] == i * 2 + 1]
        arm = rows[rows["_n"] == i * 2 + 2]
        if len(base) == 0 or len(arm) == 0:
            return None
        b, a = _vector(base.iloc[0]), _vector(arm.iloc[0])
        if b is None or a is None:
            return None
        moments.append(a - b)
    return moments


def _aarm_moments_by_order(rows: pd.DataFrame) -> Optional[List[np.ndarray]]:
    """AARM position moments read in measurement order, each ARM less the zero-field step before it."""
    if "sequence" in rows.columns and pd.to_numeric(rows["sequence"], errors="coerce").notna().all():
        rows = rows.assign(_order=pd.to_numeric(rows["sequence"], errors="coerce")).sort_values(
            "_order", kind="stable")
    pairs, baseline = [], None
    for _, rec in rows.iterrows():
        vec = _vector(rec)
        if vec is None:
            return None
        if to_float(rec.get("treat_dc_field"), 0.0) == 0:
            baseline = vec
            continue
        if baseline is None:
            return None
        pairs.append((vec - baseline, to_float(rec.get("treat_dc_field_phi")),
                      to_float(rec.get("treat_dc_field_theta"))))
        baseline = None
    n_pos = len(pairs)
    if n_pos not in ps.ANISOTROPY_POSITIONS:
        return None
    placed = [_position_index(phi, theta, n_pos) if np.isfinite(phi) and np.isfinite(theta) else None
              for _, phi, theta in pairs]
    if None not in placed and len(set(placed)) == n_pos:
        moments: List[Optional[np.ndarray]] = [None] * n_pos
        for (moment, _, _), k in zip(pairs, placed):
            moments[k] = moment
        return moments
    return [moment for moment, _, _ in pairs]


def _normalised(s6) -> List[float]:
    """Scale the tensor so that its trace is 1 (the correction factor is a ratio,
    so the scale cancels; a unit trace just makes the elements comparable)."""
    s = np.asarray(s6, dtype=float)
    total = float(np.sum(s[:3]))
    if total:
        s = s / total
    return [float(v) for v in s]


def anisotropy_from_measurements(meas: pd.DataFrame, specimen: str,
                                 thellier_steps: Optional[pd.DataFrame] = None,
                                 prefer: str = "AARM") -> Optional[dict]:
    """The specimen's anisotropy tensor, with the alternatives kept alongside.

    When a specimen has both an ATRM and an AARM experiment the AARM tensor is
    used, as the legacy Thellier GUI does; the other is kept in
    ``alternatives`` so that the Corrections pane can offer it.
    """
    found = {}
    atrm = atrm_from_measurements(meas, specimen, thellier_steps)
    if atrm:
        found["ATRM"] = atrm
    aarm = aarm_from_measurements(meas, specimen)
    if aarm:
        found["AARM"] = aarm
    if not found:
        return None
    order = [prefer] + [k for k in ("AARM", "ATRM") if k != prefer]
    kind = next(k for k in order if k in found)
    chosen = dict(found[kind])
    chosen["alternatives"] = {k: v for k, v in found.items() if k != kind}
    return chosen


def cooling_rate_from_measurements(meas: pd.DataFrame, specimen: str,
                                   ancient_rate_k_per_myr: float) -> Optional[dict]:
    """Cooling-rate correction from the LP-CR-TRM block of one specimen.

    The laboratory cooling rate of each step is recorded in the measurement
    ``description`` as ``"<value> K/min"``, as PmagPy's converters write it.
    ``ancient_rate_k_per_myr`` is the sample's ``cooling_rate`` in K/Myr.
    """
    rows = meas[(meas["specimen"].astype(str) == str(specimen)) &
                meas["method_codes"].fillna("").astype(str).str.contains(CODE_COOLING_RATE, regex=False)]
    if len(rows) < 3 or not (ancient_rate_k_per_myr and ancient_rate_k_per_myr > 0):
        return None
    ancient = float(ancient_rate_k_per_myr) / (1e6 * 365.0 * 24.0 * 60.0)     # K/Myr -> K/min
    rates, moments, check = [], [], None
    for _, rec in rows.iterrows():
        codes = set(split_codes(rec.get("method_codes", "")))
        desc = [p.strip() for p in str(rec.get("description", "") or "").split(":")]
        rate = np.nan
        for k, token in enumerate(desc):
            if token == "K/min" and k:
                rate = to_float(desc[k - 1])
        mom = to_float(rec.get("magn_moment"))
        if np.isnan(mom):
            continue
        if "LT-T-Z" in codes:
            continue
        if np.isnan(rate):
            continue
        if "LT-T-I" in codes:
            rates.append(rate)
            moments.append(mom)
        elif set(CODES_PTRM_CHECK) & codes:
            check = (rate, mom)
    if len(rates) < 2:
        return None
    result = ps.cooling_rate_factor(rates, moments, ancient, alteration_check=check)
    result["ancient_rate"] = ancient
    result["lab_rate"] = float(max(rates))
    result["n"] = len(rates)
    return result


def nlt_from_measurements(meas: pd.DataFrame, specimen: str) -> Optional[dict]:
    """Fit the non-linear TRM coefficients from the LP-TRM acquisition block."""
    rows = meas[(meas["specimen"].astype(str) == str(specimen)) &
                meas["method_codes"].fillna("").astype(str).str.contains(CODE_TRM_ACQUISITION, regex=False)]
    if len(rows) < 2:
        return None
    fields, moments = [], []
    for _, rec in rows.iterrows():
        codes = set(split_codes(rec.get("method_codes", "")))
        if not (codes & set(CODES_I)):
            continue
        b = to_float(rec.get("treat_dc_field"))
        m = to_float(rec.get("magn_moment"))
        if np.isnan(b) or np.isnan(m) or b <= 0:
            continue
        fields.append(b)
        moments.append(m)
    if len(fields) < 2:
        return None
    a1, a2 = ps.fit_nlt_coefficients(fields, moments)
    if not np.isfinite(a1) or not np.isfinite(a2):
        return None
    # a repeat at the same field is the alteration test
    alteration = np.nan
    seen = {}
    for b, m in zip(fields, moments):
        if b in seen:
            alteration = ps.alteration_percent(seen[b], m)
        else:
            seen[b] = m
    return {"A1": float(a1), "A2": float(a2), "n": len(fields), "alteration": alteration,
            "fields": fields, "moments": moments}


# ---------------------------------------------------------------------------
# Criteria tables
# ---------------------------------------------------------------------------
#: statistics kept in microtesla here and in tesla in MagIC tables
MAGIC_UNIT_SCALE = {"B_anc": 1e-6, "sigma_B": 1e-6, "mean": 1e-6, "sd": 1e-6}


def criteria_columns() -> Dict[str, Tuple[str, str]]:
    """MagIC ``table_column`` -> (level, statistic key) for every criterion this core can test.

    Specimen statistics are ``specimens.<column>``; the group statistics a
    site criterion tests are ``sites.<column>``. ``specimens.int_mad`` is
    the legacy Thellier GUI's name for the free MAD.
    """
    out: Dict[str, Tuple[str, str]] = {}
    for key, spec in ps.CATALOG.items():
        if not spec.magic_column or key in ("Tmin", "Tmax", "mean"):
            continue
        if spec.category == "Group":
            out.setdefault("sites." + spec.magic_column, ("site", key))
        else:
            out.setdefault("specimens." + spec.magic_column, ("specimen", key))
    out.setdefault("specimens.int_mad", ("specimen", "MAD_Free"))
    out.setdefault("specimens.int_scat", ("specimen", "SCAT"))
    return out


# ---------------------------------------------------------------------------
# The session object
# ---------------------------------------------------------------------------
class PintData:
    """A MagIC 3 contribution prepared for interactive paleointensity analysis.

    Attributes:
        project: the shared :class:`pmagpy.magic_project.MagicProject`.
        specimens: ordered dict specimen name -> :class:`PintSpecimen`.
        interpretations: dict specimen -> :class:`Interpretation`.
        criteria: the active :class:`CriteriaSet`.
    """

    def __init__(self, project: mp.MagicProject):
        self.project = project
        self.specimens: Dict[str, PintSpecimen] = {}
        self.interpretations: Dict[str, Interpretation] = {}
        self.criteria: CriteriaSet = CRITERIA_SETS[DEFAULT_CRITERIA]
        self.warnings: List[str] = []
        self.anisotropy: Dict[str, dict] = {}
        self.nlt: Dict[str, dict] = {}
        self.cooling_rate: Dict[str, dict] = {}
        self._result_cache: Dict[tuple, PintResult] = {}
        #: interpretations whose bound step was flagged away, with their bounds in kelvin
        self._set_aside: Dict[str, Tuple[Interpretation, Tuple[float, float]]] = {}
        self._build()

    # ----- construction ----------------------------------------------------
    @classmethod
    def from_directory(cls, directory: str, meas_file: str = "measurements.txt",
                       offline_data_model: bool = True) -> "PintData":
        project = mp.MagicProject.from_directory(
            directory, meas_file=meas_file, offline_data_model=offline_data_model,
            tables=["measurements", "specimens", "samples", "sites", "locations", "criteria"],
            app_id=APP_ID)
        return cls(project)

    @property
    def contribution(self) -> cb.Contribution:
        return self.project.contribution

    @property
    def directory(self) -> str:
        return self.project.directory

    def _table(self, name: str) -> Optional[pd.DataFrame]:
        return self.project.table(name)

    def invalidate(self, specimen: Optional[str] = None) -> None:
        """Drop cached results (after a bound, flag or correction change)."""
        if specimen is None:
            self._result_cache.clear()
        else:
            for key in [k for k in self._result_cache if k[0] == specimen]:
                del self._result_cache[key]

    def _build(self) -> None:
        meas = self._table("measurements")
        if meas is None:
            raise ValueError("Contribution has no measurements table")
        if "method_codes" not in meas.columns or "specimen" not in meas.columns:
            raise ValueError("measurements table needs 'specimen' and 'method_codes' columns")
        intensity_col = mp.intensity_column(meas)
        if intensity_col is None:
            raise ValueError("measurements table needs one of %s" % (mp.INTENSITY_COLUMNS,))
        self.intensity_column = intensity_col
        meas = meas.copy()
        meas["specimen"] = meas["specimen"].astype(str)
        self.measurements = meas

        spec_df, samp_df = self._table("specimens"), self._table("samples")
        site_df = self._table("sites")
        self.hierarchy = mp.build_hierarchy(meas, spec_df, samp_df, site_df)
        self.site_coords = mp.build_site_coords(site_df, samp_df, self.warnings)
        self.sample_cooling_rate = self._sample_cooling_rates(samp_df)

        codes = meas["method_codes"].fillna("").astype(str)
        pi_rows = meas[codes.str.contains("|".join(PI_PROTOCOLS), regex=True)]
        microwave_only = []
        no_direction, bad_unit = [], []
        for name, spec_meas in pi_rows.groupby("specimen", sort=False):
            if _is_microwave(spec_meas):
                microwave_only.append(name)
                continue
            steps = build_step_table(spec_meas, intensity_col, self.warnings)
            if len(steps) < 3:
                continue
            spec_warnings: List[str] = []
            blab, direction = _lab_field(steps, spec_warnings, name)
            if direction is None:
                no_direction.append(name)
            if np.isfinite(blab) and blab > LAB_FIELD_MAX_TESLA:
                bad_unit.append(f"{name} ({blab:g})")
            sample, site, location = self.hierarchy.loc[name, ["sample", "site", "location"]]
            arai = build_arai(steps, spec_warnings)
            if arai is None or arai.n < 2:
                self.warnings.append(f"{name}: no usable Arai points")
                continue
            self.specimens[name] = PintSpecimen(
                name=name, sample=sample, site=site, location=location, steps=steps,
                blab=blab, blab_dir=direction,
                experiments=tuple(sorted(set(spec_meas.get("experiment", pd.Series(dtype=str)).dropna()))),
                method_codes=tuple(sorted({c for v in spec_meas["method_codes"].fillna("")
                                           for c in split_codes(v)})),
                microwave=any(c.startswith("LT-M-") or c.startswith("LT-PMRM")
                              for v in spec_meas["method_codes"].fillna("") for c in split_codes(v)),
                arai=arai, warnings=spec_warnings)
        if bad_unit:
            self.warnings.append(
                f"{len(bad_unit)} specimens record a laboratory field (treat_dc_field) that cannot be in "
                f"tesla, e.g. {', '.join(bad_unit[:3])}: MagIC records it in T (40 uT is 4e-05), so "
                f"their intensities are wrong by the unit's factor")
        if no_direction:
            self.warnings.append(
                f"{len(no_direction)} specimens do not record the laboratory field direction "
                f"(treat_dc_field_phi/theta), e.g. {', '.join(no_direction[:3])}: theta, gamma, "
                f"delta_t*, CRM% and the anisotropy correction are not computed for them")
        if microwave_only:
            self.warnings.append(
                f"{len(microwave_only)} microwave specimens were not read, e.g. "
                f"{', '.join(microwave_only[:3])}: {MICROWAVE_UNSUPPORTED}")
        if not self.specimens:
            if microwave_only:
                raise ValueError(f"This study's paleointensity experiments are microwave experiments, "
                                 f"which are not supported yet: {MICROWAVE_UNSUPPORTED}")
            raise ValueError("No specimens with Thellier-type paleointensity data found")
        # the flags as the file on disk has them: what this session's flag changes are measured from
        self._flag_base = mp.flag_baseline(self._table("measurements"))

        self._load_auxiliary(spec_df)
        self.load_criteria_from_table()

    @staticmethod
    def _sample_cooling_rates(samp_df) -> Dict[str, float]:
        out: Dict[str, float] = {}
        if samp_df is None or "cooling_rate" not in samp_df.columns:
            return out
        for _, row in samp_df.iterrows():
            value = to_float(row.get("cooling_rate"))
            if np.isfinite(value) and value > 0:
                out.setdefault(str(row.get("sample", "")), value)
        return out

    def _load_auxiliary(self, spec_df) -> None:
        """Read the anisotropy tensors, NLT coefficients and cooling-rate data."""
        # the readers filter by specimen themselves; handing each the specimen's own
        # rows (grouped once) instead of the whole table is what makes a large study open quickly
        by_specimen = {name: rows for name, rows in self.measurements.groupby("specimen", sort=False)}
        empty = self.measurements.iloc[0:0]
        for name, spec in self.specimens.items():
            own = by_specimen.get(name, empty)
            aniso = anisotropy_from_measurements(own, name, spec.steps)
            stored = anisotropy_from_specimens_table(spec_df, name)
            if aniso is None:
                aniso = stored
            elif stored is not None:
                # a stored tensor of a kind not measured here is kept as an alternative
                have = {aniso["type"], *(aniso.get("alternatives") or {})}
                for tensor in [stored, *(stored.get("alternatives") or {}).values()]:
                    if tensor["type"] not in have:
                        extra = {k: v for k, v in tensor.items() if k != "alternatives"}
                        aniso.setdefault("alternatives", {})[tensor["type"]] = extra
            if aniso is not None:
                self.anisotropy[name] = aniso
            nlt = nlt_from_measurements(own, name)
            if nlt is not None:
                self.nlt[name] = nlt
            rate = self.sample_cooling_rate.get(spec.sample)
            if rate:
                cr = cooling_rate_from_measurements(own, name, rate)
                if cr is not None:
                    self.cooling_rate[name] = cr
        # a specimen without its own cooling-rate experiment inherits its
        # sample's mean, flagged as inferred (as the legacy GUI did)
        by_sample: Dict[str, List[float]] = {}
        for name, cr in self.cooling_rate.items():
            if cr.get("flag") == "calculated" and np.isfinite(cr.get("factor", np.nan)):
                by_sample.setdefault(self.specimens[name].sample, []).append(cr["factor"])
        for name, spec in self.specimens.items():
            if name in self.cooling_rate and self.cooling_rate[name].get("flag") == "calculated":
                continue
            values = by_sample.get(spec.sample)
            if values:
                self.cooling_rate[name] = {"factor": float(np.mean(values)), "flag": "inferred",
                                           "n": len(values), "alteration": np.nan}

    # ----- convenience accessors -------------------------------------------
    @property
    def specimen_names(self) -> List[str]:
        return sorted(self.specimens, key=natural_key)

    def names_at(self, level: str) -> List[str]:
        if level == "specimen":
            return self.specimen_names
        values = {getattr(s, level) for s in self.specimens.values() if getattr(s, level)}
        return sorted(values, key=natural_key)

    def specimens_in(self, level: str, name: str) -> List[str]:
        if level == "specimen":
            return [name] if name in self.specimens else []
        return [s for s in self.specimen_names if getattr(self.specimens[s], level) == name]

    def protocol_counts(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for spec in self.specimens.values():
            key = spec.arai.protocol if spec.arai else "unknown"
            out[key] = out.get(key, 0) + 1
        return out

    # ----- measurement quality ---------------------------------------------
    def set_step_quality(self, specimen: str, sequence: int, quality: str) -> List[str]:
        """Flag one measurement good ('g') or bad ('b') and rebuild the Arai plot.

        The interpretation keeps its treatment steps, not its point numbers:
        removing a point inside or outside the fit leaves Tmin and Tmax where
        the analyst put them (see :meth:`_rebuild_arai`).

        Returns the notes the rebuild produced (which pairs were dropped and
        why, and what happened to the fit), so that the caller can show the
        consequence of the flag.
        """
        spec = self.specimens[specimen]
        idx = spec.steps.index[spec.steps["sequence"] == sequence]
        if len(idx) == 0:
            raise KeyError(f"{specimen} has no step {sequence}")
        spec.steps.loc[idx, "quality"] = quality
        notes: List[str] = []
        self._rebuild_arai(specimen, notes)
        self.invalidate(specimen)
        return notes

    def _rebuild_arai(self, specimen: str, notes: List[str]) -> None:
        """Rebuild a specimen's Arai plot from its steps, keeping the fit on the same treatments.

        A bound is an Arai point index, and removing a point (or bringing one
        back) renumbers the points after it, so the bounds are carried across
        the rebuild by their temperatures. When a bound's own step is no longer
        an Arai point -- the analyst flagged the step a fit starts or ends at --
        there is no step to put it on, and the interpretation is set aside, as
        the legacy Thellier GUI leaves a specimen uninterpreted when its stored
        bounds do not match a measured step (``read_redo_file``: "can't fit
        temperature bounds ... to the actual measurement"); a fit is never
        silently moved onto other steps. It comes back as it was when the step
        is flagged good again, unless another interpretation was made meanwhile.
        """
        spec = self.specimens[specimen]
        interp = self.interpretations.get(specimen)
        bounds = None
        if interp is not None and spec.arai is not None and spec.arai.n:
            last = spec.arai.n - 1
            bounds = (float(spec.arai.temps[min(interp.imin, last)]),
                      float(spec.arai.temps[min(interp.imax if interp.imax >= 0 else last, last)]))
        arai = build_arai(spec.steps, notes)
        spec.arai = arai
        if arai is None or arai.n < 2:
            spec.warnings = notes + ["every Arai point is now excluded"]
        else:
            spec.warnings = list(notes)
        if bounds is not None:
            where = self._indices_of(arai, bounds)
            if where is None:
                self.interpretations.pop(specimen, None)
                self._set_aside[specimen] = (interp, bounds)
                notes.append(f"the fit {bounds[0] - KELVIN_OFFSET:.0f}-{bounds[1] - KELVIN_OFFSET:.0f}°C "
                             f"starts or ends at a step that is no longer an Arai point, so it was "
                             f"set aside; flag the step good again to restore it, or choose new bounds")
            else:
                interp.imin, interp.imax = where
        elif specimen in self._set_aside and arai is not None:
            held, held_bounds = self._set_aside[specimen]
            where = self._indices_of(arai, held_bounds)
            if where is not None:
                held.imin, held.imax = where
                self.interpretations[specimen] = held
                del self._set_aside[specimen]
                notes.append(f"the fit {held_bounds[0] - KELVIN_OFFSET:.0f}-"
                             f"{held_bounds[1] - KELVIN_OFFSET:.0f}°C set aside earlier is restored")

    @staticmethod
    def _indices_of(arai: Optional[AraiData], bounds: Tuple[float, float]) -> Optional[Tuple[int, int]]:
        """The Arai point indices of two temperatures, or None when either is not a point."""
        if arai is None or arai.n < 2:
            return None
        found = []
        for temp in bounds:
            hits = np.flatnonzero(np.isclose(arai.temps, temp, rtol=0.0, atol=1e-6))
            if not len(hits):
                return None
            found.append(int(hits[0]))
        return found[0], found[1]

    def toggle_step_quality(self, specimen: str, sequence: int) -> Tuple[str, List[str]]:
        spec = self.specimens[specimen]
        row = spec.steps[spec.steps["sequence"] == sequence]
        current = str(row["quality"].iloc[0]) if len(row) else "g"
        new = "b" if current != "b" else "g"
        return new, self.set_step_quality(specimen, sequence, new)

    def step_quality(self, specimen: str) -> pd.Series:
        return self.specimens[specimen].steps.set_index("sequence")["quality"]

    # ----- interpretations --------------------------------------------------
    def set_interpretation(self, specimen: str, imin: int, imax: int, **kwargs) -> Interpretation:
        spec = self.specimens[specimen]
        last = spec.arai.n - 1
        imin, imax = sorted((int(imin), int(imax)))
        imin, imax = max(0, min(imin, last)), max(0, min(imax, last))
        interp = self.interpretations.get(specimen)
        if interp is None:
            interp = Interpretation(specimen=specimen, imin=imin, imax=imax)
            self.interpretations[specimen] = interp
        self._set_aside.pop(specimen, None)      # a new choice replaces one set aside
        interp.imin, interp.imax = imin, imax
        for key, value in kwargs.items():
            setattr(interp, key, value)
        self.invalidate(specimen)
        return interp

    def remove_interpretation(self, specimen: str) -> None:
        self.interpretations.pop(specimen, None)
        self._set_aside.pop(specimen, None)
        self.invalidate(specimen)

    def clear_interpretations(self) -> None:
        self.interpretations.clear()
        self._set_aside.clear()
        self.invalidate()

    def step_index_for_temperature(self, specimen: str, temp_k: float) -> Optional[int]:
        spec = self.specimens.get(specimen)
        if spec is None or spec.arai is None:
            return None
        diffs = np.abs(spec.arai.temps - float(temp_k))
        return int(np.argmin(diffs)) if len(diffs) else None

    # ----- statistics and results ------------------------------------------
    def statistics(self, specimen: str, imin: Optional[int] = None,
                   imax: Optional[int] = None) -> Dict[str, ps.Stat]:
        """Every SPD statistic for a specimen's current (or a trial) selection."""
        spec = self.specimens[specimen]
        if spec.arai is None:
            return {}
        if imin is None or imax is None:
            interp = self.interpretations.get(specimen)
            if interp is None:
                return {}
            imin, imax = interp.imin, interp.imax
        exp = experiment(spec, chrm=None)
        if exp is None:
            return {}
        beta = self._beta_threshold()
        return ps.all_statistics(exp, int(imin), int(imax), beta_threshold=beta)

    #: an anisotropy experiment that altered by more than this percentage does
    #: not yield a correction (the tensor is replaced by the identity, as the
    #: legacy Thellier GUI does when its ``anisotropy_alt`` criterion is set)
    anisotropy_alteration_limit: Optional[float] = 5.0
    #: require the tensor to pass Hext's F-test before correcting
    anisotropy_require_ftest: bool = False

    def _anisotropy_gate(self, aniso: dict) -> str:
        """Why this tensor must not be applied, or '' when it may be."""
        alt = aniso.get("alteration")
        limit = self.anisotropy_alteration_limit
        if limit is not None and alt is not None and np.isfinite(alt) and alt > limit:
            return (f"the {aniso['type']} experiment altered by {alt:.1f}%, above the "
                    f"{limit:g}% limit, so no correction is applied")
        if self.anisotropy_require_ftest:
            hext = aniso.get("hext") or {}
            if hext.get("passes_ftest") is False:
                return (f"the {aniso['type']} tensor fails Hext's F-test "
                        f"(F = {hext.get('F', float('nan')):.1f} < {hext.get('F_crit', float('nan')):.1f})")
        return ""

    def _beta_threshold(self) -> float:
        for crit in self.criteria.specimen:
            if crit.key == "beta" and crit.operation in ("<=", "<"):
                return float(crit.value)
        return 0.1

    def result(self, specimen: str) -> Optional[PintResult]:
        """The specimen's corrected result, cached by bounds and correction state."""
        interp = self.interpretations.get(specimen)
        spec = self.specimens.get(specimen)
        if interp is None or spec is None or spec.arai is None:
            return None
        key = (specimen, interp.imin, interp.imax, interp.use_anisotropy, interp.use_nlt,
               interp.use_cooling_rate, interp.anisotropy_type, self.criteria.name)
        if key in self._result_cache:
            return self._result_cache[key]
        result = self._build_result(spec, interp)
        self._result_cache[key] = result
        return result

    def _build_result(self, spec: PintSpecimen, interp: Interpretation) -> PintResult:
        stats = self.statistics(spec.name, interp.imin, interp.imax)
        res = PintResult(specimen=spec.name, sample=spec.sample, site=spec.site,
                         location=spec.location, imin=interp.imin, imax=interp.imax,
                         tmin=float(spec.arai.temps[interp.imin]),
                         tmax=float(spec.arai.temps[interp.imax]),
                         blab=spec.blab, stats=stats, quality=interp.quality,
                         warnings=list(spec.warnings))
        b_stat = stats.get("b")
        b = float(b_stat) if b_stat else np.nan
        uncorrected = float(stats["B_anc"]) if stats.get("B_anc") else np.nan
        res.b_anc_uncorrected = uncorrected
        value = uncorrected
        sigma = float(stats["sigma_B"]) if stats.get("sigma_B") else np.nan

        # --- anisotropy ---------------------------------------------------
        aniso = self.anisotropy.get(spec.name)
        if aniso and interp.anisotropy_type and aniso.get("type") != interp.anisotropy_type:
            other = (aniso.get("alternatives") or {}).get(interp.anisotropy_type)
            if other is not None:
                alternatives = {k: v for k, v in (aniso.get("alternatives") or {}).items()
                                if k != interp.anisotropy_type}
                alternatives[aniso["type"]] = {k: v for k, v in aniso.items() if k != "alternatives"}
                aniso = dict(other, alternatives=alternatives)
            else:
                res.warnings.append(f"no {interp.anisotropy_type} tensor for this specimen; "
                                    f"the {aniso.get('type')} tensor is used")
        c_factor = np.nan
        if aniso and interp.use_anisotropy is not False:
            gate = self._anisotropy_gate(aniso)
            free = stats.get("Dec_Free"), stats.get("Inc_Free")
            if gate and interp.use_anisotropy is True:
                # switched on for this specimen (or so recorded in the stored
                # result): the policy is overridden, and the note says so
                res.warnings.append(f"anisotropy applied as switched on, although {gate.split(', so')[0]}")
                gate = ""
            if gate:
                res.corrections["anisotropy"] = Correction(
                    "anisotropy", np.nan, False, "", aniso.get("source", ""),
                    {"type": aniso["type"], "alteration": aniso.get("alteration")}, gate)
            elif spec.blab_dir is None:
                res.corrections["anisotropy"] = Correction(
                    "anisotropy", np.nan, False, "", aniso.get("source", ""), {},
                    "the laboratory field direction is not recorded, so the correction "
                    "cannot be computed")
            elif free[0] and free[1]:
                chrm = ps.dir_to_cart(float(free[0]), float(free[1]), 1.0)
                try:
                    out = ps.anisotropy_correction_factor(aniso["s"], chrm, spec.blab_dir)
                    c_factor = out["c"]
                    code = CORRECTION_CODES["anisotropy_arm" if aniso["type"] == "AARM"
                                            else "anisotropy_trm"]
                    res.corrections["anisotropy"] = Correction(
                        "anisotropy", c_factor, True, code, aniso.get("source", ""),
                        {"type": aniso["type"], "tau": list(map(float, out["tau"])),
                         "degree": out["degree"], "alteration": aniso.get("alteration")},
                        f"{aniso['type']} tensor from the {aniso.get('source', 'study')}")
                except (ValueError, np.linalg.LinAlgError) as exc:
                    res.corrections["anisotropy"] = Correction(
                        "anisotropy", np.nan, False, "", aniso.get("source", ""), {},
                        f"the anisotropy tensor could not be inverted ({exc})")
            else:
                res.corrections["anisotropy"] = Correction(
                    "anisotropy", np.nan, False, "", "", {},
                    "no free-floating direction, so the ancient field direction is unknown")
        elif aniso:
            res.corrections["anisotropy"] = Correction(
                "anisotropy", np.nan, False, "", aniso.get("source", ""), {},
                "switched off for this specimen")

        # --- non-linear TRM -----------------------------------------------
        nlt = self.nlt.get(spec.name)
        applied_c = c_factor if np.isfinite(c_factor) else 1.0
        if nlt and interp.use_nlt is not False and np.isfinite(b) and np.isfinite(spec.blab):
            corrected = ps.nlt_correction(b, spec.blab, nlt["A2"], applied_c)
            if np.isfinite(corrected):
                value = corrected * 1e6
                res.corrections["nlt"] = Correction(
                    "nlt", value / uncorrected if uncorrected else np.nan, True,
                    CORRECTION_CODES["nlt"], "measurements",
                    {"A1": nlt["A1"], "A2": nlt["A2"], "alteration": nlt.get("alteration")},
                    "hyperbolic tangent TRM acquisition fit")
            else:
                res.corrections["nlt"] = Correction(
                    "nlt", np.nan, False, "", "measurements", {},
                    "the corrected slope leaves the domain of the tanh model")
                if np.isfinite(c_factor):
                    value = uncorrected * c_factor
        elif np.isfinite(c_factor):
            value = uncorrected * c_factor
            if nlt:
                res.corrections["nlt"] = Correction("nlt", np.nan, False, "", "measurements", {},
                                                    "switched off for this specimen")
        elif nlt:
            res.corrections["nlt"] = Correction("nlt", np.nan, False, "", "measurements", {},
                                                "switched off for this specimen")

        # --- cooling rate ---------------------------------------------------
        cr = self.cooling_rate.get(spec.name)
        if cr and interp.use_cooling_rate is not False:
            factor = cr.get("factor", np.nan)
            if np.isfinite(factor):
                value = value * factor
                res.corrections["cooling_rate"] = Correction(
                    "cooling_rate", float(factor), True, CORRECTION_CODES["cooling_rate"],
                    cr.get("flag", ""), {k: cr.get(k) for k in ("alteration", "n", "ancient_rate",
                                                                "lab_rate", "slope")},
                    f"cooling-rate correction ({cr.get('flag', 'calculated')})")
            else:
                res.corrections["cooling_rate"] = Correction(
                    "cooling_rate", np.nan, False, "", cr.get("flag", ""), {},
                    "the cooling-rate experiment altered by more than 5%"
                    if cr.get("flag") == "altered" else "no usable cooling-rate experiment")
        elif cr:
            res.corrections["cooling_rate"] = Correction(
                "cooling_rate", np.nan, False, "", cr.get("flag", ""), {},
                "switched off for this specimen")

        res.b_anc = value
        # the relative error is a property of the fit, so it scales with the
        # corrections that scale the estimate
        res.sigma = sigma * (value / uncorrected) if (np.isfinite(sigma) and uncorrected) else sigma

        # --- criteria --------------------------------------------------------
        verdict = self.criteria.evaluate(stats, "specimen")
        res.passed = verdict["passed"]
        res.failures = verdict["failures"]
        if verdict["not_applicable"]:
            res.warnings.extend(f"not tested: {t}" for t in verdict["not_applicable"])
        return res

    def results(self, only_accepted: bool = False) -> List[PintResult]:
        out = []
        for name in self.specimen_names:
            res = self.result(name)
            if res is None:
                continue
            if only_accepted and not self.is_accepted(res):
                continue
            out.append(res)
        return out

    @staticmethod
    def is_accepted(res: PintResult) -> bool:
        return res.quality != "b" and res.passed is not False

    # ----- auto interpretation ---------------------------------------------
    def auto_interpret(self, specimen: str, min_n: int = 4,
                       objective: str = "criteria") -> Optional[Interpretation]:
        """Choose the best segment for one specimen against the active criteria.

        Every segment of at least ``min_n`` points is scored: those that pass
        the criteria are preferred, and among them the one with the largest
        ``FRAC x n`` (the most of the NRM over the most steps) wins. When
        nothing passes, the segment with the fewest failures and the best
        quality factor is offered, and its failures are reported so that the
        analyst can see why.
        """
        spec = self.specimens.get(specimen)
        if spec is None or spec.arai is None or spec.arai.n < min_n:
            return None
        exp = experiment(spec)
        beta = self._beta_threshold()
        best = None
        for start in range(spec.arai.n - min_n + 1):
            for end in range(start + min_n - 1, spec.arai.n):
                stats = ps.all_statistics(exp, start, end, beta_threshold=beta)
                verdict = self.criteria.evaluate(stats, "specimen")
                frac = float(stats["FRAC"]) if stats.get("FRAC") else 0.0
                n = end - start + 1
                q = float(stats["q"]) if stats.get("q") else 0.0
                score = (1 if verdict["passed"] else 0, -len(verdict["failures"]),
                         frac * n if objective == "criteria" else q)
                if best is None or score > best[0]:
                    best = (score, start, end, verdict)
        if best is None:
            return None
        _, start, end, verdict = best
        interp = self.set_interpretation(specimen, start, end)
        interp.notes = ("auto-interpreted; passes " + self.criteria.name) if verdict["passed"] else \
            ("auto-interpreted; best available, fails: " + "; ".join(verdict["failures"]))
        return interp

    def auto_interpret_all(self, min_n: int = 4, specimens: Optional[Iterable[str]] = None,
                           progress=None) -> Dict[str, Optional[Interpretation]]:
        names = list(specimens) if specimens is not None else self.specimen_names
        out = {}
        for k, name in enumerate(names):
            out[name] = self.auto_interpret(name, min_n=min_n)
            if progress is not None:
                progress((k + 1) / len(names), name)
        return out

    def copy_bounds(self, source: str, targets: Iterable[str]) -> Tuple[int, List[str]]:
        """Copy a specimen's *temperature* bounds to others where they exist.

        Bounds are indices, so copying them between specimens is only
        meaningful through the treatments they stand for; a target that does
        not have both treatments is skipped and reported.
        """
        interp = self.interpretations.get(source)
        spec = self.specimens.get(source)
        if interp is None or spec is None or spec.arai is None:
            return 0, ["the source specimen has no interpretation"]
        tmin, tmax = spec.arai.temps[interp.imin], spec.arai.temps[interp.imax]
        copied, skipped = 0, []
        for name in targets:
            if name == source:
                continue
            target = self.specimens.get(name)
            if target is None or target.arai is None:
                continue
            temps = target.arai.temps
            if not (np.any(np.isclose(temps, tmin)) and np.any(np.isclose(temps, tmax))):
                skipped.append(f"{name}: no step at {tmin - KELVIN_OFFSET:.0f}°C "
                               f"and {tmax - KELVIN_OFFSET:.0f}°C")
                continue
            imin = int(np.argmin(np.abs(temps - tmin)))
            imax = int(np.argmin(np.abs(temps - tmax)))
            self.set_interpretation(name, imin, imax)
            copied += 1
        return copied, skipped

    # ----- criteria ---------------------------------------------------------
    def set_criteria(self, name_or_set) -> CriteriaSet:
        self.criteria = CRITERIA_SETS[name_or_set] if isinstance(name_or_set, str) else name_or_set
        self.invalidate()
        return self.criteria

    def load_criteria_from_table(self) -> Optional[CriteriaSet]:
        """Read the study's own ``criteria.txt`` as the 'This study' preset.

        Specimen criteria (``specimens.*``) and site criteria (``sites.*``:
        N specimens, N samples, the scatter in T and in percent) are read; a
        value of -999, the legacy Thellier GUI's "not set", is passed over.
        Values in tesla are converted to the microtesla the statistics are in.
        """
        table = self._table("criteria")
        if table is None or "table_column" not in table.columns:
            return None
        column_to_key = criteria_columns()
        specimen, site = [], []
        for _, row in table.iterrows():
            column = str(row.get("table_column", "")).strip()
            level_key = column_to_key.get(column)
            if level_key is None:
                continue
            level, key = level_key
            op = str(row.get("criterion_operation", "")).strip() or "<="
            raw = str(row.get("criterion_value", "")).strip()
            value: float | bool
            if raw.lower() in ("true", "false", "t", "f"):
                value = raw.lower() in ("true", "t")
                op = "="
            else:
                try:
                    value = float(raw)
                except ValueError:
                    continue
                if value == -999:
                    continue
                value = value / MAGIC_UNIT_SCALE.get(key, 1.0)
            (site if level == "site" else specimen).append(Criterion(key, op, value))
        if not specimen and not site:
            return None
        # a table that is a preset (the one an earlier export wrote, say) keeps the preset's name,
        # so the descriptions and the criteria selector still say CCRIT rather than "This study"
        def signature(criteria):
            return {(c.key, c.operation, c.value if isinstance(c.value, bool) else round(float(c.value), 6))
                    for c in criteria}
        for name, preset in CRITERIA_SETS.items():
            if name != "This study" and signature(preset.specimen) == signature(specimen) \
                    and signature(preset.site) == signature(site):
                self.criteria = preset
                return preset
        citation = str(table.get("citations", pd.Series(["This study"])).iloc[0])
        cs = CriteriaSet("This study", citation, "", "The criteria table of the loaded contribution.",
                         tuple(specimen), tuple(site))
        CRITERIA_SETS[cs.name] = cs
        self.criteria = cs
        return cs

    def criteria_table(self) -> pd.DataFrame:
        """The active criteria as MagIC 3 criteria rows (IE-SPEC and IE-SITE)."""
        rows = []
        for level, crits in (("specimens", self.criteria.specimen), ("sites", self.criteria.site)):
            for crit in crits:
                spec = ps.describe(crit.key)
                if not spec.magic_column:
                    continue
                if isinstance(crit.value, bool):
                    value = "True" if crit.value else "False"
                else:
                    value = f"{crit.value * MAGIC_UNIT_SCALE.get(crit.key, 1.0):g}"
                rows.append({"criterion": "IE-SPEC" if level == "specimens" else "IE-SITE",
                             "table_column": f"{level}.{spec.magic_column}",
                             "criterion_operation": crit.operation,
                             "criterion_value": value,
                             "description": f"{self.criteria.name}: {spec.definition}"
                                            + (" Tested on the magnitude." if crit.key in MAGNITUDE_CRITERIA
                                               else ""),
                             "citations": self.criteria.citation or "This study"})
        return pd.DataFrame(rows)

    def merged_criteria_table(self) -> pd.DataFrame:
        """The contribution's criteria with this application's rows replaced and every other kept.

        The rows this application owns are the ones it can read back: a
        specimen or site paleointensity statistic (:func:`criteria_columns`).
        Directional (DE-), sample (IE-SAMP), pole and every other criterion
        stays exactly as it was.
        """
        new = self.criteria_table()
        existing = self._table("criteria")
        if existing is None or len(existing) == 0 or "table_column" not in existing.columns:
            return new
        owned = set(criteria_columns())
        mine = existing["table_column"].astype(str).str.strip().isin(owned)
        kept = existing[~mine]
        if len(new) == 0:
            return kept.reset_index(drop=True)
        return pd.concat([kept, new], ignore_index=True, sort=False)

    # ----- group results ----------------------------------------------------
    def group_results(self, level: str = "site", only_accepted: bool = True,
                      weighted: bool = False, corrected_only: bool = False,
                      include_rejected: bool = False) -> pd.DataFrame:
        """Sample, site or location means of the accepted specimen results.

        With ``include_rejected`` a group none of whose interpreted specimens
        is accepted is still listed, as the mean of those the analyst did not
        reject ('b') -- or of all of them when every one was rejected -- with
        ``passed`` False and ``n_accepted`` 0, so that it can be written with
        result_quality 'b' rather than left out.
        """
        rows = []
        site_inc = self._site_inclinations() if level == "site" else {}
        for name in self.names_at(level):
            members, interpreted = [], []
            for spec_name in self.specimens_in(level, name):
                res = self.result(spec_name)
                if res is None or not np.isfinite(res.b_anc):
                    continue
                if corrected_only and not res.corrected:
                    continue
                interpreted.append(res)
                if only_accepted and not self.is_accepted(res):
                    continue
                members.append(res)
            rejected = False
            if not members:
                if not (include_rejected and interpreted):
                    continue
                rejected = True
                members = [r for r in interpreted if r.quality != "b"] or interpreted
            values = [m.b_anc for m in members]
            weights = [1.0 / (m.sigma ** 2) if np.isfinite(m.sigma) and m.sigma > 0 else np.nan
                       for m in members] if weighted else None
            if weights is not None and not all(np.isfinite(w) for w in weights):
                weights = None
            stats = ps.group_statistics(values, weights)
            n_samples = len({m.sample for m in members if m.sample})
            row = {level: name, "n": len(members), "n_samples": n_samples,
                   "n_accepted": 0 if rejected else len(members),
                   "specimens": ":".join(m.specimen for m in members),
                   "samples": ":".join(sorted({m.sample for m in members if m.sample}, key=natural_key)),
                   "int_abs": float(stats["mean"]) if stats["mean"] else np.nan,
                   "int_abs_sigma": float(stats["sd"]) if stats["sd"] else np.nan,
                   "int_abs_sigma_perc": float(stats["dB_percent"]) if stats["dB_percent"] else np.nan,
                   "dBN_percent": float(stats["dBN_percent"]) if stats.get("dBN_percent") else np.nan,
                   "corrected": sum(1 for m in members if m.corrected),
                   }
            if weights is not None and stats.get("weighted_mean"):
                row["int_abs_weighted"] = float(stats["weighted_mean"])
                row["int_abs_weighted_sigma"] = float(stats["weighted_sd"]) \
                    if stats.get("weighted_sd") else np.nan
            verdict = self.criteria.evaluate(
                {"N": ps.ok("N", len(members)), "N_samples": ps.ok("N_samples", n_samples),
                 "sd": stats["sd"], "dB_percent": stats["dB_percent"]}, "site")
            if rejected:
                row["passed"] = False
                row["failures"] = "; ".join(
                    [f"no specimen is accepted under {self.criteria.name}"] + verdict["failures"])
            else:
                row["passed"] = verdict["passed"]
                row["failures"] = "; ".join(verdict["failures"])
            if level in ("site", "sample"):
                coords = self.site_coords.get(name if level == "site" else "")
                if coords and np.isfinite(row["int_abs"]):
                    row["lat"], row["lon"] = coords
                    row["vadm"] = vadm(row["int_abs"], coords[0])
                    # the dipole moment is linear in B, so its uncertainty is the
                    # moment of the scatter (the legacy GUI's (VADM+ - VADM-)/2)
                    row["vadm_sigma"] = vadm(row["int_abs_sigma"], coords[0])
            inc = site_inc.get(name)
            if inc is not None and np.isfinite(row["int_abs"]):
                row["vdm_inc"] = inc
                row["vdm"] = vdm(row["int_abs"], inc)
                row["vdm_sigma"] = vdm(row["int_abs_sigma"], inc)
            rows.append(row)
        return pd.DataFrame(rows)

    def _site_inclinations(self) -> Dict[str, float]:
        """site -> the inclination of its directional mean in the sites table, for a VDM.

        The tilt-corrected mean is preferred, then the geographic one; a site
        with neither (or only a specimen-coordinate one) has no VDM, since the
        paleointensity specimens themselves are rarely oriented.
        """
        df = self._table("sites")
        if df is None or not {"site", "dir_inc"} <= set(df.columns):
            return {}
        inc = pd.to_numeric(df["dir_inc"], errors="coerce")
        tilt = (pd.to_numeric(df["dir_tilt_correction"], errors="coerce")
                if "dir_tilt_correction" in df.columns else pd.Series(np.nan, index=df.index))
        out: Dict[str, float] = {}
        for coord in (COORD_TILT, COORD_GEOGRAPHIC):
            for site, value in zip(df["site"].astype(str)[(tilt == coord) & inc.notna()],
                                   inc[(tilt == coord) & inc.notna()]):
                out.setdefault(site, float(value))
        return out

    # ----- export -----------------------------------------------------------
    def specimens_table(self, analysts: Optional[str] = None,
                        only_accepted: bool = False) -> pd.DataFrame:
        """MagIC 3 specimens rows for every interpretation."""
        rows = []
        for res in self.results(only_accepted=only_accepted):
            spec = self.specimens[res.specimen]
            row = {"specimen": res.specimen, "sample": res.sample,
                   "experiments": ":".join(spec.experiments),
                   "meas_step_min": res.tmin, "meas_step_max": res.tmax,
                   "meas_step_unit": "K",
                   "int_abs": res.b_anc * 1e-6 if np.isfinite(res.b_anc) else None,
                   "int_abs_sigma": res.sigma * 1e-6 if np.isfinite(res.sigma) else None,
                   "int_treat_dc_field": spec.blab,
                   "int_corr": "c" if res.corrected else "u",
                   "result_quality": res.quality,
                   "dir_tilt_correction": COORD_SPECIMEN,
                   }
            for key, stat in res.stats.items():
                column = ps.describe(key).magic_column
                if not column or column in ("int_abs", "int_abs_sigma", "meas_step_min",
                                            "meas_step_max", "int_n_specimens"):
                    continue
                if not stat:
                    continue
                if column == "int_scat":
                    row[column] = "t" if stat.value else "f"
                else:
                    row[column] = float(stat.value)
            for name, corr in res.corrections.items():
                if not corr.applied:
                    continue
                if name == "anisotropy":
                    row["int_corr_aniso"] = corr.factor
                elif name == "cooling_rate":
                    row["int_corr_cooling_rate"] = corr.factor
                elif name == "nlt":
                    row["int_corr_nlt"] = corr.factor
            codes = set(spec.method_codes) | {"IE-TT"} | set(res.correction_codes)
            codes = {c for c in codes if c.startswith(("LP-", "LT-", "DA-", "IE-", "AE-"))}
            codes -= set(CODES_Z) | set(CODES_I) | set(CODES_NRM) | set(CODES_PTRM_CHECK) \
                | set(CODES_TAIL_CHECK) | set(CODES_ADDITIVITY)
            row["method_codes"] = join_codes(codes)
            row["description"] = res.stats.get("n") and \
                f"paleointensity from {int(float(res.stats['n']))} Arai points" or ""
            rows.append(row)
        df = pd.DataFrame(rows)
        if len(df) == 0:
            return df
        df = self.project.stamp(df, analysts)
        existing = self._table("specimens")
        df = carry_metadata(df, existing, "specimen")
        return df

    def merged_specimens_table(self, analysts: Optional[str] = None,
                               only_accepted: bool = False) -> pd.DataFrame:
        """The specimens table merged into the contribution's own under the export policy."""
        new = self.specimens_table(analysts, only_accepted)
        existing = self._table("specimens")
        owned = set(self.specimens)

        def owns(df):
            # this application owns the *intensity* rows of the specimens it has
            # measurements for; directional rows and rock-magnetic rows are inherited
            return mp.intensity_rows(df)
        merged = mp.merge_results(existing, new, "specimen", owned, owns=owns)
        merged = self._keep_the_hierarchy_whole(merged)
        warnings: List[str] = []
        merged = trim_to_model(merged, "specimens", warnings)
        self.warnings.extend(warnings)
        return merged

    def _keep_the_hierarchy_whole(self, specimens: pd.DataFrame) -> pd.DataFrame:
        """Give every measured specimen a row, even without an interpretation.

        A measurements table whose specimens are not all in the specimens table
        is an invalid contribution -- the MagIC validator's cross-table check
        fails on every measurement row -- so a specimen with no interpretation
        keeps a minimal row carrying only its place in the hierarchy.
        """
        present = set(specimens["specimen"].astype(str)) if len(specimens) else set()
        missing = [name for name in self.specimens if name not in present]
        if not missing:
            return specimens
        stubs = pd.DataFrame([{"specimen": name, "sample": self.specimens[name].sample,
                               "citations": "This study"} for name in missing])
        stubs = carry_metadata(stubs, self._table("specimens"), "specimen")
        return pd.concat([specimens, stubs], ignore_index=True, sort=False)

    def sites_table(self, analysts: Optional[str] = None, level: str = "site",
                    weighted: bool = False) -> pd.DataFrame:
        """MagIC 3 sites (or samples) rows with the group means.

        Every group with an interpreted specimen gets a row, as PmagPy
        Directions writes a mean that fails its criteria: a mean that fails
        the site criteria, or that has no accepted specimen (then the mean of
        the interpreted ones), is written with ``result_quality`` 'b' and
        says why in its description, rather than being left out -- leaving
        it out deleted the published mean from the table.
        """
        groups = self.group_results(level=level, only_accepted=True, weighted=weighted,
                                    include_rejected=True)
        if len(groups) == 0:
            return pd.DataFrame()
        rows = []
        for _, g in groups.iterrows():
            note = ("weighted mean; " if weighted else "") + \
                f"{int(g['corrected'])} of {int(g['n'])} specimens corrected"
            if int(g["n_accepted"]) == 0:
                note = (f"no specimen is accepted under {self.criteria.name}: the mean of the "
                        f"{int(g['n'])} interpreted specimens, not accepted; ") + note
            elif g["passed"] is False and g["failures"]:
                note = f"fails {self.criteria.name}: {g['failures']}; " + note
            # the data model caps int_abs_sigma_perc at 100; a group whose
            # scatter exceeds its mean cannot be expressed in that column, so
            # the percentage is left out and the absolute sigma -- which is not
            # capped, and carries the same information -- says it instead
            perc = g["int_abs_sigma_perc"]
            if np.isfinite(perc) and perc > 100:
                note += f"; scatter is {perc:.0f} % of the mean"
                perc = None
            row = {level: g[level],
                   "int_abs": g["int_abs"] * 1e-6 if np.isfinite(g["int_abs"]) else None,
                   "int_abs_sigma": g["int_abs_sigma"] * 1e-6 if np.isfinite(g["int_abs_sigma"]) else None,
                   "int_abs_sigma_perc": perc,
                   "int_n_specimens": int(g["n"]),
                   # the members of this mean (a replaced row's lists are not carried)
                   "specimens": g["specimens"],
                   "method_codes": "IE-SPEC:LP-PI-TRM",
                   "result_quality": "g" if g["passed"] is not False else "b",
                   "result_type": "a",          # an average of the specimens below it
                   "description": note,
                   }
            if level == "site":
                row["samples"] = g["samples"]
                row["int_n_samples"] = int(g["n_samples"])
                if np.isfinite(g.get("vadm", np.nan)):
                    row["vadm"] = g["vadm"]
                    row["vadm_n_samples"] = int(g["n_samples"])
                    if np.isfinite(g.get("vadm_sigma", np.nan)):
                        row["vadm_sigma"] = g["vadm_sigma"]
                    row["method_codes"] += ":IE-VADM"
                if np.isfinite(g.get("vdm", np.nan)):
                    row["vdm"] = g["vdm"]
                    row["vdm_n_samples"] = int(g["n_samples"])
                    if np.isfinite(g.get("vdm_sigma", np.nan)):
                        row["vdm_sigma"] = g["vdm_sigma"]
                row["location"] = next((s.location for s in self.specimens.values()
                                        if s.site == g[level]), "")
            rows.append(row)
        df = pd.DataFrame(rows)
        df = self.project.stamp(df, analysts)
        existing = self._table(level + "s")
        df = carry_metadata(df, existing, level)
        if existing is not None and level in existing.columns:
            # what a replaced intensity mean said about itself that is not recomputed here
            df = mp.carry_annotations(df, existing[mp.intensity_rows(existing)], level,
                                      columns=("external_database_ids",))
        return df

    def merged_group_table(self, level: str = "site", analysts: Optional[str] = None,
                           weighted: bool = False) -> pd.DataFrame:
        """The sites (or samples) table with this study's intensity means merged in.

        The groups this application owns are those with at least one
        interpreted specimen -- each gets a row (:meth:`sites_table`). A
        published mean of a group none of whose specimens is interpreted here
        is kept as it was: nothing was recomputed for it.
        """
        new = self.sites_table(analysts, level=level, weighted=weighted)
        existing = self._table(level + "s")
        owned = {getattr(self.specimens[name], level) for name in self.interpretations
                 if name in self.specimens and getattr(self.specimens[name], level)}
        merged = mp.merge_results(existing, new, level, owned, owns=mp.intensity_rows)
        return trim_to_model(merged, level + "s", self.warnings)

    def measurements_table(self) -> pd.DataFrame:
        """The measurements table with the current good/bad flags written back."""
        table = self.contribution.tables.get("measurements")
        if table is None:
            return pd.DataFrame()
        df = table.df.copy()
        if "quality" not in df.columns:
            df["quality"] = "g"
        col = df.columns.get_loc("quality")
        for spec in self.specimens.values():
            # meas_pos is the row's position in the table as it was read
            df.iloc[spec.steps["meas_pos"].values, col] = spec.steps["quality"].values
        return df

    def write_specimens(self, dir_path: str, analysts: Optional[str] = None,
                        only_accepted: bool = False, custom_name: Optional[str] = None) -> Optional[str]:
        df = self.merged_specimens_table(analysts, only_accepted)
        return self.project.write_table(df, "specimens", dir_path, custom_name)

    def write_group(self, dir_path: str, level: str = "site", analysts: Optional[str] = None,
                    weighted: bool = False) -> Optional[str]:
        df = self.merged_group_table(level, analysts, weighted)
        return self.project.write_table(df, level + "s", dir_path)

    def write_measurements(self, dir_path: str, custom_name: str = "measurements.txt",
                           source: Optional[str] = None) -> Optional[str]:
        """Write the measurements table with the current good/bad flags, changing nothing else.

        Only the flags changed in this session are changed, in the file as it
        is (``source``, default the study's own; see
        :func:`pmagpy.magic_project.write_measurement_flags`), so the rest is
        written byte for byte and flags another application wrote are kept.
        """
        table = self.contribution.tables.get("measurements")
        if table is None:
            return None
        target = os.path.join(dir_path, os.path.basename(custom_name))
        source = source or os.path.join(self.contribution.directory,
                                        self.contribution.filenames.get("measurements", "measurements.txt"))
        changes = mp.flag_changes(self._flag_base, (spec.steps for spec in self.specimens.values()))
        names = table.df["measurement"].tolist() if "measurement" in table.df.columns else None
        if os.path.isfile(source):
            written = mp.write_measurement_flags(source, target, changes, names)
            if written:
                return written
            self.warnings.append(f"{os.path.basename(source)} no longer has the rows it had when the study was "
                                 "opened; the measurements table was written in full")
        return mp.magic_write(target, self.measurements_table(), "measurements")

    def flags_written(self) -> None:
        """The study's own measurements.txt now has this session's flags (after an export into it)."""
        mp.mark_flags_written(self._flag_base, (spec.steps for spec in self.specimens.values()))

    def step_flag_changes(self) -> List[dict]:
        """The steps whose flag differs from the file on disk, each identified as in :meth:`_step_keys`."""
        changes = []
        for spec in self.specimens.values():
            positions = spec.steps["meas_pos"].to_numpy()
            now = np.where(spec.steps["quality"].to_numpy(dtype=object) == "b", "b", "g")
            for (name, measurement, occurrence), pos, q in zip(self._step_keys(spec), positions, now):
                if q != self._flag_base[pos]:
                    changes.append({"specimen": name, "measurement": measurement, "occurrence": occurrence,
                                    "meas_pos": int(pos), "quality": str(q)})
        return changes

    def write_criteria(self, dir_path: str) -> Optional[str]:
        # not trimmed to the data model: the rows kept are written as they were read
        return self.project.write_table(self.merged_criteria_table(), "criteria", dir_path)

    def validate_output(self, dir_path: str) -> dict:
        return validate_directory(dir_path)

    # ----- session persistence ---------------------------------------------
    @staticmethod
    def _step_keys(spec: PintSpecimen) -> List[tuple]:
        """What identifies each of a specimen's steps across sessions, in step order.

        The measurement name is not enough: many MagIC tables repeat names
        (every specimen's first step called ``1``, or one name for a whole
        experiment), and a flag kept by name alone lands on every step that
        shares it. The key is the specimen, the name and which occurrence of
        that name among the specimen's steps it is.
        """
        seen: Dict[str, int] = {}
        keys = []
        for m in spec.steps["measurement"].astype(str):
            k = seen.get(m, 0)
            seen[m] = k + 1
            keys.append((spec.name, m, k))
        return keys

    def to_json(self) -> str:
        """The interpretations, flags, criteria and anisotropy policy as a human-readable session."""
        bad_steps = []
        for spec in self.specimens.values():
            bad = (spec.steps["quality"] == "b").to_numpy()
            for (name, measurement, occurrence), pos, is_bad in zip(self._step_keys(spec),
                                                                    spec.steps["meas_pos"], bad):
                if is_bad:
                    bad_steps.append({"specimen": name, "measurement": measurement,
                                      "occurrence": occurrence, "meas_pos": int(pos)})
        payload = {
            "format": "pmagpy_intensity_session",
            "version": 3,
            "software": SOFTWARE_TAG,
            "directory": self.directory,
            "criteria": self.criteria.name,
            # the whole set, so that a variant (a preset with Ziggie added, a study's
            # own table) is restored as it was used rather than by its name
            "criteria_set": {"name": self.criteria.name, "citation": self.criteria.citation,
                             "doi": self.criteria.doi, "description": self.criteria.description,
                             "specimen": [[c.key, c.operation, c.value] for c in self.criteria.specimen],
                             "site": [[c.key, c.operation, c.value] for c in self.criteria.site]},
            "anisotropy_policy": {"alteration_limit": self.anisotropy_alteration_limit,
                                  "require_ftest": bool(self.anisotropy_require_ftest)},
            "interpretations": [asdict(i) for i in self.interpretations.values()],
            # version 3: the flags that differ from the measurements table on disk, and only
            # those, so that a flag another application set there is not undone on reopening
            "step_flag_changes": self.step_flag_changes(),
            # the whole state, for earlier readers (version 2: one row each; version 1: names)
            "bad_steps": bad_steps,
            "bad_measurements": sorted({b["measurement"] for b in bad_steps}),
            "bounds_in_kelvin": {
                name: [float(self.specimens[name].arai.temps[i.imin]),
                       float(self.specimens[name].arai.temps[i.imax])]
                for name, i in self.interpretations.items() if self.specimens.get(name)},
            # fits whose end step is flagged bad, kept to come back when it is flagged good
            "set_aside": [{"interpretation": asdict(i), "bounds_in_kelvin": list(bounds)}
                          for i, bounds in self._set_aside.values()],
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    def from_json(self, text: str) -> int:
        """Restore a session written by :meth:`to_json`.

        A file that is not a session, or whose interpretations are all of
        specimens this study does not have, raises ``ValueError`` before
        anything changes. A version 3 session records the flags that differ
        from the measurements table on disk, and those alone are applied, onto
        the flags the file has now: a step flagged good again stays good, and a
        flag PmagPy Directions set in the file since is not undone. Earlier
        sessions hold the whole flag state (version 2 by step, version 1 by
        measurement name only; when a flagged name belongs to more than one
        step that is said in ``warnings``).
        """
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"not a PmagPy Intensity session ({exc})") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("interpretations", []), list):
            raise ValueError("not a PmagPy Intensity session")
        items = payload.get("interpretations", [])
        if items and not any(self.specimens.get(i.get("specimen")) is not None for i in items
                             if isinstance(i, dict)):
            raise ValueError("the session holds no interpretations of specimens in this study")
        criteria = self._criteria_from_json(payload)
        if "step_flag_changes" in payload:
            # version 3: apply the session's changes onto the flags the file has now
            flagged = {}
            wanted = {(str(c.get("specimen")), str(c.get("measurement")), int(c.get("occurrence", 0))):
                      c.get("quality") for c in (payload.get("step_flag_changes") or []) if isinstance(c, dict)
                      and c.get("quality") in ("g", "b")}
            if wanted:
                for spec in self.specimens.values():
                    quality = spec.steps["quality"].to_numpy(dtype=object).copy()
                    for k, key in enumerate(self._step_keys(spec)):
                        if key in wanted:
                            quality[k] = wanted[key]
                    flagged[spec.name] = quality
        elif "bad_steps" in payload:
            bad_keys = {(str(b.get("specimen")), str(b.get("measurement")), int(b.get("occurrence", 0)))
                        for b in (payload.get("bad_steps") or []) if isinstance(b, dict)}
            flagged = {spec.name: np.array(["b" if k in bad_keys else "g" for k in self._step_keys(spec)],
                                           dtype=object)
                       for spec in self.specimens.values()}
        elif "bad_measurements" in payload:
            bad = {str(m) for m in (payload.get("bad_measurements") or [])}
            flagged = {}
            for spec in self.specimens.values():
                names = spec.steps["measurement"].astype(str)
                flagged[spec.name] = np.where(names.isin(bad), "b", "g").astype(object)
            counts = pd.Series([m for spec in self.specimens.values()
                                for m in spec.steps["measurement"].astype(str)]).value_counts()
            repeated = [m for m in bad if counts.get(m, 0) > 1]
            if repeated:
                self.warnings.append(
                    f"the session names its bad steps by measurement name only, and {len(repeated)} of "
                    f"those names belong to more than one step (e.g. {repeated[0]!r}); every step with "
                    f"the name was flagged")
        else:
            flagged = {}
        for spec in self.specimens.values():
            quality = flagged.get(spec.name)
            if quality is not None and (quality != spec.steps["quality"].to_numpy(dtype=object)).any():
                spec.steps["quality"] = quality
                spec.arai = build_arai(spec.steps, spec.warnings)
        self.interpretations.clear()
        self._set_aside.clear()
        count = 0
        bounds = payload.get("bounds_in_kelvin", {})
        for item in payload.get("interpretations", []):
            name = item.get("specimen")
            spec = self.specimens.get(name)
            if spec is None or spec.arai is None:
                continue
            if name in bounds:
                tmin, tmax = bounds[name]
                imin = int(np.argmin(np.abs(spec.arai.temps - tmin)))
                imax = int(np.argmin(np.abs(spec.arai.temps - tmax)))
            else:
                imin, imax = int(item.get("imin", 0)), int(item.get("imax", 0))
            interp = self.set_interpretation(name, imin, imax)
            for key in ("quality", "name", "notes", "use_anisotropy", "use_nlt", "use_cooling_rate",
                        "anisotropy_type"):
                if key in item:
                    setattr(interp, key, item[key])
            count += 1
        for held in payload.get("set_aside", []) or []:
            try:
                interp = Interpretation(**held["interpretation"])
                bounds = (float(held["bounds_in_kelvin"][0]), float(held["bounds_in_kelvin"][1]))
            except (KeyError, TypeError, ValueError, IndexError):
                continue
            if interp.specimen in self.specimens and interp.specimen not in self.interpretations:
                self._set_aside[interp.specimen] = (interp, bounds)
        if criteria is not None:
            self.criteria = criteria
        policy = payload.get("anisotropy_policy")
        if isinstance(policy, dict):
            limit = policy.get("alteration_limit")
            self.anisotropy_alteration_limit = None if limit is None else float(limit)
            self.anisotropy_require_ftest = bool(policy.get("require_ftest", False))
        self.invalidate()
        return count

    @staticmethod
    def _criteria_from_json(payload: dict) -> Optional[CriteriaSet]:
        """The criteria set a session was saved under: the whole set when stored, else by name."""
        stored = payload.get("criteria_set")
        name = payload.get("criteria")
        if isinstance(stored, dict):
            try:
                def crits(rows):
                    return tuple(Criterion(str(k), str(op), v if isinstance(v, bool) else float(v))
                                 for k, op, v in rows)
                cs = CriteriaSet(str(stored.get("name", name or "session")), stored.get("citation", ""),
                                 stored.get("doi", ""), stored.get("description", ""),
                                 crits(stored.get("specimen", [])), crits(stored.get("site", [])))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"the session's criteria cannot be read ({exc})") from exc
            registered = CRITERIA_SETS.get(cs.name)
            if registered is not None and registered.specimen == cs.specimen and registered.site == cs.site:
                return registered
            if registered is None:
                CRITERIA_SETS[cs.name] = cs
            return cs
        if name in CRITERIA_SETS:
            return CRITERIA_SETS[name]
        return None

    def save_session(self, path: str) -> str:
        return mp.atomic_write_text(path, self.to_json())

    def load_session(self, path: str) -> int:
        with open(path, encoding="utf-8") as fh:
            return self.from_json(fh.read())

    # ----- legacy interchange ------------------------------------------------
    def write_redo(self, path: str) -> str:
        """The legacy Thellier GUI ``.redo`` format: specimen, Tmin, Tmax in kelvin."""
        lines = []
        for name in self.specimen_names:
            interp = self.interpretations.get(name)
            spec = self.specimens.get(name)
            if interp is None or spec is None or spec.arai is None:
                continue
            lines.append(f"{name}\t{spec.arai.temps[interp.imin]:.0f}\t{spec.arai.temps[interp.imax]:.0f}")
        return mp.atomic_write_text(path, "\n".join(lines) + ("\n" if lines else ""))

    def read_redo(self, path: str, replace: bool = True) -> Tuple[int, List[str]]:
        """Read a legacy Thellier GUI ``.redo`` file (specimen, Tmin, Tmax).

        The file is read and matched to the specimens before anything changes:
        a file that cannot be read, or none of whose lines is a specimen of this
        study, raises (``OSError`` / ``ValueError``) and leaves the current
        interpretations as they were.
        """
        with open(path, "rb") as fh:
            text, _ = mp.decode_table_text(fh.read())
        planned, problems, n_lines = [], [], 0
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 3:
                continue
            n_lines += 1
            name, tmin, tmax = parts[0], to_float(parts[1]), to_float(parts[2])
            spec = self.specimens.get(name)
            if spec is None or spec.arai is None:
                problems.append(f"{name}: not in this study")
                continue
            if np.isnan(tmin) or np.isnan(tmax):
                problems.append(f"{name}: unreadable bounds")
                continue
            imin = int(np.argmin(np.abs(spec.arai.temps - tmin)))
            imax = int(np.argmin(np.abs(spec.arai.temps - tmax)))
            # a .redo names a temperature, and matching it to a step by
            # nearest value is how a bound silently lands on the wrong one.
            # The interpretation is still made -- it is almost always right
            # -- but a bound that is not a step of this specimen is said so.
            for want, got in ((tmin, spec.arai.temps[imin]), (tmax, spec.arai.temps[imax])):
                if abs(got - want) > REDO_STEP_TOLERANCE:
                    problems.append(
                        f"{name}: {want - KELVIN_OFFSET:.0f} C is not a step of this "
                        f"specimen; used {got - KELVIN_OFFSET:.0f} C")
            planned.append((name, imin, imax))
        if n_lines and not planned:
            raise ValueError(f"{os.path.basename(path)} holds no interpretations of specimens in this study")
        if replace:
            self.interpretations.clear()
            self._set_aside.clear()
        for name, imin, imax in planned:
            self.set_interpretation(name, imin, imax)
        self.invalidate()
        return len(planned), problems

    def import_from_specimens_table(self) -> Tuple[int, List[str]]:
        """Re-import stored paleointensity interpretations from the specimens table.

        Each stored result gives its bounds (``meas_step_min/max``), the
        analyst's verdict (``result_quality``: a result stored as 'b' comes
        back rejected) and the corrections it was made with, from its method
        codes: DA-AC-ATRM / DA-AC-AARM (anisotropy, and which tensor), DA-CR
        (cooling rate), DA-NL (non-linear TRM). A row that says which
        corrections were applied -- it has ``int_corr`` ('c' or 'u') or any
        DA- code -- switches each correction on or off as it records; a row
        that says nothing leaves the defaults (use what is available). A
        stored correction this study cannot recompute is reported.
        """
        table = self._table("specimens")
        if table is None or "meas_step_min" not in table.columns:
            return 0, ["the specimens table has no meas_step_min column"]
        count, problems = 0, []
        for _, row in table.iterrows():
            name = str(row.get("specimen", ""))
            spec = self.specimens.get(name)
            if spec is None or spec.arai is None:
                continue
            if not str(row.get("method_codes", "")).count("LP-PI") and \
                    not np.isfinite(to_float(row.get("int_abs"))):
                continue
            tmin, tmax = to_float(row.get("meas_step_min")), to_float(row.get("meas_step_max"))
            if np.isnan(tmin) or np.isnan(tmax):
                continue
            unit = str(row.get("meas_step_unit", "K") or "K")
            if unit == "Celsius":
                tmin, tmax = tmin + KELVIN_OFFSET, tmax + KELVIN_OFFSET
            imin = int(np.argmin(np.abs(spec.arai.temps - tmin)))
            imax = int(np.argmin(np.abs(spec.arai.temps - tmax)))
            if abs(spec.arai.temps[imin] - tmin) > 1 or abs(spec.arai.temps[imax] - tmax) > 1:
                problems.append(f"{name}: stored bounds {tmin:.0f}-{tmax:.0f} K do not match a step")
            interp = self.set_interpretation(name, imin, imax)
            quality = row.get("result_quality")
            interp.quality = "b" if (not is_null(quality) and str(quality).strip() == "b") else "g"
            problems.extend(self._import_corrections(interp, row))
            count += 1
        self.invalidate()
        return count, problems

    def _import_corrections(self, interp: Interpretation, row) -> List[str]:
        """Set an interpretation's correction switches from a stored result row; returns problems."""
        codes = set(split_codes(row.get("method_codes", "")))
        corr = row.get("int_corr")
        corr = "" if is_null(corr) else str(corr).strip().lower()
        applied = {c for c in codes if c.startswith("DA-")}
        if corr not in ("c", "u") and not applied:
            return []                           # the row does not say: keep the defaults
        name = interp.specimen

        def factor_is_one(*columns) -> bool:
            # the legacy Thellier GUI records DA-AC-* for a specimen whose tensor
            # it then did not apply (factor 1.00, e.g. an altered ATRM): the
            # factor it wrote is the better record of what was done
            for column in columns:
                value = to_float(row.get(column))
                if np.isfinite(value):
                    return abs(value - 1.0) < 1e-9
            return False
        aniso_codes = {c for c in applied if c.startswith("DA-AC")}
        interp.use_anisotropy = bool(aniso_codes) and not factor_is_one("int_corr_aniso",
                                                                        "int_corr_anisotropy")
        interp.anisotropy_type = None if not interp.use_anisotropy else (
            "AARM" if "DA-AC-AARM" in aniso_codes else "ATRM" if "DA-AC-ATRM" in aniso_codes else None)
        interp.use_cooling_rate = (any(c.startswith("DA-CR") for c in applied)
                                   and not factor_is_one("int_corr_cooling_rate"))
        interp.use_nlt = any(c.startswith("DA-NL") for c in applied) and not factor_is_one("int_corr_nlt")
        problems = []
        aniso = self.anisotropy.get(name)
        if interp.use_anisotropy:
            kinds = {aniso["type"], *(aniso.get("alternatives") or {})} if aniso else set()
            if not aniso or (interp.anisotropy_type and interp.anisotropy_type not in kinds):
                problems.append(f"{name}: the stored result is anisotropy corrected "
                                f"({', '.join(sorted(aniso_codes))}), but no "
                                f"{interp.anisotropy_type or 'anisotropy'} tensor was found here")
        if interp.use_cooling_rate and name not in self.cooling_rate:
            problems.append(f"{name}: the stored result is cooling-rate corrected (DA-CR), but this "
                            f"study has no cooling-rate experiment or sample cooling rate for it")
        if interp.use_nlt and name not in self.nlt:
            problems.append(f"{name}: the stored result is NLT corrected (DA-NL), but no TRM "
                            f"acquisition experiment was found")
        return problems


# ---------------------------------------------------------------------------
# Derived quantities
# ---------------------------------------------------------------------------
def vadm(b_uT: float, lat: float) -> float:
    """Virtual axial dipole moment (Am^2) from an intensity and a site latitude."""
    if not np.isfinite(b_uT) or not np.isfinite(lat):
        return np.nan
    b = b_uT * 1e-6
    colat = math.radians(90.0 - lat)
    return float(4 * math.pi * (6.371e6 ** 3) * b / (1e-7 * 4 * math.pi)
                 / math.sqrt(1 + 3 * math.cos(colat) ** 2))


def vdm(b_uT: float, inc: float) -> float:
    """Virtual dipole moment (Am^2) from an intensity and the observed inclination."""
    if not np.isfinite(b_uT) or not np.isfinite(inc):
        return np.nan
    b = b_uT * 1e-6
    tan_i = math.tan(math.radians(inc))
    colat = math.atan2(2.0, tan_i) if tan_i != 0 else math.pi / 2
    return float(4 * math.pi * (6.371e6 ** 3) * b / (1e-7 * 4 * math.pi)
                 / math.sqrt(1 + 3 * math.cos(colat) ** 2))


# ---------------------------------------------------------------------------
# Plot geometry (shared by every front end)
# ---------------------------------------------------------------------------
def arai_xy(spec: PintSpecimen, normalize: bool = True) -> Tuple[np.ndarray, np.ndarray]:
    """The Arai plot points, optionally normalised by the NRM."""
    a = spec.arai
    if a is None:
        return np.array([]), np.array([])
    scale = a.y[0] if (normalize and a.y[0]) else 1.0
    return a.x / scale, a.y / scale


def zijderveld_xy(spec: PintSpecimen, rotation: float = 0.0) -> dict:
    """Horizontal and vertical projections of the zero-field steps."""
    a = spec.arai
    if a is None:
        return {}
    v = np.asarray(a.nrm_vectors, dtype=float)
    if rotation:
        theta = math.radians(rotation)
        rot = np.array([[math.cos(theta), math.sin(theta), 0.0],
                        [-math.sin(theta), math.cos(theta), 0.0],
                        [0.0, 0.0, 1.0]])
        v = v @ rot.T
    scale = a.y[0] if a.y[0] else 1.0
    return {"h_x": v[:, 1] / scale, "h_y": v[:, 0] / scale,
            "v_x": v[:, 1] / scale, "v_y": -v[:, 2] / scale,
            "temps": a.temps}


def decay_curve(spec: PintSpecimen) -> Tuple[np.ndarray, np.ndarray]:
    a = spec.arai
    if a is None:
        return np.array([]), np.array([])
    scale = a.y[0] if a.y[0] else 1.0
    return a.temps, a.y / scale
