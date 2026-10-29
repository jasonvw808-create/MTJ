"""Export the finished kitchen images, named by model, for use outside the catalogues (website, social).

    python export_images.py <renders_dir> <out_dir>

Writes <out>/granite/<MODEL>_<Colour>.jpg, <out>/stainless/<MODEL>_<Finish>.jpg and the editorial views
(covers, openers, details) in <out>/editorial/. JPEG, sRGB, full rendered resolution."""
import json
import os
import sys
from PIL import Image

src, out = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(here, "data", "data.json")))
sys.path.insert(0, here)
from build import GRANITE_SHOW, COLOUR_NAME  # noqa: E402

EDITORIAL = ["cover_granite", "cover_stainless", "intro_granite", "intro_stainless", "opener_pressed", "opener_hand",
             "closing", "closing_granite", "notes_stainless", "index_granite"]


def load(p):
    im = Image.open(p)
    if im.mode in ("I;16", "I;16B", "I"):
        im = im.point(lambda v: v / 256).convert("L")
    return im.convert("RGB")


def put(name, dst):
    p = os.path.join(src, name + ".png")
    if not os.path.exists(p):
        print("missing", name)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    load(p).save(dst, "JPEG", quality=92, optimize=True, progressive=True, subsampling=0)


for m in data["granite"]:
    show = GRANITE_SHOW[m["model"]]
    put(show["recipe"], os.path.join(out, "granite", f'{m["model"].replace(" ", "-")}_{COLOUR_NAME[show["colour"]].replace(" ", "-")}.jpg'))
for m in data["stainless"]:
    put(m["model"].lower().replace(" ", ""), os.path.join(out, "stainless", f'{m["model"].replace(" ", "-")}_{m["finish"].replace(" ", "-")}.jpg'))
for e in EDITORIAL:
    put(e, os.path.join(out, "editorial", e.replace("_", "-") + ".jpg"))
print("exported to", out)
