"""
Shared pytest fixtures for PmagPy tests.

conftest.py is automatically discovered by pytest — any fixture defined here
is available to all test files in this directory without explicit import.
"""
import random

import matplotlib
import numpy as np
import pytest


@pytest.fixture(autouse=True, scope="session")
def agg_backend():
    """
    Force matplotlib to use the non-interactive Agg backend.

    This prevents tests from trying to open GUI windows, which would
    fail in CI and slow down local runs. Session-scoped so it runs
    once at the start of the test session.
    """
    matplotlib.use("Agg")


@pytest.fixture
def seed():
    """
    Set fixed random seeds for reproducible stochastic tests.

    Use this fixture in any test that calls random or Monte Carlo
    functions (fishrot, bootstrap, etc.) so results are deterministic.

    Usage:
        def test_something(seed):
            result = ipmag.fishrot(k=20, n=10)
            ...
    """
    np.random.seed(0)
    random.seed(0)
