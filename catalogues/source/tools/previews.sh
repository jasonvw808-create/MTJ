#!/bin/bash
# Render previews of the named recipes (or all) and assemble a contact sheet.
cd "$(dirname "$0")/.."
mkdir -p tests/prev
Q=${Q:-preview}
for r in "$@"; do
  s=$(date +%s)
  ${BPY:-bvenv/bin/python} -m render.scene "$r" "tests/prev/$r.png" $Q > "tests/prev/$r.log" 2>&1 || { echo "FAIL $r"; grep -E 'Error|line [0-9]+' "tests/prev/$r.log" | tail -4; }
  echo "$r $(( $(date +%s) - s ))s"
done
