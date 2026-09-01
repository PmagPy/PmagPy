"""
Clean-environment checks for the paleointensity core (PmagPy/PmagPy#769).

Issue #769 was a chain of installation problems, of which the visible one was
``ModuleNotFoundError: No module named 'past'`` raised from ``SPD/spd.py``
while merely importing ``pmagpy``. The tests here guard the property that
matters: the new core must import and run with nothing beyond what
``setup.py`` declares, in a fresh interpreter, and must not drag in the legacy
Data Model 2 or SPD machinery to do it.

They are deliberately cheap -- a subprocess import and a source scan -- so
they can run in CI on every platform rather than only where a full
installation can be built.
"""
import ast
import os
import subprocess
import sys
import textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

#: everything the new paleointensity work adds to pmagpy
NEW_MODULES = ("pmagpy.magic_project", "pmagpy.pint_stats", "pmagpy.paleointensity",
               "pmagpy.tdt", "pmagpy.bicep")
#: what setup.py promises will be installed alongside
DECLARED = {"numpy", "scipy", "matplotlib", "pandas", "pytz", "packaging"}
#: the standard library and pmagpy's own packages are always fair game
OURS = {"pmagpy", "pmag_env", "SPD", "programs", "dialogs", "locator"}


def _run(code: str, env=None):
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONPATH"] = REPO
    if env:
        environment.update(env)
    return subprocess.run([sys.executable, "-c", textwrap.dedent(code)], cwd=REPO,
                          env=environment, capture_output=True, text=True, timeout=600)


class TestCleanImport:
    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_the_module_imports_in_a_fresh_interpreter(self, module):
        result = _run(f"import {module} as m; print(m.__name__)")
        assert result.returncode == 0, result.stderr[-2000:]
        assert module in result.stdout

    def test_importing_the_core_needs_no_undeclared_third_party_package(self):
        """Nothing outside ``setup.py`` may be *required* to import and use the core.

        Merely appearing in ``sys.modules`` does not prove a dependency: pandas
        reaches for ``pyarrow`` when it happens to be installed, and pmagpy's own
        ``pmag_env.set_env`` asks IPython whether it is running in a notebook.
        Both are optional, and a clean install has neither. So the undeclared
        packages an installed environment does pull in are discovered first, then
        blocked at the meta-path, and the core has to import and compute without
        them. Whatever is genuinely required will fail here and be named.
        """
        result = _run("""
            import sys, json
            before = set(sys.modules)
            import pmagpy.paleointensity, pmagpy.pint_stats, pmagpy.tdt, pmagpy.bicep
            after = set(sys.modules) - before
            tops = sorted({name.split('.')[0] for name in after})
            print(json.dumps(tops))
        """)
        assert result.returncode == 0, result.stderr[-2000:]
        import json
        tops = json.loads(result.stdout.strip().splitlines()[-1])
        stdlib = set(sys.stdlib_module_names)
        # numpy, pandas and matplotlib are declared, and these arrive with them;
        # blocking one would only prove that pandas needs its own dependencies
        needed_by_declared = {"dateutil", "six", "pyparsing", "cycler", "kiwisolver",
                              "PIL", "fontTools", "zoneinfo", "certifi", "pytz",
                              "pytz_deprecation_shim", "tzdata"}
        candidates = sorted(name for name in tops
                            if name not in stdlib and name not in DECLARED
                            and name not in OURS and name not in needed_by_declared
                            and not name.startswith("_") and "mypyc" not in name
                            and name != "cython_runtime")
        result = _run("""
            import sys, json
            BLOCK = set(json.loads({blocked!r}))
            class Blocker:
                def find_module(self, name, path=None):
                    return self if name.split('.')[0] in BLOCK else None
                def load_module(self, name):
                    raise ImportError(name + ' is not installed')
            sys.meta_path.insert(0, Blocker())
            from pmagpy import paleointensity as pint
            data = pint.PintData.from_directory('data_files/thellier_magic')
            name = data.specimen_names[0]
            data.set_interpretation(name, 0, 5)
            print('B', round(data.result(name).b_anc_uncorrected, 3))
        """.format(blocked=json.dumps(candidates)))
        assert result.returncode == 0, (
            f"the core needs one of {candidates}:\n{result.stderr[-2000:]}")
        assert "\nB " in "\n" + result.stdout


    def test_the_core_does_not_need_the_legacy_spd_package(self):
        """SPD is python-2 era code; #769's traceback came from importing it."""
        result = _run("""
            import sys
            class Blocker:
                def find_module(self, name, path=None):
                    return self if name.split('.')[0] in ('past', 'future') else None
                def load_module(self, name):
                    raise ImportError(name + ' is not installed')
            sys.meta_path.insert(0, Blocker())
            import pmagpy.paleointensity, pmagpy.pint_stats, pmagpy.tdt, pmagpy.bicep
            print('ok')
        """)
        assert result.returncode == 0, result.stderr[-2000:]
        assert "ok" in result.stdout

    def test_an_analysis_runs_end_to_end_in_a_fresh_interpreter(self):
        result = _run("""
            from pmagpy import paleointensity as pint
            data = pint.PintData.from_directory('data_files/thellier_magic')
            name = data.specimen_names[0]
            data.set_interpretation(name, 0, 5)
            result = data.result(name)
            print('B', round(result.b_anc_uncorrected, 3))
        """)
        assert result.returncode == 0, result.stderr[-2000:]
        assert "\nB " in "\n" + result.stdout

    def test_matplotlib_is_only_needed_for_figures(self):
        """A headless run must not require a display backend to analyse data."""
        result = _run("""
            from pmagpy import paleointensity as pint, pint_stats as ps
            import numpy as np
            exp = ps.Experiment(x=np.linspace(0, 1, 6), y=np.linspace(1, 0, 6),
                                temps=np.linspace(293, 873, 6),
                                nrm_vectors=np.column_stack([np.zeros(6), np.zeros(6),
                                                             np.linspace(1, 0, 6)]),
                                blab=40.0, blab_orient=np.array([0., 0., -1.]))
            print(round(float(ps.arai_statistics(exp, 0, 5)['B_anc']), 2))
        """, env={"MPLBACKEND": "module://nonexistent"})
        assert result.returncode == 0, result.stderr[-2000:]


class TestNoLegacyDependency:
    """PmagPy/PmagPy#789: the new core must never reach the Data Model 2 helpers."""

    FORBIDDEN_IMPORTS = ("builder2", "validate_upload2", "controlled_vocabularies2",
                         "convert_2_magic2", "map_magic", "SPD")
    FORBIDDEN_CALLS = ("upload_magic2", "chi_magic2", "hysteresis_magic2", "ani_depthplot2",
                       "aarm_magic_dm2", "atrm_magic_dm2", "magic_read_dict")

    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_no_data_model_2_import(self, module):
        path = os.path.join(REPO, *module.split(".")) + ".py"
        tree = ast.parse(open(path, encoding="utf-8").read())
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                names.add(node.module)
        for banned in self.FORBIDDEN_IMPORTS:
            assert not any(banned in name for name in names), f"{module} imports {banned}"

    @pytest.mark.parametrize("module", NEW_MODULES)
    def test_no_data_model_2_call(self, module):
        path = os.path.join(REPO, *module.split(".")) + ".py"
        tree = ast.parse(open(path, encoding="utf-8").read())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Attribute):
                    called.add(func.attr)
                elif isinstance(func, ast.Name):
                    called.add(func.id)
        for banned in self.FORBIDDEN_CALLS:
            assert banned not in called, f"{module} calls {banned}"

    def test_the_application_is_free_of_them_too(self):
        app = os.path.join(REPO, "programs", "pmagpy_intensity")
        for name in sorted(os.listdir(app)):
            if not name.endswith(".py"):
                continue
            text = open(os.path.join(app, name), encoding="utf-8").read()
            for banned in self.FORBIDDEN_IMPORTS + self.FORBIDDEN_CALLS:
                assert f"import {banned}" not in text, f"{name} imports {banned}"


class TestPackaging:
    def test_the_cli_pins_the_matching_library_version(self):
        """PmagPy/PmagPy#904: pmagpy-cli must not resolve a different pmagpy."""
        import re
        setup = open(os.path.join(REPO, "command_line_setup.py"), encoding="utf-8").read()
        assert "shared_version_requirement" in setup
        assert re.search(r"pmagpy==\{version_num\}", setup)

    def test_the_application_is_not_shipped_in_the_library_package(self):
        """The Panel apps need panel and bokeh; the library must not."""
        setup = open(os.path.join(REPO, "setup.py"), encoding="utf-8").read()
        assert "panel" not in setup.split("install_requires")[1].split("]")[0]
        assert "programs" in setup            # excluded from the package list

    def test_the_new_core_is_inside_the_library_package(self):
        """The science ships with pmagpy, so scripts and notebooks get it."""
        from setuptools import find_packages
        packages = find_packages(where=REPO)
        assert "pmagpy" in packages
        for module in NEW_MODULES:
            assert os.path.exists(os.path.join(REPO, *module.split(".")) + ".py")
