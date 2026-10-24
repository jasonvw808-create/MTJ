#!/bin/bash
# Build both catalogue volumes, presentation (A4) and print (A4 + 3 mm bleed) editions.
#   make_catalogues.sh <renders_dir> <photos_dir> <logos_dir> <work_dir> <pdf_out_dir>
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
RENDERS=$1; PHOTOS=$2; LOGOS=$3; WORK=$4; OUT=$5
PY=${PY:-python3}
mkdir -p "$WORK" "$OUT"
cp "$HERE/catalogue.css" "$WORK/"
cp -r "$HERE/fonts" "$WORK/" && cp "$HERE/fonts/fonts.css" "$WORK/fonts.css"
for MODE in screen print; do
  $PY "$HERE/prepare_assets.py" "$RENDERS" "$PHOTOS" "$LOGOS" "$WORK" $MODE
  $PY "$HERE/build.py" "$HERE/data/data.json" "$WORK" $MODE
  # stop on colliding text or text outside the safe area (SKIP_CHECK=1 to build anyway)
  node "$HERE/check_layout.js" "$WORK/granite-$MODE.html" "$WORK/stainless-$MODE.html" || [ "${SKIP_CHECK:-0}" = 1 ]
  node "$HERE/export_pdf.js" "$WORK/granite-$MODE.html" "$WORK/granite-$MODE.pdf"
  node "$HERE/export_pdf.js" "$WORK/stainless-$MODE.html" "$WORK/stainless-$MODE.pdf"
done
FIN="$HERE/finalize_pdf.py"
$PY "$FIN" "$WORK/granite-screen.pdf" "$OUT/MTJ_Granite_Kitchen_Sink_Collection_Vol01.pdf" "Maju Terus Jaya — Granite Kitchen Sink Collection — Volume 01" screen
$PY "$FIN" "$WORK/granite-print.pdf" "$OUT/MTJ_Granite_Kitchen_Sink_Collection_Vol01_PRINT.pdf" "Maju Terus Jaya — Granite Kitchen Sink Collection — Volume 01 (print)" print
$PY "$FIN" "$WORK/stainless-screen.pdf" "$OUT/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02.pdf" "Maju Terus Jaya — Stainless Steel Kitchen Sink Collection — Volume 02" screen
$PY "$FIN" "$WORK/stainless-print.pdf" "$OUT/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02_PRINT.pdf" "Maju Terus Jaya — Stainless Steel Kitchen Sink Collection — Volume 02 (print)" print
ls -la "$OUT"
