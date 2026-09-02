"""
The conversion registry: every instrument-file converter, described once.

``convert_2_magic`` holds the converters; each one has its own keyword names for
the same ideas (``mag_file`` / ``magfile`` / ``agm_file``; ``location`` /
``locname``; ``samp_con`` / ``sample_naming_con``; ``phi`` / ``labfield_phi``)
and prints what it does instead of returning it. This module describes the
converters in one vocabulary — a :class:`Format` with the :class:`Field`\\ s a
user must fill in and a map from those canonical names to the function's own —
so that a form can be generated from the description, a script can call
:func:`convert_files` with a plain dict, and one test can iterate the registry
over the example files in ``data_files/convert_2_magic``.

Nothing here imports a UI. Usable from a notebook::

    from pmagpy import convert_registry as reg
    result = reg.convert_files(reg.FORMATS["sio"], ["sio_af_example.dat"],
                               {"codelist": ["AF"], "location": "Hawaii", "specnum": 1},
                               dir_path="my_study")
    print(result.message); print(result.log)

Each file is converted on its own into a scratch directory and the tables are
then combined into ``dir_path`` — so many CIT or PMD files become one
``measurements.txt`` — replacing what is there, or adding to it with ``append``.

The registry is where new instruments join: a converter for a Lakeshore VSM, a
MicroMag 3900 or a Kappabridge export is a function in ``convert_2_magic`` that
takes a file, an output directory and named output tables, plus one
:class:`Format` here with an example file under ``data_files`` — the tests then
run it with everything else. Nothing in the registry assumes demagnetization
data; a format may write measurements only (``mini``, the IODP measurement
converters) or no measurements at all (``iodp_samples``).
"""
from __future__ import annotations

import contextlib
import inspect
import io
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import pandas as pd

from pmagpy import convert_2_magic as convert

MAGIC_TABLES = ("measurements", "specimens", "samples", "sites", "locations")


# ----- describing a converter ----------------------------------------------------------


@dataclass(frozen=True)
class Field:
    """One thing a converter needs to be told.

    Attributes:
        name: canonical name — the same idea has the same name in every format
            (``location``, ``samp_con``, ``specnum``, ``labfield`` …).
        kind: ``text`` | ``int`` | ``float`` | ``bool`` | ``choice`` | ``codes`` | ``naming``.
            ``naming`` is the sample-naming convention: a code from
            :data:`NAMING_CONVENTIONS`, with ``-Z`` appended for codes 4 and 7.
            ``codes`` is several of ``choices`` at once; the converter gets them
            colon-joined (``"AF:T"``).
        label: what the form calls it.
        help: one sentence for the form; the converter's docstring says the rest.
        default: passed when the user leaves the field alone.
        required: the form insists on a value.
        choices: for ``choice`` — ``(value, label)`` pairs.
    """
    name: str
    kind: str
    label: str
    help: str = ""
    default: object = None
    required: bool = False
    choices: tuple = ()


@dataclass(frozen=True)
class Format:
    """A converter, described.

    Attributes:
        key: short id (``sio``); also the key in :data:`FORMATS`.
        label: the name a lab knows the format by.
        function: the ``convert_2_magic`` function.
        fields: what the form asks, in order; only what this converter uses.
        kwargs: canonical field name → this function's keyword, where they differ.
        file_kw: the keyword the input file (or directory) goes to.
        input_dir_kw: the keyword for the directory the input is read from ('' when
            the function has none — then the file is passed as a full path).
        output_dir_kw: the keyword for the directory the tables are written to.
        outputs: MagIC table → the keyword naming that table's output file.
        fixed: keywords always passed, whatever the user says.
        extensions: lower-case file extensions the format's files usually have —
            for guessing a format from a directory and for offering its files.
        takes_directory: the converter reads a whole directory, not files (``tdt``, ``livdb``).
        needs: MagIC table → keyword: tables that must already be in the MagIC
            directory, passed to the converter by path (the IODP measurement
            converters read the ``specimens.txt`` made from the LIMS sample file).
        prepare: turns the canonical values into extra keyword arguments when a
            plain rename will not do (``generic``'s naming lists).
        examples: paths under ``data_files`` that must convert, each
            ``(relative path, {canonical values})``; the registry's tests run them.
        notes: a line for the form about the format or the files it wants beside the input.
    """
    key: str
    label: str
    function: Callable
    fields: Tuple[Field, ...]
    kwargs: Dict[str, str] = field(default_factory=dict)
    file_kw: str = "mag_file"
    input_dir_kw: str = "input_dir_path"
    output_dir_kw: str = "dir_path"
    outputs: Dict[str, str] = field(default_factory=lambda: {
        "measurements": "meas_file", "specimens": "spec_file", "samples": "samp_file",
        "sites": "site_file", "locations": "loc_file"})
    fixed: Dict[str, object] = field(default_factory=dict)
    extensions: Tuple[str, ...] = ()
    takes_directory: bool = False
    needs: Dict[str, str] = field(default_factory=dict)
    prepare: Optional[Callable[[dict], dict]] = None
    examples: Tuple[Tuple[str, dict], ...] = ()
    notes: str = ""

    def keyword(self, name: str) -> str:
        return self.kwargs.get(name, name)

    def accepts(self, filename: str) -> bool:
        """Whether a file name looks like one of this format's, by extension (any file when none are listed)."""
        if not self.extensions:
            return True
        return filename.lower().endswith(self.extensions)


@dataclass
class ConversionResult:
    """What one conversion did."""
    ok: bool
    message: str                                   # one line for a status bar
    log: str = ""                                  # everything the converters printed
    tables: Dict[str, int] = field(default_factory=dict)      # table name → rows written
    failed: List[Tuple[str, str]] = field(default_factory=list)   # (file, reason)


# ----- the shared fields ------------------------------------------------------------------

NAMING_CONVENTIONS = (
    ("1", "XXXXY — site XXXX, one-character sample Y (TG001a)"),
    ("2", "XXXX-YY — site and sample split at a dash"),
    ("3", "XXXX.YY — site and sample split at a dot"),
    ("4", "XXXX[YYY] — the sample is the last Z characters"),
    ("5", "site name = sample name"),
    ("7", "[XXX]YYY — the site is the first Z characters"),
)

LOCATION = Field("location", "text", "Location name", "The MagIC location these sites belong to.", default="unknown")
SAMP_CON = Field("samp_con", "naming", "Sample naming convention",
                 "How the site name is read from the sample name.", default="1")
SPECNUM = Field("specnum", "int", "Specimen characters",
                "Characters at the end of a specimen name that are not part of the sample name (0: specimen = sample).",
                default=0)
LAT = Field("lat", "float", "Latitude", "Of the sites, in decimal degrees; leave blank to fill in later.")
LON = Field("lon", "float", "Longitude", "Of the sites, in decimal degrees, east positive.")
NOAVE = Field("noave", "bool", "Keep replicate measurements", "Do not average repeated measurements at a step.",
              default=False)
USER = Field("user", "text", "Analyst", "Goes in the analysts column.")
LABFIELD = Field("labfield", "float", "Lab field (μT)", "DC field of the paleointensity or ARM steps; 0 for none.",
                 default=0)
PHI = Field("phi", "float", "Lab field declination", "In specimen coordinates.", default=0)
THETA = Field("theta", "float", "Lab field inclination", "In specimen coordinates.", default=0)
PEAKFIELD = Field("peakfield", "float", "Peak AF field (mT)", "For ARM acquisition steps.", default=0)
INSTRUMENT = Field("instrument", "text", "Instrument", "Name of the magnetometer, for the instrument_codes column.")
VOLUME = Field("volume", "float", "Specimen volume (cm³)", "Used to turn moment into magnetization.", default=12)
METH_CODE = Field("meth_code", "choice", "Experiment", "The lab protocol, when the file does not say.",
                  default="LP-NO", choices=(("LP-NO", "not specified"), ("LP-DIR-AF", "AF demagnetization"),
                                            ("LP-DIR-T", "thermal demagnetization")))
TIMEZONE = Field("timezone", "text", "Time zone", "Of the measurement timestamps (e.g. US/Pacific).", default="UTC")

DEMAG_BLOCK = (LOCATION, SAMP_CON, SPECNUM, LAT, LON, NOAVE, USER)


# ----- running one -----------------------------------------------------------------------


def naming_code(value) -> str:
    """The ``samp_con`` string a converter wants from a form value: '1', '4-2', '7-3' …"""
    value = str(value or "1").strip()
    if value in ("4", "7"):
        raise ValueError(f"naming convention {value} needs the number of characters: '{value}-Z'")
    return value


def build_kwargs(fmt: Format, values: dict, input_path: str, out_dir: str, magic_dir: str = "") -> dict:
    """The keyword arguments for one call of ``fmt.function``.

    Only values the converter has a keyword for are passed, under the converter's own
    names; ``values`` may hold more (a form's whole dict) without harm, and a field left
    out takes its registry default, so a script and the form get the same conversion.
    ``magic_dir`` is where the tables a format ``needs`` are read from (``out_dir`` when
    not given).
    """
    params = inspect.signature(fmt.function).parameters
    kwargs = dict(fmt.fixed)
    for f in fmt.fields:
        value = values.get(f.name)
        if value in (None, "", [], ()):
            value = f.default
        if value in (None, "", [], ()):
            continue
        if f.kind == "naming":
            value = naming_code(value)
        elif f.kind == "int":
            value = int(value)
        elif f.kind == "float":
            value = float(value)
        elif f.kind == "codes":
            value = ":".join(value) if not isinstance(value, str) else value
        kw = fmt.keyword(f.name)
        if kw in params:
            kwargs[kw] = value
    if fmt.prepare:
        kwargs.update(fmt.prepare(values))
    for table, kw in fmt.needs.items():
        kwargs[kw] = os.path.join(magic_dir or out_dir, f"{table}.txt")
    file_kw = fmt.keyword(fmt.file_kw)
    if fmt.takes_directory:
        kwargs[file_kw] = input_path
    elif fmt.input_dir_kw and fmt.input_dir_kw in params:
        kwargs[fmt.input_dir_kw] = os.path.dirname(input_path)
        kwargs[file_kw] = os.path.basename(input_path)
    else:
        kwargs[file_kw] = input_path
    kwargs[fmt.output_dir_kw] = out_dir
    for table, kw in fmt.outputs.items():
        if kw in params:
            kwargs[kw] = f"{table}.txt"
    return kwargs


def run_one(fmt: Format, input_path: str, values: dict, out_dir: str, magic_dir: str = "") -> Tuple[bool, str, str]:
    """Convert one input into ``out_dir``. Returns (ok, message, log)."""
    kwargs = build_kwargs(fmt, values, input_path, out_dir, magic_dir)
    log = io.StringIO()
    try:
        with contextlib.redirect_stdout(log):
            result = fmt.function(**kwargs)
    except Exception as err:                      # the converters raise on malformed files; say which
        return False, f"{err.__class__.__name__}: {err}", log.getvalue()
    ok, message = _normalise(result)
    return ok, message, log.getvalue()


def _normalise(result) -> Tuple[bool, str]:
    """The converters return (ok, file_or_message), a bare bool, or a longer tuple."""
    if isinstance(result, tuple):
        ok = bool(result[0])
        rest = result[1] if len(result) > 1 else ""
        return ok, str(rest) if not isinstance(rest, (list, tuple)) else ", ".join(map(str, rest))
    return bool(result), ""


# ----- converting a batch into a directory --------------------------------------------------


def convert_files(fmt: Format, inputs: Sequence[str], values: dict, dir_path: str,
                  append: bool = False, report: Optional[Callable[[str], None]] = None) -> ConversionResult:
    """Convert files (or one directory) with one converter and write the MagIC tables into ``dir_path``.

    Each input is converted on its own in a scratch directory; the tables are then
    combined (rows concatenated, exact duplicates dropped) into ``dir_path``'s
    ``measurements.txt``, ``specimens.txt`` … — replacing what is there, or adding
    to it when ``append`` is set.

    Args:
        fmt: the format.
        inputs: paths of the files to convert (one directory for a format that
            ``takes_directory``). Relative paths are taken from ``dir_path``.
        values: canonical field name → value, as a form or a script gives them.
        dir_path: the MagIC directory the tables go to.
        append: add to the tables already in ``dir_path`` instead of replacing them.
        report: called with a line per file for a status bar.
    """
    say = report or (lambda text: None)
    dir_path = os.path.abspath(os.path.expanduser(dir_path))
    inputs = [p if os.path.isabs(p) else os.path.join(dir_path, p) for p in inputs]
    if not inputs:
        return ConversionResult(False, "No files chosen.")
    missing = [t for t in fmt.needs if not os.path.exists(os.path.join(dir_path, f"{t}.txt"))]
    if missing:
        return ConversionResult(False, f"{fmt.label} needs {', '.join(missing)}.txt in the directory first"
                                       f"{' — ' + fmt.notes if fmt.notes else '.'}")
    scratch = tempfile.mkdtemp(prefix="pmagpy_convert_")
    logs, failed, per_table = [], [], {t: [] for t in MAGIC_TABLES}
    try:
        for i, path in enumerate(inputs):
            name = os.path.basename(path.rstrip(os.sep))
            say(f"Converting {name} ({i + 1} of {len(inputs)}) …")
            out = os.path.join(scratch, f"{i:03d}")
            os.makedirs(out)
            ok, message, log = run_one(fmt, path, values, out, dir_path)
            # the scratch directory is nobody's business; macOS prints it through /private, so the
            # longer spelling goes first or its tail would survive
            for prefix in sorted({out, os.path.realpath(out)}, key=len, reverse=True):
                log = log.replace(prefix + os.sep, "").replace(prefix, ".")
            logs.append(f"── {name}\n{log.rstrip()}\n" if log.strip() else f"── {name}\n")
            if not ok:
                failed.append((name, message or "the converter reported failure"))
                continue
            for table in MAGIC_TABLES:
                written = os.path.join(out, f"{table}.txt")
                if os.path.exists(written):
                    per_table[table].append(written)
        if append:
            for table in MAGIC_TABLES:
                existing = os.path.join(dir_path, f"{table}.txt")
                if os.path.exists(existing):
                    per_table[table].insert(0, existing)
        tables = {}
        if any(per_table.values()):
            say("Combining the tables …")
            tables = combine_tables(per_table, dir_path)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    n_ok = len(inputs) - len(failed)
    if n_ok == 0:
        message = f"Nothing converted: {failed[0][1]}" if len(failed) == 1 else f"None of the {len(inputs)} files converted."
        return ConversionResult(False, message, "\n".join(logs), tables, failed)
    what = f"{n_ok} of {len(inputs)} files" if failed else (f"{n_ok} files" if n_ok > 1 else os.path.basename(inputs[0]))
    rows = tables.get("measurements", 0)
    message = f"{what} converted · {rows:,} measurements" + (f" · {len(failed)} failed" if failed else "")
    return ConversionResult(True, message, "\n".join(logs), tables, failed)


def combine_tables(per_table: Dict[str, List[str]], dir_path: str) -> Dict[str, int]:
    """Concatenate each table's files into ``dir_path/<table>.txt``; returns rows per table written."""
    from pmagpy.magic_project import magic_write
    written = {}
    for table, paths in per_table.items():
        if not paths:
            continue
        frames = [pd.read_csv(p, sep="\t", header=1, dtype=str, keep_default_na=False) for p in paths]
        df = pd.concat(frames, ignore_index=True, sort=False)
        df = df.replace("", pd.NA).drop_duplicates()
        df = _drop_redundant(df, table)
        if table == "locations":
            df = _merge_locations(df)
        if table == "measurements" and "sequence" in df:
            df["sequence"] = range(1, len(df) + 1)
        with contextlib.redirect_stdout(io.StringIO()):
            magic_write(os.path.join(dir_path, f"{table}.txt"), df, table)
        written[table] = len(df)
    return written


def _merge_locations(df: pd.DataFrame) -> pd.DataFrame:
    """One row per location: files that each named it with their own site coordinates give its bounding box.

    ``lat_n``/``lon_e`` take the largest value and ``lat_s``/``lon_w`` the smallest (a
    location straddling the dateline is not resolved); every other column keeps the
    first value given.
    """
    if "location" not in df or not df["location"].duplicated().any():
        return df
    bounds = {"lat_n": "idxmax", "lat_s": "idxmin", "lon_e": "idxmax", "lon_w": "idxmin"}
    merged = []
    for _, group in df.groupby("location", sort=False):
        row = group.bfill().iloc[0].copy()
        for col, which in bounds.items():
            if col in group:
                values = pd.to_numeric(group[col], errors="coerce").dropna()
                if len(values):
                    row[col] = group[col][getattr(values, which)()]     # as the file wrote it
        merged.append(row)
    return pd.DataFrame(merged).reset_index(drop=True)


def _drop_redundant(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Drop a row that names a specimen/sample/site/location and says nothing else, when a fuller row names it too."""
    key = table[:-1]
    if table == "measurements" or key not in df:
        return df
    ignore = [c for c in ("specimen", "sample", "site", "location", "software_packages", "citations") if c in df]
    rest = df.drop(columns=ignore)
    says_something = rest.notna().any(axis=1) if len(rest.columns) else pd.Series(True, index=df.index)
    named_elsewhere = df[key].duplicated(keep=False)
    return df[says_something | ~named_elsewhere].reset_index(drop=True)


# ----- guessing a format from a directory ----------------------------------------------------


def guess_format(names: Sequence[str], directory: str = "") -> Tuple[str, Dict[str, str]]:
    """A format key from file names (and a peek inside ambiguous ones), and a role per file.

    Offered to the analyst, never assumed. Returns ``("", {})`` when nothing is recognised.
    """
    roles: Dict[str, str] = {}
    lower = {n: n.lower() for n in names}
    sams = [n for n in names if lower[n].endswith(".sam")]
    if sams:
        stems = [os.path.splitext(n)[0].rstrip("-") for n in sams]
        for n in names:
            if n in sams:
                roles[n] = "CIT index"
            elif any(n.startswith(s) for s in stems):
                roles[n] = "CIT specimen"
        return "cit", roles
    for n in names:                      # a downloaded contribution is a .txt like any other: look inside
        if lower[n].endswith(".txt") and directory:
            try:
                with open(os.path.join(directory, n), encoding="utf-8-sig", errors="replace") as fh:
                    head = fh.read(4096)
            except OSError:
                continue
            if head.startswith("tab") and ">>>>>>>>>>" in head:
                roles[n] = "MagIC contribution file"
                return "magic", roles
    for key in ("jr6_jr6", "pmd", "tdt", "agm", "utrecht", "2g_asc", "2g_bin"):
        fmt = FORMATS[key]
        hits = [n for n in names if fmt.accepts(n) and fmt.extensions]
        if hits:
            for n in hits:
                roles[n] = fmt.label
            return key, roles
    return "", roles


# ----- the formats -----------------------------------------------------------------------------

FORMATS: Dict[str, Format] = {}


def _add(fmt: Format) -> Format:
    FORMATS[fmt.key] = fmt
    return fmt

EXAMPLES = "data_files/convert_2_magic"      # example paths below are relative to the PmagPy checkout

PROTOCOLS = (("AF", "AF demagnetization"), ("T", "thermal (including Thellier)"), ("N", "NRM only"),
             ("TRM", "TRM acquisition"), ("ANI", "anisotropy"), ("S", "Shaw"), ("I", "IRM acquisition"),
             ("D", "double AF (DC bias)"), ("G", "triple AF (GRM)"), ("CR", "cooling rate"))
CODELIST = Field("codelist", "codes", "Lab protocols", "Every protocol in the file; the steps are decoded by these.",
                 choices=PROTOCOLS)
EXPERIMENT = Field("experiment", "choice", "Experiment", "What the treatment steps in the file are.",
                   required=True,                  # no default on purpose: the file cannot say, so the analyst must
                   choices=(("Demag", "AF and/or thermal demagnetization"), ("PI", "thermal paleointensity (ZI/IZ/IZZI)"),
                            ("ATRM 6", "anisotropy of TRM, 6 positions"), ("AARM 6", "anisotropy of ARM, 6 positions"),
                            ("CR", "cooling rate"), ("NLT", "non-linear TRM")))
OR_CON = Field("or_con", "choice", "Orientation convention", "How the file's azimuth and dip give the lab arrow.",
               default="3", choices=(("1", "azimuth; dip = −hade"), ("2", "strike; dip = −hade"),
                                     ("3", "azimuth; dip = 90 − hade"), ("4", "azimuth and dip as given"),
                                     ("5", "azimuth; dip = dip − 90"), ("6", "azimuth − 90; dip = 90 − hade")))
GMETHS = Field("gmeths", "text", "Sampling method codes", "Colon-delimited: FS-FD, FS-H, SO-POM, SO-ASC, SO-MAG, SO-SUN …",
               default="FS-FD:SO-POM")
SAVELAST = Field("savelast", "bool", "Keep only the last replicate", "Instead of averaging repeated steps.", default=False)


def _generic_naming(values: dict) -> dict:
    """``generic``'s ``sample_nc``/``site_nc`` lists from the two-part choices in the form."""
    out = {}
    for key in ("sample", "site"):
        how, n = values.get(f"{key}_nc_how", "same"), values.get(f"{key}_nc_n", 0)
        if how == "same":
            continue
        code = {"initial": 0, "terminal": 1, "delimiter": 2}[how]
        out[f"{key}_nc"] = [code, n if code == 2 else int(n or 0)]
    return out


NC_HOW = (("same", "same as the level below"), ("initial", "the first N characters"),
          ("terminal", "all but the last N characters"), ("delimiter", "the part before a delimiter"))
SAMPLE_NC_HOW = Field("sample_nc_how", "choice", "Sample name is", "How the sample name comes from the specimen name.",
                      default="same", choices=NC_HOW)
SAMPLE_NC_N = Field("sample_nc_n", "text", "… N or delimiter", "Characters to keep or strip, or the delimiter.", default="0")
SITE_NC_HOW = Field("site_nc_how", "choice", "Site name is", "How the site name comes from the sample name.",
                    default="same", choices=NC_HOW)
SITE_NC_N = Field("site_nc_n", "text", "… N or delimiter", "Characters to keep or strip, or the delimiter.", default="0")


_add(Format(
    "sio", "SIO", convert.sio,
    fields=(*DEMAG_BLOCK, CODELIST, LABFIELD, PHI, THETA, PEAKFIELD,
            Field("coil", "choice", "IRM coil", "ASC coil used when IRM fields are in volts.",
                  choices=(("", "fields in T"), ("1", "coil 1"), ("2", "coil 2"), ("3", "coil 3"))),
            Field("cooling_rates", "text", "Cooling rates", "For CR experiments: comma-separated K/min, matching XXX.10, .20 …"),
            INSTRUMENT, TIMEZONE),
    extensions=(".dat", ".txt", ".mag"),
    examples=(("sio_magic/sio_af_example.dat", {"codelist": ["AF"], "location": "Hawaii", "specnum": 1}),
              ("sio_magic/sio_thermal_example.dat", {"codelist": ["T"], "specnum": 1, "labfield": 25})),
    notes="Scripps format: one line per measurement, tab or space delimited."))

_add(Format(
    "cit", "CIT", convert.cit,
    fields=(Field("location", "text", "Location name", "The MagIC location these sites belong to.", default="unknown"),
            Field("sitename", "text", "Site name", "One site for every specimen in the file; blank to read it from the names."),
            Field("samp_con", "naming", "Sample naming convention", "How the site name is read from the sample name.",
                  default="3"),
            SPECNUM,
            # CIT steps are already averaged over the measurement orientations, so a repeated step
            # is a remeasurement worth keeping; Pmag GUI's CIT dialog also keeps them
            Field("noave", "bool", "Keep replicate measurements",
                  "Keep repeated steps as separate rows rather than averaging them.", default=True),
            USER,
            Field("methods", "text", "Orientation method codes",
                  "Colon-delimited, e.g. SO-MAG:SO-SUN. A specimen file whose first line says \"sun compass\" turns "
                  "SO-MAG into SO-SUN; SO-CMD-NORTH is added when a declination correction applies.", default="SO-MAG"),
            Field("meas_n_orient", "int", "Orientations per measurement", "Number of positions the specimen was measured in.",
                  default=8),
            Field("norm", "choice", "Normalization", "Units of the volume or mass in the specimen files "
                  "(exactly 1.0 means not normalized).", default="cc",
                  choices=(("cc", "cm³"), ("m3", "m³"), ("g", "g"), ("kg", "kg")))),
    kwargs={"mag_file": "magfile", "location": "locname"},
    extensions=(".sam",),
    examples=(("cit_magic/PI47/PI47-.sam", {"location": "Slate Islands", "samp_con": "2", "specnum": 1}),
              ("cit_magic/MIT/7325B/7325B.sam", {"samp_con": "1"}),
              ("cit_magic/USGS/bl9-1/bl9-1.sam", {"samp_con": "1"})),
    notes="Choose the .sam index file; the specimen files it lists must sit beside it. Site latitude and "
          "longitude come from the .sam header (to its precision)."))

_add(Format(
    "2g_bin", "2G binary", convert._2g_bin,
    fields=(LOCATION, Field("samp_con", "naming", "Sample naming convention", "", default="2"), SPECNUM, LAT, LON, NOAVE, USER,
            OR_CON, GMETHS, EXPERIMENT, LABFIELD, PHI, THETA, INSTRUMENT, SAVELAST,
            Field("dec_corr", "bool", "Declination corrected", "The file's azimuths are already true north.", default=True),
            Field("specname", "bool", "Specimen name from file name", "Rather than from inside the file.", default=False)),
    kwargs={"phi": "labfield_phi", "theta": "labfield_theta", "instrument": "inst"},
    input_dir_kw="input_dir",
    extensions=(".dat",),
    examples=(("2g_bin_magic/mn1/mn001-1a.dat", {}),),
    notes="One binary file per specimen; choose them all."))

_add(Format(
    "2g_asc", "2G ASCII", convert._2g_asc,
    fields=(LOCATION, Field("samp_con", "naming", "Sample naming convention", "", default="2"), SPECNUM, LAT, LON, NOAVE, USER,
            OR_CON, GMETHS, EXPERIMENT, INSTRUMENT, SAVELAST),
    kwargs={"instrument": "inst"},
    input_dir_kw="input_dir",
    extensions=(".asc",),
    examples=(("2g_asc_magic/_2g_asc/DR3B.asc", {}), ("2g_asc_magic/_2g_asc/OK3_15af.asc", {}))))

_add(Format(
    "generic", "Generic (PmagPy)", convert.generic,
    fields=(EXPERIMENT, LOCATION, SAMPLE_NC_HOW, SAMPLE_NC_N, SITE_NC_HOW, SITE_NC_N, LAT, LON, NOAVE, USER,
            LABFIELD, PHI, THETA,
            Field("cooling_times_list", "text", "Cooling times", "For CR experiments: comma-separated K/min.")),
    kwargs={"mag_file": "magfile", "phi": "labfield_phi", "theta": "labfield_theta"},
    prepare=_generic_naming,
    extensions=(".txt", ".dat", ".csv"),
    examples=(("generic_magic/generic_magic_example.txt", {"experiment": "Demag"}),),
    notes="PmagPy's own tab-delimited layout — see the generic_magic help for the columns."))

_add(Format(
    "huji", "HUJI", convert.huji,
    fields=(LOCATION, SAMP_CON, SPECNUM, NOAVE, USER, Field("codelist", "codes", "Lab protocols", "Every protocol in the file.", required=True,
                                choices=tuple(c for c in PROTOCOLS if c[0] in ("AF", "T", "N", "TRM", "ANI", "CR"))),
            LABFIELD, PHI, THETA),
    kwargs={"mag_file": "magfile"},
    extensions=(".txt", ".dat"),
    examples=(("huji_magic/Massada_AF_HUJI_new_format.txt", {"codelist": ["AF"]}),),
    notes="Hebrew University format; the demagnetization data file goes with an optional .dat of sample orientations."))

_add(Format(
    "ldeo", "LDEO", convert.ldeo,
    fields=(LOCATION, SAMP_CON, SPECNUM, NOAVE, CODELIST, LABFIELD, PHI, THETA, PEAKFIELD,
            Field("coil", "choice", "IRM coil", "ASC coil used when IRM fields are in volts.",
                  choices=(("", "fields in T"), ("1", "coil 1"), ("2", "coil 2"), ("3", "coil 3"))),
            Field("mass_or_vol", "choice", "Normalized by", "What the file's normalization column holds.", default="v",
                  choices=(("v", "volume"), ("m", "mass")))),
    kwargs={"mag_file": "magfile"},
    extensions=(".dat", ".txt"),
    examples=(("ldeo_magic/ldeo_magic_example.dat", {"codelist": ["AF"]}),)))

_add(Format(
    "pmd", "PMD (Enkin)", convert.pmd,
    fields=(LOCATION, SAMP_CON, SPECNUM, LAT, LON, NOAVE, METH_CODE,
            Field("dmg", "choice", "Demagnetization", "When the file does not say (PAL files are thermal).",
                  choices=(("", "read from the file"), ("af", "AF"), ("t", "thermal")))),
    extensions=(".pmd",),
    examples=(("pmd_magic/UCSC/PMD/ss0207a.pmd", {}), ("pmd_magic/IPGP/0110C.PMD", {}), ("pmd_magic/IPGP/0210C.pmd", {})),
    notes="One .pmd file per specimen; choose them all."))

_add(Format(
    "jr6_jr6", "JR6 (.jr6)", convert.jr6_jr6,
    fields=(LOCATION, SAMP_CON, Field("specnum", "int", "Specimen characters", SPECNUM.help, default=1), LAT, LON, NOAVE,
            USER, VOLUME, METH_CODE,
            Field("JR", "bool", "JR5 format", "The file came from an AGICO JR5, not a JR6.", default=False)),
    extensions=(".jr6",),
    examples=(("jr6_magic/AF.jr6", {}), ("jr6_magic/TRM.jr6", {}), ("jr6_magic/SML07.JR6", {})),
    notes="AGICO .jr6 binary-style export; one file can hold many specimens."))

_add(Format(
    "jr6_txt", "JR6 (.txt)", convert.jr6_txt,
    fields=(LOCATION, SAMP_CON, Field("specnum", "int", "Specimen characters", SPECNUM.help, default=1), LAT, LON, NOAVE,
            USER, VOLUME, METH_CODE, TIMEZONE),
    extensions=(".txt",),
    examples=(("jr6_magic/AP12.txt", {}),),
    notes="AGICO Rema6 text export."))

_add(Format(
    "utrecht", "Utrecht", convert.utrecht,
    fields=(LOCATION, Field("samp_con", "naming", "Sample naming convention", "", default="2"),
            Field("specnum", "int", "Specimen characters", SPECNUM.help, default=1), LAT, LON, NOAVE,
            METH_CODE, LABFIELD, PHI, THETA,
            Field("meas_n_orient", "int", "Orientations per measurement", "", default=8),
            Field("dmy_flag", "bool", "Dates are day-month-year", "Rather than month-day-year.", default=False)),
    extensions=(".af", ".th", ".dat"),
    examples=(("utrecht_magic/Utrecht_Example.af", {}),)))

_add(Format(
    "bgc", "BGC", convert.bgc,
    fields=(LOCATION, Field("site", "text", "Site name", "One site for the whole file; blank to read it from the names."),
            SAMP_CON, SPECNUM, NOAVE, USER, VOLUME, METH_CODE,
            Field("timezone", "text", "Time zone", TIMEZONE.help, default="US/Pacific")),
    examples=(("bgc_magic/96MT.05.01", {}),),
    notes="Berkeley Geochronology Center format; one file per specimen."))

_add(Format(
    "mini", "MINI", convert.mini,
    fields=(NOAVE, USER, VOLUME, INSTRUMENT, Field("meth_code", "choice", "Experiment", METH_CODE.help,
                                                    default="LP-NO", choices=METH_CODE.choices)),
    kwargs={"mag_file": "magfile", "instrument": "inst", "meth_code": "methcode"},
    outputs={"measurements": "meas_file"},
    examples=(("mini_magic/Peru_rev1.txt", {}),),
    notes="Writes measurements only — specimens, samples and sites are made afterwards."))

_add(Format(
    "tdt", "TDT (ThellierTool)", convert.tdt,
    fields=(Field("experiment", "choice", "Experiment", "", default="Thellier",
                  choices=(("Thellier", "Thellier-type paleointensity"), ("ATRM 6 pos", "anisotropy of TRM, 6 positions"),
                           ("NLT", "non-linear TRM"))),
            LOCATION, USER,
            Field("lab_dec", "float", "Lab field declination", "In specimen coordinates.", default=0),
            Field("lab_inc", "float", "Lab field inclination", "In specimen coordinates.", default=90),
            Field("moment_units", "choice", "Moment units", "As written in the files.", default="mA/m",
                  choices=(("mA/m", "mA/m"), ("emu", "emu"), ("Am^2", "A m²"))),
            Field("spec_name_con", "choice", "Specimen name from", "", default="1",
                  choices=(("1", "the first column"), ("2", "the file name"))),
            Field("samp_name_con", "choice", "Sample name is", "", default="sample=specimen",
                  choices=(("sample=specimen", "the specimen name"), ("no. of initial characters", "the first N characters"),
                           ("no. of terminal characters", "all but the last N characters"),
                           ("character delimited", "the part before a delimiter"))),
            Field("samp_name_chars", "text", "… N or delimiter", "", default="0"),
            Field("site_name_con", "choice", "Site name is", "", default="site=sample",
                  choices=(("site=sample", "the sample name"), ("no. of initial characters", "the first N characters"),
                           ("no. of terminal characters", "all but the last N characters"),
                           ("character delimited", "the part before a delimiter"))),
            Field("site_name_chars", "text", "… N or delimiter", "", default="0"),
            VOLUME),
    kwargs={"experiment": "experiment_name"},
    file_kw="input_dir_path", output_dir_kw="output_dir_path", takes_directory=True,
    outputs={"measurements": "meas_file_name", "specimens": "spec_file_name", "samples": "samp_file_name",
             "sites": "site_file_name", "locations": "loc_file_name"},
    extensions=(".tdt",),
    examples=(("tdt_magic", {}),),
    notes="Converts every .tdt file in the directory at once."))

_add(Format(
    "agm", "AGM / VSM (MicroMag)", convert.agm,
    fields=(LOCATION, SAMP_CON, SPECNUM, USER, INSTRUMENT,
            Field("specimen", "text", "Specimen name", "Blank to take it from the file name."),
            Field("fmt", "choice", "File layout", "", default="new",
                  choices=(("new", "current MicroMag header"), ("old", "old MicroMag header"), ("xy", "two columns: field, moment"))),
            Field("units", "choice", "Units in the file", "", default="cgs", choices=(("cgs", "cgs"), ("SI", "SI"))),
            Field("bak", "bool", "Backfield (IRM) curve", "The file is a DCD/backfield run, not a hysteresis loop.", default=False)),
    file_kw="agm_file",
    outputs={"measurements": "meas_outfile", "specimens": "spec_outfile", "samples": "samp_outfile",
             "sites": "site_outfile", "locations": "loc_outfile"},
    extensions=(".agm", ".irm", ".hys", ".dcd"),
    examples=(("agm_magic/agm_magic_example.agm", {"fmt": "old"}),
              ("agm_magic/agm_magic_example.irm", {"fmt": "old", "bak": True, "instrument": "SIO-FLO"})),
    notes="One file per curve; choose the hysteresis loops and backfield curves separately."))

_add(Format(
    "iodp_samples", "IODP samples (LIMS)", convert.iodp_samples_csv,
    fields=(Field("comp_depth_key", "text", "Composite depth column", "The LIMS column to use for composite depth.",
                  default="Top depth CSF-B (m)"),
            LAT, LON,
            Field("exp_name", "text", "Expedition", "For the locations table."),
            Field("exp_desc", "text", "Expedition description", ""),
            Field("age_low", "float", "Youngest age (Ma)", "", default=0),
            Field("age_high", "float", "Oldest age (Ma)", "", default=200)),
    file_kw="lims_sample_file",
    outputs={"specimens": "spec_file", "samples": "samp_file", "sites": "site_file", "locations": "loc_file"},
    extensions=(".csv",),
    examples=(("../iodp_magic/U999A/samples_17_5_2019.csv", {"lat": -56.557775, "lon": -42.64212833333333}),),
    notes="The LIMS sample report; run it first — the measurement converters need the specimens it makes."))

_add(Format(
    "iodp_srm", "IODP SRM section (LORE)", convert.iodp_srm_lore,
    fields=(Field("comp_depth_key", "text", "Composite depth column", "", default="Depth CSF-B (m)"), LAT, LON, NOAVE),
    file_kw="srm_file",
    outputs={"measurements": "meas_file", "specimens": "spec_file", "samples": "samp_file", "sites": "site_file"},
    extensions=(".csv",),
    examples=(("../iodp_magic/U999A/SRM_archive_data/srmsection_17_5_2019.csv", {"lat": -56.557775, "lon": -42.64212833333333}),),
    notes="Archive-half section measurements; makes its own specimens, samples and sites for the section pieces."))

_add(Format(
    "iodp_dscr", "IODP SRM discrete (LORE)", convert.iodp_dscr_lore,
    fields=(Field("volume", "float", "Specimen volume (cm³)", VOLUME.help, default=7), NOAVE),
    file_kw="dscr_file",
    outputs={"measurements": "meas_file"},
    needs={"specimens": "spec_file"},
    extensions=(".csv",),
    examples=(("../iodp_magic/U999A/SRM_discrete_data/srmdiscrete_17_5_2019.csv", {}),),
    notes="convert the LIMS sample report with IODP samples first."))

_add(Format(
    "iodp_jr6", "IODP JR6 (LORE)", convert.iodp_jr6_lore,
    fields=(Field("volume", "float", "Specimen volume (cm³)", VOLUME.help, default=7),
            Field("dc_field", "float", "ARM DC field (T)", "", default=5e-05), SPECNUM, NOAVE),
    file_kw="jr6_file",
    outputs={"measurements": "meas_file"},
    needs={"specimens": "spec_file"},
    extensions=(".csv",),
    examples=(("../iodp_magic/U999A/JR6_data/spinner_17_5_2019.csv", {}),),
    notes="convert the LIMS sample report with IODP samples first."))
