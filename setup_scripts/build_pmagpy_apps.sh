#!/bin/zsh
# Build the PmagPy Apps desktop application (macOS; see programs/pmagpy_apps/DESKTOP.md).
#
#   setup_scripts/build_pmagpy_apps.sh                        # dist/PmagPy Apps.app: Convert + Directions + Intensity
#   setup_scripts/build_pmagpy_apps.sh --edition directions   # dist/PmagPy Directions.app: Convert + Directions
#   setup_scripts/build_pmagpy_apps.sh --zip                  # ... and zip it for sharing
#
# Runs in the conda environment named by PMAGPY_BUILD_ENV (default pmagpy-directions),
# which needs pyinstaller (conda-forge) and pywebview (pip: conda-forge has no macOS build)
# besides pmagpy[apps]. Build from a clean export (git archive) or a clean checkout: the
# example dataset is bundled from data_files/3_0/McMurdo as it is on disk.
set -euo pipefail
cd "$(dirname "$0")/.."
EDITION=desktop; ZIP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --edition) EDITION="$2"; shift 2 ;;
    --zip) ZIP=1; shift ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
done
ENV_NAME="${PMAGPY_BUILD_ENV:-pmagpy-directions}"
# an active virtualenv or a PYTHONPATH naming another checkout would decide which python and
# which pmagpy the build analyses; this tree is what gets built
unset VIRTUAL_ENV PYTHONHOME
for root in "$HOME/miniforge3" "$HOME/mambaforge" "$HOME/miniconda3" "$HOME/anaconda3"; do
  [ -x "$root/envs/$ENV_NAME/bin/python" ] && export PATH="$root/envs/$ENV_NAME/bin:$PATH" && break
done
export PYTHONPATH="$PWD:$PWD/programs"
python -c "import PyInstaller, webview" || { echo "install pyinstaller and pywebview in $ENV_NAME first"; exit 1; }
python -c "import os, pmagpy; assert os.path.dirname(os.path.dirname(os.path.realpath(pmagpy.__file__))) == os.path.realpath(os.getcwd()), pmagpy.__file__" \
  || { echo "pmagpy does not resolve to this tree"; exit 1; }

NAME=$(PYTHONPATH=programs python -c "from pmagpy_apps import EDITIONS; print(EDITIONS['$EDITION'].title)")
rm -rf build/pmagpy_apps "dist/$NAME" "dist/$NAME.app"      # PyInstaller's workpath is named after the spec
PMAGPY_BUILD_EDITION="$EDITION" MPLBACKEND=Agg pyinstaller --noconfirm --clean pmagpy_apps.spec

APP="dist/$NAME.app"
if [ -d "$APP" ]; then
  # the size trim (programs/pmagpy_apps/bundle.py) removes libraries whose versioned
  # aliases PyInstaller still symlinks; a dangling link must not go into the bundle
  find "$APP" "dist/$NAME" -type l ! -exec test -e {} \; -delete
  # both editions share the workpath: keep each one's report beside the others
  cp build/pmagpy_apps/trim_report.txt "build/trim_report-$EDITION.txt"
  echo "size trim report: build/trim_report-$EDITION.txt"
  # an ad-hoc signature is what lets an unsigned build run at all on Apple silicon; a
  # Developer ID certificate goes here when there is one (see DESKTOP.md)
  codesign --force --deep --sign "${PMAGPY_CODESIGN_IDENTITY:--}" "$APP"
  codesign --verify --deep --strict "$APP" || { echo "the signature of $APP does not verify"; exit 1; }
  echo "built $APP ($(du -sh "$APP" | cut -f1))"
  if [ -n "$ZIP" ]; then
    VERSION=$(python -c "from pmagpy import version; print(version.version.replace('pmagpy-', ''))")
    OUT="dist/${NAME// /-}-${VERSION}-macos-$(uname -m).zip"
    rm -f "$OUT"; ditto -c -k --sequesterRsrc --keepParent "$APP" "$OUT"
    echo "zipped to $OUT ($(du -sh "$OUT" | cut -f1))"
  fi
fi
