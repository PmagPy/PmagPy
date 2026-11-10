"""
Validate a MagIC contribution with the rules that MagIC applies.

This module ports the parser and the validator of the MagIC website, so that a
contribution that passes here passes the validation run on MagIC:

    https://github.com/earthref/MagIC
        lib/modules/magic/parse_contribution.js      reading a MagIC text file
        lib/modules/magic/validate_contribution.js   the validation
    (ported from commit 6b6f229, 2026-11-10)

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
    - controlled vocabularies (cv), compared exactly (case matters)
    - min() and max() with a number
    - in("table.column"): references between tables
Rules of the data model that MagIC does not check are not checked here either
(e.g. requiredUnlessSynthetic(), unique(), suggested vocabularies).

Where this module differs from MagIC, it reports more:
    - every row of the measurements table is checked (MagIC checks the first
      10000), and a measurements row with fewer values than columns is checked
      for its empty required values
    - a column that is not in the data model is reported as a warning (on MagIC
      the upload tool asks for it to be matched to a data model column or left out)
    - a table that is not in the data model, an empty column name and a
      malformed table are reported as errors, and the rest of the file is still read
One check is approximate: a Timestamp that is not in an ISO 8601 form is
accepted if it is an RFC 2822 date or dateutil can read it, where MagIC
(moment.js) falls back to the JavaScript Date parser.
MagIC's controlled-vocabulary check of Matrix and Dictionary columns never
reports a value (the comparison in validate_contribution.js always succeeds),
so those values are not checked here either.

Typical use:
    from pmagpy import magic_validation
    problems = magic_validation.validate('upload_file.txt')
    magic_validation.print_problems(problems)
"""
import datetime
import email.utils
import json
import os
import re

import pandas as pd

try:
    import requests
except ImportError:
    requests = None
try:
    from dateutil import parser as dateutil_parser
except ImportError:
    dateutil_parser = None

from pmag_env import set_env

DATA_MODEL_URL = "https://earthref.org/MagIC/data-models/3.0.json"
METHOD_CODES_URL = "https://www2.earthref.org/MagIC/method-codes.json"
MAGIC_SOURCE_URL = "https://raw.githubusercontent.com/earthref/MagIC/main/"
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
_RESOURCES = {}
_RULES = {}


# ---------------------------------------------------------------- the rules

def cache_dir():
    """The directory of the cached data model, method codes and vocabularies."""
    here = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data_model")
    if os.path.isdir(here):
        return here
    # a py2app build has a flat directory structure
    from . import find_pmag_dir
    pmag_dir = find_pmag_dir.get_pmag_dir()
    for path in (os.path.join(pmag_dir, "pmagpy", "data_model"), os.path.join(pmag_dir, "data_model")):
        if os.path.isdir(path):
            return path
    return here


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
    body = re.sub(r",(\s*[}\]])", r"\1", body)
    return json.loads(body, strict=False)


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
        copy if the download fails

    Returns
    -------
    (data, source): source is "online" or "cache"
    """
    fall_back = online is None
    if online is None:
        online = not set_env.OFFLINE
    key = (name, bool(online))
    if key not in _RESOURCES:
        data, source = None, "cache"
        if online:
            try:
                data, source = download_resource(name, timeout), "online"
            except Exception as ex:
                if not fall_back:
                    raise
                print("-W- Could not download the MagIC {} ({}); using the cached copy".format(
                    name.replace("_", " "), ex))
        if data is None:
            data = read_cached_resource(name)
        _RESOURCES[key] = (data, source)
    return _RESOURCES[key]


def update_cache(directory=None, timeout=30):
    """
    Download the MagIC data model, method codes and vocabularies and write them
    to the cached files in pmagpy/data_model (or directory).

    Returns
    -------
    dict of the files written
    """
    directory = directory or cache_dir()
    written = {}
    for name, (_, _, filename) in RESOURCES.items():
        data = download_resource(name, timeout)
        path = os.path.join(directory, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent="\t", ensure_ascii=False)
            f.write("\n")
        written[name] = path
    _RESOURCES.clear()
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
    key = online if online is not None else not set_env.OFFLINE
    if key in _RULES and online is not None:
        return _RULES[key]
    loaded = {name: get_resource(name, online, timeout) for name in ("data_model", "method_codes", "vocabularies")}
    sources = sorted({source for _, source in loaded.values()})
    data_model, method_codes, vocabularies = (loaded[n][0] for n in ("data_model", "method_codes", "vocabularies"))
    rules = {"tables": data_model["tables"],
             "updated_day": data_model.get("updated_day", ""),
             "vocabularies": {name: {"label": v.get("label", name), "items": {i["item"] for i in v["items"]}}
                              for name, v in vocabularies.items()},
             "method_codes": {c["code"] for codes in method_codes.values() for c in codes["codes"]},
             "source": " and ".join(sources)}
    _RULES[key] = rules
    return rules


# ---------------------------------------------------------------- reading a contribution

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
    (table, message)
    """
    tables, errors = {}, []
    table, columns, table_line, skip = None, [], 0, False
    for number, line in enumerate(re.split(r"[\n\v\f\r\x85  ]+", text), start=1):
        if line.strip() == "":
            continue
        if re.match(r"^>+$", line.strip()):
            table, columns, table_line, skip = None, [], 0, False
            continue
        if skip:
            continue
        table_line += 1
        if table_line == 1:
            definition = [x.strip() for x in line.split("\t")]
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
            columns = [x.strip().lower() for x in line.split("\t")]
            if "" in columns:
                errors.append((table, "Empty column names are not allowed on line {}.".format(number)))
                skip = True
            elif len(columns) != len(set(columns)):
                errors.append((table, "Found duplicate column names on line {}.".format(number)))
                skip = True
            elif tables[table] is None:
                tables[table] = _Table(columns)
            elif tables[table].columns != columns:
                errors.append((table, "The {} table is defined twice with different columns (line {})."
                               .format(table, number)))
                skip = True
        else:
            values = [x.strip() for x in line.split("\t")]
            if len(values) > len(columns):
                errors.append((table, "More values found than columns on line {}.".format(number)))
                skip = True
                continue
            tables[table].rows.append(values + [""] * (len(columns) - len(values)))
    return {name: t for name, t in tables.items() if t is not None}, errors


def _cell_text(value):
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _from_dataframe(df):
    columns = [str(c).strip().lower() for c in df.columns]
    rows = [[_cell_text(v) for v in row] for row in df.itertuples(index=False, name=None)]
    return _Table(columns, rows)


def read_contribution(contribution):
    """
    The tables of a contribution, read as MagIC reads them.

    Parameters
    ----------
    contribution : str, dict or contribution_builder.Contribution
        a MagIC text file (e.g. written by ipmag.upload_magic); a directory
        holding table files named after their table (sites.txt, ...); a dict
        of table name to DataFrame; or a Contribution

    Returns
    -------
    (tables, errors) as from parse_magic_text
    """
    if isinstance(contribution, str) and os.path.isdir(contribution):
        tables, errors = {}, []
        for name in sorted(os.listdir(contribution)):
            table = os.path.splitext(name)[0]
            if not name.endswith(".txt") or table not in read_cached_resource("data_model")["tables"]:
                continue
            with open(os.path.join(contribution, name), encoding="utf-8-sig", errors="replace") as f:
                parsed, parse_errors = parse_magic_text(f.read())
            tables.update(parsed)
            errors += parse_errors
        return tables, errors
    if isinstance(contribution, str):
        with open(contribution, encoding="utf-8-sig", errors="replace") as f:
            return parse_magic_text(f.read())
    if hasattr(contribution, "tables") and not isinstance(contribution, dict):
        contribution = {name: table.df for name, table in contribution.tables.items()}
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
# the ISO 8601 forms accepted by moment.js, which MagIC uses
_ISO_DATE = (r"(?P<date>[+-][0-9]{6}|[0-9]{4})(?:-(?P<ext>[0-9]{2}-[0-9]{2}|W[0-9]{2}-[0-9]|W[0-9]{2}|[0-9]{3}|[0-9]{2})"
             r"|(?P<basic>[0-9]{4}|W[0-9]{3}|W[0-9]{2}|[0-9]{3}|[0-9]{2})?)")
_ISO_TIME = (r"(?:[T ](?P<time>[0-9]{2}(?::?[0-9]{2}(?::?[0-9]{2}(?:[.,][0-9]+)?)?)?)"
             r"(?P<zone>[+-][0-9]{2}(?::?[0-9]{2})?|\s*Z)?)?")
ISO_8601 = re.compile(r"^\s*" + _ISO_DATE + _ISO_TIME + r"$")


def parse_float(value):
    """JavaScript parseFloat: the number at the start of the text, or NaN."""
    match = _FLOAT_PREFIX.match(str(value))
    if not match:
        return float("nan")
    return float(match.group(1).replace("Infinity", "inf"))


def _valid_iso(match):
    date = match.group("date")
    rest = match.group("ext") or match.group("basic") or ""
    year = int(date)
    try:
        if rest.startswith("W") or len(rest) == 3 or rest == "":
            pass  # week dates, ordinal dates and a year alone
        elif len(rest) == 2:
            datetime.date(2000, int(rest), 1)  # year and month
        else:
            month, day = (rest.split("-") if "-" in rest else (rest[:2], rest[2:]))
            datetime.date(year if 1 <= year <= 9999 else 2000, int(month), int(day))
        time = (match.group("time") or "").replace(":", "")
        if time:
            hour, minute, second = int(time[:2]), int(time[2:4] or 0), int(time[4:6] or 0)
            if hour > 24 or minute > 59 or second > 59:
                return False
    except ValueError:
        return False
    return True


def is_timestamp(value):
    """
    True if moment.js, which MagIC uses, reads the text as a valid date.

    ISO 8601 forms are checked as moment.js checks them; other text is accepted
    if it is an RFC 2822 date or dateutil can read it, an approximation of the
    JavaScript Date parser that moment.js falls back to.
    """
    match = ISO_8601.match(value)
    if match:
        return _valid_iso(match)
    try:
        if email.utils.parsedate_to_datetime(value):
            return True
    except (TypeError, ValueError, IndexError):
        pass
    if dateutil_parser is None or not re.search(r"[0-9]", value):
        return False
    try:
        dateutil_parser.parse(value)
        return True
    except (ValueError, OverflowError):
        return False


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
        if row is not None and row not in rows:
            rows.append(row)

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
        spec = self.model[table]["columns"][column]
        validations = spec.get("validations") or []
        kind = spec.get("type")
        label = 'The {} table'.format(table)
        n = i + 1

        def text(name):
            return (row.get(name) or "").strip()

        if "required()" in validations and (column not in columns or val is None or val.strip() == ""):
            self.add(table, column, '{} is missing data in required column "{}".'.format(label, column), n)
        empty = text(column) == ""
        match = _first(validations, r'^requiredIf\("(.*)"\)$')
        if match and empty and text(match.group(1)) != "":
            self.add(table, column, '{} is missing data in required column "{}" since column "{}" is not empty.'
                     .format(label, column, match.group(1)), n)
        match = _first(validations, r'^requiredIfGroup\("(.*)"\)$')
        if match and empty and any(text(c) != "" for c in self.groups.get((table, match.group(1)), [])):
            self.add(table, column, '{} is missing data in required column "{}" since group "{}" is not empty.'
                     .format(label, column, match.group(1)), n)
        match = _first(validations, r'^requiredOneInGroup\("(.*)"\)$')
        if match and empty and all(text(c) == "" for c in self.groups.get((table, match.group(1)), [])):
            self.add(table, column, '{} is missing possibly required column "{}" since group "{}" is empty.'
                     .format(label, column, match.group(1)), n)
        match = _first(validations, r'^requiredUnless\("(.*)"\)$')
        if match and empty and all(text(c) == "" for c in match.group(1).split('","')):
            others = match.group(1).split('","')
            self.add(table, column, '{} is missing data in required column "{}" since column{} "{}" {} empty.'
                     .format(label, column, "" if len(others) == 1 else "s", match.group(1),
                             "is" if len(others) == 1 else "are"), n)
        match = _first(validations, r'^requiredUnlessTable\("(.*)"\)$')
        if match and empty and match.group(1) not in self.tables:
            self.add(table, column, '{} is missing data in required column "{}" since there is no "{}" table.'
                     .format(label, column, match.group(1)), n)

        if not val:
            return
        values = [val]
        if kind in ("List", "Dictionary"):
            values = [v for v in split_outside_quotes(val, ":") if v.strip() != ""]
        elif kind == "Matrix":
            values = [v for v in split_outside_quotes(val, ";") if v.strip() != ""]
        cv = _first(validations, r'^cv\("(.*)"\)$')
        vocabulary = self.rules["vocabularies"].get(cv.group(1)) if cv else None
        low = _first(validations, r'^min\(([^"]*)\)$')
        high = _first(validations, r'^max\(([^"]*)\)$')
        ref = _first(validations, r'^in\("([^.]*)\.([^.]*)"\)$')
        for v in values:
            v = v.strip()
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
            if 'type("method_codes")' in validations and v not in self.rules["method_codes"]:
                self.add(table, column, '{} column "{}" value "{}" is an unknown method code.'
                         .format(label, column, v), n)
            # MagIC's check of Matrix and Dictionary values never fails (see the module docstring)
            if vocabulary and kind not in ("Matrix", "Dictionary") and v not in vocabulary["items"]:
                self.add(table, column, '{} column "{}" value "{}" is not in the "{}" controlled vocabulary.'
                         .format(label, column, v, vocabulary["label"]), n)
            if low and parse_float(v) < parse_float(low.group(1)):
                self.add(table, column, '{} column "{}" value "{}" is less than "{}".'
                         .format(label, column, v, low.group(1)), n)
            if high and parse_float(v) > parse_float(high.group(1)):
                self.add(table, column, '{} column "{}" value "{}" is greater than "{}".'
                         .format(label, column, v, high.group(1)), n)
            if ref and ref.group(1) in self.keys and v not in self.keys[ref.group(1)].get(ref.group(2), set()):
                self.add(table, column, '{} column "{}" value "{}" is not present in table "{}" column "{}".'
                         .format(label, column, v, ref.group(1), ref.group(2)), n)


def validate(contribution, rules=None, online=None):
    """
    Validate a contribution with the rules MagIC applies.

    Parameters
    ----------
    contribution : str, dict or contribution_builder.Contribution
        a MagIC text file (e.g. as written by ipmag.upload_magic), a directory
        of table files, a dict of table name to DataFrame, or a Contribution.
        Values are checked as text, as they would be written: validate the
        file to be uploaded where possible (a float column read into pandas,
        for example, gives "6.0" where the file has "6")
    rules : dict, optional
        from load_rules(); by default load_rules(online)
    online : bool or None
        passed to load_rules() when rules is not given

    Returns
    -------
    DataFrame with one row per problem: level ("error", or "warning" for a
    column that is not in the data model), table, column, message, and rows
    (the row numbers in the table, counted from 1; empty for a problem of the
    whole table). An empty DataFrame means the contribution passes.
    """
    if rules is None:
        rules = load_rules(online)
    tables, parse_errors = read_contribution(contribution)
    problems = [("error", table, "", message, []) for table, message in parse_errors]
    for table, data in sorted(tables.items()):
        if table not in rules["tables"]:
            problems.append(("error", table, "", 'Table "{}" is not in the MagIC data model.'.format(table), []))
            continue
        for column in data.columns:
            if column not in rules["tables"][table]["columns"]:
                problems.append(("warning", table, column, 'Column "{}" in table "{}" is not in the MagIC data '
                                 'model.'.format(column, table), []))
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
