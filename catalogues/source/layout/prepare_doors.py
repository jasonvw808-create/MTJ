"""Prepare the door catalogue's images: the door photographs (trimmed to the door, on the paper they are printed on),
the cover and introduction pictures, the dark stone of its dark pages, and the logos. Writes <out>/img-doors-<mode>/...
and <out>/assets-doors-<mode>.json.

    python prepare_doors.py <door photos dir> <editorial dir> <logos dir> <out dir> <print|screen>

door photos: catalogues/images/doors (made by tools/door_photos.py); editorial: catalogues/images/editorial
(cover-doors.jpg, intro-doors.jpg, stone-dark.jpg); logos: LOGO_LIGHT.webp and LOGO_INK.webp."""
import json
import os
import sys
from PIL import Image, ImageFilter

photos, editorial, logos, out, mode = sys.argv[1:6]
PRINT = mode == "print"
Q = 90 if PRINT else 82
DOOR_H = None if PRINT else 1100   # px; a door is placed at most about 125 mm tall
SMALL = 900                        # the price list's own pictures (some 370 px tall) are enlarged to this, as on the website
COVER_W = None if PRINT else 1500
INTRO_W = None if PRINT else 1700
STONE_W = None if PRINT else 1400

sub = "img-doors-" + mode
D = lambda *p: os.path.join(out, sub, *p)
R = lambda *p: "/".join([sub] + list(p))
os.makedirs(D("doors"), exist_ok=True)


def save(im, path, w=None):
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(path, "JPEG", quality=Q, optimize=True, progressive=True, subsampling=0 if PRINT else 2)


doors, src_h, aspect = {}, {}, {}
for f in sorted(os.listdir(photos)):
    if not f.endswith(".jpg"):
        continue
    slug = f[:-4]
    im = Image.open(os.path.join(photos, f)).convert("RGB")
    src_h[slug] = im.height
    if im.height < SMALL:
        k = SMALL / im.height
        im = im.resize((round(im.width * k), SMALL), Image.LANCZOS)
        if k > 1.3:
            im = im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=70, threshold=2))
    elif DOOR_H and im.height > DOOR_H:
        im = im.resize((round(im.width * DOOR_H / im.height), DOOR_H), Image.LANCZOS)
    save(im, D("doors", slug + ".jpg"))
    doors[slug] = R("doors", slug + ".jpg")
    aspect[slug] = round(im.width / im.height, 4)

extra = {}
for key, name, w in (("cover", "cover-doors.jpg", COVER_W), ("intro", "intro-doors.jpg", INTRO_W), ("stone", "stone-dark.jpg", STONE_W)):
    p = os.path.join(editorial, name)
    if os.path.exists(p):
        save(Image.open(p).convert("RGB"), D(name), w)
        extra[key] = R(name)
    else:
        print("missing", p)

for name, f in (("logo-light", "LOGO_LIGHT.webp"), ("logo-ink", "LOGO_INK.webp")):
    Image.open(os.path.join(logos, f)).convert("RGBA").save(D(name + ".png"))
mark = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 216"><g fill="#ece7df">'
        '<polygon points="0,153 64,0 116,0 197,169 176,215 93,42 44,153"/>'
        '<polygon points="169,65 198,0 250,0 319,153 274,153 223,42 191,110"/></g></svg>')
open(D("mark-light.svg"), "w").write(mark)

assets = dict(doors=doors, src_h=src_h, aspect=aspect, logo_light=R("logo-light.png"), logo_ink=R("logo-ink.png"), mark_light=R("mark-light.svg"),
              cover_pos="center 55%", intro_pos="center 60%", **extra)
json.dump(assets, open(os.path.join(out, f"assets-doors-{mode}.json"), "w"), indent=1)
print("door assets:", len(doors), "photographs,", ", ".join(sorted(extra)))
