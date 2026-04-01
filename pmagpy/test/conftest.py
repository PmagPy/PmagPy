"""
Shared pytest fixtures for PmagPy tests.

conftest.py is automatically discovered by pytest — any fixture defined here
is available to all test files in this directory without explicit import.
"""
import matplotlib
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
