"""
One-command launcher for PmagPy Directions.

    python programs/pmagpy_directions/launch.py                # start (or restart) and open the browser
    python programs/pmagpy_directions/launch.py --no-show      # start without opening a browser tab
    python programs/pmagpy_directions/launch.py --port 5200 --dir /path/to/magic --output /path/to/out

What it does:
* stops any Demag server already listening on the port (so you never have
  to hunt down and kill the old one),
* starts ``panel serve`` in *dev* mode, which reloads the app automatically
  whenever the source files change — after a code change just refresh the
  browser tab,
* opens the app in your browser.

Run it from any working directory; it uses the Python interpreter it is
started with (activate the environment that has panel installed first).
"""
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, "pmagpy_directions.py")


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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    port_default = os.environ.get("PMAGPY_DIRECTIONS_PORT") or os.environ.get("DEMAG_PORT") or 5100
    ap.add_argument("--port", type=int, default=int(port_default))
    ap.add_argument("--dir", help="MagIC directory to open (sets PMAGPY_DIRECTIONS_DIR)")
    ap.add_argument("--output", help="output directory root (sets PMAGPY_DIRECTIONS_OUTPUT)")
    ap.add_argument("--no-show", action="store_true", help="do not open a browser tab")
    ap.add_argument("--no-reload", action="store_true", help="disable automatic reload on code changes")
    args = ap.parse_args(argv)

    env = dict(os.environ)
    if args.dir:
        env["PMAGPY_DIRECTIONS_DIR"] = os.path.abspath(os.path.expanduser(args.dir))
    if args.output:
        env["PMAGPY_DIRECTIONS_OUTPUT"] = os.path.abspath(os.path.expanduser(args.output))
    env.setdefault("MPLBACKEND", "Agg")

    n = stop_previous(args.port)
    if n:
        print(f"stopped {n} previous server process(es) on port {args.port}")

    import socket
    hosts = ["localhost", "127.0.0.1", socket.gethostname(), socket.gethostname().split(".")[0] + ".local"]
    origins = [arg for h in dict.fromkeys(hosts) for arg in ("--allow-websocket-origin", f"{h}:{args.port}")]
    cmd = [sys.executable, "-m", "panel", "serve", APP, "--port", str(args.port), *origins,
           "--static-dirs", f"assets={os.path.join(HERE, 'assets')}"]
    if not args.no_reload:
        cmd.append("--dev")
    url = f"http://localhost:{args.port}/pmagpy_directions"
    print("launching:", " ".join(cmd))
    proc = subprocess.Popen(cmd, env=env, cwd=os.path.dirname(os.path.dirname(HERE)))
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


if __name__ == "__main__":
    sys.exit(main())
