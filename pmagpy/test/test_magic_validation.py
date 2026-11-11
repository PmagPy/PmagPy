"""
Tests for pmagpy.magic_validation, the port of the MagIC website's validation.

The first group ports lib/modules/magic/tests/validate_contribution.tests.js
of https://github.com/earthref/MagIC (commit 6b6f229). Some expectations there
are older than the validator or the data model they test, and are updated here:
the messages for required columns ("is missing data in required column"); the
valid contribution, given without a contribution table
(which now requires reference and lab_names) and without three columns that
have left the data model; and requiredIfGroup, which the current data model no
longer uses and is tested with a rule added. The rules
come from the cached copies in pmagpy/data_model, so the tests do not need a
network connection.
"""
import os
import re
import shutil
import tempfile
import unittest

import pandas as pd

from pmagpy import contribution_builder as cb
from pmagpy import ipmag, pmag
from pmagpy import magic_validation as mv
from pmagpy import validate_upload3

RULES = mv.load_rules(online=False)


def tables(json):
    """MagIC's test JSON as DataFrames: lists of rows, or measurements as columns and rows."""
    out = {}
    for name, value in json.items():
        if isinstance(value, dict):
            out[name] = pd.DataFrame(value["rows"], columns=value["columns"])
        else:
            out[name] = pd.DataFrame(value)
    return out


def errors(json):
    problems = mv.validate(tables(json), rules=RULES)
    return problems[problems["level"] == "error"]


def valid_contribution():
    # without the contribution table, which now requires reference and lab_names
    # (an upload file has none: MagIC makes it at upload), and without the columns
    # samples.location, specimens.location and specimens.site, no longer in the data model
    json = {
        "locations": [{"location": "location 1", "sites": "site 1", "location_type": "Archeological Ashes",
                       "geologic_classes": "archeologic", "lithologies": ":Achondrite:Agate:", "lat_s": 0,
                       "lat_n": 0, "lon_w": 0, "lon_e": 0, "age": 0, "age_unit": "Ma"}],
        "sites": [{"location": "location 1", "site": "site 1", "result_quality": "g", "result_type": "a",
                   "method_codes": ":LP-PI", "citations": "this study", "geologic_classes": "Archeologic",
                   "geologic_types": "Amphora", "lithologies": ":Achondrite:Agate:", "lat": 0, "lon": 0,
                   "age": 0, "age_unit": "Ma"}],
        "samples": [{"site": "site 1", "sample": "sample 1",
                     "specimens": "specimen 1:specimen 2:", "result_quality": "g", "result_type": "a",
                     "method_codes": ":LP-PI", "citations": "this study"}],
        "specimens": [{"sample": "sample 1", "specimen": "specimen 1",
                       "experiments": "experiment 1", "result_quality": "g", "method_codes": ":LP-PI",
                       "citations": "this study"},
                      {"sample": "sample 1", "specimen": "specimen 2",
                       "experiments": "experiment 2:", "result_quality": "g", "method_codes": ":LP-PI",
                       "citations": "this study"}],
        "measurements": {"columns": ["measurement", "experiment", "specimen", "sequence", "standard", "quality",
                                     "method_codes", "citations"],
                         "rows": [["measurement 1", "experiment 1", "specimen 1", "1", "s", "g", "LP-PI",
                                   "This Study"],
                                  ["measurement 2", "experiment 2", "specimen 2", "2", "s", "g", "LP-PI",
                                   "This Study"]]}}
    return json


class TestMagicValidationPortedTests(unittest.TestCase):
    """validate_contribution.tests.js"""

    def assertError(self, json, table, column, pattern):
        found = errors(json)
        found = found[(found["table"] == table) & (found["column"] == column)]
        self.assertTrue(any(re.search(pattern, m) for m in found["message"]),
                        "no error matching {!r} for {}.{}: {}".format(pattern, table, column, list(found["message"])))

    def assertNoError(self, json, table, column, pattern):
        found = errors(json)
        found = found[(found["table"] == table) & (found["column"] == column)]
        self.assertFalse(any(re.search(pattern, m) for m in found["message"]),
                         "unexpected error for {}.{}: {}".format(table, column, list(found["message"])))

    def check_values(self, table, column, good, bad, pattern, extra=None):
        for value in good + bad:
            json = {"contribution": [{"data_model_version": "3.0"}], table: [dict(extra or {}, **{column: value})]}
            if value in good:
                self.assertNoError(json, table, column, pattern)
            else:
                self.assertError(json, table, column, pattern)

    def test_integer(self):
        self.check_values("locations", "dir_n_sites", ["01", "9 ", "+1", " -2"], ["1.", "a1", " 2* ", "1e5", "-"],
                          r'is not of type "Integer"')

    def test_number(self):
        self.check_values("locations", "age", ["1.", "01", "9 ", "+1", " -2", "1e5", "1e5.2", "1.52e-1"],
                          ["a1", " 2* ", "a", "1-2", "1..2", "1.2.2", "1.2,2"], r'is not of type "Number"')

    def test_timestamp(self):
        # MagIC's list, with the forms that have a space before the time moved to the
        # bad ones: the EarthRef API rejects them (see test_timestamps_as_the_api)
        good = ["2013-02-08", "20130208", "2013-02-08T09", "2013-02-08T09:30:26.123", "20130208T080910,123",
                "2013-02-08T09+07:00", "2013-02-08T09Z", "2013-02-08T09:30:26.123+07:00"]
        bad = ["2013-13-08", "a", ":", "Invalid date", "2013-02-08 09:30:26.123", "2013-02-08 09+07:00",
               "2013-02-08 09Z"]
        self.check_values("samples", "timestamp", good, bad, r'is not of type "Timestamp"')

    def test_measurements_timestamp(self):
        # MagIC's version of this test lacks required measurement columns, so the
        # validation stops before the timestamp; here they are all present
        columns = ["timestamp", "measurement", "experiment", "specimen", "sequence", "quality", "standard",
                   "method_codes", "citations"]
        required = [c for c, spec in RULES["tables"]["measurements"]["columns"].items()
                    if "required()" in (spec.get("validations") or [])]
        self.assertTrue(set(required) <= set(columns), required)
        for value, is_good in [("2013-02-08T09:30:26.123", True), ("2013-13-08", False), ("a", False)]:
            json = {"measurements": {"columns": columns,
                                     "rows": [[value, "1", "a", "b", "1", "g", "u", "LP-PI", "This study"]]}}
            if is_good:
                self.assertNoError(json, "measurements", "timestamp", "Timestamp")
            else:
                self.assertError(json, "measurements", "timestamp", r'is not of type "Timestamp"')

    def test_required(self):
        self.assertError({"locations": [{"location": "location name"}]}, "locations", "location_type",
                         r'missing data in required column')

    def test_required_if(self):
        self.assertError({"locations": [{"age_sigma": 0}]}, "locations", "age",
                         r'missing data in required column .* since column .* is not empty')

    def test_required_if_group(self):
        # the data model of 2026-10-22 has no requiredIfGroup rule, so one is added to a copy
        import copy
        rules = copy.deepcopy(RULES)
        rules["tables"]["locations"]["columns"]["dir_dec"]["validations"].append('requiredIfGroup("Direction")')
        found = mv.validate(tables({"locations": [{"dir_inc": 0}]}), rules=rules)
        found = found[(found["table"] == "locations") & (found["column"] == "dir_dec")]
        self.assertTrue(any(re.search(r'missing data in required column .* since group .* is not empty', m)
                            for m in found["message"]))

    def test_required_one_in_group(self):
        self.assertError({"ages": [{"age": 0}]}, "ages", "location",
                         r'missing possibly required column .* since group .* is empty')

    def test_required_unless(self):
        self.assertError({"locations": [{"location": "location name"}]}, "locations", "age",
                         r'missing data in required column .* since columns? .* (is|are) empty')

    def test_required_unless_table(self):
        self.assertError({"locations": [{"location": "location name"}]}, "locations", "citations",
                         r'missing data in required column .* since there is no .* table')

    def test_controlled_vocabulary(self):
        self.assertError({"locations": [{"age_unit": "?"}]}, "locations", "age_unit",
                         r'not in the .* controlled vocabulary')
        # case is ignored, as by the EarthRef API
        self.assertNoError({"locations": [{"geologic_classes": "ARCHEOLOGIC"}]}, "locations", "geologic_classes",
                           r'not in the .* controlled vocabulary')
        self.assertError({"locations": [{"geologic_classes": "Archeologicc"}]}, "locations", "geologic_classes",
                         r'not in the .* controlled vocabulary')

    def test_method_code(self):
        self.assertError({"locations": [{"method_codes": "LP-PI:?"}]}, "locations", "method_codes",
                         r'value "\?" is an unknown method code')

    def test_min_max(self):
        self.assertError({"locations": [{"lat_s": -91}]}, "locations", "lat_s", r'is less than')
        self.assertError({"locations": [{"lat_s": 91}]}, "locations", "lat_s", r'is greater than')

    def test_keys(self):
        self.assertError({"sites": [{"location": "a"}]}, "sites", "location", r'not present in table .* column')
        self.assertError({"sites": [{"samples": "a"}]}, "sites", "samples", r'not present in table .* column')
        self.assertError({"sites": [{"experiments": "a"}]}, "sites", "experiments", r'not present in table .* column')

    def test_valid_contribution(self):
        self.assertEqual(list(errors(valid_contribution())["message"]), [])


class TestMagicValidation(unittest.TestCase):

    def test_timestamps_as_the_api(self):
        """
        The verdicts of the EarthRef API (api.earthref.org/v1/MagIC/validate) on
        samples.timestamp values, 2026-11-10
        """
        api = {"2013-02-08": True, "20130208": True, "2013-02-08T09": True, "2013-02-08T09:30": True,
               "2013-02-08T09:30:26": True, "2013-02-08T09:30:26.123": True, "2013-02-08T09:30:26Z": True,
               "2013-02-08T09:30:26.123Z": True, "2013-02-08T09:30:26+07:00": True,
               "2013-02-08T09:30:26.123+07:00": True, "2013-02-08 09:30": False, "2013-02-08 09:30:26": False,
               "2013-02-08 09Z": False, "2013-02-08 09+07:00": False, "20130208T080910,123": True,
               "2013-02": True, "2013": True, "2013-039": True, "2013-W06-5": True, "2013/02/08": False,
               "02/08/2013": False, "2013-02-08T24:00": True, "2013-02-30": False}
        self.assertEqual({v: mv.is_timestamp(v) for v in api}, api)

    def test_controlled_vocabulary_case(self):
        # as the EarthRef API: "igneous", "IGNEOUS" and " Igneous " for "Igneous";
        # a value that is not in the vocabulary in any case is reported
        json = valid_contribution()
        json["sites"][0]["geologic_classes"] = "igneous:IGNEOUS: Igneous "
        json["sites"][0]["age_unit"] = "ma"
        self.assertEqual(list(errors(json)["message"]), [])
        json["sites"][0]["geologic_classes"] = "Igneouss"
        self.assertEqual(list(errors(json)["message"]),
                         ['The sites table column "geologic_classes" value "Igneouss" is not in the '
                          '"Geologic Classifications" controlled vocabulary.'])

    def test_required_tables(self):
        found = errors({"samples": [{"sample": "a"}]})
        self.assertIn("The locations table is required.", list(found["message"]))
        self.assertIn("The sites table is required.", list(found["message"]))

    def test_unknown_table_and_column(self):
        json = valid_contribution()
        json["sites"][0]["not_a_column"] = "x"
        json["other"] = [{"a": 1}]
        problems = mv.validate(tables(json), rules=RULES)
        warning = problems[problems["level"] == "warning"]
        self.assertEqual(list(zip(warning["table"], warning["column"])), [("sites", "not_a_column")])
        self.assertIn('Table "other" is not in the MagIC data model.', list(problems["message"]))

    def test_parser(self):
        # a trailing tab gives a column without a name, which MagIC allows
        text = "\n".join([
            "tab \tlocations", "location\tlocation_type\t", "A\tOutcrop", ">>>>>>>>>>", "",
            "tab delimited\tSITES", "site\tlocation", "s1\tA", ">>>>>>>>>>",
            "tab\tsamples", "sample\tsample", "x\tx", ">>>>>>>>>>",
            "tab\tspecimens", "specimen\tsample", "a\tb\tc"])
        parsed, parse_errors = mv.parse_magic_text(text)
        self.assertEqual(sorted(parsed), ["locations", "samples", "sites", "specimens"])
        self.assertEqual(parsed["sites"].columns, ["site", "location"])
        self.assertEqual(parsed["locations"].rows, [["A", "Outcrop", ""]])
        self.assertEqual(parsed["samples"].rows, [])
        # line numbers are those of the file, counting the empty line
        self.assertEqual([m for _, m in parse_errors], ["Found duplicate column names on line 11.",
                                                        "More values found than columns on line 16."])
        json = valid_contribution()
        json["locations"][0][""] = "x"
        self.assertIn("The locations table has data in a column missing a name.", list(errors(json)["message"]))

    def test_split_outside_quotes(self):
        self.assertEqual(mv.split_outside_quotes('a:"b:c":d', ":"), ['a', '"b:c"', 'd'])

    def test_upload_file_and_other_inputs(self):
        """a file written by ipmag.upload_magic, a directory of tables and a Contribution"""
        json = valid_contribution()
        tmp = tempfile.mkdtemp()
        try:
            # a directory and a Contribution are validated as their upload file: without
            # contribution.txt, and with upload_magic's "2.0" -> "2" in counts
            json["contribution"] = [{"data_model_version": "3.0"}]
            json["locations"][0]["dir_n_sites"] = "2.0"
            for name, df in tables(json).items():
                pmag.magic_write(os.path.join(tmp, name + ".txt"), df, name, dataframe=True)
            self.assertEqual(len(mv.validate(tmp, rules=RULES)), 0)
            con = cb.Contribution(tmp)
            self.assertEqual(len(mv.validate(con, rules=RULES)), 0)
            upload = ipmag.upload_magic(dir_path=tmp, input_dir_path=tmp, validate=False, verbose=False)[0]
            self.assertEqual(len(mv.validate(upload, rules=RULES)), 0)
            # the same file with an unknown method code and a decimal point in an integer
            with open(upload) as f:
                text = f.read()
            with open(upload, "w") as f:
                f.write(text.replace("LP-PI", "LP-PI-NOT-A-CODE").replace("\t1\t", "\t1.0\t"))
            problems = mv.validate(upload, rules=RULES)
            messages = " ".join(problems["message"])
            self.assertIn('"LP-PI-NOT-A-CODE" is an unknown method code', messages)
            self.assertIn('"1.0" is not of type "Integer"', messages)
        finally:
            shutil.rmtree(tmp)

    def test_cached_rules(self):
        # the cached data model, method codes and vocabularies are current
        self.assertGreaterEqual(RULES["updated_day"], "2026:10:22")
        self.assertIn("int_abs_min", RULES["tables"]["sites"]["columns"])
        self.assertIn("DE-BFL-A", RULES["method_codes"])
        self.assertIn("lab_names", RULES["vocabularies"])
        self.assertEqual(RULES["source"], "cache")

    def test_read_js_object(self):
        text = ('export const x = {\n  "a": [{"item": "x // not a comment"}, // a comment\n'
                '  /* another */ {"item": "y",},\n  ],\n};\n')
        self.assertEqual(mv._read_js_object(text), {"a": [{"item": "x // not a comment"}, {"item": "y"}]})


class TestValidateUpload3(unittest.TestCase):
    """the deprecated module validate_upload3"""

    def test_validate_contribution_uses_magic_validation(self):
        import warnings
        tmp = tempfile.mkdtemp()
        try:
            json = valid_contribution()
            json["sites"][0]["method_codes"] = "LP-NOT-A-CODE"
            for name, df in tables(json).items():
                pmag.magic_write(os.path.join(tmp, name + ".txt"), df, name, dataframe=True)
            con = cb.Contribution(tmp)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                problems = validate_upload3.validate_contribution(con)
            self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
            self.assertIn('The sites table column "method_codes" value "LP-NOT-A-CODE" is an unknown method code.',
                          list(problems["message"]))
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                validate_upload3.validate_table(con, "sites", output_dir=tmp)
            self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
