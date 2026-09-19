"""
Tests for matplotlib backend selection by the command-line programs.

Modules under programs/ used to call matplotlib.use("TKAgg") (or "WXAgg") at
import time whenever the backend was not already that GUI backend. Importing
one of them from a notebook therefore replaced the inline backend and figures
stopped appearing (issue #909). They now go through
set_env.set_backend_if_unset, which only picks a backend when nothing else has.

The one backend it does override is an inline backend inherited from a parent
Jupyter kernel through MPLBACKEND (the ``!eqarea.py ...`` pattern in notebook
cells): outside IPython nothing can display it, so the program's GUI backend
is used instead.
"""
import importlib
import importlib.util
import os
import queue
import subprocess
import sys

import matplotlib
import pytest

from pmag_env import set_env


class TestSetBackendIfUnset:
    """Unit tests for set_env.set_backend_if_unset."""

    def test_respects_backend_already_chosen(self, monkeypatch):
        """A backend chosen earlier (here Agg, from conftest) is left alone."""
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        assert set_env.backend_already_chosen()
        assert set_env.set_backend_if_unset("TKAgg") is False
        assert calls == []

    def test_sets_preferred_when_nothing_chosen(self, monkeypatch):
        """With no backend chosen yet, the preferred GUI backend is requested."""
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(set_env, "chosen_backend", lambda: None)
        monkeypatch.setattr(set_env, "IS_NOTEBOOK", False)
        assert set_env.set_backend_if_unset("WXAgg") is True
        assert calls == [("WXAgg",)]

    def test_never_changes_backend_in_notebook(self, monkeypatch):
        """Inside a notebook the backend is never touched, whatever its state."""
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(set_env, "chosen_backend", lambda: None)
        monkeypatch.setattr(set_env, "IS_NOTEBOOK", True)
        assert set_env.set_backend_if_unset("TKAgg") is False
        assert calls == []

    def test_chosen_backend_reports_resolved_backend(self):
        """Once pyplot is in use the resolved backend name is reported."""
        assert set_env.chosen_backend().lower() == "agg"

    def test_replaces_inline_backend_inherited_outside_ipython(self, monkeypatch):
        """A kernel's inline backend leaking into a plain subprocess is replaced.

        ipykernel exports MPLBACKEND=module://matplotlib_inline.backend_inline
        and every ``!program.py`` subprocess inherits it. Without IPython in
        the process that backend cannot show anything, so the program gets
        its GUI backend as it always did.
        """
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(set_env, "chosen_backend",
                            lambda: "module://matplotlib_inline.backend_inline")
        monkeypatch.setattr(set_env, "IS_NOTEBOOK", False)
        monkeypatch.setattr(set_env, "IN_IPYTHON", False)
        assert set_env.set_backend_if_unset("TKAgg") is True
        assert calls == [("TKAgg",)]

    def test_keeps_inline_backend_in_unrecognised_ipython_shell(self, monkeypatch):
        """Inline stays when IPython is running but the shell class is unknown.

        Some notebook front ends subclass the kernel shell under another name
        (issue #781), so IS_NOTEBOOK is False although the inline backend
        can render. Never override it while IPython is in the process.
        """
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(set_env, "chosen_backend",
                            lambda: "module://matplotlib_inline.backend_inline")
        monkeypatch.setattr(set_env, "IS_NOTEBOOK", False)
        monkeypatch.setattr(set_env, "IN_IPYTHON", True)
        assert set_env.set_backend_if_unset("TKAgg") is False
        assert calls == []

    def test_keeps_non_inline_backend_outside_ipython(self, monkeypatch):
        """MPLBACKEND=Agg (or any non-inline choice) is still respected."""
        calls = []
        monkeypatch.setattr(matplotlib, "use", lambda *a, **k: calls.append(a))
        monkeypatch.setattr(set_env, "chosen_backend", lambda: "agg")
        monkeypatch.setattr(set_env, "IS_NOTEBOOK", False)
        monkeypatch.setattr(set_env, "IN_IPYTHON", False)
        assert set_env.set_backend_if_unset("TKAgg") is False
        assert calls == []

    @pytest.mark.parametrize("name, expected", [
        ("module://matplotlib_inline.backend_inline", True),
        ("module://ipykernel.pylab.backend_inline", True),
        ("agg", False),
        ("TkAgg", False),
        ("module://ipympl.backend_nbagg", False),
        (None, False),
    ])
    def test_is_inline_backend(self, name, expected):
        assert set_env.is_inline_backend(name) is expected


class TestProgramImports:
    """Importing programs.* must not clobber a backend that is already set."""

    @pytest.mark.parametrize("module", [
        "programs.common_mean",
        "programs.eqarea",
        "programs.di_rot",
        "programs.fishqq",
        "programs.histplot",
        "programs.zeq_magic",
        "programs.conversion_scripts.cit_magic",  # package init imports tdt_magic
        "programs.core_depthplot",  # asks for WXAgg
    ])
    def test_import_keeps_current_backend(self, module):
        """The Agg backend from conftest survives importing a program module."""
        before = matplotlib.get_backend()
        assert before.lower() == "agg", "test assumes conftest set Agg"
        try:
            importlib.import_module(module)
        except ImportError as err:
            # core_depthplot needs wxPython, which not every test env has
            pytest.skip(f"{module} not importable here: {err}")
        assert matplotlib.get_backend() == before

    def test_no_module_level_backend_forcing_remains(self):
        """Guard against import-time matplotlib.use() creeping back into programs/.

        The wxPython GUIs embed matplotlib canvases in wx windows and must run
        on WXAgg, so they are allowed to force it; everything else goes through
        set_env.set_backend_if_unset.
        """
        import pathlib
        programs_dir = pathlib.Path(set_env.__file__).resolve().parents[1] / "programs"
        allowed = {"demag_gui.py", "magic_gui.py", "pmag_gui.py", "thellier_gui.py"}
        offenders = []
        for path in programs_dir.rglob("*.py"):
            if path.name in allowed:
                continue
            for line in path.read_text(errors="ignore").splitlines():
                stripped = line.strip()
                if stripped.startswith("#") or line[:1] in (" ", "\t"):
                    # comments and indented lines (inside functions or
                    # ``if __name__ == "__main__"`` blocks) do not run on import
                    continue
                if (line.startswith(("matplotlib.use(", "mpl.use("))
                        or "get_backend() !=" in stripped):
                    offenders.append(f"{path.relative_to(programs_dir)}: {stripped}")
        assert offenders == []


class TestSubprocessInheritingInlineBackend:
    """A program started from a notebook cell with ``!`` must still get a GUI backend.

    The kernel exports MPLBACKEND=module://matplotlib_inline.backend_inline
    to its children. This reproduces that child process directly.
    """

    INLINE = "module://matplotlib_inline.backend_inline"

    def _run(self, code, mplbackend):
        repo_root = str(__import__("pathlib").Path(set_env.__file__).resolve().parents[1])
        env = dict(os.environ, MPLBACKEND=mplbackend)
        env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
        result = subprocess.run([sys.executable, "-c", code], env=env,
                                capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr
        return result.stdout.strip().splitlines()[-1]

    def test_program_replaces_inherited_inline_backend(self):
        """Importing a program in a plain process discards the inline backend."""
        backend = self._run("import matplotlib, programs.common_mean\n"
                            "print(matplotlib.get_backend())", self.INLINE)
        assert backend.lower() == "tkagg", backend

    def test_program_keeps_inherited_agg_backend(self):
        """A non-inline MPLBACKEND, e.g. Agg on a server, is still respected."""
        backend = self._run("import matplotlib, programs.common_mean\n"
                            "print(matplotlib.get_backend())", "Agg")
        assert backend.lower() == "agg", backend


def _run_in_fresh_kernel(code, timeout=90):
    """Execute code in a new ipykernel and return (stdout, n_display_data)."""
    jupyter_client = pytest.importorskip("jupyter_client")
    pytest.importorskip("ipykernel")
    from jupyter_client.manager import KernelManager

    km = KernelManager(kernel_name="python3")
    # launch the kernel with the interpreter running the tests so pmagpy and
    # its dependencies resolve the same way they do here
    km.kernel_cmd = [sys.executable, "-m", "ipykernel_launcher",
                     "-f", "{connection_file}"]
    try:
        km.start_kernel()
    except Exception as err:  # pragma: no cover - environment-dependent
        pytest.skip(f"could not start an ipykernel: {err}")
    kc = km.client()
    kc.start_channels()
    stdout, n_display = [], 0
    try:
        kc.wait_for_ready(timeout=timeout)
        kc.execute(code)
        while True:
            try:
                msg = kc.get_iopub_msg(timeout=timeout)
            except queue.Empty:
                pytest.fail("kernel did not finish executing the test cell")
            kind = msg["msg_type"]
            if kind == "stream":
                stdout.append(msg["content"]["text"])
            elif kind == "error":
                pytest.fail("\n".join(msg["content"]["traceback"]))
            elif kind == "display_data":
                n_display += 1
            elif kind == "status" and msg["content"]["execution_state"] == "idle":
                break
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)
    return "".join(stdout), n_display


class TestNotebookInlinePlotting:
    """End-to-end reproduction of issue #909 inside a real Jupyter kernel."""

    def test_importing_program_keeps_inline_backend(self):
        """Importing a programs module in a kernel leaves inline plotting working."""
        repo_root = str(__import__("pathlib").Path(set_env.__file__).resolve().parents[1])
        # programs/conversion_scripts/__init__.py imports tdt_magic eagerly and
        # tdt_magic needs wxPython, which CI does not install; the kernel runs
        # on this same interpreter so check here
        conversion_import = ("from programs.conversion_scripts import cit_magic"
                             if importlib.util.find_spec("wx") else "")
        code = f"""
import subprocess, sys
sys.path.insert(0, {repo_root!r})
import matplotlib
from pmag_env import set_env
print("IS_NOTEBOOK", set_env.IS_NOTEBOOK)
before = matplotlib.get_backend()
import programs.common_mean
import programs.eqarea_magic
{conversion_import}
after = matplotlib.get_backend()
print("BACKEND", before, after)
# what a ``!eqarea.py ...`` cell does: a child process inheriting MPLBACKEND
child = subprocess.run([sys.executable, "-c",
                        "import sys; sys.path.insert(0, {repo_root!r}); "
                        "import matplotlib, programs.common_mean; "
                        "print(matplotlib.get_backend())"],
                       capture_output=True, text=True)
print("CHILD", child.stdout.strip() or child.stderr.strip().replace(chr(10), " | "))
import matplotlib.pyplot as plt
fig = plt.figure()
plt.plot([0, 1], [0, 1])
plt.show()
"""
        stdout, n_display = _run_in_fresh_kernel(code)
        lines = dict(line.split(" ", 1) for line in stdout.strip().splitlines()
                     if " " in line)
        assert lines["IS_NOTEBOOK"] == "True", stdout
        before, after = lines["BACKEND"].split()
        assert "inline" in before.lower(), stdout
        assert after == before, f"import changed backend {before} -> {after}"
        assert lines["CHILD"].lower() == "tkagg", (
            f"subprocess from the kernel should get the GUI backend, got {lines['CHILD']!r}")
        assert n_display == 1, f"expected one inline figure, got {n_display}"
