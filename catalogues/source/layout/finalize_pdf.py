"""Finish a PDF from Chromium: document metadata, the bookmarks, and for the print edition the page
boxes — MediaBox/BleedBox the full 216 x 303 mm sheet, TrimBox the A4 page 3 mm inside it.

    python finalize_pdf.py <in.pdf> <out.pdf> <title> <print|screen> [outline.json] [en|id]

Chromium builds bookmarks from the headings but drops the space wherever a heading breaks onto a
new line, so the outline written by build.py replaces them."""
import json
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, RectangleObject, TextStringObject

src, dst, title, mode = sys.argv[1:5]
outline = json.load(open(sys.argv[5])) if len(sys.argv) > 5 and sys.argv[5] else None
lang = sys.argv[6] if len(sys.argv) > 6 else "en"
r = PdfReader(src)
w = PdfWriter(clone_from=r)
w.pdf_header = r.pdf_header   # keep Chromium's PDF 1.4: tagging and transparency need it
mm = 72 / 25.4
for page in w.pages:
    if mode == "print":
        x0, y0, x1, y1 = [float(v) for v in page.mediabox]
        b = 3 * mm
        page.bleedbox = RectangleObject([x0, y0, x1, y1])
        page.trimbox = RectangleObject([x0 + b, y0 + b, x1 - b, y1 - b])
        page.artbox = RectangleObject([x0 + b, y0 + b, x1 - b, y1 - b])
w.add_metadata({
    "/Title": title,
    "/Author": "Maju Terus Jaya",
    "/Subject": ("Kitchen sink product catalogue, 2026" + (" — print edition, 3 mm bleed" if mode == "print" else "")
                 if lang == "en" else
                 "Katalog produk bak cuci dapur, 2026" + (" — edisi cetak, bleed 3 mm" if mode == "print" else "")),
    "/Keywords": "Maju Terus Jaya, kitchen sinks, catalogue" if lang == "en" else "Maju Terus Jaya, bak cuci dapur, katalog",
    "/Creator": "Maju Terus Jaya catalogue generator (HTML/CSS, Chromium)",
})
if outline:
    if "/Outlines" in w.root_object:
        del w.root_object["/Outlines"]
    parents = {}
    for e in outline:
        parents[e["level"]] = w.add_outline_item(e["title"], e["page"] - 1, parent=parents.get(e["level"] - 1))
w.page_mode = "/UseOutlines"
w._root_object[NameObject("/Lang")] = TextStringObject("en-GB" if lang == "en" else "id-ID")
with open(dst, "wb") as f:
    w.write(f)
print(dst, len(w.pages), "pages")
