"""Put the catalogues on the website: the presentation editions in the site's catalogue/ folder, under the names the
site asks for, with the pictures of their pages for the look inside; and each PDF's pages, size and contents written
into index.src.html (KS_PDF_META, KS_PDF_PAGES).

    python publish_site.py <pdf_dir> <work_dir> <site_dir> [volume ...]

pdf_dir holds the finished PDFs (make_catalogues.sh, make_door_catalogue.sh), work_dir the bookmark lists build.py and
build_doors.py wrote beside the pages, and site_dir the website (index.src.html). The volumes are granite, stainless and
doors (all three if none is named); a volume not named keeps what index.src.html already says of it. Needs pdftoppm
(poppler-utils)."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from PIL import Image
from pypdf import PdfReader

pdf_dir, work_dir, site = sys.argv[1:4]
DOCS = {  # the site's name for each volume: its PDF here, and the name the site gives it
    "granite": ("MTJ_Granite_Kitchen_Sink_Collection_Vol01", "MTJ_Granite_Kitchen_Sink_Catalogue"),
    "stainless": ("MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02", "MTJ_Stainless_Steel_Kitchen_Sink_Catalogue"),
    "doors": ("MTJ_Wellup_UPVC_Door_Collection_Vol03", "MTJ_Wellup_UPVC_Door_Catalogue"),
}
named = sys.argv[4:]
assert all(d in DOCS for d in named), "the volumes are: " + ", ".join(DOCS)
DOCS = {d: v for d, v in DOCS.items() if not named or d in named}
# the pages that have a page with the same contents in the catalogue the site draws itself, by their bookmarks
SECTIONS = {"Cover": "cover", "The collection": "overview", "The collection: Pressed": "overview-pressed",
            "The collection: Hand Made": "overview-handmade", "Colours": "colours", "Finishes": "finishes",
            "Index": "index", "Index and notes": "index"}
PEEK_WIDTH = 640  # px: shown at most 340 px wide on the site

out = os.path.join(site, "catalogue")
os.makedirs(os.path.join(out, "img", "pages"), exist_ok=True)
meta, contents = {}, {}
for doc, (ours, theirs) in DOCS.items():
    # what is on each page, from the bookmarks (the Indonesian edition has the same pages)
    outline = json.load(open(os.path.join(work_dir, doc + "-screen.outline.json")))
    n = len(PdfReader(os.path.join(pdf_dir, ours + ".pdf")).pages)
    pages = [None] * n
    for e in sorted(outline, key=lambda e: e["level"]):  # a model's own page over its range's
        key = e["title"] if e["level"] == 1 else SECTIONS.get(e["title"])
        if key:
            pages[e["page"] - 1] = key
    overview = next(i for i, k in enumerate(pages) if k in ("overview", "overview-pressed"))
    first = next(i for i, k in enumerate(pages) if k and k not in SECTIONS.values())
    peek = [1, overview + 1, first + 1]
    contents[doc] = {"peek": peek, "pages": pages}
    for lang, sfx in (("en", ""), ("id", "_ID")):
        src = os.path.join(pdf_dir, ours + sfx + ".pdf")
        r = PdfReader(src)
        assert len(r.pages) == n, src + ": not the same pages as the English edition"
        dst = os.path.join(out, theirs + sfx + ".pdf")
        shutil.copyfile(src, dst)
        meta[doc + "-" + lang] = {"pages": n, "bytes": os.path.getsize(dst)}
        # the look inside: three of its pages, as pictures
        with tempfile.TemporaryDirectory() as tmp:
            for k, p in enumerate(peek, 1):
                base = os.path.join(tmp, str(k))
                subprocess.run(["pdftoppm", "-png", "-singlefile", "-f", str(p), "-l", str(p),
                                "-scale-to-x", str(PEEK_WIDTH), "-scale-to-y", "-1", src, base], check=True)
                Image.open(base + ".png").convert("RGB").save(
                    os.path.join(out, "img", "pages", f"{doc}-{lang}-{k}.jpg"), quality=86, optimize=True, progressive=True)
        print(dst, n, "pages", meta[doc + "-" + lang]["bytes"], "bytes; look inside: pages", peek)

# the folder's marker: a one-pixel picture the site looks for when it is opened from a disk
open(os.path.join(out, "img", "here.gif"), "wb").write(
    bytes.fromhex("47494638396101000100800000000000ffffff21f90401000000002c00000000010001000002024401003b"))

# the website's source; the page visitors get (index.html) is built from it when the change is published
page = os.path.join(site, "index.src.html")
html = open(page, encoding="utf-8", newline="").read()   # as it is: the site's lines end in CR LF
for name, value in (("KS_PDF_META", meta), ("KS_PDF_PAGES", contents)):
    line = re.compile(r"^const " + name + r" = (.*);(?=\r?$)", re.M)
    found = line.findall(html)
    assert len(found) == 1, name + " not found once in index.src.html"
    merged = json.loads(found[0])   # what it says of the volumes not published now stays
    merged.update(value)
    html = line.sub(lambda _: "const " + name + " = " + json.dumps(merged, ensure_ascii=False, separators=(",", ":")) + ";", html)
open(page, "w", encoding="utf-8", newline="").write(html)
print("index.src.html: KS_PDF_META and KS_PDF_PAGES written for", ", ".join(DOCS))
