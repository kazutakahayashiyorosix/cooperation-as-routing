#!/bin/bash
# one GH Archive hour -> out2/<hour>.tsv.gz
set -o pipefail
cd "$(dirname "$0")"
h="$1"; f="out2/$h.tsv.gz"
[ -s "$f" ] && exit 0
for t in 1 2 3; do
  if curl -sfL --retry 3 "https://data.gharchive.org/$h.json.gz" | "$PY" extract.py > "$f.tmp"; then
    mv "$f.tmp" "$f"; echo "ok $h"; exit 0
  fi
  sleep 10
done
rm -f "$f.tmp"; echo "FAIL $h"
