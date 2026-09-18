"""
What the desktop bundle leaves out, and why.

**Read this first if a packaged build misbehaves where a checkout does not.**
The PyInstaller build (``pmagpy_apps.spec``) is trimmed to keep the download
reasonable: an untrimmed build of PmagPy Apps was 372 MB on disk (145 MB
zipped), and about half of that was material the applications never touch.
The rules below say exactly what is dropped; the spec applies them and writes
``build/pmagpy_apps/trim_report.txt`` listing every file removed (the build
script then deletes the dangling symlinks PyInstaller leaves for the dropped
libraries' versioned aliases). If a
packaged build shows a 404 in the browser console for a ``bundled/…`` file, a
missing shared library, or an ``ImportError`` for a module named here, this is
where to look — add the item to the keep list or remove it from the exclusions,
rebuild, and run the browser suites.

The three cuts, and what they were worth in the first trimmed build:

1. **Panel's bundled JavaScript** (``panel/dist/bundled``, 93 MB): one folder
   per Panel component — deck.gl, VTK, Ace, Plotly, Perspective, Bootstrap,
   reveal.js … Only the components the family renders are kept
   (:data:`KEEP_BUNDLED`). The list was made by serving the desktop edition
   from a checkout and logging every static request while a browser visited
   every tab of every application (``programs/pmagpy_apps/bundle_audit.py``
   repeats that walk), then cross-checked against the resources Panel's own
   classes declare (``test_desktop.py``). Bokeh's and Panel's unminified
   JavaScript, source maps and the runtime TypeScript compiler go too: the
   server only ever serves the ``.min.js`` files.
2. **ICU** (42 MB): conda-forge's ``sqlite3`` links the ICU libraries, and the
   standard-library ``sqlite3`` module was collected although nothing in the
   family opens a database. Excluding the module drops the whole chain.
3. **Odds and ends** (~15 MB): plotly (pulled in by a Panel hook; the family
   has no Plotly pane), Tcl/Tk (via Pillow's Tk module; matplotlib draws with
   Agg here) and pyzmq.

Not dropped, deliberately: psutil, watchfiles, yaml and tqdm are imported by
Panel or Bokeh at start; nh3 is Panel's Markdown sanitiser; scipy is left whole
because its subpackages import one another. Three library chains looked
removable and are not, in conda-forge's builds: matplotlib's ``ft2font`` links
raqm (and through it HarfBuzz, GLib, FriBidi, graphite2, gettext, PCRE2),
libtiff links WebP, and Pillow's core imaging module links the X11 client
libraries (xcb, Xau, Xdmcp). Dropping any of them made the whole application
fail to import in the packaged build — which is why :data:`DROP_BINARY_PREFIXES`
names only the chains that nothing kept refers to, and why
``bundle_audit.py --libs`` exists: run it on a build to cross-check every kept
extension module's library references against the drop list.
"""
from __future__ import annotations

import os
import posixpath
from typing import Iterable, Tuple

#: Folders of ``panel/dist/bundled`` the family needs (every other folder is dropped).
#: The FastListTemplate (@microsoft/fast-components, fast, fastbasetemplate,
#: fastlisttemplate, theme, font-awesome), Tabulator (datatabulator), and the
#: ES-module shim that loads the toolkit's JSComponents (reactiveesm). ``css``,
#: ``images``, ``panel`` and ``notificationarea`` are small and kept in case a
#: pane asks for them.
KEEP_BUNDLED: Tuple[str, ...] = (
    "@microsoft", "css", "datatabulator", "fast", "fastbasetemplate", "fastlisttemplate",
    "font-awesome", "images", "notificationarea", "panel", "reactiveesm", "theme",
)

#: Files under ``bokeh/server/static/js`` and ``panel/dist`` that are never served:
#: the unminified builds, their source maps and the runtime compiler.
DROP_JS_NAMES: Tuple[str, ...] = ("compiler.js",)
DROP_JS_DIRS: Tuple[str, ...] = ("bokeh/server/static/js/lib",)      # what compiler.js compiles against

#: Python modules excluded from the analysis (see the module docstring for why).
EXCLUDE_MODULES: Tuple[str, ...] = (
    "sqlite3", "_sqlite3",                 # drops libsqlite3 and with it ICU (42 MB)
    "plotly",                              # no Plotly pane in the family
    "zmq",                                 # not imported by anything served here
    "PIL._imagingtk", "PIL.ImageTk",       # Tk, which brings libtk/libtcl
)

#: Shared libraries dropped by name prefix, belt and braces for the exclusions above:
#: the ICU chain, sqlite and Tcl/Tk. Nothing that is kept links any of these
#: (``bundle_audit.py --libs`` checks that on a build).
DROP_BINARY_PREFIXES: Tuple[str, ...] = ("libicu", "libsqlite3", "libtk", "libtcl")


def _parts(path: str) -> list:
    return posixpath.normpath(path.replace(os.sep, "/")).split("/")


def keep_data(dest: str) -> bool:
    """Whether a data file at bundle path `dest` is kept.

    Args:
        dest: the file's path inside the bundle, e.g.
            ``panel/dist/bundled/deckglplot/deck.min.js``.
    """
    path = posixpath.normpath(dest.replace(os.sep, "/"))
    parts = _parts(path)
    if len(parts) > 3 and parts[:3] == ["panel", "dist", "bundled"]:
        return parts[3] in KEEP_BUNDLED
    name = parts[-1]
    if path.startswith("bokeh/server/static/js/") or path.startswith("panel/dist/"):
        if name in DROP_JS_NAMES or name.endswith(".js.map"):
            return False
        if name.endswith(".js") and not name.endswith(".min.js") and posixpath.dirname(path) in (
                "bokeh/server/static/js", "panel/dist"):
            return False                     # an unminified build beside its .min.js
    if any(path.startswith(d + "/") for d in DROP_JS_DIRS):
        return False
    return True


def keep_binary(dest: str) -> bool:
    """Whether a shared library or extension module at bundle path `dest` is kept."""
    name = posixpath.basename(dest.replace(os.sep, "/"))
    return not any(name.startswith(prefix) for prefix in DROP_BINARY_PREFIXES)


def trim(entries: Iterable[tuple], keep) -> tuple:
    """Split a PyInstaller TOC (``(dest, source, kind)`` tuples) into (kept, dropped) by `keep(dest)`."""
    kept, dropped = [], []
    for entry in entries:
        (kept if keep(entry[0]) else dropped).append(entry)
    return kept, dropped


def report(dropped_data, dropped_binaries) -> str:
    """A human-readable account of what was left out, with sizes, for ``trim_report.txt``."""
    def size(entry):
        try:
            return os.path.getsize(entry[1])
        except OSError:
            return 0
    lines = ["What this build leaves out, and why: see programs/pmagpy_apps/bundle.py", ""]
    for title, entries in (("Data files dropped", dropped_data), ("Shared libraries dropped", dropped_binaries)):
        total = sum(size(e) for e in entries) / 1e6
        lines.append(f"{title}: {len(entries)} files, {total:.1f} MB")
        by_folder = {}
        for e in entries:
            parts = _parts(e[0])
            key = "/".join(parts[:4]) if parts[:3] == ["panel", "dist", "bundled"] else "/".join(parts[:-1]) or parts[-1]
            by_folder[key] = by_folder.get(key, 0) + size(e)
        for key, total in sorted(by_folder.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {total / 1e6:7.1f} MB  {key}")
        lines.append("")
    return "\n".join(lines)
