# PmagPy Directions as a desktop application

The family's first standalone build: the **Directions edition** of PmagPy Apps —
convert measurement files into MagIC tables, then interpret directions in
PmagPy Directions — as one application that needs no Python installed. It is the
same code that `pmagpy-apps` serves in a browser tab (`PMAGPY_APPS_EDITION=directions`
gives the same pages from a checkout); only the wrapper differs, as
[HUB_PLAN.md §8](../pmagpy_panel/HUB_PLAN.md) intended. The other applications
join by adding them to an edition (`pmagpy_apps/__init__.py`) once they are ready.

## What the analyst gets

* One application, `PmagPy Directions.app` (macOS; the same spec builds a folder
  with `PmagPy Directions.exe` on Windows). Double-click and a window opens at
  once on the magpie splash screen; the status line under the bird says what is
  happening (loading PmagPy, starting the local server) and the window turns
  into the start page a few seconds later.
* The start page's three doors: open a MagIC directory, convert a folder of
  measurement files (every converter of `pmagpy.convert_registry`), explore the
  shipped McMurdo example. A directory's page shows what it holds and opens
  PmagPy Directions on it; "← PmagPy Apps" in the header comes back.
* "Browse with Finder…" is the system's own folder chooser (pywebview's dialog,
  registered with `pmagpy_panel.runtime.set_folder_dialog`).
* Output stays out of the application: with no `PMAGPY_DIRECTIONS_OUTPUT` set, PmagPy
  Directions writes its `.redo` auto-saves, tables and figures under
  `~/PmagPy Directions/<dataset>/` — the bundle is read-only and the example
  dataset lives inside it.
* Closing the window ends the process; nothing keeps running.

## How it is built

```
programs/pmagpy_apps/desktop_directions.py   the entry point: desktop.main(edition="directions")
programs/pmagpy_apps/desktop.py              splash window → server thread → navigate; --no-window for tests
programs/pmagpy_apps/splash.py               the splash page (self-contained HTML, magpie as a data URI)
programs/pmagpy_panel/serve.py               the family as one Bokeh server in this process (FamilyServer)
pmagpy_directions.spec                       the PyInstaller specification (repository root)
setup_scripts/build_pmagpy_directions.sh     build, ad-hoc sign, optionally zip
```

In a conda environment with `pmagpy[apps]` plus `pyinstaller` and `pywebview`
(the `demag-playground` environment has both):

```bash
setup_scripts/build_pmagpy_directions.sh --zip     # → dist/PmagPy Directions.app and a zip beside it
```

or, by hand, `MPLBACKEND=Agg pyinstaller --noconfirm pmagpy_directions.spec` from the
repository root. It is a one-folder build (`--onedir`), deliberately: a one-file
build unpacks itself on every launch, which is exactly the seconds the splash
screen is there to hide. The bundle carries the MagIC data model and
vocabularies (so nothing is fetched from EarthRef at start), the Natural Earth
coastlines of the pole globe, both applications' assets and the McMurdo example.

Checking a build without a window:

```bash
"dist/PmagPy Directions.app/Contents/MacOS/PmagPy Directions" --no-window --port 5123
# prints "ready: http://localhost:5123/" — open it in any browser, or point ui_test.py at
# http://localhost:5123/pmagpy_directions
```

(A frozen build ignores command-line arguments when started by double-click; they
are read when it is started from a terminal, which is how this mode is reached.)

## Signing, and what an unsigned build means

The build script signs the bundle *ad hoc* (`codesign --sign -`), which is what
lets it run at all on Apple silicon. It is not notarized: the first time someone
else opens it, macOS says the developer cannot be verified, and they open it by
right-clicking the application and choosing **Open** (or, on macOS 15, allowing
it under System Settings → Privacy & Security after the first refusal). A
Developer ID certificate removes that step — set `PMAGPY_CODESIGN_IDENTITY` to
its name when building and notarize the zip with `xcrun notarytool`; HUB_PLAN.md §8
has the enrolment options. Windows builds face SmartScreen the same way until
they are signed.

## Where the time goes at start-up

The splash is up within about a second of the double-click (Python's boot plus
pywebview). Behind it, importing Panel, Bokeh, pandas and pmagpy takes two to
three seconds and the server is ready a moment after that; the start page has
no dataset to read, so it appears as soon as the server answers. Opening
McMurdo (1,034 specimens) in PmagPy Directions is then about a second for the
data and another for the page: the loader reads the measurements table column
by column and the tabs that are not on show draw nothing until they are opened.
