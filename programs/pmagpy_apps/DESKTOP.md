# PmagPy Apps as a desktop application

The family as one application that needs no Python installed: **PmagPy
Apps.app** is the *desktop edition* — convert measurement files into MagIC
tables, then interpret directions in PmagPy Directions and paleointensity in
PmagPy Intensity. **PmagPy Directions.app** is the same build with Directions
alone. Both are the code that `pmagpy-apps` serves in a browser tab
(`PMAGPY_APPS_EDITION=desktop pmagpy-apps` gives the same pages from a
checkout); only the wrapper differs, as [HUB_PLAN.md §8](../pmagpy_panel/HUB_PLAN.md)
intended. Rock magnetism and Anisotropy join by adding them to the edition
(`pmagpy_apps/__init__.py`) once they are ready.

## What the analyst gets

* One application. Double-click and a window opens at once on the magpie
  splash screen; the status line under the bird says what is happening
  (loading PmagPy, starting the local server) and the window turns into the
  start page a few seconds later.
* The start page's three doors: open a MagIC directory, convert a folder of
  measurement files (every converter of `pmagpy.convert_registry`), explore the
  shipped McMurdo example — which has both demagnetization and Thellier
  experiments, so both applications open on it. A directory's page shows what
  it holds and opens the applications its measurements support; "← PmagPy Apps"
  in an application's header comes back.
* "Browse with Finder…" is the system's own folder chooser (pywebview's dialog,
  registered with `pmagpy_panel.runtime.set_folder_dialog`).
* Output stays out of the application: with no `PMAGPY_DIRECTIONS_OUTPUT` /
  `PMAGPY_INTENSITY_OUTPUT` set, the applications write their auto-saves,
  tables and figures under `~/PmagPy Directions/<dataset>/` and
  `~/PmagPy Intensity/<dataset>/` — the bundle is read-only and the example
  dataset lives inside it.
* Closing the window ends the process; nothing keeps running.

## How it is built

```
programs/pmagpy_apps/desktop_apps.py         entry point of the desktop edition: desktop.main(edition="desktop")
programs/pmagpy_apps/desktop_directions.py   entry point of the Directions edition
programs/pmagpy_apps/desktop.py              splash window → server thread → navigate; --no-window for tests
programs/pmagpy_apps/splash.py               the splash page (self-contained HTML, magpie as a data URI)
programs/pmagpy_panel/serve.py               the family as one Bokeh server in this process (FamilyServer)
pmagpy_apps.spec                             the PyInstaller specification (repository root); PMAGPY_BUILD_EDITION picks the edition
setup_scripts/build_pmagpy_apps.sh           build, ad-hoc sign, optionally zip
```

In a conda environment with `pmagpy[apps]` plus `pyinstaller` and `pywebview`
(the `demag-playground` environment has both):

```bash
setup_scripts/build_pmagpy_apps.sh --zip                     # → dist/PmagPy Apps.app and a zip beside it
setup_scripts/build_pmagpy_apps.sh --edition directions      # → dist/PmagPy Directions.app
```

or, by hand, `PMAGPY_BUILD_EDITION=desktop MPLBACKEND=Agg pyinstaller --noconfirm pmagpy_apps.spec`
from the repository root. It is a one-folder build (`--onedir`), deliberately:
a one-file build unpacks itself on every launch, which is exactly the seconds
the splash screen is there to hide. The bundle carries the MagIC data model and
vocabularies (so nothing is fetched from EarthRef at start), the Natural Earth
coastlines of the pole globe, each application's assets and the McMurdo
example. The applications are imported by name at run time, so the spec names
them (and the paleointensity core, BiCEP included) as hidden imports; CmdStan
is left out and BiCEP samples with its built-in sampler.

Checking a build without a window:

```bash
"dist/PmagPy Apps.app/Contents/MacOS/PmagPy Apps" --no-window --port 5123
# prints "ready: http://localhost:5123/" — open it in any browser, or point an application's
# ui_test.py at http://localhost:5123/pmagpy_directions or /pmagpy_intensity
```

(A frozen build started by double-click gets no arguments; started from a
terminal it takes the same options as `desktop.py`.)

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
data and another for the page; its 396 Thellier specimens take PmagPy Intensity
a few seconds more, behind the header and a spinner. Both loaders read the
measurements table column by column rather than row by row, and the tabs that
are not on show draw nothing until they are opened.

PyInstaller points matplotlib at a fresh temporary config directory on every
launch, which would rebuild the font cache (tens of seconds on a Mac with many
fonts) each start; `desktop.py` keeps a cache directory of its own under
`~/Library/Caches/<application>/`, imports matplotlib only when a figure is first
asked for, and builds the cache on a thread once the site is up.
