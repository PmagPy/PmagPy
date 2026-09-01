"""
One-command launcher for the PmagPy Panel applications.

What it does, for whichever application (or set of them) is passed to it:
* stops a server already listening on the port (so you never have to hunt down
  and kill the old one),
* starts ``panel serve`` in *dev* mode, which reloads the app whenever its
  source changes — after an edit just refresh the browser tab,
* waits until the app answers before opening a browser, so the tab is never
  blank while the first dataset is read.

One application on its own is served at ``/<its name>``; several together are
served side by side on one port, with the first of them as the site's index
page, and every application is told where that index is (``PMAGPY_APPS_URL``)
so it can show the way back. That is how the hub runs the family.

Note that Panel's ``--dev`` reload does **not** push an edited ``_esm`` string
to the browser: change one of the components in ``widgets.py`` and the server
must be restarted, or the old JavaScript keeps running.

An application wraps this with its own file, environment prefix and port; see
``programs/pmagpy_directions/launch.py``.
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from typing import Sequence, Union

from .runtime import HUB_URL_VAR, open_ui


def pids_on_port(port: int) -> list[int]:
    """PIDs listening on a TCP port (macOS/Linux via lsof; empty elsewhere)."""
    try:
        out = subprocess.run(["lsof", "-ti", f"tcp:{port}", "-sTCP:LISTEN"], capture_output=True, text=True)
    except OSError:
        return []
    return [int(p) for p in out.stdout.split() if p.strip().isdigit()]


def stop_previous(port: int) -> int:
    pids = pids_on_port(port)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
    if pids:
        time.sleep(1.5)
    return len(pids)


def _app_name(app_file: str) -> str:
    return os.path.splitext(os.path.basename(app_file))[0]


def _working_dir(app_file: str) -> str:
    """The checkout's root when the application runs from one (pmagpy finds its data files
    relative to the working directory), otherwise wherever the launcher was started."""
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(app_file))))
    return repo if os.path.isfile(os.path.join(repo, "pmagpy", "pmag.py")) else os.getcwd()


def serve_command(app_files: Sequence[str], port: int, dev: bool = True, index: bool = False) -> list[str]:
    """The ``panel serve`` command line for these applications on this port."""
    import socket
    hosts = ["localhost", "127.0.0.1", socket.gethostname(), socket.gethostname().split(".")[0] + ".local"]
    origins = [arg for h in dict.fromkeys(hosts) for arg in ("--allow-websocket-origin", f"{h}:{port}")]
    cmd = [sys.executable, "-m", "panel", "serve", *app_files, "--port", str(port), *origins]
    # each application's assets/ (favicon) at /<app>_assets, so that several on one port do not collide
    assets = [f"{_app_name(f)}_assets={os.path.join(os.path.dirname(os.path.abspath(f)), 'assets')}"
              for f in app_files if os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(f)), "assets"))]
    if assets:
        cmd += ["--static-dirs", *assets]
    if index:
        cmd += ["--index", _app_name(app_files[0])]
    if dev:
        cmd.append("--dev")
    return cmd


def main(app_files: Union[str, Sequence[str]], env_prefix: str, default_port: int, argv=None,
         index: bool = False) -> int:
    """Serve the application(s), reading settings from ``<env_prefix>PORT/DIR/OUTPUT``.

    Args:
        app_files: one served file, or several — the first is the one opened in
            the browser and, with `index`, the site's front page.
        env_prefix: the environment prefix the first application answers to; the
            ``--dir`` and ``--output`` options are passed on under it.
        default_port: used unless ``<env_prefix>PORT`` or ``--port`` says otherwise.
        index: serve the first application at ``/`` as well as at its own path,
            and tell the others where it is.
    """
    app_files = [app_files] if isinstance(app_files, str) else list(app_files)
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    port_default = os.environ.get(env_prefix + "PORT") or default_port
    ap.add_argument("--port", type=int, default=int(port_default))
    ap.add_argument("--dir", help=f"MagIC directory to open (sets {env_prefix}DIR)")
    ap.add_argument("--output", help=f"output directory root (sets {env_prefix}OUTPUT)")
    ap.add_argument("--no-show", action="store_true", help="do not open a browser tab")
    ap.add_argument("--no-reload", action="store_true", help="disable automatic reload on code changes")
    args = ap.parse_args(argv)

    env = dict(os.environ)
    if args.dir:
        env[env_prefix + "DIR"] = os.path.abspath(os.path.expanduser(args.dir))
    if args.output:
        env[env_prefix + "OUTPUT"] = os.path.abspath(os.path.expanduser(args.output))
    env.setdefault("MPLBACKEND", "Agg")
    root = f"http://localhost:{args.port}/"
    url = root if index else root + _app_name(app_files[0])
    if index:
        env[HUB_URL_VAR] = root

    n = stop_previous(args.port)
    if n:
        print(f"stopped {n} previous server process(es) on port {args.port}")

    cmd = serve_command(app_files, args.port, dev=not args.no_reload, index=index)
    print("launching:", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env, cwd=_working_dir(app_files[0]))
    try:
        # the first page build (reading the dataset) takes several seconds; open the
        # browser only once the app answers, instead of showing a blank tab meanwhile
        print("building the app (the first load reads the dataset; ~10 s) ", end="", flush=True)
        ready = False
        for _ in range(120):
            if proc.poll() is not None:
                break
            try:
                import urllib.request
                with urllib.request.urlopen(url, timeout=5) as resp:
                    ready = resp.status == 200
            except Exception:
                ready = False
            if ready:
                break
            print(".", end="", flush=True)
            time.sleep(1)
        print()
        if ready:
            print(f"ready: {url}   (Ctrl-C here stops the server)")
            if not args.no_show:
                open_ui(url)
        elif proc.poll() is None:
            print(f"the server did not answer at {url}; check the messages above")
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 0
