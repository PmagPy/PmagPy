"""
The one place that knows *how* the family is running.

Everything platform-specific or session-specific lives here and nowhere else:
whether the browser is on the same machine as the server, whether a system
folder dialog can be shown and which one, how to run that dialog without
blocking the server, where the hub is when an application is served under it,
and what the URL asked for. Applications and the rest of the toolkit ask these
questions through the functions below, so that when the family is packaged
into a native window (which brings its own dialogs) or, one day, converted to
run in the browser, this is the only file that changes.

Nothing here knows what a MagIC directory is; :mod:`pmagpy_panel.datasets`
builds on it for that.
"""
from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from typing import Optional

HUB_URL_VAR = "PMAGPY_APPS_URL"       # set by the hub's launcher for the applications it serves


# ----- the session ------------------------------------------------------------

def query_param(name: str, default: str = "") -> str:
    """The value of ``?name=`` on the URL that opened this session, or `default`.

    Empty outside a server session (a notebook, a test), so callers can fall
    back to the environment and then to a built-in default.
    """
    try:
        import panel as pn
        location = pn.state.location
        if location is None or not pn.state.curdoc:
            return default
        value = location.query_params.get(name)
    except Exception:
        return default
    return value if isinstance(value, str) and value else default


def is_local_session() -> bool:
    """True when the browser viewing this session is on the machine running the server.

    Also true outside a server session, so that a script or a test behaves like a
    local user.
    """
    try:
        import panel as pn
        req = pn.state.curdoc.session_context.request if pn.state.curdoc else None
        remote_ip = getattr(req, "remote_ip", None) if req else None
        if remote_ip and remote_ip not in ("127.0.0.1", "::1", "localhost"):
            return False
    except Exception:
        pass
    return True


def hub_url() -> str:
    """Where the hub is, when this application is served under one; empty otherwise."""
    return os.environ.get(HUB_URL_VAR, "")


def open_ui(url: str) -> None:
    """Show the served page to the analyst.

    Today that is a tab in the default browser. A packaged build (HUB_PLAN.md §8)
    will show it in a native window instead — pywebview, whose window also brings
    real file dialogs on every platform — and this is the one call that changes.
    """
    import webbrowser
    webbrowser.open(url)


# ----- the system folder dialog -------------------------------------------------

def _chooser_command(start: str, prompt: str) -> Optional[list]:
    """The command that shows this platform's folder dialog, or None when it has none."""
    if sys.platform == "darwin":
        script = (
            'tell application (path to frontmost application as text)\n'
            f'  set f to choose folder with prompt "{prompt}" default location POSIX file "{start}"\n'
            "end tell\n"
            "POSIX path of f"
        )
        return ["osascript", "-e", script]
    if sys.platform.startswith("linux"):
        return ["zenity", "--file-selection", "--directory", f"--title={prompt}", f"--filename={start}/"]
    if sys.platform.startswith("win"):
        ps = ("Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog;"
              f"$d.Description = '{prompt}'; $d.SelectedPath = '{start}';"
              "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }")
        return ["powershell", "-NoProfile", "-Command", ps]
    return None


def _chosen(returncode: int, stdout: str) -> Optional[str]:
    if returncode != 0:
        return None
    return stdout.strip().rstrip("/") or None


def native_chooser_available(stub: str = "") -> bool:
    """True when a system folder dialog can be shown for this session.

    That needs the browser and the server on one machine, and a dialog program
    on the platform: ``osascript`` on macOS, ``zenity`` under a display on Linux,
    PowerShell on Windows.
    """
    if stub:
        return True
    if not is_local_session():
        return False
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    if sys.platform.startswith("linux"):
        return shutil.which("zenity") is not None and bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return sys.platform.startswith("win")


def native_choose_directory(start: Optional[str] = None, prompt: str = "Choose a MagIC directory",
                            stub: str = "") -> Optional[str]:
    """Show the system folder dialog and wait for it. Returns the chosen path, or None.

    This blocks the calling thread for as long as the dialog is open; from a
    Panel callback use :func:`choose_directory` instead.

    Args:
        stub: a directory to return instead of showing anything, so that a test
            can answer the dialog from the server side.
    """
    if stub:
        return stub
    start = start if start and os.path.isdir(start) else os.path.expanduser("~")
    cmd = _chooser_command(start, prompt)
    if cmd is None:
        return None
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except (OSError, subprocess.SubprocessError):
        return None
    return _chosen(out.returncode, out.stdout)


async def choose_directory(start: Optional[str] = None, prompt: str = "Choose a MagIC directory",
                           stub: str = "") -> Optional[str]:
    """The system folder dialog as a coroutine: the server keeps serving while it is open.

    Use it from an ``async`` widget callback::

        async def _browse(event):
            chosen = await runtime.choose_directory(start)

    Panel runs the callback on its event loop, so the widgets can be updated
    directly when the dialog closes — no thread, no document lock to worry about.
    """
    if stub:
        return stub
    start = start if start and os.path.isdir(start) else os.path.expanduser("~")
    cmd = _chooser_command(start, prompt)
    if cmd is None:
        return None
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE,
                                                    stderr=asyncio.subprocess.PIPE)
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
    except (OSError, asyncio.TimeoutError):
        return None
    return _chosen(proc.returncode or 0, stdout.decode(errors="replace"))
