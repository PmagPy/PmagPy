#!/bin/zsh
# Double-click (or keep in the Dock) to launch PmagPy Directions.
# Finds a conda environment named pmagpy-directions (or demag-playground) under
# the usual conda roots; edit PY below if yours lives elsewhere.
# export PMAGPY_DIRECTIONS_DIR="/path/to/a/MagIC/directory"   # dataset opened at start (else data_files/3_0/McMurdo)
# export PMAGPY_DIRECTIONS_OUTPUT="$HOME/pmagpy_output"       # where tables/figures/.redo go (else the data directory)

PY=""
for root in "$HOME/miniforge3" "$HOME/mambaforge" "$HOME/anaconda3" "$HOME/miniconda3" "$HOME/opt/anaconda3"; do
  for env in pmagpy-directions demag-playground; do
    [ -x "$root/envs/$env/bin/python" ] && PY="$root/envs/$env/bin/python" && break 2
  done
done
if [ -z "$PY" ]; then
  echo "No pmagpy-directions (or demag-playground) conda environment found — see the README, or edit PY in this file."
  read -k 1 -s "?Press any key to close."
  exit 1
fi

cd "$(dirname "$0")"
exec "$PY" launch.py "$@"
