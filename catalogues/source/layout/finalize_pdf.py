"""Finish a PDF from Chromium: document metadata, and for the print edition the page boxes —
MediaBox/BleedBox the full 216 x 303 mm sheet, TrimBox the A4 page 3 mm inside it.

    python finalize_pdf.py <in.pdf> <out.pdf> <title> <print|screen>"""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import RectangleObject

src, dst, title, mode = sys.argv[1:5]
r = PdfReader(src)
w = PdfWriter(clone_from=r)
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
    "/Subject": "Kitchen sink product catalogue, 2026" + (" — print edition, 3 mm bleed" if mode == "print" else ""),
    "/Keywords": "Maju Terus Jaya, kitchen sinks, catalogue",
    "/Creator": "Maju Terus Jaya catalogue generator (HTML/CSS, Chromium)",
})
w.page_mode = "/UseOutlines"
with open(dst, "wb") as f:
    w.write(f)
print(dst, len(w.pages), "pages")
