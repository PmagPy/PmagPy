"""Repeat-heating check matching in the public paleointensity calculation."""

import copy

import numpy as np
import pandas as pd
import pytest

from pmagpy import pmag


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("check_index", [2, 4])
@pytest.mark.parametrize("matched", [False, True])
def test_pintpars_ignores_checks_without_original_step(version, check_index, matched):
    temperatures = [273, 473, 573, 673, 773, 873]
    first_z = [
        [t, 20.0, 45.0, m, 1]
        for t, m in zip(temperatures, [1.0, 0.92, 0.81, 0.60, 0.41, 0.22])
    ]
    first_i = [
        [t, 0.0, 0.0, m, 1]
        for t, m in zip(temperatures, [0.0, 0.15, 0.30, 0.42, 0.60, 0.75])
    ]
    checks = [[373, 0.0, 0.0, 0.001]]
    if matched:
        checks.append([473, 0.0, 0.0, 0.165])
    arai = [first_z, first_i, [], [], [], []]
    arai[check_index] = checks
    original = copy.deepcopy(arai)
    if version == 3:
        records = pd.DataFrame({
            "method_codes": ["LT-T-Z"] * len(temperatures),
            "treat_temp": temperatures,
        })
        prefix, count_key = "int_", "int_n_ptrm"
    else:
        records = [{"magic_method_codes": "LT-T-Z", "treatment_temp": t}
                   for t in temperatures]
        prefix, count_key = "specimen_", "specimen_int_ptrm_n"
    zijd = [row + ["g"] for row in first_z]
    parameters, error = pmag.PintPars(records, arai, zijd, 0, 5, {}, version=version)

    assert error == 0
    assert parameters[count_key] == int(matched)
    expected = 100 * (0.165 - 0.15) / 0.75 if matched else -1
    np.testing.assert_allclose(parameters[prefix + "drats"], expected)
    if check_index == 2:
        np.testing.assert_allclose(parameters[prefix + "drat"], expected)
    assert arai == original
