#!/bin/bash
# GH Archive 2024-03 (744 hours): issue events and comments with @mentions. Safe to re-run: finished hours are skipped.
cd "$(dirname "$0")"
PY=$(command -v python3); [ -x "$HOME/miniforge3/bin/python3" ] && PY="$HOME/miniforge3/bin/python3"
export PY
mkdir -p out2
for d in $(seq -w 1 31); do for h in $(seq 0 23); do echo "2024-03-$d-$h"; done; done | xargs -P 4 -n 1 bash hour.sh
echo "DONE $(ls out2 | grep -c 'tsv.gz$') / 744"
