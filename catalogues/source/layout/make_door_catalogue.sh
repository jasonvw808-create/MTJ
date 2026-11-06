#!/bin/bash
# Build the door catalogue (Volume 03, Wellup UPVC Door Collection) in English and Bahasa Indonesia, as presentation
# (A4) and print (A4 + 3 mm bleed) editions: four PDFs.
#   make_door_catalogue.sh <door photos> <editorial> <logos> <work_dir> <pdf_out_dir> [index.html]
# door photos: catalogues/images/doors; editorial: catalogues/images/editorial (cover-doors.jpg, intro-doors.jpg,
# stone-dark.jpg); logos: LOGO_LIGHT.webp and LOGO_INK.webp. With index.html, the door records are first read from
# the website again (tools/extract_doors.js); the build checks every printed fact against them at the end.
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
PHOTOS=$1; EDITORIAL=$2; LOGOS=$3; WORK=$4; OUT=$5; SITE=${6:-}
PY=${PY:-python3}
mkdir -p "$WORK" "$OUT"
DATA="$HERE/data/doors.json"
if [ -n "$SITE" ]; then node "$HERE/../tools/extract_doors.js" "$SITE" "$DATA"; fi
cp "$HERE/catalogue.css" "$HERE/doors.css" "$WORK/"
cp -r "$HERE/fonts" "$WORK/" && cp "$HERE/fonts/fonts.css" "$WORK/fonts.css"
for MODE in screen print; do
  $PY "$HERE/prepare_doors.py" "$PHOTOS" "$EDITORIAL" "$LOGOS" "$WORK" $MODE
  $PY "$HERE/build_doors.py" "$DATA" "$WORK" $MODE en
  $PY "$HERE/build_doors.py" "$DATA" "$WORK" $MODE id
  # stop on colliding text or text outside the safe area (SKIP_CHECK=1 to build anyway)
  node "$HERE/check_layout.js" "$WORK"/doors-$MODE.html "$WORK"/doors-$MODE-id.html || [ "${SKIP_CHECK:-0}" = 1 ]
  for F in doors-$MODE doors-$MODE-id; do
    node "$HERE/export_pdf.js" "$WORK/$F.html" "$WORK/$F.pdf"
  done
done
FIN="$HERE/finalize_pdf.py"
D="MTJ_Wellup_UPVC_Door_Collection_Vol03"
SEN="Wellup UPVC door product catalogue, 2026"; KEN="Maju Terus Jaya, Wellup, UPVC doors, catalogue"
SID="Katalog produk pintu UPVC Wellup, 2026"; KID="Maju Terus Jaya, Wellup, pintu UPVC, katalog"
$PY "$FIN" "$WORK/doors-screen.pdf"    "$OUT/$D.pdf"          "Maju Terus Jaya — Wellup UPVC Door Collection — Volume 03" screen "$WORK/doors-screen.outline.json" en "$SEN" "$KEN"
$PY "$FIN" "$WORK/doors-print.pdf"     "$OUT/${D}_PRINT.pdf"  "Maju Terus Jaya — Wellup UPVC Door Collection — Volume 03 (print)" print "$WORK/doors-print.outline.json" en "$SEN" "$KEN"
$PY "$FIN" "$WORK/doors-screen-id.pdf" "$OUT/${D}_ID.pdf"       "Maju Terus Jaya — Koleksi Pintu UPVC Wellup — Volume 03" screen "$WORK/doors-screen-id.outline.json" id "$SID" "$KID"
$PY "$FIN" "$WORK/doors-print-id.pdf"  "$OUT/${D}_ID_PRINT.pdf" "Maju Terus Jaya — Koleksi Pintu UPVC Wellup — Volume 03 (cetak)" print "$WORK/doors-print-id.outline.json" id "$SID" "$KID"
# every model once, every printed fact and code, the index, the pages and the bookmarks, against the door records
$PY "$HERE/verify_doors.py" "$DATA" "$WORK" "$OUT"
ls -la "$OUT"/${D}*
