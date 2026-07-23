"""Tests for FORC grid smoothing and distribution calculation."""

import numpy as np
from numpy.testing import assert_allclose
import pytest

from pmagpy import forc


def quadratic_grid(size=25):
    """Return a triangular grid sampled from a known quadratic surface."""
    Hb_vals = np.linspace(-0.03, 0.03, size)
    Ha_vals = np.linspace(-0.03, 0.03, size)
    Hb, Ha = np.meshgrid(Hb_vals, Ha_vals, indexing="ij")
    M = (
        0.2
        + 0.3 * Ha
        - 0.4 * Hb
        + 8.0 * Ha ** 2
        + 0.7 * Ha * Hb
        - 4.0 * Hb ** 2
    )
    M[Ha < Hb] = np.nan
    return Hb_vals, Ha_vals, M


def test_loess_rho_recovers_quadratic_mixed_derivative():
    """Local quadratic fits recover an exactly known FORC distribution."""
    Hb_vals, Ha_vals, M = quadratic_grid()
    rho = forc.loess_rho_from_grid_fast(
        Hb_vals,
        Ha_vals,
        M,
        span_Ha_T=0.01,
        span_Hb_T=0.01,
        min_pts=10,
    )

    finite = np.isfinite(rho)
    assert finite.sum() > 200
    # rho = -0.5 * d2M/(dHa dHb), and the mixed coefficient is 0.7.
    assert_allclose(rho[finite], -0.35, rtol=0.0, atol=3e-10)


def test_loess_rho_is_independent_of_chunk_size_with_missing_data():
    """Chunking bounds memory without changing sparse-grid results."""
    Hb_vals, Ha_vals, M = quadratic_grid(size=31)
    M[::4, 2::5] = np.nan
    original = M.copy()

    small_chunks = forc.loess_rho_from_grid_fast(
        Hb_vals,
        Ha_vals,
        M,
        span_Ha_T=0.008,
        span_Hb_T=0.008,
        min_pts=10,
        chunk_size=7,
    )
    large_chunks = forc.loess_rho_from_grid_fast(
        Hb_vals,
        Ha_vals,
        M,
        span_Ha_T=0.008,
        span_Hb_T=0.008,
        min_pts=10,
        chunk_size=256,
    )

    # Batched einsum accumulation order varies slightly across NumPy versions.
    assert_allclose(small_chunks, large_chunks, rtol=1e-9, atol=1e-10)
    assert_allclose(M, original)
    assert np.isnan(small_chunks[~np.isfinite(M)]).all()
    assert np.isfinite(small_chunks).sum() > 200


def test_loess_rho_supports_irregular_field_spacing_and_validates_shape():
    """Measured irregular grids work, while malformed inputs fail early."""
    Hb_vals, Ha_vals, M = quadratic_grid(size=9)

    with pytest.raises(ValueError, match="M_grid shape"):
        forc.loess_rho_from_grid_fast(Hb_vals, Ha_vals, M[:-1])

    irregular_Ha = Ha_vals.copy()
    irregular_Ha[4] += 0.0001
    Hb, Ha = np.meshgrid(Hb_vals, irregular_Ha, indexing="ij")
    irregular_M = (
        0.2
        + 0.3 * Ha
        - 0.4 * Hb
        + 8.0 * Ha ** 2
        + 0.7 * Ha * Hb
        - 4.0 * Hb ** 2
    )
    irregular_M[Ha < Hb] = np.nan
    rho = forc.loess_rho_from_grid_fast(
        Hb_vals,
        irregular_Ha,
        irregular_M,
        span_Ha_T=0.02,
        span_Hb_T=0.02,
        min_pts=8,
    )
    assert_allclose(rho[np.isfinite(rho)], -0.35, rtol=0.0, atol=3e-10)

    descending_Ha = irregular_Ha.copy()
    descending_Ha[4] = descending_Ha[3] - 0.001
    with pytest.raises(ValueError, match="strictly increasing"):
        forc.loess_rho_from_grid_fast(Hb_vals, descending_Ha, irregular_M)

    with pytest.raises(ValueError, match="chunk_size"):
        forc.loess_rho_from_grid_fast(
            Hb_vals,
            Ha_vals,
            M,
            chunk_size=0,
        )
