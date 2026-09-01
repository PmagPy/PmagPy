"""
Finding, choosing and remembering a MagIC directory.

None of this knows what an application does with the data once it has it, so
both applications share it. Every function takes what it needs as an argument —
the environment prefixes to answer to, the file to keep the recent list in —
rather than reading a module-level configuration, so that two applications can
live in one process without one deciding where the other looks.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from typing import Optional, Sequence


def env(name: str, prefixes: Sequence[str], default: str = "") -> str:
    """Environment setting ``<prefix><name>``, taking the first prefix that is set."""
    for prefix in prefixes:
        value = os.environ.get(prefix + name)
        if value:
            return value
    return default


def looks_like_magic_dir(directory: str) -> bool:
    """A directory a contribution could be read from: it has a measurements table."""
    return os.path.isdir(directory) and os.path.exists(os.path.join(directory, "measurements.txt"))


def default_output_dir(directory: str, base: str = "") -> str:
    """The data directory itself, or ``<base>/<dataset name>`` when a base is given."""
    if base:
        return os.path.join(base, os.path.basename(os.path.abspath(directory).rstrip("/")))
    return directory


def load_recent(path: str) -> list:
    """Recently opened MagIC directories (most recent first) that still exist."""
    try:
        with open(path) as fh:
            return [d for d in json.load(fh) if os.path.isdir(d)]
    except (OSError, ValueError):
        return []


def remember_recent(path: str, directory: str, limit: int = 12) -> list:
    """Put `directory` at the head of the recent list and write it back."""
    directory = os.path.abspath(directory)
    recent = [d for d in load_recent(path) if d != directory]
    recent.insert(0, directory)
    recent = recent[:limit]
    try:
        with open(path, "w") as fh:
            json.dump(recent, fh, indent=1)
    except OSError:
        pass
    return recent


def native_choose_directory(start: Optional[str] = None, prompt: str = "Choose a MagIC directory",
                            stub: str = "") -> Optional[str]:
    """Open the operating system's folder chooser on the machine running the server.

    macOS uses an AppleScript ``choose folder`` dialog shown in the frontmost
    application, Linux uses ``zenity`` when available, Windows the .NET
    FolderBrowserDialog. Returns the chosen absolute path, or None when the
    dialog was cancelled or no chooser is available (remote sessions).

    Args:
        stub: a directory to return instead of showing anything, so that a test
            can answer the dialog from the server side.
    """
    if stub:
        return stub
    start = start if start and os.path.isdir(start) else os.path.expanduser("~")
    try:
        if sys.platform == "darwin":
            script = (
                'tell application (path to frontmost application as text)\n'
                f'  set f to choose folder with prompt "{prompt}" default location POSIX file "{start}"\n'
                "end tell\n"
                "POSIX path of f"
            )
            out = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=600)
            if out.returncode != 0:
                return None
            return out.stdout.strip().rstrip("/") or None
        if sys.platform.startswith("linux"):
            out = subprocess.run(["zenity", "--file-selection", "--directory", f"--title={prompt}",
                                  f"--filename={start}/"], capture_output=True, text=True, timeout=600)
            return out.stdout.strip() or None if out.returncode == 0 else None
        if sys.platform.startswith("win"):
            ps = ("Add-Type -AssemblyName System.Windows.Forms; $d = New-Object System.Windows.Forms.FolderBrowserDialog;"
                  f"$d.Description = '{prompt}'; $d.SelectedPath = '{start}';"
                  "if ($d.ShowDialog() -eq 'OK') { Write-Output $d.SelectedPath }")
            out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=600)
            return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None
    return None


def native_chooser_available(stub: str = "") -> bool:
    """True when a system folder dialog can be shown for this session (local browser)."""
    if stub:
        return True
    try:
        import panel as pn
        req = pn.state.curdoc.session_context.request if pn.state.curdoc else None
        remote_ip = getattr(req, "remote_ip", None) if req else None
        if remote_ip and remote_ip not in ("127.0.0.1", "::1", "localhost"):
            return False
    except Exception:
        pass
    if sys.platform == "darwin":
        return shutil.which("osascript") is not None
    if sys.platform.startswith("linux"):
        return shutil.which("zenity") is not None and bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return sys.platform.startswith("win")
