"""The MagIC metadata tables as an editor sees them.

The locations, sites, samples, specimens and ages tables are where an analyst
types in what no instrument file carries: coordinates, lithologies, ages,
orientations, citations. This module is the UI-free side of editing them --
which columns a table has and in what order, what each column means and which
values it admits, the rows a table is owed by the tables beneath it, and the
reading and writing of one table -- so that any front end (the hub's Metadata
page, a notebook) shows the same thing and writes the same file.

The criteria table rides along: the acceptance criteria a study applies to its
results (``specimens.dir_mad_free <= 5`` ...) are edited in the same grid, and
the last section evaluates them against the tables they name so an editor can
see how many rows each criterion lets through.

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

#: the tables this module edits, in the order the hierarchy runs, then the criteria that judge them
TABLES = ("locations", "sites", "samples", "specimens", "ages", "criteria")
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

#: the criteria table's columns in the model's order: the four required ones first
CRITERIA_COLUMNS = ("criterion", "table_column", "criterion_operation", "criterion_value", "description", "citations")
#: the tables a criterion may judge (``table_column`` = "<table>.<column>")
CRITERIA_TABLES = ("specimens", "samples", "sites", "locations", "measurements")
#: the criterion names PmagPy's tools use, by what they judge: DE = directions, IE = intensities; a study may coin its own
CRITERION_NAMES = ("DE-SPEC", "DE-SAMP", "DE-SITE", "IE-SPEC", "IE-SAMP", "IE-SITE", "NPOLE", "RPOLE")


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
                unit=str(row["unit"]) if "unit" in row and not mp.is_null(row["unit"]) else "",   # criteria has no unit column
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
    they are not lost on saving. The ages table leads with the four level
    names; criteria follow the model's order, which already reads as a
    sentence (criterion, table_column, operation, value).
    """
    present = list(present)
    model = columns(table)
    wanted = set(present) | set(required_columns(table))
    if table in NAME_COLUMN:
        lead = [NAME_COLUMN[table]] + ([NAME_COLUMN[PARENT[table]]] if table in PARENT else [])
    elif table == "ages":
        lead = list(LEVELS)                      # a row names whichever level it dates
    else:
        lead = []
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
        first = {"ages": list(LEVELS), "criteria": list(CRITERIA_COLUMNS)}.get(table, [NAME_COLUMN.get(table)])
        df = pd.DataFrame(columns=[c for c in first if c])
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
    editor's blank rows that were never filled in (for criteria, a row with
    none of its four required cells). The original file is copied into
    ``backup_before_pmagpy_apps/`` the first time it is rewritten.
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
    elif table == "criteria":
        named = [c for c in CRITERIA_COLUMNS[:4] if c in out.columns]
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


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------
def default_criteria() -> pd.DataFrame:
    """PmagPy's default acceptance criteria as a MagIC 3 criteria table.

    The values are those of :func:`pmagpy.pmag.default_criteria` (the ``-dcr``
    defaults of the command-line tools and Pmag GUI), written straight in the
    3.0 vocabulary the data model's ``criteria_map`` gives them. Directional
    criteria are named ``DE-SPEC``/``DE-SAMP``/``DE-SITE`` and intensity
    criteria ``IE-SPEC``/``IE-SITE`` as the PmagPy tools name them.
    """
    rows = [
        ("DE-SPEC", "specimens.dir_mad_free", "<=", "5", "Criteria for selection of specimen direction"),
        ("DE-SAMP", "samples.dir_alpha95", "<=", "5", "Criteria for selection of sample direction"),
        ("DE-SITE", "sites.dir_n_samples", ">=", "5", "Criteria for selection of site direction"),
        ("DE-SITE", "sites.dir_n_specimens_lines", ">=", "4", "Criteria for selection of site direction"),
        ("DE-SITE", "sites.dir_k", ">=", "50", "Criteria for selection of site direction"),
        ("IE-SPEC", "specimens.int_n_measurements", ">=", "4", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_n_ptrm", ">=", "2", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_drats", "<=", "20", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_b_beta", "<=", "0.1", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_maxdev", "<=", "15", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_fvds", ">=", "0.7", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_q", ">=", "1.0", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_dang", "<=", "10", "Criteria for selection of specimen intensity"),
        ("IE-SPEC", "specimens.int_mad_free", "<=", "10", "Criteria for selection of specimen intensity"),
        ("IE-SITE", "sites.int_n_samples", ">=", "2", "Criteria for selection of site intensity"),
        ("IE-SITE", "sites.int_abs_sigma", "<=", "5e-6", "Criteria for selection of site intensity"),
        ("IE-SITE", "sites.int_abs_sigma_perc", "<=", "15", "Criteria for selection of site intensity"),
    ]
    df = pd.DataFrame(rows, columns=list(CRITERIA_COLUMNS[:5]))
    df["citations"] = DEFAULTS["citations"]
    return df


def add_default_criteria(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Append the default criteria a criteria frame does not have yet (same criterion and table_column). Returns (frame, rows added)."""
    df = df.copy().fillna("").astype(str)
    for c in CRITERIA_COLUMNS:
        if c not in df.columns:
            df[c] = ""
    have = set(zip(df["criterion"].str.strip(), df["table_column"].str.strip()))
    new = default_criteria()
    new = new[[(c, t) not in have for c, t in zip(new["criterion"], new["table_column"])]]
    out = pd.concat([df, new], ignore_index=True, sort=False).fillna("")
    return out[order_columns("criteria", out.columns)], len(new)


def table_columns() -> List[str]:
    """Every ``<table>.<column>`` a criterion may name, in data-model order, result tables first."""
    return [f"{t}.{c}" for t in CRITERIA_TABLES for c in columns(t)]


def split_table_column(table_column: str) -> Tuple[str, str, str]:
    """``"specimens.dir_mad_free"`` -> ("specimens", "dir_mad_free", ""); the third item names what is wrong when it is.

    A table written in the singular ("site.dir_polarity", which older files
    have) is taken as the plural it means, with the slip reported.
    """
    text = str(table_column).strip()
    if "." not in text:
        return "", "", f"'{text}' is not written as table.column"
    table, column = text.split(".", 1)
    if table in CRITERIA_TABLES:
        return table, column, ""
    if table + "s" in CRITERIA_TABLES:
        return table + "s", column, f"the table is '{table + 's'}', not '{table}'"
    return table, column, f"no MagIC table '{table}'"


def criterion_mask(values: pd.Series, operation: str, value: str) -> Tuple[pd.Series, pd.Series, str]:
    """Which cells of ``values`` satisfy ``<operation> <value>``.

    Returns (passing, blank, problem): two boolean Series on the values' index
    and an explanation when the criterion cannot be evaluated (then nothing
    passes). Blank cells never pass -- a record without the statistic fails
    the criterion, as :func:`pmagpy.pmag.grade` has always ruled -- but are
    reported apart so an editor can tell "not computed" from "rejected".
    The comparison operations read numbers; ``=``/``equals`` compare numbers
    when both sides are numbers and text otherwise; the text operations
    (``contains`` ...) work on the cell as written.
    """
    text = values.fillna("").astype(str).str.strip()
    blank = text == ""
    value = str(value).strip()
    op = str(operation).strip()
    none = pd.Series(False, index=values.index)
    if op in ("<", "<=", ">", ">="):
        threshold = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        if pd.isna(threshold):
            return none, blank, f"'{value}' is not a number to compare with {op}"
        numbers = pd.to_numeric(text, errors="coerce")
        passing = {"<": numbers < threshold, "<=": numbers <= threshold,
                   ">": numbers > threshold, ">=": numbers >= threshold}[op]
        return passing.fillna(False).astype(bool), blank, ""
    if op in ("=", "equals"):
        threshold = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
        numbers = pd.to_numeric(text, errors="coerce")
        if not pd.isna(threshold):
            passing = (numbers == threshold) | (text == value)
        else:
            passing = text == value
        return passing.fillna(False).astype(bool) & ~blank, blank, ""
    if op == "begins with":
        return text.str.startswith(value) & ~blank, blank, ""
    if op == "ends with":
        return text.str.endswith(value) & ~blank, blank, ""
    if op == "contains":
        return text.str.contains(value, regex=False) & ~blank, blank, ""
    if op == "does not contain":
        return ~text.str.contains(value, regex=False) & ~blank, blank, ""
    return none, blank, f"'{op}' is not a criterion operation the data model knows"


@dataclass
class CriterionCheck:
    """One criteria row evaluated against the table it names.

    Attributes:
        row: the row's position in the criteria frame.
        criterion, table_column, operation, value: the row as written.
        table, column: what ``table_column`` resolved to.
        rows: rows of the target table; passing: how many satisfy the criterion;
            blank: how many have no value in the column.
        problem: why the row could not be evaluated ("" when it could).
        note: a slip that did not stop the evaluation (a table named in the singular).
    """
    row: int
    criterion: str
    table_column: str
    operation: str
    value: str
    table: str = ""
    column: str = ""
    rows: int = 0
    passing: int = 0
    blank: int = 0
    problem: str = ""
    note: str = ""

    @property
    def failing(self) -> int:
        return self.rows - self.passing - self.blank

    def summary(self) -> str:
        """"231 of 300 pass, 12 blank" (with the note, if any) or the problem."""
        if self.problem:
            return self.problem
        bits = [f"{self.passing} of {self.rows} pass"]
        if self.blank:
            bits.append(f"{self.blank} blank")
        return ", ".join(bits) + (f" — {self.note}" if self.note else "")


def check_criteria(directory: str, df: pd.DataFrame) -> List[CriterionCheck]:
    """Evaluate every row of a criteria frame against the tables in ``directory``.

    A row whose table is not there, whose column is not in the table, or whose
    operation or value cannot be read comes back with a ``problem`` instead
    of counts. Rows with nothing in them are skipped.
    """
    checks: List[CriterionCheck] = []
    frames: Dict[str, Optional[pd.DataFrame]] = {}
    df = df.fillna("").astype(str)
    for i, row in df.iterrows():
        get = lambda c: str(row.get(c, "")).strip()   # noqa: E731
        check = CriterionCheck(int(i), get("criterion"), get("table_column"), get("criterion_operation"), get("criterion_value"))
        if not any((check.criterion, check.table_column, check.operation, check.value)):
            continue
        table, column, problem = split_table_column(check.table_column)
        check.table, check.column = table, column
        if problem and (not table or table not in CRITERIA_TABLES):
            check.problem = problem
            checks.append(check)
            continue
        check.note = problem
        if table not in frames:
            frames[table] = read_table(directory, table)
        target = frames[table]
        if target is None:
            check.problem = f"no {table}.txt in the directory"
        elif column not in target.columns:
            check.problem = f"{table}.txt has no column {column}"
        else:
            passing, blank, bad = criterion_mask(target[column], check.operation, check.value)
            check.rows, check.passing, check.blank = len(target), int(passing.sum()), int(blank.sum())
            check.problem = bad
        checks.append(check)
    return checks


def passing_rows(table_df: pd.DataFrame, criteria: pd.DataFrame, table: str, criterion: Optional[str] = None,
                 blank_fails: bool = True) -> pd.Series:
    """The rows of ``table_df`` that satisfy every criterion aimed at ``table``.

    Args:
        table_df: a MagIC table as strings (:func:`read_table`).
        criteria: a criteria table.
        table: which table ``table_df`` is ("specimens" ...).
        criterion: judge by the rows of this criterion name only (``"DE-SPEC"``);
            None applies every criterion that names the table.
        blank_fails: a row without a value in the judged column fails the
            criterion (:func:`pmagpy.pmag.grade`'s rule); False lets such a
            row through, so a criterion only bites where the statistic exists.

    Returns:
        A boolean Series on ``table_df``'s index. With no applicable criterion
        every row passes. A criterion naming a column the table lacks is a
        blank cell in every row.
    """
    ok = pd.Series(True, index=table_df.index)
    criteria = criteria.fillna("").astype(str)
    for _, row in criteria.iterrows():
        if criterion is not None and row.get("criterion", "").strip() != criterion:
            continue
        t, column, _ = split_table_column(row.get("table_column", ""))
        if t != table or not column:
            continue
        values = table_df[column] if column in table_df.columns else pd.Series("", index=table_df.index)
        passing, blank, _ = criterion_mask(values, row.get("criterion_operation", ""), row.get("criterion_value", ""))
        ok &= passing | (blank & ~blank_fails)
    return ok
