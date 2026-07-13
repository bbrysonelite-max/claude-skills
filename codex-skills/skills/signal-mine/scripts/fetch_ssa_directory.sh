#!/bin/bash
# Track 5 — pull all provider types from the SSA Choose Work directory JSON API.
# Usage: bash fetch_ssa_directory.sh [workdir]   (default ~/Desktop/signal-mine)
set -e
WORKDIR="${1:-$HOME/Desktop/signal-mine}"
mkdir -p "$WORKDIR"
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

for res in "en,wf" "vra" "wipa" "paap"; do
  out="$WORKDIR/providers_$(echo "$res" | tr ',' '_').json"
  curl -s -A "$UA" -H "Accept: application/json" -H "X-Requested-With: XMLHttpRequest" \
    -H "Referer: https://choosework.ssa.gov/findhelp/result?option=2&resStr=$res" \
    -o "$out" \
    "https://choosework.ssa.gov/findhelp/sortByName?option=2&resStr=$res&p_pagesize=0&p_pagenum=1"
  count=$(python3 -c "import json;d=json.load(open('$out'));print(len(d.get('resourceVoList') or []))" 2>/dev/null || echo "PARSE-FAIL")
  echo "$res: $count providers -> $out"
  if [ "$count" = "PARSE-FAIL" ] || [ "$count" = "0" ]; then
    echo "WARNING: $res pull returned no JSON providers (a 27,215-byte HTML response = wrong params / API changed)" >&2
  fi
  sleep 2
done
