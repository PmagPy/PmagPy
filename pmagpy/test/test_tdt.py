"""
Tests for pmagpy.tdt: reading, checking and converting ThellierTool files.

The fixtures are written here rather than shipped, so that the failure modes
reported in PmagPy/PmagPy#818 are reproduced without redistributing anybody's
unpublished measurements. The SPD calibration set (which *is* shipped, and is
published for exactly this purpose) provides the twenty real files.
"""
import os
import shutil
import tempfile

import numpy as np
import pandas as pd
import pytest

from pmagpy import paleointensity as pi
from pmagpy import tdt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SPD_TT = os.path.join(REPO, "data_files", "SPD_calibration", "TT")

COE = """Thellier-tdt
45.0\t0\t0\t0\t0
SP1\t0.0\t100.0\t10.0\t30.0
SP1\t100.0\t95.0\t10.5\t30.5
SP1\t100.1\t97.0\t11.0\t35.0
SP1\t200.0\t88.0\t10.2\t29.5
SP1\t200.1\t93.0\t12.0\t40.0
SP1\t100.2\t96.5\t11.1\t34.5
SP1\t300.0\t70.0\t10.0\t29.0
SP1\t300.1\t85.0\t13.0\t48.0
SP1\t200.3\t87.0\t10.1\t29.4
SP1\t400.0\t45.0\t9.8\t28.0
SP1\t400.1\t72.0\t14.0\t58.0
"""

THELLIER_THELLIER = """Thellier-tdt
45.0\t0\t0\t0\t0
TT1\t0.00\t343.38\t177.30\t11.60
TT1\t100.10\t340.26\t177.50\t15.90
TT1\t100.50\t328.30\t178.20\t9.10
TT1\t200.10\t328.99\t180.60\t24.20
TT1\t200.50\t294.02\t179.40\t-0.20
TT1\t300.10\t324.08\t179.50\t39.20
TT1\t300.50\t261.71\t180.90\t-16.40
TT1\t400.10\t364.92\t176.10\t61.30
TT1\t400.50\t276.96\t186.20\t-50.30
"""


def write(text, directory, name="SP1.tdt"):
    path = os.path.join(directory, name)
    with open(path, "w", newline="\r\n") as fh:
        fh.write(text)
    return path


@pytest.fixture()
def workdir():
    tmp = tempfile.mkdtemp(prefix="tdt-test-")
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------
class TestReading:
    def test_a_coe_file_parses(self, workdir):
        file = tdt.read(write(COE, workdir))
        assert file.parse_errors == []
        assert file.blab_uT == pytest.approx(45.0)
        assert file.specimens == ["SP1"]
        assert len(file.rows) == 11
        assert file.protocol() == "Coe"
        assert file.line_ending == "CRLF"

    def test_the_first_low_temperature_step_is_the_nrm(self, workdir):
        file = tdt.read(write(COE, workdir))
        assert file.rows[0].is_nrm
        assert file.rows[0].temperature_k == pytest.approx(273.0)
        assert not file.rows[1].is_nrm

    def test_step_codes_are_classified(self, workdir):
        file = tdt.read(write(COE, workdir))
        kinds = [r.code for r in file.rows]
        assert kinds.count(0) == 5          # NRM plus four zero-field steps
        assert kinds.count(1) == 4
        assert kinds.count(2) == 1
        assert kinds.count(3) == 1

    def test_trailing_zeros_in_the_code_are_harmless(self):
        assert tdt._split_treatment("0.00") == (0.0, 0, "")
        assert tdt._split_treatment("400.10") == (400.0, 1, "")
        assert tdt._split_treatment("400") == (400.0, 0, "")
        assert tdt._split_treatment("400.") == (400.0, 0, "")

    def test_an_unreadable_code_is_reported_with_its_line(self, workdir):
        text = COE.replace("SP1\t300.0\t", "SP1\t300.z\t")
        file = tdt.read(write(text, workdir))
        assert any(e.code == "treatment-unreadable" for e in file.parse_errors)
        assert file.parse_errors[0].line == 9

    def test_a_missing_header_is_an_error_not_an_exception(self, workdir):
        file = tdt.read(write(COE.replace("Thellier-tdt\n", "", 1), workdir))
        assert any(e.code == "header-missing" for e in file.parse_errors)

    def test_a_short_row_is_reported_and_the_rest_still_read(self, workdir):
        text = COE.replace("SP1\t200.0\t88.0\t10.2\t29.5\n", "SP1\t200.0\t88.0\n")
        file = tdt.read(write(text, workdir))
        assert any(e.code == "row-short" for e in file.parse_errors)
        assert len(file.rows) == 10

    def test_the_original_thellier_thellier_protocol_is_recognised(self, workdir):
        file = tdt.read(write(THELLIER_THELLIER, workdir, "TT1.tdt"))
        assert file.protocol() == "Thellier-Thellier"
        assert file.parse_errors == []

    def test_a_file_with_both_zero_field_and_antiparallel_steps_is_not_thellier_thellier(self, workdir):
        text = THELLIER_THELLIER.replace("100.10", "100.00").replace("200.10", "200.00")
        file = tdt.read(write(text, workdir, "TT1.tdt"))
        assert file.protocol() != "Thellier-Thellier"

    def test_the_frame_view_names_every_step(self, workdir):
        frame = tdt.read(write(COE, workdir)).to_frame()
        assert set(frame["step"]) == {"zero field", "in field", "pTRM check", "pTRM tail check"}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
class TestValidation:
    def test_a_good_file_has_no_errors(self, workdir):
        issues = tdt.validate(tdt.read(write(COE, workdir)))
        assert tdt.summarise(issues)["ok"]
        assert tdt.summarise(issues)["errors"] == 0

    def test_an_in_field_step_with_no_zero_field_partner_is_an_error(self, workdir):
        text = COE.replace("SP1\t300.0\t70.0\t10.0\t29.0\n", "")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        errors = [i for i in issues if i.code == "unpaired-infield"]
        assert errors and "300" in errors[0].message
        assert errors[0].line
        assert "add the .0 step" in errors[0].hint

    def test_an_incomplete_antiparallel_pair_is_an_error(self, workdir):
        text = THELLIER_THELLIER.replace("TT1\t200.50\t294.02\t179.40\t-0.20\n", "")
        issues = tdt.validate(tdt.read(write(text, workdir, "TT1.tdt")))
        errors = [i for i in issues if i.code == "unpaired-antiparallel"]
        assert errors and ".5" in errors[0].message

    def test_a_check_at_a_temperature_never_used_is_a_warning(self, workdir):
        text = COE.replace("SP1\t100.2\t", "SP1\t150.2\t")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        assert any(i.code == "check-off-grid" for i in issues)

    def test_a_missing_laboratory_field_is_an_error(self, workdir):
        text = COE.replace("45.0\t0\t0\t0\t0", "\t0\t0\t0\t0")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        assert any(i.code == "blab-missing" for i in issues)

    def test_a_laboratory_field_in_the_wrong_unit_is_flagged(self, workdir):
        text = COE.replace("45.0\t0\t0\t0\t0", "45000\t0\t0\t0\t0")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        assert any(i.code == "blab-units" for i in issues)

    def test_moments_in_field_units_need_a_volume(self, workdir):
        issues = tdt.validate(tdt.read(write(COE, workdir)), moment_units="mA/m", volume_cc=0)
        assert any(i.code == "volume-missing" for i in issues)

    def test_columns_in_the_wrong_order_are_caught_by_the_inclination(self, workdir):
        text = COE.replace("SP1\t100.0\t95.0\t10.5\t30.5", "SP1\t100.0\t10.5\t30.5\t95.0")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        assert any(i.code == "inc-range" for i in issues)
        assert any("column order" in (i.hint or "") for i in issues)

    def test_a_specimen_name_that_differs_from_the_file_name_is_a_note(self, workdir):
        issues = tdt.validate(tdt.read(write(COE, workdir, "OTHER.tdt")))
        notes = [i for i in issues if i.code == "specimen-name"]
        assert notes and notes[0].level == "note"

    def test_out_of_order_temperatures_are_a_warning(self, workdir):
        lines = COE.strip().split("\n")
        lines[3], lines[7] = lines[7], lines[3]
        issues = tdt.validate(tdt.read(write("\n".join(lines) + "\n", workdir)))
        assert any(i.code == "non-monotonic" for i in issues)

    def test_a_duplicate_step_is_reported(self, workdir):
        text = COE.replace("SP1\t200.0\t88.0\t10.2\t29.5\n",
                           "SP1\t200.0\t88.0\t10.2\t29.5\nSP1\t200.0\t88.4\t10.2\t29.6\n")
        issues = tdt.validate(tdt.read(write(text, workdir)))
        assert any(i.code == "duplicate-step" for i in issues)

    def test_an_embedded_anisotropy_block_is_reported_not_swallowed(self, workdir):
        extra = "".join(f"SP1\t400.8{k}\t{50 + k}.0\t{10 * k}.0\t5.0\n" for k in range(1, 7))
        issues = tdt.validate(tdt.read(write(COE + extra, workdir)))
        blocks = [i for i in issues if i.code == "anisotropy-block"]
        assert blocks and "six-position" in blocks[0].message

    def test_the_issues_render_as_a_table(self, workdir):
        issues = tdt.validate(tdt.read(write(COE, workdir, "OTHER.tdt")))
        frame = tdt.issues_frame(issues)
        assert set(frame.columns) == {"level", "line", "specimen", "problem", "what to do", "code"}

    def test_every_issue_prints_where_and_what_to_do(self, workdir):
        text = COE.replace("SP1\t300.0\t70.0\t10.0\t29.0\n", "")
        for issue in tdt.validate(tdt.read(write(text, workdir))):
            assert str(issue).startswith(issue.level)


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------
class TestConversion:
    def test_a_coe_file_converts_and_loads(self, workdir):
        path = write(COE, workdir)
        out = os.path.join(workdir, "magic")
        result = tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0)
        assert result["ok"] and result["specimens"] == ["SP1"]
        for name in ("measurements", "specimens", "samples", "sites", "locations"):
            assert os.path.exists(os.path.join(out, name + ".txt"))
        data = pi.PintData.from_directory(out)
        arai = data.specimens["SP1"].arai
        assert arai.protocol == "Coe"
        assert arai.n == 5
        assert len(arai.ptrm_checks) == 1
        assert len(arai.tail_checks) == 1

    def test_the_thellier_thellier_pair_becomes_one_arai_point(self, workdir):
        path = write(THELLIER_THELLIER, workdir, "TT1.tdt")
        out = os.path.join(workdir, "magic")
        assert tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0)["ok"]
        data = pi.PintData.from_directory(out)
        arai = data.specimens["TT1"].arai
        assert arai.protocol == "Thellier-Thellier"
        assert arai.n == 5                       # the NRM plus one per pair
        assert arai.steps[1:] == ["II"] * 4
        # the NRM left is the half sum, the pTRM the half difference
        rows = tdt.read(path).rows
        from pmagpy import pint_stats as ps
        m1 = ps.dir_to_cart(rows[1].dec, rows[1].inc, rows[1].moment)
        m2 = ps.dir_to_cart(rows[2].dec, rows[2].inc, rows[2].moment)
        assert arai.y[1] == pytest.approx(np.linalg.norm((m1 + m2) / 2), rel=1e-6)
        assert arai.x[1] == pytest.approx(np.linalg.norm((m1 - m2) / 2), rel=1e-6)

    def test_both_halves_are_written_as_measured_not_as_synthetic_rows(self, workdir):
        path = write(THELLIER_THELLIER, workdir, "TT1.tdt")
        out = os.path.join(workdir, "magic")
        tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0)
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str)
        assert len(meas) == 9
        assert (meas["method_codes"].str.contains("LP-PI-II")).all()
        infield = meas[meas["method_codes"].str.contains("LT-T-I")]
        assert set(infield["treat_dc_field_theta"]) == {"90.0", "-90.0"}

    def test_conversion_stops_on_an_error_unless_told_otherwise(self, workdir):
        text = COE.replace("SP1\t300.0\t70.0\t10.0\t29.0\n", "")
        path = write(text, workdir)
        out = os.path.join(workdir, "magic")
        result = tdt.to_magic([path], out)
        assert not result["ok"] and result["files"] == []
        assert not os.path.exists(os.path.join(out, "measurements.txt"))
        forced = tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0,
                              validate_first=False)
        assert forced["ok"]

    def test_the_uppercase_extension_is_found(self, workdir):
        write(COE, workdir, "SP1.TDT")
        assert len(tdt.find_tdt_files(workdir)) == 1

    def test_the_anisotropy_block_is_only_imported_on_request(self, workdir):
        extra = "".join(f"SP1\t400.8{k}\t{50 + k}.0\t{60 * (k - 1)}.0\t5.0\n" for k in range(1, 7))
        path = write(COE + extra, workdir)
        out = os.path.join(workdir, "magic")
        tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0, validate_first=False)
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str)
        assert not meas["method_codes"].str.contains("LP-AN-TRM").any()
        shutil.rmtree(out)
        tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0, validate_first=False,
                     import_anisotropy=True)
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str)
        assert meas["method_codes"].str.contains("LP-AN-TRM").sum() == 6

    def test_moment_units_are_converted(self, workdir):
        path = write(COE, workdir)
        out = os.path.join(workdir, "magic")
        tdt.to_magic([path], out, moment_units="mA/m", volume_cc=12.0)
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str)
        # 100 mA/m in 12 cc is 100e-3 * 12e-6 Am^2
        assert float(meas["magn_moment"].iloc[0]) == pytest.approx(100e-3 * 12e-6)

    def test_the_specimen_can_be_named_from_the_file(self, workdir):
        path = write(COE, workdir, "MY-SPEC.tdt")
        out = os.path.join(workdir, "magic")
        result = tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0,
                              specimen_from_filename=True)
        assert result["specimens"] == ["MY-SPEC"]

    def test_sample_and_site_naming_can_be_supplied(self, workdir):
        path = write(COE, workdir)
        out = os.path.join(workdir, "magic")
        tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0,
                     sample_name=lambda s: s[:-1], site_name=lambda s: s[:-1])
        samples = pd.read_csv(os.path.join(out, "samples.txt"), sep="\t", skiprows=1, dtype=str)
        assert samples["sample"].iloc[0] == "SP"

    def test_the_written_measurements_carry_a_stable_identifier(self, workdir):
        path = write(COE, workdir)
        out = os.path.join(workdir, "magic")
        tdt.to_magic([path], out, moment_units="Am^2", volume_cc=1.0)
        meas = pd.read_csv(os.path.join(out, "measurements.txt"), sep="\t", skiprows=1, dtype=str)
        assert meas["measurement"].is_unique
        assert meas["measurement"].iloc[0].startswith("SP1-")


# ---------------------------------------------------------------------------
# The calibration files, as shipped
# ---------------------------------------------------------------------------
class TestCalibrationFiles:
    def test_every_calibration_file_reads_without_a_parse_error(self):
        paths = tdt.find_tdt_files(SPD_TT)
        assert len(paths) == 20
        for path in paths:
            file = tdt.read(path)
            assert file.parse_errors == [], f"{os.path.basename(path)}: {file.parse_errors}"
            assert file.blab_uT > 0
            assert len(file.rows) > 10

    def test_every_calibration_file_validates(self):
        for path in tdt.find_tdt_files(SPD_TT):
            issues = tdt.validate(tdt.read(path))
            errors = [i for i in issues if i.level == "error"]
            assert not errors, f"{os.path.basename(path)}: {[str(e) for e in errors]}"

    def test_the_protocols_are_the_ones_spd_documents(self):
        protocols = {}
        for path in tdt.find_tdt_files(SPD_TT):
            name = os.path.splitext(os.path.basename(path))[0]
            protocols[name] = tdt.read(path).protocol()
        # SPD Table 1: RS25b, RS26a and RS26e are IZZI, the rest are Coe-style
        assert protocols["RS25b"] == "IZZI"
        assert protocols["RS26a"] == "IZZI"
        assert protocols["RS26e"] == "IZZI"
        assert protocols["A-3-3"] in ("Coe", "Aitken")
        assert set(protocols.values()) <= {"IZZI", "Coe", "Aitken", "unknown"}
