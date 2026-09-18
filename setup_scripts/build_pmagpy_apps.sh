#!/bin/zsh
# Build the PmagPy Apps desktop application (macOS; see programs/pmagpy_apps/DESKTOP.md).
#
#   setup_scripts/build_pmagpy_apps.sh                        # dist/PmagPy Apps.app: Convert + Directions + Intensity
#   setup_scripts/build_pmagpy_apps.sh --edition directions   # dist/PmagPy Directions.app: Convert + Directions
#   setup_scripts/build_pmagpy_apps.sh --zip                  # ... and zip it for sharing
#
# Runs in the conda environment named by PMAGPY_BUILD_ENV (default demag-playground),
# which needs pyinstaller and pywebview besides pmagpy[apps].
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
ENV_NAME="${PMAGPY_BUILD_ENV:-demag-playground}"
for root in "$HOME/miniforge3" "$HOME/mambaforge" "$HOME/miniconda3" "$HOME/anaconda3"; do
  [ -f "$root/bin/activate" ] && source "$root/bin/activate" "$ENV_NAME" && break
done
python -c "import PyInstaller, webview" || { echo "install pyinstaller and pywebview in $ENV_NAME first"; exit 1; }

NAME=$(PYTHONPATH=programs python -c "from pmagpy_apps import EDITIONS; print(EDITIONS['$EDITION'].title)")
rm -rf "build/$NAME" "dist/$NAME" "dist/$NAME.app"
PMAGPY_BUILD_EDITION="$EDITION" MPLBACKEND=Agg pyinstaller --noconfirm --clean pmagpy_apps.spec

APP="dist/$NAME.app"
if [ -d "$APP" ]; then
  # the size trim (programs/pmagpy_apps/bundle.py) removes libraries whose versioned
  # aliases PyInstaller still symlinks; a dangling link must not go into the bundle
  find "$APP" "dist/$NAME" -type l ! -exec test -e {} \; -delete
  echo "size trim report: build/pmagpy_apps/trim_report.txt"
  # an ad-hoc signature is what lets an unsigned build run at all on Apple silicon; a
  # Developer ID certificate goes here when there is one (see DESKTOP.md)
  codesign --force --deep --sign "${PMAGPY_CODESIGN_IDENTITY:--}" "$APP" 2>/dev/null || true
  echo "built $APP ($(du -sh "$APP" | cut -f1))"
  if [ -n "$ZIP" ]; then
    VERSION=$(python -c "from pmagpy import version; print(version.version.replace('pmagpy-', ''))")
    OUT="dist/${NAME// /-}-${VERSION}-macos-$(uname -m).zip"
    rm -f "$OUT"; ditto -c -k --sequesterRsrc --keepParent "$APP" "$OUT"
    echo "zipped to $OUT ($(du -sh "$OUT" | cut -f1))"
  fi
fi
