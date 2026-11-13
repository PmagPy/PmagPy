"""pTRM checks acquired after the interpreted temperature range are excluded."""
import numpy as np
import pandas as pd
import pytest

from pmagpy import pmag


@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("check_index, check_method", [(2, "LT-PTRM-I"), (4, "LT-PTRM-Z")])
@pytest.mark.parametrize("case", ["inside", "mixed", "consecutive"])
def test_pintpars_check_acquisition_range(version, check_index, check_method, case):
    temperatures = [273, 473, 573, 673, 773, 873]
    first_z = [
        [t, 20., 45., m, 1]
        for t, m in zip(temperatures, [1., .92, .81, .60, .41, .22])
    ]
    first_i = [
        [t, 0., 0., m, 1]
        for t, m in zip(temperatures, [0., .15, .30, .42, .60, .75])
    ]
    meth_key = "method_codes" if version == 3 else "magic_method_codes"
    temp_key = "treat_temp" if version == 3 else "treatment_temp"
    records = [{meth_key: "LT-T-Z", temp_key: t} for t in temperatures]
    checks = [[473, 0., 0., .165]]
    if case == "consecutive":
        # Both checks follow the 873 K heating, outside the 773 K fit.
        # The second check's immediately previous temperature is only 473 K.
        records.extend([{meth_key: check_method, temp_key: 473},
                        {meth_key: check_method, temp_key: 573}])
        checks.append([573, 0., 0., .345])
        count, expected = 0, 0.
    else:
        records.insert(4, {meth_key: check_method, temp_key: 473})
        if case == "mixed":
            records.append({meth_key: check_method, temp_key: 573})
            checks.append([573, 0., 0., .345])
        count, expected = 1, 100 * (.165 - .15) / .60
    arai = [first_z, first_i, [], [], [], []]
    arai[check_index] = checks
    data = pd.DataFrame(records) if version == 3 else records
    pars, error = pmag.PintPars(data, arai, [r + ["g"] for r in first_z],
                                0, 4, {}, version=version)

    assert error == 0
    prefix = "int_" if version == 3 else "specimen_"
    n_key = "int_n_ptrm" if version == 3 else "specimen_int_ptrm_n"
    assert pars[n_key] == count
    np.testing.assert_allclose(pars[prefix + "drats"], expected)
    if check_index == 2:
        np.testing.assert_allclose(pars[prefix + "drat"], expected)
