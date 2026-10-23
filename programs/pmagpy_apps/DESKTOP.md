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
* A study is worked on where the analyst keeps it: the folder chosen in Open
  MagIC data, or the lab folder converted into on the Convert page. Lab files
  are never edited; the MagIC tables, session files and exports are written
  beside them, so they stay with the study (in its git repository, say).
  Directions, Intensity, Rock Magnetism, Anisotropy and the hub's Metadata
  page all read and write that folder, so a flag set in Directions, an
  interpretation exported from Intensity and a metadata edit on the hub are one
  set of tables, ready to upload. An export that replaces the study's tables
  asks for a second click, and keeps the tables it replaces in
  `backup_before_…/`. Contributions downloaded from MagIC go into `~/PmagPy/`
  (`MagIC_<id>/`) and are worked on there in the same way.
* The PmagPy folder, `~/PmagPy/` (`PMAGPY_APPS_OUTPUT` or `--output` names
  another), takes what cannot be worked on in place
  (`pmagpy_panel.datasets.needs_copy`): the examples, which live in the
  read-only bundle (or a checkout's `data_files`), and a study in a folder that
  cannot be written. Such a study is copied once to
  `~/PmagPy/<dataset>-<fingerprint>/` and every application works on that one
  copy; the fingerprint is a short hash of the study's full path, so studies in
  folders of the same name get copies of their own. The bundled example's copy
  is `~/PmagPy/McMurdo-example/`, whatever the application's location or
  version; a newer example's new files are added to it and the files in it are
  kept. A copy records where it came from (`.pmagpy_working_copy.json`), the
  pages name the study (McMurdo, not its fingerprinted folder), and the
  dataset block in the side column adds "working copy · ~/PmagPy/McMurdo-…".
* A copy records what it was made from: each file's size, modification time
  and checksum. When the study has changed since (a newer example), the side
  column and Home say so and offer **Start a fresh copy**: the old copy, with
  its interpretations, is set aside under its name and the date
  (`McMurdo-example-2026-10-20`, then `-2` …; nothing in it is overwritten)
  and a new copy is made. Each copy has an id of its own
  (`pmagpy_panel.datasets.copy_id`): a window still open on a copy that was
  set aside writes neither its autosave nor an export into the new copy at the
  same path, and says to reload (`pmagpy_panel.autosave`).
* Earlier builds worked on every study in a copy under `~/PmagPy/`. When such
  a study is opened now it is worked on in place, and the side column and Home
  name the earlier copy and the files in it that differ from the study's
  (`pmagpy_panel.datasets.earlier_copy_note`). **Bring the copy's work into the
  study** copies those files into the study -- each study file it replaces kept
  first in `backup_before_working_copy-<date>/` -- and sets the copy aside
  under its name and the date (`pmagpy_panel.datasets.bring_over`).
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

In a conda environment with `pmagpy[apps]` plus `pyinstaller` (conda-forge) and
`pywebview` (pip: conda-forge builds pywebview for Windows and Linux only; on a Mac
pip brings the pyobjc frameworks it needs). The build script uses the environment
named by `PMAGPY_BUILD_ENV` (default `pmagpy-directions`) and puts this tree first
on the path, so neither an editable install of another checkout nor an active
virtualenv decides what is built. Build from a clean tree -- a `git archive` export
or a checkout without stray files: the McMurdo example is bundled from
`data_files/3_0/McMurdo` as it is on disk (the trim leaves out any autosave, backup
or working-copy marker a session left there, see `bundle.py`).

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

The full check of a build, as run after the size trim was introduced — the
browser suites need the set-up each documents: Directions opened on
`dmag_magic` with the chooser stub answering McMurdo, Intensity on a study
with interpretations (the Beaver Bay data here; McMurdo trips two of its fixed
waits):

```bash
PMAGPY_DIRECTIONS_DIR=$PWD/data_files/dmag_magic \
PMAGPY_DIRECTIONS_CHOOSER_STUB=$PWD/data_files/3_0/McMurdo \
PMAGPY_APPS_OUTPUT=/tmp/out \
  "dist/PmagPy Apps.app/Contents/MacOS/PmagPy Apps" --no-window --port 5166 &
python programs/pmagpy_apps/bundle_audit.py http://localhost:5166 \
  "$PWD/dist/PmagPy Apps.app/Contents/Resources/data_files/3_0/McMurdo"    # no bundled 404s
python programs/pmagpy_apps/bundle_audit.py --libs "dist/PmagPy Apps.app"  # no dropped library is linked
(cd programs/pmagpy_directions && python ui_test.py http://localhost:5166/pmagpy_directions /tmp/shots/dir)
(cd programs/pmagpy_intensity && python ui_test.py "http://localhost:5166/pmagpy_intensity?dir=/path/to/a/study" /tmp/shots/int)
```

## What the bundle leaves out, and why (size)

An untrimmed build was 372 MB on disk and 145 MB zipped; about half of it was
material the applications never touch. Trimmed, PmagPy Apps.app is 213 MB on
disk and 92 MB zipped (2026-09-18); 212 MiB on disk (215 MB of files) and 90 MB
zipped on 2026-09-29, with Panel 1.9.4, Bokeh 3.9.2, Python 3.12.14, PyInstaller
6.22.3 and pywebview 6.2.1 (`du -h` of the zip reads 97M: it counts allocation
blocks). PmagPy Directions.app is 1 MB smaller. `pmagpy_apps.spec` therefore trims the
bundle by the rules in [`bundle.py`](bundle.py), whose docstring is the full
account. In short: Panel's bundled JavaScript is cut to the components the
family renders (the Fast template, Tabulator, the ES-module shim), the
unminified Bokeh/Panel builds and the runtime compiler go, the standard-library
`sqlite3` module is excluded (conda-forge's sqlite links the 42 MB ICU
libraries), and plotly, Tcl/Tk and pyzmq are excluded. Pillow's text-shaping
chain, WebP and the X11 client libraries stay: matplotlib, libtiff and Pillow
link them in conda-forge's builds, and the first trimmed build failed to import
without them. Every file removed is listed in `build/pmagpy_apps/trim_report.txt`
after a build (the build script keeps a copy per edition, `build/trim_report-<edition>.txt`,
since both editions share that work folder), and the spec prints the same report; the build script then
removes the dangling symlinks PyInstaller leaves for the dropped libraries'
versioned aliases.

**If a packaged build misbehaves where a checkout does not, suspect the trim
first**: a 404 in the browser console for a `bundled/…` file means a component
was added to a view without being added to `KEEP_BUNDLED`; a missing shared
library or an `ImportError` names something in `EXCLUDE_MODULES` or
`DROP_BINARY_PREFIXES`. Add it back, rebuild, and run the browser suites.
[`bundle_audit.py`](bundle_audit.py) repeats the measurement the keep list was
made from — it walks every tab of every application in a browser, logs every
static request and compares the bundled folders asked for with the keep list —
and `test_desktop.py` checks the keep list against the resources Panel's own
Tabulator and Fast template classes declare. `bundle_audit.py --libs "dist/PmagPy Apps.app"`
cross-checks every kept extension module's shared-library references against
the drop list, which is how the three chains above were found.

The Fast theme asks Google Fonts for Open Sans; offline that request fails
quietly and the system font is used. Nothing else in the page reaches the
network, except a conversion: the converters ask earthref.org for the current
data model and method codes, and use the bundled copies when it cannot be
reached (checked with the network blocked: a TDT conversion took under a second).

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
pywebview): 0.6-0.7 s on an M1 Max, 2.2 s the first time a new build is
opened. Behind it, importing Panel, Bokeh, pandas and pmagpy takes two to
three seconds and the server is ready a moment after that (`--no-window`
prints "ready" 1.9-2.5 s after launch); the start page has
no dataset to read, so it appears as soon as the server answers (2.6-3.1 s
after the double-click, 4.8 s for the first launch of a new build). Opening
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
