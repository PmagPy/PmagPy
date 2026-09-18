#!/bin/zsh
# Build the PmagPy Directions desktop application (macOS; see programs/pmagpy_apps/DESKTOP.md).
#
#   setup_scripts/build_pmagpy_directions.sh              # build dist/PmagPy Directions.app
#   setup_scripts/build_pmagpy_directions.sh --zip        # ... and zip it for sharing
#
# Runs in the conda environment named by PMAGPY_BUILD_ENV (default demag-playground),
# which needs pyinstaller and pywebview besides pmagpy[apps].
set -euo pipefail
cd "$(dirname "$0")/.."
ENV_NAME="${PMAGPY_BUILD_ENV:-demag-playground}"
for root in "$HOME/miniforge3" "$HOME/mambaforge" "$HOME/miniconda3" "$HOME/anaconda3"; do
  [ -f "$root/bin/activate" ] && source "$root/bin/activate" "$ENV_NAME" && break
done
python -c "import PyInstaller, webview" || { echo "install pyinstaller and pywebview in $ENV_NAME first"; exit 1; }

rm -rf "build/PmagPy Directions" "dist/PmagPy Directions" "dist/PmagPy Directions.app"
MPLBACKEND=Agg pyinstaller --noconfirm --clean pmagpy_directions.spec

APP="dist/PmagPy Directions.app"
if [ -d "$APP" ]; then
  # an ad-hoc signature is what lets an unsigned build run at all on Apple silicon; a
  # Developer ID certificate goes here when there is one (see DESKTOP.md)
  codesign --force --deep --sign "${PMAGPY_CODESIGN_IDENTITY:--}" "$APP" 2>/dev/null || true
  echo "built $APP ($(du -sh "$APP" | cut -f1))"
  if [ "${1:-}" = "--zip" ]; then
    VERSION=$(python -c "from pmagpy import version; print(version.version.replace('pmagpy-', ''))")
    ZIP="dist/PmagPy-Directions-${VERSION}-macos-$(uname -m).zip"
    rm -f "$ZIP"; ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
    echo "zipped to $ZIP ($(du -sh "$ZIP" | cut -f1))"
  fi
fi
