"""
What is in a directory, said the way the Home page says it.

An :class:`Inventory` is a UI-free description of one directory: which MagIC
tables it holds and how long they are, how many locations, sites, samples,
specimens and measurements, which kinds of experiment the measurements record,
what the contribution is, how far analysis has got, where the metadata has
gaps — and, for a directory that holds no MagIC tables yet, which files are
there and what format they look like. Everything on Home is read from it, and
so can a notebook::

    from pmagpy_apps.inventory import take_inventory
    inv = take_inventory("data_files/3_0/McMurdo")
    inv.counts["specimens"], [k.label for k in inv.kinds]

Nothing here imports Panel. It knows the MagIC 3 tables and the ``LP-``
method codes; it does not know any science.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import pandas as pd

from pmagpy.convert_registry import FORMATS, guess_format

# MagIC 3 tables in the order Home lists them; contribution is read but not listed
TABLES = ("measurements", "specimens", "samples", "sites", "locations", "ages", "criteria", "images", "contribution")
LISTED_TABLES = TABLES[:-1]

# the columns the inventory needs from each table — nothing else is read, so a
# multi-million-row measurements file costs only its method codes
COLUMNS = {
    "measurements": ["specimen", "experiment", "method_codes"],
    "specimens": ["specimen", "sample", "dir_dec", "int_abs", "method_codes"],
    "samples": ["sample", "site", "azimuth", "dip"],
    "sites": ["site", "location", "lat", "lon", "age", "age_low", "age_high", "lithologies", "dir_dec", "int_abs"],
    "locations": ["location", "lat_n", "lat_s", "lon_e", "lon_w"],
    "ages": ["site", "age", "age_low", "age_high"],
    "contribution": ["id", "reference", "contributor", "author", "data_model_version"],
    "criteria": [],
    "images": [],
}


@dataclass
class Table:
    """One MagIC table file: its name, path and length."""
    name: str
    path: str
    rows: int


@dataclass
class Kind:
    """A kind of experiment found in the measurements, e.g. demagnetization.

    Attributes:
        key: what the application registry matches on ("demag", "pi", "hys", ...).
        label: the word for it on the page.
        specimens: how many specimens have this kind of experiment.
        details: the variants seen, in the vocabulary of the method codes
            ("AF", "thermal"; "IZZI", "ZI").
    """
    key: str
    label: str
    specimens: int
    details: List[str] = field(default_factory=list)

    @property
    def detail(self) -> str:
        return ", ".join(self.details)


@dataclass
class Gap:
    """A piece of metadata missing from `n` rows: ``Gap("site coordinates", 1)``."""
    label: str
    n: int


@dataclass
class FileRole:
    """A file that is not a MagIC table, and what it looks like."""
    name: str
    role: str = ""


@dataclass
class Inventory:
    directory: str
    tables: Dict[str, Table] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)          # locations, sites, samples, specimens, measurements
    kinds: List[Kind] = field(default_factory=list)
    contribution: Dict[str, str] = field(default_factory=dict)    # id, reference, contributor
    analysis: Dict[str, int] = field(default_factory=dict)        # specimens_interpreted, site_means, site_intensities
    gaps: List[Gap] = field(default_factory=list)                 # largest first
    files: List[FileRole] = field(default_factory=list)           # everything that is not a MagIC table
    folders: int = 0
    format_key: str = ""                                          # a convert_registry key, "magic", or ""
    format_guess: str = ""                                        # its label: "CIT", "JR6 (.jr6)", "MagIC contribution file", or ""
    error: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.directory.rstrip(os.sep)) or self.directory

    @property
    def is_magic(self) -> bool:
        """Holds a measurements table: the analysis applications can open it."""
        return "measurements" in self.tables

    @property
    def is_empty(self) -> bool:
        """No files at all (folders do not count: a directory of directories is still empty)."""
        return not self.tables and not self.files

    def kind(self, key: str) -> Optional[Kind]:
        return next((k for k in self.kinds if k.key == key), None)

    def has(self, *keys: str) -> bool:
        return any(self.kind(k) is not None for k in keys)


# ----- experiment kinds from method codes ---------------------------------------

# (key, label, prefixes that mark it, {code prefix: the word for that variant})
KIND_RULES = [
    ("demag", "Demagnetization", ("LP-DIR-",),
     {"LP-DIR-AF": "AF", "LP-DIR-T": "thermal", "LP-DIR-M": "microwave", "LP-DIR-CHEM": "chemical"}),
    ("pi", "Paleointensity", ("LP-PI",),
     {"LP-PI-BT-IZZI": "IZZI", "LP-PI-TRM-ZI": "ZI", "LP-PI-ZI": "ZI", "LP-PI-TRM-IZ": "IZ", "LP-PI-IZ": "IZ",
      "LP-PI-II": "Thellier–Thellier", "LP-PI-TRM-II": "Thellier–Thellier", "LP-PI-M": "microwave",
      "LP-PI-AFAF": "Shaw", "LP-PI-MULT": "multi-specimen", "LP-PI-REL": "relative", "LP-PI-PARM": "pseudo-Thellier",
      "LP-PI-TRM-PERP": "perpendicular"}),
    ("hys", "Hysteresis", ("LP-HYS",), {"LP-HYS-T": "vs temperature", "LP-HYS-M": "minor loops"}),
    ("bcr", "Backfield", ("LP-BCR",), {}),
    ("irm", "IRM acquisition", ("LP-IRM",), {"LP-IRM-3D": "3-axis thermal demag", "LP-IRM-AFD": "AF demag"}),
    ("arm", "ARM acquisition", ("LP-ARM",), {}),
    ("forc", "FORC", ("LP-FORC",), {}),
    ("chi_t", "Susceptibility", ("LP-X",), {"LP-X-T": "vs temperature", "LP-X-F": "vs frequency", "LP-X-H": "vs amplitude"}),
    ("ms_t", "Ms–T", ("LP-MST", "LP-IMT"), {}),
    ("low_t", "Low temperature", ("LP-FC", "LP-ZFC", "LP-PFC", "LP-CW-", "LP-MW", "LP-MC", "LP-MRT", "LP-LT"),
     {"LP-FC": "FC", "LP-ZFC": "ZFC", "LP-CW-SIRM": "RT-SIRM cycling", "LP-CW-NRM": "RT-NRM cycling"}),
    ("aniso", "Anisotropy", ("LP-AN-",),
     {"LP-AN-ARM": "ARM", "LP-AN-TRM": "TRM", "LP-AN-MS": "AMS", "LP-AN-IRM": "IRM"}),
]

# codes that are checks on a paleointensity experiment, not experiments of their own
PI_ANCILLARY = ("LP-PI-ALT", "LP-PI-BT-MD", "LP-PI-BT-BZF", "LP-PI-BT-PTRM")


def _matches(code: str, prefixes) -> bool:
    return any(code == p.rstrip("-") or code.startswith(p) for p in prefixes)


def experiment_kinds(measurements: pd.DataFrame) -> List[Kind]:
    """The kinds of experiment in a measurements table, from its ``LP-`` method codes."""
    if "method_codes" not in measurements or "specimen" not in measurements:
        return []
    codes = measurements["method_codes"].fillna("").astype(str)
    kinds = []
    for key, label, prefixes, variants in KIND_RULES:
        per_row = codes.str.split(":").apply(lambda cs: [c.strip() for c in cs if _matches(c.strip(), prefixes)])
        hit = per_row.str.len() > 0
        if not hit.any():
            continue
        n = measurements.loc[hit, "specimen"].nunique()
        seen = set(c for cs in per_row[hit] for c in cs)
        details = []
        for prefix, word in variants.items():
            if any(c == prefix or c.startswith(prefix + "-") for c in seen) and word not in details:
                details.append(word)
        if key == "pi" and any(c.startswith("LP-PI-TRM") or c in ("LP-PI-II", "LP-PI-ZI", "LP-PI-IZ", "LP-PI-BT-IZZI")
                               for c in seen):
            label = "Thellier"
        kinds.append(Kind(key, label, int(n), details))
    return kinds


# ----- reading -------------------------------------------------------------------

def _read_table(path: str, wanted) -> Optional[pd.DataFrame]:
    """A MagIC 3 table (``tab<TAB>name`` on line 1, header on line 2), only the wanted columns."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        first = fh.readline()
        header = fh.readline().rstrip("\n").split("\t")
    if not first.startswith("tab"):
        return None
    usecols = [c for c in wanted if c in header] if wanted else []
    if wanted and not usecols:
        usecols = [header[0]]
    return pd.read_csv(path, sep="\t", header=1, usecols=usecols or None, low_memory=False,
                       encoding="utf-8", encoding_errors="replace", dtype=str if not wanted else None)


def _missing(df: pd.DataFrame, key: str, columns) -> int:
    """How many distinct `key` values have no value in any of `columns`."""
    if df is None or key not in df or not len(df):
        return 0
    present = [c for c in columns if c in df]
    if not present:
        return int(df[key].nunique())
    has_value = df[present].notna().any(axis=1)
    filled = set(df.loc[has_value, key].dropna())
    return int(len(set(df[key].dropna()) - filled))


def _guess_format(names: List[str], directory: str) -> Tuple[str, str, Dict[str, str]]:
    """The registry's guess for a directory: (format key, label for the page, role per file).

    Offered to the analyst, never assumed. A MagIC contribution file is not a
    conversion format but is recognised here so Home can say what it is.
    """
    key, roles = guess_format(names, directory)
    if key == "magic":
        return key, "MagIC contribution file", roles
    if key in FORMATS:
        return key, FORMATS[key].label, roles
    return "", "", roles


def take_inventory(directory: str) -> Inventory:
    """Read what Home needs to know about `directory`. Never raises; see ``Inventory.error``."""
    directory = os.path.abspath(os.path.expanduser(directory))
    inv = Inventory(directory=directory)
    if not os.path.isdir(directory):
        inv.error = f"{directory} is not a directory"
        return inv
    try:
        names = sorted(n for n in os.listdir(directory) if not n.startswith("."))
    except OSError as e:
        inv.error = str(e)
        return inv

    frames: Dict[str, pd.DataFrame] = {}
    others = []
    for n in names:
        stem, ext = os.path.splitext(n)
        path = os.path.join(directory, n)
        if ext == ".txt" and stem in TABLES and os.path.isfile(path):
            try:
                df = _read_table(path, COLUMNS[stem])
            except (OSError, ValueError, pd.errors.ParserError) as e:
                inv.error = f"{n}: {e}"
                df = None
            if df is None:
                others.append(n)
                continue
            frames[stem] = df
            inv.tables[stem] = Table(stem, path, len(df))
        elif os.path.isfile(path):
            others.append(n)

    inv.folders = sum(os.path.isdir(os.path.join(directory, n)) for n in names)
    inv.format_key, inv.format_guess, roles = _guess_format(others, directory)
    inv.files = [FileRole(n, roles.get(n, "")) for n in others]
    if not frames:
        return inv

    def nunique(table, column):
        df = frames.get(table)
        return int(df[column].dropna().nunique()) if df is not None and column in df else 0

    m = frames.get("measurements")
    inv.counts = {
        "locations": nunique("locations", "location") or nunique("sites", "location"),
        "sites": nunique("sites", "site") or nunique("samples", "site"),
        "samples": nunique("samples", "sample") or nunique("specimens", "sample"),
        "specimens": nunique("measurements", "specimen") or nunique("specimens", "specimen"),
        "measurements": len(m) if m is not None else 0,
    }
    if m is not None:
        inv.kinds = experiment_kinds(m)

    c = frames.get("contribution")
    if c is not None and len(c):
        row = c.iloc[0]
        for col, key in (("id", "id"), ("reference", "reference"), ("contributor", "contributor"), ("author", "author")):
            if col in c and pd.notna(row[col]):
                inv.contribution[key] = str(row[col]).strip()
        if "id" in inv.contribution:
            inv.contribution["id"] = inv.contribution["id"].split(".")[0]      # pandas reads 13436 as 13436.0

    s, si = frames.get("specimens"), frames.get("sites")
    inv.analysis = {
        "specimens_interpreted": int(s.dropna(subset=["dir_dec"])["specimen"].nunique()) if s is not None and "dir_dec" in s else 0,
        "specimen_intensities": int(s.dropna(subset=["int_abs"])["specimen"].nunique()) if s is not None and "int_abs" in s else 0,
        "site_means": int(si.dropna(subset=["dir_dec"])["site"].nunique()) if si is not None and "dir_dec" in si else 0,
        "site_intensities": int(si.dropna(subset=["int_abs"])["site"].nunique()) if si is not None and "int_abs" in si else 0,
    }

    # metadata gaps, against what the analysis applications and an upload need
    gaps = []
    if si is not None:
        gaps.append(Gap("site coordinates", _missing(si, "site", ["lat", "lon"])))
        dated = set()
        if any(c in si for c in ("age", "age_low", "age_high")):
            dated |= set(si.loc[si[[c for c in ("age", "age_low", "age_high") if c in si]].notna().any(axis=1), "site"].dropna())
        ages = frames.get("ages")
        if ages is not None and "site" in ages:
            dated |= set(ages["site"].dropna())
        gaps.append(Gap("site ages", int(len(set(si["site"].dropna()) - dated))))
        gaps.append(Gap("site lithologies", _missing(si, "site", ["lithologies"])))
    sa = frames.get("samples")
    if sa is not None:
        gaps.append(Gap("sample orientations", _missing(sa, "sample", ["azimuth", "dip"])))
    lo = frames.get("locations")
    if lo is not None:
        gaps.append(Gap("location bounds", _missing(lo, "location", ["lat_n", "lat_s", "lon_e", "lon_w"])))
    inv.gaps = sorted((g for g in gaps if g.n), key=lambda g: -g.n)
    return inv
