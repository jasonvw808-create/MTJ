#!/bin/bash
# Build both catalogue volumes in English and Bahasa Indonesia, as presentation (A4) and print (A4 + 3 mm bleed)
# editions: eight PDFs.
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
  $PY "$HERE/build.py" "$HERE/data/data.json" "$WORK" $MODE en
  $PY "$HERE/build.py" "$HERE/data/data.json" "$WORK" $MODE id
  # stop on colliding text or text outside the safe area (SKIP_CHECK=1 to build anyway)
  node "$HERE/check_layout.js" "$WORK"/{granite,stainless}-$MODE.html "$WORK"/{granite,stainless}-$MODE-id.html || [ "${SKIP_CHECK:-0}" = 1 ]
  for F in granite-$MODE stainless-$MODE granite-$MODE-id stainless-$MODE-id; do
    node "$HERE/export_pdf.js" "$WORK/$F.html" "$WORK/$F.pdf"
  done
done
FIN="$HERE/finalize_pdf.py"
fin() {  # <work name> <out name> <title> <mode> <lang>
  $PY "$FIN" "$WORK/$1.pdf" "$OUT/$2.pdf" "$3" "$4" "$WORK/$1.outline.json" "$5"
}
G="MTJ_Granite_Kitchen_Sink_Collection_Vol01"; S="MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02"
fin granite-screen      "$G"          "Maju Terus Jaya — Granite Kitchen Sink Collection — Volume 01" screen en
fin granite-print       "${G}_PRINT"  "Maju Terus Jaya — Granite Kitchen Sink Collection — Volume 01 (print)" print en
fin stainless-screen    "$S"          "Maju Terus Jaya — Stainless Steel Kitchen Sink Collection — Volume 02" screen en
fin stainless-print     "${S}_PRINT"  "Maju Terus Jaya — Stainless Steel Kitchen Sink Collection — Volume 02 (print)" print en
fin granite-screen-id   "${G}_ID"       "Maju Terus Jaya — Koleksi Bak Cuci Dapur Granit — Volume 01" screen id
fin granite-print-id    "${G}_ID_PRINT" "Maju Terus Jaya — Koleksi Bak Cuci Dapur Granit — Volume 01 (cetak)" print id
fin stainless-screen-id "${S}_ID"       "Maju Terus Jaya — Koleksi Bak Cuci Dapur Stainless Steel — Volume 02" screen id
fin stainless-print-id  "${S}_ID_PRINT" "Maju Terus Jaya — Koleksi Bak Cuci Dapur Stainless Steel — Volume 02 (cetak)" print id
ls -la "$OUT"
