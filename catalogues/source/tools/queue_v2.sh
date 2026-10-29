#!/bin/bash
# Render the queue in audit/queue_v2.txt one by one at final quality into renders/v2/, skipping what is done.
# Lines can be added (or a name re-added after deleting its PNG) while it runs; it stops when nothing is left.
#   tools/queue_v2.sh            (run in the background; progress in renders/v2/queue.log)
cd "$(dirname "$0")/.."
mkdir -p renders/v2
Q=audit/queue_v2.txt
while true; do
  next=""
  while read -r name; do
    [ -z "$name" ] && continue
    case "$name" in \#*) continue ;; esac
    if [ ! -f "renders/v2/$name.png" ] && [ ! -f "renders/v2/$name.failed" ]; then next="$name"; break; fi
  done < "$Q"
  [ -z "$next" ] && { echo "$(date +%H:%M) queue empty" >> renders/v2/queue.log; break; }
  echo "$(date +%H:%M) start $next" >> renders/v2/queue.log
  t0=$(date +%s)
  if ${BPY:-bvenv/bin/python} -m render.scene "$next" "renders/v2/$next.tmp.png" final > "renders/v2/$next.log" 2>&1 && [ -f "renders/v2/$next.tmp.png" ]; then
    mv "renders/v2/$next.tmp.png" "renders/v2/$next.png"
    mv "renders/v2/$next.tmp.json" "renders/v2/$next.json" 2>/dev/null
    echo "$(date +%H:%M) done $next $(( ($(date +%s) - t0) / 60 )) min" >> renders/v2/queue.log
  else
    touch "renders/v2/$next.failed"
    echo "$(date +%H:%M) FAILED $next" >> renders/v2/queue.log
  fi
done
