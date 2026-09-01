"""
Reading, checking and converting ThellierTool ``.tdt`` files.

A ``.tdt`` file is the interchange format of the ThellierTool (Leonhardt et
al., 2004) and of several laboratory systems. It is two header lines and then
one line per measurement::

    Thellier-tdt
    <B_lab in microtesla>  <azimuth>  <plunge>  <bedding dip direction>  <bedding dip>
    <specimen>  <treatment>  <moment>  <declination>  <inclination>

The treatment is ``TTT.C``: ``TTT`` is the temperature in degrees Celsius and
``C`` is a step code

======  ====================================================================
``.0``  zero field (the NRM at the first step, thermal demagnetisation after)
``.1``  in field (pTRM acquisition)
``.2``  pTRM check
``.3``  pTRM tail check
``.4``  additivity check (Krasa et al., 2003)
``.5``  the antiparallel half of the original Thellier-Thellier protocol,
        paired with ``.1``
======  ====================================================================

This module exists because the format is easy to get slightly wrong and the
failures are silent: a file can convert without error and still produce a
study with no Arai plot at all. :func:`read` parses a file without judging it,
:func:`validate` reports every problem it can find with the line it is on, and
:func:`to_magic` writes MagIC 3 tables. See
``docs/thellier_issue_audit.md`` for the defects this replaces
(PmagPy/PmagPy#818).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

MAGIC_HEADER = "Thellier-tdt"
KELVIN_OFFSET = 273.0

#: step code -> (short name, MagIC 3 method code, in field?)
STEP_CODES = {
    0: ("zero field", "LT-T-Z", False),
    1: ("in field", "LT-T-I", True),
    2: ("pTRM check", "LT-PTRM-I", True),
    3: ("pTRM tail check", "LT-PTRM-MD", False),
    4: ("additivity check", "LT-PTRM-AC", True),
    5: ("in field, antiparallel", "LT-T-I", True),
}
#: a treatment temperature below this is read as the NRM, as ThellierTool does
NRM_TEMPERATURE_LIMIT = 50.0
#: two-digit codes ``.81`` .. ``.86`` are seen in the wild for an anisotropy
#: block written into the same file; they are not part of the documented
#: format, so they are recognised and reported rather than silently converted
ANISOTROPY_CODE_BASE = 80
#: the six-position order PmagPy assumes for such a block: +x, +y, +z, -x, -y, -z
ANISOTROPY_POSITION_DIRS = [(0.0, 0.0), (90.0, 0.0), (0.0, 90.0),
                            (180.0, 0.0), (270.0, 0.0), (0.0, -90.0)]

MOMENT_UNITS = {"Am^2": 1.0, "emu": 1e-3, "mA/m": None}      # mA/m needs the volume


@dataclass
class TdtRow:
    """One measurement line."""
    line: int
    specimen: str
    treatment: str
    temperature: float          # degrees Celsius as written
    code: int
    moment: float
    dec: float
    inc: float
    raw: str = ""

    @property
    def is_nrm(self) -> bool:
        return self.code == 0 and self.temperature < NRM_TEMPERATURE_LIMIT

    @property
    def temperature_k(self) -> float:
        return KELVIN_OFFSET if self.is_nrm else self.temperature + KELVIN_OFFSET


@dataclass
class TdtFile:
    """A parsed ``.tdt`` file: its header, its rows, and how it was read."""
    path: str
    blab_uT: float = math.nan
    azimuth: float = math.nan
    plunge: float = math.nan
    bed_dip_direction: float = math.nan
    bed_dip: float = math.nan
    rows: List[TdtRow] = field(default_factory=list)
    header_line: str = ""
    parse_errors: List["Issue"] = field(default_factory=list)
    line_ending: str = ""

    @property
    def specimens(self) -> List[str]:
        seen = []
        for row in self.rows:
            if row.specimen not in seen:
                seen.append(row.specimen)
        return seen

    def rows_for(self, specimen: str) -> List[TdtRow]:
        return [r for r in self.rows if r.specimen == specimen]

    def protocol(self, specimen: Optional[str] = None) -> str:
        """'IZZI', 'Coe', 'Aitken', 'Thellier-Thellier' or 'unknown'."""
        rows = self.rows if specimen is None else self.rows_for(specimen)
        codes = {r.code for r in rows}
        zero = {r.temperature for r in rows if r.code == 0 and not r.is_nrm}
        # '.5' is the antiparallel half of a '.1'; with zero-field steps present
        # the experiment is a normal Coe/IZZI one whose field was reversed
        if 5 in codes and not zero:
            return "Thellier-Thellier"
        order = _pair_order(rows)
        if "ZI" in order and "IZ" in order:
            return "IZZI"
        if order == {"ZI"}:
            return "Coe"
        if order == {"IZ"}:
            return "Aitken"
        return "unknown"

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([{"line": r.line, "specimen": r.specimen, "treatment": r.treatment,
                              "temperature": r.temperature, "code": r.code,
                              "step": STEP_CODES.get(r.code, ("unknown",))[0],
                              "moment": r.moment, "dec": r.dec, "inc": r.inc} for r in self.rows])


def _pair_order(rows: Sequence[TdtRow]) -> set:
    """Which halves came first at each temperature: {'ZI'}, {'IZ'} or both."""
    seen: Dict[float, List[int]] = {}
    for row in rows:
        if row.code in (0, 1, 5) and not row.is_nrm:
            seen.setdefault(row.temperature, []).append(0 if row.code == 0 else 1)
    out = set()
    for codes in seen.values():
        if 0 in codes and 1 in codes:
            out.add("ZI" if codes.index(0) < codes.index(1) else "IZ")
    return out


@dataclass
class Issue:
    """One problem found in a file, with the line it is on and what to do."""
    level: str                  # 'error' | 'warning' | 'note'
    code: str
    message: str
    line: Optional[int] = None
    specimen: str = ""
    hint: str = ""

    def __str__(self) -> str:
        where = f"line {self.line}" if self.line else "file"
        who = f" [{self.specimen}]" if self.specimen else ""
        hint = f"  -> {self.hint}" if self.hint else ""
        return f"{self.level}: {where}{who}: {self.message}{hint}"


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
def read(path: str) -> TdtFile:
    """Parse a ``.tdt`` file. Never raises: problems become ``parse_errors``."""
    with open(path, "rb") as fh:
        raw = fh.read()
    ending = "CRLF" if b"\r\n" in raw else ("CR" if b"\r" in raw else "LF")
    text = raw.decode("utf-8", errors="replace")
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = TdtFile(path=path, line_ending=ending)

    if not lines or MAGIC_HEADER.lower() not in lines[0].strip().lower():
        out.parse_errors.append(Issue(
            "error", "header-missing",
            f"the first line should be {MAGIC_HEADER!r}, found {lines[0].strip()[:40]!r}"
            if lines else "the file is empty", line=1,
            hint=f"add a first line reading {MAGIC_HEADER}"))
    out.header_line = lines[0].strip() if lines else ""

    if len(lines) < 2:
        out.parse_errors.append(Issue("error", "header-short", "the file has no second header line",
                                      line=2, hint="the second line is: B_lab (microtesla), azimuth, "
                                                   "plunge, bedding dip direction, bedding dip"))
        return out
    header = lines[1].split()
    values = []
    for token in header[:5]:
        try:
            values.append(float(token))
        except ValueError:
            values.append(math.nan)
    while len(values) < 5:
        values.append(math.nan)
    out.blab_uT, out.azimuth, out.plunge, out.bed_dip_direction, out.bed_dip = values
    if not header:
        out.parse_errors.append(Issue("error", "header-empty", "the second header line is empty", line=2))

    for number, line in enumerate(lines[2:], start=3):
        if not line.strip():
            continue
        if line.strip().upper().startswith("END"):
            break
        parts = line.split()
        if len(parts) < 5:
            out.parse_errors.append(Issue(
                "error", "row-short", f"expected 5 fields, found {len(parts)}", line=number,
                hint="the fields are: specimen, treatment, moment, declination, inclination"))
            continue
        specimen, treatment = parts[0], parts[1]
        try:
            moment, dec, inc = float(parts[2]), float(parts[3]), float(parts[4])
        except ValueError:
            out.parse_errors.append(Issue(
                "error", "row-unreadable",
                f"moment, declination or inclination is not a number: {parts[2:5]}", line=number,
                specimen=specimen))
            continue
        temperature, code, problem = _split_treatment(treatment)
        if problem:
            out.parse_errors.append(Issue("error", "treatment-unreadable", problem, line=number,
                                          specimen=specimen,
                                          hint="the treatment is TTT.C: temperature in Celsius, "
                                               "then one digit for the step code (0-5)"))
            continue
        out.rows.append(TdtRow(line=number, specimen=specimen, treatment=treatment,
                               temperature=temperature, code=code, moment=moment,
                               dec=dec, inc=inc, raw=line))
    return out


def _split_treatment(treatment: str) -> Tuple[float, int, str]:
    """``'400.1'`` -> ``(400.0, 1, '')``; a bad code returns the reason."""
    token = treatment.strip()
    if "." not in token:
        try:
            return float(token), 0, ""
        except ValueError:
            return math.nan, -1, f"{treatment!r} is not a treatment"
    head, tail = token.split(".", 1)
    head = head or "0"
    try:
        temperature = float(head)
    except ValueError:
        return math.nan, -1, f"{treatment!r} has no readable temperature"
    tail = tail.strip()
    if tail == "":
        return temperature, 0, ""
    if not tail.isdigit():
        return temperature, -1, f"{treatment!r} has a non-numeric step code {tail!r}"
    if len(tail) == 1:
        code = int(tail)
    elif tail[1:] == "0" * (len(tail) - 1):
        code = int(tail[0])                    # '.10' and '.00' are '.1' and '.0' written out
    elif tail[0] == "8" and len(tail) == 2:
        code = ANISOTROPY_CODE_BASE + int(tail[1])   # '.81'..'.86': an embedded anisotropy block
    else:
        return temperature, -1, (f"{treatment!r} has a {len(tail)}-digit step code {tail!r}; the "
                                 f"step code is a single digit 0-5")
    if code not in STEP_CODES and not (ANISOTROPY_CODE_BASE < code <= ANISOTROPY_CODE_BASE + 8):
        return temperature, -1, f"{treatment!r} uses step code {code}, which is not one of 0-5"
    return temperature, code, ""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate(tdt: TdtFile, volume_cc: float = 12.0, moment_units: str = "Am^2",
             expected_specimen: Optional[str] = None) -> List[Issue]:
    """Every problem this file would cause, with the line it is on.

    The checks cover the header, the treatment sequence, the units, the
    specimen naming, the pairing that a Thellier experiment requires, and the
    checks that reference temperatures the experiment never reached.
    """
    issues: List[Issue] = list(tdt.parse_errors)

    if not np.isfinite(tdt.blab_uT) or tdt.blab_uT <= 0:
        issues.append(Issue("error", "blab-missing",
                            "the laboratory field on the second line is missing or not positive",
                            line=2, hint="the first number of the second line is |B_lab| in microtesla"))
    elif tdt.blab_uT > 1000:
        issues.append(Issue("warning", "blab-units",
                            f"the laboratory field reads {tdt.blab_uT:g}; that is very large for "
                            f"microtesla", line=2,
                            hint="B_lab is given in microtesla, so 45 rather than 45000 or 4.5e-05"))
    if moment_units not in MOMENT_UNITS:
        issues.append(Issue("error", "units-unknown",
                            f"moment units {moment_units!r} are not one of {sorted(MOMENT_UNITS)}"))
    if moment_units == "mA/m" and not (volume_cc and volume_cc > 0):
        issues.append(Issue("error", "volume-missing",
                            "moments in mA/m need a specimen volume to become Am^2",
                            hint="give the volume in cubic centimetres"))
    if not tdt.rows:
        issues.append(Issue("error", "no-rows", "the file has no readable measurements"))
        return issues

    names = tdt.specimens
    if len(names) > 1:
        issues.append(Issue("warning", "many-specimens",
                            f"the file holds {len(names)} specimens ({', '.join(names[:4])}"
                            f"{'...' if len(names) > 4 else ''})",
                            hint="ThellierTool writes one specimen per file; check the first column"))
    stem = os.path.splitext(os.path.basename(tdt.path))[0]
    for name in names:
        if expected_specimen and name != expected_specimen:
            issues.append(Issue("warning", "specimen-name",
                                f"the rows name the specimen {name!r}, not {expected_specimen!r}",
                                specimen=name))
        elif not expected_specimen and name != stem:
            issues.append(Issue("note", "specimen-name",
                                f"the specimen is named {name!r} in the rows and {stem!r} by the "
                                f"file name", specimen=name,
                                hint="the rows win unless you choose 'specimen = file name'"))

    for name in names:
        issues.extend(_validate_specimen(tdt, name))
    return issues


def _validate_specimen(tdt: TdtFile, specimen: str) -> List[Issue]:
    rows = tdt.rows_for(specimen)
    issues: List[Issue] = []
    zero: Dict[float, List[TdtRow]] = {}
    infield: Dict[float, List[TdtRow]] = {}
    anti: Dict[float, List[TdtRow]] = {}
    aniso: Dict[float, List[TdtRow]] = {}
    checks: List[TdtRow] = []
    nrm_rows = [r for r in rows if r.is_nrm]
    for row in rows:
        if row.is_nrm:
            continue
        if row.code == 0:
            zero.setdefault(row.temperature, []).append(row)
        elif row.code == 1:
            infield.setdefault(row.temperature, []).append(row)
        elif row.code == 5:
            anti.setdefault(row.temperature, []).append(row)
        elif row.code > ANISOTROPY_CODE_BASE:
            aniso.setdefault(row.temperature, []).append(row)
        else:
            checks.append(row)

    if not nrm_rows:
        issues.append(Issue("warning", "no-nrm",
                            "there is no NRM step (a treatment below 50 with code 0)",
                            specimen=specimen,
                            hint="the first zero-field step will normalise the plot instead"))
    elif len(nrm_rows) > 1:
        issues.append(Issue("note", "many-nrm", f"{len(nrm_rows)} NRM steps; the first is used",
                            line=nrm_rows[1].line, specimen=specimen))

    for temp, group in sorted(aniso.items()):
        issues.append(Issue(
            "warning", "anisotropy-block",
            f"{len(group)} steps at {temp:g}C use two-digit codes .8n, which look like a "
            f"six-position anisotropy experiment written into the paleointensity file",
            line=group[0].line, specimen=specimen,
            hint="the .8n codes are not part of the documented tdt format; confirm they are ATRM "
                 "positions and import them as anisotropy, or move them to their own file"))

    protocol = tdt.protocol(specimen)
    if protocol == "Thellier-Thellier":
        for temp in sorted(set(infield) | set(anti)):
            if temp not in infield or temp not in anti:
                missing = ".5" if temp not in anti else ".1"
                line = (infield.get(temp) or anti.get(temp))[0].line
                issues.append(Issue("error", "unpaired-antiparallel",
                                    f"{temp:g}C has no {missing} step, so the original "
                                    f"Thellier-Thellier pair is incomplete", line=line,
                                    specimen=specimen,
                                    hint="each temperature needs both .1 and .5"))
        if zero:
            issues.append(Issue("warning", "mixed-protocol",
                                f"{len(zero)} zero-field (.0) steps in a file that also uses .5",
                                specimen=specimen,
                                hint="a file is either Coe/IZZI (.0 and .1) or original "
                                     "Thellier-Thellier (.1 and .5), not both"))
    else:
        for temp, group in anti.items():
            infield.setdefault(temp, []).extend(group)
        if anti:
            issues.append(Issue("note", "antiparallel-infield",
                                f"{len(anti)} steps use code .5 (an antiparallel laboratory "
                                f"field) alongside zero-field steps", specimen=specimen,
                                hint="they are read as the in-field half of each pair, with the "
                                     "field reversed"))
        for temp in sorted(set(zero) | set(infield)):
            if temp not in zero:
                issues.append(Issue("error", "unpaired-infield",
                                    f"{temp:g}C has an in-field step with no zero-field step, so "
                                    f"it cannot make an Arai point", line=infield[temp][0].line,
                                    specimen=specimen,
                                    hint="add the .0 step or remove the .1 step"))
            elif temp not in infield:
                if temp != min(set(zero) | set(infield)):
                    issues.append(Issue("warning", "unpaired-zerofield",
                                        f"{temp:g}C has a zero-field step with no in-field step; "
                                        f"the point will plot at zero pTRM",
                                        line=zero[temp][0].line, specimen=specimen))
        for temp, group in {**zero, **infield}.items():
            pass
        for label, group in (("zero-field", zero), ("in-field", infield)):
            for temp, rs in group.items():
                if len(rs) > 1:
                    issues.append(Issue("warning", "duplicate-step",
                                        f"{temp:g}C has {len(rs)} {label} steps; the last is used",
                                        line=rs[-1].line, specimen=specimen))

    reached = sorted(set(zero) | set(infield) | set(anti))
    for row in checks:
        name = STEP_CODES[row.code][0]
        if row.temperature not in reached:
            issues.append(Issue("warning", "check-off-grid",
                                f"the {name} at {row.temperature:g}C is at a temperature the "
                                f"experiment never used, so it cannot be compared",
                                line=row.line, specimen=specimen))
    peak = -math.inf
    order_ok = True
    for row in rows:
        if row.code in (0, 1, 5) and not row.is_nrm:
            if row.temperature < peak - 1e-9:
                order_ok = False
            peak = max(peak, row.temperature)
    if not order_ok:
        issues.append(Issue("warning", "non-monotonic",
                            "the zero-field/in-field temperatures do not increase through the file",
                            specimen=specimen,
                            hint="checks may go back to lower temperatures, but the experiment "
                                 "itself should step upwards"))

    moments = np.array([r.moment for r in rows if np.isfinite(r.moment)])
    if len(moments) and np.all(moments == 0):
        issues.append(Issue("error", "zero-moments", "every moment is zero", specimen=specimen))
    incs = np.array([r.inc for r in rows])
    if len(incs) and (np.any(incs > 90.001) or np.any(incs < -90.001)):
        issues.append(Issue("error", "inc-range",
                            "an inclination is outside -90 to 90; the columns may be in the wrong "
                            "order", specimen=specimen,
                            hint="the column order is specimen, treatment, moment, declination, "
                                 "inclination"))
    if len(reached) < 3:
        issues.append(Issue("error", "too-few-steps",
                            f"only {len(reached)} treatment steps; at least three are needed for "
                            f"an Arai plot", specimen=specimen))
    return issues


def summarise(issues: Iterable[Issue]) -> dict:
    issues = list(issues)
    return {"errors": sum(1 for i in issues if i.level == "error"),
            "warnings": sum(1 for i in issues if i.level == "warning"),
            "notes": sum(1 for i in issues if i.level == "note"),
            "ok": not any(i.level == "error" for i in issues)}


def issues_frame(issues: Iterable[Issue]) -> pd.DataFrame:
    """The issues as a table, for the import panel."""
    return pd.DataFrame([{"level": i.level, "line": i.line, "specimen": i.specimen,
                          "problem": i.message, "what to do": i.hint, "code": i.code}
                         for i in issues])


# ---------------------------------------------------------------------------
# Conversion to MagIC 3
# ---------------------------------------------------------------------------
def measurement_records(tdt: TdtFile, volume_cc: float = 12.0, moment_units: str = "Am^2",
                        lab_dec: float = 0.0, lab_inc: float = 90.0,
                        specimen_from_filename: bool = False,
                        sample_name=None, site_name=None,
                        location: str = "unknown",
                        import_anisotropy: bool = False) -> List[dict]:
    """MagIC 3 measurement records for one parsed file.

    The original Thellier-Thellier protocol (``.1`` with ``.5``) is written as
    two in-field steps with antiparallel laboratory fields and the
    ``LP-PI-II`` protocol code; the Arai plot is formed from the pair by the
    analysis core, which is where the arithmetic belongs. Earlier PmagPy
    releases lost the step codes here entirely (PmagPy/PmagPy#818).
    """
    scale = MOMENT_UNITS.get(moment_units, 1.0)
    if moment_units == "mA/m":
        scale = 1e-3 * (volume_cc * 1e-6)
    stem = os.path.splitext(os.path.basename(tdt.path))[0]
    protocol = tdt.protocol()
    protocol_codes = ["LP-PI-TRM"]
    if protocol == "IZZI":
        protocol_codes.append("LP-PI-BT-IZZI")
    elif protocol == "Coe":
        protocol_codes.append("LP-PI-TRM-ZI")
    elif protocol == "Aitken":
        protocol_codes.append("LP-PI-TRM-IZ")
    elif protocol == "Thellier-Thellier":
        protocol_codes.append("LP-PI-II")
    if any(r.code == 2 for r in tdt.rows):
        protocol_codes.append("LP-PI-ALT-PTRM")
    if any(r.code == 3 for r in tdt.rows):
        protocol_codes.append("LP-PI-BT-MD")
    if any(r.code == 4 for r in tdt.rows):
        protocol_codes.append("LP-PI-BT")

    blab = (tdt.blab_uT or 0.0) * 1e-6
    records = []
    pair_label = _pair_labels(tdt)
    for number, row in enumerate(tdt.rows, start=1):
        specimen = stem if specimen_from_filename else row.specimen
        sample = sample_name(specimen) if callable(sample_name) else (sample_name or specimen)
        site = site_name(sample) if callable(site_name) else (site_name or sample)
        codes = list(protocol_codes)
        if row.code > ANISOTROPY_CODE_BASE:
            # an anisotropy block written into the paleointensity file; only
            # imported when the analyst has confirmed the position order,
            # because guessing it silently corrupts the correction
            if not import_anisotropy:
                continue
            position = row.code - ANISOTROPY_CODE_BASE
            if not 1 <= position <= 6:
                continue
            phi, theta = ANISOTROPY_POSITION_DIRS[position - 1]
            records.append({
                "specimen": specimen, "sample": sample, "site": site, "location": location,
                "measurement": f"{specimen}-{number}", "treat_step_num": position,
                "treat_temp": f"{row.temperature_k:.1f}", "treat_dc_field": f"{blab:.3e}",
                "treat_dc_field_phi": f"{phi:.1f}", "treat_dc_field_theta": f"{theta:.1f}",
                "meas_temp": "273", "dir_dec": f"{row.dec:.1f}", "dir_inc": f"{row.inc:.1f}",
                "magn_moment": f"{row.moment * scale:.6e}",
                "method_codes": "LP-AN-TRM:LT-T-I", "quality": "g", "standard": "u",
                "citations": "This study",
                "description": f"tdt {row.treatment}: anisotropy position {position} "
                               f"(order assumed +x +y +z -x -y -z)",
            })
            continue
        if row.is_nrm:
            codes.append("LT-NO")
            field, phi, theta = 0.0, 0.0, 0.0
        else:
            codes.append(STEP_CODES[row.code][1])
            in_field = STEP_CODES[row.code][2]
            field = blab if in_field else 0.0
            if row.code == 5:
                phi, theta = (lab_dec + 180.0) % 360.0, -lab_inc
            else:
                phi, theta = (lab_dec, lab_inc) if in_field else (0.0, 0.0)
            label = pair_label.get((specimen, row.temperature))
            if row.code in (0, 1, 5) and label:
                codes.append("LP-PI-TRM-" + label)
        records.append({
            "specimen": specimen, "sample": sample, "site": site, "location": location,
            "measurement": f"{specimen}-{number}",
            "treat_step_num": number,
            "treat_temp": f"{row.temperature_k:.1f}",
            "treat_dc_field": f"{field:.3e}",
            "treat_dc_field_phi": f"{phi:.1f}",
            "treat_dc_field_theta": f"{theta:.1f}",
            "meas_temp": "273",
            "dir_dec": f"{row.dec:.1f}", "dir_inc": f"{row.inc:.1f}",
            "magn_moment": f"{row.moment * scale:.6e}",
            "method_codes": ":".join(sorted(set(codes))),
            "quality": "g", "standard": "u", "citations": "This study",
            "description": f"tdt {row.treatment} ({STEP_CODES.get(row.code, ('?',))[0]})",
        })
    return records


def _pair_labels(tdt: TdtFile) -> Dict[Tuple[str, float], str]:
    """'ZI' or 'IZ' for every (specimen, temperature) that has both halves."""
    out: Dict[Tuple[str, float], str] = {}
    for specimen in tdt.specimens:
        seen: Dict[float, List[int]] = {}
        for row in tdt.rows_for(specimen):
            if row.code in (0, 1, 5) and not row.is_nrm:
                seen.setdefault(row.temperature, []).append(0 if row.code == 0 else 1)
        for temp, codes in seen.items():
            if 0 in codes and 1 in codes:
                out[(specimen, temp)] = "ZI" if codes.index(0) < codes.index(1) else "IZ"
    return out


def to_magic(paths, out_dir: str, volume_cc: float = 12.0, moment_units: str = "Am^2",
             lab_dec: float = 0.0, lab_inc: float = 90.0, location: str = "unknown",
             specimen_from_filename: bool = False, sample_name=None, site_name=None,
             validate_first: bool = True, import_anisotropy: bool = False) -> dict:
    """Convert one or more ``.tdt`` files to MagIC 3 tables in ``out_dir``.

    Returns ``{'files': [...], 'issues': [...], 'specimens': [...], 'ok': bool}``.
    Nothing is written when ``validate_first`` and any file has an error.
    """
    if isinstance(paths, (str, os.PathLike)):
        paths = find_tdt_files(paths)
    paths = list(paths)
    parsed, issues = [], []
    for path in paths:
        tdt = read(path)
        parsed.append(tdt)
        issues.extend(validate(tdt, volume_cc=volume_cc, moment_units=moment_units))
    if validate_first and any(i.level == "error" for i in issues):
        return {"files": [], "issues": issues, "specimens": [], "ok": False}

    records = []
    for tdt in parsed:
        records.extend(measurement_records(
            tdt, volume_cc=volume_cc, moment_units=moment_units, lab_dec=lab_dec, lab_inc=lab_inc,
            specimen_from_filename=specimen_from_filename, sample_name=sample_name,
            site_name=site_name, location=location, import_anisotropy=import_anisotropy))
    if not records:
        issues.append(Issue("error", "no-records", "no measurements to write"))
        return {"files": [], "issues": issues, "specimens": [], "ok": False}

    meas = pd.DataFrame(records)
    meas.insert(0, "sequence", range(1, len(meas) + 1))
    meas["experiment"] = meas["specimen"] + ":LP-PI-TRM"
    os.makedirs(out_dir, exist_ok=True)
    written = []
    from pmagpy import magic_project as mp
    specimens = meas[["specimen", "sample"]].drop_duplicates().copy()
    specimens["citations"] = "This study"
    samples = meas[["sample", "site"]].drop_duplicates().copy()
    samples["citations"] = "This study"
    sites = meas[["site", "location"]].drop_duplicates().copy()
    sites["citations"] = "This study"
    locations = pd.DataFrame([{"location": location, "citations": "This study",
                               "location_type": "outcrop"}])
    for df, table in ((meas.drop(columns=["sample", "site", "location"]), "measurements"),
                      (specimens, "specimens"), (samples, "samples"),
                      (sites, "sites"), (locations, "locations")):
        written.append(mp.magic_write(os.path.join(out_dir, table + ".txt"), df, table))
    return {"files": written, "issues": issues,
            "specimens": sorted(set(meas["specimen"])), "ok": True}


def find_tdt_files(directory: str) -> List[str]:
    """Every ``.tdt`` file in a directory, whatever the case of the extension.

    Earlier PmagPy releases matched only the lower-case ``.tdt``, so a file
    saved as ``SPECIMEN.TDT`` was silently skipped (PmagPy/PmagPy#818).
    """
    if os.path.isfile(directory):
        return [directory]
    return sorted(os.path.join(directory, name) for name in os.listdir(directory)
                  if name.lower().endswith(".tdt"))
