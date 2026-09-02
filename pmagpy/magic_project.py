"""
Shared MagIC Data Model 3 project infrastructure.

This module holds the parts of a MagIC 3 analysis session that have nothing to
do with *which* analysis is being done: reading a contribution, building the
specimen -> sample -> site -> location hierarchy, sample orientations, step
labelling, the export merge policy (which rows an application owns and which
it inherits), backups, stamping and validation.

It is used by both MagIC 3-native successors to the wxPython GUIs --
``pmagpy.demag`` (PmagPy Directions, replacing ``demag_gui.py``) and
``pmagpy.paleointensity`` (PmagPy Paleointensity, replacing
``thellier_gui.py``) -- so that the two agree on how a study is loaded and how
results are written back.

Nothing here imports Panel, Bokeh, wxPython or any browser state, and nothing
here converts MagIC 3 data to the 2.5 data model: canonical MagIC 3 column
names are used from input through export.
"""
from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import numpy as np
import pandas as pd

import pmagpy.contribution_builder as cb

try:
    from pmagpy import version as _pmagpy_version
    PMAGPY_VERSION = _pmagpy_version.version
except Exception:  # pragma: no cover
    PMAGPY_VERSION = "pmagpy"


def software_tag(app_id: str) -> str:
    """The ``software_packages`` value an application stamps on its rows."""
    return f"{PMAGPY_VERSION}:{app_id}"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COORD_SPECIMEN, COORD_GEOGRAPHIC, COORD_TILT = -1, 0, 100
COORD_NAMES = {COORD_SPECIMEN: "specimen",
               COORD_GEOGRAPHIC: "geographic",
               COORD_TILT: "tilt-corrected"}
COORD_CODES = {name: code for code, name in COORD_NAMES.items()}

INTENSITY_COLUMNS = ("magn_moment", "magn_volume", "magn_mass", "magn_uncal")
# orientation codes that are never the primary azimuth source
NON_PRIMARY_SO_CODES = ("SO-ASC", "SO-POM")
KELVIN_OFFSET = 273.0

LEVELS = ("specimen", "sample", "site", "location")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def is_null(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and np.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def to_float(value, default=np.nan) -> float:
    try:
        if is_null(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def split_codes(method_codes) -> list[str]:
    if is_null(method_codes):
        return []
    return [c.strip() for c in str(method_codes).split(":") if c.strip()]


def join_codes(codes) -> str:
    return ":".join(sorted(set(c for c in codes if c)))


def natural_key(name: str):
    """Sort key that orders 'sp2' before 'sp10'."""
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", str(name))]


def first_valid(series: pd.Series):
    """First non-null, non-blank value of a Series, or None."""
    valid = series.dropna()
    valid = valid[valid.astype(str).str.strip() != ""]
    return valid.iloc[0] if len(valid) else None


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
    """Human readable label for a treatment step ('NRM', '10 mT', '500C')."""
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
# Sample orientation
# ---------------------------------------------------------------------------
@dataclass
class Orientation:
    """Sample orientation used for the specimen -> geographic -> tilt chain."""
    sample: str
    azimuth: float = np.nan
    dip: float = np.nan
    bed_dip_direction: float = np.nan
    bed_dip: float = np.nan
    method_codes: list = field(default_factory=list)

    @property
    def has_geographic(self) -> bool:
        return not (np.isnan(self.azimuth) or np.isnan(self.dip))

    @property
    def has_tilt(self) -> bool:
        return self.has_geographic and not (np.isnan(self.bed_dip_direction)
                                            or np.isnan(self.bed_dip))


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
            so_codes = [c for c in split_codes(row.get("method_codes", ""))
                        if c.startswith("SO-") and c not in NON_PRIMARY_SO_CODES]
            orient.method_codes = so_codes
            for col, attr in (("bed_dip_direction", "bed_dip_direction"), ("bed_dip", "bed_dip")):
                if col in rows.columns:
                    val = to_float(row.get(col))
                    if np.isnan(val):
                        val = to_float(first_valid(pd.to_numeric(rows[col], errors="coerce")))
                    setattr(orient, attr, val)
    return orient


# ---------------------------------------------------------------------------
# The MagIC 3 data model (parsed once per process)
# ---------------------------------------------------------------------------
_DATA_MODEL: dict = {}


def data_model(offline: bool = True):
    """The MagIC 3 data model, parsed once per process.

    With ``offline`` the bundled copies of the data model *and* of the
    controlled vocabularies are used (``pmag_env.set_env.OFFLINE``), so loading
    a directory never waits on earthref.org -- the vocabulary fetch otherwise
    runs once per process with several 3-second timeouts.
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


def model_columns(table: str, offline: bool = True) -> set:
    """The set of MagIC 3 column names defined for ``table``."""
    return set(data_model(offline).dm[table].index)


# ---------------------------------------------------------------------------
# Export policy: which columns are results, which are inherited metadata
# ---------------------------------------------------------------------------
_RESULT_PREFIXES = ("dir_", "vgp_", "pole_", "int_", "aniso_", "hyst_", "rem_", "meas_", "vadm", "vdm", "pdm",
                    "padm", "paleolat", "critical_temp", "susc_", "curie", "magn_", "treat_", "result_")
_RESULT_COLUMNS = {"method_codes", "citations", "software_packages", "description", "analysts", "experiments",
                   "measurements", "criteria", "result_names", "timestamp"}


def is_metadata_column(column: str) -> bool:
    """True for descriptive columns that a new result row should inherit."""
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


def directional_rows(existing: pd.DataFrame) -> pd.Series:
    """Boolean mask of rows that hold a *directional* result."""
    mask = pd.Series(False, index=existing.index)
    if "dir_dec" in existing.columns:
        mask |= pd.to_numeric(existing["dir_dec"], errors="coerce").notna()
    if "method_codes" in existing.columns:
        codes = existing["method_codes"].fillna("").astype(str)
        mask |= codes.str.contains("LP-DIR|DE-BF|DE-FM|DE-DI|DE-VGP", regex=True)
    return mask


def intensity_rows(existing: pd.DataFrame) -> pd.Series:
    """Boolean mask of rows that hold a *paleointensity* result.

    Paleointensity specimen rows also carry ``dir_dec`` (the direction of the
    NRM segment) and a ``DE-BFL`` code, so a directional application must not
    mistake them for its own rows -- and vice versa.
    """
    mask = pd.Series(False, index=existing.index)
    for col in ("int_abs", "int_rel", "int_abs_sigma", "int_b", "vadm", "vdm"):
        if col in existing.columns:
            mask |= pd.to_numeric(existing[col], errors="coerce").notna()
    if "method_codes" in existing.columns:
        codes = existing["method_codes"].fillna("").astype(str)
        mask |= codes.str.contains("LP-PI", regex=False)
    return mask


def merge_results(existing: Optional[pd.DataFrame], new: pd.DataFrame, key: str, owned,
                  owns: Optional[Callable[[pd.DataFrame], pd.Series]] = None) -> pd.DataFrame:
    """Replace the rows an application owns; keep and inherit everything else.

    ``owned`` are the entity names (specimens, samples ...) the application has
    measurement data for: their old result rows are dropped whether or not a
    new result exists (a deleted interpretation must disappear), and an entity
    left without any row keeps one metadata-only row so that the table
    hierarchy stays intact.

    ``owns`` decides which existing rows count as the application's own; the
    default is the directional policy used by PmagPy Directions (directional
    rows that are not paleointensity results).
    """
    if existing is None or len(existing) == 0:
        return new
    if key not in existing.columns:
        return pd.concat([existing, new], ignore_index=True, sort=False)
    if owns is None:
        def owns(df):
            return directional_rows(df) & ~intensity_rows(df)
    owned = set(str(o) for o in owned)
    names = existing[key].astype(str)
    mine = owns(existing)
    keep = existing[~(mine & names.isin(owned))]
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
    known = model_columns(table)
    extra = [c for c in df.columns if c not in known]
    if extra and warnings is not None:
        warnings.append(f"{table}: dropped non-MagIC columns {extra}")
    return df.drop(columns=extra)


def stamp(df: pd.DataFrame, tag: str, analysts: Optional[str] = None,
          citations: str = "This study") -> pd.DataFrame:
    """Add provenance columns (citations, software_packages, analysts) to result rows."""
    if len(df) == 0:
        return df
    df = df.copy()
    df["citations"] = citations
    df["software_packages"] = tag
    if analysts:
        df["analysts"] = analysts
    return df


def validate_directory(dir_path: str,
                       tables=("specimens", "samples", "sites", "locations", "measurements")) -> dict:
    """Run pmagpy's MagIC validator on the tables in a directory.

    Returns:
        dict table -> None when the table passes (or is absent), otherwise a
        dict with ``bad_rows``, ``bad_cols``, ``missing_cols``,
        ``missing_groups`` and ``failing_items``: one entry per failing *cell*,
        ``{"row": name, "column": column, "problem": text}``, so a caller can
        point at the cell rather than at the table.
    """
    import tempfile
    import warnings as _warnings
    from pmagpy import validate_upload3
    present = [t for t in tables if os.path.exists(os.path.join(dir_path, t + ".txt"))]
    con = cb.Contribution(dir_path, read_tables=present, dmodel=data_model(True))
    report = {}
    # the validator drops a <table>_errors.txt beside whatever it is given; the
    # failures come back from here as cells, so it is not allowed to litter the
    # study directory to say so
    scratch = tempfile.mkdtemp(prefix="magic-validate-")
    for table in present:
        if table not in con.tables:
            continue
        with _warnings.catch_warnings():   # the validator's pandas chatter is not ours to fix here
            _warnings.simplefilter("ignore")
            fail = validate_upload3.validate_table(con, table, output_dir=scratch)
        if not fail:
            report[table] = None
        else:
            _, bad_rows, bad_cols, missing_cols, missing_groups, failing_items = fail
            report[table] = {"bad_rows": list(bad_rows), "bad_cols": list(bad_cols),
                             "missing_cols": list(missing_cols), "missing_groups": list(missing_groups),
                             "failing_items": failing_cells(failing_items)}
    shutil.rmtree(scratch, ignore_errors=True)
    return report


def failing_cells(failing_items) -> list[dict]:
    """One entry per failing cell, whatever shape the validator handed back.

    ``validate_upload3`` returns a frame indexed by the row's name, with a
    ``num`` column, an ``issues`` column of ``{column: problem}`` and a column
    per failing check -- or a plain list when nothing failed. Both become
    ``{"row": ..., "column": ..., "problem": ...}`` so that a caller never has
    to test the truthiness of a DataFrame, which raises.
    """
    if failing_items is None:
        return []
    if not isinstance(failing_items, pd.DataFrame):
        return [{"row": "", "column": "", "problem": str(item)} for item in failing_items]
    cells = []
    for name, row in failing_items.iterrows():
        issues = row.get("issues")
        if not isinstance(issues, dict):
            issues = {column: row[column] for column in failing_items.columns
                      if column not in ("num", "issues") and not is_null(row[column])}
        for column, problem in issues.items():
            cells.append({"row": str(name),
                          "column": str(column).replace("value_pass_", "").replace("_isIn", ""),
                          "problem": str(problem)})
    return cells


# ---------------------------------------------------------------------------
# Hierarchy
# ---------------------------------------------------------------------------
def build_hierarchy(meas: pd.DataFrame, spec_df, samp_df, site_df) -> pd.DataFrame:
    """specimen -> (sample, site, location), preferring the dedicated tables."""
    specimens = pd.Index(pd.unique(meas["specimen"].astype(str)), name="specimen")
    hier = pd.DataFrame(index=specimens, columns=["sample", "site", "location"], dtype=object)

    def lookup(df, key, value):
        if df is None or key not in df.columns or value not in df.columns:
            return {}
        sub = df[[key, value]].dropna()
        sub = sub[sub[value].astype(str).str.strip() != ""]
        return dict(zip(sub[key].astype(str), sub[value].astype(str)))

    spec_to_samp = lookup(meas, "specimen", "sample")
    spec_to_samp.update(lookup(spec_df, "specimen", "sample"))
    samp_to_site = lookup(meas, "sample", "site")
    samp_to_site.update(lookup(samp_df, "sample", "site"))
    site_to_loc = lookup(meas, "site", "location")
    site_to_loc.update(lookup(site_df, "site", "location"))

    hier["sample"] = [spec_to_samp.get(s, "") for s in specimens]
    hier["site"] = [samp_to_site.get(s, "") for s in hier["sample"]]
    hier["location"] = [site_to_loc.get(s, "") for s in hier["site"]]
    return hier


def build_site_coords(site_df, samp_df) -> dict:
    """site -> (lat, lon), from the sites table, falling back to the samples table."""
    coords: dict = {}
    for df in (site_df, samp_df):
        if df is None or not {"site", "lat", "lon"} <= set(df.columns):
            continue
        sub = df[["site", "lat", "lon"]].copy()
        sub["lat"] = pd.to_numeric(sub["lat"], errors="coerce")
        sub["lon"] = pd.to_numeric(sub["lon"], errors="coerce")
        sub = sub.dropna()
        for site, grp in sub.groupby("site"):
            coords.setdefault(str(site), (float(grp["lat"].mean()), float(grp["lon"].mean())))
    return coords


def intensity_column(meas_df: pd.DataFrame) -> Optional[str]:
    """The magnetization column a measurements table actually uses."""
    for col in INTENSITY_COLUMNS:
        if col in meas_df.columns and pd.to_numeric(meas_df[col], errors="coerce").notna().any():
            return col
    return None


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------
class MagicProject:
    """A MagIC 3 contribution read from a directory, with its hierarchy.

    This is the shared substrate under ``pmagpy.demag.DemagData`` and
    ``pmagpy.paleointensity.PintData``: it owns the contribution, the
    hierarchy, the site coordinates and the file-writing policy, and knows
    nothing about fits, Arai plots or statistics.
    """

    #: tables read from a MagIC directory
    TABLES = ("measurements", "specimens", "samples", "sites", "locations", "criteria", "ages")

    def __init__(self, contribution: cb.Contribution, app_id: str = "pmagpy"):
        self.contribution = contribution
        self.app_id = app_id
        self.software_tag = software_tag(app_id)
        self.warnings: list[str] = []

    # ----- construction ----------------------------------------------------
    @classmethod
    def from_directory(cls, directory: str, meas_file: str = "measurements.txt",
                       offline_data_model: bool = True, tables: Iterable[str] = None,
                       app_id: str = "pmagpy") -> "MagicProject":
        con = read_contribution(directory, meas_file=meas_file,
                                offline_data_model=offline_data_model, tables=tables)
        return cls(con, app_id=app_id)

    @property
    def directory(self) -> str:
        return self.contribution.directory

    def table(self, name: str) -> Optional[pd.DataFrame]:
        """A contribution table as a plain DataFrame, or None when absent/empty."""
        table = self.contribution.tables.get(name)
        if table is None or table.df is None or len(table.df) == 0:
            return None
        return table.df.reset_index(drop=True)

    # ----- provenance and output policy ------------------------------------
    def stamp(self, df: pd.DataFrame, analysts: Optional[str] = None) -> pd.DataFrame:
        return stamp(df, self.software_tag, analysts)

    def backup_dir_name(self) -> str:
        return f"backup_before_{self.app_id}"

    def backup_originals(self, output_dir: str, names: Iterable[str]) -> list[str]:
        """Copy the source tables once before the first in-place export.

        Only does anything when writing back into the directory the data was
        read from -- the MagIC workflow of building a contribution in place.
        Returns the list of files copied (empty on later exports).
        """
        if os.path.realpath(output_dir) != os.path.realpath(self.directory):
            return []
        backup = os.path.join(output_dir, self.backup_dir_name())
        copied = []
        for name in names:
            src, dst = os.path.join(self.directory, name), os.path.join(backup, name)
            if os.path.exists(src) and not os.path.exists(dst):
                os.makedirs(backup, exist_ok=True)
                shutil.copy2(src, dst)
                copied.append(dst)
        return copied

    def write_table(self, df: pd.DataFrame, table: str, dir_path: str,
                    custom_name: Optional[str] = None) -> Optional[str]:
        """Write a DataFrame as a MagIC 3 table inside ``dir_path`` only."""
        if df is None or len(df) == 0:
            return None
        name = custom_name or (table + ".txt")
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, name)
        magic_write(path, df, table)
        return path


def read_contribution(directory: str, meas_file: str = "measurements.txt",
                      offline_data_model: bool = True,
                      tables: Iterable[str] = None) -> cb.Contribution:
    """Read a MagIC 3 directory with ``contribution_builder``."""
    tables = list(tables) if tables is not None else \
        ["measurements", "specimens", "samples", "sites", "locations"]
    return cb.Contribution(directory, custom_filenames={"measurements": meas_file},
                           read_tables=tables, dmodel=data_model(offline_data_model))


def magic_write(path: str, df: pd.DataFrame, table: str) -> str:
    """Write a MagIC 3 tab-delimited table through ``contribution_builder``."""
    if table == "measurements" and "measurement" not in df.columns and "experiment" in df.columns:
        # MagicDataFrame adds this column itself — and writes the table into the
        # working directory as a side effect; name the measurements here instead
        df = df.copy()
        steps = df["treat_step_num"].astype(str) if "treat_step_num" in df.columns else pd.Series("", index=df.index)
        df["measurement"] = df["experiment"].astype(str) + steps.where(steps != "nan", "")
    mdf = cb.MagicDataFrame(dtype=table, df=df)
    return mdf.write_magic_file(custom_name=os.path.basename(path),
                                dir_path=os.path.dirname(os.path.realpath(path)) or ".")


# ----- MagIC (EarthRef): finding and downloading a public contribution --------------
#
# Every EarthRef call the applications make goes through these few functions, so
# the HTTP client can be swapped in one place. Nothing here prints; problems are
# raised as MagicDownloadError with a sentence a user can act on.

MAGIC_API = "https://api.earthref.org/v1/MagIC"
MAGIC_DOI_PREFIX = "10.7288/V4/MAGIC/"          # the DOI MagIC mints for a contribution: the id is its tail


class MagicDownloadError(Exception):
    """A contribution could not be found, fetched or unpacked; ``str(err)`` says why."""


@dataclass(frozen=True)
class ContributionRef:
    """What MagIC says about one contribution, from its ``contribution`` row."""
    id: int
    version: int = 0
    doi: str = ""
    contributor: str = ""
    timestamp: str = ""
    lab_names: tuple = ()

    @property
    def label(self) -> str:
        text = f"MagIC contribution {self.id}"
        return f"{text} (version {self.version})" if self.version else text


def parse_contribution_reference(text: str) -> tuple[str, str]:
    """Read a contribution ID or a reference DOI out of whatever a user pastes.

    Accepts the bare id (``20340``), an earthref.org URL, MagIC's own DOI
    (``10.7288/V4/MAGIC/20340``), and a reference DOI with or without a
    ``doi:`` or ``https://doi.org/`` prefix.

    Returns:
        ``("id", "20340")`` or ``("doi", "10.1130/G53450.1")``.
    Raises:
        ValueError: when the text is neither.
    """
    t = text.strip().strip("<>").rstrip("/")
    t = re.sub(r"^(https?://)?(www2?\.)?(dx\.)?doi\.org/", "", t, flags=re.I)
    t = re.sub(r"^(https?://)?(www2?\.)?earthref\.org/MagIC/", "", t, flags=re.I)
    t = re.sub(r"^(doi|magic|id)\s*:?\s*", "", t, flags=re.I).strip()
    if t.isdigit():
        return "id", t
    if t.upper().startswith(MAGIC_DOI_PREFIX):
        tail = t[len(MAGIC_DOI_PREFIX):].strip("/")
        if tail.isdigit():
            return "id", tail
    if re.fullmatch(r"10\.\d{4,9}/\S+", t):
        return "doi", t
    raise ValueError(f"{text.strip()!r} is not a MagIC contribution ID or a DOI")


def _contribution_ref(row: dict) -> ContributionRef:
    return ContributionRef(id=int(row.get("id") or row.get("contribution_id")),
                           version=int(row.get("version") or 0),
                           doi=str(row.get("reference") or ""),
                           contributor=str(row.get("contributor") or ""),
                           timestamp=str(row.get("timestamp") or ""),
                           lab_names=tuple(row.get("lab_names") or ()))


def find_contributions(doi: str, timeout: float = 30) -> list[ContributionRef]:
    """The public contributions whose reference is this DOI, newest version first.

    A paper can have more than one — a corrected version keeps the DOI and gets a
    new id — so the caller chooses; the first entry is the latest.
    """
    import requests
    try:
        response = requests.get(f"{MAGIC_API}/search/contributions",
                                params={"query": f'"{doi}"', "n_max_rows": 50}, timeout=timeout)
    except requests.exceptions.RequestException as err:
        raise MagicDownloadError(f"Could not reach MagIC ({err.__class__.__name__}); check the connection.") from err
    if response.status_code == 204:
        return []
    if response.status_code != 200:
        raise MagicDownloadError(f"MagIC search failed: {response.status_code} {response.reason}")
    rows = response.json().get("results", [])
    # the phrase search matches any text field; keep only the rows whose reference *is* this DOI
    refs = [_contribution_ref(r) for r in rows
            if str(r.get("reference") or "").strip().lstrip("/").lower() == doi.lower()]
    return sorted(refs, key=lambda r: (r.version, r.id), reverse=True)


def fetch_contribution(magic_id, share_key: str = "", timeout: float = 600) -> str:
    """The MagIC text of one contribution, as the ``data`` endpoint serves it.

    Args:
        magic_id: the contribution id.
        share_key: the key a private contribution was shared with; empty for a public one.
    """
    import requests
    params = {"id": str(magic_id)}
    if share_key:
        params["key"] = share_key
    try:
        response = requests.get(f"{MAGIC_API}/data", params=params, timeout=timeout)
    except requests.exceptions.RequestException as err:
        raise MagicDownloadError(f"Could not reach MagIC ({err.__class__.__name__}); check the connection.") from err
    if response.status_code == 204 or (response.status_code == 200 and not response.text.strip()):
        raise MagicDownloadError(f"MagIC has no public contribution with ID {magic_id}.")
    if response.status_code == 401:
        raise MagicDownloadError(f"Contribution {magic_id} is private and the share key does not match.")
    if response.status_code != 200:
        raise MagicDownloadError(f"MagIC returned {response.status_code} {response.reason} for contribution {magic_id}.")
    return response.text


def clean_contribution_text(text: str) -> str:
    """A downloaded file as plain lines: no byte-order mark, no ``\\r``."""
    return text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")


def contribution_tables(text: str) -> list[str]:
    """The table names in a MagIC contribution file, in order.

    Tables start with a ``tab delimited\\tsites`` line (``tab\\tsites`` in files
    PmagPy itself writes) and are separated by ``>>>>>>>>>>`` lines.
    """
    return [_table_name(line) for line in clean_contribution_text(text).splitlines() if _table_name(line)]


def _table_name(line: str) -> str:
    """The table a ``tab delimited\\t<table>`` line starts, or ''."""
    parts = line.split("\t")
    if len(parts) >= 2 and parts[0].strip().lower() in ("tab delimited", "tab"):
        return parts[1].strip()
    return ""


def describe_contribution(text: str) -> ContributionRef:
    """The ``contribution`` row of a downloaded file, if it has one; else a ref with only an id of 0."""
    lines = clean_contribution_text(text).splitlines()
    for i, line in enumerate(lines[:-2]):
        if _table_name(line) == "contribution":
            header = lines[i + 1].split("\t")
            values = lines[i + 2].split("\t")
            row = dict(zip(header, values))
            row["lab_names"] = [s for s in str(row.get("lab_names", "")).split(":") if s]
            try:
                return _contribution_ref(row)
            except (TypeError, ValueError):
                break
    return ContributionRef(id=0)


def unpack_contribution(text: str, directory: str, magic_id: int = 0) -> list[str]:
    """Write a contribution's tables into ``directory`` as ``<table>.txt`` files.

    Args:
        magic_id: the id the file was fetched by. Some older contributions are
            served without an ``id`` in their ``contribution`` row; when so, this
            is written into ``contribution.txt`` so the directory remembers where
            it came from.
    Returns:
        the table names written, in file order.
    Raises:
        MagicDownloadError: when the text holds no MagIC tables.
    """
    from pmagpy import ipmag
    text = clean_contribution_text(text)
    tables = contribution_tables(text)
    if not tables:
        raise MagicDownloadError("That is not a MagIC contribution file: no tables in it.")
    directory = os.path.expanduser(directory)
    os.makedirs(directory, exist_ok=True)
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):       # magic_write announces every table; the caller reports instead
        ok = ipmag.download_magic(txt=text, dir_path=directory, print_progress=False)
    if not ok:
        raise MagicDownloadError(f"Could not unpack the contribution into {directory}.")
    if magic_id and describe_contribution(text).id == 0:
        path = os.path.join(directory, "contribution.txt")
        if os.path.exists(path):
            df = pd.read_csv(path, sep="\t", skiprows=1, dtype=str).fillna("")
        else:
            df = pd.DataFrame([{}])
            tables.insert(0, "contribution")
        df["id"] = str(magic_id)
        with open(path, "w", encoding="utf-8") as fh:        # one row; written plainly, no data-model round trip
            fh.write("tab\tcontribution\n")
            df.to_csv(fh, sep="\t", index=False, lineterminator="\n")
    return tables


def download_contribution(reference: str, directory: str, share_key: str = "",
                          report: Optional[Callable[[str], None]] = None) -> ContributionRef:
    """Find, fetch and unpack a contribution into a directory, by id or by reference DOI.

    Args:
        reference: anything :func:`parse_contribution_reference` accepts.
        directory: where the tables go; created if need be.
        share_key: for a private contribution shared by key (id only).
        report: called with a sentence at each stage, for a status line.
    Returns:
        what MagIC says the contribution is (id, version, reference DOI, ...).
    Raises:
        ValueError: the reference is neither an id nor a DOI.
        MagicDownloadError: nothing found, no connection, or the file would not unpack.
    """
    say = report or (lambda text: None)
    kind, value = parse_contribution_reference(reference)
    if kind == "doi":
        say(f"Looking up {value} in MagIC …")
        found = find_contributions(value)
        if not found:
            raise MagicDownloadError(f"MagIC has no public contribution with reference DOI {value}.")
        chosen = found[0]
        others = f" ({len(found)} versions; taking the latest)" if len(found) > 1 else ""
        say(f"Found {chosen.label}{others}. Downloading …")
        magic_id = chosen.id
    else:
        magic_id = int(value)
        say(f"Downloading MagIC contribution {magic_id} …")
    text = fetch_contribution(magic_id, share_key=share_key)
    say(f"Unpacking {len(text) / 1e6:.1f} MB into {directory} …")
    tables = unpack_contribution(text, directory, magic_id=magic_id)
    ref = describe_contribution(text)
    if ref.id == 0:
        ref = ContributionRef(id=magic_id)
    say(f"{ref.label}: {len(tables)} tables written.")
    return ref
