"""
The packaged build: PmagPy Apps in a window of its own.

    python programs/pmagpy_apps/desktop.py                  # the full family, from a checkout
    python programs/pmagpy_apps/desktop.py --no-window      # serve only and print the URL (for tests and scripts)
    python programs/pmagpy_apps/desktop.py --port 5010 --dir /path/to/magic

What happens when the application is opened, in order and as fast as each step
allows:

1. A window opens showing the splash screen (:mod:`.splash`) — before Panel,
   Bokeh or pmagpy are imported, so it is on the screen within a moment of the
   double-click.
2. On a worker thread the libraries are imported, the family's server is built
   in this process (:class:`pmagpy_panel.serve.FamilyServer`) on a free port,
   and the splash's status line follows along.
3. When the site answers, the window navigates to it. From here on it is the
   same PmagPy Apps that ``pmagpy-apps`` serves in a browser tab, in the
   edition the build chose (:data:`pmagpy_apps.EDITIONS`).

The window is pywebview's — the system's own web view, so the download is not
a browser — and its folder dialog is handed to :func:`pmagpy_panel.runtime.set_folder_dialog`,
so "Browse with Finder…" opens the native chooser here too. Closing the window
ends the process. Without pywebview (a checkout that has not installed it) the
page opens in the default browser instead, splash and all.
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
import traceback
from typing import Optional

# no window toolkit may be imported by matplotlib: this process draws only through the browser
os.environ.setdefault("MPLBACKEND", "Agg")

from pmagpy_apps import EDITION_VAR, EDITIONS, Edition, current_edition  # noqa: E402
from pmagpy_apps.splash import splash_html, status_js  # noqa: E402

APPLICATIONS = ("pmagpy_directions", "pmagpy_intensity", "pmagpy_rockmag", "pmagpy_anisotropy")
WINDOW = dict(width=1500, height=940, min_size=(1000, 640))


def bundle_root() -> Optional[str]:
    """Where a frozen build keeps its data files (``sys._MEIPASS``), or None when running from source."""
    return getattr(sys, "_MEIPASS", None) if getattr(sys, "frozen", False) else None


def prepare_environment(edition: Edition, directory: str = "", output: str = "") -> None:
    """Environment the served pages read: the edition, the directory to open, where to write.

    A frozen build also makes the bundle its working directory (pmagpy finds
    its data files relative to it) and keeps the analyst's output out of the
    read-only bundle: with no ``PMAGPY_DIRECTIONS_OUTPUT`` set, the example
    dataset's autosave would otherwise land inside the application.
    """
    os.environ[EDITION_VAR] = edition.key
    if directory:
        os.environ["PMAGPY_APPS_DIR"] = os.path.abspath(os.path.expanduser(directory))
    if output:
        os.environ["PMAGPY_DIRECTIONS_OUTPUT"] = os.path.abspath(os.path.expanduser(output))
    root = bundle_root()
    if root:
        os.chdir(root)
        os.environ.setdefault("PMAGPY_DIRECTIONS_OUTPUT", os.path.join(os.path.expanduser("~"), "PmagPy Directions"))
        # PyInstaller's matplotlib hook points MPLCONFIGDIR at a fresh temporary directory
        # on every launch, so the font cache (tens of seconds on a Mac with many fonts)
        # would be rebuilt every time; a cache directory of our own keeps it between launches
        os.environ["MPLCONFIGDIR"] = cache_dir(edition.title, "matplotlib")


def cache_dir(app_title: str, *parts: str) -> str:
    """A per-user cache directory for this application, created if need be."""
    if sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Caches", app_title)
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), app_title, "Cache")
    else:
        base = os.path.join(os.environ.get("XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache")), app_title)
    path = os.path.join(base, *parts)
    os.makedirs(path, exist_ok=True)
    return path


def warm_fonts() -> None:
    """Build matplotlib's font cache (first launch only) on a thread, so that the first
    publication figure does not stall the page for the time it takes."""
    def work():
        try:
            import matplotlib.font_manager  # noqa: F401
        except Exception:
            pass
    threading.Thread(target=work, name="matplotlib-fonts", daemon=True).start()


def version_text() -> str:
    try:
        from pmagpy import version
        return version.version.replace("pmagpy-", "PmagPy ")
    except Exception:
        return ""


def start_server(edition: Edition, port: int, report=lambda text: None):
    """Import the family and serve it on a thread; returns the running :class:`FamilyServer`."""
    report("Loading PmagPy …")
    from pmagpy_panel.serve import FamilyServer
    report("Starting the local server …")
    apps = [a for a in APPLICATIONS if edition.offers(a)]
    server = FamilyServer(apps, port=port, hub=True).start()
    report("Building the start page …")
    if not server.wait_ready(timeout=120):
        raise RuntimeError(f"the server did not answer at {server.url}" + (f": {server.error}" if server.error else ""))
    return server


def _folder_dialog_for(window):
    """pywebview's folder dialog as the runtime's ``(start, prompt) -> path`` callable."""
    import webview

    def choose(start: Optional[str], prompt: str) -> Optional[str]:
        start = start if start and os.path.isdir(start) else os.path.expanduser("~")
        chosen = window.create_file_dialog(webview.FOLDER_DIALOG, directory=start)
        if not chosen:
            return None
        first = chosen[0] if isinstance(chosen, (list, tuple)) else chosen
        return str(first) or None
    return choose


def run_window(edition: Edition, port: int) -> int:
    """The window: splash first, then the served site once it answers."""
    import webview
    from pmagpy_panel import runtime
    title = edition.title
    window = webview.create_window(title, html=splash_html(title, edition.tagline or "PmagPy Apps",
                                                           version=version_text()), **WINDOW)
    runtime.set_folder_dialog(_folder_dialog_for(window))
    outcome = {"code": 0}

    def report(text: str) -> None:
        try:
            window.evaluate_js(status_js(text))
        except Exception:
            pass

    def bring_up():
        try:
            server = start_server(edition, port, report)
            report("Ready")
            window.load_url(server.url)
            warm_fonts()
        except Exception as exc:
            traceback.print_exc()
            outcome["code"] = 1
            report(f"Could not start: {exc}")
            time.sleep(8)
            window.destroy()

    webview.start(bring_up, private_mode=False)      # returns when the window is closed
    return outcome["code"]


def run_headless(edition: Edition, port: int) -> int:
    """Serve only: print the URL and run until interrupted (the desktop build's test mode)."""
    server = start_server(edition, port, report=lambda text: print(text, flush=True))
    print(f"ready: {server.url}   ({edition.title}, {edition.key} edition; Ctrl-C stops)", flush=True)
    warm_fonts()
    try:
        while server.thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.stop()
    return 0


def main(edition: str = "", argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--edition", default=edition or os.environ.get(EDITION_VAR, "full"), choices=sorted(EDITIONS),
                    help="which part of the family to offer")
    ap.add_argument("--port", type=int, default=0, help="port to serve on (default: a free one)")
    ap.add_argument("--dir", default="", help="MagIC directory to open at start")
    ap.add_argument("--output", default="", help="where PmagPy Directions writes tables, figures and .redo files")
    ap.add_argument("--no-window", action="store_true", help="serve only and print the URL; no window")
    # a frozen build started by double-click gets no arguments (older macOS passed a -psn_
    # process serial number, ignored here); started from a terminal it takes the same options
    given = sys.argv[1:] if argv is None else list(argv)
    args, _unknown = ap.parse_known_args([a for a in given if not a.startswith("-psn")])
    chosen = EDITIONS[args.edition]
    prepare_environment(chosen, args.dir, args.output)
    if args.no_window:
        return run_headless(chosen, args.port)
    try:
        import webview  # noqa: F401
    except ImportError:
        print("pywebview is not installed; opening the page in the browser instead", flush=True)
        server = start_server(chosen, args.port, report=lambda text: print(text, flush=True))
        from pmagpy_panel.runtime import open_ui
        open_ui(server.url)
        print(f"ready: {server.url}   (Ctrl-C here stops the server)", flush=True)
        try:
            while server.thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            server.stop()
        return 0
    code = run_window(chosen, args.port)
    # the server thread is a daemon; nothing is left to wait for
    sys.stdout.flush()
    os._exit(code)


if __name__ == "__main__":
    if not getattr(sys, "frozen", False):
        _HERE = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, os.path.dirname(_HERE))
        sys.path.insert(0, os.path.dirname(os.path.dirname(_HERE)))
    sys.exit(main())
