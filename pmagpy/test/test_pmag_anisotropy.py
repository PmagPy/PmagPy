"""
Tests for anisotropy tensor functions in pmag.py.

Covers s2a / a2s (tensor format conversion), doseigs (tensor eigenanalysis),
dosgeo (specimen → geographic rotation of tensors), and dostilt (geographic →
tilt-corrected rotation of tensors).
"""
import numpy as np
from numpy.testing import assert_allclose

from pmagpy import pmag


# ---------------------------------------------------------------------------
# s2a / a2s: tensor format conversion
# ---------------------------------------------------------------------------

class TestS2aA2s:
    """Tests for pmag.s2a and pmag.a2s."""

    def test_s2a_docstring_example(self):
        """Verify the s2a docstring example."""
        result = pmag.s2a([1, 2, 3, 4, 5, 6])
        expected = [[1., 4., 6.], [4., 2., 5.], [6., 5., 3.]]
        assert_allclose(result, expected, atol=1e-6)

    def test_a2s_docstring_example(self):
        """Verify the a2s docstring example."""
        result = pmag.a2s([[1, 4, 6], [4, 2, 5], [6, 5, 3]])
        expected = [1., 2., 3., 4., 5., 6.]
        assert_allclose(result, expected, atol=1e-6)

    def test_roundtrip_s2a_a2s(self):
        """a2s(s2a(s)) recovers the original s vector."""
        s = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        recovered = pmag.a2s(pmag.s2a(s))
        assert_allclose(recovered, s, atol=1e-6)

    def test_s2a_is_symmetric(self):
        """s2a produces a symmetric 3x3 matrix."""
        a = pmag.s2a([0.1, 0.2, 0.3, 0.4, 0.5, 0.6])
        assert_allclose(a, a.T, atol=1e-10)

    def test_s2a_shape(self):
        """s2a output is a 3x3 array."""
        a = pmag.s2a([1, 2, 3, 4, 5, 6])
        assert a.shape == (3, 3)


# ---------------------------------------------------------------------------
# doseigs: eigenanalysis of tensor in s-format
# ---------------------------------------------------------------------------

class TestDoseigs:
    """Tests for pmag.doseigs."""

    def test_docstring_example(self):
        """Verify the doseigs docstring example."""
        tau, Vdirs = pmag.doseigs([1, 2, 3, 4, 5, 6])
        assert_allclose(tau, [2.021399, -0.33896524, -0.6824337], atol=1e-4)
        assert len(Vdirs) == 3
        assert len(Vdirs[0]) == 2  # [dec, inc] pairs

    def test_eigenvalues_sorted_descending(self):
        """Eigenvalues are returned in descending order."""
        tau, _ = pmag.doseigs([0.335, 0.328, 0.337, 0.006, 0.004, -0.001])
        assert tau[0] >= tau[1] >= tau[2]

    def test_eigenvectors_lower_hemisphere(self):
        """All eigenvector inclinations are in the lower hemisphere (>= 0)."""
        _, Vdirs = pmag.doseigs([0.335, 0.328, 0.337, 0.006, 0.004, -0.001])
        for i, vdir in enumerate(Vdirs):
            assert vdir[1] >= 0, f"V{i+1} inclination is negative: {vdir[1]}"

    def test_eigenvalues_sum_to_one(self):
        """Normalized eigenvalues sum to 1.0."""
        tau, _ = pmag.doseigs([0.335, 0.328, 0.337, 0.006, 0.004, -0.001])
        assert_allclose(sum(tau), 1.0, atol=1e-4)

    def test_roundtrip_with_doeigs_s(self):
        """doeigs_s(doseigs(s)) approximately recovers the original tensor."""
        s_orig = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        tau, Vdirs = pmag.doseigs(s_orig)
        s_recovered = pmag.doeigs_s(tau, Vdirs)
        assert_allclose(s_recovered, s_orig, atol=0.01)


# ---------------------------------------------------------------------------
# dosgeo: rotate tensor to geographic coordinates
# ---------------------------------------------------------------------------

class TestDosgeo:
    """Tests for pmag.dosgeo."""

    def test_docstring_example(self):
        """Verify the dosgeo docstring example."""
        s = [0.33586472, 0.32757074, 0.33656454, 0.0056526, 0.00449771, -0.00036542]
        result = pmag.dosgeo(s, 12, 33)
        expected = [0.33509237, 0.3288845, 0.33602312,
                    0.0038898108, 0.0066036563, -0.0018823999]
        assert_allclose(result, expected, atol=1e-4)

    def test_identity_rotation(self):
        """az=0, pl=0 leaves tensor unchanged."""
        s = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        result = pmag.dosgeo(s, 0, 0)
        assert_allclose(result, s, atol=1e-4)

    def test_trace_preserved(self):
        """Rotation preserves the trace (sum of diagonal elements)."""
        s = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        trace_orig = s[0] + s[1] + s[2]
        result = pmag.dosgeo(s, 45, 20)
        trace_rot = result[0] + result[1] + result[2]
        assert_allclose(trace_rot, trace_orig, atol=1e-4)


# ---------------------------------------------------------------------------
# dostilt: rotate tensor to stratigraphic (tilt-corrected) coordinates
# ---------------------------------------------------------------------------

class TestDostilt:
    """Tests for pmag.dostilt."""

    def test_docstring_example(self):
        """Verify the dostilt docstring example."""
        s = [0.33586472, 0.32757074, 0.33656454, 0.0056526, 0.00449771, -0.00036542]
        result = pmag.dostilt(s, 20, 38)
        expected = [0.33473614, 0.32911453, 0.33614933,
                    0.0075679934, 0.0020322995, -0.0014457355]
        assert_allclose(result, expected, atol=1e-4)

    def test_zero_dip_no_change(self):
        """Horizontal bedding (dip=0) leaves tensor unchanged."""
        s = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        result = pmag.dostilt(s, 90, 0)
        assert_allclose(result, s, atol=1e-4)

    def test_trace_preserved(self):
        """Tilt correction preserves the trace."""
        s = [0.335, 0.328, 0.337, 0.006, 0.004, -0.001]
        trace_orig = s[0] + s[1] + s[2]
        result = pmag.dostilt(s, 45, 30)
        trace_rot = result[0] + result[1] + result[2]
        assert_allclose(trace_rot, trace_orig, atol=1e-4)
