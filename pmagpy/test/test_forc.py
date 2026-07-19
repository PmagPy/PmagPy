"""Tests for FORC import, conditioning, and local-regression calculations."""

import numpy as np
from numpy.testing import assert_allclose
from matplotlib.colors import to_rgb

from pmagpy import forc


def quadratic_data():
    """Return noise-free FORCs sampled from a known quadratic surface."""
    fields = []
    moments = []
    curves = []
    sequences = []
    reversal_fields = np.arange(-0.03, 0.031, 0.005)
    for curve_number, reversal in enumerate(reversal_fields):
        field = np.arange(reversal, 0.0401, 0.005)
        hc = (field - reversal) / 2.0
        hu = (field + reversal) / 2.0
        moment = 0.2 + 0.3 * hc + 8.0 * hc**2 - 0.4 * hu - 4.0 * hu**2 + 0.7 * hc * hu
        fields.append(field)
        moments.append(moment)
        curves.append(np.full(field.size, curve_number, dtype=int))
        sequences.append(np.full(field.size, curve_number, dtype=float))
    return forc.ForcData(
        field=np.concatenate(fields),
        moment=np.concatenate(moments),
        curve=np.concatenate(curves),
        reversal_field=reversal_fields,
        sequence=np.concatenate(sequences),
        curve_sequence=np.arange(reversal_fields.size, dtype=float),
        calibration_field=np.array([], dtype=float),
        calibration_moment=np.array([], dtype=float),
        calibration_sequence=np.array([], dtype=float),
        metadata={},
        source="synthetic quadratic",
    )


def test_read_forc_alternating_blocks(tmp_path):
    """MicroMag calibration/FORC pairs are assigned without losing short curves."""
    path = tmp_path / "tiny_FORC"
    path.write_text(
        "MicroMag FORC\n"
        "HCal +100.0E-03\n"
        "NForc 2\n"
        "Field Moment\n"
        "(T) (Am2)\n"
        "+100.0E-03,+10.0E-06\n\n"
        "-10.0E-03,+1.0E-06\n"
        "+0.0E-03,+2.0E-06\n\n"
        "+100.0E-03,+10.1E-06\n\n"
        "-20.0E-03,+0.5E-06\n"
        "-10.0E-03,+1.2E-06\n"
    )
    data = forc.read_forc(path)
    assert data.n_curves == 2
    assert data.moment.size == 4
    assert data.calibration_moment.size == 2
    assert_allclose(data.reversal_field, [-0.01, -0.02])


def test_multiplicative_drift_correction():
    """Calibration scaling recovers moments affected by proportional drift."""
    data = forc.ForcData(
        field=np.array([0.0, 0.01]),
        moment=np.array([2.0, 4.0]),
        curve=np.array([0, 1]),
        reversal_field=np.array([0.0, 0.01]),
        sequence=np.array([0.0, 2.0]),
        curve_sequence=np.array([0.0, 2.0]),
        calibration_field=np.array([0.1, 0.1]),
        calibration_moment=np.array([1.0, 2.0]),
        calibration_sequence=np.array([0.0, 2.0]),
        metadata={},
    )
    corrected = forc.correct_drift(data, smoothing=0)
    assert_allclose(corrected.moment, [2.0, 2.0])

    literal_egli = forc.correct_drift(
        data, method="egli_equation23", smoothing=0
    )
    assert_allclose(literal_egli.moment, [2.0, 8.0])


def test_variweight_transition():
    """Egli weights are flat inside and continuous across the outer step."""
    values = forc.variweight(np.array([0.0, 1.0, 1.5, 2.0, 2.1]), 2.0)
    assert_allclose(values, [1.0, 1.0, 0.5, 0.0, 0.0])


def test_variforc_recovers_quadratic_derivative():
    """VARIFORC exactly recovers rho=(a_hc2-a_hu2)/4 for a quadratic."""
    result = forc.calculate_forc(
        quadratic_data(),
        method="variforc",
        sc0=2,
        sc1=3,
        sb0=2,
        sb1=3,
        lambda_c=0,
        lambda_b=0,
        error_method=None,
    )
    finite = np.isfinite(result.rho)
    assert finite.sum() > 20
    assert_allclose(result.rho[finite], 3.0, atol=1e-9)


def test_harrison_loess_recovers_quadratic_derivative():
    """Nearest-neighbor tricube LOESS recovers the same known quadratic."""
    result = forc.calculate_forc(
        quadratic_data(),
        method="loess",
        smoothing_factor=1,
        error_method=None,
    )
    finite = np.isfinite(result.rho)
    assert finite.sum() > 20
    assert_allclose(result.rho[finite], 3.0, atol=1e-8)


def test_endpoint_drop_preserves_coordinates():
    """Endpoint conditioning masks moments without changing the measurement grid."""
    data = quadratic_data()
    conditioned = forc.adjust_endpoints(data, method="drop", n=1)
    assert_allclose(conditioned.field, data.field)
    assert np.count_nonzero(~np.isfinite(conditioned.moment)) == 2 * data.n_curves


def test_lower_branch_uses_curves_with_field_coverage():
    """Baseline subtraction must not constant-pad short low-reversal FORCs."""
    fields = []
    moments = []
    curves = []
    reversal_fields = np.array([-0.20, -0.15, -0.10, -0.05, 0.00, 0.05])
    maximum_fields = np.array([0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
    for curve_number, (reversal, maximum) in enumerate(
        zip(reversal_fields, maximum_fields)
    ):
        field = np.arange(reversal, maximum + 0.005, 0.01)
        baseline = 2.0 * field + 0.3 * field**2
        fields.append(field)
        moments.append(baseline)
        curves.append(np.full(field.size, curve_number, dtype=int))

    data = forc.ForcData(
        field=np.concatenate(fields),
        moment=np.concatenate(moments),
        curve=np.concatenate(curves),
        reversal_field=reversal_fields,
        sequence=np.concatenate(curves).astype(float),
        curve_sequence=np.arange(reversal_fields.size, dtype=float),
        calibration_field=np.array([], dtype=float),
        calibration_moment=np.array([], dtype=float),
        calibration_sequence=np.array([], dtype=float),
        metadata={},
        source="synthetic coverage test",
    )

    corrected, branch_field, branch_moment = forc.subtract_lower_branch(
        data, n_curves=2, smoothing=0
    )

    interior = (data.field > np.min(data.field)) & (data.field < np.max(data.field))
    assert_allclose(corrected.moment[interior], 0.0, atol=2e-12)
    assert branch_field.shape == branch_moment.shape
    assert corrected.metadata["lower_branch_method"] == "coverage_median"
    assert corrected.metadata["lower_branch_max_support"] == 2


def test_forcme_colormap_is_the_default_palette():
    """PmagPy reproduces the attributed FORCme version-1 color stops."""
    cmap = forc.get_forc_cmap(1)
    assert cmap.name == "forcme_v1"
    assert_allclose(cmap(0.0)[:3], to_rgb("#1f4aa8"), atol=0.01)
    assert_allclose(cmap(0.5)[:3], to_rgb("#ffffff"), atol=0.02)
    assert_allclose(cmap(1.0)[:3], to_rgb("#d100b5"), atol=0.01)


def test_run_forc_pipeline_retains_forcme_stages(tmp_path):
    """The FORCme-style entry point returns auditable PmagPy stages."""
    path = tmp_path / "pipeline_FORC"
    lines = [
        "MicroMag FORC",
        "HCal +100.0E-03",
        "NForc 7",
        "Field Moment",
        "(T) (Am2)",
    ]
    for curve_number, reversal in enumerate(np.linspace(-0.03, 0.0, 7)):
        lines.extend([f"+100.0E-03,{1.0 + curve_number * 0.01:+.8E}", ""])
        for field in np.arange(reversal, 0.031, 0.005):
            moment = 0.2 + field + 0.4 * reversal + 3.0 * field * reversal
            lines.append(f"{field:+.8E},{moment:+.8E}")
        lines.append("")
    path.write_text("\n".join(lines))

    output = forc.run_forc_pipeline(
        path,
        method="loess",
        endpoint_method="none",
        drift_smoothing=0,
        smoothing_factor=1,
        min_points=6,
        error_method=None,
    )

    assert output["raw"].n_curves == 7
    assert output["raw"].calibration_moment.size == 7
    assert output["sample_title"] == "pipeline_FORC"
    assert output["forcs_display"] is output["conditioned"]
    assert output["forcs_rho"] is output["processed"]
    assert output["rho"].shape == output["Hc"].shape == output["Hu"].shape
