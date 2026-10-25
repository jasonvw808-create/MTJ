#!/bin/bash
# Render, one at a time, every name appended to the queue file; waits for new names until "END" is queued.
cd "$(dirname "$0")/.."
Q=$1; OUT=${OUT:-renders/final}
mkdir -p "$OUT"
i=0
while true; do
  mapfile -t names < "$Q"
  if [ $i -ge ${#names[@]} ]; then sleep 10; continue; fi
  r=${names[$i]}; i=$((i+1))
  [ -z "$r" ] && continue
  [ "$r" = "END" ] && { echo "QUEUE END"; break; }
  if [ -f "$OUT/$r.png" ] && [ -f "$OUT/$r.json" ]; then echo "skip $r"; continue; fi
  s=$(date +%s)
  if [ "$r" = "stone_dark" ]; then cmd=(${BPY:-bvenv/bin/python} -m render.texture "$OUT/$r.png" 1500 2104); else cmd=(${BPY:-bvenv/bin/python} -m render.scene "$r" "$OUT/$r.png" final); fi
  if [ "$r" = "stone_dark" ] && [ -f "$OUT/$r.png" ]; then echo "skip $r"; continue; fi
  if "${cmd[@]}" > "$OUT/$r.log" 2>&1; then
    echo "done $r $(( $(date +%s) - s ))s"
  else
    echo "FAIL $r $(( $(date +%s) - s ))s"; grep -E 'Error|line [0-9]+' "$OUT/$r.log" | tail -3
  fi
done
