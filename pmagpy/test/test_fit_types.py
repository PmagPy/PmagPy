"""
Tests for the kinds of directional fit of Demag GUI (pmagpy.Fit): the names in
its fit type box and their MagIC method codes.
"""
from pmagpy import pmag
from pmagpy.Fit import PCA_TYPE_CODES, PCA_TYPE_NAMES, Fit


def test_names_and_codes_are_inverse():
    assert len(PCA_TYPE_NAMES) == len(PCA_TYPE_CODES)
    for name, code in PCA_TYPE_CODES.items():
        assert PCA_TYPE_NAMES[code] == name


def test_fit_type_box_order():
    assert list(PCA_TYPE_CODES) == ['line', 'line-anchored', 'line-with-origin',
                                    'vector mean', 'plane', 'Fisher']


def test_every_code_is_a_domean_calculation_type():
    data = [[step, dec, 45., moment, 'g'] for step, dec, moment in
            zip(range(4), [10., 14., 20., 30.], [1.0, 0.7, 0.4, 0.2])]
    for code in PCA_TYPE_NAMES:
        mpars = pmag.domean(data, 0, 3, code)
        assert mpars['calculation_type'] == code
        assert 'specimen_dec' in mpars and 'specimen_inc' in mpars


def test_fit_takes_code_or_keeps_given_type():
    # without a GUI, a Fit keeps the method code that it is given
    for code in PCA_TYPE_NAMES:
        assert Fit('fit', 500, 100, PCA_type=code).PCA_type == code
