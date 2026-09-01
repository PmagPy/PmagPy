"""
One-command launcher for a PmagPy Panel application.

What it does, for whichever application is passed to it:
* stops a server already listening on the port (so you never have to hunt down
  and kill the old one),
* starts ``panel serve`` in *dev* mode, which reloads the app whenever its
  source changes — after an edit just refresh the browser tab,
* waits until the app answers before opening a browser, so the tab is never
  blank while the first dataset is read.

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


def main(app_file: str, env_prefix: str, default_port: int, argv=None) -> int:
    """Serve `app_file`, reading its settings from ``<env_prefix>PORT/DIR/OUTPUT``."""
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

    app_dir = os.path.dirname(os.path.abspath(app_file))
    n = stop_previous(args.port)
    if n:
        print(f"stopped {n} previous server process(es) on port {args.port}")

    import socket
    hosts = ["localhost", "127.0.0.1", socket.gethostname(), socket.gethostname().split(".")[0] + ".local"]
    origins = [arg for h in dict.fromkeys(hosts) for arg in ("--allow-websocket-origin", f"{h}:{args.port}")]
    cmd = [sys.executable, "-m", "panel", "serve", app_file, "--port", str(args.port), *origins,
           "--static-dirs", f"assets={os.path.join(app_dir, 'assets')}"]
    if not args.no_reload:
        cmd.append("--dev")
    url = f"http://localhost:{args.port}/{os.path.splitext(os.path.basename(app_file))[0]}"
    print("launching:", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(os.path.dirname(app_dir)))
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
                import webbrowser
                webbrowser.open(url)
        elif proc.poll() is None:
            print(f"the server did not answer at {url}; check the messages above")
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 0
