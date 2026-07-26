"""First-order reversal curve (FORC) processing for RockmagPy.

This module reads FORC measurements from Lake Shore (Princeton MicroMag) VSM
files or from MagIC measurement tables, conditions them (drift correction,
endpoint replacement, optional regridding), estimates the FORC distribution by
locally weighted quadratic regression, and renders and quantifies the result.

Field conventions
-----------------
The naming follows :cite:`Pike1999` and the subsequent FORC literature
(Roberts et al., 2000; Harrison & Feinberg, 2008; Egli, 2013):

* ``Hb`` is the **reversal field** at which a curve begins.
* ``Ha`` is the **applied field** along that curve, with ``Ha >= Hb``.
* The FORC distribution is ``rho(Hb, Ha) = -0.5 * d2M / (dHb dHa)``.
* Diagrams are drawn in the rotated coordinates ``Bc = (Ha - Hb) / 2``
  (coercivity) and ``Bu = (Ha + Hb) / 2`` (interaction/bias field).

All fields are in tesla and all moments in A m^2 unless stated otherwise; cgs
input files are converted on read (see :func:`read_header_tags_and_data_start`).

Note that MicroMag FORC file headers use ``Hb1``/``hdr_Bu_max`` for the *bias* axis
limits of the FORC diagram and ``Hc1``/``hdr_Bc_max`` for the coercivity axis limits.
Those are display bounds, not the reversal/applied fields above; this module
reads them into ``Bu_min``/``Bu_max`` and ``Bc_min``/``Bc_max`` to keep the two
meanings distinct.

Originally contributed as FORCme by Maxwell Brown (Institute for Rock
Magnetism, University of Minnesota) under NSF award EAR-2148549, building on
methods developed by Pike, Roberts, Harrison, Egli, Muxworthy, Feinberg and
others.
"""
from __future__ import annotations

import csv
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from mpl_toolkits.axes_grid1 import make_axes_locatable

from scipy.interpolate import RegularGridInterpolator

# ============================================================
# Regex helpers
# ============================================================

_FLOAT = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"
_NUM_LINE = re.compile(rf"^\s*({_FLOAT})\s*,\s*({_FLOAT})\s*$")
# Header tags come in two MicroMag styles: "HCal<tab>1.1" on current Lake Shore
# exports and "HCal           = +4.610101E+03" on older Series 0015 files.
# Names may contain spaces ("Field range"), so the value anchor does the work.
_TAG_LINE = re.compile(rf"^\s*([A-Za-z][A-Za-z0-9_ .'?-]*?)\s*(?:=|\s)\s*({_FLOAT})\s*$")

@dataclass
class Segment:
    H: np.ndarray                 # Field (T)
    M: np.ndarray                 # Moment (A m^2)
    idx: int                      # Segment index in file order
    kind: str = "unknown"         # "forc" or "cal"
    Ha: Optional[float] = None    # inferred reversal field for FORCs

# ============================================================
# Plot style
# ============================================================

def set_plot_style(
    font_family: str = "Arial",
    labelsize: int = 14,
    titlesize: int = 14,
    ticksize: int = 14,
    legendsize: int = 12
) -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [font_family],
        "axes.labelsize": labelsize,
        "axes.titlesize": titlesize,
        "legend.fontsize": legendsize,
        "xtick.labelsize": ticksize,
        "ytick.labelsize": ticksize,
        "axes.formatter.useoffset": False,
        "axes.formatter.limits": (-3, 3),
    })

PathLike = Union[str, os.PathLike]

# --------------------------
# Cross-platform path helpers
# --------------------------

_WIN_BAD_CHARS = r'<>:"/\\|?*\x00-\x1F'
_WIN_RESERVED = {
    "CON","PRN","AUX","NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

def as_path(p: PathLike) -> Path:
    """
    Convert user input to a Path robustly:
    - expands ~
    - expands env vars like %USERPROFILE% / $HOME
    - tolerates users pasting Windows paths on mac (won't break read; just a path string)
    """
    s = os.fspath(p)
    s = os.path.expandvars(s)
    s = os.path.expanduser(s)
    return Path(s)

def ensure_parent_dir(filepath: PathLike) -> Path:
    """Create parent directory for an output file path (cross-platform)."""
    out = as_path(filepath)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out

def safe_filename(name: str, replacement: str = "_") -> str:
    """
    Make a filename safe across Windows/mac/Linux.
    - removes illegal Windows chars
    - trims trailing dot/space (Windows)
    - avoids reserved device names (Windows)
    """
    name = re.sub(f"[{_WIN_BAD_CHARS}]", replacement, name).strip()
    name = name.rstrip(" .")  # Windows hates trailing dot/space
    if not name:
        name = "output"

    stem, dot, suffix = name.partition(".")
    if stem.upper() in _WIN_RESERVED:
        stem = stem + replacement
    return stem + (dot + suffix if dot else "")

def get_forc_output_base_dir(out: Dict[str, object]) -> Path:
    """
    Resolve the base output directory for FORC exports.

    Priority:
      1) If run_forc_pipeline stored an explicit input_path, use that.
      2) Else if input_files exists, use the parent of the first file.
      3) Else fallback to current working directory.
    """
    p = out.get("input_path", None)
    if p is not None:
        p = as_path(p)
        if p.is_dir():
            return p
        if p.exists():
            return p.parent

    input_files = out.get("input_files", None)
    if input_files and len(input_files) > 0:
        try:
            first_input = as_path(input_files[0])
            return first_input.parent
        except Exception:
            pass

    return Path.cwd()

def get_forc_profiles_dir(out: Dict[str, object]) -> Path:
    out_dir = get_forc_output_base_dir(out) / "FORC_profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir

def get_forc_figures_dir(out: Dict[str, object]) -> Path:
    out_dir = get_forc_output_base_dir(out) / "FORC_figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


# ============================================================
# MagIC measurement export
# ============================================================

MAGIC_MEASUREMENT_HEADERS = [
    "row_id", "measurement", "experiment", "specimen", "sequence", "standard", "quality",
    "method_codes", "instrument_codes", "display_order", "result_type", "citations",
    "treat_temp", "treat_temp_decay_rate", "treat_temp_dc_on", "treat_temp_dc_off",
    "treat_ac_field", "treat_ac_field_decay_rate", "treat_ac_field_dc_on", "treat_ac_field_dc_off",
    "treat_dc_field", "treat_dc_field_decay_rate", "treat_dc_field_ac_on", "treat_dc_field_ac_off",
    "treat_dc_field_theta", "treat_dc_field_phi", "treat_mw_power", "treat_mw_time",
    "treat_mw_integral", "treat_mw_step", "treat_step_num", "meas_pos_x", "meas_pos_y",
    "meas_pos_z", "meas_orient_theta", "meas_orient_phi", "meas_n_orient", "meas_temp",
    "meas_temp_change", "meas_freq", "meas_duration", "meas_field_ac", "meas_field_ac_theta",
    "meas_field_ac_phi", "meas_field_dc", "meas_field_dc_theta", "meas_field_dc_phi",
    "inversion_height", "inversion_residuals", "magn_moment", "magn_x", "magn_x_sigma", "magn_y",
    "magn_y_sigma", "magn_z", "magn_z_sigma", "magn_xyz_sigma", "magn_induction", "magn_b_x",
    "magn_b_x_sigma", "magn_b_y", "magn_b_y_sigma", "magn_b_z", "magn_b_z_sigma", "magn_b_111",
    "magn_b_111_sigma", "magn_b_xyz_sigma", "magn_r2_det", "dir_dec", "dir_inc", "dir_csd",
    "magn_volume", "magn_mass", "magn_uncal", "aniso_type", "aniso_s", "hyst_loop",
    "hyst_sweep_rate", "hyst_charging_mode", "susc_chi_volume", "susc_chi_mass",
    "susc_chi_qdr_volume", "susc_chi_qdr_mass", "description", "timestamp", "software_packages",
    "files", "external_database_ids", "derived_value", "analysts",
]

def _magic_basename(path: PathLike) -> str:
    return as_path(path).stem.replace(" ", "-")

def _magic_timestamp_now() -> str:
    """Return the current time as an ISO-8601 timestamp, as MagIC expects."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def _read_numeric_groups_by_blanklines(path: PathLike, data_start_idx: Optional[int] = None) -> List[List[Tuple[float, float]]]:
    """
    Read the raw FORC numeric section and split it into contiguous numeric groups
    separated by one or more blank lines.

    This matches the export structure described by the user:
      group 1 = calibration line for block 1
      group 2 = FORC measurement lines for block 1
      group 3 = calibration line for block 2
      group 4 = FORC measurement lines for block 2
      etc.
    """
    txt = _read_text_normalized(path)
    lines = txt.split("\n")

    if data_start_idx is None:
        _, data_start_idx = read_header_tags_and_data_start(path)

    units = read_file_units(path)
    field_scale = float(units["field_scale"])
    moment_scale = float(units["moment_scale"])

    groups: List[List[Tuple[float, float]]] = []
    cur: List[Tuple[float, float]] = []

    for line in lines[data_start_idx:]:
        s = line.strip()
        if s == "":
            if cur:
                groups.append(cur)
                cur = []
            continue
        parsed = _parse_first_two_numeric_columns(s)
        if parsed is not None:
            cur.append((parsed[0] * field_scale, parsed[1] * moment_scale))

    if cur:
        groups.append(cur)

    return groups

def build_magic_rows_from_raw_groups(
    path: PathLike,
    groups: List[List[Tuple[float, float]]],
    meas_temp_k: Optional[float] = None,
    specimen: Optional[str] = None,
    experiment: Optional[str] = None,
    instrument_codes: str = "",
    citations: str = "This study",
    analysts: str = "",
    timestamp: Optional[str] = None,
) -> List[Dict[str, object]]:
    """Convert blank-line-delimited raw groups into MagIC measurement rows.

    The raw file alternates a one-point calibration group with the points of
    the FORC that follows it. Calibration points are written as measurement
    ``...-n-0`` and the curve points as ``...-n-1``, ``...-n-2`` and so on, so
    the block structure survives the round trip and the drift record is
    preserved.

    Args:
        path: Source file, used to derive default names.
        groups: Numeric groups from
            :func:`_read_numeric_groups_by_blanklines`.
        meas_temp_k: Measurement temperature in kelvin.
        specimen: Specimen name. Defaults to the file stem.
        experiment: Experiment name. Defaults to ``LP-FORC-<stem>``.
        instrument_codes: MagIC instrument code, e.g. ``IRM_VSM_Lake_Shore``.
        citations: Citation string for the measurements.
        analysts: Analyst names.
        timestamp: ISO-8601 measurement timestamp. Defaults to now.

    Returns:
        One dict per measurement, keyed by the MagIC measurements columns.
    """
    basename = _magic_basename(path)
    experiment = experiment or f"LP-FORC-{basename}"
    specimen = specimen or basename
    timestamp = timestamp or _magic_timestamp_now()
    source_file = as_path(path).name

    rows: List[Dict[str, object]] = []
    treat_step_num = 0

    def blank_row() -> Dict[str, str]:
        return {h: "" for h in MAGIC_MEASUREMENT_HEADERS}

    def append_row(measurement_name: str, hval: float, mval: float) -> None:
        nonlocal treat_step_num
        treat_step_num += 1
        row = blank_row()
        row["measurement"] = measurement_name
        row["experiment"] = experiment
        row["specimen"] = specimen
        row["instrument_codes"] = instrument_codes
        row["citations"] = citations
        row["analysts"] = analysts
        # MagIC uses sequence to preserve measurement order.  Populating it also
        # lets the importer distinguish repeated experiments whose sequence
        # restarts within one specimen.
        row["sequence"] = str(treat_step_num)
        row["standard"] = "u"
        row["quality"] = "g"
        row["method_codes"] = "LP-FORC"
        row["treat_step_num"] = str(treat_step_num)
        row["meas_temp"] = "" if meas_temp_k is None else f"{float(meas_temp_k):.12g}"
        # 17 significant digits round-trip a double exactly, so archiving the
        # measurements loses nothing relative to the instrument file.
        row["meas_field_dc"] = f"{float(hval):.17g}"
        # The VSM reports a calibrated moment, so it belongs in magn_moment;
        # magn_uncal is reserved for uncalibrated instrument units.
        row["magn_moment"] = f"{float(mval):.17g}"
        row["timestamp"] = timestamp
        row["files"] = source_file
        rows.append(row)

    block_num = 0
    i = 0
    while i < len(groups):
        cal_group = groups[i]
        if len(cal_group) == 0:
            i += 1
            continue

        block_num += 1

        # calibration group: write every row as block-0 if somehow more than one point,
        # but in normal files this should be exactly one row.
        for k, (h, m) in enumerate(cal_group):
            if k == 0:
                append_row(f"{experiment}-{block_num}-0", h, m)
            else:
                # defensive fallback: additional rows in the calibration group
                append_row(f"{experiment}-{block_num}-{k}", h, m)

        if i + 1 < len(groups):
            forc_group = groups[i + 1]
            for j, (h, m) in enumerate(forc_group, start=1):
                append_row(f"{experiment}-{block_num}-{j}", h, m)
            i += 2
        else:
            i += 1

    return rows

def export_magic_measurements_from_raw(
    path: PathLike,
    data_start_idx: Optional[int] = None,
    meas_temp_k: Optional[float] = None,
    out_dir: Optional[PathLike] = None,
    filename: Optional[str] = None,
    **row_metadata,
) -> Path:
    """Write the raw FORC measurements as a MagIC measurements table.

    The raw file is reparsed into its blank-line-delimited calibration and
    curve groups, so the export does not depend on the segmentation used for
    the distribution calculation. Calibration measurements are preserved,
    since the drift correction depends on them.

    Args:
        path: Raw MicroMag FORC file to convert.
        data_start_idx: Index of the first data line. Inferred when None.
        meas_temp_k: Measurement temperature in kelvin, written to
            ``meas_temp`` when available.
        out_dir: Directory to write into. Defaults to a ``MagIC``
            subdirectory beside the input file.
        filename: Output file name. Defaults to ``<stem>_measurements.txt``.
        **row_metadata: Passed to :func:`build_magic_rows_from_raw_groups`,
            for example ``specimen``, ``experiment``, ``instrument_codes``,
            ``citations``, ``analysts`` or ``timestamp``.

    Returns:
        Path to the written measurements table.
    """
    p = as_path(path)
    out_dir = (p.parent / "MagIC") if out_dir is None else as_path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / safe_filename(
        filename or f"{_magic_basename(path)}_measurements.txt")

    groups = _read_numeric_groups_by_blanklines(path, data_start_idx=data_start_idx)
    rows = build_magic_rows_from_raw_groups(path, groups, meas_temp_k=meas_temp_k,
                                            **row_metadata)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        # The "tab delimited" preamble is what makes the file a MagIC table
        # that pmag.magic_read / ipmag.unpack_magic can ingest directly.
        writer.writerow(["tab delimited", "measurements"])
        writer.writerow(MAGIC_MEASUREMENT_HEADERS)
        for row in rows:
            writer.writerow([row.get(h, "") for h in MAGIC_MEASUREMENT_HEADERS])

    return out_path


# ============================================================
# MagIC measurement import
# ============================================================

_MAGIC_BLOCK_POINT_RE = re.compile(r"-(\d+)-(\d+)$")
_MAGIC_MOMENT_FIELDS = ("magn_moment", "magn_uncal", "magn_mass", "magn_volume")


def _magic_float(value) -> Optional[float]:
    """Return a finite float for a MagIC cell, otherwise None."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return number if np.isfinite(number) else None


def _iter_magic_forc_rows(path: PathLike):
    """Yield normalized LP-FORC rows from a MagIC tab-delimited table."""
    p = as_path(path)
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        headers = None
        for values in reader:
            cleaned = [str(v).strip().lstrip("\ufeff") for v in values]
            if "specimen" in cleaned and "sequence" in cleaned and "meas_field_dc" in cleaned:
                headers = cleaned
                break
        if headers is None:
            raise ValueError(
                "Could not find a MagIC measurements header containing specimen, "
                "sequence, and meas_field_dc."
            )

        for source_order, values in enumerate(reader):
            if not values or not any(str(v).strip() for v in values):
                continue
            if len(values) < len(headers):
                values += [""] * (len(headers) - len(values))
            row = {h: values[i].strip() for i, h in enumerate(headers) if h and i < len(values)}
            method_text = ":".join((row.get("method_codes", ""), row.get("experiment", ""), row.get("measurement", ""))).upper()
            if "LP-FORC" not in method_text:
                continue

            field = _magic_float(row.get("meas_field_dc"))
            moment = None
            for name in _MAGIC_MOMENT_FIELDS:
                candidate = _magic_float(row.get(name))
                if candidate is not None:
                    moment = candidate
                    break
            if field is None or moment is None:
                continue

            measurement = row.get("measurement", "")
            match = _MAGIC_BLOCK_POINT_RE.search(measurement)
            row["_field"] = field
            row["_moment"] = moment
            row["_source_order"] = source_order
            row["_block"] = int(match.group(1)) if match else None
            row["_point"] = int(match.group(2)) if match else None
            yield row


def read_magic_forc_runs(path: PathLike) -> List[Dict[str, object]]:
    """
    Read a MagIC measurements table and split its LP-FORC data into runs.

    Runs are separated by specimen, experiment changes, sequence restarts, or
    (for legacy tables with blank sequence) a restart of the measurement block
    number.  Each returned item contains ``specimen``, ``experiment``, ``rows``,
    and a stable ``run_id``.
    """
    by_specimen: Dict[str, List[Dict[str, object]]] = {}
    current: Dict[str, Dict[str, object]] = {}

    for row in _iter_magic_forc_rows(path):
        specimen = row.get("specimen", "").strip() or "unknown_specimen"
        experiment = row.get("experiment", "").strip()
        sequence = _magic_float(row.get("sequence"))
        block = row.get("_block")
        previous = current.get(specimen)

        new_run = previous is None
        if previous is not None:
            previous_experiment = str(previous["experiment"])
            previous_sequence = previous.get("_last_sequence")
            previous_block = previous.get("_last_block")
            if experiment and previous_experiment and experiment != previous_experiment:
                new_run = True
            elif sequence is not None and previous_sequence is not None and sequence <= previous_sequence:
                new_run = True
            elif sequence is None and block is not None and previous_block is not None and block < previous_block:
                new_run = True

        if new_run:
            run_number = len(by_specimen.setdefault(specimen, [])) + 1
            repeated_experiment = bool(experiment) and any(
                str(item.get("experiment", "")) == experiment for item in by_specimen[specimen]
            )
            run_id = (
                f"{experiment}#{run_number}" if repeated_experiment
                else experiment or f"{specimen}-run-{run_number}"
            )
            run = {
                "specimen": specimen,
                "experiment": experiment,
                "run_id": run_id,
                "rows": [],
                "_last_sequence": None,
                "_last_block": None,
            }
            by_specimen[specimen].append(run)
            current[specimen] = run
        else:
            run = previous

        run["rows"].append(row)
        if sequence is not None:
            run["_last_sequence"] = sequence
        if block is not None:
            run["_last_block"] = block

    runs = [run for specimen_runs in by_specimen.values() for run in specimen_runs]
    if not runs:
        raise ValueError(f"No readable LP-FORC measurements found in MagIC file: {path}")
    for run in runs:
        run.pop("_last_sequence", None)
        run.pop("_last_block", None)
    return runs


def _write_magic_run_as_forc(run: Dict[str, object], path: PathLike) -> Path:
    """Write one parsed MagIC run in the small raw format used by the core pipeline."""
    rows = list(run["rows"])
    parsed_blocks: Dict[int, List[dict]] = {}
    for row in rows:
        if row.get("_block") is not None:
            parsed_blocks.setdefault(int(row["_block"]), []).append(row)

    blocks: List[Tuple[Optional[dict], List[dict]]] = []
    if parsed_blocks:
        for block_number in sorted(parsed_blocks):
            block_rows = sorted(parsed_blocks[block_number], key=lambda r: r["_source_order"])
            cal = next((r for r in block_rows if r.get("_point") == 0), None)
            forc = [r for r in block_rows if r.get("_point") != 0]
            if forc:
                blocks.append((cal, forc))
    else:
        # Fallback for non-standard measurement names: increasing field belongs
        # to one curve; a decrease starts the next curve.
        curves: List[List[dict]] = []
        for row in rows:
            if curves and row["_field"] < curves[-1][-1]["_field"]:
                curves.append([])
            elif not curves:
                curves.append([])
            curves[-1].append(row)
        blocks = [(None, curve) for curve in curves if curve]

    if not blocks:
        raise ValueError(f"MagIC run {run['run_id']!r} contains no FORC curves.")

    all_fields = [float(r["_field"]) for _, curve in blocks for r in curve]
    hb_values = [min(float(r["_field"]) for r in curve) for _, curve in blocks]
    max_abs_field = max(abs(v) for v in all_fields) or 1.0
    hcal_values = [float(cal["_field"]) for cal, _ in blocks if cal is not None]
    hcal = float(np.median(hcal_values)) if hcal_values else max(all_fields)
    synthetic_cal_moment = float(blocks[0][1][-1]["_moment"])
    hb2 = max(abs(v) for v in hb_values) if hb_values else max_abs_field
    hc2 = max_abs_field

    out_path = ensure_parent_dir(path)
    lines = [
        f"HCal {hcal:.17g}",
        f"Hb2 {hb2:.17g}",
        f"Hc2 {hc2:.17g}",
        "Field (T), Moment (A m^2)",
    ]
    for cal, curve in blocks:
        if cal is None:
            # One synthetic calibration point permits safe segmentation but is
            # intentionally constant, so drift correction remains zero.
            cal_field, cal_moment = hcal, synthetic_cal_moment
        else:
            cal_field, cal_moment = float(cal["_field"]), float(cal["_moment"])
        lines.append(f"{cal_field:.17g}, {cal_moment:.17g}")
        lines.extend(f"{float(r['_field']):.17g}, {float(r['_moment']):.17g}" for r in curve)
        lines.extend(("", ""))
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path

# ============================================================
# File reading / header parsing
# ============================================================

def _read_text_normalized(path: PathLike, encoding: str = "utf-8") -> str:
    """Read file robustly; normalize \r\n and \r into \n."""
    p = as_path(path)

    raw = p.read_bytes()
    try:
        txt = raw.decode(encoding, errors="replace")
    except Exception:
        txt = raw.decode("latin-1", errors="replace")
    return txt.replace("\r\n", "\n").replace("\r", "\n")

def _is_numeric_line(line: str) -> bool:
    return _NUM_LINE.match(line) is not None

def _parse_numeric_line(line: str) -> Tuple[float, float]:
    m = _NUM_LINE.match(line)
    if m is None:
        raise ValueError(f"Not a numeric line: {line!r}")
    return float(m.group(1)), float(m.group(2))


def _parse_first_two_numeric_columns(line: str) -> Optional[Tuple[float, float]]:
    """
    Parse the first two comma-separated numeric columns from a data row.

    Standard and most multi-segment files have two columns:
        Field, Moment

    Some temperature-controlled MicroMag exports have three columns:
        Field, Moment, Temperature

    FORC processing only needs Field and Moment, so this helper accepts
    either two or more comma-separated numeric columns and ignores extras.
    """
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) < 2:
        return None

    if re.fullmatch(_FLOAT, parts[0]) is None:
        return None
    if re.fullmatch(_FLOAT, parts[1]) is None:
        return None

    try:
        return float(parts[0]), float(parts[1])
    except Exception:
        return None


def _is_numeric_data_row_2plus(line: str) -> bool:
    """True for numeric rows with at least Field and Moment columns."""
    return _parse_first_two_numeric_columns(line) is not None


# Field and moment are carried internally in tesla and A m^2. MicroMag writes
# either SI or cgs depending on the "Units of measure" setting, and older
# exports (Series 0015, the vintage FORCinel was written against) default to
# cgs. Reading a cgs file as SI would introduce silent factors of 10^4 and
# 10^3, so the units are resolved explicitly and cross-checked against the
# magnitude of the data.
_OERSTED_TO_TESLA = 1.0e-4
_EMU_TO_AM2 = 1.0e-3


def read_file_units(path: PathLike) -> Dict[str, object]:
    """Resolve the field and moment units of a MicroMag FORC export.

    Args:
        path: File to inspect.

    Returns:
        dict: ``field_scale`` and ``moment_scale`` multipliers that convert the
        file's numbers to tesla and A m^2, the ``field_unit`` and
        ``moment_unit`` labels, and ``source`` recording how the units were
        determined (``"units line"``, ``"column header"`` or ``"assumed SI"``).
    """
    lines = _read_text_normalized(path).split("\n")

    for line in lines[:80]:
        low = line.lower()
        if "units of measure" in low:
            value = low.split("units of measure", 1)[1].lstrip(" \t:")
            if "cgs" in value:
                return {"field_scale": _OERSTED_TO_TESLA, "moment_scale": _EMU_TO_AM2,
                        "field_unit": "Oe", "moment_unit": "emu", "source": "units line"}
            # "SI" and Lake Shore's "SiMuNaughtH" both write tesla and A m^2.
            if "si" in value:
                return {"field_scale": 1.0, "moment_scale": 1.0,
                        "field_unit": "T", "moment_unit": "A m^2", "source": "units line"}
        # Column-unit line, e.g. "    (T)          (Am2)"
        if "(T)" in line and ("Am" in line or "A m" in line):
            return {"field_scale": 1.0, "moment_scale": 1.0,
                    "field_unit": "T", "moment_unit": "A m^2", "source": "column header"}

    return {"field_scale": 1.0, "moment_scale": 1.0,
            "field_unit": "T", "moment_unit": "A m^2", "source": "assumed SI"}


def _check_field_magnitude(max_abs_field_T: float, units: Dict[str, object], path: PathLike) -> None:
    """Guard against reading a cgs file as SI.

    Laboratory FORC measurements do not reach tens of tesla, so a field range
    that large after conversion means the units were misidentified.

    Raises:
        ValueError: If the converted field range is physically implausible.
    """
    if np.isfinite(max_abs_field_T) and max_abs_field_T > 30.0:
        raise ValueError(
            f"Field values in {as_path(path).name} reach {max_abs_field_T:.4g} T after "
            f"conversion assuming {units['field_unit']} ({units['source']}). That is not a "
            "plausible laboratory field; the file is most likely in cgs (Oe/emu) but was "
            "not recognized as such. Check the 'Units of measure' line."
        )


def read_header_tags_and_data_start(path: PathLike) -> tuple[dict, int]:
    """Parse the scalar header tags and locate the start of the data section.

    Handles both MicroMag header styles, ``Name<whitespace>value`` used by
    current Lake Shore exports and ``Name = value`` used by older Series 0015
    files. Numeric tags are converted to tesla where they are fields, so
    downstream code always sees SI.

    Args:
        path: FORC file to read.

    Returns:
        tuple: ``(tags, data_start_idx)`` where ``tags`` maps header names such
        as ``"HCal"`` and ``"Hb2"`` to floats in tesla, and ``data_start_idx``
        is the index of the first data line.

    Raises:
        ValueError: If no numeric data section can be located.
    """
    lines = _read_text_normalized(path).split("\n")
    units = read_file_units(path)
    field_scale = float(units["field_scale"])

    # Header names that carry a field value and therefore need unit conversion.
    field_tags = {"hcal", "hsat", "hncr", "hb1", "hb2", "hc1", "hc2",
                  "field range", "slewrate"}

    tags: Dict[str, float] = {}
    data_start_idx: Optional[int] = None

    for i, line in enumerate(lines):
        s = line.strip()
        if not s:
            continue

        m = _TAG_LINE.match(s)
        if m:
            name = re.sub(r"\s+", " ", m.group(1)).strip()
            value = float(m.group(2))
            tags[name] = value * field_scale if name.lower() in field_tags else value
            continue

        if "(T)" in line or ("Field" in line and "Moment" in line):
            data_start_idx = i + 1
            break

    if data_start_idx is None:
        # Older exports carry neither a units line nor a Field/Moment header;
        # the data simply begin after the last header tag.
        for i, line in enumerate(lines):
            if _is_numeric_data_row_2plus(line.strip()):
                data_start_idx = i
                break

    if data_start_idx is None:
        raise ValueError(
            f"Could not find a numeric data section in {as_path(path).name}. Expected a "
            "units line containing '(T)', a 'Field'/'Moment' column header, or "
            "comma-separated numeric rows."
        )

    return tags, data_start_idx

def read_forc_header_limits(path: PathLike) -> Tuple[Optional[float], Optional[float]]:
    """Read the FORC diagram display limits recorded in the file header.

    MicroMag stores the intended plotting window of the FORC diagram as
    ``Hb1``/``Hb2`` on the bias axis and ``Hc1``/``Hc2`` on the coercivity
    axis. Despite the tag names these are display bounds in ``Bu`` and ``Bc``,
    not reversal or applied fields.

    Args:
        path: FORC file to read.

    Returns:
        tuple: ``(Bu_max, Bc_max)`` in tesla, either of which may be None when
        the header does not record it. For multi-segment files, which carry no
        such tags, approximate values are inferred from the script table.
    """
    Bu_max = None
    Bc_max = None

    try:
        tags, _ = read_header_tags_and_data_start(path)
    except ValueError:
        tags = {}
    if "Hb2" in tags:
        Bu_max = float(tags["Hb2"])
    if "Hc2" in tags:
        Bc_max = float(tags["Hc2"])

    if Bu_max is not None or Bc_max is not None:
        return Bu_max, Bc_max

    hdr_Bu_max = Bu_max
    hdr_Bc_max = Bc_max

    if is_multi_segment_forc_file(path):
        try:
            HCal, HSat, _, _, _ = infer_multi_segment_metadata(path)
            if HSat is not None:
                hdr_Bu_max = float(abs(HSat))
                hdr_Bc_max = float(abs(HSat))
            elif HCal is not None:
                hdr_Bu_max = float(abs(HCal))
                hdr_Bc_max = float(abs(HCal))
        except Exception:
            pass

    return hdr_Bu_max, hdr_Bc_max


def is_multi_segment_forc_file(path: PathLike) -> bool:
    """Return True when the file is a MicroMag multi-segment export."""
    txt = _read_text_normalized(path)
    lines = txt.split("\n")
    if len(lines) < 2:
        return False
    return lines[1].strip() == "Direct moment vs. field; Multiple segments"


def _find_multi_segment_data_start(lines: List[str]) -> int:
    """
    Find the first numeric data row after the actual two-column
    "Field / Moment" header that follows the SCRIPT table.
    """
    header_idx = None
    for i, line in enumerate(lines):
        if ("Field" in line) and ("Moment" in line):
            header_idx = i

    if header_idx is None:
        raise ValueError("Could not find the Field/Moment header in the multi-segment file.")

    for i in range(header_idx + 1, len(lines)):
        s = lines[i].strip()
        if _is_numeric_data_row_2plus(s):
            return i

    raise ValueError("Could not find the numeric data section for the multi-segment FORC file.")


def read_multi_segment_script(path: PathLike) -> List[Dict[str, float]]:
    """Parse the SCRIPT table from a multi-segment MicroMag export."""
    txt = _read_text_normalized(path)
    lines = txt.split("\n")

    seg_re = re.compile(
        rf"^\s*(\d+)\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*({_FLOAT})\s*,\s*(\d+)\s*$"
    )

    script: List[Dict[str, float]] = []
    prev_fidx = 0

    for line in lines:
        m = seg_re.match(line.strip())
        if not m:
            continue

        final_index = int(m.group(7))
        npts = final_index - prev_fidx
        prev_fidx = final_index

        script.append({
            "num": int(m.group(1)),
            "avg": float(m.group(2)),
            "init": float(m.group(3)),
            "inc": float(m.group(4)),
            "final": float(m.group(5)),
            "pause": float(m.group(6)),
            "final_index": final_index,
            "npts": int(npts),
        })

    if not script:
        raise ValueError("Could not parse the SCRIPT table from the multi-segment file.")

    return script


def infer_multi_segment_metadata(path: PathLike) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float], List[Dict[str, float]]]:
    """
    Infer useful metadata from the multi-segment script:
      HCal, HSat, Ha_min, Ha_max, script_rows
    """
    script = read_multi_segment_script(path)

    HCal = None
    HSat = None

    cal_fields = [row["init"] for row in script if row["npts"] == 1 and abs(row["init"] - row["final"]) <= 1e-12]
    if cal_fields:
        # Use the most common single-point field as the calibration field.
        vals, counts = np.unique(np.round(np.asarray(cal_fields, float), 9), return_counts=True)
        HCal = float(vals[np.argmax(counts)])

    forc_hb = [row["init"] for row in script if row["npts"] >= 2]

    # A robust approximate saturation / maximum field for default plot limits.
    # In the evenly spaced moment variant, many measured FORC subsegments end
    # well below the saturation/calibration field, so the median final field is
    # not a good estimate. Use the maximum absolute scripted field instead.
    scripted_fields = []
    for row in script:
        scripted_fields.append(float(row["init"]))
        scripted_fields.append(float(row["final"]))
    if scripted_fields:
        HSat = float(np.nanmax(np.abs(np.asarray(scripted_fields, float))))

    Ha_min = float(np.nanmin(forc_hb)) if forc_hb else None
    Ha_max = float(np.nanmax(forc_hb)) if forc_hb else None

    return HCal, HSat, Ha_min, Ha_max, script


def read_multi_segment_segments(
    path: PathLike,
    dtype=np.float64,
    cal_tol_T: float = 2e-3,
    verbose: bool = True,
) -> List[Segment]:
    """
    Read a multi-segment FORC file and return calibration points and FORC
    curves as Segment objects.

    This parser handles both multi-segment styles:

      A) FORC data stored as one longer measured row/segment after each calibration.
      B) FORC data stored as many short measured rows/segments, with:
           calibration point:       inc = 0, npts = 1, field ≈ HCal
           ramp to reversal field:  npts = 0
           reversal-field point:    inc = 0, npts = 1, field != HCal
           FORC measured segments:  npts >= 1, usually npts = 2

    The SCRIPT table's cumulative Final Index is used to slice the numeric
    data section. Leading setup / major-loop data are ignored until the first
    calibration point is reached.
    """
    txt = _read_text_normalized(path)
    lines = txt.split("\n")
    data_start_idx = _find_multi_segment_data_start(lines)

    data_rows: List[Tuple[float, float]] = []
    for line in lines[data_start_idx:]:
        s = line.strip()
        parsed = _parse_first_two_numeric_columns(s)
        if parsed is not None:
            data_rows.append(parsed)

    if not data_rows:
        raise ValueError("No numeric field/moment data were found in the multi-segment file.")

    HCal, HSat, Ha_min, Ha_max, script = infer_multi_segment_metadata(path)
    if HCal is None:
        raise ValueError("Could not infer calibration field from the multi-segment SCRIPT table.")

    segments: List[Segment] = []
    cursor = 0
    next_idx = 0
    started = False

    current_H: List[float] = []
    current_M: List[float] = []
    current_Ha: Optional[float] = None

    def close_current_forc() -> None:
        nonlocal current_H, current_M, current_Ha, next_idx

        if len(current_H) >= 2:
            Ha = current_Ha
            if Ha is None or not np.isfinite(Ha):
                Ha = float(np.nanmin(np.asarray(current_H, float)))

            segments.append(Segment(
                H=np.asarray(current_H, dtype=dtype),
                M=np.asarray(current_M, dtype=dtype),
                idx=next_idx,
                kind="forc",
                Ha=float(Ha),
            ))
            next_idx += 1

        current_H = []
        current_M = []
        current_Ha = None

    for row in script:
        npts = int(row["npts"])
        if npts < 0:
            raise ValueError(f"Negative point count encountered in SCRIPT row {row['num']}")
        if npts == 0:
            # Usually a non-measured ramp, commonly from HCal down to the next Ha.
            continue

        block = data_rows[cursor:cursor + npts]
        cursor += npts

        if len(block) != npts:
            raise ValueError(
                f"SCRIPT/data mismatch in multi-segment file near segment {row['num']}: "
                f"expected {npts} point(s), found {len(block)}."
            )

        H_block = [float(x) for x, _ in block]
        M_block = [float(y) for _, y in block]

        is_zero_increment = abs(float(row["inc"])) <= 1e-15
        is_single_point = npts == 1
        is_stationary = abs(float(row["init"]) - float(row["final"])) <= 1e-12

        # Both calibration points and reversal-field points are usually
        # zero-increment, single-point, stationary rows. Distinguish them
        # using the modal calibration field.
        is_zero_single = is_zero_increment and is_single_point and is_stationary
        is_calibration = is_zero_single and abs(float(row["init"]) - float(HCal)) <= float(cal_tol_T)

        if is_calibration:
            # A calibration point marks the start of a new FORC cycle.
            # If a previous FORC is active, close it first.
            close_current_forc()

            segments.append(Segment(
                H=np.asarray(H_block, dtype=dtype),
                M=np.asarray(M_block, dtype=dtype),
                idx=next_idx,
                kind="cal",
                Ha=None,
            ))
            next_idx += 1
            started = True
            continue

        if not started:
            # Ignore leading setup / major-loop measurements before the first
            # recognized calibration point.
            continue

        if is_zero_single:
            # Non-calibration zero-increment single-point rows are reversal-field
            # measurements. They start a new FORC and should be retained as the
            # first point of that FORC.
            close_current_forc()
            current_H = H_block.copy()
            current_M = M_block.copy()
            current_Ha = float(H_block[0])
            continue

        # Measured FORC segment. In the evenly spaced moment version these are
        # often two measured points at a time; in the older multi-segment version
        # this may be one long segment.
        if current_Ha is None:
            current_Ha = float(np.nanmin(np.asarray(H_block, float)))

        current_H.extend(H_block)
        current_M.extend(M_block)

    close_current_forc()

    if cursor != len(data_rows):
        raise ValueError(
            f"Not all numeric data were consumed in the multi-segment parser: "
            f"used {cursor}, total {len(data_rows)}."
        )

    if verbose:
        n_cal = sum(s.kind == "cal" for s in segments)
        n_forc = sum(s.kind == "forc" for s in segments)
        forc_lens = [len(s.H) for s in segments if s.kind == "forc"]
        if forc_lens:
            print(
                f"Multi-segment FORC detected | cal field≈{HCal:.6g} T | "
                f"sat field≈{HSat:.6g} T | Ha≈{Ha_min:.6g}→{Ha_max:.6g} T | "
                f"cal points={n_cal} | FORCs={n_forc} | "
                f"FORC length min/median/max={min(forc_lens)}/{int(np.median(forc_lens))}/{max(forc_lens)}"
            )
        else:
            print(
                f"Multi-segment FORC detected | cal field≈{HCal:.6g} T | "
                f"cal points={n_cal} | FORCs={n_forc}"
            )

    return segments

def read_segments_raw(
    path: PathLike,
    data_start_idx: Optional[int] = None,
    dtype=np.float64,
    min_block_len: int = 2,
    # segmentation knobs:
    blank_sep: int = 2,          # >=2 consecutive blanks before a numeric line => new block
    jump_T: float = 0.05,        # if previous H - current H > jump_T => new block
    # calibration-start pattern:
    HCal: Optional[float] = None,
    cal_tol_T: float = 2e-3,
    cal_drop_T: float = 0.02,
    verbose: bool = True,
) -> List[Segment]:
    """Read the numeric rows of a FORC file and split them into blocks.

    Blocks are separated by whichever of three signals the export provides:
    runs of blank lines (the macOS-style layout), a large downward jump in
    field (the compact Windows-style layout), or the calibration-start pattern
    of a point near ``HCal`` followed by a large drop.

    Rows may carry a third column (temperature on some MicroMag exports);
    only the first two, field and moment, are used. Values are converted to
    tesla and A m^2 from the units declared in the file header.

    Args:
        path: FORC file to read.
        data_start_idx: Index of the first data line. Inferred when None.
        dtype: Floating-point type for the stored arrays.
        min_block_len: Blocks shorter than this are discarded.
        blank_sep: Number of consecutive blank lines that starts a new block.
        jump_T: Downward field step, in tesla, that starts a new block.
        HCal: Calibration field in tesla, enabling the third split rule.
        cal_tol_T: Tolerance for matching a point to ``HCal``.
        cal_drop_T: Field drop after a calibration point that confirms the
            start of a new curve.
        verbose: Print a one-line summary of the segmentation.

    Returns:
        The parsed segments, before calibration/FORC classification.
    """
    txt = _read_text_normalized(path)
    lines = txt.split("\n")

    if data_start_idx is None:
        _, data_start_idx = read_header_tags_and_data_start(path)

    units = read_file_units(path)
    field_scale = float(units["field_scale"])
    moment_scale = float(units["moment_scale"])

    # collect numeric rows with "how many blank lines preceded it"
    rows: List[Tuple[float, float, int]] = []  # (H, M, blanks_before)
    blank_run = 0

    for line in lines[data_start_idx:]:
        s = line.strip()
        if s == "":
            blank_run += 1
            continue
        parsed = _parse_first_two_numeric_columns(s)
        if parsed is not None:
            h, m = parsed
            rows.append((h * field_scale, m * moment_scale, blank_run))
        blank_run = 0

    if rows:
        _check_field_magnitude(max(abs(r[0]) for r in rows), units, path)

    segments: List[Segment] = []
    cur_H: List[float] = []
    cur_M: List[float] = []

    def close_block():
        nonlocal cur_H, cur_M
        # An isolated point sitting at the calibration field is a calibration
        # measurement, not a short curve. These are single points, so dropping
        # everything below min_block_len would discard the whole drift record:
        # in MicroMag exports that separate every reading with a blank line,
        # each calibration point forms a one-row block.
        is_isolated_cal = (
            len(cur_H) == 1
            and HCal is not None
            and abs(float(cur_H[0]) - float(HCal)) <= float(cal_tol_T)
        )
        if len(cur_H) >= min_block_len or is_isolated_cal:
            segments.append(Segment(
                H=np.asarray(cur_H, dtype=dtype),
                M=np.asarray(cur_M, dtype=dtype),
                idx=len(segments),
                kind="cal" if is_isolated_cal else "unknown",
            ))
        cur_H, cur_M = [], []

    n = len(rows)
    for i in range(n):
        h, m, blanks = rows[i]
        next_h = rows[i + 1][0] if (i + 1 < n) else None

        # Rule 1: blank separator
        if blanks >= blank_sep and cur_H:
            close_block()

        # Rule 2: big downward jump in H => reset => new block
        if cur_H:
            prev_h = cur_H[-1]
            if np.isfinite(prev_h) and np.isfinite(h):
                if (prev_h - h) > float(jump_T):
                    close_block()

        # Rule 3: calibration-start pattern (optional)
        if (HCal is not None) and (next_h is not None) and cur_H:
            if abs(float(h) - float(HCal)) <= float(cal_tol_T):
                if (float(h) - float(next_h)) >= float(cal_drop_T):
                    close_block()

        cur_H.append(h)
        cur_M.append(m)

    close_block()

    if verbose:
        if segments:
            curves = [len(s.H) for s in segments if s.kind != "cal"]
            n_cal = sum(1 for s in segments if s.kind == "cal")
            if curves:
                print(
                    f"Parsed {len(curves)} curve blocks and {n_cal} calibration points | "
                    f"curve length min/median/max = "
                    f"{min(curves)}/{int(np.median(curves))}/{max(curves)}"
                )
            else:
                print(f"Parsed 0 curve blocks and {n_cal} calibration points")
        else:
            print("Parsed 0 segments")

    return segments

def split_cal_first_point(
    segments: List[Segment],
    HCal: float,
    tol_T: float = 2e-3
) -> List[Segment]:
    """
    Split ONLY when the FIRST point of a block is at ~HCal:
      [cal] = first point
      [forc] = remaining points
    """
    out: List[Segment] = []
    next_idx = 0

    for s in segments:
        H = np.asarray(s.H, float)
        M = np.asarray(s.M, float)

        if H.size >= 2 and abs(float(H[0]) - float(HCal)) <= float(tol_T):
            out.append(Segment(H=np.array([H[0]]), M=np.array([M[0]]),
                               idx=next_idx, kind="cal"))
            next_idx += 1

            Ha = float(np.nanmin(H[1:])) if H[1:].size else None
            out.append(Segment(H=H[1:].copy(), M=M[1:].copy(),
                               idx=next_idx, kind="forc", Ha=Ha))
            next_idx += 1
        else:
            kind = "forc" if H.size > 1 else "cal"
            Ha = float(np.nanmin(H)) if (kind == "forc") else None
            out.append(Segment(H=H.copy(), M=M.copy(),
                               idx=next_idx, kind=kind, Ha=Ha))
            next_idx += 1

    return out

# ============================================================
# Drift correction + conditioning
# ============================================================

def compute_drift_from_cals(
    segments: List[Segment],
    fit: str = "linear"
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns drift_at_seg, cal_pos, cal_M."""
    cal_segs = [s for s in segments if s.kind == "cal"]
    if len(cal_segs) < 2:
        kinds: Dict[str, int] = {}
        for s in segments:
            kinds[s.kind] = kinds.get(s.kind, 0) + 1
        raise ValueError(f"Need >=2 calibration points; found {len(cal_segs)}. Kind counts: {kinds}.")

    cal_pos = np.array([float(s.idx) for s in cal_segs], dtype=float)
    cal_M = np.array([float(s.M[0]) for s in cal_segs], dtype=float)
    drift = cal_M - cal_M[0]

    seg_pos = np.array([float(s.idx) for s in segments], dtype=float)

    if fit == "linear":
        drift_at_seg = np.interp(seg_pos, cal_pos, drift)
    elif fit == "pchip":
        from scipy.interpolate import PchipInterpolator
        drift_at_seg = PchipInterpolator(cal_pos, drift)(seg_pos)
    else:
        raise ValueError("fit must be 'linear' or 'pchip'.")
    return drift_at_seg, cal_pos, cal_M

def apply_drift_correction(segments: List[Segment], drift_at_seg: np.ndarray) -> List[Segment]:
    out: List[Segment] = []
    for i, seg in enumerate(segments):
        d = float(drift_at_seg[i])
        out.append(Segment(
            H=seg.H.copy(),
            M=seg.M - d,
            idx=seg.idx,
            kind=seg.kind,
            Ha=seg.Ha,
        ))
    return out

def replace_endpoints(seg: Segment, n: int = 1, replace_first: bool = True, replace_last: bool = True) -> Segment:
    """Replace first and/or last n points with linear extrapolation from interior."""
    H = seg.H.copy()
    M = seg.M.copy()
    if len(H) < 4 or n <= 0:
        return seg

    if replace_first:
        for k in range(min(n, len(H) - 3)):
            x1, y1 = H[k + 1], M[k + 1]
            x2, y2 = H[k + 2], M[k + 2]
            if x2 != x1:
                slope = (y2 - y1) / (x2 - x1)
                M[k] = y1 + slope * (H[k] - x1)

    if replace_last:
        for k in range(1, min(n, len(H) - 3) + 1):
            x1, y1 = H[-k - 1], M[-k - 1]
            x2, y2 = H[-k - 2], M[-k - 2]
            if x1 != x2:
                slope = (y1 - y2) / (x1 - x2)
                M[-k] = y1 + slope * (H[-k] - x1)

    return Segment(H=H, M=M, idx=seg.idx, kind=seg.kind, Ha=seg.Ha)

def select_reference_curve(forcs: List[Segment], reference: str = "lowest_reversal") -> Segment:
    """Choose the curve to subtract as a baseline from the FORC family.

    Args:
        forcs: FORC segments to choose from.
        reference: ``"lowest_reversal"`` selects the curve with the most
            negative reversal field, which spans the widest field range and is
            the closest measured approximation to the lower branch of the
            major hysteresis loop. ``"first_measured"`` selects the curve
            measured first, which for MicroMag files is the curve at the
            *highest* reversal field and typically only a few points long.

    Returns:
        The selected reference segment.

    Raises:
        ValueError: If ``forcs`` is empty or ``reference`` is unrecognized.
    """
    if not forcs:
        raise ValueError("No FORC segments supplied.")
    if reference == "lowest_reversal":
        return min(forcs, key=lambda s: float(s.Ha) if s.Ha is not None
                   else float(np.nanmin(s.H)))
    if reference == "first_measured":
        return forcs[0]
    raise ValueError("reference must be 'lowest_reversal' or 'first_measured'.")


def subtract_reference_curve(
    segments: List[Segment],
    reference: str = "lowest_reversal",
) -> List[Segment]:
    """Subtract a reference reversal curve from every FORC in the family.

    This aids visual inspection of the curves by removing the common
    reversible/high-field signal. It does not change the FORC distribution: the
    subtracted baseline is a function of the applied field alone, so it
    vanishes under the mixed derivative with respect to ``Hb`` and ``Ha``.

    Curves are only altered over the applied-field range the reference curve
    actually spans; outside that range the result is set to NaN rather than
    silently clamped to the reference endpoints.

    Args:
        segments: All segments, including calibration points, which pass
            through unchanged.
        reference: Reference curve selection, see
            :func:`select_reference_curve`.

    Returns:
        A new list of segments with the reference subtracted from each FORC.
    """
    forcs = [s for s in segments if s.kind == "forc"]
    if not forcs:
        return segments

    base = select_reference_curve(forcs, reference=reference)
    ok = np.isfinite(base.H) & np.isfinite(base.M)
    base_H, base_M = base.H[ok], base.M[ok]
    order = np.argsort(base_H)
    base_H, base_M = base_H[order], base_M[order]

    out: List[Segment] = []
    for seg in segments:
        if seg.kind != "forc":
            out.append(seg)
            continue
        baseline = np.interp(seg.H, base_H, base_M, left=np.nan, right=np.nan)
        out.append(Segment(H=seg.H.copy(), M=seg.M - baseline,
                           idx=seg.idx, kind=seg.kind, Ha=seg.Ha))
    return out

#   Regridding FORCs onto a regular B grid

def infer_B_step_from_forcs(forcs):
    """
    Robustly infer a typical B step from many FORC segments.
    Uses the median of finite, positive |dB| values.
    """
    import numpy as np
    dB_all = []
    for s in forcs:
        if getattr(s, "kind", None) != "forc":
            continue
        B = np.asarray(s.H, float)  # your code uses H for field in T
        ok = np.isfinite(B)
        B = B[ok]
        if B.size < 3:
            continue
        dB = np.abs(np.diff(B))
        dB = dB[np.isfinite(dB) & (dB > 0)]
        if dB.size:
            dB_all.append(dB)
    if not dB_all:
        return None
    dB = np.median(np.concatenate(dB_all))
    # Optionally "round" to a nice number (e.g., 1e-3 T) if it’s close
    return float(dB)

def regrid_segment_BM(seg, B_grid, method="linear", extrapolate=False):
    """
    Interpolate seg.M(seg.H) onto a common B_grid.
    Returns new Segment with H=B_grid and M=interp.
    """
    import numpy as np

    B = np.asarray(seg.H, float)
    M = np.asarray(seg.M, float)
    ok = np.isfinite(B) & np.isfinite(M)
    B = B[ok]; M = M[ok]
    if B.size < 3:
        return seg

    # Ensure monotonic increasing B for interpolation
    order = np.argsort(B)
    B = B[order]; M = M[order]

    if method == "pchip":
        try:
            from scipy.interpolate import PchipInterpolator
            f = PchipInterpolator(B, M, extrapolate=bool(extrapolate))
            M_i = f(B_grid)
        except Exception:
            left = M[0] if extrapolate else np.nan
            right = M[-1] if extrapolate else np.nan
            M_i = np.interp(B_grid, B, M, left=left, right=right)
    else:
        left = M[0] if extrapolate else np.nan
        right = M[-1] if extrapolate else np.nan
        M_i = np.interp(B_grid, B, M, left=left, right=right)

    # Keep only within original span if extrapolate=False
    if not extrapolate:
        M_i[(B_grid < B[0]) | (B_grid > B[-1])] = np.nan

    from dataclasses import replace
    return replace(seg, H=np.asarray(B_grid, float), M=np.asarray(M_i, float))

def regrid_forcs_in_hysteresis_space(
    forcs,
    B_step=None,                # e.g. 0.001 for 1 mT
    B_min=None,
    B_max=None,
    method="linear",
    extrapolate=False,
    verbose=True,
):
    """
    Returns new list of segments where every FORC has identical B_grid.
    """
    import numpy as np

    forcs_only = [s for s in forcs if getattr(s, "kind", None) == "forc"]
    if not forcs_only:
        return forcs

    if B_step is None:
        B_step = infer_B_step_from_forcs(forcs_only)
        if B_step is None:
            raise ValueError("Could not infer B_step from FORCs.")
    B_step = float(B_step)

    # Choose overall range if not provided
    all_Bmin = min(float(np.nanmin(np.asarray(s.H, float))) for s in forcs_only)
    all_Bmax = max(float(np.nanmax(np.asarray(s.H, float))) for s in forcs_only)
    if B_min is None: B_min = all_Bmin
    if B_max is None: B_max = all_Bmax

    # Build common grid
    n = int(np.floor((B_max - B_min) / B_step)) + 1
    B_grid = B_min + B_step * np.arange(n, dtype=float)

    out = []
    for s in forcs:
        if getattr(s, "kind", None) != "forc":
            out.append(s)
            continue
        out.append(regrid_segment_BM(s, B_grid, method=method, extrapolate=extrapolate))

    if verbose:
        print(f"Regridded FORCs to common B grid: {B_grid[0]:.6g}→{B_grid[-1]:.6g} T "
              f"(n={len(B_grid)}), step={B_step:.6g} T")

    return out

def phase1_prepare_segments_dual(
    path: str,
    cal_tol_T: float = 2e-3,
    drift_fit: str = "linear",
    endpoint_replace_n: int = 1,
    replace_first: bool = True,
    replace_last: bool = True,
    do_reference_subtract: bool = False,
    reference_curve: str = "lowest_reversal",
    require_calibration: bool = False,
    blank_sep: int = 2,
    jump_T: float = 0.05,
    cal_drop_T: float = 0.02,
    export_magic: bool = True,
    verbose: bool = True,
) -> Tuple[List[Segment], List[Segment]]:
    """
    Returns:
      segs_display: drift-corrected + optional endpoint replacement (NO lower-branch subtraction)
      segs_rho:     segs_display, optionally lower-branch-subtracted
    """

    if is_multi_segment_forc_file(path):
        tags = {}
        segs = read_multi_segment_segments(path, dtype=np.float64, verbose=verbose)

        if export_magic and verbose:
            print("MagIC export is currently skipped for multi-segment FORC files.")

    else:
        tags, data_start_idx = read_header_tags_and_data_start(path)
        if "HCal" not in tags:
            raise ValueError("Header tag HCal not found; cannot split calibration points safely.")
        HCal = float(tags["HCal"])

        segs = read_segments_raw(
            path,
            data_start_idx=data_start_idx,
            dtype=np.float64,
            min_block_len=2,
            blank_sep=blank_sep,
            jump_T=jump_T,
            HCal=HCal,
            cal_tol_T=cal_tol_T,
            cal_drop_T=cal_drop_T,
            verbose=verbose,
        )

        # Export MagIC directly from the raw file structure using blank-line-
        # delimited numeric groups. This is independent of later internal FORC
        # segmentation and drift correction.
        if export_magic:
            try:
                meas_temp_k = float(tags["Temperature"]) if "Temperature" in tags else None
                export_magic_measurements_from_raw(
                    path,
                    data_start_idx=data_start_idx,
                    meas_temp_k=meas_temp_k,
                )
            except Exception as e:
                if verbose:
                    print(f"Warning: MagIC export failed for {path}: {e}")

        segs = split_cal_first_point(segs, HCal=HCal, tol_T=cal_tol_T)

    cal_segs = [s for s in segs if s.kind == "cal"]
    if len(cal_segs) >= 2:
        drift_at_seg, _, _ = compute_drift_from_cals(segs, fit=drift_fit)
        segs = apply_drift_correction(segs, drift_at_seg)
        if verbose:
            cal_M = np.array([float(s.M[0]) for s in cal_segs])
            print(f"Drift correction ({drift_fit}) from {len(cal_segs)} calibration points: "
                  f"{cal_M[-1] - cal_M[0]:+.3e} A m^2 over the run")
    elif require_calibration:
        kinds: Dict[str, int] = {}
        for s in segs:
            kinds[s.kind] = kinds.get(s.kind, 0) + 1
        raise ValueError(f"Need >=2 calibration points; found {len(cal_segs)}. Kind counts: {kinds}.")
    elif verbose:
        # Silence here would misrepresent the output as drift-corrected.
        print(f"Warning: only {len(cal_segs)} calibration point(s) identified in "
              f"{as_path(path).name}; NO drift correction has been applied.")

    # endpoint conditioning (FORCs only)
    if endpoint_replace_n > 0 and (replace_first or replace_last):
        segs_display = [
            replace_endpoints(s, n=endpoint_replace_n, replace_first=replace_first, replace_last=replace_last)
            if s.kind == "forc" else s
            for s in segs
        ]
    else:
        segs_display = segs

    segs_rho = (subtract_reference_curve(segs_display, reference=reference_curve)
                if do_reference_subtract else segs_display)
    return segs_display, segs_rho

def _list_stack_input_files(
    path: PathLike,
    stack: bool = False,
    stack_glob: Optional[str] = None,
    verbose: bool = True,
) -> List[Path]:
    """
    Resolve user input into one or more files.

    Rules
    -----
    - If path is a file: return [that file]
    - If path is a directory:
        * stack must be True
        * files are discovered with stack_glob (default: '*.txt')
    """
    p = as_path(path)

    if p.is_file():
        return [p]

    if not p.exists():
        raise FileNotFoundError(f"Path not found: {p}")

    if not p.is_dir():
        raise ValueError(f"Path is neither a file nor a directory: {p}")

    if not stack:
        raise ValueError(
            "Path points to a directory. For directory stacking, set stack=True; "
            "otherwise pass a specific file path."
        )

    pattern = "*.txt" if stack_glob is None else str(stack_glob)
    files = sorted([f for f in p.glob(pattern) if f.is_file()])

    # Never treat generated MagIC exports as input FORC files.
    files = [f for f in files if not f.name.endswith("_MagIC.txt")]

    if not files:
        raise FileNotFoundError(
            f"No non-MagIC files matched pattern {pattern!r} in directory: {p}"
        )

    if verbose:
        print(f"Stack input directory: {p}")
        print(f"Matched {len(files)} file(s) with pattern: {pattern}")

    return files

def _prepare_single_input_for_rho(
    path: PathLike,
    cal_tol_T: float = 2e-3,
    drift_fit: str = "linear",
    endpoint_replace_n: int = 1,
    replace_first: bool = True,
    replace_last: bool = True,
    do_reference_subtract: bool = False,
    reference_curve: str = "lowest_reversal",
    blank_sep: int = 2,
    jump_T: float = 0.05,
    cal_drop_T: float = 0.02,
    do_regrid: bool = False,
    B_step: Optional[float] = None,
    regrid_method: str = "linear",
    regrid_extrapolate: bool = False,
    export_magic: bool = True,
    verbose: bool = True,
) -> Dict[str, object]:
    """
    Prepare one file up to the point where it is ready to enter Ha–Hb gridding.
    """

    hdr_Bu_max, hdr_Bc_max = read_forc_header_limits(path)

    segs_display, segs_rho = phase1_prepare_segments_dual(
        str(path),
        cal_tol_T=cal_tol_T,
        drift_fit=drift_fit,
        endpoint_replace_n=endpoint_replace_n,
        replace_first=replace_first,
        replace_last=replace_last,
        do_reference_subtract=do_reference_subtract,
        reference_curve=reference_curve,
        blank_sep=blank_sep,
        jump_T=jump_T,
        cal_drop_T=cal_drop_T,
        export_magic=export_magic,
        verbose=verbose,
    )

    forcs_display = [s for s in segs_display if s.kind == "forc"]
    forcs_rho     = [s for s in segs_rho     if s.kind == "forc"]

    forcs_for_rho = forcs_rho if do_reference_subtract else forcs_display

    forcs_for_rho_corr = forcs_for_rho
    if do_regrid:
        forcs_for_rho_corr = regrid_forcs_in_hysteresis_space(
            forcs_for_rho,
            B_step=B_step,
            method=regrid_method,
            extrapolate=regrid_extrapolate,
            verbose=verbose,
        )

    n_cal = sum(1 for s in segs_display if s.kind == "cal")
    return {
        "path": as_path(path),
        "header_limits": {"Bu_max": hdr_Bu_max, "Bc_max": hdr_Bc_max},
        "n_calibration_points": n_cal,
        "drift_corrected": n_cal >= 2,
        "segs_display": segs_display,
        "segs_rho": segs_rho,
        "forcs_display": forcs_display,
        "forcs_rho": forcs_rho,
        "forcs_for_rho_corr": forcs_for_rho_corr,
    }

def _infer_common_stack_grid(
    prepared_items: List[Dict[str, object]],
    B_step: Optional[float] = None,
) -> Dict[str, float]:
    """
    Infer one common regular Ha–Hb grid for all prepared files.
    """

    all_forcs = []
    all_hb = []
    all_h = []

    for item in prepared_items:
        for s in item["forcs_for_rho_corr"]:
            if getattr(s, "kind", None) != "forc":
                continue

            H = np.asarray(s.H, float)
            M = np.asarray(s.M, float)
            ok = np.isfinite(H) & np.isfinite(M)
            if ok.sum() < 3:
                continue

            Hf = H[ok]
            Ha = float(getattr(s, "Ha", np.nan))
            if not np.isfinite(Ha):
                Ha = float(np.min(Hf))

            all_forcs.append(Segment(H=Hf.copy(), M=M[ok].copy(), idx=0, kind="forc", Ha=Ha))
            all_hb.append(Ha)
            all_h.append(Hf)

    if not all_forcs:
        raise ValueError("No usable FORCs found across stack inputs.")

    if B_step is None:
        Hb_step = infer_B_step_from_forcs(all_forcs)
        if Hb_step is None:
            raise ValueError("Could not infer common Hb_step/B_step for stacking.")
    else:
        Hb_step = float(B_step)

    all_hb = np.asarray(all_hb, float)
    hb_unique = np.unique(np.round(all_hb, decimals=6))
    if hb_unique.size > 1:
        diffs = np.diff(hb_unique)
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        Ha_step_raw = float(np.median(diffs)) if diffs.size else float(Hb_step)
    else:
        Ha_step_raw = float(Hb_step)

    Ha_step = max(Ha_step_raw, float(Hb_step))

    all_h = np.concatenate(all_h)
    Hb_min = float(np.nanmin(all_h))
    Hb_max = float(np.nanmax(all_h))
    Ha_min = float(np.nanmin(all_hb))
    Ha_max = float(np.nanmax(all_hb))

    return {
        "Hb_step": float(Hb_step),
        "Ha_step": float(Ha_step),
        "Hb_min": Hb_min,
        "Hb_max": Hb_max,
        "Ha_min": Ha_min,
        "Ha_max": Ha_max,
    }

def _stack_nan_grids(
    grids: List[np.ndarray],
    method: str = "mean",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stack a list of M(Ha,Hb) grids with NaN-awareness.

    Returns
    -------
    M_stack : 2D array
    counts  : number of finite inputs contributing at each grid cell
    """
    arr = np.asarray(grids, dtype=float)
    if arr.ndim != 3:
        raise ValueError("Expected grids with shape (n_files, n_Ha, n_Hb).")

    counts = np.sum(np.isfinite(arr), axis=0)

    method_l = str(method).strip().lower()
    if method_l == "mean":
        sums = np.nansum(arr, axis=0)
        out = np.full(arr.shape[1:], np.nan, dtype=float)
        np.divide(sums, counts, out=out, where=counts > 0)
        return out, counts

    if method_l == "median":
        with np.errstate(all="ignore"):
            out = np.nanmedian(arr, axis=0)
        out[counts == 0] = np.nan
        return out, counts

    raise ValueError("stack_method must be 'mean' or 'median'.")

# ============================================================
# Plot: individual FORC curves (hysteresis space)
# ============================================================

def plot_forc_curves_hysteresis(
    forcs: List[Segment],
    title: str = "FORC curves",
    figsize: Tuple[float, float] = (7, 6),
    dpi: int = 120,
    lw: float = 0.9,
    alpha: float = 0.7,
    add_origin_axes: bool = True,
    plot_fraction: float = 0.10,
    max_curves: Optional[int] = None,
    randomize: bool = False,
    seed: int = 0,
) -> None:
    if not forcs:
        raise ValueError("No FORC segments provided.")

    n = len(forcs)
    plot_fraction = 1.0 if plot_fraction is None else float(plot_fraction)
    plot_fraction = max(0.0, min(1.0, plot_fraction))

    n_plot = int(np.ceil(n * plot_fraction)) if plot_fraction > 0 else 0
    if max_curves is not None:
        n_plot = min(n_plot, int(max_curves))
    n_plot = max(1, n_plot) if n > 0 else 0

    if n_plot >= n:
        sel_forcs = forcs
    else:
        if randomize:
            rng = np.random.default_rng(int(seed))
            idx = rng.choice(n, size=n_plot, replace=False)
            idx.sort()
        else:
            idx = np.linspace(0, n - 1, n_plot)
            idx = np.unique(np.rint(idx).astype(int))
        sel_forcs = [forcs[i] for i in idx]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    for s in sel_forcs:
        H = np.asarray(s.H, float)
        M = np.asarray(s.M, float)
        ok = np.isfinite(H) & np.isfinite(M)
        if ok.sum() < 2:
            continue
        ax.plot(H[ok], M[ok], lw=lw, alpha=alpha)

    if add_origin_axes:
        ax.axhline(0, color="k", lw=0.8, alpha=0.8)
        ax.axvline(0, color="k", lw=0.8, alpha=0.8)

    ax.set_xlabel("H (T)")
    ax.set_ylabel("M (A m$^2$)")
    ax.set_title(title)
    fig.subplots_adjust(left=0.14, right=0.97, bottom=0.14, top=0.88)
    plt.show()

# ============================================================
# Phase 2: build grid + LOESS rho
# ============================================================

def build_forc_grid(forcs: List[Segment], Hb_min=None, Hb_max=None, verbose: bool = True):
    """Build rectangular grid M(Ha,Hb). Returns Ha_vals, Hb_vals, M_grid, dHb, dHa."""
    good: List[Segment] = []
    for s in forcs:
        if getattr(s, "kind", None) != "forc":
            continue
        H = np.asarray(s.H, dtype=float)
        M = np.asarray(s.M, dtype=float)
        finite = np.isfinite(H) & np.isfinite(M)
        if finite.sum() >= 3:
            s._Hf = H[finite]
            s._Mf = M[finite]
            if getattr(s, "Ha", None) is None or not np.isfinite(s.Ha):
                s.Ha = float(np.min(s._Hf))
            good.append(s)

    if verbose:
        print(f"FORC segments provided: {len(forcs)}")
        print(f"FORC segments usable (>=3 finite pts): {len(good)}")

    if len(good) == 0:
        raise ValueError("No usable FORC segments (need >=3 finite points each).")

    all_dH = []
    for s in good:
        dH = np.diff(s._Hf)
        dH = dH[np.isfinite(dH) & (dH != 0)]
        if dH.size:
            all_dH.append(dH)
    if not all_dH:
        raise ValueError("Could not infer dHb (no valid nonzero H steps found).")

    all_dH = np.concatenate(all_dH)
    dHb = float(np.median(all_dH))
    if not np.isfinite(dHb) or dHb <= 0:
        raise ValueError(f"Bad dHb inferred: {dHb}")

    all_H_min = min(float(np.min(s._Hf)) for s in good)
    all_H_max = max(float(np.max(s._Hf)) for s in good)
    if Hb_min is None:
        Hb_min = all_H_min
    if Hb_max is None:
        Hb_max = all_H_max
    if (not np.isfinite(Hb_min)) or (not np.isfinite(Hb_max)) or Hb_max <= Hb_min:
        raise ValueError(f"Bad H range inferred: Hb_min={Hb_min}, Hb_max={Hb_max}")

    nHb = int(np.round((Hb_max - Hb_min) / dHb)) + 1
    Hb_vals = Hb_min + dHb * np.arange(nHb, dtype=np.float64)

    Ha_vals = np.array([float(s.Ha) for s in good], dtype=np.float64)
    order = np.argsort(Ha_vals)
    Ha_vals = Ha_vals[order]
    good = [good[i] for i in order]

    if len(Ha_vals) > 1:
        dHa = float(np.median(np.diff(Ha_vals)))
        if not np.isfinite(dHa) or dHa <= 0:
            dHa = dHb
    else:
        dHa = dHb

    # Assigning each measurement to its nearest column is exact only when the
    # measured applied fields already lie on the common lattice. They do not
    # when the reversal-field increment is not a whole multiple of the
    # applied-field step: every curve then starts at a different sub-step
    # offset, and snapping would displace measurements by up to half a step.
    # Since the distribution is a second derivative in field, that displacement
    # is not a small error -- it can change rho by a factor of a few. Where the
    # offsets are significant the curves are interpolated onto the lattice
    # instead.
    offsets = [np.abs(s._Hf - (Hb_min + dHb * np.rint((s._Hf - Hb_min) / dHb)))
               for s in good]
    max_offset = float(max(np.max(o) if o.size else 0.0 for o in offsets))
    snap_tol = 1e-3 * dHb
    on_lattice = max_offset <= snap_tol

    M_grid = np.full((len(good), len(Hb_vals)), np.nan, dtype=np.float64)
    for i, s in enumerate(good):
        if on_lattice:
            col = np.rint((s._Hf - Hb_min) / dHb).astype(int)
            ok = (col >= 0) & (col < len(Hb_vals))
            M_grid[i, col[ok]] = s._Mf[ok]
        else:
            order_H = np.argsort(s._Hf)
            Hf, Mf = s._Hf[order_H], s._Mf[order_H]
            row = np.interp(Hb_vals, Hf, Mf, left=np.nan, right=np.nan)
            # Interpolation must not invent data outside the measured span or
            # below this curve's own reversal field.
            row[(Hb_vals < Hf[0]) | (Hb_vals > Hf[-1]) | (Hb_vals < float(s.Ha))] = np.nan
            M_grid[i, :] = row

    if verbose:
        print(f"Inferred dHb ≈ {dHb:.6g} T, Hb: {Hb_vals[0]:.6g}→{Hb_vals[-1]:.6g} (n={len(Hb_vals)})")
        print(f"Inferred dHa ≈ {dHa:.6g} T, Ha: {Ha_vals[0]:.6g}→{Ha_vals[-1]:.6g} (n={len(Ha_vals)})")
        print(f"M_grid shape: {M_grid.shape}")
        if not on_lattice:
            print(f"Measured applied fields sit up to {1e3 * max_offset:.3f} mT off the common "
                  f"{1e3 * dHb:.3f} mT grid; curves were interpolated onto it rather than snapped.")

    return Ha_vals, Hb_vals, M_grid, dHb, dHa

def build_forc_grid_regridded(
    forcs: List[Segment],
    Hb_step: Optional[float] = None,
    Ha_step: Optional[float] = None,
    regrid_method: str = "linear",
    regrid_extrapolate: bool = False,
    Hb_min: Optional[float] = None,
    Hb_max: Optional[float] = None,
    Ha_min: Optional[float] = None,
    Ha_max: Optional[float] = None,
    verbose: bool = True,
):
    """
    Build M(Ha,Hb) on a *regular* Ha and Hb grid:
      1) Interp each FORC M(H) onto common Hb grid (row-by-row)
      2) Interp across Ha to uniform Ha grid (column-by-column)
    """

    good = []
    for s in forcs:
        if getattr(s, "kind", None) != "forc":
            continue
        H = np.asarray(s.H, float)
        M = np.asarray(s.M, float)
        ok = np.isfinite(H) & np.isfinite(M)
        if ok.sum() >= 3:
            Hf = H[ok]; Mf = M[ok]
            # ensure Ha
            Ha = float(getattr(s, "Ha", np.nan))
            if not np.isfinite(Ha):
                Ha = float(np.min(Hf))
            good.append((Ha, Hf, Mf))

    if len(good) == 0:
        raise ValueError("No usable FORC segments (need >=3 finite pts).")

    # sort by Ha
    good.sort(key=lambda t: t[0])
    Ha_vals_meas = np.array([t[0] for t in good], dtype=float)

    # infer Hb step if needed
    if Hb_step is None:
        dHs = []
        for _, Hf, _ in good:
            d = np.diff(Hf)
            d = d[np.isfinite(d) & (d != 0)]
            if d.size:
                dHs.append(d)
        if not dHs:
            raise ValueError("Could not infer Hb_step.")
        Hb_step = float(np.median(np.concatenate(dHs)))

    # Hb range
    all_H = np.concatenate([t[1] for t in good])
    if Hb_min is None: Hb_min = float(np.nanmin(all_H))
    if Hb_max is None: Hb_max = float(np.nanmax(all_H))
    nHb = int(np.round((Hb_max - Hb_min) / Hb_step)) + 1
    Hb_vals = Hb_min + Hb_step * np.arange(nHb, dtype=float)

    # build measured M_grid at measured Ha rows (row-by-row interpolation onto Hb)
    M_meas = np.full((len(good), len(Hb_vals)), np.nan, dtype=float)

    for i, (Ha, Hf, Mf) in enumerate(good):
        # Only physical triangle region: Hb >= Ha
        tri = Hb_vals >= Ha

        if regrid_method == "pchip":
            try:
                from scipy.interpolate import PchipInterpolator
                f = PchipInterpolator(Hf, Mf, extrapolate=bool(regrid_extrapolate))
                Mi = f(Hb_vals)
            except Exception:
                Mi = np.interp(Hb_vals, Hf, Mf, left=np.nan, right=np.nan)
        else:
            left = Mf[0] if regrid_extrapolate else np.nan
            right = Mf[-1] if regrid_extrapolate else np.nan
            Mi = np.interp(Hb_vals, Hf, Mf, left=left, right=right)

        Mi[~tri] = np.nan
        M_meas[i, :] = Mi

    # infer Ha step if needed
    if Ha_step is None:
        if len(Ha_vals_meas) > 1:
            Ha_step = float(np.median(np.diff(Ha_vals_meas)))
        else:
            Ha_step = float(Hb_step)

    # uniform Ha grid
    if Ha_min is None:
        Ha_min = float(Ha_vals_meas[0])
    if Ha_max is None:
        Ha_max = float(Ha_vals_meas[-1])

    nHa = int(np.round((Ha_max - Ha_min) / Ha_step)) + 1
    Ha_vals = Ha_min + Ha_step * np.arange(nHa, dtype=float)

    # regrid across Ha column-by-column
    M_grid = np.full((len(Ha_vals), len(Hb_vals)), np.nan, dtype=float)

    for j in range(len(Hb_vals)):
        col = M_meas[:, j]
        ok = np.isfinite(col)
        if ok.sum() < 2:
            continue

        x = Ha_vals_meas[ok]
        y = col[ok]

        if regrid_method == "pchip":
            try:
                from scipy.interpolate import PchipInterpolator
                f = PchipInterpolator(x, y, extrapolate=bool(regrid_extrapolate))
                yc = f(Ha_vals)
            except Exception:
                yc = np.interp(Ha_vals, x, y, left=np.nan, right=np.nan)
        else:
            left = y[0] if regrid_extrapolate else np.nan
            right = y[-1] if regrid_extrapolate else np.nan
            yc = np.interp(Ha_vals, x, y, left=left, right=right)

        # enforce triangle mask: Hb >= Ha
        yc[Hb_vals[j] < Ha_vals] = np.nan
        M_grid[:, j] = yc

    if verbose:
        print(f"Regridded Ha: {Ha_vals[0]:.6g}→{Ha_vals[-1]:.6g} (n={len(Ha_vals)}), step={Ha_step:.6g}")
        print(f"Regridded Hb: {Hb_vals[0]:.6g}→{Hb_vals[-1]:.6g} (n={len(Hb_vals)}), step={Hb_step:.6g}")
        print(f"M_grid shape: {M_grid.shape}")

    # also return inferred steps (dHb,dHa equivalents)
    return Ha_vals, Hb_vals, M_grid, float(Hb_step), float(Ha_step)

def _build_offsets(rx: int, ry: int) -> np.ndarray:
    offs = []
    for di in range(-ry, ry + 1):
        for dj in range(-rx, rx + 1):
            u = np.sqrt((dj / rx) ** 2 + (di / ry) ** 2) if (rx > 0 and ry > 0) else 0.0
            if u <= 1.0:
                offs.append((di, dj, u))
    return np.asarray(offs, dtype=np.float64)

def loess_rho_from_grid_fast(
    Ha_vals, Hb_vals, M_grid,
    span_Hb_T: float = 0.005,
    span_Ha_T: float = 0.005,
    min_pts: int = 50,
    chunk_size: int = 512,
    return_fit: bool = False,
):
    """
    Calculate a LOESS-smoothed FORC distribution on a field grid.

    A weighted quadratic surface is fitted around every finite grid cell using
    a tricube-weighted elliptical neighborhood.  The FORC distribution is
    ``-0.5 * d2M / (dHb dHa)``, obtained from the mixed term of each local fit.

    The local systems are assembled and solved in NumPy batches.  Processing
    the finite cells in chunks keeps memory use bounded for large FORC grids
    while avoiding an optional just-in-time compiler dependency.

    Parameters
    ----------
    Ha_vals, Hb_vals : array-like
        Strictly increasing reversal- and applied-field coordinates in tesla.
        Regularly spaced axes use a shared design matrix; measured irregular
        spacing is handled using the actual local coordinates.
    M_grid : array-like
        Magnetization values with shape ``(len(Ha_vals), len(Hb_vals))``.
        Missing or nonphysical cells should contain ``NaN``.
    span_Hb_T, span_Ha_T : float, optional
        Semi-axis lengths of the elliptical smoothing neighborhood in tesla.
    min_pts : int, optional
        Minimum number of finite neighboring measurements required for a fit.
        At least six points are always required for the six quadratic terms.
    chunk_size : int, optional
        Maximum number of grid cells assembled and solved in one batch.
        Smaller values reduce peak memory use; larger values may be faster.

    return_fit : bool, optional
        Also return the locally fitted magnetization surface, the value of
        each local quadratic evaluated at its own centre.  The residual
        ``M_grid - M_fit`` is the basis of the FORCinel-style criterion for
        choosing a smoothing level (Harrison & Feinberg, 2008): the smoothing
        factor is increased until the residuals indicate that signal, rather
        than noise, is being removed.

    Returns
    -------
    numpy.ndarray
        The FORC distribution with the same shape as ``M_grid``.  Cells that
        lack enough measurements or a full-rank quadratic fit are ``NaN``.
        When ``return_fit`` is True, a ``(rho, M_fit)`` tuple is returned.

    Notes
    -----
    Local coordinates are expressed relative to the median field steps when
    the quadratic systems are solved.  This improves numerical conditioning
    for both regular and irregular measured grids.  The mixed coefficient is
    converted back to inverse tesla squared before returning the FORC
    distribution.
    """
    Ha_vals = np.asarray(Ha_vals, dtype=np.float64)
    Hb_vals = np.asarray(Hb_vals, dtype=np.float64)
    M = np.asarray(M_grid, dtype=np.float64)

    if Ha_vals.ndim != 1 or Hb_vals.ndim != 1:
        raise ValueError("Ha_vals and Hb_vals must be one-dimensional.")
    if Hb_vals.size < 2 or Ha_vals.size < 1:
        raise ValueError("Hb_vals needs at least two values and Ha_vals at least one.")
    if M.shape != (Ha_vals.size, Hb_vals.size):
        raise ValueError(
            "M_grid shape must be (len(Ha_vals), len(Hb_vals)); "
            f"received {M.shape}."
        )
    if int(chunk_size) < 1:
        raise ValueError("chunk_size must be a positive integer.")

    dHb_steps = np.diff(Hb_vals)
    dHb = float(np.median(dHb_steps))
    if not np.all(np.isfinite(dHb_steps)) or np.any(dHb_steps <= 0):
        raise ValueError("Hb_vals must be finite and strictly increasing.")
    regular_Hb = np.allclose(dHb_steps, dHb, rtol=1e-6, atol=0.0)

    if Ha_vals.size > 1:
        dHa_steps = np.diff(Ha_vals)
        dHa = float(np.median(dHa_steps))
        if not np.all(np.isfinite(dHa_steps)) or np.any(dHa_steps <= 0):
            raise ValueError("Ha_vals must be finite and strictly increasing.")
        regular_Ha = np.allclose(dHa_steps, dHa, rtol=1e-6, atol=0.0)
    else:
        dHa = dHb
        regular_Ha = True

    if not np.isfinite(span_Hb_T) or float(span_Hb_T) <= 0:
        raise ValueError("span_Hb_T must be a positive finite value.")
    if not np.isfinite(span_Ha_T) or float(span_Ha_T) <= 0:
        raise ValueError("span_Ha_T must be a positive finite value.")

    rx = max(1, int(np.ceil(float(span_Hb_T) / dHb)))
    ry = max(1, int(np.ceil(float(span_Ha_T) / dHa)))
    offsets = _build_offsets(rx, ry)

    max_pts = int(offsets.shape[0])
    min_pts = max(6, min(int(min_pts), max_pts - 1))
    chunk_size = int(chunk_size)

    di = offsets[:, 0].astype(np.intp)
    dj = offsets[:, 1].astype(np.intp)
    distance = offsets[:, 2]
    weights = (1.0 - distance ** 3) ** 3

    regular_grid = regular_Hb and regular_Ha
    if regular_grid:
        # Grid-step coordinates keep the quadratic systems well-conditioned.
        dx = dj.astype(np.float64)
        dy = di.astype(np.float64)
        shared_design = np.column_stack([
            np.ones_like(dx),
            dx,
            dy,
            dx * dx,
            dx * dy,
            dy * dy,
        ])

    physical = Hb_vals[np.newaxis, :] >= Ha_vals[:, np.newaxis]
    valid = np.isfinite(M) & physical
    center_flat = np.flatnonzero(valid)
    center_i, center_j = np.unravel_index(center_flat, M.shape)
    rho = np.full(M.shape, np.nan, dtype=np.float64)
    M_fit = np.full(M.shape, np.nan, dtype=np.float64) if return_fit else None

    for start in range(0, center_flat.size, chunk_size):
        stop = min(start + chunk_size, center_flat.size)
        ii = center_i[start:stop, np.newaxis] + di
        jj = center_j[start:stop, np.newaxis] + dj

        inside = (
            (ii >= 0) & (ii < M.shape[0])
            & (jj >= 0) & (jj < M.shape[1])
        )
        ii = np.clip(ii, 0, M.shape[0] - 1)
        jj = np.clip(jj, 0, M.shape[1] - 1)

        values = M[ii, jj]
        neighbor_valid = inside & valid[ii, jj]
        enough_points = np.count_nonzero(neighbor_valid, axis=1) >= min_pts
        if not np.any(enough_points):
            continue

        ii = ii[enough_points]
        jj = jj[enough_points]
        neighbor_valid = neighbor_valid[enough_points]
        values = np.where(neighbor_valid, values[enough_points], 0.0)
        weighted_valid = neighbor_valid * weights

        if regular_grid:
            normal_matrices = np.einsum(
                "ck,kp,kq->cpq",
                weighted_valid,
                shared_design,
                shared_design,
                optimize=True,
            )
            right_sides = np.einsum(
                "ck,kp,ck->cp",
                weighted_valid,
                shared_design,
                values,
                optimize=True,
            )
        else:
            center_rows = center_i[start:stop][enough_points, np.newaxis]
            center_cols = center_j[start:stop][enough_points, np.newaxis]
            dx = (Hb_vals[jj] - Hb_vals[center_cols]) / dHb
            dy = (Ha_vals[ii] - Ha_vals[center_rows]) / dHa
            local_design = np.stack([
                np.ones_like(dx),
                dx,
                dy,
                dx * dx,
                dx * dy,
                dy * dy,
            ], axis=2)
            normal_matrices = np.einsum(
                "ck,ckp,ckq->cpq",
                weighted_valid,
                local_design,
                local_design,
                optimize=True,
            )
            right_sides = np.einsum(
                "ck,ckp,ck->cp",
                weighted_valid,
                local_design,
                values,
                optimize=True,
            )

        # Reject cells whose local system is rank deficient -- collinear or
        # too-few neighbours -- before solving. matrix_rank uses an SVD with a
        # relative tolerance, so it also screens out systems that are merely
        # near singular and would otherwise return meaningless coefficients.
        full_rank = np.linalg.matrix_rank(normal_matrices) == 6
        if not np.any(full_rank):
            continue

        coefficients = np.linalg.solve(
            normal_matrices[full_rank],
            right_sides[full_rank, :, np.newaxis],
        )[:, :, 0]
        solved_flat = center_flat[start:stop][enough_points][full_rank]
        mixed_derivative = coefficients[:, 4] / (dHb * dHa)
        rho.ravel()[solved_flat] = -0.5 * mixed_derivative
        if return_fit:
            # Local coordinates are centred on the node, so the constant term
            # is the fitted surface evaluated at that node.
            M_fit.ravel()[solved_flat] = coefficients[:, 0]

    if return_fit:
        return rho, M_fit
    return rho

# ============================================================
# Colormap + rho plotting
# ============================================================

def forc_colormap_v1():
    # your current “attached” map
    colors = [
        (0.00, "#1f4aa8"),
        (0.22, "#86a6da"),
        (0.50, "#ffffff"),
        (0.62, "#f2e85c"),
        (0.78, "#d94b2a"),
        (0.90, "#c4172a"),
        (1.00, "#d100b5"),
    ]
    return LinearSegmentedColormap.from_list("forc_v1_attached", colors)

def forc_colormap_v2():
    """
    New colorscale (approx. from your attached colorbar):
    light blue -> white (0) -> green -> yellow/orange -> red -> purple
    (You can tweak hex values to taste.)
    """
    colors = [
        (0.00, "#8fb3ff"),  # light blue (negative)
        (0.50, "#ffffff"),  # white (0)
        (0.55, "#558D36"),  # green
        (0.65, "#f2e85c"),  # yellow
        (0.82, "#e84d3c"),  # magenta-ish
        (1.00, "#5b1e73"),  # purple (high positive)
    ]
    return LinearSegmentedColormap.from_list("forc_v2_rainbowish", colors)

def forc_colormap_v3():
    """
    New colorscale (approx. from your attached colorbar):
    light blue -> white (0) -> green -> yellow/orange -> red -> purple
    (You can tweak hex values to taste.)
    """
    colors = [
        (0.00, "#bfc6e8"),  # very pale blue-grey (strong negative)
        (0.35, "#e6e9f5"),  # lighter negative
        (0.50, "#ffffff"),  # zero (white)
        (0.60, "#4cc26b"),  # green
        (0.72, "#f2cf4a"),  # yellow
        (0.82, "#e84d3c"),  # red
        (0.92, "#c23b8f"),  # magenta
        (1.00, "#5b1e73"),  # deep purple (strong positive)
    ]
    return LinearSegmentedColormap.from_list("forc_v3_rainbowish", colors)

# --- registry + selector ---
FORC_CMAP_REGISTRY = {
    1: forc_colormap_v1,
    2: forc_colormap_v2,
    3: forc_colormap_v3,
}

def get_forc_cmap(color_scale_version: int = 1):
    fn = FORC_CMAP_REGISTRY.get(int(color_scale_version), forc_colormap_v1)
    return fn()

def _rho_norm(rho, pct=100, normalize_to_unit: bool = False):
    vmax = np.nanpercentile(np.abs(rho), pct)
    if not np.isfinite(vmax) or vmax <= 0:
        vmax = 1.0

    if normalize_to_unit:
        # caller should plot rho/vmax, and norm is fixed to [-1,1]
        return TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0), vmax

    return TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax), vmax



def plot_forc_distribution_hysteresis_space(
    Ha_vals,
    Hb_vals,
    M_grid,
    rho,
    forcs: Optional[List[Segment]] = None,
    title: str = "FORC distribution in hysteresis space",
    figsize: Tuple[float, float] = (7, 6),
    dpi: int = 120,
    plot_fraction: float = 1.0,
    max_rows: Optional[int] = None,
    overlay_forc_curves: bool = True,
    curve_lw: float = 0.45,
    curve_alpha: float = 0.20,
    marker_size: float = 10.0,
    color_scale_version: int = 1,
    normalize_to_unit: bool = True,
    pct: float = 99.0,
    add_origin_axes: bool = True,
    return_fig: bool = False,
):
    """
    Diagnostic plot of the FORC distribution in hysteresis space.

    The usual FORC distribution rho is defined on the Ha-Hb grid, where Hb is
    the applied field along a FORC and Ha is the reversal field. This function
    maps each finite rho(Ha, Hb) cell back onto the corresponding hysteresis
    curve using M_grid(Ha, Hb), and plots the result as H versus M colored by
    rho. This makes it easier to see where the calculated FORC signal sits on
    the measured/regridded FORC curves.

    Parameters
    ----------
    Ha_vals, Hb_vals : 1D arrays
        Reversal-field and applied-field grid coordinates.
    M_grid : 2D array, shape (len(Ha_vals), len(Hb_vals))
        Moment grid used for calculating rho.
    rho : 2D array, shape (len(Ha_vals), len(Hb_vals))
        FORC distribution on the same grid as M_grid.
    forcs : list of Segment, optional
        If provided, faint FORC curves are overlaid behind the colored rho
        points. These should normally be the same FORCs used for rho after any
        optional lower-branch subtraction/regridding.
    """
    Ha_vals = np.asarray(Ha_vals, float)
    Hb_vals = np.asarray(Hb_vals, float)
    M_grid = np.asarray(M_grid, float)
    rho = np.asarray(rho, float)

    if M_grid.shape != rho.shape:
        raise ValueError(f"M_grid and rho must have the same shape; got {M_grid.shape} and {rho.shape}.")
    if M_grid.shape != (len(Ha_vals), len(Hb_vals)):
        raise ValueError(
            "M_grid/rho shape must be (len(Ha_vals), len(Hb_vals)); "
            f"got {M_grid.shape}, expected {(len(Ha_vals), len(Hb_vals))}."
        )

    n_rows = len(Ha_vals)
    plot_fraction = 1.0 if plot_fraction is None else float(plot_fraction)
    plot_fraction = max(0.0, min(1.0, plot_fraction))

    if plot_fraction < 1.0 or max_rows is not None:
        n_plot = int(np.ceil(n_rows * plot_fraction)) if plot_fraction > 0 else 0
        if max_rows is not None:
            n_plot = min(n_plot, int(max_rows))
        n_plot = max(1, n_plot) if n_rows > 0 else 0
        row_idx = np.unique(np.rint(np.linspace(0, n_rows - 1, n_plot)).astype(int))
    else:
        row_idx = np.arange(n_rows, dtype=int)

    H2D = np.broadcast_to(Hb_vals[None, :], M_grid.shape)
    mask = np.zeros_like(rho, dtype=bool)
    mask[row_idx, :] = True
    mask &= np.isfinite(H2D) & np.isfinite(M_grid) & np.isfinite(rho)
    mask &= H2D >= Ha_vals[:, None]

    if not np.any(mask):
        raise ValueError("No finite rho/M_grid cells available for the hysteresis-space distribution plot.")

    cmap = get_forc_cmap(color_scale_version)
    norm, vmax = _rho_norm(rho, pct=pct, normalize_to_unit=normalize_to_unit)
    rho_plot = (rho / vmax) if normalize_to_unit else rho

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    if overlay_forc_curves and forcs is not None:
        # Use the same curve subsampling logic as plot_forc_curves_hysteresis.
        n = len(forcs)
        if n > 0:
            n_curve_plot = int(np.ceil(n * plot_fraction)) if plot_fraction > 0 else 0
            if max_rows is not None:
                n_curve_plot = min(n_curve_plot, int(max_rows))
            n_curve_plot = max(1, n_curve_plot)
            if n_curve_plot >= n:
                sel_forcs = forcs
            else:
                idx = np.unique(np.rint(np.linspace(0, n - 1, n_curve_plot)).astype(int))
                sel_forcs = [forcs[i] for i in idx]

            for s in sel_forcs:
                H = np.asarray(s.H, float)
                M = np.asarray(s.M, float)
                ok = np.isfinite(H) & np.isfinite(M)
                if ok.sum() >= 2:
                    ax.plot(H[ok], M[ok], lw=curve_lw, alpha=curve_alpha, color="0.35", zorder=1)

    sc = ax.scatter(
        H2D[mask],
        M_grid[mask],
        c=rho_plot[mask],
        s=marker_size,
        cmap=cmap,
        norm=norm,
        linewidths=0,
        zorder=2,
    )

    if add_origin_axes:
        ax.axhline(0, color="k", lw=0.8, alpha=0.8, zorder=0)
        ax.axvline(0, color="k", lw=0.8, alpha=0.8, zorder=0)

    ax.set_xlabel("H / Hb (T)")
    ax.set_ylabel("M (A m$^2$)")
    ax.set_title(title)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.08)
    cbar = fig.colorbar(sc, cax=cax)
    cbar.set_label(r"$\rho$")

    fig.subplots_adjust(left=0.14, right=0.88, bottom=0.14, top=0.88)
    plt.show()

    if return_fig:
        return fig, ax, sc, cbar
    return None


# -------------------------
# Grid upsampling for smoother FORC plots
# -------------------------

def upsample_forc_grid(Ha_vals, Hb_vals, rho, factor=3):
    """
    Upsample FORC grid for smoother visualization.
    This does NOT change the physics — it is purely a plotting refinement.
    """

    Ha_vals = np.asarray(Ha_vals, float)
    Hb_vals = np.asarray(Hb_vals, float)
    rho = np.asarray(rho, float)

    interp = RegularGridInterpolator(
        (Ha_vals, Hb_vals),
        rho,
        bounds_error=False,
        fill_value=np.nan
    )

    Ha_new = np.linspace(Ha_vals.min(), Ha_vals.max(), len(Ha_vals)*factor)
    Hb_new = np.linspace(Hb_vals.min(), Hb_vals.max(), len(Hb_vals)*factor)

    hdr_Bu_max, Ha2 = np.meshgrid(Ha_new, Hb_new, indexing="ij")

    pts = np.column_stack((hdr_Bu_max.ravel(), Ha2.ravel()))
    rho_new = interp(pts).reshape(hdr_Bu_max.shape)

    return Ha_new, Hb_new, rho_new



def _contour_levels(vmax, frac_step=0.10):
    if vmax is None or (not np.isfinite(vmax)) or vmax <= 0:
        return None
    step = vmax * frac_step
    if step <= 0:
        return None
    n = int(np.floor(vmax / step))
    if n < 1:
        return None
    levels_pos = np.arange(step, (n + 1) * step + 1e-30, step)
    return np.r_[-levels_pos[::-1], levels_pos]


def _low_level_contours(level_frac: float = 0.01) -> np.ndarray:
    """Return symmetric +/- low-level contour(s) in *fraction of full-scale*."""
    f = float(level_frac)
    f = abs(f)
    if not np.isfinite(f) or f <= 0:
        return np.array([], dtype=float)
    return np.array([-f, +f], dtype=float)

def _centers_to_edges_1d(x):
    x = np.asarray(x, float)
    if x.size < 2:
        dx = 1.0
        return np.array([x[0] - 0.5 * dx, x[0] + 0.5 * dx], dtype=float)

    edges = np.empty(x.size + 1, dtype=float)
    dx = np.diff(x)
    edges[1:-1] = 0.5 * (x[:-1] + x[1:])
    edges[0] = x[0] - 0.5 * dx[0]
    edges[-1] = x[-1] + 0.5 * dx[-1]
    return edges

def plot_rho_HaHb(
    Ha_vals, Hb_vals, rho,
    title: str = "Sample",
    show_contours: bool = False,
    contour_frac_step: float = 0.10,
    contour_alpha: float = 0.15,
    contour_lw: float = 0.6,
    pct: float = 99,
    figsize: Tuple[float, float] = (7, 6),
    dpi: int = 120,
    add_origin_axes: bool = True,
    add_ha_eq_hb_line: bool = True,
    normalize_to_unit: bool = True,

    color_scale_version: int = 1,

    show_low_level_contours: bool = True,
    low_level_frac: float = 0.05,        # +/- 1%
    low_level_color: str = "0.5",        # gray
    low_level_alpha: float = 0.8,
    low_level_lw: float = 0.8,
):
    cmap = get_forc_cmap(color_scale_version)
    
    norm, vmax = _rho_norm(rho, pct=pct, normalize_to_unit=normalize_to_unit)
    rho_plot = (rho / vmax) if normalize_to_unit else rho

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    # Use actual Ha/Hb cell edges rather than imshow extent.
    # This matters for adaptive/even-moment FORC files where Ha spacing is non-uniform.
    Ha_edges = _centers_to_edges_1d(np.asarray(Ha_vals, float))
    Hb_edges = _centers_to_edges_1d(np.asarray(Hb_vals, float))

    Ha2D_e, Hb2D_e = np.meshgrid(Ha_edges, Hb_edges, indexing="ij")

    pm = ax.pcolormesh(
        Hb2D_e,
        Ha2D_e,
        rho_plot,
        shading="auto",
        cmap=cmap,
        norm=norm,
    )

    ax.set_aspect("equal", adjustable="box")

    if show_contours:
        Ha2D, Hb2D = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")

        if normalize_to_unit:
            Zc = rho_plot
            levels_main = _contour_levels(1.0, contour_frac_step)
            levels_low = _low_level_contours(low_level_frac)
        else:
            Zc = rho
            levels_main = _contour_levels(vmax, contour_frac_step)
            levels_low = _low_level_contours(low_level_frac) * float(vmax)

        # main contours (black)
        if levels_main is not None:
            ax.contour(Hb2D, Ha2D, Zc, levels=levels_main, colors="k",
                       linewidths=contour_lw, alpha=contour_alpha)

        # low-level +/- contours (gray)
        if show_low_level_contours and levels_low.size:
            ax.contour(Hb2D, Ha2D, Zc, levels=levels_low, colors=low_level_color,
                       linewidths=low_level_lw, alpha=low_level_alpha)

    if add_origin_axes:
        ax.axhline(0, ls="-", lw=0.8, color="k", alpha=0.8)
        ax.axvline(0, ls="-", lw=0.8, color="k", alpha=0.8)

    if add_ha_eq_hb_line:
        hb_min = float(Ha_vals[0])
        ha_max = float(Hb_vals[-1])
        if hb_min < 0 and ha_max > 0:
            hi = float(min(ha_max, -hb_min))
            ax.plot([0, hi], [0, -hi], ls="--", lw=0.9, color="k", alpha=0.6)

    ax.set_xlabel("Hb (T)")
    ax.set_ylabel("Ha (T)")
    ax.set_title(title)

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.08)
    cbar = fig.colorbar(pm, cax=cax)
    cbar.set_label(r"$\rho$")

    plt.tight_layout()
    plt.show()


def _rho_window_vmax(
    Ha_vals, Hb_vals, rho,
    pct: float = 99,
    normalize_to_unit: bool = False,
    Bu_min=None, Bu_max=None,
    Bc_min=None, Bc_max=None,
    bu_expand: float = 1.0,
) -> float:
    """
    Compute vmax from |rho| using ONLY the data inside the Bu/Bc plot window.
    Returns a finite positive vmax (fallback to global if window empty).
    """
    rho = np.asarray(rho, float)

    Ha2D, Hb2D = np.meshgrid(np.asarray(Ha_vals, float), np.asarray(Hb_vals, float), indexing="ij")
    Bu = 0.5 * (Hb2D + Ha2D)
    Bc = 0.5 * (Hb2D - Ha2D)

    win = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)

    # --- Bc window ---
    if Bc_min is not None:
        win &= (Bc >= float(Bc_min))
    else:
        win &= (Bc >= 0.0)  # matches your default x_left behavior

    if Bc_max is not None:
        win &= (Bc <= float(Bc_max))

    # --- Bu window (respect bu_expand exactly as plotting does) ---
    if (Bu_min is not None) and (Bu_max is not None):
        c = 0.5 * (float(Bu_min) + float(Bu_max))
        hw = 0.5 * (float(Bu_max) - float(Bu_min)) * float(bu_expand)
        win &= (Bu >= (c - hw)) & (Bu <= (c + hw))
    elif Bu_max is not None:
        win &= (Bu >= (-float(Bu_max) * float(bu_expand))) & (Bu <= float(Bu_max))

    # compute vmax in window; fallback to global if window has nothing
    vals = np.abs(rho[win])
    if vals.size:
        vmax = float(np.nanpercentile(vals, float(pct)))
    else:
        vmax = float(np.nanpercentile(np.abs(rho), float(pct)))

    if (not np.isfinite(vmax)) or vmax <= 0:
        vmax = 1.0
    return vmax


def _rho_window_vmax_bu_bc(
    Ha_vals, Hb_vals, rho,
    pct: float = 99.0,
    Bu_min=None, Bu_max=None,
    Bc_min: float = 0.0,
    Bc_max=None,
) -> float:
    """
    Compute vmax from |rho| using ONLY points within the Bu/Bc window.
    Intended to keep profile normalization consistent with the Bu–Bc plot window.
    """
    rho = np.asarray(rho, float)

    Ha2D, Hb2D = np.meshgrid(np.asarray(Ha_vals, float), np.asarray(Hb_vals, float), indexing="ij")
    Bu = 0.5 * (Hb2D + Ha2D)
    Bc = 0.5 * (Hb2D - Ha2D)

    win = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)

    # Bc window
    if Bc_min is not None:
        win &= (Bc >= float(Bc_min))
    if Bc_max is not None:
        win &= (Bc <= float(Bc_max))

    # Bu window
    if (Bu_min is not None) and (Bu_max is not None):
        win &= (Bu >= float(Bu_min)) & (Bu <= float(Bu_max))
    elif Bu_max is not None:
        win &= (Bu >= -abs(float(Bu_max))) & (Bu <= abs(float(Bu_max)))

    vals = np.abs(rho[win])
    if vals.size:
        vmax = float(np.nanpercentile(vals, float(pct)))
    else:
        vmax = float(np.nanpercentile(np.abs(rho), float(pct)))

    if (not np.isfinite(vmax)) or vmax <= 0:
        vmax = 1.0
    return vmax


def plot_rho_BuBc(
    Ha_vals, Hb_vals, rho,
    Bu_min=None, Bu_max=None,
    Bc_min: Optional[float] = None,
    Bc_max=None,
    title: str = "Sample",
    show_contours: bool = False,
    contour_frac_step: float = 0.10,
    contour_alpha: float = 0.6,
    contour_lw: float = 0.4,
    pct: float = 99,
    figsize: Tuple[float, float] = (7, 6),
    dpi: int = 120,
    bu_expand: float = 1.0,
    add_origin_axes: bool = True,
    normalize_to_unit: bool = True,
    color_scale_version: int = 1,
    show_low_level_contours: bool = True,
    low_level_frac: float = 0.01,
    low_level_color: str = "0.1",
    low_level_alpha: float = 0.9,
    low_level_lw: float = 0.2,
    show: bool = True,
    close: bool = False,
    return_fig: bool = True,
    upsample_factor: int = 0,
    edge_mask_bc_bins: float = 0.0,
):
    """
    Plot rho in Bu/Bc space.

    Notes
    -----
    - `upsample_factor` applies optional plotting-only upsampling on the Ha/Hb
      grid before rotation into Bu/Bc space.
    - The color image is drawn with rotated cell EDGES so the plot reaches the
      zero-coercivity axis correctly.
    - Contours are drawn on the rotated cell CENTERS.
    """
    cmap = get_forc_cmap(color_scale_version)

    Ha0 = np.asarray(Ha_vals, float)
    Hb0 = np.asarray(Hb_vals, float)
    rho0 = np.asarray(rho, float).copy()

    if edge_mask_bc_bins is not None and float(edge_mask_bc_bins) > 0:
        Ha2D0, Hb2D0 = np.meshgrid(Ha0, Hb0, indexing="ij")
        Bc0 = 0.5 * (Hb2D0 - Ha2D0)

        dHb0 = float(np.nanmedian(np.diff(Hb0))) if len(Hb0) > 1 else np.nan
        dHa0 = float(np.nanmedian(np.diff(Ha0))) if len(Ha0) > 1 else dHb0
        if not np.isfinite(dHb0):
            dHb0 = 0.0
        if not np.isfinite(dHa0):
            dHa0 = dHb0

        h_edge = float(edge_mask_bc_bins) * max(dHb0, dHa0)
        if h_edge > 0:
            rho0[Bc0 < h_edge] = np.nan

    vmax = _rho_window_vmax(
        Ha0, Hb0, rho0,
        pct=pct,
        normalize_to_unit=normalize_to_unit,
        Bu_min=Bu_min, Bu_max=Bu_max,
        Bc_min=Bc_min, Bc_max=Bc_max,
        bu_expand=bu_expand,
    )
    if (not np.isfinite(vmax)) or vmax <= 0:
        vmax = 1.0

    if normalize_to_unit:
        norm = TwoSlopeNorm(vmin=-1.0, vcenter=0.0, vmax=1.0)
    else:
        norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)

    # Optional plotting-only upsampling on the native Ha/Hb grid
    upsample_factor = int(0 if upsample_factor is None else upsample_factor)
    if upsample_factor > 1:
        Ha_plot, Hb_plot, rho_plot_base = upsample_forc_grid(Ha0, Hb0, rho0, factor=upsample_factor)
    else:
        Ha_plot, Hb_plot, rho_plot_base = Ha0, Hb0, rho0

    rho_plot = rho_plot_base / vmax if normalize_to_unit else rho_plot_base

    # Centers for contours
    Ha2D_c, Hb2D_c = np.meshgrid(Ha_plot, Hb_plot, indexing="ij")
    Bu_cont = 0.5 * (Hb2D_c + Ha2D_c)
    Bc_cont = 0.5 * (Hb2D_c - Ha2D_c)

    # Edges for pcolormesh
    Ha_edges = _centers_to_edges_1d(Ha_plot)
    Hb_edges = _centers_to_edges_1d(Hb_plot)
    Ha2D_e, Hb2D_e = np.meshgrid(Ha_edges, Hb_edges, indexing="ij")
    Bu = 0.5 * (Hb2D_e + Ha2D_e)
    Bc = 0.5 * (Hb2D_e - Ha2D_e)

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    pm = ax.pcolormesh(Bc, Bu, rho_plot, shading="auto", cmap=cmap, norm=norm)
    ax.set_aspect("equal", adjustable="box")

    if add_origin_axes:
        ax.axhline(0, ls="-", lw=0.8, color="k", alpha=0.8)
        ax.axvline(0, ls="-", lw=0.8, color="k", alpha=0.8)

    if show_contours:
        if normalize_to_unit:
            Zc = rho_plot
            levels_main = _contour_levels(1.0, contour_frac_step)
            levels_low = _low_level_contours(low_level_frac)
        else:
            Zc = rho_plot
            levels_main = _contour_levels(vmax, contour_frac_step)
            levels_low = _low_level_contours(low_level_frac) * float(vmax)

        if levels_main is not None:
            ax.contour(Bc_cont, Bu_cont, Zc, levels=levels_main,
                       colors="k", linewidths=contour_lw, alpha=contour_alpha)

        if show_low_level_contours and levels_low.size:
            ax.contour(Bc_cont, Bu_cont, Zc, levels=levels_low,
                       colors=low_level_color, linewidths=low_level_lw, alpha=low_level_alpha)

    ax.set_xlabel("Bc (T)")
    ax.set_ylabel("Bu (T)")
    ax.set_title(title)

    x_left = 0.0 if Bc_min is None else float(Bc_min)
    if not np.isfinite(x_left):
        x_left = 0.0
    if x_left < 0:
        x_left = 0.0

    if Bc_max is not None:
        x_right = float(Bc_max)
        if np.isfinite(x_right):
            if x_right < x_left:
                x_left, x_right = x_right, x_left
            ax.set_xlim(x_left, x_right)
        else:
            ax.set_xlim(left=x_left)
    else:
        ax.set_xlim(left=x_left)

    if (Bu_min is not None) and (Bu_max is not None):
        c = 0.5 * (Bu_min + Bu_max)
        hw = 0.5 * (Bu_max - Bu_min) * float(bu_expand)
        ax.set_ylim(c - hw, c + hw)
    elif Bu_max is not None:
        ax.set_ylim(-float(Bu_max) * float(bu_expand), float(Bu_max))

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="4%", pad=0.08)
    cbar = fig.colorbar(pm, cax=cax)
    cbar.set_label(r"$\rho$")

    fig.tight_layout()

    if show:
        plt.show()
    if close:
        plt.close(fig)
    if return_fig:
        return fig, ax, pm, cbar
    return None

# ============================================================
# LOESS param guess helper
# ============================================================

def guess_loess_params(
    Ha_vals, Hb_vals, M_grid,
    span_Hb_T=None,
    span_Ha_T=None,
    target_n_eff: float = 60.0,
    min_pts_frac: float = 0.55,
    min_pts_min: int = 10,
    min_pts_ceiling: int = 200,
    max_rx: int = 25,
    max_ry: int = 25,
) -> Dict[str, object]:
    Ha_vals = np.asarray(Ha_vals, dtype=float)
    Hb_vals = np.asarray(Hb_vals, dtype=float)
    M = np.asarray(M_grid, dtype=float)

    dHb = float(np.nanmedian(np.diff(Hb_vals))) if len(Hb_vals) > 1 else np.nan
    dHa = float(np.nanmedian(np.diff(Ha_vals))) if len(Ha_vals) > 1 else dHb
    if not np.isfinite(dHb) or dHb <= 0:
        raise ValueError(f"Bad dHb inferred: {dHb}")
    if not np.isfinite(dHa) or dHa <= 0:
        raise ValueError(f"Bad dHa inferred: {dHa}")

    # Fill fraction is measured over the physical half-plane Hb >= Ha only.
    # Roughly half of the rectangular array is structurally empty, so counting
    # it would understate the local data density and inflate the window.
    physical = np.asarray(Hb_vals, float)[np.newaxis, :] >= np.asarray(Ha_vals, float)[:, np.newaxis]
    n_physical = int(np.count_nonzero(physical))
    fill_fraction = (float(np.count_nonzero(np.isfinite(M) & physical)) / n_physical
                     if n_physical else 0.0)
    fill_fraction = max(1e-6, fill_fraction)

    if (span_Hb_T is not None) and (span_Ha_T is not None):
        rx = max(1, int(np.ceil(float(span_Hb_T) / dHb)))
        ry = max(1, int(np.ceil(float(span_Ha_T) / dHa)))
        offsets = _build_offsets(rx, ry)
        n_candidate = float(offsets.shape[0])
        n_eff = n_candidate * fill_fraction

        min_pts = int(np.round(min_pts_frac * n_eff))
        min_pts = max(min_pts_min, min_pts)
        min_pts = min(min_pts_ceiling, min_pts)
        min_pts = min(min_pts, int(n_candidate) - 1)

        return {
            "dHb": dHb, "dHa": dHa,
            "span_Hb_T": float(rx * dHb),
            "span_Ha_T": float(ry * dHa),
            "rx": rx, "ry": ry,
            "n_candidate": n_candidate,
            "fill_fraction": fill_fraction,
            "n_eff_est": n_eff,
            "min_pts_suggested": int(min_pts),
        }

    rx = 2
    ry = 2
    aspect = dHb / dHa if np.isfinite(dHa) and dHa > 0 else 1.0

    best = None
    for _ in range(60):
        rx = min(rx, max_rx)
        ry = min(ry, max_ry)

        offsets = _build_offsets(rx, ry)
        n_candidate = float(offsets.shape[0])
        n_eff = n_candidate * fill_fraction

        best = (rx, ry, n_candidate, n_eff)
        if n_eff >= target_n_eff or (rx >= max_rx and ry >= max_ry):
            break

        rx_next = int(np.ceil(rx * 1.35))
        ry_next = int(np.ceil(ry * 1.35))
        ry_next = max(ry_next, int(np.ceil(rx_next * aspect)))

        rx, ry = rx_next, ry_next

    rx, ry, n_candidate, n_eff = best
    span_Hb_T = float(rx * dHb)
    span_Ha_T = float(ry * dHa)

    min_pts = int(np.round(min_pts_frac * n_eff))
    min_pts = max(min_pts_min, min_pts)
    min_pts = min(min_pts_ceiling, min_pts)
    min_pts = min(min_pts, int(n_candidate) - 1)

    return {
        "dHb": dHb, "dHa": dHa,
        "span_Hb_T": span_Hb_T,
        "span_Ha_T": span_Ha_T,
        "rx": int(rx), "ry": int(ry),
        "n_candidate": float(n_candidate),
        "fill_fraction": float(fill_fraction),
        "n_eff_est": float(n_eff),
        "min_pts_suggested": int(min_pts),
    }

# ============================================================
# One-call pipeline (THIS is what you use in the notebook)
# ============================================================

def run_forc_pipeline(
    path: str,
    sample_title: str = "Sample",
    # preprocessing
    cal_tol_T: float = 2e-3,
    drift_fit: str = "linear",
    endpoint_replace_n: int = 1,
    # segmentation knobs
    blank_sep: int = 2,
    jump_T: float = 0.05,
    cal_drop_T: float = 0.02,
    # loess controls
    smooth_strength: float = 1.0,
    min_pts_strength: float = 1.0,
    target_n_eff: float = 60.0,
    # plotting controls
    color_scale_version: int = 1,
    show_contours: bool = True,
    figsize: Tuple[float, float] = (7, 6),
    dpi: int = 120,
    export_dpi: int = 300,
    bu_expand: float = 1.0,
    # header/axis limits
    Bu_min: Optional[float] = None,
    Bu_max: Optional[float] = None,
    Bc_min: Optional[float] = None,
    Bc_max: Optional[float] = None,
    # hysteresis plotting
    plot_rho: bool = True,
    plot_hyst: bool = True,
    plot_fraction: float = 0.10,
    plot_hyst_dist: bool = False,
    plot_rho_ha_hb: bool = False,
    # endpoint replacement switches
    replace_first: bool = True,
    replace_last: bool = True,
    # lower-branch subtraction
    do_reference_subtract: bool = False,
    reference_curve: str = "lowest_reversal",
    plot_reference_subtracted_hyst: bool = False,
    # rho plotting normalization
    normalize_to_unit: bool = True,
    pct: float = 99.0,
    verbose: bool = True,
    # Bu/Bc display control
    display_upsample_factor: int = 0,
    edge_mask_bc_bins: float = 0.0,
    # Regridding in (B,M) space
    do_regrid: bool = False,
    B_step: Optional[float] = None,
    regrid_method: str = "linear",
    regrid_extrapolate: bool = False,
    # NEW: stacking controls
    stack: bool = False,
    stack_glob: Optional[str] = None,
    stack_method: str = "mean",   # "mean" or "median",
    export_magic: bool = True,
) -> Dict[str, object]:
    """
    Single-file mode
    ----------------
    - path is a file
    - stack=False

    Stacked mode
    ------------
    - path is a directory
    - stack=True
    - all matching files in that directory are prepared independently,
      gridded onto one common Ha–Hb grid, then stacked in M-space
      before LOESS rho calculation.
    """

    input_files = _list_stack_input_files(
        path,
        stack=stack,
        stack_glob=stack_glob,
        verbose=verbose,
    )

    prepared = [
        _prepare_single_input_for_rho(
            p,
            cal_tol_T=cal_tol_T,
            drift_fit=drift_fit,
            endpoint_replace_n=endpoint_replace_n,
            replace_first=replace_first,
            replace_last=replace_last,
            do_reference_subtract=do_reference_subtract,
            reference_curve=reference_curve,
            blank_sep=blank_sep,
            jump_T=jump_T,
            cal_drop_T=cal_drop_T,
            do_regrid=do_regrid,
            B_step=B_step,
            regrid_method=regrid_method,
            regrid_extrapolate=regrid_extrapolate,
            export_magic=(export_magic and not stack),
            verbose=verbose,
        )
        for p in input_files
    ]

    # Use header limits from first file for default plot bounds
    hdr_Bu_max = prepared[0]["header_limits"]["Bu_max"]
    hdr_Bc_max = prepared[0]["header_limits"]["Bc_max"]

    Bu_min_lim = Bu_min if Bu_min is not None else (-hdr_Bu_max if hdr_Bu_max is not None else None)
    Bu_max_lim = Bu_max if Bu_max is not None else ( hdr_Bu_max if hdr_Bu_max is not None else None)

    Bc_min_lim = 0.0 if Bc_min is None else float(Bc_min)
    Bc_lim = Bc_max if Bc_max is not None else hdr_Bc_max
    Bc_max_lim = Bc_lim

    # For plotting raw hysteresis curves, use the first file as representative
    first_item = prepared[0]
    segs_display = first_item["segs_display"]
    segs_rho     = first_item["segs_rho"]
    forcs_display = first_item["forcs_display"]
    forcs_rho     = first_item["forcs_rho"]

    # Curves that entered the distribution calculation, used for the optional
    # overlay in hysteresis space. For a stack this is the first member, which
    # is also what the other representative-curve plots show.
    forcs_for_rho_corr = first_item["forcs_for_rho_corr"]

    if len(prepared) == 1:
        # -----------------------------
        # original single-file behavior
        # -----------------------------
        Ha_vals_used, Hb_vals_used, M_grid_used, dHb_used, dHa_used = build_forc_grid(
            forcs_for_rho_corr,
            verbose=verbose,
        )

        stack_counts = np.isfinite(M_grid_used).astype(int)

    else:
        # -----------------------------
        # stacked multi-file behavior
        # -----------------------------
        grid_spec = _infer_common_stack_grid(prepared, B_step=B_step)

        Ha_vals_used = None
        Hb_vals_used = None
        stacked_grids = []

        for item in prepared:
            Ha_vals_i, Hb_vals_i, M_grid_i, dHb_i, dHa_i = build_forc_grid_regridded(
                item["forcs_for_rho_corr"],
                Hb_step=grid_spec["Hb_step"],
                Ha_step=grid_spec["Ha_step"],
                regrid_method=regrid_method,
                regrid_extrapolate=regrid_extrapolate,
                Hb_min=grid_spec["Hb_min"],
                Hb_max=grid_spec["Hb_max"],
                Ha_min=grid_spec["Ha_min"],
                Ha_max=grid_spec["Ha_max"],
                verbose=verbose,
            )
            Ha_vals_used = Ha_vals_i
            Hb_vals_used = Hb_vals_i
            dHb_used = dHb_i
            dHa_used = dHa_i
            stacked_grids.append(M_grid_i)

        M_grid_used, stack_counts = _stack_nan_grids(
            stacked_grids,
            method=stack_method,
        )

        if verbose:
            finite_cells = int(np.isfinite(M_grid_used).sum())
            print(
                f"Stacked {len(stacked_grids)} M-grids using method={stack_method!r}. "
                f"Finite stacked cells: {finite_cells}"
            )

    # LOESS params + rho
    g = guess_loess_params(
        Ha_vals_used,
        Hb_vals_used,
        M_grid_used,
        target_n_eff=float(target_n_eff),
    )
    span_Hb = float(g["span_Hb_T"]) * float(smooth_strength)
    span_Ha = float(g["span_Ha_T"]) * float(smooth_strength)
    min_pts = int(round(float(g["min_pts_suggested"]) * float(min_pts_strength)))

    rho = loess_rho_from_grid_fast(
        Ha_vals_used, Hb_vals_used, M_grid_used,
        span_Hb_T=span_Hb,
        span_Ha_T=span_Ha,
        min_pts=min_pts,
    )

    # Raw FORC curves
    if plot_hyst:
        title = f"{sample_title} — FORC curves (H vs M)"
        if len(prepared) > 1:
            title += " [first stack member]"
        plot_forc_curves_hysteresis(
            forcs_display,
            title=title,
            plot_fraction=float(plot_fraction),
            figsize=figsize,
            dpi=dpi,
        )

    if do_reference_subtract and plot_reference_subtracted_hyst:
        title = f"{sample_title} — FORC curves (H vs M) [lower-branch subtracted]"
        if len(prepared) > 1:
            title += " [first stack member]"
        plot_forc_curves_hysteresis(
            forcs_rho,
            title=title,
            plot_fraction=float(plot_fraction),
            figsize=figsize,
            dpi=dpi,
        )

    fig_hyst_dist = ax_hyst_dist = sc_hyst_dist = cbar_hyst_dist = None
    if plot_hyst_dist:
        title = f"{sample_title} — FORC distribution in hysteresis space"
        if len(prepared) > 1:
            title += " [stacked M-grid]"
        fig_hyst_dist, ax_hyst_dist, sc_hyst_dist, cbar_hyst_dist = plot_forc_distribution_hysteresis_space(
            Ha_vals_used,
            Hb_vals_used,
            M_grid_used,
            rho,
            forcs=forcs_for_rho_corr,
            title=title,
            plot_fraction=float(plot_fraction),
            figsize=figsize,
            dpi=dpi,
            color_scale_version=color_scale_version,
            normalize_to_unit=normalize_to_unit,
            pct=pct,
            return_fig=True,
        )

    if plot_rho_ha_hb:
        plot_rho_HaHb(
            Ha_vals_used, Hb_vals_used, rho,
            title=sample_title,
            show_contours=show_contours,
            figsize=figsize,
            dpi=dpi,
            normalize_to_unit=normalize_to_unit,
            pct=pct,
            color_scale_version=color_scale_version,
        )

    fig_rho = ax_rho = pm = cbar = None
    if plot_rho:
        fig_rho, ax_rho, pm, cbar = plot_rho_BuBc(
            Ha_vals_used, Hb_vals_used, rho,
            Bu_min=Bu_min_lim, Bu_max=Bu_max_lim,
            Bc_min=Bc_min_lim,
            Bc_max=Bc_lim,
            title=sample_title,
            show_contours=show_contours,
            figsize=figsize,
            dpi=dpi,
            bu_expand=bu_expand,
            normalize_to_unit=normalize_to_unit,
            pct=pct,
            color_scale_version=color_scale_version,
            show=True,
            close=False,
            return_fig=True,
            upsample_factor=display_upsample_factor,
            edge_mask_bc_bins=edge_mask_bc_bins,
        )

    return {
        "sample_title": sample_title,
        "fig_rho": fig_rho,
        "ax_rho": ax_rho,
        "pm_rho": pm,
        "cbar_rho": cbar,

        "fig_hyst_dist": fig_hyst_dist,
        "ax_hyst_dist": ax_hyst_dist,
        "sc_hyst_dist": sc_hyst_dist,
        "cbar_hyst_dist": cbar_hyst_dist,
        
        "input_path": str(path),
        "input_files": [str(p) for p in input_files],
        "n_input_files": len(input_files),
        "stack_used": (len(input_files) > 1),
        "stack_method": (stack_method if len(input_files) > 1 else None),
        "stack_counts": stack_counts,

        "segs_display": segs_display,
        "segs_rho": segs_rho,
        "forcs_display": forcs_display,
        "forcs_rho": forcs_rho,

        "Ha_vals_used": Ha_vals_used,
        "Hb_vals_used": Hb_vals_used,
        "M_grid_used": M_grid_used,
        "rho": rho,
        "dHb_used": dHb_used,
        "dHa_used": dHa_used,

        "header_limits": {"Bu_max": hdr_Bu_max, "Bc_max": hdr_Bc_max},
        "n_calibration_points": first_item["n_calibration_points"],
        "drift_corrected": first_item["drift_corrected"],
        "drift_fit": drift_fit if first_item["drift_corrected"] else None,
        "plot_limits": {
            "Bu_min_lim": Bu_min_lim,
            "Bu_max_lim": Bu_max_lim,
            "Bc_min_lim": Bc_min_lim,
            "Bc_max_lim": Bc_max_lim,
        },
        "loess_params": {
            **g,
            "span_Hb_T_used": span_Hb,
            "span_Ha_T_used": span_Ha,
            "min_pts_used": min_pts,
        },

        "dpi": int(dpi) if dpi is not None else 120,
        "export_dpi": int(export_dpi) if export_dpi is not None else 300,
    }

# ============================================================
# Profiles / slices (use LOESS-smoothed rho input)
# ============================================================

def bu_bc_from_ha_hb(Ha_vals: np.ndarray, Hb_vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    Ha2D, Hb2D = np.meshgrid(np.asarray(Ha_vals, float), np.asarray(Hb_vals, float), indexing="ij")
    Bu = 0.5 * (Hb2D + Ha2D)
    Bc = 0.5 * (Hb2D - Ha2D)
    return Bu, Bc

def estimate_steps(Ha_vals: np.ndarray, Hb_vals: np.ndarray) -> Tuple[float, float]:
    Ha_vals = np.asarray(Ha_vals, float)
    Hb_vals = np.asarray(Hb_vals, float)
    dHb = float(np.nanmedian(np.diff(Hb_vals))) if Hb_vals.size > 1 else np.nan
    dHa = float(np.nanmedian(np.diff(Ha_vals))) if Ha_vals.size > 1 else dHb
    dBu = 0.5 * (abs(dHb) + abs(dHa))
    dBc = 0.5 * (abs(dHb) + abs(dHa))
    return dBu, dBc

def bin_profile(
    x: np.ndarray,
    y: np.ndarray,
    x_min: float,
    x_max: float,
    n_bins: int = 400,
    agg: Literal["mean", "sum"] = "mean",
) -> Tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, float)
    y = np.asarray(y, float)

    edges = np.linspace(float(x_min), float(x_max), int(n_bins) + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    good = np.isfinite(x) & np.isfinite(y) & (x >= x_min) & (x <= x_max)
    if not np.any(good):
        return centers, np.full_like(centers, np.nan, dtype=float)

    xg = x[good]
    yg = y[good]
    bi = np.digitize(xg, edges) - 1
    keep = (bi >= 0) & (bi < n_bins)
    bi = bi[keep]
    yg = yg[keep]

    if agg == "sum":
        out = np.zeros(n_bins, dtype=float)
        counts = np.zeros(n_bins, dtype=float)
        np.add.at(out, bi, yg)
        np.add.at(counts, bi, 1.0)
        out[counts == 0] = np.nan
        return centers, out

    sums = np.zeros(n_bins, dtype=float)
    counts = np.zeros(n_bins, dtype=float)
    np.add.at(sums, bi, yg)
    np.add.at(counts, bi, 1.0)
    out = np.full(n_bins, np.nan, dtype=float)
    ok = counts > 0
    out[ok] = sums[ok] / counts[ok]
    return centers, out

def gaussian_smooth_1d_nan(y: np.ndarray, sigma_bins: Optional[float] = 2.0) -> np.ndarray:
    if sigma_bins is None or sigma_bins <= 0:
        return np.asarray(y, float)
    try:
        from scipy.ndimage import gaussian_filter1d
    except Exception:
        return np.asarray(y, float)

    y = np.asarray(y, float)
    mask = np.isfinite(y).astype(float)
    y0 = np.where(np.isfinite(y), y, 0.0)
    num = gaussian_filter1d(y0, sigma=float(sigma_bins), mode="nearest")
    den = gaussian_filter1d(mask, sigma=float(sigma_bins), mode="nearest")

    out = np.full_like(y, np.nan, dtype=float)
    ok = den > 0
    out[ok] = num[ok] / den[ok]
    return out

def resolve_profile_bounds(
    Bu: np.ndarray,
    Bc: np.ndarray,
    rho: np.ndarray,
    Bu_min: Optional[float] = None,
    Bu_max: Optional[float] = None,
    Bc_min: float = 0.0,
    Bc_max: Optional[float] = None,
) -> Dict[str, float]:
    rho = np.asarray(rho, float)
    valid = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)
    if not np.any(valid):
        raise ValueError("rho has no finite values — cannot infer default bounds.")

    if Bu_min is None:
        Bu_min = float(np.nanmin(Bu[valid]))
    if Bu_max is None:
        Bu_max = float(np.nanmax(Bu[valid]))

    if Bc_max is None:
        pos = valid & (Bc >= Bc_min)
        Bc_max = float(np.nanmax(Bc[pos])) if np.any(pos) else float(np.nanmax(Bc[valid]))

    return {"Bu_min": float(Bu_min), "Bu_max": float(Bu_max), "Bc_min": float(Bc_min), "Bc_max": float(Bc_max)}

_EMPTY_PEAK = {"peak_x": np.nan, "peak_y": np.nan, "half_y": np.nan,
               "left_x": np.nan, "right_x": np.nan, "fwhm": np.nan}


def profile_peak_and_fwhm(x: np.ndarray, y: np.ndarray, use_abs: bool = True) -> Dict[str, float]:
    """Locate the peak of a 1D profile and measure its full width at half maximum.

    The half-maximum crossings are found by linear interpolation between the
    bracketing samples, so the width does not depend on the bin spacing as
    strongly as a nearest-sample estimate would.

    Args:
        x: Profile abscissa, typically ``Bc`` or ``Bu`` in tesla.
        y: Profile values.
        use_abs: Locate the peak in ``|y|`` rather than ``y``. Useful when a
            profile crosses zero and the feature of interest may be negative.

    Returns:
        dict: ``peak_x`` and ``peak_y`` at the maximum, ``half_y`` and the
        interpolated ``left_x``/``right_x`` crossings, and the ``fwhm``. All
        entries are NaN where they cannot be determined -- fewer than three
        finite samples, a non-positive peak, or a profile that does not fall
        back through half maximum on one side.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if x.size < 3:
        return dict(_EMPTY_PEAK)

    yy = np.abs(y) if use_abs else y
    k = int(np.nanargmax(yy))
    peak_x, peak_y = float(x[k]), float(yy[k])
    if not np.isfinite(peak_y) or peak_y <= 0:
        return {**_EMPTY_PEAK, "peak_x": peak_x, "peak_y": peak_y}

    half = 0.5 * peak_y

    left = np.nan
    for i in range(k, 0, -1):
        if yy[i] >= half > yy[i - 1]:
            left = float(np.interp(half, [yy[i - 1], yy[i]], [x[i - 1], x[i]]))
            break

    right = np.nan
    for i in range(k, x.size - 1):
        if yy[i] >= half > yy[i + 1]:
            right = float(np.interp(half, [yy[i + 1], yy[i]], [x[i + 1], x[i]]))
            break

    fwhm = (float(right - left)
            if (np.isfinite(left) and np.isfinite(right) and right >= left) else np.nan)
    return {"peak_x": peak_x, "peak_y": peak_y, "half_y": float(half),
            "left_x": left, "right_x": right, "fwhm": fwhm}

def slice_profile_smoothed(
    Ha_vals: np.ndarray,
    Hb_vals: np.ndarray,
    rho: np.ndarray,
    mode: Literal["Bc", "Bu"],
    target: float,
    window: Optional[float] = None,
    x_min: Optional[float] = None,
    x_max: Optional[float] = None,
    bin_width: Optional[float] = None,
    n_bins: Optional[int] = None,
    smooth_sigma_bins: Optional[float] = 2.0,
    agg: Literal["mean", "sum"] = "mean",
) -> Dict[str, object]:
    """Extract a smoothed one-dimensional slice through the FORC distribution.

    Args:
        Ha_vals: Reversal-field grid coordinates in tesla.
        Hb_vals: Applied-field grid coordinates in tesla.
        rho: FORC distribution on the ``(Ha, Hb)`` grid.
        mode: ``"Bu"`` for a horizontal profile, rho against ``Bc`` at fixed
            ``Bu``; ``"Bc"`` for a vertical profile, rho against ``Bu`` at
            fixed ``Bc``.
        target: The fixed ``Bu`` (mode ``"Bu"``) or ``Bc`` (mode ``"Bc"``) of
            the slice, in tesla.
        window: Half-width in tesla of the band of grid cells contributing to
            the slice. Defaults to one grid step.
        x_min: Lower bound of the profile axis. Defaults to the finite data
            range.
        x_max: Upper bound of the profile axis.
        bin_width: Bin width in tesla along the profile axis. Defaults to the
            grid step, so bins resolve the data rather than the plotted range.
        n_bins: Explicit bin count, overriding ``bin_width`` when given.
        smooth_sigma_bins: Gaussian sigma for the profile smoothing, expressed
            in **bins**, so its physical width scales with ``bin_width``.
        agg: Aggregation applied to grid cells falling in the same bin.

    Returns:
        dict: ``x`` and ``y`` profile arrays, the ``xlabel``, the ``target``
        and ``window`` used, the axis bounds, the resulting ``bin_width``, and
        ``peak`` metrics from :func:`profile_peak_and_fwhm`.

    Notes:
        Binning follows the requested window rather than a fixed count over
        the full measured range. A FORC measurement whose lowest reversal
        curve reaches -1.2 T spans a far wider range than a typical plotted
        window, and a fixed count over that range quantizes the reported peak
        position and dilutes the peak amplitude.
    """
    rho = np.asarray(rho, float)
    Bu, Bc = bu_bc_from_ha_hb(Ha_vals, Hb_vals)
    dBu, dBc = estimate_steps(Ha_vals, Hb_vals)

    valid = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)
    if not np.any(valid):
        raise ValueError("rho has no finite values.")

    bounds = resolve_profile_bounds(Bu, Bc, rho, Bu_min=None, Bu_max=None, Bc_min=0.0, Bc_max=None)

    if mode == "Bc":
        if window is None:
            window = 1.0 * dBc
        sel = valid & (np.abs(Bc - float(target)) <= float(window))
        x = Bu[sel]
        y = rho[sel]
        xlabel = "Bu (T)"
        x_min_d, x_max_d = bounds["Bu_min"], bounds["Bu_max"]
        step = dBu
    elif mode == "Bu":
        if window is None:
            window = 1.0 * dBu
        sel = valid & (np.abs(Bu - float(target)) <= float(window))
        x = Bc[sel]
        y = rho[sel]
        xlabel = "Bc (T)"
        x_min_d, x_max_d = bounds["Bc_min"], bounds["Bc_max"]
        step = dBc
    else:
        raise ValueError("mode must be 'Bc' or 'Bu'")

    if x_min is None:
        x_min = x_min_d
    if x_max is None:
        x_max = x_max_d
    x_min, x_max = float(x_min), float(x_max)
    if not (x_max > x_min):
        raise ValueError(f"Profile axis is empty: x_min={x_min}, x_max={x_max}.")

    if n_bins is None:
        width = float(step) if bin_width is None else float(bin_width)
        if not np.isfinite(width) or width <= 0:
            raise ValueError("bin_width must be a positive finite value.")
        n_bins = max(2, int(round((x_max - x_min) / width)))
    n_bins = int(n_bins)
    resolved_bin_width = (x_max - x_min) / n_bins

    x_centers, y_b = bin_profile(x, y, x_min, x_max, n_bins=n_bins, agg=agg)
    y_s = gaussian_smooth_1d_nan(y_b, sigma_bins=smooth_sigma_bins)
    pk = profile_peak_and_fwhm(x_centers, y_s, use_abs=True)

    return {
        "mode": mode,
        "target": float(target),
        "window": float(window),
        "x": x_centers,
        "y": y_s,
        "xlabel": xlabel,
        "x_min": x_min,
        "x_max": x_max,
        "n_bins": n_bins,
        "bin_width": resolved_bin_width,
        "peak": pk,
    }

def find_bounded_peak_rho(Ha_vals, Hb_vals, rho, Bu_min=None, Bu_max=None, Bc_min=None, Bc_max=None):
    rho = np.asarray(rho, float)
    Bu, Bc = bu_bc_from_ha_hb(Ha_vals, Hb_vals)

    valid = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)
    if Bu_min is not None:
        valid &= (Bu >= float(Bu_min))
    if Bu_max is not None:
        valid &= (Bu <= float(Bu_max))
    if Bc_min is not None:
        valid &= (Bc >= float(Bc_min))
    if Bc_max is not None:
        valid &= (Bc <= float(Bc_max))

    if not np.any(valid):
        raise ValueError("No finite rho values inside bounds.")

    rr = np.where(valid, rho, np.nan)
    idx = np.nanargmax(rr)

    return {
        "bu": float(Bu.ravel()[idx]),
        "bc": float(Bc.ravel()[idx]),
        "rho": float(rho.ravel()[idx]),
        "flat_index": int(idx),
    }

def bounded_peak_profiles(
    Ha_vals,
    Hb_vals,
    rho,
    Bu_min=None,
    Bu_max=None,
    Bc_min=None,
    Bc_max=None,
    smooth_sigma_bins=2.0,
    bin_width=None,
):
    """Extract the horizontal and vertical profiles through the bounded peak.

    Args:
        Ha_vals: Reversal-field grid coordinates in tesla.
        Hb_vals: Applied-field grid coordinates in tesla.
        rho: FORC distribution on the ``(Ha, Hb)`` grid.
        Bu_min: Lower ``Bu`` bound of the region searched for the peak, and of
            the vertical profile axis.
        Bu_max: Upper ``Bu`` bound.
        Bc_min: Lower ``Bc`` bound of the region searched for the peak, and of
            the horizontal profile axis.
        Bc_max: Upper ``Bc`` bound.
        smooth_sigma_bins: Gaussian sigma, in bins, for the profiles.
        bin_width: Bin width in tesla. Defaults to the grid step.

    Returns:
        dict: the ``peak`` location, the ``horizontal`` profile of rho against
        ``Bc`` at the peak ``Bu``, and the ``vertical`` profile of rho against
        ``Bu`` at the peak ``Bc``.
    """
    pk = find_bounded_peak_rho(
        Ha_vals, Hb_vals, rho,
        Bu_min=Bu_min, Bu_max=Bu_max,
        Bc_min=Bc_min, Bc_max=Bc_max
    )

    prof_bc = slice_profile_smoothed(
        Ha_vals, Hb_vals, rho,
        mode="Bu",
        target=pk["bu"],
        x_min=Bc_min,
        x_max=Bc_max,
        bin_width=bin_width,
        smooth_sigma_bins=smooth_sigma_bins,
    )

    prof_bu = slice_profile_smoothed(
        Ha_vals, Hb_vals, rho,
        mode="Bc",
        target=pk["bc"],
        x_min=Bu_min,
        x_max=Bu_max,
        bin_width=bin_width,
        smooth_sigma_bins=smooth_sigma_bins,
    )

    return {
        "peak": pk,
        "horizontal": prof_bc,
        "vertical": prof_bu,
    }

def track_bu_offset_vs_bc(
    Ha_vals,
    Hb_vals,
    rho,
    Bu_min=None,
    Bu_max=None,
    Bc_min=None,
    Bc_max=None,
    bc_window=None,
    rho_frac_cutoff=0.001,
    n_centers=100,
):
    """Locate the crest of the FORC distribution in each coercivity bin.

    In each ``Bc`` bin the ``Bu`` position of the maximum of ``rho`` is
    recorded. For a distribution whose ridge drifts in ``Bu`` with coercivity
    -- hematite is a common case -- these positions quantify the vertical
    asymmetry, and ``rho`` along them is the ridge-following profile returned
    by :func:`ridge_profile`.

    Args:
        Ha_vals: Reversal-field grid coordinates in tesla.
        Hb_vals: Applied-field grid coordinates in tesla.
        rho: FORC distribution on the ``(Ha, Hb)`` grid.
        Bu_min: Lower bound of the ``Bu`` search band. Defaults to the finite
            data range.
        Bu_max: Upper bound of the ``Bu`` search band.
        Bc_min: Lowest coercivity bin centre. Defaults to 0.
        Bc_max: Highest coercivity bin centre. Defaults to the finite data
            range.
        bc_window: Width in tesla of each coercivity bin. Defaults to one
            grid step.
        rho_frac_cutoff: Bins whose maximum falls below this fraction of the
            distribution maximum are skipped, so the crest is not tracked
            into noise.
        n_centers: Number of coercivity bins.

    Returns:
        dict: ``bc``, ``bu`` and ``rho`` arrays giving the crest coordinates
        and amplitude, plus the ``bc_window`` and ``rho_frac_cutoff`` used.
    """
    rho = np.asarray(rho, float)
    Bu, Bc = bu_bc_from_ha_hb(Ha_vals, Hb_vals)
    _, dBc = estimate_steps(Ha_vals, Hb_vals)

    if bc_window is None:
        bc_window = float(dBc)

    # Resolve open bounds against the finite data rather than failing on None.
    finite = np.isfinite(rho) & np.isfinite(Bu) & np.isfinite(Bc)
    if not np.any(finite):
        raise ValueError("rho has no finite values inside the grid.")
    bounds = resolve_profile_bounds(
        Bu, Bc, rho,
        Bu_min=Bu_min, Bu_max=Bu_max,
        Bc_min=0.0 if Bc_min is None else float(Bc_min),
        Bc_max=Bc_max,
    )
    Bu_min, Bu_max = bounds["Bu_min"], bounds["Bu_max"]
    Bc_min, Bc_max = bounds["Bc_min"], bounds["Bc_max"]

    in_band = finite & (Bu >= Bu_min) & (Bu <= Bu_max) & (Bc >= Bc_min) & (Bc <= Bc_max)
    if not np.any(in_band):
        raise ValueError("No finite rho values inside the requested Bu/Bc bounds.")

    # Reference the cutoff to the maximum inside the search band, so that a
    # strong feature outside the band cannot suppress the whole track. Where
    # the band holds no positive signal there is no ridge to follow, and a
    # cutoff scaled from a negative maximum would exclude everything; fall
    # back to tracking the least-negative cell in each bin instead.
    band_max = float(np.nanmax(np.where(in_band, rho, np.nan)))
    rho_cut = float(rho_frac_cutoff) * band_max if band_max > 0 else -np.inf
    centers = np.linspace(Bc_min, Bc_max, int(n_centers))

    out_bc, out_bu, out_rho = [], [], []
    for bc0 in centers:
        sel = (
            in_band
            & (Bc >= bc0 - bc_window / 2)
            & (Bc < bc0 + bc_window / 2)
            & (rho >= rho_cut)
        )
        if not np.any(sel):
            continue
        idx = np.nanargmax(np.where(sel, rho, np.nan))
        out_bc.append(float(Bc.ravel()[idx]))
        out_bu.append(float(Bu.ravel()[idx]))
        out_rho.append(float(rho.ravel()[idx]))

    return {
        "bc": np.asarray(out_bc, dtype=float),
        "bu": np.asarray(out_bu, dtype=float),
        "rho": np.asarray(out_rho, dtype=float),
        "bc_window": float(bc_window),
        "rho_frac_cutoff": float(rho_frac_cutoff),
        "ranges": {"Bu_min": Bu_min, "Bu_max": Bu_max,
                   "Bc_min": Bc_min, "Bc_max": Bc_max},
    }


def ridge_profile(
    Ha_vals,
    Hb_vals,
    rho,
    Bu_min=None,
    Bu_max=None,
    Bc_min=None,
    Bc_max=None,
    bc_window=None,
    rho_frac_cutoff: float = 0.01,
    n_centers: int = 150,
    smooth_sigma_bins: Optional[float] = 2.5,
    amplitude_cutoff: float = 0.02,
) -> Dict[str, object]:
    """Extract rho along the crest of the FORC distribution.

    A conventional horizontal profile cuts the distribution at a single fixed
    ``Bu``. Where the crest drifts in ``Bu`` with coercivity, such a cut
    undersamples the ridge away from the peak and understates the width of the
    coercivity distribution. This function follows the crest instead: the
    ``Bu`` of the maximum of ``rho`` is located in each coercivity bin (see
    :func:`track_bu_offset_vs_bc`), the crest position and amplitude are
    lightly smoothed, and the high-coercivity tail is trimmed where the crest
    amplitude falls below ``amplitude_cutoff`` of its maximum -- beyond that
    point the per-bin maximum is tracking noise and produces spurious hooks.

    Args:
        Ha_vals: Reversal-field grid coordinates in tesla.
        Hb_vals: Applied-field grid coordinates in tesla.
        rho: FORC distribution on the ``(Ha, Hb)`` grid.
        Bu_min: Lower bound of the ``Bu`` band searched for the crest.
        Bu_max: Upper bound of the ``Bu`` band searched for the crest.
        Bc_min: Lowest coercivity bin centre.
        Bc_max: Highest coercivity bin centre.
        bc_window: Width in tesla of each coercivity bin.
        rho_frac_cutoff: Per-bin amplitude floor passed to the tracker.
        n_centers: Number of coercivity bins along the crest.
        smooth_sigma_bins: Gaussian sigma, in bins, applied to the tracked
            crest position and amplitude. The grid quantizes the per-bin
            maximum, so a little smoothing is usually wanted; pass None to
            disable.
        amplitude_cutoff: Fraction of the maximum crest amplitude below which
            the tail is trimmed.

    Returns:
        dict: ``bc`` and ``bu`` crest coordinates, ``rho`` along the crest,
        the unsmoothed ``bu_raw``/``rho_raw``, ``peak`` metrics from
        :func:`profile_peak_and_fwhm` evaluated along the crest, ``arc_length``
        measured along the crest in tesla, and the ``track`` dict the profile
        was built from.

    Notes:
        For a strongly sloping ridge, the full width at half maximum measured
        against ``bc`` understates the extent along the crest itself;
        ``arc_length`` is provided so the profile can be reported against
        distance along the crest instead.
    """
    track = track_bu_offset_vs_bc(
        Ha_vals, Hb_vals, rho,
        Bu_min=Bu_min, Bu_max=Bu_max, Bc_min=Bc_min, Bc_max=Bc_max,
        bc_window=bc_window, rho_frac_cutoff=rho_frac_cutoff,
        n_centers=n_centers,
    )

    bc = track["bc"]
    bu = gaussian_smooth_1d_nan(track["bu"], sigma_bins=smooth_sigma_bins)
    amp = gaussian_smooth_1d_nan(track["rho"], sigma_bins=smooth_sigma_bins)

    if amp.size and np.any(np.isfinite(amp)):
        keep = amp >= float(amplitude_cutoff) * np.nanmax(amp)
        if np.any(keep):
            last = int(np.max(np.flatnonzero(keep)))
            sl = slice(0, last + 1)
            bc, bu, amp = bc[sl], bu[sl], amp[sl]
            track = {**track,
                     "bc": track["bc"][sl],
                     "bu": track["bu"][sl],
                     "rho": track["rho"][sl]}

    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(bc), np.diff(bu)))]) \
        if bc.size > 1 else np.zeros_like(bc)

    return {
        "bc": bc,
        "bu": bu,
        "rho": amp,
        "bu_raw": track["bu"],
        "rho_raw": track["rho"],
        "arc_length": arc,
        "peak": profile_peak_and_fwhm(bc, amp, use_abs=False),
        "peak_arc": profile_peak_and_fwhm(arc, amp, use_abs=False),
        "amplitude_cutoff": float(amplitude_cutoff),
        "smooth_sigma_bins": smooth_sigma_bins,
        "track": track,
    }

# ============================================================
# Bounded-peak profile helpers
# ============================================================

def build_bounded_peak_profile_bundle(
    Ha_vals,
    Hb_vals,
    rho,
    Bu_min=None,
    Bu_max=None,
    Bc_min=None,
    Bc_max=None,
    bc_window=None,
    bu_window=None,
    rho_frac_cutoff=0.02,
    n_centers=120,
    smooth_sigma_bins=2.0,
    bin_width=None,
    dpi: int = 120,
):
    """Assemble the peak profiles and the tracked ridge into one result.

    Args:
        Ha_vals: Reversal-field grid coordinates in tesla.
        Hb_vals: Applied-field grid coordinates in tesla.
        rho: FORC distribution on the ``(Ha, Hb)`` grid.
        Bu_min: Lower ``Bu`` bound of the region of interest.
        Bu_max: Upper ``Bu`` bound.
        Bc_min: Lower ``Bc`` bound.
        Bc_max: Upper ``Bc`` bound.
        bc_window: Coercivity bin width for ridge tracking, in tesla.
        bu_window: Retained for call compatibility; unused.
        rho_frac_cutoff: Per-bin amplitude floor for ridge tracking.
        n_centers: Number of coercivity bins along the ridge.
        smooth_sigma_bins: Gaussian sigma, in bins, for the profiles.
        bin_width: Profile bin width in tesla. Defaults to the grid step.
        dpi: Display resolution recorded for downstream plotting.

    Returns:
        dict: the :func:`bounded_peak_profiles` result with ``track``,
        ``ridge``, ``ranges``, ``meta`` and ``dpi`` added.
    """
    bundle = bounded_peak_profiles(
        Ha_vals, Hb_vals, rho,
        Bu_min=Bu_min, Bu_max=Bu_max,
        Bc_min=Bc_min, Bc_max=Bc_max,
        smooth_sigma_bins=smooth_sigma_bins,
        bin_width=bin_width,
    )

    bundle["ridge"] = ridge_profile(
        Ha_vals, Hb_vals, rho,
        Bu_min=Bu_min, Bu_max=Bu_max,
        Bc_min=Bc_min, Bc_max=Bc_max,
        bc_window=bc_window,
        rho_frac_cutoff=rho_frac_cutoff,
        n_centers=n_centers,
        smooth_sigma_bins=smooth_sigma_bins,
    )
    bundle["track"] = bundle["ridge"]["track"]
    bundle["ranges"] = {
        "Bu_min": Bu_min, "Bu_max": Bu_max,
        "Bc_min": Bc_min, "Bc_max": Bc_max,
    }
    bundle["meta"] = {
        "smooth_sigma_bins": smooth_sigma_bins,
        "bin_width": bin_width,
    }
    bundle["dpi"] = {"dpi": dpi}
    return bundle

def print_bounded_peak_summary(bundle):
    pk = bundle["peak"]
    print("Peak rho point inside bounded plot area:")
    print(f"  Bu = {pk['bu']:.6f} T")
    print(f"  Bc = {pk['bc']:.6f} T")
    print(f"  rho = {pk['rho']:.6f}")

    pk_bc = bundle["horizontal"].get("peak", {})
    pk_bu = bundle["vertical"].get("peak", {})

    if np.isfinite(float(pk_bu.get("peak_x", np.nan))):
        print("")
        print("Additional smoothing is applied to the profiles, which changes the peak rho, Bc and Bu values:")
        print(f"  Peak Bu on profile = {float(pk_bu['peak_x']):.6f} T")
    if np.isfinite(float(pk_bc.get("peak_x", np.nan))):
        print(f"  Peak Bc on profile = {float(pk_bc['peak_x']):.6f} T")
    if np.isfinite(float(pk_bu.get("fwhm", np.nan))):
        print(f"  Bu-profile FWHM = {float(pk_bu['fwhm']):.6f} T")
        print(" ")

def plot_bounded_peak_profiles(
    bundle,
    title_prefix: str = "",
    figsize: Tuple[float, float] = (10.5, 4.5),
    dpi: int = 120,
    show: bool = True,
    return_fig: bool = False,
):
    """
    Two-panel plot:
      left  = rho vs Bc at Bu = bounded peak Bu
      right = rho vs Bu at Bc = bounded peak Bc

    New options:
      show=False      -> do not call plt.show()
      return_fig=True -> return the figure handle for export
    """
    prof_bc = bundle["horizontal"]
    prof_bu = bundle["vertical"]

    fig, axs = plt.subplots(1, 2, figsize=figsize, dpi=dpi)

    # ---------------- Bc profile ----------------
    ax = axs[0]
    x = np.asarray(prof_bc["x"], float)
    y = np.asarray(prof_bc["y"], float)
    ax.plot(x, y, lw=1)
    ax.axhline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.axvline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.set_xlim(float(prof_bc["x_min"]), float(prof_bc["x_max"]))
    ax.set_xlabel("Bc (T)")
    ax.set_ylabel(r"$\rho$")
    ax.set_title(f"{title_prefix}Horizontal at Bu = {float(prof_bc['target']):.6g} T".strip(), fontsize=10)

    pk = prof_bc.get("peak", {})
    peak_bc = float(pk.get("peak_x", np.nan))
    peak_rho_bc = float(pk.get("peak_y", np.nan))
    if np.isfinite(peak_bc):
        ax.axvline(peak_bc, ls="--", lw=1.0, color="0.5", alpha=0.9)
        ax.text(
            0.4, 0.98,
            f"Peak Bc = {peak_bc:.4f} T\nrho(max) = {peak_rho_bc:.4f}",
            transform=ax.transAxes,
            va="top", ha="left",
        )

    # ---------------- Bu profile ----------------
    ax = axs[1]
    x = np.asarray(prof_bu["x"], float)
    y = np.asarray(prof_bu["y"], float)
    ax.plot(x, y, lw=1)
    ax.axhline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.axvline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.set_xlim(float(prof_bu["x_min"]), float(prof_bu["x_max"]))
    ax.set_xlabel("Bu (T)")
    ax.set_ylabel(r"$\rho$")
    ax.set_title(f"{title_prefix}Vertical at Bc = {float(prof_bu['target']):.6g} T".strip(), fontsize=10)

    pk = prof_bu.get("peak", {})
    peak_bu = float(pk.get("peak_x", np.nan))
    peak_rho_bu = float(pk.get("peak_y", np.nan))
    fwhm = float(pk.get("fwhm", np.nan))
    if np.isfinite(peak_bu):
        ax.axvline(peak_bu, ls="--", lw=1.0, color="0.5", alpha=0.9)
        txt = f"Peak Bu = {peak_bu:.4f} T\nrho(max) = {peak_rho_bu:.4f}"
        if np.isfinite(fwhm):
            txt += f"\nFWHM = {fwhm:.4f} T"
        ax.text(0.68, 0.98, txt, transform=ax.transAxes, va="top", ha="left")

    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.88, wspace=0.25)
    if show:
        plt.show()
    if return_fig:
        return fig
    return None

def plot_bu_offset_tracking(bundle, title="Tracking Bu offset with coercivity", figsize=(6.8, 4.8), dpi=120):
    """
    Plot local-peak Bu vs Bc in mT.
    Drops the last point, which is often an edge artifact.
    """
    track = bundle["track"]

    bc = np.asarray(track.get("bc", []), float)
    bu = np.asarray(track.get("bu", []), float)

    ok = np.isfinite(bc) & np.isfinite(bu)
    bc = bc[ok]
    bu = bu[ok]

    # drop the last point as requested
    if bc.size > 1:
        bc = bc[:-1]
        bu = bu[:-1]

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    ax.plot(1000.0 * bc, 1000.0 * bu, lw=1.2)
    ax.axhline(0, ls="--", lw=0.8, color="0.4")

    rng = bundle.get("ranges", {})
    bc_min = rng.get("Bc_min", None)
    bc_max = rng.get("Bc_max", None)
    if (bc_min is not None) and (bc_max is not None):
        ax.set_xlim(1000.0 * float(bc_min), 1000.0 * float(bc_max))

    ax.set_xlabel("Bc of local peak rho (mT)")
    ax.set_ylabel("Bu of local peak rho (mT)")
    ax.set_title(title)
    plt.tight_layout()
    plt.show()

# ============================================================
# Figure Export Utilities (cross-platform)
# ============================================================

def export_current_figure_from_out(
    out,
    filename: Optional[str] = None,
    dpi: Optional[int] = None,
    close: bool = False,
):
    """
    Export the main FORC figure(s) from run_forc_pipeline(...) output.

    Accepts either:
      - a single output dict
      - a list of output dicts (batch mode)

    If dpi is None, uses out['export_dpi'] when present, otherwise 300.
    """
    if isinstance(out, list):
        paths = []
        for one_out in out:
            one_filename = None
            if filename is not None and len(out) == 1:
                one_filename = filename
            paths.append(
                _export_current_figure_single(
                    one_out,
                    filename=one_filename,
                    dpi=dpi,
                    close=close,
                )
            )
        return paths

    return _export_current_figure_single(
        out,
        filename=filename,
        dpi=dpi,
        close=close,
    )

def export_forc_profiles_txt(
    bundle,
    specimen_name: str = "specimen",
    out_dir: Optional[PathLike] = None,
    drop_last_tracking_point: bool = True,
):
    """
    Export the three bounded-peak workflow curves:
      1) horizontal profile: rho vs Bc
      2) vertical profile:   rho vs Bu
      3) tracking curve:     Bu vs Bc
    """
    export_dir = as_path(out_dir) if out_dir is not None else Path("profile_exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    def _write_xy(path: Path, header: str, arr: np.ndarray):
        ensure_parent_dir(path)
        np.savetxt(path, arr, fmt="%.10g", delimiter="\t", header=header, comments="")
        print(f"Saved: {path}")

    prof_bc = bundle.get("horizontal", None)
    if prof_bc is not None:
        x = np.asarray(prof_bc.get("x", []), float)
        y = np.asarray(prof_bc.get("y", []), float)
        target_bu = float(prof_bc.get("target", np.nan))
        cut_str = f"{target_bu:.6f}".rstrip("0").rstrip(".") if np.isfinite(target_bu) else "unknown"
        fname = safe_filename(f"{specimen_name}_rho_vs_Bc_at_Bu_{cut_str}") + ".txt"
        _write_xy(export_dir / fname, "Bc_T\trho", np.column_stack([x, y]))

    prof_bu = bundle.get("vertical", None)
    if prof_bu is not None:
        x = np.asarray(prof_bu.get("x", []), float)
        y = np.asarray(prof_bu.get("y", []), float)
        target_bc = float(prof_bu.get("target", np.nan))
        cut_str = f"{target_bc:.6f}".rstrip("0").rstrip(".") if np.isfinite(target_bc) else "unknown"
        fname = safe_filename(f"{specimen_name}_rho_vs_Bu_at_Bc_{cut_str}") + ".txt"
        _write_xy(export_dir / fname, "Bu_T\trho", np.column_stack([x, y]))

    track = bundle.get("track", None)
    if track is not None:
        bc = np.asarray(track.get("bc", []), float)
        bu = np.asarray(track.get("bu", []), float)
        rho = np.asarray(track.get("rho", []), float)
        ok = np.isfinite(bc) & np.isfinite(bu)
        if rho.shape == bc.shape:
            ok &= np.isfinite(rho)
        bc = bc[ok]
        bu = bu[ok]
        rho = rho[ok] if rho.shape == ok.shape else np.full(bc.shape, np.nan)
        if drop_last_tracking_point and bc.size > 1:
            bc = bc[:-1]
            bu = bu[:-1]
            rho = rho[:-1]
        fname = safe_filename(f"{specimen_name}_Bu_vs_Bc_tracking") + ".txt"
        _write_xy(export_dir / fname, "Bc_T\tBu_T\trho", np.column_stack([bc, bu, rho]))

def plot_auto_forc_profiles(
    out: Dict[str, object],
    smooth_sigma_bins: Optional[float] = 1.0,
    pct: float = 100.0,
    rho_frac_cutoff: float = 0.01,
    n_centers: int = 200,
    export_txt: bool = True,
    export_png: bool = True,
    print_summary: bool = True,
    title_prefix: Optional[str] = None,
    figsize: Tuple[float, float] = (10.5, 4.5),
    dpi=120,
    export_dpi=300,
    return_data: bool = False,
):
    Ha_vals = np.asarray(out.get("Ha_vals_used"), float)
    Hb_vals = np.asarray(out.get("Hb_vals_used"), float)
    rho = np.asarray(out["rho"], float)

    Bu_min_lim = out["plot_limits"]["Bu_min_lim"]
    Bu_max_lim = out["plot_limits"]["Bu_max_lim"]
    Bc_min_lim = out["plot_limits"]["Bc_min_lim"]
    Bc_max_lim = out["plot_limits"]["Bc_max_lim"]

    sample_title = out.get("sample_title", "Sample")
    profiles_dir = get_forc_profiles_dir(out)

    vmax_win = _rho_window_vmax_bu_bc(
        Ha_vals, Hb_vals, rho,
        pct=float(pct),
        Bu_min=Bu_min_lim,
        Bu_max=Bu_max_lim,
        Bc_min=Bc_min_lim,
        Bc_max=Bc_max_lim,
    )
    rho_u = rho / vmax_win

    bundle = build_bounded_peak_profile_bundle(
        Ha_vals, Hb_vals, rho_u,
        Bu_min=Bu_min_lim,
        Bu_max=Bu_max_lim,
        Bc_min=Bc_min_lim,
        Bc_max=Bc_max_lim,
        rho_frac_cutoff=float(rho_frac_cutoff),
        n_centers=int(n_centers),
        smooth_sigma_bins=smooth_sigma_bins,
        dpi=dpi,
    )

    if print_summary:
        print_bounded_peak_summary(bundle)

    if export_txt:
        export_forc_profiles_txt(bundle, specimen_name=sample_title, out_dir=profiles_dir)

    if title_prefix is None:
        title_prefix = f"{sample_title} — "

    fig = plot_bounded_peak_profiles(bundle, title_prefix=title_prefix, show=False, return_fig=True)

    png_path = None
    if export_png:
        png_path = export_figure(fig, filename=f"{sample_title}_auto_profiles.png", out_dir=profiles_dir, dpi=export_dpi, close=False)
        print(f"Saved: {png_path}")

    plt.show()

    if return_data:
        return {
            "bundle": bundle,
            "rho_u": rho_u,
            "vmax_win": vmax_win,
            "profiles_png_path": str(png_path) if png_path is not None else None,
            "profiles_dir": str(profiles_dir),
        }
    return None

def plot_custom_forc_profiles(
    out: Dict[str, object],
    user_Bu: float = 0.0,
    user_Bc: float = 0.02,
    smooth_sigma_bins: Optional[float] = 1.0,
    pct: float = 100.0,
    rho_frac_cutoff: float = 0.01,
    n_centers: int = 200,
    n_profile_pts: int = 400,
    export_txt: bool = False,
    export_custom_txt: bool = True,
    export_png: bool = True,
    print_summary: bool = True,
    figsize: Tuple[float, float] = (10.5, 4.5),
    dpi: int = 120,
    export_dpi: Optional[int] = None,
    return_data: bool = False,
):
    Ha_vals = np.asarray(out.get("Ha_vals_used"), float)
    Hb_vals = np.asarray(out.get("Hb_vals_used"), float)
    rho = np.asarray(out["rho"], float)

    Bu_min_lim = out["plot_limits"]["Bu_min_lim"]
    Bu_max_lim = out["plot_limits"]["Bu_max_lim"]
    Bc_min_lim = out["plot_limits"]["Bc_min_lim"]
    Bc_max_lim = out["plot_limits"]["Bc_max_lim"]

    sample_title = out.get("sample_title", "Sample")
    profiles_dir = get_forc_profiles_dir(out)
    export_dpi = int(out.get("export_dpi", 300)) if export_dpi is None else int(export_dpi)

    def _export_xy_profile_txt(x, y, specimen_name, suffix, xlabel, ylabel="rho_norm", out_dir=None) -> Path:
        filename = safe_filename(f"{specimen_name}_{suffix}") + ".txt"
        out_path = as_path(out_dir) / filename if out_dir is not None else as_path(filename)
        ensure_parent_dir(out_path)
        arr = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
        np.savetxt(out_path, arr, fmt="%.10g", delimiter="	", header=f"{xlabel}	{ylabel}", comments="")
        return out_path

    vmax_win = _rho_window_vmax_bu_bc(
        Ha_vals, Hb_vals, rho,
        pct=float(pct),
        Bu_min=Bu_min_lim,
        Bu_max=Bu_max_lim,
        Bc_min=Bc_min_lim,
        Bc_max=Bc_max_lim,
    )
    rho_u = rho / vmax_win

    bundle = build_bounded_peak_profile_bundle(
        Ha_vals, Hb_vals, rho_u,
        Bu_min=Bu_min_lim,
        Bu_max=Bu_max_lim,
        Bc_min=Bc_min_lim,
        Bc_max=Bc_max_lim,
        rho_frac_cutoff=float(rho_frac_cutoff),
        n_centers=int(n_centers),
        smooth_sigma_bins=smooth_sigma_bins,
        dpi=dpi,
    )

    if export_txt:
        export_forc_profiles_txt(bundle, specimen_name=sample_title, out_dir=profiles_dir)

    Ha2D, Hb2D = np.meshgrid(Ha_vals, Hb_vals, indexing="ij")
    Bu2D = 0.5 * (Hb2D + Ha2D)
    Bc2D = 0.5 * (Hb2D - Ha2D)
    win = np.isfinite(rho_u)
    if Bu_min_lim is not None:
        win &= (Bu2D >= float(Bu_min_lim))
    if Bu_max_lim is not None:
        win &= (Bu2D <= float(Bu_max_lim))
    if Bc_min_lim is not None:
        win &= (Bc2D >= float(Bc_min_lim))
    if Bc_max_lim is not None:
        win &= (Bc2D <= float(Bc_max_lim))
    if not np.any(win):
        raise ValueError("No finite rho values found inside the bounded Bu/Bc window.")

    rho_win = np.where(win, rho_u, np.nan)
    imax = np.nanargmax(rho_win)
    peak_Bu = float(Bu2D.ravel()[imax])
    peak_Bc = float(Bc2D.ravel()[imax])
    peak_rho = float(rho_u.ravel()[imax])

    interp = RegularGridInterpolator((Ha_vals, Hb_vals), rho_u, bounds_error=False, fill_value=np.nan)

    def _smooth_profile(y, sigma):
        if sigma in (None, 0, 0.0):
            return np.asarray(y, float)
        return gaussian_smooth_1d_nan(y, sigma_bins=float(sigma))

    def _sample_bu_profile_at_bc(Bc_fixed, Bu_min, Bu_max, npts=400):
        Bu_axis = np.linspace(Bu_min, Bu_max, int(npts))
        Hb_s = Bu_axis + float(Bc_fixed)
        Ha_s = Bu_axis - float(Bc_fixed)
        prof = interp(np.column_stack([Ha_s, Hb_s]))
        return Bu_axis, _smooth_profile(prof, smooth_sigma_bins)

    def _sample_bc_profile_at_bu(Bu_fixed, Bc_min, Bc_max, npts=400):
        Bc_axis = np.linspace(Bc_min, Bc_max, int(npts))
        Hb_s = float(Bu_fixed) + Bc_axis
        Ha_s = float(Bu_fixed) - Bc_axis
        prof = interp(np.column_stack([Ha_s, Hb_s]))
        return Bc_axis, _smooth_profile(prof, smooth_sigma_bins)

    Bu_axis_peak, prof_bu_peak = _sample_bu_profile_at_bc(peak_Bc, Bu_min_lim, Bu_max_lim, npts=n_profile_pts)
    Bu_axis_user, prof_bu_user = _sample_bu_profile_at_bc(user_Bc, Bu_min_lim, Bu_max_lim, npts=n_profile_pts)
    Bc_axis_peak, prof_bc_peak = _sample_bc_profile_at_bu(peak_Bu, Bc_min_lim, Bc_max_lim, npts=n_profile_pts)
    Bc_axis_user, prof_bc_user = _sample_bc_profile_at_bu(user_Bu, Bc_min_lim, Bc_max_lim, npts=n_profile_pts)

    peak_profile_bc = profile_peak_and_fwhm(Bc_axis_peak, prof_bc_peak, use_abs=False)
    peak_profile_bu = profile_peak_and_fwhm(Bu_axis_peak, prof_bu_peak, use_abs=False)
    user_profile_bc = profile_peak_and_fwhm(Bc_axis_user, prof_bc_user, use_abs=False)
    user_profile_bu = profile_peak_and_fwhm(Bu_axis_user, prof_bu_user, use_abs=False)

    peak_profile_Bc = float(peak_profile_bc.get("peak_x", np.nan))
    peak_profile_Bu = float(peak_profile_bu.get("peak_x", np.nan))
    peak_profile_FWHM = float(peak_profile_bu.get("fwhm", np.nan))

    user_profile_Bc = float(user_profile_bc.get("peak_x", np.nan))
    user_profile_Bu = float(user_profile_bu.get("peak_x", np.nan))
    user_profile_FWHM = float(user_profile_bu.get("fwhm", np.nan))

    custom_export_paths = {}
    if export_custom_txt:
        specimen_name_custom = f"{sample_title}_custom"
        p1 = _export_xy_profile_txt(Bu_axis_user, prof_bu_user, specimen_name_custom, f"Bu_profile_at_Bc_{user_Bc:.6f}T", "Bu_T", out_dir=profiles_dir)
        p2 = _export_xy_profile_txt(Bc_axis_user, prof_bc_user, specimen_name_custom, f"Bc_profile_at_Bu_{user_Bu:.6f}T", "Bc_T", out_dir=profiles_dir)
        custom_export_paths = {"custom_bu_profile_path": str(p1), "custom_bc_profile_path": str(p2)}
        if print_summary:
            print(f"Saved custom Bu profile to: {p1}")
            print(f"Saved custom Bc profile to: {p2}")

    if print_summary:
        # print("\nBounded peak inside plot window:")
        # print(f"  Peak Bu = {peak_Bu:.6f} T")
        # print(f"  Peak Bc = {peak_Bc:.6f} T")
        # print(f"  Peak rho = {peak_rho:.6f}")
        # if np.isfinite(peak_profile_Bu):
        #     print(f"  Peak profile Bu = {peak_profile_Bu:.6f} T")
        # if np.isfinite(peak_profile_Bc):
        #     print(f"  Peak profile Bc = {peak_profile_Bc:.6f} T")
        # if np.isfinite(peak_profile_FWHM):
        #     print(f"  Peak Bu-profile FWHM = {peak_profile_FWHM:.6f} T")
        if np.isfinite(user_profile_Bu) or np.isfinite(user_profile_Bc) or np.isfinite(user_profile_FWHM):
            print("\nCustom profiles:")
            if np.isfinite(user_profile_Bu):
                print(f"  Custom profile Peak Bu = {user_profile_Bu:.6f} T")
            if np.isfinite(user_profile_Bc):
                print(f"  Custom profile Peak Bc = {user_profile_Bc:.6f} T")
            if np.isfinite(user_profile_FWHM):
                print(f"  Custom Bu-profile FWHM = {user_profile_FWHM:.6f} T")

    fig, axes = plt.subplots(1, 2, figsize=figsize, dpi=dpi)

    ax = axes[0]
    # ax.plot(Bc_axis_peak * 1e3, prof_bc_peak, ls="--", lw=1.5, color="0.5",
    #         label=f"Peak Bu slice at Bu={peak_Bu:.2f} T")
    ax.plot(Bc_axis_user, prof_bc_user, lw=1.2)
    ax.axhline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.axvline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.set_xlim(Bc_min_lim, Bc_max_lim)
    # if np.isfinite(peak_profile_Bc):
    #     ax.axvline(peak_profile_Bc, ls="--", lw=1.2, color="0.5", alpha=0.9)
    if np.isfinite(user_profile_Bc):
        ax.axvline(user_profile_Bc, ls="--", lw=1.0, color="0.5", alpha=0.9)
    txt_bc = []
    # if np.isfinite(peak_profile_Bc):
    #     txt_bc.append(f"Peak Bc = {peak_profile_Bc:.2f} T")
    if np.isfinite(user_profile_Bc):
        # txt_bc.append(f"Custom Bc slice at Bu={user_Bu:.4g} T")
        txt_bc.append(f"Peak Bc = {user_profile_Bc:.4f} T")
    if txt_bc:
        ax.text(
            0.4, 0.98, "\n".join(txt_bc),
            transform=ax.transAxes,
            va="top", ha="left",
        )
    ax.set_xlabel("Bc (T)")
    ax.set_ylabel(r"Normalized $\rho$")
    ax.set_title(f"{sample_title} - Horizontal at Bu = {user_Bu:.6g} T".strip(), fontsize=10)
    # ax.legend()

    ax = axes[1]
    # ax.plot(Bu_axis_peak * 1e3, prof_bu_peak, ls="--", lw=1.5, color="0.5",
    #         label=f"Peak Bc slice at Bc={peak_Bc*1e3:.2f} mT")
    ax.plot(Bu_axis_user, prof_bu_user, lw=1.2)
    ax.axhline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.axvline(0, ls="--", lw=0.8, color="0.4", alpha=0.8)
    ax.set_xlim(Bu_min_lim, Bu_max_lim)
    # if np.isfinite(peak_profile_Bu):
    #     ax.axvline(peak_profile_Bu, ls="--", lw=1.2, color="0.5", alpha=0.9)
    if np.isfinite(user_profile_Bu):
        ax.axvline(user_profile_Bu, ls="--", lw=1.0, color="0.5", alpha=0.9)
    # if np.isfinite(user_profile_FWHM):
    #     x_left = float(user_profile_bu.get("left_x", np.nan))
    #     x_right = float(user_profile_bu.get("right_x", np.nan))
    #     half_y = float(user_profile_bu.get("half_y", np.nan))
    #     if np.isfinite(x_left) and np.isfinite(x_right) and np.isfinite(half_y):
    #         ax.hlines(half_y, x_left, x_right, ls="--", lw=1.2, color="0.5", alpha=0.9)
    txt_bu = []
    # if np.isfinite(peak_profile_Bu):
    #     txt_bu.append(f"Peak Bu = {peak_profile_Bu*1e3:.2f} mT")
    if np.isfinite(user_profile_Bu):
        # txt_bu.append(f"Custom Bu slice at Bc={user_Bc:.4f} T")
        txt_bu.append(f"Peak Bu = {user_profile_Bu:.4f} T")
    if np.isfinite(user_profile_FWHM):
        txt_bu.append(f"FWHM = {user_profile_FWHM:.4f} T")
    if txt_bu:
        ax.text(
            0.68, 0.98, "\n".join(txt_bu),
            transform=ax.transAxes,
            va="top", ha="left",
        )
    ax.set_xlabel("Bu (T)")
    ax.set_ylabel(r"Normalized $\rho$")
    ax.set_title(f"{sample_title} - Vertical at Bc = {user_Bc:.6g} T".strip(), fontsize=10)
    # ax.legend()
    
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.12, top=0.88, wspace=0.25)

    png_path = None
    if export_png:
        png_path = export_figure(fig, filename=f"{sample_title}_custom_profiles.png", out_dir=profiles_dir, dpi=export_dpi, close=False)
        print(f"Saved: {png_path}")

    plt.show()

    if return_data:
        return {
            "bundle": bundle,
            "peak_Bu": peak_Bu,
            "peak_Bc": peak_Bc,
            "peak_rho": peak_rho,
            "peak_profile_Bu": peak_profile_Bu,
            "peak_profile_Bc": peak_profile_Bc,
            "peak_profile_FWHM": peak_profile_FWHM,
            "user_Bu": float(user_Bu),
            "user_Bc": float(user_Bc),
            "user_profile_Bu": user_profile_Bu,
            "user_profile_Bc": user_profile_Bc,
            "user_profile_FWHM": user_profile_FWHM,
            "Bu_axis_peak": Bu_axis_peak,
            "prof_bu_peak": prof_bu_peak,
            "Bu_axis_user": Bu_axis_user,
            "prof_bu_user": prof_bu_user,
            "Bc_axis_peak": Bc_axis_peak,
            "prof_bc_peak": prof_bc_peak,
            "Bc_axis_user": Bc_axis_user,
            "prof_bc_user": prof_bc_user,
            "profiles_dir": str(profiles_dir),
            "profiles_png_path": str(png_path) if png_path is not None else None,
            **custom_export_paths,
        }
    return None


def export_figure(
    fig,
    filename: str,
    out_dir: PathLike,
    dpi: int = 300,
    close: bool = False,
) -> Path:
    """
    Save a matplotlib figure to out_dir/filename.
    """
    out_dir = as_path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / safe_filename(filename)
    ensure_parent_dir(out_path)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    if close:
        plt.close(fig)
    return out_path



# ============================================================
# Unified mode wrapper + list-aware output helpers
# ============================================================

# Preserve the original single/stack implementation
_run_forc_pipeline_core = run_forc_pipeline
_plot_auto_forc_profiles_core = plot_auto_forc_profiles
_plot_custom_forc_profiles_core = plot_custom_forc_profiles

def _is_out_list(obj) -> bool:
    return isinstance(obj, list)

def _iter_outs(obj):
    if isinstance(obj, list):
        for item in obj:
            yield item
    else:
        yield obj

def _derive_common_sample_title(files) -> str:
    """Best-effort common stem for stacked inputs."""
    stems = [Path(f).stem for f in files]
    if not stems:
        return "stack"
    if len(stems) == 1:
        return stems[0]
    common = os.path.commonprefix(stems)
    common = common.rstrip(" _-.")
    return common if common else "stack"


def _run_magic_pipeline(
    path: PathLike,
    sample_title: Optional[str],
    stack_method: str,
    kwargs: Dict[str, object],
):
    """Dispatch a MagIC table to single, stacked, or specimen-batch processing."""
    magic_path = as_path(path)
    kwargs = dict(kwargs)
    kwargs.pop("export_magic", None)
    runs = read_magic_forc_runs(magic_path)
    by_specimen: Dict[str, List[Dict[str, object]]] = {}
    for run in runs:
        by_specimen.setdefault(str(run["specimen"]), []).append(run)

    if len(by_specimen) > 1:
        detected_mode = "b"
    elif len(runs) > 1:
        detected_mode = "s"
    else:
        detected_mode = "i"

    verbose = bool(kwargs.get("verbose", True))
    if verbose:
        details = ", ".join(f"{name}: {len(items)} run(s)" for name, items in by_specimen.items())
        print(f"MagIC import detected mode={detected_mode!r} | {details}")

    outputs = []
    with tempfile.TemporaryDirectory(prefix="forcme_magic_") as temp_name:
        temp_root = Path(temp_name)
        for specimen_index, (specimen, specimen_runs) in enumerate(by_specimen.items(), start=1):
            specimen_dir = temp_root / f"specimen_{specimen_index}"
            specimen_dir.mkdir(parents=True, exist_ok=True)
            synthetic_files = []
            for run_index, run in enumerate(specimen_runs, start=1):
                synthetic_path = specimen_dir / f"run_{run_index}.txt"
                synthetic_files.append(_write_magic_run_as_forc(run, synthetic_path))

            use_stack = len(synthetic_files) > 1
            core_path = str(specimen_dir if use_stack else synthetic_files[0])
            one_out = _run_forc_pipeline_core(
                path=core_path,
                sample_title=sample_title or specimen,
                stack=use_stack,
                stack_glob="*.txt",
                stack_method=stack_method,
                export_magic=False,
                **kwargs,
            )
            # Replace temporary implementation details with durable source metadata.
            one_out["input_path"] = str(magic_path)
            one_out["input_files"] = [str(magic_path)]
            one_out["n_input_files"] = 1
            one_out["magic_import"] = True
            one_out["magic_detected_mode"] = detected_mode
            one_out["magic_specimen_mode"] = "s" if use_stack else "i"
            one_out["magic_specimen"] = specimen
            one_out["magic_run_ids"] = [str(run["run_id"]) for run in specimen_runs]
            one_out["n_magic_runs"] = len(specimen_runs)
            outputs.append(one_out)

    return outputs if detected_mode == "b" else outputs[0]

def run_forc_pipeline(
    path: str,
    sample_title: Optional[str] = None,
    mode: str = "i",
    file_type: str = "*.txt",
    stack_method: str = "mean",
    **kwargs,
):
    """
    Unified public pipeline.

    Parameters
    ----------
    mode : {"i", "s", "b", "m"}
        i = single file
        s = stacked processing over matching files in a directory
        b = batch processing of each matching file in a directory
        m = MagIC measurements file; automatically selects i, s, or b from
            specimen, experiment, and sequence fields
    file_type : str
        Glob used to discover files for stack/batch modes.
    sample_title : str or None
        Optional explicit override. When None or blank, titles are derived automatically:
          i = filename stem
          b = each filename stem
          s = common stem across matched files
    """
    mode_l = str(mode).strip().lower()
    if mode_l not in {"i", "s", "b", "m"}:
        raise ValueError("mode must be 'i', 's', 'b', or 'm'.")

    # Backward-compatibility: ignore legacy args if passed
    kwargs.pop("stack", None)
    kwargs.pop("stack_glob", None)

    user_title = None if sample_title is None else str(sample_title).strip()
    if user_title == "":
        user_title = None

    if mode_l == "m":
        return _run_magic_pipeline(
            path=path,
            sample_title=user_title,
            stack_method=stack_method,
            kwargs=kwargs,
        )

    if mode_l == "i":
        auto_title = Path(path).stem
        return _run_forc_pipeline_core(
            path=path,
            sample_title=user_title or auto_title,
            stack=False,
            stack_glob=file_type,
            stack_method=stack_method,
            **kwargs,
        )

    if mode_l == "s":
        files = _list_stack_input_files(
            path=path,
            stack=True,
            stack_glob=file_type,
            verbose=bool(kwargs.get("verbose", True)),
        )
        auto_title = _derive_common_sample_title(files)
        return _run_forc_pipeline_core(
            path=path,
            sample_title=user_title or auto_title,
            stack=True,
            stack_glob=file_type,
            stack_method=stack_method,
            **kwargs,
        )

    # Batch mode
    files = _list_stack_input_files(
        path=path,
        stack=True,
        stack_glob=file_type,
        verbose=bool(kwargs.get("verbose", True)),
    )
    outs = []
    for fp in files:
        auto_title = Path(fp).stem
        one_out = _run_forc_pipeline_core(
            path=str(fp),
            sample_title=user_title or auto_title,
            stack=False,
            stack_glob=file_type,
            stack_method=stack_method,
            **kwargs,
        )
        outs.append(one_out)
    return outs

def _export_current_figure_single(
    out: Dict[str, object],
    filename: Optional[str] = None,
    dpi: Optional[int] = None,
    close: bool = False,
) -> Path:
    """
    Export the main FORC figure from one run_forc_pipeline(...) output dict
    into FORC_figures.
    """
    fig = out.get("fig_rho", None)
    if fig is None:
        raise ValueError("No 'fig_rho' found in out.")

    figures_dir = get_forc_figures_dir(out)

    if filename is None:
        filename = f"{out.get('sample_title', 'Sample')}_FORC.png"

    if dpi is None:
        dpi = int(out.get("export_dpi", 300))

    out_path = export_figure(
        fig,
        filename=filename,
        out_dir=figures_dir,
        dpi=int(dpi),
        close=close,
    )
    print(f"Saved: {out_path}")
    return out_path

def plot_auto_forc_profiles(
    out,
    smooth_sigma_bins: Optional[float] = 1.0,
    pct: float = 100.0,
    rho_frac_cutoff: float = 0.01,
    n_centers: int = 200,
    export_txt: bool = True,
    export_png: bool = True,
    print_summary: bool = True,
    title_prefix: Optional[str] = None,
    figsize: Tuple[float, float] = (10.5, 4.5),
    dpi=120,
    export_dpi=300,
    return_data: bool = False,
):
    """
    List-aware wrapper for automatic profile plotting.
    """
    if _is_out_list(out):
        results = []
        for one_out in out:
            results.append(
                _plot_auto_forc_profiles_core(
                    one_out,
                    smooth_sigma_bins=smooth_sigma_bins,
                    pct=pct,
                    rho_frac_cutoff=rho_frac_cutoff,
                    n_centers=n_centers,
                    export_txt=export_txt,
                    export_png=export_png,
                    print_summary=print_summary,
                    title_prefix=title_prefix,
                    figsize=figsize,
                    dpi=dpi,
                    export_dpi=export_dpi,
                    return_data=return_data,
                )
            )
        return results if return_data else None

    return _plot_auto_forc_profiles_core(
        out,
        smooth_sigma_bins=smooth_sigma_bins,
        pct=pct,
        rho_frac_cutoff=rho_frac_cutoff,
        n_centers=n_centers,
        export_txt=export_txt,
        export_png=export_png,
        print_summary=print_summary,
        title_prefix=title_prefix,
        figsize=figsize,
        dpi=dpi,
        export_dpi=export_dpi,
        return_data=return_data,
    )

def plot_custom_forc_profiles(
    out,
    user_Bu: float = 0.0,
    user_Bc: float = 0.02,
    smooth_sigma_bins: Optional[float] = 1.0,
    pct: float = 100.0,
    rho_frac_cutoff: float = 0.01,
    n_centers: int = 200,
    n_profile_pts: int = 400,
    export_txt: bool = False,
    export_custom_txt: bool = True,
    export_png: bool = True,
    print_summary: bool = True,
    figsize: Tuple[float, float] = (10.5, 4.5),
    dpi: int = 120,
    export_dpi: int = 300,
    return_data: bool = False,
):
    """
    List-aware wrapper for custom profile plotting.
    """
    if _is_out_list(out):
        results = []
        for one_out in out:
            results.append(
                _plot_custom_forc_profiles_core(
                    one_out,
                    user_Bu=user_Bu,
                    user_Bc=user_Bc,
                    smooth_sigma_bins=smooth_sigma_bins,
                    pct=pct,
                    rho_frac_cutoff=rho_frac_cutoff,
                    n_centers=n_centers,
                    n_profile_pts=n_profile_pts,
                    export_txt=export_txt,
                    export_custom_txt=export_custom_txt,
                    export_png=export_png,
                    print_summary=print_summary,
                    figsize=figsize,
                    dpi=dpi,
                    export_dpi=export_dpi,
                    return_data=return_data,
                )
            )
        return results if return_data else None

    return _plot_custom_forc_profiles_core(
        out,
        user_Bu=user_Bu,
        user_Bc=user_Bc,
        smooth_sigma_bins=smooth_sigma_bins,
        pct=pct,
        rho_frac_cutoff=rho_frac_cutoff,
        n_centers=n_centers,
        n_profile_pts=n_profile_pts,
        export_txt=export_txt,
        export_custom_txt=export_custom_txt,
        export_png=export_png,
        print_summary=print_summary,
        figsize=figsize,
        dpi=dpi,
        export_dpi=export_dpi,
        return_data=return_data,
    )
