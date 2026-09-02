"""
Import-cost contracts for the modules the Panel apps start from.

The apps (and every command-line program) pay for whatever ``pmagpy.pmag``
imports at module level, so the heavy optional dependencies must stay lazy:
``SPD.lib.leastsq_jacobian`` (Arai curvature) pulls in ``scipy.optimize`` and
is imported inside ``get_curve``; the ``programs`` package must not resolve
matplotlib's automatic backend (which imports pyplot and probes the GUI
toolkits) just to pin a default for the wx programs.  Each check runs in a
fresh interpreter because the modules under test may already be loaded here.
"""
import os
import subprocess
import sys

import numpy as np
import pytest

import pmagpy.pmag as pmag

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def loaded_after(statement, **env):
    """Run ``statement`` in a fresh interpreter; return the loaded module names."""
    code = f"import sys\n{statement}\nprint('\\n'.join(sorted(sys.modules)))"
    run_env = {k: v for k, v in os.environ.items() if k != "MPLBACKEND"}
    run_env.update(env)
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=run_env,
                         capture_output=True, text=True, check=True)
    return set(out.stdout.split())


def test_pmag_does_not_import_scipy_or_spd():
    modules = loaded_after("import pmagpy.pmag")
    assert "pmagpy.pmag" in modules
    assert not any(m == "scipy" or m.startswith("scipy.") for m in modules)
    assert not any(m == "SPD" or m.startswith("SPD.") for m in modules)


def test_get_curve_still_reaches_the_curvature_code():
    n = 12
    first_Z = [[i, 0, 0, 1.0 - 0.9 * i / n] for i in range(n)]
    first_I = [[i, 0, 0, (0.9 * i / n) ** 1.3] for i in range(n)]
    pars = pmag.get_curve([first_Z, first_I], start=2, end=n - 1)
    assert set(pars) == {"int_k", "int_k_sse", "int_k_prime", "int_k_prime_sse"}
    assert all(np.isfinite(v) for v in pars.values())
    assert pars["int_k"] > 0                                   # concave-up Arai plot


def test_convert_registry_defers_the_ipmag_converters():
    """The field-notebook formats live in ipmag (all of pyplot); the registry must not import it to load."""
    modules = loaded_after("import pmagpy.convert_registry")
    assert "pmagpy.convert_registry" in modules
    assert "pmagpy.ipmag" not in modules and "matplotlib.pyplot" not in modules


def test_programs_package_pins_a_backend_without_importing_pyplot():
    modules = loaded_after("import programs")
    assert "matplotlib" in modules
    assert "matplotlib.pyplot" not in modules


@pytest.mark.parametrize("preset", ["Agg", "WXAgg"])
def test_programs_package_respects_a_preset_backend(preset):
    code = ("import programs, matplotlib\n"
            "print(dict.__getitem__(matplotlib.rcParams, 'backend'))")
    run_env = dict(os.environ, MPLBACKEND=preset)
    out = subprocess.run([sys.executable, "-c", code], cwd=REPO, env=run_env,
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip().lower() == preset.lower()
