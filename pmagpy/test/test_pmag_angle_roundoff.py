"""Angular comparisons at the endpoints of the inverse-cosine domain."""
import numpy as np
import pytest
from numpy.testing import assert_allclose

from pmagpy import pmag


@pytest.mark.parametrize("direction", [[170.7, 27.3], [47.0, 63.6], [357.0, -47.4]])
@pytest.mark.parametrize("antipodal", [False, True])
def test_angle_parallel_directions(direction, antipodal):
    """Rounded unit-vector dot products must not produce undefined angles."""
    other = [direction[0] + 180, -direction[1]] if antipodal else direction
    result = pmag.angle(direction, other)
    assert result.shape == (1,)
    assert_allclose(result, [180.0 if antipodal else 0.0], atol=2e-6)


def test_angle_batch_with_intensities():
    """Intensity is ignored, including for directions at domain endpoints."""
    directions = [[170.7, 27.3, 1.0], [47.0, 63.6, 3.0], [0.0, 0.0, 2.0]]
    other = [[170.7, 27.3, 5.0], [227.0, -63.6, 4.0], [90.0, 0.0, 1.0]]
    result = pmag.angle(directions, other)
    assert result.shape == (3,)
    assert np.isfinite(result).all()
    assert_allclose(result, [0.0, 180.0, 90.0], atol=2e-6)
