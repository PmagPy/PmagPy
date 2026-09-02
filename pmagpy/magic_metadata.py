"""The MagIC metadata tables as an editor sees them.

The locations, sites, samples, specimens and ages tables are where an analyst
types in what no instrument file carries: coordinates, lithologies, ages,
orientations, citations. This module is the UI-free side of editing them --
which columns a table has and in what order, what each column means and which
values it admits, the rows a table is owed by the tables beneath it, and the
reading and writing of one table -- so that any front end (the hub's Metadata
page, a notebook) shows the same thing and writes the same file.

Everything about a column comes from the MagIC 3 data model and its
controlled vocabularies, both read from the copies bundled with PmagPy
(:func:`pmagpy.magic_project.data_model`), so nothing here waits on
earthref.org.
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from pmagpy import magic_project as mp

#: the tables this module edits, in the order the hierarchy runs
TABLES = ("locations", "sites", "samples", "specimens", "ages")
#: the name column of each table (ages has none: a row names whichever level it dates)
NAME_COLUMN = {"locations": "location", "sites": "site", "samples": "sample", "specimens": "specimen"}
#: the table above each, whose name a row carries
PARENT = {"sites": "locations", "samples": "sites", "specimens": "samples"}
#: the table below each, whose rows name this table's members
CHILD = {"locations": "sites", "sites": "samples", "samples": "specimens", "specimens": "measurements"}
LEVELS = ("location", "site", "sample", "specimen")

#: Pmag GUI's defaults for a fresh row, kept so the two agree
DEFAULTS = {"citations": "This study", "result_quality": "g", "result_type": "i", "orientation_quality": "g"}

BACKUP_DIR = "backup_before_pmagpy_apps"


# ---------------------------------------------------------------------------
# What a column is
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Column:
    """One column of a MagIC 3 table, as the data model describes it.

    Attributes:
        name: the column name as written in the file.
        label: the data model's label ("Latitude").
        group: the data model's group ("Geography").
        dtype: "Number", "Integer", "String", "List", "Timestamp", "Matrix" or "Dictionary".
        description: one line.
        required: the data model marks it ``required()``.
        unit: "Degrees", "Am^2", ... or "".
        vocabulary: the controlled values, when the column has a vocabulary.
        suggested: the suggested values, when it has those instead.
        minimum, maximum: numeric bounds from ``min()``/``max()``, or None.
        examples: what the data model shows as examples.
        position: the data model's column order within the table.
    """
    name: str
    label: str
    group: str
    dtype: str
    description: str
    required: bool
    unit: str = ""
    vocabulary: Tuple[str, ...] = ()
    suggested: Tuple[str, ...] = ()
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    examples: Tuple[str, ...] = ()
    position: int = 0

    @property
    def is_list(self) -> bool:
        """Colon-delimited values (lithologies, method_codes, citations ...)."""
        return self.dtype == "List"

    @property
    def is_numeric(self) -> bool:
        return self.dtype in ("Number", "Integer")

    @property
    def title(self) -> str:
        """The label with its unit: "Latitude (Degrees)"."""
        return f"{self.label} ({self.unit})" if self.unit else self.label


_COLUMNS: Dict[str, Dict[str, Column]] = {}


def _bound(validations, which: str) -> Optional[float]:
    for v in validations or ():
        m = re.fullmatch(rf'{which}\((-?[\d.]+)\)', str(v))
        if m:
            return float(m.group(1))
    return None


def _vocabulary():
    from pmagpy import controlled_vocabularies3 as cv3
    return cv3.Vocabulary(dmodel=mp.data_model(True))


def columns(table: str) -> Dict[str, Column]:
    """Every column the data model defines for ``table``, name -> Column, in the model's order."""
    if table not in _COLUMNS:
        dm = mp.data_model(True).dm[table].sort_values("position", kind="stable")
        vocab = _vocabulary()
        cols = {}
        for name, row in dm.iterrows():
            validations = row["validations"] if isinstance(row["validations"], list) else []
            examples = row["examples"] if isinstance(row["examples"], list) else []
            cols[name] = Column(
                name=name, label=str(row["label"]), group=str(row["group"]), dtype=str(row["type"]),
                description=str(row["description"]) if not mp.is_null(row["description"]) else "",
                required="required()" in validations,
                unit=str(row["unit"]) if not mp.is_null(row["unit"]) else "",
                vocabulary=tuple(str(v) for v in vocab.vocabularies.get(name, ())),
                suggested=tuple(str(v) for v in vocab.suggested.get(name, ())),
                minimum=_bound(validations, "min"), maximum=_bound(validations, "max"),
                examples=tuple(str(e) for e in examples), position=int(row["position"]))
        _COLUMNS[table] = cols
    return _COLUMNS[table]


def column(table: str, name: str) -> Optional[Column]:
    return columns(table).get(name)


def required_columns(table: str) -> List[str]:
    return [c.name for c in columns(table).values() if c.required]


def groups(table: str) -> List[str]:
    """The data model's column groups for ``table``, in its order."""
    seen = []
    for c in columns(table).values():
        if c.group not in seen:
            seen.append(c.group)
    return seen


def order_columns(table: str, present: Iterable[str]) -> List[str]:
    """The columns to show, in the order an editor wants them.

    The table's own name first, then its parent's, then the required columns
    (present or not -- an empty required column is a gap to be seen), then
    every other column present, all in data-model order. Columns the model
    does not know (an application's own, a converter's leftover) come last so
    they are not lost on saving.
    """
    present = list(present)
    model = columns(table)
    wanted = set(present) | set(required_columns(table))
    if table in NAME_COLUMN:
        lead = [NAME_COLUMN[table]] + ([NAME_COLUMN[PARENT[table]]] if table in PARENT else [])
    else:
        lead = list(LEVELS)                      # ages: a row names whichever level it dates
    lead = [c for c in lead if c in model]
    ordered = lead + [c for c in model if c in wanted and c not in lead]
    return ordered + [c for c in present if c not in model]


# ---------------------------------------------------------------------------
# Reading and writing one table
# ---------------------------------------------------------------------------
def table_path(directory: str, table: str) -> str:
    return os.path.join(directory, table + ".txt")


def read_table(directory: str, table: str) -> Optional[pd.DataFrame]:
    """A MagIC 3 table as strings, cell for cell as the file has it; None when absent."""
    path = table_path(directory, table)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        first = fh.readline()
    if not first.startswith("tab"):
        return None
    df = pd.read_csv(path, sep="\t", header=1, dtype=str, keep_default_na=False, encoding="utf-8",
                     encoding_errors="replace", low_memory=False)
    df.columns = [c.strip() for c in df.columns]
    return df.reset_index(drop=True)


def read_names(directory: str, table: str) -> pd.DataFrame:
    """The name columns of a table (levels only), or an empty frame."""
    df = read_table(directory, table)
    if df is None:
        return pd.DataFrame(columns=list(LEVELS))
    return df[[c for c in LEVELS if c in df.columns]]


@dataclass
class EditorFrame:
    """A table laid out for editing.

    Attributes:
        table: which table.
        df: string cells, "" for blank, one row per row of the file, plus any
            stub rows; columns in :func:`order_columns` order.
        stubs: names that had no row in the file and were given one from the
            table below (or from measurements).
        exists: the file was there (False for a table built from names alone).
    """
    table: str
    df: pd.DataFrame
    stubs: List[str] = field(default_factory=list)
    exists: bool = True

    @property
    def key(self) -> str:
        return NAME_COLUMN.get(self.table, "")


def owed_rows(directory: str, table: str) -> pd.DataFrame:
    """The rows the table beneath says this table should have: one per distinct name it refers to.

    For sites that is every ``site`` the samples table names, with its
    ``location`` when the samples carry one; for specimens it is every
    specimen in measurements. The ages table is owed nothing.
    """
    key = NAME_COLUMN.get(table)
    child = CHILD.get(table)
    if not key or not child:
        return pd.DataFrame(columns=[key] if key else [])
    below = read_names(directory, child)
    if key not in below.columns or not len(below):
        return pd.DataFrame(columns=[key])
    parent = LEVELS[LEVELS.index(key) - 1] if LEVELS.index(key) > 0 else None
    cols = [key] + ([parent] if parent and parent in below.columns else [])
    rows = below[cols].replace("", pd.NA).dropna(subset=[key])
    rows = rows.groupby(key, sort=False, as_index=False).first().fillna("")
    return rows.reset_index(drop=True)


def editor_frame(directory: str, table: str) -> EditorFrame:
    """Read ``table`` for editing: its rows, stub rows for names it is owed, columns in editor order."""
    df = read_table(directory, table)
    exists = df is not None
    if df is None:
        df = pd.DataFrame(columns=[NAME_COLUMN[table]] if table in NAME_COLUMN else list(LEVELS))
    stubs: List[str] = []
    key = NAME_COLUMN.get(table)
    if key:
        owed = owed_rows(directory, table)
        have = set(df[key].astype(str)) if key in df.columns else set()
        new = owed[~owed[key].astype(str).isin(have)]
        if len(new):
            stubs = new[key].astype(str).tolist()
            df = pd.concat([df, new], ignore_index=True, sort=False)
    for c in order_columns(table, df.columns):
        if c not in df.columns:
            df[c] = ""
    df = df[order_columns(table, df.columns)].fillna("").astype(str)
    return EditorFrame(table=table, df=df.reset_index(drop=True), stubs=stubs, exists=exists)


def blank_row(table: str, frame_columns: Iterable[str]) -> dict:
    """A new row for the editor: Pmag GUI's defaults in the columns that take them, "" elsewhere."""
    return {c: DEFAULTS.get(c, "") for c in frame_columns}


def fill_defaults(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Pmag GUI's defaults in the blank cells of the columns that have one. Returns (frame, cells filled)."""
    df = df.copy()
    filled = 0
    for col, value in DEFAULTS.items():
        if col in df.columns:
            blank = df[col].astype(str).str.strip() == ""
            filled += int(blank.sum())
            df.loc[blank, col] = value
    return df, filled


def backup_exists(directory: str, table: str) -> bool:
    return os.path.exists(os.path.join(directory, BACKUP_DIR, table + ".txt"))


def backup_once(directory: str, table: str) -> Optional[str]:
    """Copy ``<table>.txt`` into the backup folder the first time it is about to be rewritten."""
    src = table_path(directory, table)
    if not os.path.isfile(src):
        return None
    dst = os.path.join(directory, BACKUP_DIR, table + ".txt")
    if os.path.exists(dst):
        return None
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def save_table(directory: str, table: str, df: pd.DataFrame, backup: bool = True) -> str:
    """Write the edited frame as ``<table>.txt``.

    Cells are written as typed; columns with nothing in them are left out of
    the file (a required column that stays blank is a validation finding, not
    a column of empty tabs). Rows with no name are dropped -- they are the
    editor's blank rows that were never filled in. The original file is copied
    into ``backup_before_pmagpy_apps/`` the first time it is rewritten.
    """
    out = df.copy().fillna("").astype(str)
    for c in out.columns:
        out[c] = out[c].str.strip()
    key = NAME_COLUMN.get(table)
    if key and key in out.columns:
        out = out[out[key] != ""]
    elif table == "ages":
        named = [c for c in LEVELS if c in out.columns]
        if named:
            out = out[(out[named] != "").any(axis=1)]
    keep = [c for c in out.columns if (out[c] != "").any()]
    out = out[keep]
    if backup:
        backup_once(directory, table)
    path = table_path(directory, table)
    if len(out) == 0:
        # nothing left to say: an empty table is no table
        if os.path.exists(path):
            os.remove(path)
        return path
    mp.magic_write(path, out.reset_index(drop=True), table)
    return path


# ---------------------------------------------------------------------------
# Filling in what the other tables already know
# ---------------------------------------------------------------------------
def location_bounds(directory: str) -> Dict[str, Dict[str, str]]:
    """lat_n/lat_s/lon_e/lon_w per location from the site coordinates (samples when sites have none).

    Longitudes are taken as the file has them (0-360 or -180-180); a location
    straddling the dateline is not resolved here.
    """
    for table in ("sites", "samples"):
        df = read_table(directory, table)
        if df is None or not {"location", "lat", "lon"} <= set(df.columns):
            continue
        lat = pd.to_numeric(df["lat"], errors="coerce")
        lon = pd.to_numeric(df["lon"], errors="coerce")
        ok = lat.notna() & lon.notna() & (df["location"] != "")
        if not ok.any():
            continue
        bounds = {}
        for loc, group in df[ok].groupby("location"):
            la, lo = lat[group.index], lon[group.index]
            bounds[str(loc)] = {"lat_n": f"{la.max():g}", "lat_s": f"{la.min():g}",
                                "lon_e": f"{lo.max():g}", "lon_w": f"{lo.min():g}"}
        return bounds
    return {}


def fill_location_bounds(directory: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Put the site-derived bounds into the blank bound cells of a locations frame. Returns (frame, cells filled)."""
    bounds = location_bounds(directory)
    df = df.copy()
    filled = 0
    for col in ("lat_n", "lat_s", "lon_e", "lon_w"):
        if col not in df.columns:
            df[col] = ""
    for i, row in df.iterrows():
        b = bounds.get(str(row.get("location", "")))
        if not b:
            continue
        for col, value in b.items():
            if str(row[col]).strip() == "":
                df.at[i, col] = value
                filled += 1
    return df, filled


def parent_values(directory: str, table: str, column_name: str) -> Dict[str, str]:
    """name -> value of ``column_name`` in the table above, for filling a column down (e.g. site lat onto samples)."""
    parent = PARENT.get(table)
    if not parent:
        return {}
    above = read_table(directory, parent)
    pkey = NAME_COLUMN[parent]
    if above is None or column_name not in above.columns or pkey not in above.columns:
        return {}
    values = above[above[column_name].astype(str).str.strip() != ""]
    return dict(zip(values[pkey].astype(str), values[column_name].astype(str)))


def fill_from_parent(directory: str, table: str, df: pd.DataFrame, column_names: Iterable[str]) -> Tuple[pd.DataFrame, int]:
    """Copy the parent's values into blank cells of ``column_names`` (a sample takes its site's lat/lon, lithologies ...)."""
    parent = PARENT.get(table)
    if not parent:
        return df, 0
    pkey = NAME_COLUMN[parent]
    df = df.copy()
    filled = 0
    if pkey not in df.columns:
        return df, 0
    for col in column_names:
        lookup = parent_values(directory, table, col)
        if not lookup:
            continue
        if col not in df.columns:
            df[col] = ""
        blank = df[col].astype(str).str.strip() == ""
        fill = df.loc[blank, pkey].astype(str).map(lookup)
        found = fill.notna()
        df.loc[fill[found].index, col] = fill[found]
        filled += int(found.sum())
    return df, filled


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    """One thing the validator objects to, placed on the table."""
    row: str        # the row's name (the site, the specimen ...), "" for a table-wide finding
    column: str
    problem: str


def check_table(directory: str, table: str) -> List[Finding]:
    """Run PmagPy's MagIC validator on one table and return its findings as cells.

    Missing required columns come back as findings with an empty row, so a
    caller can say "lithologies: required" at the top of the column.
    """
    report = mp.validate_directory(directory, tables=(table,)).get(table)
    if not report:
        return []
    findings = [Finding(c["row"], c["column"], c["problem"]) for c in report["failing_items"]]
    for col in report["missing_cols"]:
        findings.append(Finding("", col, "required column, not in the table"))
    for grp in report["missing_groups"]:
        findings.append(Finding("", "", f"no column from the required group {grp}"))
    return findings
