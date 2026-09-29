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


#: orientation methods in order of preference, as ``pmag.set_priorities`` ranks them
SO_PRIORITY = ("SO-SUN", "SO-GPS-DIFF", "SO-SUN-SIGHT", "SO-SIGHT", "SO-SIGHT-BS", "SO-CMD-NORTH",
               "SO-MAG", "SO-SM", "SO-REC", "SO-V", "SO-CORE", "SO-NO")


def build_orientation(samp_df: Optional[pd.DataFrame], sample: str, site_bedding: Optional[tuple] = None,
                      warnings: Optional[list] = None) -> Optional[Orientation]:
    """Pick the orientation row for a sample from a MagIC 3 samples table.

    See :func:`orientation_from_rows` for the rules. ``samp_df`` may be the
    whole table or just this sample's rows (a caller opening a large study
    groups the table once and passes each sample's rows).
    """
    if samp_df is None or "sample" not in samp_df.columns or len(samp_df) == 0:
        return None
    names = samp_df["sample"]
    if len(samp_df) > 1 or str(names.iloc[0]) != str(sample):
        samp_df = samp_df[names.astype(str) == str(sample)]
        if len(samp_df) == 0:
            return None
    # a sample has a handful of rows: plain dicts are far quicker than a frame here
    return orientation_from_rows(samp_df.to_dict("records"), sample, site_bedding, warnings)


def _so_rank(codes: list) -> int:
    ranks = [SO_PRIORITY.index(c) for c in codes if c in SO_PRIORITY]
    return min(ranks) if ranks else len(SO_PRIORITY)


def orientation_from_rows(rows: list, sample: str, site_bedding: Optional[tuple] = None,
                          warnings: Optional[list] = None) -> Optional[Orientation]:
    """The orientation of a sample from its rows (as dicts), chosen as ``pmag.get_orient`` chooses it.

    MagIC 3 tables may hold several rows per sample (orientation rows, result
    rows, one row per orientation method). Rows flagged
    ``orientation_quality == 'b'`` are skipped; of the rows with both azimuth
    and dip, the one whose orientation method ranks highest in
    :data:`SO_PRIORITY` is used (SO-ASC and SO-POM never supply the azimuth;
    among equals, the first). Bedding comes from the same row, failing that
    from any other row of the sample, failing that from the site
    (``site_bedding``, the sites table's ``(bed_dip_direction, bed_dip)``).
    Rows that give different orientations are reported in ``warnings``.
    """
    rows = [r for r in rows if str(r.get("orientation_quality", "")).strip() != "b"] \
        if any("orientation_quality" in r for r in rows) else list(rows)
    orient = Orientation(sample=str(sample))
    if not rows and site_bedding is None:
        return None
    candidates = []
    for position, row in enumerate(rows):
        az, dip = to_float(row.get("azimuth")), to_float(row.get("dip"))
        if np.isnan(az) or np.isnan(dip):
            continue
        codes = [c for c in split_codes(row.get("method_codes", ""))
                 if c.startswith("SO-") and c not in NON_PRIMARY_SO_CODES]
        if not codes and any(c in NON_PRIMARY_SO_CODES for c in split_codes(row.get("method_codes", ""))):
            continue                          # an SO-ASC/SO-POM row alone never supplies the azimuth
        candidates.append((_so_rank(codes), position, row, codes, az, dip))
    if candidates:
        candidates.sort(key=lambda c: (c[0], c[1]))
        _, _, chosen, codes, az, dip = candidates[0]
        orient.azimuth, orient.dip, orient.method_codes = az, dip, codes
        others = {(round(c[4], 1), round(c[5], 1)) for c in candidates} - {(round(az, 1), round(dip, 1))}
        if others and warnings is not None:
            warnings.append(f"sample {sample}: {len(candidates)} orientation rows disagree; azimuth/dip "
                            f"{az:g}/{dip:g} ({':'.join(codes) or 'no SO- method'}) was used")
    else:
        chosen = None
    bed_rows = ([chosen] if chosen is not None else []) + [r for r in rows if r is not chosen]
    beddings = [(to_float(r.get("bed_dip_direction")), to_float(r.get("bed_dip"))) for r in bed_rows]
    beddings = [b for b in beddings if not (np.isnan(b[0]) or np.isnan(b[1]))]
    for ddir, bdip in beddings[:1]:
        orient.bed_dip_direction, orient.bed_dip = ddir, bdip
    if warnings is not None and len({(round(d, 1), round(b, 1)) for d, b in beddings}) > 1:
        warnings.append(f"sample {sample}: its rows give different bedding; dip direction/dip "
                        f"{orient.bed_dip_direction:g}/{orient.bed_dip:g} was used for the tilt correction")
    if not beddings and site_bedding is not None:
        orient.bed_dip_direction, orient.bed_dip = site_bedding
    if not orient.has_geographic and np.isnan(orient.bed_dip):
        return orient if rows else None
    return orient


def site_bedding_table(site_df: Optional[pd.DataFrame]) -> dict:
    """site -> (bed_dip_direction, bed_dip) from the sites table, where a site gives both."""
    if site_df is None or not {"site", "bed_dip", "bed_dip_direction"} <= set(site_df.columns):
        return {}
    sub = pd.DataFrame({"site": site_df["site"].astype(str),
                        "ddir": pd.to_numeric(site_df["bed_dip_direction"], errors="coerce"),
                        "dip": pd.to_numeric(site_df["bed_dip"], errors="coerce")}).dropna()
    return {site: (float(g["ddir"].iloc[0]), float(g["dip"].iloc[0])) for site, g in sub.groupby("site", sort=False)}


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
#: the members of a mean (a site's samples, a location's sites ...): an application writes its own list;
#: the list of a row being replaced describes a mean that no longer exists and is never carried
LIST_COLUMNS = ("specimens", "samples", "sites", "locations")
#: columns whose values mean something only together, so they are always carried from one row:
#: an age from one row and its unit from another made 1730 AD into 1730 ka
COLUMN_GROUPS = (("age", "age_unit", "age_sigma", "age_low", "age_high"),
                 ("lat", "lon"),
                 ("lat_s", "lat_n", "lon_w", "lon_e"),
                 ("bed_dip", "bed_dip_direction"),
                 ("azimuth", "dip"))
#: annotations of a result row that an application does not produce itself: carried to the new row
#: that replaces it (same name, component and coordinate system) when the new row leaves them empty
ANNOTATION_COLUMNS = ("description", "dir_nrm_origin", "experiments", "analysts", "external_database_ids",
                      "dir_polarity")


def is_metadata_column(column: str) -> bool:
    """True for descriptive columns that a new result row should inherit."""
    return not (column.startswith(_RESULT_PREFIXES) or column in _RESULT_COLUMNS or column in LIST_COLUMNS)


def _blank_to_nan(frame: pd.DataFrame, cols) -> pd.DataFrame:
    frame = frame.copy()
    for c in cols:
        text = frame[c].astype(str).str.strip()
        frame[c] = frame[c].where(~(frame[c].isna() | text.isin(["", "nan", "None"])))
        frame[c] = frame[c].astype(object)
    return frame


def metadata_by_key(existing: pd.DataFrame, key: str, cols) -> pd.DataFrame:
    """One row of metadata per name: each column's first value, but each :data:`COLUMN_GROUPS` from one row."""
    cols = [c for c in cols if c in existing.columns and c != key]
    source = _blank_to_nan(existing[[key] + cols], cols)
    source[key] = source[key].fillna("").astype(str)
    grouped = {c for g in COLUMN_GROUPS for c in g}
    single = [c for c in cols if c not in grouped]
    out = source.groupby(key, sort=False)[single].first() if single else \
        pd.DataFrame(index=pd.Index(pd.unique(source[key]), name=key))
    for group in COLUMN_GROUPS:
        members = [c for c in group if c in cols]
        if not members:
            continue
        # the row that gives the group's leading column (the age, the latitude ...); failing that,
        # the first row that gives any of it
        lead = source[members[0]].notna() if members[0] == group[0] else source[members].notna().any(axis=1)
        rank = np.where(lead, 0, np.where(source[members].notna().any(axis=1), 1, 2))
        ranked = source.assign(_rank=rank)
        ranked = ranked[ranked["_rank"] < 2].sort_values("_rank", kind="stable")
        rows = ranked.groupby(key, sort=False).head(1)
        out = out.join(rows.set_index(key)[members], how="left")
    return out


def carry_metadata(new: pd.DataFrame, existing: Optional[pd.DataFrame], key: str,
                   columns: Optional[tuple] = None) -> pd.DataFrame:
    """Fill empty metadata cells of ``new`` rows from existing rows with the same key.

    Columns that belong together (:data:`COLUMN_GROUPS`: an age and its unit,
    a latitude and longitude ...) are taken from one existing row and only
    into a new row that has none of them; the member lists of a mean
    (:data:`LIST_COLUMNS`) are never carried.

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
    meta = metadata_by_key(existing, key, cols)
    new = new.copy()
    keys = new[key].astype(str)
    grouped = {c for g in COLUMN_GROUPS for c in g}

    def empty(c):
        if c not in new.columns:
            return pd.Series(True, index=new.index)
        return new[c].isna() | new[c].astype(str).str.strip().isin(["", "nan", "None"])

    for c in cols:
        if c in grouped:
            continue
        fill = keys.map(meta[c]) if c in meta.columns else pd.Series(np.nan, index=new.index)
        if c not in new.columns:
            new[c] = fill
        else:
            new[c] = new[c].astype(object).where(~empty(c), fill)
    for group in COLUMN_GROUPS:
        members = [c for c in group if c in cols and c in meta.columns]
        if not members:
            continue
        none_yet = pd.Series(True, index=new.index)
        for c in members:
            none_yet &= empty(c)
        for c in members:
            fill = keys.map(meta[c])
            if c not in new.columns:
                new[c] = np.nan
            new[c] = new[c].astype(object).where(~none_yet, fill)
    return new


def carry_annotations(new: pd.DataFrame, existing: Optional[pd.DataFrame], key: str,
                      columns=ANNOTATION_COLUMNS) -> pd.DataFrame:
    """Keep what a replaced result row said about itself (its description, NRM origin ...).

    A new row inherits these from the existing row it replaces -- the same
    name, component (``dir_comp`` or ``dir_comp_name``) and coordinate system
    -- wherever the new row leaves them empty.
    """
    if existing is None or len(new) == 0 or key not in existing.columns or key not in new.columns:
        return new
    cols = [c for c in columns if c in existing.columns]
    if not cols:
        return new
    match = [c for c in ("dir_comp", "dir_comp_name", "pole_comp_name", "dir_tilt_correction")
             if c in existing.columns and c in new.columns]

    def ids(frame):
        parts = [frame[key].fillna("").astype(str)]
        for c in match:
            values = frame[c]
            if c == "dir_tilt_correction":
                values = pd.to_numeric(values, errors="coerce").map(lambda v: "" if pd.isna(v) else str(int(v)))
            parts.append(values.fillna("").astype(str).str.strip())
        return pd.Series(["\x1f".join(t) for t in zip(*parts)], index=frame.index)

    source = _blank_to_nan(existing[cols], cols)
    source.index = ids(existing).values
    # several existing rows with the same name, component and system (a table
    # without a component column): which one a new row replaces is not known,
    # so none of them lends it anything
    source = source[~source.index.duplicated(keep=False)]
    new = new.copy()
    new_ids = ids(new)
    for c in cols:
        fill = new_ids.map(source[c])
        if c not in new.columns:
            new[c] = fill
        else:
            blank = new[c].isna() | new[c].astype(str).str.strip().isin(["", "nan", "None"])
            new[c] = new[c].astype(object).where(~blank, fill)
    return new


def directional_rows(existing: pd.DataFrame) -> pd.Series:
    """Boolean mask of rows that hold a *directional* result."""
    mask = pd.Series(False, index=existing.index)
    if "dir_dec" in existing.columns:
        mask |= pd.to_numeric(existing["dir_dec"], errors="coerce").notna()
    if "method_codes" in existing.columns:
        codes = existing["method_codes"].fillna("").astype(str)
        # an interpretation code; an LP-DIR-* protocol code alone describes the
        # experiment, as on the minimal row of a specimen without a fit
        mask |= codes.str.contains("DE-BF|DE-FM|DE-DI|DE-VGP", regex=True)
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
                  owns: Optional[Callable[[pd.DataFrame], pd.Series]] = None,
                  produced: Optional[dict] = None, warnings: Optional[list] = None) -> pd.DataFrame:
    """Replace the rows an application owns; keep and inherit everything else.

    ``owned`` are the entity names (specimens, samples ...) the application has
    measurement data for: their old result rows are dropped whether or not a
    new result exists (a deleted interpretation must disappear), and an entity
    left without any row keeps one metadata-only row so that the table
    hierarchy stays intact.

    ``owns`` decides which existing rows count as the application's own; the
    default is the directional policy used by PmagPy Directions (directional
    rows that are not paleointensity results).

    ``produced`` narrows that to the coordinate systems the application
    actually wrote: ``{name: {dir_tilt_correction codes}}``. An owned row in
    another coordinate system -- a tilt-corrected mean of a study whose
    bedding the application cannot read, a system this export left out -- is
    kept, and ``warnings`` says how many were.
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
    mine = owns(existing) & names.isin(owned)
    if produced is not None and "dir_tilt_correction" in existing.columns:
        tilt = pd.to_numeric(existing["dir_tilt_correction"], errors="coerce")
        wrote = pd.Series([pd.isna(t) or int(t) in produced.get(n, ()) for n, t in zip(names, tilt)],
                          index=existing.index)
        kept = mine & ~wrote
        if kept.any() and warnings is not None:
            systems = sorted({COORD_NAMES.get(int(t), str(t)) for t in tilt[kept]})
            warnings.append(f"{key}s: kept {int(kept.sum())} existing {' and '.join(systems)} result rows of "
                            f"{names[kept].nunique()} {key}s that this export did not recompute")
        mine &= wrote
    keep = existing[~mine]
    new_names = set(new[key].astype(str)) if len(new) and key in new.columns else set()
    gone = (owned & set(names)) - set(keep[key].astype(str)) - new_names
    if gone:
        meta_cols = [c for c in existing.columns if c != key and is_metadata_column(c)]
        lost = existing[names.isin(gone)]
        stub = metadata_by_key(lost, key, meta_cols).reset_index()
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
    # read as the applications read (cb.Contribution would rewrite an unnamed measurements.txt)
    try:
        con = read_contribution(dir_path, tables=present)
    except MagicReadError as exc:
        return {"measurements": {"bad_rows": [], "bad_cols": [], "missing_cols": [], "missing_groups": [],
                                 "failing_items": [{"row": "", "column": "", "problem": str(exc)}]}}
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
            cells.append({"row": str(name), "column": plain_column_name(str(column)), "problem": str(problem)})
    return cells


def plain_column_name(check_column: str) -> str:
    """The MagIC column behind a validator check column: ``value_pass_lat_checkMax`` -> ``lat``.

    ``validate_upload3`` names each check ``<kind>_pass_<column>_<function>``,
    with a digit appended when a column has the same check twice.
    """
    import re
    name = re.sub(r"^(value|type|presence)_pass_", "", check_column)
    return re.sub(r"_(isIn|checkMax|checkMin|cv|required\w*|test_type)\d*$", "", name)


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


def mean_position(lats, lons) -> tuple[float, float]:
    """The mean of geographic positions, as the position of the mean unit vector.

    A plain average of longitudes fails across a convention change or the
    antimeridian (-91.7 and 268.3 are the same meridian, and average to
    88.3). The longitude is returned from 0 to 360 when any of the values is
    east of 180, otherwise from -180 to 180.
    """
    lons = np.asarray(lons, dtype=float)
    lat = np.radians(np.asarray(lats, dtype=float))
    lon = np.radians(lons)
    x, y, z = np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)
    mlat = float(np.degrees(np.arctan2(z.mean(), np.hypot(x.mean(), y.mean()))))
    mlon = float(np.degrees(np.arctan2(y.mean(), x.mean())))
    if (lons > 180.0).any():
        mlon %= 360.0
    return mlat, mlon


def build_site_coords(site_df, samp_df, warnings: Optional[list] = None) -> dict:
    """site -> (lat, lon), from the sites table, falling back to the samples table.

    A site with several rows takes the mean position of their coordinates
    (:func:`mean_position`); rows that disagree by more than a few kilometres
    are reported, since one site should have one place.
    """
    coords: dict = {}
    for df in (site_df, samp_df):
        if df is None or not {"site", "lat", "lon"} <= set(df.columns):
            continue
        sub = df[["site", "lat", "lon"]].copy()
        sub["lat"] = pd.to_numeric(sub["lat"], errors="coerce")
        sub["lon"] = pd.to_numeric(sub["lon"], errors="coerce")
        sub = sub.dropna()
        for site, grp in sub.groupby("site"):
            site = str(site)
            if site in coords:
                continue
            lats, lons = grp["lat"].to_numpy(), grp["lon"].to_numpy()
            if len(grp) == 1 or (np.ptp(lats) == 0 and np.ptp(lons) == 0):
                coords[site] = (float(lats[0]), float(lons[0]))
                continue
            coords[site] = mean_position(lats, lons)
            spread = max(np.ptp(lats), np.ptp(((lons - lons[0] + 180.0) % 360.0) - 180.0))
            if spread > 0.05 and warnings is not None:
                warnings.append(f"site {site}: its rows give positions up to {spread:.2f} degrees apart; "
                                "their mean position is used for the VGP")
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
        warnings: list[str] = []
        con = read_contribution(directory, meas_file=meas_file, offline_data_model=offline_data_model,
                                tables=tables, warnings=warnings)
        project = cls(con, app_id=app_id)
        project.warnings.extend(warnings)
        return project

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

    def refresh_tables(self, output_dir: str,
                       tables=("specimens", "samples", "sites", "locations", "criteria")) -> list[str]:
        """Read the result tables again just before an export merges into them; see :func:`refresh_tables`."""
        return refresh_tables(self.contribution, output_dir, tables, self.warnings)

    def reload_table(self, table: str) -> None:
        """Read one table again from the directory (after it was written), as :func:`read_contribution` reads it."""
        path = os.path.join(self.directory, self.contribution.filenames.get(table, table + ".txt"))
        if not os.path.isfile(path):
            self.contribution.tables.pop(table, None)
            return
        _, df = read_table_file(path, expected=table, warnings=self.warnings)
        self.contribution.tables[table] = table_frame(table, df, self.contribution.data_model)

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


# ---------------------------------------------------------------------------
# Reading and writing table files
# ---------------------------------------------------------------------------
#
# The applications read a study with the functions below rather than with
# ``cb.Contribution(directory)``, for three reasons: contribution_builder
# rewrites measurements.txt in place when it has no ``measurement`` column
# (opening a study must never write to it); it lets pandas infer the type of
# the name columns (``001`` becomes 1, and one blank cell turns every name into
# a float); and it opens files in the locale's encoding, so a table saved by
# Excel on Windows either fails or reads differently on another computer.
# Tables are written back as UTF-8, whole-file-at-once (see atomic_write_text).

#: tried in order; the last never fails, and anything but UTF-8 is reported
TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
#: columns that hold names (or lists of names), which must be read as text
NAME_COLUMNS = ("measurement", "experiment", "specimen", "sample", "site", "location",
                "specimens", "samples", "sites", "locations", "experiments", "measurements",
                "table_column", "result_name")


class MagicReadError(ValueError):
    """A table file that cannot be read, with a sentence that says which and why."""


def decode_table_text(raw: bytes) -> tuple[str, str]:
    """``(text, encoding)`` for the bytes of a table file: UTF-8 when it is, else a Windows code page."""
    for encoding in TEXT_ENCODINGS:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise AssertionError("latin-1 decodes any byte")  # pragma: no cover


def read_table_file(path: str, expected: Optional[str] = None,
                    warnings: Optional[list] = None) -> tuple[Optional[str], Optional[pd.DataFrame]]:
    """Read one MagIC 3 table file without changing it: ``(table type, DataFrame)``.

    The name columns (:data:`NAME_COLUMNS`) are read as text, the file is
    decoded as UTF-8 or, failing that, as Windows-1252 (with a warning), and
    rows that are entirely blank are dropped. A file with only its header line
    reads as an empty table.

    Raises:
        MagicReadError: the file is not a MagIC 3 table (no ``tab <type>``
            first line, a MagIC 2.5 table, or a table of another type than
            ``expected``), or its body cannot be parsed.
    """
    import io
    name = os.path.basename(path)
    with open(path, "rb") as fh:
        raw = fh.read()
    text, encoding = decode_table_text(raw)
    if encoding != TEXT_ENCODINGS[0] and warnings is not None:
        warnings.append(f"{name} is not UTF-8; it was read as {'Windows-1252' if encoding == 'cp1252' else 'Latin-1'} "
                        "and will be written back as UTF-8")
    lines = text.splitlines()
    if not lines or not lines[0].strip():
        return expected, pd.DataFrame()
    first = [f.strip() for f in lines[0].split("\t")]
    if len(first) < 2 or not first[0].lower().startswith("tab"):
        raise MagicReadError(f"{name} is not a MagIC table: its first line should be 'tab' and the table name "
                             f"(it is {lines[0][:40]!r})")
    table = first[1]
    if table.startswith(("magic_", "er_", "pmag_", "rmag_")):
        raise MagicReadError(f"{name} is a MagIC 2.5 table ({table}); convert the directory to MagIC 3 first "
                             "(PmagPy's upgrade_magic.py, or the Convert page)")
    if expected and table != expected:
        raise MagicReadError(f"{name} holds a '{table}' table, not '{expected}'")
    if len(lines) < 2 or not lines[1].strip():
        return table, pd.DataFrame()
    header = lines[1].rstrip("\r").split("\t")
    dtypes = {c: str for c in header if c in NAME_COLUMNS}
    try:
        # round_trip: the fast parser can be a unit in the last place off, which turned every
        # rewritten table into a diff of thousands of lines
        df = pd.read_csv(io.StringIO(text), skiprows=1, sep="\t", dtype=dtypes, low_memory=False,
                         float_precision="round_trip")
    except (pd.errors.ParserError, ValueError) as exc:
        raise MagicReadError(f"{name} could not be read: {exc}") from exc
    df = df.dropna(how="all", axis=0)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed:")]]
    for col in dtypes:
        if col in df.columns:
            df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())
    return table, df


def _name_measurements(df: pd.DataFrame) -> pd.DataFrame:
    """Give an unnamed measurements table its ``sequence`` and ``measurement`` columns, in memory.

    contribution_builder does this too -- and then writes the file back; here
    it happens on the copy being read only.
    """
    df = df.copy()
    if "sequence" not in df.columns:
        df["sequence"] = range(1, len(df) + 1)
    if "measurement" in df.columns:
        return df
    if "number" in df.columns and "treat_step_num" not in df.columns:
        df = df.rename(columns={"number": "treat_step_num"})
    steps = df["treat_step_num"] if "treat_step_num" in df.columns else pd.Series(None, index=df.index)
    steps = steps.map(lambda v: "" if is_null(v) else (str(int(v)) if isinstance(v, float) and v.is_integer()
                                                        else str(v)))
    base = df["experiment"] if "experiment" in df.columns else df.get("specimen", pd.Series("", index=df.index))
    names = base.fillna("").astype(str) + steps
    # the name must say which row it is (the applications keep flags by it):
    # where experiment and step number do not, the row's sequence number does
    repeated = names.duplicated(keep=False) | (names == "")
    names = names.where(~repeated, names + "-" + df["sequence"].astype(str))
    df["measurement"] = names
    return df


def table_frame(table: str, df: pd.DataFrame, dmodel=None) -> "cb.MagicDataFrame":
    """A ``cb.MagicDataFrame`` for rows already read (contribution_builder's own post-processing)."""
    if table == "measurements":
        df = _name_measurements(df)
    df = df.where(df.notnull(), None)
    mdf = cb.MagicDataFrame(dtype=table, df=df, dmodel=dmodel)
    if table == "criteria" and "table_column" in mdf.df.columns:
        mdf.df.index = mdf.df["table_column"]
    return mdf


def read_contribution(directory: str, meas_file: str = "measurements.txt",
                      offline_data_model: bool = True,
                      tables: Iterable[str] = None,
                      warnings: Optional[list] = None) -> cb.Contribution:
    """Read a MagIC 3 directory into a ``cb.Contribution`` without writing anything.

    Each table is read by :func:`read_table_file`. A missing table is simply
    absent; a table that exists but cannot be read is left out with a warning,
    except the measurements table, whose problems are raised
    (:class:`MagicReadError`) because nothing can be done without it.
    """
    tables = list(tables) if tables is not None else \
        ["measurements", "specimens", "samples", "sites", "locations"]
    dmodel = data_model(offline_data_model)
    con = cb.Contribution(directory, custom_filenames={"measurements": meas_file},
                          read_tables=[], dmodel=dmodel)
    for table in tables:
        path = os.path.join(con.directory, con.filenames.get(table, table + ".txt"))
        if not os.path.isfile(path):
            continue
        try:
            _, df = read_table_file(path, expected=table, warnings=warnings)
        except (MagicReadError, OSError) as exc:
            if table == "measurements":
                raise MagicReadError(str(exc)) from exc
            if warnings is not None:
                warnings.append(f"{os.path.basename(path)} was not read: {exc}")
            continue
        name = table[:-1]
        if table == "measurements" and len(df) and "specimen" not in df.columns:
            raise MagicReadError(f"{os.path.basename(path)} has no 'specimen' column")
        if len(df) and table not in ("ages", "contribution", "images", "criteria", "measurements") \
                and name not in df.columns:
            if warnings is not None:
                warnings.append(f"{os.path.basename(path)} was not read: it has no '{name}' column")
            continue
        if table == "measurements" and len(df) == 0:
            raise MagicReadError(f"{os.path.basename(path)} holds no measurements")
        con.tables[table] = table_frame(table, df, dmodel)
    return con


def refresh_tables(contribution: cb.Contribution, output_dir: str,
                   tables=("specimens", "samples", "sites", "locations", "criteria"),
                   warnings: Optional[list] = None) -> list[str]:
    """Read the result tables again, as they are on disk now, before an export merges into them.

    An export keeps every row it does not own and replaces the ones it does
    -- so it must merge into the table as it is *now*, not as it was when the
    study was opened: with PmagPy Directions and PmagPy Intensity both open
    on one directory, each would otherwise write back its own stale copy and
    delete what the other had exported since. Each table is read from the
    output directory when that holds it, else from the source directory.

    Returns:
        the tables that were read again.
    """
    read = []
    for table in tables:
        name = contribution.filenames.get(table, table + ".txt")
        for directory in (output_dir, contribution.directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                break
        else:
            continue
        try:
            _, df = read_table_file(path, expected=table, warnings=warnings)
        except (MagicReadError, OSError) as exc:
            if warnings is not None:
                warnings.append(f"{name} could not be read again before the export ({exc}); "
                                "the copy read when the study was opened is merged into instead")
            continue
        contribution.tables[table] = table_frame(table, df, contribution.data_model)
        read.append(table)
    return read


def atomic_write_text(path: str, text: str, encoding: str = "utf-8") -> str:
    """Write ``text`` to ``path`` all at once: a crash leaves the old file or the new one, never half of one.

    The text goes to a temporary file beside the target, which then replaces
    it (``os.replace`` is atomic on one file system). UTF-8, ``\\n`` line
    endings, whatever the computer's locale.
    """
    import tempfile
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        if os.path.exists(path):
            try:
                shutil.copymode(path, tmp)
            except OSError:
                pass
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


class StagedExport:
    """Write a set of files into a directory all or nothing, keeping what they replace.

    Everything is first written to a staging folder inside ``output_dir``;
    only when every file has been written are they moved into place, each
    replacing its target in one step. An exception on the way leaves the
    output directory exactly as it was. Every file that is replaced is first
    copied to ``<backup>/previous/`` (so the last export can be undone), and,
    when ``originals`` is true, to ``<backup>/`` the first time it is
    replaced (so the contribution as it was before the application first
    wrote to it can always be recovered)::

        with StagedExport(output_dir, backup) as stage:
            data.write_specimens(stage.dir)          # writers write into stage.dir
        stage.written                                # the final paths
    """

    def __init__(self, output_dir: str, backup: Optional[str] = None, originals=False):
        self.output_dir = os.path.abspath(output_dir)
        self.backup = backup
        # True, or the names of the files the study had when it was opened: a file an
        # application created itself is not an original, however often it is replaced
        self.originals = originals
        self.dir = ""
        self.written: list[str] = []
        self.backed_up: list[str] = []

    def __enter__(self) -> "StagedExport":
        import tempfile
        os.makedirs(self.output_dir, exist_ok=True)
        self.dir = tempfile.mkdtemp(prefix=".staging-", dir=self.output_dir)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            if exc_type is None:
                self._commit()
        finally:
            shutil.rmtree(self.dir, ignore_errors=True)
        return False

    def _commit(self) -> None:
        # in the order they were written (the callers list the first table first)
        names = sorted((n for n in os.listdir(self.dir) if not n.startswith(".")),
                       key=lambda n: (os.stat(os.path.join(self.dir, n)).st_mtime_ns, n))
        if self.backup:
            previous = os.path.join(self.backup, "previous")
            for name in names:
                target = os.path.join(self.output_dir, name)
                if not os.path.isfile(target):
                    continue
                is_original = name in self.originals if isinstance(self.originals, (set, frozenset, list, tuple)) \
                    else bool(self.originals)
                if is_original and not os.path.exists(os.path.join(self.backup, name)):
                    os.makedirs(self.backup, exist_ok=True)
                    shutil.copy2(target, os.path.join(self.backup, name))
                    self.backed_up.append(os.path.join(self.backup, name))
                os.makedirs(previous, exist_ok=True)
                shutil.copy2(target, os.path.join(previous, name))
        for name in names:
            target = os.path.join(self.output_dir, name)
            os.replace(os.path.join(self.dir, name), target)
            self.written.append(target)


#: tables a complete MagIC directory carries that an application does not write itself
COMPANION_TABLES = ("contribution.txt", "ages.txt", "criteria.txt", "images.txt",
                    "specimens.txt", "samples.txt", "sites.txt", "locations.txt", "measurements.txt")


def copy_companion_tables(source_dir: str, output_dir: str, skip: Iterable[str] = ()) -> list[str]:
    """Copy the source's other tables into a separate output directory so that it is a complete contribution.

    Only tables the export did not write (``skip``) and that the output
    directory does not hold in a newer copy are copied. Nothing happens when
    the output directory is the source directory.
    """
    if os.path.realpath(source_dir) == os.path.realpath(output_dir):
        return []
    skip = {os.path.basename(s) for s in skip}
    copied = []
    for name in COMPANION_TABLES:
        src, dst = os.path.join(source_dir, name), os.path.join(output_dir, name)
        if name in skip or not os.path.isfile(src):
            continue
        if os.path.isfile(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            continue
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def write_measurement_flags(source_path: str, target_path: str, changes: dict,
                            names: Optional[Iterable[str]] = None) -> Optional[str]:
    """Write a measurements table with some ``quality`` flags changed and nothing else.

    The table is rewritten from its own text -- column order, number formats,
    blank cells and all -- so an export that changed three flags is a diff of
    three lines, however large the table (a round trip through pandas
    reformatted every number). Rows are counted as :func:`read_table_file`
    counts them, so the positions are the ``meas_pos`` of the step tables.

    Args:
        source_path: the table to start from: the study's own file, or, when
            the export goes back into the study, the file as it is on disk now
            (so flags another application wrote since are kept).
        target_path: where to write.
        changes: ``{row position: 'g' or 'b'}``, the flags the analyst changed.
        names: the measurement names, one per row, added as a ``measurement``
            column when the file has none (MagIC requires it).

    Returns:
        the path written, or None when the file's rows are not the rows the
        positions refer to (the caller then writes the table in full).
    """
    with open(source_path, "rb") as fh:
        text, _ = decode_table_text(fh.read())
    lines = text.splitlines()
    if len(lines) < 2 or not lines[0].lower().startswith("tab"):
        return None
    header = lines[1].rstrip("\r").split("\t")
    kept = [i for i, line in enumerate(lines[2:], start=2) if any(f.strip() for f in line.split("\t"))]
    names = list(names) if names is not None else None
    if names is not None and len(names) != len(kept):
        return None
    if changes and max(changes) >= len(kept):
        return None
    add_names = "measurement" not in header and names is not None
    add_quality = "quality" not in header
    new_header = header + (["measurement"] if add_names else []) + (["quality"] if add_quality else [])
    q_col = new_header.index("quality")
    out = [lines[0], "\t".join(new_header)]
    position = {line_no: k for k, line_no in enumerate(kept)}
    for line_no, line in enumerate(lines[2:], start=2):
        k = position.get(line_no)
        if k is None:
            out.append(line)
            continue
        fields = line.rstrip("\r").split("\t")
        fields += [""] * (len(header) - len(fields))
        if add_names:
            fields.append(str(names[k]))
        if add_quality:
            fields.append("g")
        if k in changes:
            fields[q_col] = changes[k]
        out.append("\t".join(fields))
    return atomic_write_text(target_path, "\n".join(out) + "\n")


def flag_changes(table_df: pd.DataFrame, steps_by_specimen) -> dict:
    """``{row position: flag}`` where a step's flag differs from the measurements table as it was read."""
    loaded = table_df["quality"].to_numpy(dtype=object) if "quality" in table_df.columns else None
    changes = {}
    for steps in steps_by_specimen:
        for pos, quality in zip(steps["meas_pos"].to_numpy(), steps["quality"].to_numpy(dtype=object)):
            was = "g"
            if loaded is not None and not is_null(loaded[pos]) and str(loaded[pos]).strip() == "b":
                was = "b"
            now = "b" if quality == "b" else "g"
            if now != was:
                changes[int(pos)] = now
    return changes


def magic_table_text(df: pd.DataFrame, table: str) -> str:
    """A DataFrame as the text of a MagIC 3 table file (columns in data-model order)."""
    if table == "measurements" and "measurement" not in df.columns:
        df = _name_measurements(df)
    mdf = cb.MagicDataFrame(dtype=table, df=df.copy())
    mdf.sort_dataframe_cols()
    out = mdf.df
    name = table[:-1]
    out = out.drop(columns=[c for c in ("num", name + "_name") if c in out.columns])
    if name in out.columns:
        out[name] = out[name].astype(str)
    out = _integers_as_integers(out, table)
    return f"tab\t{table}\n" + out.to_csv(sep="\t", index=False, lineterminator="\n")


def _integers_as_integers(df: pd.DataFrame, table: str) -> pd.DataFrame:
    """Write the data model's Integer columns as 11, not 11.0 (a column with a blank cell is float in pandas)."""
    try:
        types = data_model(True).dm[table]["type"]
    except (KeyError, AttributeError):
        return df
    for col in df.columns:
        if types.get(col) != "Integer" or pd.api.types.is_integer_dtype(df[col]):
            continue
        numbers = pd.to_numeric(df[col], errors="coerce")
        present = df[col].notna() & (df[col].astype(str).str.strip() != "")
        if present.any() and numbers[present].notna().all() and (numbers[present] % 1 == 0).all():
            df = df.copy() if df is not None else df
            df[col] = numbers.astype("Int64")
    return df


def magic_write(path: str, df: pd.DataFrame, table: str) -> str:
    """Write a MagIC 3 tab-delimited table (UTF-8, atomically)."""
    return atomic_write_text(path, magic_table_text(df, table))


def table_rows(path: str) -> int:
    """The number of rows in a MagIC 3 table file (lines after the two header lines); 0 when the file is absent."""
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        return max(0, sum(1 for line in fh if line.strip()) - 2)


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
