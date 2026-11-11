"""
Validate a MagIC contribution with the rules that MagIC applies.

This module ports the parser and the validator of the MagIC website, so that a
contribution that passes here passes the validation run on MagIC:

    https://github.com/earthref/MagIC
        lib/modules/magic/parse_contribution.js      reading a MagIC text file
        lib/modules/magic/validate_contribution.js   the validation
    (ported from commit 6b6f229, 2026-11-10: MAGIC_PORTED_COMMIT; the weekly
    workflow .github/workflows/magic-rules-sync.yml opens an issue when MagIC
    changes these files)

MagIC validates in two places: the website (the code above, which validates a
private contribution) and the EarthRef API (api.earthref.org/v1/MagIC/validate,
used by ipmag.upload_magic). Compared on the same files (2026-11-10 and
2026-11-11), they report the same problems on the same rows, except that the
API ignores case in controlled vocabularies, accepts a Timestamp only as ISO
8601 with "T" before the time, and words a missing required value "is missing
required column" where the website says "is missing data in required column".
Where they differ this module follows the API for vocabularies (case is
ignored) and the stricter rule for timestamps (ISO 8601 with "T"), and uses
the website's wording.

The rules come from the MagIC data model, the method codes and the controlled
vocabularies. load_rules() reads them from EarthRef and from the MagIC source
on GitHub and falls back to the copies in pmagpy/data_model, which
update_cache() refreshes.

The checks, as on MagIC (validate_contribution.js):
    - the locations and sites tables are present
    - required(), requiredIf(), requiredIfGroup(), requiredOneInGroup(),
      requiredUnless() and requiredUnlessTable()
    - the type of every value: Integer, Number and Timestamp
    - method codes in columns with type("method_codes")
    - controlled vocabularies (cv), ignoring case as the API does (the website
      code compares exactly)
    - min() and max() with a number
    - in("table.column"): references between tables
Rules of the data model that MagIC does not check are not checked here either
(e.g. requiredUnlessSynthetic(), unique(), suggested vocabularies).

Where this module differs from MagIC, it reports more:
    - every row of the measurements table is checked (MagIC checks the first
      10000), and a measurements row with fewer values than columns is checked
      for its empty required values
    - a column that is not in the data model is reported as a warning (on MagIC
      the upload tool asks for it to be matched to a data model column or left
      out), and in the measurements table as an error, since the API then
      fails with an HTTP 500 error instead of validating
    - data in a column without a name is reported as a warning (MagIC leaves it
      out without saying so)
    - a table that is not in the data model is reported as an error
    - a measurements table given more than once is reported as an error (MagIC
      keeps only the last one and drops the rows before it)
    - after a malformed table the rest of the file is still read (MagIC stops)
MagIC's controlled-vocabulary check of Matrix and Dictionary columns never
reports a value (the comparison in validate_contribution.js always succeeds),
so those values are not checked here either.

Typical use:
    from pmagpy import magic_validation
    problems = magic_validation.validate('upload_file.txt')
    magic_validation.print_problems(problems)
"""
import contextlib
import io
import json
import os
import re
import shutil
import tempfile

import pandas as pd

try:
    import requests
except ImportError:
    requests = None

from pmag_env import set_env

DATA_MODEL_URL = "https://earthref.org/MagIC/data-models/3.0.json"
METHOD_CODES_URL = "https://www2.earthref.org/MagIC/method-codes.json"
MAGIC_SOURCE_URL = "https://raw.githubusercontent.com/earthref/MagIC/main/"
# the commit of earthref/MagIC this module's parser and validator are ported from
MAGIC_PORTED_COMMIT = "6b6f229cc0f947a1deefe751620706270730231a"
MAGIC_VALIDATOR_FILES = ("lib/modules/magic/parse_contribution.js", "lib/modules/magic/validate_contribution.js")
# where each resource is downloaded from, how it is read, and its cached file
RESOURCES = {
    "data_model": (DATA_MODEL_URL, "json", "data_model.json"),
    "method_codes": (METHOD_CODES_URL, "json", "method_codes.json"),
    # the vocabularies are read from the MagIC source, which the MagIC website
    # validates with (EarthRef no longer serves them as JSON)
    "vocabularies": (MAGIC_SOURCE_URL + "lib/modules/er/controlled_vocabularies.js", "js",
                     "controlled_vocabularies.json"),
    "suggested_vocabularies": (MAGIC_SOURCE_URL + "lib/modules/er/suggested_vocabularies.js", "js",
                               "suggested_vocabularies.json"),
}

MEASUREMENTS = "measurements"
_RESOURCES = {}  # (name, "online" or "cache") -> data
_FAILED = set()  # resources whose download failed
_RULES = {}


# ---------------------------------------------------------------- the rules

def cache_dir():
    """The directory of the cached data model, method codes and vocabularies."""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_model")
    if os.path.isdir(here):
        return here
    # otherwise (e.g. a frozen build) look where find_pmag_dir puts PmagPy's files
    from . import find_pmag_dir
    pmag_dir = find_pmag_dir.get_pmag_dir()
    for path in (os.path.join(pmag_dir, "pmagpy", "data_model"), os.path.join(pmag_dir, "data_model")):
        if os.path.isdir(path):
            return path
    return here


_CLOSING = re.compile(r"\s*[}\]]")


def _read_js_object(text):
    """
    Read a JavaScript data file of the form `export const x = {...};` as a dict.

    The text is parsed as data (comments and trailing commas removed); no code
    is run.
    """
    out, i, n, quote = [], 0, len(text), ""
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == quote:
                quote = ""
            i += 1
        elif c in "\"'":
            quote = c
            out.append(c)
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end < 0 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i)
            i = n if end < 0 else end + 2
        else:
            out.append(c)
            i += 1
    body = "".join(out)
    body = body[body.index("{"):body.rindex("}") + 1]
    # drop trailing commas, outside strings only
    out, quote, i = [], "", 0
    while i < len(body):
        c = body[i]
        if quote:
            out.append(c)
            if c == "\\" and i + 1 < len(body):
                out.append(body[i + 1])
                i += 1
            elif c == quote:
                quote = ""
        elif c in "\"'":
            quote = c
            out.append(c)
        elif not (c == "," and _CLOSING.match(body, i + 1)):
            out.append(c)
        i += 1
    return json.loads("".join(out), strict=False)


def download_resource(name, timeout=10):
    """
    Download one of the RESOURCES (data_model, method_codes, vocabularies,
    suggested_vocabularies), in the format of its cached file.
    """
    if requests is None:
        raise ImportError("downloading the MagIC rules needs the requests package")
    url, kind, _ = RESOURCES[name]
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json() if kind == "json" else _read_js_object(response.text)


def read_cached_resource(name, directory=None):
    """One of the RESOURCES from its cached file in pmagpy/data_model."""
    with open(os.path.join(directory or cache_dir(), RESOURCES[name][2]), encoding="utf-8-sig") as f:
        return json.load(f)


def get_resource(name, online=None, timeout=10):
    """
    One of the RESOURCES, downloaded or from the cache.

    Parameters
    ----------
    name : str
        data_model, method_codes, vocabularies or suggested_vocabularies
    online : bool or None
        True to download it, False to use the cached copy; None (default)
        downloads it unless PmagPy is set to work offline, and uses the cached
        copy if the download fails (and from then on)

    Returns
    -------
    (data, source): source is "online" or "cache"
    """
    fall_back = online is None
    if online is None:
        # a download that failed is not tried again when falling back is allowed
        online = not set_env.OFFLINE and name not in _FAILED
    if online and (name, "online") not in _RESOURCES:
        try:
            _RESOURCES[(name, "online")] = download_resource(name, timeout)
        except Exception as ex:
            if not fall_back:
                raise
            _FAILED.add(name)
            print("-W- Could not download the MagIC {} ({}); using the cached copy".format(
                name.replace("_", " "), ex))
    if online and (name, "online") in _RESOURCES:
        return _RESOURCES[(name, "online")], "online"
    if (name, "cache") not in _RESOURCES:
        _RESOURCES[(name, "cache")] = read_cached_resource(name)
    return _RESOURCES[(name, "cache")], "cache"


def update_cache(directory=None, timeout=30):
    """
    Download the MagIC data model, method codes and vocabularies and write them
    to the cached files in pmagpy/data_model (or directory). Nothing is written
    unless every download succeeds. A DataModel or Vocabulary already loaded in
    this Python session keeps the old copies; they are read again in a new one.

    Returns
    -------
    dict of the files written
    """
    directory = directory or cache_dir()
    downloaded = {name: download_resource(name, timeout) for name in RESOURCES}
    written = {}
    for name, (_, _, filename) in RESOURCES.items():
        data = downloaded[name]
        path = os.path.join(directory, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)
            f.write("\n")
        written[name] = path
    _RESOURCES.clear()
    _FAILED.clear()
    _RULES.clear()
    return written


def load_rules(online=None, timeout=10):
    """
    The rules that validate() applies.

    Parameters
    ----------
    online : bool or None
        as for get_resource

    Returns
    -------
    dict with
        tables: the tables of the data model (columns with type, group and validations)
        vocabularies: vocabulary name -> dict(label, items: set of items)
        method_codes: set of method codes
        source: "online", "cache" or "online and cache"
        updated_day: date of the data model
    """
    loaded = {name: get_resource(name, online, timeout) for name in ("data_model", "method_codes", "vocabularies")}
    key = tuple(source for _, source in loaded.values())
    if key in _RULES:
        return _RULES[key]
    sources = sorted(set(key))
    data_model, method_codes, vocabularies = (loaded[n][0] for n in ("data_model", "method_codes", "vocabularies"))
    rules = {"tables": data_model["tables"],
             "updated_day": data_model.get("updated_day", ""),
             "vocabularies": {name: {"label": v.get("label", name), "items": {i["item"] for i in v["items"]},
                                     "lower": {str(i["item"]).lower() for i in v["items"]}}
                              for name, v in vocabularies.items()},
             "method_codes": {c["code"] for codes in method_codes.values() for c in codes["codes"]},
             "source": " and ".join(sources)}
    _RULES[key] = rules
    return rules


# ---------------------------------------------------------------- reading a contribution

# the characters JavaScript's trim() removes (Python's strip() keeps U+FEFF and
# removes U+001C to U+001F, which trim() keeps)
_JS_SPACE = ("\t\n\v\f\r              "
             "    　﻿")


def _trim(text):
    return text.strip(_JS_SPACE)


class _Table(object):
    """A table as MagIC reads it: column names and rows of trimmed text values."""

    def __init__(self, columns, rows=None):
        self.columns = list(columns)
        self.rows = rows if rows is not None else []


def parse_magic_text(text):
    """
    Read the text of a MagIC file as MagIC's parse_contribution.js does.

    Parameters
    ----------
    text : str
        tables separated by lines of ">", each starting with a line
        "tab<tab>name" (or "tab delimited<tab>name") and a line of column names

    Returns
    -------
    (tables, errors): tables maps a table name to a _Table; errors is a list of
    (table, message). Line numbers in the messages are those of the file.

    As on MagIC, a column without a name is allowed (e.g. after a trailing tab);
    validate() reports data in it. A table whose column names cannot be read is
    kept with no rows, as MagIC keeps it. A table given twice is read as MagIC
    reads it: the rows of both are kept, except for the measurements table,
    whose last block replaces the earlier ones (reported as an error, since
    MagIC drops those rows).
    """
    tables, errors = {}, []
    table, columns, positions, table_line, skip = None, [], [], 0, False
    for number, line in enumerate(re.split(r"\r\n|[\n\v\f\r\x85\u2028\u2029]", text), start=1):
        if _trim(line) == "":
            continue
        if re.match(r"^>+$", _trim(line)):
            table, columns, positions, table_line, skip = None, [], [], 0, False
            continue
        if skip:
            continue
        table_line += 1
        if table_line == 1:
            definition = [_trim(x) for x in line.split("\t")]
            if len(definition) < 2 or not re.match(r"^tab( delimited)?(\s|$)", definition[0], re.I):
                errors.append(("", 'Invalid table definition on line {}. Expected something like '
                                   '"tab[tab]measurements".'.format(number)))
                skip = True
            elif definition[1] == "":
                errors.append(("", "No table name following tab delimiter on line {}.".format(number)))
                skip = True
            else:
                table = definition[1].lower()
                tables.setdefault(table, None)
        elif table_line == 2:
            columns = [_trim(x).lower() for x in line.split("\t")]
            if len(columns) != len(set(columns)):
                errors.append((table, "Found duplicate column names on line {}.".format(number)))
                skip = True
                continue
            existing = tables[table]
            if existing is not None and table == MEASUREMENTS:
                errors.append((table, "The measurements table is given again on line {}; MagIC keeps only "
                                      "the last measurements table and drops the rows before it."
                               .format(number)))
            if existing is None or table == MEASUREMENTS:
                tables[table] = _Table(columns)
            else:
                existing.columns += [c for c in columns if c not in existing.columns]
                for row in existing.rows:
                    row.extend([""] * (len(existing.columns) - len(row)))
            positions = [tables[table].columns.index(c) for c in columns]
        else:
            values = [_trim(x) for x in line.split("\t")]
            if len(values) > len(columns):
                errors.append((table, "More values found than columns on line {}.".format(number)))
                skip = True
                continue
            row = [""] * len(tables[table].columns)
            for position, value in zip(positions, values):
                row[position] = value
            tables[table].rows.append(row)
    return {name: t if t is not None else _Table([]) for name, t in tables.items()}, errors


def _cell_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return _trim(str(value))


def _from_dataframe(df):
    columns = [_trim(str(c)).lower() for c in df.columns]
    rows = [[_cell_text(v) for v in row] for row in df.itertuples(index=False, name=None)]
    return _Table(columns, rows)


# the tables ipmag.upload_magic puts in an upload file, from <table>.txt
UPLOAD_TABLES = ("locations", "samples", "specimens", "sites", "ages", "measurements", "criteria", "images")


def _read_table_files(directory):
    """The tables in a directory's <table>.txt files, read as they are."""
    tables, errors = {}, []
    for name in UPLOAD_TABLES:
        path = os.path.join(directory, name + ".txt")
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            parsed, parse_errors = parse_magic_text(f.read())
        tables.update(parsed)
        errors += [(table or name, "{}.txt: {}".format(name, message)) for table, message in parse_errors]
    return tables, errors


def _read_upload_file(directory):
    """
    The tables of the upload file that ipmag.upload_magic makes from the table
    files in a directory: what would be sent to MagIC, after upload_magic's
    clean-up and without contribution.txt.

    The table files are read first. If one cannot be read as MagIC would read
    it, or upload_magic fails, the problems are reported with the tables as
    they are in the files.
    """
    tables, errors = _read_table_files(directory)
    if not tables and not errors:
        return {}, [("", "No MagIC table files to upload were found in {}.".format(directory))]
    if errors:
        return tables, errors
    from . import ipmag  # ipmag imports contribution_builder, which imports this module
    tmp = tempfile.mkdtemp(prefix="magic-validation-")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            upload = ipmag.upload_magic(dir_path=tmp, input_dir_path=directory, validate=False, verbose=False)[0]
        if not upload:
            raise ValueError("no upload file was made")
        with open(upload, encoding="utf-8-sig", errors="replace") as f:
            return parse_magic_text(f.read())
    except Exception as ex:
        return tables, [("", "ipmag.upload_magic could not make an upload file ({}: {}); the table files "
                             "are checked as they are.".format(type(ex).__name__, ex), "warning")]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read_contribution(contribution):
    """
    The tables of a contribution, read as MagIC reads them.

    Parameters
    ----------
    contribution : str, dict or contribution_builder.Contribution
        a MagIC text file (e.g. written by ipmag.upload_magic); a directory
        holding table files named after their table (sites.txt, ...); a dict
        of table name to DataFrame; or a Contribution. A directory or a
        Contribution is read as the file ipmag.upload_magic would make from
        it; a dict is read as given.

    Returns
    -------
    (tables, errors) as from parse_magic_text
    """
    if isinstance(contribution, os.PathLike):
        contribution = os.fspath(contribution)
    if isinstance(contribution, str) and os.path.isdir(contribution):
        return _read_upload_file(contribution)
    if isinstance(contribution, str):
        with open(contribution, encoding="utf-8-sig", errors="replace") as f:
            return parse_magic_text(f.read())
    if hasattr(contribution, "tables") and not isinstance(contribution, dict):
        # written here rather than with write_magic_file, which writes to the
        # table's own file and reorders its columns
        tmp = tempfile.mkdtemp(prefix="magic-validation-")
        try:
            for name, table in contribution.tables.items():
                # working columns that write_magic_file leaves out
                working = ["num"]
                if hasattr(table, "get_singular_and_plural_dtype"):
                    working.append(table.get_singular_and_plural_dtype(name)[0] + "_name")
                with open(os.path.join(tmp, name + ".txt"), "w", encoding="utf-8") as f:
                    f.write("tab\t{}\n".format(name))
                    table.df.drop(columns=working, errors="ignore").to_csv(f, sep="\t", index=False)
            return _read_upload_file(tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    tables = {}
    for name, df in contribution.items():
        name = name.lower()
        if name.endswith(".txt"):
            name = name[:-4]
        tables[name] = _from_dataframe(df.reset_index(drop=True))
    return tables, []


# ---------------------------------------------------------------- value tests

INTEGER = re.compile(r"^[+-]?[0-9]+$")
NUMBER = re.compile(r"^[+-]?([0-9]*\.?[0-9]+|[0-9]+\.)(e[+-]?[0-9]*\.?[0-9]+)?$", re.I)
_FLOAT_PREFIX = re.compile(r"^\s*([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?|[+-]?Infinity)")
# ISO 8601 dates and times as both MagIC validators accept them: the ISO forms
# of moment.js (the MagIC website; its extendedIsoRegex and basicIsoRegex),
# with "T" between date and time, which the EarthRef API requires (it rejects
# "2013-02-08 09:30"). An extended date takes an extended time (09:30), a basic
# date a basic time (0930).
_ISO_ZONE = r"(?:[+-][0-9]{2}(?::?[0-9]{2})?|\s*Z)?"
_ISO_EXTENDED = re.compile(r"^(?P<year>[+-][0-9]{6}|[0-9]{4})-(?P<rest>[0-9]{2}-[0-9]{2}|W[0-9]{2}-[0-9]|W[0-9]{2}"
                           r"|[0-9]{3}|[0-9]{2})(?:T(?P<time>[0-9]{2}(?::[0-9]{2}(?::[0-9]{2}(?:[.,][0-9]+)?)?)?)"
                           + _ISO_ZONE + r")?$")
_ISO_BASIC = re.compile(r"^(?P<year>[+-][0-9]{6}|[0-9]{4})(?P<rest>[0-9]{4}|W[0-9]{3}|W[0-9]{2}|[0-9]{3}|[0-9]{2}|)"
                        r"(?:T(?P<time>[0-9]{2}(?:[0-9]{2}(?:[0-9]{2}(?:[.,][0-9]+)?)?)?)" + _ISO_ZONE + r")?$")


def parse_float(value):
    """JavaScript parseFloat: the number at the start of the text, or NaN."""
    match = _FLOAT_PREFIX.match(str(value))
    if not match:
        return float("nan")
    return float(match.group(1).replace("Infinity", "inf"))


def _is_leap(year):
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def _iso_weeks(year):
    """The number of ISO weeks in a year (52 or 53)."""
    def p(y):
        return (y + y // 4 - y // 100 + y // 400) % 7
    return 53 if p(year) == 4 or p(year - 1) == 3 else 52


def is_timestamp(value):
    """
    True if both MagIC validators accept the text as a Timestamp: a valid
    ISO 8601 date, optionally with a time after "T" and a time zone
    (e.g. 2013-02-08, 20130208, 2013-W06-5, 2013-039,
    2013-02-08T09:30:26.123+07:00), with moment.js's ranges: months 1-12, days
    in the month, ordinal days in the year, ISO weeks in the year, weekdays 1-7,
    hours 0-24 (24 only as 24:00:00), minutes and seconds 0-59. A year alone,
    a year and month, or a year and week takes no time.

    The MagIC website (moment.js) also accepts a space before the time; the
    EarthRef API (api.earthref.org, used by ipmag.upload_magic) does not, and
    neither does this check.
    """
    value = _trim(value)
    match = _ISO_EXTENDED.match(value)
    if not match:
        match = _ISO_BASIC.match(value)
        # moment reads a signed six-digit year in the basic form only in a full date
        if match and match.group("year")[0] in "+-" and len(match.group("rest")) != 4:
            return False
    if not match:
        return False
    year, rest, time = int(match.group("year")), match.group("rest").replace("-", ""), match.group("time")
    if rest.startswith("W"):
        week, weekday = int(rest[1:3]), rest[3:]
        if not 1 <= week <= _iso_weeks(year) or (weekday and not 1 <= int(weekday) <= 7):
            return False
        takes_time = bool(weekday)
    elif len(rest) == 4:
        month, day = int(rest[:2]), int(rest[2:])
        days = [31, 29 if _is_leap(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if not 1 <= month <= 12 or not 1 <= day <= days[month - 1]:
            return False
        takes_time = True
    elif len(rest) == 3:
        if not 1 <= int(rest) <= (366 if _is_leap(year) else 365):
            return False
        takes_time = True
    elif len(rest) == 2:
        if not 1 <= int(rest) <= 12:
            return False
        takes_time = False
    else:
        takes_time = False
    if time is None:
        return True
    if not takes_time:
        return False
    digits, _, fraction = time.replace(":", "").replace(",", ".").partition(".")
    hour, minute, second = int(digits[:2]), int(digits[2:4] or 0), int(digits[4:6] or 0)
    if hour == 24:
        return minute == 0 and second == 0 and not fraction.strip("0")
    return hour <= 23 and minute <= 59 and second <= 59


def split_outside_quotes(text, delimiter):
    """Split on the delimiter, except within double quotes."""
    parts, start, quotes_after = [], 0, text.count('"')
    for i, c in enumerate(text):
        if c == '"':
            quotes_after -= 1
        elif c == delimiter and quotes_after % 2 == 0:
            parts.append(text[start:i])
            start = i + 1
    parts.append(text[start:])
    return parts


# ---------------------------------------------------------------- validation

def _first(validations, pattern):
    """The first validation that matches the pattern, as a match object."""
    for v in validations or []:
        match = re.match(pattern, v)
        if match:
            return match
    return None


class _Validator(object):

    def __init__(self, tables, rules):
        self.tables = tables
        self.rules = rules
        self.model = rules["tables"]
        self.errors = {}  # (table, column, message) -> list of row numbers
        self.column_rules = {}  # (table, column) -> the column's rules, read once
        self.groups = {}
        for table, spec in self.model.items():
            for column, col in spec["columns"].items():
                if col.get("group"):
                    self.groups.setdefault((table, col["group"]), []).append(column)
        self.keys = self._find_keys()

    def _find_keys(self):
        """The values of every column that an in() validation refers to."""
        keys = {}
        for spec in self.model.values():
            for col in spec["columns"].values():
                match = _first(col.get("validations"), r'^in\("([^.]*)\.([^.]*)"\)$')
                if not match:
                    continue
                table, column = match.groups()
                values = keys.setdefault(table, {}).setdefault(column, set())
                if table in self.tables and column in self.tables[table].columns:
                    k = self.tables[table].columns.index(column)
                    values.update(row[k] for row in self.tables[table].rows)
        return keys

    def add(self, table, column, message, row):
        rows = self.errors.setdefault((table, column, message), [])
        # rows arrive in order, so a repeat can only be the last one
        if row is not None and (not rows or rows[-1] != row):
            rows.append(row)

    def rules_for(self, table, column):
        """The rules of a column, from its validations (the first of each kind, as on MagIC)."""
        key = (table, column)
        if key not in self.column_rules:
            spec = self.model[table]["columns"][column]
            validations = spec.get("validations") or []

            def first(pattern):
                match = _first(validations, pattern)
                return match.groups() if match else None

            cv = first(r'^cv\("(.*)"\)$')
            low, high = first(r'^min\(([^"]*)\)$'), first(r'^max\(([^"]*)\)$')
            unless = first(r'^requiredUnless\("(.*)"\)$')
            self.column_rules[key] = {
                "kind": spec.get("type"),
                "required": "required()" in validations,
                "required_if": (first(r'^requiredIf\("(.*)"\)$') or [None])[0],
                "required_if_group": (first(r'^requiredIfGroup\("(.*)"\)$') or [None])[0],
                "required_one_in_group": (first(r'^requiredOneInGroup\("(.*)"\)$') or [None])[0],
                "required_unless": unless[0] if unless else None,
                "unless_columns": unless[0].split('","') if unless else [],
                "required_unless_table": (first(r'^requiredUnlessTable\("(.*)"\)$') or [None])[0],
                "method_codes": 'type("method_codes")' in validations,
                "vocabulary": self.rules["vocabularies"].get(cv[0]) if cv else None,
                "min": (low[0], parse_float(low[0])) if low else None,
                "max": (high[0], parse_float(high[0])) if high else None,
                "in": first(r'^in\("([^.]*)\.([^.]*)"\)$'),
            }
        return self.column_rules[key]

    def run(self):
        order = sorted(self.model, key=lambda t: self.model[t].get("position", 0))
        for table in order:
            if table not in self.tables:
                if table in ("locations", "sites"):
                    self.add(table, "contribution_id", "The {} table is required.".format(table), 1)
                continue
            data = self.tables[table]
            model_columns = self.model[table]["columns"]
            if table == MEASUREMENTS:
                if data.rows:
                    for column, col in model_columns.items():
                        if "required()" in (col.get("validations") or []) and column not in data.columns:
                            self.add(table, column, 'The {} table is missing required column "{}".'
                                     .format(table, column), None)
                if any(key[0] == table for key in self.errors):
                    continue
                for i, values in enumerate(data.rows):
                    row = dict(zip(data.columns, values))
                    for column, value in zip(data.columns, values):
                        if column in model_columns:
                            self.column(table, column, data.columns, i, value, row)
                continue
            for i, values in enumerate(data.rows):
                row = {c: v for c, v in zip(data.columns, values) if v != ""}
                present = list(row)
                for column in model_columns:
                    self.column(table, column, present, i, row.get(column), row)
        return self.errors

    def column(self, table, column, columns, i, val, row):
        """validate_contribution.js, _validateColumn"""
        r = self.rules_for(table, column)
        kind = r["kind"]
        label = 'The {} table'.format(table)
        n = i + 1

        def text(name):
            return _trim(row.get(name) or "")

        if r["required"] and (column not in columns or val is None or _trim(val) == ""):
            self.add(table, column, '{} is missing data in required column "{}".'.format(label, column), n)
        empty = text(column) == ""
        if empty:
            other = r["required_if"]
            if other is not None and text(other) != "":
                self.add(table, column, '{} is missing data in required column "{}" since column "{}" is not '
                         'empty.'.format(label, column, other), n)
            group = r["required_if_group"]
            if group is not None and any(text(c) != "" for c in self.groups.get((table, group), [])):
                self.add(table, column, '{} is missing data in required column "{}" since group "{}" is not '
                         'empty.'.format(label, column, group), n)
            group = r["required_one_in_group"]
            if group is not None and all(text(c) == "" for c in self.groups.get((table, group), [])):
                self.add(table, column, '{} is missing possibly required column "{}" since group "{}" is empty.'
                         .format(label, column, group), n)
            others = r["unless_columns"]
            if r["required_unless"] is not None and all(text(c) == "" for c in others):
                self.add(table, column, '{} is missing data in required column "{}" since column{} "{}" {} empty.'
                         .format(label, column, "" if len(others) == 1 else "s", r["required_unless"],
                                 "is" if len(others) == 1 else "are"), n)
            other = r["required_unless_table"]
            if other is not None and other not in self.tables:
                self.add(table, column, '{} is missing data in required column "{}" since there is no "{}" '
                         'table.'.format(label, column, other), n)

        if not val:
            return
        values = [val]
        if kind in ("List", "Dictionary"):
            values = [v for v in split_outside_quotes(val, ":") if _trim(v) != ""]
        elif kind == "Matrix":
            values = [v for v in split_outside_quotes(val, ";") if _trim(v) != ""]
        vocabulary, low, high, ref = r["vocabulary"], r["min"], r["max"], r["in"]
        for v in values:
            v = _trim(v)
            if v == "":
                continue
            if kind == "Dictionary":
                v = v.split("[", 1)[0]
            if kind == "Matrix":
                v = v.split(":", 1)[0]
            if kind == "Integer" and not INTEGER.match(v):
                self.add(table, column, '{} column "{}" value "{}" is not of type "Integer".'
                         .format(label, column, v), n)
            if kind == "Number" and not NUMBER.match(v):
                self.add(table, column, '{} column "{}" value "{}" is not of type "Number".'
                         .format(label, column, v), n)
            if kind == "Timestamp" and not is_timestamp(v):
                self.add(table, column, '{} column "{}" value "{}" is not of type "Timestamp".'
                         .format(label, column, v), n)
            if r["method_codes"] and v not in self.rules["method_codes"]:
                self.add(table, column, '{} column "{}" value "{}" is an unknown method code.'
                         .format(label, column, v), n)
            # MagIC's check of Matrix and Dictionary values never fails (see the module docstring)
            if vocabulary and kind not in ("Matrix", "Dictionary") and v.lower() not in vocabulary["lower"]:
                self.add(table, column, '{} column "{}" value "{}" is not in the "{}" controlled vocabulary.'
                         .format(label, column, v, vocabulary["label"]), n)
            if low and parse_float(v) < low[1]:
                self.add(table, column, '{} column "{}" value "{}" is less than "{}".'
                         .format(label, column, v, low[0]), n)
            if high and parse_float(v) > high[1]:
                self.add(table, column, '{} column "{}" value "{}" is greater than "{}".'
                         .format(label, column, v, high[0]), n)
            if ref and ref[0] in self.keys and v not in self.keys[ref[0]].get(ref[1], set()):
                self.add(table, column, '{} column "{}" value "{}" is not present in table "{}" column "{}".'
                         .format(label, column, v, ref[0], ref[1]), n)


def validate(contribution, rules=None, online=None):
    """
    Validate a contribution with the rules MagIC applies.

    Parameters
    ----------
    contribution : str, dict or contribution_builder.Contribution
        a MagIC text file (e.g. as written by ipmag.upload_magic), a directory
        of table files, a dict of table name to DataFrame, or a Contribution.
        A directory or a Contribution is validated as the upload file that
        ipmag.upload_magic would make from it (contribution.txt is not
        uploaded, and upload_magic tidies some values, e.g. "6.0" to "6" in
        counts). A dict is validated as given, its values as text: a float
        column gives "6.0" where a file would have "6"
    rules : dict, optional
        from load_rules(); by default load_rules(online)
    online : bool or None
        passed to load_rules() when rules is not given

    Returns
    -------
    DataFrame with one row per problem: level, table, column, message, and
    rows (the row numbers in the table, counted from 1; empty for a problem of
    the whole table). The contribution passes when no problem has the level
    "error". Warnings are data MagIC would leave out (a column that is not in
    the data model, data in a column without a name) or notes on how the
    contribution was read.
    """
    if rules is None:
        rules = load_rules(online)
    tables, parse_errors = read_contribution(contribution)
    problems = [(item[2] if len(item) > 2 else "error", item[0], "", item[1], []) for item in parse_errors]
    for table, data in sorted(tables.items()):
        if table not in rules["tables"]:
            problems.append(("error", table, "", 'Table "{}" is not in the MagIC data model.'.format(table), []))
            continue
        for column in data.columns:
            if column == "":
                k = data.columns.index("")
                rows = [i + 1 for i, row in enumerate(data.rows) if row[k] != ""]
                if rows:
                    problems.append(("warning", table, "", "The {} table has data in a column without a name, "
                                     "which MagIC leaves out.".format(table), rows))
            elif column not in rules["tables"][table]["columns"]:
                if table == MEASUREMENTS:
                    # the EarthRef API fails (HTTP 500) on such a column
                    problems.append(("error", table, column, 'Column "{}" in table "{}" is not in the MagIC data '
                                     'model, and MagIC cannot validate a measurements table with such a '
                                     'column.'.format(column, table), []))
                else:
                    problems.append(("warning", table, column, 'Column "{}" in table "{}" is not in the MagIC '
                                     'data model.'.format(column, table), []))
    known = {name: data for name, data in tables.items() if name in rules["tables"]}
    for (table, column, message), rows in _Validator(known, rules).run().items():
        problems.append(("error", table, column, message, rows))
    return pd.DataFrame(problems, columns=["level", "table", "column", "message", "rows"])


def print_problems(problems, max_rows=10):
    """Print the problems returned by validate(), one line each."""
    if not len(problems):
        print("-I- No problems found")
        return
    for p in problems.itertuples():
        rows = ""
        if p.rows:
            shown = ", ".join(str(r) for r in p.rows[:max_rows])
            rows = " (row{} {}{})".format("s" if len(p.rows) > 1 else "", shown,
                                          ", ..." if len(p.rows) > max_rows else "")
        print("-{}- {}{}".format("E" if p.level == "error" else "W", p.message, rows))
