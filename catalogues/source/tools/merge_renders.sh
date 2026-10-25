#!/bin/bash
# renders/merged: the final render of each view where there is one, else its preview.
cd "$(dirname "$0")/.."
rm -rf renders/merged && mkdir -p renders/merged
for f in tests/prev/*.png renders/final/*.png; do
  n=$(basename "$f" .png)
  ln -sf "$PWD/$f" "renders/merged/$n.png"
  [ -f "${f%.png}.json" ] && ln -sf "$PWD/${f%.png}.json" "renders/merged/$n.json"
done
ls renders/merged/*.png | wc -l
