#!/bin/bash
# Final renders, in order; anything already rendered is skipped, so the batch can be resumed.
cd "$(dirname "$0")/.."
OUT=${OUT:-renders/final}
mkdir -p "$OUT"
for r in "$@"; do
  if [ -f "$OUT/$r.png" ] && [ -f "$OUT/$r.json" ]; then echo "skip $r"; continue; fi
  s=$(date +%s)
  if ${BPY:-bvenv/bin/python} -m render.scene "$r" "$OUT/$r.png" final > "$OUT/$r.log" 2>&1; then
    echo "done $r $(( $(date +%s) - s ))s"
  else
    echo "FAIL $r $(( $(date +%s) - s ))s"; grep -E 'Error|line [0-9]+' "$OUT/$r.log" | tail -3
  fi
done
echo "BATCH END"
