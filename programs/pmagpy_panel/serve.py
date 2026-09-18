"""
Serving the family from inside one Python process.

``pmagpy_panel.launch`` runs ``panel serve`` as a child process, which is right
for development (its ``--dev`` reload, its own console). A packaged build has
no ``panel`` command to call and wants the server in the same process as its
window, so this module builds the same site — the hub at ``/`` with each
application beside it, every application's ``assets/`` mounted at
``/<app_id>_assets`` — as a Bokeh/Tornado server object and runs it on a thread
of its own. Nothing about what the pages *are* lives here: each application's
``app.serve_default`` builds its page per session, exactly as its served file
does under ``panel serve``.
"""
from __future__ import annotations

import asyncio
import importlib
import os
import socket
import threading
import time
import urllib.request
from typing import Callable, Dict, Optional, Sequence

from .runtime import HUB_URL_VAR

HUB_ID = "pmagpy_apps"


def free_port(preferred: int = 0) -> int:
    """A TCP port nobody is listening on: `preferred` when it is free, else one the system picks."""
    for candidate in ([preferred] if preferred else []) + [0]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", candidate))
                return sock.getsockname()[1]
            except OSError:
                continue
    raise OSError("no free TCP port")


def _assets_dir(app_id: str) -> Optional[str]:
    package = importlib.import_module(app_id)
    path = os.path.join(os.path.dirname(os.path.abspath(package.__file__)), "assets")
    return path if os.path.isdir(path) else None


def _page_builder(app_id: str) -> Callable:
    """The per-session page builder of an application: its ``app.serve_default``."""
    module = importlib.import_module(f"{app_id}.app")
    return module.serve_default


def family_site(app_ids: Sequence[str], hub: bool = True) -> tuple:
    """(panels, static_dirs) for ``pn.serve``: the hub (when asked) at ``/`` and ``/pmagpy_apps``,
    each application at ``/<app_id>``, each ``assets/`` at ``/<app_id>_assets``.

    Args:
        app_ids: the analysis applications to serve; one that is not installed is left out.
        hub: serve the PmagPy Apps page as the site's index.
    """
    panels: Dict[str, Callable] = {}
    static: Dict[str, str] = {}
    ids = ([HUB_ID] if hub else []) + [a for a in app_ids if a != HUB_ID]
    for app_id in ids:
        try:
            builder = _page_builder(app_id)
        except ImportError:
            continue
        if app_id == HUB_ID:
            panels["/"] = builder
        panels[f"/{app_id}"] = builder
        assets = _assets_dir(app_id)
        if assets:
            static[f"{app_id}_assets"] = assets
    return panels, static


def make_server(app_ids: Sequence[str], port: int, hub: bool = True, address: str = "127.0.0.1"):
    """The Bokeh server for the family on `port`, not yet started.

    Sets ``PMAGPY_APPS_URL`` so that the applications' headers show the way back
    to the hub, and ``MPLBACKEND`` so no window toolkit is ever imported.
    """
    os.environ.setdefault("MPLBACKEND", "Agg")
    root = f"http://localhost:{port}/"
    if hub:
        os.environ[HUB_URL_VAR] = root
    import panel as pn
    panels, static = family_site(app_ids, hub=hub)
    if not panels:
        raise ImportError(f"none of {list(app_ids)} is installed")
    origins = [f"localhost:{port}", f"127.0.0.1:{port}"]
    return pn.serve(panels, port=port, address=address, show=False, start=False, threaded=False,
                    websocket_origin=origins, static_dirs=static, title="PmagPy Apps", verbose=False)


class FamilyServer:
    """The family's server on a thread of its own.

    Args:
        app_ids: the analysis applications to serve beside the hub.
        port: the port to try; a free one is taken when it is busy or 0.
        hub: serve the PmagPy Apps page as the index.
    """

    def __init__(self, app_ids: Sequence[str], port: int = 0, hub: bool = True):
        self.app_ids = list(app_ids)
        self.port = free_port(port)
        self.hub = hub
        self.url = f"http://localhost:{self.port}/"
        self.server = None
        self.thread: Optional[threading.Thread] = None
        self.error: Optional[BaseException] = None

    def start(self) -> "FamilyServer":
        """Start serving on a daemon thread with its own event loop; returns at once."""
        started = threading.Event()

        def run():
            try:
                asyncio.set_event_loop(asyncio.new_event_loop())
                self.server = make_server(self.app_ids, self.port, hub=self.hub)
                self.server.start()
                started.set()
                self.server.io_loop.start()
            except BaseException as exc:                   # reported to whoever waits
                self.error = exc
                started.set()
        self.thread = threading.Thread(target=run, name="pmagpy-apps-server", daemon=True)
        self.thread.start()
        started.wait()
        if self.error is not None:
            raise self.error
        return self

    def wait_ready(self, timeout: float = 60.0, path: str = "") -> bool:
        """Block until the site answers a request (or `timeout` seconds pass)."""
        deadline = time.monotonic() + timeout
        url = self.url + path
        while time.monotonic() < deadline:
            if self.error is not None:
                return False
            try:
                with urllib.request.urlopen(url, timeout=5) as response:
                    if response.status == 200:
                        return True
            except Exception:
                pass
            time.sleep(0.15)
        return False

    def stop(self) -> None:
        if self.server is not None:
            loop = self.server.io_loop
            loop.add_callback(self.server.stop)
            loop.add_callback(loop.stop)
