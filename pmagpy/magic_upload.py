"""
Getting a MagIC directory ready to upload, without any UI.

What Pmag GUI's box 3 and Export menu did: check every table with PmagPy's
offline validator, build the single upload file that MagIC takes
(``ipmag.upload_magic``), send it to MagIC's public validation endpoint, and
write the publication tables (``ipmag.sites_extract`` and friends). The hub's
Upload page calls these; so can a notebook.

Every EarthRef call stays in :mod:`pmagpy.ipmag`, so the HTTP client can be
swapped in one place.
"""
from __future__ import annotations

import contextlib
import io
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pmagpy import magic_metadata as mm

#: the tables an upload carries, in the order upload_magic writes them (contribution.txt is never uploaded)
UPLOAD_TABLES = ("locations", "sites", "samples", "specimens", "ages", "measurements", "criteria", "images")

#: the tables the offline validator knows how to check
CHECKED_TABLES = ("locations", "sites", "samples", "specimens", "ages", "measurements", "criteria", "images")

UPLOAD_MARKER = ">>>>>>>>>>"


def present_tables(directory: str) -> List[str]:
    """The upload tables that exist in ``directory``, in upload order."""
    return [t for t in UPLOAD_TABLES if os.path.isfile(os.path.join(directory, t + ".txt"))]


# ---------------------------------------------------------------------------
# Offline check
# ---------------------------------------------------------------------------
def check_offline(directory: str) -> Dict[str, List[mm.Finding]]:
    """PmagPy's validator over every table present: table -> findings (an empty list is a pass)."""
    with contextlib.redirect_stdout(io.StringIO()):          # the validator narrates; the findings are the report
        return {t: mm.check_table(directory, t) for t in present_tables(directory) if t in CHECKED_TABLES}


# ---------------------------------------------------------------------------
# The upload file
# ---------------------------------------------------------------------------
@dataclass
class UploadFile:
    """The single file MagIC takes: every table, separated by ``>>>>>>>>>>``."""
    path: str
    tables: List[str]
    log: str = ""

    @property
    def name(self) -> str:
        return os.path.basename(self.path)

    @property
    def size(self) -> int:
        return os.path.getsize(self.path) if os.path.isfile(self.path) else 0


def is_upload_file(path: str) -> bool:
    """A MagIC contribution/upload file: starts with a ``tab`` header and carries the table separator."""
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as fh:
            head = fh.read(4096)
            if not head.startswith("tab"):
                return False
            if UPLOAD_MARKER in head:
                return True
            # a long first table pushes the separator past the first block
            for line in fh:
                if line.startswith(UPLOAD_MARKER):
                    return True
    except OSError:
        return False
    return False


def upload_files(directory: str) -> List[str]:
    """Names of the upload files already in ``directory``, newest first."""
    names = []
    for n in os.listdir(directory):
        stem, ext = os.path.splitext(n)
        path = os.path.join(directory, n)
        if ext == ".txt" and stem not in UPLOAD_TABLES and stem != "contribution" and os.path.isfile(path) \
                and is_upload_file(path):
            names.append(n)
    return sorted(names, key=lambda n: -os.path.getmtime(os.path.join(directory, n)))


def build_upload_file(directory: str) -> UploadFile:
    """Compile the tables into one upload file in ``directory`` (named ``<locations>_<date>.txt``).

    ``upload_magic`` drops the columns MagIC does not take, folds degrees into
    0-360 and writes each table after the last; nothing on disk but the new
    file changes. Raises ``ValueError`` when there is nothing to upload.
    """
    from pmagpy import ipmag
    tables = present_tables(directory)
    if not tables:
        raise ValueError("no MagIC tables to upload")
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        path, note, _, _ = ipmag.upload_magic(dir_path=directory, input_dir_path=directory,
                                              validate=False, verbose=False)
    if not path:
        raise ValueError(str(note))
    return UploadFile(path=path, tables=tables, log=out.getvalue())


# ---------------------------------------------------------------------------
# MagIC's public validation endpoint
# ---------------------------------------------------------------------------
@dataclass
class Issue:
    """One thing MagIC's validator said about the file."""
    table: str
    column: str
    message: str
    rows: List[int] = field(default_factory=list)      # 1-based row numbers in that table


@dataclass
class OnlineReport:
    """What the public endpoint returned, or why it could not be asked."""
    reached: bool                       # MagIC answered
    errors: List[Issue] = field(default_factory=list)
    warnings: List[Issue] = field(default_factory=list)
    trouble: str = ""                   # when not reached

    @property
    def ok(self) -> bool:
        return self.reached and not self.errors

    def by_table(self) -> Dict[str, List[Issue]]:
        out: Dict[str, List[Issue]] = {}
        for issue in self.errors:
            out.setdefault(issue.table, []).append(issue)
        return out


def _issues(items) -> List[Issue]:
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(Issue(table=str(item.get("table", "")), column=str(item.get("column", "")),
                             message=str(item.get("message", "")),
                             rows=[int(r) for r in item.get("rows", []) or [] if str(r).isdigit()]))
        else:
            out.append(Issue(table="", column="", message=str(item)))
    return out


def validate_online(path: str) -> OnlineReport:
    """Send an upload file to MagIC's public validator (``ipmag.validate_with_public_endpoint``)."""
    from pmagpy import ipmag
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            response = ipmag.validate_with_public_endpoint(path, verbose=False)
    except Exception as ex:                                   # requests raises its own family; the page only needs the words
        return OnlineReport(reached=False, trouble=f"could not reach MagIC: {ex}")
    if not response.get("status"):
        return OnlineReport(reached=False, trouble=str(response.get("warnings") or "MagIC did not validate the file"))
    validation = response.get("validation") or {}
    if not isinstance(validation, dict):
        validation = {}
    return OnlineReport(reached=True, errors=_issues(validation.get("errors")),
                        warnings=_issues(validation.get("warnings")))


# ---------------------------------------------------------------------------
# Publication tables
# ---------------------------------------------------------------------------
@dataclass
class ExportResult:
    files: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)      # tables with nothing to export
    log: str = ""


EXPORT_DIR = "publication_tables"


def export_tables(directory: str, out_dir: Optional[str] = None, latex: bool = False) -> ExportResult:
    """Write the site, specimen and criteria publication tables (``ipmag.*_extract``).

    Excel (``.xlsx``; tab-delimited ``.tsv`` when openpyxl is not installed) or
    LaTeX, into ``directory/publication_tables/`` unless ``out_dir`` says
    otherwise (``specimens.tex`` beside ``specimens.txt`` is asking for a
    slip). Only the tables present are exported; the result lists the files.
    """
    from pmagpy import ipmag
    out_dir = out_dir or os.path.join(directory, EXPORT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    result = ExportResult()
    log = io.StringIO()
    jobs = [("sites", lambda: ipmag.sites_extract(input_dir_path=directory, output_dir_path=out_dir, latex=latex)),
            ("specimens", lambda: ipmag.specimens_extract(input_dir_path=directory, output_dir_path=out_dir,
                                                          latex=latex, longtable=True)),
            ("criteria", lambda: ipmag.criteria_extract(input_dir_path=directory, output_dir_path=out_dir, latex=latex))]
    with contextlib.redirect_stdout(log):
        for table, job in jobs:
            if not os.path.isfile(os.path.join(directory, table + ".txt")):
                continue
            ok, files = job()
            if ok and files:
                result.files.extend(files)
            else:
                result.skipped.append(table)
    result.log = log.getvalue()
    return result
